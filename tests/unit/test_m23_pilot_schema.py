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
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_candidate_accession_registrants "
            "(snapshot_id, accession_plain, registrant_cik_numeric, registrant_cik_padded, "
            "role, is_anchor, evidence_level, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, 'unavailable', '2026-01-01T00:00:00Z')",
            (
                snapshot_id,
                accession_plain,
                registrant_cik_numeric,
                f"{registrant_cik_numeric:010d}",
                "anchor" if is_anchor else "associated",
                1 if is_anchor else 0,
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


def test_migration_inventory_is_contiguous_through_0009() -> None:
    versions = tuple(migration.version for migration in available_migrations())
    assert versions == tuple(range(1, 10))
    assert versions[-1] == 9


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


def test_fresh_database_applies_migrations_through_0009(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        cursor = connection.execute("SELECT version FROM ops_schema_migrations ORDER BY version")
        versions = tuple(row["version"] for row in cursor.fetchall())
    assert versions == tuple(range(1, 10))


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


def test_exactly_twenty_one_pilot_tables_exist(tmp_path: Path) -> None:
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
    }
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%'"
        ).fetchall()
    found = {row["name"] for row in rows}
    assert found == expected
    assert len(found) == 21


def test_every_pilot_table_is_strict(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name LIKE 'pilot_%'"
        ).fetchall()
    assert len(rows) == 21
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
        # no registrant row at all: zero anchors
        with pytest.raises(
            sqlite3.IntegrityError, match="requires exactly one anchor per accession"
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
            anchor_cik_numeric=1,
            multi_registrant=1,
        )
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=1,
            is_anchor=True,
        )
        # only one registrant row exists, but multi_registrant = 1
        with pytest.raises(sqlite3.IntegrityError, match="multi_registrant flag inconsistent"):
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
            anchor_cik_numeric=1,
            multi_registrant=1,
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
        _freeze_snapshot(connection, snapshot_id=snapshot_id)
        state = connection.execute(
            "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()["snapshot_state"]
    assert state == "frozen"


def test_multi_registrant_flag_false_with_extra_row_fails_without_review_reason(
    tmp_path: Path,
) -> None:
    path = _migrated_database(tmp_path)
    snapshot_id = _hex("multi-registrant-false-unreviewed")
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
        _insert_registrant(
            connection,
            snapshot_id=snapshot_id,
            accession_plain="acc-1",
            registrant_cik_numeric=2,
            is_anchor=False,
        )
        with pytest.raises(sqlite3.IntegrityError, match="multi_registrant flag inconsistent"):
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


def _insert_selected_entity(
    connection: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    cik_numeric: int,
    selected_order: int,
) -> None:
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selected_entities "
            "(selection_run_id, snapshot_id, cik_numeric, selected_order, entity_hash_sha256, "
            "entity_role, candidate_category, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, 'operating', 'operating', '2026-01-01T00:00:00Z')",
            (
                selection_run_id,
                snapshot_id,
                cik_numeric,
                selected_order,
                _hex(f"entity-hash:{selection_run_id}:{cik_numeric}"),
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
    connection: sqlite3.Connection, *, snapshot_id: str, run_id: str
) -> None:
    """Seed a running selection run with exactly 24 actual selected-entity and
    selected-accession rows, but leave the declared count columns untouched (B1)."""
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
        _running_selection_run(connection, selection_run_id=run_id, snapshot_id=snapshot_id)
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
