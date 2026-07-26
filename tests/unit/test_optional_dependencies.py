"""Optional-dependency contracts that do not depend on global test-mode state."""

from __future__ import annotations

import builtins
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from disclosure_drift.sec.httpx_transport import (
    HTTPX_INSTALL_HINT,
    HttpxTransport,
    httpx_is_available,
)
from disclosure_drift.sec.transport import TransportUnavailableError

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_install_hint_names_the_approved_extra() -> None:
    assert 'pip install -e ".[dev,sec]"' in HTTPX_INSTALL_HINT


def test_availability_probe_matches_the_import_system() -> None:
    assert httpx_is_available() is (importlib.util.find_spec("httpx") is not None)


def test_pyarrow_is_not_installed_in_either_environment() -> None:
    """PyArrow is deferred to Stage M2.7 and must not appear before then."""
    assert importlib.util.find_spec("pyarrow") is None


def test_transport_refuses_to_construct_without_the_extra(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Simulate the missing optional import deterministically in either CI job."""
    real_import = builtins.__import__

    def import_without_httpx(
        name: str,
        globals_: object = None,
        locals_: object = None,
        fromlist: object = (),
        level: int = 0,
    ) -> object:
        if name == "httpx":
            message = "simulated missing optional dependency"
            raise ImportError(message)
        return real_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", import_without_httpx)
    with pytest.raises(TransportUnavailableError, match="dev,sec"):
        HttpxTransport()


def test_ordinary_modules_do_not_import_an_http_client() -> None:
    """A fresh interpreter importing package modules must not load httpx."""
    program = (
        "import sys;"
        "import disclosure_drift;"
        "from disclosure_drift.sec import http_client, source_registry, temporal;"
        "print('httpx' in sys.modules)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert completed.stdout.strip() == "False"


def test_retrieval_policy_is_importable_without_the_extra() -> None:
    """Policy code must be reviewable and testable in the core environment."""
    from disclosure_drift.sec.http_client import RetrievalPolicy, SecClient

    assert RetrievalPolicy().cooldown_seconds >= 600.0
    assert SecClient.__module__ == "disclosure_drift.sec.http_client"
