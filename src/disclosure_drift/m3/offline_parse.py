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

import hashlib
import heapq
import json
import sqlite3
import zipfile
from collections import defaultdict
from collections.abc import Callable, Collection, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, fields
from dataclasses import field as dataclass_field
from pathlib import Path
from typing import Any, ClassVar, Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.compact_evidence import (
    CompactEvidenceSidecar,
    CorroborationDigest,
    MemberManifestEntry,
    ProjectionDigest,
    canonical_projection,
    corroboration_observations,
    materialized_fields,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.accession_resolution import AUTHORITY_LEVEL, authority_for_source
from disclosure_drift.sec.archive import (
    ArchiveDefenceError,
    canonical_member_name,
    iter_members,
    iter_named_members,
)

# ``_stable_id`` is the accepted census identifier convention. It is imported rather
# than reimplemented so exactly one derivation of an accession-observation identity
# exists in the repository (M3.3 contract §20: no second persistence implementation).
from disclosure_drift.sec.census import (
    SINGLE_TRANSACTION,
    CensusCatalog,
    ResolutionEvidence,
    _stable_id,
    reconstructed_accession_resolution,
)
from disclosure_drift.sec.census import _json as _stable_json
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.observation_catalog import load_observations
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation, merge_outcomes
from disclosure_drift.sec.parsers.full_index import INDEX_ROW_PREFIX, parse_company_index
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.sic import parse_sic_reference
from disclosure_drift.sec.parsers.submissions import (
    HISTORICAL_FILE_NAME_PATTERN,
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
    "DIAGNOSTIC_PREFIX_CLASSIFICATION",
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
    "CompactSourceEvidence",
    "DiagnosticPrefixOutcome",
    "FullIndexCorroboration",
    "OfflineParseError",
    "OfflineParseReport",
    "PlannedSource",
    "SelectedPlannedSource",
    "SingleSourceOutcome",
    "SourceLayerPhase",
    "PlannedSourceOutcome",
    "SourceDisposition",
    "classify_planned_source",
    "load_planned_sources",
    "materialize_census_associations",
    "materialize_one_planned_source",
    "materialize_planned_source_prefix",
    "materialize_source_layer",
    "membership_observation_sources",
    "run_offline_metadata_parse",
    "select_planned_source",
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
_INDEX_MEMBERSHIP_FIELD: Final = FULL_INDEX_MEMBERSHIP_FIELDS[0]
#: The submissions-side field the canonical accession row reconstructs (D112 §2.3).
_SUBMISSIONS_MEMBERSHIP_FIELD: Final = SUBMISSIONS_MEMBERSHIP_FIELDS[0]

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

    Read from the accepted ``census_historical_references`` evidence, matched on the exact
    file the bound observation actually requested. A missing or ambiguous match fails
    closed: the CIK is never guessed, and the document is never re-retrieved to find
    out (contract §8.1 correction 4).

    **Uniqueness alone is not enough, and accepted Decision 129 §6 (D129-R4) says why.** The
    ``len(rows) != 1`` guard refuses zero candidates and refuses two, so it looks
    conservative -- but a single *consistently wrong* candidate satisfies it and is then
    returned as authority. That is exactly what the observation-wide stamping defect
    produced: 5,337 rows carrying one CIK, every lookup unique, every answer wrong. The
    shard's own canonical filename is therefore required to corroborate the persisted
    parent (accepted Decision 129 §7, D129-R5). Corroboration cannot *supply* a registrant
    -- a shard with no persisted reference still fails closed -- but it can and does refuse
    one that the name contradicts.
    """
    historical_file = observation.requested_url.rsplit("/", 1)[-1]
    filename_cik = _shard_filename_cik(historical_file)
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
        persisted = normalize_cik(str(rows[0]["registrant_cik_padded"]))[1]
    except IdentifierError as exc:
        message = f"accepted historical reference carries an invalid registrant CIK: {exc}"
        raise OfflineParseError(message) from exc
    if persisted != filename_cik:
        message = (
            f"historical submissions object {historical_file!r} is persisted against "
            f"registrant {persisted} but its canonical filename encodes {filename_cik}; a "
            "uniquely persisted reference that its own file name contradicts is refused "
            "rather than trusted for being unique"
        )
        raise OfflineParseError(message)
    return persisted


#: What a bounded diagnostic member prefix is, stated as a token rather than as prose.
#:
#: A prefix is **never** a parsed source, a completed source, or a successful canary, and no
#: accepted complete-source identity may be derived from one. The token exists so that a result
#: document, a rendered operator line, and a test all say the same single thing about what was
#: run, and so that a reader who sees it cannot mistake it for a disposition: the accepted
#: ``SourceDisposition`` vocabulary is closed and this deliberately is not a member of it
#: (accepted Decision 119 §6).
DIAGNOSTIC_PREFIX_CLASSIFICATION: Final = "INCOMPLETE_DIAGNOSTIC_PREFIX"


class _DiagnosticPrefixLimit(Exception):  # noqa: N818 - a control signal, not an error
    """Internal: the diagnostic member cap was reached, so the traversal stops here.

    Deliberately **not** a :class:`~disclosure_drift.errors.DisclosureDriftError`. Nothing has
    gone wrong -- a bounded prefix reaching its bound is the requested outcome -- and an operator
    surface that renders a ``DisclosureDriftError`` as a failure must not render this one.

    It is raised inside the member stream and caught by
    :func:`materialize_planned_source_prefix`, which is the only function that can cause it to
    exist. Between those two points it passes through
    :meth:`~disclosure_drift.sec.census.CensusCatalog.persist_streamed`, and that is the whole
    reason it is an exception rather than a return: the accepted
    :class:`~disclosure_drift.sec.census.BoundedTransaction` rolls the open batch back and the
    seeded ``failed`` run row therefore stands, which is the accepted interruption behaviour
    unchanged. A prefix leaves committed batches and **no** run claiming to have completed.
    """

    def __init__(self, members: int) -> None:
        super().__init__(f"diagnostic member prefix stopped after {members} members")
        self.members = members


#: The run-level parser identity one bulk-archive traversal writes, whether it is streamed
#: into the catalog or merged first. Named once because ``persist_streamed`` is handed it
#: directly, where the merged path used to read it off the merged outcome.
_BULK_PARSER_ID: Final = "submissions-json"


@dataclass
class CompactSourceEvidence:
    """One source's D112 §§4.A and 4.E evidence, accumulated during the single traversal.

    The member manifest and the completeness digest are both properties of the frozen artifact
    and of the pure parse of it, so both are built here rather than derived later from durable
    rows -- rows the compact contract deliberately does not write. Each member's manifest entry
    is written and dropped, and the digest is one running hash, so **neither the members nor
    their records accumulate**.

    **One structure here does grow with the source, and it is stated rather than implied.**
    ``_seen`` retains the native identity of every distinct accession record the traversal has
    met, because :func:`~disclosure_drift.m3.compact_evidence.materialized_fields` needs to know
    whether the record in hand is a first witness or a rival, and that question is about the
    whole source rather than about the member. It is one interned identity string per distinct
    accession -- not a record, not a payload, and not a manifest entry -- and it is therefore
    proportional to the source's **accession count**. Accepted Decision 119 §5 (R27) corrects an
    earlier claim in this docstring that nothing proportional to the source was retained; that
    claim was true of the members and false of ``_seen``. The structure itself is deliberately
    **unchanged**: dropping it would change which observation rows the compact contract
    materializes, which is an accepted evidence semantic and not a performance decision.

    An auditor reparsing the frozen artifact reaches the same manifest and the same digest,
    which is what keeps the omitted ordinary field values cryptographically represented
    (D112 §5, §14).
    """

    source_observation_id: str
    source_id: str
    artifact_sha256: str
    artifact_byte_length: int
    sidecar: CompactEvidenceSidecar | None = None
    digest: ProjectionDigest = dataclass_field(init=False)
    members: int = 0
    records: int = 0
    omitted: int = 0
    materialized: int = 0

    def __post_init__(self) -> None:
        self.digest = ProjectionDigest(self.source_id)
        self._seen: set[str] = set()

    def absorb(self, member_name: str, payload: bytes, outcome: ParseOutcome) -> None:
        """Record one member's manifest entry and fold its records into the digest."""
        ordinal = self.members
        self.members += 1
        payload_sha256 = hashlib.sha256(payload).hexdigest()
        self.digest.begin_member(ordinal, member_name, payload_sha256)
        registrants = accessions = other = omitted = materialized = 0
        for index, record in enumerate(outcome.records):
            record_class = record.native_identity.split(":", 1)[0]
            projection = canonical_projection(record.payload)
            relation: list[str] = []
            if record_class == "accession":
                accessions += 1
                first_witness = record.native_identity not in self._seen
                self._seen.add(record.native_identity)
                kept = materialized_fields(record.payload, first_witness=first_witness)
                materialized += len(kept)
                omitted += len(record.payload) - len(kept)
                if projection.registrant_cik_padded is not None:
                    relation.append(projection.registrant_cik_padded)
            elif record_class == "registrant":
                registrants += 1
            else:
                other += 1
            self.digest.record(
                ordinal=index,
                record_class=record_class,
                native_identity=record.native_identity,
                record_sha256=record.record_sha256,
                governed=dict(projection.as_digest_mapping()),
                relation=relation,
                exception=[*record.reason_codes, *record.unknown_fields],
            )
        self.records += len(outcome.records)
        self.omitted += omitted
        self.materialized += materialized
        member_digest = self.digest.end_member()
        if self.sidecar is not None:
            self.sidecar.record_member(
                self.source_observation_id,
                MemberManifestEntry(
                    member_ordinal=ordinal,
                    member_name=member_name,
                    payload_byte_length=len(payload),
                    payload_sha256=payload_sha256,
                    parsed_registrants=registrants,
                    parsed_accessions=accessions,
                    parsed_other=other,
                    quarantined=len(outcome.quarantined),
                    structural_failures=len(outcome.structural_failures),
                    omitted_field_observations=omitted,
                    materialized_field_observations=materialized,
                    projection_digest=member_digest,
                    disposition="parsed",
                ),
            )

    def finish(self) -> str:
        """Persist the source-level evidence row and return the completeness digest."""
        completeness = self.digest.hexdigest()
        if self.sidecar is not None:
            self.sidecar.record_source(
                source_observation_id=self.source_observation_id,
                source_id=self.source_id,
                artifact_sha256=self.artifact_sha256,
                artifact_byte_length=self.artifact_byte_length,
                members=self.members,
                records=self.records,
                omitted_field_observations=self.omitted,
                materialized_field_observations=self.materialized,
                completeness_digest=completeness,
            )
        return completeness


# --------------------------------------------------------------------------- #
# Bulk historical-shard dispatch (accepted Decision 129 §5, D129-R3)
# --------------------------------------------------------------------------- #
#: How many characters precede the ten CIK digits in a canonical historical shard name.
#:
#: The shape itself is owned by one matcher --
#: :data:`~disclosure_drift.sec.parsers.submissions.HISTORICAL_FILE_NAME_PATTERN`, whose
#: pattern is ``^CIK[0-9]{10}-submissions-[0-9]{3}\.json$``. This offset is only ever applied
#: to a name that matcher has already accepted, which is what makes a fixed slice exact
#: rather than a second, drifting copy of the shape.
_SHARD_CIK_OFFSET: Final = len("CIK")
_SHARD_CIK_DIGITS: Final = 10


@dataclass(frozen=True, slots=True)
class _DeferredHistoricalShard:
    """One bulk member deferred for the historical-submissions contract.

    Deliberately holds **no payload**. The whole point of deferring is that the shard's
    bytes are dropped with every other member's and re-read once its parent is known; a
    field for the payload here would reintroduce exactly the residency accepted
    Decision 110 §8 removed, multiplied by the 5,337 shards accepted Decision 129 §5
    counted in the first planned source.
    """

    member_ordinal: int
    member_name: str


def _shard_filename_cik(member_name: str) -> str:
    """Return the CIK a canonical historical shard name encodes.

    **Corroboration only** (accepted Decision 129 §7, D129-R5). The value this returns may
    confirm an explicit parent declaration and may refuse one that contradicts it. It is
    never the source of a binding: a shard whose parent no document declared is refused
    here rather than adopted from its own filename.

    Raises:
        OfflineParseError: the name is not a canonical historical shard name, or its digits
            do not normalize to a usable CIK.
    """
    if not HISTORICAL_FILE_NAME_PATTERN.match(member_name):
        message = (
            f"bulk member {member_name!r} was deferred as a historical shard but does not "
            f"match the canonical pattern {HISTORICAL_FILE_NAME_PATTERN.pattern}; no "
            "registrant is inferred from a name this parser cannot read"
        )
        raise OfflineParseError(message)
    digits = member_name[_SHARD_CIK_OFFSET : _SHARD_CIK_OFFSET + _SHARD_CIK_DIGITS]
    try:
        return normalize_cik(digits)[1]
    except IdentifierError as exc:  # pragma: no cover - the pattern already fixes ten digits
        message = f"historical shard {member_name!r} encodes an unusable CIK: {exc}"
        raise OfflineParseError(message) from exc


def _is_historical_shard_member(member_name: str) -> bool:
    """Whether one bulk archive member is a historical submissions shard.

    The canonical matcher is applied to the **whole** canonical member name, not to its
    basename: a shard is bound to its parent by an exact name, so a name that is only
    shard-shaped after a directory prefix is dropped could not be resolved safely. Such a
    member is refused rather than quietly routed to the primary parser, which is the D128
    behaviour accepted Decision 129 §5 rejected.

    Raises:
        OfflineParseError: the member's basename is shard-shaped but its full name is not.
    """
    if HISTORICAL_FILE_NAME_PATTERN.match(member_name):
        return True
    basename = member_name.rsplit("/", 1)[-1]
    if basename != member_name and HISTORICAL_FILE_NAME_PATTERN.match(basename):
        message = (
            f"bulk member {member_name!r} carries a historical shard basename beneath a "
            "directory prefix; the explicit parent declaration names a bare file, so this "
            "member cannot be bound to a registrant and is refused rather than parsed as a "
            "primary submissions document"
        )
        raise OfflineParseError(message)
    return False


def _historical_shard_member_names(archive_path: Path) -> frozenset[str]:
    """Every canonical historical-shard member name the archive actually holds.

    Read from the archive's central directory alone: **no member is decompressed and no
    payload is read**, so this is not the extra pass over ~985k JSON documents that building
    the parent map from the documents themselves would require. It is the same index
    :func:`~disclosure_drift.sec.archive.iter_members` builds before it yields anything, read
    for one question.

    It exists to keep the parent map bounded by the *shard* population rather than by the
    *declaration* population. Those are the same size in a healthy archive, but they are not
    the same thing: a document may declare an overflow file the archive does not carry, and
    retaining that declaration would make the traversal's residency grow with members while
    answering a question nothing will ever ask. Accepted Decision 110 §8 boundedness is a
    property of the traversal, not an approximation of one.

    Raises:
        ArchiveDefenceError: the archive is corrupt, or a member name is hostile.
    """
    names: set[str] = set()
    try:
        with zipfile.ZipFile(archive_path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                canonical = canonical_member_name(info.filename)
                if HISTORICAL_FILE_NAME_PATTERN.match(canonical):
                    names.add(canonical)
    except zipfile.BadZipFile as exc:
        message = (
            f"archive {archive_path.name} is corrupt and is refused rather than read as "
            f"holding no historical shards: {exc}"
        )
        raise ArchiveDefenceError(message) from exc
    return frozenset(names)


def _declare_shard_parents(
    declared: dict[str, set[str]],
    references: Sequence[HistoricalFileReference],
    shard_members: frozenset[str],
) -> None:
    """Fold one primary document's ``filings.files`` declarations into the parent map.

    The declaring document is the authority (accepted Decision 129 §7, D129-R5), so the key
    is the exact name it declared and the value is its own registrant.

    A declaration is retained **only when the archive carries a member of exactly that
    name**. That is what keeps this map bounded by the shard population rather than growing
    with every member the traversal reads, and it drops nothing that could ever be consulted:
    a declaration naming a file the archive does not hold binds no member. Retention is not a
    judgement about the declaration -- the reference row itself is persisted either way.
    """
    if not shard_members:
        return
    for reference in references:
        name = reference.name
        if name is None or name not in shard_members:
            continue
        declared.setdefault(name, set()).add(reference.registrant_cik_padded)


def _resolve_shard_parent(member_name: str, declared: Mapping[str, set[str]]) -> str:
    """Resolve one deferred shard's registrant, or fail closed.

    Every refusal here is accepted Decision 129 §7 (D129-R5) read literally: a missing,
    ambiguous, or contradicted binding produces no registrant at all rather than a
    plausible one. A declaration naming a different member simply never keys this shard, so
    "the parent declared some other file" arrives as the missing-declaration refusal.

    Raises:
        OfflineParseError: no parent declared this shard, more than one distinct parent did,
            or the name's own CIK contradicts the declared parent.
    """
    filename_cik = _shard_filename_cik(member_name)
    parents = declared.get(member_name)
    if not parents:
        message = (
            f"historical shard {member_name!r} is present in the bulk archive but no "
            "primary submissions document declares it under filings.files; the shard's own "
            "filename is corroboration and never a binding, so the traversal refuses rather "
            "than adopting the registrant its name encodes"
        )
        raise OfflineParseError(message)
    if len(parents) > 1:
        message = (
            f"historical shard {member_name!r} is declared by {len(parents)} distinct "
            f"registrants ({sorted(parents)}); exactly one authoritative parent is required "
            "and no tie is broken"
        )
        raise OfflineParseError(message)
    parent = next(iter(parents))
    if parent != filename_cik:
        message = (
            f"historical shard {member_name!r} is declared by registrant {parent} but its "
            f"canonical filename encodes {filename_cik}; the corroboration disagrees with "
            "the explicit parent and the traversal refuses rather than choosing one"
        )
        raise OfflineParseError(message)
    return parent


def _stream_deferred_historical_shards(
    archive_path: Path,
    observation: SourceObservation,
    deferred: Sequence[_DeferredHistoricalShard],
    declared: Mapping[str, set[str]],
    *,
    evidence: CompactSourceEvidence | None = None,
) -> Iterator[tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]]:
    """Parse every deferred historical shard, after the parent map is complete.

    This is the second half of the order-independent dispatch. The first half met each shard
    during the primary traversal and kept only its name and ordinal; by the time this runs,
    every primary document in the archive has declared whatever it declares, so a shard's
    parent is resolvable no matter where the two sat relative to each other (accepted
    Decision 129 §7, D129-R6).

    **Every parent is resolved before any member is reopened.** A refusal therefore costs no
    decompression and, more importantly, cannot leave half the deferred population parsed and
    the other half refused.

    Shards are processed in their original archive ordinal order, so the correction itself
    introduces no ordering of its own. A shard yields no historical references: an overflow
    document declares no ``filings.files`` of its own.
    """
    if not deferred:
        return
    ordered = sorted(deferred, key=lambda item: item.member_ordinal)
    resolved = [
        (item.member_name, _resolve_shard_parent(item.member_name, declared)) for item in ordered
    ]
    try:
        # The reopen is the archive layer's own public named-member read, so the per-member
        # size, type, and traversal defences applied here are exactly the ones the primary
        # traversal applied -- one implementation, reached through one public surface, rather
        # than a second expression of the same answers in this module.
        members = iter_named_members(archive_path, [name for name, _ in resolved])
        for (member_name, parent_cik), (read_name, payload) in zip(resolved, members, strict=True):
            if read_name != member_name:  # pragma: no cover - the reader yields in order
                message = (
                    f"historical shard reopen returned member {read_name!r} where "
                    f"{member_name!r} was requested; the parse is refused rather than bound "
                    "to a registrant resolved for a different member"
                )
                raise OfflineParseError(message)
            location = RecordLocation(
                observation.observation_id,
                observation.source_id,
                member_name=member_name,
            )
            decoded = _json_document(payload, f"bulk historical shard {member_name!r}")
            outcome = parse_historical_submissions(decoded, location, registrant_cik=parent_cik)
            if evidence is not None:
                # The shard's one and only governed member record, written here because this
                # is the first point at which its bytes and its real parse both exist. It was
                # deliberately not recorded during the primary traversal: a member recorded
                # as parsed before its parse would be a false witness in the manifest.
                evidence.absorb(member_name, payload, outcome)
            yield outcome, ()
    except ArchiveDefenceError as exc:
        message = f"accepted bulk archive refused on historical-shard reopen: {exc}"
        raise OfflineParseError(message) from exc


# --------------------------------------------------------------------------- #
# The read-only structural source preflight -- D140-R21 (INFO-9 / INFO-10)
# --------------------------------------------------------------------------- #
#: How many offending member names a structural preflight names in its report.
#:
#: The report is evidence, not a log: a source whose parent map is broken in ten thousand places
#: is not better understood by listing ten thousand names, and the digest below is what makes the
#: whole result comparable anyway.
STRUCTURAL_PREFLIGHT_REPORT_LIMIT: Final = 20

#: The structural preflight's own contract identity, folded into its digest.
STRUCTURAL_PREFLIGHT_CONTRACT: Final = "m3.3-structural-source-preflight/1.0"


@dataclass(frozen=True, slots=True)
class StructuralSourcePreflight:
    """What one bulk archive's shard-to-parent structure actually is, proved before F0 runs.

    **Why this exists.** The D129 correction bound every historical overflow shard to the
    registrant its **primary document explicitly declares** under ``filings.files``. That binding
    is resolved during F0, roughly twenty-seven hours into a complete-source run -- so a source
    whose parent map is broken in any of the six ways :func:`_resolve_shard_parent` refuses would
    be discovered at the end of a day and a half of work, with a ~120 GiB world already built.

    This asks the same question first, from the archive alone, in minutes. It **populates
    nothing**: no SQLite, no world, no catalog, no parser run, no evidence row. It reads.
    """

    governed_members: int
    shard_members: int
    declared_shard_names: int
    shard_before_parent: bool
    orphan_shards: tuple[str, ...]
    duplicate_parent_shards: tuple[str, ...]
    conflicting_parent_shards: tuple[str, ...]
    orphan_count: int
    duplicate_parent_count: int
    conflicting_parent_count: int
    digest: str

    @property
    def parent_map_sound(self) -> bool:
        """Whether every governed shard has exactly one lawful declaring parent."""
        return (
            self.orphan_count == 0
            and self.duplicate_parent_count == 0
            and self.conflicting_parent_count == 0
        )

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "contract": STRUCTURAL_PREFLIGHT_CONTRACT,
            "governed_members": self.governed_members,
            "shard_members": self.shard_members,
            "declared_shard_names": self.declared_shard_names,
            "shard_before_parent": self.shard_before_parent,
            "orphan_count": self.orphan_count,
            "duplicate_parent_count": self.duplicate_parent_count,
            "conflicting_parent_count": self.conflicting_parent_count,
            "orphan_shards": list(self.orphan_shards),
            "duplicate_parent_shards": list(self.duplicate_parent_shards),
            "conflicting_parent_shards": list(self.conflicting_parent_shards),
            "parent_map_sound": self.parent_map_sound,
            "structural_preflight_digest": self.digest,
        }


def _primary_document_declarations(payload: bytes) -> tuple[str | None, tuple[str, ...]]:
    """One primary document's own registrant and the overflow names it declares.

    Reads the two fields the D129 parent rule depends on and nothing else. It is deliberately
    **not** the submissions parser: running the full parser over ~985,000 documents is F0's
    work, and repeating it here would make the preflight cost what the run costs. The *rule* is
    not restated -- resolution goes through :func:`_resolve_shard_parent` exactly as F0's does;
    only the extraction is narrowed to the two fields that rule reads.
    """
    try:
        document = json.loads(payload)
    except (ValueError, UnicodeDecodeError):
        return None, ()
    if not isinstance(document, dict):
        return None, ()
    raw_cik = document.get("cik")
    padded: str | None = None
    if raw_cik is not None:
        try:
            padded = normalize_cik(str(raw_cik))[1]
        except IdentifierError:
            padded = None
    filings = document.get("filings")
    names: list[str] = []
    if isinstance(filings, dict):
        files = filings.get("files")
        if isinstance(files, list):
            for entry in files:
                if not isinstance(entry, dict):
                    continue
                raw_name = entry.get("name")
                if raw_name is None:
                    continue
                name = str(raw_name).strip()
                if name:
                    names.append(name)
    return padded, tuple(names)


def structural_source_preflight(
    archive_path: Path,
    *,
    report_limit: int = STRUCTURAL_PREFLIGHT_REPORT_LIMIT,
) -> StructuralSourcePreflight:
    """Prove the shard-to-parent structure of one bulk archive, read-only -- D140-R21.

    One traversal of the archive. For each member it decides, by the accepted
    :func:`_is_historical_shard_member` predicate, whether the member is a governed historical
    shard or a primary submissions document; primary documents contribute their explicit
    ``filings.files`` declarations to the parent map, and shards are remembered in the order they
    appear so that **shard-before-parent ordering** is observed rather than assumed.

    Resolution is then the accepted rule applied verbatim: every governed shard the archive
    carries is passed to :func:`_resolve_shard_parent`, which refuses a missing declaration, more
    than one distinct declaring registrant, and a declared parent that the shard's own filename
    contradicts. **The filename remains corroboration and never a binding**, and no competing
    parent algorithm is introduced here.

    **It populates nothing and writes nothing.** No SQLite connection is opened, no world is
    created, no parser run is seeded, and F0 is not run.

    Args:
        archive_path: The bulk archive to read.
        report_limit: How many offending names to name per class.

    Returns:
        The structural facts, with a deterministic digest over all of them.

    Raises:
        ArchiveDefenceError: the archive is corrupt or hostile.
        OfflineParseError: a member's name is shard-shaped only beneath a directory prefix,
            which the accepted predicate refuses rather than routing to the primary parser.
    """
    shard_members = _historical_shard_member_names(archive_path)
    declared: dict[str, set[str]] = {}
    #: Shards already met in archive order. A set rather than a list because the ordering
    #: observation below is a membership test per declaration, and rebuilding a frozenset each
    #: time would make the preflight quadratic in a source with five thousand shards.
    seen_shards: set[str] = set()
    shard_before_parent = False
    governed_members = 0
    # ``name_suffix=".json"`` and the raw ``member.name`` are both exactly what
    # :func:`_stream_bulk_submissions` uses. The preflight must count and classify the same
    # population F0 will: a governed member count derived under different filters would be a
    # different number about a different question, and comparing it to the accepted structural
    # facts would prove nothing.
    for member in iter_members(archive_path, name_suffix=".json"):
        governed_members += 1
        if _is_historical_shard_member(member.name):
            seen_shards.add(canonical_member_name(member.name))
            continue
        padded, declarations = _primary_document_declarations(member.payload)
        if padded is None:
            continue
        for declaration in declarations:
            if declaration not in shard_members:
                # Bounded exactly as `_declare_shard_parents` bounds it: a declaration naming a
                # file the archive does not carry binds no member, and retaining it would grow
                # the map with declarations instead of with shards.
                continue
            if declaration in seen_shards:
                shard_before_parent = True
            declared.setdefault(declaration, set()).add(padded)
    orphans: list[str] = []
    duplicates: list[str] = []
    conflicts: list[str] = []
    for name in sorted(shard_members):
        parents = declared.get(name)
        if not parents:
            orphans.append(name)
            continue
        if len(parents) > 1:
            duplicates.append(name)
            continue
        try:
            _resolve_shard_parent(name, declared)
        except OfflineParseError:
            # The remaining refusal the accepted rule makes: the declared parent and the CIK
            # the filename encodes disagree. Recorded rather than raised, so that one report
            # describes every governed shard instead of stopping at the first bad one.
            conflicts.append(name)
    digest = hashlib.sha256()
    for part in (
        STRUCTURAL_PREFLIGHT_CONTRACT,
        str(governed_members),
        str(len(shard_members)),
        str(len(declared)),
        str(shard_before_parent),
        *sorted(orphans),
        "\x1e",
        *sorted(duplicates),
        "\x1e",
        *sorted(conflicts),
    ):
        digest.update(part.encode("utf-8"))
        digest.update(b"\x1f")
    return StructuralSourcePreflight(
        governed_members=governed_members,
        shard_members=len(shard_members),
        declared_shard_names=len(declared),
        shard_before_parent=shard_before_parent,
        orphan_shards=tuple(orphans[:report_limit]),
        duplicate_parent_shards=tuple(duplicates[:report_limit]),
        conflicting_parent_shards=tuple(conflicts[:report_limit]),
        orphan_count=len(orphans),
        duplicate_parent_count=len(duplicates),
        conflicting_parent_count=len(conflicts),
        digest=digest.hexdigest(),
    )


def require_sound_parent_map(preflight: StructuralSourcePreflight) -> StructuralSourcePreflight:
    """Return ``preflight``, or refuse the run before a world exists -- D140-R21.

    Raises:
        OfflineParseError: a governed shard has no declaring parent, more than one, or a parent
            its own filename contradicts.
    """
    if preflight.parent_map_sound:
        return preflight
    message = (
        "the bulk source's historical shard parent map is not sound: "
        f"{preflight.orphan_count} shard(s) no primary document declares, "
        f"{preflight.duplicate_parent_count} declared by more than one distinct registrant, and "
        f"{preflight.conflicting_parent_count} whose declared parent contradicts the CIK their "
        "own filename encodes. STOP AND REPORT: this is the condition F0 would otherwise have "
        "discovered roughly twenty-seven hours into a complete-source run, with the world "
        "already built. No world was created, nothing was parsed, and the source evidence is "
        "not repaired -- a source that does not satisfy the accepted Decision 129 parent rule "
        "is reported, never adjusted to fit it. "
        f"First offenders: orphan={list(preflight.orphan_shards)}, "
        f"duplicate={list(preflight.duplicate_parent_shards)}, "
        f"conflicting={list(preflight.conflicting_parent_shards)}"
    )
    raise OfflineParseError(message)


def _stream_bulk_submissions(
    store: SnapshotStore,
    observation: SourceObservation,
    *,
    evidence: CompactSourceEvidence | None = None,
    max_members: int | None = None,
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

    **The diagnostic member cap** (``max_members``, accepted Decision 119 §6) changes nothing
    about which members are traversed or in what order: it is a count of members already
    yielded, checked at the point the consumer asks for the next one. ``None`` -- the default,
    and what every production caller passes -- is the traversal exactly as it was.

    A cap that is set **always** ends the traversal by raising :class:`_DiagnosticPrefixLimit`,
    including when the archive runs out of members first. That is deliberate: the consumer's
    normal exhaustion path finalizes a parser run, and a bounded prefix must never reach it, not
    even when its bound happens to be the whole archive.

    **Two member shapes, two parsers** (accepted Decision 129 §5, D129-R3). The archive holds
    primary documents named ``CIK##########.json`` and historical overflow shards named
    ``CIK##########-submissions-NNN.json``. A shard is not one document describing one CIK,
    which is the primary parser's whole contract, and D128 routed 5,337 of them through it
    anyway: they were refused -- correctly -- and 3,037,614 accessions went unrecorded. A shard
    now reaches :func:`~disclosure_drift.sec.parsers.historical.parse_historical_submissions`
    instead, under the registrant its parent explicitly declared.

    **Shards are deferred, and the deferral is what makes archive order irrelevant.** A shard's
    parent is whichever primary document names it under ``filings.files``, and that document
    may sit anywhere in the archive -- before the shard, after it, or nowhere. Meeting a shard
    therefore records only its name and its ordinal, never its bytes, and every shard is parsed
    after the traversal ends, in original archive ordinal order, against a parent map that is
    by then complete. Correctness does not depend on which of the two came first (D129-R6),
    and no shard is recorded as parsed before its parse actually happens.

    **Under a diagnostic cap the deferred phase does not run.** A prefix stops mid-archive, so
    its parent map is incomplete by construction and resolving a shard against it would refuse
    a well-formed archive. A shard met inside the prefix counts against the bound as a member
    the traversal handled, which is what ``--member-limit`` names; it is simply never parsed.
    A prefix finalizes nothing and can never report success, so it carries no claim about the
    shard population either way.

    Raises:
        OfflineParseError: the archive is refused by the archive defences, a member's payload
            is not a decodable JSON object, or a deferred shard cannot be bound to exactly one
            explicitly declared parent registrant.
        _DiagnosticPrefixLimit: ``max_members`` was set and the traversal has stopped.
    """
    store.verify_payload(observation)
    path = store.payload_path(observation)
    processed = 0
    deferred: list[_DeferredHistoricalShard] = []
    declared: dict[str, set[str]] = {}
    try:
        shard_members = _historical_shard_member_names(path)
        for member in iter_members(
            path,
            name_suffix=".json",
            archive_relative_path=observation.relative_storage_path,
            archive_sha256=observation.logical_sha256,
        ):
            if _is_historical_shard_member(member.name):
                # Bounded metadata only. The payload in hand is dropped with the member, and
                # the shard is reopened by this exact name once the parent map is complete.
                deferred.append(
                    _DeferredHistoricalShard(
                        member_ordinal=member.member_index,
                        member_name=member.name,
                    )
                )
                processed += 1
                if max_members is not None and processed >= max_members:
                    raise _DiagnosticPrefixLimit(processed)
                continue
            location = RecordLocation(
                observation.observation_id,
                observation.source_id,
                member_name=member.name,
            )
            decoded = _json_document(member.payload, f"bulk member {member.name!r}")
            parsed = parse_submissions_document(decoded, location)
            _declare_shard_parents(declared, parsed[1], shard_members)
            if evidence is not None:
                # Recorded here because this is the only point at which the member's bytes and
                # its parse both exist, and recording it anywhere else would mean either a
                # second traversal of a 1.56 GB archive or retaining what the stream exists to
                # drop (accepted Decision 112 §§4.A, 4.E).
                evidence.absorb(member.name, member.payload, parsed[0])
            yield parsed
            # After the yield, so the count is of members the consumer has finished writing
            # rather than of members handed to it. A deferred shard increments it above
            # instead, at the point this traversal has finished with it.
            processed += 1
            if max_members is not None and processed >= max_members:
                raise _DiagnosticPrefixLimit(processed)
    except ArchiveDefenceError as exc:
        message = f"accepted bulk archive refused by the archive defences: {exc}"
        raise OfflineParseError(message) from exc
    if max_members is not None:
        raise _DiagnosticPrefixLimit(processed)
    yield from _stream_deferred_historical_shards(
        path,
        observation,
        deferred,
        declared,
        evidence=evidence,
    )


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


@dataclass(frozen=True, slots=True)
class FullIndexCorroboration:
    """What one ``company.idx`` quarter's R23 materialization produced (D113 §§9-10).

    ``corroborating`` rows are the ones represented by their parsed record alone; ``exceptions``
    are the ones D113 §10 keeps as explicit observation rows. Under the full-observation
    contract every bound row is an exception by definition, because nothing is compacted.
    """

    written: int
    unbound: tuple[str, ...]
    index_rows: int = 0
    corroborating: int = 0
    exceptions: int = 0
    omitted_observations: int = 0
    digest: str = ""


def _corroboration_disposition(
    payload: Mapping[str, object],
    canonical: sqlite3.Row | None,
    *,
    cik_padded: str,
) -> str:
    """Whether one bound index row merely corroborates the canonical accession (D113 §9).

    ``corroborating`` requires the row to agree with everything the canonical accession row
    already states and to add no member to the association set: the same registrant, the same
    form, the same filing date, and a canonical row that actually carries all three. Anything
    else -- a co-registrant, a disagreement, or a canonical value not yet established -- is a
    D113 §10 exception and keeps its observation rows, because each of those can change a
    Decision 012 resolution, the association set, or the totality classification, and §10
    forbids compacting any of them into a boolean.

    Requiring the canonical values to be present is not caution for its own sake: an accession
    whose canonical column is NULL cannot reconstruct the observation the omitted row carried,
    so omitting it there would not be reconstructible and would break D113 §12.
    """
    if canonical is None:
        return "exception"
    registrant = canonical["registrant_cik_padded"]
    form = canonical["form_type"]
    filing_date = canonical["filing_date_sec"]
    if registrant is None or form is None or filing_date is None:
        return "exception"
    if str(registrant) != cik_padded:
        return "exception"
    observed_form = payload.get("form_type")
    observed_date = payload.get("date_filed")
    if observed_form is not None and str(observed_form) != str(form):
        return "exception"
    if observed_date is not None and str(observed_date) != str(filing_date):
        return "exception"
    return "corroborating"


def _materialize_full_index_registrants(
    connection: sqlite3.Connection,
    *,
    observation: SourceObservation,
    parser_run_id: str,
    recorded: str,
    compact: bool = False,
) -> FullIndexCorroboration:
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

    Under the accepted **Decision 113 §9** contract a row that merely corroborates an
    already-canonical accession writes no observation row at all. Its parsed record is the
    assertion -- accession identity, quarter identity, CIK, form, filing date, line number, and
    a ``record_sha256`` over the complete raw row -- and :func:`census._corroboration_rows`
    restores from it the identical observations this function would have written. Everything
    D113 §10 names stays explicit.

    Accessions are looked up **one at a time** against the primary key rather than preloaded
    into a set (accepted Decision 110 §8). The preloaded form held one string per accession in
    the catalog, which on E0's first planned source is roughly 21.5 million strings and about
    2.9 GB -- on its own more than this host's whole memory budget, in a path D110 did not
    reach because no index quarter had been parsed yet. The same lookup now also returns the
    canonical values the corroboration verdict needs, so the per-row cost is one seek either
    way.

    Returns the counts, the corroboration digest, and the accessions the index listed that the
    authoritative accession layer does not carry. Those are reported, never created:
    ``census_accession_observations.accession_plain`` is a foreign key into
    ``census_accessions``, so an index-only accession is refused by the schema as well
    as by this check (**R23** §5.1).
    """
    rows = connection.execute(
        "SELECT parsed_record_id, native_identity, record_sha256, payload_json "
        "FROM census_parsed_records "
        "WHERE parser_run_id = ? AND native_identity LIKE ? ORDER BY parsed_record_id",
        (parser_run_id, f"{INDEX_ROW_PREFIX}%"),
    )
    digest = CorroborationDigest(observation.source_id, observation.logical_sha256 or "")
    written = 0
    index_rows = 0
    corroborating = 0
    exceptions = 0
    omitted = 0
    unbound: set[str] = set()
    with transaction(connection) as active:
        for row in rows:
            payload = _index_payload(row["payload_json"])
            if payload is None:
                continue
            plain, cik_padded = _index_identity(payload)
            if plain is None or cik_padded is None:
                continue
            index_rows += 1
            canonical = active.execute(
                "SELECT form_type, filing_date_sec, "
                "CASE WHEN registrant_cik_numeric IS NULL THEN NULL "
                "ELSE printf('%010d', registrant_cik_numeric) END AS registrant_cik_padded "
                "FROM census_accessions WHERE accession_plain = ?",
                (plain,),
            ).fetchone()
            if canonical is None:
                unbound.add(plain)
                continue
            disposition = (
                _corroboration_disposition(payload, canonical, cik_padded=cik_padded)
                if compact
                else "materialized"
            )
            observed = dict(corroboration_observations(payload, cik_padded=cik_padded))
            digest.record(
                native_identity=str(row["native_identity"]),
                record_sha256=str(row["record_sha256"]),
                accession_plain=plain,
                cik_padded=cik_padded,
                observed=observed,
                disposition=disposition,
            )
            if disposition == "corroborating":
                corroborating += 1
                omitted += len(observed)
                continue
            exceptions += 1
            for field, value in observed.items():
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
                        _stable_json(value),
                        recorded,
                    ),
                )
                written += 1
    return FullIndexCorroboration(
        written=written,
        unbound=tuple(sorted(unbound)),
        index_rows=index_rows,
        corroborating=corroborating,
        exceptions=exceptions,
        omitted_observations=omitted,
        digest=digest.hexdigest(),
    )


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


def _stored_membership_rows(connection: sqlite3.Connection) -> Iterator[Mapping[str, Any]]:
    """Every persisted membership observation, in canonical order."""
    cursor = connection.execute(
        "SELECT o.accession_plain, o.accession_observation_id, o.field_name, o.raw_value_json, "
        "o.source_observation_id, o.parsed_record_id, o.observed_at_utc, o.conflict_indicator "
        "FROM census_accession_observations AS o "
        "WHERE o.field_name IN (?, ?) "
        "ORDER BY o.accession_plain, o.accession_observation_id",
        SUBMISSIONS_MEMBERSHIP_FIELDS,
    )
    for row in cursor:
        yield dict(row)


def _reconstructed_membership_rows(
    connection: sqlite3.Connection,
) -> Iterator[Mapping[str, Any]]:
    """The membership observation each canonical accession row implies, in canonical order.

    The compact contract's membership half (accepted Decision 112 §§4.C, 6). The submissions
    ``cik`` observation of an accession's first witness is not stored, because the canonical
    row carries the same value with the same provenance; this restores it as the row it would
    have been. A second witness, a malformed rendering, and every full-index observation are
    stored rather than reconstructed, so they arrive through the other cursor and are not
    duplicated here.

    One ordered scan of ``census_accessions``, consumed lazily, so the memory bound Decision
    094 §6.4 requires is unchanged.
    """
    # The ``NOT EXISTS`` probe is a range over the accepted unique index
    # ``(accession_plain, source_observation_id, parsed_record_id, field_name)`` -- one seek per
    # accession, no intermediate, and the same shape accepted Decision 111 established for the
    # conflict pass. A row whose observation *is* stored was back-filled beside a rival and
    # must not be reconstructed as well.
    cursor = connection.execute(
        "SELECT a.accession_plain, a.source_observation_id, a.parsed_record_id, "
        "a.first_observed_at_utc, printf('%010d', a.registrant_cik_numeric) "
        "AS registrant_cik_padded "
        "FROM census_accessions AS a "
        "WHERE a.registrant_cik_numeric IS NOT NULL AND NOT EXISTS ("
        "SELECT 1 FROM census_accession_observations AS o "
        "WHERE o.accession_plain = a.accession_plain "
        "AND o.source_observation_id = a.source_observation_id "
        "AND o.parsed_record_id = a.parsed_record_id AND o.field_name = 'cik') "
        "ORDER BY a.accession_plain"
    )
    for row in cursor:
        padded = str(row["registrant_cik_padded"])
        accession_plain = str(row["accession_plain"])
        observation_id = str(row["source_observation_id"])
        parsed_id = str(row["parsed_record_id"])
        yield {
            "accession_plain": accession_plain,
            "accession_observation_id": _stable_id(
                "accession-observation", accession_plain, observation_id, parsed_id, "cik"
            ),
            "field_name": "cik",
            "raw_value_json": _stable_json(padded),
            "source_observation_id": observation_id,
            "parsed_record_id": parsed_id,
            "observed_at_utc": str(row["first_observed_at_utc"]),
            "conflict_indicator": 0,
        }


def _corroborated_membership_rows(
    connection: sqlite3.Connection,
) -> Iterator[Mapping[str, Any]]:
    """The membership rows the full-index corroboration assertions imply (D113 §9).

    A corroborating ``company.idx`` row writes no ``cik_padded`` observation; its parsed record
    is the assertion. This restores the row that assertion implies -- the same deterministic
    identifier, the same rendering, the same provenance -- so the §6.2 membership projection
    sees the corroboration it must see to call an association set corroborated, and the
    accepted §9.5 totality is unchanged.

    One ordered scan over ``idx_census_parsed_identity``. The parser stamps
    ``index_row:{dashed accession}:{line}`` and the dashes sit at fixed positions, so scanning
    by native identity is scanning by accession; rows for one accession are buffered and sorted
    on the observation identifier, which is bounded by how many quarters list one accession
    rather than by the source.

    The "was this row kept explicit?" probe is asked **after** the payload is decoded, on the
    full ``(accession, source observation, parsed record, field)`` key. That is the accepted
    unique index's own prefix, so it is one seek. Asked the obvious way -- a correlated
    ``NOT EXISTS`` on ``parsed_record_id`` alone inside the scan -- it cannot use that index at
    all, because ``parsed_record_id`` is its third column, and every index row would scan the
    whole observation table: the same shape D112 §2.6 removed from the duplicate-flag
    derivation, measured here as a real source that had not finished in fifty-two minutes.
    """
    buffered: list[Mapping[str, Any]] = []
    current: str | None = None
    for row in connection.execute(
        "SELECT p.parsed_record_id, p.source_observation_id, p.payload_json, p.recorded_at_utc "
        "FROM census_parsed_records AS p "
        "WHERE p.native_identity >= ? AND p.native_identity < ? "
        "ORDER BY p.native_identity",
        (INDEX_ROW_PREFIX, f"{INDEX_ROW_PREFIX};"),
    ):
        payload = _index_payload(row["payload_json"])
        if payload is None:
            continue
        plain, cik_padded = _index_identity(payload)
        if plain is None or cik_padded is None:
            continue
        if _membership_observation_stored(
            connection, plain, str(row["source_observation_id"]), str(row["parsed_record_id"])
        ):
            # D113 §10 kept this row explicit, so the stored cursor already carries it.
            continue
        if not _accession_is_known(connection, plain):
            # **R23** §5.1: a full-index row never creates an accession, and the accepted
            # materialization writes no observation for one the authoritative layer does not
            # carry. Reconstructing one here would hand the §6.4 projection a group for an
            # accession that does not exist, which it counts as an orphan -- a totality
            # difference the full-observation path never produces.
            continue
        if plain != current:
            yield from sorted(buffered, key=lambda item: str(item["accession_observation_id"]))
            buffered = []
            current = plain
        buffered.append(
            {
                "accession_plain": plain,
                "accession_observation_id": _stable_id(
                    "accession-observation",
                    plain,
                    str(row["source_observation_id"]),
                    str(row["parsed_record_id"]),
                    _INDEX_MEMBERSHIP_FIELD,
                ),
                "field_name": _INDEX_MEMBERSHIP_FIELD,
                "raw_value_json": _stable_json(cik_padded),
                "source_observation_id": str(row["source_observation_id"]),
                "parsed_record_id": str(row["parsed_record_id"]),
                "observed_at_utc": str(row["recorded_at_utc"]),
                "conflict_indicator": 0,
            }
        )
    yield from sorted(buffered, key=lambda item: str(item["accession_observation_id"]))


def _membership_observation_stored(
    connection: sqlite3.Connection,
    accession_plain: str,
    source_observation_id: str,
    parsed_record_id: str,
) -> bool:
    """Whether one index row's membership observation is stored rather than reconstructed.

    One seek against the accepted
    ``(accession_plain, source_observation_id, parsed_record_id, field_name)`` unique index.
    """
    return (
        connection.execute(
            "SELECT 1 FROM census_accession_observations WHERE accession_plain = ? "
            "AND source_observation_id = ? AND parsed_record_id = ? AND field_name = ?",
            (accession_plain, source_observation_id, parsed_record_id, _INDEX_MEMBERSHIP_FIELD),
        ).fetchone()
        is not None
    )


def _preserve_reconstructed_membership(
    connection: sqlite3.Connection,
    accession_plain: str,
    compact: bool,
) -> int:
    """Materialize the ``cik`` observation the canonical row implies, before it is cleared.

    The compact contract omits an accession's submissions-side membership observation because
    ``census_accessions.registrant_cik_numeric`` carries the identical value with the identical
    provenance, so the row is reconstructible (D112 §2.3). §6.4 item 2 then **clears that very
    column** on a multi-registrant accession, which makes the omitted row unreconstructible from
    that point on. Writing it once, immediately before the clear, keeps the evidence and keeps
    the two association traversals reading the same group.

    The row is byte-for-byte the one the full-observation contract already holds: the same
    deterministic identifier, the same rendering, the same provenance triple, and
    ``conflict_indicator = 0`` -- which is the accepted conflict pass's own answer here, because
    it marks rivals within one ``field_name`` and a full-index co-registrant observes
    ``cik_padded`` rather than ``cik``. Where a second submissions witness *did* disagree, the
    incumbent is already stored and this is an ``INSERT OR IGNORE`` no-op.

    Returns:
        1 when a row was written, 0 otherwise.
    """
    if not compact:
        return 0
    row = connection.execute(
        "SELECT source_observation_id, parsed_record_id, first_observed_at_utc, "
        "printf('%010d', registrant_cik_numeric) AS registrant_cik_padded "
        "FROM census_accessions WHERE accession_plain = ? AND registrant_cik_numeric IS NOT NULL",
        (accession_plain,),
    ).fetchone()
    if row is None:
        return 0
    connection.execute(
        "INSERT OR IGNORE INTO census_accession_observations "
        "(accession_observation_id, accession_plain, source_observation_id, parsed_record_id, "
        "field_name, raw_value_json, observed_at_utc, conflict_indicator) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
        (
            _stable_id(
                "accession-observation",
                accession_plain,
                str(row["source_observation_id"]),
                str(row["parsed_record_id"]),
                _SUBMISSIONS_MEMBERSHIP_FIELD,
            ),
            accession_plain,
            str(row["source_observation_id"]),
            str(row["parsed_record_id"]),
            _SUBMISSIONS_MEMBERSHIP_FIELD,
            _stable_json(str(row["registrant_cik_padded"])),
            str(row["first_observed_at_utc"]),
        ),
    )
    return 1


def _merged_membership_rows(
    connection: sqlite3.Connection,
    *,
    compact: bool,
) -> Iterator[Mapping[str, Any]]:
    """The membership rows the projection reads, whichever evidence contract wrote them.

    Under the full-observation contract this is one cursor. Under the compact contract it is
    the ordered merge of three streams -- the stored rows, the canonical accession rows'
    reconstruction (D112), and the full-index corroboration assertions' reconstruction
    (D113 §9) -- on ``(accession_plain, accession_observation_id)``: the same key and the same
    direction the single cursor ordered by, so the merged stream is indistinguishable from it.
    """
    stored = _stored_membership_rows(connection)
    if not compact:
        yield from stored
        return
    yield from heapq.merge(
        stored,
        _reconstructed_membership_rows(connection),
        _corroborated_membership_rows(connection),
        key=lambda row: (str(row["accession_plain"]), str(row["accession_observation_id"])),
    )


def _stream_membership_groups(
    connection: sqlite3.Connection,
    eligible: Mapping[str, str],
    *,
    compact: bool = False,
) -> Iterator[_MembershipGroup]:
    """Yield one accession's membership group at a time, in canonical accession order.

    The cursor is consumed lazily and the accumulator is reset at every accession
    boundary, so peak memory is one accession's membership and provenance rather than the
    whole catalog's (**Decision 094 §6.4**).
    """
    cursor = _merged_membership_rows(connection, compact=compact)
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


def _blocking_fields_clear(
    connection: sqlite3.Connection,
    accession_plain: str,
    *,
    compact: bool = False,
) -> bool:
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

    Under the accepted **Decision 113 §4** contract an accession whose resolution is the
    implicit default has no rows here at all, and silence is then not a missing resolution but
    an omitted one. The reader reconstructs it rather than failing the accession closed, which
    is the difference between a row that is absent because nothing resolved it and a row that
    is absent because the canonical evidence already states it.
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
    if compact and not latest:
        resolution = reconstructed_accession_resolution(connection, accession_plain)
        return all(
            (item := resolution.fields.get(field)) is not None
            and item.status in _RESOLVED_STATUSES
            and not item.blocks_dependents
            for field in _MEMBERSHIP_BLOCKING_FIELDS
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
    compact_evidence: bool = False,
    capacity_guard: Callable[[], None] | None = None,
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

    **Capacity is enforced from inside this transaction, not beside it** (Decision 138, D138-R8
    and D138-R9). ``capacity_guard`` is called once before the transaction opens and again from
    both membership traversals, so a free-space floor reached mid-projection raises **while the
    transaction is still open** and the rollback above discards the in-flight projection rather
    than leaving a partial one. It is called on every iteration and decides for itself whether
    enough wall-clock time has passed to take a reading, which is what keeps a per-accession call
    affordable; it returns ``None`` and changes nothing on every path that does not breach.
    Omitted, this function behaves exactly as accepted Decision 094 §6.4 left it — the guard adds
    a stopping condition and no association semantics whatsoever.

    Args:
        connection: The writing connection, already inside the E0 write containment.
        eligible_observations: Plan-bound observation id to source id. Derived from the catalog
            when omitted, which is what a read-only reconstruction needs.
        capacity_guard: The in-process continuous capacity check, or ``None`` for a run with no
            external capacity envelope. See
            :class:`~disclosure_drift.m3.external_working_root.F2CapacityGuard`.

    Returns:
        The §9.5 totality, already checked against its own invariants.

    Raises:
        OfflineParseError: a §9.5 totality invariant was broken, or a persisted relation row
            disagrees with the projection this evidence produces.
        ExternalWorkingRootError: ``capacity_guard`` reached its floor or could not measure. The
            transaction is rolled back on the way out and nothing partial is committed.
    """
    if capacity_guard is not None:
        # D138-R9: the reading taken immediately before F2 starts. Refusing here costs nothing,
        # because the transaction has not opened yet.
        capacity_guard()
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
        for group in _stream_membership_groups(connection, eligible, compact=compact_evidence):
            if capacity_guard is not None:
                capacity_guard()
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
                clear=_blocking_fields_clear(
                    active, group.accession_plain, compact=compact_evidence
                ),
            )
            unbindable_members += projection.unbindable
            provenance_failures += projection.provenance_failures

            if projection.is_multi:
                # The scalar is the column the compact contract reconstructs this accession's
                # submissions-side membership observation *from*, so clearing it destroys that
                # evidence. Back-fill it first, for the same reason D112 §2.2 back-fills an
                # incumbent before writing a rival: otherwise the completeness pass below --
                # which re-derives the verdict rather than remembering it -- reads a group with
                # no submissions side, finds it unestablished, and disagrees with the pass that
                # counted it. Measured on the real first source with one real `company.idx`
                # quarter, that is 8 established multi-registrant accessions the §9.5 totality
                # invariant then refused. A no-op under the full contract and wherever the row
                # is already stored.
                _preserve_reconstructed_membership(active, group.accession_plain, compact_evidence)
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
        for group in _stream_membership_groups(connection, eligible, compact=compact_evidence):
            if capacity_guard is not None:
                capacity_guard()
            if not _accession_is_known(active, group.accession_plain) or not group.union:
                continue
            projection = _project_membership_group(
                group,
                known_registrants=known_registrants,
                clear=_blocking_fields_clear(
                    active, group.accession_plain, compact=compact_evidence
                ),
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

        # D140-R14: the totality tail is a sequence of aggregate counts over tens of millions
        # of rows, each a full scan. Nothing can be sampled *inside* one SQL statement, so the
        # tail is bracketed instead: a reading immediately before it, and one immediately
        # after, so the longest remaining unsampled stretch in F2 is one aggregate rather than
        # the whole finalization.
        if capacity_guard is not None:
            capacity_guard()
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
        if capacity_guard is not None:
            capacity_guard()
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
    #: One entry per parsed ``company.idx`` quarter, carrying its D113 §9 corroboration
    #: counts and replay digest. Reported rather than persisted here: where the compact
    #: contract is in force the caller writes it to the run-local sidecar, which is the only
    #: place D113 §11 authorizes evidence of this shape to live.
    full_index_corroborations: tuple[tuple[SourceObservation, FullIndexCorroboration], ...] = ()
    #: The D113 §8 resolution-completeness evidence for this phase's one resolution pass.
    resolution_evidence: ResolutionEvidence | None = None


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
    corroborations: list[tuple[SourceObservation, FullIndexCorroboration]] = []
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
        corroboration = _materialize_full_index_registrants(
            connection,
            observation=observation,
            parser_run_id=run_id,
            recorded=recorded,
            compact=bool(catalog.compact_evidence),
        )
        index_observations += corroboration.written
        index_unbound.update(corroboration.unbound)
        corroborations.append((observation, corroboration))
    resolutions = catalog.count_persisted_accession_resolutions() if parsed_any else 0
    return SourceLayerPhase(
        outcomes=tuple(outcomes),
        accession_resolutions=resolutions,
        full_index_registrant_observations=index_observations,
        full_index_unbound_accessions=tuple(sorted(index_unbound)),
        full_index_corroborations=tuple(corroborations),
        resolution_evidence=catalog.resolution_evidence,
    )


# --------------------------------------------------------------------------
# The one-source entry point (accepted Decision 116 §5)
# --------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class SelectedPlannedSource:
    """Exactly one planned source, named by its own plan key, and where it sits in the plan.

    The *only* selector is ``census_plan_sources.source_instance_id``. There is no path
    argument, no source-directory option, and no ``source_id`` shorthand: a ``source_id``
    names seventy full-index quarters at once, and a path would be exactly the operator
    discovery **R13** forbids. An identifier the accepted plan does not carry, or carries
    more than once, is refused rather than disambiguated.
    """

    source: PlannedSource
    #: 1-based position in :func:`load_planned_sources` order, which is the plan's own key.
    plan_position: int
    #: How many rows the accepted plan holds, so a position can be read as "n of m".
    plan_source_count: int


def planned_source_observation(
    connection: sqlite3.Connection, selected: SelectedPlannedSource
) -> SourceObservation | None:
    """The stored observation one selected planned source is bound to, or ``None``.

    The same lookup :func:`materialize_one_planned_source` performs, exposed so that a caller
    can authenticate the artifact **before** a world exists (Decision 140, D140-R20) without
    reaching for a private helper or building a second observation index.
    """
    observation_id = selected.source.observation_id
    if observation_id is None:
        return None
    return _observations_by_id(connection).get(observation_id)


def select_planned_source(
    connection: sqlite3.Connection, source_instance_id: str
) -> SelectedPlannedSource:
    """Return the single planned source ``source_instance_id`` names, or refuse.

    Reads the accepted plan through :func:`load_planned_sources`, so the enumeration, its
    order, and every field are the ones the whole-plan driver uses. Nothing is ranked,
    defaulted, or matched by prefix.

    Raises:
        OfflineParseError: the identifier names no planned source, or names more than one.
    """
    planned = load_planned_sources(connection)
    matches = [
        (position, source)
        for position, source in enumerate(planned, start=1)
        if source.source_instance_id == source_instance_id
    ]
    if not matches:
        message = (
            f"no planned source carries source_instance_id {source_instance_id!r}; the "
            f"accepted plan holds {len(planned)} rows and a source outside it is refused "
            "rather than parsed"
        )
        raise OfflineParseError(message)
    if len(matches) > 1:
        message = (
            f"source_instance_id {source_instance_id!r} names {len(matches)} planned rows; "
            "exactly one source is run per invocation and an ambiguous identifier is "
            "refused rather than disambiguated"
        )
        raise OfflineParseError(message)
    position, source = matches[0]
    return SelectedPlannedSource(
        source=source, plan_position=position, plan_source_count=len(planned)
    )


@dataclass(frozen=True, slots=True)
class SingleSourceOutcome:
    """What one planned source's materialization produced, and nothing about any other.

    The compact-evidence fields are populated only when a sidecar was supplied and the
    source was parsed; under the full-observation contract they stay at their empty
    defaults, because D112 §§4.A and 4.E evidence is a property of the compact contract
    rather than of every parse.
    """

    outcome: PlannedSourceOutcome
    observation: SourceObservation | None = None
    #: One entry when the source is a ``company.idx`` quarter, ``None`` otherwise.
    corroboration: FullIndexCorroboration | None = None
    completeness_digest: str = ""
    members: int = 0
    records: int = 0
    omitted_field_observations: int = 0
    materialized_field_observations: int = 0


@dataclass(frozen=True, slots=True)
class DiagnosticPrefixOutcome:
    """What a bounded diagnostic member prefix traversed. **Never a source disposition.**

    Accepted Decision 119 §6. Read the field list for what it does *not* carry: there is no
    ``disposition``, no ``parser_state_after``, no ``completeness_digest``, and no member
    manifest identity, because a prefix reached none of them. Those are the properties of a
    finished source, and a type that could express them would be a type a prefix could be
    mistaken for.

    :data:`DIAGNOSTIC_PREFIX_CLASSIFICATION` is the only classification this type can carry.
    """

    source_instance_id: str
    source_id: str
    observation: SourceObservation
    #: The bound the caller asked for. Reported beside what actually happened rather than
    #: instead of it, because an archive can run out of members before the bound is reached.
    requested_member_limit: int
    #: Members the traversal finished handing to the persistence path. Their ordinals are
    #: exactly ``0 .. members_processed - 1``, which is the manifest's own ordering.
    members_processed: int
    records: int
    omitted_field_observations: int
    materialized_field_observations: int
    classification: str = DIAGNOSTIC_PREFIX_CLASSIFICATION

    @property
    def source_finalized(self) -> bool:
        """Always ``False``, structurally: no path in this module can produce it otherwise."""
        return False


def materialize_planned_source_prefix(
    *,
    writer: CatalogWriter,
    tree: DataTree,
    catalog: CensusCatalog,
    selected: SelectedPlannedSource,
    max_members: int,
    sidecar: CompactEvidenceSidecar | None = None,
    batch_size: int = SINGLE_TRANSACTION,
    checkpoint_batches: bool = False,
) -> DiagnosticPrefixOutcome:
    """Traverse the **first ``max_members``** governed members of one planned source, and stop.

    The diagnostic-only surface accepted Decision 119 §6 authorizes, so that the accepted
    materialization path can be *measured* at real scale without committing to a whole source.
    It is the same machinery: the same plan selection, the same classification, the same
    plan-bound observation, the same ``SnapshotStore``, the same member ordering, the same pure
    parser, the same :class:`~disclosure_drift.sec.census.CensusCatalog`, the same compact
    member-recording path, and the same batched persistence. The one difference is where it
    stops.

    **What it deliberately never reaches.** Everything
    :func:`materialize_one_planned_source` does *after* the member traversal is source-level
    finalization, and none of it runs here: no ``census_plan_sources.parser_state`` transition,
    no **R23** full-index materialization, no source-level compact evidence row, no completeness
    digest, and no :class:`SingleSourceOutcome`. It also runs no catalog-wide resolution and no
    Decision 094 §6.4 association projection -- those were never this function's to run.
    The parser run the persistence path seeded stays ``failed``, which is the accepted meaning
    of "no consumer may read this run's counts as a real observation".

    **Why the cap is refused for anything but a streamed source.** A prefix is a bound on a
    member *ordering*. A single-payload source is exactly one indivisible logical member
    (accepted Decision 116 §22), so there is no prefix boundary inside it, and admitting one
    would mean finalizing a complete parser run under a mode whose entire purpose is to never
    finalize. It is refused rather than silently promoted to a whole-source parse.

    Args:
        writer: The single logical writer -- a **run-local working catalog**, never the
            accepted operational one.
        tree: The data tree the frozen source artifacts are read from.
        catalog: The census catalog to persist through, carrying the caller's evidence
            contract, exactly as the complete-source entry point requires.
        selected: The one source, from :func:`select_planned_source`.
        max_members: How many governed members to traverse. Must be positive; there is no
            "unbounded prefix", and a zero or negative bound is refused rather than read as
            "all of them".
        sidecar: The run-local compact-evidence sidecar. Members are recorded through the same
            path the complete run uses; the source-level row is not written.
        batch_size: Parts per real transaction, unchanged.
        checkpoint_batches: Whether to truncate the write-ahead log at each boundary.

    Raises:
        OfflineParseError: the bound is not positive, the source is not one a prefix is defined
            over, the source is not classified for parsing, or its parser run already exists.
    """
    if max_members <= 0:
        message = (
            f"a diagnostic member prefix needs a positive bound; got {max_members}. There is "
            "no unbounded prefix, and a non-positive bound is refused rather than read as "
            "'every member'"
        )
        raise OfflineParseError(message)
    connection = writer.connection
    source = selected.source
    observations = _observations_by_id(connection)
    bound = None if source.observation_id is None else observations.get(source.observation_id)
    disposition = classify_planned_source(source, bound)
    if disposition != "E0_REQUIRED_PARSE" or bound is None:
        message = (
            f"planned source {source.source_instance_id!r} classifies as {disposition!r} and "
            "is not parsed; a diagnostic prefix measures a real parse and refuses rather than "
            "reporting an empty one"
        )
        raise OfflineParseError(message)
    if bound.source_id not in STREAMED_SOURCE_IDS:
        message = (
            f"source {bound.source_id!r} has one indivisible logical member, so no member "
            "prefix is defined over it; a diagnostic prefix is refused rather than run as a "
            "whole-source parse under a diagnostic name"
        )
        raise OfflineParseError(message)
    store = SnapshotStore(tree)
    store.adopt(observations.values())
    evidence = (
        None
        if sidecar is None
        else CompactSourceEvidence(
            source_observation_id=bound.observation_id,
            source_id=bound.source_id,
            artifact_sha256=bound.logical_sha256 or "",
            artifact_byte_length=bound.content_size_bytes or 0,
            sidecar=sidecar,
        )
    )
    try:
        catalog.persist_streamed(
            _stream_bulk_submissions(store, bound, evidence=evidence, max_members=max_members),
            parser_id=_BULK_PARSER_ID,
            parser_version=SOURCES[bound.source_id].parser_version,
            source_observation_id=bound.observation_id,
            batch_size=batch_size,
            checkpoint_batches=checkpoint_batches,
        )
    except _DiagnosticPrefixLimit as stop:
        processed = stop.members
    else:
        # Unreachable through the stream, which always raises when a cap is set. It is
        # reachable when ``persist_streamed`` short-circuits on an existing parser run and
        # never consumes the generator at all -- a measurement of nothing, refused.
        message = (
            f"planned source {source.source_instance_id!r} already carries a parser run in "
            "this catalog, so a diagnostic prefix would traverse no member; a prefix profile "
            "runs against a fresh disposable world"
        )
        raise OfflineParseError(message)
    return DiagnosticPrefixOutcome(
        source_instance_id=source.source_instance_id,
        source_id=source.source_id,
        observation=bound,
        requested_member_limit=max_members,
        members_processed=processed,
        records=0 if evidence is None else evidence.records,
        omitted_field_observations=0 if evidence is None else evidence.omitted,
        materialized_field_observations=0 if evidence is None else evidence.materialized,
    )


def materialize_one_planned_source(
    *,
    writer: CatalogWriter,
    tree: DataTree,
    catalog: CensusCatalog,
    selected: SelectedPlannedSource,
    sidecar: CompactEvidenceSidecar | None = None,
    recorded: str | None = None,
    batch_size: int = SINGLE_TRANSACTION,
    checkpoint_batches: bool = False,
    capacity_guard: Callable[[], None] | None = None,
) -> SingleSourceOutcome:
    """Materialize **exactly one** planned source, and stop.

    The one-source twin of :func:`materialize_source_layer`, for a bounded canary that must
    be able to prove it stopped rather than merely be expected to. Every step is the same
    accepted call the whole-plan driver makes -- the same classification, the same plan-bound
    observation, the same pure parsers, the same ``CensusCatalog``, the same
    ``parser_state`` transition, and the same **R23** full-index materialization -- so this
    is a second *entry point*, never a second parser.

    What it deliberately does **not** do is anything the plan's other rows imply. It never
    enumerates a second source, never continues after this one, and never runs the
    catalog-wide resolution or the Decision 094 §6.4 association projection: those are
    phases of a whole run, and a caller that wants them runs them itself, in that order,
    inside the same containment.

    Args:
        writer: The single logical writer for the catalog being written -- for a canary,
            a **run-local working catalog**, never the accepted operational one.
        tree: The data tree the frozen source artifacts are read from.
        catalog: The census catalog to persist through, carrying the evidence contract the
            caller chose. Passed in rather than built here so the compact contract is bound
            explicitly by the caller and can never be defaulted on by this function.
        selected: The one source, from :func:`select_planned_source`.
        sidecar: The run-local compact-evidence sidecar, when the caller runs under the
            compact contract. ``None`` writes no D112 §8 evidence at all.
        recorded: The timestamp the **R23** materialization records. Defaults to now.
        batch_size: Parts per real transaction for the streamed path (accepted D111).
        checkpoint_batches: Whether to truncate the write-ahead log at each boundary.

    Raises:
        OfflineParseError: any fail-closed condition, always before a durable write.
    """
    connection = writer.connection
    source = selected.source
    observations = _observations_by_id(connection)
    bound = None if source.observation_id is None else observations.get(source.observation_id)
    disposition = classify_planned_source(source, bound)
    if disposition != "E0_REQUIRED_PARSE":
        return SingleSourceOutcome(
            outcome=PlannedSourceOutcome(
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
            ),
            observation=bound,
        )
    if bound is None:  # pragma: no cover - classify_planned_source already refused
        message = (
            f"planned source {source.source_instance_id!r} lost its plan-bound observation "
            "between classification and parse"
        )
        raise OfflineParseError(message)

    store = SnapshotStore(tree)
    store.adopt(observations.values())
    evidence = (
        None
        if sidecar is None
        else CompactSourceEvidence(
            source_observation_id=bound.observation_id,
            source_id=bound.source_id,
            artifact_sha256=bound.logical_sha256 or "",
            artifact_byte_length=bound.content_size_bytes or 0,
            sidecar=sidecar,
        )
    )
    if bound.source_id in STREAMED_SOURCE_IDS:
        result = catalog.persist_streamed(
            _stream_bulk_submissions(store, bound, evidence=evidence),
            parser_id=_BULK_PARSER_ID,
            parser_version=SOURCES[bound.source_id].parser_version,
            source_observation_id=bound.observation_id,
            batch_size=batch_size,
            checkpoint_batches=checkpoint_batches,
            capacity_guard=capacity_guard,
        )
        after = _STREAMED_PARSER_STATE[result.run_outcome]
    else:
        outcome, references = _parse_source(connection, store, bound)
        if evidence is not None:
            # A single-payload artifact is its own single member, named by the frozen
            # store's own relative path -- a property of the artifact, not of this run.
            # ``classify_planned_source`` already required ``has_payload``, which is
            # exactly this field being present; it is re-asserted rather than defaulted,
            # because a blank member name would name nothing in the manifest.
            member_name = bound.relative_storage_path
            if member_name is None:  # pragma: no cover - has_payload already required it
                message = (
                    f"planned source {source.source_instance_id!r} was classified parseable "
                    "but its bound observation records no stored payload path"
                )
                raise OfflineParseError(message)
            # The payload is loaded again through the same integrity-verifying reader
            # rather than held across the parse: retaining a second copy of bytes the
            # parse has already dropped is exactly the residency Decision 110 §8 removed.
            evidence.absorb(member_name, _payload_bytes(store, bound), outcome)
        result = catalog.persist(
            outcome, historical_references=references, source_observation_id=bound.observation_id
        )
        after = _parser_state_for(outcome)
    with transaction(connection) as active:
        active.execute(
            "UPDATE census_plan_sources SET parser_state = ? "
            "WHERE census_run_id = ? AND source_instance_id = ?",
            (after, source.census_run_id, source.source_instance_id),
        )
    corroboration = None
    if source.source_id == "sec_full_index_company":
        corroboration = _materialize_full_index_registrants(
            connection,
            observation=bound,
            parser_run_id=result.parser_run_id,
            recorded=utc_now() if recorded is None else recorded,
            compact=bool(catalog.compact_evidence),
        )
    completeness = "" if evidence is None else evidence.finish()
    return SingleSourceOutcome(
        outcome=PlannedSourceOutcome(
            source_instance_id=source.source_instance_id,
            source_id=source.source_id,
            disposition=disposition,
            parser_run_id=result.parser_run_id,
            parsed_records=result.parsed,
            quarantined_records=result.quarantined,
            parser_state_before=source.parser_state,
            parser_state_after=after,
            already_present=result.already_present,
        ),
        observation=bound,
        corroboration=corroboration,
        completeness_digest=completeness,
        members=0 if evidence is None else evidence.members,
        records=0 if evidence is None else evidence.records,
        omitted_field_observations=0 if evidence is None else evidence.omitted,
        materialized_field_observations=0 if evidence is None else evidence.materialized,
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
