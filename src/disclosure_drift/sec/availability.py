"""Public-availability boundaries and the tri-state point-in-time comparison.

Decision 010 sections 5 and 6. The leakage test is

    source_public_availability_boundary <= target_public_availability_boundary

evaluated as ``eligible`` / ``ineligible`` / ``indeterminate``, never as a bare
Boolean. ``indeterminate`` blocks automatic historical use and raises a review
reason; it never asserts that the source was unavailable, and it never passes
silently.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "INDETERMINATE_REASON_CODE",
    "AvailabilityBasis",
    "AvailabilityBoundary",
    "AvailabilityError",
    "AvailabilityPrecision",
    "EligibilityOutcome",
    "EligibilityVerdict",
    "boundary_for",
    "compare_boundaries",
]

AvailabilityPrecision = Literal["timestamp", "date"]
AvailabilityBasis = Literal["same_day_acceptance", "later_official_filing_date", "filing_date_only"]
EligibilityOutcome = Literal["eligible", "ineligible", "indeterminate"]

INDETERMINATE_REASON_CODE: Final = "REVIEW_AVAILABILITY_ORDER_INDETERMINATE"


class AvailabilityError(DisclosureDriftError):
    """Raised when an availability boundary cannot be constructed."""


@dataclass(frozen=True, slots=True)
class AvailabilityBoundary:
    """The approved public-availability boundary for one accession."""

    accession_plain: str
    proxy_date: date
    precision: AvailabilityPrecision
    basis: AvailabilityBasis
    timestamp_et: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the precision and timestamp combination."""
        if self.precision == "timestamp" and self.timestamp_et is None:
            message = "timestamp precision requires an Eastern timestamp"
            raise AvailabilityError(message)
        if self.timestamp_et is not None and self.timestamp_et.tzinfo is None:
            message = "availability timestamps must be timezone aware"
            raise AvailabilityError(message)

    @property
    def is_timestamped(self) -> bool:
        """Whether an exact instant is known."""
        return self.precision == "timestamp" and self.timestamp_et is not None


def boundary_for(
    accession_plain: str,
    official_filing_date: date,
    acceptance_date: date | None,
    acceptance_datetime_et: datetime | None,
) -> AvailabilityBoundary:
    """Build the approved availability boundary for an accession.

    * Same-day acceptance yields ``timestamp`` precision with basis
      ``same_day_acceptance``.
    * A later official filing date yields ``date`` precision with basis
      ``later_official_filing_date``. No exact dissemination timestamp is invented.
    * A missing acceptance value yields ``date`` precision with basis
      ``filing_date_only``.
    """
    if acceptance_date is None or acceptance_datetime_et is None:
        return AvailabilityBoundary(
            accession_plain=accession_plain,
            proxy_date=official_filing_date,
            precision="date",
            basis="filing_date_only",
        )
    if acceptance_date == official_filing_date:
        return AvailabilityBoundary(
            accession_plain=accession_plain,
            proxy_date=official_filing_date,
            precision="timestamp",
            basis="same_day_acceptance",
            timestamp_et=acceptance_datetime_et,
        )
    return AvailabilityBoundary(
        accession_plain=accession_plain,
        proxy_date=official_filing_date,
        precision="date",
        basis="later_official_filing_date",
        timestamp_et=acceptance_datetime_et,
    )


@dataclass(frozen=True, slots=True)
class EligibilityVerdict:
    """Outcome of one boundary comparison."""

    outcome: EligibilityOutcome
    detail: str
    reason_codes: tuple[str, ...] = ()

    @property
    def permits_automatic_use(self) -> bool:
        """Only an ``eligible`` verdict permits automatic historical use."""
        return self.outcome == "eligible"

    @property
    def asserts_unavailability(self) -> bool:
        """Only an ``ineligible`` verdict asserts the source was unavailable."""
        return self.outcome == "ineligible"


def compare_boundaries(
    source: AvailabilityBoundary,
    target: AvailabilityBoundary,
) -> EligibilityVerdict:
    """Compare two availability boundaries as a tri-state outcome.

    Rules, in order:

    1. the target's own filing package is eligible against its own boundary,
       even when that boundary is later than its acceptance timestamp;
    2. two exact timestamps compare directly;
    3. different boundary dates compare by date;
    4. the same boundary date with any date-level precision is ``indeterminate``.
    """
    if source.accession_plain == target.accession_plain:
        return EligibilityVerdict(
            outcome="eligible",
            detail="source is the target accession's own filing package",
        )

    source_instant = source.timestamp_et if source.precision == "timestamp" else None
    target_instant = target.timestamp_et if target.precision == "timestamp" else None
    if source_instant is not None and target_instant is not None:
        if source_instant <= target_instant:
            return EligibilityVerdict(
                outcome="eligible",
                detail="exact source timestamp is at or before the exact target timestamp",
            )
        return EligibilityVerdict(
            outcome="ineligible",
            detail="exact source timestamp is after the exact target timestamp",
        )

    if source.proxy_date < target.proxy_date:
        return EligibilityVerdict(
            outcome="eligible",
            detail="source availability date precedes the target availability date",
        )
    if source.proxy_date > target.proxy_date:
        return EligibilityVerdict(
            outcome="ineligible",
            detail="source availability date follows the target availability date",
        )
    return EligibilityVerdict(
        outcome="indeterminate",
        detail=(
            "both accessions share the availability date "
            f"{target.proxy_date.isoformat()} and at least one boundary is date-level, "
            "so their order cannot be established"
        ),
        reason_codes=(INDETERMINATE_REASON_CODE,),
    )
