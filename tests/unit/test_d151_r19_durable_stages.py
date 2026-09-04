"""D151-C31R2-R19A-C2: the durable Level-Two stage spine -- core behaviour and shared drivers.

What is proved here, over the committed synthetic worlds every accepted multipass test uses:

* the production successor runs its exact stage graph -- one transaction per stage, the
  applied-unit row committed with the semantic writes, an exact ``PRAGMA
  main.wal_checkpoint(TRUNCATE)``, an immutable receipt -- and the world it builds is
  semantically the accepted legacy final world, counter for counter;
* the StagePlan is variable-count and its input-group equality rules refuse before any world;
* a stage that fails before COMMIT leaves neither its data nor its row, and the applied-unit
  insert sits outside the accepted write containment, which still admits exactly the sixteen
  accepted tables;
* the statement order per stage is ATTACH, BEGIN IMMEDIATE, writes, applied row, COMMIT, DETACH,
  ``PRAGMA main.wal_checkpoint(TRUNCATE)`` -- never a checkpoint over an attachment or inside a
  transaction, never more than nine attachments;
* a receipt is published only after commit, checkpoint and validation; committed data without a
  receipt converges without re-execution; a receipt without data, a gap and a duplicate refuse;
* world initialization is a create-once attempt promoted by one rename with the parent fsynced.

The drivers below are shared by every other ``test_d151_r19_*`` module.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    FINAL_WORLD_RECEIPT_FILENAME,
    write_once_json,
)
from disclosure_drift.m3.offline_parse import E0_PERMITTED_TABLES  # noqa: E402
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402

#: The exact production stage graph over a ten-chunk world (two intermediates, two batches).
PRODUCTION_STAGE_IDS_10 = (
    "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", "S11", "S12", "S13", "S14",
    "S15P", "S16.0", "S16.1", "S16.2", "S16.3", "S16.4", "S17A.0", "S17B.0", "S17A.1", "S17B.1",
    "S17C", "S18", "S19", "S20P", "S21P", "S22P", "S23P",
)  # fmt: skip

#: Every accepted E0 table, exactly: the containment allowlist R17 fixed and Decision 094 widened.
ACCEPTED_E0_TABLES = frozenset(
    {
        "census_parser_runs",
        "census_parsed_records",
        "census_structural_observations",
        "census_accessions",
        "census_accession_observations",
        "census_accession_registrants",
        "census_registrants",
        "census_registrant_observations",
        "census_accession_field_resolutions",
        "census_accession_cohort_resolutions",
        "census_quarantined_records",
        "census_historical_references",
        "census_malformed_historical_references",
        "census_candidate_lineage_edges",
        "census_calendar_days",
        "reference_sic_codes",
    }
)


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The accepted seams: pinned repository, synthetic authority, temp root and volume."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared drivers
# ==========================================================================
@dataclass
class SuccessorWorld:
    """A prepared successor input estate: chunks, intermediates, requests, and the legacy oracle."""

    database: Path
    run: dict[str, Any]
    succ: dict[str, Any]
    legacy: dict[str, Any] | None
    world: Path
    receipt_root: Path
    requirements: ct.MultipassStorageRequirements = c13.REQUIREMENTS

    @property
    def schedule(self) -> cm.MergeSchedule:
        return self.succ["schedule"]  # type: ignore[no-any-return]

    @property
    def catalog(self) -> Path:
        return self.world / WORKING_CATALOG_FILENAME


def write_group_requests(run: dict[str, Any], succ: dict[str, Any], database: Path) -> None:
    """The group request documents beside each selected attempt, as the accepted launcher writes."""
    for group, receipt in zip(succ["schedule"].groups, succ["intermediates"], strict=True):
        directory = cm.intermediate_attempt_directory(
            succ["intermediates_root"], group.group_id, receipt.attempt
        )
        request = c13.group_request(
            run,
            schedule_path=succ["schedule_path"],
            group_id=group.group_id,
            attempt=receipt.attempt,
            attempt_directory=directory,
            database=database,
        )
        write_once_json(
            directory.parent / f"{group.group_id}-{receipt.attempt:03d}-request.json",
            dict(request.as_record()),
        )


def prepare(
    tmp_path: Path,
    *,
    legacy: bool = True,
    label: str = "successor",
    requirements: ct.MultipassStorageRequirements = c13.REQUIREMENTS,
    **shape: Any,
) -> SuccessorWorld:
    """Chunks, level-1 intermediates with their requests, and (optionally) the legacy final."""
    database, _tree, run = c13i.ten_chunk_run(tmp_path, **shape)
    legacy_result = (
        c13.merge_in_process(run, database, label="legacy", requirements=requirements)
        if legacy
        else None
    )
    succ = c13.merge_in_process(
        run, database, label=label, finalize=False, requirements=requirements
    )
    write_group_requests(run, succ, database)
    return SuccessorWorld(
        database=database,
        run=run,
        succ=succ,
        legacy=legacy_result,
        world=succ["multipass_root"] / "successor-final",
        receipt_root=succ["multipass_root"] / "successor-receipts",
        requirements=requirements,
    )


def production_request(
    estate: SuccessorWorld, *, stop_after: str | None = None, **overrides: Any
) -> cm.SuccessorFinalRequest:
    """One production successor request over the prepared estate."""
    assert c1.PINNED is not None
    fields: dict[str, Any] = {
        "route": cm.SUCCESSOR_ROUTE_PRODUCTION,
        "plan_path": str(estate.run["plan_path"]),
        "schedule_path": str(estate.succ["schedule_path"]),
        "intermediates_root": str(estate.succ["intermediates_root"]),
        "internal_root": str(estate.run["chunk_root"]),
        "external_root": None,
        "operational_catalog": str(estate.database),
        "world_directory": str(estate.world),
        "stage_receipt_root": str(estate.receipt_root),
        "run_id": "r19-successor",
        "predecessor_run_id": "c13-run",
        "predecessor_checkpoint_count": 0,
        "predecessor_tip_ordinal": 0,
        "predecessor_tip_identity": "none",
        "predecessor_completed_group_count": len(estate.schedule.groups),
        "cache_bytes": cm.DEFAULT_SYNTHETIC_CACHE_BYTES,
        "repository_head_sha": c1.PINNED.head_sha,
        "repository_tree_sha": c1.PINNED.tree_sha,
        "storage_requirements": dict(estate.requirements.as_record()),
        "expected_sqlite_temp_binding": c13.synthetic_expected_binding(estate.world),
        "stop_after_stage": stop_after,
    }
    fields.update(overrides)
    return cm.SuccessorFinalRequest(**fields)


def readonly(catalog: Path) -> sqlite3.Connection:
    """A raw ``immutable=1`` inspection handle over a TEST-OWNED, checkpointed world catalog.

    ``immutable=1`` rather than ``mode=ro`` for INSPECTION: a checkpointed successor world holds
    everything in its main file, and an immutable handle creates none of the sidecars a
    ``mode=ro`` handle leaves behind -- so a test can list the world's exact file set after
    inspecting it. Tests that must observe a live write-ahead log use :func:`wal_reader`.
    """
    connection = sqlite3.connect(f"file:{catalog}?immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def wal_reader(catalog: Path) -> sqlite3.Connection:
    """A raw ``mode=ro`` handle: sees the committed write-ahead log, leaves housekeeping."""
    connection = sqlite3.connect(f"{catalog.absolute().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def writer(catalog: Path) -> sqlite3.Connection:
    """A raw read-write handle over a TEST-OWNED world catalog, for deliberate tampering."""
    connection = sqlite3.connect(catalog, isolation_level=None)
    connection.row_factory = sqlite3.Row
    return connection


def applied_units(catalog: Path) -> list[sqlite3.Row]:
    connection = readonly(catalog)
    try:
        return connection.execute(
            f"SELECT * FROM main.{cm.L2_APPLIED_UNITS_TABLE} ORDER BY stage_ordinal"  # noqa: S608
        ).fetchall()
    finally:
        connection.close()


def stage_ids(catalog: Path) -> list[str]:
    return [str(row["stage_id"]) for row in applied_units(catalog)]


def receipt_files(receipt_root: Path) -> list[Path]:
    return sorted(path for path in receipt_root.iterdir() if path.name.startswith("stage-"))


def count(catalog: Path, table: str) -> int:
    connection = readonly(catalog)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0])  # noqa: S608
    finally:
        connection.close()


def counters(record: Mapping[str, object]) -> tuple[int, int, int, int]:
    return (
        int(record["first_witness_accessions_corrected"]),  # type: ignore[call-overload]
        int(record["first_witness_rows_staged"]),  # type: ignore[call-overload]
        int(record["evidence_members_corrected"]),  # type: ignore[call-overload]
        int(record["evidence_delta"]),  # type: ignore[call-overload]
    )


def successor_child_program(repo_root: Path) -> str:
    """A fresh-interpreter program running the production successor under the accepted seams."""
    return (
        "import json, sys;"
        "from pathlib import Path;"
        "from disclosure_drift.m3 import repository_identity as ri;"
        "ri.running_repository_identity = lambda: ri.repository_identity_at("
        f"Path({str(repo_root)!r}));"
        "from disclosure_drift.m3 import external_working_root as ewr;"
        "ewr.macos_volume_identity = lambda path: ewr.VolumeIdentity("
        f"volume_uuid={c13.SYNTHETIC_MERGE_VOLUME!r}, mount_point=Path('/'), "
        "filesystem_type='apfs', device_identifier='disk-synthetic');"
        "from disclosure_drift.m3 import chunk_multipass as cm;"
        f"cm.REAL_MULTIPASS_F0_AUTHORITY = {c13.SYNTHETIC_AUTHORITY!r};"
        "request = cm.SuccessorFinalRequest.from_record(json.loads(Path(sys.argv[1]).read_text()));"
        "out = cm.run_successor_multipass_final(request);"
        "print(json.dumps({'stages': list(out.completed_stage_ids), "
        "'terminal': out.terminal_reached}))"
    )


def spawn_production(
    tmp_path: Path, request: cm.SuccessorFinalRequest, *, label: str, extra: str = ""
) -> dict[str, Any]:
    """Run ``request`` in a FRESH interpreter; return what it printed, or fail loudly."""
    path = tmp_path / f"successor-request-{label}.json"
    path.write_text(json.dumps(dict(request.as_record())), encoding="utf-8")
    program = successor_child_program(tmp_path / "repo")
    if extra:
        program = program.replace(
            "out = cm.run_successor_multipass_final(",
            extra + "out = cm.run_successor_multipass_final(",
        )
    completed = subprocess.run(
        [sys.executable, "-B", "-c", program, str(path)],
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    return {
        "returncode": completed.returncode,
        "stderr": completed.stderr,
        "result": json.loads(completed.stdout.strip().splitlines()[-1])
        if completed.returncode == 0
        else None,
    }


def install_trace(monkeypatch: pytest.MonkeyPatch, statements: list[str]) -> None:
    """Record every SQL statement every successor connection executes, in order."""
    original = cm._establish_successor_connection_state

    def traced(connection: sqlite3.Connection, plan: Any, proof: Any) -> Any:
        connection.set_trace_callback(statements.append)
        return original(connection, plan, proof)

    monkeypatch.setattr(cm, "_establish_successor_connection_state", traced)


# ==========================================================================
# The full run, the graph, the receipts and the oracle
# ==========================================================================
def test_r19_01_the_production_successor_runs_its_exact_graph_and_equals_the_legacy_final(
    tmp_path: Path,
) -> None:
    estate = prepare(tmp_path)
    outcome = cm.run_successor_multipass_final(production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert outcome.completed_stage_ids == PRODUCTION_STAGE_IDS_10
    assert stage_ids(estate.catalog) == list(PRODUCTION_STAGE_IDS_10)
    # Every applied unit recomputes, binds this plan, and chains to its predecessor.
    units = [cm.AppliedUnit.from_row(row) for row in applied_units(estate.catalog)]
    plan_identity = {unit.stage_plan_identity for unit in units}
    assert len(plan_identity) == 1 and outcome.stage_plan_identity in plan_identity
    for index, unit in enumerate(units):
        expected = units[index - 1].unit_identity if index else unit.stage_plan_identity
        assert unit.predecessor_unit_identity == expected
        assert len(unit.connection_state_identity) == 64
        assert len(unit.stage_operation_identity) == 64
    # Thirty-one stage receipts (S23P's record IS the final receipt) and every one recomputes.
    receipts = receipt_files(estate.receipt_root)
    assert len(receipts) == len(PRODUCTION_STAGE_IDS_10) - 1
    for path in receipts:
        record = cm.read_stage_receipt(path)
        assert record["normalized_wal_bytes"] == 0
        assert record["stage_plan_identity"] == outcome.stage_plan_identity
    # The world is the accepted world: same layout, same semantic content, same counters.
    assert sorted(p.name for p in estate.world.iterdir()) == [
        "compact_evidence.sqlite3",
        FINAL_WORLD_RECEIPT_FILENAME,
        "run_progress.sqlite3",
        WORKING_CATALOG_FILENAME,
    ]
    assert estate.legacy is not None
    eq.assert_equivalent(eq.measure(estate.legacy["world_directory"]), eq.measure(estate.world))
    legacy_receipt = estate.legacy["final"].as_record()
    assert counters(legacy_receipt) == counters(outcome.final_receipt)
    for key in ("table_row_counts", "completeness_digest", "member_manifest_digest", "members"):
        assert legacy_receipt[key] == outcome.final_receipt[key], key
    # The six persistent relations live in main, populated, and nothing is left in temp.
    connection = readonly(estate.catalog)
    try:
        names = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM main.sqlite_master WHERE type = 'table'"
            )
        }
        assert set(cm.L2_CONTROL_TABLES) | set(cm.L2_PERSISTENT_RELATIONS) <= names
        assert count(estate.catalog, cm.L2_WITNESS_RANK_TABLE) > 0
        assert count(estate.catalog, cm.L2_PLAN_WITNESS_RANK_TABLE) > 0
        staged = next(u for u in units if u.stage_id == "S12").outcome_witness["rows_staged"]
        assert count(estate.catalog, cm.L2_CORRECTIONS_TABLE) == staged
    finally:
        connection.close()


def test_r19_02_the_stage_plan_is_variable_count_and_its_equality_rules_refuse_early(
    tmp_path: Path,
) -> None:
    estate = prepare(tmp_path, legacy=False, members=18, shards=1)
    assert len(estate.schedule.groups) == 3
    graph = cm.successor_stage_graph(cm.SUCCESSOR_ROUTE_PRODUCTION, 19)
    assert [s.stage_id for s in graph if s.stage_id.startswith("S17")] == [
        "S17A.0", "S17B.0", "S17A.1", "S17B.1", "S17A.2", "S17B.2", "S17C",
    ]  # fmt: skip
    # A predecessor count that disagrees with the descriptor count refuses before any world.
    with pytest.raises(cm.ChunkMultipassError, match="input_group_count"):
        cm.run_successor_multipass_final(
            production_request(estate, predecessor_completed_group_count=2)
        )
    assert not estate.world.exists() and not list(estate.world.parent.glob("*init-attempt*"))
    outcome = cm.run_successor_multipass_final(production_request(estate))
    assert outcome.terminal_reached
    plan = json.loads(
        readonly(estate.catalog)
        .execute(f"SELECT body_json FROM main.{cm.L2_STAGE_PLAN_TABLE}")  # noqa: S608
        .fetchone()[0]
    )
    assert plan["input_group_count"] == 3 == len(plan["intermediates"])
    assert plan["predecessor_completed_group_count"] == 3
    assert plan["counter_source_count"] == 19
    # The calibration graph carries no production terminal and no parser-state stage.
    calibration = cm.successor_stage_graph(cm.SUCCESSOR_ROUTE_CALIBRATION, 19)
    ids = [s.stage_id for s in calibration]
    assert "S15P" not in ids and ids[-2:] == ["S20C", "S21C"]
    with pytest.raises(cm.ChunkMultipassError, match="has no stage graph"):
        cm.successor_stage_graph("legacy", 10)


def test_r19_03_no_production_contract_or_source_names_a_test_only_group_count() -> None:
    for module in (cm, cc, ct, wc):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "five synthetic-test intermediates" not in source, module.__name__
    for name in (
        "L2_STAGE_PLAN_CONTRACT",
        "L2_APPLIED_UNIT_CONTRACT",
        "L2_STAGE_RECEIPT_CONTRACT",
        "L2_CROSS_STORE_BINDING_CONTRACT",
        "L2_DEFERRED_INDEX_SET_CONTRACT",
        "L2_STAGE_ADMISSION_CONTRACT",
        "L2_CONNECTION_STATE_CONTRACT",
    ):
        assert c13i.committed_literal(cm, name) == getattr(cm, name)
        assert str(getattr(cm, name)).startswith("m3.3-chunked-f0-l2-")


# ==========================================================================
# Atomicity, containment, order
# ==========================================================================
def test_r19_04_a_failure_before_commit_leaves_neither_data_nor_applied_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S2"))
    assert count(estate.catalog, "census_parsed_records") == 0
    original = cm._stage_table_load

    def failing(*args: Any, **kwargs: Any) -> Any:
        original(*args, **kwargs)
        message = "injected failure after the writes and before COMMIT"
        raise RuntimeError(message)

    monkeypatch.setattr(cm, "_stage_table_load", failing)
    with pytest.raises(RuntimeError, match="injected failure"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S3"))
    # Rolled back: the table is empty, S3 has no row and no receipt, the WAL holds nothing.
    assert count(estate.catalog, "census_parsed_records") == 0
    assert stage_ids(estate.catalog)[-1] == "S2"
    assert all("S3" not in path.name for path in receipt_files(estate.receipt_root))
    monkeypatch.setattr(cm, "_stage_table_load", original)
    # A failure in the applied-unit insert itself rolls the semantic writes back too: the row
    # and the data are one transaction, never two.
    original_insert = cm._insert_applied_unit

    def failing_insert(connection: sqlite3.Connection, **kwargs: Any) -> Any:
        original_insert(connection, **kwargs)
        message = "injected failure after the applied row and before COMMIT"
        raise RuntimeError(message)

    monkeypatch.setattr(cm, "_insert_applied_unit", failing_insert)
    with pytest.raises(RuntimeError, match="after the applied row"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S3"))
    assert count(estate.catalog, "census_parsed_records") == 0
    assert stage_ids(estate.catalog)[-1] == "S2"
    monkeypatch.setattr(cm, "_insert_applied_unit", original_insert)
    outcome = cm.run_successor_multipass_final(production_request(estate, stop_after="S3"))
    assert outcome.completed_stage_ids[-1] == "S3"
    assert count(estate.catalog, "census_parsed_records") > 0


def test_r19_05_the_applied_row_is_inserted_outside_containment_and_the_allowlist_is_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert E0_PERMITTED_TABLES == ACCEPTED_E0_TABLES
    assert not {name for name in E0_PERMITTED_TABLES if name.startswith("m3_l2_")}
    estate = prepare(tmp_path, legacy=False)
    inside = {"depth": 0}
    original_containment = cm.write_containment
    original_insert = cm._insert_applied_unit

    class _Observed:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self._inner = original_containment(connection)

        def __enter__(self) -> None:
            inside["depth"] += 1
            self._inner.__enter__()

        def __exit__(self, *args: Any) -> None:
            inside["depth"] -= 1
            self._inner.__exit__(*args)

    seen: list[int] = []

    def observed_insert(connection: sqlite3.Connection, **kwargs: Any) -> Any:
        seen.append(inside["depth"])
        return original_insert(connection, **kwargs)

    monkeypatch.setattr(cm, "write_containment", _Observed)
    monkeypatch.setattr(cm, "_insert_applied_unit", observed_insert)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S14"))
    assert seen and set(seen) == {0}
    # And the containment genuinely would deny it: the control table is not an accepted table.
    connection = writer(estate.catalog)
    try:
        with original_containment(connection), pytest.raises(sqlite3.DatabaseError):
            connection.execute(
                f"INSERT INTO main.{cm.L2_CROSS_STORE_BINDINGS_TABLE} VALUES "  # noqa: S608
                "(99, 'k', 'c', 't', NULL, NULL, 'i', '{}', 'x')"
            )
    finally:
        connection.close()


def test_r19_06_every_stage_attaches_before_begin_commits_before_detach_and_checkpoints_main(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    statements: list[str] = []
    install_trace(monkeypatch, statements)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S3"))
    # Isolate S3's session: the last BEGIN IMMEDIATE and what surrounds it.
    begin = max(i for i, s in enumerate(statements) if s == "BEGIN IMMEDIATE")
    attach = [i for i, s in enumerate(statements) if s.startswith("ATTACH DATABASE")]
    detach = [i for i, s in enumerate(statements) if s.startswith("DETACH DATABASE")]
    commit = min(i for i, s in enumerate(statements) if s == "COMMIT" and i > begin)
    checkpoint = [i for i, s in enumerate(statements) if s == wc.MAIN_WAL_CHECKPOINT_TRUNCATE]
    applied = [
        i for i, s in enumerate(statements) if f"INSERT INTO main.{cm.L2_APPLIED_UNITS_TABLE}" in s
    ]
    last_attach = max(i for i in attach if i < begin)
    first_detach = min(i for i in detach if i > commit)
    last_checkpoint = max(i for i in checkpoint if i > commit)
    assert last_attach < begin < max(a for a in applied if a < commit) < commit
    assert commit < first_detach < last_checkpoint
    assert not any(begin < i < commit for i in attach + detach)
    assert all(i < begin or i > first_detach for i in checkpoint)
    # ONE transaction per stage: after S3's ATTACH there is exactly one BEGIN, and the semantic
    # load and the applied row both sit between that BEGIN and its COMMIT.
    begins_after_attach = [
        i for i, s in enumerate(statements) if s == "BEGIN IMMEDIATE" and i > last_attach
    ]
    assert begins_after_attach == [begin]
    loads = [i for i, s in enumerate(statements) if "INTO census_parsed_records" in s]
    assert loads and all(begin < i < commit for i in loads)
    # The checkpoint statement is exactly the main-qualified TRUNCATE, and nothing else.
    assert all(
        "wal_checkpoint" not in s or s == wc.MAIN_WAL_CHECKPOINT_TRUNCATE for s in statements
    )
    assert wc.MAIN_WAL_CHECKPOINT_TRUNCATE == "PRAGMA main.wal_checkpoint(TRUNCATE)"


def test_r19_07_no_stage_attaches_more_than_the_engine_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S1"))
    monkeypatch.setattr(cm, "_MAX_STAGE_ATTACHMENTS", 1)
    with pytest.raises(cm.ChunkMultipassError, match="bounds a stage at 1"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S2"))
    assert stage_ids(estate.catalog)[-1] == "S1"
    assert cm._MAX_STAGE_ATTACHMENTS == 1
    monkeypatch.undo()
    assert cm._MAX_STAGE_ATTACHMENTS == 9


def test_r19_08_the_checkpoint_helper_holds_the_exact_predicate(tmp_path: Path) -> None:
    catalog = tmp_path / "probe.sqlite3"
    connection = sqlite3.connect(catalog, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("CREATE TABLE t (x)")
    connection.execute("BEGIN IMMEDIATE")
    connection.executemany("INSERT INTO t VALUES (?)", [(i,) for i in range(2000)])
    # Inside a transaction: refused before the pragma runs.
    with pytest.raises(wc.WorkingCatalogError, match="only after COMMIT"):
        wc.checkpoint_main_truncate(connection)
    connection.execute("COMMIT")
    wal = catalog.with_name(catalog.name + "-wal")
    assert wal.stat().st_size > 0
    with pytest.raises(wc.WorkingCatalogError, match="nonzero"):
        wc.normalized_wal_bytes(catalog)
    # With an attachment: refused.
    other = tmp_path / "other.sqlite3"
    sqlite3.connect(other).close()
    connection.execute(f"ATTACH DATABASE '{other}' AS o")
    with pytest.raises(wc.WorkingCatalogError, match="still attached"):
        wc.checkpoint_main_truncate(connection)
    connection.execute("DETACH DATABASE o")
    # A concurrent reader blocks the truncate: the busy tuple is a refusal, never progress.
    reader = sqlite3.connect(catalog, isolation_level=None)
    reader.execute("BEGIN")
    reader.execute("SELECT COUNT(*) FROM t").fetchone()
    with pytest.raises(wc.WorkingCatalogError, match=r"\(1, "):
        wc.checkpoint_main_truncate(connection)
    reader.execute("COMMIT")
    reader.close()
    assert wc.checkpoint_main_truncate(connection) == (0, 0, 0)
    assert wal.stat().st_size == 0 and wc.normalized_wal_bytes(catalog) == 0
    assert wc.checkpoint_main_truncate(connection) == (0, 0, 0)
    connection.close()
    assert not wal.exists() and wc.normalized_wal_bytes(catalog) == 0
    wal.symlink_to(other)
    with pytest.raises(wc.WorkingCatalogError, match="symbolic link"):
        wc.normalized_wal_bytes(catalog)


def test_r19_09_a_receipt_is_published_only_after_commit_checkpoint_and_validation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    original = cm._publish_stage_receipt
    observed: list[dict[str, Any]] = []

    def checked(**kwargs: Any) -> Any:
        connection = writer(estate.catalog)
        try:
            rows = connection.execute(
                f"SELECT unit_identity FROM main.{cm.L2_APPLIED_UNITS_TABLE} "  # noqa: S608
                "ORDER BY stage_ordinal"
            ).fetchall()
        finally:
            connection.close()
        observed.append(
            {
                "stage": kwargs["stage"].stage_id,
                "wal": wc.normalized_wal_bytes(estate.catalog),
                "committed": kwargs["unit"].unit_identity == str(rows[-1]["unit_identity"]),
                "main_sha": hashlib.sha256(estate.catalog.read_bytes()).hexdigest(),
                "bound_sha": kwargs["main_state"].sha256,
            }
        )
        return original(**kwargs)

    monkeypatch.setattr(cm, "_publish_stage_receipt", checked)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S4"))
    assert [item["stage"] for item in observed] == ["S0", "S1", "S2", "S3", "S4"]
    for item in observed:
        assert item["wal"] == 0 and item["committed"]
        assert item["main_sha"] == item["bound_sha"]


def test_r19_10_committed_data_without_a_receipt_converges_without_semantic_rerun(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S5"))
    receipt = receipt_files(estate.receipt_root)[-1]
    assert "S5" in receipt.name
    before = cm.read_stage_receipt(receipt)
    rows_before = count(estate.catalog, "census_structural_observations")
    # A TEST-OWNED artifact, standing in for a crash between checkpoint and receipt.
    receipt.unlink()

    def never(*args: Any, **kwargs: Any) -> Any:
        message = "the semantic load ran again for a committed stage"
        raise AssertionError(message)

    monkeypatch.setattr(cm, "_stage_table_load", never)
    outcome = cm.run_successor_multipass_final(production_request(estate, stop_after="S5"))
    assert outcome.completed_stage_ids[-1] == "S5"
    after = cm.read_stage_receipt(receipt)
    assert after["unit_identity"] == before["unit_identity"]
    assert after["main_file_sha256"] == before["main_file_sha256"]
    assert count(estate.catalog, "census_structural_observations") == rows_before


def test_r19_11_a_receipt_without_data_a_gap_a_duplicate_and_a_moved_predecessor_refuse(
    tmp_path: Path,
) -> None:
    estate = prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(production_request(estate, stop_after="S6"))
    connection = writer(estate.catalog)
    try:
        # A duplicate unit is refused by the table itself, inside any transaction.
        row = connection.execute(
            f"SELECT * FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S6'"  # noqa: S608
        ).fetchone()
        columns = row.keys()
        placeholders = ", ".join("?" for _ in columns)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO main.{cm.L2_APPLIED_UNITS_TABLE} ({', '.join(columns)}) "  # noqa: S608
                f"VALUES ({placeholders})",
                tuple(row),
            )
        # A receipt whose applied unit is gone is a receipt that outran its data: conflict.
        connection.execute(
            f"DELETE FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S6'"  # noqa: S608
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="never outruns committed data"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S7"))
    # A gap in the middle: contiguity refuses before anything else.
    connection = writer(estate.catalog)
    try:
        connection.execute(
            f"DELETE FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S3'"  # noqa: S608
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="not contiguous"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S7"))
    # A tampered predecessor identity no longer describes its row: the reader refuses.
    connection = writer(estate.catalog)
    try:
        connection.execute(
            f"UPDATE main.{cm.L2_APPLIED_UNITS_TABLE} SET predecessor_unit_identity = 'x' "  # noqa: S608
            "WHERE stage_id = 'S2'"
        )
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="recomputes to"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S7"))


# ==========================================================================
# Initialization, promotion, idempotence
# ==========================================================================
def test_r19_12_initialization_promotes_one_attempt_fsyncs_the_parent_and_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path)
    fsynced: list[Path] = []
    original = wc._fsync_directory

    def recording(path: Path) -> None:
        fsynced.append(path)
        original(path)

    monkeypatch.setattr(wc, "_fsync_directory", recording)
    renamed: list[tuple[Path, Path]] = []
    original_rename = Path.rename

    def recording_rename(self: Path, target: Any) -> Path:
        renamed.append((self, Path(target)))
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", recording_rename)
    outcome = cm.run_successor_multipass_final(production_request(estate))
    assert outcome.terminal_reached
    assert renamed == [
        (estate.world.parent / f"{estate.world.name}.init-attempt-000", estate.world)
    ]
    attempt_sync = fsynced.index(renamed[0][0])
    parent_sync = max(i for i, path in enumerate(fsynced) if path == estate.world.parent)
    assert attempt_sync < parent_sync
    assert not list(estate.world.parent.glob("*init-attempt*"))
    admissions = sorted(
        p.name for p in estate.receipt_root.iterdir() if p.name.startswith("admission")
    )
    assert admissions == ["admission-attempt-000.json"]
    # Running the completed world again mutates nothing and returns the same outcome.
    snapshot = {p.name: p.read_bytes() for p in estate.world.iterdir()}
    again = cm.run_successor_multipass_final(production_request(estate))
    assert again.completed_stage_ids == outcome.completed_stage_ids and again.terminal_reached
    assert {p.name: p.read_bytes() for p in estate.world.iterdir()} == snapshot


def test_r19_13_an_incomplete_attempt_is_preserved_and_a_complete_one_is_promoted_as_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = prepare(tmp_path, legacy=False)
    # An abandoned incomplete attempt sits beside the absent world: preserved, never accepted.
    stale = estate.world.parent / f"{estate.world.name}.init-attempt-000"
    stale.mkdir(parents=True)
    (stale / "partial.txt").write_bytes(b"interrupted before any catalog existed")
    # A crash between S0's close and the rename: the attempt is complete but not promoted.
    original_promote = cm.promote_world_directory
    calls = {"n": 0}

    def crash_once(attempt: Path, canonical: Path) -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            message = "injected crash before promotion"
            raise RuntimeError(message)
        original_promote(attempt, canonical)

    monkeypatch.setattr(cm, "promote_world_directory", crash_once)
    with pytest.raises(RuntimeError, match="before promotion"):
        cm.run_successor_multipass_final(production_request(estate, stop_after="S0"))
    complete = estate.world.parent / f"{estate.world.name}.init-attempt-001"
    assert complete.is_dir() and not estate.world.exists()
    assert (stale / "partial.txt").read_bytes() == b"interrupted before any catalog existed"

    # The next process promotes the complete attempt WITHOUT re-admitting or re-initializing.
    def never(*args: Any, **kwargs: Any) -> Any:
        message = "admission or initialization ran again over a complete attempt"
        raise AssertionError(message)

    monkeypatch.setattr(cm, "_admit_merge_step", never)
    monkeypatch.setattr(cm, "_initialize_world_attempt", never)
    outcome = cm.run_successor_multipass_final(production_request(estate, stop_after="S0"))
    assert outcome.completed_stage_ids == ("S0",)
    assert estate.world.is_dir() and not complete.exists() and stale.is_dir()
    # A canonical world that carries no StagePlan is never continued.
    foreign = tmp_path / "foreign-world"
    shutil.copytree(estate.world, foreign)
    connection = writer(foreign / WORKING_CATALOG_FILENAME)
    try:
        connection.execute(f"DROP TABLE main.{cm.L2_STAGE_PLAN_TABLE}")
    finally:
        connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="carries no readable successor StagePlan"):
        cm.run_successor_multipass_final(production_request(estate, world_directory=str(foreign)))


def test_r19_14_the_wrappers_are_module_level_and_the_engine_is_private() -> None:
    tree = ast.parse(Path(cm.__file__).read_text(encoding="utf-8"))
    top = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"run_successor_multipass_final", "run_successor_calibration_final"} <= top
    assert "run_successor_multipass_final" in cm.__all__
    assert "run_successor_calibration_final" in cm.__all__
    assert not [name for name in cm.__all__ if "resume" in name.lower()]
    assert not hasattr(cm, "resume_l2")
    assert callable(cm._run_successor_stages) and "_run_successor_stages" not in cm.__all__


def test_r19_07b_the_attachment_bound_is_the_engine_s_own_and_is_nine(tmp_path: Path) -> None:
    assert cm._MAX_STAGE_ATTACHMENTS == 9
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    fakes = tuple(
        type("Fake", (), {"catalog_path": tmp_path / f"absent-{i}.sqlite3"})() for i in range(10)
    )
    context = type("Ctx", (), {"intermediates": fakes, "counter_sources": ()})()
    stage = cm.L2Stage(
        ordinal=2, stage_id="S2", unit_id="census_parser_runs", kind="reduced_parser_run",
        attachments=cm._ATTACH_INTERMEDIATES,
    )  # fmt: skip
    try:
        with pytest.raises(cm.ChunkMultipassError, match="bounds a stage at 9"):
            cm._attach_for_stage(connection, context, stage)  # type: ignore[arg-type]
        attached = [row["name"] for row in connection.execute("PRAGMA database_list")]
        assert attached == ["main"]
    finally:
        connection.close()
