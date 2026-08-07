"""Atomic raw-object storage, integrity, quarantine, and crash recovery."""

from __future__ import annotations

import hashlib
import tracemalloc
import zlib
from collections.abc import Iterator
from dataclasses import replace
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

#: Large enough that an implementation retaining the whole body allocates megabytes, small enough
#: that the ordinary suite stays fast. Sixteen blocks also proves multi-chunk consumption.
LARGE_BLOCK_BYTES = 512 * 1024
LARGE_BLOCK_COUNT = 16
LARGE_TOTAL_BYTES = LARGE_BLOCK_BYTES * LARGE_BLOCK_COUNT


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


# --------------------------------------------------------------------------- #
# Streaming storage (Decision 047 section 6; limitation M3-L13)
#
# The store must not hold a whole payload. These cover the two properties that makes possible --
# an incremental write path and an incremental measurement path -- and the one property it must
# not cost: the stored representation stays byte-identical to the frozen definition.
# --------------------------------------------------------------------------- #
def _repeated_blocks(block: bytes, count: int) -> Iterator[bytes]:
    """Yield one block object `count` times.

    The logical payload is ``len(block) * count`` bytes, but only one block is ever allocated. An
    implementation that retains the whole body must therefore allocate the difference itself,
    which is exactly what the memory control measures.
    """
    for _ in range(count):
        yield block


def _digest_of_repeated(block: bytes, count: int) -> str:
    """The payload's digest, computed without materializing the payload."""
    digest = hashlib.sha256()
    for _ in range(count):
        digest.update(block)
    return digest.hexdigest()


def _incompressible_block(index: int, size: int) -> bytes:
    """Deterministic filler that gzip cannot shrink, derived from a counter.

    Hash output rather than a pseudo-random generator: the bytes are reproducible across runs and
    platforms, and deriving them needs no seeded RNG.
    """
    out = bytearray()
    counter = 0
    while len(out) < size:
        out += hashlib.sha256(f"{index}:{counter}".encode()).digest()
        counter += 1
    return bytes(out[:size])


def _staged_bytes(store: RawStore) -> int:
    """Total size of the `.part` files currently staged for the fixture's accession."""
    directory = store._tree.accession_directory(CIK, ACCESSION)  # noqa: SLF001
    if not directory.is_dir():
        return 0
    return sum(path.stat().st_size for path in directory.glob("*.part"))


@pytest.mark.parametrize("chunk_size", [1, 7, 4096, 65536, len(BODY)])
def test_streaming_compression_reproduces_the_frozen_representation(
    store: RawStore,
    chunk_size: int,
) -> None:
    """However the body arrives, the stored gzip bytes are the frozen ones.

    This is the assertion the whole correction rests on: `store` no longer calls
    `compress_deterministically`, so the streaming compressor must be proved to agree with it
    rather than assumed to.
    """
    body = BODY * 400
    chunks = [body[index : index + chunk_size] for index in range(0, len(body), chunk_size)]
    stored = _store(store, chunks=chunks, compress=True, filename=f"chunked-{chunk_size}.txt")

    assert stored.absolute_path.read_bytes() == compress_deterministically(body)
    assert stored.record.content_sha256 == sha256_of(body)
    assert stored.record.stored_sha256 == sha256_of(compress_deterministically(body))
    assert stored.record.content_size_bytes == len(body)
    assert stored.record.stored_size_bytes == len(compress_deterministically(body))


def test_multi_chunk_uncompressed_store_is_byte_exact(store: RawStore) -> None:
    body = BODY * 400
    chunks = [body[index : index + 1000] for index in range(0, len(body), 1000)]
    stored = _store(store, chunks=chunks)

    assert stored.absolute_path.read_bytes() == body
    assert stored.record.content_sha256 == sha256_of(body)
    assert stored.record.stored_sha256 == sha256_of(body)
    assert stored.record.content_size_bytes == len(body)
    assert stored.record.stored_size_bytes == len(body)
    assert stored.record.compression == "none"


def test_repeated_equivalent_inputs_produce_identical_stored_objects(store: RawStore) -> None:
    """Determinism across separate invocations, under different chunkings."""
    body = BODY * 400
    first = _store(store, chunks=[body], compress=True, filename="determinism-a.txt")
    second = _store(
        store,
        chunks=[body[:13], body[13:9999], body[9999:]],
        compress=True,
        filename="determinism-b.txt",
    )

    assert first.absolute_path.read_bytes() == second.absolute_path.read_bytes()
    assert first.record.stored_sha256 == second.record.stored_sha256
    assert first.record.stored_size_bytes == second.record.stored_size_bytes
    assert first.record.content_sha256 == second.record.content_sha256


def test_large_multi_chunk_object_round_trips_exactly(store: RawStore) -> None:
    block = b"CIK,NAME,FORM,DATE\n" * (LARGE_BLOCK_BYTES // 19)
    expected = _digest_of_repeated(block, LARGE_BLOCK_COUNT)
    total = len(block) * LARGE_BLOCK_COUNT

    stored = _store(
        store,
        chunks=_repeated_blocks(block, LARGE_BLOCK_COUNT),
        compress=True,
        filename="large.txt",
    )

    assert stored.record.content_sha256 == expected
    assert stored.record.content_size_bytes == total
    assert stored.record.stored_size_bytes == stored.absolute_path.stat().st_size
    assert stored.record.stored_sha256 == sha256_of(stored.absolute_path.read_bytes())
    assert sha256_of(decompress(stored.absolute_path.read_bytes())) == expected
    assert store.verify(stored.record)


@pytest.mark.parametrize("compress", [False, True])
def test_store_does_not_retain_the_whole_object_in_memory(
    store: RawStore,
    *,
    compress: bool,
) -> None:
    """Positive control: peak Python allocation must not scale with the object.

    The pre-correction implementation accumulated every chunk into one `bytearray` -- on both
    paths, including the uncompressed one where the buffer was never read -- and then read the
    promoted file back whole. Measured on this payload it peaked at 2.12x the object size
    uncompressed and 3.80x compressed, so this assertion fails against it by a wide margin.

    `tracemalloc` is used rather than RSS deliberately: it counts Python allocations, so the
    result does not depend on the platform's allocator or on process memory the interpreter never
    returns to the OS.
    """
    block = b"CIK,NAME,FORM,DATE\n" * (LARGE_BLOCK_BYTES // 19)
    expected = _digest_of_repeated(block, LARGE_BLOCK_COUNT)
    total = len(block) * LARGE_BLOCK_COUNT

    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        baseline = tracemalloc.get_traced_memory()[0]
        stored = _store(
            store,
            chunks=_repeated_blocks(block, LARGE_BLOCK_COUNT),
            compress=compress,
            filename=f"memory-{compress}.txt",
        )
        peak = tracemalloc.get_traced_memory()[1] - baseline
    finally:
        tracemalloc.stop()

    assert stored.record.content_sha256 == expected, "the payload must still be hashed in full"
    assert stored.record.content_size_bytes == total
    assert peak < total // 2, (
        f"storing {total} bytes peaked at {peak} traced bytes, which is consistent with the whole "
        "object being retained in memory"
    )


def test_compressed_store_writes_before_the_last_chunk_is_consumed(store: RawStore) -> None:
    """Positive control: compression is incremental, not deferred to the end of the stream.

    Threshold-free. The pre-correction implementation compressed `bytes(buffer)` only after the
    generator was exhausted, so the staging file was still empty at this observation point and the
    assertion below was exactly zero.

    The payload is incompressible on purpose: highly compressible bytes can sit inside zlib's own
    pending buffer without reaching the file, which would make the observation about zlib's
    buffering rather than about this module's write path.
    """
    blocks = [_incompressible_block(index, 64 * 1024) for index in range(64)]
    body = b"".join(blocks)
    staged_before_last_chunk: list[int] = []

    def chunks() -> Iterator[bytes]:
        for index, block in enumerate(blocks):
            if index == len(blocks) - 1:
                staged_before_last_chunk.append(_staged_bytes(store))
            yield block

    stored = _store(store, chunks=chunks(), compress=True, filename="incremental.bin")

    assert staged_before_last_chunk, "the observation point was never reached"
    assert staged_before_last_chunk[0] > 0, (
        "no compressed byte had been written before the final chunk was consumed, which means the "
        "whole object was being buffered and compressed at the end"
    )
    assert stored.absolute_path.read_bytes() == compress_deterministically(body)
    assert stored.record.content_sha256 == sha256_of(body)


def test_deduplication_verifies_a_large_existing_object_exactly(store: RawStore) -> None:
    """The existing-object path still compares by exact hash, and still refuses a mismatch."""
    block = b"CIK,NAME,FORM,DATE\n" * (LARGE_BLOCK_BYTES // 19)
    first = _store(store, chunks=_repeated_blocks(block, 4), filename="dedup.txt")

    again = _store(store, chunks=_repeated_blocks(block, 4), filename="dedup.txt")
    assert again.record.stored_sha256 == first.record.stored_sha256
    assert again.absolute_path == first.absolute_path
    assert not list(first.absolute_path.parent.glob("*.part")), "the duplicate .part is released"

    with pytest.raises(RawObjectIntegrityError, match="refusing to overwrite"):
        _store(store, chunks=_repeated_blocks(block, 5), filename="dedup.txt")
    assert first.absolute_path.stat().st_size == len(block) * 4


# --------------------------------------------------------------------------- #
# Verification covers the stored representation, not just the decoded payload
#
# A raw object is one exact immutable stored representation, so recovering the expected decoded
# bytes is necessary but nowhere near sufficient. Each damage case below decodes to *exactly* the
# right payload and must still be refused; each asserts that fact about itself, so none can pass
# by accidentally being damaged in some cruder way. Every case is derived from the same object
# `_verified_gzip_object` has already proved verifies, so a green result cannot come from a
# mis-built fixture.
# --------------------------------------------------------------------------- #
VERIFIED_BODY = BODY * 400
#: Offset of the gzip header's OS field. Every reader ignores it, which is what makes overwriting
#: it a change to the stored representation and to nothing else.
GZIP_HEADER_OS_OFFSET = 9
#: The window that carries a gzip wrapper, spelled out here rather than imported, so these tests
#: do not decode with the same constant the module under test uses.
GZIP_WBITS = 16 + zlib.MAX_WBITS


def _verified_gzip_object(store: RawStore, filename: str) -> object:
    """Store the canonical gzip object, proving it is the frozen representation and verifies."""
    stored = _store(store, chunks=[VERIFIED_BODY], compress=True, filename=filename)
    assert stored.absolute_path.read_bytes() == compress_deterministically(VERIFIED_BODY)
    assert store.verify(stored.record) is True, "the positive control must verify"
    return stored


def _decode_first_member(data: bytes) -> tuple[bytes, bool, bytes]:
    """Return the first gzip member's payload, whether it ended, and whatever followed it."""
    inflater = zlib.decompressobj(GZIP_WBITS)
    decoded = inflater.decompress(data) + inflater.flush()
    return decoded, inflater.eof, inflater.unused_data


def _record_describing_the_damaged_file(record: object, path: Path) -> object:
    """Re-point a record's stored digest and length at whatever bytes are on disk now.

    Damaging a file changes its digest and its length, so the stored-representation comparison
    refuses it on its own and structural validation is never what answered. Re-recording the
    damaged bytes removes that shortcut and isolates the structural checks as the only thing left
    that can refuse.

    It is also the case that matters most. A catalog row that *faithfully describes* a malformed
    object is the one an attacker or a defective writer would produce, and self-consistency is
    exactly what must not be enough to bless it: the decoded payload is right, the digests agree
    with the bytes, and the object is still not one complete gzip member.
    """
    data = path.read_bytes()
    return replace(record, stored_sha256=sha256_of(data), stored_size_bytes=len(data))


def test_verify_streams_a_gzip_object_and_fails_closed_on_damage(store: RawStore) -> None:
    stored = _verified_gzip_object(store, "verified.txt")

    intact = stored.absolute_path.read_bytes()
    stored.absolute_path.write_bytes(intact[: len(intact) // 2])
    assert store.verify(stored.record) is False, "a truncated gzip object must not verify"

    stored.absolute_path.write_bytes(b"not gzip at all")
    assert store.verify(stored.record) is False, "bytes that are not gzip at all must not verify"


@pytest.mark.parametrize("dropped", [1, 2, 4, 8])
def test_verify_refuses_a_gzip_object_whose_trailer_is_truncated(
    store: RawStore,
    dropped: int,
) -> None:
    """Losing the CRC-32/length footer still decodes the whole payload, and must not verify.

    This is the case the earlier half-truncation missed. Cutting a file in half leaves deflate
    blocks missing, so the payload decodes short and the content digest disagrees on its own.
    Cutting only the footer leaves every deflate block intact: the full payload decodes, hashes
    correctly, and the object is short by up to eight bytes with nothing but the inflater's
    end-of-stream flag to say so.
    """
    stored = _verified_gzip_object(store, f"trailer-{dropped}.txt")
    damaged = stored.absolute_path.read_bytes()[:-dropped]
    stored.absolute_path.write_bytes(damaged)

    decoded, reached_eof, trailing = _decode_first_member(damaged)
    assert sha256_of(decoded) == stored.record.content_sha256, (
        "this case must reach structural validation with the whole payload decoded, or it only "
        "re-covers the short-read case the content digest already caught"
    )
    assert not reached_eof, "the truncated footer is the only remaining evidence of damage"
    assert not trailing

    assert store.verify(stored.record) is False
    assert (
        store.verify(_record_describing_the_damaged_file(stored.record, stored.absolute_path))
        is False
    ), (
        "re-recorded to the damaged bytes, every digest and length agrees and only the inflater's "
        "end-of-stream flag is left to refuse this"
    )


def test_verify_refuses_a_gzip_object_with_bytes_appended_after_the_stream(
    store: RawStore,
) -> None:
    """A complete member followed by garbage decodes correctly and must not verify."""
    stored = _verified_gzip_object(store, "trailing-garbage.txt")
    damaged = stored.absolute_path.read_bytes() + b"appended, and not part of this object"
    stored.absolute_path.write_bytes(damaged)

    decoded, reached_eof, trailing = _decode_first_member(damaged)
    assert sha256_of(decoded) == stored.record.content_sha256, (
        "the decoded first member must still be correct, or this proves nothing about whether a "
        "correct payload can carry uninspected bytes"
    )
    assert reached_eof
    assert trailing

    assert store.verify(stored.record) is False
    assert (
        store.verify(_record_describing_the_damaged_file(stored.record, stored.absolute_path))
        is False
    ), (
        "re-recorded to the damaged bytes, only the bytes left over after the member can refuse "
        "this -- a correct payload must not be able to carry uninspected cargo"
    )


def test_verify_refuses_a_concatenated_second_gzip_member(store: RawStore) -> None:
    """Two valid members are two objects, not one longer one."""
    stored = _verified_gzip_object(store, "second-member.txt")
    second_payload = b"a wholly different object\n"
    damaged = stored.absolute_path.read_bytes() + compress_deterministically(second_payload)
    stored.absolute_path.write_bytes(damaged)

    decoded, reached_eof, trailing = _decode_first_member(damaged)
    assert sha256_of(decoded) == stored.record.content_sha256
    assert reached_eof
    assert trailing, "the second member is present as unused input, exactly as garbage would be"
    assert decompress(damaged) == VERIFIED_BODY + second_payload, (
        "gzip itself would silently join the members into one payload, which is precisely why "
        "verification cannot delegate the question to it"
    )

    assert store.verify(stored.record) is False
    assert (
        store.verify(_record_describing_the_damaged_file(stored.record, stored.absolute_path))
        is False
    ), (
        "re-recorded to the damaged bytes, refusing the second member is the only check left, and "
        "two members must never be silently read as one object"
    )


def test_verify_binds_the_stored_hash_when_the_payload_still_decodes(store: RawStore) -> None:
    """Rewriting an ignored header byte changes the object and nothing else about it."""
    stored = _verified_gzip_object(store, "stored-hash.txt")
    intact = stored.absolute_path.read_bytes()
    mutated = bytearray(intact)
    mutated[GZIP_HEADER_OS_OFFSET] ^= 0xFF
    stored.absolute_path.write_bytes(bytes(mutated))

    assert bytes(mutated) != intact, "the stored bytes must actually differ"
    assert len(mutated) == len(intact), "same length, so the size comparison cannot be what refuses"
    decoded, reached_eof, trailing = _decode_first_member(bytes(mutated))
    assert sha256_of(decoded) == stored.record.content_sha256, (
        "the mutated header must still decode to the right payload, or this does not isolate the "
        "stored-hash comparison"
    )
    assert reached_eof and not trailing, "structure is intact, so only the stored digest is left"

    assert store.verify(stored.record) is False


@pytest.mark.parametrize("field", ["stored_size_bytes", "content_size_bytes"])
def test_verify_binds_the_recorded_sizes(store: RawStore, field: str) -> None:
    """Each recorded length is compared, not merely implied by a digest.

    The file is left untouched and the record is made to disagree with it, because any change to
    the bytes that alters a length alters a digest too. Disagreeing about the length alone is the
    only way to show that the length comparison is load-bearing rather than dead weight.
    """
    stored = _verified_gzip_object(store, f"size-{field}.txt")
    misrecorded = replace(stored.record, **{field: getattr(stored.record, field) + 1})

    assert store.verify(misrecorded) is False
    assert store.verify(stored.record) is True, "the object itself is undamaged"


def test_verify_refuses_an_object_whose_file_is_gone(store: RawStore) -> None:
    stored = _verified_gzip_object(store, "missing.txt")
    stored.absolute_path.unlink()
    assert store.verify(stored.record) is False


def test_verify_does_not_convert_an_os_failure_into_a_negative_answer(
    store: RawStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail-closed means "not verified", not "swallow everything".

    An unreadable disk is not an answer of "no". The integrity checks return ``False``; genuine
    OS failures still propagate, so a broken filesystem can never be mistaken for a clean refusal.
    """
    stored = _verified_gzip_object(store, "unreadable.txt")

    def refuse_to_open(*args: object, **kwargs: object) -> object:
        message = "simulated I/O failure"
        raise OSError(message)

    monkeypatch.setattr(Path, "open", refuse_to_open)
    with pytest.raises(OSError, match="simulated I/O failure"):
        store.verify(stored.record)
