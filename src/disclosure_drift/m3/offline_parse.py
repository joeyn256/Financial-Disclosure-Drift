"""The bounded offline metadata parse driver (M3.3 contract §10.2; **R13**–**R18**).

This is the offline **seam** accepted Decision 067 §3 (GR-C1) identified as the one
missing capability: the existing parsers are already pure over materialized content,
and payload loading, archive traversal, and ``CensusCatalog`` persistence are already
offline-capable — what did not exist was an entry point that drives them without an
orchestrator, a client, or a transport.

It is therefore deliberately **not** a second parser and **not** a second catalog
writer. Every parse call below is the same pure function
``sec/census_orchestrator.py`` calls, and every write goes through the same
``CensusCatalog``.

What this module refuses, structurally rather than by convention:

* **No transport.** It imports no client, no transport, and no socket module, and
  :data:`PROHIBITED_IMPORT_PREFIXES` is asserted against its own transitive imports.
* **No source discovery.** Every object is reached through
  ``census_plan_sources.observation_id`` and nothing else — never by ``source_id``
  alone, recency, retrieval time, object size, filesystem path, or operator choice
  (**R13**; contract §8.1 correction 2). That binding is what disambiguates the two
  bulk-submissions objects.
* **No write outside the accepted footprint.** A SQLite authorizer refuses, at
  statement-prepare time, any write to a table outside :data:`E0_PERMITTED_TABLES`,
  and any ``census_plan_sources`` update of a column other than ``parser_state``
  (**R17**).
* **No fabrication.** A source accepted as failed or unavailable stays failed or
  unavailable; it is never replaced, substituted, or turned into an empty parse
  result (**R14**; contract §8.1 correction 3).

**Executing this driver against the real private catalog is M3.3-E0, a separate owner
gate that this module does not and cannot supply.** Nothing here — no return value, no
token, no successful run — is an authorization.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from collections.abc import Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, fields
from typing import ClassVar, Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.accession_resolution import AUTHORITY_LEVEL, authority_for_source
from disclosure_drift.sec.archive import ArchiveDefenceError, iter_members

# ``_stable_id`` is the accepted census identifier convention. It is imported rather
# than reimplemented so exactly one derivation of an accession-observation identity
# exists in the repository (M3.3 contract §20: no second persistence implementation).
from disclosure_drift.sec.census import CensusCatalog, _stable_id
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.observation_catalog import load_observations
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation, merge_outcomes
from disclosure_drift.sec.parsers.full_index import parse_company_index
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.sic import parse_sic_reference
from disclosure_drift.sec.parsers.submissions import (
    HistoricalFileReference,
    parse_submissions_document,
)
from disclosure_drift.sec.parsers.tickers import (
    parse_company_tickers,
    parse_company_tickers_exchange,
)
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = [
    "CANDIDATE_SUBSTANTIVE_SOURCE_IDS",
    "E0_PERMITTED_PLAN_COLUMNS",
    "E0_PERMITTED_TABLES",
    "E0_PROHIBITED_TABLES",
    "FULL_INDEX_MEMBERSHIP_FIELDS",
    "FULL_INDEX_MEMBERSHIP_SOURCE_IDS",
    "PROHIBITED_IMPORT_PREFIXES",
    "STREAMED_SOURCE_IDS",
    "SUBMISSIONS_MEMBERSHIP_FIELDS",
    "SUBMISSIONS_MEMBERSHIP_SOURCE_IDS",
    "VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS",
    "AssociationTotality",
    "OfflineParseError",
    "OfflineParseReport",
    "PlannedSource",
    "SourceLayerPhase",
    "PlannedSourceOutcome",
    "SourceDisposition",
    "classify_planned_source",
    "load_planned_sources",
    "materialize_census_associations",
    "materialize_source_layer",
    "membership_observation_sources",
    "run_offline_metadata_parse",
    "unavailable_source_ids",
    "write_containment",
]


class OfflineParseError(DisclosureDriftError):
    """An offline-parse fail-closed condition. Never worked around, never retried."""


SourceDisposition = Literal[
    "E0_REQUIRED_PARSE",
    "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE",
    "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY",
]
"""**R18** report-level vocabulary. No database enum, no schema change, no migration."""

#: The complete **sixteen**-table durable write footprint. **R17** originally fixed
#: fifteen: the nine census parse-layer tables plus the six companion tables the same
#: reusable persistence path unavoidably and legitimately writes. Accepted
#: **Decision 094 §6.1** narrowly amends R17 by adding exactly one more —
#: ``census_accession_registrants``, the later accepted **Decision 083 R58** canonical
#: relation whose writer migration ``0014`` assigns to this driver. That is an explicit
#: one-table widening forced by a later accepted decision, not a general permission to
#: widen E0: adding anything else still needs a new owner ruling.
E0_PERMITTED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "census_parser_runs",
        "census_parsed_records",
        "census_structural_observations",
        "census_accessions",
        "census_accession_observations",
        "census_accession_registrants",
        "census_registrants",
        "census_registrant_observations",
        "census_accession_field_resolutions",
        "census_accession_cohort_resolutions",
        "census_quarantined_records",
        "census_historical_references",
        "census_malformed_historical_references",
        "census_candidate_lineage_edges",
        "census_calendar_days",
        "reference_sic_codes",
    }
)

#: The one further write **R17** permits, and the only column of it: the accepted
#: ``parser_state`` lifecycle transition, for category-A sources only.
E0_PERMITTED_PLAN_COLUMNS: Final[Mapping[str, frozenset[str]]] = {
    "census_plan_sources": frozenset({"parser_state"}),
}

#: Named explicitly so a negative assertion can be written against them rather than
#: inferred from the permitted set's complement (**R17** §3.2; contract §10.2 item 2).
E0_PROHIBITED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "census_qa_metrics",
        "census_index_instances",
        "census_index_reconciliation",
        "census_index_instance_events",
        "census_index_retrieval_accounting",
        "census_source_observations",
        "census_observation_reasons",
        "census_archive_members",
        "ops_ingestion_jobs",
        "pilot_candidate_snapshots",
        "pilot_candidate_entities",
        "pilot_candidate_accessions",
    }
)

#: Import prefixes that would give this module a network capability. Asserted against
#: the module's own transitive imports by test, not merely promised (contract §10.2
#: item 8: "proved by test, not asserted").
PROHIBITED_IMPORT_PREFIXES: Final[tuple[str, ...]] = (
    "disclosure_drift.sec.http_client",
    "disclosure_drift.sec.httpx_transport",
    "disclosure_drift.sec.transport",
    "disclosure_drift.sec.rate_limit",
    "disclosure_drift.sec.index_retrieval",
    "disclosure_drift.sec.census_orchestrator",
    "disclosure_drift.m3.acquisition",
    "httpx",
    "http",
    "socket",
    "ssl",
    "urllib",
)

#: Sources whose parser output the authoritative candidate builder substantively uses
#: (accepted OR-2 mapping §§D.2-D.6, §E). Category **A** when the accepted source is
#: usable, category **B** when it is accepted as failed or unavailable.
#:
#: ``sec_full_index_company`` is here by **R22** (Decision 072 §2), correcting the
#: Decision 068 §4 disposition. ``company.idx`` emits one row per registrant per
#: accession, and grouping those rows by canonical accession is the accepted M2.3 way to
#: establish co-registrants -- the submissions documents alone cannot. The earlier
#: category-C reading was implementation-shaped: it followed the historical orchestrator
#: routing the parsed rows only at ``census_index_*``, which **R25** forbids as a basis
#: for disposition. Accepted methodology, not current routing, decides.
CANDIDATE_SUBSTANTIVE_SOURCE_IDS: Final[frozenset[str]] = frozenset(
    {
        "sec_bulk_submissions",
        "sec_submissions_entity",
        "sec_submissions_historical",
        "sec_company_tickers",
        "sec_company_tickers_exchange",
        "sec_sic_code_list",
        "sec_full_index_company",
    }
)

#: Category **C**, each established by a forward trace rather than by assumption
#: (**R25**, Decision 072 §5; calendar-source recheck, Decision 071 §7):
#:
#: * the dated calendar announcement has no parse destination on the reusable path;
#: * the annual filing calendar parses into ``census_calendar_days``, whose **only**
#:   readers are ``sec/census.py``'s calendar QA metrics -- reached solely through the
#:   orchestrator-only ``qa_metrics()`` entry point R17 excludes from E0. No candidate
#:   column derives from it: ``acceptance_audit_date`` comes from
#:   ``census_accessions.acceptance_date_sec``, which ``sec/temporal.acceptance_date_sec``
#:   takes from the first eight characters of the raw SEC value with no calendar lookup
#:   and no timezone conversion, because the SEC calendar date is definitional rather
#:   than derived. Its parsed output therefore reaches no authoritative candidate field
#:   and no required freeze provenance.
VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS: Final[frozenset[str]] = frozenset(
    {
        "sec_edgar_calendar_announcement",
        "sec_edgar_filing_calendar",
    }
)

#: **Decision 094 §6.2** -- the sources whose plan-bound accepted usable observations
#: contribute ``S_submissions``. A submissions document states the registrant of its own
#: filings; it cannot by itself state a co-registrant.
SUBMISSIONS_MEMBERSHIP_SOURCE_IDS: Final[frozenset[str]] = frozenset(
    {
        "sec_bulk_submissions",
        "sec_submissions_entity",
        "sec_submissions_historical",
    }
)

#: **Decision 094 §6.2** -- the source whose plan-bound accepted usable observations
#: contribute ``S_full_index``. ``company.idx`` emits one row per registrant per
#: accession, so it is the only accepted evidence that a filing is joint.
FULL_INDEX_MEMBERSHIP_SOURCE_IDS: Final[frozenset[str]] = frozenset({"sec_full_index_company"})

#: The persisted ``census_accession_observations.field_name`` values each side reads.
#: Both are canonical membership fields; neither is a company name, ticker, filename,
#: source order, row order, or proximity heuristic, all of which are prohibited.
SUBMISSIONS_MEMBERSHIP_FIELDS: Final[tuple[str, ...]] = ("cik", "cik_padded")
FULL_INDEX_MEMBERSHIP_FIELDS: Final[tuple[str, ...]] = ("cik_padded",)

#: The two Decision 012 fields whose resolution must be ``resolved`` or
#: ``resolved_by_correction`` with ``blocks_dependents = 0`` before an accession's
#: substantive association set may be called established (**Decision 094 §6.2** item 5).
_MEMBERSHIP_BLOCKING_FIELDS: Final[tuple[str, ...]] = ("form", "official_filing_date")

_RESOLVED_STATUSES: Final[frozenset[str]] = frozenset({"resolved", "resolved_by_correction"})

#: Migration ``0014``'s relation vocabulary, restated where this writer uses it.
_SUBSTANTIVE: Final = "substantive"
_ESTABLISHED: Final = "established"
_UNESTABLISHED: Final = "unestablished"

_USABLE_RETRIEVAL_STATES: Final[frozenset[str]] = frozenset({"retrieved", "reused"})
_UNAVAILABLE_RETRIEVAL_STATES: Final[frozenset[str]] = frozenset(
    {"not_retrieved", "failed", "blocked", "unavailable", "unknown", "quarantined"}
)

_WRITE_ACTIONS: Final[frozenset[int]] = frozenset(
    {
        sqlite3.SQLITE_INSERT,
        sqlite3.SQLITE_UPDATE,
        sqlite3.SQLITE_DELETE,
    }
)


@dataclass(frozen=True, slots=True)
class PlannedSource:
    """One accepted ``census_plan_sources`` row, read and never rewritten."""

    census_run_id: str
    source_instance_id: str
    source_id: str
    request_identity: str
    required: bool
    source_scope: str
    retrieval_state: str
    snapshot_state: str
    parser_state: str
    observation_id: str | None


@dataclass(frozen=True, slots=True)
class PlannedSourceOutcome:
    """Exactly one **R18** disposition for one planned source, and what came of it."""

    source_instance_id: str
    source_id: str
    disposition: SourceDisposition
    parser_run_id: str | None = None
    parsed_records: int = 0
    quarantined_records: int = 0
    parser_state_before: str = "not_started"
    parser_state_after: str = "not_started"
    already_present: bool = False
    detail: str = ""

    @property
    def touched(self) -> bool:
        """Whether E0 changed anything at all for this source."""
        return self.parser_run_id is not None or self.parser_state_after != self.parser_state_before


@dataclass(frozen=True, slots=True)
class AssociationTotality:
    """**Decision 094 §9.5** -- the closed association-totality object, exactly.

    Six of the fifteen counts are invariants rather than measurements: a violated one is
    a totality failure, never a reportable state. The first three counts must partition
    every census accession, and **no assertion is made that all accessions are
    established** -- ``unestablished`` is a lawful, expected, fail-closed outcome.
    """

    census_accession_count: int = 0
    established_accession_count: int = 0
    unestablished_accession_count: int = 0
    substantive_relation_count: int = 0
    established_zero_relation_count: int = 0
    established_singleton_count: int = 0
    established_multi_count: int = 0
    singleton_scalar_mismatch_count: int = 0
    multi_nonnull_scalar_count: int = 0
    orphan_relation_count: int = 0
    invalid_cik_rendering_count: int = 0
    association_provenance_failure_count: int = 0
    submissions_member_missing_full_index_count: int = 0
    unbindable_registrant_member_count: int = 0
    unestablished_membership_conflict_count: int = 0

    #: The six counts §9.5 fixes at zero. Named so a validator states which invariant
    #: failed rather than reporting a generic mismatch.
    MUST_BE_ZERO: ClassVar[tuple[str, ...]] = (
        "established_zero_relation_count",
        "singleton_scalar_mismatch_count",
        "multi_nonnull_scalar_count",
        "orphan_relation_count",
        "invalid_cik_rendering_count",
        "association_provenance_failure_count",
    )

    def as_record(self) -> dict[str, int]:
        """The §9.5 object as a plain mapping, in the record's declared key order."""
        return {field.name: int(getattr(self, field.name)) for field in fields(self)}

    def violations(self) -> tuple[str, ...]:
        """Every §9.5 invariant this totality breaks, in declaration order."""
        broken = [name for name in self.MUST_BE_ZERO if int(getattr(self, name)) != 0]
        if (
            self.established_accession_count + self.unestablished_accession_count
            != self.census_accession_count
        ):
            broken.append("census_accession_count")
        if self.established_singleton_count + self.established_multi_count != (
            self.established_accession_count
        ):
            broken.append("established_accession_count")
        return tuple(broken)

    def require(self) -> None:
        """Raise unless every §9.5 invariant holds.

        Raises:
            OfflineParseError: an invariant the accepted totality fixes was broken.
        """
        broken = self.violations()
        if not broken:
            return
        message = (
            "census association totality failed its Decision 094 §9.5 invariants: "
            f"{', '.join(broken)}"
        )
        raise OfflineParseError(message)


@dataclass(frozen=True, slots=True)
class OfflineParseReport:
    """The E0 completeness proof: one disposition per planned source, and the counts."""

    outcomes: tuple[PlannedSourceOutcome, ...]
    accession_resolutions: int
    #: **R23** -- accession observations materialized from stored ``company.idx`` rows.
    full_index_registrant_observations: int = 0
    #: Accessions the index listed that the authoritative layer does not carry. Reported
    #: as a diagnostic and never created (**R23** §5.1).
    full_index_unbound_accessions: tuple[str, ...] = ()
    #: **Decision 094 §§6.2-6.4, 9.5** -- the canonical relation's totality.
    association_totality: AssociationTotality = AssociationTotality()
    #: Persisted membership observations each side of §6.2's set definition read.
    submissions_membership_observations: int = 0
    substantive_membership_observations: int = 0
    requests_made: int = 0
    transports_constructed: int = 0

    def by_disposition(self, disposition: SourceDisposition) -> tuple[PlannedSourceOutcome, ...]:
        """Every outcome carrying one disposition, in plan order."""
        return tuple(item for item in self.outcomes if item.disposition == disposition)

    @property
    def planned_source_count(self) -> int:
        """How many planned sources were enumerated."""
        return len(self.outcomes)

    @property
    def is_complete(self) -> bool:
        """Whether every planned source received exactly one disposition."""
        instances = [item.source_instance_id for item in self.outcomes]
        return len(instances) == len(set(instances))

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free and identity-free report mapping."""
        return {
            "planned_sources": self.planned_source_count,
            "required_parse": len(self.by_disposition("E0_REQUIRED_PARSE")),
            "required_but_accepted_unavailable": len(
                self.by_disposition("E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE")
            ),
            "not_required_validation_or_provenance_only": len(
                self.by_disposition("E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY")
            ),
            "accession_resolutions": self.accession_resolutions,
            "full_index_registrant_observations": self.full_index_registrant_observations,
            "full_index_unbound_accessions": len(self.full_index_unbound_accessions),
            "submissions_membership_observations": self.submissions_membership_observations,
            "substantive_membership_observations": self.substantive_membership_observations,
            "association_totality": self.association_totality.as_record(),
            "requests_made": self.requests_made,
            "transports_constructed": self.transports_constructed,
        }


def load_planned_sources(connection: sqlite3.Connection) -> tuple[PlannedSource, ...]:
    """Read every accepted planned source, in a deterministic order.

    The order is the plan's own composite key, so two runs enumerate identically. It
    is **not** a selection mechanism: which object each row binds to is
    ``observation_id`` alone.
    """
    rows = connection.execute(
        "SELECT census_run_id, source_instance_id, source_id, request_identity, required, "
        "source_scope, retrieval_state, snapshot_state, parser_state, observation_id "
        "FROM census_plan_sources ORDER BY census_run_id, source_instance_id"
    ).fetchall()
    return tuple(
        PlannedSource(
            census_run_id=str(row["census_run_id"]),
            source_instance_id=str(row["source_instance_id"]),
            source_id=str(row["source_id"]),
            request_identity=str(row["request_identity"]),
            required=bool(row["required"]),
            source_scope=str(row["source_scope"]),
            retrieval_state=str(row["retrieval_state"]),
            snapshot_state=str(row["snapshot_state"]),
            parser_state=str(row["parser_state"]),
            observation_id=None if row["observation_id"] is None else str(row["observation_id"]),
        )
        for row in rows
    )


def classify_planned_source(
    source: PlannedSource,
    observation: SourceObservation | None,
) -> SourceDisposition:
    """Assign **exactly one R18 disposition**, deterministically, or fail closed.

    The rule reads the plan row's accepted state and the bound observation's accepted
    outcome. It never consults recency, size, path, or operator preference, and an
    unclassifiable source is refused rather than defaulted.
    """
    if source.source_id in VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS:
        return "E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY"
    if source.source_id not in CANDIDATE_SUBSTANTIVE_SOURCE_IDS:
        message = (
            f"planned source {source.source_instance_id!r} has unclassifiable source id "
            f"{source.source_id!r}: it is neither candidate-substantive nor "
            "validation-or-provenance-only under the accepted OR-2 mapping. E0 refuses "
            "rather than assigning a default disposition."
        )
        raise OfflineParseError(message)
    if source.retrieval_state in _UNAVAILABLE_RETRIEVAL_STATES:
        return "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
    if source.retrieval_state not in _USABLE_RETRIEVAL_STATES:
        message = (
            f"planned source {source.source_instance_id!r} carries unrecognized "
            f"retrieval_state {source.retrieval_state!r}"
        )
        raise OfflineParseError(message)
    if source.observation_id is None:
        message = (
            f"planned source {source.source_instance_id!r} is accepted as "
            f"{source.retrieval_state!r} but binds no observation_id. The plan row is "
            "the only permitted disambiguator, so no substitute object may be chosen."
        )
        raise OfflineParseError(message)
    if observation is None:
        message = (
            f"planned source {source.source_instance_id!r} binds observation "
            f"{source.observation_id!r}, which is not in the accepted catalog. "
            "No observation is fabricated and no alternative is selected."
        )
        raise OfflineParseError(message)
    if not observation.is_usable or not observation.has_payload:
        return "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
    if source.snapshot_state != "verified":
        return "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
    return "E0_REQUIRED_PARSE"


@contextmanager
def write_containment(
    connection: sqlite3.Connection,
    *,
    permitted_tables: frozenset[str] = E0_PERMITTED_TABLES,
    permitted_columns: Mapping[str, frozenset[str]] = E0_PERMITTED_PLAN_COLUMNS,
) -> Iterator[None]:
    """Refuse, at statement-prepare time, any write outside the **R17** footprint.

    A SQLite authorizer is used rather than post-hoc inspection because it fires
    *before* the statement runs: a prohibited write never reaches the file, so the
    containment proof does not depend on noticing damage afterwards.
    """

    def authorizer(action: int, arg1: str | None, arg2: str | None, *_: object) -> int:
        if action not in _WRITE_ACTIONS:
            return sqlite3.SQLITE_OK
        table = arg1 or ""
        if table in permitted_tables:
            return sqlite3.SQLITE_OK
        allowed = permitted_columns.get(table)
        if (
            allowed is not None
            and action == sqlite3.SQLITE_UPDATE
            and arg2 is not None
            and arg2 in allowed
        ):
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY

    connection.set_authorizer(authorizer)
    try:
        yield
    finally:
        connection.set_authorizer(None)


def _observations_by_id(
    connection: sqlite3.Connection,
) -> Mapping[str, SourceObservation]:
    """Index the accepted observations by their own identifier.

    ``load_observations`` is the accepted reader; this only keys its result. Nothing
    here ranks, filters by recency, or prefers a larger object.
    """
    return {item.observation_id: item for item in load_observations(connection)}


def _payload_bytes(store: SnapshotStore, observation: SourceObservation) -> bytes:
    """Load and integrity-verify one accepted stored object, offline."""
    store.verify_payload(observation)
    return store.load_payload(observation)


def _json_document(payload: bytes, label: str) -> Mapping[str, object]:
    """Decode one stored JSON object, failing closed on malformed content."""
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"{label} stored payload is not decodable JSON: {exc}"
        raise OfflineParseError(message) from exc
    if not isinstance(decoded, dict):
        message = f"{label} stored payload is not a JSON object"
        raise OfflineParseError(message)
    return decoded


def _historical_registrant_cik(
    connection: sqlite3.Connection, observation: SourceObservation
) -> str:
    """Resolve the registrant a historical submissions object belongs to.

    Read from the accepted ``census_historical_references`` evidence, matched on the
    file the bound observation actually requested. A missing or ambiguous match fails
    closed: the CIK is never guessed, and the document is never re-retrieved to find
    out (contract §8.1 correction 4).
    """
    historical_file = observation.requested_url.rsplit("/", 1)[-1]
    rows = connection.execute(
        "SELECT DISTINCT registrant_cik_padded FROM census_historical_references "
        "WHERE historical_file = ? ORDER BY registrant_cik_padded",
        (historical_file,),
    ).fetchall()
    if len(rows) != 1:
        message = (
            f"historical submissions object {historical_file!r} resolves to "
            f"{len(rows)} accepted registrant references; exactly one is required and "
            "no registrant is inferred"
        )
        raise OfflineParseError(message)
    try:
        return normalize_cik(str(rows[0]["registrant_cik_padded"]))[1]
    except IdentifierError as exc:
        message = f"accepted historical reference carries an invalid registrant CIK: {exc}"
        raise OfflineParseError(message) from exc


#: The run-level parser identity one bulk-archive traversal writes, whether it is streamed
#: into the catalog or merged first. Named once because ``persist_streamed`` is handed it
#: directly, where the merged path used to read it off the merged outcome.
_BULK_PARSER_ID: Final = "submissions-json"


def _stream_bulk_submissions(
    store: SnapshotStore, observation: SourceObservation
) -> Iterator[tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]]:
    """Yield one parse outcome per accepted bulk-archive member, offline, holding none of them.

    The **bounded-memory** traversal accepted Decision 110 §8 requires, and the reason it is a
    generator rather than a list. The accepted first planned source is a 1.56 GB archive of
    985,834 JSON members that expand to 5.71 GB and parse to roughly 22.5 million records; the
    previous implementation materialised every member and every member's outcome before
    persisting any of them, which measured 92.6 KB retained per member and was what the kernel
    killed at 33.9 GB after 63 minutes without one durable source boundary (D109 finding F1).

    Member handling is unchanged -- the same defences, the same decoder, the same pure parser,
    in the same order. What changed is only that each member's outcome leaves this function
    immediately and nothing accumulates behind it.

    Raises:
        OfflineParseError: the archive is refused by the archive defences, or a member's
            payload is not a decodable JSON object.
    """
    store.verify_payload(observation)
    path = store.payload_path(observation)
    try:
        for member in iter_members(
            path,
            name_suffix=".json",
            archive_relative_path=observation.relative_storage_path,
            archive_sha256=observation.logical_sha256,
        ):
            location = RecordLocation(
                observation.observation_id,
                observation.source_id,
                member_name=member.name,
            )
            decoded = _json_document(member.payload, f"bulk member {member.name!r}")
            yield parse_submissions_document(decoded, location)
    except ArchiveDefenceError as exc:
        message = f"accepted bulk archive refused by the archive defences: {exc}"
        raise OfflineParseError(message) from exc


def _parse_bulk_submissions(
    store: SnapshotStore, observation: SourceObservation
) -> tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]:
    """Traverse the accepted bulk archive and parse each member, offline, merging the result.

    Identical member handling to the accepted orchestrator path, minus retrieval. This is the
    **merged** form of :func:`_stream_bulk_submissions`, and it retains every member's records:
    it is correct only where the archive is small enough to hold, which is true of a synthetic
    fixture and false of the accepted first planned source. E0's own driver therefore streams
    (see :func:`materialize_source_layer`); this stays as the total per-source parse path
    :func:`_parse_source` promises, so a caller that legitimately wants one outcome still has
    one, derived from the same traversal rather than a second implementation of it.
    """
    version = SOURCES["sec_bulk_submissions"].parser_version
    outcomes: list[ParseOutcome] = []
    references: list[HistoricalFileReference] = []
    for outcome, member_references in _stream_bulk_submissions(store, observation):
        outcomes.append(outcome)
        references.extend(member_references)
    return merge_outcomes(_BULK_PARSER_ID, version, outcomes), tuple(references)


def _parse_source(
    connection: sqlite3.Connection,
    store: SnapshotStore,
    observation: SourceObservation,
) -> tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]:
    """Dispatch one accepted stored object to its accepted pure parser.

    Every branch is the same function the accepted orchestrator calls. No branch
    constructs a client, and no branch reaches the network.
    """
    source_id = observation.source_id
    location = RecordLocation(observation.observation_id, source_id)
    if source_id == "sec_bulk_submissions":
        return _parse_bulk_submissions(store, observation)
    payload = _payload_bytes(store, observation)
    if source_id == "sec_submissions_entity":
        decoded = _json_document(payload, "entity submissions document")
        outcome, references = parse_submissions_document(decoded, location)
        return outcome, references
    if source_id == "sec_submissions_historical":
        decoded = _json_document(payload, "historical submissions document")
        cik = _historical_registrant_cik(connection, observation)
        return parse_historical_submissions(decoded, location, registrant_cik=cik), ()
    if source_id == "sec_company_tickers":
        return parse_company_tickers(_json_document(payload, "company tickers"), location), ()
    if source_id == "sec_company_tickers_exchange":
        decoded = _json_document(payload, "company tickers exchange")
        return parse_company_tickers_exchange(decoded, location), ()
    if source_id == "sec_sic_code_list":
        return parse_sic_reference(payload.decode("utf-8", "replace"), location), ()
    if source_id == "sec_full_index_company":
        return parse_company_index(payload.decode("utf-8", "replace"), location), ()
    message = (
        f"source {source_id!r} is classified candidate-substantive but has no accepted "
        "offline parse path; E0 refuses rather than inventing one"
    )
    raise OfflineParseError(message)


#: Native-identity prefix the accepted full-index parser stamps on every data row.
_INDEX_ROW_PREFIX: Final = "index_row:"

#: The full-index native fields Decision 012 already maps to canonical accession fields.
#: ``cik_padded`` is the one that establishes registrant membership (**R23** §5.2);
#: ``form_type`` and ``date_filed`` enter as consistency evidence only, and Decision 012
#: gives ``full_index`` authority level 3, so neither can overwrite an authoritative
#: value established by an entity-submissions observation at level 2 (**R23** §5.5).
_INDEX_OBSERVED_FIELDS: Final[tuple[str, ...]] = ("cik_padded", "form_type", "date_filed")


def _materialize_full_index_registrants(
    connection: sqlite3.Connection,
    *,
    observation: SourceObservation,
    parser_run_id: str,
    recorded: str,
) -> tuple[int, tuple[str, ...]]:
    """**R23** -- candidate-facing registrant evidence from stored ``company.idx`` rows.

    The accepted parser has already run and its rows are durable in
    ``census_parsed_records``; this reads them back and writes the accession
    observations Decision 012's resolver and the candidate builder both consume. It is
    a narrow offline persistence helper, permitted by R23 §5.6: it writes exactly one
    already-R17-permitted table, reuses the accepted stable-identifier convention, and
    creates no schema, role, or evidence state.

    Reading the rows **back** rather than recomputing them is deliberate: it makes the
    ``parsed_record_id`` foreign key correct by construction rather than by a second
    derivation of the accepted identifier.

    Returns the number of observation rows written and the accessions the index listed
    that the authoritative accession layer does not carry. Those are reported, never
    created: ``census_accession_observations.accession_plain`` is a foreign key into
    ``census_accessions``, so an index-only accession is refused by the schema as well
    as by this check (**R23** §5.1).
    """
    known = {
        str(row["accession_plain"])
        for row in connection.execute("SELECT accession_plain FROM census_accessions").fetchall()
    }
    rows = connection.execute(
        "SELECT parsed_record_id, payload_json FROM census_parsed_records "
        "WHERE parser_run_id = ? AND native_identity LIKE ? ORDER BY parsed_record_id",
        (parser_run_id, f"{_INDEX_ROW_PREFIX}%"),
    ).fetchall()
    written = 0
    unbound: set[str] = set()
    with transaction(connection) as active:
        for row in rows:
            payload = _index_payload(row["payload_json"])
            if payload is None:
                continue
            plain, cik_padded = _index_identity(payload)
            if plain is None or cik_padded is None:
                continue
            if plain not in known:
                unbound.add(plain)
                continue
            for field in _INDEX_OBSERVED_FIELDS:
                value = payload.get(field)
                if value is None:
                    continue
                active.execute(
                    "INSERT OR IGNORE INTO census_accession_observations "
                    "(accession_observation_id, accession_plain, source_observation_id, "
                    "parsed_record_id, field_name, raw_value_json, observed_at_utc, "
                    "conflict_indicator) VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                    (
                        _stable_id(
                            "accession-observation",
                            plain,
                            observation.observation_id,
                            str(row["parsed_record_id"]),
                            field,
                        ),
                        plain,
                        observation.observation_id,
                        str(row["parsed_record_id"]),
                        field,
                        json.dumps(cik_padded if field == "cik_padded" else value, sort_keys=True),
                        recorded,
                    ),
                )
                written += 1
    return written, tuple(sorted(unbound))


def _index_payload(raw: object) -> Mapping[str, object] | None:
    """One stored index-row payload, or ``None`` when the parser already refused it.

    A row the accepted parser recorded ``problems`` for stays exactly what the parser
    made it -- retained, quarantined evidence -- and establishes no registrant. It is
    never repaired into a usable row.
    """
    try:
        decoded = json.loads(str(raw))
    except (TypeError, ValueError):
        return None
    if not isinstance(decoded, dict) or decoded.get("problems"):
        return None
    return decoded


def _index_identity(payload: Mapping[str, object]) -> tuple[str | None, str | None]:
    """Canonicalize one index row's accession and CIK, or refuse it.

    The parser's ``accession_plain`` payload key holds the **dashed** rendering, so the
    canonical plain form comes from the accepted ``parse_accession`` and never from the
    stored string. A malformed accession or CIK yields ``(None, None)``: it contributes
    no registrant rather than contributing a guessed one.
    """
    raw_accession = payload.get("accession_plain")
    raw_cik = payload.get("cik_padded")
    if not isinstance(raw_accession, str) or not isinstance(raw_cik, str):
        return None, None
    try:
        return parse_accession(raw_accession).plain, normalize_cik(raw_cik)[1]
    except IdentifierError:
        return None, None


# --------------------------------------------------------------------------
# Decision 094 §§6.2-6.4 -- the canonical census association projection
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _MembershipWitness:
    """One persisted observation supporting one accession-registrant membership.

    Ordered by **Decision 094 §6.3**'s deterministic tie-break: Decision 012's existing
    source-authority level first, then ``source_observation_id``, then the nullable
    ``parsed_record_id`` with a missing identity sorting **after** every present one.
    """

    authority_level: int
    source_observation_id: str
    parsed_record_id: str | None
    observed_at_utc: str
    conflicting: bool

    @property
    def rank(self) -> tuple[int, str, int, str]:
        """The total order §6.3 fixes. Nothing here reads recency or row order."""
        return (
            self.authority_level,
            self.source_observation_id,
            1 if self.parsed_record_id is None else 0,
            self.parsed_record_id or "",
        )


@dataclass(frozen=True, slots=True)
class _MembershipGroup:
    """One canonical accession's complete membership evidence, and nothing else.

    Exactly one of these is alive at a time (**Decision 094 §6.4**): the streaming loop
    yields a group, the projection consumes it, and the next group replaces it. No
    all-catalog membership map is ever materialized.
    """

    accession_plain: str
    submissions: frozenset[int]
    full_index: frozenset[int]
    witnesses: Mapping[int, tuple[_MembershipWitness, ...]]
    invalid_renderings: int

    @property
    def union(self) -> tuple[int, ...]:
        """``U = S_submissions union S_full_index``, ordered by canonical numeric CIK only."""
        return tuple(sorted(self.submissions | self.full_index))


def membership_observation_sources(
    connection: sqlite3.Connection,
) -> Mapping[str, str]:
    """The plan-bound accepted usable observations §6.2's two sets may be read through.

    Membership is joined through ``census_plan_sources.observation_id`` exclusively
    (**R13**), so an observation the accepted plan does not bind contributes nothing even
    if it is present in the catalog. The mapping is observation id to source id, which is
    all the projection needs to decide which side of §6.2 a row belongs to.
    """
    rows = connection.execute(
        "SELECT DISTINCT p.observation_id, s.source_id FROM census_plan_sources AS p "
        "JOIN census_source_observations AS s ON s.observation_id = p.observation_id "
        "WHERE p.observation_id IS NOT NULL "
        "ORDER BY p.observation_id"
    ).fetchall()
    eligible: dict[str, str] = {}
    for row in rows:
        observation_id = str(row["observation_id"])
        source_id = str(row["source_id"])
        if source_id in SUBMISSIONS_MEMBERSHIP_SOURCE_IDS | FULL_INDEX_MEMBERSHIP_SOURCE_IDS:
            eligible[observation_id] = source_id
    return eligible


def _membership_cik(raw_value_json: object) -> int | None:
    """One persisted membership value as a canonical numeric CIK, or ``None``.

    A value that does not normalize **exactly** contributes nothing and is counted as an
    invalid rendering. It is never repaired by inference, and it never becomes a guessed
    member (**Decision 094 §6.2**).
    """
    try:
        decoded = json.loads(str(raw_value_json))
    except (TypeError, ValueError):
        return None
    if isinstance(decoded, bool) or not isinstance(decoded, (str, int)):
        return None
    try:
        return normalize_cik(decoded)[0]
    except IdentifierError:
        return None


def _stream_membership_groups(
    connection: sqlite3.Connection,
    eligible: Mapping[str, str],
) -> Iterator[_MembershipGroup]:
    """Yield one accession's membership group at a time, in canonical accession order.

    The cursor is consumed lazily and the accumulator is reset at every accession
    boundary, so peak memory is one accession's membership and provenance rather than the
    whole catalog's (**Decision 094 §6.4**).
    """
    cursor = connection.execute(
        "SELECT o.accession_plain, o.field_name, o.raw_value_json, o.source_observation_id, "
        "o.parsed_record_id, o.observed_at_utc, o.conflict_indicator "
        "FROM census_accession_observations AS o "
        "WHERE o.field_name IN (?, ?) "
        "ORDER BY o.accession_plain, o.accession_observation_id",
        SUBMISSIONS_MEMBERSHIP_FIELDS,
    )
    current: str | None = None
    submissions: set[int] = set()
    full_index: set[int] = set()
    witnesses: dict[int, list[_MembershipWitness]] = defaultdict(list)
    invalid = 0

    def _finish(accession: str) -> _MembershipGroup:
        return _MembershipGroup(
            accession_plain=accession,
            submissions=frozenset(submissions),
            full_index=frozenset(full_index),
            witnesses={
                cik: tuple(sorted(items, key=lambda item: item.rank))
                for cik, items in sorted(witnesses.items())
            },
            invalid_renderings=invalid,
        )

    for row in cursor:
        accession = str(row["accession_plain"])
        if accession != current:
            if current is not None:
                yield _finish(current)
            current = accession
            submissions = set()
            full_index = set()
            witnesses = defaultdict(list)
            invalid = 0
        source_id = eligible.get(str(row["source_observation_id"]))
        if source_id is None:
            continue
        field = str(row["field_name"])
        submissions_side = (
            source_id in SUBMISSIONS_MEMBERSHIP_SOURCE_IDS
            and field in SUBMISSIONS_MEMBERSHIP_FIELDS
        )
        full_index_side = (
            source_id in FULL_INDEX_MEMBERSHIP_SOURCE_IDS and field in FULL_INDEX_MEMBERSHIP_FIELDS
        )
        if not (submissions_side or full_index_side):
            continue
        numeric = _membership_cik(row["raw_value_json"])
        if numeric is None:
            invalid += 1
            continue
        if submissions_side:
            submissions.add(numeric)
        if full_index_side:
            full_index.add(numeric)
        parsed_record_id = row["parsed_record_id"]
        witnesses[numeric].append(
            _MembershipWitness(
                authority_level=AUTHORITY_LEVEL[authority_for_source(source_id)],
                source_observation_id=str(row["source_observation_id"]),
                parsed_record_id=None if parsed_record_id is None else str(parsed_record_id),
                observed_at_utc=str(row["observed_at_utc"]),
                conflicting=bool(row["conflict_indicator"]),
            )
        )
    if current is not None:
        yield _finish(current)


def _blocking_fields_clear(connection: sqlite3.Connection, accession_plain: str) -> bool:
    """Whether one accession's latest Decision 012 resolutions clear §6.2 item 5.

    ``form`` and ``official_filing_date`` must each be ``resolved`` or
    ``resolved_by_correction`` with ``blocks_dependents = 0``. A missing resolution is a
    failure, not a pass: silence about a material field never establishes a set.

    The latest resolution per ``(accession, field)`` wins, matching the accepted reader in
    ``candidate_snapshot`` -- ordering by ``resolved_at_utc`` and taking the last.
    ``policy_version`` breaks a tie, because it is the remaining component of this table's
    primary key and two resolutions of the same field at the same instant would otherwise be
    separated by nothing.

    Asked one accession at a time, against the primary-key index, rather than preloaded for the
    whole catalog (accepted Decision 110 §8). The preloaded form held one entry per
    ``(accession, field)`` for every accession in the catalog, which on E0's first planned source
    is roughly 43 million entries and several gigabytes -- memory proportional to the parsed
    record count, which is exactly what the memory invariant forbids.
    """
    latest: dict[str, bool] = {}
    for row in connection.execute(
        "SELECT field_name, status, blocks_dependents "
        "FROM census_accession_field_resolutions "
        "WHERE accession_plain = ? AND field_name IN (?, ?) "
        "ORDER BY field_name, resolved_at_utc, policy_version",
        (accession_plain, *_MEMBERSHIP_BLOCKING_FIELDS),
    ):
        latest[str(row["field_name"])] = str(row["status"]) in _RESOLVED_STATUSES and not int(
            row["blocks_dependents"]
        )
    return all(latest.get(field, False) for field in _MEMBERSHIP_BLOCKING_FIELDS)


def _accession_is_known(connection: sqlite3.Connection, accession_plain: str) -> bool:
    """Whether the authoritative accession layer carries this accession.

    One primary-key lookup, rather than a preloaded set of every ``accession_plain`` in the
    catalog (accepted Decision 110 §8). On E0's first planned source that set would hold roughly
    21.5 million accession strings and cost about 2.9 GB -- on its own more than the whole memory
    budget this host has. The predicate is unchanged; only where the answer comes from is.
    """
    return (
        connection.execute(
            "SELECT 1 FROM census_accessions WHERE accession_plain = ?",
            (accession_plain,),
        ).fetchone()
        is not None
    )


@dataclass(frozen=True, slots=True)
class _GroupProjection:
    """Everything **Decision 094 §6.4** decides about one accession's membership group.

    Pure: derived from the group, the known-registrant set, and the §6.2 item 5 verdict, and
    from nothing this projection writes. That is what lets the completeness pass recompute it
    from the same evidence instead of the first pass carrying an accession-sized list of results
    across the whole traversal -- the ordering law §6.4 item 5 states is about *when* completeness
    is written, not about where the decision is remembered.
    """

    candidates: tuple[tuple[int, tuple[object, ...]], ...]
    provenance_failures: int
    conflicting: bool
    uncorroborated: int
    unbindable: int
    is_multi: bool
    is_established: bool
    scalar: int | None


def _project_membership_group(
    group: _MembershipGroup, *, known_registrants: Collection[int], clear: bool
) -> _GroupProjection:
    """Derive §6.4's verdict for one group without writing anything."""
    members = group.union
    bindable = tuple(cik for cik in members if cik in known_registrants)
    unbindable = len(members) - len(bindable)
    candidates: list[tuple[int, tuple[object, ...]]] = []
    levels: list[str] = []
    conflicting = False
    provenance_failures = 0
    for cik in bindable:
        witnesses = group.witnesses.get(cik, ())
        if not witnesses:
            provenance_failures += 1
            continue
        conflicting = conflicting or any(item.conflicting for item in witnesses)
        chosen = witnesses[0]
        level = _evidence_level_for(witnesses, fields_clear=clear)
        levels.append(level)
        candidates.append(
            (
                cik,
                (
                    normalize_cik(cik)[1],
                    _SUBSTANTIVE,
                    level,
                    chosen.source_observation_id,
                    chosen.parsed_record_id,
                    min(item.observed_at_utc for item in witnesses),
                    max(item.observed_at_utc for item in witnesses),
                ),
            )
        )
    # §6.2 condition 2. Counted in **members**, which is what the §9.5 name says: an accession
    # missing three corroborations is a bigger evidence gap than one missing a single member,
    # and collapsing both to "1 accession" would hide that.
    uncorroborated = len(group.submissions - group.full_index)
    is_established = (
        bool(group.submissions)
        and bool(group.full_index)
        and not uncorroborated
        and unbindable == 0
        and group.invalid_renderings == 0
        and clear
        and len(bindable) == len(members)
        and bool(levels)
        and all(level == "provisional" for level in levels)
    )
    return _GroupProjection(
        candidates=tuple(candidates),
        provenance_failures=provenance_failures,
        conflicting=conflicting,
        uncorroborated=uncorroborated,
        unbindable=unbindable,
        is_multi=len(bindable) > 1,
        is_established=is_established,
        scalar=bindable[0] if len(bindable) == 1 else None,
    )


def _evidence_level_for(
    witnesses: Sequence[_MembershipWitness],
    *,
    fields_clear: bool,
) -> str:
    """**Decision 094 §6.3** -- the relation row's evidence level.

    ``provisional`` is reserved for a valid, internally consistent accepted metadata
    witness. Everything weaker keeps the existing migration-``0014`` fail-closed
    vocabulary, and no weaker state can establish completeness.
    """
    if not witnesses:
        return "unavailable"
    if any(item.conflicting for item in witnesses):
        return "conflicting"
    if not fields_clear:
        return "review_required"
    return "provisional"


def _existing_relation_row(
    connection: sqlite3.Connection, accession_plain: str, cik: int
) -> sqlite3.Row | None:
    """The persisted relation row for one membership, or ``None``."""
    row: sqlite3.Row | None = connection.execute(
        "SELECT registrant_cik_padded, association_class, evidence_level, "
        "source_observation_id, parsed_record_id, first_observed_at_utc, latest_observed_at_utc "
        "FROM census_accession_registrants "
        "WHERE accession_plain = ? AND registrant_cik_numeric = ?",
        (accession_plain, cik),
    ).fetchone()
    return row


def materialize_census_associations(
    connection: sqlite3.Connection,
    *,
    eligible_observations: Mapping[str, str] | None = None,
) -> AssociationTotality:
    """Write the canonical **Decision 083 R58** relation and its completeness state.

    This is **Decision 094 §§6.2-6.4** exactly, and it is the capability migration ``0014``'s
    own comment assigns to E0. Membership is a **set union** of the plan-bound submissions and
    full-index evidence -- never a scalar, an anchor, a first write, a company name, a row
    count, or any proximity heuristic. Distinct valid CIKs are co-registrants, not a conflict.
    The submitter stays a submission fact and is never promoted here.

    Everything is written **and checked** in one transaction, so SQLite rollback makes the
    projection all-or-nothing: neither an interruption before commit nor a broken §9.5
    invariant can leave an ``established`` incomplete set, a partial relation, or a persisted
    projection behind. Completeness is written **last**, after the relation is total, and a member
    the accepted evidence names but no ``census_registrants`` row describes is recorded as
    unbindable and **fails its accession closed** -- no entity is invented.

    **Create-once, and re-enterable.** §6.4 item 3 forbids a replacement write, and contract
    §10.2 item 5 requires a reparse of the same accepted observation set to be deterministic.
    Both hold together the same way the accepted receipt writer resolves the same tension: an
    existing row that is byte-for-byte what this run would write is a **collision by identity**
    and is left exactly as it is, while an existing row that differs **fails closed**. Nothing
    is ever overwritten, and a second identical parse changes no durable byte.

    Args:
        connection: The writing connection, already inside the E0 write containment.
        eligible_observations: Plan-bound observation id to source id. Derived from the catalog
            when omitted, which is what a read-only reconstruction needs.

    Returns:
        The §9.5 totality, already checked against its own invariants.

    Raises:
        OfflineParseError: a §9.5 totality invariant was broken, or a persisted relation row
            disagrees with the projection this evidence produces.
    """
    eligible = (
        membership_observation_sources(connection)
        if eligible_observations is None
        else eligible_observations
    )
    known_registrants = {
        int(row["cik_numeric"])
        for row in connection.execute("SELECT cik_numeric FROM census_registrants")
    }

    # Bounded accumulators only: counters, and one accession's group at a time. Nothing here
    # holds a per-accession entry, so peak memory does not follow the parsed record count
    # (accepted Decision 110 §8). ``known_registrants`` is the one preloaded set that stays,
    # because it is bounded by the *registrant* count -- roughly 985,000 integers, about 60 MB --
    # rather than by the accession count, which is more than twenty times larger and made of
    # strings.
    relation_rows = 0
    invalid_renderings = 0
    provenance_failures = 0
    orphans = 0
    missing_corroboration = 0
    unbindable_members = 0
    membership_conflicts = 0
    singletons = 0
    multi = 0

    with transaction(connection) as active:
        for group in _stream_membership_groups(connection, eligible):
            invalid_renderings += group.invalid_renderings
            if not _accession_is_known(active, group.accession_plain):
                # A full-index row never creates an accession (**R23** §5.1). Membership
                # evidence bound to an accession the authoritative layer does not carry is
                # reported, never repaired into a relation row.
                orphans += 1
                continue
            if not group.union:
                continue
            projection = _project_membership_group(
                group,
                known_registrants=known_registrants,
                clear=_blocking_fields_clear(active, group.accession_plain),
            )
            unbindable_members += projection.unbindable
            provenance_failures += projection.provenance_failures

            if projection.is_multi:
                # §6.4 item 2: the scalar must already be NULL when the second substantive
                # relation row is inserted, which is exactly when migration ``0014``'s trigger
                # becomes able to observe the cardinality. Clearing it before the first insert
                # reaches the same state and needs no ordering assumption.
                active.execute(
                    "UPDATE census_accessions SET registrant_cik_numeric = NULL "
                    "WHERE accession_plain = ? AND registrant_cik_numeric IS NOT NULL",
                    (group.accession_plain,),
                )

            for cik, candidate in projection.candidates:
                existing = _existing_relation_row(active, group.accession_plain, cik)
                if existing is not None:
                    persisted = tuple(existing)
                    if persisted != candidate:
                        message = (
                            f"the persisted association row for accession "
                            f"{group.accession_plain!r} registrant {cik} disagrees with the "
                            f"projection this evidence produces; the relation is create-once "
                            f"and a correction is a new run, never a replacement write"
                        )
                        raise OfflineParseError(message)
                    relation_rows += 1
                    continue
                active.execute(
                    "INSERT INTO census_accession_registrants "
                    "(accession_plain, registrant_cik_numeric, registrant_cik_padded, "
                    "association_class, evidence_level, source_observation_id, "
                    "parsed_record_id, first_observed_at_utc, latest_observed_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (group.accession_plain, cik, *candidate),
                )
                relation_rows += 1

            missing_corroboration += projection.uncorroborated
            if projection.conflicting:
                # A conflict is an accepted observation carrying the conflict indicator -- not
                # merely a blocked resolution, and never two distinct valid CIKs, which §9.5
                # says explicitly may not increment a conflict count.
                membership_conflicts += 1
            if projection.is_established:
                if projection.scalar is not None:
                    singletons += 1
                else:
                    multi += 1

        # §6.4 item 5: completeness is written last, after every relation row exists, so no
        # window can be observed in which an accession claims a complete set it has not yet
        # materialized. Migration ``0014``'s own trigger refuses the claim from the other
        # direction; this ordering is what keeps the lawful write shape available at all.
        #
        # It is a **second traversal** of the same evidence rather than a list carried across
        # the first (accepted Decision 110 §8). Remembering the established accessions cost one
        # tuple each, which on E0's first planned source is roughly 21.5 million of them and
        # about 2.9 GB. The verdict is recomputed instead, which is sound because
        # `_project_membership_group` is pure and reads nothing the loop above writes: the
        # membership observations, the field resolutions, and the registrant set are all
        # untouched by this projection, so the second pass necessarily reaches the same answer.
        for group in _stream_membership_groups(connection, eligible):
            if not _accession_is_known(active, group.accession_plain) or not group.union:
                continue
            projection = _project_membership_group(
                group,
                known_registrants=known_registrants,
                clear=_blocking_fields_clear(active, group.accession_plain),
            )
            if not projection.is_established:
                continue
            active.execute(
                "UPDATE census_accessions SET registrant_cik_numeric = ? WHERE accession_plain = ?",
                (projection.scalar, group.accession_plain),
            )
            active.execute(
                "UPDATE census_accessions SET registrant_set_completeness = ? "
                "WHERE accession_plain = ?",
                (_ESTABLISHED, group.accession_plain),
            )

        # §6.4: the projection transaction is all-or-nothing, so the totality is measured
        # and required **inside** it. Measuring after the commit would still detect a
        # violation, but it would detect one that had already been persisted -- an
        # `established` completeness written beside a broken §9.5 invariant is exactly the
        # durable state the rollback rule exists to make unreachable.
        totality = _measure_association_totality(
            active,
            invalid_renderings=invalid_renderings,
            provenance_failures=provenance_failures,
            orphans=orphans,
            missing_corroboration=missing_corroboration,
            unbindable_members=unbindable_members,
            membership_conflicts=membership_conflicts,
            expected_singletons=singletons,
            expected_multi=multi,
            expected_relation_rows=relation_rows,
        )
        totality.require()
    return totality


def _membership_observation_counts(connection: sqlite3.Connection) -> tuple[int, int]:
    """How many persisted observations each side of §6.2's set definition reads.

    Reported as evidence that the two sets were derived from real durable rows rather
    than asserted: a zero submissions count with a non-empty relation would be visible
    immediately. Returns ``(submissions, substantive)`` where the second total counts
    every membership observation on either side.
    """
    eligible = membership_observation_sources(connection)
    submissions = 0
    substantive = 0
    # Iterated, never `fetchall`ed: this is one row per membership observation, which on E0's
    # first planned source is tens of millions of them (accepted Decision 110 §8).
    for row in connection.execute(
        "SELECT source_observation_id, field_name FROM census_accession_observations "
        "WHERE field_name IN (?, ?)",
        SUBMISSIONS_MEMBERSHIP_FIELDS,
    ):
        source_id = eligible.get(str(row["source_observation_id"]))
        if source_id is None:
            continue
        field = str(row["field_name"])
        if (
            source_id in SUBMISSIONS_MEMBERSHIP_SOURCE_IDS
            and field in SUBMISSIONS_MEMBERSHIP_FIELDS
        ):
            submissions += 1
            substantive += 1
        elif (
            source_id in FULL_INDEX_MEMBERSHIP_SOURCE_IDS and field in FULL_INDEX_MEMBERSHIP_FIELDS
        ):
            substantive += 1
    return submissions, substantive


def _measure_association_totality(
    connection: sqlite3.Connection,
    *,
    invalid_renderings: int,
    provenance_failures: int,
    orphans: int,
    missing_corroboration: int,
    unbindable_members: int,
    membership_conflicts: int,
    expected_singletons: int,
    expected_multi: int,
    expected_relation_rows: int,
) -> AssociationTotality:
    """Read the §9.5 counts back from the persisted rows, not from the writer's tallies.

    The six zero-fixed invariants are measured against the database so a writer bug shows
    up as a totality failure rather than as a self-consistent report. The three
    ``unestablished``-only counts are the writer's own dispositions, because they describe
    why a set was refused and no persisted row records a refusal.
    """
    accessions = int(connection.execute("SELECT COUNT(*) FROM census_accessions").fetchone()[0])
    established = int(
        connection.execute(
            "SELECT COUNT(*) FROM census_accessions WHERE registrant_set_completeness = ?",
            (_ESTABLISHED,),
        ).fetchone()[0]
    )
    relation_rows = int(
        connection.execute(
            "SELECT COUNT(*) FROM census_accession_registrants WHERE association_class = ?",
            (_SUBSTANTIVE,),
        ).fetchone()[0]
    )
    zero_relation = 0
    singleton = 0
    multi = 0
    singleton_mismatch = 0
    multi_nonnull = 0
    # One lazy pass, and the cardinality is carried by the query rather than by a Python map of
    # every accession (accepted Decision 110 §8). ``sole`` is read with ``MIN`` and is consulted
    # only where the count is exactly 1, so it is that single row's CIK -- the same value the
    # per-accession lookup returned, without a query per established accession.
    for row in connection.execute(
        "SELECT a.accession_plain, a.registrant_cik_numeric, "
        "(SELECT COUNT(*) FROM census_accession_registrants AS r "
        " WHERE r.accession_plain = a.accession_plain AND r.association_class = ?) AS members, "
        "(SELECT MIN(r.registrant_cik_numeric) FROM census_accession_registrants AS r "
        " WHERE r.accession_plain = a.accession_plain AND r.association_class = ?) AS sole "
        "FROM census_accessions AS a WHERE a.registrant_set_completeness = ? "
        "ORDER BY a.accession_plain",
        (_SUBSTANTIVE, _SUBSTANTIVE, _ESTABLISHED),
    ):
        scalar = row["registrant_cik_numeric"]
        members = int(row["members"])
        if members == 0:
            zero_relation += 1
        elif members == 1:
            singleton += 1
            sole = int(row["sole"])
            if scalar is None or int(scalar) != sole:
                singleton_mismatch += 1
        else:
            multi += 1
            if scalar is not None:
                multi_nonnull += 1
    orphan_rows = orphans + int(
        connection.execute(
            "SELECT COUNT(*) FROM census_accession_registrants AS r "
            "WHERE NOT EXISTS (SELECT 1 FROM census_accessions AS a "
            "WHERE a.accession_plain = r.accession_plain)"
        ).fetchone()[0]
    )
    invalid = invalid_renderings + int(
        connection.execute(
            "SELECT COUNT(*) FROM census_accession_registrants "
            "WHERE registrant_cik_padded <> printf('%010d', registrant_cik_numeric)"
        ).fetchone()[0]
    )
    provenance = provenance_failures + int(
        connection.execute(
            "SELECT COUNT(*) FROM census_accession_registrants AS r "
            "WHERE NOT EXISTS (SELECT 1 FROM census_source_observations AS s "
            "WHERE s.observation_id = r.source_observation_id) "
            "OR (r.parsed_record_id IS NOT NULL AND NOT EXISTS "
            "(SELECT 1 FROM census_parsed_records AS p "
            "WHERE p.parsed_record_id = r.parsed_record_id))"
        ).fetchone()[0]
    )
    if (singleton, multi, relation_rows) != (
        expected_singletons,
        expected_multi,
        expected_relation_rows,
    ):
        message = (
            "the persisted association projection disagrees with what the writer recorded: "
            f"persisted singleton/multi/rows {(singleton, multi, relation_rows)} versus "
            f"written {(expected_singletons, expected_multi, expected_relation_rows)}"
        )
        raise OfflineParseError(message)
    return AssociationTotality(
        census_accession_count=accessions,
        established_accession_count=established,
        unestablished_accession_count=accessions - established,
        substantive_relation_count=relation_rows,
        established_zero_relation_count=zero_relation,
        established_singleton_count=singleton,
        established_multi_count=multi,
        singleton_scalar_mismatch_count=singleton_mismatch,
        multi_nonnull_scalar_count=multi_nonnull,
        orphan_relation_count=orphan_rows,
        invalid_cik_rendering_count=invalid,
        association_provenance_failure_count=provenance,
        submissions_member_missing_full_index_count=missing_corroboration,
        unbindable_registrant_member_count=unbindable_members,
        unestablished_membership_conflict_count=membership_conflicts,
    )


#: The sources E0 persists by streaming rather than by merging first (Decision 110 §8).
#:
#: Membership is a statement about *scale*, not about semantics: these are the sources whose
#: parsed output does not fit in memory, and nothing else about how they are parsed, classified,
#: or accounted for differs. Every other source keeps the merged path unchanged, so this is the
#: whole of the behavioural difference and it is enumerable.
STREAMED_SOURCE_IDS: Final[frozenset[str]] = frozenset({"sec_bulk_submissions"})

#: ``census_parser_runs.outcome`` to the accepted ``census_plan_sources.parser_state`` terminal.
#:
#: The merged path derives the terminal from the outcome object with :func:`_parser_state_for`;
#: a streamed run has no such object left, so it reads the state the same write already recorded.
#: The two agree by construction -- ``persist`` and ``persist_streamed`` choose the run state by
#: the identical rule -- and this mapping is one-to-one so neither can drift into the other's
#: vocabulary unnoticed.
_STREAMED_PARSER_STATE: Final[Mapping[str, str]] = {
    "failed": "failed",
    "completed_with_quarantine": "quarantined",
    "completed": "completed",
}


def _parser_state_for(outcome: ParseOutcome) -> str:
    """The accepted ``parser_state`` terminal for one completed parse.

    Mirrors the accepted census lifecycle exactly: a structural failure is ``failed``,
    a quarantined record is ``quarantined``, and anything else is ``completed``. A
    reparse of the same accepted observation reaches the same terminal, because the
    outcome it is derived from is itself deterministic (**GR-C2**).
    """
    if outcome.structural_failures:
        return "failed"
    if outcome.quarantined:
        return "quarantined"
    return "completed"


@dataclass(frozen=True, slots=True)
class SourceLayerPhase:
    """Everything E0 writes **before** the Decision 094 §6.4 association projection.

    Decision 094 §6.4 fixes an order rather than a preference: the projection runs strictly
    after every category-A parse, after full-index observation materialization, and after
    ``resolve_persisted_accessions()``, because membership evidence may bind only to an
    accession the submissions layer has already established and because §6.2 item 5 reads
    the resolver's own output.

    Naming that boundary makes the ordering a structure instead of a comment, so the
    dependency can be exercised directly at exactly the state the projection consumes.
    """

    outcomes: tuple[PlannedSourceOutcome, ...]
    accession_resolutions: int
    full_index_registrant_observations: int
    full_index_unbound_accessions: tuple[str, ...]


def materialize_source_layer(
    *,
    writer: CatalogWriter,
    tree: DataTree,
    approved_2024_transitions: Mapping[str, bool] | None = None,
) -> SourceLayerPhase:
    """Parse every planned source, materialize the full index, and resolve accessions.

    This is the whole of E0's durable database work **except** the §6.4 association
    projection, and it is a phase of one ``CatalogWriter`` invocation rather than a second
    catalog writer: :func:`run_offline_metadata_parse` calls it inside the same
    :func:`write_containment`, and a caller reaching it directly must do the same.

    Raises:
        OfflineParseError: any fail-closed condition, always before a durable write.
    """
    connection = writer.connection
    planned = load_planned_sources(connection)
    observations = _observations_by_id(connection)
    store = SnapshotStore(tree)
    store.adopt(observations.values())
    catalog = CensusCatalog(writer, approved_2024_transitions=approved_2024_transitions)

    dispositions: list[tuple[PlannedSource, SourceDisposition]] = []
    for source in planned:
        bound = None if source.observation_id is None else observations.get(source.observation_id)
        dispositions.append((source, classify_planned_source(source, bound)))

    outcomes: list[PlannedSourceOutcome] = []
    index_runs: list[tuple[SourceObservation, str]] = []
    index_observations = 0
    index_unbound: set[str] = set()
    parsed_any = False
    for source, disposition in dispositions:
        if disposition != "E0_REQUIRED_PARSE":
            outcomes.append(
                PlannedSourceOutcome(
                    source_instance_id=source.source_instance_id,
                    source_id=source.source_id,
                    disposition=disposition,
                    parser_state_before=source.parser_state,
                    parser_state_after=source.parser_state,
                    detail=(
                        "accepted source preserved as failed or unavailable"
                        if disposition == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"
                        else "deliberately untouched: parser output is not used by "
                        "the authoritative candidate builder"
                    ),
                )
            )
            continue
        bound_id = source.observation_id
        if bound_id is None or bound_id not in observations:
            message = (
                f"planned source {source.source_instance_id!r} lost its plan-bound "
                "observation between classification and parse"
            )
            raise OfflineParseError(message)
        observation = observations[bound_id]
        if observation.source_id in STREAMED_SOURCE_IDS:
            # **Decision 110 §8.** The bulk archive is persisted member by member rather than
            # merged first: the merged form retains every record of a 985,834-member source at
            # once, which is the D109 finding F1 kill. The rows, their identities, and their
            # order are the same either way -- only the residency changes.
            result = catalog.persist_streamed(
                _stream_bulk_submissions(store, observation),
                parser_id=_BULK_PARSER_ID,
                parser_version=SOURCES[observation.source_id].parser_version,
                source_observation_id=observation.observation_id,
            )
            after = _STREAMED_PARSER_STATE[result.run_outcome]
        else:
            outcome, references = _parse_source(connection, store, observation)
            result = catalog.persist(
                outcome,
                historical_references=references,
                source_observation_id=observation.observation_id,
            )
            after = _parser_state_for(outcome)
        parsed_any = True
        with transaction(connection) as active:
            active.execute(
                "UPDATE census_plan_sources SET parser_state = ? "
                "WHERE census_run_id = ? AND source_instance_id = ?",
                (after, source.census_run_id, source.source_instance_id),
            )
        if source.source_id == "sec_full_index_company":
            index_runs.append((observation, result.parser_run_id))
        outcomes.append(
            PlannedSourceOutcome(
                source_instance_id=source.source_instance_id,
                source_id=source.source_id,
                disposition=disposition,
                parser_run_id=result.parser_run_id,
                parsed_records=result.parsed,
                quarantined_records=result.quarantined,
                parser_state_before=source.parser_state,
                parser_state_after=after,
                already_present=result.already_present,
            )
        )
    # R23: materialization runs only after every category-A parse, because a
    # company.idx row may bind only to an accession the submissions layer has
    # already established. Ordering by plan row would make binding depend on plan
    # order, which is exactly what the accepted source binding forbids.
    recorded = utc_now()
    for observation, run_id in index_runs:
        written, unbound = _materialize_full_index_registrants(
            connection, observation=observation, parser_run_id=run_id, recorded=recorded
        )
        index_observations += written
        index_unbound.update(unbound)
    resolutions = catalog.count_persisted_accession_resolutions() if parsed_any else 0
    return SourceLayerPhase(
        outcomes=tuple(outcomes),
        accession_resolutions=resolutions,
        full_index_registrant_observations=index_observations,
        full_index_unbound_accessions=tuple(sorted(index_unbound)),
    )


def run_offline_metadata_parse(
    *,
    writer: CatalogWriter,
    tree: DataTree,
    approved_2024_transitions: Mapping[str, bool] | None = None,
) -> OfflineParseReport:
    """Derive the census parse layer from accepted stored objects, offline.

    Every planned source is enumerated and receives exactly one **R18** disposition.
    Category **A** traverses the accepted parse-and-persist path; category **B** stays
    truthfully unavailable; category **C** is left deliberately untouched — no parser
    run, no index-table population, and no ``parser_state`` mutation merely to complete
    a ledger.

    **This function performs no network access and constructs no transport.** Calling
    it against the accepted real private catalog is M3.3-E0 and requires its own owner
    authorization; this module grants none.

    Raises:
        OfflineParseError: any fail-closed condition, always before a durable write.
    """
    connection = writer.connection
    with write_containment(connection):
        phase = materialize_source_layer(
            writer=writer, tree=tree, approved_2024_transitions=approved_2024_transitions
        )
        # **Decision 094 §6.4**: the association projection runs strictly after every
        # category-A parse, after full-index materialization, and after canonical
        # accession resolution — because membership evidence may bind only to an
        # accession the submissions layer has already established, and because §6.2
        # item 5 reads the resolver's own output. It is part of *this* CatalogWriter
        # invocation and is not a second catalog writer (contract §20, D094 §6.1 item 4).
        membership = _membership_observation_counts(connection)
        totality = materialize_census_associations(connection)

    report = OfflineParseReport(
        outcomes=phase.outcomes,
        accession_resolutions=phase.accession_resolutions,
        full_index_registrant_observations=phase.full_index_registrant_observations,
        full_index_unbound_accessions=phase.full_index_unbound_accessions,
        association_totality=totality,
        submissions_membership_observations=membership[0],
        substantive_membership_observations=membership[1],
    )
    if not report.is_complete:
        message = "every planned source must receive exactly one E0 disposition"
        raise OfflineParseError(message)
    return report


def unavailable_source_ids(report: OfflineParseReport) -> tuple[str, ...]:
    """The candidate-substantive sources E0 truthfully could not parse.

    The builder consults this rather than discovering emptiness later: a classification
    that requires one of these fails closed at its accepted evidence floor
    (contract §8.1 correction 3).
    """
    return tuple(
        sorted(
            {
                item.source_id
                for item in report.by_disposition("E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE")
            }
        )
    )
