"""Milestone 3.1: the cumulative physical-attempt ceiling gate.

Decision 028 §7 fixes the invariant ``actual_physical_attempt_count <= approved_request_ceiling``
and requires the refusal to happen *before* the attempt that would exceed it, so attempt ``C+1``
is never placed and the counter remains ``C``. Reaching the ceiling exactly is not a failure: a
complete run ending exactly at ``C`` succeeds, and only equality *with planned work remaining*
yields ``stopped_at_ceiling`` and ``SEC_REQUEST_CEILING_EXHAUSTED``.

The gate is the production path scenario A5 exercises, and the seam its ceiling substitution
injects at.
"""

from __future__ import annotations

import contextlib

import pytest

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)


# --------------------------------------------------------------------------- #
# Construction
# --------------------------------------------------------------------------- #
def test_a_ceiling_starts_unconsumed_with_full_headroom() -> None:
    gate = PhysicalAttemptCeiling(10)
    assert gate.approved_ceiling == 10
    assert gate.consumed == 0
    assert gate.remaining == 10
    assert not gate.is_exhausted


@pytest.mark.parametrize("ceiling", [-1, -10])
def test_a_negative_ceiling_is_refused(ceiling: int) -> None:
    with pytest.raises(ValueError, match="approved_ceiling"):
        PhysicalAttemptCeiling(ceiling)


def test_a_zero_ceiling_is_lawful_and_immediately_exhausted() -> None:
    """M3.1A and M3.1B both run at ceiling 0; one physical attempt is a phase failure."""
    gate = PhysicalAttemptCeiling(0)
    assert gate.remaining == 0
    assert gate.is_exhausted
    with pytest.raises(RequestCeilingExhaustedError):
        gate.before_attempt()
    assert gate.consumed == 0


def test_a_resume_carries_consumed_attempts_forward() -> None:
    gate = PhysicalAttemptCeiling(10, consumed=4)
    assert gate.consumed == 4
    assert gate.remaining == 6


@pytest.mark.parametrize("consumed", [-1, 11])
def test_an_incoherent_consumed_count_is_refused(consumed: int) -> None:
    """Fail closed: a resume may not begin already past its own ceiling."""
    with pytest.raises(ValueError, match="consumed"):
        PhysicalAttemptCeiling(10, consumed=consumed)


# --------------------------------------------------------------------------- #
# The boundary: exactly C succeeds, C+1 is never placed
# --------------------------------------------------------------------------- #
def test_exactly_the_ceiling_many_attempts_are_permitted() -> None:
    gate = PhysicalAttemptCeiling(3)
    assert [gate.before_attempt() for _ in range(3)] == [1, 2, 3]
    assert gate.consumed == 3
    assert gate.remaining == 0
    assert gate.is_exhausted


def test_the_attempt_that_would_exceed_the_ceiling_is_refused() -> None:
    gate = PhysicalAttemptCeiling(3)
    for _ in range(3):
        gate.before_attempt()

    with pytest.raises(RequestCeilingExhaustedError) as excinfo:
        gate.before_attempt()

    assert excinfo.value.approved_ceiling == 3
    assert excinfo.value.consumed == 3


def test_the_counter_remains_at_the_ceiling_after_a_refusal() -> None:
    """Attempt ``C+1`` is never placed, so it can never be counted."""
    gate = PhysicalAttemptCeiling(2)
    gate.before_attempt()
    gate.before_attempt()

    for _ in range(5):
        with pytest.raises(RequestCeilingExhaustedError):
            gate.before_attempt()

    assert gate.consumed == 2, "a refused attempt must never increment the counter"
    assert gate.consumed <= gate.approved_ceiling


@pytest.mark.parametrize("ceiling", [1, 2, 5, 25])
def test_the_invariant_holds_for_every_ceiling(ceiling: int) -> None:
    gate = PhysicalAttemptCeiling(ceiling)
    for _ in range(ceiling + 10):
        with contextlib.suppress(RequestCeilingExhaustedError):
            gate.before_attempt()
    assert gate.consumed == ceiling
    assert gate.consumed <= gate.approved_ceiling


# --------------------------------------------------------------------------- #
# Refusal carries the registered reason
# --------------------------------------------------------------------------- #
def test_a_refusal_names_the_registered_release_blocking_reason() -> None:
    gate = PhysicalAttemptCeiling(0)
    with pytest.raises(RequestCeilingExhaustedError) as excinfo:
        gate.before_attempt()

    code = excinfo.value.reason_code
    assert code == "SEC_REQUEST_CEILING_EXHAUSTED"
    assert code in REASON_CODES
    assert REASON_CODES[code].blocks_release


def test_a_refusal_is_distinct_from_an_exhausted_retry_budget() -> None:
    """Decision 028 §6: a consumed window ceiling is not an exhausted retry budget."""
    gate = PhysicalAttemptCeiling(0)
    with pytest.raises(RequestCeilingExhaustedError) as excinfo:
        gate.before_attempt()
    assert excinfo.value.reason_code != "SEC_RETRIES_EXHAUSTED"


# --------------------------------------------------------------------------- #
# Headroom questions a caller must be able to ask without consuming
# --------------------------------------------------------------------------- #
def test_asking_whether_work_fits_never_consumes_headroom() -> None:
    gate = PhysicalAttemptCeiling(10, consumed=4)
    assert gate.fits(6)
    assert not gate.fits(7)
    assert gate.consumed == 4, "a question must never be an attempt"


def test_a_worst_case_remainder_that_does_not_fit_stops_for_replanning() -> None:
    """Decision 028 §7: the run stops rather than silently enlarging the active ceiling."""
    gate = PhysicalAttemptCeiling(10, consumed=8)
    assert not gate.fits(3)
    assert gate.remaining == 2
    assert gate.approved_ceiling == 10, "the active ceiling is never raised"


@pytest.mark.parametrize("worst_case", [-1, -5])
def test_a_negative_worst_case_is_refused(worst_case: int) -> None:
    gate = PhysicalAttemptCeiling(10)
    with pytest.raises(ValueError, match="worst_case"):
        gate.fits(worst_case)


# --------------------------------------------------------------------------- #
# Equality is not, by itself, a failure
# --------------------------------------------------------------------------- #
def test_reaching_the_ceiling_exactly_is_not_itself_a_failure() -> None:
    """Decision 028 §7 supersedes every 'strictly below' formulation."""
    gate = PhysicalAttemptCeiling(4)
    for _ in range(4):
        gate.before_attempt()

    assert gate.is_exhausted
    assert gate.consumed == gate.approved_ceiling
    assert gate.remaining == 0
    # Exhausted headroom is a fact about the gate, not a verdict about the run:
    # only the caller knows whether planned work remains.
    assert not gate.stopped_at_ceiling(planned_work_remains=False)
    assert gate.stopped_at_ceiling(planned_work_remains=True)


def test_an_unexhausted_gate_is_never_stopped_at_ceiling() -> None:
    gate = PhysicalAttemptCeiling(4, consumed=1)
    assert not gate.stopped_at_ceiling(planned_work_remains=True)
    assert not gate.stopped_at_ceiling(planned_work_remains=False)


# --------------------------------------------------------------------------- #
# The active ceiling is immutable
# --------------------------------------------------------------------------- #
def test_the_ceiling_cannot_be_raised_during_a_running_window() -> None:
    """Decision 028 §7: no ceiling is raised during a running window."""
    gate = PhysicalAttemptCeiling(5)
    gate.before_attempt()
    with pytest.raises(AttributeError):
        gate.approved_ceiling = 50  # type: ignore[misc]
    assert gate.approved_ceiling == 5
