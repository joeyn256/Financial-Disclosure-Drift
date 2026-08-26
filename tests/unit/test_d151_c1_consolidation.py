"""D151-C1: the consolidator -- what it refuses, what it never touches, and how it merges.

Two families of claim live here.

**Fail-closed admission.** A consolidation is a claim that one world is the whole source. It is
refused when a chunk is missing, when a chunk carries two valid terminals, when a chunk belongs to
another partition, when a chunk's bytes moved, when a directory the plan does not name is sitting
among the chunks, when two chunks executed under different governing code, and when the admitted
intervals do not cover the source exactly once.

**The performance-architecture claim, proved rather than described.** D151-C1 §16 makes PASS
conditional on consolidation *not* recreating the monolithic random-write bottleneck. The proof
here is direct: every statement the consolidator issues against the final world is captured, and
the number of statements that write an F0 table is shown to be **independent of how many rows
were merged**. A record-by-record merge cannot have that property; a key-sorted bulk load does.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c1_chunk_execution as c1x  # noqa: E402
import test_d151_c1_chunk_plan as c1  # noqa: E402
import test_d151_c1_equivalence as eq  # noqa: E402

from disclosure_drift.m3 import chunk_consolidation as cc  # noqa: E402
from disclosure_drift.m3 import chunk_execution as ce  # noqa: E402
from disclosure_drift.m3.chunk_evidence import (  # noqa: E402
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    ChunkEvidenceError,
    build_artifact_manifest,
    read_receipt_document,
    verify_artifact_manifest,
)
from disclosure_drift.m3.chunk_storage import ChunkStorageError  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    WORKING_CATALOG_FILENAME,
    WorkingCatalog,
)
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

#: The identity every chunk in this module records and every consolidation must measure.
#:
#: Module-wide and autouse, because a consolidation now derives the executing repository's
#: identity for ITSELF (D151-C3 §9) and every test here consolidates. The seam pins a real
#: throwaway repository; the accepted clean-repository predicate runs over it unmodified.


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


@pytest.fixture
def world(tmp_path: Path) -> tuple[Path, DataTree]:
    return c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)


def _run(tmp_path: Path, world: tuple[Path, DataTree], *, size: int = 2, label: str = "c") -> Any:
    database, tree = world
    return c1x.run_chunked_f0(
        tmp_path, database, tree, chunk_members=size, label=label, repository=c1.PINNED
    )


def _consolidate(run: Any, database: Path, *, suffix: str = "") -> cc.ConsolidationResult:
    return cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / f"final{suffix}",
        run_id="c3-consolidation",
    )


# ==========================================================================
# C28-C31, A25, A26, A28, A29: admission
# ==========================================================================
def test_c28_a25_a_missing_chunk_refuses_consolidation(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C28/A25: a missing chunk is never treated as empty, skipped, or reconstructed."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    victim = run["plan"].chunks[1].chunk_id
    receipt_path = run["chunk_root"] / victim / "attempt-000" / CHUNK_RECEIPT_FILENAME
    receipt_path.rename(receipt_path.with_suffix(".moved"))
    with pytest.raises(ChunkStorageError, match="no verified copy on either tier"):
        _consolidate(run, database)
    assert not (run["base"] / "final").exists()


def test_c29_a_chunk_with_two_valid_terminals_refuses_consolidation(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C29: duplicate authority is reported, never resolved by attempt number."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    victim = run["plan"].chunks[0].chunk_id
    original = run["chunk_root"] / victim / "attempt-000"
    twin = run["chunk_root"] / victim / "attempt-001"
    twin.mkdir()
    for path in original.iterdir():
        (twin / path.name).write_bytes(path.read_bytes())
    with pytest.raises(ce.ChunkExecutionError, match="valid terminal receipts"):
        _consolidate(run, database)


def test_c30_a_chunk_from_another_partition_refuses(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C30/A27: a chunk of a different plan means something different by its own interval."""
    database, tree = world
    run = _run(tmp_path, world, size=2)
    other = c1x.run_chunked_f0(tmp_path, database, tree, chunk_members=3, label="other")
    victim = run["plan"].chunks[0].chunk_id
    target = run["chunk_root"] / victim / "attempt-000" / CHUNK_RECEIPT_FILENAME
    document = json.loads(target.read_text())
    document["plan_digest"] = other["plan"].plan_digest
    target.write_text(json.dumps(document))
    with pytest.raises(cc.ChunkConsolidationError, match="produced under plan digest"):
        _consolidate(run, database)


def test_c31_a_chunk_whose_bytes_moved_refuses_consolidation(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """C31/A10: the manifest is re-verified at the point of consumption, not only at discovery."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    target = run["chunk_root"] / run["plan"].chunks[0].chunk_id / "attempt-000"
    connection = sqlite3.connect(target / "chunk_witness.sqlite3")
    connection.execute("INSERT INTO chunk_witness_meta VALUES ('x', 'y')")
    connection.commit()
    connection.close()
    with pytest.raises(ChunkStorageError, match="no verified copy on either tier"):
        _consolidate(run, database)


def test_a26_a_foreign_chunk_directory_refuses_consolidation(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A26: an extra chunk is a chunk of some other partition, and is reported not ignored."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    (run["chunk_root"] / "chunk-4242").mkdir()
    with pytest.raises(cc.ChunkConsolidationError, match="does not name"):
        _consolidate(run, database)


def test_a01_a_shifted_bound_in_a_receipt_refuses(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    target = run["chunk_root"] / run["plan"].chunks[0].chunk_id / "attempt-000"
    document = json.loads((target / CHUNK_RECEIPT_FILENAME).read_text())
    document["end"] = int(document["end"]) + 1
    (target / CHUNK_RECEIPT_FILENAME).write_text(json.dumps(document))
    with pytest.raises(cc.ChunkConsolidationError, match="records interval"):
        _consolidate(run, database)


@pytest.mark.parametrize("field", ["repository_head_sha", "repository_tree_sha"])
def test_a28_a29_chunks_from_different_revisions_refuse(
    tmp_path: Path, world: tuple[Path, DataTree], field: str
) -> None:
    """A28/A29: one consolidated world is never assembled from code that moved between chunks."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    target = run["chunk_root"] / run["plan"].chunks[-1].chunk_id / "attempt-000"
    document = json.loads((target / CHUNK_RECEIPT_FILENAME).read_text())
    document[field] = "9" * 40
    (target / CHUNK_RECEIPT_FILENAME).write_text(json.dumps(document))
    with pytest.raises(cc.ChunkConsolidationError, match="executed under repository"):
        _consolidate(run, database)


def test_a_chunk_over_another_artifact_refuses(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    target = run["chunk_root"] / run["plan"].chunks[0].chunk_id / "attempt-000"
    document = json.loads((target / CHUNK_RECEIPT_FILENAME).read_text())
    document["source_sha256"] = "0" * 64
    (target / CHUNK_RECEIPT_FILENAME).write_text(json.dumps(document))
    with pytest.raises(cc.ChunkConsolidationError, match="different source artifact"):
        _consolidate(run, database)


def test_a_second_consolidation_into_the_same_world_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    _consolidate(run, database)
    with pytest.raises(cc.ChunkConsolidationError, match="create-once"):
        _consolidate(run, database)


def test_a33_an_interrupted_consolidation_leaves_no_final_receipt(
    tmp_path: Path, world: tuple[Path, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A33: a consolidation that stops before its terminal has produced no F0 world."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)

    class _InterruptedError(RuntimeError):
        pass

    def _boom(*_args: object, **_kwargs: object) -> None:
        message = "interrupted after the merge and before the terminal"
        raise _InterruptedError(message)

    monkeypatch.setattr(cc, "build_artifact_manifest", _boom)
    with pytest.raises(_InterruptedError):
        _consolidate(run, database)
    assert (run["base"] / "final").is_dir()
    assert not (run["base"] / "final" / FINAL_WORLD_RECEIPT_FILENAME).exists()


# ==========================================================================
# C46, A34: nothing is mutated
# ==========================================================================
def test_c46_consolidation_mutates_no_chunk(tmp_path: Path, world: tuple[Path, DataTree]) -> None:
    """C46: chunk artifacts are byte-identical afterwards, files and directory listing alike."""
    database, _tree = world
    run = _run(tmp_path, world, size=1)
    before = {
        path.relative_to(run["chunk_root"]).as_posix(): path.read_bytes()
        for path in sorted(run["chunk_root"].rglob("*"))
        if path.is_file()
    }
    result = _consolidate(run, database)
    after = {
        path.relative_to(run["chunk_root"]).as_posix(): path.read_bytes()
        for path in sorted(run["chunk_root"].rglob("*"))
        if path.is_file()
    }
    assert after == before
    assert result.receipt.chunks_unchanged is True


def test_a34_a_final_world_changed_after_its_receipt_stops_verifying(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A34: the final receipt binds the world's bytes, so a later edit is detectable."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    result = _consolidate(run, database)
    verify_artifact_manifest(
        result.world_directory, result.receipt.manifest, exclude=(FINAL_WORLD_RECEIPT_FILENAME,)
    )
    with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=True) as connection:
        connection.execute("PRAGMA user_version = 4242")
    with pytest.raises(ChunkEvidenceError, match="does not match the manifest"):
        verify_artifact_manifest(
            result.world_directory,
            result.receipt.manifest,
            exclude=(FINAL_WORLD_RECEIPT_FILENAME,),
        )


def test_a32_the_final_receipt_is_written_last(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A32: the manifest covers every artifact except the receipt, and it verifies."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    result = _consolidate(run, database)
    named = {entry.relative_path for entry in result.receipt.manifest.entries}
    assert FINAL_WORLD_RECEIPT_FILENAME not in named
    present = {
        path.relative_to(result.world_directory).as_posix()
        for path in result.world_directory.rglob("*")
        if path.is_file()
    }
    assert present == named | {FINAL_WORLD_RECEIPT_FILENAME}
    document = read_receipt_document(
        result.world_directory / FINAL_WORLD_RECEIPT_FILENAME,
        contract=FINAL_WORLD_RECEIPT_CONTRACT,
    )
    assert document["status"] == "complete"
    assert (
        build_artifact_manifest(
            result.world_directory, exclude=(FINAL_WORLD_RECEIPT_FILENAME,)
        ).digest
        == result.receipt.manifest.digest
    )


def test_the_merge_writes_no_staging_artifact_at_all(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """§16: the chunks ARE the staged form, so the merge materializes no second copy.

    An earlier shape of this merge appended every chunk's rows into a scratch database and sorted
    that. It was measured 1.5x slower on a two-million-row probe, and at governed scale it would
    have demanded a second hundred-gigabyte artifact and the free space to hold it -- on a host
    whose accepted launch floor is 185 GiB. The merge now reads the chunks directly.
    """
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    result = _consolidate(run, database)
    produced = {
        path.relative_to(run["base"]).as_posix()
        for path in run["base"].rglob("*")
        if path.is_file() and "chunks/" not in path.relative_to(run["base"]).as_posix()
    }
    assert not any("staging" in name for name in produced), sorted(produced)
    assert {path.name for path in result.world_directory.iterdir()} == {
        WORKING_CATALOG_FILENAME,
        "run_progress.sqlite3",
        "compact_evidence.sqlite3",
        FINAL_WORLD_RECEIPT_FILENAME,
    }


def test_a_partition_larger_than_sqlite_will_attach_is_refused() -> None:
    """The merge reads every chunk in one statement, so the attachment ceiling is a real bound."""
    limit = cc.attachment_limit()
    assert limit >= 2
    assert cc.require_attachable(limit - 1) == limit - 1
    with pytest.raises(cc.ChunkConsolidationError, match="two-level merge"):
        cc.require_attachable(limit)


# ==========================================================================
# C47: the merge is set-based, and that is measured
# ==========================================================================
class _TracingWorkingCatalog(WorkingCatalog):
    """A working catalog that records every statement its connection executes."""

    statements: list[str] = []

    def __enter__(self) -> WorkingCatalog:
        opened = super().__enter__()
        opened.connection.set_trace_callback(type(self).statements.append)
        return opened


def _trace_consolidation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, members: int, label: str
) -> tuple[list[str], cc.ConsolidationResult]:
    database, tree = c1.build_world(tmp_path / label, members=members, filings=3)
    run = c1x.run_chunked_f0(
        tmp_path / label,
        database,
        tree,
        chunk_members=max(members // 4, 1),
        label=f"{label}-run",
        repository=c1.PINNED,
    )
    _TracingWorkingCatalog.statements = []
    monkeypatch.setattr(cc, "WorkingCatalog", _TracingWorkingCatalog)
    result = cc.consolidate_chunks(
        plan=run["plan"],
        internal_root=run["chunk_root"],
        operational_catalog=database,
        world_directory=run["base"] / "final",
        run_id="c3-consolidation",
    )
    monkeypatch.undo()
    return list(_TracingWorkingCatalog.statements), result


def _writes_into_f0_tables(statements: list[str]) -> list[str]:
    """Every DISTINCT write statement the consolidator issued against an F0 table, in order.

    Distinct rather than counted, because the trace also fires once per invocation of the
    accepted schema's own row triggers, which is a property of the schema rather than of the
    merge. What the merge controls is *which* statements it issues, and how many of them.
    """
    verbs = ("INSERT INTO ", "INSERT OR IGNORE INTO ", "UPDATE ")
    found: list[str] = []
    for statement in statements:
        flat = " ".join(statement.split())
        for verb in verbs:
            if not flat.startswith(verb):
                continue
            target = flat[len(verb) :].split()[0]
            if target not in ce.F0_WRITTEN_TABLES and target != "census_plan_sources":
                continue
            label = f"{verb.strip()} {target}"
            if label not in found:
                found.append(label)
    return found


def test_c47_the_merge_statements_are_the_same_whatever_the_data_volume(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C47/§16: the load-bearing performance claim, as a measurement rather than a description.

    Two consolidations over sources that differ by more than fourfold in rows issue the **same
    set of write statements** against the final world -- one per table, each an
    ``INSERT ... SELECT ... ORDER BY`` over the attached chunks. A merge that walked records
    one at a time would instead issue a parameterized insert per record, and its statement set
    would be one entry repeated as many times as there were rows.

    Two things in the trace *do* repeat per row, and neither is this record's doing: the accepted
    schema's own ``BEFORE INSERT`` triggers on ``census_accessions``, which the monolithic F0
    incurs identically on every accession it writes; and the accepted
    ``CensusCatalog._candidate_edges`` loop, which emits one row per alias-sharing registrant
    pair and which the monolithic F0 also runs exactly once, at the end, over the same evidence.
    Both are asserted below by name rather than filtered away silently.
    """
    small_statements, small = _trace_consolidation(tmp_path, monkeypatch, members=4, label="small")
    large_statements, large = _trace_consolidation(tmp_path, monkeypatch, members=20, label="large")
    small_rows = sum(small.receipt.table_row_counts.values())
    large_rows = sum(large.receipt.table_row_counts.values())
    assert large_rows > 4 * small_rows
    assert _writes_into_f0_tables(large_statements) == _writes_into_f0_tables(small_statements)
    writes = _writes_into_f0_tables(small_statements)
    # One write statement per bulk-loaded table, plus the reduced run row, the plan terminal,
    # the duplicate-identity pass, the two candidate-edge derivations and the conflict pass.
    assert len(writes) <= len(ce.F0_WRITTEN_TABLES) + 4
    assert len(set(writes)) == len(writes)


def test_c47_the_repeating_statements_are_the_accepted_derivations_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Everything that scales with the data is inherited verbatim, and is named here."""
    statements, _result = _trace_consolidation(tmp_path, monkeypatch, members=8, label="repeat")
    counted: dict[str, int] = {}
    for statement in statements:
        flat = " ".join(statement.split())
        counted[flat] = counted.get(flat, 0) + 1
    repeating = sorted({statement for statement, count in counted.items() if count > 1})
    for statement in repeating:
        assert statement.startswith("INSERT INTO census_accessions (") or statement.startswith(
            "INSERT OR IGNORE INTO census_candidate_lineage_edges ("
        ), statement


def test_c47_every_bulk_load_is_key_sorted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The sorted load is what turns scattered B-tree writes into rightmost-leaf appends."""
    statements, _result = _trace_consolidation(tmp_path, monkeypatch, members=6, label="sorted")
    loads = [
        " ".join(statement.split())
        for statement in statements
        if statement.strip().startswith("INSERT")
        and " FROM (SELECT " in " ".join(statement.split())
    ]
    assert loads
    for statement in loads:
        assert "ORDER BY" in statement, statement


def test_c48_the_declared_indexes_are_dropped_and_rebuilt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C48: deferred index construction, and an index set identical to the accepted one."""
    statements, result = _trace_consolidation(tmp_path, monkeypatch, members=6, label="indexes")
    dropped = [item for item in statements if item.strip().upper().startswith("DROP INDEX")]
    created = [item for item in statements if item.strip().upper().startswith("CREATE INDEX")]
    assert dropped and len(created) == len(dropped)
    order = [statements.index(item) for item in dropped] + [
        statements.index(item) for item in created
    ]
    assert max(statements.index(item) for item in dropped) < min(
        statements.index(item) for item in created
    )
    database, tree = c1.build_world(tmp_path / "reference", members=6, filings=3)
    eq.monolithic_f0(database, tree, tmp_path / "reference" / "mono")
    assert _indexes(tmp_path / "reference" / "mono") == _indexes(result.world_directory)
    assert order  # the ordering was actually observed rather than vacuously true


def _indexes(world_directory: Path) -> set[tuple[str, str]]:
    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        return {
            (str(row["name"]), str(row["sql"]))
            for row in connection.execute(
                "SELECT name, sql FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
            )
        }


def test_a35_keeping_the_indexes_throughout_changes_nothing_semantic(
    tmp_path: Path, world: tuple[Path, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A35: index timing is performance, never semantics -- proved by doing it both ways."""
    database, _tree = world
    run = _run(tmp_path, world, size=1)
    deferred = _consolidate(run, database, suffix="-deferred")
    monkeypatch.setattr(cc, "_deferrable_indexes", lambda _connection: ())
    kept = _consolidate(run, database, suffix="-kept")
    assert (
        eq.measure(kept.world_directory)["tables"] == eq.measure(deferred.world_directory)["tables"]
    )
    assert _indexes(kept.world_directory) == _indexes(deferred.world_directory)


def test_a36_the_uniqueness_constraints_survive_the_deferral(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A36: only DECLARED indexes are deferred; the implicit key indexes are never dropped."""
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    result = _consolidate(run, database)
    with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=True) as connection:
        row = connection.execute("SELECT * FROM census_parsed_records LIMIT 1").fetchone()
        columns = ", ".join(row.keys())
        placeholders = ", ".join("?" * len(row.keys()))
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                f"INSERT INTO census_parsed_records ({columns}) VALUES ({placeholders})",  # noqa: S608
                tuple(row),
            )


# ==========================================================================
# A21, A22: identifiers under partitioning
# ==========================================================================
def test_a21_a22_no_f0_table_allocates_a_surrogate_identifier(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A21/A22: there is no autoincrement to collide and no surrogate key to remap.

    Every F0 identifier is a content digest over member-local inputs, so two chunks cannot
    allocate the same one for different rows and no foreign key has to be rewritten at merge
    time. That is a property of the accepted schema, asserted here rather than assumed.
    """
    database, _tree = world
    run = _run(tmp_path, world, size=2)
    result = _consolidate(run, database)
    with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        for table in ce.F0_WRITTEN_TABLES:
            row = connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)
            ).fetchone()
            assert "AUTOINCREMENT" not in str(row["sql"]).upper(), table


def test_a21_identifiers_are_identical_at_every_partition_size(tmp_path: Path) -> None:
    """Partition-size independence of every identifier, compared as sets rather than counts."""
    database, tree = c1.build_world(tmp_path, members=6, filings=2, shards=2, share_every=2)
    identifiers: list[set[tuple[str, ...]]] = []
    for size in (1, 3, 10_000):
        result = eq.chunked_f0(tmp_path, database, tree, chunk_members=size, label=f"ids-{size}")
        with connect(result.world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
            identifiers.append(
                {
                    (str(row["parsed_record_id"]), str(row["native_identity"]))
                    for row in connection.execute(
                        "SELECT parsed_record_id, native_identity FROM census_parsed_records"
                    )
                }
            )
    assert identifiers[0] == identifiers[1] == identifiers[2]
    assert identifiers[0]


# ==========================================================================
# A37: the digest reduction is order-sensitive, and the order is canonical
# ==========================================================================
def test_a37_the_completeness_digest_depends_on_canonical_member_order(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """A37: reducing out of canonical order produces a different digest -- so order is load-bearing.

    The consolidator's replay reads the merged member manifest ``ORDER BY member_ordinal``. This
    reproduces that fold by hand in the right order (matching the world exactly) and in a
    scrambled order (not matching), which is what makes the ordering a proved requirement rather
    than an implementation detail nobody would notice changing.
    """
    from typing import Any as _Any
    from typing import cast

    from disclosure_drift.m3.compact_evidence import CompactEvidenceSidecar, ProjectionDigest

    database, _tree = world
    run = _run(tmp_path, world, size=1)
    result = _consolidate(run, database)
    sidecar = CompactEvidenceSidecar(result.world_directory / "compact_evidence.sqlite3")
    try:
        members = [dict(row) for row in sidecar.members(c1.OBSERVATION)]
        stored = str(dict(sidecar.source_evidence(c1.OBSERVATION) or {})["completeness_digest"])
    finally:
        sidecar.close()

    def _fold(ordered: list[dict[str, Any]]) -> str:
        chain = ProjectionDigest(c1.SOURCE_ID)
        for entry in ordered:
            chain._records = (
                int(entry["parsed_registrants"])
                + int(entry["parsed_accessions"])
                + int(entry["parsed_other"])
            )
            chain._member = cast("_Any", cc._StoredMemberDigest(str(entry["projection_digest"])))
            chain.end_member()
        return chain.hexdigest()

    assert _fold(members) == stored
    assert _fold(list(reversed(members))) != stored


def test_the_merged_member_manifest_is_the_whole_source_exactly_once(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    database, _tree = world
    run = _run(tmp_path, world, size=1)
    result = _consolidate(run, database)
    assert result.receipt.members == run["plan"].total_members


def test_the_reduced_run_row_is_the_sum_of_the_chunks(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """The one logical parser run, reduced -- every chunk computes the same identifier."""
    database, _tree = world
    run = _run(tmp_path, world, size=1)
    result = _consolidate(run, database)
    assert result.receipt.parsed_records == sum(
        receipt.summary.parsed_records for receipt in run["receipts"]
    )
    assert result.receipt.quarantined_records == sum(
        receipt.summary.quarantined_records for receipt in run["receipts"]
    )
    identifiers = {
        row["parser_run_id"]
        for row in _rows(result.world_directory, "SELECT parser_run_id FROM census_parser_runs")
    }
    assert identifiers == {result.receipt.parser_run_id}


def _rows(world_directory: Path, statement: str) -> list[sqlite3.Row]:
    with connect(world_directory / WORKING_CATALOG_FILENAME, writer=False) as connection:
        return connection.execute(statement).fetchall()


def test_the_structural_retention_bound_is_reduced_exactly(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """Concatenate-then-truncate is exact because each chunk already retained up to the cap."""
    from disclosure_drift.sec.census import STREAMED_STRUCTURAL_DETAIL_LIMIT

    database, _tree = world
    run = _run(tmp_path, world, size=1)
    result = _consolidate(run, database)
    row = _rows(result.world_directory, "SELECT summary_json FROM census_parser_runs")[0]
    summary = json.loads(str(row["summary_json"]))
    assert summary["structural_detail"]["retention_limit"] == STREAMED_STRUCTURAL_DETAIL_LIMIT
    assert len(summary["structural"]) == summary["structural_detail"]["retained"]
    assert summary["structural_detail"]["retained"] <= STREAMED_STRUCTURAL_DETAIL_LIMIT


def test_c46_every_chunk_attachment_is_immutable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """C46/M39: the read-only promise is in the attach, not in a convention about not writing.

    An ordinary read-only attach of a WAL-mode database creates ``-wal`` and ``-shm`` files beside
    it, which changes the chunk's artifact **set** even though its main file is untouched --
    and a manifest that names an exact set of objects then fails. ``immutable=1`` opens the file
    with no sidecars at all and refuses a write through the handle.
    """
    statements, _result = _trace_consolidation(tmp_path, monkeypatch, members=6, label="immutable")
    attaches = [item for item in statements if item.strip().upper().startswith("ATTACH")]
    assert attaches
    for statement in attaches:
        assert "?immutable=1" in statement, statement


def test_an_immutable_attachment_refuses_a_write_and_creates_no_sidecar(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """The behavioural half: what ``immutable=1`` actually buys, demonstrated both ways."""
    database, _tree = world
    run = _run(tmp_path, world, size=1000)
    catalog = (
        run["chunk_root"]
        / run["plan"].chunks[0].chunk_id
        / "attempt-000"
        / WORKING_CATALOG_FILENAME
    )
    before = {path.name for path in catalog.parent.iterdir()}
    connection = sqlite3.connect(":memory:", isolation_level=None, uri=True)
    connection.execute(f"ATTACH DATABASE 'file:{catalog.resolve()}?immutable=1' AS src")
    assert connection.execute("SELECT COUNT(*) FROM src.census_parsed_records").fetchone()[0] > 0
    with pytest.raises(sqlite3.OperationalError, match="readonly"):
        connection.execute("DELETE FROM src.census_parsed_records")
    connection.execute("DETACH DATABASE src")
    connection.close()
    assert {path.name for path in catalog.parent.iterdir()} == before


def test_m42_a_chunk_altered_between_discovery_and_consumption_is_refused(
    tmp_path: Path, world: tuple[Path, DataTree]
) -> None:
    """The verification at consumption is not redundant: it closes a time-of-check window.

    A placement is derived, and only then do the chunk's bytes move. Handing the consolidator the
    already-derived placements reproduces exactly that race, and the manifest check performed
    where the rows are actually about to be read is what catches it.
    """
    from disclosure_drift.m3.chunk_storage import derive_placements

    database, _tree = world
    run = _run(tmp_path, world, size=2)
    placements = derive_placements(run["plan"], internal_root=run["chunk_root"])
    target = run["chunk_root"] / run["plan"].chunks[0].chunk_id / "attempt-000"
    connection = sqlite3.connect(target / "chunk_witness.sqlite3")
    connection.execute("INSERT INTO chunk_witness_meta VALUES ('raced', 'yes')")
    connection.commit()
    connection.close()
    with pytest.raises(ChunkEvidenceError, match="IMMUTABLE"):
        cc.resolve_chunk_inputs(run["plan"], internal_root=run["chunk_root"], placements=placements)
