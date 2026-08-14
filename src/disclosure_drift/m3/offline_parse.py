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
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.paths import DataTree
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
    "PROHIBITED_IMPORT_PREFIXES",
    "VALIDATION_OR_PROVENANCE_ONLY_SOURCE_IDS",
    "OfflineParseError",
    "OfflineParseReport",
    "PlannedSource",
    "PlannedSourceOutcome",
    "SourceDisposition",
    "classify_planned_source",
    "load_planned_sources",
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

#: The complete fifteen-table durable write footprint **R17** fixes: the nine census
#: parse-layer tables plus the six companion tables the same reusable persistence path
#: unavoidably and legitimately writes. Not a wish list — it is the mechanically
#: verified footprint of ``CensusCatalog``, and adding to it needs a new owner ruling.
E0_PERMITTED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "census_parser_runs",
        "census_parsed_records",
        "census_structural_observations",
        "census_accessions",
        "census_accession_observations",
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
#: ``sec_full_index_company`` is here by **R22** (Decision 072 §4), correcting the
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
#: (Decision 071 §13; **R25**):
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
class OfflineParseReport:
    """The E0 completeness proof: one disposition per planned source, and the counts."""

    outcomes: tuple[PlannedSourceOutcome, ...]
    accession_resolutions: int
    #: **R23** -- accession observations materialized from stored ``company.idx`` rows.
    full_index_registrant_observations: int = 0
    #: Accessions the index listed that the authoritative layer does not carry. Reported
    #: as a diagnostic and never created (**R23** §5.1).
    full_index_unbound_accessions: tuple[str, ...] = ()
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


def _parse_bulk_submissions(
    store: SnapshotStore, observation: SourceObservation
) -> tuple[ParseOutcome, tuple[HistoricalFileReference, ...]]:
    """Traverse the accepted bulk archive and parse each member, offline.

    Identical member handling to the accepted orchestrator path, minus retrieval.
    """
    store.verify_payload(observation)
    path = store.payload_path(observation)
    try:
        members = tuple(
            iter_members(
                path,
                name_suffix=".json",
                archive_relative_path=observation.relative_storage_path,
                archive_sha256=observation.logical_sha256,
            )
        )
    except ArchiveDefenceError as exc:
        message = f"accepted bulk archive refused by the archive defences: {exc}"
        raise OfflineParseError(message) from exc
    version = SOURCES["sec_bulk_submissions"].parser_version
    outcomes: list[ParseOutcome] = []
    references: list[HistoricalFileReference] = []
    for member in members:
        location = RecordLocation(
            observation.observation_id,
            observation.source_id,
            member_name=member.name,
        )
        decoded = _json_document(member.payload, f"bulk member {member.name!r}")
        outcome, member_references = parse_submissions_document(decoded, location)
        outcomes.append(outcome)
        references.extend(member_references)
    return merge_outcomes("submissions-json", version, outcomes), tuple(references)


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
    with write_containment(connection):
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
            outcome, references = _parse_source(connection, store, observation)
            result = catalog.persist(
                outcome,
                historical_references=references,
                source_observation_id=observation.observation_id,
            )
            parsed_any = True
            after = _parser_state_for(outcome)
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
        resolutions = len(catalog.resolve_persisted_accessions()) if parsed_any else 0

    report = OfflineParseReport(
        outcomes=tuple(outcomes),
        accession_resolutions=resolutions,
        full_index_registrant_observations=index_observations,
        full_index_unbound_accessions=tuple(sorted(index_unbound)),
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
