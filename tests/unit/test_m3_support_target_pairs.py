"""The IN-3 2009/2010 support-target pair matrix (Decision 071 §6).

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


# ==========================================================================
# Accepted Decision 084 R66 -- the joint 2009/2010 pair, proofs A through E
#
# Under accepted Decision 083 R58 a jointly filed accession has NO anchor, and under
# R62 it belongs to every substantive registrant's history. These five proofs are the
# exact obligations R66 states, held against the pure rule.
# ==========================================================================


def test_r66_a_a_joint_pair_reaches_every_substantive_entity() -> None:
    """**A.** A joint pair receives truthful entity-domain attribution.

    Both legs are jointly filed by CIK 1 and CIK 901 and neither carries an anchor. Both
    entities genuinely filed both legs, so both contribute -- and no CIK is designated.
    """
    support = _support(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    target = _target(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    assert pairs.support_target_pair_entities([support, target]) == (1, 901)


def test_r66_b_a_joint_pair_is_still_one_accession_each_side() -> None:
    """**B.** No duplicate accession-domain credit.

    Entity-domain attribution reaching two entities must not multiply the accessions.
    Each leg is one accession however many registrants it carries, and repeating the same
    accession in the input cannot manufacture a second one.
    """
    support = _support(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    target = _target(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    entities = pairs.support_target_pair_entities([support, target])
    # Two entities, from exactly two distinct accessions.
    assert entities == (1, 901)
    assert len({support.accession_plain, target.accession_plain}) == 2
    # Decision 018 §16 counts DISTINCT entities: repeating the legs changes nothing.
    assert pairs.support_target_pair_entities([support, target, support, target]) == (1, 901)


def test_r66_c_joint_pair_attribution_is_order_invariant() -> None:
    """**C.** Insertion and order invariance.

    Neither the order of the legs nor the order of the association set may change the
    result -- which is what makes first-write, row-order, and archive-order attribution
    unreconstructable from the output.
    """
    support_forward = _support(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    target_forward = _target(anchor_cik_numeric=None, substantive_registrant_ciks=(1, 901))
    support_reverse = _support(anchor_cik_numeric=None, substantive_registrant_ciks=(901, 1))
    target_reverse = _target(anchor_cik_numeric=None, substantive_registrant_ciks=(901, 1, 901))
    expected = (1, 901)
    assert pairs.support_target_pair_entities([support_forward, target_forward]) == expected
    assert pairs.support_target_pair_entities([target_forward, support_forward]) == expected
    assert pairs.support_target_pair_entities([support_reverse, target_reverse]) == expected
    assert pairs.support_target_pair_entities([target_reverse, support_reverse]) == expected


def test_r66_d_an_unestablished_association_set_grants_zero_pair_credit() -> None:
    """**D.** An unestablished set fails closed at zero credit.

    An accession with no anchor and no supplied association set names no entity, and the
    rule refuses to invent one. Fail-closed in the safe direction: a hard quota only ever
    gets harder to satisfy.
    """
    support = _support(anchor_cik_numeric=None, substantive_registrant_ciks=())
    target = _target(anchor_cik_numeric=None, substantive_registrant_ciks=())
    assert support.contributing_ciks == ()
    assert target.contributing_ciks == ()
    assert pairs.support_target_pair_entities([support, target]) == ()
    # And a legitimate half pair beside it still contributes nothing on its own.
    assert pairs.support_target_pair_entities([support, target, _target(cik=2)]) == ()


def test_r66_e_established_single_registrant_pair_behaviour_is_unchanged() -> None:
    """**E.** Established single-registrant behaviour does not change.

    The anchor is the whole substantive set, so the result is identical whether the set
    is stated explicitly or left to the anchor alone.
    """
    anchor_only = pairs.support_target_pair_entities([_support(cik=1), _target(cik=1)])
    stated = pairs.support_target_pair_entities(
        [
            _support(cik=1, substantive_registrant_ciks=(1,)),
            _target(cik=1, substantive_registrant_ciks=(1,)),
        ]
    )
    assert anchor_only == (1,)
    assert stated == anchor_only


def test_r66_the_caller_supplied_association_set_is_what_reaches_the_rule() -> None:
    """The R66 caller correction, at the assembly boundary it fixes.

    ``paired_accessions_from_rows`` must carry the supplied set onto the leg. Without it
    an anchorless row contributes nothing -- which is the Decision 083 MINOR-1 defect this
    ruling closes.
    """
    rows = [
        {
            "accession_plain": "0000000001090000012",
            "anchor_cik_numeric": None,
            "accession_role": "support",
        }
    ]
    candidates = {
        "0000000001090000012": {
            "form_type": "10-K",
            "is_amendment": 0,
            "official_filing_date": "2009-03-01",
            "provisional_official_cohort": None,
        }
    }
    without = pairs.paired_accessions_from_rows(rows, candidates, ("0000000001090000012",))
    assert without[0].is_support_leg
    assert without[0].contributing_ciks == ()

    with_set = pairs.paired_accessions_from_rows(
        rows, candidates, ("0000000001090000012",), {"0000000001090000012": (1, 901)}
    )
    assert with_set[0].is_support_leg
    assert with_set[0].contributing_ciks == (1, 901)
    assert with_set[0].anchor_cik_numeric is None
