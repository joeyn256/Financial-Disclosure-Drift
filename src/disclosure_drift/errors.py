"""Shared exception hierarchy for Disclosure Drift.

Configuration errors defined in :mod:`disclosure_drift.config` predate this module
and are re-exported there for backward compatibility. Every exception raised by
package code should derive from :class:`DisclosureDriftError` so callers and the
CLI can distinguish expected, actionable failures from defects.
"""

from __future__ import annotations

__all__ = [
    "CatalogWriteError",
    "DisclosureDriftError",
    "GateFailureError",
    "NetworkDisabledError",
    "RawObjectIntegrityError",
    "ReviewRequiredError",
    "SchemaDriftError",
    "SecUserAgentError",
    "SingleWriterViolationError",
    "SqliteVersionError",
    "StageNotEnabledError",
]


class DisclosureDriftError(Exception):
    """Base class for every expected, actionable Disclosure Drift failure."""


class NetworkDisabledError(DisclosureDriftError):
    """Raised when a command needs the network and network access is disabled."""


class SecUserAgentError(DisclosureDriftError):
    """Raised when the SEC contact identity is absent, blank, or invalid.

    Raised at the network boundary *before* any request is constructed.
    """


class StageNotEnabledError(DisclosureDriftError):
    """Raised when a command belongs to a milestone stage that is not yet enabled."""


class RawObjectIntegrityError(DisclosureDriftError):
    """Raised when a raw object fails a checksum, size, or content validation gate."""


class CatalogWriteError(DisclosureDriftError):
    """Raised when a catalog write cannot be completed atomically."""


class SingleWriterViolationError(CatalogWriteError):
    """Raised when a second logical writer attempts to write to the catalog."""


class SqliteVersionError(DisclosureDriftError):
    """Raised when the available SQLite runtime is older than the required floor."""


class SchemaDriftError(DisclosureDriftError):
    """Raised when a required SEC field is missing or structurally invalid.

    Unknown *extra* fields are retained and logged; they never raise.
    """


class ReviewRequiredError(DisclosureDriftError):
    """Raised when policy requires human review before automatic processing continues.

    Carries the machine-readable reason codes that describe why review is required,
    so callers can record them without re-deriving the cause from the message.
    """

    def __init__(self, message: str, reason_codes: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.reason_codes = reason_codes


class GateFailureError(DisclosureDriftError):
    """Raised when a release-blocking quality gate fails."""
