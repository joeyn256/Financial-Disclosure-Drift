"""The single logical catalog writer (Decision 009 section 8).

All database writes are serialized through :class:`CatalogWriter`. Retrieval and
parsing workers may produce staging artifacts and completion messages, but they
never open a writing connection. A second writer fails loudly rather than
corrupting state.
"""

from __future__ import annotations

import importlib
import json
import os
import sqlite3
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Any, Final

from disclosure_drift.cohorts import COHORT_ORDER, FROZEN_COHORTS
from disclosure_drift.errors import CatalogWriteError, SingleWriterViolationError
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.storage.sqlite import (
    IntegrityReport,
    apply_migrations,
    connect,
    integrity_report,
    transaction,
    utc_now,
)

try:
    fcntl: Any = importlib.import_module("fcntl")
except ImportError:  # pragma: no cover - supported CI and production platforms are Unix
    fcntl = None

__all__ = [
    "DEFAULT_LEASE_SECONDS",
    "ELIGIBLE_FORM_TYPES",
    "CatalogWriter",
    "WriterLease",
    "read_only_connection",
    "strictly_read_only_connection",
]

DEFAULT_LEASE_SECONDS: Final = 900
_LEASE_FILENAME: Final = "catalog_writer.lease"

ELIGIBLE_FORM_TYPES: Final[tuple[tuple[str, bool, bool, str], ...]] = (
    ("10-K", False, True, "Original annual report."),
    ("10-K/A", True, True, "Amendment to an annual report."),
    ("10-KT", False, True, "Original transition-period annual report."),
    ("10-KT/A", True, True, "Amendment to a transition-period annual report."),
    ("20-F", False, False, "Foreign private issuer annual report; control evidence only."),
    ("20-F/A", True, False, "Amendment to a foreign private issuer annual report."),
    ("40-F", False, False, "Canadian MJDS annual report; control evidence only."),
    ("40-F/A", True, False, "Amendment to a Canadian MJDS annual report."),
)
_DECISION_007: Final = "Docs/Decisions/decision_007_sec_universe.md"
_DECISION_010: Final = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"


def _host_fingerprint() -> str:
    """Return a coarse host identifier without importing any network module."""
    uname = getattr(os, "uname", None)
    return uname().nodename if uname is not None else "unknown-host"


@dataclass(frozen=True, slots=True)
class WriterLease:
    """A held writer lease."""

    lease_id: str
    path: Path
    writer_pid: int
    acquired_at_utc: str
    expires_at_utc: str


def read_only_connection(database_path: Path) -> AbstractContextManager[sqlite3.Connection]:
    """Return a read-only connection context manager for non-writer callers."""
    return connect(database_path, writer=False)


def strictly_read_only_connection(
    database_path: Path,
) -> AbstractContextManager[sqlite3.Connection]:
    """Return a connection whose operating-system handle cannot write at all.

    :func:`read_only_connection` is read-only by convention: it takes no writer lease and its
    callers issue no mutating statement. That is not enough for a caller that must leave the
    database file byte-identical, because SQLite writes on its own account — closing the last
    read-write handle to a WAL-mode database checkpoints the pending log into the main file.
    ``SQLITE_OPEN_READONLY`` removes that capability rather than trusting nobody exercises it.
    """
    return connect(database_path, read_only=True)


class CatalogWriter:
    """Serialized writer for the operational catalog."""

    def __init__(
        self,
        database_path: Path,
        lock_directory: Path,
        *,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ) -> None:
        self._database_path = database_path
        self._lock_path = lock_directory / _LEASE_FILENAME
        self._lease_seconds = lease_seconds
        self._lease: WriterLease | None = None
        self._lock_descriptor: int | None = None
        self._connection: sqlite3.Connection | None = None
        self._context: AbstractContextManager[sqlite3.Connection] | None = None

    # -- lifecycle --------------------------------------------------------- #
    def __enter__(self) -> CatalogWriter:
        """Acquire the writer lease and open the writing connection."""
        self._lease = self._acquire_lease()
        try:
            self._context = connect(self._database_path, writer=True)
            self._connection = self._context.__enter__()
        except BaseException:
            self._context = None
            self._connection = None
            self._release_lease()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the connection and release the lease."""
        if self._context is not None:
            self._context.__exit__(exc_type, exc, traceback)
        self._context = None
        self._connection = None
        self._release_lease()

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the open writing connection."""
        if self._connection is None:
            message = "catalog writer is not open; use it as a context manager"
            raise CatalogWriteError(message)
        return self._connection

    @property
    def lease(self) -> WriterLease:
        """Return the held lease."""
        if self._lease is None:
            message = "catalog writer holds no lease"
            raise CatalogWriteError(message)
        return self._lease

    def _acquire_lease(self) -> WriterLease:
        if fcntl is None:
            message = (
                "catalog writes require operating-system advisory locking, but fcntl.flock "
                "is unavailable on this platform; refusing to fall back to timestamp ownership"
            )
            raise CatalogWriteError(message)
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        now = datetime.now(UTC)
        expires = now + timedelta(seconds=self._lease_seconds)
        lease_id = uuid.uuid4().hex
        writer_pid = os.getpid()
        acquired_at_utc = now.isoformat().replace("+00:00", "Z")
        expires_at_utc = expires.isoformat().replace("+00:00", "Z")
        payload: dict[str, object] = {
            "lease_id": lease_id,
            "writer_pid": writer_pid,
            "host_fingerprint": _host_fingerprint(),
            "acquired_at_utc": acquired_at_utc,
            "expires_at_utc": expires_at_utc,
            "state": "held",
        }
        try:
            descriptor = os.open(self._lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        except OSError as exc:
            message = f"unable to open catalog writer lock {self._lock_path}: {exc}"
            raise CatalogWriteError(message) from exc
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            existing = self._read_lease_file()
            os.close(descriptor)
            message = (
                "another catalog writer holds the process-lifetime advisory lock "
                f"(pid {(existing or {}).get('writer_pid', 'unknown')}, "
                f"acquired {(existing or {}).get('acquired_at_utc', 'unknown')})\n"
                "Fix: wait for it to finish. Elapsed time never permits takeover."
            )
            raise SingleWriterViolationError(message) from None
        except OSError as exc:
            os.close(descriptor)
            message = f"unable to acquire catalog writer advisory lock: {exc}"
            raise CatalogWriteError(message) from exc

        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        try:
            os.ftruncate(descriptor, 0)
            os.lseek(descriptor, 0, os.SEEK_SET)
            os.write(descriptor, encoded)
            os.fsync(descriptor)
        except BaseException:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
            raise
        self._lock_descriptor = descriptor
        return WriterLease(
            lease_id=lease_id,
            path=self._lock_path,
            writer_pid=writer_pid,
            acquired_at_utc=acquired_at_utc,
            expires_at_utc=expires_at_utc,
        )

    def _read_lease_file(self) -> Mapping[str, Any] | None:
        try:
            loaded = json.loads(self._lock_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return loaded if isinstance(loaded, dict) else None

    def _release_lease(self) -> None:
        descriptor = self._lock_descriptor
        lease = self._lease
        if descriptor is None or lease is None:
            self._lock_descriptor = None
            self._lease = None
            return
        if fcntl is None:  # pragma: no cover - acquisition already fails closed
            os.close(descriptor)
            self._lock_descriptor = None
            self._lease = None
            return
        try:
            persisted = self._read_locked_metadata(descriptor)
            if persisted.get("lease_id") == lease.lease_id:
                persisted["state"] = "released"
                persisted["released_at_utc"] = utc_now()
                encoded = json.dumps(persisted, sort_keys=True).encode("utf-8")
                os.ftruncate(descriptor, 0)
                os.lseek(descriptor, 0, os.SEEK_SET)
                os.write(descriptor, encoded)
                os.fsync(descriptor)
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
            self._lock_descriptor = None
        self._lease = None

    @staticmethod
    def _read_locked_metadata(descriptor: int) -> dict[str, Any]:
        try:
            os.lseek(descriptor, 0, os.SEEK_SET)
            raw = os.read(descriptor, 64 * 1024)
            loaded = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, ValueError):
            return {}
        return dict(loaded) if isinstance(loaded, dict) else {}

    # -- schema and seeds --------------------------------------------------- #
    def migrate(self) -> tuple[str, ...]:
        """Apply pending migrations and return their names.

        :func:`apply_migrations` commits each schema script and its immutable
        name/checksum provenance row atomically. It also verifies the applied
        chain before and after pending migrations.
        """
        applied = apply_migrations(self.connection)
        return tuple(migration.name for migration in applied)

    def seed_reference_data(self) -> Mapping[str, int]:
        """Seed the reference tables that come from already-frozen definitions.

        ``reference_sic_codes`` is deliberately **not** seeded: the official SIC
        reference data is loaded in Stage M2.2 from an approved SEC snapshot.
        """
        now = utc_now()
        counts = {"form_types": 0, "reason_codes": 0, "cohorts": 0, "policies": 0}
        with transaction(self.connection) as connection:
            for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
                connection.execute(
                    "INSERT OR REPLACE INTO reference_form_types "
                    "(form_type, is_amendment, is_eligible_universe, description, decision_record)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (form_type, int(is_amendment), int(eligible), description, _DECISION_007),
                )
                counts["form_types"] += 1

            for code in REASON_CODES.values():
                connection.execute(
                    "INSERT OR REPLACE INTO reference_reason_codes "
                    "(reason_code, category, description, blocks_release, "
                    "requires_manual_review, decision_record) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        code.code,
                        code.category,
                        code.description,
                        int(code.blocks_release),
                        int(code.requires_manual_review),
                        code.decision_reference,
                    ),
                )
                counts["reason_codes"] += 1

            for name in COHORT_ORDER:
                window = FROZEN_COHORTS[name]
                connection.execute(
                    "INSERT OR REPLACE INTO reference_cohort_definitions "
                    "(cohort_name, window_start, window_end, role, assignment_date_source, "
                    "decision_record) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        window.name,
                        window.start.isoformat(),
                        window.end.isoformat(),
                        window.role,
                        "official_sec_filing_date",
                        _DECISION_010,
                    ),
                )
                counts["cohorts"] += 1

            for key, version, record in (
                ("universe", "1.0", _DECISION_007),
                ("filing_inventory", "1.0", "Docs/Decisions/decision_008_filing_inventory.md"),
                ("raw_governance", "1.0", "Docs/Decisions/decision_009_raw_data_governance.md"),
                ("temporal", "1.0", _DECISION_010),
            ):
                connection.execute(
                    "INSERT OR REPLACE INTO reference_policy_versions "
                    "(policy_key, policy_version, decision_record, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?)",
                    (key, version, record, now),
                )
                counts["policies"] += 1
        return counts

    # -- write helpers ------------------------------------------------------ #
    @contextmanager
    def batch(self) -> Iterator[sqlite3.Connection]:
        """Run several writes inside one explicit transaction."""
        with transaction(self.connection) as connection:
            yield connection

    def insert(self, table: str, values: Mapping[str, Any]) -> None:
        """Insert one row inside the caller's transaction."""
        columns = ", ".join(values)
        placeholders = ", ".join("?" for _ in values)
        statement = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"  # noqa: S608
        self.connection.execute(statement, tuple(values.values()))

    def record_reasons(self, accession_plain: str, reason_codes: Sequence[str]) -> int:
        """Attach reason codes to an accession, ignoring duplicates."""
        now = utc_now()
        written = 0
        for code in reason_codes:
            if code not in REASON_CODES:
                message = f"unregistered reason code {code!r}"
                raise CatalogWriteError(message)
            self.connection.execute(
                "INSERT OR IGNORE INTO inventory_reasons "
                "(accession_plain, reason_code, detail, recorded_at_utc) VALUES (?, ?, ?, ?)",
                (accession_plain, code, None, now),
            )
            written += 1
        return written

    def record_event(self, kind: str, payload: Mapping[str, Any], accession: str | None) -> str:
        """Append an inventory audit event."""
        event_id = uuid.uuid4().hex
        self.connection.execute(
            "INSERT INTO audit_inventory_events "
            "(event_id, accession_plain, event_kind, event_payload_json, occurred_at_utc) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_id, accession, kind, json.dumps(payload, sort_keys=True), utc_now()),
        )
        return event_id

    def integrity(self) -> IntegrityReport:
        """Run the three SQLite integrity gates."""
        return integrity_report(self.connection)
