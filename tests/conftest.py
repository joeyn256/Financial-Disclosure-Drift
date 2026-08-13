"""Shared fixtures for the Disclosure Drift test suite.

Every test runs with a sanitized environment and with in-process network access
blocked. Configuration fixtures write to ``tmp_path``, so no test depends on a
machine-specific directory.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest
import yaml

from disclosure_drift.cohorts import (
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
)
from disclosure_drift.config import ENV_PREFIX, SEC_USER_AGENT_ENV

REPO_ROOT = Path(__file__).resolve().parent.parent
SHIPPED_CONFIG = REPO_ROOT / "configs" / "project.yaml"
EXAMPLE_USER_AGENT = "Example Researcher researcher@example.com"


class NetworkAccessAttemptedError(RuntimeError):
    """Raised when code under test attempts to open a network connection."""


class VirtualClock:
    """A monotonic clock that only advances when the wait strategy is invoked.

    Offline tests exercise the real retry and rate-limiting code paths, so the policy
    still *requests* every delay it would request against the live SEC. This pair makes
    taking that delay free: :meth:`sleep` records the requested seconds and advances
    :meth:`time` by exactly that amount instead of blocking.

    Advancing the clock is what makes this correct rather than merely fast. The
    limiter's token-refill loop waits until enough time has passed, so a sleeper that
    returned immediately without moving the clock would spin forever instead of
    yielding a slot. Because virtual time tracks the requested delays exactly, the
    limiter grants slots on the same schedule it would in production.

    Each test constructs its own instance, so nothing is shared across tests, across
    modules, or across xdist workers, and no global time function is patched.
    """

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def time(self) -> float:
        """Return the current virtual time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Record a requested delay and advance virtual time by it, without blocking."""
        self.sleeps.append(seconds)
        self.now += seconds

    @property
    def total_slept(self) -> float:
        """Total virtual seconds the code under test asked to wait."""
        return sum(self.sleeps)


@pytest.fixture
def virtual_clock() -> VirtualClock:
    """Return a per-test deterministic clock/sleeper pair."""
    return VirtualClock()


@pytest.fixture(autouse=True)
def _isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every ``DISCLOSURE_DRIFT_*`` variable inherited from the host."""
    for name in [key for key in os.environ if key.startswith(ENV_PREFIX)]:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make any in-process socket use raise :class:`NetworkAccessAttemptedError`."""

    def _blocked(*args: Any, **kwargs: Any) -> Any:
        message = "network access is not permitted in the Milestone 1 test suite"
        raise NetworkAccessAttemptedError(message)

    monkeypatch.setattr(socket, "socket", _blocked)
    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked)


#: Staged in a subprocess that exits through ``os._exit``: the writing connection never gets its
#: close-time checkpoint, so the committed log stays pending exactly as an interrupted writer
#: leaves it. ``user_version`` is written because nothing in the project reads it, so the staged
#: transaction is a real committed write that carries no domain meaning of its own.
_PENDING_WAL_WRITER = """
import os
import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1], isolation_level=None)
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("BEGIN IMMEDIATE")
connection.execute("PRAGMA user_version = 66")
connection.execute("COMMIT")
os._exit(0)
"""


@pytest.fixture
def stage_pending_wal() -> Callable[[Path], None]:
    """Return a helper that leaves a committed, un-checkpointed WAL beside a SQLite catalog.

    The subprocess matters twice over. It denies SQLite the close-time checkpoint that would fold
    the log into the main database file, *and* it leaves no connection alive in the test process —
    which is what makes the resulting state prove anything. A live connection anywhere stops every
    other reader from checkpointing, so an assertion made in its shadow would hold no matter how
    the code under test opened the database.
    """

    def _stage(catalog: Path) -> None:
        staged = subprocess.run(  # noqa: S603
            [sys.executable, "-c", _PENDING_WAL_WRITER, str(catalog)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert staged.returncode == 0, staged.stderr
        log = catalog.with_name(f"{catalog.name}-wal")
        assert log.is_file() and log.stat().st_size > 0, "no pending log was staged"

    return _stage


@pytest.fixture
def repo_root() -> Path:
    """Return the repository root."""
    return REPO_ROOT


@pytest.fixture
def shipped_config() -> Path:
    """Return the tracked ``configs/project.yaml`` path."""
    return SHIPPED_CONFIG


@pytest.fixture
def frozen_mapping() -> dict[str, Any]:
    """Return a valid configuration mapping mirroring the frozen definitions."""
    return {
        "project": {"name": "disclosure-drift", "version": "0.1.0"},
        "paths": {"data_root": "./data", "log_dir": "./logs"},
        "logging": {"level": "INFO", "to_file": False, "filename": "disclosure_drift.log"},
        "sec": {
            "user_agent_env": SEC_USER_AGENT_ENV,
            "requests_per_second": 5.0,
            "max_retries": 3,
        },
        "cohorts": {
            name: {"start": FROZEN_COHORTS[name].start, "end": FROZEN_COHORTS[name].end}
            for name in COHORT_ORDER
        },
        "gates": dict(FROZEN_MATURITY_GATES),
        "seeds": {"bootstrap": FROZEN_BOOTSTRAP_SEED},
    }


@pytest.fixture
def write_config(tmp_path: Path) -> Callable[..., Path]:
    """Return a factory that writes a configuration mapping into ``tmp_path``."""

    def _write(mapping: Mapping[str, Any], name: str = "project.yaml") -> Path:
        path = tmp_path / name
        path.write_text(yaml.safe_dump(dict(mapping), sort_keys=False), encoding="utf-8")
        return path

    return _write


@pytest.fixture
def config_file(write_config: Callable[..., Path], frozen_mapping: dict[str, Any]) -> Path:
    """Return a temporary, valid configuration file path."""
    return write_config(frozen_mapping)
