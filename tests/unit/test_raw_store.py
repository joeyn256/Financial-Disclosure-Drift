"""Atomic raw-object storage, integrity, quarantine, and crash recovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.raw_store import (
    LINEAGE_SUFFIX,
    RawStore,
    compress_deterministically,
    decompress,
    sha256_of,
)

CIK = "0000320193"
ACCESSION = "000032019324000123"
NOW = "2026-07-26T12:00:00Z"
BODY = b"<SEC-HEADER>\nFILED AS OF DATE:\t\t20240215\n</SEC-HEADER>\nbody\r\n"


@pytest.fixture
def store(tmp_path: Path) -> RawStore:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    return RawStore(tree)


def _store(store: RawStore, body: bytes = BODY, **overrides: object) -> object:
    arguments: dict[str, object] = {
        "chunks": [body],
        "logical_role": "complete_submission",
        "source_url_canonical": "https://www.sec.gov/Archives/edgar/data/320193/x.txt",
        "retrieval_attempt_id": "attempt-1",
        "retrieved_at_utc": NOW,
        "filename": "0000320193-24-000123.txt",
        "accession_plain": ACCESSION,
        "cik_padded": CIK,
        "media_type": "text/plain",
    }
    arguments.update(overrides)
    return store.store(**arguments)  # type: ignore[arg-type]


def test_object_is_accession_addressed_and_path_is_relative(store: RawStore) -> None:
    stored = _store(store)
    assert stored.record.relative_storage_path.startswith(f"raw/sec/filings/{CIK}/{ACCESSION}/")
    assert not Path(stored.record.relative_storage_path).is_absolute()
    assert stored.absolute_path.is_file()


def test_content_hash_covers_decoded_bytes(store: RawStore) -> None:
    stored = _store(store)
    assert stored.record.content_sha256 == sha256_of(BODY)
    assert stored.record.stored_sha256 == sha256_of(stored.absolute_path.read_bytes())
    assert stored.record.content_size_bytes == len(BODY)
    assert stored.record.compression == "none"


def test_bytes_are_not_normalized(store: RawStore) -> None:
    stored = _store(store)
    assert stored.absolute_path.read_bytes() == BODY
    assert b"\r\n" in stored.absolute_path.read_bytes()


def test_deterministic_gzip_round_trip(store: RawStore) -> None:
    stored = _store(store, compress=True, filename="doc.txt")
    raw = stored.absolute_path.read_bytes()
    assert stored.absolute_path.name.endswith(".gz")
    assert stored.record.compression == "gzip"
    assert decompress(raw) == BODY
    assert sha256_of(decompress(raw)) == stored.record.content_sha256
    assert compress_deterministically(BODY) == compress_deterministically(BODY)


def test_no_part_file_survives_a_successful_store(store: RawStore) -> None:
    stored = _store(store)
    siblings = list(stored.absolute_path.parent.iterdir())
    assert not [path for path in siblings if path.name.endswith(".part")]


def test_interrupted_stream_leaves_a_part_file_and_no_final_object(store: RawStore) -> None:
    def interrupt() -> None:
        message = "connection reset mid-stream"
        raise ConnectionResetError(message)

    with pytest.raises(ConnectionResetError):
        _store(store, raise_during_stream=interrupt)

    directory = store._tree.accession_directory(CIK, ACCESSION)  # noqa: SLF001
    files = list(directory.iterdir())
    assert files, "the partial transfer must be preserved for reconciliation"
    assert all(path.name.endswith(".part") for path in files)


def test_crash_after_promotion_leaves_a_valid_orphan(store: RawStore) -> None:
    with pytest.raises(RawObjectIntegrityError, match="simulated crash"):
        _store(store, fail_after="promotion")

    directory = store._tree.accession_directory(CIK, ACCESSION)  # noqa: SLF001
    promoted = [
        path for path in directory.iterdir() if not path.name.endswith((".part", LINEAGE_SUFFIX))
    ]
    assert len(promoted) == 1
    assert promoted[0].read_bytes() == BODY


def test_catalog_independent_reconciliation_quarantines_unproven_orphans(
    store: RawStore,
) -> None:
    with pytest.raises(RawObjectIntegrityError):
        _store(store, fail_after="promotion")

    def interrupt() -> None:
        message = "interrupted"
        raise TimeoutError(message)

    with pytest.raises(TimeoutError):
        _store(store, filename="other.txt", raise_during_stream=interrupt)

    report = store.reconcile(known=[])
    assert report.adopted == ()
    assert len(report.quarantined) == 2
    assert all(path.startswith("raw/sec/quarantine/") for path in report.quarantined)
    assert not report.is_clean
    assert not report.missing_files


def test_reconciliation_reports_catalog_rows_without_files(store: RawStore) -> None:
    stored = _store(store)
    stored.absolute_path.unlink()
    report = store.reconcile(known=[stored.record])
    assert report.missing_files == (stored.record.relative_storage_path,)


def test_reconciliation_is_clean_when_everything_matches(store: RawStore) -> None:
    stored = _store(store)
    assert store.reconcile(known=[stored.record]).is_clean


def test_changed_remote_content_becomes_a_new_observation(store: RawStore) -> None:
    first = _store(store)
    changed = _store(
        store,
        body=BODY + b"amended\n",
        filename="0000320193-24-000123-v2.txt",
        known_observations=[first.record],
        retrieved_at_utc="2026-07-27T12:00:00Z",
    )
    assert changed.record.supersedes_observation_id == first.record.observation_id
    assert changed.record.reason_code == "REMOTE_CONTENT_CHANGED"
    assert changed.record.is_new_observation_of_changed_content
    assert first.absolute_path.read_bytes() == BODY, "the earlier observation is untouched"


def test_identical_content_is_not_treated_as_a_change(store: RawStore) -> None:
    first = _store(store)
    again = _store(
        store,
        filename="second-fetch.txt",
        known_observations=[first.record],
        retrieved_at_utc="2026-07-27T12:00:00Z",
    )
    assert again.record.supersedes_observation_id is None
    assert again.record.reason_code is None


def test_conflicting_existing_destination_is_never_overwritten(store: RawStore) -> None:
    first = _store(store)
    with pytest.raises(RawObjectIntegrityError, match="refusing to overwrite"):
        _store(store, body=BODY + b"changed", filename=first.absolute_path.name)
    assert first.absolute_path.read_bytes() == BODY
    assert list(first.absolute_path.parent.glob("*.part"))


def test_verify_detects_local_corruption(store: RawStore) -> None:
    stored = _store(store)
    assert store.verify(stored.record)
    stored.absolute_path.write_bytes(b"tampered")
    assert not store.verify(stored.record)


def test_quarantine_preserves_the_file_and_records_a_reason(store: RawStore) -> None:
    stored = _store(store)
    target = store.quarantine(stored.absolute_path, "RAW_FILE_CHECKSUM_MISMATCH", "hash mismatch")
    assert target.is_file()
    assert target.read_bytes() == BODY
    assert "RAW_FILE_CHECKSUM_MISMATCH" in target.with_suffix(target.suffix + ".reason").read_text()
    assert not stored.absolute_path.exists(), "the damaged file is moved, never duplicated"
