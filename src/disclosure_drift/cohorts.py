"""Frozen temporal definitions for the Disclosure Drift study.

This module is the **canonical source of truth** for the study's temporal
cohorts, prospective maturity gates, and bootstrap seed. Every value here is a
frozen research definition transcribed from the approved Milestone 0 record:

* ``Docs/Decisions/decision_003_temporal_split.md`` — cohort windows
* ``Docs/Decisions/decision_005_2025_2026_recency_extension.md`` — maturity gates
* ``Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md`` — the
  date source used for assignment
* ``Docs/preregistration.md`` section 8 — temporal design
* ``Docs/preregistration.md`` section 15.1 — bootstrap seed
* ``Docs/preregistration.md`` section 25.1 — Deviation D001

The windows are **date-source agnostic**. Decision 010 makes the official SEC
filing date the authoritative assignment date and keeps the acceptance date as a
separate audit-only cohort; both are produced by calling :func:`cohort_for` twice.
Nothing in this module selects a date source.

These constants must never be changed by configuration files, environment
variables, or command-line flags. ``configs/project.yaml`` mirrors them for
transparency and :func:`disclosure_drift.config.load_config` hard-fails when the
mirror disagrees. Changing any value requires an approved research decision
record followed by an explicit code change reviewed against that record.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True, slots=True)
class CohortWindow:
    """An inclusive cohort-assignment-date window for one study cohort."""

    name: str
    start: date
    end: date
    role: str

    def contains(self, moment: date) -> bool:
        """Return ``True`` when ``moment`` falls inside the inclusive window.

        ``moment`` may be any cohort-assignment date. The caller chooses the date
        source; this method never does.
        """
        return self.start <= moment <= self.end

    @property
    def label(self) -> str:
        """Return an ISO ``start to end`` label for display."""
        return f"{self.start.isoformat()} to {self.end.isoformat()}"


COHORT_ORDER: Final[tuple[str, ...]] = (
    "development",
    "transition",
    "primary_test",
    "prospective",
    "monitoring",
)
"""Chronological cohort order. Also the required key order in ``project.yaml``."""

FROZEN_COHORTS: Final[Mapping[str, CohortWindow]] = MappingProxyType(
    {
        "development": CohortWindow(
            name="development",
            start=date(2010, 1, 1),
            end=date(2021, 12, 31),
            role=(
                "Feature development, estimator and hyperparameter selection, "
                "rolling-origin selection, and outcome-based analysis"
            ),
        ),
        "transition": CohortWindow(
            name="transition",
            start=date(2022, 1, 1),
            end=date(2023, 12, 31),
            role="Locked evaluation and mechanism analysis; no predictive-model tuning",
        ),
        "primary_test": CohortWindow(
            name="primary_test",
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
            role="One untouched confirmatory evaluation",
        ),
        "prospective": CohortWindow(
            name="prospective",
            start=date(2025, 1, 1),
            end=date(2025, 12, 31),
            role=(
                "Secondary confirmatory replication; predictions frozen and hashed "
                "before outcome linkage"
            ),
        ),
        "monitoring": CohortWindow(
            name="monitoring",
            start=date(2026, 1, 1),
            end=date(2026, 12, 31),
            role=(
                "Outcome-free disclosure-language and data-quality monitoring with "
                "frozen prospective predictions"
            ),
        ),
    }
)
"""The five frozen cohorts, keyed by cohort name."""

FROZEN_MATURITY_GATES: Final[Mapping[str, date]] = MappingProxyType(
    {
        "prospective_outcome_cutoff": date(2027, 3, 31),
        "monitoring_outcome_cutoff": date(2028, 3, 31),
    }
)
"""Earliest permitted outcome-availability cutoffs for the prospective cohorts."""

FROZEN_BOOTSTRAP_SEED: Final[int] = 20260725
"""Deterministic bootstrap seed fixed by the preregistration."""

FROZEN_SOURCE_RECORDS: Final[tuple[str, ...]] = (
    "Docs/Decisions/decision_003_temporal_split.md",
    "Docs/Decisions/decision_005_2025_2026_recency_extension.md",
    "Docs/preregistration.md (section 8, temporal design)",
    "Docs/preregistration.md (section 15.1, bootstrap)",
    "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
    "Docs/preregistration.md (section 25.1, Deviation D001)",
)
"""Governing research records for every constant in this module."""

STUDY_START: Final[date] = date(2010, 1, 1)
"""First cohort-assignment date covered by the design."""

STUDY_END: Final[date] = date(2026, 12, 31)
"""Last cohort-assignment date covered by the design."""


def cohort_for(moment: date) -> CohortWindow | None:
    """Return the cohort containing ``moment``, or ``None`` when outside the design."""
    for name in COHORT_ORDER:
        window = FROZEN_COHORTS[name]
        if window.contains(moment):
            return window
    return None


def _validate_frozen_definitions() -> None:
    """Assert the frozen constants are internally consistent at import time."""
    if set(FROZEN_COHORTS) != set(COHORT_ORDER):
        message = "COHORT_ORDER and FROZEN_COHORTS disagree on cohort names"
        raise AssertionError(message)

    previous: CohortWindow | None = None
    for name in COHORT_ORDER:
        window = FROZEN_COHORTS[name]
        if window.name != name:
            message = f"cohort {name!r} carries mismatched name {window.name!r}"
            raise AssertionError(message)
        if window.start > window.end:
            message = f"cohort {name!r} starts after it ends"
            raise AssertionError(message)
        if previous is not None and window.start != previous.end + timedelta(days=1):
            message = f"cohort {name!r} is not contiguous with {previous.name!r}"
            raise AssertionError(message)
        previous = window

    first = FROZEN_COHORTS[COHORT_ORDER[0]]
    last = FROZEN_COHORTS[COHORT_ORDER[-1]]
    if first.start != STUDY_START or last.end != STUDY_END:
        message = "cohort coverage does not span STUDY_START through STUDY_END"
        raise AssertionError(message)

    expected_gates = {"prospective_outcome_cutoff", "monitoring_outcome_cutoff"}
    if set(FROZEN_MATURITY_GATES) != expected_gates:
        message = f"FROZEN_MATURITY_GATES must define exactly {sorted(expected_gates)}"
        raise AssertionError(message)
    if FROZEN_MATURITY_GATES["prospective_outcome_cutoff"] <= last.start:
        message = "the prospective maturity gate must fall after the prospective cohort begins"
        raise AssertionError(message)
    if (
        FROZEN_MATURITY_GATES["monitoring_outcome_cutoff"]
        <= FROZEN_MATURITY_GATES["prospective_outcome_cutoff"]
    ):
        message = "the monitoring maturity gate must fall after the prospective gate"
        raise AssertionError(message)


_validate_frozen_definitions()
