"""Temporal policy for SEC accessions (Decision 010, Deviation D001).

Key rules implemented here:

* the **official SEC filing date** determines the authoritative cohort;
* the **acceptance date** determines a separate audit-only cohort;
* the complete-submission header and a separately retrieved SGML header are one
  **co-authoritative** source class; disagreement between them is preserved as a
  conflict requiring review and is never resolved silently;
* Submissions API and master-index values are provisional discovery observations;
* ``acceptance_date_sec`` comes from the **first eight characters** of the SEC
  ``YYYYMMDDHHMMSS`` value, never from a UTC conversion;
* the frozen cohort windows are untouched, and ``cohort_for()`` is called twice;
* the after-hours cutoff is **frozen** at 17:30 America/New_York for supported
  annual-report forms and is not configurable; tests may inject another value;
* a purported acceptance on a **non-operating day** is never rollover-eligible. It
  is preserved and flagged ``REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`` for
  reconciliation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Final, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from disclosure_drift.cohorts import cohort_for
from disclosure_drift.errors import DisclosureDriftError, ReviewRequiredError
from disclosure_drift.sec.calendar import (
    FROZEN_FILING_CUTOFF_ET,
    SUPPORTED_CUTOFF_FORMS,
    CalendarCoverageError,
    CalendarProvenance,
    OperatingCalendar,
)

__all__ = [
    "ACCESSION_HEADER_SOURCES",
    "DateDivergenceClassification",
    "DateDivergenceReason",
    "classify_date_divergence",
    "is_mapped_cohort",
    "OUT_OF_SCOPE_COHORT",
    "SEC_TIMEZONE_NAME",
    "SUPPORT_2009_COHORT",
    "AcceptanceTimestamps",
    "CohortAssignment",
    "DateObservation",
    "ResolvedDate",
    "SourceConflict",
    "SourceKind",
    "TemporalPolicyError",
    "acceptance_date_sec",
    "acceptance_timestamps",
    "assign_cohorts",
    "cohort_name_for",
    "correction_status",
    "resolve_acceptance_value",
    "resolve_official_filing_date",
]

SourceKind = Literal[
    "complete_submission_header",
    "sgml_header",
    "submissions_api",
    "master_index",
]

ACCESSION_HEADER_SOURCES: Final[frozenset[str]] = frozenset(
    {"complete_submission_header", "sgml_header"}
)
"""Co-authoritative accession-header sources. Neither outranks the other."""

_PRECEDENCE: Final[dict[str, int]] = {
    "complete_submission_header": 1,
    "sgml_header": 1,
    "submissions_api": 2,
    "master_index": 2,
}

SEC_TIMEZONE_NAME: Final = "America/New_York"
SUPPORT_2009_COHORT: Final = "support_2009"
OUT_OF_SCOPE_COHORT: Final = "out_of_scope"
_ACCEPTANCE_PATTERN: Final = re.compile(r"^\d{14}$")

DateDivergenceReason = Literal[
    "same_day_filing",
    "expected_after_cutoff_rollover",
    "post_acceptance_date_correction",
    "unexplained_date_divergence",
]
"""Approved reasons for a difference between acceptance and official filing dates."""


class TemporalPolicyError(DisclosureDriftError):
    """Raised when a temporal value is malformed or violates policy."""


# --------------------------------------------------------------------------- #
# Observations and resolution
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class DateObservation:
    """One observation of a date-like accession field from one source."""

    source: SourceKind
    field_name: str
    raw_value: str
    observed_at_utc: datetime
    snapshot_id: str
    parsed_date: date | None = None

    @property
    def precedence_rank(self) -> int:
        """Lower is stronger. Accession-header sources share rank 1."""
        return _PRECEDENCE[self.source]

    @property
    def is_accession_header(self) -> bool:
        """Whether this observation came from the co-authoritative header class."""
        return self.source in ACCESSION_HEADER_SOURCES


@dataclass(frozen=True, slots=True)
class SourceConflict:
    """A preserved disagreement between source observations."""

    kind: Literal[
        "accession_header_conflict",
        "provisional_disagreement",
        "provisional_versus_canonical",
    ]
    field_name: str
    values: tuple[str, ...]
    sources: tuple[str, ...]
    detail: str


@dataclass(frozen=True, slots=True)
class ResolvedDate:
    """Resolution outcome for one date-like field.

    ``value`` is ``None`` when policy forbids choosing between conflicting
    co-authoritative observations. Every observation is retained regardless.
    """

    field_name: str
    value: date | None
    source: SourceKind | None
    precedence_rank: int | None
    observations: tuple[DateObservation, ...]
    conflicts: tuple[SourceConflict, ...] = ()
    reason_codes: tuple[str, ...] = ()

    @property
    def is_canonical(self) -> bool:
        """Whether the resolved value came from the accession-header class."""
        return self.source is not None and self.source in ACCESSION_HEADER_SOURCES


def _parsed(observations: Iterable[DateObservation]) -> tuple[DateObservation, ...]:
    return tuple(item for item in observations if item.parsed_date is not None)


def _distinct_dates(observations: Sequence[DateObservation]) -> tuple[date, ...]:
    seen: list[date] = []
    for item in observations:
        parsed = item.parsed_date
        if parsed is not None and parsed not in seen:
            seen.append(parsed)
    return tuple(seen)


def _resolve(field_name: str, observations: Sequence[DateObservation]) -> ResolvedDate:
    """Shared resolution logic for date-like fields."""
    usable = _parsed(observations)
    if not usable:
        return ResolvedDate(
            field_name=field_name,
            value=None,
            source=None,
            precedence_rank=None,
            observations=tuple(observations),
            reason_codes=("SEC_SCHEMA_REQUIRED_FIELD_MISSING",),
        )

    header = tuple(item for item in usable if item.is_accession_header)
    provisional = tuple(item for item in usable if not item.is_accession_header)
    conflicts: list[SourceConflict] = []
    reasons: list[str] = []

    if header:
        header_values = _distinct_dates(header)
        if len(header_values) > 1:
            conflicts.append(
                SourceConflict(
                    kind="accession_header_conflict",
                    field_name=field_name,
                    values=tuple(value.isoformat() for value in header_values),
                    sources=tuple(item.source for item in header),
                    detail=(
                        "co-authoritative accession-header sources disagree; "
                        "neither may be selected silently"
                    ),
                )
            )
            reasons.append("REVIEW_ACCESSION_HEADER_SOURCE_CONFLICT")
            return ResolvedDate(
                field_name=field_name,
                value=None,
                source=None,
                precedence_rank=1,
                observations=tuple(observations),
                conflicts=tuple(conflicts),
                reason_codes=tuple(reasons),
            )

        resolved_value = header_values[0]
        chosen = header[0]
        differing = tuple(item for item in provisional if item.parsed_date != resolved_value)
        if differing:
            values = {resolved_value.isoformat()}
            values.update(
                item.parsed_date.isoformat() for item in differing if item.parsed_date is not None
            )
            conflicts.append(
                SourceConflict(
                    kind="provisional_versus_canonical",
                    field_name=field_name,
                    values=tuple(sorted(values)),
                    sources=tuple(item.source for item in differing),
                    detail="provisional discovery value disagrees with the canonical header value",
                )
            )
        return ResolvedDate(
            field_name=field_name,
            value=resolved_value,
            source=chosen.source,
            precedence_rank=1,
            observations=tuple(observations),
            conflicts=tuple(conflicts),
            reason_codes=tuple(reasons),
        )

    provisional_values = _distinct_dates(provisional)
    if len(provisional_values) > 1:
        conflicts.append(
            SourceConflict(
                kind="provisional_disagreement",
                field_name=field_name,
                values=tuple(value.isoformat() for value in provisional_values),
                sources=tuple(item.source for item in provisional),
                detail="provisional discovery sources disagree and no header value is available",
            )
        )
        reasons.append("REVIEW_PROVISIONAL_DATE_DISAGREEMENT")
        return ResolvedDate(
            field_name=field_name,
            value=None,
            source=None,
            precedence_rank=2,
            observations=tuple(observations),
            conflicts=tuple(conflicts),
            reason_codes=tuple(reasons),
        )

    return ResolvedDate(
        field_name=field_name,
        value=provisional_values[0],
        source=provisional[0].source,
        precedence_rank=2,
        observations=tuple(observations),
    )


def resolve_official_filing_date(observations: Sequence[DateObservation]) -> ResolvedDate:
    """Resolve the official SEC filing date from all retained observations."""
    return _resolve("filing_date_sec", observations)


def resolve_acceptance_value(observations: Sequence[DateObservation]) -> ResolvedDate:
    """Resolve the acceptance **date** from all retained observations.

    Raw acceptance strings are preserved by the caller; this resolves only the
    SEC calendar date used for the audit cohort.
    """
    return _resolve("acceptance_date_sec", observations)


# --------------------------------------------------------------------------- #
# Acceptance timestamps
# --------------------------------------------------------------------------- #
def acceptance_date_sec(raw_value: str) -> date:
    """Return the SEC calendar acceptance date from a ``YYYYMMDDHHMMSS`` value.

    The date is taken from the **first eight characters**. No timezone conversion
    is performed, because the SEC calendar date is definitional, not derived.

    Raises:
        TemporalPolicyError: the raw value is not fourteen digits.
    """
    candidate = raw_value.strip()
    if not _ACCEPTANCE_PATTERN.match(candidate):
        message = (
            f"acceptance value {raw_value!r} is not a fourteen-digit YYYYMMDDHHMMSS string\n"
            "Fix: preserve the raw SEC value and report it for review."
        )
        raise TemporalPolicyError(message)
    try:
        return date(int(candidate[0:4]), int(candidate[4:6]), int(candidate[6:8]))
    except ValueError as exc:
        message = f"acceptance value {raw_value!r} contains an impossible date: {exc}"
        raise TemporalPolicyError(message) from exc


@dataclass(frozen=True, slots=True)
class AcceptanceTimestamps:
    """Raw and normalized acceptance representations."""

    raw: str
    date_sec: date
    datetime_et: datetime
    datetime_utc: datetime

    @property
    def is_after_normal_cutoff(self) -> bool:
        """Whether acceptance occurred at or after the frozen 17:30 Eastern cutoff.

        Indicative only. The official filing date, not this flag, assigns cohorts.
        """
        return self.datetime_et.timetz().replace(tzinfo=None) >= FROZEN_FILING_CUTOFF_ET


def acceptance_timestamps(raw_value: str) -> AcceptanceTimestamps:
    """Normalize an SEC acceptance value while preserving the raw string.

    Raises:
        TemporalPolicyError: the value is malformed or the zone database is absent.
        ReviewRequiredError: the wall-clock time is nonexistent (spring forward) or
            ambiguous (fall back) under SEC Eastern-time policy. The two cases carry
            distinct messages and reason codes, and neither picks an offset.
    """
    candidate = raw_value.strip()
    day = acceptance_date_sec(candidate)
    try:
        zone = ZoneInfo(SEC_TIMEZONE_NAME)
    except ZoneInfoNotFoundError as exc:  # pragma: no cover - platform dependent
        message = (
            f"time-zone database entry {SEC_TIMEZONE_NAME!r} is unavailable: {exc}\n"
            "Fix: install system tzdata or the tzdata package."
        )
        raise TemporalPolicyError(message) from exc

    try:
        naive = datetime(
            day.year,
            day.month,
            day.day,
            int(candidate[8:10]),
            int(candidate[10:12]),
            int(candidate[12:14]),
        )
    except ValueError as exc:
        message = f"acceptance value {raw_value!r} contains an impossible time: {exc}"
        raise TemporalPolicyError(message) from exc

    # Round-trip both folds through UTC. A candidate survives only when the wall
    # clock it renders back to is the wall clock we started from.
    candidates = [
        aware
        for aware in (naive.replace(tzinfo=zone, fold=fold) for fold in (0, 1))
        if aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == naive
    ]

    if not candidates:
        message = (
            f"acceptance value {raw_value!r} does not exist in {SEC_TIMEZONE_NAME}; the "
            "wall-clock time is skipped by the daylight-saving spring-forward transition, "
            "so it cannot be interpreted as supplied. Stopping for review."
        )
        raise ReviewRequiredError(message, ("REVIEW_TIMEZONE_NONEXISTENT",))

    offsets = {candidate.utcoffset() for candidate in candidates}
    if len(offsets) > 1:
        rendered = ", ".join(sorted(str(offset) for offset in offsets))
        message = (
            f"acceptance value {raw_value!r} is ambiguous in {SEC_TIMEZONE_NAME}; the "
            f"wall-clock time occurs twice under the daylight-saving fall-back with "
            f"offsets {rendered}. Stopping for review rather than assuming an offset."
        )
        raise ReviewRequiredError(message, ("REVIEW_TIMEZONE_AMBIGUOUS",))

    resolved = candidates[0]
    return AcceptanceTimestamps(
        raw=raw_value,
        date_sec=day,
        datetime_et=resolved,
        datetime_utc=resolved.astimezone(UTC),
    )


# --------------------------------------------------------------------------- #
# Cohort assignment
# --------------------------------------------------------------------------- #
def cohort_name_for(day: date) -> str:
    """Return the cohort label for ``day``.

    2009 filings are ``support_2009`` per Decision 008 section 3. Dates outside
    the frozen design are ``out_of_scope``. The frozen windows are unchanged.
    """
    if day.year == 2009:
        return SUPPORT_2009_COHORT
    window = cohort_for(day)
    return window.name if window is not None else OUT_OF_SCOPE_COHORT


@dataclass(frozen=True, slots=True)
class DateDivergenceClassification:
    """Why an official filing date differs from the SEC acceptance date.

    Classification is reason-based. No calendar-day allowance is used, and no
    correction is ever silently converted into ordinary after-hours behaviour.
    """

    reason: DateDivergenceReason
    explained: bool
    requires_review: bool
    blocks_release: bool
    detail: str
    reason_codes: tuple[str, ...] = ()
    calendar_provenance: CalendarProvenance | None = None


def classify_date_divergence(
    official_filing_date: date,
    acceptance: AcceptanceTimestamps | date | None,
    *,
    calendar: OperatingCalendar | None = None,
    cutoff: time = FROZEN_FILING_CUTOFF_ET,
    form_type: str | None = None,
    date_as_of_change: date | None = None,
    correction_indicated: bool = False,
    affects_cohort_assignment: bool = False,
) -> DateDivergenceClassification:
    """Classify the acceptance-to-filing-date relationship by reason.

    Order of evaluation matters: a correction is recognized *before* rollover, so an
    authorized filing-date adjustment can never be recorded as after-hours behaviour.

    An expected rollover requires **all** of: acceptance on a proven operating day,
    acceptance at or after the frozen 17:30 America/New_York cutoff, and an official
    filing date equal to the next operating business day.

    Args:
        cutoff: Test-injection hook only. Production uses the frozen
            :data:`~disclosure_drift.sec.calendar.FROZEN_FILING_CUTOFF_ET`; there is
            no configuration key or environment variable for it.
        form_type: When supplied, the frozen cutoff applies only to the supported
            annual-report forms; any other form cannot be classified as a rollover.
    """
    acceptance_date = _acceptance_date_of(acceptance)
    if acceptance_date is None:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=False,
            detail="no acceptance date is available, so the relationship cannot be established",
            reason_codes=("REVIEW_MISSING_ACCEPTANCE_TIMESTAMP",),
        )

    if official_filing_date == acceptance_date:
        return DateDivergenceClassification(
            reason="same_day_filing",
            explained=True,
            requires_review=False,
            blocks_release=False,
            detail="official filing date equals the SEC acceptance date",
            reason_codes=("SAME_DAY_FILING",),
        )

    if official_filing_date < acceptance_date:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=True,
            detail=(
                "official filing date precedes the acceptance date; SEC mechanics do not "
                "explain this and it is never an ordinary rollover"
            ),
            reason_codes=("REVIEW_FILING_DATE_BEFORE_ACCEPTANCE", "UNEXPLAINED_DATE_DIVERGENCE"),
        )

    correction = correction_indicated or (
        date_as_of_change is not None and date_as_of_change > acceptance_date
    )
    if correction:
        codes = ["POST_ACCEPTANCE_DATE_CORRECTION"]
        if affects_cohort_assignment:
            codes.append("REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY")
        return DateDivergenceClassification(
            reason="post_acceptance_date_correction",
            explained=True,
            requires_review=affects_cohort_assignment,
            blocks_release=False,
            detail=(
                "filing metadata or DATE AS OF CHANGE indicates an authorized later correction "
                "or filing-date adjustment"
            ),
            reason_codes=tuple(codes),
        )

    if calendar is None:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=True,
            detail="no EDGAR operating calendar was supplied, so rollover cannot be established",
            reason_codes=("OPERATING_CALENDAR_UNAVAILABLE", "UNEXPLAINED_DATE_DIVERGENCE"),
        )

    try:
        accepted_on_operating_day = calendar.is_operating_day(acceptance_date)
        expected_rollover = calendar.next_operating_day(acceptance_date)
    except CalendarCoverageError as exc:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=True,
            detail=f"operating calendar cannot answer for these dates: {exc}",
            reason_codes=("OPERATING_CALENDAR_UNAVAILABLE", "UNEXPLAINED_DATE_DIVERGENCE"),
            calendar_provenance=calendar.provenance,
        )

    if not accepted_on_operating_day:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=True,
            detail=(
                f"acceptance date {acceptance_date.isoformat()} is not an EDGAR operating "
                "day; EDGAR does not ordinarily accept filings on weekends or federal "
                "holidays, so rollover cannot be inferred and the observation requires "
                "reconciliation"
            ),
            reason_codes=(
                "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY",
                "UNEXPLAINED_DATE_DIVERGENCE",
            ),
            calendar_provenance=calendar.provenance,
        )

    if form_type is not None and form_type not in SUPPORTED_CUTOFF_FORMS:
        return DateDivergenceClassification(
            reason="unexplained_date_divergence",
            explained=False,
            requires_review=True,
            blocks_release=True,
            detail=(
                f"the frozen after-hours cutoff does not govern form {form_type!r}, "
                "so an after-cutoff rollover cannot be inferred"
            ),
            reason_codes=("UNEXPLAINED_DATE_DIVERGENCE",),
            calendar_provenance=calendar.provenance,
        )

    acceptance_time = _acceptance_time_of(acceptance)
    after_cutoff = acceptance_time is not None and acceptance_time >= cutoff

    if after_cutoff and official_filing_date == expected_rollover:
        return DateDivergenceClassification(
            reason="expected_after_cutoff_rollover",
            explained=True,
            requires_review=False,
            blocks_release=False,
            detail=(
                f"accepted on operating day {acceptance_date.isoformat()} at or after the "
                f"frozen {cutoff.isoformat()} cutoff; the official filing date equals the "
                f"next EDGAR operating day {expected_rollover.isoformat()}"
            ),
            reason_codes=("EXPECTED_AFTER_CUTOFF_ROLLOVER",),
            calendar_provenance=calendar.provenance,
        )

    return DateDivergenceClassification(
        reason="unexplained_date_divergence",
        explained=False,
        requires_review=True,
        blocks_release=True,
        detail=(
            "the difference matches no approved rule: expected next operating day "
            f"{expected_rollover.isoformat()}, observed filing date "
            f"{official_filing_date.isoformat()}"
        ),
        reason_codes=("UNEXPLAINED_DATE_DIVERGENCE",),
        calendar_provenance=calendar.provenance,
    )


def _acceptance_date_of(acceptance: AcceptanceTimestamps | date | None) -> date | None:
    if acceptance is None:
        return None
    if isinstance(acceptance, AcceptanceTimestamps):
        return acceptance.date_sec
    return acceptance


def _acceptance_time_of(acceptance: AcceptanceTimestamps | date | None) -> time | None:
    if isinstance(acceptance, AcceptanceTimestamps):
        return acceptance.datetime_et.timetz().replace(tzinfo=None)
    return None


def is_mapped_cohort(name: str | None) -> bool:
    """Whether a cohort label resolves to supported cohort coverage."""
    return name is not None and name != OUT_OF_SCOPE_COHORT


@dataclass(frozen=True, slots=True)
class CohortAssignment:
    """Dual cohort assignment plus divergence audit facts.

    Three distinct concepts are kept separate (Decision 010 section 8):

    * ``date_divergence`` — the dates differ, even inside one cohort;
    * ``cohort_boundary_crossing`` — both dates map and the cohort names differ;
    * ``coverage_boundary_divergence`` — one date maps and the other does not.
    """

    official_filing_date: date
    official_filing_temporal_cohort: str
    acceptance_date: date | None
    accepted_temporal_cohort: str | None
    date_divergence: bool
    cohort_boundary_crossing: bool
    coverage_boundary_divergence: bool
    touches_primary_test: bool
    divergence: DateDivergenceClassification
    reason_codes: tuple[str, ...] = ()

    @property
    def cohort_divergence(self) -> bool:
        """Whether the two cohort labels differ in any way."""
        return self.cohort_boundary_crossing or self.coverage_boundary_divergence

    @property
    def divergence_explained(self) -> bool:
        """Whether the date difference is explained by an approved rule."""
        return self.divergence.explained

    @property
    def requires_manual_review(self) -> bool:
        """Whether policy requires human review before release freezing."""
        return (
            self.cohort_boundary_crossing
            or self.coverage_boundary_divergence
            or self.divergence.requires_review
        )

    @property
    def blocks_release(self) -> bool:
        """Whether this assignment blocks release freezing on its own."""
        return self.divergence.blocks_release or self.coverage_boundary_divergence

    @property
    def requires_explicit_approval(self) -> bool:
        """Whether the accession enters or leaves the untouched 2024 cohort."""
        return self.touches_primary_test


def assign_cohorts(
    official_filing_date: date,
    acceptance: AcceptanceTimestamps | date | None,
    *,
    calendar: OperatingCalendar | None = None,
    cutoff: time = FROZEN_FILING_CUTOFF_ET,
    form_type: str | None = None,
    date_as_of_change: date | None = None,
    correction_indicated: bool = False,
) -> CohortAssignment:
    """Assign the authoritative and audit cohorts and classify any divergence.

    ``cohort_for()`` is called twice with different date sources. The frozen
    windows are never modified.
    """
    acceptance_date = _acceptance_date_of(acceptance)
    official_cohort = cohort_name_for(official_filing_date)
    accepted_cohort = None if acceptance_date is None else cohort_name_for(acceptance_date)

    official_mapped = is_mapped_cohort(official_cohort)
    accepted_mapped = is_mapped_cohort(accepted_cohort)

    both_mapped = official_mapped and accepted_mapped
    cohort_boundary_crossing = both_mapped and official_cohort != accepted_cohort
    coverage_boundary_divergence = (
        acceptance_date is not None and official_mapped != accepted_mapped
    )

    divergence = classify_date_divergence(
        official_filing_date,
        acceptance,
        calendar=calendar,
        cutoff=cutoff,
        form_type=form_type,
        date_as_of_change=date_as_of_change,
        correction_indicated=correction_indicated,
        affects_cohort_assignment=cohort_boundary_crossing or coverage_boundary_divergence,
    )

    reasons = list(divergence.reason_codes)
    if cohort_boundary_crossing:
        reasons.append("REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING")
    if coverage_boundary_divergence:
        reasons.append("COVERAGE_BOUNDARY_DIVERGENCE")

    primary = cohort_for(date(2024, 6, 30))
    primary_name = primary.name if primary is not None else "primary_test"
    touches_primary_test = (
        cohort_boundary_crossing or coverage_boundary_divergence
    ) and primary_name in {official_cohort, accepted_cohort}

    return CohortAssignment(
        official_filing_date=official_filing_date,
        official_filing_temporal_cohort=official_cohort,
        acceptance_date=acceptance_date,
        accepted_temporal_cohort=accepted_cohort,
        date_divergence=acceptance_date is not None and official_filing_date != acceptance_date,
        cohort_boundary_crossing=cohort_boundary_crossing,
        coverage_boundary_divergence=coverage_boundary_divergence,
        touches_primary_test=touches_primary_test,
        divergence=divergence,
        reason_codes=tuple(dict.fromkeys(reasons)),
    )


def correction_status(
    official_filing_date: date,
    date_as_of_change: date | None,
    cohort_assignment: CohortAssignment | None = None,
) -> tuple[str, tuple[str, ...]]:
    """Classify post-acceptance correction state and any review reasons."""
    if date_as_of_change is None or date_as_of_change <= official_filing_date:
        return "none", ()
    corrected_cohort = cohort_name_for(date_as_of_change)
    if corrected_cohort != cohort_name_for(official_filing_date):
        return "post_acceptance_correction", ("REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY",)
    if cohort_assignment is not None and cohort_assignment.cohort_divergence:
        return "post_acceptance_correction", ("REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING",)
    return "post_acceptance_correction", ()
