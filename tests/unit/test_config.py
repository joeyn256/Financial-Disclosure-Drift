"""Configuration loading behaviour."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from disclosure_drift.cohorts import (
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
)
from disclosure_drift.config import (
    SEC_USER_AGENT_ENV,
    ConfigValidationError,
    ProjectConfig,
    default_config_path,
    load_config,
)

EXAMPLE_USER_AGENT = "Example Researcher researcher@example.com"


def test_loads_the_tracked_configuration(shipped_config: Path) -> None:
    config = load_config(shipped_config, env={})
    assert isinstance(config, ProjectConfig)
    assert config.project.name == "disclosure-drift"
    assert config.paths.data_root == Path("./data")
    assert config.logging.level == "INFO"
    assert config.logging.to_file is False
    assert config.sec.user_agent_env == SEC_USER_AGENT_ENV
    assert config.sec.requests_per_second == 4.0
    assert config.sec.burst == 1
    assert config.sec.max_retries == 5
    assert config.sec.cooldown_seconds >= 600.0
    assert config.seeds.bootstrap == FROZEN_BOOTSTRAP_SEED
    assert config.config_path == shipped_config


def test_tracked_configuration_uses_no_machine_specific_path(shipped_config: Path) -> None:
    text = shipped_config.read_text(encoding="utf-8")
    for marker in ("/Users/", "/home/", "~/", "C:\\Users"):
        assert marker not in text


def test_loads_temporary_configuration(config_file: Path) -> None:
    config = load_config(config_file, env={})
    expected_gate = FROZEN_MATURITY_GATES["prospective_outcome_cutoff"]
    assert config.cohorts["primary_test"].start == date(2024, 1, 1)
    assert config.gates.prospective_outcome_cutoff == expected_gate
    assert len(config.cohorts) == len(FROZEN_COHORTS)


def test_configuration_is_immutable(config_file: Path) -> None:
    config = load_config(config_file, env={})
    with pytest.raises(ValidationError):
        config.logging.level = "DEBUG"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        config.seeds.bootstrap = 1  # type: ignore[misc]


def test_cohort_names_follow_frozen_order(config_file: Path) -> None:
    config = load_config(config_file, env={})
    assert config.cohort_names() == COHORT_ORDER


def test_secret_is_resolved_on_demand_and_absent_from_repr(config_file: Path) -> None:
    config = load_config(config_file, env={})
    assert config.resolve_sec_user_agent(env={}) is None
    assert config.sec_user_agent_is_set(env={}) is False

    env = {SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT}
    assert config.resolve_sec_user_agent(env) == EXAMPLE_USER_AGENT
    assert config.sec_user_agent_is_set(env) is True

    rendered = f"{config!r} {config.model_dump_json()}"
    assert EXAMPLE_USER_AGENT not in rendered
    assert SEC_USER_AGENT_ENV in rendered


def test_blank_secret_is_treated_as_unset(config_file: Path) -> None:
    config = load_config(config_file, env={})
    assert config.resolve_sec_user_agent({SEC_USER_AGENT_ENV: "   "}) is None


def test_secret_read_from_process_environment(
    config_file: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = load_config(config_file, env={})
    monkeypatch.setenv(SEC_USER_AGENT_ENV, EXAMPLE_USER_AGENT)
    assert config.resolve_sec_user_agent() == EXAMPLE_USER_AGENT


def test_log_file_path_follows_configuration(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    disabled = load_config(write_config(frozen_mapping), env={})
    assert disabled.log_file_path() is None

    logging_section = dict(frozen_mapping["logging"])
    logging_section["to_file"] = True
    enabled_mapping = {**frozen_mapping, "logging": logging_section}
    enabled = load_config(write_config(enabled_mapping, "enabled.yaml"), env={})
    assert enabled.log_file_path() == Path("./logs") / "disclosure_drift.log"


def test_default_config_path_searches_upwards(
    repo_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(repo_root / "src" / "disclosure_drift")
    assert default_config_path() == (repo_root / "configs" / "project.yaml").resolve()


def test_reserved_top_level_key_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    mapping = {**frozen_mapping, "config_path": "./elsewhere.yaml"}
    path = write_config(mapping)
    with pytest.raises(ConfigValidationError, match="reserved top-level key"):
        load_config(path, env={})
