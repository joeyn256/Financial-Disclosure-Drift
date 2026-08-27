"""D151-C13: intermediates are create-once, authenticated and nonterminal; merges own a process.

A level-1 intermediate is a first-class artifact: it carries a manifest over every file, a
create-once receipt written last that binds the multipass plan, the merge schedule, its group,
every input chunk by identity and receipt digest, the source, the execution contract and the code
that ran it, and it is re-verified byte-exactly at every consumption. This module attacks every
one of those bindings (A12-A18), proves the crash/restart semantics the record requires -- reuse
of a valid intermediate, a fresh attempt beside a dead one, ambiguity refused, and a completed
intermediate whose bytes moved refused LOUDLY rather than reinterpreted as never run -- and proves
the process contract: every level-1 merge and the finalization run in their own operating-system
process, each proved gone before the next begins.

It also carries the closure proofs for the two new modules: every authority ``None``, no
environment or configuration route, no command-line reach, no removal capability, no transport,
and importable without a world.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402
import test_d151_c10_calibration_plan_width as c10  # noqa: E402
import test_d151_c13_multipass_plan as c13  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import repository_identity  # noqa: E402
from disclosure_drift.m3.canary_phases import PHASE_F0, read_phase_checkpoint  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_PLAN_FILENAME,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    file_sha256,
    read_receipt_document,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE_SIDECAR_FILENAME  # noqa: E402
from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

NEW_MODULES = (cm, ct)


def multipass_child_bootstrap(root: Path) -> str:
    """The production merge-child bootstrap with the accepted identity seam applied inside it."""
    return (
        "import sys;"
        "from pathlib import Path;"
        "from disclosure_drift.m3 import repository_identity as ri;"
        f"ri.running_repository_identity = lambda: ri.repository_identity_at(Path({str(root)!r}));"
        # D151-C15 R2: the child requires the real multipass authority before it reads its
        # request, so a synthetic child is opened here, in test code, exactly as the parent is.
        "from disclosure_drift.m3 import chunk_multipass as cm;"
        f"cm.REAL_MULTIPASS_F0_AUTHORITY = {c13.SYNTHETIC_AUTHORITY!r};"
        "from disclosure_drift.m3.chunk_multipass import _child_main;"
        "sys.exit(_child_main(sys.argv[1]))"
    )


def committed_literal(module: Any, name: str) -> object:
    """The value a module-level constant is assigned in the COMMITTED source, read by AST."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    for node in tree.body:
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            return ast.literal_eval(node.value)
    message = f"{name} is not assigned at module level"
    raise AssertionError(message)


def refusal_in_a_fresh_interpreter() -> str:
    """Call the COMMITTED authority gate in a new process; return the refusal it prints."""
    program = (
        "from disclosure_drift.m3.chunk_multipass import require_real_multipass_authority as r;r()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program], capture_output=True, text=True, check=False
    )
    assert completed.returncode != 0
    return completed.stderr


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin, and the same redirect inside every merge child this module spawns."""
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    c13.open_synthetic_multipass(patcher)
    patcher.setattr(cm, "_CHILD_BOOTSTRAP", multipass_child_bootstrap(tmp_path / "repo"))
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# Shared drivers
# ==========================================================================
def ten_chunk_run(tmp_path: Path, **shape: Any) -> tuple[Path, DataTree, dict[str, Any]]:
    shape.setdefault("members", 9)
    shape.setdefault("shards", 1)
    shape.setdefault("filings", 2)
    shape.setdefault("share_every", 3)
    database, tree = c1.build_world(tmp_path, **shape)
    plan = c13.multipass_plan(tree, database, chunk_members=1)
    run = c13.execute_in_process(plan, tmp_path / "run", database, tree)
    return database, tree, run


def intermediate_directory(partial: dict[str, Any], index: int) -> Path:
    group = partial["schedule"].groups[index]
    receipt = partial["intermediates"][index]
    return partial["intermediates_root"] / group.group_id / f"attempt-{receipt.attempt:03d}"


def chunk_directory(run: dict[str, Any], index: int) -> Path:
    receipt = run["receipts"][index]
    return run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"


def edit_json(path: Path, mutate: Any) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    mutate(document)
    path.write_text(json.dumps(document, indent=2, sort_keys=True), encoding="utf-8")


def resolve(partial: dict[str, Any], run: dict[str, Any]) -> tuple[cm.IntermediateInput, ...]:
    return cm.resolve_intermediate_inputs(
        run["plan"],
        partial["schedule"],
        intermediates_root=partial["intermediates_root"],
        internal_root=run["chunk_root"],
    )


def finalize(partial: dict[str, Any], run: dict[str, Any], database: Path, suffix: str = "") -> Any:
    return cm.finalize_multipass_body(
        c13.final_request(
            run,
            schedule_path=partial["schedule_path"],
            intermediates_root=partial["intermediates_root"],
            world_directory=partial["multipass_root"] / f"final{suffix}",
            database=database,
            run_id=f"final{suffix}",
        )
    )


# ==========================================================================
# I01-I03: the intermediate receipt and manifest
# ==========================================================================
def test_i01_the_receipt_binds_everything_the_record_requires(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    assert c1.PINNED is not None
    for index, group in enumerate(partial["schedule"].groups):
        receipt = partial["intermediates"][index]
        directory = intermediate_directory(partial, index)
        assert receipt.contract == cm.INTERMEDIATE_RECEIPT_CONTRACT
        assert receipt.plan_digest == run["plan"].plan_digest
        assert receipt.merge_schedule_digest == partial["schedule"].schedule_digest
        assert (receipt.group_id, receipt.group_ordinal, receipt.region) == (
            group.group_id,
            group.ordinal,
            group.region,
        )
        assert (receipt.start, receipt.end) == (group.start, group.end)
        assert receipt.input_chunk_ids == group.chunk_ids
        # Every input receipt digest is the digest of the receipt document on disk, and every
        # input manifest digest is the chunk's own.
        for chunk_id, bound, manifest in zip(
            receipt.input_chunk_ids,
            receipt.input_receipt_sha256,
            receipt.input_manifest_digests,
            strict=True,
        ):
            chunk_receipt, chunk_dir = ce.completed_chunk_receipt(run["chunk_root"], chunk_id)
            assert bound == file_sha256(chunk_dir / CHUNK_RECEIPT_FILENAME)[0]
            assert manifest == chunk_receipt.manifest.digest
        assert [item["chunk_id"] for item in receipt.chunk_inputs] == list(group.chunk_ids)
        assert receipt.source_sha256 == run["plan"].source_sha256
        assert receipt.member_order_digest == run["plan"].member_order_digest
        assert receipt.repository_head_sha == c1.PINNED.head_sha
        assert receipt.repository_tree_sha == c1.PINNED.tree_sha
        assert receipt.execution_contract == run["receipts"][0].execution_contract
        assert len(receipt.parser_run_id) == 64
        assert len(receipt.witness_ledger_identity) == 64
        assert len(receipt.compact_evidence_identity) == 64
        assert receipt.storage_admission["admitted"] is True
        assert receipt.status == "complete" and receipt.pid == os.getpid()
        # The manifest names every file but the receipt, and it verifies.
        named = {entry.relative_path for entry in receipt.manifest.entries}
        present = {
            path.relative_to(directory).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        }
        assert present == named | {cm.INTERMEDIATE_RECEIPT_FILENAME}
        assert named >= {
            WORKING_CATALOG_FILENAME,
            COMPACT_EVIDENCE_SIDECAR_FILENAME,
            cm.INTERMEDIATE_WITNESS_FILENAME,
            PROGRESS_LEDGER_FILENAME,
            CHUNK_PLAN_FILENAME,
            cm.MERGE_SCHEDULE_FILENAME,
        }
        catalog_entry = next(
            e for e in receipt.manifest.entries if e.relative_path == WORKING_CATALOG_FILENAME
        )
        assert receipt.catalog_sha256 == catalog_entry.sha256
        verify_artifact_manifest(
            directory, receipt.manifest, exclude=(cm.INTERMEDIATE_RECEIPT_FILENAME,)
        )
        stored = read_receipt_document(
            directory / cm.INTERMEDIATE_RECEIPT_FILENAME, contract=cm.INTERMEDIATE_RECEIPT_CONTRACT
        )
        assert cm.IntermediateReceipt.from_record(stored) == receipt
        plan_copy = json.loads((directory / CHUNK_PLAN_FILENAME).read_text(encoding="utf-8"))
        assert cp.ChunkPlan.from_record(plan_copy) == run["plan"]
        schedule_copy = json.loads(
            (directory / cm.MERGE_SCHEDULE_FILENAME).read_text(encoding="utf-8")
        )
        assert cm.MergeSchedule.from_record(schedule_copy) == partial["schedule"]
    assert [item.group_id for item in resolve(partial, run)] == [
        g.group_id for g in partial["schedule"].groups
    ]


def test_i02_the_reduced_witness_ledger_holds_one_row_per_identity(tmp_path: Path) -> None:
    """One reduced row per native identity: the group's first witness, canonical ordinal kept."""
    import sqlite3

    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    for index, group in enumerate(partial["schedule"].groups):
        directory = intermediate_directory(partial, index)
        reduced = sqlite3.connect(
            f"file:{directory / cm.INTERMEDIATE_WITNESS_FILENAME}?immutable=1", uri=True
        )
        try:
            rows = reduced.execute(
                "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                "FROM chunk_first_witness ORDER BY native_identity"
            ).fetchall()
            meta = dict(reduced.execute("SELECT key, value FROM chunk_witness_meta").fetchall())
        finally:
            reduced.close()
        assert meta["group_id"] == group.group_id and meta["level"] == "1"
        # Recomputed from the input chunks' own ledgers: the minimum ordinal per identity.
        expected: dict[str, tuple[int, int, int]] = {}
        for chunk_id in group.chunk_ids:
            _receipt, chunk_dir = ce.completed_chunk_receipt(run["chunk_root"], chunk_id)
            ledger = sqlite3.connect(
                f"file:{chunk_dir / 'chunk_witness.sqlite3'}?immutable=1", uri=True
            )
            try:
                for identity, member, record, delta in ledger.execute(
                    "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                    "FROM chunk_first_witness"
                ):
                    if identity not in expected or (member, record) < expected[identity][:2]:
                        expected[identity] = (member, record, delta)
            finally:
                ledger.close()
        assert {row[0]: row[1:] for row in rows} == expected
        assert len(rows) == len({row[0] for row in rows})
        assert all(group.start <= row[1] < group.end for row in rows)


# ==========================================================================
# A12-A18: every binding, attacked
# ==========================================================================
def test_a12_a_changed_input_receipt_digest_is_refused(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    # The chunk receipt on disk is rewritten with the same content -- byte-different, artifact
    # bytes untouched, its own manifest still green -- and the intermediate that bound its digest
    # refuses.
    # A field the accepted admission never compares, so the chunk still counts as completed.
    target = chunk_directory(run, 3) / CHUNK_RECEIPT_FILENAME
    edit_json(target, lambda document: document.__setitem__("rss_peak_bytes", 1))
    assert ce.completed_chunk_receipt(run["chunk_root"], run["receipts"][3].chunk_id) is not None
    with pytest.raises(cm.ChunkMultipassError, match="never admitted over inputs other than"):
        resolve(partial, run)
    with pytest.raises(cm.ChunkMultipassError, match="never admitted over inputs other than"):
        finalize(partial, run, database)
    assert not (partial["multipass_root"] / "final").exists()


def test_a12_a_forged_bound_digest_inside_the_intermediate_receipt_is_refused(
    tmp_path: Path,
) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    path = intermediate_directory(partial, 0) / cm.INTERMEDIATE_RECEIPT_FILENAME

    def forge(document: dict[str, Any]) -> None:
        document["input_receipt_sha256"][0] = "f" * 64

    edit_json(path, forge)
    # The receipt is excluded from its own manifest, so the artifact still verifies ...
    receipt = cm.IntermediateReceipt.from_record(
        read_receipt_document(path, contract=cm.INTERMEDIATE_RECEIPT_CONTRACT)
    )
    verify_artifact_manifest(
        path.parent, receipt.manifest, exclude=(cm.INTERMEDIATE_RECEIPT_FILENAME,)
    )
    # ... and only the comparison against the chunk on disk catches it.
    with pytest.raises(cm.ChunkMultipassError, match="never admitted over inputs other than"):
        resolve(partial, run)


def test_a13_a_changed_repository_identity_is_refused(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    path = intermediate_directory(partial, 1) / cm.INTERMEDIATE_RECEIPT_FILENAME
    edit_json(path, lambda document: document.__setitem__("repository_head_sha", "f" * 40))
    with pytest.raises(cm.ChunkMultipassError, match="was merged under repository"):
        resolve(partial, run)
    # Every intermediate moved consistently: the measured checkout still disagrees.
    for index in range(len(partial["intermediates"])):
        edit_json(
            intermediate_directory(partial, index) / cm.INTERMEDIATE_RECEIPT_FILENAME,
            lambda document: document.__setitem__("repository_head_sha", "f" * 40),
        )
    with pytest.raises(cm.ChunkMultipassError, match="this merge is running from"):
        finalize(partial, run, database)


def test_a14_a_changed_execution_contract_is_refused(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    path = intermediate_directory(partial, 1) / cm.INTERMEDIATE_RECEIPT_FILENAME
    edit_json(
        path,
        lambda document: document["execution_contract"].__setitem__(
            "parser_version", "9.9.9-forged"
        ),
    )
    with pytest.raises(cm.ChunkMultipassError, match="different execution contract"):
        resolve(partial, run)


def test_a15_a16_a17_manifest_extra_missing_and_symlink_are_loud_refusals(tmp_path: Path) -> None:
    """A completed intermediate whose artifact set moved is REFUSED, never 'never ran'."""
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    group = partial["schedule"].groups[0].group_id
    directory = intermediate_directory(partial, 0)
    # A15: an extra object.
    (directory / "unexpected.txt").write_text("an object no receipt names", encoding="utf-8")
    with pytest.raises(cm.ChunkMultipassError, match="STOPS rather than reinterpreting"):
        cm.completed_intermediate_receipt(partial["intermediates_root"], group)
    with pytest.raises(cm.ChunkMultipassError, match="STOPS rather than reinterpreting"):
        cm.next_intermediate_attempt_directory(partial["intermediates_root"], group)
    (directory / "unexpected.txt").rename(tmp_path / "moved-away.txt")
    assert cm.completed_intermediate_receipt(partial["intermediates_root"], group) is not None
    # A16: a missing object -- moved aside rather than deleted, which is enough to be absent.
    (directory / cm.MERGE_SCHEDULE_FILENAME).rename(tmp_path / "schedule-aside.json")
    with pytest.raises(cm.ChunkMultipassError, match="not present"):
        cm.completed_intermediate_receipt(partial["intermediates_root"], group)
    (tmp_path / "schedule-aside.json").rename(directory / cm.MERGE_SCHEDULE_FILENAME)
    assert cm.completed_intermediate_receipt(partial["intermediates_root"], group) is not None
    # A17: a symbolic link.
    (directory / "link.sqlite3").symlink_to(directory / WORKING_CATALOG_FILENAME)
    with pytest.raises(cm.ChunkMultipassError, match="symbolic link"):
        cm.completed_intermediate_receipt(partial["intermediates_root"], group)
    with pytest.raises(cm.ChunkMultipassError, match="symbolic link"):
        resolve(partial, run)


def test_a15_a_changed_intermediate_is_refused_at_and_after_consumption(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    victim = intermediate_directory(partial, 1) / cm.INTERMEDIATE_WITNESS_FILENAME
    victim.write_bytes(victim.read_bytes() + b"\x00")
    with pytest.raises(cm.ChunkMultipassError, match="does not verify"):
        finalize(partial, run, database)
    assert not (partial["multipass_root"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).exists()
    # Altered DURING the finalization: caught by the post-merge re-verification.
    database2, _tree2, run2 = ten_chunk_run(tmp_path / "second")
    partial2 = c13.merge_in_process(run2, database2, finalize=False)
    target = intermediate_directory(partial2, 1) / cm.INTERMEDIATE_WITNESS_FILENAME
    original = cm._merge_sidecar

    def corrupt_then_merge(**kwargs: Any) -> Any:
        target.write_bytes(target.read_bytes() + b"\x00")
        return original(**kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "_merge_sidecar", corrupt_then_merge)
        with pytest.raises(ChunkEvidenceError, match="does not match the manifest"):
            finalize(partial2, run2, database2)
    assert not (partial2["multipass_root"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).exists()


def test_a18_two_valid_receipts_for_one_group_are_ambiguous_authority(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    original = intermediate_directory(partial, 0)
    twin = original.parent / "attempt-777"
    twin.mkdir()
    for path in original.iterdir():
        (twin / path.name).write_bytes(path.read_bytes())
    with pytest.raises(cm.ChunkMultipassError, match="valid terminal receipts"):
        cm.completed_intermediate_receipt(
            partial["intermediates_root"], partial["schedule"].groups[0].group_id
        )
    with pytest.raises(cm.ChunkMultipassError, match="valid terminal receipts"):
        resolve(partial, run)


def test_a_foreign_intermediate_directory_is_refused(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    (partial["intermediates_root"] / "group-0099").mkdir()
    with pytest.raises(cm.ChunkMultipassError, match="does not name"):
        resolve(partial, run)


def test_a_schedule_or_plan_that_moved_is_refused_by_the_receipts(tmp_path: Path) -> None:
    database, tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    other_database, other_tree = c1.build_world(tmp_path / "other", members=9, filings=2, shards=1)
    other_plan = c13.multipass_plan(other_tree, other_database, chunk_members=1)
    other_schedule = cm.derive_merge_schedule(other_plan)
    with pytest.raises(cm.ChunkMultipassError, match="built under plan digest"):
        cm.resolve_intermediate_inputs(
            other_plan, other_schedule, intermediates_root=partial["intermediates_root"]
        )
    assert tree is not None


# ==========================================================================
# Crash / restart -- D151-C13 §27
# ==========================================================================
def test_r01_an_interrupted_level_one_merge_leaves_no_receipt_and_retries_beside(
    tmp_path: Path,
) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "multipass"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    intermediates_root = root / "intermediates"
    group = schedule.groups[0].group_id
    dead, attempt = cm.next_intermediate_attempt_directory(intermediates_root, group)

    def _boom(*_args: Any, **_kwargs: Any) -> Any:
        message = "synthetic interruption before the receipt"
        raise RuntimeError(message)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "build_artifact_manifest", _boom)
        with pytest.raises(RuntimeError, match="synthetic interruption"):
            cm.merge_group_body(
                c13.group_request(
                    run,
                    schedule_path=schedule_path,
                    group_id=group,
                    attempt=attempt,
                    attempt_directory=dead,
                    database=database,
                )
            )
    assert dead.is_dir() and not (dead / cm.INTERMEDIATE_RECEIPT_FILENAME).exists()
    assert cm.completed_intermediate_receipt(intermediates_root, group) is None
    retry, retry_attempt = cm.next_intermediate_attempt_directory(intermediates_root, group)
    assert retry_attempt == attempt + 1 and retry != dead
    receipt = cm.merge_group_body(
        c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id=group,
            attempt=retry_attempt,
            attempt_directory=retry,
            database=database,
        )
    )
    assert receipt.status == "complete" and receipt.attempt == retry_attempt
    # The dead attempt is exactly where it was: nothing was deleted, renamed or cleaned.
    assert dead.is_dir() and not (dead / cm.INTERMEDIATE_RECEIPT_FILENAME).exists()
    found = cm.completed_intermediate_receipt(intermediates_root, group)
    assert found is not None and found[1] == retry
    with pytest.raises(cm.ChunkMultipassError, match="IMMUTABLE and is reused"):
        cm.next_intermediate_attempt_directory(intermediates_root, group)
    with pytest.raises(cm.ChunkMultipassError, match="already exists"):
        cm.merge_group_body(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id=group,
                attempt=retry_attempt,
                attempt_directory=retry,
                database=database,
            )
        )


def test_r02_a_valid_intermediate_is_reused_and_a_restart_continues_the_recorded_run(
    tmp_path: Path,
) -> None:
    """The orchestrator skips every group that already carries a valid receipt."""
    database, _tree, run = ten_chunk_run(tmp_path)
    multipass_root = run["base"] / "orchestrated"
    events: list[str] = []
    # First: every level-1 merge in a child, then the finalization is interrupted.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(cm, "run_final_merge", _boom_final)
        with pytest.raises(RuntimeError, match="synthetic final interruption"):
            cm.run_multipass_f0(
                plan=run["plan"],
                internal_root=run["chunk_root"],
                operational_catalog=database,
                multipass_root=multipass_root,
                run_id="restart",
                observe=events.append,
            )
    groups = cm.derive_merge_schedule(run["plan"]).groups
    assert events.count("MERGE_PROCESS_START") == len(groups)
    assert not (multipass_root / "final").exists()
    # Then: the restart reuses every intermediate and spawns exactly one process, the final.
    events.clear()
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=multipass_root,
        run_id="restart",
        observe=events.append,
    )
    assert events == ["MERGE_PROCESS_START", "MERGE_PROCESS_EXIT"]
    assert result.merge_pids == ()
    assert result.receipt["status"] == "complete"
    assert len(result.intermediates) == len(groups)
    for group in groups:
        assert len(list((multipass_root / "intermediates" / group.group_id).glob("attempt-*"))) == 1
    # A restart under a different plan refuses against the recorded one.
    other_database, other_tree = c1.build_world(tmp_path / "other", members=9, filings=2, shards=1)
    with pytest.raises(cm.ChunkMultipassError, match="not the one this consolidation was given"):
        cm.run_multipass_f0(
            plan=c13.multipass_plan(other_tree, other_database, chunk_members=1),
            internal_root=run["chunk_root"],
            operational_catalog=other_database,
            multipass_root=multipass_root,
            run_id="restart",
        )


def _boom_final(*_args: Any, **_kwargs: Any) -> Any:
    message = "synthetic final interruption"
    raise RuntimeError(message)


def test_r03_a_completed_intermediate_whose_bytes_moved_is_never_rebuilt_beside(
    tmp_path: Path,
) -> None:
    """The C8-N1 ambiguity is not inherited: an invalid completed receipt is a STOP."""
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    directory = intermediate_directory(partial, 0)
    group = partial["schedule"].groups[0].group_id
    victim = directory / cm.INTERMEDIATE_WITNESS_FILENAME
    victim.write_bytes(victim.read_bytes() + b"\x00")
    with pytest.raises(
        cm.ChunkMultipassError, match="changed artifact, not an attempt that never ran"
    ):
        cm.completed_intermediate_receipt(partial["intermediates_root"], group)
    with pytest.raises(cm.ChunkMultipassError, match="changed artifact"):
        cm.next_intermediate_attempt_directory(partial["intermediates_root"], group)
    with pytest.raises(cm.ChunkMultipassError, match="changed artifact"):
        cm.run_multipass_f0(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            multipass_root=partial["multipass_root"],
            run_id="stop",
        )
    assert len(list((partial["intermediates_root"] / group).glob("attempt-*"))) == 1
    # By contrast, the accepted chunk discovery still swallows an invalid chunk receipt (C8-N1);
    # the intermediate layer deliberately does not.
    chunk_victim = chunk_directory(run, 0) / "chunk_witness.sqlite3"
    chunk_victim.write_bytes(chunk_victim.read_bytes() + b"\x00")
    assert ce.completed_chunk_receipt(run["chunk_root"], run["receipts"][0].chunk_id) is None


# ==========================================================================
# The process contract -- D151-C13 §26
# ==========================================================================
def test_x01_every_merge_runs_in_its_own_process_and_ends_before_the_next(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    eq.monolithic_f0(database, _tree, tmp_path / "mono")
    reference = eq.measure(tmp_path / "mono")
    events: list[str] = []
    result = cm.run_multipass_f0(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        multipass_root=run["base"] / "orchestrated",
        run_id="processes",
        observe=events.append,
    )
    groups = cm.derive_merge_schedule(run["plan"]).groups
    assert len(result.merge_pids) == len(set(result.merge_pids)) == len(groups)
    assert os.getpid() not in result.merge_pids
    for pid in result.merge_pids:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    assert events == ["MERGE_PROCESS_START", "MERGE_PROCESS_EXIT"] * (len(groups) + 1)
    ledger = RunProgressLedger(result.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        checkpoint = read_phase_checkpoint(ledger, PHASE_F0)
        assert checkpoint is not None
        assert checkpoint.pid != os.getpid() and checkpoint.pid not in result.merge_pids
        with pytest.raises(ProcessLookupError):
            os.kill(checkpoint.pid, 0)
    finally:
        ledger.close()
    for receipt in result.intermediates:
        assert receipt.pid != os.getpid()
    eq.assert_equivalent(reference, eq.measure(result.world_directory))
    assert result.receipt["consolidation_contract"] == cm.MULTIPASS_CONSOLIDATION_CONTRACT
    assert result.storage_plan.reclaimable_bytes == 0 and result.storage_plan.inputs_retained


def test_x02_a_live_predecessor_refuses_the_successor(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "multipass"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", "group-0000"
    )
    with pytest.raises(ce.ChunkExecutionError, match="must END before"):
        cm.run_group_merge(
            c13.group_request(
                run,
                schedule_path=schedule_path,
                group_id="group-0000",
                attempt=attempt,
                attempt_directory=directory,
                database=database,
            ),
            predecessor_pid=os.getpid(),
        )
    assert not directory.exists()
    with pytest.raises(ce.ChunkExecutionError, match="must END before"):
        cm.run_final_merge(
            c13.final_request(
                run,
                schedule_path=schedule_path,
                intermediates_root=root / "intermediates",
                world_directory=root / "final",
                database=database,
            ),
            predecessor_pid=os.getpid(),
        )
    assert not (root / "final").exists()


def test_x03_the_coordinator_has_no_in_process_fallback() -> None:
    source = Path(cm.__file__).read_text(encoding="utf-8")
    assert "subprocess.run(" in source
    assert (
        "merge_group_body("
        not in source.split("def run_group_merge(")[1].split("def run_final_merge(")[0]
    )
    assert (
        "finalize_multipass_body("
        not in source.split("def run_final_merge(")[1].split("class MultipassResult")[0]
    )
    assert "gc.collect" not in source
    assert "SIGSTOP" not in source and "SIGCONT" not in source
    assert "-m disclosure_drift" not in cm._CHILD_BOOTSTRAP
    assert "_child_main" in cm._CHILD_BOOTSTRAP
    tree = ast.parse(source)
    spawns = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "run"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "subprocess"
    ]
    assert len(spawns) == 1
    argv = spawns[0].args[0]
    assert isinstance(argv, ast.List)
    executable = argv.elts[0]
    assert isinstance(executable, ast.Attribute) and executable.attr == "executable"


def test_x04_a_merge_child_measures_its_own_code_identity(tmp_path: Path) -> None:
    from dataclasses import replace

    database, _tree, run = ten_chunk_run(tmp_path)
    schedule = cm.derive_merge_schedule(run["plan"])
    root = run["base"] / "multipass"
    root.mkdir()
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", "group-0000"
    )
    request = replace(
        c13.group_request(
            run,
            schedule_path=schedule_path,
            group_id="group-0000",
            attempt=attempt,
            attempt_directory=directory,
            database=database,
        ),
        repository_head_sha="a" * 40,
        repository_tree_sha="b" * 40,
    )
    with pytest.raises(cm.ChunkMultipassError, match="NOT complete") as refusal:
        cm.run_group_merge(request)
    assert "asked to execute under repository" in str(refusal.value)
    assert not directory.exists()
    # In-process, the same refusal, before anything is created.
    with pytest.raises(cm.ChunkMultipassError, match="MEASURED by the merge process"):
        cm.merge_group_body(request)
    assert not directory.exists()


def test_x05_a_dirty_checkout_refuses_every_merge(tmp_path: Path) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    partial = c13.merge_in_process(run, database, finalize=False)
    assert c1.PINNED_ROOT is not None
    (c1.PINNED_ROOT / "untracked.py").write_text("# a file no commit describes\n", encoding="utf-8")
    with pytest.raises(
        repository_identity.RepositoryIdentityError, match="clean tracked working tree"
    ):
        finalize(partial, run, database)
    assert not (partial["multipass_root"] / "final").exists()


# ==========================================================================
# A19: a calibration chunk can never be a multipass input
# ==========================================================================
def test_a19_a_calibration_chunk_is_refused_by_plan_digest(tmp_path: Path) -> None:
    database, tree = c1.build_world(tmp_path, members=9, filings=2, shards=1)
    calibration = c10.calibration_plan(tree, database, chunk_members=1)
    multipass = c13.multipass_plan(tree, database, chunk_members=1)
    assert (
        calibration.chunks == multipass.chunks and calibration.plan_digest != multipass.plan_digest
    )
    run = c13.execute_in_process(calibration, tmp_path / "calibration", database, tree)
    assert run["receipts"][0].plan_digest == calibration.plan_digest
    with pytest.raises(cc.ChunkConsolidationError, match="produced under plan digest"):
        cc.resolve_chunk_inputs(multipass, internal_root=run["chunk_root"])
    schedule = cm.derive_merge_schedule(multipass)
    root = tmp_path / "multipass"
    root.mkdir()
    plan_path = root / "plan.json"
    write_once_json(plan_path, dict(multipass.as_record()))
    schedule_path = root / cm.MERGE_SCHEDULE_FILENAME
    write_once_json(schedule_path, dict(schedule.as_record()))
    directory, attempt = cm.next_intermediate_attempt_directory(
        root / "intermediates", "group-0000"
    )
    laundering = c13.group_request(
        {**run, "plan_path": plan_path},
        schedule_path=schedule_path,
        group_id="group-0000",
        attempt=attempt,
        attempt_directory=directory,
        database=database,
    )
    with pytest.raises(cc.ChunkConsolidationError, match="produced under plan digest"):
        cm.merge_group_body(laundering)
    assert not directory.exists()
    # And the calibration plan itself, handed to a merge, is refused by contract before any read.
    calibration_path = root / "calibration.json"
    write_once_json(calibration_path, dict(calibration.as_record()))
    with pytest.raises(cm.ChunkMultipassError, match="never consolidated by the multipass"):
        cm.merge_group_body(
            c13.group_request(
                {**run, "plan_path": calibration_path},
                schedule_path=schedule_path,
                group_id="group-0000",
                attempt=attempt,
                attempt_directory=directory,
                database=database,
            )
        )
    assert not directory.exists()


# ==========================================================================
# Closure: authorities, environment, command line, deletion, transport
# ==========================================================================
def test_z01_every_authority_and_every_sizing_constant_is_none() -> None:
    # The COMMITTED literal, read from the source: this module's fixture opens the live attribute
    # for synthetic execution. The behavioural proof that the committed literal governs every
    # world-creating entry is test_d151_c15_corrections (D151-C15 R2, closing C14-MINOR-3).
    assert committed_literal(cm, "REAL_MULTIPASS_F0_AUTHORITY") is None
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY is None
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    assert cp.PRODUCTION_CHUNK_MEMBERS is None
    assert cs.INTERNAL_RESERVE_BYTES is None
    assert cs.CHUNK_PEAK_REQUIREMENT_BYTES is None
    assert ct.MULTIPASS_LEVEL_ONE_PEAK_RATIO is None
    assert ct.MULTIPASS_LEVEL_TWO_PEAK_RATIO is None
    assert ct.MULTIPASS_TRANSIENT_BYTES is None
    assert ct.PRODUCTION_SPILL_POLICY is None
    assert ct.QUALIFIED_EXTERNAL_TIER is None
    assert "NOT AUTHORIZED" in refusal_in_a_fresh_interpreter()
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()
    with pytest.raises(ce.ChunkExecutionError, match="NOT AUTHORIZED"):
        ce.require_real_chunk_execution_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_chunk_transfer_authority()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.require_real_internal_reclaim_authority()


def test_z02_no_environment_configuration_or_command_line_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from disclosure_drift import cli

    cli_source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in ("chunk_multipass", "chunk_tiering", "multipass", "tiering", "chunked"):
        assert name not in cli_source, name
    for module in NEW_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        attributes = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
        assert "environ" not in names and "environ" not in attributes, module.__name__
        assert "getenv" not in names and "getenv" not in attributes, module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "load_config" not in names, module.__name__
        assert "argparse" not in source, module.__name__
        assert "apply_migrations" not in source, module.__name__
        assert "build_calibration_chunk_plan" not in source, module.__name__
    package_root = Path(cli.__file__).parent
    chunk_family = {
        "chunk_plan",
        "chunk_evidence",
        "chunk_execution",
        "chunk_storage",
        "chunk_consolidation",
        "chunk_multipass",
        "chunk_tiering",
    }
    importers = [
        path.name
        for path in sorted(package_root.rglob("*.py"))
        if path.stem not in chunk_family
        and (
            "chunk_multipass" in path.read_text(encoding="utf-8")
            or "chunk_tiering" in path.read_text(encoding="utf-8")
        )
    ]
    assert importers == []
    monkeypatch.setenv("DISCLOSURE_DRIFT_MULTIPASS_AUTHORITY", "granted")
    monkeypatch.setenv("DISCLOSURE_DRIFT_INTERNAL_RESERVE_BYTES", "0")
    # A FRESH interpreter inheriting those variables still refuses on the committed literal.
    assert "NOT AUTHORIZED" in refusal_in_a_fresh_interpreter()
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()


def test_z03_no_new_module_can_delete_copy_or_reach_a_transport() -> None:
    for module in NEW_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for capability in (
            "shutil.rmtree",
            "os.remove(",
            "os.rmdir(",
            ".unlink(",
            "shutil.move",
            "shutil.copy",
            "rmtree",
            "unlink",
        ):
            assert capability not in source, (module.__name__, capability)
        for prefix in PROHIBITED_IMPORT_PREFIXES:
            assert f"import {prefix}" not in source
            assert f"from {prefix}" not in source
        assert "from disclosure_drift.m3.e0" not in source
        assert "M3_3_E0_EXECUTION_AUTHORITY" not in source
        assert "external_working_root" not in source
        tree = ast.parse(source)
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)} | {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        for needle in ("SecClient", "HttpxTransport", "socket", "urlopen", "create_connection"):
            assert needle not in names, (module.__name__, needle)
    assert "shutil" not in Path(ct.__file__).read_text(encoding="utf-8")


def test_z04_the_new_modules_are_importable_without_a_world(tmp_path: Path) -> None:
    probe = tmp_path / "probe"
    probe.mkdir()
    program = (
        "import sys, json;"
        "from pathlib import Path;"
        "root = Path(sys.argv[1]);"
        "before = sorted(p.name for p in root.iterdir());"
        "import disclosure_drift.m3;"
        "loaded = set(sys.modules);"
        "import disclosure_drift.m3.chunk_tiering, disclosure_drift.m3.chunk_multipass;"
        "from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES as P;"
        "after = sorted(p.name for p in root.iterdir());"
        "added = set(sys.modules) - loaded;"
        "bad = sorted(n for n in added if any(n == p or n.startswith(p + '.') for p in P));"
        "print(json.dumps({'before': before, 'after': after, 'bad': bad}))"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program, str(probe)], capture_output=True, text=True, check=True
    )
    observed = json.loads(completed.stdout.strip().splitlines()[-1])
    assert observed["before"] == observed["after"] == []
    assert observed["bad"] == []


def test_z05_no_c13_test_reloads_a_production_module() -> None:
    for path in sorted(Path(__file__).parent.glob("test_d151_c13_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            assert not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "reload"
            ), path.name


def test_z06_the_final_world_is_never_read_as_an_intermediate_and_the_reverse(
    tmp_path: Path,
) -> None:
    database, _tree, run = ten_chunk_run(tmp_path)
    result = c13.merge_in_process(run, database)
    with pytest.raises(ChunkEvidenceError, match="no receipt exists"):
        read_receipt_document(
            result["world_directory"] / cm.INTERMEDIATE_RECEIPT_FILENAME,
            contract=cm.INTERMEDIATE_RECEIPT_CONTRACT,
        )
    with pytest.raises(ChunkEvidenceError, match="carries contract"):
        read_receipt_document(
            result["world_directory"] / FINAL_WORLD_RECEIPT_FILENAME,
            contract=cm.INTERMEDIATE_RECEIPT_CONTRACT,
        )
    assert cm.completed_intermediate_receipt(result["multipass_root"], "final") is None
    with connect(result["world_directory"] / WORKING_CATALOG_FILENAME, writer=False) as world:
        assert inspect.isfunction(cm.finalize_multipass_body)
        row = world.execute("SELECT COUNT(*) AS n FROM census_parser_runs").fetchone()
    assert int(row["n"]) == 1
    assert FINAL_WORLD_RECEIPT_CONTRACT == "m3.3-chunked-f0-final-receipt/2"
