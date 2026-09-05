"""D151-C31R2-R19B-C2 §24-§25, §27-§29, §33-§34: journals, the progress handler and S18.

* the statement journal is create-once at 0600, every event is one canonical chained line
  fsynced before the call returns, ``STATEMENT_START`` lands before sqlite3 sees the SQL, a
  successful statement is sealed to 0444 with its digest and length bound into the execution
  set, an error seals a failure, a partial tail or a killed writer leaves an incomplete journal
  a later attempt never appends to;
* the progress handler is installed around exactly one statement and removed on success, on
  error and on abort; it issues no SQL; a free-space ``None``, a peak-RSS ``None``, a failed
  WAL observation or a failed fsync interrupts the statement and refuses the stage; the four
  observability terms are held to their bounds; an oversize event refuses;
* S18 journals its path decision first: an absent sidecar builds under COMPACT_EVIDENCE
  instrumentation, a complete sidecar authenticates with exact AUTHENTICATE coverage, a crash
  after the build and before the applied unit retries through AUTHENTICATE, and a partial
  sidecar selects no path and conflicts.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import signal
import sqlite3
import sys
import textwrap
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_r19_cross_store_recovery as cross  # noqa: E402
import test_d151_r19_durable_stages as r19  # noqa: E402
import test_d151_r19b_request_contract as rc  # noqa: E402
from test_d151_r19_durable_stages import _pinned_repository  # noqa: E402, F401

from disclosure_drift.m3 import chunk_multipass as cm  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.m3.chunk_plan import canonical_json_bytes  # noqa: E402
from disclosure_drift.m3.compact_evidence import COMPACT_EVIDENCE_SIDECAR_FILENAME  # noqa: E402

HEAVY_INSERT = (
    "INSERT INTO probe WITH RECURSIVE s(v) AS (SELECT 1 UNION ALL SELECT v + 1 FROM s "
    "WHERE v < 6000) SELECT v, hex(randomblob(160)) FROM s"
)

#: A frame bound wide enough that the probe insert samples without tripping (under the
#: 64 MiB synthetic ceiling: 16000 x 4120 bytes).
WIDE_FRAMES = 16000


def fast_clock(step_ns: int = 2_000_000_000) -> Any:
    """A monotonic clock that advances ``step_ns`` per read: every callback samples."""
    state = {"now": 1_000_000_000}

    def read() -> int:
        state["now"] += step_ns
        return state["now"]

    return read


def synthetic_descriptors(stage: cm.L2Stage) -> tuple[cm._OperationDescriptor, ...]:
    """A test-owned registry slice for driving the runner directly over a probe table."""
    return (
        cm._descriptor(
            stage,
            0,
            "probe.insert",
            mode="DYNAMIC_SQL_CAPTURE",
            kind="execute",
            source="test.probe",
        ),
        cm._descriptor(
            stage,
            1,
            "probe.select",
            mode="DYNAMIC_SQL_CAPTURE",
            kind="fetchall",
            source="test.probe",
        ),
        cm._descriptor(
            stage,
            2,
            "probe.iterate",
            mode="DYNAMIC_SQL_CAPTURE",
            kind="execute_iterate",
            source="test.probe",
        ),
        cm._descriptor(
            stage,
            3,
            "probe.many",
            mode="DYNAMIC_SQL_CAPTURE",
            kind="executemany",
            source="test.probe",
            expected="data_dependent",
        ),
        cm._descriptor(
            stage,
            4,
            "probe.count",
            mode="STATIC_SQL",
            kind="fetchall",
            source="test.probe",
            static_sql="SELECT COUNT(*) AS n FROM probe",
        ),
        cm._descriptor(
            stage,
            5,
            "probe.callable",
            mode="CALLABLE_NON_SQL",
            kind="callable",
            source="test.probe",
        ),
    )


def driven(
    tmp_path: Path, *, cache_bytes: int | None = None, frames: int | None = None
) -> tuple[r19.SuccessorWorld, cm._StageInstrumentation, rc._Recording]:
    """A world at S11, an instrumentation for S12 over a synthetic registry, and an open
    recording writer with a probe table inside an open transaction."""
    estate, ctx, stage, units = rc.boundary_world(tmp_path, "S11")
    ordinal, directory = cm._allocate_stage_attempt(ctx, stage)
    instr = cm._StageInstrumentation(
        ctx, stage, units, ordinal, directory, descriptors=synthetic_descriptors(stage)
    )
    if frames is not None:
        instr.terms = cm.require_statement_observability_terms(
            {**r19.SYNTHETIC_OBSERVABILITY, "wal_watchdog_max_uncommitted_frames": frames}
        )
    connection = rc.recording_connection(estate.catalog)
    if cache_bytes is not None:
        connection.execute(f"PRAGMA cache_size = {wc.cache_size_pragma(cache_bytes)}")
    connection.execute("BEGIN IMMEDIATE")
    instr.begin_world_transaction(connection)  # the baseline, taken right after BEGIN
    connection.execute("CREATE TABLE probe (x INTEGER, y TEXT)")  # unjournaled control DDL
    return estate, instr, connection


def journals_of(instr: cm._StageInstrumentation) -> list[wc.StatementJournalReading]:
    return [
        wc.read_statement_journal(path)
        for path in sorted(instr.attempt_directory.glob("statement-*.jsonl"))
    ]


# ==========================================================================
# §27 -- the journal primitives
# ==========================================================================
def test_c01_the_journal_is_create_once_chained_sealed_and_classified_without_repair(
    tmp_path: Path,
) -> None:
    path = tmp_path / "statement-0000.jsonl"
    writer = wc.StatementJournalWriter.create(path)
    assert os.lstat(path).st_mode & 0o7777 == 0o600 and os.lstat(path).st_nlink == 1
    first = writer.append(wc.EVENT_STATEMENT_START, {"a": 1})
    second = writer.append(wc.EVENT_STATEMENT_SAMPLE, {"b": [1, 2]})
    third = writer.append(wc.EVENT_STATEMENT_END, {"c": None})
    sha256, length = writer.seal()
    assert os.lstat(path).st_mode & 0o7777 == 0o444
    reading = wc.read_statement_journal(path)
    assert reading.status == wc.JOURNAL_SEALED_SUCCESS and reading.successful
    assert [e["sequence"] for e in reading.events] == [0, 1, 2]
    assert [e["previous_event_identity"] for e in reading.events] == [
        wc.JOURNAL_GENESIS_IDENTITY,
        first,
        second,
    ]
    assert reading.tip_identity == third and (reading.sha256, reading.byte_length) == (
        sha256,
        length,
    )
    lines = path.read_bytes().split(b"\n")
    assert lines[-1] == b"" and all(
        canonical_json_bytes(json.loads(line)) == line + b"\n" for line in lines[:-1]
    )
    for event in reading.events:
        body = {k: v for k, v in event.items() if k != "event_identity"}
        assert event["event_identity"] == cm._identity_of(body)
    assert wc._canonical_line({"z": 1, "a": ["é"]}) == canonical_json_bytes({"z": 1, "a": ["é"]})
    assert (
        wc.authenticate_statement_journal(path, expected_sha256=sha256, expected_byte_length=length)
        == wc.JOURNAL_AUTHENTIC
    )
    # Create-once: the same path refuses; a sealed writer refuses more events.
    with pytest.raises(wc.WorkingCatalogError, match="create-once"):
        wc.StatementJournalWriter.create(path)
    with pytest.raises(wc.WorkingCatalogError, match="closed"):
        writer.append(wc.EVENT_STATEMENT_END, {})
    # A partial tail, a missing terminal event and an unsealed terminal are all incomplete.
    partial = tmp_path / "statement-0001.jsonl"
    other = wc.StatementJournalWriter.create(partial)
    other.append(wc.EVENT_STATEMENT_START, {})
    other.abandon()
    with partial.open("ab") as handle:
        handle.write(b'{"event_kind": "STATEMENT_END", "sequ')
    incomplete = wc.read_statement_journal(partial)
    assert incomplete.status == wc.JOURNAL_INCOMPLETE and incomplete.partial_tail_bytes > 0
    assert incomplete.mode == 0o600 and len(incomplete.events) == 1
    unsealed = tmp_path / "statement-0002.jsonl"
    third_writer = wc.StatementJournalWriter.create(unsealed)
    third_writer.append(wc.EVENT_STATEMENT_START, {})
    third_writer.append(wc.EVENT_STATEMENT_END, {})
    third_writer.abandon()
    assert wc.read_statement_journal(unsealed).status == wc.JOURNAL_INCOMPLETE
    assert "never sealed" in wc.read_statement_journal(unsealed).detail
    # A tampered byte is MALFORMED to the reader and CHANGED to the authenticator; an absent
    # journal is MISSING; nothing is repaired.
    payload = bytearray(path.read_bytes())
    payload[10] ^= 0x01
    path.chmod(0o644)
    path.write_bytes(bytes(payload))
    assert wc.read_statement_journal(path).status == wc.JOURNAL_MALFORMED
    assert (
        wc.authenticate_statement_journal(path, expected_sha256=sha256, expected_byte_length=length)
        == wc.JOURNAL_CHANGED
    )
    path.unlink()
    assert wc.read_statement_journal(path).status == wc.JOURNAL_ABSENT
    assert (
        wc.authenticate_statement_journal(path, expected_sha256=sha256, expected_byte_length=length)
        == wc.JOURNAL_MISSING
    )
    # Oversize and reserved keys refuse.
    big = wc.StatementJournalWriter.create(tmp_path / "statement-0003.jsonl")
    with pytest.raises(wc.WorkingCatalogError, match="at most 4096"):
        big.append(wc.EVENT_STATEMENT_START, {"x": "y" * 5000})
    with pytest.raises(wc.WorkingCatalogError, match="reserved"):
        big.append(wc.EVENT_STATEMENT_START, {"sequence": 9})
    with pytest.raises(wc.WorkingCatalogError, match="no terminal event"):
        big.seal()
    assert wc.STATEMENT_EVENT_MAX_BYTES == 4096


# ==========================================================================
# §33 -- the handler around one statement; START before SQL; END sealed
# ==========================================================================
def test_c02_start_is_on_disk_before_sql_and_every_kind_seals_an_end(tmp_path: Path) -> None:
    estate, instr, connection = driven(tmp_path)
    rc._JOURNAL_DIRECTORY[:] = [instr.attempt_directory]
    try:
        connection.seen.clear()
        instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        rows = instr.execute(
            connection,
            "SELECT x FROM probe ORDER BY x",
            (),
            operation="probe.select",
            kind="fetchall",
        )
        assert isinstance(rows, list) and len(rows) == 6000
        streamed = instr.execute(
            connection,
            "SELECT x FROM probe ORDER BY x",
            (),
            operation="probe.iterate",
            kind="execute_iterate",
        )
        assert isinstance(streamed, Iterator) and sum(1 for _ in streamed) == 6000
        count = instr.execute(
            connection,
            "SELECT COUNT(*) AS n FROM probe",
            (),
            operation="probe.count",
            kind="fetchall",
        )
        assert int(count[0]["n"]) == 6000  # type: ignore[index]
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    material = [item for item in connection.seen if not item[1].startswith(("PRAGMA", "ROLLBACK"))]
    assert [item[0] for item in material] == ["execute"] * 4
    assert all(item[2] > 0 for item in material), "START was not on disk before sqlite3 saw the SQL"
    readings = journals_of(instr)
    assert [r.status for r in readings] == [wc.JOURNAL_SEALED_SUCCESS] * 4
    for reading in readings:
        kinds = [e["event_kind"] for e in reading.events]
        assert kinds[0] == wc.EVENT_STATEMENT_START and kinds[-1] == wc.EVENT_STATEMENT_END
        assert reading.mode == 0o444
        end = reading.events[-1]
        assert "maximum_process_peak_rss_bytes" in end and "process_rss_bytes" not in json.dumps(
            reading.events
        )
        assert end["rowcount"] in {6000, 1, -1}
    assert [e.record["execution_kind"] for e in instr.executions] == [
        "execute",
        "fetchall",
        "execute_iterate",
        "fetchall",
    ]
    assert instr.executions[0].record["rowcount"] == 6000
    for execution in instr.executions:
        record = execution.record
        assert (record["journal_sha256"], record["journal_byte_length"]) == (
            wc.read_statement_journal(
                instr.progress_root / str(record["journal_relative_path"])
            ).sha256,
            wc.read_statement_journal(
                instr.progress_root / str(record["journal_relative_path"])
            ).byte_length,
        )
    assert connection.handlers.count(("installed", 1000)) == 4
    assert connection.handlers.count(("removed", 0)) == 4
    assert connection.handlers[-1] == ("removed", 0)
    # Under the real clock a sub-second statement samples nothing: the interval is the clock.
    assert [r.events[-1]["samples"] for r in readings] == [0, 0, 0, 0]


def test_c03_samples_land_on_the_monotonic_interval_with_every_measurement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cm, "_monotonic_ns", fast_clock())
    estate, instr, connection = driven(tmp_path, cache_bytes=1024, frames=WIDE_FRAMES)
    try:
        instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    reading = journals_of(instr)[0]
    samples = [e for e in reading.events if e["event_kind"] == wc.EVENT_STATEMENT_SAMPLE]
    assert samples, "no sample fired on the interval"
    assert [int(s["sample_ordinal"]) for s in samples] == list(range(1, len(samples) + 1))
    for sample in samples:
        assert sample["free_bytes"]["same_device"] is True
        assert sample["free_bytes"]["drawdowns_summed"] is False
        assert (
            sample["free_bytes"]["world_free_bytes"]
            == sample["free_bytes"]["sqlite_temp_free_bytes"]
        )
        assert int(sample["process_peak_rss_bytes"]) > 0
        assert sample["wal"]["state"] in {"WAL_ZERO", "WAL_NONZERO", "WAL_ABSENT"}
        assert (
            int(sample["observed_growth_frames"]) >= 0
            and int(sample["transaction_baseline_frames"]) == 0
        )
        assert int(sample["wal_watchdog_max_uncommitted_frames"]) == WIDE_FRAMES
        assert int(sample["vm_step_ticks"]) >= 1
    assert "process_rss_bytes" not in json.dumps(reading.events)
    start = reading.events[0]
    measurements = start["measurements"]
    for key in (
        "wal",
        "transaction_baseline_frames",
        "wal_watchdog_max_uncommitted_frames",
        "page_size_bytes",
        "frame_size_bytes",
        "derived_byte_ceiling",
        "wal_watchdog_storage_ceiling_bytes",
        "progress_handler_vm_steps",
        "statement_progress_interval_seconds",
        "free_bytes",
        "process_peak_rss_bytes",
    ):
        assert key in measurements, key
    assert measurements["frame_size_bytes"] == 4096 + 24
    assert measurements["derived_byte_ceiling"] == WIDE_FRAMES * 4120
    for key in (
        "successor_run_id",
        "stage_plan_identity",
        "statement_registry_identity",
        "stage_id",
        "stage_ordinal",
        "unit_id",
        "unit_kind",
        "stage_attempt_ordinal",
        "statement_id",
        "statement_ordinal",
        "database_role",
        "sql_identity_mode",
        "runtime_sql_sha256",
        "execution_kind",
        "process_pid",
        "utc",
        "monotonic_ns",
        "event_identity",
    ):
        assert key in start, key
    assert start["process_pid"] == os.getpid()
    end = reading.events[-1]
    assert end["samples"] == len(samples) and end["peak_observed_growth_frames"] >= 0
    assert all(len(canonical_json_bytes(dict(e))) <= 4096 for e in reading.events)


def test_c03b_samples_are_spaced_by_the_interval_never_by_the_callback_cadence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§27 "SAMPLE: only at configured monotonic interval" and §39: the clock decides, never
    the callback cadence. Under a tenth-of-a-second clock step and the one-second synthetic
    interval, samples land exactly one interval -- exactly ten ticks -- apart; a sampler whose
    next-sample mark never advances would sample on every tick after the first."""
    step_ns = 100_000_000
    interval_ns = (
        int(r19.SYNTHETIC_OBSERVABILITY["statement_progress_interval_seconds"]) * 1_000_000_000
    )
    ticks_per_interval = interval_ns // step_ns
    assert ticks_per_interval == 10 and interval_ns % step_ns == 0
    monkeypatch.setattr(cm, "_monotonic_ns", fast_clock(step_ns))
    estate, instr, connection = driven(tmp_path, cache_bytes=1024, frames=WIDE_FRAMES)
    try:
        instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    reading = journals_of(instr)[0]
    assert reading.status == wc.JOURNAL_SEALED_SUCCESS
    start, end = reading.events[0], reading.events[-1]
    samples = [e for e in reading.events if e["event_kind"] == wc.EVENT_STATEMENT_SAMPLE]
    ticks = int(end["vm_step_ticks"])
    assert len(samples) >= 3, f"only {len(samples)} sample(s) over {ticks} tick(s)"
    clocks = [int(s["monotonic_ns"]) for s in samples]
    tick_marks = [int(s["vm_step_ticks"]) for s in samples]
    # Never before one interval has elapsed since START; then exactly one interval apart.
    assert clocks[0] - int(start["monotonic_ns"]) >= interval_ns
    assert [b - a for a, b in pairwise(clocks)] == [interval_ns] * (len(samples) - 1)
    assert [b - a for a, b in pairwise(tick_marks)] == [ticks_per_interval] * (len(samples) - 1)
    assert len(samples) <= ticks // ticks_per_interval
    assert int(end["samples"]) == len(samples)


def test_c04_an_unrelated_sqlite_error_seals_a_failure_and_is_never_misclassified(
    tmp_path: Path,
) -> None:
    estate, instr, connection = driven(tmp_path)
    try:
        with pytest.raises(sqlite3.OperationalError, match="no such table"):
            instr.execute(
                connection,
                "SELECT x FROM no_such_table",
                (),
                operation="probe.select",
                kind="fetchall",
            )
        assert instr.abort is None
        assert connection.handlers[-1] == ("removed", 0)
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    reading = journals_of(instr)[0]
    assert reading.status == wc.JOURNAL_SEALED_FAILURE
    assert reading.terminal_kind == wc.EVENT_STATEMENT_ERROR
    assert "abort_cause" not in reading.events[-1]
    assert reading.events[-1]["error_type"] == "OperationalError"
    assert instr.executions == []


def test_c05_a_killed_writer_leaves_an_incomplete_journal_a_later_attempt_never_touches(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    request = r19.production_request(estate, cache_bytes=1024)
    extra = (
        "import os, signal;"
        "cm._monotonic_ns = (lambda s={'n': 10**9}: "
        "(s.__setitem__('n', s['n'] + 2 * 10**9), s['n'])[1]);"
        "cm._ProgressSampler._sample = (lambda self, now: os.kill(os.getpid(), signal.SIGKILL));"
    )
    killed = r19.spawn_production(tmp_path, request, label="killed", extra=extra)
    assert killed["returncode"] == -signal.SIGKILL
    progress = estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY
    incomplete = [
        (path, wc.read_statement_journal(path))
        for path in sorted(progress.rglob("statement-*.jsonl"))
        if wc.read_statement_journal(path).status != wc.JOURNAL_SEALED_SUCCESS
    ]
    assert len(incomplete) == 1
    path, reading = incomplete[0]
    assert reading.status == wc.JOURNAL_INCOMPLETE and reading.mode == 0o600
    assert (
        reading.terminal_kind is None
        and reading.events[0]["event_kind"] == wc.EVENT_STATEMENT_START
    )
    before = (path.stat().st_ino, path.stat().st_size, path.read_bytes())
    resumed = r19.spawn_production(tmp_path, request, label="resumed")
    assert resumed["returncode"] == 0, resumed["stderr"][-2000:]
    assert resumed["result"]["terminal"]
    assert (path.stat().st_ino, path.stat().st_size, path.read_bytes()) == before
    assert wc.read_statement_journal(path).status == wc.JOURNAL_INCOMPLETE
    stage_directory = path.parent.parent
    attempts = sorted(p.name for p in stage_directory.iterdir() if p.name.startswith("attempt-"))
    assert attempts == ["attempt-000", "attempt-001"]
    assert estate.legacy is not None
    r19.eq.assert_equivalent(
        r19.eq.measure(estate.legacy["world_directory"]), r19.eq.measure(estate.world)
    )


def test_c06_attempts_and_journals_are_create_once_and_names_are_validated(tmp_path: Path) -> None:
    estate, ctx, stage, units = rc.boundary_world(tmp_path, "S11")
    ordinal, directory = cm._allocate_stage_attempt(ctx, stage)
    assert ordinal == 0 and directory.name == "attempt-000"
    assert directory.parent.name == "stage-012-S12"
    second, later = cm._allocate_stage_attempt(ctx, stage)
    assert (second, later.name) == (1, "attempt-001")
    (directory.parent / "attempt-xyz").mkdir()
    with pytest.raises(cm.ChunkMultipassError, match="never writes"):
        cm._allocate_stage_attempt(ctx, stage)
    (directory.parent / "attempt-xyz").rmdir()
    link = directory.parent / "attempt-002"
    link.symlink_to(directory)
    with pytest.raises(cm.ChunkMultipassError, match="not a real directory"):
        cm._allocate_stage_attempt(ctx, stage)
    link.unlink()
    assert cm._stage_directory_name(cm.L2Stage(3, "S16.2", "u", "k", "none")) == "stage-003-S16_2"
    with pytest.raises(cm.ChunkMultipassError, match="not a valid successor stage id"):
        cm._stage_directory_name(cm.L2Stage(3, "../x", "u", "k", "none"))


def test_c07_the_execution_set_is_exact_and_bound_into_unit_and_receipt(tmp_path: Path) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S12"))
    unit = rc._units(estate)["S12"]
    assert unit.contract == cm.L2_APPLIED_UNIT_CONTRACT_V2
    execution_set = unit.statement_execution_set
    assert execution_set is not None
    body = {k: v for k, v in execution_set.items() if k != "execution_set_identity"}
    assert (
        cm._identity_of(body)
        == execution_set["execution_set_identity"]
        == unit.statement_execution_set_identity
    )
    assert execution_set["contract"] == cm.L2_STATEMENT_EXECUTION_SET_CONTRACT
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    assert (
        unit.statement_registry_identity
        == plan.statement_registry_identity
        == execution_set["statement_registry_identity"]
    )
    progress = plan.statement_progress_root
    statements = rc._statements(unit)
    assert [s["operation"] for s in statements] == [
        "count:m3_l2_chunk_observation_corrections",
        "corrections.orphaned_winners",
        "corrections.orphaned_rivals",
        "corrections.insert_winners",
        "corrections.insert_rivals",
        "corrections.summary",
    ]
    assert [s["statement_ordinal"] for s in statements] == list(range(6))
    on_disk = sorted(
        p.name for p in (progress / "stage-012-S12" / "attempt-000").glob("statement-*.jsonl")
    )
    assert on_disk == [Path(str(s["journal_relative_path"])).name for s in statements]
    for statement in statements:
        reading = wc.read_statement_journal(progress / str(statement["journal_relative_path"]))
        assert reading.status == wc.JOURNAL_SEALED_SUCCESS
        assert (reading.sha256, reading.byte_length, reading.tip_identity) == (
            statement["journal_sha256"],
            statement["journal_byte_length"],
            statement["journal_chain_tip"],
        )
        assert (
            statement["stage_attempt_ordinal"] == 0
            and statement["database_role"] == "WORKING_CATALOG"
        )
    receipt = cm.read_stage_receipt(r19.receipt_files(estate.receipt_root)[-1])
    assert receipt["stage_id"] == "S12"
    assert receipt["statement_execution_set_identity"] == unit.statement_execution_set_identity
    assert receipt["statement_registry_identity"] == plan.statement_registry_identity
    assert receipt["statement_execution_set"] == dict(execution_set)
    assert receipt["observability_status"] == "OBSERVABILITY_COMPLETE"
    coverage = {item["statement_id"]: item for item in execution_set["coverage"]}  # type: ignore[union-attr]
    assert all(item["observed"] == item["expected"] for item in coverage.values())
    assert coverage["S12/count:m3_l2_chunk_observation_corrections"]["expected"] == 1


# ==========================================================================
# §33 -- fail-closed interruption
# ==========================================================================
def test_c08_the_handler_issues_no_sqlite_and_is_removed_on_every_path() -> None:
    forbidden = {
        "execute",
        "executemany",
        "executescript",
        "connect",
        "mkdir",
        "unlink",
        "rename",
        "open",
        "chmod",
        "attach",
    }
    for function in (cm._ProgressSampler.__call__, cm._ProgressSampler._sample):
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        called = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        } | {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assert not (called & forbidden), called & forbidden
    source = inspect.getsource(cm._StageInstrumentation.execute)
    assert source.count("set_progress_handler(None, 0)") >= 2
    assert "finally:" in source


def test_c09_free_space_none_interrupts_before_and_during_a_statement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate, instr, connection = driven(tmp_path, cache_bytes=1024)
    try:
        monkeypatch.setattr(cm, "free_bytes", lambda path: None)
        with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE.*returned None"):
            instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        assert not [s for s in connection.seen if s[1].startswith("WITH RECURSIVE")]
        assert journals_of(instr)[-1].status == wc.JOURNAL_SEALED_FAILURE
        monkeypatch.undo()
        # During: the helper returns None on the interval -> the sample fails -> interrupted.
        monkeypatch.setattr(cm, "_monotonic_ns", fast_clock())
        calls = {"n": 0}

        def flaky(path: Path) -> int | None:
            calls["n"] += 1
            return None if calls["n"] > 1 else 1 << 40

        monkeypatch.setattr(cm, "free_bytes", flaky)
        with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE") as info:
            instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        assert isinstance(info.value.__cause__, sqlite3.OperationalError)
        assert instr.abort is not None and instr.abort.cause == "INSTRUMENTATION_FAILURE"
        assert not connection.in_transaction  # SQLite rolled the interrupted transaction back
        assert connection.handlers[-1] == ("removed", 0)
    finally:
        connection.close()
    readings = journals_of(instr)
    assert [r.status for r in readings] == [wc.JOURNAL_SEALED_FAILURE] * 2
    assert readings[1].events[-1]["abort_cause"] == "INSTRUMENTATION_FAILURE"
    assert instr.executions == []


def test_c10_rss_wal_and_fsync_failures_interrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate, instr, connection = driven(tmp_path, cache_bytes=1024)
    try:
        monkeypatch.setattr(cm, "_monotonic_ns", fast_clock())
        original_rss = cm.process_peak_resident_bytes
        calls = {"n": 0}

        def rss_then_none() -> int | None:
            calls["n"] += 1
            return original_rss() if calls["n"] <= 1 else None

        monkeypatch.setattr(cm, "process_peak_resident_bytes", rss_then_none)
        with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE"):
            instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        monkeypatch.setattr(cm, "process_peak_resident_bytes", original_rss)
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS probe (x INTEGER, y TEXT)")
        instr.begin_world_transaction(connection)
        original_observe = cm.observe_wal
        seen = {"n": 0}

        def failing_observe(path: Path, *, expected_page_size: int) -> Any:
            seen["n"] += 1
            if seen["n"] > 1:
                message = "injected observation failure"
                raise wc.WorkingCatalogError(message)
            return original_observe(path, expected_page_size=expected_page_size)

        monkeypatch.setattr(cm, "observe_wal", failing_observe)
        with pytest.raises(cm.ChunkMultipassError, match="injected observation failure"):
            instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        monkeypatch.setattr(cm, "observe_wal", original_observe)
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS probe (x INTEGER, y TEXT)")
        instr.begin_world_transaction(connection)
        original_fsync = os.fsync
        fsyncs = {"n": 0}

        def failing_fsync(descriptor: int) -> None:
            fsyncs["n"] += 1
            if fsyncs["n"] > 1:
                message = "injected fsync failure"
                raise OSError(message)
            original_fsync(descriptor)

        monkeypatch.setattr(wc.os, "fsync", failing_fsync)
        with pytest.raises(cm.ChunkMultipassError, match="INSTRUMENTATION_FAILURE"):
            instr.execute(connection, HEAVY_INSERT, (), operation="probe.insert", kind="execute")
        monkeypatch.setattr(wc.os, "fsync", original_fsync)
        assert not connection.in_transaction
    finally:
        connection.close()
    assert instr.executions == []
    assert all(r.status != wc.JOURNAL_SEALED_SUCCESS for r in journals_of(instr))


def test_c11_the_four_terms_are_held_to_their_bounds() -> None:
    base = dict(r19.SYNTHETIC_OBSERVABILITY)
    for field, bad in (
        ("progress_handler_vm_steps", (999, 100_001, True, 1000.0, "1000")),
        ("statement_progress_interval_seconds", (0, 301, True)),
        ("wal_watchdog_max_uncommitted_frames", (0, -5, True)),
        ("expected_page_size_bytes", (4095, 3, True, 4096.0)),
    ):
        for value in bad:
            with pytest.raises(cm.ChunkMultipassError):
                cm.require_statement_observability_terms({**base, field: value})
    for value in (1000, 100_000):
        terms = cm.require_statement_observability_terms(
            {**base, "progress_handler_vm_steps": value}
        )
        assert terms.progress_handler_vm_steps == value
    for value in (1, 300):
        assert (
            cm.require_statement_observability_terms(
                {**base, "statement_progress_interval_seconds": value}
            ).statement_progress_interval_seconds
            == value
        )
    with pytest.raises(cm.ChunkMultipassError, match="exactly"):
        cm.require_statement_observability_terms({**base, "extra": 1})
    with pytest.raises(cm.ChunkMultipassError, match="mapping"):
        cm.require_statement_observability_terms([1, 2, 3])
    assert cm.require_statement_observability_terms(base).derived_watchdog_bytes == 128 * 4120


def test_c12_an_oversize_event_refuses_and_executemany_streams_bounded_evidence(
    tmp_path: Path,
) -> None:
    estate, instr, connection = driven(tmp_path)
    try:
        with pytest.raises(cm.ChunkMultipassError, match="at most 4096"):
            instr.record_callable("probe.callable", lambda: None, facts={"big": "x" * 5000})
        consumed = {"n": 0}

        def rows() -> Iterator[tuple[int, str]]:
            for index in range(3000):
                consumed["n"] += 1
                yield (index, "z")

        cursor = instr.execute(
            connection,
            "INSERT INTO probe VALUES (?, ?)",
            rows(),
            operation="probe.many",
            kind="executemany",
        )
        assert isinstance(cursor, sqlite3.Cursor) and consumed["n"] == 3000
        connection.execute("ROLLBACK")
    finally:
        connection.close()
    record = instr.executions[-1].record
    evidence = record["parameter_identity"]
    assert evidence["kind"] == "streamed" and evidence["count"] == 3000
    assert evidence["shape_consistent"] is True and evidence["representable"] is True
    assert len(str(evidence["value_sha256"])) == 64 and len(str(evidence["shape_identity"])) == 64
    assert record["execution_kind"] == "executemany" and record["rowcount"] == 3000
    reading = wc.read_statement_journal(instr.progress_root / str(record["journal_relative_path"]))
    assert reading.status == wc.JOURNAL_SEALED_SUCCESS
    assert "row" not in json.dumps(
        reading.events[-1]["parameter_evidence"]
    )  # no raw bodies persisted
    bound = cm._parameter_evidence((1, "a", None, b"\x00"))
    assert (
        bound["kind"] == "bound" and bound["count"] == 4 and len(str(bound["value_sha256"])) == 64
    )
    assert cm._parameter_evidence(object())["kind"] == "unrepresentable"


# ==========================================================================
# §24, §25, §40 -- S18 BUILD / AUTHENTICATE
# ==========================================================================
def _s18(estate: r19.SuccessorWorld) -> tuple[cm.AppliedUnit, list[dict[str, Any]]]:
    unit = rc._units(estate)["S18"]
    return unit, rc._statements(unit)


def test_c13_an_absent_sidecar_builds_under_compact_evidence_instrumentation(
    tmp_path: Path,
) -> None:
    estate = r19.prepare(tmp_path)
    cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    unit, statements = _s18(estate)
    assert unit.statement_execution_set is not None
    assert unit.statement_execution_set["selected_path"] == "BUILD"
    operations = [s["operation"] for s in statements]
    assert operations[0] == "path_decision"
    assert {
        "member_deltas.create_temp",
        "member_deltas.summary",
        "merge_sidecar.insert_members",
        "merge_sidecar.summary",
        "merge_sidecar.digest_replay",
        "sidecar.member_manifest_rows",
        "sidecar.identity_fold:compact_source_members",
    } <= set(operations)
    assert len(operations) == 1 + 5 + 1 + 4
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    registry = {str(i["statement_id"]): i for i in plan.statement_registry}
    for statement in statements[1:]:
        assert statement["database_role"] == "COMPACT_EVIDENCE"
        reading = wc.read_statement_journal(
            plan.statement_progress_root / str(statement["journal_relative_path"])
        )
        assert reading.status == wc.JOURNAL_SEALED_SUCCESS
        start = reading.events[0]
        assert start["measurements"]["watchdog_applicable"] is True
        assert registry[str(statement["statement_id"])]["watchdog_applicable"] is True
        assert start["measurements"]["wal"]["page_size"] == 4096
    decision = wc.read_statement_journal(
        plan.statement_progress_root / str(statements[0]["journal_relative_path"])
    )
    assert decision.events[0]["decision"]["selected_path"] == "BUILD"
    assert decision.events[0]["decision"]["expected_path"] == "BUILD"
    assert decision.events[0]["decision"]["sidecar_file_state"]["lstat_class"] == "absent"
    assert len(str(decision.events[0]["decision"]["file_state_identity"])) == 64
    assert estate.legacy is not None
    legacy = estate.legacy["final"].as_record()
    assert unit.outcome_witness["completeness_digest"] == legacy["completeness_digest"]


def test_c14_a_complete_sidecar_authenticates_with_exact_authenticate_coverage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    cross._raise_once_for(monkeypatch, cm._BINDING_SIDECAR)
    with pytest.raises(RuntimeError, match="sidecar binding"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    sidecar = estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    assert sidecar.is_file() and r19.stage_ids(estate.catalog)[-1] == "S17C"
    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    unit, statements = _s18(estate)
    assert unit.statement_execution_set is not None
    assert unit.statement_execution_set["selected_path"] == "AUTHENTICATE"
    operations = [s["operation"] for s in statements]
    assert operations == [
        "path_decision",
        "sidecar.member_manifest_rows",
        *[
            f"sidecar.identity_fold:{table}"
            for table in (
                "compact_source_evidence",
                "compact_source_members",
                "compact_resolution_evidence",
                "compact_corroboration_evidence",
            )
        ],
    ]
    coverage = [item["statement_id"] for item in unit.statement_execution_set["coverage"]]  # type: ignore[union-attr]
    assert not [c for c in coverage if "merge_sidecar" in c or "member_deltas" in c]
    assert "S18/path_decision" in coverage and "S18/sidecar.member_manifest_rows" in coverage
    # The path decision and its attempt directory: attempt-001 (the first attempt built).
    assert statements[0]["stage_attempt_ordinal"] == 1
    plan = cm._read_stored_stage_plan(r19.readonly(estate.catalog))
    decision = wc.read_statement_journal(
        plan.statement_progress_root / str(statements[0]["journal_relative_path"])
    )
    assert decision.events[0]["decision"]["selected_path"] == "AUTHENTICATE"
    assert decision.events[0]["decision"]["sidecar_file_state"]["complete"] is True
    # The first attempt's BUILD journals are intact and sealed: nothing was appended to them.
    s18 = next(stage for stage in plan.stages if stage.stage_id == "S18")
    first_attempt = plan.statement_progress_root / cm._stage_directory_name(s18) / "attempt-000"
    assert first_attempt.is_dir()
    assert all(
        wc.read_statement_journal(p).status == wc.JOURNAL_SEALED_SUCCESS
        for p in first_attempt.glob("statement-*.jsonl")
    )


def test_c15_a_crash_after_the_build_and_before_the_unit_retries_through_authenticate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    estate = r19.prepare(tmp_path, legacy=False)
    original = cm._insert_applied_unit
    fired = {"done": False}

    def crash_at_s18(connection: sqlite3.Connection, **kwargs: Any) -> Any:
        if kwargs["stage"].stage_id == "S18" and not fired["done"]:
            fired["done"] = True
            message = "injected crash after the sidecar build, before the applied unit"
            raise RuntimeError(message)
        return original(connection, **kwargs)

    monkeypatch.setattr(cm, "_insert_applied_unit", crash_at_s18)
    with pytest.raises(RuntimeError, match="before the applied unit"):
        cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert (estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME).is_file()
    assert r19.stage_ids(estate.catalog)[-1] == "S17C"
    monkeypatch.setattr(cm, "_merge_sidecar", cross._never("_merge_sidecar"))
    outcome = cm.run_successor_multipass_final(r19.production_request(estate, stop_after="S18"))
    assert outcome.completed_stage_ids[-1] == "S18"
    unit, statements = _s18(estate)
    assert unit.statement_execution_set is not None
    assert unit.statement_execution_set["selected_path"] == "AUTHENTICATE"
    assert [s["operation"] for s in statements][0] == "path_decision"
    assert not [
        s for s in statements if str(s["operation"]).startswith(("merge_sidecar", "member_deltas"))
    ]
    # A partial sidecar selects no path: the decision is journaled, then the conflict.
    partial_estate = r19.prepare(tmp_path / "partial", legacy=False)
    cm.run_successor_multipass_final(r19.production_request(partial_estate, stop_after="S17C"))
    sidecar = partial_estate.world / COMPACT_EVIDENCE_SIDECAR_FILENAME
    handle = sqlite3.connect(sidecar)
    handle.execute("CREATE TABLE compact_source_evidence (source_observation_id TEXT)")
    handle.close()
    payload = sidecar.read_bytes()
    with pytest.raises(
        cm.ChunkMultipassError, match="preserved exactly as it is and never rebuilt"
    ):
        cm.run_successor_multipass_final(r19.production_request(partial_estate, stop_after="S18"))
    assert sidecar.read_bytes() == payload
    progress = partial_estate.receipt_root / cm.STATEMENT_PROGRESS_DIRECTORY
    partial_plan = cm._read_stored_stage_plan(r19.readonly(partial_estate.catalog))
    s18 = next(stage for stage in partial_plan.stages if stage.stage_id == "S18")
    decisions = sorted(
        (progress / cm._stage_directory_name(s18) / "attempt-000").glob("statement-*.jsonl")
    )
    assert len(decisions) == 1
    reading = wc.read_statement_journal(decisions[0])
    assert reading.status == wc.JOURNAL_SEALED_SUCCESS
    assert reading.events[0]["decision"]["selected_path"] is None
    assert reading.events[0]["decision"]["sidecar_file_state"]["complete"] is False
