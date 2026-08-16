"""CLI behaviour and exit codes, exercised through real subprocesses."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.config import ENV_PREFIX, SEC_USER_AGENT_ENV

EXAMPLE_USER_AGENT = "Example Researcher researcher@example.com"


def _run(
    arguments: list[str],
    cwd: Path,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    clean = {key: value for key, value in os.environ.items() if not key.startswith(ENV_PREFIX)}
    clean.update(env or {})
    return subprocess.run(
        [sys.executable, "-m", "disclosure_drift", *arguments],
        cwd=cwd,
        env=clean,
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_lists_both_commands(repo_root: Path) -> None:
    result = _run(["--help"], repo_root)
    normalized = " ".join(result.stdout.split())
    assert result.returncode == 0
    assert "validate-config" in normalized
    assert "show-cohorts" in normalized
    assert "no network access" in normalized


def test_version_flag(repo_root: Path) -> None:
    result = _run(["--version"], repo_root)
    assert result.returncode == 0
    assert "disclosure-drift 0.1.0" in result.stdout


def test_no_command_prints_usage_and_exits_two(repo_root: Path) -> None:
    result = _run([], repo_root)
    assert result.returncode == 2
    assert "usage:" in result.stderr


def test_unknown_command_exits_two(repo_root: Path) -> None:
    result = _run(["ingest-filings"], repo_root)
    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_validate_config_succeeds(repo_root: Path) -> None:
    result = _run(["validate-config"], repo_root)
    assert result.returncode == 0, result.stderr
    assert "Configuration valid." in result.stdout
    assert "frozen definitions match" in result.stdout
    assert "20260725" in result.stdout


def test_validate_config_warns_when_user_agent_unset(repo_root: Path) -> None:
    result = _run(["validate-config"], repo_root)
    assert result.returncode == 0
    assert "not set" in result.stdout
    assert "WARNING" in result.stderr
    assert "Milestone 2" in result.stderr


def test_validate_config_never_prints_the_secret(repo_root: Path) -> None:
    result = _run(["validate-config"], repo_root, env={SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT})
    assert result.returncode == 0
    combined = result.stdout + result.stderr
    assert EXAMPLE_USER_AGENT not in combined
    assert "value not displayed" in result.stdout
    assert "WARNING" not in result.stderr


def test_show_cohorts_prints_frozen_definitions(repo_root: Path) -> None:
    result = _run(["show-cohorts"], repo_root)
    assert result.returncode == 0, result.stderr
    for cohort in ("development", "transition", "primary_test", "prospective", "monitoring"):
        assert cohort in result.stdout
    assert "2010-01-01 to 2021-12-31" in result.stdout
    assert "2024-01-01 to 2024-12-31" in result.stdout
    assert "2027-03-31" in result.stdout
    assert "2028-03-31" in result.stdout
    assert "20260725" in result.stdout
    assert "decision_003_temporal_split.md" in result.stdout


def test_commands_accept_an_explicit_config_path(repo_root: Path, config_file: Path) -> None:
    for command in ("validate-config", "show-cohorts"):
        result = _run([command, "--config", str(config_file)], repo_root)
        assert result.returncode == 0, result.stderr


def test_invalid_config_exits_one_with_actionable_message(
    repo_root: Path,
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    mapping = {**frozen_mapping, "logging": {**frozen_mapping["logging"], "level": "CHATTY"}}
    path = write_config(mapping)
    result = _run(["validate-config", "--config", str(path)], repo_root)
    assert result.returncode == 1
    assert "configuration error" in result.stderr
    assert "logging.level" in result.stderr


def test_frozen_mismatch_exits_one(
    repo_root: Path,
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    cohorts = {name: dict(window) for name, window in frozen_mapping["cohorts"].items()}
    cohorts["primary_test"]["end"] = cohorts["primary_test"]["start"]
    path = write_config({**frozen_mapping, "cohorts": cohorts})
    result = _run(["show-cohorts", "--config", str(path)], repo_root)
    assert result.returncode == 1
    assert "cohorts.primary_test.end" in result.stderr
    assert "approved decision record" in result.stderr


def test_unknown_environment_variable_exits_one(repo_root: Path) -> None:
    result = _run(["validate-config"], repo_root, env={"DISCLOSURE_DRIFT_COHORT_START": "2010"})
    assert result.returncode == 1
    assert "unrecognized environment variable" in result.stderr


def test_the_evidence_root_is_recognized_and_changes_no_rendered_value(
    repo_root: Path, tmp_path: Path
) -> None:
    """Accepted **Decision 095 R80**, at the boundary the finding was measured at.

    The central loader rejects every unrecognized ``DISCLOSURE_DRIFT_*`` name **before a
    command dispatches**, which is why the two Decision 094 PRE-E0 commands returned
    configuration exit ``1`` before R80: their required runtime root was not recognized.
    Recognition is proved here by an ordinary command succeeding with the variable set, and
    it is bounded by the control above — an unrelated unknown name still exits ``1``. The
    value reaches no rendered output on either path.
    """
    synthetic = tmp_path / "synthetic-runtime-root"
    synthetic.mkdir()
    with_root = _run(
        ["validate-config"], repo_root, env={"DISCLOSURE_DRIFT_EVIDENCE_ROOT": str(synthetic)}
    )
    without_root = _run(["validate-config"], repo_root)

    assert with_root.returncode == 0, with_root.stderr
    assert with_root.stdout == without_root.stdout
    assert str(synthetic) not in with_root.stdout + with_root.stderr
    assert "synthetic-runtime-root" not in with_root.stdout + with_root.stderr


@pytest.mark.parametrize("command", ["validate-config", "show-cohorts"])
def test_commands_run_from_a_subdirectory(repo_root: Path, command: str) -> None:
    result = _run([command], repo_root / "src" / "disclosure_drift")
    assert result.returncode == 0, result.stderr
