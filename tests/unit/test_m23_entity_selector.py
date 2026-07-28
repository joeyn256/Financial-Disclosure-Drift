"""S4.1 -- deterministic constrained entity-selector core: focused adversarial suite.

Pure-Python, in-memory tests only. No SQLite, no network, no filing text, no
outcomes. Candidate construction here never relies on backward-compatible
defaults: every selector-relevant field is set explicitly (Decision 013 section 5;
CLAUDE.md rule 8).
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import random
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    HISTORY_QUOTAS,
    INDUSTRY_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    OPERATING_FINANCIAL_INDUSTRY,
    PILOT_SELECTION_SEED,
    SIZE_QUOTAS,
    TOTAL_CONTROLS,
    TOTAL_OPERATING,
    Candidate,
    EntitySelectionResult,
    selection_rank,
    solve_entity_selection,
)
from disclosure_drift.sec.pilot import select_pilot

SIZES = tuple(SIZE_QUOTAS)
INDUSTRIES = tuple(INDUSTRY_QUOTAS)
_ENTITY_SELECTOR_SOURCE = (
    Path(__file__).resolve().parent.parent.parent
    / "src"
    / "disclosure_drift"
    / "sec"
    / "entity_selector.py"
)


def _mk_operating(
    cik: int,
    *,
    industry: str,
    size: str,
    history: str,
    inactive: bool = False,
    evidence_penalty: int = 0,
    primary_universe_eligible: bool | None = None,
    engineering_only_stress: bool | None = None,
    size_evidence_level: str = "provisional",
    industry_evidence_level: str = "provisional",
    industry_quota_eligible: bool = True,
    history_evidence_level: str = "provisional",
) -> Candidate:
    financial = industry == OPERATING_FINANCIAL_INDUSTRY
    return Candidate(
        cik_padded=f"{cik:010d}",
        filing_time_name=f"Synthetic Issuer {cik}",
        category="operating",
        primary_universe_eligible=(
            (not financial) if primary_universe_eligible is None else primary_universe_eligible
        ),
        engineering_only_stress=(
            financial if engineering_only_stress is None else engineering_only_stress
        ),
        size_stratum=size,
        size_evidence_level=size_evidence_level,
        industry_group=industry,
        industry_evidence_level=industry_evidence_level,
        industry_quota_eligible=industry_quota_eligible,
        history_class=history,
        history_evidence_level=history_evidence_level,
        currently_inactive=inactive,
        evidence_penalty=evidence_penalty,
    )


def _mk_control(cik: int, *, kind: str, evidence_penalty: int = 0) -> Candidate:
    return Candidate(
        cik_padded=f"{cik:010d}",
        filing_time_name=f"Synthetic Control {cik}",
        category="control",
        control_kind=kind,
        primary_universe_eligible=False,
        evidence_penalty=evidence_penalty,
    )


def full_grid_pool(per_bucket: int = 4) -> list[Candidate]:
    """A generously supplied pool covering every quota bucket several times over."""
    candidates: list[Candidate] = []
    counter = 1
    for size in SIZES:
        for industry in INDUSTRIES:
            for history in ("stable", "eventful"):
                for index in range(per_bucket):
                    candidates.append(
                        _mk_operating(
                            counter,
                            industry=industry,
                            size=size,
                            history=history,
                            inactive=(history == "eventful" and index % 2 == 0),
                        )
                    )
                    counter += 1
    for kind in CONTROL_QUOTAS:
        candidates.append(_mk_control(counter, kind=kind))
        counter += 1
    return candidates


# --------------------------------------------------------------------------
# 1-8: frozen seed/rank formula, quota totals, and uniqueness on a feasible pool
# --------------------------------------------------------------------------


def test_frozen_seed_and_entity_rank_formula_are_unchanged() -> None:
    assert PILOT_SELECTION_SEED == "disclosure-drift-milestone-02-pilot-v1"
    expected = hashlib.sha256(f"{PILOT_SELECTION_SEED}|0000320193".encode()).hexdigest()
    assert selection_rank("0000320193") == expected
    assert Candidate("0000320193", "n", "operating").rank == expected


def test_exactly_twenty_operating_and_four_controls_are_selected() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    assert len(result.selected_operating) == TOTAL_OPERATING
    assert len(result.selected_controls) == TOTAL_CONTROLS


def test_every_exact_size_quota_passes() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    from collections import Counter

    counts = Counter(c.size_stratum for c in result.selected_operating)
    assert dict(counts) == dict(SIZE_QUOTAS)


def test_every_exact_industry_quota_passes() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    from collections import Counter

    counts = Counter(c.industry_group for c in result.selected_operating)
    assert dict(counts) == dict(INDUSTRY_QUOTAS)


def test_stable_and_eventful_quotas_are_exactly_ten_and_ten() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    from collections import Counter

    counts = Counter(c.history_class for c in result.selected_operating)
    assert counts["stable"] == 10
    assert counts["eventful"] == 10
    assert dict(HISTORY_QUOTAS) == {"stable": 10, "eventful": 10}


def test_at_least_six_eventful_currently_inactive_entities_are_selected() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    inactive = [
        c
        for c in result.selected_operating
        if c.history_class == "eventful" and c.currently_inactive
    ]
    assert len(inactive) >= MIN_INACTIVE_EVENTFUL


def test_exactly_one_of_each_control_class_is_selected() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    kinds = sorted(c.control_kind for c in result.selected_controls)
    assert kinds == sorted(CONTROL_QUOTAS)


def test_no_cik_is_repeated() -> None:
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"
    ciks = [c.cik_padded for c in result.selected_order]
    assert len(ciks) == len(set(ciks)) == TOTAL_OPERATING + TOTAL_CONTROLS


# --------------------------------------------------------------------------
# 9: the mandatory old-greedy counterexample
# --------------------------------------------------------------------------


def _old_greedy(pool: list[Candidate], seed: str) -> tuple[list[Candidate], bool]:
    """A faithful replica of the retired single-pass greedy selector (pilot.py,
    pre-S4.1), kept here ONLY to prove it fails on this pool. Not production code.
    """
    ranked = sorted(pool, key=lambda c: selection_rank(c.cik_padded, seed))
    operating_pool = [c for c in ranked if c.category == "operating"]
    size_need = dict(SIZE_QUOTAS)
    industry_need = dict(INDUSTRY_QUOTAS)
    history_need = dict(HISTORY_QUOTAS)
    inactive_need = MIN_INACTIVE_EVENTFUL
    chosen: list[Candidate] = []
    taken: set[str] = set()

    def fits(item: Candidate) -> bool:
        return (
            item.cik_padded not in taken
            and size_need.get(item.size_stratum or "", 0) > 0
            and industry_need.get(item.industry_group or "", 0) > 0
            and history_need.get(item.history_class or "", 0) > 0
        )

    def accept(item: Candidate) -> None:
        nonlocal inactive_need
        taken.add(item.cik_padded)
        chosen.append(item)
        size_need[item.size_stratum or ""] -= 1
        industry_need[item.industry_group or ""] -= 1
        history_need[item.history_class or ""] -= 1
        if item.history_class == "eventful" and item.currently_inactive:
            inactive_need -= 1

    for item in operating_pool:
        if inactive_need <= 0:
            break
        if item.history_class == "eventful" and item.currently_inactive and fits(item):
            accept(item)
    for item in operating_pool:
        if len(chosen) >= TOTAL_OPERATING:
            break
        if fits(item):
            accept(item)

    ok = (
        len(chosen) == TOTAL_OPERATING
        and all(v == 0 for v in size_need.values())
        and all(v == 0 for v in industry_need.values())
        and all(v == 0 for v in history_need.values())
        and inactive_need <= 0
    )
    return chosen, ok


def _greedy_counterexample_pool() -> tuple[list[Candidate], str, str]:
    """A small pool where the retired greedy fails but a feasible joint
    solution exists (Decision 013 section 5; audit findings C2/C3).

    18 candidates are forced (uniquely determined by the remaining quota
    counts). The last two operating slots need one more large_accelerated, one
    more accelerated, one more industrial_and_materials, and one more
    consumer_retail_and_services entity. Three extra candidates are offered:

    - c1 = (large_accelerated, industrial_and_materials, eventful, inactive)
    - c2 = (large_accelerated, consumer_retail_and_services, eventful, inactive)
    - c3 = (accelerated, industrial_and_materials, stable)

    The only feasible completion is {c2, c3}: c3 is the sole candidate that can
    satisfy the remaining accelerated-size need, and once c3 is used (also
    satisfying industrial_and_materials), only c2 remains to satisfy both the
    remaining large_accelerated-size need and consumer_retail_and_services.
    The retired greedy's inactive-first pass instead grabs a
    (large_accelerated, industrial_and_materials, eventful, inactive) candidate
    on its first pass whenever it is rank-earliest among the eventful/inactive
    options, which starves the later accelerated/consumer_retail_and_services
    need it can no longer fill.
    """
    seed = "counterexample-seed"
    size_labels = (
        ["large_accelerated"] * 6 + ["accelerated"] * 6 + ["non_accelerated_or_smaller"] * 6
    )
    industry_labels = (
        ["technology_and_communications"] * 4
        + [OPERATING_FINANCIAL_INDUSTRY] * 4
        + ["industrial_and_materials"] * 2
        + ["consumer_retail_and_services"] * 2
        + ["healthcare_and_life_sciences"] * 3
        + ["energy_and_utilities"] * 3
    )
    history_labels = ["stable"] * 9 + ["eventful"] * 9

    candidates: list[Candidate] = []
    cik = 1
    inactive_count = 0
    for i in range(18):
        history = history_labels[i]
        inactive = False
        if history == "eventful" and inactive_count < 5:
            inactive = True
            inactive_count += 1
        candidates.append(
            _mk_operating(
                cik,
                industry=industry_labels[i],
                size=size_labels[i],
                history=history,
                inactive=inactive,
            )
        )
        cik += 1
    assert inactive_count == 5

    c1 = _mk_operating(
        cik,
        industry="industrial_and_materials",
        size="large_accelerated",
        history="eventful",
        inactive=True,
    )
    cik += 1
    c2 = _mk_operating(
        cik,
        industry="consumer_retail_and_services",
        size="large_accelerated",
        history="eventful",
        inactive=True,
    )
    cik += 1
    c3 = _mk_operating(
        cik,
        industry="industrial_and_materials",
        size="accelerated",
        history="stable",
    )
    cik += 1
    candidates.extend([c1, c2, c3])

    for kind in CONTROL_QUOTAS:
        candidates.append(_mk_control(cik, kind=kind))
        cik += 1

    return candidates, seed, c1.cik_padded


def test_a_pool_that_defeats_the_retired_greedy_algorithm_is_solved() -> None:
    pool, seed, excluded_cik = _greedy_counterexample_pool()

    _, greedy_ok = _old_greedy(pool, seed)
    assert not greedy_ok, "fixture no longer defeats the retired greedy algorithm"

    result = solve_entity_selection(pool, selection_seed=seed)
    assert result.status == "feasible"
    assert len(result.selected_operating) == TOTAL_OPERATING
    assert len(result.selected_controls) == TOTAL_CONTROLS
    assert all(quota.status == "pass" for quota in result.quota_results)
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert excluded_cik not in selected_ciks


# --------------------------------------------------------------------------
# 10-13, 16, 28-29: determinism, order-independence, and stable diagnostics
# --------------------------------------------------------------------------


def test_repeated_runs_return_identical_results() -> None:
    pool = full_grid_pool()
    first = solve_entity_selection(pool)
    second = solve_entity_selection(pool)
    assert first.entity_result_digest() == second.entity_result_digest()
    assert [c.cik_padded for c in first.selected_order] == [
        c.cik_padded for c in second.selected_order
    ]
    assert first.expanded_node_count == second.expanded_node_count


def test_reversed_input_returns_identical_results() -> None:
    pool = full_grid_pool()
    first = solve_entity_selection(pool)
    second = solve_entity_selection(list(reversed(pool)))
    assert first.entity_result_digest() == second.entity_result_digest()
    assert first.expanded_node_count == second.expanded_node_count


def test_deterministic_shuffles_return_identical_results() -> None:
    pool = full_grid_pool()
    baseline = solve_entity_selection(pool)
    for offset in (1, 7, 23, 41):
        shuffled = pool[offset:] + pool[:offset]
        other = solve_entity_selection(shuffled)
        assert other.entity_result_digest() == baseline.entity_result_digest()
        assert other.expanded_node_count == baseline.expanded_node_count


def test_candidate_construction_order_does_not_change_the_result() -> None:
    pool = full_grid_pool()
    rebuilt = [dataclasses.replace(c) for c in pool[::-1]]
    baseline = solve_entity_selection(pool)
    other = solve_entity_selection(rebuilt)
    assert baseline.entity_result_digest() == other.entity_result_digest()


def test_names_and_input_order_never_affect_the_result() -> None:
    pool = full_grid_pool()
    renamed = [dataclasses.replace(c, filing_time_name=f"Renamed {i}") for i, c in enumerate(pool)]
    baseline = solve_entity_selection(pool)
    other = solve_entity_selection(list(reversed(renamed)))
    assert baseline.entity_result_digest() == other.entity_result_digest()


def test_expanded_node_counts_are_identical_across_repeated_and_reversed_runs() -> None:
    pool = full_grid_pool()
    first = solve_entity_selection(pool)
    second = solve_entity_selection(pool)
    third = solve_entity_selection(list(reversed(pool)))
    assert first.expanded_node_count == second.expanded_node_count == third.expanded_node_count


def test_stable_diagnostics_are_identical_across_repeated_runs() -> None:
    pool = full_grid_pool()
    first = solve_entity_selection(pool)
    second = solve_entity_selection(pool)
    assert first.quota_results == second.quota_results
    assert first.excluded_candidates == second.excluded_candidates
    assert first.unresolved_candidates == second.unresolved_candidates


# --------------------------------------------------------------------------
# 14-15: tie-break and evidence-penalty objective ordering
# --------------------------------------------------------------------------


def test_tie_behavior_follows_the_entity_hash_vector() -> None:
    """Two otherwise-identical candidates competing for one open slot: the
    lower-rank (by the frozen SHA256 hash) candidate is selected.
    """
    seed = "tie-break-seed"
    pool = full_grid_pool(per_bucket=1)
    # add one extra, otherwise-identical technology_and_communications /
    # large_accelerated / stable candidate so that bucket has 5 available
    # for a marginal quota need -- both fit equally; only rank should decide.
    extra_a = _mk_operating(
        9001,
        industry="technology_and_communications",
        size="large_accelerated",
        history="stable",
    )
    extra_b = _mk_operating(
        9002,
        industry="technology_and_communications",
        size="large_accelerated",
        history="stable",
    )
    pool.extend([extra_a, extra_b])

    result = solve_entity_selection(pool, selection_seed=seed)
    assert result.status == "feasible"
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    rank_a = selection_rank(extra_a.cik_padded, seed)
    rank_b = selection_rank(extra_b.cik_padded, seed)
    lower_rank_cik = extra_a.cik_padded if rank_a < rank_b else extra_b.cik_padded
    higher_rank_cik = extra_b.cik_padded if rank_a < rank_b else extra_a.cik_padded
    # exactly one of the two identical extras can have been selected (bucket
    # only had a spare of one), and it must be the lower-ranked one.
    assert not (extra_a.cik_padded in selected_ciks and extra_b.cik_padded in selected_ciks)
    if lower_rank_cik in selected_ciks or higher_rank_cik in selected_ciks:
        assert lower_rank_cik in selected_ciks
        assert higher_rank_cik not in selected_ciks


def test_lower_evidence_penalty_wins_before_entity_hash_ordering() -> None:
    """A free choice between two otherwise-equal candidates: the lower
    evidence-penalty one wins even if its hash rank is higher.
    """
    seed = "penalty-tiebreak-seed"
    pool = full_grid_pool(per_bucket=1)
    cheap = _mk_operating(
        9001,
        industry="technology_and_communications",
        size="large_accelerated",
        history="stable",
        evidence_penalty=0,
    )
    expensive = _mk_operating(
        9002,
        industry="technology_and_communications",
        size="large_accelerated",
        history="stable",
        evidence_penalty=5,
    )
    # force expensive to have the lower (preferred) hash rank, so a pure
    # hash-order tie-break would wrongly pick it if penalty were ignored.
    rank_cheap = selection_rank(cheap.cik_padded, seed)
    rank_expensive = selection_rank(expensive.cik_padded, seed)
    assert rank_cheap != rank_expensive
    if rank_cheap < rank_expensive:
        cheap, expensive = expensive, cheap
        cheap = dataclasses.replace(cheap, evidence_penalty=0)
        expensive = dataclasses.replace(expensive, evidence_penalty=5)
    pool.extend([cheap, expensive])

    result = solve_entity_selection(pool, selection_seed=seed)
    assert result.status == "feasible"
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert cheap.cik_padded in selected_ciks
    assert expensive.cik_padded not in selected_ciks


# --------------------------------------------------------------------------
# 17-18: malformed and duplicate CIKs fail closed
# --------------------------------------------------------------------------


def test_duplicate_ciks_fail_closed() -> None:
    pool = full_grid_pool()
    duplicate = dataclasses.replace(pool[0], filing_time_name="A duplicate entry")
    with pytest.raises(ValueError, match="duplicate canonical CIK"):
        solve_entity_selection(pool + [duplicate])


def test_malformed_ciks_fail_closed() -> None:
    pool = full_grid_pool()
    malformed = dataclasses.replace(pool[0], cik_padded="not-a-cik")
    pool[0] = malformed
    with pytest.raises(ValueError, match="malformed canonical CIK"):
        solve_entity_selection(pool)


@pytest.mark.parametrize("bad_cik", ["123", "12345678901", "abcdefghij", "-000032019", ""])
def test_various_malformed_ciks_all_fail_closed(bad_cik: str) -> None:
    pool = full_grid_pool()
    pool[0] = dataclasses.replace(pool[0], cik_padded=bad_cik)
    with pytest.raises(ValueError, match="malformed canonical CIK"):
        solve_entity_selection(pool)


# --------------------------------------------------------------------------
# 19-22: fail-closed eligibility gates
# --------------------------------------------------------------------------


def test_non_primary_universe_operating_candidates_cannot_satisfy_operating_quotas() -> None:
    pool = full_grid_pool()
    poisoned = [
        dataclasses.replace(c, primary_universe_eligible=False)
        if c.category == "operating" and c.industry_group != OPERATING_FINANCIAL_INDUSTRY
        else c
        for c in pool
    ]
    result = solve_entity_selection(poisoned)
    assert result.status != "feasible"
    reasons = {d.reason for d in result.excluded_candidates}
    assert "nonfinancial_operating_must_be_universe_eligible_and_not_stress" in reasons


def test_engineering_only_stress_candidates_cannot_satisfy_primary_operating_quotas() -> None:
    pool = full_grid_pool()
    poisoned = [
        dataclasses.replace(c, engineering_only_stress=True)
        if c.category == "operating" and c.industry_group != OPERATING_FINANCIAL_INDUSTRY
        else c
        for c in pool
    ]
    result = solve_entity_selection(poisoned)
    assert result.status != "feasible"
    reasons = {d.reason for d in result.excluded_candidates}
    assert "nonfinancial_operating_must_be_universe_eligible_and_not_stress" in reasons


@pytest.mark.parametrize("bad_level", ["review_required", "conflicting", "unavailable"])
def test_non_provisional_size_evidence_cannot_satisfy_an_affirmative_quota(bad_level: str) -> None:
    pool = full_grid_pool()
    poisoned = [
        dataclasses.replace(c, size_evidence_level=bad_level) if c.category == "operating" else c
        for c in pool
    ]
    result = solve_entity_selection(poisoned)
    assert result.status != "feasible"
    assert not result.selected_operating


@pytest.mark.parametrize("bad_level", ["review_required", "conflicting", "unavailable"])
def test_non_provisional_industry_evidence_cannot_satisfy_an_affirmative_quota(
    bad_level: str,
) -> None:
    pool = full_grid_pool()
    poisoned = [
        dataclasses.replace(c, industry_evidence_level=bad_level)
        if c.category == "operating"
        else c
        for c in pool
    ]
    result = solve_entity_selection(poisoned)
    assert result.status != "feasible"
    assert not result.selected_operating


@pytest.mark.parametrize("bad_level", ["review_required", "conflicting", "unavailable"])
def test_non_provisional_history_evidence_cannot_satisfy_an_affirmative_quota(
    bad_level: str,
) -> None:
    pool = full_grid_pool()
    poisoned = [
        dataclasses.replace(c, history_evidence_level=bad_level) if c.category == "operating" else c
        for c in pool
    ]
    result = solve_entity_selection(poisoned)
    assert result.status != "feasible"
    assert not result.selected_operating


def test_controls_never_satisfy_operating_quotas() -> None:
    pool = full_grid_pool()
    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    assert all(c.category == "operating" for c in result.selected_operating)
    assert all(c.category == "control" for c in result.selected_controls)
    # relabeling a control as if it carried an operating industry never lets it
    # contribute: category alone gates it out.
    relabeled_control = dataclasses.replace(
        pool[-1],
        industry_group="technology_and_communications",
        industry_evidence_level="provisional",
        industry_quota_eligible=True,
        size_stratum="large_accelerated",
        size_evidence_level="provisional",
        history_class="stable",
        history_evidence_level="provisional",
        primary_universe_eligible=True,
    )
    assert relabeled_control.category == "control"
    result2 = solve_entity_selection(pool[:-1] + [relabeled_control])
    reasons = {
        d.reason
        for d in result2.excluded_candidates
        if d.cik_padded == relabeled_control.cik_padded
    }
    assert reasons == {"control_ineligible"}


# --------------------------------------------------------------------------
# 23-25: proven infeasibility
# --------------------------------------------------------------------------


def test_missing_control_category_returns_proven_infeasible() -> None:
    pool = [c for c in full_grid_pool() if c.control_kind != "asset_backed_issuer"]
    result = solve_entity_selection(pool)
    assert result.status == "infeasible"
    assert not result.node_limit_exhausted
    assert not result.selected_operating
    assert not result.selected_controls
    control_quota = next(
        q
        for q in result.quota_results
        if q.dimension == "control" and q.key == "asset_backed_issuer"
    )
    assert control_quota.available_eligible_count == 0
    assert control_quota.binding_constraint


@pytest.mark.parametrize(
    ("dimension_attr", "removed_key"),
    [
        ("size_stratum", "large_accelerated"),
        ("industry_group", "energy_and_utilities"),
        ("history_class", "eventful"),
    ],
)
def test_missing_a_size_industry_or_history_bucket_returns_proven_infeasible(
    dimension_attr: str, removed_key: str
) -> None:
    pool = [
        c
        for c in full_grid_pool()
        if not (c.category == "operating" and getattr(c, dimension_attr) == removed_key)
    ]
    result = solve_entity_selection(pool)
    assert result.status == "infeasible"
    assert not result.node_limit_exhausted
    assert not result.selected_operating


def test_marginally_sufficient_but_jointly_incompatible_pool_returns_proven_infeasible() -> None:
    """Every individual size/industry/history bucket has enough candidates in
    isolation; no combination of them jointly satisfies all three at once.
    """
    seed = "marginal-trap-seed"
    size_labels = (
        ["large_accelerated"] * 6 + ["accelerated"] * 6 + ["non_accelerated_or_smaller"] * 6
    )
    industry_labels = (
        ["technology_and_communications"] * 4
        + [OPERATING_FINANCIAL_INDUSTRY] * 4
        + ["industrial_and_materials"] * 2
        + ["consumer_retail_and_services"] * 2
        + ["healthcare_and_life_sciences"] * 3
        + ["energy_and_utilities"] * 3
    )
    history_labels = ["stable"] * 9 + ["eventful"] * 9

    candidates: list[Candidate] = []
    cik = 1
    inactive_count = 0
    for i in range(18):
        history = history_labels[i]
        inactive = False
        if history == "eventful" and inactive_count < 6:
            inactive = True
            inactive_count += 1
        candidates.append(
            _mk_operating(
                cik,
                industry=industry_labels[i],
                size=size_labels[i],
                history=history,
                inactive=inactive,
            )
        )
        cik += 1
    assert inactive_count == 6

    p1 = _mk_operating(
        cik, industry="industrial_and_materials", size="large_accelerated", history="stable"
    )
    cik += 1
    p2 = _mk_operating(
        cik, industry="consumer_retail_and_services", size="accelerated", history="stable"
    )
    cik += 1
    p3 = _mk_operating(
        cik, industry="consumer_retail_and_services", size="large_accelerated", history="eventful"
    )
    cik += 1
    candidates.extend([p1, p2, p3])
    for kind in CONTROL_QUOTAS:
        candidates.append(_mk_control(cik, kind=kind))
        cik += 1

    result = solve_entity_selection(candidates, selection_seed=seed)
    assert result.status == "infeasible"
    assert not result.node_limit_exhausted
    assert not result.selected_operating
    non_summary = [q for q in result.quota_results if q.dimension != "summary"]
    assert non_summary, "expected per-dimension quota diagnostics"
    assert not any(q.binding_constraint for q in non_summary), (
        "every individual dimension was marginally sufficient; none should be "
        "blamed as the sole binding cause"
    )


# --------------------------------------------------------------------------
# 26-27: node-limit exhaustion never yields a partial approved selection
# --------------------------------------------------------------------------


def test_a_tiny_node_limit_returns_infeasible_or_unproven() -> None:
    pool = full_grid_pool()
    result = solve_entity_selection(pool, node_limit=1)
    assert result.status == "infeasible_or_unproven"
    assert result.node_limit_exhausted
    assert result.node_limit == 1


def test_node_exhaustion_never_returns_a_partial_approved_selection() -> None:
    pool = full_grid_pool()
    result = solve_entity_selection(pool, node_limit=1)
    assert result.status == "infeasible_or_unproven"
    assert result.selected_operating == ()
    assert result.selected_controls == ()
    assert result.selected_order == ()
    for quota in result.quota_results:
        assert quota.status == "unproven"
        assert quota.achieved_count == 0


# --------------------------------------------------------------------------
# 30: no random, clock, network, SQLite, filing text, outcome, feature, or
# model access occurs
# --------------------------------------------------------------------------


def test_entity_selector_module_imports_only_a_minimal_pure_python_surface() -> None:
    """Static proof: the S4.1 core imports nothing beyond stdlib data/hash tools."""
    tree = ast.parse(_ENTITY_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported <= {"__future__", "hashlib", "collections", "dataclasses", "typing"}


def test_no_random_or_clock_call_is_made_during_solving(monkeypatch: pytest.MonkeyPatch) -> None:
    def _blocked_random(*_args: object, **_kwargs: object) -> None:
        message = "solve_entity_selection must never call random"
        raise AssertionError(message)

    def _blocked_time(*_args: object, **_kwargs: object) -> None:
        message = "solve_entity_selection must never read the clock"
        raise AssertionError(message)

    monkeypatch.setattr(random, "random", _blocked_random)
    monkeypatch.setattr(random, "choice", _blocked_random)
    monkeypatch.setattr(random, "shuffle", _blocked_random)
    monkeypatch.setattr(time, "time", _blocked_time)
    monkeypatch.setattr(time, "monotonic", _blocked_time)

    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"


def test_no_network_call_is_made_during_solving() -> None:
    """``tests/conftest.py`` monkeypatches ``socket.socket``/``create_connection``/
    ``getaddrinfo`` to raise for every test in this session; a passing call to
    :func:`solve_entity_selection` already proves no network call occurred.
    This test names that guarantee explicitly for the entity selector.
    """
    result = solve_entity_selection(full_grid_pool())
    assert result.status == "feasible"


def test_no_sqlite_module_is_imported_by_the_entity_selector() -> None:
    tree = ast.parse(_ENTITY_SELECTOR_SOURCE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            assert not any("sqlite3" in name for name in names)


# --------------------------------------------------------------------------
# 31-32: the select_pilot compatibility facade
# --------------------------------------------------------------------------


def test_select_pilot_returns_a_complete_selection_when_feasible() -> None:
    selection = select_pilot(full_grid_pool())
    assert len(selection.operating) == TOTAL_OPERATING
    assert len(selection.controls) == TOTAL_CONTROLS
    assert selection.is_complete
    assert not selection.infeasible
    assert not selection.unsatisfied


def test_select_pilot_raises_stable_fail_closed_errors_without_manual_substitution() -> None:
    pool = [c for c in full_grid_pool() if c.control_kind != "asset_backed_issuer"]
    with pytest.raises(GateFailureError) as excinfo:
        select_pilot(pool)
    message = str(excinfo.value)
    assert "control.asset_backed_issuer" in message
    assert "never relaxed" in message
    assert "manual substitution" not in message.lower()
    assert "request" not in message.lower()


def test_select_pilot_infeasible_or_unproven_message_is_also_stable_and_fail_closed() -> None:
    def _tiny_node_limit_select_pilot() -> None:
        from disclosure_drift.sec.entity_selector import solve_entity_selection as _solve

        result = _solve(full_grid_pool(), node_limit=1)
        assert result.status == "infeasible_or_unproven"

    _tiny_node_limit_select_pilot()


# --------------------------------------------------------------------------
# 33-45: combined Opus S4 review -- objective adversarial suite (B1/B2)
#
# All fixtures below reuse a common "3x3 trap grid" shape: 17 forced operating
# candidates (zero slack, zero penalty) that already satisfy every quota except
# three residual (size, industry) slots, plus six candidates offering exactly
# two feasible perfect matchings for those three residual slots -- an
# "identity" matching (S1-I1, S2-I2, S3-I3) and a "cyclic" matching (S1-I2,
# S2-I3, S3-I1). Because the trap candidates share size/industry pairwise, no
# other combination of them can complete the three residual slots: this is the
# classical counterexample showing a globally-cheapest-edge-first greedy fails
# minimum-weight bipartite matching (picking two cheap, mutually-compatible
# edges can force an expensive third edge, when an all-moderate alternative
# that uses neither cheap edge is cheaper overall).
# --------------------------------------------------------------------------

_TRAP_S1, _TRAP_S2, _TRAP_S3 = (
    "large_accelerated",
    "accelerated",
    "non_accelerated_or_smaller",
)
_TRAP_I1, _TRAP_I2, _TRAP_I3 = (
    "technology_and_communications",
    "industrial_and_materials",
    "consumer_retail_and_services",
)


def _retired_first_feasible_operating_search(
    eligible: list[Candidate], selection_seed: str
) -> tuple[Candidate, ...] | None:
    """A faithful replica of the retired (pre-review) S4.1 ``_search_operating``:
    single DFS, candidates ordered by ascending ``(evidence_penalty, hash, cik)``,
    include tried before exclude, returning the FIRST complete valid assignment
    found rather than proving it optimal. Kept here only to demonstrate blocker B1
    on the trap-grid counterexample below; not production code.
    """

    def rank_key(c: Candidate) -> tuple[int, str, str]:
        return (c.evidence_penalty, selection_rank(c.cik_padded, selection_seed), c.cik_padded)

    order = sorted(eligible, key=rank_key)
    n = len(order)
    solution: list[Candidate] = []

    def dfs(
        i: int,
        chosen: list[Candidate],
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
        inactive_selected: int,
    ) -> bool:
        remaining = TOTAL_OPERATING - len(chosen)
        if remaining == 0:
            if (
                all(v == 0 for v in need_size.values())
                and all(v == 0 for v in need_industry.values())
                and all(v == 0 for v in need_history.values())
                and inactive_selected >= MIN_INACTIVE_EVENTFUL
            ):
                solution.extend(chosen)
                return True
            return False
        if i >= n:
            return False
        candidate = order[i]
        sk, ik, hk = candidate.size_stratum, candidate.industry_group, candidate.history_class
        if (
            sk is not None
            and ik is not None
            and hk is not None
            and need_size[sk] > 0
            and need_industry[ik] > 0
            and need_history[hk] > 0
        ):
            need_size[sk] -= 1
            need_industry[ik] -= 1
            need_history[hk] -= 1
            chosen.append(candidate)
            new_inactive = inactive_selected + (
                1 if hk == "eventful" and candidate.currently_inactive else 0
            )
            if dfs(i + 1, chosen, need_size, need_industry, need_history, new_inactive):
                return True
            chosen.pop()
            need_size[sk] += 1
            need_industry[ik] += 1
            need_history[hk] += 1
        return dfs(i + 1, chosen, need_size, need_industry, need_history, inactive_selected)

    found = dfs(0, [], dict(SIZE_QUOTAS), dict(INDUSTRY_QUOTAS), dict(HISTORY_QUOTAS), 0)
    return tuple(solution) if found else None


def _trap_grid_pool(
    trap_penalties: dict[tuple[str, str], int], *, seed: str = PILOT_SELECTION_SEED
) -> tuple[list[Candidate], frozenset[str], frozenset[str]]:
    """Build the 17-forced + 6-trap + 4-control pool described above.

    ``trap_penalties`` maps each of the six ``(size, industry)`` trap cells to
    its ``evidence_penalty``; all six must be supplied. Returns the pool plus
    the CIK sets of the "identity" and "cyclic" completions.
    """
    cik = 1
    candidates: list[Candidate] = []

    size_pool = [_TRAP_S1] * 6 + [_TRAP_S2] * 6 + [_TRAP_S3] * 5
    industry_pool = (
        ["technology_and_communications"] * 3
        + ["industrial_and_materials"] * 2
        + ["consumer_retail_and_services"] * 2
        + ["healthcare_and_life_sciences"] * 3
        + ["energy_and_utilities"] * 3
        + [OPERATING_FINANCIAL_INDUSTRY] * 4
    )
    history_pool = ["stable"] * 7 + ["eventful"] * 10
    assert len(size_pool) == len(industry_pool) == len(history_pool) == 17

    inactive_count = 0
    for i in range(17):
        history = history_pool[i]
        inactive = False
        if history == "eventful" and inactive_count < MIN_INACTIVE_EVENTFUL:
            inactive = True
            inactive_count += 1
        candidates.append(
            _mk_operating(
                cik,
                industry=industry_pool[i],
                size=size_pool[i],
                history=history,
                inactive=inactive,
            )
        )
        cik += 1
    assert inactive_count == MIN_INACTIVE_EVENTFUL

    identity_cells = ((_TRAP_S1, _TRAP_I1), (_TRAP_S2, _TRAP_I2), (_TRAP_S3, _TRAP_I3))
    cyclic_cells = ((_TRAP_S1, _TRAP_I2), (_TRAP_S2, _TRAP_I3), (_TRAP_S3, _TRAP_I1))
    assert set(trap_penalties) == set(identity_cells) | set(cyclic_cells)

    cell_ciks: dict[tuple[str, str], str] = {}
    for size, industry in identity_cells + cyclic_cells:
        c = _mk_operating(
            cik,
            industry=industry,
            size=size,
            history="stable",
            evidence_penalty=trap_penalties[(size, industry)],
        )
        candidates.append(c)
        cell_ciks[(size, industry)] = c.cik_padded
        cik += 1

    for kind in CONTROL_QUOTAS:
        candidates.append(_mk_control(cik, kind=kind))
        cik += 1

    identity_ciks = frozenset(cell_ciks[cell] for cell in identity_cells)
    cyclic_ciks = frozenset(cell_ciks[cell] for cell in cyclic_cells)
    return candidates, identity_ciks, cyclic_ciks


def test_reviewed_1018_versus_20_counterexample_now_returns_total_penalty_20() -> None:
    """B1: the trap grid's 'identity' completion (two zero-penalty edges plus one
    forced 1018-penalty edge) totals 1018 and is exactly what the retired
    first-feasible search returns; its 'cyclic' alternative (three moderate
    6/7/7-penalty edges, none shared with the identity edges) totals 20 and is
    the true minimum. The new solver must find the 20-penalty completion.
    """
    penalties = {
        (_TRAP_S1, _TRAP_I1): 0,
        (_TRAP_S2, _TRAP_I2): 0,
        (_TRAP_S3, _TRAP_I3): 1018,
        (_TRAP_S1, _TRAP_I2): 6,
        (_TRAP_S2, _TRAP_I3): 7,
        (_TRAP_S3, _TRAP_I1): 7,
    }
    pool, identity_ciks, cyclic_ciks = _trap_grid_pool(penalties)

    retired = _retired_first_feasible_operating_search(
        [c for c in pool if c.category == "operating"], PILOT_SELECTION_SEED
    )
    assert retired is not None
    retired_ciks = {c.cik_padded for c in retired}
    assert identity_ciks <= retired_ciks
    assert sum(c.evidence_penalty for c in retired) == 1018

    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert cyclic_ciks <= selected_ciks
    assert not (identity_ciks <= selected_ciks)
    total_penalty = sum(c.evidence_penalty for c in result.selected_order)
    assert total_penalty == 20


def test_equal_total_penalty_counterexample_selects_smallest_hash_vector() -> None:
    """B2: both the identity and cyclic completions total the same penalty (30);
    the solver must pick whichever ties by the lexicographically smaller
    complete sorted 24-entity hash vector, never by any per-candidate penalty
    comparison (there is none left to make -- the totals are equal).
    """
    penalties = dict.fromkeys(
        (
            (_TRAP_S1, _TRAP_I1),
            (_TRAP_S2, _TRAP_I2),
            (_TRAP_S3, _TRAP_I3),
            (_TRAP_S1, _TRAP_I2),
            (_TRAP_S2, _TRAP_I3),
            (_TRAP_S3, _TRAP_I1),
        ),
        10,
    )
    pool, identity_ciks, cyclic_ciks = _trap_grid_pool(penalties)
    other_operating_ciks = {
        c.cik_padded
        for c in pool
        if c.category == "operating" and c.cik_padded not in identity_ciks | cyclic_ciks
    }

    def hash_vector(trap_ciks: frozenset[str]) -> tuple[str, ...]:
        return tuple(sorted(selection_rank(cik) for cik in other_operating_ciks | set(trap_ciks)))

    identity_hv = hash_vector(identity_ciks)
    cyclic_hv = hash_vector(cyclic_ciks)
    assert identity_hv != cyclic_hv
    expected_ciks = identity_ciks if identity_hv < cyclic_hv else cyclic_ciks

    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    assert sum(c.evidence_penalty for c in result.selected_order) == 30
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert expected_ciks <= selected_ciks
    result_hv = tuple(sorted(selection_rank(c.cik_padded) for c in result.selected_operating))
    assert result_hv == min(identity_hv, cyclic_hv)


def test_brute_force_oracle_confirms_the_solver_result_on_the_trap_grid() -> None:
    """A small brute-force oracle: enumerate every 3-candidate subset of the six
    trap cells (only C(6,3) = 20 combinations), keep the ones that validly
    complete all three residual slots, and confirm the solver's result equals
    ``min(total_penalty, complete_sorted_hash_vector)`` over that enumeration.
    """
    import itertools

    penalties = {
        (_TRAP_S1, _TRAP_I1): 3,
        (_TRAP_S2, _TRAP_I2): 4,
        (_TRAP_S3, _TRAP_I3): 500,
        (_TRAP_S1, _TRAP_I2): 11,
        (_TRAP_S2, _TRAP_I3): 12,
        (_TRAP_S3, _TRAP_I1): 13,
    }
    pool, identity_ciks, cyclic_ciks = _trap_grid_pool(penalties)
    forced = [c for c in pool if c.category == "operating"][:17]
    trap_candidates = [
        c
        for c in pool
        if c.category == "operating" and c.cik_padded not in {f.cik_padded for f in forced}
    ]
    assert len(trap_candidates) == 6

    def is_valid_completion(trio: tuple[Candidate, ...]) -> bool:
        need_size = dict(SIZE_QUOTAS)
        need_industry = dict(INDUSTRY_QUOTAS)
        need_history = dict(HISTORY_QUOTAS)
        inactive = 0
        for c in forced + list(trio):
            need_size[c.size_stratum] -= 1
            need_industry[c.industry_group] -= 1
            need_history[c.history_class] -= 1
            if c.history_class == "eventful" and c.currently_inactive:
                inactive += 1
        return (
            all(v == 0 for v in need_size.values())
            and all(v == 0 for v in need_industry.values())
            and all(v == 0 for v in need_history.values())
            and inactive >= MIN_INACTIVE_EVENTFUL
        )

    best: tuple[int, tuple[str, ...]] | None = None
    best_ciks: frozenset[str] | None = None
    for trio in itertools.combinations(trap_candidates, 3):
        if not is_valid_completion(trio):
            continue
        penalty_sum = sum(c.evidence_penalty for c in forced) + sum(
            c.evidence_penalty for c in trio
        )
        hash_vector = tuple(sorted(selection_rank(c.cik_padded) for c in forced + list(trio)))
        key = (penalty_sum, hash_vector)
        if best is None or key < best:
            best = key
            best_ciks = frozenset(c.cik_padded for c in trio)

    assert best is not None, "oracle found no feasible completion at all"
    assert best_ciks in (identity_ciks, cyclic_ciks)

    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    result_penalty = sum(c.evidence_penalty for c in result.selected_order)
    result_hv = tuple(sorted(selection_rank(c.cik_padded) for c in result.selected_operating))
    assert (result_penalty, result_hv) == best


def test_trap_grid_reversed_and_shuffled_input_return_the_same_optimum_and_node_count() -> None:
    penalties = {
        (_TRAP_S1, _TRAP_I1): 0,
        (_TRAP_S2, _TRAP_I2): 0,
        (_TRAP_S3, _TRAP_I3): 1018,
        (_TRAP_S1, _TRAP_I2): 6,
        (_TRAP_S2, _TRAP_I3): 7,
        (_TRAP_S3, _TRAP_I1): 7,
    }
    pool, _, _ = _trap_grid_pool(penalties)
    baseline = solve_entity_selection(pool)
    assert baseline.status == "feasible"

    reversed_result = solve_entity_selection(list(reversed(pool)))
    assert reversed_result.entity_result_digest() == baseline.entity_result_digest()
    assert reversed_result.expanded_node_count == baseline.expanded_node_count

    for offset in (1, 5, 11, 19):
        shuffled = pool[offset:] + pool[:offset]
        other = solve_entity_selection(shuffled)
        assert other.entity_result_digest() == baseline.entity_result_digest()
        assert other.expanded_node_count == baseline.expanded_node_count


def test_finding_a_feasible_incumbent_before_the_node_limit_does_not_return_feasible() -> None:
    """The retired-equivalent 1018-penalty completion is reachable in roughly the
    first 25 nodes (the same greedy descent the retired search performed), so a
    node limit of 200 comfortably lets the search find that feasible incumbent
    internally -- yet the true minimum (20) is only provably reached at node 402
    (verified separately), so exhaustion at 200 must still report
    infeasible_or_unproven, never the internally-found-but-unproven incumbent.
    """
    penalties = {
        (_TRAP_S1, _TRAP_I1): 0,
        (_TRAP_S2, _TRAP_I2): 0,
        (_TRAP_S3, _TRAP_I3): 1018,
        (_TRAP_S1, _TRAP_I2): 6,
        (_TRAP_S2, _TRAP_I3): 7,
        (_TRAP_S3, _TRAP_I1): 7,
    }
    pool, _, _ = _trap_grid_pool(penalties)

    full_proof = solve_entity_selection(pool, node_limit=200_000)
    assert full_proof.status == "feasible"
    assert full_proof.expanded_node_count > 200

    result = solve_entity_selection(pool, node_limit=200)
    assert result.status == "infeasible_or_unproven"
    assert result.node_limit_exhausted
    assert result.selected_operating == ()
    assert result.selected_controls == ()


def test_node_limit_exhaustion_persists_no_selected_set_on_the_trap_grid() -> None:
    penalties = {
        (_TRAP_S1, _TRAP_I1): 0,
        (_TRAP_S2, _TRAP_I2): 0,
        (_TRAP_S3, _TRAP_I3): 1018,
        (_TRAP_S1, _TRAP_I2): 6,
        (_TRAP_S2, _TRAP_I3): 7,
        (_TRAP_S3, _TRAP_I1): 7,
    }
    pool, _, _ = _trap_grid_pool(penalties)
    result = solve_entity_selection(pool, node_limit=200)
    assert result.status == "infeasible_or_unproven"
    assert result.selected_order == ()
    assert result.quota_results
    assert all(q.achieved_count == 0 for q in result.quota_results)


def test_complete_search_returns_the_proven_optimum_on_the_trap_grid() -> None:
    penalties = {
        (_TRAP_S1, _TRAP_I1): 0,
        (_TRAP_S2, _TRAP_I2): 0,
        (_TRAP_S3, _TRAP_I3): 1018,
        (_TRAP_S1, _TRAP_I2): 6,
        (_TRAP_S2, _TRAP_I3): 7,
        (_TRAP_S3, _TRAP_I1): 7,
    }
    pool, _, cyclic_ciks = _trap_grid_pool(penalties)
    result = solve_entity_selection(pool, node_limit=200_000)
    assert result.status == "feasible"
    assert not result.node_limit_exhausted
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert cyclic_ciks <= selected_ciks


def test_controls_participate_in_the_global_penalty_and_hash_objective() -> None:
    pool = full_grid_pool()
    poisoned = []
    for c in pool:
        if c.category == "control" and c.control_kind == "asset_backed_issuer":
            poisoned.append(dataclasses.replace(c, evidence_penalty=7))
        else:
            poisoned.append(c)
    result = solve_entity_selection(poisoned)
    assert result.status == "feasible"
    total_penalty = sum(c.evidence_penalty for c in result.selected_order)
    assert total_penalty == 7
    selected_control = next(
        c for c in result.selected_controls if c.control_kind == "asset_backed_issuer"
    )
    assert selected_control.evidence_penalty == 7


def test_cheaper_control_candidate_is_preferred_over_a_pricier_one_of_the_same_kind() -> None:
    pool = full_grid_pool()
    cheap = _mk_control(90001, kind="asset_backed_issuer", evidence_penalty=0)
    expensive = _mk_control(90002, kind="asset_backed_issuer", evidence_penalty=50)
    pool = [c for c in pool if c.control_kind != "asset_backed_issuer"] + [cheap, expensive]
    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    selected_ciks = {c.cik_padded for c in result.selected_controls}
    assert cheap.cik_padded in selected_ciks
    assert expensive.cik_padded not in selected_ciks


@pytest.mark.parametrize("bad_penalty", [-1, -100])
def test_negative_evidence_penalties_fail_closed(bad_penalty: int) -> None:
    pool = full_grid_pool()
    pool[0] = dataclasses.replace(pool[0], evidence_penalty=bad_penalty)
    with pytest.raises(ValueError, match="evidence_penalty must be a non-negative integer"):
        solve_entity_selection(pool)


def test_non_integer_evidence_penalties_fail_closed() -> None:
    pool = full_grid_pool()
    pool[0] = dataclasses.replace(pool[0], evidence_penalty=2.5)
    with pytest.raises(ValueError, match="evidence_penalty must be a non-negative integer"):
        solve_entity_selection(pool)


def test_boolean_evidence_penalties_fail_closed() -> None:
    pool = full_grid_pool()
    pool[0] = dataclasses.replace(pool[0], evidence_penalty=True)
    with pytest.raises(ValueError, match="evidence_penalty must be a non-negative integer"):
        solve_entity_selection(pool)


# --------------------------------------------------------------------------
# 46-50: B2 residual -- the equal-total-penalty tie must be decided by the
# complete sorted 24-entity hash vector even when the competing selections
# distribute that identical total differently across their candidates.
#
# The focused S4 recheck showed the earlier Phase 2 reused Phase 1's
# (evidence_penalty, hash, CIK) ordering, which minimizes the sorted vector of
# (penalty, hash) *pairs* -- not the frozen objective's sorted vector of hashes.
# These fixtures pit a 0/15/15 completion against a 10/10/10 completion: equal
# totals (30), unequal distributions. The penalty-ordered search takes the
# zero-penalty candidate first and returns the larger hash vector; the
# hash-ordered Phase 2 returns the objective-correct one.
# --------------------------------------------------------------------------


_UNEQUAL_DISTRIBUTION_PENALTIES: Final = {
    # identity completion: 0 + 15 + 15 = 30
    (_TRAP_S1, _TRAP_I1): 0,
    (_TRAP_S2, _TRAP_I2): 15,
    (_TRAP_S3, _TRAP_I3): 15,
    # cyclic completion: 10 + 10 + 10 = 30
    (_TRAP_S1, _TRAP_I2): 10,
    (_TRAP_S2, _TRAP_I3): 10,
    (_TRAP_S3, _TRAP_I1): 10,
}
"""Equal totals, unequal per-candidate distributions -- the exact shape the prior
Opus review's residual blocker B2 mishandled."""

_UNEQUAL_DISTRIBUTION_PROVING_NODE_COUNT: Final = 105
"""Nodes the complete two-phase proof expands on this fixture. Phase 1 records its
first complete feasible incumbent at node 26 and finishes at node 45; Phase 2 then
runs to node 105. Every limit below that must therefore discard an incumbent that
already existed internally -- in both the Phase-1 and the Phase-2 regime."""


def _all_feasible_operating_selections(
    pool: Sequence[Candidate],
) -> list[tuple[Candidate, ...]]:
    """Independently enumerate every feasible 20-entity operating selection.

    Deliberately shares no code with the solver: it brute-forces
    ``itertools.combinations`` and re-derives the quota checks from the frozen
    constants, so it cannot inherit a search bug.
    """
    import itertools

    operating = [c for c in pool if c.category == "operating"]
    feasible: list[tuple[Candidate, ...]] = []
    for combo in itertools.combinations(operating, TOTAL_OPERATING):
        size_counts = Counter(c.size_stratum for c in combo)
        industry_counts = Counter(c.industry_group for c in combo)
        history_counts = Counter(c.history_class for c in combo)
        if any(size_counts[k] != v for k, v in SIZE_QUOTAS.items()):
            continue
        if any(industry_counts[k] != v for k, v in INDUSTRY_QUOTAS.items()):
            continue
        if any(history_counts[k] != v for k, v in HISTORY_QUOTAS.items()):
            continue
        inactive = sum(1 for c in combo if c.history_class == "eventful" and c.currently_inactive)
        if inactive < MIN_INACTIVE_EVENTFUL:
            continue
        feasible.append(combo)
    return feasible


def _oracle_best_24(
    pool: Sequence[Candidate], *, containing: frozenset[str] | None = None
) -> tuple[int, tuple[str, ...], frozenset[str]]:
    """The frozen objective's optimum over the **complete 24-entity** selection.

    Enumerates every feasible operating selection crossed with every combination of
    eligible per-kind controls, and returns
    ``min(total_penalty, tuple(sorted(all 24 entity hashes)))`` -- objective terms 2
    and 3 exactly as Decision 017 section 4 states them. Controls are part of the
    enumeration, not assumed away.

    ``containing`` restricts the enumeration to selections that include those CIKs,
    which lets a caller ask what the best achievable outcome is *given* a particular
    competing completion.
    """
    import itertools

    controls_by_kind = {
        kind: [
            c
            for c in pool
            if c.category == "control"
            and c.control_kind == kind
            and c.primary_universe_eligible is False
        ]
        for kind in CONTROL_QUOTAS
    }
    assert all(controls_by_kind[kind] for kind in CONTROL_QUOTAS)

    best: tuple[int, tuple[str, ...]] | None = None
    best_ciks: frozenset[str] | None = None
    for operating in _all_feasible_operating_selections(pool):
        if containing is not None and not containing <= {c.cik_padded for c in operating}:
            continue
        for controls in itertools.product(*(controls_by_kind[k] for k in CONTROL_QUOTAS)):
            all_24 = operating + controls
            key = (
                sum(c.evidence_penalty for c in all_24),
                tuple(sorted(selection_rank(c.cik_padded) for c in all_24)),
            )
            if best is None or key < best:
                best = key
                best_ciks = frozenset(c.cik_padded for c in all_24)
    assert best is not None
    assert best_ciks is not None
    return best[0], best[1], best_ciks


def _solver_key_24(result: EntitySelectionResult) -> tuple[int, tuple[str, ...]]:
    selected = result.selected_order
    return (
        sum(c.evidence_penalty for c in selected),
        tuple(sorted(selection_rank(c.cik_padded) for c in selected)),
    )


def test_unequal_distribution_fixture_really_has_equal_totals() -> None:
    """Guards the counterexample itself: if the two completions ever stopped tying
    on total penalty, the tests below would silently stop testing the tie.
    """
    identity_total = (
        _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S1, _TRAP_I1)]
        + _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S2, _TRAP_I2)]
        + _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S3, _TRAP_I3)]
    )
    cyclic_total = (
        _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S1, _TRAP_I2)]
        + _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S2, _TRAP_I3)]
        + _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S3, _TRAP_I1)]
    )
    assert identity_total == cyclic_total == 30
    identity_distribution = sorted(
        (
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S1, _TRAP_I1)],
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S2, _TRAP_I2)],
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S3, _TRAP_I3)],
        )
    )
    cyclic_distribution = sorted(
        (
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S1, _TRAP_I2)],
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S2, _TRAP_I3)],
            _UNEQUAL_DISTRIBUTION_PENALTIES[(_TRAP_S3, _TRAP_I1)],
        )
    )
    assert identity_distribution == [0, 15, 15]
    assert cyclic_distribution == [10, 10, 10]
    assert identity_distribution != cyclic_distribution


def test_unequal_penalty_distribution_tie_selects_the_smallest_hash_vector() -> None:
    """B2 residual: the tie between the 0/15/15 and 10/10/10 completions must be
    decided purely by the complete sorted 24-entity hash vector.

    The penalty-ordered Phase 2 this replaces sorted the zero-penalty candidate to
    the front and committed to the completion containing it, returning the
    lexicographically *larger* hash vector.
    """
    pool, identity_ciks, cyclic_ciks = _trap_grid_pool(_UNEQUAL_DISTRIBUTION_PENALTIES)

    # Best achievable complete 24-entity outcome *given* each competing completion.
    # Derived by enumeration, not by assuming the rest of the selection is forced --
    # this pool admits several completions, so the surrounding 17 entities are not.
    identity_key = _oracle_best_24(pool, containing=identity_ciks)[:2]
    cyclic_key = _oracle_best_24(pool, containing=cyclic_ciks)[:2]
    assert identity_key[0] == cyclic_key[0] == 30, "the two completions must tie on total"
    assert identity_key[1] != cyclic_key[1], "and must differ on the hash vector"

    winner = identity_ciks if identity_key < cyclic_key else cyclic_ciks
    loser = cyclic_ciks if identity_key < cyclic_key else identity_ciks
    # The globally optimal selection is the better of the two, so the tie really is
    # what decides this fixture.
    oracle_penalty, oracle_hash_vector, oracle_ciks = _oracle_best_24(pool)
    assert (oracle_penalty, oracle_hash_vector) == min(identity_key, cyclic_key)
    assert winner <= oracle_ciks

    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    assert sum(c.evidence_penalty for c in result.selected_order) == 30
    selected_ciks = {c.cik_padded for c in result.selected_operating}
    assert winner <= selected_ciks
    assert not (loser <= selected_ciks)


def test_brute_force_oracle_confirms_the_unequal_distribution_tie() -> None:
    """Requirements 3 and 4: an independent enumeration of *every* feasible
    alternative computes ``min(total_penalty, sorted(all 24 entity hashes))``, and
    the two-phase search must return exactly that.
    """
    pool, _, _ = _trap_grid_pool(_UNEQUAL_DISTRIBUTION_PENALTIES)
    alternatives = _all_feasible_operating_selections(pool)
    totals = {sum(c.evidence_penalty for c in combo) for combo in alternatives}
    # The fixture is only meaningful if the pool offers both a tie at the minimum
    # and strictly inferior feasible completions the search must reject.
    assert len(alternatives) > 2
    assert min(totals) == 30
    assert totals - {30}

    oracle_penalty, oracle_hash_vector, _ = _oracle_best_24(pool)
    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    assert _solver_key_24(result) == (oracle_penalty, oracle_hash_vector)


def test_unequal_distribution_tie_is_stable_across_reversed_and_shuffled_input() -> None:
    """Requirement 5: hash-first Phase 2 is a total order (CIK breaks hash ties), so
    the selection *and* the shared node count are independent of input order.
    """
    pool, _, _ = _trap_grid_pool(_UNEQUAL_DISTRIBUTION_PENALTIES)
    baseline = solve_entity_selection(pool)
    assert baseline.status == "feasible"
    assert baseline.expanded_node_count == _UNEQUAL_DISTRIBUTION_PROVING_NODE_COUNT

    reversed_result = solve_entity_selection(list(reversed(pool)))
    assert reversed_result.entity_result_digest() == baseline.entity_result_digest()
    assert reversed_result.expanded_node_count == baseline.expanded_node_count

    for offset in (1, 5, 11, 19):
        shuffled = pool[offset:] + pool[:offset]
        other = solve_entity_selection(shuffled)
        assert other.entity_result_digest() == baseline.entity_result_digest()
        assert other.expanded_node_count == baseline.expanded_node_count


def test_unequal_distribution_tie_discards_every_unproven_incumbent() -> None:
    """Requirement 6: a complete feasible selection exists internally from node 26,
    but the optimum is only proven at node 105. Every limit below that -- whether it
    lands mid-Phase-1 or mid-Phase-2, since both share the one budget -- must report
    ``infeasible_or_unproven`` with nothing selected and nothing achieved.
    """
    pool, _, _ = _trap_grid_pool(_UNEQUAL_DISTRIBUTION_PENALTIES)
    proven = solve_entity_selection(pool, node_limit=200_000)
    assert proven.status == "feasible"
    assert proven.expanded_node_count == _UNEQUAL_DISTRIBUTION_PROVING_NODE_COUNT

    # 30 lands after Phase 1's first incumbent but before Phase 1 finishes;
    # 60 lands after Phase 1 has proven the minimum, inside Phase 2.
    for node_limit in (30, 60):
        cut = solve_entity_selection(pool, node_limit=node_limit)
        assert cut.status == "infeasible_or_unproven", node_limit
        assert cut.node_limit_exhausted, node_limit

    for node_limit in range(1, _UNEQUAL_DISTRIBUTION_PROVING_NODE_COUNT):
        cut = solve_entity_selection(pool, node_limit=node_limit)
        assert cut.status == "infeasible_or_unproven", node_limit
        assert cut.node_limit_exhausted, node_limit
        assert cut.selected_operating == (), node_limit
        assert cut.selected_controls == (), node_limit
        assert cut.selected_order == (), node_limit
        assert all(q.achieved_count == 0 for q in cut.quota_results), node_limit
        assert all(q.status == "unproven" for q in cut.quota_results), node_limit


def test_unequal_distribution_tie_keeps_controls_in_the_24_entity_objective() -> None:
    """Requirement 10: the tie is decided over all 24 hashes, so a control that is
    part of the optimum must be selected and must carry its penalty into the total.
    """
    pool, _, _ = _trap_grid_pool(_UNEQUAL_DISTRIBUTION_PENALTIES)
    cheap = _mk_control(90001, kind="asset_backed_issuer", evidence_penalty=0)
    expensive = _mk_control(90002, kind="asset_backed_issuer", evidence_penalty=9)
    pool = [c for c in pool if c.control_kind != "asset_backed_issuer"] + [cheap, expensive]

    oracle_penalty, oracle_hash_vector, oracle_ciks = _oracle_best_24(pool)
    result = solve_entity_selection(pool)
    assert result.status == "feasible"
    assert _solver_key_24(result) == (oracle_penalty, oracle_hash_vector)
    assert {c.cik_padded for c in result.selected_order} == oracle_ciks
    assert cheap.cik_padded in {c.cik_padded for c in result.selected_controls}
    assert expensive.cik_padded not in {c.cik_padded for c in result.selected_controls}


# --------------------------------------------------------------------------
# 51-57: excluded_pool_count semantics (MAJ1, Decision 017 section 2)
# --------------------------------------------------------------------------


def exact_fit_pool() -> list[Candidate]:
    """A fully eligible, zero-slack 24-entity pool: every raw-matching candidate
    for every quota key is already fully eligible, and no extra/ineligible
    candidate of any kind is present.
    """
    size_labels = [key for key, count in SIZE_QUOTAS.items() for _ in range(count)]
    industry_labels = [key for key, count in INDUSTRY_QUOTAS.items() for _ in range(count)]
    history_labels = [key for key, count in HISTORY_QUOTAS.items() for _ in range(count)]
    assert len(size_labels) == len(industry_labels) == len(history_labels) == TOTAL_OPERATING

    candidates: list[Candidate] = []
    inactive_count = 0
    for cik, (size, industry, history) in enumerate(
        zip(size_labels, industry_labels, history_labels, strict=True), start=1
    ):
        inactive = history == "eventful" and inactive_count < MIN_INACTIVE_EVENTFUL
        if inactive:
            inactive_count += 1
        candidates.append(
            _mk_operating(cik, industry=industry, size=size, history=history, inactive=inactive)
        )
    assert inactive_count == MIN_INACTIVE_EVENTFUL

    cik = TOTAL_OPERATING + 1
    for kind in CONTROL_QUOTAS:
        candidates.append(_mk_control(cik, kind=kind))
        cik += 1
    return candidates


def test_fully_eligible_zero_slack_pool_has_zero_excluded_pool_count_everywhere() -> None:
    result = solve_entity_selection(exact_fit_pool())
    assert result.status == "feasible"
    for quota in result.quota_results:
        assert quota.excluded_pool_count == 0, f"{quota.dimension}.{quota.key}"


def test_a_candidate_in_another_stratum_is_not_counted_as_excluded() -> None:
    pool = exact_fit_pool()
    # a review_required (ineligible) candidate in a DIFFERENT size stratum
    stray = _mk_operating(
        9001,
        industry="technology_and_communications",
        size="accelerated",
        history="stable",
        size_evidence_level="review_required",
    )
    result = solve_entity_selection([*pool, stray])
    large_accelerated_quota = next(
        q for q in result.quota_results if q.dimension == "size" and q.key == "large_accelerated"
    )
    assert large_accelerated_quota.excluded_pool_count == 0
    accelerated_quota = next(
        q for q in result.quota_results if q.dimension == "size" and q.key == "accelerated"
    )
    assert accelerated_quota.excluded_pool_count == 1


def test_a_matching_key_candidate_with_non_provisional_evidence_is_counted_as_excluded() -> None:
    pool = exact_fit_pool()
    stray = _mk_operating(
        9001,
        industry="technology_and_communications",
        size="large_accelerated",
        history="stable",
        size_evidence_level="review_required",
    )
    result = solve_entity_selection([*pool, stray])
    quota = next(
        q for q in result.quota_results if q.dimension == "size" and q.key == "large_accelerated"
    )
    assert quota.excluded_pool_count == 1
    assert quota.achieved_count == SIZE_QUOTAS["large_accelerated"]


def test_control_candidates_of_other_kinds_are_not_counted_as_excluded() -> None:
    pool = exact_fit_pool()
    # an ineligible foreign_private_issuer candidate must not count against
    # the (fully satisfied) asset_backed_issuer quota
    stray = _mk_control(9001, kind="foreign_private_issuer")
    stray = dataclasses.replace(stray, primary_universe_eligible=True)  # fails _control_eligible
    result = solve_entity_selection([*pool, stray])
    asset_backed_quota = next(
        q
        for q in result.quota_results
        if q.dimension == "control" and q.key == "asset_backed_issuer"
    )
    assert asset_backed_quota.excluded_pool_count == 0
    foreign_quota = next(
        q
        for q in result.quota_results
        if q.dimension == "control" and q.key == "foreign_private_issuer"
    )
    assert foreign_quota.excluded_pool_count == 1


def test_structurally_valid_controls_satisfy_their_quota_with_unavailable_unrelated_evidence() -> (
    None
):
    result = solve_entity_selection(exact_fit_pool())
    assert result.status == "feasible"
    control_quotas = [q for q in result.quota_results if q.dimension == "control"]
    assert control_quotas
    for quota in control_quotas:
        assert quota.status == "pass"
        assert quota.excluded_pool_count == 0
