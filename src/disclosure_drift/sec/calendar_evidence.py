"""Versioned manifest of date-specific EDGAR calendar evidence (Decision 011 §8).

An announcement is retrievable only by its ``evidence_id`` in this manifest. There is
no arbitrary-URL escape hatch: :func:`require_evidence` refuses an unknown identifier,
and :func:`validate_manifest` refuses an entry that is not on an approved SEC host,
carries no affected dates, or asserts a status without an official source URL.

The manifest deliberately ships **without date assertions**. No date may be recorded as
operating or closed from memory; entries are added only after the corresponding
official SEC evidence has been retrieved as an immutable observation and reviewed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "APPROVED_SEC_HOSTS",
    "CALENDAR_EVIDENCE_MANIFEST",
    "CALENDAR_EVIDENCE_MANIFEST_VERSION",
    "CalendarEvidenceEntry",
    "CalendarEvidenceError",
    "EvidenceReviewStatus",
    "EvidenceType",
    "approved_entries",
    "entries_for_date",
    "require_evidence",
    "validate_manifest",
]

CALENDAR_EVIDENCE_MANIFEST_VERSION: Final = "edgar-calendar-evidence/1.0"

APPROVED_SEC_HOSTS: Final[tuple[str, ...]] = ("https://www.sec.gov/", "https://data.sec.gov/")

EvidenceType = Literal[
    "date_specific_announcement",
    "annual_calendar_snapshot",
    "general_operating_rule",
    "positive_activity",
]
AssertedStatus = Literal["operating", "non_operating"]
EvidenceReviewStatus = Literal["pending_retrieval", "pending_review", "approved", "rejected"]


class CalendarEvidenceError(DisclosureDriftError):
    """Raised when calendar evidence is unregistered, unapproved, or malformed."""


@dataclass(frozen=True, slots=True)
class CalendarEvidenceEntry:
    """One reviewed piece of date-specific calendar evidence."""

    evidence_id: str
    url: str
    evidence_type: EvidenceType
    asserted_status: AssertedStatus
    affected_dates: tuple[date, ...]
    title: str
    parser_version: str
    review_status: EvidenceReviewStatus
    published_on: date | None = None
    source_observation_id: str | None = None
    affected_range_start: date | None = None
    affected_range_end: date | None = None
    notes: str | None = None

    @property
    def is_approved(self) -> bool:
        """Only an approved entry with a recorded observation supplies a determination."""
        return self.review_status == "approved" and bool(self.source_observation_id)

    def covers(self, day: date) -> bool:
        """Whether this entry asserts a status for ``day``."""
        if day in self.affected_dates:
            return True
        start, end = self.affected_range_start, self.affected_range_end
        return start is not None and end is not None and start <= day <= end

    def dates(self) -> tuple[date, ...]:
        """Return every date this entry asserts, expanding any range."""
        if self.affected_range_start is None or self.affected_range_end is None:
            return self.affected_dates
        expanded = list(self.affected_dates)
        current = self.affected_range_start
        while current <= self.affected_range_end:
            if current not in expanded:
                expanded.append(current)
            current = date.fromordinal(current.toordinal() + 1)
        return tuple(sorted(expanded))


_ENTRIES: Final[tuple[CalendarEvidenceEntry, ...]] = ()
"""No date assertions ship in source control (Decision 011 section 8).

Entries are appended after the official SEC evidence has been retrieved, stored as an
immutable observation, and reviewed. Until then the derivation reports ``unknown``
for the affected dates rather than assuming a status.
"""

CALENDAR_EVIDENCE_MANIFEST: Final[Mapping[str, CalendarEvidenceEntry]] = MappingProxyType(
    {entry.evidence_id: entry for entry in _ENTRIES}
)


def require_evidence(evidence_id: str) -> CalendarEvidenceEntry:
    """Return a manifest entry, or refuse.

    Raises:
        CalendarEvidenceError: the identifier is not in the reviewed manifest.
    """
    try:
        return CALENDAR_EVIDENCE_MANIFEST[evidence_id]
    except KeyError:
        message = (
            f"calendar evidence {evidence_id!r} is not in the reviewed manifest "
            f"({CALENDAR_EVIDENCE_MANIFEST_VERSION})\n"
            "Fix: add the official SEC announcement to "
            "src/disclosure_drift/sec/calendar_evidence.py with its exact URL, affected "
            "dates, and review status. Arbitrary URLs are not retrievable."
        )
        raise CalendarEvidenceError(message) from None


def approved_entries() -> tuple[CalendarEvidenceEntry, ...]:
    """Return only entries that are approved and tied to an observation."""
    return tuple(entry for entry in _ENTRIES if entry.is_approved)


def entries_for_date(day: date) -> tuple[CalendarEvidenceEntry, ...]:
    """Return approved entries asserting a status for ``day``."""
    return tuple(entry for entry in approved_entries() if entry.covers(day))


def validate_manifest(entries: Sequence[CalendarEvidenceEntry] = _ENTRIES) -> None:
    """Assert manifest invariants.

    Raises:
        CalendarEvidenceError: an entry is malformed or not on an approved SEC host.
    """
    seen: set[str] = set()
    for entry in entries:
        if entry.evidence_id in seen:
            message = f"duplicate calendar evidence identifier {entry.evidence_id!r}"
            raise CalendarEvidenceError(message)
        seen.add(entry.evidence_id)
        if not entry.url.startswith(APPROVED_SEC_HOSTS):
            message = (
                f"calendar evidence {entry.evidence_id!r} is not on an approved SEC host: "
                f"{entry.url}"
            )
            raise CalendarEvidenceError(message)
        if not entry.dates():
            message = f"calendar evidence {entry.evidence_id!r} names no affected date"
            raise CalendarEvidenceError(message)
        if not entry.title.strip():
            message = f"calendar evidence {entry.evidence_id!r} needs the official title"
            raise CalendarEvidenceError(message)
        if "/" not in entry.parser_version:
            message = f"calendar evidence {entry.evidence_id!r} needs a versioned parser id"
            raise CalendarEvidenceError(message)
        if entry.review_status == "approved" and not entry.source_observation_id:
            message = (
                f"calendar evidence {entry.evidence_id!r} cannot be approved without a "
                "source-observation identifier"
            )
            raise CalendarEvidenceError(message)


validate_manifest()
