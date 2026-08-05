"""Typed configuration loading for the Disclosure Drift foundation.

The loader runs four explicit stages:

1. read ``configs/project.yaml`` with :func:`yaml.safe_load`;
2. merge **only** the explicitly permitted environment overrides;
3. validate through Pydantic v2 models that forbid unknown fields;
4. hard-fail when the file disagrees with the frozen definitions in
   :mod:`disclosure_drift.cohorts`.

Cohort windows, maturity gates, and the bootstrap seed are frozen research
definitions. They are deliberately absent from the override allowlist, so no
environment variable can change them.

``DISCLOSURE_DRIFT_SEC_USER_AGENT`` is a *recognized secret* variable: it never
becomes an ordinary configuration override, it never appears in a model, a
repr, a log record, or CLI output, and it is resolved on demand only.

This module performs no network access and imports no HTTP client.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from disclosure_drift.cohorts import (
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
    FROZEN_SOURCE_RECORDS,
)
from disclosure_drift.errors import NetworkDisabledError, SecUserAgentError
from disclosure_drift.paths import BackupRootStatus, DataTree, backup_root_status

__all__ = [
    "BACKUP_ROOT_ENV",
    "CONFIG_PATH_ENV",
    "ENV_OVERRIDES",
    "ENV_PREFIX",
    "FROZEN_CONFIG_SECTIONS",
    "PLACEHOLDER_CONTACT_DOMAINS",
    "RECOGNIZED_ENV_VARS",
    "RUNTIME_ROOT_ENV_VARS",
    "SECRET_ENV_VARS",
    "SEC_USER_AGENT_ENV",
    "CompanyFactsSection",
    "ConfigError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "FrozenDefinitionMismatchError",
    "NetworkSection",
    "ProjectConfig",
    "UnknownEnvironmentOverrideError",
    "default_config_path",
    "load_config",
    "validate_sec_user_agent",
]


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class ConfigError(Exception):
    """Base class for every configuration failure raised by this package."""


class ConfigFileNotFoundError(ConfigError):
    """Raised when the requested configuration file does not exist."""


class ConfigValidationError(ConfigError):
    """Raised when configuration content is missing, malformed, or out of range."""


class UnknownEnvironmentOverrideError(ConfigError):
    """Raised when an unrecognized ``DISCLOSURE_DRIFT_*`` variable is present."""


class FrozenDefinitionMismatchError(ConfigError):
    """Raised when the configuration file disagrees with a frozen definition."""


# --------------------------------------------------------------------------- #
# Environment contract
# --------------------------------------------------------------------------- #
ENV_PREFIX: Final = "DISCLOSURE_DRIFT_"
CONFIG_PATH_ENV: Final = "DISCLOSURE_DRIFT_CONFIG"
SEC_USER_AGENT_ENV: Final = "DISCLOSURE_DRIFT_SEC_USER_AGENT"

BACKUP_ROOT_ENV: Final = "DISCLOSURE_DRIFT_BACKUP_ROOT"

SECRET_ENV_VARS: Final[frozenset[str]] = frozenset({SEC_USER_AGENT_ENV})
"""Recognized secret variables: resolved on demand, never stored or logged."""

RUNTIME_ROOT_ENV_VARS: Final[frozenset[str]] = frozenset({BACKUP_ROOT_ENV})
"""Runtime roots that may be absolute machine-local paths and are not config overrides.

The backup root deliberately has no entry in tracked YAML (Decision 009 section 2):
a fabricated relative destination would be worse than an unset one. It may remain
unset during offline work; commands that back up or restore validate it.
"""

ENV_OVERRIDES: Final[Mapping[str, tuple[str, str]]] = MappingProxyType(
    {
        "DISCLOSURE_DRIFT_DATA_ROOT": ("paths", "data_root"),
        "DISCLOSURE_DRIFT_LOG_DIR": ("paths", "log_dir"),
        "DISCLOSURE_DRIFT_LOG_LEVEL": ("logging", "level"),
        "DISCLOSURE_DRIFT_LOG_TO_FILE": ("logging", "to_file"),
    }
)
"""The only environment variables that may change configuration values."""

RECOGNIZED_ENV_VARS: Final[frozenset[str]] = (
    frozenset(ENV_OVERRIDES) | SECRET_ENV_VARS | RUNTIME_ROOT_ENV_VARS | {CONFIG_PATH_ENV}
)
"""Every ``DISCLOSURE_DRIFT_*`` variable this package accepts."""

FROZEN_CONFIG_SECTIONS: Final[frozenset[str]] = frozenset({"cohorts", "gates", "seeds"})
"""Configuration sections mirrored from frozen research definitions."""

DEFAULT_CONFIG_RELATIVE: Final = Path("configs") / "project.yaml"
RESERVED_TOP_LEVEL_KEYS: Final[frozenset[str]] = frozenset({"config_path"})
MACHINE_SPECIFIC_PREFIXES: Final[tuple[str, ...]] = (
    "~",
    "/Users/",
    "/home/",
    "/root/",
    "C:\\Users",
)
_TRUE_TOKENS: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_TOKENS: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
class _Section(BaseModel):
    """Base model: unknown fields are rejected and instances are immutable."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectSection(_Section):
    """Project identity."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class PathsSection(_Section):
    """Filesystem locations. Values may be relative or absolute."""

    data_root: Path
    log_dir: Path


class LoggingSection(_Section):
    """Logging behaviour."""

    level: LogLevel
    to_file: bool
    filename: str = Field(min_length=1)


class SecSection(_Section):
    """SEC client policy (assignment section 6, Decision 009 section 8).

    Default 4 requests per second with a configurable maximum of 8. The published
    SEC ceiling of 10 requests per second is not the project target.
    """

    user_agent_env: str = Field(min_length=1)
    requests_per_second: float = Field(gt=0, le=8)
    max_retries: int = Field(ge=0, le=10)
    burst: int = Field(default=1, ge=1, le=4)
    connect_timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    read_timeout_seconds: float = Field(default=60.0, gt=0, le=600)
    bulk_read_timeout_seconds: float = Field(default=180.0, gt=0, le=1800)
    backoff_ceiling_seconds: float = Field(default=60.0, gt=0, le=600)
    cooldown_seconds: float = Field(default=600.0, ge=600, le=7200)

    @field_validator("user_agent_env")
    @classmethod
    def _must_be_recognized_secret(cls, value: str) -> str:
        if value not in SECRET_ENV_VARS:
            recognized = ", ".join(sorted(SECRET_ENV_VARS))
            message = (
                f"must name a recognized secret variable ({recognized}); "
                "the user-agent value itself is never stored in configuration"
            )
            raise ValueError(message)
        return value


class NetworkSection(_Section):
    """Network posture. Two independent switches, both disabled by default.

    ``enabled`` is the global kill switch Stage M2.2 requires. ``m3_acquire_enabled`` is the
    command-scoped Milestone 3.2 acquisition switch, read only by ``m3 acquire --live``.

    **Neither field implies the other.** Enabling the global switch grants no acquisition
    permission, and enabling the acquire-scoped switch reaches no Stage M2.2 command. Both are
    ``False`` in the tracked configuration and neither has an environment override; acquisition
    is enabled only in an owner-supplied window-local configuration under a separate per-window
    owner authorization. Being permitted by configuration is never sufficient on its own: the
    acquisition command additionally requires its own explicit flag and every later gate.
    """

    enabled: bool = False
    m3_acquire_enabled: bool = False


class CompanyFactsSection(_Section):
    """CompanyFacts posture. Disabled by default; reconciliation and QA only."""

    enabled: bool = False
    documented_need: str | None = None
    approved_by: str | None = None


class CohortWindowSpec(_Section):
    """Mirrored cohort window. Validated against the frozen definitions."""

    start: date
    end: date

    @model_validator(mode="after")
    def _ordered(self) -> CohortWindowSpec:
        if self.start > self.end:
            message = f"start {self.start.isoformat()} is after end {self.end.isoformat()}"
            raise ValueError(message)
        return self


class GatesSection(_Section):
    """Mirrored prospective maturity gates."""

    prospective_outcome_cutoff: date
    monitoring_outcome_cutoff: date


class SeedsSection(_Section):
    """Mirrored deterministic seeds."""

    bootstrap: int


class ProjectConfig(_Section):
    """Fully validated project configuration."""

    project: ProjectSection
    paths: PathsSection
    logging: LoggingSection
    sec: SecSection
    cohorts: dict[str, CohortWindowSpec]
    gates: GatesSection
    seeds: SeedsSection
    config_path: Path
    network: NetworkSection = NetworkSection()
    companyfacts: CompanyFactsSection = CompanyFactsSection()

    def resolve_sec_user_agent(self, env: Mapping[str, str] | None = None) -> str | None:
        """Read the SEC user-agent on demand; return ``None`` when unset or blank.

        The value is never stored on this model and never logged.
        """
        source: Mapping[str, str] = os.environ if env is None else env
        value = source.get(self.sec.user_agent_env)
        if value is None:
            return None
        return value.strip() or None

    def sec_user_agent_is_set(self, env: Mapping[str, str] | None = None) -> bool:
        """Return whether the SEC user-agent variable holds a non-blank value."""
        return self.resolve_sec_user_agent(env) is not None

    def log_file_path(self) -> Path | None:
        """Return the configured log-file path, or ``None`` when file logging is off."""
        if not self.logging.to_file:
            return None
        return self.paths.log_dir / self.logging.filename

    def cohort_names(self) -> tuple[str, ...]:
        """Return cohort names in frozen chronological order."""
        return COHORT_ORDER

    # -- Milestone 2 runtime helpers --------------------------------------- #
    def data_tree(self) -> DataTree:
        """Return the resolved data tree for the configured data root."""
        return DataTree.from_root(self.paths.data_root)

    def backup_root(self, env: Mapping[str, str] | None = None) -> BackupRootStatus:
        """Report the backup-root state; never required for offline work."""
        source: Mapping[str, str] = os.environ if env is None else env
        return backup_root_status(source.get(BACKUP_ROOT_ENV))

    def require_sec_user_agent(self, env: Mapping[str, str] | None = None) -> str:
        """Return a validated SEC contact identity or raise before any request.

        Raises:
            SecUserAgentError: the value is absent, blank, a placeholder, or lacks
                a project identity or an administrative contact.
        """
        return validate_sec_user_agent(
            self.resolve_sec_user_agent(env),
            variable=self.sec.user_agent_env,
        )

    def require_network(self) -> None:
        """Raise unless network access is enabled in configuration.

        Raises:
            NetworkDisabledError: network access is disabled.
        """
        if not self.network.enabled:
            message = (
                "network access is disabled in configuration\n"
                "Fix: enable network.enabled only for an authorized Stage M2.2 metadata "
                "census. The default configuration makes no request."
            )
            raise NetworkDisabledError(message)


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #
PLACEHOLDER_CONTACT_DOMAINS: Final[tuple[str, ...]] = (
    "example.com",
    "example.org",
    "example.net",
    "example.edu",
    ".example",
    ".invalid",
    ".test",
    ".localhost",
)
"""RFC-reserved domains that identify a placeholder rather than a real contact."""

_CONTACT_PATTERN: Final = re.compile(r"[^@\s,;]+@[^@\s,;]+\.[A-Za-z]{2,}")
_IDENTITY_PATTERN: Final = re.compile(r"[A-Za-z]{2,}")


def validate_sec_user_agent(value: str | None, variable: str = SEC_USER_AGENT_ENV) -> str:
    """Validate an SEC contact identity at the network boundary.

    Rejects absent, blank, unchanged-example, and RFC-reserved-placeholder values,
    values with no project or organization identity, and values with no email-like
    administrative contact. No personal-name format and no arbitrary total-length
    threshold are imposed beyond what is needed to reject invalid values.

    The value is returned for immediate use in a request header. Callers must not
    log it, store it, or write it into a manifest.

    Raises:
        SecUserAgentError: the value is unusable.
    """
    fix = (
        f"Fix: export {variable} as your project or organization identity followed by a "
        "real administrative contact address, for example "
        '"Financial Disclosure Drift research@your-institution.edu".'
    )
    if value is None or not value.strip():
        message = f"{variable} is not set or is blank.\n{fix}"
        raise SecUserAgentError(message)

    candidate = " ".join(value.split())
    contact = _CONTACT_PATTERN.search(candidate)
    if contact is None:
        message = f"{variable} contains no email-like administrative contact.\n{fix}"
        raise SecUserAgentError(message)

    address = contact.group(0)
    domain = address.rsplit("@", 1)[-1].lower()
    if domain.endswith(PLACEHOLDER_CONTACT_DOMAINS):
        message = (
            f"{variable} uses the reserved placeholder domain {domain!r}, so it is either the "
            f"unchanged example or an invalid contact.\n{fix}"
        )
        raise SecUserAgentError(message)

    remainder = candidate.replace(address, " ")
    if _IDENTITY_PATTERN.search(remainder) is None:
        message = (
            f"{variable} carries a contact address but no project or organization identity.\n{fix}"
        )
        raise SecUserAgentError(message)

    return candidate


def default_config_path(start: Path | None = None) -> Path:
    """Locate ``configs/project.yaml`` in ``start`` or its parents.

    No absolute path is hardcoded: the search begins at the current working
    directory and walks upwards, so the loader works from any location inside a
    clone without knowing the machine it runs on.
    """
    origin = (start or Path.cwd()).resolve()
    for directory in (origin, *origin.parents):
        candidate = directory / DEFAULT_CONFIG_RELATIVE
        if candidate.is_file():
            return candidate
    return DEFAULT_CONFIG_RELATIVE


def load_config(
    path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ProjectConfig:
    """Load, override, validate, and frozen-check the project configuration.

    Args:
        path: Explicit configuration path. Takes precedence over
            ``DISCLOSURE_DRIFT_CONFIG`` and over the upward search.
        env: Environment mapping to read. Defaults to :data:`os.environ`.

    Raises:
        UnknownEnvironmentOverrideError: an unrecognized ``DISCLOSURE_DRIFT_*``
            variable is set.
        ConfigFileNotFoundError: the configuration file does not exist.
        ConfigValidationError: the content is malformed or out of range.
        FrozenDefinitionMismatchError: the file disagrees with a frozen definition.
    """
    environ: Mapping[str, str] = os.environ if env is None else env
    _reject_unknown_environment_variables(environ)
    resolved = _resolve_config_path(path, environ)
    raw = _load_yaml_mapping(resolved)
    _reject_machine_specific_paths(raw, resolved)
    merged = _apply_env_overrides(raw, environ)
    config = _validate(merged, resolved)
    _enforce_frozen_definitions(config, resolved)
    return config


def _reject_unknown_environment_variables(environ: Mapping[str, str]) -> None:
    unknown = sorted(
        name for name in environ if name.startswith(ENV_PREFIX) and name not in RECOGNIZED_ENV_VARS
    )
    if not unknown:
        return
    recognized = "\n".join(f"  {name}" for name in sorted(RECOGNIZED_ENV_VARS))
    message = (
        f"unrecognized environment variable(s): {', '.join(unknown)}\n"
        f"Recognized {ENV_PREFIX}* variables are:\n{recognized}\n"
        "Fix: unset the variable, or correct the spelling. Cohort windows, maturity "
        "gates, and seeds are frozen research definitions and cannot be overridden "
        "from the environment."
    )
    raise UnknownEnvironmentOverrideError(message)


def _resolve_config_path(path: str | Path | None, environ: Mapping[str, str]) -> Path:
    if path is not None:
        candidate = Path(path)
    elif environ.get(CONFIG_PATH_ENV):
        candidate = Path(environ[CONFIG_PATH_ENV])
    else:
        candidate = default_config_path()
    candidate = candidate.expanduser()
    if not candidate.is_file():
        message = (
            f"configuration file not found: {candidate}\n"
            f"Fix: run from a clone containing {DEFAULT_CONFIG_RELATIVE.as_posix()}, "
            f"pass --config PATH, or set {CONFIG_PATH_ENV}."
        )
        raise ConfigFileNotFoundError(message)
    return candidate


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem dependent
        message = f"could not read configuration file {path}: {exc}"
        raise ConfigValidationError(message) from exc
    try:
        parsed = yaml.safe_load(text)
    except (yaml.YAMLError, ValueError) as exc:
        # ValueError covers scalars that look like dates but are impossible,
        # for example ``2022-13-45``, which PyYAML rejects while constructing.
        message = f"{path} is not valid YAML: {exc}\nFix: correct the YAML syntax."
        raise ConfigValidationError(message) from exc
    if parsed is None:
        message = f"{path} is empty\nFix: restore the project configuration sections."
        raise ConfigValidationError(message)
    if not isinstance(parsed, dict):
        message = (
            f"{path} must contain a top-level mapping, found {type(parsed).__name__}\n"
            "Fix: restore the project configuration sections."
        )
        raise ConfigValidationError(message)
    reserved = sorted(RESERVED_TOP_LEVEL_KEYS.intersection(parsed))
    if reserved:
        message = (
            f"{path} uses reserved top-level key(s): {', '.join(reserved)}\n"
            "Fix: remove them; they are populated by the loader."
        )
        raise ConfigValidationError(message)
    return dict(parsed)


def _reject_machine_specific_paths(raw: Mapping[str, Any], path: Path) -> None:
    """Forbid home-directory paths in the *tracked* configuration file.

    Absolute paths supplied at runtime through an approved environment override
    are allowed; a machine-specific path committed to the repository is not.
    """
    paths_section = raw.get("paths")
    if not isinstance(paths_section, Mapping):
        return
    for key, value in paths_section.items():
        if not isinstance(value, str):
            continue
        if value.startswith(MACHINE_SPECIFIC_PREFIXES):
            override = next(
                (var for var, target in ENV_OVERRIDES.items() if target == ("paths", key)),
                None,
            )
            hint = (
                f" Fix: keep a relative default and set {override} at runtime."
                if override is not None
                else ""
            )
            message = (
                f"{path} sets paths.{key} to the machine-specific path {value!r}\n"
                f"Tracked configuration must not contain a home-directory path.{hint}"
            )
            raise ConfigValidationError(message)


def _apply_env_overrides(
    raw: Mapping[str, Any],
    environ: Mapping[str, str],
) -> dict[str, Any]:
    merged: dict[str, Any] = {
        key: dict(value) if isinstance(value, Mapping) else value for key, value in raw.items()
    }
    for variable, (section, key) in ENV_OVERRIDES.items():
        if variable not in environ:
            continue
        if section in FROZEN_CONFIG_SECTIONS:  # pragma: no cover - guarded by test
            message = f"{variable} targets frozen section {section!r} and must not exist"
            raise AssertionError(message)
        target = merged.setdefault(section, {})
        if not isinstance(target, dict):
            message = (
                f"cannot apply {variable}: configuration section {section!r} is not a mapping\n"
                "Fix: restore the section in the configuration file."
            )
            raise ConfigValidationError(message)
        raw_value = environ[variable]
        target[key] = _coerce_bool(raw_value, variable) if key == "to_file" else raw_value
    return merged


def _coerce_bool(value: str, variable: str) -> bool:
    token = value.strip().lower()
    if token in _TRUE_TOKENS:
        return True
    if token in _FALSE_TOKENS:
        return False
    accepted = ", ".join(sorted(_TRUE_TOKENS | _FALSE_TOKENS))
    message = f"{variable}={value!r} is not a boolean\nFix: use one of: {accepted}."
    raise ConfigValidationError(message)


def _validate(merged: Mapping[str, Any], path: Path) -> ProjectConfig:
    try:
        return ProjectConfig.model_validate({**merged, "config_path": path})
    except ValidationError as exc:
        raise ConfigValidationError(_format_validation_error(exc, path)) from exc


def _format_validation_error(exc: ValidationError, path: Path) -> str:
    lines = [f"{path} failed validation:"]
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"]) or "<root>"
        detail = error["msg"]
        if error["type"] == "extra_forbidden":
            detail = "unknown field is not permitted"
        received = error.get("input")
        suffix = "" if received is None else f" (received {received!r})"
        lines.append(f"  {location}: {detail}{suffix}")
    lines.append(f"Fix: correct the listed field(s) in {path}.")
    return "\n".join(lines)


def _enforce_frozen_definitions(config: ProjectConfig, path: Path) -> None:
    mismatches: list[str] = []

    configured = set(config.cohorts)
    expected = set(FROZEN_COHORTS)
    if configured != expected:
        missing = sorted(expected - configured)
        unexpected = sorted(configured - expected)
        if missing:
            mismatches.append(f"cohorts: missing {', '.join(missing)}")
        if unexpected:
            mismatches.append(f"cohorts: unexpected {', '.join(unexpected)}")

    for name in COHORT_ORDER:
        spec = config.cohorts.get(name)
        if spec is None:
            continue
        frozen = FROZEN_COHORTS[name]
        for bound in ("start", "end"):
            found: date = getattr(spec, bound)
            wanted: date = getattr(frozen, bound)
            if found != wanted:
                mismatches.append(
                    f"cohorts.{name}.{bound}: configuration {found.isoformat()}, "
                    f"frozen {wanted.isoformat()}"
                )

    for gate, wanted_date in FROZEN_MATURITY_GATES.items():
        found_date: date = getattr(config.gates, gate)
        if found_date != wanted_date:
            mismatches.append(
                f"gates.{gate}: configuration {found_date.isoformat()}, "
                f"frozen {wanted_date.isoformat()}"
            )

    if config.seeds.bootstrap != FROZEN_BOOTSTRAP_SEED:
        mismatches.append(
            f"seeds.bootstrap: configuration {config.seeds.bootstrap}, "
            f"frozen {FROZEN_BOOTSTRAP_SEED}"
        )

    if not mismatches:
        return

    records = "\n".join(f"  {record}" for record in FROZEN_SOURCE_RECORDS)
    message = (
        f"{path} disagrees with the frozen research definitions in "
        "disclosure_drift.cohorts:\n"
        + "\n".join(f"  {item}" for item in mismatches)
        + "\nThe code constants are canonical. Fix: restore the configuration file to "
        "mirror them. Changing a frozen definition requires an approved decision "
        "record and a reviewed code change.\nGoverning records:\n" + records
    )
    raise FrozenDefinitionMismatchError(message)
