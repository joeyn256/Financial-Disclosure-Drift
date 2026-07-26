"""Evidence-based amendment linkage (Decision 008 section 2).

An amendment never overwrites, re-dates, or re-cohorts its parent. Parentage is
established from evidence only; ambiguity stays unresolved. A ``/A`` suffix is
never treated as a restatement, and the XBRL amendment flag is never treated as
equivalent to the EDGAR form suffix.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

__all__ = [
    "AmendmentCandidate",
    "AmendmentEvidence",
    "AmendmentLink",
    "AmendmentRelationship",
    "link_amendment",
]

AmendmentRelationship = Literal[
    "amends_original",
    "amends_prior_amendment",
    "supplements_original",
    "possible_amendment_of",
    "unresolved_amendment",
]


@dataclass(frozen=True, slots=True)
class AmendmentCandidate:
    """A possible parent accession."""

    accession_plain: str
    form_type: str
    official_filing_date: date
    period_of_report: date | None = None
    registrant_ciks: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class AmendmentEvidence:
    """Evidence extracted for one amendment accession."""

    accession_plain: str
    form_type: str
    official_filing_date: date
    period_of_report: date | None = None
    registrant_ciks: tuple[int, ...] = ()
    referenced_accession_plain: str | None = None
    declares_supplement_only: bool = False
    xbrl_amendment_flag: bool | None = None
    candidates: tuple[AmendmentCandidate, ...] = ()


@dataclass(frozen=True, slots=True)
class AmendmentLink:
    """Resolved or unresolved amendment relationship."""

    amendment_accession_plain: str
    parent_accession_plain: str | None
    relationship: AmendmentRelationship
    evidence: str
    reason_codes: tuple[str, ...] = ()
    is_restatement_claim: bool = False

    @property
    def is_resolved(self) -> bool:
        """Whether a specific parent was established from evidence."""
        return self.parent_accession_plain is not None and self.relationship in {
            "amends_original",
            "amends_prior_amendment",
            "supplements_original",
        }


def link_amendment(evidence: AmendmentEvidence) -> AmendmentLink:
    """Link an amendment to a parent accession using evidence only."""
    unresolved_codes = ("REVIEW_AMENDMENT_PARENT_UNRESOLVED",)
    flag_conflict = (
        evidence.xbrl_amendment_flag is not None
        and evidence.xbrl_amendment_flag != evidence.form_type.endswith("/A")
    )
    extra = ("REVIEW_AMENDMENT_PARENT_UNRESOLVED",) if flag_conflict else ()

    explicit = _explicit_parent(evidence)
    if explicit is not None:
        relationship: AmendmentRelationship = (
            "supplements_original"
            if evidence.declares_supplement_only
            else (
                "amends_prior_amendment" if explicit.form_type.endswith("/A") else "amends_original"
            )
        )
        if explicit.official_filing_date > evidence.official_filing_date:
            return AmendmentLink(
                amendment_accession_plain=evidence.accession_plain,
                parent_accession_plain=None,
                relationship="unresolved_amendment",
                evidence=(
                    "referenced accession was filed after the amendment, which evidence "
                    "cannot explain"
                ),
                reason_codes=unresolved_codes,
            )
        return AmendmentLink(
            amendment_accession_plain=evidence.accession_plain,
            parent_accession_plain=explicit.accession_plain,
            relationship=relationship,
            evidence="the amendment references the parent accession explicitly",
            reason_codes=extra,
        )

    matches = _period_matches(evidence)
    if len(matches) == 1:
        return AmendmentLink(
            amendment_accession_plain=evidence.accession_plain,
            parent_accession_plain=matches[0].accession_plain,
            relationship="possible_amendment_of",
            evidence="a single earlier candidate shares the period of report and registrant",
            reason_codes=unresolved_codes,
        )
    if len(matches) > 1:
        return AmendmentLink(
            amendment_accession_plain=evidence.accession_plain,
            parent_accession_plain=None,
            relationship="unresolved_amendment",
            evidence=f"{len(matches)} candidates share the period of report",
            reason_codes=unresolved_codes,
        )

    return AmendmentLink(
        amendment_accession_plain=evidence.accession_plain,
        parent_accession_plain=None,
        relationship="unresolved_amendment",
        evidence="no candidate could be established from evidence",
        reason_codes=unresolved_codes,
    )


def _explicit_parent(evidence: AmendmentEvidence) -> AmendmentCandidate | None:
    if evidence.referenced_accession_plain is None:
        return None
    for candidate in evidence.candidates:
        if candidate.accession_plain == evidence.referenced_accession_plain:
            return candidate
    return None


def _period_matches(evidence: AmendmentEvidence) -> tuple[AmendmentCandidate, ...]:
    if evidence.period_of_report is None:
        return ()
    registrants = set(evidence.registrant_ciks)
    return tuple(
        candidate
        for candidate in evidence.candidates
        if candidate.period_of_report == evidence.period_of_report
        and candidate.official_filing_date <= evidence.official_filing_date
        and (not registrants or registrants & set(candidate.registrant_ciks))
    )
