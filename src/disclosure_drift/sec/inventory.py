"""Accession classification and eligibility (Decisions 007 and 008).

Pure functions over already-parsed records. Every non-eligible outcome carries at
least one machine-readable reason code, and unknown classification never produces
silent eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

from disclosure_drift.sec.temporal import SUPPORT_2009_COHORT, cohort_name_for

__all__ = [
    "AMENDMENT_FORMS",
    "ELIGIBLE_FORMS",
    "AccessionFacts",
    "Classification",
    "IssuerType",
    "classify_accession",
]

IssuerType = Literal[
    "operating",
    "operating_financial_institution",
    "asset_backed",
    "registered_investment_company",
    "shell_or_blank_check",
    "blank_check",
    "unknown",
]
InventoryRole = Literal[
    "primary_target",
    "support_only",
    "amendment_non_target",
    "control_evidence",
    "excluded",
]
EligibilityState = Literal["eligible", "excluded", "review_required"]

ELIGIBLE_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
AMENDMENT_FORMS: Final[frozenset[str]] = frozenset({"10-K/A", "10-KT/A"})
_TRANSITION_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A"})


@dataclass(frozen=True, slots=True)
class AccessionFacts:
    """Evidence available for one accession, already parsed from source objects."""

    accession_plain: str
    form_type: str
    official_filing_date: date | None
    issuer_type: IssuerType = "unknown"
    registrant_ciks: tuple[int, ...] = ()
    registrant_cik_resolved: bool = True
    shell_for_accession: bool | None = None
    was_shell_previously: bool = False
    post_de_spac: bool = False
    sic_codes_observed: tuple[str, ...] = ()
    xbrl_amendment_flag: bool | None = None
    uses_domestic_regime: bool = True


@dataclass(frozen=True, slots=True)
class Classification:
    """Eligibility outcome for one accession."""

    accession_plain: str
    inventory_role: InventoryRole
    primary_target_flag: bool
    eligibility_state: EligibilityState
    temporal_cohort: str | None
    reason_codes: tuple[str, ...]

    @property
    def requires_review(self) -> bool:
        """Whether the accession is held for human review."""
        return self.eligibility_state == "review_required"


def classify_accession(facts: AccessionFacts) -> Classification:
    """Classify one accession into a role, eligibility state, and reason codes."""
    reasons: list[str] = []

    if facts.form_type not in ELIGIBLE_FORMS:
        return Classification(
            accession_plain=facts.accession_plain,
            inventory_role="control_evidence",
            primary_target_flag=False,
            eligibility_state="excluded",
            temporal_cohort=_cohort_or_none(facts.official_filing_date),
            reason_codes=("EXCLUDED_UNSUPPORTED_FORM",),
        )

    exclusion = _issuer_exclusion(facts.issuer_type)
    if exclusion is not None:
        return Classification(
            accession_plain=facts.accession_plain,
            inventory_role="excluded",
            primary_target_flag=False,
            eligibility_state="excluded",
            temporal_cohort=_cohort_or_none(facts.official_filing_date),
            reason_codes=(exclusion,),
        )

    if facts.shell_for_accession:
        return Classification(
            accession_plain=facts.accession_plain,
            inventory_role="excluded",
            primary_target_flag=False,
            eligibility_state="excluded",
            temporal_cohort=_cohort_or_none(facts.official_filing_date),
            reason_codes=("EXCLUDED_SHELL_COMPANY",),
        )

    review: list[str] = []
    if facts.issuer_type == "unknown" or facts.shell_for_accession is None:
        review.append("REVIEW_UNKNOWN_ISSUER_TYPE")
    if not facts.registrant_cik_resolved or not facts.registrant_ciks:
        review.append("REVIEW_REGISTRANT_CIK_UNRESOLVED")
    if len(facts.registrant_ciks) > 1:
        review.append("REVIEW_MULTI_REGISTRANT")
    if len(set(facts.sic_codes_observed)) > 1:
        review.append("REVIEW_CONFLICTING_SIC")
    if facts.post_de_spac or (facts.was_shell_previously and not facts.shell_for_accession):
        review.append("REVIEW_POST_DE_SPAC_TRANSITION")
    if facts.official_filing_date is None:
        review.append("SEC_SCHEMA_REQUIRED_FIELD_MISSING")
    if facts.xbrl_amendment_flag is not None and facts.xbrl_amendment_flag != (
        facts.form_type in AMENDMENT_FORMS
    ):
        review.append("REVIEW_AMENDMENT_PARENT_UNRESOLVED")

    cohort = _cohort_or_none(facts.official_filing_date)
    role, primary, eligibility_code = _role_for(facts, cohort)
    reasons.append(eligibility_code)

    blocking_review = [code for code in review if code != "REVIEW_MULTI_REGISTRANT"]
    state: EligibilityState = "review_required" if blocking_review else "eligible"
    if role in {"amendment_non_target", "support_only"} and not blocking_review:
        state = "eligible"

    return Classification(
        accession_plain=facts.accession_plain,
        inventory_role=role,
        primary_target_flag=primary and state == "eligible",
        eligibility_state=state,
        temporal_cohort=cohort,
        reason_codes=tuple(dict.fromkeys([*reasons, *review])),
    )


def _issuer_exclusion(issuer_type: IssuerType) -> str | None:
    return {
        "asset_backed": "EXCLUDED_ASSET_BACKED_ISSUER",
        "registered_investment_company": "EXCLUDED_REGISTERED_INVESTMENT_COMPANY",
        "shell_or_blank_check": "EXCLUDED_SHELL_COMPANY",
        "blank_check": "EXCLUDED_BLANK_CHECK_COMPANY",
    }.get(issuer_type)


def _cohort_or_none(day: date | None) -> str | None:
    return None if day is None else cohort_name_for(day)


def _role_for(
    facts: AccessionFacts,
    cohort: str | None,
) -> tuple[InventoryRole, bool, str]:
    if facts.form_type in AMENDMENT_FORMS:
        return "amendment_non_target", False, "AMENDMENT_NON_TARGET"
    if cohort == SUPPORT_2009_COHORT:
        return "support_only", False, "SUPPORT_ONLY"
    if facts.form_type in _TRANSITION_FORMS:
        return "primary_target", True, "ELIGIBLE_TRANSITION_10KT"
    return "primary_target", True, "ELIGIBLE_ORIGINAL_10K"
