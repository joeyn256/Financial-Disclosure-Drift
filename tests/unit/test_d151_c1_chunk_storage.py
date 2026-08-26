"""D151-C1: the internal-hot / external-spill tier, its capacity floor, and its reclaim gate.

Four claims carry this module, and each is proved against a world built to break it:

**Capacity is a precondition.** The runtime never waits for ``ENOSPC``. Before the next chunk
starts, internal free space must be at least the accepted reserve plus the projected peak of the
chunk about to run, and a ``None`` reserve **refuses** rather than contributing zero.

**A transfer is proved, not attempted.** Every object is copied and hashed as it is written, then
independently re-read and re-hashed from the destination, then compared to the source manifest,
and only then is the transfer receipt written -- LAST. A truncated copy, a same-length copy with
different bytes, and an extra object all fail before any receipt exists.

**State is derived from durable evidence.** No status file decides anything: a chunk's placement
is recomputed by re-reading and re-hashing objects on both tiers, and two copies that disagree
are refused rather than resolved.

**Nothing is deleted.** Reclaim eligibility is a computation. The module holds no deletion
capability at all, which is asserted against its own source text, and its authority constant is
``None``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_FILENAME,
    TRANSFER_RECEIPT_FILENAME,
    ChunkEvidenceError,
)
from disclosure_drift.m3.external_working_root import QUALIFIED_EXTERNAL_VOLUME_UUID  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

SYNTHETIC_VOLUME = "00000000-0000-0000-0000-0000C1C1C1C1"


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin: since D151-C5 every chunk child authenticates its own code identity."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, DataTree]:
    return c1.build_world(tmp_path, members=6, filings=2, shards=2)


@pytest.fixture
def completed(tmp_path: Path, world: tuple[Path, DataTree]) -> dict[str, object]:
    """A complete chunk set on the internal tier, and nothing on the external one."""
    database, tree = world
    return c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=2)


def _internal_directory(run: dict[str, object], chunk_id: str) -> Path:
    from disclosure_drift.m3.chunk_execution import completed_chunk_receipt

    found = completed_chunk_receipt(run["chunk_root"], chunk_id)  # type: ignore[index]
    assert found is not None
    return found[1]


# ==========================================================================
# C25, C26, A16, A17, A47, A48: the capacity floor
# ==========================================================================
def test_c25_c26_the_floor_is_reserve_plus_projected_peak() -> None:
    admitted = cs.require_capacity_for_next_chunk(
        free_bytes=300, reserve_bytes=100, projected_peak_bytes=200
    )
    assert admitted.admitted
    assert admitted.required_bytes == 300
    with pytest.raises(cs.ChunkStorageError, match="NOT ADMITTED"):
        cs.require_capacity_for_next_chunk(
            free_bytes=299, reserve_bytes=100, projected_peak_bytes=200
        )


def test_a48_a_none_reserve_is_a_refusal_and_never_a_zero() -> None:
    """A48: zero would satisfy every comparison and turn the floor into decoration."""
    assert cs.INTERNAL_RESERVE_BYTES is None
    with pytest.raises(cs.ChunkStorageError, match="never a zero reserve"):
        cs.accepted_internal_reserve_bytes()
    with pytest.raises(cs.ChunkStorageError, match="never a zero reserve"):
        cs.require_capacity_for_next_chunk(free_bytes=1 << 60, projected_peak_bytes=1)


def test_an_unknown_projection_is_a_refusal_and_never_a_zero() -> None:
    with pytest.raises(cs.ChunkStorageError, match="REFUSAL, never a zero"):
        cs.require_capacity_for_next_chunk(
            free_bytes=1 << 60, reserve_bytes=0, projected_peak_bytes=None
        )


def test_the_frozen_chunk_peak_requirement_is_closed() -> None:
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None


def test_a47_the_capacity_arithmetic_cannot_wrap() -> None:
    """A47: Python integers are arbitrary precision, so the sum is exact at any magnitude."""
    huge = 2**80
    with pytest.raises(cs.ChunkStorageError, match="NOT ADMITTED"):
        cs.require_capacity_for_next_chunk(
            free_bytes=huge, reserve_bytes=huge, projected_peak_bytes=huge
        )
    decision = cs.require_capacity_for_next_chunk(
        free_bytes=2 * huge, reserve_bytes=huge, projected_peak_bytes=huge
    )
    assert decision.required_bytes == 2 * huge


@pytest.mark.parametrize(("free", "reserve", "peak"), [(-1, 0, 0), (0, -1, 0), (0, 0, -1)])
def test_negative_byte_quantities_are_refused(free: int, reserve: int, peak: int) -> None:
    with pytest.raises(cs.ChunkStorageError, match="non-negative"):
        cs.require_capacity_for_next_chunk(
            free_bytes=free, reserve_bytes=reserve, projected_peak_bytes=peak
        )


def test_the_projection_is_measured_from_completed_chunks(completed: dict[str, object]) -> None:
    """A projection from nothing is a guess, and a guess is what the floor may not rest on."""
    from disclosure_drift.m3.chunk_plan import ChunkPlan

    plan = completed["plan"]
    assert isinstance(plan, ChunkPlan)
    placements = cs.derive_placements(plan, internal_root=completed["chunk_root"])  # type: ignore[arg-type]
    projected = cs.projected_next_chunk_peak_bytes(placements)
    assert projected is not None
    assert projected == max(placement.internal_bytes or 0 for placement in placements)
    assert cs.projected_next_chunk_peak_bytes(()) is None
    assert cs.projected_next_chunk_peak_bytes(placements, headroom_ratio=2.0) == 2 * projected
    with pytest.raises(cs.ChunkStorageError, match="below 1.0"):
        cs.projected_next_chunk_peak_bytes(placements, headroom_ratio=0.5)


def test_a16_a17_below_the_floor_the_next_chunk_does_not_start(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """A16/A17: the gate runs BEFORE the chunk, and a refusal creates nothing and frees nothing."""
    from disclosure_drift.m3.chunk_execution import attempt_directory

    plan = completed["plan"]
    root = completed["chunk_root"]
    placements = cs.derive_placements(plan, internal_root=root)  # type: ignore[arg-type]
    projected = cs.projected_next_chunk_peak_bytes(placements)
    assert projected is not None
    next_chunk = "chunk-9999"
    target = attempt_directory(root, next_chunk, 0)  # type: ignore[arg-type]
    with pytest.raises(cs.ChunkStorageError, match="does not start"):
        cs.require_capacity_for_next_chunk(
            free_bytes=projected - 1, reserve_bytes=0, projected_peak_bytes=projected
        )
        target.mkdir(parents=True)
    assert not target.exists()
    # And every already-completed chunk is untouched: nothing was evacuated to clear the floor.
    assert cs.derive_placements(plan, internal_root=root) == placements  # type: ignore[arg-type]


# ==========================================================================
# C21-C23, A12-A15, A19-A20: transfer and reclaim
# ==========================================================================
def test_c21_the_transfer_receipt_is_written_last_and_the_copy_verifies(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    source = _internal_directory(completed, "chunk-0000")
    destination = tmp_path / "external" / "chunk-0000"
    receipt = cs.transfer_chunk(
        source_directory=source,
        destination_directory=destination,
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    assert receipt.status == "verified"
    assert (destination / TRANSFER_RECEIPT_FILENAME).is_file()
    named = {entry.relative_path for entry in receipt.destination_manifest.entries}
    assert TRANSFER_RECEIPT_FILENAME not in named
    assert CHUNK_RECEIPT_FILENAME not in named
    assert (destination / CHUNK_RECEIPT_FILENAME).read_bytes() == (
        source / CHUNK_RECEIPT_FILENAME
    ).read_bytes()
    for entry in receipt.destination_manifest.entries:
        assert (destination / entry.relative_path).read_bytes() == (
            source / entry.relative_path
        ).read_bytes()


def test_a_transfer_onto_an_unidentified_volume_is_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    source = _internal_directory(completed, "chunk-0000")
    with pytest.raises(cs.ChunkStorageError, match="could not be identified"):
        cs.transfer_chunk(
            source_directory=source,
            destination_directory=tmp_path / "external" / "chunk-0000",
            destination_volume_uuid=None,
        )
    assert not (tmp_path / "external" / "chunk-0000").exists()


def test_c50_a39_a_transfer_onto_the_qualified_volume_is_closed(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """C50/A39: real transfer authority is None, so the real destination refuses."""
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    source = _internal_directory(completed, "chunk-0000")
    destination = tmp_path / "external" / "chunk-0000"
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.transfer_chunk(
            source_directory=source,
            destination_directory=destination,
            destination_volume_uuid=QUALIFIED_EXTERNAL_VOLUME_UUID,
        )
    assert not destination.exists()


def test_a_transfer_of_an_altered_chunk_is_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """A11: a chunk altered after completion never becomes a durable copy."""
    source = _internal_directory(completed, "chunk-0000")
    (source / "chunk_witness.sqlite3").write_bytes(b"tampered")
    with pytest.raises(ChunkEvidenceError, match="IMMUTABLE"):
        cs.transfer_chunk(
            source_directory=source,
            destination_directory=tmp_path / "external" / "chunk-0000",
            destination_volume_uuid=SYNTHETIC_VOLUME,
        )


def test_a_destination_that_already_exists_is_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    source = _internal_directory(completed, "chunk-0000")
    destination = tmp_path / "external" / "chunk-0000"
    destination.mkdir(parents=True)
    with pytest.raises(cs.ChunkStorageError, match="create-once"):
        cs.transfer_chunk(
            source_directory=source,
            destination_directory=destination,
            destination_volume_uuid=SYNTHETIC_VOLUME,
        )


def _transfer(tmp_path: Path, completed: dict[str, object], chunk_id: str) -> Path:
    destination = tmp_path / "external" / chunk_id
    cs.transfer_chunk(
        source_directory=_internal_directory(completed, chunk_id),
        destination_directory=destination,
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    return destination


def test_a12_a_truncated_external_copy_is_not_a_verified_copy(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    destination = _transfer(tmp_path, completed, "chunk-0000")
    target = destination / "chunk_witness.sqlite3"
    target.write_bytes(target.read_bytes()[:-16])
    with pytest.raises(ChunkEvidenceError, match="does not match the manifest"):
        cs.derive_chunk_placement(
            completed["plan"],  # type: ignore[arg-type]
            "chunk-0000",
            internal_root=completed["chunk_root"],  # type: ignore[arg-type]
            external_root=tmp_path / "external",
        )


def test_a13_a_same_length_external_copy_with_different_bytes_is_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    destination = _transfer(tmp_path, completed, "chunk-0000")
    target = destination / "chunk_witness.sqlite3"
    original = bytearray(target.read_bytes())
    original[-1] = (original[-1] + 1) % 256
    target.write_bytes(bytes(original))
    with pytest.raises(ChunkEvidenceError, match="does not match the manifest"):
        cs.derive_chunk_placement(
            completed["plan"],  # type: ignore[arg-type]
            "chunk-0000",
            internal_root=completed["chunk_root"],  # type: ignore[arg-type]
            external_root=tmp_path / "external",
        )


def test_a22_a_partial_external_transfer_carries_no_receipt(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """C22: a directory holding some of a chunk's objects is not a durable copy."""
    source = _internal_directory(completed, "chunk-0000")
    destination = tmp_path / "external" / "chunk-0000"
    destination.mkdir(parents=True)
    (destination / "working_catalog.sqlite3").write_bytes(
        (source / "working_catalog.sqlite3").read_bytes()
    )
    placement = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
        external_root=tmp_path / "external",
    )
    assert placement.state == cs.STATE_COMPLETE_INTERNAL
    assert not placement.has_verified_external


def test_c17_an_internal_only_chunk_is_a_valid_input(completed: dict[str, object]) -> None:
    placement = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
    )
    assert placement.state == cs.STATE_COMPLETE_INTERNAL
    directory, tier = cs.authoritative_input(placement)
    assert tier == cs.TIER_INTERNAL
    assert directory == _internal_directory(completed, "chunk-0000")


def test_c18_a_verified_external_only_chunk_is_a_valid_input(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """C18: the external copy alone is admissible once it verifies."""
    destination = _transfer(tmp_path, completed, "chunk-0000")
    empty_internal = tmp_path / "no-internal"
    empty_internal.mkdir()
    placement = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=empty_internal,
        external_root=tmp_path / "external",
    )
    assert placement.state == cs.STATE_INTERNAL_RECLAIMED
    directory, tier = cs.authoritative_input(placement)
    assert tier == cs.TIER_EXTERNAL
    assert directory == destination


def test_c19_identical_dual_copies_resolve_deterministically(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """C19/§22: which physical copy is read is policy; the logical identity is not."""
    _transfer(tmp_path, completed, "chunk-0000")
    placement = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
        external_root=tmp_path / "external",
    )
    assert placement.state == cs.STATE_INTERNAL_RECLAIM_ELIGIBLE
    assert placement.internal_receipt is not None
    assert placement.external_receipt is not None
    assert placement.internal_receipt.manifest.digest == placement.external_receipt.manifest.digest
    directory, tier = cs.authoritative_input(placement)
    assert tier == cs.TIER_INTERNAL
    assert directory == _internal_directory(completed, "chunk-0000")


def test_c20_a14_a15_conflicting_dual_copies_are_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """C20/A14/A15: disagreement is reported, never resolved by tier, speed, or recency."""
    destination = _transfer(tmp_path, completed, "chunk-0000")
    receipt_path = destination / CHUNK_RECEIPT_FILENAME
    import json

    forged = json.loads(receipt_path.read_text())
    forged["end"] = forged["end"] + 1
    receipt_path.write_text(json.dumps(forged))
    with pytest.raises(cs.ChunkStorageError, match="two copies that disagree on end"):
        cs.derive_chunk_placement(
            completed["plan"],  # type: ignore[arg-type]
            "chunk-0000",
            internal_root=completed["chunk_root"],  # type: ignore[arg-type]
            external_root=tmp_path / "external",
        )


def test_a_transfer_receipt_bound_to_another_manifest_is_refused(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """A15: an unverified external copy never wins by having a receipt beside it."""
    import json

    destination = _transfer(tmp_path, completed, "chunk-0000")
    path = destination / TRANSFER_RECEIPT_FILENAME
    document = json.loads(path.read_text())
    document["chunk_receipt_manifest_digest"] = "0" * 64
    path.write_text(json.dumps(document))
    with pytest.raises(cs.ChunkStorageError, match="binds artifact manifest"):
        cs.derive_chunk_placement(
            completed["plan"],  # type: ignore[arg-type]
            "chunk-0000",
            internal_root=completed["chunk_root"],  # type: ignore[arg-type]
            external_root=tmp_path / "external",
        )


# ==========================================================================
# C23, C24, A19, A20: reclaim
# ==========================================================================
def test_c23_reclaim_eligibility_requires_a_verified_external_copy(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """A19/A20: without an external copy the internal one may be the only verified copy."""
    internal_only = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
    )
    plan = cs.internal_reclaim_plan(internal_only)
    assert not plan.eligible
    assert plan.objects == ()
    assert plan.bytes_reclaimable == 0
    assert plan.proofs["external_copy_exists"] is False

    _transfer(tmp_path, completed, "chunk-0000")
    both = cs.derive_chunk_placement(
        completed["plan"],  # type: ignore[arg-type]
        "chunk-0000",
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
        external_root=tmp_path / "external",
    )
    eligible = cs.internal_reclaim_plan(both)
    assert eligible.eligible
    assert all(eligible.proofs.values())
    assert eligible.objects
    assert eligible.bytes_reclaimable > 0


def test_c24_no_real_reclaim_authority_and_no_deletion_capability() -> None:
    """C24/A49: the constant is None, and the module holds nothing for it to enable."""
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    source = Path(cs.__file__).read_text(encoding="utf-8")
    for capability in ("unlink", "rmtree", "os.remove", "rmdir", "shutil.move"):
        assert capability not in source, capability
    # `shutil` is present for exactly one call, and it is a measurement.
    assert set(re.findall(r"shutil\.\w+", source)) == {"shutil.disk_usage"}


def test_no_c1_module_can_delete_anything() -> None:
    """The same guarantee, across the whole C1 surface."""
    from disclosure_drift.m3 import (
        chunk_consolidation,
        chunk_evidence,
        chunk_execution,
        chunk_plan,
    )

    for module in (chunk_plan, chunk_evidence, chunk_execution, chunk_storage_module()):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for capability in ("shutil.rmtree", "os.remove(", "os.rmdir(", ".unlink("):
            assert capability not in source, (module.__name__, capability)
    source = Path(chunk_consolidation.__file__).read_text(encoding="utf-8")
    for capability in ("shutil.rmtree", "os.remove(", "os.rmdir(", ".unlink("):
        assert capability not in source, capability


def chunk_storage_module() -> object:
    from disclosure_drift.m3 import chunk_storage

    return chunk_storage


# ==========================================================================
# C27, A18: deterministic spill selection
# ==========================================================================
def test_c27_a18_spill_selection_is_canonical_plan_order(completed: dict[str, object]) -> None:
    """C27/A18: never filesystem order, never mtime, never size, never an operator's pick."""
    plan = completed["plan"]
    placements = cs.derive_placements(plan, internal_root=completed["chunk_root"])  # type: ignore[arg-type]
    total = sum(placement.internal_bytes or 0 for placement in placements)
    first = cs.select_spill_candidates(placements, needed_bytes=1)
    assert [placement.chunk_id for placement in first] == [plan.chunks[0].chunk_id]  # type: ignore[index]
    # Presented in reverse, the selection is unchanged: the rule reads the plan, not the list.
    reversed_order = cs.select_spill_candidates(tuple(reversed(placements)), needed_bytes=1)
    assert [placement.chunk_id for placement in reversed_order] == [placements[-1].chunk_id]
    everything = cs.select_spill_candidates(placements, needed_bytes=total)
    assert [placement.chunk_id for placement in everything] == [
        bounds.chunk_id
        for bounds in plan.chunks  # type: ignore[union-attr]
    ]


def test_a_spill_that_cannot_release_enough_is_refused(completed: dict[str, object]) -> None:
    placements = cs.derive_placements(
        completed["plan"],
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
    )
    with pytest.raises(cs.ChunkStorageError, match="does not start"):
        cs.select_spill_candidates(placements, needed_bytes=1 << 50)
    with pytest.raises(cs.ChunkStorageError, match="non-negative"):
        cs.select_spill_candidates(placements, needed_bytes=-1)


def test_only_a_completed_internal_chunk_is_eligible_to_spill(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    _transfer(tmp_path, completed, "chunk-0000")
    placements = cs.derive_placements(
        completed["plan"],  # type: ignore[arg-type]
        internal_root=completed["chunk_root"],  # type: ignore[arg-type]
        external_root=tmp_path / "external",
    )
    assert placements[0].state == cs.STATE_INTERNAL_RECLAIM_ELIGIBLE
    selected = cs.select_spill_candidates(placements, needed_bytes=1)
    assert selected[0].chunk_id != placements[0].chunk_id


# ==========================================================================
# The derived state machine
# ==========================================================================
def test_the_states_derive_from_evidence_rather_than_from_a_status_file(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=2, stop_after=1)
    plan = run["plan"]
    started = cs.derive_chunk_placement(
        plan, plan.chunks[0].chunk_id, internal_root=run["chunk_root"]
    )
    assert started.state == cs.STATE_COMPLETE_INTERNAL
    untouched = cs.derive_chunk_placement(
        plan, plan.chunks[-1].chunk_id, internal_root=run["chunk_root"]
    )
    assert untouched.state == cs.STATE_PLANNED
    # An attempt that began and never finished is RUNNING, derived from the absent receipt.
    directory = run["chunk_root"] / plan.chunks[-1].chunk_id / "attempt-000"
    directory.mkdir(parents=True)
    running = cs.derive_chunk_placement(
        plan, plan.chunks[-1].chunk_id, internal_root=run["chunk_root"]
    )
    assert running.state == cs.STATE_RUNNING_INTERNAL
    assert cs.CHUNK_STORAGE_STATES == (
        cs.STATE_PLANNED,
        cs.STATE_RUNNING_INTERNAL,
        cs.STATE_COMPLETE_INTERNAL,
        cs.STATE_TRANSFER_VERIFIED_EXTERNAL,
        cs.STATE_INTERNAL_RECLAIM_ELIGIBLE,
        cs.STATE_INTERNAL_RECLAIMED,
    )


def test_a_verified_transfer_never_removes_the_internal_copy(
    tmp_path: Path, completed: dict[str, object]
) -> None:
    """§11: a valid external transfer does NOT automatically delete the internal copy."""
    internal = _internal_directory(completed, "chunk-0000")
    before = sorted(path.name for path in internal.iterdir())
    _transfer(tmp_path, completed, "chunk-0000")
    assert sorted(path.name for path in internal.iterdir()) == before
