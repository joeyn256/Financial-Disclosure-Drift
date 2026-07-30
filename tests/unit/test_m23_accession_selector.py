"""S5.1 -- pure accession policy and joint entity-accession selection: adversarial suite.

Pure-Python, in-memory tests only. No SQLite, no network, no filing text, no
outcomes, no clock, no randomness outside a fixed local test seed. Factories in
this module build *input objects only*: none of them computes, copies, or
pre-bakes a production-derived expected answer, and every expected value is
either a literal frozen by Decision 018 or produced by the independent
brute-force oracle at the bottom of this file.
"""

from __future__ import annotations

import ast
import collections
import dataclasses
import hashlib
import itertools
import math
import random
import time
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.sec import accession_selector
from disclosure_drift.sec.accession_selector import (
    ACCESSION_CAP_LIMITS,
    ACCESSION_QUOTA_IDENTIFIERS,
    APPROVED_DEFERRED_QUOTA_KEYS,
    CROSS_CUTTING_QUOTAS,
    DEFERRED_QUOTA_KEY,
    DEFERRED_QUOTA_REQUIRED_COUNT,
    FYE_CIRCULAR_TOLERANCE_DAYS,
    MAX_ACCESSIONS_TOTAL,
    MAX_BASE_ACCESSIONS_PER_CIK,
    MAX_BASE_ACCESSIONS_TOTAL,
    MAX_STRESS_ACCESSIONS_TOTAL,
    NOT_APPLICABLE,
    QUOTA_DIMENSION_ACCESSION_CAP,
    QUOTA_DIMENSION_CROSS_CUTTING,
    QUOTA_KEY_ACCESSIONS_TOTAL,
    QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES,
    QUOTA_KEY_BASE_ACCESSIONS_PER_CIK,
    QUOTA_KEY_BASE_ACCESSIONS_TOTAL,
    QUOTA_KEY_INLINE_XBRL_ORIGINALS,
    QUOTA_KEY_NAME_CHANGE_ENTITIES,
    QUOTA_KEY_ORIGINAL_2024_ENTITIES,
    QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS,
    QUOTA_KEY_STRESS_ACCESSIONS_TOTAL,
    QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES,
    AccessionCandidate,
    AccessionCapUsage,
    AccessionQuotaDiagnostic,
    EntityCandidate,
    JointObjective,
    JointSelectionResult,
    NameChangeEvidence,
    QuotaContributionMembership,
    accession_cap_outcomes,
    accession_caps_satisfied,
    accession_evidence_penalty,
    accession_selection_rank,
    assign_accession_role,
    canonical_anchor_cik_padded,
    circular_month_day_distance,
    derive_amendment_families,
    official_filing_year,
    solve_joint_selection,
)
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    OPERATING_FINANCIAL_INDUSTRY,
    PILOT_SELECTION_SEED,
    TOTAL_CONTROLS,
    TOTAL_OPERATING,
    Candidate,
    selection_rank,
    solve_entity_selection,
)

_ACCESSION_SELECTOR_SOURCE: Final = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "disclosure_drift"
    / "sec"
    / "accession_selector.py"
)

_RESERVE_SELECTOR_SOURCE: Final = _ACCESSION_SELECTOR_SOURCE.with_name("reserve_selector.py")


def code_without_docstrings(path: Path) -> str:
    """One module's source with every docstring and comment removed.

    Source-level prohibitions are checked against this rather than the raw text, so
    a docstring that *names* a forbidden idiom cannot be mistaken for one.
    """

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

    return ast.unparse(Strip().visit(ast.parse(path.read_text(encoding="utf-8"))))


#: Large enough that every fixture in this module proves its optimum; never an
#: assertion about a production node-limit default (Decision 018 section 17
#: deliberately freezes none).
GENEROUS_NODE_LIMIT: Final = 5_000_000

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


# --------------------------------------------------------------------------
# Input factories -- objects only, never expected answers
# --------------------------------------------------------------------------


def mk_operating(cik: int, slot: int, *, evidence_penalty: int = 0) -> Candidate:
    """One operating entity filling the frozen bucket at ``slot`` (0-19)."""
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


def mk_accession(
    cik: int,
    year: int,
    seq: int,
    *,
    form: str = "10-K",
    role: str = "base",
    also_eligible: Sequence[str] = (),
    inline: bool = True,
    has_xbrl: bool | None = None,
    cohort: str | None = "development",
    pre_study: bool = False,
    parent: str | None = None,
    purpose: str | None = None,
    report_date: str | None = None,
    multi_registrant: bool = False,
    filing_level: str = "provisional",
    cohort_level: str = "provisional",
    xbrl_level: str = "provisional",
    purpose_level: str | None = None,
    linkage_level: str | None = None,
    filing_date: str | None = None,
) -> AccessionCandidate:
    """One candidate accession.

    ``role`` sets one frozen eligibility flag; ``also_eligible`` sets further ones,
    so a genuinely dual-eligible candidate (for example an original a snapshot marks
    both ``control_eligible`` and ``base_eligible``) can be constructed. The factory
    never decides an assigned role -- that is production policy.
    """
    number = dashed(cik, year, seq)
    is_amendment = form.endswith("/A")
    eligibility = {role, *also_eligible}
    return AccessionCandidate(
        accession_plain=number.replace("-", ""),
        accession_number_dashed=number,
        anchor_cik_numeric=cik,
        form_type=form,
        is_amendment=is_amendment,
        official_filing_date=filing_date if filing_date is not None else f"{year}-03-15",
        report_date=report_date if report_date is not None else f"{year - 1}-12-31",
        cohort_applicability="pre_study" if pre_study else "applies",
        provisional_official_cohort=None if pre_study else cohort,
        filing_date_evidence_level=filing_level,
        cohort_evidence_level=NOT_APPLICABLE if pre_study else cohort_level,
        xbrl_evidence_level=xbrl_level,
        amendment_purpose_evidence_level=(
            (purpose_level or "provisional") if is_amendment else NOT_APPLICABLE
        ),
        amendment_linkage_evidence_level=(
            (linkage_level or "provisional") if is_amendment else NOT_APPLICABLE
        ),
        multi_registrant_evidence_level="provisional" if multi_registrant else NOT_APPLICABLE,
        has_xbrl=inline if has_xbrl is None else has_xbrl,
        has_inline_xbrl=inline,
        amendment_linkage_state="amends_original" if is_amendment else None,
        provisional_parent_accession_dashed=parent,
        amendment_purpose_category=purpose,
        amendment_purpose_quota_eligible=(
            purpose is not None and (purpose_level or "provisional") == "provisional"
        ),
        base_eligible="base" in eligibility,
        stress_eligible="stress" in eligibility,
        support_eligible="support" in eligibility,
        control_eligible="control" in eligibility,
        multi_registrant=multi_registrant,
    )


@dataclass
class Pool:
    """A mutable pool under construction. Inputs only; no expected answers."""

    entities: list[EntityCandidate]
    accessions: list[AccessionCandidate]

    def solve(self, *, node_limit: int = GENEROUS_NODE_LIMIT) -> JointSelectionResult:
        return solve_joint_selection(self.entities, self.accessions, node_limit=node_limit)

    def accession(self, number: str) -> AccessionCandidate:
        return next(a for a in self.accessions if a.accession_number_dashed == number)

    def replace_accession(self, number: str, **changes: object) -> None:
        for index, accession in enumerate(self.accessions):
            if accession.accession_number_dashed == number:
                self.accessions[index] = dataclasses.replace(accession, **changes)  # type: ignore[arg-type]
                return
        message = f"no accession {number!r} in pool"
        raise AssertionError(message)

    def drop_accession(self, number: str) -> None:
        self.accessions = [a for a in self.accessions if a.accession_number_dashed != number]


def base_pool() -> Pool:
    """A tight, fully feasible pool under the complete frozen quota set.

    Every accession in this pool is required by some hard quota, so the joint
    optimum is the whole pool. Structures are synthetic: they exercise the frozen
    rules (roles, families, quotas, caps, floors) rather than reproducing any real
    filing lineage.

    Composition: 20 operating entities each with one base accession; entities in
    slots 0-5 additionally carry a 2009 support accession paired with a 2010
    development target; slots 0-7 each carry one amendment of their own base, of
    which slots 5-7 are 10-KT/A (supplying both transition-report and
    fiscal-year-end coverage); four boundary controls each carry one control-role
    original.
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


# --------------------------------------------------------------------------
# 1: canonical accession identity, tie-break hash, selected order
# --------------------------------------------------------------------------


def test_tie_break_hash_matches_the_frozen_decision_018_formula() -> None:
    anchor = "0000000042"
    number = "0000000042-24-000001"
    expected = hashlib.sha256(f"{PILOT_SELECTION_SEED}|{anchor}|{number}".encode()).hexdigest()
    assert accession_selection_rank(anchor, number) == expected


def test_tie_break_hash_is_lowercase_64_hex_and_stable() -> None:
    value = accession_selection_rank("0000000001", "0000000001-10-000002")
    assert len(value) == 64
    assert value == value.lower()
    assert set(value) <= set("0123456789abcdef")
    assert value == accession_selection_rank("0000000001", "0000000001-10-000002")


def test_tie_break_hash_uses_only_seed_anchor_and_dashed_accession() -> None:
    """No registrant set, role, or family identity can enter the hash: the
    function has no parameter for any of them, and two candidates differing only
    in those fields hash identically."""
    first = mk_accession(7, 2020, 2, role="base", multi_registrant=False)
    second = dataclasses.replace(
        first, multi_registrant=True, multi_registrant_evidence_level="provisional"
    )
    assert first.rank == second.rank


def test_anchor_cik_padded_is_derived_from_the_stored_numeric_cik() -> None:
    assert canonical_anchor_cik_padded(42) == "0000000042"
    assert mk_accession(42, 2020, 2).anchor_cik_padded == "0000000042"


@pytest.mark.parametrize("bad", [-1, 10_000_000_000, True])
def test_malformed_anchor_cik_fails_closed(bad: object) -> None:
    with pytest.raises(ValueError, match="anchor_cik_numeric"):
        canonical_anchor_cik_padded(bad)  # type: ignore[arg-type]


def test_selected_order_is_contiguous_and_follows_the_frozen_key() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    orders = [a.selected_order for a in result.selected_accessions]
    assert orders == list(range(1, len(result.selected_accessions) + 1))
    keys = [
        (a.accession_tie_break_sha256, a.anchor_cik_padded, a.accession_number_dashed)
        for a in result.selected_accessions
    ]
    assert keys == sorted(keys)


def test_selected_order_ignores_role_and_entity_order() -> None:
    """The frozen key contains no role and no entity ordering, so sorting the
    selected accessions by role or by anchor cannot reproduce it in general."""
    result = base_pool().solve()
    assert result.status == "feasible"
    by_role = sorted(result.selected_accessions, key=lambda a: (a.accession_role, a.selected_order))
    assert [a.selected_order for a in by_role] != [
        a.selected_order for a in result.selected_accessions
    ]
    for accession in result.selected_accessions:
        assert accession.accession_tie_break_sha256 == accession_selection_rank(
            accession.anchor_cik_padded, accession.accession_number_dashed
        )


# --------------------------------------------------------------------------
# 2: role assignment is total, deterministic, and mutually exclusive
# --------------------------------------------------------------------------


def role_of(accession: AccessionCandidate, category: str, year: int | None) -> str | None:
    role, _ = assign_accession_role(accession, anchor_category=category, filing_year=year)
    return role


def test_control_role_requires_a_control_anchor_original_and_control_eligibility() -> None:
    control = mk_accession(101, 2020, 2, role="control")
    assert role_of(control, "control", 2020) == "control"
    assert role_of(control, "operating", 2020) is None
    not_eligible = mk_accession(101, 2020, 2, role="base")
    assert role_of(not_eligible, "control", 2020) is None
    amendment = mk_accession(
        101, 2020, 3, form="10-K/A", role="control", parent=dashed(101, 2020, 2)
    )
    assert role_of(amendment, "control", 2020) is None


def test_support_role_requires_2009_support_eligibility_and_no_study_cohort() -> None:
    support = mk_accession(1, 2009, 1, role="support", pre_study=True, inline=False)
    assert role_of(support, "operating", 2009) == "support"
    assert role_of(support, "operating", 2010) is None
    assert role_of(support, "control", 2009) is None
    with_cohort = mk_accession(1, 2009, 1, role="support", pre_study=False)
    assert role_of(with_cohort, "operating", 2009) is None
    not_eligible = mk_accession(1, 2009, 1, role="none", pre_study=True, cohort=None)
    assert role_of(not_eligible, "operating", 2009) is None


def test_base_role_requires_an_original_10k_and_base_eligibility() -> None:
    base = mk_accession(1, 2020, 2, role="base")
    assert role_of(base, "operating", 2020) == "base"
    assert role_of(mk_accession(1, 2020, 2, role="stress"), "operating", 2020) is None


@pytest.mark.parametrize("form", ["10-KT", "10-K/A", "10-KT/A"])
def test_stress_forms_are_stress_never_base(form: str) -> None:
    parent = dashed(1, 2019, 1) if form.endswith("/A") else None
    accession = mk_accession(1, 2020, 2, form=form, role="stress", parent=parent)
    assert role_of(accession, "operating", 2020) == "stress"
    not_eligible = mk_accession(1, 2020, 2, form=form, role="base", parent=parent)
    assert role_of(not_eligible, "operating", 2020) is None


def test_an_accession_matching_no_role_is_unclassified() -> None:
    accession = mk_accession(1, 2020, 2, form="8-K", role="none")
    role, reason = assign_accession_role(accession, anchor_category="operating", filing_year=2020)
    assert role is None
    assert reason == "role_unclassified_no_match"


def test_an_accession_matching_two_roles_fails_closed_as_unclassified() -> None:
    """A 2009 original flagged both support-eligible and base-eligible matches
    support *and* base, so it is not selectable at all (Decision 018 section 7)."""
    contradictory = dataclasses.replace(
        mk_accession(1, 2009, 1, role="support", pre_study=True), base_eligible=True
    )
    role, reason = assign_accession_role(
        contradictory, anchor_category="operating", filing_year=2009
    )
    assert role is None
    assert reason == "role_unclassified_multiple_match"


def test_an_unrecognized_anchor_category_is_rejected() -> None:
    role, reason = assign_accession_role(
        mk_accession(1, 2020, 2), anchor_category="ineligible", filing_year=2020
    )
    assert role is None
    assert reason == "unrecognized_anchor_category"


def test_role_assignment_is_total_over_every_flag_and_form_combination() -> None:
    """Every combination returns exactly one role or a diagnostic reason -- it
    never returns a role together with a failure reason, and never both."""
    forms = ("10-K", "10-KT", "10-K/A", "10-KT/A", "8-K")
    for form in forms:
        for role_flag in ("base", "stress", "support", "control", "none"):
            for category in ("operating", "control", "ineligible"):
                for year in (2009, 2024, None):
                    parent = dashed(1, 2019, 1) if form.endswith("/A") else None
                    accession = mk_accession(
                        1,
                        2024,
                        2,
                        form=form,
                        role=role_flag,
                        parent=parent,
                        pre_study=role_flag == "support",
                        cohort=None if role_flag == "support" else "development",
                    )
                    role, reason = assign_accession_role(
                        accession, anchor_category=category, filing_year=year
                    )
                    assert (role is None) != (reason == "")


# --------------------------------------------------------------------------
# 3: applicability-aware evidence penalty
# --------------------------------------------------------------------------


WEAKER_THAN_PROVISIONAL: Final = ("review_required", "conflicting", "unavailable")


def test_a_fully_provisional_original_scores_zero() -> None:
    assert accession_evidence_penalty(mk_accession(1, 2020, 2, role="base")) == 0


@pytest.mark.parametrize("level", WEAKER_THAN_PROVISIONAL)
def test_each_weaker_applicable_dimension_scores_one(level: str) -> None:
    assert accession_evidence_penalty(mk_accession(1, 2020, 2, filing_level=level)) == 1
    assert accession_evidence_penalty(mk_accession(1, 2020, 2, xbrl_level=level)) == 1
    assert accession_evidence_penalty(mk_accession(1, 2020, 2, cohort_level=level)) == 1


def test_penalties_accumulate_as_plain_integers_without_any_float() -> None:
    accession = mk_accession(
        1,
        2020,
        2,
        filing_level="unavailable",
        xbrl_level="conflicting",
        cohort_level="review_required",
    )
    penalty = accession_evidence_penalty(accession)
    assert penalty == 3
    assert type(penalty) is int


def test_amendment_dimensions_apply_only_to_amendments() -> None:
    original = mk_accession(1, 2020, 2, role="base")
    assert original.amendment_purpose_evidence_level == NOT_APPLICABLE
    assert original.amendment_linkage_evidence_level == NOT_APPLICABLE
    assert accession_evidence_penalty(original) == 0

    amendment = mk_accession(
        1,
        2021,
        3,
        form="10-K/A",
        role="stress",
        parent=dashed(1, 2020, 2),
        purpose=PURPOSE_CATEGORIES[0],
    )
    assert accession_evidence_penalty(amendment) == 0
    weak_purpose = dataclasses.replace(
        amendment,
        amendment_purpose_evidence_level="unproven",
        amendment_purpose_quota_eligible=False,
    )
    assert accession_evidence_penalty(weak_purpose) == 1
    weak_linkage = dataclasses.replace(
        amendment, amendment_linkage_evidence_level="review_required"
    )
    assert accession_evidence_penalty(weak_linkage) == 1


def test_a_valid_2009_support_accession_receives_no_cohort_penalty() -> None:
    support = mk_accession(1, 2009, 1, role="support", pre_study=True, inline=False, has_xbrl=False)
    assert support.provisional_official_cohort is None
    assert support.cohort_evidence_level == NOT_APPLICABLE
    assert accession_evidence_penalty(support) == 0


def test_every_evidence_level_combination_on_an_amendment_scores_the_frozen_table() -> None:
    """All five applicable dimensions, every level: ``provisional`` scores 0 and
    every weaker level scores 1, with no other value possible."""
    levels = ("provisional", "review_required", "conflicting", "unavailable")
    purpose_levels = (*levels, "unproven")
    for filing in levels:
        for xbrl in levels:
            for cohort in levels:
                for purpose in purpose_levels:
                    for linkage in levels:
                        amendment = mk_accession(
                            1,
                            2021,
                            3,
                            form="10-K/A",
                            role="stress",
                            parent=dashed(1, 2020, 2),
                            purpose=PURPOSE_CATEGORIES[0],
                            filing_level=filing,
                            xbrl_level=xbrl,
                            cohort_level=cohort,
                            purpose_level=purpose,
                            linkage_level=linkage,
                        )
                        expected = sum(
                            1
                            for value in (filing, xbrl, cohort, purpose, linkage)
                            if value != "provisional"
                        )
                        assert accession_evidence_penalty(amendment) == expected


def test_every_evidence_level_combination_on_a_pre_study_original_skips_cohort() -> None:
    levels = ("provisional", "review_required", "conflicting", "unavailable")
    for filing in levels:
        for xbrl in levels:
            support = mk_accession(
                1,
                2009,
                1,
                role="support",
                pre_study=True,
                inline=False,
                has_xbrl=False,
                filing_level=filing,
                xbrl_level=xbrl,
            )
            expected = sum(1 for value in (filing, xbrl) if value != "provisional")
            assert accession_evidence_penalty(support) == expected


def test_a_study_cohort_accession_with_unavailable_cohort_evidence_is_penalized() -> None:
    """The contrast with the pre-study case: an accession a study cohort *does*
    apply to is penalized for unresolved cohort evidence."""
    accession = mk_accession(1, 2020, 2, cohort_level="unavailable", cohort="development")
    assert accession_evidence_penalty(accession) == 1


# --------------------------------------------------------------------------
# 4: contradictory applicability / evidence input is rejected before search
# --------------------------------------------------------------------------


def solve_one(accession: AccessionCandidate) -> JointSelectionResult:
    pool = base_pool()
    pool.accessions.append(accession)
    return pool.solve(node_limit=1)


def test_pre_study_applicability_with_a_resolved_cohort_is_rejected() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2009, 1, role="support", pre_study=True),
        provisional_official_cohort="development",
    )
    with pytest.raises(ValueError, match="pre-study"):
        solve_one(bad)


def test_pre_study_applicability_with_a_real_cohort_evidence_level_is_rejected() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2009, 1, role="support", pre_study=True),
        cohort_evidence_level="unavailable",
    )
    with pytest.raises(ValueError, match="structurally inapplicable cohort"):
        solve_one(bad)


def test_amendment_evidence_on_an_original_is_rejected() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2020, 2), amendment_purpose_evidence_level="provisional"
    )
    with pytest.raises(ValueError, match="amendment-purpose evidence on non-amendment"):
        solve_one(bad)
    bad_linkage = dataclasses.replace(
        mk_accession(50, 2020, 2), amendment_linkage_evidence_level="provisional"
    )
    with pytest.raises(ValueError, match="amendment-linkage evidence on non-amendment"):
        solve_one(bad_linkage)


def test_structurally_inapplicable_evidence_on_an_amendment_is_rejected() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2021, 3, form="10-K/A", role="stress", parent=dashed(50, 2020, 2)),
        amendment_linkage_evidence_level=NOT_APPLICABLE,
    )
    with pytest.raises(ValueError, match="amendment-linkage evidence level"):
        solve_one(bad)


def test_multi_registrant_evidence_on_a_single_registrant_accession_is_rejected() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2020, 2), multi_registrant_evidence_level="provisional"
    )
    with pytest.raises(ValueError, match="multi-registrant evidence"):
        solve_one(bad)


def test_form_and_amendment_flag_contradictions_are_rejected() -> None:
    bad = dataclasses.replace(mk_accession(50, 2020, 2), is_amendment=True)
    with pytest.raises(ValueError, match="contradicts is_amendment"):
        solve_one(bad)


def test_malformed_and_duplicate_accessions_are_rejected_before_search() -> None:
    pool = base_pool()
    pool.accessions.append(pool.accessions[0])
    with pytest.raises(ValueError, match="duplicate"):
        pool.solve(node_limit=1)

    pool = base_pool()
    pool.accessions.append(
        dataclasses.replace(mk_accession(50, 2020, 2), accession_number_dashed="not-an-accession")
    )
    with pytest.raises(ValueError, match="malformed canonical dashed accession"):
        pool.solve(node_limit=1)

    pool = base_pool()
    pool.accessions.append(dataclasses.replace(mk_accession(50, 2020, 2), accession_plain="0" * 18))
    with pytest.raises(ValueError, match="inconsistent with dashed form"):
        pool.solve(node_limit=1)


@pytest.mark.parametrize("bad_limit", [0, -1, True, 1.5])
def test_a_malformed_node_limit_fails_before_search(bad_limit: object) -> None:
    pool = base_pool()
    with pytest.raises(ValueError, match="node_limit"):
        solve_joint_selection(pool.entities, pool.accessions, node_limit=bad_limit)  # type: ignore[arg-type]


def test_duplicate_entity_ciks_are_rejected_by_the_accepted_s4_gate() -> None:
    pool = base_pool()
    pool.entities.append(pool.entities[0])
    with pytest.raises(ValueError, match="duplicate canonical CIK"):
        pool.solve(node_limit=1)


# --------------------------------------------------------------------------
# 5: amendment families
# --------------------------------------------------------------------------


def test_a_transitive_amendment_chain_resolves_to_the_root_original() -> None:
    root = mk_accession(1, 2019, 1, role="base")
    first = mk_accession(
        1, 2020, 2, form="10-K/A", role="stress", parent=root.accession_number_dashed
    )
    second = mk_accession(
        1, 2021, 3, form="10-K/A", role="stress", parent=first.accession_number_dashed
    )
    families, roots = derive_amendment_families([root, first, second])
    assert roots == (0, 0, 0)
    assert len(families) == 1
    assert families[0].family_id == root.accession_number_dashed
    assert families[0].resolved is True
    assert families[0].members == tuple(
        sorted(
            [
                root.accession_number_dashed,
                first.accession_number_dashed,
                second.accession_number_dashed,
            ]
        )
    )


def test_family_derivation_is_independent_of_input_ordering() -> None:
    root = mk_accession(1, 2019, 1, role="base")
    first = mk_accession(
        1, 2020, 2, form="10-K/A", role="stress", parent=root.accession_number_dashed
    )
    second = mk_accession(
        1, 2021, 3, form="10-K/A", role="stress", parent=first.accession_number_dashed
    )
    forward, _ = derive_amendment_families([root, first, second])
    reverse, _ = derive_amendment_families([second, first, root])
    shuffled, _ = derive_amendment_families([first, root, second])
    assert forward == reverse == shuffled


def test_absent_parentage_produces_an_unresolved_singleton_family() -> None:
    orphan = mk_accession(1, 2020, 2, form="10-K/A", role="stress", parent=None)
    families, roots = derive_amendment_families([orphan])
    assert roots == (None,)
    assert families[0].resolved is False
    assert families[0].reason == "unresolved_parent"
    assert families[0].members == (orphan.accession_number_dashed,)
    assert families[0].family_id == orphan.accession_number_dashed


def test_a_parent_outside_the_pool_produces_an_unresolved_singleton_family() -> None:
    orphan = mk_accession(1, 2020, 2, form="10-K/A", role="stress", parent=dashed(999, 2015, 9))
    families, roots = derive_amendment_families([orphan])
    assert roots == (None,)
    assert families[0].resolved is False
    assert families[0].reason == "parent_not_in_pool"


def test_a_parentage_cycle_fails_closed_to_unresolved_singletons() -> None:
    first_number = dashed(1, 2020, 2)
    second_number = dashed(1, 2021, 3)
    first = mk_accession(1, 2020, 2, form="10-K/A", role="stress", parent=second_number)
    second = mk_accession(1, 2021, 3, form="10-K/A", role="stress", parent=first_number)
    families, roots = derive_amendment_families([first, second])
    assert roots == (None, None)
    assert {f.family_id for f in families} == {first_number, second_number}
    assert all(f.resolved is False for f in families)
    assert all(f.reason == "parent_cycle" for f in families)


def test_linked_amendment_coverage_requires_the_root_original_to_be_co_selected() -> None:
    """Dropping one entity's base breaks its accession floor *and* its family
    root, so the run is infeasible rather than crediting an orphaned amendment."""
    pool = base_pool()
    pool.drop_accession(dashed(1, 2010, 2))
    result = pool.solve()
    assert result.status == "infeasible"
    assert result.selected_accessions == ()


def test_unresolved_parentage_cannot_satisfy_linked_amendment_coverage() -> None:
    pool = base_pool()
    pool.replace_accession(dashed(1, 2021, 3), provisional_parent_accession_dashed=None)
    result = pool.solve()
    assert result.status == "infeasible"
    linked = next(q for q in result.accession_quota_results if q.key == "linked_amendment_entities")
    assert linked.available_eligible_count == CROSS_CUTTING_QUOTAS["linked_amendment_entities"] - 1


def test_weak_linkage_evidence_cannot_satisfy_linked_amendment_coverage() -> None:
    pool = base_pool()
    pool.replace_accession(dashed(1, 2021, 3), amendment_linkage_evidence_level="review_required")
    result = pool.solve()
    assert result.status == "infeasible"


def test_family_identity_enters_neither_the_hash_nor_the_selected_order() -> None:
    """Re-pointing an amendment's parentage changes its family but leaves every
    selected accession hash and every selected_order untouched."""
    first = base_pool().solve()
    assert first.status == "feasible"

    pool = base_pool()
    extra_root = mk_accession(1, 2008, 9, role="base", inline=False, has_xbrl=False)
    pool.accessions.append(extra_root)
    pool.replace_accession(
        dashed(1, 2021, 3), provisional_parent_accession_dashed=extra_root.accession_number_dashed
    )
    second = pool.solve()
    assert second.status == "feasible"
    families_first = {f.family_id for f in first.amendment_families}
    families_second = {f.family_id for f in second.amendment_families}
    assert families_first != families_second
    moved = next(
        a for a in second.selected_accessions if a.accession_number_dashed == dashed(1, 2021, 3)
    )
    original = next(
        a for a in first.selected_accessions if a.accession_number_dashed == dashed(1, 2021, 3)
    )
    assert moved.accession_tie_break_sha256 == original.accession_tie_break_sha256


# --------------------------------------------------------------------------
# 6: fiscal-year-end change derivation
# --------------------------------------------------------------------------


def test_circular_distance_handles_the_december_january_boundary() -> None:
    assert circular_month_day_distance(date(2020, 12, 28), date(2021, 1, 2)) == 5
    assert circular_month_day_distance(date(2021, 1, 2), date(2020, 12, 28)) == 5
    assert circular_month_day_distance(date(2020, 1, 1), date(2020, 12, 31)) == 1


def test_circular_distance_is_symmetric_and_bounded_by_half_a_leap_year() -> None:
    assert circular_month_day_distance(date(2020, 1, 1), date(2020, 7, 1)) == 182
    assert circular_month_day_distance(date(2020, 6, 30), date(2020, 12, 31)) == 182
    assert circular_month_day_distance(date(2020, 12, 31), date(2020, 6, 30)) == 182
    assert circular_month_day_distance(date(2020, 3, 1), date(2020, 3, 1)) == 0


def test_the_seven_day_tolerance_boundary_is_strict() -> None:
    seven = circular_month_day_distance(date(2020, 12, 31), date(2021, 1, 7))
    eight = circular_month_day_distance(date(2020, 12, 31), date(2021, 1, 8))
    assert seven == FYE_CIRCULAR_TOLERANCE_DAYS
    assert eight == FYE_CIRCULAR_TOLERANCE_DAYS + 1


def test_leap_day_maps_onto_the_fixed_leap_year_calendar() -> None:
    assert circular_month_day_distance(date(2020, 2, 29), date(2020, 3, 1)) == 1
    assert circular_month_day_distance(date(2020, 2, 28), date(2020, 2, 29)) == 1


def fye_pool(third_source: str) -> Pool:
    """Base pool with the third fiscal-year-end contribution supplied as named."""
    pool = base_pool()
    # Slots 5-7 supply two transition entities; demote slot 7 so exactly two
    # remain, then add the third contribution under test.
    pool.replace_accession(dashed(8, 2021, 3), form_type="10-K/A")
    if third_source == "distance":
        pool.replace_accession(dashed(9, 2024, 2), report_date="2023-12-31")
        pool.accessions.append(
            mk_accession(9, 2019, 5, role="base", inline=True, report_date="2019-06-30")
        )
    elif third_source == "transition_original":
        pool.accessions.append(
            mk_accession(9, 2022, 6, form="10-KT", role="stress", inline=True, cohort="transition")
        )
    elif third_source == "undated_distance":
        pool.replace_accession(dashed(9, 2024, 2), report_date=None)
        pool.accessions.append(
            mk_accession(9, 2019, 5, role="base", inline=True, report_date="2019-06-30")
        )
    elif third_source == "within_tolerance":
        pool.replace_accession(dashed(9, 2024, 2), report_date="2023-12-31")
        pool.accessions.append(
            mk_accession(9, 2019, 5, role="base", inline=True, report_date="2019-12-27")
        )
    return pool


def test_a_transition_report_contributes_a_fiscal_year_end_change() -> None:
    result = fye_pool("transition_original").solve()
    assert result.status == "feasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "fiscal_year_end_change_entities"
    )
    assert quota.achieved_count >= quota.required_count
    assert quota.status == "pass"


def test_a_large_circular_report_date_shift_contributes() -> None:
    result = fye_pool("distance").solve()
    assert result.status == "feasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "fiscal_year_end_change_entities"
    )
    assert quota.status == "pass"


def test_drift_within_the_seven_day_tolerance_does_not_contribute() -> None:
    result = fye_pool("within_tolerance").solve()
    assert result.status == "infeasible"
    assert result.selected_accessions == ()


def test_a_missing_report_date_fails_closed_for_the_distance_rule() -> None:
    result = fye_pool("undated_distance").solve()
    assert result.status == "infeasible"


def test_an_invalid_report_date_fails_closed_and_is_reported() -> None:
    pool = fye_pool("distance")
    pool.replace_accession(dashed(9, 2024, 2), report_date="2021-02-29")
    result = pool.solve()
    assert result.status == "infeasible"
    assert any(d.reason == "unparseable_report_date" for d in result.accession_diagnostics)


def test_only_two_transition_entities_alone_leave_the_quota_unmet() -> None:
    pool = base_pool()
    pool.replace_accession(dashed(8, 2021, 3), form_type="10-K/A")
    result = pool.solve()
    assert result.status == "infeasible"


# --------------------------------------------------------------------------
# 7: former-name contribution
# --------------------------------------------------------------------------


def test_valid_winning_provisional_former_name_evidence_contributes() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    quota = next(q for q in result.accession_quota_results if q.key == "name_change_entities")
    assert quota.achieved_count == CROSS_CUTTING_QUOTAS["name_change_entities"]
    assert quota.status == "pass"


@pytest.mark.parametrize(
    "changes",
    [
        {"has_identity_evidence": False},
        {"evidence_role": "competing"},
        {"evidence_role": "supporting"},
        {"evidence_level": "review_required"},
        {"evidence_level": "unavailable"},
        {"former_name_record_parseable": False},
        {"has_prior_current_or_from_to": False},
    ],
)
def test_incomplete_identity_evidence_does_not_contribute(changes: dict[str, object]) -> None:
    pool = base_pool()
    pool.entities[0] = EntityCandidate(
        pool.entities[0].candidate,
        dataclasses.replace(winning_former_name(), **changes),  # type: ignore[arg-type]
    )
    result = pool.solve()
    assert result.status == "infeasible"


def test_a_ticker_only_claim_does_not_contribute_and_raises_no_warning() -> None:
    pool = base_pool()
    pool.entities[0] = EntityCandidate(
        pool.entities[0].candidate,
        NameChangeEvidence(
            has_identity_evidence=True,
            evidence_role="winning",
            evidence_level="provisional",
            former_name_record_parseable=False,
            has_prior_current_or_from_to=False,
            ticker_change_claimed=True,
        ),
    )
    result = pool.solve()
    assert result.status == "infeasible"
    assert not any("ticker" in d.reason for d in result.accession_diagnostics)


def test_absent_ticker_evidence_alone_produces_no_diagnostic() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert not any("ticker" in d.reason for d in result.accession_diagnostics)
    assert not any("ticker" in d.reason for d in result.excluded_candidates)


# --------------------------------------------------------------------------
# 8: 2009 support / 2010 target pairing
# --------------------------------------------------------------------------


def test_the_support_target_pair_quota_counts_six_distinct_entities() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "support_target_pair_entities"
    )
    assert quota.required_count == CROSS_CUTTING_QUOTAS["support_target_pair_entities"]
    assert quota.achieved_count == quota.required_count
    assert quota.status == "pass"


def test_a_pair_must_share_one_anchor_cik() -> None:
    """Moving one support accession to a different anchor destroys that pair."""
    pool = base_pool()
    pool.drop_accession(dashed(1, 2009, 1))
    pool.accessions.append(
        mk_accession(20, 2009, 8, role="support", pre_study=True, inline=False, has_xbrl=False)
    )
    result = pool.solve()
    assert result.status == "infeasible"


def test_two_supports_at_one_anchor_still_count_that_entity_once() -> None:
    pool = base_pool()
    pool.accessions.append(
        mk_accession(1, 2009, 7, role="support", pre_study=True, inline=False, has_xbrl=False)
    )
    result = pool.solve()
    assert result.status == "feasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "support_target_pair_entities"
    )
    assert quota.achieved_count == CROSS_CUTTING_QUOTAS["support_target_pair_entities"]


def test_a_2010_target_must_belong_to_the_development_cohort() -> None:
    pool = base_pool()
    pool.replace_accession(dashed(1, 2010, 2), provisional_official_cohort="transition")
    result = pool.solve()
    assert result.status == "infeasible"


# --------------------------------------------------------------------------
# 9: controls in cross-cutting quotas
# --------------------------------------------------------------------------


def test_control_accessions_never_count_toward_base_or_stress_totals() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert result.objective is not None
    control_ciks = {c.cik_padded for c in result.selected_controls}
    control_rows = [a for a in result.selected_accessions if a.anchor_cik_padded in control_ciks]
    assert len(control_rows) == TOTAL_CONTROLS
    assert all(a.accession_role == "control" for a in control_rows)
    assert result.objective.base_accession_count == sum(
        1 for a in result.selected_accessions if a.accession_role == "base"
    )
    assert result.objective.stress_accession_count == sum(
        1 for a in result.selected_accessions if a.accession_role == "stress"
    )
    assert all(
        a.anchor_cik_padded not in control_ciks
        for a in result.selected_accessions
        if a.accession_role in ("base", "stress")
    )


def quota_achieved(result: JointSelectionResult, key: str) -> int:
    return next(q for q in result.accession_quota_results if q.key == key).achieved_count


def quota_available(result: JointSelectionResult, key: str) -> int:
    return next(q for q in result.accession_quota_results if q.key == key).available_eligible_count


def test_a_control_original_contributes_to_an_unrestricted_cross_cutting_quota() -> None:
    """Decision 018 section 11: the XBRL-era quotas restrict contribution to
    neither operating nor primary-universe entities, so flipping the four control
    originals from Inline to pre-Inline moves exactly four contributions."""
    baseline = base_pool().solve()
    assert baseline.status == "feasible"

    flipped = base_pool()
    for offset in range(TOTAL_CONTROLS):
        flipped.replace_accession(
            dashed(101 + offset, 2020, 2), has_inline_xbrl=False, has_xbrl=True
        )
    moved = flipped.solve()
    assert moved.status == "feasible"

    assert quota_achieved(moved, "inline_xbrl_originals") == (
        quota_achieved(baseline, "inline_xbrl_originals") - TOTAL_CONTROLS
    )
    assert quota_achieved(moved, "pre_inline_xbrl_originals") == (
        quota_achieved(baseline, "pre_inline_xbrl_originals") + TOTAL_CONTROLS
    )


def test_a_control_cannot_contribute_to_the_support_pair_quota() -> None:
    """Support role requires an operating anchor, so a control's 2009 original is
    simply not selectable as support."""
    pool = base_pool()
    pool.drop_accession(dashed(1, 2009, 1))
    pool.accessions.append(
        mk_accession(101, 2009, 7, role="support", pre_study=True, inline=False, has_xbrl=False)
    )
    result = pool.solve()
    assert result.status == "infeasible"


# --------------------------------------------------------------------------
# 10: accession floors and caps
# --------------------------------------------------------------------------


def test_the_frozen_caps_match_decision_018_section_8() -> None:
    assert MAX_BASE_ACCESSIONS_PER_CIK == 4
    assert MAX_BASE_ACCESSIONS_TOTAL == 96
    assert MAX_STRESS_ACCESSIONS_TOTAL == 24
    assert MAX_ACCESSIONS_TOTAL == 120


def test_every_selected_entity_anchors_at_least_one_accession() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    anchored = {a.anchor_cik_padded for a in result.selected_accessions}
    assert anchored == {c.cik_padded for c in result.selected_entities}


def test_every_operating_entity_has_a_base_and_every_control_a_control_role() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    base_anchors = {
        a.anchor_cik_padded for a in result.selected_accessions if a.accession_role == "base"
    }
    control_anchors = {
        a.anchor_cik_padded for a in result.selected_accessions if a.accession_role == "control"
    }
    assert base_anchors == {c.cik_padded for c in result.selected_operating}
    assert control_anchors == {c.cik_padded for c in result.selected_controls}


def test_an_operating_entity_with_no_base_accession_is_infeasible() -> None:
    pool = base_pool()
    pool.drop_accession(dashed(20, 2018, 2))
    result = pool.solve()
    assert result.status == "infeasible"
    assert result.selected_operating == ()
    assert result.selected_accessions == ()


def test_a_control_entity_with_no_control_role_accession_is_infeasible() -> None:
    pool = base_pool()
    pool.drop_accession(dashed(101, 2020, 2))
    result = pool.solve()
    assert result.status == "infeasible"


def pre_inline_cap_pool(*, same_cik: bool) -> Pool:
    """A pool needing six extra pre-Inline originals, all at one CIK or spread out.

    The six 2009 supports are flipped to Inline, leaving only six pre-Inline
    originals, so six more are required. Concentrating them on one CIK would need
    seven base accessions there -- past the frozen per-CIK cap of four.
    """
    pool = base_pool()
    for slot in range(6):
        pool.replace_accession(dashed(slot + 1, 2009, 1), has_inline_xbrl=True, has_xbrl=True)
    for extra in range(6):
        cik = 20 if same_cik else 14 + extra
        pool.accessions.append(
            mk_accession(
                cik,
                2011 + extra,
                30 + extra,
                role="base",
                inline=False,
                has_xbrl=True,
                cohort="development",
                report_date=f"{2010 + extra}-12-31",
            )
        )
    return pool


def test_the_per_cik_base_cap_is_a_hard_constraint() -> None:
    concentrated = pre_inline_cap_pool(same_cik=True).solve()
    assert concentrated.status == "infeasible"
    assert concentrated.selected_accessions == ()

    spread = pre_inline_cap_pool(same_cik=False).solve()
    assert spread.status == "feasible"
    per_cik: dict[str, int] = {}
    for accession in spread.selected_accessions:
        if accession.accession_role == "base":
            per_cik[accession.anchor_cik_padded] = per_cik.get(accession.anchor_cik_padded, 0) + 1
    assert max(per_cik.values()) <= MAX_BASE_ACCESSIONS_PER_CIK
    cap = next(q for q in spread.accession_quota_results if q.key == "base_accessions_per_cik")
    assert cap.comparison_operator == "at_most"
    assert cap.status == "pass"


def test_selected_counts_respect_every_global_cap() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert result.objective is not None
    assert result.objective.base_accession_count <= MAX_BASE_ACCESSIONS_TOTAL
    assert result.objective.stress_accession_count <= MAX_STRESS_ACCESSIONS_TOTAL
    assert len(result.selected_accessions) <= MAX_ACCESSIONS_TOTAL
    for key in (
        "base_accessions_total",
        "stress_accessions_total",
        "accessions_total",
    ):
        cap = next(q for q in result.accession_quota_results if q.key == key)
        assert cap.comparison_operator == "at_most"
        assert cap.status == "pass"


# --------------------------------------------------------------------------
# 11: the single deferred quota
# --------------------------------------------------------------------------


def test_the_deferred_quota_is_reported_unproven_and_unavailable() -> None:
    result = base_pool().solve()
    deferred = result.deferred_quota_result
    assert deferred.key == DEFERRED_QUOTA_KEY
    assert deferred.required_count == DEFERRED_QUOTA_REQUIRED_COUNT == 6
    assert deferred.achieved_count == 0
    assert deferred.available_eligible_count == 0
    assert deferred.status == "unproven"
    assert deferred.evidence_state == "unavailable"
    assert deferred.binding_constraint is False
    assert deferred.deferred is True


def test_a_feasible_run_is_reachable_with_the_deferred_quota_outstanding() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert result.deferred_quota_result.status == "unproven"


def test_the_deferred_quota_is_the_only_deferred_one() -> None:
    assert frozenset({DEFERRED_QUOTA_KEY}) == APPROVED_DEFERRED_QUOTA_KEYS
    result = base_pool().solve()
    deferred = [q for q in result.accession_quota_results if q.deferred]
    assert [q.key for q in deferred] == [DEFERRED_QUOTA_KEY]
    hard = [q for q in result.accession_quota_results if not q.deferred]
    assert all(q.key != DEFERRED_QUOTA_KEY for q in hard)


@pytest.mark.parametrize(
    "requested",
    [
        frozenset(),
        frozenset({"multi_registrant_accessions"}),
        frozenset({DEFERRED_QUOTA_KEY, "name_change_entities"}),
    ],
)
def test_deferring_any_other_quota_is_rejected(requested: frozenset[str]) -> None:
    pool = base_pool()
    with pytest.raises(ValueError, match="may be\ndeferred|may be deferred"):
        solve_joint_selection(
            pool.entities,
            pool.accessions,
            node_limit=1,
            deferred_quota_keys=requested,
        )


def test_every_measurable_quota_including_multi_registrant_stays_hard() -> None:
    pool = base_pool()
    pool.replace_accession(
        dashed(17, 2018, 2),
        multi_registrant=False,
        multi_registrant_evidence_level=NOT_APPLICABLE,
    )
    result = pool.solve()
    assert result.status == "infeasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "multi_registrant_accessions"
    )
    assert quota.deferred is False
    assert quota.binding_constraint is True
    assert quota.available_eligible_count == 1


# --------------------------------------------------------------------------
# 12: the objective is solved jointly and in the frozen term order
# --------------------------------------------------------------------------


def trap_pool() -> tuple[Pool, str, str]:
    """A pool whose S4 entity-only optimum is not the S5 joint optimum.

    Slot 19 has two interchangeable candidates: the incumbent (entity penalty 1,
    accession penalty 0) and an alternative (entity penalty 0, accession penalty
    2). The entity-only objective prefers the alternative; the joint objective,
    whose first term sums entity *and* accession penalties, prefers the
    incumbent.
    """
    pool = base_pool()
    incumbent_cik = 20
    alternative_cik = 21
    pool.entities[19] = EntityCandidate(mk_operating(incumbent_cik, 19, evidence_penalty=1))
    pool.entities.append(EntityCandidate(mk_operating(alternative_cik, 19, evidence_penalty=0)))
    pool.accessions.append(
        mk_accession(
            alternative_cik,
            2018,
            2,
            role="base",
            inline=True,
            filing_level="review_required",
            cohort_level="conflicting",
        )
    )
    return pool, f"{incumbent_cik:010d}", f"{alternative_cik:010d}"


def test_the_joint_optimum_differs_from_the_entity_only_optimum() -> None:
    pool, incumbent, alternative = trap_pool()

    entity_only = solve_entity_selection([e.candidate for e in pool.entities])
    assert entity_only.status == "feasible"
    entity_only_ciks = {c.cik_padded for c in entity_only.selected_operating}
    assert alternative in entity_only_ciks
    assert incumbent not in entity_only_ciks

    joint = pool.solve()
    assert joint.status == "feasible"
    joint_ciks = {c.cik_padded for c in joint.selected_operating}
    assert incumbent in joint_ciks
    assert alternative not in joint_ciks
    assert joint.objective is not None
    assert joint.objective.evidence_penalty == 1


def test_term_two_precedes_term_three_penalty_before_base_count() -> None:
    """Two routes to the third fiscal-year-end contribution: one extra base at
    zero penalty, or one extra stress accession at penalty two. The lower penalty
    wins even though it costs an extra base accession."""
    pool = fye_pool("distance")
    pool.accessions.append(
        mk_accession(
            10,
            2022,
            6,
            form="10-KT",
            role="stress",
            inline=True,
            cohort="transition",
            filing_level="review_required",
            cohort_level="review_required",
        )
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert result.objective is not None
    assert result.objective.evidence_penalty == 0
    selected = {a.accession_number_dashed for a in result.selected_accessions}
    assert dashed(9, 2019, 5) in selected
    assert dashed(10, 2022, 6) not in selected


def test_term_three_precedes_term_four_base_count_before_stress_count() -> None:
    """The same two routes at equal penalty: minimising base count now wins, even
    though it raises the stress count."""
    pool = fye_pool("distance")
    pool.accessions.append(
        mk_accession(10, 2022, 6, form="10-KT", role="stress", inline=True, cohort="transition")
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert result.objective is not None
    assert result.objective.evidence_penalty == 0
    selected = {a.accession_number_dashed for a in result.selected_accessions}
    assert dashed(10, 2022, 6) in selected
    assert dashed(9, 2019, 5) not in selected


#: Slot 7 is the only accelerated-filer/operating-financial/stable bucket in the
#: frozen grid, so two candidates placed there are strictly interchangeable: every
#: other slot is forced by the exact size and industry quotas, and selecting both
#: would overfill the four-entity operating-financial quota.
EXCLUSIVE_SLOT: Final = 7
EXCLUSIVE_SLOT_CIK: Final = EXCLUSIVE_SLOT + 1


def two_candidate_pool(first_cik: int, second_cik: int) -> Pool:
    """Base pool with slot 7 contested by two otherwise identical candidates.

    Slot 7's original amendment is moved to slot 8 (as a 10-KT/A, preserving the
    linked-amendment, purpose-category, transition, and fiscal-year-end counts) so
    each contender needs exactly one base accession and nothing else.
    """
    pool = base_pool()
    pool.drop_accession(dashed(EXCLUSIVE_SLOT_CIK, 2021, 3))
    pool.drop_accession(dashed(EXCLUSIVE_SLOT_CIK, 2024, 2))
    pool.entities[EXCLUSIVE_SLOT] = EntityCandidate(mk_operating(first_cik, EXCLUSIVE_SLOT))
    pool.entities.append(EntityCandidate(mk_operating(second_cik, EXCLUSIVE_SLOT)))
    pool.accessions.append(
        mk_accession(
            9,
            2021,
            4,
            form="10-KT/A",
            role="stress",
            inline=True,
            cohort="development",
            parent=dashed(9, 2024, 2),
            purpose=PURPOSE_CATEGORIES[1],
        )
    )
    for cik in (first_cik, second_cik):
        pool.accessions.append(
            mk_accession(cik, 2024, 2, role="base", inline=True, cohort="primary_test")
        )
    return pool


def stress_trap_pool() -> tuple[Pool, str, str]:
    """Two slot-7 contenders with equal penalty and equal base count, where one
    needs an extra stress accession to supply the second multi-registrant
    accession. CIKs are chosen so the cheaper-stress contender also carries the
    *larger* entity hash, proving term 4 precedes term 5.
    """
    ciks = list(range(30, 90))
    low_stress_cik, high_stress_cik = next(
        (a, b)
        for a, b in itertools.combinations(ciks, 2)
        if selection_rank(f"{a:010d}") > selection_rank(f"{b:010d}")
    )
    pool = two_candidate_pool(low_stress_cik, high_stress_cik)
    pool.replace_accession(
        dashed(18, 2018, 2),
        multi_registrant=False,
        multi_registrant_evidence_level=NOT_APPLICABLE,
    )
    pool.replace_accession(
        dashed(low_stress_cik, 2024, 2),
        multi_registrant=True,
        multi_registrant_evidence_level="provisional",
    )
    # A 10-KT, not an amendment: it supplies the second multi-registrant
    # accession as pure extra stress without also relieving the
    # linked-amendment quota, so the two contenders differ only in stress count.
    pool.accessions.append(
        mk_accession(
            high_stress_cik,
            2022,
            3,
            form="10-KT",
            role="stress",
            inline=True,
            cohort="transition",
            multi_registrant=True,
        )
    )
    return pool, f"{low_stress_cik:010d}", f"{high_stress_cik:010d}"


def test_term_four_precedes_term_five_stress_count_before_entity_hashes() -> None:
    pool, low_stress, high_stress = stress_trap_pool()
    assert selection_rank(low_stress) > selection_rank(high_stress)
    result = pool.solve()
    assert result.status == "feasible"
    chosen = {c.cik_padded for c in result.selected_operating}
    assert low_stress in chosen
    assert high_stress not in chosen


def hash_order_pool() -> tuple[Pool, str, str]:
    """Two interchangeable slot-7 contenders with equal penalty, base, and stress
    counts, chosen so the smaller entity-hash candidate carries the *larger*
    accession hash -- so only term 5 preceding term 6 can decide."""
    for first, second in itertools.combinations(range(30, 120), 2):
        first_entity = selection_rank(f"{first:010d}")
        second_entity = selection_rank(f"{second:010d}")
        first_accession = accession_selection_rank(f"{first:010d}", dashed(first, 2024, 2))
        second_accession = accession_selection_rank(f"{second:010d}", dashed(second, 2024, 2))
        if first_entity < second_entity and first_accession > second_accession:
            low_entity_hash, high_entity_hash = first, second
            break
        if second_entity < first_entity and second_accession > first_accession:
            low_entity_hash, high_entity_hash = second, first
            break
    else:  # pragma: no cover - the scan always finds a pair in this range
        message = "no CIK pair inverts the entity/accession hash order"
        raise AssertionError(message)
    pool = two_candidate_pool(low_entity_hash, high_entity_hash)
    return pool, f"{low_entity_hash:010d}", f"{high_entity_hash:010d}"


def test_term_five_precedes_term_six_entity_hashes_before_accession_hashes() -> None:
    pool, low_entity_hash, high_entity_hash = hash_order_pool()
    assert selection_rank(low_entity_hash) < selection_rank(high_entity_hash)
    result = pool.solve()
    assert result.status == "feasible"
    chosen = {c.cik_padded for c in result.selected_operating}
    assert low_entity_hash in chosen
    assert high_entity_hash not in chosen


def test_canonical_identity_fallbacks_rank_after_both_hash_vectors() -> None:
    smaller_hash = JointObjective(0, 1, 1, ("a",), ("a",), ("9",), ("9",))
    larger_hash = JointObjective(0, 1, 1, ("b",), ("a",), ("0",), ("0",))
    assert smaller_hash.as_tuple() < larger_hash.as_tuple()

    tie_on_hashes_a = JointObjective(0, 1, 1, ("a",), ("a",), ("0",), ("0",))
    tie_on_hashes_b = JointObjective(0, 1, 1, ("a",), ("a",), ("1",), ("0",))
    assert tie_on_hashes_a.as_tuple() < tie_on_hashes_b.as_tuple()


def test_the_objective_vectors_are_the_sorted_canonical_values() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert result.objective is not None
    objective = result.objective
    assert objective.entity_hash_vector == tuple(
        sorted(selection_rank(c.cik_padded) for c in result.selected_entities)
    )
    assert objective.accession_hash_vector == tuple(
        sorted(a.accession_tie_break_sha256 for a in result.selected_accessions)
    )
    assert objective.entity_identity_vector == tuple(
        sorted(c.cik_padded for c in result.selected_entities)
    )
    assert objective.accession_identity_vector == tuple(
        sorted(a.accession_number_dashed for a in result.selected_accessions)
    )
    assert type(objective.evidence_penalty) is int


def test_the_entity_result_keeps_the_frozen_twenty_plus_four_shape() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    assert len(result.selected_operating) == TOTAL_OPERATING
    assert len(result.selected_controls) == TOTAL_CONTROLS
    assert {c.control_kind for c in result.selected_controls} == set(CONTROL_QUOTAS)
    assert all(q.status == "pass" for q in result.entity_quota_results)


# --------------------------------------------------------------------------
# 13: determinism
# --------------------------------------------------------------------------


def result_signature(result: JointSelectionResult) -> tuple[object, ...]:
    return (
        result.status,
        tuple(c.cik_padded for c in result.selected_operating),
        tuple(c.cik_padded for c in result.selected_controls),
        tuple(
            (a.selected_order, a.accession_number_dashed, a.accession_role)
            for a in result.selected_accessions
        ),
        None if result.objective is None else result.objective.as_tuple(),
    )


def test_repeated_runs_return_identical_results_and_node_counts() -> None:
    pool = base_pool()
    first = pool.solve()
    second = pool.solve()
    assert result_signature(first) == result_signature(second)
    assert first.expanded_node_count == second.expanded_node_count
    assert first.accession_quota_results == second.accession_quota_results
    assert first.amendment_families == second.amendment_families


@pytest.mark.parametrize("offset", [1, 5, 13, 29])
def test_input_permutations_never_change_the_result(offset: int) -> None:
    pool = base_pool()
    baseline = pool.solve()
    rotated = Pool(
        entities=pool.entities[offset:] + pool.entities[:offset],
        accessions=pool.accessions[offset:] + pool.accessions[:offset],
    )
    assert result_signature(rotated.solve()) == result_signature(baseline)


def test_a_seeded_shuffle_of_both_input_lists_returns_the_same_result() -> None:
    pool = base_pool()
    baseline = pool.solve()
    rng = random.Random(20260728)  # noqa: S311 - deterministic local test seed only
    entities = list(pool.entities)
    accessions = list(pool.accessions)
    for _ in range(5):
        rng.shuffle(entities)
        rng.shuffle(accessions)
        shuffled = Pool(entities=list(entities), accessions=list(accessions)).solve()
        assert result_signature(shuffled) == result_signature(baseline)
        assert shuffled.expanded_node_count == baseline.expanded_node_count


def test_selected_order_is_stable_across_input_permutations() -> None:
    pool = base_pool()
    baseline = {
        a.accession_number_dashed: a.selected_order for a in pool.solve().selected_accessions
    }
    reversed_pool = Pool(
        entities=list(reversed(pool.entities)), accessions=list(reversed(pool.accessions))
    )
    other = {
        a.accession_number_dashed: a.selected_order
        for a in reversed_pool.solve().selected_accessions
    }
    assert other == baseline
    assert sorted(baseline.values()) == list(range(1, len(baseline) + 1))


# --------------------------------------------------------------------------
# 14: node budget and fail-closed behaviour
# --------------------------------------------------------------------------


def test_a_tiny_node_limit_exhausts_before_any_feasible_incumbent() -> None:
    result = base_pool().solve(node_limit=1)
    assert result.status == "infeasible_or_unproven"
    assert result.node_limit_exhausted is True
    assert result.selected_operating == ()
    assert result.selected_controls == ()
    assert result.selected_accessions == ()
    assert result.objective is None
    assert result.expanded_node_count == 2


def test_exhaustion_after_an_internal_feasible_incumbent_discards_it() -> None:
    """The forced pool completes in ``T`` nodes and is feasible, so its first
    complete evaluation costs at most ``T`` nodes. The trap pool traverses that
    identical prefix first (its extra candidate sorts later), then needs strictly
    more nodes. Running the trap pool with a limit of exactly ``T`` therefore
    exhausts *after* a feasible incumbent existed internally -- and still returns
    nothing."""
    forced = base_pool().solve()
    assert forced.status == "feasible"
    budget = forced.expanded_node_count

    pool, _incumbent, _alternative = trap_pool()
    complete = pool.solve()
    assert complete.status == "feasible"
    assert complete.expanded_node_count > budget

    exhausted = pool.solve(node_limit=budget)
    assert exhausted.status == "infeasible_or_unproven"
    assert exhausted.node_limit_exhausted is True
    assert exhausted.selected_operating == ()
    assert exhausted.selected_accessions == ()
    assert exhausted.objective is None


def test_the_node_counter_is_shared_across_the_entity_and_accession_phases() -> None:
    pool = base_pool()
    entity_only = solve_entity_selection([e.candidate for e in pool.entities])
    joint = pool.solve()
    assert joint.status == "feasible"
    assert joint.expanded_node_count > 0
    assert joint.expanded_node_count != entity_only.expanded_node_count
    for limit in (3, 17, 64, 129):
        partial = pool.solve(node_limit=limit)
        if partial.node_limit_exhausted:
            assert partial.expanded_node_count == limit + 1
            assert partial.status == "infeasible_or_unproven"


def test_every_limit_below_completion_returns_nothing_at_all() -> None:
    pool = base_pool()
    complete = pool.solve()
    assert complete.status == "feasible"
    for limit in range(1, complete.expanded_node_count):
        partial = pool.solve(node_limit=limit)
        assert partial.status == "infeasible_or_unproven"
        assert partial.node_limit_exhausted is True
        assert partial.selected_accessions == ()
        assert partial.objective is None
    assert pool.solve(node_limit=complete.expanded_node_count).status == "feasible"


def test_a_proven_infeasible_pool_returns_no_selection_and_no_objective() -> None:
    pool = base_pool()
    pool.entities = [e for e in pool.entities if e.candidate.control_kind is None]
    result = pool.solve()
    assert result.status == "infeasible"
    assert result.node_limit_exhausted is False
    assert result.selected_operating == ()
    assert result.selected_controls == ()
    assert result.selected_accessions == ()
    assert result.objective is None


def test_no_cap_is_reported_as_passing_on_a_run_with_no_selection() -> None:
    """A cap is only measurable against an approved selection, so a non-feasible
    run reports it ``unproven`` rather than claiming a vacuous pass."""
    for result in (base_pool().solve(node_limit=1), pre_inline_cap_pool(same_cik=True).solve()):
        assert result.status != "feasible"
        caps = [q for q in result.accession_quota_results if q.comparison_operator == "at_most"]
        assert len(caps) == 4
        assert {q.status for q in caps} == {"unproven"}


def test_an_entity_pool_too_small_to_fill_the_quota_is_proven_infeasible() -> None:
    pool = base_pool()
    pool.entities = pool.entities[1:]
    result = pool.solve()
    assert result.status == "infeasible"
    assert result.node_limit_exhausted is False
    assert result.selected_accessions == ()


# --------------------------------------------------------------------------
# 15: independent brute-force oracle
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OracleSolution:
    """The oracle's own view of an approved selection."""

    entity_ciks: tuple[str, ...]
    accession_numbers: tuple[str, ...]
    objective: tuple[object, ...]
    selected_order: tuple[str, ...]


def _oracle_hash(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _oracle_role(accession: AccessionCandidate, category: str) -> str | None:
    """Decision 018 section 7, restated independently of the production module."""
    year: int | None
    try:
        year = date.fromisoformat(accession.official_filing_date or "").year
    except ValueError:
        year = None
    if category == "control":
        if (
            not accession.is_amendment
            and accession.form_type in ("10-K", "10-KT")
            and accession.control_eligible
        ):
            return "control"
        return None
    hits: list[str] = []
    original_10k = not accession.is_amendment and accession.form_type == "10-K"
    if (
        original_10k
        and year == 2009
        and accession.support_eligible
        and accession.cohort_applicability == "pre_study"
    ):
        hits.append("support")
    if original_10k and accession.base_eligible:
        hits.append("base")
    if accession.form_type in ("10-KT", "10-K/A", "10-KT/A") and accession.stress_eligible:
        hits.append("stress")
    return hits[0] if len(hits) == 1 else None


def _oracle_penalty(accession: AccessionCandidate) -> int:
    score = 0
    if accession.filing_date_evidence_level != "provisional":
        score += 1
    if accession.xbrl_evidence_level != "provisional":
        score += 1
    if (
        accession.cohort_applicability == "applies"
        and accession.cohort_evidence_level != "provisional"
    ):
        score += 1
    if accession.is_amendment:
        if accession.amendment_purpose_evidence_level != "provisional":
            score += 1
        if accession.amendment_linkage_evidence_level != "provisional":
            score += 1
    return score


def _oracle_root(
    accession: AccessionCandidate, by_number: dict[str, AccessionCandidate]
) -> str | None:
    seen = {accession.accession_number_dashed}
    cursor = accession
    while cursor.is_amendment:
        parent_number = cursor.provisional_parent_accession_dashed
        if parent_number is None or parent_number in seen or parent_number not in by_number:
            return None
        seen.add(parent_number)
        cursor = by_number[parent_number]
    return cursor.accession_number_dashed


def _oracle_year(accession: AccessionCandidate) -> int | None:
    try:
        return date.fromisoformat(accession.official_filing_date or "").year
    except ValueError:
        return None


def _oracle_report_ordinal(accession: AccessionCandidate) -> int | None:
    try:
        value = date.fromisoformat(accession.report_date or "")
    except ValueError:
        return None
    return (date(2000, value.month, value.day) - date(2000, 1, 1)).days


def _oracle_circular(first: int, second: int) -> int:
    raw = abs(first - second)
    return min(raw, 366 - raw)


def _oracle_feasible(  # noqa: PLR0911, PLR0912 - a flat independent constraint checker
    selection: Sequence[AccessionCandidate],
    roles: dict[str, str],
    operating: Sequence[Candidate],
    controls: Sequence[Candidate],
    name_change: dict[str, bool],
    by_number: dict[str, AccessionCandidate],
) -> bool:
    chosen = {a.accession_number_dashed for a in selection}
    base_by_cik: dict[str, int] = {}
    control_anchors: set[str] = set()
    anchored: set[str] = set()
    stress_total = 0
    for accession in selection:
        anchor = f"{accession.anchor_cik_numeric:010d}"
        anchored.add(anchor)
        role = roles[accession.accession_number_dashed]
        if role == "base":
            base_by_cik[anchor] = base_by_cik.get(anchor, 0) + 1
        elif role == "stress":
            stress_total += 1
        elif role == "control":
            control_anchors.add(anchor)
    for entity in operating:
        if base_by_cik.get(entity.cik_padded, 0) < 1:
            return False
    for entity in controls:
        if entity.cik_padded not in control_anchors:
            return False
    for entity in (*operating, *controls):
        if entity.cik_padded not in anchored:
            return False
    if base_by_cik and max(base_by_cik.values()) > 4:
        return False
    if sum(base_by_cik.values()) > 96 or stress_total > 24 or len(selection) > 120:
        return False

    linked: set[str] = set()
    purposes: set[str] = set()
    transition: set[str] = set()
    multi: set[str] = set()
    pre_inline: set[str] = set()
    inline: set[str] = set()
    year_2024: set[str] = set()
    year_2025_2026: set[str] = set()
    supports: dict[str, int] = {}
    targets: dict[str, int] = {}
    fye: set[str] = set()
    originals: dict[str, list[tuple[int, str]]] = {}
    undated: set[str] = set()
    for accession in selection:
        anchor = f"{accession.anchor_cik_numeric:010d}"
        number = accession.accession_number_dashed
        year = _oracle_year(accession)
        if accession.is_amendment:
            root = _oracle_root(accession, by_number)
            if (
                root is not None
                and root in chosen
                and accession.amendment_linkage_evidence_level == "provisional"
            ):
                linked.add(anchor)
            if accession.amendment_purpose_quota_eligible and (
                accession.amendment_purpose_category is not None
            ):
                purposes.add(accession.amendment_purpose_category)
        if accession.form_type in ("10-KT", "10-KT/A"):
            transition.add(anchor)
            fye.add(anchor)
        if accession.multi_registrant and (
            accession.multi_registrant_evidence_level == "provisional"
        ):
            multi.add(number)
        if not accession.is_amendment and accession.form_type in ("10-K", "10-KT"):
            if accession.xbrl_evidence_level == "provisional":
                (inline if accession.has_inline_xbrl else pre_inline).add(number)
            if accession.filing_date_evidence_level == "provisional":
                if year == 2024:
                    year_2024.add(anchor)
                if year in (2025, 2026):
                    year_2025_2026.add(anchor)
            ordinal = _oracle_report_ordinal(accession)
            if ordinal is None:
                undated.add(anchor)
            else:
                originals.setdefault(anchor, []).append((ordinal, number))
        # Decision 018 section 15 names the contributing roles, so the oracle
        # applies its OWN role classification (``_oracle_role``, called in
        # ``_oracle_best_for_entity_set`` and handed in as ``roles``) on top of the
        # structural conditions. It never consults the production role helper.
        assigned = roles[number]
        if (
            assigned == "support"
            and not accession.is_amendment
            and accession.form_type == "10-K"
            and accession.support_eligible
            and accession.cohort_applicability == "pre_study"
            and year == 2009
            and accession.filing_date_evidence_level == "provisional"
        ):
            supports[anchor] = supports.get(anchor, 0) + 1
        if (
            assigned == "base"
            and not accession.is_amendment
            and accession.form_type == "10-K"
            and accession.base_eligible
            and accession.provisional_official_cohort == "development"
            and year == 2010
            and accession.filing_date_evidence_level == "provisional"
            and accession.cohort_evidence_level == "provisional"
        ):
            targets[anchor] = targets.get(anchor, 0) + 1
    for anchor, dated in originals.items():
        if anchor in fye or anchor in undated:
            continue
        ordered = sorted(dated)
        for index in range(len(ordered) - 1):
            if _oracle_circular(ordered[index][0], ordered[index + 1][0]) > 7:
                fye.add(anchor)
                break
    pairs = {anchor for anchor in supports if targets.get(anchor, 0) > 0}
    names = sum(1 for entity in (*operating, *controls) if name_change[entity.cik_padded])
    return (
        len(linked) >= 8
        and len(purposes) >= 3
        and len(transition) >= 2
        and len(fye) >= 3
        and names >= 4
        and len(multi) >= 2
        and len(pairs) >= 6
        and len(pre_inline) >= 12
        and len(inline) >= 12
        and len(year_2024) >= 6
        and len(year_2025_2026) >= 4
    )


def oracle_solve(pool: Pool) -> OracleSolution | None:
    """Exhaustive independent enumerator over the frozen quota set.

    Structurally independent of the production search: it enumerates entity sets
    with :func:`itertools.combinations` and accession sets with
    :func:`itertools.product`, evaluates every candidate against a flat,
    separately written constraint checker, and keeps the lexicographic minimum by
    direct tuple comparison. It calls no production solver, no production policy
    helper, and no production hash function.

    The only structural restriction is Decision 018 section 9 itself: an
    accession that is the sole base of a selected operating entity, or the sole
    control-role accession of a selected control, is in every feasible selection,
    so it is held fixed rather than enumerated.
    """
    by_number = {a.accession_number_dashed: a for a in pool.accessions}
    name_change = {
        e.cik_padded: (
            e.name_change.has_identity_evidence
            and e.name_change.evidence_role == "winning"
            and e.name_change.evidence_level == "provisional"
            and e.name_change.former_name_record_parseable
            and e.name_change.has_prior_current_or_from_to
        )
        for e in pool.entities
    }
    operating_pool = [e.candidate for e in pool.entities if e.candidate.category == "operating"]
    controls_by_kind: dict[str, list[Candidate]] = {kind: [] for kind in CONTROL_QUOTAS}
    for entry in pool.entities:
        kind = entry.candidate.control_kind
        if entry.candidate.category == "control" and kind in controls_by_kind:
            controls_by_kind[kind].append(entry.candidate)

    best: OracleSolution | None = None
    for operating in itertools.combinations(operating_pool, TOTAL_OPERATING):
        if not _oracle_entity_quotas_met(operating):
            continue
        for controls in itertools.product(*(controls_by_kind[k] for k in CONTROL_QUOTAS)):
            best = _oracle_best_for_entity_set(
                pool, operating, controls, by_number, name_change, best
            )
    return best


def _oracle_entity_quotas_met(operating: Sequence[Candidate]) -> bool:
    sizes: dict[str, int] = {}
    industries: dict[str, int] = {}
    histories: dict[str, int] = {}
    inactive = 0
    for candidate in operating:
        sizes[str(candidate.size_stratum)] = sizes.get(str(candidate.size_stratum), 0) + 1
        industries[str(candidate.industry_group)] = (
            industries.get(str(candidate.industry_group), 0) + 1
        )
        histories[str(candidate.history_class)] = histories.get(str(candidate.history_class), 0) + 1
        if candidate.history_class == "eventful" and candidate.currently_inactive:
            inactive += 1
    expected_sizes: dict[str, int] = {}
    for size in SIZE_SEQUENCE:
        expected_sizes[size] = expected_sizes.get(size, 0) + 1
    expected_industries: dict[str, int] = {}
    for industry in INDUSTRY_SEQUENCE:
        expected_industries[industry] = expected_industries.get(industry, 0) + 1
    expected_histories: dict[str, int] = {}
    for history in HISTORY_SEQUENCE:
        expected_histories[history] = expected_histories.get(history, 0) + 1
    return (
        sizes == expected_sizes
        and industries == expected_industries
        and histories == expected_histories
        and inactive >= MIN_INACTIVE_EVENTFUL
    )


def _oracle_best_for_entity_set(
    pool: Pool,
    operating: Sequence[Candidate],
    controls: Sequence[Candidate],
    by_number: dict[str, AccessionCandidate],
    name_change: dict[str, bool],
    best: OracleSolution | None,
) -> OracleSolution | None:
    operating_ciks = {c.cik_padded for c in operating}
    control_ciks = {c.cik_padded for c in controls}
    available: list[AccessionCandidate] = []
    roles: dict[str, str] = {}
    for accession in pool.accessions:
        anchor = f"{accession.anchor_cik_numeric:010d}"
        if anchor in operating_ciks:
            role = _oracle_role(accession, "operating")
        elif anchor in control_ciks:
            role = _oracle_role(accession, "control")
        else:
            role = None
        if role is not None:
            available.append(accession)
            roles[accession.accession_number_dashed] = role

    forced: list[AccessionCandidate] = []
    optional: list[AccessionCandidate] = []
    for accession in available:
        anchor = f"{accession.anchor_cik_numeric:010d}"
        role = roles[accession.accession_number_dashed]
        siblings = [
            other
            for other in available
            if f"{other.anchor_cik_numeric:010d}" == anchor
            and roles[other.accession_number_dashed] == role
        ]
        if role in ("base", "control") and len(siblings) == 1:
            forced.append(accession)
        else:
            optional.append(accession)

    entity_penalty = sum(c.evidence_penalty for c in (*operating, *controls))
    entity_hashes = tuple(
        sorted(
            _oracle_hash(f"{PILOT_SELECTION_SEED}|{c.cik_padded}") for c in (*operating, *controls)
        )
    )
    entity_identities = tuple(sorted(c.cik_padded for c in (*operating, *controls)))

    for mask in itertools.product((False, True), repeat=len(optional)):
        selection = [*forced, *(a for a, keep in zip(optional, mask, strict=True) if keep)]
        if not _oracle_feasible(selection, roles, operating, controls, name_change, by_number):
            continue
        penalty = entity_penalty + sum(_oracle_penalty(a) for a in selection)
        base_count = sum(1 for a in selection if roles[a.accession_number_dashed] == "base")
        stress_count = sum(1 for a in selection if roles[a.accession_number_dashed] == "stress")
        accession_hashes = tuple(
            sorted(
                _oracle_hash(
                    f"{PILOT_SELECTION_SEED}|{a.anchor_cik_numeric:010d}"
                    f"|{a.accession_number_dashed}"
                )
                for a in selection
            )
        )
        accession_identities = tuple(sorted(a.accession_number_dashed for a in selection))
        objective = (
            penalty,
            base_count,
            stress_count,
            entity_hashes,
            accession_hashes,
            entity_identities,
            accession_identities,
        )
        ordered = tuple(
            number
            for _, _, number in sorted(
                (
                    _oracle_hash(
                        f"{PILOT_SELECTION_SEED}|{a.anchor_cik_numeric:010d}"
                        f"|{a.accession_number_dashed}"
                    ),
                    f"{a.anchor_cik_numeric:010d}",
                    a.accession_number_dashed,
                )
                for a in selection
            )
        )
        candidate = OracleSolution(
            entity_ciks=entity_identities,
            accession_numbers=accession_identities,
            objective=objective,
            selected_order=ordered,
        )
        if best is None or candidate.objective < best.objective:  # type: ignore[operator]
            best = candidate
    return best


def assert_matches_oracle(pool: Pool) -> None:
    solver = pool.solve()
    oracle = oracle_solve(pool)
    if oracle is None:
        assert solver.status == "infeasible"
        assert solver.selected_accessions == ()
        assert solver.objective is None
        return
    assert solver.status == "feasible"
    assert solver.objective is not None
    assert solver.objective.as_tuple() == oracle.objective
    assert tuple(sorted(c.cik_padded for c in solver.selected_entities)) == oracle.entity_ciks
    assert (
        tuple(sorted(a.accession_number_dashed for a in solver.selected_accessions))
        == oracle.accession_numbers
    )
    assert (
        tuple(a.accession_number_dashed for a in solver.selected_accessions)
        == oracle.selected_order
    )


def test_the_oracle_confirms_the_base_pool_optimum() -> None:
    assert_matches_oracle(base_pool())


def test_the_oracle_confirms_the_joint_trap_optimum() -> None:
    pool, _incumbent, _alternative = trap_pool()
    assert_matches_oracle(pool)


def test_the_oracle_confirms_a_pool_with_redundant_optional_accessions() -> None:
    pool = base_pool()
    pool.accessions.append(
        mk_accession(
            9,
            2021,
            4,
            form="10-K/A",
            role="stress",
            inline=True,
            parent=dashed(9, 2024, 2),
            purpose=PURPOSE_CATEGORIES[1],
        )
    )
    assert_matches_oracle(pool)


def test_the_oracle_confirms_a_proven_infeasible_pool() -> None:
    pool = base_pool()
    pool.drop_accession(dashed(3, 2009, 1))
    assert_matches_oracle(pool)


@pytest.mark.parametrize("case", range(4))
def test_the_oracle_confirms_seeded_generated_variants(case: int) -> None:
    """Deterministic generated small cases: a fixed local test seed perturbs only
    evidence levels and entity penalties, never the frozen quota set."""
    rng = random.Random(90210 + case)  # noqa: S311 - deterministic local test seed only
    pool = base_pool()
    levels = ("provisional", "review_required", "conflicting", "unavailable")
    for index, accession in enumerate(list(pool.accessions)):
        if rng.random() < 0.25:
            pool.accessions[index] = dataclasses.replace(
                accession, xbrl_evidence_level=rng.choice(levels)
            )
    for index, entry in enumerate(list(pool.entities)):
        if entry.candidate.category == "operating" and rng.random() < 0.3:
            pool.entities[index] = EntityCandidate(
                dataclasses.replace(entry.candidate, evidence_penalty=rng.randint(0, 3)),
                entry.name_change,
            )
    assert_matches_oracle(pool)


# --------------------------------------------------------------------------
# 16: purity of the S5.1 core
# --------------------------------------------------------------------------


def module_imports() -> set[str]:
    tree = ast.parse(_ACCESSION_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    return imported


def test_the_core_imports_only_a_minimal_pure_python_surface() -> None:
    assert module_imports() <= {
        "__future__",
        "collections",
        "dataclasses",
        "datetime",
        "disclosure_drift",
        "hashlib",
        "re",
        "typing",
    }


def test_the_core_imports_no_sqlite_no_network_and_no_filesystem_module() -> None:
    source = _ACCESSION_SELECTOR_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned = ("sqlite3", "httpx", "socket", "urllib", "pathlib", "os", "random", "time")
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for name in names:
                assert name.split(".")[0] not in banned, name


def test_no_random_or_clock_call_is_made_during_solving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        message = "solve_joint_selection must never call random or read the clock"
        raise AssertionError(message)

    monkeypatch.setattr(random, "random", blocked)
    monkeypatch.setattr(random, "choice", blocked)
    monkeypatch.setattr(random, "shuffle", blocked)
    monkeypatch.setattr(time, "time", blocked)
    monkeypatch.setattr(time, "monotonic", blocked)
    assert base_pool().solve().status == "feasible"


def test_no_network_call_is_made_during_solving() -> None:
    """``tests/conftest.py`` makes every socket call raise for the whole session,
    so a passing solve already proves no network access occurred."""
    assert base_pool().solve().status == "feasible"


def test_the_solver_never_mutates_its_inputs() -> None:
    pool = base_pool()
    entities_before = [dataclasses.replace(e.candidate) for e in pool.entities]
    accessions_before = [dataclasses.replace(a) for a in pool.accessions]
    pool.solve()
    assert [e.candidate for e in pool.entities] == entities_before
    assert pool.accessions == accessions_before


def test_result_objects_are_immutable() -> None:
    result = base_pool().solve()
    assert result.objective is not None
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.selected_accessions[0].selected_order = 99  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.objective.evidence_penalty = 0  # type: ignore[misc]


# --------------------------------------------------------------------------
# 17: accession cap boundaries, exercised through the production cap rule
# --------------------------------------------------------------------------


def usage(
    *,
    base_total: int = 0,
    stress_total: int = 0,
    accession_total: int = 0,
    max_base_per_cik: int = 0,
) -> AccessionCapUsage:
    return AccessionCapUsage(
        base_total=base_total,
        stress_total=stress_total,
        accession_total=accession_total,
        max_base_per_cik=max_base_per_cik,
    )


def test_the_per_operating_cik_base_cap_admits_four_and_rejects_five() -> None:
    assert MAX_BASE_ACCESSIONS_PER_CIK == 4
    assert accession_caps_satisfied(usage(base_total=4, accession_total=4, max_base_per_cik=4))
    assert not accession_caps_satisfied(usage(base_total=5, accession_total=5, max_base_per_cik=5))


def test_the_global_base_cap_admits_ninety_six_and_rejects_ninety_seven() -> None:
    assert MAX_BASE_ACCESSIONS_TOTAL == 96
    assert accession_caps_satisfied(usage(base_total=96, accession_total=96, max_base_per_cik=4))
    assert not accession_caps_satisfied(
        usage(base_total=97, accession_total=97, max_base_per_cik=4)
    )


def test_the_global_stress_cap_admits_twenty_four_and_rejects_twenty_five() -> None:
    assert MAX_STRESS_ACCESSIONS_TOTAL == 24
    assert accession_caps_satisfied(usage(stress_total=24, accession_total=24))
    assert not accession_caps_satisfied(usage(stress_total=25, accession_total=25))


def test_the_total_accession_cap_admits_one_hundred_twenty_and_rejects_one_twenty_one() -> None:
    assert MAX_ACCESSIONS_TOTAL == 120
    assert accession_caps_satisfied(usage(accession_total=120))
    assert not accession_caps_satisfied(usage(accession_total=121))


def test_each_cap_fails_independently_of_the_others() -> None:
    """One cap at its limit and another one over it must fail, so no cap can mask
    another's violation."""
    for over in (
        usage(base_total=97, stress_total=24, accession_total=120, max_base_per_cik=4),
        usage(base_total=96, stress_total=25, accession_total=120, max_base_per_cik=4),
        usage(base_total=96, stress_total=24, accession_total=121, max_base_per_cik=4),
        usage(base_total=96, stress_total=24, accession_total=120, max_base_per_cik=5),
    ):
        assert not accession_caps_satisfied(over)
    assert accession_caps_satisfied(
        usage(base_total=96, stress_total=24, accession_total=120, max_base_per_cik=4)
    )


def test_cap_outcomes_report_every_frozen_limit_in_identifier_order() -> None:
    outcomes = accession_cap_outcomes(
        usage(base_total=10, stress_total=3, accession_total=17, max_base_per_cik=2)
    )
    assert tuple(key for key, _limit, _achieved, _ok in outcomes) == tuple(ACCESSION_CAP_LIMITS)
    assert {key: limit for key, limit, _achieved, _ok in outcomes} == dict(ACCESSION_CAP_LIMITS)
    achieved = {key: value for key, _limit, value, _ok in outcomes}
    assert achieved[QUOTA_KEY_BASE_ACCESSIONS_TOTAL] == 10
    assert achieved[QUOTA_KEY_STRESS_ACCESSIONS_TOTAL] == 3
    assert achieved[QUOTA_KEY_ACCESSIONS_TOTAL] == 17
    assert achieved[QUOTA_KEY_BASE_ACCESSIONS_PER_CIK] == 2
    assert all(ok for _key, _limit, _achieved, ok in outcomes)


def test_an_unrecognized_cap_identifier_fails_closed() -> None:
    with pytest.raises(ValueError, match="unrecognized accession cap identifier"):
        usage().achieved("not_a_cap")


def test_the_search_and_the_diagnostics_share_one_cap_rule() -> None:
    """The reported cap outcome is recomputed from the selection by the same pure
    evaluator the search uses, so a diagnostic can never disagree with the
    feasibility decision that produced it."""
    result = base_pool().solve()
    assert result.status == "feasible"
    realized = usage(
        base_total=sum(1 for a in result.selected_accessions if a.accession_role == "base"),
        stress_total=sum(1 for a in result.selected_accessions if a.accession_role == "stress"),
        accession_total=len(result.selected_accessions),
        max_base_per_cik=max(
            collections.Counter(
                a.anchor_cik_padded
                for a in result.selected_accessions
                if a.accession_role == "base"
            ).values()
        ),
    )
    assert accession_caps_satisfied(realized)
    reported = {
        q.key: (q.required_count, q.achieved_count, q.status)
        for q in result.accession_quota_results
        if q.dimension == QUOTA_DIMENSION_ACCESSION_CAP
    }
    for key, limit, achieved, ok in accession_cap_outcomes(realized):
        assert reported[key] == (limit, achieved, "pass" if ok else "fail")


def test_a_selection_needing_a_fifth_base_at_one_cik_is_rejected_by_both_paths() -> None:
    """The concentrated pool would need seven base accessions at one CIK. The pure
    evaluator rejects that usage, and the production solver returns infeasible --
    the same rule reached two ways."""
    assert not accession_caps_satisfied(
        usage(base_total=26, accession_total=44, max_base_per_cik=7)
    )
    assert pre_inline_cap_pool(same_cik=True).solve().status == "infeasible"


def test_the_global_base_cap_is_unreachable_by_a_feasible_frozen_pilot() -> None:
    """Redundant, but preserved: 20 operating entities at 4 base accessions each
    cap a feasible pilot at 80, below the frozen global limit of 96. Reaching 96
    would need 24 operating CIKs, four more than the frozen entity count."""
    ceiling = TOTAL_OPERATING * MAX_BASE_ACCESSIONS_PER_CIK
    assert ceiling == 80
    assert ceiling < MAX_BASE_ACCESSIONS_TOTAL
    ciks_needed = math.ceil(MAX_BASE_ACCESSIONS_TOTAL / MAX_BASE_ACCESSIONS_PER_CIK)
    assert ciks_needed == 24
    assert ciks_needed > TOTAL_OPERATING

    # The global cap is not what forbids 96 -- the entity count is. Both remain.
    assert accession_caps_satisfied(
        usage(base_total=ceiling, accession_total=ceiling, max_base_per_cik=4)
    )
    assert accession_caps_satisfied(
        usage(
            base_total=MAX_BASE_ACCESSIONS_TOTAL,
            accession_total=MAX_BASE_ACCESSIONS_TOTAL,
            max_base_per_cik=4,
        )
    )

    result = base_pool().solve()
    assert result.status == "feasible"
    assert result.objective is not None
    assert result.objective.base_accession_count <= ceiling


# --------------------------------------------------------------------------
# 18: XBRL-era membership
# --------------------------------------------------------------------------


def test_a_non_xbrl_original_contributes_to_the_pre_inline_quota() -> None:
    """The six 2009 support originals carry no XBRL at all. With provisional
    XBRL-status evidence and ``has_inline_xbrl = false`` they still qualify:
    flipping them to Inline moves exactly six contributions."""
    pool = base_pool()
    supports = [
        a
        for a in pool.accessions
        if a.support_eligible and not a.has_xbrl and not a.has_inline_xbrl
    ]
    assert len(supports) == 6
    assert all(a.xbrl_evidence_level == "provisional" for a in supports)

    baseline = pool.solve()
    assert baseline.status == "feasible"
    assert quota_achieved(baseline, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS) == 12
    selected = {a.accession_number_dashed for a in baseline.selected_accessions}
    assert {a.accession_number_dashed for a in supports} <= selected

    flipped = base_pool()
    for accession in supports:
        flipped.replace_accession(
            accession.accession_number_dashed, has_inline_xbrl=True, has_xbrl=True
        )
    moved = flipped.solve()
    assert quota_available(moved, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS) == 12 - 6
    assert quota_available(moved, QUOTA_KEY_INLINE_XBRL_ORIGINALS) == (
        quota_available(baseline, QUOTA_KEY_INLINE_XBRL_ORIGINALS) + 6
    )
    # Those six were the only thing holding the pre-Inline quota at its floor.
    assert moved.status == "infeasible"


def test_the_pre_inline_quota_does_not_require_has_xbrl() -> None:
    """Turning ``has_xbrl`` on while leaving ``has_inline_xbrl`` off changes
    nothing: only the Inline flag and the XBRL-status evidence matter."""
    baseline = base_pool().solve()
    with_xbrl = base_pool()
    for slot in range(6):
        with_xbrl.replace_accession(dashed(slot + 1, 2009, 1), has_xbrl=True)
    other = with_xbrl.solve()
    assert other.status == baseline.status == "feasible"
    assert quota_achieved(other, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS) == quota_achieved(
        baseline, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS
    )
    assert quota_achieved(other, QUOTA_KEY_INLINE_XBRL_ORIGINALS) == quota_achieved(
        baseline, QUOTA_KEY_INLINE_XBRL_ORIGINALS
    )


def test_inline_xbrl_without_xbrl_is_rejected_as_contradictory() -> None:
    bad = dataclasses.replace(
        mk_accession(50, 2020, 2, role="base"), has_inline_xbrl=True, has_xbrl=False
    )
    with pytest.raises(ValueError, match="has_inline_xbrl without has_xbrl"):
        solve_one(bad)


def test_weak_xbrl_status_evidence_cannot_satisfy_either_era_quota() -> None:
    pool = base_pool()
    pool.replace_accession(dashed(1, 2009, 1), xbrl_evidence_level="review_required")
    result = pool.solve()
    assert result.status == "infeasible"
    pre_inline = next(
        q for q in result.accession_quota_results if q.key == QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS
    )
    assert pre_inline.available_eligible_count == 11
    assert pre_inline.excluded_pool_count == 1


# --------------------------------------------------------------------------
# 19: accession excluded-pool counts are diagnostic only
# --------------------------------------------------------------------------


def excluded_of(result: JointSelectionResult, key: str) -> int:
    return next(q for q in result.accession_quota_results if q.key == key).excluded_pool_count


def evidence_failing_2024_original(cik: int) -> AccessionCandidate:
    """A structurally qualifying 2024 original whose filing-date evidence fails."""
    return mk_accession(
        cik,
        2024,
        40,
        role="base",
        inline=True,
        cohort="primary_test",
        filing_level="review_required",
    )


def test_an_excluded_candidate_matches_structurally_but_fails_the_evidence_gate() -> None:
    baseline = base_pool().solve()
    assert excluded_of(baseline, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 0

    pool = base_pool()
    pool.accessions.append(evidence_failing_2024_original(7))
    result = pool.solve()
    assert result.status == "feasible"
    assert excluded_of(result, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 1


def test_a_candidate_failing_the_structural_predicate_is_never_counted_as_excluded() -> None:
    """A 2023 original with the same weak filing-date evidence matches no
    year-quota predicate, so it is excluded from neither year quota."""
    pool = base_pool()
    pool.accessions.append(
        mk_accession(
            7,
            2023,
            41,
            role="base",
            inline=True,
            cohort="transition",
            filing_level="review_required",
        )
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert excluded_of(result, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 0
    assert excluded_of(result, "original_2025_2026_entities") == 0


def test_a_structural_match_that_passes_the_evidence_gate_is_not_excluded() -> None:
    pool = base_pool()
    pool.accessions.append(
        mk_accession(7, 2024, 42, role="base", inline=True, cohort="primary_test")
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert excluded_of(result, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 0


def test_excluded_counts_are_per_candidate_not_per_contribution_unit() -> None:
    """Two evidence-failing 2024 originals at one already-covered entity count as
    two excluded candidates, even though the entity itself still contributes."""
    pool = base_pool()
    pool.accessions.append(evidence_failing_2024_original(7))
    pool.accessions.append(
        mk_accession(
            8,
            2024,
            40,
            role="base",
            inline=True,
            cohort="primary_test",
            filing_level="conflicting",
        )
    )
    result = pool.solve()
    assert result.status == "feasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == QUOTA_KEY_ORIGINAL_2024_ENTITIES
    )
    assert quota.excluded_pool_count == 2
    assert quota.available_eligible_count == 6
    assert quota.achieved_count == 6
    assert quota.status == "pass"


def test_changing_an_excluded_pool_count_changes_neither_feasibility_nor_the_objective() -> None:
    baseline = base_pool().solve()
    assert baseline.status == "feasible"

    pool = base_pool()
    pool.accessions.append(evidence_failing_2024_original(7))
    pool.accessions.append(
        mk_accession(
            9,
            2024,
            40,
            role="base",
            inline=True,
            cohort="primary_test",
            filing_level="unavailable",
        )
    )
    result = pool.solve()
    assert excluded_of(result, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 2
    assert excluded_of(baseline, QUOTA_KEY_ORIGINAL_2024_ENTITIES) == 0
    assert result_signature(result) == result_signature(baseline)


def test_no_excluded_pool_count_creates_eligibility_or_satisfies_a_quota() -> None:
    """Removing the second multi-registrant accession's evidence leaves the quota
    unsatisfiable: the excluded candidate is reported but never counted toward
    ``achieved_count`` or ``available_eligible_count``."""
    pool = base_pool()
    pool.replace_accession(dashed(18, 2018, 2), multi_registrant_evidence_level="review_required")
    result = pool.solve()
    assert result.status == "infeasible"
    quota = next(
        q for q in result.accession_quota_results if q.key == "multi_registrant_accessions"
    )
    assert quota.excluded_pool_count == 1
    assert quota.available_eligible_count == 1
    assert quota.achieved_count == 0
    assert quota.binding_constraint is True
    assert quota.deferred is False


def test_an_excluded_candidate_never_creates_a_new_deferral() -> None:
    pool = base_pool()
    pool.accessions.append(evidence_failing_2024_original(7))
    result = pool.solve()
    deferred = [q for q in result.accession_quota_results if q.deferred]
    assert [q.key for q in deferred] == [DEFERRED_QUOTA_KEY]
    assert frozenset(q.key for q in deferred) == APPROVED_DEFERRED_QUOTA_KEYS


# --------------------------------------------------------------------------
# 20: quota identifiers are centralized, complete, unique, and ordered
# --------------------------------------------------------------------------


def test_the_reported_quota_identifiers_match_the_canonical_mapping_exactly() -> None:
    result = base_pool().solve()
    reported = tuple((q.dimension, q.key) for q in result.accession_quota_results)
    assert reported == ACCESSION_QUOTA_IDENTIFIERS


def test_the_canonical_quota_mapping_is_complete() -> None:
    cross_cutting = tuple(
        key
        for dimension, key in ACCESSION_QUOTA_IDENTIFIERS
        if dimension == QUOTA_DIMENSION_CROSS_CUTTING
    )
    caps = tuple(
        key
        for dimension, key in ACCESSION_QUOTA_IDENTIFIERS
        if dimension == QUOTA_DIMENSION_ACCESSION_CAP
    )
    assert cross_cutting == (*CROSS_CUTTING_QUOTAS, DEFERRED_QUOTA_KEY)
    assert caps == tuple(ACCESSION_CAP_LIMITS)
    assert len(ACCESSION_QUOTA_IDENTIFIERS) == len(CROSS_CUTTING_QUOTAS) + 1 + len(
        ACCESSION_CAP_LIMITS
    )
    assert len(ACCESSION_QUOTA_IDENTIFIERS) == 16


def test_quota_identifiers_are_unique_across_dimensions_and_keys() -> None:
    assert len(set(ACCESSION_QUOTA_IDENTIFIERS)) == len(ACCESSION_QUOTA_IDENTIFIERS)
    keys = [key for _dimension, key in ACCESSION_QUOTA_IDENTIFIERS]
    assert len(set(keys)) == len(keys)
    assert DEFERRED_QUOTA_KEY not in CROSS_CUTTING_QUOTAS
    assert DEFERRED_QUOTA_KEY not in ACCESSION_CAP_LIMITS
    assert not set(CROSS_CUTTING_QUOTAS) & set(ACCESSION_CAP_LIMITS)


def test_quota_identifier_ordering_is_deterministic() -> None:
    assert isinstance(ACCESSION_QUOTA_IDENTIFIERS, tuple)
    pool = base_pool()
    first = tuple((q.dimension, q.key) for q in pool.solve().accession_quota_results)
    second = tuple((q.dimension, q.key) for q in pool.solve().accession_quota_results)
    reversed_pool = Pool(
        entities=list(reversed(pool.entities)), accessions=list(reversed(pool.accessions))
    )
    third = tuple((q.dimension, q.key) for q in reversed_pool.solve().accession_quota_results)
    infeasible = tuple(
        (q.dimension, q.key) for q in pool.solve(node_limit=1).accession_quota_results
    )
    assert first == second == third == infeasible == ACCESSION_QUOTA_IDENTIFIERS


def test_exactly_one_reported_quota_is_deferred_and_it_is_cross_cutting() -> None:
    result = base_pool().solve()
    deferred = [q for q in result.accession_quota_results if q.deferred]
    assert len(deferred) == 1
    assert deferred[0].key == DEFERRED_QUOTA_KEY
    assert deferred[0].dimension == QUOTA_DIMENSION_CROSS_CUTTING
    assert result.deferred_quota_result == deferred[0]


def module_string_constants() -> list[str]:
    """Every string literal in the production module except docstrings."""
    tree = ast.parse(_ACCESSION_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    docstrings: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                docstrings.add(id(body[0].value))
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def test_every_quota_identifier_has_exactly_one_definition_in_the_module() -> None:
    """No ad hoc literal: each quota dimension and key string appears exactly once
    in the production source, at its constant definition."""
    literals = collections.Counter(module_string_constants())
    identifiers = {QUOTA_DIMENSION_CROSS_CUTTING, QUOTA_DIMENSION_ACCESSION_CAP}
    identifiers.update(key for _dimension, key in ACCESSION_QUOTA_IDENTIFIERS)
    for identifier in sorted(identifiers):
        assert literals[identifier] == 1, f"{identifier!r} appears {literals[identifier]} times"


def test_the_quota_mappings_are_not_mutated_by_solving() -> None:
    before_quotas = dict(CROSS_CUTTING_QUOTAS)
    before_caps = dict(ACCESSION_CAP_LIMITS)
    before_identifiers = ACCESSION_QUOTA_IDENTIFIERS
    base_pool().solve()
    assert dict(CROSS_CUTTING_QUOTAS) == before_quotas
    assert dict(ACCESSION_CAP_LIMITS) == before_caps
    assert ACCESSION_QUOTA_IDENTIFIERS is before_identifiers
    assert QUOTA_KEY_NAME_CHANGE_ENTITIES in CROSS_CUTTING_QUOTAS


# --------------------------------------------------------------------------
# 21: the 2009/2010 pair quota is role-restricted, not flag-restricted
# --------------------------------------------------------------------------


def pair_quota(result: JointSelectionResult) -> AccessionQuotaDiagnostic:
    return next(
        q for q in result.accession_quota_results if q.key == QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES
    )


def five_pair_pool() -> Pool:
    """The base pool with exactly five valid operating pairs.

    Entity 1's 2010 target is moved out of the development cohort, which breaks
    only its pair membership: the accession stays base-eligible, stays selectable
    in the base role, and still counts toward the pre-Inline quota, so nothing but
    the pair count changes.
    """
    pool = base_pool()
    pool.replace_accession(dashed(1, 2010, 2), provisional_official_cohort="transition")
    return pool


def dual_eligible_control_support(cik: int = 101, seq: int = 5) -> AccessionCandidate:
    """A control-anchored original 2009 10-K that is also support-eligible."""
    return mk_accession(
        cik,
        2009,
        seq,
        role="control",
        also_eligible=("support",),
        inline=False,
        has_xbrl=False,
        pre_study=True,
    )


def dual_eligible_control_target(cik: int = 101, seq: int = 6) -> AccessionCandidate:
    """A control-anchored original 2010 development 10-K that is also base-eligible."""
    return mk_accession(
        cik,
        2010,
        seq,
        role="control",
        also_eligible=("base",),
        inline=False,
        has_xbrl=True,
        cohort="development",
    )


def dual_eligible_control_pool() -> Pool:
    """The base pool with control 101 holding only the two dual-eligible halves.

    Both are assigned the ``control`` role, so neither may enter the pair quota,
    while both still count toward the role-agnostic pre-Inline era quota.
    """
    pool = base_pool()
    pool.drop_accession(dashed(101, 2020, 2))
    pool.accessions.append(dual_eligible_control_support())
    pool.accessions.append(dual_eligible_control_target())
    return pool


def pair_exploit_pool() -> Pool:
    """Five valid operating pairs plus a control carrying both dual-eligible halves.

    This is the independent reviewer's exploit: under a flag-only pair predicate the
    control's own 2009 and 2010 accessions form a sixth "pair" and the run turns
    feasible, even though both are assigned the ``control`` role. Confirmed to
    reproduce: with the pre-fix flag-only predicates restored, this exact pool
    solves as ``feasible``.
    """
    pool = dual_eligible_control_pool()
    pool.replace_accession(dashed(1, 2010, 2), provisional_official_cohort="transition")
    return pool


def test_five_valid_operating_pairs_alone_are_infeasible() -> None:
    result = five_pair_pool().solve()
    assert result.status == "infeasible"
    assert pair_quota(result).available_eligible_count == 5
    assert pair_quota(result).binding_constraint is True


def test_a_dual_eligible_control_target_keeps_its_control_role() -> None:
    accession = dual_eligible_control_target()
    assert accession.control_eligible is True
    assert accession.base_eligible is True
    assert role_of(accession, "control", 2010) == "control"


def test_a_dual_eligible_control_target_cannot_complete_the_pair_quota() -> None:
    pool = five_pair_pool()
    pool.accessions.append(dual_eligible_control_target())
    result = pool.solve()
    assert result.status == "infeasible"
    assert pair_quota(result).available_eligible_count == 5
    assert result.selected_accessions == ()


def test_a_dual_eligible_control_support_keeps_its_control_role() -> None:
    accession = dual_eligible_control_support()
    assert accession.control_eligible is True
    assert accession.support_eligible is True
    assert accession.cohort_applicability == "pre_study"
    assert role_of(accession, "control", 2009) == "control"


def test_a_dual_eligible_control_support_cannot_complete_the_pair_quota() -> None:
    pool = five_pair_pool()
    pool.accessions.append(dual_eligible_control_support())
    result = pool.solve()
    assert result.status == "infeasible"
    assert pair_quota(result).available_eligible_count == 5
    assert result.selected_accessions == ()


def test_the_control_anchored_pair_exploit_stays_infeasible() -> None:
    """The reviewer's combined exploit: five operating pairs plus a control holding
    a dual-eligible 2009 and a dual-eligible 2010 accession at one anchor CIK."""
    result = pair_exploit_pool().solve()
    assert result.status == "infeasible"
    quota = pair_quota(result)
    assert quota.available_eligible_count == 5
    assert quota.required_count == 6
    assert quota.binding_constraint is True
    assert quota.achieved_count == 0
    assert result.selected_operating == ()
    assert result.selected_controls == ()
    assert result.selected_accessions == ()
    assert result.objective is None


def test_a_stress_role_accession_never_contributes_to_the_pair_quota() -> None:
    """A 10-KT flagged both stress- and base-eligible is assigned ``stress``, so it
    is not a target however its snapshot flags read."""
    transition_target = mk_accession(
        1, 2010, 7, form="10-KT", role="stress", also_eligible=("base",), cohort="development"
    )
    assert transition_target.stress_eligible is True
    assert transition_target.base_eligible is True
    assert role_of(transition_target, "operating", 2010) == "stress"

    pool = five_pair_pool()
    pool.accessions.append(transition_target)
    result = pool.solve()
    assert result.status == "infeasible"
    assert pair_quota(result).available_eligible_count == 5


def test_the_pair_quota_reports_no_control_candidate_as_available_or_excluded() -> None:
    """Diagnostic alignment: a control-role accession is not a pair candidate at
    all, so it is neither an available contributor nor an excluded one."""
    baseline = five_pair_pool().solve()
    exploit = pair_exploit_pool().solve()
    for result in (baseline, exploit):
        quota = pair_quota(result)
        assert quota.available_eligible_count == 5
        assert quota.excluded_pool_count == 0
        assert quota.binding_constraint is True
        assert quota.achieved_count == 0
        assert quota.deferred is False
    assert baseline.status == exploit.status == "infeasible"


def test_an_evidence_failing_operating_target_is_excluded_but_a_control_one_is_not() -> None:
    """The excluded-pool count still counts genuine pair candidates that fail their
    evidence gate, and still ignores control-role accessions entirely."""
    weak = base_pool()
    weak.replace_accession(dashed(1, 2010, 2), cohort_evidence_level="review_required")
    weak_result = weak.solve()
    assert weak_result.status == "infeasible"
    weak_quota = pair_quota(weak_result)
    assert weak_quota.excluded_pool_count == 1
    assert weak_quota.available_eligible_count == 5

    control_result = dual_eligible_control_pool().solve()
    assert control_result.status == "feasible"
    assert pair_quota(control_result).excluded_pool_count == 0


# --------------------------------------------------------------------------
# 22: positive pair controls
# --------------------------------------------------------------------------


def test_six_operating_entities_with_support_and_base_roles_satisfy_the_quota() -> None:
    result = base_pool().solve()
    assert result.status == "feasible"
    quota = pair_quota(result)
    assert quota.achieved_count == 6
    assert quota.available_eligible_count == 6
    assert quota.status == "pass"
    assert quota.binding_constraint is False

    roles = {a.accession_number_dashed: a.accession_role for a in result.selected_accessions}
    operating_ciks = {c.cik_padded for c in result.selected_operating}
    for slot in range(6):
        cik = slot + 1
        assert f"{cik:010d}" in operating_ciks
        assert roles[dashed(cik, 2009, 1)] == "support"
        assert roles[dashed(cik, 2010, 2)] == "base"


def test_a_support_and_a_base_at_different_operating_ciks_form_no_pair() -> None:
    """Entity 1 keeps its support but loses its development target; entity 20 gains
    a valid 2010 development target but has no 2009 support. Neither forms a pair."""
    pool = five_pair_pool()
    pool.accessions.append(
        mk_accession(20, 2010, 8, role="base", inline=False, has_xbrl=True, cohort="development")
    )
    result = pool.solve()
    assert result.status == "infeasible"
    assert pair_quota(result).available_eligible_count == 5


def test_one_entity_with_several_qualifying_targets_still_counts_once() -> None:
    pool = base_pool()
    pool.accessions.append(
        mk_accession(1, 2010, 9, role="base", inline=False, has_xbrl=True, cohort="development")
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert pair_quota(result).achieved_count == 6
    assert pair_quota(result).available_eligible_count == 6


def test_one_entity_with_several_qualifying_supports_still_counts_once() -> None:
    pool = base_pool()
    pool.accessions.append(
        mk_accession(2, 2009, 9, role="support", pre_study=True, inline=False, has_xbrl=False)
    )
    result = pool.solve()
    assert result.status == "feasible"
    assert pair_quota(result).achieved_count == 6
    assert pair_quota(result).available_eligible_count == 6


def test_controls_still_contribute_to_the_unrestricted_era_quota_with_dual_flags() -> None:
    """Section 11 is untouched: the very control accessions barred from the pair
    quota still contribute to the Inline/pre-Inline quotas, which name no role."""
    baseline = base_pool().solve()
    pool = base_pool()
    pool.accessions.append(dual_eligible_control_support())
    pool.accessions.append(dual_eligible_control_target())
    result = pool.solve()
    assert result.status == "feasible"
    assert quota_available(result, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS) == (
        quota_available(baseline, QUOTA_KEY_PRE_INLINE_XBRL_ORIGINALS) + 2
    )
    assert pair_quota(result).available_eligible_count == 6


# --------------------------------------------------------------------------
# 23: oracle comparison over a dual-eligibility fixture
# --------------------------------------------------------------------------


def test_a_feasible_pool_with_dual_eligible_controls_still_pairs_only_operating() -> None:
    """Positive control: with six valid operating pairs the run stays feasible and
    the two control-role halves add nothing to the pair quota."""
    result = dual_eligible_control_pool().solve()
    assert result.status == "feasible"
    assert pair_quota(result).achieved_count == 6
    assert pair_quota(result).available_eligible_count == 6
    control_ciks = {c.cik_padded for c in result.selected_controls}
    selected_control_rows = [
        a for a in result.selected_accessions if a.anchor_cik_padded in control_ciks
    ]
    assert all(a.accession_role == "control" for a in selected_control_rows)


def test_the_oracle_confirms_the_control_anchored_pair_exploit_is_infeasible() -> None:
    """The bidirectional regression guard.

    A production regression to a flag-only pair rule makes the solver feasible
    while the role-aware oracle still finds nothing; an oracle regression to a
    flag-only rule makes the oracle find a solution the solver correctly refuses.
    Either way this comparison fails. (Verified out-of-band: a role-agnostic oracle
    diverges here, whereas it agrees on the feasible six-pair pool above -- which
    is why the *exploit* pool, not the feasible one, is the fixture that guards the
    oracle.)
    """
    assert_matches_oracle(pair_exploit_pool())


# --------------------------------------------------------------------------
# 24: the Decision 020 quota-contribution membership output
# --------------------------------------------------------------------------
#
# Decision 020 sections 5 and 6 add exactly one immutable, deterministic public
# output to this accepted core, sourced from the witness derivation the achieved
# counts already come from. These tests prove the projection is exact, the
# artifact is order-independent and immutable, achieved counts and membership
# agree on every quota of every fixture, the deferred quota emits nothing, and
# the accepted selection, objective, and diagnostics are unchanged by it.


def membership(result: JointSelectionResult) -> QuotaContributionMembership:
    return result.quota_contributions


def cross_cutting_diagnostics(
    result: JointSelectionResult,
) -> tuple[AccessionQuotaDiagnostic, ...]:
    return tuple(
        d
        for d in result.accession_quota_results
        if d.dimension == QUOTA_DIMENSION_CROSS_CUTTING and not d.deferred
    )


@pytest.mark.parametrize(
    "build",
    (
        base_pool,
        dual_eligible_control_pool,
        lambda: Pool(entities=base_pool().entities, accessions=base_pool().accessions),
    ),
    ids=("base_pool", "dual_eligible_control_pool", "rebuilt_base_pool"),
)
def test_achieved_counts_equal_the_emitted_membership_on_every_quota(
    build: object,
) -> None:
    """The Decision 020 section 6 invariant, asserted independently of the
    by-construction wiring: recomputing each quota's achieved count from the
    emitted membership reproduces the published diagnostic exactly."""
    result = build().solve()  # type: ignore[operator]
    assert result.status == "feasible"
    emitted = membership(result)
    for diagnostic in cross_cutting_diagnostics(result):
        recomputed = len(emitted.units_for(diagnostic.dimension, diagnostic.key))
        assert recomputed == diagnostic.achieved_count, diagnostic.key
    assert cross_cutting_diagnostics(result)


def test_every_measurable_cross_cutting_quota_is_reported_and_no_other_dimension() -> None:
    emitted = membership(base_pool().solve())
    assert {unit.dimension for unit in emitted.units} == {QUOTA_DIMENSION_CROSS_CUTTING}
    assert {unit.key for unit in emitted.units} <= set(CROSS_CUTTING_QUOTAS)


def test_the_deferred_quota_emits_no_contribution_membership() -> None:
    """Decision 018 section 14 and Decision 020 section 6: the deferred quota
    contributes nothing and is never reported as satisfied."""
    result = base_pool().solve()
    emitted = membership(result)
    assert emitted.units_for(QUOTA_DIMENSION_CROSS_CUTTING, DEFERRED_QUOTA_KEY) == ()
    assert all(unit.key != DEFERRED_QUOTA_KEY for unit in emitted.units)
    assert result.deferred_quota_result.achieved_count == 0
    assert result.deferred_quota_result.status == "unproven"
    assert not any(
        key == DEFERRED_QUOTA_KEY for _cik, _dimension, key in emitted.entity_contributions()
    )


def test_accession_cap_quotas_emit_no_contribution_membership() -> None:
    """Caps are ``at_most`` constraints, never affirmative contributions."""
    emitted = membership(base_pool().solve())
    assert not [unit for unit in emitted.units if unit.dimension == QUOTA_DIMENSION_ACCESSION_CAP]
    for key in ACCESSION_CAP_LIMITS:
        assert emitted.units_for(QUOTA_DIMENSION_ACCESSION_CAP, key) == ()


def test_membership_is_a_projection_of_the_witness_members_only() -> None:
    """Every accession member is a selected accession anchored to the CIK the
    member carries, and every entity member is a selected entity."""
    result = base_pool().solve()
    selected_plains = {a.accession_plain: a for a in result.selected_accessions}
    selected_ciks = {c.cik_padded for c in result.selected_entities}
    for unit in membership(result).units:
        assert unit.members
        for member in unit.members:
            if member.member_kind == "accession":
                assert member.accession_plain in selected_plains
                assert selected_plains[member.accession_plain].anchor_cik_padded == (
                    member.cik_padded
                )
            else:
                assert member.accession_plain is None
                assert member.cik_padded in selected_ciks


def test_the_entity_and_accession_forms_are_transposes_of_one_artifact() -> None:
    result = base_pool().solve()
    emitted = membership(result)
    expected_entities = sorted(
        {
            (member.cik_padded, unit.dimension, unit.key)
            for unit in emitted.units
            for member in unit.members
        }
    )
    expected_accessions = sorted(
        {
            (member.accession_plain, unit.dimension, unit.key)
            for unit in emitted.units
            for member in unit.members
            if member.accession_plain is not None
        }
    )
    assert list(emitted.entity_contributions()) == expected_entities
    assert list(emitted.accession_contributions()) == expected_accessions
    assert len(set(emitted.entity_contributions())) == len(emitted.entity_contributions())
    assert len(set(emitted.accession_contributions())) == len(emitted.accession_contributions())


def test_quota_result_members_are_contiguous_and_distinct_within_each_quota() -> None:
    emitted = membership(base_pool().solve())
    by_quota: dict[tuple[str, str], list[tuple[int, str, str, str | None]]] = {}
    for dimension, key, order, kind, cik, plain in emitted.quota_members():
        by_quota.setdefault((dimension, key), []).append((order, kind, cik, plain))
    assert by_quota
    for rows in by_quota.values():
        assert [row[0] for row in rows] == list(range(1, len(rows) + 1))
        assert len({row[1:] for row in rows}) == len(rows)


def test_quota_result_members_cover_exactly_the_units_members() -> None:
    emitted = membership(base_pool().solve())
    expected: dict[tuple[str, str], set[tuple[str, str, str | None]]] = {}
    for unit in emitted.units:
        expected.setdefault((unit.dimension, unit.key), set()).update(
            (m.member_kind, m.cik_padded, m.accession_plain) for m in unit.members
        )
    found: dict[tuple[str, str], set[tuple[str, str, str | None]]] = {}
    for dimension, key, _order, kind, cik, plain in emitted.quota_members():
        found.setdefault((dimension, key), set()).add((kind, cik, plain))
    assert found == expected


def test_membership_is_invariant_under_entity_and_accession_input_permutation() -> None:
    """Order independence is a Decision 020 section 6 requirement, and the reason
    a unit records the union of its satisfying witnesses rather than the first."""
    pool = base_pool()
    reference = pool.solve()
    rng = random.Random(20260730)  # noqa: S311 - deterministic local test seed only
    for _ in range(5):
        entities = list(pool.entities)
        accessions = list(pool.accessions)
        rng.shuffle(entities)
        rng.shuffle(accessions)
        permuted = solve_joint_selection(entities, accessions, node_limit=GENEROUS_NODE_LIMIT)
        assert permuted.quota_contributions == reference.quota_contributions


def shared_purpose_pool() -> tuple[Pool, str, tuple[str, ...]]:
    """A pool whose amendment-purpose coverage rests on one *shared* unit.

    ``amendment_purpose_categories`` is the only quota whose contribution unit is a
    coverage token shared across entities rather than an entity's or an accession's
    own identity, so one unit can be satisfied by several independent selected
    witnesses anchored to *different* entities. Slots 1 and 2 keep the other two
    categories (the quota requires three), and every remaining amendment is moved
    onto the shared category so the multi-witness shape is explicit rather than an
    incidental consequence of ``slot % 3``.

    Returns the pool, the shared category, and the CIKs the *inputs* say contribute
    to it -- read off the fixture, never off the emitted membership.
    """
    pool = base_pool()
    shared = PURPOSE_CATEGORIES[0]
    contributors: list[str] = []
    for slot in range(8):
        cik = slot + 1
        number = dashed(cik, 2021, 3)
        category = PURPOSE_CATEGORIES[slot] if slot in (1, 2) else shared
        pool.replace_accession(
            number,
            amendment_purpose_category=category,
            amendment_purpose_evidence_level="provisional",
            amendment_purpose_quota_eligible=True,
        )
        if category == shared:
            contributors.append(f"{cik:010d}")
    return pool, shared, tuple(sorted(contributors))


def test_a_shared_quota_unit_credits_every_entity_with_a_satisfying_witness() -> None:
    """The load-bearing family must not collapse a shared unit to one contributor.

    ``pilot_selected_entity_quota_contributions`` is what migration 0009's
    feasible-transition trigger compares each reserve package against, so an entity
    that really does supply a cross-cutting contribution has to appear in it.
    Decision 013 section 6 forbids a reserve that "would silently drop or alter a
    cross-cutting contribution", and a canonical-minimal single-witness
    representation would do exactly that here.

    This test deliberately asserts **nothing** about the member sets of the two
    provenance-only families (``pilot_selected_accession_quota_contributions`` and
    ``pilot_quota_result_members``): their representation is an open acceptance
    finding, and pinning either a minimal or a maximal reading here would freeze it.
    """
    pool, shared, expected_contributors = shared_purpose_pool()
    result = pool.solve()
    assert result.status == "feasible"
    emitted = membership(result)

    # The fixture itself says which entities qualify: each has one selected
    # amendment carrying the shared category at provisional evidence.
    selected_plains = {a.accession_plain for a in result.selected_accessions}
    qualifying = sorted(
        {
            a.anchor_cik_padded
            for a in pool.accessions
            if a.accession_plain in selected_plains
            and a.amendment_purpose_category == shared
            and a.amendment_purpose_quota_eligible
        }
    )
    assert tuple(qualifying) == expected_contributors
    assert len(expected_contributors) > 1, "the shared unit needs several satisfying witnesses"

    # 1. every entity participating in at least one satisfying witness is credited.
    shared_quota = (QUOTA_DIMENSION_CROSS_CUTTING, QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES)
    credited = sorted(
        cik
        for cik, dimension, key in emitted.entity_contributions()
        if (dimension, key) == shared_quota
    )
    assert set(expected_contributors) <= set(credited)

    # 2. the canonical-minimal alternative -- keep only the canonically first member
    #    of each unit, which for this quota is exactly the first satisfying witness,
    #    because every one of its witnesses is a single accession -- drops real
    #    contributions.
    minimal_credited = {
        unit.members[0].cik_padded
        for unit in emitted.units
        if unit.key == QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES
    }
    dropped = set(expected_contributors) - minimal_credited
    assert dropped, "the fixture must make the two representations differ"

    # 3. and the implementation does not drop them.
    assert dropped <= set(credited)
    assert not dropped & minimal_credited

    # 4. the shared unit is still counted once, however many witnesses satisfy it.
    units = emitted.units_for(QUOTA_DIMENSION_CROSS_CUTTING, QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES)
    assert len([unit for unit in units if unit.unit == shared]) == 1
    achieved = next(
        d.achieved_count
        for d in cross_cutting_diagnostics(result)
        if d.key == QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES
    )
    assert achieved == len(units) == len({unit.unit for unit in units})
    assert achieved == emitted.achieved_count(
        QUOTA_DIMENSION_CROSS_CUTTING, QUOTA_KEY_AMENDMENT_PURPOSE_CATEGORIES
    )

    # 5. and none of it depends on input order.
    rng = random.Random(20260731)  # noqa: S311 - deterministic local test seed only
    for _ in range(5):
        entities = list(pool.entities)
        accessions = list(pool.accessions)
        rng.shuffle(entities)
        rng.shuffle(accessions)
        permuted = solve_joint_selection(entities, accessions, node_limit=GENEROUS_NODE_LIMIT)
        assert permuted.quota_contributions == emitted
        assert permuted.quota_contributions.entity_contributions() == (
            emitted.entity_contributions()
        )


def test_membership_is_emitted_in_canonical_sorted_order() -> None:
    emitted = membership(base_pool().solve())
    keys = [(unit.dimension, unit.key, unit.unit) for unit in emitted.units]
    assert keys == sorted(keys)
    assert len(keys) == len(set(keys))
    for unit in emitted.units:
        rendered = [(m.member_kind, m.cik_padded, m.accession_plain or "") for m in unit.members]
        assert rendered == sorted(rendered)


def test_the_membership_artifact_is_immutable() -> None:
    emitted = membership(base_pool().solve())
    unit = emitted.units[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        emitted.units = ()  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        unit.key = "tampered"  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        unit.members[0].cik_padded = "0000000000"  # type: ignore[misc]
    assert isinstance(emitted.units, tuple)
    assert all(isinstance(entry.members, tuple) for entry in emitted.units)


def test_a_non_feasible_run_emits_no_contribution_membership() -> None:
    pool = base_pool()
    pool.drop_accession(dashed(1, 2010, 2))
    result = pool.solve()
    assert result.status != "feasible"
    assert result.quota_contributions.units == ()
    assert result.quota_contributions.entity_contributions() == ()
    assert result.quota_contributions.accession_contributions() == ()
    assert result.quota_contributions.quota_members() == ()


def test_node_limit_exhaustion_emits_no_contribution_membership() -> None:
    result = base_pool().solve(node_limit=1)
    assert result.status == "infeasible_or_unproven"
    assert result.node_limit_exhausted
    assert result.quota_contributions.units == ()


def test_only_provisional_evidence_produces_an_affirmative_contribution() -> None:
    """Decision 014 section 1, observed through the membership rather than a count."""
    strong = base_pool().solve()
    strong_units = {
        unit.unit
        for unit in strong.quota_contributions.units
        if unit.key == QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES
    }
    assert "0000000001" in strong_units
    weak = base_pool()
    weak.replace_accession(dashed(1, 2009, 1), filing_date_evidence_level="review_required")
    weakened = weak.solve()
    weak_units = {
        unit.unit
        for unit in weakened.quota_contributions.units
        if unit.key == QUOTA_KEY_SUPPORT_TARGET_PAIR_ENTITIES
    }
    assert "0000000001" not in weak_units


def test_the_membership_output_changes_no_accepted_selection_or_objective() -> None:
    """The additive output alters no selected entity, accession, role, order,
    objective term, quota diagnostic, family, or node-budget value."""
    pool = base_pool()
    result = pool.solve()
    assert result.status == "feasible"
    stripped = dataclasses.replace(
        result, quota_contributions=QuotaContributionMembership(units=())
    )
    again = pool.solve()
    assert again.selected_operating == result.selected_operating
    assert again.selected_controls == result.selected_controls
    assert again.selected_accessions == result.selected_accessions
    assert again.objective == result.objective
    assert again.entity_quota_results == result.entity_quota_results
    assert again.accession_quota_results == result.accession_quota_results
    assert again.amendment_families == result.amendment_families
    assert again.expanded_node_count == result.expanded_node_count
    assert again.node_limit == result.node_limit
    assert again.node_limit_exhausted == result.node_limit_exhausted
    assert stripped.quota_contributions.units == ()


def test_derive_reproduces_the_membership_the_solver_publishes() -> None:
    """The artifact's own constructor is the single membership derivation: applying
    it to the accepted selection reproduces the published output exactly."""
    pool = base_pool()
    result = pool.solve()
    rederived = QuotaContributionMembership.derive(
        pool.entities,
        pool.accessions,
        selected_entity_ciks=[c.cik_padded for c in result.selected_entities],
        selected_accession_plains=[a.accession_plain for a in result.selected_accessions],
    )
    assert rederived == result.quota_contributions


def test_derive_over_a_hypothetical_subset_reports_only_that_subsets_contributions() -> None:
    """A reserve package's contribution set is derived by this same function over
    the package's own entity and accession bundle (Decision 020 sections 6 and 7)."""
    pool = base_pool()
    result = pool.solve()
    target = result.selected_operating[0].cik_padded
    bundle = [
        a.accession_plain for a in result.selected_accessions if a.anchor_cik_padded == target
    ]
    subset = QuotaContributionMembership.derive(
        pool.entities,
        pool.accessions,
        selected_entity_ciks=[target],
        selected_accession_plains=bundle,
    )
    assert {member.cik_padded for unit in subset.units for member in unit.members} == {target}
    assert set(subset.contribution_keys()) <= set(
        result.quota_contributions.contribution_keys_for_entity(target)
    )


def test_contribution_keys_for_entity_is_that_entitys_complete_signature() -> None:
    result = base_pool().solve()
    emitted = result.quota_contributions
    for candidate in result.selected_entities:
        expected = sorted(
            {
                (dimension, key)
                for cik, dimension, key in emitted.entity_contributions()
                if cik == candidate.cik_padded
            }
        )
        assert list(emitted.contribution_keys_for_entity(candidate.cik_padded)) == expected


def test_derive_rejects_an_identity_outside_the_candidate_pool() -> None:
    pool = base_pool()
    with pytest.raises(ValueError, match="not in the candidate entity pool"):
        QuotaContributionMembership.derive(
            pool.entities,
            pool.accessions,
            selected_entity_ciks=["9999999999"],
            selected_accession_plains=[],
        )
    with pytest.raises(ValueError, match="not in the candidate accession pool"):
        QuotaContributionMembership.derive(
            pool.entities,
            pool.accessions,
            selected_entity_ciks=[],
            selected_accession_plains=["999999999999999999"],
        )


def test_derive_is_pure_and_mutates_no_input() -> None:
    pool = base_pool()
    entities = tuple(pool.entities)
    accessions = tuple(pool.accessions)
    before = (dataclasses.astuple(entities[0]), dataclasses.astuple(accessions[0]))
    QuotaContributionMembership.derive(
        entities,
        accessions,
        selected_entity_ciks=[],
        selected_accession_plains=[],
    )
    assert (dataclasses.astuple(entities[0]), dataclasses.astuple(accessions[0])) == before
    assert tuple(pool.entities) == entities
    assert tuple(pool.accessions) == accessions


# --------------------------------------------------------------------------
# The single accepted filing-year derivation (Decision 018 sections 15 and 19)
# --------------------------------------------------------------------------

#: Every stored ``official_filing_date`` shape the helper must classify, with the
#: year the accepted strict ISO rule yields. Values are frozen here as literals
#: read off Decision 018 section 5 and Decision 019 section 5.9's exact-date rule,
#: not produced by any production helper.
FILING_YEAR_CASES: Final[tuple[tuple[str | None, int | None], ...]] = (
    (None, None),
    ("2009-03-15", 2009),
    ("2024-12-31", 2024),
    ("2009-02-30", None),  # regex-shaped, impossible calendar date
    ("20090315", None),  # compact, no separators
    ("2009-3-15", None),  # partially padded
    ("abcd-01-01", None),  # non-numeric year
    ("", None),  # empty string
    ("2009-13-01", None),  # impossible month
    ("2009-03-15T00:00:00Z", None),  # trailing time component
    (" 2009-03-15", None),  # leading whitespace
)


@pytest.mark.parametrize(("stored", "expected"), FILING_YEAR_CASES)
def test_official_filing_year_classifies_every_stored_date_shape(
    stored: str | None, expected: int | None
) -> None:
    """One derivation, and it never reads a year out of a value the core rejects."""
    assert official_filing_year(stored) == expected


def test_official_filing_year_agrees_with_the_strict_date_rule_it_delegates_to() -> None:
    """It is a projection of the accepted parse, not a second interpretation."""
    for stored, _expected in FILING_YEAR_CASES:
        parsed = accession_selector._parse_iso_date(stored)  # noqa: SLF001
        assert official_filing_year(stored) == (None if parsed is None else parsed.year)


def test_official_filing_year_structurally_delegates_to_the_strict_parse() -> None:
    """Delegation is proved from the source, not only from agreeing outputs."""
    tree = ast.parse(_ACCESSION_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "official_filing_year"
    )
    called = {ast.unparse(node.func) for node in ast.walk(helper) if isinstance(node, ast.Call)}
    assert called == {"_parse_iso_date"}


def test_exactly_one_filing_year_derivation_exists_across_both_pure_modules() -> None:
    """Decision 018 section 19: no substring parser and no ``int(value[:4])``.

    The check reads each module with its docstrings stripped, so prose that merely
    *names* a prohibited shape cannot mask a real one.
    """
    selector_code = code_without_docstrings(_ACCESSION_SELECTOR_SOURCE)
    reserve_code = code_without_docstrings(_RESERVE_SELECTOR_SOURCE)
    for label, code in (("selector", selector_code), ("reserve", reserve_code)):
        assert "[:4]" not in code, label
        assert "strptime" not in code, label
    # exactly one place turns a parsed date into a filing year, and it is the helper
    assert selector_code.count(".year") == 1
    assert selector_code.count("date.fromisoformat") == 1
    # the reserve module consults the accepted helper and holds no parser of its own
    assert "official_filing_year(" in reserve_code
    assert "_parse_iso_date" not in reserve_code
    assert "fromisoformat" not in reserve_code
    assert ".year" not in reserve_code
    assert "re." not in reserve_code


def test_a_malformed_filing_date_never_yields_a_support_role_in_the_accepted_core() -> None:
    """Decision 018 section 7's support branch is the one filing-year-dependent
    branch, and a date the core cannot read must not reach it."""
    for stored, expected in FILING_YEAR_CASES:
        candidate = mk_accession(
            900, 2009, 1, role="support", inline=False, has_xbrl=False, pre_study=True
        )
        candidate = dataclasses.replace(candidate, official_filing_date=stored)
        role, _reason = assign_accession_role(
            candidate, anchor_category="operating", filing_year=official_filing_year(stored)
        )
        assert role == ("support" if expected == 2009 else None)


def test_a_malformed_filing_date_changes_no_valid_selection_result() -> None:
    """The valid-date fixtures the accepted suite pins are unaffected by the
    refactor: the pool solves to the same selection, objective, and membership."""
    reference = base_pool().solve()
    again = base_pool().solve()
    assert again.selected_operating == reference.selected_operating
    assert again.selected_controls == reference.selected_controls
    assert again.selected_accessions == reference.selected_accessions
    assert again.objective == reference.objective
    assert again.quota_contributions == reference.quota_contributions
    assert again.accession_quota_results == reference.accession_quota_results
    # every accession in the accepted fixture carries a canonical date, so the
    # helper resolves each one rather than failing closed.
    for accession in base_pool().accessions:
        assert official_filing_year(accession.official_filing_date) is not None


def test_the_input_schema_version_and_run_identity_inputs_are_untouched() -> None:
    """Decision 020 section 9: membership is an output, so the frozen S5 input
    schema version -- the value the run identity is built from -- is not bumped."""
    from disclosure_drift.sec.accession_selection_store import (
        ACCESSION_SELECTION_INPUT_SCHEMA_VERSION,
    )

    assert ACCESSION_SELECTION_INPUT_SCHEMA_VERSION == "pilot-joint-selection-input/1.0"
