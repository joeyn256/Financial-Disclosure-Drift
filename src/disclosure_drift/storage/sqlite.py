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
from typing import Final, Never

from disclosure_drift.errors import GateFailureError, SqliteVersionError

__all__ = [
    "MIGRATIONS_PACKAGE",
    "transaction",
    "REQUIRED_SQLITE_VERSION",
    "IntegrityReport",
    "Migration",
    "applied_versions",
    "apply_migrations",
    "available_migrations",
    "backup_database",
    "connect",
    "integrity_report",
    "require_sqlite_version",
    "utc_now",
    "validate_observation_lineage",
    "verify_applied_migrations",
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
        verify_applied_migrations(connection)
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
        try:
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise


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
                # Decode the exact packaged bytes used for the checksum and execution.
                # ``read_text`` would normalize CRLF on some platforms.
                sql=entry.read_bytes().decode("utf-8"),
            )
        )
    migrations = tuple(sorted(found, key=lambda migration: migration.version))
    _validate_migration_inventory(migrations)
    return migrations


def _validate_migration_inventory(migrations: tuple[Migration, ...]) -> None:
    """Reject an ambiguous, duplicated, reordered, or gapped migration inventory."""
    if not migrations:
        message = "the packaged migration inventory is empty"
        raise GateFailureError(message)
    versions = tuple(migration.version for migration in migrations)
    expected_versions = tuple(range(1, len(migrations) + 1))
    if versions != expected_versions:
        message = (
            "packaged migration versions must be unique, ordered, and contiguous from 1; "
            f"found {versions}, expected {expected_versions}"
        )
        raise GateFailureError(message)
    names = tuple(migration.name for migration in migrations)
    if any(not name for name in names) or len(set(names)) != len(names):
        message = f"packaged migration names must be non-empty and unique; found {names}"
        raise GateFailureError(message)


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


def verify_applied_migrations(
    connection: sqlite3.Connection,
    migrations: tuple[Migration, ...] | None = None,
) -> tuple[int, ...]:
    """Verify that recorded migrations are an exact prefix of the packaged chain.

    Stored migration provenance is immutable evidence. A recorded checksum or name
    is never repaired from the package: any drift, unknown version, gap, duplicate,
    or invalid ordering fails before the connection is handed to a caller.
    """
    inventory = migrations if migrations is not None else available_migrations()
    _validate_migration_inventory(inventory)
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'ops_schema_migrations'"
    ).fetchone()
    if table is None:
        return ()

    rows = connection.execute(
        "SELECT version, name, checksum_sha256 FROM ops_schema_migrations ORDER BY version"
    ).fetchall()
    versions = tuple(_as_int(row["version"], "ops_schema_migrations.version") for row in rows)
    if len(set(versions)) != len(versions):
        message = f"applied migration metadata contains duplicate versions: {versions}"
        raise GateFailureError(message)

    known_versions = {migration.version for migration in inventory}
    unknown = tuple(version for version in versions if version not in known_versions)
    if unknown:
        message = (
            "applied migration provenance contains versions absent from the packaged "
            f"inventory: {unknown}"
        )
        raise GateFailureError(message)

    expected_versions = tuple(range(1, len(versions) + 1))
    if versions != expected_versions:
        message = (
            "applied migration provenance is reordered or has a gap; "
            f"found {versions}, expected the packaged prefix {expected_versions}"
        )
        raise GateFailureError(message)

    expected_by_version = {migration.version: migration for migration in inventory}
    for row, version in zip(rows, versions, strict=True):
        expected = expected_by_version[version]
        recorded_name = str(row["name"])
        if recorded_name != expected.name:
            message = (
                f"applied migration {version} name mismatch: recorded "
                f"{recorded_name!r}, packaged {expected.name!r}"
            )
            raise GateFailureError(message)
        recorded_checksum = str(row["checksum_sha256"])
        if recorded_checksum != expected.checksum_sha256:
            message = (
                f"applied migration {version} ({expected.name}) checksum mismatch; "
                "packaged SQL changed after application or catalog provenance was altered"
            )
            raise GateFailureError(message)
    return versions


_REUSED_OBJECT_FIELDS: Final[tuple[str, ...]] = (
    "relative_storage_path",
    "transport_sha256",
    "stored_sha256",
    "logical_sha256",
    "content_sha256",
    "transport_size_bytes",
    "stored_size_bytes",
    "content_size_bytes",
    "storage_representation",
    "parser_version",
    "observed_content_kind",
)


def validate_observation_lineage(connection: sqlite3.Connection) -> None:
    """Fail closed when pre-R3 observation lineage cannot satisfy migration 0008."""
    _require_no_foreign_key_violations(
        connection,
        context="before migration 0008",
    )
    table = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'census_source_observations'"
    ).fetchone()
    if table is None:
        return

    rows = connection.execute(
        "SELECT observation_id, source_id, request_identity, retrieved_at_utc, outcome, "
        "supersedes_observation_id, reused_observation_id, relative_storage_path, "
        "transport_sha256, stored_sha256, logical_sha256, content_sha256, "
        "transport_size_bytes, stored_size_bytes, content_size_bytes, "
        "storage_representation, parser_version, observed_content_kind "
        "FROM census_source_observations"
    ).fetchall()
    by_id = {str(row["observation_id"]): row for row in rows}
    edges: dict[str, tuple[str, ...]] = {}

    for row in rows:
        observation_id = str(row["observation_id"])
        supersedes = _optional_cell_text(row["supersedes_observation_id"])
        reused = _optional_cell_text(row["reused_observation_id"])
        targets = tuple(target for target in (supersedes, reused) if target is not None)
        edges[observation_id] = targets
        if supersedes is not None and reused is not None:
            _lineage_failure(observation_id, "cannot both supersede and reuse another observation")
        if observation_id in targets:
            _lineage_failure(observation_id, "cannot reference itself")

        outcome = str(row["outcome"])
        if (outcome == "superseded") != (supersedes is not None):
            _lineage_failure(
                observation_id,
                "supersession lineage and the superseded outcome disagree",
            )
        if reused is not None and outcome not in {"unchanged_content", "reused_snapshot"}:
            _lineage_failure(
                observation_id,
                f"outcome {outcome!r} cannot carry reuse lineage",
            )
        if outcome in {"unchanged_content", "reused_snapshot"} and reused is None:
            _lineage_failure(observation_id, f"outcome {outcome!r} lacks reuse lineage")
        if supersedes is not None:
            missing_new_object = tuple(
                field
                for field in _REUSED_OBJECT_FIELDS
                if row[field] is None or (isinstance(row[field], str) and not row[field])
            )
            if missing_new_object:
                _lineage_failure(
                    observation_id,
                    "superseding observation lacks complete new-object metadata "
                    f"{missing_new_object}",
                )
            if (
                row["logical_sha256"] != row["content_sha256"]
                or row["transport_sha256"] != row["logical_sha256"]
                or row["transport_size_bytes"] != row["content_size_bytes"]
            ):
                _lineage_failure(
                    observation_id,
                    "superseding observation has inconsistent transport or logical metadata",
                )

        for relationship, target_id in (
            ("supersedes", supersedes),
            ("reuses", reused),
        ):
            if target_id is None:
                continue
            target = by_id.get(target_id)
            if target is None:
                _lineage_failure(
                    observation_id,
                    f"{relationship} missing observation {target_id!r}",
                )
            if str(target["source_id"]) != str(row["source_id"]) or str(
                target["request_identity"]
            ) != str(row["request_identity"]):
                _lineage_failure(
                    observation_id,
                    f"{relationship} an incompatible source or request identity",
                )
            if str(target["retrieved_at_utc"]) > str(row["retrieved_at_utc"]):
                _lineage_failure(
                    observation_id,
                    f"{relationship} an observation retrieved later than itself",
                )
            if relationship == "supersedes":
                if str(target["outcome"]) not in {
                    "stored_new",
                    "superseded",
                    "unchanged_content",
                    "reused_snapshot",
                }:
                    _lineage_failure(
                        observation_id,
                        "supersedes a failed or quarantined observation",
                    )
                missing_target = tuple(
                    field
                    for field in _REUSED_OBJECT_FIELDS
                    if target[field] is None
                    or (isinstance(target[field], str) and not target[field])
                )
                if missing_target:
                    _lineage_failure(
                        observation_id,
                        f"supersession target lacks complete object metadata {missing_target}",
                    )
                if (
                    target["logical_sha256"] != target["content_sha256"]
                    or target["transport_sha256"] != target["logical_sha256"]
                    or target["transport_size_bytes"] != target["content_size_bytes"]
                ):
                    _lineage_failure(
                        observation_id,
                        "supersession target has inconsistent transport or logical metadata",
                    )

        if reused is not None:
            target = by_id[reused]
            if str(target["outcome"]) not in {"stored_new", "superseded"}:
                _lineage_failure(
                    observation_id,
                    "reuse target does not own an independently stored raw object",
                )
            missing = tuple(
                field
                for field in _REUSED_OBJECT_FIELDS
                if target[field] is None or (isinstance(target[field], str) and not target[field])
            )
            if missing:
                _lineage_failure(
                    observation_id,
                    f"reuse target lacks required raw-object metadata {missing}",
                )
            if target["logical_sha256"] != target["content_sha256"]:
                _lineage_failure(
                    observation_id,
                    "reuse target has inconsistent logical and content hashes",
                )
            if (
                target["transport_sha256"] != target["logical_sha256"]
                or target["transport_size_bytes"] != target["content_size_bytes"]
            ):
                _lineage_failure(
                    observation_id,
                    "reuse target has inconsistent transport and logical metadata",
                )
            if str(target["storage_representation"]) == "identical" and (
                target["stored_sha256"] != target["logical_sha256"]
                or target["stored_size_bytes"] != target["content_size_bytes"]
            ):
                _lineage_failure(
                    observation_id,
                    "reuse target's identical representation has inconsistent metadata",
                )
            mismatched = tuple(
                field for field in _REUSED_OBJECT_FIELDS if row[field] != target[field]
            )
            if mismatched:
                _lineage_failure(
                    observation_id,
                    f"reused raw-object metadata differs in {mismatched}",
                )

    visited: set[str] = set()
    for start in sorted(edges):
        if start in visited:
            continue
        visiting: set[str] = set()
        stack: list[tuple[str, bool]] = [(start, False)]
        while stack:
            observation_id, exiting = stack.pop()
            if exiting:
                visiting.remove(observation_id)
                visited.add(observation_id)
                continue
            if observation_id in visited:
                continue
            if observation_id in visiting:
                _lineage_failure(
                    observation_id,
                    "participates in an observation-lineage cycle",
                )
            visiting.add(observation_id)
            stack.append((observation_id, True))
            stack.extend(
                (target_id, False)
                for target_id in reversed(edges.get(observation_id, ()))
                if target_id not in visited
            )


def _optional_cell_text(value: object) -> str | None:
    return None if value is None else str(value)


def _lineage_failure(observation_id: str, detail: str) -> Never:
    message = f"observation lineage fails migration 0008 preflight: {observation_id!r} {detail}"
    raise GateFailureError(message)


def _require_no_foreign_key_violations(
    connection: sqlite3.Connection,
    *,
    context: str,
) -> None:
    violations = connection.execute("PRAGMA foreign_key_check").fetchall()
    if not violations:
        return
    preview = tuple(tuple(row) for row in violations[:5])
    message = (
        f"foreign-key integrity failed {context}: {len(violations)} violation(s); "
        f"first violations={preview}"
    )
    raise GateFailureError(message)


def apply_migrations(
    connection: sqlite3.Connection,
    migrations: tuple[Migration, ...] | None = None,
) -> tuple[Migration, ...]:
    """Apply pending migrations and return those applied.

    Idempotent and crash-tolerant: each packaged script and its immutable
    provenance row commit in one explicit transaction. ``executescript`` commits
    any caller transaction before executing, so the transaction must be included
    in the script passed to it rather than opened by a surrounding context manager.
    """
    inventory = migrations if migrations is not None else available_migrations()
    _validate_migration_inventory(inventory)
    already = set(verify_applied_migrations(connection, inventory))
    applied: list[Migration] = []
    for migration in inventory:
        if migration.version in already:
            continue
        try:
            if migration.version == 8:
                validate_observation_lineage(connection)
            script = (
                migration.sql if migration.version == 8 else f"BEGIN IMMEDIATE;\n{migration.sql}\n"
            )
            connection.executescript(script)
            if not connection.in_transaction:
                message = (
                    f"migration {migration.version:04d} did not retain its schema transaction "
                    "for atomic provenance bookkeeping"
                )
                raise GateFailureError(message)
            if migration.version == 8:
                _require_no_foreign_key_violations(
                    connection,
                    context="after migration 0008 schema rebuild",
                )
            connection.execute(
                "INSERT INTO ops_schema_migrations "
                "(version, name, checksum_sha256, applied_at_utc) VALUES (?, ?, ?, ?)",
                (migration.version, migration.name, migration.checksum_sha256, utc_now()),
            )
            connection.execute("COMMIT")
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            connection.execute("PRAGMA foreign_keys = ON")
            foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
            if foreign_keys != 1:
                message = (
                    f"migration {migration.version:04d} did not restore foreign-key "
                    "enforcement on the live connection"
                )
                raise GateFailureError(message)
        applied.append(migration)
    verify_applied_migrations(connection, inventory)
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
