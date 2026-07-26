"""Tri-state public-availability comparison (Decision 010 section 6)."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from disclosure_drift.sec.availability import (
    INDETERMINATE_REASON_CODE,
    AvailabilityBoundary,
    AvailabilityError,
    boundary_for,
    compare_boundaries,
)

ET = ZoneInfo("America/New_York")


def timestamped(accession: str, day: date, hour: int, minute: int = 0) -> AvailabilityBoundary:
    return AvailabilityBoundary(
        accession_plain=accession,
        proxy_date=day,
        precision="timestamp",
        basis="same_day_acceptance",
        timestamp_et=datetime(day.year, day.month, day.day, hour, minute, tzinfo=ET),
    )


def date_only(accession: str, day: date) -> AvailabilityBoundary:
    return AvailabilityBoundary(
        accession_plain=accession,
        proxy_date=day,
        precision="date",
        basis="later_official_filing_date",
    )


# --------------------------------------------------------------------------- #
# Boundary construction
# --------------------------------------------------------------------------- #
def test_same_day_acceptance_gives_timestamp_precision() -> None:
    day = date(2024, 2, 15)
    boundary = boundary_for(
        "000123456724000001",
        official_filing_date=day,
        acceptance_date=day,
        acceptance_datetime_et=datetime(2024, 2, 15, 16, 5, tzinfo=ET),
    )
    assert boundary.precision == "timestamp"
    assert boundary.basis == "same_day_acceptance"
    assert boundary.is_timestamped


def test_later_filing_date_gives_date_precision_without_inventing_a_timestamp() -> None:
    boundary = boundary_for(
        "000123456724000002",
        official_filing_date=date(2024, 2, 16),
        acceptance_date=date(2024, 2, 15),
        acceptance_datetime_et=datetime(2024, 2, 15, 20, 15, tzinfo=ET),
    )
    assert boundary.precision == "date"
    assert boundary.basis == "later_official_filing_date"
    assert boundary.proxy_date == date(2024, 2, 16)
    assert not boundary.is_timestamped


def test_missing_acceptance_gives_filing_date_only() -> None:
    boundary = boundary_for(
        "000123456724000003",
        official_filing_date=date(2024, 2, 16),
        acceptance_date=None,
        acceptance_datetime_et=None,
    )
    assert boundary.basis == "filing_date_only"
    assert boundary.precision == "date"


def test_timestamp_precision_requires_a_timestamp() -> None:
    with pytest.raises(AvailabilityError, match="requires an Eastern timestamp"):
        AvailabilityBoundary(
            accession_plain="000123456724000004",
            proxy_date=date(2024, 2, 15),
            precision="timestamp",
            basis="same_day_acceptance",
        )


def test_naive_timestamps_are_rejected() -> None:
    with pytest.raises(AvailabilityError, match="timezone aware"):
        AvailabilityBoundary(
            accession_plain="000123456724000005",
            proxy_date=date(2024, 2, 15),
            precision="timestamp",
            basis="same_day_acceptance",
            timestamp_et=datetime(2024, 2, 15, 16, 0),
        )


# --------------------------------------------------------------------------- #
# Tri-state comparison
# --------------------------------------------------------------------------- #
def test_own_package_is_eligible_even_when_the_boundary_is_later_than_acceptance() -> None:
    target = boundary_for(
        "000123456724000010",
        official_filing_date=date(2024, 2, 16),
        acceptance_date=date(2024, 2, 15),
        acceptance_datetime_et=datetime(2024, 2, 15, 20, 15, tzinfo=ET),
    )
    verdict = compare_boundaries(target, target)
    assert verdict.outcome == "eligible"
    assert verdict.permits_automatic_use


def test_exact_source_before_exact_target_is_eligible() -> None:
    source = timestamped("000000000124000001", date(2024, 2, 15), 9)
    target = timestamped("000000000124000002", date(2024, 2, 15), 16)
    assert compare_boundaries(source, target).outcome == "eligible"


def test_identical_exact_timestamps_are_eligible() -> None:
    source = timestamped("000000000124000001", date(2024, 2, 15), 16)
    target = timestamped("000000000124000002", date(2024, 2, 15), 16)
    assert compare_boundaries(source, target).outcome == "eligible"


def test_exact_source_after_exact_target_is_ineligible() -> None:
    source = timestamped("000000000124000001", date(2024, 2, 15), 17)
    target = timestamped("000000000124000002", date(2024, 2, 15), 16)
    verdict = compare_boundaries(source, target)
    assert verdict.outcome == "ineligible"
    assert verdict.asserts_unavailability
    assert not verdict.permits_automatic_use


def test_earlier_date_is_eligible_across_precisions() -> None:
    source = date_only("000000000124000001", date(2024, 2, 14))
    target = timestamped("000000000124000002", date(2024, 2, 15), 9)
    assert compare_boundaries(source, target).outcome == "eligible"


def test_later_date_is_ineligible_across_precisions() -> None:
    source = date_only("000000000124000001", date(2024, 2, 17))
    target = timestamped("000000000124000002", date(2024, 2, 15), 9)
    assert compare_boundaries(source, target).outcome == "ineligible"


def test_same_date_with_date_precision_is_indeterminate() -> None:
    source = date_only("000000000124000001", date(2024, 2, 15))
    target = timestamped("000000000124000002", date(2024, 2, 15), 9)
    verdict = compare_boundaries(source, target)
    assert verdict.outcome == "indeterminate"
    assert verdict.reason_codes == (INDETERMINATE_REASON_CODE,)


def test_indeterminate_neither_permits_use_nor_asserts_unavailability() -> None:
    source = date_only("000000000124000001", date(2024, 2, 15))
    target = date_only("000000000124000002", date(2024, 2, 15))
    verdict = compare_boundaries(source, target)
    assert verdict.outcome == "indeterminate"
    assert not verdict.permits_automatic_use
    assert not verdict.asserts_unavailability


def test_comparison_is_never_a_bare_boolean() -> None:
    source = date_only("000000000124000001", date(2024, 2, 15))
    target = date_only("000000000124000002", date(2024, 2, 15))
    verdict = compare_boundaries(source, target)
    assert not isinstance(verdict, bool)
    assert verdict.outcome in {"eligible", "ineligible", "indeterminate"}
