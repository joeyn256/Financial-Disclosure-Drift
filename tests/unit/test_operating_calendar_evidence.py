"""Tri-state operating-calendar derivation and evidence manifest (Decision 011).

Every determination in this module comes from evidence objects constructed inside the
test. No SEC date is asserted from memory, no generic holiday library is consulted,
and no test touches the network.
"""

from __future__ import annotations

from datetime import date

import pytest

from disclosure_drift.sec.calendar import (
    CALENDAR_DERIVATION_VERSION,
    CALENDAR_PROVENANCE_DECISION_RECORD,
    EVIDENCE_PRECEDENCE,
    Announcement,
    AnnualHolidayList,
    CalendarCoverageError,
    CalendarProvenance,
    EvidenceCalendar,
    GeneralOperatingRule,
    OperatingCalendar,
    PositiveActivity,
)
from disclosure_drift.sec.calendar_evidence import (
    APPROVED_SEC_HOSTS,
    CALENDAR_EVIDENCE_MANIFEST,
    CALENDAR_EVIDENCE_MANIFEST_VERSION,
    CalendarEvidenceEntry,
    CalendarEvidenceError,
    approved_entries,
    entries_for_date,
    require_evidence,
    validate_manifest,
)
from disclosure_drift.sec.temporal import acceptance_timestamps, assign_cohorts

PROVENANCE = CalendarProvenance(
    source_kind="sec_snapshot",
    description="official EDGAR calendar evidence",
    snapshot_id="snapshot-test-1",
    retrieved_at_utc="2026-07-26T00:00:00Z",
)
RULE = GeneralOperatingRule(
    evidence_id="sec_general_operating_rule",
    source_observation_id="obs-rule",
)
# One synthetic listed weekday holiday supplied *as evidence by this test*.
ANNUAL_2024 = AnnualHolidayList(
    year=2024,
    holidays=frozenset({date(2024, 3, 5)}),
    evidence_id="annual_calendar_2024",
    source_observation_id="obs-annual-2024",
)
FRIDAY = date(2024, 3, 1)
SATURDAY = date(2024, 3, 2)
SUNDAY = date(2024, 3, 3)
MONDAY = date(2024, 3, 4)
HOLIDAY = date(2024, 3, 5)
WEDNESDAY = date(2024, 3, 6)
UNPROVEN_WEEKDAY = date(2019, 3, 4)


def calendar(**overrides: object) -> EvidenceCalendar:
    """Build an evidence calendar with the general rule and the 2024 snapshot."""
    base: dict[str, object] = {"general_rule": RULE, "annual_holidays": [ANNUAL_2024]}
    base.update(overrides)
    return EvidenceCalendar(PROVENANCE, **base)  # type: ignore[arg-type]


def entry(**overrides: object) -> CalendarEvidenceEntry:
    base: dict[str, object] = {
        "evidence_id": "synthetic_entry",
        "url": "https://www.sec.gov/synthetic-announcement",
        "evidence_type": "date_specific_announcement",
        "asserted_status": "non_operating",
        "affected_dates": (MONDAY,),
        "title": "Synthetic announcement",
        "parser_version": "edgar-calendar/1.0",
        "review_status": "pending_review",
    }
    base.update(overrides)
    return CalendarEvidenceEntry(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# Evidence manifest
# --------------------------------------------------------------------------- #
def test_manifest_is_versioned_and_ships_without_date_assertions() -> None:
    assert CALENDAR_EVIDENCE_MANIFEST_VERSION.startswith("edgar-calendar-evidence/")
    assert dict(CALENDAR_EVIDENCE_MANIFEST) == {}
    assert approved_entries() == ()
    assert entries_for_date(MONDAY) == ()


def test_unknown_evidence_identifier_is_refused() -> None:
    with pytest.raises(CalendarEvidenceError, match="not in the reviewed manifest"):
        require_evidence("some_announcement_i_remembered")


def test_evidence_must_sit_on_an_approved_sec_host() -> None:
    assert APPROVED_SEC_HOSTS == ("https://www.sec.gov/", "https://data.sec.gov/")
    with pytest.raises(CalendarEvidenceError, match="approved SEC host"):
        validate_manifest([entry(url="https://example.invalid/announcement")])


def test_evidence_must_name_at_least_one_affected_date() -> None:
    with pytest.raises(CalendarEvidenceError, match="names no affected date"):
        validate_manifest([entry(affected_dates=())])


def test_approval_requires_a_source_observation() -> None:
    with pytest.raises(CalendarEvidenceError, match="without a source-observation"):
        validate_manifest([entry(review_status="approved")])


def test_approved_entry_with_an_observation_validates() -> None:
    validate_manifest([entry(review_status="approved", source_observation_id="obs-1")])


def test_date_ranges_expand_and_match() -> None:
    ranged = entry(
        affected_dates=(),
        affected_range_start=MONDAY,
        affected_range_end=WEDNESDAY,
    )
    assert ranged.dates() == (MONDAY, HOLIDAY, WEDNESDAY)
    assert ranged.covers(HOLIDAY)
    assert not ranged.covers(FRIDAY)


# --------------------------------------------------------------------------- #
# Tri-state determination
# --------------------------------------------------------------------------- #
def test_evidence_calendar_satisfies_the_operating_calendar_protocol() -> None:
    assert isinstance(calendar(), OperatingCalendar)


def test_evidence_hierarchy_precedence_is_ordered() -> None:
    assert EVIDENCE_PRECEDENCE == {
        "date_specific_announcement": 1,
        "annual_calendar_snapshot": 2,
        "general_operating_rule": 3,
        "positive_activity": 4,
    }
    assert CALENDAR_PROVENANCE_DECISION_RECORD.endswith(
        "decision_011_edgar_operating_calendar_provenance.md"
    )


@pytest.mark.parametrize("day", [SATURDAY, SUNDAY])
def test_weekends_are_non_operating_from_the_general_rule(day: date) -> None:
    determination = calendar().status_for(day)
    assert determination.status == "non_operating"
    assert [item.kind for item in determination.evidence] == ["general_operating_rule"]
    assert determination.source_observation_ids == ("obs-rule",)


def test_ordinary_proven_weekday_is_operating() -> None:
    determination = calendar().status_for(MONDAY)
    assert determination.status == "operating"
    assert determination.is_proven
    assert [item.kind for item in determination.evidence] == ["annual_calendar_snapshot"]
    assert determination.derivation_version == CALENDAR_DERIVATION_VERSION


def test_annual_calendar_holiday_is_non_operating() -> None:
    determination = calendar().status_for(HOLIDAY)
    assert determination.status == "non_operating"
    assert determination.source_observation_ids == ("obs-annual-2024",)


def test_weekday_without_an_annual_snapshot_is_unknown() -> None:
    """The general rule alone supplies no historical holiday list."""
    determination = calendar().status_for(UNPROVEN_WEEKDAY)
    assert determination.status == "unknown"
    assert not determination.is_proven
    assert determination.reason_codes == ("REVIEW_CALENDAR_DATE_UNKNOWN",)


def test_year_specific_snapshot_does_not_cover_another_year() -> None:
    assert calendar().status_for(date(2023, 3, 6)).status == "unknown"
    assert calendar().status_for(MONDAY).status == "operating"


def test_announcement_overrides_the_ordinary_weekday_rule() -> None:
    exceptional = calendar(
        announcements=[
            Announcement(
                days=frozenset({MONDAY}),
                status="non_operating",
                evidence_id="announcement_closure",
                source_observation_id="obs-ann-1",
            )
        ]
    )
    determination = exceptional.status_for(MONDAY)
    assert determination.status == "non_operating"
    assert [item.kind for item in determination.evidence] == ["date_specific_announcement"]


def test_announcement_can_prove_an_exceptional_operating_date() -> None:
    exceptional = calendar(
        announcements=[
            Announcement(
                days=frozenset({HOLIDAY}),
                status="operating",
                evidence_id="announcement_remained_open",
                source_observation_id="obs-ann-2",
            )
        ]
    )
    assert exceptional.status_for(HOLIDAY).status == "operating"


def test_absence_of_filings_never_establishes_closure() -> None:
    assert calendar(activity=[]).status_for(UNPROVEN_WEEKDAY).status == "unknown"


def test_positive_activity_alone_establishes_operating() -> None:
    with_activity = EvidenceCalendar(
        PROVENANCE,
        general_rule=RULE,
        activity=[PositiveActivity(UNPROVEN_WEEKDAY, "daily_index_2019", "obs-activity-2019")],
    )
    determination = with_activity.status_for(UNPROVEN_WEEKDAY)
    assert determination.status == "operating"
    assert [item.kind for item in determination.evidence] == ["positive_activity"]


def test_conflicting_evidence_returns_unknown_and_blocks_release() -> None:
    conflicted = calendar(
        activity=[PositiveActivity(HOLIDAY, "daily_index_2024", "obs-activity-2024")]
    )
    determination = conflicted.status_for(HOLIDAY)
    assert determination.status == "unknown"
    assert determination.conflicting
    assert determination.reason_codes == ("REVIEW_CALENDAR_EVIDENCE_CONFLICT",)
    assert len(determination.evidence) == 2


def test_conflicting_announcements_are_not_resolved_by_source_order() -> None:
    double = calendar(
        announcements=[
            Announcement(frozenset({WEDNESDAY}), "non_operating", "ann_a", "obs-a"),
            Announcement(frozenset({WEDNESDAY}), "operating", "ann_b", "obs-b"),
        ]
    )
    determination = double.status_for(WEDNESDAY)
    assert determination.status == "unknown"
    assert determination.conflicting
    assert {item.evidence_id for item in determination.evidence} == {"ann_a", "ann_b"}


def test_a_government_shutdown_is_not_edgar_closure() -> None:
    """Only EDGAR-specific SEC evidence may close a date.

    A shutdown with no EDGAR announcement leaves the date exactly as the ordinary
    evidence made it, and positive EDGAR activity keeps it operating.
    """
    unaffected = calendar(
        activity=[PositiveActivity(MONDAY, "daily_index_2024", "obs-activity-monday")]
    )
    assert unaffected.status_for(MONDAY).status == "operating"
    assert calendar().status_for(MONDAY).status == "operating"


def test_no_generic_holiday_library_is_consulted() -> None:
    """Removing the SEC evidence makes the date unknown, not a library holiday."""
    without_evidence = EvidenceCalendar(PROVENANCE, general_rule=RULE)
    assert without_evidence.status_for(date(2024, 12, 25)).status == "unknown"
    assert without_evidence.status_for(date(2024, 7, 4)).status == "unknown"


# --------------------------------------------------------------------------- #
# Fail-closed access and rollover derivation
# --------------------------------------------------------------------------- #
def test_unknown_date_raises_rather_than_answering() -> None:
    with pytest.raises(CalendarCoverageError, match="no proven EDGAR operating status"):
        calendar().is_operating_day(UNPROVEN_WEEKDAY)


def test_proven_dates_answer_directly() -> None:
    assert calendar().is_operating_day(MONDAY) is True
    assert calendar().is_operating_day(SATURDAY) is False


def test_friday_to_monday_rollover_across_a_proven_weekend() -> None:
    assert calendar().next_operating_day(FRIDAY) == MONDAY


def test_rollover_across_a_proven_holiday() -> None:
    assert calendar().next_operating_day(MONDAY) == WEDNESDAY


def test_rollover_is_refused_when_an_intervening_date_is_unknown() -> None:
    without_snapshot = EvidenceCalendar(PROVENANCE, general_rule=RULE)
    with pytest.raises(CalendarCoverageError, match="unproven"):
        without_snapshot.next_operating_day(FRIDAY)


def test_rollover_is_refused_without_any_evidence_at_all() -> None:
    bare = EvidenceCalendar(PROVENANCE)
    with pytest.raises(CalendarCoverageError):
        bare.next_operating_day(FRIDAY)


# --------------------------------------------------------------------------- #
# Coverage accounting
# --------------------------------------------------------------------------- #
def test_coverage_is_date_specific() -> None:
    report = calendar().coverage_report(FRIDAY, date(2024, 3, 10))
    summary = report.as_summary()
    assert summary["operating"] == 5
    assert summary["non_operating"] == 5
    assert summary["unknown"] == 0
    assert summary["conflicting"] == 0
    assert report.fully_supported
    assert report.first_supported == FRIDAY
    assert report.last_supported == date(2024, 3, 10)
    assert report.evidence_by_date["2024-03-05"] == ("annual_calendar_2024",)
    assert "obs-annual-2024" in report.source_observation_ids
    assert report.derivation_version == CALENDAR_DERIVATION_VERSION


def test_a_year_is_not_fully_covered_without_date_evidence() -> None:
    report = EvidenceCalendar(PROVENANCE, general_rule=RULE).coverage_report(
        date(2019, 3, 1), date(2019, 3, 7)
    )
    assert not report.fully_supported
    assert len(report.unknown) == 5
    assert len(report.non_operating) == 2


def test_conflicting_dates_are_reported_and_prevent_full_support() -> None:
    conflicted = calendar(
        activity=[PositiveActivity(HOLIDAY, "daily_index_2024", "obs-activity-2024")]
    )
    report = conflicted.coverage_report(FRIDAY, WEDNESDAY)
    assert report.conflicting == (HOLIDAY,)
    assert HOLIDAY in report.unknown
    assert not report.fully_supported


def test_reversed_coverage_window_is_refused() -> None:
    with pytest.raises(CalendarCoverageError, match="ends before it starts"):
        calendar().coverage_report(WEDNESDAY, FRIDAY)


# --------------------------------------------------------------------------- #
# Integration with the frozen Decision 010 rules
# --------------------------------------------------------------------------- #
def test_proven_rollover_still_classifies_under_decision_010() -> None:
    assignment = assign_cohorts(
        MONDAY,
        acceptance_timestamps("20240301201500"),
        calendar=calendar(),
        form_type="10-K",
    )
    assert assignment.divergence.reason == "expected_after_cutoff_rollover"
    assert assignment.divergence.calendar_provenance is not None
    assert assignment.divergence.calendar_provenance.snapshot_id == "snapshot-test-1"


def test_non_operating_day_acceptance_is_still_flagged() -> None:
    assignment = assign_cohorts(
        MONDAY,
        acceptance_timestamps("20240302103000"),
        calendar=calendar(),
        form_type="10-K",
    )
    assert "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY" in assignment.divergence.reason_codes
    assert assignment.blocks_release


def test_unknown_calendar_dates_block_rollover_classification() -> None:
    assignment = assign_cohorts(
        date(2019, 3, 5),
        acceptance_timestamps("20190304201500"),
        calendar=EvidenceCalendar(PROVENANCE, general_rule=RULE),
        form_type="10-K",
    )
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert "OPERATING_CALENDAR_UNAVAILABLE" in assignment.divergence.reason_codes
    assert assignment.blocks_release
