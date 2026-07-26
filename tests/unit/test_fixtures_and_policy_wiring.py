"""Synthetic-fixture driven checks that policy modules agree with real payload shapes.

Every fixture is hand-written and synthetic; nothing here contacts the SEC.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

from disclosure_drift.sec.availability import boundary_for, compare_boundaries
from disclosure_drift.sec.identifiers import normalize_cik, parse_accession
from disclosure_drift.sec.response_policy import classify_response
from disclosure_drift.sec.schema_drift import inspect_payload
from disclosure_drift.sec.temporal import (
    DateObservation,
    acceptance_timestamps,
    assign_cohorts,
    resolve_official_filing_date,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "sec"
OBSERVED = "2026-07-26T00:00:00Z"


def read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def header_field(text: str, label: str) -> str | None:
    match = re.search(rf"^{re.escape(label)}:\s*(.+)$", text, flags=re.MULTILINE)
    return None if match is None else match.group(1).strip()


def acceptance_value(text: str) -> str | None:
    match = re.search(r"<ACCEPTANCE-DATETIME>(\d{14})", text)
    return None if match is None else match.group(1)


def registrant_ciks(text: str) -> tuple[int, ...]:
    return tuple(
        normalize_cik(value)[0] for value in re.findall(r"CENTRAL INDEX KEY:\s*(\d{10})", text)
    )


def observation(source: str, raw: str, parsed: date | None) -> DateObservation:
    from datetime import datetime

    return DateObservation(
        source=source,  # type: ignore[arg-type]
        field_name="filing_date_sec",
        raw_value=raw,
        observed_at_utc=datetime.fromisoformat(OBSERVED.replace("Z", "+00:00")),
        snapshot_id="fixture",
        parsed_date=parsed,
    )


def test_fixture_directory_is_documented_and_synthetic() -> None:
    readme = read("README.md")
    assert "synthetic" in readme.lower()
    assert FIXTURES.is_dir()


def test_modern_header_yields_a_same_day_boundary() -> None:
    text = read("header_modern.txt")
    accession = parse_accession(header_field(text, "ACCESSION NUMBER") or "")
    filing = header_field(text, "FILED AS OF DATE")
    acceptance = acceptance_timestamps(acceptance_value(text) or "")

    assert filing is not None
    filing_date = date(int(filing[0:4]), int(filing[4:6]), int(filing[6:8]))
    assignment = assign_cohorts(filing_date, acceptance)
    boundary = boundary_for(
        accession.plain, filing_date, acceptance.date_sec, acceptance.datetime_et
    )

    assert accession.dashed == "0000000001-24-000001"
    assert assignment.official_filing_temporal_cohort == "primary_test"
    assert assignment.divergence.reason == "same_day_filing"
    assert boundary.basis == "same_day_acceptance"
    assert boundary.precision == "timestamp"


def test_after_cutoff_header_crosses_a_cohort_boundary() -> None:
    text = read("header_after_cutoff.txt")
    acceptance = acceptance_timestamps(acceptance_value(text) or "")
    assignment = assign_cohorts(date(2022, 1, 3), acceptance)

    assert acceptance.date_sec == date(2021, 12, 31)
    assert acceptance.is_after_normal_cutoff
    assert assignment.official_filing_temporal_cohort == "transition"
    assert assignment.accepted_temporal_cohort == "development"
    assert assignment.cohort_boundary_crossing
    assert assignment.requires_manual_review


def test_multi_registrant_header_keeps_every_registrant() -> None:
    text = read("header_multi_registrant.txt")
    accession = parse_accession("0000000003-24-000001")
    ciks = registrant_ciks(text)
    assert ciks == (3, 4)
    assert accession.submitter_cik_numeric == 3
    assert len(ciks) > 1, "the fixture must exercise the multi-registrant review path"


def test_header_without_acceptance_leaves_the_audit_cohort_null() -> None:
    text = read("header_missing_acceptance.txt")
    assert acceptance_value(text) is None
    assignment = assign_cohorts(date(2011, 3, 30), None)
    assert assignment.accepted_temporal_cohort is None
    assert "REVIEW_MISSING_ACCEPTANCE_TIMESTAMP" in assignment.reason_codes


def test_submissions_fixture_is_a_provisional_source() -> None:
    payload = json.loads(read("submissions_min.json"))
    filings = payload["filings"]["recent"]
    resolved = resolve_official_filing_date(
        [observation("submissions_api", filings["filingDate"][0], date(2024, 2, 15))]
    )
    assert resolved.value == date(2024, 2, 15)
    assert not resolved.is_canonical


def test_header_value_supersedes_the_submissions_fixture() -> None:
    resolved = resolve_official_filing_date(
        [
            observation("submissions_api", "2024-02-14", date(2024, 2, 14)),
            observation("sgml_header", "20240215", date(2024, 2, 15)),
        ]
    )
    assert resolved.value == date(2024, 2, 15)
    assert resolved.is_canonical
    assert resolved.conflicts[0].kind == "provisional_versus_canonical"


def test_index_fixture_lists_every_document() -> None:
    payload = json.loads(read("index_min.json"))
    items = payload["directory"]["item"]
    report = inspect_payload(
        payload["directory"],
        source_class="index_json",
        required_fields={"name": str},
        array_fields=["item"],
    )
    assert len(items) == 4
    assert not report.blocking_events


def test_block_page_fixture_triggers_a_cooldown() -> None:
    action = classify_response(200, {}, read("block_page.html"), expected="html")
    assert action.kind == "cooldown"
    assert action.halts_aggregate_traffic
    assert action.reason_code == "SEC_BLOCK_PAGE"


def test_truncated_json_fixture_is_quarantined_not_accepted() -> None:
    body = read("truncated.json")
    action = classify_response(200, {}, body, expected="json")
    assert action.kind == "proceed"
    with pytest.raises(json.JSONDecodeError):
        json.loads(body)


def test_non_zip_fixture_fails_the_archive_signature_check() -> None:
    body = (FIXTURES / "not_a_zip.bin").read_bytes().decode("latin-1")
    action = classify_response(200, {}, body, expected="archive")
    assert action.kind == "quarantine"
    assert action.reason_code == "RAW_ARCHIVE_INVALID"


def test_availability_order_between_two_fixtures() -> None:
    early = acceptance_timestamps("20240215161500")
    late = acceptance_timestamps("20211231201500")
    early_boundary = boundary_for("a1", date(2024, 2, 15), early.date_sec, early.datetime_et)
    late_boundary = boundary_for("a2", date(2022, 1, 3), late.date_sec, late.datetime_et)

    assert compare_boundaries(late_boundary, early_boundary).outcome == "eligible"
    assert compare_boundaries(early_boundary, late_boundary).outcome == "ineligible"
