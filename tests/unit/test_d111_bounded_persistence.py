"""Bounded-transaction persistence and the run-local working catalog (accepted Decision 111).

Decision 110 left one accepted MAJOR open: E0's durable database work is not executable within
any bounded time or journal budget. Three separate defects were measured on the real first
planned source, and this module holds the proofs for the three corrections:

**Throughput.** Two derivations were recomputed after **every** record even though each is a
function of the run's whole observation -- candidate lineage edges (a full grouped scan of every
registrant observation of the source, twice per registrant record) and accession conflict
indicators (a grouped read plus update per accession record). Both are monotone, so computing
each once after the last record writes exactly the same rows; what changes is that the work stops
being quadratic. A companion mutation test restores the per-record form and requires the
statement-count proof to fail, so the bound is an observation rather than a threshold nothing
could cross.

**Journal residency.** One transaction per source cannot keep its journal bounded once the source
is large enough. :class:`~disclosure_drift.sec.census.BoundedTransaction` splits a logical write
into bounded real transactions. Batch size must not be observable in the result, so the
equivalence tests run materially different batch sizes over the same input and compare every row
of every table the parse touches.

**Blast radius.** Partial progress must never become durable in the accepted operational catalog.
:class:`~disclosure_drift.m3.working_catalog.WorkingCatalog` gives the run a writable twin at the
same migration head, leaves the accepted artifact byte-identical, and records truthful run-local
progress in a ledger outside the accepted schema -- so an interruption leaves committed rows that
cannot be mistaken for a completed source.

Everything here runs over synthetic archives and disposable catalogs beneath ``tmp_path``. No test
resolves, opens, names, or infers the accepted private evidence root, none reads a real SEC
artifact, and none promotes a real catalog.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

# The accepted synthetic bulk-archive world. Reusing D110's builders is what keeps this module
# from carrying a second, drifting copy of the fixture whose equivalence claims it extends.
import test_d110_bounded_parse_memory as world  # noqa: E402

from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.m3.working_catalog import (  # noqa: E402
    WORKING_CATALOG_FILENAME,
    WorkingCatalog,
    WorkingCatalogError,
    file_digest,
    promote_working_catalog,
)
from disclosure_drift.sec.census import (  # noqa: E402
    SINGLE_TRANSACTION,
    BoundedTransaction,
    CensusCatalog,
)
from disclosure_drift.sec.source_registry import SOURCES  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

_BULK = "sec_bulk_submissions"


# ==========================================================================
# Helpers
# ==========================================================================


class _StubWriter:
    """The one attribute :class:`CensusCatalog` reads from a writer."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection


def _stream(tree: Any, observation: Any) -> Any:
    return op._stream_bulk_submissions(op.SnapshotStore(tree), observation)


def _persist_with_batch(
    database: Path,
    tree: Any,
    *,
    batch_size: int,
    checkpoint: bool = False,
) -> Any:
    """Persist the synthetic bulk source into ``database`` at one batch size."""
    observation = world._observation(tree, database)
    store = op.SnapshotStore(tree)
    with connect(database, writer=True) as connection:
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(connection))
        catalog = CensusCatalog(_StubWriter(connection))  # type: ignore[arg-type]
        return catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=observation.observation_id,
            batch_size=batch_size,
            checkpoint_batches=checkpoint,
        )


def _catalog_rows(database: Path) -> dict[str, list[tuple[Any, ...]]]:
    """Every compared table's rows, volatile timestamp columns dropped."""
    return {table: world._rows(database, table) for table in world._COMPARED_TABLES}


# ==========================================================================
# BoundedTransaction: the primitive itself
# ==========================================================================


def _counting_connection(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("CREATE TABLE t (a INTEGER)")
    return connection


def test_a_single_transaction_batch_size_commits_exactly_once(tmp_path: Path) -> None:
    """``SINGLE_TRANSACTION`` is the accepted whole-write behaviour, unchanged."""
    connection = _counting_connection(tmp_path / "t.sqlite3")
    with BoundedTransaction(connection, batch_size=SINGLE_TRANSACTION) as bounded:
        for value in range(50):
            connection.execute("INSERT INTO t VALUES (?)", (value,))
            bounded.unit()
        assert connection.in_transaction
    assert bounded.batches == 1
    assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 50
    connection.close()


def test_a_positive_batch_size_commits_on_each_boundary(tmp_path: Path) -> None:
    """Ten units at a batch size of four is three commits, and every row lands."""
    connection = _counting_connection(tmp_path / "t.sqlite3")
    with BoundedTransaction(connection, batch_size=4) as bounded:
        for value in range(10):
            connection.execute("INSERT INTO t VALUES (?)", (value,))
            bounded.unit()
    assert bounded.batches == 3
    assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 10
    connection.close()


def test_a_failure_rolls_back_only_the_open_batch(tmp_path: Path) -> None:
    """Committed batches stay durable; the batch in flight when it failed does not.

    This is the durability contract an interruption depends on: whole batches or nothing,
    never half of one.
    """
    connection = _counting_connection(tmp_path / "t.sqlite3")
    boom = RuntimeError("interrupted mid-batch")
    with (
        pytest.raises(RuntimeError, match="interrupted mid-batch"),
        BoundedTransaction(connection, batch_size=4) as bounded,
    ):
        for value in range(10):
            connection.execute("INSERT INTO t VALUES (?)", (value,))
            bounded.unit()
            if value == 9:
                raise boom
    assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 8
    assert not connection.in_transaction
    connection.close()


def test_a_negative_batch_size_is_refused(tmp_path: Path) -> None:
    connection = _counting_connection(tmp_path / "t.sqlite3")
    with pytest.raises(ValueError, match="must not be negative"):
        BoundedTransaction(connection, batch_size=-1)
    connection.close()


def test_checkpointing_truncates_the_write_ahead_log_at_each_boundary(tmp_path: Path) -> None:
    """The log is bounded by the batch, not by the whole write."""
    path = tmp_path / "t.sqlite3"
    connection = _counting_connection(path)
    wal = path.with_name(path.name + "-wal")
    with BoundedTransaction(connection, batch_size=200, checkpoint=True) as bounded:
        for value in range(1000):
            connection.execute("INSERT INTO t VALUES (?)", (value,))
            bounded.unit()
    # Five full batches plus the transaction left open after the last one. That trailing
    # transaction is empty here and is not in production: it is where a real caller writes
    # the run's finalization, after the last unit and before the write ends.
    assert bounded.batches == 6
    assert wal.stat().st_size == 0
    assert connection.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1000
    connection.close()


# ==========================================================================
# Section 8: batch size is not observable in the result
# ==========================================================================


@pytest.mark.parametrize(
    ("members", "filings", "malformed", "duplicate"),
    [
        pytest.param(8, 3, 0, False, id="plain"),
        pytest.param(8, 3, 2, False, id="with-malformed-members"),
        pytest.param(8, 3, 0, True, id="with-a-cross-member-duplicate"),
    ],
)
def test_two_batch_sizes_write_byte_identical_governed_output(
    tmp_path: Path, members: int, filings: int, malformed: int, duplicate: bool
) -> None:
    """Materially different batch sizes produce the same rows in every table.

    A commit boundary makes already-decided rows durable; it never participates in deciding
    them. Asserted on the rows rather than on counts, because a count can agree while an
    identity has moved.
    """
    left_root = tmp_path / "batch-one"
    right_root = tmp_path / "batch-three"
    left_db, left_tree = world._world(
        left_root, members=members, filings=filings, malformed=malformed, duplicate=duplicate
    )
    right_db, right_tree = world._world(
        right_root, members=members, filings=filings, malformed=malformed, duplicate=duplicate
    )

    left = _persist_with_batch(left_db, left_tree, batch_size=1, checkpoint=True)
    right = _persist_with_batch(right_db, right_tree, batch_size=3)

    assert left.parser_run_id == right.parser_run_id
    assert (left.parsed, left.quarantined, left.run_outcome) == (
        right.parsed,
        right.quarantined,
        right.run_outcome,
    )
    assert _catalog_rows(left_db) == _catalog_rows(right_db)


def test_batching_matches_the_accepted_single_transaction_result(tmp_path: Path) -> None:
    """A batched run equals the accepted whole-source transaction, row for row."""
    single_db, single_tree = world._world(tmp_path / "single", members=8, filings=4)
    batched_db, batched_tree = world._world(tmp_path / "batched", members=8, filings=4)

    single = _persist_with_batch(single_db, single_tree, batch_size=SINGLE_TRANSACTION)
    batched = _persist_with_batch(batched_db, batched_tree, batch_size=2, checkpoint=True)

    assert single.parser_run_id == batched.parser_run_id
    assert _catalog_rows(single_db) == _catalog_rows(batched_db)


def test_the_full_driver_still_agrees_with_the_merged_path_after_batching(
    tmp_path: Path,
) -> None:
    """End to end, the streamed driver and the pre-D110 merged driver still agree.

    The run-level derivations moved out of the per-record path in **both** implementations, so
    this is the test that catches a hoist that changed one path's answer and not the other's.
    """
    streamed_db, streamed_tree = world._world(tmp_path / "streamed", members=6, filings=3)
    merged_db, merged_tree = world._world(tmp_path / "merged", members=6, filings=3)

    world._run_streamed(streamed_db, streamed_tree, tmp_path / "streamed-locks")
    world._run_merged(merged_db, merged_tree, tmp_path / "merged-locks")

    for table in world._COMPARED_TABLES:
        # ``census_parser_runs`` carries the one deliberate, owner-ratified D110 summary
        # difference -- the streamed summary's bounded ``structural`` array. That difference
        # predates this record and is asserted exactly in the D110 suite; excluding it here
        # keeps this test about the derivations that moved.
        if table == "census_parser_runs":
            continue
        assert world._rows(streamed_db, table) == world._rows(merged_db, table), table


# ==========================================================================
# Section 7: the throughput correction, and its non-vacuity
# ==========================================================================


def _count_statements(database: Path, tree: Any, *, batch_size: int) -> dict[str, int]:
    """Count the statements one persist issues, grouped by the derivation they belong to."""
    counts = {"candidate_edges": 0, "conflict_marks": 0}
    observation = world._observation(tree, database)
    store = op.SnapshotStore(tree)
    with connect(database, writer=True) as connection:
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(connection))

        def trace(statement: str) -> None:
            collapsed = " ".join(statement.split())
            if "FROM census_registrant_observations" in collapsed and "GROUP BY" in collapsed:
                counts["candidate_edges"] += 1
            if collapsed.startswith("UPDATE census_accession_observations") and (
                "conflict_indicator = 1" in collapsed
            ):
                counts["conflict_marks"] += 1

        connection.set_trace_callback(trace)
        catalog = CensusCatalog(_StubWriter(connection))  # type: ignore[arg-type]
        catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=observation.observation_id,
            batch_size=batch_size,
        )
        connection.set_trace_callback(None)
    return counts


def test_the_run_level_derivations_do_not_scale_with_the_record_count(
    tmp_path: Path,
) -> None:
    """A tenfold record count must not produce a tenfold derivation-statement count.

    This is the whole throughput claim, stated as the thing that was actually wrong: the
    derivations used to run once per record, so their cost followed the source. Now each runs
    once per run, and a source ten times larger issues exactly as many.
    """
    small_db, small_tree = world._world(tmp_path / "small", members=4, filings=2)
    large_db, large_tree = world._world(tmp_path / "large", members=4, filings=20)

    small = _count_statements(small_db, small_tree, batch_size=SINGLE_TRANSACTION)
    large = _count_statements(large_db, large_tree, batch_size=SINGLE_TRANSACTION)

    assert small == large
    # Two alias kinds, one conflict pass -- per run, whatever the source holds.
    assert small["candidate_edges"] == 2
    assert small["conflict_marks"] == 1


def test_the_scaling_proof_fails_against_the_pre_d111_per_record_implementation(
    tmp_path: Path,
) -> None:
    """Non-vacuity: restore the per-record recomputation and the bound must break.

    Without this, the test above would pass just as happily against an implementation that
    never issued the statements at all.
    """
    from disclosure_drift.sec import census as census_module

    def per_record_normalize(
        self: CensusCatalog,
        connection: sqlite3.Connection,
        parsed_id: str,
        record: Any,
        observed: str,
    ) -> tuple[int, int]:
        result = original(self, connection, parsed_id, record, observed)
        # The pre-D111 shape exactly: both derivations, after every record.
        self._candidate_edges(connection, record.location.observation_id, kind="company_name")
        self._candidate_edges(connection, record.location.observation_id, kind="ticker")
        self._mark_accession_conflicts(connection)
        return result

    original = census_module.CensusCatalog._normalize_record

    small_db, small_tree = world._world(tmp_path / "small", members=4, filings=2)
    large_db, large_tree = world._world(tmp_path / "large", members=4, filings=20)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(census_module.CensusCatalog, "_normalize_record", per_record_normalize)
        small = _count_statements(small_db, small_tree, batch_size=SINGLE_TRANSACTION)
        large = _count_statements(large_db, large_tree, batch_size=SINGLE_TRANSACTION)

    assert large["candidate_edges"] > small["candidate_edges"]
    assert large["conflict_marks"] > small["conflict_marks"]
    assert large["candidate_edges"] >= 8 * small["candidate_edges"] // 10


def _shared_name_world(root: Path) -> tuple[Path, Any]:
    """A world whose first two members are different CIKs carrying one company name.

    This is exactly the evidence a candidate lineage edge is made of, and exactly the case the
    per-record recomputation existed to catch. Built as its own archive rather than by editing
    one afterwards, because the observation's recorded digest has to be the digest of the
    archive that is actually parsed.
    """
    import json
    import zipfile

    from disclosure_drift.paths import DataTree

    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    archive = tree.data_root / world._ARCHIVE_RELATIVE
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as target:
        for index in range(4):
            document = world._submissions_document(index + 1, filings=2)
            if index < 2:
                document["name"] = "SHARED REGISTRANT NAME"
            target.writestr(
                f"CIK{index + 1:010d}-member-{index:06d}.json",
                json.dumps(document, sort_keys=True),
            )
        target.writestr("readme.txt", "not a submissions document")
    world._seed_catalog(database, tree, archive.read_bytes())
    return database, tree


def test_the_hoisted_derivations_still_write_the_edges_and_conflicts(
    tmp_path: Path,
) -> None:
    """Computing once is not computing less: the same evidence still produces the same rows.

    Two members sharing one company name across different CIKs is the case the per-record
    implementation existed to catch, and it is still caught -- at every batch size, since the
    derivation now runs after the last record rather than inside any one batch.
    """
    for batch_size in (SINGLE_TRANSACTION, 1, 3):
        database, tree = _shared_name_world(tmp_path / f"edges-{batch_size}")
        _persist_with_batch(database, tree, batch_size=batch_size)
        with connect(database, writer=False) as connection:
            rows = sorted(
                (str(row["from_cik_padded"]), str(row["to_cik_padded"]), str(row["evidence_value"]))
                for row in connection.execute(
                    "SELECT from_cik_padded, to_cik_padded, evidence_value "
                    "FROM census_candidate_lineage_edges WHERE evidence_kind = 'company_name'"
                )
            )
        assert rows == [("0000000001", "0000000002", "SHARED REGISTRANT NAME")], batch_size


# ==========================================================================
# Section 4: the working catalog, and the operational catalog's isolation
# ==========================================================================


def test_a_working_catalog_copies_the_accepted_catalog_and_leaves_it_untouched(
    tmp_path: Path,
) -> None:
    """The accepted artifact is byte-identical before and after, and the copy matches its head."""
    database, _tree = world._world(tmp_path / "accepted", members=4, filings=2)
    before_sha, before_bytes = file_digest(database)

    with WorkingCatalog(database, tmp_path / "run") as working:
        assert working.path.name == WORKING_CATALOG_FILENAME
        assert working.identity.source_file_sha256 == before_sha
        assert working.identity.applied_migrations == _applied(database)
        working.connection.execute("PRAGMA user_version")

    after_sha, after_bytes = file_digest(database)
    assert (after_sha, after_bytes) == (before_sha, before_bytes)


def _applied(database: Path) -> tuple[int, ...]:
    from disclosure_drift.storage.sqlite import applied_versions

    with connect(database, writer=False) as connection:
        return applied_versions(connection)


def test_a_working_catalog_refuses_to_adopt_a_previous_attempts_file(tmp_path: Path) -> None:
    """A second attempt builds its own, so two attempts' progress can never be conflated."""
    database, _tree = world._world(tmp_path / "accepted", members=3, filings=2)
    directory = tmp_path / "run"
    with WorkingCatalog(database, directory):
        pass
    with (
        pytest.raises(WorkingCatalogError, match="already exists"),
        WorkingCatalog(database, directory),
    ):
        pass


def test_a_missing_accepted_catalog_is_refused(tmp_path: Path) -> None:
    with (
        pytest.raises(WorkingCatalogError, match="does not exist"),
        WorkingCatalog(tmp_path / "absent.sqlite3", tmp_path / "run"),
    ):
        pass


def test_parse_writes_land_in_the_working_catalog_and_not_the_accepted_one(
    tmp_path: Path,
) -> None:
    """The whole point of the architecture, asserted on the accepted catalog's bytes."""
    database, tree = world._world(tmp_path / "accepted", members=5, filings=3)
    before_sha, _ = file_digest(database)

    with WorkingCatalog(database, tmp_path / "run") as working:
        store = op.SnapshotStore(tree)
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(working.connection))
        observation = world._observation(tree, database)
        catalog = CensusCatalog(_StubWriter(working.connection))  # type: ignore[arg-type]
        result = catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=observation.observation_id,
            batch_size=2,
            checkpoint_batches=True,
        )
        assert result.parsed > 0
        assert working.wal_byte_length() == 0
        working_rows = working.connection.execute(
            "SELECT COUNT(*) AS n FROM census_parsed_records"
        ).fetchone()["n"]
    assert working_rows == result.parsed

    assert file_digest(database)[0] == before_sha
    with connect(database, writer=False) as connection:
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM census_parsed_records").fetchone()["n"]
            == 0
        )


# ==========================================================================
# Section 5: run-local progress is truthful and is never a disposition
# ==========================================================================


def test_progress_distinguishes_the_four_required_states(tmp_path: Path) -> None:
    database, _tree = world._world(tmp_path / "accepted", members=3, filings=2)
    with WorkingCatalog(database, tmp_path / "run") as working:
        ledger = working.ledger
        assert ledger.progress(world._INSTANCE) is None

        ledger.begin_source(world._INSTANCE, _BULK)
        started = ledger.progress(world._INSTANCE)
        assert started is not None
        assert started.state == "in_progress"
        assert not started.is_complete

        ledger.record_batch(world._INSTANCE, parts=2, batches=1)
        mid = ledger.progress(world._INSTANCE)
        assert mid is not None
        assert mid.state == "in_progress"
        assert mid.parts_committed == 2
        assert not mid.is_complete
        assert ledger.incomplete() == (mid,)

        ledger.mark_parsed(world._INSTANCE, parts=3, batches=2)
        parsed = ledger.progress(world._INSTANCE)
        assert parsed is not None
        assert parsed.state == "parsed"
        assert parsed.is_complete
        assert parsed.disposition is None
        assert ledger.incomplete() == ()

        ledger.mark_disposed(world._INSTANCE, "completed")
        disposed = ledger.progress(world._INSTANCE)
        assert disposed is not None
        assert disposed.state == "disposed"
        assert disposed.disposition == "completed"


def test_a_partially_parsed_source_cannot_be_disposed(tmp_path: Path) -> None:
    """Committed batches are execution progress. They are never a success claim."""
    database, _tree = world._world(tmp_path / "accepted", members=3, filings=2)
    with WorkingCatalog(database, tmp_path / "run") as working:
        working.ledger.begin_source(world._INSTANCE, _BULK)
        working.ledger.record_batch(world._INSTANCE, parts=1, batches=1)
        with pytest.raises(WorkingCatalogError, match="only a fully parsed source"):
            working.ledger.mark_disposed(world._INSTANCE, "completed")


def test_a_never_started_source_cannot_be_disposed(tmp_path: Path) -> None:
    database, _tree = world._world(tmp_path / "accepted", members=3, filings=2)
    with (
        WorkingCatalog(database, tmp_path / "run") as working,
        pytest.raises(WorkingCatalogError, match="only a fully parsed source"),
    ):
        working.ledger.mark_disposed(world._INSTANCE, "completed")


# ==========================================================================
# Section 11: interruption
# ==========================================================================


def test_an_interrupted_batched_parse_leaves_truthful_partial_working_state(
    tmp_path: Path,
) -> None:
    """Interrupt mid-batch and prove all five claims the interruption proof requires.

    The accepted catalog is untouched; the working catalog is structurally valid; whole
    committed batches survived and the batch in flight did not; the run wears no success; and
    the run-local ledger still says ``in_progress``.
    """
    database, tree = world._world(tmp_path / "accepted", members=12, filings=3)
    accepted_before = file_digest(database)

    class _InterruptError(RuntimeError):
        pass

    with WorkingCatalog(database, tmp_path / "run") as working:
        store = op.SnapshotStore(tree)
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(working.connection))
        observation = world._observation(tree, database)
        working.ledger.begin_source(world._INSTANCE, _BULK)

        def interrupting() -> Any:
            for index, item in enumerate(op._stream_bulk_submissions(store, observation)):
                # Mid-batch: batch size is 4, so 6 parts is two whole batches plus two.
                if index == 6:
                    raise _InterruptError
                yield item

        catalog = CensusCatalog(_StubWriter(working.connection))  # type: ignore[arg-type]
        with pytest.raises(_InterruptError):
            catalog.persist_streamed(
                interrupting(),
                parser_id=op._BULK_PARSER_ID,
                parser_version=SOURCES[_BULK].parser_version,
                source_observation_id=observation.observation_id,
                batch_size=4,
            )

        connection = working.connection
        assert not connection.in_transaction
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

        run = connection.execute("SELECT outcome, parsed_count FROM census_parser_runs").fetchone()
        assert run is not None
        # Committed, and truthfully claiming nothing: the accepted meaning of `failed` is
        # that no consumer may read this run's counts as a real observation.
        assert run["outcome"] == "failed"
        assert run["parsed_count"] == 0

        members_written = connection.execute(
            "SELECT COUNT(DISTINCT member_name) AS n FROM census_parsed_records"
        ).fetchone()["n"]
        # Two whole batches of four landed; the two parts of the batch in flight did not.
        assert members_written == 4

        progress = working.ledger.progress(world._INSTANCE)
        assert progress is not None
        assert progress.state == "in_progress"
        assert not progress.is_complete

    assert file_digest(database) == accepted_before


def test_a_restart_after_an_interruption_creates_no_duplicate_identities(
    tmp_path: Path,
) -> None:
    """Replaying the same source into a fresh working catalog reproduces the same identities.

    Identity preimages do not mention a batch, a boundary, or an attempt, so a restart lands
    on exactly the rows the uninterrupted run would have written.
    """
    database, tree = world._world(tmp_path / "accepted", members=8, filings=3)

    class _InterruptError(RuntimeError):
        pass

    with WorkingCatalog(database, tmp_path / "first") as first:
        store = op.SnapshotStore(tree)
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(first.connection))
        observation = world._observation(tree, database)

        def interrupting() -> Any:
            for index, item in enumerate(op._stream_bulk_submissions(store, observation)):
                if index == 5:
                    raise _InterruptError
                yield item

        catalog = CensusCatalog(_StubWriter(first.connection))  # type: ignore[arg-type]
        with pytest.raises(_InterruptError):
            catalog.persist_streamed(
                interrupting(),
                parser_id=op._BULK_PARSER_ID,
                parser_version=SOURCES[_BULK].parser_version,
                source_observation_id=observation.observation_id,
                batch_size=2,
            )
        interrupted_ids = {
            str(row["parsed_record_id"])
            for row in first.connection.execute(
                "SELECT parsed_record_id FROM census_parsed_records"
            )
        }
    assert interrupted_ids

    with WorkingCatalog(database, tmp_path / "second") as second:
        store = op.SnapshotStore(tree)
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(second.connection))
        observation = world._observation(tree, database)
        catalog = CensusCatalog(_StubWriter(second.connection))  # type: ignore[arg-type]
        catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=observation.observation_id,
            batch_size=2,
        )
        replayed_ids = {
            str(row["parsed_record_id"])
            for row in second.connection.execute(
                "SELECT parsed_record_id FROM census_parsed_records"
            )
        }

    assert interrupted_ids <= replayed_ids
    assert len(replayed_ids) == len(set(replayed_ids))


# ==========================================================================
# Section 12: promotion, disposable only
# ==========================================================================


def test_a_verified_working_catalog_promotes_atomically(tmp_path: Path) -> None:
    """Promotion installs exactly the verified bytes, with no re-parsing.

    Both files live in one directory, which is what makes the install a single ``rename``.
    """
    directory = tmp_path / "catalogs"
    directory.mkdir()
    accepted = directory / "operational.sqlite3"
    database, tree = world._world(tmp_path / "seed", members=4, filings=2)
    accepted.write_bytes(database.read_bytes())
    accepted_before = file_digest(accepted)[0]

    with WorkingCatalog(accepted, tmp_path / "run") as working:
        store = op.SnapshotStore(tree)
        from disclosure_drift.sec.observation_catalog import load_observations

        store.adopt(load_observations(working.connection))
        observation = world._observation(tree, database)
        catalog = CensusCatalog(_StubWriter(working.connection))  # type: ignore[arg-type]
        catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[_BULK].parser_version,
            source_observation_id=observation.observation_id,
            batch_size=2,
            checkpoint_batches=True,
        )
        working_path = working.path
    candidate = directory / "candidate.sqlite3"
    working_path.replace(candidate)
    verified = file_digest(candidate)[0]

    promoted = promote_working_catalog(
        candidate,
        accepted,
        expected_working_sha256=verified,
        expected_operational_sha256=accepted_before,
    )

    assert promoted == verified
    assert file_digest(accepted)[0] == verified
    assert not candidate.exists()
    with connect(accepted, writer=False) as connection:
        assert (
            connection.execute("SELECT COUNT(*) AS n FROM census_parsed_records").fetchone()["n"]
            > 0
        )


def test_promotion_refuses_when_the_catalog_it_replaces_changed(tmp_path: Path) -> None:
    """A catalog that moved since verification is not the one this promotion prepared against."""
    directory = tmp_path / "catalogs"
    directory.mkdir()
    accepted = directory / "operational.sqlite3"
    candidate = directory / "candidate.sqlite3"
    database, _tree = world._world(tmp_path / "seed", members=3, filings=2)
    accepted.write_bytes(database.read_bytes())
    candidate.write_bytes(database.read_bytes())
    before = file_digest(accepted)[0]
    accepted.write_bytes(database.read_bytes() + b"\x00")

    with pytest.raises(WorkingCatalogError, match="not the one this promotion"):
        promote_working_catalog(
            candidate,
            accepted,
            expected_working_sha256=file_digest(candidate)[0],
            expected_operational_sha256=before,
        )
    assert candidate.exists()


def test_promotion_refuses_a_candidate_that_is_not_the_verified_artifact(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "catalogs"
    directory.mkdir()
    accepted = directory / "operational.sqlite3"
    candidate = directory / "candidate.sqlite3"
    database, _tree = world._world(tmp_path / "seed", members=3, filings=2)
    accepted.write_bytes(database.read_bytes())
    candidate.write_bytes(database.read_bytes())

    with pytest.raises(WorkingCatalogError, match="not the artifact that was verified"):
        promote_working_catalog(
            candidate,
            accepted,
            expected_working_sha256="0" * 64,
            expected_operational_sha256=file_digest(accepted)[0],
        )
    assert file_digest(accepted)[0] == file_digest(database)[0]


def test_promotion_refuses_across_directories(tmp_path: Path) -> None:
    """A cross-directory move is not atomic, so it is refused rather than attempted."""
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    database, _tree = world._world(tmp_path / "seed", members=3, filings=2)
    candidate = left / "candidate.sqlite3"
    accepted = right / "operational.sqlite3"
    candidate.write_bytes(database.read_bytes())
    accepted.write_bytes(database.read_bytes())

    with pytest.raises(WorkingCatalogError, match="rename inside one directory"):
        promote_working_catalog(
            candidate,
            accepted,
            expected_working_sha256=file_digest(candidate)[0],
            expected_operational_sha256=file_digest(accepted)[0],
        )


# ==========================================================================
# Execution authority is unchanged by any of this
# ==========================================================================


def test_every_execution_authority_still_ships_none() -> None:
    """A passing remediation is not permission to run anything (accepted Decision 110, and D111)."""
    from disclosure_drift.m3 import e0

    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None
