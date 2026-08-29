"""D151-C13: the canonical multipass plan contract, its merge schedule, and C11-MINOR-1.

Three plan families now exist and this module proves they cannot be confused. The ordinary
``m3.3-chunked-f0-plan/2`` and calibration-only ``m3.3-chunked-f0-calibration-plan/1`` identities
are byte-exact what they were -- pinned by the D151-C10 golden vectors and by fresh builds over the
hostile synthetic world -- and the new ``m3.3-chunked-f0-multipass-plan/1`` is a third sealed
identity over the same partition arithmetic: ten to thirty-four chunks, held to exactly this
build's single-pass cap, relabellable in no direction after sealing.

The merge schedule is derived from the sealed plan and never accepted as input: contiguous,
region-homogeneous groups of at most nine, sealed under their own digest, re-derived and compared
at every consumption. The real thirty-thousand-member partition -- thirty-three primary chunks and
one shard chunk -- is proved from its region counts to schedule as ``9 / 9 / 9 / 6`` plus one.

This module also carries the shared in-process drivers every other C13 module uses, beside the
D151-C1 pin: chunk execution through the accepted chunk body, and the two multipass merge bodies
called directly. The process-boundary proofs live in ``test_d151_c13_intermediates``. Since
D151-C15 every world-creating multipass entry requires the real multipass authority FIRST, so the
drivers run under :func:`open_synthetic_multipass` -- a test-only monkeypatch of the authority
literal and of the storage-term derivation, applied by each C13 module's fixture; the committed
literal stays ``None`` and ``test_d151_c15_corrections`` proves every entry refuses against it.
"""

from __future__ import annotations

import ast
import inspect
import json
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c10_calibration_plan_width as c10  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_DECLARATIONS_FILENAME,
    write_once_json,
)
from disclosure_drift.paths import DataTree  # noqa: E402

# ==========================================================================
# Frozen facts and golden vectors
# ==========================================================================
#: The multipass plan digest over FIXED fields -- nine primaries and three shards, one member per
#: chunk, twelve chunks -- measured when this record introduced the contract. Pure JSON plus
#: SHA-256, so it is deterministic on every host and moves if a digest input is added, removed,
#: renamed or reordered.
GOLDEN_MULTIPASS_PLAN_DIGEST = "a0e65219963e903c81411a7900c8488c92c6eb7621b846566decb4a1d70104d7"

#: The merge schedule digest that fixed multipass plan implies.
GOLDEN_MERGE_SCHEDULE_DIGEST = "f3e86fdd522c1ef06fabeb21c4267e55f052e9e3e4115ea432d0f7f89902970a"

#: Explicit, synthetic storage terms for every in-process merge: nothing is reserved, a merge
#: world is projected at exactly its inputs, and no transient allowance -- the seam D151-C13 §20
#: permits a synthetic test to inject. Never a production value; production terms are ``None``.
REQUIREMENTS = ct.MultipassStorageRequirements(
    internal_reserve_bytes=0,
    level_one_peak_ratio=1.0,
    level_two_peak_ratio=1.0,
    level_one_transient_bytes=0,
    level_two_transient_bytes=0,
)

#: Two distinct, nonzero, TEST-ONLY transient sentinels -- D151-C24-R2. :data:`REQUIREMENTS`
#: charges both levels zero, which is right for every proof that is not about the levels but
#: makes the two indistinguishable: the orchestrator could charge a level-1 group at level 2, or
#: the finalization at level 1, and no assertion would move. These two do move. They are not
#: production values and appear nowhere in production source; the production terms stay ``None``.
LEVEL_ONE_TRANSIENT_SENTINEL = 1_048_576
LEVEL_TWO_TRANSIENT_SENTINEL = 3_145_728

#: The same synthetic terms as :data:`REQUIREMENTS` except that the two levels are told apart.
LEVEL_DISTINCT_REQUIREMENTS = ct.MultipassStorageRequirements(
    internal_reserve_bytes=0,
    level_one_peak_ratio=1.0,
    level_two_peak_ratio=1.0,
    level_one_transient_bytes=LEVEL_ONE_TRANSIENT_SENTINEL,
    level_two_transient_bytes=LEVEL_TWO_TRANSIENT_SENTINEL,
)

#: The one volume identity every synthetic merge measures for both its world and its SQLite
#: temporary root -- D151-C17 §15. Substituting the provider is THE accepted seam; no test in
#: this repository may depend on the host's real volume layout, and production compares measured
#: identities either way.
SYNTHETIC_MERGE_VOLUME = "00000000-0000-0000-0000-00000C170000"


#: An inert, shape-valid binding record for requests built only to be refused BEFORE the binding
#: is consulted (the authority-first proofs run with no temporary root stated). Device and inode
#: ``0`` name no directory a child could measure, so a body that DID reach the comparison refuses.
INERT_BINDING_RECORD: dict[str, object] = dict(
    ct.SqliteTempBinding(
        temp_root_device=0,
        temp_root_inode=0,
        temp_volume_uuid=SYNTHETIC_MERGE_VOLUME,
        temp_filesystem_type="apfs",
        temp_device_identifier="disk-synthetic",
        charged_volume_uuid=SYNTHETIC_MERGE_VOLUME,
        charged_filesystem_type="apfs",
        charged_device_identifier="disk-synthetic",
    ).as_record()
)


def synthetic_expected_binding(charged_path: Path) -> dict[str, object]:
    """The binding a synthetic request carries -- D151-C19 R4.

    MEASURED now, in this process, through the same provider seam the merge child will use:
    exactly what ``run_multipass_f0`` does before it writes a request. With no usable temporary
    root stated the inert record is returned, for requests that exist only to be refused earlier.
    """
    try:
        return dict(ct.require_sqlite_temp_binding(charged_path=charged_path).as_record())
    except ct.ChunkTieringError:
        return dict(INERT_BINDING_RECORD)


def synthetic_volume_provider(uuid: str = SYNTHETIC_MERGE_VOLUME) -> Any:
    """A :data:`VolumeIdentityProvider` that reports ``uuid`` for every path."""

    def identify(path: Path) -> ewr.VolumeIdentity:
        return ewr.VolumeIdentity(
            volume_uuid=uuid,
            mount_point=Path("/"),
            filesystem_type="apfs",
            device_identifier="disk-synthetic",
        )

    return identify


#: The token every SYNTHETIC in-process merge runs under. Test-only, never a production value:
#: the committed ``REAL_MULTIPASS_F0_AUTHORITY`` is ``None``, and a merge CHILD is opened
#: separately through its bootstrap (``test_d151_c13_intermediates.multipass_child_bootstrap``).
SYNTHETIC_AUTHORITY = "synthetic-multipass-authority/test-only"

BATCH = 2


def open_synthetic_multipass(
    patcher: pytest.MonkeyPatch,
    *,
    temp_root: Path,
    requirements: ct.MultipassStorageRequirements = REQUIREMENTS,
    volume_uuid: str = SYNTHETIC_MERGE_VOLUME,
) -> None:
    """Open the multipass gates for synthetic execution, in THIS process only -- D151-C15 §8.

    Four names are redirected, all in test code and none of them a production surface:

    * the authority literal, to the synthetic token (D151-C15 R2);
    * the accepted storage-term derivation, to explicit synthetic terms -- the seam D151-C15 §9
      removed from the production signature;
    * ``SQLITE_TMPDIR``, to a created directory, because since D151-C17 R6 production refuses a
      merge whose temporary root is not stated;
    * the accepted volume-identity provider, to one that reports a single synthetic identity for
      every path -- the seam :data:`VolumeIdentityProvider` exists for. Production still COMPARES
      two measured identities; only the measurement is substituted, so the positive path is
      exercised here rather than depending on the host's real volume layout.

    Nothing in production reads any of these as a bypass: there is no flag, Boolean, request
    field or configuration key that skips either gate.
    """
    patcher.setattr(cm, "REAL_MULTIPASS_F0_AUTHORITY", SYNTHETIC_AUTHORITY)
    patcher.setattr(cm, "accepted_multipass_storage_requirements", lambda: requirements)
    temp_root.mkdir(parents=True, exist_ok=True)
    patcher.setenv(ewr.SQLITE_TMPDIR_ENV, str(temp_root))
    patcher.setattr(ewr, "macos_volume_identity", synthetic_volume_provider(volume_uuid))


def chunk_directories(run: dict[str, Any]) -> list[Path]:
    """Every chunk attempt directory of one executed run, in plan order."""
    return [
        run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
        for receipt in run["receipts"]
    ]


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin, through the accepted identity seam -- see ``test_d151_c1_chunk_plan``."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared drivers
# ==========================================================================
def world(tmp_path: Path, *, members: int, shards: int, **kwargs: Any) -> tuple[Path, DataTree]:
    """A synthetic world holding exactly ``members + shards`` governed members."""
    kwargs.setdefault("filings", 1)
    return c1.build_world(tmp_path, members=members, shards=shards, **kwargs)


def multipass_plan(tree: DataTree, database: Path, *, chunk_members: int) -> cp.ChunkPlan:
    """One multipass plan over this world's archive, at a caller-chosen partition size."""
    observation = c1.observation_of(tree, database)
    return cp.build_multipass_chunk_plan(
        archive_path=c1.archive_of(tree),
        source_instance_id=c1.INSTANCE,
        source_observation_id=c1.OBSERVATION,
        source_id=c1.SOURCE_ID,
        source_sha256=observation.logical_sha256,
        source_byte_length=observation.content_size_bytes,
        chunk_members=chunk_members,
    )


def execute_in_process(
    plan: cp.ChunkPlan,
    base: Path,
    database: Path,
    tree: DataTree,
    *,
    batch_size: int = BATCH,
) -> dict[str, Any]:
    """Execute every chunk of ``plan`` through the accepted chunk body, in THIS process.

    The semantic oracles do not depend on the process boundary, and the accepted chunk body run
    in-process is the same parse, the same writer and the same receipt as the child runs. The
    parent-map barrier is applied exactly as ``run_chunked_f0`` applies it.
    """
    base.mkdir(parents=True)
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
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
        receipts.append(
            ce.execute_chunk_body(
                c1x.chunk_request(
                    plan_path=plan_path,
                    chunk_id=bounds.chunk_id,
                    attempt=attempt,
                    attempt_directory=attempt_directory,
                    database=database,
                    tree=tree,
                    parent_map_path=parent_map_path,
                    batch_size=batch_size,
                    repository=c1.PINNED,
                )
            )
        )
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


def group_request(
    run: dict[str, Any],
    *,
    schedule_path: Path,
    group_id: str,
    attempt: int,
    attempt_directory: Path,
    database: Path,
    requirements: ct.MultipassStorageRequirements = REQUIREMENTS,
    external_root: Path | None = None,
    expected_binding: Mapping[str, object] | None = None,
) -> cm.GroupMergeRequest:
    assert c1.PINNED is not None
    return cm.GroupMergeRequest(
        plan_path=str(run["plan_path"]),
        schedule_path=str(schedule_path),
        group_id=group_id,
        attempt=attempt,
        attempt_directory=str(attempt_directory),
        internal_root=str(run["chunk_root"]),
        external_root=None if external_root is None else str(external_root),
        operational_catalog=str(database),
        cache_bytes=None,
        repository_head_sha=c1.PINNED.head_sha,
        repository_tree_sha=c1.PINNED.tree_sha,
        storage_requirements=dict(requirements.as_record()),
        expected_sqlite_temp_binding=(
            synthetic_expected_binding(attempt_directory)
            if expected_binding is None
            else dict(expected_binding)
        ),
    )


def final_request(
    run: dict[str, Any],
    *,
    schedule_path: Path,
    intermediates_root: Path,
    world_directory: Path,
    database: Path,
    run_id: str = "c13-run",
    requirements: ct.MultipassStorageRequirements = REQUIREMENTS,
    external_root: Path | None = None,
    expected_binding: Mapping[str, object] | None = None,
) -> cm.FinalMergeRequest:
    assert c1.PINNED is not None
    return cm.FinalMergeRequest(
        plan_path=str(run["plan_path"]),
        schedule_path=str(schedule_path),
        intermediates_root=str(intermediates_root),
        internal_root=str(run["chunk_root"]),
        external_root=None if external_root is None else str(external_root),
        operational_catalog=str(database),
        world_directory=str(world_directory),
        run_id=run_id,
        cache_bytes=None,
        repository_head_sha=c1.PINNED.head_sha,
        repository_tree_sha=c1.PINNED.tree_sha,
        storage_requirements=dict(requirements.as_record()),
        expected_sqlite_temp_binding=(
            synthetic_expected_binding(world_directory)
            if expected_binding is None
            else dict(expected_binding)
        ),
    )


def merge_in_process(
    run: dict[str, Any],
    database: Path,
    *,
    label: str = "multipass",
    run_id: str = "c13-run",
    requirements: ct.MultipassStorageRequirements = REQUIREMENTS,
    finalize: bool = True,
) -> dict[str, Any]:
    """Every level-1 merge and the level-2 finalization, called directly in THIS process."""
    plan = run["plan"]
    schedule = cm.derive_merge_schedule(plan)
    multipass_root = run["base"] / label
    multipass_root.mkdir()
    schedule_path = multipass_root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    intermediates_root = multipass_root / "intermediates"
    intermediates = []
    for group in schedule.groups:
        attempt_directory, attempt = cm.next_intermediate_attempt_directory(
            intermediates_root, group.group_id
        )
        intermediates.append(
            cm.merge_group_body(
                group_request(
                    run,
                    schedule_path=schedule_path,
                    group_id=group.group_id,
                    attempt=attempt,
                    attempt_directory=attempt_directory,
                    database=database,
                    requirements=requirements,
                )
            )
        )
    result: dict[str, Any] = {
        "schedule": schedule,
        "schedule_path": schedule_path,
        "multipass_root": multipass_root,
        "intermediates_root": intermediates_root,
        "intermediates": intermediates,
        "world_directory": multipass_root / "final",
    }
    if finalize:
        result["final"] = cm.finalize_multipass_body(
            final_request(
                run,
                schedule_path=schedule_path,
                intermediates_root=intermediates_root,
                world_directory=multipass_root / "final",
                database=database,
                run_id=run_id,
                requirements=requirements,
            )
        )
    return result


def _fixed_multipass_plan() -> cp.ChunkPlan:
    """A multipass plan over fixed fields -- the digest algorithm's own test vector."""
    bounds = cp.partition_regions(primary_members=9, shard_members=3, chunk_members=1)
    plan = replace(
        c10._fixed_ordinary_plan(),
        contract=cp.MULTIPASS_PLAN_CONTRACT,
        total_members=12,
        primary_members=9,
        shard_members=3,
        chunk_members=1,
        chunk_count=12,
        chunks=bounds,
        plan_digest="",
    )
    return replace(plan, plan_digest=cp._plan_digest(plan))


def _resealed(plan: cp.ChunkPlan, **changes: Any) -> dict[str, object]:
    """A tampered plan whose digest is recomputed, so only a rule can catch it."""
    tampered = replace(plan, **changes, plan_digest="")
    record = dict(tampered.as_record())
    record["plan_digest"] = cp._plan_digest(tampered)
    return record


def _resealed_schedule(schedule: cm.MergeSchedule, **changes: Any) -> cm.MergeSchedule:
    tampered = replace(schedule, **changes, schedule_digest="")
    return replace(tampered, schedule_digest=cm._schedule_digest(tampered))


def _names(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


# ==========================================================================
# P01-P03: the three contracts, their literals, and their golden vectors
# ==========================================================================
def test_p01_the_contract_literals_are_frozen_together() -> None:
    assert cp.MULTIPASS_PLAN_CONTRACT == "m3.3-chunked-f0-multipass-plan/1"
    assert cp.MULTIPASS_CHUNK_FLOOR == 10 == cp.SINGLE_PASS_CHUNK_CAP + 1
    assert cp.MULTIPASS_CHUNK_CEILING == 34 == cp.CALIBRATION_CHUNK_CEILING
    assert cp.CHUNK_PLAN_CONTRACT == "m3.3-chunked-f0-plan/2"
    assert cp.CALIBRATION_PLAN_CONTRACT == "m3.3-chunked-f0-calibration-plan/1"
    assert cp.SINGLE_PASS_CHUNK_CAP == 9 == cm.MERGE_FAN_IN
    assert cm.MERGE_SCHEDULE_CONTRACT == "m3.3-chunked-f0-merge-schedule/1"
    assert cm.INTERMEDIATE_RECEIPT_CONTRACT == "m3.3-chunked-f0-intermediate-receipt/1"
    assert cm.MULTIPASS_CONSOLIDATION_CONTRACT == "m3.3-chunked-f0-multipass-consolidation/1"
    assert (
        len({cp.CHUNK_PLAN_CONTRACT, cp.CALIBRATION_PLAN_CONTRACT, cp.MULTIPASS_PLAN_CONTRACT}) == 3
    )
    for name in (
        "MULTIPASS_CHUNK_CEILING",
        "MULTIPASS_CHUNK_FLOOR",
        "MULTIPASS_PLAN_CONTRACT",
        "build_multipass_chunk_plan",
    ):
        assert name in cp.__all__, name
    assert cp.PRODUCTION_CHUNK_MEMBERS is None


def test_p02_the_ordinary_and_calibration_identities_are_byte_exact(tmp_path: Path) -> None:
    """The D151-C10 golden vectors still hold, and the record keys gained nothing."""
    ordinary = c10._fixed_ordinary_plan()
    assert ordinary.plan_digest == c10.GOLDEN_ORDINARY_PLAN_DIGEST
    assert set(ordinary.as_record()) == c10.ORDINARY_RECORD_KEYS
    assert cp.compute_member_order_digest(c10.FIXED_MEMBERS) == c10.GOLDEN_MEMBER_ORDER_DIGEST
    assert "multipass" not in json.dumps(dict(ordinary.as_record()))
    database, tree = world(tmp_path, members=33, shards=1)
    calibration = c10.calibration_plan(tree, database, chunk_members=1)
    assert calibration.contract == cp.CALIBRATION_PLAN_CONTRACT
    assert calibration.chunk_count == 34
    assert set(calibration.as_record()) == c10.ORDINARY_RECORD_KEYS
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(calibration.as_record())))) == (
        calibration
    )
    assert calibration.multipass is False and calibration.calibration_only is True
    assert ordinary.multipass is False and ordinary.calibration_only is False


def test_p03_the_multipass_golden_vector_and_round_trip() -> None:
    plan = _fixed_multipass_plan()
    assert plan.plan_digest == GOLDEN_MULTIPASS_PLAN_DIGEST
    assert set(plan.as_record()) == c10.ORDINARY_RECORD_KEYS
    assert plan.multipass is True and plan.calibration_only is False
    assert cp.require_sealed_plan(plan) is plan
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record())))) == plan
    schedule = cm.derive_merge_schedule(plan)
    assert schedule.schedule_digest == GOLDEN_MERGE_SCHEDULE_DIGEST
    assert cm.MergeSchedule.from_record(json.loads(json.dumps(dict(schedule.as_record())))) == (
        schedule
    )
    # Three contracts over the same partition are three distinct sealed identities.
    twins = {
        cp._plan_digest(replace(plan, contract=contract))
        for contract in (cp.CHUNK_PLAN_CONTRACT, cp.CALIBRATION_PLAN_CONTRACT, plan.contract)
    }
    assert len(twins) == 3


# ==========================================================================
# P04-P06, A07, A08: the width rules
# ==========================================================================
def test_p04_a07_nine_chunks_is_not_a_multipass_plan(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=6, shards=3)
    before = _names(tmp_path)
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        multipass_plan(tree, database, chunk_members=1)
    assert _names(tmp_path) == before
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        cp.ChunkPlan.from_record(
            _resealed(c10._fixed_ordinary_plan(), contract=cp.MULTIPASS_PLAN_CONTRACT)
        )


def test_p04_ten_chunks_is_the_floor_and_is_admitted(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=9, shards=1)
    plan = multipass_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 10 == cp.MULTIPASS_CHUNK_FLOOR
    assert plan.multipass
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record())))) == plan


def test_p05_a08_thirty_five_chunks_are_refused_and_thirty_four_admitted(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=34, shards=1)
    before = _names(tmp_path)
    with pytest.raises(cp.ChunkPlanError, match="MULTIPASS_CHUNK_CEILING = 34"):
        multipass_plan(tree, database, chunk_members=1)
    assert _names(tmp_path) == before
    forged = replace(
        _fixed_multipass_plan(),
        total_members=35,
        primary_members=34,
        shard_members=1,
        chunk_count=35,
        chunks=cp.partition_regions(primary_members=34, shard_members=1, chunk_members=1),
    )
    with pytest.raises(cp.ChunkPlanError, match="MULTIPASS_CHUNK_CEILING = 34"):
        cp.ChunkPlan.from_record(_resealed(forged))
    wide_database, wide_tree = world(tmp_path / "wide", members=33, shards=1)
    plan = multipass_plan(wide_tree, wide_database, chunk_members=1)
    assert plan.chunk_count == 34 == cp.MULTIPASS_CHUNK_CEILING


def test_p06_a_multipass_plan_is_held_to_exactly_this_builds_cap() -> None:
    """A lowered declared cap is refused as firmly as a raised one -- the C11 hole, closed here."""
    plan = _fixed_multipass_plan()
    with pytest.raises(cp.ChunkPlanError, match="held to the constant"):
        cp.ChunkPlan.from_record(_resealed(plan, single_pass_chunk_cap=3))
    with pytest.raises(cp.ChunkPlanError, match="never a permission to exceed"):
        cp.ChunkPlan.from_record(_resealed(plan, single_pass_chunk_cap=34))
    record = dict(plan.as_record())
    record["single_pass_chunk_cap"] = 3
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)


# ==========================================================================
# A01-A06: no relabelling in any direction
# ==========================================================================
def test_a01_a02_an_ordinary_plan_cannot_become_calibration_or_multipass(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=6, shards=3)
    plan = c1.build_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 9
    for contract in (cp.CALIBRATION_PLAN_CONTRACT, cp.MULTIPASS_PLAN_CONTRACT):
        record = dict(plan.as_record())
        record["contract"] = contract
        with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
            cp.ChunkPlan.from_record(record)
        with pytest.raises(cp.ChunkPlanError, match="built as one"):
            cp.ChunkPlan.from_record(_resealed(plan, contract=contract))


def test_a03_a19_a_calibration_plan_relabelled_multipass_is_a_different_identity(
    tmp_path: Path,
) -> None:
    """Unresealed: the digest refuses. Resealed: a NEW identity no calibration chunk binds."""
    database, tree = world(tmp_path, members=33, shards=1)
    calibration = c10.calibration_plan(tree, database, chunk_members=1)
    record = dict(calibration.as_record())
    record["contract"] = cp.MULTIPASS_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    resealed = cp.ChunkPlan.from_record(_resealed(calibration, contract=cp.MULTIPASS_PLAN_CONTRACT))
    assert resealed.plan_digest != calibration.plan_digest
    assert resealed == multipass_plan(tree, database, chunk_members=1)
    # The calibration plan itself is refused by the multipass entry, by contract.
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.require_multipass_plan(calibration)
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.derive_merge_schedule(calibration)


def test_a04_a05_a_multipass_plan_cannot_become_ordinary_or_calibration(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=33, shards=1)
    plan = multipass_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record["contract"] = cp.CHUNK_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="needs 34 chunks and the single-pass"):
        cp.ChunkPlan.from_record(_resealed(plan, contract=cp.CHUNK_PLAN_CONTRACT))
    record["contract"] = cp.CALIBRATION_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    # Resealed as calibration it is a different identity, and it is consumed by nobody: the
    # single-pass consolidator refuses it by width, the multipass entry by contract.
    twin = cp.ChunkPlan.from_record(_resealed(plan, contract=cp.CALIBRATION_PLAN_CONTRACT))
    assert twin.plan_digest != plan.plan_digest
    with pytest.raises(cc.ChunkConsolidationError, match=c10.WIDTH_REFUSAL):
        cc.require_single_pass_plan(twin)
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.require_multipass_plan(twin)


def test_a06_an_unknown_contract_is_refused_everywhere() -> None:
    plan = replace(_fixed_multipass_plan(), contract="someone-elses-multipass-plan/9")
    with pytest.raises(cp.ChunkPlanError, match="no width rule"):
        cp.require_plan_coverage(plan)
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(_resealed(plan))
    with pytest.raises(cp.ChunkPlanError):
        cm.require_multipass_plan(plan)
    record = dict(_fixed_multipass_plan().as_record())
    record["contract"] = "m3.3-chunked-f0-multipass-plan/2"
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(record)


def test_the_single_pass_consolidator_refuses_a_multipass_plan_by_width_then_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = world(tmp_path, members=9, shards=1)
    plan = multipass_plan(tree, database, chunk_members=1)
    c10._arm_tripwires(monkeypatch)
    with pytest.raises(cc.ChunkConsolidationError, match=c10.WIDTH_REFUSAL):
        cc.consolidate_chunks(
            plan=plan,
            internal_root=tmp_path / "chunks",
            operational_catalog=database,
            world_directory=tmp_path / "final",
            run_id="c13-refused",
        )
    assert not (tmp_path / "final").exists()
    # And with the width invariant removed, the contract line still refuses it.
    monkeypatch.setattr(cc, "require_sealed_plan", lambda plan: plan)
    monkeypatch.setattr(cc, "require_attachable", lambda width: width)
    monkeypatch.setattr(cc, "SINGLE_PASS_CHUNK_CAP", 99)
    with pytest.raises(cc.ChunkConsolidationError, match="never consolidated by this"):
        cc.require_single_pass_plan(plan)


def test_the_multipass_entry_refuses_an_ordinary_plan(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=6, shards=3)
    plan = c1.build_plan(tree, database, chunk_members=1)
    with pytest.raises(cm.ChunkMultipassError, match="ordinary plan is the single-pass"):
        cm.require_multipass_plan(plan)
    # A multipass plan altered in memory is refused before its contract is asked.
    wide_database, wide_tree = world(tmp_path / "wide", members=9, shards=1)
    wide = multipass_plan(wide_tree, wide_database, chunk_members=1)
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cm.require_multipass_plan(replace(wide, chunks=wide.chunks[:9], chunk_count=9))


# ==========================================================================
# S01-S08, A09-A11: the merge schedule
# ==========================================================================
@pytest.mark.parametrize(
    ("members", "shards", "expected"),
    [
        (9, 1, [("primary", 9), ("shard", 1)]),
        (16, 2, [("primary", 9), ("primary", 7), ("shard", 2)]),
        (33, 1, [("primary", 9), ("primary", 9), ("primary", 9), ("primary", 6), ("shard", 1)]),
        (10, 8, [("primary", 9), ("primary", 1), ("shard", 8)]),
    ],
    ids=["ten", "eighteen", "thirty-four", "ten-plus-eight"],
)
def test_s01_s02_the_schedule_is_contiguous_region_homogeneous_and_bounded(
    tmp_path: Path, members: int, shards: int, expected: list[tuple[str, int]]
) -> None:
    database, tree = world(tmp_path, members=members, shards=shards)
    plan = multipass_plan(tree, database, chunk_members=1)
    schedule = cm.derive_merge_schedule(plan)
    assert schedule.contract == cm.MERGE_SCHEDULE_CONTRACT
    assert schedule.plan_digest == plan.plan_digest
    assert schedule.fan_in == 9
    assert [(group.region, len(group.chunk_ids)) for group in schedule.groups] == expected
    assert schedule.level_two_inputs == tuple(group.group_id for group in schedule.groups)
    assert len(schedule.level_two_inputs) <= cm.MERGE_FAN_IN
    cursor = 0
    for ordinal, group in enumerate(schedule.groups):
        assert group.group_id == f"group-{group.ordinal:04d}"
        assert group.ordinal == ordinal
        assert group.start == cursor
        assert len(group.chunk_ids) <= cm.MERGE_FAN_IN
        regions = {cp.chunk_by_id(plan, chunk_id).region for chunk_id in group.chunk_ids}
        assert regions == {group.region}
        bounds = [cp.chunk_by_id(plan, chunk_id) for chunk_id in group.chunk_ids]
        assert [b.start for b in bounds] == [group.start, *[b.end for b in bounds[:-1]]]
        assert bounds[-1].end == group.end
        assert group.plan_ordinals == tuple(plan.chunks.index(b) for b in bounds)
        cursor = group.end
    assert cursor == plan.total_members
    assert cm.require_sealed_schedule(schedule, plan) is schedule


def test_s03_every_admissible_width_groups_into_at_most_five_homogeneous_intermediates() -> None:
    """Exhaustive over every (primary, shard) chunk split of every admissible width."""
    widest = 0
    for total in range(cp.MULTIPASS_CHUNK_FLOOR, cp.MULTIPASS_CHUNK_CEILING + 1):
        for primary in range(0, total + 1):
            bounds = cp.partition_regions(
                primary_members=primary, shard_members=total - primary, chunk_members=1
            )
            groups = cm.group_chunks(bounds)
            assert 2 <= len(groups) <= 5
            widest = max(widest, len(groups))
            for group in groups:
                assert len({b.region for b in bounds if b.chunk_id in group.chunk_ids}) == 1
                assert 1 <= len(group.chunk_ids) <= 9
            assert sum(len(group.chunk_ids) for group in groups) == total
    assert widest == 5


def test_s04_the_real_thirty_thousand_partition_schedules_as_nine_nine_nine_six_plus_one() -> None:
    bounds = cp.partition_regions(
        primary_members=c10.REAL_PRIMARY_MEMBERS,
        shard_members=c10.REAL_SHARD_MEMBERS,
        chunk_members=c10.CALIBRATION_CHUNK_MEMBERS,
    )
    assert len(bounds) == 34
    groups = cm.group_chunks(bounds)
    assert [(g.region, len(g.chunk_ids)) for g in groups] == [
        ("primary", 9),
        ("primary", 9),
        ("primary", 9),
        ("primary", 6),
        ("shard", 1),
    ]
    assert groups[0].chunk_ids[0] == "chunk-0000" and groups[0].end == 270_000
    assert groups[3].chunk_ids == (
        "chunk-0027",
        "chunk-0028",
        "chunk-0029",
        "chunk-0030",
        "chunk-0031",
        "chunk-0032",
    )
    assert groups[3].end == c10.REAL_PRIMARY_MEMBERS
    assert groups[4] == cm.MergeGroup(
        group_id="group-0004",
        ordinal=4,
        region="shard",
        chunk_ids=("chunk-0033",),
        plan_ordinals=(33,),
        start=c10.REAL_PRIMARY_MEMBERS,
        end=c10.REAL_TOTAL_MEMBERS,
    )
    assert len(groups) == 5 < cm.MERGE_FAN_IN


def test_s05_a09_a10_a11_the_schedule_digest_binds_every_field(tmp_path: Path) -> None:
    database, tree = world(tmp_path, members=16, shards=2)
    plan = multipass_plan(tree, database, chunk_members=1)
    schedule = cm.derive_merge_schedule(plan)
    first, second, third = schedule.groups
    # A09: membership moved between groups; A10: order changed; A11: region changed.
    moved = (
        replace(first, chunk_ids=first.chunk_ids[:-1], end=first.end - 1),
        replace(second, chunk_ids=(first.chunk_ids[-1], *second.chunk_ids), start=second.start - 1),
        third,
    )
    reordered = (second, first, third)
    relabelled = (replace(first, region=cp.REGION_SHARD), second, third)
    for label, groups in (("A09", moved), ("A10", reordered), ("A11", relabelled)):
        tampered = replace(schedule, groups=groups)
        with pytest.raises(cm.ChunkMultipassError, match="does not describe its own contents"):
            cm.require_sealed_schedule(tampered, plan)
        resealed = _resealed_schedule(schedule, groups=groups)
        assert resealed.schedule_digest != schedule.schedule_digest, label
        with pytest.raises(cm.ChunkMultipassError, match="never accepted as discretionary input"):
            cm.require_sealed_schedule(resealed, plan)
    # Every other field moves the digest too.
    for changes in (
        {"fan_in": 8},
        {"plan_digest": "0" * 64},
        {"level_two_inputs": tuple(reversed(schedule.level_two_inputs))},
    ):
        assert _resealed_schedule(schedule, **changes).schedule_digest != schedule.schedule_digest
        with pytest.raises(cm.ChunkMultipassError, match="never accepted as discretionary input"):
            cm.require_sealed_schedule(_resealed_schedule(schedule, **changes), plan)
    # And a schedule of ANOTHER plan is refused against this one.
    other_database, other_tree = world(tmp_path / "other", members=16, shards=2, filings=2)
    other = cm.derive_merge_schedule(multipass_plan(other_tree, other_database, chunk_members=1))
    with pytest.raises(cm.ChunkMultipassError, match="never accepted as discretionary input"):
        cm.require_sealed_schedule(other, plan)


def test_s06_a_schedule_record_is_recomputed_and_compared() -> None:
    schedule = cm.derive_merge_schedule(_fixed_multipass_plan())
    record = dict(schedule.as_record())
    record["schedule_digest"] = "0" * 64
    with pytest.raises(cm.ChunkMultipassError, match="does not describe its own contents"):
        cm.MergeSchedule.from_record(record)
    record = dict(schedule.as_record())
    record["contract"] = "m3.3-chunked-f0-merge-schedule/2"
    with pytest.raises(cm.ChunkMultipassError, match="never adopts another shape"):
        cm.MergeSchedule.from_record(record)
    record = dict(schedule.as_record())
    del record["groups"]
    with pytest.raises(cm.ChunkMultipassError, match="missing"):
        cm.MergeSchedule.from_record(record)
    with pytest.raises(cm.ChunkMultipassError, match="is not in this merge schedule"):
        cm.group_by_id(schedule, "group-9999")
    assert cm.group_by_id(schedule, "group-0001").region == cp.REGION_SHARD


def test_s07_the_grouping_arithmetic_refuses_a_bad_fan_in_and_a_gap() -> None:
    bounds = cp.partition_regions(primary_members=12, shard_members=0, chunk_members=1)
    with pytest.raises(cm.ChunkMultipassError, match="positive fan-in"):
        cm.group_chunks(bounds, fan_in=0)
    assert [len(g.chunk_ids) for g in cm.group_chunks(bounds, fan_in=5)] == [5, 5, 2]
    gapped = (*bounds[:3], *bounds[4:])
    with pytest.raises(cm.ChunkMultipassError, match="not contiguous"):
        cm.group_chunks(gapped)


def test_s08_a_caller_cannot_supply_a_grouping() -> None:
    """The only constructor a consumer reaches derives the schedule from the sealed plan."""
    parameters = inspect.signature(cm.derive_merge_schedule).parameters
    assert list(parameters) == ["plan"]
    for name in ("merge_group_body", "finalize_multipass_body", "run_multipass_f0"):
        signature = inspect.signature(getattr(cm, name))
        assert "groups" not in signature.parameters and "schedule" not in signature.parameters
    body_source = inspect.getsource(cm._read_plan_and_schedule)
    assert "require_sealed_schedule(schedule, plan)" in body_source


# ==========================================================================
# C11-MINOR-1: the contract check in require_single_pass_plan is load-bearing
# ==========================================================================
def _narrow_calibration_record(tmp_path: Path) -> dict[str, object]:
    """A valid, sealed calibration record: five chunks under a DECLARED cap of three.

    The calibration width rule compares the chunk count against the declared cap, so this record
    passes every coverage rule; and a declared cap below the constant is not refused. It is the
    record D151-C11 built to reach the contract check, written to disk and read back so that no
    in-memory object is involved.
    """
    database, tree = world(tmp_path, members=4, shards=1)
    # Five chunks: an ordinary plan, relabelled calibration and declared under a cap of three.
    calibration = replace(
        c1.build_plan(tree, database, chunk_members=1),
        contract=cp.CALIBRATION_PLAN_CONTRACT,
        single_pass_chunk_cap=3,
        plan_digest="",
    )
    record = dict(calibration.as_record())
    record["plan_digest"] = cp._plan_digest(calibration)
    path = tmp_path / "narrow_calibration.json"
    write_once_json(path, record)
    return json.loads(path.read_text(encoding="utf-8"))


def test_c11_minor_1_a_lowered_cap_calibration_record_reaches_the_contract_check(
    tmp_path: Path,
) -> None:
    """The non-monkeypatched regression: nothing is patched, and only the contract line refuses."""
    record = _narrow_calibration_record(tmp_path)
    plan = cp.ChunkPlan.from_record(record)
    assert plan.calibration_only and plan.chunk_count == 5 and plan.single_pass_chunk_cap == 3
    assert cp.require_sealed_plan(plan) is plan
    assert cc.require_attachable(plan.chunk_count) == 5
    with pytest.raises(cc.ChunkConsolidationError) as refusal:
        cc.require_single_pass_plan(plan)
    message = str(refusal.value)
    assert "never consolidated by this single-pass consolidator" in message
    assert "single-pass chunked-F0 architecture admits" not in message
    assert "SQLITE_LIMIT_ATTACHED" not in message


def test_c11_minor_1_the_refusal_lands_before_any_primitive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = _narrow_calibration_record(tmp_path)
    plan = cp.ChunkPlan.from_record(record)
    c10._arm_tripwires(monkeypatch)
    before = _names(tmp_path)
    with pytest.raises(cc.ChunkConsolidationError, match="never consolidated by this"):
        cc.consolidate_chunks(
            plan=plan,
            internal_root=tmp_path / "chunks",
            operational_catalog=tmp_path / "catalog.sqlite3",
            world_directory=tmp_path / "final",
            run_id="c11-minor-1",
        )
    assert _names(tmp_path) == before


def test_c11_minor_1_the_docstring_states_the_check_is_reachable_and_load_bearing() -> None:
    docstring = inspect.getdoc(cc.require_single_pass_plan) or ""
    assert "reachable and load-bearing" in docstring
    assert "D151-C11" in docstring
    assert "lowered cap" in docstring
    assert "only thing that refuses it" in docstring
    assert "reached only if that invariant is ever removed" not in docstring
    # And the check is a real branch in the function body, on the contract, after the width gate.
    tree = ast.parse(inspect.getsource(cc.require_single_pass_plan))
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    compares = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Attribute)
        and node.left.attr == "contract"
    ]
    assert len(compares) == 1


def test_c11_minor_1_the_multipass_analogue_is_closed_at_the_plan_level(tmp_path: Path) -> None:
    """A multipass record with a lowered declared cap does not even read back."""
    database, tree = world(tmp_path, members=9, shards=1)
    plan = multipass_plan(tree, database, chunk_members=1)
    with pytest.raises(cp.ChunkPlanError, match="held to the constant"):
        cp.ChunkPlan.from_record(_resealed(plan, single_pass_chunk_cap=3))


# ==========================================================================
# D151-C24-R2: the orchestrator charges every step at its own level -- C23-MINOR-4
# ==========================================================================
def test_c24_r2_the_orchestrator_charges_each_step_its_own_level_transient(
    tmp_path: Path,
) -> None:
    """D151-C24-R2, closing C23-MINOR-4: the level argument is load-bearing at every call site.

    ``MultipassStorageRequirements.transient_for`` has no fallback between levels, and
    ``test_d151_c17_storage_binding`` holds that pure selector to it. What was unheld is the
    orchestrator's own choice of which level to name for which step: every full-run fixture in
    this repository charges both levels zero, so swapping the two arguments changed nothing any
    committed assertion could see. This run tells the levels apart and reads back the admission
    the production gate itself returned for every step the orchestrator took -- each level-1
    group, then the level-2 finalization -- and the children's durable record of their own.
    """
    assert LEVEL_ONE_TRANSIENT_SENTINEL != LEVEL_TWO_TRANSIENT_SENTINEL
    assert LEVEL_ONE_TRANSIENT_SENTINEL > 0
    assert LEVEL_TWO_TRANSIENT_SENTINEL > 0
    assert (
        LEVEL_DISTINCT_REQUIREMENTS.transient_for(ct.MERGE_LEVEL_ONE)
        == LEVEL_ONE_TRANSIENT_SENTINEL
    )
    assert (
        LEVEL_DISTINCT_REQUIREMENTS.transient_for(ct.MERGE_LEVEL_TWO)
        == LEVEL_TWO_TRANSIENT_SENTINEL
    )

    # Imported here, not at module scope: test_d151_c13_intermediates imports THIS module, and
    # its accepted child bootstrap is the one seam that opens a merge child.
    import test_d151_c13_intermediates as c13i

    database, tree = world(tmp_path, members=9, shards=1, filings=2)
    plan = multipass_plan(tree, database, chunk_members=1)
    run = execute_in_process(plan, tmp_path / "run", database, tree)

    taken: list[ct.MergeAdmission] = []
    admit = cm._admit_merge_step

    def recording(**terms: Any) -> ct.MergeAdmission:
        """Delegate to the production gate and keep the admission it returned."""
        admission = admit(**terms)
        taken.append(admission)
        return admission

    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(
            cm, "accepted_multipass_storage_requirements", lambda: LEVEL_DISTINCT_REQUIREMENTS
        )
        patcher.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))
        patcher.setattr(cm, "_admit_merge_step", recording)
        result = cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=tmp_path / "multipass",
            run_id="c24-r2",
        )

    groups = [group.group_id for group in result.schedule.groups]
    assert len(groups) >= 2, groups
    assert [admission.step for admission in taken] == [*groups, "final"]

    for admission in taken[:-1]:
        assert admission.level == ct.MERGE_LEVEL_ONE, admission.step
        assert admission.transient_bytes == LEVEL_ONE_TRANSIENT_SENTINEL, admission.step
        assert admission.admitted is True, admission.step
        assert admission.required_free_bytes == (
            admission.peak_bytes + admission.reserve_bytes + admission.transient_bytes
        ), admission.step

    final = taken[-1]
    assert final.step == "final"
    assert final.level == ct.MERGE_LEVEL_TWO
    assert final.transient_bytes == LEVEL_TWO_TRANSIENT_SENTINEL
    assert final.admitted is True
    assert final.required_free_bytes == (
        final.peak_bytes + final.reserve_bytes + final.transient_bytes
    )

    # Each merge child charged its own group at level one and recorded it durably, under the
    # same terms the parent admitted it on.
    assert [receipt.group_id for receipt in result.intermediates] == groups
    for receipt in result.intermediates:
        recorded = dict(receipt.storage_admission)
        assert recorded["step"] == receipt.group_id
        assert recorded["level"] == ct.MERGE_LEVEL_ONE, receipt.group_id
        assert recorded["transient_bytes"] == LEVEL_ONE_TRANSIENT_SENTINEL, receipt.group_id

    # The sealed storage plan and the run itself are the accepted ones.
    assert result.storage_plan.contract == ct.MULTIPASS_STORAGE_PLAN_CONTRACT
    assert result.receipt["chunks_unchanged"] is True
