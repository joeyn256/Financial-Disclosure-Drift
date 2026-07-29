"""S5.2 -- frozen accession reader, joint run identity, and selection persistence.

The accession-side analogue of :mod:`disclosure_drift.sec.entity_selection_store`
(S4.2). It reads one frozen ``pilot_candidate_snapshots`` row and its migration-0009
child rows, validates their canonical forms and stored hashes, converts them into the
**accepted, unmodified** S5.1 immutable inputs, derives a deterministic content-derived
run identity, invokes the accepted pure solver, persists the result transactionally,
and reconstructs it idempotently.

Governing records:

* Decision 018 -- section 5.3 (fail-closed loader obligations), section 6 (the S4
  entity-only draft is untouched and the S5 joint run gets its own content-derived
  identity), section 17 (the node limit is a required positive run input inside run
  identity; exhaustion discards every incumbent), section 18 (no retry entry point; a
  same-ID ``failed``/``planned``/incomplete-``running`` row gate-fails), section 19
  (**the adapter must not become a second methodological implementation**), section 20
  (the joint policy constant and additive migration ``0011``), section 21 (reason
  codes), sections 26-28 (hashing, lifecycle, failure behaviour).
* Decision 019 -- the four frozen storage-to-pure-input mappings this loader depends
  on: amendment linkage (section 5), multi-registrant aggregation (section 6),
  pre-study support provenance (section 7), former-name identity evidence (section 8),
  the snapshot-freeze obligations (section 9), and the run-identity content those
  mappings contribute (section 10).
* Decision 016 -- section 5 lifecycle vocabulary, section 6 composite
  ``(selection_run_id, snapshot_id)`` keys, section 8 hash boundaries and exclusions.

**Every methodological rule stays in the accepted pure core.** Roles, penalties,
families, fiscal-year-end derivation, name-change contribution, quota counting, the
objective, and the search all live in :mod:`disclosure_drift.sec.accession_selector`
and are *called* here, never re-expressed. The entity side is likewise reused: the
accepted S4.2 :func:`~disclosure_drift.sec.entity_selection_store.load_frozen_entity_candidates`
performs entity-row validation and reconstruction unchanged.

This module opens no network connection, reads no filing text, no CompanyFacts value,
no outcome, and no ``inventory_*`` or ``census_*`` table. The only acceptance field it
reads is ``pilot_candidate_accessions.acceptance_audit_date`` (Decision 019 section
5.9.1); ``acceptance_audit_cohort`` is audit-only and is never read for ordering.

Two deliberate persistence boundaries, recorded so neither is mistaken for an omission:

* **No quota-contribution or quota-result-member rows are written.** No migration-0009
  trigger requires them for a feasible run, the Stage S5.2 contract's persistence list
  does not name them, and deriving per-quota membership here would duplicate quota
  methodology the pure core owns (Decision 018 section 19).
* **``selection_result_sha256`` is left ``NULL``**, exactly as the accepted S4.2
  precedent leaves it. Reconstruction validates the persisted rows against a
  deterministic re-derivation of the pure result instead, which is strictly stronger
  than a stored scalar digest and introduces no new persisted contract.

Neither hash derived here is the M2.3 manifest hash (Stage S6); no manifest or
publication behaviour exists in this module.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from datetime import date
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.pilot_policy import (
    PILOT_JOINT_SELECTOR_POLICY_VERSION,
    PILOT_QUOTA_POLICY_VERSION,
)
from disclosure_drift.release.hashing import hash_table
from disclosure_drift.sec.accession_selector import (
    NOT_APPLICABLE,
    AccessionCandidate,
    AccessionQuotaDiagnostic,
    EntityCandidate,
    JointSelectionResult,
    NameChangeEvidence,
    accession_selection_rank,
    canonical_anchor_cik_padded,
    solve_joint_selection,
)
from disclosure_drift.sec.entity_selection_store import load_frozen_entity_candidates
from disclosure_drift.sec.entity_selector import (
    PILOT_SELECTION_SEED,
    Candidate,
    QuotaDiagnostic,
    selection_rank,
)
from disclosure_drift.storage.sqlite import transaction

__all__ = [
    "ACCESSION_SELECTION_INPUT_SCHEMA_VERSION",
    "FrozenJointCandidateSet",
    "JointSelectionRunIdentity",
    "PersistedJointSelectionResult",
    "build_joint_selection_run_identity",
    "execute_and_persist_joint_selection",
    "load_frozen_joint_candidates",
    "reconstruct_persisted_joint_selection",
]

# Owned by this module (not a repository-wide policy constant): versions the
# normalized joint-selection input/run-identity record shape defined below.
ACCESSION_SELECTION_INPUT_SCHEMA_VERSION: Final = "pilot-joint-selection-input/1.0"

#: Decision 013 section 5 / Decision 018 section 3.1, rendered once so that a change to
#: the frozen term order would visibly change every run identity derived under it.
_OBJECTIVE_TERM_ORDER: Final = (
    "zero_unmet_hard_quotas|minimize_evidence_penalty|minimize_base_accession_count|"
    "minimize_stress_accession_count|minimize_entity_hash_vector|"
    "minimize_accession_hash_vector|canonical_identity_fallback"
)

_PILOT_SELECTION_INFEASIBLE: Final = "PILOT_SELECTION_INFEASIBLE"
_PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN: Final = "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN"

_TERMINAL_RECONSTRUCTABLE_STATES: Final[frozenset[str]] = frozenset(
    {"feasible", "infeasible", "infeasible_or_unproven"}
)

_PROVISIONAL: Final = "provisional"
_REVIEW_REQUIRED: Final = "review_required"
_UNAVAILABLE: Final = "unavailable"

_PLAIN_ACCESSION_PATTERN: Final = re.compile(r"^\d{18}$")
_DASHED_ACCESSION_PATTERN: Final = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_ISO_DATE_PATTERN: Final = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# -- Decision 019 section 5: amendment linkage -------------------------------------- #

_RESOLVED_LINKAGE_STATES: Final[frozenset[str]] = frozenset(
    {"amends_original", "amends_prior_amendment", "supplements_original"}
)
_UNRESOLVED_LINKAGE_STATES: Final[frozenset[str]] = frozenset(
    {"possible_amendment_of", "unresolved_amendment"}
)
_LINKAGE_STATES: Final[frozenset[str]] = _RESOLVED_LINKAGE_STATES | _UNRESOLVED_LINKAGE_STATES

#: Decision 019 section 5.4.1: each resolved state is defined by the *type* of the
#: accession it points at, and that definition is a validation obligation.
_REQUIRED_PARENT_IS_AMENDMENT: Final[Mapping[str, bool]] = {
    "amends_original": False,
    "supplements_original": False,
    "amends_prior_amendment": True,
}

_UNRESOLVED_PARENT_REASON: Final = "REVIEW_AMENDMENT_PARENT_UNRESOLVED"

# -- Decision 019 section 6: multi-registrant --------------------------------------- #

_MULTI_REGISTRANT_SCOPE: Final = "multi_registrant"
_MULTI_REGISTRANT_INCOMPLETE_REASON: Final = "REVIEW_PILOT_MULTI_REGISTRANT_INCOMPLETE"
_REGISTRANT_DIGEST_TABLE: Final = "pilot_candidate_accession_registrants"
_REGISTRANT_DIGEST_COLUMNS: Final[tuple[str, ...]] = (
    "registrant_cik_padded",
    "role",
    "is_anchor",
    "evidence_level",
)
#: Decision 019 section 6.5, evaluated by membership in this exact order.
_REGISTRANT_WEAKER_PRECEDENCE: Final[tuple[str, ...]] = (
    "conflicting",
    "review_required",
    "unavailable",
)

# -- Decision 019 section 7: pre-study support provenance --------------------------- #

_COHORT_SCOPE: Final = "cohort"
_PRE_STUDY_REASON: Final = "PILOT_ACCESSION_PRE_STUDY_SUPPORT"
_PRE_STUDY_FILING_YEAR: Final = 2009
_ORIGINAL_ANNUAL_REPORT_FORM: Final = "10-K"

# -- Decision 019 section 8: former-name identity evidence -------------------------- #

_IDENTITY_DIMENSION: Final = "identity"
_IDENTITY_SCOPE: Final = "identity"
_FORMER_NAME_SOURCE_FIELD: Final = "former_name_relationship"
_TICKER_CHANGE_SOURCE_FIELD: Final = "ticker_change"
_SUPPORTED_IDENTITY_SOURCE_FIELDS: Final[frozenset[str]] = frozenset(
    {_FORMER_NAME_SOURCE_FIELD, _TICKER_CHANGE_SOURCE_FIELD}
)
_EVIDENCE_ROLES: Final[frozenset[str]] = frozenset({"winning", "competing", "supporting"})
_PRIOR_CURRENT_KEYS: Final[frozenset[str]] = frozenset(
    {"current_name", "prior_name", "relationship"}
)
_FROM_TO_KEYS: Final[frozenset[str]] = frozenset({"from_name", "relationship", "to_name"})
_PRIOR_CURRENT_RELATIONSHIP: Final = "prior_current"
_FROM_TO_RELATIONSHIP: Final = "from_to"
_ASCII_LOWER_TABLE: Final[Mapping[int, int]] = str.maketrans(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"
)

# -- Run-identity record shapes ------------------------------------------------------ #

_ENTITY_CONTENT_TABLE: Final = "pilot_joint_selection_entity_candidates"
_ENTITY_CONTENT_COLUMNS: Final[tuple[str, ...]] = (
    "cik_padded",
    "category",
    "primary_universe_eligible",
    "engineering_only_stress",
    "size_stratum",
    "size_evidence_level",
    "industry_group",
    "industry_evidence_level",
    "industry_quota_eligible",
    "history_class",
    "history_evidence_level",
    "currently_inactive",
    "control_kind",
    "evidence_penalty",
    "name_change_has_identity_evidence",
    "name_change_evidence_role",
    "name_change_evidence_level",
    "name_change_former_name_record_parseable",
    "name_change_has_prior_current_or_from_to",
    "name_change_ticker_change_claimed",
)

_ACCESSION_CONTENT_TABLE: Final = "pilot_joint_selection_accession_candidates"
_ACCESSION_CONTENT_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "accession_number_dashed",
    "anchor_cik_padded",
    "form_type",
    "is_amendment",
    "official_filing_date",
    "report_date",
    "acceptance_audit_date",
    "cohort_applicability",
    "provisional_official_cohort",
    "cohort_ambiguous",
    "filing_date_evidence_level",
    "cohort_evidence_level",
    "stored_cohort_evidence_level",
    "xbrl_evidence_level",
    "amendment_purpose_evidence_level",
    "stored_amendment_purpose_evidence_level",
    "amendment_linkage_evidence_level",
    "multi_registrant_evidence_level",
    "has_xbrl",
    "has_inline_xbrl",
    "stored_amendment_linkage_state",
    "stored_provisional_parent_accession",
    "provisional_parent_accession_dashed",
    "amendment_purpose_category",
    "amendment_purpose_quota_eligible",
    "base_eligible",
    "stress_eligible",
    "support_eligible",
    "control_eligible",
    "multi_registrant",
    "registrant_content_sha256",
)

_EVIDENCE_CONTENT_COLUMNS: Final[tuple[str, ...]] = (
    "owner",
    "classification_dimension",
    "evidence_role",
    "source_field",
    "canonical_observed_value",
    "policy_version",
    "precedence",
    "parsed_record_id",
    "evidence_sha256",
)
_REASON_CONTENT_COLUMNS: Final[tuple[str, ...]] = ("owner", "reason_scope", "reason_code")

_ENTITY_EVIDENCE_CONTENT_TABLE: Final = "pilot_candidate_entity_evidence_content"
_ACCESSION_EVIDENCE_CONTENT_TABLE: Final = "pilot_candidate_accession_evidence_content"
_ENTITY_REASON_CONTENT_TABLE: Final = "pilot_candidate_entity_reasons_content"
_ACCESSION_REASON_CONTENT_TABLE: Final = "pilot_candidate_accession_reasons_content"

_CANDIDATE_ACCESSION_COLUMNS: Final[tuple[str, ...]] = (
    "accession_plain",
    "accession_number_dashed",
    "accession_tie_break_sha256",
    "anchor_cik_numeric",
    "form_type",
    "is_amendment",
    "official_filing_date",
    "report_date",
    "acceptance_audit_date",
    "filing_date_evidence_level",
    "provisional_official_cohort",
    "cohort_evidence_level",
    "cohort_ambiguous",
    "has_xbrl",
    "has_inline_xbrl",
    "xbrl_evidence_level",
    "amendment_linkage_state",
    "provisional_parent_accession",
    "amendment_purpose_category",
    "amendment_purpose_evidence_level",
    "amendment_purpose_quota_eligible",
    "base_eligible",
    "stress_eligible",
    "support_eligible",
    "control_eligible",
    "multi_registrant",
)


# --------------------------------------------------------------------------
# Public records
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FrozenJointCandidateSet:
    """One frozen snapshot converted into the accepted S5.1 immutable inputs.

    ``entity_content_sha256`` and ``accession_content_sha256`` are the row-order
    independent digests of the complete normalized candidate content each side
    contributes to run identity (Decision 019 section 10).
    """

    snapshot_id: str
    candidate_snapshot_sha256: str
    entity_count: int
    accession_count: int
    entities: tuple[EntityCandidate, ...]
    accessions: tuple[AccessionCandidate, ...]
    entity_content_sha256: str
    accession_content_sha256: str


@dataclass(frozen=True, slots=True)
class JointSelectionRunIdentity:
    """The deterministic, content-derived identity of one S5 joint selection run."""

    snapshot_id: str
    selection_seed: str
    selector_policy_version: str
    quota_policy_version: str
    node_limit: int
    selection_input_sha256: str
    selection_run_id: str


@dataclass(frozen=True, slots=True)
class PersistedJointSelectionResult:
    """The single S5.2 run-metadata wrapper around an accepted pure S5.1 result.

    It carries the run identity, the snapshot and policy provenance, the execution
    inputs, and the reconstructed
    :class:`~disclosure_drift.sec.accession_selector.JointSelectionResult`. It derives
    no methodological value of its own and reinterprets nothing the pure core computed.
    """

    selection_run_id: str
    snapshot_id: str
    candidate_snapshot_sha256: str
    run_state: str
    selection_seed: str
    selector_policy_version: str
    quota_policy_version: str
    node_limit: int
    expanded_node_count: int
    node_limit_exhausted: bool
    selection_input_sha256: str
    selected_entity_count: int
    selected_accession_count: int
    result: JointSelectionResult


# --------------------------------------------------------------------------
# Narrowing helpers -- SQLite cells are ``Any``; every field is narrowed once
# --------------------------------------------------------------------------


def _fail(message: str) -> GateFailureError:
    return GateFailureError(message)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str):
        message = f"{field} must be TEXT, found {type(value).__name__}"
        raise _fail(message)
    return value


def _optional_text(value: object, field: str) -> str | None:
    return None if value is None else _text(value, field)


def _integer(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"{field} must be an INTEGER, found {type(value).__name__}"
        raise _fail(message)
    return value


def _flag(value: object, field: str) -> bool:
    number = _integer(value, field)
    if number not in (0, 1):
        message = f"{field} must be 0 or 1, found {number}"
        raise _fail(message)
    return number == 1


def _exact_calendar_date(value: str | None) -> date | None:
    """Parse an exact, real ``YYYY-MM-DD`` calendar date, else ``None``.

    The regular expression is required: :meth:`datetime.date.fromisoformat` accepts
    further ISO-8601 spellings, and Decision 019 section 5.9 admits exactly one.
    """
    if value is None or _ISO_DATE_PATTERN.match(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _dashed_from_plain(plain: str, context: str) -> str:
    """Render the canonical dashed form of a plain 18-digit accession (Decision 018 §5.1)."""
    if _PLAIN_ACCESSION_PATTERN.match(plain) is None:
        message = (
            f"{context}: stored accession identity {plain!r} is not exactly eighteen decimal digits"
        )
        raise _fail(message)
    return f"{plain[:10]}-{plain[10:12]}-{plain[12:]}"


# --------------------------------------------------------------------------
# Narrowed frozen row shapes
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _AccessionRow:
    """One narrowed ``pilot_candidate_accessions`` row."""

    accession_plain: str
    accession_number_dashed: str
    accession_tie_break_sha256: str
    anchor_cik_numeric: int
    form_type: str
    is_amendment: bool
    official_filing_date: str | None
    report_date: str | None
    acceptance_audit_date: str | None
    filing_date_evidence_level: str
    provisional_official_cohort: str | None
    cohort_evidence_level: str
    cohort_ambiguous: bool
    has_xbrl: bool
    has_inline_xbrl: bool
    xbrl_evidence_level: str
    amendment_linkage_state: str | None
    provisional_parent_accession: str | None
    amendment_purpose_category: str | None
    amendment_purpose_evidence_level: str
    amendment_purpose_quota_eligible: bool
    base_eligible: bool
    stress_eligible: bool
    support_eligible: bool
    control_eligible: bool
    multi_registrant: bool


@dataclass(frozen=True, slots=True)
class _RegistrantRow:
    """One narrowed ``pilot_candidate_accession_registrants`` row."""

    accession_plain: str
    registrant_cik_numeric: int
    registrant_cik_padded: str
    role: str
    is_anchor: bool
    evidence_level: str


@dataclass(frozen=True, slots=True)
class _EvidenceRow:
    """One narrowed candidate-evidence row (entity or accession side)."""

    owner: str
    classification_dimension: str
    evidence_role: str
    source_field: str
    canonical_observed_value: str | None
    policy_version: str
    precedence: int
    parsed_record_id: str | None
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class _ReasonRow:
    """One narrowed candidate-reason row (entity or accession side)."""

    owner: str
    reason_scope: str
    reason_code: str


def _accession_row(row: sqlite3.Row) -> _AccessionRow:
    plain = _text(row["accession_plain"], "pilot_candidate_accessions.accession_plain")
    return _AccessionRow(
        accession_plain=plain,
        accession_number_dashed=_text(row["accession_number_dashed"], f"{plain} dashed accession"),
        accession_tie_break_sha256=_text(row["accession_tie_break_sha256"], f"{plain} tie-break"),
        anchor_cik_numeric=_integer(row["anchor_cik_numeric"], f"{plain} anchor_cik_numeric"),
        form_type=_text(row["form_type"], f"{plain} form_type"),
        is_amendment=_flag(row["is_amendment"], f"{plain} is_amendment"),
        official_filing_date=_optional_text(row["official_filing_date"], f"{plain} filing date"),
        report_date=_optional_text(row["report_date"], f"{plain} report_date"),
        acceptance_audit_date=_optional_text(
            row["acceptance_audit_date"], f"{plain} acceptance_audit_date"
        ),
        filing_date_evidence_level=_text(
            row["filing_date_evidence_level"], f"{plain} filing_date_evidence_level"
        ),
        provisional_official_cohort=_optional_text(
            row["provisional_official_cohort"], f"{plain} provisional_official_cohort"
        ),
        cohort_evidence_level=_text(row["cohort_evidence_level"], f"{plain} cohort_evidence_level"),
        cohort_ambiguous=_flag(row["cohort_ambiguous"], f"{plain} cohort_ambiguous"),
        has_xbrl=_flag(row["has_xbrl"], f"{plain} has_xbrl"),
        has_inline_xbrl=_flag(row["has_inline_xbrl"], f"{plain} has_inline_xbrl"),
        xbrl_evidence_level=_text(row["xbrl_evidence_level"], f"{plain} xbrl_evidence_level"),
        amendment_linkage_state=_optional_text(
            row["amendment_linkage_state"], f"{plain} amendment_linkage_state"
        ),
        provisional_parent_accession=_optional_text(
            row["provisional_parent_accession"], f"{plain} provisional_parent_accession"
        ),
        amendment_purpose_category=_optional_text(
            row["amendment_purpose_category"], f"{plain} amendment_purpose_category"
        ),
        amendment_purpose_evidence_level=_text(
            row["amendment_purpose_evidence_level"], f"{plain} amendment_purpose_evidence_level"
        ),
        amendment_purpose_quota_eligible=_flag(
            row["amendment_purpose_quota_eligible"], f"{plain} amendment_purpose_quota_eligible"
        ),
        base_eligible=_flag(row["base_eligible"], f"{plain} base_eligible"),
        stress_eligible=_flag(row["stress_eligible"], f"{plain} stress_eligible"),
        support_eligible=_flag(row["support_eligible"], f"{plain} support_eligible"),
        control_eligible=_flag(row["control_eligible"], f"{plain} control_eligible"),
        multi_registrant=_flag(row["multi_registrant"], f"{plain} multi_registrant"),
    )


# --------------------------------------------------------------------------
# Decision 019 section 5 -- amendment-linkage evidence
# --------------------------------------------------------------------------


def _validate_linkage_representation(row: _AccessionRow, reason_codes: frozenset[str]) -> None:
    """Every Decision 019 section 5.8 condition that a single stored row can express.

    These are evaluated for **every** candidate accession before any chain is walked,
    so a gate always precedes a mapping (Decision 019 section 4 principle 7).
    """
    state = row.amendment_linkage_state
    parent = row.provisional_parent_accession
    where = f"accession {row.accession_number_dashed}"

    if state is not None and state not in _LINKAGE_STATES:
        message = f"{where}: amendment_linkage_state {state!r} is outside the frozen vocabulary"
        raise _fail(message)
    if not row.is_amendment:
        if state is not None:
            message = f"{where}: a non-amendment carries amendment_linkage_state {state!r}"
            raise _fail(message)
        if parent is not None:
            message = f"{where}: a non-amendment carries provisional_parent_accession {parent!r}"
            raise _fail(message)
        return
    if state is None:
        message = f"{where}: an amendment carries no amendment_linkage_state"
        raise _fail(message)

    if parent is not None:
        if _PLAIN_ACCESSION_PATTERN.match(parent) is None:
            message = (
                f"{where}: provisional_parent_accession {parent!r} is not exactly eighteen "
                "decimal digits"
            )
            raise _fail(message)
        if parent == row.accession_plain:
            message = f"{where}: provisional_parent_accession is self-referential"
            raise _fail(message)
    if state in _RESOLVED_LINKAGE_STATES and parent is None:
        message = f"{where}: resolved linkage state {state!r} carries no parent identity"
        raise _fail(message)
    if state == "unresolved_amendment" and parent is not None:
        message = (
            f"{where}: unresolved_amendment cannot also carry the stored parent identity {parent!r}"
        )
        raise _fail(message)

    carries_review = _UNRESOLVED_PARENT_REASON in reason_codes
    if state in _RESOLVED_LINKAGE_STATES and carries_review:
        message = (
            f"{where}: resolved linkage state {state!r} contradicts its stored "
            f"{_UNRESOLVED_PARENT_REASON} reason row"
        )
        raise _fail(message)
    if state in _UNRESOLVED_LINKAGE_STATES and not carries_review:
        message = (
            f"{where}: unresolved linkage state {state!r} requires a "
            f"{_UNRESOLVED_PARENT_REASON} reason row"
        )
        raise _fail(message)


def _walk_to_root_original(
    start: _AccessionRow, rows_by_plain: Mapping[str, _AccessionRow]
) -> _AccessionRow | None:
    """Walk ``provisional_parent_accession`` to the resolved root original.

    Returns the root original's row, or ``None`` when a hop's well-formed parent
    identity is simply **absent** from the frozen snapshot (Decision 019 section 5.6).
    Every other chain condition of sections 5.4.1, 5.4.2, and 5.8 raises.
    """
    where = f"accession {start.accession_number_dashed}"
    visited = {start.accession_plain}
    cursor = start
    while True:
        parent_plain = cursor.provisional_parent_accession
        if parent_plain is None:  # pragma: no cover -- excluded by the row-level gate
            message = f"{where}: chain hop {cursor.accession_number_dashed} carries no parent"
            raise _fail(message)
        parent = rows_by_plain.get(parent_plain)
        if parent is None:
            return None
        if parent_plain in visited:
            message = (
                f"{where}: the amendment parent chain revisits {parent.accession_number_dashed} "
                "and therefore terminates at no original"
            )
            raise _fail(message)
        visited.add(parent_plain)

        state = cursor.amendment_linkage_state or ""
        required_is_amendment = _REQUIRED_PARENT_IS_AMENDMENT.get(state)
        if required_is_amendment is not None and parent.is_amendment != required_is_amendment:
            message = (
                f"{where}: chain hop {cursor.accession_number_dashed} is stored as {state!r} but "
                f"its parent {parent.accession_number_dashed} has "
                f"is_amendment={int(parent.is_amendment)}"
            )
            raise _fail(message)
        if not parent.is_amendment:
            return parent

        parent_state = parent.amendment_linkage_state
        if parent_state == "unresolved_amendment":
            message = (
                f"{where}: the parent chain reaches {parent.accession_number_dashed} in "
                "unresolved_amendment, a dead end that terminates at no original"
            )
            raise _fail(message)
        if parent_state == "possible_amendment_of" and parent.provisional_parent_accession is None:
            message = (
                f"{where}: the parent chain reaches {parent.accession_number_dashed} in "
                "possible_amendment_of with no stored candidate parent, a dead end that "
                "terminates at no original"
            )
            raise _fail(message)
        cursor = parent


def _require_strict_acceptance_order(amendment: _AccessionRow, root: _AccessionRow) -> None:
    """Decision 019 section 5.9.3: only a strictly later amendment date is admissible.

    Reads ``acceptance_audit_date`` alone. ``acceptance_audit_cohort`` is a categorical
    audit-only label and is never consulted; no ``inventory_*`` or ``census_*``
    acceptance column is read, and no timestamp, time of day, or time zone is inferred.
    """
    where = f"accession {amendment.accession_number_dashed}"
    amendment_date = _exact_calendar_date(amendment.acceptance_audit_date)
    root_date = _exact_calendar_date(root.acceptance_audit_date)
    if amendment_date is None:
        message = (
            f"{where}: a resolved linkage state requires an exact YYYY-MM-DD "
            f"acceptance_audit_date, found {amendment.acceptance_audit_date!r}"
        )
        raise _fail(message)
    if root_date is None:
        message = (
            f"{where}: its resolved root original {root.accession_number_dashed} requires an exact "
            f"YYYY-MM-DD acceptance_audit_date, found {root.acceptance_audit_date!r}"
        )
        raise _fail(message)
    # Two exact calendar dates are always totally ordered by comparison, so this covers
    # strictly earlier, equal, and every residual "otherwise incomparable" condition.
    if amendment_date <= root_date:
        message = (
            f"{where}: acceptance_audit_date {amendment.acceptance_audit_date!r} is not strictly "
            f"later than its resolved root original {root.accession_number_dashed}'s "
            f"{root.acceptance_audit_date!r}"
        )
        raise _fail(message)


def _amendment_linkage_mapping(
    row: _AccessionRow, rows_by_plain: Mapping[str, _AccessionRow]
) -> tuple[str, str | None]:
    """Decision 019 section 5.2's frozen mapping: ``(evidence_level, parent_dashed)``."""
    state = row.amendment_linkage_state
    if state is None:
        return NOT_APPLICABLE, None
    if state == "possible_amendment_of":
        return _REVIEW_REQUIRED, None
    if state == "unresolved_amendment":
        return _UNAVAILABLE, None

    root = _walk_to_root_original(row, rows_by_plain)
    if root is None:
        # Section 5.6: an affirmative claim the snapshot cannot corroborate. The
        # section 5.9 ordering gate is inapplicable rather than failed here.
        return _REVIEW_REQUIRED, None
    _require_strict_acceptance_order(row, root)
    parent_plain = row.provisional_parent_accession
    if parent_plain is None:  # pragma: no cover -- excluded by the row-level gate
        message = f"accession {row.accession_number_dashed}: resolved state lost its parent"
        raise _fail(message)
    return _PROVISIONAL, _dashed_from_plain(
        parent_plain, f"accession {row.accession_number_dashed}"
    )


# --------------------------------------------------------------------------
# Decision 019 section 6 -- multi-registrant evidence
# --------------------------------------------------------------------------


def _registrant_content_sha256(registrants: Sequence[_RegistrantRow]) -> str:
    """Decision 019 section 6.6.1's frozen per-accession registrant digest.

    Every registrant row of the accession is included, ``submitter_only`` rows among
    them; ``recorded_at_utc`` and every other timestamp is excluded, and
    :func:`~disclosure_drift.release.hashing.hash_table` sorts its rendered rows, so
    the digest is row-order independent by construction. It is never written back.
    """
    rows = (
        {
            "registrant_cik_padded": registrant.registrant_cik_padded,
            "role": registrant.role,
            "is_anchor": int(registrant.is_anchor),
            "evidence_level": registrant.evidence_level,
        }
        for registrant in registrants
    )
    return hash_table(
        _REGISTRANT_DIGEST_TABLE, _REGISTRANT_DIGEST_COLUMNS, rows
    ).normalized_content_sha256


def _multi_registrant_mapping(
    row: _AccessionRow,
    registrants: Sequence[_RegistrantRow],
    reason_scopes: Mapping[str, frozenset[str]],
) -> str:
    """Decision 019 sections 6.2-6.5: the aggregate ``multi_registrant_evidence_level``."""
    where = f"accession {row.accession_number_dashed}"
    if not registrants:
        message = f"{where}: no pilot_candidate_accession_registrants row exists"
        raise _fail(message)

    anchors = [registrant for registrant in registrants if registrant.role == "anchor"]
    if len(anchors) != 1:
        message = f"{where}: expected exactly one anchor registrant row, found {len(anchors)}"
        raise _fail(message)
    if anchors[0].registrant_cik_numeric != row.anchor_cik_numeric:
        message = (
            f"{where}: the anchor registrant CIK {anchors[0].registrant_cik_numeric} does not "
            f"match anchor_cik_numeric {row.anchor_cik_numeric}"
        )
        raise _fail(message)

    seen_padded: set[str] = set()
    for registrant in registrants:
        expected = canonical_anchor_cik_padded(registrant.registrant_cik_numeric)
        if registrant.registrant_cik_padded != expected:
            message = (
                f"{where}: registrant_cik_padded {registrant.registrant_cik_padded!r} is not the "
                f"canonical rendering of {registrant.registrant_cik_numeric}"
            )
            raise _fail(message)
        if registrant.registrant_cik_padded in seen_padded:
            message = f"{where}: duplicate registrant identity {registrant.registrant_cik_padded!r}"
            raise _fail(message)
        seen_padded.add(registrant.registrant_cik_padded)

    set_establishing = [
        registrant for registrant in registrants if registrant.role in ("anchor", "associated")
    ]
    qualifies = any(registrant.role == "associated" for registrant in registrants)

    if not row.multi_registrant:
        if qualifies:
            _require_multi_registrant_divergence(where, reason_scopes)
        return NOT_APPLICABLE
    if not qualifies:
        message = (
            f"{where}: multi_registrant = 1 without a qualifying registrant set (one anchor plus "
            "at least one associated row)"
        )
        raise _fail(message)
    if all(registrant.evidence_level == _PROVISIONAL for registrant in set_establishing):
        return _PROVISIONAL
    present = {registrant.evidence_level for registrant in set_establishing}
    for level in _REGISTRANT_WEAKER_PRECEDENCE:
        if level in present:
            return level
    message = f"{where}: registrant evidence levels {sorted(present)!r} are outside the frozen set"
    raise _fail(message)


def _require_multi_registrant_divergence(
    where: str, reason_scopes: Mapping[str, frozenset[str]]
) -> None:
    """Decision 019 section 6.3's single permitted divergence, by exact code.

    Deliberately stricter than migration 0009's freeze trigger, which can only test the
    scope: a scope is not a fact, and the divergence is meaningful for exactly one
    recorded condition.
    """
    codes = reason_scopes.get(_MULTI_REGISTRANT_SCOPE, frozenset())
    if codes != frozenset({_MULTI_REGISTRANT_INCOMPLETE_REASON}):
        message = (
            f"{where}: multi_registrant = 0 alongside associated registrant rows is authorized "
            f"only by exactly one {_MULTI_REGISTRANT_SCOPE}-scope reason row carrying exactly "
            f"{_MULTI_REGISTRANT_INCOMPLETE_REASON}, found {sorted(codes)!r}"
        )
        raise _fail(message)


# --------------------------------------------------------------------------
# Decision 019 section 7 -- explicit pre-study support provenance
# --------------------------------------------------------------------------


def _cohort_mapping(
    row: _AccessionRow, reason_scopes: Mapping[str, frozenset[str]]
) -> tuple[str, str, str | None]:
    """Return ``(cohort_applicability, cohort_evidence_level, provisional_official_cohort)``.

    Pre-study applicability is established only by the complete Decision 019 section 7.2
    conjunction, never by a null cohort alone. The marker row is validated and consumed;
    it is never created here (section 7.3).
    """
    where = f"accession {row.accession_number_dashed}"
    if row.cohort_evidence_level == _PROVISIONAL and row.provisional_official_cohort is None:
        message = (
            f"{where}: provisional cohort evidence without a resolved provisional_official_cohort "
            "is contradictory cohort evidence"
        )
        raise _fail(message)

    marker = _PRE_STUDY_REASON in reason_scopes.get(_COHORT_SCOPE, frozenset())
    if not marker:
        # Section 7.4: an in-window or otherwise out-of-window accession stays
        # applicable and carries whatever cohort evidence it has.
        return "applies", row.cohort_evidence_level, row.provisional_official_cohort

    filing_date = _exact_calendar_date(row.official_filing_date)
    # A calendar-2009 official filing date is outside every frozen study window by
    # construction (the development window opens in 2010), so section 7.5's
    # "inside a study cohort window" condition is discharged by the year test.
    failures: list[str] = []
    if row.is_amendment or row.form_type != _ORIGINAL_ANNUAL_REPORT_FORM:
        failures.append(f"not an original 10-K (form {row.form_type!r})")
    if filing_date is None or filing_date.year != _PRE_STUDY_FILING_YEAR:
        failures.append(f"official_filing_date {row.official_filing_date!r} is not in 2009")
    if not row.support_eligible:
        failures.append("support_eligible = 0")
    if row.base_eligible:
        failures.append("base_eligible = 1")
    if row.provisional_official_cohort is not None:
        failures.append(
            f"provisional_official_cohort {row.provisional_official_cohort!r} is not NULL"
        )
    if row.cohort_ambiguous:
        failures.append("cohort_ambiguous = 1")
    if failures:
        message = (
            f"{where}: the {_PRE_STUDY_REASON} provenance row is contradicted by "
            f"{'; '.join(failures)}"
        )
        raise _fail(message)
    return "pre_study", NOT_APPLICABLE, None


# --------------------------------------------------------------------------
# Decision 019 section 8 -- former-name identity evidence
# --------------------------------------------------------------------------


def _normalized_name(value: str, where: str) -> str:
    """Decision 019 section 8.2.1's frozen normalization, applied as a *test* only."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as error:
        message = f"{where}: a stored name value is not decodable as valid Unicode"
        raise _fail(message) from error
    return " ".join(unicodedata.normalize("NFC", value).split())


def _canonical_json(payload: Mapping[str, str]) -> str:
    return json.dumps(dict(payload), sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _ascii_casefold(value: str) -> str:
    return value.translate(_ASCII_LOWER_TABLE)


def _parse_former_name_payload(stored: str | None, where: str) -> dict[str, str]:
    """Validate one ``former_name_relationship`` payload against Decision 019 section 8.2.

    Every failure here is *structural corruption*: the snapshot is invalid for Stage S5.
    Content failures (empty or equal names) are separate and produce ``review_required``.
    """
    if stored is None or stored == "":
        message = f"{where}: a former-name row carries a NULL or empty canonical_observed_value"
        raise _fail(message)
    try:
        parsed: object = json.loads(stored)
    except json.JSONDecodeError as error:
        message = f"{where}: the former-name payload does not parse under strict JSON"
        raise _fail(message) from error
    if not isinstance(parsed, dict):
        message = f"{where}: the former-name payload is not a JSON object"
        raise _fail(message)

    keys = frozenset(parsed)
    if keys == _PRIOR_CURRENT_KEYS:
        expected_relationship = _PRIOR_CURRENT_RELATIONSHIP
    elif keys == _FROM_TO_KEYS:
        expected_relationship = _FROM_TO_RELATIONSHIP
    else:
        message = (
            f"{where}: the former-name payload key set {sorted(keys)!r} is neither permitted form"
        )
        raise _fail(message)

    payload: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(value, str):
            message = f"{where}: former-name payload value for {key!r} is not a JSON string"
            raise _fail(message)
        payload[key] = value
    if payload["relationship"] != expected_relationship:
        message = (
            f"{where}: former-name relationship {payload['relationship']!r} does not match the "
            f"required {expected_relationship!r} for its key set"
        )
        raise _fail(message)
    for key, value in payload.items():
        if key == "relationship":
            continue
        if _normalized_name(value, where) != value:
            message = f"{where}: stored name {key!r} is not byte-identical to its normalized form"
            raise _fail(message)
    if _canonical_json(payload) != stored:
        message = f"{where}: the former-name payload is not its own canonical reserialization"
        raise _fail(message)
    return payload


def _former_name_content_ok(payload: Mapping[str, str]) -> bool:
    """Decision 019 section 8.4's content tests: nonempty, and a genuine change."""
    if payload["relationship"] == _PRIOR_CURRENT_RELATIONSHIP:
        first, second = payload["prior_name"], payload["current_name"]
    else:
        first, second = payload["from_name"], payload["to_name"]
    if not first or not second:
        return False
    return _ascii_casefold(first) != _ascii_casefold(second)


def _ticker_change_claimed(rows: Sequence[_EvidenceRow], where: str) -> bool:
    """Decision 019 section 8.5's total derivation. Absence is silent, never a warning."""
    if not rows:
        return False
    if len(rows) > 1:
        message = f"{where}: {len(rows)} ticker_change rows exist; at most one is permitted"
        raise _fail(message)
    row = rows[0]
    if row.parsed_record_id is None:
        message = f"{where}: the ticker_change row carries a NULL parsed_record_id"
        raise _fail(message)
    if row.canonical_observed_value is not None:
        message = (
            f"{where}: the ticker_change row carries a non-NULL canonical_observed_value; M2.3 "
            "freezes no ticker payload interpretation"
        )
        raise _fail(message)
    return True


def _name_change_evidence(cik_padded: str, rows: Sequence[_EvidenceRow]) -> NameChangeEvidence:
    """Decision 019 sections 8.3.1-8.3.2: the deterministic six-field branch table."""
    where = f"entity {cik_padded} identity evidence"
    for row in rows:
        if row.parsed_record_id is None:
            message = f"{where}: an identity row carries a NULL parsed_record_id"
            raise _fail(message)
        if row.evidence_role not in _EVIDENCE_ROLES:
            message = f"{where}: evidence_role {row.evidence_role!r} is outside the vocabulary"
            raise _fail(message)
        if row.source_field not in _SUPPORTED_IDENTITY_SOURCE_FIELDS:
            message = f"{where}: source_field {row.source_field!r} is unsupported at Stage S5"
            raise _fail(message)

    former = [row for row in rows if row.source_field == _FORMER_NAME_SOURCE_FIELD]
    ticker = [row for row in rows if row.source_field == _TICKER_CHANGE_SOURCE_FIELD]
    _reject_byte_identical_duplicates(former, where, _FORMER_NAME_SOURCE_FIELD)
    _reject_byte_identical_duplicates(ticker, where, _TICKER_CHANGE_SOURCE_FIELD)

    payloads = {
        row: _parse_former_name_payload(row.canonical_observed_value, where) for row in former
    }
    claimed = _ticker_change_claimed(ticker, where)

    if not former:
        # Branch 1 (no identity rows at all) and branch 2 (ticker-only).
        return NameChangeEvidence(
            has_identity_evidence=claimed,
            evidence_role="supporting",
            evidence_level=_UNAVAILABLE,
            ticker_change_claimed=claimed,
        )

    winning = [row for row in former if row.evidence_role == "winning"]
    others = [row for row in former if row.evidence_role != "winning"]
    if len(winning) == 1:
        passes = _former_name_content_ok(payloads[winning[0]])
        return NameChangeEvidence(  # branches 3 and 4
            has_identity_evidence=True,
            evidence_role="winning",
            evidence_level=_PROVISIONAL if passes else _REVIEW_REQUIRED,
            former_name_record_parseable=passes,
            has_prior_current_or_from_to=passes,
            ticker_change_claimed=claimed,
        )
    if not winning:
        parseable = any(_former_name_content_ok(payloads[row]) for row in others)
        competing = any(row.evidence_role == "competing" for row in others)
        return NameChangeEvidence(  # branch 5
            has_identity_evidence=True,
            evidence_role="competing" if competing else "supporting",
            evidence_level=_REVIEW_REQUIRED,
            former_name_record_parseable=parseable,
            has_prior_current_or_from_to=parseable,
            ticker_change_claimed=claimed,
        )
    parseable = all(_former_name_content_ok(payloads[row]) for row in winning)
    return NameChangeEvidence(  # branch 6: two or more distinct winning payloads
        has_identity_evidence=True,
        evidence_role="winning",
        evidence_level="conflicting",
        former_name_record_parseable=parseable,
        has_prior_current_or_from_to=parseable,
        ticker_change_claimed=claimed,
    )


def _reject_byte_identical_duplicates(
    rows: Sequence[_EvidenceRow], where: str, source_field: str
) -> None:
    """Duplicated representations of one fact are never deduplicated or counted once."""
    seen: set[str | None] = set()
    for row in rows:
        if row.canonical_observed_value in seen:
            message = (
                f"{where}: two {source_field} rows carry byte-identical canonical_observed_value"
            )
            raise _fail(message)
        seen.add(row.canonical_observed_value)


# --------------------------------------------------------------------------
# Frozen reader
# --------------------------------------------------------------------------


def _fetch_evidence(
    connection: sqlite3.Connection, snapshot_id: str, *, entity_side: bool
) -> tuple[_EvidenceRow, ...]:
    table = (
        "pilot_candidate_entity_evidence" if entity_side else "pilot_candidate_accession_evidence"
    )
    owner_column = "cik_numeric" if entity_side else "accession_plain"
    rows = connection.execute(
        f"SELECT {owner_column} AS owner, classification_dimension, evidence_role, "  # noqa: S608
        "source_field, canonical_observed_value, policy_version, precedence, parsed_record_id, "
        f"evidence_sha256 FROM {table} WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()
    loaded: list[_EvidenceRow] = []
    for row in rows:
        owner = (
            canonical_anchor_cik_padded(_integer(row["owner"], f"{table}.cik_numeric"))
            if entity_side
            else _text(row["owner"], f"{table}.accession_plain")
        )
        loaded.append(
            _EvidenceRow(
                owner=owner,
                classification_dimension=_text(row["classification_dimension"], table),
                evidence_role=_text(row["evidence_role"], table),
                source_field=_text(row["source_field"], table),
                canonical_observed_value=_optional_text(row["canonical_observed_value"], table),
                policy_version=_text(row["policy_version"], table),
                precedence=_integer(row["precedence"], table),
                parsed_record_id=_optional_text(row["parsed_record_id"], table),
                evidence_sha256=_text(row["evidence_sha256"], table),
            )
        )
    return tuple(loaded)


def _fetch_reasons(
    connection: sqlite3.Connection, snapshot_id: str, *, entity_side: bool
) -> tuple[_ReasonRow, ...]:
    table = "pilot_candidate_entity_reasons" if entity_side else "pilot_candidate_accession_reasons"
    owner_column = "cik_numeric" if entity_side else "accession_plain"
    rows = connection.execute(
        f"SELECT {owner_column} AS owner, reason_scope, reason_code "  # noqa: S608
        f"FROM {table} WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()
    loaded: list[_ReasonRow] = []
    for row in rows:
        owner = (
            canonical_anchor_cik_padded(_integer(row["owner"], f"{table}.cik_numeric"))
            if entity_side
            else _text(row["owner"], f"{table}.accession_plain")
        )
        loaded.append(
            _ReasonRow(
                owner=owner,
                reason_scope=_text(row["reason_scope"], table),
                reason_code=_text(row["reason_code"], table),
            )
        )
    return tuple(loaded)


def _require_supported_identity_storage(
    accession_evidence: Sequence[_EvidenceRow],
    entity_reasons: Sequence[_ReasonRow],
    accession_reasons: Sequence[_ReasonRow],
) -> None:
    """Decision 019 section 8.1.1's frozen identity storage scope.

    An unsupported row invalidates the snapshot for Stage S5 and is reported; it is
    never skipped, filtered, deduplicated, or ignored.
    """
    for row in accession_evidence:
        if row.classification_dimension == _IDENTITY_DIMENSION:
            message = (
                f"accession {row.owner}: identity-dimension accession evidence is unsupported at "
                "Stage S5"
            )
            raise _fail(message)
    for reason in entity_reasons:
        if reason.reason_scope == _IDENTITY_SCOPE:
            message = f"entity {reason.owner}: identity-scope entity reasons are unsupported"
            raise _fail(message)
    for reason in accession_reasons:
        if reason.reason_scope == _IDENTITY_SCOPE:
            message = f"accession {reason.owner}: identity-scope accession reasons are unsupported"
            raise _fail(message)


def load_frozen_joint_candidates(
    connection: sqlite3.Connection, snapshot_id: str
) -> FrozenJointCandidateSet:
    """Reconstruct the accepted S5.1 joint inputs from one frozen candidate snapshot.

    Performs no write. The entity side reuses the accepted S4.2 loader unchanged, so
    snapshot state, the three candidate policy versions, the declared entity count,
    canonical CIK rendering, and the stored entity tie-break hash are validated exactly
    as Stage S4 validates them. The accession side adds the declared accession count,
    canonical dashed/plain agreement, the Decision 018 section 5.2 tie-break hash, the
    canonical anchor CIK, and every Decision 019 mapping and fail-closed condition.

    Raises:
        GateFailureError: any fail-closed condition, always before a solver is invoked.
    """
    entity_set = load_frozen_entity_candidates(connection, snapshot_id)

    snapshot_row = connection.execute(
        "SELECT accession_count FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    declared_accessions = _integer(
        snapshot_row["accession_count"], "pilot_candidate_snapshots.accession_count"
    )

    rows = tuple(
        _accession_row(row)
        for row in connection.execute(
            f"SELECT {', '.join(_CANDIDATE_ACCESSION_COLUMNS)} "  # noqa: S608 -- fixed allowlist
            "FROM pilot_candidate_accessions WHERE snapshot_id = ? ORDER BY accession_plain",
            (snapshot_id,),
        ).fetchall()
    )
    if len(rows) != declared_accessions:
        message = (
            f"pilot candidate snapshot {snapshot_id!r} declares accession_count "
            f"{declared_accessions}, but {len(rows)} pilot_candidate_accessions rows exist"
        )
        raise _fail(message)

    registrants = _fetch_registrants(connection, snapshot_id)
    entity_evidence = _fetch_evidence(connection, snapshot_id, entity_side=True)
    accession_evidence = _fetch_evidence(connection, snapshot_id, entity_side=False)
    entity_reasons = _fetch_reasons(connection, snapshot_id, entity_side=True)
    accession_reasons = _fetch_reasons(connection, snapshot_id, entity_side=False)
    _require_supported_identity_storage(accession_evidence, entity_reasons, accession_reasons)

    scopes_by_accession: dict[str, dict[str, set[str]]] = {}
    reason_codes_by_accession: dict[str, set[str]] = {}
    for reason in accession_reasons:
        by_scope = scopes_by_accession.setdefault(reason.owner, {})
        by_scope.setdefault(reason.reason_scope, set()).add(reason.reason_code)
        reason_codes_by_accession.setdefault(reason.owner, set()).add(reason.reason_code)

    rows_by_plain = {row.accession_plain: row for row in rows}
    for row in rows:
        _validate_accession_identity(row)
        _validate_linkage_representation(
            row, frozenset(reason_codes_by_accession.get(row.accession_plain, ()))
        )

    accessions: list[AccessionCandidate] = []
    accession_content: list[dict[str, object]] = []
    for row in rows:
        scopes: Mapping[str, frozenset[str]] = {
            scope: frozenset(codes)
            for scope, codes in scopes_by_accession.get(row.accession_plain, {}).items()
        }
        applicability, cohort_level, official_cohort = _cohort_mapping(row, scopes)
        linkage_level, parent_dashed = _amendment_linkage_mapping(row, rows_by_plain)
        accession_registrants = registrants.get(row.accession_plain, ())
        multi_level = _multi_registrant_mapping(row, accession_registrants, scopes)
        candidate = AccessionCandidate(
            accession_plain=row.accession_plain,
            accession_number_dashed=row.accession_number_dashed,
            anchor_cik_numeric=row.anchor_cik_numeric,
            form_type=row.form_type,
            is_amendment=row.is_amendment,
            official_filing_date=row.official_filing_date,
            report_date=row.report_date,
            cohort_applicability="pre_study" if applicability == "pre_study" else "applies",
            provisional_official_cohort=official_cohort,
            filing_date_evidence_level=row.filing_date_evidence_level,
            cohort_evidence_level=cohort_level,
            xbrl_evidence_level=row.xbrl_evidence_level,
            amendment_purpose_evidence_level=(
                row.amendment_purpose_evidence_level if row.is_amendment else NOT_APPLICABLE
            ),
            amendment_linkage_evidence_level=linkage_level,
            multi_registrant_evidence_level=multi_level,
            has_xbrl=row.has_xbrl,
            has_inline_xbrl=row.has_inline_xbrl,
            amendment_linkage_state=row.amendment_linkage_state,
            provisional_parent_accession_dashed=parent_dashed,
            amendment_purpose_category=row.amendment_purpose_category,
            amendment_purpose_quota_eligible=row.amendment_purpose_quota_eligible,
            base_eligible=row.base_eligible,
            stress_eligible=row.stress_eligible,
            support_eligible=row.support_eligible,
            control_eligible=row.control_eligible,
            multi_registrant=row.multi_registrant,
        )
        accessions.append(candidate)
        accession_content.append(
            _accession_content_record(
                row, candidate, _registrant_content_sha256(accession_registrants)
            )
        )

    identity_by_cik: dict[str, list[_EvidenceRow]] = {}
    for evidence in entity_evidence:
        if evidence.classification_dimension == _IDENTITY_DIMENSION:
            identity_by_cik.setdefault(evidence.owner, []).append(evidence)
    entities = tuple(
        EntityCandidate(
            candidate=candidate,
            name_change=_name_change_evidence(
                candidate.cik_padded, identity_by_cik.get(candidate.cik_padded, ())
            ),
        )
        for candidate in entity_set.candidates
    )

    return FrozenJointCandidateSet(
        snapshot_id=snapshot_id,
        candidate_snapshot_sha256=entity_set.candidate_snapshot_sha256,
        entity_count=entity_set.entity_count,
        accession_count=declared_accessions,
        entities=entities,
        accessions=tuple(accessions),
        entity_content_sha256=_entity_content_sha256(entities, entity_evidence, entity_reasons),
        accession_content_sha256=_accession_content_sha256(
            accession_content, accession_evidence, accession_reasons
        ),
    )


def _fetch_registrants(
    connection: sqlite3.Connection, snapshot_id: str
) -> Mapping[str, tuple[_RegistrantRow, ...]]:
    rows = connection.execute(
        "SELECT accession_plain, registrant_cik_numeric, registrant_cik_padded, role, is_anchor, "
        "evidence_level FROM pilot_candidate_accession_registrants WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchall()
    grouped: dict[str, list[_RegistrantRow]] = {}
    table = "pilot_candidate_accession_registrants"
    for row in rows:
        plain = _text(row["accession_plain"], f"{table}.accession_plain")
        grouped.setdefault(plain, []).append(
            _RegistrantRow(
                accession_plain=plain,
                registrant_cik_numeric=_integer(row["registrant_cik_numeric"], table),
                registrant_cik_padded=_text(row["registrant_cik_padded"], table),
                role=_text(row["role"], table),
                is_anchor=_flag(row["is_anchor"], table),
                evidence_level=_text(row["evidence_level"], table),
            )
        )
    return {plain: tuple(entries) for plain, entries in grouped.items()}


def _validate_accession_identity(row: _AccessionRow) -> None:
    """Decision 018 section 5.3's two fail-closed loader obligations, per candidate row."""
    where = f"accession {row.accession_plain}"
    if _DASHED_ACCESSION_PATTERN.match(row.accession_number_dashed) is None:
        message = (
            f"{where}: stored accession_number_dashed {row.accession_number_dashed!r} is not the "
            "canonical dashed form"
        )
        raise _fail(message)
    if _dashed_from_plain(row.accession_plain, where) != row.accession_number_dashed:
        message = (
            f"{where}: stored accession_plain and accession_number_dashed "
            f"{row.accession_number_dashed!r} are inconsistent"
        )
        raise _fail(message)
    anchor_padded = canonical_anchor_cik_padded(row.anchor_cik_numeric)
    expected = accession_selection_rank(
        anchor_padded, row.accession_number_dashed, PILOT_SELECTION_SEED
    )
    if row.accession_tie_break_sha256 != expected:
        message = (
            f"{where}: stored accession_tie_break_sha256 does not match "
            "SHA256(selection_seed | anchor_cik_padded | accession_number_dashed)"
        )
        raise _fail(message)


# --------------------------------------------------------------------------
# Deterministic run identity (Decision 018 section 26; Decision 019 section 10)
# --------------------------------------------------------------------------


def _accession_content_record(
    row: _AccessionRow, candidate: AccessionCandidate, registrant_sha256: str
) -> dict[str, object]:
    """The material normalized content of one candidate accession.

    Carries the stored fields the Decision 019 mappings read -- including
    ``acceptance_audit_date`` for **every** candidate accession, whether or not a
    section 5.9 check reads that particular row -- alongside the derived pure-input
    values and the per-accession registrant digest paired with the accession identity.

    **Where a mapping derives a value rather than carrying the stored one, both are
    recorded**, exactly as the linkage pair already is. Decision 018 section 3.4 makes
    the cohort dimension structurally inapplicable on a valid pre-study accession and
    the amendment-purpose dimension structurally inapplicable on an original, so those
    two derived values are ``not_applicable`` regardless of what the frozen row stores.
    Recording the stored value beside the derived one keeps the accession-candidate
    content **complete**, so two frozen snapshots differing only in one of those stored
    columns cannot produce the same ``selection_input_sha256``. Neither stored value
    reaches the pure S5.1 input, changes an evidence penalty, or affects a quota.
    """
    return {
        "accession_plain": row.accession_plain,
        "accession_number_dashed": row.accession_number_dashed,
        "anchor_cik_padded": candidate.anchor_cik_padded,
        "form_type": row.form_type,
        "is_amendment": row.is_amendment,
        "official_filing_date": row.official_filing_date,
        "report_date": row.report_date,
        "acceptance_audit_date": row.acceptance_audit_date,
        "cohort_applicability": candidate.cohort_applicability,
        "provisional_official_cohort": candidate.provisional_official_cohort,
        "cohort_ambiguous": row.cohort_ambiguous,
        "filing_date_evidence_level": candidate.filing_date_evidence_level,
        "cohort_evidence_level": candidate.cohort_evidence_level,
        "stored_cohort_evidence_level": row.cohort_evidence_level,
        "xbrl_evidence_level": candidate.xbrl_evidence_level,
        "amendment_purpose_evidence_level": candidate.amendment_purpose_evidence_level,
        "stored_amendment_purpose_evidence_level": row.amendment_purpose_evidence_level,
        "amendment_linkage_evidence_level": candidate.amendment_linkage_evidence_level,
        "multi_registrant_evidence_level": candidate.multi_registrant_evidence_level,
        "has_xbrl": row.has_xbrl,
        "has_inline_xbrl": row.has_inline_xbrl,
        "stored_amendment_linkage_state": row.amendment_linkage_state,
        "stored_provisional_parent_accession": row.provisional_parent_accession,
        "provisional_parent_accession_dashed": candidate.provisional_parent_accession_dashed,
        "amendment_purpose_category": row.amendment_purpose_category,
        "amendment_purpose_quota_eligible": row.amendment_purpose_quota_eligible,
        "base_eligible": row.base_eligible,
        "stress_eligible": row.stress_eligible,
        "support_eligible": row.support_eligible,
        "control_eligible": row.control_eligible,
        "multi_registrant": row.multi_registrant,
        "registrant_content_sha256": registrant_sha256,
    }


def _evidence_content_sha256(table: str, rows: Sequence[_EvidenceRow]) -> str:
    records = (
        {
            "owner": row.owner,
            "classification_dimension": row.classification_dimension,
            "evidence_role": row.evidence_role,
            "source_field": row.source_field,
            "canonical_observed_value": row.canonical_observed_value,
            "policy_version": row.policy_version,
            "precedence": row.precedence,
            "parsed_record_id": row.parsed_record_id,
            "evidence_sha256": row.evidence_sha256,
        }
        for row in rows
    )
    return hash_table(table, _EVIDENCE_CONTENT_COLUMNS, records).normalized_content_sha256


def _reason_content_sha256(table: str, rows: Sequence[_ReasonRow]) -> str:
    records = (
        {"owner": row.owner, "reason_scope": row.reason_scope, "reason_code": row.reason_code}
        for row in rows
    )
    return hash_table(table, _REASON_CONTENT_COLUMNS, records).normalized_content_sha256


def _entity_content_sha256(
    entities: Sequence[EntityCandidate],
    evidence: Sequence[_EvidenceRow],
    reasons: Sequence[_ReasonRow],
) -> str:
    """The complete normalized frozen entity-candidate content.

    ``filing_time_name`` is excluded: names never enter a hash or an ordering decision
    (accepted S4.2 precedent). Every timestamp and free-text ``detail`` column is
    excluded (Decision 016 section 8).
    """
    records = (
        {
            "cik_padded": entry.cik_padded,
            "category": entry.candidate.category,
            "primary_universe_eligible": entry.candidate.primary_universe_eligible,
            "engineering_only_stress": entry.candidate.engineering_only_stress,
            "size_stratum": entry.candidate.size_stratum,
            "size_evidence_level": entry.candidate.size_evidence_level,
            "industry_group": entry.candidate.industry_group,
            "industry_evidence_level": entry.candidate.industry_evidence_level,
            "industry_quota_eligible": entry.candidate.industry_quota_eligible,
            "history_class": entry.candidate.history_class,
            "history_evidence_level": entry.candidate.history_evidence_level,
            "currently_inactive": entry.candidate.currently_inactive,
            "control_kind": entry.candidate.control_kind,
            "evidence_penalty": entry.candidate.evidence_penalty,
            "name_change_has_identity_evidence": entry.name_change.has_identity_evidence,
            "name_change_evidence_role": entry.name_change.evidence_role,
            "name_change_evidence_level": entry.name_change.evidence_level,
            "name_change_former_name_record_parseable": (
                entry.name_change.former_name_record_parseable
            ),
            "name_change_has_prior_current_or_from_to": (
                entry.name_change.has_prior_current_or_from_to
            ),
            "name_change_ticker_change_claimed": entry.name_change.ticker_change_claimed,
        }
        for entry in entities
    )
    combined = {
        "candidates": hash_table(
            _ENTITY_CONTENT_TABLE, _ENTITY_CONTENT_COLUMNS, records
        ).normalized_content_sha256,
        "evidence": _evidence_content_sha256(_ENTITY_EVIDENCE_CONTENT_TABLE, evidence),
        "reasons": _reason_content_sha256(_ENTITY_REASON_CONTENT_TABLE, reasons),
    }
    return hash_table(
        "pilot_joint_selection_entity_content", tuple(sorted(combined)), [combined]
    ).normalized_content_sha256


def _accession_content_sha256(
    records: Sequence[Mapping[str, object]],
    evidence: Sequence[_EvidenceRow],
    reasons: Sequence[_ReasonRow],
) -> str:
    """The complete normalized frozen accession-candidate content."""
    combined = {
        "candidates": hash_table(
            _ACCESSION_CONTENT_TABLE, _ACCESSION_CONTENT_COLUMNS, records
        ).normalized_content_sha256,
        "evidence": _evidence_content_sha256(_ACCESSION_EVIDENCE_CONTENT_TABLE, evidence),
        "reasons": _reason_content_sha256(_ACCESSION_REASON_CONTENT_TABLE, reasons),
    }
    return hash_table(
        "pilot_joint_selection_accession_content", tuple(sorted(combined)), [combined]
    ).normalized_content_sha256


def build_joint_selection_run_identity(
    candidate_set: FrozenJointCandidateSet,
    *,
    node_limit: int,
    selection_seed: str = PILOT_SELECTION_SEED,
    selector_policy_version: str = PILOT_JOINT_SELECTOR_POLICY_VERSION,
    quota_policy_version: str = PILOT_QUOTA_POLICY_VERSION,
) -> JointSelectionRunIdentity:
    """Derive the deterministic input hash and S5 joint ``selection_run_id``.

    Includes the joint selector policy version, the selection seed, the required
    positive ``node_limit`` (Decision 018 section 17), the complete normalized frozen
    entity- and accession-candidate content, the frozen quota-policy input, the frozen
    S5 objective-term order, the snapshot identity, and this module's input-schema
    version.

    Excludes, without exception: every timestamp and wall-clock read, process identity,
    filesystem paths, database and insertion row order, Python object representations,
    mutable lifecycle state, the S4 entity-only selection result and its
    ``selection_run_id``, and any outcome or future information. No clock is read.

    Neither hash is the M2.3 manifest hash (Stage S6).
    """
    if isinstance(node_limit, bool) or not isinstance(node_limit, int) or node_limit < 1:
        message = f"node_limit must be a positive integer, got {node_limit!r}"
        raise _fail(message)

    input_fields: dict[str, object] = {
        "schema": ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
        "snapshot_id": candidate_set.snapshot_id,
        "candidate_snapshot_sha256": candidate_set.candidate_snapshot_sha256,
        "selection_seed": selection_seed,
        "selector_policy_version": selector_policy_version,
        "quota_policy_version": quota_policy_version,
        "node_limit": node_limit,
        "objective_term_order": _OBJECTIVE_TERM_ORDER,
        "entity_content_sha256": candidate_set.entity_content_sha256,
        "accession_content_sha256": candidate_set.accession_content_sha256,
    }
    selection_input_sha256 = hash_table(
        "pilot_joint_selection_input", tuple(sorted(input_fields)), [input_fields]
    ).normalized_content_sha256

    run_identity_fields: dict[str, object] = {
        "schema": ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
        "snapshot_id": candidate_set.snapshot_id,
        "selection_input_sha256": selection_input_sha256,
    }
    selection_run_id = hash_table(
        "pilot_joint_selection_run_identity",
        tuple(sorted(run_identity_fields)),
        [run_identity_fields],
    ).normalized_content_sha256

    return JointSelectionRunIdentity(
        snapshot_id=candidate_set.snapshot_id,
        selection_seed=selection_seed,
        selector_policy_version=selector_policy_version,
        quota_policy_version=quota_policy_version,
        node_limit=node_limit,
        selection_input_sha256=selection_input_sha256,
        selection_run_id=selection_run_id,
    )


# --------------------------------------------------------------------------
# Derivation shared by execution and reconstruction
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Derived:
    """One deterministic derivation of the pure result and its run identity."""

    candidate_set: FrozenJointCandidateSet
    identity: JointSelectionRunIdentity
    result: JointSelectionResult


def _derive(
    connection: sqlite3.Connection,
    snapshot_id: str,
    *,
    node_limit: int,
    selection_seed: str,
    selector_policy_version: str,
    quota_policy_version: str,
) -> _Derived:
    candidate_set = load_frozen_joint_candidates(connection, snapshot_id)
    identity = build_joint_selection_run_identity(
        candidate_set,
        node_limit=node_limit,
        selection_seed=selection_seed,
        selector_policy_version=selector_policy_version,
        quota_policy_version=quota_policy_version,
    )
    result = solve_joint_selection(
        candidate_set.entities,
        candidate_set.accessions,
        node_limit=node_limit,
        selection_seed=selection_seed,
    )
    return _Derived(candidate_set=candidate_set, identity=identity, result=result)


# --------------------------------------------------------------------------
# Persistence
# --------------------------------------------------------------------------


def _quota_result_id(selection_run_id: str, dimension: str, key: str) -> str:
    payload = f"{selection_run_id}|{dimension}|{key}".encode()
    return hashlib.sha256(payload).hexdigest()


def _persist_feasible_result(
    c: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    selection_seed: str,
    result: JointSelectionResult,
    recorded_at_utc: str,
) -> None:
    """Persist one complete feasible joint result into the migration-0009 tables.

    Selected entities are written before selected accessions so that every accession's
    composite ``(selection_run_id, snapshot_id, anchor_cik_numeric)`` foreign key
    resolves. ``selected_order`` is persisted exactly as the pure core computed it and
    is never reordered here (Decision 018 section 4).
    """
    for order, candidate in enumerate(result.selected_entities, start=1):
        c.execute(
            "INSERT INTO pilot_selected_entities "
            "(selection_run_id, snapshot_id, cik_numeric, selected_order, entity_hash_sha256, "
            "entity_role, candidate_category, size_stratum, industry_family, history_class, "
            "control_kind, recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                selection_run_id,
                snapshot_id,
                int(candidate.cik_padded),
                order,
                selection_rank(candidate.cik_padded, selection_seed),
                "operating" if candidate.category == "operating" else "control",
                candidate.category,
                candidate.size_stratum,
                candidate.industry_group,
                candidate.history_class,
                candidate.control_kind,
                recorded_at_utc,
            ),
        )
    for selected in result.selected_accessions:
        c.execute(
            "INSERT INTO pilot_selected_accessions "
            "(selection_run_id, snapshot_id, accession_plain, anchor_cik_numeric, selected_order, "
            "accession_hash_sha256, accession_role, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                selection_run_id,
                snapshot_id,
                selected.accession_plain,
                int(selected.anchor_cik_padded),
                selected.selected_order,
                selected.accession_tie_break_sha256,
                selected.accession_role,
                recorded_at_utc,
            ),
        )
    for diagnostic in result.entity_quota_results:
        _insert_quota_result(
            c,
            selection_run_id=selection_run_id,
            snapshot_id=snapshot_id,
            dimension=diagnostic.dimension,
            key=diagnostic.key,
            comparison_operator=diagnostic.comparison_operator,
            required_count=diagnostic.required_count,
            achieved_count=diagnostic.achieved_count,
            eligible_pool_count=diagnostic.available_eligible_count,
            excluded_pool_count=diagnostic.excluded_pool_count,
            # The entity-side diagnostic carries no evidence state of its own; 'provisional'
            # here means the frozen classification is provisionally accepted, exactly as the
            # accepted S4.2 persistence records it (Decision 017 section 3).
            evidence_state=_PROVISIONAL,
            quota_result=diagnostic.status,
            binding_constraint=diagnostic.binding_constraint,
            recorded_at_utc=recorded_at_utc,
        )
    # ``accession_quota_results`` already contains the single Decision 018 section 14
    # deferred-quota row, so ``deferred_quota_result`` is deliberately not written again:
    # UNIQUE (selection_run_id, snapshot_id, quota_dimension, quota_key) permits one row.
    for accession_diagnostic in result.accession_quota_results:
        _insert_quota_result(
            c,
            selection_run_id=selection_run_id,
            snapshot_id=snapshot_id,
            dimension=accession_diagnostic.dimension,
            key=accession_diagnostic.key,
            comparison_operator=accession_diagnostic.comparison_operator,
            required_count=accession_diagnostic.required_count,
            achieved_count=accession_diagnostic.achieved_count,
            eligible_pool_count=accession_diagnostic.available_eligible_count,
            excluded_pool_count=accession_diagnostic.excluded_pool_count,
            evidence_state=accession_diagnostic.evidence_state,
            quota_result=accession_diagnostic.status,
            binding_constraint=accession_diagnostic.binding_constraint,
            recorded_at_utc=recorded_at_utc,
        )


def _insert_quota_result(
    c: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    dimension: str,
    key: str,
    comparison_operator: str,
    required_count: int,
    achieved_count: int,
    eligible_pool_count: int,
    excluded_pool_count: int,
    evidence_state: str,
    quota_result: str,
    binding_constraint: bool,
    recorded_at_utc: str,
) -> None:
    c.execute(
        "INSERT INTO pilot_quota_results "
        "(quota_result_id, selection_run_id, snapshot_id, quota_dimension, quota_key, "
        "comparison_operator, required_count, achieved_count, eligible_pool_count, "
        "excluded_pool_count, evidence_state, quota_result, binding_constraint, recorded_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            _quota_result_id(selection_run_id, dimension, key),
            selection_run_id,
            snapshot_id,
            dimension,
            key,
            comparison_operator,
            required_count,
            achieved_count,
            eligible_pool_count,
            excluded_pool_count,
            evidence_state,
            quota_result,
            1 if binding_constraint else 0,
            recorded_at_utc,
        ),
    )


def execute_and_persist_joint_selection(
    connection: sqlite3.Connection,
    snapshot_id: str,
    *,
    node_limit: int,
    selection_seed: str = PILOT_SELECTION_SEED,
    selector_policy_version: str = PILOT_JOINT_SELECTOR_POLICY_VERSION,
    quota_policy_version: str = PILOT_QUOTA_POLICY_VERSION,
    occurred_at_utc: str,
    event_id: str,
) -> PersistedJointSelectionResult:
    """Run the accepted S5.1 solver against one frozen snapshot and persist the result.

    The S5 joint run receives its own content-derived ``selection_run_id``, distinct
    from the S4 entity-only draft's. **The S4 draft is never read, mutated, promoted,
    deleted, or used as an input**: nothing in this module queries it, and its
    permanently-``running`` row is expected residue (Decision 018 sections 6 and 27).

    Idempotent: a run with the same content-derived identity whose stored
    ``selection_input_sha256`` agrees is fully reconstructed and returned rather than
    rewritten. A same-ID row whose stored content differs is rejected, never
    overwritten, and a same-ID row in ``planned``, ``running``, or ``failed`` state
    raises :class:`~disclosure_drift.errors.GateFailureError` -- there is no retry
    entry point, and no new identity is manufactured to bypass the gate (section 18).

    **Reuse requires every stored identity field to agree, not the digest alone.** The
    reconstruction below compares the persisted run's snapshot identity, seed, selector
    and quota policy versions, node limit, input digest, and run ID against the identity
    derived here, so this path and :func:`reconstruct_persisted_joint_selection` fail
    closed on exactly the same stored corruption.

    Everything durable happens inside one explicit transaction: the lifecycle row, its
    single ``planned -> running`` event, and every result row commit together or not at
    all. A non-feasible run -- proven infeasible or node-limit exhausted -- persists no
    selected row and no partial objective. The pure solve itself is in-memory and runs
    before the transaction opens.

    ``occurred_at_utc`` and ``event_id`` are audit metadata only; neither enters
    ``selection_input_sha256`` or ``selection_run_id``.
    """
    derived = _derive(
        connection,
        snapshot_id,
        node_limit=node_limit,
        selection_seed=selection_seed,
        selector_policy_version=selector_policy_version,
        quota_policy_version=quota_policy_version,
    )
    identity = derived.identity

    existing = connection.execute(
        "SELECT run_state, selection_input_sha256 FROM pilot_selection_runs "
        "WHERE selection_run_id = ?",
        (identity.selection_run_id,),
    ).fetchone()
    if existing is not None:
        stored_input = _text(existing["selection_input_sha256"], "selection_input_sha256")
        if stored_input != identity.selection_input_sha256:
            message = (
                f"selection_run_id {identity.selection_run_id!r} already exists with a different "
                "stored selection_input_sha256; refusing to overwrite"
            )
            raise _fail(message)
        run_state = _text(existing["run_state"], "run_state")
        if run_state not in _TERMINAL_RECONSTRUCTABLE_STATES:
            message = (
                f"selection_run_id {identity.selection_run_id!r} already exists in state "
                f"{run_state!r}; Decision 018 section 18 makes this a gate failure, and no retry "
                "entry point or replacement identity is authorized"
            )
            raise _fail(message)
        return _reconstruct(connection, identity.selection_run_id, derived)

    result = derived.result
    feasible = result.status == "feasible"
    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_runs "
            "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
            "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
            "started_at_utc) VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)",
            (
                identity.selection_run_id,
                snapshot_id,
                selection_seed,
                selector_policy_version,
                quota_policy_version,
                node_limit,
                identity.selection_input_sha256,
                occurred_at_utc,
            ),
        )
        c.execute(
            "INSERT INTO pilot_selection_run_events "
            "(event_id, selection_run_id, snapshot_id, from_state, to_state, attempt_number, "
            "occurred_at_utc) VALUES (?, ?, ?, 'planned', 'running', 1, ?)",
            (event_id, identity.selection_run_id, snapshot_id, occurred_at_utc),
        )
        c.execute(
            "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
            (identity.selection_run_id,),
        )

        if feasible:
            _persist_feasible_result(
                c,
                selection_run_id=identity.selection_run_id,
                snapshot_id=snapshot_id,
                selection_seed=selection_seed,
                result=result,
                recorded_at_utc=occurred_at_utc,
            )
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = 'feasible', "
                "selected_entity_count = ?, selected_accession_count = ?, "
                "expanded_node_count = ?, node_limit_exhausted = 0, finished_at_utc = ? "
                "WHERE selection_run_id = ?",
                (
                    len(result.selected_entities),
                    len(result.selected_accessions),
                    result.expanded_node_count,
                    occurred_at_utc,
                    identity.selection_run_id,
                ),
            )
        else:
            # No further pilot_selection_run_events row is recorded: UNIQUE
            # (selection_run_id, attempt_number) permits exactly one event per attempt,
            # and attempt 1's event already recorded planned -> running above.
            reason_code = (
                _PILOT_SELECTION_INFEASIBLE
                if result.status == "infeasible"
                else _PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN
            )
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = ?, selected_entity_count = 0, "
                "selected_accession_count = 0, expanded_node_count = ?, node_limit_exhausted = ?, "
                "failure_reason_code = ?, finished_at_utc = ? WHERE selection_run_id = ?",
                (
                    result.status,
                    result.expanded_node_count,
                    1 if result.node_limit_exhausted else 0,
                    reason_code,
                    occurred_at_utc,
                    identity.selection_run_id,
                ),
            )

    return _reconstruct(connection, identity.selection_run_id, derived)


# --------------------------------------------------------------------------
# Reconstruction
# --------------------------------------------------------------------------


def reconstruct_persisted_joint_selection(
    connection: sqlite3.Connection, selection_run_id: str
) -> PersistedJointSelectionResult:
    """Reconstruct one persisted S5 joint run, failing closed on any disagreement.

    The accepted pure result is reproduced as a
    :class:`~disclosure_drift.sec.accession_selector.JointSelectionResult` by
    re-deriving it deterministically from the same frozen snapshot under the run's own
    recorded seed, policy versions, and node limit -- the property Decision 013 section
    5 guarantees -- and every persisted component is then validated against it.
    Persisted corruption is never silently normalized: a corrupted, incomplete,
    contradictory, or policy-mismatched persisted run raises
    :class:`~disclosure_drift.errors.GateFailureError`.

    The comparison is independent of SQLite retrieval order.
    """
    return _reconstruct(connection, selection_run_id, None)


def _stored_run_identity(run_row: sqlite3.Row, selection_run_id: str) -> JointSelectionRunIdentity:
    """The run's own persisted identity-driving values, narrowed into the identity record.

    Every column read here is one the content-derived identity is built from, so a
    persisted run can be compared against a derived identity field by field rather than
    only through the input digest. ``selection_run_id`` is the lookup key itself, which is
    what makes a stored row that no longer derives its own primary key detectable.
    """
    return JointSelectionRunIdentity(
        snapshot_id=_text(run_row["snapshot_id"], "snapshot_id"),
        selection_seed=_text(run_row["selection_seed"], "selection_seed"),
        selector_policy_version=_text(
            run_row["selector_policy_version"], "selector_policy_version"
        ),
        quota_policy_version=_text(run_row["quota_policy_version"], "quota_policy_version"),
        node_limit=_integer(run_row["search_node_limit"], "search_node_limit"),
        selection_input_sha256=_text(run_row["selection_input_sha256"], "selection_input_sha256"),
        selection_run_id=selection_run_id,
    )


def _require_stored_identity_matches(
    stored: JointSelectionRunIdentity, derived: JointSelectionRunIdentity
) -> None:
    """Fail closed unless **every** persisted identity field equals the derived one.

    Decision 018 section 18 makes a same-ID terminal run idempotently reusable only when
    the values it recorded are the ones that produced it. Both public entry points reach
    this single check, so neither carries its own copy:

    * :func:`reconstruct_persisted_joint_selection` re-derives from the stored columns, so
      the snapshot identity, seed, two policy versions, and node limit agree by
      construction there and a disagreement can surface only in the input digest or the
      run ID -- exactly the behaviour that path already had;
    * the idempotent branch of :func:`execute_and_persist_joint_selection` supplies a
      caller-derived identity, so the scalars the digest is built from are compared here
      too, rather than being read into the returned wrapper unexamined.

    The comparison walks :class:`JointSelectionRunIdentity`'s own fields, so an identity
    field added later is covered without editing this function. A disagreement is
    reported and refused: no stored value is replaced by the supplied one, no persisted
    row is overwritten, and no replacement identity is manufactured.
    """
    disagreements = [
        f"{entry.name} (stored {getattr(stored, entry.name)!r}, "
        f"derived {getattr(derived, entry.name)!r})"
        for entry in fields(JointSelectionRunIdentity)
        if getattr(stored, entry.name) != getattr(derived, entry.name)
    ]
    if not disagreements:
        return
    message = (
        f"selection_run_id {stored.selection_run_id!r} has a stored "
        f"{', '.join(disagreements)} that does not match the identity re-derived from its own "
        "frozen snapshot and recorded policy; the persisted run is refused rather than reused, "
        "rewritten, or reissued under a new identity"
    )
    raise _fail(message)


def _reconstruct(
    connection: sqlite3.Connection, selection_run_id: str, derived: _Derived | None
) -> PersistedJointSelectionResult:
    run_row = connection.execute(
        "SELECT selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
        "quota_policy_version, search_node_limit, run_state, expanded_node_count, "
        "node_limit_exhausted, selected_entity_count, selected_accession_count, "
        "selection_input_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
        (selection_run_id,),
    ).fetchone()
    if run_row is None:
        message = f"no pilot selection run exists for selection_run_id {selection_run_id!r}"
        raise _fail(message)

    snapshot_id = _text(run_row["snapshot_id"], "snapshot_id")
    run_state = _text(run_row["run_state"], "run_state")
    if run_state not in _TERMINAL_RECONSTRUCTABLE_STATES:
        message = (
            f"selection_run_id {selection_run_id!r} is in state {run_state!r} and carries no "
            "complete persisted result to reconstruct"
        )
        raise _fail(message)

    stored_identity = _stored_run_identity(run_row, selection_run_id)
    if derived is None:
        # Historical reconstruction always re-executes under the run's own recorded
        # inputs, never under this process's current defaults.
        derived = _derive(
            connection,
            snapshot_id,
            node_limit=stored_identity.node_limit,
            selection_seed=stored_identity.selection_seed,
            selector_policy_version=stored_identity.selector_policy_version,
            quota_policy_version=stored_identity.quota_policy_version,
        )
    identity = derived.identity
    result = derived.result

    _require_stored_identity_matches(stored_identity, identity)

    if run_state != result.status:
        message = (
            f"selection_run_id {selection_run_id!r} is persisted as {run_state!r} but its frozen "
            f"inputs deterministically yield {result.status!r}"
        )
        raise _fail(message)

    expanded = _integer(run_row["expanded_node_count"], "expanded_node_count")
    exhausted = _flag(run_row["node_limit_exhausted"], "node_limit_exhausted")
    if expanded != result.expanded_node_count or exhausted != result.node_limit_exhausted:
        message = (
            f"selection_run_id {selection_run_id!r} persists expanded_node_count {expanded} / "
            f"node_limit_exhausted {exhausted}, but its inputs yield "
            f"{result.expanded_node_count} / {result.node_limit_exhausted}"
        )
        raise _fail(message)

    entity_count = _integer(run_row["selected_entity_count"], "selected_entity_count")
    accession_count = _integer(run_row["selected_accession_count"], "selected_accession_count")
    if entity_count != len(result.selected_entities) or accession_count != len(
        result.selected_accessions
    ):
        message = (
            f"selection_run_id {selection_run_id!r} declares {entity_count} selected entities and "
            f"{accession_count} selected accessions, but its inputs yield "
            f"{len(result.selected_entities)} and {len(result.selected_accessions)}"
        )
        raise _fail(message)

    _validate_persisted_entities(
        connection, selection_run_id, snapshot_id, stored_identity.selection_seed, result
    )
    _validate_persisted_accessions(connection, selection_run_id, snapshot_id, result)
    _validate_persisted_quota_results(connection, selection_run_id, snapshot_id, result)

    # Every field below is the value the run itself persisted. The identity comparison
    # above has already proved each one equals the derived value, so the wrapper can
    # never report a supplied value in place of a stored one.
    return PersistedJointSelectionResult(
        selection_run_id=selection_run_id,
        snapshot_id=snapshot_id,
        candidate_snapshot_sha256=derived.candidate_set.candidate_snapshot_sha256,
        run_state=run_state,
        selection_seed=stored_identity.selection_seed,
        selector_policy_version=stored_identity.selector_policy_version,
        quota_policy_version=stored_identity.quota_policy_version,
        node_limit=stored_identity.node_limit,
        expanded_node_count=expanded,
        node_limit_exhausted=exhausted,
        selection_input_sha256=stored_identity.selection_input_sha256,
        selected_entity_count=entity_count,
        selected_accession_count=accession_count,
        result=result,
    )


def _validate_persisted_entities(
    connection: sqlite3.Connection,
    selection_run_id: str,
    snapshot_id: str,
    selection_seed: str,
    result: JointSelectionResult,
) -> None:
    rows = connection.execute(
        "SELECT cik_numeric, selected_order, entity_hash_sha256, entity_role, candidate_category, "
        "size_stratum, industry_family, history_class, control_kind FROM pilot_selected_entities "
        "WHERE selection_run_id = ? AND snapshot_id = ? ORDER BY selected_order",
        (selection_run_id, snapshot_id),
    ).fetchall()
    expected = result.selected_entities
    if len(rows) != len(expected):
        message = (
            f"selection_run_id {selection_run_id!r} has {len(rows)} pilot_selected_entities rows, "
            f"but its inputs yield {len(expected)}"
        )
        raise _fail(message)
    orders = [_integer(row["selected_order"], "selected_order") for row in rows]
    if orders != list(range(1, len(rows) + 1)):
        message = (
            f"selection_run_id {selection_run_id!r} entity selected_order values are not "
            f"contiguous and unique from 1: {orders!r}"
        )
        raise _fail(message)
    for row, candidate in zip(rows, expected, strict=True):
        _require_persisted_entity_row_matches(row, candidate, selection_run_id, selection_seed)


def _require_persisted_entity_row_matches(
    row: sqlite3.Row, candidate: Candidate, selection_run_id: str, selection_seed: str
) -> None:
    where = f"selection_run_id {selection_run_id!r} entity {candidate.cik_padded}"
    if canonical_anchor_cik_padded(_integer(row["cik_numeric"], "cik_numeric")) != (
        candidate.cik_padded
    ):
        message = f"{where}: a persisted selected entity does not match the derived selection"
        raise _fail(message)
    expected_role = "operating" if candidate.category == "operating" else "control"
    if _text(row["entity_role"], "entity_role") != expected_role:
        message = f"{where}: persisted entity_role does not match the derived selection"
        raise _fail(message)
    if _text(row["candidate_category"], "candidate_category") != candidate.category:
        message = f"{where}: persisted candidate_category does not match the frozen snapshot"
        raise _fail(message)
    classification = (
        _optional_text(row["size_stratum"], "size_stratum"),
        _optional_text(row["industry_family"], "industry_family"),
        _optional_text(row["history_class"], "history_class"),
        _optional_text(row["control_kind"], "control_kind"),
    )
    if classification != (
        candidate.size_stratum,
        candidate.industry_group,
        candidate.history_class,
        candidate.control_kind,
    ):
        message = f"{where}: persisted classification does not match the frozen snapshot"
        raise _fail(message)
    if _text(row["entity_hash_sha256"], "entity_hash_sha256") != selection_rank(
        candidate.cik_padded, selection_seed
    ):
        message = f"{where}: persisted entity_hash_sha256 does not match the S4.1 rank formula"
        raise _fail(message)


def _validate_persisted_accessions(
    connection: sqlite3.Connection,
    selection_run_id: str,
    snapshot_id: str,
    result: JointSelectionResult,
) -> None:
    rows = connection.execute(
        "SELECT accession_plain, anchor_cik_numeric, selected_order, accession_hash_sha256, "
        "accession_role FROM pilot_selected_accessions WHERE selection_run_id = ? "
        "AND snapshot_id = ? ORDER BY selected_order",
        (selection_run_id, snapshot_id),
    ).fetchall()
    expected = result.selected_accessions
    if len(rows) != len(expected):
        message = (
            f"selection_run_id {selection_run_id!r} has {len(rows)} pilot_selected_accessions "
            f"rows, but its inputs yield {len(expected)}"
        )
        raise _fail(message)
    orders = [_integer(row["selected_order"], "selected_order") for row in rows]
    if orders != list(range(1, len(rows) + 1)):
        message = (
            f"selection_run_id {selection_run_id!r} accession selected_order values are not "
            f"contiguous and unique from 1: {orders!r}"
        )
        raise _fail(message)
    selected_ciks = {candidate.cik_padded for candidate in result.selected_entities}
    for row, selected in zip(rows, expected, strict=True):
        where = (
            f"selection_run_id {selection_run_id!r} accession {selected.accession_number_dashed}"
        )
        anchor = canonical_anchor_cik_padded(_integer(row["anchor_cik_numeric"], "anchor"))
        persisted = (
            _text(row["accession_plain"], "accession_plain"),
            anchor,
            _text(row["accession_role"], "accession_role"),
            _text(row["accession_hash_sha256"], "accession_hash_sha256"),
        )
        if persisted != (
            selected.accession_plain,
            selected.anchor_cik_padded,
            selected.accession_role,
            selected.accession_tie_break_sha256,
        ):
            message = f"{where}: the persisted selected accession does not match the derived one"
            raise _fail(message)
        if anchor not in selected_ciks:
            message = f"{where}: its anchor CIK is not among the persisted selected entities"
            raise _fail(message)
    if result.objective is not None:
        _require_objective_vectors_match(rows, result, selection_run_id)


def _require_objective_vectors_match(
    rows: Sequence[sqlite3.Row], result: JointSelectionResult, selection_run_id: str
) -> None:
    """The persisted rows must reproduce the pure objective's accession-side vectors."""
    objective = result.objective
    if objective is None:  # pragma: no cover -- guarded by the caller
        return
    hashes = tuple(sorted(_text(row["accession_hash_sha256"], "hash") for row in rows))
    identities = tuple(
        sorted(selected.accession_number_dashed for selected in (result.selected_accessions))
    )
    base = sum(1 for row in rows if _text(row["accession_role"], "role") == "base")
    stress = sum(1 for row in rows if _text(row["accession_role"], "role") == "stress")
    if (hashes, identities, base, stress) != (
        objective.accession_hash_vector,
        objective.accession_identity_vector,
        objective.base_accession_count,
        objective.stress_accession_count,
    ):
        message = (
            f"selection_run_id {selection_run_id!r}: the persisted selected accessions do not "
            "reproduce the pure objective's accession hash vector, identity vector, or "
            "base/stress counts"
        )
        raise _fail(message)


def _validate_persisted_quota_results(
    connection: sqlite3.Connection,
    selection_run_id: str,
    snapshot_id: str,
    result: JointSelectionResult,
) -> None:
    rows = connection.execute(
        "SELECT quota_result_id, quota_dimension, quota_key, comparison_operator, required_count, "
        "achieved_count, eligible_pool_count, excluded_pool_count, evidence_state, quota_result, "
        "binding_constraint FROM pilot_quota_results "
        "WHERE selection_run_id = ? AND snapshot_id = ? ORDER BY quota_dimension, quota_key",
        (selection_run_id, snapshot_id),
    ).fetchall()
    if result.status != "feasible":
        if rows:
            message = (
                f"selection_run_id {selection_run_id!r} is {result.status!r} but persists "
                f"{len(rows)} quota-result rows; a non-feasible run carries no result rows"
            )
            raise _fail(message)
        return

    expected: dict[tuple[str, str], tuple[object, ...]] = {}
    for diagnostic in result.entity_quota_results:
        expected[(diagnostic.dimension, diagnostic.key)] = _expected_quota_row(
            diagnostic, _PROVISIONAL
        )
    for accession_diagnostic in result.accession_quota_results:
        expected[(accession_diagnostic.dimension, accession_diagnostic.key)] = _expected_quota_row(
            accession_diagnostic, accession_diagnostic.evidence_state
        )
    if len(rows) != len(expected):
        message = (
            f"selection_run_id {selection_run_id!r} persists {len(rows)} quota-result rows, but "
            f"its inputs yield {len(expected)}"
        )
        raise _fail(message)
    for row in rows:
        key = (
            _text(row["quota_dimension"], "quota_dimension"),
            _text(row["quota_key"], "quota_key"),
        )
        if key not in expected:
            message = f"selection_run_id {selection_run_id!r} persists unknown quota {key!r}"
            raise _fail(message)
        persisted = (
            _text(row["comparison_operator"], "comparison_operator"),
            _integer(row["required_count"], "required_count"),
            _integer(row["achieved_count"], "achieved_count"),
            _integer(row["eligible_pool_count"], "eligible_pool_count"),
            _integer(row["excluded_pool_count"], "excluded_pool_count"),
            _text(row["evidence_state"], "evidence_state"),
            _text(row["quota_result"], "quota_result"),
            _flag(row["binding_constraint"], "binding_constraint"),
        )
        if persisted != expected[key]:
            message = (
                f"selection_run_id {selection_run_id!r} quota {key!r} is persisted as "
                f"{persisted!r} but its inputs yield {expected[key]!r}"
            )
            raise _fail(message)
        if _text(row["quota_result_id"], "quota_result_id") != _quota_result_id(
            selection_run_id, key[0], key[1]
        ):
            message = (
                f"selection_run_id {selection_run_id!r} quota {key!r} carries a quota_result_id "
                "that is not derived from its own run identity and quota identifiers"
            )
            raise _fail(message)


def _expected_quota_row(
    diagnostic: QuotaDiagnostic | AccessionQuotaDiagnostic, evidence_state: str
) -> tuple[object, ...]:
    return (
        diagnostic.comparison_operator,
        diagnostic.required_count,
        diagnostic.achieved_count,
        diagnostic.available_eligible_count,
        diagnostic.excluded_pool_count,
        evidence_state,
        diagnostic.status,
        diagnostic.binding_constraint,
    )
