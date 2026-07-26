"""Immutable source observations: hashing, conditional reuse, supersession, quarantine."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.raw_store import sha256_of
from disclosure_drift.sec.snapshots import (
    SnapshotStore,
    SourceObservation,
    observations_by_outcome,
)

TICKERS = "sec_company_tickers_exchange"
BULK = "sec_bulk_submissions"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
BODY_ONE = b'{"0":{"cik_str":1,"ticker":"SYN"}}'
BODY_TWO = b'{"0":{"cik_str":1,"ticker":"SYN2"}}'


@pytest.fixture
def store(tmp_path: Path) -> SnapshotStore:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    return SnapshotStore(tree)


def retrieved(**overrides: object) -> FetchResult:
    values: dict[str, object] = {
        "outcome": "retrieved",
        "source_id": TICKERS,
        "url": TICKERS_URL,
        "purpose": "census alias evidence",
        "status": 200,
        "body": BODY_ONE,
        "etag": 'W/"snap-1"',
        "last_modified": "Wed, 01 Jul 2026 00:00:00 GMT",
        "declared_content_type": "application/json",
        "attempts": 1,
    }
    values.update(overrides)
    return FetchResult(**values)  # type: ignore[arg-type]


def failed(**overrides: object) -> FetchResult:
    values: dict[str, object] = {
        "outcome": "failed",
        "source_id": TICKERS,
        "url": TICKERS_URL,
        "purpose": "census alias evidence",
        "status": 200,
        "reason_code": "SEC_RESPONSE_EMPTY",
        "detail": "empty body; a failure never becomes a valid empty result",
        "attempts": 1,
    }
    values.update(overrides)
    return FetchResult(**values)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# First observation
# --------------------------------------------------------------------------- #
def test_first_retrieval_stores_a_new_observation(store: SnapshotStore) -> None:
    observation = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    assert isinstance(observation, SourceObservation)
    assert observation.outcome == "stored_new"
    assert observation.content_sha256 == sha256_of(BODY_ONE)
    assert observation.transport_sha256 == observation.content_sha256
    assert observation.content_size_bytes == len(BODY_ONE)
    assert observation.parser_version == "company-tickers-exchange/1.0"
    assert observation.retrieved_at_utc == "2026-07-26T00:00:00Z"
    assert observation.is_usable


def test_only_relative_paths_are_persisted(store: SnapshotStore) -> None:
    observation = store.record(retrieved())
    assert observation.relative_storage_path is not None
    assert observation.relative_storage_path.startswith("raw/sec/")
    assert not Path(observation.relative_storage_path).is_absolute()
    assert "/Users/" not in json.dumps(dict(observation.as_record()))


def test_provenance_headers_are_persisted(store: SnapshotStore) -> None:
    observation = store.record(retrieved())
    assert observation.etag == 'W/"snap-1"'
    assert observation.last_modified == "Wed, 01 Jul 2026 00:00:00 GMT"
    assert observation.headers["etag"] == 'W/"snap-1"'
    assert observation.headers["content-type"] == "application/json"


def test_no_request_headers_are_ever_stored(store: SnapshotStore) -> None:
    observation = store.record(retrieved())
    stored = json.dumps(dict(observation.as_record())).lower()
    assert "user-agent" not in stored
    assert "your-institution" not in stored


def test_stored_payload_verifies_against_its_recorded_hash(store: SnapshotStore) -> None:
    observation = store.record(retrieved())
    assert store.load_payload(observation) == BODY_ONE


def test_tampered_payload_is_detected(store: SnapshotStore) -> None:
    observation = store.record(retrieved())
    store.payload_path(observation).write_bytes(b"tampered")
    with pytest.raises(RawObjectIntegrityError, match="does not match"):
        store.load_payload(observation)


def test_snapshot_index_supplies_conditional_request_inputs(store: SnapshotStore) -> None:
    empty = store.latest_for(TICKERS)
    assert not empty.has_snapshot
    store.record(retrieved())
    index = store.latest_for(TICKERS)
    assert index.has_snapshot
    assert index.etag == 'W/"snap-1"'
    assert index.last_modified is not None
    assert index.content_sha256 == sha256_of(BODY_ONE)


# --------------------------------------------------------------------------- #
# Repeat retrieval
# --------------------------------------------------------------------------- #
def test_identical_content_reuses_the_object_and_records_a_new_observation(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    second = store.record(retrieved(), retrieved_at_utc="2026-07-27T00:00:00Z")
    assert second.outcome == "unchanged_content"
    assert second.relative_storage_path == first.relative_storage_path
    assert second.observation_id != first.observation_id
    assert second.retrieved_at_utc != first.retrieved_at_utc
    assert second.storage_representation == first.storage_representation
    assert second.stored_size_bytes == first.stored_size_bytes
    assert second.content_size_bytes == first.content_size_bytes
    assert len(store.observations) == 2


def test_changed_content_supersedes_without_overwriting(store: SnapshotStore) -> None:
    first = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    changed = store.record(
        retrieved(body=BODY_TWO, etag='W/"snap-2"'),
        retrieved_at_utc="2026-07-28T00:00:00Z",
    )
    assert changed.outcome == "superseded"
    assert changed.supersedes_observation_id == first.observation_id
    assert "SOURCE_CONTENT_UPDATED" in changed.reason_codes
    assert changed.relative_storage_path != first.relative_storage_path
    assert store.load_payload(first) == BODY_ONE
    assert store.load_payload(changed) == BODY_TWO


def test_not_modified_records_a_reused_snapshot(store: SnapshotStore) -> None:
    first = store.record(retrieved())
    reused = store.record(
        FetchResult(
            outcome="not_modified",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=304,
            etag='W/"snap-1"',
            identity=first.identity,
            sent_etag='W/"snap-1"',
            attempts=1,
        )
    )
    assert reused.outcome == "reused_snapshot"
    assert reused.relative_storage_path == first.relative_storage_path
    assert reused.content_sha256 == first.content_sha256
    assert reused.storage_representation == first.storage_representation
    assert reused.stored_size_bytes == first.stored_size_bytes
    assert reused.content_size_bytes == first.content_size_bytes
    assert reused.is_usable
    assert "preserved snapshot" in reused.detail


# --------------------------------------------------------------------------- #
# Failures and quarantine
# --------------------------------------------------------------------------- #
def test_failure_is_distinguishable_from_a_successful_empty_response(
    store: SnapshotStore,
) -> None:
    observation = store.record(failed())
    assert observation.outcome == "failed"
    assert observation.is_failure
    assert not observation.is_usable
    assert observation.relative_storage_path is None
    assert observation.reason_codes == ("SEC_RESPONSE_EMPTY",)


def test_malformed_payload_is_quarantined_and_preserved(store: SnapshotStore) -> None:
    observation = store.record(
        FetchResult(
            outcome="quarantined",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=200,
            body=b"<!DOCTYPE html><html>blocked</html>",
            reason_code="SEC_RESPONSE_MALFORMED",
            detail="HTML returned where JSON was expected",
            attempts=1,
        )
    )
    assert observation.outcome == "quarantined"
    assert observation.relative_storage_path is not None
    assert observation.relative_storage_path.startswith("raw/sec/quarantine/")
    assert store.payload_path(observation).is_file()
    assert not observation.is_usable


def test_failures_do_not_become_the_latest_snapshot(store: SnapshotStore) -> None:
    good = store.record(retrieved())
    store.record(failed())
    assert store.latest_for(TICKERS).observation_id == good.observation_id


# --------------------------------------------------------------------------- #
# Streaming, audit log, and reporting
# --------------------------------------------------------------------------- #
def test_streamed_archive_is_materialized_and_stored_uncompressed(
    store: SnapshotStore,
) -> None:
    observation = store.record(
        retrieved(
            source_id=BULK,
            url=BULK_URL,
            purpose="census bulk submissions snapshot",
            body=b"",
            chunks=iter([b"PK\x03\x04", b"payload"]),
            declared_content_type="application/zip",
        )
    )
    assert observation.outcome == "stored_new"
    assert observation.content_sha256 == sha256_of(b"PK\x03\x04payload")
    assert observation.relative_storage_path is not None
    assert observation.relative_storage_path.startswith("raw/sec/bulk/")
    assert observation.relative_storage_path.endswith(".zip")
    assert not list(store._tree.staging.glob("*.part"))  # noqa: SLF001


def test_interrupted_stream_leaves_a_recoverable_part_file(store: SnapshotStore) -> None:
    def interrupted() -> Iterator[bytes]:
        yield b"PK\x03\x04"
        message = "stream interrupted"
        raise RuntimeError(message)

    with pytest.raises(RuntimeError, match="stream interrupted"):
        store.record(
            retrieved(
                source_id=BULK,
                url=BULK_URL,
                purpose="census bulk submissions snapshot",
                body=b"",
                chunks=interrupted(),
                declared_content_type="application/zip",
            )
        )
    assert len(list(store._tree.staging.glob("*.part"))) == 1  # noqa: SLF001


def test_audit_log_records_every_observation(store: SnapshotStore) -> None:
    store.record(retrieved())
    store.record(failed())
    path = store.write_audit_log()
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["source_id"] == TICKERS
    assert first["parser_version"] == "company-tickers-exchange/1.0"
    assert "/Users/" not in json.dumps(first)


def test_outcomes_are_counted_for_the_coverage_report(store: SnapshotStore) -> None:
    store.record(retrieved())
    store.record(retrieved())
    store.record(retrieved(body=BODY_TWO))
    store.record(failed())
    counts = observations_by_outcome(store.observations)
    assert counts == {
        "failed": 1,
        "stored_new": 1,
        "superseded": 1,
        "unchanged_content": 1,
    }
    assert len(list(store.iter_usable())) == 3


def test_unregistered_source_cannot_be_recorded(store: SnapshotStore) -> None:
    with pytest.raises(Exception, match="not registered"):
        store.record(retrieved(source_id="kaggle_issuers"))
