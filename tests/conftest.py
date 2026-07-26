"""Shared fixtures for the Disclosure Drift test suite.

Every test runs with a sanitized environment and with in-process network access
blocked. Configuration fixtures write to ``tmp_path``, so no test depends on a
machine-specific directory.
"""

from __future__ import annotations

import os
import socket
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
