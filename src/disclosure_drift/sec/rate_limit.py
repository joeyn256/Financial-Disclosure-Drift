"""One shared aggregate rate limiter for all SEC hosts.

Default 4 requests per second, configurable maximum 8, burst 1. The published
SEC ceiling of 10 requests per second is not the project target.

Coordination has two layers:

* an in-process token bucket, and
* a lease file under ``{data_root}/locks`` so separate worker processes cannot
  collectively exceed the shared rate.

The limiter takes an injected clock and sleep function, so every behaviour here is
testable without wall-clock delays and without network access.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "DEFAULT_BURST",
    "DEFAULT_REQUESTS_PER_SECOND",
    "MAX_REQUESTS_PER_SECOND",
    "SEC_PUBLISHED_CEILING_PER_SECOND",
    "AggregateRateLimiter",
    "RateLimitConfigError",
    "SharedRateLease",
]

DEFAULT_REQUESTS_PER_SECOND: Final = 4.0
MAX_REQUESTS_PER_SECOND: Final = 8.0
SEC_PUBLISHED_CEILING_PER_SECOND: Final = 10.0
DEFAULT_BURST: Final = 1
_LEASE_FILENAME: Final = "sec_rate_limiter.json"


class RateLimitConfigError(DisclosureDriftError):
    """Raised when a rate-limit configuration exceeds policy."""


@dataclass(frozen=True, slots=True)
class SharedRateLease:
    """Cross-process record of the last granted request slot."""

    path: Path
    owner_pid: int

    def read_last_grant(self) -> float:
        """Return the last granted monotonic-equivalent timestamp, or 0.0."""
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return 0.0
        value = payload.get("last_grant_epoch")
        return float(value) if isinstance(value, (int, float)) else 0.0

    def write_last_grant(self, epoch_seconds: float) -> None:
        """Record the last granted slot atomically."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".part")
        payload = {"last_grant_epoch": epoch_seconds, "owner_pid": self.owner_pid}
        temporary.write_text(json.dumps(payload), encoding="utf-8")
        # Same-directory rename: atomic replacement on the same filesystem.
        temporary.replace(self.path)


class AggregateRateLimiter:
    """Token bucket shared across every SEC host and every worker pool."""

    def __init__(
        self,
        requests_per_second: float = DEFAULT_REQUESTS_PER_SECOND,
        burst: int = DEFAULT_BURST,
        *,
        lease: SharedRateLease | None = None,
        clock: Callable[[], float] | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if requests_per_second <= 0:
            message = "requests_per_second must be positive"
            raise RateLimitConfigError(message)
        if requests_per_second > MAX_REQUESTS_PER_SECOND:
            message = (
                f"requests_per_second {requests_per_second} exceeds the project maximum "
                f"{MAX_REQUESTS_PER_SECOND}. The SEC published ceiling of "
                f"{SEC_PUBLISHED_CEILING_PER_SECOND} is not the project target."
            )
            raise RateLimitConfigError(message)
        if burst < 1:
            message = "burst must be at least 1"
            raise RateLimitConfigError(message)

        self._interval = 1.0 / requests_per_second
        self._burst = burst
        self._lease = lease
        self._clock = clock or time.monotonic
        self._sleeper = sleeper or time.sleep
        self._mutex = Lock()
        self._tokens = float(burst)
        self._last_refill = self._clock()
        self._granted = 0
        self._total_wait = 0.0
        self._halted_until: float | None = None

    # -- properties -------------------------------------------------------- #
    @property
    def requests_per_second(self) -> float:
        """Configured aggregate rate."""
        return 1.0 / self._interval

    @property
    def granted(self) -> int:
        """Number of slots granted."""
        return self._granted

    @property
    def total_wait_seconds(self) -> float:
        """Total time spent waiting for slots."""
        return self._total_wait

    @property
    def is_halted(self) -> bool:
        """Whether aggregate traffic is currently halted by a cooldown."""
        return self._halted_until is not None and self._clock() < self._halted_until

    # -- operations -------------------------------------------------------- #
    def halt(self, seconds: float) -> None:
        """Halt all aggregate traffic for ``seconds``.

        Used for a ``403`` or an unqualified ``429`` so every worker is stopped,
        not merely the one that observed the response.
        """
        with self._mutex:
            self._halted_until = self._clock() + max(seconds, 0.0)

    def acquire(self) -> float:
        """Acquire one request slot, waiting if necessary. Returns the wait taken."""
        with self._mutex:
            waited = 0.0
            if self._halted_until is not None:
                remaining = self._halted_until - self._clock()
                if remaining > 0:
                    self._sleeper(remaining)
                    waited += remaining
                self._halted_until = None

            waited += self._wait_for_shared_lease()
            waited += self._wait_for_token()

            self._tokens -= 1.0
            self._granted += 1
            self._total_wait += waited
            if self._lease is not None:
                self._lease.write_last_grant(time.time())
            return waited

    # -- internals --------------------------------------------------------- #
    def _refill(self) -> None:
        now = self._clock()
        elapsed = max(now - self._last_refill, 0.0)
        self._last_refill = now
        self._tokens = min(float(self._burst), self._tokens + elapsed / self._interval)

    def _wait_for_token(self) -> float:
        waited = 0.0
        self._refill()
        while self._tokens < 1.0:
            deficit = (1.0 - self._tokens) * self._interval
            self._sleeper(deficit)
            waited += deficit
            self._refill()
        return waited

    def _wait_for_shared_lease(self) -> float:
        if self._lease is None:
            return 0.0
        last_grant = self._lease.read_last_grant()
        if last_grant <= 0.0:
            return 0.0
        remaining = (last_grant + self._interval) - time.time()
        if remaining <= 0:
            return 0.0
        self._sleeper(remaining)
        return remaining
