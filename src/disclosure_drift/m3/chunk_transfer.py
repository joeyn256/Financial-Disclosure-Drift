"""Verified transfer, exact receipts, reclaim records and interruption recovery -- D151-C22.

This module is the generic, family-independent engine behind a governed transfer of one
immutable, manifested artifact directory onto a qualified external tier, and behind the
separately authorized reclaim of its internal copy. It is deliberately written against plain
manifest entries and plain authorization objects rather than against any particular artifact
family: the family module that owns the artifacts and the closed authority constants wires it
in, holds the authority-first gates, and is the only production caller.

The rulings it implements, in the order a transfer meets them:

* **C22-R3 -- verified transfer lifecycle.** Terminal immutable source, deterministic exact
  manifest, qualified-tier reauthentication, external capacity admission, no-overwrite partial
  destination, bounded streaming copy, close and fsync (F_FULLFSYNC where available),
  independent destination reopen and full read-back, exact size/hash/manifest equality, atomic
  finalization, final destination reauthentication, and only then a durable transfer receipt.
  Nothing short of the independent read-back makes a copy verified: not the copy's exit, not
  the streaming hash, not the caller's word, not the destination's existence.
* **C22-R4 -- reclaim is a separate authorized state machine.** A transfer never implies a
  reclaim. Eligibility is a pure derived predicate; the first effective gate of the deletion
  itself is the reclaim authorization the family module obtains from its closed constant; a
  durable intent record precedes the first deletion; deletion is exact-entry, deterministic
  order, never a recursive tree removal; completion is recorded only after source absence and a
  measured free-space reconciliation. A COPY_ONLY tier is refused before eligibility.
* **C22-R5 -- integer, dynamic, pre-mutation admission.** Checked non-negative integers, no
  Booleans, no floats, measured on the charged filesystem immediately before the partial
  destination is created. ENOSPC is never control flow.
* **C22-R6 -- nonperturbing instrumentation.** An append-only JSONL ledger outside the active
  database, fed by process-local self-reporting and filesystem/process inspection only. The
  sampler stats a write-ahead log's size and a volume's free bytes; it never opens a database.
* **C22-R7 -- interruption and idempotent recovery.** Seven explicit states, derived from what
  is on disk; a partial copy is removed exactly and recopied; an unreceipted final destination
  is independently reverified before a receipt is written; a receipt with a missing or
  conflicting destination refuses; an intent with an exact remaining subset resumes; a
  completion with the source still present refuses; an unknown or relabelled contract refuses
  without upgrade.

The verified transfer receipt contract is exactly ``m3.3-chunked-f0-transfer-receipt/2`` and the
reclaim record contract is exactly ``m3.3-chunked-f0-reclaim-record/1`` (D151-C22E-R1). The
accepted single-pass receipt keeps ``m3.3-chunked-f0-transfer-receipt/1`` and its own exact
shape; one contract string maps to one exact shape, and a ``/1`` receipt confers no C22
verification, eligibility, intent or completion. No ``/3``, no alias, no automatic upgrade,
relabel, fallback or field-defaulting: a document of another version or shape is refused where it
is met, and never rewritten.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_runtime import process_peak_resident_bytes
from disclosure_drift.m3.host_a_ssd_qualification import (
    HostASsdQualification,
    HostASsdQualificationError,
    LiveTierObservation,
    canonical_json_bytes,
    require_copy_capable,
    require_reclaim_capable,
    require_tier_reauthentication,
    sealed_identity,
)

__all__ = [
    "EVIDENCE_OVERHEAD_BYTES",
    "RECLAIM_COMPLETE",
    "RECLAIM_COMPLETE_FILENAME",
    "RECLAIM_DIRECTORY_SUFFIX",
    "RECLAIM_INTENT",
    "RECLAIM_INTENT_FILENAME",
    "RECLAIM_RECORD_CONTRACT",
    "RECLAIM_RECORD_FIELDS",
    "RECLAIM_RECORD_IDENTITY_KEY",
    "RECLAIM_RECORD_KINDS",
    "PARTIAL_SUFFIX",
    "RECEIPT_IDENTITY_KEY",
    "SAMPLE_FIELDS",
    "SOURCE_RECEIPT_FILENAME",
    "STATE_FINAL_UNVERIFIED",
    "STATE_NOT_STARTED",
    "STATE_PARTIAL_COPY",
    "STATE_RECLAIM_COMPLETE",
    "STATE_RECLAIM_INTENT_DURABLE",
    "STATE_RECLAIM_IN_PROGRESS",
    "STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE",
    "LEGACY_TRANSFER_RECEIPT_CONTRACT",
    "TRANSFER_OUTCOME_VERIFIED",
    "TRANSFER_RECEIPT_FIELDS",
    "TRANSFER_RECEIPT_FILENAME",
    "TRANSFER_RECEIPT_REQUIRED_BINDINGS",
    "TRANSFER_STATES",
    "VERIFIED_TRANSFER_RECEIPT_CONTRACT",
    "ChunkTransferError",
    "ExternalAdmission",
    "InstrumentationLedger",
    "ManifestEntry",
    "ReclaimAuthorization",
    "ReclaimEligibilityReport",
    "ReclaimRecord",
    "TransferAuthorization",
    "TransferSource",
    "TransferStateReport",
    "VerifiedTransferReceipt",
    "allocation_overhead_bytes",
    "derive_transfer_state",
    "entries_from_record",
    "external_transfer_requirement",
    "manifest_digest",
    "manifest_record",
    "measured_free_bytes",
    "reclaim_eligibility",
    "reclaim_source",
    "recover_transfer",
    "require_count",
    "require_external_admission",
    "require_terminal_source",
    "swap_used_bytes",
    "utc_now",
    "verified_transfer",
    "write_reclaim_intent",
]


class ChunkTransferError(DisclosureDriftError):
    """A transfer, receipt, reclaim, admission or telemetry step is refused."""


#: The verified transfer receipt contract -- D151-C22E-R1. This module writes only this version
#: and its exact parser accepts only this version.
VERIFIED_TRANSFER_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-transfer-receipt/2"
#: The accepted single-pass receipt contract, named here only so a ``/1`` document met on a C22
#: route is refused by name: it is never read as a superset, relabelled, resealed or upgraded.
LEGACY_TRANSFER_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-transfer-receipt/1"
#: The reclaim record contract, for both record kinds.
RECLAIM_RECORD_CONTRACT: Final = "m3.3-chunked-f0-reclaim-record/1"
#: The two reclaim record kinds, distinguished by the required ``record_kind`` field.
RECLAIM_INTENT: Final = "reclaim_intent"
RECLAIM_COMPLETE: Final = "reclaim_complete"
RECLAIM_RECORD_KINDS: Final[tuple[str, ...]] = (RECLAIM_INTENT, RECLAIM_COMPLETE)
#: File names. The transfer receipt lives inside the final destination, written LAST; the two
#: reclaim records live in a sibling directory beside it so the artifact set stays exact.
TRANSFER_RECEIPT_FILENAME: Final = "transfer_receipt.json"
RECLAIM_INTENT_FILENAME: Final = "reclaim_intent.json"
RECLAIM_COMPLETE_FILENAME: Final = "reclaim_complete.json"
RECLAIM_DIRECTORY_SUFFIX: Final = ".reclaim"
#: The source's own terminal receipt travels with the copy, outside the manifest.
SOURCE_RECEIPT_FILENAME: Final = "chunk_receipt.json"
#: A destination being copied is ``<chunk_id>.partial`` until it is finalized by one rename.
PARTIAL_SUFFIX: Final = ".partial"
#: The identity keys: SHA-256 over the canonical record without the key.
RECEIPT_IDENTITY_KEY: Final = "receipt_identity"
RECLAIM_RECORD_IDENTITY_KEY: Final = "record_identity"
#: The only transfer outcome a receipt may record.
TRANSFER_OUTCOME_VERIFIED: Final = "verified"
#: Receipt and record allowance charged to every external admission.
EVIDENCE_OVERHEAD_BYTES: Final = 1 << 20

#: The seven lifecycle states -- C22-R7.
STATE_NOT_STARTED: Final = "not_started"
STATE_PARTIAL_COPY: Final = "partial_copy"
STATE_FINAL_UNVERIFIED: Final = "final_unverified"
STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE: Final = "transfer_verified_receipt_durable"
STATE_RECLAIM_INTENT_DURABLE: Final = "reclaim_intent_durable"
STATE_RECLAIM_IN_PROGRESS: Final = "reclaim_in_progress"
STATE_RECLAIM_COMPLETE: Final = "reclaim_complete"
TRANSFER_STATES: Final[tuple[str, ...]] = (
    STATE_NOT_STARTED,
    STATE_PARTIAL_COPY,
    STATE_FINAL_UNVERIFIED,
    STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE,
    STATE_RECLAIM_INTENT_DURABLE,
    STATE_RECLAIM_IN_PROGRESS,
    STATE_RECLAIM_COMPLETE,
)

#: The bindings a receipt supplies to the accepted reclaim-eligibility predicate.
TRANSFER_RECEIPT_REQUIRED_BINDINGS: Final[tuple[str, ...]] = (
    "source_chunk_id",
    "source_manifest_digest",
    "source_receipt_sha256",
    "source_bytes",
    "source_plan_digest",
    "source_repository_head_sha",
    "source_repository_tree_sha",
    "destination_volume_identity",
    "destination_canonical_path",
    "destination_bytes",
    "destination_manifest_verified",
    "destination_content_verified",
    "transfer_started_at_utc",
    "transfer_completed_at_utc",
    "transfer_outcome",
)
#: The exact top-level key set of a verified transfer receipt.
TRANSFER_RECEIPT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "bytes_transferred",
        "chunk_id",
        "chunk_receipt_manifest_digest",
        "contract",
        "destination_bytes",
        "destination_canonical_path",
        "destination_content_verified",
        "destination_manifest",
        "destination_manifest_verified",
        "destination_volume_identity",
        "destination_volume_uuid",
        "durability",
        "objects",
        "plan_digest",
        "qualification_class",
        "qualification_identity",
        "receipt_identity",
        "recovered_from_state",
        "source_bytes",
        "source_manifest_digest",
        "source_receipt_sha256",
        "source_repository_head_sha",
        "source_repository_tree_sha",
        "stable_tier_compatibility_identity",
        "status",
        "transfer_completed_at_utc",
        "transfer_outcome",
        "transfer_started_at_utc",
        "verified_at_utc",
    }
)
#: The exact key set of a reclaim record, both kinds.
RECLAIM_RECORD_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "chunk_id",
        "completed_at_utc",
        "contract",
        "deleted_entries",
        "entries",
        "expected_freed_bytes",
        "free_after_bytes",
        "free_before_bytes",
        "freed_bytes",
        "issued_at_utc",
        "qualification_identity",
        "receipt_identity",
        "reconciled",
        "record_identity",
        "record_kind",
        "source_bytes",
        "source_manifest_digest",
    }
)
#: The exact field set of every instrumentation sample -- C22-R6.
SAMPLE_FIELDS: Final[tuple[str, ...]] = (
    "phase",
    "monotonic_s",
    "utc",
    "pid",
    "rss_bytes",
    "swap_used_bytes",
    "internal_free_bytes",
    "internal_low_water_bytes",
    "external_free_bytes",
    "external_low_water_bytes",
    "bytes_copied",
    "bytes_read_back",
    "copy_bytes_per_second",
    "read_bytes_per_second",
    "sqlite_temp_high_water_bytes",
    "wal_high_water_bytes",
    "retained_input_bytes",
    "output_bytes",
    "sorter_workfile_observations",
    "process_exit_rss_reclaimed_bytes",
    "qualification_identity",
    "tier_reauthentication",
)

_COPY_BLOCK: Final = 1 << 20
_DIRECTORY_MODE: Final = 0o700
_FILE_MODE: Final = 0o600
_UNCLOSED_DATABASE_SUFFIXES: Final[tuple[str, ...]] = ("-wal", "-shm", "-journal")
_HEX64: Final = re.compile(r"\A[0-9a-f]{64}\Z")
_SYSCTL: Final = "/usr/sbin/sysctl"
_F_FULLFSYNC: Final = getattr(fcntl, "F_FULLFSYNC", None)
_F_NOCACHE: Final = getattr(fcntl, "F_NOCACHE", None)


def utc_now() -> str:
    """The current instant, UTC, to the second."""
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


# --------------------------------------------------------------------------- #
# Checked integers -- C22-R5
# --------------------------------------------------------------------------- #
def require_count(value: object, name: str) -> int:
    """``value`` as a non-negative integer, or a refusal. Booleans and floats are refused."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = (
            f"{name} must be a non-negative integer, never a Boolean, a float or an absent "
            f"value; got {value!r}"
        )
        raise ChunkTransferError(message)
    return value


def _require_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        message = f"{name} must be a non-empty string; got {value!r}"
        raise ChunkTransferError(message)
    return value


def _require_hex64(value: object, name: str) -> str:
    text = _require_text(value, name)
    if _HEX64.match(text) is None:
        message = f"{name} must be a 64-hex-digit digest; refused"
        raise ChunkTransferError(message)
    return text


def _require_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        message = f"{name} must be a Boolean; got {value!r}"
        raise ChunkTransferError(message)
    return value


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = f"{name} must be an object; refused"
        raise ChunkTransferError(message)
    return {str(key): item for key, item in value.items()}


# --------------------------------------------------------------------------- #
# Manifest entries
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ManifestEntry:
    """One object of a manifested artifact directory: relative POSIX path, length, digest."""

    relative_path: str
    byte_length: int
    sha256: str

    def __post_init__(self) -> None:
        path = _require_text(self.relative_path, "relative_path")
        parts = path.split("/")
        if path.startswith("/") or "\\" in path or any(part in ("", ".", "..") for part in parts):
            message = f"manifest entry path {path!r} is not a plain relative POSIX path; refused"
            raise ChunkTransferError(message)
        require_count(self.byte_length, "byte_length")
        _require_hex64(self.sha256, "sha256")

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "relative_path": self.relative_path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


def manifest_digest(entries: Sequence[ManifestEntry]) -> str:
    """A deterministic digest over every entry, in the order given.

    The same fold the accepted artifact manifest uses -- path, length and digest joined by a
    unit separator, entries terminated by a record separator -- so a source manifest digest
    carried through a receipt is reproducible from the entries beside it.
    """
    digest = hashlib.sha256()
    for entry in entries:
        digest.update(
            "\x1f".join((entry.relative_path, str(entry.byte_length), entry.sha256)).encode("utf-8")
        )
        digest.update(b"\x1e")
    return digest.hexdigest()


def manifest_record(entries: Sequence[ManifestEntry]) -> Mapping[str, object]:
    """The manifest as a plain mapping: entries, their digest, their total."""
    return {
        "entries": [dict(entry.as_record()) for entry in entries],
        "manifest_digest": manifest_digest(entries),
        "total_bytes": sum(entry.byte_length for entry in entries),
    }


def entries_from_record(record: Mapping[str, object]) -> tuple[ManifestEntry, ...]:
    """Rebuild entries from an exact manifest record and re-derive its digest and total.

    Raises:
        ChunkTransferError: the record is malformed, or its digest or total does not describe
            the entries beside it.
    """
    stored = _require_mapping(record, "manifest")
    if set(stored) != {"entries", "manifest_digest", "total_bytes"}:
        message = f"a manifest record is exact; got keys {sorted(stored)}"
        raise ChunkTransferError(message)
    raw = stored["entries"]
    if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
        message = "a manifest record's entries must be a list; refused"
        raise ChunkTransferError(message)
    entries = []
    for item in raw:
        fields = _require_mapping(item, "manifest entry")
        if set(fields) != {"relative_path", "byte_length", "sha256"}:
            message = f"a manifest entry is exact; got keys {sorted(fields)}"
            raise ChunkTransferError(message)
        entries.append(
            ManifestEntry(
                relative_path=_require_text(fields["relative_path"], "relative_path"),
                byte_length=require_count(fields["byte_length"], "byte_length"),
                sha256=_require_hex64(fields["sha256"], "sha256"),
            )
        )
    rebuilt = tuple(entries)
    if stored["manifest_digest"] != manifest_digest(rebuilt):
        message = "a manifest record's digest does not describe its own entries; refused"
        raise ChunkTransferError(message)
    if stored["total_bytes"] != sum(entry.byte_length for entry in rebuilt):
        message = "a manifest record's total does not describe its own entries; refused"
        raise ChunkTransferError(message)
    return rebuilt


# --------------------------------------------------------------------------- #
# Source, authorizations, admission
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class TransferSource:
    """One terminal, immutable, manifested artifact directory and the identities it carries.

    The family module that owns the artifacts constructs this from a **verified** terminal
    receipt; nothing here re-derives the identities from the directory's own say-so.
    """

    chunk_id: str
    plan_digest: str
    directory: Path
    entries: tuple[ManifestEntry, ...]
    receipt_sha256: str
    receipt_bytes: int
    repository_head_sha: str
    repository_tree_sha: str

    def __post_init__(self) -> None:
        _require_text(self.chunk_id, "chunk_id")
        _require_text(self.plan_digest, "plan_digest")
        if not self.entries:
            message = "a transfer source with no manifest entries is refused"
            raise ChunkTransferError(message)
        paths = [entry.relative_path for entry in self.entries]
        if paths != sorted(paths) or len(set(paths)) != len(paths):
            message = "a transfer source's entries must be unique and in relative-path order"
            raise ChunkTransferError(message)
        if SOURCE_RECEIPT_FILENAME in paths:
            message = "the source's terminal receipt is never a manifest entry; refused"
            raise ChunkTransferError(message)
        _require_hex64(self.receipt_sha256, "receipt_sha256")
        require_count(self.receipt_bytes, "receipt_bytes")
        _require_text(self.repository_head_sha, "repository_head_sha")
        _require_text(self.repository_tree_sha, "repository_tree_sha")

    @property
    def manifest_digest(self) -> str:
        """The digest over the source's entries."""
        return manifest_digest(self.entries)

    @property
    def total_bytes(self) -> int:
        """The bytes the manifest's objects occupy in total."""
        return sum(entry.byte_length for entry in self.entries)


@dataclass(frozen=True, slots=True)
class TransferAuthorization:
    """The grant a governed transfer runs under: the value the family module's closed
    transfer-authority constant granted, or an isolated test grant over disposable fixtures;
    never derived from a receipt or a path."""

    grant: str
    granted_by: str

    def __post_init__(self) -> None:
        _require_text(self.grant, "transfer authorization grant")
        _require_text(self.granted_by, "transfer authorization grantor")


@dataclass(frozen=True, slots=True)
class ReclaimAuthorization:
    """The grant a governed reclaim deletes under. A transfer authorization, a transfer receipt,
    an intent record and eligibility are each necessary and none is this."""

    grant: str
    granted_by: str

    def __post_init__(self) -> None:
        _require_text(self.grant, "reclaim authorization grant")
        _require_text(self.granted_by, "reclaim authorization grantor")


@dataclass(frozen=True, slots=True)
class ExternalAdmission:
    """One external admission decision with every term it was made from -- C22-R5."""

    free_bytes: int
    source_bytes: int
    partial_copy_overhead_bytes: int
    evidence_overhead_bytes: int
    reserve_bytes: int
    required_bytes: int
    admitted: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "free_bytes": self.free_bytes,
            "source_bytes": self.source_bytes,
            "partial_copy_overhead_bytes": self.partial_copy_overhead_bytes,
            "evidence_overhead_bytes": self.evidence_overhead_bytes,
            "reserve_bytes": self.reserve_bytes,
            "required_bytes": self.required_bytes,
            "admitted": self.admitted,
        }


def external_transfer_requirement(
    *,
    source_bytes: int,
    partial_copy_overhead_bytes: int,
    evidence_overhead_bytes: int,
    reserve_bytes: int,
) -> int:
    """``source + partial overhead + evidence overhead + reserve``, every term checked."""
    return (
        require_count(source_bytes, "source_bytes")
        + require_count(partial_copy_overhead_bytes, "partial_copy_overhead_bytes")
        + require_count(evidence_overhead_bytes, "evidence_overhead_bytes")
        + require_count(reserve_bytes, "reserve_bytes")
    )


def require_external_admission(
    *,
    free_bytes: int,
    source_bytes: int,
    partial_copy_overhead_bytes: int,
    evidence_overhead_bytes: int,
    reserve_bytes: int,
) -> ExternalAdmission:
    """Admit a transfer onto the external tier, or refuse it BEFORE anything is created.

    ``>=`` at the floor: the floor itself admits and one byte below refuses.

    Raises:
        ChunkTransferError: a term is not a non-negative integer, or the floor is not met.
    """
    free = require_count(free_bytes, "free_bytes")
    required = external_transfer_requirement(
        source_bytes=source_bytes,
        partial_copy_overhead_bytes=partial_copy_overhead_bytes,
        evidence_overhead_bytes=evidence_overhead_bytes,
        reserve_bytes=reserve_bytes,
    )
    decision = ExternalAdmission(
        free_bytes=free,
        source_bytes=source_bytes,
        partial_copy_overhead_bytes=partial_copy_overhead_bytes,
        evidence_overhead_bytes=evidence_overhead_bytes,
        reserve_bytes=reserve_bytes,
        required_bytes=required,
        admitted=free >= required,
    )
    if not decision.admitted:
        message = (
            f"the transfer is NOT ADMITTED onto the external tier: {free} bytes free, below the "
            f"required {required} = {source_bytes} source + {partial_copy_overhead_bytes} "
            f"partial-copy overhead + {evidence_overhead_bytes} evidence overhead + "
            f"{reserve_bytes} reserve. Nothing was created, and there is no mode that copies "
            "until the filesystem refuses"
        )
        raise ChunkTransferError(message)
    return decision


def _nearest_existing(path: Path) -> Path:
    candidate = Path(os.path.realpath(path))
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def measured_free_bytes(path: Path) -> int:
    """Free bytes on the filesystem hosting ``path``, measured now (nearest existing ancestor)."""
    statistics = os.statvfs(_nearest_existing(path))
    return statistics.f_bavail * statistics.f_frsize


def allocation_overhead_bytes(entries: Sequence[ManifestEntry], path: Path) -> int:
    """The partial-copy rounding overhead: one allocation unit per object, plus the receipt."""
    statistics = os.statvfs(_nearest_existing(path))
    return (len(entries) + 1) * statistics.f_frsize


# --------------------------------------------------------------------------- #
# Durable primitives
# --------------------------------------------------------------------------- #
def _fullfsync(descriptor: int) -> str:
    if _F_FULLFSYNC is None:
        return "unavailable"
    try:
        fcntl.fcntl(descriptor, _F_FULLFSYNC)
    except OSError as exc:
        return f"unsupported:{exc.errno}"
    return "succeeded"


def _fsync_directory(directory: Path) -> tuple[str, str]:
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        try:
            os.fsync(descriptor)
            fsync = "succeeded"
        except OSError as exc:
            fsync = f"unsupported:{exc.errno}"
        full = _fullfsync(descriptor)
    finally:
        os.close(descriptor)
    return fsync, full


def _write_once(path: Path, payload: bytes) -> None:
    """Create-once, write, flush, fsync, F_FULLFSYNC, close, then fsync the parent directory."""
    if path.is_symlink():
        message = f"{path.name!r} exists as a symbolic link and is never written through"
        raise ChunkTransferError(message)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _FILE_MODE)
    except FileExistsError as exc:
        message = (
            f"{path.name!r} already exists; this record is create-once and is never overwritten, "
            "repaired or re-stamped"
        )
        raise ChunkTransferError(message) from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        _fullfsync(handle.fileno())
    _fsync_directory(path.parent)


def _read_document(path: Path, *, contract: str, label: str) -> Mapping[str, object]:
    if path.is_symlink():
        message = f"{label} {path.name!r} is a symbolic link and is refused rather than read"
        raise ChunkTransferError(message)
    if not path.is_file():
        message = f"no {label} exists at {path.name!r}"
        raise ChunkTransferError(message)
    raw = path.read_bytes()
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"{label} {path.name!r} is not decodable canonical JSON: {exc}"
        raise ChunkTransferError(message) from exc
    if not isinstance(decoded, dict):
        message = f"{label} {path.name!r} is not a JSON object; refused"
        raise ChunkTransferError(message)
    # Contract FIRST (D151-C22E-R1): the version selects the shape, and byte-canonical form is
    # part of this build's shape, so a document of another version is refused by name before
    # its serialization is judged.
    observed = decoded.get("contract")
    if observed == LEGACY_TRANSFER_RECEIPT_CONTRACT and contract != observed:
        message = (
            f"{label} {path.name!r} carries the accepted legacy contract {observed!r}; a legacy "
            "single-pass receipt confers no C22 verification, eligibility, intent or completion "
            f"and is never relabelled or upgraded to {contract!r}. Refused; the file is untouched"
        )
        raise ChunkTransferError(message)
    if observed != contract:
        message = (
            f"{label} {path.name!r} carries contract {observed!r}; this build reads exactly "
            f"{contract!r} and never upgrades, aliases or reinterprets another"
        )
        raise ChunkTransferError(message)
    if canonical_json_bytes(decoded) != raw:
        message = f"{label} {path.name!r} is not byte-canonical; an edited record is refused"
        raise ChunkTransferError(message)
    return {str(key): value for key, value in decoded.items()}


# --------------------------------------------------------------------------- #
# The verified transfer receipt
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class VerifiedTransferReceipt:
    """One verified transfer's create-once terminal record, addendum-complete -- C22-R3."""

    contract: str
    chunk_id: str
    plan_digest: str
    source_manifest_digest: str
    source_receipt_sha256: str
    source_bytes: int
    source_repository_head_sha: str
    source_repository_tree_sha: str
    destination_volume_uuid: str
    destination_canonical_path: str
    destination_bytes: int
    destination_entries: tuple[ManifestEntry, ...]
    destination_manifest_verified: bool
    destination_content_verified: bool
    qualification_identity: str
    stable_tier_compatibility_identity: str
    qualification_class: str
    transfer_started_at_utc: str
    transfer_completed_at_utc: str
    transfer_outcome: str
    durability: Mapping[str, str]
    recovered_from_state: str | None
    receipt_identity: str

    @property
    def objects(self) -> int:
        """How many objects the destination manifest binds."""
        return len(self.destination_entries)

    def as_record(self) -> Mapping[str, object]:
        """The complete receipt as a plain mapping, identity included."""
        return {**self._body(), RECEIPT_IDENTITY_KEY: self.receipt_identity}

    def _body(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "chunk_id": self.chunk_id,
            "plan_digest": self.plan_digest,
            "chunk_receipt_manifest_digest": self.source_manifest_digest,
            "source_manifest_digest": self.source_manifest_digest,
            "source_receipt_sha256": self.source_receipt_sha256,
            "source_bytes": self.source_bytes,
            "source_repository_head_sha": self.source_repository_head_sha,
            "source_repository_tree_sha": self.source_repository_tree_sha,
            "destination_volume_uuid": self.destination_volume_uuid,
            "destination_volume_identity": self.destination_volume_uuid,
            "destination_canonical_path": self.destination_canonical_path,
            "destination_bytes": self.destination_bytes,
            "bytes_transferred": self.destination_bytes,
            "objects": self.objects,
            "destination_manifest": dict(manifest_record(self.destination_entries)),
            "destination_manifest_verified": self.destination_manifest_verified,
            "destination_content_verified": self.destination_content_verified,
            "qualification_identity": self.qualification_identity,
            "stable_tier_compatibility_identity": self.stable_tier_compatibility_identity,
            "qualification_class": self.qualification_class,
            "transfer_started_at_utc": self.transfer_started_at_utc,
            "transfer_completed_at_utc": self.transfer_completed_at_utc,
            "verified_at_utc": self.transfer_completed_at_utc,
            "transfer_outcome": self.transfer_outcome,
            "status": self.transfer_outcome,
            "durability": dict(self.durability),
            "recovered_from_state": self.recovered_from_state,
        }

    def bindings(self) -> Mapping[str, object]:
        """Exactly the bindings the accepted reclaim-eligibility predicate requires."""
        record = self.as_record()
        return {
            "receipt_contract": record["contract"],
            "receipt_identity": record[RECEIPT_IDENTITY_KEY],
            "source_chunk_id": record["chunk_id"],
            "source_manifest_digest": record["source_manifest_digest"],
            "source_receipt_sha256": record["source_receipt_sha256"],
            "source_bytes": record["source_bytes"],
            "source_plan_digest": record["plan_digest"],
            "source_repository_head_sha": record["source_repository_head_sha"],
            "source_repository_tree_sha": record["source_repository_tree_sha"],
            "destination_volume_identity": record["destination_volume_identity"],
            "destination_canonical_path": record["destination_canonical_path"],
            "destination_bytes": record["destination_bytes"],
            "destination_manifest_verified": record["destination_manifest_verified"],
            "destination_content_verified": record["destination_content_verified"],
            "transfer_started_at_utc": record["transfer_started_at_utc"],
            "transfer_completed_at_utc": record["transfer_completed_at_utc"],
            "transfer_outcome": record["transfer_outcome"],
        }

    @classmethod
    def seal(cls, **fields: object) -> VerifiedTransferReceipt:
        """Construct and seal a receipt: the identity is computed over its own body."""
        unsealed = cls(**fields, receipt_identity="0" * 64)  # type: ignore[arg-type]
        identity = sealed_identity(unsealed.as_record(), identity_key=RECEIPT_IDENTITY_KEY)
        return cls(**fields, receipt_identity=identity)  # type: ignore[arg-type]

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> VerifiedTransferReceipt:
        """Read one receipt exactly, or refuse -- no missing, extra, relabelled, stale or
        type-confused field, no duplicate-key disagreement, no automatic repair.

        Raises:
            ChunkTransferError: any refusal.
        """
        stored = _require_mapping(document, "transfer receipt")
        present = set(stored)
        if present != TRANSFER_RECEIPT_FIELDS:
            message = (
                "a transfer receipt is exact; this one is missing "
                f"{sorted(TRANSFER_RECEIPT_FIELDS - present)} and carries unexpected "
                f"{sorted(present - TRANSFER_RECEIPT_FIELDS)}; refused rather than read"
            )
            raise ChunkTransferError(message)
        if stored["contract"] == LEGACY_TRANSFER_RECEIPT_CONTRACT:
            message = (
                "a verified transfer receipt is never a legacy single-pass receipt: contract "
                f"{LEGACY_TRANSFER_RECEIPT_CONTRACT!r} is refused on every C22 route, whatever "
                "fields the document carries, and is never upgraded"
            )
            raise ChunkTransferError(message)
        if stored["contract"] != VERIFIED_TRANSFER_RECEIPT_CONTRACT:
            message = (
                f"a transfer receipt carries contract {stored['contract']!r}; this build reads "
                f"exactly {VERIFIED_TRANSFER_RECEIPT_CONTRACT!r}"
            )
            raise ChunkTransferError(message)
        if stored["transfer_outcome"] != TRANSFER_OUTCOME_VERIFIED:
            message = f"a transfer receipt records outcome {stored['transfer_outcome']!r}; refused"
            raise ChunkTransferError(message)
        for left, right in (
            ("chunk_receipt_manifest_digest", "source_manifest_digest"),
            ("destination_volume_uuid", "destination_volume_identity"),
            ("bytes_transferred", "destination_bytes"),
            ("verified_at_utc", "transfer_completed_at_utc"),
            ("status", "transfer_outcome"),
        ):
            if stored[left] != stored[right]:
                message = f"a transfer receipt's {left!r} and {right!r} disagree; refused"
                raise ChunkTransferError(message)
        entries = entries_from_record(_require_mapping(stored["destination_manifest"], "manifest"))
        if stored["objects"] != len(entries):
            message = "a transfer receipt's object count does not describe its manifest; refused"
            raise ChunkTransferError(message)
        durability = _require_mapping(stored["durability"], "durability")
        recovered = stored["recovered_from_state"]
        if recovered is not None and recovered not in TRANSFER_STATES:
            message = f"a transfer receipt names recovery state {recovered!r}; refused"
            raise ChunkTransferError(message)
        receipt = cls(
            contract=VERIFIED_TRANSFER_RECEIPT_CONTRACT,
            chunk_id=_require_text(stored["chunk_id"], "chunk_id"),
            plan_digest=_require_text(stored["plan_digest"], "plan_digest"),
            source_manifest_digest=_require_hex64(
                stored["source_manifest_digest"], "source_manifest_digest"
            ),
            source_receipt_sha256=_require_hex64(
                stored["source_receipt_sha256"], "source_receipt_sha256"
            ),
            source_bytes=require_count(stored["source_bytes"], "source_bytes"),
            source_repository_head_sha=_require_text(
                stored["source_repository_head_sha"], "source_repository_head_sha"
            ),
            source_repository_tree_sha=_require_text(
                stored["source_repository_tree_sha"], "source_repository_tree_sha"
            ),
            destination_volume_uuid=_require_text(
                stored["destination_volume_uuid"], "destination_volume_uuid"
            ),
            destination_canonical_path=_require_text(
                stored["destination_canonical_path"], "destination_canonical_path"
            ),
            destination_bytes=require_count(stored["destination_bytes"], "destination_bytes"),
            destination_entries=entries,
            destination_manifest_verified=_require_bool(
                stored["destination_manifest_verified"], "destination_manifest_verified"
            ),
            destination_content_verified=_require_bool(
                stored["destination_content_verified"], "destination_content_verified"
            ),
            qualification_identity=_require_hex64(
                stored["qualification_identity"], "qualification_identity"
            ),
            stable_tier_compatibility_identity=_require_hex64(
                stored["stable_tier_compatibility_identity"], "stable_tier_compatibility_identity"
            ),
            qualification_class=_require_text(stored["qualification_class"], "qualification_class"),
            transfer_started_at_utc=_require_text(
                stored["transfer_started_at_utc"], "transfer_started_at_utc"
            ),
            transfer_completed_at_utc=_require_text(
                stored["transfer_completed_at_utc"], "transfer_completed_at_utc"
            ),
            transfer_outcome=TRANSFER_OUTCOME_VERIFIED,
            durability={str(key): _require_text(value, key) for key, value in durability.items()},
            recovered_from_state=None if recovered is None else str(recovered),
            receipt_identity=_require_hex64(stored[RECEIPT_IDENTITY_KEY], RECEIPT_IDENTITY_KEY),
        )
        if receipt.destination_bytes != sum(entry.byte_length for entry in entries):
            message = "a transfer receipt's destination bytes do not describe its manifest"
            raise ChunkTransferError(message)
        if not (receipt.destination_manifest_verified and receipt.destination_content_verified):
            message = "a transfer receipt without both verification flags is refused"
            raise ChunkTransferError(message)
        expected = sealed_identity(receipt.as_record(), identity_key=RECEIPT_IDENTITY_KEY)
        if receipt.receipt_identity != expected:
            message = (
                "a transfer receipt's identity does not seal the record beside it; a relabelled, "
                "edited or stale receipt is refused rather than resealed"
            )
            raise ChunkTransferError(message)
        if json.loads(canonical_json_bytes(receipt.as_record())) != json.loads(
            canonical_json_bytes(stored)
        ):
            message = "a transfer receipt carries values its identity does not seal; refused"
            raise ChunkTransferError(message)
        return receipt


# --------------------------------------------------------------------------- #
# Instrumentation -- C22-R6
# --------------------------------------------------------------------------- #
def swap_used_bytes() -> int | None:
    """Swap in use, from a fixed read-only system query, or ``None`` when it cannot be read."""
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_SYSCTL, "-n", "vm.swapusage"], capture_output=True, check=False, timeout=15
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"used\s*=\s*([0-9.]+)([KMGT]?)", completed.stdout.decode("utf-8", "replace"))
    if match is None:
        return None
    scale = {"": 1, "K": 1 << 10, "M": 1 << 20, "G": 1 << 30, "T": 1 << 40}[match.group(2)]
    return int(float(match.group(1)) * scale)


def _within(ancestor: Path, descendant: Path) -> bool:
    left = Path(os.path.realpath(ancestor)).parts
    right = Path(os.path.realpath(descendant)).parts
    return len(right) >= len(left) and right[: len(left)] == left


class InstrumentationLedger:
    """An append-only JSONL ledger of process-local, stat-only observations -- C22-R6.

    Never opens a database. Free bytes come from ``statvfs``; a write-ahead log's high-water
    from ``stat`` of its path; the temporary high-water from the temporary volume's free-space
    drawdown against the baseline taken at construction, which is the only way an unlinked
    SQLite spill file can be observed at all; RSS from the process's own accounting; swap from
    one fixed read-only system query. The ledger path must lie outside the charged directory.
    """

    def __init__(
        self,
        path: Path,
        *,
        internal_path: Path,
        external_path: Path | None = None,
        temp_root: Path | None = None,
        charged_directory: Path | None = None,
        qualification_identity: str | None = None,
        tier_identity: str | None = None,
    ) -> None:
        if path.is_symlink():
            message = "an instrumentation ledger is never written through a symbolic link"
            raise ChunkTransferError(message)
        if charged_directory is not None and _within(charged_directory, path):
            message = (
                "an instrumentation ledger must live outside the active world directory it "
                "observes; a ledger inside the charged directory perturbs the measurement"
            )
            raise ChunkTransferError(message)
        self.path = path
        self.internal_path = internal_path
        self.external_path = external_path
        self.temp_root = temp_root
        self.qualification_identity = qualification_identity
        self.tier_identity = tier_identity
        self._lock = threading.Lock()
        self._started = time.monotonic()
        self.internal_low_water = measured_free_bytes(internal_path)
        self.external_low_water = (
            None if external_path is None else measured_free_bytes(external_path)
        )
        self._temp_baseline = None if temp_root is None else measured_free_bytes(temp_root)
        self.sqlite_temp_high_water = 0
        self.wal_high_water = 0
        self.bytes_copied = 0
        self.bytes_read_back = 0
        self.copy_bytes_per_second: int | None = None
        self.read_bytes_per_second: int | None = None
        self.retained_input_bytes: int | None = None
        self.output_bytes: int | None = None
        self.sorter_workfile_observations = 0
        self.process_exit_rss_reclaimed: int | None = None
        self._open_watches = 0
        self._samples = 0

    def observe_volumes(self, *, wal_path: Path | None = None) -> Mapping[str, int | None]:
        """One stat-only reading of free bytes, temporary drawdown and write-ahead-log size.

        The reading that moves a low- or high-water mark is the reading returned, so a sample
        records the same numbers its marks were derived from.
        """
        with self._lock:
            internal = measured_free_bytes(self.internal_path)
            self.internal_low_water = min(self.internal_low_water, internal)
            external: int | None = None
            if self.external_path is not None and self.external_low_water is not None:
                external = measured_free_bytes(self.external_path)
                self.external_low_water = min(self.external_low_water, external)
            if self.temp_root is not None and self._temp_baseline is not None:
                drawdown = self._temp_baseline - measured_free_bytes(self.temp_root)
                self.sqlite_temp_high_water = max(self.sqlite_temp_high_water, drawdown, 0)
                try:
                    visible = sum(
                        1
                        for entry in os.scandir(self.temp_root)
                        if entry.name.startswith("etilqs_")
                    )
                except OSError:
                    visible = 0
                self.sorter_workfile_observations = max(self.sorter_workfile_observations, visible)
            if wal_path is not None:
                try:
                    size = wal_path.stat().st_size if not wal_path.is_symlink() else 0
                except FileNotFoundError:
                    size = 0
                self.wal_high_water = max(self.wal_high_water, size)
            return {"internal_free_bytes": internal, "external_free_bytes": external}

    def sample(self, phase: str, **overrides: object) -> Mapping[str, object]:
        """Append one sample carrying every :data:`SAMPLE_FIELDS` field, and return it."""
        _require_text(phase, "phase")
        wal_path = overrides.pop("wal_path", None)
        if wal_path is not None and not isinstance(wal_path, Path):
            message = "a sample's wal_path must be a path"
            raise ChunkTransferError(message)
        unknown = set(overrides) - set(SAMPLE_FIELDS)
        if unknown:
            message = f"a sample carries fields outside the required set: {sorted(unknown)}"
            raise ChunkTransferError(message)
        readings = self.observe_volumes(wal_path=wal_path)
        with self._lock:
            record: dict[str, object] = {
                "phase": phase,
                "monotonic_s": round(time.monotonic() - self._started, 6),
                "utc": utc_now(),
                "pid": os.getpid(),
                "rss_bytes": process_peak_resident_bytes(),
                "swap_used_bytes": swap_used_bytes(),
                "internal_free_bytes": readings["internal_free_bytes"],
                "internal_low_water_bytes": self.internal_low_water,
                "external_free_bytes": readings["external_free_bytes"],
                "external_low_water_bytes": self.external_low_water,
                "bytes_copied": self.bytes_copied,
                "bytes_read_back": self.bytes_read_back,
                "copy_bytes_per_second": self.copy_bytes_per_second,
                "read_bytes_per_second": self.read_bytes_per_second,
                "sqlite_temp_high_water_bytes": self.sqlite_temp_high_water,
                "wal_high_water_bytes": self.wal_high_water,
                "retained_input_bytes": self.retained_input_bytes,
                "output_bytes": self.output_bytes,
                "sorter_workfile_observations": self.sorter_workfile_observations,
                "process_exit_rss_reclaimed_bytes": self.process_exit_rss_reclaimed,
                "qualification_identity": self.qualification_identity,
                "tier_reauthentication": self.tier_identity,
            }
            record.update(overrides)
            if set(record) != set(SAMPLE_FIELDS):
                message = "a sample must carry exactly the required fields"  # pragma: no cover
                raise ChunkTransferError(message)
            descriptor = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, _FILE_MODE)
            try:
                with os.fdopen(descriptor, "ab") as handle:
                    handle.write(canonical_json_bytes(record))
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                pass
            self._samples += 1
            return record

    def record_transfer(
        self, *, bytes_copied: int, copy_seconds: float, bytes_read_back: int, read_seconds: float
    ) -> None:
        """Self-report a transfer's counters."""
        with self._lock:
            self.bytes_copied += require_count(bytes_copied, "bytes_copied")
            self.bytes_read_back += require_count(bytes_read_back, "bytes_read_back")
            self.copy_bytes_per_second = (
                int(bytes_copied / copy_seconds) if copy_seconds > 0 else None
            )
            self.read_bytes_per_second = (
                int(bytes_read_back / read_seconds) if read_seconds > 0 else None
            )

    def record_sizes(self, *, retained_input_bytes: int | None, output_bytes: int | None) -> None:
        """Self-report retained input and produced output sizes."""
        with self._lock:
            self.retained_input_bytes = retained_input_bytes
            self.output_bytes = output_bytes

    def record_child_exit(
        self, *, parent_rss_before: int | None, parent_rss_after: int | None
    ) -> None:
        """Self-report memory reclaimed across a child process's exit."""
        with self._lock:
            if parent_rss_before is None or parent_rss_after is None:
                self.process_exit_rss_reclaimed = None
            else:
                self.process_exit_rss_reclaimed = parent_rss_before - parent_rss_after

    @contextmanager
    def watch(self, *, wal_path: Path | None, interval_seconds: float = 0.5) -> Iterator[None]:
        """Sample the write-ahead log and the volumes on a thread, stat-only, until exit."""
        if interval_seconds <= 0:
            message = "a watch interval must be positive"
            raise ChunkTransferError(message)
        stop = threading.Event()

        def loop() -> None:
            while not stop.wait(interval_seconds):
                self.observe_volumes(wal_path=wal_path)

        thread = threading.Thread(target=loop, name="c22-instrumentation-watch", daemon=True)
        self._open_watches += 1
        thread.start()
        try:
            yield
        finally:
            stop.set()
            thread.join()
            self.observe_volumes(wal_path=wal_path)
            self._open_watches -= 1

    def require_complete(self) -> int:
        """The number of samples written, or a refusal while a watch is still open."""
        if self._open_watches:
            message = "an instrumentation watch is still open; the ledger is not complete"
            raise ChunkTransferError(message)
        return self._samples


# --------------------------------------------------------------------------- #
# The transfer
# --------------------------------------------------------------------------- #
def _walk_files(directory: Path) -> list[str]:
    """Every regular file beneath ``directory`` as a relative POSIX path; links refuse."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(directory):
        here = Path(dirpath)
        for name in list(dirnames):
            if (here / name).is_symlink():
                message = f"{name!r} is a symbolic link; a manifested directory holds none"
                raise ChunkTransferError(message)
        for name in filenames:
            full = here / name
            if full.is_symlink():
                message = f"{name!r} is a symbolic link; a manifested directory holds none"
                raise ChunkTransferError(message)
            if not stat.S_ISREG(full.lstat().st_mode):
                message = f"{name!r} is not a regular file; refused"
                raise ChunkTransferError(message)
            found.append(full.relative_to(directory).as_posix())
    return sorted(found)


def _hash_file(path: Path, *, nocache: bool) -> tuple[str, int]:
    """Reopen ``path`` and read every byte in bounded blocks, hashing as it goes."""
    digest = hashlib.sha256()
    length = 0
    descriptor = os.open(path, os.O_RDONLY)
    if nocache and _F_NOCACHE is not None:
        with suppress(OSError):
            fcntl.fcntl(descriptor, _F_NOCACHE, 1)
    with os.fdopen(descriptor, "rb") as handle:
        for block in iter(lambda: handle.read(_COPY_BLOCK), b""):
            digest.update(block)
            length += len(block)
    return digest.hexdigest(), length


def require_terminal_source(source: TransferSource) -> TransferSource:
    """Refuse a source that is not exactly its manifest plus its terminal receipt, at rest.

    Every entry must exist as a regular file of the manifested length; the receipt must exist
    with the manifested digest; no write-ahead log, shared-memory file or hot journal may be
    present anywhere in the directory; and no object outside the manifest may be present.

    Raises:
        ChunkTransferError: the source is missing, mutable, incomplete or carries extras.
    """
    directory = source.directory
    if directory.is_symlink() or not directory.is_dir():
        message = f"transfer source {directory.name!r} is not a directory; refused"
        raise ChunkTransferError(message)
    present = _walk_files(directory)
    for name in present:
        if name.endswith(_UNCLOSED_DATABASE_SUFFIXES):
            message = (
                f"transfer source {directory.name!r} holds {name!r}: a database in the set is not "
                "closed, so the source is not immutable and is refused"
            )
            raise ChunkTransferError(message)
    expected = sorted([entry.relative_path for entry in source.entries] + [SOURCE_RECEIPT_FILENAME])
    if present != expected:
        message = (
            f"transfer source {directory.name!r} is not exactly its manifest plus its terminal "
            f"receipt: missing {sorted(set(expected) - set(present))}, unexpected "
            f"{sorted(set(present) - set(expected))}"
        )
        raise ChunkTransferError(message)
    for entry in source.entries:
        if os.lstat(directory / entry.relative_path).st_size != entry.byte_length:
            message = f"source object {entry.relative_path!r} is not its manifested length"
            raise ChunkTransferError(message)
    digest, length = _hash_file(directory / SOURCE_RECEIPT_FILENAME, nocache=False)
    if digest != source.receipt_sha256 or length != source.receipt_bytes:
        message = "the source's terminal receipt is not the receipt the source was built from"
        raise ChunkTransferError(message)
    return source


def _require_on_observed_volume(path: Path, observation: LiveTierObservation) -> None:
    device = observation.attachment.get("st_dev")
    if not isinstance(device, int) or _nearest_existing(path).stat().st_dev != device:
        message = (
            "the destination is not on the volume that was just reauthenticated; a copy onto "
            "another volume, or onto a directory left at a mount point after the volume went "
            "away, is refused"
        )
        raise ChunkTransferError(message)


def _copy_one(source_path: Path, target_path: Path, entry: ManifestEntry) -> Mapping[str, object]:
    digest = hashlib.sha256()
    written = 0
    started = time.monotonic()
    descriptor = os.open(target_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, _FILE_MODE)
    with source_path.open("rb") as reader, os.fdopen(descriptor, "wb") as writer:
        for block in iter(lambda: reader.read(_COPY_BLOCK), b""):
            digest.update(block)
            writer.write(block)
            written += len(block)
        writer.flush()
        os.fsync(writer.fileno())
        full = _fullfsync(writer.fileno())
    if digest.hexdigest() != entry.sha256 or written != entry.byte_length:
        message = (
            f"object {entry.relative_path!r} changed while it was being copied: read "
            f"{written} bytes / {digest.hexdigest()} against the manifest's "
            f"{entry.byte_length} / {entry.sha256}. The transfer is refused; the source is "
            "untouched and remains the only authoritative copy"
        )
        raise ChunkTransferError(message)
    return {"seconds": time.monotonic() - started, "fullfsync": full}


def _read_back(
    directory: Path,
    entries: Sequence[ManifestEntry],
    *,
    receipt_sha256: str,
    exclude: tuple[str, ...] = (),
) -> float:
    """Independently reopen and fully re-read every object; the set must be exact.

    ``exclude`` names the one object a verified destination legitimately holds beyond the
    manifested set and the terminal receipt: its own transfer receipt, once written.
    """
    started = time.monotonic()
    present = [name for name in _walk_files(directory) if name not in exclude]
    expected = sorted([entry.relative_path for entry in entries] + [SOURCE_RECEIPT_FILENAME])
    if present != expected:
        message = (
            f"the destination does not hold exactly the manifested set: missing "
            f"{sorted(set(expected) - set(present))}, unexpected "
            f"{sorted(set(present) - set(expected))}; no receipt is written"
        )
        raise ChunkTransferError(message)
    for entry in entries:
        digest, length = _hash_file(directory / entry.relative_path, nocache=True)
        if digest != entry.sha256 or length != entry.byte_length:
            message = (
                f"destination object {entry.relative_path!r} read back as {length} bytes / "
                f"{digest} against the manifest's {entry.byte_length} / {entry.sha256}; the copy "
                "is not verified and no receipt is written"
            )
            raise ChunkTransferError(message)
    digest, _length = _hash_file(directory / SOURCE_RECEIPT_FILENAME, nocache=True)
    if digest != receipt_sha256:
        message = "the copied terminal receipt does not read back as the source's receipt"
        raise ChunkTransferError(message)
    return time.monotonic() - started


def _final_path(destination_root: Path, chunk_id: str) -> Path:
    return destination_root / chunk_id


def _partial_path(destination_root: Path, chunk_id: str) -> Path:
    return destination_root / f"{chunk_id}{PARTIAL_SUFFIX}"


def _reclaim_directory(destination_root: Path, chunk_id: str) -> Path:
    return destination_root / f"{chunk_id}{RECLAIM_DIRECTORY_SUFFIX}"


def _require_tier(
    qualification: HostASsdQualification, observation: LiveTierObservation, destination_root: Path
) -> None:
    require_copy_capable(qualification)
    require_tier_reauthentication(qualification, observation)
    if destination_root.is_symlink() or not destination_root.is_dir():
        message = "the destination root is not a directory; refused"
        raise ChunkTransferError(message)
    _require_on_observed_volume(destination_root, observation)


def verified_transfer(  # noqa: PLR0915
    *,
    source: TransferSource,
    destination_root: Path,
    qualification: HostASsdQualification,
    observation: LiveTierObservation,
    authorization: object,
    external_reserve_bytes: int,
    telemetry: InstrumentationLedger | None = None,
    recovered_from_state: str | None = None,
) -> VerifiedTransferReceipt:
    """Transfer one terminal source onto the qualified tier and prove it arrived -- C22-R3.

    The sequence is fixed and every step is a refusal point; nothing later in it can be reached
    by skipping something earlier. The receipt is written LAST, inside the final destination,
    after the independent read-back and the final-path reauthentication.

    Raises:
        ChunkTransferError: any step refuses. The source is untouched throughout.
        HostASsdQualificationError: the tier does not admit a copy or is not the qualified one.
    """
    if not isinstance(authorization, TransferAuthorization):
        message = "a transfer runs only under a transfer authorization; none was supplied"
        raise ChunkTransferError(message)
    _require_tier(qualification, observation, destination_root)
    require_terminal_source(source)
    final = _final_path(destination_root, source.chunk_id)
    partial = _partial_path(destination_root, source.chunk_id)
    if os.path.lexists(final):
        message = (
            f"a final destination {final.name!r} already exists; a verified copy is create-once "
            "and an existing destination is never overwritten, resumed or repaired here"
        )
        raise ChunkTransferError(message)
    if os.path.lexists(partial):
        message = (
            f"a partial destination {partial.name!r} already exists; it is removed only by an "
            "explicit recovery that proves it is exactly this transfer's own partial"
        )
        raise ChunkTransferError(message)
    admission = require_external_admission(
        free_bytes=measured_free_bytes(destination_root),
        source_bytes=source.total_bytes + source.receipt_bytes,
        partial_copy_overhead_bytes=allocation_overhead_bytes(source.entries, destination_root),
        evidence_overhead_bytes=EVIDENCE_OVERHEAD_BYTES,
        reserve_bytes=require_count(external_reserve_bytes, "external_reserve_bytes"),
    )
    started_at = utc_now()
    if telemetry is not None:
        telemetry.record_sizes(retained_input_bytes=source.total_bytes, output_bytes=None)
        telemetry.sample("transfer_admitted")
    partial.mkdir(mode=_DIRECTORY_MODE)
    copy_seconds = 0.0
    fullfsync_outcomes: set[str] = set()
    for entry in source.entries:
        target = partial / entry.relative_path
        target.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
        result = _copy_one(source.directory / entry.relative_path, target, entry)
        copy_seconds += float(result["seconds"])  # type: ignore[arg-type]
        fullfsync_outcomes.add(str(result["fullfsync"]))
    receipt_entry = ManifestEntry(
        relative_path=SOURCE_RECEIPT_FILENAME,
        byte_length=source.receipt_bytes,
        sha256=source.receipt_sha256,
    )
    _copy_one(
        source.directory / SOURCE_RECEIPT_FILENAME, partial / SOURCE_RECEIPT_FILENAME, receipt_entry
    )
    parent_fsync, parent_full = _fsync_directory(partial)
    if telemetry is not None:
        telemetry.sample("transfer_copied")
    read_seconds = _read_back(partial, source.entries, receipt_sha256=source.receipt_sha256)
    if telemetry is not None:
        telemetry.record_transfer(
            bytes_copied=source.total_bytes + source.receipt_bytes,
            copy_seconds=copy_seconds,
            bytes_read_back=source.total_bytes + source.receipt_bytes,
            read_seconds=read_seconds,
        )
        telemetry.sample("transfer_read_back")
    partial.rename(final)
    _fsync_directory(destination_root)
    # Final destination reauthentication: the volume, the set and every length, after the rename.
    _require_on_observed_volume(final, observation)
    present = _walk_files(final)
    expected = sorted([entry.relative_path for entry in source.entries] + [SOURCE_RECEIPT_FILENAME])
    if present != expected:
        message = "the final destination does not hold the manifested set after finalization"
        raise ChunkTransferError(message)
    for entry in source.entries:
        if os.lstat(final / entry.relative_path).st_size != entry.byte_length:
            message = f"final object {entry.relative_path!r} is not its manifested length"
            raise ChunkTransferError(message)
    receipt = VerifiedTransferReceipt.seal(
        contract=VERIFIED_TRANSFER_RECEIPT_CONTRACT,
        chunk_id=source.chunk_id,
        plan_digest=source.plan_digest,
        source_manifest_digest=source.manifest_digest,
        source_receipt_sha256=source.receipt_sha256,
        source_bytes=source.total_bytes,
        source_repository_head_sha=source.repository_head_sha,
        source_repository_tree_sha=source.repository_tree_sha,
        destination_volume_uuid=observation.stable.volume_uuid,
        destination_canonical_path=source.chunk_id,
        destination_bytes=source.total_bytes,
        destination_entries=tuple(source.entries),
        destination_manifest_verified=True,
        destination_content_verified=True,
        qualification_identity=qualification.qualification_identity,
        stable_tier_compatibility_identity=qualification.stable_tier_compatibility_identity,
        qualification_class=qualification.qualification_class,
        transfer_started_at_utc=started_at,
        transfer_completed_at_utc=utc_now(),
        transfer_outcome=TRANSFER_OUTCOME_VERIFIED,
        durability={
            "file_fsync": "succeeded",
            "file_fullfsync": ",".join(sorted(fullfsync_outcomes)),
            "parent_directory_fsync": parent_fsync,
            "parent_directory_fullfsync": parent_full,
            "admission": json.dumps(dict(admission.as_record()), sort_keys=True),
        },
        recovered_from_state=recovered_from_state,
    )
    # LAST. An interrupted transfer therefore leaves a partial or an unreceipted final directory
    # and no receipt, which every reader below derives as exactly that.
    _write_once(final / TRANSFER_RECEIPT_FILENAME, canonical_json_bytes(receipt.as_record()))
    if telemetry is not None:
        telemetry.record_sizes(
            retained_input_bytes=source.total_bytes, output_bytes=source.total_bytes
        )
        telemetry.sample("transfer_receipt_durable")
    return receipt


# --------------------------------------------------------------------------- #
# Reclaim records -- C22-R4
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ReclaimRecord:
    """One reclaim record: an intent before the first deletion, or a completion after the last."""

    contract: str
    record_kind: str
    chunk_id: str
    receipt_identity: str
    qualification_identity: str
    source_manifest_digest: str
    entries: tuple[str, ...]
    source_bytes: int
    issued_at_utc: str
    completed_at_utc: str | None
    deleted_entries: int | None
    free_before_bytes: int | None
    free_after_bytes: int | None
    freed_bytes: int | None
    expected_freed_bytes: int | None
    reconciled: bool | None
    record_identity: str

    def as_record(self) -> Mapping[str, object]:
        """The complete record as a plain mapping, identity included."""
        return {
            "contract": self.contract,
            "record_kind": self.record_kind,
            "chunk_id": self.chunk_id,
            "receipt_identity": self.receipt_identity,
            "qualification_identity": self.qualification_identity,
            "source_manifest_digest": self.source_manifest_digest,
            "entries": list(self.entries),
            "source_bytes": self.source_bytes,
            "issued_at_utc": self.issued_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "deleted_entries": self.deleted_entries,
            "free_before_bytes": self.free_before_bytes,
            "free_after_bytes": self.free_after_bytes,
            "freed_bytes": self.freed_bytes,
            "expected_freed_bytes": self.expected_freed_bytes,
            "reconciled": self.reconciled,
            RECLAIM_RECORD_IDENTITY_KEY: self.record_identity,
        }

    @classmethod
    def seal(cls, **fields: object) -> ReclaimRecord:
        """Construct and seal a record over its own body."""
        unsealed = cls(**fields, record_identity="0" * 64)  # type: ignore[arg-type]
        identity = sealed_identity(unsealed.as_record(), identity_key=RECLAIM_RECORD_IDENTITY_KEY)
        return cls(**fields, record_identity=identity)  # type: ignore[arg-type]

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> ReclaimRecord:
        """Read one reclaim record exactly, or refuse.

        Raises:
            ChunkTransferError: any field missing, extra, of the wrong type or kind, a completion
                without its measurements, an intent carrying them, or a stale identity.
        """
        stored = _require_mapping(document, "reclaim record")
        present = set(stored)
        if present != RECLAIM_RECORD_FIELDS:
            message = (
                "a reclaim record is exact; this one is missing "
                f"{sorted(RECLAIM_RECORD_FIELDS - present)} and carries unexpected "
                f"{sorted(present - RECLAIM_RECORD_FIELDS)}"
            )
            raise ChunkTransferError(message)
        if stored["contract"] != RECLAIM_RECORD_CONTRACT:
            message = f"a reclaim record carries contract {stored['contract']!r}; refused"
            raise ChunkTransferError(message)
        kind = stored["record_kind"]
        if kind not in RECLAIM_RECORD_KINDS:
            message = f"a reclaim record names kind {kind!r}; refused rather than mapped"
            raise ChunkTransferError(message)
        raw_entries = stored["entries"]
        if not isinstance(raw_entries, Sequence) or isinstance(raw_entries, str | bytes):
            message = "a reclaim record's entries must be a list"
            raise ChunkTransferError(message)
        entries = tuple(_require_text(item, "entry") for item in raw_entries)
        if list(entries) != sorted(set(entries)) or not entries:
            message = "a reclaim record's entries must be unique, sorted and non-empty"
            raise ChunkTransferError(message)
        measurements = (
            "completed_at_utc",
            "deleted_entries",
            "free_before_bytes",
            "free_after_bytes",
            "freed_bytes",
            "expected_freed_bytes",
            "reconciled",
        )
        if kind == RECLAIM_INTENT:
            if any(stored[name] is not None for name in measurements):
                message = "a reclaim intent carries completion measurements; refused"
                raise ChunkTransferError(message)
            record = cls(
                contract=RECLAIM_RECORD_CONTRACT,
                record_kind=kind,
                chunk_id=_require_text(stored["chunk_id"], "chunk_id"),
                receipt_identity=_require_hex64(stored["receipt_identity"], "receipt_identity"),
                qualification_identity=_require_hex64(
                    stored["qualification_identity"], "qualification_identity"
                ),
                source_manifest_digest=_require_hex64(
                    stored["source_manifest_digest"], "source_manifest_digest"
                ),
                entries=entries,
                source_bytes=require_count(stored["source_bytes"], "source_bytes"),
                issued_at_utc=_require_text(stored["issued_at_utc"], "issued_at_utc"),
                completed_at_utc=None,
                deleted_entries=None,
                free_before_bytes=None,
                free_after_bytes=None,
                freed_bytes=None,
                expected_freed_bytes=None,
                reconciled=None,
                record_identity=_require_hex64(
                    stored[RECLAIM_RECORD_IDENTITY_KEY], RECLAIM_RECORD_IDENTITY_KEY
                ),
            )
        else:
            record = cls(
                contract=RECLAIM_RECORD_CONTRACT,
                record_kind=kind,
                chunk_id=_require_text(stored["chunk_id"], "chunk_id"),
                receipt_identity=_require_hex64(stored["receipt_identity"], "receipt_identity"),
                qualification_identity=_require_hex64(
                    stored["qualification_identity"], "qualification_identity"
                ),
                source_manifest_digest=_require_hex64(
                    stored["source_manifest_digest"], "source_manifest_digest"
                ),
                entries=entries,
                source_bytes=require_count(stored["source_bytes"], "source_bytes"),
                issued_at_utc=_require_text(stored["issued_at_utc"], "issued_at_utc"),
                completed_at_utc=_require_text(stored["completed_at_utc"], "completed_at_utc"),
                deleted_entries=require_count(stored["deleted_entries"], "deleted_entries"),
                free_before_bytes=require_count(stored["free_before_bytes"], "free_before_bytes"),
                free_after_bytes=require_count(stored["free_after_bytes"], "free_after_bytes"),
                freed_bytes=_require_signed(stored["freed_bytes"], "freed_bytes"),
                expected_freed_bytes=require_count(
                    stored["expected_freed_bytes"], "expected_freed_bytes"
                ),
                reconciled=_require_bool(stored["reconciled"], "reconciled"),
                record_identity=_require_hex64(
                    stored[RECLAIM_RECORD_IDENTITY_KEY], RECLAIM_RECORD_IDENTITY_KEY
                ),
            )
            if record.deleted_entries != len(entries):
                message = "a reclaim completion does not account for every intended entry; refused"
                raise ChunkTransferError(message)
        expected = sealed_identity(record.as_record(), identity_key=RECLAIM_RECORD_IDENTITY_KEY)
        if record.record_identity != expected:
            message = "a reclaim record's identity does not seal the record beside it; refused"
            raise ChunkTransferError(message)
        return record


def _require_signed(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{name} must be an integer; got {value!r}"
        raise ChunkTransferError(message)
    return value


def _read_reclaim_record(path: Path, *, kind: str) -> ReclaimRecord | None:
    if not os.path.lexists(path):
        return None
    record = ReclaimRecord.from_document(
        _read_document(path, contract=RECLAIM_RECORD_CONTRACT, label="reclaim record")
    )
    if record.record_kind != kind:
        message = (
            f"{path.name!r} is a {record.record_kind} record, not the expected {kind}; refused"
        )
        raise ChunkTransferError(message)
    return record


def _read_receipt(final: Path) -> VerifiedTransferReceipt | None:
    path = final / TRANSFER_RECEIPT_FILENAME
    if not os.path.lexists(path):
        return None
    return VerifiedTransferReceipt.from_document(
        _read_document(path, contract=VERIFIED_TRANSFER_RECEIPT_CONTRACT, label="transfer receipt")
    )


@dataclass(frozen=True, slots=True)
class TransferStateReport:
    """Where one transfer stands, derived from what is on disk -- C22-R7."""

    chunk_id: str
    state: str
    receipt: VerifiedTransferReceipt | None
    intent: ReclaimRecord | None
    completion: ReclaimRecord | None
    source_entries_present: int | None
    detail: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "chunk_id": self.chunk_id,
            "state": self.state,
            "receipt_identity": None if self.receipt is None else self.receipt.receipt_identity,
            "intent_identity": None if self.intent is None else self.intent.record_identity,
            "completion_identity": (
                None if self.completion is None else self.completion.record_identity
            ),
            "source_entries_present": self.source_entries_present,
            "detail": self.detail,
        }


def derive_transfer_state(
    *, destination_root: Path, chunk_id: str, source_directory: Path | None
) -> TransferStateReport:
    """The one state the destination and the reclaim records imply -- C22-R7.

    Raises:
        ChunkTransferError: the records conflict -- a reclaim record without a verified
            receipt, a completion with the source still present, a partial beside a final, or a
            record of another contract or shape.
    """
    final = _final_path(destination_root, chunk_id)
    partial = _partial_path(destination_root, chunk_id)
    reclaim = _reclaim_directory(destination_root, chunk_id)
    intent = _read_reclaim_record(reclaim / RECLAIM_INTENT_FILENAME, kind=RECLAIM_INTENT)
    completion = _read_reclaim_record(reclaim / RECLAIM_COMPLETE_FILENAME, kind=RECLAIM_COMPLETE)
    receipt = _read_receipt(final) if final.is_dir() and not final.is_symlink() else None
    source_present = (
        None
        if source_directory is None or not source_directory.is_dir()
        else len(_walk_files(source_directory))
    )
    if (intent is not None or completion is not None) and receipt is None:
        message = (
            f"chunk {chunk_id!r} carries a reclaim record without a verified transfer receipt; "
            "conflicting evidence is refused rather than resolved"
        )
        raise ChunkTransferError(message)
    if os.path.lexists(partial) and os.path.lexists(final):
        message = f"chunk {chunk_id!r} has both a partial and a final destination; refused"
        raise ChunkTransferError(message)
    if receipt is not None:
        if receipt.chunk_id != chunk_id:
            message = f"the receipt at {final.name!r} describes chunk {receipt.chunk_id!r}; refused"
            raise ChunkTransferError(message)
        if completion is not None:
            if intent is None or completion.receipt_identity != receipt.receipt_identity:
                message = "a reclaim completion without its intent or for another receipt; refused"
                raise ChunkTransferError(message)
            if source_present:
                message = (
                    f"chunk {chunk_id!r} records a completed reclaim while {source_present} "
                    "source objects are still present; refused rather than trusted"
                )
                raise ChunkTransferError(message)
            return TransferStateReport(
                chunk_id,
                STATE_RECLAIM_COMPLETE,
                receipt,
                intent,
                completion,
                source_present,
                "reclaim complete; source absent",
            )
        if intent is not None:
            if intent.receipt_identity != receipt.receipt_identity:
                message = "a reclaim intent for another receipt; refused"
                raise ChunkTransferError(message)
            if source_present is not None and source_present == len(intent.entries):
                return TransferStateReport(
                    chunk_id,
                    STATE_RECLAIM_INTENT_DURABLE,
                    receipt,
                    intent,
                    None,
                    source_present,
                    "durable intent; nothing deleted yet",
                )
            return TransferStateReport(
                chunk_id,
                STATE_RECLAIM_IN_PROGRESS,
                receipt,
                intent,
                None,
                source_present,
                "durable intent; deletion begun and not recorded complete",
            )
        return TransferStateReport(
            chunk_id,
            STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE,
            receipt,
            None,
            None,
            source_present,
            "verified copy with a durable receipt; the source is retained",
        )
    if final.is_dir() and not final.is_symlink():
        return TransferStateReport(
            chunk_id,
            STATE_FINAL_UNVERIFIED,
            None,
            None,
            None,
            source_present,
            "a final destination exists and carries no receipt; it is not a verified copy",
        )
    if os.path.lexists(partial):
        return TransferStateReport(
            chunk_id,
            STATE_PARTIAL_COPY,
            None,
            None,
            None,
            source_present,
            "a partial destination exists; the source remains authoritative",
        )
    return TransferStateReport(
        chunk_id, STATE_NOT_STARTED, None, None, None, source_present, "no destination exists"
    )


def _remove_exact_entries(base: Path, files: Sequence[str]) -> int:
    """Delete exactly ``files`` (relative, sorted) beneath ``base``, then the emptied
    directories deepest-first, then ``base``. Never a recursive tree removal: anything that is
    not listed refuses before the first deletion."""
    present = _walk_files(base)
    unexpected = sorted(set(present) - set(files))
    if unexpected:
        message = (
            f"{base.name!r} holds objects outside the exact entry list: {unexpected}; nothing "
            "is deleted"
        )
        raise ChunkTransferError(message)
    deleted = 0
    for relative in sorted(files):
        target = base / relative
        if os.path.lexists(target):
            target.unlink()
            deleted += 1
    directories = sorted(
        {Path(relative).parent for relative in files if "/" in relative},
        key=lambda item: len(item.parts),
        reverse=True,
    )
    for directory in directories:
        if (base / directory).is_dir():
            (base / directory).rmdir()
    base.rmdir()
    return deleted


def recover_transfer(
    *,
    source: TransferSource,
    destination_root: Path,
    qualification: HostASsdQualification,
    observation: LiveTierObservation,
    authorization: object,
    external_reserve_bytes: int,
    telemetry: InstrumentationLedger | None = None,
) -> VerifiedTransferReceipt:
    """Bring one transfer to a verified receipt from whatever state it was left in -- C22-R7.

    * ``not_started``: a verified transfer.
    * ``partial_copy``: the partial is proved to hold only objects of this source's manifest,
      removed exactly, and the transfer is redone.
    * ``final_unverified``: the final destination is independently reverified against the
      source manifest and the tier; a receipt is written only if every identity matches.
    * ``transfer_verified_receipt_durable``: the receipt is held to the source and the tier
      and returned; a disagreeing receipt refuses, and no duplicate is ever written.
    * any reclaim state: refused -- recovery of a reclaim is :func:`reclaim_source`.

    Raises:
        ChunkTransferError: any refusal.
    """
    if not isinstance(authorization, TransferAuthorization):
        message = "a transfer recovery runs only under a transfer authorization"
        raise ChunkTransferError(message)
    _require_tier(qualification, observation, destination_root)
    report = derive_transfer_state(
        destination_root=destination_root,
        chunk_id=source.chunk_id,
        source_directory=source.directory,
    )
    if report.state == STATE_NOT_STARTED:
        return verified_transfer(
            source=source,
            destination_root=destination_root,
            qualification=qualification,
            observation=observation,
            authorization=authorization,
            external_reserve_bytes=external_reserve_bytes,
            telemetry=telemetry,
        )
    if report.state == STATE_PARTIAL_COPY:
        partial = _partial_path(destination_root, source.chunk_id)
        allowed = [entry.relative_path for entry in source.entries] + [SOURCE_RECEIPT_FILENAME]
        _remove_exact_entries(partial, sorted(allowed))
        _fsync_directory(destination_root)
        return verified_transfer(
            source=source,
            destination_root=destination_root,
            qualification=qualification,
            observation=observation,
            authorization=authorization,
            external_reserve_bytes=external_reserve_bytes,
            telemetry=telemetry,
            recovered_from_state=STATE_PARTIAL_COPY,
        )
    if report.state == STATE_FINAL_UNVERIFIED:
        final = _final_path(destination_root, source.chunk_id)
        require_terminal_source(source)
        _require_on_observed_volume(final, observation)
        _read_back(final, source.entries, receipt_sha256=source.receipt_sha256)
        now = utc_now()
        receipt = VerifiedTransferReceipt.seal(
            contract=VERIFIED_TRANSFER_RECEIPT_CONTRACT,
            chunk_id=source.chunk_id,
            plan_digest=source.plan_digest,
            source_manifest_digest=source.manifest_digest,
            source_receipt_sha256=source.receipt_sha256,
            source_bytes=source.total_bytes,
            source_repository_head_sha=source.repository_head_sha,
            source_repository_tree_sha=source.repository_tree_sha,
            destination_volume_uuid=observation.stable.volume_uuid,
            destination_canonical_path=source.chunk_id,
            destination_bytes=source.total_bytes,
            destination_entries=tuple(source.entries),
            destination_manifest_verified=True,
            destination_content_verified=True,
            qualification_identity=qualification.qualification_identity,
            stable_tier_compatibility_identity=qualification.stable_tier_compatibility_identity,
            qualification_class=qualification.qualification_class,
            transfer_started_at_utc=now,
            transfer_completed_at_utc=now,
            transfer_outcome=TRANSFER_OUTCOME_VERIFIED,
            durability={
                "file_fsync": "unknown",
                "file_fullfsync": "unknown",
                "parent_directory_fsync": "unknown",
                "parent_directory_fullfsync": "unknown",
                "admission": "recovered",
            },
            recovered_from_state=STATE_FINAL_UNVERIFIED,
        )
        _write_once(final / TRANSFER_RECEIPT_FILENAME, canonical_json_bytes(receipt.as_record()))
        if telemetry is not None:
            telemetry.sample("transfer_receipt_durable")
        return receipt
    if report.state == STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE and report.receipt is not None:
        receipt = report.receipt
        disagreements = [
            name
            for name, left, right in (
                ("chunk_id", receipt.chunk_id, source.chunk_id),
                ("plan_digest", receipt.plan_digest, source.plan_digest),
                ("source_manifest_digest", receipt.source_manifest_digest, source.manifest_digest),
                ("source_receipt_sha256", receipt.source_receipt_sha256, source.receipt_sha256),
                (
                    "qualification_identity",
                    receipt.qualification_identity,
                    qualification.qualification_identity,
                ),
                (
                    "destination_volume_uuid",
                    receipt.destination_volume_uuid,
                    observation.stable.volume_uuid,
                ),
            )
            if left != right
        ]
        if disagreements:
            message = (
                f"the existing receipt for chunk {source.chunk_id!r} disagrees with this source "
                f"and tier on {disagreements}; a conflicting receipt is refused, never replaced"
            )
            raise ChunkTransferError(message)
        return receipt
    message = (
        f"chunk {source.chunk_id!r} is in state {report.state!r}; transfer recovery does not "
        "resume a reclaim"
    )
    raise ChunkTransferError(message)


# --------------------------------------------------------------------------- #
# Reclaim -- C22-R4
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ReclaimEligibilityReport:
    """Whether one internal copy may be reclaimed. A computation; never an action."""

    chunk_id: str
    eligible: bool
    proofs: Mapping[str, bool]
    detail: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "chunk_id": self.chunk_id,
            "eligible": self.eligible,
            "proofs": dict(sorted(self.proofs.items())),
            "detail": self.detail,
        }


def reclaim_eligibility(
    *,
    source: TransferSource,
    destination_root: Path,
    qualification: HostASsdQualification,
    observation: LiveTierObservation,
) -> ReclaimEligibilityReport:
    """The pure derived predicate C22-R4 names. Every proof is re-established now.

    A valid receipt agreeing with the source; the current tier reauthenticated; the destination
    fully re-read; the exact source manifest; the immutable terminal source; and a
    RECLAIM_CAPABLE qualification. Eligible is not reclaimed.
    """
    proofs: dict[str, bool] = {}
    final = _final_path(destination_root, source.chunk_id)
    try:
        receipt = _read_receipt(final)
    except ChunkTransferError:
        receipt = None
    proofs["transfer_receipt_valid"] = receipt is not None and (
        receipt.chunk_id == source.chunk_id
        and receipt.plan_digest == source.plan_digest
        and receipt.source_manifest_digest == source.manifest_digest
        and receipt.source_receipt_sha256 == source.receipt_sha256
        and receipt.qualification_identity == qualification.qualification_identity
    )
    try:
        require_tier_reauthentication(qualification, observation)
        _require_on_observed_volume(destination_root, observation)
        proofs["tier_reauthenticated_now"] = True
    except (HostASsdQualificationError, ChunkTransferError):
        proofs["tier_reauthenticated_now"] = False
    try:
        _read_back(
            final,
            source.entries,
            receipt_sha256=source.receipt_sha256,
            exclude=(TRANSFER_RECEIPT_FILENAME,),
        )
        proofs["destination_fully_reread"] = True
    except ChunkTransferError:
        proofs["destination_fully_reread"] = False
    try:
        require_terminal_source(source)
        proofs["source_manifest_exact"] = True
        proofs["source_immutable_terminal"] = True
    except ChunkTransferError:
        proofs["source_manifest_exact"] = False
        proofs["source_immutable_terminal"] = False
    if proofs["source_manifest_exact"]:
        proofs["source_manifest_exact"] = all(
            _hash_file(source.directory / entry.relative_path, nocache=False)
            == (entry.sha256, entry.byte_length)
            for entry in source.entries
        )
    proofs["qualification_reclaim_capable"] = qualification.admits_reclaim
    eligible = all(proofs.values())
    return ReclaimEligibilityReport(
        chunk_id=source.chunk_id,
        eligible=eligible,
        proofs=proofs,
        detail=(
            "RECLAIM-ELIGIBLE and NOT reclaimed: deletion needs a reclaim authorization and a "
            "durable intent, in that order"
            if eligible
            else "not eligible: at least one proof is absent"
        ),
    )


def _intent_entries(source: TransferSource) -> tuple[str, ...]:
    return tuple(
        sorted([entry.relative_path for entry in source.entries] + [SOURCE_RECEIPT_FILENAME])
    )


def write_reclaim_intent(
    *,
    source: TransferSource,
    destination_root: Path,
    qualification: HostASsdQualification,
    observation: LiveTierObservation,
) -> ReclaimRecord:
    """Record, durably and create-once, exactly what a reclaim would delete -- before any deletion.

    Raises:
        ChunkTransferError: the copy is not eligible, or an intent already exists.
    """
    require_reclaim_capable(qualification)
    eligibility = reclaim_eligibility(
        source=source,
        destination_root=destination_root,
        qualification=qualification,
        observation=observation,
    )
    if not eligibility.eligible:
        message = (
            f"no reclaim intent for chunk {source.chunk_id!r}: the copy is not eligible "
            f"({dict(sorted(eligibility.proofs.items()))}); nothing is deleted"
        )
        raise ChunkTransferError(message)
    receipt = _read_receipt(_final_path(destination_root, source.chunk_id))
    if receipt is None:  # pragma: no cover - eligibility already proved the receipt
        message = "no receipt"
        raise ChunkTransferError(message)
    reclaim = _reclaim_directory(destination_root, source.chunk_id)
    reclaim.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    record = ReclaimRecord.seal(
        contract=RECLAIM_RECORD_CONTRACT,
        record_kind=RECLAIM_INTENT,
        chunk_id=source.chunk_id,
        receipt_identity=receipt.receipt_identity,
        qualification_identity=qualification.qualification_identity,
        source_manifest_digest=source.manifest_digest,
        entries=_intent_entries(source),
        source_bytes=source.total_bytes + source.receipt_bytes,
        issued_at_utc=utc_now(),
        completed_at_utc=None,
        deleted_entries=None,
        free_before_bytes=None,
        free_after_bytes=None,
        freed_bytes=None,
        expected_freed_bytes=None,
        reconciled=None,
    )
    _write_once(reclaim / RECLAIM_INTENT_FILENAME, canonical_json_bytes(record.as_record()))
    return record


def reclaim_source(
    *,
    authorization: object,
    source: TransferSource,
    destination_root: Path,
    qualification: HostASsdQualification,
    observation: LiveTierObservation,
    telemetry: InstrumentationLedger | None = None,
) -> ReclaimRecord:
    """Delete the internal copy exactly, under authorization, after a durable intent -- C22-R4.

    The first effective gate is the reclaim authorization; the family module obtains it from its
    closed constant, so while that constant is ``None`` no production caller ever reaches the
    second statement. Then: the destination is re-read and every eligibility proof is
    re-established; a durable intent for exactly this receipt must already exist; the source is
    proved to hold nothing outside the intent; and the intent's entries -- or the exact
    remaining subset of them, on a resumption -- are deleted in deterministic order. The
    completion record is written only after the source is absent and free space was measured.

    Raises:
        ChunkTransferError: any refusal. Nothing is deleted on a refusal before the first
            deletion; a refusal after it leaves the exact remaining subset for a resumption.
    """
    if not isinstance(authorization, ReclaimAuthorization):
        message = (
            "a reclaim deletes only under a reclaim authorization; none was supplied. A transfer "
            "receipt, an intent, eligibility and a transfer authorization are each necessary "
            "and none of them is this"
        )
        raise ChunkTransferError(message)
    require_reclaim_capable(qualification)
    reclaim = _reclaim_directory(destination_root, source.chunk_id)
    intent = _read_reclaim_record(reclaim / RECLAIM_INTENT_FILENAME, kind=RECLAIM_INTENT)
    if intent is None:
        message = (
            f"no durable reclaim intent exists for chunk {source.chunk_id!r}; the first deletion "
            "never precedes the intent, and nothing was deleted"
        )
        raise ChunkTransferError(message)
    if _read_reclaim_record(reclaim / RECLAIM_COMPLETE_FILENAME, kind=RECLAIM_COMPLETE) is not None:
        message = f"chunk {source.chunk_id!r} already records a completed reclaim; refused"
        raise ChunkTransferError(message)
    receipt = _read_receipt(_final_path(destination_root, source.chunk_id))
    if receipt is None or intent.receipt_identity != receipt.receipt_identity:
        message = "the reclaim intent does not name the verified receipt beside it; refused"
        raise ChunkTransferError(message)
    if (
        intent.chunk_id != source.chunk_id
        or intent.source_manifest_digest != source.manifest_digest
        or intent.qualification_identity != qualification.qualification_identity
        or intent.entries != _intent_entries(source)
    ):
        message = "the reclaim intent does not describe this source under this qualification"
        raise ChunkTransferError(message)
    # Destination revalidation immediately before deletion, and the tier again.
    require_tier_reauthentication(qualification, observation)
    _require_on_observed_volume(destination_root, observation)
    _read_back(
        _final_path(destination_root, source.chunk_id),
        source.entries,
        receipt_sha256=source.receipt_sha256,
        exclude=(TRANSFER_RECEIPT_FILENAME,),
    )
    directory = source.directory
    if not directory.is_dir() or directory.is_symlink():
        message = (
            f"the source {directory.name!r} is not a directory; a resumption needs its exact "
            "remaining subset"
        )
        raise ChunkTransferError(message)
    present = _walk_files(directory)
    unexpected = sorted(set(present) - set(intent.entries))
    if unexpected:
        message = (
            f"the source holds objects outside the reclaim intent: {unexpected}; nothing is "
            "deleted and no recursive removal exists here"
        )
        raise ChunkTransferError(message)
    for name in present:
        if name.endswith(_UNCLOSED_DATABASE_SUFFIXES):
            message = (
                f"the source holds {name!r}; a database in the set is not closed and nothing is "
                "deleted"
            )
            raise ChunkTransferError(message)
    if telemetry is not None:
        telemetry.sample("reclaim_begin")
    free_before = measured_free_bytes(directory.parent)
    expected_freed = sum(os.lstat(directory / name).st_size for name in present)
    deleted = _remove_exact_entries(directory, list(intent.entries))
    _fsync_directory(directory.parent)
    if os.path.lexists(directory):
        message = "the source still exists after the exact deletion"  # pragma: no cover
        raise ChunkTransferError(message)
    free_after = measured_free_bytes(directory.parent)
    freed = free_after - free_before
    completion = ReclaimRecord.seal(
        contract=RECLAIM_RECORD_CONTRACT,
        record_kind=RECLAIM_COMPLETE,
        chunk_id=intent.chunk_id,
        receipt_identity=intent.receipt_identity,
        qualification_identity=intent.qualification_identity,
        source_manifest_digest=intent.source_manifest_digest,
        entries=intent.entries,
        source_bytes=intent.source_bytes,
        issued_at_utc=intent.issued_at_utc,
        completed_at_utc=utc_now(),
        deleted_entries=len(intent.entries),
        free_before_bytes=free_before,
        free_after_bytes=free_after,
        freed_bytes=freed,
        expected_freed_bytes=expected_freed,
        reconciled=freed >= 0
        and freed
        >= expected_freed
        - (len(present) + 1) * os.statvfs(_nearest_existing(directory.parent)).f_frsize,
    )
    _write_once(reclaim / RECLAIM_COMPLETE_FILENAME, canonical_json_bytes(completion.as_record()))
    if telemetry is not None:
        telemetry.record_sizes(retained_input_bytes=0, output_bytes=None)
        telemetry.sample("reclaim_complete")
    return completion if deleted >= 0 else completion  # pragma: no cover
