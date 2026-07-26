"""Temporal policy: source precedence, acceptance derivation, dual cohorts."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

import pytest

from disclosure_drift.errors import ReviewRequiredError
from disclosure_drift.sec.calendar import (
    FROZEN_FILING_CUTOFF_ET,
    CalendarProvenance,
    StaticOperatingCalendar,
)
from disclosure_drift.sec.temporal import (
    ACCESSION_HEADER_SOURCES,
    OUT_OF_SCOPE_COHORT,
    SUPPORT_2009_COHORT,
    DateObservation,
    SourceKind,
    TemporalPolicyError,
    acceptance_date_sec,
    acceptance_timestamps,
    assign_cohorts,
    cohort_name_for,
    correction_status,
    resolve_official_filing_date,
)

OBSERVED = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)


def observation(
    source: SourceKind,
    raw: str,
    parsed: date | None,
    field_name: str = "filing_date_sec",
) -> DateObservation:
    return DateObservation(
        source=source,
        field_name=field_name,
        raw_value=raw,
        observed_at_utc=OBSERVED,
        snapshot_id="snapshot-1",
        parsed_date=parsed,
    )


# --------------------------------------------------------------------------- #
# Source precedence and conflicts
# --------------------------------------------------------------------------- #
def test_header_sources_are_co_authoritative() -> None:
    assert {"complete_submission_header", "sgml_header"} == ACCESSION_HEADER_SOURCES
    complete = observation("complete_submission_header", "20240215", date(2024, 2, 15))
    sgml = observation("sgml_header", "20240215", date(2024, 2, 15))
    assert complete.precedence_rank == sgml.precedence_rank == 1


def test_header_value_outranks_provisional_observations() -> None:
    resolved = resolve_official_filing_date(
        [
            observation("submissions_api", "2024-02-14", date(2024, 2, 14)),
            observation("master_index", "2024-02-14", date(2024, 2, 14)),
            observation("sgml_header", "20240215", date(2024, 2, 15)),
        ]
    )
    assert resolved.value == date(2024, 2, 15)
    assert resolved.source == "sgml_header"
    assert resolved.is_canonical
    assert [conflict.kind for conflict in resolved.conflicts] == ["provisional_versus_canonical"]
    assert resolved.reason_codes == ()
    assert len(resolved.observations) == 3


def test_conflicting_header_sources_are_never_resolved_silently() -> None:
    resolved = resolve_official_filing_date(
        [
            observation("complete_submission_header", "20240215", date(2024, 2, 15)),
            observation("sgml_header", "20240216", date(2024, 2, 16)),
        ]
    )
    assert resolved.value is None
    assert resolved.source is None
    assert "REVIEW_ACCESSION_HEADER_SOURCE_CONFLICT" in resolved.reason_codes
    conflict = resolved.conflicts[0]
    assert conflict.kind == "accession_header_conflict"
    assert conflict.values == ("2024-02-15", "2024-02-16")
    assert len(resolved.observations) == 2


def test_agreeing_header_sources_resolve_without_review() -> None:
    resolved = resolve_official_filing_date(
        [
            observation("complete_submission_header", "20240215", date(2024, 2, 15)),
            observation("sgml_header", "20240215", date(2024, 2, 15)),
        ]
    )
    assert resolved.value == date(2024, 2, 15)
    assert resolved.reason_codes == ()
    assert resolved.conflicts == ()


def test_provisional_sources_are_usable_for_discovery() -> None:
    resolved = resolve_official_filing_date(
        [observation("submissions_api", "2024-02-14", date(2024, 2, 14))]
    )
    assert resolved.value == date(2024, 2, 14)
    assert resolved.precedence_rank == 2
    assert not resolved.is_canonical


def test_disagreeing_provisional_sources_require_review() -> None:
    resolved = resolve_official_filing_date(
        [
            observation("submissions_api", "2024-02-14", date(2024, 2, 14)),
            observation("master_index", "2024-02-15", date(2024, 2, 15)),
        ]
    )
    assert resolved.value is None
    assert "REVIEW_PROVISIONAL_DATE_DISAGREEMENT" in resolved.reason_codes


def test_no_parseable_observation_reports_missing_required_field() -> None:
    resolved = resolve_official_filing_date([observation("master_index", "not-a-date", None)])
    assert resolved.value is None
    assert resolved.reason_codes == ("SEC_SCHEMA_REQUIRED_FIELD_MISSING",)


# --------------------------------------------------------------------------- #
# Acceptance values
# --------------------------------------------------------------------------- #
def test_acceptance_date_uses_first_eight_characters() -> None:
    assert acceptance_date_sec("20211231201500") == date(2021, 12, 31)


def test_acceptance_date_is_not_a_utc_conversion() -> None:
    """23:30 Eastern is the next UTC day; the SEC calendar date must not shift."""
    raw = "20211231233000"
    stamps = acceptance_timestamps(raw)
    assert stamps.date_sec == date(2021, 12, 31)
    assert stamps.datetime_utc.date() == date(2022, 1, 1)
    assert acceptance_date_sec(raw) == stamps.date_sec


@pytest.mark.parametrize("raw", ["2021123120150", "20211231T2015", "", "2021-12-31 20:15:00"])
def test_malformed_acceptance_values_are_rejected(raw: str) -> None:
    with pytest.raises(TemporalPolicyError):
        acceptance_date_sec(raw)


def test_impossible_acceptance_date_is_rejected() -> None:
    with pytest.raises(TemporalPolicyError, match="impossible date"):
        acceptance_date_sec("20211331201500")


def test_raw_acceptance_value_is_preserved() -> None:
    stamps = acceptance_timestamps("20240215173000")
    assert stamps.raw == "20240215173000"
    assert stamps.datetime_et.utcoffset() is not None
    assert stamps.is_after_normal_cutoff


def test_acceptance_before_cutoff_is_not_flagged() -> None:
    assert not acceptance_timestamps("20240215120000").is_after_normal_cutoff


def test_nonexistent_spring_forward_time_is_reported_as_nonexistent() -> None:
    """02:30 on 2021-03-14 is skipped entirely in America/New_York."""
    with pytest.raises(ReviewRequiredError) as excinfo:
        acceptance_timestamps("20210314023000")
    assert "does not exist" in str(excinfo.value)
    assert "ambiguous" not in str(excinfo.value)
    assert excinfo.value.reason_codes == ("REVIEW_TIMEZONE_NONEXISTENT",)


def test_ambiguous_fall_back_time_is_reported_as_ambiguous() -> None:
    """01:30 on 2021-11-07 occurs twice in America/New_York."""
    with pytest.raises(ReviewRequiredError) as excinfo:
        acceptance_timestamps("20211107013000")
    assert "ambiguous" in str(excinfo.value)
    assert "does not exist" not in str(excinfo.value)
    assert excinfo.value.reason_codes == ("REVIEW_TIMEZONE_AMBIGUOUS",)


def test_normal_winter_timestamp_resolves_to_standard_time() -> None:
    stamps = acceptance_timestamps("20210115143000")
    assert stamps.date_sec == date(2021, 1, 15)
    assert stamps.datetime_et.utcoffset() == timedelta(hours=-5)
    assert stamps.datetime_utc.hour == 19


def test_normal_summer_timestamp_resolves_to_daylight_time() -> None:
    stamps = acceptance_timestamps("20210715143000")
    assert stamps.date_sec == date(2021, 7, 15)
    assert stamps.datetime_et.utcoffset() == timedelta(hours=-4)
    assert stamps.datetime_utc.hour == 18


def test_times_adjacent_to_the_transitions_remain_valid() -> None:
    """01:59 before the gap and 03:00 after it are both ordinary times."""
    before = acceptance_timestamps("20210314015900")
    after = acceptance_timestamps("20210314030000")
    assert before.datetime_et.utcoffset() == timedelta(hours=-5)
    assert after.datetime_et.utcoffset() == timedelta(hours=-4)


# --------------------------------------------------------------------------- #
# Cohort assignment
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2009, 6, 30), SUPPORT_2009_COHORT),
        (date(2010, 1, 1), "development"),
        (date(2022, 1, 1), "transition"),
        (date(2024, 12, 31), "primary_test"),
        (date(2026, 12, 31), "monitoring"),
        (date(2008, 12, 31), OUT_OF_SCOPE_COHORT),
        (date(2027, 1, 1), OUT_OF_SCOPE_COHORT),
    ],
)
def test_cohort_labels(day: date, expected: str) -> None:
    assert cohort_name_for(day) == expected


def calendar(days: list[date]) -> StaticOperatingCalendar:
    """Build a synthetic EDGAR operating calendar for the supplied days."""
    return StaticOperatingCalendar.from_days(
        days,
        CalendarProvenance(
            source_kind="synthetic_fixture",
            description="synthetic operating calendar for Stage M2.1 tests",
        ),
    )


def business_days(first: date, last: date, *, closed: set[date] | None = None) -> list[date]:
    """Weekdays between two dates, minus explicitly closed days."""
    skip = closed or set()
    days: list[date] = []
    current = first
    while current <= last:
        if current.weekday() < 5 and current not in skip:
            days.append(current)
        current += timedelta(days=1)
    return days


def test_same_day_filing_has_no_divergence() -> None:
    assignment = assign_cohorts(date(2024, 3, 1), date(2024, 3, 1))
    assert assignment.official_filing_temporal_cohort == "primary_test"
    assert assignment.accepted_temporal_cohort == "primary_test"
    assert not assignment.date_divergence
    assert not assignment.cohort_boundary_crossing
    assert not assignment.coverage_boundary_divergence
    assert assignment.divergence.reason == "same_day_filing"
    assert assignment.divergence_explained
    assert not assignment.requires_manual_review
    assert not assignment.blocks_release


def test_after_cutoff_rollover_is_explained_by_the_operating_calendar() -> None:
    """Accepted 20:15 on a Friday, filed on the following Monday."""
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
    )
    assert assignment.date_divergence
    assert not assignment.cohort_boundary_crossing
    assert assignment.divergence.reason == "expected_after_cutoff_rollover"
    assert assignment.divergence_explained
    assert not assignment.requires_manual_review
    assert "EXPECTED_AFTER_CUTOFF_ROLLOVER" in assignment.reason_codes
    provenance = assignment.divergence.calendar_provenance
    assert provenance is not None
    assert provenance.is_synthetic


def test_rollover_skips_a_non_operating_weekday() -> None:
    """A closed Monday means the expected filing date is the Tuesday."""
    closed = {date(2024, 3, 4)}
    days = business_days(date(2024, 2, 26), date(2024, 3, 15), closed=closed)
    monday = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
    )
    tuesday = assign_cohorts(
        date(2024, 3, 5),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
    )
    assert monday.divergence.reason == "unexplained_date_divergence"
    assert tuesday.divergence.reason == "expected_after_cutoff_rollover"


def test_acceptance_on_a_non_operating_day_is_never_rollover_eligible() -> None:
    """EDGAR does not ordinarily accept filings on weekends or federal holidays."""
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240302103000"),
        calendar=calendar(days),
    )
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY" in assignment.divergence.reason_codes
    assert "not an EDGAR operating day" in assignment.divergence.detail
    assert assignment.requires_manual_review
    assert assignment.blocks_release


def test_acceptance_on_a_closed_holiday_requires_reconciliation() -> None:
    closed = {date(2024, 3, 1)}
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(business_days(date(2024, 2, 26), date(2024, 3, 15), closed=closed)),
    )
    assert "REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY" in assignment.divergence.reason_codes
    assert "EXPECTED_AFTER_CUTOFF_ROLLOVER" not in assignment.reason_codes


def test_rollover_requires_all_three_conditions() -> None:
    """Operating-day acceptance, after the frozen cutoff, next operating day filing."""
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    accepted = acceptance_timestamps("20240301201500")

    complete = assign_cohorts(date(2024, 3, 4), accepted, calendar=calendar(days))
    wrong_day = assign_cohorts(date(2024, 3, 5), accepted, calendar=calendar(days))
    before_cutoff = assign_cohorts(
        date(2024, 3, 4), acceptance_timestamps("20240301120000"), calendar=calendar(days)
    )

    assert complete.divergence.reason == "expected_after_cutoff_rollover"
    assert wrong_day.divergence.reason == "unexplained_date_divergence"
    assert before_cutoff.divergence.reason == "unexplained_date_divergence"


def test_production_cutoff_is_frozen_and_only_tests_may_inject_another() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    accepted = acceptance_timestamps("20240301161500")

    frozen_policy = assign_cohorts(date(2024, 3, 4), accepted, calendar=calendar(days))
    injected = assign_cohorts(
        date(2024, 3, 4), accepted, calendar=calendar(days), cutoff=time(16, 0)
    )

    assert time(17, 30) == FROZEN_FILING_CUTOFF_ET
    assert frozen_policy.divergence.reason == "unexplained_date_divergence"
    assert injected.divergence.reason == "expected_after_cutoff_rollover"


def test_unsupported_forms_cannot_claim_a_rollover() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    accepted = acceptance_timestamps("20240301201500")

    supported = assign_cohorts(
        date(2024, 3, 4), accepted, calendar=calendar(days), form_type="10-KT"
    )
    unsupported = assign_cohorts(
        date(2024, 3, 4), accepted, calendar=calendar(days), form_type="20-F"
    )

    assert supported.divergence.reason == "expected_after_cutoff_rollover"
    assert unsupported.divergence.reason == "unexplained_date_divergence"
    assert "does not govern form" in unsupported.divergence.detail


def test_before_cutoff_gap_is_not_a_rollover() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301090000"),
        calendar=calendar(days),
    )
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert assignment.blocks_release


def test_no_calendar_means_rollover_cannot_be_established() -> None:
    assignment = assign_cohorts(date(2024, 3, 4), acceptance_timestamps("20240301201500"))
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert "OPERATING_CALENDAR_UNAVAILABLE" in assignment.divergence.reason_codes
    assert assignment.blocks_release


def test_dates_outside_calendar_coverage_are_unexplained_not_assumed() -> None:
    days = business_days(date(2024, 6, 3), date(2024, 6, 14))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
    )
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert "OPERATING_CALENDAR_UNAVAILABLE" in assignment.divergence.reason_codes


def test_no_five_day_allowance_exists() -> None:
    """A four-day gap with no approved reason is still unexplained."""
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 7),
        acceptance_timestamps("20240304201500"),
        calendar=calendar(days),
    )
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert assignment.blocks_release


def test_correction_is_never_silently_treated_as_after_hours() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
        date_as_of_change=date(2024, 3, 4),
    )
    assert assignment.divergence.reason == "post_acceptance_date_correction"
    assert "POST_ACCEPTANCE_DATE_CORRECTION" in assignment.reason_codes
    assert "EXPECTED_AFTER_CUTOFF_ROLLOVER" not in assignment.reason_codes


def test_correction_requires_review_only_when_it_moves_the_cohort() -> None:
    days = business_days(date(2023, 12, 20), date(2024, 1, 15))
    inside = assign_cohorts(
        date(2024, 3, 4),
        date(2024, 3, 1),
        correction_indicated=True,
    )
    assert not inside.requires_manual_review

    crossing = assign_cohorts(
        date(2024, 1, 3),
        acceptance_timestamps("20231229201500"),
        calendar=calendar(days),
        correction_indicated=True,
    )
    assert crossing.cohort_boundary_crossing
    assert crossing.requires_manual_review
    assert "REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY" in crossing.reason_codes


def test_december_boundary_crossing_requires_review() -> None:
    days = business_days(date(2021, 12, 20), date(2022, 1, 14))
    assignment = assign_cohorts(
        date(2022, 1, 3),
        acceptance_timestamps("20211231201500"),
        calendar=calendar(days),
    )
    assert assignment.official_filing_temporal_cohort == "transition"
    assert assignment.accepted_temporal_cohort == "development"
    assert assignment.cohort_boundary_crossing
    assert not assignment.coverage_boundary_divergence
    assert assignment.requires_manual_review
    assert "REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING" in assignment.reason_codes
    assert assignment.divergence.reason == "expected_after_cutoff_rollover"
    assert not assignment.requires_explicit_approval


def test_date_divergence_inside_one_cohort_is_not_a_boundary_crossing() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(
        date(2024, 3, 4),
        acceptance_timestamps("20240301201500"),
        calendar=calendar(days),
    )
    assert assignment.date_divergence
    assert not assignment.cohort_boundary_crossing
    assert not assignment.cohort_divergence


def test_coverage_boundary_divergence_requires_review() -> None:
    """2026 acceptance with a 2027 filing date leaves supported coverage."""
    assignment = assign_cohorts(date(2027, 1, 4), date(2026, 12, 31))
    assert assignment.official_filing_temporal_cohort == OUT_OF_SCOPE_COHORT
    assert assignment.accepted_temporal_cohort == "monitoring"
    assert assignment.coverage_boundary_divergence
    assert not assignment.cohort_boundary_crossing
    assert "COVERAGE_BOUNDARY_DIVERGENCE" in assignment.reason_codes
    assert assignment.requires_manual_review
    assert assignment.blocks_release


def test_entering_the_untouched_2024_cohort_requires_explicit_approval() -> None:
    days = business_days(date(2023, 12, 20), date(2024, 1, 15))
    assignment = assign_cohorts(
        date(2024, 1, 2),
        acceptance_timestamps("20231229201500"),
        calendar=calendar(days),
    )
    assert assignment.official_filing_temporal_cohort == "primary_test"
    assert assignment.accepted_temporal_cohort == "transition"
    assert assignment.touches_primary_test
    assert assignment.requires_explicit_approval


def test_leaving_the_untouched_2024_cohort_requires_explicit_approval() -> None:
    days = business_days(date(2024, 12, 20), date(2025, 1, 15))
    assignment = assign_cohorts(
        date(2025, 1, 2),
        acceptance_timestamps("20241231201500"),
        calendar=calendar(days),
    )
    assert assignment.accepted_temporal_cohort == "primary_test"
    assert assignment.official_filing_temporal_cohort == "prospective"
    assert assignment.requires_explicit_approval


def test_filing_date_before_acceptance_is_never_a_rollover() -> None:
    days = business_days(date(2024, 2, 26), date(2024, 3, 15))
    assignment = assign_cohorts(date(2024, 3, 1), date(2024, 3, 4), calendar=calendar(days))
    assert assignment.divergence.reason == "unexplained_date_divergence"
    assert "REVIEW_FILING_DATE_BEFORE_ACCEPTANCE" in assignment.reason_codes
    assert assignment.requires_manual_review
    assert assignment.blocks_release


def test_missing_acceptance_date_yields_audit_null_and_review() -> None:
    assignment = assign_cohorts(date(2024, 3, 1), None)
    assert assignment.accepted_temporal_cohort is None
    assert not assignment.coverage_boundary_divergence
    assert "REVIEW_MISSING_ACCEPTANCE_TIMESTAMP" in assignment.reason_codes
    assert assignment.requires_manual_review


def test_amendment_cohort_is_independent_of_the_original() -> None:
    original = assign_cohorts(date(2021, 3, 1), date(2021, 3, 1))
    amendment = assign_cohorts(date(2024, 5, 1), date(2024, 5, 1))
    assert original.official_filing_temporal_cohort == "development"
    assert amendment.official_filing_temporal_cohort == "primary_test"


# --------------------------------------------------------------------------- #
# Corrections
# --------------------------------------------------------------------------- #
def test_no_correction_when_change_date_is_not_later() -> None:
    assert correction_status(date(2024, 3, 1), date(2024, 3, 1)) == ("none", ())
    assert correction_status(date(2024, 3, 1), None) == ("none", ())


def test_correction_within_cohort_is_recorded_without_boundary_reason() -> None:
    status, reasons = correction_status(date(2024, 3, 1), date(2024, 4, 1))
    assert status == "post_acceptance_correction"
    assert reasons == ()


def test_correction_crossing_a_cohort_boundary_is_flagged() -> None:
    status, reasons = correction_status(date(2024, 12, 30), date(2025, 1, 6))
    assert status == "post_acceptance_correction"
    assert reasons == ("REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY",)
