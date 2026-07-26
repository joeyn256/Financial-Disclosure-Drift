"""Aggregate rate limiter behaviour, exercised with an injected clock."""

from __future__ import annotations

from pathlib import Path

import pytest

from disclosure_drift.sec.rate_limit import (
    DEFAULT_REQUESTS_PER_SECOND,
    MAX_REQUESTS_PER_SECOND,
    SEC_PUBLISHED_CEILING_PER_SECOND,
    AggregateRateLimiter,
    RateLimitConfigError,
    SharedRateLease,
)


class FakeClock:
    """Monotonic clock advanced only by the sleeper."""

    def __init__(self) -> None:
        self.now = 1_000.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def test_default_rate_is_four_and_below_the_sec_ceiling() -> None:
    assert DEFAULT_REQUESTS_PER_SECOND == 4.0
    assert MAX_REQUESTS_PER_SECOND == 8.0
    assert MAX_REQUESTS_PER_SECOND < SEC_PUBLISHED_CEILING_PER_SECOND


def test_configured_rate_above_the_project_maximum_is_rejected() -> None:
    with pytest.raises(RateLimitConfigError, match="exceeds the project maximum"):
        AggregateRateLimiter(requests_per_second=8.5)


@pytest.mark.parametrize("value", [0.0, -1.0])
def test_non_positive_rate_is_rejected(value: float) -> None:
    with pytest.raises(RateLimitConfigError, match="must be positive"):
        AggregateRateLimiter(requests_per_second=value)


def test_burst_below_one_is_rejected() -> None:
    with pytest.raises(RateLimitConfigError, match="at least 1"):
        AggregateRateLimiter(burst=0)


def test_burst_of_one_serializes_requests() -> None:
    clock = FakeClock()
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)

    assert limiter.acquire() == 0.0
    second_wait = limiter.acquire()

    assert second_wait == pytest.approx(0.25)
    assert limiter.granted == 2
    assert limiter.total_wait_seconds == pytest.approx(0.25)


def test_sustained_rate_never_exceeds_the_configured_value() -> None:
    clock = FakeClock()
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
    start = clock.now

    for _ in range(9):
        limiter.acquire()

    elapsed = clock.now - start
    assert limiter.granted == 9
    assert elapsed >= (9 - 1) / limiter.requests_per_second


def test_halt_stops_every_caller_until_the_cooldown_expires() -> None:
    clock = FakeClock()
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)

    limiter.halt(600.0)
    assert limiter.is_halted

    waited = limiter.acquire()

    assert waited >= 600.0
    assert not limiter.is_halted


def test_shared_lease_serializes_separate_worker_pools(tmp_path: Path) -> None:
    lease_path = tmp_path / "locks" / "sec_rate_limiter.json"
    lease_one = SharedRateLease(path=lease_path, owner_pid=101)
    lease_two = SharedRateLease(path=lease_path, owner_pid=202)

    clock_one = FakeClock()
    clock_two = FakeClock()
    worker_one = AggregateRateLimiter(
        4.0, lease=lease_one, clock=clock_one.time, sleeper=clock_one.sleep
    )
    worker_two = AggregateRateLimiter(
        4.0, lease=lease_two, clock=clock_two.time, sleeper=clock_two.sleep
    )

    worker_one.acquire()
    worker_two.acquire()

    assert lease_path.is_file()
    assert lease_two.read_last_grant() > 0.0
    assert clock_two.sleeps, "the second pool must wait for the shared lease"


def test_missing_lease_file_does_not_block(tmp_path: Path) -> None:
    lease = SharedRateLease(path=tmp_path / "absent.json", owner_pid=1)
    assert lease.read_last_grant() == 0.0


def test_corrupt_lease_file_is_treated_as_absent(tmp_path: Path) -> None:
    path = tmp_path / "sec_rate_limiter.json"
    path.write_text("{not json", encoding="utf-8")
    assert SharedRateLease(path=path, owner_pid=1).read_last_grant() == 0.0
