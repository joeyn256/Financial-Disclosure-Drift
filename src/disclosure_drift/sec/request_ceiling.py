"""Cumulative physical-attempt ceiling for one acquisition window.

Milestone 2 bounds requests two ways, and neither is this one: ``index_retrieval`` derives a
**logical** retrieval budget, and ``http_client`` caps retries and cooldowns **within a single
retrieval**. Neither accumulates *physical* attempts across a window, so an approved window
ceiling had no production path. Decision 028 §7 fixes the invariant this module enforces:

.. code-block:: text

    actual_physical_attempt_count <= approved_request_ceiling

The refusal happens **before** the attempt that would exceed the ceiling, so attempt ``C+1`` is
never placed and the counter remains ``C``. A refused attempt never reaches transport.

Reaching the ceiling exactly is **not** a failure. Decision 028 §7 supersedes every formulation
requiring attempts to be strictly below the ceiling:

- a complete run ending exactly at ``C`` succeeds;
- equality **with planned work remaining** is ``stopped_at_ceiling`` with
  ``SEC_REQUEST_CEILING_EXHAUSTED``;
- Gate H separately requires a complete, reconciled plan, so equality alone can never be read as
  success.

The gate never decides whether planned work remains — only its caller knows that — and it never
raises its own ceiling. A resume carries consumed attempts forward; if the proven worst-case
remainder does not fit the remaining headroom, the caller stops for re-planning and a fresh exact
approval rather than silently enlarging the active window.

This module opens no socket and holds no transport. It is the seam scenario A5's ceiling
substitution injects at.
"""

from __future__ import annotations

import threading
from typing import Final

__all__ = [
    "CEILING_EXHAUSTED_REASON_CODE",
    "PhysicalAttemptCeiling",
    "RequestCeilingExhaustedError",
]

#: The registered reason a ceiling refusal names (Decision 028 §6). Distinct from
#: ``SEC_RETRIES_EXHAUSTED``, which means one logical retrieval exhausted response-policy
#: retries rather than that the window-wide physical-attempt ceiling was consumed.
CEILING_EXHAUSTED_REASON_CODE: Final = "SEC_REQUEST_CEILING_EXHAUSTED"


class RequestCeilingExhaustedError(RuntimeError):
    """Raised instead of placing an attempt that would exceed the approved ceiling.

    Carries the registered reason code so a caller converts the refusal into evidence
    rather than into an empty or successful result.
    """

    def __init__(self, approved_ceiling: int, consumed: int) -> None:
        self.approved_ceiling = approved_ceiling
        self.consumed = consumed
        self.reason_code: Final = CEILING_EXHAUSTED_REASON_CODE
        super().__init__(
            f"placing another physical attempt would exceed the approved request ceiling: "
            f"{consumed} of {approved_ceiling} consumed, so attempt {consumed + 1} is refused "
            f"and never placed ({CEILING_EXHAUSTED_REASON_CODE})"
        )


class PhysicalAttemptCeiling:
    """One window's approved ceiling, its consumed count, and its refusal.

    The ceiling is fixed at construction and is never raised. ``before_attempt`` performs the
    check and the increment as one atomic operation, so a concurrent caller can never race the
    counter past the ceiling.
    """

    __slots__ = ("_approved_ceiling", "_consumed", "_lock")

    def __init__(self, approved_ceiling: int, *, consumed: int = 0) -> None:
        if approved_ceiling < 0:
            message = f"approved_ceiling must not be negative; received {approved_ceiling!r}"
            raise ValueError(message)
        if consumed < 0:
            message = f"consumed must not be negative; received {consumed!r}"
            raise ValueError(message)
        if consumed > approved_ceiling:
            message = (
                f"consumed {consumed} already exceeds approved_ceiling {approved_ceiling}; a "
                f"resume may not begin past its own ceiling"
            )
            raise ValueError(message)
        self._approved_ceiling = approved_ceiling
        self._consumed = consumed
        self._lock = threading.Lock()

    @property
    def approved_ceiling(self) -> int:
        """The exact owner-approved ceiling for this window.

        Read-only by construction: assigning to it raises ``AttributeError``, so no ceiling is
        raised during a running window (Decision 028 §7). Re-plan and obtain a fresh exact
        approval instead. ``__slots__`` additionally prevents introducing a shadowing attribute.
        """
        return self._approved_ceiling

    @property
    def consumed(self) -> int:
        """Physical attempts actually placed. Never exceeds :attr:`approved_ceiling`."""
        with self._lock:
            return self._consumed

    @property
    def remaining(self) -> int:
        """Headroom left before the next attempt would be refused."""
        with self._lock:
            return self._approved_ceiling - self._consumed

    @property
    def is_exhausted(self) -> bool:
        """Whether the next physical attempt would be refused.

        Exhausted headroom is a fact about the gate, not a verdict about the run: a complete
        run ending exactly at the ceiling succeeded.
        """
        return self.remaining == 0

    def before_attempt(self) -> int:
        """Consume one attempt, or refuse it.

        Returns the cumulative attempt ordinal just consumed. Raises
        :class:`RequestCeilingExhaustedError` when placing the attempt would exceed the ceiling,
        in which case nothing is consumed and no attempt is placed.
        """
        with self._lock:
            if self._consumed >= self._approved_ceiling:
                raise RequestCeilingExhaustedError(self._approved_ceiling, self._consumed)
            self._consumed += 1
            return self._consumed

    def fits(self, worst_case_remaining_attempts: int) -> bool:
        """Whether a proven worst-case remainder fits the remaining headroom.

        Asking is never an attempt: this consumes nothing. A ``False`` answer means the caller
        must stop for re-planning and a fresh exact approval, not enlarge the active ceiling.
        """
        if worst_case_remaining_attempts < 0:
            message = (
                f"worst_case_remaining_attempts must not be negative; "
                f"received {worst_case_remaining_attempts!r}"
            )
            raise ValueError(message)
        return worst_case_remaining_attempts <= self.remaining

    def stopped_at_ceiling(self, *, planned_work_remains: bool) -> bool:
        """Whether this window ends as ``stopped_at_ceiling`` (Decision 028 §7).

        Only equality **with planned work remaining** is a stop. The gate cannot know whether
        work remains, so the caller states it.
        """
        return self.is_exhausted and planned_work_remains
