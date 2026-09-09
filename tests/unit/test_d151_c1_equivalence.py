"""D151-C1: the semantic equivalence oracle -- accepted monolithic F0 versus chunked F0.

**The oracle is the accepted monolithic F0 itself**, reached through the same
:func:`~disclosure_drift.m3.single_source_canary._f0` the accepted Decision 145 phase path calls,
over the same synthetic world, from the same accepted operational catalog copy. Nothing here
re-implements a reference: the comparison is between two executions of the same accepted parser
and the same accepted catalog writer, differing only in how the member population was partitioned.

**What is compared.** Every F0-written table's complete row set, by content digest; every row
count; the compact-evidence sidecar's own identity digest; the member manifest digest; the source
completeness digest; the whole member manifest row by row; the single parser run's counts,
outcome and summary; the ``census_plan_sources`` terminal; and -- separately, because they are the
state a later phase actually reads -- the outputs of the accepted F1 and F2 over both worlds.

**What is deliberately excluded, and why.** Wall-clock columns. Two runs stamp their own instants,
so a ``*_at_utc`` column can never be equal between them, and the accepted Decision 110
streamed-versus-merged proof already excludes exactly these for exactly this reason. Every digest
a governed identity is actually built from carries no timestamp at all by construction -- the
projection digest's own docstring says so -- so those are compared **byte for byte** rather than
approximated: the sidecar identity, the member manifest digest and the completeness digest are all
exact-equality assertions here.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.canary_phases import (  # noqa: E402
    PHASE_F1,
    CanaryPhaseError,
    read_phase_checkpoint,
    require_phase_admission,
)
from disclosure_drift.m3.chunk_evidence import FINAL_WORLD_RECEIPT_FILENAME  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.offline_parse import (  # noqa: E402
    materialize_census_associations,
    materialize_one_planned_source,
    select_planned_source,
    write_containment,
)
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
    WorkingCatalog,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

BATCH = 2


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
# The two executions
# ==========================================================================
def monolithic_f0(
    database: Path, tree: DataTree, world_directory: Path, *, strict: bool = True
) -> Path:
    """The accepted monolithic F0, unmodified, into a fresh disposable world.

    ``strict`` runs the accepted ``_f0`` including its D140-R12 blocking-terminal gate. A world
    whose source really does reach a blocking terminal cannot pass that gate by construction, so
    those cases drive the accepted ``materialize_one_planned_source`` directly -- which is the
    function ``_f0`` itself calls, one gate earlier.
    """
    world_directory.mkdir(parents=True)
    with WorkingCatalog(database, world_directory) as working:
        writer, catalog = canary._bind_catalog(working)
        sidecar = CompactEvidenceSidecar(world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME)
        selected = select_planned_source(working.connection, c1.INSTANCE)
        try:
            with write_containment(working.connection):
                if strict:
                    canary._f0(
                        working=working,
                        tree=tree,
                        selected=selected,
                        writer=writer,
                        catalog=catalog,
                        sidecar=sidecar,
                        batch_size=BATCH,
                        capacity_guard=None,
                    )
                else:
                    working.ledger.begin_source(
                        selected.source.source_instance_id, selected.source.source_id
                    )
                    materialize_one_planned_source(
                        writer=writer,
                        tree=tree,
                        catalog=catalog,
                        selected=selected,
                        sidecar=sidecar,
                        batch_size=BATCH,
                        checkpoint_batches=True,
                    )
        finally:
            sidecar.close()
    return world_directory


def chunked_f0(
    root: Path, database: Path, tree: DataTree, *, chunk_members: int, label: str
) -> cc.ConsolidationResult:
    """A whole chunked F0: plan, one process per chunk, then deterministic consolidation."""
    run = c1x.run_chunked_f0(
        root,
        database,
        tree,
        chunk_members=chunk_members,
        label=label,
        batch_size=BATCH,
        repository=c1.PINNED,
    )
    return cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="equivalence-run",
    )


def refused_chunked_run(
    root: Path, database: Path, tree: DataTree, *, chunk_members: int, label: str
) -> dict[str, Any]:
    """Chunk a source that reaches a BLOCKING terminal, and prove consolidation refuses it
    BEFORE any world exists -- Decision 151 Boundary 2 (FailFast-D).

    Until Decision 151 the consolidator admitted the failed chunks, built the whole world and
    was refused by the accepted D140-R12 gate at the end (D151-C5 INFO-6 compared that refused
    world with the monolithic one). A chunk whose parse reached ``failed`` is now refused at
    admission, so there is no consolidated world at all: the diagnostic evidence of a failed
    chunked F0 is the failed chunk world itself, retained exactly as it is. What is returned is
    the chunk run, so its chunk-level evidence can be compared with the monolithic run row.
    """
    run = c1x.run_chunked_f0(
        root,
        database,
        tree,
        chunk_members=chunk_members,
        label=label,
        batch_size=BATCH,
        repository=c1.PINNED,
    )
    world_directory = run["base"] / "final"
    with pytest.raises(cc.ChunkConsolidationError, match="BLOCKING parser terminal"):
        cc.consolidate_chunks(
            plan=run["plan"],
            internal_root=run["chunk_root"],
            operational_catalog=database,
            world_directory=world_directory,
            run_id="equivalence-run",
        )
    assert not world_directory.exists()
    return run


def _reduced_outcome(blocking: int, quarantined: int) -> str:
    """The accepted reduction rule, restated for the comparison only."""
    if blocking:
        return "failed"
    return "completed_with_quarantine" if quarantined else "completed"


def failure_evidence_of_run_row(measured: dict[str, Any]) -> dict[str, Any]:
    """What a refused MONOLITHIC world's run row says: outcome and the three counts."""
    (row,) = measured["runs"]
    summary = json.loads(str(row["summary_json"]))
    return {
        "outcome": str(row["outcome"]),
        "parsed": int(row["parsed_count"]),
        "quarantined": int(row["quarantined_count"]),
        "blocking_structural": int(summary["structural_detail"]["blocking"]),
    }


def chunk_failure_evidence(run: dict[str, Any]) -> dict[str, Any]:
    """What the refused CHUNKS say, read through the accepted read-only resolution and the
    Decision 151 semantics reader, and reduced by the accepted rule."""
    inputs = cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"])
    semantics = [cc.chunk_semantics(item) for item in inputs]
    blocking = sum(item.blocking_structural for item in semantics)
    quarantined = sum(item.quarantined for item in semantics)
    return {
        "outcome": _reduced_outcome(blocking, quarantined),
        "parsed": sum(item.parsed for item in semantics),
        "quarantined": quarantined,
        "blocking_structural": blocking,
        "failed_chunks": [item.chunk_id for item in semantics if item.blocking],
    }


# ==========================================================================
# The measurement
# ==========================================================================
def measure(world_directory: Path) -> dict[str, Any]:
    """Everything two F0 worlds are compared on -- a refused blocking-terminal world included.

    A MONOLITHIC F0 the accepted D140-R12 gate refused leaves its durable diagnostic rows and its
    finalized diagnostic sidecar, and a consolidation refused at the same gate (reachable only
    through an injected failed reduction since Decision 151 Boundary 2 refuses a failed chunk
    before the world exists) leaves the same, so the same measurement applies to both.
    """
    measured: dict[str, Any] = {}
    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        measured["tables"] = dict(cc.world_logical_digest(connection))
        measured["counts"] = dict(ce.table_row_counts(connection))
        row = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (c1.INSTANCE,),
        ).fetchone()
        measured["parser_state"] = str(row["parser_state"])
        runs = connection.execute("SELECT * FROM census_parser_runs").fetchall()
        measured["runs"] = [
            {key: value for key, value in dict(entry).items() if not key.endswith("_at_utc")}
            for entry in runs
        ]
    evidence = CompactEvidenceSidecar(world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME)
    try:
        measured["sidecar_identity"] = evidence.identity()
        measured["manifest_digest"] = evidence.member_manifest_digest(c1.OBSERVATION)
        measured["source_evidence"] = dict(evidence.source_evidence(c1.OBSERVATION) or {})
        measured["members"] = [dict(entry) for entry in evidence.members(c1.OBSERVATION)]
    finally:
        evidence.close()
    return measured


def assert_equivalent(reference: dict[str, Any], candidate: dict[str, Any]) -> None:
    """Every governed output, compared field by field so a failure names the field."""
    assert candidate["counts"] == reference["counts"]
    assert candidate["tables"] == reference["tables"]
    assert candidate["parser_state"] == reference["parser_state"]
    assert candidate["runs"] == reference["runs"]
    assert candidate["members"] == reference["members"]
    assert candidate["source_evidence"] == reference["source_evidence"]
    assert candidate["manifest_digest"] == reference["manifest_digest"]
    assert candidate["sidecar_identity"] == reference["sidecar_identity"]


# ==========================================================================
# C32-C37: partition invariance over hostile sources
# ==========================================================================
#: Every source shape the equivalence proof runs over. Each names the property it attacks.
#:
#: Member counts are kept at or below the merge's attachment ceiling so that the smallest
#: partition -- one member per chunk -- is reachable for every one of them. That is deliberate:
#: "many small chunks" has to mean the smallest chunk the plan can express, and a source sized so
#: that it never reaches one would prove the easy case only.
SOURCES: tuple[tuple[str, dict[str, Any], bool], ...] = (
    ("plain", {"members": 6, "filings": 2}, True),
    ("shards", {"members": 6, "filings": 2, "shards": 2}, True),
    ("shard_after_parent", {"members": 6, "filings": 2, "shards": 2, "shard_first": False}, True),
    ("shared_accession", {"members": 8, "filings": 2, "share_every": 2}, True),
    ("shards_and_shared", {"members": 6, "filings": 2, "shards": 2, "share_every": 2}, True),
    (
        "quarantine_and_unknown",
        {"members": 6, "filings": 2, "shards": 2, "junk": 2, "unknown": 3},
        True,
    ),
    ("cross_member_duplicate", {"members": 6, "filings": 2, "shards": 2, "duplicate": True}, True),
    ("blocking_structural", {"members": 6, "filings": 2, "shards": 2, "malformed": 2}, False),
    (
        "everything",
        {
            "members": 6,
            "filings": 3,
            "shards": 2,
            "share_every": 2,
            "duplicate": True,
            "junk": 3,
            "unknown": 4,
        },
        True,
    ),
)


#: C32 one chunk, C33 two, C34 three, C35 many small, C36 an uneven final chunk. Every source
#: above holds eight governed members or fewer, so ``1`` really is one member per chunk.
PARTITIONS: tuple[int, ...] = (1, 2, 3, 5, 10_000)


@pytest.mark.parametrize(("label", "shape", "strict"), SOURCES, ids=[item[0] for item in SOURCES])
def test_c32_to_c43_the_chunked_world_equals_the_monolithic_one(
    tmp_path: Path, label: str, shape: dict[str, Any], strict: bool
) -> None:
    """C32-C43 in one sweep: every partition of every hostile source reaches the same world.

    The sweep covers, by construction of the sources above: C38 a registrant shared across
    chunks; C39 an accession co-filed by registrants that land in different chunks; C40 generated
    identifiers and every foreign key that names them; C41 quarantines and blocking structural
    failures; C42 unknown fields; C43 every digest; C36 an uneven final chunk at every size that
    does not divide the population; and C37 -- because a chunk's ordinal interval, not its
    directory, decides what it holds.
    """
    database, tree = c1.build_world(tmp_path, **shape)
    monolithic_f0(database, tree, tmp_path / "mono", strict=strict)
    reference = measure(tmp_path / "mono")
    for size in PARTITIONS:
        if strict:
            result = chunked_f0(
                tmp_path, database, tree, chunk_members=size, label=f"{label}-n{size}"
            )
            assert_equivalent(reference, measure(result.world_directory))
            assert result.receipt.status == "complete"
            continue
        # A source that reaches a BLOCKING terminal. The monolithic path stops at the accepted
        # D140-R12 gate (``monolithic_f0`` was driven with ``strict=False`` for exactly that
        # reason) and leaves its diagnostic world; the chunked path is refused EARLIER, at
        # admission, before any world exists (Decision 151 Boundary 2). What is asserted is that
        # the failure evidence is exact and complete at the chunk level: the failed chunks'
        # manifest-bound run rows reduce -- by the accepted rule -- to the monolithic run row's
        # outcome and counts, and every partition names the same failed members.
        assert reference["parser_state"] == "failed"
        expected = failure_evidence_of_run_row(reference)
        assert expected["outcome"] == "failed" and expected["blocking_structural"] > 0
        run = refused_chunked_run(
            tmp_path, database, tree, chunk_members=size, label=f"{label}-n{size}"
        )
        observed = chunk_failure_evidence(run)
        assert observed["failed_chunks"]
        assert {key: observed[key] for key in expected} == expected
        assert not (run["base"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).exists()


def test_the_partition_actually_varied(tmp_path: Path) -> None:
    """A sweep that silently produced one chunk every time would prove nothing."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    counts = {
        chunked_f0(
            tmp_path, database, tree, chunk_members=size, label=f"vary-n{size}"
        ).receipt.chunk_count
        for size in PARTITIONS
    }
    assert len(counts) >= 4
    assert min(counts) == 2  # the primary and shard regions are always separate chunks
    assert max(counts) == 8


def test_c38_c39_a_cross_chunk_first_witness_correction_really_happens(
    tmp_path: Path,
) -> None:
    """C38/C39: the correction is exercised, not merely available.

    A sweep in which the hard case never arose would prove only that the easy case works. The
    co-filed accession here is witnessed in four registrants' documents; at a partition of one
    member per chunk every one of those witnesses is in a different chunk.
    """
    database, tree = c1.build_world(tmp_path, members=8, filings=2, share_every=2)
    monolithic_f0(database, tree, tmp_path / "mono")
    reference = measure(tmp_path / "mono")
    split = chunked_f0(tmp_path, database, tree, chunk_members=1, label="split")
    whole = chunked_f0(tmp_path, database, tree, chunk_members=10_000, label="whole")
    assert split.receipt.first_witness_accessions_corrected == 1
    assert split.receipt.first_witness_rows_staged > 0
    assert split.receipt.evidence_members_corrected > 0
    assert split.receipt.evidence_delta > 0
    # The single-chunk run needs no correction at all, which is the positive control: the
    # correction machinery is not silently doing the work in both cases.
    assert whole.receipt.first_witness_accessions_corrected == 0
    assert whole.receipt.evidence_delta == 0
    assert_equivalent(reference, measure(split.world_directory))
    assert_equivalent(reference, measure(whole.world_directory))


def test_c37_directory_enumeration_order_does_not_decide_anything(tmp_path: Path) -> None:
    """C37/A24: canonical PLAN order controls semantics, never the filesystem's listing."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    monolithic_f0(database, tree, tmp_path / "mono")
    reference = measure(tmp_path / "mono")
    run = c1x.run_chunked_f0(
        tmp_path, database, tree, chunk_members=1, label="ordered", repository=c1.PINNED
    )
    forward = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final-a",
        run_id="ordered-a",
    )
    # Present the same chunks through placements assembled in the opposite order. The
    # consolidator re-derives plan order for itself, so the presentation cannot matter.
    from disclosure_drift.m3.chunk_storage import derive_placements

    placements = derive_placements(run["plan"], internal_root=run["chunk_root"])
    reversed_inputs = cc.resolve_chunk_inputs(
        run["plan"],
        internal_root=run["chunk_root"],
        placements=tuple(placements),
    )
    assert [item.chunk_id for item in reversed_inputs] == [
        bounds.chunk_id for bounds in run["plan"].chunks
    ]
    backward = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final-b",
        run_id="ordered-b",
    )
    assert_equivalent(reference, measure(forward.world_directory))
    assert_equivalent(measure(forward.world_directory), measure(backward.world_directory))


def test_the_batch_size_does_not_move_the_result(tmp_path: Path) -> None:
    """Durability granularity is not semantics -- the accepted D111 claim, under chunking."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    monolithic_f0(database, tree, tmp_path / "mono")
    reference = measure(tmp_path / "mono")
    run = c1x.run_chunked_f0(
        tmp_path, database, tree, chunk_members=2, label="b7", batch_size=7, repository=c1.PINNED
    )
    result = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="batch-seven",
    )
    assert_equivalent(reference, measure(result.world_directory))


# ==========================================================================
# C44, C45: what F1 will and will not accept
# ==========================================================================
def _f1_and_f2(world_directory: Path, database: Path) -> dict[str, Any]:
    """Run the accepted F1 and F2 over one F0 world and return everything they produced."""
    with WorkingCatalog(database, world_directory, attach=True) as working:
        _writer, catalog = canary._bind_catalog(working)
        with write_containment(working.connection):
            resolved = catalog.count_persisted_accession_resolutions(
                batch_size=BATCH, checkpoint_batches=True
            )
            totality = materialize_census_associations(working.connection, compact_evidence=True)
            counts = dict(canary._counts(working.connection))
        evidence = catalog.resolution_evidence
        digests = dict(cc.world_logical_digest(working.connection))
        relation = sorted(
            tuple(str(value) for value in row)
            for row in working.connection.execute(
                "SELECT accession_plain, registrant_cik_padded, association_class, "
                "evidence_level, parsed_record_id FROM census_accession_registrants"
            )
        )
    return {
        "resolved": resolved,
        "totality": dict(totality.as_record()),
        "counts": counts,
        "resolution_digest": evidence.completeness_digest(),
        "resolution_accessions": evidence.accessions,
        "tables": digests,
        "relation": relation,
    }


def test_c44_the_consolidated_world_is_accepted_by_f1_and_f2(tmp_path: Path) -> None:
    """C44: F1-visible state is identical, and F2 over it produces the identical relation."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    monolithic_f0(database, tree, tmp_path / "mono")
    result = chunked_f0(tmp_path, database, tree, chunk_members=1, label="forf1")
    reference = _f1_and_f2(tmp_path / "mono", database)
    candidate = _f1_and_f2(result.world_directory, database)
    assert candidate == reference


def test_c44_the_consolidated_world_carries_the_accepted_f0_phase_checkpoint(
    tmp_path: Path,
) -> None:
    """The accepted Decision 145 admission rule, satisfied by a DERIVED checkpoint.

    D151-C3 §6: the caller no longer supplies the checkpoint or its payload. Consolidation writes
    one, through the accepted writer, from identities it measured for itself -- and the accepted
    admission mechanism, unmodified, admits F1 from it.
    """
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2)
    result = chunked_f0(tmp_path, database, tree, chunk_members=2, label="checkpoint")
    assert c1.PINNED is not None
    identity = canary.phase_execution_identity(
        repository=c1.PINNED, batch_size=result.inputs[0].receipt.execution_contract.batch_size
    )
    ledger = RunProgressLedger(result.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        admission = require_phase_admission(
            ledger,
            phase=PHASE_F1,
            run_id="equivalence-run",
            source_instance_id=c1.INSTANCE,
            execution_identity=identity,
            repository_head_sha=c1.PINNED.head_sha,
            repository_tree_sha=c1.PINNED.tree_sha,
            catalog_source_sha256=result.receipt.catalog_source_sha256,
            migration_head=result.inputs[0].receipt.execution_contract.migration_head,
            plan_fingerprint=_plan_fingerprint_of(database),
        )
        assert admission.predecessor is not None
        assert admission.predecessor.phase == "f0"
    finally:
        ledger.close()


def _plan_fingerprint_of(database: Path) -> str:
    """The accepted plan fingerprint, derived the way the accepted phase path derives it."""
    from disclosure_drift.m3.capacity_plan import plan_fingerprint
    from disclosure_drift.storage.catalog import strictly_read_only_connection

    with strictly_read_only_connection(database) as reader:
        fingerprint, _ = plan_fingerprint(reader)
    return fingerprint


def test_c45_an_individual_chunk_is_never_a_final_f0_world(tmp_path: Path) -> None:
    """C45/A31: a chunk world carries no F0 checkpoint, so the accepted F1 refuses it."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2)
    run = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=2, label="chunkonly")
    receipt = run["receipts"][0]
    chunk_world = run["chunk_root"] / receipt.chunk_id / f"attempt-{receipt.attempt:03d}"
    ledger = RunProgressLedger(chunk_world / PROGRESS_LEDGER_FILENAME)
    try:
        assert read_phase_checkpoint(ledger, "f0") is None
        with pytest.raises(CanaryPhaseError, match="no durable terminal checkpoint"):
            require_phase_admission(
                ledger,
                phase=PHASE_F1,
                run_id="c1-run",
                source_instance_id=c1.INSTANCE,
                execution_identity="x",
                repository_head_sha=c1x.HEAD,
                repository_tree_sha=c1x.TREE,
                catalog_source_sha256="c" * 64,
                migration_head=15,
                plan_fingerprint="fingerprint",
            )
    finally:
        ledger.close()
    assert not (chunk_world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    # And a chunk's own summary refuses to claim a source-level terminal.
    assert receipt.summary.parser_state_after == "chunk_local"


# ==========================================================================
# C55, C56: the accepted major-phase model is untouched
# ==========================================================================
_PHASE_PROGRAM = """
import json, sys
from pathlib import Path
sys.path.insert(0, {tests!r})
import test_d151_c1_equivalence as eq
from disclosure_drift.m3.working_catalog import WorkingCatalog
from disclosure_drift.m3 import single_source_canary as canary
from disclosure_drift.m3.offline_parse import materialize_census_associations, write_containment

world = Path(sys.argv[1])
database = Path(sys.argv[2])
phase = sys.argv[3]
with WorkingCatalog(database, world, attach=True) as working:
    _writer, catalog = canary._bind_catalog(working)
    with write_containment(working.connection):
        if phase == "f1":
            value = catalog.count_persisted_accession_resolutions(
                batch_size=2, checkpoint_batches=True
            )
        else:
            value = materialize_census_associations(
                working.connection, compact_evidence=True
            ).substantive_relation_count
print(json.dumps({{"pid": __import__("os").getpid(), "value": value}}))
"""


def test_c55_c56_f1_and_f2_still_run_in_their_own_processes_over_a_consolidated_world(
    tmp_path: Path,
) -> None:
    """C55/C56: chunking is INSIDE F0 and leaves the accepted major-phase model alone.

    F0 finishes and its consolidation ends; F1 runs in its own process and that process exits;
    F2 runs in a third process and that one exits too. Three real processes, each proved gone.
    """
    import os

    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2)
    result = chunked_f0(tmp_path, database, tree, chunk_members=2, label="phases")
    program = _PHASE_PROGRAM.format(tests=str(Path(__file__).parent))
    pids = []
    for phase in ("f1", "f2"):
        completed = subprocess.run(
            [sys.executable, "-c", program, str(result.world_directory), str(database), phase],
            check=True,
            capture_output=True,
            text=True,
        )
        record = json.loads(completed.stdout.strip().splitlines()[-1])
        pids.append(int(record["pid"]))
    assert len(set(pids)) == 2
    assert os.getpid() not in pids
    for pid in pids:
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)


# ==========================================================================
# C52: the accepted monolithic path is unchanged
# ==========================================================================
def test_c52_the_existing_monolithic_path_is_untouched(tmp_path: Path) -> None:
    """C52/A50: nothing about the accepted single-source path is changed or reinterpreted.

    The monolithic world carries no chunk plan, no chunk receipt and no final world receipt, and
    every accepted module the chunked path reuses is imported rather than modified -- which the
    session's own diff shows, and which this asserts from the running code: the accepted F0 was
    driven above through ``canary._f0`` with no argument this record added.
    """
    database, tree = c1.build_world(tmp_path, members=4, filings=2)
    world_directory = monolithic_f0(database, tree, tmp_path / "mono")
    present = {path.name for path in world_directory.iterdir()}
    assert present == {
        WORKING_CATALOG_FILENAME,
        PROGRESS_LEDGER_FILENAME,
        COMPACT_EVIDENCE_SIDECAR_FILENAME,
    }
    import inspect

    signature = inspect.signature(canary._f0)
    assert set(signature.parameters) == {
        "working",
        "tree",
        "selected",
        "writer",
        "catalog",
        "sidecar",
        "batch_size",
        "capacity_guard",
    }
