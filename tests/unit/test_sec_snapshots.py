"""Immutable source observations: hashing, conditional reuse, supersession, quarantine."""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import replace
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
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import CloseableByteStream

TICKERS = "sec_company_tickers_exchange"
BULK = "sec_bulk_submissions"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
BULK_URL = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip"
BODY_ONE = b'{"0":{"cik_str":1,"ticker":"SYN"}}'
BODY_TWO = b'{"0":{"cik_str":1,"ticker":"SYN2"}}'
SHARED_METADATA_FIELDS = (
    "relative_storage_path",
    "storage_representation",
    "stored_sha256",
    "logical_sha256",
    "content_sha256",
    "transport_sha256",
    "stored_size_bytes",
    "content_size_bytes",
    "transport_size_bytes",
    "content_encoding",
    "declared_content_type",
    "observed_content_kind",
    "parser_version",
)


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


def not_modified(observation: SourceObservation, **overrides: object) -> FetchResult:
    values: dict[str, object] = {
        "outcome": "not_modified",
        "source_id": observation.source_id,
        "url": observation.requested_url,
        "purpose": "census snapshot reuse evidence",
        "status": 304,
        "identity": observation.identity,
        "sent_etag": observation.etag,
        "sent_last_modified": observation.last_modified,
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


def test_empty_identity_never_supplies_a_snapshot_for_a_concrete_request(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved())
    restarted = SnapshotStore(store._tree)  # noqa: SLF001 - restart fixture
    restarted.adopt((replace(first, identity=""),))
    previous = restarted.latest_for(TICKERS, first.identity)
    assert not previous.has_snapshot
    assert previous.etag is None
    assert previous.last_modified is None


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
    assert second.stored_sha256 == first.stored_sha256
    assert second.logical_sha256 == first.logical_sha256
    assert second.stored_size_bytes == first.stored_size_bytes
    assert second.content_size_bytes == first.content_size_bytes
    assert second.reused_observation_id == first.observation_id
    assert all(getattr(second, field) == getattr(first, field) for field in SHARED_METADATA_FIELDS)
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
    assert reused.stored_sha256 == first.stored_sha256
    assert reused.logical_sha256 == first.logical_sha256
    assert reused.transport_sha256 == first.transport_sha256
    assert reused.stored_size_bytes == first.stored_size_bytes
    assert reused.content_size_bytes == first.content_size_bytes
    assert reused.transport_size_bytes == first.transport_size_bytes
    assert reused.content_encoding == first.content_encoding
    assert reused.reused_observation_id == first.observation_id
    assert all(getattr(reused, field) == getattr(first, field) for field in SHARED_METADATA_FIELDS)
    assert reused.is_usable
    assert "preserved snapshot" in reused.detail


def test_repeated_reuse_points_to_the_object_owning_observation(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved())
    second = store.record(
        FetchResult(
            outcome="not_modified",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=304,
            identity=first.identity,
            sent_etag=first.etag,
        )
    )
    third = store.record(
        FetchResult(
            outcome="not_modified",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=304,
            identity=first.identity,
            sent_etag=second.etag,
        )
    )
    assert second.reused_observation_id == first.observation_id
    assert third.reused_observation_id == first.observation_id


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    [
        ({"storage_representation": None}, "prior_object_metadata_complete"),
        ({"storage_representation": "identical"}, "prior_stored_hash_verifies"),
        ({"stored_size_bytes": 1}, "prior_stored_hash_verifies"),
        ({"content_size_bytes": 1}, "prior_stored_hash_verifies"),
        ({"transport_size_bytes": 1}, "prior_transport_metadata_consistent"),
        ({"transport_sha256": "0" * 64}, "prior_transport_metadata_consistent"),
        ({"content_sha256": "0" * 64}, "prior_transport_metadata_consistent"),
    ],
)
def test_incomplete_or_inconsistent_object_metadata_refuses_reuse(
    store: SnapshotStore,
    changes: dict[str, object],
    failed_check: str,
) -> None:
    first = store.record(retrieved())
    prior = replace(store.latest_for(TICKERS, first.identity), **changes)
    decision = store.evaluate_reuse(
        SOURCES[TICKERS],
        FetchResult(
            outcome="not_modified",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=304,
            identity=first.identity,
            sent_etag=first.etag,
        ),
        prior,
        first.identity,
    )
    assert not decision.permitted
    assert failed_check in decision.failed_checks


@pytest.mark.parametrize(
    ("source_id", "url", "body", "declared_content_type"),
    (
        (TICKERS, TICKERS_URL, BODY_ONE, "application/json"),
        (BULK, BULK_URL, b"PK\x03\x04synthetic-offline-archive", "application/zip"),
    ),
)
def test_reuse_verification_reads_large_objects_as_bounded_streams(
    store: SnapshotStore,
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    url: str,
    body: bytes,
    declared_content_type: str,
) -> None:
    first = store.record(
        retrieved(
            source_id=source_id,
            url=url,
            body=body,
            declared_content_type=declared_content_type,
        )
    )
    raw_path = store.payload_path(first)
    original_read_bytes = Path.read_bytes

    def reject_unbounded_raw_read(path: Path) -> bytes:
        if path == raw_path:
            message = "reuse verification must not materialize the complete raw object"
            raise AssertionError(message)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_unbounded_raw_read)
    reused = store.record(not_modified(first))
    assert reused.outcome == "reused_snapshot"


@pytest.mark.parametrize(
    ("source_id", "url", "body", "declared_content_type", "representation"),
    (
        (
            TICKERS,
            TICKERS_URL,
            b'{"payload":"' + (b"x" * (2 * 1024 * 1024)) + b'"}',
            "application/json",
            "deterministic_gzip",
        ),
        (
            BULK,
            BULK_URL,
            b"PK\x03\x04" + (b"x" * (2 * 1024 * 1024)),
            "application/zip",
            "identical",
        ),
    ),
)
def test_new_object_reconciliation_uses_bounded_reads_for_both_representations(
    store: SnapshotStore,
    monkeypatch: pytest.MonkeyPatch,
    source_id: str,
    url: str,
    body: bytes,
    declared_content_type: str,
    representation: str,
) -> None:
    observation = store.record(
        retrieved(
            source_id=source_id,
            url=url,
            body=body,
            declared_content_type=declared_content_type,
        )
    )
    raw_path = store.payload_path(observation)
    assert observation.storage_representation == representation
    assert observation.transport_sha256 is not None
    assert observation.stored_sha256 is not None
    original_read_bytes = Path.read_bytes

    def reject_unbounded_raw_read(path: Path) -> bytes:
        if path == raw_path:
            message = "reconciliation must not materialize the complete raw object"
            raise AssertionError(message)
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", reject_unbounded_raw_read)
    disagreement = store._reconcile_hashes(  # noqa: SLF001 - resource-safety regression
        observation.storage_representation,
        observation.transport_sha256,
        raw_path,
        observation.stored_sha256,
    )
    assert disagreement is None


def test_corrupt_non_owning_terminal_observation_refuses_reuse(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    second = store.record(not_modified(first), retrieved_at_utc="2026-07-27T00:00:00Z")
    restarted = SnapshotStore(store._tree)  # noqa: SLF001 - corrupt restart fixture
    restarted.adopt((replace(first, outcome="quarantined"), second))

    refused = restarted.record(
        not_modified(second),
        retrieved_at_utc="2026-07-28T00:00:00Z",
    )
    assert refused.outcome == "failed"
    assert "evidence_owner_verified" in refused.detail


def test_incompatible_intermediate_reuse_hop_refuses_reuse(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    second = store.record(not_modified(first), retrieved_at_utc="2026-07-27T00:00:00Z")
    chained = replace(
        second,
        observation_id="synthetic-third-hop",
        reused_observation_id=second.observation_id,
        retrieved_at_utc="2026-07-28T00:00:00Z",
    )
    incompatible = replace(second, identity="different-request-identity")
    restarted = SnapshotStore(store._tree)  # noqa: SLF001 - corrupt restart fixture
    restarted.adopt((first, incompatible, chained))

    refused = restarted.record(
        not_modified(chained),
        retrieved_at_utc="2026-07-29T00:00:00Z",
    )
    assert refused.outcome == "failed"
    assert "evidence_owner_verified" in refused.detail


@pytest.mark.parametrize("damage", ["dangling", "cycle"])
def test_dangling_or_cyclic_in_memory_reuse_chain_is_not_an_evidence_owner(
    store: SnapshotStore,
    damage: str,
) -> None:
    first = store.record(retrieved(), retrieved_at_utc="2026-07-26T00:00:00Z")
    second = store.record(not_modified(first), retrieved_at_utc="2026-07-27T00:00:00Z")
    if damage == "dangling":
        observations = (first, replace(second, reused_observation_id="missing-owner"))
    else:
        observations = (
            replace(
                first,
                outcome="unchanged_content",
                reused_observation_id=second.observation_id,
                retrieved_at_utc=second.retrieved_at_utc,
            ),
            replace(second, retrieved_at_utc=second.retrieved_at_utc),
        )
    restarted = SnapshotStore(store._tree)  # noqa: SLF001 - corrupt restart fixture
    restarted.adopt(observations)
    previous = restarted.latest_for(TICKERS, first.identity)
    assert previous.evidence_observation_id is None

    refused = restarted.record(
        not_modified(second),
        retrieved_at_utc="2026-07-28T00:00:00Z",
    )
    assert refused.outcome == "failed"
    assert "evidence_owner_verified" in refused.detail


@pytest.mark.parametrize(
    ("changes", "failed_check"),
    (
        ({"observed_content_kind": "html"}, "observed_content_kind_compatible"),
        ({"declared_content_type": "text/html"}, "declared_content_type_compatible"),
    ),
)
def test_incompatible_interpretation_metadata_refuses_reuse(
    store: SnapshotStore,
    changes: dict[str, object],
    failed_check: str,
) -> None:
    first = store.record(retrieved())
    corrupted = replace(first, **changes)
    restarted = SnapshotStore(store._tree)  # noqa: SLF001 - corrupt restart fixture
    restarted.adopt((corrupted,))
    previous = restarted.latest_for(TICKERS, first.identity)
    decision = restarted.evaluate_reuse(
        SOURCES[TICKERS],
        not_modified(corrupted),
        previous,
        first.identity,
    )
    assert not decision.permitted
    assert failed_check in decision.failed_checks


@pytest.mark.parametrize(
    "unsafe_kind",
    ("absolute", "traversal"),
)
def test_absolute_or_traversal_catalog_path_refuses_reuse(
    store: SnapshotStore,
    unsafe_kind: str,
) -> None:
    first = store.record(retrieved())
    unsafe_path = (
        str(store.payload_path(first))
        if unsafe_kind == "absolute"
        else "raw/sec/indexes/../../../outside-disclosure-drift-evidence.gz"
    )
    prior = replace(store.latest_for(TICKERS, first.identity), relative_storage_path=unsafe_path)
    decision = store.evaluate_reuse(
        SOURCES[TICKERS],
        not_modified(first),
        prior,
        first.identity,
    )
    assert not decision.permitted
    assert "prior_raw_path_contained" in decision.failed_checks


def test_symlinked_catalog_path_refuses_reuse(store: SnapshotStore) -> None:
    first = store.record(retrieved())
    target = store.payload_path(first)
    link = store._tree.raw_indexes / "symlinked-evidence.json.gz"  # noqa: SLF001
    link.symlink_to(target)
    prior = replace(
        store.latest_for(TICKERS, first.identity),
        relative_storage_path=store._tree.relative(link),  # noqa: SLF001
    )
    decision = store.evaluate_reuse(
        SOURCES[TICKERS],
        not_modified(first),
        prior,
        first.identity,
    )
    assert not decision.permitted
    assert "prior_raw_path_contained" in decision.failed_checks


@pytest.mark.parametrize("damage", ["missing", "tampered"])
def test_missing_or_tampered_prior_object_refuses_304_reuse(
    store: SnapshotStore,
    damage: str,
) -> None:
    first = store.record(retrieved())
    path = store.payload_path(first)
    if damage == "missing":
        path.unlink()
    else:
        path.write_bytes(b"tampered")

    refused = store.record(
        FetchResult(
            outcome="not_modified",
            source_id=TICKERS,
            url=TICKERS_URL,
            purpose="census alias evidence",
            status=304,
            identity=first.identity,
            sent_etag=first.etag,
        )
    )
    assert refused.outcome == "failed"
    assert refused.reason_codes == ("SOURCE_SNAPSHOT_REUSE_UNRECONCILED",)
    assert refused.relative_storage_path is None


def test_fresh_identical_response_does_not_trust_incorrect_prior_size(
    store: SnapshotStore,
) -> None:
    first = store.record(retrieved())
    store._observations[0] = replace(  # noqa: SLF001 - controlled corrupt catalog fixture
        first,
        stored_size_bytes=(first.stored_size_bytes or 0) + 1,
    )

    fresh = store.record(retrieved())
    assert fresh.outcome == "stored_new"
    assert fresh.reused_observation_id is None
    assert fresh.stored_size_bytes == store.payload_path(fresh).stat().st_size
    assert "reuse was refused" in fresh.detail


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


@pytest.mark.parametrize(
    ("payload", "declared_content_type", "reason_code"),
    [
        (b"not-a-zip", "application/zip", "RAW_ARCHIVE_INVALID"),
        (b"PK\x03\x04payload", "text/html", "SEC_RESPONSE_MALFORMED"),
    ],
)
def test_streamed_quarantine_is_durably_preserved_with_complete_provenance(
    store: SnapshotStore,
    payload: bytes,
    declared_content_type: str,
    reason_code: str,
) -> None:
    closed: list[str] = []
    stream = CloseableByteStream(
        iter([payload[:4], payload[4:]]),
        close_callback=lambda: closed.append("closed"),
    )
    result = FetchResult(
        outcome="quarantined",
        source_id=BULK,
        url=BULK_URL,
        final_url=BULK_URL,
        purpose="census bulk submissions snapshot",
        status=200,
        body=b"",
        chunks=stream,
        etag='"quarantine-etag"',
        last_modified="Sun, 26 Jul 2026 12:00:00 GMT",
        declared_content_type=declared_content_type,
        content_encoding="gzip",
        provenance_headers={
            "etag": '"quarantine-etag"',
            "last-modified": "Sun, 26 Jul 2026 12:00:00 GMT",
            "content-type": declared_content_type,
            "content-encoding": "gzip",
        },
        attempts=1,
        reason_code=reason_code,
        detail="synthetic malformed streamed response",
    )

    observation = store.record(result, retrieved_at_utc="2026-07-26T12:00:00Z")

    assert observation.outcome == "quarantined"
    assert observation.relative_storage_path is not None
    assert observation.relative_storage_path.startswith("raw/sec/quarantine/")
    assert observation.transport_sha256 == sha256_of(payload)
    assert observation.stored_sha256 == sha256_of(payload)
    assert observation.logical_sha256 == sha256_of(payload)
    assert observation.transport_size_bytes == len(payload)
    assert observation.stored_size_bytes == len(payload)
    assert observation.content_size_bytes == len(payload)
    assert observation.storage_representation == "identical"
    assert observation.etag == '"quarantine-etag"'
    assert observation.last_modified == "Sun, 26 Jul 2026 12:00:00 GMT"
    assert observation.content_encoding == "gzip"
    assert observation.declared_content_type == declared_content_type
    quarantined = store.payload_path(observation)
    assert quarantined.read_bytes() == payload
    assert quarantined.with_suffix(quarantined.suffix + ".reason").is_file()
    assert result.chunks is not None and result.chunks.closed
    assert closed == ["closed"]


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
    result = retrieved(
        source_id=BULK,
        url=BULK_URL,
        purpose="census bulk submissions snapshot",
        body=b"",
        chunks=iter([b"PK\x03\x04", b"payload"]),
        declared_content_type="application/zip",
    )
    observation = store.record(result)
    assert observation.outcome == "stored_new"
    assert observation.content_sha256 == sha256_of(b"PK\x03\x04payload")
    assert observation.relative_storage_path is not None
    assert observation.relative_storage_path.startswith("raw/sec/bulk/")
    assert observation.relative_storage_path.endswith(".zip")
    assert result.chunks is not None and result.chunks.closed
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
    assert first["observed_content_kind"] == "json"
    assert "/Users/" not in json.dumps(first)


def test_audit_log_refuses_symlink_without_modifying_its_target(
    store: SnapshotStore,
) -> None:
    store.record(retrieved())
    target = store._tree.data_root / "outside-audit-target.jsonl"  # noqa: SLF001
    sentinel = b"existing unrelated evidence\n"
    target.write_bytes(sentinel)
    link = store._tree.audit / "census_source_observations.jsonl"  # noqa: SLF001
    link.symlink_to(target)

    with pytest.raises(RawObjectIntegrityError, match="non-linked regular file"):
        store.write_audit_log()

    assert link.is_symlink()
    assert target.read_bytes() == sentinel


def test_audit_log_refuses_symlinked_parent_without_modifying_target(
    store: SnapshotStore,
) -> None:
    store.record(retrieved())
    outside = store._tree.data_root / "outside-audit-directory"  # noqa: SLF001
    outside.mkdir()
    target = outside / "census_source_observations.jsonl"
    sentinel = b"outside projection must stay unchanged\n"
    target.write_bytes(sentinel)
    store._tree.audit.rmdir()  # noqa: SLF001 - isolated temporary-tree setup
    store._tree.audit.symlink_to(outside, target_is_directory=True)  # noqa: SLF001

    with pytest.raises(RawObjectIntegrityError, match="safe, non-linked directory"):
        store.write_audit_log()

    assert store._tree.audit.is_symlink()  # noqa: SLF001
    assert target.read_bytes() == sentinel


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
