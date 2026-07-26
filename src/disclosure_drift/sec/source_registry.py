"""Versioned registry of approved official SEC sources for Stage M2.2.

Every source used by the census is registered here before a parser may touch it.
A registration records the source identifier, the official URL or URL template,
its purpose, retrieval method, expected content type, parser version, governing
decision record, and whether it is bulk, entity-specific, or reference data.

Only SEC-controlled sources appear here. Third-party issuer lists, commercial
APIs, dataset mirrors, encyclopaedias, and remembered reference tables are
prohibited (Decision 007 section 2), and :func:`require_registered` refuses any
identifier that is not registered.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.sec.parsers.versions import PARSER_VERSIONS, parser_version_for

__all__ = [
    "M22_SOURCE_REGISTRY_VERSION",
    "SEC_ORIGINS",
    "SOURCES",
    "ContentKind",
    "RetrievalMethod",
    "SourceCategory",
    "SourceMutability",
    "SourceRegistrationError",
    "SourceSpec",
    "entity_sources",
    "filing_body_url_is_prohibited",
    "reference_sources",
    "require_registered",
    "sources_for_category",
]

M22_SOURCE_REGISTRY_VERSION: Final = "m2.2-source-registry/1.0"

SourceCategory = Literal[
    "registrant_index",
    "submissions",
    "historical_submissions",
    "ticker_exchange_alias",
    "sic_reference",
    "operating_calendar_evidence",
    "calendar_announcement",
]
RetrievalMethod = Literal["bulk_archive", "bulk_document", "entity_document"]
ContentKind = Literal["json", "zip", "html", "text"]
SourceMutability = Literal["living", "dated_snapshot", "immutable"]
"""How a source's content is expected to behave at a stable official identity.

* ``living`` — the dataset is maintained and is expected to change over time. A
  changed body is an ordinary update, not an anomaly.
* ``dated_snapshot`` — the identity embeds a period. Change is ordinary while the
  period is open and is an anomaly once the period has closed.
* ``immutable`` — the identity is expected to name fixed content. Any change is an
  anomaly requiring review.
"""

_D007: Final = "Docs/Decisions/decision_007_sec_universe.md"
_D010: Final = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"
_D011: Final = "Docs/Decisions/decision_011_edgar_operating_calendar_provenance.md"

_SEC_WWW: Final = "https://www.sec.gov"
_SEC_DATA: Final = "https://data.sec.gov"

SEC_ORIGINS: Final[tuple[str, ...]] = (_SEC_WWW, _SEC_DATA)
"""The only origins any registered source, redirect hop, or final URL may use."""


class SourceRegistrationError(DisclosureDriftError):
    """Raised when an unregistered or prohibited source is requested."""


@dataclass(frozen=True, slots=True)
class SourceSpec:
    """One approved official SEC source."""

    source_id: str
    category: SourceCategory
    url_template: str
    purpose: str
    retrieval_method: RetrievalMethod
    expected_content: ContentKind
    parser_id: str
    decision_record: str
    is_bulk: bool
    mutability: SourceMutability = "living"
    expected_parser_version: str | None = None
    supports_conditional_requests: bool = True
    manifest_resolved: bool = False
    notes: str | None = None

    @property
    def parser_version(self) -> str:
        """The authoritative parser version, read from the implementation.

        The registry records which parser is compatible, not what version that parser
        happens to be at. Duplicating the version here is what allowed three sources to
        fall behind their implementations, so it is derived rather than stored.
        """
        return parser_version_for(self.parser_id)

    @property
    def is_entity_specific(self) -> bool:
        """Whether the source addresses a single entity rather than a bulk snapshot."""
        return self.retrieval_method == "entity_document"

    def url(self, **parameters: str) -> str:
        """Render the official URL for this source.

        Raises:
            SourceRegistrationError: a required template parameter is missing.
        """
        try:
            return self.url_template.format(**parameters)
        except KeyError as exc:
            missing = exc.args[0]
            message = (
                f"source {self.source_id!r} requires template parameter {missing!r}\n"
                f"template: {self.url_template}"
            )
            raise SourceRegistrationError(message) from exc


_ALL: Final[tuple[SourceSpec, ...]] = (
    SourceSpec(
        source_id="sec_bulk_submissions",
        category="submissions",
        url_template=f"{_SEC_WWW}/Archives/edgar/daily-index/bulkdata/submissions.zip",
        purpose=(
            "Bulk snapshot of every EDGAR filer's submissions metadata: canonical CIK, "
            "registrant names, former names, tickers, exchanges, SIC, fiscal year end, "
            "and accession-level filing metadata including historical-file references."
        ),
        retrieval_method="bulk_archive",
        expected_content="zip",
        parser_id="submissions-json",
        decision_record=_D007,
        is_bulk=True,
        mutability="living",
        notes="Primary census source. Member entries are per-CIK submissions JSON.",
    ),
    SourceSpec(
        source_id="sec_company_tickers_exchange",
        category="ticker_exchange_alias",
        url_template=f"{_SEC_WWW}/files/company_tickers_exchange.json",
        purpose=(
            "Current ticker and exchange aliases keyed by CIK. Noncanonical aliases "
            "only; never a universe definition."
        ),
        retrieval_method="bulk_document",
        expected_content="json",
        parser_id="company-tickers-exchange",
        decision_record=_D007,
        is_bulk=True,
        mutability="living",
        notes="Alias evidence only, per Decision 007 section 2 item 8.",
    ),
    SourceSpec(
        source_id="sec_company_tickers",
        category="ticker_exchange_alias",
        url_template=f"{_SEC_WWW}/files/company_tickers.json",
        purpose="Current ticker aliases keyed by CIK, used to reconcile the exchange file.",
        retrieval_method="bulk_document",
        expected_content="json",
        parser_id="company-tickers",
        decision_record=_D007,
        is_bulk=True,
        mutability="living",
    ),
    SourceSpec(
        source_id="sec_submissions_entity",
        category="submissions",
        url_template=f"{_SEC_DATA}/submissions/CIK{{cik_padded}}.json",
        purpose=(
            "Per-CIK submissions metadata. Entity-specific retrieval is permitted only "
            "for a controlled reconciliation check or a field absent from the bulk "
            "snapshot, and every request records its purpose."
        ),
        retrieval_method="entity_document",
        expected_content="json",
        parser_id="submissions-json",
        decision_record=_D007,
        is_bulk=False,
        mutability="living",
    ),
    SourceSpec(
        source_id="sec_submissions_historical",
        category="historical_submissions",
        url_template=f"{_SEC_DATA}/submissions/{{historical_file}}",
        purpose=(
            "Historical submissions overflow file referenced by a bulk or entity "
            "submissions document, holding older accessions beyond the recent window."
        ),
        retrieval_method="entity_document",
        expected_content="json",
        parser_id="submissions-historical",
        decision_record=_D007,
        is_bulk=False,
        mutability="living",
        notes=(
            "Retrieved only when an approved source explicitly names the file. Content "
            "changes as accessions age out of the recent window, so it is living."
        ),
    ),
    SourceSpec(
        source_id="sec_sic_code_list",
        category="sic_reference",
        url_template=(
            f"{_SEC_WWW}/corpfin/division-of-corporation-finance-standard-industrial"
            "-classification-sic-code-list"
        ),
        purpose=(
            "Official SEC Division of Corporation Finance SIC code list, the only "
            "permitted source of SIC codes and descriptions."
        ),
        retrieval_method="bulk_document",
        expected_content="html",
        parser_id="sic-code-list",
        decision_record=_D007,
        is_bulk=True,
        mutability="living",
        notes="SIC 6000-6999 rows are retained and flagged, never deleted.",
    ),
    SourceSpec(
        source_id="sec_edgar_filing_calendar",
        category="operating_calendar_evidence",
        url_template=f"{_SEC_WWW}/submit-filings/filer-support-resources/edgar-calendar",
        purpose=(
            "Canonical official EDGAR calendar: listed filing holidays for the year the "
            "preserved snapshot covers, per Decision 011 precedence 2. The older "
            "/edgar/filer-information/calendar path redirects here; redirect history is "
            "validated and recorded one hop at a time by the policy client."
        ),
        retrieval_method="bulk_document",
        expected_content="html",
        parser_id="edgar-calendar",
        decision_record=_D011,
        is_bulk=True,
        mutability="living",
        notes=(
            "No generic holiday library is substituted. Coverage outside the parsed "
            "evidence fails closed. One page never establishes 2009-2026 coverage."
        ),
    ),
    SourceSpec(
        source_id="sec_edgar_calendar_announcement",
        category="calendar_announcement",
        url_template="{announcement_url}",
        purpose=(
            "Exact date-specific SEC EDGAR closure or operating announcement, Decision "
            "011 precedence 1. Retrievable only by an evidence_id in the reviewed "
            "manifest; the URL is supplied by that manifest entry, never by a caller."
        ),
        retrieval_method="bulk_document",
        expected_content="html",
        parser_id="edgar-calendar-announcement",
        decision_record=_D011,
        is_bulk=True,
        mutability="immutable",
        manifest_resolved=True,
        notes=(
            "Not an arbitrary-URL escape hatch: see calendar_evidence.require_evidence. "
            "A dated announcement is immutable, so a changed body is an anomaly."
        ),
    ),
    SourceSpec(
        source_id="sec_full_index_company",
        category="registrant_index",
        url_template=f"{_SEC_WWW}/Archives/edgar/full-index/{{year}}/QTR{{quarter}}/company.idx",
        purpose=(
            "Quarterly EDGAR company index used to reconcile accession coverage by "
            "year and quarter without retrieving any filing body."
        ),
        retrieval_method="bulk_document",
        expected_content="text",
        parser_id="company-idx",
        decision_record=_D007,
        is_bulk=True,
        mutability="dated_snapshot",
        notes=(
            "The identity embeds year and quarter. While the quarter is open the index "
            "grows, which is expected; once the quarter has closed a change is an "
            "anomaly unless an official SEC correction explains it."
        ),
    ),
)

SOURCES: Final[Mapping[str, SourceSpec]] = MappingProxyType(
    {source.source_id: source for source in _ALL}
)
"""Every approved M2.2 source, keyed by identifier."""

PROHIBITED_SOURCE_HINTS: Final[tuple[str, ...]] = (
    "kaggle",
    "github",
    "githubusercontent",
    "wikipedia",
    "webcache",
    "sec-api.io",
    "edgar-online",
    "rapidapi",
    "quandl",
    "bloomberg",
    "refinitiv",
)
"""Substrings that identify a non-SEC source and must never be retrieved."""

_FILING_BODY_MARKERS: Final[tuple[str, ...]] = (
    "/Archives/edgar/data/",
    "-index.htm",
    ".txt",
    ".htm",
    ".xml",
    ".xsd",
)


def require_registered(source_id: str) -> SourceSpec:
    """Return the registered source, or refuse.

    Raises:
        SourceRegistrationError: the identifier is not registered.
    """
    try:
        return SOURCES[source_id]
    except KeyError:
        registered = ", ".join(sorted(SOURCES))
        message = (
            f"source {source_id!r} is not registered for Stage M2.2\n"
            f"Registered sources: {registered}\n"
            "Fix: register the official SEC source with its purpose, parser version, "
            "and decision record before using it. Third-party sources are prohibited."
        )
        raise SourceRegistrationError(message) from None


def sources_for_category(category: SourceCategory) -> tuple[SourceSpec, ...]:
    """Return registered sources in ``category``, in registry order."""
    return tuple(source for source in _ALL if source.category == category)


def reference_sources() -> tuple[SourceSpec, ...]:
    """Return the reference-data sources: SIC codes and calendar evidence."""
    return tuple(
        source
        for source in _ALL
        if source.category in {"sic_reference", "operating_calendar_evidence"}
    )


def entity_sources() -> tuple[SourceSpec, ...]:
    """Return the entity-specific sources, which require a recorded purpose."""
    return tuple(source for source in _ALL if source.is_entity_specific)


def filing_body_url_is_prohibited(url: str) -> bool:
    """Whether ``url`` looks like a filing body or accession package.

    Stage M2.2 retrieves metadata only. The census guard uses this to refuse a
    filing-document URL even if a future parser mistakenly produces one.
    """
    lowered = url.lower()
    if "/archives/edgar/full-index/" in lowered:
        return False
    if "/archives/edgar/daily-index/" in lowered:
        return False
    return any(marker.lower() in lowered for marker in _FILING_BODY_MARKERS)


def _validate_registry() -> None:
    """Assert registry invariants at import time."""
    if len(SOURCES) != len(_ALL):
        message = "duplicate source identifier in the M2.2 registry"
        raise AssertionError(message)
    for source in _ALL:
        _validate_registry_entry(source)


def _validate_registry_entry(source: SourceSpec) -> None:
    """Assert the invariants for one registration, failing closed on any breach.

    Extracted from the import-time loop so the parser-version guards can be exercised on
    a deliberately drifted copy without mutating the real registry.
    """
    if source.manifest_resolved:
        if source.url_template != "{announcement_url}":
            message = (
                f"source {source.source_id!r} is manifest-resolved and must not carry "
                "a literal URL template"
            )
            raise AssertionError(message)
    elif not source.url_template.startswith((_SEC_WWW, _SEC_DATA)):
        message = f"source {source.source_id!r} is not an official SEC URL"
        raise AssertionError(message)
    if any(hint in source.url_template.lower() for hint in PROHIBITED_SOURCE_HINTS):
        message = f"source {source.source_id!r} points at a prohibited host"
        raise AssertionError(message)
    if not source.decision_record.startswith("Docs/"):
        message = f"source {source.source_id!r} must cite a decision record"
        raise AssertionError(message)
    _validate_parser_identity(source)
    if source.is_bulk == source.is_entity_specific:
        message = f"source {source.source_id!r} must be either bulk or entity-specific"
        raise AssertionError(message)


def _validate_parser_identity(source: SourceSpec) -> None:
    """Fail closed when a registration and a parser implementation disagree.

    Two ways to disagree: naming a parser nothing implements, or pinning an expected
    version the implementation has moved past. Both stop the process at import, before
    any ingestion or reuse could record the wrong provenance.
    """
    if source.parser_id not in PARSER_VERSIONS:
        known = ", ".join(sorted(PARSER_VERSIONS))
        message = (
            f"source {source.source_id!r} references parser {source.parser_id!r}, "
            f"which no implementation declares. Implemented parsers: {known}."
        )
        raise AssertionError(message)
    authoritative = PARSER_VERSIONS[source.parser_id]
    if (
        source.expected_parser_version is not None
        and source.expected_parser_version != authoritative
    ):
        message = (
            f"source {source.source_id!r} expects parser version "
            f"{source.expected_parser_version!r} but the {source.parser_id!r} "
            f"implementation is {authoritative!r}. Update the registration deliberately, "
            "or drop the pin so the version is derived."
        )
        raise AssertionError(message)
    if "/" not in authoritative:
        message = f"source {source.source_id!r} needs a versioned parser identifier"
        raise AssertionError(message)


_validate_registry()
