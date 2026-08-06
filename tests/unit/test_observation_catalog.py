"""Authoritative observation catalog, projection, lineage, and restart recovery."""

from __future__ import annotations

import io
import json
import sqlite3
import zipfile
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from disclosure_drift.paths import DataTree
from disclosure_drift.sec.archive import ArchiveMember
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    load_observations,
    rebuild_audit_projection,
    reconcile,
)
from disclosure_drift.sec.raw_store import RawStore
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import CatalogWriter

URL = "https://www.sec.gov/files/company_tickers.json"


def observation(tree: DataTree) -> SourceObservation:
    return SnapshotStore(tree).record(
        FetchResult(
            outcome="retrieved",
            source_id="sec_company_tickers",
            url=URL,
            purpose="census ticker alias evidence",
            status=200,
            body=b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}',
            etag='"fixture"',
            declared_content_type="application/json",
            attempts=1,
        )
    )


def test_catalog_is_authoritative_and_projection_is_recoverable(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        item = observation(tree)
        recorder = ObservationRecorder(writer, tree)
        recorder.record(item)

        report = reconcile(writer.connection, tree)
        assert report.unprojected_observations == (item.observation_id,)
        assert "audit_projection_interrupted" in report.by_scenario()
        assert report.blocking_reasons()

        destination = tree.audit / "rebuilt.jsonl"
        assert rebuild_audit_projection(writer.connection, destination) == 1
        recovered = load_observations(writer.connection)

    assert recovered == (item,)
    assert json.loads(destination.read_text(encoding="utf-8"))["observation_id"] == (
        item.observation_id
    )


def test_projection_flush_marks_only_committed_rows_projected(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        item = observation(tree)
        recorder = ObservationRecorder(writer, tree)
        recorder.record(item)
        written, remaining = recorder.flush_projection()
        row = writer.connection.execute(
            "SELECT projected_to_audit FROM census_source_observations WHERE observation_id = ?",
            (item.observation_id,),
        ).fetchone()
    assert written == 1
    assert remaining == ()
    assert row["projected_to_audit"] == 1


def test_archive_member_lineage_is_atomic_with_observation(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        item = observation(tree)
        member = ArchiveMember(
            name="CIK0000000001.json",
            compressed_size=10,
            uncompressed_size=20,
            payload=b'{"cik":"1"}',
            archive_relative_path="raw/sec/bulk/fixture.zip",
            archive_sha256="a" * 64,
        )
        recorder = ObservationRecorder(writer, tree)
        recorder.record(item, members=(member,))
        row = writer.connection.execute(
            "SELECT member_name, member_sha256, archive_sha256 "
            "FROM census_archive_members WHERE observation_id = ?",
            (item.observation_id,),
        ).fetchone()
        with pytest.raises(Exception, match="already recorded"):
            recorder.record(item)
    assert row["member_name"] == member.name
    assert row["member_sha256"] == member.member_sha256
    assert row["archive_sha256"] == "a" * 64


class _SingleUseMembers:
    """An archive-member source that refuses everything except one forward pass.

    A recorder that quietly called ``tuple()``, ``len()``, or indexed its input would still
    persist correct rows, so a row-shape assertion cannot tell a streaming recorder from a
    materializing one. This can: every operation that implies materialization raises, and a
    second ``__iter__`` raises too, so the only way the recorder can succeed is by iterating
    exactly once and holding nothing.
    """

    def __init__(self, members: tuple[ArchiveMember, ...]) -> None:
        self._members = members
        self.iterations = 0
        self.yielded = 0

    def __iter__(self) -> Iterator[ArchiveMember]:
        self.iterations += 1
        if self.iterations > 1:
            message = "the member source was iterated more than once"
            raise AssertionError(message)
        for member in self._members:
            self.yielded += 1
            yield member

    def __len__(self) -> int:
        message = "the member source was measured with len()"
        raise AssertionError(message)

    def __getitem__(self, index: object) -> ArchiveMember:
        message = "the member source was accessed by index"
        raise AssertionError(message)


def _archive_bytes() -> bytes:
    """A minimal, byte-stable ZIP. Explicit metadata keeps it independent of the clock."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("CIK0000000001.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_STORED
        info.create_system = 3
        info.external_attr = 0o600 << 16
        archive.writestr(info, '{"cik":1}')
    return buffer.getvalue()


def _archive_fetch() -> FetchResult:
    return FetchResult(
        outcome="retrieved",
        source_id="sec_bulk_submissions",
        url=SOURCES["sec_bulk_submissions"].url(),
        purpose="census bulk submissions archive evidence",
        status=200,
        body=_archive_bytes(),
        declared_content_type="application/zip",
        attempts=1,
    )


def _member(index: int, *, archive_sha: str = "a" * 64) -> ArchiveMember:
    return ArchiveMember(
        name=f"CIK{index:010d}.json",
        compressed_size=10 + index,
        uncompressed_size=20 + index,
        payload=f'{{"cik":{index}}}'.encode(),
        archive_relative_path="raw/sec/bulk/fixture.zip",
        archive_sha256=archive_sha,
        member_index=index,
    )


def _member_rows(writer: CatalogWriter, observation_id: str) -> list[tuple[object, ...]]:
    return [
        tuple(row)
        for row in writer.connection.execute(
            "SELECT member_index, member_name FROM census_archive_members "
            "WHERE observation_id = ? ORDER BY rowid",
            (observation_id,),
        ).fetchall()
    ]


@pytest.fixture
def recorder_writer(tmp_path: Path) -> Iterator[tuple[CatalogWriter, DataTree]]:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        yield writer, tree


@pytest.mark.parametrize("shape", ["list", "tuple", "generator"])
def test_archive_members_accept_every_supported_input_shape(
    recorder_writer: tuple[CatalogWriter, DataTree],
    shape: str,
) -> None:
    """Existing sequence callers keep working, and a one-shot generator now works too."""
    writer, tree = recorder_writer
    item = observation(tree)
    members = (_member(0), _member(1))
    supplied: object = {
        "list": list(members),
        "tuple": members,
        "generator": (member for member in members),
    }[shape]
    ObservationRecorder(writer, tree).record(item, members=supplied)  # type: ignore[arg-type]
    assert _member_rows(writer, item.observation_id) == [
        (0, "CIK0000000000.json"),
        (1, "CIK0000000001.json"),
    ]


def test_archive_members_are_consumed_exactly_once_and_never_materialized(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """The defensive source proves no len, no indexing, and no second pass."""
    writer, tree = recorder_writer
    item = observation(tree)
    source = _SingleUseMembers((_member(0), _member(1), _member(2)))
    ObservationRecorder(writer, tree).record(item, members=source)
    assert source.iterations == 1
    assert source.yielded == 3
    assert len(_member_rows(writer, item.observation_id)) == 3


def test_member_rows_are_written_while_the_source_is_still_being_consumed(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """Streaming, proved from inside the transaction rather than inferred from the result.

    At the moment member ``k`` is yielded, rows ``0..k-1`` must already be visible on the
    writer's own connection. A recorder that built the whole row set before opening its
    transaction would show nothing at all here, so this fails against materialization even
    though the committed rows would look identical.
    """
    writer, tree = recorder_writer
    item = observation(tree)
    visible_at_yield: list[int] = []

    def _members() -> Iterator[ArchiveMember]:
        for index in range(4):
            visible_at_yield.append(
                writer.connection.execute(
                    "SELECT count(*) AS n FROM census_archive_members WHERE observation_id = ?",
                    (item.observation_id,),
                ).fetchone()["n"]
            )
            yield _member(index)

    ObservationRecorder(writer, tree).record(item, members=_members())
    assert visible_at_yield == [0, 1, 2, 3], "each row lands before the next member is read"
    assert len(_member_rows(writer, item.observation_id)) == 4


def test_member_rows_keep_the_source_order(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """Rows are persisted in generator order; no sort is applied and none is needed."""
    writer, tree = recorder_writer
    item = observation(tree)
    ordered = (_member(0), _member(1), _member(2), _member(3))
    ObservationRecorder(writer, tree).record(item, members=iter(ordered))
    assert _member_rows(writer, item.observation_id) == [
        (index, f"CIK{index:010d}.json") for index in range(4)
    ]


def test_an_empty_member_source_records_the_observation_with_no_lineage(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """Emptiness is lawful at this layer; whether it is lawful for a route is not its call."""
    writer, tree = recorder_writer
    item = observation(tree)
    ObservationRecorder(writer, tree).record(item, members=iter(()))
    assert _member_rows(writer, item.observation_id) == []
    assert load_observations(writer.connection)[0].observation_id == item.observation_id


def test_a_late_member_failure_rolls_back_the_observation_and_every_row(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """Failing at member three must leave nothing at all — not two rows, not the observation."""
    writer, tree = recorder_writer
    item = observation(tree)
    recorder = ObservationRecorder(writer, tree)

    def _fails_late() -> Iterator[ArchiveMember]:
        yield _member(0)
        yield _member(1)
        message = "the archive reader failed partway through enumeration"
        raise RuntimeError(message)

    with pytest.raises(RuntimeError, match="partway through enumeration"):
        recorder.record(item, members=_fails_late())

    assert _member_rows(writer, item.observation_id) == []
    assert load_observations(writer.connection) == ()
    assert recorder.unprojected() == (), "a rolled-back observation is never queued to project"
    # The rollback is complete, so the same identity may still be recorded lawfully.
    recorder.record(item)
    assert load_observations(writer.connection)[0].observation_id == item.observation_id


def test_a_member_insert_failure_rolls_back_the_observation_and_prior_rows(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """The same guarantee when the database, not the source, is what fails."""
    writer, tree = recorder_writer
    item = observation(tree)
    # The second member's index is not an integer, which the STRICT table refuses outright —
    # a database-side failure reached only after the first member's row is already inserted.
    # (A NOT NULL or PRIMARY KEY violation would not do: ``INSERT OR IGNORE`` swallows those,
    # so the row would be dropped silently and nothing would roll back.)
    malformed = (_member(0), replace(_member(1), member_index="two"))  # type: ignore[arg-type]
    recorder = ObservationRecorder(writer, tree)
    with pytest.raises(sqlite3.DatabaseError, match="cannot store TEXT value in INTEGER column"):
        recorder.record(item, members=iter(malformed))
    assert _member_rows(writer, item.observation_id) == []
    assert load_observations(writer.connection) == ()


def test_member_payload_bytes_are_never_persisted(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """Only identity, hash, and sizes are stored — the payload itself is never written."""
    writer, tree = recorder_writer
    item = observation(tree)
    marker = b"canary-member-payload-marker"
    member = replace(_member(0), payload=marker)
    ObservationRecorder(writer, tree).record(item, members=iter((member,)))
    stored = writer.connection.execute(
        "SELECT * FROM census_archive_members WHERE observation_id = ?",
        (item.observation_id,),
    ).fetchone()
    assert marker.decode() not in " ".join(str(value) for value in tuple(stored))
    assert stored["member_sha256"] == member.member_sha256


def test_reuse_without_explicit_members_persists_the_preserved_owner_lineage(
    recorder_writer: tuple[CatalogWriter, DataTree],
) -> None:
    """The normal archive-reuse path: no members supplied, prior evidence carried forward.

    Both observations come from the real snapshot store over the same archive bytes, so the
    reuse edge carries the complete provenance the accepted catalog triggers require. A
    hand-built pair would prove only that a forged row can be inserted.
    """
    writer, tree = recorder_writer
    store = SnapshotStore(tree)
    owner = store.record(_archive_fetch())
    reuse = store.record(_archive_fetch())
    assert owner.outcome == "stored_new"
    assert reuse.outcome == "unchanged_content"
    assert reuse.reused_observation_id == owner.observation_id

    recorder = ObservationRecorder(writer, tree)
    lineage = replace(
        _member(0),
        archive_relative_path=owner.relative_storage_path,
        archive_sha256=owner.logical_sha256,
    )
    recorder.record(owner, members=iter((lineage,)))
    recorder.record(reuse)
    assert _member_rows(writer, reuse.observation_id) == [(0, "CIK0000000000.json")]


def test_reconcile_detects_missing_and_orphan_raw_objects(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        item = observation(tree)
        ObservationRecorder(writer, tree).record(item)
        assert item.relative_storage_path is not None
        (tree.data_root / item.relative_storage_path).unlink()
        orphan = tree.raw_indexes / "orphan.json"
        orphan.write_bytes(b"orphan")
        partial = tree.staging / "interrupted.part"
        partial.write_bytes(b"partial")
        scenarios = reconcile(writer.connection, tree).by_scenario()
    assert scenarios["catalog_row_without_object"] == 1
    assert scenarios["object_without_catalog_row"] == 1
    assert scenarios["interrupted_part_download"] == 1
    assert not partial.exists()
    assert list(tree.quarantine.glob("*__interrupted.part"))
    assert not orphan.exists()


def test_valid_orphan_is_adopted_only_from_verified_lineage(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        writer.seed_reference_data()
        item = observation(tree)
        report = reconcile(writer.connection, tree)
        row = writer.connection.execute(
            "SELECT source_id, stored_sha256, projected_to_audit "
            "FROM census_source_observations WHERE observation_id = ?",
            (item.observation_id,),
        ).fetchone()
    adopted = [event for event in report.events if event.action_taken == "adopted_verified"]
    assert len(adopted) == 1
    assert row["source_id"] == item.source_id
    assert row["stored_sha256"] == item.stored_sha256
    assert row["projected_to_audit"] == 0
    assert not report.blocking_reasons(projection_rebuilt=True)


def test_unproven_orphan_is_quarantined_not_adopted(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    orphan = tree.raw_indexes / "unproven.json"
    orphan.write_bytes(b"unproven")
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        report = reconcile(writer.connection, tree)
        count = writer.connection.execute(
            "SELECT COUNT(*) FROM census_source_observations"
        ).fetchone()[0]
    assert count == 0
    assert not orphan.exists()
    assert any(event.action_taken == "quarantined_unproven" for event in report.events)
    assert list(tree.quarantine.glob("*__unproven.json"))


def test_orphan_with_forged_request_identity_is_quarantined(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    item = observation(tree)
    assert item.relative_storage_path is not None
    object_path = tree.data_root / item.relative_storage_path
    lineage_path = RawStore.lineage_path(object_path)
    lineage = json.loads(lineage_path.read_text(encoding="utf-8"))
    lineage["identity"] = str(lineage["identity"]) + "forged=yes"
    lineage_path.write_text(json.dumps(lineage), encoding="utf-8")

    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        report = reconcile(writer.connection, tree)
        count = writer.connection.execute(
            "SELECT COUNT(*) FROM census_source_observations"
        ).fetchone()[0]
    assert count == 0
    assert any(event.action_taken == "quarantined_unproven" for event in report.events)
    assert not object_path.exists()


def test_tampered_raw_object_is_an_unresolved_recovery_blocker(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        item = observation(tree)
        ObservationRecorder(writer, tree).record(item)
        assert item.relative_storage_path is not None
        (tree.data_root / item.relative_storage_path).write_bytes(b"tampered")
        report = reconcile(writer.connection, tree)
    assert report.blocking_reasons()
    assert any(
        event.observation_id == item.observation_id and event.resolution_state == "blocked"
        for event in report.events
    )


def test_storage_representation_mismatch_blocks_recovery(tmp_path: Path) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        item = observation(tree)
        ObservationRecorder(writer, tree).record(item)
        writer.connection.execute(
            "UPDATE census_source_observations SET storage_representation = 'identical' "
            "WHERE observation_id = ?",
            (item.observation_id,),
        )
        report = reconcile(writer.connection, tree)
    assert report.blocking_reasons()
    assert any("representation" in event.detail for event in report.events)


def test_unsafe_catalog_object_path_blocks_recovery_without_external_read(
    tmp_path: Path,
) -> None:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    with CatalogWriter(tree.catalog_database, tree.locks) as writer:
        writer.migrate()
        item = observation(tree)
        ObservationRecorder(writer, tree).record(item)
        assert item.relative_storage_path is not None
        absolute = str(tree.data_root / item.relative_storage_path)
        writer.connection.execute(
            "UPDATE census_source_observations SET relative_storage_path = ? "
            "WHERE observation_id = ?",
            (absolute, item.observation_id),
        )
        report = reconcile(writer.connection, tree)
    assert report.blocking_reasons()
    assert any("unsafe" in event.detail for event in report.events)
