"""D151-C31R2-R19A-C2 §21-§23: connection-state reconstruction and the mode=ro pre-state probe.

* the probe is SQLite-logically read-only through the accepted ``read_only=True`` helper: on a
  clean world it leaves main byte-identical and creates at most the two exact sidecars; a
  zero-length log is admissible; a preexisting committed nonzero log is preserved inode, length
  and SHA-256 while its committed rows stay visible; an interrupted uncommitted tail left by a
  killed writer is never folded, and the next process re-executes exactly the interrupted stage;
* a read-write or ``immutable=1`` substitution is detected: the first folds a committed log
  before classification, the second cannot see a StagePlan committed only in the log;
* every reopen re-establishes row factory, ``foreign_keys``, the exact cache pragma and the three
  deterministic correction functions -- read back from SQLite -- and seals them as one identity
  every applied unit binds; a StagePlan identity that differs between the probe and the writer
  refuses before any mutation; S12 in one process and S13 in another both succeed;
* exactly one dedicated test exercises the owner-selected 512 MiB budget.
"""

from __future__ import annotations

import hashlib
import shutil
import signal
import sqlite3
import subprocess
import sys
import textwrap
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    WORKING_CATALOG_FILENAME,
    cache_size_pragma,
)
from disclosure_drift.storage import sqlite as storage_sqlite  # noqa: E402

DETERMINISTIC = 0x800


@contextmanager
def _immutable_context(path: Path) -> Iterator[sqlite3.Connection]:
    """The forbidden substitution: an ``immutable=1`` handle standing in for the probe."""
    handle = sqlite3.connect(f"file:{path}?immutable=1", uri=True)
    handle.row_factory = sqlite3.Row
    try:
        yield handle
    finally:
        handle.close()


def _files(world: Path) -> dict[str, int]:
    return {p.name: p.stat().st_size for p in world.iterdir()}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_world(estate: r19.SuccessorWorld, tmp_path: Path, name: str) -> Path:
    copy = tmp_path / name
    shutil.copytree(estate.world, copy)
    return copy


def _killed_committer(catalog: Path, statement: str) -> None:
    """A child process that commits ``statement`` into ``catalog`` and is SIGKILLed before close."""
    program = textwrap.dedent(
        f"""
        import os, signal, sqlite3
        connection = sqlite3.connect({str(catalog)!r}, isolation_level=None)
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute({statement!r})
        connection.execute("COMMIT")
        os.kill(os.getpid(), signal.SIGKILL)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", program], check=False, capture_output=True
    )
    assert completed.returncode == -signal.SIGKILL, completed.stderr


# ==========================================================================
# A, B, E: clean world, zero-length log, housekeeping is not a conflict
# ==========================================================================
def test_k01_the_probe_on_a_clean_world_preserves_main_and_leaves_only_housekeeping(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S1"))
    before = _files(estate.world)
    assert set(before) == {WORKING_CATALOG_FILENAME, "run_progress.sqlite3"}
    main_before = _sha(estate.catalog)
    identity = cm._prestate_stage_plan_identity(estate.catalog)
    after = _files(estate.world)
    assert _sha(estate.catalog) == main_before
    assert identity.contract == cm.L2_STAGE_PLAN_CONTRACT_V2
    assert identity.route == cm.SUCCESSOR_ROUTE_PRODUCTION
    assert identity.snapshot_before.wal_class == cm._WAL_ABSENT
    assert identity.snapshot_after.wal_class in {cm._WAL_ABSENT, cm._WAL_ZERO}
    extra = set(after) - set(before)
    assert extra <= {f"{WORKING_CATALOG_FILENAME}-wal", f"{WORKING_CATALOG_FILENAME}-shm"}
    assert after.get(f"{WORKING_CATALOG_FILENAME}-wal", 0) == 0
    assert cm._normalized_wal_class(identity.snapshot_after) == 0
    # B: the zero-length log left behind is admissible, and the engine continues over it.
    again = cm._prestate_stage_plan_identity(estate.catalog)
    assert again.stage_plan_identity == identity.stage_plan_identity
    assert again.snapshot_before.wal_class in {cm._WAL_ZERO, cm._WAL_ABSENT}
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    assert outcome.completed_stage_ids[-1] == "S2"
    # E: directory inventory is never database state -- the sidecars decided nothing.
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]


# ==========================================================================
# C, F: a committed nonzero log is preserved; the two forbidden modes are detectable
# ==========================================================================
def test_k02_a_committed_nonzero_log_is_preserved_by_the_probe_and_folded_only_by_read_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    copy = _copy_world(estate, tmp_path, "copy-c")
    catalog = copy / WORKING_CATALOG_FILENAME
    _killed_committer(
        catalog,
        f"INSERT INTO main.{cm.L2_PLAN_WITNESS_TABLE} VALUES ('probe-acc', 'probe-id', 0)",  # noqa: S608
    )
    wal = catalog.with_name(catalog.name + "-wal")
    assert wal.stat().st_size > 0
    before = (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(catalog))
    identity = cm._prestate_stage_plan_identity(catalog)
    assert identity.snapshot_before.wal_class == cm._WAL_NONZERO
    assert identity.snapshot_after.wal_class == cm._WAL_NONZERO
    assert (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(catalog)) == before
    # The committed row is visible through mode=ro, invisible to immutable=1.
    visible = r19.wal_reader(catalog)
    try:
        assert (
            visible.execute(f"SELECT COUNT(*) FROM main.{cm.L2_PLAN_WITNESS_TABLE}").fetchone()[0]  # noqa: S608
            == 1
        )  # noqa: S608
    finally:
        visible.close()
    blind = r19.readonly(catalog)
    try:
        assert (
            blind.execute(f"SELECT COUNT(*) FROM main.{cm.L2_PLAN_WITNESS_TABLE}").fetchone()[0]  # noqa: S608
            == 0
        )  # noqa: S608
    finally:
        blind.close()
    assert (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(catalog)) == before
    # F: a read-write substitution folds the committed log before classification -- caught.
    original = storage_sqlite.connect

    def read_write(path: Path, *, writer: bool = False, read_only: bool = False) -> Any:
        return original(path, writer=writer, read_only=False)

    monkeypatch.setattr(cm, "connect", read_write)
    with pytest.raises(
        cm.ChunkMultipassError, match="changed the world's main file|changed a preexisting nonzero"
    ):
        cm._prestate_stage_plan_identity(catalog)
    monkeypatch.setattr(cm, "connect", original)


def test_k03_an_immutable_substitution_cannot_see_a_plan_committed_only_in_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    copy = _copy_world(estate, tmp_path, "copy-f")
    catalog = copy / WORKING_CATALOG_FILENAME
    # Move the StagePlan row out of main and back in through the log alone.
    connection = r19.writer(catalog)
    try:
        row = connection.execute(f"SELECT * FROM main.{cm.L2_STAGE_PLAN_TABLE}").fetchone()  # noqa: S608
        values = tuple(row)
        connection.execute(f"DELETE FROM main.{cm.L2_STAGE_PLAN_TABLE}")  # noqa: S608
        connection.execute("PRAGMA main.wal_checkpoint(TRUNCATE)")
    finally:
        connection.close()
    placeholders = ", ".join("?" for _ in values)
    # SQL literals, not Python reprs: the /2 body carries the registry's quoted SQL text.
    rendered = ", ".join(
        "'" + v.replace("'", "''") + "'" if isinstance(v, str) else repr(v) for v in values
    )
    _killed_committer(catalog, f"INSERT INTO main.{cm.L2_STAGE_PLAN_TABLE} VALUES ({rendered})")  # noqa: S608
    assert placeholders  # the row shape is what was moved
    assert cm._prestate_stage_plan_identity(catalog).stage_plan_identity == str(
        row["stage_plan_identity"]
    )
    original = storage_sqlite.connect

    def immutable(path: Path, *, writer: bool = False, read_only: bool = False) -> Any:
        return _immutable_context(path)

    monkeypatch.setattr(cm, "connect", immutable)
    with pytest.raises(cm.ChunkMultipassError, match="carries no successor StagePlan"):
        cm._prestate_stage_plan_identity(catalog)
    monkeypatch.setattr(cm, "connect", original)


# ==========================================================================
# D: an interrupted, uncommitted tail is never folded and the stage re-executes
# ==========================================================================
def test_k04_a_writer_killed_mid_stage_leaves_a_tail_the_next_process_reclassifies(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    # A one-kibibyte page cache: the interrupted transaction spills into the log before the
    # kill, which is the shape a real 16-million-row stage has and a tiny world does not.
    request = r19.production_request(estate, cache_bytes=1024)
    extra = (
        "import os, signal;"
        "_orig = cm._stage_table_load;"
        "cm._stage_table_load = (lambda connection, aliases, ctx, stage, units, instr: "
        "(_orig(connection, aliases, ctx, stage, units, instr), "
        "os.kill(os.getpid(), signal.SIGKILL))[0] "
        "if stage.stage_id == 'S3' else _orig(connection, aliases, ctx, stage, units, instr));"
    )
    killed = r19.spawn_production(tmp_path, request, label="killed", extra=extra)
    assert killed["returncode"] == -signal.SIGKILL
    wal = estate.catalog.with_name(estate.catalog.name + "-wal")
    assert wal.exists() and wal.stat().st_size > 0
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert len(r19.receipt_files(estate.receipt_root)) == 3
    before = (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(estate.catalog))
    identity = cm._prestate_stage_plan_identity(estate.catalog)
    assert identity.snapshot_after.wal_class == cm._WAL_NONZERO
    assert (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(estate.catalog)) == before
    resumed = r19.spawn_production(tmp_path, request, label="resumed")
    assert resumed["returncode"] == 0, resumed["stderr"][-2000:]
    assert resumed["result"]["terminal"]
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


# ==========================================================================
# §21: reconstruction on every reopen, identity bound, fresh-process S12 then S13
# ==========================================================================
def test_k05_every_reopen_reestablishes_and_verifies_the_connection_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    original = cm._establish_successor_connection_state
    observed: list[dict[str, Any]] = []

    def observing(connection: sqlite3.Connection, plan: Any, proof: Any) -> Any:
        state = original(connection, plan, proof)
        functions = {
            str(row["name"]): (int(row["narg"]), int(row["flags"]))
            for row in connection.execute("PRAGMA function_list")
            if str(row["name"]).startswith("dd_")
        }
        observed.append(
            {
                "cache": int(connection.execute("PRAGMA cache_size").fetchone()[0]),
                "foreign_keys": int(connection.execute("PRAGMA foreign_keys").fetchone()[0]),
                "row": type(connection.execute("SELECT 1").fetchone()).__name__,
                "functions": functions,
                "identity": state.identity,
            }
        )
        return state

    monkeypatch.setattr(cm, "_establish_successor_connection_state", observing)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S4"))
    assert len(observed) >= 6  # S0 plus a classification and an execution session per stage
    for item in observed:
        assert item["cache"] == cache_size_pragma(cm.DEFAULT_SYNTHETIC_CACHE_BYTES) == -8192
        assert item["foreign_keys"] == 1 and item["row"] == "Row"
        assert item["functions"] == {
            "dd_stable_id": (5, DETERMINISTIC),
            "dd_rival_fields_json": (1, DETERMINISTIC),
            "dd_reconstructed_fields_json": (6, DETERMINISTIC),
        }
    assert len({item["identity"] for item in observed}) == 1
    units = [cm.AppliedUnit.from_row(row) for row in r19.applied_units(estate.catalog)]
    assert {unit.connection_state_identity for unit in units} == {observed[0]["identity"]}
    for path in r19.receipt_files(estate.receipt_root):
        assert cm.read_stage_receipt(path)["connection_state_identity"] == observed[0]["identity"]


def test_k06_the_state_helper_refuses_a_missing_function_and_binds_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S0"))
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    proof = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )
    copy = _copy_world(estate, tmp_path, "state-copy")
    connection = r19.writer(copy / WORKING_CATALOG_FILENAME)
    try:
        state = cm._establish_successor_connection_state(connection, plan, proof)
        assert state.body["cache_bytes"] == cm.DEFAULT_SYNTHETIC_CACHE_BYTES
        assert state.body["cache_size_pragma"] == -8192
        assert state.body["setup_complete"] is True
        assert state.body["tool_manifest_identity"] == plan.tool_manifest_identity
        # Registration is reached through the accepted mechanism; removing it is caught.
        monkeypatch.setattr(cm, "_register_correction_functions", lambda connection: None)
        fresh = r19.writer(copy / WORKING_CATALOG_FILENAME)
        try:
            with pytest.raises(
                cm.ChunkMultipassError, match="is not registered on this connection"
            ):
                cm._establish_successor_connection_state(fresh, plan, proof)
        finally:
            fresh.close()
    finally:
        connection.close()


def test_k07_a_stage_plan_identity_that_moved_between_probe_and_writer_refuses_before_mutation(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    connection = r19.writer(estate.catalog)
    try:
        connection.execute(
            f"UPDATE main.{cm.L2_STAGE_PLAN_TABLE} "  # noqa: S608
            "SET stage_plan_identity = "
            "(CASE WHEN substr(stage_plan_identity, 1, 1) = '0' THEN '1' ELSE '0' END) "
            "|| substr(stage_plan_identity, 2)"
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="minimal StagePlan identity"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]


def test_k08_s12_in_one_process_and_s13_in_another_both_reestablish_the_functions(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    first = r19.spawn_production(
        tmp_path, r19.production_request(estate, stop_after="S12"), label="a"
    )
    assert first["returncode"] == 0, first["stderr"][-2000:]
    assert first["result"]["stages"][-1] == "S12"
    second = r19.spawn_production(
        tmp_path, r19.production_request(estate, stop_after="S13"), label="b"
    )
    assert second["returncode"] == 0, second["stderr"][-2000:]
    assert second["result"]["stages"][-1] == "S13"
    units = {
        u.stage_id: u
        for u in (cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog))
    }
    assert units["S12"].connection_state_identity == units["S13"].connection_state_identity
    assert units["S13"].predecessor_unit_identity == units["S12"].unit_identity
    assert units["S13"].rows_written > 0 and units["S12"].outcome_witness["rows_staged"] >= 0
    third = r19.spawn_production(tmp_path, r19.production_request(estate), label="c")
    assert third["returncode"] == 0 and third["result"]["terminal"]
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


# ==========================================================================
# §40: the one dedicated 512 MiB cache test, and the cache validator
# ==========================================================================
def _minimal_plan(cache_bytes: int) -> cm.L2StagePlan:
    """A minimal EXECUTABLE (/2) plan: every /2 field, over a one-chunk production registry."""
    assert c1.PINNED is not None
    registry = cm.successor_statement_registry(cm.SUCCESSOR_ROUTE_PRODUCTION, 1)
    return cm.L2StagePlan.from_record(
        {
            "contract": cm.L2_STAGE_PLAN_CONTRACT_V2,
            "route": cm.SUCCESSOR_ROUTE_PRODUCTION,
            "successor_run_id": "cache-test",
            "canonical_world_path": "/nonexistent/world",
            "cache_bytes": cache_bytes,
            "input_group_count": 0,
            "intermediates": [],
            "predecessor_completed_group_count": 0,
            "counter_source_count": 1,
            "stage_graph": [],
            "tool_manifest_identity": cm._runtime_tool_manifest().identity,
            "repository_head_sha": c1.PINNED.head_sha,
            "repository_tree_sha": c1.PINNED.tree_sha,
            "stage_receipt_root": "/nonexistent/receipts",
            "statement_progress_root": "/nonexistent/receipts/statement-progress",
            "statement_registry": [dict(item) for item in registry],
            "statement_registry_identity": cm._registry_identity(
                cm.SUCCESSOR_ROUTE_PRODUCTION, 1, registry
            ),
            **r19.SYNTHETIC_OBSERVABILITY,
            "wal_watchdog_storage_ceiling_bytes": r19.R19B_REQUIREMENTS.level_two_transient_bytes,
        }
    )


def test_k09_the_owner_selected_512_mib_cache_is_supported_and_bound(tmp_path: Path) -> None:
    owner = _minimal_plan(536_870_912)
    default = _minimal_plan(cm.DEFAULT_SYNTHETIC_CACHE_BYTES)
    assert owner.identity != default.identity
    proof = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="t"
    )
    catalog = tmp_path / "tiny.sqlite3"
    connection = sqlite3.connect(catalog, isolation_level=None)
    try:
        connection.execute("CREATE TABLE t (x)")
        state = cm._establish_successor_connection_state(connection, owner, proof)
        assert int(connection.execute("PRAGMA cache_size").fetchone()[0]) == -524288
        assert state.body["cache_bytes"] == 536_870_912
        assert state.body["cache_size_pragma"] == -524288
    finally:
        connection.close()
    other = sqlite3.connect(catalog, isolation_level=None)
    try:
        assert (
            cm._establish_successor_connection_state(other, default, proof).identity
            != state.identity
        )
    finally:
        other.close()


def test_k10_the_cache_validator_refuses_every_wrong_shape_independently() -> None:
    for value in (None, True, False, 1_048_576.0, 0, -1024, 1000, "8388608"):
        with pytest.raises(cm.ChunkMultipassError):
            cm.require_successor_cache_bytes(value)
    assert cm.require_successor_cache_bytes(536_870_912) == 536_870_912
    assert cache_size_pragma(536_870_912) == -524288
    record = {
        "kind": cm.SUCCESSOR_REQUEST_KIND_FINAL,
        "route": cm.SUCCESSOR_ROUTE_PRODUCTION,
        "plan_path": "p",
        "schedule_path": "s",
        "intermediates_root": "i",
        "internal_root": "c",
        "external_root": None,
        "operational_catalog": "o",
        "world_directory": "w",
        "stage_receipt_root": "r",
        "run_id": "run",
        "predecessor_run_id": "pred",
        "predecessor_checkpoint_count": 0,
        "predecessor_tip_ordinal": 0,
        "predecessor_tip_identity": "none",
        "predecessor_completed_group_count": 0,
        "cache_bytes": None,
        "repository_head_sha": "a" * 40,
        "repository_tree_sha": "b" * 40,
        "storage_requirements": {},
        "expected_sqlite_temp_binding": {},
        "statement_observability": dict(r19.SYNTHETIC_OBSERVABILITY),
        "capacity_observations": [],
        "stop_after_stage": None,
    }
    with pytest.raises(cm.ChunkMultipassError, match="requires cache_bytes"):
        cm.SuccessorFinalRequest.from_record(record)
    with pytest.raises(cm.ChunkMultipassError, match="must be an int"):
        cm.SuccessorFinalRequest.from_record({**record, "cache_bytes": True})
    with pytest.raises(cm.ChunkMultipassError, match="must be an int"):
        cm.SuccessorFinalRequest.from_record({**record, "cache_bytes": 1_048_576.0})


def test_k11_the_probe_predicate_refuses_a_changed_log_even_when_main_is_untouched() -> None:
    main = cm._FileState("working_catalog.sqlite3", "file", 1, 4096, "a" * 64)
    wal = cm._FileState("working_catalog.sqlite3-wal", "file", 2, 8192, "b" * 64)
    shm = cm._FileState("working_catalog.sqlite3-shm", "absent", None, None, None)
    before = cm._WorldSnapshot(main=main, wal=wal, wal_class=cm._WAL_NONZERO, shm=shm)
    same = cm._WorldSnapshot(main=main, wal=wal, wal_class=cm._WAL_NONZERO, shm=shm)
    cm._require_probe_preserved(before, same)
    moved = cm._FileState("working_catalog.sqlite3-wal", "file", 2, 8192, "c" * 64)
    after = cm._WorldSnapshot(main=main, wal=moved, wal_class=cm._WAL_NONZERO, shm=shm)
    with pytest.raises(cm.ChunkMultipassError, match="changed a preexisting nonzero"):
        cm._require_probe_preserved(before, after)
    shorter = cm._FileState("working_catalog.sqlite3-wal", "file", 2, 4096, "b" * 64)
    with pytest.raises(cm.ChunkMultipassError, match="changed a preexisting nonzero"):
        cm._require_probe_preserved(
            before, cm._WorldSnapshot(main=main, wal=shorter, wal_class=cm._WAL_NONZERO, shm=shm)
        )
    # Housekeeping around a clean boundary is never a conflict.
    zero = cm._FileState(
        "working_catalog.sqlite3-wal", "file", 3, 0, hashlib.sha256(b"").hexdigest()
    )
    absent = cm._FileState("working_catalog.sqlite3-wal", "absent", None, None, None)
    cm._require_probe_preserved(
        cm._WorldSnapshot(main=main, wal=absent, wal_class=cm._WAL_ABSENT, shm=shm),
        cm._WorldSnapshot(main=main, wal=zero, wal_class=cm._WAL_ZERO, shm=shm),
    )
    cm._require_probe_preserved(
        cm._WorldSnapshot(main=main, wal=zero, wal_class=cm._WAL_ZERO, shm=shm),
        cm._WorldSnapshot(main=main, wal=absent, wal_class=cm._WAL_ABSENT, shm=shm),
    )
