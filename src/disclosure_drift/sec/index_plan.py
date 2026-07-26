"""Quarterly index-instance planning for full-index reconciliation.

The quarterly company index is the required reconciliation unit. Which quarters are
required is decided **from explicit plan inputs only** — a coverage window and an
as-of date — never from the current clock. Reading the clock inside planning would make
the same coverage request produce different plans on different days, and would silently
turn an unfinished quarter into a missing one.

Three instance kinds, with different obligations:

``required_closed_quarter``
    The quarter's final calendar date is on or before ``as_of_date``. It is required for
    census completion, and a missing, failed, malformed, unavailable, or unreconciled
    instance blocks completion.

``provisional_open_quarter``
    The quarter containing ``as_of_date``. Optional by default, retrieved only when
    explicitly included. It is never described as finalized coverage, is reported
    separately, and its failure never fails closed-quarter historical completion.

``not_planned``
    A quarter beginning after ``as_of_date``. Not requested, not missing, and not a
    completion failure.

An annual index is never a substitute for a missing required quarterly instance. Any
future annual support is an additional reconciliation layer only.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Final, Literal

__all__ = [
    "INDEX_PLAN_POLICY_VERSION",
    "CoverageWindow",
    "IndexInstancePlan",
    "InstanceKind",
    "PlannedIndexInstances",
    "plan_index_instances",
    "quarter_of",
    "quarter_end",
    "quarter_start",
]

INDEX_PLAN_POLICY_VERSION: Final = "quarterly-index-instances/1.0"

InstanceKind = Literal[
    "required_closed_quarter",
    "provisional_open_quarter",
    "not_planned",
]

_QUARTER_END_MONTH: Final[Mapping[int, int]] = {1: 3, 2: 6, 3: 9, 4: 12}
_QUARTER_END_DAY: Final[Mapping[int, int]] = {1: 31, 2: 30, 3: 30, 4: 31}


def quarter_of(day: date) -> int:
    """Return the calendar quarter (1-4) containing ``day``."""
    return (day.month - 1) // 3 + 1


def quarter_start(year: int, quarter: int) -> date:
    """Return the first calendar date of ``year`` ``quarter``."""
    _require_quarter(quarter)
    return date(year, 3 * (quarter - 1) + 1, 1)


def quarter_end(year: int, quarter: int) -> date:
    """Return the last calendar date of ``year`` ``quarter``.

    Quarter ends are fixed calendar boundaries, so this is leap-year safe by
    construction: Q1 always ends 31 March, never 28 or 29 February.
    """
    _require_quarter(quarter)
    return date(year, _QUARTER_END_MONTH[quarter], _QUARTER_END_DAY[quarter])


def _require_quarter(quarter: int) -> None:
    if quarter not in {1, 2, 3, 4}:
        message = f"quarter must be 1, 2, 3, or 4; received {quarter!r}"
        raise ValueError(message)


@dataclass(frozen=True, slots=True)
class CoverageWindow:
    """Explicit coverage request and as-of date for one census plan.

    Every field is supplied by the caller. Nothing here consults the clock.
    """

    coverage_start: date
    coverage_end: date
    as_of_date: date
    include_open_quarter: bool = False
    policy_version: str = INDEX_PLAN_POLICY_VERSION

    def __post_init__(self) -> None:
        """Reject a window that cannot describe a coherent request."""
        if self.coverage_end < self.coverage_start:
            message = (
                f"coverage_end {self.coverage_end.isoformat()} precedes coverage_start "
                f"{self.coverage_start.isoformat()}"
            )
            raise ValueError(message)
        if self.as_of_date < self.coverage_start:
            message = (
                f"as_of_date {self.as_of_date.isoformat()} precedes coverage_start "
                f"{self.coverage_start.isoformat()}, so no quarter could ever be closed"
            )
            raise ValueError(message)

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence and the plan hash."""
        return {
            "coverage_start": self.coverage_start.isoformat(),
            "coverage_end": self.coverage_end.isoformat(),
            "as_of_date": self.as_of_date.isoformat(),
            "include_open_quarter": self.include_open_quarter,
            "policy_version": self.policy_version,
        }


@dataclass(frozen=True, slots=True)
class IndexInstancePlan:
    """One planned quarterly index instance."""

    year: int
    quarter: int
    kind: InstanceKind
    required: bool
    period_start: date
    period_end: date

    @property
    def instance_key(self) -> str:
        """Stable key, matching the SEC full-index path convention."""
        return f"{self.year}QTR{self.quarter}"

    @property
    def is_finalized_period(self) -> bool:
        """Whether this instance can contribute to finalized coverage.

        Only a closed quarter can. An open quarter is provisional however successfully
        it was retrieved.
        """
        return self.kind == "required_closed_quarter"

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence and the plan hash."""
        return {
            "instance_key": self.instance_key,
            "year": self.year,
            "quarter": self.quarter,
            "kind": self.kind,
            "required": self.required,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "is_finalized_period": self.is_finalized_period,
        }


@dataclass(frozen=True, slots=True)
class PlannedIndexInstances:
    """The full quarterly plan for one coverage request."""

    window: CoverageWindow
    instances: tuple[IndexInstancePlan, ...]
    excluded_future_quarters: tuple[str, ...]

    @property
    def required_closed(self) -> tuple[IndexInstancePlan, ...]:
        """Required closed-quarter instances, in chronological order."""
        return tuple(item for item in self.instances if item.kind == "required_closed_quarter")

    @property
    def provisional_open(self) -> IndexInstancePlan | None:
        """The provisional open-quarter instance, when the window reaches it."""
        for item in self.instances:
            if item.kind == "provisional_open_quarter":
                return item
        return None

    @property
    def required_keys(self) -> tuple[str, ...]:
        """Instance keys that must succeed for the census to claim completion."""
        return tuple(item.instance_key for item in self.instances if item.required)

    def plan_hash(self) -> str:
        """Deterministic hash over the window and the exact instance list.

        The coverage window, the as-of date, and every planned instance are included,
        so two plans agree only when they requested exactly the same thing.
        """
        payload = {
            "policy_version": self.window.policy_version,
            "window": dict(self.window.as_record()),
            "instances": [dict(item.as_record()) for item in self.instances],
            "excluded_future_quarters": list(self.excluded_future_quarters),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the census-plan report."""
        return {
            "policy_version": self.window.policy_version,
            "window": dict(self.window.as_record()),
            "required_closed_quarters_planned": len(self.required_closed),
            "provisional_open_quarter": (
                None if self.provisional_open is None else self.provisional_open.instance_key
            ),
            "provisional_open_quarter_included": (
                self.provisional_open is not None and self.provisional_open.required
            ),
            "excluded_future_quarters": list(self.excluded_future_quarters),
            "instances": [dict(item.as_record()) for item in self.instances],
            "required_keys": list(self.required_keys),
            "plan_sha256": self.plan_hash(),
        }


def plan_index_instances(window: CoverageWindow) -> PlannedIndexInstances:
    """Derive the quarterly index plan from an explicit coverage request.

    Args:
        window: Explicit coverage start, coverage end, and as-of date. The as-of date is
            never inferred from the clock.

    Returns:
        Every quarter intersecting the coverage window, classified as a required closed
        quarter, the provisional open quarter, or excluded as a future quarter. A quarter
        that only partially intersects the window is still planned in full, because the
        index instance is published per quarter and cannot be requested in part.
    """
    instances: list[IndexInstancePlan] = []
    excluded: list[str] = []

    open_year = window.as_of_date.year
    open_quarter = quarter_of(window.as_of_date)

    year = window.coverage_start.year
    quarter = quarter_of(window.coverage_start)
    while True:
        start = quarter_start(year, quarter)
        end = quarter_end(year, quarter)
        if start > window.coverage_end:
            break

        if start > window.as_of_date:
            # Begins after the as-of date: not requested, not missing, not a failure.
            excluded.append(f"{year}QTR{quarter}")
        elif (year, quarter) == (open_year, open_quarter):
            instances.append(
                IndexInstancePlan(
                    year=year,
                    quarter=quarter,
                    kind="provisional_open_quarter",
                    required=window.include_open_quarter,
                    period_start=start,
                    period_end=end,
                )
            )
        elif end <= window.as_of_date:
            instances.append(
                IndexInstancePlan(
                    year=year,
                    quarter=quarter,
                    kind="required_closed_quarter",
                    required=True,
                    period_start=start,
                    period_end=end,
                )
            )
        else:  # pragma: no cover - defensive; a quarter is closed, open, or future
            instances.append(
                IndexInstancePlan(
                    year=year,
                    quarter=quarter,
                    kind="provisional_open_quarter",
                    required=window.include_open_quarter,
                    period_start=start,
                    period_end=end,
                )
            )

        quarter += 1
        if quarter > 4:
            quarter = 1
            year += 1

    return PlannedIndexInstances(
        window=window,
        instances=tuple(instances),
        excluded_future_quarters=tuple(excluded),
    )


def coverage_summary(
    plan: PlannedIndexInstances,
    satisfied_keys: Sequence[str] = (),
    retrieved_open: bool = False,
) -> Mapping[str, object]:
    """Summarize coverage with finalized and provisional parts kept apart.

    Args:
        plan: The quarterly plan.
        satisfied_keys: Instance keys that were retrieved, parsed, and reconciled.
        retrieved_open: Whether the provisional open quarter was retrieved.

    Returns:
        A deterministic mapping the census report can print without ever describing the
        open quarter or a future period as finalized.
    """
    satisfied = set(satisfied_keys)
    closed = plan.required_closed
    successful = tuple(item for item in closed if item.instance_key in satisfied)
    failed = tuple(item for item in closed if item.instance_key not in satisfied)
    open_instance = plan.provisional_open
    return {
        "required_closed_quarters_planned": len(closed),
        "required_closed_quarters_successful": len(successful),
        "required_closed_quarters_failed_or_unavailable": len(failed),
        "required_closed_quarters_failed_keys": [item.instance_key for item in failed],
        "provisional_open_quarter": (None if open_instance is None else open_instance.instance_key),
        "provisional_open_quarter_retrieved": bool(open_instance is not None and retrieved_open),
        "provisional_open_quarter_not_retrieved": bool(
            open_instance is not None and not retrieved_open
        ),
        "future_quarters_not_planned": list(plan.excluded_future_quarters),
        "finalized_reconciliation_coverage": [item.instance_key for item in successful],
        "provisional_reconciliation_coverage": (
            [open_instance.instance_key] if open_instance is not None and retrieved_open else []
        ),
        "closed_quarter_coverage_complete": not failed,
        "plan_sha256": plan.plan_hash(),
    }
