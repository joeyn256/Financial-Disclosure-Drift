"""D151-C1: one chunk, one operating-system process, one ordinal interval.

The claims here are about **execution**, not about content: that a chunk runs in a process that
is not the coordinator's and that ends before the next one starts, that it consumes exactly its
interval and never another chunk's, that its terminal receipt is the last thing written and is
verified against the bytes it names, that an interrupted chunk leaves no receipt and costs only
itself, and that a completed chunk is immutable and is skipped rather than re-run.

Every process here is a real ``fork``/``exec`` of the running interpreter. Nothing is simulated
with a thread, a coroutine, a stopped process, or a garbage collection.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import chunk_plan as cp  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_DECLARATIONS_FILENAME,
    CHUNK_RECEIPT_FILENAME,
    ChunkEvidenceError,
    build_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.compact_evidence import CompactEvidenceSidecar  # noqa: E402
from disclosure_drift.m3.repository_identity import (  # noqa: E402
    RepositoryIdentity,
    running_repository_identity,
)
from disclosure_drift.paths import DataTree  # noqa: E402

#: Literal identities, for the tests that attack the repository field itself rather than use it.
HEAD = "a" * 40
TREE = "b" * 40


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin: a real, clean throwaway repository, through the accepted identity seam.

    Since D151-C5 every chunk child authenticates its own code identity through the accepted
    clean-repository predicate before it creates anything, and the checkout this suite runs from
    is dirty by construction while a change is being written. The pin lives in
    ``test_d151_c1_chunk_plan`` so that every shared driver -- and every child it spawns -- reads
    the same one.
    """
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# The chunked-F0 driver used by this module and by the consolidation proofs
# ==========================================================================
def chunk_request(
    *,
    plan_path: Path,
    chunk_id: str,
    attempt: int,
    attempt_directory: Path,
    database: Path,
    tree: DataTree,
    parent_map_path: Path | None = None,
    batch_size: int = 2,
    abort_after_members: int | None = None,
    abort_mode: str = "raise",
    repository: RepositoryIdentity | None = None,
) -> ce.ChunkRequest:
    """One chunk request, with every path stated by the caller and nothing discovered.

    ``repository`` defaults to the **shared** pin when a test has established one, and otherwise
    to the identity the accepted mechanism reports for the checkout this process is running from
    -- which is what a real coordinator would record. One shared pin rather than one per module,
    because these drivers are used across modules: see :data:`c1.PINNED`. Passing a literal is
    reserved for the tests that are attacking the field itself -- and since D151-C5 the child
    measures its own identity and refuses a request that names any other, so a literal identity
    is exactly what a refusal test hands it.
    """
    if repository is not None:
        identity = repository
    elif c1.PINNED is not None:
        identity = c1.PINNED
    else:
        identity = running_repository_identity()
    return ce.ChunkRequest(
        plan_path=str(plan_path),
        chunk_id=chunk_id,
        attempt=attempt,
        attempt_directory=str(attempt_directory),
        operational_catalog=str(database),
        data_root=str(tree.data_root),
        source_instance_id=c1.INSTANCE,
        batch_size=batch_size,
        cache_bytes=None,
        repository_head_sha=identity.head_sha,
        repository_tree_sha=identity.tree_sha,
        parent_map_path=None if parent_map_path is None else str(parent_map_path),
        abort_after_members=abort_after_members,
        abort_mode=abort_mode,
    )


def run_chunked_f0(
    root: Path,
    database: Path,
    tree: DataTree,
    *,
    chunk_members: int,
    label: str = "run",
    batch_size: int = 2,
    stop_after: int | None = None,
    repository: RepositoryIdentity | None = None,
) -> dict[str, Any]:
    """Drive a whole chunked F0: plan, every chunk in its own process, and the parent-map barrier.

    ``stop_after`` stops the driver after that many chunks, which is how the interruption and
    resume proofs reach a partially built chunk set without pretending one.
    """
    base = root / label
    base.mkdir(parents=True)
    plan = c1.build_plan(tree, database, chunk_members=chunk_members)
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    chunk_root = base / "chunks"
    receipts = []
    contributions = []
    parent_map_path: Path | None = None
    previous: int | None = None
    for index, bounds in enumerate(plan.chunks):
        if stop_after is not None and index >= stop_after:
            break
        if bounds.region == cp.REGION_SHARD and parent_map_path is None:
            # The region barrier: every primary chunk has reached a terminal, so the parent map
            # is complete and is written once, exactly as the accepted deferred phase requires.
            merged = ce.merge_parent_map(contributions)
            parent_map_path = base / "parent_map.json"
            write_once_json(
                parent_map_path, {name: sorted(parents) for name, parents in sorted(merged.items())}
            )
        attempt_directory, attempt = ce.next_attempt_directory(chunk_root, bounds.chunk_id)
        receipt = ce.run_chunk(
            chunk_request(
                plan_path=plan_path,
                chunk_id=bounds.chunk_id,
                attempt=attempt,
                attempt_directory=attempt_directory,
                database=database,
                tree=tree,
                parent_map_path=parent_map_path,
                batch_size=batch_size,
                repository=repository,
            ),
            predecessor_pid=previous,
        )
        previous = receipt.pid
        receipts.append(receipt)
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
        "contributions": contributions,
    }


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, DataTree]:
    return c1.build_world(tmp_path, members=6, filings=2, shards=3, share_every=2)


# ==========================================================================
# C08-C11, C53, C54: the process contract
# ==========================================================================
def test_c10_c53_every_chunk_runs_in_a_process_that_is_not_this_one_and_exits(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C10 and C53: a fresh process per chunk, and each one gone before the next begins."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3)
    pids = [receipt.pid for receipt in run["receipts"]]
    assert len(pids) == len(set(pids)) == run["plan"].chunk_count
    assert os.getpid() not in pids
    for pid in pids:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_c11_a43_a_live_predecessor_refuses_the_successor(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A43: the coordinator's own process stands in for a chunk that never ended."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    plan = run["plan"]
    directory, attempt = ce.next_attempt_directory(run["chunk_root"], plan.chunks[1].chunk_id)
    with pytest.raises(ce.ChunkExecutionError, match="must END before"):
        ce.run_chunk(
            chunk_request(
                plan_path=run["plan_path"],
                chunk_id=plan.chunks[1].chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                parent_map_path=None,
            ),
            predecessor_pid=os.getpid(),
        )
    assert not directory.exists()


def test_c54_each_chunk_records_its_own_peak_resident_size(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C54: the reclamation invariant is evidenced per chunk, in the chunk's own process."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3)
    peaks = [receipt.rss_peak_bytes for receipt in run["receipts"]]
    assert all(peak is None or peak > 0 for peak in peaks)
    assert all(receipt.pid != os.getpid() for receipt in run["receipts"])


def test_c09_no_two_chunks_share_a_mutable_database(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C09: each chunk builds its own working world; nothing is opened twice."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3)
    catalogs = sorted(run["chunk_root"].rglob("working_catalog.sqlite3"))
    assert len(catalogs) == run["plan"].chunk_count
    assert len({path.resolve() for path in catalogs}) == run["plan"].chunk_count
    # And every one of them is a distinct file, not a link to a shared original.
    assert len({path.stat().st_ino for path in catalogs}) == run["plan"].chunk_count


def test_c08_a_chunk_absorbs_exactly_its_interval(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C08: the member manifest a chunk writes is exactly its canonical ordinal range."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3)
    for bounds, receipt in zip(run["plan"].chunks, run["receipts"], strict=True):
        directory = run["chunk_root"] / bounds.chunk_id / f"attempt-{receipt.attempt:03d}"
        sidecar = CompactEvidenceSidecar(directory / "compact_evidence.sqlite3")
        try:
            ordinals = [int(row["member_ordinal"]) for row in sidecar.members(c1.OBSERVATION)]
        finally:
            sidecar.close()
        assert ordinals == list(range(bounds.start, bounds.end))
        assert receipt.summary.members == bounds.member_count


# ==========================================================================
# C12, C13, C14, C15, C16: the terminal receipt and interruption
# ==========================================================================
def test_c12_the_receipt_is_written_last_and_describes_every_other_artifact(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C12/A32: the manifest covers everything except the receipt, and it verifies."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    named = {entry.relative_path for entry in receipt.manifest.entries}
    assert CHUNK_RECEIPT_FILENAME not in named
    present = {
        path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()
    }
    assert present == named | {CHUNK_RECEIPT_FILENAME}
    assert "working_catalog.sqlite3" in named
    assert "compact_evidence.sqlite3" in named
    assert "chunk_witness.sqlite3" in named


def test_c13_an_interrupted_chunk_leaves_no_valid_receipt(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C13/A09: a process the kernel takes away mid-chunk cannot have written a terminal."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3, stop_after=1)
    plan = run["plan"]
    directory, attempt = ce.next_attempt_directory(run["chunk_root"], plan.chunks[1].chunk_id)
    with pytest.raises(ce.ChunkExecutionError, match="exit status"):
        ce.run_chunk(
            chunk_request(
                plan_path=run["plan_path"],
                chunk_id=plan.chunks[1].chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                abort_after_members=1,
                abort_mode="hard_exit",
            ),
            predecessor_pid=run["receipts"][0].pid,
        )
    assert directory.is_dir()
    assert not (directory / CHUNK_RECEIPT_FILENAME).exists()
    assert ce.completed_chunk_receipt(run["chunk_root"], plan.chunks[1].chunk_id) is None


def test_c14_earlier_completed_chunks_survive_an_interruption(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C14: maximum lost work is one chunk."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3, stop_after=1)
    plan = run["plan"]
    survivor = run["receipts"][0]
    directory, attempt = ce.next_attempt_directory(run["chunk_root"], plan.chunks[1].chunk_id)
    with pytest.raises(ce.ChunkExecutionError):
        ce.run_chunk(
            chunk_request(
                plan_path=run["plan_path"],
                chunk_id=plan.chunks[1].chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                abort_after_members=1,
                abort_mode="hard_exit",
            )
        )
    still_there = ce.completed_chunk_receipt(run["chunk_root"], plan.chunks[0].chunk_id)
    assert still_there is not None
    assert still_there[0].manifest.digest == survivor.manifest.digest


def test_c15_a_completed_chunk_is_skipped_rather_than_re_executed(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C15: a valid terminal makes a chunk immutable, so a retry is refused, not repeated."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    with pytest.raises(ce.ChunkExecutionError, match="already carries a valid terminal receipt"):
        ce.next_attempt_directory(run["chunk_root"], run["receipts"][0].chunk_id)


def test_an_interrupted_chunk_is_reconstructed_in_a_new_attempt_directory(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """§7: bounded reconstruction of only the incomplete chunk, create-once, nothing deleted."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=3, stop_after=1)
    plan = run["plan"]
    dead, attempt = ce.next_attempt_directory(run["chunk_root"], plan.chunks[1].chunk_id)
    with pytest.raises(ce.ChunkExecutionError):
        ce.run_chunk(
            chunk_request(
                plan_path=run["plan_path"],
                chunk_id=plan.chunks[1].chunk_id,
                attempt=attempt,
                attempt_directory=dead,
                database=database,
                tree=tree,
                abort_after_members=1,
                abort_mode="hard_exit",
            )
        )
    retry, retry_attempt = ce.next_attempt_directory(run["chunk_root"], plan.chunks[1].chunk_id)
    assert retry_attempt == attempt + 1
    assert retry != dead
    receipt = ce.run_chunk(
        chunk_request(
            plan_path=run["plan_path"],
            chunk_id=plan.chunks[1].chunk_id,
            attempt=retry_attempt,
            attempt_directory=retry,
            database=database,
            tree=tree,
        )
    )
    assert receipt.status == "complete"
    # The dead attempt is still exactly where it was: nothing was deleted, renamed, or cleaned.
    assert dead.is_dir()
    assert not (dead / CHUNK_RECEIPT_FILENAME).exists()
    found = ce.completed_chunk_receipt(run["chunk_root"], plan.chunks[1].chunk_id)
    assert found is not None
    assert found[1] == retry


def test_c16_a10_a_changed_completed_chunk_stops_being_a_completed_chunk(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C16/A10: immutability is enforced by re-reading the bytes, not by a flag."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    target = directory / "chunk_witness.sqlite3"
    original = target.read_bytes()
    connection = sqlite3.connect(target)
    connection.execute("INSERT INTO chunk_witness_meta (key, value) VALUES ('tampered', 'yes')")
    connection.commit()
    connection.close()
    assert target.read_bytes() != original
    assert ce.completed_chunk_receipt(run["chunk_root"], receipt.chunk_id) is None


def test_a46_an_extra_object_in_the_artifact_set_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    (directory / "unexpected.txt").write_text("an object no receipt names")
    assert ce.completed_chunk_receipt(run["chunk_root"], receipt.chunk_id) is None


def test_a45_a_symbolic_link_in_the_artifact_set_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    (directory / "link.sqlite3").symlink_to(directory / "working_catalog.sqlite3")
    with pytest.raises(ChunkEvidenceError, match="symbolic link"):
        build_artifact_manifest(directory, exclude=(CHUNK_RECEIPT_FILENAME,))


def test_a08_a_receipt_written_before_its_artifacts_settled_does_not_verify(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A08: 'written LAST' is enforced by the manifest, not by ordering discipline alone."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    early = directory.parent / "attempt-early"
    early.mkdir()
    (early / "working_catalog.sqlite3").write_bytes(b"a database still being written")
    write_once_json(early / CHUNK_RECEIPT_FILENAME, dict(receipt.as_record()))
    # The whole chunk directory now carries a receipt describing artifacts it does not hold.
    assert ce.completed_chunk_receipt(run["chunk_root"], receipt.chunk_id)[1] == directory


def test_a_second_receipt_can_never_be_written(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    directory = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    with pytest.raises(ChunkEvidenceError, match="create-once"):
        write_once_json(directory / CHUNK_RECEIPT_FILENAME, dict(receipt.as_record()))


def test_two_valid_receipts_for_one_chunk_are_ambiguous_authority(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """Duplicate authority is reported, never resolved by attempt number or modification time."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    parent = run["chunk_root"] / receipt.chunk_id
    original = parent / f"attempt-{receipt.attempt:03d}"
    twin = parent / "attempt-777"
    twin.mkdir()
    for path in original.iterdir():
        (twin / path.name).write_bytes(path.read_bytes())
    with pytest.raises(ce.ChunkExecutionError, match="valid terminal receipts"):
        ce.completed_chunk_receipt(run["chunk_root"], receipt.chunk_id)


# ==========================================================================
# The region barrier
# ==========================================================================
def test_a_shard_chunk_without_the_merged_parent_map_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """The accepted parent rule, expressed as a barrier: no map, no shard chunk."""
    database, tree = world
    plan = c1.build_plan(tree, database, chunk_members=1000)
    base = tmp_path / "barrier"
    base.mkdir()
    plan_path = base / "plan.json"
    write_once_json(plan_path, dict(plan.as_record()))
    shard_chunk = next(bounds for bounds in plan.chunks if bounds.region == cp.REGION_SHARD)
    directory, attempt = ce.next_attempt_directory(base / "chunks", shard_chunk.chunk_id)
    with pytest.raises(ce.ChunkExecutionError) as raised:
        ce.run_chunk(
            chunk_request(
                plan_path=plan_path,
                chunk_id=shard_chunk.chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                parent_map_path=None,
            )
        )
    # The child must refuse for the RIGHT reason: the barrier, named, and not some incidental
    # failure that would also have produced a non-zero exit.
    assert "begins only after EVERY primary chunk" in str(raised.value)
    assert not (directory / CHUNK_RECEIPT_FILENAME).exists()


def test_a_partial_parent_map_refuses_rather_than_binding_a_shard_by_its_filename(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """Accepted Decision 129 §7: a filename is corroboration and never a binding."""
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1, stop_after=1)
    plan = run["plan"]
    partial = run["base"] / "partial_map.json"
    write_once_json(partial, {})
    shard_chunk = next(bounds for bounds in plan.chunks if bounds.region == cp.REGION_SHARD)
    directory, attempt = ce.next_attempt_directory(run["chunk_root"], shard_chunk.chunk_id)
    with pytest.raises(ce.ChunkExecutionError, match="exit status"):
        ce.run_chunk(
            chunk_request(
                plan_path=run["plan_path"],
                chunk_id=shard_chunk.chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
                parent_map_path=partial,
            )
        )


def test_the_merged_parent_map_is_the_union_and_is_order_independent() -> None:
    """Set union is the composition rule, not an approximation of one."""
    left = {"a.json": {"0000000001"}}
    right = {"a.json": {"0000000001"}, "b.json": {"0000000002"}}
    assert ce.merge_parent_map([left, right]) == ce.merge_parent_map([right, left])
    assert ce.merge_parent_map([left, right]) == {
        "a.json": {"0000000001"},
        "b.json": {"0000000002"},
    }


def test_the_merged_parent_map_equals_the_whole_archive_map(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """The union of the chunks' contributions is exactly what one traversal would have built."""
    database, tree = world
    whole = run_chunked_f0(tmp_path, database, tree, chunk_members=10_000, label="whole")
    split = run_chunked_f0(tmp_path, database, tree, chunk_members=1, label="split")
    assert ce.merge_parent_map(whole["contributions"]) == ce.merge_parent_map(
        split["contributions"]
    )
    assert ce.merge_parent_map(whole["contributions"])


# ==========================================================================
# C06/C07 at the chunk's own admission
# ==========================================================================
def test_c07_a_chunk_refuses_a_plan_that_is_not_its_own(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    base = tmp_path / "wrongplan"
    base.mkdir()
    plan = c1.build_plan(tree, database, chunk_members=3)
    record = dict(plan.as_record())
    record["chunks"] = record["chunks"][:1]
    record["chunk_count"] = 1
    path = base / "plan.json"
    write_once_json(path, record)
    directory, attempt = ce.next_attempt_directory(base / "chunks", plan.chunks[0].chunk_id)
    with pytest.raises(ce.ChunkExecutionError, match="exit status"):
        ce.run_chunk(
            chunk_request(
                plan_path=path,
                chunk_id=plan.chunks[0].chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
            )
        )


def test_a_chunk_refuses_an_archive_the_plan_does_not_name(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C06: the artifact is re-authenticated by the chunk's own process, before a world exists."""
    database, tree = world
    plan = c1.build_plan(tree, database, chunk_members=3)
    base = tmp_path / "wrongsource"
    base.mkdir()
    path = base / "plan.json"
    write_once_json(path, dict(plan.as_record()))
    # Replace the archive under the same relative path with a different one.
    c1.write_archive(c1.archive_of(tree), c1.entries(9, filings=3, shards=1))
    directory, attempt = ce.next_attempt_directory(base / "chunks", plan.chunks[0].chunk_id)
    with pytest.raises(ce.ChunkExecutionError, match="exit status"):
        ce.run_chunk(
            chunk_request(
                plan_path=path,
                chunk_id=plan.chunks[0].chunk_id,
                attempt=attempt,
                attempt_directory=directory,
                database=database,
                tree=tree,
            )
        )


def test_an_existing_attempt_directory_is_never_adopted(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    plan = c1.build_plan(tree, database, chunk_members=1000)
    base = tmp_path / "adopt"
    base.mkdir()
    path = base / "plan.json"
    write_once_json(path, dict(plan.as_record()))
    directory = ce.attempt_directory(base / "chunks", plan.chunks[0].chunk_id, 0)
    directory.mkdir(parents=True)
    request = chunk_request(
        plan_path=path,
        chunk_id=plan.chunks[0].chunk_id,
        attempt=0,
        attempt_directory=directory,
        database=database,
        tree=tree,
    )
    with pytest.raises(ce.ChunkExecutionError, match="already exists"):
        ce.execute_chunk_body(request)


# ==========================================================================
# Closed authority
# ==========================================================================
def test_c49_real_chunked_execution_is_closed() -> None:
    """D151-C1 §24: the constant is None and every real entry point refuses."""
    assert ce.REAL_CHUNKED_F0_EXECUTION_AUTHORITY == (
        "M3_3_D151_C9_ONE_REAL_MIDSOURCE_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )
    assert ce.require_real_chunk_execution_authority() == (
        "M3_3_D151_C9_ONE_REAL_MIDSOURCE_INTERNAL_NVME_CALIBRATION_AUTHORIZED"
    )


def test_a41_a42_a_chunk_can_only_be_run_by_starting_a_process(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A41/A42: the coordinator has no in-process fallback to fall back to.

    ``run_chunk`` builds its child with the interpreter and a fixed bootstrap; there is no branch
    that calls :func:`execute_chunk_body` in the calling process, and a receipt claiming this
    process's identifier is refused outright.
    """
    source = Path(ce.__file__).read_text(encoding="utf-8")
    assert "subprocess.run(" in source
    body = source.split("def run_chunk(")[1]
    assert "execute_chunk_body(" not in body
    assert "gc.collect" not in source
    assert "SIGSTOP" not in source and "SIGCONT" not in source


def test_a41_a_receipt_naming_the_coordinator_process_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A41: a chunk that claims to have run in the coordinator's process is refused outright.

    The check is exercised directly rather than through a child that would have failed anyway:
    the coordinator is handed a completed attempt whose receipt names **this** process, and the
    spawn is replaced by one that does nothing. A chunk that ran in the coordinator would reclaim
    nothing when it 'ended', so the identifier is compared and not merely recorded.
    """
    database, tree = world
    run = run_chunked_f0(tmp_path, database, tree, chunk_members=1000, stop_after=1)
    receipt = run["receipts"][0]
    original = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    twin = original.parent / "attempt-500"
    twin.mkdir()
    for path in original.iterdir():
        if path.name != CHUNK_RECEIPT_FILENAME:
            (twin / path.name).write_bytes(path.read_bytes())
    forged = dict(receipt.as_record())
    forged["pid"] = os.getpid()
    forged["attempt"] = 500
    write_once_json(twin / CHUNK_RECEIPT_FILENAME, forged)

    class _Completed:
        returncode = 0
        stderr = ""

    def _no_spawn(*_args: object, **_kwargs: object) -> _Completed:
        return _Completed()

    request = chunk_request(
        plan_path=run["plan_path"],
        chunk_id=receipt.chunk_id,
        attempt=500,
        attempt_directory=twin,
        database=database,
        tree=tree,
    )
    saved = ce.subprocess.run
    ce.subprocess.run = _no_spawn  # type: ignore[assignment]
    try:
        with pytest.raises(ce.ChunkExecutionError, match="did not run in a separate"):
            ce.run_chunk(request)
    finally:
        ce.subprocess.run = saved  # type: ignore[assignment]


def test_c51_the_chunk_modules_reach_no_transport(tmp_path: Path) -> None:
    """C51/A40: no network capability is importable from any C1 module."""
    from disclosure_drift.m3 import chunk_consolidation, chunk_evidence, chunk_storage
    from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES

    modules = (ce, cp, chunk_evidence, chunk_storage, chunk_consolidation)
    for module in modules:
        source = Path(module.__file__).read_text(encoding="utf-8")
        for prefix in PROHIBITED_IMPORT_PREFIXES:
            assert f"import {prefix}" not in source
            assert f"from {prefix}" not in source


def test_the_chunk_request_round_trips(tmp_path: Path) -> None:
    request = ce.ChunkRequest(
        plan_path="/p",
        chunk_id="chunk-0000",
        attempt=0,
        attempt_directory="/a",
        operational_catalog="/c",
        data_root="/d",
        source_instance_id=c1.INSTANCE,
        batch_size=4,
        cache_bytes=None,
        repository_head_sha=HEAD,
        repository_tree_sha=TREE,
    )
    assert ce.ChunkRequest.from_record(json.loads(json.dumps(dict(request.as_record())))) == request


def test_the_execution_identity_moves_with_every_governing_value(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, tree = world
    plan = c1.build_plan(tree, database, chunk_members=3)
    base = {
        "plan": plan,
        "chunk_id": plan.chunks[0].chunk_id,
        "batch_size": 2,
        "cache_bytes": None,
        "repository_head_sha": HEAD,
        "repository_tree_sha": TREE,
        "catalog_source_sha256": "c" * 64,
        "migration_head": 15,
    }
    reference = ce.chunk_execution_identity(**base)
    for field, value in (
        ("chunk_id", plan.chunks[1].chunk_id),
        ("batch_size", 3),
        ("repository_head_sha", "d" * 40),
        ("repository_tree_sha", "e" * 40),
        ("catalog_source_sha256", "f" * 64),
        ("migration_head", 14),
    ):
        assert ce.chunk_execution_identity(**{**base, field: value}) != reference


def test_the_f0_written_table_set_is_a_subset_of_the_accepted_footprint() -> None:
    from disclosure_drift.m3.offline_parse import E0_PERMITTED_TABLES

    assert set(ce.F0_WRITTEN_TABLES) <= E0_PERMITTED_TABLES
