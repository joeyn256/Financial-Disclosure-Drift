"""Create-once evidence for a chunked F0: manifests, digests and terminal receipts.

**One rule runs through the whole module: the receipt is written LAST.** A chunk's receipt, a
transfer's receipt and the final world's receipt are each written after every artifact they
describe is closed, complete and on disk, and each of them carries a manifest of exactly those
artifacts with a per-object SHA-256. A receipt that exists is therefore proof the work finished;
a receipt that is absent is a refusal rather than a gap; and a receipt that describes bytes the
artifacts no longer carry is refused rather than believed.

**Nothing here is a status file.** D151-C1 §11 asks that a chunk's state derive from durable
evidence rather than from something claiming a state. That is what
:func:`verify_artifact_manifest` is for: it re-opens every named object, re-reads it, re-hashes
it, and refuses a missing object, a changed object, an extra object, and a symbolic link. A
state derived from that survives an adversary with write access to the JSON.

**Create-once is enforced by the operating system, not by a check.** :func:`write_once_json`
opens with ``O_CREAT | O_EXCL``, so a second writer loses the race rather than winning it, and
a receipt is never overwritten, repaired, or re-stamped.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "CHUNK_DECLARATIONS_FILENAME",
    "CHUNK_PLAN_FILENAME",
    "CHUNK_RECEIPT_CONTRACT",
    "CHUNK_RECEIPT_FILENAME",
    "CHUNK_WITNESS_FILENAME",
    "FINAL_WORLD_RECEIPT_CONTRACT",
    "FINAL_WORLD_RECEIPT_FILENAME",
    "PARENT_MAP_FILENAME",
    "TRANSFER_RECEIPT_CONTRACT",
    "TRANSFER_RECEIPT_FILENAME",
    "ArtifactEntry",
    "ArtifactManifest",
    "ChunkEvidenceError",
    "ChunkReceipt",
    "SemanticSummary",
    "build_artifact_manifest",
    "file_sha256",
    "read_receipt_document",
    "verify_artifact_manifest",
    "write_once_json",
]


class ChunkEvidenceError(DisclosureDriftError):
    """A create-once evidence precondition failed. Never overwritten, never repaired."""


#: The chunk terminal receipt's contract identity.
CHUNK_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-chunk-receipt/1"

#: The verified-transfer receipt's contract identity.
TRANSFER_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-transfer-receipt/1"

#: The consolidated world receipt's contract identity.
FINAL_WORLD_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-final-receipt/1"

#: The chunk terminal receipt's fixed filename. Written LAST, inside the chunk attempt directory.
CHUNK_RECEIPT_FILENAME: Final = "chunk_receipt.json"

#: The verified-transfer receipt's fixed filename, written LAST inside the external chunk copy.
TRANSFER_RECEIPT_FILENAME: Final = "transfer_receipt.json"

#: The consolidated world receipt's fixed filename, written LAST inside the final world.
FINAL_WORLD_RECEIPT_FILENAME: Final = "final_world_receipt.json"

#: The plan copy every chunk attempt carries, so an artifact found on its own still says which
#: partition it belongs to.
CHUNK_PLAN_FILENAME: Final = "chunk_plan.json"

#: One primary chunk's contribution to the historical-shard parent map.
CHUNK_DECLARATIONS_FILENAME: Final = "chunk_declarations.json"

#: The merged parent map a shard chunk consumes, written once the primary region is complete.
PARENT_MAP_FILENAME: Final = "parent_map.json"

#: The chunk-local first-witness ledger. Run-local; no migration, no accepted-schema change.
CHUNK_WITNESS_FILENAME: Final = "chunk_witness.sqlite3"

#: File suffixes that must never be present when a manifest is built.
#:
#: A ``-wal`` or ``-shm`` beside a chunk database means a connection is still open or was not
#: closed cleanly, and hashing the main file then would hash a database missing its committed
#: tail. The chunk closes every handle before it manifests, so their presence is a defect.
_UNCLOSED_DATABASE_SUFFIXES: Final[tuple[str, ...]] = ("-wal", "-shm", "-journal")

_FILE_MODE: Final = 0o600
_READ_CHUNK_BYTES: Final = 1 << 20


def file_sha256(path: Path) -> tuple[str, int]:
    """One file's SHA-256 and byte length, read in bounded chunks.

    Raises:
        ChunkEvidenceError: the path is a symbolic link or is not a regular file.
    """
    if path.is_symlink():
        message = (
            f"{path.name!r} is a symbolic link; a chunk artifact is a regular file and a link "
            "is refused rather than followed to whatever it currently points at"
        )
        raise ChunkEvidenceError(message)
    if not path.is_file():
        message = f"{path.name!r} is not a regular file and cannot be an artifact"
        raise ChunkEvidenceError(message)
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(_READ_CHUNK_BYTES), b""):
            digest.update(block)
            length += len(block)
    return digest.hexdigest(), length


@dataclass(frozen=True, slots=True)
class ArtifactEntry:
    """One object a receipt binds: its relative path, its length, and its content digest."""

    relative_path: str
    byte_length: int
    sha256: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free-above-the-root rendering."""
        return {
            "relative_path": self.relative_path,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ArtifactEntry:
        """Rebuild one entry from its stored mapping.

        Raises:
            ChunkEvidenceError: a field is absent or is not of the recorded type.
        """
        try:
            length = record["byte_length"]
            if isinstance(length, bool) or not isinstance(length, int):
                message = "an artifact entry's byte_length is not an integer and is refused"
                raise ChunkEvidenceError(message)
            return cls(
                relative_path=str(record["relative_path"]),
                byte_length=int(length),
                sha256=str(record["sha256"]),
            )
        except KeyError as exc:
            message = f"an artifact entry is missing {exc}; it is refused rather than read"
            raise ChunkEvidenceError(message) from exc


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    """Every object one receipt binds, in a fixed order, with a digest over all of them."""

    entries: tuple[ArtifactEntry, ...]

    @property
    def digest(self) -> str:
        """A deterministic digest over every entry, in relative-path order."""
        digest = hashlib.sha256()
        for entry in self.entries:
            digest.update(
                "\x1f".join((entry.relative_path, str(entry.byte_length), entry.sha256)).encode(
                    "utf-8"
                )
            )
            digest.update(b"\x1e")
        return digest.hexdigest()

    @property
    def total_bytes(self) -> int:
        """How many bytes the manifest's objects occupy in total."""
        return sum(entry.byte_length for entry in self.entries)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering, entries included."""
        return {
            "entries": [dict(entry.as_record()) for entry in self.entries],
            "manifest_digest": self.digest,
            "total_bytes": self.total_bytes,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ArtifactManifest:
        """Rebuild a manifest and re-derive its digest from the entries it actually carries.

        Raises:
            ChunkEvidenceError: the record is malformed, or its stored digest does not describe
                the entries beside it.
        """
        raw = record.get("entries")
        if not isinstance(raw, Sequence) or isinstance(raw, str | bytes):
            message = "an artifact manifest's 'entries' field is not a sequence and is refused"
            raise ChunkEvidenceError(message)
        entries = tuple(
            ArtifactEntry.from_record(item) for item in raw if isinstance(item, Mapping)
        )
        if len(entries) != len(raw):
            message = "an artifact manifest carries an entry that is not a mapping; refused"
            raise ChunkEvidenceError(message)
        manifest = cls(entries=entries)
        recorded = record.get("manifest_digest")
        if recorded is not None and str(recorded) != manifest.digest:
            message = (
                "an artifact manifest's recorded digest does not describe its own entries: "
                f"recorded {recorded!r}, recomputed {manifest.digest!r}"
            )
            raise ChunkEvidenceError(message)
        return manifest


def _relative_files(directory: Path, *, exclude: frozenset[str]) -> list[Path]:
    if directory.is_symlink() or not directory.is_dir():
        message = (
            f"{directory.name!r} is not a directory this build will manifest; a symbolic link "
            "or a missing directory is refused rather than walked"
        )
        raise ChunkEvidenceError(message)
    found: list[Path] = []
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if relative in exclude:
            continue
        if path.is_symlink():
            message = (
                f"artifact {relative!r} is a symbolic link; a chunk artifact set holds regular "
                "files only, and a link is refused rather than followed"
            )
            raise ChunkEvidenceError(message)
        if path.is_dir():
            continue
        if relative.endswith(_UNCLOSED_DATABASE_SUFFIXES):
            message = (
                f"artifact directory holds {relative!r}: a write-ahead log or hot journal is "
                "present, so a database in this set was not closed cleanly. Hashing the main "
                "file now would hash a database missing its committed tail, and the manifest is "
                "refused rather than taken over an inconsistent set"
            )
            raise ChunkEvidenceError(message)
        if not path.is_file():
            message = f"artifact {relative!r} is not a regular file and is refused"
            raise ChunkEvidenceError(message)
        found.append(path)
    return found


def build_artifact_manifest(directory: Path, *, exclude: Iterable[str] = ()) -> ArtifactManifest:
    """Manifest every regular file beneath ``directory``, hashed, in relative-path order.

    ``exclude`` names the objects a receipt must not describe -- above all, the receipt file
    itself, which does not yet exist when the manifest is taken and must not exist when it is
    verified either.

    Raises:
        ChunkEvidenceError: the directory is missing or is a link, an entry is a link or is not
            a regular file, or a write-ahead log betrays an unclosed database.
    """
    excluded = frozenset(exclude)
    entries: list[ArtifactEntry] = []
    for path in _relative_files(directory, exclude=excluded):
        sha256, length = file_sha256(path)
        entries.append(
            ArtifactEntry(
                relative_path=path.relative_to(directory).as_posix(),
                byte_length=length,
                sha256=sha256,
            )
        )
    return ArtifactManifest(entries=tuple(entries))


def verify_artifact_manifest(
    directory: Path, manifest: ArtifactManifest, *, exclude: Iterable[str] = ()
) -> None:
    """Re-read every named object and refuse anything the manifest does not exactly describe.

    Four refusals, and each one is dispositive:

    * an object the manifest names is **absent**;
    * an object's bytes **changed** -- length or digest;
    * an object is present that the manifest **does not name** (D151-C1 §30 A46: a spill that
      carried an extra file is not the artifact set the receipt bound);
    * an object is a **symbolic link**, or a write-ahead log is present.

    Raises:
        ChunkEvidenceError: any of them.
    """
    excluded = frozenset(exclude)
    present = {
        path.relative_to(directory).as_posix(): path
        for path in _relative_files(directory, exclude=excluded)
    }
    named = {entry.relative_path: entry for entry in manifest.entries}
    missing = sorted(set(named) - set(present))
    if missing:
        message = (
            f"the artifact manifest names {len(missing)} object(s) that are not present: "
            f"{missing[:8]}. A manifest is verified against what is on disk, never assumed"
        )
        raise ChunkEvidenceError(message)
    extra = sorted(set(present) - set(named))
    if extra:
        message = (
            f"{len(extra)} object(s) are present that the artifact manifest does not name: "
            f"{extra[:8]}. An artifact set with an unrecorded file is not the set the receipt "
            "bound, and it is refused rather than accepted as a superset"
        )
        raise ChunkEvidenceError(message)
    for relative, entry in sorted(named.items()):
        sha256, length = file_sha256(present[relative])
        if length != entry.byte_length or sha256 != entry.sha256:
            message = (
                f"artifact {relative!r} does not match the manifest: recorded "
                f"{entry.byte_length} bytes / {entry.sha256}, observed {length} bytes / "
                f"{sha256}. A completed chunk is IMMUTABLE, and an altered one is refused "
                "rather than re-manifested"
            )
            raise ChunkEvidenceError(message)


def write_once_json(path: Path, document: Mapping[str, object]) -> Path:
    """Write one canonical JSON document exactly once, or refuse.

    ``O_CREAT | O_EXCL`` rather than an existence check and a write: the check-then-write form
    has a window in which two processes both see nothing and both proceed, and the whole point
    of a create-once terminal is that exactly one of them can succeed.

    Raises:
        ChunkEvidenceError: the path already exists, or is a symbolic link.
    """
    if path.is_symlink():
        message = f"{path.name!r} exists as a symbolic link and is never written through"
        raise ChunkEvidenceError(message)
    payload = json.dumps(document, sort_keys=True, indent=2, default=str).encode("utf-8")
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, _FILE_MODE)
    except FileExistsError as exc:
        message = (
            f"{path.name!r} already exists; this document is create-once and is never "
            "overwritten, repaired, or re-stamped. A second write here would be either a "
            "duplicate execution recording itself or a later attempt erasing an earlier one"
        )
        raise ChunkEvidenceError(message) from exc
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return path


def read_receipt_document(path: Path, *, contract: str) -> Mapping[str, object]:
    """One receipt document, or a refusal.

    Raises:
        ChunkEvidenceError: the receipt is absent, is a link, is not decodable JSON, is not a
            JSON object, or carries a contract this build does not read.
    """
    if path.is_symlink():
        message = f"receipt {path.name!r} is a symbolic link and is refused rather than read"
        raise ChunkEvidenceError(message)
    if not path.is_file():
        message = (
            f"no receipt exists at {path.name!r}. An absent terminal receipt is a REFUSAL, not "
            "a gap: work that did not reach its terminal never wrote one, which is exactly what "
            "makes the presence of one proof that it did"
        )
        raise ChunkEvidenceError(message)
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        message = f"receipt {path.name!r} is not decodable JSON and is refused: {exc}"
        raise ChunkEvidenceError(message) from exc
    if not isinstance(decoded, dict):
        message = f"receipt {path.name!r} is not a JSON object and is refused"
        raise ChunkEvidenceError(message)
    observed = str(decoded.get("contract", ""))
    if observed != contract:
        message = (
            f"receipt {path.name!r} carries contract {observed!r}; this build reads "
            f"{contract!r} and never adopts a shape it half understands"
        )
        raise ChunkEvidenceError(message)
    return decoded


@dataclass(frozen=True, slots=True)
class SemanticSummary:
    """What one chunk actually produced, as counts and digests rather than as prose.

    Every field is a property of the parse rather than of the write, so a consolidator can
    compare two independently produced chunks and a reviewer can compare a chunked run against
    the accepted monolithic one without opening a database.
    """

    members: int
    records: int
    parsed_records: int
    quarantined_records: int
    omitted_field_observations: int
    materialized_field_observations: int
    parser_state_after: str
    run_outcome: str
    table_row_counts: Mapping[str, int]
    member_manifest_digest: str
    projection_digest_chain: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "members": self.members,
            "records": self.records,
            "parsed_records": self.parsed_records,
            "quarantined_records": self.quarantined_records,
            "omitted_field_observations": self.omitted_field_observations,
            "materialized_field_observations": self.materialized_field_observations,
            "parser_state_after": self.parser_state_after,
            "run_outcome": self.run_outcome,
            "table_row_counts": dict(sorted(self.table_row_counts.items())),
            "member_manifest_digest": self.member_manifest_digest,
            "projection_digest_chain": self.projection_digest_chain,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> SemanticSummary:
        """Rebuild a summary from its stored mapping.

        Raises:
            ChunkEvidenceError: a field is absent or is not of the recorded type.
        """
        try:
            counts = record["table_row_counts"]
            if not isinstance(counts, Mapping):
                message = "a semantic summary's table_row_counts is not a mapping and is refused"
                raise ChunkEvidenceError(message)
            return cls(
                members=_stored_int(record["members"], "members"),
                records=_stored_int(record["records"], "records"),
                parsed_records=_stored_int(record["parsed_records"], "parsed_records"),
                quarantined_records=_stored_int(
                    record["quarantined_records"], "quarantined_records"
                ),
                omitted_field_observations=_stored_int(
                    record["omitted_field_observations"], "omitted_field_observations"
                ),
                materialized_field_observations=_stored_int(
                    record["materialized_field_observations"], "materialized_field_observations"
                ),
                parser_state_after=str(record["parser_state_after"]),
                run_outcome=str(record["run_outcome"]),
                table_row_counts={
                    str(key): _stored_int(value, str(key)) for key, value in counts.items()
                },
                member_manifest_digest=str(record["member_manifest_digest"]),
                projection_digest_chain=str(record["projection_digest_chain"]),
            )
        except KeyError as exc:
            message = f"a semantic summary is missing {exc}; it is refused rather than read"
            raise ChunkEvidenceError(message) from exc


def _stored_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = (
            f"evidence field {field!r} holds {type(value).__name__} where an integer is "
            "required; a record that cannot be read is refused rather than coerced"
        )
        raise ChunkEvidenceError(message)
    return int(value)


@dataclass(frozen=True, slots=True)
class ChunkReceipt:
    """One chunk's create-once terminal record -- D151-C1 §14.

    It binds, in one document, every identity a consolidator must agree with before it may read
    one row of this chunk: the plan it belongs to, which interval it consumed, the artifact it
    consumed, the code that executed it, the process that executed it, the exact objects it
    produced with their sizes and digests, and what those objects mean.
    """

    contract: str
    chunk_id: str
    region: str
    start: int
    end: int
    plan_digest: str
    member_order_digest: str
    source_instance_id: str
    source_observation_id: str
    source_sha256: str
    source_byte_length: int
    repository_head_sha: str
    repository_tree_sha: str
    execution_identity: str
    attempt: int
    pid: int
    rss_peak_bytes: int | None
    completed_at_utc: str
    status: str
    manifest: ArtifactManifest
    summary: SemanticSummary

    def as_record(self) -> Mapping[str, object]:
        """The complete receipt as a plain mapping, carrying no absolute path."""
        return {
            "contract": self.contract,
            "chunk_id": self.chunk_id,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "plan_digest": self.plan_digest,
            "member_order_digest": self.member_order_digest,
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_sha256": self.source_sha256,
            "source_byte_length": self.source_byte_length,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "execution_identity": self.execution_identity,
            "attempt": self.attempt,
            "pid": self.pid,
            "rss_peak_bytes": self.rss_peak_bytes,
            "completed_at_utc": self.completed_at_utc,
            "status": self.status,
            "manifest": dict(self.manifest.as_record()),
            "summary": dict(self.summary.as_record()),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ChunkReceipt:
        """Rebuild a receipt from its stored mapping, refusing one this build cannot read.

        Raises:
            ChunkEvidenceError: a required field is absent or is not of the recorded type.
        """
        try:
            manifest = record["manifest"]
            summary = record["summary"]
            if not isinstance(manifest, Mapping) or not isinstance(summary, Mapping):
                message = "a chunk receipt's manifest or summary is not a mapping and is refused"
                raise ChunkEvidenceError(message)
            peak = record.get("rss_peak_bytes")
            return cls(
                contract=str(record["contract"]),
                chunk_id=str(record["chunk_id"]),
                region=str(record["region"]),
                start=_stored_int(record["start"], "start"),
                end=_stored_int(record["end"], "end"),
                plan_digest=str(record["plan_digest"]),
                member_order_digest=str(record["member_order_digest"]),
                source_instance_id=str(record["source_instance_id"]),
                source_observation_id=str(record["source_observation_id"]),
                source_sha256=str(record["source_sha256"]),
                source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                execution_identity=str(record["execution_identity"]),
                attempt=_stored_int(record["attempt"], "attempt"),
                pid=_stored_int(record["pid"], "pid"),
                rss_peak_bytes=None if peak is None else _stored_int(peak, "rss_peak_bytes"),
                completed_at_utc=str(record["completed_at_utc"]),
                status=str(record["status"]),
                manifest=ArtifactManifest.from_record(manifest),
                summary=SemanticSummary.from_record(summary),
            )
        except KeyError as exc:
            message = f"a chunk receipt is missing {exc}; it is refused rather than read"
            raise ChunkEvidenceError(message) from exc
