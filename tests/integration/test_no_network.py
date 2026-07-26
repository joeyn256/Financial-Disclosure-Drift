"""Foundation commands must complete with in-process network access blocked.

The autouse ``_block_network`` fixture patches :mod:`socket` in *this* process.
A monkeypatch does not propagate into a child process, so strict blocking is
exercised in-process through :func:`disclosure_drift.cli.main` and
:mod:`runpy`; subprocess execution is reserved for CLI smoke and exit codes in
``test_cli.py``.
"""

from __future__ import annotations

import runpy
import socket
import sys
import warnings
from pathlib import Path

import pytest

from disclosure_drift.cli import main
from disclosure_drift.config import CONFIG_PATH_ENV

NETWORK_BLOCKED_MESSAGE = "network access is not permitted"


def test_the_guard_actually_blocks_sockets() -> None:
    with pytest.raises(RuntimeError, match=NETWORK_BLOCKED_MESSAGE):
        socket.socket()
    with pytest.raises(RuntimeError, match=NETWORK_BLOCKED_MESSAGE):
        socket.getaddrinfo("www.sec.gov", 443)
    with pytest.raises(RuntimeError, match=NETWORK_BLOCKED_MESSAGE):
        socket.create_connection(("www.sec.gov", 443))


@pytest.mark.parametrize("command", ["validate-config", "show-cohorts"])
def test_commands_succeed_with_network_blocked(
    command: str,
    shipped_config: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main([command, "--config", str(shipped_config)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out


def test_help_succeeds_with_network_blocked(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0
    assert "usage:" in capsys.readouterr().out


def test_module_execution_succeeds_with_network_blocked(
    shipped_config: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv(CONFIG_PATH_ENV, str(shipped_config))
    monkeypatch.setattr(sys, "argv", ["disclosure_drift", "show-cohorts"])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_module("disclosure_drift", run_name="__main__")

    assert excinfo.value.code == 0
    assert "Frozen temporal cohorts" in capsys.readouterr().out


def test_invalid_configuration_fails_without_network(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "absent.yaml"
    exit_code = main(["validate-config", "--config", str(missing)])
    assert exit_code == 1
    assert "configuration error" in capsys.readouterr().err
