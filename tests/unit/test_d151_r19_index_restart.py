"""D151-C31R2-R19A-C2 §29: deferred-index capture, drop, restart and rebuild.

The five declared secondary indexes are captured -- ordinal, name, table, exact stored DDL --
and dropped in ONE transaction that also commits the S1 applied unit; after that no code reads
their DDL from ``sqlite_master`` (it is gone) and the S16 units rebuild each index from the
persisted rows alone, one transaction, checkpoint and receipt each; a fresh process after the
DROP rebuilds them; the final set is exactly the seed catalog's, name for name and byte for byte
of DDL; a persisted set whose bytes moved, a missing row and a wrong expected set all refuse.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402


def _declared_indexes(catalog: Path) -> dict[str, tuple[str, str]]:
    connection = r19.readonly(catalog)
    try:
        return {
            str(row["name"]): (str(row["tbl_name"]), str(row["sql"]))
            for row in connection.execute(
                "SELECT name, tbl_name, sql FROM main.sqlite_master "
                "WHERE type = 'index' AND sql IS NOT NULL"
            )
        }
    finally:
        connection.close()


def _persisted(catalog: Path) -> list[sqlite3.Row]:
    connection = r19.readonly(catalog)
    try:
        return connection.execute(
            f"SELECT * FROM main.{cm.L2_DEFERRED_INDEXES_TABLE} ORDER BY ordinal"  # noqa: S608
        ).fetchall()
    finally:
        connection.close()


def test_g01_s1_persists_the_exact_ddl_in_the_drop_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    statements: list[str] = []
    r19.install_trace(monkeypatch, statements)
    seed = {
        name: value
        for name, value in _declared_indexes(estate.database).items()
        if name in cm.EXPECTED_DEFERRED_INDEX_NAMES
    }
    assert set(seed) == set(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    # Persisted and dropped inside ONE transaction: no COMMIT separates the two.
    persist = [
        i for i, s in enumerate(statements) if f"INTO main.{cm.L2_DEFERRED_INDEXES_TABLE}" in s
    ]
    drops = [i for i, s in enumerate(statements) if s.startswith("DROP INDEX main.")]
    assert len(persist) == 5 and len(drops) == 5
    begin = max(i for i, s in enumerate(statements) if s == "BEGIN IMMEDIATE" and i < min(persist))
    commit = min(i for i, s in enumerate(statements) if s == "COMMIT" and i > max(drops))
    assert not any(
        begin < i < commit for i, s in enumerate(statements) if s in {"COMMIT", "BEGIN IMMEDIATE"}
    )
    assert all(begin < i < commit for i in persist + drops)
    rows = _persisted(estate.catalog)
    assert [str(row["name"]) for row in rows] == list(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    assert [int(row["ordinal"]) for row in rows] == [0, 1, 2, 3, 4]
    for row in rows:
        table, sql = seed[str(row["name"])]
        assert (str(row["table_name"]), str(row["create_sql"])) == (table, sql)
    assert len({str(row["set_identity"]) for row in rows}) == 1
    # Dropped in the same transaction: none of the five exists, and the S1 unit binds the set.
    present = _declared_indexes(estate.catalog)
    assert not set(present) & set(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    unit = [cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog)][-1]
    assert unit.stage_id == "S1"
    assert unit.outcome_witness["deferred_index_count"] == 5
    assert unit.outcome_witness["deferred_index_set_identity"] == str(rows[0]["set_identity"])
    # The accepted enumeration and the successor's records agree on names and DDL.
    connection = r19.readonly(estate.database)
    try:
        legacy = cc._deferrable_indexes(connection)
        records = cc._deferrable_index_records(connection)
    finally:
        connection.close()
    assert dict(legacy) == {name: sql for _o, name, _t, sql in records}
    assert [name for _o, name, _t, _s in records] == sorted(name for name, _s in legacy)


def test_g02_a_fresh_process_after_the_drop_rebuilds_every_index_from_the_persisted_ddl(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    first = r19.spawn_production(
        tmp_path, r19.production_request(estate, stop_after="S1"), label="drop"
    )
    assert first["returncode"] == 0, first["stderr"][-2000:]
    assert not set(_declared_indexes(estate.catalog)) & set(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    second = r19.spawn_production(
        tmp_path, r19.production_request(estate, stop_after="S16.4"), label="rebuild"
    )
    assert second["returncode"] == 0, second["stderr"][-2000:]
    assert second["result"]["stages"][-5:] == ["S16.0", "S16.1", "S16.2", "S16.3", "S16.4"]
    seed = _declared_indexes(estate.database)
    rebuilt = _declared_indexes(estate.catalog)
    for name in cm.EXPECTED_DEFERRED_INDEX_NAMES:
        assert rebuilt[name] == seed[name], name
    units = {
        u.stage_id: u
        for u in (cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog))
    }
    for index, name in enumerate(cm.EXPECTED_DEFERRED_INDEX_NAMES):
        witness = units[f"S16.{index}"].outcome_witness
        assert witness["index"] == name and witness["create_sql"] == seed[name][1]
    third = r19.spawn_production(tmp_path, r19.production_request(estate), label="finish")
    assert third["returncode"] == 0 and third["result"]["terminal"]
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_g03_a_persisted_set_whose_bytes_moved_or_a_missing_row_refuses_the_rebuild(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S15P"))
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(
            f"UPDATE main.{cm.L2_DEFERRED_INDEXES_TABLE} SET create_sql = "  # noqa: S608
            "replace(create_sql, 'CREATE INDEX', 'CREATE INDEX IF NOT EXISTS') WHERE ordinal = 0"
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="never executes DDL the plan did not seal"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S16.0"))
    assert r19.stage_ids(estate.catalog)[-1] == "S15P"
    assert not set(_declared_indexes(estate.catalog)) & set(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(
            f"DELETE FROM main.{cm.L2_DEFERRED_INDEXES_TABLE} WHERE ordinal = 0"  # noqa: S608
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="deferred-index rows persisted where 5"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S16.0"))


def test_g04_a_world_whose_declared_set_disagrees_with_the_plan_refuses_before_the_drop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    original = cm._deferrable_index_records

    def four(connection: sqlite3.Connection) -> tuple[tuple[int, str, str, str], ...]:
        records = original(connection)
        files = [str(row["file"]) for row in connection.execute("PRAGMA database_list")]
        # The WORLD's own enumeration disagrees with the plan; the seed's stays exact.
        return records[:4] if any("successor-final" in file for file in files) else records

    monkeypatch.setattr(cm, "_deferrable_index_records", four)
    with pytest.raises(cm.ChunkMultipassError, match="exactly"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    assert r19.stage_ids(estate.catalog) == ["S0"]
    assert set(_declared_indexes(estate.catalog)) >= set(cm.EXPECTED_DEFERRED_INDEX_NAMES)
    assert _persisted(estate.catalog) == []
    monkeypatch.setattr(cm, "_deferrable_index_records", original)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    assert outcome.completed_stage_ids == ("S0", "S1")
