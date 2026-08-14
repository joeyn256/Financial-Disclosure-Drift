"""The frozen candidate classification rules, applied verbatim (Decisions 002, 014, 016).

Every rule here is **inherited, never redefined**. Decision 014 §4 froze
``sic-family-mapping/0.2`` as a decision-record artifact and expressly left it
unimplemented; this module is its first executable expression and reproduces the frozen
ranges exactly, including every v0.2 correction and every deliberate
``review_required`` hole. Decision 014 §5's stable/eventful definitions and §2's filer-size
mapping are reproduced the same way, and Decision 016 §2's four primary-universe
conditions are applied as four conditions rather than as a SIC test.

**Nothing here may be adjusted after seeing a real candidate distribution** (Decision
014 §5). A code that no frozen range covers is ``review_required`` — it is never mapped
by proximity, and never defaulted into a family.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Final, Literal

from disclosure_drift.m3.candidate_events import EventDetection

__all__ = [
    "AMENDMENT_PURPOSE_CATEGORIES",
    "ENGINEERING_ONLY_SIC_CODES",
    "QUOTA_INELIGIBLE_SIC_CODES",
    "STABLE_MINIMUM_ORIGINAL_ANNUAL_REPORTS",
    "EvidenceLevel",
    "classify_history",
    "classify_size_stratum",
    "industry_family_for_sic",
    "primary_universe_eligible",
]

EvidenceLevel = Literal["provisional", "review_required", "conflicting", "unavailable"]

#: Decision 014 §2's three strata. ``non_accelerated_or_smaller`` is one combined
#: stratum because the two SEC categories are not always mutually exclusive and no M2.3
#: source can separate them without document evidence.
_SIZE_BY_CATEGORY: Final[Mapping[str, str]] = {
    "large accelerated filer": "large_accelerated",
    "accelerated filer": "accelerated",
    "non-accelerated filer": "non_accelerated_or_smaller",
    "smaller reporting company": "non_accelerated_or_smaller",
    "non-accelerated filer and smaller reporting company": "non_accelerated_or_smaller",
    "accelerated filer and smaller reporting company": "accelerated",
    "large accelerated filer and smaller reporting company": "large_accelerated",
}

#: Decision 014 §4's frozen ``sic-family-mapping/0.2``, as inclusive numeric ranges in
#: the order the record states them. Every exclusion the record makes is expressed as a
#: narrower range rather than as a subtraction, so no code is covered twice.
_SIC_FAMILY_RANGES: Final[tuple[tuple[str, tuple[tuple[int, int], ...]], ...]] = (
    (
        "technology_and_communications",
        (
            (3570, 3579),
            (3661, 3669),
            (3670, 3679),
            (4812, 4813),
            (4822, 4822),
            (4830, 4830),
            (4841, 4841),
            (4899, 4899),
            (7370, 7374),
        ),
    ),
    (
        "operating_financial_institutions",
        (
            (6020, 6036),
            (6141, 6199),
            (6200, 6221),
            (6300, 6411),
            (6712, 6712),
        ),
    ),
    (
        "industrial_and_materials",
        (
            (1000, 1219),
            (1242, 1299),
            (1400, 1499),
            (1500, 1799),
            (2200, 2299),
            (2600, 2699),
            (2800, 2819),
            (2860, 2899),
            (3000, 3099),
            (3200, 3299),
            (3300, 3499),
            (3500, 3569),
            (3580, 3599),
            (3612, 3612),
            (3620, 3629),
            (3700, 3799),
            (4000, 4699),
        ),
    ),
    (
        "consumer_retail_and_services",
        (
            (2000, 2199),
            (2300, 2399),
            (2500, 2599),
            (2700, 2799),
            (5000, 5199),
            (5200, 5999),
            (7000, 7099),
            (7200, 7299),
            (7300, 7369),
            (7377, 7377),
            (7500, 7599),
            (7800, 7999),
        ),
    ),
    (
        "healthcare_and_life_sciences",
        ((2830, 2836), (3841, 3851), (8000, 8099)),
    ),
    (
        "energy_and_utilities",
        ((1220, 1241), (1300, 1399), (2900, 2999), (4900, 4999)),
    ),
)

#: Decision 014 §4 and Decision 016 §2: `review_required` under every evidence level,
#: and never able to satisfy an affirmative industry quota. Listed explicitly so a
#: reader can see them rather than deduce them from range arithmetic.
QUOTA_INELIGIBLE_SIC_CODES: Final[frozenset[str]] = frozenset({"6719", "6798", "3826", "8731"})

#: Decision 014 §4 / Decision 016 §2: mapped to a family, but engineering-only —
#: 6712 may not affirmatively satisfy the operating-financial quota, and both are
#: primary-universe ineligible regardless.
ENGINEERING_ONLY_SIC_CODES: Final[frozenset[str]] = frozenset({"6712", "6798"})

#: Decision 014 §6's three frozen amendment-purpose categories.
AMENDMENT_PURPOSE_CATEGORIES: Final[tuple[str, ...]] = (
    "administrative_or_exhibit",
    "financial_or_xbrl_correction",
    "narrative_or_governance",
)

#: Decision 014 §5's first stable condition.
STABLE_MINIMUM_ORIGINAL_ANNUAL_REPORTS: Final = 4


def classify_size_stratum(categories: Sequence[str]) -> tuple[str | None, EvidenceLevel]:
    """Decision 014 §2 -- map the SEC ``category`` field, or refuse.

    A blank category is ``unavailable``; an unmapped one is ``review_required``;
    disagreeing observations are ``conflicting``. **None is defaulted to a stratum** --
    the record is explicit that ``category`` is commonly blank for exactly the inactive
    population the eventful quota depends on.
    """
    values = [value.strip() for value in categories if value and value.strip()]
    if not values:
        return None, "unavailable"
    mapped = {_SIZE_BY_CATEGORY.get(_normalize_category(value)) for value in values}
    if len(mapped) > 1:
        return None, "conflicting"
    stratum = mapped.pop()
    if stratum is None:
        return None, "review_required"
    return stratum, "provisional"


def _normalize_category(value: str) -> str:
    """Case-fold and collapse whitespace only; no synonym invention."""
    return " ".join(value.lower().split())


def industry_family_for_sic(sic_code: str | None) -> tuple[str | None, EvidenceLevel]:
    """Decision 014 §4 -- the frozen mapping, applied verbatim.

    Returns ``(None, "unavailable")`` when no SIC is on record, and
    ``(None, "review_required")`` for a code the frozen ranges do not cover or that
    v0.2 deliberately excluded. A family is **never** assigned by proximity.
    """
    if sic_code is None or not sic_code.strip():
        return None, "unavailable"
    code = sic_code.strip()
    if not (len(code) == 4 and code.isdigit()):
        return None, "review_required"
    if code in QUOTA_INELIGIBLE_SIC_CODES:
        return None, "review_required"
    numeric = int(code)
    for family, ranges in _SIC_FAMILY_RANGES:
        if any(low <= numeric <= high for low, high in ranges):
            return family, "provisional"
    return None, "review_required"


def classify_history(
    detection: EventDetection,
    *,
    eligible_original_annual_reports: int,
    evidence_available: bool,
) -> tuple[str | None, EvidenceLevel]:
    """Decision 014 §5 as **R19 §4.13** operationalizes it.

    ``eventful`` needs one affirmatively observed event flag. ``stable`` needs every
    Decision 014 §5 condition to hold mechanically, which -- because each of those
    conditions is the *absence* of one of the twelve flags -- reduces to "no flag
    observed, and at least four eligible original annual reports".

    An unresolved comparison is **never** turned into "no event": if a fact required to
    establish ``stable`` could not be established, history is ``review_required`` and
    contributes to no affirmative quota.
    """
    if not evidence_available:
        return None, "unavailable"
    if detection.is_eventful:
        return "eventful", "provisional"
    if detection.unresolved:
        return None, "review_required"
    if eligible_original_annual_reports >= STABLE_MINIMUM_ORIGINAL_ANNUAL_REPORTS:
        return "stable", "provisional"
    return None, "review_required"


def primary_universe_eligible(
    *,
    is_operating_candidate: bool,
    classification_resolved: bool,
    sic_code: str | None,
) -> bool:
    """Decision 016 §2 -- all four conditions, none of them SIC alone.

    Condition 4's "no other Decision 002 exclusion" is carried by the engineering-only
    SIC set, which condition 3 already excludes numerically; it is asserted separately
    so a future widening of 6000-6999 cannot silently readmit one.
    """
    if not is_operating_candidate or not classification_resolved:
        return False
    if sic_code is None:
        return False
    if not (len(sic_code) == 4 and sic_code.isdigit()):
        return False
    if 6000 <= int(sic_code) <= 6999:
        return False
    return sic_code not in ENGINEERING_ONLY_SIC_CODES
