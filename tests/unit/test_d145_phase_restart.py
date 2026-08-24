"""Decision 145 — the governed major-phase restart, proved boundary by boundary.

**What is under test.** One OS process per major execution phase, so that a phase which reached
its durable terminal is followed by a process that did not exist while it ran -- and the memory
the finished phase was holding is returned to the operating system by the only mechanism that
genuinely returns it, which is the process ending.

The organising rule, inherited from the Decision 140, 141 and 144 files: **a test that cannot
fail proves nothing.** Every refusal here is asserted through a production entry point --
`run_single_source_canary_phase` or `run_canary_source_command` -- and never against a helper with
the argument obligingly supplied by the test. Nothing depends on the operator's SSD being
attached, on a dock being present, or on any particular machine: every topology, volume, power
state and lid state is synthesised through the same provider seams Decisions 137-144 already use.

**The three claims.**

*Continuation is earned.* A phase begins only when its predecessor left a durable terminal
checkpoint of the same run, of the same source, under the same governing code, against the same
accepted catalog -- and only when the predecessor's process is gone. Committed rows, a world
directory and a working catalog are **never** read as phase completion.

*Continuation is not a pause.* An interrupted phase leaves no checkpoint, so it refuses its
successor rather than resuming. A restart confers no right to detach, eject, unmount, sleep, or
change topology, and the D144 narrowing to `USB_VIA_THUNDERBOLT_DOCK` survives every boundary.

*Continuation changes nothing about the result.* The three-process sequence and the accepted
whole-run path produce result documents that differ in exactly the fields two whole runs differ
in -- and in no others.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d138_safety_envelope_correction as d138  # noqa: E402
import test_d140_total_pre_canary_hardening as d140  # noqa: E402
import test_d144_first_canary_transport_narrowing as d144  # noqa: E402

from disclosure_drift.config import EVIDENCE_ROOT_ENV  # noqa: E402
from disclosure_drift.m3 import canary_phases as phases  # noqa: E402
from disclosure_drift.m3 import canary_runtime as runtime  # noqa: E402
from disclosure_drift.m3 import dock_transport as dt  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    RunProgressLedger,
    WorkingCatalogError,
)
from disclosure_drift.paths import DataTree  # noqa: E402

_BULK = d116._BULK_INSTANCE
_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID
_OTHER_UUID = "0BADCAFE-0000-0000-0000-000000000000"
_DOCK = d144._DOCK
_DIRECT = d144._DIRECT
_THIRD_PARTY_HUB = d144._THIRD_PARTY_HUB


# ==========================================================================
# The world, and the two ways of driving it
# ==========================================================================
def _world(root: Path) -> tuple[Path, Path]:
    """A stand-in private root and a lawful, already-existing work root."""
    private = d116._private_root(root)
    work = root / "work"
    work.mkdir(exist_ok=True)
    return private, work


def _phase(
    private: Path,
    work: Path,
    phase: str,
    *,
    run_id: str = "d145",
    instance: str = _BULK,
    asserted: str | None = None,
) -> Any:
    """One phase, through the library production entry point."""
    return canary.run_single_source_canary_phase(
        phase=phase,
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=work,
        run_id=run_id,
        source_instance_id=instance,
        require_volume_uuid=asserted,
    )


def _sequence(
    private: Path,
    work: Path,
    *,
    run_id: str = "d145",
    through: str = "f2",
    asserted: str | None = None,
) -> list[Any]:
    """Run the phases in order up to and including ``through``."""
    done = []
    for phase in phases.CANARY_PHASE_SEQUENCE:
        done.append(_phase(private, work, phase, run_id=run_id, asserted=asserted))
        if phase == through:
            break
    return done


def _operator(
    root: Path,
    private: Path,
    work: Path,
    mode: str,
    *,
    run_id: str = "d145-op",
    asserted: str | None = _QUALIFIED,
    temp: Path | None = None,
) -> Any:
    """One phase, through the real operator entry point `cli.py` invokes."""
    checkout = root / "checkout"
    checkout.mkdir(exist_ok=True)
    environ = {EVIDENCE_ROOT_ENV: str(private)}
    if temp is not None:
        environ[ewr.SQLITE_TMPDIR_ENV] = str(temp)
    return canary.run_canary_source_command(
        mode=mode,
        run_id=run_id,
        source_instance_id=_BULK,
        work_root=str(work),
        repository_root=checkout,
        require_volume_uuid=asserted,
        environ=environ,
    )


def _ledger(work: Path, run_id: str) -> RunProgressLedger:
    return RunProgressLedger(work / run_id / PROGRESS_LEDGER_FILENAME)


def _rewrite_checkpoint(work: Path, world: str, label: str, **changes: object) -> None:
    """Tamper with one stored checkpoint field, in place, the way a hostile world would."""
    ledger = _ledger(work, world)
    try:
        key = f"{phases.PHASE_CHECKPOINT_KEY_PREFIX}{label}"
        record = json.loads(str(ledger.recorded_value(key)))
        record.update(changes)
        ledger.record_value(key, json.dumps(record, sort_keys=True))
    finally:
        ledger.close()


def _drop_checkpoint(work: Path, run_id: str, phase: str) -> None:
    """Remove one stored checkpoint, leaving every durable row the phase wrote behind.

    This is the shape of an **interrupted** phase: the rows are committed, the world is populated,
    and the phase never reached its terminal. Nothing here is allowed to read that as completion.
    """
    ledger = _ledger(work, run_id)
    try:
        ledger._connection.execute(  # noqa: SLF001 - a hostile world, built deliberately
            "DELETE FROM run_working_catalog WHERE key = ?",
            (f"{phases.PHASE_CHECKPOINT_KEY_PREFIX}{phase}",),
        )
    finally:
        ledger.close()


@pytest.fixture(scope="module")
def completed(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, Path, list[Any]]:
    """One whole run driven phase by phase. Module-scoped: it is built once and never mutated."""
    root = tmp_path_factory.mktemp("d145-complete")
    private, work = _world(root)
    return private, work, _sequence(private, work)


# ==========================================================================
# The reconstructed phase inventory — §§2-4
# ==========================================================================
def test_the_phases_are_the_accepted_capacity_vocabulary_and_not_a_new_one() -> None:
    """The phase names are Decision 135 §11's, carried by the accepted capacity labels."""
    assert phases.CANARY_PHASE_SEQUENCE == ("f0", "f1", "f2")
    for phase in phases.CANARY_PHASE_SEQUENCE:
        assert any(label.lower().endswith(phase) for label in ewr.CAPACITY_PHASES)


def test_every_inter_phase_boundary_is_declared_and_the_last_one_terminates() -> None:
    """Two inter-phase boundaries, and F2 has no successor to invent one for."""
    assert phases.PHASE_PREDECESSOR == {"f0": None, "f1": "f0", "f2": "f1"}
    assert phases.PHASE_SUCCESSOR == {"f0": "f1", "f1": "f2", "f2": None}


def test_a_phase_label_this_build_does_not_execute_is_refused() -> None:
    with pytest.raises(phases.CanaryPhaseError, match="not a canary execution phase"):
        phases.validate_phase("f3")


def test_each_phase_is_admitted_under_an_accepted_floor_and_not_an_invented_one() -> None:
    """**§7.** Every admission floor is an already-accepted constant at its accepted meaning."""
    assert canary.PHASE_ADMISSION_FLOOR["f0"] == ewr.LAUNCH_MINIMUM_FREE_BYTES
    assert canary.PHASE_ADMISSION_FLOOR["f1"] == ewr.PRE_F1_MINIMUM_FREE_BYTES
    assert canary.PHASE_ADMISSION_FLOOR["f2"] == canary.PRE_F2_MINIMUM_FREE_BYTES


# ==========================================================================
# A. A complete predecessor admits its successor — §18.A
# ==========================================================================
def test_the_three_phase_sequence_completes_and_writes_one_result_document(
    completed: tuple[Path, Path, list[Any]],
) -> None:
    _private, work, done = completed
    assert [step.phase for step in done] == ["f0", "f1", "f2"]
    assert [step.predecessor_phase for step in done] == [None, "f0", "f1"]
    assert [step.result_document_written for step in done] == [False, False, True]
    assert (work / "d145" / "canary_result.json").is_file()


def test_each_phase_records_its_own_durable_terminal_checkpoint(
    completed: tuple[Path, Path, list[Any]],
) -> None:
    _private, work, _done = completed
    ledger = _ledger(work, "d145")
    try:
        for phase in phases.CANARY_PHASE_SEQUENCE:
            checkpoint = phases.read_phase_checkpoint(ledger, phase)
            assert checkpoint is not None
            assert checkpoint.status == phases.PHASE_STATUS_COMPLETE
            assert checkpoint.contract == phases.PHASE_RESTART_CONTRACT
            assert checkpoint.run_id == "d145"
    finally:
        ledger.close()


def test_the_phase_sequence_and_a_whole_run_differ_only_where_two_whole_runs_differ(
    tmp_path: Path,
) -> None:
    """**The equivalence proof.** Not "close enough" -- the same fields, and no others.

    A phased run is compared against a whole run, and the set of fields that differ is required to
    be *exactly* the set that differs between two whole runs of the same source into two worlds.
    That baseline is measured here rather than assumed, so the proof cannot quietly weaken if
    something run-scoped is added to the result surface later.
    """
    private, work = _world(tmp_path)
    catalog, tree = d116._catalog(private), DataTree.from_root(private)
    whole_a = canary.run_single_source_canary(
        operational_catalog=catalog,
        tree=tree,
        work_root=work,
        run_id="whole-a",
        source_instance_id=_BULK,
    )
    whole_b = canary.run_single_source_canary(
        operational_catalog=catalog,
        tree=tree,
        work_root=work,
        run_id="whole-b",
        source_instance_id=_BULK,
    )
    _sequence(private, work, run_id="phased")
    phased = json.loads((work / "phased" / "canary_result.json").read_text(encoding="utf-8"))
    record_a, record_b = dict(whole_a.as_record()), dict(whole_b.as_record())

    baseline = {key for key in record_a if record_a[key] != record_b[key]}
    observed = {key for key in record_a if record_a[key] != phased.get(key)}
    assert observed == baseline
    assert whole_a.identities() == {key: phased[key] for key in whole_a.identities()}


def test_the_run_carries_one_chronological_capacity_record_across_all_three_processes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Observations from every phase reach the one result document, in order."""
    private, work = _world(tmp_path)
    temp = d144._attach(monkeypatch, tmp_path)
    _sequence(private, work, run_id="ext", asserted=_QUALIFIED)
    assert temp.is_dir()
    document = json.loads((work / "ext" / "canary_result.json").read_text(encoding="utf-8"))
    labels = [item["phase"] for item in document["capacity_observations"]]
    assert labels.count("PRE_LAUNCH") == 3, "each phase process launches, and says so"
    for expected in ("POST_F0", "PRE_F1", "POST_F1_PRE_F2", "POST_F2"):
        assert expected in labels
    assert labels.index("POST_F0") < labels.index("PRE_F1") < labels.index("POST_F2")


# ==========================================================================
# B, C. An incomplete or failed predecessor refuses — §18.B, §18.C
# ==========================================================================
def test_a_successor_refuses_when_its_predecessor_never_ran(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError, match="does not exist"):
        _phase(private, work, "f1", run_id="orphan")


def test_committed_rows_and_a_populated_world_are_not_phase_completion(tmp_path: Path) -> None:
    """**§13.** The existence of durable output is never read as a completed phase."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="cut", through="f0")
    assert (work / "cut" / "working_catalog.sqlite3").is_file()
    _drop_checkpoint(work, "cut", "f0")
    with pytest.raises(phases.CanaryPhaseError, match="no durable terminal checkpoint"):
        _phase(private, work, "f1", run_id="cut")


def test_a_failed_predecessor_leaves_no_checkpoint_and_refuses_its_successor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§14.** A phase that stopped on a blocking terminal is not a restart boundary."""
    private, work = _world(tmp_path)
    monkeypatch.setattr(
        canary, "materialize_one_planned_source", lambda **_kw: d140._outcome("failed")
    )
    with pytest.raises(canary.SingleSourceCanaryError, match="blocking terminal"):
        _phase(private, work, "f0", run_id="failed")
    monkeypatch.undo()
    ledger = _ledger(work, "failed")
    try:
        assert phases.read_phase_checkpoint(ledger, "f0") is None
    finally:
        ledger.close()
    with pytest.raises(phases.CanaryPhaseError, match="no durable terminal checkpoint"):
        _phase(private, work, "f1", run_id="failed")


def test_a_checkpoint_is_never_written_with_any_status_but_complete(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="status", through="f0")
    ledger = _ledger(work, "status")
    try:
        stored = phases.read_phase_checkpoint(ledger, "f0")
        assert stored is not None
        pending = phases.PhaseCheckpoint(**{**stored.as_record(), "status": "in_progress"})  # type: ignore[arg-type]
        with pytest.raises(phases.CanaryPhaseError, match="durable terminal success"):
            phases.write_phase_checkpoint(ledger, pending)
    finally:
        ledger.close()


# ==========================================================================
# D-G. Identity — §18.D, §18.E, §18.F, §18.G and §12
# ==========================================================================
def test_a_successor_refuses_another_runs_checkpoint(tmp_path: Path) -> None:
    """**§13.** A checkpoint is never consumed by a run that did not write it."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="owner", through="f0")
    _rewrite_checkpoint(work, "owner", "f0", run_id="somebody-else")
    with pytest.raises(phases.CanaryPhaseError, match="run_id"):
        _phase(private, work, "f1", run_id="owner")


def test_a_successor_refuses_a_checkpoint_that_names_another_phase(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="mixed", through="f0")
    _rewrite_checkpoint(work, "mixed", "f0", phase="f2")
    with pytest.raises(phases.CanaryPhaseError, match="describes phase"):
        _phase(private, work, "f1", run_id="mixed")


def test_a_successor_refuses_a_checkpoint_written_under_another_contract(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="contract", through="f0")
    _rewrite_checkpoint(work, "contract", "f0", contract="m3.3-canary-phase-restart/99")
    with pytest.raises(phases.CanaryPhaseError, match="does not continue from"):
        _phase(private, work, "f1", run_id="contract")


def test_a_successor_refuses_a_different_source(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="source", through="f0")
    _rewrite_checkpoint(work, "source", "f0", source_instance_id="another|source|1")
    with pytest.raises(phases.CanaryPhaseError, match="source_instance_id"):
        _phase(private, work, "f1", run_id="source")


def test_a_successor_refuses_a_moved_plan_fingerprint(tmp_path: Path) -> None:
    """**§12.** The input identity is re-derived live and compared, never carried."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="plan", through="f0")
    _rewrite_checkpoint(work, "plan", "f0", plan_fingerprint="0" * 64)
    with pytest.raises(phases.CanaryPhaseError, match="plan_fingerprint"):
        _phase(private, work, "f1", run_id="plan")


def test_a_successor_refuses_an_accepted_catalog_that_moved(tmp_path: Path) -> None:
    """A changed accepted catalog refuses at the working-catalog attach, before admission."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="catalog", through="f0")
    with d116.connect(d116._catalog(private), writer=True) as connection:
        connection.execute("CREATE TABLE d145_intrusion (x INTEGER)")
    with pytest.raises(WorkingCatalogError, match="NOT the artifact"):
        _phase(private, work, "f1", run_id="catalog")


def test_a_successor_refuses_a_changed_governing_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§18.F.** The frozen constants that govern a phase *are* this path's configuration."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="config", through="f0")
    monkeypatch.setattr(canary, "CANARY_RESOLUTION_SCOPE", "somewhere-else")
    with pytest.raises(phases.CanaryPhaseError, match="execution_identity"):
        _phase(private, work, "f1", run_id="config")


def test_a_successor_refuses_a_changed_code_revision(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§18.G.** A build whose version moved does not continue another build's checkpoint."""
    import disclosure_drift

    private, work = _world(tmp_path)
    _sequence(private, work, run_id="revision", through="f0")
    monkeypatch.setattr(disclosure_drift, "__version__", "99.99.99")
    with pytest.raises(phases.CanaryPhaseError, match="execution_identity"):
        _phase(private, work, "f1", run_id="revision")


def test_the_execution_identity_folds_the_values_that_govern_a_phase() -> None:
    """It is a digest of the governing constants, not a constant that happens to be a digest."""
    identity = canary.phase_execution_identity()
    assert identity != canary.phase_execution_identity(batch_size=canary.CANARY_BATCH_SIZE + 1)
    assert identity == canary.phase_execution_identity()
    assert len(identity) == 64


def test_the_page_cache_budget_is_deliberately_not_part_of_the_identity(tmp_path: Path) -> None:
    """**Accepted Decision 119** proves the budget evidence-neutral, so it must not refuse."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="cache", through="f0")
    outcome = canary.run_single_source_canary_phase(
        phase="f1",
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=work,
        run_id="cache",
        source_instance_id=_BULK,
        cache_bytes=None,
    )
    assert outcome.phase == "f1"


# ==========================================================================
# H-P. The envelope is re-established by every process — §10, §11, §18.H-P
# ==========================================================================
@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_a_missing_volume_assertion(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.I / D140-R2.** Omitting the assertion is itself the refusal, at every boundary."""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="--require-volume-uuid is required"):
        _phase(private, work, phase, run_id="uuidless", asserted=None)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_a_volume_that_is_not_the_qualified_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.H.**"""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one qualified external"):
        _phase(private, work, phase, run_id="wronguuid", asserted=_OTHER_UUID)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_a_qualified_direct_attachment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§11 and §18.K.** A restart is not a way to reach the topology the owner did not select.

    `USB_DIRECT` is **qualified** -- D141-R8 and Decision 142 §5 keep it so -- and it is still
    refused here, at every boundary, because Decision 142 §4 selected the dock for the *first*
    canary and D144-R1 made that selection mechanical. A phase boundary is exactly where an
    operator answering a dock refusal by re-plugging directly would try again.
    """
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError, match="requires USB_VIA_THUNDERBOLT_DOCK"):
        _phase(private, work, phase, run_id="direct", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_an_unqualified_topology(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.J / §18.L.**"""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path, chain=_THIRD_PARTY_HUB)
    with pytest.raises(dt.DockTransportError):
        _phase(private, work, phase, run_id="hub", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_battery_power(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.M / D141-R9.** Re-read by each process; the previous one's reading is not inherited."""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path, on_ac=False)
    with pytest.raises(runtime.CanaryRuntimeError):
        _phase(private, work, phase, run_id="battery", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_a_closed_lid(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.N.**"""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path, lid_closed=True)
    with pytest.raises(runtime.CanaryRuntimeError):
        _phase(private, work, phase, run_id="lid", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_a_work_root_inside_the_d130_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.O / D137-R3.**"""
    private, _work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    archive = ewr.d130_archive_directory(tmp_path)
    archive.mkdir(parents=True, exist_ok=True)
    inside = archive / "world"
    inside.mkdir(exist_ok=True)
    with pytest.raises(ewr.ExternalWorkingRootError):
        _phase(private, inside, phase, run_id="d130", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_an_internal_sqlite_tmpdir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, phase: str
) -> None:
    """**§18.P / D137-R8.** The temporary root is re-checked by every process."""
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    monkeypatch.delenv(ewr.SQLITE_TMPDIR_ENV, raising=False)
    with pytest.raises(ewr.ExternalWorkingRootError):
        _phase(private, work, phase, run_id="tmpdir", asserted=_QUALIFIED)


@pytest.mark.parametrize("phase", ["f0", "f1", "f2"])
def test_every_phase_refuses_when_another_canary_holds_the_host_lock(
    tmp_path: Path, phase: str
) -> None:
    """**§18.Q / D140-R16.** Each phase process takes the lock itself and refuses on conflict."""
    private, work = _world(tmp_path)
    held = runtime.acquire_canary_execution_lock(private, detail={"run_id": "someone-else"})
    try:
        with pytest.raises(runtime.CanaryRuntimeError, match="already running"):
            _phase(private, work, phase, run_id="locked")
    finally:
        held.release()


def test_a_continuation_is_admitted_under_the_phase_floor_and_not_the_launch_floor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§7.** The launch floor is false by construction once F0 has written; F1 uses PRE_F1.

    Pinned just above the accepted `PRE_F1` floor and far below the launch floor, which is the
    real shape of a volume part-way through a run. F1 must be admitted, and a byte below the
    accepted floor must refuse -- so the relaxation is bounded by an accepted number rather than
    being an absence of one.
    """
    private, work = _world(tmp_path)
    d144._attach(monkeypatch, tmp_path)
    # Both worlds are built while the launch floor still holds, because F0 is a launch and keeps
    # it. Only the continuations below run on a volume that a launch could no longer start on.
    for world in ("floor-admits", "floor-refuses"):
        _sequence(private, work, run_id=world, through="f0", asserted=_QUALIFIED)

    d138._pin_free(monkeypatch, ewr.PRE_F1_MINIMUM_FREE_BYTES)
    assert ewr.PRE_F1_MINIMUM_FREE_BYTES < ewr.LAUNCH_MINIMUM_FREE_BYTES
    assert _phase(private, work, "f1", run_id="floor-admits", asserted=_QUALIFIED).phase == "f1"

    d138._pin_free(monkeypatch, ewr.PRE_F1_MINIMUM_FREE_BYTES - 1)
    with pytest.raises(ewr.ExternalWorkingRootError, match="free-space"):
        _phase(private, work, "f1", run_id="floor-refuses", asserted=_QUALIFIED)


def test_the_operator_surface_narrows_the_transport_on_every_phase_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**D144-R1 survives D145.** The operator seam is narrowed for the phase modes too."""
    private, work = _world(tmp_path)
    temp = d144._attach(monkeypatch, tmp_path, chain=_DIRECT)
    for mode in sorted(canary.CANARY_PHASE_MODES):
        with pytest.raises(dt.DockTransportError, match="requires USB_VIA_THUNDERBOLT_DOCK"):
            _operator(tmp_path, private, work, mode, temp=temp)


def test_no_production_envelope_call_omits_the_transport_narrowing() -> None:
    """**The D144 recurrence killer, re-asserted over the seams Decision 145 added.**

    Read from the source rather than from behaviour, because a *fourth* or *fifth* seam added
    without the narrowing is exactly what behavioural tests over the existing ones cannot see.
    """
    tree = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_external_envelope"
    ]
    assert len(calls) == 4, "the production seam count changed; each one needs the narrowing"
    for call in calls:
        pinned = [
            keyword
            for keyword in call.keywords
            if keyword.arg == "required_transport"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "FIRST_CANARY_REQUIRED_TRANSPORT"
        ]
        assert pinned, "a production envelope call does not narrow the transport"


# ==========================================================================
# T, U. Exactly-once phase advancement — §13, §18.T, §18.U
# ==========================================================================
def test_a_completed_phase_is_never_re_entered(tmp_path: Path) -> None:
    """**§18.U.**"""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="twice", through="f1")
    with pytest.raises(phases.CanaryPhaseError, match="already reached its durable terminal"):
        _phase(private, work, "f1", run_id="twice")


def test_a_finished_run_is_never_re_entered(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="finished")
    for phase in phases.CANARY_PHASE_SEQUENCE:
        with pytest.raises((canary.SingleSourceCanaryError, phases.CanaryPhaseError)):
            _phase(private, work, phase, run_id="finished")


def test_f0_never_creates_a_world_a_continuation_should_have_inherited(tmp_path: Path) -> None:
    """`create_world` and `attach_world` are exact inverses, so neither can manufacture state."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="inverse", through="f0")
    with pytest.raises(canary.SingleSourceCanaryError, match="already exists"):
        _phase(private, work, "f0", run_id="inverse")
    with pytest.raises(canary.SingleSourceCanaryError, match="does not exist"):
        canary.attach_world(work, "never-built")


def test_the_successor_does_not_rerun_its_predecessor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§18.T.** F1 does not parse, and F2 neither parses nor resolves. Proved by detonation."""
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="norerun", through="f0")

    def detonate(**_kw: object) -> Any:
        message = "a completed phase was re-run by its successor"
        raise AssertionError(message)

    monkeypatch.setattr(canary, "materialize_one_planned_source", detonate)
    assert _phase(private, work, "f1", run_id="norerun").phase == "f1"
    monkeypatch.setattr(canary, "_f1", detonate)
    assert _phase(private, work, "f2", run_id="norerun").phase == "f2"


def test_a_checkpoint_is_create_once_and_is_never_overwritten(tmp_path: Path) -> None:
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="createonce", through="f0")
    ledger = _ledger(work, "createonce")
    try:
        stored = phases.read_phase_checkpoint(ledger, "f0")
        assert stored is not None
        with pytest.raises(phases.CanaryPhaseError, match="create-once"):
            phases.write_phase_checkpoint(ledger, stored)
    finally:
        ledger.close()


# ==========================================================================
# V, W. Process replacement is the mechanism — §9, §18.V, §18.W, §20
# ==========================================================================
def test_a_live_predecessor_process_refuses_the_successor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """**§18.W.** A checkpoint plus a still-running writer is the state that must refuse.

    The checkpoint is written *before* the process exits, so "the predecessor finished its phase"
    and "the predecessor is gone" are two different claims and the second one is enforced here.
    Two writers on one working catalog is not a restart.
    """
    private, work = _world(tmp_path)
    _sequence(private, work, run_id="alive", through="f0")
    monkeypatch.setattr(
        canary,
        "process_is_live_canary",
        lambda _pid, *, run_id, **_kw: True,  # noqa: ARG005
    )
    with pytest.raises(canary.SingleSourceCanaryError, match="still running this canary"):
        _phase(private, work, "f1", run_id="alive")


def test_a_recycled_process_id_is_not_mistaken_for_a_live_predecessor() -> None:
    """A bare process id is not an identity: the argv must be this canary and this run."""
    assert not runtime.process_is_live_canary(
        4242, run_id="rid", argv_provider=lambda _pid: ("zsh", "-c", "m3 canary-source")
    )
    assert runtime.process_is_live_canary(
        4242,
        run_id="rid",
        argv_provider=lambda _pid: ("python", "m3", "canary-source", "--run-id", "rid"),
    )
    assert not runtime.process_is_live_canary(
        4242,
        run_id="rid",
        argv_provider=lambda _pid: ("python", "m3", "canary-source", "--run-id", "other"),
    )


def test_an_exited_process_reports_gone_rather_than_raising() -> None:
    """The real `ps` path, over a process id that has genuinely finished."""
    finished = subprocess.Popen([sys.executable, "-c", "pass"])  # noqa: S603
    assert finished.wait(timeout=120) == 0
    assert not runtime.process_is_live_canary(finished.pid, run_id="rid")


def test_peak_resident_bytes_is_measured_and_is_plausible() -> None:
    peak = runtime.process_peak_resident_bytes()
    assert peak is not None
    assert peak > 1024 * 1024, "a running CPython process holds more than a mebibyte"


# ==========================================================================
# §20. The bounded memory-reclamation demonstration — three real OS processes
# ==========================================================================
def _cli_phase(private: Path, work: Path, phase: str, run_id: str) -> Mapping[str, object]:
    """Run one phase in a genuinely separate OS process, through the operator command."""
    environment = dict(os.environ)
    environment[EVIDENCE_ROOT_ENV] = str(private)
    child = subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "disclosure_drift",
            "m3",
            "canary-source",
            "--mode",
            f"phase-{phase}",
            "--source-instance-id",
            _BULK,
            "--run-id",
            run_id,
            "--work-root",
            str(work),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(canary.__file__).resolve().parents[3],
        env=environment,
    )
    # `Popen` rather than `run`, so the OPERATING SYSTEM's own process id is observed here and
    # can be compared against the one the phase reported for itself. A test that only compared
    # the phase's self-report against itself would prove nothing about process replacement.
    stdout, stderr = child.communicate(timeout=600)
    assert child.returncode == 0, stderr.decode("utf-8", errors="replace")
    record: dict[str, object] = {}
    for line in stdout.decode("utf-8").splitlines()[1:]:
        key, _, value = line.partition("  ")
        record[key.strip()] = json.loads(value.strip())
    record["_process_pid"] = child.pid
    return record


def test_the_three_phases_run_in_three_different_processes_and_each_one_ends(
    tmp_path: Path,
) -> None:
    """**§20.** The demonstration: distinct processes, old ones gone, deterministic continuation.

    Bounded and disposable -- the hostile Decision 112 synthetic world, not the real source, and
    not a performance benchmark. What it proves is mechanical and is the whole point of Decision
    145: **the next phase runs in a different process, and the previous process is gone**.
    """
    private, work = _world(tmp_path)
    observed = [_cli_phase(private, work, phase, "demo") for phase in ("f0", "f1", "f2")]

    identifiers = [int(step["pid"]) for step in observed]  # type: ignore[call-overload]
    assert len(set(identifiers)) == 3, "each phase must run in its own process"
    assert [step["_process_pid"] for step in observed] == identifiers
    assert [step["predecessor_pid"] for step in observed] == [None, *identifiers[:2]]
    assert [step["predecessor_process_gone"] for step in observed] == [None, True, True]
    for step in observed:
        assert step["operational_catalog_unchanged"] is True
        assert step["rss_peak_bytes_at_terminal"] is not None

    for identifier in identifiers:
        assert not runtime.process_is_live_canary(identifier, run_id="demo")

    document = json.loads((work / "demo" / "canary_result.json").read_text(encoding="utf-8"))
    reference = canary.run_single_source_canary(
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=work,
        run_id="demo-reference",
        source_instance_id=_BULK,
    )
    assert reference.identities() == {key: document[key] for key in reference.identities()}


# ==========================================================================
# R, S, X. Authority, network, and _parse_bulk — §§15, 16, 18.R, 18.S, 18.X
# ==========================================================================
def test_no_activation_constant_is_minted_by_this_record() -> None:
    """**§15.** Decision 145 is architecture. It authorizes nothing."""
    from disclosure_drift.m3 import e0

    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None


def _phase_path_modules() -> tuple[Any, ...]:
    return (canary, phases, runtime)


def test_the_phase_path_consults_no_authority_constant_and_no_network_switch() -> None:
    """**§18.R / §18.S.** Not "does not use one" -- does not *mention* one, on any phase path."""
    forbidden = (
        "PRE_E0_CATALOG_TRANSITION_AUTHORITY",
        "M3_3_E0_EXECUTION_AUTHORITY",
        "STALE_WRITER_LEASE_RECOVERY_AUTHORITY",
        "m3_acquire_enabled",
        "httpx",
        "http_client",
    )
    for module in _phase_path_modules():
        source = Path(module.__file__).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{module.__name__} names {token}"


def test_the_phase_path_imports_no_e0_and_no_transport() -> None:
    """A fresh interpreter that imports the phase path loads neither E0 nor an HTTP transport.

    ``disclosure_drift.sec.http_client`` **is** reachable in the import graph and is not asserted
    against: it is imported by the accepted census layer and has been for the whole life of this
    path. The claim Decision 145 makes, and the one this checks, is the accepted one -- no E0
    module and no transport library is loaded, and nothing here constructs a transport.
    """
    probe = (
        "import sys;"
        "import disclosure_drift.m3.single_source_canary, disclosure_drift.m3.canary_phases;"
        "print([m for m in sys.modules if m.endswith('.e0') or m.startswith('httpx')])"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe], capture_output=True, check=True, timeout=120
    )
    assert completed.stdout.decode("utf-8").strip() == "[]"


def test_parse_bulk_remains_canary_unreachable_after_the_phase_decomposition() -> None:
    """**§16 / §18.X.** The D143 finding is re-traced against the seams Decision 145 added.

    Three independent ways, because one of them alone would be an argument rather than a proof:
    no phase-path module names the orchestrator; a fresh interpreter that imports the whole phase
    path never loads its module; and the phase entry points reach it through no call.
    """
    for module in _phase_path_modules():
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "census_orchestrator" not in source
        assert "CensusOrchestrator" not in source
        assert "_parse_bulk" not in source

    probe = (
        "import sys;"
        "import disclosure_drift.m3.single_source_canary;"
        "print('census_orchestrator' in ' '.join(sys.modules))"
    )
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe], capture_output=True, check=True, timeout=120
    )
    assert completed.stdout.decode("utf-8").strip() == "False"


def test_no_pause_resume_or_safe_to_eject_state_is_introduced() -> None:
    """**§6.** A major-phase restart grants zero physical-detach rights, and introduces no
    state that could be read as granting one."""
    root = Path(canary.__file__).resolve().parents[3]
    forbidden = {"SAFE_TO_EJECT", "GOVERNED_PAUSE_RESUME"}
    for directory in ("src", "tests"):
        for path in (root / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)} | {
                node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
            }
            assert not (names & forbidden), f"{path} introduces {names & forbidden}"


def test_the_disk_usage_seam_the_tests_pin_is_the_one_the_run_measures_with() -> None:
    """A guard on the guards: if the module stopped using `shutil`, the floor tests would lie."""
    assert "shutil.disk_usage" in Path(canary.__file__).read_text(encoding="utf-8")
    assert shutil.disk_usage is not None
