"""Authoritative observation catalog, projection, lineage, and restart recovery."""

from __future__ import annotations

import json
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
