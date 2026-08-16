"""Environment-override allowlist, secret recognition, and frozen-value protection."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.config import (
    BACKUP_ROOT_ENV,
    CONFIG_PATH_ENV,
    ENV_OVERRIDES,
    EVIDENCE_ROOT_ENV,
    FROZEN_CONFIG_SECTIONS,
    RECOGNIZED_ENV_VARS,
    RUNTIME_ROOT_ENV_VARS,
    SEC_USER_AGENT_ENV,
    SECRET_ENV_VARS,
    ConfigValidationError,
    UnknownEnvironmentOverrideError,
    load_config,
)

EXAMPLE_USER_AGENT = "Example Researcher researcher@example.com"


def test_allowlist_never_targets_a_frozen_section() -> None:
    targeted = {section for section, _ in ENV_OVERRIDES.values()}
    assert targeted.isdisjoint(FROZEN_CONFIG_SECTIONS)


def test_secret_variable_is_recognized_but_is_not_an_override() -> None:
    assert SEC_USER_AGENT_ENV in SECRET_ENV_VARS
    assert SEC_USER_AGENT_ENV in RECOGNIZED_ENV_VARS
    assert SEC_USER_AGENT_ENV not in ENV_OVERRIDES


def test_the_evidence_root_is_a_recognized_runtime_root_and_not_an_override() -> None:
    """Accepted **Decision 095 R80** items 1-3: recognized centrally, applied by nothing here.

    The Decision 094 operator surface requires this variable, and the central loader rejects
    every unrecognized ``DISCLOSURE_DRIFT_*`` name before a command dispatches — so without
    central recognition the two PRE-E0 commands would exit ``1`` before resolving anything.
    Recognition is all it gets: it is a **runtime root**, not a configuration override, and
    it appears in no override table, no secret set, and no tracked configuration section.
    """
    assert EVIDENCE_ROOT_ENV == "DISCLOSURE_DRIFT_EVIDENCE_ROOT"
    assert EVIDENCE_ROOT_ENV in RUNTIME_ROOT_ENV_VARS
    assert EVIDENCE_ROOT_ENV in RECOGNIZED_ENV_VARS
    assert EVIDENCE_ROOT_ENV not in ENV_OVERRIDES
    assert EVIDENCE_ROOT_ENV not in SECRET_ENV_VARS
    assert BACKUP_ROOT_ENV in RUNTIME_ROOT_ENV_VARS


def test_the_evidence_root_changes_no_configuration_value_and_is_never_rendered(
    config_file: Path,
) -> None:
    """**R80** items 3-4: ``load_config`` learns the name and stops.

    The value is a machine-local absolute path. It must not reach a model field, a
    configuration fingerprint, or a ``repr`` — so the loaded configuration is compared
    field-for-field against one loaded without the variable, and the synthetic value is
    searched for in the rendering.
    """
    synthetic = "/synthetic/not-a-real-evidence-root"
    baseline = load_config(config_file, env={})
    config = load_config(config_file, env={EVIDENCE_ROOT_ENV: synthetic})
    without_path = {"config_path"}

    assert config.model_dump(exclude=without_path) == baseline.model_dump(exclude=without_path)
    assert synthetic not in repr(config)
    assert "not-a-real-evidence-root" not in repr(config)


def test_recognition_comes_from_the_runtime_roots_and_not_from_a_command_bypass() -> None:
    """**R80** item 7 and Decision 095 §7 proof 5: the mutation control.

    ``RECOGNIZED_ENV_VARS`` is the union the loader consults, so removing the entry from
    ``RUNTIME_ROOT_ENV_VARS`` must stop the name being recognized — while an unrelated
    unknown ``DISCLOSURE_DRIFT_*`` name stays rejected either way. That difference is what
    separates "centrally recognized" from "the allowlist was loosened".
    """
    assert (
        frozenset(ENV_OVERRIDES)
        | SECRET_ENV_VARS
        | RUNTIME_ROOT_ENV_VARS
        | frozenset({CONFIG_PATH_ENV})
    ) == RECOGNIZED_ENV_VARS
    mutated = frozenset(RUNTIME_ROOT_ENV_VARS - {EVIDENCE_ROOT_ENV})
    recomputed = frozenset(ENV_OVERRIDES) | SECRET_ENV_VARS | mutated | frozenset({CONFIG_PATH_ENV})
    assert EVIDENCE_ROOT_ENV not in recomputed
    assert "DISCLOSURE_DRIFT_NOT_A_REAL_SETTING" not in recomputed
    assert "DISCLOSURE_DRIFT_NOT_A_REAL_SETTING" not in RECOGNIZED_ENV_VARS


def test_the_evidence_root_is_not_filtered_out_at_cli_dispatch() -> None:
    """**R80** item 7: a command-local bypass is prohibited, so no command may delete it.

    Asserted against ``cli.py``'s own source, because the prohibited implementation is a
    specific one — filtering or deleting the variable from the environment mapping at
    dispatch — and its absence is exactly what makes the central contract load-bearing.
    """
    import disclosure_drift.cli as cli_module

    source = Path(cli_module.__file__).read_text(encoding="utf-8")
    assert EVIDENCE_ROOT_ENV not in source
    assert "EVIDENCE_ROOT_ENV" not in source


def test_data_root_override(config_file: Path) -> None:
    config = load_config(config_file, env={"DISCLOSURE_DRIFT_DATA_ROOT": "./elsewhere"})
    assert config.paths.data_root == Path("./elsewhere")


def test_absolute_data_root_override_is_allowed(config_file: Path, tmp_path: Path) -> None:
    absolute = tmp_path / "corpus"
    config = load_config(config_file, env={"DISCLOSURE_DRIFT_DATA_ROOT": str(absolute)})
    assert config.paths.data_root == absolute
    assert config.paths.data_root.is_absolute()


def test_log_directory_and_level_overrides(config_file: Path, tmp_path: Path) -> None:
    log_dir = tmp_path / "dd-logs"
    config = load_config(
        config_file,
        env={
            "DISCLOSURE_DRIFT_LOG_DIR": str(log_dir),
            "DISCLOSURE_DRIFT_LOG_LEVEL": "DEBUG",
        },
    )
    assert config.paths.log_dir == log_dir
    assert config.logging.level == "DEBUG"


@pytest.mark.parametrize("token", ["true", "TRUE", "1", "yes", "on"])
def test_to_file_true_tokens(config_file: Path, token: str) -> None:
    config = load_config(config_file, env={"DISCLOSURE_DRIFT_LOG_TO_FILE": token})
    assert config.logging.to_file is True


@pytest.mark.parametrize("token", ["false", "FALSE", "0", "no", "off"])
def test_to_file_false_tokens(config_file: Path, token: str) -> None:
    config = load_config(config_file, env={"DISCLOSURE_DRIFT_LOG_TO_FILE": token})
    assert config.logging.to_file is False


def test_to_file_invalid_token_is_actionable(config_file: Path) -> None:
    with pytest.raises(ConfigValidationError, match="is not a boolean") as excinfo:
        load_config(config_file, env={"DISCLOSURE_DRIFT_LOG_TO_FILE": "maybe"})
    assert "DISCLOSURE_DRIFT_LOG_TO_FILE" in str(excinfo.value)


def test_config_path_environment_variable(config_file: Path) -> None:
    config = load_config(env={CONFIG_PATH_ENV: str(config_file)})
    assert config.config_path == config_file


def test_secret_variable_does_not_raise_and_changes_no_value(config_file: Path) -> None:
    env = {SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT}
    baseline = load_config(config_file, env={})
    config = load_config(config_file, env=env)
    without_path = {"config_path"}

    assert config.model_dump(exclude=without_path) == baseline.model_dump(exclude=without_path)
    assert config.resolve_sec_user_agent(env) == EXAMPLE_USER_AGENT
    assert EXAMPLE_USER_AGENT not in repr(config)


@pytest.mark.parametrize(
    "variable",
    [
        "DISCLOSURE_DRIFT_COHORTS",
        "DISCLOSURE_DRIFT_COHORT_DEVELOPMENT_START",
        "DISCLOSURE_DRIFT_PRIMARY_TEST_END",
        "DISCLOSURE_DRIFT_BOOTSTRAP_SEED",
        "DISCLOSURE_DRIFT_PROSPECTIVE_OUTCOME_CUTOFF",
        "DISCLOSURE_DRIFT_DATA_ROOTT",
    ],
)
def test_unknown_variables_are_rejected(config_file: Path, variable: str) -> None:
    with pytest.raises(UnknownEnvironmentOverrideError) as excinfo:
        load_config(config_file, env={variable: "2011-01-01"})
    message = str(excinfo.value)
    assert variable in message
    assert "frozen research definitions" in message


def test_frozen_values_survive_every_allowlisted_override(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    tmp_path: Path,
) -> None:
    path = write_config(frozen_mapping)
    env = {
        "DISCLOSURE_DRIFT_DATA_ROOT": str(tmp_path / "data"),
        "DISCLOSURE_DRIFT_LOG_DIR": str(tmp_path / "logs"),
        "DISCLOSURE_DRIFT_LOG_LEVEL": "ERROR",
        "DISCLOSURE_DRIFT_LOG_TO_FILE": "true",
        SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT,
    }
    config = load_config(path, env=env)
    baseline = load_config(path, env={})
    assert config.cohorts == baseline.cohorts
    assert config.gates == baseline.gates
    assert config.seeds == baseline.seeds
