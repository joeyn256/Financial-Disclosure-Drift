"""The candidate-snapshot builder (M3.3 contract §6 item 1, §10; **R5**, **R16**).

Decision 019 §9.1 recorded that this component does not exist. It exists now, under the
identity rules **OR-1** fixed (§10.1) and the source→candidate mapping **OR-2** fixed
(§8.1), and it is the only writer of the ``pilot_candidate_*`` family.

**Atomicity is the whole design (R5).** One explicit authoritative transaction inserts
the ``building`` snapshot, inserts every child row, computes and stores the governed
digests and counts, independently recomputes every identity from the rows it just
persisted, runs the freeze validations, and transitions ``building -> frozen`` as its
last statement. Any failure rolls the whole transaction back, so **no partial
authoritative snapshot can survive**. A ``building`` row found at entry blocks and
returns to the owner: it is never resumed, completed, repaired, invalidated, or
superseded. A duplicate ``snapshot_id`` in the same catalog fails closed **before** any
mutation — never ``INSERT OR REPLACE``, never ``INSERT OR IGNORE``, and never a silent
recognize-and-return.

**The builder never repairs** (Decision 019 §4 principle 9). It does not normalize a
non-conforming input into a conforming one, does not synthesize an identity or a
registrant row, and does not backfill. A required value accepted evidence cannot
establish **refuses the snapshot** rather than being imputed, filled, or best-efforted
(§8.1 correction 8).

Running this against the accepted real private catalog is **M3.3-E1**, a separate owner
gate. Nothing here supplies it.
"""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Final

from disclosure_drift.cohorts import FROZEN_COHORTS
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3 import candidate_classification as classify
from disclosure_drift.m3 import candidate_controls as controls
from disclosure_drift.m3 import candidate_events as events
from disclosure_drift.m3.candidate_identity import (
    ACCESSION_EVIDENCE_COLUMNS,
    ACCESSION_REASONS_COLUMNS,
    ACCESSION_TABLE_COLUMNS,
    ENTITY_EVIDENCE_COLUMNS,
    ENTITY_REASONS_COLUMNS,
    ENTITY_TABLE_COLUMNS,
    REGISTRANT_TABLE_COLUMNS,
    CandidateEvidenceRow,
    SourceObservation,
    candidate_accession_evidence_sha256,
    candidate_accession_reasons_sha256,
    candidate_accession_table_sha256,
    candidate_entity_evidence_sha256,
    candidate_entity_reasons_sha256,
    candidate_entity_table_sha256,
    candidate_registrant_table_sha256,
    candidate_snapshot_sha256,
    coverage_window_sha256,
    input_observation_set_sha256,
    resolution_contributors,
    resolution_sha256,
    snapshot_identity_sha256,
)
from disclosure_drift.pilot_policy import (
    PILOT_CANDIDATE_POLICY_VERSION,
    PILOT_COVERAGE_POLICY_VERSION,
    PILOT_EVIDENCE_POLICY_VERSION,
    SIC_FAMILY_MAPPING_VERSION,
)
from disclosure_drift.sec.accession_resolution import AUTHORITY_LEVEL, authority_for_source
from disclosure_drift.sec.accession_selector import (
    accession_selection_rank,
    canonical_anchor_cik_padded,
)
from disclosure_drift.sec.entity_selector import selection_rank
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.temporal import UNRESOLVED_COHORT, cohort_label_for_value
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = [
    "CandidateDerivation",
    "CandidateSnapshotError",
    "CandidateSnapshotInputs",
    "FrozenCandidateSnapshot",
    "build_and_freeze_candidate_snapshot",
    "derive_candidate_snapshot",
    "persist_and_freeze_derivation",
]


class CandidateSnapshotError(DisclosureDriftError):
    """A fail-closed candidate-construction condition. Never worked around."""


#: Migration ``0009`` forces this literal, and Decision 013 §1 fixes it as methodology.
_INCLUDE_OPEN_QUARTER: Final = 0

#: Decision 014 §7 / Decision 010 §4.1: every M2.3 official filing date is precedence 2,
#: because accession-header evidence is precedence 1 and is a filing-body operation.
_FILING_DATE_PRECEDENCE: Final = 2

_ORIGINAL_ANNUAL_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-KT"})
_TRANSITION_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A"})

_SIZE_SOURCE_FIELD: Final = "category"
_SIC_SOURCE_FIELD: Final = "sic"
_ENTITY_TYPE_SOURCE_FIELD: Final = "entityType"
_FISCAL_YEAR_END_SOURCE_FIELD: Final = "fiscalYearEnd"
_COMPANY_NAME_SOURCE_FIELD: Final = "name"

#: Decision 019 §8.1.1's permitted identity source fields; M3.3 writes only the first.
_FORMER_NAME_SOURCE_FIELD: Final = "former_name_relationship"
_PRIOR_CURRENT_RELATIONSHIP: Final = "prior_current"

#: Decision 019 §6.2: a submitter that is not a registrant never establishes the set.
_CONTRIBUTING_REGISTRANT_ROLES: Final[frozenset[str]] = frozenset({"anchor", "associated"})

_FILING_DATE_FIELDS: Final[tuple[str, ...]] = ("filingDate", "date_filed")
_XBRL_FIELDS: Final[tuple[str, ...]] = ("isXBRL", "isInlineXBRL")
_FORM_FIELDS: Final[tuple[str, ...]] = ("form", "form_type")

#: ``temporal.cohort_label_for_value``'s label for a valid 2009 date: support-only,
#: never analysis membership (Decision 018 §15; Decision 019 §7).
PRE_STUDY_SUPPORT_COHORT: Final = "support_2009"


@dataclass(frozen=True, slots=True)
class CandidateSnapshotInputs:
    """The caller-supplied run inputs, never inferred from Git or the environment.

    Decision 013 §1 fixes the coverage window as methodology; the caller states it
    explicitly so a snapshot's identity records what it was actually built over.
    """

    census_run_id: str
    coverage_start: str
    coverage_end: str
    as_of_date: str


@dataclass(frozen=True, slots=True)
class FrozenCandidateSnapshot:
    """What one successful construct-and-freeze produced, for the caller to verify."""

    snapshot_id: str
    entity_count: int
    accession_count: int
    coverage_window_sha256: str
    input_observation_set_sha256: str
    candidate_snapshot_sha256: str
    family_digests: Mapping[str, str]
    cited_observation_ids: tuple[str, ...]
    #: Census accessions the candidate form universe excluded, by form. A diagnostic
    #: reported to the caller; it enters no digest and no persisted row.
    excluded_form_counts: Mapping[str, int] = field(default_factory=dict)
    #: Census accessions dropped for sitting outside the coverage window.
    excluded_out_of_coverage: int = 0


@dataclass(slots=True)
class _EvidenceDraft:
    """One candidate evidence row before it is persisted."""

    owner: str
    dimension: str
    role: str
    source_observation_id: str
    parsed_record_id: str | None
    source_field: str
    canonical_observed_value: str | None
    precedence: int

    def content(self) -> CandidateEvidenceRow:
        """The identity-bearing projection of this row."""
        return CandidateEvidenceRow(
            classification_dimension=self.dimension,
            evidence_role=self.role,
            source_observation_id=self.source_observation_id,
            parsed_record_id=self.parsed_record_id,
            source_field=self.source_field,
            canonical_observed_value=self.canonical_observed_value,
            policy_version=PILOT_EVIDENCE_POLICY_VERSION,
            precedence=self.precedence,
        )


@dataclass(slots=True)
class _EntityDraft:
    """One derived ``pilot_candidate_entities`` row and its children."""

    columns: dict[str, object]
    evidence: list[_EvidenceDraft] = field(default_factory=list)
    reasons: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class _AccessionDraft:
    """One derived ``pilot_candidate_accessions`` row and its children."""

    columns: dict[str, object]
    registrants: list[dict[str, object]] = field(default_factory=list)
    evidence: list[_EvidenceDraft] = field(default_factory=list)
    reasons: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class CandidateDerivation:
    """The complete in-memory derivation, produced before any write (§A.2.1)."""

    entities: list[_EntityDraft]
    accessions: list[_AccessionDraft]
    observations: list[SourceObservation]
    cited_observation_ids: tuple[str, ...]
    #: Census accessions the candidate form universe excludes, counted by form so the
    #: reduction is reported rather than silent (CLAUDE.md rule 11).
    excluded_form_counts: Mapping[str, int] = field(default_factory=dict)
    #: Census accessions dropped because their resolved filing date sits outside the
    #: coverage window, reported for the same reason.
    excluded_out_of_coverage: int = 0


def _precedence_for(source_id: str) -> int:
    """Decision 012 §4's authority level, reused rather than re-ranked.

    An unclassified source has no default level: the accepted helper raises, and the
    snapshot is refused rather than admitting evidence of unknown authority.
    """
    try:
        return AUTHORITY_LEVEL[authority_for_source(source_id)]
    except KeyError as exc:
        message = f"candidate evidence carries an unclassified source authority: {exc}"
        raise CandidateSnapshotError(message) from exc


def _as_int(value: object) -> int:
    """Read one derived column as an integer, refusing anything else."""
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"expected an integer candidate column value, got {value!r}"
        raise CandidateSnapshotError(message)
    return value


def _as_str(value: object) -> str:
    """Read one derived column as text, refusing anything else."""
    if not isinstance(value, str):
        message = f"expected a text candidate column value, got {value!r}"
        raise CandidateSnapshotError(message)
    return value


def _text(value: object) -> str | None:
    """Canonical text, with blank collapsed to absent."""
    if value is None:
        return None
    rendered = str(value).strip()
    return rendered or None


def _json_scalar(raw: object) -> str | None:
    """Decode one ``census_accession_observations.raw_value_json`` scalar."""
    if raw is None:
        return None
    try:
        decoded = json.loads(str(raw))
    except (TypeError, ValueError):
        return None
    if decoded is None or isinstance(decoded, (list, dict)):
        return None
    if isinstance(decoded, bool):
        return "1" if decoded else "0"
    return str(decoded).strip() or None


# --------------------------------------------------------------------------
# Reading the census layer. Read order is the accepted OR-2 order (proposal §D),
# fixed so two builds read identically.
# --------------------------------------------------------------------------


def _read_registrant_observations(
    connection: sqlite3.Connection,
) -> Mapping[int, list[sqlite3.Row]]:
    rows = connection.execute(
        "SELECT o.cik_numeric, o.observation_kind, o.value_text, o.source_observation_id, "
        "o.parsed_record_id, o.source_field, s.source_id "
        "FROM census_registrant_observations AS o "
        "JOIN census_source_observations AS s ON s.observation_id = o.source_observation_id "
        "ORDER BY o.cik_numeric, o.observation_kind, o.value_text, o.registrant_observation_id"
    ).fetchall()
    grouped: dict[int, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[int(row["cik_numeric"])].append(row)
    return grouped


def _read_accession_observations(
    connection: sqlite3.Connection,
) -> Mapping[str, list[sqlite3.Row]]:
    rows = connection.execute(
        "SELECT o.accession_plain, o.field_name, o.raw_value_json, o.source_observation_id, "
        "o.parsed_record_id, s.source_id "
        "FROM census_accession_observations AS o "
        "JOIN census_source_observations AS s ON s.observation_id = o.source_observation_id "
        "ORDER BY o.accession_plain, o.field_name, o.accession_observation_id"
    ).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        grouped[str(row["accession_plain"])].append(row)
    return grouped


def _read_full_index_registrants(
    connection: sqlite3.Connection,
) -> Mapping[str, tuple[int, ...]]:
    """**R23** §5.2 -- the associated registrant set, from accepted ``company.idx`` rows.

    ``company.idx`` emits one row per registrant per accession, so grouping its accepted
    ``cik_padded`` observations by canonical accession is what establishes co-registrants
    (Decision 072 §4). The submissions documents alone cannot: ``census_accessions``
    carries one registrant CIK and one submitter CIK and no more.

    Identity is the canonical CIK and nothing else -- never a company name, never a row
    count. A malformed stored CIK fails the snapshot closed rather than contributing a
    guessed registrant.
    """
    rows = connection.execute(
        "SELECT o.accession_plain, o.raw_value_json FROM census_accession_observations AS o "
        "JOIN census_source_observations AS s ON s.observation_id = o.source_observation_id "
        "WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' "
        "ORDER BY o.accession_plain, o.accession_observation_id"
    ).fetchall()
    grouped: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        value = _json_scalar(row["raw_value_json"])
        if value is None:
            continue
        try:
            grouped[str(row["accession_plain"])].add(normalize_cik(value)[0])
        except IdentifierError as exc:
            message = (
                f"accepted full-index registrant evidence for accession "
                f"{row['accession_plain']!r} carries a non-canonical CIK: {exc}"
            )
            raise CandidateSnapshotError(message) from exc
    return {accession: tuple(sorted(ciks)) for accession, ciks in grouped.items()}


def _read_cohort_resolutions(connection: sqlite3.Connection) -> Mapping[str, sqlite3.Row]:
    rows = connection.execute(
        "SELECT accession_plain, official_filing_temporal_cohort, accepted_temporal_cohort, "
        "cohort_boundary_crossed, reason_codes_json FROM census_accession_cohort_resolutions "
        "ORDER BY accession_plain, resolved_at_utc"
    ).fetchall()
    return {str(row["accession_plain"]): row for row in rows}


def _read_field_resolutions(
    connection: sqlite3.Connection,
) -> Mapping[tuple[str, str], sqlite3.Row]:
    rows = connection.execute(
        "SELECT accession_plain, field_name, status, resolved_value "
        "FROM census_accession_field_resolutions ORDER BY accession_plain, field_name, "
        "resolved_at_utc"
    ).fetchall()
    return {(str(row["accession_plain"]), str(row["field_name"])): row for row in rows}


def _read_lineage_edge_kinds(connection: sqlite3.Connection) -> Mapping[str, set[str]]:
    """The accepted lineage ``evidence_kind`` values touching each padded CIK.

    The **raw** kinds are returned, never a pre-translated flag name: **R19** §4.5 and
    §4.6 are the only rules that turn a lineage edge into an event flag, and
    :func:`~disclosure_drift.m3.candidate_events.detect_event_flags` applies them
    against :data:`~disclosure_drift.m3.candidate_events.LINEAGE_SUCCESSION_EVIDENCE_KINDS`
    and :data:`~disclosure_drift.m3.candidate_events.REVERSE_MERGER_EVIDENCE_KINDS`. A
    second translation here would both hide the succession edge from that rule and
    create a name-transition path R19 §4.9 does not authorize -- §4.9 is name-only, from
    winning provisional identity evidence, and never from a lineage edge.

    ``status`` is not consulted: migration ``0003`` constrains it to the single value
    ``candidate_only``, so it carries no acceptance signal and filtering on it would be
    a condition the schema cannot express.
    """
    rows = connection.execute(
        "SELECT from_cik_padded, to_cik_padded, evidence_kind "
        "FROM census_candidate_lineage_edges ORDER BY candidate_edge_id"
    ).fetchall()
    kinds: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        kind = str(row["evidence_kind"])
        for column in ("from_cik_padded", "to_cik_padded"):
            kinds[str(row[column])].add(kind)
    return kinds


def _read_observations(connection: sqlite3.Connection) -> Mapping[str, SourceObservation]:
    """Every accepted observation, at exactly Decision 021 §8.1's hashed content.

    ``schema_fingerprint_sha256`` is derived from the observation's own structural rows
    through the accepted seven-step rule (**R14**); an observation whose parser
    legitimately produced no structural rows contributes the accepted empty-row-set
    digest, and a source that never parsed contributes nothing here because it is
    never cited.
    """
    structural: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for row in connection.execute(
        "SELECT source_observation_id, parser_run_id, region, state, observed_type, "
        "member_name, record_path FROM census_structural_observations "
        "ORDER BY structural_observation_id"
    ).fetchall():
        structural[str(row["source_observation_id"])].append(
            {
                "parser_run_id": row["parser_run_id"],
                "region": row["region"],
                "state": row["state"],
                "observed_type": row["observed_type"],
                "member_name": row["member_name"],
                "record_path": row["record_path"],
            }
        )
    observations: dict[str, SourceObservation] = {}
    for row in connection.execute(
        "SELECT observation_id, source_id, request_identity, logical_sha256, parser_version, "
        "outcome FROM census_source_observations ORDER BY observation_id"
    ).fetchall():
        observation_id = str(row["observation_id"])
        observations[observation_id] = SourceObservation(
            source_id=str(row["source_id"]),
            request_identity=str(row["request_identity"]),
            logical_sha256=str(row["logical_sha256"] or ""),
            parser_version=str(row["parser_version"] or ""),
            outcome=str(row["outcome"]),
            structural_rows=tuple(structural.get(observation_id, ())),
        )
    return observations


# --------------------------------------------------------------------------
# Entity derivation (accepted OR-2 mapping §D.2)
# --------------------------------------------------------------------------


def _entity_evidence(
    cik_padded: str,
    observations: Sequence[sqlite3.Row],
    kinds: Mapping[str, str],
    dimension: str,
) -> list[_EvidenceDraft]:
    """Evidence rows for one entity dimension, from the observation kinds it reads.

    ``kinds`` maps ``observation_kind`` to the source-native ``source_field`` the
    census parser recorded, so the evidence row names the field the value came from
    rather than a candidate-layer alias.
    """
    drafts: list[_EvidenceDraft] = []
    for row in observations:
        kind = str(row["observation_kind"])
        if kind not in kinds:
            continue
        drafts.append(
            _EvidenceDraft(
                owner=cik_padded,
                dimension=dimension,
                role="winning",
                source_observation_id=str(row["source_observation_id"]),
                parsed_record_id=(
                    None if row["parsed_record_id"] is None else str(row["parsed_record_id"])
                ),
                source_field=kinds[kind],
                canonical_observed_value=_text(row["value_text"]),
                precedence=_precedence_for(str(row["source_id"])),
            )
        )
    return drafts


def _values_for(observations: Sequence[sqlite3.Row], kind: str) -> list[str]:
    """Distinct canonical values recorded for one observation kind, sorted."""
    return sorted(
        {
            value
            for row in observations
            if str(row["observation_kind"]) == kind and (value := _text(row["value_text"]))
        }
    )


def _resolution_for(
    dimension: str,
    drafts: Sequence[_EvidenceDraft],
    classification: Mapping[str, object],
) -> str:
    """One ``*_resolution_sha256``, over the R16-C1 contributor set."""
    contributors = resolution_contributors(draft.content() for draft in drafts)
    return resolution_sha256(
        dimension=dimension,
        contributors=contributors,
        evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
        classification=classification,
    )


@dataclass(frozen=True, slots=True)
class _EntityAggregates:
    """Per-entity facts aggregated from the accession side, before entity derivation."""

    eligible_forms: tuple[str, ...] = ()
    original_annual_report_dates: tuple[str | None, ...] = ()
    original_annual_report_count: int = 0
    submission_forms: frozenset[str] = frozenset()
    multi_registrant_annual_filing: bool = False
    non_ordinary_amendment_lineage: bool = False
    material_conflict: bool = False


def _derive_entity(
    cik_numeric: int,
    cik_padded: str,
    observations: Sequence[sqlite3.Row],
    aggregates: _EntityAggregates,
    lineage_kinds: frozenset[str],
    sic_authority: frozenset[str],
    *,
    recorded: str,
) -> _EntityDraft:
    """Derive one candidate entity row from its accepted registrant observations.

    Event flags come from **R19**'s evidence predicates and boundary-control status from
    **R20**'s. Neither consults a company name, a ticker, or ``entityType`` text.
    """
    size_values = _values_for(observations, "filing_status")
    sic_values = _values_for(observations, "sic")
    status_values = _values_for(observations, "entity_type") + size_values
    names = _values_for(observations, "company_name")

    filing_time_name = names[0] if names else None
    if filing_time_name is None:
        message = (
            f"registrant {cik_padded} has no accepted company-name observation; "
            "filing_time_name is NOT NULL and is never synthesized"
        )
        raise CandidateSnapshotError(message)

    size_stratum, size_level = classify.classify_size_stratum(size_values)
    # Decision 007 makes the SEC SIC code list the **only** permitted source of SIC
    # codes, and Decision 067 §10.5 fails SIC-dependent classification closed when the
    # accepted corpus cannot establish that authority. An observed code the accepted
    # authority does not carry -- or any observed code at all when the authority itself
    # was never established -- therefore resolves no SIC.
    observed_sic = sic_values[0] if len(sic_values) == 1 else None
    sic_resolved = observed_sic is not None and observed_sic in sic_authority
    sic_code = observed_sic if sic_resolved else None
    industry_family, industry_level = classify.industry_family_for_sic(sic_code)
    if len(sic_values) > 1:
        industry_family, industry_level = None, "conflicting"
    elif observed_sic is not None and not sic_resolved:
        industry_family, industry_level = None, "review_required"

    identity_evidence, winning_former_name = _identity_evidence(cik_padded, observations, names)

    control = controls.classify_control_kind(
        controls.ControlEvidence(
            sic_code=sic_code,
            sic_resolved=sic_resolved,
            submission_forms=controls.original_forms(aggregates.submission_forms)
            | (aggregates.submission_forms & controls.ASSET_BACKED_FORMS),
        )
    )

    detection = events.detect_event_flags(
        events.EntityEventEvidence(
            status_values=tuple(status_values),
            lineage_evidence_kinds=lineage_kinds,
            eligible_forms=aggregates.eligible_forms,
            original_annual_report_dates=aggregates.original_annual_report_dates,
            winning_provisional_former_name=winning_former_name,
            multi_registrant_annual_filing=aggregates.multi_registrant_annual_filing,
            non_ordinary_amendment_lineage=aggregates.non_ordinary_amendment_lineage,
            material_conflict=(
                aggregates.material_conflict
                or size_level == "conflicting"
                or industry_level == "conflicting"
            ),
        )
    )
    history_class, history_level = classify.classify_history(
        detection,
        eligible_original_annual_reports=aggregates.original_annual_report_count,
        evidence_available=bool(status_values or names),
    )

    if control.status == "resolved":
        candidate_category = "control"
    elif control.status == "conflicting":
        candidate_category = "ineligible"
    elif size_stratum is not None or industry_family is not None:
        candidate_category = "operating"
    else:
        candidate_category = "ineligible"

    classification_resolved = (
        size_level == "provisional"
        and industry_level == "provisional"
        and history_level == "provisional"
    )
    universe_eligible = classify.primary_universe_eligible(
        is_operating_candidate=candidate_category == "operating",
        classification_resolved=classification_resolved,
        sic_code=sic_code,
    )
    engineering_only = sic_code in classify.ENGINEERING_ONLY_SIC_CODES if sic_code else False
    # Decision 016 §2: "quota eligibility and primary-universe eligibility are
    # independent flags; satisfying one never implies the other", and SIC 6712 "may
    # provisionally satisfy the operating-financial pilot industry quota ... but it is
    # engineering-only and primary-universe ineligible regardless". Excluding the
    # engineering-only stratum here would contradict that and, because the accepted S4
    # `_operating_eligible` requires an operating-financial candidate to be both
    # `industry_quota_eligible` **and** `engineering_only_stress`, would make the
    # operating-financial industry quota unsatisfiable by construction rather than by
    # evidence. The other engineering-only code, 6798, never reaches this branch: it is
    # in `QUOTA_INELIGIBLE_SIC_CODES` and resolves to no family at all.
    industry_quota_eligible = industry_family is not None and industry_level == "provisional"
    inactive = "inactive" in detection.observed

    size_evidence = _entity_evidence(
        cik_padded, observations, {"filing_status": _SIZE_SOURCE_FIELD}, "size"
    )
    industry_evidence = _entity_evidence(
        cik_padded, observations, {"sic": _SIC_SOURCE_FIELD}, "industry"
    )
    history_evidence = _entity_evidence(
        cik_padded,
        observations,
        {
            "fiscal_year_end": _FISCAL_YEAR_END_SOURCE_FIELD,
            "filing_status": _SIZE_SOURCE_FIELD,
            "entity_type": _ENTITY_TYPE_SOURCE_FIELD,
        },
        "history",
    )
    universe_evidence = _entity_evidence(
        cik_padded,
        observations,
        {"sic": _SIC_SOURCE_FIELD, "entity_type": _ENTITY_TYPE_SOURCE_FIELD},
        "primary_universe",
    )

    columns: dict[str, object] = {
        "cik_numeric": cik_numeric,
        "cik_padded": cik_padded,
        "entity_tie_break_sha256": selection_rank(cik_padded),
        "candidate_category": candidate_category,
        "control_kind": control.control_kind if candidate_category == "control" else None,
        "size_stratum": size_stratum,
        "size_evidence_level": size_level,
        "size_resolution_sha256": None,
        "sic_code": sic_code,
        "industry_family": industry_family,
        "industry_quota_eligible": int(industry_quota_eligible),
        "industry_evidence_level": industry_level,
        "industry_resolution_sha256": None,
        "history_class": history_class,
        "history_evidence_level": history_level,
        "history_resolution_sha256": None,
        "currently_inactive": int(inactive),
        "eligible_original_annual_report_count": aggregates.original_annual_report_count,
        "primary_universe_eligible": int(universe_eligible),
        "primary_universe_evidence_level": (
            "provisional" if universe_eligible else _weakest(size_level, industry_level)
        ),
        "primary_universe_resolution_sha256": None,
        "engineering_only_stress": int(engineering_only and not universe_eligible),
        "filing_time_name": filing_time_name,
        "recorded_at_utc": recorded,
        "detail": "",
    }

    for dimension, drafts, value_columns in (
        ("size", size_evidence, {"size_stratum": size_stratum}),
        ("industry", industry_evidence, {"industry_family": industry_family}),
        ("history", history_evidence, {"history_class": history_class}),
    ):
        if next(iter(value_columns.values())) is not None:
            columns[f"{dimension}_resolution_sha256"] = _resolution_for(
                dimension, drafts, value_columns
            )
    if universe_eligible:
        columns["primary_universe_resolution_sha256"] = _resolution_for(
            "primary_universe",
            universe_evidence,
            {"primary_universe_eligible": int(universe_eligible)},
        )

    reasons = _entity_reasons(
        history_level,
        sic_code=observed_sic,
        industry_family=industry_family,
        conflicting_sic=len(sic_values) > 1,
        conflicting_control=control.status == "conflicting",
    )
    return _EntityDraft(
        columns=columns,
        evidence=[
            *size_evidence,
            *industry_evidence,
            *history_evidence,
            *universe_evidence,
            *identity_evidence,
        ],
        reasons=reasons,
    )


def _weakest(*levels: str) -> str:
    """The weakest of several evidence levels, by Decision 014 §1's ordering."""
    order = ("provisional", "review_required", "conflicting", "unavailable")
    return max(levels, key=order.index)


def normalized_name(value: str) -> str:
    """Decision 019 §8.2.1's frozen name normalization, applied exactly.

    NFC, then trim and collapse Unicode whitespace runs to one ``U+0020``
    (``" ".join(value.split())``), preserving case and every other code point. The
    builder produces already-normalized names so that Stage S5.2's byte-for-byte
    validation passes without S5.2 ever rewriting a stored value.
    """
    return " ".join(unicodedata.normalize("NFC", value).split())


def _former_name_payload(current: str, prior: str) -> str:
    """Decision 019 §8.2's prior/current canonical JSON, serialized exactly as fixed.

    The key set is complete -- ``relationship`` included -- because §8.2 admits exactly
    two key sets and rejects any other. Serialization is §8.2's own frozen call:
    sorted keys, ``ensure_ascii=False``, compact separators. This is a stored value
    compared byte for byte, not a hash payload, which is why it uses §8.2's rendering
    rather than the document canonical-JSON serializer.
    """
    payload = {
        "current_name": current,
        "prior_name": prior,
        "relationship": _PRIOR_CURRENT_RELATIONSHIP,
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _identity_evidence(
    cik_padded: str, observations: Sequence[sqlite3.Row], names: Sequence[str]
) -> tuple[list[_EvidenceDraft], bool]:
    """Decision 019 §8 -- former-name identity evidence, name-only at M2.3.

    §8.1.1 restricts the ``identity`` dimension's ``source_field`` to exactly
    ``former_name_relationship`` and ``ticker_change``. M3.3 writes only the former:
    R19 §4.9 keeps the name/ticker transition flag name-only, and a ticker-only row
    contributes nothing to it.

    Returns the drafts and whether R19 §4.9's affirmative condition holds -- exactly one
    **winning** row whose payload is parseable and whose two names are nonempty and
    differ. Several valid former names is not a conflict; it is simply not a single
    winning record, so the flag stays unobserved rather than becoming a conflict.
    """
    if not names:
        return [], False
    current = normalized_name(names[0])
    drafts: list[_EvidenceDraft] = []
    for row in observations:
        if str(row["observation_kind"]) != "former_name":
            continue
        raw = _text(row["value_text"])
        if raw is None:
            continue
        prior = normalized_name(raw)
        drafts.append(
            _EvidenceDraft(
                owner=cik_padded,
                dimension="identity",
                role="winning",
                source_observation_id=str(row["source_observation_id"]),
                parsed_record_id=(
                    None if row["parsed_record_id"] is None else str(row["parsed_record_id"])
                ),
                source_field=_FORMER_NAME_SOURCE_FIELD,
                canonical_observed_value=_former_name_payload(current, prior),
                precedence=_precedence_for(str(row["source_id"])),
            )
        )
    if len(drafts) > 1:
        # Decision 019 §8.3: more than one former-name row cannot have a single winner,
        # so every row is supporting and the accepted branch table resolves the level.
        return [replace(draft, role="supporting") for draft in drafts], False
    if not drafts:
        return [], False
    prior = normalized_name(_text(next(iter(observations_former(observations)))) or "")
    return drafts, _former_name_content_ok(current, prior)


def observations_former(observations: Sequence[sqlite3.Row]) -> list[sqlite3.Row]:
    """The entity's accepted ``former_name`` observations, in read order."""
    return [row for row in observations if str(row["observation_kind"]) == "former_name"]


def _former_name_content_ok(current: str, prior: str) -> bool:
    """Decision 019 §8.4's content rule: both names nonempty, and they differ."""
    return bool(current) and bool(prior) and current != prior


def _entity_reasons(
    history_level: str,
    *,
    sic_code: str | None,
    industry_family: str | None,
    conflicting_sic: bool,
    conflicting_control: bool,
) -> list[tuple[str, str]]:
    """Reason rows written exactly when an accepted record requires one.

    Never free commentary, and never a second copy of a fact the candidate row already
    carries in normalized form (Decision 019 §9).
    """
    reasons: list[tuple[str, str]] = []
    if conflicting_sic:
        reasons.append(("industry", "REVIEW_CONFLICTING_SIC"))
    elif sic_code is not None and industry_family is None:
        # A SIC is on record but the frozen v0.2 mapping does not place it. That is a
        # different fact from having no SIC at all, so it is recorded rather than left
        # to be inferred from a NULL family.
        reasons.append(("industry", "REVIEW_PILOT_SIC_UNMAPPED"))
    if sic_code in classify.ENGINEERING_ONLY_SIC_CODES:
        reasons.append(("industry", "REVIEW_PILOT_SIC_ENGINEERING_ONLY"))
    if conflicting_control:
        reasons.append(("eligibility", "REVIEW_UNKNOWN_ISSUER_TYPE"))
    if history_level != "provisional":
        reasons.append(("history", "REVIEW_PILOT_HISTORY_EVIDENCE_INSUFFICIENT"))
    return reasons


# --------------------------------------------------------------------------
# Accession derivation (accepted OR-2 mapping §§D.3, D.4)
# --------------------------------------------------------------------------


def _accession_evidence(
    accession_plain: str,
    observations: Sequence[sqlite3.Row],
    fields: Sequence[str],
    dimension: str,
) -> list[_EvidenceDraft]:
    """Evidence rows for one accession dimension, from the fields it reads."""
    drafts: list[_EvidenceDraft] = []
    for row in observations:
        name = str(row["field_name"])
        if name not in fields:
            continue
        drafts.append(
            _EvidenceDraft(
                owner=accession_plain,
                dimension=dimension,
                role="winning",
                source_observation_id=str(row["source_observation_id"]),
                parsed_record_id=(
                    None if row["parsed_record_id"] is None else str(row["parsed_record_id"])
                ),
                source_field=name,
                canonical_observed_value=_json_scalar(row["raw_value_json"]),
                precedence=_precedence_for(str(row["source_id"])),
            )
        )
    return drafts


def _amendment_linkage(
    accession_plain: str,
    *,
    is_amendment: bool,
    resolution: sqlite3.Row | None,
    originals: Mapping[str, bool],
) -> tuple[str | None, str | None]:
    """Decision 019 §5 -- the frozen linkage mapping, from accepted evidence only.

    The parent comes from the accepted ``amendment_relationship`` field resolution and
    nowhere else. An unresolved relationship, or a parent absent from this snapshot, is
    ``unresolved_amendment`` (§5.6) -- never a guessed parent and never a silent link.
    ``provisional_parent_accession`` is stored in the canonical **plain** form (§5.7).
    """
    if not is_amendment:
        return None, None
    resolved = (
        None
        if resolution is None or not str(resolution["status"]).startswith("resolved")
        else _text(resolution["resolved_value"])
    )
    if resolved is None:
        return "unresolved_amendment", None
    try:
        parent = parse_accession(resolved)
    except IdentifierError:
        return "unresolved_amendment", None
    if parent.plain == accession_plain or parent.plain not in originals:
        return "unresolved_amendment", None
    state = "amends_original" if originals[parent.plain] else "amends_prior_amendment"
    return state, parent.plain


def _cohort_boundary(
    official_filing_date: str | None, acceptance_audit_date: str | None
) -> tuple[str, str, int, bool]:
    """**R33** (Decision 074 §6) — the same-build cohort-boundary derivation.

    Decision 010 already fixes every input: the official filing date determines the
    authoritative temporal cohort, ``acceptance_date_sec`` determines the audit-only
    acceptance cohort, and both are labelled by the **same** frozen
    :func:`~disclosure_drift.sec.temporal.cohort_label_for_value` windows. A crossing is
    therefore a property of *this* build's own resolved candidate facts, and needs no
    earlier snapshot, no previous E0 pass, no prior candidate resolution, and no second
    execution cycle. That is why the census resolution's own ``cohort_boundary_crossed``
    — which the accepted resolver raises only from **earlier persisted** resolutions of
    the same accession, and which a single offline pass therefore never raises — is not
    consulted here.

    Returns ``(official_label, audit_label, cohort_ambiguous, unknown)``:

    * both labels resolved and **different** ⇒ crossed;
    * both resolved and equal ⇒ not crossed;
    * either unresolved, absent, or malformed ⇒ **not silently "no crossing"**. The
      accession is marked ambiguous and ``unknown`` is set, so the caller records the
      review-required state in the existing candidate vocabulary rather than asserting a
      negative it cannot establish.

    ``cohort_label_for_value`` is the single accepted labeller: an absent or unparseable
    value is ``unresolved`` rather than an exception, so no second date parser exists here.
    """
    official_label = cohort_label_for_value(official_filing_date)
    audit_label = cohort_label_for_value(acceptance_audit_date)
    unknown = UNRESOLVED_COHORT in {official_label, audit_label}
    if unknown:
        return official_label, audit_label, 1, True
    return official_label, audit_label, int(official_label != audit_label), False


def _derive_accession(
    row: sqlite3.Row,
    observations: Sequence[sqlite3.Row],
    cohort: sqlite3.Row | None,
    filing_date_resolution: sqlite3.Row | None,
    linkage: tuple[str | None, str | None],
    associated: Sequence[int],
    *,
    recorded: str,
) -> _AccessionDraft:
    """Derive one candidate accession row, its registrants, evidence, and reasons."""
    accession_plain = str(row["accession_plain"])
    try:
        identity = parse_accession(str(row["accession_dashed"]))
    except IdentifierError as exc:
        message = f"accession {accession_plain!r} has a non-canonical stored identity: {exc}"
        raise CandidateSnapshotError(message) from exc
    if identity.plain != accession_plain:
        message = (
            f"accession plain form {accession_plain!r} disagrees with the canonical "
            f"dashed form {identity.dashed!r}; disagreement fails closed and is never "
            "reconciled (Decision 018 §5)"
        )
        raise CandidateSnapshotError(message)

    anchor_numeric = int(row["registrant_cik_numeric"])
    anchor_padded = canonical_anchor_cik_padded(anchor_numeric)
    form_type = str(row["form_type"])
    is_amendment = int(row["is_amendment"])

    resolved_date = (
        None
        if filing_date_resolution is None
        else _text(filing_date_resolution["resolved_value"])
        if str(filing_date_resolution["status"]).startswith("resolved")
        else None
    )
    acceptance_audit_date = _text(row["acceptance_date_sec"])
    official_label, audit_label, cohort_ambiguous, cohort_unknown = _cohort_boundary(
        resolved_date, acceptance_audit_date
    )
    official_cohort = official_label if official_label in FROZEN_COHORTS else None
    audit_cohort = audit_label if audit_label in FROZEN_COHORTS else None
    pre_study = official_label == PRE_STUDY_SUPPORT_COHORT

    has_xbrl = int(bool(row["xbrl_flag"]))
    has_inline = int(bool(row["inline_xbrl_flag"]))

    filing_evidence = _accession_evidence(
        accession_plain, observations, _FILING_DATE_FIELDS, "filing_date"
    )
    cohort_evidence = _accession_evidence(
        accession_plain, observations, _FILING_DATE_FIELDS, "cohort"
    )
    xbrl_evidence = _accession_evidence(accession_plain, observations, _XBRL_FIELDS, "xbrl")
    purpose_evidence = _accession_evidence(
        accession_plain, observations, _FORM_FIELDS, "amendment_purpose"
    )
    registrant_evidence = _accession_evidence(
        accession_plain, observations, ("cik", "cik_padded"), "multi_registrant"
    )

    xbrl_level = "provisional" if xbrl_evidence else "unavailable"
    filing_level = "provisional" if resolved_date is not None else "unavailable"
    if official_cohort is None:
        cohort_level = "unavailable"
    elif cohort_unknown:
        # **R33**: the cohort itself is established, but one of the two labels the
        # boundary comparison needs is not, so the accession is review-required rather
        # than silently asserted uncrossed.
        cohort_level = "review_required"
    else:
        cohort_level = "provisional"

    # Decision 014 §6: definitive purpose needs filing-body evidence, prohibited here.
    # Metadata alone establishes no category, so none is assigned and the level records
    # exactly that rather than an invented classification.
    purpose_category: str | None = None
    purpose_level = "unproven" if is_amendment else "unavailable"

    registrants = _registrant_rows(row, associated, recorded=recorded)
    contributing = [item for item in registrants if item["role"] in _CONTRIBUTING_REGISTRANT_ROLES]
    multi_registrant = int(len(contributing) > 1)

    linkage_state, parent_plain = linkage

    columns: dict[str, object] = {
        "accession_plain": accession_plain,
        "accession_number_dashed": identity.dashed,
        "accession_tie_break_sha256": accession_selection_rank(anchor_padded, identity.dashed),
        "anchor_cik_numeric": anchor_numeric,
        "form_type": form_type,
        "is_amendment": is_amendment,
        "official_filing_date": resolved_date,
        "report_date": _text(row["report_date"]),
        "acceptance_audit_date": _text(row["acceptance_date_sec"]),
        "filing_date_evidence_level": filing_level,
        "filing_date_resolution_sha256": None,
        "filing_date_precedence": _FILING_DATE_PRECEDENCE if resolved_date else None,
        "provisional_official_cohort": official_cohort,
        "acceptance_audit_cohort": audit_cohort,
        "cohort_evidence_level": cohort_level,
        "cohort_resolution_sha256": None,
        "cohort_ambiguous": cohort_ambiguous,
        "has_xbrl": has_xbrl,
        "has_inline_xbrl": has_inline,
        "xbrl_evidence_level": xbrl_level,
        "xbrl_resolution_sha256": None,
        "amendment_linkage_state": linkage_state,
        "provisional_parent_accession": parent_plain,
        "amendment_purpose_category": purpose_category,
        "amendment_purpose_evidence_level": purpose_level,
        "amendment_purpose_resolution_sha256": None,
        "amendment_purpose_quota_eligible": 0,
        "base_eligible": int(
            is_amendment == 0 and cohort_ambiguous == 0 and official_cohort is not None
        ),
        "stress_eligible": int(bool(is_amendment)),
        "support_eligible": int(pre_study),
        "control_eligible": 0,
        "multi_registrant": multi_registrant,
        "recorded_at_utc": recorded,
        "detail": "",
    }

    if resolved_date is not None:
        columns["filing_date_resolution_sha256"] = _resolution_for(
            "filing_date", filing_evidence, {"official_filing_date": resolved_date}
        )
    if official_cohort is not None:
        columns["cohort_resolution_sha256"] = _resolution_for(
            "cohort", cohort_evidence, {"provisional_official_cohort": official_cohort}
        )
    if xbrl_level == "provisional":
        columns["xbrl_resolution_sha256"] = _resolution_for(
            "xbrl", xbrl_evidence, {"has_xbrl": has_xbrl, "has_inline_xbrl": has_inline}
        )
    # ``amendment_purpose_resolution_sha256`` stays NULL, which migration ``0009``
    # requires as an iff on the category: no accepted metadata rule assigns a category,
    # so none is assigned, and the resolution digest that would tie a category to its
    # evidence has nothing to tie. The evidence rows are still written, because the
    # freeze guard requires backing for any accession carrying a linkage state.

    reasons: list[tuple[str, str]] = []
    if linkage_state == "unresolved_amendment":
        reasons.append(("amendment", "REVIEW_AMENDMENT_PARENT_UNRESOLVED"))
    if multi_registrant == 0 and len(registrants) > 1:
        # Decision 019 §6.3's single permitted divergence: more registrant rows than
        # substantive contributors. Migration 0009's freeze guard requires exactly this
        # reason to explain it, so the flag and the rows can never silently disagree.
        reasons.append(("multi_registrant", "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE"))
    if pre_study:
        reasons.append(("cohort", "PILOT_ACCESSION_PRE_STUDY_SUPPORT"))
    if cohort_unknown and official_cohort is not None:
        # **R33**: the boundary comparison could not be completed, so the condition is
        # recorded rather than resolved to "no crossing".
        reasons.append(("cohort", "REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING"))
    if purpose_level == "unproven":
        # Decision 014 §6 / IN-2: the category is assignable only from document
        # evidence M2.3 prohibits, so it is left absent and the state is recorded
        # rather than manufactured from the form suffix or the filing timing.
        reasons.append(("amendment", "REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN"))

    return _AccessionDraft(
        columns=columns,
        registrants=registrants,
        evidence=[
            *filing_evidence,
            *cohort_evidence,
            *xbrl_evidence,
            *purpose_evidence,
            *registrant_evidence,
        ],
        reasons=reasons,
    )


def _registrant_rows(
    row: sqlite3.Row, associated: Sequence[int], *, recorded: str
) -> list[dict[str, object]]:
    """Decision 019 §6 and **R23** §5.2 -- the structural registrant set, one anchor.

    Built only from approved census observations, with no inference beyond what the
    parser captured. The anchor stays the authoritative census anchor; every other
    distinct canonical CIK the accepted ``company.idx`` rows list for the same accession
    is ``associated``; a submitter that is neither is ``submitter_only`` and never
    establishes the registrant set (Decision 019 §6.2). ``company.idx`` creates no
    ``submitter_only`` membership of its own.

    Repeated index rows for one CIK collapse to one registrant, because membership is
    the distinct canonical CIK set and never a row count (**R23** §5.3).
    """
    anchor = int(row["registrant_cik_numeric"])
    rows: dict[int, dict[str, object]] = {
        anchor: {
            "registrant_cik_numeric": anchor,
            "registrant_cik_padded": canonical_anchor_cik_padded(anchor),
            "role": "anchor",
            "is_anchor": 1,
            "evidence_level": "provisional",
            "recorded_at_utc": recorded,
        }
    }
    for numeric in associated:
        if numeric == anchor:
            continue
        rows[numeric] = {
            "registrant_cik_numeric": numeric,
            "registrant_cik_padded": canonical_anchor_cik_padded(numeric),
            "role": "associated",
            "is_anchor": 0,
            "evidence_level": "provisional",
            "recorded_at_utc": recorded,
        }
    submitter = row["submitter_cik_numeric"]
    if submitter is not None and int(submitter) not in rows:
        numeric = int(submitter)
        rows[numeric] = {
            "registrant_cik_numeric": numeric,
            "registrant_cik_padded": canonical_anchor_cik_padded(numeric),
            "role": "submitter_only",
            "is_anchor": 0,
            "evidence_level": "provisional",
            "recorded_at_utc": recorded,
        }
    return [rows[key] for key in sorted(rows)]


# --------------------------------------------------------------------------
# Whole-snapshot derivation
# --------------------------------------------------------------------------


def _material_conflict_ciks(
    connection: sqlite3.Connection, anchor_by_accession: Mapping[str, int]
) -> set[int]:
    """R19 §4.12 -- entities whose accepted machinery explicitly reports a conflict.

    Only two accepted signals qualify, and neither is an inference: a **material**
    census field resolution the Decision 012 resolver left ``unresolved`` because
    equal-authority observations disagreed, and an accession observation the accepted
    persistence path flagged with ``conflict_indicator``. A missing, unavailable, or
    merely ``review_required`` field is **not** a conflict, and neither is the mere
    existence of former-name history or of more than one observation.
    """
    conflicted: set[int] = set()
    for row in connection.execute(
        "SELECT DISTINCT accession_plain FROM census_accession_field_resolutions "
        "WHERE is_material = 1 AND status = 'unresolved' "
        "UNION SELECT DISTINCT accession_plain FROM census_accession_observations "
        "WHERE conflict_indicator = 1"
    ).fetchall():
        anchor = anchor_by_accession.get(str(row["accession_plain"]))
        if anchor is not None:
            conflicted.add(anchor)
    return conflicted


def _sic_authority(connection: sqlite3.Connection) -> frozenset[str]:
    """The accepted SIC authority, from the one permitted source (Decision 007).

    ``reference_sic_codes`` is populated only by parsing the official SEC SIC code
    list. If that source is accepted as failed or unavailable the table is empty, the
    authority is not established, and every SIC-dependent classification fails closed
    (Decision 067 §10.5) -- which, if it removes a required control category or industry
    quota, makes selection infeasible rather than loosening the rule.
    """
    return frozenset(
        str(row["sic_code"])
        for row in connection.execute(
            "SELECT sic_code FROM reference_sic_codes ORDER BY sic_code"
        ).fetchall()
    )


def _candidate_form_universe(connection: sqlite3.Connection) -> frozenset[str]:
    """The forms a candidate accession row may carry, from the schema contract itself.

    Migration ``0009`` declares ``pilot_candidate_accessions.form_type REFERENCES
    reference_form_types(form_type)``, so the accepted candidate accession universe is
    exactly that reference table -- the eligible annual-report forms plus the
    control-evidence annual forms. ``census_accessions`` is deliberately wider: the
    accepted persistence path stores **every** form the submissions parser emits, and
    **R20** §§6.2 and 6.4 read that wider history for the asset-backed and
    foreign-private-issuer predicates.

    Bounding the candidate rows by the reference table is therefore reading the
    persisted contract, not narrowing the pilot universe by judgement: a form outside it
    cannot be persisted as a candidate accession at all. The excluded rows are counted
    and reported rather than dropped silently.
    """
    return frozenset(
        str(row["form_type"])
        for row in connection.execute(
            "SELECT form_type FROM reference_form_types ORDER BY form_type"
        ).fetchall()
    )


def _submission_forms(connection: sqlite3.Connection) -> Mapping[int, frozenset[str]]:
    """R20 §§6.2, 6.4 -- every exact form in each entity's stored submissions history.

    Deliberately **not** restricted to the eligible annual-report universe or to the
    coverage window: the asset-backed and foreign-private-issuer predicates read the
    whole accepted stored history, and a ``10-D`` or a ``20-F`` is never an eligible
    annual report.
    """
    forms: dict[int, set[str]] = defaultdict(set)
    for row in connection.execute(
        "SELECT registrant_cik_numeric, form_type FROM census_accessions "
        "ORDER BY registrant_cik_numeric, form_type"
    ).fetchall():
        forms[int(row["registrant_cik_numeric"])].add(str(row["form_type"]))
    return {cik: frozenset(values) for cik, values in forms.items()}


def derive_candidate_snapshot(
    connection: sqlite3.Connection, inputs: CandidateSnapshotInputs
) -> CandidateDerivation:
    """Derive the whole candidate snapshot in memory, before any write.

    Completing the derivation first is what lets ``input_observation_set_sha256`` --
    and therefore ``snapshot_id`` -- be fixed at row creation, as migration ``0009``
    requires, while still being recomputable from the persisted evidence afterwards
    (Decision 067 §9.1).

    The accession side is derived first because **R19**'s event evidence and **R20**'s
    control evidence are both aggregated from it.
    """
    recorded = utc_now()
    registrant_observations = _read_registrant_observations(connection)
    accession_observations = _read_accession_observations(connection)
    cohort_resolutions = _read_cohort_resolutions(connection)
    field_resolutions = _read_field_resolutions(connection)
    lineage = _read_lineage_edge_kinds(connection)
    full_index_registrants = _read_full_index_registrants(connection)
    observations = _read_observations(connection)
    submission_forms = _submission_forms(connection)
    sic_authority = _sic_authority(connection)
    candidate_forms = _candidate_form_universe(connection)

    every_accession_row = connection.execute(
        "SELECT accession_plain, accession_dashed, registrant_cik_numeric, "
        "submitter_cik_numeric, form_type, is_amendment, report_date, acceptance_date_sec, "
        "xbrl_flag, inline_xbrl_flag FROM census_accessions ORDER BY accession_plain"
    ).fetchall()
    excluded_forms: dict[str, int] = defaultdict(int)
    accession_rows = []
    for row in every_accession_row:
        form = str(row["form_type"])
        if form in candidate_forms:
            accession_rows.append(row)
        else:
            excluded_forms[form] += 1
    anchor_by_accession = {
        str(row["accession_plain"]): int(row["registrant_cik_numeric"]) for row in accession_rows
    }
    conflicted = _material_conflict_ciks(connection, anchor_by_accession)

    originals: dict[str, bool] = {
        str(row["accession_plain"]): not int(row["is_amendment"]) for row in accession_rows
    }
    accessions: list[_AccessionDraft] = []
    out_of_coverage = 0
    for row in accession_rows:
        plain = str(row["accession_plain"])
        draft = _derive_accession(
            row,
            accession_observations.get(plain, ()),
            cohort_resolutions.get(plain),
            field_resolutions.get((plain, "official_filing_date")),
            _amendment_linkage(
                plain,
                is_amendment=bool(int(row["is_amendment"])),
                resolution=field_resolutions.get((plain, "amendment_relationship")),
                originals=originals,
            ),
            full_index_registrants.get(plain, ()),
            recorded=recorded,
        )
        if _within_coverage(draft, inputs):
            accessions.append(draft)
        else:
            out_of_coverage += 1

    aggregates = _aggregate_by_entity(accessions, submission_forms, conflicted)

    entities: list[_EntityDraft] = []
    for registrant in connection.execute(
        "SELECT cik_numeric, cik_padded FROM census_registrants ORDER BY cik_numeric"
    ).fetchall():
        cik_numeric = int(registrant["cik_numeric"])
        cik_padded = str(registrant["cik_padded"])
        try:
            expected = normalize_cik(cik_numeric)[1]
        except IdentifierError as exc:
            message = f"registrant {cik_numeric} carries a non-canonical CIK: {exc}"
            raise CandidateSnapshotError(message) from exc
        if expected != cik_padded:
            message = (
                f"registrant {cik_numeric} stores padded CIK {cik_padded!r}, which is not "
                f"the canonical rendering {expected!r}; disagreement fails closed"
            )
            raise CandidateSnapshotError(message)
        entities.append(
            _derive_entity(
                cik_numeric,
                cik_padded,
                registrant_observations.get(cik_numeric, ()),
                aggregates.get(cik_numeric, _EntityAggregates()),
                frozenset(lineage.get(cik_padded, set())),
                sic_authority,
                recorded=recorded,
            )
        )

    boundary_controls = {
        _as_int(entry.columns["cik_numeric"])
        for entry in entities
        if entry.columns["candidate_category"] == "control"
    }
    for draft in accessions:
        if _as_int(draft.columns["anchor_cik_numeric"]) in boundary_controls:
            draft.columns["control_eligible"] = 1
            draft.columns["base_eligible"] = 0
            draft.columns["support_eligible"] = 0

    known = {_as_int(entry.columns["cik_numeric"]) for entry in entities}
    for draft in accessions:
        anchor = _as_int(draft.columns["anchor_cik_numeric"])
        if anchor not in known:
            message = (
                f"accession {draft.columns['accession_plain']!r} anchors on CIK {anchor}, "
                "which has no accepted registrant row; no entity is synthesized"
            )
            raise CandidateSnapshotError(message)

    cited = sorted(
        {draft.source_observation_id for entry in entities for draft in entry.evidence}
        | {draft.source_observation_id for entry in accessions for draft in entry.evidence}
    )
    missing = [item for item in cited if item not in observations]
    if missing:
        message = f"candidate evidence cites observation(s) absent from the catalog: {missing}"
        raise CandidateSnapshotError(message)
    return CandidateDerivation(
        entities=entities,
        accessions=accessions,
        observations=[observations[item] for item in cited],
        cited_observation_ids=tuple(cited),
        excluded_form_counts=dict(sorted(excluded_forms.items())),
        excluded_out_of_coverage=out_of_coverage,
    )


def _aggregate_by_entity(
    accessions: Sequence[_AccessionDraft],
    submission_forms: Mapping[int, frozenset[str]],
    conflicted: set[int],
) -> Mapping[int, _EntityAggregates]:
    """Collect the per-entity facts R19 and R20 read, from the derived accession rows.

    Original annual reports are ordered by resolved official filing date so that the
    R19 §4.7 branch-B comparison is between *consecutive* reports; one whose date the
    accepted evidence does not establish sorts last and makes its comparison unresolved
    rather than silently skipped.
    """
    forms: dict[int, list[str]] = defaultdict(list)
    originals: dict[int, list[tuple[str, str | None]]] = defaultdict(list)
    multi: dict[int, bool] = defaultdict(bool)
    non_ordinary: dict[int, bool] = defaultdict(bool)
    for draft in accessions:
        anchor = _as_int(draft.columns["anchor_cik_numeric"])
        form = _as_str(draft.columns["form_type"])
        forms[anchor].append(form)
        if form in _ORIGINAL_ANNUAL_FORMS:
            filing_date = draft.columns["official_filing_date"]
            report_date = draft.columns["report_date"]
            originals[anchor].append(
                (
                    "" if filing_date is None else str(filing_date),
                    None if report_date is None else str(report_date),
                )
            )
        if draft.columns["multi_registrant"]:
            multi[anchor] = True
        linkage = draft.columns["amendment_linkage_state"]
        if isinstance(linkage, str) and linkage in events.NON_ORDINARY_AMENDMENT_LINKAGE_STATES:
            non_ordinary[anchor] = True

    aggregated: dict[int, _EntityAggregates] = {}
    for anchor in set(forms) | set(submission_forms) | conflicted:
        ordered = sorted(originals.get(anchor, ()), key=lambda item: (item[0] == "", item[0]))
        aggregated[anchor] = _EntityAggregates(
            eligible_forms=tuple(sorted(forms.get(anchor, ()))),
            original_annual_report_dates=tuple(report for _, report in ordered),
            original_annual_report_count=len(ordered),
            submission_forms=submission_forms.get(anchor, frozenset()),
            multi_registrant_annual_filing=multi.get(anchor, False),
            non_ordinary_amendment_lineage=non_ordinary.get(anchor, False),
            material_conflict=anchor in conflicted,
        )
    return aggregated


def _within_coverage(draft: _AccessionDraft, inputs: CandidateSnapshotInputs) -> bool:
    """Whether one accession's resolved filing date sits inside the frozen window.

    An accession with no resolved filing date is retained: its exclusion, if any, is a
    downstream eligibility decision, and dropping it here would silently narrow the
    universe.
    """
    filing_date = draft.columns["official_filing_date"]
    if filing_date is None:
        return True
    return inputs.coverage_start <= str(filing_date) <= inputs.coverage_end


# --------------------------------------------------------------------------
# The single authoritative construct-and-freeze transaction (R5)
# --------------------------------------------------------------------------


def _family_digests(derivation: CandidateDerivation) -> dict[str, str]:
    """The seven family digests, over the rows about to be written."""
    entity_rows = [entry.columns for entry in derivation.entities]
    accession_rows = [entry.columns for entry in derivation.accessions]
    registrant_rows = [
        {**registrant, "accession_plain": entry.columns["accession_plain"]}
        for entry in derivation.accessions
        for registrant in entry.registrants
    ]
    entity_evidence = [
        {
            "cik_numeric": _as_int(entry.columns["cik_numeric"]),
            **_evidence_content(draft),
        }
        for entry in derivation.entities
        for draft in entry.evidence
    ]
    accession_evidence = [
        {"accession_plain": entry.columns["accession_plain"], **_evidence_content(draft)}
        for entry in derivation.accessions
        for draft in entry.evidence
    ]
    entity_reasons = [
        {
            "cik_numeric": _as_int(entry.columns["cik_numeric"]),
            "reason_scope": scope,
            "reason_code": code,
        }
        for entry in derivation.entities
        for scope, code in entry.reasons
    ]
    accession_reasons = [
        {
            "accession_plain": entry.columns["accession_plain"],
            "reason_scope": scope,
            "reason_code": code,
        }
        for entry in derivation.accessions
        for scope, code in entry.reasons
    ]
    return {
        "candidate_entity_table_sha256": candidate_entity_table_sha256(entity_rows),
        "candidate_accession_table_sha256": candidate_accession_table_sha256(accession_rows),
        "candidate_registrant_table_sha256": candidate_registrant_table_sha256(registrant_rows),
        "candidate_entity_evidence_sha256": candidate_entity_evidence_sha256(entity_evidence),
        "candidate_accession_evidence_sha256": candidate_accession_evidence_sha256(
            accession_evidence
        ),
        "candidate_entity_reasons_sha256": candidate_entity_reasons_sha256(entity_reasons),
        "candidate_accession_reasons_sha256": candidate_accession_reasons_sha256(accession_reasons),
    }


def _evidence_content(draft: _EvidenceDraft) -> dict[str, object]:
    """The evidence columns the family digests hash, plus the row's own identity."""
    content = draft.content()
    return {
        "classification_dimension": content.classification_dimension,
        "evidence_role": content.evidence_role,
        "source_field": content.source_field,
        "canonical_observed_value": content.canonical_observed_value,
        "policy_version": content.policy_version,
        "precedence": content.precedence,
        "evidence_sha256": content.evidence_sha256,
    }


def _evidence_id(snapshot_id: str, owner: str, draft: _EvidenceDraft) -> str:
    """A stable per-row identifier, excluded from every digest (proposal §D.5)."""
    content = draft.content()
    dimension = content.classification_dimension
    return f"{snapshot_id[:16]}-{owner}-{dimension}-{content.evidence_sha256[:24]}"


def _refuse_existing(connection: sqlite3.Connection, snapshot_id: str) -> None:
    """OQ-3 and R5, both checked **before** any mutation."""
    building = connection.execute(
        "SELECT snapshot_id FROM pilot_candidate_snapshots WHERE snapshot_state = 'building' "
        "ORDER BY snapshot_id"
    ).fetchall()
    if building:
        message = (
            "a building candidate snapshot is present at entry. It is nonauthoritative and "
            "blocks execution pending owner disposition: it is never automatically resumed, "
            "completed, repaired, invalidated, or superseded (R5)."
        )
        raise CandidateSnapshotError(message)
    existing = connection.execute(
        "SELECT snapshot_state FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    if existing is not None:
        message = (
            f"candidate snapshot {snapshot_id} already exists in this catalog. A rebuild "
            "from identical content fails closed (OQ-3): the existing snapshot is never "
            "replaced, ignored, or returned as though newly built."
        )
        raise CandidateSnapshotError(message)


def build_and_freeze_candidate_snapshot(
    *,
    writer: CatalogWriter,
    inputs: CandidateSnapshotInputs,
    fault: str | None = None,
) -> FrozenCandidateSnapshot:
    """Construct and freeze one authoritative candidate snapshot, atomically.

    Args:
        writer: The single logical catalog writer holding the lease.
        inputs: The caller-supplied coverage window and census run.
        fault: A rehearsal-only injection point naming the step to fail at. Production
            callers pass ``None``; it exists so E1's rollback branches exercise the
            **real** transaction rather than a stub of it.

    Raises:
        CandidateSnapshotError: any fail-closed condition. The transaction is rolled
            back in full, leaving no partial authoritative snapshot.
    """
    derivation = derive_candidate_snapshot(writer.connection, inputs)
    return persist_and_freeze_derivation(
        writer=writer, inputs=inputs, derivation=derivation, fault=fault
    )


def persist_and_freeze_derivation(
    *,
    writer: CatalogWriter,
    inputs: CandidateSnapshotInputs,
    derivation: CandidateDerivation,
    fault: str | None = None,
) -> FrozenCandidateSnapshot:
    """Persist and freeze one already-derived candidate snapshot, atomically.

    The single authoritative persistence routine, split from
    :func:`build_and_freeze_candidate_snapshot` so that **exactly one** implementation
    writes the ``pilot_candidate_*`` family (contract §20: no second persistence
    implementation). It writes whatever derivation it is handed and derives nothing of
    its own -- in particular it has no fixture hook, no injection point, and no
    knowledge of any rehearsal path: the production builder above reaches it only with
    the derivation the production rules produced.
    """
    connection = writer.connection

    window = {
        "as_of_date": inputs.as_of_date,
        "coverage_end": inputs.coverage_end,
        "coverage_policy_version": PILOT_COVERAGE_POLICY_VERSION,
        "coverage_start": inputs.coverage_start,
        "include_open_quarter": _INCLUDE_OPEN_QUARTER,
    }
    window_digest = coverage_window_sha256(window)
    observation_digest = input_observation_set_sha256(derivation.observations)
    snapshot_id = snapshot_identity_sha256(
        {
            "candidate_policy_version": PILOT_CANDIDATE_POLICY_VERSION,
            "coverage_window_sha256": window_digest,
            "evidence_policy_version": PILOT_EVIDENCE_POLICY_VERSION,
            "input_observation_set_sha256": observation_digest,
            "sic_family_mapping_version": SIC_FAMILY_MAPPING_VERSION,
        }
    )
    _refuse_existing(connection, snapshot_id)

    digests = _family_digests(derivation)
    entity_count = len(derivation.entities)
    accession_count = len(derivation.accessions)
    content_digest = candidate_snapshot_sha256(
        {
            "accession_count": accession_count,
            "coverage_window_sha256": window_digest,
            "entity_count": entity_count,
            "input_observation_set_sha256": observation_digest,
            "snapshot_id": snapshot_id,
            **digests,
        }
    )

    now = utc_now()
    try:
        with transaction(connection) as active:
            _insert_snapshot(
                active,
                snapshot_id=snapshot_id,
                inputs=inputs,
                window_digest=window_digest,
                observation_digest=observation_digest,
                created=now,
            )
            _fail_at(fault, "after_snapshot_insert")
            _insert_children(active, snapshot_id, derivation)
            _fail_at(fault, "after_children")
            _store_digests(
                active,
                snapshot_id,
                digests=digests,
                entity_count=entity_count,
                accession_count=accession_count,
            )
            _fail_at(fault, "after_digests")
            _revalidate(
                active,
                snapshot_id=snapshot_id,
                derivation=derivation,
                digests=digests,
                observation_digest=observation_digest,
                content_digest=content_digest,
            )
            _fail_at(fault, "after_revalidation")
            active.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'frozen', "
                "frozen_at_utc = ?, candidate_snapshot_sha256 = ? WHERE snapshot_id = ?",
                (now, content_digest, snapshot_id),
            )
    except CandidateSnapshotError:
        raise
    except Exception as exc:  # noqa: BLE001 - every failure rolls back identically
        message = f"candidate snapshot construction failed and rolled back in full: {exc}"
        raise CandidateSnapshotError(message) from exc

    return FrozenCandidateSnapshot(
        snapshot_id=snapshot_id,
        entity_count=entity_count,
        accession_count=accession_count,
        coverage_window_sha256=window_digest,
        input_observation_set_sha256=observation_digest,
        candidate_snapshot_sha256=content_digest,
        family_digests=digests,
        cited_observation_ids=derivation.cited_observation_ids,
        excluded_form_counts=derivation.excluded_form_counts,
        excluded_out_of_coverage=derivation.excluded_out_of_coverage,
    )


def _fail_at(fault: str | None, step: str) -> None:
    """Raise at one named transaction step, for the E1 rollback branches only."""
    if fault == step:
        message = f"injected rehearsal fault at {step}"
        raise CandidateSnapshotError(message)


def _insert_snapshot(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    inputs: CandidateSnapshotInputs,
    window_digest: str,
    observation_digest: str,
    created: str,
) -> None:
    connection.execute(
        "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
        "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
        "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
        "coverage_window_sha256, input_observation_set_sha256, snapshot_state, "
        "created_at_utc, detail) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'building', ?, '')",
        (
            snapshot_id,
            inputs.census_run_id,
            inputs.coverage_start,
            inputs.coverage_end,
            inputs.as_of_date,
            _INCLUDE_OPEN_QUARTER,
            PILOT_COVERAGE_POLICY_VERSION,
            PILOT_CANDIDATE_POLICY_VERSION,
            SIC_FAMILY_MAPPING_VERSION,
            PILOT_EVIDENCE_POLICY_VERSION,
            window_digest,
            observation_digest,
            created,
        ),
    )


def _insert_children(
    connection: sqlite3.Connection, snapshot_id: str, derivation: CandidateDerivation
) -> None:
    """Insert every candidate child row inside the caller's single transaction."""
    for entity in derivation.entities:
        _insert_row(connection, "pilot_candidate_entities", snapshot_id, entity.columns)
    for accession in derivation.accessions:
        _insert_row(connection, "pilot_candidate_accessions", snapshot_id, accession.columns)
        plain = _as_str(accession.columns["accession_plain"])
        for registrant in accession.registrants:
            _insert_row(
                connection,
                "pilot_candidate_accession_registrants",
                snapshot_id,
                {**registrant, "accession_plain": plain},
            )
    for entity in derivation.entities:
        cik = _as_int(entity.columns["cik_numeric"])
        for draft in entity.evidence:
            _insert_evidence(connection, snapshot_id, "cik_numeric", cik, draft, entity=True)
        for scope, code in entity.reasons:
            _insert_row(
                connection,
                "pilot_candidate_entity_reasons",
                snapshot_id,
                {
                    "cik_numeric": cik,
                    "reason_scope": scope,
                    "reason_code": code,
                    "detail": "",
                    "recorded_at_utc": entity.columns["recorded_at_utc"],
                },
            )
    for accession in derivation.accessions:
        plain = _as_str(accession.columns["accession_plain"])
        for draft in accession.evidence:
            _insert_evidence(connection, snapshot_id, "accession_plain", plain, draft, entity=False)
        for scope, code in accession.reasons:
            _insert_row(
                connection,
                "pilot_candidate_accession_reasons",
                snapshot_id,
                {
                    "accession_plain": plain,
                    "reason_scope": scope,
                    "reason_code": code,
                    "detail": "",
                    "recorded_at_utc": accession.columns["recorded_at_utc"],
                },
            )


def _insert_evidence(
    connection: sqlite3.Connection,
    snapshot_id: str,
    parent_column: str,
    parent_value: object,
    draft: _EvidenceDraft,
    *,
    entity: bool,
) -> None:
    content = draft.content()
    table = "pilot_candidate_entity_evidence" if entity else "pilot_candidate_accession_evidence"
    _insert_row(
        connection,
        table,
        snapshot_id,
        {
            "evidence_id": _evidence_id(snapshot_id, str(parent_value), draft),
            parent_column: parent_value,
            "classification_dimension": content.classification_dimension,
            "evidence_role": content.evidence_role,
            "source_observation_id": content.source_observation_id,
            "parsed_record_id": content.parsed_record_id,
            "source_field": content.source_field,
            "canonical_observed_value": content.canonical_observed_value,
            "policy_version": content.policy_version,
            "precedence": content.precedence,
            "evidence_sha256": content.evidence_sha256,
            "recorded_at_utc": utc_now(),
        },
    )


def _insert_row(
    connection: sqlite3.Connection,
    table: str,
    snapshot_id: str,
    values: Mapping[str, object],
) -> None:
    """One plain ``INSERT``. Never ``OR REPLACE``, never ``OR IGNORE`` (OQ-3)."""
    payload = {"snapshot_id": snapshot_id, **values}
    columns = ", ".join(payload)
    placeholders = ", ".join("?" for _ in payload)
    statement = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"  # noqa: S608
    connection.execute(statement, tuple(payload.values()))


def _store_digests(
    connection: sqlite3.Connection,
    snapshot_id: str,
    *,
    digests: Mapping[str, str],
    entity_count: int,
    accession_count: int,
) -> None:
    """Store the seven family digests and both counts while the snapshot is building.

    ``candidate_snapshot_sha256`` is deliberately **not** written here: migration
    ``0009`` forbids a building snapshot from carrying it, so it is written by the
    freeze statement itself, after it has been recomputed from persisted rows.
    """
    assignments = ", ".join(f"{name} = ?" for name in sorted(digests))
    statement = (
        f"UPDATE pilot_candidate_snapshots SET {assignments}, "  # noqa: S608
        "entity_count = ?, accession_count = ? WHERE snapshot_id = ?"
    )
    connection.execute(
        statement,
        (
            *(digests[name] for name in sorted(digests)),
            entity_count,
            accession_count,
            snapshot_id,
        ),
    )


def _recompute_families(connection: sqlite3.Connection, snapshot_id: str) -> dict[str, str]:
    """Recompute the seven family digests from the **persisted** child rows.

    Read back through the same frozen column tuples the write used, so the comparison
    in :func:`_revalidate` tests persistence rather than restating memory.
    """

    def rows(table: str, columns: Sequence[str]) -> list[Mapping[str, object]]:
        selected = ", ".join(columns)
        return [
            dict(row)
            for row in connection.execute(
                f"SELECT {selected} FROM {table} WHERE snapshot_id = ?",  # noqa: S608
                (snapshot_id,),
            ).fetchall()
        ]

    return {
        "candidate_entity_table_sha256": candidate_entity_table_sha256(
            rows("pilot_candidate_entities", ENTITY_TABLE_COLUMNS)
        ),
        "candidate_accession_table_sha256": candidate_accession_table_sha256(
            rows("pilot_candidate_accessions", ACCESSION_TABLE_COLUMNS)
        ),
        "candidate_registrant_table_sha256": candidate_registrant_table_sha256(
            rows("pilot_candidate_accession_registrants", REGISTRANT_TABLE_COLUMNS)
        ),
        "candidate_entity_evidence_sha256": candidate_entity_evidence_sha256(
            rows("pilot_candidate_entity_evidence", ENTITY_EVIDENCE_COLUMNS)
        ),
        "candidate_accession_evidence_sha256": candidate_accession_evidence_sha256(
            rows("pilot_candidate_accession_evidence", ACCESSION_EVIDENCE_COLUMNS)
        ),
        "candidate_entity_reasons_sha256": candidate_entity_reasons_sha256(
            rows("pilot_candidate_entity_reasons", ENTITY_REASONS_COLUMNS)
        ),
        "candidate_accession_reasons_sha256": candidate_accession_reasons_sha256(
            rows("pilot_candidate_accession_reasons", ACCESSION_REASONS_COLUMNS)
        ),
    }


def _revalidate(
    connection: sqlite3.Connection,
    *,
    snapshot_id: str,
    derivation: CandidateDerivation,
    digests: Mapping[str, str],
    observation_digest: str,
    content_digest: str,
) -> None:
    """Independently recompute every identity from the rows just persisted.

    Nothing stored is trusted that was not re-derived (Decision 021 §12). The cited
    observation set is rebuilt from the **persisted** candidate evidence rather than
    from memory, which is what makes the equality non-vacuous (Decision 067 §9.1).
    """
    persisted_ids = sorted(
        {
            str(row["source_observation_id"])
            for row in connection.execute(
                "SELECT source_observation_id FROM pilot_candidate_entity_evidence "
                "WHERE snapshot_id = ? UNION SELECT source_observation_id FROM "
                "pilot_candidate_accession_evidence WHERE snapshot_id = ?",
                (snapshot_id, snapshot_id),
            ).fetchall()
        }
    )
    if tuple(persisted_ids) != derivation.cited_observation_ids:
        message = (
            "the cited observation set recomputed from persisted candidate evidence "
            "differs from the set the snapshot identity was computed over; the whole "
            "transaction rolls back (Decision 067 §9.1; R5)"
        )
        raise CandidateSnapshotError(message)
    if input_observation_set_sha256(derivation.observations) != observation_digest:
        message = "input_observation_set_sha256 did not recompute; the transaction rolls back"
        raise CandidateSnapshotError(message)

    recomputed = _recompute_families(connection, snapshot_id)
    stored = connection.execute(
        "SELECT * FROM pilot_candidate_snapshots WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchone()
    for name, expected in digests.items():
        if recomputed[name] != expected or str(stored[name]) != expected:
            message = f"{name} did not recompute from persisted rows; the transaction rolls back"
            raise CandidateSnapshotError(message)
    _require_counts(connection, snapshot_id, derivation)

    reconstructed = candidate_snapshot_sha256(
        {
            "accession_count": int(stored["accession_count"]),
            "coverage_window_sha256": str(stored["coverage_window_sha256"]),
            "entity_count": int(stored["entity_count"]),
            "input_observation_set_sha256": str(stored["input_observation_set_sha256"]),
            "snapshot_id": str(stored["snapshot_id"]),
            **recomputed,
        }
    )
    if reconstructed != content_digest:
        message = "candidate_snapshot_sha256 did not recompute; the transaction rolls back"
        raise CandidateSnapshotError(message)


def _require_counts(
    connection: sqlite3.Connection, snapshot_id: str, derivation: CandidateDerivation
) -> None:
    """Decision 019 §9 -- declared counts equal actual rows, one anchor per accession."""
    for table, expected in (
        ("pilot_candidate_entities", len(derivation.entities)),
        ("pilot_candidate_accessions", len(derivation.accessions)),
    ):
        actual = int(
            connection.execute(
                f"SELECT COUNT(*) FROM {table} WHERE snapshot_id = ?",  # noqa: S608
                (snapshot_id,),
            ).fetchone()[0]
        )
        if actual != expected:
            message = f"{table} holds {actual} rows for a declared count of {expected}"
            raise CandidateSnapshotError(message)
    offending = connection.execute(
        "SELECT accession_plain FROM pilot_candidate_accession_registrants "
        "WHERE snapshot_id = ? GROUP BY accession_plain HAVING SUM(is_anchor) <> 1",
        (snapshot_id,),
    ).fetchall()
    if offending:
        message = (
            "every candidate accession requires exactly one anchor registrant; "
            f"{len(offending)} accession(s) do not"
        )
        raise CandidateSnapshotError(message)
