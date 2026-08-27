"""D151-C15: the D151-C14 corrections, proved behaviourally against the COMMITTED tree.

**C14-MAJOR-1 and C14-MINOR-3 -- the authority is load-bearing.** This module's fixture pins the
repository and nothing else: ``REAL_MULTIPASS_F0_AUTHORITY`` is the committed literal, ``None``,
and the drivers that open it for synthetic execution are deliberately not applied to the refusal
proofs. A01-A08 call every world-creating entry -- the orchestrator, both launchers, both merge
bodies and the child entry point, in-process and as a real child under the PRODUCTION bootstrap --
and require the authority refusal before the first filesystem mutation, with tripwires on every
later gate so that the ORDER is proved and not only the outcome. B01-B03 open the gate with a
test-only monkeypatch and require the same entries to complete, so the correction closes a gate
rather than an architecture; C1509 opens the authority, leaves the storage terms ``None`` and
requires the orchestrator to refuse on storage -- authority is necessary and not sufficient.
Opening the committed literal (mutation M15) is therefore killed here behaviourally, not by an
assertion on the literal.

**C14-MINOR-1 -- the four correction counters are whole-F0.** The accepted single-pass receipt
reports the cross-chunk first-witness correction its consolidation applied over its plan's chunks.
C15 derives the multipass receipt's four counters over ITS plan's chunks by the accepted definition,
and this module proves it three ways: against the accepted single-pass functions themselves over
the same ten chunks attached at once; against an independent restatement of the definition that
never sees a merge schedule, at 10, 18 and 34 chunks; and against the accepted single-pass receipt
of the same source wherever the accepted definition says the two partitions agree. It also states,
on the accepted path, the fact that bounds what any correction can promise: the accepted single-pass
counters are a function of the partition, not of the source alone.

**C14-MINOR-2 -- the post-merge input re-verification is live.** An input chunk artifact changed
after admission and attachment, before the merge's final re-verification, refuses the merge and
leaves no intermediate receipt.
"""

from __future__ import annotations

import ast
import inspect
import json
import sqlite3
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c13_intermediates as c13i  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402
import test_d151_c13_multipass_semantics as sem  # noqa: E402
import test_d151_c13_set_based_correction as sbc  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    write_once_json,
)
from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE_SIDECAR_FILENAME  # noqa: E402
from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

AUTHORITY_REFUSAL = "real multipass F0 consolidation is NOT AUTHORIZED"

#: Every production entry that can create a request document, an attempt directory, a child
#: process, an intermediate or a final world. The AST proof below holds each to the gate.
WORLD_CREATING_ENTRIES = (
    "run_multipass_f0",
    "run_group_merge",
    "run_final_merge",
    "merge_group_body",
    "finalize_multipass_body",
    "_child_main",
)


@pytest.fixture(autouse=True)
def _pinned_repository_only(tmp_path: Path) -> Any:
    """The accepted identity pin and NOTHING else: the authority stays the committed literal."""
    # No earlier test may have left the storage-term derivation patched on the production module.
    # The authority literal is deliberately NOT asserted here: the refusal proofs below hold the
    # entries to whatever the committed literal is, so an opened literal fails them behaviourally
    # rather than at setup (D151-C15 §13).
    assert cm.accepted_multipass_storage_requirements is ct.accepted_multipass_storage_requirements
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


def _tripwire(name: str) -> Any:
    def reached(*_args: Any, **_kwargs: Any) -> Any:
        message = f"{name} was reached; the authority refusal did not come first"
        raise AssertionError(message)

    return reached


def _arm(monkeypatch: pytest.MonkeyPatch, *names: str) -> None:
    for name in names:
        monkeypatch.setattr(cm, name, _tripwire(name))


def _open(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The test-only opening: the synthetic token in this process and in every merge child."""
    c13.open_synthetic_multipass(monkeypatch, temp_root=tmp_path / "sqlite-temp")
    monkeypatch.setattr(cm, "_CHILD_BOOTSTRAP", c13i.multipass_child_bootstrap(tmp_path / "repo"))


def _schedule_on_disk(run: dict[str, Any], root: Path) -> tuple[cm.MergeSchedule, Path]:
    schedule = cm.derive_merge_schedule(run["plan"])
    root.mkdir(parents=True, exist_ok=True)
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    return schedule, schedule_path


def _nothing_under(root: Path) -> None:
    assert not root.exists() or not any(root.rglob("*")), sorted(root.rglob("*"))


# ==========================================================================
# A01-A08: with the COMMITTED authority, every world-creating entry refuses first
# ==========================================================================
def test_c1501_a01_the_orchestrator_refuses_on_the_authority_before_anything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    _arm(
        monkeypatch,
        "accepted_multipass_storage_requirements",
        "require_multipass_plan",
        "require_clean_running_repository",
        "derive_merge_schedule",
        "resolve_chunk_inputs",
        "plan_multipass_storage",
        "run_group_merge",
        "run_final_merge",
        "_spawn_merge",
    )
    root = run["base"] / "orchestrated"
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root,
            run_id="a01",
        )
    assert not root.exists()


def test_c1502_a02_satisfiable_storage_terms_do_not_bypass_the_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The seam is gone; the strongest substitute -- valid terms from the derivation -- is inert."""
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    monkeypatch.setattr(cm, "accepted_multipass_storage_requirements", lambda: c13.REQUIREMENTS)
    _arm(monkeypatch, "require_multipass_plan", "resolve_chunk_inputs", "run_group_merge")
    root = run["base"] / "orchestrated"
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root,
            run_id="a02",
        )
    assert not root.exists()
    signature = inspect.signature(cm.run_multipass_f0)
    assert "injected_storage_requirements" not in signature.parameters


def test_c1503_a03_the_group_launcher_refuses_before_the_request_and_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "launched"
    schedule, schedule_path = _schedule_on_disk(run, root)
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", schedule.groups[0].group_id
    )
    _arm(monkeypatch, "_spawn_merge", "write_once_json", "_require_process_dead")
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_group_merge(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id=schedule.groups[0].group_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
            ),
            predecessor_pid=1,
        )
    assert not (root / "intermediates").exists()
    assert not list(root.glob("*-request.json"))


def test_c1504_a04_the_final_launcher_refuses_before_the_request_and_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "launched"
    _schedule, schedule_path = _schedule_on_disk(run, root)
    _arm(monkeypatch, "_spawn_merge", "write_once_json", "_require_process_dead")
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.run_final_merge(
            c13.final_request(
                run,
                schedule_path=schedule_path,
                intermediates_root=root / "intermediates",
                world_directory=root / "final",
                database=database,
                run_id="a04",
            ),
            predecessor_pid=1,
        )
    assert not (root / "final").exists()
    assert not list(root.glob("*-request.json"))


def test_c1505_a05_the_group_body_refuses_before_identity_plan_and_attempt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A request that would fail every later check fails on the authority first."""
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "body"
    _arm(
        monkeypatch,
        "_authenticate_running_repository",
        "_read_plan_and_schedule",
        "resolve_chunk_inputs",
        "_admit_merge_step",
    )
    request = replace(
        c13.group_request(
            run,
            schedule_path=root / "absent-schedule.json",
            group_id="group-0000",
            attempt=0,
            attempt_directory=root / "intermediates" / "group-0000" / "attempt-000",
            database=database,
        ),
        plan_path=str(root / "absent-plan.json"),
        repository_head_sha="a" * 40,
        repository_tree_sha="b" * 40,
    )
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.merge_group_body(request)
    _nothing_under(root)


def test_c1506_a06_the_final_body_refuses_before_identity_plan_and_world(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "body"
    _arm(
        monkeypatch,
        "_authenticate_running_repository",
        "_read_plan_and_schedule",
        "resolve_chunk_inputs",
        "resolve_intermediate_inputs",
        "_admit_merge_step",
    )
    request = replace(
        c13.final_request(
            run,
            schedule_path=root / "absent-schedule.json",
            intermediates_root=root / "intermediates",
            world_directory=root / "final",
            database=database,
            run_id="a06",
        ),
        plan_path=str(root / "absent-plan.json"),
        repository_head_sha="a" * 40,
        repository_tree_sha="b" * 40,
    )
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm.finalize_multipass_body(request)
    _nothing_under(root)


def _hand_written_request(tmp_path: Path, kind: str) -> tuple[Path, Path, dict[str, Any], Path]:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "hand-written"
    schedule, schedule_path = _schedule_on_disk(run, root)
    if kind == cm.MULTIPASS_REQUEST_KIND_GROUP:
        target = root / "intermediates" / schedule.groups[0].group_id / "attempt-000"
        request = c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=schedule.groups[0].group_id,
            attempt=0,
            attempt_directory=target,
            database=database,
        )
    else:
        target = root / "final"
        request = c13.final_request(
            run,
            schedule_path=schedule_path,
            intermediates_root=root / "intermediates",
            world_directory=target,
            database=database,
            run_id="hand-written",
        )
    path = root / f"{kind}-request.json"
    path.write_text(json.dumps(dict(request.as_record())), encoding="utf-8")
    return path, target, run, database


@pytest.mark.parametrize(
    "kind", [cm.MULTIPASS_REQUEST_KIND_GROUP, cm.MULTIPASS_REQUEST_KIND_FINAL], ids=["a07", "a08"]
)
def test_c1507_c1508_a_hand_written_child_request_refuses_in_the_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    path, target, _run, _database = _hand_written_request(tmp_path, kind)
    # 1. The child entry point, in-process: refused before the request is even read.
    _arm(monkeypatch, "_read_json_object", "merge_group_body", "finalize_multipass_body")
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm._child_main(str(path))
    with pytest.raises(cm.ChunkMultipassError, match=AUTHORITY_REFUSAL):
        cm._child_main(str(path.parent / "absent-request.json"))
    monkeypatch.undo()
    # 2. A REAL child under the PRODUCTION bootstrap, which nothing here has patched.
    assert "_child_main" in cm._CHILD_BOOTSTRAP and "REAL_MULTIPASS" not in cm._CHILD_BOOTSTRAP
    completed = subprocess.run(
        [sys.executable, "-c", cm._CHILD_BOOTSTRAP, str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode != 0
    assert AUTHORITY_REFUSAL in completed.stderr
    assert not target.exists()
    assert not (path.parent / "intermediates").exists() and not (path.parent / "final").exists()


# ==========================================================================
# C1509: authority is necessary, not sufficient
# ==========================================================================
def test_c1509_an_open_authority_with_none_storage_terms_refuses_on_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    monkeypatch.setattr(cm, "REAL_MULTIPASS_F0_AUTHORITY", c13.SYNTHETIC_AUTHORITY)
    assert cm.require_real_multipass_authority() == c13.SYNTHETIC_AUTHORITY
    derivation = cm.accepted_multipass_storage_requirements
    assert derivation is ct.accepted_multipass_storage_requirements, (
        derivation.__code__.co_filename,
        derivation.__code__.co_firstlineno,
    )
    assert ct.MULTIPASS_LEVEL_ONE_PEAK_RATIO is None
    assert ct.MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES is None
    assert ct.MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES is None
    _arm(monkeypatch, "require_multipass_plan", "resolve_chunk_inputs", "run_group_merge")
    root = run["base"] / "orchestrated"
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=root,
            run_id="c1509",
        )
    assert not root.exists()


# ==========================================================================
# B01-B03: the gate closes a door, not the architecture
# ==========================================================================
def test_c1510_c1511_b01_b02_the_bodies_complete_under_the_test_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    assert all(receipt.status == "complete" for receipt in partial["intermediates"])
    final = c13i.finalize(partial, run, database)
    assert final.status == "complete"
    assert (partial["multipass_root"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).is_file()


def test_c1512_b03_the_orchestrator_completes_under_the_test_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, tree, run = c13i.ten_chunk_run(tmp_path)
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "orchestrated",
        run_id="b03",
    )
    assert result.receipt["status"] == "complete"
    assert len(result.merge_pids) == len(result.schedule.groups)
    eq.assert_equivalent(eq.measure(tmp_path / "mono"), eq.measure(result.world_directory))


# ==========================================================================
# The committed source: the literal is None and the gate is the FIRST statement everywhere
# ==========================================================================
def test_c1527_the_committed_literal_is_none_and_every_entry_opens_with_the_gate() -> None:
    assert c13i.committed_literal(cm, "REAL_MULTIPASS_F0_AUTHORITY") is None
    tree = ast.parse(Path(cm.__file__).read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    for name in WORLD_CREATING_ENTRIES:
        body = functions[name].body
        first = body[1] if isinstance(body[0], ast.Expr) else body[0]  # past the docstring
        assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), name
        callee = first.value.func
        assert isinstance(callee, ast.Name) and callee.id == "require_real_multipass_authority"
    # The gate is reached by every world-creating entry and read by nothing else.
    callers = {
        node.name
        for node in functions.values()
        for call in ast.walk(node)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "require_real_multipass_authority"
    }
    assert callers == set(WORLD_CREATING_ENTRIES)


# ==========================================================================
# C1513-C1516: the four correction counters are whole-F0
# ==========================================================================
SHAPE: dict[str, Any] = {"filings": 2, "share_every": 3, "junk": 4, "unknown": 5, "duplicate": True}


def _multipass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, database: Path, tree: DataTree, label: str
) -> dict[str, Any]:
    _open(monkeypatch, tmp_path)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / f"run-{label}", database, tree)
    result = c13.merge_in_process(run, database, label=f"mp-{label}", run_id=label)
    result["run"] = run
    result["plan"] = plan
    return result


def _single_pass(
    tmp_path: Path, database: Path, tree: DataTree, *, chunk_members: int, label: str
) -> tuple[cc.ConsolidationResult, dict[str, Any]]:
    run = c1x.run_chunked_f0(
        tmp_path,
        database,
        tree,
        chunk_members=chunk_members,
        label=label,
        batch_size=c13.BATCH,
        repository=c1.PINNED,
    )
    consolidated = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id=label,
    )
    return consolidated, run


def _accepted_functions_over(
    tmp_path: Path, database: Path, plan: Any, run: dict[str, Any]
) -> tuple[int, int, int, int]:
    """The accepted single-pass correction FUNCTIONS, over every chunk of ``plan`` at once.

    Possible only up to the library's attachment limit -- ten on this host, which is why the
    ten-chunk world is the one that can be held to the accepted code itself rather than to a
    restatement of it.
    """
    inputs = cc.resolve_chunk_inputs(plan, internal_root=run["chunk_root"])
    assert len(inputs) <= cc.attachment_limit()
    world, aliases, _state = sbc._loaded_world(tmp_path / "accepted-over-all", database, inputs)
    try:
        contested, staged = cc._first_witness_corrections(world.connection, aliases)
    finally:
        world.__exit__(None, None, None)
    ledgers = sqlite3.connect(":memory:")
    ledgers.row_factory = sqlite3.Row
    try:
        witness_aliases = cc._attach_all(ledgers, [item.witness_path for item in inputs], "w")
        members, delta = cc._member_deltas(ledgers, witness_aliases)
    finally:
        ledgers.close()
    return contested, staged, members, delta


def test_c1513_w10_all_four_counters_equal_the_accepted_single_pass_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C14 measured 0/0/0/0 here against single-pass 3/35/4/25. Now: 3/35/4/25, three ways."""
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **SHAPE)
    single, single_run = _single_pass(tmp_path, database, tree, chunk_members=2, label="sp2")
    assert sem.correction_counters(single.receipt) == (3, 35, 4, 25)
    result = _multipass(tmp_path, monkeypatch, database, tree, "w10")
    final = result["final"]
    assert result["plan"].chunk_count == 10
    assert sem.correction_counters(final) == (3, 35, 4, 25)
    # 1. the accepted single-pass receipt of the same source (the owner's §16 values);
    assert sem.correction_counters(final) == sem.correction_counters(single.receipt)
    # 2. the accepted single-pass FUNCTIONS over the multipass plan's own ten chunks;
    assert sem.correction_counters(final) == _accepted_functions_over(
        tmp_path, database, result["plan"], result["run"]
    )
    # 3. the independent restatement, over the multipass chunks and over the single-pass chunks.
    assert sem.correction_counters(final) == sem.whole_f0_counters(
        c13.chunk_directories(result["run"])
    )
    assert sem.correction_counters(single.receipt) == sem.whole_f0_counters(
        c13.chunk_directories(single_run)
    )
    # And the world itself is the monolithic one.
    eq.monolithic_f0(database, tree, tmp_path / "mono")
    eq.assert_equivalent(eq.measure(tmp_path / "mono"), eq.measure(result["world_directory"]))


def test_c1514_w18_rows_staged_is_the_single_pass_fifty_not_the_naive_sixty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = c1.build_world(tmp_path, members=16, shards=2, **SHAPE)
    single, single_run = _single_pass(tmp_path, database, tree, chunk_members=3, label="sp3")
    assert sem.correction_counters(single.receipt) == (3, 50, 7, 50)
    result = _multipass(tmp_path, monkeypatch, database, tree, "w18")
    final = result["final"]
    assert result["plan"].chunk_count == 18
    assert [len(group.chunk_ids) for group in result["schedule"].groups] == [9, 7, 2]
    assert sem.correction_counters(final) == (3, 50, 7, 50)
    assert sem.correction_counters(final) == sem.correction_counters(single.receipt)
    assert sem.correction_counters(final) == sem.whole_f0_counters(
        c13.chunk_directories(result["run"])
    )
    assert sem.correction_counters(single.receipt) == sem.whole_f0_counters(
        c13.chunk_directories(single_run)
    )
    # The two wrong answers C14 measured, reproduced from the same artifacts and both refused.
    level_one_sum = sum(item.first_witness_rows_staged for item in result["intermediates"])
    intermediates = cm.resolve_intermediate_inputs(
        result["plan"], result["schedule"], intermediates_root=result["intermediates_root"]
    )
    world, aliases, _state = sbc._loaded_world(tmp_path / "level-two", database, intermediates)
    try:
        _contested, level_two_only = cm.stage_first_witness_corrections(world.connection, aliases)
    finally:
        world.__exit__(None, None, None)
    assert level_one_sum == 30 and level_two_only == 30
    assert final.first_witness_rows_staged == 50
    assert final.first_witness_rows_staged != level_two_only
    assert final.first_witness_rows_staged != level_one_sum + level_two_only == 60


def test_c1515_w34_every_receipt_is_the_accepted_definition_over_its_own_chunks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The thirty-four-chunk world, and the fact that bounds what a correction can promise.

    No partition of thirty-two primaries into at most nine chunks keeps every sharer of the shared
    accession in a chunk of its own, so the accepted single-pass counters of this source are
    different at every single-pass partition -- three receipts, three tuples, each exactly the
    accepted definition over its own chunks. The multipass receipt is that same definition over
    its thirty-four chunks, where every witness IS in a chunk of its own. Equality across
    partitions is therefore not a property the accepted field has; equality with the accepted
    definition over the receipt's own plan is, and it holds for all four receipts.
    """
    database, tree = c1.build_world(tmp_path, members=32, shards=2, **SHAPE)
    observed: dict[int, tuple[int, int, int, int]] = {}
    for chunk_members in (4, 5, 8):
        single, single_run = _single_pass(
            tmp_path, database, tree, chunk_members=chunk_members, label=f"sp{chunk_members}"
        )
        observed[chunk_members] = sem.correction_counters(single.receipt)
        assert observed[chunk_members] == sem.whole_f0_counters(c13.chunk_directories(single_run))
    assert observed[5] == (3, 55, 11, 65)  # the C14 §32 value
    assert len(set(observed.values())) == 3, observed
    result = _multipass(tmp_path, monkeypatch, database, tree, "w34")
    final = result["final"]
    assert result["plan"].chunk_count == 34
    assert [len(group.chunk_ids) for group in result["schedule"].groups] == [9, 9, 9, 5, 2]
    expected = sem.whole_f0_counters(c13.chunk_directories(result["run"]))
    assert sem.correction_counters(final) == expected
    assert expected[0] == 3 and expected[1] > observed[4][1] > observed[5][1] > observed[8][1]
    level_one = tuple(
        sum(getattr(item, field) for item in result["intermediates"])
        for field in sem.CORRECTION_COUNTERS
    )
    assert sem.correction_counters(final) != level_one


def test_c1516_the_counters_follow_the_chunks_and_never_the_grouping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Same source, three partitions that separate every witness, two of them multipass.

    Twenty-two chunks scheduled ``9 / 9 / 2 / 2``, eleven scheduled ``9 / 1 / 1`` and the
    accepted single-pass eight all report the same four counters, because all three place every
    sharer of the shared accession in a chunk of its own; the level-1 grouping decides nothing.
    The accepted single-pass five-chunk partition of the same source co-chunks two sharers and
    reports less -- the accepted field's own partition-dependence, stated and not concealed.
    """
    database, tree = c1.build_world(tmp_path, members=20, filings=2, shards=2, share_every=3)
    _open(monkeypatch, tmp_path)
    seen: dict[str, tuple[int, int, int, int]] = {}
    for chunk_members in (1, 2):
        plan = c13.multipass_plan(tree, database, chunk_members=chunk_members)
        run = c13.execute_in_process(plan, tmp_path / f"run{chunk_members}", database, tree)
        merged = c13.merge_in_process(run, database, label=f"mp{chunk_members}", run_id="g")
        shape = tuple(len(group.chunk_ids) for group in merged["schedule"].groups)
        seen[f"multipass {plan.chunk_count} chunks, groups {shape}"] = sem.correction_counters(
            merged["final"]
        )
        assert sem.correction_counters(merged["final"]) == sem.whole_f0_counters(
            c13.chunk_directories(run)
        )
    single, single_run = _single_pass(tmp_path, database, tree, chunk_members=3, label="sp3")
    assert single_run["plan"].chunk_count == 8
    seen["single-pass 8 chunks"] = sem.correction_counters(single.receipt)
    assert len(seen) == 3 and len(set(seen.values())) == 1, seen
    co_chunked, co_chunked_run = _single_pass(
        tmp_path, database, tree, chunk_members=6, label="sp6"
    )
    assert co_chunked_run["plan"].chunk_count == 5
    assert sem.correction_counters(co_chunked.receipt) == sem.whole_f0_counters(
        c13.chunk_directories(co_chunked_run)
    )
    assert sem.correction_counters(co_chunked.receipt) != next(iter(seen.values()))
    # The restatement the receipts are held to takes chunk directories and nothing else.
    assert list(inspect.signature(sem.whole_f0_counters).parameters) == ["chunk_directories"]


def test_the_accepted_single_pass_counters_are_a_function_of_the_partition(
    tmp_path: Path,
) -> None:
    """Stated on the accepted path alone, so no reader mistakes it for a multipass property."""
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **SHAPE)
    observed: dict[int, tuple[int, int, int, int]] = {}
    for chunk_members in (2, 3, 5, 9):
        single, _run = _single_pass(
            tmp_path, database, tree, chunk_members=chunk_members, label=f"n{chunk_members}"
        )
        observed[chunk_members] = sem.correction_counters(single.receipt)
    assert observed[2] == observed[3] == (3, 35, 4, 25)
    assert observed[5] == (3, 30, 3, 20)
    assert observed[9] == (0, 0, 0, 0)


def test_c1517_the_comparison_helper_compares_the_four_counters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database, tree = c1.build_world(tmp_path, members=9, shards=1, **SHAPE)
    single, single_run = _single_pass(tmp_path, database, tree, chunk_members=2, label="sp2")
    result = _multipass(tmp_path, monkeypatch, database, tree, "helper")
    sem._assert_same_final_semantics(
        single.receipt, result["final"], single_run=single_run, multipass_run=result["run"]
    )
    for field in sem.CORRECTION_COUNTERS:
        perturbed = replace(result["final"], **{field: getattr(result["final"], field) + 1})
        with pytest.raises(AssertionError):
            sem._assert_same_final_semantics(
                single.receipt, perturbed, single_run=single_run, multipass_run=result["run"]
            )


# ==========================================================================
# C1518: the post-merge input re-verification is live
# ==========================================================================
def test_c1518_an_input_chunk_changed_after_attachment_refuses_the_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _open(monkeypatch, tmp_path)
    database, _tree, run = c13i.ten_chunk_run(tmp_path)
    root = run["base"] / "reverify"
    schedule, schedule_path = _schedule_on_disk(run, root)
    group = schedule.groups[0]
    victim_directory = c13i.chunk_directory(run, 0)
    databases = {WORKING_CATALOG_FILENAME, COMPACT_EVIDENCE_SIDECAR_FILENAME, cc._WITNESS_FILENAME}
    manifested = [
        entry.relative_path
        for entry in run["receipts"][0].manifest.entries
        if entry.relative_path not in databases
    ]
    assert manifested, "the chunk manifests only its databases"
    victim = victim_directory / manifested[0]
    original = victim.read_bytes()
    real_attach = cm._attach_all
    fired: list[str] = []

    def attach_then_tamper(*args: Any, **kwargs: Any) -> Any:
        aliases = real_attach(*args, **kwargs)
        if not fired:
            fired.append("tampered")
            victim.write_bytes(original + b"\n")
        return aliases

    monkeypatch.setattr(cm, "_attach_all", attach_then_tamper)
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", group.group_id
    )
    with pytest.raises(ChunkEvidenceError, match="does not match the manifest") as refusal:
        cm.merge_group_body(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id=group.group_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
            )
        )
    assert fired == ["tampered"] and manifested[0] in str(refusal.value)
    assert not (directory / cm.INTERMEDIATE_RECEIPT_FILENAME).exists()
    assert cm.completed_intermediate_receipt(root / "intermediates", group.group_id) is None
