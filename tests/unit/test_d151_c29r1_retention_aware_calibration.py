"""D151-C29R1: the retention-aware calibration multipass -- P1-P9, M1-M16 killing nodes.

What is proved here, over the committed C27R1 synthetic worlds (the exact 34-chunk topology of
the C29 campaign -- 33 primary chunks, one shard chunk, 9 / 9 / 9 / 6 / 1 -- and the 11-chunk
small world), every chunk world retained through the merge or exact-deleted group by group:

* **P1** the C29 retention conflict is real on the whole-plan resolver -- a missing chunk refuses
  the whole plan -- and the group-local resolver admits exactly a contiguous run (M1, M2);
* **P2** a calibration level-1 group merges with only ITS chunks present, in this process and in
  a real calibration child, inspects no other chunk's placement, and refuses a missing, wrong,
  foreign or other-plan member before any attempt directory exists (M1, M2);
* **P3** the retained witness is written only after the chunk's terminal authenticated, is the
  exact two-table projection plus the byte-identical declarations copy, seals every field, and
  refuses missing, extra, duplicate, wrong-run, wrong-plan, wrong-schedule, wrong-chunk,
  wrong-interval, wrong-receipt, stale and resealed forms (M3, M4, M6, M7, M8);
* **P4** a chunk world is deleted only under an explicit grant that is the first gate, after the
  checkpoint binds chunk receipt + witness + intermediate, after every witness and the
  intermediate are re-read durable, through the accepted exact-entry primitive and never a tree
  removal; an unexpected entry or a non-suffix partial refuses; a sorted-suffix partial resumes
  (M9, M10, M11, M12);
* **P5 / P6** the calibration final consumes five intermediates + one witness per planned
  chunk + five checkpoints, opens no chunk world, and reproduces the retain-everything result --
  and the COMMITTED pre-C29R1 route's values, recorded in the C29R1 ledger from the same worlds
  -- semantic for semantic, counter for counter (M5, M13, M14);
* **P7** every production body, launcher, bootstrap and authority gate is unchanged and none can
  consume a retained witness (M15, M16);
* **P8** the exact 34-chunk lifecycle executes group by group under deletion with at most one
  group's bulky worlds present, survives a restart between groups without re-parsing a deleted
  group, and its final child charges level two with the level-two peak ratio (C28-MINOR-4, for
  the calibration final);
* **P9** every closed value stays closed and no new module joined the chunk family.

Every calibration child in this module runs with the COMMITTED production authority (``None``).
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import shutil
import sqlite3
import sys
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c13_multipass_semantics as sem  # noqa: E402
import test_d151_c27r1_dependency_closed_subset as c27  # noqa: E402
from test_d151_c27r1_dependency_closed_subset import _calibration_seams  # noqa: E402, F401

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import chunk_transfer as ctr  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_DECLARATIONS_FILENAME,
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    CHUNK_WITNESS_FILENAME,
    ChunkEvidenceError,
    ChunkReceipt,
    file_sha256,
    read_receipt_document,
    write_once_json,
)
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402

RUN = "c27r1"
MISSING = "has no verified copy on either tier"
WITNESS_CONTRACT = "m3.3-chunked-f0-calibration-chunk-retained-witness/1"

#: The COMMITTED (93e5229a, pre-C29R1) calibration final route's semantic observations over the
#: C27R1 topology world -- every chunk world retained, in-process bodies -- recorded twice in
#: the C29R1 ledger (`path_a/run1/topology.json`, identical to `run2`). Path A of packet §8.
TOPOLOGY_COMMITTED: Mapping[str, object] = {
    "chunk_count": 34,
    "intermediate_count": 5,
    "selected_members": 38,
    "full_total_members": 40,
    "members": 38,
    "records": 125,
    "parsed_records": 125,
    "quarantined_records": 0,
    "omitted_field_observations": 472,
    "materialized_field_observations": 50,
    "completeness_digest": "2dd29b2450b14febe8e9a647d873f946e40da0b5a8d203bb78c0b5dec9a61d16",
    "member_manifest_digest": "6d615c4efc61b0f6a0e462f875fd0dedcc3afe2dbd0e9873ea1f09b8fde3112e",
    "first_witness_accessions_corrected": 1,
    "first_witness_rows_staged": 55,
    "evidence_members_corrected": 10,
    "evidence_delta": 50,
    # ``_stable_id("parser-run", "obs-bulk-1", "submissions-json", "submissions-json/1.3")``:
    # Decision 151 R3 moved the parser version and the accepted preimage carries it, so this
    # identity moved with it (it was ``de12930b…`` under 1.2). Every other committed value is
    # unchanged, which is what proves the move is the version string and nothing else.
    "parser_run_id": "a89638030cbd9afee06234df3ba01ec6a94dd1119f3468a14bedb596f6d4656d",
    "run_outcome": "completed",
    "world_parser_state": "not_started",
    "parser_state_after": "chunk_local",
    "status": "complete",
    "table_row_counts": {
        "census_accession_observations": 55,
        "census_accessions": 82,
        "census_candidate_lineage_edges": 528,
        "census_historical_references": 5,
        "census_malformed_historical_references": 0,
        "census_parsed_records": 125,
        "census_parser_runs": 1,
        "census_quarantined_records": 0,
        "census_registrant_observations": 231,
        "census_registrants": 33,
        "census_structural_observations": 66,
    },
}
#: The same, over the 11-chunk small world (`path_a/run1/small.json`).
SMALL_COMMITTED: Mapping[str, object] = {
    "chunk_count": 11,
    "intermediate_count": 3,
    "selected_members": 12,
    "full_total_members": 15,
    "members": 12,
    "records": 40,
    "parsed_records": 40,
    "quarantined_records": 0,
    "omitted_field_observations": 153,
    "materialized_field_observations": 15,
    "completeness_digest": "058348841bf0eb1ac5459c152ca2957ab892b45d00350fd3f9dea44a1becacf0",
    "member_manifest_digest": "928b81e7851c4befd64d987d883c1b3f0b0a63f996d6df0f7164558b8619be15",
    "first_witness_accessions_corrected": 1,
    "first_witness_rows_staged": 20,
    "evidence_members_corrected": 3,
    "evidence_delta": 15,
    # ``_stable_id("parser-run", "obs-bulk-1", "submissions-json", "submissions-json/1.3")``:
    # Decision 151 R3 moved the parser version and the accepted preimage carries it, so this
    # identity moved with it (it was ``de12930b…`` under 1.2). Every other committed value is
    # unchanged, which is what proves the move is the version string and nothing else.
    "parser_run_id": "a89638030cbd9afee06234df3ba01ec6a94dd1119f3468a14bedb596f6d4656d",
    "run_outcome": "completed",
    "world_parser_state": "not_started",
    "parser_state_after": "chunk_local",
    "status": "complete",
    "table_row_counts": {
        "census_accession_observations": 20,
        "census_accessions": 27,
        "census_candidate_lineage_edges": 45,
        "census_historical_references": 2,
        "census_malformed_historical_references": 0,
        "census_parsed_records": 40,
        "census_parser_runs": 1,
        "census_quarantined_records": 0,
        "census_registrant_observations": 70,
        "census_registrants": 10,
        "census_structural_observations": 20,
    },
}
#: The committed level-1 counters of the topology world: their sums (4, 55, 7, 35) are NOT the
#: whole-F0 counters (1, 55, 10, 50), so the equality proofs below can tell the two apart.
TOPOLOGY_LEVEL_ONE = ((1, 15, 2, 10), (1, 15, 2, 10), (1, 15, 2, 10), (1, 10, 1, 5), (0, 0, 0, 0))
COUNTERS = (
    "first_witness_accessions_corrected",
    "first_witness_rows_staged",
    "evidence_members_corrected",
    "evidence_delta",
)
#: The witness fields a tampering test can move (everything but the identity).
WITNESS_FIELDS = tuple(sorted(cm._WITNESS_KEYS - {"witness_identity"}))
#: Level-distinct terms whose PEAK RATIOS also differ -- C28-MINOR-4: the C24-R2 fixture tells
#: the two transients apart but not the two ratios, so a final charged with the level-one ratio
#: was invisible to it. Test-only; the production terms stay ``None``.
DISTINCT_RATIO_REQUIREMENTS = ct.MultipassStorageRequirements(
    internal_reserve_bytes=0,
    level_one_peak_ratio=1.0,
    level_two_peak_ratio=1.5,
    level_one_transient_bytes=c13.LEVEL_ONE_TRANSIENT_SENTINEL,
    level_two_transient_bytes=c13.LEVEL_TWO_TRANSIENT_SENTINEL,
)


# ==========================================================================
# Drivers
# ==========================================================================
def topology_run(root: Path) -> tuple[Path, Any, dict[str, Any], dict[str, Any]]:
    database, tree = c27.topology_world(root)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    run = c27.execute_chunks_in_process(plan, root / "run", database, tree)
    partial = c27.prepared_multipass(run)
    return database, tree, run, partial


def small_run(root: Path) -> tuple[Path, Any, dict[str, Any], dict[str, Any]]:
    database, tree = c27.small_world(root)
    plan = c27.subset_plan(tree, database, prefix=10)
    run = c27.execute_chunks_in_process(plan, root / "run", database, tree)
    partial = c27.prepared_multipass(run)
    return database, tree, run, partial


def execute_chunk_subset(
    plan: cp.CalibrationSubsetPlan, base: Path, database: Path, tree: Any, chunk_ids: Iterable[str]
) -> dict[str, Any]:
    """The C27R1 in-process chunk driver restricted to the named PRIMARY chunks."""
    wanted = set(chunk_ids)
    plan_path = c27.plan_on_disk(plan, base)
    chunk_root = base / "chunks"
    receipts = []
    for bounds in plan.chunks:
        if bounds.chunk_id not in wanted:
            continue
        assert bounds.region == cp.REGION_PRIMARY
        attempt_directory, attempt = ce.next_attempt_directory(chunk_root, bounds.chunk_id)
        request = c1x.chunk_request(
            plan_path=plan_path,
            chunk_id=bounds.chunk_id,
            attempt=attempt,
            attempt_directory=attempt_directory,
            database=database,
            tree=tree,
            parent_map_path=None,
            batch_size=c13.BATCH,
            repository=c1.PINNED,
        )
        request_path = base / f"{bounds.chunk_id}-{attempt:03d}-request.json"
        write_once_json(request_path, dict(request.as_record()))
        envelope = c27.issued(
            plan=plan,
            role=ce.CALIBRATION_ROLE_CHUNK,
            step_id=bounds.chunk_id,
            request_path=request_path,
        )
        receipts.append(ce.execute_calibration_subset_chunk_body(request, envelope))
    return {
        "base": base,
        "plan": plan,
        "plan_path": plan_path,
        "chunk_root": chunk_root,
        "receipts": receipts,
        "parent_map_path": None,
    }


def retained_of(partial: dict[str, Any]) -> Path:
    root = cm.calibration_retained_root(partial["intermediates_root"])
    root.mkdir(exist_ok=True)
    return root


def world_of(run: dict[str, Any], chunk_id: str, attempt: int = 0) -> Path:
    return run["chunk_root"] / chunk_id / f"attempt-{attempt:03d}"


def witness_of(partial: dict[str, Any], chunk_id: str, attempt: int = 0) -> Path:
    return cm.calibration_witness_attempt_directory(retained_of(partial), chunk_id, attempt)


def write_witness(
    run: dict[str, Any], partial: dict[str, Any], chunk_id: str, run_id: str = RUN
) -> tuple[cm.CalibrationChunkWitness, Path]:
    return cm.write_calibration_chunk_witness(
        run["plan"],
        partial["schedule"],
        chunk_id=chunk_id,
        run_id=run_id,
        chunk_root=run["chunk_root"],
        retained_root=retained_of(partial),
    )


def group_launch(
    run: dict[str, Any], partial: dict[str, Any], group: cm.MergeGroup, database: Path
) -> tuple[cm.GroupMergeRequest, Path, ce.CalibrationChildEnvelope, Path]:
    _directory, attempt = cm.next_intermediate_attempt_directory(
        partial["intermediates_root"], group.group_id
    )
    request, directory = c27.group_request(run, partial, group, database, attempt)
    request_path = partial["multipass_root"] / f"{group.group_id}-{attempt:03d}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = c27.issued(
        plan=run["plan"],
        role=ce.CALIBRATION_ROLE_GROUP,
        step_id=group.group_id,
        request_path=request_path,
        ledger=partial["ledger"],
    )
    return request, request_path, envelope, directory


def merge_group(
    run: dict[str, Any], partial: dict[str, Any], group: cm.MergeGroup, database: Path
) -> cm.IntermediateReceipt:
    request, _path, envelope, _directory = group_launch(run, partial, group, database)
    return cm.merge_calibration_subset_group_body(request, envelope)


def write_checkpoint(
    run: dict[str, Any], partial: dict[str, Any], group_id: str, run_id: str = RUN
) -> cm.CalibrationGroupCheckpoint:
    return cm.write_calibration_group_checkpoint(
        run["plan"],
        partial["schedule"],
        group_id=group_id,
        run_id=run_id,
        chunk_root=run["chunk_root"],
        retained_root=retained_of(partial),
        intermediates_root=partial["intermediates_root"],
    )


def grant_for(
    partial: dict[str, Any], plan: cp.CalibrationSubsetPlan, *group_ids: str, run_id: str = RUN
) -> cm.CalibrationDeletionGrant:
    schedule = partial["schedule"]
    return cm.CalibrationDeletionGrant(
        run_id=run_id,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_ids=group_ids or tuple(g.group_id for g in schedule.groups),
    )


def delete_group(
    run: dict[str, Any],
    partial: dict[str, Any],
    group_id: str,
    grant: object,
    run_id: str = RUN,
) -> cm.CalibrationGroupDeletion:
    return cm.delete_calibration_group_chunk_worlds(
        grant,
        plan=run["plan"],
        schedule=partial["schedule"],
        group_id=group_id,
        run_id=run_id,
        chunk_root=run["chunk_root"],
        retained_root=retained_of(partial),
        intermediates_root=partial["intermediates_root"],
    )


def lifecycle(
    run: dict[str, Any],
    partial: dict[str, Any],
    database: Path,
    *,
    delete: bool,
    run_id: str = RUN,
) -> dict[str, Any]:
    """Witness, merge, checkpoint and (optionally) exact-delete every group, in THIS process."""
    plan = run["plan"]
    grant = grant_for(partial, plan, run_id=run_id) if delete else None
    out: dict[str, Any] = {"receipts": [], "checkpoints": [], "deletions": [], "witnesses": []}
    for group in partial["schedule"].groups:
        for chunk_id in group.chunk_ids:
            out["witnesses"].append(write_witness(run, partial, chunk_id, run_id)[0])
        out["receipts"].append(merge_group(run, partial, group, database))
        out["checkpoints"].append(write_checkpoint(run, partial, group.group_id, run_id))
        if grant is not None:
            out["deletions"].append(delete_group(run, partial, group.group_id, grant, run_id))
    return out


def final_in_process(
    run: dict[str, Any],
    partial: dict[str, Any],
    database: Path,
    *,
    label: str,
    run_id: str = RUN,
) -> cm.CalibrationSubsetResult:
    """The calibration final body in THIS process, under a fresh request document per call."""
    request = c13.final_request(
        run,
        schedule_path=partial["schedule_path"],
        intermediates_root=partial["intermediates_root"],
        world_directory=partial["world_directory"],
        database=database,
        run_id=run_id,
        requirements=c13.LEVEL_DISTINCT_REQUIREMENTS,
    )
    request_path = partial["multipass_root"] / f"final-{label}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = c27.issued(
        plan=run["plan"],
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="final",
        request_path=request_path,
        run_id=run_id,
        ledger=partial["ledger"],
    )
    return cm.finalize_calibration_subset_body(request, envelope)


def semantic(result: cm.CalibrationSubsetResult) -> dict[str, object]:
    record = dict(result.as_record())
    return {key: record[key] for key in TOPOLOGY_COMMITTED}


def counters(result: Any) -> tuple[int, int, int, int]:
    return tuple(getattr(result, name) for name in COUNTERS)  # type: ignore[return-value]


def snapshot(root: Path) -> dict[str, tuple[str, int]]:
    """Every regular file beneath ``root`` with its digest -- to prove nothing was touched."""
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def reseal_witness(directory: Path, **changes: Any) -> cm.CalibrationChunkWitness:
    """Tamper a witness record and recompute its identity, so only a binding can catch it."""
    path = directory / cm.CALIBRATION_RETAINED_WITNESS_FILENAME
    record = json.loads(path.read_bytes())
    record.update(changes)
    record["witness_identity"] = cm._record_identity(record, "witness_identity")
    path.write_bytes(cp.canonical_json_bytes(record))
    return cm.CalibrationChunkWitness.from_record(record)


def edit_json(path: Path, mutate: Callable[[dict[str, Any]], None]) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


def first_call(name: str) -> str:
    tree = ast.parse(Path(cm.__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    body = functions[name].body
    first = body[1] if isinstance(body[0], ast.Expr) else body[0]
    value = first.value if isinstance(first, ast.Expr | ast.Assign) else None
    assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name), name
    return value.func.id


# ==========================================================================
# P1: the C29 conflict on the whole-plan resolver; the group-local resolver -- M1, M2
# ==========================================================================
def test_p1_m1_m2_the_whole_plan_resolver_refuses_a_missing_chunk_and_group_local_admits(
    tmp_path: Path,
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    g0 = schedule.groups[0]
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, g0.chunk_ids)
    assert len(run["receipts"]) == 9
    # The C29 conflict, reproduced on the resolver the committed calibration bodies used.
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0009' {MISSING}"):
        cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    # The group-local resolver admits exactly the group, in plan order, with plan ordinals.
    inputs = cc.resolve_contiguous_chunk_inputs(plan, g0.chunk_ids, internal_root=run["chunk_root"])
    assert [item.chunk_id for item in inputs] == list(g0.chunk_ids)
    assert [item.ordinal for item in inputs] == list(g0.plan_ordinals)
    assert cm.select_group_inputs(inputs, g0) == inputs
    (one,) = cc.resolve_contiguous_chunk_inputs(
        plan, ("chunk-0004",), internal_root=run["chunk_root"]
    )
    assert one.ordinal == 4 and one.start == 4 and one.end == 5
    for bad, problem in (
        ((), "at least one chunk"),
        (("chunk-0001", "chunk-0001"), "at least one chunk exactly once"),
        (("chunk-0001", "chunk-9999"), "does not carry"),
        (("chunk-0001", "chunk-0003"), "not one contiguous run"),
        (("chunk-0002", "chunk-0001"), "not one contiguous run"),
    ):
        with pytest.raises(cc.ChunkConsolidationError, match=problem):
            cc.resolve_contiguous_chunk_inputs(plan, bad, internal_root=run["chunk_root"])
    # A member of the run that is absent refuses; a foreign directory refuses the run too.
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0009' {MISSING}"):
        cc.resolve_contiguous_chunk_inputs(
            plan, ("chunk-0008", "chunk-0009"), internal_root=run["chunk_root"]
        )
    (run["chunk_root"] / "chunk-9999").mkdir()
    with pytest.raises(cc.ChunkConsolidationError, match="does not name"):
        cc.resolve_contiguous_chunk_inputs(plan, g0.chunk_ids, internal_root=run["chunk_root"])


# ==========================================================================
# P2: group-local calibration input resolution -- M1, M2
# ==========================================================================
def test_p2_m1_a_group_merges_with_only_its_own_chunks_present_and_inspects_no_other(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    g0 = schedule.groups[0]
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, g0.chunk_ids)
    partial = c27.prepared_multipass(run)
    placements: list[str] = []
    original = cc.derive_chunk_placement

    def recording(plan_: Any, chunk_id: str, **kwargs: Any) -> Any:
        placements.append(chunk_id)
        return original(plan_, chunk_id, **kwargs)

    monkeypatch.setattr(cc, "derive_chunk_placement", recording)
    request, _path, envelope, directory = group_launch(run, partial, g0, database)
    receipt = cm.merge_calibration_subset_group_body(request, envelope)
    assert receipt.group_id == "group-0000" and receipt.input_chunk_ids == g0.chunk_ids
    assert receipt.status == "complete" and directory.is_dir()
    assert sorted(set(placements)) == list(g0.chunk_ids), placements
    assert not any(chunk_id in placements for chunk_id in schedule.groups[1].chunk_ids)
    monkeypatch.undo()
    # The REAL calibration child, on a second multipass root, merges the same group.
    other = c27.prepared_multipass(run, label="child")
    request, request_path, envelope, directory = group_launch(run, other, g0, database)
    completed = c27.spawn_calibration_child(request_path, envelope)
    assert completed.returncode == 0, completed.stderr[-3000:]
    child = cm.completed_intermediate_receipt(other["intermediates_root"], "group-0000")
    assert child is not None and child[0].pid != os.getpid()
    assert child[0].input_chunk_ids == g0.chunk_ids
    assert child[0].table_row_counts == receipt.table_row_counts
    assert child[0].witness_ledger_identity == receipt.witness_ledger_identity


def test_p2_m2_a_group_with_one_member_missing_refuses_before_any_attempt_directory(
    tmp_path: Path,
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    g0 = schedule.groups[0]
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, g0.chunk_ids)
    shutil.rmtree(run["chunk_root"] / "chunk-0004")
    partial = c27.prepared_multipass(run)
    request, request_path, envelope, directory = group_launch(run, partial, g0, database)
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0004' {MISSING}"):
        cm.merge_calibration_subset_group_body(request, envelope)
    assert not directory.exists() and sorted(p.name for p in partial["ledger"].iterdir()) == []
    fresh = c27.issued(
        plan=plan,
        role=ce.CALIBRATION_ROLE_GROUP,
        step_id=g0.group_id,
        request_path=request_path,
        ledger=partial["ledger"],
    )
    completed = c27.spawn_calibration_child(request_path, fresh)
    assert completed.returncode != 0 and f"chunk 'chunk-0004' {MISSING}" in completed.stderr
    assert not directory.exists() and sorted(p.name for p in partial["ledger"].iterdir()) == []


def test_p2_a_wrong_chunk_a_foreign_directory_and_another_plans_receipt_refuse(
    tmp_path: Path,
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    g0 = schedule.groups[0]
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, g0.chunk_ids)
    partial = c27.prepared_multipass(run)
    # Wrong chunk: chunk-0003's world sitting in chunk-0004's slot is no chunk-0004.
    held = tmp_path / "held"
    shutil.move(str(run["chunk_root"] / "chunk-0004"), str(held))
    shutil.copytree(run["chunk_root"] / "chunk-0003", run["chunk_root"] / "chunk-0004")
    request, _path, envelope, directory = group_launch(run, partial, g0, database)
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0004' {MISSING}"):
        cm.merge_calibration_subset_group_body(request, envelope)
    assert not directory.exists()
    shutil.rmtree(run["chunk_root"] / "chunk-0004")
    shutil.move(str(held), str(run["chunk_root"] / "chunk-0004"))
    # A receipt under another plan: every byte of the chunk's data is unchanged.
    edit_json(
        world_of(run, "chunk-0002") / CHUNK_RECEIPT_FILENAME,
        lambda d: d.__setitem__("plan_digest", "ab" * 32),
    )
    with pytest.raises(cc.ChunkConsolidationError, match="plan digest"):
        cm.merge_calibration_subset_group_body(request, envelope)
    assert not directory.exists()
    edit_json(
        world_of(run, "chunk-0002") / CHUNK_RECEIPT_FILENAME,
        lambda d: d.__setitem__("plan_digest", plan.plan_digest),
    )
    # A foreign chunk directory anywhere under the root refuses the group.
    (run["chunk_root"] / "chunk-9999").mkdir()
    with pytest.raises(cc.ChunkConsolidationError, match="does not name"):
        cm.merge_calibration_subset_group_body(request, envelope)
    assert not directory.exists()
    (run["chunk_root"] / "chunk-9999").rmdir()
    receipt = cm.merge_calibration_subset_group_body(request, envelope)
    assert receipt.input_chunk_ids == g0.chunk_ids


def test_p2_a_later_group_merges_after_an_earlier_group_was_exact_deleted(tmp_path: Path) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    plan = run["plan"]
    g0, g1 = partial["schedule"].groups[0], partial["schedule"].groups[1]
    for chunk_id in g0.chunk_ids:
        write_witness(run, partial, chunk_id)
    merge_group(run, partial, g0, database)
    write_checkpoint(run, partial, g0.group_id)
    delete_group(run, partial, g0.group_id, grant_for(partial, plan, g0.group_id))
    for chunk_id in g0.chunk_ids:
        assert not world_of(run, chunk_id).exists()
    receipt = merge_group(run, partial, g1, database)
    assert receipt.group_id == "group-0001" and receipt.input_chunk_ids == g1.chunk_ids


# ==========================================================================
# P3: the retained witness -- M3, M4, M6, M7, M8
# ==========================================================================
def test_p3_m3_a_witness_is_written_only_after_the_terminal_and_is_the_exact_projection(
    tmp_path: Path,
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    g0 = schedule.groups[0]
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, g0.chunk_ids)
    partial = c27.prepared_multipass(run)
    retained = retained_of(partial)
    # Before the terminal: no receipt, no witness -- and nothing under the retained root.
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0009' {MISSING}"):
        write_witness(run, partial, "chunk-0009")
    assert list(retained.iterdir()) == []
    # A terminal whose artifacts moved is not a terminal.
    evidence = world_of(run, "chunk-0001") / "compact_evidence.sqlite3"
    original = evidence.read_bytes()
    evidence.write_bytes(original + b"\x00")
    with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0001' {MISSING}"):
        write_witness(run, partial, "chunk-0001")
    assert list(retained.iterdir()) == []
    evidence.write_bytes(original)
    # The exact projection, sealed, deep re-read, bound to the receipt found beside the chunk.
    witness, directory = write_witness(run, partial, "chunk-0000")
    world = world_of(run, "chunk-0000")
    receipt_sha256, _ = file_sha256(world / CHUNK_RECEIPT_FILENAME)
    receipt = ChunkReceipt.from_record(
        read_receipt_document(world / CHUNK_RECEIPT_FILENAME, contract=CHUNK_RECEIPT_CONTRACT)
    )
    assert witness.chunk_receipt_sha256 == receipt_sha256
    assert witness.chunk_manifest_digest == receipt.manifest.digest
    assert witness.chunk_manifest_total_bytes == receipt.manifest.total_bytes
    assert witness.chunk_execution_identity == receipt.execution_identity
    assert (witness.chunk_ordinal, witness.region, witness.start, witness.end) == (
        0,
        "primary",
        0,
        1,
    )
    assert witness.contract == WITNESS_CONTRACT and witness.classifications == c27.LABELS
    assert witness.run_id == RUN and witness.plan_digest == plan.plan_digest
    assert witness.merge_schedule_digest == schedule.schedule_digest
    assert witness.witness_identity == witness.identity()
    assert sorted(p.name for p in directory.iterdir()) == [
        CHUNK_DECLARATIONS_FILENAME,
        cm.CALIBRATION_RETAINED_WITNESS_FILENAME,
        cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME,
    ]
    assert (directory / CHUNK_DECLARATIONS_FILENAME).read_bytes() == (
        world / CHUNK_DECLARATIONS_FILENAME
    ).read_bytes()
    catalog = sqlite3.connect(f"file:{world / WORKING_CATALOG_FILENAME}?immutable=1", uri=True)
    ledger = sqlite3.connect(f"file:{world / CHUNK_WITNESS_FILENAME}?immutable=1", uri=True)
    payload = sqlite3.connect(
        f"file:{directory / cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME}?immutable=1", uri=True
    )
    try:
        accessions = "SELECT accession_plain, parsed_record_id FROM census_accessions ORDER BY 1"
        assert payload.execute(accessions).fetchall() == catalog.execute(accessions).fetchall()
        rows = (
            "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
            "FROM chunk_first_witness ORDER BY 1"
        )
        assert payload.execute(rows).fetchall() == ledger.execute(rows).fetchall()
        assert witness.accession_rows == len(payload.execute(accessions).fetchall()) > 0
        assert witness.ledger_rows == len(payload.execute(rows).fetchall()) > 0
        assert sorted(
            name for (name,) in payload.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ) == ["census_accessions", "chunk_first_witness", "retained_witness_meta"]
        assert dict(payload.execute("SELECT key, value FROM retained_witness_meta")) == dict(
            witness.meta_rows()
        )
    finally:
        payload.close()
        ledger.close()
        catalog.close()
    assert cm.read_calibration_chunk_witness(directory, deep=True) == witness
    found = cm.completed_calibration_chunk_witness(retained, "chunk-0000")
    assert found is not None and found[0] == witness and found[1] == directory
    # Create-once: never rewritten, never a second attempt beside a valid one.
    with pytest.raises(cm.ChunkMultipassError, match="create-once"):
        write_witness(run, partial, "chunk-0000")
    with pytest.raises(cm.ChunkMultipassError, match="create-once"):
        cm.next_calibration_witness_attempt_directory(retained, "chunk-0000")
    # It is not a chunk receipt, not an intermediate receipt, and not a chunk world.
    record_path = directory / cm.CALIBRATION_RETAINED_WITNESS_FILENAME
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(record_path, contract=CHUNK_RECEIPT_CONTRACT)
    with pytest.raises(ChunkEvidenceError):
        ChunkReceipt.from_record(dict(witness.as_record()))
    with pytest.raises(cm.ChunkMultipassError):
        cm.IntermediateReceipt.from_record(dict(witness.as_record()))
    assert ce.completed_chunk_receipt(retained, "chunk-0000") is None
    assert cs.derive_chunk_placement(plan, "chunk-0000", internal_root=retained).state == (
        cs.STATE_RUNNING_INTERNAL
    )


def test_p3_the_shard_chunk_witness_carries_no_declarations_and_the_parent_map_survives_deletion(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    plan = run["plan"]
    witness, directory = write_witness(run, partial, "chunk-0033")
    assert witness.region == cp.REGION_SHARD and witness.declarations_sha256 is None
    assert witness.declarations_byte_length is None
    assert sorted(p.name for p in directory.iterdir()) == [
        cm.CALIBRATION_RETAINED_WITNESS_FILENAME,
        cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME,
    ]
    # The merged parent map from every primary witness's retained copy equals the one the C27R1
    # driver merged from the live worlds -- so the shard chunk still binds its parents after
    # every primary world is gone.
    live = json.loads(Path(run["parent_map_path"]).read_bytes())
    contributions = []
    for bounds in plan.chunks:
        if bounds.region != cp.REGION_PRIMARY:
            continue
        _w, primary_directory = write_witness(run, partial, bounds.chunk_id)
        contributions.append(ce.read_declarations(primary_directory / CHUNK_DECLARATIONS_FILENAME))
    merged = ce.merge_parent_map(contributions)
    assert {name: sorted(parents) for name, parents in merged.items()} == live
    assert len(live) == 5


@pytest.mark.parametrize("field", WITNESS_FIELDS)
def test_p3_m4_every_witness_field_is_inside_the_seal(tmp_path: Path, field: str) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    run = execute_chunk_subset(plan, tmp_path / "run", database, tree, ("chunk-0000",))
    partial = c27.prepared_multipass(run)
    witness, directory = write_witness(run, partial, "chunk-0000")
    record = dict(witness.as_record())
    value = record[field]
    if isinstance(value, bool) or value is None:
        moved: object = not value if isinstance(value, bool) else 0
    elif isinstance(value, int):
        moved = value + 1
    elif isinstance(value, list):
        moved = [*value, "extra"]
    elif isinstance(value, str) and len(value) == 64:
        moved = ("0" if value[0] != "0" else "1") + value[1:]
    else:
        moved = f"{value}x"
    tampered = {**record, field: moved}
    with pytest.raises(cm.ChunkMultipassError):
        cm.CalibrationChunkWitness.from_record(tampered)
    path = directory / cm.CALIBRATION_RETAINED_WITNESS_FILENAME
    path.write_bytes(cp.canonical_json_bytes(tampered))
    with pytest.raises(cm.ChunkMultipassError):
        cm.read_calibration_chunk_witness(directory)
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        cm.completed_calibration_chunk_witness(retained_of(partial), "chunk-0000")


def test_p3_m4_a_resealed_witness_is_a_different_witness_and_refuses_downstream(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    plan = run["plan"]
    schedule = partial["schedule"]
    retained = retained_of(partial)
    g0 = schedule.groups[0]
    witnesses = {cid: write_witness(run, partial, cid)[0] for cid in g0.chunk_ids}
    merge_group(run, partial, g0, database)
    checkpoint = write_checkpoint(run, partial, g0.group_id)
    directory = witness_of(partial, "chunk-0003")
    original = (directory / cm.CALIBRATION_RETAINED_WITNESS_FILENAME).read_bytes()
    bound = next(item for item in checkpoint.chunks if item.chunk_id == "chunk-0003")

    def restore() -> None:
        (directory / cm.CALIBRATION_RETAINED_WITNESS_FILENAME).write_bytes(original)

    # A resealed content identity: the record verifies shallow, the deep re-read refuses, and
    # the checkpoint no longer binds it.
    resealed = reseal_witness(directory, semantic_payload_identity="f" * 64)
    assert resealed.witness_identity != bound.witness_identity
    assert (
        cm.read_calibration_chunk_witness(directory).witness_identity == resealed.witness_identity
    )
    with pytest.raises(cm.ChunkMultipassError, match="stale or resealed"):
        cm.read_calibration_chunk_witness(directory, deep=True)
    with pytest.raises(cm.ChunkMultipassError, match="resealed or substituted"):
        cm._require_checkpoint_binds_witnesses(checkpoint, {**witnesses, "chunk-0003": resealed})
    restore()
    # A resealed run, plan, schedule, chunk, ordinal, interval or receipt refuses at the binding
    # that owns it -- never silently admitted.
    for changes, problem in (
        ({"run_id": "other"}, "another run"),
        ({"plan_digest": "ab" * 32}, "another run"),
        ({"merge_schedule_digest": "cd" * 32}, "another run"),
        ({"chunk_ordinal": 4}, "records ordinal"),
        ({"start": 2, "end": 3}, "records ordinal"),
        ({"member_order_digest": "ef" * 32}, "names a source"),
        ({"selected_member_order_digest": "ef" * 32}, "names a source"),
    ):
        resealed = reseal_witness(directory, **changes)
        with pytest.raises(cm.ChunkMultipassError, match=problem):
            cm._require_witness_binds_plan(
                resealed, plan=plan, schedule=schedule, run_id=RUN, ordinal=3, bounds=plan.chunks[3]
            )
        restore()
    # A primary witness relabelled as a shard chunk is not even readable: the declarations
    # copy it carries contradicts the kind it now claims.
    with pytest.raises(cm.ChunkMultipassError, match="declarations copy exactly when"):
        reseal_witness(directory, region="shard")
    restore()
    # A resealed chunk id contradicts the payload's own meta table before any plan binding.
    resealed = reseal_witness(directory, chunk_id="chunk-0004")
    with pytest.raises(cm.ChunkMultipassError, match="payload describes"):
        cm.completed_calibration_chunk_witness(retained, "chunk-0003")
    restore()
    resealed = reseal_witness(directory, chunk_receipt_sha256="9" * 64)
    receipt = cm.completed_intermediate_receipt(partial["intermediates_root"], g0.group_id)
    assert receipt is not None
    with pytest.raises(cm.ChunkMultipassError, match="resealed or substituted"):
        cm._require_checkpoint_binds_witnesses(checkpoint, {**witnesses, "chunk-0003": resealed})
    with pytest.raises(cm.ChunkMultipassError, match="never admitted beside a chunk other"):
        cm._require_witness_matches_chunk(resealed, run["receipts"][3], world_of(run, "chunk-0003"))
    restore()
    assert cm.completed_calibration_chunk_witness(retained, "chunk-0003") is not None


def test_p3_m6_m7_m8_missing_extra_duplicate_wrong_run_and_stale_witnesses_refuse_the_final(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    lifecycle(run, partial, database, delete=False)
    retained = retained_of(partial)
    world = partial["world_directory"]
    directory = witness_of(partial, "chunk-0010")
    aside = tmp_path / "aside"
    # 33 of 34: a missing witness refuses before the world exists.
    shutil.move(str(directory.parent), str(aside))
    with pytest.raises(cm.ChunkMultipassError, match="chunk 'chunk-0010' has no valid retained"):
        final_in_process(run, partial, database, label="missing")
    assert not world.exists()
    shutil.move(str(aside), str(directory.parent))
    # An extra witness directory the plan does not name refuses.
    (retained / "chunk-9999").mkdir()
    with pytest.raises(cm.ChunkMultipassError, match="do not name"):
        final_in_process(run, partial, database, label="extra")
    (retained / "chunk-9999").rmdir()
    # A stray file under the retained root refuses too.
    (retained / "notes.txt").write_text("stray", encoding="utf-8")
    with pytest.raises(cm.ChunkMultipassError, match="do not name"):
        final_in_process(run, partial, database, label="stray")
    (retained / "notes.txt").unlink()
    # Two valid witnesses for one chunk are ambiguous authority.
    shutil.copytree(directory, directory.parent / "attempt-001")
    with pytest.raises(cm.ChunkMultipassError, match="2 valid retained witnesses"):
        final_in_process(run, partial, database, label="duplicate")
    shutil.rmtree(directory.parent / "attempt-001")
    # A witness of another run -- genuinely written under that run -- refuses.
    shutil.move(str(directory.parent), str(aside))
    write_witness(run, partial, "chunk-0010", run_id="other-run")
    with pytest.raises(cm.ChunkMultipassError, match="another run"):
        final_in_process(run, partial, database, label="wrong-run")
    shutil.rmtree(directory.parent)
    shutil.move(str(aside), str(directory.parent))
    # A stale payload: the bytes moved under a sealed record.
    payload = directory / cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME
    original = payload.read_bytes()
    payload.write_bytes(original + b"\x00")
    with pytest.raises(cm.ChunkMultipassError, match="changed payload is refused"):
        final_in_process(run, partial, database, label="stale")
    payload.write_bytes(original)
    # A resealed payload identity: the checkpoint that bound the witness refuses it.
    reseal_witness(directory, semantic_payload_identity="f" * 64)
    with pytest.raises(cm.ChunkMultipassError, match="resealed or substituted"):
        final_in_process(run, partial, database, label="resealed")
    assert not world.exists()


# ==========================================================================
# P4: exact calibration deletion -- M9, M10, M11, M12
# ==========================================================================
def test_p4_m9_m10_m12_the_grant_is_first_and_nothing_is_deleted_before_durability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    plan = run["plan"]
    g0 = partial["schedule"].groups[0]
    retained = retained_of(partial)
    for chunk_id in g0.chunk_ids:
        write_witness(run, partial, chunk_id)
    merge_group(run, partial, g0, database)
    worlds = {chunk_id: snapshot(world_of(run, chunk_id)) for chunk_id in g0.chunk_ids}

    def intact() -> None:
        assert {chunk_id: snapshot(world_of(run, chunk_id)) for chunk_id in g0.chunk_ids} == worlds
        assert not cm.calibration_group_deletion_path(retained, g0.group_id).exists()

    grant = grant_for(partial, plan, g0.group_id)
    # Before the checkpoint: no deletion, whatever the grant.
    with pytest.raises(cm.ChunkMultipassError, match="no calibration group checkpoint"):
        delete_group(run, partial, g0.group_id, grant)
    intact()
    checkpoint = write_checkpoint(run, partial, g0.group_id)
    # The grant is the FIRST gate: none, a wrong run, a wrong plan, a wrong group all refuse.
    assert (
        first_call("delete_calibration_group_chunk_worlds") == "_require_calibration_deletion_grant"
    )
    for bad, problem in (
        (None, "explicit CalibrationDeletionGrant"),
        ("granted", "explicit CalibrationDeletionGrant"),
        (grant_for(partial, plan, g0.group_id, run_id="other"), "nothing is deleted"),
        (grant_for(partial, plan, "group-0001"), "nothing is deleted"),
        (
            cm.CalibrationDeletionGrant(
                run_id=RUN,
                plan_digest="ab" * 32,
                merge_schedule_digest=partial["schedule"].schedule_digest,
                group_ids=(g0.group_id,),
            ),
            "nothing is deleted",
        ),
    ):
        with pytest.raises(cm.ChunkMultipassError, match=problem):
            delete_group(run, partial, g0.group_id, bad)
        intact()
    # M12: the grant precedes every world mutation -- a refused grant never reaches the primitive.
    removals: list[Path] = []
    monkeypatch.setattr(cm, "_remove_exact_entries", lambda base, files: removals.append(base))

    def tripwire(*_args: Any, **_kwargs: Any) -> Any:
        message = "grant refused"
        raise cm.ChunkMultipassError(message)

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm, "_require_calibration_deletion_grant", tripwire)
        with pytest.raises(cm.ChunkMultipassError, match="grant refused"):
            delete_group(run, partial, g0.group_id, grant)
    assert removals == []
    intact()
    monkeypatch.undo()
    # M9: a witness that is not durable refuses the deletion.
    payload = witness_of(partial, "chunk-0005") / cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME
    original = payload.read_bytes()
    payload.write_bytes(original + b"\x00")
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        delete_group(run, partial, g0.group_id, grant)
    intact()
    payload.write_bytes(original)
    aside = tmp_path / "aside"
    shutil.move(str(witness_of(partial, "chunk-0005").parent), str(aside))
    with pytest.raises(cm.ChunkMultipassError, match="no durable retained witness"):
        delete_group(run, partial, g0.group_id, grant)
    intact()
    shutil.move(str(aside), str(witness_of(partial, "chunk-0005").parent))
    # M10: an intermediate that is not durable refuses the deletion.
    receipt_path = (
        partial["intermediates_root"]
        / g0.group_id
        / "attempt-000"
        / cm.INTERMEDIATE_RECEIPT_FILENAME
    )
    receipt_bytes = receipt_path.read_bytes()
    edit_json(receipt_path, lambda d: d.__setitem__("members", 999))
    with pytest.raises(cm.ChunkMultipassError, match="binds intermediate receipt"):
        delete_group(run, partial, g0.group_id, grant)
    intact()
    receipt_path.write_bytes(receipt_bytes)
    # Positive: exact deletion, record bound to the grant and the checkpoint, sources absent.
    deletion = delete_group(run, partial, g0.group_id, grant)
    assert deletion.grant_identity == grant.identity()
    assert deletion.checkpoint_identity == checkpoint.checkpoint_identity
    assert deletion.sources_absent and deletion.expected_freed_bytes > 0
    assert [item.chunk_id for item in deletion.chunks] == list(g0.chunk_ids)
    assert all(
        item.entries_deleted == len(item.entries) and not item.resumed for item in deletion.chunks
    )
    assert all(CHUNK_RECEIPT_FILENAME in item.entries for item in deletion.chunks)
    for chunk_id in g0.chunk_ids:
        assert not world_of(run, chunk_id).exists()
    reread = cm.read_calibration_group_deletion(
        cm.calibration_group_deletion_path(retained, g0.group_id)
    )
    assert reread == deletion and reread.identity() == deletion.deletion_identity
    with pytest.raises(cm.ChunkMultipassError, match="already records a completed deletion"):
        delete_group(run, partial, g0.group_id, grant)
    # Every other group's world is untouched by group-0000's deletion.
    for chunk_id in partial["schedule"].groups[1].chunk_ids:
        assert world_of(run, chunk_id).is_dir()


def test_p4_m11_unexpected_entries_refuse_and_only_a_sorted_suffix_partial_resumes(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    plan = run["plan"]
    g0, g1 = partial["schedule"].groups[0], partial["schedule"].groups[1]
    for group in (g0, g1):
        for chunk_id in group.chunk_ids:
            write_witness(run, partial, chunk_id)
        merge_group(run, partial, group, database)
        write_checkpoint(run, partial, group.group_id)
    grant = grant_for(partial, plan, g0.group_id, g1.group_id)
    before = {chunk_id: snapshot(world_of(run, chunk_id)) for chunk_id in g0.chunk_ids}
    # An unexpected entry in ONE world refuses the whole group before the first deletion.
    stray = world_of(run, "chunk-0002") / "stray.bin"
    stray.write_bytes(b"not manifested")
    with pytest.raises(cm.ChunkMultipassError, match="outside its checkpointed manifest"):
        delete_group(run, partial, g0.group_id, grant)
    stray.unlink()
    assert {chunk_id: snapshot(world_of(run, chunk_id)) for chunk_id in g0.chunk_ids} == before
    # A changed object refuses too -- a changed world is never deleted.
    target = world_of(run, "chunk-0007") / "chunk_plan.json"
    original = target.read_bytes()
    target.write_bytes(original + b"\n")
    with pytest.raises(cm.ChunkMultipassError, match="does not match the checkpointed manifest"):
        delete_group(run, partial, g0.group_id, grant)
    target.write_bytes(original)
    # An interrupted exact deletion -- the first entries in sorted order gone -- resumes.
    checkpoint = cm.read_calibration_group_checkpoint(
        cm.calibration_group_checkpoint_path(retained_of(partial), g0.group_id)
    )
    entries = next(item for item in checkpoint.chunks if item.chunk_id == "chunk-0001").entries
    assert entries[0] == "chunk_declarations.json" and entries[-1] == "working_catalog.sqlite3"
    for relative in entries[:2]:
        (world_of(run, "chunk-0001") / relative).unlink()
    deletion = delete_group(run, partial, g0.group_id, grant)
    resumed = next(item for item in deletion.chunks if item.chunk_id == "chunk-0001")
    assert resumed.resumed and resumed.entries_deleted == len(entries) - 2
    assert all(not item.resumed for item in deletion.chunks if item.chunk_id != "chunk-0001")
    for chunk_id in g0.chunk_ids:
        assert not world_of(run, chunk_id).exists()
    # A partial world that is NOT the remainder of an exact deletion refuses.
    (world_of(run, "chunk-0012") / "working_catalog.sqlite3").unlink()
    with pytest.raises(cm.ChunkMultipassError, match="not the remainder of an exact deletion"):
        delete_group(run, partial, g1.group_id, grant)
    for chunk_id in g1.chunk_ids:
        assert world_of(run, chunk_id).is_dir()
    # The deletion reaches exactly the accepted exact-entry primitive, from exactly one site,
    # and the module spells no removal capability of its own (z03 stays the audit).
    source = Path(cm.__file__).read_text(encoding="utf-8")
    assert c13i.capability_violations(source, module="disclosure_drift.m3.chunk_multipass") == []
    assert source.count("_remove_exact_entries(") == 1
    deleter = inspect.getsource(cm.delete_calibration_group_chunk_worlds)
    assert "_remove_exact_entries(" in deleter
    assert "import shutil" not in source and ".rmtree(" not in source
    assert inspect.getsource(ctr._remove_exact_entries).count("os.walk") == 0
    assert "Never a recursive tree removal" in inspect.getsource(ctr._remove_exact_entries)


# ==========================================================================
# P5 + P6: five intermediates + witnesses; retain-everything == retention-aware == committed
# ==========================================================================
def test_p5_p6_m5_m13_m14_retention_aware_equals_retain_everything_equals_the_committed_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Path A: every chunk world retained; witnesses and checkpoints written; no deletion.
    database_a, _tree_a, run_a, partial_a = topology_run(tmp_path / "a")
    a = lifecycle(run_a, partial_a, database_a, delete=False)
    assert [counters(r) for r in a["receipts"]] == list(TOPOLOGY_LEVEL_ONE)
    result_a = final_in_process(run_a, partial_a, database_a, label="a")
    # The accepted derivation over the retained CHUNK WORLDS, against Path A's final world.
    chunks = cc.resolve_chunk_inputs(run_a["plan"], internal_root=run_a["chunk_root"])
    connection = sqlite3.connect(
        str(partial_a["world_directory"] / WORKING_CATALOG_FILENAME), isolation_level=None
    )
    connection.row_factory = sqlite3.Row
    try:
        over_chunks = cm._plan_first_witness_counters(connection, chunks)
    finally:
        connection.close()
    # Path B: the same source, every group exact-deleted after its checkpoint.
    database_b, _tree_b, run_b, partial_b = topology_run(tmp_path / "b")
    b = lifecycle(run_b, partial_b, database_b, delete=True)
    assert all(d is not None for d in b["deletions"]) and len(b["witnesses"]) == 34
    for bounds in run_b["plan"].chunks:
        assert not world_of(run_b, bounds.chunk_id).exists()

    # M13: the final opens no chunk world -- every chunk-resolving name is a tripwire.
    def never(*_args: Any, **_kwargs: Any) -> Any:
        message = "the calibration final resolved a chunk world"
        raise AssertionError(message)

    monkeypatch.setattr(cm, "resolve_chunk_inputs", never)
    monkeypatch.setattr(cm, "derive_chunk_placement", never)
    monkeypatch.setattr(cc, "derive_chunk_placement", never)
    monkeypatch.setattr(cc, "derive_placements", never)
    result_b = final_in_process(run_b, partial_b, database_b, label="b")
    monkeypatch.undo()
    # Exact equality: every accepted whole-run semantic and counter, three ways.
    assert semantic(result_a) == semantic(result_b) == dict(TOPOLOGY_COMMITTED)
    assert counters(result_a) == counters(result_b) == over_chunks == (1, 55, 10, 50)
    level_one = tuple(sum(item[i] for item in TOPOLOGY_LEVEL_ONE) for i in range(4))
    assert level_one == (4, 55, 7, 35) != counters(result_b)
    assert result_a.result_identity != result_b.result_identity  # process facts differ
    assert result_b.intermediate_count == 5 and result_b.chunk_count == 34
    # The independent restatement, read LAST because its read-only opens leave -wal/-shm.
    assert sem.whole_f0_counters(c13.chunk_directories(run_a)) == counters(result_b)


def test_p6_the_small_world_under_groupwise_deletion_equals_its_committed_values(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = small_run(tmp_path)
    b = lifecycle(run, partial, database, delete=True)
    assert [len(g.chunk_ids) for g in partial["schedule"].groups] == [9, 1, 1]
    assert [counters(r) for r in b["receipts"]] == [(1, 15, 2, 10), (0, 0, 0, 0), (0, 0, 0, 0)]
    result = final_in_process(run, partial, database, label="small")
    record = dict(result.as_record())
    assert {key: record[key] for key in SMALL_COMMITTED} == dict(SMALL_COMMITTED)
    for bounds in run["plan"].chunks:
        assert not world_of(run, bounds.chunk_id).exists()


def test_p6_m14_an_inert_sharer_world_keeps_the_plan_ordinal_load_bearing(tmp_path: Path) -> None:
    """The C8 asymmetry, on the witness route: a sharer whose shared-accession fields are inert
    materializes nothing as a first witness and six rows as a rival, so WHICH chunk ranks first
    moves ``first_witness_rows_staged``. The witnesses' plan ordinals must therefore be the
    chunks' own -- and the witness route must equal the chunk-world derivation exactly."""
    members = sem.o1_members(primaries=12, sharers=(0, 4, 9), inert=(9,))
    database, tree = sem.build_custom_world(tmp_path / "world", members)
    plan = c27.subset_plan(tree, database, prefix=10, chunk_members=1)
    assert plan.chunk_count == 11 and plan.selected_shard_members == 2
    run = c27.execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    partial = c27.prepared_multipass(run)
    assert [len(g.chunk_ids) for g in partial["schedule"].groups] == [9, 1, 1]
    lifecycle(run, partial, database, delete=False)
    result = final_in_process(run, partial, database, label="inert")
    chunks = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    connection = sqlite3.connect(
        str(partial["world_directory"] / WORKING_CATALOG_FILENAME), isolation_level=None
    )
    connection.row_factory = sqlite3.Row
    try:
        over_chunks = cm._plan_first_witness_counters(connection, chunks)
    finally:
        connection.close()
    assert counters(result) == over_chunks
    assert counters(result)[0] == 1 and counters(result)[1] > 0
    # The ranking is load-bearing here: reversing the witnesses' ordinals moves the staged rows,
    # so the equality above is a real proof and not a coincidence of uniform payloads.
    witnesses = cm.resolve_calibration_chunk_witnesses(
        plan, partial["schedule"], run_id=RUN, retained_root=retained_of(partial)
    )
    reversed_ordinals = [
        cm.RetainedWitnessInput(
            chunk_id=item.chunk_id,
            ordinal=plan.chunk_count - 1 - item.ordinal,
            region=item.region,
            start=item.start,
            end=item.end,
            directory=item.directory,
            witness=item.witness,
        )
        for item in witnesses
    ]
    connection = sqlite3.connect(
        str(partial["world_directory"] / WORKING_CATALOG_FILENAME), isolation_level=None
    )
    connection.row_factory = sqlite3.Row
    try:
        drifted = cm._plan_first_witness_counters(connection, reversed_ordinals)
    finally:
        connection.close()
    assert drifted != counters(result)
    assert sem.whole_f0_counters(c13.chunk_directories(run)) == counters(result)


def test_p5_the_final_refuses_a_missing_or_moved_checkpoint_and_an_unbound_intermediate(
    tmp_path: Path,
) -> None:
    database, _tree, run, partial = topology_run(tmp_path)
    lifecycle(run, partial, database, delete=True)
    retained = retained_of(partial)
    path = cm.calibration_group_checkpoint_path(retained, "group-0002")
    original = path.read_bytes()
    # Missing checkpoint.
    aside = tmp_path / "checkpoint.aside"
    shutil.move(str(path), str(aside))
    with pytest.raises(cm.ChunkMultipassError, match="no calibration group checkpoint"):
        final_in_process(run, partial, database, label="missing-checkpoint")
    shutil.move(str(aside), str(path))
    # A tampered checkpoint refuses on its seal; a resealed one refuses on its binding.
    record = json.loads(original)
    record["intermediate_receipt_sha256"] = "9" * 64
    path.write_bytes(cp.canonical_json_bytes(record))
    with pytest.raises(cm.ChunkMultipassError, match="does not describe its own contents"):
        final_in_process(run, partial, database, label="tampered-checkpoint")
    record["checkpoint_identity"] = cm._record_identity(record, "checkpoint_identity")
    path.write_bytes(cp.canonical_json_bytes(record))
    with pytest.raises(cm.ChunkMultipassError, match="binds intermediate receipt"):
        final_in_process(run, partial, database, label="resealed-checkpoint")
    path.write_bytes(original)
    # An intermediate whose bound receipt digest is not the witness's is never admitted.
    receipt_path = (
        partial["intermediates_root"]
        / "group-0001"
        / "attempt-000"
        / cm.INTERMEDIATE_RECEIPT_FILENAME
    )
    receipt_bytes = receipt_path.read_bytes()
    edit_json(receipt_path, lambda d: d["input_receipt_sha256"].__setitem__(0, "8" * 64))
    with pytest.raises(cm.ChunkMultipassError, match="binds intermediate receipt"):
        final_in_process(run, partial, database, label="unbound-intermediate")
    receipt_path.write_bytes(receipt_bytes)
    assert not partial["world_directory"].exists()
    result = final_in_process(run, partial, database, label="ok")
    assert counters(result) == (1, 55, 10, 50)


# ==========================================================================
# P7: production isolation -- M15, M16
# ==========================================================================
PRODUCTION_ENTRIES = (
    "run_multipass_f0",
    "run_group_merge",
    "run_final_merge",
    "merge_group_body",
    "finalize_multipass_body",
    "_child_main",
    # D151-C31R2-R19A-C2 §16: the production successor wrapper is gated, delegates narrowly and
    # is held to the same retention-name byte scan as every other production entry.
    "run_successor_multipass_final",
)
RETENTION_NAMES = (
    "resolve_contiguous_chunk_inputs",
    "resolve_calibration_chunk_witnesses",
    "resolve_calibration_group_checkpoints",
    "calibration_retained_root",
    "RetainedWitnessInput",
    "CalibrationDeletionGrant",
    "_remove_exact_entries",
    "delete_calibration_group_chunk_worlds",
    "_require_witness_bound_intermediates",
)


def test_p7_m16_production_entries_keep_their_gates_and_name_no_retention_route() -> None:
    # Every production entry is byte-wise free of the retention route and keeps resolving the
    # WHOLE plan through the accepted single-pass admission, authority first.
    for name in PRODUCTION_ENTRIES:
        text = inspect.getsource(getattr(cm, name))
        for needle in RETENTION_NAMES:
            assert needle not in text, (name, needle)
    for body in ("merge_group_body", "finalize_multipass_body"):
        text = inspect.getsource(getattr(cm, body))
        assert "resolve_chunk_inputs(" in text and "_require_expected_binding(" in text
    assert "chunk_inputs=chunks" in inspect.getsource(cm.finalize_multipass_body)
    assert "_plan_first_witness_counters(connection, chunks)" in inspect.getsource(
        cm.finalize_multipass_body
    )
    tree = ast.parse(Path(cm.__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    callers = {
        node.name
        for node in functions.values()
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "require_real_multipass_authority"
    }
    assert callers == set(PRODUCTION_ENTRIES)
    for name in PRODUCTION_ENTRIES:
        assert first_call(name) == "require_real_multipass_authority", name
    assert c13i.committed_literal(cm, "_CHILD_BOOTSTRAP") == c13i.MULTIPASS_CHILD_BOOTSTRAP
    assert (
        c13i.committed_literal(cm, "_CALIBRATION_CHILD_BOOTSTRAP")
        == c13i.CALIBRATION_MULTIPASS_CHILD_BOOTSTRAP
    )
    assert c13i.committed_literal(cm, "REAL_MULTIPASS_F0_AUTHORITY") is None
    assert "NOT AUTHORIZED" in c13i.refusal_in_a_fresh_interpreter()


def test_p7_m15_production_bodies_never_consume_a_retained_witness(tmp_path: Path) -> None:
    # Behaviourally, with the production authority OPENED synthetically: a production final and
    # a production group merge over a plan whose chunk world is gone refuse on the missing chunk
    # -- with a real retained witness and a checkpoint sitting exactly where the calibration
    # route would look. Nothing in production reads them.
    database_c, _tree_c, run_c, partial_c = small_run(tmp_path / "calibration")
    lifecycle(run_c, partial_c, database_c, delete=False)
    with pytest.MonkeyPatch.context() as patcher:
        c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
        database, tree = c1.build_world(tmp_path / "production", members=9, shards=1, filings=2)
        plan = c13.multipass_plan(tree, database, chunk_members=1)
        run = c13.execute_in_process(plan, tmp_path / "production" / "run", database, tree)
        merged = c13.merge_in_process(run, database, finalize=False)
        retained = cm.calibration_retained_root(merged["intermediates_root"])
        shutil.copytree(retained_of(partial_c), retained)
        shutil.rmtree(run["chunk_root"] / "chunk-0000")
        with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0000' {MISSING}"):
            cm.finalize_multipass_body(
                c13.final_request(
                    run,
                    schedule_path=merged["schedule_path"],
                    intermediates_root=merged["intermediates_root"],
                    world_directory=merged["multipass_root"] / "final",
                    database=database,
                    run_id="m15",
                )
            )
        assert not (merged["multipass_root"] / "final").exists()
        group = merged["schedule"].groups[0]
        with pytest.raises(cs.ChunkStorageError, match=f"chunk 'chunk-0000' {MISSING}"):
            cm.merge_group_body(
                c13.group_request(
                    run,
                    schedule_path=merged["schedule_path"],
                    group_id=group.group_id,
                    attempt=7,
                    attempt_directory=merged["intermediates_root"] / group.group_id / "attempt-007",
                    database=database,
                )
            )
        assert not (merged["intermediates_root"] / group.group_id / "attempt-007").exists()
    assert cm.REAL_MULTIPASS_F0_AUTHORITY is None
    # No production reclaim is conferred: the authority stays closed and the storage module still
    # holds no removal call (the C1 invariant, re-asserted beside the calibration deletion).
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    storage = Path(cs.__file__).read_text(encoding="utf-8")
    for capability in ("unlink", "rmtree", "os.remove", "rmdir", "shutil.move"):
        assert capability not in storage, capability
    deletion_record = cm.read_calibration_group_deletion  # the reader exists
    assert "reclaim" not in cm.CALIBRATION_GROUP_DELETION_EVENT_KIND
    with pytest.raises(cm.ChunkMultipassError):
        deletion_record(tmp_path / "absent-deletion.json")


# ==========================================================================
# P8: the exact 34-chunk lifecycle, group by group, with a restart -- and C28-MINOR-4
# ==========================================================================
def test_p8_the_exact_34_chunk_lifecycle_runs_groupwise_under_deletion_with_a_restart(
    tmp_path: Path,
) -> None:
    database, tree = c27.topology_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=33, chunk_members=1)
    schedule = cm.derive_calibration_subset_schedule(plan)
    assert [len(g.chunk_ids) for g in schedule.groups] == [9, 9, 9, 6, 1]
    base = tmp_path / "campaign"
    chunk_root = base / "chunks"
    events: list[str] = []
    present: list[int] = []

    def observe(event: str) -> None:
        events.append(event)
        if event == "CALIBRATION_PROCESS_START":
            present.append(
                sum(
                    1
                    for bounds in plan.chunks
                    if (chunk_root / bounds.chunk_id / "attempt-000").is_dir()
                )
            )

    grant = cm.CalibrationDeletionGrant(
        run_id="lifecycle",
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_ids=tuple(g.group_id for g in schedule.groups),
    )
    orchestrate: dict[str, Any] = {
        "plan": plan,
        "internal_root": chunk_root,
        "operational_catalog": database,
        "multipass_root": base / "multipass",
        "run_id": "lifecycle",
        "storage_requirements": DISTINCT_RATIO_REQUIREMENTS,
        "instrumentation_ledger": base / "ledger",
        "chunk_execution": cm.CalibrationChunkExecution(
            data_root=tree.data_root, source_instance_id=c1.INSTANCE, batch_size=c13.BATCH
        ),
        "deletion_grant": grant,
        "observe": observe,
    }
    # An INTERRUPTED supervisor: groups 0 and 1 complete -- parsed, witnessed, merged,
    # checkpointed, deleted -- and the process dies before group 2 starts.
    deleted: list[str] = []
    original = cm.delete_calibration_group_chunk_worlds

    def interrupting(grant_: object, **kwargs: Any) -> Any:
        record = original(grant_, **kwargs)
        deleted.append(kwargs["group_id"])
        if len(deleted) == 2:
            message = "simulated supervisor interruption after group-0001's deletion"
            raise cm.ChunkMultipassError(message)
        return record

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm, "delete_calibration_group_chunk_worlds", interrupting)
        with pytest.raises(cm.ChunkMultipassError, match="simulated"):
            cm.run_calibration_subset_multipass(**orchestrate)
    assert deleted == ["group-0000", "group-0001"]
    assert events.count("CALIBRATION_PROCESS_START") == 18 + 2
    retained = base / "multipass" / "retained"
    for group in schedule.groups[:2]:
        assert cm.calibration_group_deletion_path(retained, group.group_id).is_file()
        for chunk_id in group.chunk_ids:
            assert not (chunk_root / chunk_id / "attempt-000").exists()
            assert cm.completed_calibration_chunk_witness(retained, chunk_id) is not None
    for group in schedule.groups[2:]:
        assert not cm.calibration_group_checkpoint_path(retained, group.group_id).exists()
        for chunk_id in group.chunk_ids:
            assert not (chunk_root / chunk_id).exists()
    # The RESUMED supervisor never re-parses a deleted group, parses the rest group by group,
    # and finalizes over five intermediates and 34 witnesses with no chunk world left.
    events.clear()
    result = cm.run_calibration_subset_multipass(**orchestrate)
    assert events.count("CALIBRATION_PROCESS_START") == 16 + 3 + 1
    assert max(present) <= 9, present
    assert [len(w) for w in (result.witnesses,)] == [34]
    assert [c.group_id for c in result.checkpoints] == [g.group_id for g in schedule.groups]
    assert all(d is not None for d in result.deletions)
    assert [len(r.input_chunk_ids) for r in result.intermediates] == [9, 9, 9, 6, 1]
    for bounds in plan.chunks:
        assert not (chunk_root / bounds.chunk_id / "attempt-000").exists()
        assert not (chunk_root / bounds.chunk_id / "attempt-001").exists()
    final = result.result
    assert semantic(final) == dict(TOPOLOGY_COMMITTED)
    assert final.run_id == "lifecycle" and os.getpid() not in {r.pid for r in result.intermediates}
    assert result.storage_plan.chunk_bytes_by_id == {
        w.chunk_id: w.chunk_manifest_total_bytes for w in result.witnesses
    }
    # C28-MINOR-4, for the calibration final: the final child charged level two with the
    # LEVEL-TWO peak ratio -- ceil(inputs x 1.5) + seed -- not the level-one ratio.
    event = cm.read_calibration_admission_event(
        cm.calibration_admission_event_path(
            base / "ledger", role="final", step_id="final", attempt=None
        )
    )
    inputs = sum(r.manifest.total_bytes for r in result.intermediates)
    assert event.level == ct.MERGE_LEVEL_TWO and event.input_bytes == inputs
    assert event.peak_bytes == -(-inputs * 15 // 10) + event.seed_catalog_bytes
    assert event.peak_bytes != inputs + event.seed_catalog_bytes
    assert event.transient_bytes == c13.LEVEL_TWO_TRANSIENT_SENTINEL
    for group in schedule.groups:
        level_one = cm.read_calibration_admission_event(
            cm.calibration_admission_event_path(
                base / "ledger", role="group", step_id=group.group_id, attempt=0
            )
        )
        assert level_one.peak_bytes == level_one.input_bytes + level_one.seed_catalog_bytes
    # A COMPLETED run is never re-run under its root, and starts no child on the way.
    events.clear()
    with pytest.raises(ChunkEvidenceError, match="already exists"):
        cm.run_calibration_subset_multipass(**orchestrate)
    assert events == []


def test_p8_a_deleted_group_is_never_reparsed_and_inconsistent_states_refuse(
    tmp_path: Path,
) -> None:
    database, tree = c27.small_world(tmp_path)
    plan = c27.subset_plan(tree, database, prefix=10)
    schedule = cm.derive_calibration_subset_schedule(plan)
    base = tmp_path / "campaign"
    events: list[str] = []
    grant = cm.CalibrationDeletionGrant(
        run_id="small",
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_ids=("group-0000",),
    )
    orchestrate: dict[str, Any] = {
        "plan": plan,
        "internal_root": base / "chunks",
        "operational_catalog": database,
        "multipass_root": base / "multipass",
        "run_id": "small",
        "storage_requirements": c13.LEVEL_DISTINCT_REQUIREMENTS,
        "instrumentation_ledger": base / "ledger",
        "chunk_execution": cm.CalibrationChunkExecution(
            data_root=tree.data_root, source_instance_id=c1.INSTANCE, batch_size=c13.BATCH
        ),
        "observe": events.append,
    }
    # Interrupt right after group-0000's deletion, before group-0001's merge.
    real_merge = cm.run_calibration_subset_group_merge

    def interrupting(request: cm.GroupMergeRequest, **kwargs: Any) -> Any:
        if request.group_id == "group-0001":
            message = "simulated interruption before group-0001"
            raise cm.ChunkMultipassError(message)
        return real_merge(request, **kwargs)

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm, "run_calibration_subset_group_merge", interrupting)
        with pytest.raises(cm.ChunkMultipassError, match="simulated"):
            cm.run_calibration_subset_multipass(**orchestrate, deletion_grant=grant)
    retained = base / "multipass" / "retained"
    assert cm.calibration_group_deletion_path(retained, "group-0000").is_file()
    assert (
        events.count("CALIBRATION_PROCESS_START") == 9 + 1 + 1
    )  # nine chunks, one merge, chunk-0009
    # Resumed WITHOUT the grant: group-0000 is reused from its witnesses -- nothing re-parsed --
    # and the run completes; group-0001's and group-0002's worlds are retained.
    events.clear()
    result = cm.run_calibration_subset_multipass(**orchestrate)
    assert events.count("CALIBRATION_PROCESS_START") == 1 + 2 + 1  # chunk-0010, two merges, final
    assert result.deletions[0] is not None and result.deletions[1] is None
    record = dict(result.result.as_record())
    assert {key: record[key] for key in SMALL_COMMITTED} == dict(SMALL_COMMITTED)
    assert (base / "chunks" / "chunk-0009" / "attempt-000").is_dir()
    assert not (base / "chunks" / "chunk-0000" / "attempt-000").exists()
    # Inconsistent states refuse loudly rather than re-parsing beside a witness.
    fresh = tmp_path / "fresh"
    database2, tree2 = c27.small_world(fresh)
    plan2 = c27.subset_plan(tree2, database2, prefix=10)
    run2 = c27.execute_chunks_in_process(plan2, fresh / "run", database2, tree2)
    partial2 = c27.prepared_multipass(run2)
    write_witness(run2, partial2, "chunk-0000")
    shutil.rmtree(run2["chunk_root"] / "chunk-0000")
    with pytest.raises(cm.ChunkMultipassError, match="no chunk world"):
        cm.run_calibration_subset_multipass(
            plan=plan2,
            internal_root=run2["chunk_root"],
            operational_catalog=database2,
            multipass_root=partial2["multipass_root"],
            run_id=RUN,
            storage_requirements=c13.LEVEL_DISTINCT_REQUIREMENTS,
            instrumentation_ledger=partial2["ledger"],
        )
    assert not (partial2["multipass_root"] / "intermediates").exists()


# ==========================================================================
# P9: closed values, contract literals, family
# ==========================================================================
def test_p9_every_closed_value_stays_closed_and_the_contract_literals_are_exact() -> None:
    for module, name in (
        (ce, "REAL_CHUNKED_F0_EXECUTION_AUTHORITY"),
        (cm, "REAL_MULTIPASS_F0_AUTHORITY"),
        (cs, "REAL_CHUNK_TRANSFER_AUTHORITY"),
        (cs, "REAL_INTERNAL_RECLAIM_AUTHORITY"),
        (cp, "PRODUCTION_CHUNK_MEMBERS"),
        (cs, "INTERNAL_RESERVE_BYTES"),
        (cs, "CHUNK_PEAK_REQUIREMENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_ONE_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_TWO_PEAK_RATIO"),
        (ct, "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES"),
        (ct, "PRODUCTION_SPILL_POLICY"),
        (ct, "QUALIFIED_EXTERNAL_TIER"),
    ):
        assert getattr(module, name) is None, name
        assert c13i.committed_literal(module, name) is None, name
    assert not hasattr(ct, "MULTIPASS_TRANSIENT_BYTES")
    assert cm.CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT == WITNESS_CONTRACT
    assert cm.CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND == "calibration_group_checkpoint"
    assert cm.CALIBRATION_GROUP_DELETION_EVENT_KIND == "calibration_group_deletion"
    assert cm.CALIBRATION_RETAINED_WITNESS_FILENAME == "chunk_retained_witness.json"
    assert cm.CALIBRATION_RETAINED_PAYLOAD_FILENAME == "retained_witness.sqlite3"
    package_root = Path(cm.__file__).parent
    assert sorted(path.stem for path in package_root.glob("chunk_*.py")) == [
        "chunk_consolidation",
        "chunk_evidence",
        "chunk_execution",
        "chunk_multipass",
        "chunk_plan",
        "chunk_storage",
        "chunk_tiering",
        "chunk_transfer",
    ]
    # The new entries open with the calibration gate, never the production one.
    for name in ("write_calibration_chunk_witness", "write_calibration_group_checkpoint"):
        assert first_call(name) == "require_calibration_subset_plan", name
        assert "require_real_multipass_authority" not in inspect.getsource(getattr(cm, name))
    assert first_call("run_calibration_subset_multipass") == "require_calibration_subset_plan"
    # The counter derivation's protocol is satisfied by both sources, and its statement
    # envelope prose is unchanged.
    docstring = inspect.getdoc(cm._plan_first_witness_counters) or ""
    assert "11 + 6 * chunks" in docstring and "PlanWitnessSource" in docstring
    for source_type in (cc.ChunkInput, cm.RetainedWitnessInput):
        assert {"ordinal", "catalog_path", "witness_path"} <= set(dir(source_type))
    assert list(cp.CALIBRATION_SUBSET_CLASSIFICATIONS) == list(c27.LABELS)
