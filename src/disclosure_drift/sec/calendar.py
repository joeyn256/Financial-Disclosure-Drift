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
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, time
from typing import Final, Literal, Protocol, runtime_checkable

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "CUTOFF_DECISION_RECORD",
    "FROZEN_FILING_CUTOFF_ET",
    "SUPPORTED_CUTOFF_FORMS",
    "CalendarCoverageError",
    "CalendarProvenance",
    "OperatingCalendar",
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
