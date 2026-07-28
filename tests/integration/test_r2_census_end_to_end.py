"""Stage M2.2-R2.8: end-to-end proof through the public orchestrator entry point.

These tests call ``CensusOrchestrator.run()`` — the real connected workflow — against a
scripted synthetic transport and a real temporary SQLite catalog on a real temporary data
root. No engine is invoked directly, no socket is opened, and no live SEC request is made:
the autouse fixture in ``tests/conftest.py`` makes any socket use raise.

Covered: base metadata sources, a structurally valid submissions source, multiple quarterly
index instances with two required closed quarters and one optional open quarter, persisted
raw snapshots, parsing, normalization, index reconciliation, Decision 012 resolution,
canonical projection, the completion contract, and retrieval accounting.
"""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import pytest
from conftest import VirtualClock

from disclosure_drift.config import (
    SEC_USER_AGENT_ENV,
    NetworkSection,
    ProjectConfig,
    load_config,
)
from disclosure_drift.sec.census_orchestrator import CensusOrchestrator
from disclosure_drift.sec.index_plan import CoverageWindow
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    validate_audit_projection,
)
from disclosure_drift.sec.transport import SecRequest, TransportResponse

VALID_AGENT = "Financial Disclosure Drift research@your-institution.edu"

COVERAGE = CoverageWindow(
    coverage_start=date(2024, 1, 1),
    coverage_end=date(2024, 12, 31),
    as_of_date=date(2024, 8, 15),
)
COVERAGE_WITH_OPEN = CoverageWindow(
    coverage_start=date(2024, 1, 1),
    coverage_end=date(2024, 12, 31),
    as_of_date=date(2024, 8, 15),
    include_open_quarter=True,
)

ACCESSION = "000000000124000001"  # census_accessions.accession_plain is undashed
ACCESSION_DASHED = "0000000001-24-000001"
_INDEX_HEADER = (
    "Company Name        Form Type  CIK     Date Filed  File Name\n"
    "---------------------------------------------------------------------------\n"
)
_INDEX_ROW = "SYNTHETIC ONE INC   10-K       1       2024-02-01  d/0000000001-24-000001.txt\n"


def submissions_payload() -> dict[str, object]:
    """One structurally valid submissions document with a 10-K and an amendment."""
    return {
        "cik": "1",
        "name": "SYNTHETIC ONE",
        "sic": "2834",
        "fiscalYearEnd": "1231",
        "tickers": ["SYN"],
        "exchanges": ["Nasdaq"],
        "formerNames": [{"name": "OLD SYNTHETIC", "from": "2018-01-01", "to": "2020-01-01"}],
        "filings": {
            "recent": {
                "accessionNumber": [ACCESSION_DASHED, "0000000001-24-000002"],
                "filingDate": ["2024-02-01", "2024-03-01"],
                "form": ["10-K", "10-K/A"],
                "acceptanceDateTime": ["2024-02-01T17:31:00.000Z", "2024-03-01T09:00:00.000Z"],
            },
            "files": [],
        },
    }


def bulk_archive() -> bytes:
    """A bulk submissions archive holding the one synthetic registrant."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("CIK0000000001.json", json.dumps(submissions_payload()))
    return buffer.getvalue()


def index_url(year: int, quarter: int) -> str:
    """The only URL shape the index source may request."""
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"


class ScriptedTransport:
    """Answers base sources by identifier and index instances by URL.

    Records every request so order and URL containment can be asserted. Opens no socket.
    """

    def __init__(
        self,
        *,
        malformed_quarters: frozenset[str] = frozenset(),
        block_quarters: frozenset[str] = frozenset(),
    ) -> None:
        self.requests: list[SecRequest] = []
        self.malformed_quarters = malformed_quarters
        self.block_quarters = block_quarters

    @property
    def urls(self) -> list[str]:
        """Requested URLs in order."""
        return [request.url for request in self.requests]

    @property
    def source_order(self) -> list[str]:
        """Requested source identifiers in order, duplicates collapsed in sequence."""
        ordered: list[str] = []
        for request in self.requests:
            if not ordered or ordered[-1] != request.source_id:
                ordered.append(request.source_id)
        return ordered

    def index_requests(self) -> list[str]:
        """Quarterly index URLs in the order they were requested."""
        return [
            request.url
            for request in self.requests
            if request.source_id == "sec_full_index_company"
        ]

    def send(self, request: SecRequest) -> TransportResponse:
        """Return the scripted response for one request."""
        self.requests.append(request)
        if request.source_id == "sec_full_index_company":
            return self._index_response(request)
        body, content_type = self._base_payload(request)
        return TransportResponse(
            status=200,
            headers={"Content-Type": content_type, "ETag": f'W/"{request.source_id}"'},
            final_url=request.url,
            body=body,
        )

    def close(self) -> None:
        """No resource to release."""

    def _index_response(self, request: SecRequest) -> TransportResponse:
        key = _quarter_key(request.url)
        if key in self.block_quarters:
            # An off-boundary redirect fails closed immediately. A block page is equally
            # valid as a global stop but triggers the real 600-second aggregate cooldown,
            # which would stall the suite.
            return TransportResponse(
                status=302,
                headers={"Location": "https://evil.example/company.idx"},
                final_url=request.url,
            )
        if key in self.malformed_quarters:
            body = b"this index has no dashed separator line at all"
        else:
            body = (_INDEX_HEADER + _INDEX_ROW).encode()
        return TransportResponse(
            status=200,
            headers={"Content-Type": "text/plain", "ETag": f'W/"{key}"'},
            final_url=request.url,
            body=body,
        )

    @staticmethod
    def _base_payload(request: SecRequest) -> tuple[bytes, str]:
        values: Mapping[str, tuple[bytes, str]] = {
            "sec_bulk_submissions": (bulk_archive(), "application/zip"),
            "sec_company_tickers_exchange": (
                json.dumps(
                    {
                        "fields": ["cik", "name", "ticker", "exchange"],
                        "data": [[1, "SYNTHETIC ONE", "SYN", "Nasdaq"]],
                    }
                ).encode(),
                "application/json",
            ),
            "sec_company_tickers": (
                json.dumps(
                    {"0": {"cik_str": 1, "ticker": "SYN", "title": "SYNTHETIC ONE"}}
                ).encode(),
                "application/json",
            ),
            "sec_sic_code_list": (
                b"<table><tr><td>Office A</td><td>2834</td><td>Pharma</td></tr></table>",
                "text/html",
            ),
            "sec_edgar_filing_calendar": (
                b"<table><caption>2024 EDGAR federal holidays</caption>"
                b"<tr><td>New Year's Day</td><td>January 1, 2024</td></tr></table>",
                "text/html",
            ),
        }
        return values[request.source_id]


def _quarter_key(url: str) -> str:
    """Extract ``YYYYQTRn`` from a full-index URL."""
    parts = url.rstrip("/").split("/")
    return f"{parts[-3]}{parts[-2]}"


def network_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectConfig:
    """A configuration rooted at ``tmp_path`` with network access enabled."""
    monkeypatch.setenv(SEC_USER_AGENT_ENV, VALID_AGENT)
    base = load_config()
    return base.model_copy(
        update={
            "paths": base.paths.model_copy(update={"data_root": tmp_path}),
            "network": NetworkSection(enabled=True),
        }
    )


def catalog(config: ProjectConfig) -> sqlite3.Connection:
    """Open the real catalog written by the run, read-only for assertions."""
    connection = sqlite3.connect(config.data_tree().catalog_database)
    connection.row_factory = sqlite3.Row
    return connection


def run_census(
    config: ProjectConfig,
    transport: ScriptedTransport,
    coverage: CoverageWindow = COVERAGE,
) -> object:
    """Invoke the public orchestrator entry point.

    The run is fully real — real catalog, real parsing, real retrieval policy — but its
    waits are virtual. A fresh clock per call keeps every run independent; see
    :class:`conftest.VirtualClock`.
    """
    clock = VirtualClock()
    return CensusOrchestrator(
        config,
        transport=transport,
        calendar_target_year=2024,
        coverage=coverage,
        clock=clock.time,
        sleeper=clock.sleep,
    ).run()


# --------------------------------------------------------------------------- #
# Clean end-to-end run
# --------------------------------------------------------------------------- #
@pytest.fixture
def clean_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[object, ScriptedTransport, ProjectConfig]:
    """One complete run with the open quarter included."""
    config = network_config(tmp_path, monkeypatch)
    transport = ScriptedTransport()
    report = run_census(config, transport, COVERAGE_WITH_OPEN)
    return report, transport, config


def test_base_sources_are_requested_before_index_instances(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, transport, _ = clean_run
    order = transport.source_order
    assert order[0] == "sec_bulk_submissions"
    assert "sec_full_index_company" in order
    # Every index request comes after every base-source request, so reconciliation
    # compares against a complete submissions side.
    first_index = order.index("sec_full_index_company")
    assert set(order[:first_index]) >= {
        "sec_bulk_submissions",
        "sec_company_tickers_exchange",
        "sec_company_tickers",
        "sec_sic_code_list",
        "sec_edgar_filing_calendar",
    }


def test_closed_quarters_are_requested_chronologically_and_open_quarter_last(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, transport, _ = clean_run
    keys = [_quarter_key(url) for url in transport.index_requests()]
    assert keys == ["2024QTR1", "2024QTR2", "2024QTR3"]


def test_no_prohibited_url_is_ever_constructed(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, transport, _ = clean_run
    for url in transport.urls:
        lowered = url.lower()
        assert "/archives/edgar/data/" not in lowered
        assert "-index.htm" not in lowered
        assert not lowered.endswith(".xml")
        assert not lowered.endswith(".xsd")
        assert "financial_report" not in lowered
        assert url.startswith(("https://www.sec.gov/", "https://data.sec.gov/"))


def test_source_native_observations_exist_for_the_canonical_accession(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        observations = connection.execute(
            "SELECT COUNT(*) AS n FROM census_accession_observations WHERE accession_plain = ?",
            (ACCESSION,),
        ).fetchone()["n"]
        canonical = connection.execute(
            "SELECT COUNT(*) AS n FROM census_accessions WHERE accession_plain = ?",
            (ACCESSION,),
        ).fetchone()["n"]
    # Observations are the evidence the canonical projection is derived from, so there
    # must be strictly more of them than the single canonical row.
    assert observations > 1
    assert canonical == 1


def test_field_resolution_rows_are_persisted(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        rows = {
            str(row["field_name"]): str(row["status"])
            for row in connection.execute(
                "SELECT field_name, status FROM census_accession_field_resolutions "
                "WHERE accession_plain = ?",
                (ACCESSION,),
            )
        }
        cohort = connection.execute(
            "SELECT official_filing_temporal_cohort FROM census_accession_cohort_resolutions "
            "WHERE accession_plain = ?",
            (ACCESSION,),
        ).fetchone()
    assert rows["form"] in {"resolved", "resolved_by_correction"}
    assert rows["official_filing_date"] in {"resolved", "resolved_by_correction"}
    assert cohort is not None
    assert str(cohort["official_filing_temporal_cohort"]) == "primary_test"


def test_canonical_values_come_from_the_resolver(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        canonical = connection.execute(
            "SELECT form_type, filing_date_sec, official_filing_temporal_cohort "
            "FROM census_accessions WHERE accession_plain = ?",
            (ACCESSION,),
        ).fetchone()
        resolved = {
            str(row["field_name"]): row["resolved_value"]
            for row in connection.execute(
                "SELECT field_name, resolved_value FROM census_accession_field_resolutions "
                "WHERE accession_plain = ?",
                (ACCESSION,),
            )
        }
    assert str(canonical["form_type"]) == str(resolved["form"])
    assert str(canonical["filing_date_sec"]) == str(resolved["official_filing_date"])
    assert str(canonical["official_filing_temporal_cohort"]) == "primary_test"


def test_full_index_evidence_is_lower_authority_than_submissions(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        row = connection.execute(
            "SELECT authority_class, status FROM census_accession_field_resolutions "
            "WHERE accession_plain = ? AND field_name = 'form'",
            (ACCESSION,),
        ).fetchone()
    # The index observes the same form, so this resolves rather than conflicting, and the
    # winning authority is the submissions class, never full_index.
    assert str(row["status"]) in {"resolved", "resolved_by_correction"}
    assert str(row["authority_class"]) == "entity_submissions"


def test_reconciliation_rows_are_persisted(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        states = [
            str(row["state"])
            for row in connection.execute(
                "SELECT state FROM census_index_reconciliation ORDER BY state"
            )
        ]
    assert states
    assert "matching" in states


def test_logical_retrievals_attempts_and_retries_stay_distinct(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    report, transport, config = clean_run
    accounting = report.index_accounting  # type: ignore[attr-defined]
    assert accounting["instances_planned"] == 3
    assert accounting["logical_budget"] == 3
    assert accounting["logical_retrievals_initiated"] == 3
    assert accounting["http_attempts"] == 3
    assert accounting["retries"] == 0
    assert accounting["instances_successful"] == 3
    assert len(transport.index_requests()) == 3
    with catalog(config) as connection:
        persisted = connection.execute(
            "SELECT logical_retrievals_initiated, http_attempts, retries "
            "FROM census_index_retrieval_accounting"
        ).fetchone()
    assert int(persisted["logical_retrievals_initiated"]) == 3
    assert int(persisted["retries"]) == 0


def test_finalized_and_provisional_coverage_remain_separate(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    report, _, _ = clean_run
    coverage = report.index_coverage  # type: ignore[attr-defined]
    assert coverage["required_closed_quarters_planned"] == 2
    assert coverage["required_closed_quarters_successful"] == 2
    assert coverage["finalized_reconciliation_coverage"] == ["2024QTR1", "2024QTR2"]
    assert coverage["provisional_reconciliation_coverage"] == ["2024QTR3"]
    assert "2024QTR3" not in coverage["finalized_reconciliation_coverage"]
    assert coverage["closed_quarter_coverage_complete"] is True


def test_all_required_closed_quarters_satisfied_clears_the_index_gate(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    report, _, config = clean_run
    blocking = [
        reason
        for reason in report.completion.recovery_blocking_reasons  # type: ignore[attr-defined]
        if reason.startswith("index_required_closed_quarter_missing")
    ]
    assert blocking == []
    with catalog(config) as connection:
        satisfied = [
            str(row["instance_key"])
            for row in connection.execute(
                "SELECT instance_key FROM census_index_instances "
                "WHERE satisfied = 1 ORDER BY instance_key"
            )
        ]
    assert satisfied == ["2024QTR1", "2024QTR2", "2024QTR3"]


def test_lifecycle_events_were_appended_for_every_instance(
    clean_run: tuple[object, ScriptedTransport, ProjectConfig],
) -> None:
    _, _, config = clean_run
    with catalog(config) as connection:
        rows = connection.execute(
            "SELECT instance_key, lifecycle_state FROM census_index_instance_events "
            "ORDER BY instance_key, occurred_at_utc"
        ).fetchall()
    states = {str(row["instance_key"]) for row in rows}
    assert states == {"2024QTR1", "2024QTR2", "2024QTR3"}
    assert "retrieval_started" in {str(row["lifecycle_state"]) for row in rows}
    assert "satisfied" in {str(row["lifecycle_state"]) for row in rows}


def test_final_validation_repairs_projection_corrupted_immediately_after_flush(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Completion is withheld until deterministic post-flush damage is repaired."""
    config = network_config(tmp_path, monkeypatch)
    original_flush = ObservationRecorder.flush_projection
    injected_paths: list[Path] = []

    def flush_then_corrupt(
        recorder: ObservationRecorder,
    ) -> tuple[int, tuple[str, ...]]:
        result = original_flush(recorder)
        projection_path = recorder.audit_path()
        projection_path.write_bytes(b'{"truncated":')
        injected_paths.append(projection_path)
        return result

    monkeypatch.setattr(ObservationRecorder, "flush_projection", flush_then_corrupt)
    report = run_census(config, ScriptedTransport(), COVERAGE_WITH_OPEN)

    assert injected_paths == [config.data_tree().audit / "census_source_observations.jsonl"]
    assert report.completed  # type: ignore[attr-defined]

    with catalog(config) as connection:
        validation = validate_audit_projection(connection, injected_paths[0])
        projection_events = connection.execute(
            "SELECT detected_condition, resolution_state FROM census_projection_recovery_events"
        ).fetchall()
        run_recovery_states = connection.execute(
            "SELECT resolution_state FROM census_recovery_states "
            "WHERE census_run_id = ? AND scenario = 'audit_projection_interrupted'",
            (report.census_run_id,),  # type: ignore[attr-defined]
        ).fetchall()

    assert validation.is_valid
    assert projection_events
    assert any("malformed_json" in str(row["detected_condition"]) for row in projection_events)
    assert {str(row["resolution_state"]) for row in projection_events} == {"resolved"}
    assert run_recovery_states
    assert {str(row["resolution_state"]) for row in run_recovery_states} == {"resolved"}


# --------------------------------------------------------------------------- #
# Restart
# --------------------------------------------------------------------------- #
def test_restart_reuses_the_verified_quarter_and_resumes_at_the_gap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A blocked second quarter stops the loop; the rerun resumes without re-requesting."""
    config = network_config(tmp_path, monkeypatch)

    first_transport = ScriptedTransport(block_quarters=frozenset({"2024QTR2"}))
    first = run_census(config, first_transport, COVERAGE_WITH_OPEN)
    first_keys = [_quarter_key(url) for url in first_transport.index_requests()]

    assert first_keys[0] == "2024QTR1"
    assert "2024QTR2" in first_keys
    # The block stopped the loop, so the open quarter was never reached.
    assert "2024QTR3" not in first_keys
    assert first.index_accounting["stopped_early"] is True  # type: ignore[attr-defined]
    assert (
        first.index_accounting["stop_reason"]  # type: ignore[attr-defined]
        == "network_containment_failure"
    )
    assert not first.completed  # type: ignore[attr-defined]

    with catalog(config) as connection:
        after_first = {
            str(row["instance_key"]): (str(row["lifecycle_state"]), int(row["satisfied"]))
            for row in connection.execute(
                "SELECT instance_key, lifecycle_state, satisfied FROM census_index_instances"
            )
        }
        blocked_events = connection.execute(
            "SELECT COUNT(*) AS n FROM census_index_instance_events "
            "WHERE instance_key = '2024QTR2' AND lifecycle_state = 'blocked'"
        ).fetchone()["n"]
    assert after_first["2024QTR1"] == ("satisfied", 1)
    assert after_first["2024QTR2"][1] == 0
    assert blocked_events >= 1

    second_transport = ScriptedTransport()
    second = run_census(config, second_transport, COVERAGE_WITH_OPEN)
    second_keys = [_quarter_key(url) for url in second_transport.index_requests()]

    # The verified first quarter is reused, not retrieved again, and the run resumes at
    # the earliest unsatisfied instance.
    assert "2024QTR1" not in second_keys
    assert second_keys == ["2024QTR2", "2024QTR3"]
    accounting = second.index_accounting  # type: ignore[attr-defined]
    assert accounting["instances_already_satisfied"] == 1
    assert accounting["logical_budget"] == 2
    assert accounting["logical_retrievals_initiated"] == 2

    coverage = second.index_coverage  # type: ignore[attr-defined]
    assert coverage["closed_quarter_coverage_complete"] is True
    assert coverage["provisional_reconciliation_coverage"] == ["2024QTR3"]

    # Earlier failed evidence is preserved, never overwritten or deleted.
    with catalog(config) as connection:
        preserved = connection.execute(
            "SELECT COUNT(*) AS n FROM census_index_instance_events "
            "WHERE instance_key = '2024QTR2' AND lifecycle_state = 'blocked'"
        ).fetchone()["n"]
    assert preserved >= 1


def test_restart_produces_the_same_canonical_resolution_as_a_clean_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An interrupted-then-resumed run and a clean run agree on canonical values."""
    interrupted_root = tmp_path / "interrupted"
    clean_root = tmp_path / "clean"
    interrupted_root.mkdir()
    clean_root.mkdir()

    interrupted_config = network_config(interrupted_root, monkeypatch)
    run_census(
        interrupted_config,
        ScriptedTransport(block_quarters=frozenset({"2024QTR2"})),
        COVERAGE_WITH_OPEN,
    )
    run_census(interrupted_config, ScriptedTransport(), COVERAGE_WITH_OPEN)

    # Compare like with like: the resumed scenario made two orchestrator passes, so the
    # clean comparison makes two as well. A single pass legitimately has fewer competing
    # observations of the living bulk source.
    clean_config = network_config(clean_root, monkeypatch)
    run_census(clean_config, ScriptedTransport(), COVERAGE_WITH_OPEN)
    run_census(clean_config, ScriptedTransport(), COVERAGE_WITH_OPEN)

    def canonical_values(config: ProjectConfig) -> tuple:
        """Canonical values, excluding per-run observation identifiers."""
        with catalog(config) as connection:
            accession = connection.execute(
                "SELECT accession_plain, form_type, is_amendment, filing_date_sec, "
                "report_date, official_filing_temporal_cohort, accepted_temporal_cohort "
                "FROM census_accessions ORDER BY accession_plain"
            ).fetchall()
            fields = connection.execute(
                "SELECT accession_plain, field_name, status, resolved_value, "
                "authority_class FROM census_accession_field_resolutions "
                "ORDER BY accession_plain, field_name"
            ).fetchall()
        return (
            tuple(tuple(row) for row in accession),
            tuple(tuple(row) for row in fields),
        )

    assert canonical_values(interrupted_config) == canonical_values(clean_config)


# --------------------------------------------------------------------------- #
# Failure variant
# --------------------------------------------------------------------------- #
def test_a_malformed_required_quarter_blocks_completion_but_not_later_quarters(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = network_config(tmp_path, monkeypatch)
    transport = ScriptedTransport(malformed_quarters=frozenset({"2024QTR1"}))
    report = run_census(config, transport, COVERAGE)

    keys = [_quarter_key(url) for url in transport.index_requests()]
    # The malformed first quarter did not stop the loop; the later safe quarter ran.
    assert keys == ["2024QTR1", "2024QTR2"]
    assert not report.completed  # type: ignore[attr-defined]

    accounting = report.index_accounting  # type: ignore[attr-defined]
    assert accounting["instances_failed"] >= 1
    assert accounting["instances_successful"] >= 1
    assert accounting["stopped_early"] is False

    coverage = report.index_coverage  # type: ignore[attr-defined]
    assert coverage["closed_quarter_coverage_complete"] is False
    assert coverage["required_closed_quarters_failed_keys"] == ["2024QTR1"]

    blocking = [
        reason
        for reason in report.completion.recovery_blocking_reasons  # type: ignore[attr-defined]
        if "2024QTR1" in reason
    ]
    assert blocking, report.completion.recovery_blocking_reasons  # type: ignore[attr-defined]
    assert any("index_required_closed_quarter_missing" in reason for reason in blocking)

    with catalog(config) as connection:
        state = connection.execute(
            "SELECT lifecycle_state, satisfied, detail FROM census_index_instances "
            "WHERE instance_key = '2024QTR1'"
        ).fetchone()
        raw = connection.execute(
            "SELECT COUNT(*) AS n FROM census_source_observations "
            "WHERE source_id = 'sec_full_index_company'"
        ).fetchone()["n"]
    assert int(state["satisfied"]) == 0
    assert str(state["lifecycle_state"]) == "indeterminate"
    # The malformed snapshot is preserved as evidence.
    assert raw >= 2


def test_the_excluded_open_quarter_is_not_retrieved_and_not_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = network_config(tmp_path, monkeypatch)
    transport = ScriptedTransport()
    report = run_census(config, transport, COVERAGE)

    keys = [_quarter_key(url) for url in transport.index_requests()]
    assert keys == ["2024QTR1", "2024QTR2"]

    coverage = report.index_coverage  # type: ignore[attr-defined]
    assert coverage["provisional_open_quarter"] == "2024QTR3"
    assert coverage["provisional_open_quarter_not_retrieved"] is True
    assert coverage["provisional_reconciliation_coverage"] == []
    assert coverage["closed_quarter_coverage_complete"] is True
    assert coverage["future_quarters_not_planned"] == ["2024QTR4"]

    blocking = [
        reason
        for reason in report.completion.recovery_blocking_reasons  # type: ignore[attr-defined]
        if "2024QTR3" in reason or "2024QTR4" in reason
    ]
    assert blocking == []
