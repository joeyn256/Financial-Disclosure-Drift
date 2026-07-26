"""Structured logging for the Disclosure Drift foundation.

Console output is always configured. File output is optional and controlled by
``logging.to_file`` in ``configs/project.yaml``. Records carry a timestamp, the
logger name, and the level. Values of recognized secret environment variables
are redacted before a record is emitted, so a secret cannot reach a handler even
if a caller interpolates one into a message.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Iterable, Mapping
from typing import IO, Final

from disclosure_drift.config import ProjectConfig

__all__ = [
    "LOG_DATE_FORMAT",
    "LOG_FORMAT",
    "PACKAGE_LOGGER",
    "REDACTION_PLACEHOLDER",
    "SecretRedactingFilter",
    "configure_logging",
    "get_logger",
]

PACKAGE_LOGGER: Final = "disclosure_drift"
LOG_FORMAT: Final = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT: Final = "%Y-%m-%dT%H:%M:%S%z"
REDACTION_PLACEHOLDER: Final = "[REDACTED]"


class SecretRedactingFilter(logging.Filter):
    """Replace known secret values with :data:`REDACTION_PLACEHOLDER`."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        super().__init__()
        self._secrets: tuple[str, ...] = tuple(secret for secret in secrets if secret)

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact secrets in ``record`` and always allow it through."""
        if not self._secrets:
            return True
        message = record.getMessage()
        redacted = message
        for secret in self._secrets:
            redacted = redacted.replace(secret, REDACTION_PLACEHOLDER)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True


def collect_secret_values(
    config: ProjectConfig,
    env: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Return the currently set secret values, resolved on demand."""
    user_agent = config.resolve_sec_user_agent(env)
    return (user_agent,) if user_agent else ()


def configure_logging(
    config: ProjectConfig,
    *,
    stream: IO[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> logging.Logger:
    """Configure and return the package logger.

    Existing handlers are replaced, so repeated calls never duplicate output.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(config.logging.level)
    logger.propagate = False

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)
    redactor = SecretRedactingFilter(collect_secret_values(config, env))

    console = logging.StreamHandler(sys.stderr if stream is None else stream)
    console.setFormatter(formatter)
    console.addFilter(redactor)
    logger.addHandler(console)

    log_file = config.log_file_path()
    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redactor)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child of the package logger, or the package logger itself."""
    if name is None or name == PACKAGE_LOGGER:
        return logging.getLogger(PACKAGE_LOGGER)
    return logging.getLogger(f"{PACKAGE_LOGGER}.{name}")
