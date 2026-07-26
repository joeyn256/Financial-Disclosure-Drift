"""EDGAR operating-calendar abstraction and the frozen filing cutoff.

Decision 010 sections 5.1 and 5.2.

Cutoff rollover is classified against an **injected** operating calendar. Nothing
here assumes that every weekday is an EDGAR operating day, and no calendar is
hardcoded. Stage M2.1 supplies synthetic calendars in tests; Stage M2.2 loads the
production calendar from an approved official source and records its snapshot
provenance.

The production after-hours cutoff is **frozen** at 17:30 America/New_York for the
supported annual-report forms. It is deliberately absent from ``configs/project.yaml``
and from the environment allowlist: tests may inject another cutoff, but a
production change requires a versioned methodological update supported by official
SEC documentation.

Day status is **tri-state** (Decision 011): ``operating``, ``non_operating``, or
``unknown``. :class:`EvidenceCalendar` derives status from the approved evidence
hierarchy and fails closed on ``unknown``; :class:`StaticOperatingCalendar` remains a
synthetic fixture calendar for tests.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, time
from types import MappingProxyType
from typing import Final, Literal, Protocol, runtime_checkable

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "CALENDAR_DERIVATION_VERSION",
    "CALENDAR_PROVENANCE_DECISION_RECORD",
    "CUTOFF_DECISION_RECORD",
    "EVIDENCE_PRECEDENCE",
    "FROZEN_FILING_CUTOFF_ET",
    "SUPPORTED_CUTOFF_FORMS",
    "AnnualHolidayList",
    "CalendarCoverageError",
    "CalendarCoverageReport",
    "CalendarProvenance",
    "DayDetermination",
    "DayEvidence",
    "DayStatus",
    "EvidenceCalendar",
    "EvidenceKind",
    "GeneralOperatingRule",
    "OperatingCalendar",
    "PositiveActivity",
    "StaticOperatingCalendar",
    "cutoff_for_form",
]

FROZEN_FILING_CUTOFF_ET: Final = time(17, 30)
"""Frozen production after-hours cutoff, 17:30 America/New_York.

Not user-configurable. There is no YAML key and no environment variable for it.
Tests may inject a different cutoff; production policy changes require a versioned
methodological update supported by official SEC documentation.
"""

SUPPORTED_CUTOFF_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
"""Forms whose after-hours rollover is governed by the frozen cutoff."""

CUTOFF_DECISION_RECORD: Final = (
    "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"
)

CalendarSourceKind = Literal["synthetic_fixture", "sec_snapshot"]


class CalendarCoverageError(DisclosureDriftError):
    """Raised when a date falls outside the calendar's known coverage."""


@dataclass(frozen=True, slots=True)
class CalendarProvenance:
    """Where an operating calendar came from."""

    source_kind: CalendarSourceKind
    description: str
    snapshot_id: str | None = None
    retrieved_at_utc: str | None = None

    def __post_init__(self) -> None:
        """Require snapshot provenance for any non-synthetic calendar."""
        if self.source_kind == "sec_snapshot" and not self.snapshot_id:
            message = "an SEC-derived operating calendar requires a snapshot_id"
            raise CalendarCoverageError(message)

    @property
    def is_synthetic(self) -> bool:
        """Whether this calendar is a test fixture rather than official data."""
        return self.source_kind == "synthetic_fixture"


def cutoff_for_form(form_type: str) -> time:
    """Return the frozen cutoff for a supported annual-report form.

    Raises:
        CalendarCoverageError: the form is outside the supported set, so no frozen
            cutoff applies and rollover must not be inferred.
    """
    if form_type not in SUPPORTED_CUTOFF_FORMS:
        supported = ", ".join(sorted(SUPPORTED_CUTOFF_FORMS))
        message = (
            f"no frozen filing cutoff is defined for form {form_type!r}; "
            f"the frozen cutoff governs {supported} only ({CUTOFF_DECISION_RECORD})"
        )
        raise CalendarCoverageError(message)
    return FROZEN_FILING_CUTOFF_ET


@runtime_checkable
class OperatingCalendar(Protocol):
    """Minimal EDGAR operating-day interface."""

    @property
    def provenance(self) -> CalendarProvenance:
        """Where the calendar came from."""
        ...  # pragma: no cover - protocol

    def covers(self, day: date) -> bool:
        """Whether the calendar can answer questions about ``day``."""
        ...  # pragma: no cover - protocol

    def is_operating_day(self, day: date) -> bool:
        """Whether EDGAR operated on ``day``."""
        ...  # pragma: no cover - protocol

    def next_operating_day(self, day: date) -> date:
        """Return the first operating day strictly after ``day``."""
        ...  # pragma: no cover - protocol


@dataclass(frozen=True, slots=True)
class StaticOperatingCalendar:
    """An explicit set of operating days with a bounded coverage window."""

    operating_days: frozenset[date]
    provenance: CalendarProvenance
    coverage_start: date
    coverage_end: date

    @classmethod
    def from_days(
        cls,
        days: Iterable[date],
        provenance: CalendarProvenance,
    ) -> StaticOperatingCalendar:
        """Build a calendar whose coverage spans the supplied days."""
        ordered = sorted(set(days))
        if not ordered:
            message = "an operating calendar needs at least one day"
            raise CalendarCoverageError(message)
        return cls(
            operating_days=frozenset(ordered),
            provenance=provenance,
            coverage_start=ordered[0],
            coverage_end=ordered[-1],
        )

    def covers(self, day: date) -> bool:
        """Whether ``day`` falls inside the coverage window."""
        return self.coverage_start <= day <= self.coverage_end

    def is_operating_day(self, day: date) -> bool:
        """Whether EDGAR operated on ``day``.

        Raises:
            CalendarCoverageError: ``day`` is outside the coverage window, so the
                answer is unknown rather than negative.
        """
        if not self.covers(day):
            message = (
                f"{day.isoformat()} is outside calendar coverage "
                f"{self.coverage_start.isoformat()} to {self.coverage_end.isoformat()}"
            )
            raise CalendarCoverageError(message)
        return day in self.operating_days

    def next_operating_day(self, day: date) -> date:
        """Return the first operating day strictly after ``day``.

        Raises:
            CalendarCoverageError: no operating day after ``day`` is known.
        """
        later = sorted(candidate for candidate in self.operating_days if candidate > day)
        if not later:
            message = (
                f"no operating day after {day.isoformat()} is known; "
                f"coverage ends {self.coverage_end.isoformat()}"
            )
            raise CalendarCoverageError(message)
        return later[0]


# --------------------------------------------------------------------------- #
# Tri-state evidence calendar (Decision 011)
# --------------------------------------------------------------------------- #
CALENDAR_DERIVATION_VERSION: Final = "edgar-operating-calendar-derivation/1.0"
CALENDAR_PROVENANCE_DECISION_RECORD: Final = (
    "Docs/Decisions/decision_011_edgar_operating_calendar_provenance.md"
)

DayStatus = Literal["operating", "non_operating", "unknown"]
EvidenceKind = Literal[
    "date_specific_announcement",
    "annual_calendar_snapshot",
    "general_operating_rule",
    "positive_activity",
]

EVIDENCE_PRECEDENCE: Final[Mapping[EvidenceKind, int]] = MappingProxyType(
    {
        "date_specific_announcement": 1,
        "annual_calendar_snapshot": 2,
        "general_operating_rule": 3,
        "positive_activity": 4,
    }
)
"""Approved evidence hierarchy. Lower is more authoritative."""

_WEEKEND_DAYS: Final[frozenset[int]] = frozenset({5, 6})


@dataclass(frozen=True, slots=True)
class DayEvidence:
    """One piece of evidence behind a day determination."""

    kind: EvidenceKind
    evidence_id: str
    source_observation_id: str | None
    detail: str

    @property
    def precedence(self) -> int:
        """Authority rank of this evidence kind."""
        return EVIDENCE_PRECEDENCE[self.kind]


@dataclass(frozen=True, slots=True)
class DayDetermination:
    """Tri-state status for one date with its supporting evidence."""

    day: date
    status: DayStatus
    evidence: tuple[DayEvidence, ...]
    derivation_version: str = CALENDAR_DERIVATION_VERSION
    conflicting: bool = False
    reason_codes: tuple[str, ...] = ()

    @property
    def is_proven(self) -> bool:
        """Whether official evidence settled this date."""
        return self.status != "unknown"

    @property
    def source_observation_ids(self) -> tuple[str, ...]:
        """Observation identifiers behind this determination."""
        return tuple(
            item.source_observation_id
            for item in self.evidence
            if item.source_observation_id is not None
        )


@dataclass(frozen=True, slots=True)
class GeneralOperatingRule:
    """The official SEC rule that ordinary operations run Monday through Friday.

    It establishes weekends as non-operating. It never supplies an unproven historical
    holiday list, so a weekday in a year without a preserved annual snapshot stays
    ``unknown``.
    """

    evidence_id: str
    source_observation_id: str | None = None
    detail: str = "official SEC general operating rule: ordinary operations Monday to Friday"

    def as_evidence(self) -> DayEvidence:
        """Return this rule as a day-evidence record."""
        return DayEvidence(
            kind="general_operating_rule",
            evidence_id=self.evidence_id,
            source_observation_id=self.source_observation_id,
            detail=self.detail,
        )


@dataclass(frozen=True, slots=True)
class AnnualHolidayList:
    """Listed filing holidays for exactly the year a preserved snapshot covers."""

    year: int
    holidays: frozenset[date]
    evidence_id: str
    source_observation_id: str | None = None

    def as_evidence(self) -> DayEvidence:
        """Return this snapshot as a day-evidence record."""
        return DayEvidence(
            kind="annual_calendar_snapshot",
            evidence_id=self.evidence_id,
            source_observation_id=self.source_observation_id,
            detail=f"annual EDGAR calendar snapshot covering {self.year}",
        )


@dataclass(frozen=True, slots=True)
class PositiveActivity:
    """Preserved official evidence that EDGAR operated on a date.

    Absence of activity is never evidence of closure.
    """

    day: date
    evidence_id: str
    source_observation_id: str | None = None
    detail: str = "official EDGAR activity observed"

    def as_evidence(self) -> DayEvidence:
        """Return this activity as a day-evidence record."""
        return DayEvidence(
            kind="positive_activity",
            evidence_id=self.evidence_id,
            source_observation_id=self.source_observation_id,
            detail=self.detail,
        )


@dataclass(frozen=True, slots=True)
class Announcement:
    """A date-specific SEC EDGAR announcement, the highest authority for its dates."""

    days: frozenset[date]
    status: Literal["operating", "non_operating"]
    evidence_id: str
    source_observation_id: str | None = None
    detail: str = "date-specific SEC EDGAR announcement"

    def as_evidence(self) -> DayEvidence:
        """Return this announcement as a day-evidence record."""
        return DayEvidence(
            kind="date_specific_announcement",
            evidence_id=self.evidence_id,
            source_observation_id=self.source_observation_id,
            detail=self.detail,
        )


@dataclass(frozen=True, slots=True)
class CalendarCoverageReport:
    """Date-specific coverage accounting for a requested window."""

    window_start: date
    window_end: date
    derivation_version: str
    operating: tuple[date, ...]
    non_operating: tuple[date, ...]
    unknown: tuple[date, ...]
    conflicting: tuple[date, ...]
    evidence_by_date: Mapping[str, tuple[str, ...]]
    source_observation_ids: tuple[str, ...]
    first_supported: date | None
    last_supported: date | None

    @property
    def fully_supported(self) -> bool:
        """Whether every date in the window is proven and unconflicted."""
        return not self.unknown and not self.conflicting

    def as_summary(self) -> Mapping[str, object]:
        """Return a deterministic summary for the census audit."""
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "derivation_version": self.derivation_version,
            "operating": len(self.operating),
            "non_operating": len(self.non_operating),
            "unknown": len(self.unknown),
            "conflicting": len(self.conflicting),
            "first_supported": None
            if self.first_supported is None
            else (self.first_supported.isoformat()),
            "last_supported": None
            if self.last_supported is None
            else (self.last_supported.isoformat()),
            "fully_supported": self.fully_supported,
            "source_observations": len(self.source_observation_ids),
        }


class EvidenceCalendar:
    """Operating calendar derived from approved official SEC evidence.

    Implements the :class:`OperatingCalendar` protocol and fails closed: an
    ``unknown`` or conflicted date raises :class:`CalendarCoverageError` rather than
    guessing, so rollover classification degrades to
    ``unexplained_date_divergence`` with ``OPERATING_CALENDAR_UNAVAILABLE``.
    """

    def __init__(
        self,
        provenance: CalendarProvenance,
        *,
        general_rule: GeneralOperatingRule | None = None,
        annual_holidays: Iterable[AnnualHolidayList] = (),
        announcements: Iterable[Announcement] = (),
        activity: Iterable[PositiveActivity] = (),
    ) -> None:
        self._provenance = provenance
        self._general_rule = general_rule
        self._annual = {item.year: item for item in annual_holidays}
        self._announcements = tuple(announcements)
        self._activity = {item.day: item for item in activity}

    @property
    def provenance(self) -> CalendarProvenance:
        """Where this calendar's evidence came from."""
        return self._provenance

    @property
    def derivation_version(self) -> str:
        """Version of the derivation rules that produced determinations."""
        return CALENDAR_DERIVATION_VERSION

    # -- determination ------------------------------------------------------ #
    def status_for(self, day: date) -> DayDetermination:
        """Return the tri-state determination for ``day``."""
        announcements = [item for item in self._announcements if day in item.days]
        if announcements:
            statuses = {item.status for item in announcements}
            evidence = tuple(item.as_evidence() for item in announcements)
            if len(statuses) > 1:
                return DayDetermination(
                    day=day,
                    status="unknown",
                    evidence=evidence,
                    conflicting=True,
                    reason_codes=("REVIEW_CALENDAR_EVIDENCE_CONFLICT",),
                )
            return DayDetermination(day=day, status=statuses.pop(), evidence=evidence)

        candidates: list[tuple[DayStatus, DayEvidence]] = []

        snapshot = self._annual.get(day.year)
        is_weekend = day.weekday() in _WEEKEND_DAYS
        if self._general_rule is not None and is_weekend:
            candidates.append(("non_operating", self._general_rule.as_evidence()))
        elif snapshot is not None and not is_weekend:
            status: DayStatus = "non_operating" if day in snapshot.holidays else "operating"
            candidates.append((status, snapshot.as_evidence()))

        activity = self._activity.get(day)
        if activity is not None:
            candidates.append(("operating", activity.as_evidence()))

        if not candidates:
            return DayDetermination(
                day=day,
                status="unknown",
                evidence=(),
                reason_codes=("REVIEW_CALENDAR_DATE_UNKNOWN",),
            )

        candidate_statuses: set[DayStatus] = {status for status, _ in candidates}
        evidence = tuple(item for _, item in candidates)
        if len(candidate_statuses) > 1:
            return DayDetermination(
                day=day,
                status="unknown",
                evidence=evidence,
                conflicting=True,
                reason_codes=("REVIEW_CALENDAR_EVIDENCE_CONFLICT",),
            )
        return DayDetermination(day=day, status=candidate_statuses.pop(), evidence=evidence)

    # -- OperatingCalendar protocol ----------------------------------------- #
    def covers(self, day: date) -> bool:
        """Whether official evidence settles ``day``."""
        return self.status_for(day).is_proven

    def is_operating_day(self, day: date) -> bool:
        """Whether EDGAR operated on ``day``.

        Raises:
            CalendarCoverageError: the date is ``unknown`` or conflicted, so the
                answer is unproven rather than negative.
        """
        determination = self.status_for(day)
        if not determination.is_proven:
            reasons = ", ".join(determination.reason_codes)
            message = (
                f"{day.isoformat()} has no proven EDGAR operating status "
                f"({reasons or 'no evidence'}); derivation "
                f"{determination.derivation_version} fails closed"
            )
            raise CalendarCoverageError(message)
        return determination.status == "operating"

    def next_operating_day(self, day: date) -> date:
        """Return the next proven operating day after ``day``.

        Every intervening date must be proven ``non_operating`` and the returned date
        must be proven ``operating``.

        Raises:
            CalendarCoverageError: any intervening or target date is unproven.
        """
        current = date.fromordinal(day.toordinal() + 1)
        horizon = date.fromordinal(day.toordinal() + 30)
        while current <= horizon:
            determination = self.status_for(current)
            if not determination.is_proven:
                reasons = ", ".join(determination.reason_codes)
                message = (
                    f"cannot derive the next operating day after {day.isoformat()}: "
                    f"{current.isoformat()} is unproven ({reasons or 'no evidence'})"
                )
                raise CalendarCoverageError(message)
            if determination.status == "operating":
                return current
            current = date.fromordinal(current.toordinal() + 1)
        message = (
            f"no proven operating day within thirty days after {day.isoformat()}; "
            "evidence coverage is insufficient"
        )
        raise CalendarCoverageError(message)

    # -- coverage ----------------------------------------------------------- #
    def coverage_report(self, window_start: date, window_end: date) -> CalendarCoverageReport:
        """Return date-specific coverage accounting for the requested window."""
        if window_end < window_start:
            message = "coverage window ends before it starts"
            raise CalendarCoverageError(message)

        operating: list[date] = []
        non_operating: list[date] = []
        unknown: list[date] = []
        conflicting: list[date] = []
        evidence_by_date: dict[str, tuple[str, ...]] = {}
        observations: list[str] = []

        current = window_start
        while current <= window_end:
            determination = self.status_for(current)
            evidence_by_date[current.isoformat()] = tuple(
                item.evidence_id for item in determination.evidence
            )
            observations.extend(determination.source_observation_ids)
            if determination.conflicting:
                conflicting.append(current)
            if determination.status == "operating":
                operating.append(current)
            elif determination.status == "non_operating":
                non_operating.append(current)
            else:
                unknown.append(current)
            current = date.fromordinal(current.toordinal() + 1)

        proven = sorted(operating + non_operating)
        supported = [day for day in proven if day not in conflicting]
        return CalendarCoverageReport(
            window_start=window_start,
            window_end=window_end,
            derivation_version=CALENDAR_DERIVATION_VERSION,
            operating=tuple(operating),
            non_operating=tuple(non_operating),
            unknown=tuple(unknown),
            conflicting=tuple(conflicting),
            evidence_by_date=evidence_by_date,
            source_observation_ids=tuple(dict.fromkeys(observations)),
            first_supported=supported[0] if supported else None,
            last_supported=supported[-1] if supported else None,
        )
