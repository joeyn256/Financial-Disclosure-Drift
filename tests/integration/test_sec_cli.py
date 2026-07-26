"""Milestone 2 CLI surface: offline behaviour and exit codes.

Exit codes: 0 success, 1 configuration error, 2 usage, 3 stage not enabled,
4 gate failure.
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

import pytest

from disclosure_drift.config import ENV_PREFIX, SEC_USER_AGENT_ENV

VALID_USER_AGENT = "Financial Disclosure Drift research@your-institution.edu"
EXIT_CONFIG_ERROR = 1
EXIT_USAGE = 2
EXIT_STAGE_NOT_ENABLED = 3


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


def test_sec_group_is_registered(repo_root: Path) -> None:
    result = _run(["sec", "--help"], repo_root)
    normalized = " ".join(result.stdout.split())
    assert result.returncode == 0
    for command in (
        "census",
        "select-pilot",
        "show-pilot",
        "ingest-pilot",
        "validate-inventory",
        "forecast-storage",
        "build-release",
        "verify-release",
        "backup",
        "restore-test",
    ):
        assert command in normalized


def test_top_level_help_lists_the_sec_group(repo_root: Path) -> None:
    normalized = " ".join(_run(["--help"], repo_root).stdout.split())
    assert "validate-sec-config" in normalized
    assert "sec " in normalized or "sec\n" in normalized


def test_outcome_commands_do_not_exist(repo_root: Path) -> None:
    for forbidden in ("evaluate-outcomes", "build-outcomes", "compute-ddi"):
        result = _run([forbidden], repo_root)
        assert result.returncode == EXIT_USAGE
        assert "invalid choice" in result.stderr


def test_validate_sec_config_fails_without_a_contact_identity(repo_root: Path) -> None:
    result = _run(["validate-sec-config"], repo_root)
    assert result.returncode == EXIT_CONFIG_ERROR
    assert "SEC contact identity invalid" in result.stderr
    assert "not set or is blank" in result.stderr


def test_validate_sec_config_rejects_the_unchanged_example(repo_root: Path) -> None:
    example = "Example Researcher researcher@example.com"
    result = _run(["validate-sec-config"], repo_root, env={SEC_USER_AGENT_ENV: example})
    assert result.returncode == EXIT_CONFIG_ERROR
    assert "placeholder domain" in result.stderr


def test_validate_sec_config_succeeds_and_hides_the_value(repo_root: Path) -> None:
    result = _run(["validate-sec-config"], repo_root, env={SEC_USER_AGENT_ENV: VALID_USER_AGENT})
    combined = result.stdout + result.stderr
    assert result.returncode == 0, result.stderr
    assert "SEC configuration valid." in result.stdout
    assert "value not displayed" in result.stdout
    assert VALID_USER_AGENT not in combined
    assert "research@your-institution.edu" not in combined


def test_validate_sec_config_reports_policy_values(repo_root: Path) -> None:
    result = _run(["validate-sec-config"], repo_root, env={SEC_USER_AGENT_ENV: VALID_USER_AGENT})
    normalized = " ".join(result.stdout.split())
    assert "4.0 requests/second, burst 1" in normalized
    assert "connect 10.0s" in normalized
    assert "5 transient retries" in normalized
    assert "cooldown 600.0s" in normalized
    assert "network : disabled (Stage M2.1)" in normalized
    assert "companyfacts : disabled (reconciliation only)" in normalized


def test_network_commands_fail_before_requesting_when_identity_is_missing(
    repo_root: Path,
) -> None:
    for command in ("census", "ingest-pilot"):
        result = _run(["sec", command], repo_root)
        assert result.returncode == EXIT_CONFIG_ERROR
        assert "SEC contact identity invalid" in result.stderr


def test_network_commands_refuse_while_network_is_disabled(repo_root: Path) -> None:
    for command, stage in (("census", "Stage M2.2"), ("ingest-pilot", "Stage M2.5")):
        result = _run(["sec", command], repo_root, env={SEC_USER_AGENT_ENV: VALID_USER_AGENT})
        assert result.returncode == EXIT_STAGE_NOT_ENABLED
        assert stage in result.stderr
        assert "network access is disabled" in result.stderr


@pytest.mark.parametrize(
    ("command", "stage"),
    [
        ("select-pilot", "Stage M2.3"),
        ("show-pilot", "Stage M2.3"),
        ("forecast-storage", "Stage M2.7"),
        ("build-release", "Stage M2.7"),
        ("verify-release", "Stage M2.7"),
        ("restore-test", "Stage M2.7"),
    ],
)
def test_unimplemented_stages_refuse_with_exit_three(
    repo_root: Path, command: str, stage: str
) -> None:
    result = _run(["sec", command], repo_root)
    assert result.returncode == EXIT_STAGE_NOT_ENABLED
    assert stage in result.stderr


def test_backup_validates_the_backup_root_first(repo_root: Path) -> None:
    unset = _run(["sec", "backup"], repo_root)
    assert unset.returncode == EXIT_CONFIG_ERROR
    assert "backup root is not configured" in unset.stderr


def test_backup_with_a_configured_root_defers_to_its_stage(repo_root: Path, tmp_path: Path) -> None:
    result = _run(
        ["sec", "backup"],
        repo_root,
        env={"DISCLOSURE_DRIFT_BACKUP_ROOT": str(tmp_path)},
    )
    assert result.returncode == EXIT_STAGE_NOT_ENABLED
    assert "Stage M2.7" in result.stderr


def test_validate_inventory_builds_the_catalog_offline(repo_root: Path, tmp_path: Path) -> None:
    result = _run(
        ["sec", "validate-inventory"],
        repo_root,
        env={"DISCLOSURE_DRIFT_DATA_ROOT": str(tmp_path)},
    )
    normalized = " ".join(result.stdout.split())

    assert result.returncode == 0, result.stderr
    assert "Inventory catalog validated." in result.stdout
    assert "quick_check : ok" in normalized
    assert "integrity_check : ok" in normalized
    assert "0 violation(s)" in normalized
    assert "reference SIC codes : 0" in normalized
    assert "accessions inventoried : 0" in normalized
    assert (tmp_path / "catalog" / "sec_ingestion.sqlite3").is_file()
    assert (tmp_path / "raw" / "sec" / "quarantine").is_dir()
    assert (tmp_path / "audit" / "sec").is_dir()


def test_validate_inventory_is_idempotent(repo_root: Path, tmp_path: Path) -> None:
    env = {"DISCLOSURE_DRIFT_DATA_ROOT": str(tmp_path)}
    first = _run(["sec", "validate-inventory"], repo_root, env=env)
    second = _run(["sec", "validate-inventory"], repo_root, env=env)

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert "migrations applied : initial" in " ".join(first.stdout.split())
    assert "migrations applied : none pending" in " ".join(second.stdout.split())


def test_validate_inventory_leaves_no_writer_lease_behind(repo_root: Path, tmp_path: Path) -> None:
    _run(
        ["sec", "validate-inventory"],
        repo_root,
        env={"DISCLOSURE_DRIFT_DATA_ROOT": str(tmp_path)},
    )
    assert not (tmp_path / "locks" / "catalog_writer.lease").exists()


def test_show_cohorts_states_the_authoritative_date_source(repo_root: Path) -> None:
    result = _run(["show-cohorts"], repo_root)
    assert result.returncode == 0
    assert "official SEC filing date" in result.stdout
    assert "audit-only cohort" in result.stdout
    assert "decision_010_temporal_availability_and_cohort_assignment.md" in result.stdout
