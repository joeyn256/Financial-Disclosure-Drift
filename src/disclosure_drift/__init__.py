"""Disclosure Drift — reproducible research foundation.

Milestone 1 provides packaging, typed configuration, logging, an offline CLI,
tests, and CI. It contains no SEC ingestion, no research features, no outcome
construction, and no network access.

``__version__`` is the single canonical version for the project: ``pyproject.toml``
declares the version dynamically and Hatch reads it from this module.
"""

from __future__ import annotations

__version__ = "0.1.0"

from disclosure_drift.cohorts import (  # noqa: E402
    COHORT_ORDER,
    FROZEN_BOOTSTRAP_SEED,
    FROZEN_COHORTS,
    FROZEN_MATURITY_GATES,
    CohortWindow,
    cohort_for,
)
from disclosure_drift.config import (  # noqa: E402
    ConfigError,
    ConfigFileNotFoundError,
    ConfigValidationError,
    FrozenDefinitionMismatchError,
    ProjectConfig,
    UnknownEnvironmentOverrideError,
    load_config,
)
from disclosure_drift.logging_config import configure_logging, get_logger  # noqa: E402

__all__ = [
    "COHORT_ORDER",
    "FROZEN_BOOTSTRAP_SEED",
    "FROZEN_COHORTS",
    "FROZEN_MATURITY_GATES",
    "CohortWindow",
    "ConfigError",
    "ConfigFileNotFoundError",
    "ConfigValidationError",
    "FrozenDefinitionMismatchError",
    "ProjectConfig",
    "UnknownEnvironmentOverrideError",
    "__version__",
    "cohort_for",
    "configure_logging",
    "get_logger",
    "load_config",
]
