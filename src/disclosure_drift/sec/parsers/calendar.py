"""Source-native parsers for EDGAR calendar and announcement evidence.

Stage M2.2-R2.2 rule: **a visible date is not an assertion.** An official SEC page
carries publication dates, page-update dates, filing deadlines, worked examples,
navigation labels, and dates belonging to other years. Treating every date on the page
as an EDGAR operating-status claim would manufacture holidays that the SEC never
declared, so date selection here is structural rather than textual.

Annual calendar
    A date becomes a ``non_operating`` assertion only when it appears in a table row
    (or equivalent reviewed list item) whose enclosing structure is identified as an
    official holiday listing by its caption, heading, or header cells. Every other
    visible date is retained as *contextual* evidence with status ``unknown`` and a
    classification explaining what it appears to be. Contextual evidence is never
    promoted to an assertion.

Date-specific announcements
    The reviewed manifest remains authoritative for the intended affected dates, the
    asserted status, and the evidence identity. This parser's job is verification: it
    confirms that each manifest date is actually supported by the retrieved document,
    refuses to spread a one-day announcement across every date on the page, retains
    unrelated dates as context, and returns ``unknown`` with a release-blocking review
    reason when the document does not support the manifest, contradicts it, is
    ambiguous, or asserts a date the manifest never named.

Decision 011's tri-state model is preserved throughout: ``operating``,
``non_operating``, and ``unknown``. Absence of evidence never proves closure.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Final, Literal

from disclosure_drift.sec.parsers.base import (
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    StructuralObservation,
    count_duplicates,
)

__all__ = [
    "ANNOUNCEMENT_PARSER_VERSION",
    "CALENDAR_PARSER_VERSION",
    "CONTEXTUAL_KINDS",
    "HOLIDAY_TABLE_MARKERS",
    "ContextualKind",
    "DateSighting",
    "parse_calendar_announcement",
    "parse_edgar_calendar",
]

CALENDAR_PARSER_ID: Final = "edgar-calendar"
CALENDAR_PARSER_VERSION: Final = "edgar-calendar/2.0"
ANNOUNCEMENT_PARSER_ID: Final = "edgar-calendar-announcement"
ANNOUNCEMENT_PARSER_VERSION: Final = "edgar-calendar-announcement/2.0"

_DATE_TEXT: Final = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},\s+\d{4}\b"
)
_ISO_DATE: Final = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

HOLIDAY_TABLE_MARKERS: Final[tuple[str, ...]] = (
    "federal holiday",
    "federal holidays",
    "edgar holiday",
    "edgar holidays",
    "filing holiday",
    "filing holidays",
    "holiday schedule",
    "edgar will be closed",
    "edgar is closed",
    "edgar closed",
    "holidays",
)
"""Phrases that identify an enclosing structure as an official holiday listing.

A table or list is only read for assertions when its caption, its heading, or one of
its header cells matches one of these. A bare table of dates asserts nothing.
"""

_DEADLINE_MARKERS: Final[tuple[str, ...]] = (
    "due",
    "deadline",
    "must be filed",
    "filing date for",
    "no later than",
)
_PUBLICATION_MARKERS: Final[tuple[str, ...]] = (
    "published",
    "posted",
    "issued",
    "release date",
    "press release",
)
_UPDATE_MARKERS: Final[tuple[str, ...]] = (
    "last updated",
    "modified",
    "page last reviewed",
    "reviewed or updated",
    "updated on",
)
_EXAMPLE_MARKERS: Final[tuple[str, ...]] = ("for example", "e.g.", "such as", "suppose")
_NAVIGATION_MARKERS: Final[tuple[str, ...]] = (
    "archive",
    "previous year",
    "next year",
    "see also",
    "related",
    "breadcrumb",
)
_CLOSED_MARKERS: Final[tuple[str, ...]] = (
    "will be closed",
    "is closed",
    "was closed",
    "closed",
    "not accept filings",
    "will not accept",
    "unavailable",
    "suspended",
)
_OPEN_MARKERS: Final[tuple[str, ...]] = (
    "will be open",
    "is open",
    "remain open",
    "remained open",
    "will operate",
    "operating normally",
    "will accept filings",
)

ContextualKind = Literal[
    "publication_date",
    "page_update_date",
    "filing_deadline",
    "example",
    "navigation",
    "other_year",
    "unclassified",
]
CONTEXTUAL_KINDS: Final[tuple[str, ...]] = (
    "publication_date",
    "page_update_date",
    "filing_deadline",
    "example",
    "navigation",
    "other_year",
    "unclassified",
)
"""Every classification a retained-but-non-asserting date may carry."""

_ASSERTING_CONTAINERS: Final[frozenset[str]] = frozenset({"td", "th", "li"})


# --------------------------------------------------------------------------- #
# Structural HTML reading
# --------------------------------------------------------------------------- #
class DateSighting:
    """One date found in the document, with the structure that enclosed it.

    ``section_text`` carries the enclosing heading, caption, and header cells. A date
    cell often contains only the date itself, so what the date *means* is determined by
    the structure around it rather than by the cell's own words.
    """

    __slots__ = (
        "context_text",
        "day",
        "in_holiday_structure",
        "order",
        "section_text",
        "structure",
    )

    def __init__(
        self,
        day: date,
        structure: str,
        context_text: str,
        in_holiday_structure: bool,
        order: int,
        section_text: str = "",
    ) -> None:
        self.day = day
        self.structure = structure
        self.context_text = context_text
        self.in_holiday_structure = in_holiday_structure
        self.order = order
        self.section_text = section_text

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"DateSighting({self.day.isoformat()}, {self.structure!r}, "
            f"holiday={self.in_holiday_structure})"
        )


class _StructuralReader(HTMLParser):
    """Collect dates together with the structural context that produced them.

    Only text inside a table cell or list item can carry an assertion, and only when
    the enclosing table or list was identified as a holiday listing. Headings and
    captions seen so far establish that identification.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._table_depth = 0
        self._holiday_table: list[bool] = []
        self._heading_is_holiday = False
        self._heading_text = ""
        self._header_cells: list[str] = []
        self._buffer: list[str] = []
        self._buffer_tag: str | None = None
        self._order = 0
        self.sightings: list[DateSighting] = []
        self.all_text: list[str] = []
        self.tables_seen = 0
        self.holiday_structures_seen = 0

    # -- tag handling ------------------------------------------------------- #
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track structural nesting and open a text buffer for leaf containers."""
        self._stack.append(tag)
        if tag == "table":
            self._table_depth += 1
            self.tables_seen += 1
            # A nested table inherits its parent's identification until its own
            # caption or header says otherwise.
            inherited = self._holiday_table[-1] if self._holiday_table else False
            self._holiday_table.append(inherited or self._heading_is_holiday)
            self._header_cells = []
        if tag in {"td", "th", "li", "caption", "h1", "h2", "h3", "h4", "p", "title"}:
            self._flush()
            self._buffer_tag = tag
            self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        """Close buffers and pop structural state."""
        if tag == self._buffer_tag:
            self._flush()
        if tag == "table" and self._table_depth:
            self._table_depth -= 1
            if self._holiday_table:
                self._holiday_table.pop()
            # Header cells describe one table only; they must not leak into the text
            # that follows it.
            self._header_cells = []
        if tag in self._stack:
            for index in range(len(self._stack) - 1, -1, -1):
                if self._stack[index] == tag:
                    del self._stack[index:]
                    break

    def handle_data(self, data: str) -> None:
        """Accumulate visible text."""
        cleaned = " ".join(data.split())
        if not cleaned:
            return
        self.all_text.append(cleaned)
        self._buffer.append(cleaned)

    # -- internals ---------------------------------------------------------- #
    def _flush(self) -> None:
        if self._buffer_tag is None:
            self._buffer_tag = None
            return
        text = " ".join(self._buffer).strip()
        tag = self._buffer_tag
        self._buffer = []
        self._buffer_tag = None
        if not text:
            return
        lowered = text.lower()
        marks_holiday = any(marker in lowered for marker in HOLIDAY_TABLE_MARKERS)

        if tag in {"caption", "h1", "h2", "h3", "h4", "title"}:
            self._heading_is_holiday = marks_holiday
            self._heading_text = text
            if tag == "caption":
                self._header_cells = []
            if marks_holiday:
                self.holiday_structures_seen += 1
                if self._holiday_table:
                    self._holiday_table[-1] = True
            return
        if tag == "th":
            self._header_cells.append(text)
            if marks_holiday and self._holiday_table:
                self._holiday_table[-1] = True
                self.holiday_structures_seen += 1
            return

        in_holiday = bool(self._holiday_table and self._holiday_table[-1])
        if tag == "li":
            in_holiday = self._heading_is_holiday
        asserting_container = tag in _ASSERTING_CONTAINERS
        section = " ".join([self._heading_text, *self._header_cells]).strip()
        for day in _dates_in(text):
            self._order += 1
            self.sightings.append(
                DateSighting(
                    day=day,
                    structure=tag,
                    context_text=text,
                    in_holiday_structure=in_holiday and asserting_container,
                    order=self._order,
                    section_text=section,
                )
            )

    def close(self) -> None:
        """Flush any trailing buffer before finishing."""
        self._flush()
        super().close()

    def text(self) -> str:
        """All visible text, whitespace-normalized."""
        return " ".join(self.all_text)


def _read(html: str) -> _StructuralReader:
    reader = _StructuralReader()
    reader.feed(html)
    reader.close()
    return reader


def _dates_in(text: str) -> tuple[date, ...]:
    values: list[date] = []
    for raw in _DATE_TEXT.findall(text):
        values.append(datetime.strptime(raw, "%B %d, %Y").date())  # noqa: DTZ007
    for year, month, day in _ISO_DATE.findall(text):
        try:
            values.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    seen: set[date] = set()
    ordered: list[date] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return tuple(ordered)


def _classify_context(sighting: DateSighting, target_year: int | None) -> ContextualKind:
    """Explain what a non-asserting date appears to be.

    The date's own text is consulted first, then its enclosing section. That order
    matters: a date cell in a deadlines table usually contains nothing but the date, so
    the table's heading or its ``Due`` header is what identifies it, while a sentence
    that says "for example" identifies itself and must not be overridden by whichever
    table happened to precede it.
    """
    own = _marker_kind(sighting.context_text)
    if own is not None:
        return own
    section = _marker_kind(sighting.section_text)
    if section is not None:
        return section
    if target_year is not None and sighting.day.year != target_year:
        return "other_year"
    return "unclassified"


def _marker_kind(text: str) -> ContextualKind | None:
    """Return the contextual kind ``text`` identifies, if any."""
    lowered = text.lower()
    for markers, kind in (
        (_UPDATE_MARKERS, "page_update_date"),
        (_PUBLICATION_MARKERS, "publication_date"),
        (_EXAMPLE_MARKERS, "example"),
        (_DEADLINE_MARKERS, "filing_deadline"),
        (_NAVIGATION_MARKERS, "navigation"),
    ):
        if any(marker in lowered for marker in markers):
            return kind  # type: ignore[return-value]
    return None


# --------------------------------------------------------------------------- #
# Annual calendar
# --------------------------------------------------------------------------- #
def parse_edgar_calendar(
    html: str,
    location: RecordLocation,
    *,
    target_year: int | None = None,
) -> ParseOutcome:
    """Parse the official annual EDGAR calendar structurally for one requested year.

    ``target_year`` is required in practice: every annual-calendar instance in the
    census plan carries it explicitly. It is never inferred from the current date or
    from the retrieval timestamp, because that would silently change what a preserved
    snapshot is taken to assert. Passing ``None`` is therefore treated as an
    unanswerable request: nothing is asserted, the region resolves to
    ``indeterminate``, and the source is blocked.

    Args:
        html: Preserved page bytes decoded as text.
        location: Source observation the page came from.
        target_year: Year the census plan requested this snapshot to cover. Identified
            holiday rows from any other year stay contextual and never establish
            coverage for that year.

    Returns:
        A parse outcome whose asserted records are only holiday-structure dates in
        ``target_year``. Every other date is retained as a contextual record with
        status ``unknown``. The requested year is carried in the structural verdict and
        in every record payload, so it participates in the deterministic record hash
        and two runs with different target years are distinguishable.
    """
    if target_year is None:
        return _unanswerable_calendar(html, location)
    reader = _read(html)
    asserted: list[ParsedRecord] = []
    contextual: list[ParsedRecord] = []
    seen_assertions: set[date] = set()

    for sighting in reader.sightings:
        base_location = RecordLocation(
            observation_id=location.observation_id,
            source_id=location.source_id,
            record_path=f"structure.{sighting.structure}",
            record_index=sighting.order,
        )
        wrong_year = sighting.day.year != target_year
        if sighting.in_holiday_structure and not wrong_year:
            if sighting.day in seen_assertions:
                continue
            seen_assertions.add(sighting.day)
            asserted.append(
                ParsedRecord(
                    native_identity=(f"calendar_holiday:{target_year}:{sighting.day.isoformat()}"),
                    payload={
                        "date": sighting.day.isoformat(),
                        "year": sighting.day.year,
                        "requested_target_year": target_year,
                        "status": "non_operating",
                        "evidence_kind": "annual_calendar_snapshot",
                        "selection": "holiday_structure",
                        "structure": sighting.structure,
                        "context_text": sighting.context_text,
                    },
                    location=base_location,
                    parser_id="edgar-calendar",
                    parser_version=CALENDAR_PARSER_VERSION,
                )
            )
            continue

        kind = "other_year" if wrong_year else _classify_context(sighting, target_year)
        contextual.append(
            ParsedRecord(
                native_identity=(
                    f"calendar_context:{target_year}:{kind}:"
                    f"{sighting.day.isoformat()}:{sighting.order}"
                ),
                payload={
                    "date": sighting.day.isoformat(),
                    "year": sighting.day.year,
                    "requested_target_year": target_year,
                    "status": "unknown",
                    "evidence_kind": "contextual_date",
                    "contextual_kind": kind,
                    "selection": "not_asserting",
                    "in_identified_holiday_structure": sighting.in_holiday_structure,
                    "structure": sighting.structure,
                    "context_text": sighting.context_text,
                },
                location=base_location,
                parser_id="edgar-calendar",
                parser_version=CALENDAR_PARSER_VERSION,
                reason_codes=("CALENDAR_CONTEXTUAL_DATE_RETAINED",),
                normalization_warnings=(
                    f"date retained as {kind} context only; it asserts no EDGAR operating status",
                ),
            )
        )

    records = (*asserted, *contextual)
    quarantined: tuple[QuarantinedRecord, ...] = ()
    recognized = bool(reader.holiday_structures_seen)
    year_supported = bool(asserted)

    if not recognized:
        # A redesigned or unrecognized page is not an empty holiday list. The count is
        # unknowable, so the region is indeterminate rather than valid_empty, the raw
        # observation and contextual dates stay preserved, and the source is blocked.
        state: str = "indeterminate"
        detail = (
            "no official holiday table, caption, or heading was recognized, so the "
            f"holiday set for {target_year} is unknown; {len(contextual)} contextual "
            "dates and all unknown fields are preserved"
        )
        quarantined = (
            QuarantinedRecord(
                location=location,
                parser_id="edgar-calendar",
                parser_version=CALENDAR_PARSER_VERSION,
                reason_codes=("REVIEW_CALENDAR_STRUCTURE_UNRECOGNIZED",),
                detail=detail,
                raw_excerpt=html[:500],
            ),
        )
    elif not year_supported:
        # The page was recognized but says nothing about the requested year. That is
        # not "the year had no holidays": the snapshot simply does not cover it.
        state = "indeterminate"
        detail = (
            f"an official holiday structure was recognized but it asserts nothing for "
            f"the requested year {target_year}; coverage for that year is unknown"
        )
        quarantined = (
            QuarantinedRecord(
                location=location,
                parser_id="edgar-calendar",
                parser_version=CALENDAR_PARSER_VERSION,
                reason_codes=("REVIEW_CALENDAR_TARGET_YEAR_UNSUPPORTED",),
                detail=detail,
                raw_excerpt=html[:500],
            ),
        )
    else:
        state = "valid_present"
        detail = (
            f"{len(asserted)} dates were asserted from identified holiday structures for "
            f"{target_year}; {len(contextual)} further visible dates were retained as "
            "context only"
        )

    structural = (
        StructuralObservation(
            region="annual_calendar.holiday_rows",
            state=state,  # type: ignore[arg-type]
            observed_type="html",
            location=RecordLocation(
                observation_id=location.observation_id,
                source_id=location.source_id,
                record_path=f"annual_calendar.holiday_rows[{target_year}]",
            ),
            row_count=len(asserted) if state == "valid_present" else None,
            detail=detail,
            raw_excerpt=reader.text()[:500],
        ),
    )
    return ParseOutcome(
        parser_id="edgar-calendar",
        parser_version=CALENDAR_PARSER_VERSION,
        records=records,
        quarantined=quarantined,
        duplicate_identities=count_duplicates([record.native_identity for record in records]),
        structural=structural,
    )


def _unanswerable_calendar(html: str, location: RecordLocation) -> ParseOutcome:
    """Refuse to parse an annual calendar without an explicitly requested year.

    The year is never inferred from the current date or the retrieval timestamp, so a
    missing target year makes the request unanswerable rather than defaulting.
    """
    reader = _read(html)
    contextual = tuple(
        ParsedRecord(
            native_identity=(
                f"calendar_context:no_target_year:{sighting.day.isoformat()}:{sighting.order}"
            ),
            payload={
                "date": sighting.day.isoformat(),
                "year": sighting.day.year,
                "requested_target_year": None,
                "status": "unknown",
                "evidence_kind": "contextual_date",
                "contextual_kind": "unclassified",
                "selection": "not_asserting",
                "structure": sighting.structure,
                "context_text": sighting.context_text,
            },
            location=RecordLocation(
                observation_id=location.observation_id,
                source_id=location.source_id,
                record_path=f"structure.{sighting.structure}",
                record_index=sighting.order,
            ),
            parser_id="edgar-calendar",
            parser_version=CALENDAR_PARSER_VERSION,
            reason_codes=("CALENDAR_CONTEXTUAL_DATE_RETAINED",),
            normalization_warnings=(
                "no target year was requested, so no date may assert an operating status",
            ),
        )
        for sighting in reader.sightings
    )
    return ParseOutcome(
        parser_id="edgar-calendar",
        parser_version=CALENDAR_PARSER_VERSION,
        records=contextual,
        quarantined=(
            QuarantinedRecord(
                location=location,
                parser_id="edgar-calendar",
                parser_version=CALENDAR_PARSER_VERSION,
                reason_codes=("REVIEW_CALENDAR_TARGET_YEAR_ABSENT",),
                detail=(
                    "the census plan supplied no target year for this annual-calendar "
                    "instance; the year is never inferred from the current date or the "
                    "retrieval timestamp, so nothing is asserted"
                ),
                raw_excerpt=html[:500],
            ),
        ),
        structural=(
            StructuralObservation(
                region="annual_calendar.holiday_rows",
                state="indeterminate",
                observed_type="html",
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path="annual_calendar.holiday_rows[unspecified]",
                ),
                detail="no target year was requested, so no holiday set can be established",
                raw_excerpt=reader.text()[:500],
            ),
        ),
    )


# --------------------------------------------------------------------------- #
# Date-specific announcements
# --------------------------------------------------------------------------- #
def parse_calendar_announcement(
    html: str,
    location: RecordLocation,
    *,
    asserted_status: str | None = None,
    evidence_id: str | None = None,
    manifest_dates: tuple[date, ...] = (),
) -> ParseOutcome:
    """Verify a date-specific announcement against its reviewed manifest entry.

    The manifest is authoritative for which dates are affected and what is asserted.
    This parser confirms the retrieved document actually supports that, and refuses to
    apply the asserted status to any other date on the page.

    Args:
        html: Preserved announcement page decoded as text.
        location: Source observation the page came from.
        asserted_status: ``"operating"`` or ``"non_operating"`` from the manifest.
        evidence_id: Reviewed manifest evidence identifier.
        manifest_dates: The dates the manifest says this announcement affects.

    Returns:
        A parse outcome carrying one record per manifest date, each either supported by
        the document or resolved to ``unknown`` with a release-blocking review reason,
        plus contextual records for unrelated dates and for any date the document
        appears to assert that the manifest never named.
    """
    reader = _read(html)
    status = asserted_status if asserted_status in {"operating", "non_operating"} else "unknown"
    sightings_by_date: dict[date, list[DateSighting]] = {}
    for sighting in reader.sightings:
        sightings_by_date.setdefault(sighting.day, []).append(sighting)

    records: list[ParsedRecord] = []
    quarantined: list[QuarantinedRecord] = []

    if not manifest_dates:
        quarantined.append(
            QuarantinedRecord(
                location=location,
                parser_id="edgar-calendar-announcement",
                parser_version=ANNOUNCEMENT_PARSER_VERSION,
                reason_codes=("REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED",),
                detail=(
                    "no reviewed manifest dates were supplied, so the document cannot be "
                    "verified and no operating status may be asserted from it"
                ),
                raw_excerpt=html[:500],
            )
        )

    for day in manifest_dates:
        found = sightings_by_date.get(day, [])
        support = _support_for(found, status)
        resolved = status if support.supports else "unknown"
        records.append(
            ParsedRecord(
                native_identity=(
                    f"calendar_announcement:{evidence_id or 'unreviewed'}:{day.isoformat()}"
                ),
                payload={
                    "date": day.isoformat(),
                    "status": resolved,
                    "manifest_status": status,
                    "evidence_kind": "date_specific_announcement",
                    "evidence_id": evidence_id,
                    "document_support": support.verdict,
                    "supporting_text": support.text,
                },
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path="manifest.affected_dates",
                    record_index=manifest_dates.index(day),
                ),
                parser_id="edgar-calendar-announcement",
                parser_version=ANNOUNCEMENT_PARSER_VERSION,
                reason_codes=support.reason_codes,
                normalization_warnings=support.warnings,
            )
        )
        if not support.supports:
            quarantined.append(
                QuarantinedRecord(
                    location=location,
                    parser_id="edgar-calendar-announcement",
                    parser_version=ANNOUNCEMENT_PARSER_VERSION,
                    reason_codes=support.reason_codes,
                    detail=(
                        f"manifest date {day.isoformat()} is not supported by the retrieved "
                        f"document ({support.verdict}); the date resolves to unknown"
                    ),
                    raw_excerpt=(support.text or reader.text())[:500],
                    native_identity=evidence_id,
                )
            )

    manifest_set = set(manifest_dates)
    for day, found in sorted(sightings_by_date.items()):
        if day in manifest_set:
            continue
        kind = _classify_context(found[0], None)
        claims = _status_language(" ".join(item.context_text for item in found))
        # Status language often sits in the same sentence as an unrelated date, for
        # example "EDGAR will be closed on July 3. Published June 1." A date that is
        # already explained as a publication, update, deadline, example, navigation, or
        # other-year date is not an assertion candidate, so only an otherwise
        # unexplained date accompanied by status language is reported as unexpected.
        unexpected = claims in {"closed", "open"} and kind == "unclassified"
        records.append(
            ParsedRecord(
                native_identity=f"calendar_announcement_context:{day.isoformat()}",
                payload={
                    "date": day.isoformat(),
                    "status": "unknown",
                    "evidence_kind": "contextual_date",
                    "contextual_kind": _classify_context(found[0], None),
                    "evidence_id": evidence_id,
                    "appears_to_assert": claims,
                    "context_text": found[0].context_text,
                },
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path=f"structure.{found[0].structure}",
                    record_index=found[0].order,
                ),
                parser_id="edgar-calendar-announcement",
                parser_version=ANNOUNCEMENT_PARSER_VERSION,
                reason_codes=(
                    ("REVIEW_CALENDAR_UNEXPECTED_AFFECTED_DATE",)
                    if unexpected
                    else ("CALENDAR_CONTEXTUAL_DATE_RETAINED",)
                ),
                normalization_warnings=(
                    (
                        f"the document appears to assert {claims!r} for {day.isoformat()}, "
                        "which the reviewed manifest does not name; no status is applied",
                    )
                    if unexpected
                    else (
                        "date retained as context only; the announcement asserts nothing about it",
                    )
                ),
            )
        )
        if unexpected:
            quarantined.append(
                QuarantinedRecord(
                    location=location,
                    parser_id="edgar-calendar-announcement",
                    parser_version=ANNOUNCEMENT_PARSER_VERSION,
                    reason_codes=("REVIEW_CALENDAR_UNEXPECTED_AFFECTED_DATE",),
                    detail=(
                        f"the document appears to assert an operating status for "
                        f"{day.isoformat()}, which is absent from the reviewed manifest"
                    ),
                    raw_excerpt=found[0].context_text[:500],
                    native_identity=evidence_id,
                )
            )

    return ParseOutcome(
        parser_id="edgar-calendar-announcement",
        parser_version=ANNOUNCEMENT_PARSER_VERSION,
        records=tuple(records),
        quarantined=tuple(quarantined),
        duplicate_identities=count_duplicates([record.native_identity for record in records]),
        structural=(
            StructuralObservation(
                region="announcement.manifest_dates",
                state="valid_present" if manifest_dates else "absent",
                observed_type="html",
                location=RecordLocation(
                    observation_id=location.observation_id,
                    source_id=location.source_id,
                    record_path="announcement.manifest_dates",
                ),
                row_count=len(manifest_dates),
                detail=(
                    f"{len(manifest_dates)} manifest dates verified against the document; "
                    f"{len(sightings_by_date) - len(manifest_set & set(sightings_by_date))} "
                    "unrelated visible dates retained as context"
                ),
                raw_excerpt=reader.text()[:500],
            ),
        ),
    )


class _Support:
    """Whether the document supports the manifest's claim for one date."""

    __slots__ = ("reason_codes", "supports", "text", "verdict", "warnings")

    def __init__(
        self,
        supports: bool,
        verdict: str,
        text: str,
        reason_codes: tuple[str, ...],
        warnings: tuple[str, ...],
    ) -> None:
        self.supports = supports
        self.verdict = verdict
        self.text = text
        self.reason_codes = reason_codes
        self.warnings = warnings


def _support_for(found: list[DateSighting], status: str) -> _Support:
    """Decide whether the retrieved document supports the manifest claim."""
    if status == "unknown":
        return _Support(
            False,
            "manifest_status_not_approved",
            " ".join(item.context_text for item in found),
            ("REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED",),
            ("the manifest did not supply an approved status for this evidence",),
        )
    if not found:
        return _Support(
            False,
            "date_absent_from_document",
            "",
            ("REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED",),
            ("the manifest date does not appear in the retrieved document",),
        )
    text = " ".join(item.context_text for item in found)
    language = _status_language(text)
    if language == "ambiguous":
        return _Support(
            False,
            "prose_ambiguous",
            text,
            ("REVIEW_CALENDAR_EVIDENCE_AMBIGUOUS",),
            ("the surrounding prose does not determine an operating status",),
        )
    if language == "none":
        return _Support(
            False,
            "no_status_language",
            text,
            ("REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED",),
            ("the date appears without any operating-status language",),
        )
    expected = "closed" if status == "non_operating" else "open"
    if language != expected:
        return _Support(
            False,
            "document_contradicts_manifest",
            text,
            ("REVIEW_CALENDAR_EVIDENCE_CONFLICT",),
            (
                f"the manifest asserts {status!r} but the document reads as {language!r}; "
                "both observations are preserved and the date resolves to unknown",
            ),
        )
    return _Support(True, "supported", text, (), ())


def _status_language(text: str) -> str:
    """Classify operating-status language as closed, open, ambiguous, or none."""
    lowered = text.lower()
    closed = any(marker in lowered for marker in _CLOSED_MARKERS)
    opened = any(marker in lowered for marker in _OPEN_MARKERS)
    if closed and opened:
        return "ambiguous"
    if closed:
        return "closed"
    if opened:
        return "open"
    return "none"
