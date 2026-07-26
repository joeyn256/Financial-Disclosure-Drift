"""Invalid-configuration handling and error-message quality."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.config import (
    ConfigFileNotFoundError,
    ConfigValidationError,
    load_config,
)


def _without(mapping: dict[str, Any], section: str, key: str) -> dict[str, Any]:
    return {**mapping, section: {k: v for k, v in mapping[section].items() if k != key}}


def _with(mapping: dict[str, Any], section: str, key: str, value: Any) -> dict[str, Any]:
    return {**mapping, section: {**mapping[section], key: value}}


def test_missing_file_is_actionable(tmp_path: Path) -> None:
    missing = tmp_path / "absent.yaml"
    with pytest.raises(ConfigFileNotFoundError) as excinfo:
        load_config(missing, env={})
    message = str(excinfo.value)
    assert "configuration file not found" in message
    assert "--config" in message


def test_malformed_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "broken.yaml"
    path.write_text("project: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="not valid YAML"):
        load_config(path, env={})


def test_empty_file_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="is empty"):
        load_config(path, env={})


def test_non_mapping_document_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "list.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="top-level mapping"):
        load_config(path, env={})


def test_missing_required_key_names_the_field(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    path = write_config(_without(frozen_mapping, "paths", "data_root"))
    with pytest.raises(ConfigValidationError) as excinfo:
        load_config(path, env={})
    message = str(excinfo.value)
    assert "paths.data_root" in message
    assert "Fix:" in message


def test_unknown_field_is_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    path = write_config(_with(frozen_mapping, "logging", "colour", "green"))
    with pytest.raises(ConfigValidationError) as excinfo:
        load_config(path, env={})
    message = str(excinfo.value)
    assert "logging.colour" in message
    assert "unknown field is not permitted" in message


def test_unknown_top_level_section_is_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    path = write_config({**frozen_mapping, "modelling": {"family": "S"}})
    with pytest.raises(ConfigValidationError, match="modelling"):
        load_config(path, env={})


@pytest.mark.parametrize(
    ("section", "key", "value", "expected"),
    [
        ("logging", "level", "CHATTY", "logging.level"),
        ("logging", "to_file", "sometimes", "logging.to_file"),
        ("logging", "filename", "", "logging.filename"),
        ("sec", "requests_per_second", 0, "sec.requests_per_second"),
        ("sec", "requests_per_second", -1.5, "sec.requests_per_second"),
        ("sec", "requests_per_second", 9.0, "sec.requests_per_second"),
        ("sec", "requests_per_second", 25, "sec.requests_per_second"),
        ("sec", "burst", 0, "sec.burst"),
        ("sec", "cooldown_seconds", 60, "sec.cooldown_seconds"),
        ("sec", "max_retries", -1, "sec.max_retries"),
        ("sec", "user_agent_env", "SOME_OTHER_VARIABLE", "sec.user_agent_env"),
        ("project", "name", "", "project.name"),
        ("seeds", "bootstrap", "not-an-int", "seeds.bootstrap"),
    ],
)
def test_out_of_range_values_are_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    section: str,
    key: str,
    value: Any,
    expected: str,
) -> None:
    path = write_config(_with(frozen_mapping, section, key, value))
    with pytest.raises(ConfigValidationError) as excinfo:
        load_config(path, env={})
    assert expected in str(excinfo.value)


def test_reversed_cohort_window_is_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    cohorts = {name: dict(window) for name, window in frozen_mapping["cohorts"].items()}
    cohorts["development"] = {
        "start": cohorts["development"]["end"],
        "end": cohorts["development"]["start"],
    }
    path = write_config({**frozen_mapping, "cohorts": cohorts})
    with pytest.raises(ConfigValidationError) as excinfo:
        load_config(path, env={})
    assert "is after end" in str(excinfo.value)


def test_unparseable_date_names_the_field(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    cohorts = {name: dict(window) for name, window in frozen_mapping["cohorts"].items()}
    cohorts["transition"]["start"] = "first quarter"
    path = write_config({**frozen_mapping, "cohorts": cohorts})
    with pytest.raises(ConfigValidationError, match="cohorts.transition.start"):
        load_config(path, env={})


def test_impossible_date_literal_is_reported_as_invalid_yaml(tmp_path: Path) -> None:
    """PyYAML raises ValueError, not YAMLError, for a date like ``2022-13-45``."""
    path = tmp_path / "impossible.yaml"
    path.write_text("cohorts:\n  transition:\n    start: 2022-13-45\n", encoding="utf-8")
    with pytest.raises(ConfigValidationError, match="not valid YAML"):
        load_config(path, env={})


@pytest.mark.parametrize(
    "value",
    # hygiene-scan: allow - synthetic paths that must be rejected by the loader
    ["/Users/someone/Projects/data", "/home/someone/data", "~/Projects/data", "/root/data"],
)
def test_machine_specific_path_in_file_is_rejected(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    value: str,
) -> None:
    path = write_config(_with(frozen_mapping, "paths", "data_root", value))
    with pytest.raises(ConfigValidationError) as excinfo:
        load_config(path, env={})
    message = str(excinfo.value)
    assert "machine-specific" in message
    assert "DISCLOSURE_DRIFT_DATA_ROOT" in message
