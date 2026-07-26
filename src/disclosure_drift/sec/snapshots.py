"""Immutable source observations over the raw store (Decision 009, Stage M2.2).

Every official-source retrieval becomes a :class:`SourceObservation` recording the
source identifier, normalized request identity, requested and final URL, validated
redirect chain, retrieval timestamp, HTTP status, provenance headers, validators sent
and returned, declared and observed content types, byte counts, three distinct
hashes, parser version, relative local path, supersession relationship, and reason
codes.

**Three byte identities, kept separate.**

* ``transport_sha256`` — the bytes as delivered by the transport for this response.
  HTTP content-coding (``gzip``, ``deflate``) has already been removed by the HTTP
  library at this boundary; ``content_encoding`` records what was declared, so the
  representation the hash covers is unambiguous. The wire-compressed octets are not
  preserved and this hash never stands for them.
* ``stored_sha256`` — the bytes actually written to disk, which is the deterministic
  gzip container when a text-like payload is compressed for storage, and identical to
  the transport bytes otherwise. ``storage_representation`` says which.
* ``logical_sha256`` — the parser's input for this object. For a JSON, HTML, or text
  payload it equals the transport bytes. For an archive it is the archive itself; each
  member is hashed separately by :mod:`disclosure_drift.sec.archive` and tied back
  through archive-to-member lineage. A decompressed member hash is never reported as
  the transport hash of the archive.

``content_sha256`` is retained as the Decision 009 integrity anchor and always equals
``logical_sha256``.

**Rules enforced here.**

* An existing observation is never overwritten and no raw object is ever replaced.
* Identical content reuses the stored object and still records a fresh observation.
* Changed content at a living source is an ordinary update: a new observation
  supersedes the prior one with the neutral ``SOURCE_CONTENT_UPDATED`` reason. Only a
  change the source's semantics cannot explain earns a blocking mutation reason; see
  :mod:`disclosure_drift.sec.mutation`.
* A ``304`` may be honoured only when every reuse precondition holds; otherwise it
  fails closed and is never read as an empty or new dataset.
* Partial and malformed payloads are quarantined and preserved.
* An unsuccessful retrieval stays distinguishable from a successful empty response.
* No absolute local path is persisted.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import uuid
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree, relative_to_root
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.mutation import PriorContent, classify_content_change
from disclosure_drift.sec.parsers.versions import versions_agree
from disclosure_drift.sec.raw_store import RawStore, decompress, sha256_of
from disclosure_drift.sec.source_registry import SourceSpec, require_registered
from disclosure_drift.sec.urls import request_identity

__all__ = [
    "PROVENANCE_HEADERS",
    "ObservationOutcome",
    "ReuseDecision",
    "SnapshotIndex",
    "SnapshotStore",
    "SourceObservation",
    "StorageRepresentation",
    "observations_by_outcome",
]

PROVENANCE_HEADERS: Final[tuple[str, ...]] = (
    "etag",
    "last-modified",
    "content-type",
    "content-length",
    "content-encoding",
    "date",
)
"""Response headers retained for provenance. No request headers are ever stored."""

ObservationOutcome = Literal[
    "stored_new",
    "unchanged_content",
    "superseded",
    "reused_snapshot",
    "quarantined",
    "failed",
]
StorageRepresentation = Literal["identical", "deterministic_gzip"]
_TEXT_LIKE: Final[frozenset[str]] = frozenset({"json", "html", "text"})


class _ReadableBytes(Protocol):
    def read(self, size: int = -1) -> bytes:
        """Read up to ``size`` bytes."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class SourceObservation:
    """One immutable observation of an official SEC source."""

    observation_id: str
    source_id: str
    requested_url: str
    purpose: str
    retrieved_at_utc: str
    outcome: ObservationOutcome
    identity: str = ""
    final_url: str | None = None
    http_status: int | None = None
    headers: Mapping[str, str] = field(default_factory=dict)
    etag: str | None = None
    last_modified: str | None = None
    validators_sent: Mapping[str, str] = field(default_factory=dict)
    declared_content_type: str | None = None
    observed_content_kind: str | None = None
    content_encoding: str | None = None
    transport_sha256: str | None = None
    stored_sha256: str | None = None
    logical_sha256: str | None = None
    content_sha256: str | None = None
    transport_size_bytes: int | None = None
    content_size_bytes: int | None = None
    stored_size_bytes: int | None = None
    storage_representation: StorageRepresentation | None = None
    relative_storage_path: str | None = None
    parser_version: str | None = None
    supersedes_observation_id: str | None = None
    reused_observation_id: str | None = None
    redirects: tuple[str, ...] = ()
    redirect_hops: tuple[Mapping[str, object], ...] = ()
    attempts: int = 0
    reason_codes: tuple[str, ...] = ()
    detail: str = ""

    @property
    def is_usable(self) -> bool:
        """Whether a parser may read this observation's payload."""
        return self.outcome in {"stored_new", "unchanged_content", "superseded", "reused_snapshot"}

    @property
    def is_failure(self) -> bool:
        """Whether this observation records an unsuccessful retrieval."""
        return self.outcome in {"failed", "quarantined"}

    @property
    def has_payload(self) -> bool:
        """Whether a local payload path is recorded."""
        return self.relative_storage_path is not None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the catalog and the audit projection."""
        return {
            "observation_id": self.observation_id,
            "source_id": self.source_id,
            "identity": self.identity,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "purpose": self.purpose,
            "retrieved_at_utc": self.retrieved_at_utc,
            "outcome": self.outcome,
            "http_status": self.http_status,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "validators_sent": dict(sorted(self.validators_sent.items())),
            "declared_content_type": self.declared_content_type,
            "content_encoding": self.content_encoding,
            "transport_sha256": self.transport_sha256,
            "stored_sha256": self.stored_sha256,
            "logical_sha256": self.logical_sha256,
            "content_sha256": self.content_sha256,
            "transport_size_bytes": self.transport_size_bytes,
            "content_size_bytes": self.content_size_bytes,
            "stored_size_bytes": self.stored_size_bytes,
            "storage_representation": self.storage_representation,
            "relative_storage_path": self.relative_storage_path,
            "parser_version": self.parser_version,
            "supersedes_observation_id": self.supersedes_observation_id,
            "reused_observation_id": self.reused_observation_id,
            "redirects": list(self.redirects),
            "redirect_hops": [dict(hop) for hop in self.redirect_hops],
            "attempts": self.attempts,
            "reason_codes": list(self.reason_codes),
            "headers": dict(sorted(self.headers.items())),
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class SnapshotIndex:
    """What is already preserved for one request identity."""

    source_id: str
    identity: str
    observation_id: str | None
    logical_sha256: str | None
    stored_sha256: str | None
    etag: str | None
    last_modified: str | None
    parser_version: str | None
    relative_storage_path: str | None
    content_size_bytes: int | None = None
    stored_size_bytes: int | None = None
    storage_representation: StorageRepresentation | None = None

    @property
    def has_snapshot(self) -> bool:
        """Whether a prior payload exists to reuse or compare against."""
        return self.logical_sha256 is not None and self.relative_storage_path is not None

    @property
    def content_sha256(self) -> str | None:
        """Decision 009 integrity anchor of the preserved object."""
        return self.logical_sha256


@dataclass(frozen=True, slots=True)
class ReuseDecision:
    """Whether a ``304`` may be honoured, and why."""

    permitted: bool
    checks: tuple[tuple[str, bool], ...]
    detail: str

    @property
    def failed_checks(self) -> tuple[str, ...]:
        """Names of the preconditions that did not hold."""
        return tuple(name for name, passed in self.checks if not passed)


class SnapshotStore:
    """Records immutable source observations and persists their payloads."""

    def __init__(self, tree: DataTree, raw_store: RawStore | None = None) -> None:
        self._tree = tree
        self._raw = raw_store or RawStore(tree)
        self._observations: list[SourceObservation] = []

    # -- state -------------------------------------------------------------- #
    @property
    def observations(self) -> tuple[SourceObservation, ...]:
        """Every observation recorded by this store instance, in order."""
        return tuple(self._observations)

    def adopt(self, observations: Iterable[SourceObservation]) -> None:
        """Load observations recovered from the authoritative catalog.

        The catalog, not this in-memory list, is the operational source of truth. A
        restarted run adopts its recorded observations so conditional requests,
        supersession, and reuse decisions continue from the real prior state.
        """
        for observation in observations:
            self._append(observation)

    def latest_for(self, source_id: str, identity: str | None = None) -> SnapshotIndex:
        """Return the most recent usable snapshot for one request identity.

        Args:
            source_id: Registered source identifier.
            identity: Normalized request identity. When omitted, any identity of the
                source matches, which is only appropriate for a single-URL source.
        """
        resolved = identity or ""
        for observation in reversed(self._observations):
            if observation.source_id != source_id or not observation.has_payload:
                continue
            if not observation.is_usable:
                continue
            if resolved and observation.identity and observation.identity != resolved:
                continue
            return SnapshotIndex(
                source_id=source_id,
                identity=observation.identity,
                observation_id=observation.observation_id,
                logical_sha256=observation.logical_sha256,
                stored_sha256=observation.stored_sha256,
                etag=observation.etag,
                last_modified=observation.last_modified,
                parser_version=observation.parser_version,
                relative_storage_path=observation.relative_storage_path,
                content_size_bytes=observation.content_size_bytes,
                stored_size_bytes=observation.stored_size_bytes,
                storage_representation=observation.storage_representation,
            )
        return SnapshotIndex(source_id, resolved, None, None, None, None, None, None, None)

    def payload_path(self, observation: SourceObservation) -> Path:
        """Return the absolute local path for a stored observation.

        Absolute paths are used only at runtime; only the relative path is persisted.
        """
        if observation.relative_storage_path is None:
            message = f"observation {observation.observation_id} stored no payload"
            raise RawObjectIntegrityError(message)
        return self._tree.data_root / observation.relative_storage_path

    def load_payload(self, observation: SourceObservation) -> bytes:
        """Read a stored payload, verifying both stored and logical hashes.

        Raises:
            RawObjectIntegrityError: the stored bytes or the decoded logical content
                do not match the hashes recorded for this observation.
        """
        self.verify_payload(observation)
        path = self.payload_path(observation)
        stored = path.read_bytes()
        return self._decode(stored, observation, path)

    def verify_payload(self, observation: SourceObservation) -> None:
        """Verify presence, representation, sizes, and stored/logical hashes."""
        path = self.payload_path(observation)
        if not path.is_file():
            message = f"stored object for {observation.observation_id} is missing"
            raise RawObjectIntegrityError(message)
        representation = observation.storage_representation
        if representation not in {"identical", "deterministic_gzip"}:
            message = (
                f"stored object for {observation.observation_id} has no verified storage "
                "representation"
            )
            raise RawObjectIntegrityError(message)
        if (representation == "deterministic_gzip") != (path.suffix == ".gz"):
            message = (
                f"stored representation for {observation.observation_id} does not match "
                f"its path {path.name!r}"
            )
            raise RawObjectIntegrityError(message)

        with path.open("rb") as handle:
            stored_hash, stored_size = self._stream_digest(handle)
        if observation.stored_sha256 is None or stored_hash != observation.stored_sha256:
            message = (
                f"stored object for {observation.observation_id} does not match the recorded "
                "stored_sha256; the object is not trustworthy evidence"
            )
            raise RawObjectIntegrityError(message)
        if (
            observation.stored_size_bytes is not None
            and stored_size != observation.stored_size_bytes
        ):
            message = f"stored size for {observation.observation_id} does not match its catalog row"
            raise RawObjectIntegrityError(message)

        if representation == "deterministic_gzip":
            try:
                with gzip.open(path, "rb") as handle:
                    logical_hash, logical_size = self._stream_digest(handle)
            except (OSError, EOFError) as exc:
                message = f"stored gzip representation for {observation.observation_id} is invalid"
                raise RawObjectIntegrityError(message) from exc
        else:
            logical_hash, logical_size = stored_hash, stored_size
        expected = observation.logical_sha256 or observation.content_sha256
        if expected is None or logical_hash != expected:
            message = (
                f"stored payload for {observation.observation_id} does not match its "
                "recorded content hash"
            )
            raise RawObjectIntegrityError(message)
        if (
            observation.content_size_bytes is not None
            and logical_size != observation.content_size_bytes
        ):
            message = (
                f"logical size for {observation.observation_id} does not match its catalog row"
            )
            raise RawObjectIntegrityError(message)

    @staticmethod
    def _stream_digest(handle: _ReadableBytes) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
        return digest.hexdigest(), size

    # -- recording ---------------------------------------------------------- #
    def record(
        self,
        result: FetchResult,
        *,
        retrieved_at_utc: str | None = None,
        period_is_closed: bool | None = None,
        correction_observation_id: str | None = None,
    ) -> SourceObservation:
        """Turn one retrieval outcome into an immutable observation.

        Args:
            result: Outcome of one controlled retrieval.
            retrieved_at_utc: Timestamp to record; defaults to now.
            period_is_closed: For a dated-snapshot source, whether the period named in
                the URL has closed. ``None`` fails closed rather than assuming open.
            correction_observation_id: Official SEC evidence explaining a correction to
                a dated artifact, when one exists.
        """
        spec = require_registered(result.source_id)
        timestamp = retrieved_at_utc or _utc_now()
        identity = result.identity or request_identity(result.source_id, result.url)
        previous = self.latest_for(result.source_id, identity)

        if result.outcome == "not_modified":
            return self._record_reuse(spec, result, timestamp, identity, previous)
        if result.is_failure:
            return self._record_failure(spec, result, timestamp, identity)
        return self._record_payload(
            spec,
            result,
            timestamp,
            identity,
            previous,
            period_is_closed=period_is_closed,
            correction_observation_id=correction_observation_id,
        )

    # -- 304 reuse ---------------------------------------------------------- #
    def evaluate_reuse(
        self,
        spec: SourceSpec,
        result: FetchResult,
        previous: SnapshotIndex,
        identity: str | None = None,
    ) -> ReuseDecision:
        """Decide whether a ``304`` may be honoured for this identity.

        Every precondition must hold: a prior successful observation exists for the
        same source and normalized request identity, the conditional request used
        validators taken from that observation, the prior raw object still exists, its
        stored hash verifies, and its parser compatibility is known.
        """
        checks: list[tuple[str, bool]] = []
        notes: list[str] = []

        has_prior = previous.has_snapshot and previous.observation_id is not None
        checks.append(("prior_successful_observation", has_prior))
        if not has_prior:
            notes.append("no prior successful observation exists for this request identity")

        wanted = identity or result.identity or ""
        same_identity = (
            previous.source_id == spec.source_id
            and bool(previous.identity)
            and previous.identity == wanted
        )
        checks.append(("same_source_and_request_identity", same_identity))
        if not same_identity:
            notes.append(f"prior identity {previous.identity!r} does not match {wanted!r}")

        sent_from_prior = result.sent_any_validator and (
            (result.sent_etag is None or result.sent_etag == previous.etag)
            and (
                result.sent_last_modified is None
                or result.sent_last_modified == previous.last_modified
            )
        )
        checks.append(("validators_from_that_observation", bool(sent_from_prior)))
        if not sent_from_prior:
            notes.append(
                "the conditional request did not send validators drawn from the prior observation"
            )

        exists = False
        verified = False
        if has_prior and previous.relative_storage_path is not None:
            path = self._tree.data_root / previous.relative_storage_path
            exists = path.is_file()
            if (
                exists
                and previous.stored_sha256 is not None
                and previous.storage_representation in {"identical", "deterministic_gzip"}
            ):
                stored = path.read_bytes()
                representation_matches = (
                    previous.storage_representation == "deterministic_gzip"
                ) == (path.suffix == ".gz")
                try:
                    logical = (
                        decompress(stored)
                        if previous.storage_representation == "deterministic_gzip"
                        else stored
                    )
                except (OSError, EOFError):
                    logical = b""
                verified = (
                    representation_matches
                    and sha256_of(stored) == previous.stored_sha256
                    and sha256_of(logical) == previous.logical_sha256
                    and (
                        previous.stored_size_bytes is None
                        or len(stored) == previous.stored_size_bytes
                    )
                    and (
                        previous.content_size_bytes is None
                        or len(logical) == previous.content_size_bytes
                    )
                )
            elif exists:
                verified = False
                notes.append("the prior observation lacks a stored hash or storage representation")
        checks.append(("prior_raw_object_present", exists))
        if has_prior and not exists:
            notes.append("the prior raw object is missing from the store")
        checks.append(("prior_stored_hash_verifies", verified))
        if exists and not verified:
            notes.append("the prior raw object did not verify against its stored hash")

        # The authoritative version comes from the parser implementation, not from a
        # separately maintained registry string, so a result parsed by an older
        # implementation is never silently reused under the current version's name.
        compatible = versions_agree(spec.parser_id, previous.parser_version)
        checks.append(("parser_compatibility_known", compatible))
        if not compatible:
            notes.append(
                f"prior parser version {previous.parser_version!r} is not the "
                f"{spec.parser_id!r} implementation's current {spec.parser_version!r}, "
                "so compatibility is unknown and the result must be reparsed"
            )

        permitted = all(passed for _, passed in checks)
        detail = (
            "every 304 reuse precondition held for the verified preserved snapshot"
            if permitted
            else "; ".join(notes)
        )
        return ReuseDecision(permitted=permitted, checks=tuple(checks), detail=detail)

    def _record_reuse(
        self,
        spec: SourceSpec,
        result: FetchResult,
        timestamp: str,
        identity: str,
        previous: SnapshotIndex,
    ) -> SourceObservation:
        decision = self.evaluate_reuse(spec, result, previous, identity)
        base = self._base(spec, result, timestamp, "reused_snapshot", identity)
        if not decision.permitted:
            failed = ", ".join(decision.failed_checks)
            return self._append_values(
                base
                | {
                    "outcome": "failed",
                    "reason_codes": ("SOURCE_SNAPSHOT_REUSE_UNRECONCILED",),
                    "detail": (
                        f"304 for {spec.source_id!r} could not be reconciled with a recorded "
                        f"observation (failed: {failed}). {decision.detail}. The response is "
                        "failed closed and is not an empty or new dataset."
                    ),
                }
            )
        return self._append_values(
            base
            | {
                "logical_sha256": previous.logical_sha256,
                "content_sha256": previous.logical_sha256,
                "content_size_bytes": previous.content_size_bytes,
                "stored_sha256": previous.stored_sha256,
                "stored_size_bytes": previous.stored_size_bytes,
                "storage_representation": previous.storage_representation,
                "relative_storage_path": previous.relative_storage_path,
                "reused_observation_id": previous.observation_id,
                "reason_codes": ("SOURCE_SNAPSHOT_REUSED",),
                "detail": (
                    f"conditional request confirmed the preserved snapshot; {decision.detail}"
                ),
            }
        )

    # -- failures ----------------------------------------------------------- #
    def _record_failure(
        self,
        spec: SourceSpec,
        result: FetchResult,
        timestamp: str,
        identity: str,
    ) -> SourceObservation:
        outcome: ObservationOutcome = "quarantined" if result.outcome == "quarantined" else "failed"
        quarantined_path: str | None = None
        evidence: dict[str, object] = {}
        if outcome == "quarantined" and result.body:
            quarantined_path = self._quarantine_payload(spec, result, timestamp)
            evidence_hash = sha256_of(result.body)
            evidence_size = len(result.body)
            evidence = {
                "transport_sha256": evidence_hash,
                "stored_sha256": evidence_hash,
                "logical_sha256": evidence_hash,
                "content_sha256": evidence_hash,
                "transport_size_bytes": evidence_size,
                "stored_size_bytes": evidence_size,
                "content_size_bytes": evidence_size,
                "storage_representation": "identical",
            }
        return self._append_values(
            self._base(spec, result, timestamp, outcome, identity)
            | {
                "relative_storage_path": quarantined_path,
                "reason_codes": (result.reason_code,) if result.reason_code else (),
                "detail": result.detail,
            }
            | evidence
        )

    # -- payloads ----------------------------------------------------------- #
    def _record_payload(
        self,
        spec: SourceSpec,
        result: FetchResult,
        timestamp: str,
        identity: str,
        previous: SnapshotIndex,
        *,
        period_is_closed: bool | None,
        correction_observation_id: str | None,
    ) -> SourceObservation:
        transport_bytes: bytes | None = None
        stream_part: Path | None = None
        if result.chunks is None:
            transport_bytes = result.body
            transport_hash = sha256_of(transport_bytes)
            transport_size = len(transport_bytes)
        else:
            stream_part, transport_hash, transport_size = self._spool_stream(
                result.chunks,
                spec.source_id,
            )
        # For every source registered in Stage M2.2 the parser's input is the object
        # as delivered: a JSON, HTML, or text document, or the archive itself. Archive
        # members are hashed separately with their own lineage.
        logical_hash = transport_hash
        base = self._base(spec, result, timestamp, "stored_new", identity) | {
            "transport_sha256": transport_hash,
            "transport_size_bytes": transport_size,
            "logical_sha256": logical_hash,
            "content_sha256": logical_hash,
            "content_size_bytes": transport_size,
        }

        if previous.has_snapshot and previous.logical_sha256 == logical_hash:
            if stream_part is not None:
                stream_part.unlink()
            return self._append_values(
                base
                | {
                    "outcome": "unchanged_content",
                    "stored_sha256": previous.stored_sha256,
                    "stored_size_bytes": previous.stored_size_bytes,
                    "storage_representation": previous.storage_representation,
                    "content_size_bytes": previous.content_size_bytes,
                    "relative_storage_path": previous.relative_storage_path,
                    "reused_observation_id": previous.observation_id,
                    "reason_codes": ("SOURCE_CONTENT_UNCHANGED",),
                    "detail": (
                        "official content is byte-identical to the preserved object; the "
                        "prior payload is reused and this retrieval is still recorded"
                    ),
                }
            )

        compress = spec.expected_content in _TEXT_LIKE
        stored = self._raw.store(
            chunks=(
                self._file_chunks(stream_part)
                if stream_part is not None
                else [transport_bytes or b""]
            ),
            logical_role=(
                "bulk_archive"
                if spec.retrieval_method == "bulk_archive"
                else f"census_{spec.category}"
            ),
            source_url_canonical=result.final_url or result.url,
            retrieval_attempt_id=f"attempt-{uuid.uuid4().hex}",
            retrieved_at_utc=timestamp,
            filename=self._filename(spec, logical_hash),
            media_type=result.declared_content_type,
            content_encoding_received=result.content_encoding,
            compress=compress,
            recovery_context=base,
        )
        representation: StorageRepresentation = "deterministic_gzip" if compress else "identical"
        stored_values = {
            "stored_sha256": stored.record.stored_sha256,
            "stored_size_bytes": stored.record.stored_size_bytes,
            "storage_representation": representation,
            "relative_storage_path": stored.record.relative_storage_path,
        }
        reconciliation = self._reconcile_hashes(
            representation,
            transport_hash,
            stored.absolute_path,
            stored.record.stored_sha256,
        )
        if stream_part is not None:
            stream_part.unlink()
        if reconciliation is not None:
            return self._append_values(
                base
                | stored_values
                | {
                    "outcome": "quarantined",
                    "reason_codes": ("SOURCE_HASH_DISAGREEMENT",),
                    "detail": reconciliation,
                }
            )

        if not previous.has_snapshot:
            return self._append_values(
                base
                | stored_values
                | {"detail": "first preserved snapshot for this request identity"}
            )

        verdict = classify_content_change(
            spec,
            PriorContent(
                observation_id=previous.observation_id or "",
                logical_sha256=previous.logical_sha256 or "",
                etag=previous.etag,
                last_modified=previous.last_modified,
            ),
            logical_sha256=logical_hash,
            etag=result.etag,
            last_modified=result.last_modified,
            period_is_closed=period_is_closed,
            correction_observation_id=correction_observation_id,
        )
        return self._append_values(
            base
            | stored_values
            | {
                "outcome": "superseded",
                "supersedes_observation_id": previous.observation_id,
                "reason_codes": verdict.reason_codes,
                "detail": verdict.detail,
            }
        )

    def _reconcile_hashes(
        self,
        representation: StorageRepresentation,
        transport_sha256: str,
        stored_path: Path,
        stored_sha256: str,
    ) -> str | None:
        """Return a message when transport and stored bytes cannot be reconciled."""
        on_disk = stored_path.read_bytes()
        if sha256_of(on_disk) != stored_sha256:
            return "the bytes on disk do not match the stored hash recorded by the raw store"
        recovered = decompress(on_disk) if representation == "deterministic_gzip" else on_disk
        if sha256_of(recovered) != transport_sha256:
            return (
                f"stored representation {representation!r} does not reproduce the transport "
                "bytes, so the stored object cannot stand as evidence for this response"
            )
        return None

    def _spool_stream(
        self,
        chunks: Iterable[bytes],
        source_id: str,
    ) -> tuple[Path, str, int]:
        """Spool a bulk response to a recoverable part file while hashing it."""
        self._tree.staging.mkdir(parents=True, exist_ok=True)
        part = self._tree.staging / f"{source_id}-{uuid.uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        with part.open("wb") as handle:
            for chunk in chunks:
                digest.update(chunk)
                size += len(chunk)
                handle.write(chunk)
        return part, digest.hexdigest(), size

    @staticmethod
    def _file_chunks(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
        """Yield a spooled response without reading it all into memory."""
        with path.open("rb") as handle:
            while chunk := handle.read(chunk_size):
                yield chunk

    # -- audit projection --------------------------------------------------- #
    def write_audit_log(
        self,
        filename: str = "census_source_observations.jsonl",
        observations: Iterable[SourceObservation] | None = None,
    ) -> Path:
        """Append observations to the readable audit projection and return its path.

        The projection is derived, not authoritative: it can always be rebuilt from the
        catalog rows, so a failure here never makes a recorded observation disappear.
        """
        self._tree.audit.mkdir(parents=True, exist_ok=True)
        path = self._tree.audit / filename
        with path.open("a", encoding="utf-8") as handle:
            for observation in observations if observations is not None else (self._observations):
                handle.write(json.dumps(observation.as_record(), sort_keys=True) + "\n")
        return path

    def iter_usable(self) -> Iterator[SourceObservation]:
        """Yield observations whose payloads may be parsed."""
        for observation in self._observations:
            if observation.is_usable and observation.has_payload:
                yield observation

    # -- internals ---------------------------------------------------------- #
    def _append_values(self, values: Mapping[str, object]) -> SourceObservation:
        return self._append(SourceObservation(**values))  # type: ignore[arg-type]

    def _append(self, observation: SourceObservation) -> SourceObservation:
        if any(item.observation_id == observation.observation_id for item in self._observations):
            message = f"refusing to overwrite observation {observation.observation_id}"
            raise RawObjectIntegrityError(message)
        self._observations.append(observation)
        return observation

    def _base(
        self,
        spec: SourceSpec,
        result: FetchResult,
        timestamp: str,
        outcome: ObservationOutcome,
        identity: str,
    ) -> dict[str, object]:
        return {
            "observation_id": uuid.uuid4().hex,
            "source_id": spec.source_id,
            "identity": identity,
            "requested_url": result.url,
            "final_url": result.final_url or result.url,
            "purpose": result.purpose,
            "retrieved_at_utc": timestamp,
            "outcome": outcome,
            "http_status": result.status,
            "headers": self._provenance_headers(result),
            "etag": result.etag,
            "last_modified": result.last_modified,
            "validators_sent": self._validators_sent(result),
            "declared_content_type": result.declared_content_type,
            "observed_content_kind": spec.expected_content,
            "content_encoding": result.content_encoding,
            "parser_version": spec.parser_version,
            "redirects": result.redirects,
            "redirect_hops": tuple(hop.as_record() for hop in result.redirect_hops),
            "attempts": result.attempts,
        }

    @staticmethod
    def _validators_sent(result: FetchResult) -> Mapping[str, str]:
        sent: dict[str, str] = {}
        if result.sent_etag:
            sent["if-none-match"] = result.sent_etag
        if result.sent_last_modified:
            sent["if-modified-since"] = result.sent_last_modified
        return sent

    @staticmethod
    def _provenance_headers(result: FetchResult) -> Mapping[str, str]:
        collected = dict(result.provenance_headers)
        if result.etag:
            collected["etag"] = result.etag
        if result.last_modified:
            collected["last-modified"] = result.last_modified
        if result.declared_content_type:
            collected["content-type"] = result.declared_content_type
        if result.content_encoding:
            collected["content-encoding"] = result.content_encoding
        return collected

    @staticmethod
    def _filename(spec: SourceSpec, content_hash: str) -> str:
        suffix = {"json": ".json", "zip": ".zip", "html": ".html", "text": ".txt"}[
            spec.expected_content
        ]
        return f"{spec.source_id}-{content_hash[:16]}{suffix}"

    def _quarantine_payload(self, spec: SourceSpec, result: FetchResult, timestamp: str) -> str:
        staging = self._tree.staging
        staging.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(result.body).hexdigest()[:16]
        temporary = staging / f"{spec.source_id}-{digest}.rejected"
        temporary.write_bytes(result.body)
        target = self._raw.quarantine(
            temporary,
            result.reason_code or "SEC_RESPONSE_MALFORMED",
            f"{spec.source_id} rejected at {timestamp}: {result.detail}",
        )
        return relative_to_root(target, self._tree.data_root)

    @staticmethod
    def _decode(stored: bytes, observation: SourceObservation, path: Path) -> bytes:
        gzipped = observation.storage_representation == "deterministic_gzip" or (
            observation.storage_representation is None and path.suffix == ".gz"
        )
        return decompress(stored) if gzipped else stored


def observations_by_outcome(
    observations: Iterable[SourceObservation],
) -> Mapping[str, int]:
    """Count observations by outcome for the census coverage report."""
    counts: dict[str, int] = {}
    for observation in observations:
        counts[observation.outcome] = counts.get(observation.outcome, 0) + 1
    return dict(sorted(counts.items()))
