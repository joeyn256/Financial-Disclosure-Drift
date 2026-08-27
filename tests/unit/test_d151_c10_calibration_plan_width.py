"""D151-C10: calibration-only plan-width decoupling.

Two widths, proved separately and proved not to leak into each other. The width a plan may
DESCRIBE grows to thirty-four chunks under a distinct, sealed calibration-only contract, so that
one individual chunk of a smaller size can be executed and measured before any multi-pass
consolidation exists. The width the single-pass consolidator may CONSUME stays nine, and the
consolidator refuses a wider plan by width before it measures, reads, lists or attaches anything.

Every proof runs over the hostile synthetic world of ``test_d151_c1_chunk_plan``. No real
artifact is read: the real 30,000-member partition is proved from its region counts, which are
the accepted ones (980,497 primary members and 5,337 historical shards), through the same
arithmetic both plan builders run.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F1,
    CanaryPhaseError,
    read_phase_checkpoint,
    require_phase_admission,
)
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_PLAN_FILENAME,
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    read_receipt_document,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.offline_parse import _BULK_PARSER_ID  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.source_registry import SOURCES  # noqa: E402

# ==========================================================================
# Frozen facts
# ==========================================================================
#: The governed source's region counts: accepted (985,834 members, 5,337 shards) and reproduced
#: read-only from the frozen archive's central directory during D151-C7 and again during D151-C10.
REAL_PRIMARY_MEMBERS = 980_497
REAL_SHARD_MEMBERS = 5_337
REAL_TOTAL_MEMBERS = 985_834

#: The accepted calibration partition size (D151-C7, D151-C9) and the future one (D151-C10 §4).
ACCEPTED_CHUNK_MEMBERS = 122_563
CALIBRATION_CHUNK_MEMBERS = 30_000

#: The ordinary plan digest over FIXED fields, measured at the D151-C9 closure tree a2eed813
#: BEFORE this change. Pure JSON plus SHA-256, so it is deterministic on every host, and it moves
#: if a key is added to, removed from, renamed in or reordered within an ordinary plan's digest
#: inputs. The accepted real plan's digest (1bc46e2d...) is the same algorithm over the real
#: archive; this is the algorithm pinned where no real artifact is needed.
GOLDEN_ORDINARY_PLAN_DIGEST = "51447b01f7f09abe121e3fc4cab7da1e2a3d1e7a45183fe2820bbfc5a4b4b736"

#: The member-order digest over a FIXED three-member sequence, measured the same way.
GOLDEN_MEMBER_ORDER_DIGEST = "e21cee5624a669cbd7c72bf4c261102b69cf61d503edead520486062a0017520"

#: Exactly the keys an ordinary plan record carried before this change, and still carries.
ORDINARY_RECORD_KEYS = frozenset(
    {
        "chunk_count",
        "chunk_members",
        "chunks",
        "contract",
        "member_order_contract",
        "member_order_digest",
        "plan_digest",
        "primary_members",
        "shard_members",
        "single_pass_chunk_cap",
        "source_byte_length",
        "source_id",
        "source_instance_id",
        "source_observation_id",
        "source_sha256",
        "total_members",
    }
)

FIXED_MEMBERS = (
    cp.CanonicalMember(0, 1, "CIK0000000001.json", cp.REGION_PRIMARY),
    cp.CanonicalMember(1, 2, "CIK0000000002.json", cp.REGION_PRIMARY),
    cp.CanonicalMember(2, 0, "CIK0000000001-submissions-001.json", cp.REGION_SHARD),
)

WIDTH_REFUSAL = r"needs (\d+) chunks and the single-pass chunked-F0 architecture admits 9"


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin, through the accepted identity seam -- see ``test_d151_c1_chunk_plan``."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Helpers
# ==========================================================================
def _world(tmp_path: Path, *, members: int, shards: int) -> tuple[Path, DataTree]:
    """A synthetic world holding exactly ``members + shards`` governed members."""
    return c1.build_world(tmp_path, members=members, filings=1, shards=shards)


def calibration_plan(tree: DataTree, database: Path, *, chunk_members: int) -> cp.ChunkPlan:
    """One calibration-only plan over this world's archive, at a caller-chosen partition size."""
    observation = c1.observation_of(tree, database)
    return cp.build_calibration_chunk_plan(
        archive_path=c1.archive_of(tree),
        source_instance_id=c1.INSTANCE,
        source_observation_id=c1.OBSERVATION,
        source_id=c1.SOURCE_ID,
        source_sha256=observation.logical_sha256,
        source_byte_length=observation.content_size_bytes,
        chunk_members=chunk_members,
    )


def _fixed_ordinary_plan() -> cp.ChunkPlan:
    """An ordinary plan over fixed fields -- the digest algorithm's own test vector."""
    bounds = cp.partition_regions(primary_members=6, shard_members=3, chunk_members=4)
    plan = cp.ChunkPlan(
        contract=cp.CHUNK_PLAN_CONTRACT,
        member_order_contract=cp.MEMBER_ORDER_CONTRACT,
        source_instance_id="base|sec_bulk_submissions|1",
        source_observation_id="obs-bulk-1",
        source_id="sec_bulk_submissions",
        source_sha256="ab" * 32,
        source_byte_length=123456,
        member_order_digest="cd" * 32,
        total_members=9,
        primary_members=6,
        shard_members=3,
        chunk_members=4,
        chunk_count=3,
        single_pass_chunk_cap=cp.SINGLE_PASS_CHUNK_CAP,
        chunks=bounds,
        plan_digest="",
    )
    return replace(plan, plan_digest=cp._plan_digest(plan))


def _resealed(plan: cp.ChunkPlan, **changes: Any) -> dict[str, object]:
    """A tampered plan whose digest is recomputed, so only a coverage rule can catch it."""
    tampered = replace(plan, **changes, plan_digest="")
    record = dict(tampered.as_record())
    record["plan_digest"] = cp._plan_digest(tampered)
    return record


def _names(root: Path) -> list[str]:
    return sorted(str(path.relative_to(root)) for path in root.rglob("*"))


def _tripwire(name: str) -> Any:
    def reached(*_args: Any, **_kwargs: Any) -> Any:
        message = f"{name} was reached; the single-pass width refusal must land before it"
        raise AssertionError(message)

    return reached


def _arm_tripwires(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail loudly if consolidation reaches anything past its entry gate."""
    for name in (
        "require_clean_running_repository",
        "resolve_chunk_inputs",
        "_accepted_plan_state",
        "WorkingCatalog",
        "_attach_all",
    ):
        monkeypatch.setattr(cc, name, _tripwire(name))


def _execute_chunk_zero(
    tmp_path: Path, plan: cp.ChunkPlan, database: Path, tree: DataTree
) -> tuple[Any, Path, Path]:
    """Run chunk-0000 of ``plan`` in the accepted child process; return receipt, dir, root."""
    base = tmp_path / "calibration"
    base.mkdir()
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    chunk_root = base / "chunks"
    attempt_directory, attempt = ce.next_attempt_directory(chunk_root, "chunk-0000")
    receipt = ce.run_chunk(
        c1x.chunk_request(
            plan_path=plan_path,
            chunk_id="chunk-0000",
            attempt=attempt,
            attempt_directory=attempt_directory,
            database=database,
            tree=tree,
        )
    )
    return receipt, attempt_directory, chunk_root


# ==========================================================================
# C1001-C1003: the accepted ordinary plan keeps its identity
# ==========================================================================
def test_c1001_the_accepted_partition_is_exactly_nine_chunks() -> None:
    """122,563 members per chunk over the governed counts is eight primaries and one shard."""
    bounds = cp.partition_regions(
        primary_members=REAL_PRIMARY_MEMBERS,
        shard_members=REAL_SHARD_MEMBERS,
        chunk_members=ACCEPTED_CHUNK_MEMBERS,
    )
    assert len(bounds) == 9 == cp.SINGLE_PASS_CHUNK_CAP
    assert [b.region for b in bounds] == [cp.REGION_PRIMARY] * 8 + [cp.REGION_SHARD]
    assert bounds[0] == cp.ChunkBounds("chunk-0000", cp.REGION_PRIMARY, 0, 122_563)
    assert bounds[7] == cp.ChunkBounds("chunk-0007", cp.REGION_PRIMARY, 857_941, 980_497)
    assert bounds[8] == cp.ChunkBounds("chunk-0008", cp.REGION_SHARD, 980_497, 985_834)
    assert bounds[-1].end == REAL_TOTAL_MEMBERS == REAL_PRIMARY_MEMBERS + REAL_SHARD_MEMBERS


def test_c1002_the_ordinary_plan_digest_algorithm_is_byte_exact() -> None:
    """The digest inputs of an ordinary plan are exactly what they were: no key gained or lost."""
    plan = _fixed_ordinary_plan()
    assert plan.plan_digest == GOLDEN_ORDINARY_PLAN_DIGEST
    assert set(plan.as_record()) == ORDINARY_RECORD_KEYS
    assert "purpose" not in plan.as_record() and "calibration" not in json.dumps(
        dict(plan.as_record())
    )
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record())))) == plan
    assert cp.CHUNK_PLAN_CONTRACT == "m3.3-chunked-f0-plan/2"
    assert plan.calibration_only is False


def test_c1003_the_member_order_digest_algorithm_is_byte_exact() -> None:
    assert cp.compute_member_order_digest(FIXED_MEMBERS) == GOLDEN_MEMBER_ORDER_DIGEST
    assert cp.MEMBER_ORDER_CONTRACT == "m3.3-chunked-f0-member-order/1"


def test_c1001_a_nine_member_world_still_builds_nine_ordinary_chunks(tmp_path: Path) -> None:
    """The accepted builder, unchanged in what it seals: contract, cap and partition."""
    database, tree = _world(tmp_path, members=6, shards=3)
    plan = c1.build_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 9 == len(plan.chunks)
    assert plan.contract == cp.CHUNK_PLAN_CONTRACT
    assert plan.single_pass_chunk_cap == 9
    assert plan.chunks == cp.partition_regions(primary_members=6, shard_members=3, chunk_members=1)
    assert cp.require_sealed_plan(plan) is plan
    assert cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record())))) == plan


# ==========================================================================
# C1004-C1007: the 30,000-member calibration partition
# ==========================================================================
def test_c1004_to_c1007_the_thirty_thousand_partition_is_thirty_four_chunks() -> None:
    """ceil(980497 / 30000) = 33 primary chunks, ceil(5337 / 30000) = 1 shard chunk, 34 in all."""
    bounds = cp.partition_regions(
        primary_members=REAL_PRIMARY_MEMBERS,
        shard_members=REAL_SHARD_MEMBERS,
        chunk_members=CALIBRATION_CHUNK_MEMBERS,
    )
    assert len(bounds) == 34 == cp.CALIBRATION_CHUNK_CEILING
    assert sum(1 for b in bounds if b.region == cp.REGION_PRIMARY) == 33
    assert sum(1 for b in bounds if b.region == cp.REGION_SHARD) == 1
    # C1007: the future target.
    assert bounds[0] == cp.ChunkBounds("chunk-0000", cp.REGION_PRIMARY, 0, 30_000)
    assert bounds[0].member_count == 30_000
    assert bounds[32] == cp.ChunkBounds("chunk-0032", cp.REGION_PRIMARY, 960_000, 980_497)
    assert bounds[33] == cp.ChunkBounds("chunk-0033", cp.REGION_SHARD, 980_497, 985_834)
    # Exact coverage once, and the region boundary is a chunk boundary.
    cursor = 0
    for b in bounds:
        assert b.start == cursor
        cursor = b.end
    assert cursor == REAL_TOTAL_MEMBERS
    assert [b.chunk_id for b in bounds] == [f"chunk-{i:04d}" for i in range(34)]


def test_c1004_a_synthetic_calibration_plan_constructs_and_round_trips(tmp_path: Path) -> None:
    """Thirty-three primaries and one shard, one member per chunk: the real shape in miniature."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    assert plan.contract == cp.CALIBRATION_PLAN_CONTRACT
    assert plan.calibration_only is True
    assert plan.chunk_count == 34 == len(plan.chunks)
    assert plan.primary_members == 33 and plan.shard_members == 1
    assert plan.chunks[0] == cp.ChunkBounds("chunk-0000", cp.REGION_PRIMARY, 0, 1)
    assert plan.chunks[-1] == cp.ChunkBounds("chunk-0033", cp.REGION_SHARD, 33, 34)
    # The cap it was sealed under is the single-pass cap it exceeds -- recorded, not raised.
    assert plan.single_pass_chunk_cap == cp.SINGLE_PASS_CHUNK_CAP == 9
    # Same fields as an ordinary record, so no consumer half-reads it; the contract differs.
    assert set(plan.as_record()) == ORDINARY_RECORD_KEYS
    restored = cp.ChunkPlan.from_record(json.loads(json.dumps(dict(plan.as_record()))))
    assert restored == plan
    assert cp.require_sealed_plan(plan) is plan
    assert cp.chunk_by_id(plan, "chunk-0000") == plan.chunks[0]


def test_the_two_builders_share_one_partition_and_one_ordering(tmp_path: Path) -> None:
    """A calibration plan partitions the members an ordinary plan would, in the same order."""
    database, tree = _world(tmp_path, members=33, shards=1)
    wide = calibration_plan(tree, database, chunk_members=1)
    narrow = c1.build_plan(tree, database, chunk_members=5)
    assert wide.member_order_digest == narrow.member_order_digest
    assert (wide.total_members, wide.primary_members, wide.shard_members) == (34, 33, 1)
    assert narrow.chunk_count == 8
    assert wide.chunks == cp.partition_regions(primary_members=33, shard_members=1, chunk_members=1)
    assert narrow.chunks == cp.partition_regions(
        primary_members=33, shard_members=1, chunk_members=5
    )
    assert cp.resolve_chunk_members(wide, c1.archive_of(tree), "chunk-0000") == (
        cp.canonical_member_sequence(c1.archive_of(tree))[0],
    )


# ==========================================================================
# C1008-C1010, A02, A08, A09, A13: the distinction is sealed and unmistakable
# ==========================================================================
def test_c1008_the_calibration_identity_binds_the_distinction(tmp_path: Path) -> None:
    """Same fields, different contract, different digest -- the distinction is in the seal."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    twin = replace(plan, contract=cp.CHUNK_PLAN_CONTRACT)
    assert cp._plan_digest(twin) != plan.plan_digest
    assert dict(plan.as_record())["contract"] == cp.CALIBRATION_PLAN_CONTRACT
    assert "calibration" in json.dumps(dict(plan.as_record()))


def test_c1009_a02_changing_the_distinction_after_sealing_breaks_verification(
    tmp_path: Path,
) -> None:
    """Relabel the record, or the object: the digest no longer describes it."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record["contract"] = cp.CHUNK_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.require_sealed_plan(replace(plan, contract=cp.CHUNK_PLAN_CONTRACT))
    record["contract"] = "m3.3-chunked-f0-calibration-plan/2"
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(record)


def test_c1010_a08_an_ordinary_plan_cannot_be_relabelled_calibration_after_sealing(
    tmp_path: Path,
) -> None:
    """A nine-chunk plan marked wider: the digest catches the label, the width rule the reseal."""
    database, tree = _world(tmp_path, members=6, shards=3)
    plan = c1.build_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 9
    record = dict(plan.as_record())
    record["contract"] = cp.CALIBRATION_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    # Resealed -- digest and all -- it is still refused, because a calibration-only plan must be
    # wider than the single-pass cap. That rule is what keeps every calibration plan outside the
    # width the consolidator accepts.
    with pytest.raises(cp.ChunkPlanError, match="single-pass chunked-F0 architecture admits"):
        cp.ChunkPlan.from_record(_resealed(plan, contract=cp.CALIBRATION_PLAN_CONTRACT))
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        cp.require_sealed_plan(
            cp.ChunkPlan.from_record(_resealed(plan, contract=cp.CALIBRATION_PLAN_CONTRACT))
        )


def test_a09_a_calibration_plan_cannot_be_relabelled_ordinary_after_sealing(
    tmp_path: Path,
) -> None:
    """Thirty-four chunks marked ordinary: the label moves the digest; a reseal hits the cap."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record["contract"] = cp.CHUNK_PLAN_CONTRACT
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="needs 34 chunks and the single-pass"):
        cp.ChunkPlan.from_record(_resealed(plan, contract=cp.CHUNK_PLAN_CONTRACT))


def test_a13_a_wider_partition_without_the_calibration_distinction_is_refused(
    tmp_path: Path,
) -> None:
    """The ordinary builder refuses ten and thirty-four exactly as before; nothing is written."""
    database, tree = _world(tmp_path, members=33, shards=1)
    before = _names(tmp_path)
    with pytest.raises(cp.ChunkPlanError, match="needs 34 chunks and the single-pass"):
        c1.build_plan(tree, database, chunk_members=1)
    with pytest.raises(cp.ChunkPlanError, match="needs 10 chunks and the single-pass"):
        c1.build_plan(tree, database, chunk_members=4)
    assert _names(tmp_path) == before
    # And the accepted nine is still built by the accepted builder, over the same world.
    assert c1.build_plan(tree, database, chunk_members=5).chunk_count == 8


def test_a_calibration_plan_that_fits_the_single_pass_cap_is_refused(tmp_path: Path) -> None:
    """Nine or fewer chunks is an ordinary plan; the calibration builder refuses to seal it."""
    database, tree = _world(tmp_path, members=6, shards=3)
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        calibration_plan(tree, database, chunk_members=1)
    wide_database, wide_tree = _world(tmp_path / "wide", members=33, shards=1)
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        calibration_plan(wide_tree, wide_database, chunk_members=5)
    assert calibration_plan(wide_tree, wide_database, chunk_members=4).chunk_count == 10


def test_a10_thirty_five_chunks_are_refused_at_construction_and_on_read(tmp_path: Path) -> None:
    """The ceiling is exactly thirty-four: one more refuses, before and after sealing."""
    database, tree = _world(tmp_path, members=34, shards=1)
    before = _names(tmp_path)
    with pytest.raises(cp.ChunkPlanError, match="CALIBRATION_CHUNK_CEILING = 34"):
        calibration_plan(tree, database, chunk_members=1)
    assert _names(tmp_path) == before
    # A record that declares thirty-five chunks and seals them is refused when it is read back.
    bounds = cp.partition_regions(primary_members=34, shard_members=1, chunk_members=1)
    forged = replace(
        _fixed_ordinary_plan(),
        contract=cp.CALIBRATION_PLAN_CONTRACT,
        total_members=35,
        primary_members=34,
        shard_members=1,
        chunk_members=1,
        chunk_count=35,
        chunks=bounds,
    )
    with pytest.raises(cp.ChunkPlanError, match="CALIBRATION_CHUNK_CEILING = 34"):
        cp.ChunkPlan.from_record(_resealed(forged))
    # Thirty-four itself is admitted by the same read path.
    admitted = replace(
        forged,
        total_members=34,
        primary_members=33,
        chunk_count=34,
        chunks=cp.partition_regions(primary_members=33, shard_members=1, chunk_members=1),
    )
    assert cp.ChunkPlan.from_record(_resealed(admitted)).chunk_count == 34


def test_the_ceiling_the_cap_and_the_contracts_are_frozen_together() -> None:
    """The literals this decoupling rests on, pinned as a set."""
    assert cp.CALIBRATION_CHUNK_CEILING == 34
    assert cp.CALIBRATION_PLAN_CONTRACT == "m3.3-chunked-f0-calibration-plan/1"
    assert cp.CHUNK_PLAN_CONTRACT == "m3.3-chunked-f0-plan/2"
    assert cp.SINGLE_PASS_CHUNK_CAP == 9
    assert cp.RESERVED_ATTACHMENT_HEADROOM == 1
    assert cp.CALIBRATION_PLAN_CONTRACT != cp.CHUNK_PLAN_CONTRACT
    for name in (
        "CALIBRATION_CHUNK_CEILING",
        "CALIBRATION_PLAN_CONTRACT",
        "build_calibration_chunk_plan",
        "partition_regions",
        "require_sealed_plan",
    ):
        assert name in cp.__all__, name
    assert "require_single_pass_plan" in cc.__all__


def test_an_unknown_contract_has_no_width_rule() -> None:
    plan = replace(_fixed_ordinary_plan(), contract="someone-elses-plan/9")
    with pytest.raises(cp.ChunkPlanError, match="no width rule"):
        cp.require_plan_coverage(plan)
    with pytest.raises(cp.ChunkPlanError, match="never adopts another shape"):
        cp.ChunkPlan.from_record(_resealed(plan))


@pytest.mark.parametrize("size", [0, -1])
def test_partition_regions_refuses_a_non_positive_size(size: int) -> None:
    with pytest.raises(cp.ChunkPlanError, match="positive chunk size"):
        cp.partition_regions(primary_members=3, shard_members=0, chunk_members=size)
    assert cp.partition_regions(primary_members=0, shard_members=0, chunk_members=1) == ()


# ==========================================================================
# A01, A03, A04, A05: hostile calibration records
# ==========================================================================
def test_a01_the_width_field_changed_after_seal(tmp_path: Path) -> None:
    """Raising the single-pass cap inside a calibration record: digest first, constant second."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record["single_pass_chunk_cap"] = 34
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="never a permission to exceed"):
        cp.ChunkPlan.from_record(_resealed(plan, single_pass_chunk_cap=34))


def test_a03_the_chunk_count_changed_after_seal(tmp_path: Path) -> None:
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record["chunk_count"] = 9
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="built as one"):
        cp.ChunkPlan.from_record(_resealed(plan, chunk_count=9))
    with pytest.raises(cp.ChunkPlanError, match="declares 10 chunks and carries 34"):
        cp.ChunkPlan.from_record(_resealed(plan, chunk_count=10))


def test_a04_an_interval_changed_after_seal(tmp_path: Path) -> None:
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    shifted = list(plan.chunks)
    shifted[0] = replace(shifted[0], end=2)
    record = dict(plan.as_record())
    record["chunks"] = [dict(b.as_record()) for b in shifted]
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)
    with pytest.raises(cp.ChunkPlanError, match="overlap"):
        cp.ChunkPlan.from_record(_resealed(plan, chunks=tuple(shifted)))


@pytest.mark.parametrize(
    "field",
    [
        "source_sha256",
        "source_byte_length",
        "member_order_digest",
        "source_observation_id",
        "source_instance_id",
    ],
)
def test_a05_the_source_identity_changed_after_seal(tmp_path: Path, field: str) -> None:
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    record = dict(plan.as_record())
    record[field] = 1 if field == "source_byte_length" else "f" * 64
    with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
        cp.ChunkPlan.from_record(record)


# ==========================================================================
# C1011-C1015, A06, A07, A11, A12, A14: one individual calibration chunk
# ==========================================================================
def test_c1011_to_c1015_a12_one_synthetic_calibration_chunk_executes_and_stays_noncanonical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """chunk-0000 of a thirty-four-chunk calibration plan: a valid chunk, never an F0 world.

    C1011 the child runs, in its own process, and exits; C1012 the receipt binds the wider plan's
    digest and every source identity; A07 the execution identity is derived from that digest and
    differs under the ordinary twin; C1013 the artifact verifies and carries the calibration plan;
    C1014 no F0 terminal exists; C1015/A11 the accepted F1 admission refuses it; A12 the current
    consolidator refuses the plan by width without touching the chunk.
    """
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    receipt, attempt_directory, chunk_root = _execute_chunk_zero(tmp_path, plan, database, tree)
    assert c1.PINNED is not None

    # C1011: a fresh child that measured its own code identity, parsed, and ended.
    assert receipt.status == "complete"
    assert (receipt.chunk_id, receipt.region, receipt.start, receipt.end) == (
        "chunk-0000",
        cp.REGION_PRIMARY,
        0,
        1,
    )
    assert receipt.pid != os.getpid()
    with pytest.raises(ProcessLookupError):
        os.kill(receipt.pid, 0)
    assert (receipt.repository_head_sha, receipt.repository_tree_sha) == (
        c1.PINNED.head_sha,
        c1.PINNED.tree_sha,
    )
    assert receipt.summary.members == 1
    assert receipt.summary.parsed_records >= 1

    # C1012: the receipt binds the WIDER plan and every source identity the plan binds.
    assert receipt.plan_digest == plan.plan_digest
    assert receipt.member_order_digest == plan.member_order_digest
    assert receipt.source_sha256 == plan.source_sha256
    assert receipt.source_byte_length == plan.source_byte_length
    assert receipt.source_instance_id == plan.source_instance_id
    assert receipt.source_observation_id == plan.source_observation_id
    assert receipt.execution_contract.parser_id == _BULK_PARSER_ID
    assert receipt.execution_contract.parser_version == str(SOURCES[c1.SOURCE_ID].parser_version)

    # A07: the execution identity recomputes from the calibration plan and moves with it.
    def identity_under(candidate: cp.ChunkPlan) -> str:
        return ce.chunk_execution_identity(
            plan=candidate,
            chunk_id="chunk-0000",
            batch_size=receipt.execution_contract.batch_size,
            cache_bytes=receipt.cache_bytes,
            repository_head_sha=receipt.repository_head_sha,
            repository_tree_sha=receipt.repository_tree_sha,
            catalog_source_sha256=receipt.execution_contract.catalog_source_sha256,
            migration_head=receipt.execution_contract.migration_head,
        )

    assert receipt.execution_identity == identity_under(plan)
    twin = replace(plan, contract=cp.CHUNK_PLAN_CONTRACT)
    twin = replace(twin, plan_digest=cp._plan_digest(twin))
    assert identity_under(twin) != receipt.execution_identity

    # C1013: the artifact verifies, and the plan it carries is the calibration plan.
    verify_artifact_manifest(attempt_directory, receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,))
    manifest_paths = {entry.relative_path for entry in receipt.manifest.entries}
    assert CHUNK_PLAN_FILENAME in manifest_paths
    stored = json.loads((attempt_directory / CHUNK_PLAN_FILENAME).read_text(encoding="utf-8"))
    assert stored["contract"] == cp.CALIBRATION_PLAN_CONTRACT
    assert cp.ChunkPlan.from_record(stored) == plan
    assert (
        read_receipt_document(
            attempt_directory / CHUNK_RECEIPT_FILENAME, contract=CHUNK_RECEIPT_CONTRACT
        )["plan_digest"]
        == plan.plan_digest
    )

    # C1014: nonterminal and noncanonical -- no F0 checkpoint, no final receipt, no source state.
    assert not (attempt_directory / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert receipt.summary.parser_state_after == "chunk_local"
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(
            attempt_directory / CHUNK_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )
    ledger = RunProgressLedger(attempt_directory / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, "f0") is None
        # C1015 / A11: the ACCEPTED admission rule, with every identity the chunk itself recorded.
        with pytest.raises(CanaryPhaseError, match="no durable terminal checkpoint"):
            require_phase_admission(
                ledger,
                phase=PHASE_F1,
                run_id="c10-calibration",
                source_instance_id=c1.INSTANCE,
                execution_identity=receipt.execution_identity,
                repository_head_sha=receipt.repository_head_sha,
                repository_tree_sha=receipt.repository_tree_sha,
                catalog_source_sha256=receipt.execution_contract.catalog_source_sha256,
                migration_head=receipt.execution_contract.migration_head,
                plan_fingerprint="fingerprint",
            )
    finally:
        ledger.close()

    # A12 / C1018: the current consolidator refuses the whole plan by width, reading nothing.
    _arm_tripwires(monkeypatch)
    before = _names(chunk_root)
    world_directory = tmp_path / "calibration" / "final"
    with pytest.raises(cc.ChunkConsolidationError, match=WIDTH_REFUSAL) as refusal:
        cc.consolidate_chunks(
            plan=plan,
            internal_root=chunk_root,
            operational_catalog=database,
            world_directory=world_directory,
            run_id="c10-calibration",
        )
    assert "needs 34 chunks" in str(refusal.value)
    assert not world_directory.exists()
    assert _names(chunk_root) == before
    verify_artifact_manifest(attempt_directory, receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,))


def test_a06_a_request_naming_another_repository_is_refused_by_the_child(tmp_path: Path) -> None:
    """The child measures its own code identity; a calibration request cannot claim another."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    base = tmp_path / "calibration"
    base.mkdir()
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    chunk_root = base / "chunks"
    attempt_directory, attempt = ce.next_attempt_directory(chunk_root, "chunk-0000")
    assert c1.PINNED is not None
    foreign = replace(c1.PINNED, head_sha="a" * 40, tree_sha="b" * 40)
    with pytest.raises(ce.ChunkExecutionError, match="NOT complete") as refusal:
        ce.run_chunk(
            c1x.chunk_request(
                plan_path=plan_path,
                chunk_id="chunk-0000",
                attempt=attempt,
                attempt_directory=attempt_directory,
                database=database,
                tree=tree,
                repository=foreign,
            )
        )
    assert "asked to execute under repository" in str(refusal.value)
    assert not attempt_directory.exists()
    assert ce.completed_chunk_receipt(chunk_root, "chunk-0000") is None


def test_a14_a_wrong_target_interval_is_refused_before_anything_is_created(
    tmp_path: Path,
) -> None:
    """A chunk the plan does not carry, and a plan whose target interval was moved: both refuse."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    base = tmp_path / "calibration"
    base.mkdir()
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    chunk_root = base / "chunks"
    # A chunk identity outside the plan: refused by the child before an attempt directory exists.
    attempt_directory, attempt = ce.next_attempt_directory(chunk_root, "chunk-0034")
    with pytest.raises(ce.ChunkExecutionError, match="NOT complete") as refusal:
        ce.run_chunk(
            c1x.chunk_request(
                plan_path=plan_path,
                chunk_id="chunk-0034",
                attempt=attempt,
                attempt_directory=attempt_directory,
                database=database,
                tree=tree,
            )
        )
    assert "is not in this plan" in str(refusal.value)
    assert not attempt_directory.exists()
    # The target interval moved and resealed: the plan is refused when the child reads it.
    shifted = list(plan.chunks)
    shifted[0] = replace(shifted[0], end=2)
    moved_path = base / "moved.json"
    write_once_json(moved_path, _resealed(plan, chunks=tuple(shifted)))
    attempt_directory, attempt = ce.next_attempt_directory(chunk_root, "chunk-0000")
    with pytest.raises(ce.ChunkExecutionError, match="NOT complete") as refusal:
        ce.run_chunk(
            c1x.chunk_request(
                plan_path=moved_path,
                chunk_id="chunk-0000",
                attempt=attempt,
                attempt_directory=attempt_directory,
                database=database,
                tree=tree,
            )
        )
    assert "overlap" in str(refusal.value)
    assert not attempt_directory.exists()
    assert ce.completed_chunk_receipt(chunk_root, "chunk-0000") is None


# ==========================================================================
# C1016-C1020: the single-pass consolidator still refuses >9, before it reads anything
# ==========================================================================
def test_c1016_a_nine_chunk_ordinary_plan_passes_the_gate_and_consolidates(
    tmp_path: Path,
) -> None:
    """Nine is accepted at the entry gate and consolidates end to end, exactly as before."""
    database, tree = _world(tmp_path, members=6, shards=3)
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=1, label="nine")
    plan = run["plan"]
    assert plan.chunk_count == 9 and len(run["receipts"]) == 9
    assert cc.require_single_pass_plan(plan) is plan
    assert cc.require_attachable(9) == 9
    result = cc.consolidate_chunks(
        plan=plan,
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="c10-nine",
    )
    assert result.receipt.contract == FINAL_WORLD_RECEIPT_CONTRACT
    assert result.receipt.chunk_count == 9
    assert result.receipt.status == "complete"
    assert result.receipt.plan_digest == plan.plan_digest
    assert (run["base"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).is_file()


def test_c1017_c1019_c1020_a_ten_chunk_calibration_plan_is_refused_by_width_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ten chunks, none executed, no chunk root: the only reason given is the single-pass cap."""
    database, tree = _world(tmp_path, members=7, shards=3)
    plan = calibration_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 10 and plan.calibration_only
    _arm_tripwires(monkeypatch)
    internal_root = tmp_path / "chunks"
    world_directory = tmp_path / "final"
    before = _names(tmp_path)
    with pytest.raises(cc.ChunkConsolidationError, match=WIDTH_REFUSAL) as refusal:
        cc.consolidate_chunks(
            plan=plan,
            internal_root=internal_root,
            operational_catalog=database,
            world_directory=world_directory,
            run_id="c10-ten",
        )
    message = str(refusal.value)
    assert "needs 10 chunks" in message
    assert "before a database is attached" in message
    assert "missing" not in message and "receipt" not in message.split("before")[0]
    assert not internal_root.exists() and not world_directory.exists()
    assert _names(tmp_path) == before


def test_c1018_c1019_c1020_a_thirty_four_chunk_calibration_plan_is_refused_by_width_before_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    assert plan.chunk_count == 34
    _arm_tripwires(monkeypatch)
    internal_root = tmp_path / "chunks"
    world_directory = tmp_path / "final"
    before = _names(tmp_path)
    with pytest.raises(cc.ChunkConsolidationError, match=WIDTH_REFUSAL) as refusal:
        cc.consolidate_chunks(
            plan=plan,
            internal_root=internal_root,
            operational_catalog=database,
            world_directory=world_directory,
            run_id="c10-thirty-four",
        )
    assert "needs 34 chunks" in str(refusal.value)
    assert not internal_root.exists() and not world_directory.exists()
    assert _names(tmp_path) == before


def test_c1019_the_entry_refusal_is_architectural_not_the_library_limit(tmp_path: Path) -> None:
    """Thirty-four also exceeds what SQLite attaches; the gate names the architecture first."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    assert cc.attachment_limit() == 10
    # Asked of the library alone, thirty-four is a capability refusal ...
    with pytest.raises(cc.ChunkConsolidationError, match="SQLITE_LIMIT_ATTACHED = 10"):
        cc.require_attachable(34, limit=10)
    # ... but the consolidator's entry gate answers the architectural question first, so the
    # reason a calibration plan is refused does not depend on which host is consolidating.
    with pytest.raises(cc.ChunkConsolidationError, match=WIDTH_REFUSAL) as refusal:
        cc.require_single_pass_plan(plan)
    assert "SQLITE_LIMIT_ATTACHED" not in str(refusal.value)
    assert "single-pass chunked-F0 architecture admits 9" in str(refusal.value)


def test_the_consolidator_refuses_a_plan_that_is_not_its_sealed_self(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A calibration plan trimmed or relabelled in memory is refused before its width is asked."""
    database, tree = _world(tmp_path, members=33, shards=1)
    plan = calibration_plan(tree, database, chunk_members=1)
    _arm_tripwires(monkeypatch)
    trimmed = replace(plan, chunks=plan.chunks[:9], chunk_count=9, total_members=9)
    relabelled = replace(plan, contract=cp.CHUNK_PLAN_CONTRACT)
    for forged in (trimmed, relabelled):
        with pytest.raises(cp.ChunkPlanError, match="does not describe its own contents"):
            cc.consolidate_chunks(
                plan=forged,
                internal_root=tmp_path / "chunks",
                operational_catalog=database,
                world_directory=tmp_path / "final",
                run_id="c10-forged",
            )
    assert not (tmp_path / "final").exists()


def test_the_contract_line_of_defence_is_live(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the upstream invariant, and the consolidator's own source still refuses."""
    monkeypatch.setattr(cc, "require_sealed_plan", lambda plan: plan)
    monkeypatch.setattr(cc, "require_attachable", lambda width: width)
    narrow_calibration = replace(_fixed_ordinary_plan(), contract=cp.CALIBRATION_PLAN_CONTRACT)
    with pytest.raises(cc.ChunkConsolidationError, match="never consolidated"):
        cc.require_single_pass_plan(narrow_calibration)
    assert cc.require_single_pass_plan(_fixed_ordinary_plan()) is not None


def test_the_gate_runs_first_and_the_post_resolve_capability_check_survives() -> None:
    """Read from the source: the gate precedes every other call, and the second check remains."""
    source = Path(cc.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    body = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "consolidate_chunks"
    ).body
    calls = []
    for statement in body:
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call):
            callee = statement.value.func
            calls.append(callee.id if isinstance(callee, ast.Name) else ast.dump(callee))
        if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call):
            callee = statement.value.func
            calls.append(callee.id if isinstance(callee, ast.Name) else ast.dump(callee))
    assert calls[:2] == ["require_chunkable_source", "require_single_pass_plan"]
    assert calls.index("require_single_pass_plan") < calls.index("require_clean_running_repository")
    assert calls.index("require_single_pass_plan") < calls.index("resolve_chunk_inputs")
    assert "require_attachable" in calls
    assert calls.index("resolve_chunk_inputs") < calls.index("require_attachable")


def test_the_existing_width_gate_semantics_are_unchanged() -> None:
    """R33/R34/C527, restated: nine passes, ten refuses architecturally, a low library refuses."""
    assert cc.require_attachable(9, limit=10) == 9
    assert cc.require_attachable(4, limit=5) == 4
    with pytest.raises(cc.ChunkConsolidationError, match="SQLITE_LIMIT_ATTACHED = 3"):
        cc.require_attachable(4, limit=3)
    with pytest.raises(cc.ChunkConsolidationError, match="single-pass chunked-F0"):
        cc.require_attachable(10, limit=10)
    source = Path(cc.__file__).read_text(encoding="utf-8")
    for absent in ("two_level", "multi_pass", "second_pass", "def _merge_pass"):
        assert absent not in source, absent


# ==========================================================================
# C1021-C1025, A15: nothing is opened
# ==========================================================================
def test_c1021_c1022_c1023_every_activation_and_capacity_constant_remains_none() -> None:
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY is None
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    assert cs.INTERNAL_RESERVE_BYTES is None
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None
    with pytest.raises(ce.ChunkExecutionError, match="NOT AUTHORIZED"):
        ce.require_real_chunk_execution_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    with pytest.raises(cp.ChunkPlanError, match="never defaulted"):
        cp.production_chunk_members()


def test_c1024_a15_no_cli_environment_or_configuration_route_reaches_the_capability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nothing to type, nothing to set: the calibration builder has no caller under ``src``."""
    from disclosure_drift import cli

    cli_source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in ("calibration", "chunk_plan", "chunk_consolidation", "chunk_execution"):
        assert name not in cli_source, name
    package_root = Path(cli.__file__).parent
    callers = [
        path.name
        for path in sorted(package_root.rglob("*.py"))
        if path.name != "chunk_plan.py"
        and "build_calibration_chunk_plan" in path.read_text(encoding="utf-8")
    ]
    assert callers == []
    for module in (cp, cc):
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "environ" not in names and "environ" not in attributes, module.__name__
        assert "getenv" not in names and "getenv" not in attributes, module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "load_config" not in names, module.__name__
        assigned = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign | ast.AnnAssign)
            for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            if isinstance(target, ast.Name)
        }
        assert not {name for name in assigned if "AUTHORITY" in name}, module.__name__
    # A15: an environment value that merely LOOKS like an authority opens nothing.
    monkeypatch.setenv("DISCLOSURE_DRIFT_CHUNKED_F0_AUTHORITY", "granted")
    monkeypatch.setenv("DISCLOSURE_DRIFT_CALIBRATION_PLAN", "granted")
    with pytest.raises(ce.ChunkExecutionError, match="NOT AUTHORIZED"):
        ce.require_real_chunk_execution_authority()
    assert cp.CALIBRATION_CHUNK_CEILING == 34


def test_c1025_no_migration_0016_exists() -> None:
    import importlib

    from disclosure_drift.storage.sqlite import available_migrations

    migrations = available_migrations()
    assert migrations[-1].version == 15
    directory = Path(importlib.import_module("disclosure_drift.storage.migrations").__file__).parent
    assert not list(directory.glob("0016_*.sql"))
    for module in (cp, cc):
        assert "apply_migrations" not in Path(module.__file__).read_text(encoding="utf-8")
