"""Canonical SEC source addressing (Decision 007 section 2).

URL construction only. No module here performs a request. Prohibited sources
raise rather than returning a URL, so a disallowed source cannot be reached even
by accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.sec.identifiers import cik_padded, parse_accession

__all__ = [
    "APPROVED_SOURCE_PRECEDENCE",
    "PROHIBITED_SOURCES",
    "ProhibitedSourceError",
    "SourceRef",
    "accession_index_html_url",
    "accession_index_json_url",
    "bulk_submissions_url",
    "companyfacts_url",
    "complete_submission_url",
    "master_index_url",
    "submissions_json_url",
]

_ARCHIVES: Final = "https://www.sec.gov/Archives/edgar"
_DATA: Final = "https://data.sec.gov"
_BULK: Final = "https://www.sec.gov/Archives/edgar/daily-index/bulkdata"

SourceClass = Literal[
    "bulk_submissions",
    "master_index",
    "submissions_json",
    "accession_package",
    "complete_submission",
    "xbrl",
    "companyfacts",
    "ticker_alias",
]

APPROVED_SOURCE_PRECEDENCE: Final[tuple[SourceClass, ...]] = (
    "bulk_submissions",
    "master_index",
    "submissions_json",
    "accession_package",
    "complete_submission",
    "xbrl",
    "companyfacts",
    "ticker_alias",
)
"""Approved hierarchy, strongest first. CompanyFacts is reconciliation-only."""

PROHIBITED_SOURCES: Final[frozenset[str]] = frozenset(
    {
        "frames_api",
        "current_exchange_membership",
        "current_ticker_universe",
        "third_party_company_universe",
    }
)


class ProhibitedSourceError(DisclosureDriftError):
    """Raised when a prohibited source is requested."""


@dataclass(frozen=True, slots=True)
class SourceRef:
    """A canonical SEC URL and its source class."""

    source_class: SourceClass
    url: str
    logical_role: str


def _guard(name: str) -> None:
    if name in PROHIBITED_SOURCES:
        message = (
            f"source {name!r} is prohibited by Decision 007 section 2 and may not be used for "
            "universe construction or point-in-time features"
        )
        raise ProhibitedSourceError(message)


def bulk_submissions_url() -> SourceRef:
    """Bulk Submissions archive."""
    return SourceRef("bulk_submissions", f"{_BULK}/submissions.zip", "bulk_archive")


def master_index_url(year: int, quarter: int) -> SourceRef:
    """Quarterly EDGAR master index."""
    if not 1993 <= year <= 2100:
        message = f"year {year} is outside the supported range"
        raise ValueError(message)
    if quarter not in {1, 2, 3, 4}:
        message = f"quarter must be 1-4, received {quarter}"
        raise ValueError(message)
    return SourceRef(
        "master_index",
        f"{_ARCHIVES}/full-index/{year}/QTR{quarter}/master.idx",
        "master_index",
    )


def submissions_json_url(cik: str | int) -> SourceRef:
    """Per-CIK Submissions JSON."""
    return SourceRef(
        "submissions_json",
        f"{_DATA}/submissions/CIK{cik_padded(cik)}.json",
        "submissions_json",
    )


def accession_index_json_url(cik: str | int, accession: str) -> SourceRef:
    """Accession index JSON."""
    parsed = parse_accession(accession)
    return SourceRef(
        "accession_package",
        f"{_ARCHIVES}/data/{int(cik_padded(cik))}/{parsed.plain}/index.json",
        "index_json",
    )


def accession_index_html_url(cik: str | int, accession: str) -> SourceRef:
    """Accession index HTML."""
    parsed = parse_accession(accession)
    return SourceRef(
        "accession_package",
        f"{_ARCHIVES}/data/{int(cik_padded(cik))}/{parsed.plain}/{parsed.dashed}-index.htm",
        "index_html",
    )


def complete_submission_url(cik: str | int, accession: str) -> SourceRef:
    """Complete submission text file, which carries the SGML header."""
    parsed = parse_accession(accession)
    return SourceRef(
        "complete_submission",
        f"{_ARCHIVES}/data/{int(cik_padded(cik))}/{parsed.plain}/{parsed.dashed}.txt",
        "complete_submission",
    )


def companyfacts_url(cik: str | int) -> SourceRef:
    """CompanyFacts endpoint.

    Reconciliation and QA only, and disabled by default. See
    :mod:`disclosure_drift.sec.companyfacts_policy`.
    """
    _guard("frames_api")
    return SourceRef(
        "companyfacts",
        f"{_DATA}/api/xbrl/companyfacts/CIK{cik_padded(cik)}.json",
        "companyfacts",
    )
