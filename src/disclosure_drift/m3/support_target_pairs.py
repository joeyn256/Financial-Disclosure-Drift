"""The 2009-support / 2010-target pair rule (Decision 071 §6, IN-3).

Decision 018 §15 and Decision 019 §7 freeze the pre-study support pairing; the first-cut
implementation treated a 2009 ``support_2009`` cohort label as sufficient proof, which it
is not. **A pair is a property of the joint selection result, not of one accession.**

Every condition below must hold together, and the quota counts **distinct entities**:

* one anchor CIK;
* one **selected** SUPPORT-role original ``10-K`` whose official filing date falls in
  calendar year 2009 and which is explicitly pre-study — outside every applicable study
  cohort, carrying the accepted pre-study provenance reason;
* one **selected** BASE-role original ``10-K`` whose official filing date falls in
  calendar year 2010 with provisional official cohort ``development``;
* both accessions selected in the **same** joint result.

A 2009 support accession without its selected 2010 target satisfies no pair, and a 2010
target without its selected 2009 support satisfies none either. Several qualifying pairs
for one CIK count **once**.

This module reads a selection result and the frozen candidate rows it selected from; it
changes no accepted role definition and performs no selection of its own.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

__all__ = [
    "PRE_STUDY_SUPPORT_REASON_CODE",
    "REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES",
    "SUPPORT_YEAR",
    "TARGET_COHORT",
    "TARGET_YEAR",
    "PairedAccession",
    "pair_quota_satisfied",
    "paired_accessions_from_rows",
    "support_target_pair_entities",
]

#: Decision 018 §15's frozen years, and Decision 019 §7's provenance marker.
SUPPORT_YEAR: Final = 2009
TARGET_YEAR: Final = 2010
TARGET_COHORT: Final = "development"
PRE_STUDY_SUPPORT_REASON_CODE: Final = "PILOT_ACCESSION_PRE_STUDY_SUPPORT"

#: Decision 018 §16's hard quota: six **distinct** entities.
REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES: Final = 6

_ORIGINAL_ANNUAL_FORM: Final = "10-K"


@dataclass(frozen=True, slots=True)
class PairedAccession:
    """One selected accession, at the fields the pair rule reads."""

    accession_plain: str
    anchor_cik_numeric: int
    accession_role: str
    form_type: str
    is_amendment: bool
    official_filing_date: str | None
    provisional_official_cohort: str | None
    has_pre_study_reason: bool

    def _filing_year(self) -> int | None:
        """The calendar year of the resolved official filing date, or ``None``."""
        if self.official_filing_date is None or len(self.official_filing_date) < 4:
            return None
        head = self.official_filing_date[:4]
        return int(head) if head.isdigit() else None

    @property
    def is_support_leg(self) -> bool:
        """Every support-side condition, together."""
        return (
            self.accession_role == "support"
            and self.form_type == _ORIGINAL_ANNUAL_FORM
            and not self.is_amendment
            and self._filing_year() == SUPPORT_YEAR
            and self.provisional_official_cohort is None
            and self.has_pre_study_reason
        )

    @property
    def is_target_leg(self) -> bool:
        """Every target-side condition, together."""
        return (
            self.accession_role == "base"
            and self.form_type == _ORIGINAL_ANNUAL_FORM
            and not self.is_amendment
            and self._filing_year() == TARGET_YEAR
            and self.provisional_official_cohort == TARGET_COHORT
        )


def support_target_pair_entities(selected: Iterable[PairedAccession]) -> tuple[int, ...]:
    """The distinct anchor CIKs contributing a complete 2009/2010 pair.

    Both legs must be present in the **same** selection result, which is what the single
    ``selected`` sequence expresses: an accession that was not selected never appears
    here, so a half pair contributes nothing.
    """
    support: set[int] = set()
    target: set[int] = set()
    for item in selected:
        if item.is_support_leg:
            support.add(item.anchor_cik_numeric)
        if item.is_target_leg:
            target.add(item.anchor_cik_numeric)
    return tuple(sorted(support & target))


def pair_quota_satisfied(selected: Iterable[PairedAccession]) -> bool:
    """Whether the frozen six-distinct-entity pair quota is met.

    Reported, never engineered around: an unmet quota is an infeasible selection, not a
    reason to relax the pair rule (Decision 018 §16; **R10**).
    """
    return len(support_target_pair_entities(selected)) >= REQUIRED_SUPPORT_TARGET_PAIR_ENTITIES


def paired_accessions_from_rows(
    selected_rows: Sequence[Mapping[str, object]],
    candidate_rows: Mapping[str, Mapping[str, object]],
    pre_study_reasons: Iterable[str],
) -> tuple[PairedAccession, ...]:
    """Assemble pair inputs from persisted selection and candidate rows.

    ``selected_rows`` are ``pilot_selected_accessions`` rows, ``candidate_rows`` the
    ``pilot_candidate_accessions`` rows they reference, and ``pre_study_reasons`` the
    accessions carrying the accepted pre-study provenance reason. Nothing is inferred:
    an accession absent from ``candidate_rows`` fails closed.
    """
    marked = set(pre_study_reasons)
    assembled: list[PairedAccession] = []
    for row in selected_rows:
        plain = str(row["accession_plain"])
        candidate = candidate_rows.get(plain)
        if candidate is None:
            message = f"selected accession {plain!r} has no frozen candidate row"
            raise KeyError(message)
        cohort = candidate["provisional_official_cohort"]
        filing_date = candidate["official_filing_date"]
        assembled.append(
            PairedAccession(
                accession_plain=plain,
                anchor_cik_numeric=int(str(row["anchor_cik_numeric"])),
                accession_role=str(row["accession_role"]),
                form_type=str(candidate["form_type"]),
                is_amendment=bool(candidate["is_amendment"]),
                official_filing_date=None if filing_date is None else str(filing_date),
                provisional_official_cohort=None if cohort is None else str(cohort),
                has_pre_study_reason=plain in marked,
            )
        )
    return tuple(assembled)
