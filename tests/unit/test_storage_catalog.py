"""SQLite policy, migrations, integrity gates, and the single logical writer."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from disclosure_drift.errors import GateFailureError, SingleWriterViolationError
from disclosure_drift.reasons import REASON_CODES
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


def test_migration_creates_every_required_logical_table(writer: CatalogWriter) -> None:
    with writer as catalog:
        applied = catalog.migrate()
        rows = catalog.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    names = {row["name"] for row in rows}
    assert applied == ("initial",)
    assert names >= REQUIRED_TABLES


def test_migrations_are_idempotent(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
    second = CatalogWriter(writer._database_path, writer._lock_path.parent)  # noqa: SLF001
    with second as catalog:
        assert catalog.migrate() == ()


def test_migration_checksums_are_recorded(writer: CatalogWriter) -> None:
    with writer as catalog:
        catalog.migrate()
        row = catalog.connection.execute(
            "SELECT version, checksum_sha256 FROM ops_schema_migrations"
        ).fetchone()
    expected = available_migrations()[0].checksum_sha256
    assert row["version"] == 1
    assert row["checksum_sha256"] == expected


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


def test_expired_lease_may_be_taken_over(tmp_path: Path) -> None:
    path = tmp_path / "catalog" / "sec.sqlite3"
    stale = CatalogWriter(path, tmp_path / "locks", lease_seconds=-1)
    with stale as catalog:
        catalog.migrate()
        successor = CatalogWriter(path, tmp_path / "locks")
        with successor as taken_over:
            assert taken_over.lease.lease_id != catalog.lease.lease_id


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
    assert [migration.version for migration in applied] == [1]
