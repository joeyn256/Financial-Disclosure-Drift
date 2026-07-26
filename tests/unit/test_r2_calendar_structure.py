"""Stage M2.2-R2.2: calendar evidence is selected structurally, not textually.

An official SEC page carries publication dates, page-update dates, filing deadlines,
worked examples, navigation labels, and dates from other years. None of those is an
EDGAR operating-status assertion. A date becomes an assertion only inside an identified
official holiday structure, or when a reviewed manifest names it *and* the retrieved
document supports it. Decision 011's tri-state model is preserved throughout.
"""

from __future__ import annotations

from datetime import date

import pytest

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation
from disclosure_drift.sec.parsers.calendar import (
    parse_calendar_announcement,
    parse_edgar_calendar,
)
from disclosure_drift.sec.source_registry import require_registered
from disclosure_drift.sec.urls import validate_url

CALENDAR_LOCATION = RecordLocation(observation_id="obs-cal", source_id="sec_edgar_filing_calendar")
ANNOUNCEMENT_LOCATION = RecordLocation(
    observation_id="obs-ann", source_id="sec_edgar_calendar_announcement"
)

PAGE = """
<html><head><title>EDGAR Filing Calendar</title></head><body>
<p>Page last updated March 4, 2026.</p>
<p>This notice was published February 2, 2026.</p>
<h2>2026 EDGAR federal holidays</h2>
<table>
  <tr><th>Holiday</th><th>Date</th></tr>
  <tr><td>New Year's Day</td><td>January 1, 2026</td></tr>
  <tr><td>Independence Day</td><td>July 3, 2026</td></tr>
</table>
<h2>Filing deadlines</h2>
<table>
  <tr><th>Form</th><th>Due</th></tr>
  <tr><td>10-K</td><td>March 2, 2026</td></tr>
</table>
<p>For example, a filing submitted on May 5, 2026 is timely.</p>
<h2>Archive</h2>
<ul><li>Previous year: December 25, 2025</li></ul>
</body></html>
"""


def assertions(outcome: ParseOutcome) -> dict[str, str]:
    """Dates the outcome actually asserts an operating status for."""
    return {
        str(record.payload["date"]): str(record.payload["status"])
        for record in outcome.records
        if record.payload.get("evidence_kind") == "annual_calendar_snapshot"
    }


def contexts(outcome: ParseOutcome) -> dict[str, str]:
    """Dates retained as contextual evidence, mapped to their classification."""
    return {
        str(record.payload["date"]): str(record.payload["contextual_kind"])
        for record in outcome.records
        if record.payload.get("evidence_kind") == "contextual_date"
    }


# --------------------------------------------------------------------------- #
# Annual calendar
# --------------------------------------------------------------------------- #
def test_only_identified_holiday_rows_are_asserted() -> None:
    outcome = parse_edgar_calendar(PAGE, CALENDAR_LOCATION, target_year=2026)
    assert assertions(outcome) == {
        "2026-01-01": "non_operating",
        "2026-07-03": "non_operating",
    }


@pytest.mark.parametrize(
    ("day", "kind"),
    [
        ("2026-03-04", "page_update_date"),
        ("2026-02-02", "publication_date"),
        ("2026-03-02", "filing_deadline"),
        ("2026-05-05", "example"),
        ("2025-12-25", "other_year"),
    ],
)
def test_distractor_dates_are_retained_as_context_only(day: str, kind: str) -> None:
    outcome = parse_edgar_calendar(PAGE, CALENDAR_LOCATION, target_year=2026)
    assert contexts(outcome)[day] == kind


def test_no_contextual_date_carries_an_operating_status() -> None:
    outcome = parse_edgar_calendar(PAGE, CALENDAR_LOCATION, target_year=2026)
    contextual = [
        record
        for record in outcome.records
        if record.payload.get("evidence_kind") == "contextual_date"
    ]
    assert contextual
    for record in contextual:
        assert record.payload["status"] == "unknown"
        assert "CALENDAR_CONTEXTUAL_DATE_RETAINED" in record.reason_codes
    assert not REASON_CODES["CALENDAR_CONTEXTUAL_DATE_RETAINED"].blocks_release


def test_multiple_years_on_one_page_do_not_establish_other_year_coverage() -> None:
    html = (
        "<h2>EDGAR federal holidays</h2><table><tr><th>Date</th></tr>"
        "<tr><td>January 1, 2026</td></tr><tr><td>January 1, 2025</td></tr></table>"
    )
    outcome = parse_edgar_calendar(html, CALENDAR_LOCATION, target_year=2026)
    assert assertions(outcome) == {"2026-01-01": "non_operating"}
    assert contexts(outcome)["2025-01-01"] == "other_year"


def test_prose_alone_never_asserts_a_holiday() -> None:
    outcome = parse_edgar_calendar(
        "<p>EDGAR will be closed January 1, 2026 for the holiday.</p>",
        CALENDAR_LOCATION,
        target_year=2026,
    )
    assert assertions(outcome) == {}
    assert outcome.quarantined
    assert "REVIEW_CALENDAR_STRUCTURE_UNRECOGNIZED" in outcome.quarantined[0].reason_codes
    assert REASON_CODES["REVIEW_CALENDAR_STRUCTURE_UNRECOGNIZED"].blocks_release


def test_an_unidentified_table_of_dates_asserts_nothing() -> None:
    outcome = parse_edgar_calendar(
        "<table><tr><th>Date</th></tr><tr><td>January 1, 2026</td></tr></table>",
        CALENDAR_LOCATION,
        target_year=2026,
    )
    assert assertions(outcome) == {}


def test_calendar_structural_verdict_reports_the_asserted_row_count() -> None:
    outcome = parse_edgar_calendar(PAGE, CALENDAR_LOCATION, target_year=2026)
    verdict = outcome.structural[0]
    assert verdict.region == "annual_calendar.holiday_rows"
    assert verdict.row_count == 2
    assert verdict.count_is_trustworthy


# --------------------------------------------------------------------------- #
# Date-specific announcements
# --------------------------------------------------------------------------- #
def test_exact_manifest_date_supported_by_the_document_is_asserted() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026. Published June 1, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-1",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "non_operating"
    assert outcome.records[0].payload["document_support"] == "supported"
    assert not outcome.quarantined


def test_a_one_day_announcement_is_not_spread_across_the_page() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026. Published June 1, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-1",
        manifest_dates=(date(2026, 7, 3),),
    )
    asserted = [record for record in outcome.records if record.payload["status"] == "non_operating"]
    assert len(asserted) == 1
    unrelated = [record for record in outcome.records if record.payload["date"] == "2026-06-01"]
    assert unrelated and all(record.payload["status"] == "unknown" for record in unrelated)


def test_manifest_date_absent_from_the_document_resolves_to_unknown() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 6, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-2",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "unknown"
    assert "REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED" in outcome.records[0].reason_codes
    assert REASON_CODES["REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED"].blocks_release


def test_a_date_the_manifest_never_named_is_flagged_not_applied() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 6, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-2",
        manifest_dates=(date(2026, 7, 3),),
    )
    unexpected = [record for record in outcome.records if record.payload["date"] == "2026-07-06"]
    assert unexpected
    assert "REVIEW_CALENDAR_UNEXPECTED_AFFECTED_DATE" in unexpected[0].reason_codes
    assert unexpected[0].payload["status"] == "unknown"


def test_document_contradicting_the_manifest_yields_a_conflict() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will remain open on July 3, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-3",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "unknown"
    assert "REVIEW_CALENDAR_EVIDENCE_CONFLICT" in outcome.records[0].reason_codes


def test_ambiguous_prose_resolves_to_unknown() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026, though some systems remain open.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-4",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "unknown"
    assert "REVIEW_CALENDAR_EVIDENCE_AMBIGUOUS" in outcome.records[0].reason_codes


def test_a_date_without_status_language_is_unsupported() -> None:
    outcome = parse_calendar_announcement(
        "<p>Notice regarding July 3, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-5",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "unknown"
    assert outcome.records[0].payload["document_support"] == "no_status_language"


def test_multiple_explicitly_affected_dates_are_each_verified() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026 and July 6, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-6",
        manifest_dates=(date(2026, 7, 3), date(2026, 7, 6)),
    )
    assert [record.payload["status"] for record in outcome.records[:2]] == [
        "non_operating",
        "non_operating",
    ]
    assert not outcome.quarantined


def test_exceptional_operation_is_asserted_only_when_the_document_says_open() -> None:
    outcome = parse_calendar_announcement(
        "<table><caption>EDGAR federal holidays</caption>"
        "<tr><td>EDGAR will be open on July 3, 2026</td></tr></table>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="operating",
        evidence_id="ann-7",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "operating"


def test_an_unapproved_manifest_status_never_becomes_an_assertion() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        evidence_id="ann-8",
        manifest_dates=(date(2026, 7, 3),),
    )
    assert outcome.records[0].payload["status"] == "unknown"
    assert outcome.records[0].payload["document_support"] == "manifest_status_not_approved"


def test_without_manifest_dates_nothing_is_asserted() -> None:
    outcome = parse_calendar_announcement(
        "<p>EDGAR will be closed on July 3, 2026.</p>",
        ANNOUNCEMENT_LOCATION,
        asserted_status="non_operating",
        evidence_id="ann-9",
    )
    assert all(record.payload["status"] == "unknown" for record in outcome.records)
    assert outcome.quarantined
    assert "REVIEW_CALENDAR_EVIDENCE_UNSUPPORTED" in outcome.quarantined[0].reason_codes


def test_only_the_three_decision_011_states_are_ever_produced() -> None:
    produced: set[str] = set()
    for html, status, dates in (
        ("<p>EDGAR will be closed on July 3, 2026.</p>", "non_operating", (date(2026, 7, 3),)),
        ("<p>EDGAR will be open on July 3, 2026.</p>", "operating", (date(2026, 7, 3),)),
        ("<p>Nothing relevant here.</p>", "non_operating", (date(2026, 7, 3),)),
    ):
        outcome = parse_calendar_announcement(
            html,
            ANNOUNCEMENT_LOCATION,
            asserted_status=status,
            evidence_id="ann-tri",
            manifest_dates=dates,
        )
        produced.update(str(record.payload["status"]) for record in outcome.records)
    assert produced <= {"operating", "non_operating", "unknown"}


# --------------------------------------------------------------------------- #
# R1 portability regression found during R2 review
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "source_id",
    [
        "sec_company_tickers_exchange",
        "sec_company_tickers",
        "sec_bulk_submissions",
        "sec_edgar_filing_calendar",
        "sec_sic_code_list",
    ],
)
def test_a_url_without_a_query_string_is_not_treated_as_malformed(source_id: str) -> None:
    """``parse_qsl`` only gained an empty-query guard in Python 3.12.

    With ``strict_parsing=True`` and no guard of our own, every registered SEC URL
    without a query string was refused on Python 3.10 and 3.11 as carrying a
    "malformed query string". The boundary must behave identically on every
    interpreter.
    """
    spec = require_registered(source_id)
    assert validate_url(spec.url(), spec)


# --------------------------------------------------------------------------- #
# Acceptance regression: an omitted calendar year is fail-closed
# --------------------------------------------------------------------------- #
def test_an_omitted_target_year_cannot_produce_a_successful_calendar_source() -> None:
    """Decision 011 stays fail-closed when the census plan omits the year.

    A well-formed page that *would* assert a holiday for 2026 must still assert nothing
    when no year was requested, must resolve the region to ``indeterminate`` so its count
    is not believed, and must carry a release-blocking review reason. The year is never
    inferred from the current date, so an omitted year is an unanswerable request rather
    than a defaulted one.
    """
    well_formed = (
        "<table><caption>2026 EDGAR federal holidays</caption>"
        "<tr><td>New Year's Day</td><td>January 1, 2026</td></tr></table>"
    )
    answered = parse_edgar_calendar(well_formed, CALENDAR_LOCATION, target_year=2026)
    unanswered = parse_edgar_calendar(well_formed, CALENDAR_LOCATION)

    # The same page yields an assertion only when a year was requested.
    assert assertions(answered) == {"2026-01-01": "non_operating"}
    assert assertions(unanswered) == {}

    verdict = unanswered.structural[0]
    assert verdict.state == "indeterminate"
    assert not verdict.count_is_trustworthy
    assert not verdict.is_genuine_zero
    assert not unanswered.counts_are_trustworthy

    assert unanswered.quarantined
    assert "REVIEW_CALENDAR_TARGET_YEAR_ABSENT" in unanswered.quarantined[0].reason_codes
    assert REASON_CODES["REVIEW_CALENDAR_TARGET_YEAR_ABSENT"].blocks_release

    # Every visible date is retained as context at status unknown, none as an assertion.
    for record in unanswered.records:
        assert record.payload["status"] == "unknown"
        assert record.payload["requested_target_year"] is None


def test_a_recognized_page_that_omits_the_requested_year_is_also_blocked() -> None:
    """Coverage for a year the snapshot does not mention is unknown, not empty."""
    outcome = parse_edgar_calendar(
        "<table><caption>2026 EDGAR federal holidays</caption>"
        "<tr><td>New Year's Day</td><td>January 1, 2026</td></tr></table>",
        CALENDAR_LOCATION,
        target_year=2025,
    )
    assert assertions(outcome) == {}
    assert outcome.structural[0].state == "indeterminate"
    assert outcome.quarantined
    assert "REVIEW_CALENDAR_TARGET_YEAR_UNSUPPORTED" in outcome.quarantined[0].reason_codes
    assert REASON_CODES["REVIEW_CALENDAR_TARGET_YEAR_UNSUPPORTED"].blocks_release
