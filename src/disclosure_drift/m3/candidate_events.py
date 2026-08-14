"""Decision 014 §5 event-flag detection, under owner ruling **R19** (Decision 071 §4).

Decision 014 §5 froze the **names** of twelve event flags but no accepted record stated
how any of them is *detected* from accepted M2.2 metadata. **R19 supplies that
operational definition**, and this module is its only executable expression.

The governing rule, applied to every detector below without exception:

> An event flag is true **only** from accepted, structured, explicit evidence that
> mechanically establishes that event. **Lack of evidence is not a positive event.**

Structurally forbidden here, and asserted by test rather than promised: substring
matching, regular expressions over descriptive status text, fuzzy matching, synonym
tables, company-name keywords, ticker keywords, `entityType` inference, operator
judgment, outcome data, filing narrative, and absence from an alias-only ticker list.

Two consequences are recorded rather than engineered around:

* the four *status* flags (`inactive`, `acquired`, `delisted`, `bankrupt_or_failed`)
  require an accepted structured status observation whose canonical value **equals** the
  frozen token. The accepted M2.2 submissions vocabulary is not known to emit those
  tokens, so on the real corpus they are expected to be **NOT OBSERVED** — which is
  exactly what R19 §4.1–4.4 rule, and R19 §4.13 already fixes the consequence: if the
  inactive-eventful quota cannot be satisfied from accepted evidence, the selector
  reports **infeasible**. It is never satisfied by absence from `sec_company_tickers*`,
  which is an alias source and not an authoritative universe.
* `reverse_merger_or_de_spac_review` requires lineage evidence that **explicitly**
  identifies the condition. The accepted lineage layer emits only `company_name` and
  `ticker` edge kinds, so it is **NOT OBSERVED** and no proxy is invented (R19 §4.6).

Everything here is engineering-coverage stratification only. It never influences a
feature, vocabulary, threshold, transform, model choice, or outcome (Decision 015;
leakage register L19).
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Final

from disclosure_drift.sec.accession_selector import (
    FYE_CIRCULAR_TOLERANCE_DAYS,
    circular_month_day_distance,
)

__all__ = [
    "CANONICAL_STATUS_TOKENS",
    "EVENT_FLAGS",
    "LINEAGE_SUCCESSION_EVIDENCE_KINDS",
    "NON_ORDINARY_AMENDMENT_LINKAGE_STATES",
    "ORDINARY_AMENDMENT_LINKAGE_STATES",
    "REVERSE_MERGER_EVIDENCE_KINDS",
    "STATUS_OBSERVATION_KINDS",
    "TRANSITION_REPORT_FORMS",
    "EntityEventEvidence",
    "EventDetection",
    "canonical_status_token",
    "detect_event_flags",
]

#: Decision 014 §5's twelve frozen event names, in the record's own order. The names are
#: not changed, reordered, added to, or removed by R19 — only their detection is fixed.
EVENT_FLAGS: Final[tuple[str, ...]] = (
    "inactive",
    "acquired",
    "delisted",
    "bankrupt_or_failed",
    "successor_or_predecessor_lineage",
    "reverse_merger_or_de_spac_review",
    "fiscal_year_end_change",
    "transition_report_filed",
    "company_name_or_ticker_transition",
    "multi_registrant_annual_filing",
    "unusual_amendment_history",
    "material_source_or_identity_conflict",
)

#: The accepted structured observation kinds that may carry an entity status or
#: classification (migration ``0003``'s vocabulary). No other kind is consulted, and a
#: company name or ticker is never one of them.
STATUS_OBSERVATION_KINDS: Final[frozenset[str]] = frozenset({"entity_type", "filing_status"})

#: R19 §§4.1–4.4. One frozen canonical token per status flag, compared for **equality**
#: after canonicalization — never as a substring, a prefix, a pattern, or a synonym.
CANONICAL_STATUS_TOKENS: Final[Mapping[str, str]] = {
    "inactive": "inactive",
    "acquired": "acquired",
    "delisted": "delisted",
    "bankrupt_or_failed": "bankrupt_or_failed",
}

#: R19 §4.5. A shared **identical company name** across two distinct CIKs is the accepted
#: succession signal the census lineage layer records. ``ticker`` edges are deliberately
#: excluded: R19 §4.5 names "ticker reuse" among the inferences it forbids, and R19 §4.9
#: keeps M3.3 name-only.
LINEAGE_SUCCESSION_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"company_name"})

#: R19 §4.6. Only an edge kind that *explicitly* identifies the condition counts. The
#: accepted census lineage layer emits neither, so this is NOT OBSERVED rather than
#: proxied from a generic predecessor/successor edge.
REVERSE_MERGER_EVIDENCE_KINDS: Final[frozenset[str]] = frozenset({"reverse_merger", "de_spac"})

#: R19 §4.8. Exact forms only; no text inference.
TRANSITION_REPORT_FORMS: Final[frozenset[str]] = frozenset({"10-KT", "10-KT/A"})

#: R19 §4.11. Migration ``0009``'s linkage vocabulary, split into the two states that
#: represent an ordinary resolved amendment and the three that do not.
ORDINARY_AMENDMENT_LINKAGE_STATES: Final[frozenset[str]] = frozenset(
    {"amends_original", "amends_prior_amendment"}
)
NON_ORDINARY_AMENDMENT_LINKAGE_STATES: Final[frozenset[str]] = frozenset(
    {"supplements_original", "possible_amendment_of", "unresolved_amendment"}
)


def canonical_status_token(value: str) -> str:
    """Canonicalize one observed status value for **equality** comparison.

    NFC, then Decision 019 §8.2.1's whitespace rule (``" ".join(value.split())``), then
    case folding. This is canonicalization, not interpretation: it changes no character
    that distinguishes one token from another, and it introduces no synonym, no
    stemming, and no partial match. ``"Formerly Inactive Holdings"`` does not
    canonicalize to ``"inactive"``.
    """
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


@dataclass(frozen=True, slots=True)
class EntityEventEvidence:
    """Exactly what the twelve detectors read, all from accepted persisted evidence.

    Assembling this is the caller's job, and every field is a fact the accepted census
    or candidate layer already establishes. A detector cannot reach past it, which is
    what keeps free text out of event detection.
    """

    #: Canonical values of this entity's ``entity_type`` / ``filing_status`` observations.
    status_values: tuple[str, ...] = ()
    #: ``evidence_kind`` of every accepted lineage edge touching this entity's CIK.
    lineage_evidence_kinds: frozenset[str] = frozenset()
    #: Exact ``form_type`` of every eligible candidate accession anchored on this entity.
    eligible_forms: tuple[str, ...] = ()
    #: ``report_date`` of each eligible **original** annual report, in filing order.
    #: ``None`` marks one whose report date the accepted evidence does not establish.
    original_annual_report_dates: tuple[str | None, ...] = ()
    #: A winning, provisional, parseable former-name identity record exists (R19 §4.9).
    winning_provisional_former_name: bool = False
    #: An eligible annual filing carries more than one substantively contributing
    #: registrant under the accepted mapping; submitter-only rows never establish it.
    multi_registrant_annual_filing: bool = False
    #: The accepted amendment-lineage machinery reported a non-ordinary diagnostic.
    non_ordinary_amendment_lineage: bool = False
    #: The accepted evidence/resolution machinery explicitly classified a material
    #: source or identity-relevant fact as conflicting.
    material_conflict: bool = False


@dataclass(frozen=True, slots=True)
class EventDetection:
    """Which flags are affirmatively observed, and which comparisons stayed unresolved."""

    observed: frozenset[str] = frozenset()
    unresolved: tuple[str, ...] = field(default=())

    @property
    def is_eventful(self) -> bool:
        """R19 §4.13: eventful needs one affirmatively true flag, never an absence."""
        return bool(self.observed)


def _status_flags(values: Sequence[str]) -> set[str]:
    """R19 §§4.1–4.4 -- exact canonical equality against the frozen tokens."""
    canonical = {canonical_status_token(value) for value in values if value}
    return {flag for flag, token in CANONICAL_STATUS_TOKENS.items() if token in canonical}


def _fiscal_year_end_change(
    forms: Sequence[str], report_dates: Sequence[str | None]
) -> tuple[bool, bool]:
    """R19 §4.7 -- branch A (transition report) or branch B (circular distance).

    Returns ``(observed, unresolved_comparison)``. A missing or invalid ``report_date``
    needed for an adjacent comparison makes that comparison unresolved; it never
    silently becomes "no change" and it is never guessed.
    """
    if any(form in TRANSITION_REPORT_FORMS for form in forms):
        return True, False
    unresolved = False
    parsed: list[date | None] = []
    for value in report_dates:
        try:
            parsed.append(None if value is None else date.fromisoformat(value))
        except ValueError:
            parsed.append(None)
    for first, second in zip(parsed, parsed[1:], strict=False):
        if first is None or second is None:
            unresolved = True
            continue
        if circular_month_day_distance(first, second) > FYE_CIRCULAR_TOLERANCE_DAYS:
            return True, unresolved
    return False, unresolved


def detect_event_flags(evidence: EntityEventEvidence) -> EventDetection:
    """Apply **R19** to one entity's accepted evidence, and nothing else.

    Every branch is an affirmative predicate over structured evidence. No branch reads
    a company name, a ticker, an ``entityType`` string, or any descriptive prose, and no
    branch treats an absence as a positive event.
    """
    observed = _status_flags(evidence.status_values)
    unresolved: list[str] = []

    if evidence.lineage_evidence_kinds & LINEAGE_SUCCESSION_EVIDENCE_KINDS:
        observed.add("successor_or_predecessor_lineage")
    if evidence.lineage_evidence_kinds & REVERSE_MERGER_EVIDENCE_KINDS:
        observed.add("reverse_merger_or_de_spac_review")

    fye_observed, fye_unresolved = _fiscal_year_end_change(
        evidence.eligible_forms, evidence.original_annual_report_dates
    )
    if fye_observed:
        observed.add("fiscal_year_end_change")
    if fye_unresolved:
        unresolved.append("fiscal_year_end_change")

    if any(form in TRANSITION_REPORT_FORMS for form in evidence.eligible_forms):
        observed.add("transition_report_filed")
    if evidence.winning_provisional_former_name:
        observed.add("company_name_or_ticker_transition")
    if evidence.multi_registrant_annual_filing:
        observed.add("multi_registrant_annual_filing")
    if evidence.non_ordinary_amendment_lineage:
        observed.add("unusual_amendment_history")
    if evidence.material_conflict:
        observed.add("material_source_or_identity_conflict")

    unknown = observed - set(EVENT_FLAGS)
    if unknown:
        message = f"unregistered Decision 014 §5 event flag(s): {sorted(unknown)}"
        raise ValueError(message)
    return EventDetection(observed=frozenset(observed), unresolved=tuple(sorted(unresolved)))
