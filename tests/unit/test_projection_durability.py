"""Adversarial durability tests for the reconstructible observation projection."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from pathlib import Path

import pytest

from disclosure_drift.errors import CatalogWriteError
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.archive import ArchiveMember
from disclosure_drift.sec.census_completion import CensusCompletionDecision
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    ProjectionFaultPoint,
    rebuild_audit_projection,
    reconcile,
    record_recovery_events,
    validate_audit_projection,
)
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.storage.catalog import CatalogWriter

URL = "https://www.sec.gov/files/company_tickers.json"
BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"


def _observation(index: int) -> SourceObservation:
    return SourceObservation(
        observation_id=f"observation-{index:03d}",
        source_id="sec_company_tickers",
        identity=f"sec_company_tickers:{index}",
        requested_url=URL,
        final_url=URL,
        purpose="offline projection durability fixture",
        retrieved_at_utc=f"2025-01-01T00:00:{index:02d}Z",
        outcome="failed",
        http_status=503,
        attempts=1,
        detail=f"synthetic offline failure {index}",
    )


def _seed_projection(
    writer: CatalogWriter,
    tree: DataTree,
    *,
    count: int = 3,
) -> tuple[ObservationRecorder, tuple[SourceObservation, ...], bytes]:
    recorder = ObservationRecorder(writer, tree)
    observations = tuple(_observation(index) for index in range(count))
    for item in observations:
        recorder.record(item)
    assert recorder.flush_projection() == (count, ())
    return recorder, observations, recorder.audit_path().read_bytes()


def _replace_line(
    original: bytes,
    index: int,
    transform: Callable[[dict[str, object]], dict[str, object]],
) -> bytes:
    lines = original.splitlines(keepends=True)
    payload = json.loads(lines[index])
    assert isinstance(payload, dict)
    lines[index] = (
        json.dumps(transform({str(key): value for key, value in payload.items()}), sort_keys=True)
        + "\n"
    ).encode()
    return b"".join(lines)


def _truncate(original: bytes) -> bytes:
    return original[:-1]


def _malformed_middle(original: bytes) -> bytes:
    lines = original.splitlines(keepends=True)
    lines[1] = b'{"broken":\n'
    return b"".join(lines)


def _malformed_final(original: bytes) -> bytes:
    lines = original.splitlines(keepends=True)
    lines[-1] = b'{"broken":\n'
    return b"".join(lines)


def _valid_prefix(original: bytes) -> bytes:
    return original.splitlines(keepends=True)[0]


def _duplicate_line(original: bytes) -> bytes:
    lines = original.splitlines(keepends=True)
    return original + lines[0]


def _unknown_line(original: bytes) -> bytes:
    return _replace_line(
        original,
        1,
        lambda payload: {**payload, "observation_id": "observation-unknown"},
    )


def _modified_payload(original: bytes) -> bytes:
    return _replace_line(
        original,
        1,
        lambda payload: {**payload, "purpose": "modified after projection"},
    )


def _extra_garbage(original: bytes) -> bytes:
    return original + b"not-json\n"


def _incorrect_order(original: bytes) -> bytes:
    lines = original.splitlines(keepends=True)
    return b"".join((lines[1], lines[0], *lines[2:]))


def _missing_line_identity(original: bytes) -> bytes:
    def remove_identity(payload: dict[str, object]) -> dict[str, object]:
        payload.pop("observation_id")
        return payload

    return _replace_line(original, 1, remove_identity)


@pytest.mark.parametrize(
    ("damage", "condition"),
    (
        (_truncate, "truncated_final_line"),
        (_malformed_middle, "malformed_middle_line"),
        (_malformed_final, "malformed_final_line"),
        (_valid_prefix, "valid_prefix_only"),
        (_duplicate_line, "duplicate_observation_identity"),
        (_unknown_line, "unknown_observation_identity"),
        (_modified_payload, "payload_hash_mismatch"),
        (_extra_garbage, "extra_appended_garbage"),
        (_incorrect_order, "incorrect_ordering"),
        (_missing_line_identity, "missing_observation_identity"),
    ),
)
def test_damaged_projection_is_detected_recorded_and_rebuilt(
    tmp_path: Path,
    damage: Callable[[bytes], bytes],
    condition: str,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, observations, canonical = _seed_projection(writer, tree)
        immutable_before = writer.connection.execute(
            "SELECT observation_id, source_id, request_identity, detail, recorded_at_utc "
            "FROM census_source_observations ORDER BY observation_id"
        ).fetchall()
        recorder.audit_path().write_bytes(damage(canonical))

        report = reconcile(writer.connection, tree)
        assert report.projection_recovery_required
        assert report.projection_validation is not None
        assert condition in report.projection_validation.conditions
        assert report.blocking_reasons()
        event = writer.connection.execute(
            "SELECT * FROM census_projection_recovery_events"
        ).fetchone()
        assert condition in event["detected_condition"]
        assert event["projection_path"] == "audit/sec/census_source_observations.jsonl"
        assert event["resolution_state"] == "blocked"
        assert event["release_blocking_before_resolution"] == 1
        assert event["expected_count"] == len(observations)
        assert event["observed_count"] is not None
        assert event["rebuild_identity"]
        assert event["detected_at_utc"].endswith("Z")
        assert event["resolved_at_utc"] is None

        assert rebuild_audit_projection(writer.connection, recorder.audit_path()) == len(
            observations
        )
        validation = validate_audit_projection(writer.connection, recorder.audit_path())
        recovered_event = writer.connection.execute(
            "SELECT * FROM census_projection_recovery_events"
        ).fetchone()
        immutable_after = writer.connection.execute(
            "SELECT observation_id, source_id, request_identity, detail, recorded_at_utc "
            "FROM census_source_observations ORDER BY observation_id"
        ).fetchall()

    assert validation.is_valid
    assert [tuple(row) for row in immutable_after] == [tuple(row) for row in immutable_before]
    assert recorder.audit_path().read_bytes() == canonical
    assert recovered_event["resolution_state"] == "resolved"
    assert recovered_event["resolved_at_utc"] is not None
    assert recovered_event["projection_sha256"] == hashlib.sha256(canonical).hexdigest()


def test_deleted_projection_is_rebuilt_even_when_every_flag_claims_completion(
    tmp_path: Path,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, observations, canonical = _seed_projection(writer, tree)
        recorder.audit_path().unlink()

        report = reconcile(writer.connection, tree)
        assert report.projection_validation is not None
        assert "missing_projection_file" in report.projection_validation.conditions
        assert "projected_flags_claim_damaged_file" in (report.projection_validation.conditions)
        rebuild_audit_projection(writer.connection, recorder.audit_path())
        flags = writer.connection.execute(
            "SELECT projected_to_audit FROM census_source_observations ORDER BY observation_id"
        ).fetchall()

    assert recorder.audit_path().read_bytes() == canonical
    assert len(flags) == len(observations)
    assert all(row["projected_to_audit"] == 1 for row in flags)


def test_empty_projection_with_projected_rows_is_not_accepted(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, canonical = _seed_projection(writer, tree)
        recorder.audit_path().write_bytes(b"")
        validation = validate_audit_projection(writer.connection, recorder.audit_path())
        assert "empty_file_with_projected_rows" in validation.conditions
        rebuild_audit_projection(writer.connection, recorder.audit_path())
    assert recorder.audit_path().read_bytes() == canonical


def test_append_crash_replays_by_identity_without_duplicate_line(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    fault_points: list[ProjectionFaultPoint] = []

    def crash(point: ProjectionFaultPoint) -> None:
        fault_points.append(point)
        message = "simulated crash after durable append"
        raise RuntimeError(message)

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        item = _observation(0)
        recorder = ObservationRecorder(writer, tree, fault_hook=crash)
        recorder.record(item)
        with pytest.raises(RuntimeError, match="after durable append"):
            recorder.flush_projection()
        durable_bytes = recorder.audit_path().read_bytes()
        flag = writer.connection.execute(
            "SELECT projected_to_audit FROM census_source_observations WHERE observation_id = ?",
            (item.observation_id,),
        ).fetchone()
        assert flag["projected_to_audit"] == 0
        assert fault_points == ["after_append_durable_before_flag"]

        report = reconcile(writer.connection, tree)
        assert "sqlite_projection_flag_stale" in report.projection_validation.conditions
        restarted = ObservationRecorder(writer, tree)
        assert restarted.flush_projection() == (0, ())
        assert restarted.audit_path().read_bytes() == durable_bytes
        assert len(durable_bytes.splitlines()) == 1
        event = writer.connection.execute(
            "SELECT resolution_state, projection_sha256 FROM census_projection_recovery_events"
        ).fetchone()
        assert tuple(event) == (
            "resolved",
            hashlib.sha256(durable_bytes).hexdigest(),
        )


@pytest.mark.parametrize(
    "fault_point",
    (
        "after_rebuild_temporary_durable_before_replace",
        "after_rebuild_replace_before_directory_fsync",
        "after_rebuild_directory_fsync_before_catalog_update",
    ),
)
def test_rebuild_fault_keeps_recovery_blocked_until_durable_retry(
    tmp_path: Path,
    fault_point: ProjectionFaultPoint,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()

    def crash(point: ProjectionFaultPoint) -> None:
        if point == fault_point:
            message = f"simulated {point}"
            raise RuntimeError(message)

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, canonical = _seed_projection(writer, tree)
        recorder.audit_path().write_bytes(b"damaged\n")
        report = reconcile(writer.connection, tree)
        assert report.blocking_reasons()

        with pytest.raises(RuntimeError, match=fault_point):
            rebuild_audit_projection(
                writer.connection,
                recorder.audit_path(),
                fault_hook=crash,
            )
        blocked = writer.connection.execute(
            "SELECT resolution_state FROM census_projection_recovery_events"
        ).fetchone()
        assert blocked["resolution_state"] == "blocked"
        restarted_report = reconcile(writer.connection, tree)
        assert restarted_report.blocking_reasons()

        rebuild_audit_projection(writer.connection, recorder.audit_path())
        resolved = writer.connection.execute(
            "SELECT resolution_state FROM census_projection_recovery_events"
        ).fetchone()

    assert recorder.audit_path().read_bytes() == canonical
    assert resolved["resolution_state"] == "resolved"
    assert tuple(recorder.audit_path().parent.glob(f".{recorder.audit_path().name}.*.tmp")) == ()


@pytest.mark.parametrize("target_scope", ["inside_data_root", "outside_data_root"])
def test_projection_symlink_is_replaced_without_touching_its_target(
    tmp_path: Path,
    target_scope: str,
) -> None:
    tree = DataTree.from_root(tmp_path / "managed")
    tree.ensure_tree()
    target = (
        tree.data_root / "inside-projection-target.jsonl"
        if target_scope == "inside_data_root"
        else tmp_path / "outside-projection-target.jsonl"
    )
    target_bytes = f"{target_scope} file must remain untouched\n".encode()
    target.write_bytes(target_bytes)

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, canonical = _seed_projection(writer, tree)
        recorder.audit_path().unlink()
        recorder.audit_path().symlink_to(target)

        validation = validate_audit_projection(writer.connection, recorder.audit_path())
        assert "unsafe_projection_path" in validation.conditions
        report = reconcile(writer.connection, tree)
        assert report.projection_recovery_required

        rebuild_audit_projection(writer.connection, recorder.audit_path())
        recovered = validate_audit_projection(writer.connection, recorder.audit_path())

    assert recovered.is_valid
    assert not recorder.audit_path().is_symlink()
    assert recorder.audit_path().read_bytes() == canonical
    assert target.read_bytes() == target_bytes


def test_projection_parent_symlink_is_rejected_without_writing_target(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path / "managed")
    tree.ensure_tree()
    outside = tmp_path / "outside-audit-directory"
    outside.mkdir()
    tree.audit.rmdir()
    tree.audit.symlink_to(outside, target_is_directory=True)

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder = ObservationRecorder(writer, tree)
        recorder.record(_observation(0))

        validation = validate_audit_projection(writer.connection, recorder.audit_path())
        assert "unsafe_projection_path" in validation.conditions
        with pytest.raises(CatalogWriteError, match="symbolic link"):
            recorder.flush_projection()
        with pytest.raises(CatalogWriteError, match="symbolic link"):
            rebuild_audit_projection(writer.connection, recorder.audit_path())

    assert tuple(outside.iterdir()) == ()


def test_machine_local_symlink_above_data_root_does_not_block_projection(
    tmp_path: Path,
) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    local_alias = tmp_path / "machine-local-alias"
    local_alias.symlink_to(real_parent, target_is_directory=True)
    tree = DataTree.from_root(local_alias / "managed")
    tree.ensure_tree()

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, canonical = _seed_projection(writer, tree)
        validation = validate_audit_projection(writer.connection, recorder.audit_path())

    assert validation.is_valid
    assert recorder.audit_path().read_bytes() == canonical


def test_successful_rebuild_removes_only_strictly_named_stale_temporaries(
    tmp_path: Path,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, canonical = _seed_projection(writer, tree)
        destination = recorder.audit_path()
        destination.write_bytes(b"damaged\n")
        reconcile(writer.connection, tree)
        stale = destination.parent / f".{destination.name}.{'a' * 32}.tmp"
        near_miss = destination.parent / f".{destination.name}.not-a-rebuild-id.tmp"
        stale.write_bytes(b"abandoned durable rebuild")
        near_miss.write_bytes(b"unrelated file")

        rebuild_audit_projection(writer.connection, destination)

    assert destination.read_bytes() == canonical
    assert not stale.exists()
    assert near_miss.read_bytes() == b"unrelated file"


def test_projection_catalog_updates_are_one_transaction(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    census_run_id = "projection-atomicity-run"
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, observations, canonical = _seed_projection(writer, tree)
        writer.connection.execute(
            "INSERT INTO ops_ingestion_jobs "
            "(job_id, job_kind, job_state, stage, started_at_utc, detail) "
            "VALUES (?, 'sec_census', 'running', 'M2.2-R3', ?, ?)",
            (census_run_id, "2025-01-01T00:00:00Z", "offline atomicity fixture"),
        )
        recorder.audit_path().write_bytes(b"damaged\n")
        writer.connection.execute("UPDATE census_source_observations SET projected_to_audit = 0")
        report = reconcile(writer.connection, tree)
        record_recovery_events(
            writer,
            report.events,
            census_run_id=census_run_id,
        )
        writer.connection.execute(
            "CREATE TRIGGER reject_projection_resolution "
            "BEFORE UPDATE OF resolution_state ON census_recovery_states "
            "WHEN NEW.resolution_state = 'resolved' "
            "BEGIN SELECT RAISE(ABORT, 'synthetic recovery update failure'); END"
        )

        with pytest.raises(sqlite3.IntegrityError, match="synthetic recovery update failure"):
            rebuild_audit_projection(
                writer.connection,
                recorder.audit_path(),
                census_run_id=census_run_id,
            )

        flags_after_failure = writer.connection.execute(
            "SELECT projected_to_audit FROM census_source_observations ORDER BY observation_id"
        ).fetchall()
        dedicated_after_failure = writer.connection.execute(
            "SELECT resolution_state FROM census_projection_recovery_events"
        ).fetchall()
        generic_after_failure = writer.connection.execute(
            "SELECT resolution_state FROM census_recovery_states "
            "WHERE census_run_id = ? AND scenario = 'audit_projection_interrupted'",
            (census_run_id,),
        ).fetchall()
        writer.connection.execute("DROP TRIGGER reject_projection_resolution")

        rebuild_audit_projection(
            writer.connection,
            recorder.audit_path(),
            census_run_id=census_run_id,
        )
        flags_after_retry = writer.connection.execute(
            "SELECT projected_to_audit FROM census_source_observations ORDER BY observation_id"
        ).fetchall()
        dedicated_after_retry = writer.connection.execute(
            "SELECT resolution_state FROM census_projection_recovery_events"
        ).fetchall()
        generic_after_retry = writer.connection.execute(
            "SELECT resolution_state FROM census_recovery_states "
            "WHERE census_run_id = ? AND scenario = 'audit_projection_interrupted'",
            (census_run_id,),
        ).fetchall()

    assert recorder.audit_path().read_bytes() == canonical
    assert len(flags_after_failure) == len(observations)
    assert {row["projected_to_audit"] for row in flags_after_failure} == {0}
    assert {row["resolution_state"] for row in dedicated_after_failure} == {"blocked"}
    assert {row["resolution_state"] for row in generic_after_failure} == {"blocked"}
    assert {row["projected_to_audit"] for row in flags_after_retry} == {1}
    assert {row["resolution_state"] for row in dedicated_after_retry} == {"resolved"}
    assert {row["resolution_state"] for row in generic_after_retry} == {"resolved"}


def test_repeated_rebuild_is_byte_identical_and_restart_is_clean(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, observations, _ = _seed_projection(writer, tree)
        assert rebuild_audit_projection(writer.connection, recorder.audit_path()) == len(
            observations
        )
        first = recorder.audit_path().read_bytes()
        first_hash = hashlib.sha256(first).hexdigest()
        assert rebuild_audit_projection(writer.connection, recorder.audit_path()) == len(
            observations
        )
        second = recorder.audit_path().read_bytes()
        second_hash = hashlib.sha256(second).hexdigest()

    with CatalogWriter(tree.catalog_database, tree.locks) as restarted:
        restarted.migrate()
        validation = validate_audit_projection(restarted.connection, recorder.audit_path())
        report = reconcile(restarted.connection, tree)

    assert first == second
    assert first_hash == second_hash
    assert validation.is_valid
    assert not report.projection_recovery_required
    assert not report.blocking_reasons()


def test_recovery_block_clears_only_after_successful_durable_rebuild(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        recorder, _, _ = _seed_projection(writer, tree)
        recorder.audit_path().write_bytes(b'{"observation_id":"observation-000"}')
        before = reconcile(writer.connection, tree)
        assert before.blocking_reasons()
        blocked_completion = CensusCompletionDecision(
            sources=(),
            recovery_passed=False,
            recovery_blocking_reasons=before.blocking_reasons(),
            sqlite_integrity_passed=True,
            release_blocking_reason_count=0,
            qa_report_written=True,
            audit_projection_complete=False,
        )
        assert not blocked_completion.completed
        event_before = writer.connection.execute(
            "SELECT resolution_state, release_blocking_before_resolution "
            "FROM census_projection_recovery_events"
        ).fetchone()
        assert tuple(event_before) == ("blocked", 1)

        rebuild_audit_projection(writer.connection, recorder.audit_path())
        after = reconcile(writer.connection, tree)
        recovered_completion = CensusCompletionDecision(
            sources=(),
            recovery_passed=not after.blocking_reasons(),
            recovery_blocking_reasons=after.blocking_reasons(),
            sqlite_integrity_passed=True,
            release_blocking_reason_count=0,
            qa_report_written=True,
            audit_projection_complete=not after.projection_recovery_required,
        )
        event_after = writer.connection.execute(
            "SELECT resolution_state, release_blocking_before_resolution "
            "FROM census_projection_recovery_events"
        ).fetchone()

    assert not after.blocking_reasons()
    assert recovered_completion.completed
    assert tuple(event_after) == ("resolved", 1)


def test_bulk_archive_reuse_copies_member_hash_lineage_for_identical_and_304(
    tmp_path: Path,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    store = SnapshotStore(tree)
    payload = b"PK\x03\x04synthetic-offline-archive"
    prior = store.record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_bulk_submissions",
            url=BULK_URL,
            purpose="offline archive lineage fixture",
            status=200,
            body=payload,
            etag='"archive-v1"',
            declared_content_type="application/zip",
            attempts=1,
        )
    )
    identical = store.record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_bulk_submissions",
            url=BULK_URL,
            purpose="offline archive lineage fixture",
            status=200,
            body=payload,
            etag='"archive-v1"',
            declared_content_type="application/zip",
            attempts=1,
        )
    )
    reused = store.record(
        FetchResult(
            outcome="not_modified",
            source_id="sec_bulk_submissions",
            url=BULK_URL,
            purpose="offline archive lineage fixture",
            status=304,
            identity=prior.identity,
            sent_etag=prior.etag,
            attempts=1,
        )
    )
    assert prior.relative_storage_path is not None
    assert prior.logical_sha256 is not None
    member = ArchiveMember(
        name="CIK0000000001.json",
        compressed_size=10,
        uncompressed_size=20,
        payload=b'{"cik":"1"}',
        archive_relative_path=prior.relative_storage_path,
        archive_sha256=prior.logical_sha256,
    )
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        recorder = ObservationRecorder(writer, tree)
        recorder.record(prior, members=(member,))
        recorder.record(identical)
        recorder.record(reused)
        rows = writer.connection.execute(
            "SELECT observation_id, member_name, member_sha256, archive_sha256 "
            "FROM census_archive_members ORDER BY observation_id"
        ).fetchall()

    assert len(rows) == 3
    assert {row["observation_id"] for row in rows} == {
        prior.observation_id,
        identical.observation_id,
        reused.observation_id,
    }
    assert {row["member_sha256"] for row in rows} == {member.member_sha256}
    assert {row["archive_sha256"] for row in rows} == {prior.logical_sha256}


@pytest.mark.parametrize("prior_member_state", ["missing", "mismatched"])
def test_bulk_archive_reuse_refuses_missing_or_mismatched_member_lineage(
    tmp_path: Path,
    prior_member_state: str,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    store = SnapshotStore(tree)
    payload = b"PK\x03\x04synthetic-offline-archive"
    prior = store.record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_bulk_submissions",
            url=BULK_URL,
            purpose="offline archive lineage fixture",
            status=200,
            body=payload,
            declared_content_type="application/zip",
            attempts=1,
        )
    )
    reused = store.record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_bulk_submissions",
            url=BULK_URL,
            purpose="offline archive lineage fixture",
            status=200,
            body=payload,
            declared_content_type="application/zip",
            attempts=1,
        )
    )
    assert prior.relative_storage_path is not None
    assert prior.logical_sha256 is not None
    members = (
        ()
        if prior_member_state == "missing"
        else (
            ArchiveMember(
                name="CIK0000000001.json",
                compressed_size=10,
                uncompressed_size=20,
                payload=b'{"cik":"1"}',
                archive_relative_path=prior.relative_storage_path,
                archive_sha256="0" * 64,
            ),
        )
    )
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        recorder = ObservationRecorder(writer, tree)
        recorder.record(prior, members=members)
        with pytest.raises(CatalogWriteError, match="archive"):
            recorder.record(reused)
        assert (
            writer.connection.execute("SELECT COUNT(*) FROM census_source_observations").fetchone()[
                0
            ]
            == 1
        )
