"""S5.1 -- pure accession policy and joint entity-accession selection core.

Pure Python, in-memory only. This module opens no database, issues no SQL, reads no
file, makes no network call, reads no clock, generates no randomness, inspects no
environment variable, mutates no candidate, and persists nothing. Every S5.2
concern (frozen reader, canonical row validation, run identity, transactionality,
persistence, reconstruction, idempotence, the joint policy constant, migration
``0011``) is deliberately absent.

Governing records:

* `Decision 013 <../../../Docs/Decisions/decision_013_pilot_selection_mechanics.md>`_
  section 5 -- the frozen lexicographic objective, integer/categorical comparisons
  only, explicit input ordering, deterministic branch ordering, a deterministic
  search-node limit, and ``infeasible_or_unproven`` on exhaustion.
* Decision 018 -- every accession-specific rule implemented here (roles section 7,
  caps section 8, floors section 9, families section 10, control contribution
  section 11, fiscal-year-end section 12, name change section 13, the single
  deferred quota section 14, 2009/2010 pairing section 15, node limit and failure
  semantics section 17, and the S5.1/S5.2 boundary section 19).
* Decision 014 section 1 -- only ``provisional`` evidence may satisfy an
  affirmative quota.
* Decision 017 section 4 -- the accepted S4 entity objective is unchanged.

**The entity side is reused, never reimplemented.** Entity eligibility, control
eligibility, canonical CIK validation, the entity tie-break hash, entity evidence
penalties, and entity quota diagnostics are imported from the accepted S4.1 core
(``entity_selector``) and called unchanged. Decision 018 section 3.3 forbids
retrofitting entity behaviour, and section 19 forbids a second methodological
implementation of any rule; importing the accepted helpers -- rather than copying
them -- is what keeps both true.

**The objective is solved jointly, not sequentially.** Decision 013 section 5 puts
the accession penalty contribution and the base/stress counts *before* the entity
hash vector, so the S5 entity optimum may legitimately differ from the S4
entity-only draft. This module never fixes an entity optimum first.

*Why the decomposition below is exact.* For a fixed selected entity set ``E`` the
joint key is
``(entity_penalty(E) + accession_penalty(S), base(S), stress(S), hashes(E),
hashes(S), identity(E), identity(S))``. Terms 4 and 6 (``hashes(E)``,
``identity(E)``) are constants once ``E`` is fixed, and every other term depends
only on ``S``; so the joint key for ``E`` is minimised exactly by the accession
selection that lexicographically minimises
``(penalty, base, stress, accession hashes, accession identities)``. Taking the
minimum of that per-``E`` optimum over every feasible ``E`` is therefore the joint
optimum, not a sequential approximation.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Final, Literal

from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    HISTORY_QUOTAS,
    INDUSTRY_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    PILOT_SELECTION_SEED,
    SIZE_QUOTAS,
    TOTAL_OPERATING,
    Candidate,
    CandidateDiagnostic,
    QuotaDiagnostic,
    _build_quota_results,
    _operating_eligible,
    _quota_status,
    _rank_key,
    _select_controls,
    _validate_and_normalize,
    selection_rank,
)

__all__ = [
    "ACCESSION_CAP_LIMITS",
    "ACCESSION_EVIDENCE_LEVELS",
    "ACCESSION_QUOTA_IDENTIFIERS",
    "AMENDMENT_FORMS",
    "AMENDMENT_PURPOSE_EVIDENCE_LEVELS",
    "APPROVED_DEFERRED_QUOTA_KEYS",
    "CROSS_CUTTING_QUOTAS",
    "DEFERRED_QUOTA_KEY",
    "DEFERRED_QUOTA_REQUIRED_COUNT",
    "FYE_CIRCULAR_TOLERANCE_DAYS",
    "MAX_ACCESSIONS_TOTAL",
    "MAX_BASE_ACCESSIONS_PER_CIK",
    "MAX_BASE_ACCESSIONS_TOTAL",
    "MAX_STRESS_ACCESSIONS_TOTAL",
    "MULTI_REGISTRANT_MINIMUM",
    "MULTI_REGISTRANT_TIE_BREAK_SENTINEL",
    "NOT_APPLICABLE",
    "ORIGINAL_ANNUAL_FORMS",
    "QUOTA_DIMENSION_ACCESSION_CAP",
    "QUOTA_DIMENSION_CROSS_CUTTING",
    "QUOTA_KEY_ACCESSIONS_TOTAL",
    "QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES",
    "QUOTA_KEY_BASE_ACCESSIONS_PER_CIK",
    "QUOTA_KEY_BASE_ACCESSIONS_TOTAL",
    "QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES",
    "QUOTA_KEY_INLINE_XBRL_ORIGINALS",
    "QUOTA_KEY_LINKED_AMENDMENT_ENTITIES",
    "QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS",
    "QUOTA_KEY_NAME_CHANGE_ENTITIES",
    "QUOTA_KEY_ORIGINAL_2024_ENTITIES",
    "QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES",
    "QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS",
    "QUOTA_KEY_STRESS_ACCESSIONS_TOTAL",
    "QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES",
    "QUOTA_KEY_TRANSITION_REPORT_ENTITIES",
    "STRESS_FORMS",
    "TRANSITION_REPORT_FORMS",
    "AccessionCandidate",
    "AccessionCapUsage",
    "AccessionDiagnostic",
    "AccessionQuotaDiagnostic",
    "AccessionRole",
    "AmendmentFamily",
    "EntityCandidate",
    "JointObjective",
    "JointSelectionResult",
    "JointSelectionStatus",
    "NameChangeEvidence",
    "QuotaContributionMember",
    "QuotaContributionMembership",
    "QuotaContributionUnit",
    "QuotaMemberKind",
    "SelectedAccession",
    "accession_cap_outcomes",
    "accession_caps_satisfied",
    "accession_evidence_penalty",
    "accession_registrant_slot",
    "accession_selection_rank",
    "assign_accession_role",
    "canonical_anchor_cik_padded",
    "circular_month_day_distance",
    "derive_amendment_families",
    "official_filing_year",
    "solve_joint_selection",
]

# --------------------------------------------------------------------------
# Frozen policy constants
# --------------------------------------------------------------------------

#: Decision 018 section 8 (restating milestone plan section 4.2 as decision
#: authority). Hard constraints, never penalty terms.
MAX_BASE_ACCESSIONS_PER_CIK: Final = 4
MAX_BASE_ACCESSIONS_TOTAL: Final = 96
MAX_STRESS_ACCESSIONS_TOTAL: Final = 24
MAX_ACCESSIONS_TOTAL: Final = 120

#: Decision 018 section 12: 52/53-week fiscal calendars drift a few days without
#: changing the fiscal year end, so only a *circular* month-day distance strictly
#: greater than this tolerance is a fiscal-year-end change.
FYE_CIRCULAR_TOLERANCE_DAYS: Final = 7

_LEAP_REFERENCE_YEAR: Final = 2000
_DAYS_IN_LEAP_YEAR: Final = 366

#: **Decision 083 R60** (adopting Decision 082 section 10.9 option **H-a**). The exact
#: domain-separated literal that occupies the registrant slot of the accession tie-break
#: preimage when -- and only when -- the substantive registrant set is *established* with
#: cardinality greater than one.
#:
#: It is **not a CIK**. It is never parsed as one, never persisted in a CIK column, never
#: presented as an entity, never counted toward any entity or quota, and never a transport
#: locator. It selects **no** registrant at all, which is precisely why it does not violate
#: Decision 081 **R46** section 3.2(5)'s prohibition on choosing a primary CIK by hash:
#: recording that no anchor exists is not selecting one.
#:
#: Being non-numeric, it cannot collide with any ten-digit zero-padded CIK, so the
#: multi-registrant and single-registrant preimage spaces are provably disjoint.
MULTI_REGISTRANT_TIE_BREAK_SENTINEL: Final = "MULTI_REGISTRANT_NO_SINGLETON"

#: Decision 072 **R23** section 5.3, restated anchor-free at identical extension by
#: **Decision 083 R58**: an accession is multi-registrant exactly when its *established*
#: substantive association set has **distinct canonical CIK** cardinality of at least two.
#: Never a raw row count, and never a submitter-only row.
MULTI_REGISTRANT_MINIMUM: Final = 2

ORIGINAL_ANNUAL_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-KT"})
AMENDMENT_FORMS: Final[frozenset[str]] = frozenset({"10-K/A", "10-KT/A"})
#: Decision 018 section 7: eligible 10-KT, 10-K/A, or 10-KT/A anchored to a
#: selected operating entity. 10-KT and 10-KT/A are stress, never base.
STRESS_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-K/A", "10-KT/A"})
TRANSITION_REPORT_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A"})
_ANNUAL_REPORT_FORM: Final = "10-K"

_SUPPORT_FILING_YEAR: Final = 2009
_TARGET_FILING_YEAR: Final = 2010
_TARGET_COHORT: Final = "development"
_RECENT_ORIGINAL_YEARS: Final[frozenset[int]] = frozenset({2025, 2026})
_CURRENT_ORIGINAL_YEAR: Final = 2024

_PROVISIONAL: Final = "provisional"
_WINNING: Final = "winning"

#: Encodes Decision 018 section 3.4's "structurally not applicable" row on a pure
#: input. It is **not** a ``pilot_candidate_accession_evidence.evidence_level``
#: value; the S5.2 loader is what maps stored rows onto these pure inputs.
NOT_APPLICABLE: Final = "not_applicable"

ACCESSION_EVIDENCE_LEVELS: Final[frozenset[str]] = frozenset(
    {"provisional", "review_required", "conflicting", "unavailable"}
)
#: Decision 014 section 6 adds ``unproven`` for amendment purpose only: the
#: category is assignable from metadata but unprovable without document evidence.
AMENDMENT_PURPOSE_EVIDENCE_LEVELS: Final[frozenset[str]] = ACCESSION_EVIDENCE_LEVELS | {"unproven"}

_AMENDMENT_LINKAGE_STATES: Final[frozenset[str]] = frozenset(
    {
        "amends_original",
        "amends_prior_amendment",
        "supplements_original",
        "possible_amendment_of",
        "unresolved_amendment",
    }
)
_AMENDMENT_PURPOSE_CATEGORIES: Final[frozenset[str]] = frozenset(
    {"administrative_or_exhibit", "financial_or_xbrl_correction", "narrative_or_governance"}
)

# --------------------------------------------------------------------------
# Quota identifiers -- one canonical definition for every dimension and key
# --------------------------------------------------------------------------
#
# Decision 016 section 6 leaves ``quota_dimension`` and ``quota_key`` as
# unconstrained text, so these strings are this module's to fix. They are
# declared once here and used everywhere; policy logic never repeats a literal.
# They are identifiers only -- nothing below is a persistence-shaped record, and
# the S5.2 policy-version constant is deliberately not defined here.

QUOTA_DIMENSION_CROSS_CUTTING: Final = "cross_cutting"
QUOTA_DIMENSION_ACCESSION_CAP: Final = "accession_cap"

QUOTA_KEY_LINKED_AMENDMENT_ENTITIES: Final = "linked_amendment_entities"
QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES: Final = "amendment_purpose_categories"
QUOTA_KEY_TRANSITION_REPORT_ENTITIES: Final = "transition_report_entities"
QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES: Final = "fiscal_year_end_change_entities"
QUOTA_KEY_NAME_CHANGE_ENTITIES: Final = "name_change_entities"
QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS: Final = "multi_registrant_accessions"
QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES: Final = "support_target_pair_entities"
QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS: Final = "pre_inline_xbrl_originals"
QUOTA_KEY_INLINE_XBRL_ORIGINALS: Final = "inline_xbrl_originals"
QUOTA_KEY_ORIGINAL_2024_ENTITIES: Final = "original_2024_entities"
QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES: Final = "original_2025_2026_entities"

#: Decision 018 section 14: the one genuinely unmeasurable M2.3 quota. It is
#: excluded from hard feasibility, never proxied, never reported as satisfied,
#: and remains a mandatory M2.5 verification obligation.
DEFERRED_QUOTA_KEY: Final = "difficult_or_nonstandard_packages"
DEFERRED_QUOTA_REQUIRED_COUNT: Final = 6
APPROVED_DEFERRED_QUOTA_KEYS: Final[frozenset[str]] = frozenset({DEFERRED_QUOTA_KEY})

QUOTA_KEY_BASE_ACCESSIONS_PER_CIK: Final = "base_accessions_per_cik"
QUOTA_KEY_BASE_ACCESSIONS_TOTAL: Final = "base_accessions_total"
QUOTA_KEY_STRESS_ACCESSIONS_TOTAL: Final = "stress_accessions_total"
QUOTA_KEY_ACCESSIONS_TOTAL: Final = "accessions_total"

#: Milestone plan section 4.2's measurable cross-cutting coverage, with the
#: counting units frozen by Decision 013 section 3 and the contribution rules
#: frozen by Decision 018 sections 10-15. Every one of these is hard.
CROSS_CUTTING_QUOTAS: Final[Mapping[str, int]] = {
    QUOTA_KEY_LINKED_AMENDMENT_ENTITIES: 8,
    QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES: 3,
    QUOTA_KEY_TRANSITION_REPORT_ENTITIES: 2,
    QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES: 3,
    QUOTA_KEY_NAME_CHANGE_ENTITIES: 4,
    QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS: 2,
    QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES: 6,
    QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS: 12,
    QUOTA_KEY_INLINE_XBRL_ORIGINALS: 12,
    QUOTA_KEY_ORIGINAL_2024_ENTITIES: 6,
    QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES: 4,
}

#: Decision 018 section 8's four caps, keyed by the identifier each is reported
#: under. Both base caps are kept: the per-CIK cap and the global cap are
#: separate constraints, and the global one is never relaxed on the grounds that
#: the per-CIK cap happens to bind first at pilot scale.
ACCESSION_CAP_LIMITS: Final[Mapping[str, int]] = {
    QUOTA_KEY_BASE_ACCESSIONS_PER_CIK: MAX_BASE_ACCESSIONS_PER_CIK,
    QUOTA_KEY_BASE_ACCESSIONS_TOTAL: MAX_BASE_ACCESSIONS_TOTAL,
    QUOTA_KEY_STRESS_ACCESSIONS_TOTAL: MAX_STRESS_ACCESSIONS_TOTAL,
    QUOTA_KEY_ACCESSIONS_TOTAL: MAX_ACCESSIONS_TOTAL,
}

#: Every ``(quota_dimension, quota_key)`` pair S5.1 reports, in the exact,
#: deterministic order :func:`solve_joint_selection` emits them.
ACCESSION_QUOTA_IDENTIFIERS: Final[tuple[tuple[str, str], ...]] = (
    *((QUOTA_DIMENSION_CROSS_CUTTING, key) for key in CROSS_CUTTING_QUOTAS),
    (QUOTA_DIMENSION_CROSS_CUTTING, DEFERRED_QUOTA_KEY),
    *((QUOTA_DIMENSION_ACCESSION_CAP, key) for key in ACCESSION_CAP_LIMITS),
)

_DASHED_ACCESSION_PATTERN: Final = re.compile(r"^\d{10}-\d{2}-\d{6}$")
_ISO_DATE_PATTERN: Final = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MAX_CIK_NUMERIC: Final = 9_999_999_999

AccessionRole = Literal["base", "stress", "support", "control"]
JointSelectionStatus = Literal["feasible", "infeasible", "infeasible_or_unproven"]
#: The two member kinds ``pilot_quota_result_members.member_kind`` admits.
QuotaMemberKind = Literal["entity", "accession"]


# --------------------------------------------------------------------------
# Pure identity and calendar helpers
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AccessionCapUsage:
    """The cap-relevant counts of one candidate accession selection.

    ``max_base_per_cik`` is the largest number of base accessions any single
    selected operating CIK carries. Support and control accessions count toward
    ``accession_total`` only (Decision 018 section 7), so they never appear in
    ``base_total`` or ``stress_total``.
    """

    base_total: int = 0
    stress_total: int = 0
    accession_total: int = 0
    max_base_per_cik: int = 0

    def achieved(self, quota_key: str) -> int:
        """The count this usage records against one cap identifier."""
        if quota_key == QUOTA_KEY_BASE_ACCESSIONS_PER_CIK:
            return self.max_base_per_cik
        if quota_key == QUOTA_KEY_BASE_ACCESSIONS_TOTAL:
            return self.base_total
        if quota_key == QUOTA_KEY_STRESS_ACCESSIONS_TOTAL:
            return self.stress_total
        if quota_key == QUOTA_KEY_ACCESSIONS_TOTAL:
            return self.accession_total
        message = f"unrecognized accession cap identifier: {quota_key!r}"
        raise ValueError(message)


def accession_cap_outcomes(usage: AccessionCapUsage) -> tuple[tuple[str, int, int, bool], ...]:
    """Evaluate all four Decision 018 section 8 caps over one usage.

    Returns ``(quota_key, limit, achieved, satisfied)`` in the frozen identifier
    order. Every cap is an ``at_most`` constraint satisfied when
    ``achieved <= limit``; integer comparisons only.

    **This is the single implementation of the cap rule.** The joint search calls
    it to decide whether adding an accession keeps the selection feasible, and
    the diagnostics builder calls it to report the same outcome, so a cap can
    never pass a report while failing the search or the reverse.
    """
    return tuple(
        (quota_key, limit, usage.achieved(quota_key), usage.achieved(quota_key) <= limit)
        for quota_key, limit in ACCESSION_CAP_LIMITS.items()
    )


def accession_caps_satisfied(usage: AccessionCapUsage) -> bool:
    """Whether a usage violates none of the four frozen accession caps.

    A cap violation is an infeasibility condition, never a penalty and never a
    warning (Decision 018 section 28).
    """
    return all(satisfied for _key, _limit, _achieved, satisfied in accession_cap_outcomes(usage))


def canonical_anchor_cik_padded(cik_numeric: int) -> str:
    """Return the canonical ten-digit anchor CIK derived from the stored numeric CIK.

    ``anchor_cik_padded`` is **derived**, not a schema column:
    ``pilot_candidate_accessions`` stores ``anchor_cik_numeric`` only. Deriving it
    here keeps the rendering that feeds the tie-break hash in one place.
    """
    if isinstance(cik_numeric, bool) or not isinstance(cik_numeric, int):
        message = f"anchor_cik_numeric must be an integer, got {cik_numeric!r}"
        raise ValueError(message)
    if cik_numeric < 0 or cik_numeric > _MAX_CIK_NUMERIC:
        message = f"anchor_cik_numeric out of canonical range: {cik_numeric!r}"
        raise ValueError(message)
    return f"{cik_numeric:010d}"


def accession_registrant_slot(
    anchor_cik_numeric: int | None,
    substantive_registrant_ciks: Sequence[int] = (),
) -> str:
    """Return what occupies the tie-break registrant slot (**Decision 083 R60**).

    Exactly two outcomes, and no third:

    * an **established sole** substantive registrant yields that registrant's
      canonical ten-digit padded CIK, byte-identical to what the pre-correction
      implementation produced -- which is what preserves every existing
      single-registrant preimage (Decision 082 section 10.9);
    * an **established** substantive set of cardinality greater than one yields
      :data:`MULTI_REGISTRANT_TIE_BREAK_SENTINEL`, which names **no** registrant.

    ``anchor_cik_numeric`` is authoritative when present: migration ``0014``'s
    ``CHECK`` constraints already guarantee it exists only under an established set
    of cardinality exactly one. When it is ``None`` the set must be genuinely
    multi-registrant, and a sole-registrant set arriving without its anchor is a
    contradiction rather than a case to be papered over.

    The slot is a pure function of the *cardinality* of the association set and
    never of its membership, so it cannot drift when the set is later corrected --
    the exact hazard Decision 082 section 10.9 rejected option H-b for -- and it is
    invariant to observation, parser, archive, and insertion order.

    Raises:
        ValueError: no anchor and fewer than two substantive registrants.
    """
    if anchor_cik_numeric is not None:
        return canonical_anchor_cik_padded(anchor_cik_numeric)
    if len(set(substantive_registrant_ciks)) < MULTI_REGISTRANT_MINIMUM:
        message = (
            "an accession with no anchor must carry at least two distinct substantive "
            f"registrants; got {sorted(set(substantive_registrant_ciks))!r}"
        )
        raise ValueError(message)
    return MULTI_REGISTRANT_TIE_BREAK_SENTINEL


def accession_selection_rank(
    anchor_cik_padded: str,
    accession_number_dashed: str,
    selection_seed: str = PILOT_SELECTION_SEED,
) -> str:
    """Return the frozen accession tie-break rank (Decision 018 section 5.2).

    ``SHA256(selection_seed + "|" + registrant_slot + "|" +
    accession_number_dashed)``, lowercase 64-character hexadecimal. The **dashed**
    form is canonical for hashing; the plain 18-character form remains the
    database and foreign-key column. Associated registrant CIKs never enter this
    hash, so a multi-registrant accession's identity cannot drift when its
    registrant set is later corrected.

    The first positional argument is the **registrant slot**
    (:func:`accession_registrant_slot`), not necessarily a CIK: under **Decision 083
    R60** an established multi-registrant accession passes
    :data:`MULTI_REGISTRANT_TIE_BREAK_SENTINEL` here, because no anchor exists to
    pass. The parameter keeps its historical name so that every single-registrant
    call site, and therefore every single-registrant digest, is untouched.
    """
    payload = f"{selection_seed}|{anchor_cik_padded}|{accession_number_dashed}".encode()
    return hashlib.sha256(payload).hexdigest()


def _month_day_ordinal(value: date) -> int:
    """Map a date's month/day onto the fixed leap-year calendar (year 2000)."""
    mapped = date(_LEAP_REFERENCE_YEAR, value.month, value.day)
    return (mapped - date(_LEAP_REFERENCE_YEAR, 1, 1)).days


def circular_month_day_distance(first: date, second: date) -> int:
    """Return the circular calendar month-day distance in days.

    Decision 018 section 12 requires a *circular* distance so the year boundary is
    handled correctly: late December to early January is a small distance, not a
    large one. Month/day values are mapped onto the fixed leap-year calendar 2000
    and compared as ``min(abs(a - b), 366 - abs(a - b))``.
    """
    raw = abs(_month_day_ordinal(first) - _month_day_ordinal(second))
    return min(raw, _DAYS_IN_LEAP_YEAR - raw)


def _parse_iso_date(value: str | None) -> date | None:
    """Parse a strict ``YYYY-MM-DD`` date, returning ``None`` when absent or invalid.

    Missing or invalid required dates fail closed (Decision 018 section 12): they
    never affirmatively contribute. A rejected value is surfaced as a candidate
    diagnostic rather than silently ignored.
    """
    if value is None:
        return None
    if not isinstance(value, str) or _ISO_DATE_PATTERN.match(value) is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def official_filing_year(official_filing_date: str | None) -> int | None:
    """The calendar year of a stored official filing date, or ``None`` if unusable.

    **The single accepted filing-year derivation.** Decision 018 section 19 puts
    every methodological rule in exactly one place, and this is that place for the
    filing year Decision 018 sections 7 and 15 make the 2009 support role depend
    on. It delegates to :func:`_parse_iso_date` and adds no second regex, no
    substring parser, and no ``int(value[:4])`` shortcut, so a caller cannot read a
    year out of a value the accepted core rejects.

    ``None`` is returned for an absent date and for every value
    :func:`_parse_iso_date` refuses -- an impossible calendar date such as
    ``2009-02-30``, a compact ``20090315``, a partially padded ``2009-3-15``, a
    non-numeric ``abcd-01-01``, and the empty string alike. Returning ``None``
    rather than raising keeps this helper's contract identical to the accepted
    core's existing fail-closed behaviour; a caller that needs a usable year for a
    non-null stored date raises its own fail-closed error.
    """
    parsed = _parse_iso_date(official_filing_date)
    return None if parsed is None else parsed.year


# --------------------------------------------------------------------------
# Pure inputs
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NameChangeEvidence:
    """Entity-level identity evidence for the name-change quota (Decision 018 section 13).

    Every field defaults to its fail-closed value. M2.3 is name-only: a
    ticker-only claim never contributes, and the mere absence of ticker evidence
    is the expected M2.3 condition, so it produces no warning and no diagnostic.
    """

    has_identity_evidence: bool = False
    evidence_role: str | None = None
    evidence_level: str = "unavailable"
    former_name_record_parseable: bool = False
    has_prior_current_or_from_to: bool = False
    ticker_change_claimed: bool = False


@dataclass(frozen=True, slots=True)
class EntityCandidate:
    """One immutable selected-entity input: the accepted S4 candidate plus S5 evidence.

    ``candidate`` is the accepted S4.1 :class:`~disclosure_drift.sec.entity_selector.Candidate`
    used verbatim -- its eligibility, evidence penalty, and tie-break hash keep
    exactly their S4 meaning (Decision 018 section 3.3).
    """

    candidate: Candidate
    name_change: NameChangeEvidence = field(default_factory=NameChangeEvidence)

    @property
    def cik_padded(self) -> str:
        """Canonical ten-digit CIK of the wrapped S4 candidate."""
        return self.candidate.cik_padded


@dataclass(frozen=True, slots=True)
class AccessionCandidate:
    """One immutable candidate accession from the frozen candidate snapshot.

    Every eligibility- and evidence-relevant field defaults to its fail-closed
    value, so a field left unset can never satisfy an affirmative quota. The
    dashed accession is canonical for hashing, ordering, and identity fallback
    (Decision 018 section 5.1); ``accession_plain`` is carried through because it
    remains the future database key.
    """

    accession_plain: str
    accession_number_dashed: str
    #: **Decision 083 R58.** ``None`` whenever the accession does not have exactly one
    #: established substantive registrant. No arbitrary primary CIK is ever put here.
    anchor_cik_numeric: int | None
    form_type: str
    #: **Decision 083 R58/R62.** The complete substantive registrant association set.
    #: Left empty for a sole-registrant accession, where ``anchor_cik_numeric`` already
    #: carries the whole set -- see :attr:`substantive_registrant_ciks_resolved`. It is
    #: *required* when there is no anchor, because an accession can never have neither.
    substantive_registrant_ciks: tuple[int, ...] = ()
    is_amendment: bool = False
    official_filing_date: str | None = None
    report_date: str | None = None
    cohort_applicability: Literal["applies", "pre_study"] = "applies"
    provisional_official_cohort: str | None = None
    filing_date_evidence_level: str = "unavailable"
    cohort_evidence_level: str = "unavailable"
    xbrl_evidence_level: str = "unavailable"
    amendment_purpose_evidence_level: str = NOT_APPLICABLE
    amendment_linkage_evidence_level: str = NOT_APPLICABLE
    multi_registrant_evidence_level: str = NOT_APPLICABLE
    has_xbrl: bool = False
    has_inline_xbrl: bool = False
    amendment_linkage_state: str | None = None
    provisional_parent_accession_dashed: str | None = None
    amendment_purpose_category: str | None = None
    amendment_purpose_quota_eligible: bool = False
    base_eligible: bool = False
    stress_eligible: bool = False
    support_eligible: bool = False
    control_eligible: bool = False
    multi_registrant: bool = False

    @property
    def substantive_registrant_ciks_resolved(self) -> tuple[int, ...]:
        """The complete substantive association set, sorted and deduplicated.

        An anchor is available only under an established set of cardinality exactly
        one (migration ``0014``), so an anchor *is* the whole substantive set and
        needs no second field to restate it. That equivalence is what lets every
        existing single-registrant construction stay byte-unchanged while the
        relational set becomes authoritative for the multi-registrant case.
        """
        if self.anchor_cik_numeric is not None:
            return (self.anchor_cik_numeric,)
        return tuple(sorted(set(self.substantive_registrant_ciks)))

    @property
    def substantive_registrants_padded(self) -> tuple[str, ...]:
        """The substantive association set as canonical ten-digit padded CIKs.

        Sorted by canonical CIK, so it is invariant to observation, parser, archive,
        full-index row, and insertion order (**Decision 083 R58**).
        """
        return tuple(
            canonical_anchor_cik_padded(cik) for cik in self.substantive_registrant_ciks_resolved
        )

    @property
    def is_established_multi_registrant(self) -> bool:
        """Whether the established substantive set has cardinality greater than one."""
        return len(self.substantive_registrant_ciks_resolved) >= MULTI_REGISTRANT_MINIMUM

    @property
    def anchor_cik_padded(self) -> str | None:
        """Canonical ten-digit anchor CIK, or ``None`` when no anchor exists.

        ``None`` is the truthful answer for an established multi-registrant accession
        (**Decision 083 R58**) and is never replaced by a substitute CIK.
        """
        if self.anchor_cik_numeric is None:
            return None
        return canonical_anchor_cik_padded(self.anchor_cik_numeric)

    @property
    def registrant_slot(self) -> str:
        """What occupies the tie-break registrant slot (**Decision 083 R60**)."""
        return accession_registrant_slot(self.anchor_cik_numeric, self.substantive_registrant_ciks)

    @property
    def rank(self) -> str:
        """Deterministic tie-break rank under the frozen production seed."""
        return accession_selection_rank(self.registrant_slot, self.accession_number_dashed)


# --------------------------------------------------------------------------
# Pure results
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SelectedAccession:
    """One selected accession with its role and contiguous deterministic order."""

    accession_plain: str
    accession_number_dashed: str
    #: **Decision 083 R58/R61.** ``None`` for an established multi-registrant accession,
    #: where the relational set below is authoritative and no anchor exists.
    anchor_cik_padded: str | None
    accession_role: AccessionRole
    selected_order: int
    accession_tie_break_sha256: str
    #: The complete substantive association set, sorted by canonical CIK. For a
    #: sole-registrant accession this is exactly ``(anchor_cik_padded,)``.
    substantive_registrants_padded: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AccessionDiagnostic:
    """Why a candidate accession could not be selected, or was not selected."""

    accession_number_dashed: str
    #: The **Decision 083 R60** registrant slot: a padded CIK for a sole-registrant
    #: accession, or :data:`MULTI_REGISTRANT_TIE_BREAK_SENTINEL`. A diagnostic label,
    #: never a claim of primacy and never an entity reference.
    registrant_slot_padded: str
    form_type: str
    reason: str


@dataclass(frozen=True, slots=True)
class AmendmentFamily:
    """A transitive amendment chain rooted at an original accession.

    Family identity is the resolved root original's canonical dashed accession
    (Decision 018 section 10.1). Unresolved or absent parentage produces a
    singleton diagnostic family that can never satisfy linked-amendment coverage
    (section 10.2). Family identity enters neither the tie-break hash nor
    ``selected_order``, and creates no cap of its own (section 10.3).
    """

    family_id: str
    members: tuple[str, ...]
    resolved: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AccessionQuotaDiagnostic:
    """One accession-side quota's integer-only satisfaction state.

    ``deferred`` is true only for the single Decision 018 section 14 quota; every
    other quota here is hard and binding on feasibility (section 16).
    """

    dimension: str
    key: str
    comparison_operator: str
    required_count: int
    available_eligible_count: int
    achieved_count: int
    status: str
    binding_constraint: bool
    excluded_pool_count: int
    evidence_state: str
    deferred: bool


@dataclass(frozen=True, slots=True)
class JointObjective:
    """The complete frozen lexicographic objective of an approved selection.

    Field order is the frozen term order (Decision 013 section 5, Decision 018
    section 3.1): term 2 is one integer over entities *and* accessions, then base
    count, then stress count, then the complete sorted entity-hash vector, then
    the complete sorted accession-hash vector, then canonical identity fallbacks.
    """

    evidence_penalty: int
    base_accession_count: int
    stress_accession_count: int
    entity_hash_vector: tuple[str, ...]
    accession_hash_vector: tuple[str, ...]
    entity_identity_vector: tuple[str, ...]
    accession_identity_vector: tuple[str, ...]

    def as_tuple(
        self,
    ) -> tuple[
        int,
        int,
        int,
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, ...],
        tuple[str, ...],
    ]:
        """The objective as one comparable lexicographic tuple."""
        return (
            self.evidence_penalty,
            self.base_accession_count,
            self.stress_accession_count,
            self.entity_hash_vector,
            self.accession_hash_vector,
            self.entity_identity_vector,
            self.accession_identity_vector,
        )


@dataclass(frozen=True, slots=True)
class QuotaContributionMember:
    """One member of one achieved quota-contribution unit.

    ``cik_padded`` is the member entity for an ``entity`` member and the **anchor**
    entity for an ``accession`` member, so the entity-level projection of a
    membership artifact needs no further derivation. Under **Decision 083 R58** an
    established multi-registrant accession has no anchor, so ``cik_padded`` is
    ``None`` there and :attr:`registrant_ciks_padded` carries the truth instead --
    no substitute CIK is invented to keep the column populated. ``accession_plain``
    is ``None`` on an ``entity`` member and the canonical eighteen-digit identity on
    an ``accession`` member, matching ``pilot_quota_result_members``'s two
    mutually exclusive member columns (Decision 016 section 3), which already
    require ``cik_numeric`` to be ``NULL`` for an accession member in any case.
    """

    member_kind: QuotaMemberKind
    cik_padded: str | None
    accession_plain: str | None
    #: **Decision 083 R58/R62.** The complete substantive association set of an
    #: ``accession`` member, sorted by canonical CIK. Empty on an ``entity`` member,
    #: whose contributing entity is ``cik_padded`` itself.
    registrant_ciks_padded: tuple[str, ...] = ()

    @property
    def contributing_ciks(self) -> tuple[str, ...]:
        """Every entity this member makes contribute, in canonical order.

        For an ``entity`` member that is the entity itself. For an ``accession``
        member it is the **complete** substantive association set: **Decision 083
        R62** attributes a joint filing to every substantive registrant, never to one
        and never to none. A sole-registrant accession yields exactly its anchor, so
        the pre-correction result is reproduced unchanged.
        """
        if self.member_kind == "entity":
            return () if self.cik_padded is None else (self.cik_padded,)
        return self.registrant_ciks_padded


@dataclass(frozen=True, slots=True)
class QuotaContributionUnit:
    """One achieved contribution unit of one quota, with the members achieving it.

    ``unit`` is the unit identity the accepted witness model already uses -- an
    anchor CIK, a canonical dashed accession, or an amendment-purpose category --
    and is never reinterpreted here.
    """

    dimension: str
    key: str
    unit: str
    members: tuple[QuotaContributionMember, ...]


@dataclass(frozen=True, slots=True)
class QuotaContributionMembership:
    """The single immutable quota-contribution membership artifact (Decision 020).

    **One artifact, three projections.** Decision 020 sections 5 and 6 make Stage
    S5.1 the sole source of quota-contribution membership: the entity-level form,
    the accession-level form, and the quota-result-member form are transposes of
    the units carried here, and no consumer re-derives a contribution rule
    (Decision 018 section 19).

    Membership covers exactly the eleven measurable cross-cutting quotas. The
    Decision 018 section 14 deferred quota contributes nothing and is never
    reported as satisfied; the four accession caps are ``at_most`` constraints
    rather than affirmative contributions and produce no membership either.

    The artifact is canonical and order-independent: units are emitted sorted by
    ``(dimension, key, unit)`` and members sorted within a unit, so neither the
    candidate input order nor a database retrieval order can change a result.
    """

    units: tuple[QuotaContributionUnit, ...]

    @classmethod
    def derive(
        cls,
        entities: Iterable[EntityCandidate],
        accessions: Iterable[AccessionCandidate],
        *,
        selected_entity_ciks: Iterable[str],
        selected_accession_plains: Iterable[str],
        selection_seed: str = PILOT_SELECTION_SEED,
    ) -> QuotaContributionMembership:
        """Derive the membership a selection -- or a hypothetical package -- supplies.

        ``entities`` and ``accessions`` are the complete frozen candidate pool, so
        amendment parentage resolves transitively exactly as it does for the
        selection itself; the two ``selected_*`` arguments name the subset whose
        contributions are being derived. Passing a reserve package's own entity
        and accession bundle therefore yields the contribution set that package
        would supply, computed by this one derivation rather than by a second
        implementation of any quota rule (Decision 020 sections 6 and 7).

        Raises:
            ValueError: a malformed candidate pool, or a selected identity that is
                not in it.
        """
        entity_pool = _validate_entities(entities)
        accession_pool = _validate_accessions(accessions)
        ctx = _build_pool_context(accession_pool, selection_seed)
        return _derive_membership(
            ctx,
            entity_pool,
            selected_entity_ciks=selected_entity_ciks,
            selected_accession_plains=selected_accession_plains,
        )

    def units_for(self, dimension: str, key: str) -> tuple[QuotaContributionUnit, ...]:
        """Every achieved unit of one quota, in canonical order."""
        return tuple(unit for unit in self.units if unit.dimension == dimension and unit.key == key)

    def achieved_count(self, dimension: str, key: str) -> int:
        """The number of achieved units of one quota.

        This is the value :func:`solve_joint_selection` publishes as that quota's
        ``achieved_count``, so the published integer and the emitted membership
        agree by construction rather than by a downstream reconciliation.
        """
        return len(self.units_for(dimension, key))

    def entity_contributions(self) -> tuple[tuple[str, str, str], ...]:
        """``(cik_padded, dimension, key)`` rows, deduplicated and sorted.

        The projection behind ``pilot_selected_entity_quota_contributions``. An
        entity contributes to a quota when it is an entity member of one of that
        quota's achieved units, or when it is a **substantive registrant** of an
        accession member of one (**Decision 083 R62**; for a sole-registrant
        accession that is exactly its anchor, as before).
        """
        rows = {
            (cik, unit.dimension, unit.key)
            for unit in self.units
            for member in unit.members
            for cik in member.contributing_ciks
        }
        return tuple(sorted(rows))

    def accession_contributions(self) -> tuple[tuple[str, str, str], ...]:
        """``(accession_plain, dimension, key)`` rows, deduplicated and sorted.

        The projection behind ``pilot_selected_accession_quota_contributions``.
        """
        rows = {
            (member.accession_plain, unit.dimension, unit.key)
            for unit in self.units
            for member in unit.members
            if member.accession_plain is not None
        }
        return tuple(sorted(rows))

    def quota_members(self) -> tuple[tuple[str, str, int, str, str | None, str | None], ...]:
        """``(dimension, key, member_order, member_kind, cik_padded, accession_plain)``.

        The projection behind ``pilot_quota_result_members``: every distinct
        member of a quota's achieved units, in canonical order, numbered
        contiguously from 1 within that quota.
        """
        by_quota: dict[tuple[str, str], set[QuotaContributionMember]] = {}
        for unit in self.units:
            by_quota.setdefault((unit.dimension, unit.key), set()).update(unit.members)
        rows: list[tuple[str, str, int, str, str | None, str | None]] = []
        for (dimension, key), members in sorted(by_quota.items()):
            for order, member in enumerate(sorted(members, key=_member_sort_key), start=1):
                rows.append(
                    (
                        dimension,
                        key,
                        order,
                        member.member_kind,
                        member.cik_padded,
                        member.accession_plain,
                    )
                )
        return tuple(rows)

    def contribution_keys_for_entity(self, cik_padded: str) -> tuple[tuple[str, str], ...]:
        """The complete ``(dimension, key)`` contribution signature of one entity.

        This is the set Decision 013 section 6 requires a reserve package to
        preserve exactly, and the set migration ``0009``'s feasible-transition
        trigger compares each reserve package against.
        """
        return tuple(
            sorted(
                {
                    (dimension, key)
                    for cik, dimension, key in self.entity_contributions()
                    if cik == cik_padded
                }
            )
        )

    def contribution_keys(self) -> tuple[tuple[str, str], ...]:
        """Every ``(dimension, key)`` this membership contributes to, sorted."""
        return tuple(sorted({(unit.dimension, unit.key) for unit in self.units}))


def _member_sort_key(member: QuotaContributionMember) -> tuple[str, str, str]:
    """Canonical member order: kind, then entity identity, then accession identity.

    An anchorless accession member sorts under the empty entity identity, which is
    below every padded CIK and is not a CIK -- so ordering stays total and
    deterministic without the sentinel ever entering an entity position.
    """
    return (member.member_kind, member.cik_padded or "", member.accession_plain or "")


@dataclass(frozen=True, slots=True)
class JointSelectionResult:
    """The S5.1 joint entity-accession outcome.

    A non-feasible result never carries a partial selection and never exposes a
    partial approved objective: ``selected_operating``, ``selected_controls``, and
    ``selected_accessions`` are empty, ``objective`` is ``None``, and
    ``quota_contributions`` is empty unless ``status == "feasible"`` (Decision 018
    section 17).
    """

    status: JointSelectionStatus
    selection_seed: str
    selected_operating: tuple[Candidate, ...]
    selected_controls: tuple[Candidate, ...]
    selected_accessions: tuple[SelectedAccession, ...]
    objective: JointObjective | None
    entity_quota_results: tuple[QuotaDiagnostic, ...]
    accession_quota_results: tuple[AccessionQuotaDiagnostic, ...]
    deferred_quota_result: AccessionQuotaDiagnostic
    excluded_candidates: tuple[CandidateDiagnostic, ...]
    accession_diagnostics: tuple[AccessionDiagnostic, ...]
    amendment_families: tuple[AmendmentFamily, ...]
    quota_contributions: QuotaContributionMembership
    expanded_node_count: int
    node_limit: int
    node_limit_exhausted: bool

    @property
    def is_feasible(self) -> bool:
        """Whether this result is a complete, approved joint selection."""
        return self.status == "feasible"

    @property
    def selected_entities(self) -> tuple[Candidate, ...]:
        """All selected entities in deterministic rank order, operating then controls."""
        return self.selected_operating + self.selected_controls


# --------------------------------------------------------------------------
# Input validation -- every malformed input fails before search begins
# --------------------------------------------------------------------------


def _validate_entities(entities: Iterable[EntityCandidate]) -> tuple[EntityCandidate, ...]:
    """Validate entity inputs, reusing the accepted S4 canonical-CIK gate verbatim."""
    pool = tuple(entities)
    for entry in pool:
        # Typed as ``object`` on purpose: the guard is a runtime gate against an
        # untyped caller, not a restatement of the annotation.
        supplied: object = entry
        if not isinstance(supplied, EntityCandidate):
            message = f"entity input must be an EntityCandidate, got {type(supplied).__name__}"
            raise TypeError(message)
    _validate_and_normalize(entry.candidate for entry in pool)
    for entry in pool:
        evidence = entry.name_change
        if evidence.evidence_role is not None and evidence.evidence_role not in (
            "winning",
            "competing",
            "supporting",
        ):
            message = (
                f"unrecognized identity evidence_role {evidence.evidence_role!r} "
                f"for CIK {entry.cik_padded!r}"
            )
            raise ValueError(message)
        if evidence.evidence_level not in ACCESSION_EVIDENCE_LEVELS:
            message = (
                f"unrecognized identity evidence level {evidence.evidence_level!r} "
                f"for CIK {entry.cik_padded!r}"
            )
            raise ValueError(message)
    return pool


def _reject(condition: bool, message: str) -> None:
    if condition:
        raise ValueError(message)


def _validate_accessions(
    accessions: Iterable[AccessionCandidate],
) -> tuple[AccessionCandidate, ...]:
    """Reject malformed, duplicate, or contradictory accession inputs.

    Canonical shape (dashed form, plain/dashed agreement, canonical anchor CIK),
    duplicate identity, and every applicability/evidence contradiction Decision
    018 section 3.4 makes meaningless are rejected here, before any search node is
    expanded (Decision 018 section 17). Database-row validation -- stored hashes
    and stored plain/dashed columns -- belongs to the S5.2 loader (section 5.3).
    """
    pool = tuple(accessions)
    seen_plain: set[str] = set()
    seen_dashed: set[str] = set()
    for accession in pool:
        # Typed as ``object`` on purpose: a runtime gate against an untyped caller.
        supplied: object = accession
        if not isinstance(supplied, AccessionCandidate):
            message = (
                f"accession input must be an AccessionCandidate, got {type(supplied).__name__}"
            )
            raise TypeError(message)
        dashed = accession.accession_number_dashed
        _reject(
            _DASHED_ACCESSION_PATTERN.match(dashed) is None,
            f"malformed canonical dashed accession: {dashed!r}",
        )
        plain = accession.accession_plain
        _reject(
            plain != dashed.replace("-", ""),
            f"accession_plain {plain!r} is inconsistent with dashed form {dashed!r}",
        )
        _reject(dashed in seen_dashed, f"duplicate dashed accession in candidate pool: {dashed!r}")
        _reject(plain in seen_plain, f"duplicate plain accession in candidate pool: {plain!r}")
        seen_dashed.add(dashed)
        seen_plain.add(plain)

        # Raises on a malformed or out-of-range numeric CIK, and -- under
        # **Decision 083 R58/R60** -- on an anchorless accession that does not carry a
        # genuine multi-registrant set. An accession can never have neither an anchor
        # nor an association set: that combination is unrepresentable, not a default.
        registrants = accession.substantive_registrants_padded
        _reject(
            not registrants,
            f"accession {dashed!r} carries neither an anchor nor a substantive "
            "registrant association set",
        )
        _reject(
            accession.anchor_cik_numeric is None and len(registrants) < MULTI_REGISTRANT_MINIMUM,
            f"accession {dashed!r} has no anchor but fewer than "
            f"{MULTI_REGISTRANT_MINIMUM} distinct substantive registrants",
        )
        # **Decision 072 R23 section 5.3**, restated anchor-free at identical extension.
        # The flag and the association set can never disagree.
        _reject(
            accession.multi_registrant != accession.is_established_multi_registrant,
            f"multi_registrant on {dashed!r} disagrees with its substantive association "
            f"set of {len(registrants)} distinct registrant(s)",
        )

        _reject(
            not isinstance(accession.form_type, str) or not accession.form_type,
            f"missing form_type on accession {dashed!r}",
        )
        if accession.form_type in AMENDMENT_FORMS:
            _reject(
                not accession.is_amendment,
                f"form {accession.form_type!r} on {dashed!r} contradicts is_amendment=False",
            )
        if accession.form_type in ORIGINAL_ANNUAL_FORMS:
            _reject(
                accession.is_amendment,
                f"form {accession.form_type!r} on {dashed!r} contradicts is_amendment=True",
            )

        _reject(
            accession.filing_date_evidence_level not in ACCESSION_EVIDENCE_LEVELS,
            f"unrecognized filing-date evidence level on {dashed!r}: "
            f"{accession.filing_date_evidence_level!r}",
        )
        _reject(
            accession.xbrl_evidence_level not in ACCESSION_EVIDENCE_LEVELS,
            f"unrecognized XBRL evidence level on {dashed!r}: {accession.xbrl_evidence_level!r}",
        )

        _validate_cohort_applicability(accession, dashed)
        _validate_amendment_applicability(accession, dashed)
        _validate_multi_registrant_applicability(accession, dashed)

        _reject(
            accession.base_eligible and accession.is_amendment,
            f"base_eligible amendment is contradictory on {dashed!r}",
        )
        _reject(
            accession.amendment_purpose_quota_eligible
            and (
                accession.amendment_purpose_category is None
                or accession.amendment_purpose_evidence_level != _PROVISIONAL
            ),
            f"amendment_purpose_quota_eligible requires a provisional category on {dashed!r}",
        )
        if accession.amendment_purpose_category is not None:
            _reject(
                accession.amendment_purpose_category not in _AMENDMENT_PURPOSE_CATEGORIES,
                f"unrecognized amendment purpose category on {dashed!r}: "
                f"{accession.amendment_purpose_category!r}",
            )
        _reject(
            accession.has_inline_xbrl and not accession.has_xbrl,
            f"has_inline_xbrl without has_xbrl is contradictory on {dashed!r}",
        )
        _reject(
            any(not cik.isdigit() for cik in registrants),
            f"non-canonical registrant CIK rendering on {dashed!r}: {registrants!r}",
        )
    return pool


def _validate_cohort_applicability(accession: AccessionCandidate, dashed: str) -> None:
    """Distinguish pre-study structural inapplicability from missing cohort evidence."""
    _reject(
        accession.cohort_applicability not in ("applies", "pre_study"),
        f"unrecognized cohort applicability on {dashed!r}: {accession.cohort_applicability!r}",
    )
    if accession.cohort_applicability == "pre_study":
        _reject(
            accession.cohort_evidence_level != NOT_APPLICABLE,
            f"pre-study accession {dashed!r} must carry a structurally inapplicable cohort "
            f"evidence level, got {accession.cohort_evidence_level!r}",
        )
        _reject(
            accession.provisional_official_cohort is not None,
            f"pre-study accession {dashed!r} cannot carry a provisional official cohort",
        )
        return
    _reject(
        accession.cohort_evidence_level not in ACCESSION_EVIDENCE_LEVELS,
        f"unrecognized cohort evidence level on {dashed!r}: {accession.cohort_evidence_level!r}",
    )
    _reject(
        accession.cohort_evidence_level == _PROVISIONAL
        and accession.provisional_official_cohort is None,
        f"provisional cohort evidence on {dashed!r} without a resolved cohort value",
    )


def _validate_amendment_applicability(accession: AccessionCandidate, dashed: str) -> None:
    """Amendment-only dimensions exist only on amendments (Decision 018 section 3.4)."""
    if not accession.is_amendment:
        _reject(
            accession.amendment_linkage_state is not None,
            f"amendment_linkage_state on non-amendment {dashed!r}",
        )
        _reject(
            accession.provisional_parent_accession_dashed is not None,
            f"provisional parent on non-amendment {dashed!r}",
        )
        _reject(
            accession.amendment_purpose_category is not None,
            f"amendment purpose category on non-amendment {dashed!r}",
        )
        _reject(
            accession.amendment_purpose_evidence_level != NOT_APPLICABLE,
            f"amendment-purpose evidence on non-amendment {dashed!r} must be structurally "
            f"inapplicable, got {accession.amendment_purpose_evidence_level!r}",
        )
        _reject(
            accession.amendment_linkage_evidence_level != NOT_APPLICABLE,
            f"amendment-linkage evidence on non-amendment {dashed!r} must be structurally "
            f"inapplicable, got {accession.amendment_linkage_evidence_level!r}",
        )
        return
    _reject(
        accession.amendment_linkage_state is None,
        f"amendment {dashed!r} must carry an amendment_linkage_state",
    )
    _reject(
        accession.amendment_linkage_state not in _AMENDMENT_LINKAGE_STATES,
        f"unrecognized amendment_linkage_state on {dashed!r}: "
        f"{accession.amendment_linkage_state!r}",
    )
    _reject(
        accession.amendment_purpose_evidence_level not in AMENDMENT_PURPOSE_EVIDENCE_LEVELS,
        f"unrecognized amendment-purpose evidence level on {dashed!r}: "
        f"{accession.amendment_purpose_evidence_level!r}",
    )
    _reject(
        accession.amendment_linkage_evidence_level not in ACCESSION_EVIDENCE_LEVELS,
        f"unrecognized amendment-linkage evidence level on {dashed!r}: "
        f"{accession.amendment_linkage_evidence_level!r}",
    )
    parent = accession.provisional_parent_accession_dashed
    if parent is not None:
        _reject(
            _DASHED_ACCESSION_PATTERN.match(parent) is None,
            f"malformed provisional parent accession on {dashed!r}: {parent!r}",
        )


def _validate_multi_registrant_applicability(accession: AccessionCandidate, dashed: str) -> None:
    if accession.multi_registrant:
        _reject(
            accession.multi_registrant_evidence_level not in ACCESSION_EVIDENCE_LEVELS,
            f"unrecognized multi-registrant evidence level on {dashed!r}: "
            f"{accession.multi_registrant_evidence_level!r}",
        )
        return
    _reject(
        accession.multi_registrant_evidence_level != NOT_APPLICABLE,
        f"multi-registrant evidence on a single-registrant accession {dashed!r} must be "
        f"structurally inapplicable, got {accession.multi_registrant_evidence_level!r}",
    )


# --------------------------------------------------------------------------
# Policy function: applicability-aware accession evidence penalty
# --------------------------------------------------------------------------


def accession_evidence_penalty(accession: AccessionCandidate) -> int:
    """Return the applicability-aware accession evidence penalty (Decision 018 section 3.4).

    Each *applicable* dimension contributes ``0`` at ``provisional`` and ``1``
    when weaker than ``provisional``; a structurally inapplicable dimension
    contributes ``0``. The applicable dimensions are filing date (always), cohort
    (only where a study cohort applies), XBRL (always), and amendment purpose and
    amendment linkage (only on an amendment).

    Structural inapplicability is not a penalty: a valid pre-study 2009 support
    accession receives **no** cohort penalty merely because its cohort columns are
    unavailable. The return value is a plain non-negative ``int``; no
    floating-point value appears anywhere in its computation (section 3.2).
    """
    penalty = 0
    if accession.filing_date_evidence_level != _PROVISIONAL:
        penalty += 1
    if accession.xbrl_evidence_level != _PROVISIONAL:
        penalty += 1
    if accession.cohort_applicability == "applies" and accession.cohort_evidence_level != (
        _PROVISIONAL
    ):
        penalty += 1
    if accession.is_amendment:
        if accession.amendment_purpose_evidence_level != _PROVISIONAL:
            penalty += 1
        if accession.amendment_linkage_evidence_level != _PROVISIONAL:
            penalty += 1
    return penalty


# --------------------------------------------------------------------------
# Policy function: accession role assignment
# --------------------------------------------------------------------------


def assign_accession_role(
    accession: AccessionCandidate,
    *,
    anchor_category: str,
    filing_year: int | None,
) -> tuple[AccessionRole | None, str]:
    """Assign the single mutually exclusive accession role (Decision 018 section 7).

    Total and deterministic: it returns exactly one role, or ``None`` with a
    diagnostic reason when the accession's frozen attributes map to zero or to
    more than one role. An unclassifiable accession is a candidate-level failure
    -- it is simply not selectable (section 28) -- never a run-level failure.

    Role is a function of the accession's own frozen attributes and its anchor
    entity's category, never of which quota it happens to serve, so role
    assignment can never be used to move an accession between objective terms 3
    and 4.
    """
    if anchor_category == "control":
        if (
            not accession.is_amendment
            and accession.form_type in ORIGINAL_ANNUAL_FORMS
            and accession.control_eligible
        ):
            return "control", ""
        return None, "role_unclassified_no_match"
    if anchor_category != "operating":
        return None, "unrecognized_anchor_category"

    matches: list[AccessionRole] = []
    is_original_annual_report = (
        not accession.is_amendment and accession.form_type == _ANNUAL_REPORT_FORM
    )
    if (
        is_original_annual_report
        and filing_year == _SUPPORT_FILING_YEAR
        and accession.support_eligible
        and accession.cohort_applicability == "pre_study"
    ):
        matches.append("support")
    if is_original_annual_report and accession.base_eligible:
        matches.append("base")
    if accession.form_type in STRESS_FORMS and accession.stress_eligible:
        matches.append("stress")

    if len(matches) == 1:
        return matches[0], ""
    if not matches:
        return None, "role_unclassified_no_match"
    return None, "role_unclassified_multiple_match"


# --------------------------------------------------------------------------
# Policy function: amendment families
# --------------------------------------------------------------------------


def derive_amendment_families(
    accessions: Sequence[AccessionCandidate],
) -> tuple[tuple[AmendmentFamily, ...], tuple[int | None, ...]]:
    """Derive amendment families and each accession's resolved root original index.

    The result is independent of input ordering: parentage is resolved by dashed
    accession identity, and families and members are emitted in sorted order. A
    parentage cycle, an absent parent pointer, and a parent that is not in the
    pool all fail closed to an unresolved singleton family, which can never
    satisfy linked-amendment coverage (Decision 018 section 10.2).
    """
    index_by_dashed = {a.accession_number_dashed: i for i, a in enumerate(accessions)}
    roots: list[int | None] = [None] * len(accessions)
    reasons: list[str] = [""] * len(accessions)

    for i, accession in enumerate(accessions):
        if not accession.is_amendment:
            roots[i] = i
            continue
        seen: set[int] = {i}
        cursor = i
        reason = "unresolved_parent"
        while True:
            parent_dashed = accessions[cursor].provisional_parent_accession_dashed
            if parent_dashed is None:
                break
            parent_index = index_by_dashed.get(parent_dashed)
            if parent_index is None:
                reason = "parent_not_in_pool"
                break
            if parent_index in seen:
                reason = "parent_cycle"
                break
            seen.add(parent_index)
            if not accessions[parent_index].is_amendment:
                roots[i] = parent_index
                reason = ""
                break
            cursor = parent_index
        reasons[i] = reason

    members_by_root: dict[str, list[str]] = {}
    resolved_by_root: dict[str, bool] = {}
    reason_by_root: dict[str, str] = {}
    for i, accession in enumerate(accessions):
        root_index = roots[i]
        if root_index is None:
            family_id = accession.accession_number_dashed
            members_by_root.setdefault(family_id, []).append(accession.accession_number_dashed)
            resolved_by_root[family_id] = False
            reason_by_root[family_id] = reasons[i]
            continue
        family_id = accessions[root_index].accession_number_dashed
        members_by_root.setdefault(family_id, []).append(accession.accession_number_dashed)
        resolved_by_root.setdefault(family_id, True)
        reason_by_root.setdefault(family_id, "")

    families = tuple(
        AmendmentFamily(
            family_id=family_id,
            members=tuple(sorted(members_by_root[family_id])),
            resolved=resolved_by_root[family_id],
            reason=reason_by_root[family_id],
        )
        for family_id in sorted(members_by_root)
    )
    return families, tuple(roots)


# --------------------------------------------------------------------------
# Quota contribution model
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _Witness:
    """One way a contribution unit can be achieved: every member must be selected."""

    unit: str
    members: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class _PoolContext:
    """Everything derived once from the validated candidate pool."""

    accessions: tuple[AccessionCandidate, ...]
    penalties: tuple[int, ...]
    #: **Decision 083 R60.** Per accession, what occupies the tie-break registrant slot:
    #: a padded CIK for a sole substantive registrant, or the non-CIK sentinel. Used for
    #: hashing and deterministic ordering, **never** as an entity reference.
    slots: tuple[str, ...]
    #: **Decision 083 R58/R62.** Per accession, the complete substantive association set
    #: as sorted padded CIKs. This -- not a scalar -- is the attachment domain: history,
    #: eligibility, role assignment, and every entity-domain quota read it.
    registrants: tuple[tuple[str, ...], ...]
    hashes: tuple[str, ...]
    filing_years: tuple[int | None, ...]
    report_dates: tuple[date | None, ...]
    is_original_annual: tuple[bool, ...]
    root_index: tuple[int | None, ...]
    families: tuple[AmendmentFamily, ...]
    role_if_operating: tuple[AccessionRole | None, ...]
    role_if_control: tuple[AccessionRole | None, ...]
    role_reason: tuple[str, ...]


def _build_pool_context(
    accessions: tuple[AccessionCandidate, ...],
    selection_seed: str,
) -> _PoolContext:
    families, roots = derive_amendment_families(accessions)
    filing_years: list[int | None] = []
    report_dates: list[date | None] = []
    for accession in accessions:
        filing_years.append(official_filing_year(accession.official_filing_date))
        report_dates.append(_parse_iso_date(accession.report_date))

    role_if_operating: list[AccessionRole | None] = []
    role_if_control: list[AccessionRole | None] = []
    role_reason: list[str] = []
    for i, accession in enumerate(accessions):
        operating_role, operating_reason = assign_accession_role(
            accession, anchor_category="operating", filing_year=filing_years[i]
        )
        control_role, _ = assign_accession_role(
            accession, anchor_category="control", filing_year=filing_years[i]
        )
        role_if_operating.append(operating_role)
        role_if_control.append(control_role)
        role_reason.append(operating_reason)

    return _PoolContext(
        accessions=accessions,
        penalties=tuple(accession_evidence_penalty(a) for a in accessions),
        slots=tuple(a.registrant_slot for a in accessions),
        registrants=tuple(a.substantive_registrants_padded for a in accessions),
        hashes=tuple(
            accession_selection_rank(a.registrant_slot, a.accession_number_dashed, selection_seed)
            for a in accessions
        ),
        filing_years=tuple(filing_years),
        report_dates=tuple(report_dates),
        is_original_annual=tuple(
            (not a.is_amendment) and a.form_type in ORIGINAL_ANNUAL_FORMS for a in accessions
        ),
        root_index=roots,
        families=families,
        role_if_operating=tuple(role_if_operating),
        role_if_control=tuple(role_if_control),
        role_reason=tuple(role_reason),
    )


def _name_change_contributes(evidence: NameChangeEvidence) -> bool:
    """Decision 018 section 13: provisional winning identity evidence, name only.

    A ticker-only claim never contributes at M2.3, and the absence of ticker
    evidence alone is neither a contribution nor a warnable condition.
    """
    return (
        evidence.has_identity_evidence
        and evidence.evidence_role == _WINNING
        and evidence.evidence_level == _PROVISIONAL
        and evidence.former_name_record_parseable
        and evidence.has_prior_current_or_from_to
    )


def _is_support_accession(
    ctx: _PoolContext, i: int, *, assigned_role: AccessionRole | None, require_evidence: bool
) -> bool:
    """Whether accession ``i`` is the 2009 support half of a pair (section 15).

    **The assigned role decides, not the stored eligibility flags.** Decision 018
    section 15 restricts the pair to the ``support`` and ``base`` roles, so a
    control-anchored original carrying ``support_eligible`` alongside
    ``control_eligible`` is assigned the ``control`` role and contributes nothing
    here -- section 11's allowance for controls in cross-cutting quotas does not
    reach a quota whose own definition names the contributing roles.

    Everything else section 15 requires of a support accession -- an original
    10-K, an official filing date in calendar 2009, ``support_eligible``, and
    pre-study provenance placing it outside every study cohort -- is exactly what
    :func:`assign_accession_role` already proved when it returned ``support``.
    Restating those conditions here would be a second, drift-prone copy of role
    classification, so this predicate consults the assigned role instead and adds
    only the affirmative evidence gate.
    """
    if assigned_role != "support":
        return False
    return not require_evidence or (ctx.accessions[i].filing_date_evidence_level == _PROVISIONAL)


def _is_target_accession(
    ctx: _PoolContext, i: int, *, assigned_role: AccessionRole | None, require_evidence: bool
) -> bool:
    """Whether accession ``i`` is the 2010 target half of a pair (section 15).

    The assigned role must be exactly ``base``, which already establishes the
    original 10-K form and ``base_eligible``. The calendar-2010 filing date and
    the ``development`` provisional official cohort are the two section 15
    conditions the role rule does not cover, so they are checked here.
    """
    if assigned_role != "base":
        return False
    a = ctx.accessions[i]
    if (
        ctx.filing_years[i] != _TARGET_FILING_YEAR
        or a.provisional_official_cohort != _TARGET_COHORT
    ):
        return False
    return not require_evidence or (
        a.filing_date_evidence_level == _PROVISIONAL and a.cohort_evidence_level == _PROVISIONAL
    )


def _build_witnesses(
    ctx: _PoolContext,
    available: Sequence[int],
    *,
    assigned_roles: Mapping[int, AccessionRole],
    require_evidence: bool,
) -> dict[str, tuple[_Witness, ...]]:
    """Build every quota's contribution witnesses over the available accessions.

    A quota unit is achieved when at least one of its witnesses is entirely
    selected. Most witnesses are a single accession; the 2009/2010 pair
    (Decision 018 section 15) and linked-amendment coverage (section 10.4) are
    conjunctive, because both require a second accession to be selected in the
    same run.

    ``require_evidence`` distinguishes the affirmative-quota view (Decision 014
    section 1: only ``provisional`` evidence may satisfy an affirmative quota)
    from the structural view used to report ``excluded_pool_count``.

    ``assigned_roles`` carries the single mutually exclusive role
    :func:`assign_accession_role` gave each available accession under its own
    anchor's category. Quotas whose definition names a contributing role -- the
    2009/2010 pair (Decision 018 section 15) -- consult it rather than the stored
    eligibility flags.
    """
    available_set = set(available)
    witnesses: dict[str, list[_Witness]] = {key: [] for key in CROSS_CUTTING_QUOTAS}

    for i in available:
        a = ctx.accessions[i]
        # **Decision 083 R62.** An established multi-registrant accession participates in
        # the filing history of EVERY substantive registrant associated with it -- not one
        # CIK, and not none. Each entity-domain quota below therefore emits one witness per
        # substantive registrant. Accession-domain quotas keep their accession key and are
        # untouched, so one joint filing still counts exactly once there.
        entities = ctx.registrants[i]

        if a.is_amendment:
            root = ctx.root_index[i]
            linkage_ok = (not require_evidence) or (
                a.amendment_linkage_evidence_level == _PROVISIONAL
            )
            if root is not None and root in available_set and linkage_ok:
                for entity in entities:
                    witnesses[QUOTA_KEY_LINKED_AMENDMENT_ENTITIES].append(
                        _Witness(entity, (i, root))
                    )
            if a.amendment_purpose_category is not None and (
                (not require_evidence) or a.amendment_purpose_quota_eligible
            ):
                witnesses[QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES].append(
                    _Witness(a.amendment_purpose_category, (i,))
                )

        if a.form_type in TRANSITION_REPORT_FORMS:
            for entity in entities:
                witnesses[QUOTA_KEY_TRANSITION_REPORT_ENTITIES].append(_Witness(entity, (i,)))

        # Accession-keyed already, and therefore needing no anchor: Decision 013 fixes
        # that an accession satisfies this quota ONCE however many registrants it
        # carries (Decision 082 section 10.11). The hard requirement stays 2 accessions.
        if a.multi_registrant and (
            (not require_evidence) or a.multi_registrant_evidence_level == _PROVISIONAL
        ):
            witnesses[QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS].append(
                _Witness(a.accession_number_dashed, (i,))
            )

        if ctx.is_original_annual[i]:
            xbrl_ok = (not require_evidence) or a.xbrl_evidence_level == _PROVISIONAL
            if xbrl_ok:
                key = (
                    QUOTA_KEY_INLINE_XBRL_ORIGINALS
                    if a.has_inline_xbrl
                    else QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS
                )
                witnesses[key].append(_Witness(a.accession_number_dashed, (i,)))
            filing_ok = (not require_evidence) or a.filing_date_evidence_level == _PROVISIONAL
            if filing_ok and ctx.filing_years[i] == _CURRENT_ORIGINAL_YEAR:
                for entity in entities:
                    witnesses[QUOTA_KEY_ORIGINAL_2024_ENTITIES].append(_Witness(entity, (i,)))
            if filing_ok and ctx.filing_years[i] in _RECENT_ORIGINAL_YEARS:
                for entity in entities:
                    witnesses[QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES].append(_Witness(entity, (i,)))

        # Fiscal-year-end witnesses are an upper-bound model only; the exact rule
        # (Decision 018 section 12) is evaluated on the complete selection.
        if a.form_type in TRANSITION_REPORT_FORMS:
            for entity in entities:
                witnesses[QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES].append(_Witness(entity, (i,)))

    _add_pair_witnesses(
        ctx,
        available,
        witnesses,
        assigned_roles=assigned_roles,
        require_evidence=require_evidence,
    )
    _add_fye_distance_witnesses(ctx, available, witnesses)
    return {key: tuple(values) for key, values in witnesses.items()}


def _add_pair_witnesses(
    ctx: _PoolContext,
    available: Sequence[int],
    witnesses: dict[str, list[_Witness]],
    *,
    assigned_roles: Mapping[int, AccessionRole],
    require_evidence: bool,
) -> None:
    """One ``support``-role 2009 accession plus one ``base``-role 2010 development
    target sharing an anchor CIK.

    Because both halves must carry an operating-only role, a pair is necessarily
    anchored to one selected operating entity, and it contributes once for that
    entity however many qualifying supports or targets it holds.
    """
    supports: dict[str, list[int]] = {}
    targets: dict[str, list[int]] = {}
    for i in available:
        role = assigned_roles.get(i)
        # **Decision 083 R62**: a jointly filed leg belongs to every substantive
        # registrant's history, so each of them may form a pair with its own other leg.
        # The quota still counts DISTINCT entities, so no entity is double-counted.
        if _is_support_accession(ctx, i, assigned_role=role, require_evidence=require_evidence):
            for entity in ctx.registrants[i]:
                supports.setdefault(entity, []).append(i)
        if _is_target_accession(ctx, i, assigned_role=role, require_evidence=require_evidence):
            for entity in ctx.registrants[i]:
                targets.setdefault(entity, []).append(i)
    for anchor in sorted(supports):
        for support_index in supports[anchor]:
            for target_index in targets.get(anchor, ()):
                witnesses[QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES].append(
                    _Witness(anchor, (support_index, target_index))
                )


def _add_fye_distance_witnesses(
    ctx: _PoolContext,
    available: Sequence[int],
    witnesses: dict[str, list[_Witness]],
) -> None:
    """Optimistic upper-bound witnesses for the fiscal-year-end distance branch.

    Any selection whose *consecutive* selected original annual reports differ by
    more than the seven-day circular tolerance necessarily contains some selected
    pair that differs by more than the tolerance, so this pairwise model can never
    understate what a completion could achieve -- which is exactly what a sound
    pruning bound requires. The exact consecutive-pair rule, including its
    fail-closed treatment of missing ``report_date`` values, is applied to the
    complete selection.
    """
    originals_by_anchor: dict[str, list[tuple[date, int]]] = {}
    for i in available:
        report = ctx.report_dates[i]
        if ctx.is_original_annual[i] and report is not None:
            for entity in ctx.registrants[i]:
                originals_by_anchor.setdefault(entity, []).append((report, i))
    for anchor in sorted(originals_by_anchor):
        dated = originals_by_anchor[anchor]
        for position, (first_date, first) in enumerate(dated):
            for second_date, second in dated[position + 1 :]:
                distance = circular_month_day_distance(first_date, second_date)
                if distance > FYE_CIRCULAR_TOLERANCE_DAYS:
                    witnesses[QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES].append(
                        _Witness(anchor, (first, second))
                    )


def _fiscal_year_end_contributions(
    ctx: _PoolContext, chosen: Sequence[int]
) -> dict[str, tuple[int, ...]]:
    """Exact fiscal-year-end contribution over a complete selection (section 12).

    An entity contributes when it has a selected 10-KT or 10-KT/A, or when two
    consecutive selected original annual reports differ by more than the seven-day
    circular month-day tolerance. Missing or invalid required ``report_date``
    values fail closed: an entity with any undated selected original annual report
    makes no distance-rule contribution at all, which also prevents an undated
    filing from creating a false adjacency between two dated ones.

    **This is the single fiscal-year-end contribution rule.** It returns each
    contributing anchor with the selected accessions that establish the
    contribution, so the published ``achieved_count`` and the emitted membership
    (Decision 020 section 6) come from one derivation rather than two. The
    pairwise witnesses :func:`_add_fye_distance_witnesses` builds are an
    optimistic *pruning* bound only and never define a contribution.
    """
    contributing: dict[str, list[int]] = {}
    originals_by_anchor: dict[str, list[tuple[date, str, int]]] = {}
    undated_anchors: set[str] = set()
    for i in chosen:
        # **Decision 083 R62**: a joint filing is part of every substantive registrant's
        # annual-report history, so it enters each of their consecutive-report sequences.
        entities = ctx.registrants[i]
        if ctx.accessions[i].form_type in TRANSITION_REPORT_FORMS:
            for entity in entities:
                contributing.setdefault(entity, []).append(i)
        if ctx.is_original_annual[i]:
            report = ctx.report_dates[i]
            if report is None:
                undated_anchors.update(entities)
            else:
                for entity in entities:
                    originals_by_anchor.setdefault(entity, []).append(
                        (report, ctx.accessions[i].accession_number_dashed, i)
                    )
    for anchor in sorted(originals_by_anchor):
        if anchor in contributing or anchor in undated_anchors:
            continue
        ordered = sorted(originals_by_anchor[anchor])
        members: list[int] = []
        for position in range(len(ordered) - 1):
            distance = circular_month_day_distance(ordered[position][0], ordered[position + 1][0])
            if distance > FYE_CIRCULAR_TOLERANCE_DAYS:
                members.extend((ordered[position][2], ordered[position + 1][2]))
        if members:
            contributing[anchor] = members
    return {anchor: tuple(sorted(set(members))) for anchor, members in contributing.items()}


def _fiscal_year_end_entities(ctx: _PoolContext, chosen: Sequence[int]) -> set[str]:
    """The contributing anchors of :func:`_fiscal_year_end_contributions`.

    A projection of that single rule, kept so callers that need only the entity
    set do not carry the member detail.
    """
    return set(_fiscal_year_end_contributions(ctx, chosen))


def _achieved_unit_members(
    witnesses: Sequence[_Witness], present: Sequence[bool]
) -> dict[str, tuple[int, ...]]:
    """Every achieved unit with the accessions that achieve it.

    A unit is achieved when at least one of its witnesses is entirely selected --
    the same predicate :func:`_count_units` applies -- and its members are the
    **union** of every satisfying witness's members. Taking the union rather than
    the first satisfying witness is what makes the emitted membership independent
    of candidate input order, which a first-match rule would not be.
    """
    achieved: dict[str, set[int]] = {}
    for witness in witnesses:
        if all(present[member] for member in witness.members):
            achieved.setdefault(witness.unit, set()).update(witness.members)
    return {unit: tuple(sorted(members)) for unit, members in achieved.items()}


def _attached_category(
    registrants: Sequence[str], category_by_cik: Mapping[str, str | None]
) -> str | None:
    """The single candidate category an accession's attached registrants agree on.

    **Decision 083 R62** attaches an accession to every substantive registrant, so an
    accession can reach more than one entity. Decision 018's role model assigns each
    accession exactly one mutually exclusive role, chosen by its entity's category,
    and that stays true here.

    Two entities of the *same* category leave the role well defined. Entities of
    *different* categories do not, and there is no non-arbitrary way to prefer one --
    picking either would be exactly the kind of unjustified primacy **R58**
    prohibits. That case therefore returns ``None`` and the accession is simply not
    available: **fail closed, order-independent, and inventing nothing.**
    """
    categories = {
        category_by_cik[cik] for cik in registrants if category_by_cik.get(cik) is not None
    }
    if len(categories) != 1:
        return None
    return categories.pop()


def _accession_member(
    ctx: _PoolContext, index: int, selected_ciks: Collection[str]
) -> QuotaContributionMember:
    """One accession member, carrying the substantive registrants that are selected.

    ``cik_padded`` is the anchor when one lawfully exists and ``None`` otherwise
    (**Decision 083 R58**); the association set is what the entity-level projection
    reads either way, so nothing depends on a fabricated anchor.

    The set is narrowed to **selected** entities on purpose. Membership is a property
    of a selection, and ``pilot_selected_entity_quota_contributions`` is keyed on
    selected entities: a co-registrant the accepted index names but that this run never
    selected has no row to contribute to. **Decision 083 R62** lets each truthful
    substantive entity participate *according to that metric's existing definition*, and
    this metric's existing definition is per selected entity. For a sole-registrant
    accession the narrowing is a no-op -- an accession is only available when its
    attached registrants are in the entity set -- so every pre-correction contribution is
    reproduced exactly.
    """
    return QuotaContributionMember(
        member_kind="accession",
        cik_padded=ctx.accessions[index].anchor_cik_padded,
        accession_plain=ctx.accessions[index].accession_plain,
        registrant_ciks_padded=tuple(cik for cik in ctx.registrants[index] if cik in selected_ciks),
    )


def _derive_membership(
    ctx: _PoolContext,
    entity_pool: Sequence[EntityCandidate],
    *,
    selected_entity_ciks: Iterable[str],
    selected_accession_plains: Iterable[str],
) -> QuotaContributionMembership:
    """Build the membership artifact for one selected entity and accession set.

    Every quota's membership comes from the accepted rule that already decides
    that quota's achieved count: the witness model for the nine witness-derived
    cross-cutting quotas, :func:`_fiscal_year_end_contributions` for the
    fiscal-year-end quota whose witnesses are only a pruning bound, and
    :func:`_name_change_contributes` for the purely entity-level name-change
    quota. Nothing here re-expresses a contribution rule (Decision 018 section 19).

    Raises:
        ValueError: a selected identity that is not in the candidate pool.
    """
    entity_by_cik = {entry.cik_padded: entry for entry in entity_pool}
    selected_ciks: list[str] = []
    for cik in selected_entity_ciks:
        if cik not in entity_by_cik:
            message = f"selected CIK {cik!r} is not in the candidate entity pool"
            raise ValueError(message)
        selected_ciks.append(cik)
    category_by_cik = {cik: entity_by_cik[cik].candidate.category for cik in selected_ciks}

    index_by_plain = {a.accession_plain: i for i, a in enumerate(ctx.accessions)}
    chosen: list[int] = []
    for plain in selected_accession_plains:
        index = index_by_plain.get(plain)
        if index is None:
            message = f"selected accession {plain!r} is not in the candidate accession pool"
            raise ValueError(message)
        chosen.append(index)
    chosen.sort()

    assigned_roles: dict[int, AccessionRole] = {}
    for index in chosen:
        category = _attached_category(ctx.registrants[index], category_by_cik)
        role: AccessionRole | None
        if category == "operating":
            role = ctx.role_if_operating[index]
        elif category == "control":
            role = ctx.role_if_control[index]
        else:
            role = None
        if role is not None:
            assigned_roles[index] = role

    witnesses = _build_witnesses(ctx, chosen, assigned_roles=assigned_roles, require_evidence=True)
    present = [False] * len(ctx.accessions)
    for index in chosen:
        present[index] = True

    units: list[QuotaContributionUnit] = []
    for key in CROSS_CUTTING_QUOTAS:
        members_by_unit: Mapping[str, tuple[int, ...]]
        if key == QUOTA_KEY_NAME_CHANGE_ENTITIES:
            members_by_unit = {
                cik: ()
                for cik in selected_ciks
                if _name_change_contributes(entity_by_cik[cik].name_change)
            }
            entity_units = True
        elif key == QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES:
            members_by_unit = _fiscal_year_end_contributions(ctx, chosen)
            entity_units = False
        else:
            members_by_unit = _achieved_unit_members(witnesses[key], present)
            entity_units = False
        for unit in sorted(members_by_unit):
            members = (
                (QuotaContributionMember("entity", unit, None),)
                if entity_units
                else tuple(
                    _accession_member(ctx, index, selected_ciks) for index in members_by_unit[unit]
                )
            )
            units.append(
                QuotaContributionUnit(
                    dimension=QUOTA_DIMENSION_CROSS_CUTTING,
                    key=key,
                    unit=unit,
                    members=tuple(sorted(members, key=_member_sort_key)),
                )
            )
    units.sort(key=lambda entry: (entry.dimension, entry.key, entry.unit))
    return QuotaContributionMembership(units=tuple(units))


# --------------------------------------------------------------------------
# Search machinery
# --------------------------------------------------------------------------


class _NodeBudget:
    """One shared expanded-node counter across every search phase (section 17)."""

    __slots__ = ("count", "exhausted", "limit")

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.count = 0
        self.exhausted = False

    def expand(self) -> bool:
        """Count one expanded node; ``False`` once the shared budget is exhausted."""
        if self.exhausted:
            return False
        self.count += 1
        if self.count > self.limit:
            self.exhausted = True
            return False
        return True


@dataclass(frozen=True, slots=True)
class _AccessionSolution:
    """The per-entity-set optimum of the accession-only objective prefix."""

    chosen: tuple[int, ...]
    penalty: int
    base_count: int
    stress_count: int
    hash_vector: tuple[str, ...]
    identity_vector: tuple[str, ...]

    def key(self) -> tuple[int, int, int, tuple[str, ...], tuple[str, ...]]:
        return (
            self.penalty,
            self.base_count,
            self.stress_count,
            self.hash_vector,
            self.identity_vector,
        )


@dataclass(frozen=True, slots=True)
class _Subproblem:
    """The accession subproblem induced by one complete entity set."""

    order: tuple[int, ...]
    roles: tuple[AccessionRole, ...]
    penalties: tuple[int, ...]
    #: **Decision 083 R62.** Per ordered position, every *selected* substantive
    #: registrant the accession attaches to. One entry for a sole-registrant accession;
    #: several for a joint filing, which really is part of each of their histories.
    attachments: tuple[tuple[str, ...], ...]
    hashes: tuple[str, ...]
    identities: tuple[str, ...]
    base_positions_by_cik: Mapping[str, tuple[int, ...]]
    control_positions_by_cik: Mapping[str, tuple[int, ...]]
    positions_by_cik: Mapping[str, tuple[int, ...]]
    witnesses: Mapping[str, tuple[_Witness, ...]]
    operating_ciks: tuple[str, ...]
    control_ciks: tuple[str, ...]
    requirements: Mapping[str, int]


def _selected_order_key(ctx: _PoolContext, index: int) -> tuple[str, str, str]:
    """Decision 018 section 4: tie-break hash, then registrant slot, then dashed accession.

    Role, entity ``selected_order``, amendment family, and associated registrants
    are deliberately absent, so the ordering is a pure function of accession
    identity. The middle component is the **Decision 083 R60** registrant slot, which
    is the anchor CIK exactly when one exists -- so every single-registrant ordering
    is unchanged -- and the non-CIK sentinel otherwise. The sentinel depends only on
    the *cardinality* of the association set, never its membership, so the order is
    invariant to which registrants a joint filing happens to carry.
    """
    return (
        ctx.hashes[index],
        ctx.slots[index],
        ctx.accessions[index].accession_number_dashed,
    )


def _build_subproblem(
    ctx: _PoolContext,
    operating_ciks: frozenset[str],
    control_ciks: frozenset[str],
) -> _Subproblem | None:
    """Induce the accession subproblem for one entity set, or ``None`` if hopeless.

    ``name_change_entities`` is deliberately absent from ``requirements``: it is a
    purely entity-level quota (Decision 018 section 13) and is settled before the
    accession search begins, so no accession choice can affect it.
    """
    category_by_cik: dict[str, str | None] = dict.fromkeys(operating_ciks, "operating")
    category_by_cik.update(dict.fromkeys(control_ciks, "control"))

    available: list[int] = []
    roles: list[AccessionRole] = []
    attached: list[tuple[str, ...]] = []
    for i in range(len(ctx.accessions)):
        # **Decision 083 R62.** An accession is available when at least one of its
        # substantive registrants is in this entity set -- the section 10.11 attachment
        # rule -- and its role comes from the category those attached entities agree on.
        entities = tuple(cik for cik in ctx.registrants[i] if cik in category_by_cik)
        category = _attached_category(entities, category_by_cik)
        role: AccessionRole | None
        if category == "operating":
            role = ctx.role_if_operating[i]
        elif category == "control":
            role = ctx.role_if_control[i]
        else:
            role = None
        if role is not None:
            available.append(i)
            roles.append(role)
            attached.append(entities)

    order_positions = sorted(
        range(len(available)), key=lambda p: _selected_order_key(ctx, available[p])
    )
    order = tuple(available[p] for p in order_positions)
    ordered_roles = tuple(roles[p] for p in order_positions)
    ordered_attachments = tuple(attached[p] for p in order_positions)

    base_positions: dict[str, list[int]] = {cik: [] for cik in operating_ciks}
    control_positions: dict[str, list[int]] = {cik: [] for cik in control_ciks}
    positions_by_cik: dict[str, list[int]] = {cik: [] for cik in operating_ciks | control_ciks}
    for position, _index in enumerate(order):
        for anchor in ordered_attachments[position]:
            positions_by_cik[anchor].append(position)
            if ordered_roles[position] == "base":
                base_positions[anchor].append(position)
            elif ordered_roles[position] == "control":
                control_positions[anchor].append(position)

    if any(not values for values in base_positions.values()):
        return None
    if any(not values for values in control_positions.values()):
        return None
    if any(not values for values in positions_by_cik.values()):
        return None

    position_of = {index: position for position, index in enumerate(order)}
    assigned_roles = dict(zip(order, ordered_roles, strict=True))
    raw_witnesses = _build_witnesses(
        ctx, order, assigned_roles=assigned_roles, require_evidence=True
    )
    witnesses = {
        key: tuple(_Witness(w.unit, tuple(position_of[m] for m in w.members)) for w in values)
        for key, values in raw_witnesses.items()
    }
    requirements = {
        key: required
        for key, required in CROSS_CUTTING_QUOTAS.items()
        if key != QUOTA_KEY_NAME_CHANGE_ENTITIES
    }

    return _Subproblem(
        order=order,
        roles=ordered_roles,
        penalties=tuple(ctx.penalties[i] for i in order),
        attachments=ordered_attachments,
        hashes=tuple(ctx.hashes[i] for i in order),
        identities=tuple(ctx.accessions[i].accession_number_dashed for i in order),
        base_positions_by_cik={k: tuple(v) for k, v in base_positions.items()},
        control_positions_by_cik={k: tuple(v) for k, v in control_positions.items()},
        positions_by_cik={k: tuple(v) for k, v in positions_by_cik.items()},
        witnesses=witnesses,
        operating_ciks=tuple(sorted(operating_ciks)),
        control_ciks=tuple(sorted(control_ciks)),
        requirements=requirements,
    )


def _count_units(witnesses: Sequence[_Witness], present: Sequence[bool]) -> int:
    units: set[str] = set()
    for witness in witnesses:
        if witness.unit in units:
            continue
        if all(present[member] for member in witness.members):
            units.add(witness.unit)
    return len(units)


def _solve_accessions(
    ctx: _PoolContext,
    sub: _Subproblem,
    budget: _NodeBudget,
) -> _AccessionSolution | None:
    """Exact lexicographic minimum of ``(penalty, base, stress, hashes, identities)``.

    Deterministic depth-first branch-and-bound over the accessions in the frozen
    Decision 018 section 4 order, exclude-branch first. Every prune is a sound
    bound:

    * a cap violation makes the include branch infeasible outright (section 8);
    * ``(penalty, base, stress)`` are monotone non-decreasing as accessions are
      added, so a running prefix that already exceeds the incumbent's prefix
      lexicographically can never complete to a better solution;
    * a floor or quota whose achievable upper bound over ``selected + suffix``
      falls short of its requirement can never be met by any completion
      (sections 9 and 16).

    The hash and identity vectors are compared only at complete leaves, so no
    heuristic ordering can discard the optimum.
    """
    n = len(sub.order)
    chosen_flags = [False] * n
    reachable_flags = [False] * n
    chosen: list[int] = []
    base_by_cik: dict[str, int] = dict.fromkeys(sub.operating_ciks, 0)
    best: _AccessionSolution | None = None

    def bound_present(i: int) -> list[bool]:
        for position in range(n):
            reachable_flags[position] = chosen_flags[position] or position >= i
        return reachable_flags

    def reachable(i: int) -> bool:
        present = bound_present(i)
        for cik in sub.operating_ciks:
            if not any(present[p] for p in sub.base_positions_by_cik[cik]):
                return False
        for cik in sub.control_ciks:
            if not any(present[p] for p in sub.control_positions_by_cik[cik]):
                return False
        for positions in sub.positions_by_cik.values():
            if not any(present[p] for p in positions):
                return False
        for key, required in sub.requirements.items():
            if required > 0 and _count_units(sub.witnesses[key], present) < required:
                return False
        return True

    def leaf_solution() -> _AccessionSolution | None:
        present = [False] * n
        for position in chosen:
            present[position] = True
        for cik in sub.operating_ciks:
            if not any(present[p] for p in sub.base_positions_by_cik[cik]):
                return None
        for cik in sub.control_ciks:
            if not any(present[p] for p in sub.control_positions_by_cik[cik]):
                return None
        for positions in sub.positions_by_cik.values():
            if not any(present[p] for p in positions):
                return None
        achieved_fye = _fiscal_year_end_entities(ctx, [sub.order[p] for p in chosen])
        for key, required in sub.requirements.items():
            if required <= 0:
                continue
            if key == QUOTA_KEY_FISCAL_YEAR_END_CHANGE_ENTITIES:
                if len(achieved_fye) < required:
                    return None
                continue
            if _count_units(sub.witnesses[key], present) < required:
                return None
        penalty = sum(sub.penalties[p] for p in chosen)
        base_count = sum(1 for p in chosen if sub.roles[p] == "base")
        stress_count = sum(1 for p in chosen if sub.roles[p] == "stress")
        return _AccessionSolution(
            chosen=tuple(sorted(chosen)),
            penalty=penalty,
            base_count=base_count,
            stress_count=stress_count,
            hash_vector=tuple(sorted(sub.hashes[p] for p in chosen)),
            identity_vector=tuple(sorted(sub.identities[p] for p in chosen)),
        )

    def dfs(
        i: int, penalty: int, base_count: int, stress_count: int, max_base_per_cik: int
    ) -> None:
        nonlocal best
        if not budget.expand():
            return
        if best is not None and (penalty, base_count, stress_count) > (
            best.penalty,
            best.base_count,
            best.stress_count,
        ):
            return
        if i == n:
            solution = leaf_solution()
            if solution is not None and (best is None or solution.key() < best.key()):
                best = solution
            return
        if not reachable(i):
            return

        dfs(i + 1, penalty, base_count, stress_count, max_base_per_cik)
        if budget.exhausted:
            return

        role = sub.roles[i]
        # **Decision 083 R62.** A joint base filing counts toward the per-CIK base cap
        # of every substantive registrant it attaches to -- the cap is entity-domain,
        # and each of them genuinely filed it. Only those CIKs' counts can change here,
        # so the new per-CIK maximum is the old maximum or one of their incremented
        # counts -- still exact, and O(attachments).
        attachments = sub.attachments[i]
        next_max_base_per_cik = (
            max(max_base_per_cik, *(base_by_cik[cik] + 1 for cik in attachments))
            if role == "base" and attachments
            else max_base_per_cik
        )
        prospective = AccessionCapUsage(
            base_total=base_count + (1 if role == "base" else 0),
            stress_total=stress_count + (1 if role == "stress" else 0),
            accession_total=len(chosen) + 1,
            max_base_per_cik=next_max_base_per_cik,
        )
        if not accession_caps_satisfied(prospective):
            return

        chosen_flags[i] = True
        chosen.append(i)
        if role == "base":
            for cik in attachments:
                base_by_cik[cik] += 1
        dfs(
            i + 1,
            penalty + sub.penalties[i],
            prospective.base_total,
            prospective.stress_total,
            next_max_base_per_cik,
        )
        if role == "base":
            for cik in attachments:
                base_by_cik[cik] -= 1
        chosen.pop()
        chosen_flags[i] = False

    dfs(0, 0, 0, 0, 0)
    if budget.exhausted:
        return None
    return best


@dataclass(frozen=True, slots=True)
class _Incumbent:
    """One complete joint candidate solution and its full objective tuple."""

    operating: tuple[Candidate, ...]
    controls: tuple[Candidate, ...]
    objective: JointObjective
    accession_indices: tuple[int, ...]
    accession_roles: Mapping[int, AccessionRole]

    def key(
        self,
    ) -> tuple[int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return self.objective.as_tuple()


def _entity_hash_vector(entities: Iterable[Candidate], selection_seed: str) -> tuple[str, ...]:
    return tuple(sorted(selection_rank(c.cik_padded, selection_seed) for c in entities))


def _build_min_suffix_penalty(
    order: Sequence[Candidate], unreachable: int
) -> tuple[tuple[int, ...], ...]:
    """``table[i][k]``: the minimum entity penalty of any ``k``-subset of ``order[i:]``.

    Quota-respecting completions are a subset of all ``k``-subsets, so this
    minimum never overstates the cheapest reachable completion; pruning on it can
    never discard a branch that could still improve on the incumbent. This is the
    accepted S4.1 admissibility argument, applied to the entity prefix of the
    joint objective.
    """
    n = len(order)
    table: list[tuple[int, ...]] = [()] * (n + 1)
    table[n] = tuple([0] + [unreachable] * TOTAL_OPERATING)
    for i in range(n - 1, -1, -1):
        penalty = order[i].evidence_penalty
        nxt = table[i + 1]
        current = [0]
        for k in range(1, TOTAL_OPERATING + 1):
            take = penalty + nxt[k - 1]
            best = nxt[k] if nxt[k] < take else take
            current.append(best if best < unreachable else unreachable)
        table[i] = tuple(current)
    return tuple(table)


@dataclass(frozen=True, slots=True)
class _SuffixCapacity:
    """Suffix quota-reachability counters for the fixed operating ordering."""

    total: tuple[int, ...]
    size: Mapping[str, tuple[int, ...]]
    industry: Mapping[str, tuple[int, ...]]
    history: Mapping[str, tuple[int, ...]]
    inactive: tuple[int, ...]

    def reachable(
        self,
        i: int,
        remaining_slots: int,
        need_size: Mapping[str, int],
        need_industry: Mapping[str, int],
        need_history: Mapping[str, int],
        inactive_selected: int,
    ) -> bool:
        """Whether the suffix at ``i`` could still cover every outstanding need."""
        if remaining_slots < 0 or self.total[i] < remaining_slots:
            return False
        for key, still_needed in need_size.items():
            if still_needed > self.size[key][i]:
                return False
        for key, still_needed in need_industry.items():
            if still_needed > self.industry[key][i]:
                return False
        for key, still_needed in need_history.items():
            if still_needed > self.history[key][i]:
                return False
        return inactive_selected + self.inactive[i] >= MIN_INACTIVE_EVENTFUL


def _build_suffix_capacity(order: Sequence[Candidate]) -> _SuffixCapacity:
    n = len(order)
    total = [0] * (n + 1)
    size = {key: [0] * (n + 1) for key in SIZE_QUOTAS}
    industry = {key: [0] * (n + 1) for key in INDUSTRY_QUOTAS}
    history = {key: [0] * (n + 1) for key in HISTORY_QUOTAS}
    inactive = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        c = order[i]
        total[i] = total[i + 1] + 1
        for key in SIZE_QUOTAS:
            size[key][i] = size[key][i + 1] + (1 if c.size_stratum == key else 0)
        for key in INDUSTRY_QUOTAS:
            industry[key][i] = industry[key][i + 1] + (1 if c.industry_group == key else 0)
        for key in HISTORY_QUOTAS:
            history[key][i] = history[key][i + 1] + (1 if c.history_class == key else 0)
        inactive[i] = inactive[i + 1] + (
            1 if c.history_class == "eventful" and c.currently_inactive else 0
        )
    return _SuffixCapacity(
        total=tuple(total),
        size={key: tuple(values) for key, values in size.items()},
        industry={key: tuple(values) for key, values in industry.items()},
        history={key: tuple(values) for key, values in history.items()},
        inactive=tuple(inactive),
    )


def _search_joint(
    ctx: _PoolContext,
    operating_eligible: Sequence[Candidate],
    control_eligible_by_kind: Mapping[str, list[Candidate]],
    name_change_by_cik: Mapping[str, bool],
    selection_seed: str,
    budget: _NodeBudget,
) -> _Incumbent | None:
    """Deterministic branch-and-bound over the joint entity-accession problem.

    Entities are never fixed first: every complete entity set is scored by the
    *joint* key, whose first component is the single Decision 018 section 3.2
    integer over selected entities **and** selected accessions. Because that
    component and the base/stress counts precede the entity-hash vector, the
    entity set this search returns may legitimately differ from the accepted S4
    entity-only optimum.
    """
    incumbent: _Incumbent | None = None
    n = len(operating_eligible)
    if n < TOTAL_OPERATING:
        return None

    unreachable = sum(c.evidence_penalty for c in operating_eligible) + 1
    order = tuple(sorted(operating_eligible, key=lambda c: _rank_key(c, selection_seed)))
    capacity = _build_suffix_capacity(order)
    penalty_bound = _build_min_suffix_penalty(order, unreachable)

    control_kinds = tuple(CONTROL_QUOTAS)
    control_options = {
        kind: tuple(
            sorted(control_eligible_by_kind[kind], key=lambda c: _rank_key(c, selection_seed))
        )
        for kind in control_kinds
    }
    if any(not control_options[kind] for kind in control_kinds):
        return None
    min_control_penalty = sum(
        min(c.evidence_penalty for c in control_options[kind]) for kind in control_kinds
    )

    def evaluate(operating: tuple[Candidate, ...], controls: tuple[Candidate, ...]) -> None:
        nonlocal incumbent
        if not budget.expand():
            return
        entity_penalty = sum(c.evidence_penalty for c in operating) + sum(
            c.evidence_penalty for c in controls
        )
        if incumbent is not None and entity_penalty > incumbent.objective.evidence_penalty:
            return
        selected = operating + controls
        name_change_achieved = sum(1 for c in selected if name_change_by_cik[c.cik_padded])
        if name_change_achieved < CROSS_CUTTING_QUOTAS[QUOTA_KEY_NAME_CHANGE_ENTITIES]:
            return
        sub = _build_subproblem(
            ctx,
            frozenset(c.cik_padded for c in operating),
            frozenset(c.cik_padded for c in controls),
        )
        if sub is None:
            return
        solution = _solve_accessions(ctx, sub, budget)
        if solution is None:
            return
        objective = JointObjective(
            evidence_penalty=entity_penalty + solution.penalty,
            base_accession_count=solution.base_count,
            stress_accession_count=solution.stress_count,
            entity_hash_vector=_entity_hash_vector(selected, selection_seed),
            accession_hash_vector=solution.hash_vector,
            entity_identity_vector=tuple(sorted(c.cik_padded for c in selected)),
            accession_identity_vector=solution.identity_vector,
        )
        indices = tuple(sub.order[p] for p in solution.chosen)
        roles = {sub.order[p]: sub.roles[p] for p in solution.chosen}
        candidate = _Incumbent(
            operating=operating,
            controls=controls,
            objective=objective,
            accession_indices=indices,
            accession_roles=roles,
        )
        if incumbent is None or candidate.key() < incumbent.key():
            incumbent = candidate

    def dfs_controls(
        kind_index: int, operating: tuple[Candidate, ...], controls: tuple[Candidate, ...]
    ) -> None:
        if not budget.expand():
            return
        if kind_index == len(control_kinds):
            evaluate(operating, controls)
            return
        for option in control_options[control_kinds[kind_index]]:
            dfs_controls(kind_index + 1, operating, (*controls, option))
            if budget.exhausted:
                return

    def admissible_bucket(
        candidate: Candidate,
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
    ) -> tuple[str, str, str] | None:
        size_key = candidate.size_stratum
        industry_key = candidate.industry_group
        history_key = candidate.history_class
        if (
            size_key is not None
            and industry_key is not None
            and history_key is not None
            and need_size[size_key] > 0
            and need_industry[industry_key] > 0
            and need_history[history_key] > 0
        ):
            return size_key, industry_key, history_key
        return None

    def dfs_operating(
        i: int,
        chosen: list[Candidate],
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
        inactive_selected: int,
        running_penalty: int,
    ) -> None:
        if not budget.expand():
            return
        remaining_slots = TOTAL_OPERATING - len(chosen)
        if remaining_slots == 0:
            if (
                all(v == 0 for v in need_size.values())
                and all(v == 0 for v in need_industry.values())
                and all(v == 0 for v in need_history.values())
                and inactive_selected >= MIN_INACTIVE_EVENTFUL
            ):
                dfs_controls(0, tuple(chosen), ())
            return
        if i >= n:
            return
        if not capacity.reachable(
            i, remaining_slots, need_size, need_industry, need_history, inactive_selected
        ):
            return
        if incumbent is not None:
            lower_bound = running_penalty + penalty_bound[i][remaining_slots] + min_control_penalty
            if lower_bound > incumbent.objective.evidence_penalty:
                return

        candidate = order[i]
        bucket = admissible_bucket(candidate, need_size, need_industry, need_history)
        if bucket is not None:
            size_key, industry_key, history_key = bucket
            need_size[size_key] -= 1
            need_industry[industry_key] -= 1
            need_history[history_key] -= 1
            chosen.append(candidate)
            dfs_operating(
                i + 1,
                chosen,
                need_size,
                need_industry,
                need_history,
                inactive_selected
                + (1 if history_key == "eventful" and candidate.currently_inactive else 0),
                running_penalty + candidate.evidence_penalty,
            )
            chosen.pop()
            need_size[size_key] += 1
            need_industry[industry_key] += 1
            need_history[history_key] += 1
            if budget.exhausted:
                return

        dfs_operating(
            i + 1,
            chosen,
            need_size,
            need_industry,
            need_history,
            inactive_selected,
            running_penalty,
        )

    dfs_operating(0, [], dict(SIZE_QUOTAS), dict(INDUSTRY_QUOTAS), dict(HISTORY_QUOTAS), 0, 0)
    if budget.exhausted:
        return None
    return incumbent


# --------------------------------------------------------------------------
# Diagnostics
# --------------------------------------------------------------------------


def _deferred_quota_diagnostic() -> AccessionQuotaDiagnostic:
    """Decision 018 section 14's controlled deferral, reported on every run.

    Never satisfied, never proxied, never binding: ``unproven`` with evidence
    state ``unavailable``, ``achieved_count = 0``, ``eligible_pool_count = 0``.
    It remains a mandatory M2.5 verification obligation, and a feasible run is
    still reachable with it outstanding. The values do not depend on run status,
    because the deferral is unconditional at M2.3.
    """
    return AccessionQuotaDiagnostic(
        dimension=QUOTA_DIMENSION_CROSS_CUTTING,
        key=DEFERRED_QUOTA_KEY,
        comparison_operator="at_least",
        required_count=DEFERRED_QUOTA_REQUIRED_COUNT,
        available_eligible_count=0,
        achieved_count=0,
        status="unproven",
        binding_constraint=False,
        excluded_pool_count=0,
        evidence_state="unavailable",
        deferred=True,
    )


def _candidate_quota_gates(
    ctx: _PoolContext,
    index: int,
    eligible: frozenset[int],
    assigned_roles: Mapping[int, AccessionRole],
) -> tuple[tuple[str, bool], ...]:
    """Yield ``(quota_key, affirmative_evidence_ok)`` for each quota whose
    *structural* predicate this candidate accession matches.

    Structural means the accession is the right kind of thing for the quota,
    ignoring evidence; the second element is whether it also clears the
    affirmative evidence gate Decision 014 section 1 requires. A quota with no
    affirmative evidence gate (transition reports and fiscal-year-end changes are
    derived from frozen form and date attributes alone) contributes nothing here,
    because no candidate can match structurally and then fail an evidence test
    that does not exist.
    """
    accession = ctx.accessions[index]
    gates: list[tuple[str, bool]] = []
    if accession.is_amendment:
        root = ctx.root_index[index]
        if root is not None and root in eligible:
            gates.append(
                (
                    QUOTA_KEY_LINKED_AMENDMENT_ENTITIES,
                    accession.amendment_linkage_evidence_level == _PROVISIONAL,
                )
            )
        if accession.amendment_purpose_category is not None:
            gates.append(
                (
                    QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES,
                    accession.amendment_purpose_quota_eligible,
                )
            )
    if accession.multi_registrant:
        gates.append(
            (
                QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS,
                accession.multi_registrant_evidence_level == _PROVISIONAL,
            )
        )
    if ctx.is_original_annual[index]:
        xbrl_ok = accession.xbrl_evidence_level == _PROVISIONAL
        era_key = (
            QUOTA_KEY_INLINE_XBRL_ORIGINALS
            if accession.has_inline_xbrl
            else QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS
        )
        gates.append((era_key, xbrl_ok))
        filing_ok = accession.filing_date_evidence_level == _PROVISIONAL
        if ctx.filing_years[index] == _CURRENT_ORIGINAL_YEAR:
            gates.append((QUOTA_KEY_ORIGINAL_2024_ENTITIES, filing_ok))
        if ctx.filing_years[index] in _RECENT_ORIGINAL_YEARS:
            gates.append((QUOTA_KEY_ORIGINAL_2025_2026_ENTITIES, filing_ok))
    # The pair quota's structural predicate is role-restricted exactly as its
    # feasibility witnesses are, so a control-role accession is neither an
    # available contributor nor an excluded one -- it is not a pair candidate.
    role = assigned_roles.get(index)
    structural_support = _is_support_accession(
        ctx, index, assigned_role=role, require_evidence=False
    )
    structural_target = _is_target_accession(ctx, index, assigned_role=role, require_evidence=False)
    if structural_support or structural_target:
        supports = _is_support_accession(ctx, index, assigned_role=role, require_evidence=True)
        targets = _is_target_accession(ctx, index, assigned_role=role, require_evidence=True)
        gates.append((QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES, supports or targets))
    return tuple(gates)


def _excluded_pool_counts(
    ctx: _PoolContext,
    eligible_positions: Sequence[int],
    assigned_roles: Mapping[int, AccessionRole],
) -> dict[str, int]:
    """Count, per quota, the candidates that match structurally but fail evidence.

    Decision 017 section 2's shape, applied to the accession side: a candidate is
    counted only against the one quota whose structural predicate it actually
    matches, and only when the applicable affirmative evidence gate fails. The
    result is **diagnostic only** -- it feeds no feasibility test, no objective
    component, no eligibility decision, and no deferral.

    Note the deliberate asymmetry with ``available_eligible_count``, which counts
    distinct *contribution units* (entities, accessions, or categories) because
    ``binding_constraint`` compares it against a distinct-unit requirement. This
    count is per *candidate*, which is what Decision 017 section 2 defines and
    what the project owner's ruling restates for accessions.
    """
    eligible = frozenset(eligible_positions)
    counts = dict.fromkeys(CROSS_CUTTING_QUOTAS, 0)
    for index in eligible_positions:
        for quota_key, evidence_ok in _candidate_quota_gates(ctx, index, eligible, assigned_roles):
            if not evidence_ok:
                counts[quota_key] += 1
    return counts


def _build_accession_quota_results(
    ctx: _PoolContext,
    status: JointSelectionStatus,
    eligible_positions: Sequence[int],
    assigned_roles: Mapping[int, AccessionRole],
    name_change_eligible: int,
    name_change_structural: int,
    membership: QuotaContributionMembership,
) -> tuple[AccessionQuotaDiagnostic, ...]:
    """Build one integer-only diagnostic per measurable cross-cutting quota.

    Every ``achieved_count`` is the number of achieved units in ``membership``, so
    the published integer and the emitted quota-contribution membership agree **by
    construction** (Decision 020 section 6). ``available_eligible_count`` and
    ``excluded_pool_count`` remain pool-level diagnostics over the eligible
    candidates and are unchanged.
    """
    strict = _build_witnesses(
        ctx, eligible_positions, assigned_roles=assigned_roles, require_evidence=True
    )
    all_present = [True] * len(ctx.accessions)
    excluded_counts = _excluded_pool_counts(ctx, eligible_positions, assigned_roles)
    excluded_counts[QUOTA_KEY_NAME_CHANGE_ENTITIES] = max(
        0, name_change_structural - name_change_eligible
    )

    results: list[AccessionQuotaDiagnostic] = []
    for key, required in CROSS_CUTTING_QUOTAS.items():
        achieved = membership.achieved_count(QUOTA_DIMENSION_CROSS_CUTTING, key)
        if key == QUOTA_KEY_NAME_CHANGE_ENTITIES:
            available = name_change_eligible
        else:
            available = _count_units(strict[key], all_present)
        results.append(
            AccessionQuotaDiagnostic(
                dimension=QUOTA_DIMENSION_CROSS_CUTTING,
                key=key,
                comparison_operator="at_least",
                required_count=required,
                available_eligible_count=available,
                achieved_count=achieved,
                status=_quota_status(status, achieved, required),
                binding_constraint=available < required,
                excluded_pool_count=excluded_counts[key],
                evidence_state=_PROVISIONAL,
                deferred=False,
            )
        )
    results.append(_deferred_quota_diagnostic())
    return tuple(results)


def _build_cap_quota_results(
    status: JointSelectionStatus, usage: AccessionCapUsage
) -> tuple[AccessionQuotaDiagnostic, ...]:
    """Report the four Decision 018 section 8 caps as ``at_most`` quota outcomes.

    Pass/fail comes from :func:`accession_cap_outcomes` -- the same pure rule the
    joint search enforces -- so a reported cap outcome can never disagree with
    the feasibility decision that produced the selection.

    A cap is only measurable against an approved selection. On any non-feasible
    status there is no selection at all, so the cap is reported ``unproven``
    rather than claiming a vacuous ``pass`` over an empty set.
    """
    results: list[AccessionQuotaDiagnostic] = []
    for key, limit, achieved, satisfied in accession_cap_outcomes(usage):
        measured = "pass" if satisfied else "fail"
        cap_status = "unproven" if status != "feasible" else measured
        results.append(
            AccessionQuotaDiagnostic(
                dimension=QUOTA_DIMENSION_ACCESSION_CAP,
                key=key,
                comparison_operator="at_most",
                required_count=limit,
                available_eligible_count=limit,
                achieved_count=achieved,
                status=cap_status,
                binding_constraint=achieved >= limit,
                excluded_pool_count=0,
                evidence_state=_PROVISIONAL,
                deferred=False,
            )
        )
    return tuple(results)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def solve_joint_selection(
    entities: Iterable[EntityCandidate],
    accessions: Iterable[AccessionCandidate],
    *,
    node_limit: int,
    selection_seed: str = PILOT_SELECTION_SEED,
    deferred_quota_keys: frozenset[str] = APPROVED_DEFERRED_QUOTA_KEYS,
) -> JointSelectionResult:
    """Solve the S5.1 joint entity-accession allocation problem deterministically.

    The frozen lexicographic objective (Decision 013 section 5; Decision 018
    section 3.1) is applied in exactly this order: satisfy every hard quota; then
    minimise the single integer evidence-penalty sum across selected entities and
    accessions; then the base-accession count; then the stress-accession count;
    then the complete sorted entity-hash vector; then the complete sorted
    accession-hash vector; then canonical identity fallbacks after hash equality.

    ``node_limit`` is a required positive integer run input. Decision 018 section
    17 deliberately freezes no production default, because the limit enters the
    future deterministic run identity; this module reports the normalised value
    but derives and persists no identity. Exhaustion in any phase discards every
    incumbent, returns ``infeasible_or_unproven`` with ``node_limit_exhausted``,
    and returns no selection at all.

    ``deferred_quota_keys`` exists only so that an attempt to defer any quota
    other than Decision 018 section 14's single unmeasurable one fails loudly
    instead of silently. Any value other than the approved singleton is rejected;
    an additional deferral requires a new owner-approved decision record.

    Raises:
        ValueError: malformed or contradictory input, a non-positive node limit,
            or an attempt to defer a quota other than the approved one.
        TypeError: an input that is not an :class:`EntityCandidate` or
            :class:`AccessionCandidate`.
    """
    if frozenset(deferred_quota_keys) != APPROVED_DEFERRED_QUOTA_KEYS:
        message = (
            "only the Decision 018 section 14 difficult-or-nonstandard-package quota may be "
            f"deferred at M2.3; refusing {sorted(deferred_quota_keys)!r}"
        )
        raise ValueError(message)
    if isinstance(node_limit, bool) or not isinstance(node_limit, int) or node_limit < 1:
        message = f"node_limit must be a positive integer, got {node_limit!r}"
        raise ValueError(message)

    entity_pool = _validate_entities(entities)
    accession_pool = _validate_accessions(accessions)
    entity_candidates = tuple(entry.candidate for entry in entity_pool)
    name_change_by_cik = {
        entry.cik_padded: _name_change_contributes(entry.name_change) for entry in entity_pool
    }
    name_change_structural_by_cik = {
        entry.cik_padded: (
            entry.name_change.former_name_record_parseable
            and entry.name_change.has_prior_current_or_from_to
        )
        for entry in entity_pool
    }

    operating_eligible: list[Candidate] = []
    excluded: list[CandidateDiagnostic] = []
    for candidate in entity_candidates:
        if candidate.category not in ("operating", "control"):
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded,
                    candidate.filing_time_name,
                    candidate.category,
                    "unrecognized_category",
                )
            )
            continue
        if candidate.category != "operating":
            continue
        ok, reason = _operating_eligible(candidate)
        if ok:
            operating_eligible.append(candidate)
        else:
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded, candidate.filing_time_name, candidate.category, reason
                )
            )

    control_eligible_by_kind, _s4_controls, missing_control_kinds = _select_controls(
        entity_candidates, selection_seed
    )
    eligible_control_ids = {
        c.cik_padded for options in control_eligible_by_kind.values() for c in options
    }
    for candidate in entity_candidates:
        if candidate.category == "control" and candidate.cik_padded not in eligible_control_ids:
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded,
                    candidate.filing_time_name,
                    candidate.category,
                    "control_ineligible",
                )
            )

    ctx = _build_pool_context(accession_pool, selection_seed)
    eligible_entity_ciks = {c.cik_padded for c in operating_eligible} | eligible_control_ids
    operating_eligible_ciks = {c.cik_padded for c in operating_eligible}
    # An accession's assigned role is the one its attached registrants' category
    # selects, so a control-attached accession is `control` no matter which other
    # eligibility flags its snapshot row happens to carry. Under **Decision 083 R62**
    # an accession attaches to every substantive registrant, and `_attached_category`
    # fails closed when those span more than one category.
    pool_category_by_cik: dict[str, str | None] = dict.fromkeys(
        operating_eligible_ciks, "operating"
    )
    pool_category_by_cik.update(dict.fromkeys(eligible_control_ids, "control"))
    pool_assigned_roles: dict[int, AccessionRole] = {}
    for i in range(len(accession_pool)):
        category = _attached_category(ctx.registrants[i], pool_category_by_cik)
        role: AccessionRole | None
        if category == "operating":
            role = ctx.role_if_operating[i]
        elif category == "control":
            role = ctx.role_if_control[i]
        else:
            role = None
        if role is not None:
            pool_assigned_roles[i] = role
    eligible_positions = sorted(pool_assigned_roles)

    accession_diagnostics = _accession_diagnostics(ctx, eligible_entity_ciks, eligible_positions)

    budget = _NodeBudget(node_limit)
    incumbent: _Incumbent | None = None
    if not missing_control_kinds and len(operating_eligible) >= TOTAL_OPERATING:
        incumbent = _search_joint(
            ctx,
            operating_eligible,
            control_eligible_by_kind,
            name_change_by_cik,
            selection_seed,
            budget,
        )

    if budget.exhausted:
        status: JointSelectionStatus = "infeasible_or_unproven"
    elif incumbent is None:
        status = "infeasible"
    else:
        status = "feasible"

    if status == "feasible" and incumbent is not None:
        selected_operating = tuple(
            sorted(incumbent.operating, key=lambda c: _rank_key(c, selection_seed))
        )
        selected_controls = tuple(
            sorted(incumbent.controls, key=lambda c: _rank_key(c, selection_seed))
        )
        chosen_indices = tuple(
            sorted(incumbent.accession_indices, key=lambda i: _selected_order_key(ctx, i))
        )
        selected_accessions = tuple(
            SelectedAccession(
                accession_plain=ctx.accessions[index].accession_plain,
                accession_number_dashed=ctx.accessions[index].accession_number_dashed,
                anchor_cik_padded=ctx.accessions[index].anchor_cik_padded,
                accession_role=incumbent.accession_roles[index],
                selected_order=position,
                accession_tie_break_sha256=ctx.hashes[index],
                substantive_registrants_padded=ctx.registrants[index],
            )
            for position, index in enumerate(chosen_indices, start=1)
        )
        objective = incumbent.objective
    else:
        selected_operating = ()
        selected_controls = ()
        chosen_indices = ()
        selected_accessions = ()
        objective = None

    entity_quota_results = _build_quota_results(
        status,
        entity_candidates,
        operating_eligible,
        selected_operating,
        control_eligible_by_kind,
        selected_controls,
    )

    name_change_eligible = sum(1 for cik in sorted(eligible_entity_ciks) if name_change_by_cik[cik])
    name_change_structural = sum(
        1 for cik in sorted(eligible_entity_ciks) if name_change_structural_by_cik[cik]
    )
    # The one additive Decision 020 output. It is derived from the same pool context
    # and the same accepted contribution rules the diagnostics below report, and the
    # diagnostics take their achieved counts from it.
    membership = _derive_membership(
        ctx,
        entity_pool,
        selected_entity_ciks=[c.cik_padded for c in (*selected_operating, *selected_controls)],
        selected_accession_plains=[
            ctx.accessions[index].accession_plain for index in chosen_indices
        ],
    )
    accession_quota_results = _build_accession_quota_results(
        ctx,
        status,
        eligible_positions,
        pool_assigned_roles,
        name_change_eligible,
        name_change_structural,
        membership,
    )
    # **Decision 083 R62.** ``max_base_per_cik`` is entity-domain, so a joint base
    # filing counts once for each substantive registrant. The three totals below stay
    # accession-domain and are computed over ``selected_accessions``, which holds one
    # row per accession -- so one joint filing is still exactly one filing there.
    base_by_cik: dict[str, int] = {}
    for selected in selected_accessions:
        if selected.accession_role == "base":
            for cik in selected.substantive_registrants_padded:
                base_by_cik[cik] = base_by_cik.get(cik, 0) + 1
    cap_usage = AccessionCapUsage(
        base_total=sum(1 for s in selected_accessions if s.accession_role == "base"),
        stress_total=sum(1 for s in selected_accessions if s.accession_role == "stress"),
        accession_total=len(selected_accessions),
        max_base_per_cik=max(base_by_cik.values(), default=0),
    )
    cap_results = _build_cap_quota_results(status, cap_usage)

    excluded.sort(key=lambda d: d.cik_padded)
    return JointSelectionResult(
        status=status,
        selection_seed=selection_seed,
        selected_operating=selected_operating,
        selected_controls=selected_controls,
        selected_accessions=selected_accessions,
        objective=objective,
        entity_quota_results=entity_quota_results,
        accession_quota_results=accession_quota_results + cap_results,
        deferred_quota_result=_deferred_quota_diagnostic(),
        excluded_candidates=tuple(excluded),
        accession_diagnostics=accession_diagnostics,
        amendment_families=ctx.families,
        quota_contributions=membership,
        expanded_node_count=budget.count,
        node_limit=node_limit,
        node_limit_exhausted=budget.exhausted,
    )


def _accession_diagnostics(
    ctx: _PoolContext,
    eligible_entity_ciks: set[str],
    eligible_positions: Sequence[int],
) -> tuple[AccessionDiagnostic, ...]:
    """Explain every candidate accession that could not enter the search pool."""
    eligible = set(eligible_positions)
    diagnostics: list[AccessionDiagnostic] = []
    for i, accession in enumerate(ctx.accessions):
        if i in eligible:
            continue
        slot = ctx.slots[i]
        # **Decision 083 R62**: an accession attaches to every substantive registrant,
        # so it is only entity-ineligible when NONE of them is eligible.
        if not any(cik in eligible_entity_ciks for cik in ctx.registrants[i]):
            reason = "anchor_entity_not_eligible"
        elif ctx.role_if_operating[i] is None and ctx.role_if_control[i] is None:
            reason = ctx.role_reason[i] or "role_unclassified_no_match"
        else:
            reason = "role_not_available_for_anchor_category"
        diagnostics.append(
            AccessionDiagnostic(
                accession_number_dashed=accession.accession_number_dashed,
                registrant_slot_padded=slot,
                form_type=accession.form_type,
                reason=reason,
            )
        )
        if (
            accession.official_filing_date is not None
            and _parse_iso_date(accession.official_filing_date) is None
        ):
            diagnostics.append(
                AccessionDiagnostic(
                    accession_number_dashed=accession.accession_number_dashed,
                    registrant_slot_padded=slot,
                    form_type=accession.form_type,
                    reason="unparseable_official_filing_date",
                )
            )
    for i, accession in enumerate(ctx.accessions):
        if accession.report_date is not None and ctx.report_dates[i] is None:
            diagnostics.append(
                AccessionDiagnostic(
                    accession_number_dashed=accession.accession_number_dashed,
                    registrant_slot_padded=ctx.slots[i],
                    form_type=accession.form_type,
                    reason="unparseable_report_date",
                )
            )
    diagnostics.sort(key=lambda d: (d.accession_number_dashed, d.reason))
    return tuple(diagnostics)
