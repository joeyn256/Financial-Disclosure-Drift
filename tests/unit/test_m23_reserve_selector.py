"""S5.4 -- pure reserve construction: adversarial suite.

Pure-Python, in-memory tests only. No SQLite, no network, no filing text, no
outcomes, no clock, no randomness outside a fixed local test seed. Factories here
build *input objects only*: none of them computes, copies, or pre-bakes a
production-derived expected answer.

Every fixture is a spare candidate deliberately given a non-zero entity evidence
penalty, so objective term 2 keeps it out of the accepted selection and it remains
available as a replacement. Entity evidence penalty is a selection-objective term
and is deliberately **not** one of Decision 016 section 7's signature inputs, so a
dispreferred candidate can still be a compatible reserve.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import random
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.pilot_policy import (
    PILOT_QUOTA_POLICY_VERSION,
    PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION,
)
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_selector import (
    ACCESSION_CAP_LIMITS,
    MAX_BASE_ACCESSIONS_PER_CIK,
    NOT_APPLICABLE,
    QUOTA_DIMENSION_CROSS_CUTTING,
    QUOTA_KEY_BASE_ACCESSIONS_PER_CIK,
    AccessionCandidate,
    EntityCandidate,
    JointSelectionResult,
    NameChangeEvidence,
    QuotaContributionMembership,
    accession_caps_satisfied,
    official_filing_year,
    solve_joint_selection,
)
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    OPERATING_FINANCIAL_INDUSTRY,
    PILOT_SELECTION_SEED,
    TOTAL_OPERATING,
    Candidate,
    selection_rank,
)
from disclosure_drift.sec.reserve_selector import (
    EVIDENCE_LEVEL_PRECEDENCE,
    NO_COMPATIBLE_RESERVE_REASON_CODE,
    RESERVE_RANK,
    ReserveAccession,
    ReserveConstruction,
    ReservePackage,
    _bundle_filing_year,
    _bundle_for,
    _CandidateProfile,
    _caps_preserved,
    _usage_from,
    build_reserve_packages,
)

_RESERVE_SELECTOR_SOURCE: Final = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "disclosure_drift"
    / "sec"
    / "reserve_selector.py"
)

GENEROUS_NODE_LIMIT: Final = 5_000_000
RUN_ID: Final = "r" * 64
SNAPSHOT_ID: Final = "a" * 64

SIZE_SEQUENCE: Final = (
    ["large_accelerated"] * 7 + ["accelerated"] * 7 + ["non_accelerated_or_smaller"] * 6
)
INDUSTRY_SEQUENCE: Final = (
    ["technology_and_communications"] * 4
    + [OPERATING_FINANCIAL_INDUSTRY] * 4
    + ["industrial_and_materials"] * 3
    + ["consumer_retail_and_services"] * 3
    + ["healthcare_and_life_sciences"] * 3
    + ["energy_and_utilities"] * 3
)
HISTORY_SEQUENCE: Final = ["stable"] * 10 + ["eventful"] * 10
PURPOSE_CATEGORIES: Final = (
    "administrative_or_exhibit",
    "financial_or_xbrl_correction",
    "narrative_or_governance",
)

#: Operating slot 18 -- a plain entity whose only accession is one 2018 Inline-XBRL
#: base original, so its complete contribution set is a single quota.
PLAIN_SLOT: Final = 18
#: Operating slot 6 -- a 2024 base original plus a linked 10-KT/A, so its
#: contribution set spans linked-amendment, amendment-purpose, transition-report,
#: fiscal-year-end, Inline-XBRL, and 2024-original coverage.
AMENDMENT_SLOT: Final = 6
PLAIN_TARGETS: Final = ("0000000019", "0000000020")
AMENDMENT_TARGET: Final = "0000000007"


# --------------------------------------------------------------------------
# Input factories -- objects only, never expected answers
# --------------------------------------------------------------------------


def mk_operating(cik: int, slot: int, *, evidence_penalty: int = 0) -> Candidate:
    industry = INDUSTRY_SEQUENCE[slot]
    history = HISTORY_SEQUENCE[slot]
    financial = industry == OPERATING_FINANCIAL_INDUSTRY
    return Candidate(
        cik_padded=f"{cik:010d}",
        filing_time_name=f"Synthetic Issuer {cik}",
        category="operating",
        primary_universe_eligible=not financial,
        engineering_only_stress=financial,
        size_stratum=SIZE_SEQUENCE[slot],
        size_evidence_level="provisional",
        industry_group=industry,
        industry_evidence_level="provisional",
        industry_quota_eligible=True,
        history_class=history,
        history_evidence_level="provisional",
        currently_inactive=history == "eventful" and 10 <= slot < 10 + MIN_INACTIVE_EVENTFUL,
        evidence_penalty=evidence_penalty,
    )


def mk_control(cik: int, kind: str, *, evidence_penalty: int = 0) -> Candidate:
    return Candidate(
        cik_padded=f"{cik:010d}",
        filing_time_name=f"Synthetic Control {cik}",
        category="control",
        control_kind=kind,
        primary_universe_eligible=False,
        evidence_penalty=evidence_penalty,
    )


def winning_former_name() -> NameChangeEvidence:
    return NameChangeEvidence(
        has_identity_evidence=True,
        evidence_role="winning",
        evidence_level="provisional",
        former_name_record_parseable=True,
        has_prior_current_or_from_to=True,
    )


def dashed(cik: int, year: int, seq: int) -> str:
    return f"{cik:010d}-{year % 100:02d}-{seq:06d}"


#: **Decision 083 R58**: ``multi_registrant`` is not a free-standing flag -- it IS the
#: distinct substantive association-set cardinality. A fixture that wants a
#: multi-registrant accession must therefore state the SET: no anchor, and a real
#: co-registrant. This offset keeps the synthetic co-registrant CIK clear of the
#: fixture's own entity CIKs.
_CO_REGISTRANT_OFFSET = 900


def _multi_registrant_set(cik: int, multi_registrant: bool) -> tuple[int | None, tuple[int, ...]]:
    """The (anchor, substantive set) pair for one fixture accession."""
    if not multi_registrant:
        return cik, ()
    return None, (cik, _CO_REGISTRANT_OFFSET + cik)


def mk_accession(
    cik: int,
    year: int,
    seq: int,
    *,
    form: str = "10-K",
    role: str = "base",
    inline: bool = True,
    has_xbrl: bool | None = None,
    cohort: str | None = "development",
    pre_study: bool = False,
    parent: str | None = None,
    purpose: str | None = None,
    multi_registrant: bool = False,
    filing_level: str = "provisional",
    cohort_level: str = "provisional",
    xbrl_level: str = "provisional",
) -> AccessionCandidate:
    number = dashed(cik, year, seq)
    is_amendment = form.endswith("/A")
    anchor, substantive = _multi_registrant_set(cik, multi_registrant)
    return AccessionCandidate(
        accession_plain=number.replace("-", ""),
        accession_number_dashed=number,
        anchor_cik_numeric=anchor,
        substantive_registrant_ciks=substantive,
        form_type=form,
        is_amendment=is_amendment,
        official_filing_date=f"{year}-03-15",
        report_date=f"{year - 1}-12-31",
        cohort_applicability="pre_study" if pre_study else "applies",
        provisional_official_cohort=None if pre_study else cohort,
        filing_date_evidence_level=filing_level,
        cohort_evidence_level=NOT_APPLICABLE if pre_study else cohort_level,
        xbrl_evidence_level=xbrl_level,
        amendment_purpose_evidence_level="provisional" if is_amendment else NOT_APPLICABLE,
        amendment_linkage_evidence_level="provisional" if is_amendment else NOT_APPLICABLE,
        multi_registrant_evidence_level="provisional" if multi_registrant else NOT_APPLICABLE,
        has_xbrl=inline if has_xbrl is None else has_xbrl,
        has_inline_xbrl=inline,
        amendment_linkage_state="amends_original" if is_amendment else None,
        provisional_parent_accession_dashed=parent,
        amendment_purpose_category=purpose,
        amendment_purpose_quota_eligible=purpose is not None,
        base_eligible=role == "base",
        stress_eligible=role == "stress",
        support_eligible=role == "support",
        control_eligible=role == "control",
        multi_registrant=multi_registrant,
    )


@dataclass
class Pool:
    """A mutable pool under construction. Inputs only; no expected answers."""

    entities: list[EntityCandidate]
    accessions: list[AccessionCandidate]

    def solve(self, *, node_limit: int = GENEROUS_NODE_LIMIT) -> JointSelectionResult:
        return solve_joint_selection(self.entities, self.accessions, node_limit=node_limit)

    def add_spare_operating(
        self, cik: int, slot: int, accessions: list[AccessionCandidate]
    ) -> None:
        self.entities.append(
            EntityCandidate(mk_operating(cik, slot, evidence_penalty=1), NameChangeEvidence())
        )
        self.accessions.extend(accessions)

    def add_spare_control(self, cik: int, kind: str, accessions: list[AccessionCandidate]) -> None:
        self.entities.append(EntityCandidate(mk_control(cik, kind, evidence_penalty=1)))
        self.accessions.extend(accessions)


def base_pool() -> Pool:
    """The accepted tight, fully feasible pool: 20 operating entities and 4 controls.

    Structurally identical to the accepted S5.1 fixture, so a reserve is built
    against exactly the selection that suite already pins.
    """
    entities: list[EntityCandidate] = []
    accessions: list[AccessionCandidate] = []
    for slot in range(TOTAL_OPERATING):
        cik = slot + 1
        entities.append(
            EntityCandidate(
                mk_operating(cik, slot),
                winning_former_name() if slot < 4 else NameChangeEvidence(),
            )
        )
        if slot < 6:
            accessions.append(
                mk_accession(
                    cik, 2009, 1, role="support", inline=False, has_xbrl=False, pre_study=True
                )
            )
            base = mk_accession(
                cik, 2010, 2, role="base", inline=False, has_xbrl=True, cohort="development"
            )
        elif slot < 12:
            base = mk_accession(cik, 2024, 2, role="base", inline=True, cohort="primary_test")
        elif slot < 16:
            base = mk_accession(cik, 2025, 2, role="base", inline=True, cohort="prospective")
        else:
            base = mk_accession(
                cik, 2018, 2, role="base", inline=True, multi_registrant=slot in (16, 17)
            )
        accessions.append(base)
        if slot < 8:
            accessions.append(
                mk_accession(
                    cik,
                    2021,
                    3,
                    form="10-KT/A" if slot >= 5 else "10-K/A",
                    role="stress",
                    inline=True,
                    cohort="development",
                    parent=base.accession_number_dashed,
                    purpose=PURPOSE_CATEGORIES[slot % 3],
                )
            )
    for offset, kind in enumerate(CONTROL_QUOTAS):
        cik = 101 + offset
        entities.append(EntityCandidate(mk_control(cik, kind)))
        accessions.append(mk_accession(cik, 2020, 2, role="control", inline=True))
    return Pool(entities=entities, accessions=accessions)


def plain_spare_accessions(cik: int, **overrides: object) -> list[AccessionCandidate]:
    """One 2018 Inline-XBRL base original -- the plain-slot contribution shape."""
    return [mk_accession(cik, 2018, 2, role="base", inline=True, **overrides)]  # type: ignore[arg-type]


def amendment_spare_accessions(
    cik: int, *, parent_present: bool = True, purpose: str = PURPOSE_CATEGORIES[0]
) -> list[AccessionCandidate]:
    """A 2024 base original plus a linked 10-KT/A -- the amendment-slot shape."""
    base = mk_accession(cik, 2024, 2, role="base", inline=True, cohort="primary_test")
    amendment = mk_accession(
        cik,
        2025,
        3,
        form="10-KT/A",
        role="stress",
        inline=True,
        cohort="development",
        parent=base.accession_number_dashed if parent_present else dashed(999, 2000, 1),
        purpose=purpose,
    )
    return [base, amendment]


def construct(pool: Pool, **overrides: object) -> tuple[JointSelectionResult, ReserveConstruction]:
    result = pool.solve()
    assert result.status == "feasible"
    kwargs: dict[str, object] = {"selection_run_id": RUN_ID, "snapshot_id": SNAPSHOT_ID}
    kwargs.update(overrides)
    construction = build_reserve_packages(
        pool.entities,
        pool.accessions,
        result,
        **kwargs,  # type: ignore[arg-type]
    )
    return result, construction


def pool_with_plain_spare(cik: int = 300, **overrides: object) -> Pool:
    pool = base_pool()
    pool.add_spare_operating(cik, PLAIN_SLOT, plain_spare_accessions(cik, **overrides))
    return pool


def equally_weakened_pool(level: str = "conflicting") -> Pool:
    """Both plain targets and their spare carry the same weakened filing evidence.

    Weakening only one side changes the evidence floor and is refused; weakening
    both makes the package compatible again, so the floor a compatible package
    records can be observed directly rather than only through a refusal.
    """
    pool = base_pool()
    for cik in (19, 20):
        for index, accession in enumerate(pool.accessions):
            if accession.accession_number_dashed == dashed(cik, 2018, 2):
                pool.accessions[index] = dataclasses.replace(
                    accession, filing_date_evidence_level=level
                )
    pool.add_spare_operating(308, PLAIN_SLOT, plain_spare_accessions(308, filing_level=level))
    return pool


def package_for(construction: ReserveConstruction, target: str) -> ReservePackage | None:
    return next((p for p in construction.packages if p.target_cik_padded == target), None)


# --------------------------------------------------------------------------
# 1: target coverage and reserve count
# --------------------------------------------------------------------------


def test_every_selected_entity_carries_exactly_one_disposition() -> None:
    result, construction = construct(pool_with_plain_spare())
    targets = construction.disposition_targets()
    assert sorted(targets) == sorted(c.cik_padded for c in result.selected_entities)
    assert len(targets) == len(set(targets)) == 24


def test_the_two_disposition_families_are_mutually_exclusive() -> None:
    _result, construction = construct(pool_with_plain_spare())
    covered = {p.target_cik_padded for p in construction.packages}
    uncovered = {entry.target_cik_padded for entry in construction.no_compatible_reserve}
    assert covered
    assert uncovered
    assert not covered & uncovered


def test_every_package_is_rank_one_and_no_alternative_is_produced() -> None:
    _result, construction = construct(pool_with_plain_spare())
    assert construction.packages
    assert {p.reserve_rank for p in construction.packages} == {RESERVE_RANK}
    assert RESERVE_RANK == 1
    by_target = [p.target_cik_padded for p in construction.packages]
    assert len(by_target) == len(set(by_target))


def test_controls_are_reserve_targets_and_can_be_covered() -> None:
    """Decision 020 section 7 and owner ruling 14.6: compatibility alone decides,
    never entity role."""
    pool = base_pool()
    kind = next(iter(CONTROL_QUOTAS))
    pool.add_spare_control(310, kind, [mk_accession(310, 2020, 2, role="control", inline=True)])
    result, construction = construct(pool)
    control_ciks = {c.cik_padded for c in result.selected_controls}
    assert len(control_ciks) == 4
    assert control_ciks <= set(construction.disposition_targets())
    covered_controls = {
        p.target_cik_padded for p in construction.packages if p.target_cik_padded in control_ciks
    }
    assert covered_controls
    package = package_for(construction, next(iter(covered_controls)))
    assert package is not None
    assert package.replacement_cik_padded == "0000000310"


def test_a_pool_with_no_spare_candidate_covers_no_target() -> None:
    result, construction = construct(base_pool())
    assert construction.packages == ()
    assert len(construction.no_compatible_reserve) == len(result.selected_entities) == 24


# --------------------------------------------------------------------------
# 2: no compatible reserve
# --------------------------------------------------------------------------


def test_an_uncovered_target_carries_the_single_authorized_reason_code() -> None:
    _result, construction = construct(base_pool())
    assert {entry.reason_code for entry in construction.no_compatible_reserve} == {
        "REVIEW_PILOT_NO_COMPATIBLE_RESERVE"
    }
    assert NO_COMPATIBLE_RESERVE_REASON_CODE == "REVIEW_PILOT_NO_COMPATIBLE_RESERVE"


def test_the_reason_code_is_registered_review_required_and_nonblocking() -> None:
    entry = REASON_CODES[NO_COMPATIBLE_RESERVE_REASON_CODE]
    assert entry.category == "review"
    assert entry.requires_manual_review is True
    assert entry.blocks_release is False


def test_no_pool_exhaustion_or_substitution_reason_code_exists() -> None:
    """Decision 020 section 13 authorizes exactly one code and forbids these."""
    for forbidden in (
        "REVIEW_PILOT_RESERVE_POOL_EXHAUSTED",
        "PILOT_RESERVE_POOL_EXHAUSTED",
        "REVIEW_PILOT_RESERVE_APPROXIMATE",
        "PILOT_RESERVE_SUBSTITUTION_APPROVED",
        "REVIEW_PILOT_RESERVE_RETRY",
    ):
        assert forbidden not in REASON_CODES


def test_no_compatible_reserve_leaves_the_run_feasible_and_unexhausted() -> None:
    """Decision 020 section 7.1: nonblocking, not infeasibility, not exhaustion."""
    result, construction = construct(base_pool())
    assert result.status == "feasible"
    assert result.node_limit_exhausted is False
    assert len(construction.no_compatible_reserve) == 24
    assert len(result.selected_entities) == 24
    assert len(result.selected_accessions) == 38


def test_an_uncovered_target_never_receives_an_approximate_package() -> None:
    """The subset candidate is the closest available match and is still refused."""
    pool = pool_with_plain_spare(301, xbrl_level="review_required")
    _result, construction = construct(pool)
    assert package_for(construction, PLAIN_TARGETS[0]) is None
    assert "0000000301" not in {p.replacement_cik_padded for p in construction.packages}


# --------------------------------------------------------------------------
# 3: cross-target reuse, independence, and order invariance
# --------------------------------------------------------------------------


def test_one_replacement_may_serve_two_different_targets() -> None:
    """Decision 020 section 7 and owner ruling 14.7: packages are independent
    contingencies, never simultaneously applied, so reuse is permitted."""
    _result, construction = construct(pool_with_plain_spare())
    replacements = [p.replacement_cik_padded for p in construction.packages]
    assert replacements.count("0000000300") == 2
    assert sorted(p.target_cik_padded for p in construction.packages) == list(PLAIN_TARGETS)


def test_no_target_consumes_a_replacement_from_a_shared_pool() -> None:
    """Removing one of the two targets does not change the other's package."""
    pool = pool_with_plain_spare()
    _result, both = construct(pool)
    first = package_for(both, PLAIN_TARGETS[0])
    second = package_for(both, PLAIN_TARGETS[1])
    assert first is not None
    assert second is not None
    assert first.replacement_cik_padded == second.replacement_cik_padded
    assert first.accessions == second.accessions
    assert first.reserve_signature_sha256 == second.reserve_signature_sha256
    # Different targets, so the content-derived package identities still differ.
    assert first.reserve_package_id != second.reserve_package_id


def test_the_construction_is_invariant_under_the_order_targets_are_processed() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    reference = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    reversed_targets = dataclasses.replace(
        result,
        selected_operating=tuple(reversed(result.selected_operating)),
        selected_controls=tuple(reversed(result.selected_controls)),
    )
    permuted = build_reserve_packages(
        pool.entities,
        pool.accessions,
        reversed_targets,
        selection_run_id=RUN_ID,
        snapshot_id=SNAPSHOT_ID,
    )
    assert permuted == reference


def test_the_construction_is_invariant_under_candidate_input_permutation() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    reference = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    rng = random.Random(20260730)  # noqa: S311 - deterministic local test seed only
    for _ in range(4):
        entities = list(pool.entities)
        accessions = list(pool.accessions)
        rng.shuffle(entities)
        rng.shuffle(accessions)
        assert (
            build_reserve_packages(
                entities, accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
            )
            == reference
        )


def test_two_spares_do_not_split_the_targets_between_them() -> None:
    """No global assignment: both targets take the rank-1 candidate, and the
    second spare is used by neither."""
    pool = base_pool()
    for cik in (300, 302):
        pool.add_spare_operating(cik, PLAIN_SLOT, plain_spare_accessions(cik))
    _result, construction = construct(pool)
    ranked = sorted(("0000000300", "0000000302"), key=lambda cik: (selection_rank(cik), cik))
    assert {p.replacement_cik_padded for p in construction.packages} == {ranked[0]}
    assert len(construction.packages) == 2


# --------------------------------------------------------------------------
# 4: disjointness and within-target uniqueness
# --------------------------------------------------------------------------


def test_no_replacement_is_the_target_itself_or_a_selected_entity() -> None:
    """An S5.4 invariant Decision 020 section 7 requires even though migration
    ``0009`` enforces only ``target <> replacement``."""
    result, construction = construct(pool_with_plain_spare())
    selected = {c.cik_padded for c in result.selected_entities}
    for package in construction.packages:
        assert package.replacement_cik_padded != package.target_cik_padded
        assert package.replacement_cik_padded not in selected


def test_a_replacement_appears_at_most_once_within_one_target() -> None:
    _result, construction = construct(pool_with_plain_spare())
    for package in construction.packages:
        plains = [entry.accession_plain for entry in package.accessions]
        assert len(plains) == len(set(plains))
        assert {entry.accession_order for entry in package.accessions} == set(
            range(1, len(plains) + 1)
        )


def test_a_replacements_bundle_never_reuses_a_selected_accession() -> None:
    result, construction = construct(pool_with_plain_spare())
    selected_plains = {a.accession_plain for a in result.selected_accessions}
    for package in construction.packages:
        for entry in package.accessions:
            assert entry.accession_plain not in selected_plains


# --------------------------------------------------------------------------
# 5: contribution-set compatibility
# --------------------------------------------------------------------------


def test_a_package_reproduces_its_targets_exact_contribution_set() -> None:
    result, construction = construct(pool_with_plain_spare())
    membership = result.quota_contributions
    for package in construction.packages:
        expected = membership.contribution_keys_for_entity(package.target_cik_padded)
        assert package.quota_contributions == expected
        assert package.quota_contributions
        assert all(
            dimension == QUOTA_DIMENSION_CROSS_CUTTING
            for dimension, _key in package.quota_contributions
        )


def test_a_package_contribution_set_is_independently_reproducible_from_its_bundle() -> None:
    """Recomputed from the replacement's own rows through the single S5.1
    derivation, not read back from the package."""
    pool = pool_with_plain_spare()
    result, construction = construct(pool)
    for package in construction.packages:
        derived = QuotaContributionMembership.derive(
            pool.entities,
            pool.accessions,
            selected_entity_ciks=[package.replacement_cik_padded],
            selected_accession_plains=[e.accession_plain for e in package.accessions],
        )
        assert derived.contribution_keys() == package.quota_contributions
        assert (
            derived.contribution_keys()
            == result.quota_contributions.contribution_keys_for_entity(package.target_cik_padded)
        )


def test_a_strict_subset_contribution_set_is_refused() -> None:
    pool = pool_with_plain_spare(301, xbrl_level="review_required")
    result, construction = construct(pool)
    derived = QuotaContributionMembership.derive(
        pool.entities,
        pool.accessions,
        selected_entity_ciks=["0000000301"],
        selected_accession_plains=[dashed(301, 2018, 2).replace("-", "")],
    )
    target = result.quota_contributions.contribution_keys_for_entity(PLAIN_TARGETS[0])
    assert set(derived.contribution_keys()) < set(target)
    assert construction.packages == ()


def test_a_strict_superset_contribution_set_is_refused() -> None:
    pool = base_pool()
    pool.add_spare_operating(
        302,
        PLAIN_SLOT,
        [
            mk_accession(302, 2018, 2, role="base", inline=True),
            mk_accession(302, 2019, 4, role="base", inline=True, multi_registrant=True),
        ],
    )
    result, construction = construct(pool)
    derived = QuotaContributionMembership.derive(
        pool.entities,
        pool.accessions,
        selected_entity_ciks=["0000000302"],
        selected_accession_plains=[
            dashed(302, 2018, 2).replace("-", ""),
            dashed(302, 2019, 4).replace("-", ""),
        ],
    )
    target = result.quota_contributions.contribution_keys_for_entity(PLAIN_TARGETS[0])
    assert set(derived.contribution_keys()) > set(target)
    assert construction.packages == ()


def test_an_amendment_family_bundle_preserves_linked_amendment_coverage() -> None:
    pool = base_pool()
    pool.add_spare_operating(400, AMENDMENT_SLOT, amendment_spare_accessions(400))
    result, construction = construct(pool)
    package = package_for(construction, AMENDMENT_TARGET)
    assert package is not None
    assert package.replacement_cik_padded == "0000000400"
    assert len(package.accessions) == 2
    keys = {key for _dimension, key in package.quota_contributions}
    assert {"linked_amendment_entities", "amendment_purpose_categories"} <= keys
    assert package.quota_contributions == result.quota_contributions.contribution_keys_for_entity(
        AMENDMENT_TARGET
    )


def test_an_unresolved_amendment_parent_drops_linked_coverage_and_is_refused() -> None:
    """Decision 018 section 10.2: unresolved parentage fails closed, so the bundle
    no longer supplies the target's linked-amendment contribution."""
    pool = base_pool()
    pool.add_spare_operating(
        401, AMENDMENT_SLOT, amendment_spare_accessions(401, parent_present=False)
    )
    _result, construction = construct(pool)
    assert package_for(construction, AMENDMENT_TARGET) is None
    assert "0000000401" not in {p.replacement_cik_padded for p in construction.packages}


def test_a_different_amendment_purpose_category_is_refused() -> None:
    """The one contribution whose unit identity is a shared coverage token: the
    same quota key with a different category must not pass."""
    pool = base_pool()
    pool.add_spare_operating(
        402, AMENDMENT_SLOT, amendment_spare_accessions(402, purpose=PURPOSE_CATEGORIES[2])
    )
    _result, construction = construct(pool)
    assert package_for(construction, AMENDMENT_TARGET) is None


# --------------------------------------------------------------------------
# 6: role, stratum, cap, and floor compatibility
# --------------------------------------------------------------------------


def test_an_operating_spare_never_covers_a_control_target_and_the_reverse() -> None:
    pool = base_pool()
    pool.add_spare_operating(300, PLAIN_SLOT, plain_spare_accessions(300))
    kind = next(iter(CONTROL_QUOTAS))
    pool.add_spare_control(310, kind, [mk_accession(310, 2020, 2, role="control", inline=True)])
    result, construction = construct(pool)
    control_ciks = {c.cik_padded for c in result.selected_controls}
    operating_ciks = {c.cik_padded for c in result.selected_operating}
    for package in construction.packages:
        if package.target_cik_padded in control_ciks:
            assert package.replacement_cik_padded == "0000000310"
        else:
            assert package.target_cik_padded in operating_ciks
            assert package.replacement_cik_padded == "0000000300"


def test_a_spare_in_a_different_size_industry_or_history_stratum_is_refused() -> None:
    """Signature equality carries Decision 016 section 7's entity attributes, so a
    mismatched stratum can never be covered by a matching contribution set."""
    pool = base_pool()
    pool.add_spare_operating(303, 0, plain_spare_accessions(303))
    _result, construction = construct(pool)
    assert construction.packages == ()
    spare = mk_operating(303, 0)
    target = mk_operating(19, PLAIN_SLOT)
    assert (spare.size_stratum, spare.industry_group, spare.history_class) != (
        target.size_stratum,
        target.industry_group,
        target.history_class,
    )


def test_a_spare_with_no_base_accession_fails_the_entity_floor_and_is_refused() -> None:
    """Decision 018 section 9: an operating entity needs at least one base."""
    pool = base_pool()
    pool.add_spare_operating(
        304,
        PLAIN_SLOT,
        [
            mk_accession(
                304,
                2019,
                5,
                form="10-K/A",
                role="stress",
                inline=True,
                purpose=PURPOSE_CATEGORIES[0],
            )
        ],
    )
    _result, construction = construct(pool)
    assert construction.packages == ()


def test_a_spare_anchoring_no_accession_at_all_is_refused() -> None:
    pool = base_pool()
    pool.add_spare_operating(305, PLAIN_SLOT, [])
    _result, construction = construct(pool)
    assert construction.packages == ()


def test_a_spare_breaching_the_per_cik_base_cap_is_refused() -> None:
    """Decision 020 section 7(d): the bundle must satisfy the floors without
    breaching the section 8 caps. Both the cap gate and the role-count half of the
    signature refuse this bundle."""
    pool = base_pool()
    over_cap = [
        mk_accession(306, 2014 + offset, 10 + offset, role="base", inline=True)
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK + 1)
    ]
    pool.add_spare_operating(306, PLAIN_SLOT, over_cap)
    _result, construction = construct(pool)
    assert construction.packages == ()


def _reserve_entry(accession: AccessionCandidate, order: int) -> ReserveAccession:
    """One bundle entry for a candidate accession, at the accepted role and rank."""
    role = (
        "base"
        if accession.base_eligible
        else "stress"
        if accession.stress_eligible
        else "support"
        if accession.support_eligible
        else "control"
    )
    return ReserveAccession(
        accession_plain=accession.accession_plain,
        accession_number_dashed=accession.accession_number_dashed,
        accession_role=role,  # type: ignore[arg-type]
        accession_order=order,
        accession_tie_break_sha256=accession.rank,
    )


def _profile_for(
    cik: int, accessions: list[AccessionCandidate]
) -> tuple[_CandidateProfile, dict[str, AccessionCandidate]]:
    """A replacement profile over exactly these accessions, plus their pool mapping."""
    profile = _CandidateProfile(
        entity=EntityCandidate(mk_operating(cik, PLAIN_SLOT), NameChangeEvidence()),
        bundle=tuple(
            _reserve_entry(accession, order) for order, accession in enumerate(accessions, start=1)
        ),
        contributions=(),
        evidence_floor="provisional",
        signature="0" * 64,
    )
    return profile, {a.accession_plain: a for a in accessions}


def test_the_cap_gate_rejects_an_over_cap_bundle_on_its_own() -> None:
    """The cap gate is load-bearing independently of the signature comparison."""
    over_cap = [
        mk_accession(306, 2014 + offset, 10 + offset, role="base", inline=True)
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK + 1)
    ]
    profile, pool = _profile_for(306, over_cap)
    bundle = profile.bundle
    assert not _caps_preserved(
        profile, target_plains=set(), selected_roles={}, accession_by_plain=pool
    )
    usage = _usage_from(
        {entry.accession_plain: (("0000000306",), entry.accession_role) for entry in bundle}
    )
    assert usage.max_base_per_cik == MAX_BASE_ACCESSIONS_PER_CIK + 1
    assert (
        usage.achieved(QUOTA_KEY_BASE_ACCESSIONS_PER_CIK)
        > (ACCESSION_CAP_LIMITS[QUOTA_KEY_BASE_ACCESSIONS_PER_CIK])
    )
    assert not accession_caps_satisfied(usage)


def test_a_conforming_bundle_preserves_every_cap_under_substitution() -> None:
    pool = pool_with_plain_spare()
    by_plain = {a.accession_plain: a for a in pool.accessions}
    result, construction = construct(pool)
    # **Decision 083 R62**: the cap key is the complete substantive association set, so a
    # joint base filing counts toward each of its registrants' per-CIK base caps.
    selected_roles = {
        a.accession_plain: (a.substantive_registrants_padded, a.accession_role)
        for a in result.selected_accessions
    }
    for package in construction.packages:
        target_plains = {
            a.accession_plain
            for a in result.selected_accessions
            if package.target_cik_padded in a.substantive_registrants_padded
        }
        substituted = {
            plain: entry for plain, entry in selected_roles.items() if plain not in target_plains
        }
        for entry in package.accessions:
            # **Decision 085 §8**: the substituted world charges every truthful
            # substantive registrant, exactly as the retained selections above are
            # charged -- not the replacement alone.
            substituted[entry.accession_plain] = (
                by_plain[entry.accession_plain].substantive_registrants_padded,
                entry.accession_role,
            )
        assert accession_caps_satisfied(_usage_from(substituted))


# --------------------------------------------------------------------------
# 7: signatures, ranking, and package identity
# --------------------------------------------------------------------------


def test_both_signatures_are_equal_and_are_lowercase_64_hex() -> None:
    _result, construction = construct(pool_with_plain_spare())
    assert construction.packages
    for package in construction.packages:
        assert package.replaces_signature_sha256 == package.reserve_signature_sha256
        for digest in (package.replaces_signature_sha256, package.reserve_package_id):
            assert len(digest) == 64
            assert digest == digest.lower()
            assert all(character in "0123456789abcdef" for character in digest)


def test_the_two_signature_sides_are_built_from_disjoint_accession_sets() -> None:
    """A precondition for Decision 016 section 7's recomputation obligation, not the
    recomputation itself: the target's rows and the replacement's rows share no
    accession, so an equal digest cannot come from hashing the same content twice.

    The obligation itself -- independently reassembling both signature inputs from
    normalized persisted content and comparing each against its stored column -- is
    discharged by
    ``test_both_persisted_signatures_recompute_from_normalized_persisted_content``
    in ``tests/unit/test_m23_accession_selection_store.py``.
    """
    pool = pool_with_plain_spare()
    result, construction = construct(pool)
    package = package_for(construction, PLAIN_TARGETS[0])
    assert package is not None
    target_bundle = {
        a.accession_plain
        for a in result.selected_accessions
        if a.anchor_cik_padded == package.target_cik_padded
    }
    replacement_bundle = {entry.accession_plain for entry in package.accessions}
    assert target_bundle
    assert replacement_bundle
    assert not target_bundle & replacement_bundle
    assert package.target_cik_padded != package.replacement_cik_padded


def test_the_signature_and_quota_policy_versions_are_the_existing_frozen_constants() -> None:
    """Decision 020 sections 9 and 12: no new policy constant is introduced."""
    _result, construction = construct(pool_with_plain_spare())
    for package in construction.packages:
        assert package.signature_policy_version == PILOT_REPLACEMENT_SIGNATURE_POLICY_VERSION
        assert package.signature_policy_version == "quota-contribution/1.0"
        assert package.quota_policy_version == PILOT_QUOTA_POLICY_VERSION


def test_the_reserve_tie_break_is_the_accepted_initial_selection_rank() -> None:
    _result, construction = construct(pool_with_plain_spare())
    for package in construction.packages:
        assert package.reserve_tie_break_sha256 == selection_rank(package.replacement_cik_padded)
        assert (
            package.reserve_tie_break_sha256
            == hashlib.sha256(
                f"{PILOT_SELECTION_SEED}|{package.replacement_cik_padded}".encode()
            ).hexdigest()
        )


def test_the_rank_one_replacement_is_the_first_compatible_candidate_by_that_rank() -> None:
    pool = base_pool()
    for cik in (300, 302, 307):
        pool.add_spare_operating(cik, PLAIN_SLOT, plain_spare_accessions(cik))
    _result, construction = construct(pool)
    compatible = sorted(
        ("0000000300", "0000000302", "0000000307"),
        key=lambda cik: (selection_rank(cik), cik),
    )
    assert {p.replacement_cik_padded for p in construction.packages} == {compatible[0]}


def test_construction_is_byte_reproducible_across_repeated_calls() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    first = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    second = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    assert first == second


@pytest.mark.parametrize(
    "override",
    (
        {"selection_run_id": "b" * 64},
        {"snapshot_id": "c" * 64},
    ),
    ids=("run_id", "snapshot_id"),
)
def test_the_package_identity_is_subordinate_to_the_run_and_snapshot(
    override: dict[str, object],
) -> None:
    pool = pool_with_plain_spare()
    _result, reference = construct(pool)
    _result2, shifted = construct(pool_with_plain_spare(), **override)
    reference_ids = {p.reserve_package_id for p in reference.packages}
    shifted_ids = {p.reserve_package_id for p in shifted.packages}
    assert reference_ids
    assert not reference_ids & shifted_ids


def test_changing_bundle_content_changes_the_package_identity() -> None:
    """The identity is content-derived, so a materially different package can
    never reuse an existing package identity."""
    _result, reference = construct(pool_with_plain_spare())
    _result2, altered = construct(equally_weakened_pool())
    assert reference.packages
    assert altered.packages
    assert not {p.reserve_package_id for p in reference.packages} & {
        p.reserve_package_id for p in altered.packages
    }


@pytest.mark.parametrize("level", ("review_required", "conflicting", "unavailable"))
def test_the_evidence_floor_is_the_weakest_applicable_level_in_the_bundle(level: str) -> None:
    _result, construction = construct(equally_weakened_pool(level))
    assert construction.packages
    assert {p.evidence_floor for p in construction.packages} == {level}
    assert level in EVIDENCE_LEVEL_PRECEDENCE
    strong = pool_with_plain_spare()
    _result2, covered = construct(strong)
    assert {p.evidence_floor for p in covered.packages} == {"provisional"}
    assert EVIDENCE_LEVEL_PRECEDENCE[0] == "provisional"
    assert EVIDENCE_LEVEL_PRECEDENCE[-1] == "unavailable"


def test_a_weaker_floor_than_the_target_is_refused() -> None:
    """The floor is a signature input, so a package resting on weaker evidence
    than the entity it would replace can never be compatible."""
    pool = base_pool()
    pool.add_spare_operating(
        309, PLAIN_SLOT, plain_spare_accessions(309, filing_level="conflicting")
    )
    _result, construction = construct(pool)
    assert construction.packages == ()


# --------------------------------------------------------------------------
# 8: malformed input and non-feasible behaviour
# --------------------------------------------------------------------------


def test_a_non_feasible_result_produces_an_empty_construction() -> None:
    pool = base_pool()
    pool.accessions = [
        a for a in pool.accessions if a.accession_number_dashed != dashed(1, 2010, 2)
    ]
    result = pool.solve()
    assert result.status != "feasible"
    construction = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    assert construction == ReserveConstruction(packages=(), no_compatible_reserve=())


def test_a_node_limit_exhausted_result_produces_an_empty_construction() -> None:
    pool = base_pool()
    result = pool.solve(node_limit=1)
    assert result.node_limit_exhausted
    construction = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    assert construction.packages == ()
    assert construction.no_compatible_reserve == ()


@pytest.mark.parametrize(
    ("run_id", "snapshot"),
    (("", SNAPSHOT_ID), (RUN_ID, ""), ("", "")),
)
def test_an_empty_run_or_snapshot_identity_is_rejected(run_id: str, snapshot: str) -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    with pytest.raises(ValueError, match="required to scope a reserve package"):
        build_reserve_packages(
            pool.entities,
            pool.accessions,
            result,
            selection_run_id=run_id,
            snapshot_id=snapshot,
        )


def test_a_selected_entity_absent_from_the_candidate_pool_is_rejected() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    trimmed = [e for e in pool.entities if e.cik_padded != result.selected_operating[0].cik_padded]
    with pytest.raises(ValueError, match="not in the candidate entity pool"):
        build_reserve_packages(
            trimmed,
            pool.accessions,
            result,
            selection_run_id=RUN_ID,
            snapshot_id=SNAPSHOT_ID,
        )


def test_a_malformed_candidate_pool_is_rejected_before_any_package_is_built() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    broken = [*pool.accessions, dataclasses.replace(pool.accessions[0], accession_plain="123")]
    with pytest.raises(ValueError, match="inconsistent with dashed form"):
        build_reserve_packages(
            pool.entities,
            broken,
            result,
            selection_run_id=RUN_ID,
            snapshot_id=SNAPSHOT_ID,
        )


# --------------------------------------------------------------------------
# 8b: stored official filing dates -- one derivation, fail closed
# --------------------------------------------------------------------------
#
# Decision 018 section 19 puts every methodological rule in exactly one place.
# The filing year the section 15 support role depends on is derived only by the
# accepted core's ``official_filing_year``; this module holds no parser. A stored
# date the accepted core cannot read is a failed gate (Decision 020 section 10,
# CLAUDE.md rule 12), not a value to reinterpret, drop, or classify.

#: ``pilot_candidate_accessions.official_filing_date`` carries no format CHECK in
#: migration 0009 and the S5.2 loader does not validate it, so every shape below is
#: storable. Expected years are literals read off Decision 019 section 5.9's
#: exact-``YYYY-MM-DD`` rule, never produced by a production helper.
STORED_FILING_DATES: Final[tuple[tuple[str | None, int | None], ...]] = (
    (None, None),
    ("2009-03-15", 2009),
    ("2009-02-30", None),
    ("20090315", None),
    ("2009-3-15", None),
    ("abcd-01-01", None),
    ("", None),
)
MALFORMED_FILING_DATES: Final[tuple[str, ...]] = tuple(
    stored for stored, year in STORED_FILING_DATES if stored is not None and year is None
)


def support_spare_pool(cik: int = 600, *, filing_date: str | None) -> Pool:
    """A spare operating candidate whose 2009 support accession carries ``filing_date``.

    Slot 0's shape, so the spare is the one candidate whose bundle can contain a
    ``support``-role accession -- exactly the role the filing year decides.
    """
    pool = base_pool()
    support = dataclasses.replace(
        mk_accession(cik, 2009, 1, role="support", inline=False, has_xbrl=False, pre_study=True),
        official_filing_date=filing_date,
    )
    target = mk_accession(
        cik, 2010, 2, role="base", inline=False, has_xbrl=True, cohort="development"
    )
    pool.add_spare_operating(cik, 0, [support, target])
    return pool


@pytest.mark.parametrize(("stored", "expected"), STORED_FILING_DATES)
def test_the_reserve_module_and_the_accepted_helper_agree_on_every_stored_date(
    stored: str | None, expected: int | None
) -> None:
    """No divergence is possible: the module consults the accepted helper only."""
    accession = dataclasses.replace(
        mk_accession(600, 2009, 1, role="support", inline=False, has_xbrl=False, pre_study=True),
        official_filing_date=stored,
    )
    assert official_filing_year(stored) == expected
    if stored is None:
        assert _bundle_filing_year(accession) is None
    elif expected is None:
        with pytest.raises(GateFailureError):
            _bundle_filing_year(accession)
    else:
        assert _bundle_filing_year(accession) == expected


@pytest.mark.parametrize("stored", MALFORMED_FILING_DATES)
def test_a_malformed_stored_filing_date_fails_closed_in_a_reserve_bundle(stored: str) -> None:
    """Not silently omitted, not given a role, not reinterpreted -- refused."""
    pool = support_spare_pool(filing_date=stored)
    entity = pool.entities[-1]
    assert entity.cik_padded == "0000000600"
    with pytest.raises(GateFailureError, match="not an exact YYYY-MM-DD calendar date"):
        _bundle_for(entity, pool.accessions, PILOT_SELECTION_SEED)


@pytest.mark.parametrize("stored", MALFORMED_FILING_DATES)
def test_a_malformed_stored_filing_date_fails_closed_through_the_public_entry_point(
    stored: str,
) -> None:
    pool = support_spare_pool(filing_date=stored)
    result = pool.solve()
    assert result.status == "feasible"
    with pytest.raises(GateFailureError, match="not an exact YYYY-MM-DD calendar date"):
        build_reserve_packages(
            pool.entities,
            pool.accessions,
            result,
            selection_run_id=RUN_ID,
            snapshot_id=SNAPSHOT_ID,
        )


@pytest.mark.parametrize("stored", MALFORMED_FILING_DATES)
def test_a_malformed_stored_filing_date_never_leaks_valueerror(stored: str) -> None:
    """``GateFailureError`` derives from ``DisclosureDriftError``, not ``ValueError``,
    so a caller distinguishing a failed gate from a malformed argument still can."""
    pool = support_spare_pool(filing_date=stored)
    result = pool.solve()
    with pytest.raises(GateFailureError) as raised:
        build_reserve_packages(
            pool.entities,
            pool.accessions,
            result,
            selection_run_id=RUN_ID,
            snapshot_id=SNAPSHOT_ID,
        )
    assert not isinstance(raised.value, ValueError)
    assert stored in str(raised.value)


@pytest.mark.parametrize("stored", MALFORMED_FILING_DATES)
def test_no_malformed_date_enters_a_support_role_reserve_bundle(stored: str) -> None:
    """The regression this closes: reading ``2009`` out of a rejected date and
    assigning the section 15 ``support`` role the accepted core withheld.

    The canonical control below proves the assertion is not vacuous -- with a real
    ``2009-03-15`` the same fixture *does* produce a ``support`` accession.
    """
    canonical = support_spare_pool(filing_date="2009-03-15")
    bundle = _bundle_for(canonical.entities[-1], canonical.accessions, PILOT_SELECTION_SEED)
    assert "support" in {entry.accession_role for entry in bundle}

    pool = support_spare_pool(filing_date=stored)
    with pytest.raises(GateFailureError):
        _bundle_for(pool.entities[-1], pool.accessions, PILOT_SELECTION_SEED)
    _result, construction = construct(canonical)
    assert all(
        entry.accession_role != "support" or official_filing_year(stored) == 2009
        for package in construction.packages
        for entry in package.accessions
    )


def test_a_canonical_filing_date_preserves_the_accepted_role_behaviour() -> None:
    """Valid dates are untouched: 2009 yields ``support``, another year does not."""
    for filing_date, expect_support in (("2009-03-15", True), ("2011-03-15", False)):
        pool = support_spare_pool(filing_date=filing_date)
        bundle = _bundle_for(pool.entities[-1], pool.accessions, PILOT_SELECTION_SEED)
        roles = {entry.accession_role for entry in bundle}
        assert ("support" in roles) is expect_support
        assert "base" in roles


def test_the_target_side_derives_no_filing_year_at_all() -> None:
    """Recorded boundary: a target's bundle is read from the accepted selection's
    own rows, so the reserve module performs no filing-year derivation there and can
    neither diverge from nor duplicate the accepted core on the selected side."""
    reserve_code = _RESERVE_SELECTOR_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(reserve_code)
    callers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(call.func, ast.Name) and call.func.id == "_bundle_filing_year"
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
        )
    }
    assert callers == {"_bundle_for"}


def test_the_reserve_module_holds_no_filing_year_parser_of_its_own() -> None:
    """Decision 018 section 19, checked on code with docstrings stripped."""

    class Strip(ast.NodeTransformer):
        def _strip(self, node: ast.AST) -> ast.AST:
            self.generic_visit(node)
            body = node.body  # type: ignore[attr-defined]
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                node.body = body[1:] or [ast.Pass()]  # type: ignore[attr-defined]
            return node

        visit_Module = _strip  # noqa: N815
        visit_FunctionDef = _strip  # noqa: N815
        visit_AsyncFunctionDef = _strip  # noqa: N815
        visit_ClassDef = _strip  # noqa: N815

    code = ast.unparse(
        Strip().visit(ast.parse(_RESERVE_SELECTOR_SOURCE.read_text(encoding="utf-8")))
    )
    for forbidden in ("[:4]", "fromisoformat", "strptime", "_parse_iso_date", ".year", "re."):
        assert forbidden not in code, forbidden
    assert "official_filing_year(" in code


def test_the_accepted_fixture_is_unaffected_by_the_filing_year_refactor() -> None:
    """Every accepted-fixture date is canonical, so nothing fails closed and the
    construction stays byte-reproducible."""
    pool = pool_with_plain_spare()
    for accession in pool.accessions:
        assert official_filing_year(accession.official_filing_date) is not None
    result, first = construct(pool)
    second = build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    assert first == second
    assert first.packages


# --------------------------------------------------------------------------
# 9: purity and immutability
# --------------------------------------------------------------------------


def module_imports() -> set[str]:
    tree = ast.parse(_RESERVE_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_the_reserve_module_imports_only_a_minimal_pure_python_surface() -> None:
    assert module_imports() <= {
        "__future__",
        "collections",
        "dataclasses",
        "disclosure_drift",
        "typing",
    }


def test_the_reserve_module_imports_no_sqlite_network_filesystem_or_clock_module() -> None:
    banned = ("sqlite3", "httpx", "socket", "urllib", "pathlib", "os", "random", "time", "datetime")
    for name in module_imports():
        assert name not in banned, name


def test_the_reserve_module_declares_no_manifest_release_or_publication_behaviour() -> None:
    """Stage S6 is out of scope: no manifest, release, or publication table, hash,
    or entry point is referenced (Decision 020 section 2)."""
    tree = ast.parse(_RESERVE_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not {"hash_release", "publish", "write_manifest"} & called
    modules = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "disclosure_drift.release.manifest" not in modules
    assert modules <= {
        "__future__",
        "collections.abc",
        "dataclasses",
        "typing",
        "disclosure_drift.errors",
        "disclosure_drift.pilot_policy",
        "disclosure_drift.reasons",
        "disclosure_drift.release.hashing",
        "disclosure_drift.sec.accession_selector",
        "disclosure_drift.sec.entity_selector",
    }
    literals = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert not any(
        "pilot_manifest" in value or "reserves_sha256" in value or "root_manifest" in value
        for value in literals
    )


def test_no_random_or_clock_call_is_made_during_reserve_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        message = "build_reserve_packages must never call random or read the clock"
        raise AssertionError(message)

    monkeypatch.setattr(random, "random", blocked)
    monkeypatch.setattr(random, "choice", blocked)
    monkeypatch.setattr(random, "shuffle", blocked)
    monkeypatch.setattr(time, "time", blocked)
    monkeypatch.setattr(time, "monotonic", blocked)
    _result, construction = construct(pool_with_plain_spare())
    assert construction.packages


def test_reserve_construction_never_mutates_its_inputs() -> None:
    pool = pool_with_plain_spare()
    result = pool.solve()
    entities_before = [dataclasses.replace(e.candidate) for e in pool.entities]
    accessions_before = list(pool.accessions)
    result_before = dataclasses.replace(result)
    build_reserve_packages(
        pool.entities, pool.accessions, result, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    assert [e.candidate for e in pool.entities] == entities_before
    assert pool.accessions == accessions_before
    assert result == result_before


def test_reserve_construction_alters_no_selected_entity_or_accession() -> None:
    """A reserve is constructed, never applied (Decision 013 section 6)."""
    pool = pool_with_plain_spare()
    before = pool.solve()
    build_reserve_packages(
        pool.entities, pool.accessions, before, selection_run_id=RUN_ID, snapshot_id=SNAPSHOT_ID
    )
    after = pool.solve()
    assert after.selected_operating == before.selected_operating
    assert after.selected_controls == before.selected_controls
    assert after.selected_accessions == before.selected_accessions
    assert after.objective == before.objective
    assert after.quota_contributions == before.quota_contributions


def test_reserve_records_are_immutable() -> None:
    _result, construction = construct(pool_with_plain_spare())
    package = construction.packages[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        package.reserve_rank = 2  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        package.accessions[0].accession_order = 99  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        construction.packages[0].replacement_cik_padded = "0000000000"  # type: ignore[misc]
    uncovered = construction.no_compatible_reserve[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        uncovered.reason_code = "OTHER"  # type: ignore[misc]


# --------------------------------------------------------------------------
# Decision 085 §8: the per-CIK cap attaches to every substantive registrant
#
# `max_base_per_cik` is the one ENTITY-DOMAIN cap of Decision 018 section 8's four, so
# under **Decision 083 R62** a jointly filed base accession charges each of its truthful
# substantive registrants -- in the substituted world exactly as in the retained one.
# Attributing a joint bundle accession to the replacement alone understates a
# co-registrant's usage and can admit a substitution that breaches their cap.
# `base_total`, `stress_total`, and `accession_total` stay accession-domain and count the
# joint filing once, because the substituted map is keyed by accession.
# --------------------------------------------------------------------------

#: The co-registrant of any joint fixture accession for CIK `n`, as `mk_accession` builds
#: it: `_multi_registrant_set` returns `(None, (n, 900 + n))`.
_JOINT_CO_REGISTRANT: Final = f"{_CO_REGISTRANT_OFFSET + 306:010d}"


def _base_usage_for(cik_padded: str, roles: dict[str, object]) -> int:
    """The per-CIK base count one CIK carries in a substituted world."""
    return sum(
        1
        for registrants, role in roles.values()  # type: ignore[misc]
        if role == "base" and cik_padded in registrants  # type: ignore[operator]
    )


def test_min4_a_joint_replacement_charges_both_substantive_registrants() -> None:
    """**A.** A joint bundle accession reaches BOTH of its registrants' per-CIK caps."""
    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    assert joint.substantive_registrants_padded == ("0000000306", _JOINT_CO_REGISTRANT)
    profile, pool = _profile_for(306, [joint])

    assert _caps_preserved(profile, target_plains=set(), selected_roles={}, accession_by_plain=pool)
    substituted = {
        joint.accession_plain: (joint.substantive_registrants_padded, "base"),
    }
    usage = _usage_from(substituted)  # type: ignore[arg-type]
    assert usage.max_base_per_cik == 1
    assert _base_usage_for("0000000306", substituted) == 1
    assert _base_usage_for(_JOINT_CO_REGISTRANT, substituted) == 1


def test_min4_b_and_c_a_co_registrant_at_the_cap_refuses_the_joint_replacement() -> None:
    """**B** and **C.** The co-registrant is already at the cap, so the joint filing
    that would take them past it is refused -- fail-closed, not undercounted.

    This is the exact corner the review found: the co-registrant holds
    ``MAX_BASE_ACCESSIONS_PER_CIK`` retained base selections of their own and is not a
    registrant of any accession the target gives up, so nothing else in the substituted
    world notices them. Attributing the bundle accession to the replacement alone leaves
    their usage at the cap and admits the substitution.
    """
    at_cap = {
        f"retained-{offset}": ((_JOINT_CO_REGISTRANT,), "base")
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK)
    }
    assert _usage_from(at_cap).max_base_per_cik == MAX_BASE_ACCESSIONS_PER_CIK  # type: ignore[arg-type]
    assert accession_caps_satisfied(_usage_from(at_cap))  # type: ignore[arg-type]

    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    profile, pool = _profile_for(306, [joint])
    assert not _caps_preserved(
        profile,
        target_plains=set(),
        selected_roles=at_cap,  # type: ignore[arg-type]
        accession_by_plain=pool,
    )

    # And the pre-correction attribution is what would have let it through: charging the
    # replacement alone leaves the co-registrant at exactly the cap.
    replacement_only = dict(at_cap)
    replacement_only[joint.accession_plain] = (("0000000306",), "base")
    assert accession_caps_satisfied(_usage_from(replacement_only))  # type: ignore[arg-type]
    assert _base_usage_for(_JOINT_CO_REGISTRANT, replacement_only) == MAX_BASE_ACCESSIONS_PER_CIK


def test_min4_c_one_below_the_cap_still_admits_the_joint_replacement() -> None:
    """**C**, the other side: the guard is a cap, not a blanket refusal of joint work."""
    below_cap = {
        f"retained-{offset}": ((_JOINT_CO_REGISTRANT,), "base")
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK - 1)
    }
    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    profile, pool = _profile_for(306, [joint])
    assert _caps_preserved(
        profile,
        target_plains=set(),
        selected_roles=below_cap,  # type: ignore[arg-type]
        accession_by_plain=pool,
    )


def test_min4_d_a_joint_accession_is_counted_once_in_the_accession_domain() -> None:
    """**D.** Two registrants, one filing: the accession-domain totals do not double."""
    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    sole = mk_accession(306, 2019, 3, role="base", multi_registrant=False)
    usage = _usage_from(
        {
            joint.accession_plain: (joint.substantive_registrants_padded, "base"),
            sole.accession_plain: (sole.substantive_registrants_padded, "base"),
        }  # type: ignore[arg-type]
    )
    assert usage.base_total == 2
    assert usage.accession_total == 2
    # ...while the entity-domain cap still sees the joint filing from both sides.
    assert usage.max_base_per_cik == 2  # CIK 306 files both
    assert (
        _base_usage_for(
            _JOINT_CO_REGISTRANT,
            {
                joint.accession_plain: (joint.substantive_registrants_padded, "base"),
                sole.accession_plain: (sole.substantive_registrants_padded, "base"),
            },
        )
        == 1
    )


def test_min4_e_the_order_of_associated_registrants_changes_no_decision() -> None:
    """**E.** The substantive set is canonical, so no ordering can move the outcome."""
    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    reversed_set = dataclasses.replace(
        joint, substantive_registrant_ciks=tuple(reversed(joint.substantive_registrant_ciks))
    )
    assert reversed_set.substantive_registrants_padded == joint.substantive_registrants_padded
    at_cap = {
        f"retained-{offset}": ((_JOINT_CO_REGISTRANT,), "base")
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK)
    }
    decisions = set()
    for variant in (joint, reversed_set):
        profile, pool = _profile_for(306, [variant])
        decisions.add(
            _caps_preserved(
                profile,
                target_plains=set(),
                selected_roles=at_cap,  # type: ignore[arg-type]
                accession_by_plain=pool,
            )
        )
    assert decisions == {False}


def test_min4_f_single_registrant_reserve_behaviour_is_unchanged() -> None:
    """**F.** A sole-registrant bundle charges exactly the replacement, as before.

    The corrected attribution reduces to the old one when the set has cardinality 1,
    which is why no single-registrant reserve identity moves.
    """
    sole = mk_accession(306, 2018, 2, role="base", multi_registrant=False)
    assert sole.substantive_registrants_padded == ("0000000306",)
    profile, pool = _profile_for(306, [sole])

    # A co-registrant at the cap is irrelevant: they did not file this accession.
    at_cap = {
        f"retained-{offset}": ((_JOINT_CO_REGISTRANT,), "base")
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK)
    }
    assert _caps_preserved(
        profile,
        target_plains=set(),
        selected_roles=at_cap,  # type: ignore[arg-type]
        accession_by_plain=pool,
    )
    # The replacement's own cap still binds.
    own_cap = {
        f"retained-{offset}": (("0000000306",), "base")
        for offset in range(MAX_BASE_ACCESSIONS_PER_CIK)
    }
    assert not _caps_preserved(
        profile,
        target_plains=set(),
        selected_roles=own_cap,  # type: ignore[arg-type]
        accession_by_plain=pool,
    )


def test_min4_a_bundle_accession_outside_the_candidate_pool_fails_closed() -> None:
    """No silent fallback: an unreadable substantive set refuses rather than guesses."""
    joint = mk_accession(306, 2018, 2, role="base", multi_registrant=True)
    profile, _pool = _profile_for(306, [joint])
    with pytest.raises(ValueError, match="absent from the candidate pool"):
        _caps_preserved(profile, target_plains=set(), selected_roles={}, accession_by_plain={})
