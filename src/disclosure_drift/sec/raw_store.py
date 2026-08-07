"""Immutable raw-object storage with an atomic write protocol (Decision 009).

Guarantees implemented here:

* a ``.part`` file is never treated as complete;
* promotion is an atomic, no-overwrite hard link and the parent directory is fsynced;
* ``content_sha256`` covers decoded entity bytes and is the integrity anchor;
* text-like payloads use deterministic gzip whose round trip must reproduce
  ``content_sha256``;
* verification establishes the **stored representation**, not merely that the expected decoded
  bytes can be recovered from it: stored digest and length, decoded digest and length, and — for a
  gzip object — that the file is exactly one complete gzip member;
* a later differing response becomes a **new observation**, never an overwrite;
* damaged files are quarantined and preserved, never replaced or deleted;
* crash recovery may only adopt a valid orphan or quarantine a partial file;
* **memory does not scale with the object.** Every payload is hashed, sized, compressed,
  decompressed, and verified over bounded blocks, so storing a multi-gigabyte bulk archive costs
  no more resident memory than storing a small one (accepted Decision 047 §6; limitation
  **M3-L13**).

The last guarantee is the reason this module never materializes a whole payload. The retrieval
layer already spools a response to disk and yields it back in blocks precisely so the body need not
be held at once; buffering it here would have thrown that away, and the one route in the M3.2A plan
that retrieves a full bulk archive is exactly where that would have failed. What replaces the
buffer is a streaming compressor whose output is **byte-identical** to
:func:`compress_deterministically`, and a single bounded read pass that establishes the stored
digest, the stored size, and the decompressed digest together.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import uuid
import zlib
from collections.abc import Callable, Iterable, Iterator, Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree, relative_to_root

__all__ = [
    "GZIP_COMPRESSION_LEVEL",
    "LINEAGE_SUFFIX",
    "Compression",
    "RawObjectRecord",
    "RawStore",
    "ReconciliationReport",
    "StoredObject",
    "compress_deterministically",
    "decompress",
    "sha256_of",
]

GZIP_COMPRESSION_LEVEL: Final = 6
#: The ``zlib`` window size that carries a gzip wrapper. ``gzip.compress(data, level, mtime=0)``
#: reduces to ``zlib.compress(data, level=level, wbits=31)``, so a streaming compressor opened on
#: the same window emits the same bytes for the same input regardless of how that input is chunked.
#: That equality is what lets the frozen deterministic representation stay frozen while the object
#: is compressed incrementally, and it is asserted directly by the tests rather than assumed.
_GZIP_WBITS: Final = 16 + zlib.MAX_WBITS
#: How much of a stored object is resident at once while it is hashed, sized, or verified. The same
#: 1 MiB block the accepted snapshot spooler already reads with.
_STREAM_BLOCK_BYTES: Final = 1024 * 1024
_PART_SUFFIX: Final = ".part"
_GZIP_SUFFIX: Final = ".gz"
LINEAGE_SUFFIX: Final = ".lineage.json"
Compression = Literal["none", "gzip"]


def sha256_of(data: bytes) -> str:
    """Return the hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def compress_deterministically(data: bytes) -> bytes:
    """Compress with gzip in a reproducible way (level 6, mtime 0).

    This is the frozen definition of the stored representation. :meth:`RawStore.store` no longer
    calls it — it cannot, without holding the whole payload — but the streaming compressor it uses
    instead must reproduce these exact bytes, so this function remains the reference the tests
    compare against.
    """
    return gzip.compress(data, compresslevel=GZIP_COMPRESSION_LEVEL, mtime=0)


def decompress(data: bytes) -> bytes:
    """Decompress gzip bytes."""
    return gzip.decompress(data)


@dataclass(frozen=True, slots=True)
class _StoredFileMeasurement:
    """What one bounded read pass establishes about bytes already on disk."""

    stored_sha256: str
    stored_size_bytes: int
    #: Digest of the decompressed stream, present only when the file was read as gzip.
    decompressed_sha256: str | None
    #: Length of the decompressed stream, present only when the file was read as gzip. Counted as
    #: the stream is drained, so it costs nothing beyond the pass that was happening anyway.
    decompressed_size_bytes: int | None


def _require_one_complete_gzip_member(path: Path, inflater: zlib._Decompress) -> None:
    """Refuse gzip bytes that are not exactly one complete member.

    The decoded payload agreeing with ``content_sha256`` is necessary but *not* sufficient: three
    structurally invalid files decode to the right bytes and would otherwise pass unnoticed.

    * A **truncated trailer** removes the CRC-32 and length footer. Every deflate block is still
      present, so the full payload decodes and only ``eof`` — which stays ``False`` because zlib
      never saw the footer it validates against — reveals that the object is short.
    * **Trailing garbage** after a complete member decodes correctly and leaves the extra bytes in
      ``unused_data``.
    * A **concatenated second member** is the same signal. ``gzip`` would silently join the members
      into one logical payload; a raw object is one exact immutable stored representation, so a
      second member is a different object, not more of this one.

    ``unconsumed_tail`` is checked for completeness: the read loop drains it, so anything left is
    input the inflater neither consumed nor disowned.
    """
    if not inflater.eof:
        message = f"stored object {path.name} ends before its gzip stream is complete"
        raise RawObjectIntegrityError(message)
    if inflater.unconsumed_tail:
        message = (
            f"stored object {path.name} leaves {len(inflater.unconsumed_tail)} undecoded byte(s) "
            "in its gzip stream"
        )
        raise RawObjectIntegrityError(message)
    if inflater.unused_data:
        message = (
            f"stored object {path.name} carries {len(inflater.unused_data)} byte(s) after the end "
            "of its gzip stream"
        )
        raise RawObjectIntegrityError(message)


def _measure_stored_file(path: Path, *, decompressing: bool) -> _StoredFileMeasurement:
    """Hash and size a stored object in bounded blocks, decompressing as it reads if asked.

    One pass establishes everything the store needs to know about bytes that are already written:
    their digest, their exact length, and — for a gzip object — the digest of what they decompress
    back to. Reading the file whole would make storage memory scale with the object, which is the
    defect this exists to avoid.

    The decompressed digest is taken from the **file**, not from the compressor's own output, so
    the deterministic round trip still verifies what actually landed on disk rather than what was
    intended to. For the same reason the pass also establishes that the file *is* one complete
    gzip member — decoding the expected bytes says nothing about what surrounds them.

    Raises:
        RawObjectIntegrityError: the bytes do not form a readable, complete, single-member gzip
            stream. A corrupt stored representation is an integrity fact about a raw object, so it
            is raised as one rather than surfacing a driver-level ``zlib`` error a caller would
            have to string-match.
    """
    stored = hashlib.sha256()
    decompressed = hashlib.sha256() if decompressing else None
    inflater = zlib.decompressobj(_GZIP_WBITS) if decompressing else None

    size = 0
    decompressed_size = 0
    with path.open("rb") as handle:
        while block := handle.read(_STREAM_BLOCK_BYTES):
            stored.update(block)
            size += len(block)
            if inflater is None or decompressed is None:
                continue
            # `max_length` matters as much as the read size does. A block of a compressible object
            # expands enormously, so an unbounded `decompress` would rebuild the whole payload in
            # one object and reintroduce the defect on the verification path -- and would make a
            # decompression bomb a memory fault rather than an integrity finding. Draining
            # `unconsumed_tail` keeps every intermediate piece bounded instead.
            #
            # Feeding blocks that follow the end of the member is safe and deliberate: zlib
            # accumulates them into `unused_data` instead of decoding them, so trailing bytes
            # remain visible however far into the file they begin, and the loop still reads every
            # block -- which it must, because the stored digest covers the whole file.
            pending = block
            while pending:
                try:
                    piece = inflater.decompress(pending, _STREAM_BLOCK_BYTES)
                except zlib.error as exc:
                    message = f"stored object {path.name} is not a readable gzip stream: {exc}"
                    raise RawObjectIntegrityError(message) from exc
                decompressed.update(piece)
                decompressed_size += len(piece)
                pending = inflater.unconsumed_tail

    if inflater is not None and decompressed is not None:
        try:
            remainder = inflater.flush()
        except zlib.error as exc:
            message = f"stored object {path.name} ends mid-gzip-stream: {exc}"
            raise RawObjectIntegrityError(message) from exc
        decompressed.update(remainder)
        decompressed_size += len(remainder)
        _require_one_complete_gzip_member(path, inflater)

    return _StoredFileMeasurement(
        stored_sha256=stored.hexdigest(),
        stored_size_bytes=size,
        decompressed_sha256=None if decompressed is None else decompressed.hexdigest(),
        decompressed_size_bytes=None if decompressed is None else decompressed_size,
    )


@dataclass(frozen=True, slots=True)
class RawObjectRecord:
    """Catalog-facing description of one stored observation."""

    raw_object_id: str
    observation_id: str
    logical_role: str
    source_url_canonical: str
    relative_storage_path: str
    media_type: str | None
    content_encoding_received: str | None
    content_sha256: str
    stored_sha256: str
    content_size_bytes: int
    stored_size_bytes: int
    compression: Compression
    retrieved_at_utc: str
    retrieval_attempt_id: str
    accession_plain: str | None = None
    cik_padded: str | None = None
    supersedes_observation_id: str | None = None
    reason_code: str | None = None

    @property
    def is_new_observation_of_changed_content(self) -> bool:
        """Whether this observation supersedes an earlier, differing one."""
        return self.supersedes_observation_id is not None


@dataclass(frozen=True, slots=True)
class StoredObject:
    """Result of a completed store operation."""

    record: RawObjectRecord
    absolute_path: Path


@dataclass(frozen=True, slots=True)
class ReconciliationReport:
    """Outcome of post-crash reconciliation."""

    adopted: tuple[str, ...]
    quarantined: tuple[str, ...]
    missing_files: tuple[str, ...]

    @property
    def is_clean(self) -> bool:
        """Whether nothing needed adoption, quarantine, or reporting."""
        return not (self.adopted or self.quarantined or self.missing_files)


class RawStore:
    """Accession-addressed immutable object store."""

    def __init__(self, tree: DataTree) -> None:
        self._tree = tree

    # -- storing ------------------------------------------------------------ #
    def store(
        self,
        *,
        chunks: Iterable[bytes],
        logical_role: str,
        source_url_canonical: str,
        retrieval_attempt_id: str,
        retrieved_at_utc: str,
        filename: str,
        accession_plain: str | None = None,
        cik_padded: str | None = None,
        media_type: str | None = None,
        content_encoding_received: str | None = None,
        compress: bool = False,
        known_observations: Iterable[RawObjectRecord] = (),
        recovery_context: Mapping[str, object] | None = None,
        fail_after: Literal["promotion", "none"] = "none",
        raise_during_stream: Callable[[], None] | None = None,
    ) -> StoredObject:
        """Write one raw object using the eleven-step atomic protocol.

        Args:
            chunks: Decoded response byte chunks.
            compress: Whether the payload is text-like and should be gzipped.
            known_observations: Prior observations of the same logical object, used
                to detect changed remote content.
            fail_after: Test hook. ``"promotion"`` raises after the atomic rename
                but before the caller can commit, to exercise crash recovery.
            raise_during_stream: Test hook invoked mid-stream to simulate an
                interrupted transfer.
        """
        directory = self._directory_for(accession_plain, cik_padded, logical_role)
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / (filename + (_GZIP_SUFFIX if compress else ""))
        part_path = directory / f"{filename}.{uuid.uuid4().hex}{_PART_SUFFIX}"

        digest = hashlib.sha256()
        content_size = 0
        # A streaming compressor rather than a whole-object one. Its output is byte-identical to
        # `compress_deterministically` for the same input, so the frozen stored representation is
        # unchanged; what changes is that no step here is proportional to the object's size.
        compressor = (
            zlib.compressobj(GZIP_COMPRESSION_LEVEL, zlib.DEFLATED, _GZIP_WBITS)
            if compress
            else None
        )
        # Any failure below leaves the .part file in place: it is preserved for
        # reconciliation and never deleted here.
        with part_path.open("wb") as handle:
            for chunk in chunks:
                if raise_during_stream is not None:
                    raise_during_stream()
                digest.update(chunk)
                content_size += len(chunk)
                if compressor is None:
                    handle.write(chunk)
                else:
                    handle.write(compressor.compress(chunk))
            if compressor is not None:
                handle.write(compressor.flush())
            handle.flush()
            os.fsync(handle.fileno())

        content_sha256 = digest.hexdigest()
        # One bounded pass over what was just written establishes the stored digest, the exact
        # stored size, and — for a gzip object — the digest of what it decompresses back to.
        measured = _measure_stored_file(part_path, decompressing=compress)
        stored_sha256 = measured.stored_sha256

        if compress and measured.decompressed_sha256 != content_sha256:
            message = "deterministic gzip round trip did not reproduce content_sha256"
            raise RawObjectIntegrityError(message)

        superseded = self._superseded_observation(known_observations, content_sha256)
        # A hard-link promotion is same-filesystem, atomic, and cannot overwrite an
        # existing object. If the destination already exists, deduplication is allowed
        # only after its exact stored hash verifies.
        try:
            os.link(part_path, destination)
        except FileExistsError:
            existing_hash = (
                _measure_stored_file(destination, decompressing=False).stored_sha256
                if destination.is_file()
                else None
            )
            if existing_hash != stored_sha256:
                message = (
                    f"refusing to overwrite existing raw object {destination}: its stored "
                    "hash does not match the object being promoted"
                )
                raise RawObjectIntegrityError(message) from None
            part_path.unlink()
        else:
            part_path.unlink()

        if recovery_context is not None:
            self._write_lineage_intent(
                destination,
                {
                    **recovery_context,
                    "manifest_version": "raw-object-lineage/1.0",
                    "relative_storage_path": relative_to_root(destination, self._tree.data_root),
                    "stored_sha256": stored_sha256,
                    "stored_size_bytes": measured.stored_size_bytes,
                    "content_sha256": content_sha256,
                    "logical_sha256": content_sha256,
                    "content_size_bytes": content_size,
                    "storage_representation": ("deterministic_gzip" if compress else "identical"),
                },
            )
        self._fsync_directory(directory)

        if fail_after == "promotion":
            message = "simulated crash after promotion and before catalog commit"
            raise RawObjectIntegrityError(message)

        record = RawObjectRecord(
            raw_object_id=self._object_id(source_url_canonical),
            observation_id=uuid.uuid4().hex,
            logical_role=logical_role,
            source_url_canonical=source_url_canonical,
            relative_storage_path=relative_to_root(destination, self._tree.data_root),
            media_type=media_type,
            content_encoding_received=content_encoding_received,
            content_sha256=content_sha256,
            stored_sha256=stored_sha256,
            content_size_bytes=content_size,
            stored_size_bytes=measured.stored_size_bytes,
            compression="gzip" if compress else "none",
            retrieved_at_utc=retrieved_at_utc,
            retrieval_attempt_id=retrieval_attempt_id,
            accession_plain=accession_plain,
            cik_padded=cik_padded,
            supersedes_observation_id=superseded,
            reason_code="REMOTE_CONTENT_CHANGED" if superseded else None,
        )
        return StoredObject(record=record, absolute_path=destination)

    @staticmethod
    def lineage_path(path: Path) -> Path:
        """Return the durable recovery-intent path for a promoted object."""
        return path.with_name(path.name + LINEAGE_SUFFIX)

    def _write_lineage_intent(
        self,
        destination: Path,
        payload: Mapping[str, object],
    ) -> None:
        """Create recovery lineage without replacing an existing owner's intent."""
        lineage = self.lineage_path(destination)
        encoded = (json.dumps(dict(payload), sort_keys=True) + "\n").encode("utf-8")
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            descriptor = os.open(lineage, flags, 0o600)
        except FileExistsError:
            # A deduplicated object may already carry the original observation's
            # recovery intent. Never rewrite that evidence.
            return
        try:
            os.write(descriptor, encoded)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    # -- verification and quarantine ---------------------------------------- #
    def verify(self, record: RawObjectRecord) -> bool:
        """Return whether the file on disk is still exactly the object ``record`` describes.

        Read in bounded blocks, so verifying a bulk archive costs no more memory than verifying a
        small object.

        A raw object is **one exact immutable stored representation**, so recovering the expected
        decoded bytes is not on its own a passing answer — bytes that decode correctly can still
        be the wrong stored object. Every identity the record carries is therefore checked:

        * the stored bytes' digest and length match ``stored_sha256`` and ``stored_size_bytes``;
        * the decoded bytes' digest and length match ``content_sha256`` and ``content_size_bytes``;
        * a gzip object is one complete gzip member and nothing else
          (:func:`_require_one_complete_gzip_member`).

        Damage fails closed as ``False``, whatever kind it is: a short read, a corrupted byte, a
        truncated trailer, appended bytes, a concatenated second member, or bytes that are not a
        gzip stream at all. Distinguishing those is diagnosis, not verification, and this method
        was asked a yes-or-no question. Genuine filesystem and OS failures are *not* caught — an
        unreadable disk is not an answer of "no", and it still propagates.
        """
        path = self._tree.data_root / record.relative_storage_path
        if not path.is_file():
            return False
        try:
            measured = _measure_stored_file(path, decompressing=record.compression == "gzip")
        except RawObjectIntegrityError:
            return False
        decoded_sha256 = (
            measured.stored_sha256
            if measured.decompressed_sha256 is None
            else measured.decompressed_sha256
        )
        decoded_size_bytes = (
            measured.stored_size_bytes
            if measured.decompressed_size_bytes is None
            else measured.decompressed_size_bytes
        )
        return (
            measured.stored_sha256 == record.stored_sha256
            and measured.stored_size_bytes == record.stored_size_bytes
            and decoded_sha256 == record.content_sha256
            and decoded_size_bytes == record.content_size_bytes
        )

    def quarantine(self, path: Path, reason_code: str, detail: str) -> Path:
        """Durably move a damaged or partial file into quarantine, preserving it."""
        self._tree.quarantine.mkdir(parents=True, exist_ok=True)
        source_directory = path.parent
        target = self._tree.quarantine / f"{uuid.uuid4().hex}__{path.name}"
        path.replace(target)
        with target.open("rb") as handle:
            os.fsync(handle.fileno())
        self._fsync_directory(source_directory)
        if source_directory != self._tree.quarantine:
            self._fsync_directory(self._tree.quarantine)

        marker = target.with_suffix(target.suffix + ".reason")
        marker_part = marker.with_name(f"{marker.name}.{uuid.uuid4().hex}{_PART_SUFFIX}")
        with marker_part.open("xb") as handle:
            handle.write(f"{reason_code}\n{detail}\n".encode())
            handle.flush()
            os.fsync(handle.fileno())
        marker_part.replace(marker)
        self._fsync_directory(self._tree.quarantine)
        return target

    def reconcile(self, known: Iterable[RawObjectRecord]) -> ReconciliationReport:
        """Reconcile the filesystem with the catalog after an interrupted run.

        This catalog-independent helper cannot prove a source registry identity or
        request lineage, so it quarantines every unrecorded object. Verified adoption
        is performed only by :func:`disclosure_drift.sec.observation_catalog.reconcile`,
        which has the authoritative catalog and durable lineage intent. Nothing is
        deleted.
        """
        recorded_paths = {record.relative_storage_path for record in known}
        adopted: list[str] = []
        quarantined: list[str] = []
        missing = [
            record.relative_storage_path
            for record in known
            if not (self._tree.data_root / record.relative_storage_path).is_file()
        ]

        for path in sorted(self._iter_stored_files()):
            relative = relative_to_root(path, self._tree.data_root)
            if path.name.endswith(_PART_SUFFIX):
                quarantined.append(
                    relative_to_root(
                        self.quarantine(
                            path,
                            "RAW_PARTIAL_DOWNLOAD",
                            "partial transfer found during reconciliation",
                        ),
                        self._tree.data_root,
                    )
                )
                continue
            if relative not in recorded_paths:
                quarantined.append(
                    relative_to_root(
                        self.quarantine(
                            path,
                            "RAW_FILE_CHECKSUM_MISMATCH",
                            "unrecorded raw object lacks catalog context for verified adoption",
                        ),
                        self._tree.data_root,
                    )
                )

        return ReconciliationReport(
            adopted=tuple(adopted),
            quarantined=tuple(quarantined),
            missing_files=tuple(missing),
        )

    # -- internals ---------------------------------------------------------- #
    def _iter_stored_files(self) -> Iterator[Path]:
        for root in (self._tree.raw_filings, self._tree.raw_bulk, self._tree.raw_indexes):
            if root.is_dir():
                for path in root.rglob("*"):
                    if (
                        path.is_file()
                        and not path.name.endswith(".reason")
                        and not path.name.endswith(LINEAGE_SUFFIX)
                    ):
                        yield path

    def _directory_for(
        self,
        accession_plain: str | None,
        cik_padded: str | None,
        logical_role: str,
    ) -> Path:
        if accession_plain and cik_padded:
            return self._tree.accession_directory(cik_padded, accession_plain)
        if logical_role in {"bulk_archive"}:
            return self._tree.raw_bulk
        return self._tree.raw_indexes

    @staticmethod
    def _object_id(source_url_canonical: str) -> str:
        return hashlib.sha256(source_url_canonical.encode("utf-8")).hexdigest()[:32]

    @staticmethod
    def _superseded_observation(
        known: Iterable[RawObjectRecord],
        content_sha256: str,
    ) -> str | None:
        latest: RawObjectRecord | None = None
        for record in known:
            if latest is None or record.retrieved_at_utc > latest.retrieved_at_utc:
                latest = record
        if latest is None or latest.content_sha256 == content_sha256:
            return None
        return latest.observation_id

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        try:
            descriptor = os.open(directory, os.O_RDONLY)
        except OSError:  # pragma: no cover - platform dependent
            return
        try:
            with suppress(OSError):  # pragma: no cover - best effort
                os.fsync(descriptor)
        finally:
            os.close(descriptor)
