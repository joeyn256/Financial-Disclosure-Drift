"""Cohort-divergence audit (Decision 010 section 8).

Reports totals and per-accession detail, and decides what blocks release freezing:

* divergence explained by an approved reason is reported, not failed;
* ``unexplained_date_divergence`` blocks freezing;
* a cohort-boundary crossing requires manual review;
* a coverage-boundary divergence requires review and blocks freezing;
* any accession entering or leaving the untouched 2024 cohort must be listed
  explicitly and approved before freezing.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from disclosure_drift.sec.temporal import CohortAssignment

__all__ = [
    "PRIMARY_TEST_COHORT",
    "DivergenceAudit",
    "DivergenceRecord",
    "build_divergence_audit",
]

PRIMARY_TEST_COHORT = "primary_test"


@dataclass(frozen=True, slots=True)
class DivergenceRecord:
    """One accession's divergence facts, as reported in the audit."""

    accession_plain: str
    form_type: str
    is_amendment: bool
    official_filing_date: str
    acceptance_datetime_sec_raw: str | None
    official_filing_temporal_cohort: str
    accepted_temporal_cohort: str | None
    date_divergence: bool
    cohort_boundary_crossing: bool
    coverage_boundary_divergence: bool
    divergence_reason: str
    explained: bool
    availability_basis: str
    source_observations: tuple[str, ...]
    reason_codes: tuple[str, ...]

    @property
    def touches_primary_test(self) -> bool:
        """Whether the accession enters or leaves the untouched 2024 cohort."""
        return (self.cohort_boundary_crossing or self.coverage_boundary_divergence) and (
            PRIMARY_TEST_COHORT
            in {self.official_filing_temporal_cohort, self.accepted_temporal_cohort}
        )


@dataclass(frozen=True, slots=True)
class DivergenceAudit:
    """Aggregated divergence audit for a batch or release."""

    total_accessions: int
    date_divergence_total: int
    cohort_boundary_crossings: int
    coverage_boundary_divergences: int
    unexplained_total: int
    by_reason: Mapping[str, int]
    by_form: Mapping[str, int]
    by_original_or_amendment: Mapping[str, int]
    by_acceptance_year: Mapping[str, int]
    by_official_filing_year: Mapping[str, int]
    boundary_crossing_records: tuple[DivergenceRecord, ...]
    primary_test_records: tuple[DivergenceRecord, ...]
    unexplained_records: tuple[DivergenceRecord, ...]
    approvals: Mapping[str, str] = field(default_factory=dict)

    @property
    def blocks_release(self) -> bool:
        """Whether the audit blocks release freezing."""
        return bool(self.unexplained_records) or bool(self.unapproved_primary_test_records)

    @property
    def requires_manual_review(self) -> bool:
        """Whether any record requires human review."""
        return bool(self.boundary_crossing_records) or bool(self.unexplained_records)

    @property
    def unapproved_primary_test_records(self) -> tuple[DivergenceRecord, ...]:
        """2024-cohort entries or exits without a recorded approval."""
        return tuple(
            record
            for record in self.primary_test_records
            if record.accession_plain not in self.approvals
        )

    def gate_results(self) -> Mapping[str, str]:
        """Return release-gate outcomes for the acceptance report."""
        return {
            "cohort_divergence_explained": "fail" if self.unexplained_records else "pass",
            "cohort_boundary_review": "fail" if self.boundary_crossing_records else "pass",
            "coverage_boundary_divergence": (
                "fail" if self.coverage_boundary_divergences else "pass"
            ),
            "primary_test_membership_approved": (
                "fail" if self.unapproved_primary_test_records else "pass"
            ),
        }


def build_divergence_audit(
    entries: Iterable[tuple[str, str, CohortAssignment, str, Sequence[str]]],
    approvals: Mapping[str, str] | None = None,
) -> DivergenceAudit:
    """Build the audit from ``(accession, form, assignment, basis, observations)`` tuples."""
    records: list[DivergenceRecord] = []
    for accession, form_type, assignment, basis, observations in entries:
        records.append(
            DivergenceRecord(
                accession_plain=accession,
                form_type=form_type,
                is_amendment=form_type.endswith("/A"),
                official_filing_date=assignment.official_filing_date.isoformat(),
                acceptance_datetime_sec_raw=(
                    None
                    if assignment.acceptance_date is None
                    else assignment.acceptance_date.isoformat()
                ),
                official_filing_temporal_cohort=assignment.official_filing_temporal_cohort,
                accepted_temporal_cohort=assignment.accepted_temporal_cohort,
                date_divergence=assignment.date_divergence,
                cohort_boundary_crossing=assignment.cohort_boundary_crossing,
                coverage_boundary_divergence=assignment.coverage_boundary_divergence,
                divergence_reason=assignment.divergence.reason,
                explained=assignment.divergence.explained,
                availability_basis=basis,
                source_observations=tuple(observations),
                reason_codes=assignment.reason_codes,
            )
        )

    diverging = [record for record in records if record.date_divergence]
    crossings = tuple(record for record in records if record.cohort_boundary_crossing)
    coverage = tuple(record for record in records if record.coverage_boundary_divergence)
    unexplained = tuple(
        record
        for record in records
        if record.divergence_reason == "unexplained_date_divergence"
        or record.coverage_boundary_divergence
    )

    return DivergenceAudit(
        total_accessions=len(records),
        date_divergence_total=len(diverging),
        cohort_boundary_crossings=len(crossings),
        coverage_boundary_divergences=len(coverage),
        unexplained_total=len(unexplained),
        by_reason=dict(Counter(record.divergence_reason for record in records)),
        by_form=dict(Counter(record.form_type for record in diverging)),
        by_original_or_amendment=dict(
            Counter("amendment" if record.is_amendment else "original" for record in diverging)
        ),
        by_acceptance_year=dict(
            Counter(
                record.acceptance_datetime_sec_raw[:4]
                for record in diverging
                if record.acceptance_datetime_sec_raw
            )
        ),
        by_official_filing_year=dict(
            Counter(record.official_filing_date[:4] for record in diverging)
        ),
        boundary_crossing_records=crossings + coverage,
        primary_test_records=tuple(record for record in records if record.touches_primary_test),
        unexplained_records=unexplained,
        approvals=dict(approvals or {}),
    )
