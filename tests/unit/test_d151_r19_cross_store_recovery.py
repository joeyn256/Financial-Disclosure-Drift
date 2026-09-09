"""D151-C31R2-R19A-C2 §36: cross-store convergence -- never atomic, always fail-closed.

The sidecar, the run-progress ledger, the F0 phase checkpoint and the final record each live
in a store the world catalog's transaction cannot cover. Every one is bound into the catalog by
a committed row AFTER the other store's write; a crash between the two converges on the next
run without re-execution; a binding whose other-store state is missing conflicts; a changed
input is caught before any checkpoint or result; the accepted D140-R12 gate cannot be bypassed;
and the final semantic record is published LAST, after its RESULT_READY row. The calibration
terminal (S20C, S21C) converges the same way, in-process under an issued envelope.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c27r1_dependency_closed_subset as c27  # noqa: E402
import test_d151_c29r1_retention_aware_calibration as c29  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402

from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3.canary_phases import PHASE_F0, read_phase_checkpoint  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    FINAL_WORLD_RECEIPT_FILENAME,
    write_once_json,
)
from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE_SIDECAR_FILENAME  # noqa: E402
from disclosure_drift.m3.single_source_canary import SingleSourceCanaryError  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    RunProgressLedger,
)


@pytest.fixture(autouse=True)
def _seams(tmp_path: Path) -> Any:
    """The accepted seams for BOTH routes in one process: production opened synthetically for
    the production tests; the calibration tests run under the committed ``None``-independent
    envelope gate, exactly as the accepted calibration tests do."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
    patcher.setattr(ewr, "macos_volume_identity", c13.synthetic_volume_provider())
    yield
    patcher.undo()
    c1.unpin_repository()


def _raise_once_for(monkeypatch: pytest.MonkeyPatch, kind: str) -> None:
    original = cm._insert_cross_store_binding
    fired = {"done": False}

    def wrapped(connection: sqlite3.Connection, **kwargs: Any) -> str:
        if kwargs["kind"] == kind and not fired["done"]:
            fired["done"] = True
            message = f"injected crash before the {kind} binding"
            raise RuntimeError(message)
        return original(connection, **kwargs)

    monkeypatch.setattr(cm, "_insert_cross_store_binding", wrapped)


def _never(name: str) -> Any:
    def reached(*args: Any, **kwargs: Any) -> Any:
        message = f"{name} ran again over converged cross-store state"
        raise AssertionError(message)

    return reached


# ==========================================================================
# Sidecar
# ==========================================================================
def test_x01_an_authentic_sidecar_without_a_binding_is_bound_without_a_rebuild(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    _raise_once_for(monkeypatch, cm._BINDING_SIDECAR)
    with pytest.raises(RuntimeError, match="sidecar binding"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert sidecar.is_file() and r19.stage_ids(estate.catalog)[-1] == "S17C"
    monkeypatch.setattr(cm, "_merge_sidecar", _never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    unit = [cm.AppliedUnit.from_row(r) for r in r19.applied_units(estate.catalog)][-1]
    assert estate.legacy is not None
    legacy = estate.legacy["final"].as_record()
    assert unit.outcome_witness["completeness_digest"] == legacy["completeness_digest"]
    assert unit.outcome_witness["member_manifest_digest"] == legacy["member_manifest_digest"]
    assert len(unit.outcome_witness["binding_identity"]) == 64  # type: ignore[arg-type]


def test_x02_a_partial_sidecar_is_preserved_and_refused_never_overwritten(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S17C"))
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    partial = sqlite3.connect(sidecar)
    partial.execute("CREATE TABLE compact_source_evidence (source_observation_id TEXT)")
    partial.close()
    payload = sidecar.read_bytes()
    with pytest.raises(
        cm.ChunkMultipassError, match="preserved exactly as it is and never rebuilt"
    ):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert sidecar.read_bytes() == payload
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"


# ==========================================================================
# mark_parsed, reauthentication, F0 checkpoint
# ==========================================================================
def test_x03_mark_parsed_converges_and_a_binding_without_a_mark_conflicts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    _raise_once_for(monkeypatch, cm._BINDING_MARK_PARSED)
    with pytest.raises(RuntimeError, match="mark_parsed binding"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S20P"))
    ledger = RunProgressLedger(estate.world / PROGRESS_LEDGER_FILENAME)
    try:
        progress = ledger.progress(estate.run["plan"].source_instance_id)
    finally:
        ledger.close()
    assert progress is not None and progress.state == "parsed"
    assert r19.stage_ids(estate.catalog)[-1] == "S19"
    monkeypatch.setattr(RunProgressLedger, "mark_parsed", _never("mark_parsed"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S20P"))
    assert outcome.completed_stage_ids[-1] == "S20P"
    monkeypatch.undo()
    # The other store rolled back behind the binding: conflict, before any later stage.
    ledger_connection = sqlite3.connect(
        estate.world / PROGRESS_LEDGER_FILENAME, isolation_level=None
    )
    try:
        ledger_connection.execute("UPDATE run_source_progress SET state = 'in_progress'")
    finally:
        ledger_connection.close()
    with pytest.raises(cm.ChunkMultipassError, match="ledger is not parsed"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S21P"))


def test_x04_a_changed_input_is_caught_before_any_checkpoint_and_a_retained_request_is_legal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S20P"))
    ledger = RunProgressLedger(estate.world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()
    root = Path(estate.succ["intermediates_root"])
    group = estate.schedule.groups[0]
    receipt = root / group.group_id / "attempt-000" / cm.INTERMEDIATE_RECEIPT_FILENAME
    original = receipt.read_bytes()
    # A receipt that changed BEFORE this process started: the fresh StagePlan disagrees with the
    # sealed one and the world refuses at its first reopen, before any stage runs.
    receipt.write_bytes(original + b"\n")
    with pytest.raises(cm.ChunkMultipassError, match="minimal StagePlan identity"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S22P"))
    assert r19.stage_ids(estate.catalog)[-1] == "S20P"
    receipt.write_bytes(original)
    # A receipt that changes AFTER admission and before S21P: the terminal reauthentication
    # re-derives every descriptor and refuses before any checkpoint exists.
    prepare = cm._prepare_stage

    def change_then_prepare(ctx: Any, stage: Any, units: Any, instr: Any) -> Any:
        if stage.stage_id == "S21P":
            receipt.write_bytes(original + b"\n")
        return prepare(ctx, stage, units, instr)

    monkeypatch.setattr(cm, "_prepare_stage", change_then_prepare)
    with pytest.raises(cm.ChunkMultipassError, match="changed after the merge"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S22P"))
    monkeypatch.undo()
    assert r19.stage_ids(estate.catalog)[-1] == "S20P"
    ledger = RunProgressLedger(estate.world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()
    receipt.write_bytes(original)
    # A changed selected request is a changed StagePlan; a retained request of another attempt
    # ordinal is not ambiguity and changes nothing.
    request = root / group.group_id / f"{group.group_id}-000-request.json"
    request_bytes = request.read_bytes()
    request.write_bytes(request_bytes + b"\n")
    with pytest.raises(cm.ChunkMultipassError, match="minimal StagePlan identity"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S22P"))
    request.write_bytes(request_bytes)
    (root / group.group_id / f"{group.group_id}-007-request.json").write_bytes(b"{}")
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S22P"))
    assert outcome.completed_stage_ids[-2:] == ("S21P", "S22P")
    ledger = RunProgressLedger(estate.world / PROGRESS_LEDGER_FILENAME)
    try:
        checkpoint = read_phase_checkpoint(ledger, PHASE_F0)
    finally:
        ledger.close()
    assert checkpoint is not None and checkpoint.run_id == "r19-successor"


def test_x05_an_existing_f0_checkpoint_is_bound_without_a_second_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    _raise_once_for(monkeypatch, cm._BINDING_F0_CHECKPOINT)
    with pytest.raises(RuntimeError, match="f0_checkpoint binding"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S22P"))
    assert r19.stage_ids(estate.catalog)[-1] == "S21P"
    monkeypatch.setattr(cm, "write_phase_checkpoint", _never("write_phase_checkpoint"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached and outcome.final_receipt is not None
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_x06_the_gate_cannot_be_bypassed_and_the_final_record_is_published_last(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)

    def blocking(outcome: Any) -> Any:
        message = "injected blocking terminal"
        raise SingleSourceCanaryError(message)

    monkeypatch.setattr(cm, "require_f0_success", blocking)
    with pytest.raises(SingleSourceCanaryError, match="blocking terminal"):
        cm.run_successor_multipass_final(r19.production_request(estate))
    # Decision 151 Boundary 4: the SAME accepted predicate is consulted over the committed S2
    # reduced run before any statement of S3 begins, so an unconditional refusal stops the spine
    # at S2 and publishes a create-once semantic-refusal record; nothing of S3 was executed.
    assert r19.stage_ids(estate.catalog)[-1] == "S2"
    refusals = sorted(
        path.name for path in estate.receipt_root.iterdir() if path.name.startswith("semantic-")
    )
    assert refusals == ["semantic-refusal-S3-attempt-000.json"]
    refusal = json.loads((estate.receipt_root / refusals[0]).read_text(encoding="utf-8"))
    assert refusal["contract"] == cm.L2_SEMANTIC_REFUSAL_CONTRACT
    assert refusal["refused_stage_id"] == "S3" and refusal["s3_statements_begun"] == 0

    def blocking_at_s19(outcome: Any) -> Any:
        # The Boundary 4 outcome carries no sidecar totals yet (S18 has not run); the complete
        # S19 outcome does. Admitting the former and refusing the latter reaches the S19 gate.
        if outcome.members > 0:
            message = "injected blocking terminal"
            raise SingleSourceCanaryError(message)
        return outcome

    monkeypatch.setattr(cm, "require_f0_success", blocking_at_s19)
    with pytest.raises(SingleSourceCanaryError, match="blocking terminal"):
        cm.run_successor_multipass_final(r19.production_request(estate))
    assert r19.stage_ids(estate.catalog)[-1] == "S18"
    assert not (estate.world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    ledger = RunProgressLedger(estate.world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
        progress = ledger.progress(estate.run["plan"].source_instance_id)
    finally:
        ledger.close()
    assert progress is not None and progress.state == "in_progress"
    monkeypatch.undo()
    seen: list[list[str]] = []
    original = write_once_json

    def observed(path: Path, document: Any) -> Path:
        if path.name == FINAL_WORLD_RECEIPT_FILENAME:
            seen.append(r19.stage_ids(estate.catalog))
        return original(path, document)

    monkeypatch.setattr(cm, "write_once_json", observed)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached
    assert seen == [list(r19.PRODUCTION_STAGE_IDS_10)]


# ==========================================================================
# The calibration terminal, in-process under an issued envelope
# ==========================================================================
def calibration_estate(tmp_path: Path) -> dict[str, Any]:
    """The C29R1 small world under groupwise deletion, with the accepted request documents."""
    database, _tree, run, partial = c29.small_run(tmp_path)
    out = c29.lifecycle(run, partial, database, delete=True)
    for group, receipt in zip(partial["schedule"].groups, out["receipts"], strict=True):
        directory = cm.intermediate_attempt_directory(
            partial["intermediates_root"], group.group_id, receipt.attempt
        )
        request, _ = c27.group_request(run, partial, group, database, receipt.attempt)
        write_once_json(
            directory.parent / f"{group.group_id}-{receipt.attempt:03d}-request.json",
            dict(request.as_record()),
        )
    return {"database": database, "run": run, "partial": partial, "groups": out["receipts"]}


def calibration_request(
    estate: dict[str, Any], *, stop_after: str | None = None
) -> cm.SuccessorFinalRequest:
    assert c1.PINNED is not None
    partial = estate["partial"]
    world = partial["multipass_root"] / "successor-final"
    return cm.SuccessorFinalRequest(
        route=cm.SUCCESSOR_ROUTE_CALIBRATION,
        plan_path=str(estate["run"]["plan_path"]),
        schedule_path=str(partial["schedule_path"]),
        intermediates_root=str(partial["intermediates_root"]),
        internal_root=str(estate["run"]["chunk_root"]),
        external_root=None,
        operational_catalog=str(estate["database"]),
        world_directory=str(world),
        stage_receipt_root=str(partial["multipass_root"] / "successor-receipts"),
        run_id="r19-calibration",
        predecessor_run_id=c29.RUN,
        predecessor_checkpoint_count=0,
        predecessor_tip_ordinal=0,
        predecessor_tip_identity="none",
        predecessor_completed_group_count=len(partial["schedule"].groups),
        cache_bytes=cm.DEFAULT_SYNTHETIC_CACHE_BYTES,
        repository_head_sha=c1.PINNED.head_sha,
        repository_tree_sha=c1.PINNED.tree_sha,
        storage_requirements=dict(c13.LEVEL_DISTINCT_REQUIREMENTS.as_record()),
        expected_sqlite_temp_binding=c13.synthetic_expected_binding(world),
        statement_observability=dict(r19.SYNTHETIC_OBSERVABILITY),
        stop_after_stage=stop_after,
    )


def run_calibration_in_process(
    estate: dict[str, Any], request: cm.SuccessorFinalRequest
) -> cm.SuccessorRunOutcome:
    """The successor calibration child body in THIS process, under a freshly issued envelope."""
    partial = estate["partial"]
    receipt_root = Path(request.stage_receipt_root)
    receipt_root.mkdir(parents=True, exist_ok=True)
    launch = len(list(receipt_root.glob("successor-request-*.json")))
    request_path = receipt_root / f"successor-request-{launch:03d}.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = c27.issued(
        plan=estate["run"]["plan"],
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="successor-final",
        request_path=request_path,
        run_id=request.run_id,
        ledger=partial["ledger"],
    )
    return cm._successor_calibration_final_body(request, envelope)


def test_x07_the_calibration_terminal_converges_and_equals_the_legacy_calibration_final(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = calibration_estate(tmp_path)
    legacy = c29.final_in_process(
        estate["run"], estate["partial"], estate["database"], label="legacy"
    )
    world = Path(calibration_request(estate).world_directory)
    catalog = world / r19.WORKING_CATALOG_FILENAME
    original = cm.write_once_canonical_json
    fired = {"done": False}

    def crash_once(path: Path, document: Any) -> Path:
        if path.name == cm.CALIBRATION_SUBSET_RESULT_FILENAME and not fired["done"]:
            fired["done"] = True
            message = "injected crash before the calibration result"
            raise RuntimeError(message)
        return original(path, document)

    monkeypatch.setattr(cm, "write_once_canonical_json", crash_once)
    with pytest.raises(RuntimeError, match="before the calibration result"):
        run_calibration_in_process(estate, calibration_request(estate))
    assert r19.stage_ids(catalog)[-1] == "S21C"
    assert not (world / cm.CALIBRATION_SUBSET_RESULT_FILENAME).exists()
    monkeypatch.setattr(cm, "_run_stage", _never("_run_stage"))
    outcome = run_calibration_in_process(estate, calibration_request(estate))
    assert outcome.terminal_reached and outcome.calibration_result is not None
    assert c29.semantic(outcome.calibration_result) == c29.semantic(legacy)
    ids = r19.stage_ids(catalog)
    assert "S15P" not in ids and ids[-2:] == ["S20C", "S21C"]
    events = sorted(
        p.name
        for p in estate["partial"]["ledger"].iterdir()
        if p.name.startswith("admission-final-successor")
    )
    assert events == ["admission-final-successor-final-attempt-000.json"]
    # A result without its RESULT_READY unit is a conflict, never a silent re-publication.
    connection = r19.writer(catalog)
    try:
        connection.execute(f"DELETE FROM main.{cm.L2_APPLIED_UNITS_TABLE} WHERE stage_id = 'S21C'")  # noqa: S608
    finally:
        connection.close()
    monkeypatch.undo()
    with pytest.raises(cm.ChunkMultipassError, match="no RESULT_READY unit"):
        run_calibration_in_process(estate, calibration_request(estate))
    assert (
        json.loads((world / cm.CALIBRATION_SUBSET_RESULT_FILENAME).read_bytes())["run_id"]
        == "r19-calibration"
    )


def test_x08_an_envelope_bound_to_another_plan_refuses_the_child_body_before_the_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = calibration_estate(tmp_path)
    other_database, other_tree = c27.small_world(tmp_path / "other")
    other = c27.subset_plan(other_tree, other_database, prefix=9)
    request = calibration_request(estate)
    request_path = Path(request.stage_receipt_root) / "successor-request-999.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    write_once_json(request_path, dict(request.as_record()))
    foreign = c27.issued(
        plan=other,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="successor-final",
        request_path=request_path,
        run_id=request.run_id,
        ledger=estate["partial"]["ledger"],
    )
    monkeypatch.setattr(cm, "_run_successor_final", _never("_run_successor_final"))
    with pytest.raises(ce.ChunkExecutionError, match="does not describe this work"):
        cm._successor_calibration_final_body(request, foreign)
    assert not Path(request.world_directory).exists()
