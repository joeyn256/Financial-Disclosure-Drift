"""Stage M2.2-R2.1: a malformed submissions schema must never become a false zero.

Only two shapes permit a record count to be believed: a nested region that is present
with rows, and a nested region that is present, correctly typed, and empty. Every other
shape yields an unknown count, a release-blocking reason, a retained raw payload, and an
exact field location, and therefore prevents required-source success.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation, record_hash
from disclosure_drift.sec.parsers.submissions import (
    REGION_FILES,
    REGION_FILINGS,
    REGION_RECENT,
    parse_submissions_document,
)

LOCATION = RecordLocation(
    observation_id="obs-1",
    source_id="sec_bulk_submissions",
    member_name="CIK0000000001.json",
)

_BASE: dict[str, Any] = {
    "cik": "1",
    "name": "SYNTHETIC ONE",
    "sic": "2834",
    "fiscalYearEnd": "1231",
    "tickers": ["SYN"],
    "exchanges": ["Nasdaq"],
    "formerNames": [{"name": "OLD SYNTHETIC", "from": "2018-01-01", "to": "2020-01-01"}],
    "filings": {
        "recent": {
            "accessionNumber": ["0000000001-24-000001"],
            "filingDate": ["2024-02-01"],
            "form": ["10-K"],
        },
        "files": [
            {
                "name": "CIK0000000001-submissions-001.json",
                "filingCount": 1,
                "filingFrom": "2010-01-01",
                "filingTo": "2010-12-31",
            }
        ],
    },
}


def document(**overrides: Any) -> dict[str, Any]:
    """Return a deep copy of the valid fixture with ``overrides`` applied."""
    payload = copy.deepcopy(_BASE)
    payload.update(overrides)
    return payload


def blocking_reasons(outcome: ParseOutcome) -> tuple[str, ...]:
    """Release-blocking reason codes implied by a parser outcome."""
    return tuple(
        code
        for code in outcome.reason_codes
        if code in REASON_CODES and REASON_CODES[code].blocks_release
    )


# --------------------------------------------------------------------------- #
# Genuine zeros
# --------------------------------------------------------------------------- #
def test_structurally_valid_empty_recent_arrays_are_a_real_zero() -> None:
    payload = document()
    payload["filings"]["recent"] = {"accessionNumber": [], "filingDate": [], "form": []}
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_RECENT) == "valid_empty"
    assert outcome.counts_are_trustworthy
    assert outcome.structural[0].is_genuine_zero
    assert outcome.structural[0].row_count == 0
    assert "PARSER_STRUCTURE_VALID_EMPTY" in outcome.reason_codes
    assert not blocking_reasons(outcome)


def test_empty_recent_object_is_a_real_zero() -> None:
    payload = document()
    payload["filings"]["recent"] = {}
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_RECENT) == "valid_empty"
    assert outcome.counts_are_trustworthy


def test_explicit_empty_files_list_is_a_real_zero() -> None:
    payload = document()
    payload["filings"]["files"] = []
    outcome, references = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_FILES) == "valid_empty"
    assert references == ()
    assert outcome.counts_are_trustworthy


def test_valid_document_permits_its_counts_to_be_believed() -> None:
    outcome, references = parse_submissions_document(document(), LOCATION)
    assert outcome.region_state(REGION_RECENT) == "valid_present"
    assert outcome.region_state(REGION_FILES) == "valid_present"
    assert outcome.counts_are_trustworthy
    assert references[0].is_retrievable


# --------------------------------------------------------------------------- #
# The false-zero shapes
# --------------------------------------------------------------------------- #
def _without_filings() -> dict[str, Any]:
    payload = document()
    del payload["filings"]
    return payload


def _without_recent() -> dict[str, Any]:
    payload = document()
    del payload["filings"]["recent"]
    return payload


def _null_recent() -> dict[str, Any]:
    payload = document()
    payload["filings"]["recent"] = None
    return payload


def _list_recent() -> dict[str, Any]:
    payload = document()
    payload["filings"]["recent"] = [{"accessionNumber": "x"}]
    return payload


def _scalar_recent() -> dict[str, Any]:
    payload = document()
    payload["filings"]["recent"] = "unavailable"
    return payload


def _ragged_recent() -> dict[str, Any]:
    payload = document()
    payload["filings"]["recent"] = {
        "accessionNumber": ["a", "b"],
        "filingDate": ["2024-01-01"],
        "form": ["10-K"],
    }
    return payload


def _scalar_columns() -> dict[str, Any]:
    payload = document()
    payload["filings"]["recent"] = {
        "accessionNumber": "0000000001-24-000001",
        "filingDate": "2024-02-01",
        "form": "10-K",
    }
    return payload


@pytest.mark.parametrize(
    ("factory", "region", "expected"),
    [
        (_without_filings, REGION_FILINGS, "absent"),
        (_without_recent, REGION_RECENT, "absent"),
        (_null_recent, REGION_RECENT, "null"),
        (_list_recent, REGION_RECENT, "wrong_type"),
        (_scalar_recent, REGION_RECENT, "wrong_type"),
        (_ragged_recent, REGION_RECENT, "malformed"),
        (_scalar_columns, REGION_RECENT, "malformed"),
    ],
)
def test_unusable_nested_shapes_never_become_a_genuine_zero(
    factory: Any,
    region: str,
    expected: str,
) -> None:
    outcome, _ = parse_submissions_document(factory(), LOCATION)
    assert outcome.region_state(region) == expected
    assert not outcome.counts_are_trustworthy
    assert blocking_reasons(outcome)
    assert all(not item.is_genuine_zero for item in outcome.structural_failures)


@pytest.mark.parametrize(
    ("factory", "region"),
    [
        (_without_filings, REGION_FILINGS),
        (_without_recent, REGION_RECENT),
        (_null_recent, REGION_RECENT),
        (_list_recent, REGION_RECENT),
        (_ragged_recent, REGION_RECENT),
    ],
)
def test_unusable_nested_shapes_retain_payload_and_location(
    factory: Any,
    region: str,
) -> None:
    outcome, _ = parse_submissions_document(factory(), LOCATION)
    failure = next(item for item in outcome.structural_failures if item.region == region)
    assert failure.raw_excerpt
    assert failure.location.record_path == region
    assert failure.location.member_name == "CIK0000000001.json"
    assert failure.observed_type


def test_ragged_arrays_are_quarantined_rather_than_truncated() -> None:
    outcome, _ = parse_submissions_document(_ragged_recent(), LOCATION)
    assert not any(record.native_identity.startswith("accession:") for record in outcome.records)
    assert any("disagree in length" in item.detail for item in outcome.quarantined)


def test_malformed_row_is_quarantined_while_siblings_still_parse() -> None:
    payload = document()
    payload["filings"]["recent"] = {
        "accessionNumber": ["0000000001-24-000001", ""],
        "filingDate": ["2024-02-01", "2024-03-01"],
        "form": ["10-K", "10-K/A"],
    }
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_RECENT) == "valid_present"
    identities = {record.native_identity for record in outcome.records}
    assert "accession:0000000001-24-000001" in identities
    assert len(outcome.quarantined) == 1


def test_document_that_fails_top_level_validation_still_reports_regions() -> None:
    payload = document()
    del payload["filings"]
    del payload["name"]
    outcome, _ = parse_submissions_document(payload, LOCATION)
    # Without a structural verdict here a caller would be told the counts are
    # trustworthy for a document nothing could be counted from.
    assert not outcome.counts_are_trustworthy
    assert outcome.region_state(REGION_FILINGS) == "absent"
    assert outcome.region_state(REGION_RECENT) == "indeterminate"


# --------------------------------------------------------------------------- #
# filings.files
# --------------------------------------------------------------------------- #
def test_null_files_is_not_an_empty_list() -> None:
    payload = document()
    payload["filings"]["files"] = None
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_FILES) == "null"
    assert not outcome.counts_are_trustworthy


def test_wrong_type_files_is_refused() -> None:
    payload = document()
    payload["filings"]["files"] = {"name": "x"}
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert outcome.region_state(REGION_FILES) == "wrong_type"


def _mixed_files_payload() -> dict[str, Any]:
    payload = document()
    payload["filings"]["files"] = [
        {"name": "CIK0000000001-submissions-001.json", "filingCount": 5},
        {"filingCount": 12},
        "not-an-object",
        {"name": "../escape.json", "filingCount": 3},
        {"name": "CIK0000000001-submissions-002.json", "filingCount": "many"},
        {"name": "CIK0000000001-submissions-003.json", "filingCount": 7, "brandNewKey": True},
    ]
    return payload


def test_every_files_entry_is_preserved_and_none_is_skipped() -> None:
    outcome, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert len(references) == 6
    assert "PARSER_HISTORICAL_REFERENCE_MALFORMED" in outcome.reason_codes
    assert outcome.region_state(REGION_FILES) == "malformed"


def test_historical_entry_without_a_name_is_preserved_not_dropped() -> None:
    _, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    nameless = references[1]
    assert nameless.name is None
    assert not nameless.is_retrievable
    assert nameless.problems
    assert nameless.location.record_index == 1


def test_non_object_files_entry_records_its_observed_type() -> None:
    _, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert references[2].name is None
    assert "not an object" in references[2].problems[0]


def test_unexpected_historical_name_is_never_retrievable() -> None:
    _, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert references[3].name == "../escape.json"
    assert not references[3].is_retrievable


def test_unusable_filing_count_is_a_problem_and_the_value_is_kept() -> None:
    _, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert not references[4].is_retrievable
    assert references[4].raw_entry is not None
    assert references[4].raw_entry["filingCount"] == "many"


def test_valid_references_survive_malformed_siblings() -> None:
    _, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert references[0].is_retrievable
    assert references[5].is_retrievable


def test_unknown_key_on_a_reference_is_retained() -> None:
    outcome, references = parse_submissions_document(_mixed_files_payload(), LOCATION)
    assert references[5].unknown_fields == ("brandNewKey",)
    assert "filings.files[5].brandNewKey" in outcome.unknown_fields


# --------------------------------------------------------------------------- #
# Nested unknown fields and SEC schema additions
# --------------------------------------------------------------------------- #
def _nested_additions() -> dict[str, Any]:
    payload = document()
    payload["filings"]["newFilingsBlock"] = {"a": 1}
    payload["filings"]["recent"]["newColumn"] = ["z"]
    payload["formerNames"][0]["reasonForChange"] = "merger"
    payload["addresses"] = {
        "business": {"street1": "1 Loop", "newAddressField": "x"},
        "newAddressKind": {"street1": "y"},
    }
    payload["flags"] = {"newFlag": True}
    payload["topLevelAddition"] = ["scalar", 1]
    return payload


@pytest.mark.parametrize(
    "path",
    [
        "filings.newFilingsBlock",
        "filings.recent.newColumn",
        "formerNames[0].reasonForChange",
        "addresses.business.newAddressField",
        "addresses.newAddressKind",
        "flags.newFlag",
        "topLevelAddition",
    ],
)
def test_unknown_nested_paths_are_recorded(path: str) -> None:
    outcome, _ = parse_submissions_document(_nested_additions(), LOCATION)
    assert path in outcome.unknown_fields


@pytest.mark.parametrize(
    ("label", "value"),
    [("scalar", 42), ("list", [1, 2]), ("object", {"k": "v"})],
)
def test_unknown_nested_scalar_list_and_object_are_all_recorded(
    label: str,
    value: Any,
) -> None:
    payload = document()
    payload["filings"][f"unknown_{label}"] = value
    outcome, _ = parse_submissions_document(payload, LOCATION)
    assert f"filings.unknown_{label}" in outcome.unknown_fields


def test_unknown_fields_reach_records_summary_and_hash() -> None:
    outcome, _ = parse_submissions_document(_nested_additions(), LOCATION)
    baseline, _ = parse_submissions_document(document(), LOCATION)
    registrant = outcome.records[0]
    assert "filings.newFilingsBlock" in registrant.unknown_fields
    assert "filings.newFilingsBlock" in outcome.summary()["unknown_field_paths"]
    assert "PARSER_SCHEMA_DRIFT_OBSERVED" in outcome.reason_codes
    assert registrant.record_sha256 != baseline.records[0].record_sha256


def test_record_hash_is_deterministic_and_covers_unknown_paths() -> None:
    first, _ = parse_submissions_document(_nested_additions(), LOCATION)
    second, _ = parse_submissions_document(_nested_additions(), LOCATION)
    assert first.records[0].record_sha256 == second.records[0].record_sha256
    assert record_hash({"a": 1}, ["x"]) != record_hash({"a": 1}, [])


def test_registered_structural_reason_codes_have_the_right_severity() -> None:
    for code in (
        "PARSER_STRUCTURE_ABSENT",
        "PARSER_STRUCTURE_NULL",
        "PARSER_STRUCTURE_WRONG_TYPE",
        "PARSER_STRUCTURE_MALFORMED",
        "PARSER_STRUCTURE_INDETERMINATE",
        "PARSER_HISTORICAL_REFERENCE_MALFORMED",
    ):
        assert REASON_CODES[code].blocks_release
        assert REASON_CODES[code].requires_manual_review
    assert not REASON_CODES["PARSER_STRUCTURE_VALID_EMPTY"].blocks_release
