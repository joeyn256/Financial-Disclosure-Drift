"""Offline metadata parse driver tests (M3.3 contract §26 item 2; **R13**, **R17**, **R18**).

Each test here is non-vacuous by construction: the containment tests attempt a real
write and require a real refusal, the binding tests set up a genuine ambiguity and
require the plan row to resolve it, and the end-to-end test drives the accepted parser
and persistence path over a real stored object rather than a stub.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.m3 import candidate_snapshot
from disclosure_drift.m3 import offline_parse as op
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES, CatalogWriter
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

_AT = "2026-01-01T00:00:00Z"
_RUN = "job-census-1"
_TICKERS = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc"}}


def _payload() -> bytes:
    return json.dumps(_TICKERS, sort_keys=True).encode("utf-8")


def _planned(**overrides: object) -> op.PlannedSource:
    base: dict[str, object] = {
        "census_run_id": _RUN,
        "source_instance_id": "base|sec_company_tickers|1",
        "source_id": "sec_company_tickers",
        "request_identity": "req/tickers/1",
        "required": True,
        "source_scope": "base",
        "retrieval_state": "retrieved",
        "snapshot_state": "verified",
        "parser_state": "not_started",
        "observation_id": "obs-tickers-1",
    }
    base.update(overrides)
    return op.PlannedSource(**base)  # type: ignore[arg-type]


def _observation(store_path: str, **overrides: object) -> object:
    from disclosure_drift.sec.snapshots import SourceObservation

    base: dict[str, object] = {
        "observation_id": "obs-tickers-1",
        "source_id": "sec_company_tickers",
        "requested_url": "https://example.invalid/company_tickers.json",
        "purpose": "census",
        "retrieved_at_utc": _AT,
        "outcome": "stored_new",
        "storage_representation": "identical",
        "relative_storage_path": store_path,
    }
    base.update(overrides)
    return SourceObservation(**base)  # type: ignore[arg-type]


# ==========================================================================
# Group A: R18 dispositions -- exactly one per planned source, deterministic
# ==========================================================================


def test_the_full_index_family_is_candidate_substantive() -> None:
    """**R22** (Decision 072 §4), correcting the Decision 068 §4 disposition.

    ``company.idx`` is the accepted M2.3 source for co-registrants, so its disposition
    follows accepted methodology rather than whatever route the current code exposes.
    """
    source = _planned(source_id="sec_full_index_company")
    assert (
        op.classify_planned_source(source, _observation("raw/sec/indexes/a.idx"))
        == "E0_REQUIRED_PARSE"
    )
    assert "sec_full_index_company" in op.CANDIDATE_SUBSTANTIVE_SOURCE_IDS
    assert "sec_full_index_company" not in op.VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS


def test_an_unavailable_full_index_object_is_category_b_not_category_c() -> None:
    """**R22**: never category C, and never converted into a fabricated empty parse."""
    source = _planned(source_id="sec_full_index_company", retrieval_state="failed")
    assert op.classify_planned_source(source, None) == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"


@pytest.mark.parametrize(
    "source_id", ["sec_edgar_filing_calendar", "sec_edgar_calendar_announcement"]
)
def test_the_calendar_sources_are_category_c_by_forward_trace(source_id: str) -> None:
    """Decision 071 §13: traced, not assumed.

    ``census_calendar_days`` -- the only destination the annual calendar parses into --
    is read solely by ``sec/census.py``'s calendar QA metrics, which are reachable only
    through the orchestrator-only ``qa_metrics()`` entry point R17 excludes from E0. No
    candidate column derives from it, so its parsed output reaches no authoritative
    candidate field and no required freeze provenance.
    """
    source = _planned(source_id=source_id)
    assert (
        op.classify_planned_source(source, _observation("raw/sec/bulk/a.html"))
        == "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY"
    )


def test_no_candidate_column_derives_from_the_calendar_layer() -> None:
    """The trace above, asserted against the builder's own source rather than prose."""
    builder = Path(candidate_snapshot.__file__).read_text(encoding="utf-8")
    assert "census_calendar_days" not in builder


def test_a_usable_candidate_substantive_source_is_category_a() -> None:
    assert (
        op.classify_planned_source(_planned(), _observation("raw/sec/bulk/a.json"))
        == "E0_REQUIRED_PARSE"
    )


@pytest.mark.parametrize(
    "state", ["failed", "blocked", "unavailable", "quarantined", "not_retrieved", "unknown"]
)
def test_an_accepted_unavailable_source_stays_unavailable(state: str) -> None:
    """**R14**: never converted into a fabricated empty parse."""
    assert (
        op.classify_planned_source(_planned(retrieval_state=state), None)
        == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
    )


def test_an_unverified_snapshot_state_is_category_b() -> None:
    source = _planned(snapshot_state="hash_mismatch")
    assert (
        op.classify_planned_source(source, _observation("raw/sec/bulk/a.json"))
        == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
    )


def test_an_unclassifiable_source_fails_closed() -> None:
    with pytest.raises(op.OfflineParseError, match="unclassifiable source id"):
        op.classify_planned_source(_planned(source_id="sec_future_source"), None)


def test_a_retrieved_source_with_no_bound_observation_fails_closed() -> None:
    """§8.1 correction 2: the plan row is the only permitted disambiguator."""
    with pytest.raises(op.OfflineParseError, match="binds no observation_id"):
        op.classify_planned_source(_planned(observation_id=None), None)


def test_a_bound_observation_absent_from_the_catalog_fails_closed() -> None:
    with pytest.raises(op.OfflineParseError, match="not in the accepted catalog"):
        op.classify_planned_source(_planned(), None)


def test_classification_is_deterministic_over_repeated_calls() -> None:
    source = _planned()
    observation = _observation("raw/sec/bulk/a.json")
    assert {op.classify_planned_source(source, observation) for _ in range(5)} == {
        "E0_REQUIRED_PARSE"
    }


# ==========================================================================
# Group B: R17 write containment, proved by attempting a real write
# ==========================================================================


@pytest.fixture
def blank_catalog(tmp_path: Path) -> Iterator[Path]:
    database = tmp_path / "catalog.sqlite3"
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
    yield database


@pytest.mark.parametrize("table", sorted(op.E0_PROHIBITED_TABLES))
def test_every_prohibited_table_is_refused_at_prepare_time(blank_catalog: Path, table: str) -> None:
    with (
        connect(blank_catalog, writer=True) as connection,
        op.write_containment(connection),
        pytest.raises(sqlite3.DatabaseError, match="not authorized"),
    ):
        connection.execute(f"INSERT INTO {table} DEFAULT VALUES")  # noqa: S608


@pytest.mark.parametrize("table", sorted(op.E0_PERMITTED_TABLES))
def test_every_permitted_table_is_reachable(blank_catalog: Path, table: str) -> None:
    """A containment that also blocked the permitted set would be vacuously safe."""
    with (
        connect(blank_catalog, writer=True) as connection,
        op.write_containment(connection),
        pytest.raises(sqlite3.IntegrityError),
    ):
        connection.execute(f"INSERT INTO {table} DEFAULT VALUES")  # noqa: S608


def test_only_parser_state_may_be_updated_on_the_plan_table(blank_catalog: Path) -> None:
    with connect(blank_catalog, writer=True) as connection, op.write_containment(connection):
        connection.execute("UPDATE census_plan_sources SET parser_state = 'completed' WHERE 1 = 0")
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            connection.execute(
                "UPDATE census_plan_sources SET retrieval_state = 'retrieved' WHERE 1 = 0"
            )
        with pytest.raises(sqlite3.DatabaseError, match="not authorized"):
            connection.execute("DELETE FROM census_plan_sources")


def test_the_permitted_footprint_is_exactly_fifteen_tables() -> None:
    assert len(op.E0_PERMITTED_TABLES) == 15
    assert "census_qa_metrics" not in op.E0_PERMITTED_TABLES
    assert not {table for table in op.E0_PERMITTED_TABLES if table.startswith("census_index_")}


def test_containment_is_removed_when_the_context_exits(blank_catalog: Path) -> None:
    with connect(blank_catalog, writer=True) as connection:
        with op.write_containment(connection), pytest.raises(sqlite3.DatabaseError):
            connection.execute("INSERT INTO census_qa_metrics DEFAULT VALUES")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO census_qa_metrics DEFAULT VALUES")


# ==========================================================================
# Group C: no network is constructible on any offline-parse path
# ==========================================================================


def test_the_driver_imports_no_transport_module() -> None:
    """Contract §10.2 item 8: proved by test, not asserted.

    Measured in a clean interpreter, and measured as what **this module adds**: the
    ``disclosure_drift.m3`` package initializer already imports the M3.1/M3.2
    acquisition stack, so importing the package first and differencing isolates the
    driver's own transitive closure from a dependency it inherits and does not use.
    """
    program = (
        "import sys, json;"
        "import disclosure_drift.m3;"
        "before = set(sys.modules);"
        "import disclosure_drift.m3.offline_parse as op;"
        "added = set(sys.modules) - before;"
        "print(json.dumps(sorted("
        "name for name in added if any("
        "name == p or name.startswith(p + '.') for p in op.PROHIBITED_IMPORT_PREFIXES"
        "))))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed argument vector, no shell
        [sys.executable, "-c", program],
        capture_output=True,
        text=True,
        check=True,
    )
    offenders = json.loads(completed.stdout)
    assert offenders == [], f"an offline-parse import pulled in {offenders}"


def test_the_driver_constructs_no_client_on_any_code_path() -> None:
    """The module's executable body names no client, transport, or socket API."""
    source = Path(op.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.Name):
            names.add(node.id)
    for needle in ("SecClient", "HttpxTransport", "socket", "urlopen", "create_connection"):
        assert needle not in names, f"the offline parse driver reaches for {needle}"


# ==========================================================================
# Group D: an end-to-end offline parse over a real stored object
# ==========================================================================


_ANCHOR_CIK = 320193
_ASSOCIATED_CIK = 789019
_ACCESSION_DASHED = "0000320193-20-000096"
_ACCESSION_PLAIN = "0000320193" + "20" + "000096"


def _company_index(rows: tuple[tuple[str, int], ...]) -> bytes:
    """A synthetic ``company.idx``, in the fixed-width shape the accepted parser reads."""
    header = (
        "Company Name                  Form Type   CIK         Date Filed  File Name\n"
        + "-" * 100
        + "\n"
    )
    body = "".join(
        f"{name:<30}{'10-K':<12}{cik:<12}{'2020-10-30':<12}"
        f"edgar/data/{cik}/{_ACCESSION_DASHED}.txt\n"
        for name, cik in rows
    )
    return (header + body).encode("utf-8")


def _seed_accession_layer(connection: sqlite3.Connection) -> None:
    """The authoritative accession layer a prior submissions parse leaves behind."""
    for cik in (_ANCHOR_CIK, _ASSOCIATED_CIK):
        connection.execute(
            "INSERT OR IGNORE INTO census_registrants (cik_numeric, cik_padded, "
            "first_observed_at_utc, latest_observed_at_utc) VALUES (?, ?, ?, ?)",
            (cik, f"{cik:010d}", _AT, _AT),
        )
    connection.execute(
        "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, parser_id, "
        "parser_version, started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
        "outcome, summary_json) VALUES ('pr-seed', 'obs-tickers-1', 'submissions-json', "
        "'submissions-json/1.0', ?, ?, 1, 0, 'completed', '{}')",
        (_AT, _AT),
    )
    connection.execute(
        "INSERT INTO census_parsed_records (parsed_record_id, parser_run_id, "
        "source_observation_id, native_identity, record_sha256, record_index, payload_json, "
        "unknown_fields_json, warnings_json, reason_codes_json, duplicate_indicator, "
        "conflict_indicator, recorded_at_utc) VALUES ('parsed-seed', 'pr-seed', "
        "'obs-tickers-1', ?, ?, 0, '{}', '[]', '[]', '[]', 0, 0, ?)",
        (f"accession:{_ACCESSION_PLAIN}", "f" * 64, _AT),
    )
    connection.execute(
        "INSERT INTO census_accessions (accession_plain, accession_dashed, "
        "registrant_cik_numeric, submitter_cik_numeric, form_type, is_amendment, "
        "is_discovery_form, is_negative_control, filing_date_sec, xbrl_flag, "
        "inline_xbrl_flag, source_observation_id, parsed_record_id, first_observed_at_utc, "
        "latest_observed_at_utc) VALUES (?, ?, ?, ?, '10-K', 0, 1, 0, '2020-10-30', 1, 1, "
        "'obs-tickers-1', 'parsed-seed', ?, ?)",
        (_ACCESSION_PLAIN, _ACCESSION_DASHED, _ANCHOR_CIK, _ANCHOR_CIK, _AT, _AT),
    )


def _seed(
    database: Path,
    tree: DataTree,
    *,
    extra_observation: bool,
    index_rows: tuple[tuple[str, int], ...] = (
        ("APPLE INC", _ANCHOR_CIK),
        ("CO REGISTRANT LLC", _ASSOCIATED_CIK),
    ),
) -> None:
    payload = _payload()
    relative = "raw/sec/bulk/company_tickers.json"
    target = tree.data_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()

    index_relative = "raw/sec/indexes/company_2020_QTR4.idx"
    index_payload = _company_index(index_rows)
    index_target = tree.data_root / index_relative
    index_target.parent.mkdir(parents=True, exist_ok=True)
    index_target.write_bytes(index_payload)
    index_digest = hashlib.sha256(index_payload).hexdigest()

    decoy_relative = "raw/sec/bulk/company_tickers_decoy.json"
    decoy_payload = json.dumps({"0": {"cik_str": 1, "ticker": "ZZZZ", "title": "Decoy"}}).encode()
    decoy = tree.data_root / decoy_relative
    decoy.write_bytes(decoy_payload)
    decoy_digest = hashlib.sha256(decoy_payload).hexdigest()

    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        with transaction(connection) as active:
            for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
                active.execute(
                    "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                    "is_eligible_universe, description, decision_record) VALUES (?,?,?,?,?)",
                    (form_type, int(is_amendment), int(eligible), description, "D007"),
                )
            for code in REASON_CODES.values():
                active.execute(
                    "INSERT OR REPLACE INTO reference_reason_codes (reason_code, category, "
                    "description, blocks_release, requires_manual_review, decision_record) "
                    "VALUES (?,?,?,?,?,?)",
                    (
                        code.code,
                        code.category,
                        code.description,
                        int(code.blocks_release),
                        int(code.requires_manual_review),
                        code.decision_reference,
                    ),
                )
            active.execute(
                "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
                "started_at_utc, detail) VALUES (?, 'sec_census', 'completed', 'M2.2', ?, '')",
                (_RUN, _AT),
            )
            rows = [
                ("obs-tickers-1", relative, digest, len(payload), _AT, "sec_company_tickers"),
                (
                    "obs-index-1",
                    index_relative,
                    index_digest,
                    len(index_payload),
                    _AT,
                    "sec_full_index_company",
                ),
            ]
            if extra_observation:
                rows.append(
                    (
                        "obs-tickers-2",
                        decoy_relative,
                        decoy_digest,
                        len(decoy_payload),
                        "2026-06-01T00:00:00Z",
                        "sec_company_tickers",
                    )
                )
            for observation_id, path, sha, size, retrieved, source_id in rows:
                active.execute(
                    "INSERT INTO census_source_observations (observation_id, source_id, "
                    "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
                    "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
                    "content_size_bytes, storage_representation, relative_storage_path, "
                    "parser_version, recorded_at_utc) VALUES (?, ?, "
                    "'req/tickers/1', 'https://example.invalid/company_tickers.json', 'census', "
                    "?, 'stored_new', ?, ?, ?, ?, ?, 'identical', ?, 'company-tickers/1.0', ?)",
                    (
                        observation_id,
                        source_id,
                        retrieved,
                        sha,
                        sha,
                        sha,
                        size,
                        size,
                        path,
                        _AT,
                    ),
                )
            _seed_accession_layer(active)
            for instance, source_id, observation_id, scope in (
                ("base|tickers", "sec_company_tickers", "obs-tickers-1", "base"),
                ("base|index-2020q1", "sec_full_index_company", "obs-index-1", "base"),
                ("base|calendar", "sec_edgar_filing_calendar", "obs-tickers-1", "base"),
            ):
                active.execute(
                    "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                    "source_id, request_identity, required, source_scope, retrieval_state, "
                    "snapshot_state, parser_state, catalog_state, qa_state, "
                    "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                    "updated_at_utc) VALUES (?, ?, ?, 'req/x', 1, ?, 'retrieved', 'verified', "
                    "'not_started', 'committed', 'passed', '[]', ?, 1, ?)",
                    (_RUN, instance, source_id, scope, observation_id, _AT),
                )


@pytest.fixture
def corpus(tmp_path: Path) -> Iterator[tuple[Path, DataTree]]:
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(database, tree, extra_observation=True)
    yield database, tree


def _run(database: Path, tree: DataTree, tmp_path: Path) -> op.OfflineParseReport:
    with CatalogWriter(database, tmp_path / "locks") as writer:
        return op.run_offline_metadata_parse(writer=writer, tree=tree)


def test_the_offline_parse_derives_the_census_layer(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    database, tree = corpus
    report = _run(database, tree, tmp_path)
    assert report.planned_source_count == 3
    assert report.is_complete
    assert len(report.by_disposition("E0_REQUIRED_PARSE")) == 2
    assert len(report.by_disposition("E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY")) == 1
    with connect(database) as connection:
        runs = connection.execute(
            "SELECT parser_id FROM census_parser_runs ORDER BY parser_id"
        ).fetchall()
    assert [str(row[0]) for row in runs] == ["company-idx", "company-tickers", "submissions-json"]


def test_the_plan_row_disambiguates_two_observations_of_one_source(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    """Recency, size, path, and ``source_id`` alone never decide (**R13**)."""
    database, tree = corpus
    _run(database, tree, tmp_path)
    with connect(database) as connection:
        bound = connection.execute(
            "SELECT DISTINCT source_observation_id FROM census_parsed_records "
            "WHERE native_identity LIKE 'ticker_alias:%' OR native_identity LIKE "
            "'exchange_alias:%'"
        ).fetchall()
        names = connection.execute(
            "SELECT value_text FROM census_registrant_observations "
            "WHERE observation_kind = 'company_name'"
        ).fetchall()
    assert [str(row[0]) for row in bound] == ["obs-tickers-1"]
    assert "Decoy" not in {str(row[0]) for row in names}


def test_category_c_sources_are_left_deliberately_untouched(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    database, tree = corpus
    report = _run(database, tree, tmp_path)
    untouched = report.by_disposition("E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY")
    assert [item.touched for item in untouched] == [False]
    with connect(database) as connection:
        state = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_id = "
            "'sec_edgar_filing_calendar'"
        ).fetchone()[0]
        for table in (
            "census_index_instances",
            "census_index_reconciliation",
            "census_index_instance_events",
            "census_index_retrieval_accounting",
            "census_qa_metrics",
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608 -- fixed allowlist
            ).fetchone()[0]
            assert count == 0, f"{table} was written at E0"
    assert state == "not_started"


def test_a_category_a_source_transitions_its_parser_state(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    database, tree = corpus
    _run(database, tree, tmp_path)
    with connect(database) as connection:
        state = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_id = 'sec_company_tickers'"
        ).fetchone()[0]
    assert state == "completed"


def test_a_reparse_of_the_same_observation_is_deterministic(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    """**GR-C2**: ``parser_run_id`` and ``parsed_record_id`` reproduce exactly."""
    database, tree = corpus
    first = _run(database, tree, tmp_path)
    with connect(database) as connection:
        before = connection.execute(
            "SELECT parsed_record_id FROM census_parsed_records ORDER BY parsed_record_id"
        ).fetchall()
    second = _run(database, tree, tmp_path / "second")
    with connect(database) as connection:
        after = connection.execute(
            "SELECT parsed_record_id FROM census_parsed_records ORDER BY parsed_record_id"
        ).fetchall()
    parsed_first = first.by_disposition("E0_REQUIRED_PARSE")[0]
    parsed_second = second.by_disposition("E0_REQUIRED_PARSE")[0]
    assert parsed_first.parser_run_id == parsed_second.parser_run_id
    assert parsed_second.already_present
    assert [str(row[0]) for row in before] == [str(row[0]) for row in after]


def test_a_missing_plan_bound_object_fails_closed(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(database, tree, extra_observation=False)
    (tree.data_root / "raw/sec/bulk/company_tickers.json").unlink()
    with pytest.raises(RawObjectIntegrityError, match="is missing"):
        _run(database, tree, tmp_path)


def test_no_observation_or_stored_object_is_added(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    database, tree = corpus
    with connect(database) as connection:
        before = connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()[0]
    objects_before = sorted(p.name for p in (tree.data_root / "raw/sec/bulk").iterdir())
    _run(database, tree, tmp_path)
    with connect(database) as connection:
        after = connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()[0]
    assert after == before
    assert sorted(p.name for p in (tree.data_root / "raw/sec/bulk").iterdir()) == objects_before


# ==========================================================================
# Group E: R23 full-index registrant materialization (Decision 072 §§5, 10)
# ==========================================================================


def _registrant_observations(database: Path) -> list[tuple[str, str]]:
    """The accession/CIK pairs the full-index materialization wrote."""
    with connect(database) as connection:
        return [
            (str(row["accession_plain"]), str(json.loads(str(row["raw_value_json"]))))
            for row in connection.execute(
                "SELECT o.accession_plain, o.raw_value_json FROM census_accession_observations "
                "AS o JOIN census_source_observations AS s "
                "ON s.observation_id = o.source_observation_id "
                "WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' "
                "ORDER BY o.raw_value_json"
            ).fetchall()
        ]


def test_full_index_rows_materialize_anchor_and_associated_registrants(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    """**R23** §5.2 -- one row per registrant per accession, grouped by accession."""
    database, tree = corpus
    report = _run(database, tree, tmp_path)
    assert report.full_index_registrant_observations > 0
    assert report.full_index_unbound_accessions == ()
    assert _registrant_observations(database) == [
        (_ACCESSION_PLAIN, f"{_ANCHOR_CIK:010d}"),
        (_ACCESSION_PLAIN, f"{_ASSOCIATED_CIK:010d}"),
    ]


def test_a_repeated_index_row_yields_one_registrant_identity(tmp_path: Path) -> None:
    """**R23** §5.3: membership is the distinct canonical CIK set, never a row count."""
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(
        database,
        tree,
        extra_observation=False,
        index_rows=(
            ("APPLE INC", _ANCHOR_CIK),
            ("CO REGISTRANT LLC", _ASSOCIATED_CIK),
            ("CO REGISTRANT LLC", _ASSOCIATED_CIK),
        ),
    )
    _run(database, tree, tmp_path)
    observed = {cik for _, cik in _registrant_observations(database)}
    assert observed == {f"{_ANCHOR_CIK:010d}", f"{_ASSOCIATED_CIK:010d}"}


def test_a_different_company_name_never_creates_a_second_registrant(tmp_path: Path) -> None:
    """**R23** §5.2: identity is the canonical CIK; names never group registrants."""
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(
        database,
        tree,
        extra_observation=False,
        index_rows=(("APPLE INC", _ANCHOR_CIK), ("APPLE INC (FORMERLY)", _ANCHOR_CIK)),
    )
    _run(database, tree, tmp_path)
    assert {cik for _, cik in _registrant_observations(database)} == {f"{_ANCHOR_CIK:010d}"}


def test_an_index_only_accession_is_reported_and_never_created(tmp_path: Path) -> None:
    """**R23** §5.1: the index never manufactures a candidate accession."""
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(database, tree, extra_observation=False)
    other = tree.data_root / "raw/sec/indexes/company_2020_QTR4.idx"
    other.write_bytes(
        _company_index((("APPLE INC", _ANCHOR_CIK),)).replace(
            _ACCESSION_DASHED.encode(), b"0000999999-20-000001"
        )
    )
    with connect(database, writer=True) as connection, transaction(connection) as active:
        digest = hashlib.sha256(other.read_bytes()).hexdigest()
        active.execute(
            "UPDATE census_source_observations SET stored_sha256 = ?, logical_sha256 = ?, "
            "content_sha256 = ?, stored_size_bytes = ?, content_size_bytes = ? "
            "WHERE observation_id = 'obs-index-1'",
            (digest, digest, digest, other.stat().st_size, other.stat().st_size),
        )
    report = _run(database, tree, tmp_path)
    assert report.full_index_unbound_accessions == ("0000999999" + "20" + "000001",)
    with connect(database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM census_accessions WHERE accession_plain = ?",
            ("0000999999" + "20" + "000001",),
        ).fetchone()[0]
    assert count == 0


def test_a_malformed_index_row_establishes_no_registrant(tmp_path: Path) -> None:
    """**R23**: the accepted parser retains and quarantines it; E0 repairs nothing."""
    tree = DataTree.from_root(tmp_path / "data")
    database = tmp_path / "catalog.sqlite3"
    _seed(database, tree, extra_observation=False)
    target = tree.data_root / "raw/sec/indexes/company_2020_QTR4.idx"
    payload = target.read_bytes() + b"MALFORMED ROW WITH NO COLUMNS\n"
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with connect(database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_source_observations SET stored_sha256 = ?, logical_sha256 = ?, "
            "content_sha256 = ?, stored_size_bytes = ?, content_size_bytes = ? "
            "WHERE observation_id = 'obs-index-1'",
            (digest, digest, digest, len(payload), len(payload)),
        )
    _run(database, tree, tmp_path)
    assert {cik for _, cik in _registrant_observations(database)} == {
        f"{_ANCHOR_CIK:010d}",
        f"{_ASSOCIATED_CIK:010d}",
    }
    with connect(database) as connection:
        quarantined = connection.execute(
            "SELECT COUNT(*) FROM census_quarantined_records"
        ).fetchone()[0]
    assert quarantined >= 1


def test_full_index_materialization_writes_no_index_table(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    """**R23** §5.6 / **R17**: the historical orchestrator's route stays unused."""
    database, tree = corpus
    _run(database, tree, tmp_path)
    with connect(database) as connection:
        for table in (
            "census_index_instances",
            "census_index_reconciliation",
            "census_index_instance_events",
            "census_index_retrieval_accounting",
            "census_qa_metrics",
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608 -- fixed allowlist
            ).fetchone()[0]
            assert count == 0, f"{table} was written by full-index materialization"


def test_full_index_evidence_never_overwrites_the_authoritative_accession(
    corpus: tuple[Path, DataTree], tmp_path: Path
) -> None:
    """**R23** §5.5: Decision 012 gives full_index level 3, weaker than submissions."""
    database, tree = corpus
    with connect(database) as connection:
        before = connection.execute(
            "SELECT registrant_cik_numeric, form_type, filing_date_sec FROM census_accessions "
            "WHERE accession_plain = ?",
            (_ACCESSION_PLAIN,),
        ).fetchone()
        anchor_before = int(before["registrant_cik_numeric"])
    _run(database, tree, tmp_path)
    with connect(database) as connection:
        after = connection.execute(
            "SELECT registrant_cik_numeric FROM census_accessions WHERE accession_plain = ?",
            (_ACCESSION_PLAIN,),
        ).fetchone()
    assert int(after["registrant_cik_numeric"]) == anchor_before == _ANCHOR_CIK


def test_index_object_order_does_not_change_the_result(tmp_path: Path) -> None:
    """**R23**: row and object order are not selection mechanisms."""
    digests = []
    for order in (
        (("APPLE INC", _ANCHOR_CIK), ("CO REGISTRANT LLC", _ASSOCIATED_CIK)),
        (("CO REGISTRANT LLC", _ASSOCIATED_CIK), ("APPLE INC", _ANCHOR_CIK)),
    ):
        root = tmp_path / f"run-{len(digests)}"
        tree = DataTree.from_root(root / "data")
        database = root / "catalog.sqlite3"
        _seed(database, tree, extra_observation=False, index_rows=order)
        _run(database, tree, root)
        digests.append(sorted({cik for _, cik in _registrant_observations(database)}))
    assert digests[0] == digests[1]
