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
import json
import os
import sqlite3
import stat
import struct
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
    "checkpoint_main_truncate",
    "normalized_wal_bytes",
    "promote_working_catalog",
    "promote_world_directory",
    "STATEMENT_JOURNAL_CONTRACT",
    "STATEMENT_EVENT_CONTRACT",
    "STATEMENT_EVENT_MAX_BYTES",
    "StatementJournalReading",
    "StatementJournalWriter",
    "WalObservation",
    "authenticate_statement_journal",
    "observe_wal",
    "read_statement_journal",
    "require_sqlite_page_size",
    "wal_index_committed_frames",
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

    def record_value(self, key: str, value: str) -> None:
        """Persist one run-local key/value fact beside the working catalog.

        The generic writer behind :meth:`record_identity`, and the durable home accepted
        Decision 145 puts a phase's terminal checkpoint in. It stays in **this** database rather
        than in the working catalog for the reason the class docstring already gives: the
        working catalog is a byte-for-byte schema twin of the accepted operational catalog and
        must stay one, and a phase checkpoint is bookkeeping about the attempt. Storing it here
        is why phase-boundary restart needed no migration and why head stays ``0015``.
        """
        self._connection.execute(
            "INSERT INTO run_working_catalog (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )

    def recorded_value(self, key: str) -> str | None:
        """Read one recorded run-local value, or ``None`` when it was never written."""
        row = self._connection.execute(
            "SELECT value FROM run_working_catalog WHERE key = ?", (key,)
        ).fetchone()
        return None if row is None else str(row["value"])

    def identity_value(self, key: str) -> str | None:
        """Read one recorded provenance value, or ``None`` when it was never written."""
        return self.recorded_value(key)

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
        attach: Open the working catalog a **previous phase process** already built, instead of
            building one (accepted Decision 145). It is the successor half of phase-boundary
            restart and it inverts exactly one rule: creation refuses a directory that already
            holds a working catalog, and attachment refuses one that does not. It copies
            nothing, creates nothing, and proves the accepted catalog is still byte-identical to
            the artifact the copy descends from before admitting anything.
    """

    def __init__(
        self,
        source_path: Path,
        directory: Path,
        *,
        cache_bytes: int | None = None,
        attach: bool = False,
    ) -> None:
        self._source_path = source_path
        self._directory = directory
        #: Accepted Decision 145: open the working catalog a **previous phase process** built,
        #: rather than build one. Defaults to ``False``, so every accepted caller creates
        #: exactly as it did before and a silent reuse is still impossible on that path.
        self._attach = attach
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
        if self._attach:
            # The ledger is opened FIRST here and only here: the recorded identity is what the
            # attach proves against, so it has to be readable before anything is admitted.
            if not self._ledger_path.is_file():
                message = (
                    f"no run-local progress ledger exists at {self._ledger_path.name}; a phase "
                    "continuation attaches to the world a previous phase built and never "
                    "creates one, so an absent ledger is a refusal rather than a fresh start"
                )
                raise WorkingCatalogError(message)
            self._ledger = RunProgressLedger(self._ledger_path)
            self._identity = self._attach_existing()
        else:
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

    def _attach_existing(self) -> WorkingCatalogIdentity:
        """Open the working catalog a previous phase built, and prove it is that one.

        **Nothing is copied and nothing is created.** This is the successor half of accepted
        Decision 145's phase-boundary restart: F0 built the working catalog, F1 and F2 continue
        into it from separate processes, and the copy that :meth:`_create` refuses to overwrite
        is exactly the copy this must find already present.

        Three proofs, and each refuses rather than warns:

        * the working catalog and the run-local ledger both **exist**;
        * the accepted operational catalog is still **byte-identical** to the artifact this copy
          was taken from -- compared against the digest the ledger recorded at creation, so an
          accepted catalog that changed between phases refuses instead of being continued
          against;
        * the copy's applied migration chain is still exactly the recorded one.

        **The full integrity check is deliberately not repeated here.** ``PRAGMA
        integrity_check`` is O(database) and :meth:`_create` runs it when the copy is fresh,
        which is the moment it can be afforded and the moment a bad copy would be born. Running
        it again at every phase boundary of a multi-hundred-gibibyte working catalog would cost
        hours per boundary and is not what the boundary is asking about.

        Raises:
            WorkingCatalogError: the working catalog is absent, its identity was never recorded,
                the accepted catalog has moved, or the migration chain does not match.
        """
        if not self._path.is_file():
            message = (
                f"no working catalog exists at {self._path.name}; a phase continuation attaches "
                "to the one a previous phase built and never builds its own"
            )
            raise WorkingCatalogError(message)
        ledger = self._ledger
        if ledger is None:  # pragma: no cover - __enter__ opens it before calling this
            message = "the run-local ledger must be open before a working catalog is attached"
            raise WorkingCatalogError(message)
        recorded = {
            key: ledger.identity_value(key)
            for key in (
                "source_path",
                "source_file_sha256",
                "source_byte_length",
                "applied_migrations",
                "created_at_utc",
            )
        }
        missing = sorted(key for key, value in recorded.items() if value is None)
        if missing:
            message = (
                "the run-local ledger records no working-catalog identity "
                f"({', '.join(missing)} absent); a copy that cannot name the artifact it "
                "descends from is never continued against"
            )
            raise WorkingCatalogError(message)
        if not self._source_path.is_file():
            message = f"accepted catalog {self._source_path} does not exist"
            raise WorkingCatalogError(message)
        source_sha256, source_bytes = file_digest(self._source_path)
        if source_sha256 != recorded["source_file_sha256"]:
            message = (
                "the accepted operational catalog is NOT the artifact this working catalog was "
                "taken from: its digest has changed since the phase that created the copy. A "
                "continuation is a continuation of one governed run against one frozen catalog, "
                "so this is refused rather than continued"
            )
            raise WorkingCatalogError(message)
        if str(source_bytes) != recorded["source_byte_length"]:  # pragma: no cover - digest first
            message = (
                "the accepted operational catalog's byte length has changed since this working "
                "catalog was taken from it; the run is refused"
            )
            raise WorkingCatalogError(message)
        applied = tuple(
            int(part) for part in str(recorded["applied_migrations"]).split(",") if part
        )
        self._verify_attached(applied)
        return WorkingCatalogIdentity(
            source_path=Path(str(recorded["source_path"])),
            source_file_sha256=source_sha256,
            source_byte_length=source_bytes,
            applied_migrations=applied,
            created_at_utc=str(recorded["created_at_utc"]),
        )

    def _verify_attached(self, expected: tuple[int, ...]) -> None:
        """Refuse an attached copy whose migration chain is no longer the recorded one."""
        with strictly_read_only_connection(self._path) as copy:
            applied = applied_versions(copy)
        if applied != expected:
            message = (
                "the attached working catalog's migration chain does not match the one recorded "
                f"when it was created: expected {list(expected)}, found {list(applied)}"
            )
            raise WorkingCatalogError(message)

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


# --------------------------------------------------------------------------- #
# D151-C31R2-R19A-C2: the durable-stage successor's three world-level primitives
# --------------------------------------------------------------------------- #
#: The exact checkpoint statement every successor stage boundary issues, and the only one.
#: ``main.`` is deliberate: an unqualified ``wal_checkpoint`` acts on every attached database,
#: and a stage boundary is a statement about the world catalog alone -- the attachments are
#: immutable inputs that carry no log of their own and were detached before this runs.
MAIN_WAL_CHECKPOINT_TRUNCATE: Final = "PRAGMA main.wal_checkpoint(TRUNCATE)"


def checkpoint_main_truncate(connection: sqlite3.Connection) -> tuple[int, int, int]:
    """Fold the world catalog's write-ahead log into its main file and truncate the log.

    The successor stage boundary -- D151-C31R2-R19A-C2 §30 steps 10-12. Two prerequisites are
    required rather than assumed: no transaction is active (a checkpoint inside one would leave
    the frames it cannot yet fold) and no database is attached (``main.`` names the world alone,
    and an attachment present here would mean the stage's DETACH order was wrong). The result is
    held to the exact success tuple ``(busy, log_frames, checkpointed) == (0, 0, 0)``: after a
    TRUNCATE checkpoint SQLite reports the log as zero frames, so anything else means a frame
    was not folded -- a blocked checkpoint reports ``busy = 1``, a PASSIVE one reports the
    frames it left behind -- and is refused rather than read as partial progress.

    Raises:
        WorkingCatalogError: a transaction is active, a database is attached, or the checkpoint
            did not report the exact success tuple.
    """
    if connection.in_transaction:
        message = (
            "a stage checkpoint is issued only after COMMIT; a transaction is still active and "
            "the checkpoint is refused rather than taken over frames it could not fold"
        )
        raise WorkingCatalogError(message)
    attached = [
        str(row["name"])
        for row in connection.execute("PRAGMA database_list")
        if str(row["name"]) not in {"main", "temp"}
    ]
    if attached:
        message = (
            f"a stage checkpoint is issued only after every input is detached; {attached} are "
            "still attached and the checkpoint is refused"
        )
        raise WorkingCatalogError(message)
    row = connection.execute(MAIN_WAL_CHECKPOINT_TRUNCATE).fetchone()
    result = (int(row[0]), int(row[1]), int(row[2]))
    if result != (0, 0, 0):
        message = (
            f"{MAIN_WAL_CHECKPOINT_TRUNCATE} reported (busy, log_frames, checkpointed) = "
            f"{result}; a stage boundary requires exactly (0, 0, 0) -- every frame folded and "
            "the log truncated -- and anything else is refused rather than read as progress"
        )
        raise WorkingCatalogError(message)
    return result


def normalized_wal_bytes(catalog_path: Path) -> int:
    """The post-checkpoint write-ahead log length, normalized -- D151-C31R2-R19A-C2 §30 step 13.

    An absent log and a zero-length log are the same clean boundary and both normalize to
    ``0``. A nonzero log after a TRUNCATE checkpoint is a refusal: it means a frame was written
    after the checkpoint, and a stage receipt that bound ``0`` over it would be a lie.

    Raises:
        WorkingCatalogError: the log path is a symbolic link, is not a regular file, or is
            nonzero.
    """
    wal = catalog_path.with_name(catalog_path.name + "-wal")
    if wal.is_symlink():
        message = f"{wal.name!r} is a symbolic link; a world's write-ahead log is never a link"
        raise WorkingCatalogError(message)
    if not os.path.lexists(wal):
        return 0
    if not wal.is_file():
        message = f"{wal.name!r} exists and is not a regular file; refused"
        raise WorkingCatalogError(message)
    length = wal.stat().st_size
    if length != 0:
        message = (
            f"the write-ahead log {wal.name!r} holds {length} bytes after the stage checkpoint; "
            "a stage boundary normalizes only an absent or zero-length log to 0, and a nonzero "
            "log is refused rather than bound as clean"
        )
        raise WorkingCatalogError(message)
    return 0


def promote_world_directory(attempt: Path, canonical: Path) -> None:
    """Promote a complete initialization attempt to the absent canonical world path, atomically.

    D151-C31R2-R19A-C2 §28. The attempt directory was built beside its destination on the same
    filesystem, so the promotion is one ``rename`` of a directory onto a name that does not
    exist -- which POSIX makes atomic: a crash leaves either the attempt where it was or the
    canonical world complete, never a half-moved tree. Before the rename every regular file
    inside the attempt and the attempt directory itself are fsynced, so the bytes the rename
    exposes under the canonical name are durable; after it the canonical world's parent
    directory is fsynced, so the rename itself survives a crash rather than merely being
    visible to the running kernel.

    Nothing is ever overwritten: an existing canonical path -- a directory, a file, a link, or
    anything at all -- refuses before the rename, and a directory that is missing, is a link or
    lies in another directory refuses as well.

    Raises:
        WorkingCatalogError: the attempt is not a real directory beside the canonical path, or
            the canonical path already exists.
    """
    if attempt.is_symlink() or not attempt.is_dir():
        message = (
            f"initialization attempt {attempt.name!r} is not a real directory and is never promoted"
        )
        raise WorkingCatalogError(message)
    if attempt.parent != canonical.parent:
        message = (
            "a world is promoted by one rename inside one directory so it is atomic; "
            f"{attempt.parent} and {canonical.parent} are different"
        )
        raise WorkingCatalogError(message)
    if os.path.lexists(canonical):
        message = (
            f"the canonical world {canonical.name!r} already exists; a canonical world is "
            "create-once and is NEVER overwritten by a later attempt -- the attempt is left "
            "exactly where it is"
        )
        raise WorkingCatalogError(message)
    for dirpath, _dirnames, filenames in os.walk(attempt):
        for name in sorted(filenames):
            _fsync_file(Path(dirpath) / name)
    _fsync_directory(attempt)
    attempt.rename(canonical)
    _fsync_directory(canonical.parent)


# --------------------------------------------------------------------------- #
# D151-C31R2-R19B-C2: WAL observation, the wal-index reader and statement journals
# --------------------------------------------------------------------------- #
#: The statement-journal contract: one create-once, append-only, canonical-line file per
#: material statement execution of one durable Level-Two stage attempt.
STATEMENT_JOURNAL_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-journal/1"

#: The contract every journal event line carries.
STATEMENT_EVENT_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-event/1"

#: The largest encoded event line a journal accepts; an oversize event is an instrumentation
#: failure and interrupts the statement rather than being truncated or dropped.
STATEMENT_EVENT_MAX_BYTES: Final = 4096

#: The previous-event identity of a journal's first event.
JOURNAL_GENESIS_IDENTITY: Final = "0" * 64

EVENT_STATEMENT_START: Final = "STATEMENT_START"
EVENT_STATEMENT_SAMPLE: Final = "STATEMENT_SAMPLE"
EVENT_STATEMENT_END: Final = "STATEMENT_END"
EVENT_STATEMENT_ERROR: Final = "STATEMENT_ERROR"
EVENT_WATCHDOG_ABORT: Final = "WATCHDOG_ABORT"
STATEMENT_EVENT_KINDS: Final[tuple[str, ...]] = (
    EVENT_STATEMENT_START,
    EVENT_STATEMENT_SAMPLE,
    EVENT_STATEMENT_END,
    EVENT_STATEMENT_ERROR,
    EVENT_WATCHDOG_ABORT,
)
#: The kinds that end a journal; a journal is sealed only after one of them.
TERMINAL_EVENT_KINDS: Final[frozenset[str]] = frozenset(
    {EVENT_STATEMENT_END, EVENT_STATEMENT_ERROR, EVENT_WATCHDOG_ABORT}
)
#: The event keys the writer owns; a body carrying one of them is refused.
_RESERVED_EVENT_KEYS: Final[frozenset[str]] = frozenset(
    {"contract", "event_kind", "sequence", "previous_event_identity", "event_identity"}
)
JOURNAL_OPEN_MODE: Final = 0o600
JOURNAL_SEALED_MODE: Final = 0o444

JOURNAL_SEALED_SUCCESS: Final = "SEALED_SUCCESS"
JOURNAL_SEALED_FAILURE: Final = "SEALED_FAILURE"
JOURNAL_INCOMPLETE: Final = "INCOMPLETE"
JOURNAL_MALFORMED: Final = "MALFORMED"
JOURNAL_ABSENT: Final = "ABSENT"

JOURNAL_AUTHENTIC: Final = "AUTHENTIC"
JOURNAL_MISSING: Final = "MISSING"
JOURNAL_CHANGED: Final = "CHANGED"

#: The SQLite write-ahead log format: a 32-byte header, then frames of 24-byte header plus one
#: page. The magic selects the checksum byte order; the version is fixed.
WAL_HEADER_BYTES: Final = 32
WAL_FRAME_HEADER_BYTES: Final = 24
WAL_MAGIC_VALUES: Final[frozenset[int]] = frozenset({0x377F0682, 0x377F0683})
WAL_FORMAT_VERSION: Final = 3007000
#: Every page size SQLite accepts: the powers of two from 512 to 65536.
SQLITE_PAGE_SIZES: Final[frozenset[int]] = frozenset(1 << power for power in range(9, 17))

WAL_STATE_ABSENT: Final = "WAL_ABSENT"
WAL_STATE_ZERO: Final = "WAL_ZERO"
WAL_STATE_NONZERO: Final = "WAL_NONZERO"

#: The wal-index (``-shm``) header: two identical 48-byte copies, host byte order --
#: iVersion, unused, iChange, isInit, bigEndCksum, szPage, mxFrame, nPage, aFrameCksum[2],
#: aSalt[2], aCksum[2]. ``mxFrame`` counts the frames a committed transaction made valid.
_WAL_INDEX_HEADER_BYTES: Final = 48
_WAL_INDEX_HEADER_FORMAT: Final = "=IIIBBHIIIIIIII"


def require_sqlite_page_size(value: object) -> int:
    """An exact SQLite page size -- ``type(value) is int`` and one of the accepted sizes.

    Raises:
        WorkingCatalogError: the value is a bool, not an int, or not a SQLite page size.
    """
    if type(value) is not int or value not in SQLITE_PAGE_SIZES:
        message = (
            f"expected_page_size_bytes must be one of the SQLite page sizes "
            f"{sorted(SQLITE_PAGE_SIZES)}; got {value!r}"
        )
        raise WorkingCatalogError(message)
    return value


@dataclass(frozen=True, slots=True)
class WalObservation:
    """One bounded observation of a write-ahead log: state, bytes and conservative frames."""

    state: str
    byte_length: int
    page_size: int
    frame_size: int
    complete_frames: int
    trailing_bytes: int
    conservative_frames: int
    header_page_size: int | None
    checkpoint_sequence: int | None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "state": self.state,
            "byte_length": self.byte_length,
            "page_size": self.page_size,
            "frame_size": self.frame_size,
            "complete_frames": self.complete_frames,
            "trailing_bytes": self.trailing_bytes,
            "conservative_frames": self.conservative_frames,
            "header_page_size": self.header_page_size,
            "checkpoint_sequence": self.checkpoint_sequence,
        }


def observe_wal(wal_path: Path, *, expected_page_size: int) -> WalObservation:
    """The pure bounded WAL observation -- D151-C31R2-R19B-C2 §35.

    Absent and zero-length logs carry zero frames. A nonzero log must hold at least the
    32-byte header, whose magic, format version and declared page size are authenticated
    against ``expected_page_size`` -- the exact frame stride is ``page_size + 24``. The frame
    count is conservative: every complete frame counts, and a trailing partial frame counts as
    one more. Nothing here reads a frame header, so the cost never scales with the log.

    Raises:
        WorkingCatalogError: the log is a link or not a regular file, is shorter than its
            header, or its header is not a WAL header declaring the expected page size.
    """
    page_size = require_sqlite_page_size(expected_page_size)
    frame_size = page_size + WAL_FRAME_HEADER_BYTES
    try:
        status = os.lstat(wal_path)
    except FileNotFoundError:
        return WalObservation(WAL_STATE_ABSENT, 0, page_size, frame_size, 0, 0, 0, None, None)
    if stat.S_ISLNK(status.st_mode):
        message = f"{wal_path.name!r} is a symbolic link; a write-ahead log is never a link"
        raise WorkingCatalogError(message)
    if not stat.S_ISREG(status.st_mode):
        message = f"{wal_path.name!r} exists and is not a regular file; refused"
        raise WorkingCatalogError(message)
    length = int(status.st_size)
    if length == 0:
        return WalObservation(WAL_STATE_ZERO, 0, page_size, frame_size, 0, 0, 0, None, None)
    if length < WAL_HEADER_BYTES:
        message = (
            f"{wal_path.name!r} holds {length} bytes, fewer than the {WAL_HEADER_BYTES}-byte "
            "header a nonzero write-ahead log must carry; its boundary cannot be authenticated"
        )
        raise WorkingCatalogError(message)
    with wal_path.open("rb") as handle:
        header = handle.read(WAL_HEADER_BYTES)
    if len(header) != WAL_HEADER_BYTES:
        message = f"{wal_path.name!r} header could not be read completely; refused"
        raise WorkingCatalogError(message)
    magic = int.from_bytes(header[0:4], "big")
    version = int.from_bytes(header[4:8], "big")
    header_page_size = int.from_bytes(header[8:12], "big")
    checkpoint_sequence = int.from_bytes(header[12:16], "big")
    if magic not in WAL_MAGIC_VALUES or version != WAL_FORMAT_VERSION:
        message = (
            f"{wal_path.name!r} does not carry a SQLite write-ahead log header (magic "
            f"{magic:#x}, version {version}); refused"
        )
        raise WorkingCatalogError(message)
    if header_page_size != page_size:
        message = (
            f"{wal_path.name!r} declares page size {header_page_size} where the StagePlan "
            f"expects {page_size}; the frame boundary cannot be derived and is refused"
        )
        raise WorkingCatalogError(message)
    complete, trailing = divmod(length - WAL_HEADER_BYTES, frame_size)
    return WalObservation(
        state=WAL_STATE_NONZERO,
        byte_length=length,
        page_size=page_size,
        frame_size=frame_size,
        complete_frames=complete,
        trailing_bytes=trailing,
        conservative_frames=complete + (1 if trailing else 0),
        header_page_size=header_page_size,
        checkpoint_sequence=checkpoint_sequence,
    )


def wal_index_committed_frames(shm_path: Path) -> int:
    """The number of committed, valid frames the wal-index reports -- ``mxFrame``.

    SQLite's own recovery writes this header when a connection opens over a log: it counts
    exactly the frames a committed transaction made valid, and it does not move while an
    uncommitted transaction appends frames. Read from the ``-shm`` file after a writer has
    opened, it answers the one question the file length cannot: whether any of a nonzero log
    is committed content.

    Raises:
        WorkingCatalogError: the wal-index is absent, a link, not a regular file, too short,
            its two header copies disagree, or it is not an initialized version-3007000 header.
    """
    try:
        status = os.lstat(shm_path)
    except FileNotFoundError as exc:
        message = f"{shm_path.name!r} is absent; committed frames cannot be counted"
        raise WorkingCatalogError(message) from exc
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        message = f"{shm_path.name!r} is not a regular file; refused"
        raise WorkingCatalogError(message)
    if status.st_size < 2 * _WAL_INDEX_HEADER_BYTES:
        message = f"{shm_path.name!r} holds {status.st_size} bytes, too few for a wal-index header"
        raise WorkingCatalogError(message)
    with shm_path.open("rb") as handle:
        payload = handle.read(2 * _WAL_INDEX_HEADER_BYTES)
    first = payload[:_WAL_INDEX_HEADER_BYTES]
    second = payload[_WAL_INDEX_HEADER_BYTES : 2 * _WAL_INDEX_HEADER_BYTES]
    if first != second:
        message = f"{shm_path.name!r} carries two different wal-index header copies; refused"
        raise WorkingCatalogError(message)
    fields = struct.unpack(_WAL_INDEX_HEADER_FORMAT, first)
    version, is_init, mx_frame = int(fields[0]), int(fields[3]), int(fields[6])
    if version != WAL_FORMAT_VERSION or is_init != 1:
        message = (
            f"{shm_path.name!r} is not an initialized version-{WAL_FORMAT_VERSION} wal-index "
            f"(version {version}, isInit {is_init}); refused"
        )
        raise WorkingCatalogError(message)
    return mx_frame


def _canonical_line(document: Mapping[str, object]) -> bytes:
    """UTF-8, sorted keys, compact separators, no NaN or Infinity, one trailing newline.

    The estate's one canonical serialization, restated here so this module stays free of any
    other module's name; the identity of a record is the SHA-256 over exactly these bytes.
    """
    try:
        rendered = json.dumps(
            document, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False
        )
    except (TypeError, ValueError) as exc:
        message = f"a journal event holds a value JSON cannot represent: {exc}"
        raise WorkingCatalogError(message) from exc
    return rendered.encode("utf-8") + b"\n"


def _event_identity(event: Mapping[str, object]) -> str:
    body = {key: value for key, value in event.items() if key != "event_identity"}
    return hashlib.sha256(_canonical_line(body)).hexdigest()


class StatementJournalWriter:
    """One create-once, append-only statement journal -- D151-C31R2-R19B-C2 §27.

    Created ``O_CREAT | O_EXCL | O_WRONLY | O_APPEND`` at mode 0600 with one link; every event
    is one canonical JSON line carrying its sequence, the previous event's identity and its own
    recomputed identity, appended and fsynced before the call returns; sealing fsyncs, closes,
    sets mode 0444, fsyncs the parent directory and returns the final SHA-256 and byte length.
    A crash leaves a 0600 file with no terminal event and possibly a partial last line, which
    the reader classifies as incomplete and never repairs.
    """

    __slots__ = (
        "_byte_length",
        "_descriptor",
        "_last_kind",
        "_path",
        "_sealed",
        "_sequence",
        "_tip",
    )

    def __init__(self, path: Path, descriptor: int) -> None:
        self._path = path
        self._descriptor: int | None = descriptor
        self._sequence = 0
        self._tip = JOURNAL_GENESIS_IDENTITY
        self._byte_length = 0
        self._sealed = False
        self._last_kind: str | None = None

    @classmethod
    def create(cls, path: Path) -> StatementJournalWriter:
        """Create the journal exactly once.

        Raises:
            WorkingCatalogError: the parent is not a real directory, the path already exists
                (as anything), or the created file is not a regular single-link file.
        """
        parent = path.parent
        if parent.is_symlink() or not parent.is_dir():
            message = f"journal parent {parent.name!r} is not a real directory; refused"
            raise WorkingCatalogError(message)
        if os.path.lexists(path):
            message = (
                f"journal {path.name!r} already exists; a statement journal is create-once and a "
                "later attempt uses a new path"
            )
            raise WorkingCatalogError(message)
        try:
            descriptor = os.open(
                path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_APPEND, JOURNAL_OPEN_MODE
            )
        except OSError as exc:
            message = f"journal {path.name!r} could not be created: {exc}"
            raise WorkingCatalogError(message) from exc
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            os.close(descriptor)
            message = f"journal {path.name!r} is not a regular single-link file; refused"
            raise WorkingCatalogError(message)
        return cls(path, descriptor)

    @property
    def path(self) -> Path:
        """Where the journal lives."""
        return self._path

    @property
    def sequence(self) -> int:
        """The next event's sequence number: the number of events appended so far."""
        return self._sequence

    @property
    def tip(self) -> str:
        """The identity of the last appended event, or the genesis identity."""
        return self._tip

    @property
    def byte_length(self) -> int:
        """The bytes appended so far."""
        return self._byte_length

    @property
    def sealed(self) -> bool:
        """Whether :meth:`seal` completed."""
        return self._sealed

    def append(self, kind: str, body: Mapping[str, object]) -> str:
        """Append one event, fsynced before returning; return its identity.

        Raises:
            WorkingCatalogError: the journal is sealed or abandoned, the kind is unknown, the
                body carries a reserved key, the encoded line exceeds the bound, or the write
                or fsync fails.
        """
        if self._descriptor is None:
            message = f"journal {self._path.name!r} is closed; no event can be appended"
            raise WorkingCatalogError(message)
        if kind not in STATEMENT_EVENT_KINDS:
            message = f"journal event kind {kind!r} is not one this build writes"
            raise WorkingCatalogError(message)
        if self._last_kind in TERMINAL_EVENT_KINDS:
            message = f"journal {self._path.name!r} already holds a terminal event; refused"
            raise WorkingCatalogError(message)
        reserved = sorted(_RESERVED_EVENT_KEYS & set(body))
        if reserved:
            message = f"a journal event body may not carry the reserved keys {reserved}"
            raise WorkingCatalogError(message)
        event: dict[str, object] = {
            "contract": STATEMENT_EVENT_CONTRACT,
            "event_kind": kind,
            "sequence": self._sequence,
            "previous_event_identity": self._tip,
            **body,
        }
        identity = _event_identity(event)
        event["event_identity"] = identity
        line = _canonical_line(event)
        if len(line) > STATEMENT_EVENT_MAX_BYTES:
            message = (
                f"a journal event encodes to {len(line)} bytes where at most "
                f"{STATEMENT_EVENT_MAX_BYTES} are admitted; refused"
            )
            raise WorkingCatalogError(message)
        try:
            view = memoryview(line)
            while view:
                written = os.write(self._descriptor, view)
                view = view[written:]
            os.fsync(self._descriptor)
        except OSError as exc:
            message = f"journal {self._path.name!r} could not be appended: {exc}"
            raise WorkingCatalogError(message) from exc
        self._sequence += 1
        self._tip = identity
        self._byte_length += len(line)
        self._last_kind = kind
        return identity

    def seal(self) -> tuple[str, int]:
        """Seal the journal after its terminal event: fsync, close, 0444, fsync parent, digest.

        Raises:
            WorkingCatalogError: no terminal event was appended, or a step fails.
        """
        if self._descriptor is None:
            message = f"journal {self._path.name!r} is closed and cannot be sealed"
            raise WorkingCatalogError(message)
        if self._last_kind not in TERMINAL_EVENT_KINDS:
            message = f"journal {self._path.name!r} has no terminal event and cannot be sealed"
            raise WorkingCatalogError(message)
        descriptor = self._descriptor
        try:
            os.fsync(descriptor)
            os.close(descriptor)
            self._descriptor = None
            self._path.chmod(JOURNAL_SEALED_MODE)
            _fsync_directory(self._path.parent)
        except OSError as exc:
            self._descriptor = None
            message = f"journal {self._path.name!r} could not be sealed: {exc}"
            raise WorkingCatalogError(message) from exc
        sha256, length = file_digest(self._path)
        if length != self._byte_length:
            message = (
                f"journal {self._path.name!r} holds {length} bytes where {self._byte_length} "
                "were appended; refused"
            )
            raise WorkingCatalogError(message)
        self._sealed = True
        return sha256, length

    def abandon(self) -> None:
        """Close the descriptor without sealing: the journal stays 0600 and incomplete."""
        if self._descriptor is not None:
            with suppress(OSError):
                os.close(self._descriptor)
            self._descriptor = None


@dataclass(frozen=True, slots=True)
class StatementJournalReading:
    """What one journal on disk says, classified without repair."""

    name: str
    status: str
    events: tuple[Mapping[str, object], ...]
    terminal_kind: str | None
    tip_identity: str
    sha256: str | None
    byte_length: int | None
    mode: int | None
    partial_tail_bytes: int
    detail: str

    @property
    def successful(self) -> bool:
        """Whether this journal records one sealed, successful execution."""
        return self.status == JOURNAL_SEALED_SUCCESS


def read_statement_journal(path: Path) -> StatementJournalReading:
    """Read and classify one journal: sealed success, sealed failure, incomplete or malformed.

    Every complete line must be a canonical event whose sequence, previous identity and own
    identity chain exactly; bytes after the last newline are a partial tail; a journal whose
    last event is not terminal, or that was never sealed to mode 0444, is incomplete. Nothing
    is repaired, truncated or appended.
    """
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return StatementJournalReading(
            path.name,
            JOURNAL_ABSENT,
            (),
            None,
            JOURNAL_GENESIS_IDENTITY,
            None,
            None,
            None,
            0,
            "absent",
        )
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        return StatementJournalReading(
            path.name,
            JOURNAL_MALFORMED,
            (),
            None,
            JOURNAL_GENESIS_IDENTITY,
            None,
            None,
            None,
            0,
            "not a regular file",
        )
    payload = path.read_bytes()
    mode = status.st_mode & 0o7777
    sha256 = hashlib.sha256(payload).hexdigest()
    pieces = payload.split(b"\n")
    tail = pieces[-1]
    events: list[Mapping[str, object]] = []
    tip = JOURNAL_GENESIS_IDENTITY

    def malformed(detail: str) -> StatementJournalReading:
        return StatementJournalReading(
            path.name,
            JOURNAL_MALFORMED,
            tuple(events),
            None,
            tip,
            sha256,
            len(payload),
            mode,
            len(tail),
            detail,
        )

    for index, raw in enumerate(pieces[:-1]):
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return malformed(f"line {index} is not decodable JSON")
        if not isinstance(decoded, dict):
            return malformed(f"line {index} is not a JSON object")
        event: Mapping[str, object] = decoded
        if (
            event.get("contract") != STATEMENT_EVENT_CONTRACT
            or event.get("event_kind") not in STATEMENT_EVENT_KINDS
            or event.get("sequence") != index
            or event.get("previous_event_identity") != tip
        ):
            return malformed(
                f"line {index} does not chain (contract, kind, sequence or predecessor)"
            )
        identity = event.get("event_identity")
        if identity != _event_identity(event) or _canonical_line(event) != raw + b"\n":
            return malformed(f"line {index} is not its own canonical identity")
        tip = str(identity)
        events.append(event)
    if tail:
        return StatementJournalReading(
            path.name,
            JOURNAL_INCOMPLETE,
            tuple(events),
            None,
            tip,
            sha256,
            len(payload),
            mode,
            len(tail),
            "partial final line",
        )
    if not events:
        return StatementJournalReading(
            path.name, JOURNAL_INCOMPLETE, (), None, tip, sha256, len(payload), mode, 0, "no event"
        )
    last_kind = str(events[-1]["event_kind"])
    if last_kind not in TERMINAL_EVENT_KINDS:
        return StatementJournalReading(
            path.name,
            JOURNAL_INCOMPLETE,
            tuple(events),
            None,
            tip,
            sha256,
            len(payload),
            mode,
            0,
            "no terminal event",
        )
    if mode != JOURNAL_SEALED_MODE:
        return StatementJournalReading(
            path.name,
            JOURNAL_INCOMPLETE,
            tuple(events),
            last_kind,
            tip,
            sha256,
            len(payload),
            mode,
            0,
            "terminal event present but the journal was never sealed",
        )
    status_label = (
        JOURNAL_SEALED_SUCCESS if last_kind == EVENT_STATEMENT_END else JOURNAL_SEALED_FAILURE
    )
    return StatementJournalReading(
        path.name,
        status_label,
        tuple(events),
        last_kind,
        tip,
        sha256,
        len(payload),
        mode,
        0,
        "sealed",
    )


def authenticate_statement_journal(
    path: Path, *, expected_sha256: str, expected_byte_length: int
) -> str:
    """Whether a sealed journal still holds exactly the bound bytes: authentic, missing, changed."""
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return JOURNAL_MISSING
    if stat.S_ISLNK(status.st_mode) or not stat.S_ISREG(status.st_mode):
        return JOURNAL_CHANGED
    if status.st_size != expected_byte_length:
        return JOURNAL_CHANGED
    sha256, length = file_digest(path)
    if length != expected_byte_length or sha256 != expected_sha256:
        return JOURNAL_CHANGED
    return JOURNAL_AUTHENTIC
