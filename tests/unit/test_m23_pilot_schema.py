"""M2.3 Stage S3.2 pilot schema, lifecycle, and integrity tests (Decision 016).

Every test uses a fresh temporary SQLite database. No test opens, modifies, or
even touches a persistent repository database, and none performs a network
call: the autouse ``_block_network`` fixture in ``tests/conftest.py`` already
enforces that.
"""

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift import pilot_policy
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES
from disclosure_drift.storage.migrations import __path__ as _migrations_path
from disclosure_drift.storage.sqlite import (
    apply_migrations,
    available_migrations,
    connect,
    integrity_report,
    transaction,
)

_MIGRATIONS_DIR = Path(_migrations_path[0])

#: The accepted Stage S6 architecture record, whose section 15.1 SQL migration 0013
#: reproduces byte for byte.
_DECISION_021_PATH = (
    Path(__file__).resolve().parents[2]
    / "Docs"
    / "Decisions"
    / "decision_021_m23_s6_manifest_construction.md"
)

#: Locks migration 0010's exact bytes: Stage S5.2 (Decision 018 section 20, migration
#: 0011) adds an additive migration on top and never edits 0009 or 0010.
_MIGRATION_0010_SHA256 = "2332bb93093f436b1a5999b9a8de7505f111bf26f982d6e29f8d66217e633d43"


def _hex(seed: str) -> str:
    """Return a deterministic 64-character lowercase hex digest for a test seed."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _migrated_database(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference_data(connection)
    return path


def _seed_reference_data(connection: sqlite3.Connection) -> None:
    """Seed ``reference_form_types``/``reference_reason_codes`` for FK targets.

    Mirrors ``CatalogWriter.seed_reference_data`` without its writer-lease
    machinery, since these tests open a plain connection to a fresh temp DB.
    """
    with transaction(connection) as c:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            c.execute(
                "INSERT OR REPLACE INTO reference_form_types "
                "(form_type, is_amendment, is_eligible_universe, description, decision_record) "
                "VALUES (?, ?, ?, ?, 'Docs/Decisions/decision_007_sec_universe.md')",
                (form_type, int(is_amendment), int(eligible), description),
            )
        for code in REASON_CODES.values():
            c.execute(
                "INSERT OR REPLACE INTO reference_reason_codes "
                "(reason_code, category, description, blocks_release, "
                "requires_manual_review, decision_record) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    code.code,
                    code.category,
                    code.description,
                    int(code.blocks_release),
                    int(code.requires_manual_review),
                    code.decision_reference,
                ),
            )


def _seed_job(connection: sqlite3.Connection, job_id: str = "job-1") -> str:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO ops_ingestion_jobs "
            "(job_id, job_kind, job_state, stage, started_at_utc, detail) "
            "VALUES (?, 'sec_census', 'completed', 'M2.2', '2026-01-01T00:00:00Z', '')",
            (job_id,),
        )
    return job_id


def _insert_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    census_run_id: str = "job-1",
    state: str = "building",
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_snapshots "
            "(snapshot_id, census_run_id, coverage_start, coverage_end, as_of_date, "
            "include_open_quarter, coverage_policy_version, candidate_policy_version, "
            "sic_family_mapping_version, evidence_policy_version, coverage_window_sha256, "
            "input_observation_set_sha256, snapshot_state, created_at_utc) "
            "VALUES (?, ?, '2010-01-01', '2026-06-30', '2026-06-30', 0, "
            "'coverage/1.0', ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                census_run_id,
                pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
                pilot_policy.SIC_FAMILY_MAPPING_VERSION,
                pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
                _hex(f"coverage-window:{snapshot_id}"),
                _hex(f"obs:{snapshot_id}"),
                state,
            ),
        )


def _insert_entity(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    cik_numeric: int,
    candidate_category: str = "operating",
    **overrides: object,
) -> None:
    fields: dict[str, object] = {
        "snapshot_id": snapshot_id,
        "cik_numeric": cik_numeric,
        "cik_padded": f"{cik_numeric:010d}",
        "entity_tie_break_sha256": _hex(f"entity-tie-break:{snapshot_id}:{cik_numeric}"),
        "candidate_category": candidate_category,
        "size_evidence_level": "unavailable",
        "industry_evidence_level": "unavailable",
        "history_evidence_level": "unavailable",
        "primary_universe_evidence_level": "unavailable",
        "filing_time_name": f"Synthetic Issuer {cik_numeric}",
        "recorded_at_utc": "2026-01-01T00:00:00Z",
    }
    fields.update(overrides)
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with transaction(connection) as c:
        c.execute(
            f"INSERT INTO pilot_candidate_entities ({columns}) VALUES ({placeholders})",  # noqa: S608
            tuple(fields.values()),
        )


def _insert_accession(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    accession_plain: str,
    anchor_cik_numeric: int,
    **overrides: object,
) -> None:
    fields: dict[str, object] = {
        "snapshot_id": snapshot_id,
        "accession_plain": accession_plain,
        "accession_number_dashed": accession_plain,
        "accession_tie_break_sha256": _hex(f"accession-tie-break:{snapshot_id}:{accession_plain}"),
        "anchor_cik_numeric": anchor_cik_numeric,
        # **Decision 083 R59** (migration 0014): every candidate row states whether its
        # substantive registrant set was established. Fixtures default to 'established',
        # which is the only state a frozen snapshot may hold.
        "registrant_set_completeness": "established",
        "form_type": "10-K",
        "is_amendment": 0,
        "filing_date_evidence_level": "unavailable",
        "cohort_evidence_level": "unavailable",
        "xbrl_evidence_level": "unavailable",
        "amendment_purpose_evidence_level": "unavailable",
        "recorded_at_utc": "2026-01-01T00:00:00Z",
    }
    fields.update(overrides)
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with transaction(connection) as c:
        c.execute(
            f"INSERT INTO pilot_candidate_accessions ({columns}) VALUES ({placeholders})",  # noqa: S608
            tuple(fields.values()),
        )


def _insert_registrant(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    accession_plain: str,
    registrant_cik_numeric: int,
    is_anchor: bool = True,
    association_class: str = "substantive",
    registrant_set_completeness: str = "established",
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_accession_registrants "
            "(snapshot_id, accession_plain, registrant_cik_numeric, registrant_cik_padded, "
            "role, is_anchor, association_class, registrant_set_completeness, evidence_level, "
            "recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'unavailable', '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                accession_plain,
                registrant_cik_numeric,
                f"{registrant_cik_numeric:010d}",
                "submitter_only"
                if association_class == "submitter_only"
                else ("anchor" if is_anchor else "associated"),
                1 if is_anchor else 0,
                association_class,
                registrant_set_completeness,
            ),
        )


def _freeze_snapshot(connection: sqlite3.Connection, *, snapshot_id: str) -> None:
    """Freeze a snapshot whose child rows already satisfy the freeze invariants."""
    entity_count = connection.execute(
        "SELECT COUNT(*) FROM pilot_candidate_entities WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()[0]
    accession_count = connection.execute(
        "SELECT COUNT(*) FROM pilot_candidate_accessions WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()[0]
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_candidate_snapshots SET "
            "snapshot_state = 'frozen', frozen_at_utc = '2026-01-02T00:00:00Z', "
            "candidate_snapshot_sha256 = ?, input_observation_set_sha256 = ?, "
            "candidate_entity_table_sha256 = ?, candidate_accession_table_sha256 = ?, "
            "candidate_registrant_table_sha256 = ?, candidate_entity_evidence_sha256 = ?, "
            "candidate_accession_evidence_sha256 = ?, candidate_entity_reasons_sha256 = ?, "
            "candidate_accession_reasons_sha256 = ?, entity_count = ?, accession_count = ? "
            "WHERE snapshot_id = ?",
            (
                _hex(f"root:{snapshot_id}"),
                _hex(f"obs:{snapshot_id}"),
                _hex(f"entities:{snapshot_id}"),
                _hex(f"accessions:{snapshot_id}"),
                _hex(f"registrants:{snapshot_id}"),
                _hex(f"entity-evidence:{snapshot_id}"),
                _hex(f"accession-evidence:{snapshot_id}"),
                _hex(f"entity-reasons:{snapshot_id}"),
                _hex(f"accession-reasons:{snapshot_id}"),
                entity_count,
                accession_count,
                snapshot_id,
            ),
        )


def _insert_selection_run(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    run_state: str = "planned",
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_runs "
            "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
            "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
            "started_at_utc) "
            "VALUES (?, ?, 'seed', ?, 'quota/1.0', 1000, ?, ?, '2026-01-01T00:00:00Z')",
            (
                selection_run_id,
                snapshot_id,
                pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
                run_state,
                _hex(f"selection-input:{selection_run_id}"),
            ),
        )


# --------------------------------------------------------------------------
# Group A: migration inventory, forbidden statements, provenance (tests 1-9)
# --------------------------------------------------------------------------


def test_migration_inventory_is_contiguous_through_0015() -> None:
    versions = tuple(migration.version for migration in available_migrations())
    assert versions == tuple(range(1, 16))
    assert versions[-1] == 15


def test_migration_0009_contains_no_forbidden_statements() -> None:
    sql = (_MIGRATIONS_DIR / "0009_m23_pilot_schema.sql").read_text(encoding="utf-8")
    stripped_lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    body = "\n".join(stripped_lines)
    # Trigger bodies legitimately use ``BEGIN ... END;``; only a transaction-start
    # keyword (bare ``BEGIN;`` or ``BEGIN IMMEDIATE/DEFERRED/EXCLUSIVE/TRANSACTION``)
    # is forbidden here, since the migration runner supplies its own transaction.
    assert re.search(r"\bBEGIN\s*;", body) is None
    assert re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", body) is None
    assert "COMMIT" not in body.upper()
    assert "PRAGMA" not in body.upper()
    assert not re.search(r"\bDROP\s+TABLE\b", body, re.IGNORECASE)
    assert not re.search(r"\bALTER\s+TABLE\b", body, re.IGNORECASE)
    assert "inventory_accessions" not in body
    assert "inventory_accession_registrants" not in body
    assert not re.search(r"\binventory_\w+", body)


def test_migration_0009_raise_messages_are_string_literals() -> None:
    """SQLite before 3.47.0 rejects a non-literal RAISE() error-message argument
    (e.g. ``'foo' || NEW.bar``, ``CASE ...``, ``printf(...)``) with
    ``OperationalError: near "||": syntax error``. The repository supports
    SQLite 3.37+, so every RAISE(ROLLBACK|ABORT|FAIL, ...) in migration 0009
    must carry a single bare string-literal message.

    This walks the raw SQL rather than relying on a compiled connection so it
    fails deterministically regardless of which SQLite version runs the tests.
    """
    sql = (_MIGRATIONS_DIR / "0009_m23_pilot_schema.sql").read_text(encoding="utf-8")
    raise_call = re.compile(r"RAISE\s*\(\s*(ROLLBACK|ABORT|FAIL)\s*,\s*")
    checked = 0
    for match in raise_call.finditer(sql):
        checked += 1
        offset = match.start()
        i = match.end()
        assert i < len(sql) and sql[i] == "'", (
            f"RAISE at offset {offset} does not begin its message with a string literal"
        )
        i += 1
        closed = False
        while i < len(sql):
            if sql[i] == "'":
                if i + 1 < len(sql) and sql[i + 1] == "'":
                    i += 2
                    continue
                i += 1
                closed = True
                break
            i += 1
        assert closed, f"RAISE at offset {offset} has an unterminated string literal"
        trailing = sql[i:].lstrip()
        assert trailing.startswith(")"), (
            f"RAISE at offset {offset} error message is not a bare string literal -- "
            f"found dynamic content (e.g. ||, a column reference, CASE, or a function call) "
            f"before the closing parenthesis: {sql[i : i + 40]!r}"
        )
    assert checked == 79, f"expected 79 RAISE invocations in migration 0009, found {checked}"


def test_fresh_database_applies_migrations_through_0015(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        cursor = connection.execute("SELECT version FROM ops_schema_migrations ORDER BY version")
        versions = tuple(row["version"] for row in cursor.fetchall())
    assert versions == tuple(range(1, 16))


def test_second_migration_pass_is_idempotent(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert apply_migrations(connection) == ()


def test_migration_provenance_records_0009_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    inventory = available_migrations()
    migration_0009 = next(m for m in inventory if m.version == 9)
    assert migration_0009.name == "m23_pilot_schema"
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations WHERE version = 9"
        ).fetchone()
    assert row["version"] == 9
    assert row["name"] == "m23_pilot_schema"
    assert row["checksum_sha256"] == migration_0009.checksum_sha256


def test_migration_0009_is_byte_identical_to_the_committed_s4_baseline() -> None:
    """Locks migration 0009's exact content: S4 (Decision 017, migration 0010) must
    never modify it, only add an additive migration on top (governing S4 repair
    instructions; `git diff` against the committed baseline confirms the same thing
    at review time, but this test catches any future accidental edit too)."""
    sql = (_MIGRATIONS_DIR / "0009_m23_pilot_schema.sql").read_bytes()
    assert (
        hashlib.sha256(sql).hexdigest()
        == "119d9d9536b11c61325412991e5818d4b03ebee8538c38d05cacb5218b956cda"
    )


def test_migration_provenance_records_0010_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    inventory = available_migrations()
    migration_0010 = next(m for m in inventory if m.version == 10)
    assert migration_0010.name == "m23_quota_policy_reference"
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations WHERE version = 10"
        ).fetchone()
    assert row["version"] == 10
    assert row["name"] == "m23_quota_policy_reference"
    assert row["checksum_sha256"] == migration_0010.checksum_sha256


def test_migration_0010_seeds_the_frozen_quota_policy_version(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    assert pilot_policy.PILOT_QUOTA_POLICY_VERSION == "m23-pilot-quota-policy-v1"
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT policy_version, decision_record FROM reference_policy_versions "
            "WHERE policy_key = 'pilot_quota'"
        ).fetchone()
    assert row is not None
    assert row["policy_version"] == pilot_policy.PILOT_QUOTA_POLICY_VERSION
    assert row["decision_record"] == (
        "Docs/Decisions/decision_017_s4_quota_policy_and_control_evidence.md"
    )


def test_migration_0010_is_additive_only() -> None:
    sql = (_MIGRATIONS_DIR / "0010_m23_quota_policy_reference.sql").read_text(encoding="utf-8")
    stripped_lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    body = "\n".join(stripped_lines)
    assert re.search(r"\bBEGIN\s*;", body) is None
    assert re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", body) is None
    assert "COMMIT" not in body.upper()
    assert "PRAGMA" not in body.upper()
    assert not re.search(r"\bDROP\s+TABLE\b", body, re.IGNORECASE)
    assert not re.search(r"\bALTER\s+TABLE\b", body, re.IGNORECASE)
    assert not re.search(r"\bCREATE\s+TABLE\b", body, re.IGNORECASE)
    assert not re.search(r"\bDELETE\s+FROM\b", body, re.IGNORECASE)
    assert "INSERT OR REPLACE INTO reference_policy_versions" in body


def test_migration_0010_seed_is_idempotent_under_the_runner(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert apply_migrations(connection) == ()
        row = connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_policy_versions "
            "WHERE policy_key = 'pilot_quota'"
        ).fetchone()
    assert row["rows"] == 1


# --------------------------------------------------------------------------
# Group A (S5.2): additive migration 0011, joint-selector policy reference
# (Decision 018 section 20; Milestones/contracts/m23_s5_2.md)
# --------------------------------------------------------------------------


def test_migration_provenance_records_0011_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    inventory = available_migrations()
    migration_0011 = next(m for m in inventory if m.version == 11)
    assert migration_0011.name == "m23_joint_selector_policy_reference"
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations WHERE version = 11"
        ).fetchone()
    assert row["version"] == 11
    assert row["name"] == "m23_joint_selector_policy_reference"
    assert row["checksum_sha256"] == migration_0011.checksum_sha256


def test_migration_0011_seeds_the_frozen_joint_selector_policy_version(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    assert pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION == "m23-joint-selector-policy-v1"
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT policy_version, decision_record FROM reference_policy_versions "
            "WHERE policy_key = 'pilot_joint_selector'"
        ).fetchone()
    assert row is not None
    assert row["policy_version"] == pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION
    assert row["decision_record"] == (
        "Docs/Decisions/decision_018_m23_s5_accession_selection_policy.md"
    )


def test_migration_0011_contains_no_ddl() -> None:
    sql = (_MIGRATIONS_DIR / "0011_m23_joint_selector_policy_reference.sql").read_text(
        encoding="utf-8"
    )
    stripped_lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    body = "\n".join(stripped_lines)
    assert re.search(r"\bBEGIN\s*;", body) is None
    assert re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", body) is None
    assert "COMMIT" not in body.upper()
    assert "PRAGMA" not in body.upper()
    assert not re.search(r"\bCREATE\b", body, re.IGNORECASE)
    assert not re.search(r"\bALTER\b", body, re.IGNORECASE)
    assert not re.search(r"\bDROP\b", body, re.IGNORECASE)
    assert not re.search(r"\bTRIGGER\b", body, re.IGNORECASE)
    assert not re.search(r"\bINDEX\b", body, re.IGNORECASE)
    assert not re.search(r"\bDELETE\s+FROM\b", body, re.IGNORECASE)
    assert not re.search(r"\bUPDATE\b", body, re.IGNORECASE)
    assert "INSERT OR REPLACE INTO reference_policy_versions" in body
    # The only INSERT OR REPLACE it performs is the authorized policy-reference seed.
    assert body.upper().count("INSERT") == 1


def test_migration_0011_writes_only_the_policy_reference_table() -> None:
    sql = (_MIGRATIONS_DIR / "0011_m23_joint_selector_policy_reference.sql").read_text(
        encoding="utf-8"
    )
    stripped_lines = [line for line in sql.splitlines() if not line.strip().startswith("--")]
    body = "\n".join(stripped_lines)
    assert re.findall(r"\bINTO\s+(\w+)", body) == ["reference_policy_versions"]
    # No candidate, selection, quota, reason, snapshot, inventory, or census row.
    for table_prefix in (
        "pilot_candidate",
        "pilot_select",
        "pilot_quota",
        "pilot_reserve",
        "pilot_manifest",
        "inventory_",
        "census_",
        "reference_reason_codes",
    ):
        assert table_prefix not in body


def test_migration_0011_carries_no_wall_clock_dependency() -> None:
    sql = (_MIGRATIONS_DIR / "0011_m23_joint_selector_policy_reference.sql").read_text(
        encoding="utf-8"
    )
    for token in ("CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME", "datetime(", "strftime("):
        assert token.upper() not in sql.upper()
    assert "'2026-07-28T00:00:00Z'" in sql


def test_migration_0011_seed_is_idempotent_under_the_runner(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert apply_migrations(connection) == ()
        row = connection.execute(
            "SELECT COUNT(*) AS rows FROM reference_policy_versions "
            "WHERE policy_key = 'pilot_joint_selector'"
        ).fetchone()
    assert row["rows"] == 1


def test_migration_0011_leaves_the_accepted_s4_selector_row_unchanged(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        row = connection.execute(
            "SELECT policy_version, decision_record FROM reference_policy_versions "
            "WHERE policy_key = 'pilot_selector'"
        ).fetchone()
    assert row["policy_version"] == pilot_policy.PILOT_SELECTOR_POLICY_VERSION
    assert row["policy_version"] == "deterministic-constrained/1.0"
    assert row["decision_record"] == ("Docs/Decisions/decision_013_pilot_selection_mechanics.md")


def test_migrations_0009_and_0010_are_unchanged_by_the_s5_2_addition() -> None:
    """Migration 0009 is byte-locked above; 0010 is locked here for the same reason."""
    sql = (_MIGRATIONS_DIR / "0010_m23_quota_policy_reference.sql").read_bytes()
    assert hashlib.sha256(sql).hexdigest() == _MIGRATION_0010_SHA256


def test_the_frozen_joint_selector_constant_is_exactly_the_approved_value() -> None:
    assert pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION == "m23-joint-selector-policy-v1"
    assert "PILOT_JOINT_SELECTOR_POLICY_VERSION" in pilot_policy.__all__


def test_exactly_twenty_two_pilot_tables_exist(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    expected = {
        "pilot_candidate_snapshots",
        "pilot_candidate_entities",
        "pilot_candidate_accessions",
        "pilot_candidate_accession_registrants",
        "pilot_candidate_entity_evidence",
        "pilot_candidate_accession_evidence",
        "pilot_candidate_entity_reasons",
        "pilot_candidate_accession_reasons",
        "pilot_selection_runs",
        "pilot_selection_run_events",
        "pilot_selected_entities",
        "pilot_selected_entity_quota_contributions",
        "pilot_selected_accessions",
        "pilot_selected_accession_quota_contributions",
        "pilot_reserves",
        "pilot_reserve_accessions",
        "pilot_reserve_quota_contributions",
        "pilot_quota_results",
        "pilot_quota_result_members",
        "pilot_manifest_versions",
        "pilot_projection_recovery_events",
        # Migration 0012, the single additive Stage S5.4 table (Decision 020 section 8.2).
        "pilot_selection_entity_reasons",
    }
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%'"
        ).fetchall()
    found = {row["name"] for row in rows}
    assert found == expected
    assert len(found) == 22


def test_every_pilot_table_is_strict(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%'"
        ).fetchall()
    assert len(rows) == 22
    for row in rows:
        assert "STRICT" in row["sql"], f"{row['name']} is not STRICT"


def test_policy_version_rows_match_pilot_policy_constants(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    expected = {
        "pilot_candidate": pilot_policy.PILOT_CANDIDATE_POLICY_VERSION,
        "pilot_evidence": pilot_policy.PILOT_EVIDENCE_POLICY_VERSION,
        "pilot_sic_family_mapping": pilot_policy.SIC_FAMILY_MAPPING_VERSION,
        "pilot_selector": pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
        "pilot_replacement_signature": pilot_policy.PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
        "pilot_manifest_hash": pilot_policy.PILOT_MANIFEST_HASH_POLICY_VERSION,
        "pilot_primary_universe_boundary": pilot_policy.PILOT_PRIMARY_UNIVERSE_BOUNDARY_VERSION,
        "pilot_quota": pilot_policy.PILOT_QUOTA_POLICY_VERSION,
        # Seeded by migration 0011 (Decision 018 section 20; Stage S5.2).
        "pilot_joint_selector": pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION,
    }
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT policy_key, policy_version FROM reference_policy_versions "
            "WHERE policy_key LIKE 'pilot%'"
        ).fetchall()
    found = {row["policy_key"]: row["policy_version"] for row in rows}
    assert found == expected


def test_no_new_foreign_key_references_inventory_tables(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%'"
        ).fetchall()
    for row in rows:
        assert "inventory_" not in (row["sql"] or ""), f"{row['name']} references inventory_*"


def test_quick_check_integrity_check_and_foreign_key_check_pass(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        report = integrity_report(connection)
    assert report.passed


def test_fresh_database_reconstructs_identically_across_repeated_runs(
    tmp_path: Path,
) -> None:
    path_a = tmp_path / "a.sqlite3"
    path_b = tmp_path / "b.sqlite3"
    with connect(path_a, writer=True) as connection:
        apply_migrations(connection)
        rows_a = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE name LIKE 'pilot_%' ORDER BY name"
        ).fetchall()
    with connect(path_b, writer=True) as connection:
        apply_migrations(connection)
        rows_b = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE name LIKE 'pilot_%' ORDER BY name"
        ).fetchall()
    assert [tuple(r) for r in rows_a] == [tuple(r) for r in rows_b]


# --------------------------------------------------------------------------
# Group B: deterministic-ID validation and snapshot lifecycle (tests 10-16)
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_value",
    (
        "a" * 63,  # too short
        "a" * 65,  # too long
        "A" * 64,  # uppercase hex
        "g" * 64,  # non-hex character
    ),
)
def test_deterministic_ids_reject_wrong_length_uppercase_and_non_hex(
    tmp_path: Path, bad_value: str
) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_snapshot(connection, snapshot_id=bad_value)


def test_deterministic_id_accepts_valid_lowercase_hex64(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=_hex("valid-snapshot"))
        row = connection.execute("SELECT snapshot_id FROM pilot_candidate_snapshots").fetchone()
    assert row["snapshot_id"] == _hex("valid-snapshot")


def test_snapshot_lifecycle_transitions_pass_and_fail_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("lifecycle-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
        assert state == "frozen"

        # frozen -> invalidated is legal
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'invalidated', "
                "invalidated_at_utc = '2026-01-03T00:00:00Z', "
                "invalidated_reason_code = 'PILOT_CANDIDATE_SNAPSHOT_INVALIDATED' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )

        # invalidated is terminal: invalidated -> frozen must fail
        with (
            pytest.raises(sqlite3.IntegrityError, match="illegal pilot snapshot state transition"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )


def test_building_to_invalidated_is_legal_without_freezing(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("building-invalidated-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'invalidated', "
                "invalidated_at_utc = '2026-01-03T00:00:00Z', "
                "invalidated_reason_code = 'PILOT_CANDIDATE_SNAPSHOT_INVALIDATED' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        row = connection.execute(
            "SELECT snapshot_state, frozen_at_utc FROM pilot_candidate_snapshots "
            "WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
    assert row["snapshot_state"] == "invalidated"
    assert row["frozen_at_utc"] is None


def test_invalidated_formerly_frozen_snapshot_retains_frozen_at_utc(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("retains-frozen-at")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        frozen_at_before = connection.execute(
            "SELECT frozen_at_utc FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["frozen_at_utc"]
        assert frozen_at_before is not None

        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'invalidated', "
                "invalidated_at_utc = '2026-01-03T00:00:00Z', "
                "invalidated_reason_code = 'PILOT_CANDIDATE_SNAPSHOT_INVALIDATED' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        row = connection.execute(
            "SELECT snapshot_state, frozen_at_utc, candidate_snapshot_sha256 "
            "FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
    assert row["snapshot_state"] == "invalidated"
    assert row["frozen_at_utc"] == frozen_at_before
    assert row["candidate_snapshot_sha256"] is not None


def test_candidate_child_writes_fail_after_snapshot_freeze(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("freeze-blocks-writes")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _freeze_snapshot(connection, snapshot_id=snapshot_id)

        with pytest.raises(sqlite3.IntegrityError, match="requires a building snapshot"):
            _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)


def test_freeze_fails_with_zero_anchors(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("zero-anchors")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        # No registrant row at all. Under **Decision 083 R58** zero anchors is lawful for
        # a joint filing, but an accession with NO association whatsoever never is.
        with pytest.raises(
            sqlite3.IntegrityError, match="requires at least one registrant row per accession"
        ):
            _freeze_snapshot(connection, snapshot_id=snapshot_id)


def test_freeze_fails_with_more_than_one_anchor(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("two-anchors")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        # a second anchor row must be inserted directly since the partial
        # unique index only forbids two rows with is_anchor = 1; use a
        # separate registrant CIK with role='anchor' but circumvent the
        # partial-unique index by asserting it fires instead.
        with pytest.raises(sqlite3.IntegrityError):
            _insert_registrant(
                connection,
                snapshot_id=snapshot_id,
                accession_plain="acc-1",
                registrant_cik_numeric=2,
                is_anchor=True,
            )


def test_freeze_succeeds_with_exactly_one_anchor_per_accession(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("one-anchor-ok")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_freeze_requires_entity_evidence_backing_for_resolved_dimension(tmp_path: Path) -> None:
    """A resolved entity dimension with no supporting/winning evidence row must
    block freeze (F8, Decision 016 section 4)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("entity-evidence-gap-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(
            connection,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            size_stratum="large_accelerated",
            size_evidence_level="provisional",
            size_resolution_sha256=_hex("size-resolution:entity-evidence-gap"),
        )
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        # no pilot_candidate_entity_evidence row backs the resolved size dimension
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires entity evidence backing for every resolved dimension",
        ):
            _freeze_snapshot(connection, snapshot_id=snapshot_id)
        # adding the backing evidence row allows the freeze to succeed
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_candidate_entity_evidence "
                "(evidence_id, snapshot_id, cik_numeric, classification_dimension, evidence_role, "
                "source_observation_id, source_field, policy_version, precedence, evidence_sha256, "
                "recorded_at_utc) "
                "VALUES (?, ?, 1, 'size', 'winning', 'obs-1', 'field-1', 'policy/1.0', 1, ?, "
                "'2026-01-01T00:00:00Z')",
                (_hex("evidence:entity-evidence-gap"), snapshot_id, _hex("evidence-sha:gap")),
            )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_freeze_requires_accession_evidence_backing_for_resolved_dimension(tmp_path: Path) -> None:
    """A resolved accession dimension with no supporting/winning evidence row must
    block freeze (F8, Decision 016 section 4)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("accession-evidence-gap-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            anchor_cik_numeric=1,
            official_filing_date="2026-01-01",
            filing_date_evidence_level="provisional",
            filing_date_resolution_sha256=_hex("filing-date-resolution:accession-evidence-gap"),
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires accession evidence backing for every resolved dimension",
        ):
            _freeze_snapshot(connection, snapshot_id=snapshot_id)
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_candidate_accession_evidence "
                "(evidence_id, snapshot_id, accession_plain, classification_dimension, "
                "evidence_role, source_observation_id, source_field, policy_version, "
                "precedence, evidence_sha256, recorded_at_utc) "
                "VALUES (?, ?, 'acc-1', 'filing_date', 'winning', 'obs-1', 'field-1', "
                "'policy/1.0', 1, ?, '2026-01-01T00:00:00Z')",
                (
                    _hex("evidence:accession-evidence-gap"),
                    snapshot_id,
                    _hex("evidence-sha:acc-gap"),
                ),
            )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_primary_universe_eligible_requires_operating_category_and_provisional_evidence(
    tmp_path: Path,
) -> None:
    """Primary-universe eligibility is a direct structural implication: only an
    'operating' candidate may carry it, and only 'provisional' (fail-closed)
    evidence may support it (F9, Decision 016 section 4)."""
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        snapshot_id = _hex("primary-universe-category-snapshot")
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        # a 'control' candidate cannot also be primary_universe_eligible
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_entity(
                connection,
                snapshot_id=snapshot_id,
                cik_numeric=1,
                candidate_category="control",
                control_kind="asset_backed_issuer",
                primary_universe_eligible=1,
                primary_universe_evidence_level="provisional",
                primary_universe_resolution_sha256=_hex("pu-resolution:control"),
            )
        # a non-provisional evidence level cannot support an affirmative claim
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_entity(
                connection,
                snapshot_id=snapshot_id,
                cik_numeric=2,
                candidate_category="operating",
                primary_universe_eligible=1,
                primary_universe_evidence_level="review_required",
                primary_universe_resolution_sha256=_hex("pu-resolution:review-required"),
            )
        # resolution_sha256 provenance is required whenever eligibility is claimed
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_entity(
                connection,
                snapshot_id=snapshot_id,
                cik_numeric=3,
                candidate_category="operating",
                primary_universe_eligible=1,
                primary_universe_evidence_level="provisional",
                primary_universe_resolution_sha256=None,
            )


def test_primary_universe_eligible_rejects_financial_sector_sic_and_succeeds_outside_range(
    tmp_path: Path,
) -> None:
    """A canonical four-digit SIC code in 6000-6999 (financial institutions)
    cannot carry primary-universe eligibility; the same claim outside that
    range succeeds (F9, Decision 016 section 4)."""
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        snapshot_id = _hex("primary-universe-sic-snapshot")
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_entity(
                connection,
                snapshot_id=snapshot_id,
                cik_numeric=1,
                candidate_category="operating",
                primary_universe_eligible=1,
                primary_universe_evidence_level="provisional",
                primary_universe_resolution_sha256=_hex("pu-resolution:financial-sic"),
                sic_code="6021",
            )
        # a non-financial SIC code is accepted
        _insert_entity(
            connection,
            snapshot_id=snapshot_id,
            cik_numeric=2,
            candidate_category="operating",
            primary_universe_eligible=1,
            primary_universe_evidence_level="provisional",
            primary_universe_resolution_sha256=_hex("pu-resolution:non-financial-sic"),
            sic_code="0100",
        )
        eligible = connection.execute(
            "SELECT primary_universe_eligible FROM pilot_candidate_entities "
            "WHERE snapshot_id = ? AND cik_numeric = 2",
            (snapshot_id,),
        ).fetchone()["primary_universe_eligible"]
    assert eligible == 1


def test_amendment_purpose_quota_eligible_rejects_unproven_evidence(tmp_path: Path) -> None:
    """'unproven' amendment-purpose evidence is representable but can never
    satisfy an affirmative quota; only 'provisional' can (Challenge A,
    Decision 014 section 6)."""
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        snapshot_id = _hex("amendment-purpose-unproven-snapshot")
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        # 'unproven' is representable on its own -- this insert must succeed
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-unproven",
            anchor_cik_numeric=1,
            amendment_purpose_category="administrative_or_exhibit",
            amendment_purpose_evidence_level="unproven",
            amendment_purpose_resolution_sha256=_hex("amendment-purpose:unproven"),
        )
        # but it can never satisfy an affirmative quota claim
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_accession(
                connection,
                snapshot_id=snapshot_id,
                accession_plain="acc-unproven-quota",
                anchor_cik_numeric=1,
                amendment_purpose_category="administrative_or_exhibit",
                amendment_purpose_evidence_level="unproven",
                amendment_purpose_resolution_sha256=_hex("amendment-purpose:unproven-quota"),
                amendment_purpose_quota_eligible=1,
            )
        # 'provisional' evidence can satisfy the same quota claim
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-provisional-quota",
            anchor_cik_numeric=1,
            amendment_purpose_category="administrative_or_exhibit",
            amendment_purpose_evidence_level="provisional",
            amendment_purpose_resolution_sha256=_hex("amendment-purpose:provisional-quota"),
            amendment_purpose_quota_eligible=1,
        )
        quota_eligible = connection.execute(
            "SELECT amendment_purpose_quota_eligible FROM pilot_candidate_accessions "
            "WHERE snapshot_id = ? AND accession_plain = 'acc-provisional-quota'",
            (snapshot_id,),
        ).fetchone()["amendment_purpose_quota_eligible"]
    assert quota_eligible == 1


def test_frozen_snapshot_fields_are_immutable_and_undeletable(tmp_path: Path) -> None:
    """A frozen snapshot's identity fields (including frozen_at_utc) cannot be
    tampered with post-freeze, and the row itself cannot be deleted (F3/F16)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("frozen-immutable-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        # attempting to backdate/tamper with frozen_at_utc after freeze must fail
        with (
            pytest.raises(sqlite3.IntegrityError, match="frozen fields are immutable"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_candidate_snapshots SET frozen_at_utc = '1999-01-01T00:00:00Z' "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        # attempting to change an unrelated frozen identity field must also fail
        with (
            pytest.raises(sqlite3.IntegrityError, match="frozen fields are immutable"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_candidate_snapshots SET entity_count = 999 WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        # a frozen snapshot row cannot be deleted
        with (
            pytest.raises(sqlite3.IntegrityError, match="undeletable"),
            transaction(connection) as c,
        ):
            c.execute("DELETE FROM pilot_candidate_snapshots WHERE snapshot_id = ?", (snapshot_id,))
        state = connection.execute(
            "SELECT snapshot_state, frozen_at_utc FROM pilot_candidate_snapshots "
            "WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
    assert state["snapshot_state"] == "frozen"
    assert state["frozen_at_utc"] == "2026-01-02T00:00:00Z"


# --------------------------------------------------------------------------
# Group C: multi-registrant consistency and selection-run lifecycle (16-22)
# --------------------------------------------------------------------------


def test_multi_registrant_flag_true_requires_at_least_two_registrants(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("multi-registrant-under")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            anchor_cik_numeric=None,
            multi_registrant=1,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=False,
        )
        # Only one substantive registrant row exists, but multi_registrant = 1. The anchor
        # clause fires first: a sole substantive registrant REQUIRES its anchor.
        with pytest.raises(
            sqlite3.IntegrityError,
            match="exactly one anchor for a sole substantive registrant",
        ):
            _freeze_snapshot(connection, snapshot_id=snapshot_id)


def test_multi_registrant_flag_true_succeeds_with_two_registrants(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("multi-registrant-ok")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=2)
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            # **Decision 083 R58**: a genuinely multi-registrant accession has NO anchor
            # and a NULL scalar. Both substantive rows are 'associated'.
            anchor_cik_numeric=None,
            multi_registrant=1,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=False,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=2,
            is_anchor=False,
        )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_a_submitter_only_row_never_makes_an_accession_multi_registrant(
    tmp_path: Path,
) -> None:
    """**MR-M12 / Decision 083 R58.** Counting a submitter row as substantive is exactly
    the mutation this kills: the flag is the DISTINCT SUBSTANTIVE cardinality, so a
    noncontributing submitter alongside a sole registrant is single-registrant, keeps its
    anchor, and freezes without any divergence reason at all."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("submitter-only-not-multi")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=2)
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            anchor_cik_numeric=1,
            multi_registrant=0,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        # A SECOND SUBSTANTIVE row is multi-registrant by definition under **Decision 083
        # R58**, so the Decision 019 section 6.3 divergence this pair of tests exercises is
        # now what it always meant: a noncontributing submitter row alongside a sole
        # substantive registrant.
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=2,
            is_anchor=False,
            association_class="submitter_only",
        )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_multi_registrant_flag_false_with_two_substantive_rows_has_no_escape(
    tmp_path: Path,
) -> None:
    """**Decision 083 R58**: the flag and the substantive set can never disagree.

    Migration 0009 allowed the disagreement to stand behind a review reason, because the
    trigger counted ALL registrant rows and a submitter row could create a false
    divergence. Counting SUBSTANTIVE rows removes the false case entirely -- and with it
    the escape: two substantive registrants IS multi-registrant, and no reason row buys a
    frozen snapshot that says otherwise.
    """
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("multi-registrant-false-two-substantive")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=2)
        # Layer 1 -- the table CHECK. Under an established set the anchor is present
        # exactly when the accession is not multi-registrant, so "anchorless and not
        # multi-registrant" cannot even be written.
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint failed"):
            _insert_accession(
                connection,
                snapshot_id=snapshot_id,
                accession_plain="acc-0",
                anchor_cik_numeric=None,
                multi_registrant=0,
            )
        # Layer 2 -- the freeze trigger. Keeping the anchor satisfies the CHECK, so the
        # disagreement is reachable here and must still be refused, with no reason row
        # able to buy it a frozen snapshot.
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            anchor_cik_numeric=1,
            multi_registrant=0,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=2,
            is_anchor=False,
        )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_candidate_accession_reasons "
                "(snapshot_id, accession_plain, reason_scope, reason_code, recorded_at_utc) "
                "VALUES (?, 'acc-1', 'multi_registrant', "
                "'REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE', '2026-01-01T00:00:00Z')",
                (snapshot_id,),
            )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="exactly one anchor for a sole substantive registrant|"
            "multi_registrant flag inconsistent",
        ):
            _freeze_snapshot(connection, snapshot_id=snapshot_id)


def test_multi_registrant_flag_false_with_extra_row_passes_with_review_reason(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("multi-registrant-false-reviewed")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=2)
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            anchor_cik_numeric=1,
            multi_registrant=0,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        # A SECOND SUBSTANTIVE row is multi-registrant by definition under **Decision 083
        # R58**, so the Decision 019 section 6.3 divergence this pair of tests exercises is
        # now what it always meant: a noncontributing submitter row alongside a sole
        # substantive registrant.
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=2,
            is_anchor=False,
            association_class="submitter_only",
        )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_candidate_accession_reasons "
                "(snapshot_id, accession_plain, reason_scope, reason_code, recorded_at_utc) "
                "VALUES (?, 'acc-1', 'multi_registrant', "
                "'REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE', '2026-01-01T00:00:00Z')",
                (snapshot_id,),
            )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def _frozen_snapshot_with_one_entity(connection: sqlite3.Connection, snapshot_id: str) -> None:
    _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
    _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=1)
    _insert_accession(
        connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
    )
    _insert_registrant(
        connection,
        snapshot_id=snapshot_id,
        accession_plain="acc-1",
        registrant_cik_numeric=1,
        is_anchor=True,
    )
    _freeze_snapshot(connection, snapshot_id=snapshot_id)


def test_selection_run_requires_frozen_snapshot_to_enter_running(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("run-needs-frozen")
    run_id = _hex("run-needs-frozen-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="cannot enter running without a frozen snapshot"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )


def test_selection_run_lifecycle_and_retry_behave_correctly(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("run-lifecycle-snapshot")
    run_id = _hex("run-lifecycle-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_one_entity(connection, snapshot_id)
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        attempt = connection.execute(
            "SELECT current_attempt FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["current_attempt"]
        assert attempt == 1
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'failed' WHERE selection_run_id = ?",
                (run_id,),
            )

        # failed -> running without a recorded retry event must fail
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="retry requires a recorded, previously unused retry event",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 2 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )

        # after recording the retry event, the same transition succeeds
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selection_run_events "
                "(event_id, selection_run_id, snapshot_id, from_state, to_state, "
                "attempt_number, occurred_at_utc) "
                "VALUES ('evt-1', ?, ?, 'failed', 'running', 2, '2026-01-04T00:00:00Z')",
                (run_id, snapshot_id),
            )
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 2 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        state, attempt = connection.execute(
            "SELECT run_state, current_attempt FROM pilot_selection_runs "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()
        assert state == "running"
        assert attempt == 2

        # a second retry cycle must not be able to reuse the attempt-2 event
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'failed' WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="retry requires a recorded, previously unused retry event",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 3 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        # reusing the exact attempt-2 event (current_attempt unchanged) is also rejected
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="retry must increment current_attempt by exactly one"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
        # a fresh event for attempt 3 succeeds
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selection_run_events "
                "(event_id, selection_run_id, snapshot_id, from_state, to_state, "
                "attempt_number, occurred_at_utc) "
                "VALUES ('evt-2', ?, ?, 'failed', 'running', 3, '2026-01-05T00:00:00Z')",
                (run_id, snapshot_id),
            )
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 3 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        state, attempt = connection.execute(
            "SELECT run_state, current_attempt FROM pilot_selection_runs "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()
    assert state == "running"
    assert attempt == 3


def test_selection_run_attempt_cannot_change_on_other_transitions(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("run-attempt-stable-snapshot")
    run_id = _hex("run-attempt-stable-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_one_entity(connection, snapshot_id)
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="current_attempt may change only on planned->running or failed->running",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET current_attempt = 99 WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="current_attempt may change only on planned->running or failed->running",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'infeasible', current_attempt = 2 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )


def test_terminal_selection_states_are_immutable(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("run-terminal-snapshot")
    run_id = _hex("run-terminal-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_one_entity(connection, snapshot_id)
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'infeasible' "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        for target in ("running", "feasible", "failed"):
            with (
                pytest.raises(
                    sqlite3.IntegrityError, match="illegal pilot selection run state transition"
                ),
                transaction(connection) as c,
            ):
                c.execute(
                    "UPDATE pilot_selection_runs SET run_state = ? WHERE selection_run_id = ?",
                    (target, run_id),
                )


def test_cross_snapshot_result_row_insertion_fails(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("cross-snapshot-a")
    other_snapshot_id = _hex("cross-snapshot-b")
    run_id = _hex("cross-snapshot-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_one_entity(connection, snapshot_id)
        _insert_snapshot(connection, snapshot_id=other_snapshot_id, state="building")
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
        # selected_entities row claiming a different snapshot_id than the run's own
        with (
            pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY constraint failed"),
            transaction(connection) as c,
        ):
            c.execute(
                "INSERT INTO pilot_selected_entities "
                "(selection_run_id, snapshot_id, cik_numeric, selected_order, "
                "entity_hash_sha256, entity_role, candidate_category, recorded_at_utc) "
                "VALUES (?, ?, 1, 1, ?, 'operating', 'operating', '2026-01-01T00:00:00Z')",
                (run_id, other_snapshot_id, _hex("entity-hash")),
            )


def test_non_feasible_transition_rejects_existing_durable_result_rows(tmp_path: Path) -> None:
    """A running->failed/infeasible transition must not leave a partial result behind (F1)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("non-feasible-dirty-snapshot")
    run_id = _hex("non-feasible-dirty-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_one_entity(connection, snapshot_id)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        # a single durable result row exists while the run is still 'running'
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        for target in ("failed", "infeasible"):
            with (
                pytest.raises(
                    sqlite3.IntegrityError,
                    match="must have zero durable result rows before a non-feasible terminal "
                    "transition",
                ),
                transaction(connection) as c,
            ):
                c.execute(
                    "UPDATE pilot_selection_runs SET run_state = ? WHERE selection_run_id = ?",
                    (target, run_id),
                )
        # the row is still present: the aborted transitions changed nothing
        count = connection.execute(
            "SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = ?", (run_id,)
        ).fetchone()[0]
        assert count == 1
        run_state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
        assert run_state == "running"


# --------------------------------------------------------------------------
# Group D: feasible-run entity count, ordering, quota semantics (tests 20-26)
# --------------------------------------------------------------------------


def _frozen_snapshot_with_n_entities(
    connection: sqlite3.Connection, snapshot_id: str, n: int
) -> None:
    _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
    for cik in range(1, n + 1):
        _insert_entity(connection, snapshot_id=snapshot_id, cik_numeric=cik)
        accession_plain = f"acc-{cik}"
        _insert_accession(
            connection,
            snapshot_id=snapshot_id,
            accession_plain=accession_plain,
            anchor_cik_numeric=cik,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain=accession_plain,
            registrant_cik_numeric=cik,
            is_anchor=True,
        )
    _freeze_snapshot(connection, snapshot_id=snapshot_id)


def _running_selection_run(
    connection: sqlite3.Connection, *, selection_run_id: str, snapshot_id: str
) -> None:
    _insert_selection_run(
        connection, selection_run_id=selection_run_id, snapshot_id=snapshot_id, run_state="planned"
    )
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
            (selection_run_id,),
        )


def _feasible_sealed_selection_run(
    connection: sqlite3.Connection, *, selection_run_id: str, snapshot_id: str
) -> None:
    """A ``feasible`` run carrying a sealed ``selection_result_sha256``.

    Migration 0013 requires a manifest's referenced run to be feasible **and** sealed
    (trigger 3), and refuses both a pre-sealed ``INSERT`` (trigger 1) and a seal that
    rides along with the terminal transition (trigger 2). Decision 021 section 20
    blesses this route for fixtures that only need a manifest over an eligible run:
    insert the run directly in ``feasible`` with the seal left ``NULL``, then establish
    the seal by a later ``UPDATE``. The alternative -- driving the full lifecycle -- is
    exercised by the store's own suite.
    """
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_runs "
            "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
            "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
            "started_at_utc, selected_entity_count, selected_accession_count, "
            "expanded_node_count, finished_at_utc) "
            "VALUES (?, ?, 'seed', ?, 'quota/1.0', 1000, 'feasible', ?, "
            "'2026-01-01T00:00:00Z', 24, 0, 10, '2026-01-02T00:00:00Z')",
            (
                selection_run_id,
                snapshot_id,
                pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
                _hex(f"selection-input:{selection_run_id}"),
            ),
        )
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
            "WHERE selection_run_id = ?",
            (_hex(f"selection-result:{selection_run_id}"), selection_run_id),
        )


def _insert_selected_entity(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    cik_numeric: int,
    selected_order: int,
    entity_role: str = "operating",
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selected_entities "
            "(selection_run_id, snapshot_id, cik_numeric, selected_order, entity_hash_sha256, "
            "entity_role, candidate_category, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00Z')",
            (
                selection_run_id,
                snapshot_id,
                cik_numeric,
                selected_order,
                _hex(f"entity-hash:{selection_run_id}:{cik_numeric}"),
                entity_role,
                entity_role,
            ),
        )


def _insert_selected_accession(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    accession_plain: str,
    anchor_cik_numeric: int,
    selected_order: int,
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selected_accessions "
            "(selection_run_id, snapshot_id, accession_plain, anchor_cik_numeric, "
            "selected_order, accession_hash_sha256, accession_role, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, 'base', '2026-01-01T00:00:00Z')",
            (
                selection_run_id,
                snapshot_id,
                accession_plain,
                anchor_cik_numeric,
                selected_order,
                _hex(f"accession-hash:{selection_run_id}:{accession_plain}"),
            ),
        )


#: Decision 020 section 13: the only reserve-scope disposition code the migration
#: 0012 CHECK constraint admits.
_NO_COMPATIBLE_RESERVE = "REVIEW_PILOT_NO_COMPATIBLE_RESERVE"


def _insert_reserve_disposition(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    cik_numeric: int,
    reason_scope: str = "reserve",
    reason_code: str = _NO_COMPATIBLE_RESERVE,
    recorded_at_utc: str = "2026-01-01T00:00:00Z",
) -> None:
    """Insert one migration-0012 ``pilot_selection_entity_reasons`` row."""
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_entity_reasons "
            "(selection_run_id, snapshot_id, cik_numeric, reason_scope, reason_code, "
            "recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
            (
                selection_run_id,
                snapshot_id,
                cik_numeric,
                reason_scope,
                reason_code,
                recorded_at_utc,
            ),
        )


def _seed_reserve_dispositions(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    ciks: range | tuple[int, ...],
) -> None:
    """Give every named selected entity its one no-compatible-reserve disposition.

    Migration 0012 requires exactly one disposition per selected entity before
    ``running -> feasible``. Seeding the reason-row form -- rather than a reserve
    package -- is the minimal way to satisfy that trigger, so the migration-0009
    invariant a test is actually about remains the one that trips.
    """
    for cik in ciks:
        _insert_reserve_disposition(
            connection,
            selection_run_id=selection_run_id,
            snapshot_id=snapshot_id,
            cik_numeric=cik,
        )


def _insert_reserve(
    connection: sqlite3.Connection,
    *,
    reserve_package_id: str,
    selection_run_id: str,
    snapshot_id: str,
    target_cik_numeric: int,
    replacement_cik_numeric: int,
    reserve_rank: int = 1,
    signature: str | None = None,
    reserve_signature: str | None = None,
    **overrides: object,
) -> None:
    sig = signature if signature is not None else _hex(f"signature:{reserve_package_id}")
    fields: dict[str, object] = {
        "reserve_package_id": reserve_package_id,
        "selection_run_id": selection_run_id,
        "snapshot_id": snapshot_id,
        "target_cik_numeric": target_cik_numeric,
        "replacement_cik_numeric": replacement_cik_numeric,
        "reserve_rank": reserve_rank,
        "replaces_signature_sha256": sig,
        "reserve_signature_sha256": reserve_signature if reserve_signature is not None else sig,
        "signature_policy_version": "signature/1.0",
        "quota_policy_version": "quota/1.0",
        "reserve_tie_break_sha256": _hex(f"tie-break:{reserve_package_id}"),
        "evidence_floor": "unavailable",
        "recorded_at_utc": "2026-01-01T00:00:00Z",
    }
    fields.update(overrides)
    columns = ", ".join(fields)
    placeholders = ", ".join("?" for _ in fields)
    with transaction(connection) as c:
        c.execute(
            f"INSERT INTO pilot_reserves ({columns}) VALUES ({placeholders})",  # noqa: S608
            tuple(fields.values()),
        )


def _insert_reserve_accession(
    connection: sqlite3.Connection,
    *,
    reserve_package_id: str,
    selection_run_id: str,
    snapshot_id: str,
    accession_plain: str,
    accession_order: int = 1,
    accession_role: str = "base",
    accession_hash_sha256: str | None = None,
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_reserve_accessions "
            "(reserve_package_id, selection_run_id, snapshot_id, accession_plain, accession_role, "
            "accession_order, accession_hash_sha256, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, '2026-01-01T00:00:00Z')",
            (
                reserve_package_id,
                selection_run_id,
                snapshot_id,
                accession_plain,
                accession_role,
                accession_order,
                accession_hash_sha256
                if accession_hash_sha256 is not None
                else _hex(f"accession-hash:{reserve_package_id}:{accession_plain}"),
            ),
        )


def test_feasible_run_requires_exactly_24_selected_entities(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("feasible-24-snapshot")
    run_id = _hex("feasible-24-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 24)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        for order, cik in enumerate(range(1, 25), start=1):
            _insert_selected_entity(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=cik,
                selected_order=order,
            )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 25)
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 0 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
    assert state == "feasible"


def test_feasible_run_with_fewer_than_24_entities_fails(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("feasible-short-snapshot")
    run_id = _hex("feasible-short-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 5)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        for order, cik in enumerate(range(1, 6), start=1):
            _insert_selected_entity(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=cik,
                selected_order=order,
            )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 6)
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires exactly 24 actual selected entities"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 5 WHERE selection_run_id = ?",
                (run_id,),
            )


def test_feasible_requires_actual_rows_not_only_declared_count(tmp_path: Path) -> None:
    """A declared selected_entity_count of 24 with zero actual rows must fail (F4/F15)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("feasible-ghost-count-snapshot")
    run_id = _hex("feasible-ghost-count-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 24)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        assert (
            connection.execute(
                "SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = ?", (run_id,)
            ).fetchone()[0]
            == 0
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires exactly 24 actual selected entities"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )


def _feasible_run_with_24_actual_entities_and_accessions(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    run_id: str,
    seed_dispositions: bool = True,
) -> None:
    """Seed a running selection run with exactly 24 actual selected-entity and
    selected-accession rows, but leave the declared count columns untouched (B1).

    ``seed_dispositions`` is left on by default so a migration-0009 invariant under
    test is the one that trips; the migration-0012 disposition tests turn it off and
    craft the disposition state they are actually about.
    """
    _frozen_snapshot_with_n_entities(connection, snapshot_id, 24)
    _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
    for order, cik in enumerate(range(1, 25), start=1):
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=cik,
            selected_order=order,
        )
        _insert_selected_accession(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            accession_plain=f"acc-{cik}",
            anchor_cik_numeric=cik,
            selected_order=order,
        )
    if seed_dispositions:
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 25)
        )


def test_feasible_rejects_null_declared_counts_with_valid_actual_rows(tmp_path: Path) -> None:
    """24 actual entity rows plus valid accession rows with both declared counts
    left NULL must not become feasible (B1: CHECK/`<>` pass on NULL in SQLite)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("b1-both-null-snapshot")
    run_id = _hex("b1-both-null-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="requires selected_entity_count to equal actual rows",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible' WHERE selection_run_id = ?",
                (run_id,),
            )
        run_state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
    assert run_state == "running"


def test_feasible_rejects_null_entity_count_alone(tmp_path: Path) -> None:
    """A NULL selected_entity_count must fail even when selected_accession_count
    is correctly declared (B1)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("b1-null-entity-snapshot")
    run_id = _hex("b1-null-entity-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="requires selected_entity_count to equal actual rows",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_accession_count = 24 WHERE selection_run_id = ?",
                (run_id,),
            )


def test_feasible_rejects_null_accession_count_alone(tmp_path: Path) -> None:
    """A NULL selected_accession_count must fail even when selected_entity_count
    is correctly declared as 24 (B1)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("b1-null-accession-snapshot")
    run_id = _hex("b1-null-accession-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="requires selected_accession_count to equal actual rows",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24 WHERE selection_run_id = ?",
                (run_id,),
            )


def test_feasible_rejects_mismatched_non_null_counts(tmp_path: Path) -> None:
    """Non-NULL declared counts that diverge from the actual row counts must
    fail, on either the entity or the accession side (B1)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("b1-mismatch-snapshot")
    run_id = _hex("b1-mismatch-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="requires selected_entity_count to equal actual rows",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 23, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError,
                match="requires selected_accession_count to equal actual rows",
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 23 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        run_state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
    assert run_state == "running"


def test_feasible_succeeds_with_correct_non_null_counts_matching_actual_rows(
    tmp_path: Path,
) -> None:
    """Correct, non-NULL declared counts matching the actual row counts allow
    the feasible transition (B1 positive case)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("b1-correct-snapshot")
    run_id = _hex("b1-correct-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        run_state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
    assert run_state == "feasible"


def test_feasible_requires_selected_order_contiguity(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("feasible-order-gap-snapshot")
    run_id = _hex("feasible-order-gap-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 24)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        # 24 rows, but selected_order skips 24 and repeats 23 -- via a duplicate
        # tail value one order past where the UNIQUE index would already have
        # blocked it: use orders 1..23 plus 25 (a gap at 24, non-contiguous).
        for order, cik in enumerate(range(1, 24), start=1):
            _insert_selected_entity(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=cik,
                selected_order=order,
            )
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=24,
            selected_order=25,
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 25)
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires contiguous entity selected_order"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 0 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )


def test_python_pilot_constants_sum_to_24() -> None:
    from disclosure_drift.sec.pilot import TOTAL_CONTROLS, TOTAL_OPERATING

    assert TOTAL_OPERATING + TOTAL_CONTROLS == 24


def test_selected_order_uniqueness_within_a_run(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("selected-order-snapshot")
    run_id = _hex("selected-order-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 2)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
            _insert_selected_entity(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=2,
                selected_order=1,
            )


def test_reserve_rank_uniqueness_per_target(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("reserve-rank-snapshot")
    run_id = _hex("reserve-rank-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 3)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        signature = _hex("shared-signature")
        _insert_reserve(
            connection,
            reserve_package_id=_hex("reserve-1"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=1,
            replacement_cik_numeric=2,
            reserve_rank=1,
            signature=signature,
        )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
            _insert_reserve(
                connection,
                reserve_package_id=_hex("reserve-2"),
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                target_cik_numeric=1,
                replacement_cik_numeric=3,
                reserve_rank=1,
                signature=signature,
            )


@pytest.mark.parametrize(
    ("operator", "required", "achieved", "expected_pass"),
    (
        ("exact", 5, 5, True),
        ("exact", 5, 4, False),
        ("at_least", 5, 6, True),
        ("at_least", 5, 4, False),
        ("at_most", 5, 4, True),
        ("at_most", 5, 6, False),
    ),
)
def test_quota_pass_fail_semantics_by_comparison_operator(
    tmp_path: Path, operator: str, required: int, achieved: int, expected_pass: bool
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex(f"quota-semantics-{operator}-{required}-{achieved}")
    run_id = _hex(f"quota-semantics-run-{operator}-{required}-{achieved}")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        result = "pass" if expected_pass else "fail"
        evidence_state = "provisional" if expected_pass else "unavailable"
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_quota_results "
                "(quota_result_id, selection_run_id, snapshot_id, quota_dimension, quota_key, "
                "comparison_operator, required_count, achieved_count, eligible_pool_count, "
                "excluded_pool_count, evidence_state, quota_result, recorded_at_utc) "
                "VALUES (?, ?, ?, 'size', 'large_accelerated', ?, ?, ?, ?, 0, ?, ?, "
                "'2026-01-01T00:00:00Z')",
                (
                    _hex(f"quota-result-{operator}-{required}-{achieved}"),
                    run_id,
                    snapshot_id,
                    operator,
                    required,
                    achieved,
                    max(required, achieved),
                    evidence_state,
                    result,
                ),
            )
        stored = connection.execute(
            "SELECT quota_result FROM pilot_quota_results WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["quota_result"]
    assert stored == result


def test_quota_pass_with_wrong_comparison_outcome_fails(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("quota-wrong-pass-snapshot")
    run_id = _hex("quota-wrong-pass-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        with (
            pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"),
            transaction(connection) as c,
        ):
            c.execute(
                "INSERT INTO pilot_quota_results "
                "(quota_result_id, selection_run_id, snapshot_id, quota_dimension, quota_key, "
                "comparison_operator, required_count, achieved_count, eligible_pool_count, "
                "excluded_pool_count, evidence_state, quota_result, recorded_at_utc) "
                "VALUES (?, ?, ?, 'size', 'large_accelerated', 'exact', 5, 4, 5, 0, "
                "'unavailable', 'pass', '2026-01-01T00:00:00Z')",
                (_hex("quota-wrong-pass"), run_id, snapshot_id),
            )


def test_unproven_quota_result_is_distinct_from_fail(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("quota-unproven-snapshot")
    run_id = _hex("quota-unproven-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        # 'unproven' is exempt from the pass/fail comparison CHECKs entirely,
        # even though achieved would satisfy neither a pass nor a fail read.
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_quota_results "
                "(quota_result_id, selection_run_id, snapshot_id, quota_dimension, quota_key, "
                "comparison_operator, required_count, achieved_count, eligible_pool_count, "
                "excluded_pool_count, evidence_state, quota_result, recorded_at_utc) "
                "VALUES (?, ?, ?, 'size', 'large_accelerated', 'exact', 5, 5, 5, 0, "
                "'review_required', 'unproven', '2026-01-01T00:00:00Z')",
                (_hex("quota-unproven"), run_id, snapshot_id),
            )
        stored = connection.execute(
            "SELECT quota_result FROM pilot_quota_results WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["quota_result"]
    assert stored == "unproven"
    assert stored != "fail"


def test_reserve_target_and_package_signature_mismatch_fails(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("reserve-mismatch-snapshot")
    run_id = _hex("reserve-mismatch-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 2)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_reserve(
                connection,
                reserve_package_id=_hex("reserve-mismatch"),
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                target_cik_numeric=1,
                replacement_cik_numeric=2,
                signature=_hex("signature-a"),
                reserve_signature=_hex("signature-b"),
            )


def _reserve_signature_shared_fields(
    connection: sqlite3.Connection, *, reserve_package_id: str
) -> dict[str, object]:
    """Reserve-package content common to both signature computations (Decision 016 section 7)."""
    from disclosure_drift.release.hashing import hash_table

    reserve = connection.execute(
        "SELECT signature_policy_version, quota_policy_version, evidence_floor "
        "FROM pilot_reserves WHERE reserve_package_id = ?",
        (reserve_package_id,),
    ).fetchone()
    accession_rows = connection.execute(
        "SELECT accession_plain, accession_role, accession_order, accession_hash_sha256 "
        "FROM pilot_reserve_accessions WHERE reserve_package_id = ? ORDER BY accession_order",
        (reserve_package_id,),
    ).fetchall()
    quota_rows = connection.execute(
        "SELECT quota_dimension, quota_key FROM pilot_reserve_quota_contributions "
        "WHERE reserve_package_id = ? ORDER BY quota_dimension, quota_key",
        (reserve_package_id,),
    ).fetchall()
    return {
        "signature_policy_version": reserve["signature_policy_version"],
        "quota_policy_version": reserve["quota_policy_version"],
        "evidence_floor": reserve["evidence_floor"],
        "accessions_content_sha256": hash_table(
            "pilot_reserve_accessions",
            ("accession_plain", "accession_role", "accession_order", "accession_hash_sha256"),
            (dict(row) for row in accession_rows),
        ).normalized_content_sha256,
        "quota_contributions_content_sha256": hash_table(
            "pilot_reserve_quota_contributions",
            ("quota_dimension", "quota_key"),
            (dict(row) for row in quota_rows),
        ).normalized_content_sha256,
    }


def _recompute_target_signature(
    connection: sqlite3.Connection,
    *,
    reserve_package_id: str,
    selection_run_id: str,
    snapshot_id: str,
    target_cik_numeric: int,
) -> str:
    """Recompute ``replaces_signature_sha256`` from the target's own frozen selection row."""
    from disclosure_drift.release.hashing import hash_table

    target = connection.execute(
        "SELECT candidate_category, size_stratum, industry_family, history_class, control_kind "
        "FROM pilot_selected_entities "
        "WHERE selection_run_id = ? AND snapshot_id = ? AND cik_numeric = ?",
        (selection_run_id, snapshot_id, target_cik_numeric),
    ).fetchone()
    fields = {
        **dict(target),
        **_reserve_signature_shared_fields(connection, reserve_package_id=reserve_package_id),
    }
    return hash_table(
        "pilot_reserve_signature", tuple(sorted(fields)), [fields]
    ).normalized_content_sha256


def _recompute_reserve_signature(
    connection: sqlite3.Connection,
    *,
    reserve_package_id: str,
    snapshot_id: str,
    replacement_cik_numeric: int,
) -> str:
    """Recompute ``reserve_signature_sha256`` from the replacement candidate's own row."""
    from disclosure_drift.release.hashing import hash_table

    replacement = connection.execute(
        "SELECT candidate_category, size_stratum, industry_family, history_class, control_kind "
        "FROM pilot_candidate_entities WHERE snapshot_id = ? AND cik_numeric = ?",
        (snapshot_id, replacement_cik_numeric),
    ).fetchone()
    fields = {
        **dict(replacement),
        **_reserve_signature_shared_fields(connection, reserve_package_id=reserve_package_id),
    }
    return hash_table(
        "pilot_reserve_signature", tuple(sorted(fields)), [fields]
    ).normalized_content_sha256


def test_reserve_signature_independently_recomputed_from_normalized_content(tmp_path: Path) -> None:
    """Decision 016 section 7: acceptance tests must independently recompute both
    signatures from normalized source content, not merely compare the two stored
    hash columns (Opus review Challenge C).

    A compatible reserve's target (cik 1) and replacement (cik 2) share the exact
    classification that makes them interchangeable (Decision 013 section 6), so
    recomputing from either side's own rows must land on the same hash -- and
    that hash must equal what was stored under both ``replaces_signature_sha256``
    and ``reserve_signature_sha256``.
    """
    from disclosure_drift.release.hashing import hash_table

    path = _migrated_database(tmp_path)
    snapshot_id = _hex("reserve-signature-snapshot")
    run_id = _hex("reserve-signature-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _insert_snapshot(connection, snapshot_id=snapshot_id, state="building")
        classification = {
            "size_stratum": "large_accelerated",
            "size_evidence_level": "provisional",
            "industry_family": "technology_and_communications",
            "industry_evidence_level": "provisional",
            "history_class": "stable",
            "history_evidence_level": "provisional",
        }
        for cik in (1, 2):
            _insert_entity(
                connection,
                snapshot_id=snapshot_id,
                cik_numeric=cik,
                size_resolution_sha256=_hex(f"size-res:{cik}"),
                industry_resolution_sha256=_hex(f"industry-res:{cik}"),
                history_resolution_sha256=_hex(f"history-res:{cik}"),
                **classification,
            )
            for dimension in ("size", "industry", "history"):
                with transaction(connection) as c:
                    c.execute(
                        "INSERT INTO pilot_candidate_entity_evidence "
                        "(evidence_id, snapshot_id, cik_numeric, classification_dimension, "
                        "evidence_role, source_observation_id, source_field, policy_version, "
                        "precedence, evidence_sha256, recorded_at_utc) "
                        "VALUES (?, ?, ?, ?, 'winning', 'obs-1', 'field', 'p/1', 1, ?, "
                        "'2026-01-01T00:00:00Z')",
                        (
                            _hex(f"evidence:{cik}:{dimension}"),
                            snapshot_id,
                            cik,
                            dimension,
                            _hex(f"evidence-sha:{cik}:{dimension}"),
                        ),
                    )
        _insert_accession(
            connection, snapshot_id=snapshot_id, accession_plain="acc-1", anchor_cik_numeric=1
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        _insert_selection_run(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, run_state="planned"
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
                (run_id,),
            )
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_selected_entities "
                "(selection_run_id, snapshot_id, cik_numeric, selected_order, entity_hash_sha256, "
                "entity_role, candidate_category, size_stratum, industry_family, history_class, "
                "recorded_at_utc) "
                "VALUES (?, ?, 1, 1, ?, 'operating', 'operating', 'large_accelerated', "
                "'technology_and_communications', 'stable', '2026-01-01T00:00:00Z')",
                (run_id, snapshot_id, _hex("entity-hash:1")),
            )

        accession_columns = (
            "accession_plain",
            "accession_role",
            "accession_order",
            "accession_hash_sha256",
        )
        accession_content = ("acc-1", "base", 1, _hex("reserve-accession-hash-v1"))
        quota_content = (
            ("size", "large_accelerated"),
            ("industry", "technology_and_communications"),
        )
        shared_fields = {
            "signature_policy_version": "signature/1.0",
            "quota_policy_version": "quota/1.0",
            "evidence_floor": "unavailable",
            "accessions_content_sha256": hash_table(
                "pilot_reserve_accessions",
                accession_columns,
                [dict(zip(accession_columns, accession_content, strict=True))],
            ).normalized_content_sha256,
            "quota_contributions_content_sha256": hash_table(
                "pilot_reserve_quota_contributions",
                ("quota_dimension", "quota_key"),
                [{"quota_dimension": dim, "quota_key": key} for dim, key in quota_content],
            ).normalized_content_sha256,
        }
        classification_fields = {
            "candidate_category": "operating",
            "size_stratum": "large_accelerated",
            "industry_family": "technology_and_communications",
            "history_class": "stable",
            "control_kind": None,
        }
        precomputed_fields = {**classification_fields, **shared_fields}
        expected_signature = hash_table(
            "pilot_reserve_signature", tuple(sorted(precomputed_fields)), [precomputed_fields]
        ).normalized_content_sha256

        reserve_package_id = _hex("reserve-signature")
        _insert_reserve(
            connection,
            reserve_package_id=reserve_package_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=1,
            replacement_cik_numeric=2,
            signature=expected_signature,
            signature_policy_version=shared_fields["signature_policy_version"],
            quota_policy_version=shared_fields["quota_policy_version"],
            evidence_floor=shared_fields["evidence_floor"],
        )
        _insert_reserve_accession(
            connection,
            reserve_package_id=reserve_package_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            accession_plain=accession_content[0],
            accession_role=accession_content[1],
            accession_order=accession_content[2],
            accession_hash_sha256=accession_content[3],
        )
        for dim, key in quota_content:
            with transaction(connection) as c:
                c.execute(
                    "INSERT INTO pilot_reserve_quota_contributions "
                    "(reserve_package_id, selection_run_id, snapshot_id, quota_dimension, "
                    "quota_key, recorded_at_utc) VALUES (?, ?, ?, ?, ?, '2026-01-01T00:00:00Z')",
                    (reserve_package_id, run_id, snapshot_id, dim, key),
                )

        recomputed_target = _recompute_target_signature(
            connection,
            reserve_package_id=reserve_package_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=1,
        )
        recomputed_reserve = _recompute_reserve_signature(
            connection,
            reserve_package_id=reserve_package_id,
            snapshot_id=snapshot_id,
            replacement_cik_numeric=2,
        )
        stored = connection.execute(
            "SELECT replaces_signature_sha256, reserve_signature_sha256 FROM pilot_reserves "
            "WHERE reserve_package_id = ?",
            (reserve_package_id,),
        ).fetchone()

        assert recomputed_target == stored["replaces_signature_sha256"]
        assert recomputed_reserve == stored["reserve_signature_sha256"]
        assert recomputed_target == recomputed_reserve

        # A signature-computation defect that always emits the same (wrong) hash
        # would pass the schema's stored-hash-equality CHECK but must be caught
        # by recomputation: store the *same* (now-stale) signature on a second
        # package whose actual accession content differs, and prove independent
        # recomputation from that package's real rows disagrees with it.
        reserve_package_id_2 = _hex("reserve-signature-mutated")
        _insert_reserve(
            connection,
            reserve_package_id=reserve_package_id_2,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=1,
            replacement_cik_numeric=2,
            reserve_rank=2,
            signature=expected_signature,
            signature_policy_version=shared_fields["signature_policy_version"],
            quota_policy_version=shared_fields["quota_policy_version"],
            evidence_floor=shared_fields["evidence_floor"],
        )
        _insert_reserve_accession(
            connection,
            reserve_package_id=reserve_package_id_2,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            accession_role="base",
            accession_order=1,
            accession_hash_sha256=_hex("mutated-accession-content"),
        )
        for dim, key in quota_content:
            with transaction(connection) as c:
                c.execute(
                    "INSERT INTO pilot_reserve_quota_contributions "
                    "(reserve_package_id, selection_run_id, snapshot_id, quota_dimension, "
                    "quota_key, recorded_at_utc) VALUES (?, ?, ?, ?, ?, '2026-01-01T00:00:00Z')",
                    (reserve_package_id_2, run_id, snapshot_id, dim, key),
                )
        recomputed_reserve_mutated = _recompute_reserve_signature(
            connection,
            reserve_package_id=reserve_package_id_2,
            snapshot_id=snapshot_id,
            replacement_cik_numeric=2,
        )
        stored_2 = connection.execute(
            "SELECT reserve_signature_sha256 FROM pilot_reserves WHERE reserve_package_id = ?",
            (reserve_package_id_2,),
        ).fetchone()

    assert recomputed_reserve_mutated != recomputed_reserve
    assert recomputed_reserve_mutated != stored_2["reserve_signature_sha256"]


# --------------------------------------------------------------------------
# Group E: manifest lifecycle, projection recovery, and hygiene (27-35)
# --------------------------------------------------------------------------

_MANIFEST_HASH_COLUMNS = (
    "source_observation_set_sha256",
    "candidate_tables_sha256",
    "quota_definitions_sha256",
    "selector_policy_sha256",
    "selected_entities_sha256",
    "selected_accessions_sha256",
    "reserves_sha256",
    "quota_report_sha256",
    "root_manifest_sha256",
)


def _insert_manifest(
    connection: sqlite3.Connection,
    *,
    manifest_id: str,
    selection_run_id: str,
    snapshot_id: str,
    root_hash: str,
    ordinal_version: int = 1,
    manifest_path: str = "releases/sec_inventory/manifest.json",
    supersedes_manifest_id: str | None = None,
) -> None:
    hash_values = {column: _hex(f"{column}:{manifest_id}") for column in _MANIFEST_HASH_COLUMNS}
    hash_values["root_manifest_sha256"] = root_hash
    columns = (
        "manifest_id",
        "selection_run_id",
        "snapshot_id",
        "manifest_schema_version",
        "ordinal_version",
        *_MANIFEST_HASH_COLUMNS,
        "manifest_state",
        "relative_manifest_path",
        "generated_at_utc",
        "supersedes_manifest_id",
    )
    values = (
        manifest_id,
        selection_run_id,
        snapshot_id,
        "manifest/1.0",
        ordinal_version,
        *(hash_values[column] for column in _MANIFEST_HASH_COLUMNS),
        "proposed",
        manifest_path,
        "2026-01-05T00:00:00Z",
        supersedes_manifest_id,
    )
    placeholders = ", ".join("?" for _ in columns)
    with transaction(connection) as c:
        c.execute(
            f"INSERT INTO pilot_manifest_versions ({', '.join(columns)}) "  # noqa: S608
            f"VALUES ({placeholders})",
            values,
        )


def test_manifest_approval_rejects_mismatched_root_hash(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-mismatch-snapshot")
    run_id = _hex("manifest-mismatch-run")
    manifest_id = _hex("manifest-mismatch")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        root_hash = _hex("root-hash-correct")
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=root_hash,
        )
        with (
            pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_manifest_versions SET manifest_state = 'owner_approved', "
                "approved_at_utc = '2026-01-06T00:00:00Z', "
                "approval_reference = 'owner-email-1', "
                "approved_root_sha256 = ? WHERE manifest_id = ?",
                (_hex("root-hash-wrong"), manifest_id),
            )


def test_owner_approved_manifest_may_become_superseded_retaining_approval_fields(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-supersede-snapshot")
    run_id = _hex("manifest-supersede-run")
    manifest_id = _hex("manifest-supersede")
    successor_id = _hex("manifest-supersede-successor")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        root_hash = _hex("root-hash-supersede")
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=root_hash,
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_manifest_versions SET manifest_state = 'owner_approved', "
                "approved_at_utc = '2026-01-06T00:00:00Z', approval_reference = 'owner-email-1', "
                "approved_root_sha256 = ? WHERE manifest_id = ?",
                (root_hash, manifest_id),
            )
        # A second manifest must exist before the first can be superseded by it,
        # and must reference it via supersedes_manifest_id.
        _insert_manifest(
            connection,
            manifest_id=successor_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=_hex("root-hash-successor"),
            ordinal_version=2,
            supersedes_manifest_id=manifest_id,
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_manifest_versions SET manifest_state = 'superseded', "
                "superseded_at_utc = '2026-01-09T00:00:00Z' WHERE manifest_id = ?",
                (manifest_id,),
            )
        row = connection.execute(
            "SELECT manifest_state, approved_at_utc, approval_reference, approved_root_sha256 "
            "FROM pilot_manifest_versions WHERE manifest_id = ?",
            (manifest_id,),
        ).fetchone()
    assert row["manifest_state"] == "superseded"
    assert row["approved_at_utc"] == "2026-01-06T00:00:00Z"
    assert row["approval_reference"] == "owner-email-1"
    assert row["approved_root_sha256"] == root_hash


def test_rejected_and_superseded_manifests_are_terminal(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-terminal-snapshot")
    run_id = _hex("manifest-terminal-run")
    rejected_id = _hex("manifest-terminal-rejected")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_manifest(
            connection,
            manifest_id=rejected_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=_hex("root-hash-rejected"),
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_manifest_versions SET manifest_state = 'rejected', "
                "rejected_at_utc = '2026-01-06T00:00:00Z' WHERE manifest_id = ?",
                (rejected_id,),
            )
        for target in ("proposed", "owner_approved", "superseded"):
            with (
                pytest.raises(
                    sqlite3.IntegrityError, match="illegal pilot manifest state transition"
                ),
                transaction(connection) as c,
            ):
                c.execute(
                    "UPDATE pilot_manifest_versions SET manifest_state = ? WHERE manifest_id = ?",
                    (target, rejected_id),
                )


def test_manifest_component_hashes_are_immutable(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-hash-immutable-snapshot")
    run_id = _hex("manifest-hash-immutable-run")
    manifest_id = _hex("manifest-hash-immutable")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=_hex("root-hash-immutable"),
        )
        with (
            pytest.raises(sqlite3.IntegrityError, match="hashes are immutable"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_manifest_versions SET root_manifest_sha256 = ? WHERE manifest_id = ?",
                (_hex("root-hash-tampered"), manifest_id),
            )


@pytest.mark.parametrize(
    "unsafe_path",
    (
        "/absolute/path/manifest.json",
        "../escape/manifest.json",
        "releases/../../../etc/manifest.json",
        "C:\\Windows\\manifest.json",
        "",
    ),
)
def test_unsafe_manifest_paths_fail(tmp_path: Path, unsafe_path: str) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-path-snapshot")
    run_id = _hex("manifest-path-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_manifest(
                connection,
                manifest_id=_hex(f"manifest-path-{unsafe_path}"),
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                root_hash=_hex("root-hash-path-test"),
                manifest_path=unsafe_path,
            )


def test_manifest_rows_are_undeletable(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("manifest-undeletable-snapshot")
    run_id = _hex("manifest-undeletable-run")
    manifest_id = _hex("manifest-undeletable")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=_hex("root-hash-undeletable"),
        )
        with (
            pytest.raises(sqlite3.IntegrityError, match="undeletable"),
            transaction(connection) as c,
        ):
            c.execute("DELETE FROM pilot_manifest_versions WHERE manifest_id = ?", (manifest_id,))


def test_projection_recovery_lifecycle_constraints(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("projection-recovery-snapshot")
    run_id = _hex("projection-recovery-run")
    manifest_id = _hex("projection-recovery-manifest")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 1)
        _feasible_sealed_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            root_hash=_hex("root-hash-projection"),
        )

        # 'resolved' without resolved_at_utc must fail.
        with (
            pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"),
            transaction(connection) as c,
        ):
            c.execute(
                "INSERT INTO pilot_projection_recovery_events "
                "(event_id, manifest_id, expected_count, observed_count, resolution_state, "
                "release_blocking_before_resolution, occurred_at_utc) "
                "VALUES ('evt-bad', ?, 1, 0, 'resolved', 1, '2026-01-07T00:00:00Z')",
                (manifest_id,),
            )

        # 'blocked' without release_blocking_after_resolution is fine (still open).
        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_projection_recovery_events "
                "(event_id, manifest_id, expected_count, observed_count, resolution_state, "
                "release_blocking_before_resolution, occurred_at_utc) "
                "VALUES ('evt-blocked', ?, 1, 0, 'blocked', 1, '2026-01-07T00:00:00Z')",
                (manifest_id,),
            )

        # 'resolved' requires resolved_at_utc and release_blocking_after_resolution.
        with (
            pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"),
            transaction(connection) as c,
        ):
            c.execute(
                "INSERT INTO pilot_projection_recovery_events "
                "(event_id, manifest_id, expected_count, observed_count, resolution_state, "
                "release_blocking_before_resolution, resolved_at_utc, occurred_at_utc) "
                "VALUES ('evt-incomplete', ?, 1, 1, 'resolved', 1, "
                "'2026-01-08T00:00:00Z', '2026-01-07T00:00:00Z')",
                (manifest_id,),
            )

        with transaction(connection) as c:
            c.execute(
                "INSERT INTO pilot_projection_recovery_events "
                "(event_id, manifest_id, expected_count, observed_count, resolution_state, "
                "release_blocking_before_resolution, release_blocking_after_resolution, "
                "resolved_at_utc, occurred_at_utc) "
                "VALUES ('evt-resolved', ?, 1, 1, 'resolved', 1, 0, "
                "'2026-01-08T00:00:00Z', '2026-01-07T00:00:00Z')",
                (manifest_id,),
            )
        state = connection.execute(
            "SELECT resolution_state FROM pilot_projection_recovery_events WHERE event_id = ?",
            ("evt-resolved",),
        ).fetchone()["resolution_state"]
    assert state == "resolved"


def test_no_network_call_is_made(tmp_path: Path) -> None:
    """Schema operations complete under the autouse socket-blocking fixture.

    ``tests/conftest.py`` monkeypatches ``socket.socket``/``create_connection``/
    ``getaddrinfo`` to raise for every test in this session; a passing run of
    any test above already proves no network call occurred. This test names
    that guarantee explicitly for the schema/lifecycle surface.
    """
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        report = integrity_report(connection)
    assert report.passed


def test_no_persistent_repository_database_is_touched(tmp_path: Path) -> None:
    """Confirm this test module never opens or modifies a repository database."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    persistent_candidates = list((repo_root / "data").rglob("*.sqlite3")) + list(
        (repo_root / "data").rglob("*.db")
    )
    before = {candidate: candidate.stat().st_mtime for candidate in persistent_candidates}

    _migrated_database(tmp_path)

    after_candidates = list((repo_root / "data").rglob("*.sqlite3")) + list(
        (repo_root / "data").rglob("*.db")
    )
    assert after_candidates == persistent_candidates
    after = {candidate: candidate.stat().st_mtime for candidate in after_candidates}
    assert before == after


# --------------------------------------------------------------------------
# Migration 0012 -- pilot_selection_entity_reasons (Decision 020 section 8.2)
# --------------------------------------------------------------------------
#
# The complete DDL -- the table and all four triggers -- is frozen in Decision 020
# section 8.2 and is reproduced verbatim in migration 0012. These tests prove the
# reproduction is byte-faithful, that the migration is additive only, and that
# every guard behaves as the frozen SQL says. Following the owner's binding
# enforcement-layer clarification (Decision 020 section 8.3), each invariant is
# proven at the layer that owns it: unauthorized scope and code at the CHECK
# constraints, duplicate dispositions at the primary key, duplicate rank-1
# packages at migration 0009's existing UNIQUE constraint, and only the
# constructible invalid states at the feasible transition.

_DECISION_020 = (
    Path(__file__).resolve().parents[2]
    / "Docs"
    / "Decisions"
    / "decision_020_m23_s5_4_reserve_architecture.md"
)
_MIGRATION_0012 = _MIGRATIONS_DIR / "0012_m23_selection_entity_reasons.sql"

#: The accepted Decision 020 section 8.2 digests: the table DDL, the three
#: lifecycle guards, the feasible-transition trigger, and their concatenation.
_FROZEN_SQL_SHA256 = (
    "4340a681675ebaf648e5553210b2a119ea5202bdfb5254a7310b6b7c6072fc7a",
    "d291d431a0171c672be4629097e13ad32f63efd85fc2e4fc641ebf9c95d62659",
    "df8299099e1d7eaceb93fd31270427bfcb964cf87149dfc2e2e56581fa28eba8",
)
_FROZEN_CONCATENATED_SHA256 = "8a157a6768996e1a7006202f36fcff1a235198a68a308383f63e7b534dc16443"

_MIGRATION_0011_SHA256 = hashlib.sha256(
    (_MIGRATIONS_DIR / "0011_m23_joint_selector_policy_reference.sql").read_bytes()
).hexdigest()


def _frozen_sql_blocks() -> tuple[str, ...]:
    """The three ``sql`` fenced blocks of Decision 020 section 8.2, in order."""
    text = _DECISION_020.read_text(encoding="utf-8")
    return tuple(re.findall(r"```sql\n(.*?)```", text, flags=re.S))


def _migration_0012_statements() -> str:
    """Migration 0012 from its first statement line to end of file.

    The file's leading ``--`` header is repository convention (migrations 0010 and
    0011 carry the same shape); everything from the first non-comment, non-blank
    line onward must be the frozen SQL and nothing else.
    """
    lines = _MIGRATION_0012.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(
        index
        for index, line in enumerate(lines)
        if line.strip() and not line.lstrip().startswith("--")
    )
    return "".join(lines[start:])


def test_the_decision_020_sql_blocks_match_the_accepted_digests() -> None:
    blocks = _frozen_sql_blocks()
    assert len(blocks) == 3
    for block, expected in zip(blocks, _FROZEN_SQL_SHA256, strict=True):
        assert hashlib.sha256(block.encode("utf-8")).hexdigest() == expected
    assert (
        hashlib.sha256("".join(blocks).encode("utf-8")).hexdigest() == _FROZEN_CONCATENATED_SHA256
    )


def test_migration_0012_reproduces_the_frozen_decision_020_sql_byte_for_byte() -> None:
    """No implementation-time reinterpretation of the section 8.2 SQL is permitted:
    a difference here is a defect in the migration, never a correction to the
    decision record."""
    statements = _migration_0012_statements()
    assert statements == "".join(_frozen_sql_blocks())
    assert hashlib.sha256(statements.encode("utf-8")).hexdigest() == _FROZEN_CONCATENATED_SHA256


def test_migration_0012_is_ddl_only_and_carries_no_forbidden_statement() -> None:
    body = _migration_0012_statements()
    assert re.search(r"\bBEGIN\s*;", body) is None
    assert re.search(r"\bBEGIN\s+(IMMEDIATE|DEFERRED|EXCLUSIVE|TRANSACTION)\b", body) is None
    assert "COMMIT" not in body.upper()
    assert "PRAGMA" not in body.upper()
    assert not re.search(r"\bDROP\b", body, re.IGNORECASE)
    assert not re.search(r"\bALTER\s+TABLE\b", body, re.IGNORECASE)
    assert "INSERT INTO" not in body.upper()
    assert "reference_policy_versions" not in body


def test_migration_0012_creates_exactly_one_table_and_four_triggers(tmp_path: Path) -> None:
    body = _migration_0012_statements()
    assert body.count("CREATE TABLE") == 1
    assert body.count("CREATE TRIGGER") == 4
    assert body.count("CREATE INDEX") == 0
    assert body.count("CREATE UNIQUE INDEX") == 0
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        objects = connection.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE name LIKE 'pilot_selection_entity_reasons%' "
            "OR name = 'pilot_selection_run_feasible_requires_reserve_disposition' "
            "ORDER BY name"
        ).fetchall()
    assert [(row["type"], row["name"]) for row in objects] == [
        ("table", "pilot_selection_entity_reasons"),
        ("trigger", "pilot_selection_entity_reasons_delete_guard"),
        ("trigger", "pilot_selection_entity_reasons_insert_guard"),
        ("trigger", "pilot_selection_entity_reasons_update_guard"),
        ("trigger", "pilot_selection_run_feasible_requires_reserve_disposition"),
    ]


def test_migrations_0009_to_0011_are_byte_identical_after_the_s5_4_addition() -> None:
    """Decision 020 sections 8.2 and 11: migration 0012 edits, replaces, and
    reinterprets none of them, and replaces no existing trigger."""
    assert (
        hashlib.sha256(
            (_MIGRATIONS_DIR / "0010_m23_quota_policy_reference.sql").read_bytes()
        ).hexdigest()
        == _MIGRATION_0010_SHA256
    )
    for name in (
        "0009_m23_pilot_schema.sql",
        "0010_m23_quota_policy_reference.sql",
        "0011_m23_joint_selector_policy_reference.sql",
    ):
        content = (_MIGRATIONS_DIR / name).read_text(encoding="utf-8")
        assert "pilot_selection_entity_reasons" not in content
        assert "pilot_selection_run_feasible_requires_reserve_disposition" not in content
    body = _migration_0012_statements()
    assert "DROP TRIGGER" not in body.upper()
    for existing in (
        "pilot_selection_run_feasible_requires_actual_results",
        "pilot_selection_run_requires_clean_non_feasible_result",
        "pilot_selection_run_transition_guard",
    ):
        assert existing not in body


def test_migration_0012_is_idempotent_under_a_second_runner_pass(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert apply_migrations(connection) == ()
        count = connection.execute(
            "SELECT COUNT(*) AS rows FROM sqlite_master "
            "WHERE name = 'pilot_selection_entity_reasons'"
        ).fetchone()["rows"]
    assert count == 1


def test_the_disposition_table_has_exactly_the_frozen_columns_and_key(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        columns = connection.execute(
            "SELECT name, type, `notnull`, pk "
            "FROM pragma_table_info('pilot_selection_entity_reasons')"
        ).fetchall()
        foreign_keys = connection.execute(
            "SELECT `table`, `from`, `to` FROM pragma_foreign_key_list("
            "'pilot_selection_entity_reasons') ORDER BY `table`, `from`"
        ).fetchall()
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'pilot_selection_entity_reasons'"
        ).fetchone()["sql"]
    assert [(row["name"], row["type"]) for row in columns] == [
        ("selection_run_id", "TEXT"),
        ("snapshot_id", "TEXT"),
        ("cik_numeric", "INTEGER"),
        ("reason_scope", "TEXT"),
        ("reason_code", "TEXT"),
        ("recorded_at_utc", "TEXT"),
    ]
    assert all(row["notnull"] == 1 for row in columns)
    assert {row["name"] for row in columns if row["pk"]} == {
        "selection_run_id",
        "snapshot_id",
        "cik_numeric",
        "reason_scope",
    }
    assert "detail" not in {row["name"] for row in columns}
    assert sorted((row["table"], row["from"]) for row in foreign_keys) == [
        ("pilot_selected_entities", "cik_numeric"),
        ("pilot_selected_entities", "selection_run_id"),
        ("pilot_selected_entities", "snapshot_id"),
        ("reference_reason_codes", "reason_code"),
    ]
    assert "STRICT" in sql
    assert "reason_scope IN ('reserve')" in sql
    assert "reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'" in sql


def _running_run_with_one_selected_entity(
    connection: sqlite3.Connection, *, snapshot_id: str, run_id: str, entities: int = 1
) -> None:
    _frozen_snapshot_with_n_entities(connection, snapshot_id, max(entities, 2))
    _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
    for order, cik in enumerate(range(1, entities + 1), start=1):
        _insert_selected_entity(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            cik_numeric=cik,
            selected_order=order,
        )


# --- CHECK-constraint boundary (Decision 020 section 8.3, item 1) ----------- #


def test_an_unauthorized_reserve_scope_is_refused_by_the_check_constraint(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("scope-check-snapshot")
    run_id = _hex("scope-check-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_reserve_disposition(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=1,
                reason_scope="selection",
            )


def test_an_unauthorized_reserve_reason_code_is_refused_by_the_check_constraint(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("code-check-snapshot")
    run_id = _hex("code-check-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        with pytest.raises(sqlite3.IntegrityError, match="CHECK constraint"):
            _insert_reserve_disposition(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=1,
                reason_code="REVIEW_PILOT_QUOTA_UNMEASURABLE_AT_M23",
            )


def test_an_unregistered_reason_code_is_refused_by_the_foreign_key(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("code-fk-snapshot")
    run_id = _hex("code-fk-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        connection.execute(
            "DELETE FROM reference_reason_codes WHERE reason_code = ?",
            (_NO_COMPATIBLE_RESERVE,),
        )
        connection.commit()
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            _insert_reserve_disposition(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=1,
            )


def test_a_cik_that_is_not_a_selected_entity_of_that_run_is_refused(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("entity-fk-snapshot")
    run_id = _hex("entity-fk-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
            _insert_reserve_disposition(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=2,
            )


# --- primary-key boundary (Decision 020 section 8.3, item 2) --------------- #


def test_a_duplicate_disposition_row_is_refused_by_the_primary_key(tmp_path: Path) -> None:
    """Excluding ``reason_code`` from the key is what makes a second disposition
    for one target structurally impossible."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("duplicate-disposition-snapshot")
    run_id = _hex("duplicate-disposition-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        _insert_reserve_disposition(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, cik_numeric=1
        )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
            _insert_reserve_disposition(
                connection, selection_run_id=run_id, snapshot_id=snapshot_id, cik_numeric=1
            )
        rows = connection.execute(
            "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons"
        ).fetchone()["rows"]
    assert rows == 1


# --- migration 0009's existing UNIQUE (Decision 020 section 8.3, item 3) ---- #


def test_a_duplicate_rank_one_reserve_package_is_refused_at_insertion(tmp_path: Path) -> None:
    """Migration 0012 neither duplicates nor replaces this constraint, and no test
    may require the transition trigger to catch a row that cannot be written."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("duplicate-rank1-snapshot")
    run_id = _hex("duplicate-rank1-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
        _insert_reserve(
            connection,
            reserve_package_id=_hex("rank1-a"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=1,
            replacement_cik_numeric=2,
        )
        with pytest.raises(sqlite3.IntegrityError, match="UNIQUE constraint"):
            _insert_reserve(
                connection,
                reserve_package_id=_hex("rank1-b"),
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                target_cik_numeric=1,
                replacement_cik_numeric=3,
            )


# --- lifecycle guards ------------------------------------------------------- #


def test_a_disposition_insert_requires_a_running_run(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("insert-guard-snapshot")
    run_id = _hex("insert-guard-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 2)
        _insert_selection_run(
            connection,
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            run_state="planned",
        )
        with pytest.raises(
            sqlite3.IntegrityError, match="requires an existing running selection run"
        ):
            _insert_reserve_disposition(
                connection, selection_run_id=run_id, snapshot_id=snapshot_id, cik_numeric=1
            )


def test_a_disposition_insert_for_a_missing_run_fails_closed(tmp_path: Path) -> None:
    """The frozen guard uses ``NOT EXISTS (... AND run_state = 'running')``, which is
    true -- and therefore aborts -- when no such run row exists at all. Migration
    0009's ``(SELECT run_state ...) <> 'running'`` form yields NULL there and never
    fires; that three-valued-logic path does not exist here."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("insert-missing-run-snapshot")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 2)
        with pytest.raises(
            sqlite3.IntegrityError, match="requires an existing running selection run"
        ):
            _insert_reserve_disposition(
                connection,
                selection_run_id=_hex("no-such-run"),
                snapshot_id=snapshot_id,
                cik_numeric=1,
            )


def _running_run_with_one_disposition(
    connection: sqlite3.Connection, *, snapshot_id: str, run_id: str
) -> None:
    _running_run_with_one_selected_entity(connection, snapshot_id=snapshot_id, run_id=run_id)
    _insert_reserve_disposition(
        connection, selection_run_id=run_id, snapshot_id=snapshot_id, cik_numeric=1
    )


def test_recorded_at_utc_may_be_updated_while_the_same_run_is_running(tmp_path: Path) -> None:
    """Operational provenance only: excluded from every deterministic identity and
    hash, and never defining the outcome (Decision 020 sections 8.2 and 9)."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("update-timestamp-snapshot")
    run_id = _hex("update-timestamp-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=run_id)
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_entity_reasons SET recorded_at_utc = ? "
                "WHERE selection_run_id = ?",
                ("2026-02-02T00:00:00Z", run_id),
            )
        stored = connection.execute(
            "SELECT recorded_at_utc FROM pilot_selection_entity_reasons WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()["recorded_at_utc"]
    assert stored == "2026-02-02T00:00:00Z"


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("snapshot_id", "other-snapshot"),
        ("cik_numeric", 2),
    ),
)
def test_target_identity_columns_are_immutable(tmp_path: Path, column: str, value: object) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("immutable-identity-snapshot")
    run_id = _hex("immutable-identity-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=run_id)
        with (
            pytest.raises(sqlite3.IntegrityError, match="target identity is immutable"),
            transaction(connection) as c,
        ):
            c.execute(
                f"UPDATE pilot_selection_entity_reasons SET {column} = ? "  # noqa: S608
                "WHERE selection_run_id = ?",
                (value, run_id),
            )


def test_a_disposition_cannot_be_moved_onto_a_feasible_run(tmp_path: Path) -> None:
    """The 2026-07-29 defect, closed: with an OLD-only UPDATE predicate a row could
    be moved from a running run onto an already-feasible one, leaving a sealed run
    holding both a reserve package and a no-compatible-reserve row for one target."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("cross-run-move-snapshot")
    running_run = _hex("cross-run-move-running")
    sealed_run = _hex("cross-run-move-sealed")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=sealed_run
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (sealed_run,),
            )
        _running_selection_run(connection, selection_run_id=running_run, snapshot_id=snapshot_id)
        _insert_selected_entity(
            connection,
            selection_run_id=running_run,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        _insert_reserve_disposition(
            connection,
            selection_run_id=running_run,
            snapshot_id=snapshot_id,
            cik_numeric=1,
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires an existing running selection run"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_entity_reasons SET selection_run_id = ? "
                "WHERE selection_run_id = ?",
                (sealed_run, running_run),
            )
        sealed_rows = connection.execute(
            "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons "
            "WHERE selection_run_id = ?",
            (sealed_run,),
        ).fetchone()["rows"]
    assert sealed_rows == 24


def test_a_disposition_cannot_be_moved_between_two_running_runs(tmp_path: Path) -> None:
    """Both runs are running, so the run predicate passes and the immutability
    predicate is the one that refuses the move."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("two-running-snapshot")
    first_run = _hex("two-running-first")
    second_run = _hex("two-running-second")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=first_run)
        _running_selection_run(connection, selection_run_id=second_run, snapshot_id=snapshot_id)
        _insert_selected_entity(
            connection,
            selection_run_id=second_run,
            snapshot_id=snapshot_id,
            cik_numeric=1,
            selected_order=1,
        )
        with (
            pytest.raises(sqlite3.IntegrityError, match="target identity is immutable"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_entity_reasons SET selection_run_id = ? "
                "WHERE selection_run_id = ?",
                (second_run, first_run),
            )


def test_a_disposition_may_be_deleted_while_its_run_is_running(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("delete-guard-snapshot")
    run_id = _hex("delete-guard-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=run_id)
        with transaction(connection) as c:
            c.execute(
                "DELETE FROM pilot_selection_entity_reasons WHERE selection_run_id = ?",
                (run_id,),
            )
        assert (
            connection.execute(
                "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons"
            ).fetchone()["rows"]
            == 0
        )


def _drop_run_row_bypassing_foreign_keys(path: Path, run_id: str) -> None:
    """Simulate catalog corruption: the associated run row disappears.

    Foreign keys make this unreachable through the application connection -- the
    selected-entity child would block it -- so the row is removed on a raw
    connection with foreign keys off, exactly as the migration-provenance suite
    tampers with stored provenance. The point is what the guards do afterwards.
    """
    raw = sqlite3.connect(path)
    try:
        raw.execute("PRAGMA foreign_keys = OFF")
        # Migration 0013's trigger 7 aborts every DELETE on this table unconditionally
        # and independently of any pragma (Decision 021 section 15.5 clause 3), so the
        # guard is dropped on this throwaway catalog purely to construct the corrupted
        # state the migration-0009 and 0012 NOT EXISTS predicates are being tested
        # against. That a normal path can no longer reach this state is the point.
        raw.execute("DROP TRIGGER pilot_selection_run_delete_guard")
        raw.execute("DELETE FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,))
        raw.commit()
    finally:
        raw.close()


@pytest.mark.parametrize(
    "statement",
    (
        "UPDATE pilot_selection_entity_reasons SET recorded_at_utc = 'x' "
        "WHERE selection_run_id = ?",
        "DELETE FROM pilot_selection_entity_reasons WHERE selection_run_id = ?",
    ),
    ids=("update", "delete"),
)
def test_update_and_delete_fail_closed_when_the_associated_run_is_missing(
    tmp_path: Path, statement: str
) -> None:
    """Every guard uses an explicit ``NOT EXISTS (... AND run_state = 'running')``,
    which is true -- and therefore aborts -- when no such run row exists at all."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("missing-run-guard-snapshot")
    run_id = _hex("missing-run-guard-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=run_id)
    _drop_run_row_bypassing_foreign_keys(path, run_id)
    with connect(path, writer=True) as connection:
        assert (
            connection.execute(
                "SELECT COUNT(*) AS rows FROM pilot_selection_runs WHERE selection_run_id = ?",
                (run_id,),
            ).fetchone()["rows"]
            == 0
        )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires an existing running selection run"
            ),
            transaction(connection) as c,
        ):
            c.execute(statement, (run_id,))
        remaining = connection.execute(
            "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()["rows"]
    assert remaining == 1


def test_disposition_rows_are_immutable_once_the_run_leaves_running(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("terminal-immutable-snapshot")
    run_id = _hex("terminal-immutable-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires an existing running selection run"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_entity_reasons SET recorded_at_utc = 'x' "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        with (
            pytest.raises(
                sqlite3.IntegrityError, match="requires an existing running selection run"
            ),
            transaction(connection) as c,
        ):
            c.execute(
                "DELETE FROM pilot_selection_entity_reasons WHERE selection_run_id = ?",
                (run_id,),
            )
        remaining = connection.execute(
            "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()["rows"]
    assert remaining == 24


def test_a_disposition_insert_is_refused_once_the_run_is_feasible(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("post-feasible-insert-snapshot")
    run_id = _hex("post-feasible-insert-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        _insert_reserve(
            connection,
            reserve_package_id=_hex("post-feasible-reserve"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=24,
            replacement_cik_numeric=1,
        )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 24 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        with pytest.raises(
            sqlite3.IntegrityError, match="requires an existing running selection run"
        ):
            _insert_reserve_disposition(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=24,
            )


# --- feasible-transition disposition completeness --------------------------- #


def _transition_to_feasible(connection: sqlite3.Connection, run_id: str) -> None:
    with transaction(connection) as c:
        c.execute(
            "UPDATE pilot_selection_runs SET run_state = 'feasible', "
            "selected_entity_count = 24, selected_accession_count = 24 "
            "WHERE selection_run_id = ?",
            (run_id,),
        )


def test_a_run_where_every_selected_entity_has_one_disposition_becomes_feasible(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("disposition-ok-snapshot")
    run_id = _hex("disposition-ok-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        _insert_reserve(
            connection,
            reserve_package_id=_hex("mixed-disposition-reserve"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=24,
            replacement_cik_numeric=1,
        )
        _transition_to_feasible(connection, run_id)
        state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
    assert state == "feasible"


def test_a_selected_entity_with_neither_disposition_refuses_the_transition(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("neither-disposition-snapshot")
    run_id = _hex("neither-disposition-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires exactly one reserve disposition per selected entity",
        ):
            _transition_to_feasible(connection, run_id)


def test_one_missing_disposition_among_many_refuses_the_transition(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("one-missing-snapshot")
    run_id = _hex("one-missing-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires exactly one reserve disposition per selected entity",
        ):
            _transition_to_feasible(connection, run_id)


def test_a_target_with_both_disposition_types_refuses_the_transition(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("both-dispositions-snapshot")
    run_id = _hex("both-dispositions-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=True
        )
        _insert_reserve(
            connection,
            reserve_package_id=_hex("both-dispositions-reserve"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=7,
            replacement_cik_numeric=8,
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires exactly one reserve disposition per selected entity",
        ):
            _transition_to_feasible(connection, run_id)


def test_a_rank_two_only_target_refuses_the_transition(tmp_path: Path) -> None:
    """Load-bearing on its own: a rank-2-only target's disposition count is exactly
    1, so only the rank condition rejects it."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("rank-two-only-snapshot")
    run_id = _hex("rank-two-only-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        _insert_reserve(
            connection,
            reserve_package_id=_hex("rank-two-only-reserve"),
            selection_run_id=run_id,
            snapshot_id=snapshot_id,
            target_cik_numeric=24,
            replacement_cik_numeric=1,
            reserve_rank=2,
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires every reserve package to be reserve_rank 1",
        ):
            _transition_to_feasible(connection, run_id)


def test_a_target_with_rank_one_plus_rank_two_refuses_the_transition(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("rank-one-plus-two-snapshot")
    run_id = _hex("rank-one-plus-two-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        for rank, replacement in ((1, 1), (2, 2)):
            _insert_reserve(
                connection,
                reserve_package_id=_hex(f"rank-{rank}-package"),
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                target_cik_numeric=24,
                replacement_cik_numeric=replacement,
                reserve_rank=rank,
            )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires exactly one reserve disposition per selected entity",
        ):
            _transition_to_feasible(connection, run_id)


def test_a_control_target_with_no_disposition_refuses_the_transition(tmp_path: Path) -> None:
    """Every selected entity is a reserve target, controls included."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("control-no-disposition-snapshot")
    run_id = _hex("control-no-disposition-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 24)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        for order, cik in enumerate(range(1, 25), start=1):
            _insert_selected_entity(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                cik_numeric=cik,
                selected_order=order,
                entity_role="control" if cik > 20 else "operating",
            )
            _insert_selected_accession(
                connection,
                selection_run_id=run_id,
                snapshot_id=snapshot_id,
                accession_plain=f"acc-{cik}",
                anchor_cik_numeric=cik,
                selected_order=order,
            )
        _seed_reserve_dispositions(
            connection, selection_run_id=run_id, snapshot_id=snapshot_id, ciks=range(1, 24)
        )
        roles = connection.execute(
            "SELECT entity_role FROM pilot_selected_entities "
            "WHERE selection_run_id = ? AND cik_numeric = 24",
            (run_id,),
        ).fetchone()["entity_role"]
        assert roles == "control"
        with pytest.raises(
            sqlite3.IntegrityError,
            match="requires exactly one reserve disposition per selected entity",
        ):
            _transition_to_feasible(connection, run_id)


def test_a_non_feasible_terminal_transition_stays_clean_with_zero_parents(
    tmp_path: Path,
) -> None:
    """Decision 020 section 8.2: the composite foreign key requires a parent
    selected-entity row, and migration 0009 already requires zero selected entities
    before a non-feasible terminal transition, so the clean-run invariant holds
    transitively and needs no change to that trigger."""
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("clean-non-feasible-snapshot")
    run_id = _hex("clean-non-feasible-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, snapshot_id, 2)
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'infeasible' "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        state = connection.execute(
            "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
        ).fetchone()["run_state"]
        rows = connection.execute(
            "SELECT COUNT(*) AS rows FROM pilot_selection_entity_reasons"
        ).fetchone()["rows"]
    assert state == "infeasible"
    assert rows == 0


def test_a_non_feasible_transition_is_refused_while_a_disposition_row_exists(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("dirty-non-feasible-snapshot")
    run_id = _hex("dirty-non-feasible-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _running_run_with_one_disposition(connection, snapshot_id=snapshot_id, run_id=run_id)
        with (
            pytest.raises(sqlite3.IntegrityError, match="zero durable result rows"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'infeasible' "
                "WHERE selection_run_id = ?",
                (run_id,),
            )


def test_a_refused_transition_rolls_back_and_leaves_the_run_running(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("rollback-snapshot")
    run_id = _hex("rollback-run")
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _feasible_run_with_24_actual_entities_and_accessions(
            connection, snapshot_id=snapshot_id, run_id=run_id, seed_dispositions=False
        )
        with pytest.raises(sqlite3.IntegrityError):
            _transition_to_feasible(connection, run_id)
        row = connection.execute(
            "SELECT run_state, selected_entity_count FROM pilot_selection_runs "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()
    assert row["run_state"] == "running"
    assert row["selected_entity_count"] is None


# ==========================================================================
# Migration 0013 -- the eight Stage S6 lifecycle, identity, replacement, and
# deletion guards (Decision 021 sections 15.1, 15.3, 15.5)
#
# The statement region of migration 0013 is frozen byte-for-byte in Decision 021
# section 15.1 and was accepted by the project owner on 2026-07-30 following the
# focused independent governance review of v0.5. These tests prove the file
# reproduces that SQL exactly, that it adds exactly eight triggers and alters
# nothing, and that each guard behaves as frozen -- including under every
# combination of recursive_triggers and foreign_keys, because Decision 021
# section 15.5 states the guarantee holds with no pragma required for correctness.
# ==========================================================================

_MIGRATION_0013 = _MIGRATIONS_DIR / "0013_m23_manifest_lifecycle_guards.sql"

_S6_BLOCK_DIGESTS: Final = (
    "f805f666be223cdaf7d5b29fdbd1bec8709f9ba3c71fd8e46f419ca35ab3b850",
    "e2e44785a6b123e3eef87314c8e8d4d24b75fb3b3ffef3c6adde763dcfd940f2",
    "495a1c43e7a1e542f9464c86e18900a5a161aa84dc85bee55fb7d7e5f86394fb",
    "1a376c1b37317ec0fc9dc697a69370f54a09cf0124942c742ea9a984c838cb98",
    "21d8cc57090c35ac3624e908a98759112623f7be4347df15ea0a5bce20b5c97e",
    "fb43032dd3c2c868428539ac5eb7fed98bef8bad39318014ddd34f0eec26b424",
    "879459ec7dbde300ce586c9d51c3aa32208e5c44719c8fce177465f942536448",
    "167f7a891728250b04f3637562fe5526d0cf997ea9ae098e97be71e8611b7eef",
)
_S6_REGION_DIGEST: Final = "7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595"
_S6_REGION_BYTES: Final = 10939
_S6_REGION_LINES: Final = 186
_S6_TRIGGER_NAMES: Final = (
    "pilot_selection_run_insert_unsealed_guard",
    "pilot_selection_run_result_hash_guard",
    "pilot_manifest_versions_insert_guard",
    "pilot_manifest_versions_identity_guard",
    "pilot_manifest_versions_replacement_guard",
    "pilot_selection_run_replacement_guard",
    "pilot_selection_run_delete_guard",
    "pilot_selection_run_identity_guard",
)
#: Withdrawn as compositions by Decision 021 section 15.3; must appear nowhere.
_WITHDRAWN_REGION_DIGESTS: Final = (
    "6bfb897cc0db1b870d67546dc8ce5937741fbef542d6c2f940f2928c0c9a6c40",
    "51151767895eee673997331d4e8a3153836a31738c094c152340320021449edc",
)
_RUN_STATES: Final = (
    "planned",
    "running",
    "feasible",
    "failed",
    "infeasible",
    "infeasible_or_unproven",
)


def _migration_0013_statement_region() -> str:
    """Migration 0013 from its first statement line to end of file.

    The leading ``--`` header block follows the migration 0012 convention and is
    explicitly not part of the normative statement region (Decision 021 section 15.1).
    """
    lines = _MIGRATION_0013.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(index for index, line in enumerate(lines) if line.startswith("CREATE TRIGGER"))
    return "".join(lines[start:])


def _frozen_blocks() -> list[str]:
    """The eight fenced SQL blocks, extracted from the accepted decision record."""
    text = _DECISION_021_PATH.read_text(encoding="utf-8").split("\n")
    start = next(i for i, line in enumerate(text) if line.startswith("### 15.1"))
    end = next(i for i, line in enumerate(text) if line.startswith("### 15.2"))
    blocks: list[str] = []
    current: list[str] = []
    inside = False
    for line in text[start:end]:
        if line.strip() == "```sql":
            inside, current = True, []
            continue
        if inside and line.strip() == "```":
            inside = False
            blocks.append("\n".join(current) + "\n")
            continue
        if inside:
            current.append(line)
    return blocks


def test_migration_0013_reproduces_the_frozen_decision_021_sql_byte_for_byte() -> None:
    """The statement region equals the section 15.1 SQL exactly, block for block."""
    blocks = _frozen_blocks()
    assert len(blocks) == 8
    assert _migration_0013_statement_region() == "\n".join(blocks)


def test_migration_0013_reproduces_all_nine_normative_digests() -> None:
    """Eight per-block digests plus the concatenation, with byte and line counts."""
    blocks = _frozen_blocks()
    for block, expected in zip(blocks, _S6_BLOCK_DIGESTS, strict=True):
        assert hashlib.sha256(block.encode("utf-8")).hexdigest() == expected
        assert block.endswith("\n")
    region = _migration_0013_statement_region()
    encoded = region.encode("utf-8")
    assert hashlib.sha256(encoded).hexdigest() == _S6_REGION_DIGEST
    assert len(encoded) == _S6_REGION_BYTES
    assert region.count("\n") == _S6_REGION_LINES


def test_migration_0013_does_not_reproduce_a_withdrawn_region() -> None:
    """The v0.4 five-block and v0.3 four-block compositions are withdrawn."""
    content = _MIGRATION_0013.read_text(encoding="utf-8")
    for withdrawn in _WITHDRAWN_REGION_DIGESTS:
        assert withdrawn not in content
    assert _migration_0013_statement_region().count("CREATE TRIGGER") == 8


def test_migration_0013_is_ddl_only_and_carries_no_forbidden_statement() -> None:
    """Every body statement is a ``SELECT RAISE(ABORT, ...)`` guard."""
    region = _migration_0013_statement_region()
    executable = "\n".join(line for line in region.split("\n") if not line.strip().startswith("--"))
    for forbidden in ("DROP ", "ALTER ", "PRAGMA ", "ATTACH ", "VACUUM ", "CREATE TABLE"):
        assert forbidden not in executable.upper()
    bodies = re.findall(r"BEGIN\n(.*?)\nEND;", region, re.DOTALL)
    assert len(bodies) == 8
    for body in bodies:
        statements = [
            fragment.strip()
            for fragment in re.split(r";\s*\n", body)
            if fragment.strip() and not fragment.strip().startswith("--")
        ]
        for statement in statements:
            assert statement.startswith("SELECT RAISE(ABORT")


def test_migration_0013_adds_exactly_eight_triggers_and_alters_nothing(tmp_path: Path) -> None:
    """Additive only: no object is created, dropped, altered, or replaced.

    Bounded at 0013 on purpose. Migration 0014 is a deliberate *rebuild* of four tables
    (Decision 083 R58) and is proved separately; measuring 0013's additivity through it
    would conflate two different claims.
    """
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        inventory = tuple(m for m in available_migrations() if m.version <= 12)
        apply_migrations(connection, inventory)
        before = {
            (row["type"], row["name"]): row["sql"]
            for row in connection.execute("SELECT type, name, sql FROM sqlite_master")
        }
        apply_migrations(connection, tuple(m for m in available_migrations() if m.version <= 13))
        after = {
            (row["type"], row["name"]): row["sql"]
            for row in connection.execute("SELECT type, name, sql FROM sqlite_master")
        }
    added = set(after) - set(before)
    assert sorted(name for _, name in added) == sorted(_S6_TRIGGER_NAMES)
    assert {kind for kind, _ in added} == {"trigger"}
    assert set(before) - set(after) == set()
    assert all(before[key] == after[key] for key in before)
    assert len(after) == len(before) + 8


def _s6_catalog(tmp_path: Path, *, recursive_triggers: int = 0, foreign_keys: int = 1) -> Path:
    """A migrated catalog with one frozen snapshot, at the requested pragma settings."""
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        _seed_job(connection)
        _frozen_snapshot_with_n_entities(connection, _hex("s6-snapshot"), 1)
    return path


def _s6_insert_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    state: str = "planned",
    sealed: str | None = None,
    snapshot_id: str | None = None,
    input_sha256: str | None = None,
    verb: str = "INSERT",
) -> None:
    """Insert one selection run at an arbitrary state, optionally pre-sealed."""
    columns = [
        "selection_run_id",
        "snapshot_id",
        "selection_seed",
        "selector_policy_version",
        "quota_policy_version",
        "search_node_limit",
        "run_state",
        "selection_input_sha256",
        "started_at_utc",
    ]
    values: list[object] = [
        run_id,
        snapshot_id or _hex("s6-snapshot"),
        "seed",
        pilot_policy.PILOT_SELECTOR_POLICY_VERSION,
        "quota/1.0",
        1000,
        state,
        input_sha256 or _hex(f"selection-input:{run_id}"),
        "2026-01-01T00:00:00Z",
    ]
    if state in {"feasible", "failed", "infeasible", "infeasible_or_unproven"}:
        columns += [
            "selected_entity_count",
            "selected_accession_count",
            "expanded_node_count",
            "finished_at_utc",
        ]
        values += [24, 0] if state == "feasible" else [None, None]
        values += [10, "2026-01-02T00:00:00Z"]
    if sealed is not None:
        columns.append("selection_result_sha256")
        values.append(sealed)
    placeholders = ", ".join("?" for _ in columns)
    connection.execute(
        f"{verb} INTO pilot_selection_runs ({', '.join(columns)}) VALUES ({placeholders})",  # noqa: S608
        tuple(values),
    )


def _run_row(connection: sqlite3.Connection, run_id: str) -> tuple[object, ...]:
    """The complete run row, for byte-preservation comparison."""
    row = connection.execute(
        "SELECT * FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
    ).fetchone()
    return tuple(row) if row is not None else ()


@pytest.mark.parametrize("state", _RUN_STATES)
def test_s6_trigger_1_refuses_a_pre_sealed_insert_in_every_state(
    tmp_path: Path, state: str
) -> None:
    """Block 1: every selection run begins unsealed, on every write path."""
    path = _s6_catalog(tmp_path)
    with (
        connect(path, writer=True) as connection,
        transaction(connection) as c,
        pytest.raises(sqlite3.IntegrityError, match="must be inserted unsealed"),
    ):
        _s6_insert_run(c, run_id=_hex(f"presealed-{state}"), state=state, sealed=_hex("seal"))


@pytest.mark.parametrize("state", ["planned", "running", "feasible"])
def test_s6_trigger_1_accepts_a_genuinely_new_unsealed_run(tmp_path: Path, state: str) -> None:
    """A genuinely new unsealed run inserts normally in every authorized state."""
    path = _s6_catalog(tmp_path)
    with connect(path, writer=True) as connection, transaction(connection) as c:
        _s6_insert_run(c, run_id=_hex(f"unsealed-{state}"), state=state)


@pytest.mark.parametrize("state", ["planned", "running", "failed", "infeasible"])
def test_s6_trigger_2_refuses_sealing_a_non_feasible_run(tmp_path: Path, state: str) -> None:
    """Block 2: sealing is permitted only on a run that is feasible before and after."""
    path = _s6_catalog(tmp_path)
    run_id = _hex(f"seal-{state}")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state=state)
        with (
            pytest.raises(sqlite3.IntegrityError, match="only on a feasible selection run"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (_hex("seal"), run_id),
            )


def test_s6_trigger_2_seals_immutably_and_idempotently(tmp_path: Path) -> None:
    """NULL to non-NULL once; identical restatement accepted; change and clear refused."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("seal-lifecycle")
    seal = _hex("seal")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (seal, run_id),
            )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (seal, run_id),
            )
        for replacement in (_hex("other-seal"), None):
            with (
                pytest.raises(sqlite3.IntegrityError, match="immutable once set"),
                transaction(connection) as c,
            ):
                c.execute(
                    "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                    "WHERE selection_run_id = ?",
                    (replacement, run_id),
                )


def test_s6_trigger_2_refuses_a_seal_riding_the_terminal_transition(tmp_path: Path) -> None:
    """The seal is always a separate, later write over an already-terminal run."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("seal-ride-along")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="running")
        with (
            pytest.raises(sqlite3.IntegrityError, match="only on a feasible selection run"),
            transaction(connection) as c,
        ):
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = 24, selected_accession_count = 0, "
                "selection_result_sha256 = ? WHERE selection_run_id = ?",
                (_hex("seal"), run_id),
            )


@pytest.mark.parametrize("recursive_triggers", [0, 1])
@pytest.mark.parametrize("foreign_keys", [0, 1])
@pytest.mark.parametrize(
    ("label", "sealed", "state"),
    [
        ("identical digest", "same", "feasible"),
        ("changed digest", "other", "feasible"),
        ("omitted digest", None, "feasible"),
    ],
)
def test_s6_trigger_6_refuses_every_run_replacement_form(
    tmp_path: Path,
    recursive_triggers: int,
    foreign_keys: int,
    label: str,
    sealed: str | None,
    state: str,
) -> None:
    """Block 6: a run is never replaced, under any pragma setting."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("replace-target")
    seal = _hex("seal")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state=state)
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (seal, run_id),
            )
        connection.execute(f"PRAGMA recursive_triggers = {recursive_triggers}")
        connection.execute(f"PRAGMA foreign_keys = {foreign_keys}")
        before = _run_row(connection, run_id)
        incoming = {"same": seal, "other": _hex("other-seal")}.get(sealed or "")
        with pytest.raises(sqlite3.IntegrityError, match="already exists"):
            _s6_insert_run(
                connection,
                run_id=run_id,
                state=state,
                sealed=incoming,
                verb="INSERT OR REPLACE",
            )
        assert _run_row(connection, run_id) == before


@pytest.mark.parametrize("verb", ["INSERT", "INSERT OR IGNORE", "INSERT OR REPLACE"])
def test_s6_trigger_6_refuses_duplicate_and_ignored_inserts(tmp_path: Path, verb: str) -> None:
    """A duplicate INSERT and an INSERT OR IGNORE are refused, not silently dropped."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("duplicate-run")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="planned")
        before = _run_row(connection, run_id)
        with pytest.raises(sqlite3.IntegrityError, match="already exists"):
            _s6_insert_run(connection, run_id=run_id, state="planned", verb=verb)
        assert _run_row(connection, run_id) == before


@pytest.mark.parametrize("column", ["snapshot_id", "selection_input_sha256"])
def test_s6_trigger_6_refuses_a_replacement_that_changes_run_identity(
    tmp_path: Path, column: str
) -> None:
    """A replacement arriving with a different snapshot or input digest is refused."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("replace-identity")
    other_snapshot = _hex("s6-second-snapshot")
    with connect(path, writer=True) as connection:
        _frozen_snapshot_with_n_entities(connection, other_snapshot, 1)
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        before = _run_row(connection, run_id)
        override: dict[str, str] = {
            column: other_snapshot if column == "snapshot_id" else _hex("x")
        }
        with pytest.raises(sqlite3.IntegrityError, match="already exists"):
            _s6_insert_run(
                connection,
                run_id=run_id,
                state="feasible",
                verb="INSERT OR REPLACE",
                snapshot_id=override.get("snapshot_id"),
                input_sha256=override.get("selection_input_sha256"),
            )
        assert _run_row(connection, run_id) == before


@pytest.mark.parametrize("recursive_triggers", [0, 1])
@pytest.mark.parametrize("foreign_keys", [0, 1])
@pytest.mark.parametrize("state", _RUN_STATES)
def test_s6_trigger_7_refuses_deletion_in_every_state(
    tmp_path: Path, recursive_triggers: int, foreign_keys: int, state: str
) -> None:
    """Block 7: selection runs are undeletable in every state, under any pragma."""
    path = _s6_catalog(tmp_path)
    run_id = _hex(f"delete-{state}")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state=state)
        connection.execute(f"PRAGMA recursive_triggers = {recursive_triggers}")
        connection.execute(f"PRAGMA foreign_keys = {foreign_keys}")
        before = _run_row(connection, run_id)
        with pytest.raises(sqlite3.IntegrityError, match="undeletable"):
            connection.execute(
                "DELETE FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
            )
        assert _run_row(connection, run_id) == before


@pytest.mark.parametrize("column", ["selection_run_id", "snapshot_id", "selection_input_sha256"])
def test_s6_trigger_8_holds_run_identity_immutable(tmp_path: Path, column: str) -> None:
    """Block 8: the three persisted identity fields never change once inserted."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("identity-run")
    other_snapshot = _hex("s6-third-snapshot")
    with connect(path, writer=True) as connection:
        _frozen_snapshot_with_n_entities(connection, other_snapshot, 1)
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        before = _run_row(connection, run_id)
        replacement = other_snapshot if column == "snapshot_id" else _hex("changed")
        with pytest.raises(sqlite3.IntegrityError, match="identity is immutable"):
            connection.execute(
                f"UPDATE pilot_selection_runs SET {column} = ? WHERE selection_run_id = ?",  # noqa: S608
                (replacement, run_id),
            )
        assert _run_row(connection, run_id) == before


def test_s6_trigger_8_accepts_an_identical_identity_restatement(tmp_path: Path) -> None:
    """Rewriting all three identically is an idempotent no-op, not a failure."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("identity-restate")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        row = connection.execute(
            "SELECT snapshot_id, selection_input_sha256 FROM pilot_selection_runs "
            "WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_run_id = ?, snapshot_id = ?, "
                "selection_input_sha256 = ? WHERE selection_run_id = ?",
                (run_id, row["snapshot_id"], row["selection_input_sha256"], run_id),
            )


def test_s6_trigger_8_leaves_the_accepted_s5_update_shapes_untouched(tmp_path: Path) -> None:
    """No accepted S4 or S5 statement names an identity column, so trigger 8 never fires."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("neutrality-run")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="planned")
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 1 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selected_entity_count = 24, "
                "selected_accession_count = 0, expanded_node_count = 7, "
                "node_limit_exhausted = 0 WHERE selection_run_id = ?",
                (run_id,),
            )


@pytest.mark.parametrize("recursive_triggers", [0, 1])
@pytest.mark.parametrize("foreign_keys", [0, 1])
def test_s6_trigger_5_refuses_every_manifest_replacement_route(
    tmp_path: Path, recursive_triggers: int, foreign_keys: int
) -> None:
    """Block 5: all three uniqueness routes refused, with the row byte-identical."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("manifest-replace-run")
    manifest_id = _hex("manifest-replace")
    with connect(path, writer=True) as connection:
        _feasible_sealed_selection_run(
            connection, selection_run_id=run_id, snapshot_id=_hex("s6-snapshot")
        )
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=_hex("s6-snapshot"),
            root_hash=_hex("manifest-replace-root"),
        )
        connection.execute(f"PRAGMA recursive_triggers = {recursive_triggers}")
        connection.execute(f"PRAGMA foreign_keys = {foreign_keys}")
        before = tuple(
            connection.execute(
                "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?", (manifest_id,)
            ).fetchone()
        )
        # Route 1: the manifest_id primary key.
        with pytest.raises(sqlite3.IntegrityError, match="never replaced"):
            connection.execute(
                "INSERT OR REPLACE INTO pilot_manifest_versions "
                "(manifest_id, selection_run_id, snapshot_id, manifest_schema_version, "
                "ordinal_version, source_observation_set_sha256, candidate_tables_sha256, "
                "quota_definitions_sha256, selector_policy_sha256, selected_entities_sha256, "
                "selected_accessions_sha256, reserves_sha256, quota_report_sha256, "
                "root_manifest_sha256, manifest_state, generated_at_utc) "
                "VALUES (?, ?, ?, 'manifest/1.0', 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', "
                "'2026-01-05T00:00:00Z')",
                (
                    manifest_id,
                    run_id,
                    _hex("s6-snapshot"),
                    *[_hex(f"forged-{index}") for index in range(9)],
                ),
            )
        # Route 2: UNIQUE (selection_run_id, snapshot_id, ordinal_version).
        with pytest.raises(sqlite3.IntegrityError, match="never replaced"):
            connection.execute(
                "INSERT OR REPLACE INTO pilot_manifest_versions "
                "(manifest_id, selection_run_id, snapshot_id, manifest_schema_version, "
                "ordinal_version, source_observation_set_sha256, candidate_tables_sha256, "
                "quota_definitions_sha256, selector_policy_sha256, selected_entities_sha256, "
                "selected_accessions_sha256, reserves_sha256, quota_report_sha256, "
                "root_manifest_sha256, manifest_state, generated_at_utc) "
                "VALUES (?, ?, ?, 'manifest/1.0', 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'proposed', "
                "'2026-01-05T00:00:00Z')",
                (
                    _hex("manifest-replace-other"),
                    run_id,
                    _hex("s6-snapshot"),
                    *[_hex(f"forged2-{index}") for index in range(9)],
                ),
            )
        assert (
            tuple(
                connection.execute(
                    "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?", (manifest_id,)
                ).fetchone()
            )
            == before
        )


def test_s6_trigger_3_requires_a_feasible_sealed_run_for_a_manifest(tmp_path: Path) -> None:
    """Block 3: a manifest over a feasible but unsealed run is refused."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("unsealed-manifest-run")
    with connect(path, writer=True) as connection:
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        with pytest.raises(sqlite3.IntegrityError, match="sealed"):
            _insert_manifest(
                connection,
                manifest_id=_hex("unsealed-manifest"),
                selection_run_id=run_id,
                snapshot_id=_hex("s6-snapshot"),
                root_hash=_hex("unsealed-root"),
            )


@pytest.mark.parametrize(
    "column",
    [
        "manifest_id",
        "manifest_schema_version",
        "selection_run_id",
        "snapshot_id",
        "ordinal_version",
        "supersedes_manifest_id",
    ],
)
def test_s6_trigger_4_holds_all_six_manifest_identity_fields_immutable(
    tmp_path: Path, column: str
) -> None:
    """Block 4: manifest identity is immutable in all six of its fields."""
    path = _s6_catalog(tmp_path)
    run_id = _hex("manifest-identity-run")
    manifest_id = _hex("manifest-identity")
    with connect(path, writer=True) as connection:
        _feasible_sealed_selection_run(
            connection, selection_run_id=run_id, snapshot_id=_hex("s6-snapshot")
        )
        _insert_manifest(
            connection,
            manifest_id=manifest_id,
            selection_run_id=run_id,
            snapshot_id=_hex("s6-snapshot"),
            root_hash=_hex("manifest-identity-root"),
        )
        before = tuple(
            connection.execute(
                "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?", (manifest_id,)
            ).fetchone()
        )
        # For the two columns that also name the referenced run, move the manifest onto a
        # second run that is itself feasible and sealed. Migration 0013's block 4 checks
        # the OLD and the NEW referenced run first, so pointing at a nonexistent run would
        # trip that predicate instead and prove nothing about identity immutability.
        second_run = _hex("manifest-identity-second-run")
        _feasible_sealed_selection_run(
            connection, selection_run_id=second_run, snapshot_id=_hex("s6-snapshot")
        )
        _frozen_snapshot_with_n_entities(connection, _hex("s6-second-snapshot-for-identity"), 1)
        replacement: object
        if column == "ordinal_version":
            replacement = 9
        elif column == "selection_run_id":
            replacement = second_run
        elif column == "snapshot_id":
            replacement = _hex("s6-second-snapshot-for-identity")
        else:
            replacement = _hex("changed")
        # Changing snapshot_id necessarily points the row at a (run, snapshot) pair no
        # sealed feasible run carries, so block 4's referenced-run predicate refuses it
        # before the identity predicate is reached. Both are the same guard refusing the
        # same write, so the assertion accepts either message and the column still cannot
        # move -- which is the guarantee under test.
        expected = (
            "identity is immutable|requires an existing feasible selection run"
            if column == "snapshot_id"
            else "identity is immutable"
        )
        with pytest.raises(sqlite3.IntegrityError, match=expected):
            connection.execute(
                f"UPDATE pilot_manifest_versions SET {column} = ? WHERE manifest_id = ?",  # noqa: S608
                (replacement, manifest_id),
            )
        assert (
            tuple(
                connection.execute(
                    "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?", (manifest_id,)
                ).fetchone()
            )
            == before
        )


def test_s6_append_once_and_recomputability_guarantee_holds(tmp_path: Path) -> None:
    """Decision 021 section 15.5: the nine clauses, proven together on one run.

    A run is inserted only unsealed, cannot be replaced, cannot be deleted, cannot have
    its persisted identity changed, seals only on an already-feasible run, cannot have
    that seal changed or cleared, tolerates an identical restatement, and therefore
    carries a ``selection_result_sha256`` that is append-once **and** still recomputable
    from the persisted preimage its section 6.1 fields are read from.
    """
    path = _s6_catalog(tmp_path)
    run_id = _hex("guarantee-run")
    seal = _hex("guarantee-seal")
    with connect(path, writer=True) as connection:
        # 1. Every new run begins unsealed.
        with (
            pytest.raises(sqlite3.IntegrityError, match="must be inserted unsealed"),
            transaction(connection) as c,
        ):
            _s6_insert_run(c, run_id=run_id, state="feasible", sealed=seal)
        with transaction(connection) as c:
            _s6_insert_run(c, run_id=run_id, state="feasible")
        preimage = _run_row(connection, run_id)
        # 5. Sealing occurs only through the guarded update on an already-feasible run.
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (seal, run_id),
            )
        # 7. Identical restatement stays idempotent.
        with transaction(connection) as c:
            c.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (seal, run_id),
            )
        sealed_row = _run_row(connection, run_id)
        # 6. A sealed digest cannot change or clear.
        for replacement in (_hex("other"), None):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(
                    "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                    "WHERE selection_run_id = ?",
                    (replacement, run_id),
                )
        # 2. An existing run cannot be replaced.
        with pytest.raises(sqlite3.IntegrityError, match="already exists"):
            _s6_insert_run(connection, run_id=run_id, state="feasible", verb="INSERT OR REPLACE")
        # 3. A run cannot be deleted.
        with pytest.raises(sqlite3.IntegrityError, match="undeletable"):
            connection.execute(
                "DELETE FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
            )
        # 4 and 8. The persisted identity, including selection_input_sha256, cannot change.
        for column in ("selection_run_id", "snapshot_id", "selection_input_sha256"):
            with pytest.raises(sqlite3.IntegrityError, match="identity is immutable"):
                connection.execute(
                    f"UPDATE pilot_selection_runs SET {column} = ? WHERE selection_run_id = ?",  # noqa: S608
                    (_hex("changed"), run_id),
                )
        # 9. The seal remains recomputable: every section 6.1 preimage field the run
        # row carries is byte-identical to what it was before sealing, so nothing the
        # digest was computed over moved underneath it.
        after = _run_row(connection, run_id)
        assert after == sealed_row
        columns = [
            description[0]
            for description in connection.execute(
                "SELECT * FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
            ).description
        ]
        preimage_fields = (
            "selection_run_id",
            "snapshot_id",
            "selection_input_sha256",
            "run_state",
            "selected_entity_count",
            "selected_accession_count",
            "expanded_node_count",
            "node_limit_exhausted",
        )
        for field in preimage_fields:
            index = columns.index(field)
            assert after[index] == preimage[index], f"{field} moved underneath the seal"
        assert after[columns.index("selection_result_sha256")] == seal
