"""SQLite policy, migrations, integrity gates, and the single logical writer."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from disclosure_drift.errors import CatalogWriteError, GateFailureError, SingleWriterViolationError
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.storage import catalog as catalog_module
from disclosure_drift.storage.catalog import CatalogWriter, read_only_connection
from disclosure_drift.storage.sqlite import (
    REQUIRED_SQLITE_VERSION,
    apply_migrations,
    available_migrations,
    backup_database,
    connect,
    integrity_report,
    require_sqlite_version,
    transaction,
)

REQUIRED_TABLES = {
    "ops_ingestion_jobs",
    "ops_job_events",
    "ops_retrieval_attempts",
    "ops_checkpoints",
    "ops_schema_migrations",
    "raw_source_snapshots",
    "raw_objects",
    "raw_object_observations",
    "raw_http_responses",
    "raw_quarantine_objects",
    "inventory_accessions",
    "inventory_accession_registrants",
    "inventory_filing_documents",
    "inventory_accession_observations",
    "inventory_amendment_relationships",
    "inventory_classifications",
    "inventory_reasons",
    "inventory_company_aliases",
    "inventory_company_lineage",
    "audit_inventory_events",
    "audit_classification_events",
    "audit_checksum_events",
    "audit_schema_events",
    "audit_parser_runs",
    "audit_parser_failures",
    "audit_release_diffs",
    "release_inventory_releases",
    "release_membership",
    "release_files",
    "release_acceptance_results",
    "reference_form_types",
    "reference_reason_codes",
    "reference_sic_codes",
    "reference_cohort_definitions",
    "reference_policy_versions",
    "census_source_observations",
    "census_archive_members",
    "census_parser_runs",
    "census_parsed_records",
    "census_quarantined_records",
    "census_historical_references",
    "census_registrants",
    "census_registrant_observations",
    "census_candidate_lineage_edges",
    "census_accessions",
    "census_accession_observations",
    "census_calendar_days",
    "census_qa_metrics",
    "census_plan_sources",
    "census_projection_recovery_events",
    "census_recovery_states",
}


@pytest.fixture
def writer(tmp_path: Path) -> CatalogWriter:
    """Return an unopened catalog writer over a temporary database."""
    return CatalogWriter(tmp_path / "catalog" / "sec.sqlite3", tmp_path / "locks")


def test_sqlite_version_floor_is_enforced() -> None:
    assert require_sqlite_version()
    with pytest.raises(Exception, match="older than the required"):
        require_sqlite_version((99, 0))


def test_version_floor_matches_strict_table_requirement() -> None:
    assert REQUIRED_SQLITE_VERSION == (3, 37)


EXPECTED_MIGRATIONS: tuple[tuple[int, str], ...] = (
    (1, "initial"),
    (2, "source_observations"),
    (3, "census_catalog"),
    (4, "m22_r1_safety"),
    (5, "r2_structural_evidence"),
    (6, "r2_resolution_and_reconciliation"),
    (7, "r2_index_retrieval"),
    (8, "r3_durability_and_lineage"),
    (9, "m23_pilot_schema"),
    (10, "m23_quota_policy_reference"),
    (11, "m23_joint_selector_policy_reference"),
    (12, "m23_selection_entity_reasons"),
    (13, "m23_manifest_lifecycle_guards"),
    (14, "m33_multi_registrant_relational_correction"),
)
"""The canonical migration chain, asserted by exact version and name.

Checking the ordered versions and names rather than only a count means adding,
renaming, reordering, or skipping a migration all fail loudly.
"""


def test_the_packaged_migration_chain_is_exactly_as_expected() -> None:
    discovered = tuple((item.version, item.name) for item in available_migrations())
    assert discovered == EXPECTED_MIGRATIONS


def test_migration_creates_every_required_logical_table(writer: CatalogWriter) -> None:
    with writer as catalog:
        applied = catalog.migrate()
        rows = catalog.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    names = {row["name"] for row in rows}
    assert applied == tuple(name for _, name in EXPECTED_MIGRATIONS)
    assert names >= REQUIRED_TABLES


def test_migrations_are_idempotent(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
    second = CatalogWriter(writer._database_path, writer._lock_path.parent)  # noqa: SLF001
    with second as catalog:
        assert catalog.migrate() == ()


def test_every_migration_version_and_checksum_is_recorded(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        rows = catalog.connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version"
        ).fetchall()
    recorded = tuple((int(row["version"]), str(row["name"])) for row in rows)
    assert recorded == EXPECTED_MIGRATIONS
    expected_checksums = {item.version: item.checksum_sha256 for item in available_migrations()}
    for row in rows:
        assert row["checksum_sha256"] == expected_checksums[int(row["version"])]


def test_foreign_keys_are_enforced_on_every_connection(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        with pytest.raises(sqlite3.IntegrityError), transaction(catalog.connection):
            catalog.connection.execute(
                "INSERT INTO inventory_reasons "
                "(accession_plain, reason_code, detail, recorded_at_utc) VALUES (?, ?, ?, ?)",
                ("000000000024000001", "ELIGIBLE_ORIGINAL_10K", None, "2026-07-26T00:00:00Z"),
            )


def test_strict_typing_rejects_a_wrong_type(writer: CatalogWriter) -> None:
    """STRICT rejects TEXT in an INTEGER column.

    The wording differs across SQLite versions ("datatype mismatch" on 3.37,
    "cannot store TEXT value in INTEGER column" on 3.53), so the invariant is the
    exception type plus either accepted phrasing.
    """
    with writer as catalog:
        catalog.migrate()
        with pytest.raises(sqlite3.IntegrityError) as excinfo:
            catalog.connection.execute(
                "INSERT INTO ops_retrieval_attempts "
                "(retrieval_attempt_id, source_url_canonical, logical_role, attempt_number, "
                "attempt_state, started_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
                ("a", "https://example.invalid/x", "index_json", "not-an-int", "started", "now"),
            )

    message = str(excinfo.value).lower()
    assert "datatype mismatch" in message or (
        "cannot store text value" in message and "integer column" in message
    ), message


def test_check_constraints_reject_an_unknown_state(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            catalog.connection.execute(
                "INSERT INTO ops_ingestion_jobs "
                "(job_id, job_kind, job_state, stage, started_at_utc) VALUES (?, ?, ?, ?, ?)",
                ("j", "census", "bogus", "M2.1", "now"),
            )


def test_transaction_rolls_back_on_failure(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        catalog.seed_reference_data()
        with pytest.raises(RuntimeError), catalog.batch() as connection:
            connection.execute(
                "INSERT INTO reference_policy_versions "
                "(policy_key, policy_version, decision_record, recorded_at_utc) "
                "VALUES ('scratch', '1', 'doc', 'now')"
            )
            message = "boom"
            raise RuntimeError(message)
        remaining = catalog.connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_policy_versions WHERE policy_key = 'scratch'"
        ).fetchone()["rows"]
    assert remaining == 0


def test_reference_seed_covers_reason_codes_and_frozen_cohorts(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        counts = catalog.seed_reference_data()
        codes = catalog.connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_reason_codes"
        ).fetchone()["rows"]
        cohorts = catalog.connection.execute(
            "SELECT cohort_name, assignment_date_source FROM reference_cohort_definitions "
            "ORDER BY window_start"
        ).fetchall()
        sic = catalog.connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_sic_codes"
        ).fetchone()["rows"]

    assert codes == len(REASON_CODES) == counts["reason_codes"]
    assert [row["cohort_name"] for row in cohorts] == [
        "development",
        "transition",
        "primary_test",
        "prospective",
        "monitoring",
    ]
    assert {row["assignment_date_source"] for row in cohorts} == {"official_sec_filing_date"}
    assert sic == 0, "SIC reference data is loaded in Stage M2.2 from an SEC snapshot"


def test_the_s5_4_reserve_reason_code_reaches_the_catalog(writer: CatalogWriter) -> None:
    """Decision 020 section 8: registering ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE``
    needs no migration, because ``reference_reason_codes`` is seeded at runtime
    from ``reasons.py`` through the established catalog convention. Migration
    ``0012`` therefore seeds no reason code and no policy-reference row."""
    with writer as catalog:
        catalog.migrate()
        catalog.seed_reference_data()
        row = catalog.connection.execute(
            "SELECT category, blocks_release, requires_manual_review, decision_record "
            "FROM reference_reason_codes WHERE reason_code = ?",
            ("REVIEW_PILOT_NO_COMPATIBLE_RESERVE",),
        ).fetchone()
        pool_exhausted = catalog.connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_reason_codes WHERE reason_code = ?",
            ("REVIEW_PILOT_RESERVE_POOL_EXHAUSTED",),
        ).fetchone()["rows"]
    assert row is not None
    assert row["category"] == "review"
    assert row["blocks_release"] == 0
    assert row["requires_manual_review"] == 1
    assert row["decision_record"] == (
        "Docs/Decisions/decision_020_m23_s5_4_reserve_architecture.md"
    )
    assert pool_exhausted == 0


def test_migration_0012_seeds_no_policy_reference_row(writer: CatalogWriter) -> None:
    """The signature and quota policy versions already exist, so the S5.4
    migration adds none (Decision 020 sections 8 and 12)."""
    packaged = next(item for item in available_migrations() if item.version == 12)
    statements = "".join(
        line
        for line in packaged.sql.splitlines(keepends=True)
        if not line.lstrip().startswith("--")
    )
    assert "reference_policy_versions" not in statements
    assert "reference_reason_codes(reason_code)" in statements
    assert "INSERT INTO" not in statements.upper()
    assert "REVIEW_PILOT_NO_COMPATIBLE_RESERVE" in statements
    with writer as catalog:
        catalog.migrate()
        rows = catalog.connection.execute(
            "SELECT policy_key FROM reference_policy_versions ORDER BY policy_key"
        ).fetchall()
    keys = [row["policy_key"] for row in rows]
    assert "pilot_replacement_signature" in keys
    assert len(keys) == len(set(keys))


def test_seeding_is_idempotent(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        catalog.seed_reference_data()
        catalog.seed_reference_data()
        rows = catalog.connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_reason_codes"
        ).fetchone()["rows"]
    assert rows == len(REASON_CODES)


def test_unregistered_reason_codes_are_refused(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        catalog.seed_reference_data()
        with pytest.raises(Exception, match="unregistered reason code"):
            catalog.record_reasons("000000000024000001", ["NOT_A_CODE"])


def test_second_writer_fails_loudly(tmp_path: Path) -> None:
    first = CatalogWriter(tmp_path / "catalog" / "sec.sqlite3", tmp_path / "locks")
    second = CatalogWriter(tmp_path / "catalog" / "sec.sqlite3", tmp_path / "locks")
    with first as catalog:
        catalog.migrate()
        with pytest.raises(SingleWriterViolationError, match="another catalog writer"):
            second.__enter__()


def test_lease_is_released_and_reusable(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    with CatalogWriter(path, tmp_path / "locks") as catalog:
        catalog.migrate()
    with CatalogWriter(path, tmp_path / "locks") as catalog:
        assert catalog.lease.lease_id


def test_elapsed_timestamp_never_allows_takeover_of_active_writer(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    active = CatalogWriter(path, tmp_path / "locks", lease_seconds=-1)
    with active as catalog:
        catalog.migrate()
        successor = CatalogWriter(path, tmp_path / "locks")
        with pytest.raises(SingleWriterViolationError, match="Elapsed time never"):
            successor.__enter__()


def test_writer_fails_closed_when_advisory_locking_is_unavailable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(catalog_module, "fcntl", None)
    with pytest.raises(CatalogWriteError, match="refusing to fall back"):
        CatalogWriter(
            tmp_path / "catalog" / "sec.sqlite3",
            tmp_path / "locks",
        ).__enter__()


def test_released_metadata_is_diagnostic_and_recoverable(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    lock_path = tmp_path / "locks" / "catalog_writer.lease"
    with CatalogWriter(path, tmp_path / "locks") as first:
        first.migrate()
        first_id = first.lease.lease_id
    released = json.loads(lock_path.read_text(encoding="utf-8"))
    assert released["lease_id"] == first_id
    assert released["state"] == "released"
    assert released["released_at_utc"]

    with CatalogWriter(path, tmp_path / "locks") as successor:
        assert successor.lease.lease_id != first_id


def test_old_metadata_without_a_held_lock_is_safely_recovered(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    lock_path = tmp_path / "locks" / "catalog_writer.lease"
    lock_path.parent.mkdir(parents=True)
    lock_path.write_text(
        json.dumps(
            {
                "lease_id": "old-owner",
                "writer_pid": 1,
                "acquired_at_utc": "2000-01-01T00:00:00Z",
                "expires_at_utc": "2000-01-01T00:15:00Z",
            }
        ),
        encoding="utf-8",
    )
    with CatalogWriter(path, tmp_path / "locks") as catalog:
        catalog.migrate()
        assert catalog.lease.lease_id != "old-owner"


def test_non_owner_release_cannot_change_active_metadata(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    lock_path = tmp_path / "locks" / "catalog_writer.lease"
    owner = CatalogWriter(path, tmp_path / "locks")
    intruder = CatalogWriter(path, tmp_path / "locks")
    with owner:
        before = lock_path.read_text(encoding="utf-8")
        intruder._release_lease()  # noqa: SLF001 - exercise non-owner release boundary
        assert lock_path.read_text(encoding="utf-8") == before


def _wait_for(path: Path, *, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            message = f"timed out waiting for {path}"
            raise AssertionError(message)
        time.sleep(0.01)


def test_process_termination_releases_the_advisory_lock(tmp_path: Path) -> None:
    database = tmp_path / "catalog" / "sec.sqlite3"
    locks = tmp_path / "locks"
    ready = tmp_path / "ready"
    program = (
        "import sys,time;"
        "from pathlib import Path;"
        "from disclosure_drift.storage.catalog import CatalogWriter;"
        "writer=CatalogWriter(Path(sys.argv[1]),Path(sys.argv[2]));"
        "writer.__enter__();"
        "writer.migrate();"
        "Path(sys.argv[3]).write_text('ready');"
        "time.sleep(60)"
    )
    process = subprocess.Popen(
        [sys.executable, "-c", program, str(database), str(locks), str(ready)]
    )
    try:
        _wait_for(ready)
        with pytest.raises(SingleWriterViolationError):
            CatalogWriter(database, locks).__enter__()
    finally:
        process.terminate()
        process.wait(timeout=5)

    with CatalogWriter(database, locks) as recovered:
        assert recovered.lease.lease_id


def test_simultaneous_process_acquisition_has_exactly_one_winner(tmp_path: Path) -> None:
    database = tmp_path / "catalog" / "sec.sqlite3"
    locks = tmp_path / "locks"
    start = tmp_path / "start"
    release = tmp_path / "release"
    results = [tmp_path / "result-1", tmp_path / "result-2"]
    program = (
        "import sys,time;"
        "from pathlib import Path;"
        "from disclosure_drift.errors import SingleWriterViolationError;"
        "from disclosure_drift.storage.catalog import CatalogWriter;"
        "start=Path(sys.argv[3]);release=Path(sys.argv[4]);result=Path(sys.argv[5]);"
        "\nwhile not start.exists(): time.sleep(0.01)\n"
        "try:\n"
        "  with CatalogWriter(Path(sys.argv[1]),Path(sys.argv[2])):\n"
        "    result.write_text('acquired')\n"
        "    while not release.exists(): time.sleep(0.01)\n"
        "except SingleWriterViolationError:\n"
        "  result.write_text('blocked')\n"
    )
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                program,
                str(database),
                str(locks),
                str(start),
                str(release),
                str(result),
            ]
        )
        for result in results
    ]
    start.write_text("go", encoding="utf-8")
    try:
        for result in results:
            _wait_for(result)
        assert sorted(result.read_text(encoding="utf-8") for result in results) == [
            "acquired",
            "blocked",
        ]
    finally:
        release.write_text("release", encoding="utf-8")
        for process in processes:
            process.wait(timeout=5)


def test_integrity_gates_pass_on_a_fresh_catalog(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        report = catalog.integrity()
    assert report.quick_check == "ok"
    assert report.integrity_check == "ok"
    assert report.foreign_key_violations == 0
    assert report.passed
    report.require()


def test_integrity_failure_blocks_release() -> None:
    from disclosure_drift.storage.sqlite import IntegrityReport

    failing = IntegrityReport("ok", "ok", 3)
    assert not failing.passed
    with pytest.raises(GateFailureError, match="foreign_key_violations=3"):
        failing.require()


def test_reader_connection_cannot_be_confused_with_the_writer(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
    with read_only_connection(writer._database_path) as connection:  # noqa: SLF001
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] in {"wal", "delete"}


def test_read_only_connection_remains_available_while_writer_holds_lock(
    writer: CatalogWriter,
) -> None:
    with writer as catalog:
        catalog.migrate()
        with read_only_connection(writer._database_path) as connection:  # noqa: SLF001
            assert connection.execute("SELECT COUNT(*) FROM ops_schema_migrations").fetchone()[
                0
            ] == len(EXPECTED_MIGRATIONS)


def test_backup_uses_the_sqlite_backup_api(tmp_path: Path) -> None:
    source = tmp_path / "catalog" / "sec.sqlite3"
    with CatalogWriter(source, tmp_path / "locks") as catalog:
        catalog.migrate()
        catalog.seed_reference_data()

    destination = backup_database(source, tmp_path / "backup" / "sec.sqlite3")
    assert destination.is_file()
    with connect(destination) as connection:
        assert integrity_report(connection).passed
        rows = connection.execute("SELECT COUNT(*) AS rows FROM reference_reason_codes").fetchone()[
            "rows"
        ]
    assert rows == len(REASON_CODES)


def test_apply_migrations_on_a_bare_connection(tmp_path: Path) -> None:
    with connect(tmp_path / "bare.sqlite3", writer=True) as connection, transaction(connection):
        applied = apply_migrations(connection)
    assert [migration.version for migration in applied] == [
        version for version, _ in EXPECTED_MIGRATIONS
    ]
