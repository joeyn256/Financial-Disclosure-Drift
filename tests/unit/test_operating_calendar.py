"""EDGAR operating-calendar abstraction and its provenance requirements."""

from __future__ import annotations

from datetime import date, time

import pytest

from disclosure_drift.sec.calendar import (
    CUTOFF_DECISION_RECORD,
    FROZEN_FILING_CUTOFF_ET,
    SUPPORTED_CUTOFF_FORMS,
    CalendarCoverageError,
    CalendarProvenance,
    OperatingCalendar,
    StaticOperatingCalendar,
    cutoff_for_form,
)

WEEK = [date(2024, 3, 4), date(2024, 3, 5), date(2024, 3, 6), date(2024, 3, 7), date(2024, 3, 8)]
SYNTHETIC = CalendarProvenance(
    source_kind="synthetic_fixture",
    description="synthetic operating calendar for tests",
)


def test_production_cutoff_is_frozen_at_1730_eastern() -> None:
    assert time(17, 30) == FROZEN_FILING_CUTOFF_ET


@pytest.mark.parametrize("form", ["10-K", "10-K/A", "10-KT", "10-KT/A"])
def test_frozen_cutoff_governs_the_supported_annual_report_forms(form: str) -> None:
    assert form in SUPPORTED_CUTOFF_FORMS
    assert cutoff_for_form(form) == FROZEN_FILING_CUTOFF_ET


@pytest.mark.parametrize("form", ["20-F", "40-F", "8-K", "10-Q"])
def test_unsupported_forms_have_no_frozen_cutoff(form: str) -> None:
    with pytest.raises(CalendarCoverageError, match="no frozen filing cutoff"):
        cutoff_for_form(form)


def test_cutoff_cites_its_decision_record() -> None:
    with pytest.raises(CalendarCoverageError, match="decision_010"):
        cutoff_for_form("S-1")
    assert CUTOFF_DECISION_RECORD.startswith("Docs/Decisions/decision_010")


def test_static_calendar_satisfies_the_protocol() -> None:
    calendar = StaticOperatingCalendar.from_days(WEEK, SYNTHETIC)
    assert isinstance(calendar, OperatingCalendar)


def test_coverage_window_follows_the_supplied_days() -> None:
    calendar = StaticOperatingCalendar.from_days(WEEK, SYNTHETIC)
    assert calendar.coverage_start == date(2024, 3, 4)
    assert calendar.coverage_end == date(2024, 3, 8)
    assert calendar.covers(date(2024, 3, 6))
    assert not calendar.covers(date(2024, 3, 9))


def test_operating_days_are_explicit_not_inferred_from_weekdays() -> None:
    calendar = StaticOperatingCalendar.from_days(
        [day for day in WEEK if day != date(2024, 3, 6)], SYNTHETIC
    )
    assert calendar.is_operating_day(date(2024, 3, 5))
    assert not calendar.is_operating_day(date(2024, 3, 6))
    assert calendar.next_operating_day(date(2024, 3, 5)) == date(2024, 3, 7)


def test_next_operating_day_is_strictly_later() -> None:
    calendar = StaticOperatingCalendar.from_days(WEEK, SYNTHETIC)
    assert calendar.next_operating_day(date(2024, 3, 4)) == date(2024, 3, 5)


def test_dates_outside_coverage_raise_rather_than_answering() -> None:
    calendar = StaticOperatingCalendar.from_days(WEEK, SYNTHETIC)
    with pytest.raises(CalendarCoverageError, match="outside calendar coverage"):
        calendar.is_operating_day(date(2024, 4, 1))
    with pytest.raises(CalendarCoverageError, match="no operating day after"):
        calendar.next_operating_day(date(2024, 3, 8))


def test_empty_calendar_is_refused() -> None:
    with pytest.raises(CalendarCoverageError, match="at least one day"):
        StaticOperatingCalendar.from_days([], SYNTHETIC)


def test_synthetic_provenance_is_flagged() -> None:
    assert SYNTHETIC.is_synthetic
    assert StaticOperatingCalendar.from_days(WEEK, SYNTHETIC).provenance.is_synthetic


def test_sec_derived_calendar_requires_a_snapshot_id() -> None:
    with pytest.raises(CalendarCoverageError, match="requires a snapshot_id"):
        CalendarProvenance(source_kind="sec_snapshot", description="official calendar")


def test_sec_derived_calendar_with_provenance_is_accepted() -> None:
    provenance = CalendarProvenance(
        source_kind="sec_snapshot",
        description="official EDGAR operating calendar",
        snapshot_id="snapshot-2026-07-26",
        retrieved_at_utc="2026-07-26T00:00:00Z",
    )
    calendar = StaticOperatingCalendar.from_days(WEEK, provenance)
    assert not calendar.provenance.is_synthetic
    assert calendar.provenance.snapshot_id == "snapshot-2026-07-26"


def test_duplicate_days_are_collapsed() -> None:
    calendar = StaticOperatingCalendar.from_days([*WEEK, *WEEK], SYNTHETIC)
    assert len(calendar.operating_days) == len(WEEK)
