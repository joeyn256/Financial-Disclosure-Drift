"""Durable persistence and recovery for census source observations.

Authority is explicit and single:

* **SQLite** rows in ``census_source_observations`` are the operational source of
  truth for what has been retrieved.
* **Immutable raw objects** on disk are the evidence those rows point at.
* **JSONL** is a deterministic audit projection. Normal writes append, while repair
  reconstructs it by durable atomic replacement from SQLite. A failed append never
  makes a committed observation appear unrecorded: stable identities and canonical
  payload bytes are reconciled instead of trusting the projected flag.

Each observation is written inside one transaction together with its reason codes
and archive-member lineage, so a crash leaves either the whole observation or none of
it. The projection flag is set in a second transaction only after the JSONL file and
required directory metadata have passed explicit ``fsync`` barriers, which is what
makes an interrupted append recoverable rather than lossy.

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
import os
import re
import sqlite3
import stat
import uuid
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Final, Literal, Protocol
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
    "ProjectionFaultHook",
    "ProjectionFaultPoint",
    "ProjectionValidation",
    "RecoveryEvent",
    "RecoveryReport",
    "RecoveryResolution",
    "RecoveryScenario",
    "load_observations",
    "rebuild_audit_projection",
    "reconcile",
    "record_recovery_events",
    "validate_audit_projection",
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
ProjectionFaultPoint = Literal[
    "after_append_durable_before_flag",
    "after_rebuild_temporary_durable_before_replace",
    "after_rebuild_replace_before_directory_fsync",
    "after_rebuild_directory_fsync_before_catalog_update",
]
ProjectionFaultHook = Callable[[ProjectionFaultPoint], None]
ProjectionCondition = Literal[
    "unsafe_projection_path",
    "missing_projection_file",
    "empty_file_with_projected_rows",
    "truncated_final_line",
    "malformed_json",
    "malformed_middle_line",
    "malformed_final_line",
    "duplicate_observation_identity",
    "missing_observation_identity",
    "unknown_observation_identity",
    "payload_hash_mismatch",
    "wrong_row_count",
    "incorrect_ordering",
    "valid_prefix_only",
    "extra_appended_garbage",
    "sqlite_projection_flag_stale",
    "unresolved_recovery_event",
    "projected_flags_claim_damaged_file",
]

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
_MAX_PROJECTION_LINE_BYTES: Final = 8 * 1024 * 1024
_PROJECTION_CONDITION_ORDER: Final[tuple[ProjectionCondition, ...]] = (
    "unsafe_projection_path",
    "missing_projection_file",
    "empty_file_with_projected_rows",
    "truncated_final_line",
    "malformed_json",
    "malformed_middle_line",
    "malformed_final_line",
    "duplicate_observation_identity",
    "missing_observation_identity",
    "unknown_observation_identity",
    "payload_hash_mismatch",
    "wrong_row_count",
    "incorrect_ordering",
    "valid_prefix_only",
    "extra_appended_garbage",
    "sqlite_projection_flag_stale",
    "unresolved_recovery_event",
    "projected_flags_claim_damaged_file",
)
_PROJECTION_TEMP_NAME = re.compile(r"^\.(?P<destination>.+)\.[0-9a-f]{32}\.tmp$")


class _Digest(Protocol):
    def update(self, data: bytes) -> object:
        """Add bytes to the digest."""


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
class ProjectionValidation:
    """Byte-for-byte comparison of the JSONL projection with SQLite authority."""

    projection_path: str
    expected_count: int
    observed_count: int | None
    expected_sha256: str
    observed_sha256: str | None
    conditions: tuple[ProjectionCondition, ...] = ()
    valid_prefix_count: int = 0

    @property
    def is_valid(self) -> bool:
        """Whether the projection and every SQLite projection flag agree."""
        return not self.conditions

    @property
    def requires_recovery(self) -> bool:
        """Whether startup must durably reconstruct or reconcile the projection."""
        return not self.is_valid

    @property
    def detail(self) -> str:
        """Stable machine-readable recovery evidence."""
        return json.dumps(
            {
                "conditions": list(self.conditions),
                "expected_count": self.expected_count,
                "expected_sha256": self.expected_sha256,
                "observed_count": self.observed_count,
                "observed_sha256": self.observed_sha256,
                "projection_path": self.projection_path,
                "valid_prefix_count": self.valid_prefix_count,
            },
            sort_keys=True,
        )


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    """Outcome of restart reconciliation."""

    events: tuple[RecoveryEvent, ...] = ()
    unprojected_observations: tuple[str, ...] = ()
    projection_validation: ProjectionValidation | None = None

    @property
    def is_clean(self) -> bool:
        """Whether nothing needed recovery."""
        return not (self.events or self.unprojected_observations)

    @property
    def projection_recovery_required(self) -> bool:
        """Whether the canonical audit projection needs durable recovery."""
        return bool(
            self.projection_validation is not None and self.projection_validation.requires_recovery
        )

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
    fault_hook: ProjectionFaultHook | None = field(default=None, repr=False)
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

        member_rows = self._archive_member_rows(observation, members)
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
            for member_row in member_rows:
                connection.execute(
                    "INSERT OR IGNORE INTO census_archive_members "
                    "(observation_id, member_index, member_name, member_sha256, "
                    "member_compressed_size_bytes, member_uncompressed_size_bytes, "
                    "archive_relative_path, archive_sha256, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        observation.observation_id,
                        *member_row,
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
        path = self.audit_path()
        observations = load_observations(self.writer.connection)
        validation = validate_audit_projection(self.writer.connection, path)
        if validation.is_valid:
            self._drop_projected_pending(observations)
            return 0, self.unprojected()

        expected_lines = tuple(_serialize_observation(item) for item in observations)
        can_append = _can_append_canonical_suffix(
            validation,
            self.writer.connection,
            observations,
        )
        if not can_append:
            rebuild_audit_projection(self.writer.connection, path)
            self._drop_projected_pending(observations)
            return 0, self.unprojected()

        path.parent.mkdir(parents=True, exist_ok=True)
        if validation.valid_prefix_count:
            _fsync_projection_and_directory(path)
            for observation in observations[: validation.valid_prefix_count]:
                self._mark_projected(observation.observation_id)
                self._drop_projected_pending((observation,))

        written = 0
        for observation, encoded in zip(
            observations[validation.valid_prefix_count :],
            expected_lines[validation.valid_prefix_count :],
            strict=True,
        ):
            _require_safe_projection_location(path)
            descriptor = _open_no_follow(
                path,
                os.O_APPEND | os.O_CREAT | os.O_WRONLY,
                mode=0o600,
            )
            with os.fdopen(descriptor, "ab") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            _fsync_directory(path.parent)
            if self.fault_hook is not None:
                self.fault_hook("after_append_durable_before_flag")
            self._mark_projected(observation.observation_id)
            self._drop_projected_pending((observation,))
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
            cursor = connection.execute(
                "UPDATE census_source_observations SET projected_to_audit = 1 "
                "WHERE observation_id = ?",
                (observation_id,),
            )
            if cursor.rowcount != 1:
                message = (
                    f"cannot mark unknown observation {observation_id} projected; "
                    "SQLite remains authoritative"
                )
                raise CatalogWriteError(message)

    def _drop_projected_pending(
        self,
        observations: Sequence[SourceObservation],
    ) -> None:
        projected = {item.observation_id for item in observations}
        self._pending_projection[:] = [
            item for item in self._pending_projection if item.observation_id not in projected
        ]

    def _archive_member_rows(
        self,
        observation: SourceObservation,
        members: Sequence[ArchiveMember],
    ) -> tuple[tuple[object, ...], ...]:
        explicit = tuple(
            sorted(
                (
                    lineage["member_index"],
                    lineage["member_name"],
                    lineage["member_sha256"],
                    lineage["member_compressed_size_bytes"],
                    lineage["member_uncompressed_size_bytes"],
                    lineage["archive_relative_path"],
                    lineage["archive_sha256"],
                )
                for lineage in (member.lineage() for member in members)
            )
        )
        reused = observation.reused_observation_id
        if reused is None:
            return explicit
        prior = tuple(
            tuple(row)
            for row in self.writer.connection.execute(
                "SELECT member_index, member_name, member_sha256, "
                "member_compressed_size_bytes, member_uncompressed_size_bytes, "
                "archive_relative_path, archive_sha256 "
                "FROM census_archive_members WHERE observation_id = ? "
                "ORDER BY member_index, member_name",
                (reused,),
            ).fetchall()
        )
        spec = require_registered(observation.source_id)
        if spec.expected_content == "zip" and not prior:
            message = (
                f"archive reuse {observation.observation_id} cannot be completed because "
                f"object owner {reused} has no preserved archive-member lineage"
            )
            raise CatalogWriteError(message)
        if spec.expected_content == "zip" and any(
            row[5] != observation.relative_storage_path or row[6] != observation.logical_sha256
            for row in prior
        ):
            message = (
                f"archive-member lineage for reused observation {reused} does not "
                "identify the verified shared archive object"
            )
            raise CatalogWriteError(message)
        if explicit and explicit != prior:
            message = (
                f"archive-member lineage for reused observation {reused} does not "
                "match the prior immutable evidence"
            )
            raise CatalogWriteError(message)
        return prior

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
    *,
    fault_hook: ProjectionFaultHook | None = None,
    census_run_id: str | None = None,
) -> int:
    """Atomically reconstruct the JSONL projection and return the row count.

    The replacement becomes authoritative as a projection only after its temporary
    file and destination-directory entry are durable. SQLite flags and any blocked
    projection-recovery event are updated in one transaction *after* those barriers.
    A fault before then leaves immutable observations untouched and recovery blocked.
    """
    initial_validation = validate_audit_projection(connection, destination)
    if initial_validation.requires_recovery:
        _persist_projection_recovery_detection(connection, initial_validation)
    observations = load_observations(connection)
    _require_safe_projection_location(destination, allow_symlink_destination=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _require_safe_projection_location(destination, allow_symlink_destination=True)
    temporary = destination.parent / f".{destination.name}.{uuid.uuid4().hex}.tmp"
    digest = hashlib.sha256()
    expected_size = 0
    with temporary.open("xb") as handle:
        for observation in observations:
            encoded = _serialize_observation(observation)
            handle.write(encoded)
            digest.update(encoded)
            expected_size += len(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    if fault_hook is not None:
        fault_hook("after_rebuild_temporary_durable_before_replace")
    temporary.replace(destination)
    if fault_hook is not None:
        fault_hook("after_rebuild_replace_before_directory_fsync")
    _fsync_directory(destination.parent)

    now = utc_now()
    path_identity = _projection_path_identity(destination)
    projection_sha256 = digest.hexdigest()
    stored_sha256, stored_size = _digest_projection_path(destination)
    if stored_sha256 != projection_sha256 or stored_size != expected_size:
        message = (
            "atomically replaced audit projection does not match the durable temporary "
            "file; SQLite projection status remains unchanged"
        )
        raise CatalogWriteError(message)
    _remove_stale_projection_temporaries(destination)
    if fault_hook is not None:
        fault_hook("after_rebuild_directory_fsync_before_catalog_update")
    with transaction(connection) as writable:
        writable.execute("UPDATE census_source_observations SET projected_to_audit = 1")
        if _table_exists(writable, "census_projection_recovery_events"):
            writable.execute(
                "UPDATE census_projection_recovery_events "
                "SET projection_sha256 = ?, resolution_state = 'resolved', "
                "resolved_at_utc = ?, detail = detail || ? "
                "WHERE projection_path = ? AND resolution_state = 'blocked'",
                (
                    projection_sha256,
                    now,
                    "; deterministic atomic rebuild completed and parent directory fsynced",
                    path_identity,
                ),
            )
        if census_run_id is not None and _table_exists(writable, "census_recovery_states"):
            writable.execute(
                "UPDATE census_recovery_states SET resolution_state = 'resolved', "
                "action_taken = 'projection_rebuilt', "
                "detail = detail || '; projection rebuilt from authoritative catalog' "
                "WHERE census_run_id = ? AND "
                "scenario = 'audit_projection_interrupted' AND "
                "resolution_state = 'blocked'",
                (census_run_id,),
            )
    return len(observations)


def validate_audit_projection(
    connection: sqlite3.Connection,
    destination: Path,
) -> ProjectionValidation:
    """Validate the complete JSONL projection against immutable SQLite rows.

    Validation never trusts ``projected_to_audit``. Stable observation identifiers,
    deterministic line bytes, canonical ordering, and the full-file digest are checked
    independently. The flags are then compared as an additional reconciliation signal.
    """
    observations = load_observations(connection)
    expected_lines = tuple(_serialize_observation(item) for item in observations)
    expected_ids = tuple(item.observation_id for item in observations)
    expected_by_id = dict(zip(expected_ids, expected_lines, strict=True))
    expected_sha256 = _digest_chunks(expected_lines)
    path_identity = _projection_path_identity(destination)
    flags = {
        str(row["observation_id"]): int(row["projected_to_audit"])
        for row in connection.execute(
            "SELECT observation_id, projected_to_audit FROM census_source_observations"
        ).fetchall()
    }
    unsafe_detail = _projection_location_failure(destination)
    if unsafe_detail is not None:
        unsafe_conditions: set[ProjectionCondition] = {"unsafe_projection_path"}
        if expected_ids and all(flags[item] == 1 for item in expected_ids):
            unsafe_conditions.add("projected_flags_claim_damaged_file")
        if _has_unresolved_projection_recovery(connection, path_identity):
            unsafe_conditions.add("unresolved_recovery_event")
        return ProjectionValidation(
            projection_path=path_identity,
            expected_count=len(expected_ids),
            observed_count=None,
            expected_sha256=expected_sha256,
            observed_sha256=None,
            conditions=_ordered_projection_conditions(unsafe_conditions),
        )
    if not destination.is_file():
        missing_conditions: set[ProjectionCondition] = {"missing_projection_file"}
        if expected_ids and all(flags[item] == 1 for item in expected_ids):
            missing_conditions.add("projected_flags_claim_damaged_file")
        if _has_unresolved_projection_recovery(connection, path_identity):
            missing_conditions.add("unresolved_recovery_event")
        return ProjectionValidation(
            projection_path=path_identity,
            expected_count=len(expected_ids),
            observed_count=None,
            expected_sha256=expected_sha256,
            observed_sha256=None,
            conditions=_ordered_projection_conditions(missing_conditions),
        )

    conditions: set[ProjectionCondition] = set()
    observed_digest = hashlib.sha256()
    raw_lines: list[bytes] = []
    parsed_ids: list[str] = []
    malformed_lines: list[int] = []
    line_limit = max(
        _MAX_PROJECTION_LINE_BYTES,
        max((len(line) for line in expected_lines), default=0),
    )
    descriptor = _open_no_follow(destination, os.O_RDONLY)
    with os.fdopen(descriptor, "rb") as handle:
        while True:
            raw_line = handle.readline(line_limit + 1)
            if not raw_line:
                break
            raw_lines.append(raw_line)
            observed_digest.update(raw_line)
            line_number = len(raw_lines)
            if len(raw_line) > line_limit:
                conditions.add("extra_appended_garbage")
                malformed_lines.append(line_number)
                _consume_projection_remainder(handle, observed_digest)
                break
            if not raw_line.endswith(b"\n"):
                conditions.add("truncated_final_line")
            try:
                payload = json.loads(raw_line)
            except (UnicodeDecodeError, ValueError, RecursionError):
                conditions.add("malformed_json")
                malformed_lines.append(line_number)
                continue
            if not isinstance(payload, dict):
                conditions.add("malformed_json")
                malformed_lines.append(line_number)
                continue
            observation_id = payload.get("observation_id")
            if not isinstance(observation_id, str) or not observation_id:
                conditions.add("missing_observation_identity")
                continue
            parsed_ids.append(observation_id)
            expected_line = expected_by_id.get(observation_id)
            if expected_line is None:
                conditions.add("unknown_observation_identity")
            elif raw_line != expected_line:
                conditions.add("payload_hash_mismatch")

    observed_count = len(raw_lines)
    if not raw_lines and expected_ids and any(flags[item] == 1 for item in expected_ids):
        conditions.add("empty_file_with_projected_rows")
    if malformed_lines:
        final_line_number = len(raw_lines)
        if final_line_number in malformed_lines:
            conditions.add("malformed_final_line")
        if any(line_number < final_line_number for line_number in malformed_lines):
            conditions.add("malformed_middle_line")
    if len(set(parsed_ids)) != len(parsed_ids):
        conditions.add("duplicate_observation_identity")
    if observed_count != len(expected_ids):
        conditions.add("wrong_row_count")
    missing_expected = set(expected_ids).difference(parsed_ids)
    if missing_expected:
        conditions.add("missing_observation_identity")
    if (
        len(parsed_ids) == len(expected_ids)
        and set(parsed_ids) == set(expected_ids)
        and tuple(parsed_ids) != expected_ids
    ):
        conditions.add("incorrect_ordering")

    valid_prefix_count = 0
    for raw_line, expected_line in zip(raw_lines, expected_lines, strict=False):
        if raw_line != expected_line:
            break
        valid_prefix_count += 1
    if valid_prefix_count == observed_count and observed_count < len(expected_ids):
        conditions.add("valid_prefix_only")
    if observed_count > len(expected_ids) or (
        malformed_lines and min(malformed_lines) > len(expected_ids)
    ):
        conditions.add("extra_appended_garbage")

    byte_conditions = set(conditions)
    if not byte_conditions and any(flags[item] == 0 for item in expected_ids):
        conditions.add("sqlite_projection_flag_stale")
    elif byte_conditions and expected_ids and all(flags[item] == 1 for item in expected_ids):
        conditions.add("projected_flags_claim_damaged_file")
    if _has_unresolved_projection_recovery(connection, path_identity):
        conditions.add("unresolved_recovery_event")

    return ProjectionValidation(
        projection_path=path_identity,
        expected_count=len(expected_ids),
        observed_count=observed_count,
        expected_sha256=expected_sha256,
        observed_sha256=observed_digest.hexdigest(),
        conditions=_ordered_projection_conditions(conditions),
        valid_prefix_count=valid_prefix_count,
    )


def _serialize_observation(observation: SourceObservation) -> bytes:
    """Return the one canonical UTF-8 JSONL record for an observation."""
    return (
        json.dumps(
            observation.as_record(),
            ensure_ascii=True,
            allow_nan=False,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _digest_chunks(chunks: Iterable[bytes]) -> str:
    digest = hashlib.sha256()
    for chunk in chunks:
        digest.update(chunk)
    return digest.hexdigest()


def _ordered_projection_conditions(
    conditions: set[ProjectionCondition],
) -> tuple[ProjectionCondition, ...]:
    return tuple(condition for condition in _PROJECTION_CONDITION_ORDER if condition in conditions)


def _consume_projection_remainder(handle: BinaryIO, digest: _Digest) -> None:
    """Hash the rest of an oversized damaged projection without retaining it."""
    while chunk := handle.read(1024 * 1024):
        digest.update(chunk)


def _projection_location_failure(
    path: Path,
    *,
    allow_symlink_destination: bool = False,
) -> str | None:
    """Return why the managed audit path is unsafe without following its links.

    The configured data root may itself be reached through a machine-local alias
    (macOS ``/tmp`` is a symlink to ``/private/tmp``). That is outside the managed
    audit subtree. The components this module owns are ``audit``, ``sec``, and the
    final projection entry, so only those components are rejected when linked.
    """
    managed_parents = [path.parent]
    if path.parent.name == "sec" and path.parent.parent.name == "audit":
        managed_parents.append(path.parent.parent)
    for parent in managed_parents:
        try:
            metadata = parent.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            return f"projection parent {parent} cannot be inspected: {exc}"
        if stat.S_ISLNK(metadata.st_mode):
            return f"projection parent {parent} is a symbolic link"

    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        return f"projection path {path} cannot be inspected: {exc}"
    if stat.S_ISLNK(metadata.st_mode):
        return None if allow_symlink_destination else "projection path is a symbolic link"
    if not stat.S_ISREG(metadata.st_mode):
        return "projection path exists but is not a regular file"
    return None


def _require_safe_projection_location(
    path: Path,
    *,
    allow_symlink_destination: bool = False,
) -> None:
    failure = _projection_location_failure(
        path,
        allow_symlink_destination=allow_symlink_destination,
    )
    if failure is not None:
        message = f"{failure}; refusing unsafe projection filesystem access"
        raise CatalogWriteError(message)


def _open_no_follow(path: Path, flags: int, *, mode: int = 0o600) -> int:
    """Open one safe projection file without following its final component."""
    _require_safe_projection_location(path)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        return os.open(path, flags, mode)
    except OSError as exc:
        message = f"cannot safely open audit projection {path}: {exc}"
        raise CatalogWriteError(message) from exc


def _fsync_projection_and_directory(path: Path) -> None:
    descriptor = _open_no_follow(path, os.O_RDONLY)
    with os.fdopen(descriptor, "rb") as handle:
        os.fsync(handle.fileno())
    _fsync_directory(path.parent)


def _fsync_directory(directory: Path) -> None:
    parent_failure = _projection_location_failure(directory / ".projection-safety-check")
    if parent_failure is not None:
        message = f"{parent_failure}; cannot durably persist the projection directory"
        raise CatalogWriteError(message)
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(directory, flags)
    except OSError as exc:
        message = f"cannot open projection directory for durability barrier {directory}: {exc}"
        raise CatalogWriteError(message) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        message = f"cannot fsync projection directory {directory}: {exc}"
        raise CatalogWriteError(message) from exc
    finally:
        os.close(descriptor)


def _digest_projection_path(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    descriptor = _open_no_follow(path, os.O_RDONLY)
    with os.fdopen(descriptor, "rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def _remove_stale_projection_temporaries(destination: Path) -> int:
    """Remove only this projection's strictly named derived rebuild artifacts."""
    _require_safe_projection_location(destination, allow_symlink_destination=True)
    removed = 0
    try:
        candidates = tuple(destination.parent.iterdir())
    except OSError as exc:
        message = f"cannot inspect projection rebuild artifacts in {destination.parent}: {exc}"
        raise CatalogWriteError(message) from exc
    for candidate in sorted(candidates):
        match = _PROJECTION_TEMP_NAME.fullmatch(candidate.name)
        if match is None or match.group("destination") != destination.name:
            continue
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            continue
        if not (stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)):
            message = (
                f"projection rebuild artifact {candidate.name} is not a regular file "
                "or symlink; refusing ambiguous cleanup"
            )
            raise CatalogWriteError(message)
        try:
            candidate.unlink()
        except OSError as exc:
            message = f"cannot remove stale projection rebuild artifact {candidate}: {exc}"
            raise CatalogWriteError(message) from exc
        removed += 1
    if removed:
        _fsync_directory(destination.parent)
    return removed


def _projection_path_identity(destination: Path) -> str:
    parts = destination.parts
    for index in range(len(parts) - 1):
        if parts[index : index + 2] == ("audit", "sec"):
            return Path(*parts[index:]).as_posix()
    return destination.name


def _can_append_canonical_suffix(
    validation: ProjectionValidation,
    connection: sqlite3.Connection,
    observations: Sequence[SourceObservation],
) -> bool:
    """Return whether append/replay can proceed without replacing damaged bytes."""
    if not observations and "missing_projection_file" in validation.conditions:
        return False
    append_only_conditions: set[ProjectionCondition] = {
        "missing_projection_file",
        "missing_observation_identity",
        "wrong_row_count",
        "valid_prefix_only",
        "sqlite_projection_flag_stale",
    }
    if not set(validation.conditions).issubset(append_only_conditions):
        return False
    if "missing_projection_file" not in validation.conditions and validation.valid_prefix_count != (
        validation.observed_count or 0
    ):
        return False
    tail_ids = tuple(item.observation_id for item in observations[validation.valid_prefix_count :])
    if not tail_ids:
        return True
    already_projected = {
        str(row["observation_id"])
        for row in connection.execute(
            "SELECT observation_id FROM census_source_observations WHERE projected_to_audit = 1"
        ).fetchall()
    }
    return already_projected.isdisjoint(tail_ids)


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _has_unresolved_projection_recovery(
    connection: sqlite3.Connection,
    projection_path: str,
) -> bool:
    if not _table_exists(connection, "census_projection_recovery_events"):
        return False
    row = connection.execute(
        "SELECT 1 FROM census_projection_recovery_events "
        "WHERE projection_path = ? AND resolution_state = 'blocked' LIMIT 1",
        (projection_path,),
    ).fetchone()
    return row is not None


def _persist_projection_recovery_detection(
    connection: sqlite3.Connection,
    validation: ProjectionValidation,
) -> None:
    """Persist one unresolved projection incident before attempting reconstruction."""
    if not _table_exists(connection, "census_projection_recovery_events"):
        return
    existing = connection.execute(
        "SELECT event_id FROM census_projection_recovery_events "
        "WHERE projection_path = ? AND resolution_state = 'blocked' "
        "ORDER BY detected_at_utc DESC LIMIT 1",
        (validation.projection_path,),
    ).fetchone()
    if existing is not None:
        return
    with transaction(connection) as writable:
        writable.execute(
            "INSERT INTO census_projection_recovery_events "
            "(event_id, detected_condition, projection_path, expected_count, "
            "observed_count, rebuild_identity, projection_sha256, resolution_state, "
            "release_blocking_before_resolution, detected_at_utc, resolved_at_utc, "
            "detail) VALUES (?, ?, ?, ?, ?, ?, NULL, 'blocked', 1, ?, NULL, ?)",
            (
                uuid.uuid4().hex,
                ",".join(validation.conditions),
                validation.projection_path,
                validation.expected_count,
                validation.observed_count,
                uuid.uuid4().hex,
                utc_now(),
                validation.detail,
            ),
        )


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
            path, failure = _safe_catalog_object_path(tree, str(relative))
            if failure is None and path is not None:
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

    flag_unprojected = tuple(
        str(row["observation_id"])
        for row in connection.execute(
            "SELECT observation_id FROM census_source_observations "
            "WHERE projected_to_audit = 0 ORDER BY observation_id"
        ).fetchall()
    )
    projection_path = tree.audit / "census_source_observations.jsonl"
    projection_validation = validate_audit_projection(connection, projection_path)
    if projection_validation.requires_recovery:
        expected_ids = tuple(
            str(row["observation_id"])
            for row in connection.execute(
                "SELECT observation_id FROM census_source_observations "
                "ORDER BY retrieved_at_utc, recorded_at_utc, observation_id"
            ).fetchall()
        )
        unprojected = expected_ids or flag_unprojected
        _persist_projection_recovery_detection(connection, projection_validation)
        events.append(
            RecoveryEvent(
                scenario="audit_projection_interrupted",
                action_taken="projection_rebuild_required",
                detail=projection_validation.detail,
                relative_path=projection_validation.projection_path,
                resolution_state="blocked",
            )
        )
    else:
        unprojected = flag_unprojected
    return RecoveryReport(
        events=tuple(events),
        unprojected_observations=unprojected,
        projection_validation=projection_validation,
    )


def _safe_catalog_object_path(tree: DataTree, relative_path: str) -> tuple[Path | None, str | None]:
    """Resolve recorded evidence without traversing outside managed raw storage."""
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
        return None, "catalog observation has an unsafe or non-raw relative storage path"
    candidate = tree.data_root / relative
    current = tree.data_root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            return None, "catalog observation path traverses a symbolic link"
    try:
        root = tree.data_root.resolve(strict=True)
        candidate.resolve(strict=False).relative_to(root)
    except (OSError, ValueError):
        return None, "catalog observation path escapes the configured data root"
    return candidate, None


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
