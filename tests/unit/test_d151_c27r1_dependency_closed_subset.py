"""D151-C27R1: the dependency-closed calibration subset -- P1-P7, M1-M16 killing nodes.

What is proved here, over synthetic worlds whose shard parents straddle the primary prefix:

* **P1** the three authorized contracts each have one exact shape; every existing reader refuses
  them and the subset readers refuse every existing contract (M1, M2);
* **P2** the builder selects all and only the D129-R5-valid shards whose declaring parent lies in
  the prefix, under every hostile shape -- undeclared, same-CIK-only, conflicting declarers, a
  second declarer beyond the prefix, a declared parent the filename contradicts, a canonical
  order that is not the parent order (M5, M6, M7);
* **P3** full and selected identities stay independently load-bearing: a moved digest, a false
  total or a moved archive refuses in the child, which rederives the whole universe and the
  closure rather than trusting anything carried (M3, M4, M8, M9);
* **P4** the C29 topology -- 33 primary chunks, one shard chunk, 9 / 9 / 9 / 6 / 1, five
  intermediates, one five-input final -- is built and executes end to end (M10);
* **P5** production launchers, bodies and the production bootstrap refuse the subset plan; the
  calibration route accepts only a matching pipe envelope, validated before anything exists,
  never through argv or the environment (M11, M12, M13);
* **P6** a calibration final world carries no canonical terminal and satisfies no production
  reader (M14);
* **P7** the final child reports level two, the level-two allowance and exact arithmetic in an
  event it produced itself, after validation and never before (M15, M16).

Every calibration child in this module runs with the COMMITTED production authority (``None``);
nothing here opens a production gate.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d110_bounded_parse_memory as d110  # noqa: E402
import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.canary_phases import PHASE_F0, read_phase_checkpoint  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_DECLARATIONS_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    read_receipt_document,
    write_once_json,
)
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

AUTHORITY_REFUSAL = "NOT AUTHORIZED"
LABELS = (
    "CALIBRATION_ONLY",
    "NONCANONICAL",
    "NOT_A_PRODUCTION_INPUT",
    "NOT_A_BOUNDED_CANARY",
)


# ==========================================================================
# Fixtures and world builders
# ==========================================================================
@pytest.fixture(autouse=True)
def _calibration_seams(tmp_path: Path) -> Any:
    """The accepted seams only: pinned repository, temp root, volume provider, child bootstrap.

    Deliberately NOT :func:`test_d151_c13_multipass_plan.open_synthetic_multipass`: the
    production authority stays the committed ``None`` in this process and in every child.
    """
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    temp_root = tmp_path / "sqlite-temp"
    temp_root.mkdir()
    patcher.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp_root))
    patcher.setattr(ewr, "macos_volume_identity", c13.synthetic_volume_provider())
    patcher.setattr(
        cm,
        "_CALIBRATION_CHILD_BOOTSTRAP",
        c13i.calibration_multipass_child_bootstrap(tmp_path / "repo"),
    )
    yield
    patcher.undo()
    c1.unpin_repository()
    assert cm.REAL_MULTIPASS_F0_AUTHORITY is None


def shard_name(cik: int, index: int = 1) -> str:
    return f"CIK{cik:010d}-submissions-{index:03d}.json"


def members_for(
    primaries: int,
    *,
    declares: Mapping[int, tuple[str, ...]],
    shards: list[tuple[int, int]],
    share_every: int = 3,
) -> list[tuple[str, dict[str, Any]]]:
    """Shards first in the given order, then primaries CIK 1..N in order.

    Canonical positions follow: primary CIK ``k`` sits at full position ``k - 1``; the shard
    region is the shards in the order given.
    """
    built: list[tuple[str, dict[str, Any]]] = [c1.shard_document(c, i) for c, i in shards]
    for index in range(primaries):
        cik = index + 1
        built.append(
            c1.primary_document(
                cik,
                filings=2,
                declares=declares.get(cik, ()),
                share=bool(share_every) and index % share_every == 0,
            )
        )
    return built


def build_world(root: Path, members: list[tuple[str, dict[str, Any]]]) -> tuple[Path, DataTree]:
    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = c1.write_archive(tree.data_root / c1.ARCHIVE_RELATIVE, members)
    d110._seed_catalog(database, tree, raw)
    return database, tree


def subset_plan(
    tree: DataTree, database: Path, *, prefix: int, chunk_members: int = 1
) -> cp.CalibrationSubsetPlan:
    observation = c1.observation_of(tree, database)
    return cp.build_calibration_subset_plan(
        archive_path=c1.archive_of(tree),
        source_instance_id=c1.INSTANCE,
        source_observation_id=c1.OBSERVATION,
        source_id=c1.SOURCE_ID,
        source_sha256=observation.logical_sha256,
        source_byte_length=observation.content_size_bytes,
        target=cp.CalibrationSubsetTarget(
            primary_prefix_members=prefix, chunk_members=chunk_members
        ),
    )


def topology_world(root: Path) -> tuple[Path, DataTree]:
    """34 primaries; shards of CIK 1..5 declared inside prefix 33, CIK 34's beyond it."""
    declares = {cik: (shard_name(cik),) for cik in (1, 2, 3, 4, 5, 34)}
    shards = [(cik, 1) for cik in (1, 2, 3, 4, 5, 34)]
    return build_world(root, members_for(34, declares=declares, shards=shards))


def small_world(root: Path) -> tuple[Path, DataTree]:
    """12 primaries; shards of CIK 1 and 3 inside prefix 10, CIK 12's beyond it -> 11 chunks."""
    declares = {cik: (shard_name(cik),) for cik in (1, 3, 12)}
    return build_world(root, members_for(12, declares=declares, shards=[(1, 1), (3, 1), (12, 1)]))


#: Names used by the hostile world: S2 has two declarers (one beyond the prefix), S3 is
#: undeclared with its same-CIK primary inside the prefix, S4 is declared by a registrant its
#: filename contradicts, S11's one parent lies beyond the prefix, S6 and S1 are selected -- in
#: the archive order S2, S6, S3, S1, S4, S11, so the selected order is S6 then S1. Twelve
#: primaries and prefix 10 keep the plan at the multipass floor: 10 primary chunks + 1.
HOSTILE_SHARDS = [(2, 1), (6, 1), (3, 1), (1, 1), (4, 1), (11, 1)]
HOSTILE_PREFIX = 10


def hostile_world(root: Path) -> tuple[Path, DataTree]:
    declares = {
        1: (shard_name(1),),
        2: (shard_name(2),),
        12: (shard_name(2),),
        5: (shard_name(4),),
        6: (shard_name(6),),
        11: (shard_name(11),),
    }
    return build_world(root, members_for(12, declares=declares, shards=HOSTILE_SHARDS))


def plan_on_disk(plan: cp.CalibrationSubsetPlan, base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    plan_path = base / "plan.json"
    ce.write_once_canonical_json(plan_path, dict(plan.as_record()))
    return plan_path


def issued(
    *,
    plan: cp.CalibrationSubsetPlan,
    role: str,
    step_id: str,
    request_path: Path,
    run_id: str = "c27r1",
    ledger: Path | None = None,
) -> ce.CalibrationChildEnvelope:
    return ce.issue_calibration_envelope(
        run_id=run_id,
        plan=plan,
        role=role,
        step_id=step_id,
        request_path=request_path,
        instrumentation_ledger=ledger,
    )


def execute_chunks_in_process(
    plan: cp.CalibrationSubsetPlan, base: Path, database: Path, tree: DataTree
) -> dict[str, Any]:
    """Every chunk through the calibration chunk body, in THIS process, under issued envelopes."""
    plan_path = plan_on_disk(plan, base)
    chunk_root = base / "chunks"
    receipts = []
    contributions = []
    parent_map_path: Path | None = None
    for bounds in plan.chunks:
        if bounds.region == cp.REGION_SHARD and parent_map_path is None:
            merged = ce.merge_parent_map(contributions)
            parent_map_path = base / "parent_map.json"
            write_once_json(
                parent_map_path, {name: sorted(parents) for name, parents in sorted(merged.items())}
            )
        attempt_directory, attempt = ce.next_attempt_directory(chunk_root, bounds.chunk_id)
        request = c1x.chunk_request(
            plan_path=plan_path,
            chunk_id=bounds.chunk_id,
            attempt=attempt,
            attempt_directory=attempt_directory,
            database=database,
            tree=tree,
            parent_map_path=parent_map_path,
            batch_size=c13.BATCH,
            repository=c1.PINNED,
        )
        request_path = base / f"{bounds.chunk_id}-{attempt:03d}-request.json"
        write_once_json(request_path, dict(request.as_record()))
        envelope = issued(
            plan=plan,
            role=ce.CALIBRATION_ROLE_CHUNK,
            step_id=bounds.chunk_id,
            request_path=request_path,
        )
        receipts.append(ce.execute_calibration_subset_chunk_body(request, envelope))
        if bounds.region == cp.REGION_PRIMARY:
            contributions.append(
                ce.read_declarations(attempt_directory / CHUNK_DECLARATIONS_FILENAME)
            )
    return {
        "base": base,
        "plan": plan,
        "plan_path": plan_path,
        "chunk_root": chunk_root,
        "receipts": receipts,
        "parent_map_path": parent_map_path,
    }


def prepared_multipass(run: dict[str, Any], label: str = "multipass") -> dict[str, Any]:
    plan = run["plan"]
    schedule = cm.derive_calibration_subset_schedule(plan)
    multipass_root = run["base"] / label
    multipass_root.mkdir()
    schedule_path = multipass_root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    ledger = run["base"] / f"{label}-ledger"
    ledger.mkdir()
    return {
        "schedule": schedule,
        "schedule_path": schedule_path,
        "multipass_root": multipass_root,
        "intermediates_root": multipass_root / "intermediates",
        "world_directory": multipass_root / "final",
        "ledger": ledger,
    }


def group_request(
    run: dict[str, Any], partial: dict[str, Any], group: cm.MergeGroup, database: Path, attempt: int
) -> tuple[cm.GroupMergeRequest, Path]:
    directory = cm.intermediate_attempt_directory(
        partial["intermediates_root"], group.group_id, attempt
    )
    request = c13.group_request(
        run,
        schedule_path=partial["schedule_path"],
        group_id=group.group_id,
        attempt=attempt,
        attempt_directory=directory,
        database=database,
        requirements=c13.LEVEL_DISTINCT_REQUIREMENTS,
    )
    return request, directory


def retain_in_process(run: dict[str, Any], partial: dict[str, Any], run_id: str) -> Path:
    """D151-C29R1: the retained witnesses and group checkpoints the calibration final consumes,
    written in THIS process for the run the final names, once every intermediate exists.

    Idempotent: an existing witness or checkpoint is re-read by the writer's own reader and
    left alone; nothing is deleted here -- these drivers retain every chunk world.
    """
    plan, schedule = run["plan"], partial["schedule"]
    retained = cm.calibration_retained_root(partial["intermediates_root"])
    retained.mkdir(exist_ok=True)
    for group in schedule.groups:
        for chunk_id in group.chunk_ids:
            if cm.completed_calibration_chunk_witness(retained, chunk_id) is None:
                cm.write_calibration_chunk_witness(
                    plan,
                    schedule,
                    chunk_id=chunk_id,
                    run_id=run_id,
                    chunk_root=run["chunk_root"],
                    retained_root=retained,
                )
        if not cm.calibration_group_checkpoint_path(retained, group.group_id).exists():
            cm.write_calibration_group_checkpoint(
                plan,
                schedule,
                group_id=group.group_id,
                run_id=run_id,
                chunk_root=run["chunk_root"],
                retained_root=retained,
                intermediates_root=partial["intermediates_root"],
            )
    return retained


def final_request(
    run: dict[str, Any], partial: dict[str, Any], database: Path, run_id: str = "c27r1"
) -> cm.FinalMergeRequest:
    # D151-C29R1: a final presupposes every group's lifecycle records for the run it names.
    # They are written only when a final is possible at all -- every intermediate exists -- so
    # a request built only to be refused earlier leaves nothing behind.
    if all(
        cm.completed_intermediate_receipt(partial["intermediates_root"], group.group_id) is not None
        for group in partial["schedule"].groups
    ):
        retain_in_process(run, partial, run_id)
    return c13.final_request(
        run,
        schedule_path=partial["schedule_path"],
        intermediates_root=partial["intermediates_root"],
        world_directory=partial["world_directory"],
        database=database,
        run_id=run_id,
        requirements=c13.LEVEL_DISTINCT_REQUIREMENTS,
    )


def merge_groups_in_process(
    run: dict[str, Any], partial: dict[str, Any], database: Path
) -> list[cm.IntermediateReceipt]:
    receipts = []
    for group in partial["schedule"].groups:
        _directory, attempt = cm.next_intermediate_attempt_directory(
            partial["intermediates_root"], group.group_id
        )
        request, _directory = group_request(run, partial, group, database, attempt)
        request_path = partial["multipass_root"] / f"{group.group_id}-{attempt:03d}-request.json"
        write_once_json(request_path, dict(request.as_record()))
        envelope = issued(
            plan=run["plan"],
            role=ce.CALIBRATION_ROLE_GROUP,
            step_id=group.group_id,
            request_path=request_path,
            ledger=partial["ledger"],
        )
        receipts.append(cm.merge_calibration_subset_group_body(request, envelope))
    return receipts


def finalize_in_process(
    run: dict[str, Any], partial: dict[str, Any], database: Path, run_id: str = "c27r1"
) -> cm.CalibrationSubsetResult:
    request = final_request(run, partial, database, run_id)
    request_path = partial["multipass_root"] / "final-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = issued(
        plan=run["plan"],
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="final",
        request_path=request_path,
        run_id=run_id,
        ledger=partial["ledger"],
    )
    return cm.finalize_calibration_subset_body(request, envelope)


def spawn_calibration_child(
    request_path: Path, envelope: ce.CalibrationChildEnvelope
) -> subprocess.CompletedProcess[str]:
    """A REAL calibration child under the patched bootstrap, exactly as the launcher starts one."""
    with ce.delivered_calibration_envelope(envelope) as envelope_fd:
        return subprocess.run(
            [
                sys.executable,
                "-c",
                cm._CALIBRATION_CHILD_BOOTSTRAP,
                str(request_path),
                str(envelope_fd),
            ],
            capture_output=True,
            text=True,
            check=False,
            pass_fds=(envelope_fd,),
        )


def resealed(plan: cp.CalibrationSubsetPlan, **changes: Any) -> dict[str, object]:
    """A tampered subset plan whose digest is recomputed, so only a rule can catch it."""
    tampered = replace(plan, **changes, plan_digest="")
    record = dict(tampered.as_record())
    record["plan_digest"] = cp._plan_digest(tampered)
    return record


def nothing_under(root: Path) -> None:
    assert not root.exists() or not any(root.rglob("*")), sorted(root.rglob("*"))


# ==========================================================================
# P1: contracts and exact shapes -- M1, M2
# ==========================================================================
def test_p1_the_three_authorized_contracts_are_exact_literals() -> None:
    assert cp.CALIBRATION_SUBSET_PLAN_CONTRACT == "m3.3-chunked-f0-calibration-subset-plan/1"
    assert (
        ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT
        == "m3.3-chunked-f0-calibration-subset-child-envelope/1"
    )
    assert cm.CALIBRATION_SUBSET_RESULT_CONTRACT == "m3.3-chunked-f0-calibration-subset-result/1"
    assert cp.CALIBRATION_SUBSET_CLASSIFICATIONS == LABELS
    assert cp.SHARD_EXCLUSION_CLASSES == (
        "parent_outside_prefix",
        "undeclared",
        "multiple_declarers",
        "cik_conflict",
    )
    # No production reader learned the subset contract: the three-contract set is unchanged.
    assert (
        frozenset(
            {cp.CHUNK_PLAN_CONTRACT, cp.CALIBRATION_PLAN_CONTRACT, cp.MULTIPASS_PLAN_CONTRACT}
        )
        == cp._PLAN_CONTRACTS
    )


def test_p1_m1_m2_the_existing_readers_refuse_the_subset_plan_and_the_reverse(
    tmp_path: Path,
) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    record = json.loads(cp.canonical_json_bytes(plan.as_record()))
    # M1: the accepted plan reader never adopts the subset contract.
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(record)
    # The consolidator, the multipass gate and the schedule derivation refuse the object too.
    with pytest.raises(cc.ChunkConsolidationError, match="single-pass"):
        cc.require_single_pass_plan(plan)
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.require_multipass_plan(plan)
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.derive_merge_schedule(plan)
    # M2: the subset reader refuses every complete-source contract, sealed or relabelled.
    ordinary = c1.build_plan(tree, database, chunk_members=5)
    observation = c1.observation_of(tree, database)
    common: dict[str, Any] = {
        "archive_path": c1.archive_of(tree),
        "source_instance_id": c1.INSTANCE,
        "source_observation_id": c1.OBSERVATION,
        "source_id": c1.SOURCE_ID,
        "source_sha256": observation.logical_sha256,
        "source_byte_length": observation.content_size_bytes,
    }
    calibration = cp.build_calibration_chunk_plan(**common, chunk_members=1)
    multipass = cp.build_multipass_chunk_plan(**common, chunk_members=1)
    for other in (ordinary, calibration, multipass):
        with pytest.raises(cp.ChunkPlanError, match="is exact"):
            cp.CalibrationSubsetPlan.from_record(dict(other.as_record()))
        with pytest.raises(cp.ChunkPlanError, match="not a calibration-subset plan"):
            cp.require_calibration_subset_plan(other)
        with pytest.raises(cp.ChunkPlanError):
            cm.derive_calibration_subset_schedule(other)
    for contract in (
        cp.CHUNK_PLAN_CONTRACT,
        cp.CALIBRATION_PLAN_CONTRACT,
        cp.MULTIPASS_PLAN_CONTRACT,
    ):
        relabelled = resealed(plan, contract=contract)
        with pytest.raises(cp.ChunkPlanError):
            cp.CalibrationSubsetPlan.from_record(relabelled)
    # A base plan wearing the subset contract is refused at the width rule.
    base = replace(
        cp.ChunkPlan(**{f: getattr(plan, f) for f in cp.ChunkPlan.__dataclass_fields__}),
        plan_digest="",
    )
    base = replace(base, plan_digest=cp._plan_digest(base))
    with pytest.raises(cp.ChunkPlanError, match="names a shape"):
        cp.require_sealed_plan(base)


def test_p1_the_subset_reader_is_exact_shape(tmp_path: Path) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    record = json.loads(cp.canonical_json_bytes(plan.as_record()))
    assert cp.CalibrationSubsetPlan.from_record(record) == plan
    for key in sorted(record):
        missing = {k: v for k, v in record.items() if k != key}
        with pytest.raises(cp.ChunkPlanError, match="is exact"):
            cp.CalibrationSubsetPlan.from_record(missing)
    with pytest.raises(cp.ChunkPlanError, match="is exact"):
        cp.CalibrationSubsetPlan.from_record({**record, "smuggled": 1})
    with pytest.raises(cp.ChunkPlanError, match="integer is required"):
        cp.CalibrationSubsetPlan.from_record({**record, "selected_members": "12"})
    with pytest.raises(cp.ChunkPlanError, match="integer is required"):
        cp.CalibrationSubsetPlan.from_record({**record, "selected_members": True})
    assert plan.calibration_subset and not plan.calibration_only and not plan.multipass


def test_p1_the_envelope_event_and_result_readers_are_exact(tmp_path: Path) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    request_path = tmp_path / "request.json"
    write_once_json(request_path, {"anything": 1})
    envelope = issued(
        plan=plan, role=ce.CALIBRATION_ROLE_GROUP, step_id="group-0000", request_path=request_path
    )
    record = dict(envelope.as_record())
    assert set(record) == {
        "contract",
        "run_id",
        "plan_digest",
        "selected_member_ceiling",
        "role",
        "step_id",
        "request_sha256",
        "parent_pid",
        "nonce",
        "instrumentation_ledger",
    }
    assert ce.CalibrationChildEnvelope.from_record(record) == envelope
    assert envelope.selected_member_ceiling == plan.primary_prefix_members + plan.full_shard_members
    for key in record:
        with pytest.raises(ce.ChunkExecutionError, match="is exact"):
            ce.CalibrationChildEnvelope.from_record({k: v for k, v in record.items() if k != key})
    with pytest.raises(ce.ChunkExecutionError, match="is exact"):
        ce.CalibrationChildEnvelope.from_record({**record, "extra": 1})
    with pytest.raises(ce.ChunkExecutionError, match="refused; this build reads"):
        ce.CalibrationChildEnvelope.from_record({**record, "contract": cm.MERGE_SCHEDULE_CONTRACT})
    with pytest.raises(ce.ChunkExecutionError, match="no other is executed"):
        ce.CalibrationChildEnvelope.from_record({**record, "role": "supervisor"})
    with pytest.raises(ce.ChunkExecutionError, match="non-negative integer"):
        ce.CalibrationChildEnvelope.from_record({**record, "parent_pid": True})
    # Canonical bytes: sorted keys, compact separators, one trailing newline, no NaN.
    rendered = cp.canonical_json_bytes({"b": 1, "a": [1, 2]})
    assert rendered == b'{"a":[1,2],"b":1}\n'
    with pytest.raises(cp.ChunkPlanError, match="cannot carry"):
        cp.canonical_json_bytes({"a": float("nan")})
    with pytest.raises(cp.ChunkPlanError, match="cannot carry"):
        cp.canonical_json_bytes({"a": Path("x")})


# ==========================================================================
# P2: dependency-closed selection -- M5, M6, M7
# ==========================================================================
def test_p2_m5_m6_m7_the_closure_selects_all_and_only_valid_shards_inside_the_prefix(
    tmp_path: Path,
) -> None:
    database, tree = hostile_world(tmp_path)
    members = cp.canonical_member_sequence(c1.archive_of(tree))
    closure = cp.derive_dependency_closure(
        c1.archive_of(tree), members, primary_prefix_members=HOSTILE_PREFIX
    )
    # All and only: S6 and S1, in CANONICAL (archive) order, not parent order (M5, M6).
    assert [b.shard_member_name for b in closure.selected] == [shard_name(6), shard_name(1)]
    assert [b.parent_canonical_position for b in closure.selected] == [5, 0]
    assert [b.parent_member_name for b in closure.selected] == [
        "CIK0000000006.json",
        "CIK0000000001.json",
    ]
    assert [b.parent_registrant_cik_padded for b in closure.selected] == [
        "0000000006",
        "0000000001",
    ]
    excluded = {e.shard_member_name: e for e in closure.excluded}
    assert set(excluded) == {shard_name(2), shard_name(3), shard_name(4), shard_name(11)}
    # A second declarer BEYOND the prefix makes the shard ineligible -- only a complete scan can
    # see it, so a prefix-only ("partial") closure is refused by this line (M7).
    assert excluded[shard_name(2)].exclusion_class == cp.SHARD_EXCLUSION_MULTIPLE_DECLARERS
    assert excluded[shard_name(2)].declarer_positions == (1, 11)
    assert excluded[shard_name(2)].declared_ciks == ("0000000002", "0000000012")
    # Undeclared: the same-CIK primary sits INSIDE the prefix and still binds nothing (M6).
    assert excluded[shard_name(3)].exclusion_class == cp.SHARD_EXCLUSION_UNDECLARED
    assert excluded[shard_name(3)].declarer_positions == ()
    # A declared parent the filename contradicts (M7).
    assert excluded[shard_name(4)].exclusion_class == cp.SHARD_EXCLUSION_CIK_CONFLICT
    assert excluded[shard_name(4)].declared_ciks == ("0000000005",)
    # A valid parent beyond the prefix.
    assert excluded[shard_name(11)].exclusion_class == cp.SHARD_EXCLUSION_PARENT_OUTSIDE_PREFIX
    assert excluded[shard_name(11)].declarer_positions == (10,)
    assert closure.excluded_by_class() == {
        "parent_outside_prefix": 1,
        "undeclared": 1,
        "multiple_declarers": 1,
        "cik_conflict": 1,
    }
    assert (closure.full_primary_members, closure.full_shard_members) == (12, 6)
    # Every shard of the full region is classified exactly once, in canonical order.
    positions = sorted(
        [b.shard_canonical_position for b in closure.selected]
        + [e.shard_canonical_position for e in closure.excluded]
    )
    assert positions == list(range(12, 18))
    # The binding digest covers both sets: moving an exclusion class moves it.
    moved = replace(
        closure,
        excluded=tuple(
            replace(e, exclusion_class=cp.SHARD_EXCLUSION_UNDECLARED)
            if e.shard_member_name == shard_name(11)
            else e
            for e in closure.excluded
        ),
    )
    assert moved.binding_digest() != closure.binding_digest()
    # The plan records exactly this closure.
    plan = subset_plan(tree, database, prefix=HOSTILE_PREFIX)
    assert plan.selected_shard_members == 2 and plan.excluded_shard_members == 4
    assert dict(plan.excluded_shards_by_class) == closure.excluded_by_class()
    assert plan.shard_parent_binding_digest == closure.binding_digest()
    assert plan.selected_shard_member_order_digest == cp.selected_shard_member_order_digest(
        members, closure
    )
    selected = cp.selected_member_sequence(members, closure)
    assert [m.member_name for m in selected[HOSTILE_PREFIX:]] == [shard_name(6), shard_name(1)]
    assert [m.canonical_position for m in selected] == list(range(12))
    assert [m.archive_ordinal for m in selected[HOSTILE_PREFIX:]] == [
        members[13].archive_ordinal,
        members[15].archive_ordinal,
    ]


def test_p2_a_prefix_that_selects_no_shard_or_is_not_proper_is_refused(tmp_path: Path) -> None:
    database2, tree2 = build_world(
        tmp_path / "none",
        members_for(4, declares={4: (shard_name(4),)}, shards=[(4, 1)]),
    )
    with pytest.raises(cp.ChunkPlanError, match="no shard is dependency-closed"):
        subset_plan(tree2, database2, prefix=2)
    with pytest.raises(cp.ChunkPlanError, match="PROPER primary prefix"):
        subset_plan(tree2, database2, prefix=4)
    with pytest.raises(cp.ChunkPlanError, match="PROPER primary prefix"):
        subset_plan(tree2, database2, prefix=5)
    with pytest.raises(cp.ChunkPlanError, match="positive integer"):
        cp.CalibrationSubsetTarget(primary_prefix_members=0, chunk_members=1)
    with pytest.raises(cp.ChunkPlanError, match="positive integer"):
        cp.CalibrationSubsetTarget(primary_prefix_members=1, chunk_members=True)


# ==========================================================================
# P3: full provenance and child rederivation -- M3, M4, M8, M9
# ==========================================================================
TAMPERABLE_DIGESTS = (
    "member_order_digest",
    "selected_member_order_digest",
    "shard_parent_binding_digest",
    "selected_shard_member_order_digest",
)


@pytest.mark.parametrize("field", TAMPERABLE_DIGESTS)
def test_p3_m3_m4_every_identity_is_inside_the_seal(tmp_path: Path, field: str) -> None:
    database, tree = hostile_world(tmp_path)
    plan = subset_plan(tree, database, prefix=HOSTILE_PREFIX)
    record = dict(plan.as_record())
    record[field] = "ef" * 32
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.CalibrationSubsetPlan.from_record(record)
    for count_field in ("full_total_members", "selected_members", "excluded_shard_members"):
        counted = dict(plan.as_record())
        counted[count_field] = int(counted[count_field]) + 1  # type: ignore[call-overload]
        with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
            cp.CalibrationSubsetPlan.from_record(counted)


@pytest.mark.parametrize("field", TAMPERABLE_DIGESTS)
def test_p3_m9_a_moved_identity_is_refused_by_the_child_against_the_real_source(
    tmp_path: Path, field: str
) -> None:
    database, tree = hostile_world(tmp_path)
    plan = subset_plan(tree, database, prefix=HOSTILE_PREFIX)
    tampered = cp.CalibrationSubsetPlan.from_record(resealed(plan, **{field: "ef" * 32}))
    shard_chunk = cp.chunks_in_region(plan, cp.REGION_SHARD)[0].chunk_id
    with pytest.raises(cp.ChunkPlanError, match="where the (calibration-subset )?plan records"):
        cp.resolve_calibration_subset_members(tampered, c1.archive_of(tree), shard_chunk)
    with pytest.raises(cp.ChunkPlanError, match="where the (calibration-subset )?plan records"):
        cp.resolve_calibration_subset_members(tampered, c1.archive_of(tree), "chunk-0000")


def test_p3_a_false_total_or_a_moved_archive_is_refused_by_the_child(tmp_path: Path) -> None:
    database, tree = hostile_world(tmp_path)
    plan = subset_plan(tree, database, prefix=HOSTILE_PREFIX)
    # A resealed record claiming one more full primary member: coverage passes, the child refuses.
    false_total = cp.CalibrationSubsetPlan.from_record(
        resealed(plan, full_total_members=19, full_primary_members=13)
    )
    with pytest.raises(cp.ChunkPlanError, match="archive holds .* governed members where"):
        cp.resolve_calibration_subset_members(false_total, c1.archive_of(tree), "chunk-0000")
    # A resealed record whose selected-shard counts moved together: the closure refuses.
    counts = cp.CalibrationSubsetPlan.from_record(
        resealed(
            plan,
            selected_shard_members=3,
            shard_members=3,
            excluded_shard_members=3,
            excluded_shards_by_class={**dict(plan.excluded_shards_by_class), "undeclared": 0},
            selected_members=13,
            total_members=13,
            chunks=(*plan.chunks[:-1], replace(plan.chunks[-1], end=13)),
        )
    )
    with pytest.raises(cp.ChunkPlanError, match="rederived"):
        cp.resolve_calibration_subset_members(counts, c1.archive_of(tree), "chunk-0000")
    # A moved archive: one extra governed member changes the full universe.
    moved = build_world(
        tmp_path / "moved",
        members_for(9, declares={1: (shard_name(1),)}, shards=[(1, 1)]),
    )
    with pytest.raises(cp.ChunkPlanError, match="FULL canonical member ordering digest"):
        cp.resolve_calibration_subset_members(plan, c1.archive_of(moved[1]), "chunk-0000")


def test_p3_m8_the_child_rebuilds_the_universe_and_the_closure_rather_than_slicing(
    tmp_path: Path,
) -> None:
    """The selected shards are NOT a prefix of the shard region: S6 (9) and S1 (11)."""
    database, tree = hostile_world(tmp_path)
    plan = subset_plan(tree, database, prefix=HOSTILE_PREFIX)
    shard_chunk = cp.chunks_in_region(plan, cp.REGION_SHARD)[0]
    assert (shard_chunk.start, shard_chunk.end) == (10, 12)
    members = cp.resolve_calibration_subset_members(plan, c1.archive_of(tree), shard_chunk.chunk_id)
    assert [m.member_name for m in members] == [shard_name(6), shard_name(1)]
    assert [m.canonical_position for m in members] == [10, 11]
    full = cp.canonical_member_sequence(c1.archive_of(tree))
    assert [m.member_name for m in full[12:14]] != [m.member_name for m in members]
    primary = cp.resolve_calibration_subset_members(plan, c1.archive_of(tree), "chunk-0005")
    assert [m.member_name for m in primary] == ["CIK0000000006.json"]
    with pytest.raises(cp.ChunkPlanError, match="is not in this plan"):
        cp.resolve_calibration_subset_members(plan, c1.archive_of(tree), "chunk-0099")
    # Executed: the shard chunk parses exactly those two members, bound to the merged map.
    run = execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    shard_receipt = run["receipts"][-1]
    assert (shard_receipt.region, shard_receipt.start, shard_receipt.end) == ("shard", 10, 12)
    assert shard_receipt.summary.members == 2
    assert shard_receipt.member_order_digest == plan.member_order_digest
    assert shard_receipt.plan_digest == plan.plan_digest
    # The plan copy inside every attempt is the canonical record carrying the four labels.
    copy = json.loads(
        (run["chunk_root"] / "chunk-0000" / "attempt-000" / "chunk_plan.json").read_bytes()
    )
    assert copy["classifications"] == list(LABELS)
    assert copy["contract"] == cp.CALIBRATION_SUBSET_PLAN_CONTRACT


def test_p3_subset_coverage_rules_refuse_every_broken_shape(tmp_path: Path) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    cases: dict[str, dict[str, Any]] = {
        "not exactly the four classes": {
            "excluded_shards_by_class": {**dict(plan.excluded_shards_by_class), "other": 0}
        },
        "do not sum": {"full_shard_members": 5, "full_total_members": 17},
        "closure rule": {"dependency_closure_rule": "filename-only"},
        "classifications are not exactly": {"classifications": LABELS[:3]},
        "PROPER primary prefix": {
            "primary_prefix_members": 12,
            "primary_members": 12,
            "total_members": 14,
            "selected_members": 14,
            "chunk_count": 13,
            "chunks": (
                *cp.partition_regions(primary_members=12, shard_members=0, chunk_members=1),
                cp.ChunkBounds(chunk_id="chunk-0012", region="shard", start=12, end=14),
            ),
        },
        "exactly ONE shard chunk": {
            "chunks": (
                *plan.chunks[:-1],
                replace(plan.chunks[-1], end=11),
                cp.ChunkBounds(chunk_id="chunk-0011", region="shard", start=11, end=12),
            ),
            "chunk_count": 12,
        },
        "is not a SHA-256": {"selected_member_order_digest": "nope"},
        "declares a single-pass cap": {"single_pass_chunk_cap": 3},
    }
    for pattern, changes in cases.items():
        with pytest.raises(cp.ChunkPlanError, match=pattern):
            cp.CalibrationSubsetPlan.from_record(resealed(plan, **changes))


# ==========================================================================
# P4: the exact 34-chunk topology -- M10
# ==========================================================================
def test_p4_m10_the_c29_topology_is_33_primary_chunks_one_shard_chunk_and_9_9_9_6_1(
    tmp_path: Path,
) -> None:
    database, tree = topology_world(tmp_path)
    plan = subset_plan(tree, database, prefix=33, chunk_members=1)
    assert plan.chunk_count == 34
    primaries = cp.chunks_in_region(plan, cp.REGION_PRIMARY)
    shards = cp.chunks_in_region(plan, cp.REGION_SHARD)
    assert len(primaries) == 33 and len(shards) == 1
    assert [(b.start, b.end) for b in primaries] == [(i, i + 1) for i in range(33)]
    assert (shards[0].chunk_id, shards[0].start, shards[0].end) == ("chunk-0033", 33, 38)
    assert (plan.primary_members, plan.shard_members, plan.total_members) == (33, 5, 38)
    assert (plan.full_primary_members, plan.full_shard_members, plan.full_total_members) == (
        34,
        6,
        40,
    )
    assert plan.selected_shard_members == 5 and plan.excluded_shard_members == 1
    assert dict(plan.excluded_shards_by_class)["parent_outside_prefix"] == 1
    schedule = cm.derive_calibration_subset_schedule(plan)
    assert [len(g.chunk_ids) for g in schedule.groups] == [9, 9, 9, 6, 1]
    assert [g.region for g in schedule.groups] == ["primary"] * 4 + ["shard"]
    assert schedule.level_two_inputs == tuple(f"group-{i:04d}" for i in range(5))
    assert schedule.plan_digest == plan.plan_digest
    assert cm.require_sealed_schedule(schedule, plan) == schedule
    # The selected shard count is derived from the source, never assumed: a larger primary chunk
    # keeps ONE shard chunk holding the same five shards.
    wider = subset_plan(tree, database, prefix=33, chunk_members=2)
    assert wider.chunk_count == 18 and cp.chunks_in_region(wider, cp.REGION_SHARD)[0].end == 38
    assert wider.selected_shard_members == 5 and wider.plan_digest != plan.plan_digest
    # A subset plan is multipass-shaped: fewer than ten chunks is refused at construction.
    with pytest.raises(cp.ChunkPlanError, match="admits more than"):
        subset_plan(tree, database, prefix=33, chunk_members=10)


def test_p4_the_full_topology_executes_to_a_five_input_final(tmp_path: Path) -> None:
    database, tree = topology_world(tmp_path)
    plan = subset_plan(tree, database, prefix=33, chunk_members=1)
    run = execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    assert len(run["receipts"]) == 34
    partial = prepared_multipass(run)
    intermediates = merge_groups_in_process(run, partial, database)
    assert [r.group_id for r in intermediates] == [f"group-{i:04d}" for i in range(5)]
    assert [len(r.input_chunk_ids) for r in intermediates] == [9, 9, 9, 6, 1]
    result = finalize_in_process(run, partial, database)
    assert result.intermediate_count == 5 and result.chunk_count == 34
    assert (result.selected_members, result.members, result.full_total_members) == (38, 38, 40)
    assert result.classifications == LABELS
    assert result.world_parser_state == "not_started"
    assert result.parser_state_after == "chunk_local"
    events = sorted(p.name for p in partial["ledger"].iterdir())
    assert events == [
        "admission-final-final.json",
        *[f"admission-group-group-{i:04d}-attempt-000.json" for i in range(5)],
    ]


# ==========================================================================
# P5: separate process capability -- M11, M12, M13
# ==========================================================================
def test_p5_m11_production_entries_and_the_production_bootstrap_refuse_the_subset_plan(
    tmp_path: Path,
) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    run = execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    root = tmp_path / "production"
    assert cm.REAL_MULTIPASS_F0_AUTHORITY is None
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_multipass_f0(
            plan=plan,
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root / "orch",
            run_id="m11",
        )
    partial = prepared_multipass(run)
    group = partial["schedule"].groups[0]
    request, directory = group_request(run, partial, group, database, 0)
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_group_merge(request)
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.merge_group_body(request)
    final = final_request(run, partial, database)
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_final_merge(final)
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.finalize_multipass_body(final)
    request_path = root / "group-request.json"
    root.mkdir()
    write_once_json(request_path, dict(request.as_record()))
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm._child_main(str(request_path))
    # A REAL child under the PRODUCTION bootstrap, which nothing here has patched.
    assert "REAL_MULTIPASS" not in cm._CHILD_BOOTSTRAP
    completed = subprocess.run(
        [sys.executable, "-c", cm._CHILD_BOOTSTRAP, str(request_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0 and AUTHORITY_REFUSAL in completed.stderr
    assert not directory.exists() and not partial["intermediates_root"].exists()
    # The production CHUNK route refuses the subset plan too: the pinned child body reads plans
    # only through the accepted reader, and refuses before its attempt directory exists.
    attempt_directory = run["chunk_root"] / "chunk-0000" / "attempt-007"
    chunk_request = c1x.chunk_request(
        plan_path=run["plan_path"],
        chunk_id="chunk-0000",
        attempt=7,
        attempt_directory=attempt_directory,
        database=database,
        tree=tree,
        repository=c1.PINNED,
    )
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        ce.execute_chunk_body(chunk_request)
    assert not attempt_directory.exists()
    with pytest.raises(ce.ChunkExecutionError, match="never adopts another shape"):
        ce.run_chunk(chunk_request)
    assert not attempt_directory.exists()
    with pytest.raises(cc.ChunkConsolidationError, match="single-pass"):
        cc.consolidate_chunks(
            plan=plan,
            internal_root=run["chunk_root"],
            operational_catalog=database,
            world_directory=root / "single",
            run_id="m11",
        )
    assert not (root / "single").exists()
    # The calibration launchers refuse a plan that is not a subset plan, before anything.
    multipass = c13.multipass_plan(tree, database, chunk_members=1)
    with pytest.raises(cp.ChunkPlanError, match="not a calibration-subset plan"):
        cm.run_calibration_subset_multipass(
            plan=multipass,  # type: ignore[arg-type]
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root / "cal",
            run_id="m11",
            storage_requirements=c13.LEVEL_DISTINCT_REQUIREMENTS,
            instrumentation_ledger=root / "ledger",
        )
    assert not (root / "cal").exists() and not (root / "ledger").exists()


def test_p5_m12_m13_a_calibration_child_refuses_every_wrong_envelope_before_anything_exists(
    tmp_path: Path,
) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    run = execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    partial = prepared_multipass(run)
    group = partial["schedule"].groups[0]
    request, directory = group_request(run, partial, group, database, 0)
    request_path = partial["multipass_root"] / "group-0000-000-request.json"
    write_once_json(request_path, dict(request.as_record()))
    good = issued(
        plan=plan,
        role=ce.CALIBRATION_ROLE_GROUP,
        step_id=group.group_id,
        request_path=request_path,
        ledger=partial["ledger"],
    )
    other_plan = subset_plan(tree, database, prefix=11)
    wrong: dict[str, tuple[ce.CalibrationChildEnvelope, str]] = {
        "contract": (replace(good, contract=cm.CALIBRATION_SUBSET_RESULT_CONTRACT), "refused"),
        "role": (replace(good, role=ce.CALIBRATION_ROLE_CHUNK), "must agree"),
        "step": (replace(good, step_id="group-0001"), "binds step"),
        "plan": (replace(good, plan_digest=other_plan.plan_digest), "binds plan"),
        "request digest": (replace(good, request_sha256="ab" * 32), "digests to"),
        "ceiling": (
            replace(good, selected_member_ceiling=good.selected_member_ceiling - 1),
            "selected-member ceiling",
        ),
        "parent pid": (replace(good, parent_pid=os.getpid() + 100000), "started by"),
    }
    for label, (envelope, needle) in wrong.items():
        completed = spawn_calibration_child(request_path, envelope)
        assert completed.returncode != 0, label
        assert needle in completed.stderr, (label, completed.stderr[-1500:])
        assert not directory.exists(), label
        assert not any(partial["ledger"].iterdir()), label
    # Non-canonical bytes and a missing pipe refuse as well.
    read_end, write_end = os.pipe()
    with os.fdopen(write_end, "wb") as pipe:
        pipe.write(json.dumps(dict(good.as_record()), indent=2).encode("utf-8"))
    completed = subprocess.run(
        [sys.executable, "-c", cm._CALIBRATION_CHILD_BOOTSTRAP, str(request_path), str(read_end)],
        capture_output=True,
        text=True,
        check=False,
        pass_fds=(read_end,),
    )
    os.close(read_end)
    assert completed.returncode != 0 and "canonical bytes" in completed.stderr
    completed = subprocess.run(
        [sys.executable, "-c", cm._CALIBRATION_CHILD_BOOTSTRAP, str(request_path), "not-a-pipe"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0 and "not a pipe number" in completed.stderr
    assert not directory.exists() and not any(partial["ledger"].iterdir())
    # A final-role envelope whose run id is not the request's refuses too.
    final = final_request(run, partial, database, run_id="the-run")
    final_path = partial["multipass_root"] / "final-request.json"
    write_once_json(final_path, dict(final.as_record()))
    stale = issued(
        plan=plan,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="final",
        request_path=final_path,
        run_id="another-run",
        ledger=partial["ledger"],
    )
    completed = spawn_calibration_child(final_path, stale)
    assert completed.returncode != 0 and "binds run" in completed.stderr
    assert not partial["world_directory"].exists() and not any(partial["ledger"].iterdir())
    # Positive control: the matching envelope, same request, same child -> it completes.
    completed = spawn_calibration_child(request_path, good)
    assert completed.returncode == 0, completed.stderr[-3000:]
    receipt = cm.completed_intermediate_receipt(partial["intermediates_root"], group.group_id)
    assert receipt is not None and receipt[0].plan_digest == plan.plan_digest
    event = cm.read_calibration_admission_event(
        cm.calibration_admission_event_path(
            partial["ledger"], role="group", step_id=group.group_id, attempt=0
        )
    )
    assert event.envelope_sha256 == good.sha256 and event.level == ct.MERGE_LEVEL_ONE
    # In-process, the bodies apply the same gate first: nothing is read or created on a wrong
    # role, and a chunk body refuses a group envelope.
    with pytest.raises(ce.ChunkExecutionError, match="refused before anything"):
        cm.merge_calibration_subset_group_body(
            replace(request, attempt=5), replace(good, role="final")
        )
    with pytest.raises(ce.ChunkExecutionError, match="refused before anything"):
        cm.finalize_calibration_subset_body(final, good)
    with pytest.raises(ce.ChunkExecutionError, match="refused before anything"):
        ce.execute_calibration_subset_chunk_body(
            c1x.chunk_request(
                plan_path=run["plan_path"],
                chunk_id="chunk-0000",
                attempt=9,
                attempt_directory=run["chunk_root"] / "chunk-0000" / "attempt-009",
                database=database,
                tree=tree,
                repository=c1.PINNED,
            ),
            good,
        )
    assert not (run["chunk_root"] / "chunk-0000" / "attempt-009").exists()


def test_p5_the_envelope_never_enters_argv_or_the_environment(tmp_path: Path) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    base = tmp_path / "run"
    seen: list[tuple[list[str], dict[str, str]]] = []
    real_run = subprocess.run

    def recording(argv: list[str], **kwargs: Any) -> Any:
        seen.append((list(argv), dict(os.environ)))
        return real_run(argv, **kwargs)

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm.subprocess, "run", recording)
        receipts = cm.run_calibration_subset_chunks(
            plan,
            plan_path=base / "plan.json",
            chunk_root=base / "chunks",
            operational_catalog=database,
            data_root=tree.data_root,
            source_instance_id=c1.INSTANCE,
            run_id="argv",
            batch_size=c13.BATCH,
        )
    children = [(argv, env) for argv, env in seen if argv[0] == sys.executable]
    assert len(receipts) == plan.chunk_count == len(children)
    for argv, environment in children:
        assert argv[0] == sys.executable and argv[1] == "-c"
        assert argv[2] == cm._CALIBRATION_CHILD_BOOTSTRAP
        assert len(argv) == 5 and argv[4].isdigit()
        assert plan.plan_digest not in " ".join(argv)
        assert ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT not in " ".join(argv)
        joined = " ".join(f"{k}={v}" for k, v in environment.items())
        assert ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT not in joined
        assert plan.plan_digest not in joined
    # Restart: every receipt is reused, no child starts.
    seen.clear()
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm.subprocess, "run", recording)
        again = cm.run_calibration_subset_chunks(
            plan,
            plan_path=base / "plan.json",
            chunk_root=base / "chunks",
            operational_catalog=database,
            data_root=tree.data_root,
            source_instance_id=c1.INSTANCE,
            run_id="argv",
            batch_size=c13.BATCH,
        )
    assert [argv for argv, _ in seen if argv[0] == sys.executable] == []
    assert [r.pid for r in again] == [r.pid for r in receipts]


def test_p5_the_calibration_launch_shape_and_gate_order_are_pinned() -> None:
    source = Path(cm.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    ]
    assert len(spawns) == 2
    calibration = [s for s in spawns if any(k.arg == "pass_fds" for k in s.keywords)]
    assert len(calibration) == 1
    argv = calibration[0].args[0]
    assert isinstance(argv, ast.List) and len(argv.elts) == 5
    assert {k.arg for k in calibration[0].keywords} == {
        "check",
        "capture_output",
        "text",
        "timeout",
        "pass_fds",
    }
    assert c13i.subprocess_launches(source)[1] == (
        "<sys.executable>",
        ("-c", c13i.CALIBRATION_MULTIPASS_CHILD_BOOTSTRAP, "str(request_path)", "str(envelope_fd)"),
    )
    assert c13i.capability_violations(source, module="disclosure_drift.m3.chunk_multipass") == []
    assert c13i.environment_accesses(source) == []

    def first_call(name: str) -> str:
        body = functions[name].body
        first = body[1] if isinstance(body[0], ast.Expr) else body[0]
        value = first.value if isinstance(first, ast.Expr | ast.Assign) else None
        assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name), name
        return value.func.id

    assert first_call("_calibration_child_main") == "receive_calibration_envelope"
    for body in ("merge_calibration_subset_group_body", "finalize_calibration_subset_body"):
        assert first_call(body) == "require_calibration_envelope"
        text = inspect.getsource(getattr(cm, body))
        assert (
            text.index("require_calibration_envelope(")
            < text.index("require_envelope_binding(")
            < text.index("_require_expected_binding(")
            < text.index("_admit_merge_step(")
            < text.index("_emit_calibration_admission_event(")
            < text.index(".mkdir(")
        )
        assert "require_real_multipass_authority" not in text
        assert "for row in" not in text
    for launcher in (
        "run_calibration_subset_chunk",
        "run_calibration_subset_chunks",
        "run_calibration_subset_group_merge",
        "run_calibration_subset_final_merge",
        "run_calibration_subset_multipass",
    ):
        assert first_call(launcher) == "require_calibration_subset_plan"
        assert "require_real_multipass_authority" not in inspect.getsource(getattr(cm, launcher))
    # The chunk body: the calibration gate first, then the measured identity, then mkdir.
    execution = Path(ce.__file__).read_text(encoding="utf-8")
    chunk = inspect.getsource(ce.execute_calibration_subset_chunk_body)
    assert (
        chunk.index("require_calibration_envelope(")
        < chunk.index("authenticate_running_repository(")
        < chunk.index("require_envelope_binding(")
        < chunk.index(".mkdir(")
    )
    # The calibration binding is measured through the accepted guard with ONE argument: the
    # charged path. Never a provider, an environment mapping, a request field or a claim.
    guard_calls = [
        node
        for node in ast.walk(ast.parse(execution))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_sqlite_temp_binding"
    ]
    assert len(guard_calls) == 1
    assert not guard_calls[0].args
    assert {k.arg for k in guard_calls[0].keywords} == {"charged_path"}
    # The finalizer that never writes a canonical terminal names none of them.
    final = inspect.getsource(cm.finalize_calibration_subset_body)
    for terminal in (
        "mark_parsed(",
        "write_phase_checkpoint(",
        "FINAL_WORLD_RECEIPT",
        "SET parser_state",
    ):
        assert terminal not in final, terminal
    assert "require_f0_success(" in final and "_plan_first_witness_counters(" in final


# ==========================================================================
# P6 + P7: the real-process run -- isolation (M14) and the child-produced event (M15, M16)
# ==========================================================================
def test_p6_p7_m14_m15_m16_a_real_calibration_run_is_isolated_and_the_final_child_reports_level_two(
    tmp_path: Path,
) -> None:
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    base = tmp_path / "run"
    events: list[str] = []
    receipts = cm.run_calibration_subset_chunks(
        plan,
        plan_path=base / "plan.json",
        chunk_root=base / "chunks",
        operational_catalog=database,
        data_root=tree.data_root,
        source_instance_id=c1.INSTANCE,
        run_id="real",
        batch_size=c13.BATCH,
        observe=events.append,
    )
    assert len(receipts) == 11 and os.getpid() not in {r.pid for r in receipts}
    assert len({r.pid for r in receipts}) == 11
    ledger = base / "ledger"
    orchestrate: dict[str, Any] = {
        "plan": plan,
        "internal_root": base / "chunks",
        "operational_catalog": database,
        "multipass_root": base / "multipass",
        "run_id": "real",
        "storage_requirements": c13.LEVEL_DISTINCT_REQUIREMENTS,
        "instrumentation_ledger": ledger,
    }

    # R5: an INTERRUPTED supervisor -- every level-1 merge completes, the final never starts.
    def interrupted(*_args: Any, **_kwargs: Any) -> Any:
        message = "simulated supervisor interruption before the final child"
        raise cm.ChunkMultipassError(message)

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm, "run_calibration_subset_final_merge", interrupted)
        with pytest.raises(cm.ChunkMultipassError, match="simulated"):
            cm.run_calibration_subset_multipass(**orchestrate, observe=events.append)
    assert events == ["CALIBRATION_PROCESS_START", "CALIBRATION_PROCESS_EXIT"] * 14
    assert not (base / "multipass" / "final").exists()
    first_events = sorted(p.name for p in ledger.iterdir())
    assert len(first_events) == 3
    # The RESUMED supervisor revalidates the durable plan, schedule and storage plan, reuses
    # every completed intermediate -- no level-1 child starts -- and issues a fresh envelope
    # for the one remaining step.
    result = cm.run_calibration_subset_multipass(**orchestrate, observe=events.append)
    assert events == ["CALIBRATION_PROCESS_START", "CALIBRATION_PROCESS_EXIT"] * 15
    assert result.merge_pids == ()
    assert [len(g.chunk_ids) for g in result.schedule.groups] == [9, 1, 1]
    merge_pids = tuple(receipt.pid for receipt in result.intermediates)
    assert len(set(merge_pids)) == 3 and os.getpid() not in merge_pids
    for pid in (*merge_pids, result.result.pid):
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    final = result.result
    # P6 / M14: no canonical terminal of any kind.
    world = result.world_directory
    assert not (world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert (world / cm.CALIBRATION_SUBSET_RESULT_FILENAME).exists()
    progress = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(progress, PHASE_F0) is None
        recorded = progress.progress(c1.INSTANCE)
        assert recorded is not None and recorded.state == "in_progress"
    finally:
        progress.close()
    with connect(world / WORKING_CATALOG_FILENAME, writer=False) as connection:
        row = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (c1.INSTANCE,),
        ).fetchone()
    assert row["parser_state"] == "not_started" == final.world_parser_state
    assert final.parser_state_after == "chunk_local" and final.run_outcome == "completed"
    assert (
        final.classifications == LABELS and final.contract == cm.CALIBRATION_SUBSET_RESULT_CONTRACT
    )
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(
            world / cm.CALIBRATION_SUBSET_RESULT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )
    with pytest.raises(ChunkEvidenceError, match="no receipt exists"):
        read_receipt_document(
            world / FINAL_WORLD_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )
    with pytest.raises(cm.ChunkMultipassError):
        cm.IntermediateReceipt.from_record(dict(final.as_record()))
    reread = cm.read_calibration_subset_result(world / cm.CALIBRATION_SUBSET_RESULT_FILENAME)
    assert reread == final and reread.identity() == final.result_identity
    assert (final.selected_members, final.members, final.full_total_members) == (12, 12, 15)
    assert final.member_order_digest == plan.member_order_digest
    assert final.selected_member_order_digest == plan.selected_member_order_digest
    assert final.shard_parent_binding_digest == plan.shard_parent_binding_digest
    # The plan copies in every intermediate and in the multipass root carry the four labels.
    for copy in (
        base / "multipass" / cm.CHUNK_PLAN_FILENAME,
        *(
            base
            / "multipass"
            / "intermediates"
            / g.group_id
            / "attempt-000"
            / cm.CHUNK_PLAN_FILENAME
            for g in result.schedule.groups
        ),
    ):
        assert json.loads(copy.read_bytes())["classifications"] == list(LABELS)
        assert copy.read_bytes() == cp.canonical_json_bytes(dict(plan.as_record()))
    # P7 / M15: the FINAL child charged level two, with the level-two allowance, exactly.
    event = cm.read_calibration_admission_event(
        cm.calibration_admission_event_path(ledger, role="final", step_id="final", attempt=None)
    )
    assert event.level == ct.MERGE_LEVEL_TWO
    assert event.transient_bytes == c13.LEVEL_TWO_TRANSIENT_SENTINEL
    assert event.transient_bytes != c13.LEVEL_ONE_TRANSIENT_SENTINEL
    assert (
        event.required_free_bytes == event.peak_bytes + event.reserve_bytes + event.transient_bytes
    )
    assert event.free_before_bytes >= event.required_free_bytes and event.admitted
    assert dict(final.storage_admission) == {
        "step": "final",
        "level": ct.MERGE_LEVEL_TWO,
        "free_bytes": event.free_before_bytes,
        "required_free_bytes": event.required_free_bytes,
        "peak_bytes": event.peak_bytes,
        "reserve_bytes": event.reserve_bytes,
        "transient_bytes": event.transient_bytes,
        "admitted": True,
    }
    # M16: child-produced, bound and create-once -- never the parent's.
    assert event.child_pid == final.pid != os.getpid()
    assert event.event_identity == final.admission_event_identity
    assert event.envelope_sha256 == final.envelope_sha256
    assert event.run_id == "real" and event.plan_digest == plan.plan_digest
    assert event.classifications == LABELS
    assert event.sqlite_temp_binding_identity == cm.stable_binding_identity(
        result.storage_plan.sqlite_temp_binding
    )
    with pytest.raises(ce.ChunkExecutionError, match="create-once"):
        ce.write_once_canonical_json(
            cm.calibration_admission_event_path(
                ledger, role="final", step_id="final", attempt=None
            ),
            dict(event.as_record()),
        )
    for group in result.schedule.groups:
        level_one = cm.read_calibration_admission_event(
            cm.calibration_admission_event_path(
                ledger, role="group", step_id=group.group_id, attempt=0
            )
        )
        assert level_one.level == ct.MERGE_LEVEL_ONE
        assert level_one.transient_bytes == c13.LEVEL_ONE_TRANSIENT_SENTINEL
        assert level_one.child_pid in merge_pids
    # A tampered event refuses on its identity, its arithmetic and its kind.
    record = dict(event.as_record())
    with pytest.raises(cm.ChunkMultipassError, match="does not describe"):
        cm.CalibrationAdmissionEvent.from_record({**record, "level": ct.MERGE_LEVEL_ONE})
    forged = {**record, "level": ct.MERGE_LEVEL_ONE}
    forged["event_identity"] = cm._record_identity(forged, "event_identity")
    assert (
        cm.CalibrationAdmissionEvent.from_record(forged).event_identity
        != final.admission_event_identity
    )
    with pytest.raises(cm.ChunkMultipassError, match="is exact"):
        cm.CalibrationAdmissionEvent.from_record({k: v for k, v in record.items() if k != "level"})
    # A COMPLETED run is never re-run under its root: the final request document is create-once
    # and refuses before any child starts, exactly as the production orchestrator's does.
    with pytest.raises(ChunkEvidenceError, match="already exists"):
        cm.run_calibration_subset_multipass(**orchestrate)
    assert sorted(p.name for p in ledger.iterdir()) == [
        "admission-final-final.json",
        *first_events,
    ]


def test_p7_m16_a_final_child_refused_at_its_binding_emits_no_event_and_no_world(
    tmp_path: Path,
) -> None:
    """The event comes AFTER validation: a child whose measured binding differs leaves nothing."""
    database, tree = small_world(tmp_path)
    plan = subset_plan(tree, database, prefix=10)
    run = execute_chunks_in_process(plan, tmp_path / "run", database, tree)
    partial = prepared_multipass(run)
    merge_groups_in_process(run, partial, database)
    final = final_request(run, partial, database, run_id="binding")
    final_path = partial["multipass_root"] / "final-request.json"
    write_once_json(final_path, dict(final.as_record()))
    envelope = issued(
        plan=plan,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="final",
        request_path=final_path,
        run_id="binding",
        ledger=partial["ledger"],
    )
    for name in list(partial["ledger"].iterdir()):
        name.unlink()  # the in-process group events; the final event is what is proved absent
    mismatching = cm._CALIBRATION_CHILD_BOOTSTRAP.replace(
        f"volume_uuid={c13.SYNTHETIC_MERGE_VOLUME!r}",
        f"volume_uuid=({'00000000-0000-0000-0000-00000C27R1FF'!r} if 'sqlite-temp' in str(path) "
        f"else {c13.SYNTHETIC_MERGE_VOLUME!r})",
    )
    assert mismatching != cm._CALIBRATION_CHILD_BOOTSTRAP
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cm, "_CALIBRATION_CHILD_BOOTSTRAP", mismatching)
        completed = spawn_calibration_child(final_path, envelope)
    assert completed.returncode != 0
    assert (
        "refused BEFORE any world" in completed.stderr or "not the one this" in completed.stderr
    ), completed.stderr[-2000:]
    assert not partial["world_directory"].exists()
    assert list(partial["ledger"].iterdir()) == []
    # A ledger inside the charged directory, or absent, refuses before the world exists too.
    inside = issued(
        plan=plan,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="final",
        request_path=final_path,
        run_id="binding",
        ledger=partial["world_directory"] / "ledger",
    )
    with pytest.raises(cm.ChunkMultipassError, match="existing directory"):
        cm.finalize_calibration_subset_body(final, inside)
    assert not partial["world_directory"].exists()
    with pytest.raises(cm.ChunkMultipassError, match="needs an instrumentation ledger"):
        cm.finalize_calibration_subset_body(final, replace(envelope, instrumentation_ledger=None))
    assert not partial["world_directory"].exists()
    # Positive control: the accepted child, same request, same envelope -> result and event.
    completed = spawn_calibration_child(final_path, envelope)
    assert completed.returncode == 0, completed.stderr[-3000:]
    event = cm.read_calibration_admission_event(
        cm.calibration_admission_event_path(
            partial["ledger"], role="final", step_id="final", attempt=None
        )
    )
    result = cm.read_calibration_subset_result(
        partial["world_directory"] / cm.CALIBRATION_SUBSET_RESULT_FILENAME
    )
    assert event.level == ct.MERGE_LEVEL_TWO and event.child_pid == result.pid != os.getpid()
    assert event.transient_bytes == c13.LEVEL_TWO_TRANSIENT_SENTINEL


# ==========================================================================
# P9: prior invariants -- every closed value stays closed; the family sets are unchanged
# ==========================================================================
def test_p9_every_production_value_stays_closed_and_no_new_module_joined_the_family() -> None:
    for module, name in (
        (ce, "REAL_CHUNKED_F0_EXECUTION_AUTHORITY"),
        (cm, "REAL_MULTIPASS_F0_AUTHORITY"),
        (cp, "PRODUCTION_CHUNK_MEMBERS"),
        (ct, "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES"),
        (ct, "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES"),
        (ct, "PRODUCTION_SPILL_POLICY"),
        (ct, "QUALIFIED_EXTERNAL_TIER"),
    ):
        assert getattr(module, name) is None, name
        assert c13i.committed_literal(module, name) is None, name
    assert not hasattr(ct, "MULTIPASS_TRANSIENT_BYTES")
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()
    assert "NOT AUTHORIZED" in c13i.refusal_in_a_fresh_interpreter()
    for module in (cp, cm, ct, ce):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        for node in tree.body:
            value = getattr(node, "value", None)
            assert not (isinstance(value, ast.Constant) and value.value == 30000), module.__name__
    package_root = Path(cm.__file__).parent
    stems = sorted(path.stem for path in package_root.glob("chunk_*.py"))
    assert stems == [
        "chunk_consolidation",
        "chunk_evidence",
        "chunk_execution",
        "chunk_multipass",
        "chunk_plan",
        "chunk_storage",
        "chunk_tiering",
        "chunk_transfer",
    ]
    for name in ("build_calibration_chunk_plan", "DISCLOSURE_DRIFT", "external_working_root"):
        assert name not in Path(cm.__file__).read_text(encoding="utf-8"), name
