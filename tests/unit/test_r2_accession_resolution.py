"""Stage M2.2-R2.3: canonical accession fields resolve deterministically.

Decision 012. Every conflict class is run in **both** ingestion orders and must produce
identical canonical values, identical unresolved statuses, and identical resolution
hashes. Recency is never authority; equal authority with conflicting values stays
unresolved; identity-alias sources carry no filing-field authority.
"""

from __future__ import annotations

import itertools
from typing import Any

import pytest

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_resolution import (
    AUTHORITY_LEVEL,
    DEFERRED_AUTHORITY_CLASSES,
    MATERIAL_FIELDS,
    RESOLUTION_POLICY_VERSION,
    AccessionFieldObservation,
    authority_for_source,
    resolve_accession,
)

ACCESSION = "0000320193-24-000001"


def observation(
    observation_id: str,
    source_id: str,
    field_name: str,
    value: Any,
    **overrides: Any,
) -> AccessionFieldObservation:
    """Build one field observation with an explicit, non-ranking timestamp."""
    return AccessionFieldObservation(
        observation_id=observation_id,
        source_id=source_id,
        accession_plain=ACCESSION,
        field_name=field_name,
        value=value,
        observed_at_utc=overrides.pop("observed_at_utc", "2026-01-01T00:00:00Z"),
        **overrides,
    )


def both_orders(
    observations: list[AccessionFieldObservation],
    **kwargs: Any,
) -> tuple[Any, Any]:
    """Resolve the same set forwards and backwards."""
    forward = resolve_accession(ACCESSION, observations, **kwargs)
    backward = resolve_accession(ACCESSION, list(reversed(observations)), **kwargs)
    return forward, backward


# --------------------------------------------------------------------------- #
# Authority model
# --------------------------------------------------------------------------- #
def test_authority_levels_follow_decision_012() -> None:
    assert AUTHORITY_LEVEL["filing_level_metadata"] < AUTHORITY_LEVEL["entity_submissions"]
    assert AUTHORITY_LEVEL["entity_submissions"] < AUTHORITY_LEVEL["full_index"]
    assert AUTHORITY_LEVEL["full_index"] < AUTHORITY_LEVEL["identity_alias"]
    assert "filing_level_metadata" in DEFERRED_AUTHORITY_CLASSES


def test_an_unclassified_source_never_gets_a_default_authority() -> None:
    with pytest.raises(KeyError, match="no registered accession-authority class"):
        authority_for_source("some_new_source")


def test_material_fields_are_exactly_the_declared_set() -> None:
    assert {
        "form",
        "official_filing_date",
        "registrant_cik",
        "amendment_relationship",
    } == MATERIAL_FIELDS


def test_an_identity_alias_source_cannot_resolve_a_filing_field() -> None:
    forward, backward = both_orders([observation("A", "sec_company_tickers", "form", "10-K")])
    assert forward.fields["form"].status == "unresolved"
    assert forward.resolution_hash() == backward.resolution_hash()


def test_a_stronger_source_wins_without_creating_a_conflict() -> None:
    forward, backward = both_orders(
        [
            observation("A", "sec_full_index_company", "form", "10-K405"),
            observation("B", "sec_bulk_submissions", "form", "10-K"),
        ]
    )
    assert forward.fields["form"].status == "resolved"
    assert forward.fields["form"].value == "10-K"
    assert forward.fields["form"].authority == "entity_submissions"
    assert forward.resolution_hash() == backward.resolution_hash()


def test_a_later_ordinary_retrieval_does_not_win_on_recency() -> None:
    forward, backward = both_orders(
        [
            observation(
                "A",
                "sec_bulk_submissions",
                "official_filing_date",
                "2024-02-01",
                observed_at_utc="2026-01-01T00:00:00Z",
            ),
            observation(
                "B",
                "sec_bulk_submissions",
                "official_filing_date",
                "2024-03-01",
                observed_at_utc="2026-06-01T00:00:00Z",
            ),
        ]
    )
    assert forward.fields["official_filing_date"].status == "unresolved"
    assert forward.official_filing_cohort == "unresolved"
    assert forward.resolution_hash() == backward.resolution_hash()


# --------------------------------------------------------------------------- #
# Conflict classes, both orders
# --------------------------------------------------------------------------- #
def _corrected_filing_date() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "official_filing_date", "2024-02-01"),
        observation(
            "B",
            "sec_bulk_submissions",
            "official_filing_date",
            "2024-02-05",
            is_correction=True,
            correction_evidence_id="DAOC-1",
        ),
    ]


def _equal_authority_filing_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "official_filing_date", "2024-02-01"),
        observation("B", "sec_submissions_entity", "official_filing_date", "2024-03-01"),
    ]


def _form_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "form", "10-K"),
        observation("B", "sec_submissions_entity", "form", "10-K/A"),
    ]


def _registrant_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "registrant_cik", "0000320193"),
        observation("B", "sec_submissions_entity", "registrant_cik", "0000789019"),
    ]


def _submitter_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "submitter_cik", "0000320193"),
        observation("B", "sec_submissions_entity", "submitter_cik", "0000789019"),
    ]


def _report_date_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "report_date", "2023-09-30"),
        observation("B", "sec_submissions_entity", "report_date", "2023-12-31"),
    ]


def _acceptance_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "acceptance_timestamp", "2024-01-31T17:31:00"),
        observation("B", "sec_submissions_entity", "acceptance_timestamp", "2024-02-01T09:00:00"),
    ]


def _amendment_conflict() -> list[AccessionFieldObservation]:
    return [
        observation("A", "sec_bulk_submissions", "amendment_relationship", "original"),
        observation(
            "B", "sec_submissions_entity", "amendment_relationship", "amends:0000320193-23-000009"
        ),
    ]


@pytest.mark.parametrize(
    ("label", "factory", "kwargs"),
    [
        ("corrected filing date", _corrected_filing_date, {}),
        ("equal-authority filing date", _equal_authority_filing_conflict, {}),
        ("form", _form_conflict, {}),
        ("registrant", _registrant_conflict, {}),
        ("submitter", _submitter_conflict, {}),
        ("report date", _report_date_conflict, {}),
        ("acceptance timestamp", _acceptance_conflict, {}),
        ("amendment relationship", _amendment_conflict, {}),
        (
            "same-cohort correction",
            lambda: [
                observation(
                    "A",
                    "sec_bulk_submissions",
                    "official_filing_date",
                    "2024-05-01",
                    is_correction=True,
                    correction_evidence_id="C",
                )
            ],
            {"prior_filing_dates": ["2024-02-01"]},
        ),
        (
            "cross-cohort correction",
            lambda: [
                observation(
                    "A",
                    "sec_bulk_submissions",
                    "official_filing_date",
                    "2022-05-01",
                    is_correction=True,
                    correction_evidence_id="C",
                )
            ],
            {"prior_filing_dates": ["2021-12-30"]},
        ),
        (
            "entry into 2024",
            lambda: [
                observation(
                    "A",
                    "sec_bulk_submissions",
                    "official_filing_date",
                    "2024-01-02",
                    is_correction=True,
                    correction_evidence_id="C",
                )
            ],
            {"prior_filing_dates": ["2023-12-29"]},
        ),
        (
            "exit from 2024",
            lambda: [
                observation(
                    "A",
                    "sec_bulk_submissions",
                    "official_filing_date",
                    "2025-01-05",
                    is_correction=True,
                    correction_evidence_id="C",
                )
            ],
            {"prior_filing_dates": ["2024-12-31"]},
        ),
    ],
)
def test_every_conflict_class_is_order_independent(
    label: str,
    factory: Any,
    kwargs: dict[str, Any],
) -> None:
    forward, backward = both_orders(factory(), **kwargs)
    assert forward.resolution_hash() == backward.resolution_hash(), label
    assert forward.as_record() == backward.as_record(), label
    assert forward.unresolved_fields == backward.unresolved_fields, label
    assert forward.official_filing_cohort == backward.official_filing_cohort, label


def test_all_permutations_of_a_mixed_set_agree() -> None:
    observations = [
        observation("A", "sec_bulk_submissions", "official_filing_date", "2024-02-01"),
        observation(
            "B",
            "sec_bulk_submissions",
            "official_filing_date",
            "2024-02-05",
            is_correction=True,
            correction_evidence_id="D",
        ),
        observation("C", "sec_full_index_company", "form", "10-K405"),
        observation("D", "sec_bulk_submissions", "form", "10-K"),
    ]
    hashes = {
        resolve_accession(ACCESSION, list(order)).resolution_hash()
        for order in itertools.permutations(observations)
    }
    assert len(hashes) == 1


# --------------------------------------------------------------------------- #
# Statuses and consequences
# --------------------------------------------------------------------------- #
def test_a_correction_resolves_and_records_its_evidence() -> None:
    resolution, _ = both_orders(_corrected_filing_date())
    filing = resolution.fields["official_filing_date"]
    assert filing.status == "resolved_by_correction"
    assert filing.value == "2024-02-05"
    assert filing.correction_evidence_id == "DAOC-1"
    assert set(filing.competing_observation_ids) == {"A", "B"}


def test_an_equal_authority_conflict_blocks_a_material_field() -> None:
    resolution, _ = both_orders(_equal_authority_filing_conflict())
    filing = resolution.fields["official_filing_date"]
    assert filing.status == "unresolved"
    assert filing.blocks_dependents
    assert "ACCESSION_FIELD_UNRESOLVED_EQUAL_AUTHORITY" in filing.reason_codes
    assert "ACCESSION_FIELD_CONFLICT_MATERIAL" in filing.reason_codes
    assert resolution.blocking_fields == ("official_filing_date",)


def test_a_non_material_conflict_is_reviewed_but_does_not_block() -> None:
    resolution, _ = both_orders(_report_date_conflict())
    report = resolution.fields["report_date"]
    assert report.status == "unresolved"
    assert not report.blocks_dependents
    assert "ACCESSION_FIELD_CONFLICT_NON_MATERIAL" in report.reason_codes
    assert REASON_CODES["ACCESSION_FIELD_CONFLICT_NON_MATERIAL"].requires_manual_review
    assert not REASON_CODES["ACCESSION_FIELD_CONFLICT_NON_MATERIAL"].blocks_release


def test_a_registrant_conflict_never_merges_ciks() -> None:
    resolution, _ = both_orders(_registrant_conflict())
    assert resolution.fields["registrant_cik"].status == "unresolved"
    assert "ACCESSION_REGISTRANT_CONFLICT_PRESERVED" in resolution.reason_codes
    assert set(resolution.fields["registrant_cik"].competing_observation_ids) == {"A", "B"}


def test_a_submitter_differing_from_the_registrant_is_a_review_signal() -> None:
    resolution, _ = both_orders(
        [
            observation("A", "sec_bulk_submissions", "registrant_cik", "0000320193"),
            observation("B", "sec_bulk_submissions", "submitter_cik", "0000789019"),
        ]
    )
    assert "ACCESSION_SUBMITTER_DIFFERS_FROM_REGISTRANT" in resolution.reason_codes


@pytest.mark.parametrize(
    ("prior", "corrected", "expected_cohort", "needs_approval"),
    [
        (["2024-02-01"], "2024-05-01", "primary_test", False),
        (["2021-12-30"], "2022-05-01", "transition", False),
        (["2023-12-29"], "2024-01-02", "primary_test", True),
        (["2024-12-31"], "2025-01-05", "prospective", True),
    ],
)
def test_filing_date_corrections_recompute_cohorts_and_gate_2024(
    prior: list[str],
    corrected: str,
    expected_cohort: str,
    needs_approval: bool,
) -> None:
    resolution, backward = both_orders(
        [
            observation(
                "A",
                "sec_bulk_submissions",
                "official_filing_date",
                corrected,
                is_correction=True,
                correction_evidence_id="C",
            )
        ],
        prior_filing_dates=prior,
    )
    assert resolution.official_filing_cohort == expected_cohort
    assert resolution.requires_2024_approval is needs_approval
    assert resolution.prior_filing_cohorts
    assert resolution.resolution_hash() == backward.resolution_hash()
    if needs_approval:
        assert "ACCESSION_2024_COHORT_TRANSITION_REQUIRES_APPROVAL" in resolution.reason_codes


def test_an_approved_2024_transition_is_recorded_but_not_blocked() -> None:
    resolution, _ = both_orders(
        [
            observation(
                "A",
                "sec_bulk_submissions",
                "official_filing_date",
                "2024-01-02",
                is_correction=True,
                correction_evidence_id="C",
            )
        ],
        prior_filing_dates=["2023-12-29"],
        approved_2024_transition=True,
    )
    assert not resolution.requires_2024_approval
    assert resolution.cohort_boundary_crossed
    assert "ACCESSION_COHORT_BOUNDARY_CROSSED" in resolution.reason_codes


def test_the_policy_version_is_recorded_on_every_resolution() -> None:
    resolution, _ = both_orders(_form_conflict())
    assert resolution.as_record()["policy_version"] == RESOLUTION_POLICY_VERSION
    assert resolution.fields["form"].as_record()["policy_version"] == RESOLUTION_POLICY_VERSION


def test_an_absent_field_is_distinct_from_an_unresolved_one() -> None:
    resolution, _ = both_orders([observation("A", "sec_bulk_submissions", "form", "10-K")])
    assert resolution.fields["report_date"].status == "absent"
    assert not resolution.fields["report_date"].blocks_dependents
    assert resolution.fields["form"].status == "resolved"
