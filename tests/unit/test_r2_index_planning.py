"""Stage M2.2-R2.6: quarterly index-instance planning.

Which quarters are required is decided from explicit plan inputs only — a coverage window
and an as-of date. Nothing here reads the clock, so the same request produces the same
plan on any later day. Closed quarters are required, the quarter containing the as-of date
is provisional, and a quarter beginning after the as-of date is simply not planned.
"""

from __future__ import annotations

from datetime import date

import pytest

from disclosure_drift.sec.index_plan import (
    INDEX_PLAN_POLICY_VERSION,
    CoverageWindow,
    coverage_summary,
    plan_index_instances,
    quarter_end,
    quarter_of,
    quarter_start,
)


def window(start: str, end: str, as_of: str, *, include_open: bool = False) -> CoverageWindow:
    """Build a coverage window from ISO date text."""
    return CoverageWindow(
        coverage_start=date.fromisoformat(start),
        coverage_end=date.fromisoformat(end),
        as_of_date=date.fromisoformat(as_of),
        include_open_quarter=include_open,
    )


# --------------------------------------------------------------------------- #
# Quarter arithmetic
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("day", "expected"),
    [
        ("2024-01-01", 1),
        ("2024-03-31", 1),
        ("2024-04-01", 2),
        ("2024-06-30", 2),
        ("2024-07-01", 3),
        ("2024-09-30", 3),
        ("2024-10-01", 4),
        ("2024-12-31", 4),
    ],
)
def test_quarter_of_covers_every_boundary(day: str, expected: int) -> None:
    assert quarter_of(date.fromisoformat(day)) == expected


@pytest.mark.parametrize("quarter", [1, 2, 3, 4])
def test_quarter_bounds_are_leap_year_safe(quarter: int) -> None:
    start = quarter_start(2024, quarter)
    end = quarter_end(2024, quarter)
    assert start < end
    assert quarter_of(start) == quarter
    assert quarter_of(end) == quarter
    # Q1 always ends 31 March, never on a February date, leap year or not.
    assert (end.month, end.day) != (2, 29)


def test_an_invalid_quarter_is_refused() -> None:
    with pytest.raises(ValueError, match="quarter must be"):
        quarter_start(2024, 5)


# --------------------------------------------------------------------------- #
# Plan classification
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("label", "as_of", "closed", "open_key"),
    [
        ("first day of a quarter", "2024-01-01", 0, "2024QTR1"),
        ("middle of a quarter", "2024-02-15", 0, "2024QTR1"),
        ("last day of a quarter", "2024-03-31", 0, "2024QTR1"),
        ("first day after quarter close", "2024-04-01", 1, "2024QTR2"),
        ("leap day", "2024-02-29", 0, "2024QTR1"),
        ("mid-year", "2024-08-15", 2, "2024QTR3"),
    ],
)
def test_as_of_date_decides_closed_and_open_quarters(
    label: str,
    as_of: str,
    closed: int,
    open_key: str,
) -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", as_of))
    assert len(plan.required_closed) == closed, label
    assert plan.provisional_open is not None
    assert plan.provisional_open.instance_key == open_key, label


def test_the_quarter_containing_the_as_of_date_is_never_required_by_default() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-02-15"))
    open_instance = plan.provisional_open
    assert open_instance is not None
    assert open_instance.kind == "provisional_open_quarter"
    assert not open_instance.required
    assert not open_instance.is_finalized_period


def test_the_open_quarter_can_be_requested_explicitly_and_stays_provisional() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-08-15", include_open=True))
    open_instance = plan.provisional_open
    assert open_instance is not None
    assert open_instance.required
    assert not open_instance.is_finalized_period


def test_future_quarters_are_excluded_not_missing() -> None:
    plan = plan_index_instances(window("2026-01-01", "2026-12-31", "2026-07-26"))
    assert plan.excluded_future_quarters == ("2026QTR4",)
    assert [item.instance_key for item in plan.required_closed] == ["2026QTR1", "2026QTR2"]
    assert plan.provisional_open is not None
    assert plan.provisional_open.instance_key == "2026QTR3"
    assert "2026QTR4" not in plan.required_keys


def test_a_fully_closed_historical_year_is_all_required() -> None:
    plan = plan_index_instances(window("2010-01-01", "2010-12-31", "2012-01-01"))
    assert len(plan.required_closed) == 4
    assert plan.provisional_open is None
    assert all(item.is_finalized_period for item in plan.instances)


def test_the_2009_support_year_plans_four_closed_quarters() -> None:
    plan = plan_index_instances(window("2009-01-01", "2009-12-31", "2011-01-01"))
    assert [item.instance_key for item in plan.required_closed] == [
        "2009QTR1",
        "2009QTR2",
        "2009QTR3",
        "2009QTR4",
    ]


def test_coverage_beginning_and_ending_mid_quarter_plans_whole_quarters() -> None:
    plan = plan_index_instances(window("2009-02-15", "2010-05-20", "2011-01-01"))
    keys = [item.instance_key for item in plan.instances]
    # The instance is published per quarter, so a partial intersection is still planned
    # in full rather than requested in part.
    assert keys[0] == "2009QTR1"
    assert keys[-1] == "2010QTR2"
    assert len(keys) == 6


def test_an_incoherent_window_is_refused() -> None:
    with pytest.raises(ValueError, match="precedes coverage_start"):
        window("2024-12-31", "2024-01-01", "2025-01-01")
    with pytest.raises(ValueError, match="no quarter could ever be closed"):
        window("2024-01-01", "2024-12-31", "2023-06-01")


# --------------------------------------------------------------------------- #
# Determinism
# --------------------------------------------------------------------------- #
def test_the_plan_hash_is_deterministic() -> None:
    first = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-07-01"))
    second = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-07-01"))
    assert first.plan_hash() == second.plan_hash()


@pytest.mark.parametrize(
    ("start", "end", "as_of"),
    [
        ("2024-01-01", "2024-12-31", "2024-08-01"),
        ("2024-01-02", "2024-12-31", "2024-07-01"),
        ("2024-01-01", "2024-12-30", "2024-07-01"),
    ],
)
def test_any_change_to_the_window_changes_the_plan_hash(
    start: str,
    end: str,
    as_of: str,
) -> None:
    baseline = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-07-01"))
    altered = plan_index_instances(window(start, end, as_of))
    assert altered.plan_hash() != baseline.plan_hash()


def test_the_plan_hash_covers_the_window_and_the_instance_list() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-07-01"))
    record = plan.as_record()
    assert record["policy_version"] == INDEX_PLAN_POLICY_VERSION
    assert record["window"]["as_of_date"] == "2024-07-01"  # type: ignore[index]
    assert record["window"]["coverage_start"] == "2024-01-01"  # type: ignore[index]
    assert len(record["instances"]) == len(plan.instances)  # type: ignore[arg-type]
    assert record["plan_sha256"] == plan.plan_hash()


def test_including_the_open_quarter_changes_the_plan_hash() -> None:
    closed = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-07-01"))
    opened = plan_index_instances(
        window("2024-01-01", "2024-12-31", "2024-07-01", include_open=True)
    )
    assert closed.plan_hash() != opened.plan_hash()


# --------------------------------------------------------------------------- #
# Coverage semantics
# --------------------------------------------------------------------------- #
def test_coverage_summary_separates_finalized_from_provisional() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-08-15"))
    summary = coverage_summary(plan, satisfied_keys=["2024QTR1", "2024QTR2"])
    assert summary["required_closed_quarters_planned"] == 2
    assert summary["required_closed_quarters_successful"] == 2
    assert summary["required_closed_quarters_failed_or_unavailable"] == 0
    assert summary["closed_quarter_coverage_complete"] is True
    assert summary["finalized_reconciliation_coverage"] == ["2024QTR1", "2024QTR2"]
    assert summary["provisional_reconciliation_coverage"] == []
    assert summary["provisional_open_quarter"] == "2024QTR3"
    assert summary["provisional_open_quarter_not_retrieved"] is True
    assert summary["future_quarters_not_planned"] == ["2024QTR4"]


def test_a_missing_closed_quarter_is_reported_as_incomplete() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-08-15"))
    summary = coverage_summary(plan, satisfied_keys=["2024QTR1"])
    assert summary["required_closed_quarters_failed_or_unavailable"] == 1
    assert summary["required_closed_quarters_failed_keys"] == ["2024QTR2"]
    assert summary["closed_quarter_coverage_complete"] is False


def test_a_retrieved_open_quarter_is_provisional_never_finalized() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-08-15", include_open=True))
    summary = coverage_summary(
        plan,
        satisfied_keys=["2024QTR1", "2024QTR2", "2024QTR3"],
        retrieved_open=True,
    )
    assert summary["provisional_reconciliation_coverage"] == ["2024QTR3"]
    assert "2024QTR3" not in summary["finalized_reconciliation_coverage"]  # type: ignore[operator]
    assert summary["closed_quarter_coverage_complete"] is True


def test_a_missing_open_quarter_does_not_fail_closed_quarter_coverage() -> None:
    plan = plan_index_instances(window("2024-01-01", "2024-12-31", "2024-08-15"))
    summary = coverage_summary(plan, satisfied_keys=["2024QTR1", "2024QTR2"])
    # The open quarter was never retrieved, but historical completion is unaffected.
    assert summary["provisional_open_quarter_retrieved"] is False
    assert summary["closed_quarter_coverage_complete"] is True
    assert summary["provisional_reconciliation_coverage"] == []
