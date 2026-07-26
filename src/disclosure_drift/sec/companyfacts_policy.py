"""CompanyFacts and Frames guards (Decision 007, assignment section 9).

CompanyFacts is disabled by default and permitted only for a documented
reconciliation or QA need. It may never construct outcomes or silently fill
historical facts. The full-archive download path does not exist in this code base,
and the Frames API is prohibited for point-in-time construction.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "REQUIRED_FACT_PROVENANCE_FIELDS",
    "CompanyFactsAuthorization",
    "CompanyFactsProhibitedError",
    "fact_is_eligible_for_history",
    "require_companyfacts_authorization",
    "require_frames_prohibited",
]

REQUIRED_FACT_PROVENANCE_FIELDS: Final[tuple[str, ...]] = (
    "snapshot_id",
    "retrieval_timestamp",
    "namespace",
    "concept",
    "unit",
    "value",
    "financial_period",
    "accession",
    "form",
    "filed_date",
    "fiscal_year",
    "fiscal_period",
    "frame",
    "source_payload_checksum",
)
"""Provenance a CompanyFacts observation must retain to be usable at all."""


class CompanyFactsProhibitedError(DisclosureDriftError):
    """Raised when CompanyFacts or Frames use is not permitted."""


@dataclass(frozen=True, slots=True)
class CompanyFactsAuthorization:
    """A documented, approved reconciliation need."""

    enabled: bool
    documented_need: str | None
    approved_by: str | None

    def require(self) -> None:
        """Raise unless CompanyFacts use is enabled and documented.

        Raises:
            CompanyFactsProhibitedError: use is disabled, undocumented, or unapproved.
        """
        if not self.enabled:
            message = (
                "CompanyFacts is disabled by default in Milestone 2.\n"
                "Fix: present a specific reconciliation or QA need for approval before enabling it."
            )
            raise CompanyFactsProhibitedError(message)
        if not (self.documented_need and self.documented_need.strip()):
            message = "CompanyFacts use requires a documented reconciliation or QA need"
            raise CompanyFactsProhibitedError(message)
        if not (self.approved_by and self.approved_by.strip()):
            message = "CompanyFacts use requires a recorded approver"
            raise CompanyFactsProhibitedError(message)


def require_companyfacts_authorization(
    enabled: bool,
    documented_need: str | None = None,
    approved_by: str | None = None,
) -> CompanyFactsAuthorization:
    """Validate and return a CompanyFacts authorization."""
    authorization = CompanyFactsAuthorization(enabled, documented_need, approved_by)
    authorization.require()
    return authorization


def require_frames_prohibited() -> None:
    """Always raise. The Frames API may not be used for historical construction."""
    message = (
        "the SEC Frames API is prohibited for historical point-in-time construction "
        "(Decision 007 section 2)"
    )
    raise CompanyFactsProhibitedError(message)


def fact_is_eligible_for_history(fact: Mapping[str, object]) -> tuple[bool, tuple[str, ...]]:
    """Return eligibility and any missing provenance fields.

    A CompanyFacts value without resolved accession provenance is never eligible
    for historical feature or outcome construction.
    """
    missing = tuple(
        name
        for name in REQUIRED_FACT_PROVENANCE_FIELDS
        if name not in fact or fact[name] in (None, "")
    )
    return (not missing), missing
