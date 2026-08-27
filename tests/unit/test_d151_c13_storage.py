"""D151-C13: storage risk is load-bearing -- admission, lifecycle, spill seam, qualification.

The owner's tiered-storage addendum states a future model; this module proves the model's
mechanics refuse correctly today. Every owner term is ``None`` and ``None`` refuses: a real
multipass consolidation is NOT ADMISSIBLE, before the plan is read and before any directory
exists. The admission arithmetic admits at the floor and refuses one byte below it. The lifecycle
is monotonic, a transfer never implies a reclaim, an unqualified tier refuses, an accepted ``/1``
transfer receipt is not reclaim evidence, and no reclaim is ever authorized. Every input of a
multipass consolidation is retained: nothing here can delete, and the storage plan credits
nothing it would have to delete to obtain.
"""

from __future__ import annotations

import inspect
import json
import sys
from dataclasses import replace
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
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_FILENAME,
    TRANSFER_RECEIPT_FILENAME,
    verify_artifact_manifest,
)

SYNTHETIC_VOLUME = "00000000-0000-0000-0000-0000C1C1C1C1"


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    patcher.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# T01, T02: durable lifecycle states and monotonic, evidence-backed transitions
# ==========================================================================
def test_t01_the_lifecycle_is_monotonic_and_forbids_complete_to_reclaimed() -> None:
    assert ct.ARTIFACT_LIFECYCLE_STATES == (
        "INTERNAL_COMPLETE",
        "SSD_COPY_IN_PROGRESS",
        "SSD_COPY_VERIFIED",
        "INTERNAL_RECLAIM_ELIGIBLE",
        "INTERNAL_RECLAIMED",
    )
    order = {state: index for index, state in enumerate(ct.ARTIFACT_LIFECYCLE_STATES)}
    for current, targets in ct.LIFECYCLE_TRANSITIONS.items():
        for target in targets:
            assert order[target] > order[current], (current, target)
    assert (
        ct.LIFECYCLE_INTERNAL_RECLAIMED
        not in ct.LIFECYCLE_TRANSITIONS[ct.LIFECYCLE_INTERNAL_COMPLETE]
    )
    assert ct.LIFECYCLE_TRANSITIONS[ct.LIFECYCLE_INTERNAL_RECLAIMED] == frozenset()
    full = ct.LifecycleEvidence(
        external_tier_qualified=True,
        transfer_authority="synthetic",
        external_copy_verified=True,
        transfer_receipt_bindings_complete=True,
        reclaim_authority="synthetic",
    )
    with pytest.raises(ct.ChunkTieringError, match="never reaches INTERNAL_RECLAIMED"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_INTERNAL_COMPLETE, ct.LIFECYCLE_INTERNAL_RECLAIMED, full
        )
    with pytest.raises(ct.ChunkTieringError, match="not an edge"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED, ct.LIFECYCLE_INTERNAL_COMPLETE, full
        )
    with pytest.raises(ct.ChunkTieringError, match="does not have"):
        ct.require_lifecycle_transition("INTERNAL_COMPLETE", "SOMEWHERE", full)
    # Every edge admits under full evidence, one step at a time.
    for current, targets in ct.LIFECYCLE_TRANSITIONS.items():
        for target in targets:
            assert ct.require_lifecycle_transition(current, target, full) == target


def test_t01_every_edge_needs_its_own_evidence_and_a_transfer_never_implies_a_reclaim() -> None:
    none = ct.LifecycleEvidence()
    with pytest.raises(ct.ChunkTieringError, match="QUALIFIED external tier"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_INTERNAL_COMPLETE, ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, none
        )
    qualified = replace(none, external_tier_qualified=True)
    with pytest.raises(ct.ChunkTieringError, match="transfer authority"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_INTERNAL_COMPLETE, ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, qualified
        )
    authorized = replace(qualified, transfer_authority="synthetic")
    assert (
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_INTERNAL_COMPLETE, ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, authorized
        )
        == ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS
    )
    with pytest.raises(ct.ChunkTieringError, match="not verified merely because it completed"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED, authorized
        )
    verified = replace(authorized, external_copy_verified=True)
    with pytest.raises(ct.ChunkTieringError, match="not RECLAIM-ELIGIBLE"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED, ct.LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE, verified
        )
    eligible = replace(verified, transfer_receipt_bindings_complete=True)
    assert (
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED, ct.LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE, eligible
        )
        == ct.LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE
    )
    # The transfer authority is present and the copy is verified: STILL not a reclaim.
    with pytest.raises(ct.ChunkTieringError, match="never implies a deletion"):
        ct.require_lifecycle_transition(
            ct.LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE, ct.LIFECYCLE_INTERNAL_RECLAIMED, eligible
        )


def test_t02_the_lifecycle_derives_from_durable_evidence(tmp_path: Path) -> None:
    database, tree, run = c13i.ten_chunk_run(tmp_path)
    plan = run["plan"]
    placement = cs.derive_chunk_placement(plan, "chunk-0000", internal_root=run["chunk_root"])
    assert (
        ct.derive_artifact_lifecycle(placement, external_root=None)
        == ct.LIFECYCLE_INTERNAL_COMPLETE
    )
    external = tmp_path / "external"
    # A partial copy: an external directory with no verified transfer receipt is IN PROGRESS.
    (external / "chunk-0000").mkdir(parents=True)
    source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0000")[1]
    (external / "chunk-0000" / "working_catalog.sqlite3").write_bytes(
        (source / "working_catalog.sqlite3").read_bytes()
    )
    placement = cs.derive_chunk_placement(
        plan, "chunk-0000", internal_root=run["chunk_root"], external_root=external
    )
    assert placement.state == cs.STATE_COMPLETE_INTERNAL
    assert ct.derive_artifact_lifecycle(placement, external_root=external) == (
        ct.LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS
    )
    # A verified copy (a synthetic, unqualified volume): VERIFIED, not eligible.
    other_source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0001")[1]
    cs.transfer_chunk(
        source_directory=other_source,
        destination_directory=external / "chunk-0001",
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    verified = cs.derive_chunk_placement(
        plan, "chunk-0001", internal_root=run["chunk_root"], external_root=external
    )
    assert verified.state == cs.STATE_INTERNAL_RECLAIM_ELIGIBLE
    assert ct.derive_artifact_lifecycle(verified, external_root=external) == (
        ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED
    )
    planned = cs.derive_chunk_placement(plan, "chunk-0009", internal_root=tmp_path / "nowhere")
    with pytest.raises(ct.ChunkTieringError, match="not a completed artifact"):
        ct.derive_artifact_lifecycle(planned, external_root=None)
    assert tree is not None and database is not None


# ==========================================================================
# T03, T04: the transfer receipt bindings and reclaim eligibility
# ==========================================================================
def _complete_transfer_record() -> dict[str, object]:
    record: dict[str, object] = {
        name: f"synthetic-{name}" for name in ct.TRANSFER_RECEIPT_REQUIRED_BINDINGS
    }
    record.update(
        {
            "source_bytes": 10,
            "destination_bytes": 10,
            "destination_manifest_verified": True,
            "destination_content_verified": True,
            "transfer_outcome": "verified",
        }
    )
    return record


def test_t03_the_accepted_transfer_receipt_is_verification_evidence_not_reclaim_evidence(
    tmp_path: Path,
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0000")[1]
    receipt = cs.transfer_chunk(
        source_directory=source,
        destination_directory=tmp_path / "external" / "chunk-0000",
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    bindings = ct.transfer_receipt_bindings_of(receipt)
    missing = [name for name in ct.TRANSFER_RECEIPT_REQUIRED_BINDINGS if name not in bindings]
    assert set(missing) >= {
        "source_receipt_sha256",
        "source_bytes",
        "source_repository_head_sha",
        "source_repository_tree_sha",
        "destination_canonical_path",
        "transfer_started_at_utc",
    }
    with pytest.raises(ct.ChunkTieringError, match="does not bind"):
        ct.require_transfer_receipt_bindings(bindings)
    complete = _complete_transfer_record()
    assert ct.require_transfer_receipt_bindings(complete) is complete
    for name in ct.TRANSFER_RECEIPT_REQUIRED_BINDINGS:
        for hole in (None, ""):
            with pytest.raises(ct.ChunkTieringError, match="does not bind"):
                ct.require_transfer_receipt_bindings({**complete, name: hole})
    with pytest.raises(ct.ChunkTieringError, match="only a 'verified' outcome"):
        ct.require_transfer_receipt_bindings({**complete, "transfer_outcome": "copied"})
    with pytest.raises(ct.ChunkTieringError, match="True is required"):
        ct.require_transfer_receipt_bindings({**complete, "destination_content_verified": 1})
    assert database is not None


def test_t04_a23_reclaim_is_computed_and_never_performed(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    plan = run["plan"]
    external = tmp_path / "external"
    source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0000")[1]
    before = sorted(path.name for path in source.iterdir())
    internal_only = cs.derive_chunk_placement(plan, "chunk-0000", internal_root=run["chunk_root"])
    eligibility = ct.reclaim_eligibility(internal_only, transfer_record=None)
    assert not eligibility.eligible and eligibility.reclaim_authority is None
    assert eligibility.proofs["external_copy_verified"] is False
    with pytest.raises(ct.ChunkTieringError, match="not RECLAIM-ELIGIBLE"):
        ct.require_internal_reclaim(eligibility)
    receipt = cs.transfer_chunk(
        source_directory=source,
        destination_directory=external / "chunk-0000",
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    both = cs.derive_chunk_placement(
        plan, "chunk-0000", internal_root=run["chunk_root"], external_root=external
    )
    # The accepted /1 receipt: verified copy, but not eligible under the addendum.
    with_accepted = ct.reclaim_eligibility(
        both, transfer_record=ct.transfer_receipt_bindings_of(receipt), external_root=external
    )
    assert with_accepted.lifecycle == ct.LIFECYCLE_EXTERNAL_COPY_VERIFIED
    assert not with_accepted.eligible
    assert with_accepted.proofs["transfer_receipt_bindings_complete"] is False
    assert with_accepted.proofs["external_copy_verified"] is True
    # A complete future record: ELIGIBLE, and still refused, because the authority is None.
    with_complete = ct.reclaim_eligibility(
        both, transfer_record=_complete_transfer_record(), external_root=external
    )
    assert with_complete.eligible and all(with_complete.proofs.values())
    with pytest.raises(ct.ChunkTieringError, match="NOT AUTHORIZED"):
        ct.require_internal_reclaim(with_complete)
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()
    assert sorted(path.name for path in source.iterdir()) == before
    assert (external / "chunk-0000" / TRANSFER_RECEIPT_FILENAME).is_file()
    assert json.loads(json.dumps(dict(with_complete.as_record())))["eligible"] is True
    assert database is not None


# ==========================================================================
# T05: the qualification predicate takes no path
# ==========================================================================
def test_t05_no_external_tier_is_qualified_and_none_is_inferred_from_a_path() -> None:
    assert ct.QUALIFIED_EXTERNAL_TIER is None
    candidate = ct.ExternalTierQualification(
        volume_identity="397A4D4A-9508-391E-814E-3B533C7BD049",
        filesystem="ExFAT",
        physical_topology="USB_VIA_THUNDERBOLT_DOCK",
        mount_identity="/Volumes/SSK",
        writable_capacity_bytes=1 << 40,
        sustained_copy_bytes_per_second=400_000_000,
        sustained_read_bytes_per_second=400_000_000,
        round_trip_verified=True,
        disconnect_semantics="fail-closed",
        qualified_by="nobody",
    )
    assert ct.external_tier_is_qualified(candidate) is False
    assert ct.external_tier_is_qualified(None) is False
    with pytest.raises(ct.ChunkTieringError, match="no external tier is qualified"):
        ct.require_qualified_external_tier(candidate)
    with pytest.raises(ct.ChunkTieringError, match="no external tier is qualified"):
        ct.require_qualified_external_tier(None)
    for function in (ct.external_tier_is_qualified, ct.require_qualified_external_tier):
        parameters = inspect.signature(function).parameters
        assert list(parameters) == ["candidate"]
        assert "Path" not in str(parameters["candidate"].annotation)
    assert set(candidate.as_record()) >= {
        "volume_identity",
        "filesystem",
        "physical_topology",
        "mount_identity",
        "writable_capacity_bytes",
        "sustained_copy_bytes_per_second",
        "round_trip_verified",
        "disconnect_semantics",
    }


# ==========================================================================
# T06, T07, A22: admission arithmetic, None refusals, the storage plan
# ==========================================================================
def _requirements(**changes: Any) -> ct.MultipassStorageRequirements:
    base = {
        "internal_reserve_bytes": 100,
        "level_one_peak_ratio": 1.5,
        "level_two_peak_ratio": 2.0,
        "level_one_transient_bytes": 7,
        "level_two_transient_bytes": 11,
    }
    base.update(changes)
    return ct.MultipassStorageRequirements(**base)


def test_t06_the_floor_admits_exactly_and_one_byte_below_refuses() -> None:
    requirement = ct.merge_step_requirement(
        step="group-0000",
        level=ct.MERGE_LEVEL_ONE,
        input_bytes=1000,
        seed_catalog_bytes=50,
        peak_ratio=1.5,
        requirements=_requirements(),
    )
    assert requirement.peak_bytes == 1550 and requirement.required_free_bytes == 1550 + 100 + 7
    floor = requirement.required_free_bytes
    assert ct.require_merge_admission(free_bytes=floor, requirement=requirement).admitted
    assert ct.require_merge_admission(free_bytes=floor + 1, requirement=requirement).admitted
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMITTED"):
        ct.require_merge_admission(free_bytes=floor - 1, requirement=requirement)
    with pytest.raises(ct.ChunkTieringError, match="non-negative"):
        ct.require_merge_admission(free_bytes=-1, requirement=requirement)
    # ceil(): a fractional product rounds UP, never down.
    odd = ct.merge_step_requirement(
        step="x",
        level=ct.MERGE_LEVEL_ONE,
        input_bytes=7,
        seed_catalog_bytes=0,
        peak_ratio=1.5,
        requirements=_requirements(),
    )
    assert odd.peak_bytes == 11
    with pytest.raises(ct.ChunkTieringError, match="non-negative"):
        ct.merge_step_requirement(
            step="x",
            level=ct.MERGE_LEVEL_ONE,
            input_bytes=-1,
            seed_catalog_bytes=0,
            peak_ratio=1.0,
            requirements=_requirements(),
        )
    huge = 2**80
    assert (
        ct.merge_step_requirement(
            step="x",
            level=ct.MERGE_LEVEL_ONE,
            input_bytes=huge,
            seed_catalog_bytes=0,
            peak_ratio=1.0,
            requirements=_requirements(internal_reserve_bytes=huge),
        ).required_free_bytes
        == 2 * huge + 7
    )


def test_t06_a22_none_terms_refuse_and_are_never_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE") as refusal:
        ct.accepted_multipass_storage_requirements()
    assert "never a zero reserve" in str(refusal.value)
    # With a reserve frozen and the ratios still None, the ratios refuse next.
    monkeypatch.setattr(cs, "INTERNAL_RESERVE_BYTES", 1 << 30)
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE") as refusal:
        ct.accepted_multipass_storage_requirements()
    assert "MULTIPASS_LEVEL_ONE_PEAK_RATIO" in str(refusal.value)
    for name in ("MULTIPASS_LEVEL_ONE_PEAK_RATIO", "MULTIPASS_LEVEL_TWO_PEAK_RATIO"):
        monkeypatch.setattr(ct, name, 1.0)
    with pytest.raises(ct.ChunkTieringError, match="None"):
        ct.accepted_multipass_storage_requirements()
    # Explicit requirements validate their own terms.
    for changes in (
        {"internal_reserve_bytes": -1},
        {"level_one_transient_bytes": -1},
        {"level_two_transient_bytes": -1},
        {"level_one_peak_ratio": 0.5},
        {"level_two_peak_ratio": 0.99},
        {"internal_reserve_bytes": True},
    ):
        with pytest.raises(ct.ChunkTieringError):
            _requirements(**changes)
    record = dict(_requirements().as_record())
    assert ct.MultipassStorageRequirements.from_record(record) == _requirements()
    with pytest.raises(ct.ChunkTieringError, match="missing"):
        ct.MultipassStorageRequirements.from_record({})


def test_t07_the_storage_plan_retains_every_input_and_credits_no_reclaim(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    plan = run["plan"]
    schedule = cm.derive_merge_schedule(plan)
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    bytes_by_id = {item.chunk_id: item.receipt.manifest.total_bytes for item in inputs}
    storage = ct.plan_multipass_storage(
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        groups=[(g.group_id, g.chunk_ids) for g in schedule.groups],
        chunk_bytes_by_id=bytes_by_id,
        seed_catalog_bytes=database.stat().st_size,
        requirements=_requirements(),
    )
    assert storage.contract == ct.MULTIPASS_STORAGE_PLAN_CONTRACT
    assert storage.retained_chunk_bytes == sum(bytes_by_id.values())
    assert storage.inputs_retained is True and storage.reclaimable_bytes == 0
    assert storage.reclaim_authority is None and storage.transfer_authority is None
    assert storage.external_tier_qualified is False
    assert [step.step for step in storage.steps] == [
        *(g.group_id for g in schedule.groups),
        "final",
    ]
    for group, step in zip(schedule.groups, storage.steps, strict=False):
        assert step.input_bytes == sum(bytes_by_id[c] for c in group.chunk_ids)
        assert step.peak_ratio == 1.5
    final = storage.steps[-1]
    assert final.input_bytes == sum(step.peak_bytes for step in storage.steps[:-1])
    assert final.peak_ratio == 2.0
    assert storage.projected_intermediate_bytes == final.input_bytes
    assert storage.peak_required_free_bytes == max(s.required_free_bytes for s in storage.steps)
    identity = storage.identity()
    moved = replace(storage, requirements=_requirements(internal_reserve_bytes=101))
    assert moved.identity() != identity
    assert json.loads(json.dumps(dict(storage.as_record())))["reclaimable_bytes"] == 0
    with pytest.raises(ct.ChunkTieringError, match="no authenticated byte length"):
        ct.plan_multipass_storage(
            plan_digest=plan.plan_digest,
            merge_schedule_digest=schedule.schedule_digest,
            groups=[("group-0000", ("chunk-0000", "chunk-9999"))],
            chunk_bytes_by_id=bytes_by_id,
            seed_catalog_bytes=0,
            requirements=_requirements(),
        )


# ==========================================================================
# The gate is load-bearing end to end -- D151-C13 §§20, 21
# ==========================================================================
def _tripwire(name: str) -> Any:
    def reached(*_args: Any, **_kwargs: Any) -> Any:
        message = f"{name} was reached; the storage refusal must land before it"
        raise AssertionError(message)

    return reached


def test_a22_a_real_consolidation_refuses_before_reading_anything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    for name in (
        "require_multipass_plan",
        "require_clean_running_repository",
        "derive_merge_schedule",
        "resolve_chunk_inputs",
        "run_group_merge",
        "run_final_merge",
    ):
        monkeypatch.setattr(cm, name, _tripwire(name))
    root = run["base"] / "real"
    # D151-C15 §12: the authority is OPEN here -- the module fixture opens it for synthetic
    # execution -- and the storage terms are the REAL ones, every one None. Authority alone
    # admits nothing: the refusal is on storage, before anything is read or created. The
    # derivation is restored inside a nested context, so the fixture's own patch of the same
    # attribute is undone last and nothing leaks past this test.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            cm,
            "accepted_multipass_storage_requirements",
            ct.accepted_multipass_storage_requirements,
        )
        with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
            cm.run_multipass_f0(
                plan=run["plan"],
                internal_root=run["chunk_root"],
                operational_catalog=database,
                multipass_root=root,
                run_id="real",
            )
    assert not root.exists()
    # D151-C15 §9: the storage seam is gone from the production signature; no parameter of the
    # orchestrator names a storage term.
    signature = inspect.signature(cm.run_multipass_f0)
    assert "injected_storage_requirements" not in signature.parameters
    assert not any("storage" in name or "requirement" in name for name in signature.parameters)


def test_below_the_floor_no_world_is_created(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    starved = _requirements(internal_reserve_bytes=1 << 62)
    root = run["base"] / "starved"
    # The starved terms replace the fixture's synthetic ones inside a nested context (see
    # test_a22): the same attribute, undone before the fixture's own patch.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "accepted_multipass_storage_requirements", lambda: starved)
        with pytest.raises(ct.ChunkTieringError, match="NOT ADMITTED") as refusal:
            cm.run_multipass_f0(
                plan=run["plan"],
                internal_root=run["chunk_root"],
                operational_catalog=database,
                multipass_root=root,
                run_id="starved",
            )
    assert "group-0000" in str(refusal.value)
    assert not (root / "intermediates").exists()
    assert (root / cm.STORAGE_PLAN_FILENAME).is_file()  # the plan is recorded; nothing is built
    # The child body re-applies the gate before its attempt directory exists.
    schedule = cm.derive_merge_schedule(run["plan"])
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", "group-0000"
    )
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMITTED"):
        cm.merge_group_body(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id="group-0000",
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                requirements=starved,
            )
        )
    assert not directory.exists()
    assert schedule.groups[0].group_id == "group-0000"
    # And the final step is gated separately: level 1 admitted, level 2 starved.
    partial = c13.merge_in_process(run, database, label="two-tier", finalize=False)
    with pytest.raises(ct.ChunkTieringError, match="'final' is NOT ADMITTED"):
        cm.finalize_multipass_body(
            c13.final_request(
                run,
                schedule_path=partial["schedule_path"],
                intermediates_root=partial["intermediates_root"],
                world_directory=partial["multipass_root"] / "final",
                database=database,
                requirements=replace(starved, level_one_peak_ratio=1.0),
            )
        )
    assert not (partial["multipass_root"] / "final").exists()
    admission = partial["intermediates"][0].storage_admission
    assert admission["admitted"] is True and admission["reserve_bytes"] == 0


def test_the_admission_record_travels_with_the_intermediate(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    for receipt in partial["intermediates"]:
        admission = receipt.storage_admission
        assert admission["step"] == receipt.group_id
        assert admission["free_bytes"] >= admission["required_free_bytes"]
        expected_inputs = sum(
            chunk.manifest.total_bytes
            for chunk in run["receipts"]
            if chunk.chunk_id in receipt.input_chunk_ids
        )
        assert admission["peak_bytes"] == expected_inputs + database.stat().st_size


# ==========================================================================
# A24: no external path without authority; logical chunk identity is never duplicated
# ==========================================================================
def test_a24_an_external_root_is_read_only_and_a_verified_copy_is_one_logical_input(
    tmp_path: Path,
) -> None:
    database, tree, run = c13i.ten_chunk_run(tmp_path)
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    reference = eq.measure(tmp_path / "mono")
    external = tmp_path / "external"
    source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0000")[1]
    cs.transfer_chunk(
        source_directory=source,
        destination_directory=external / "chunk-0000",
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    external_before = sorted(str(p.relative_to(external)) for p in external.rglob("*"))
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "dual",
        run_id="dual",
        external_root=external,
    )
    assert sorted(str(p.relative_to(external)) for p in external.rglob("*")) == external_before
    chunk_inputs = result.intermediates[0].chunk_inputs
    assert [item["chunk_id"] for item in chunk_inputs].count("chunk-0000") == 1
    assert chunk_inputs[0]["tier"] == cs.TIER_INTERNAL
    assert [item["chunk_id"] for item in result.receipt["chunk_inputs"]].count("chunk-0000") == 1
    assert len(result.receipt["chunk_inputs"]) == 10
    eq.assert_equivalent(reference, eq.measure(result.world_directory))
    # A disagreeing external copy is refused rather than resolved.
    receipt_path = external / "chunk-0000" / CHUNK_RECEIPT_FILENAME
    document = json.loads(receipt_path.read_text(encoding="utf-8"))
    document["end"] = document["end"] + 1
    receipt_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(cs.ChunkStorageError, match="two copies that disagree"):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=run["base"] / "dual-conflict",
            run_id="dual-conflict",
            external_root=external,
        )
    # A transfer onto the QUALIFIED volume remains closed, whatever the multipass does.
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.transfer_chunk(
            source_directory=source,
            destination_directory=tmp_path / "qualified" / "chunk-0000",
            destination_volume_uuid=cs.QUALIFIED_EXTERNAL_VOLUME_UUID,
        )
    assert not (tmp_path / "qualified").exists()


def test_nothing_is_deleted_by_a_whole_multipass_consolidation(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    before = {
        str(path.relative_to(run["chunk_root"])): path.read_bytes()
        for path in run["chunk_root"].rglob("*")
        if path.is_file()
    }
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "kept",
        run_id="kept",
    )
    after = {
        str(path.relative_to(run["chunk_root"])): path.read_bytes()
        for path in run["chunk_root"].rglob("*")
        if path.is_file()
    }
    assert after == before
    for group, receipt in zip(result.schedule.groups, result.intermediates, strict=True):
        directory = (
            run["base"]
            / "kept"
            / "intermediates"
            / group.group_id
            / f"attempt-{receipt.attempt:03d}"
        )
        verify_artifact_manifest(
            directory, receipt.manifest, exclude=(cm.INTERMEDIATE_RECEIPT_FILENAME,)
        )
    assert result.receipt["chunks_unchanged"] is True


# ==========================================================================
# T08: the deterministic spill seam
# ==========================================================================
def test_t08_every_spill_policy_is_deterministic_and_none_is_production(tmp_path: Path) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    plan = run["plan"]
    placements = cs.derive_placements(plan, internal_root=run["chunk_root"])
    total = sum(p.internal_bytes or 0 for p in placements)
    ordinal = ct.propose_spill(
        placements, plan=plan, policy=ct.SPILL_POLICY_PLAN_ORDINAL, needed_bytes=total
    )
    assert ordinal.candidates == tuple(b.chunk_id for b in plan.chunks) and ordinal.sufficient
    assert ordinal.candidates == tuple(
        p.chunk_id for p in cs.select_spill_candidates(placements, needed_bytes=total)
    )
    reversed_order = ct.propose_spill(
        tuple(reversed(placements)), plan=plan, policy=ct.SPILL_POLICY_PLAN_ORDINAL, needed_bytes=1
    )
    assert reversed_order.candidates == (plan.chunks[0].chunk_id,)
    largest = ct.propose_spill(
        placements, plan=plan, policy=ct.SPILL_POLICY_LARGEST_ARTIFACT, needed_bytes=total
    )
    sizes = {p.chunk_id: p.internal_bytes or 0 for p in placements}
    assert [sizes[c] for c in largest.candidates] == sorted(sizes.values(), reverse=True)
    region = ct.propose_spill(
        placements, plan=plan, policy=ct.SPILL_POLICY_REGION_THEN_ORDINAL, needed_bytes=total
    )
    assert region.candidates == ordinal.candidates  # a valid plan is already region-ordered
    sealed_order = tuple(reversed([b.chunk_id for b in plan.chunks]))
    sealed = ct.propose_spill(
        placements,
        plan=plan,
        policy=ct.SPILL_POLICY_SEALED_ORDER,
        needed_bytes=1,
        sealed_order=sealed_order,
    )
    assert sealed.candidates == (sealed_order[0],)
    with pytest.raises(ct.ChunkTieringError, match="naming every eligible chunk exactly once"):
        ct.propose_spill(placements, plan=plan, policy=ct.SPILL_POLICY_SEALED_ORDER, needed_bytes=1)
    with pytest.raises(ct.ChunkTieringError, match="not one of"):
        ct.propose_spill(placements, plan=plan, policy="newest", needed_bytes=1)
    with pytest.raises(ct.ChunkTieringError, match="non-negative"):
        ct.propose_spill(
            placements, plan=plan, policy=ct.SPILL_POLICY_PLAN_ORDINAL, needed_bytes=-1
        )
    short = ct.propose_spill(
        placements, plan=plan, policy=ct.SPILL_POLICY_PLAN_ORDINAL, needed_bytes=1 << 50
    )
    assert not short.sufficient and short.candidates == ordinal.candidates
    with pytest.raises(ct.ChunkTieringError, match="STOP FOR OWNER"):
        ct.require_sufficient_spill(short)
    assert ct.require_sufficient_spill(ordinal) is ordinal
    with pytest.raises(ct.ChunkTieringError, match="never defaulted"):
        ct.production_spill_policy()
    # Only a completed internal chunk is eligible: a verified dual copy is skipped.
    external = tmp_path / "external"
    source = cs.completed_chunk_receipt(run["chunk_root"], "chunk-0000")[1]
    cs.transfer_chunk(
        source_directory=source,
        destination_directory=external / "chunk-0000",
        destination_volume_uuid=SYNTHETIC_VOLUME,
    )
    dual = cs.derive_placements(plan, internal_root=run["chunk_root"], external_root=external)
    proposal = ct.propose_spill(
        dual, plan=plan, policy=ct.SPILL_POLICY_PLAN_ORDINAL, needed_bytes=1
    )
    assert proposal.candidates == (plan.chunks[1].chunk_id,)
    assert cp.CHUNK_REGION_ORDER == ("primary", "shard")
    assert database is not None
