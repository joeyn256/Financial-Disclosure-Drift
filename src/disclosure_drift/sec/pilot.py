"""Deterministic pilot selection scaffold (assignment section 14).

Selection is deterministic, never based on familiarity, and stops rather than
relaxing a quota. The frozen seed and tie-break are fixed:

``sha256(f"{selection_seed}|{cik_padded}".encode("utf-8"))``
"""

from __future__ import annotations

import hashlib
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError

__all__ = [
    "CONTROL_QUOTAS",
    "INDUSTRY_QUOTAS",
    "MAX_BASE_ACCESSIONS",
    "MAX_BASE_ACCESSIONS_PER_CIK",
    "MAX_TOTAL_ACCESSIONS",
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

PILOT_SELECTION_SEED: Final = "disclosure-drift-milestone-02-pilot-v1"
TOTAL_OPERATING: Final = 20
TOTAL_CONTROLS: Final = 4
MAX_BASE_ACCESSIONS_PER_CIK: Final = 4
MAX_BASE_ACCESSIONS: Final = 96
MAX_TOTAL_ACCESSIONS: Final = 120

SIZE_QUOTAS: Final[Mapping[str, int]] = {
    "large_accelerated": 7,
    "accelerated": 7,
    "non_accelerated_or_smaller": 6,
}
INDUSTRY_QUOTAS: Final[Mapping[str, int]] = {
    "technology_and_communications": 4,
    "operating_financial_institutions": 4,
    "industrial_and_materials": 3,
    "consumer_retail_and_services": 3,
    "healthcare_and_life_sciences": 3,
    "energy_and_utilities": 3,
}
HISTORY_QUOTAS: Final[Mapping[str, int]] = {"stable": 10, "eventful": 10}
CONTROL_QUOTAS: Final[Mapping[str, int]] = {
    "registered_investment_company_or_etf": 1,
    "asset_backed_issuer": 1,
    "shell_or_blank_check_issuer": 1,
    "foreign_private_issuer": 1,
}
MIN_INACTIVE_EVENTFUL: Final = 6


def selection_rank(cik_padded: str, selection_seed: str = PILOT_SELECTION_SEED) -> str:
    """Return the frozen deterministic tie-break rank for a CIK."""
    payload = f"{selection_seed}|{cik_padded}".encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class Candidate:
    """One candidate entity from the metadata census."""

    cik_padded: str
    filing_time_name: str
    category: str
    size_stratum: str | None = None
    industry_group: str | None = None
    history_class: str | None = None
    currently_inactive: bool = False
    control_kind: str | None = None

    @property
    def rank(self) -> str:
        """Deterministic tie-break rank."""
        return selection_rank(self.cik_padded)


@dataclass(frozen=True, slots=True)
class QuotaResult:
    """One quota's satisfaction state."""

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
    """Deterministic selection outcome plus the quota audit."""

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

    The selector walks candidates in frozen rank order and accepts one only when it
    still fills a remaining need in every quota dimension. Eventful, currently
    inactive issuers are filled first so the minimum can be met without relaxing
    any other quota. Nothing is chosen for familiarity, and no quota is relaxed.

    Raises:
        GateFailureError: a quota cannot be met from the candidate pool. The binding
            constraints are reported instead of being relaxed.
    """
    pool = sorted(
        candidates,
        key=lambda candidate: selection_rank(candidate.cik_padded, selection_seed),
    )
    operating_pool = [item for item in pool if item.category == "operating"]
    control_pool = [item for item in pool if item.category == "control"]

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

    quotas: list[QuotaResult] = []
    for dimension, requirements, attribute in (
        ("size", SIZE_QUOTAS, "size_stratum"),
        ("industry", INDUSTRY_QUOTAS, "industry_group"),
        ("history", HISTORY_QUOTAS, "history_class"),
    ):
        for key, required in requirements.items():
            quotas.append(
                QuotaResult(
                    dimension=dimension,
                    key=key,
                    required=required,
                    available=_count_selected(operating_pool, attribute, key),
                    selected=_count_selected(chosen, attribute, key),
                )
            )

    controls: list[Candidate] = []
    for key, required in CONTROL_QUOTAS.items():
        eligible = [item for item in control_pool if item.control_kind == key]
        controls.extend(eligible[:required])
        quotas.append(
            QuotaResult(
                dimension="control",
                key=key,
                required=required,
                available=len(eligible),
                selected=len(eligible[:required]),
            )
        )

    quotas.append(
        QuotaResult(
            dimension="history_status",
            key="eventful_currently_inactive",
            required=MIN_INACTIVE_EVENTFUL,
            available=len(
                [
                    item
                    for item in operating_pool
                    if item.history_class == "eventful" and item.currently_inactive
                ]
            ),
            selected=len(
                [
                    item
                    for item in chosen
                    if item.history_class == "eventful" and item.currently_inactive
                ]
            ),
        )
    )

    selection = PilotSelection(
        selection_seed=selection_seed,
        operating=tuple(chosen),
        controls=tuple(controls),
        quotas=tuple(quotas),
    )

    blocking = selection.infeasible or selection.unsatisfied
    if blocking:
        binding = ", ".join(
            f"{quota.dimension}.{quota.key} needs {quota.required}, "
            f"pool has {quota.available}, selected {quota.selected}"
            for quota in blocking
        )
        message = (
            f"pilot quotas cannot be satisfied from the candidate pool: {binding}\n"
            "Quotas are frozen and are never relaxed. Stop, report the binding "
            "constraints, and request a methodological review or a documented manual "
            "substitution."
        )
        raise GateFailureError(message)

    return selection


def _count_selected(items: Sequence[Candidate], attribute: str, key: str) -> int:
    return Counter(getattr(item, attribute) for item in items)[key]
