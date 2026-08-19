"""Run-local working catalog for a long-running E0 successor materialization.

**The accepted D111 remediation instrument.** E0's durable database work is
long enough, and large enough, that carrying it out directly against the accepted operational
catalog is not safe: a single transaction spanning one planned source cannot keep its journal
bounded, and any bounded-commit scheme applied to the operational catalog would make partial,
un-dispositioned progress durable in the artifact the project treats as accepted state.

This module separates the two:

* the **accepted operational catalog** stays byte-identical for the whole of a long parse -- it
  is opened strictly read-only, exactly once, to copy from;
* a **run-local working catalog** carries every write, at the same migration head and the same
  schema, and is the only place partial progress may become durable.

An interruption therefore leaves the accepted catalog untouched and the working catalog holding
truthful, inspectable partial state. Neither is promoted here: promotion is a separate bounded
operation (:func:`promote_working_catalog`) and D111 authorizes it only against disposable state.

**Progress state lives outside the accepted schema.** ``census_parser_runs.outcome`` and
``census_plan_sources.parser_state`` have closed accepted vocabularies with no in-progress term,
and no migration may add one under this record. The distinction the accepted D111 instrument
requires -- not started, in progress, parsed, disposed -- is recorded in a run-local ledger beside
the working catalog, which is where run-local execution bookkeeping belongs anyway: it is a fact
about *this attempt*, not about the census.

A committed batch is execution progress and is never a source disposition.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.storage.catalog import strictly_read_only_connection
from disclosure_drift.storage.sqlite import (
    applied_versions,
    connect,
    integrity_report,
    utc_now,
)

__all__ = [
    "PROGRESS_LEDGER_FILENAME",
    "SQLITE_DEFAULT_CACHE_SIZE_PRAGMA",
    "cache_size_pragma",
    "file_digest",
    "WORKING_CATALOG_FILENAME",
    "RunProgressLedger",
    "SourceProgress",
    "WorkingCatalog",
    "WorkingCatalogError",
    "WorkingCatalogIdentity",
    "promote_working_catalog",
]


class WorkingCatalogError(DisclosureDriftError):
    """A working catalog could not be created, used, or promoted safely."""


def file_digest(path: Path) -> tuple[str, int]:
    """Return one file's SHA-256 and byte length, read in bounded chunks.

    Local rather than imported from the E0 driver so this module stays usable by it without
    an import cycle, and so a working catalog can be measured without pulling in E0 at all.
    """
    digest = hashlib.sha256()
    length = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
            length += len(chunk)
    return digest.hexdigest(), length


#: The working catalog's fixed name inside its run-local directory.
WORKING_CATALOG_FILENAME: Final = "working_catalog.sqlite3"

#: The run-local progress ledger's fixed name, beside the working catalog.
PROGRESS_LEDGER_FILENAME: Final = "run_progress.sqlite3"

#: What SQLite's own default ``cache_size`` reports when nothing configures one: 2000 pages,
#: which at the 1 KiB granularity of the negative form is about 2 MiB. Named here so a test can
#: assert that an unconfigured connection is genuinely unconfigured rather than merely different
#: from the budget under test.
SQLITE_DEFAULT_CACHE_SIZE_PRAGMA: Final = -2000


def cache_size_pragma(cache_bytes: int) -> int:
    """Return the ``PRAGMA cache_size`` value that requests ``cache_bytes`` of page cache.

    SQLite reads a **negative** ``cache_size`` as a kibibyte budget and a positive one as a
    page count. A page count is the wrong unit here: it silently means a different amount of
    memory at a different ``page_size``, so a budget stated in bytes is converted to the
    negative form rather than divided by an assumed page size.

    Args:
        cache_bytes: The requested budget in bytes. Must be a positive whole number of
            kibibytes -- a fractional kibibyte has no representation in this form, and
            rounding one silently would make the effective budget disagree with the requested
            one.

    Raises:
        WorkingCatalogError: the budget is not a positive whole number of kibibytes.
    """
    if cache_bytes <= 0:
        message = f"a working-catalog cache budget must be positive; got {cache_bytes} bytes"
        raise WorkingCatalogError(message)
    kibibytes, remainder = divmod(cache_bytes, 1024)
    if remainder:
        message = (
            f"a working-catalog cache budget must be a whole number of kibibytes; "
            f"{cache_bytes} bytes is not"
        )
        raise WorkingCatalogError(message)
    return -kibibytes


#: The four states the accepted D111 instrument requires a run-local source to be
#: distinguishable between.
#:
#: ``parsed`` deliberately sits between ``in_progress`` and ``disposed``: a source whose rows are
#: all written has finished *materializing*, which is not the same claim as its accepted
#: disposition having been recorded. Collapsing the two is exactly the "invent success for a
#: partial batch" failure this vocabulary exists to make impossible.
SourceProgressState = Literal["not_started", "in_progress", "parsed", "disposed"]

_PROGRESS_STATES: Final[frozenset[str]] = frozenset(
    {"not_started", "in_progress", "parsed", "disposed"}
)

_LEDGER_SCHEMA: Final = """
CREATE TABLE IF NOT EXISTS run_source_progress (
    source_instance_id  TEXT PRIMARY KEY,
    source_id           TEXT NOT NULL,
    state               TEXT NOT NULL CHECK (state IN
                            ('not_started', 'in_progress', 'parsed', 'disposed')),
    parts_committed     INTEGER NOT NULL DEFAULT 0 CHECK (parts_committed >= 0),
    batches_committed   INTEGER NOT NULL DEFAULT 0 CHECK (batches_committed >= 0),
    disposition         TEXT,
    detail              TEXT NOT NULL DEFAULT '',
    started_at_utc      TEXT,
    updated_at_utc      TEXT NOT NULL
) STRICT;

CREATE TABLE IF NOT EXISTS run_working_catalog (
    key                 TEXT PRIMARY KEY,
    value               TEXT NOT NULL
) STRICT;
"""


@dataclass(frozen=True, slots=True)
class WorkingCatalogIdentity:
    """The accepted catalog identity a working catalog was derived from.

    Captured strictly read-only at creation and written into the run-local ledger, so a
    working catalog can always name the exact artifact it descends from. Promotion refuses
    unless the artifact it is about to replace is still that one.
    """

    source_path: Path
    source_file_sha256: str
    source_byte_length: int
    applied_migrations: tuple[int, ...]
    created_at_utc: str

    @property
    def migration_head(self) -> int:
        """The highest applied migration version, which the working copy must match."""
        if not self.applied_migrations:
            message = "an accepted catalog with no applied migration cannot be copied"
            raise WorkingCatalogError(message)
        return max(self.applied_migrations)

    def as_mapping(self) -> Mapping[str, str]:
        """The ledger projection: every field as text, for the key/value provenance table."""
        return {
            "source_path": str(self.source_path),
            "source_file_sha256": self.source_file_sha256,
            "source_byte_length": str(self.source_byte_length),
            "applied_migrations": ",".join(str(v) for v in self.applied_migrations),
            "migration_head": str(self.migration_head),
            "created_at_utc": self.created_at_utc,
        }


@dataclass(frozen=True, slots=True)
class SourceProgress:
    """One planned source's run-local execution progress."""

    source_instance_id: str
    source_id: str
    state: SourceProgressState
    parts_committed: int
    batches_committed: int
    disposition: str | None
    detail: str
    started_at_utc: str | None
    updated_at_utc: str

    @property
    def is_complete(self) -> bool:
        """Whether this source finished materializing.

        ``in_progress`` is never complete however many parts committed, which is the whole
        point of separating durable progress from disposition.
        """
        return self.state in {"parsed", "disposed"}


class RunProgressLedger:
    """Truthful run-local progress, in its own database beside the working catalog.

    Deliberately not a table in the working catalog: the working catalog is a byte-for-byte
    schema twin of the accepted operational catalog, and it must stay one so that promoting it
    is a file operation rather than a schema reconciliation. Progress bookkeeping is about the
    attempt, not the census, so it lives next to it instead of inside it.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._connection = sqlite3.connect(path, isolation_level=None)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.execute("PRAGMA synchronous = FULL")
        self._connection.executescript(_LEDGER_SCHEMA)

    @property
    def path(self) -> Path:
        """Where this ledger is stored."""
        return self._path

    def close(self) -> None:
        """Close the ledger connection."""
        self._connection.close()

    def record_identity(self, identity: WorkingCatalogIdentity) -> None:
        """Persist the accepted catalog identity this working catalog descends from."""
        for key, value in identity.as_mapping().items():
            self._connection.execute(
                "INSERT INTO run_working_catalog (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def identity_value(self, key: str) -> str | None:
        """Read one recorded provenance value, or ``None`` when it was never written."""
        row = self._connection.execute(
            "SELECT value FROM run_working_catalog WHERE key = ?", (key,)
        ).fetchone()
        return None if row is None else str(row["value"])

    def begin_source(self, source_instance_id: str, source_id: str) -> None:
        """Record that a source has started, before its first durable row.

        Written and committed *ahead* of any parse write, so an interruption between this and
        the first batch is still visibly an interruption rather than an untouched source.
        """
        now = utc_now()
        self._connection.execute(
            "INSERT INTO run_source_progress (source_instance_id, source_id, state, "
            "started_at_utc, updated_at_utc) VALUES (?, ?, 'in_progress', ?, ?) "
            "ON CONFLICT(source_instance_id) DO UPDATE SET state = 'in_progress', "
            "updated_at_utc = excluded.updated_at_utc",
            (source_instance_id, source_id, now, now),
        )

    def record_batch(self, source_instance_id: str, *, parts: int, batches: int) -> None:
        """Record committed execution progress. This is never a disposition."""
        self._connection.execute(
            "UPDATE run_source_progress SET parts_committed = ?, batches_committed = ?, "
            "updated_at_utc = ? WHERE source_instance_id = ?",
            (parts, batches, utc_now(), source_instance_id),
        )

    def mark_parsed(self, source_instance_id: str, *, parts: int, batches: int) -> None:
        """Record that every row this source implies is durable in the working catalog.

        Still not a disposition: it says materialization finished, nothing about the accepted
        terminal the census will record.
        """
        self._connection.execute(
            "UPDATE run_source_progress SET state = 'parsed', parts_committed = ?, "
            "batches_committed = ?, updated_at_utc = ? WHERE source_instance_id = ?",
            (parts, batches, utc_now(), source_instance_id),
        )

    def mark_disposed(self, source_instance_id: str, disposition: str, detail: str = "") -> None:
        """Record the accepted final disposition, which the census layer decided.

        Refuses on a source that never reached ``parsed``: a disposition standing over
        unfinished materialization is the exact untruth the D111 instrument prohibits.
        """
        current = self.progress(source_instance_id)
        if current is None or current.state != "parsed":
            observed = "absent" if current is None else current.state
            message = (
                f"source {source_instance_id!r} cannot record disposition {disposition!r} "
                f"from run-local state {observed!r}; only a fully parsed source may be disposed"
            )
            raise WorkingCatalogError(message)
        self._connection.execute(
            "UPDATE run_source_progress SET state = 'disposed', disposition = ?, detail = ?, "
            "updated_at_utc = ? WHERE source_instance_id = ?",
            (disposition, detail, utc_now(), source_instance_id),
        )

    def progress(self, source_instance_id: str) -> SourceProgress | None:
        """One source's recorded progress, or ``None`` when it never started."""
        row = self._connection.execute(
            "SELECT * FROM run_source_progress WHERE source_instance_id = ?",
            (source_instance_id,),
        ).fetchone()
        return None if row is None else _progress(row)

    def all_progress(self) -> tuple[SourceProgress, ...]:
        """Every recorded source, ordered by identifier for a stable report."""
        rows = self._connection.execute(
            "SELECT * FROM run_source_progress ORDER BY source_instance_id"
        ).fetchall()
        return tuple(_progress(row) for row in rows)

    def incomplete(self) -> tuple[SourceProgress, ...]:
        """Every source that started and did not finish materializing."""
        return tuple(item for item in self.all_progress() if item.state == "in_progress")


def _progress(row: sqlite3.Row) -> SourceProgress:
    state = str(row["state"])
    if state not in _PROGRESS_STATES:
        message = f"run-local progress state {state!r} is not one this build recognizes"
        raise WorkingCatalogError(message)
    return SourceProgress(
        source_instance_id=str(row["source_instance_id"]),
        source_id=str(row["source_id"]),
        state=state,  # type: ignore[arg-type]
        parts_committed=int(row["parts_committed"]),
        batches_committed=int(row["batches_committed"]),
        disposition=None if row["disposition"] is None else str(row["disposition"]),
        detail=str(row["detail"]),
        started_at_utc=None if row["started_at_utc"] is None else str(row["started_at_utc"]),
        updated_at_utc=str(row["updated_at_utc"]),
    )


class WorkingCatalog:
    """A run-local writable twin of the accepted operational catalog.

    Use as a context manager. Entering copies the accepted catalog -- read strictly read-only,
    through the supported online-backup interface rather than a file copy, which is not valid
    for a WAL-mode database -- opens the copy for writing, and opens the run-local ledger.
    Leaving closes both. The accepted catalog is never opened for writing on any path here, so
    nothing in this class can alter one of its bytes.

    **The page cache is a connection-local execution parameter, and it is opt-in.** SQLite
    configures no ``cache_size`` unless one is asked for, which leaves a writer on the
    two-mebibyte default however large the database grows -- and a random-write working set far
    larger than that is what accepted Decision 118 measured as the primary constraint on real
    materialization throughput. ``cache_bytes`` sets one, on **this** connection alone: it is
    applied to the writing handle this class opens on its own run-local copy, after the handle
    exists, and it reaches no other connection, no other database, and no global default. A
    caller that asks for nothing gets exactly the behaviour it got before, which is why the
    parameter defaults to ``None`` rather than to a value.

    A cache budget changes how much memory the write is allowed to use, and nothing else. It
    moves no row, no identity, no digest, and no commit boundary.

    Args:
        source_path: The accepted operational catalog to derive from. Read-only.
        directory: The run-local directory to build in. Must not already hold a working
            catalog; a silent reuse would make a second attempt's progress indistinguishable
            from the first's.
        cache_bytes: An explicit page-cache budget for the writing connection, in bytes, or
            ``None`` for SQLite's own default. See :func:`cache_size_pragma`.
    """

    def __init__(
        self, source_path: Path, directory: Path, *, cache_bytes: int | None = None
    ) -> None:
        self._source_path = source_path
        self._directory = directory
        self._path = directory / WORKING_CATALOG_FILENAME
        self._ledger_path = directory / PROGRESS_LEDGER_FILENAME
        self._identity: WorkingCatalogIdentity | None = None
        self._ledger: RunProgressLedger | None = None
        self._connection: sqlite3.Connection | None = None
        self._context: object = None
        #: Validated at construction rather than at ``__enter__``, so an unrepresentable
        #: budget is refused before a copy of the accepted catalog has been taken.
        self._cache_bytes = cache_bytes
        self._cache_pragma = None if cache_bytes is None else cache_size_pragma(cache_bytes)

    # -- lifecycle --------------------------------------------------------- #
    def __enter__(self) -> WorkingCatalog:
        self._identity = self._create()
        self._ledger = RunProgressLedger(self._ledger_path)
        self._ledger.record_identity(self._identity)
        context = connect(self._path, writer=True)
        self._context = context
        self._connection = context.__enter__()
        if self._cache_pragma is not None:
            # Connection-local, and deliberately set here rather than inside ``connect``:
            # every other caller of that function -- the operational catalog included -- must
            # keep the durability and cache behaviour it already has.
            self._connection.execute(f"PRAGMA cache_size = {self._cache_pragma}")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self._context is not None:
            self._context.__exit__(exc_type, exc, traceback)  # type: ignore[attr-defined]
        self._context = None
        self._connection = None
        if self._ledger is not None:
            self._ledger.close()
        self._ledger = None

    # -- accessors --------------------------------------------------------- #
    @property
    def path(self) -> Path:
        """Where the working catalog file lives."""
        return self._path

    @property
    def connection(self) -> sqlite3.Connection:
        """The writing connection to the working catalog."""
        if self._connection is None:
            message = "working catalog is not open; use it as a context manager"
            raise WorkingCatalogError(message)
        return self._connection

    @property
    def ledger(self) -> RunProgressLedger:
        """The run-local progress ledger."""
        if self._ledger is None:
            message = "working catalog is not open; use it as a context manager"
            raise WorkingCatalogError(message)
        return self._ledger

    @property
    def requested_cache_bytes(self) -> int | None:
        """The page-cache budget this working catalog was asked for, or ``None``."""
        return self._cache_bytes

    @property
    def requested_cache_size_pragma(self) -> int | None:
        """The ``PRAGMA cache_size`` value the budget resolves to, or ``None``."""
        return self._cache_pragma

    @property
    def effective_cache_size_pragma(self) -> int:
        """What the writing connection **reports** its ``cache_size`` to be.

        Read back from SQLite rather than echoed from the request, so a caller verifying the
        budget is verifying the connection rather than its own argument.
        """
        return int(self.connection.execute("PRAGMA cache_size").fetchone()[0])

    @property
    def identity(self) -> WorkingCatalogIdentity:
        """The accepted catalog identity this copy descends from."""
        if self._identity is None:
            message = "working catalog has not been created yet"
            raise WorkingCatalogError(message)
        return self._identity

    def checkpoint(self) -> tuple[int, int, int]:
        """Truncate the write-ahead log and report ``(busy, log_frames, checkpointed)``.

        Safe here in a way it is not against the operational catalog: this file has exactly
        one connection, so the checkpoint never contends with a reader that legitimately
        holds frames.
        """
        row = self.connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        return (int(row[0]), int(row[1]), int(row[2]))

    def wal_byte_length(self) -> int:
        """The working catalog's current write-ahead log size, or ``0`` when absent."""
        sidecar = self._path.with_name(self._path.name + "-wal")
        return sidecar.stat().st_size if sidecar.is_file() else 0

    def byte_length(self) -> int:
        """The working catalog file's current size."""
        return self._path.stat().st_size

    # -- creation ---------------------------------------------------------- #
    def _create(self) -> WorkingCatalogIdentity:
        if not self._source_path.is_file():
            message = f"accepted catalog {self._source_path} does not exist"
            raise WorkingCatalogError(message)
        if self._path.exists():
            message = (
                f"working catalog {self._path} already exists; a run builds its own rather "
                "than adopting whatever a previous attempt left behind"
            )
            raise WorkingCatalogError(message)
        self._directory.mkdir(parents=True, exist_ok=True)
        source_sha256, source_bytes = file_digest(self._source_path)
        # Strictly read-only on the source: a read-write handle to a WAL-mode database
        # checkpoints on close and would rewrite accepted bytes for no reason at all.
        with strictly_read_only_connection(self._source_path) as origin:
            applied = applied_versions(origin)
            target = sqlite3.connect(self._path)
            try:
                origin.backup(target)
            finally:
                target.close()
        self._verify_copy(applied)
        return WorkingCatalogIdentity(
            source_path=self._source_path,
            source_file_sha256=source_sha256,
            source_byte_length=source_bytes,
            applied_migrations=applied,
            created_at_utc=utc_now(),
        )

    def _verify_copy(self, expected: tuple[int, ...]) -> None:
        """Refuse a copy that is not the accepted schema, before one row is written."""
        with strictly_read_only_connection(self._path) as copy:
            applied = applied_versions(copy)
            report = integrity_report(copy)
        if applied != expected:
            message = (
                "working catalog migration chain does not match the accepted catalog: "
                f"expected {list(expected)}, found {list(applied)}"
            )
            raise WorkingCatalogError(message)
        report.require()


@contextmanager
def promoted_candidate(path: Path) -> Iterator[Path]:
    """Yield ``path`` and remove it if the caller fails, so no half-promotion survives."""
    try:
        yield path
    except BaseException:
        with suppress(OSError):
            path.unlink()
        raise


def promote_working_catalog(
    working_path: Path,
    operational_path: Path,
    *,
    expected_working_sha256: str,
    expected_operational_sha256: str,
) -> str:
    """Replace an accepted catalog with a verified working catalog, atomically.

    The accepted D111 instrument asks only that this be *demonstrable*, and it authorizes it against
    disposable state alone. Nothing here is wired to the real operational catalog, and no
    caller in this package invokes it against one.

    The operation is a single ``rename`` within one directory, which POSIX makes atomic: a
    concurrent reader sees either the whole previous catalog or the whole new one, never a
    partial file. Everything else exists so the rename is only reached when it is correct:

    * both identities are asserted **before** anything moves, so a promotion cannot install a
      catalog other than the one that was verified, and cannot silently overwrite an
      operational catalog that changed since it was measured;
    * the working catalog's write-ahead log is checkpointed and its sidecars are removed
      first, so the promoted file is self-contained rather than depending on a log that is
      about to be orphaned by the rename;
    * the file and then its containing directory are fsynced, so the rename survives a crash
      rather than merely being visible to the running kernel;
    * the previous catalog is not deleted here -- recovering it is the already-governed
      backup's job, and this refuses to be a second, weaker copy of that mechanism.

    No re-parsing happens: the promoted bytes are the verified bytes.

    Args:
        working_path: The verified working catalog to promote.
        operational_path: The catalog it becomes.
        expected_working_sha256: The working catalog's verified digest.
        expected_operational_sha256: The digest the operational catalog must still have.

    Returns:
        The promoted catalog's digest, which equals ``expected_working_sha256``.

    Raises:
        WorkingCatalogError: any identity, residency, or durability precondition failed.
    """
    if working_path.parent != operational_path.parent:
        message = (
            "promotion must be a rename inside one directory so it is atomic; "
            f"{working_path.parent} and {operational_path.parent} are different"
        )
        raise WorkingCatalogError(message)
    if operational_path.is_file():
        actual_operational, _ = file_digest(operational_path)
        if actual_operational != expected_operational_sha256:
            message = (
                "the catalog being replaced is not the one this promotion was prepared "
                f"against: expected {expected_operational_sha256}, found {actual_operational}"
            )
            raise WorkingCatalogError(message)
    # Fold the log in and drop the sidecars: after the rename they would belong to a name
    # that no longer refers to this file.
    with connect(working_path, writer=True) as connection:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    for suffix in ("-wal", "-shm"):
        sidecar = working_path.with_name(working_path.name + suffix)
        if sidecar.is_file():
            sidecar.unlink()
    actual_working, _ = file_digest(working_path)
    if actual_working != expected_working_sha256:
        message = (
            "the working catalog is not the artifact that was verified: expected "
            f"{expected_working_sha256}, found {actual_working}"
        )
        raise WorkingCatalogError(message)
    _fsync_file(working_path)
    working_path.replace(operational_path)
    _fsync_directory(operational_path.parent)
    promoted, _ = file_digest(operational_path)
    if promoted != expected_working_sha256:
        message = (
            "the promoted catalog is not the verified working catalog: expected "
            f"{expected_working_sha256}, found {promoted}"
        )
        raise WorkingCatalogError(message)
    return promoted


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
