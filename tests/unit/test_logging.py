"""Logging initialization, file output, and secret redaction."""

from __future__ import annotations

import io
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from disclosure_drift.config import SEC_USER_AGENT_ENV, load_config
from disclosure_drift.logging_config import (
    PACKAGE_LOGGER,
    REDACTION_PLACEHOLDER,
    configure_logging,
    get_logger,
)

EXAMPLE_USER_AGENT = "Example Researcher researcher@example.com"


def test_console_logging_is_configured(config_file: Path) -> None:
    config = load_config(config_file, env={})
    stream = io.StringIO()
    logger = configure_logging(config, stream=stream, env={})

    assert logger.name == PACKAGE_LOGGER
    assert logger.level == logging.INFO
    assert logger.propagate is False
    assert len(logger.handlers) == 1

    logger.info("foundation ready")
    output = stream.getvalue()
    assert "foundation ready" in output
    assert "INFO" in output
    assert PACKAGE_LOGGER in output
    assert output.startswith("20")  # ISO timestamp


def test_configuration_is_idempotent(config_file: Path) -> None:
    config = load_config(config_file, env={})
    first = configure_logging(config, stream=io.StringIO(), env={})
    second = configure_logging(config, stream=io.StringIO(), env={})
    assert first is second
    assert len(second.handlers) == 1


def test_log_level_is_honoured(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
) -> None:
    mapping = {**frozen_mapping, "logging": {**frozen_mapping["logging"], "level": "WARNING"}}
    config = load_config(write_config(mapping), env={})
    stream = io.StringIO()
    logger = configure_logging(config, stream=stream, env={})

    logger.info("suppressed")
    logger.warning("surfaced")
    output = stream.getvalue()
    assert "suppressed" not in output
    assert "surfaced" in output


def test_optional_file_output(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    tmp_path: Path,
) -> None:
    log_dir = tmp_path / "nested" / "logs"
    mapping = {
        **frozen_mapping,
        "logging": {**frozen_mapping["logging"], "to_file": True},
    }
    config = load_config(
        write_config(mapping),
        env={"DISCLOSURE_DRIFT_LOG_DIR": str(log_dir)},
    )
    logger = configure_logging(config, stream=io.StringIO(), env={})
    logger.info("written to file")

    for handler in logger.handlers:
        handler.flush()

    log_file = log_dir / "disclosure_drift.log"
    assert log_file.is_file()
    contents = log_file.read_text(encoding="utf-8")
    assert "written to file" in contents


def test_secret_values_are_redacted(config_file: Path) -> None:
    env = {SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT}
    config = load_config(config_file, env=env)
    stream = io.StringIO()
    logger = configure_logging(config, stream=stream, env=env)

    logger.info("contacting SEC as %s", EXAMPLE_USER_AGENT)
    logger.warning("user agent is %s", EXAMPLE_USER_AGENT)

    output = stream.getvalue()
    assert EXAMPLE_USER_AGENT not in output
    assert output.count(REDACTION_PLACEHOLDER) == 2


def test_secret_redaction_reaches_the_file_handler(
    write_config: Callable[..., Path],
    frozen_mapping: dict[str, Any],
    tmp_path: Path,
) -> None:
    mapping = {**frozen_mapping, "logging": {**frozen_mapping["logging"], "to_file": True}}
    env = {
        SEC_USER_AGENT_ENV: EXAMPLE_USER_AGENT,
        "DISCLOSURE_DRIFT_LOG_DIR": str(tmp_path / "logs"),
    }
    config = load_config(write_config(mapping), env=env)
    logger = configure_logging(config, stream=io.StringIO(), env=env)
    logger.error("failed while identifying as %s", EXAMPLE_USER_AGENT)

    for handler in logger.handlers:
        handler.flush()

    contents = (tmp_path / "logs" / "disclosure_drift.log").read_text(encoding="utf-8")
    assert EXAMPLE_USER_AGENT not in contents
    assert REDACTION_PLACEHOLDER in contents


def test_get_logger_returns_package_children() -> None:
    assert get_logger().name == PACKAGE_LOGGER
    assert get_logger(PACKAGE_LOGGER).name == PACKAGE_LOGGER
    assert get_logger("cli").name == f"{PACKAGE_LOGGER}.cli"
