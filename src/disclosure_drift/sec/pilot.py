"""Deterministic pilot selection: compatibility facade over the S4.1 entity selector.

The actual deterministic constrained-search core lives in
:mod:`disclosure_drift.sec.entity_selector` (Decision 013 section 5). This module
re-exports the frozen seed, quota constants, and candidate type from there, and
adapts :func:`solve_entity_selection`'s richer result into the legacy
``PilotSelection``/``QuotaResult`` shape so existing callers are unaffected.

``PILOT_SELECTION_SEED`` stays reachable from this module (not moved to
``cohorts.py`` or ``pilot_policy.py``) through Stage S4, per Decision 016 section 1.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.sec.entity_selector import (
    CONTROL_QUOTAS,
    HISTORY_QUOTAS,
    INDUSTRY_QUOTAS,
    MIN_INACTIVE_EVENTFUL,
    PILOT_SELECTION_SEED,
    SIZE_QUOTAS,
    TOTAL_CONTROLS,
    TOTAL_OPERATING,
    Candidate,
    selection_rank,
    solve_entity_selection,
)

__all__ = [
    "CONTROL_QUOTAS",
    "HISTORY_QUOTAS",
    "INDUSTRY_QUOTAS",
    "MAX_BASE_ACCESSIONS",
    "MAX_BASE_ACCESSIONS_PER_CIK",
    "MAX_TOTAL_ACCESSIONS",
    "MIN_INACTIVE_EVENTFUL",
    "PILOT_SELECTION_SEED",
    "SIZE_QUOTAS",
    "TOTAL_CONTROLS",
    "TOTAL_OPERATING",
    "Candidate",
    "PilotSelection",
    "QuotaResult",
    "select_pilot",
    "selection_rank",
]

# Accession-level caps (Decision 013 section 1 / plan section 4.2). Not touched by
# the S4.1 entity selector; accession selection itself remains frozen for S5.
MAX_BASE_ACCESSIONS_PER_CIK: Final = 4
MAX_BASE_ACCESSIONS: Final = 96
MAX_TOTAL_ACCESSIONS: Final = 120


@dataclass(frozen=True, slots=True)
class QuotaResult:
    """One quota's satisfaction state (legacy shape)."""

    dimension: str
    key: str
    required: int
    available: int
    selected: int

    @property
    def satisfied(self) -> bool:
        """Whether the quota was met exactly."""
        return self.selected == self.required

    @property
    def feasible(self) -> bool:
        """Whether enough candidates existed at all."""
        return self.available >= self.required


@dataclass(frozen=True, slots=True)
class PilotSelection:
    """Deterministic selection outcome plus the quota audit (legacy shape)."""

    selection_seed: str
    operating: tuple[Candidate, ...]
    controls: tuple[Candidate, ...]
    quotas: tuple[QuotaResult, ...]

    @property
    def entities(self) -> tuple[Candidate, ...]:
        """All selected entities in deterministic order."""
        return self.operating + self.controls

    @property
    def infeasible(self) -> tuple[QuotaResult, ...]:
        """Quotas that could not be met from the candidate pool."""
        return tuple(quota for quota in self.quotas if not quota.feasible)

    @property
    def unsatisfied(self) -> tuple[QuotaResult, ...]:
        """Quotas that were feasible but not filled."""
        return tuple(quota for quota in self.quotas if quota.feasible and not quota.satisfied)

    @property
    def is_complete(self) -> bool:
        """Whether every quota is satisfied and totals match."""
        return (
            not self.infeasible
            and not self.unsatisfied
            and len(self.operating) == TOTAL_OPERATING
            and len(self.controls) == TOTAL_CONTROLS
        )

    def manifest_digest(self) -> str:
        """Stable digest over the selected identity, for manifest freezing."""
        payload = "|".join(
            f"{candidate.category}:{candidate.cik_padded}" for candidate in self.entities
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def select_pilot(
    candidates: Iterable[Candidate],
    selection_seed: str = PILOT_SELECTION_SEED,
) -> PilotSelection:
    """Select the pilot deterministically, or stop with a feasibility report.

    Delegates to the S4.1 deterministic constrained-search core
    (:func:`disclosure_drift.sec.entity_selector.solve_entity_selection`). Quotas are
    frozen and never relaxed; there is no discretionary manual substitution
    (Decision 013 section 6).

    Raises:
        GateFailureError: the search proved the pool infeasible, or exhausted its
            deterministic node limit without proving feasibility. The binding or
            unresolved constraints are reported instead of being relaxed.
        ValueError: a candidate has a malformed or duplicate canonical CIK.
    """
    result = solve_entity_selection(candidates, selection_seed=selection_seed)

    if result.status != "feasible":
        binding = ", ".join(
            f"{quota.dimension}.{quota.key} needs {quota.required_count}, "
            f"pool has {quota.available_eligible_count}, selected {quota.achieved_count}"
            for quota in result.quota_results
            if quota.dimension != "summary" and quota.status != "pass"
        )
        if result.status == "infeasible_or_unproven":
            message = (
                "pilot selection could not be proven feasible within the deterministic "
                f"search-node limit ({result.expanded_node_count}/{result.node_limit} "
                "nodes expanded). Quotas are frozen and are never relaxed. "
                f"Unresolved constraints: {binding}"
            )
        else:
            message = (
                f"pilot quotas cannot be satisfied from the candidate pool: {binding}\n"
                "Quotas are frozen and are never relaxed."
            )
        raise GateFailureError(message)

    quotas = tuple(
        QuotaResult(
            dimension=quota.dimension,
            key=quota.key,
            required=quota.required_count,
            available=quota.available_eligible_count,
            selected=quota.achieved_count,
        )
        for quota in result.quota_results
        if quota.dimension != "summary"
    )
    return PilotSelection(
        selection_seed=selection_seed,
        operating=result.selected_operating,
        controls=result.selected_controls,
        quotas=quotas,
    )
