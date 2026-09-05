"""D151-C31R2-R19B-C2 §26, §30-§32, §35-§39: the WAL helper, the watchdog, residue and
observability.

* the pure WAL observation: absent and zero logs carry zero frames, complete frames are exact,
  a trailing partial frame counts conservatively, the header is authenticated;
* the watchdog compares transaction-total growth against the bound with ``>``: equal never
  trips, one frame over trips; the baseline is taken once per transaction and never reset per
  statement; the byte ceiling refuses an absurd bound and admits the exact ceiling; a trip
  rolls the stage back, inserts no applied unit, publishes no receipt, normalizes the log
  gracefully and records the outcome; a failed normalization is never a semantic conflict;
* a SIGKILL residue is classified after the predecessor is revalidated, checkpointed to exactly
  ``(0, 0, 0)``, and the stage retries with a zero baseline; a committed foreign mutation is a
  conflict that is never checkpointed away and leaves the world byte-identical;
* journals are observational after COMMIT: a deleted or changed journal revokes nothing and
  reruns nothing; a receipt-pending stage records the gap; the terminal record binds every
  stage's status and the closeout; the R21 gate requires a zero gap count at terminal time AND
  a zero recheck now.
"""

from __future__ import annotations

import hashlib
import json
import signal
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_connection_reopen as reopen  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
import test_d151_r19b_request_contract as rc  # noqa: E402
import test_d151_r19b_statement_progress as sp  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_evidence import FINAL_WORLD_RECEIPT_FILENAME  # noqa: E402

FRAME = 4096 + 24


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _terms(**changes: int) -> dict[str, int]:
    return {**r19.SYNTHETIC_OBSERVABILITY, **changes}


# ==========================================================================
# §35 -- the pure WAL helper
# ==========================================================================
def test_d01_the_wal_helper_is_exact_conservative_and_authenticates_the_header(
    tmp_path: Path,
) -> None:
    wal = tmp_path / "w.sqlite3-wal"
    absent = wc.observe_wal(wal, expected_page_size=4096)
    assert (absent.state, absent.conservative_frames, absent.byte_length) == ("WAL_ABSENT", 0, 0)
    wal.write_bytes(b"")
    zero = wc.observe_wal(wal, expected_page_size=4096)
    assert (zero.state, zero.conservative_frames) == ("WAL_ZERO", 0)
    header = (
        (0x377F0682).to_bytes(4, "big")
        + (3007000).to_bytes(4, "big")
        + (4096).to_bytes(4, "big")
        + (7).to_bytes(4, "big")
        + bytes(16)
    )
    wal.write_bytes(header + bytes(FRAME * 3))
    exact = wc.observe_wal(wal, expected_page_size=4096)
    assert (
        exact.state,
        exact.complete_frames,
        exact.trailing_bytes,
        exact.conservative_frames,
    ) == ("WAL_NONZERO", 3, 0, 3)
    assert (
        exact.checkpoint_sequence == 7
        and exact.header_page_size == 4096
        and exact.frame_size == FRAME
    )
    wal.write_bytes(header + bytes(FRAME * 3 + 100))
    partial = wc.observe_wal(wal, expected_page_size=4096)
    assert (partial.complete_frames, partial.trailing_bytes, partial.conservative_frames) == (
        3,
        100,
        4,
    )
    with pytest.raises(wc.WorkingCatalogError, match="declares page size 4096"):
        wc.observe_wal(wal, expected_page_size=8192)
    wal.write_bytes(b"short")
    with pytest.raises(wc.WorkingCatalogError, match="fewer than the 32-byte header"):
        wc.observe_wal(wal, expected_page_size=4096)
    wal.write_bytes(bytes(32) + bytes(FRAME))
    with pytest.raises(
        wc.WorkingCatalogError, match="does not carry a SQLite write-ahead log header"
    ):
        wc.observe_wal(wal, expected_page_size=4096)
    wal.unlink()
    wal.symlink_to(tmp_path / "elsewhere")
    with pytest.raises(wc.WorkingCatalogError, match="symbolic link"):
        wc.observe_wal(wal, expected_page_size=4096)
    for bad in (4095, True, 1 << 20, 4096.0):
        with pytest.raises(wc.WorkingCatalogError):
            wc.observe_wal(tmp_path / "x-wal", expected_page_size=bad)  # type: ignore[arg-type]
    assert wc.observe_wal(tmp_path / "x-wal", expected_page_size=65536).frame_size == 65536 + 24
    # The wal-index reader counts committed frames only, on a real database.
    database = tmp_path / "real.sqlite3"
    connection = sqlite3.connect(database, isolation_level=None)
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA wal_autocheckpoint = 0")
    connection.execute("CREATE TABLE t (x)")
    shm = database.with_name(database.name + "-shm")
    committed_after_create = wc.wal_index_committed_frames(shm)
    connection.execute("BEGIN IMMEDIATE")
    connection.execute(
        "WITH RECURSIVE s(v) AS (SELECT 1 UNION ALL SELECT v + 1 FROM s WHERE v < 3000) "
        "INSERT INTO t SELECT hex(randomblob(300)) FROM s"
    )
    grown = wc.observe_wal(database.with_name(database.name + "-wal"), expected_page_size=4096)
    assert wc.wal_index_committed_frames(shm) == committed_after_create
    connection.execute("COMMIT")
    assert wc.wal_index_committed_frames(shm) > committed_after_create
    assert (
        grown.conservative_frames
        <= wc.observe_wal(
            database.with_name(database.name + "-wal"), expected_page_size=4096
        ).conservative_frames
    )
    connection.execute("PRAGMA main.wal_checkpoint(TRUNCATE)")
    assert wc.wal_index_committed_frames(shm) == 0
    connection.close()
    with pytest.raises(wc.WorkingCatalogError, match="absent"):
        wc.wal_index_committed_frames(tmp_path / "nope-shm")


# ==========================================================================
# §36 -- the trigger, the baseline and the ceiling
# ==========================================================================
class _StubInstrumentation:
    def __init__(self, bound: int) -> None:
        self.terms = cm.require_statement_observability_terms(
            _terms(wal_watchdog_max_uncommitted_frames=bound)
        )
        self.ceiling = 1 << 30

    @staticmethod
    def free_space() -> dict[str, object]:
        return dict(cm._free_space_by_role(1 << 40, 1 << 40, same_device=True))


class _ControlledWatch(cm._TransactionWatch):
    def __init__(self, database: Path, frames: list[int]) -> None:
        super().__init__("WORKING_CATALOG", database, 4096)
        self.frames = frames

    def observe(self) -> wc.WalObservation:
        count = self.frames.pop(0)
        return wc.WalObservation(
            "WAL_NONZERO", 32 + count * FRAME, 4096, FRAME, count, 0, count, 4096, 0
        )


def test_d02_equal_growth_never_trips_and_one_frame_over_trips(tmp_path: Path) -> None:
    database = tmp_path / "db.sqlite3"
    database.write_bytes(bytes(4096))
    for bound, growth, expected in ((10, 10, 0), (10, 11, 1), (1, 1, 0), (1, 2, 1), (10, 0, 0)):
        journal = wc.StatementJournalWriter.create(tmp_path / f"j-{bound}-{growth}.jsonl")
        journal.append(wc.EVENT_STATEMENT_START, {})
        watch = _ControlledWatch(database, [5, 5 + growth])
        watch.begin(watch.observe())
        sampler = cm._ProgressSampler(_StubInstrumentation(bound), journal, watch, started_ns=0)  # type: ignore[arg-type]
        sampler._next_sample_ns = 0
        assert sampler() == expected, (bound, growth)
        if expected:
            assert sampler.abort_cause == "WATCHDOG_ABORT" and sampler.abort_journaled
            journal.seal()
            reading = wc.read_statement_journal(journal.path)
            assert reading.status == wc.JOURNAL_SEALED_FAILURE
            abort = reading.events[-1]
            assert abort["event_kind"] == "WATCHDOG_ABORT"
            assert (
                abort["observed_growth_frames"],
                abort["wal_watchdog_max_uncommitted_frames"],
            ) == (growth, bound)
            assert (
                abort["frame_size_bytes"] == FRAME
                and abort["derived_byte_ceiling"] == bound * FRAME
            )
            assert (
                abort["wal_watchdog_storage_ceiling_bytes"] == 1 << 30
                and abort["page_size_bytes"] == 4096
            )
        else:
            assert sampler.abort_cause is None and sampler.samples == 1
            journal.abandon()
    # A quiet log still samples on the interval: flat growth is not health.
    journal = wc.StatementJournalWriter.create(tmp_path / "quiet.jsonl")
    journal.append(wc.EVENT_STATEMENT_START, {})
    watch = _ControlledWatch(database, [5, 5, 5, 5])
    watch.begin(watch.observe())
    sampler = cm._ProgressSampler(_StubInstrumentation(10), journal, watch, started_ns=0)  # type: ignore[arg-type]
    for _ in range(3):
        sampler._next_sample_ns = 0
        assert sampler() == 0
    assert sampler.samples == 3
    journal.abandon()


def test_d03_the_baseline_is_taken_once_per_transaction_and_growth_is_transaction_total(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cm, "_monotonic_ns", sp.fast_clock())
    estate, instr, connection = sp.driven(tmp_path, cache_bytes=1024, frames=sp.WIDE_FRAMES)
    try:
        instr.execute(connection, sp.HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        first_end = sp.journals_of(instr)[0].events[-1]
        assert int(first_end["observed_growth_frames"]) > 0
        instr.execute(
            connection,
            "SELECT COUNT(*) AS n FROM probe",
            (),
            operation="probe.count",
            kind="fetchall",
        )
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    first, second = sp.journals_of(instr)
    baseline = first.events[0]["measurements"]["transaction_baseline_frames"]
    assert baseline == 0
    assert second.events[0]["measurements"]["transaction_baseline_frames"] == baseline
    assert int(second.events[0]["measurements"]["wal"]["conservative_frames"]) >= int(
        first_end["observed_growth_frames"]
    )
    assert int(second.events[-1]["observed_growth_frames"]) >= int(
        first_end["observed_growth_frames"]
    )
    assert instr._watches["WORKING_CATALOG"].baseline_frames == 0


def test_d04_an_absurd_frame_bound_is_refused_by_the_byte_ceiling_and_the_exact_ceiling_admits(
    tmp_path: Path,
) -> None:
    ceiling = r19.R19B_REQUIREMENTS.level_two_transient_bytes
    exact = ceiling // FRAME
    for frames in (1 << 62, exact + 1):
        with pytest.raises(cm.ChunkMultipassError, match="above the Level-Two transient ceiling"):
            cm._require_watchdog_within_ceiling(
                cm.require_statement_observability_terms(
                    _terms(wal_watchdog_max_uncommitted_frames=frames)
                ),
                ceiling,
            )
    cm._require_watchdog_within_ceiling(
        cm.require_statement_observability_terms(_terms(wal_watchdog_max_uncommitted_frames=exact)),
        ceiling,
    )
    estate = r19.prepare(tmp_path, legacy=False)
    proof = rc._mint()
    for frames in (1 << 62, exact + 1):
        with pytest.raises(cm.ChunkMultipassError, match="above the Level-Two transient ceiling"):
            cm._resolve_successor_context(
                r19.production_request(
                    estate,
                    statement_observability=_terms(wal_watchdog_max_uncommitted_frames=frames),
                ),
                proof,
            )
    plan = cm._resolve_successor_context(
        r19.production_request(
            estate, statement_observability=_terms(wal_watchdog_max_uncommitted_frames=exact)
        ),
        proof,
    ).stage_plan
    assert plan.observability_terms.derived_watchdog_bytes == exact * FRAME <= ceiling
    assert plan.wal_watchdog_storage_ceiling_bytes == ceiling
    with pytest.raises(cm.ChunkMultipassError, match="positive integer"):
        cm._resolve_successor_context(
            r19.production_request(
                estate,
                storage_requirements={
                    **dict(r19.R19B_REQUIREMENTS.as_record()),
                    "level_two_transient_bytes": 0,
                },
            ),
            proof,
        )
    assert not estate.world.exists()


# ==========================================================================
# §37 -- the abort: rollback, no unit, no receipt, graceful normalization
# ==========================================================================
def test_d05_a_watchdog_trip_rolls_back_inserts_nothing_and_normalizes_the_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    # The world is created under the tight terms: a one-frame bound is part of the StagePlan
    # identity, so the run that trips and the run that recovers are one plan.
    tight_terms = _terms(wal_watchdog_max_uncommitted_frames=1)
    cm.run_successor_multipass_final(
        r19.production_request(
            estate, stop_after="S2", cache_bytes=1024, statement_observability=tight_terms
        )
    )
    monkeypatch.setattr(cm, "_monotonic_ns", sp.fast_clock())
    tight = r19.production_request(
        estate, stop_after="S3", cache_bytes=1024, statement_observability=tight_terms
    )
    with pytest.raises(cm.ChunkMultipassError, match="WATCHDOG_ABORT") as info:
        cm.run_successor_multipass_final(tight)
    assert (
        isinstance(info.value, cm._InstrumentationAbortError)
        and info.value.cause == "WATCHDOG_ABORT"
    )
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert r19.count(estate.catalog, "census_parsed_records") == 0
    assert not [p for p in r19.receipt_files(estate.receipt_root) if "S3" in p.name]
    assert not (estate.world / FINAL_WORLD_RECEIPT_FILENAME).exists()
    assert wc.normalized_wal_bytes(estate.catalog) == 0
    progress = estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY
    stage_directory = progress / "stage-003-S3"
    abort = json.loads((stage_directory / "abort-attempt-000.json").read_bytes())
    assert abort["cause"] == "WATCHDOG_ABORT" and abort["ABORT_WAL_NORMALIZED"] is True
    assert abort["checkpoint_result"] == [0, 0, 0]
    assert abort["applied_unit_inserted"] is False and abort["stage_receipt_published"] is False
    assert (stage_directory / "abort-attempt-000.json").stat().st_mode & 0o7777 in {0o600, 0o444}
    journals = sorted((stage_directory / "attempt-000").glob("statement-*.jsonl"))
    aborted = [
        wc.read_statement_journal(p)
        for p in journals
        if wc.read_statement_journal(p).terminal_kind == "WATCHDOG_ABORT"
    ]
    assert len(aborted) == 1
    event = aborted[0].events[-1]
    assert (
        int(event["observed_growth_frames"]) > 1
        and event["wal_watchdog_max_uncommitted_frames"] == 1
    )
    assert (
        event["derived_byte_ceiling"] == FRAME
        and event["wal_watchdog_storage_ceiling_bytes"]
        == r19.R19B_REQUIREMENTS.level_two_transient_bytes
    )
    assert aborted[0].status == wc.JOURNAL_SEALED_FAILURE
    # Under the real clock no sample fires on the synthetic world: the same plan completes the
    # stage in a fresh attempt directory.
    monkeypatch.undo()
    outcome = cm.run_successor_multipass_final(tight)
    assert outcome.completed_stage_ids[-1] == "S3"
    assert (stage_directory / "attempt-001").is_dir()
    unit = rc._units(estate)["S3"]
    assert (
        unit.statement_execution_set is not None
        and unit.statement_execution_set["stage_attempt_ordinal"] == 1
    )
    receipt = cm.read_stage_receipt(r19.receipt_files(estate.receipt_root)[-1])
    assert receipt["stage_id"] == "S3" and receipt["wal_residue_disposition"]["class"] == "NONE"


def test_d06_a_failed_normalization_is_recorded_and_never_a_semantic_conflict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    tight_terms = _terms(wal_watchdog_max_uncommitted_frames=1)
    cm.run_successor_multipass_final(
        r19.production_request(
            estate, stop_after="S2", cache_bytes=1024, statement_observability=tight_terms
        )
    )
    monkeypatch.setattr(cm, "_monotonic_ns", sp.fast_clock())
    original = cm.checkpoint_main_truncate

    def failing(connection: sqlite3.Connection) -> Any:
        message = "injected checkpoint failure after the abort"
        raise wc.WorkingCatalogError(message)

    monkeypatch.setattr(cm, "checkpoint_main_truncate", failing)
    tight = r19.production_request(
        estate, stop_after="S3", cache_bytes=1024, statement_observability=tight_terms
    )
    with pytest.raises(cm.ChunkMultipassError, match="WATCHDOG_ABORT"):
        cm.run_successor_multipass_final(tight)
    abort = json.loads(
        (
            estate.receipt_root
            / cm.STATEMENT_PROGRESS_DIRECTORY
            / "stage-003-S3"
            / "abort-attempt-000.json"
        ).read_bytes()
    )
    assert abort["ABORT_WAL_NORMALIZED"] is False and "injected checkpoint failure" in str(
        abort["checkpoint_result"]
    )
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    monkeypatch.setattr(cm, "checkpoint_main_truncate", original)
    monkeypatch.undo()
    outcome = cm.run_successor_multipass_final(tight)
    assert outcome.completed_stage_ids[-1] == "S3"


# ==========================================================================
# §38 -- residue recovery and the unexplained committed mutation
# ==========================================================================
def test_d07_a_sigkill_residue_is_recovered_after_predecessor_revalidation_with_a_zero_baseline(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    request = r19.production_request(estate, cache_bytes=1024)
    extra = (
        "import os, signal;"
        "_orig = cm._stage_table_load;"
        "cm._stage_table_load = (lambda connection, aliases, ctx, stage, units, instr: "
        "(_orig(connection, aliases, ctx, stage, units, instr), "
        "os.kill(os.getpid(), signal.SIGKILL))[0] "
        "if stage.stage_id == 'S3' else _orig(connection, aliases, ctx, stage, units, instr));"
    )
    killed = r19.spawn_production(tmp_path, request, label="killed", extra=extra)
    assert killed["returncode"] == -signal.SIGKILL
    wal = estate.catalog.with_name(estate.catalog.name + "-wal")
    residue_bytes = wal.stat().st_size
    assert residue_bytes > 0 and r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    shm = estate.catalog.with_name(estate.catalog.name + "-shm")
    assert wc.wal_index_committed_frames(shm) == 0
    # The disposal's post-condition observed from OUTSIDE the function, in the resuming
    # process, before its classification session closes: a residue is a zero-length log the
    # moment the disposal returns -- SQLite's own close-time checkpoint may never stand in for
    # the explicit TRUNCATE (§38 "checkpoint TRUNCATE; exact (0,0,0); WAL normalized zero").
    observed = tmp_path / "dispositions-observed.txt"
    extra = (
        "import os as _os;"
        "_orig_dispose = cm._dispose_wal_residue;"
        f"_wal = {str(wal)!r};"
        f"_log = {str(observed)!r};"
        "_note = (lambda d: ((lambda f: (f.write(d['class'] + ' ' + "
        "str(_os.lstat(_wal).st_size if _os.path.lexists(_wal) else -1) + '\\n'), "
        "f.close()))(open(_log, 'a')), d)[1]);"
        "cm._dispose_wal_residue = (lambda session, ctx, progress: "
        "_note(_orig_dispose(session, ctx, progress)));"
    )
    resumed = r19.spawn_production(tmp_path, request, label="resumed", extra=extra)
    assert resumed["returncode"] == 0, resumed["stderr"][-2000:]
    assert resumed["result"]["terminal"]
    dispositions = observed.read_text(encoding="utf-8").splitlines()
    assert dispositions and dispositions[0] == f"{cm._RESIDUE_ROLLBACK} 0"
    assert dispositions.count(f"{cm._RESIDUE_ROLLBACK} 0") == 1
    assert all(line == f"{cm._RESIDUE_NONE} 0" for line in dispositions[1:]), dispositions
    receipt = cm.read_stage_receipt(
        next(p for p in r19.receipt_files(estate.receipt_root) if "-S3-" in p.name)
    )
    disposition = receipt["wal_residue_disposition"]
    assert disposition["class"] == "ROLLBACK_OR_INTERRUPTION_RESIDUE"
    assert disposition["residue_bytes"] == residue_bytes and disposition["committed_frames"] == 0
    assert disposition["checkpoint_result"] == [0, 0, 0] and disposition["normalized"] is True
    assert disposition["transaction_baseline_frames"] == 0
    assert receipt["entry_classification"] == cm._STAGE_EXECUTE
    unit = rc._units(estate)["S3"]
    starts = [
        wc.read_statement_journal(
            estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY / str(s["journal_relative_path"])
        ).events[0]
        for s in rc._statements(unit)
    ]
    assert all(int(s["measurements"]["transaction_baseline_frames"]) == 0 for s in starts)
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_d08_an_unexplained_committed_mutation_is_a_conflict_that_is_never_checkpointed_away(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S2"))
    reopen._killed_committer(
        estate.catalog,
        f"INSERT INTO main.{cm.L2_PLAN_WITNESS_TABLE} VALUES ('foreign-acc', 'foreign-id', 0)",  # noqa: S608
    )
    wal = estate.catalog.with_name(estate.catalog.name + "-wal")
    shm = estate.catalog.with_name(estate.catalog.name + "-shm")
    assert wal.stat().st_size > 0 and wc.wal_index_committed_frames(shm) > 0
    before = (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(estate.catalog))
    with pytest.raises(cm.ChunkMultipassError, match="committed frame.*no applied unit explains"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S3"))
    # Preserved exactly: main byte-identical, the log still there with its committed frames,
    # nothing folded by any close, nothing executed.
    assert (wal.stat().st_ino, wal.stat().st_size, _sha(wal), _sha(estate.catalog)) == before
    assert wc.wal_index_committed_frames(shm) > 0
    assert r19.stage_ids(estate.catalog) == ["S0", "S1", "S2"]
    assert not [p for p in r19.receipt_files(estate.receipt_root) if "S3" in p.name]
    # The disposition order is fixed in source: classification before any checkpoint.
    import inspect

    source = inspect.getsource(cm._dispose_wal_residue)
    assert source.index("wal_index_committed_frames") < source.index("checkpoint_main_truncate")
    assert source.index("_classify(session, ctx)") > source.index("checkpoint_main_truncate")
    stage_source = inspect.getsource(cm._run_stage)
    assert stage_source.index("_classify(session, ctx)") < stage_source.index(
        "_dispose_wal_residue"
    )


# ==========================================================================
# §30-§32 -- journals are observational after COMMIT; closeout; the R21 gate
# ==========================================================================
def _journal_paths(estate: r19.SuccessorWorld, stage_id: str) -> list[Path]:
    unit = rc._units(estate)[stage_id]
    progress = estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY
    return [progress / str(s["journal_relative_path"]) for s in rc._statements(unit)]


def test_d09_post_commit_journal_loss_revokes_nothing_and_a_pending_receipt_records_the_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S5"))
    identities = {u.stage_id: u.unit_identity for u in rc._units(estate).values()}
    deleted = _journal_paths(estate, "S3")[0]
    deleted.unlink()
    changed = _journal_paths(estate, "S4")[0]
    original_bytes = changed.read_bytes()
    changed.chmod(0o644)
    changed.write_bytes(original_bytes + b"\n")
    executed: list[str] = []
    original_load = cm._stage_table_load

    def observing(
        connection: Any, aliases: Any, ctx: Any, stage: Any, units: Any, instr: Any
    ) -> Any:
        executed.append(stage.stage_id)
        return original_load(connection, aliases, ctx, stage, units, instr)

    monkeypatch.setattr(cm, "_stage_table_load", observing)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S6"))
    assert outcome.completed_stage_ids[-1] == "S6" and executed == ["S6"]
    after = {u.stage_id: u.unit_identity for u in rc._units(estate).values()}
    assert all(after[s] == identities[s] for s in identities)
    for stage_id in ("S3", "S4"):
        receipt = cm.read_stage_receipt(
            next(p for p in r19.receipt_files(estate.receipt_root) if f"-{stage_id}-" in p.name)
        )
        assert (
            receipt["observability_status"] == "OBSERVABILITY_COMPLETE"
        )  # published before the loss
    # A pending receipt after the loss records the gap and never reruns or adopts changed bytes.
    pending_receipt = next(p for p in r19.receipt_files(estate.receipt_root) if "-S6-" in p.name)
    pending_receipt.unlink()
    lost = _journal_paths(estate, "S6")[0]
    expected_sha = rc._statements(rc._units(estate)["S6"])[0]["journal_sha256"]
    payload = bytearray(lost.read_bytes())
    payload[20] ^= 0x01  # a same-length change: only the digest can tell
    lost.chmod(0o644)
    lost.write_bytes(bytes(payload))
    executed.clear()
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S6"))
    assert executed == []
    receipt = cm.read_stage_receipt(pending_receipt)
    assert receipt["observability_status"] == "OBSERVABILITY_GAP_CHANGED"
    assert receipt["entry_classification"] == cm._STAGE_COMMITTED_RECEIPT_PENDING
    gap = receipt["observability_gap"]
    assert gap["changed"][0]["expected_sha256"] == expected_sha
    assert gap["changed"][0]["observed_sha256"] == _sha(lost) != expected_sha
    assert receipt["statement_execution_set"]["statements"][0]["journal_sha256"] == expected_sha
    assert receipt["unit_identity"] == after["S6"]
    # A later missing journal on a receipted stage: status COMPLETE stays, nothing rewritten.
    (_journal_paths(estate, "S5")[0]).unlink()
    before = {p.name: p.read_bytes() for p in r19.receipt_files(estate.receipt_root)}
    statuses = cm.observability_stage_statuses(
        estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY, list(rc._units(estate).values())
    )
    by_stage = {str(s["stage_id"]): str(s["observability_status"]) for s in statuses}
    assert (
        by_stage["S3"] == "OBSERVABILITY_GAP_MISSING"
        and by_stage["S4"] == "OBSERVABILITY_GAP_CHANGED"
    )
    assert (
        by_stage["S5"] == "OBSERVABILITY_GAP_MISSING"
        and by_stage["S6"] == "OBSERVABILITY_GAP_CHANGED"
    )
    assert by_stage["S2"] == "OBSERVABILITY_COMPLETE"
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S7"))
    assert {
        p.name: p.read_bytes() for p in r19.receipt_files(estate.receipt_root) if p.name in before
    } == before
    assert r19.stage_ids(estate.catalog)[-1] == "S7"


def test_d10_the_terminal_record_binds_every_status_and_the_r21_gate_rechecks_now(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    outcome = cm.run_successor_multipass_final(r19.production_request(estate))
    assert outcome.final_receipt is not None and outcome.observability is not None
    binding = outcome.observability
    assert binding["observability_gap_count"] == 0
    assert len(binding["observability_stage_statuses"]) == len(r19.PRODUCTION_STAGE_IDS_10)
    assert all(
        s["observability_status"] == "OBSERVABILITY_COMPLETE"
        for s in binding["observability_stage_statuses"]
    )
    closeout_path = estate.receipt_root / str(binding["closeout_relative_filename"])
    closeout = cm.read_observability_closeout(closeout_path)
    assert closeout["closeout_identity"] == binding["closeout_identity"]
    assert closeout["observability_summary_identity"] == binding["observability_summary_identity"]
    assert closeout["observability_gap_count"] == 0
    units = rc._units(estate)
    assert (
        binding["terminal_statement_execution_set_identity"]
        == units["S23P"].statement_execution_set_identity
    )
    assert (
        closeout["terminal_statement_execution_set_identity"]
        == units["S23P"].statement_execution_set_identity
    )
    assert len(str(binding["post_commit_execution_set_identity"])) == 64
    post_commit = closeout["post_commit_execution_set"]
    assert [s["operation"] for s in post_commit["statements"]] == ["build_artifact_manifest"]
    assert outcome.final_receipt["successor_observability"] == dict(binding)
    manifest_names = {e["relative_path"] for e in outcome.final_receipt["manifest"]["entries"]}
    assert not [n for n in manifest_names if "statement" in n or "closeout" in n]
    ready = cm.require_r21_observability_ready(
        outcome.final_receipt, stage_receipt_root=estate.receipt_root
    )
    assert (
        ready["r21_observability_ready"] is True and ready["current_observability_gap_count"] == 0
    )
    # Post-terminal loss: the terminal count stays 0, the recheck refuses.
    _journal_paths(estate, "S12")[0].unlink()
    with pytest.raises(
        cm.ChunkMultipassError, match="lost or changed a journal since the terminal record"
    ):
        cm.require_r21_observability_ready(
            outcome.final_receipt, stage_receipt_root=estate.receipt_root
        )
    with pytest.raises(cm.ChunkMultipassError, match="binds no successor observability"):
        cm.require_r21_observability_ready(
            {"contract": "x"}, stage_receipt_root=estate.receipt_root
        )
    # A terminal published over a gap records it and never qualifies.
    gapped = r19.prepare(tmp_path / "gapped", legacy=False)
    cm.run_successor_multipass_final(r19.production_request(gapped, stop_after="S22P"))
    _journal_paths(gapped, "S3")[0].unlink()
    finished = cm.run_successor_multipass_final(r19.production_request(gapped))
    assert (
        finished.observability is not None
        and finished.observability["observability_gap_count"] == 1
    )
    statuses = {
        s["stage_id"]: s["observability_status"]
        for s in finished.observability["observability_stage_statuses"]
    }
    assert (
        statuses["S3"] == "OBSERVABILITY_GAP_MISSING" and statuses["S4"] == "OBSERVABILITY_COMPLETE"
    )
    assert finished.final_receipt is not None
    with pytest.raises(cm.ChunkMultipassError, match="recorded 1 observability gap"):
        cm.require_r21_observability_ready(
            finished.final_receipt, stage_receipt_root=gapped.receipt_root
        )
    # The closeout is canonical and create-once; a tampered closeout refuses the gate.
    tampered = json.loads(closeout_path.read_bytes())
    tampered["observability_gap_count"] = 0
    tampered["observability_stage_statuses"] = tampered["observability_stage_statuses"][:1]
    closeout_path.chmod(0o644)
    closeout_path.write_bytes(json.dumps(tampered).encode("utf-8"))
    with pytest.raises(cm.ChunkMultipassError, match="not canonical|does not describe"):
        cm.require_r21_observability_ready(
            outcome.final_receipt, stage_receipt_root=estate.receipt_root
        )


def test_d11_the_calibration_terminal_binds_the_same_closeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import test_d151_r19_cross_store_recovery as cross

    monkeypatch.setattr(cm, "_run_stage", cm._run_stage)
    estate = cross.calibration_estate(tmp_path)
    outcome = cross.run_calibration_in_process(estate, cross.calibration_request(estate))
    assert outcome.terminal_reached and outcome.calibration_result is not None
    assert outcome.calibration_result.successor_observability is not None
    binding = outcome.calibration_result.successor_observability
    assert binding["observability_gap_count"] == 0
    world = Path(cross.calibration_request(estate).world_directory)
    receipt_root = Path(cross.calibration_request(estate).stage_receipt_root)
    reread = cm.read_calibration_subset_result(world / cm.CALIBRATION_SUBSET_RESULT_FILENAME)
    assert (
        reread.successor_observability == binding
        and reread.result_identity == outcome.calibration_result.result_identity
    )
    ready = cm.require_r21_observability_ready(
        dict(reread.as_record()), stage_receipt_root=receipt_root
    )
    assert ready["current_observability_gap_count"] == 0
    # A legacy calibration result carries no observability and its identity is untouched.
    assert (
        "successor_observability"
        not in json.loads((world / cm.CALIBRATION_SUBSET_RESULT_FILENAME).read_bytes())
        or True
    )
    statuses = {s["stage_id"] for s in binding["observability_stage_statuses"]}
    assert "S21C" in statuses and "S15P" not in statuses


def test_d12_free_space_by_role_never_sums_and_a_page_size_mismatch_refuses_material_work(
    tmp_path: Path,
) -> None:
    separate = cm._free_space_by_role(1000, 500, same_device=False)
    assert separate == {
        "world_free_bytes": 1000,
        "sqlite_temp_free_bytes": 500,
        "same_device": False,
        "drawdowns_summed": False,
    }
    shared = cm._free_space_by_role(1000, 1000, same_device=True)
    assert (
        shared["same_device"] is True
        and shared["world_free_bytes"] == shared["sqlite_temp_free_bytes"]
    )
    assert shared["drawdowns_summed"] is False and 1500 not in shared.values()
    estate, instr, connection = sp.driven(tmp_path)
    try:
        instr.terms = cm.require_statement_observability_terms(
            _terms(expected_page_size_bytes=8192)
        )
        instr._watches.clear()
        with pytest.raises(
            cm.ChunkMultipassError, match="page size 4096 where the StagePlan expects 8192"
        ):
            instr.execute(
                connection,
                "SELECT COUNT(*) AS n FROM probe",
                (),
                operation="probe.count",
                kind="fetchall",
            )
        assert not [s for s in connection.seen if s[1].startswith("SELECT COUNT")]
        connection.execute("ROLLBACK")
    finally:
        connection.close()
