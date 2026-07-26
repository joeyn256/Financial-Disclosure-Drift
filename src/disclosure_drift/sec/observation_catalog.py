"""Durable persistence and recovery for census source observations.

Authority is explicit and single:

* **SQLite** rows in ``census_source_observations`` are the operational source of
  truth for what has been retrieved.
* **Immutable raw objects** on disk are the evidence those rows point at.
* **JSONL** is an append-only audit projection. It is derived, must be
  reconstructible from the catalog, and a failed append never makes a committed
  observation appear unrecorded: the row is marked unprojected and rebuilt later.

Each observation is written inside one transaction together with its reason codes
and archive-member lineage, so a crash leaves either the whole observation or none of
it. The projection flag is set in a second transaction *after* the JSONL append
succeeds, which is what makes an interrupted append recoverable rather than lossy.

Writes are serialized by the existing catalog writer lease, so two concurrent census
processes cannot interleave source-observation state.

:func:`reconcile` covers the eight required restart scenarios:

1. an interrupted ``.part`` download;
2. a raw object completed with no catalog row;
3. a catalog row whose raw object is missing;
4. an interrupted audit projection append;
5. an identical-content rerun;
6. a changed-content rerun;
7. a ``304`` reuse;
8. a quarantined malformed response.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
import sqlite3
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Literal
from urllib.parse import urlsplit

from disclosure_drift.errors import CatalogWriteError
from disclosure_drift.paths import DataTree, relative_to_root
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.archive import ArchiveMember
from disclosure_drift.sec.raw_store import LINEAGE_SUFFIX, RawStore
from disclosure_drift.sec.snapshots import SourceObservation, StorageRepresentation
from disclosure_drift.sec.source_registry import require_registered
from disclosure_drift.sec.urls import (
    REDIRECT_STATUSES,
    RedirectHop,
    normalize_url,
    request_identity,
    validate_chain,
    validate_url,
)
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = [
    "OBSERVATION_COLUMNS",
    "ObservationRecorder",
    "RecoveryEvent",
    "RecoveryReport",
    "RecoveryResolution",
    "RecoveryScenario",
    "load_observations",
    "rebuild_audit_projection",
    "reconcile",
    "record_recovery_events",
]

RecoveryScenario = Literal[
    "interrupted_part_download",
    "object_without_catalog_row",
    "catalog_row_without_object",
    "audit_projection_interrupted",
    "identical_content_rerun",
    "changed_content_rerun",
    "not_modified_reuse",
    "quarantined_response",
]
RecoveryResolution = Literal["resolved", "blocked"]

OBSERVATION_COLUMNS: Final[tuple[str, ...]] = (
    "observation_id",
    "source_id",
    "request_identity",
    "requested_url",
    "final_url",
    "purpose",
    "retrieved_at_utc",
    "outcome",
    "http_status",
    "etag",
    "last_modified",
    "validators_sent_json",
    "headers_json",
    "declared_content_type",
    "observed_content_kind",
    "content_encoding",
    "transport_sha256",
    "stored_sha256",
    "logical_sha256",
    "content_sha256",
    "transport_size_bytes",
    "content_size_bytes",
    "stored_size_bytes",
    "storage_representation",
    "relative_storage_path",
    "parser_version",
    "supersedes_observation_id",
    "reused_observation_id",
    "redirects_json",
    "redirect_hops_json",
    "attempts",
    "detail",
    "projected_to_audit",
    "recorded_at_utc",
)
_PART_SUFFIX: Final = ".part"
_ENTITY_PATH: Final = re.compile(r"^/submissions/CIK([0-9]{10})\.json$")
_HISTORICAL_PATH: Final = re.compile(r"^/submissions/(CIK[0-9]{10}-submissions-[0-9]{3}\.json)$")
_FULL_INDEX_PATH: Final = re.compile(
    r"^/Archives/edgar/full-index/([0-9]{4})/QTR([1-4])/company\.idx$"
)


@dataclass(frozen=True, slots=True)
class RecoveryEvent:
    """One recorded recovery action."""

    scenario: RecoveryScenario
    action_taken: str
    detail: str
    observation_id: str | None = None
    relative_path: str | None = None
    resolution_state: RecoveryResolution = "resolved"


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    """Outcome of restart reconciliation."""

    events: tuple[RecoveryEvent, ...] = ()
    unprojected_observations: tuple[str, ...] = ()

    @property
    def is_clean(self) -> bool:
        """Whether nothing needed recovery."""
        return not (self.events or self.unprojected_observations)

    def by_scenario(self) -> Mapping[str, int]:
        """Count events by scenario for the QA report."""
        counts: dict[str, int] = {}
        for event in self.events:
            counts[event.scenario] = counts.get(event.scenario, 0) + 1
        return dict(sorted(counts.items()))

    def blocking_reasons(self, *, projection_rebuilt: bool = False) -> tuple[str, ...]:
        """Return every unresolved recovery reason after any successful repair."""
        reasons: list[str] = []
        for event in self.events:
            if event.resolution_state != "blocked":
                continue
            if event.scenario == "audit_projection_interrupted" and projection_rebuilt:
                continue
            target = event.observation_id or event.relative_path or "unknown"
            reasons.append(f"{event.scenario}:{target}")
        return tuple(sorted(reasons))


@dataclass(slots=True)
class ObservationRecorder:
    """Writes observations durably and keeps the audit projection derivable."""

    writer: CatalogWriter
    tree: DataTree
    audit_filename: str = "census_source_observations.jsonl"
    _pending_projection: list[SourceObservation] = field(default_factory=list)

    # -- authoritative write ------------------------------------------------- #
    def record(
        self,
        observation: SourceObservation,
        *,
        members: Sequence[ArchiveMember] = (),
    ) -> str:
        """Commit one observation, its reasons, and its member lineage atomically.

        The observation is recorded once this returns, whatever happens to the audit
        projection afterwards.

        Raises:
            CatalogWriteError: a reason code is unregistered, or the observation
                identifier already exists. An existing row is never overwritten.
        """
        for code in observation.reason_codes:
            if code not in REASON_CODES:
                message = (
                    f"unregistered reason code {code!r} on observation {observation.observation_id}"
                )
                raise CatalogWriteError(message)
        if self._exists(observation.observation_id):
            message = (
                f"observation {observation.observation_id} is already recorded; "
                "observations are immutable and are never overwritten"
            )
            raise CatalogWriteError(message)

        now = utc_now()
        with transaction(self.writer.connection) as connection:
            connection.execute(
                f"INSERT INTO census_source_observations "  # noqa: S608 - fixed columns
                f"({', '.join(OBSERVATION_COLUMNS)}) VALUES "
                f"({', '.join('?' for _ in OBSERVATION_COLUMNS)})",
                self._row(observation, now),
            )
            for code in observation.reason_codes:
                connection.execute(
                    "INSERT OR IGNORE INTO census_observation_reasons "
                    "(observation_id, reason_code, detail, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?)",
                    (observation.observation_id, code, observation.detail or None, now),
                )
            for member in members:
                lineage = member.lineage()
                connection.execute(
                    "INSERT OR IGNORE INTO census_archive_members "
                    "(observation_id, member_index, member_name, member_sha256, "
                    "member_compressed_size_bytes, member_uncompressed_size_bytes, "
                    "archive_relative_path, archive_sha256, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        observation.observation_id,
                        lineage["member_index"],
                        lineage["member_name"],
                        lineage["member_sha256"],
                        lineage["member_compressed_size_bytes"],
                        lineage["member_uncompressed_size_bytes"],
                        lineage["archive_relative_path"],
                        lineage["archive_sha256"],
                        now,
                    ),
                )
        self._pending_projection.append(observation)
        return observation.observation_id

    def flush_projection(self) -> tuple[int, tuple[str, ...]]:
        """Append committed observations to the JSONL projection.

        Returns:
            The number of rows appended and the identifiers still unprojected. A
            failure here leaves the rows committed and unprojected, never lost.
        """
        if not self._pending_projection:
            return 0, self.unprojected()
        path = self.audit_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with path.open("a", encoding="utf-8") as handle:
            for observation in list(self._pending_projection):
                handle.write(json.dumps(observation.as_record(), sort_keys=True) + "\n")
                handle.flush()
                self._mark_projected(observation.observation_id)
                self._pending_projection.remove(observation)
                written += 1
        return written, self.unprojected()

    def audit_path(self) -> Path:
        """Absolute path of the audit projection file."""
        return self.tree.audit / self.audit_filename

    def unprojected(self) -> tuple[str, ...]:
        """Identifiers of committed observations not yet in the projection."""
        rows = self.writer.connection.execute(
            "SELECT observation_id FROM census_source_observations "
            "WHERE projected_to_audit = 0 ORDER BY retrieved_at_utc, observation_id"
        ).fetchall()
        return tuple(str(row["observation_id"]) for row in rows)

    # -- internals ---------------------------------------------------------- #
    def _exists(self, observation_id: str) -> bool:
        row = self.writer.connection.execute(
            "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        return row is not None

    def _mark_projected(self, observation_id: str) -> None:
        with transaction(self.writer.connection) as connection:
            connection.execute(
                "UPDATE census_source_observations SET projected_to_audit = 1 "
                "WHERE observation_id = ?",
                (observation_id,),
            )

    @staticmethod
    def _row(observation: SourceObservation, now: str) -> tuple[object, ...]:
        return (
            observation.observation_id,
            observation.source_id,
            observation.identity,
            observation.requested_url,
            observation.final_url,
            observation.purpose,
            observation.retrieved_at_utc,
            observation.outcome,
            observation.http_status,
            observation.etag,
            observation.last_modified,
            json.dumps(dict(sorted(observation.validators_sent.items())), sort_keys=True),
            json.dumps(dict(sorted(observation.headers.items())), sort_keys=True),
            observation.declared_content_type,
            observation.observed_content_kind,
            observation.content_encoding,
            observation.transport_sha256,
            observation.stored_sha256,
            observation.logical_sha256,
            observation.content_sha256,
            observation.transport_size_bytes,
            observation.content_size_bytes,
            observation.stored_size_bytes,
            observation.storage_representation,
            observation.relative_storage_path,
            observation.parser_version,
            observation.supersedes_observation_id,
            observation.reused_observation_id,
            json.dumps(list(observation.redirects)),
            json.dumps([dict(hop) for hop in observation.redirect_hops], sort_keys=True),
            observation.attempts,
            observation.detail,
            0,
            now,
        )


def load_observations(connection: sqlite3.Connection) -> tuple[SourceObservation, ...]:
    """Rebuild observations from the authoritative catalog rows, oldest first."""
    rows = connection.execute(
        "SELECT * FROM census_source_observations "
        "ORDER BY retrieved_at_utc, recorded_at_utc, observation_id"
    ).fetchall()
    reasons: dict[str, list[str]] = {}
    for reason_row in connection.execute(
        "SELECT observation_id, reason_code FROM census_observation_reasons "
        "ORDER BY observation_id, reason_code"
    ).fetchall():
        reasons.setdefault(str(reason_row["observation_id"]), []).append(
            str(reason_row["reason_code"])
        )
    return tuple(_observation_from_row(row, reasons) for row in rows)


def rebuild_audit_projection(
    connection: sqlite3.Connection,
    destination: Path,
) -> int:
    """Rewrite the JSONL projection from the catalog and return the row count.

    This proves the projection is derived: it can always be regenerated from the
    authoritative rows, so an interrupted append is a recoverable inconvenience
    rather than a loss of evidence.
    """
    observations = load_observations(connection)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for observation in observations:
            handle.write(json.dumps(observation.as_record(), sort_keys=True) + "\n")
    return len(observations)


def reconcile(
    connection: sqlite3.Connection,
    tree: DataTree,
    *,
    quarantine_partial: bool = True,
) -> RecoveryReport:
    """Reconcile catalog rows, raw objects, and the audit projection after a restart.

    Nothing is deleted. A partial transfer is quarantined and preserved, an orphan
    object is reported for adoption rather than silently trusted, and a row whose
    object is missing is reported rather than repaired.
    """
    events: list[RecoveryEvent] = []
    rows = connection.execute(
        "SELECT * FROM census_source_observations ORDER BY retrieved_at_utc, observation_id"
    ).fetchall()

    recorded_paths: set[str] = set()
    for row in rows:
        relative = row["relative_storage_path"]
        outcome = str(row["outcome"])
        if relative:
            recorded_paths.add(str(relative))
            path = tree.data_root / str(relative)
            failure = _catalog_object_failure(row, path)
            if failure is not None:
                events.append(
                    RecoveryEvent(
                        scenario="catalog_row_without_object",
                        action_taken="blocked_preserved",
                        detail=failure,
                        observation_id=str(row["observation_id"]),
                        relative_path=str(relative),
                        resolution_state="blocked",
                    )
                )
        events.extend(_classify_rerun(row, outcome))

    raw_store = RawStore(tree)
    for path in _iter_raw_files(tree):
        relative = relative_to_root(path, tree.data_root)
        if path.name.endswith(_PART_SUFFIX):
            if quarantine_partial:
                target = raw_store.quarantine(
                    path,
                    "RAW_PARTIAL_DOWNLOAD",
                    "interrupted census transfer found during restart reconciliation",
                )
                events.append(
                    RecoveryEvent(
                        scenario="interrupted_part_download",
                        action_taken="quarantined",
                        detail=(
                            "an interrupted transfer was preserved in quarantine; the "
                            "partial object is resolved and can never be treated as complete"
                        ),
                        relative_path=relative_to_root(target, tree.data_root),
                    )
                )
            else:
                events.append(
                    RecoveryEvent(
                        scenario="interrupted_part_download",
                        action_taken="blocked_preserved",
                        detail="an interrupted .part object remains unreconciled",
                        relative_path=relative,
                        resolution_state="blocked",
                    )
                )
            continue
        if relative in recorded_paths:
            continue
        event = _recover_orphan(connection, tree, path)
        events.append(event)
        if event.action_taken == "adopted_verified":
            recorded_paths.add(relative)

    for lineage in _iter_lineage_files(tree):
        object_name = lineage.name.removesuffix(LINEAGE_SUFFIX)
        object_path = lineage.with_name(object_name)
        object_relative = relative_to_root(object_path, tree.data_root)
        if object_relative in recorded_paths:
            continue
        if object_path.exists():
            continue
        target = raw_store.quarantine(
            lineage,
            "RAW_PARTIAL_DOWNLOAD",
            "lineage intent existed without its promoted raw object",
        )
        events.append(
            RecoveryEvent(
                scenario="object_without_catalog_row",
                action_taken="quarantined_interrupted_promotion",
                detail=(
                    "a recovery intent existed without its raw object; the intent was "
                    "preserved in quarantine and was not adopted"
                ),
                relative_path=relative_to_root(target, tree.data_root),
            )
        )

    unprojected = tuple(
        str(row["observation_id"])
        for row in connection.execute(
            "SELECT observation_id FROM census_source_observations "
            "WHERE projected_to_audit = 0 ORDER BY observation_id"
        ).fetchall()
    )
    if unprojected:
        events.append(
            RecoveryEvent(
                scenario="audit_projection_interrupted",
                action_taken="projection_rebuild_required",
                detail=(
                    f"{len(unprojected)} committed observations are absent from the audit "
                    "projection; the projection is derived and will be rebuilt from the "
                    "catalog. The observations themselves remain recorded."
                ),
                resolution_state="blocked",
            )
        )
    return RecoveryReport(events=tuple(events), unprojected_observations=unprojected)


def _catalog_object_failure(
    row: sqlite3.Row | Mapping[str, object],
    path: Path,
) -> str | None:
    """Return a blocking integrity failure for a cataloged object, if any."""
    if not path.is_file():
        return "the catalog references a missing raw object; the row is preserved"
    required = (
        "source_id",
        "request_identity",
        "stored_sha256",
        "logical_sha256",
        "content_sha256",
        "stored_size_bytes",
        "content_size_bytes",
        "storage_representation",
        "parser_version",
    )
    missing = [name for name in required if row[name] is None or str(row[name]) == ""]
    if missing:
        return f"catalog observation is missing required lineage fields {missing}"
    representation = str(row["storage_representation"])
    if representation not in _REPRESENTATIONS:
        return f"catalog observation has unsupported storage representation {representation!r}"
    if (representation == "deterministic_gzip") != (path.suffix == ".gz"):
        return "stored representation does not agree with the raw-object filename"

    stored_hash, stored_size = _digest_path(path)
    if stored_hash != str(row["stored_sha256"]):
        return "raw object does not match its recorded stored hash; evidence is preserved"
    if stored_size != _required_number(row["stored_size_bytes"]):
        return "raw object does not match its recorded stored size; evidence is preserved"
    if representation == "deterministic_gzip":
        try:
            logical_hash, logical_size = _digest_gzip(path)
        except (OSError, EOFError):
            return "raw object does not contain the recorded deterministic gzip representation"
    else:
        logical_hash, logical_size = stored_hash, stored_size
    if logical_hash != str(row["logical_sha256"]) or logical_hash != str(row["content_sha256"]):
        return "raw object does not reproduce its recorded logical hash"
    if logical_size != _required_number(row["content_size_bytes"]):
        return "raw object does not reproduce its recorded logical size"
    return None


def _recover_orphan(
    connection: sqlite3.Connection,
    tree: DataTree,
    path: Path,
) -> RecoveryEvent:
    """Adopt a cryptographically proven orphan; otherwise quarantine it."""
    lineage = RawStore.lineage_path(path)
    failure: str | None = None
    observation: SourceObservation | None = None
    if not lineage.is_file():
        failure = "the completed raw object has no durable request-lineage intent"
    else:
        try:
            payload = json.loads(lineage.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                message = "lineage intent is not a JSON object"
                raise ValueError(message)
            observation = _observation_from_intent(payload, tree, path)
        except (KeyError, TypeError, ValueError, OSError) as exc:
            failure = f"lineage intent could not be proven: {exc}"

    if observation is not None:
        now = utc_now()
        with transaction(connection) as writable:
            existing = writable.execute(
                "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
                (observation.observation_id,),
            ).fetchone()
            if existing is not None:
                failure = "lineage intent reuses an existing observation identifier"
            else:
                writable.execute(
                    f"INSERT INTO census_source_observations "  # noqa: S608 - fixed columns
                    f"({', '.join(OBSERVATION_COLUMNS)}) VALUES "
                    f"({', '.join('?' for _ in OBSERVATION_COLUMNS)})",
                    ObservationRecorder._row(observation, now),
                )
        if failure is None:
            return RecoveryEvent(
                scenario="object_without_catalog_row",
                action_taken="adopted_verified",
                detail=(
                    "the orphan's registry entry, normalized request identity, storage "
                    "representation, sizes, and hashes were verified before catalog adoption"
                ),
                observation_id=observation.observation_id,
                relative_path=observation.relative_storage_path,
            )

    raw_store = RawStore(tree)
    target = raw_store.quarantine(
        path,
        "RAW_FILE_CHECKSUM_MISMATCH",
        failure or "orphan lineage could not be proven",
    )
    if lineage.is_file():
        raw_store.quarantine(
            lineage,
            "RAW_FILE_CHECKSUM_MISMATCH",
            failure or "orphan lineage could not be proven",
        )
    return RecoveryEvent(
        scenario="object_without_catalog_row",
        action_taken="quarantined_unproven",
        detail=(
            f"{failure or 'orphan lineage could not be proven'}; the object and any "
            "lineage intent were preserved in quarantine"
        ),
        relative_path=relative_to_root(target, tree.data_root),
    )


def _observation_from_intent(
    payload: Mapping[str, object],
    tree: DataTree,
    path: Path,
) -> SourceObservation:
    """Validate a raw-object lineage intent and rebuild its observation."""
    if payload.get("manifest_version") != "raw-object-lineage/1.0":
        message = "unsupported raw-object lineage version"
        raise ValueError(message)
    source_id = str(payload["source_id"])
    spec = require_registered(source_id)
    requested_url = str(payload["requested_url"])
    final_url = str(payload["final_url"])
    validate_url(
        requested_url,
        spec,
        role="recovery request",
        identity_url=requested_url,
    )
    validate_url(
        final_url,
        spec,
        role="recovery final URL",
        identity_url=requested_url,
    )
    identity = str(payload["identity"])
    expected_identity = _recovery_request_identity(source_id, requested_url)
    if identity != expected_identity:
        message = "request identity does not exactly match the registered normalized request"
        raise ValueError(message)
    relative = str(payload["relative_storage_path"])
    if tree.data_root / relative != path:
        message = "lineage intent points at a different raw-object path"
        raise ValueError(message)
    if str(payload["parser_version"]) != spec.parser_version:
        message = "lineage intent parser version is not registry-compatible"
        raise ValueError(message)
    representation = str(payload["storage_representation"])
    if representation not in _REPRESENTATIONS:
        message = "lineage intent has an unsupported storage representation"
        raise ValueError(message)

    redirect_hop_records = tuple(
        _object_mapping(item) for item in _sequence(payload.get("redirect_hops", ()))
    )
    redirect_hops = tuple(_validated_recovery_hop(item) for item in redirect_hop_records)
    validated_chain = validate_chain(requested_url, redirect_hops, final_url, spec)
    expected_from = normalize_url(requested_url)
    for hop in redirect_hops:
        if normalize_url(hop.from_url) != expected_from:
            message = "redirect lineage is not a contiguous policy-owned hop chain"
            raise ValueError(message)
        expected_from = normalize_url(hop.to_url)
    if normalize_url(final_url) != expected_from:
        message = "final URL implies an unrecorded redirect outside the policy-owned hop chain"
        raise ValueError(message)
    recorded_chain = tuple(str(item) for item in _sequence(payload.get("redirects", ())))
    if recorded_chain and tuple(normalize_url(item) for item in recorded_chain) != validated_chain:
        message = "recorded redirect chain does not match the validated hop lineage"
        raise ValueError(message)

    observation = SourceObservation(
        observation_id=str(payload["observation_id"]),
        source_id=source_id,
        identity=identity,
        requested_url=requested_url,
        final_url=final_url,
        purpose=str(payload["purpose"]),
        retrieved_at_utc=str(payload["retrieved_at_utc"]),
        outcome="stored_new",
        http_status=_required_number(payload["http_status"]),
        headers=_string_mapping(payload.get("headers", {})),
        etag=_optional_text(payload.get("etag")),
        last_modified=_optional_text(payload.get("last_modified")),
        validators_sent=_string_mapping(payload.get("validators_sent", {})),
        declared_content_type=_optional_text(payload.get("declared_content_type")),
        observed_content_kind=_optional_text(payload.get("observed_content_kind")),
        content_encoding=_optional_text(payload.get("content_encoding")),
        transport_sha256=str(payload["transport_sha256"]),
        stored_sha256=str(payload["stored_sha256"]),
        logical_sha256=str(payload["logical_sha256"]),
        content_sha256=str(payload["content_sha256"]),
        transport_size_bytes=_required_number(payload["transport_size_bytes"]),
        content_size_bytes=_required_number(payload["content_size_bytes"]),
        stored_size_bytes=_required_number(payload["stored_size_bytes"]),
        storage_representation=representation,
        relative_storage_path=relative,
        parser_version=str(payload["parser_version"]),
        redirects=recorded_chain,
        redirect_hops=redirect_hop_records,
        attempts=_required_number(payload.get("attempts", 0)),
        detail="verified adoption after raw promotion and before catalog commit",
    )
    failure = _catalog_object_failure(
        _row_for_verification(observation),
        path,
    )
    if failure is not None:
        raise ValueError(failure)
    return observation


def _recovery_request_identity(source_id: str, requested_url: str) -> str:
    """Reconstruct the exact request identity from a validated registered URL."""
    path = urlsplit(requested_url).path
    parameters: dict[str, str] = {}
    if source_id == "sec_submissions_entity":
        match = _ENTITY_PATH.fullmatch(path)
        if match is None:
            message = "entity request path cannot supply its canonical CIK parameter"
            raise ValueError(message)
        parameters["cik_padded"] = match.group(1)
    elif source_id == "sec_submissions_historical":
        match = _HISTORICAL_PATH.fullmatch(path)
        if match is None:
            message = "historical request path cannot supply its canonical filename"
            raise ValueError(message)
        parameters["historical_file"] = match.group(1)
    elif source_id == "sec_full_index_company":
        match = _FULL_INDEX_PATH.fullmatch(path)
        if match is None:
            message = "full-index request path cannot supply its year and quarter"
            raise ValueError(message)
        parameters = {"year": match.group(1), "quarter": match.group(2)}
    return request_identity(source_id, requested_url, parameters)


def _validated_recovery_hop(payload: Mapping[str, object]) -> RedirectHop:
    """Build one redirect hop only when its status belongs to the policy contract."""
    status = _required_number(payload.get("status"))
    if status not in REDIRECT_STATUSES:
        message = f"redirect lineage carries non-redirect status {status}"
        raise ValueError(message)
    return RedirectHop(
        status=status,
        from_url=str(payload["from_url"]),
        to_url=str(payload["to_url"]),
    )


def _row_for_verification(observation: SourceObservation) -> Mapping[str, object]:
    return {
        "source_id": observation.source_id,
        "request_identity": observation.identity,
        "stored_sha256": observation.stored_sha256,
        "logical_sha256": observation.logical_sha256,
        "content_sha256": observation.content_sha256,
        "stored_size_bytes": observation.stored_size_bytes,
        "content_size_bytes": observation.content_size_bytes,
        "storage_representation": observation.storage_representation,
        "parser_version": observation.parser_version,
    }


def _digest_path(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _digest_gzip(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _sequence(value: object) -> Sequence[object]:
    if not isinstance(value, list | tuple):
        message = "lineage sequence field has the wrong type"
        raise TypeError(message)
    return value


def _object_mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, dict):
        message = "lineage mapping field has the wrong type"
        raise TypeError(message)
    return {str(key): item for key, item in value.items()}


def _string_mapping(value: object) -> Mapping[str, str]:
    return {str(key): str(item) for key, item in _object_mapping(value).items()}


def _optional_text(value: object) -> str | None:
    return None if value is None else str(value)


def record_recovery_events(
    writer: CatalogWriter,
    events: Iterable[RecoveryEvent],
    *,
    census_run_id: str | None = None,
) -> int:
    """Persist recovery events for the QA report and return how many were written."""
    now = utc_now()
    written = 0
    with transaction(writer.connection) as connection:
        for event in events:
            event_id = uuid.uuid4().hex
            connection.execute(
                "INSERT INTO census_recovery_events "
                "(event_id, scenario, observation_id, relative_path, action_taken, "
                "detail, occurred_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    event_id,
                    event.scenario,
                    event.observation_id,
                    event.relative_path,
                    event.action_taken,
                    event.detail,
                    now,
                ),
            )
            if census_run_id is not None:
                connection.execute(
                    "INSERT INTO census_recovery_states "
                    "(census_run_id, recovery_state_id, scenario, observation_id, "
                    "relative_path, resolution_state, action_taken, detail, "
                    "recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        census_run_id,
                        event_id,
                        event.scenario,
                        event.observation_id,
                        event.relative_path,
                        event.resolution_state,
                        event.action_taken,
                        event.detail,
                        now,
                    ),
                )
            written += 1
    return written


def _classify_rerun(row: sqlite3.Row, outcome: str) -> tuple[RecoveryEvent, ...]:
    """Record the rerun shape an outcome represents, for restart accounting."""
    mapping: dict[str, tuple[RecoveryScenario, str]] = {
        "unchanged_content": (
            "identical_content_rerun",
            "a rerun returned identical bytes; the stored object was reused and the "
            "retrieval was still recorded",
        ),
        "superseded": (
            "changed_content_rerun",
            "a rerun returned changed bytes; a new observation supersedes the prior one, "
            "which is preserved",
        ),
        "reused_snapshot": (
            "not_modified_reuse",
            "a conditional request reused a verified preserved snapshot",
        ),
        "quarantined": (
            "quarantined_response",
            "a malformed response was quarantined and preserved rather than parsed",
        ),
    }
    if outcome not in mapping:
        return ()
    scenario, detail = mapping[outcome]
    return (
        RecoveryEvent(
            scenario=scenario,
            action_taken="accounted",
            detail=detail,
            observation_id=str(row["observation_id"]),
            relative_path=(
                str(row["relative_storage_path"]) if row["relative_storage_path"] else None
            ),
        ),
    )


def _iter_raw_files(tree: DataTree) -> Iterable[Path]:
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings, tree.staging):
        if root.is_dir():
            for path in sorted(root.rglob("*")):
                if (
                    path.is_file()
                    and not path.name.endswith(".reason")
                    and not path.name.endswith(LINEAGE_SUFFIX)
                ):
                    yield path


def _iter_lineage_files(tree: DataTree) -> Iterable[Path]:
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if root.is_dir():
            yield from sorted(root.rglob(f"*{LINEAGE_SUFFIX}"))


def _observation_from_row(
    row: sqlite3.Row,
    reasons: Mapping[str, list[str]],
) -> SourceObservation:
    representation = row["storage_representation"]
    hops = tuple(json.loads(str(row["redirect_hops_json"] or "[]")))
    return SourceObservation(
        observation_id=str(row["observation_id"]),
        source_id=str(row["source_id"]),
        identity=str(row["request_identity"]),
        requested_url=str(row["requested_url"]),
        final_url=_text(row["final_url"]),
        purpose=str(row["purpose"]),
        retrieved_at_utc=str(row["retrieved_at_utc"]),
        outcome=str(row["outcome"]),  # type: ignore[arg-type]
        http_status=_number(row["http_status"]),
        headers=json.loads(str(row["headers_json"] or "{}")),
        etag=_text(row["etag"]),
        last_modified=_text(row["last_modified"]),
        validators_sent=json.loads(str(row["validators_sent_json"] or "{}")),
        declared_content_type=_text(row["declared_content_type"]),
        observed_content_kind=_text(row["observed_content_kind"]),
        content_encoding=_text(row["content_encoding"]),
        transport_sha256=_text(row["transport_sha256"]),
        stored_sha256=_text(row["stored_sha256"]),
        logical_sha256=_text(row["logical_sha256"]),
        content_sha256=_text(row["content_sha256"]),
        transport_size_bytes=_number(row["transport_size_bytes"]),
        content_size_bytes=_number(row["content_size_bytes"]),
        stored_size_bytes=_number(row["stored_size_bytes"]),
        storage_representation=(
            None if representation is None else str(representation)  # type: ignore[arg-type]
        ),
        relative_storage_path=_text(row["relative_storage_path"]),
        parser_version=_text(row["parser_version"]),
        supersedes_observation_id=_text(row["supersedes_observation_id"]),
        reused_observation_id=_text(row["reused_observation_id"]),
        redirects=tuple(json.loads(str(row["redirects_json"] or "[]"))),
        redirect_hops=hops,
        attempts=int(row["attempts"] or 0),
        reason_codes=tuple(reasons.get(str(row["observation_id"]), ())),
        detail=str(row["detail"] or ""),
    )


def _text(value: object) -> str | None:
    return None if value is None else str(value)


def _number(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int | str | bytes):
        return int(value)
    message = f"catalog integer column has unsupported value {value!r}"
    raise TypeError(message)


def _required_number(value: object) -> int:
    number = _number(value)
    if number is None:
        message = "required catalog or lineage integer is missing"
        raise ValueError(message)
    return number


_REPRESENTATIONS: Final[tuple[StorageRepresentation, ...]] = (
    "identical",
    "deterministic_gzip",
)
