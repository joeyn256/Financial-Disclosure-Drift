"""Applied migration metadata is immutable, ordered provenance."""

from __future__ import annotations

import hashlib
import sqlite3
from importlib import resources
from pathlib import Path

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.storage import sqlite as sqlite_module
from disclosure_drift.storage.sqlite import (
    MIGRATIONS_PACKAGE,
    Migration,
    apply_migrations,
    available_migrations,
    connect,
    verify_applied_migrations,
)


def _migrated_database(tmp_path: Path) -> Path:
    path = tmp_path / "catalog.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
    return path


def _tamper(path: Path, sql: str, parameters: tuple[object, ...] = ()) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(sql, parameters)
        connection.commit()
    finally:
        connection.close()


def test_valid_unchanged_chain_reopens_successfully(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert verify_applied_migrations(connection) == tuple(
            migration.version for migration in available_migrations()
        )


def test_packaged_chain_is_contiguous_and_ends_at_0013() -> None:
    """Stage S6 adds exactly one additive migration on top of the accepted chain."""
    inventory = available_migrations()
    versions = tuple(migration.version for migration in inventory)
    assert versions == tuple(range(1, len(inventory) + 1))
    assert versions[-1] == 13
    assert inventory[-1].name == "m23_manifest_lifecycle_guards"
    assert inventory[-2].name == "m23_selection_entity_reasons"


def test_migration_0011_provenance_is_recorded_in_order(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    packaged = next(m for m in available_migrations() if m.version == 11)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version"
        ).fetchall()
    assert [row["version"] for row in rows] == list(range(1, 14))
    recorded = next(row for row in rows if row["version"] == 11)
    assert recorded["name"] == "m23_joint_selector_policy_reference"
    assert recorded["checksum_sha256"] == packaged.checksum_sha256


def test_migration_0012_provenance_is_recorded_in_order(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    packaged = next(m for m in available_migrations() if m.version == 12)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version"
        ).fetchall()
    assert [row["version"] for row in rows] == list(range(1, 14))
    recorded = next(row for row in rows if row["version"] == 12)
    assert recorded["name"] == "m23_selection_entity_reasons"
    assert recorded["checksum_sha256"] == packaged.checksum_sha256


def test_migration_0013_provenance_is_recorded_in_order(tmp_path: Path) -> None:
    """Stage S6's migration is recorded last, with its packaged checksum."""
    path = _migrated_database(tmp_path)
    packaged = next(m for m in available_migrations() if m.version == 13)
    with connect(path, writer=True) as connection:
        rows = connection.execute(
            "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version"
        ).fetchall()
    assert [row["version"] for row in rows] == list(range(1, 14))
    assert rows[-1]["name"] == "m23_manifest_lifecycle_guards"
    assert rows[-1]["checksum_sha256"] == packaged.checksum_sha256


@pytest.mark.parametrize("version", (11, 12, 13))
def test_altered_migration_bytes_block_reopen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, version: int
) -> None:
    path = _migrated_database(tmp_path)
    inventory = list(available_migrations())
    position = next(i for i, m in enumerate(inventory) if m.version == version)
    original = inventory[position]
    inventory[position] = Migration(
        version=original.version,
        name=original.name,
        sql=original.sql + "\n-- altered fixture\n",
    )
    monkeypatch.setattr(sqlite_module, "available_migrations", lambda: tuple(inventory))
    with pytest.raises(GateFailureError, match="checksum mismatch"), connect(path, writer=True):
        pass


def test_no_earlier_migration_mentions_the_s5_4_objects() -> None:
    """Decision 020 sections 8.2 and 11: migration 0012 edits, replaces, and
    reinterprets nothing that came before it, so the new table and the new
    feasible-transition trigger appear in migration 0012 and nowhere else."""
    packaged = {
        entry.name: entry.read_bytes()
        for entry in resources.files(MIGRATIONS_PACKAGE).iterdir()
        if entry.name.endswith(".sql")
    }
    new_objects = (
        b"pilot_selection_entity_reasons",
        b"pilot_selection_run_feasible_requires_reserve_disposition",
    )
    for name, content in packaged.items():
        if name == "0012_m23_selection_entity_reasons.sql":
            assert all(marker in content for marker in new_objects)
            continue
        if name == "0013_m23_manifest_lifecycle_guards.sql":
            # Migration 0013 names pilot_selection_entity_reasons only in its header
            # prose; it creates no table and no object belonging to migration 0012.
            assert b"CREATE TABLE" not in content
            continue
        for marker in new_objects:
            assert marker not in content, f"{marker!r} leaked into {name}"


_S6_TRIGGERS = (
    b"pilot_selection_run_insert_unsealed_guard",
    b"pilot_selection_run_result_hash_guard",
    b"pilot_manifest_versions_insert_guard",
    b"pilot_manifest_versions_identity_guard",
    b"pilot_manifest_versions_replacement_guard",
    b"pilot_selection_run_replacement_guard",
    b"pilot_selection_run_delete_guard",
    b"pilot_selection_run_identity_guard",
)


def test_migration_0013_objects_leak_into_no_earlier_migration() -> None:
    """Decision 021 section 15: migrations 0009 to 0012 are untouched by Stage S6."""
    packaged = {
        entry.name: entry.read_bytes()
        for entry in resources.files(MIGRATIONS_PACKAGE).iterdir()
        if entry.name.endswith(".sql")
    }
    for name, content in packaged.items():
        if name == "0013_m23_manifest_lifecycle_guards.sql":
            assert all(marker in content for marker in _S6_TRIGGERS)
            continue
        for marker in _S6_TRIGGERS:
            assert marker not in content, f"{marker!r} leaked into {name}"


def test_second_normal_application_is_idempotent(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    with connect(path, writer=True) as connection:
        assert apply_migrations(connection) == ()


def test_packaged_checksums_cover_exact_sql_bytes() -> None:
    packaged = {
        entry.name: hashlib.sha256(entry.read_bytes()).hexdigest()
        for entry in resources.files(MIGRATIONS_PACKAGE).iterdir()
        if entry.name.endswith(".sql")
    }
    for migration in available_migrations():
        filename = f"{migration.version:04d}_{migration.name}.sql"
        assert migration.checksum_sha256 == packaged[filename]
    assert (
        Migration(1, "fixture", "SELECT 1;\n").checksum_sha256
        != Migration(
            1,
            "fixture",
            "SELECT 1;\r\n",
        ).checksum_sha256
    )


def test_changed_packaged_sql_blocks_reopen_without_rewriting_checksum(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _migrated_database(tmp_path)
    inventory = list(available_migrations())
    original = inventory[2]
    inventory[2] = Migration(
        version=original.version,
        name=original.name,
        sql=original.sql + "\n-- altered fixture\n",
    )
    raw = sqlite3.connect(path)
    recorded_before = raw.execute(
        "SELECT checksum_sha256 FROM ops_schema_migrations WHERE version = 3"
    ).fetchone()[0]
    raw.close()

    monkeypatch.setattr(sqlite_module, "available_migrations", lambda: tuple(inventory))
    with pytest.raises(GateFailureError, match="checksum mismatch"), connect(path, writer=True):
        pass

    raw = sqlite3.connect(path)
    recorded_after = raw.execute(
        "SELECT checksum_sha256 FROM ops_schema_migrations WHERE version = 3"
    ).fetchone()[0]
    raw.close()
    assert recorded_after == recorded_before


def test_renamed_packaged_migration_is_rejected(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    inventory = list(available_migrations())
    original = inventory[3]
    inventory[3] = Migration(original.version, "renamed_fixture", original.sql)
    with connect(path) as connection, pytest.raises(GateFailureError, match="name mismatch"):
        verify_applied_migrations(connection, tuple(inventory))


@pytest.mark.parametrize(
    ("column", "value", "message"),
    (
        ("name", "renamed_in_catalog", "name mismatch"),
        ("checksum_sha256", "0" * 64, "checksum mismatch"),
    ),
)
def test_altered_stored_provenance_blocks_reopen(
    tmp_path: Path,
    column: str,
    value: str,
    message: str,
) -> None:
    path = _migrated_database(tmp_path)
    _tamper(
        path,
        f"UPDATE ops_schema_migrations SET {column} = ? WHERE version = 4",  # noqa: S608
        (value,),
    )
    with pytest.raises(GateFailureError, match=message), connect(path, writer=True):
        pass


def test_unknown_applied_version_blocks_reopen(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    _tamper(
        path,
        "INSERT INTO ops_schema_migrations "
        "(version, name, checksum_sha256, applied_at_utc) VALUES (99, 'unknown', ?, 'now')",
        ("f" * 64,),
    )
    with pytest.raises(GateFailureError, match="absent from the packaged inventory"), connect(path):
        pass


def test_applied_chain_gap_blocks_reopen(tmp_path: Path) -> None:
    path = _migrated_database(tmp_path)
    _tamper(path, "DELETE FROM ops_schema_migrations WHERE version = 4")
    with pytest.raises(GateFailureError, match="has a gap"), connect(path, writer=True):
        pass


@pytest.mark.parametrize(
    "inventory",
    (
        (
            Migration(1, "first", "SELECT 1;"),
            Migration(1, "duplicate", "SELECT 2;"),
        ),
        (
            Migration(2, "second", "SELECT 2;"),
            Migration(1, "first", "SELECT 1;"),
        ),
        (
            Migration(1, "first", "SELECT 1;"),
            Migration(3, "third", "SELECT 3;"),
        ),
    ),
)
def test_duplicate_reordered_or_gapped_injected_inventory_is_rejected(
    tmp_path: Path,
    inventory: tuple[Migration, ...],
) -> None:
    with (
        connect(tmp_path / "empty.sqlite3", writer=True) as connection,
        pytest.raises(GateFailureError, match="unique, ordered, and contiguous"),
    ):
        verify_applied_migrations(connection, inventory)
