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
environment-derived configuration capability through the finite route taxonomy the audit
enumerates (D151-C21 R2) beyond the exact owner-approved ``SQLITE_TMPDIR`` reads, no command-line
reach, exact per-module program and argv allowlists with no removal, shell, network or destructive
write capability outside them (D151-C21 R3), no transport, and importable without a world.
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
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import (
    repository_identity,  # noqa: E402
)
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
        # D151-C17 R6: the child measures the temp/world volume binding for ITSELF, so the
        # accepted provider seam is substituted inside the child too -- the same synthetic
        # identity the parent uses, so no test depends on the host's real volume layout. The
        # comparison the child performs is the production one, unpatched.
        "from disclosure_drift.m3 import external_working_root as ewr;"
        "ewr.macos_volume_identity = lambda path: ewr.VolumeIdentity("
        f"volume_uuid={c13.SYNTHETIC_MERGE_VOLUME!r}, mount_point=Path('/'), "
        "filesystem_type='apfs', device_identifier='disk-synthetic');"
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
    c13.open_synthetic_multipass(patcher, temp_root=tmp_path / "sqlite-temp")
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
    assert ct.MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES is None
    assert ct.MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES is None
    assert not hasattr(ct, "MULTIPASS_TRANSIENT_BYTES"), (
        "the generic transient term is superseded by the two level-specific ones (D151-C17 R5); "
        "leaving it in place is what would let level 2 be charged at level 1's allowance"
    )
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


# --------------------------------------------------------------------------------------------
# Environment-derived configuration closure by BINDING analysis -- D151-C19 R3, widened to the
# owner-defined finite route taxonomy by D151-C21 R2 (closing D151-C20 MINOR-2)
# --------------------------------------------------------------------------------------------
#: The names on ``os`` (and ``posix``/``nt``) through which a process environment is read or
#: written.
ENVIRONMENT_NAMES: frozenset[str] = frozenset(
    {"environ", "environb", "getenv", "getenvb", "putenv", "unsetenv"}
)
#: ``os.path`` (``posixpath``/``ntpath``) names that read the environment to expand a path.
PATH_EXPANSION_NAMES: frozenset[str] = frozenset({"expandvars", "expanduser"})
#: ``pathlib`` class names whose ``home``/``expanduser`` read the environment.
PATHLIB_CLASSES: frozenset[str] = frozenset(
    {"Path", "PurePath", "PosixPath", "WindowsPath", "PurePosixPath", "PureWindowsPath"}
)
#: ``pathlib`` method names that read the environment (``HOME``, ``USERPROFILE``).
PATHLIB_ENVIRONMENT_NAMES: frozenset[str] = frozenset({"home", "expanduser"})
#: ``tempfile`` names whose result is derived from ``TMPDIR``/``TEMP``/``TMP``.
TEMPFILE_ENVIRONMENT_NAMES: frozenset[str] = frozenset(
    {
        "gettempdir",
        "gettempdirb",
        "gettempprefix",
        "gettempprefixb",
        "mkdtemp",
        "mkstemp",
        "mktemp",
        "NamedTemporaryFile",
        "SpooledTemporaryFile",
        "TemporaryDirectory",
        "TemporaryFile",
    }
)
#: ``getpass`` names that read ``LOGNAME``/``USER``/``LNAME``/``USERNAME``.
GETPASS_ENVIRONMENT_NAMES: frozenset[str] = frozenset({"getuser", "getpass"})
#: ``shutil`` names that read ``PATH`` or ``COLUMNS``/``LINES``.
SHUTIL_ENVIRONMENT_NAMES: frozenset[str] = frozenset({"which", "get_terminal_size"})
#: Programs whose output IS the process environment, or configuration derived from it.
ENVIRONMENT_PROGRAMS: frozenset[str] = frozenset({"printenv", "env", "launchctl", "defaults"})
#: The subprocess module entries that start a process.
_SUBPROCESS_ENTRIES: frozenset[str] = frozenset(
    {"run", "Popen", "call", "check_call", "check_output", "getoutput", "getstatusoutput"}
)
#: Every module whose attributes are an environment route, with the names that are one.
_ENVIRONMENT_MODULE_NAMES: dict[str, frozenset[str]] = {
    "os": ENVIRONMENT_NAMES,
    "posix": ENVIRONMENT_NAMES,
    "nt": ENVIRONMENT_NAMES,
    "os.path": PATH_EXPANSION_NAMES,
    "posixpath": PATH_EXPANSION_NAMES,
    "ntpath": PATH_EXPANSION_NAMES,
    "tempfile": TEMPFILE_ENVIRONMENT_NAMES,
    "getpass": GETPASS_ENVIRONMENT_NAMES,
    "shutil": SHUTIL_ENVIRONMENT_NAMES,
}
#: The module roots whose bindings the audit follows.
_TRACKED_MODULE_ROOTS: frozenset[str] = frozenset(
    {
        "os",
        "posix",
        "nt",
        "posixpath",
        "ntpath",
        "tempfile",
        "getpass",
        "shutil",
        "pathlib",
        "ctypes",
        "importlib",
        "subprocess",
    }
)
#: The exact dotted routes the attribute pass recognizes.
_ENVIRONMENT_ROUTES: frozenset[str] = frozenset(
    {f"{module}.{name}" for module, names in _ENVIRONMENT_MODULE_NAMES.items() for name in names}
    | {f"pathlib.Path.{name}" for name in PATHLIB_ENVIRONMENT_NAMES}
)

#: The finite route taxonomy this audit enumerates -- D151-C21 R2. The closure CLAIMS exactly
#: this: no audited module reaches the process environment through any of these routes except
#: the exact owner-approved ``SQLITE_TMPDIR`` reads. It claims nothing about routes outside
#: this list; a route added to Python, or found missing here, is added by review.
ENVIRONMENT_ROUTE_TAXONOMY: tuple[str, ...] = (
    "os.environ / os.environb / os.getenv / os.getenvb / os.putenv / os.unsetenv",
    "the same names on posix / nt, and any of them imported or aliased",
    "os.path.expandvars / os.path.expanduser (also posixpath / ntpath)",
    "pathlib.Path.home / pathlib.Path.expanduser (every pathlib class, any receiver)",
    "tempfile.gettempdir / gettempdirb / gettempprefix / mk*temp / *TemporaryFile / "
    "TemporaryDirectory",
    "getpass.getuser / getpass.getpass",
    "shutil.which / shutil.get_terminal_size",
    "ctypes, by any import form (libc getenv is reachable through it)",
    "sys.modules subscripts, getattr / vars on a tracked module, importlib.import_module, "
    "__import__",
    "subprocess env= keyword, or a printenv / env / launchctl / defaults program",
)


def _attribute_chain(node: ast.AST) -> list[str] | None:
    """``a.b.c`` as ``["a", "b", "c"]`` when it is rooted in a plain name, else ``None``."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(node.id)
    return parts[::-1]


def _subprocess_argv(node: ast.Call) -> ast.expr | None:
    if node.args:
        return node.args[0]
    return next((k.value for k in node.keywords if k.arg == "args"), None)


def environment_accesses(source: str) -> list[tuple[int, str]]:  # noqa: PLR0912, PLR0915
    """Every environment-derived route ``source`` reaches, found by what names are BOUND to.

    Resolves what every tracked module is bound to (``import os``, ``import os as x``,
    ``import os.path``, ``from os import path as p``, ``from pathlib import Path as P``, ...),
    what its environment names are bound to (``from os import environ as e``,
    ``from tempfile import gettempdir``, ...), and then reports every attribute chain through a
    tracked alias that lands on a route in :data:`ENVIRONMENT_ROUTE_TAXONOMY`, every use of a
    bound route name, every ``ctypes`` import, every ``sys.modules`` subscript, every reflective
    lookup on a tracked alias, every dynamic import, every ``.home()`` / ``.expanduser()`` call
    on any receiver, and every subprocess that is handed an ``env=`` or runs an
    environment-printing program. A text scan cannot see ``_o.environ``, ``_e[...]`` or
    ``p.expandvars``; this can.
    """
    tree = ast.parse(source)
    module_aliases: dict[str, str] = {}
    name_aliases: dict[str, str] = {}
    subprocess_aliases: set[str] = set()
    subprocess_functions: set[str] = set()
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root not in _TRACKED_MODULE_ROOTS:
                    continue
                bound = alias.asname or root
                module_aliases[bound] = alias.name if alias.asname else root
                if root in {"posix", "nt", "ctypes"}:
                    found.append((node.lineno, f"import {alias.name}"))
                if root == "subprocess":
                    subprocess_aliases.add(bound)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root = module.split(".")[0]
            if root == "ctypes":
                found.append((node.lineno, f"from {module} import ..."))
                continue
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name == "*":
                    if module in _ENVIRONMENT_MODULE_NAMES or root in {"pathlib", "importlib"}:
                        found.append((node.lineno, f"from {module} import *"))
                elif (
                    module in _ENVIRONMENT_MODULE_NAMES
                    and alias.name in _ENVIRONMENT_MODULE_NAMES[module]
                ):
                    name_aliases[bound] = f"{module}.{alias.name}"
                    found.append((node.lineno, f"from {module} import {alias.name}"))
                elif module == "os" and alias.name == "path":
                    module_aliases[bound] = "os.path"
                elif module == "pathlib" and alias.name in PATHLIB_CLASSES:
                    module_aliases[bound] = "pathlib.Path"
                elif root == "importlib" and alias.name in {"import_module", "__import__"}:
                    found.append((node.lineno, f"from {module} import {alias.name}"))
                elif module == "subprocess" and alias.name in _SUBPROCESS_ENTRIES:
                    subprocess_functions.add(bound)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            chain = _attribute_chain(node)
            if chain is not None and chain[0] in module_aliases:
                dotted = [module_aliases[chain[0]], *chain[1:]]
                for stop in range(2, len(dotted) + 1):
                    candidate = ".".join(dotted[:stop])
                    if candidate in _ENVIRONMENT_ROUTES:
                        found.append((node.lineno, candidate))
                        break
        elif (
            isinstance(node, ast.Name)
            and node.id in name_aliases
            and isinstance(node.ctx, ast.Load)
        ):
            found.append((node.lineno, f"{node.id} (bound to {name_aliases[node.id]})"))
        elif (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Attribute)
            and node.value.attr == "modules"
        ):
            found.append((node.lineno, "sys.modules[...]"))
        elif isinstance(node, ast.Call):
            func = node.func
            callee = func.id if isinstance(func, ast.Name) else None
            if isinstance(func, ast.Attribute) and func.attr == "import_module":
                found.append((node.lineno, "import_module(...)"))
            if callee in {"__import__", "import_module"}:
                found.append((node.lineno, f"{callee}(...)"))
            if (
                callee in {"getattr", "vars"}
                and node.args
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in module_aliases
            ):
                found.append((node.lineno, f"{callee}({node.args[0].id}, ...)"))
            if (
                isinstance(func, ast.Attribute)
                and func.attr in PATHLIB_ENVIRONMENT_NAMES
                and not node.args
                and not node.keywords
            ):
                found.append((node.lineno, f".{func.attr}()"))
            is_subprocess = (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id in subprocess_aliases
                and func.attr in _SUBPROCESS_ENTRIES
            ) or (callee is not None and callee in subprocess_functions)
            if is_subprocess:
                if any(keyword.arg == "env" for keyword in node.keywords):
                    found.append((node.lineno, "subprocess env="))
                argv = _subprocess_argv(node)
                if isinstance(argv, ast.List) and argv.elts:
                    program = argv.elts[0]
                    if isinstance(program, ast.Constant) and isinstance(program.value, str):
                        basename = program.value.rsplit("/", 1)[-1]
                        if basename in ENVIRONMENT_PROGRAMS:
                            found.append((node.lineno, f"subprocess {basename}"))
    return sorted(set(found))


def permitted_sqlite_tmpdir_reads(source: str, *, function: str) -> set[int]:
    """Lines inside ``function`` that are EXACTLY ``os.environ.get(SQLITE_TMPDIR_ENV)``.

    One positional ``Name`` argument, no default, no keywords, through the plain ``os`` binding:
    the accepted D138-R3 shape and nothing looser. A default value, a second argument or an
    aliased ``os`` is not this read.
    """
    lines: set[int] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and node.name == function:
            for call in ast.walk(node):
                if (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "get"
                    and isinstance(call.func.value, ast.Attribute)
                    and call.func.value.attr == "environ"
                    and isinstance(call.func.value.value, ast.Name)
                    and call.func.value.value.id == "os"
                    and len(call.args) == 1
                    and isinstance(call.args[0], ast.Name)
                    and call.args[0].id == "SQLITE_TMPDIR_ENV"
                    and not call.keywords
                ):
                    lines.add(call.lineno)
    return lines


#: The exact owner-approved direct reads -- D151-C21 R2. Nothing else on the audited path.
PERMITTED_SQLITE_TMPDIR_READS: dict[str, str] = {
    "chunk_tiering": "require_sqlite_temp_binding",
    "external_working_root": "require_external_sqlite_tmpdir",
}


def environment_closure_violations(module_name: str, source: str) -> list[tuple[int, str]]:
    """Every environment-derived route beyond the accepted reads -- D151-C19 R3, D151-C21 R2.

    ``chunk_multipass`` may read nothing. ``chunk_tiering`` may read exactly one thing: the
    governed ``SQLITE_TMPDIR`` value, inside ``require_sqlite_temp_binding``, in the accepted
    shape. ``external_working_root`` -- reached, not new -- may read the same one thing inside
    the accepted D137-R8 guard. Everything else on the reached chain reads nothing, through any
    route :data:`ENVIRONMENT_ROUTE_TAXONOMY` names. That finite property is the claim.
    """
    accesses = environment_accesses(source)
    stem = module_name.rsplit(".", 1)[-1]
    if stem in PERMITTED_SQLITE_TMPDIR_READS:
        permitted = permitted_sqlite_tmpdir_reads(
            source, function=PERMITTED_SQLITE_TMPDIR_READS[stem]
        )
        return [item for item in accesses if not (item[1] == "os.environ" and item[0] in permitted)]
    return accesses


# --------------------------------------------------------------------------------------------
# Transitive capability closure of the storage-binding chain -- D151-C19 R5 (C18 INFO-2),
# made exact per module by D151-C21 R3 (closing D151-C20 MINOR-3)
# --------------------------------------------------------------------------------------------
#: Where the package lives, for resolving ``disclosure_drift.*`` imports to files.
_SRC_ROOT = Path(cm.__file__).parents[2]

#: Modules that open a network or transport. An import of any of them, by either statement
#: form, is a capability the storage-binding chain must not reach.
NETWORK_MODULES: frozenset[str] = frozenset(
    {
        "socket",
        "ssl",
        "http",
        "urllib",
        "httpx",
        "requests",
        "ftplib",
        "smtplib",
        "telnetlib",
        "xmlrpc",
        "websocket",
        "websockets",
        "aiohttp",
    }
)
#: Modules that create processes outside ``subprocess``: ``asyncio`` (``create_subprocess_*``),
#: ``multiprocessing``, ``concurrent`` (``ProcessPoolExecutor``) and ``pty``. None is accepted.
PROCESS_MODULES: frozenset[str] = frozenset({"asyncio", "multiprocessing", "concurrent", "pty"})
#: Attribute names that start a process through ``asyncio`` or an event loop.
ASYNC_PROCESS_NAMES: frozenset[str] = frozenset(
    {"create_subprocess_exec", "create_subprocess_shell", "subprocess_exec", "subprocess_shell"}
)
#: ``shutil`` names that copy, move or delete. ``disk_usage`` is the one measurement allowed.
DESTRUCTIVE_SHUTIL: frozenset[str] = frozenset(
    {"rmtree", "copy", "copy2", "copyfile", "copytree", "copymode", "copystat", "move", "chown"}
)
#: ``os`` names that delete, rename, truncate, change ownership or mode, link, run a shell,
#: replace or spawn a process, or signal. Every one is forbidden; ``os.open`` is governed
#: separately by the per-module write allowlist.
DESTRUCTIVE_OS: frozenset[str] = frozenset(
    {
        "remove",
        "unlink",
        "rmdir",
        "removedirs",
        "rename",
        "renames",
        "replace",
        "truncate",
        "chmod",
        "lchmod",
        "fchmod",
        "chown",
        "lchown",
        "fchown",
        "chflags",
        "lchflags",
        "link",
        "symlink",
        "system",
        "popen",
        "posix_spawn",
        "posix_spawnp",
        "execl",
        "execle",
        "execlp",
        "execlpe",
        "execv",
        "execve",
        "execvp",
        "execvpe",
        "spawnl",
        "spawnle",
        "spawnlp",
        "spawnlpe",
        "spawnv",
        "spawnve",
        "spawnvp",
        "spawnvpe",
        "fork",
        "forkpty",
        "kill",
        "killpg",
    }
)
#: Method names that delete, copy, move, write, rename, truncate or change mode on ANY receiver.
#: ``.replace(`` is handled by shape (one positional argument, the ``Path.replace`` form).
_DESTRUCTIVE_METHODS: frozenset[str] = frozenset(
    {
        "rmtree",
        "copyfile",
        "copytree",
        "copy2",
        "move",
        "unlink",
        "rmdir",
        "removedirs",
        "system",
        "popen",
        "write_text",
        "write_bytes",
        "rename",
        "truncate",
        "chmod",
        "lchmod",
    }
)
#: Programs no audited module may launch, whatever their argv -- a fixed absolute path is never
#: sufficient (D151-C21 R3): removal, mutation, shells, interpreters, network clients, process
#: control and volume tools.
FORBIDDEN_PROGRAM_NAMES: frozenset[str] = frozenset(
    {
        "rm",
        "rmdir",
        "unlink",
        "mv",
        "cp",
        "dd",
        "shred",
        "srm",
        "truncate",
        "chmod",
        "chown",
        "chflags",
        "ln",
        "sh",
        "bash",
        "zsh",
        "dash",
        "ksh",
        "csh",
        "tcsh",
        "fish",
        "env",
        "printenv",
        "xargs",
        "osascript",
        "python",
        "python3",
        "perl",
        "ruby",
        "curl",
        "wget",
        "nc",
        "ncat",
        "netcat",
        "ssh",
        "scp",
        "sftp",
        "rsync",
        "ftp",
        "telnet",
        "open",
        "launchctl",
        "kill",
        "killall",
        "pkill",
        "hdiutil",
        "tar",
    }
)
#: ``os.open`` flag names that create, write, truncate or append.
WRITE_OPEN_FLAGS: frozenset[str] = frozenset(
    {"O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND", "O_EXCL"}
)
#: ``os`` names that write through an already-open descriptor. Allowed only in a module that
#: holds an accepted write-open site (the descriptor has to come from somewhere), and forbidden
#: everywhere else -- D151-C21 R3.
DESCRIPTOR_WRITE_OS: frozenset[str] = frozenset(
    {"ftruncate", "write", "writev", "pwrite", "pwritev", "sendfile", "copy_file_range"}
)


def module_path(name: str) -> Path | None:
    """The file a dotted package module name resolves to, or ``None``."""
    relative = name.replace(".", "/")
    for candidate in (_SRC_ROOT / f"{relative}.py", _SRC_ROOT / relative / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def package_imports(source: str) -> set[str]:
    """The ``disclosure_drift`` modules ``source`` imports by statement, both forms."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names if a.name.startswith("disclosure_drift"))
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "disclosure_drift"
        ):
            module = str(node.module)
            for alias in node.names:
                submodule = f"{module}.{alias.name}"
                names.add(submodule if module_path(submodule) is not None else module)
    return names


def reached_from(module_name: str) -> set[str]:
    """Every package module reached from ``module_name`` by import statements, transitively.

    Statement-level: the ``disclosure_drift.m3`` package ``__init__`` is executed by every
    ``m3`` import alike and is not a capability this chain adds; what is measured here is what
    the chain's own statements pull in.
    """
    seen: set[str] = set()
    frontier = [module_name]
    while frontier:
        name = frontier.pop()
        if name in seen:
            continue
        seen.add(name)
        path = module_path(name)
        assert path is not None, name
        frontier.extend(package_imports(path.read_text(encoding="utf-8")))
    return seen


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    constants: dict[str, str] = {}
    for node in tree.body:
        target = None
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
        elif isinstance(node, ast.AnnAssign):
            target = node.target
        value = getattr(node, "value", None)
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            constants[target.id] = value.value
    return constants


def _render_argv_element(element: ast.expr, constants: dict[str, str]) -> str:
    """One argv element as the allowlist spells it: a constant, a module constant's value,
    ``<sys.executable>``, ``str(<name>)``, or ``<unbounded>``."""
    if isinstance(element, ast.Constant):
        return str(element.value)
    if isinstance(element, ast.Name):
        return constants.get(element.id, f"<{element.id}>")
    if (
        isinstance(element, ast.Attribute)
        and isinstance(element.value, ast.Name)
        and element.value.id == "sys"
        and element.attr == "executable"
    ):
        return "<sys.executable>"
    if (
        isinstance(element, ast.Call)
        and isinstance(element.func, ast.Name)
        and element.func.id == "str"
        and len(element.args) == 1
        and isinstance(element.args[0], ast.Name)
        and not element.keywords
    ):
        return f"str({element.args[0].id})"
    return "<unbounded>"


def _subprocess_calls(tree: ast.Module) -> list[ast.Call]:
    subprocess_aliases: set[str] = set()
    subprocess_functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "subprocess":
                    subprocess_aliases.add(alias.asname or "subprocess")
        elif isinstance(node, ast.ImportFrom) and (node.module or "") == "subprocess":
            for alias in node.names:
                if alias.name == "*" or alias.name in _SUBPROCESS_ENTRIES:
                    subprocess_functions.add(alias.asname or alias.name)
    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id in subprocess_aliases
            and func.attr in _SUBPROCESS_ENTRIES
        ) or (isinstance(func, ast.Name) and func.id in subprocess_functions):
            calls.append(node)
    return calls


def subprocess_launches(source: str) -> list[tuple[str, tuple[str, ...]]]:
    """Every subprocess launch in ``source`` as ``(program, argv-shape)`` -- D151-C21 R3.

    The program and every argument are rendered by :func:`_render_argv_element`, so a module
    string constant is rendered by its VALUE: the merge-child launch pins the exact committed
    bootstrap text, and a changed entrypoint is a changed launch.
    """
    tree = ast.parse(source)
    constants = _module_string_constants(tree)
    launches: list[tuple[str, tuple[str, ...]]] = []
    for call in _subprocess_calls(tree):
        argv = _subprocess_argv(call)
        if not isinstance(argv, ast.List) or not argv.elts:
            launches.append(("<argv is not a literal list>", ()))
            continue
        program = _render_argv_element(argv.elts[0], constants)
        launches.append(
            (program, tuple(_render_argv_element(item, constants) for item in argv.elts[1:]))
        )
    return launches


def _os_open_write_flags(call: ast.Call, os_aliases: set[str]) -> tuple[str, ...] | None:
    """The sorted write-class ``O_*`` flag names of an ``os.open`` call, or ``None``."""
    func = call.func
    if not (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id in os_aliases
        and func.attr == "open"
    ):
        return None
    flags = call.args[1] if len(call.args) > 1 else None
    if flags is None:
        flags = next((k.value for k in call.keywords if k.arg == "flags"), None)
    names = sorted(
        {
            node.attr
            for node in ast.walk(flags)
            if isinstance(node, ast.Attribute) and node.attr.startswith("O_")
        }
        if flags is not None
        else set()
    )
    if flags is not None and not names:
        return ("<flags are not O_* names>",)
    return tuple(names) if any(name in WRITE_OPEN_FLAGS for name in names) else ()


def _builtin_open_mode_is_write(call: ast.Call) -> bool:
    mode: ast.expr | None = call.args[1] if len(call.args) > 1 else None
    if mode is None:
        mode = next((k.value for k in call.keywords if k.arg == "mode"), None)
    if mode is None:
        return False
    if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
        return any(letter in mode.value for letter in "wax+")
    return True


#: The committed merge-child bootstrap, pinned exactly -- D151-C21 R3. The only launch
#: ``chunk_multipass`` may make is ``[sys.executable, "-c", <this text>, str(request_path)]``.
MULTIPASS_CHILD_BOOTSTRAP: str = (
    "import sys;"
    "from disclosure_drift.m3.chunk_multipass import _child_main;"
    "sys.exit(_child_main(sys.argv[1]))"
)

#: The storage-binding chain: what ``chunk_tiering`` reaches for the SQLite temp binding, and
#: everything those modules reach in turn. Exact -- a new helper joins this list by review.
STORAGE_BINDING_CHAIN: frozenset[str] = frozenset(
    {
        "disclosure_drift.m3.external_working_root",
        "disclosure_drift.m3.canary_runtime",
        "disclosure_drift.m3.dock_transport",
        "disclosure_drift.errors",
        "disclosure_drift.storage.sqlite",
    }
)

#: Every module the capability and environment audits hold to an exact allowlist.
AUDITED_MODULES: tuple[str, ...] = (
    "disclosure_drift.m3.chunk_multipass",
    "disclosure_drift.m3.chunk_tiering",
    *sorted(STORAGE_BINDING_CHAIN),
)

#: The exact subprocess launches each audited module may make -- D151-C21 R3. Program AND argv
#: shape, re-derived from the committed implementation: read-only system queries with fixed
#: argv on the binding chain, the one ``sys.executable`` child launch in ``chunk_multipass``
#: with its exact bootstrap, and nothing at all in ``chunk_tiering``.
ACCEPTED_SUBPROCESS_LAUNCHES: dict[str, tuple[tuple[str, tuple[str, ...]], ...]] = {
    "disclosure_drift.m3.chunk_multipass": (
        ("<sys.executable>", ("-c", MULTIPASS_CHILD_BOOTSTRAP, "str(request_path)")),
    ),
    "disclosure_drift.m3.chunk_tiering": (),
    "disclosure_drift.m3.external_working_root": (
        ("/usr/sbin/diskutil", ("info", "-plist", "str(mount)")),
    ),
    "disclosure_drift.m3.canary_runtime": (
        ("/bin/ps", ("-ww", "-o", "args=", "-p", "str(pid)")),
        ("/usr/bin/pmset", ("-g", "ps")),
        ("/usr/sbin/ioreg", ("-r", "-k", "AppleClamshellState", "-d", "4")),
    ),
    "disclosure_drift.m3.dock_transport": (
        (
            "/usr/sbin/ioreg",
            ("-a", "-p", "IOService", "-r", "-c", "IOUSBHostDevice", "-l", "-w0"),
        ),
    ),
    "disclosure_drift.errors": (),
    "disclosure_drift.storage.sqlite": (),
}

#: The exact write-class ``os.open`` sites each audited module may hold, as sorted flag names,
#: one entry per site -- D151-C21 R3. ``canary_runtime`` holds the accepted execution-lock file
#: and pid record (D140); no other audited module opens anything for writing directly -- the
#: accepted create-once writers live in ``chunk_evidence`` and are reached by call, and the
#: guarded world creation in ``chunk_multipass`` is governed by the authority-first and
#: exact-call-site proofs, not by this list.
ACCEPTED_WRITE_OPENS: dict[str, tuple[tuple[str, ...], ...]] = {
    "disclosure_drift.m3.canary_runtime": (
        ("O_CREAT", "O_RDWR"),
        ("O_CREAT", "O_TRUNC", "O_WRONLY"),
    ),
}


def capability_violations(  # noqa: PLR0912, PLR0915
    source: str, *, module: str | None = None
) -> list[tuple[int, str]]:
    """Every forbidden capability ``source`` reaches -- D151-C19 R5, exact per module since
    D151-C21 R3.

    Both ``import`` and ``from ... import`` are inspected. Always forbidden: network modules;
    process-creating modules (``asyncio``, ``multiprocessing``, ``concurrent``, ``pty``) and
    ``create_subprocess_*``; ``shutil`` copy/move/delete; the destructive ``os`` names; the
    destructive methods on any receiver, ``Path.write_text`` / ``write_bytes`` / ``rename`` /
    ``replace`` / ``truncate`` / ``chmod`` included; a builtin ``open`` in a write, append,
    exclusive or update mode, or with a non-constant mode; a ``shell=`` that is not literally
    ``False``; a subprocess whose argv is not a literal list, whose program is not a fixed
    absolute path, whose program is a forbidden one whatever its path, or whose arguments are
    not bounded elements. A fixed absolute path alone never establishes safety.

    With ``module`` given, the module's EXACT allowlists apply as well: every subprocess launch
    must be one of :data:`ACCEPTED_SUBPROCESS_LAUNCHES` for that module (program and argv shape),
    a module with no accepted launch may not import ``subprocess`` at all, and every write-class
    ``os.open`` must be one of :data:`ACCEPTED_WRITE_OPENS` for that module, each used once,
    and a descriptor write (``os.ftruncate``, ``os.write``, ...) may appear only in a module
    that holds an accepted write-open site.
    """
    tree = ast.parse(source)
    constants = _module_string_constants(tree)
    os_aliases: set[str] = set()
    shutil_aliases: set[str] = set()
    imports_subprocess = False
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in NETWORK_MODULES or root in PROCESS_MODULES:
                    found.append((node.lineno, f"import {alias.name}"))
                if root == "os":
                    os_aliases.add(alias.asname or "os")
                if root == "shutil":
                    shutil_aliases.add(alias.asname or "shutil")
                if root == "subprocess":
                    imports_subprocess = True
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module or ""
            root = module_name.split(".")[0]
            names = [alias.name for alias in node.names]
            if root in NETWORK_MODULES or root in PROCESS_MODULES:
                found.append((node.lineno, f"from {module_name} import {', '.join(names)}"))
            if root == "shutil":
                found.extend(
                    (node.lineno, f"from shutil import {name}")
                    for name in names
                    if name == "*" or name in DESTRUCTIVE_SHUTIL
                )
            if root == "os":
                found.extend(
                    (node.lineno, f"from os import {name}")
                    for name in names
                    if name == "*" or name in DESTRUCTIVE_OS
                )
            if root == "subprocess":
                imports_subprocess = True
    subprocess_calls = _subprocess_calls(tree)
    write_opens: list[tuple[int, tuple[str, ...]]] = []
    descriptor_writes: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id in shutil_aliases and node.attr != "disk_usage":
                found.append((node.lineno, f"shutil.{node.attr}"))
            if node.value.id in os_aliases and node.attr in DESTRUCTIVE_OS:
                found.append((node.lineno, f"os.{node.attr}"))
            if node.value.id in os_aliases and node.attr in DESCRIPTOR_WRITE_OS:
                descriptor_writes.append((node.lineno, f"os.{node.attr}"))
            if node.attr in ASYNC_PROCESS_NAMES:
                found.append((node.lineno, f".{node.attr}"))
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in (DESTRUCTIVE_SHUTIL | _DESTRUCTIVE_METHODS):
            found.append((node.lineno, f"{func.id}("))
        if isinstance(func, ast.Attribute) and func.attr in _DESTRUCTIVE_METHODS:
            found.append((node.lineno, f".{func.attr}("))
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "replace"
            and len(node.args) == 1
            and not node.keywords
        ):
            found.append((node.lineno, ".replace(<target>) -- the Path.replace shape"))
        if isinstance(func, ast.Name) and func.id == "open" and _builtin_open_mode_is_write(node):
            found.append((node.lineno, "open( in a write, append, exclusive or unknown mode"))
        flags = _os_open_write_flags(node, os_aliases)
        if flags:
            write_opens.append((node.lineno, flags))
        if node not in subprocess_calls:
            continue
        for keyword in node.keywords:
            if keyword.arg is None:
                found.append((node.lineno, "subprocess **kwargs"))
            if keyword.arg == "shell" and not (
                isinstance(keyword.value, ast.Constant) and keyword.value.value is False
            ):
                found.append((node.lineno, "subprocess shell="))
        argv = _subprocess_argv(node)
        if not isinstance(argv, ast.List) or not argv.elts:
            found.append((node.lineno, "subprocess argv is not a literal list"))
            continue
        program = argv.elts[0]
        rendered = _render_argv_element(program, constants)
        fixed = rendered == "<sys.executable>" or rendered.startswith("/")
        if not fixed:
            found.append((node.lineno, "subprocess program is not a fixed absolute path"))
        if rendered.rsplit("/", 1)[-1] in FORBIDDEN_PROGRAM_NAMES:
            found.append((node.lineno, f"subprocess program {rendered!r} is forbidden"))
        for element in argv.elts[1:]:
            if _render_argv_element(element, constants) == "<unbounded>":
                found.append((node.lineno, "subprocess argument is not a bounded element"))
    if module is not None:
        allowed = ACCEPTED_SUBPROCESS_LAUNCHES.get(module)
        if allowed is None:
            found.append((0, f"{module} is not an audited module and has no allowlist"))
            allowed = ()
        for call, launch in zip(subprocess_calls, subprocess_launches(source), strict=True):
            if launch not in allowed:
                found.append((call.lineno, f"subprocess launch not allowlisted: {launch!r}"))
        if not allowed and imports_subprocess:
            found.append((0, f"{module} imports subprocess and has no accepted program"))
        remaining = list(ACCEPTED_WRITE_OPENS.get(module, ()))
        for lineno, flags in write_opens:
            if flags in remaining:
                remaining.remove(flags)
            else:
                found.append((lineno, f"os.open write site not allowlisted: {flags!r}"))
        if not ACCEPTED_WRITE_OPENS.get(module):
            found.extend(
                (lineno, f"{name} in a module with no accepted write-open site")
                for lineno, name in descriptor_writes
            )
    return sorted(set(found))


def subprocess_programs(source: str) -> set[str]:
    """The fixed programs every subprocess call in ``source`` runs (``<sys.executable>`` for
    the interpreter's own path)."""
    return {program for program, _argv in subprocess_launches(source)}


def test_z02_no_environment_derived_configuration_capability_beyond_the_accepted_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The finite property D151-C21 R2 defines: through every route
    :data:`ENVIRONMENT_ROUTE_TAXONOMY` names, no audited module derives configuration from the
    process environment except the two exact owner-approved ``SQLITE_TMPDIR`` reads; and no
    command-line surface reaches the multipass modules."""
    from disclosure_drift import cli

    cli_source = Path(cli.__file__).read_text(encoding="utf-8")
    for name in ("chunk_multipass", "chunk_tiering", "multipass", "tiering", "chunked"):
        assert name not in cli_source, name
    for module in NEW_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        # D151-C19 R3 (closing D151-C18 MINOR-2): the closure is decided by what names are BOUND
        # to, so `from os import environ`, an aliased `os`, a subscript through an alias and
        # `os.getenv` are all seen. D151-C21 R2 widened the audited routes to the owner-defined
        # finite taxonomy (path expansion, pathlib, tempfile, getpass, shutil.which, ctypes,
        # reflective and dynamic import, environment-printing subprocesses). The multipass path
        # reads EXACTLY ONE environment name -- SQLITE_TMPDIR, in chunk_tiering, inside the
        # binding guard, in the accepted D138-R3 shape -- because that is the only environment
        # SQLite itself consults to decide where it spills. What the invariant always protected
        # is unchanged and re-proved below: no environment value can GRANT authority or SUPPLY a
        # sizing term.
        assert environment_closure_violations(module.__name__, source) == [], module.__name__
        assert "DISCLOSURE_DRIFT" not in source, module.__name__
        assert "load_config" not in names, module.__name__
        assert "argparse" not in source, module.__name__
        assert "apply_migrations" not in source, module.__name__
        assert "build_calibration_chunk_plan" not in source, module.__name__
    assert environment_accesses(Path(cm.__file__).read_text(encoding="utf-8")) == []
    tiering = Path(ct.__file__).read_text(encoding="utf-8")
    permitted = permitted_sqlite_tmpdir_reads(tiering, function="require_sqlite_temp_binding")
    assert len(permitted) == 1, permitted
    assert [item[1] for item in environment_accesses(tiering)] == ["os.environ"]
    # D151-C21 R2: the same finite property over every audited module, with the exact accepted
    # read sites and nothing else.
    for name in AUDITED_MODULES:
        path = module_path(name)
        assert path is not None, name
        assert environment_closure_violations(name, path.read_text(encoding="utf-8")) == [], name
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
    # D151-C17 R6: the one environment name the path DOES read cannot grant anything either.
    # Pointing it at a real directory admits nothing -- the sizing terms still refuse -- and the
    # binding guard it feeds still measures two volume identities rather than trusting the value.
    monkeypatch.setenv(ewr.SQLITE_TMPDIR_ENV, str(Path(cm.__file__).parent))
    assert "NOT AUTHORIZED" in refusal_in_a_fresh_interpreter()
    with pytest.raises(ct.ChunkTieringError, match="NOT ADMISSIBLE"):
        ct.accepted_multipass_storage_requirements()


def test_z03_no_new_module_can_delete_copy_or_reach_a_transport() -> None:
    for module in NEW_MODULES:
        source = Path(module.__file__).read_text(encoding="utf-8")
        # AST, not substring -- D151-C17. chunk_tiering DESCRIBES, at length, SQLite unlinking
        # the spill files it is still writing, because that is the whole reason the level-2
        # transient term must be measured as free-space drawdown rather than by a traversal. A
        # text ban cannot tell that prose from a capability; the call can.
        assert capability_violations(source) == [], module.__name__
        module_tree = ast.parse(source)
        assert "shutil" not in {
            node.value.id
            for node in ast.walk(module_tree)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
        }, module.__name__
        for prefix in PROHIBITED_IMPORT_PREFIXES:
            assert f"import {prefix}" not in source
            assert f"from {prefix}" not in source
        assert "from disclosure_drift.m3.e0" not in source
        assert "M3_3_E0_EXECUTION_AUTHORITY" not in source
        names = {node.attr for node in ast.walk(module_tree) if isinstance(node, ast.Attribute)} | {
            node.id for node in ast.walk(module_tree) if isinstance(node, ast.Name)
        }
        for needle in ("SecClient", "HttpxTransport", "socket", "urlopen", "create_connection"):
            assert needle not in names, (module.__name__, needle)
    assert "shutil" not in Path(ct.__file__).read_text(encoding="utf-8")
    # D151-C17 R6: chunk_tiering reaches external_working_root, and chunk_multipass still does
    # not. The ban is an allowlist of exactly the accepted D137-R8 names plus the ONE shared
    # candidate validator D151-C19 R2 added.
    assert "external_working_root" not in Path(cm.__file__).read_text(encoding="utf-8")
    tiering_source = Path(ct.__file__).read_text(encoding="utf-8")
    imported = {
        alias.name
        for node in ast.walk(ast.parse(tiering_source))
        if isinstance(node, ast.ImportFrom)
        and node.module == "disclosure_drift.m3.external_working_root"
        for alias in node.names
    }
    assert imported == {
        "SQLITE_TMPDIR_ENV",
        "ExternalWorkingRootError",
        "VolumeIdentity",
        "VolumeIdentityProvider",
        "require_usable_sqlite_temp_root",
    }, imported
    # D151-C19 R5 (closing D151-C18 INFO-2): the proof covers the chain ACTUALLY reached --
    # external_working_root, canary_runtime, dock_transport and the two leaf helpers -- by both
    # import statement forms, and it distinguishes the accepted bounded capability (a fixed-argv
    # read-only system query) from a forbidden one rather than banning every import.
    assert reached_from(ewr.__name__) == set(STORAGE_BINDING_CHAIN)
    # D151-C22: chunk_tiering additionally reaches the qualification-record module, which reads
    # sealed Host-A/SSD qualification records and launches only fixed read-only system queries.
    assert package_imports(tiering_source) == {
        "disclosure_drift.errors",
        "disclosure_drift.m3.external_working_root",
        "disclosure_drift.m3.chunk_evidence",
        "disclosure_drift.m3.chunk_plan",
        "disclosure_drift.m3.chunk_storage",
        "disclosure_drift.m3.host_a_ssd_qualification",
    }
    programs: dict[str, set[str]] = {}
    for name in sorted(STORAGE_BINDING_CHAIN):
        path = module_path(name)
        assert path is not None, name
        reached_source = path.read_text(encoding="utf-8")
        assert capability_violations(reached_source) == [], name
        assert environment_closure_violations(name, reached_source) == [], name
        programs[name] = subprocess_programs(reached_source)
    # D151-C21 R3 (closing D151-C20 MINOR-3): a fixed absolute path is never sufficient. Every
    # audited module is held to its EXACT program-and-argv allowlist and its exact write-open
    # sites: chunk_tiering launches nothing and may not import subprocess; chunk_multipass makes
    # the one sys.executable launch with the exact committed bootstrap; the chain's inspection
    # programs keep their accepted fixed read-only argv.
    for name in AUDITED_MODULES:
        path = module_path(name)
        assert path is not None, name
        audited_source = path.read_text(encoding="utf-8")
        assert capability_violations(audited_source, module=name) == [], name
        assert subprocess_launches(audited_source) == list(ACCEPTED_SUBPROCESS_LAUNCHES[name]), name
    assert committed_literal(cm, "_CHILD_BOOTSTRAP") == MULTIPASS_CHILD_BOOTSTRAP
    assert programs == {
        "disclosure_drift.errors": set(),
        "disclosure_drift.m3.canary_runtime": {"/bin/ps", "/usr/bin/pmset", "/usr/sbin/ioreg"},
        "disclosure_drift.m3.dock_transport": {"/usr/sbin/ioreg"},
        "disclosure_drift.m3.external_working_root": {"/usr/sbin/diskutil"},
        "disclosure_drift.storage.sqlite": set(),
    }, programs
    ewr_source = Path(ewr.__file__).read_text(encoding="utf-8")
    assert (
        len(permitted_sqlite_tmpdir_reads(ewr_source, function="require_external_sqlite_tmpdir"))
        == 1
    )


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
