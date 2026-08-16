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
import re
import sqlite3
import stat
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
    "LEASE_FILENAME",
    "LEASE_STATE_HELD",
    "LEASE_STATE_RELEASED",
    "STALE_LEASE_RECONCILIATION_REASON",
    "CatalogWriter",
    "LeaseFormatError",
    "PersistedLease",
    "WriterLease",
    "exclusive_lease_lock",
    "host_fingerprint",
    "lease_path",
    "read_only_connection",
    "read_persisted_lease",
    "reconciled_lease_document",
    "rewrite_locked_lease",
    "strictly_read_only_connection",
    "writer_process_is_alive",
]

DEFAULT_LEASE_SECONDS: Final = 900

#: The one lease filename. Public because the Decision 103 R3 stale-writer reconciliation must
#: name the same file this class writes, and a second literal would be a second contract.
LEASE_FILENAME: Final = "catalog_writer.lease"
_LEASE_FILENAME: Final = LEASE_FILENAME

#: The two lifecycle states this module has ever written. There is no third: accepted
#: Decision 103 R4 reconciles a stale lease **into** ``released`` and distinguishes it by
#: provenance fields, rather than by inventing a state vocabulary no existing reader knows.
LEASE_STATE_HELD: Final = "held"
LEASE_STATE_RELEASED: Final = "released"

#: The Decision 103 R4 provenance marker. Its presence is what separates an owner-authorized
#: stale-writer reconciliation from an ordinary holder release, which records
#: ``released_at_utc`` instead and never carries this field.
STALE_LEASE_RECONCILIATION_REASON: Final = "owner_authorized_stale_writer_recovery"

#: Required keys of a structurally valid lease document, and the optional lifecycle keys the
#: two release paths may add. Anything else is refused: a lease carrying an unknown key has
#: been written by something that is not this module, and a recovery must not act on it.
_LEASE_REQUIRED_KEYS: Final[frozenset[str]] = frozenset(
    {"lease_id", "writer_pid", "host_fingerprint", "acquired_at_utc", "expires_at_utc", "state"}
)
_LEASE_OPTIONAL_KEYS: Final[frozenset[str]] = frozenset(
    {"released_at_utc", "reconciliation_reason", "reconciled_at_utc", "reconciled_prior_state"}
)

_LEASE_TIMESTAMP_PATTERN: Final = re.compile(r"\A\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\Z")

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


def host_fingerprint() -> str:
    """The current host's coarse identifier, as a lease records it.

    Public so a stale-lease reconciliation can compare a persisted lease's recorded host
    against *this* host using the same function that wrote it. A recovery that compared
    against a separately derived identifier could pass while the two definitions drifted.
    """
    return _host_fingerprint()


def lease_path(lock_directory: Path) -> Path:
    """The lease file :class:`CatalogWriter` uses for ``lock_directory``."""
    return lock_directory / LEASE_FILENAME


def writer_process_is_alive(pid: int) -> bool:
    """Whether ``pid`` names a live process on this host.

    ``os.kill(pid, 0)`` sends no signal; it asks the kernel whether the process exists and
    whether this user could signal it. ``PermissionError`` therefore means **alive and owned
    by someone else**, which is a live writer, not an absent one. Anything the platform will
    not answer is reported as alive, so an unanswerable question never authorizes a takeover.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:  # pragma: no cover - defensive; no supported platform reaches this
        return True
    return True


class LeaseFormatError(CatalogWriteError):
    """A persisted lease document is absent, unreadable, or not structurally valid.

    Its own class because the Decision 103 R3 recovery must distinguish "this lease is not
    something I may act on" from "this lease is valid and ineligible". Both refuse; only the
    second is a finding about the writer.
    """


@dataclass(frozen=True, slots=True)
class WriterLease:
    """A held writer lease."""

    lease_id: str
    path: Path
    writer_pid: int
    acquired_at_utc: str
    expires_at_utc: str


@dataclass(frozen=True, slots=True)
class PersistedLease:
    """One structurally valid persisted lease document, as read from disk.

    ``document`` is the exact parsed mapping, kept so a reconciliation rewrites the lease it
    actually read rather than a reconstruction of it: a field this dataclass does not model
    survives the rewrite instead of being silently dropped.
    """

    lease_id: str
    writer_pid: int
    host_fingerprint: str
    acquired_at_utc: str
    expires_at_utc: str
    state: str
    document: Mapping[str, Any]

    @property
    def expires_at(self) -> datetime:
        """The recorded expiry as an aware UTC instant."""
        return datetime.fromisoformat(self.expires_at_utc.replace("Z", "+00:00"))

    def has_expired(self, *, now: datetime | None = None) -> bool:
        """Whether the recorded expiry is in the past."""
        return (datetime.now(UTC) if now is None else now) > self.expires_at


def _require_lease_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        message = f"the persisted lease field {label!r} must be a non-empty string"
        raise LeaseFormatError(message)
    return value


def _require_lease_timestamp(label: str, value: object) -> str:
    text = _require_lease_text(label, value)
    if not _LEASE_TIMESTAMP_PATTERN.fullmatch(text):
        message = f"the persisted lease field {label!r} is not an accepted UTC timestamp"
        raise LeaseFormatError(message)
    return text


def read_persisted_lease(raw: bytes) -> PersistedLease:
    """Parse and structurally validate one persisted lease document.

    Fail-closed in both directions: a missing required field is refused, and so is an
    **unknown** field. A lease carrying a key this module never writes was written by
    something else, and a governed recovery must not reconcile a document whose meaning it
    cannot account for.

    Raises:
        LeaseFormatError: the bytes are not a structurally valid lease document.
    """
    try:
        loaded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"the persisted lease is not readable UTF-8 JSON: {exc}"
        raise LeaseFormatError(message) from exc
    if not isinstance(loaded, dict):
        message = "the persisted lease is not a JSON object"
        raise LeaseFormatError(message)
    missing = tuple(sorted(_LEASE_REQUIRED_KEYS - set(loaded)))
    if missing:
        message = f"the persisted lease is missing required field(s) {missing}"
        raise LeaseFormatError(message)
    unknown = tuple(sorted(set(loaded) - _LEASE_REQUIRED_KEYS - _LEASE_OPTIONAL_KEYS))
    if unknown:
        message = f"the persisted lease carries unrecognized field(s) {unknown}"
        raise LeaseFormatError(message)
    pid = loaded["writer_pid"]
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        message = "the persisted lease field 'writer_pid' must be a positive integer"
        raise LeaseFormatError(message)
    return PersistedLease(
        lease_id=_require_lease_text("lease_id", loaded["lease_id"]),
        writer_pid=pid,
        host_fingerprint=_require_lease_text("host_fingerprint", loaded["host_fingerprint"]),
        acquired_at_utc=_require_lease_timestamp("acquired_at_utc", loaded["acquired_at_utc"]),
        expires_at_utc=_require_lease_timestamp("expires_at_utc", loaded["expires_at_utc"]),
        state=_require_lease_text("state", loaded["state"]),
        document=dict(loaded),
    )


def reconciled_lease_document(lease: PersistedLease, *, reconciled_at_utc: str) -> dict[str, Any]:
    """The Decision 103 R4 reconciled form of a stale ``held`` lease.

    The transition is ``held -> released`` — the state the ordinary holder-release path
    already writes, so every existing reader (``CatalogWriter._acquire_lease``, the E0
    preflight lease predicate) understands it without a vocabulary change.

    What makes it **truthful** is what is added and what is not:

    * ``released_at_utc`` is **not** written. That field means "the holder released this",
      and the holder did not; it died.
    * ``reconciliation_reason`` and ``reconciled_at_utc`` record that this release was an
      owner-authorized stale-writer recovery, performed by a different process at a later
      instant. Their presence is unambiguous — no ordinary release writes them.
    * ``reconciled_prior_state`` names the state that was displaced.
    * ``lease_id``, ``writer_pid``, ``host_fingerprint``, ``acquired_at_utc``, and
      ``expires_at_utc`` are carried through **unchanged**. They are already the prior
      holder's values, so separate ``prior_*`` copies would be exact duplicates rather than
      new provenance; the dead writer stays named in the record it left behind.

    Raises:
        LeaseFormatError: ``lease`` is not in the ``held`` state.
    """
    if lease.state != LEASE_STATE_HELD:
        message = (
            f"only a lease in state {LEASE_STATE_HELD!r} can be reconciled; this one records "
            f"{lease.state!r}"
        )
        raise LeaseFormatError(message)
    document = dict(lease.document)
    document["state"] = LEASE_STATE_RELEASED
    document["reconciliation_reason"] = STALE_LEASE_RECONCILIATION_REASON
    document["reconciled_at_utc"] = reconciled_at_utc
    document["reconciled_prior_state"] = LEASE_STATE_HELD
    return document


@contextmanager
def exclusive_lease_lock(path: Path, *, writable: bool) -> Iterator[int]:
    """Hold the accepted exclusive advisory lock on an **existing** lease file.

    This is the same mechanism :meth:`CatalogWriter._acquire_lease` uses — a non-blocking
    ``flock(LOCK_EX)`` on the lease file's own descriptor — and deliberately not a second
    locking scheme. Two differences from the writer path, both required by Decision 103 R3:

    * The file is never created. ``O_CREAT`` is absent, so asking whether the lock is free
      cannot bring a lease into existence.
    * A symbolic link or non-regular file is refused before the descriptor is used, so the
      lock and any subsequent write land on the lease itself and not on an aliased target.

    Args:
        path: The lease file, which must already exist.
        writable: Open read-write. Required only by the reconciliation, which rewrites the
            same descriptor it locked; a read-only inspection passes ``False``.

    Raises:
        LeaseFormatError: the path is absent, a symlink, or not a regular file.
        SingleWriterViolationError: another process holds the advisory lock.
        CatalogWriteError: advisory locking is unavailable on this platform.
    """
    if fcntl is None:  # pragma: no cover - supported CI and production platforms are Unix
        message = (
            "stale-lease reconciliation requires operating-system advisory locking, but "
            "fcntl.flock is unavailable on this platform; refusing to proceed without it"
        )
        raise CatalogWriteError(message)
    if path.is_symlink():
        message = "the catalog writer lease is a symbolic link and is refused"
        raise LeaseFormatError(message)
    if not path.is_file():
        message = "the catalog writer lease is absent or is not a regular file"
        raise LeaseFormatError(message)
    flags = (os.O_RDWR if writable else os.O_RDONLY) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):  # pragma: no cover - defensive
            message = "the opened catalog writer lease is not a regular file"
            raise LeaseFormatError(message)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            message = (
                "another process holds the catalog writer advisory lock; a lease held by a "
                "live writer is never stale and is never reconciled"
            )
            raise SingleWriterViolationError(message) from None
        try:
            yield descriptor
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def rewrite_locked_lease(descriptor: int, payload: bytes) -> None:
    """Rewrite the locked lease **in place**, preserving its inode, mode, and lock.

    Decision 103 R5 asks for the repository's safest existing atomic/private-file pattern.
    That pattern, for this file, is the in-place locked rewrite
    :meth:`CatalogWriter._release_lease` already performs — not a temporary file replaced by
    ``rename``. A rename would swap the inode, and ``flock`` is held on the *inode*: the
    exclusive lock would survive on an orphaned file while the new one sat unlocked and open
    to any writer. R5 also requires the lock to remain continuously held across the
    check-and-reconcile section, and those two requirements cannot both hold. Lock continuity
    wins, and the crash window is bounded instead:

    * the new payload is required to be no shorter than the old, so the file is never
      truncated first and no window exists in which it is legitimately empty;
    * the write is fsynced before the caller re-reads and revalidates it; and
    * a torn write leaves a document that fails structural validation, which every reader of
      this file refuses rather than interpreting.

    Raises:
        CatalogWriteError: the replacement payload is shorter than the document on disk.
    """
    existing = os.fstat(descriptor).st_size
    if len(payload) < existing:
        message = (
            "a reconciled lease may only add provenance to the document it replaces; refusing "
            "a replacement shorter than the persisted one"
        )
        raise CatalogWriteError(message)
    os.pwrite(descriptor, payload, 0)
    os.ftruncate(descriptor, len(payload))
    os.fsync(descriptor)


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
            "state": LEASE_STATE_HELD,
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
                persisted["state"] = LEASE_STATE_RELEASED
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
