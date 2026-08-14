"""Boundary-control classification, under owner ruling **R20** (Decision 071 §6).

Decision 013 §3 and Decision 016 §2 froze the **four** boundary-control kinds; no
accepted record said how a candidate is *established* as one. **R20 supplies that
operational definition** as four independent evidence predicates, and this module is
their only executable expression.

**SEC ``entityType`` is not used, at all.** Neither is a company name, an incorporation
state, a country, or any other free text. Each predicate reads exactly one accepted
structured fact:

======================================  ==================================================
kind                                    predicate
======================================  ==================================================
``registered_investment_company_or_etf``  accepted SIC in the RIC/ETF boundary-control set
``asset_backed_issuer``                   at least one exact Form ``10-D`` in accepted
                                          stored submissions history
``shell_or_blank_check_issuer``           accepted SIC in the shell/blank-check set
``foreign_private_issuer``                at least one **original** ``20-F`` or ``40-F``
======================================  ==================================================

Overlap is not resolved by precedence, because R20 §6.5 forbids defining one: exactly
one predicate assigns that kind, zero predicates means the candidate is not a boundary
control, and more than one is a conflicting classification that can satisfy no
control-kind quota until a later owner ruling resolves it.

If a required control category cannot be supplied from the accepted candidate pool,
**selection is infeasible**. The predicates are never loosened after seeing the pool,
and acquisition is never reopened (R20 §6.5).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final, Literal

__all__ = [
    "ASSET_BACKED_FORMS",
    "BOUNDARY_CONTROL_KINDS",
    "FPI_ANNUAL_REPORT_FORMS",
    "RIC_ETF_SIC_CODES",
    "SHELL_BLANK_CHECK_SIC_CODES",
    "ControlClassification",
    "ControlEvidence",
    "classify_control_kind",
]

#: Migration ``0009``'s persisted vocabulary, which governs the stored contract. Decision
#: 071 §6 describes the fourth kind as "foreign_private_issuer_annual_report_filer"; that
#: is the same kind under its descriptive name, and the persisted value stays the
#: schema's ``foreign_private_issuer`` because the migration is the schema authority.
BOUNDARY_CONTROL_KINDS: Final[tuple[str, ...]] = (
    "registered_investment_company_or_etf",
    "asset_backed_issuer",
    "shell_or_blank_check_issuer",
    "foreign_private_issuer",
)

#: Decision 014 §4 excludes these from the operating-financial industry family and states
#: that they "map to the RIC/ETF **boundary-control** category": 6726 is named there
#: explicitly, and 6722 is the SEC SIC list's only open-end fund code. The set is
#: enumerated here rather than widened by proximity, and no competing SIC list exists.
RIC_ETF_SIC_CODES: Final[frozenset[str]] = frozenset({"6722", "6726"})

#: Decision 014 §4: "6770 (blank checks), which maps to the shell/blank-check
#: **boundary-control** category".
SHELL_BLANK_CHECK_SIC_CODES: Final[frozenset[str]] = frozenset({"6770"})

#: R20 §6.2. Form metadata only -- no filing body, no narrative, no name heuristic.
ASSET_BACKED_FORMS: Final[frozenset[str]] = frozenset({"10-D"})

#: R20 §6.4. The **original** forms only; an amendment alone never satisfies it.
FPI_ANNUAL_REPORT_FORMS: Final[frozenset[str]] = frozenset({"20-F", "40-F"})

ControlStatus = Literal["not_a_control", "resolved", "conflicting"]


@dataclass(frozen=True, slots=True)
class ControlEvidence:
    """The accepted structured facts the four predicates read, and nothing else.

    There is deliberately no ``entity_type`` field and no name field: a fact this
    container cannot carry is a fact no predicate can consult.
    """

    #: The entity's resolved four-digit SIC, or ``None`` when accepted evidence does not
    #: establish exactly one well-formed value.
    sic_code: str | None = None
    #: Whether exactly one well-formed SIC value is on record. A missing, conflicting,
    #: or malformed SIC supports no affirmative SIC-based control classification.
    sic_resolved: bool = False
    #: Every exact ``form_type`` in the entity's accepted stored submissions history,
    #: including forms outside the eligible annual-report universe.
    submission_forms: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class ControlClassification:
    """One deterministic control verdict, and the predicates that produced it."""

    control_kind: str | None
    status: ControlStatus
    satisfied: tuple[str, ...]

    @property
    def is_control(self) -> bool:
        """Whether the candidate is affirmatively a boundary control."""
        return self.status == "resolved"


def _satisfied_predicates(evidence: ControlEvidence) -> list[str]:
    """Evaluate the four predicates independently, in the frozen kind order."""
    satisfied: list[str] = []
    sic = evidence.sic_code if evidence.sic_resolved else None
    if sic is not None and sic in RIC_ETF_SIC_CODES:
        satisfied.append("registered_investment_company_or_etf")
    if evidence.submission_forms & ASSET_BACKED_FORMS:
        satisfied.append("asset_backed_issuer")
    if sic is not None and sic in SHELL_BLANK_CHECK_SIC_CODES:
        satisfied.append("shell_or_blank_check_issuer")
    if evidence.submission_forms & FPI_ANNUAL_REPORT_FORMS:
        satisfied.append("foreign_private_issuer")
    return satisfied


def classify_control_kind(evidence: ControlEvidence) -> ControlClassification:
    """Apply **R20** to one entity's accepted evidence.

    Order-independent by construction: each predicate is evaluated against a set, and
    the verdict depends only on how many hold, never on which was tested first.
    """
    satisfied = _satisfied_predicates(evidence)
    if not satisfied:
        return ControlClassification(control_kind=None, status="not_a_control", satisfied=())
    if len(satisfied) == 1:
        return ControlClassification(
            control_kind=satisfied[0], status="resolved", satisfied=tuple(satisfied)
        )
    return ControlClassification(
        control_kind=None, status="conflicting", satisfied=tuple(satisfied)
    )


def original_forms(forms: Iterable[str]) -> frozenset[str]:
    """The exact original (non-amendment) forms in a submissions history.

    Applied before the FPI predicate so that a ``20-F/A`` with no original ``20-F``
    cannot satisfy it (R20 §6.4). An amendment is recognized by the accepted ``/A``
    suffix convention, which is the same rule ``census_accessions.is_amendment`` uses.
    """
    return frozenset(form for form in forms if not form.endswith("/A"))
