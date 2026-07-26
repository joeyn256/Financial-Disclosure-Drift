"""Stage M2.2 parsers, transactional census, and network-free orchestration."""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import pytest

from disclosure_drift.config import (
    SEC_USER_AGENT_ENV,
    NetworkSection,
    ProjectConfig,
    load_config,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.census import CensusCatalog
from disclosure_drift.sec.census_completion import (
    CensusCompletionDecision,
    PlannedSourceState,
)
from disclosure_drift.sec.census_orchestrator import CensusOrchestrator
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.parsers.base import RecordLocation
from disclosure_drift.sec.parsers.calendar import (
    parse_calendar_announcement,
    parse_edgar_calendar,
)
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.sic import parse_sic_reference
from disclosure_drift.sec.parsers.submissions import parse_submissions_document
from disclosure_drift.sec.parsers.tickers import parse_company_tickers_exchange
from disclosure_drift.sec.snapshots import SnapshotStore
from disclosure_drift.sec.transport import SecRequest, TransportResponse
from disclosure_drift.storage.catalog import CatalogWriter, read_only_connection

VALID_AGENT = "Financial Disclosure Drift research@your-institution.edu"


def location(source: str = "fixture", observation: str = "obs-1") -> RecordLocation:
    return RecordLocation(observation_id=observation, source_id=source)


def submissions_payload() -> dict[str, object]:
    return {
        "cik": "1",
        "name": "SYNTHETIC ONE",
        "formerNames": [{"name": "OLD SYNTHETIC", "from": "2018-01-01", "to": "2020-01-01"}],
        "tickers": ["SYN"],
        "exchanges": ["Nasdaq"],
        "sic": "2834",
        "fiscalYearEnd": "1231",
        "entityType": "operating",
        "filings": {
            "recent": {
                "accessionNumber": ["0000000001-24-000001", "0000000001-24-000002"],
                "filingDate": ["2024-02-01", "2024-03-01"],
                "form": ["10-K", "10-K/A"],
                "acceptanceDateTime": ["20240201170000", "20240301170000"],
            },
            "files": [
                {
                    "name": "CIK0000000001-submissions-001.json",
                    "filingCount": 1,
                    "filingFrom": "2010-01-01",
                    "filingTo": "2010-12-31",
                }
            ],
        },
    }


def test_submissions_parser_retains_three_layers_and_amendments() -> None:
    outcome, references = parse_submissions_document(submissions_payload(), location())
    assert len(outcome.records) == 3
    assert {record.native_identity for record in outcome.records} >= {
        "accession:0000000001-24-000001",
        "accession:0000000001-24-000002",
    }
    assert outcome.records[0].record_sha256
    assert references[0].name == "CIK0000000001-submissions-001.json"
    assert references[0].as_record()["retrieved"] is False


def test_historical_parser_refuses_parallel_array_truncation() -> None:
    outcome = parse_historical_submissions(
        {
            "accessionNumber": ["0000000001-10-000001"],
            "filingDate": [],
            "form": ["10-K"],
        },
        location("sec_submissions_historical"),
        registrant_cik="1",
    )
    assert not outcome.records
    assert outcome.quarantined
    assert outcome.required_field_failures


def test_historical_parser_keeps_source_native_unknown_fields() -> None:
    outcome = parse_historical_submissions(
        {
            "accessionNumber": ["0000000001-10-000001"],
            "filingDate": ["2010-02-01"],
            "form": ["10-K"],
            "futureField": ["retained"],
        },
        location("sec_submissions_historical"),
        registrant_cik="1",
    )
    assert outcome.records[0].payload["futureField"] == "retained"
    assert outcome.records[0].unknown_fields == ("futureField",)


def test_sic_parser_retains_financial_sector_rows_without_filtering() -> None:
    outcome = parse_sic_reference(
        "<table><tr><th>Office</th><th>SIC</th><th>Industry</th></tr>"
        "<tr><td>Office A</td><td>6021</td><td>National Commercial Banks</td></tr></table>",
        location("sec_sic_code_list"),
    )
    assert outcome.records[0].payload["sic"] == "6021"
    assert outcome.records[0].payload["financial_sector_6000_6999"] is True


def test_calendar_parsers_are_explicit_and_tri_state() -> None:
    # R2.2: a date must sit inside an identified official holiday structure before it
    # asserts anything, and the covered year is an explicit plan input rather than
    # something the parser infers. A date in a paragraph is contextual evidence only.
    calendar = parse_edgar_calendar(
        "<table><caption>2026 EDGAR federal holidays</caption>"
        "<tr><td>New Year's Day</td><td>January 1, 2026</td></tr></table>",
        location("sec_edgar_filing_calendar"),
        target_year=2026,
    )
    prose_only = parse_edgar_calendar(
        "<p>EDGAR will be closed January 1, 2026.</p>",
        location("sec_edgar_filing_calendar"),
        target_year=2026,
    )
    announcement = parse_calendar_announcement(
        "<p>EDGAR notice for July 3, 2026.</p>",
        location("sec_edgar_calendar_announcement"),
        manifest_dates=(date(2026, 7, 3),),
    )
    assert calendar.records[0].payload["status"] == "non_operating"
    assert prose_only.records[0].payload["status"] == "unknown"
    assert prose_only.records[0].payload["evidence_kind"] == "contextual_date"
    assert not any(record.payload["status"] == "non_operating" for record in prose_only.records)
    assert prose_only.structural[0].state == "indeterminate"
    assert announcement.records[0].payload["status"] == "unknown"
    assert announcement.records[0].normalization_warnings


def _record_observation(
    writer: CatalogWriter,
    tree: DataTree,
    *,
    source_id: str,
    url: str,
    body: bytes,
    content_type: str,
) -> str:
    store = SnapshotStore(tree)
    observation = store.record(
        FetchResult(
            outcome="retrieved",
            source_id=source_id,
            url=url,
            purpose="synthetic offline parser test",
            status=200,
            body=body,
            declared_content_type=content_type,
            attempts=1,
        )
    )
    ObservationRecorder(writer, tree).record(observation)
    return observation.observation_id


def test_transactional_census_is_logically_idempotent(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        observation_id = _record_observation(
            writer,
            tree,
            source_id="sec_submissions_entity",
            url="https://data.sec.gov/submissions/CIK0000000001.json",
            body=json.dumps(submissions_payload()).encode(),
            content_type="application/json",
        )
        outcome, references = parse_submissions_document(
            submissions_payload(),
            location("sec_submissions_entity", observation_id),
        )
        census = CensusCatalog(writer)
        first = census.persist(
            outcome,
            historical_references=references,
            source_observation_id=observation_id,
        )
        second = census.persist(
            outcome,
            historical_references=references,
            source_observation_id=observation_id,
        )
        accessions = writer.connection.execute(
            "SELECT form_type, is_amendment FROM census_accessions ORDER BY accession_plain"
        ).fetchall()
        aliases = writer.connection.execute(
            "SELECT observation_kind, value_text FROM census_registrant_observations "
            "ORDER BY observation_kind, value_text"
        ).fetchall()

    assert first.normalized_registrants == 1
    assert first.normalized_accessions == 2
    assert second.already_present
    assert [(row["form_type"], row["is_amendment"]) for row in accessions] == [
        ("10-K", 0),
        ("10-K/A", 1),
    ]
    assert ("former_name", "OLD SYNTHETIC") in [
        (row["observation_kind"], row["value_text"]) for row in aliases
    ]


def test_shared_ticker_creates_candidate_edge_without_merging_ciks(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    payload = {
        "fields": ["cik", "name", "ticker", "exchange"],
        "data": [[1, "ONE", "SYN", "NYSE"], [2, "TWO", "SYN", "Nasdaq"]],
    }
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        observation_id = _record_observation(
            writer,
            tree,
            source_id="sec_company_tickers_exchange",
            url="https://www.sec.gov/files/company_tickers_exchange.json",
            body=json.dumps(payload).encode(),
            content_type="application/json",
        )
        outcome = parse_company_tickers_exchange(
            payload,
            location("sec_company_tickers_exchange", observation_id),
        )
        CensusCatalog(writer).persist(outcome, source_observation_id=observation_id)
        registrants = writer.connection.execute(
            "SELECT cik_padded FROM census_registrants ORDER BY cik_padded"
        ).fetchall()
        edges = writer.connection.execute(
            "SELECT from_cik_padded, to_cik_padded, status FROM census_candidate_lineage_edges"
        ).fetchall()
    assert [row["cik_padded"] for row in registrants] == ["0000000001", "0000000002"]
    assert [tuple(row) for row in edges] == [("0000000001", "0000000002", "candidate_only")]


class FixtureTransport:
    """Returns official-source-shaped fixtures without opening a socket."""

    def __init__(self, archive: bytes) -> None:
        self.archive = archive
        self.requests: list[SecRequest] = []

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        validator = request.headers.get("If-None-Match")
        if validator:
            return TransportResponse(
                status=304,
                headers={"ETag": validator},
                final_url=request.url,
                body=b"",
            )
        body, content_type = self._payload(request)
        return TransportResponse(
            status=200,
            headers={"Content-Type": content_type, "ETag": f'"fixture-{len(self.requests)}"'},
            final_url=request.url,
            body=b"" if request.stream else body,
            chunks=iter([body]) if request.stream else None,
        )

    def close(self) -> None:
        return None

    def _payload(self, request: SecRequest) -> tuple[bytes, str]:
        values: Mapping[str, tuple[bytes, str]] = {
            "sec_bulk_submissions": (self.archive, "application/zip"),
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
                b"<table><caption>2026 EDGAR federal holidays</caption>"
                b"<tr><td>New Year's Day</td><td>January 1, 2026</td></tr></table>",
                "text/html",
            ),
            "sec_submissions_historical": (
                json.dumps(
                    {
                        "accessionNumber": ["0000000001-10-000001"],
                        "filingDate": ["2010-02-01"],
                        "form": ["10-K"],
                    }
                ).encode(),
                "application/json",
            ),
        }
        return values[request.source_id]


class OverrideTransport(FixtureTransport):
    """Override selected source responses while retaining all other fixtures."""

    def __init__(
        self,
        archive: bytes,
        overrides: Mapping[str, TransportResponse],
    ) -> None:
        super().__init__(archive)
        self.overrides = overrides

    def send(self, request: SecRequest) -> TransportResponse:
        if request.source_id not in self.overrides:
            return super().send(request)
        self.requests.append(request)
        response = self.overrides[request.source_id]
        return TransportResponse(
            status=response.status,
            headers=response.headers,
            final_url=request.url,
            redirects=response.redirects,
            body=response.body,
            chunks=response.chunks,
            failure=response.failure,
            detail=response.detail,
        )


def _bulk_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("CIK0000000001.json", json.dumps(submissions_payload()))
    return buffer.getvalue()


def _empty_bulk_archive() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED):
        pass
    return buffer.getvalue()


def _network_config(tmp_path: Path, monkeypatch: object) -> ProjectConfig:
    monkeypatch.setenv(SEC_USER_AGENT_ENV, VALID_AGENT)  # type: ignore[attr-defined]
    base = load_config()
    return base.model_copy(
        update={
            "paths": base.paths.model_copy(update={"data_root": tmp_path}),
            "network": NetworkSection(enabled=True),
        }
    )


def test_orchestrator_completes_offline_with_fixture_transport(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    # pytest's MonkeyPatch is intentionally not imported into production typing.
    config = _network_config(tmp_path, monkeypatch)
    transport = FixtureTransport(_bulk_archive())
    report = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()
    rerun = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()

    assert report.completed
    assert report.source_observations == 6
    assert report.parsed_records >= 8
    assert report.historical_references_retrieved == 1
    assert report.audit_path.is_file()
    assert rerun.completed
    assert rerun.source_observations == 12
    assert any("If-None-Match" in request.headers for request in transport.requests)
    assert all("Archives/edgar/data/" not in request.url for request in transport.requests)


def test_prose_only_calendar_blocks_required_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    report = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=OverrideTransport(
            _bulk_archive(),
            {
                "sec_edgar_filing_calendar": TransportResponse(
                    status=200,
                    headers={"Content-Type": "text/html"},
                    final_url="",
                    body=b"<p>EDGAR will be closed January 1, 2026.</p>",
                )
            },
        ),
    ).run()

    calendar = next(
        source
        for source in report.completion.sources
        if source.source_id == "sec_edgar_filing_calendar"
    )
    assert not report.completed
    assert calendar.blocks_completion
    assert calendar.parser_state == "failed"
    assert calendar.qa_state == "blocked"
    assert "REVIEW_CALENDAR_STRUCTURE_UNRECOGNIZED" in calendar.unresolved_blocking_reasons


@pytest.mark.parametrize(
    "response",
    [
        TransportResponse(status=404, headers={}, final_url="", body=b""),
        TransportResponse(
            status=0,
            headers={},
            final_url="",
            failure="read_timeout",
        ),
        TransportResponse(
            status=200,
            headers={"Content-Type": "text/html"},
            final_url="",
            body=b"<html>wrong source shape</html>",
        ),
    ],
)
def test_required_retrieval_failures_never_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    response: TransportResponse,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    transport = OverrideTransport(
        _bulk_archive(),
        {"sec_company_tickers_exchange": response},
    )
    report = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()

    assert not report.completed
    failed = {source.source_id: source for source in report.completion.incomplete_required_sources}
    assert "sec_company_tickers_exchange" in failed
    assert failed["sec_company_tickers_exchange"].retrieval_state in {
        "failed",
        "quarantined",
    }
    assert any(
        source.successful_terminal
        for source in report.completion.sources
        if source.source_id != "sec_company_tickers_exchange"
    )
    with read_only_connection(config.data_tree().catalog_database) as connection:
        job = connection.execute(
            "SELECT job_state FROM ops_ingestion_jobs WHERE job_id = ?",
            (report.census_run_id,),
        ).fetchone()
    assert job["job_state"] == "failed"


def test_exhausted_5xx_never_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    transport = OverrideTransport(
        _bulk_archive(),
        {
            "sec_company_tickers_exchange": TransportResponse(
                status=503,
                headers={},
                final_url="",
                body=b"",
            )
        },
    )
    report = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()
    requests = [
        request
        for request in transport.requests
        if request.source_id == "sec_company_tickers_exchange"
    ]
    assert not report.completed
    assert len(requests) == config.sec.max_retries


def test_report_lists_every_incomplete_required_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    failure = TransportResponse(status=404, headers={}, final_url="", body=b"")
    report = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=OverrideTransport(
            _bulk_archive(),
            {
                "sec_company_tickers": failure,
                "sec_sic_code_list": failure,
            },
        ),
    ).run()
    incomplete = {source.source_id for source in report.completion.incomplete_required_sources}
    assert {"sec_company_tickers", "sec_sic_code_list"} <= incomplete
    assert "sec_company_tickers" in report.detail
    assert "sec_sic_code_list" in report.detail


def test_malformed_required_source_is_not_a_genuine_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    transport = OverrideTransport(
        _bulk_archive(),
        {
            "sec_company_tickers": TransportResponse(
                status=200,
                headers={"Content-Type": "application/json"},
                final_url="",
                body=b"[]",
            )
        },
    )
    report = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()
    state = next(
        source for source in report.completion.sources if source.source_id == "sec_company_tickers"
    )
    assert not report.completed
    assert state.parser_state == "quarantined"
    assert state.catalog_state == "committed"


def test_empty_bulk_archive_is_not_a_genuine_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    report = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=FixtureTransport(_empty_bulk_archive()),
    ).run()
    state = next(
        source for source in report.completion.sources if source.source_id == "sec_bulk_submissions"
    )
    assert not report.completed
    assert state.retrieval_state == "retrieved"
    assert state.snapshot_state == "verified"
    assert state.parser_state == "quarantined"
    assert state.catalog_state == "committed"


def test_failed_discovered_historical_reference_blocks_completion(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    transport = OverrideTransport(
        _bulk_archive(),
        {
            "sec_submissions_historical": TransportResponse(
                status=404,
                headers={},
                final_url="",
                body=b"",
            )
        },
    )
    report = CensusOrchestrator(config, transport=transport, calendar_target_year=2026).run()
    historical = [source for source in report.completion.sources if source.scope == "historical"]
    assert len(historical) == 1
    assert historical[0].required
    assert historical[0].retrieval_state == "failed"
    assert not report.completed


def test_restart_after_failed_run_can_complete_from_verified_snapshots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    failed = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=OverrideTransport(
            _bulk_archive(),
            {
                "sec_company_tickers": TransportResponse(
                    status=404,
                    headers={},
                    final_url="",
                    body=b"",
                )
            },
        ),
    ).run()
    recovered = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=FixtureTransport(_bulk_archive()),
    ).run()
    assert not failed.completed
    assert recovered.completed
    assert not recovered.completion.incomplete_required_sources


def test_restart_after_quarantined_response_retains_evidence_and_can_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    failed = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=OverrideTransport(
            _bulk_archive(),
            {
                "sec_company_tickers": TransportResponse(
                    status=200,
                    headers={"Content-Type": "text/html"},
                    final_url="",
                    body=b"<html>wrong source shape</html>",
                )
            },
        ),
    ).run()
    recovered = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=FixtureTransport(_bulk_archive()),
    ).run()

    assert not failed.completed
    assert recovered.completed
    assert not recovered.completion.recovery_blocking_reasons
    with read_only_connection(config.data_tree().catalog_database) as connection:
        retained = connection.execute(
            "SELECT stored_sha256, logical_sha256, storage_representation, "
            "relative_storage_path FROM census_source_observations "
            "WHERE outcome = 'quarantined' ORDER BY recorded_at_utc LIMIT 1"
        ).fetchone()
    assert retained["stored_sha256"] == retained["logical_sha256"]
    assert retained["storage_representation"] == "identical"
    assert (config.data_tree().data_root / retained["relative_storage_path"]).is_file()


def test_restart_with_missing_cataloged_raw_object_cannot_complete(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    first = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=FixtureTransport(_bulk_archive()),
    ).run()
    assert first.completed
    with read_only_connection(config.data_tree().catalog_database) as connection:
        row = connection.execute(
            "SELECT relative_storage_path FROM census_source_observations "
            "WHERE source_id = 'sec_company_tickers' ORDER BY recorded_at_utc DESC LIMIT 1"
        ).fetchone()
    (config.data_tree().data_root / row["relative_storage_path"]).unlink()

    restarted = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=FixtureTransport(_bulk_archive()),
    ).run()
    assert not restarted.completed
    assert restarted.completion.recovery_blocking_reasons


def test_structurally_valid_zero_records_remain_successful(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    empty_exchange = json.dumps(
        {"fields": ["cik", "name", "ticker", "exchange"], "data": []}
    ).encode()
    report = CensusOrchestrator(
        config,
        calendar_target_year=2026,
        transport=OverrideTransport(
            _bulk_archive(),
            {
                "sec_company_tickers_exchange": TransportResponse(
                    status=200,
                    headers={"Content-Type": "application/json"},
                    final_url="",
                    body=empty_exchange,
                )
            },
        ),
    ).run()
    state = next(
        source
        for source in report.completion.sources
        if source.source_id == "sec_company_tickers_exchange"
    )
    assert state.successful_terminal
    assert report.completed


def test_optional_failure_is_not_promoted_to_required() -> None:
    required = PlannedSourceState(
        instance_id="required",
        source_id="required_source",
        request_identity="required|url|",
        required=True,
        scope="base",
        retrieval_state="retrieved",
        snapshot_state="verified",
        parser_state="completed",
        catalog_state="committed",
        qa_state="passed",
    )
    optional = PlannedSourceState(
        instance_id="optional",
        source_id="optional_source",
        request_identity="optional|url|",
        required=False,
        scope="base",
        retrieval_state="unavailable",
        parser_state="missing",
        qa_state="failed",
        unresolved_blocking_reasons=("optional_unavailable",),
    )
    decision = CensusCompletionDecision(
        sources=(required, optional),
        recovery_passed=True,
        recovery_blocking_reasons=(),
        sqlite_integrity_passed=True,
        release_blocking_reason_count=0,
        qa_report_written=True,
        audit_projection_complete=True,
    )
    assert decision.completed
    assert decision.incomplete_required_sources == ()


@pytest.mark.parametrize(
    ("retrieval", "parser"),
    [
        ("unavailable", "missing"),
        ("unknown", "missing"),
        ("not_retrieved", "not_started"),
        ("retrieved", "missing"),
    ],
)
def test_required_nonterminal_states_fail_closed(
    retrieval: str,
    parser: str,
) -> None:
    source = PlannedSourceState(
        instance_id="required",
        source_id="required_source",
        request_identity="required|url|",
        required=True,
        scope="base",
        retrieval_state=retrieval,  # type: ignore[arg-type]
        snapshot_state="verified" if retrieval == "retrieved" else "not_verified",
        parser_state=parser,  # type: ignore[arg-type]
        catalog_state="not_started",
        qa_state="failed",
        unresolved_blocking_reasons=("incomplete",),
    )
    decision = CensusCompletionDecision(
        sources=(source,),
        recovery_passed=True,
        recovery_blocking_reasons=(),
        sqlite_integrity_passed=True,
        release_blocking_reason_count=0,
        qa_report_written=True,
        audit_projection_complete=True,
    )
    assert not decision.completed
    assert decision.incomplete_required_sources == (source,)


def test_missing_parser_result_is_explicitly_terminal_and_blocking(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    config = _network_config(tmp_path, monkeypatch)
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    observation = SnapshotStore(tree).record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_company_tickers",
            url="https://www.sec.gov/files/company_tickers.json",
            purpose="census ticker evidence",
            status=200,
            body=b"{}",
            declared_content_type="application/json",
            attempts=1,
        )
    )
    # ``_base_plan`` is instance-bound because the annual-calendar instance identity
    # includes the requested target year, so it is invoked through an orchestrator.
    orchestrator = CensusOrchestrator(config, transport=FixtureTransport(_bulk_archive()))
    state = CensusOrchestrator._after_observation(  # noqa: SLF001 - completion seam
        orchestrator._base_plan("sec_company_tickers"),  # noqa: SLF001
        observation,
        None,
    )
    assert state.retrieval_state == "retrieved"
    assert state.snapshot_state == "verified"
    assert state.parser_state == "missing"
    assert not state.successful_terminal
