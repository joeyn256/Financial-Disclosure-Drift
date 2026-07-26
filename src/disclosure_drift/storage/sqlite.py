"""SQLite connection policy, migrations, and integrity gates (Decision 009 section 8).

Every connection enables foreign keys and a busy timeout. The writer additionally
uses WAL with ``synchronous = FULL``. Migrations are explicit and versioned.
Backups use the SQLite backup API; a live WAL-mode database is never copied naïvely.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Final

from disclosure_drift.errors import GateFailureError, SqliteVersionError

__all__ = [
    "MIGRATIONS_PACKAGE",
    "transaction",
    "REQUIRED_SQLITE_VERSION",
    "IntegrityReport",
    "Migration",
    "apply_migrations",
    "available_migrations",
    "backup_database",
    "connect",
    "integrity_report",
    "require_sqlite_version",
    "utc_now",
]

REQUIRED_SQLITE_VERSION: Final[tuple[int, int]] = (3, 37)
MIGRATIONS_PACKAGE: Final = "disclosure_drift.storage.migrations"
_BUSY_TIMEOUT_MS: Final = 10_000


def utc_now() -> str:
    """Return the current UTC instant as an ISO-8601 string with a ``Z`` suffix."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def require_sqlite_version(minimum: tuple[int, int] = REQUIRED_SQLITE_VERSION) -> str:
    """Return the SQLite version, or raise when it is older than the floor.

    Raises:
        SqliteVersionError: the runtime is too old for STRICT tables.
    """
    parts = tuple(int(part) for part in sqlite3.sqlite_version.split("."))
    if parts[: len(minimum)] < minimum:
        wanted = ".".join(str(part) for part in minimum)
        message = (
            f"SQLite {sqlite3.sqlite_version} is older than the required {wanted}\n"
            "Fix: use a Python build linked against a newer SQLite; STRICT tables need it."
        )
        raise SqliteVersionError(message)
    return sqlite3.sqlite_version


@contextmanager
def connect(path: Path, *, writer: bool = False) -> Iterator[sqlite3.Connection]:
    """Open a catalog connection with the required pragmas.

    Args:
        path: Database path. Parent directories are created for a writer.
        writer: Whether this connection may write. Writers set WAL and
            ``synchronous = FULL``; readers do not change durability settings.
    """
    require_sqlite_version()
    if writer:
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, isolation_level=None, timeout=_BUSY_TIMEOUT_MS / 1000)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
        if writer:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
        yield connection
    finally:
        connection.close()


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run an explicit transaction, rolling back on any exception.

    ``sqlite3.Connection.executescript`` implicitly commits, so the guards check
    :attr:`sqlite3.Connection.in_transaction` before committing or rolling back.
    """
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        if connection.in_transaction:
            connection.execute("ROLLBACK")
        raise
    if connection.in_transaction:
        connection.execute("COMMIT")


@dataclass(frozen=True, slots=True)
class Migration:
    """One versioned migration script."""

    version: int
    name: str
    sql: str

    @property
    def checksum_sha256(self) -> str:
        """Content hash of the migration script."""
        return hashlib.sha256(self.sql.encode("utf-8")).hexdigest()


def available_migrations() -> tuple[Migration, ...]:
    """Return every packaged migration in version order."""
    found: list[Migration] = []
    for entry in resources.files(MIGRATIONS_PACKAGE).iterdir():
        name = entry.name
        if not name.endswith(".sql"):
            continue
        version_text, _, remainder = name.partition("_")
        found.append(
            Migration(
                version=int(version_text),
                name=remainder.removesuffix(".sql"),
                sql=entry.read_text(encoding="utf-8"),
            )
        )
    return tuple(sorted(found, key=lambda migration: migration.version))


def _as_int(value: object, field: str) -> int:
    """Narrow a SQLite cell to ``int`` without trusting the driver's ``Any``."""
    if isinstance(value, bool):
        message = f"{field} must be an integer, received a boolean"
        raise GateFailureError(message)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    message = f"{field} must be an integer, received {type(value).__name__}"
    raise GateFailureError(message)


def applied_versions(connection: sqlite3.Connection) -> tuple[int, ...]:
    """Return applied migration versions, or an empty tuple on a fresh database."""
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'ops_schema_migrations'"
    ).fetchone()
    if row is None:
        return ()
    rows = connection.execute("SELECT version FROM ops_schema_migrations ORDER BY version")
    return tuple(_as_int(item["version"], "ops_schema_migrations.version") for item in rows)


def apply_migrations(connection: sqlite3.Connection) -> tuple[Migration, ...]:
    """Apply pending migrations and return those applied.

    Idempotent and crash-tolerant: the DDL uses ``IF NOT EXISTS`` and the version
    row is written with ``INSERT OR REPLACE``, so a crash between the script and
    the bookkeeping row is repaired by simply running again. ``executescript``
    commits implicitly, so the version row is written immediately afterwards
    rather than inside a wrapping transaction.
    """
    already = set(applied_versions(connection))
    applied: list[Migration] = []
    for migration in available_migrations():
        if migration.version in already:
            continue
        connection.executescript(migration.sql)
        connection.execute(
            "INSERT OR REPLACE INTO ops_schema_migrations "
            "(version, name, checksum_sha256, applied_at_utc) VALUES (?, ?, ?, ?)",
            (migration.version, migration.name, migration.checksum_sha256, utc_now()),
        )
        applied.append(migration)
    return tuple(applied)


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    """Outcome of the three SQLite integrity gates."""

    quick_check: str
    integrity_check: str
    foreign_key_violations: int

    @property
    def passed(self) -> bool:
        """Whether the database may be frozen into a release."""
        return (
            self.quick_check == "ok"
            and self.integrity_check == "ok"
            and self.foreign_key_violations == 0
        )

    def require(self) -> None:
        """Raise unless every gate passed.

        Raises:
            GateFailureError: an integrity gate failed.
        """
        if self.passed:
            return
        message = (
            "SQLite integrity gate failed: "
            f"quick_check={self.quick_check}, integrity_check={self.integrity_check}, "
            f"foreign_key_violations={self.foreign_key_violations}"
        )
        raise GateFailureError(message)


def integrity_report(connection: sqlite3.Connection) -> IntegrityReport:
    """Run ``quick_check``, ``integrity_check``, and ``foreign_key_check``."""
    quick = str(connection.execute("PRAGMA quick_check").fetchone()[0])
    integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
    violations = len(connection.execute("PRAGMA foreign_key_check").fetchall())
    return IntegrityReport(quick, integrity, violations)


def backup_database(source: Path, destination: Path) -> Path:
    """Copy a live database consistently using the SQLite backup API.

    A naïve file copy of a WAL-mode database is prohibited; this uses the
    supported online-backup interface instead.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    with connect(source) as origin, sqlite3.connect(destination) as target:
        origin.backup(target)
    return destination
