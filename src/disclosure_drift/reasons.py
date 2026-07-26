"""Machine-readable reason codes for eligibility, exclusion, review, and integrity.

Every excluded row carries at least one exclusion reason and every review row
carries at least one review reason (Decision 007 section 6, Decision 008 section 4).
Unknown classification never produces silent eligibility.

This registry seeds ``reference_reason_codes`` in the operational catalog.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

__all__ = [
    "REASON_CODES",
    "ReasonCategory",
    "ReasonCode",
    "codes_for_category",
    "reason",
    "release_blocking_codes",
]

ReasonCategory = Literal[
    "eligible",
    "support",
    "amendment",
    "excluded",
    "review",
    "integrity",
    "temporal",
]


@dataclass(frozen=True, slots=True)
class ReasonCode:
    """One machine-readable reason with its policy consequences."""

    code: str
    category: ReasonCategory
    description: str
    blocks_release: bool
    requires_manual_review: bool
    decision_reference: str


def _code(
    code: str,
    category: ReasonCategory,
    description: str,
    *,
    blocks_release: bool = False,
    requires_manual_review: bool = False,
    decision_reference: str,
) -> ReasonCode:
    return ReasonCode(
        code=code,
        category=category,
        description=description,
        blocks_release=blocks_release,
        requires_manual_review=requires_manual_review,
        decision_reference=decision_reference,
    )


_D007: Final = "Docs/Decisions/decision_007_sec_universe.md"
_D008: Final = "Docs/Decisions/decision_008_filing_inventory.md"
_D009: Final = "Docs/Decisions/decision_009_raw_data_governance.md"
_D010: Final = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"

_ALL: Final[tuple[ReasonCode, ...]] = (
    # --- eligibility -------------------------------------------------------- #
    _code(
        "ELIGIBLE_ORIGINAL_10K",
        "eligible",
        "Original annual report eligible as a primary target filing.",
        decision_reference=_D008,
    ),
    _code(
        "ELIGIBLE_TRANSITION_10KT",
        "eligible",
        "Original transition-period annual report eligible as a primary target filing.",
        decision_reference=_D008,
    ),
    _code(
        "SUPPORT_ONLY",
        "support",
        "Filing retained only as prior-year support; never a primary target.",
        decision_reference=_D008,
    ),
    _code(
        "AMENDMENT_NON_TARGET",
        "amendment",
        "Amendment retained with its own dates and cohorts; never a primary target.",
        decision_reference=_D008,
    ),
    # --- exclusions --------------------------------------------------------- #
    _code(
        "EXCLUDED_ASSET_BACKED_ISSUER",
        "excluded",
        "Asset-backed issuer excluded from the study universe.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_REGISTERED_INVESTMENT_COMPANY",
        "excluded",
        "Registered investment company, fund, or ETF excluded from the study universe.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_SHELL_COMPANY",
        "excluded",
        "Shell filing excluded for this accession; exclusion is accession-specific.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_BLANK_CHECK_COMPANY",
        "excluded",
        "Blank-check filing excluded for this accession; exclusion is accession-specific.",
        decision_reference=_D007,
    ),
    _code(
        "EXCLUDED_UNSUPPORTED_FORM",
        "excluded",
        "Form outside the eligible study universe; retained as inventory or control evidence.",
        decision_reference=_D007,
    ),
    # --- review ------------------------------------------------------------- #
    _code(
        "REVIEW_MULTI_REGISTRANT",
        "review",
        "Accession lists multiple registrants; registrant relationships must be confirmed.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_UNKNOWN_ISSUER_TYPE",
        "review",
        "Issuer type could not be classified; eligibility must not be inferred.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_CONFLICTING_SIC",
        "review",
        "Conflicting SIC evidence across sources for the same accession.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_POST_DE_SPAC_TRANSITION",
        "review",
        "Issuer appears to have transitioned out of shell status; classification is per accession.",
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_REGISTRANT_CIK_UNRESOLVED",
        "review",
        "Registrant CIK could not be resolved; the accession prefix is not a substitute.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D007,
    ),
    _code(
        "REVIEW_AMENDMENT_PARENT_UNRESOLVED",
        "review",
        "Amendment parentage could not be established from evidence.",
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "REVIEW_MISSING_ACCEPTANCE_TIMESTAMP",
        "review",
        "No acceptance timestamp available; availability precision falls back to date level.",
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY",
        "review",
        "A post-acceptance correction moves the filing across a frozen cohort boundary.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING",
        "review",
        "Official-filing and acceptance cohorts differ across a frozen boundary.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_AVAILABILITY_ORDER_INDETERMINATE",
        "review",
        "Availability order between two accessions cannot be established at date precision; "
        "automatic historical use is blocked without asserting unavailability.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_ACCESSION_HEADER_SOURCE_CONFLICT",
        "review",
        "Co-authoritative accession-header sources disagree; neither may be chosen silently.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_PROVISIONAL_DATE_DISAGREEMENT",
        "review",
        "Provisional discovery sources disagree and no accession-header value is available yet.",
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_FILING_DATE_BEFORE_ACCEPTANCE",
        "review",
        "Official filing date precedes the acceptance date, which SEC mechanics do not explain.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_TIMEZONE_AMBIGUOUS",
        "review",
        "Acceptance wall-clock time occurs twice under the Eastern daylight-saving fall-back, "
        "so two UTC offsets are possible and none may be chosen automatically.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_TIMEZONE_NONEXISTENT",
        "review",
        "Acceptance wall-clock time does not exist under the Eastern daylight-saving "
        "spring-forward transition, so the value cannot be interpreted as supplied.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    # --- temporal classification -------------------------------------------- #
    _code(
        "SAME_DAY_FILING",
        "temporal",
        "Official filing date equals the SEC acceptance date.",
        decision_reference=_D010,
    ),
    _code(
        "EXPECTED_AFTER_CUTOFF_ROLLOVER",
        "temporal",
        "Accepted after the applicable SEC cutoff, with the official filing date on the next "
        "EDGAR operating day; explained, and still reported in the divergence audit.",
        decision_reference=_D010,
    ),
    _code(
        "POST_ACCEPTANCE_DATE_CORRECTION",
        "temporal",
        "Filing metadata or DATE AS OF CHANGE indicates an authorized later correction or "
        "filing-date adjustment; never treated as ordinary after-hours behaviour.",
        decision_reference=_D010,
    ),
    _code(
        "UNEXPLAINED_DATE_DIVERGENCE",
        "temporal",
        "The acceptance-to-filing-date difference cannot be established from the approved rules "
        "and preserved source evidence.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "COVERAGE_BOUNDARY_DIVERGENCE",
        "temporal",
        "One date maps to a frozen cohort while the other is unresolved or outside supported "
        "cohort coverage.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY",
        "review",
        "A purported SEC acceptance falls on a non-operating day; EDGAR does not "
        "ordinarily accept filings on weekends or federal holidays. The observation is "
        "preserved, automatic rollover classification is blocked, and reconciliation is "
        "required.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    _code(
        "OPERATING_CALENDAR_UNAVAILABLE",
        "temporal",
        "No EDGAR operating calendar covered the dates, so rollover could not be established.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D010,
    ),
    # --- integrity ---------------------------------------------------------- #
    _code(
        "RAW_FILE_CHECKSUM_MISMATCH",
        "integrity",
        "Stored raw file does not match its recorded checksum; the file is quarantined, "
        "never replaced.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "REMOTE_CONTENT_CHANGED",
        "integrity",
        "A later response differs from an earlier observation; recorded as a new observation.",
        requires_manual_review=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_BLOCK_PAGE",
        "integrity",
        "SEC returned a block page; aggregate traffic halts and enters cooldown.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_SCHEMA_REQUIRED_FIELD_MISSING",
        "integrity",
        "A required SEC field is absent; no default is applied.",
        blocks_release=True,
        requires_manual_review=True,
        decision_reference=_D008,
    ),
    _code(
        "SEC_RESPONSE_EMPTY",
        "integrity",
        "SEC returned an empty body; a failure never becomes a valid empty result.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "SEC_RESPONSE_MALFORMED",
        "integrity",
        "SEC response could not be parsed as its declared type; payload quarantined.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "RAW_ARCHIVE_INVALID",
        "integrity",
        "Archive payload failed structural validation; payload quarantined.",
        blocks_release=True,
        decision_reference=_D009,
    ),
    _code(
        "RAW_PARTIAL_DOWNLOAD",
        "integrity",
        "Transfer ended before completion; the partial file is preserved, never promoted.",
        decision_reference=_D009,
    ),
    _code(
        "PARSER_FAILURE_RECORDED",
        "integrity",
        "Parser failed; the failure is recorded and raw evidence is retained.",
        decision_reference=_D009,
    ),
)

REASON_CODES: Final[Mapping[str, ReasonCode]] = MappingProxyType({item.code: item for item in _ALL})
"""Every reason code, keyed by code."""


def reason(code: str) -> ReasonCode:
    """Return the registered reason code.

    Raises:
        KeyError: the code is not registered. Reason codes are a closed set;
            ad-hoc strings are not permitted in the catalog.
    """
    try:
        return REASON_CODES[code]
    except KeyError:
        message = f"unregistered reason code {code!r}; add it to disclosure_drift.reasons"
        raise KeyError(message) from None


def codes_for_category(category: ReasonCategory) -> tuple[str, ...]:
    """Return the registered codes in ``category``, sorted."""
    return tuple(sorted(item.code for item in _ALL if item.category == category))


def release_blocking_codes() -> tuple[str, ...]:
    """Return the codes whose presence blocks release freezing, sorted."""
    return tuple(sorted(item.code for item in _ALL if item.blocks_release))


def _validate_registry() -> None:
    """Assert registry invariants at import time."""
    if len(REASON_CODES) != len(_ALL):
        message = "duplicate reason code detected in the registry"
        raise AssertionError(message)
    for item in _ALL:
        if not item.code.isupper() or " " in item.code:
            message = f"reason code {item.code!r} must be upper snake case"
            raise AssertionError(message)
        if not item.description.endswith("."):
            message = f"reason code {item.code!r} needs a sentence description"
            raise AssertionError(message)
        if item.category == "review" and not item.requires_manual_review:
            message = f"review code {item.code!r} must require manual review"
            raise AssertionError(message)
        if item.category == "eligible" and (item.blocks_release or item.requires_manual_review):
            message = f"eligible code {item.code!r} must not block release or require review"
            raise AssertionError(message)


_validate_registry()
