"""D151-C3 §7: the consolidated world, proved through the ACCEPTED phase machinery.

D151-C1 proved F1 and F2 would accept a consolidated world by **calling them directly**. That is
not the same claim. The accepted Decision 145 path does considerably more than call a phase body:
it re-reads the plan in a fresh process, re-derives the repository identity, re-derives the plan
fingerprint, admits the phase against its predecessor's durable checkpoint, proves the
predecessor's process is gone, runs the body inside the accepted write containment, writes F1's
evidence at F1's own terminal, takes the accepted pre-F2 free-space gate immediately before F2's
transaction opens, assembles the result document from durable values, and writes a create-once
terminal checkpoint LAST. A world that satisfies a direct call and fails any of that is a world
that fails at the end of a twenty-seven-hour run.

So this module drives :func:`~disclosure_drift.m3.single_source_canary._run_phase_locked` -- the
accepted phase machinery itself -- once per phase, each in a **fresh operating-system process**,
over both a consolidated chunked F0 world and a monolithic F0 world produced by the same
machinery, and compares what the two runs produced.

**Two host seams, both of them capacity predicates, and neither of them weakens a guard.**

*The external envelope* is absent: ``external=None`` is the accepted internal-root path, which is
what a host with no qualified external volume is. Host B is capacity-ineligible; the dock,
volume-UUID, power and lid predicates are Host-A hardware questions and are not reachable here.

*The free-space measurement* is pinned, through the accepted ``shutil.disk_usage`` seam that
Decisions 127 and 137 already use. :data:`PRE_F2_MINIMUM_FREE_BYTES` is untouched, the comparison
is untouched, and :func:`test_the_fifty_gib_guard_is_not_weakened` proves both halves through that
same seam -- the guard still holds the accepted constant, F2 over this very world is REFUSED one
byte below the floor and ADMITTED at it -- without ever asking the physical host how much room it
has (D151-C5 MINOR-1).
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F0,
    PHASE_F1,
    PHASE_F2,
    read_phase_checkpoint,
)
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    RunProgressLedger,
)
from disclosure_drift.paths import DataTree  # noqa: E402

BATCH = 2

#: A free-space reading a Host-A run would produce. Handed to the ACCEPTED guard, which compares
#: it against the accepted constant exactly as it always has.
HOST_A_FREE_BYTES = 400 * 1024**3


@pytest.fixture(autouse=True)
def _pinned_repository(tmp_path: Path) -> Any:
    """The shared pin: a real, clean throwaway repository, through the accepted identity seam.

    A consolidation derives the executing repository's identity for itself (D151-C3 §9), and the
    checkout this suite runs from is dirty by construction while a change is being written. The
    pin lives in ``test_d151_c1_chunk_plan`` so that every shared driver reads the same one --
    a per-module pin leaves a cross-module driver recording the wrong identity.
    """
    patcher = pytest.MonkeyPatch()
    c1.pin_repository(tmp_path / "repo", patcher)
    yield
    patcher.undo()
    c1.unpin_repository()


# ==========================================================================
# The accepted phase machinery, in a fresh process, once per phase
# ==========================================================================
#: Runs ONE accepted phase in this child process and prints what it produced.
#:
#: Every predicate the accepted machinery takes is taken here: the repository identity through
#: the accepted clean-repository predicate over the pinned repository, the work-root boundary
#: through the accepted primitive, admission against the predecessor's durable checkpoint, and
#: the accepted pre-F2 free-space gate. Only the two host capacity seams are applied.
_PHASE_PROGRAM = """
import json, os, shutil, sys
from collections import namedtuple
from pathlib import Path

sys.path.insert(0, {tests!r})

from disclosure_drift.m3 import repository_identity as ri
from disclosure_drift.m3 import single_source_canary as canary
from disclosure_drift.paths import DataTree
from disclosure_drift.storage.sqlite import utc_now

payload = json.loads(sys.argv[1])
repo = Path(payload["repository"])
# The accepted seam: WHICH repository is redirected, to a real one. Every predicate below --
# require_clean_running_repository included -- is the accepted one, unmodified.
ri.running_repository_identity = lambda: ri.repository_identity_at(repo)
canary.running_repository_identity = ri.running_repository_identity
repository = canary.require_clean_running_repository()

# The accepted Host-B capacity seam (Decisions 127 and 137): the MEASUREMENT is pinned, the
# accepted floors and comparisons are untouched.
Usage = namedtuple("Usage", "total used free")
if payload["free_bytes"] is not None:
    shutil.disk_usage = lambda _path: Usage(
        payload["free_bytes"] * 2, payload["free_bytes"], payload["free_bytes"]
    )

tree = DataTree.from_root(Path(payload["data_root"]))
work_root = canary.require_canary_work_root(Path(payload["work_root"]), tree=tree)
result = canary._run_phase_locked(
    phase=payload["phase"],
    operational_catalog=Path(payload["catalog"]),
    tree=tree,
    resolved_work_root=work_root,
    run_id=payload["run_id"],
    source_instance_id=payload["instance"],
    batch_size=payload["batch_size"],
    cache_bytes=None,
    external=None,
    started=utc_now(),
    repository=repository,
)
print("PHASE_RESULT " + json.dumps({{"pid": os.getpid(), "record": result.as_record()}}))
"""


def run_accepted_phase(
    *,
    phase: str,
    work_root: Path,
    database: Path,
    tree: DataTree,
    run_id: str,
    free_bytes: int | None = HOST_A_FREE_BYTES,
    check: bool = True,
) -> dict[str, Any]:
    """Run one accepted phase in a fresh process and return what it produced."""
    assert c1.PINNED is not None
    request = {
        "phase": phase,
        "work_root": str(work_root),
        "catalog": str(database),
        "data_root": str(tree.data_root),
        "run_id": run_id,
        "instance": c1.INSTANCE,
        "batch_size": BATCH,
        "repository": str(c1.PINNED_ROOT),
        "free_bytes": free_bytes,
    }
    completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed program, no shell
        [
            sys.executable,
            "-c",
            _PHASE_PROGRAM.format(tests=str(Path(__file__).parent)),
            json.dumps(request),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        message = f"phase {phase} failed:\n{completed.stderr[-4000:]}"
        raise AssertionError(message)
    if completed.returncode != 0:
        return {"failed": True, "stderr": completed.stderr}
    line = next(
        entry for entry in completed.stdout.splitlines() if entry.startswith("PHASE_RESULT ")
    )
    return json.loads(line[len("PHASE_RESULT ") :])


def consolidated_world(
    root: Path, database: Path, tree: DataTree, *, chunk_members: int, run_id: str
) -> cc.ConsolidationResult:
    """A chunked F0 consolidated INTO the accepted world layout: ``work_root/run_id``."""
    work_root = root / "work"
    work_root.mkdir(parents=True, exist_ok=True)
    run = c1x.run_chunked_f0(
        root,
        database,
        tree,
        chunk_members=chunk_members,
        label=f"chunked-{run_id}",
        batch_size=BATCH,
        repository=c1.PINNED,
    )
    return cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=work_root / run_id,
        run_id=run_id,
    )


def governed_outputs(world_directory: Path) -> dict[str, Any]:
    """Everything the accepted F2 leaves behind that a later stage would read."""
    from disclosure_drift.m3.working_catalog import WORKING_CATALOG_FILENAME
    from disclosure_drift.storage.sqlite import connect

    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        digests = dict(cc.world_logical_digest(connection))
        counts = dict(canary._counts(connection))
        relation = sorted(
            tuple(str(value) for value in row)
            for row in connection.execute(
                "SELECT accession_plain, registrant_cik_padded, association_class, "
                "evidence_level, parsed_record_id FROM census_accession_registrants"
            )
        )
    return {"tables": digests, "counts": counts, "relation": relation}


def _result_document(world_directory: Path) -> dict[str, Any]:
    document = json.loads((world_directory / "canary_result.json").read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


# ==========================================================================
# R14, R15, R16: the consolidated world through the accepted F1 and F2
# ==========================================================================
def test_r14_r15_r16_the_consolidated_world_runs_the_accepted_f1_and_f2_phase_paths(
    tmp_path: Path,
) -> None:
    """R14/R15/R16: chunked F0 -> accepted F1 -> accepted F2, against the monolithic reference.

    Both sides are driven through the **same** accepted phase machinery, so the comparison is
    between two F0s rather than between two harnesses. The chunked side's F0 is the consolidation;
    the monolithic side's F0 is the accepted ``f0`` phase. F1 and F2 are then byte-for-byte the
    same accepted code on both sides, in four fresh processes.
    """
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)

    # --- the monolithic reference, through the accepted machinery ------------------
    mono_root = tmp_path / "mono"
    mono_root.mkdir()
    (mono_root / "work").mkdir()
    mono_pids = [
        run_accepted_phase(
            phase=phase,
            work_root=mono_root / "work",
            database=database,
            tree=tree,
            run_id="mono-run",
        )["pid"]
        for phase in (PHASE_F0, PHASE_F1, PHASE_F2)
    ]
    mono_world = mono_root / "work" / "mono-run"

    # --- the chunked candidate ----------------------------------------------------
    chunk_root = tmp_path / "chunked"
    chunk_root.mkdir()
    result = consolidated_world(chunk_root, database, tree, chunk_members=1, run_id="chunked-run")
    assert result.receipt.status == "complete"
    # F0 is the consolidation, so only F1 and F2 are phases here.
    chunk_pids = [
        run_accepted_phase(
            phase=phase,
            work_root=chunk_root / "work",
            database=database,
            tree=tree,
            run_id="chunked-run",
        )["pid"]
        for phase in (PHASE_F1, PHASE_F2)
    ]

    # R16: the governed outputs are identical.
    assert governed_outputs(result.world_directory) == governed_outputs(mono_world)

    # And so is the run's own deliverable, field for field, excluding what is a property of
    # WHEN and WHERE rather than of what was found.
    volatile = {
        "completed_at_utc",
        "started_at_utc",
        "run_id",
        "working_catalog_sha256",
        "working_catalog_byte_length",
        "working_catalog_wal_byte_length",
        "operational_catalog_sha256_after",
        "work_root_free_bytes_before",
        "work_root_free_bytes_after",
        "capacity_observations",
    }
    candidate = _result_document(result.world_directory)
    reference = _result_document(mono_world)
    assert {k: v for k, v in candidate.items() if k not in volatile} == {
        k: v for k, v in reference.items() if k not in volatile
    }

    # Every phase really did run in a process that is not this one, and every one of them ended.
    every = [*mono_pids, *chunk_pids]
    assert len(set(every)) == len(every)
    assert os.getpid() not in every
    for pid in every:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


def test_r14_the_accepted_f1_admission_really_reads_the_derived_checkpoint(
    tmp_path: Path,
) -> None:
    """The derived F0 terminal is what admits F1 -- proved by removing it.

    A world whose durable F0 checkpoint has been deleted is refused by the accepted admission
    rule, and refused for the accepted reason. That is what makes the passing case above a proof
    that the derived checkpoint is load-bearing rather than incidental.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    root = tmp_path / "chunked"
    root.mkdir()
    result = consolidated_world(root, database, tree, chunk_members=2, run_id="admit-run")
    ledger_path = result.world_directory / PROGRESS_LEDGER_FILENAME
    ledger = RunProgressLedger(ledger_path)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is not None
    finally:
        ledger.close()
    # Remove the ONE row that holds the durable F0 terminal, and nothing else. The working
    # catalog, the sidecar, the working-catalog provenance and every committed row stay exactly
    # where they are, so the only thing that has gone is the checkpoint -- which is precisely the
    # state accepted Decision 145 refuses, and the reason its refusal names that and not
    # something earlier.
    with sqlite3.connect(ledger_path) as raw:
        deleted = raw.execute(
            "DELETE FROM run_working_catalog WHERE key LIKE ?", ("%f0%",)
        ).rowcount
        raw.commit()
    assert deleted == 1
    ledger = RunProgressLedger(ledger_path)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F0) is None
    finally:
        ledger.close()
    outcome = run_accepted_phase(
        phase=PHASE_F1,
        work_root=root / "work",
        database=database,
        tree=tree,
        run_id="admit-run",
        check=False,
    )
    assert outcome.get("failed")
    assert "no durable terminal checkpoint" in outcome["stderr"]


# ==========================================================================
# The 50-GiB guard is used, not weakened -- proved on any host
# ==========================================================================
def test_the_fifty_gib_guard_is_not_weakened(tmp_path: Path) -> None:
    """The accepted pre-F2 floor holds its accepted value, refuses below it, and admits at it.

    **D151-C5 MINOR-1.** The previous form of this proof removed the ``disk_usage`` seam and
    asserted that the physical host had less than 50 GiB free, so its negative half fired only
    on a capacity-ineligible host and FAILED outright on Host A. An authoritative unit test cannot
    depend on how much room the machine running it happens to have.

    Both halves now go through the accepted ``shutil.disk_usage`` seam -- the one Decisions 127
    and 137 already use, and the one every other phase in this module is driven through -- and
    the accepted guard does the comparing, unmodified, against the accepted constant:

    * at ``floor - 1`` bytes the accepted guard REFUSES F2 over a consolidated world, before its
      single transaction opens: no F2 terminal, no result document, F1's terminal untouched;
    * at exactly ``floor`` bytes -- the boundary of ``free < PRE_F2_MINIMUM_FREE_BYTES`` -- the
      same world, with every other predicate holding, is ADMITTED and F2 completes;
    * at ``floor + 1`` bytes a fresh world is admitted as well.

    The constant is asserted first and never touched. Nothing here reads the host's own free
    space, so the verdict is the same on Host A, on Host B, and in CI.
    """
    floor = canary.PRE_F2_MINIMUM_FREE_BYTES
    assert floor == 50 * 1024**3
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    root = tmp_path / "chunked"
    root.mkdir()
    consolidated_world(root, database, tree, chunk_members=2, run_id="floor-run")
    run_accepted_phase(
        phase=PHASE_F1,
        work_root=root / "work",
        database=database,
        tree=tree,
        run_id="floor-run",
    )
    world = root / "work" / "floor-run"

    # One byte below the floor, through the accepted seam: the accepted guard refuses, and the
    # reading it refused is the pinned one -- so the seam demonstrably reached the guard.
    refused = run_accepted_phase(
        phase=PHASE_F2,
        work_root=root / "work",
        database=database,
        tree=tree,
        run_id="floor-run",
        free_bytes=floor - 1,
        check=False,
    )
    assert refused.get("failed")
    assert "pre-F2 free-space admission failed" in refused["stderr"]
    assert f"{floor - 1} bytes free" in refused["stderr"]
    assert not (world / "canary_result.json").exists()
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F2) is None
        assert read_phase_checkpoint(ledger, PHASE_F1) is not None
    finally:
        ledger.close()

    # Exactly the floor: the boundary of the accepted comparison, and every other predicate
    # holds, so the same world is admitted and F2 reaches its terminal.
    admitted = run_accepted_phase(
        phase=PHASE_F2,
        work_root=root / "work",
        database=database,
        tree=tree,
        run_id="floor-run",
        free_bytes=floor,
    )
    assert admitted["record"]["phase"] == PHASE_F2
    assert admitted["record"]["result_document_written"] is True
    assert (world / "canary_result.json").exists()
    ledger = RunProgressLedger(world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, PHASE_F2) is not None
    finally:
        ledger.close()

    # One byte above the floor, on a fresh world: admitted as well.
    other = tmp_path / "chunked-plus-one"
    other.mkdir()
    consolidated_world(other, database, tree, chunk_members=2, run_id="floor-plus-one")
    run_accepted_phase(
        phase=PHASE_F1,
        work_root=other / "work",
        database=database,
        tree=tree,
        run_id="floor-plus-one",
    )
    plus_one = run_accepted_phase(
        phase=PHASE_F2,
        work_root=other / "work",
        database=database,
        tree=tree,
        run_id="floor-plus-one",
        free_bytes=floor + 1,
    )
    assert plus_one["record"]["result_document_written"] is True
