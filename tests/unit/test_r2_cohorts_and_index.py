"""Stage M2.2-R2.4 and R2.5: cohort labels and full-index reconciliation.

R2.4 — four meanings must stay distinct in the catalog: ``support_2009`` (support only),
the five frozen analysis cohorts, ``out_of_scope`` (a valid resolved date outside every
supported window), and ``unresolved`` (the date itself is unknown). A valid date is
never persisted as ``NULL`` merely for falling outside the analysis cohorts.

R2.5 — the quarterly company index is a coverage check. It never merges identities,
never deletes a record, and never yields a filing-document URL.
"""

from __future__ import annotations

import itertools
from typing import Any

import pytest

from disclosure_drift.cohorts import COHORT_ORDER
from disclosure_drift.sec.index_reconciliation import (
    APPROVED_FORMS,
    IndexInstance,
    SubmissionsAccession,
    reconcile_index,
)
from disclosure_drift.sec.parsers.base import RecordLocation
from disclosure_drift.sec.parsers.full_index import REGION_INDEX_ROWS, parse_company_index
from disclosure_drift.sec.temporal import (
    OUT_OF_SCOPE_COHORT,
    SUPPORT_2009_COHORT,
    UNRESOLVED_COHORT,
    cohort_label_for_value,
)

INDEX_LOCATION = RecordLocation(observation_id="obs-idx", source_id="sec_full_index_company")

INDEX_TEXT = """\
Company Name        Form Type  CIK     Date Filed  File Name
-----------------------------------------------------------------------------
SYNTHETIC ONE INC   10-K       320193  2024-02-01  d/0000320193-24-000001.txt
SYNTHETIC TWO INC   10-K/A     789019  2024-03-01  d/0000789019-24-000002.txt
SYNTHETIC THREE INC 10-KT      111111  2024-04-01  d/0000111111-24-000003.txt
CONTROL CORP        8-K        222222  2024-05-01  d/0000222222-24-000004.txt
BROKEN ROW
SYNTHETIC ONE INC   10-K       320193  2024-02-01  d/0000320193-24-000001.txt
"""


# --------------------------------------------------------------------------- #
# R2.4 cohort labels
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("day", "expected"),
    [
        ("2008-12-31", OUT_OF_SCOPE_COHORT),
        ("2009-01-01", SUPPORT_2009_COHORT),
        ("2009-12-31", SUPPORT_2009_COHORT),
        ("2010-01-01", "development"),
        ("2021-12-31", "development"),
        ("2022-01-01", "transition"),
        ("2023-12-31", "transition"),
        ("2024-01-01", "primary_test"),
        ("2024-12-31", "primary_test"),
        ("2025-01-01", "prospective"),
        ("2025-12-31", "prospective"),
        ("2026-01-01", "monitoring"),
        ("2026-12-31", "monitoring"),
        ("2027-01-01", OUT_OF_SCOPE_COHORT),
    ],
)
def test_every_cohort_boundary_gets_a_concrete_label(day: str, expected: str) -> None:
    assert cohort_label_for_value(day) == expected


@pytest.mark.parametrize("value", [None, "", "   ", "not-a-date", "2024-13-45"])
def test_an_unresolvable_date_is_unresolved_not_out_of_scope(value: Any) -> None:
    assert cohort_label_for_value(value) == UNRESOLVED_COHORT


def test_a_valid_date_is_never_labelled_unresolved() -> None:
    for day in ("2008-06-01", "2009-06-01", "2027-06-01"):
        assert cohort_label_for_value(day) != UNRESOLVED_COHORT


def test_out_of_scope_and_unresolved_are_different_meanings() -> None:
    assert cohort_label_for_value("2008-01-01") != cohort_label_for_value(None)


def test_support_2009_is_not_one_of_the_five_analysis_cohorts() -> None:
    assert SUPPORT_2009_COHORT not in COHORT_ORDER
    assert OUT_OF_SCOPE_COHORT not in COHORT_ORDER
    assert UNRESOLVED_COHORT not in COHORT_ORDER
    assert len(COHORT_ORDER) == 5


def test_a_date_object_is_accepted_as_well_as_text() -> None:
    from datetime import date

    assert cohort_label_for_value(date(2024, 6, 1)) == "primary_test"


# --------------------------------------------------------------------------- #
# R2.5 index parsing
# --------------------------------------------------------------------------- #
def test_index_rows_parse_with_normalized_fields() -> None:
    outcome = parse_company_index(INDEX_TEXT, INDEX_LOCATION)
    usable = [
        record.payload
        for record in outcome.records
        if not record.payload["problems"] and record.payload["accession_plain"]
    ]
    assert len(usable) == 5
    first = usable[0]
    assert first["company_name"] == "SYNTHETIC ONE INC"
    assert first["form_type"] == "10-K"
    assert first["cik_padded"] == "0000320193"
    assert first["date_filed"] == "2024-02-01"
    assert first["accession_plain"] == "0000320193-24-000001"


def test_no_filing_document_url_is_ever_constructed() -> None:
    outcome = parse_company_index(INDEX_TEXT, INDEX_LOCATION)
    for record in outcome.records:
        for key, value in record.payload.items():
            if key == "raw_line":
                continue
            assert "http" not in str(value).lower()
            assert "sec.gov" not in str(value).lower()


def test_a_malformed_index_row_is_retained_and_quarantined() -> None:
    outcome = parse_company_index(INDEX_TEXT, INDEX_LOCATION)
    broken = [
        record for record in outcome.records if "BROKEN ROW" in str(record.payload["raw_line"])
    ]
    assert broken
    assert broken[0].payload["problems"]
    assert outcome.quarantined


def test_duplicate_index_rows_are_retained() -> None:
    outcome = parse_company_index(INDEX_TEXT, INDEX_LOCATION)
    duplicated = [
        record
        for record in outcome.records
        if record.payload["accession_plain"] == "0000320193-24-000001"
    ]
    assert len(duplicated) == 2
    assert outcome.duplicate_identities


def test_a_structurally_valid_index_with_no_rows_is_a_real_zero() -> None:
    outcome = parse_company_index(
        "Company Name Form Type CIK Date Filed File Name\n--------------------\n",
        INDEX_LOCATION,
    )
    assert outcome.region_state(REGION_INDEX_ROWS) == "valid_empty"
    assert outcome.counts_are_trustworthy


def test_an_index_without_a_separator_is_not_an_empty_quarter() -> None:
    outcome = parse_company_index("garbage with no separator", INDEX_LOCATION)
    assert outcome.region_state(REGION_INDEX_ROWS) == "wrong_type"
    assert not outcome.counts_are_trustworthy


# --------------------------------------------------------------------------- #
# R2.5 reconciliation
# --------------------------------------------------------------------------- #
def index_rows() -> list[dict[str, Any]]:
    """Parsed index payloads for the fixture."""
    outcome = parse_company_index(INDEX_TEXT, INDEX_LOCATION)
    return [dict(record.payload) for record in outcome.records]


def submissions_side() -> list[SubmissionsAccession]:
    """Submissions-derived accessions covering every comparison state."""
    return [
        SubmissionsAccession("0000320193-24-000001", "10-K", "0000320193", "2024-02-01", "obs-sub"),
        # form conflict: index says 10-K/A
        SubmissionsAccession("0000789019-24-000002", "10-K", "0000789019", "2024-03-01", "obs-sub"),
        SubmissionsAccession(
            "0000111111-24-000003", "10-KT", "0000111111", "2024-04-01", "obs-sub"
        ),
        # submissions only
        SubmissionsAccession("0000999999-24-000009", "10-K", "0000999999", "2024-06-01", "obs-sub"),
    ]


def required_instances() -> list[IndexInstance]:
    """One satisfied instance and one missing instance."""
    return [
        IndexInstance(2024, 1, retrieved=True, parse_usable=True, observation_id="obs-idx"),
        IndexInstance(2024, 2),
    ]


def test_all_six_reconciliation_states_are_produced() -> None:
    report = reconcile_index(
        index_rows(),
        submissions_side(),
        required_instances=required_instances(),
        index_observation_id="obs-idx",
    )
    counts = report.counts
    assert counts["matching"] >= 1
    assert counts["index_only"] == 1
    assert counts["submissions_only"] == 1
    assert counts["conflicting"] == 1
    assert counts["unavailable"] == 1
    assert counts["indeterminate"] == 1


def test_a_field_conflict_names_the_field_and_keeps_both_sides() -> None:
    report = reconcile_index(index_rows(), submissions_side(), index_observation_id="obs-idx")
    conflict = next(item for item in report.outcomes if item.state == "conflicting")
    assert conflict.conflicting_fields == ("form_type",)
    assert conflict.index_values["form_type"] == "10-K/A"
    assert conflict.submissions_values["form_type"] == "10-K"
    assert conflict.index_observation_id == "obs-idx"
    assert conflict.submissions_observation_id == "obs-sub"


def test_a_missing_required_instance_blocks_completion() -> None:
    report = reconcile_index(
        index_rows(),
        submissions_side(),
        required_instances=required_instances(),
        index_observation_id="obs-idx",
    )
    assert report.missing_instances == ("2024QTR2",)
    assert report.blocks_completion
    assert "INDEX_REQUIRED_INSTANCE_MISSING" in report.reason_codes
    assert "INDEX_INSTANCE_UNAVAILABLE" in report.reason_codes


def test_all_required_instances_present_does_not_block() -> None:
    report = reconcile_index(
        index_rows(),
        submissions_side(),
        required_instances=[
            IndexInstance(2024, 1, retrieved=True, parse_usable=True, observation_id="obs-idx")
        ],
        index_observation_id="obs-idx",
    )
    assert report.missing_instances == ()
    assert not report.blocks_completion


def test_a_retrieved_but_unparsable_instance_still_blocks() -> None:
    report = reconcile_index(
        [],
        [],
        required_instances=[IndexInstance(2024, 1, retrieved=True, parse_usable=False)],
    )
    assert report.missing_instances == ("2024QTR1",)
    assert report.blocks_completion


def test_control_forms_are_retained_but_not_eligibility_evidence() -> None:
    report = reconcile_index(index_rows(), submissions_side(), index_observation_id="obs-idx")
    control = next(
        item for item in report.outcomes if item.accession_plain == "0000222222-24-000004"
    )
    assert control.state == "index_only"
    assert control.index_values["form_type"] == "8-K"
    assert not control.is_approved_form


@pytest.mark.parametrize("form", sorted(APPROVED_FORMS))
def test_approved_forms_are_marked_for_eligibility_comparison(form: str) -> None:
    report = reconcile_index(
        [
            {
                "accession_plain": "0000320193-24-000099",
                "form_type": form,
                "cik_padded": "0000320193",
                "date_filed": "2024-02-01",
                "line_number": 3,
                "problems": [],
            }
        ],
        [],
    )
    assert report.outcomes[0].is_approved_form


def test_amendments_and_transition_reports_reconcile_as_themselves() -> None:
    report = reconcile_index(index_rows(), submissions_side(), index_observation_id="obs-idx")
    transition = next(
        item for item in report.outcomes if item.accession_plain == "0000111111-24-000003"
    )
    assert transition.state == "matching"
    assert transition.index_values["form_type"] == "10-KT"
    assert transition.is_approved_form


def test_reconciliation_is_order_independent() -> None:
    rows = index_rows()[:4]
    subs = submissions_side()
    instances = required_instances()
    hashes = {
        reconcile_index(
            list(order),
            list(sub_order),
            required_instances=list(instance_order),
            index_observation_id="obs-idx",
        ).reconciliation_hash()
        for order in itertools.permutations(rows)
        for sub_order in (subs, list(reversed(subs)))
        for instance_order in (instances, list(reversed(instances)))
    }
    assert len(hashes) == 1


def test_reconciliation_never_deletes_or_merges() -> None:
    report = reconcile_index(
        index_rows(),
        submissions_side(),
        required_instances=required_instances(),
        index_observation_id="obs-idx",
    )
    # Every index accession and every submissions accession still appears somewhere.
    seen = {item.accession_plain for item in report.outcomes}
    for accession in (
        "0000320193-24-000001",
        "0000789019-24-000002",
        "0000111111-24-000003",
        "0000222222-24-000004",
        "0000999999-24-000009",
    ):
        assert accession in seen
