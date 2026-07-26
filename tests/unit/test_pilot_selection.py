"""Deterministic pilot selection, quota audit, and infeasibility behaviour."""

from __future__ import annotations

import hashlib

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.sec.pilot import (
    CONTROL_QUOTAS,
    INDUSTRY_QUOTAS,
    MAX_BASE_ACCESSIONS,
    MAX_BASE_ACCESSIONS_PER_CIK,
    MAX_TOTAL_ACCESSIONS,
    PILOT_SELECTION_SEED,
    SIZE_QUOTAS,
    TOTAL_CONTROLS,
    TOTAL_OPERATING,
    Candidate,
    select_pilot,
    selection_rank,
)

SIZES = ("large_accelerated", "accelerated", "non_accelerated_or_smaller")
INDUSTRIES = tuple(INDUSTRY_QUOTAS)


def build_pool(per_bucket: int = 4) -> list[Candidate]:
    """Build a synthetic candidate pool covering every quota bucket."""
    candidates: list[Candidate] = []
    counter = 1
    for size in SIZES:
        for industry in INDUSTRIES:
            for history in ("stable", "eventful"):
                for index in range(per_bucket):
                    candidates.append(
                        Candidate(
                            cik_padded=f"{counter:010d}",
                            filing_time_name=f"Synthetic Issuer {counter}",
                            category="operating",
                            size_stratum=size,
                            industry_group=industry,
                            history_class=history,
                            currently_inactive=history == "eventful" and index % 2 == 0,
                        )
                    )
                    counter += 1
    for kind in CONTROL_QUOTAS:
        candidates.append(
            Candidate(
                cik_padded=f"{counter:010d}",
                filing_time_name=f"Synthetic Control {kind}",
                category="control",
                control_kind=kind,
            )
        )
        counter += 1
    return candidates


def test_frozen_seed_and_tie_break_formula() -> None:
    assert PILOT_SELECTION_SEED == "disclosure-drift-milestone-02-pilot-v1"
    expected = hashlib.sha256(f"{PILOT_SELECTION_SEED}|0000320193".encode()).hexdigest()
    assert selection_rank("0000320193") == expected
    assert Candidate("0000320193", "n", "operating").rank == expected


def test_tie_break_uses_the_pipe_separator() -> None:
    without_separator = hashlib.sha256(f"{PILOT_SELECTION_SEED}0000320193".encode()).hexdigest()
    assert selection_rank("0000320193") != without_separator


def test_quota_constants_match_the_approved_design() -> None:
    assert sum(SIZE_QUOTAS.values()) == TOTAL_OPERATING == 20
    assert sum(INDUSTRY_QUOTAS.values()) == TOTAL_OPERATING
    assert sum(CONTROL_QUOTAS.values()) == TOTAL_CONTROLS == 4
    assert (MAX_BASE_ACCESSIONS_PER_CIK, MAX_BASE_ACCESSIONS, MAX_TOTAL_ACCESSIONS) == (4, 96, 120)


def test_selection_is_complete_and_satisfies_every_quota() -> None:
    selection = select_pilot(build_pool())
    assert len(selection.operating) == TOTAL_OPERATING
    assert len(selection.controls) == TOTAL_CONTROLS
    assert selection.is_complete
    assert not selection.unsatisfied
    assert not selection.infeasible


def test_selection_is_deterministic_across_runs_and_input_order() -> None:
    pool = build_pool()
    first = select_pilot(pool)
    second = select_pilot(list(reversed(pool)))
    assert [item.cik_padded for item in first.entities] == [
        item.cik_padded for item in second.entities
    ]
    assert first.manifest_digest() == second.manifest_digest()


def test_a_different_seed_changes_the_selection() -> None:
    pool = build_pool()
    baseline = select_pilot(pool)
    alternative = select_pilot(pool, selection_seed="some-other-seed")
    assert baseline.manifest_digest() != alternative.manifest_digest()


def test_size_industry_and_history_quotas_are_all_filled() -> None:
    selection = select_pilot(build_pool())
    for quota in selection.quotas:
        assert quota.satisfied, f"{quota.dimension}.{quota.key} was not filled"


def test_minimum_inactive_eventful_entities_are_selected() -> None:
    selection = select_pilot(build_pool())
    inactive = [
        item
        for item in selection.operating
        if item.history_class == "eventful" and item.currently_inactive
    ]
    assert len(inactive) >= 6


def test_each_control_kind_is_represented_exactly_once() -> None:
    selection = select_pilot(build_pool())
    kinds = [item.control_kind for item in selection.controls]
    assert sorted(kinds) == sorted(CONTROL_QUOTAS)


def test_selection_never_repeats_a_cik() -> None:
    selection = select_pilot(build_pool())
    identifiers = [item.cik_padded for item in selection.entities]
    assert len(identifiers) == len(set(identifiers))


def test_infeasible_pool_stops_and_names_the_binding_constraint() -> None:
    pool = [
        item
        for item in build_pool()
        if not (item.category == "operating" and item.industry_group == "energy_and_utilities")
    ]
    with pytest.raises(GateFailureError) as excinfo:
        select_pilot(pool)
    message = str(excinfo.value)
    assert "industry.energy_and_utilities" in message
    assert "never relaxed" in message


def test_missing_control_stops_selection() -> None:
    pool = [item for item in build_pool() if item.control_kind != "asset_backed_issuer"]
    with pytest.raises(GateFailureError, match="control.asset_backed_issuer"):
        select_pilot(pool)


def test_insufficient_inactive_eventful_pool_stops_selection() -> None:
    pool = [
        Candidate(
            cik_padded=item.cik_padded,
            filing_time_name=item.filing_time_name,
            category=item.category,
            size_stratum=item.size_stratum,
            industry_group=item.industry_group,
            history_class=item.history_class,
            currently_inactive=False,
            control_kind=item.control_kind,
        )
        for item in build_pool()
    ]
    with pytest.raises(GateFailureError, match="history_status.eventful_currently_inactive"):
        select_pilot(pool)


def test_manifest_digest_is_stable_for_the_same_identity() -> None:
    selection = select_pilot(build_pool())
    assert selection.manifest_digest() == selection.manifest_digest()
    assert len(selection.manifest_digest()) == 64
