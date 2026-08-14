"""The IN-3 2009/2010 support-target pair matrix (Decision 071 §6; §17 item L).

Every condition of the pair rule is negated **one at a time**, so no single condition can
be dropped without a test failing. A half pair -- either leg selected without the other --
must contribute nothing, which is the defect this rule exists to prevent.
"""

from __future__ import annotations

import pytest

from disclosure_drift.m3 import support_target_pairs as pairs


def _support(cik: int = 1, **overrides: object) -> pairs.PairedAccession:
    base: dict[str, object] = {
        "accession_plain": f"{cik:010d}09000001",
        "anchor_cik_numeric": cik,
        "accession_role": "support",
        "form_type": "10-K",
        "is_amendment": False,
        "official_filing_date": "2009-03-01",
        "provisional_official_cohort": None,
        "has_pre_study_reason": True,
    }
    base.update(overrides)
    return pairs.PairedAccession(**base)  # type: ignore[arg-type]


def _target(cik: int = 1, **overrides: object) -> pairs.PairedAccession:
    base: dict[str, object] = {
        "accession_plain": f"{cik:010d}10000002",
        "anchor_cik_numeric": cik,
        "accession_role": "base",
        "form_type": "10-K",
        "is_amendment": False,
        "official_filing_date": "2010-03-01",
        "provisional_official_cohort": "development",
        "has_pre_study_reason": False,
    }
    base.update(overrides)
    return pairs.PairedAccession(**base)  # type: ignore[arg-type]


def test_a_complete_pair_contributes_its_entity() -> None:
    assert pairs.support_target_pair_entities([_support(), _target()]) == (1,)


def test_a_support_leg_without_its_selected_target_contributes_nothing() -> None:
    assert pairs.support_target_pair_entities([_support()]) == ()


def test_a_target_leg_without_its_selected_support_contributes_nothing() -> None:
    assert pairs.support_target_pair_entities([_target()]) == ()


def test_legs_from_different_entities_do_not_pair() -> None:
    assert pairs.support_target_pair_entities([_support(cik=1), _target(cik=2)]) == ()


def test_several_pairs_for_one_entity_count_once() -> None:
    extra = _target(accession_plain="0000000001" + "10" + "000009")
    assert pairs.support_target_pair_entities([_support(), _target(), extra]) == (1,)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("accession_role", "base"),
        ("form_type", "10-KT"),
        ("is_amendment", True),
        ("official_filing_date", "2010-03-01"),
        ("official_filing_date", None),
        ("provisional_official_cohort", "development"),
        ("has_pre_study_reason", False),
    ],
)
def test_every_support_condition_is_load_bearing(field: str, value: object) -> None:
    """Negate one support-side condition at a time; the pair must disappear."""
    assert pairs.support_target_pair_entities([_support(**{field: value}), _target()]) == ()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("accession_role", "stress"),
        ("form_type", "10-K/A"),
        ("is_amendment", True),
        ("official_filing_date", "2011-03-01"),
        ("official_filing_date", None),
        ("provisional_official_cohort", "transition"),
        ("provisional_official_cohort", None),
    ],
)
def test_every_target_condition_is_load_bearing(field: str, value: object) -> None:
    """Negate one target-side condition at a time; the pair must disappear."""
    assert pairs.support_target_pair_entities([_support(), _target(**{field: value})]) == ()


def test_a_support_label_alone_is_not_proof_of_a_pair() -> None:
    """IN-3: ``support_eligible = support_2009`` was the defect this rule replaces."""
    labelled_only = [_support(cik=index) for index in range(1, 7)]
    assert pairs.support_target_pair_entities(labelled_only) == ()
    assert not pairs.pair_quota_satisfied(labelled_only)


def test_the_quota_needs_six_distinct_entities() -> None:
    five = [leg for cik in range(1, 6) for leg in (_support(cik=cik), _target(cik=cik))]
    assert not pairs.pair_quota_satisfied(five)
    six = [*five, _support(cik=6), _target(cik=6)]
    assert pairs.pair_quota_satisfied(six)
    assert pairs.support_target_pair_entities(six) == (1, 2, 3, 4, 5, 6)


def test_the_result_is_input_order_independent() -> None:
    legs = [_support(cik=2), _target(cik=1), _support(cik=1), _target(cik=2)]
    assert pairs.support_target_pair_entities(legs) == pairs.support_target_pair_entities(
        list(reversed(legs))
    )


def test_assembly_from_persisted_rows_fails_closed_on_a_missing_candidate() -> None:
    with pytest.raises(KeyError, match="no frozen candidate row"):
        pairs.paired_accessions_from_rows(
            [{"accession_plain": "x", "anchor_cik_numeric": 1, "accession_role": "base"}],
            {},
            (),
        )


def test_assembly_from_persisted_rows_reads_the_frozen_candidate_facts() -> None:
    assembled = pairs.paired_accessions_from_rows(
        [
            {
                "accession_plain": "0000000001090000012",
                "anchor_cik_numeric": 1,
                "accession_role": "support",
            }
        ],
        {
            "0000000001090000012": {
                "form_type": "10-K",
                "is_amendment": 0,
                "official_filing_date": "2009-03-01",
                "provisional_official_cohort": None,
            }
        },
        ("0000000001090000012",),
    )
    assert assembled[0].is_support_leg
