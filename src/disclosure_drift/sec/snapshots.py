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
import os
import stat
import uuid
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Literal, Protocol

from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree, relative_to_root
from disclosure_drift.sec.http_client import ACCEPTABLE_CONTENT_TYPES, FetchResult
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
            "observed_content_kind": self.observed_content_kind,
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
    observation_id: str | None = None
    logical_sha256: str | None = None
    content_sha256: str | None = None
    stored_sha256: str | None = None
    etag: str | None = None
    last_modified: str | None = None
    parser_version: str | None = None
    relative_storage_path: str | None = None
    transport_sha256: str | None = None
    transport_size_bytes: int | None = None
    content_size_bytes: int | None = None
    stored_size_bytes: int | None = None
    storage_representation: StorageRepresentation | None = None
    content_encoding: str | None = None
    declared_content_type: str | None = None
    observed_content_kind: str | None = None
    evidence_observation_id: str | None = None

    @property
    def has_snapshot(self) -> bool:
        """Whether a prior payload exists to reuse or compare against."""
        return self.logical_sha256 is not None and self.relative_storage_path is not None


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
            if resolved and observation.identity != resolved:
                continue
            owner = self._evidence_owner(observation)
            return SnapshotIndex(
                source_id=source_id,
                identity=observation.identity,
                observation_id=observation.observation_id,
                logical_sha256=observation.logical_sha256,
                content_sha256=observation.content_sha256,
                stored_sha256=observation.stored_sha256,
                etag=observation.etag,
                last_modified=observation.last_modified,
                parser_version=observation.parser_version,
                relative_storage_path=observation.relative_storage_path,
                transport_sha256=observation.transport_sha256,
                transport_size_bytes=observation.transport_size_bytes,
                content_size_bytes=observation.content_size_bytes,
                stored_size_bytes=observation.stored_size_bytes,
                storage_representation=observation.storage_representation,
                content_encoding=observation.content_encoding,
                declared_content_type=observation.declared_content_type,
                observed_content_kind=observation.observed_content_kind,
                evidence_observation_id=(owner.observation_id if owner is not None else None),
            )
        return SnapshotIndex(source_id=source_id, identity=resolved)

    def _evidence_owner(self, observation: SourceObservation) -> SourceObservation | None:
        """Resolve and validate every hop to the observation owning the raw object."""
        by_id = {item.observation_id: item for item in self._observations}
        current = observation
        visited: set[str] = set()
        while current.reused_observation_id is not None:
            if current.observation_id in visited or current.outcome not in {
                "unchanged_content",
                "reused_snapshot",
            }:
                return None
            visited.add(current.observation_id)
            owner = by_id.get(current.reused_observation_id)
            if owner is None or not self._reuse_edge_is_compatible(current, owner):
                return None
            current = owner
        if current.observation_id in visited or current.outcome not in {
            "stored_new",
            "superseded",
        }:
            return None
        return current

    @staticmethod
    def _reuse_edge_is_compatible(
        observation: SourceObservation,
        target: SourceObservation,
    ) -> bool:
        """Require one reuse edge to preserve the complete shared-object identity."""
        if (
            observation.source_id != target.source_id
            or observation.identity != target.identity
            or target.retrieved_at_utc > observation.retrieved_at_utc
        ):
            return False
        fields = (
            "relative_storage_path",
            "stored_sha256",
            "logical_sha256",
            "content_sha256",
            "transport_sha256",
            "stored_size_bytes",
            "content_size_bytes",
            "transport_size_bytes",
            "storage_representation",
            "parser_version",
            "observed_content_kind",
        )
        return all(getattr(observation, field) == getattr(target, field) for field in fields)

    def payload_path(self, observation: SourceObservation) -> Path:
        """Return the absolute local path for a stored observation.

        Absolute paths are used only at runtime; only the relative path is persisted.
        """
        if observation.relative_storage_path is None:
            message = f"observation {observation.observation_id} stored no payload"
            raise RawObjectIntegrityError(message)
        return self._trusted_raw_path(
            observation.relative_storage_path,
            observation_id=observation.observation_id,
        )

    def _trusted_raw_path(self, relative_path: str, *, observation_id: str) -> Path:
        """Resolve a catalog path without permitting traversal or symlink escape."""
        relative = Path(relative_path)
        approved_roots = {
            ("raw", "sec", "bulk"),
            ("raw", "sec", "filings"),
            ("raw", "sec", "indexes"),
            ("raw", "sec", "quarantine"),
        }
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or tuple(relative.parts[:3]) not in approved_roots
        ):
            message = (
                f"stored object for {observation_id} has an unsafe catalog path {relative_path!r}"
            )
            raise RawObjectIntegrityError(message)

        root = self._tree.data_root
        candidate = root / relative
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                message = (
                    f"stored object for {observation_id} traverses a symbolic link at {current}"
                )
                raise RawObjectIntegrityError(message)
        try:
            resolved_root = root.resolve(strict=True)
            resolved_candidate = candidate.resolve(strict=False)
            resolved_candidate.relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            message = (
                f"stored object for {observation_id} cannot be safely resolved "
                "beneath the configured data root"
            )
            raise RawObjectIntegrityError(message) from exc
        return candidate

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
        wanted = identity or result.identity or ""
        shared = self._evaluate_shared_object(spec, previous, wanted)
        checks = list(shared.checks)
        notes = [] if shared.permitted else [shared.detail]

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

        permitted = all(passed for _, passed in checks)
        detail = (
            "every 304 reuse precondition held for the verified preserved snapshot"
            if permitted
            else "; ".join(notes)
        )
        return ReuseDecision(permitted=permitted, checks=tuple(checks), detail=detail)

    def _evaluate_shared_object(
        self,
        spec: SourceSpec,
        previous: SnapshotIndex,
        identity: str,
    ) -> ReuseDecision:
        """Verify every immutable-object field before any form of reuse."""
        checks: list[tuple[str, bool]] = []
        notes: list[str] = []

        has_prior = previous.has_snapshot and previous.observation_id is not None
        checks.append(("prior_successful_observation", has_prior))
        if not has_prior:
            notes.append("no prior successful observation exists for this request identity")

        same_identity = (
            previous.source_id == spec.source_id
            and bool(previous.identity)
            and previous.identity == identity
        )
        checks.append(("same_source_and_request_identity", same_identity))
        if not same_identity:
            notes.append(f"prior identity {previous.identity!r} does not match {identity!r}")

        metadata_complete = all(
            value is not None
            for value in (
                previous.logical_sha256,
                previous.content_sha256,
                previous.stored_sha256,
                previous.transport_sha256,
                previous.transport_size_bytes,
                previous.content_size_bytes,
                previous.stored_size_bytes,
                previous.storage_representation,
                previous.relative_storage_path,
                previous.parser_version,
                previous.observed_content_kind,
                previous.evidence_observation_id,
            )
        )
        checks.append(("prior_object_metadata_complete", metadata_complete))
        if not metadata_complete:
            notes.append("the prior observation lacks complete immutable-object metadata")

        transport_consistent = (
            previous.transport_sha256 is not None
            and previous.logical_sha256 is not None
            and previous.content_sha256 == previous.logical_sha256
            and previous.transport_sha256 == previous.logical_sha256
            and previous.transport_size_bytes is not None
            and previous.content_size_bytes is not None
            and previous.transport_size_bytes == previous.content_size_bytes
        )
        checks.append(("prior_transport_metadata_consistent", transport_consistent))
        if not transport_consistent:
            notes.append("the prior transport hash or size disagrees with its logical content")

        content_kind_compatible = previous.observed_content_kind == spec.expected_content
        checks.append(("observed_content_kind_compatible", content_kind_compatible))
        if not content_kind_compatible:
            notes.append(
                f"prior observed content kind {previous.observed_content_kind!r} does not "
                f"match registered kind {spec.expected_content!r}"
            )
        declared = previous.declared_content_type
        declared_compatible = declared is None or (
            declared.split(";", 1)[0].strip().lower()
            in ACCEPTABLE_CONTENT_TYPES[spec.expected_content]
        )
        checks.append(("declared_content_type_compatible", declared_compatible))
        if not declared_compatible:
            notes.append(
                f"prior declared content type {declared!r} is incompatible with "
                f"registered kind {spec.expected_content!r}"
            )

        path: Path | None = None
        path_contained = False
        if previous.relative_storage_path is not None:
            try:
                path = self._trusted_raw_path(
                    previous.relative_storage_path,
                    observation_id=previous.observation_id or "unknown",
                )
                path_contained = True
            except RawObjectIntegrityError as exc:
                notes.append(str(exc))
        checks.append(("prior_raw_path_contained", path_contained))
        exists = path_contained and path is not None and path.is_file()
        checks.append(("prior_raw_object_present", exists))
        if has_prior and not exists:
            notes.append("the prior raw object is missing from the store")

        compatible = versions_agree(spec.parser_id, previous.parser_version)
        checks.append(("parser_compatibility_known", compatible))
        if not compatible:
            notes.append(
                f"prior parser version {previous.parser_version!r} is not the "
                f"{spec.parser_id!r} implementation's current {spec.parser_version!r}, "
                "so compatibility is unknown and the result must be reparsed"
            )

        indexed = next(
            (item for item in self._observations if item.observation_id == previous.observation_id),
            None,
        )
        owner = self._evidence_owner(indexed) if indexed is not None else None
        owner_verified = (
            owner is not None
            and owner.outcome in {"stored_new", "superseded"}
            and owner.reused_observation_id is None
            and owner.observation_id == previous.evidence_observation_id
            and owner.source_id == previous.source_id
            and owner.identity == previous.identity
            and owner.relative_storage_path == previous.relative_storage_path
            and owner.stored_sha256 == previous.stored_sha256
            and owner.logical_sha256 == previous.logical_sha256
            and owner.content_sha256 == previous.content_sha256
            and owner.transport_sha256 == previous.transport_sha256
            and owner.stored_size_bytes == previous.stored_size_bytes
            and owner.content_size_bytes == previous.content_size_bytes
            and owner.transport_size_bytes == previous.transport_size_bytes
            and owner.storage_representation == previous.storage_representation
            and owner.parser_version == previous.parser_version
            and owner.observed_content_kind == previous.observed_content_kind
        )
        checks.append(("evidence_owner_verified", owner_verified))
        if not owner_verified:
            notes.append(
                "the reused object does not resolve to a compatible object-owning observation"
            )

        verified = False
        if exists and metadata_complete and owner_verified and owner is not None:
            try:
                self.verify_payload(owner)
            except RawObjectIntegrityError as exc:
                notes.append(str(exc))
            else:
                verified = True
        checks.append(("prior_stored_hash_verifies", verified))
        if exists and not verified:
            notes.append("the prior raw object, representation, hash, or size did not verify")

        permitted = all(passed for _, passed in checks)
        return ReuseDecision(
            permitted=permitted,
            checks=tuple(checks),
            detail=(
                "complete immutable-object metadata and evidence ownership verified"
                if permitted
                else "; ".join(notes)
            ),
        )

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
                "etag": result.etag or previous.etag,
                "last_modified": result.last_modified or previous.last_modified,
                "declared_content_type": previous.declared_content_type,
                "observed_content_kind": previous.observed_content_kind,
                "content_encoding": previous.content_encoding,
                "transport_sha256": previous.transport_sha256,
                "transport_size_bytes": previous.transport_size_bytes,
                "logical_sha256": previous.logical_sha256,
                "content_sha256": previous.content_sha256,
                "content_size_bytes": previous.content_size_bytes,
                "stored_sha256": previous.stored_sha256,
                "stored_size_bytes": previous.stored_size_bytes,
                "storage_representation": previous.storage_representation,
                "relative_storage_path": previous.relative_storage_path,
                "reused_observation_id": previous.evidence_observation_id,
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
        if outcome == "quarantined" and (result.body or result.chunks is not None):
            quarantined_path, evidence_hash, evidence_size = self._quarantine_payload(
                spec,
                result,
                timestamp,
            )
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

        refused_identical_reuse: ReuseDecision | None = None
        if previous.has_snapshot and previous.logical_sha256 == logical_hash:
            identical_reuse = self._evaluate_shared_object(spec, previous, identity)
            if identical_reuse.permitted:
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
                        "reused_observation_id": previous.evidence_observation_id,
                        "reason_codes": ("SOURCE_CONTENT_UNCHANGED",),
                        "detail": (
                            "official content is byte-identical to the preserved object; "
                            f"{identical_reuse.detail}; the prior payload is reused and "
                            "this retrieval is still recorded"
                        ),
                    }
                )
            refused_identical_reuse = identical_reuse

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
        if refused_identical_reuse is not None:
            return self._append_values(
                base
                | stored_values
                | {
                    "detail": (
                        "the response matched the prior logical hash, but reuse was "
                        f"refused ({refused_identical_reuse.detail}); current bytes were "
                        "persisted and will be parsed as a fresh observation"
                    )
                }
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
        with stored_path.open("rb") as handle:
            on_disk_sha256, _ = self._stream_digest(handle)
        if on_disk_sha256 != stored_sha256:
            return "the bytes on disk do not match the stored hash recorded by the raw store"
        if representation == "deterministic_gzip":
            with gzip.open(stored_path, "rb") as handle:
                recovered_sha256, _ = self._stream_digest(handle)
        else:
            recovered_sha256 = on_disk_sha256
        if recovered_sha256 != transport_sha256:
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
        close = getattr(chunks, "close", None)
        try:
            with part.open("wb") as handle:
                for chunk in chunks:
                    digest.update(chunk)
                    size += len(chunk)
                    handle.write(chunk)
        finally:
            if callable(close):
                close()
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
        if (
            not filename
            or filename in {".", ".."}
            or "\x00" in filename
            or Path(filename).name != filename
        ):
            message = f"refusing unsafe audit-log filename {filename!r}"
            raise RawObjectIntegrityError(message)

        path = self._tree.audit / filename
        selected = observations if observations is not None else self._observations
        directory_descriptor = self._open_audit_directory()
        try:
            descriptor, created = self._open_audit_append(directory_descriptor, filename)
            try:
                with os.fdopen(descriptor, "ab", closefd=False) as handle:
                    for observation in selected:
                        encoded = (
                            json.dumps(
                                observation.as_record(),
                                ensure_ascii=True,
                                allow_nan=False,
                                sort_keys=True,
                            )
                            + "\n"
                        ).encode("utf-8")
                        handle.write(encoded)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                os.close(descriptor)
            if created:
                os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        return path

    def _open_audit_directory(self) -> int:
        """Open ``audit/sec`` without following either managed path component."""
        no_follow = getattr(os, "O_NOFOLLOW", None)
        directory = getattr(os, "O_DIRECTORY", None)
        if not isinstance(no_follow, int) or not isinstance(directory, int):
            message = "this platform cannot safely open audit paths without following links"
            raise RawObjectIntegrityError(message)

        self._tree.data_root.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDONLY | directory | getattr(os, "O_CLOEXEC", 0)
        try:
            descriptor = os.open(self._tree.data_root, flags)
        except OSError as exc:
            message = "the configured data root cannot be opened as a directory"
            raise RawObjectIntegrityError(message) from exc

        managed_flags = flags | no_follow
        try:
            for component in ("audit", "sec"):
                next_descriptor = self._open_or_create_audit_component(
                    descriptor,
                    component,
                    managed_flags,
                )
                os.close(descriptor)
                descriptor = next_descriptor
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    @staticmethod
    def _open_or_create_audit_component(
        parent_descriptor: int,
        component: str,
        flags: int,
    ) -> int:
        """Open one managed directory component and reject links or non-directories."""
        try:
            os.mkdir(component, mode=0o700, dir_fd=parent_descriptor)
        except FileExistsError:
            pass
        except OSError as exc:
            message = f"audit path component {component!r} could not be created safely"
            raise RawObjectIntegrityError(message) from exc
        else:
            os.fsync(parent_descriptor)

        try:
            return os.open(component, flags, dir_fd=parent_descriptor)
        except OSError as exc:
            message = f"audit path component {component!r} is not a safe, non-linked directory"
            raise RawObjectIntegrityError(message) from exc

    @staticmethod
    def _open_audit_append(directory_descriptor: int, filename: str) -> tuple[int, bool]:
        """Open one regular audit file for append without following symbolic links."""
        no_follow = getattr(os, "O_NOFOLLOW", None)
        if not isinstance(no_follow, int):
            message = "this platform cannot safely append audit logs without following links"
            raise RawObjectIntegrityError(message)

        flags = os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK | no_follow | getattr(os, "O_CLOEXEC", 0)
        try:
            descriptor = os.open(
                filename,
                flags | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory_descriptor,
            )
            created = True
        except FileExistsError:
            try:
                descriptor = os.open(filename, flags, dir_fd=directory_descriptor)
            except OSError as exc:
                message = f"audit log {filename!r} is not a safe, non-linked regular file"
                raise RawObjectIntegrityError(message) from exc
            created = False
        except OSError as exc:
            message = f"audit log {filename!r} could not be created safely"
            raise RawObjectIntegrityError(message) from exc

        try:
            metadata = os.fstat(descriptor)
        except OSError as exc:
            os.close(descriptor)
            message = f"audit log {filename!r} could not be verified after opening"
            raise RawObjectIntegrityError(message) from exc
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            os.close(descriptor)
            message = f"audit log {filename!r} is not a singly linked regular file"
            raise RawObjectIntegrityError(message)
        return descriptor, created

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

    def _quarantine_payload(
        self,
        spec: SourceSpec,
        result: FetchResult,
        timestamp: str,
    ) -> tuple[str, str, int]:
        """Durably spool malformed evidence, transfer it to quarantine, and hash it."""
        staging = self._tree.staging
        staging.mkdir(parents=True, exist_ok=True)
        temporary = staging / f"{spec.source_id}-{uuid.uuid4().hex}.rejected"
        digest = hashlib.sha256()
        size = 0
        chunks: Iterable[bytes] = result.chunks if result.chunks is not None else (result.body,)
        try:
            with temporary.open("xb") as handle:
                for chunk in chunks:
                    digest.update(chunk)
                    size += len(chunk)
                    handle.write(chunk)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            result.close()
        target = self._raw.quarantine(
            temporary,
            result.reason_code or "SEC_RESPONSE_MALFORMED",
            f"{spec.source_id} rejected at {timestamp}: {result.detail}",
        )
        return relative_to_root(target, self._tree.data_root), digest.hexdigest(), size

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
