"""One chunk, in one operating-system process, over one ordinal interval -- D151-C1 §§2, 6, 7.

**The process boundary is the mechanism, not a description of one.** A chunk runs in a child
process this module starts; that process parses its interval, closes every handle, writes its
create-once terminal receipt LAST, and **exits**. The parent then proves the child is gone
before the next chunk begins. There is no same-process continuation, no sleeping worker, no
stop/continue signal pair, no resident coordinator holding a chunk database open, and no
garbage-collection substitute: the memory a chunk used is reclaimed because the process that
held it ended, which is the only mechanism that reclaims it.

**A chunk consumes its interval and nothing else.** The interval is a half-open range over the
canonical governed member ordering
(:mod:`~disclosure_drift.m3.chunk_plan`), and the members are read by exact name through the
accepted named-member reader. A chunk never enumerates the archive for work, never continues
past its end, and never touches another chunk's world or the future consolidated world.

**Every parse call below is the accepted one.** ``parse_submissions_document``,
``parse_historical_submissions``, ``_declare_shard_parents``, ``_resolve_shard_parent``,
``CompactSourceEvidence`` and ``CensusCatalog.persist_streamed`` are reached exactly as
``offline_parse`` reaches them. This module is a second *entry point* over a restricted member
range; it is never a second parser and never a second catalog writer.

**The two regions, and the barrier between them.** Accepted Decision 129 §7 parses every
historical shard *after* the primary traversal, against a parent map every primary document
contributed to. A primary chunk therefore emits its own declaration contribution and parses no
shard; the union of those contributions is the complete map; and a shard chunk consumes that
map. The barrier is the accepted contract expressed as an ordinal property, not a new rule.

**Nothing here authorizes a real chunked F0.**
:data:`REAL_CHUNKED_F0_EXECUTION_AUTHORITY` is ``None``, no command-line surface reaches this
module, no environment variable is consulted, and :func:`require_real_chunk_execution_authority`
refuses on every call. A synthetic chunk over a bounded fixture is engineering evidence; it is
not an authorization and it never becomes one.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_phases import execution_identity
from disclosure_drift.m3.canary_runtime import process_peak_resident_bytes
from disclosure_drift.m3.chunk_evidence import (
    CHUNK_DECLARATIONS_FILENAME,
    CHUNK_PLAN_FILENAME,
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    CHUNK_WITNESS_FILENAME,
    ChunkEvidenceError,
    ChunkReceipt,
    SemanticSummary,
    build_artifact_manifest,
    read_receipt_document,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.chunk_plan import (
    REGION_PRIMARY,
    REGION_SHARD,
    CanonicalMember,
    ChunkPlan,
    chunk_by_id,
    resolve_chunk_members,
    verify_source_identity,
)
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    GOVERNED_ACCESSION_FIELDS,
    CompactEvidenceSidecar,
    materialized_fields,
)
from disclosure_drift.m3.offline_parse import (
    _BULK_PARSER_ID,
    CompactSourceEvidence,
    OfflineParseError,
    _declare_shard_parents,
    _json_document,
    _observations_by_id,
    _resolve_shard_parent,
    classify_planned_source,
    select_planned_source,
    write_containment,
)
from disclosure_drift.m3.working_catalog import WorkingCatalog, file_digest
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.archive import ArchiveDefenceError, iter_named_members
from disclosure_drift.sec.census import CensusCatalog
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.submissions import (
    HistoricalFileReference,
    parse_submissions_document,
)
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import utc_now

__all__ = [
    "CHUNK_EXECUTION_CONTRACT",
    "CHUNK_REQUEST_FILENAME",
    "F0_WRITTEN_TABLES",
    "REAL_CHUNKED_F0_EXECUTION_AUTHORITY",
    "ChunkExecutionError",
    "ChunkRequest",
    "attempt_directory",
    "chunk_execution_identity",
    "completed_chunk_receipt",
    "execute_chunk_body",
    "merge_parent_map",
    "next_attempt_directory",
    "read_declarations",
    "run_chunk",
    "table_row_counts",
    "require_real_chunk_execution_authority",
]


class ChunkExecutionError(DisclosureDriftError):
    """A chunk-execution precondition failed. Never worked around, never retried in place."""


#: This execution shape's own contract identity, folded into every execution identity.
CHUNK_EXECUTION_CONTRACT: Final = "m3.3-chunked-f0-execution/1"

#: The filename a chunk request is handed to a child process under.
CHUNK_REQUEST_FILENAME: Final = "chunk_request.json"

#: The governed token authorizing one **real** chunked F0 over a complete governed source.
#:
#: ``None`` means real chunked execution is **not enabled**, and D151-C1 §24 keeps it that way:
#: C1 engineers, falsifies and benchmarks the architecture and authorizes no run of it. Every
#: real-execution entry point calls :func:`require_real_chunk_execution_authority` and refuses.
#:
#: There is deliberately **no command-line surface** that reaches this module at all, so the
#: closure is structural rather than conditional: there is no invocation to guard. No operator
#: flag, environment variable, configuration key, plan, receipt or passing test substitutes for
#: this constant, and a later owner instrument replaces **only** this literal in a reviewed
#: change.
REAL_CHUNKED_F0_EXECUTION_AUTHORITY: Final[str | None] = None

#: The eleven durable tables an F0 over the governed bulk source writes.
#:
#: A strict subset of the accepted sixteen-table
#: :data:`~disclosure_drift.m3.offline_parse.E0_PERMITTED_TABLES` footprint: the calendar and SIC
#: reference tables belong to other sources, and the two resolution tables and the canonical
#: relation belong to F1 and F2. Stated explicitly because the consolidator's merge strategy is
#: defined table by table, and a table nobody classified is a table nobody merged.
F0_WRITTEN_TABLES: Final[tuple[str, ...]] = (
    "census_parser_runs",
    "census_parsed_records",
    "census_quarantined_records",
    "census_structural_observations",
    "census_registrants",
    "census_registrant_observations",
    "census_candidate_lineage_edges",
    "census_accessions",
    "census_accession_observations",
    "census_historical_references",
    "census_malformed_historical_references",
)

#: The accession record class prefix the first-witness rule keys on. The same prefix
#: ``CompactSourceEvidence.absorb`` and ``CensusCatalog._normalize_record`` both test.
_ACCESSION_PREFIX: Final = "accession:"

#: The chunk-local first-witness ledger's schema. Run-local: no migration, no accepted-schema
#: change, and it never reaches a catalog (D151-C1 §25).
_WITNESS_SCHEMA: Final = """
CREATE TABLE IF NOT EXISTS chunk_first_witness (
    native_identity     TEXT PRIMARY KEY,
    member_ordinal      INTEGER NOT NULL,
    record_ordinal      INTEGER NOT NULL,
    delta_materialized  INTEGER NOT NULL CHECK (delta_materialized >= 0)
) STRICT;

CREATE TABLE IF NOT EXISTS chunk_witness_meta (
    key                 TEXT PRIMARY KEY,
    value               TEXT NOT NULL
) STRICT;
"""

#: The bootstrap the child process runs. Deliberately **not** a console script, a module
#: ``__main__``, or a subcommand: a chunk child is an internal execution mechanism, and giving
#: it a name an operator could type would be exactly the activation surface §24 forbids.
_CHILD_BOOTSTRAP: Final = (
    "import sys;"
    "from disclosure_drift.m3.chunk_execution import _child_main;"
    "sys.exit(_child_main(sys.argv[1]))"
)

_DIRECTORY_MODE: Final = 0o700


def require_real_chunk_execution_authority() -> str:
    """The governed token authorizing one real chunked F0, or a refusal -- D151-C1 §24.

    Raises:
        ChunkExecutionError: :data:`REAL_CHUNKED_F0_EXECUTION_AUTHORITY` is ``None``, which is
            its D151-C1 state and the only state this record leaves it in.
    """
    granted = REAL_CHUNKED_F0_EXECUTION_AUTHORITY
    if granted is None:
        message = (
            "real chunked-F0 execution is NOT AUTHORIZED: "
            "REAL_CHUNKED_F0_EXECUTION_AUTHORITY is None. D151-C1 engineers, falsifies and "
            "benchmarks this architecture and authorizes no run of it. There is no operator "
            "flag, environment variable, configuration key, chunk plan, receipt, passing test "
            "or command-line surface that substitutes for this constant -- no command-line "
            "surface reaches this module at all -- and a real run needs both a new owner "
            "instrument and a reviewed source change"
        )
        raise ChunkExecutionError(message)
    return granted


def chunk_execution_identity(
    *,
    plan: ChunkPlan,
    chunk_id: str,
    batch_size: int,
    cache_bytes: int | None,
    repository_head_sha: str,
    repository_tree_sha: str,
    catalog_source_sha256: str,
    migration_head: int,
) -> str:
    """Digest the frozen values that govern how one chunk executes.

    Folded into the chunk receipt so that a consolidator can refuse a chunk produced under
    different governing values without comparing seventeen fields, and so that two chunks of one
    plan can be proved to have run under the same ones.
    """
    return execution_identity(
        {
            "chunk_execution_contract": CHUNK_EXECUTION_CONTRACT,
            "chunk_id": chunk_id,
            "plan_digest": plan.plan_digest,
            "member_order_digest": plan.member_order_digest,
            "evidence_contract": COMPACT_EVIDENCE_CONTRACT,
            "compact_evidence": bool(COMPACT_EVIDENCE),
            "parser_id": _BULK_PARSER_ID,
            "parser_version": SOURCES[plan.source_id].parser_version,
            "batch_size": batch_size,
            "cache_bytes": cache_bytes,
            "repository_head_sha": repository_head_sha,
            "repository_tree_sha": repository_tree_sha,
            "catalog_source_sha256": catalog_source_sha256,
            "migration_head": migration_head,
        }
    )


@dataclass(frozen=True, slots=True)
class ChunkRequest:
    """Everything one chunk child process is given, and the only thing it is given.

    Serialized to JSON and handed to the child by path. The child re-derives every predicate
    from it rather than inheriting anything from the parent's memory: it re-reads the plan,
    re-derives the canonical ordering, re-authenticates the artifact, and re-selects the planned
    source. A successor process may never say *"the coordinator already checked this"*.

    ``abort_after_members`` and ``abort_mode`` are **fault injection**, and they are stated in
    the request rather than read from an environment variable so that they cannot be switched on
    from outside a caller that already holds the whole request. They can never enable anything:
    real execution is closed by :data:`REAL_CHUNKED_F0_EXECUTION_AUTHORITY`, and these only ever
    make a chunk stop earlier than it would have.
    """

    plan_path: str
    chunk_id: str
    attempt: int
    attempt_directory: str
    operational_catalog: str
    data_root: str
    source_instance_id: str
    batch_size: int
    cache_bytes: int | None
    repository_head_sha: str
    repository_tree_sha: str
    parent_map_path: str | None = None
    abort_after_members: int | None = None
    abort_mode: str = "raise"

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Paths are the caller's; nothing is discovered."""
        return {
            "plan_path": self.plan_path,
            "chunk_id": self.chunk_id,
            "attempt": self.attempt,
            "attempt_directory": self.attempt_directory,
            "operational_catalog": self.operational_catalog,
            "data_root": self.data_root,
            "source_instance_id": self.source_instance_id,
            "batch_size": self.batch_size,
            "cache_bytes": self.cache_bytes,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "parent_map_path": self.parent_map_path,
            "abort_after_members": self.abort_after_members,
            "abort_mode": self.abort_mode,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ChunkRequest:
        """Rebuild a request from its stored mapping.

        Raises:
            ChunkExecutionError: a field is absent or is not of the recorded type.
        """
        try:
            cache = record["cache_bytes"]
            abort = record["abort_after_members"]
            return cls(
                plan_path=str(record["plan_path"]),
                chunk_id=str(record["chunk_id"]),
                attempt=int(str(record["attempt"])),
                attempt_directory=str(record["attempt_directory"]),
                operational_catalog=str(record["operational_catalog"]),
                data_root=str(record["data_root"]),
                source_instance_id=str(record["source_instance_id"]),
                batch_size=int(str(record["batch_size"])),
                cache_bytes=None if cache is None else int(str(cache)),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                parent_map_path=(
                    None
                    if record.get("parent_map_path") is None
                    else str(record["parent_map_path"])
                ),
                abort_after_members=None if abort is None else int(str(abort)),
                abort_mode=str(record.get("abort_mode", "raise")),
            )
        except (KeyError, ValueError) as exc:
            message = f"a chunk request could not be read as this build writes them: {exc}"
            raise ChunkExecutionError(message) from exc


class _ChunkFaultInjected(Exception):  # noqa: N818 - a fault-injection signal, not an error type
    """Raised by the injected fault so an interrupted chunk is reachable deterministically."""


def attempt_directory(chunk_root: Path, chunk_id: str, attempt: int) -> Path:
    """Where one attempt at one chunk lives. Create-once, and never reused.

    Attempts are numbered rather than overwritten because D151-C1 §7 and §12 forbid deletion:
    a chunk that died leaves its partial world exactly as it is, for diagnosis, and the retry
    builds a **new** directory beside it. Nothing is renamed, cleaned, or reclaimed to make room.
    """
    return chunk_root / chunk_id / f"attempt-{attempt:03d}"


def next_attempt_directory(chunk_root: Path, chunk_id: str) -> tuple[Path, int]:
    """The lowest unused attempt directory for one chunk, and its ordinal.

    Raises:
        ChunkExecutionError: the chunk already carries a valid terminal receipt, so a further
            attempt would be a duplicate execution rather than a reconstruction.
    """
    existing = completed_chunk_receipt(chunk_root, chunk_id)
    if existing is not None:
        message = (
            f"chunk {chunk_id!r} already carries a valid terminal receipt (attempt "
            f"{existing[0].attempt}); a completed chunk is IMMUTABLE and is skipped, never "
            "re-executed. Re-running it would duplicate persistent output and overwrite the "
            "evidence of the execution that produced it"
        )
        raise ChunkExecutionError(message)
    attempt = 0
    while attempt_directory(chunk_root, chunk_id, attempt).exists():
        attempt += 1
    return attempt_directory(chunk_root, chunk_id, attempt), attempt


def _attempt_directories(chunk_root: Path, chunk_id: str) -> list[Path]:
    parent = chunk_root / chunk_id
    if not parent.is_dir():
        return []
    return sorted(path for path in parent.iterdir() if path.is_dir() and not path.is_symlink())


def completed_chunk_receipt(chunk_root: Path, chunk_id: str) -> tuple[ChunkReceipt, Path] | None:
    """The one valid terminal receipt this chunk carries, or ``None``.

    Every attempt directory is inspected and every receipt found is **verified against the
    artifacts it names** before it counts. A receipt whose artifacts moved is not a completed
    chunk; a chunk with two valid receipts is ambiguous authority and is refused rather than
    resolved by recency, attempt number, or modification time.

    Raises:
        ChunkExecutionError: more than one attempt carries a valid receipt.
    """
    found: list[tuple[ChunkReceipt, Path]] = []
    for directory in _attempt_directories(chunk_root, chunk_id):
        receipt_path = directory / CHUNK_RECEIPT_FILENAME
        if not receipt_path.is_file():
            continue
        try:
            receipt = ChunkReceipt.from_record(
                read_receipt_document(receipt_path, contract=CHUNK_RECEIPT_CONTRACT)
            )
            verify_artifact_manifest(directory, receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,))
        except ChunkEvidenceError:
            # An unreadable or unverifiable receipt is not a completed chunk. It is deliberately
            # not raised here: an abandoned attempt whose receipt was truncated must not stop the
            # coordinator from finding the attempt that genuinely finished. A receipt that
            # matters -- one a consolidator is asked to consume -- is verified there, where the
            # refusal is dispositive.
            continue
        if receipt.chunk_id != chunk_id or receipt.status != "complete":
            continue
        found.append((receipt, directory))
    if len(found) > 1:
        message = (
            f"chunk {chunk_id!r} carries {len(found)} valid terminal receipts, in "
            f"{[path.name for _, path in found]}. Duplicate authority is refused rather than "
            "resolved: nothing here ranks two completed executions of the same interval by "
            "attempt number, modification time, or size"
        )
        raise ChunkExecutionError(message)
    return found[0] if found else None


# --------------------------------------------------------------------------- #
# The restricted traversal
# --------------------------------------------------------------------------- #
@dataclass
class _WitnessLedger:
    """The chunk-local first-witness ledger -- the one cross-chunk correction input.

    ``CompactSourceEvidence`` decides ``first_witness`` from a set of accession identities the
    traversal has already met, which is a fact about the **whole source** and therefore wrong in
    a chunk that does not hold the whole source. The chunk cannot know the global answer, so it
    records what the consolidator needs to compute it: for every accession identity **this chunk
    saw first**, where it saw it and what the counters would become if a lower chunk saw it
    earlier.

    The rule mirrored here is the accepted one, three lines of it, and it calls the same
    :func:`~disclosure_drift.m3.compact_evidence.materialized_fields` the accepted absorber
    calls. It is proved equal rather than asserted: a single chunk covering the whole source
    must produce a ledger whose corrections are all zero.
    """

    connection: sqlite3.Connection
    seen: set[str]

    def observe(self, *, member_ordinal: int, outcome: ParseOutcome) -> None:
        """Record this member's first-witness contribution, in absorb order."""
        rows: list[tuple[str, int, int, int]] = []
        for ordinal, record in enumerate(outcome.records):
            identity = record.native_identity
            if not identity.startswith(_ACCESSION_PREFIX) or identity in self.seen:
                continue
            self.seen.add(identity)
            kept_first = len(materialized_fields(record.payload, first_witness=True))
            # The rival count is the accepted function's own ``not first_witness`` branch,
            # which keeps every governed field the payload carries and nothing else. It is
            # counted here rather than called for because this runs once per distinct accession
            # of the whole source -- measured at 0.045 ms per call, or roughly an hour over the
            # governed source -- and a second full call would double it for a six-element
            # membership test. A test asserts the two agree over a hostile payload set, so the
            # shortcut cannot drift away from the rule it restates.
            kept_rival = sum(1 for field in GOVERNED_ACCESSION_FIELDS if field in record.payload)
            rows.append((identity, member_ordinal, ordinal, kept_rival - kept_first))
        if rows:
            self.connection.executemany(
                "INSERT INTO chunk_first_witness (native_identity, member_ordinal, "
                "record_ordinal, delta_materialized) VALUES (?, ?, ?, ?)",
                rows,
            )


def _stream_chunk_members(
    *,
    store: SnapshotStore,
    observation: SourceObservation,
    archive_path: Path,
    members: Sequence[CanonicalMember],
    region: str,
    evidence: CompactSourceEvidence,
    ledger: _WitnessLedger,
    declared: dict[str, set[str]],
    shard_members: frozenset[str],
    parent_map: Mapping[str, set[str]] | None,
    abort_after_members: int | None,
    abort_mode: str,
) -> Iterator[tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]]:
    """Yield one parse outcome per member of **this chunk's interval**, holding none of them.

    The bounded-memory shape accepted Decision 110 §8 requires, restricted to an interval. Each
    member's bytes are read, parsed, absorbed and dropped before the next one is opened, exactly
    as the accepted whole-archive traversal does -- the reader is the accepted public
    named-member reader, so the per-member size, type and traversal defences are the same ones,
    reached through the same surface.

    **The cumulative-expansion cap is not re-applied from zero**, for the reason
    :func:`~disclosure_drift.sec.archive.iter_named_members` already states: comparing part of an
    archive against a whole-archive limit would refuse a healthy source. The per-member caps are
    applied to every member.

    Raises:
        OfflineParseError: a member's payload is not a decodable JSON object, the archive is
            refused by the archive defences, or a shard cannot be bound to exactly one parent.
        _ChunkFaultInjected: the injected fault fired.
    """
    names = [member.member_name for member in members]
    resolved: list[str] = []
    if region == REGION_SHARD:
        if parent_map is None:
            message = (
                "a shard chunk was started without the merged parent map. Accepted Decision 129 "
                "§7 binds a historical shard to whichever primary document declares it, and "
                "that document may sit in any chunk; a shard chunk therefore begins only after "
                "EVERY primary chunk has reached its terminal, and it is refused rather than "
                "resolved against a partial map"
            )
            raise ChunkExecutionError(message)
        # Every parent is resolved before any member is reopened, exactly as the accepted
        # deferred phase does: a refusal then costs no decompression and cannot leave half the
        # interval parsed and the other half refused.
        resolved = [_resolve_shard_parent(name, parent_map) for name in names]
    store.verify_payload(observation)
    processed = 0
    try:
        for index, (read_name, payload) in enumerate(iter_named_members(archive_path, names)):
            member = members[index]
            if read_name != member.member_name:  # pragma: no cover - the reader yields in order
                message = (
                    f"the named-member read returned {read_name!r} where {member.member_name!r} "
                    "was requested; the chunk is refused rather than parsed against the wrong "
                    "member"
                )
                raise ChunkExecutionError(message)
            location = RecordLocation(
                observation.observation_id,
                observation.source_id,
                member_name=member.member_name,
            )
            if region == REGION_PRIMARY:
                decoded = _json_document(payload, f"bulk member {member.member_name!r}")
                parsed = parse_submissions_document(decoded, location)
                _declare_shard_parents(declared, parsed[1], shard_members)
                outcome, references = parsed
            else:
                decoded = _json_document(payload, f"bulk historical shard {member.member_name!r}")
                outcome = parse_historical_submissions(
                    decoded, location, registrant_cik=resolved[index]
                )
                references = ()
            ledger.observe(member_ordinal=member.canonical_position, outcome=outcome)
            evidence.absorb(member.member_name, payload, outcome)
            yield outcome, references
            processed += 1
            if abort_after_members is not None and processed >= abort_after_members:
                _fire_fault(abort_mode, processed)
    except ArchiveDefenceError as exc:
        message = f"accepted bulk archive refused during a chunk read: {exc}"
        raise OfflineParseError(message) from exc


def _fire_fault(mode: str, processed: int) -> None:
    """Fire the injected fault. Never reached unless a caller put it in its own request."""
    if mode == "hard_exit":
        # A deterministic stand-in for a process the kernel took away: no unwinding, no
        # `finally`, no chance to write a receipt. Exactly the state D151-C1 §7 governs.
        os._exit(137)  # noqa: PLR1722 - the point is to leave no unwinding behind
    message = f"chunk fault injected after {processed} member(s)"
    raise _ChunkFaultInjected(message)


# --------------------------------------------------------------------------- #
# The chunk body -- runs INSIDE the child process
# --------------------------------------------------------------------------- #
def _open_witness_ledger(path: Path) -> sqlite3.Connection:
    """Open the chunk-local first-witness ledger, and open it for **bulk append**.

    Journalling and synchronous writes are both off, and every row lands in one transaction that
    commits when the chunk closes the ledger. That is sound rather than a shortcut: the ledger is
    a derived artifact whose only consumer is a consolidator, it is written once and never read
    back inside the chunk, and it counts for nothing unless the chunk's terminal receipt exists --
    which is written afterwards, over a manifest that includes this file's digest. A ledger lost
    to a crash therefore belongs to a chunk that has no receipt, which is already invalid.

    Measured on a hundred-member chunk of the synthetic source, the autocommit form spent 3.75 s
    of a 5.97 s chunk in one-transaction-per-member commits; this form spends about 0.05 s.
    """
    connection = sqlite3.connect(path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.executescript(_WITNESS_SCHEMA)
    connection.execute("BEGIN")
    return connection


def _close_witness_ledger(connection: sqlite3.Connection) -> None:
    """Commit the ledger's single transaction and close it, before anything hashes the file."""
    try:
        if connection.in_transaction:
            connection.execute("COMMIT")
    finally:
        connection.close()


def table_row_counts(connection: sqlite3.Connection) -> Mapping[str, int]:
    """Row counts for every table an F0 over the governed bulk source writes."""
    counts: dict[str, int] = {}
    for table in F0_WRITTEN_TABLES:
        row = connection.execute(f"SELECT COUNT(*) AS rows FROM {table}").fetchone()  # noqa: S608
        counts[table] = 0 if row is None else int(row["rows"])
    return counts


def read_declarations(path: Path) -> dict[str, set[str]]:
    """One chunk's shard-parent declaration contribution, read back.

    Raises:
        ChunkExecutionError: the document is absent, undecodable, or not the recorded shape.
    """
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        message = f"a chunk declaration contribution could not be read: {exc}"
        raise ChunkExecutionError(message) from exc
    if not isinstance(decoded, dict):
        message = "a chunk declaration contribution is not a JSON object and is refused"
        raise ChunkExecutionError(message)
    declared: dict[str, set[str]] = {}
    for name, parents in decoded.items():
        if not isinstance(parents, list):
            message = f"declaration entry {name!r} is not a list of parents and is refused"
            raise ChunkExecutionError(message)
        declared[str(name)] = {str(parent) for parent in parents}
    return declared


def merge_parent_map(contributions: Sequence[Mapping[str, set[str]]]) -> dict[str, set[str]]:
    """Union every primary chunk's contribution into the complete parent map.

    The accepted map is built by ``setdefault(name, set()).add(cik)`` over every primary
    document in the archive. A partition of those documents into chunks partitions the ``add``
    calls, so the union of the per-chunk maps is exactly the whole-archive map -- **set union is
    the composition rule, not an approximation of one**, and it is independent of the order the
    contributions are merged in.
    """
    merged: dict[str, set[str]] = {}
    for contribution in contributions:
        for name, parents in contribution.items():
            merged.setdefault(name, set()).update(parents)
    return merged


def execute_chunk_body(request: ChunkRequest) -> ChunkReceipt:  # noqa: PLR0915
    """Parse exactly one chunk's interval, and write its terminal receipt LAST.

    Every predicate is re-established here, in the process that will do the work: the plan is
    re-read and its digest recomputed, the canonical ordering is re-derived from the archive and
    proved to be the one the plan partitions, the artifact is re-authenticated by digest and
    length, and the planned source is re-selected through the accepted selector. Nothing is
    inherited from the coordinator's memory.

    Raises:
        ChunkExecutionError: any chunk-level precondition fails.
        ChunkPlanError: the plan or the archive's ordering is not the one this chunk belongs to.
        OfflineParseError: the accepted parse path refuses.
    """
    attempt_root = Path(request.attempt_directory)
    if attempt_root.exists():
        message = (
            f"chunk attempt directory {attempt_root.name!r} already exists; an attempt is "
            "create-once. A previous attempt is left exactly as it is and a retry builds a new "
            "directory beside it -- nothing is reused, repaired, cleaned, or deleted"
        )
        raise ChunkExecutionError(message)
    plan = ChunkPlan.from_record(_read_json_object(Path(request.plan_path), "chunk plan"))
    bounds = chunk_by_id(plan, request.chunk_id)
    operational_catalog = Path(request.operational_catalog)
    catalog_sha256, _ = file_digest(operational_catalog)
    tree = DataTree.from_root(Path(request.data_root))
    attempt_root.mkdir(mode=_DIRECTORY_MODE, parents=True)
    started = utc_now()
    rss_before = process_peak_resident_bytes()
    migration_head = 0

    with WorkingCatalog(
        operational_catalog, attempt_root, cache_bytes=request.cache_bytes
    ) as working:
        connection = working.connection
        migration_head = working.identity.migration_head
        selected = select_planned_source(connection, request.source_instance_id)
        if selected.source.source_id != plan.source_id:
            message = (
                f"planned source {request.source_instance_id!r} is "
                f"{selected.source.source_id!r} where the chunk plan partitions "
                f"{plan.source_id!r}; the chunk is refused rather than run against another source"
            )
            raise ChunkExecutionError(message)
        observations = _observations_by_id(connection)
        observation_id = selected.source.observation_id
        bound = None if observation_id is None else observations.get(observation_id)
        disposition = classify_planned_source(selected.source, bound)
        if disposition != "E0_REQUIRED_PARSE" or bound is None:
            message = (
                f"planned source {request.source_instance_id!r} classifies as {disposition!r}; "
                "a chunk parses only a source the accepted classification requires a parse of, "
                "and it is never substituted, fabricated, or turned into an empty result"
            )
            raise ChunkExecutionError(message)
        if bound.observation_id != plan.source_observation_id:
            message = (
                f"the planned source is bound to observation {bound.observation_id!r} where the "
                f"chunk plan records {plan.source_observation_id!r}"
            )
            raise ChunkExecutionError(message)
        store = SnapshotStore(tree)
        store.adopt(observations.values())
        archive_path = store.payload_path(bound)
        verify_source_identity(
            plan,
            observed_sha256=bound.logical_sha256 or "",
            observed_byte_length=int(bound.content_size_bytes or 0),
        )
        members = resolve_chunk_members(plan, archive_path, request.chunk_id)
        shard_names = frozenset(
            member.member_name for member in _all_shard_members(plan, archive_path)
        )
        parent_map = (
            None
            if request.parent_map_path is None
            else read_declarations(Path(request.parent_map_path))
        )
        sidecar = CompactEvidenceSidecar(attempt_root / "compact_evidence.sqlite3")
        witness_path = attempt_root / CHUNK_WITNESS_FILENAME
        witness = _open_witness_ledger(witness_path)
        declared: dict[str, set[str]] = {}
        evidence = CompactSourceEvidence(
            source_observation_id=bound.observation_id,
            source_id=bound.source_id,
            artifact_sha256=bound.logical_sha256 or "",
            artifact_byte_length=bound.content_size_bytes or 0,
            sidecar=sidecar,
            # The chunk's member ordinals are the CANONICAL ones, not zero-based within the
            # chunk. That is what makes two chunks' manifests mergeable without renumbering,
            # and what makes the completeness digest replayable in source order.
            members=bounds.start,
        )
        catalog = CensusCatalog(_ChunkWriter(working), compact_evidence=COMPACT_EVIDENCE)
        working.ledger.begin_source(selected.source.source_instance_id, selected.source.source_id)
        ledger = _WitnessLedger(connection=witness, seen=set())
        try:
            with write_containment(connection):
                result = catalog.persist_streamed(
                    _stream_chunk_members(
                        store=store,
                        observation=bound,
                        archive_path=archive_path,
                        members=members,
                        region=bounds.region,
                        evidence=evidence,
                        ledger=ledger,
                        declared=declared,
                        shard_members=shard_names,
                        parent_map=parent_map,
                        abort_after_members=request.abort_after_members,
                        abort_mode=request.abort_mode,
                    ),
                    parser_id=_BULK_PARSER_ID,
                    parser_version=SOURCES[bound.source_id].parser_version,
                    source_observation_id=bound.observation_id,
                    batch_size=request.batch_size,
                    checkpoint_batches=True,
                )
            completeness = evidence.finish()
            counts = table_row_counts(connection)
        finally:
            _close_witness_ledger(witness)
            sidecar.close()
        working.ledger.mark_parsed(
            selected.source.source_instance_id,
            parts=evidence.members - bounds.start,
            batches=result.parsed,
        )
        manifest_digest = sidecar_manifest_digest(
            attempt_root / "compact_evidence.sqlite3", bound.observation_id
        )
        summary = SemanticSummary(
            members=evidence.members - bounds.start,
            records=evidence.records,
            parsed_records=result.parsed,
            quarantined_records=result.quarantined,
            omitted_field_observations=evidence.omitted,
            materialized_field_observations=evidence.materialized,
            # A chunk never claims a source-level parser state: it did not establish one. The
            # source's terminal is decided once, by the consolidator, over every chunk.
            parser_state_after="chunk_local",
            run_outcome=result.run_outcome,
            table_row_counts=counts,
            member_manifest_digest=manifest_digest,
            projection_digest_chain=completeness,
        )
        if bounds.region == REGION_PRIMARY:
            write_once_json(
                attempt_root / CHUNK_DECLARATIONS_FILENAME,
                {name: sorted(parents) for name, parents in sorted(declared.items())},
            )
        write_once_json(attempt_root / CHUNK_PLAN_FILENAME, dict(plan.as_record()))

    # Every handle is closed before the manifest is taken: a hash of a database with a live
    # write-ahead log beside it is a hash of a file missing its committed tail.
    manifest = build_artifact_manifest(attempt_root, exclude=(CHUNK_RECEIPT_FILENAME,))
    receipt = ChunkReceipt(
        contract=CHUNK_RECEIPT_CONTRACT,
        chunk_id=bounds.chunk_id,
        region=bounds.region,
        start=bounds.start,
        end=bounds.end,
        plan_digest=plan.plan_digest,
        member_order_digest=plan.member_order_digest,
        source_instance_id=request.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        source_byte_length=plan.source_byte_length,
        repository_head_sha=request.repository_head_sha,
        repository_tree_sha=request.repository_tree_sha,
        execution_identity=chunk_execution_identity(
            plan=plan,
            chunk_id=bounds.chunk_id,
            batch_size=request.batch_size,
            cache_bytes=request.cache_bytes,
            repository_head_sha=request.repository_head_sha,
            repository_tree_sha=request.repository_tree_sha,
            catalog_source_sha256=catalog_sha256,
            migration_head=migration_head,
        ),
        attempt=request.attempt,
        pid=os.getpid(),
        rss_peak_bytes=_peak(rss_before),
        completed_at_utc=started,
        status="complete",
        manifest=manifest,
        summary=summary,
    )
    # LAST. Nothing is written after this, and nothing that fails before it leaves one.
    write_once_json(attempt_root / CHUNK_RECEIPT_FILENAME, dict(receipt.as_record()))
    return receipt


def _peak(before: int | None) -> int | None:
    observed = process_peak_resident_bytes()
    if observed is None:
        return before
    return observed


def sidecar_manifest_digest(path: Path, observation_id: str) -> str:
    """One chunk sidecar's member-manifest digest, read and closed."""
    sidecar = CompactEvidenceSidecar(path)
    try:
        return sidecar.member_manifest_digest(observation_id)
    finally:
        sidecar.close()


class _ChunkWriter(CatalogWriter):
    """The accepted writer type, bound to one chunk working catalog's already-open connection.

    Exactly the accepted Decision 116 binding, for exactly the accepted reason: the D111 working
    catalog owns its file and its single writing handle, and taking a second
    :class:`~disclosure_drift.storage.catalog.CatalogWriter` lease on the same file would open a
    second writing handle for a serialization guarantee the single owner already provides. It
    acquires no lease, opens nothing, and closes nothing, and the file it reads is a disposable
    chunk-local copy rather than the accepted catalog -- which stays strictly read-only on every
    path here.
    """

    def __init__(self, working: WorkingCatalog) -> None:
        super().__init__(working.path, working.path.parent)
        self._connection = working.connection


def _all_shard_members(plan: ChunkPlan, archive_path: Path) -> tuple[CanonicalMember, ...]:
    from disclosure_drift.m3.chunk_plan import (  # noqa: PLC0415 - narrow, call-time
        canonical_member_sequence,
    )

    return tuple(
        member
        for member in canonical_member_sequence(archive_path)
        if member.region == REGION_SHARD
    )


def _read_json_object(path: Path, label: str) -> Mapping[str, object]:
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        message = f"the {label} at {path.name!r} could not be read: {exc}"
        raise ChunkExecutionError(message) from exc
    if not isinstance(decoded, dict):
        message = f"the {label} at {path.name!r} is not a JSON object and is refused"
        raise ChunkExecutionError(message)
    return decoded


# --------------------------------------------------------------------------- #
# The coordinator half -- runs in the PARENT process
# --------------------------------------------------------------------------- #
def _child_main(request_path: str) -> int:
    """The child process's entry point. Not a command; there is no surface that names it."""
    request = ChunkRequest.from_record(_read_json_object(Path(request_path), "chunk request"))
    execute_chunk_body(request)
    return 0


def _require_process_dead(pid: int) -> None:
    """Refuse to continue while the predecessor chunk's process is still alive -- §29 C11.

    The child has already been reaped by the time this runs, so a live process at that
    identifier would mean the chunk did not end. A reaped identifier can in principle be reused
    by the operating system, which this cannot distinguish and does not claim to: the check is
    stated as what it is, one of three independent proofs the predecessor ended, beside the
    process object's own exit status and the receipt's recorded pid.
    """
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return
    except PermissionError:  # pragma: no cover - a reused pid owned by another user
        pass
    message = (
        f"the previous chunk's process {pid} is still live. A chunk process must END before "
        "its successor begins -- that ending is the whole mechanism by which the memory it "
        "used is reclaimed. There is no same-process continuation, no suspended worker, and no "
        "garbage-collection substitute"
    )
    raise ChunkExecutionError(message)


def run_chunk(
    request: ChunkRequest,
    *,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> ChunkReceipt:
    """Run one chunk in a **fresh child process**, and prove that process ended.

    Four properties, and each of them is checked rather than described:

    1. the predecessor chunk's process is **dead** before this one is started;
    2. the chunk runs in a process that is **not this one** -- the receipt records its pid;
    3. the child **exits**, and its exit status is inspected;
    4. the receipt exists, verifies against its own artifacts, and describes this chunk.

    Raises:
        ChunkExecutionError: the predecessor is alive, the child failed, the child left no
            receipt, or the receipt does not describe this chunk.
    """
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    attempt_root = Path(request.attempt_directory)
    attempt_root.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = attempt_root.parent / f"{request.chunk_id}-{request.attempt:03d}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    if observe is not None:
        observe("CHUNK_PROCESS_START")
    completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed bootstrap, no shell
        [sys.executable, "-c", _CHILD_BOOTSTRAP, str(request_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if observe is not None:
        observe("CHUNK_PROCESS_EXIT")
    if completed.returncode != 0:
        message = (
            f"chunk {request.chunk_id!r} attempt {request.attempt} ended with exit status "
            f"{completed.returncode} and is NOT complete. Nothing was cleaned, deleted, or "
            f"retried in place, and no terminal receipt exists for it. stderr tail: "
            f"{completed.stderr.strip()[-800:]!r}"
        )
        raise ChunkExecutionError(message)
    receipt_path = attempt_root / CHUNK_RECEIPT_FILENAME
    receipt = ChunkReceipt.from_record(
        read_receipt_document(receipt_path, contract=CHUNK_RECEIPT_CONTRACT)
    )
    verify_artifact_manifest(attempt_root, receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,))
    if receipt.chunk_id != request.chunk_id or receipt.attempt != request.attempt:
        message = (
            f"the receipt in {attempt_root.name!r} describes chunk {receipt.chunk_id!r} attempt "
            f"{receipt.attempt}, not {request.chunk_id!r} attempt {request.attempt}"
        )
        raise ChunkExecutionError(message)
    if receipt.pid == os.getpid():
        message = (
            "the chunk receipt records THIS process's pid, so the chunk did not run in a "
            "separate operating-system process. A chunk that ran in the coordinator would "
            "reclaim nothing when it 'ended'"
        )
        raise ChunkExecutionError(message)
    _require_process_dead(receipt.pid)
    return receipt
