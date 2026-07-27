"""Immutable raw-object storage with an atomic write protocol (Decision 009).

Guarantees implemented here:

* a ``.part`` file is never treated as complete;
* promotion is an atomic, no-overwrite hard link and the parent directory is fsynced;
* ``content_sha256`` covers decoded entity bytes and is the integrity anchor;
* text-like payloads use deterministic gzip whose round trip must reproduce
  ``content_sha256``;
* a later differing response becomes a **new observation**, never an overwrite;
* damaged files are quarantined and preserved, never replaced or deleted;
* crash recovery may only adopt a valid orphan or quarantine a partial file.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import uuid
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
_PART_SUFFIX: Final = ".part"
_GZIP_SUFFIX: Final = ".gz"
LINEAGE_SUFFIX: Final = ".lineage.json"
Compression = Literal["none", "gzip"]


def sha256_of(data: bytes) -> str:
    """Return the hex SHA-256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def compress_deterministically(data: bytes) -> bytes:
    """Compress with gzip in a reproducible way (level 6, mtime 0)."""
    return gzip.compress(data, compresslevel=GZIP_COMPRESSION_LEVEL, mtime=0)


def decompress(data: bytes) -> bytes:
    """Decompress gzip bytes."""
    return gzip.decompress(data)


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
        buffer = bytearray()
        # Any failure below leaves the .part file in place: it is preserved for
        # reconciliation and never deleted here.
        with part_path.open("wb") as handle:
            for chunk in chunks:
                if raise_during_stream is not None:
                    raise_during_stream()
                digest.update(chunk)
                content_size += len(chunk)
                buffer.extend(chunk)
                if not compress:
                    handle.write(chunk)
            if compress:
                handle.write(compress_deterministically(bytes(buffer)))
            handle.flush()
            os.fsync(handle.fileno())

        content_sha256 = digest.hexdigest()
        stored_bytes = part_path.read_bytes()
        stored_sha256 = sha256_of(stored_bytes)

        if compress and sha256_of(decompress(stored_bytes)) != content_sha256:
            message = "deterministic gzip round trip did not reproduce content_sha256"
            raise RawObjectIntegrityError(message)

        superseded = self._superseded_observation(known_observations, content_sha256)
        # A hard-link promotion is same-filesystem, atomic, and cannot overwrite an
        # existing object. If the destination already exists, deduplication is allowed
        # only after its exact stored hash verifies.
        try:
            os.link(part_path, destination)
        except FileExistsError:
            existing_hash = sha256_of(destination.read_bytes()) if destination.is_file() else None
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
                    "stored_size_bytes": len(stored_bytes),
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
            stored_size_bytes=len(stored_bytes),
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
        """Return whether the stored bytes still match the recorded content hash."""
        path = self._tree.data_root / record.relative_storage_path
        if not path.is_file():
            return False
        stored = path.read_bytes()
        decoded = decompress(stored) if record.compression == "gzip" else stored
        return sha256_of(decoded) == record.content_sha256

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
