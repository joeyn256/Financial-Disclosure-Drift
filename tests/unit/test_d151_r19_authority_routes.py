"""D151-C31R2-R19A-C2 §15-§16: the two successor route gates, their proofs, and their pins.

* the production wrapper's absolute first operation is the real multipass authority, and with
  the committed ``None`` it refuses before any path is read, any plan parsed, any proof minted
  or any file created; its source names no retention-aware calibration machinery;
* the calibration wrapper's absolute first operation is the sealed calibration-subset plan; an
  envelope is never authority; the spawned child body requires the exact-role envelope first;
* the private engine refuses a missing, forged, persisted, cross-route or Boolean proof, and a
  withdrawn authority refuses at the NEXT stage's route gate rather than being carried;
* both wrappers are module-level, the exact production caller set is preserved, and no public
  generic resume exists.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c15_corrections as c15  # noqa: E402
import test_d151_c29r1_retention_aware_calibration as c29  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402

#: The explicit calibration-successor caller set -- §16: neither name is a production entry.
CALIBRATION_SUCCESSOR_ENTRIES = (
    "run_successor_calibration_final",
    "_successor_calibration_final_body",
)
AUTHORITY_REFUSAL = "real multipass F0 consolidation is NOT AUTHORIZED"


def _functions() -> dict[str, ast.FunctionDef]:
    tree = ast.parse(Path(cm.__file__).read_text(encoding="utf-8"))
    return {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}


def _first_call(name: str) -> str:
    body = _functions()[name].body
    first = body[1] if isinstance(body[0], ast.Expr) else body[0]
    value = first.value if isinstance(first, ast.Expr | ast.Assign) else None
    assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name), name
    return value.func.id


def _callers_of(gate: str) -> set[str]:
    return {
        node.name
        for node in _functions().values()
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == gate
    }


def _tripwire(name: str) -> Any:
    def reached(*_args: Any, **_kwargs: Any) -> Any:
        message = f"{name} was reached; the route gate did not come first"
        raise AssertionError(message)

    return reached


def _nonexistent_request(route: str = cm.SUCCESSOR_ROUTE_PRODUCTION) -> cm.SuccessorFinalRequest:
    return cm.SuccessorFinalRequest(
        route=route,
        plan_path="/nonexistent/r19/plan.json",
        schedule_path="/nonexistent/r19/schedule.json",
        intermediates_root="/nonexistent/r19/intermediates",
        internal_root="/nonexistent/r19/chunks",
        external_root=None,
        operational_catalog="/nonexistent/r19/catalog.sqlite3",
        world_directory="/nonexistent/r19/world",
        stage_receipt_root="/nonexistent/r19/receipts",
        run_id="r19",
        predecessor_run_id="none",
        predecessor_checkpoint_count=0,
        predecessor_tip_ordinal=0,
        predecessor_tip_identity="none",
        predecessor_completed_group_count=0,
        cache_bytes=cm.DEFAULT_SYNTHETIC_CACHE_BYTES,
        repository_head_sha="a" * 40,
        repository_tree_sha="b" * 40,
        storage_requirements=dict(r19.R19B_REQUIREMENTS.as_record()),
        expected_sqlite_temp_binding=dict(c13.INERT_BINDING_RECORD),
        statement_observability=dict(r19.SYNTHETIC_OBSERVABILITY),
    )


# ==========================================================================
# Structure: top-level wrappers, first gates, exact caller sets
# ==========================================================================
def test_f01_both_wrappers_are_top_level_open_with_their_gate_and_keep_the_caller_sets_exact() -> (
    None
):
    functions = _functions()
    assert {"run_successor_multipass_final", "run_successor_calibration_final"} <= set(functions)
    assert _first_call("run_successor_multipass_final") == "require_real_multipass_authority"
    assert _first_call("run_successor_calibration_final") == "require_calibration_subset_plan"
    assert _first_call("_successor_calibration_final_body") == "require_calibration_envelope"
    # The production gate's exact caller set is the accepted one plus the production wrapper.
    assert _callers_of("require_real_multipass_authority") == set(c15.WORLD_CREATING_ENTRIES)
    assert _callers_of("require_real_multipass_authority") == set(c29.PRODUCTION_ENTRIES)
    assert "run_successor_multipass_final" in c15.WORLD_CREATING_ENTRIES
    # No calibration-successor entry calls the production gate; none is in a production tuple.
    for name in CALIBRATION_SUCCESSOR_ENTRIES:
        assert name not in c15.WORLD_CREATING_ENTRIES and name not in c29.PRODUCTION_ENTRIES
        assert "require_real_multipass_authority" not in inspect.getsource(getattr(cm, name))
    # The private engine never calls either gate by name: it consumes a proof.
    for name in (
        "_run_successor_final",
        "_run_successor_stages",
        "_resolve_successor_context",
        "_run_stage",
    ):
        assert name not in _callers_of("require_real_multipass_authority"), name
        assert name not in _callers_of("require_calibration_subset_plan"), name
    # The successor engine section is reached only through the two wrappers and the child body.
    callers = _callers_of("_run_successor_final")
    assert callers == {"run_successor_multipass_final", "_successor_calibration_final_body"}


def test_f02_the_production_wrapper_names_no_retention_route_and_delegates_narrowly() -> None:
    source = inspect.getsource(cm.run_successor_multipass_final)
    for needle in c29.RETENTION_NAMES:
        assert needle not in source, needle
    assert source.count("_run_successor_final(") == 1
    body = _functions()["run_successor_multipass_final"].body
    calls = [
        node.func.id
        for statement in body
        for node in ast.walk(statement)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    ]
    assert calls[0] == "require_real_multipass_authority"
    assert calls.count("_mint_successor_route_proof") == 1


def test_f03_no_public_generic_resume_exists() -> None:
    assert not [name for name in cm.__all__ if "resume" in name.lower()]
    assert not [
        name for name in _functions() if "resume" in name.lower() and not name.startswith("_")
    ]
    assert not hasattr(cm, "resume_l2")


# ==========================================================================
# Behaviour: the gates come first, with the COMMITTED literal
# ==========================================================================
def test_f04_the_production_authority_none_refuses_before_any_path_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The authority literal is ALSO patched by the module's autouse seam fixture, whose own
    # MonkeyPatch is undone before this test's ``monkeypatch``: patching the same attribute
    # through ``monkeypatch`` would leak the seam's token after the test. A test-local context
    # restores it before any fixture teardown runs.
    with pytest.MonkeyPatch.context() as local:
        local.setattr(cm, "REAL_MULTIPASS_F0_AUTHORITY", None)
        for name in (
            "_authenticate_running_repository",
            "_read_plan_and_schedule",
            "resolve_chunk_inputs",
            "resolve_intermediate_inputs",
            "_mint_successor_route_proof",
            "_run_successor_final",
            "_resolve_successor_context",
            "_measured_successor_binding",
        ):
            local.setattr(cm, name, _tripwire(name))
        with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
            cm.run_successor_multipass_final(_nonexistent_request())
    assert not Path("/nonexistent/r19").exists()
    assert cm.REAL_MULTIPASS_F0_AUTHORITY == c13.SYNTHETIC_AUTHORITY


def test_f05_a_calibration_envelope_alone_is_never_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    for name in ("issue_calibration_envelope", "_spawn_calibration_child", "_run_successor_final"):
        monkeypatch.setattr(cm, name, _tripwire(name))
    # An ordinary multipass plan is not a sealed calibration-subset plan: refused FIRST.
    with pytest.raises(cp.ChunkPlanError, match="not a calibration-subset plan"):
        cm.run_successor_calibration_final(
            _nonexistent_request(cm.SUCCESSOR_ROUTE_CALIBRATION),
            calibration_plan=estate.run["plan"],
            instrumentation_ledger=tmp_path / "ledger",
        )
    assert not (tmp_path / "ledger").exists() and not Path("/nonexistent/r19").exists()
    # A hand-constructed correct-role envelope handed straight to the child body: the role gate
    # passes, then the sealed plan is required and no engine is entered.
    envelope = ce.CalibrationChildEnvelope(
        contract=ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT,
        run_id="r19",
        plan_digest="ab" * 32,
        selected_member_ceiling=1,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="successor-final",
        request_sha256="cd" * 32,
        parent_pid=1,
        nonce="ef" * 16,
        instrumentation_ledger=None,
    )
    with pytest.raises(ce.ChunkExecutionError, match="could not be read"):
        cm._successor_calibration_final_body(
            _nonexistent_request(cm.SUCCESSOR_ROUTE_CALIBRATION), envelope
        )
    # A wrong-role envelope refuses before the plan is even read.
    monkeypatch.setattr(cm, "_read_calibration_plan_and_schedule", _tripwire("plan read"))
    wrong = ce.CalibrationChildEnvelope(
        **{**dict(envelope.as_record()), "role": ce.CALIBRATION_ROLE_GROUP}
    )
    with pytest.raises(ce.ChunkExecutionError, match="refused before anything is read"):
        cm._successor_calibration_final_body(
            _nonexistent_request(cm.SUCCESSOR_ROUTE_CALIBRATION), wrong
        )


def test_f06_a_child_without_a_pid_bound_received_envelope_refuses(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(dict(_nonexistent_request(cm.SUCCESSOR_ROUTE_CALIBRATION).as_record()))
    )
    envelope = ce.CalibrationChildEnvelope(
        contract=ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT,
        run_id="r19",
        plan_digest="ab" * 32,
        selected_member_ceiling=1,
        role=ce.CALIBRATION_ROLE_FINAL,
        step_id="successor-final",
        request_sha256="cd" * 32,
        parent_pid=os.getpid(),  # THIS process, which is not this process's parent
        nonce="ef" * 16,
        instrumentation_ledger=None,
    )
    with ce.delivered_calibration_envelope(envelope) as descriptor:
        duplicate = os.dup(descriptor)  # the child's own copy; the parent closes its own
        with pytest.raises(ce.ChunkExecutionError, match="names parent pid"):
            cm._calibration_child_main(str(request_path), str(duplicate))


def test_f07_the_engine_refuses_every_non_proof_and_every_cross_route_proof(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    request = r19.production_request(estate)
    for stand_in in (None, True, "proof", {"route": "production"}, estate.run["plan"]):
        with pytest.raises(cm.ChunkMultipassError, match="requires a process-local route proof"):
            cm._run_successor_final(request, stand_in)  # type: ignore[arg-type]
    forged = cm._SuccessorRouteProof(
        route=cm.SUCCESSOR_ROUTE_PRODUCTION,
        pid=os.getpid(),
        nonce="not-the-process-nonce",
        gate_name="require_real_multipass_authority",
        gate=lambda: None,
        envelope=None,
        plan_digest=None,
    )
    with pytest.raises(cm.ChunkMultipassError, match="not minted by a route gate in this process"):
        cm._run_successor_final(request, forged)
    calibration = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_CALIBRATION, gate=lambda: None, gate_name="test"
    )
    with pytest.raises(cm.ChunkMultipassError, match="never crosses routes"):
        cm._run_successor_final(request, calibration)
    production = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=lambda: None, gate_name="test"
    )
    with pytest.raises(cm.ChunkMultipassError, match="never crosses routes"):
        production.require_live(cm.SUCCESSOR_ROUTE_CALIBRATION)

    # A proof whose bound gate refuses refuses live, every time it is asked.
    def refusing() -> object:
        message = "the bound gate refuses"
        raise cm.ChunkMultipassError(message)

    refused = cm._mint_successor_route_proof(
        cm.SUCCESSOR_ROUTE_PRODUCTION, gate=refusing, gate_name="r"
    )
    with pytest.raises(cm.ChunkMultipassError, match="the bound gate refuses"):
        refused.require_live(cm.SUCCESSOR_ROUTE_PRODUCTION)
    assert not estate.world.exists()


def test_f08_a_withdrawn_authority_refuses_at_the_next_stage_and_the_world_stays_where_it_was(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path)
    original = cm._run_stage

    # Same-attribute rule as test_f04: the withdrawal goes through a test-local MonkeyPatch that
    # is undone inside the test, never through the fixture-ordered ``monkeypatch``.
    local = pytest.MonkeyPatch()

    def withdraw_after_s3(ctx: Any, stage: Any, prior: Any, *args: Any, **kwargs: Any) -> None:
        # D151-C31R2-R19B-C2: the stage loop also hands _run_stage the classification
        # session's WAL disposition; the wrapper forwards whatever it is given.
        original(ctx, stage, prior, *args, **kwargs)
        if stage.stage_id == "S3":
            local.setattr(cm, "REAL_MULTIPASS_F0_AUTHORITY", None)

    monkeypatch.setattr(cm, "_run_stage", withdraw_after_s3)
    try:
        with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
            cm.run_successor_multipass_final(r19.production_request(estate))
        assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2", "S3"]
        assert len(r19.receipt_files(estate.receipt_root)) == 4
    finally:
        local.undo()
    assert cm.REAL_MULTIPASS_F0_AUTHORITY == c13.SYNTHETIC_AUTHORITY
    monkeypatch.setattr(cm, "_run_stage", original)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.terminal_reached
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_f09_the_legacy_children_refuse_a_successor_request(tmp_path: Path) -> None:
    request_path = tmp_path / "successor-request.json"
    payload = json.dumps(dict(_nonexistent_request(cm.SUCCESSOR_ROUTE_CALIBRATION).as_record()))
    request_path.write_text(payload)
    # The production child refuses the kind outright (after its authority gate).
    with pytest.raises(cm.ChunkMultipassError, match="not one this build executes"):
        cm._child_main(str(request_path))
    # The calibration child dispatches the successor kind ONLY under the final role: a group
    # envelope over the very same bytes, received through the real pipe, refuses.
    envelope = ce.CalibrationChildEnvelope(
        contract=ce.CALIBRATION_CHILD_ENVELOPE_CONTRACT,
        run_id="r19",
        plan_digest="ab" * 32,
        selected_member_ceiling=1,
        role=ce.CALIBRATION_ROLE_GROUP,
        step_id="group-0000",
        request_sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
        parent_pid=os.getppid(),
        nonce="ef" * 16,
        instrumentation_ledger=None,
    )
    with ce.delivered_calibration_envelope(envelope) as descriptor:
        duplicate = os.dup(descriptor)
        with pytest.raises(cm.ChunkMultipassError, match="the two must agree"):
            cm._calibration_child_main(str(request_path), str(duplicate))
