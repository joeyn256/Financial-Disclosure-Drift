"""S4.1 -- deterministic constrained entity-selector core (Decision 013 section 5).

Pure Python, in-memory only. No SQLite access, no network calls, no filing text, no
outcomes. The selector consumes frozen candidate-snapshot fields and fails closed on
unresolved or ineligible evidence; it does not implement the SIC-family mapping or
the Decision 002 classification algorithm itself -- those are owned by the frozen
candidate snapshot (Stage S3, migration 0009).

Industry-quota admission for the ``operating_financial_institutions`` family is
intentionally decoupled from ``primary_universe_eligible`` (Decision 002's
"Primary-universe boundary clarification"): those four entities are, by design,
``primary_universe_eligible = False`` and ``engineering_only_stress = True`` while
still satisfying their industry quota via ``industry_quota_eligible``. The other
five operating industry families require the opposite: ``primary_universe_eligible
= True`` and ``engineering_only_stress = False``.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, Literal

__all__ = [
    "CONTROL_QUOTAS",
    "DEFAULT_NODE_LIMIT",
    "HISTORY_QUOTAS",
    "INDUSTRY_QUOTAS",
    "MIN_INACTIVE_EVENTFUL",
    "OPERATING_FINANCIAL_INDUSTRY",
    "PILOT_SELECTION_SEED",
    "SIZE_QUOTAS",
    "TOTAL_CONTROLS",
    "TOTAL_OPERATING",
    "Candidate",
    "CandidateDiagnostic",
    "EntitySelectionResult",
    "EntitySelectionStatus",
    "QuotaDiagnostic",
    "selection_rank",
    "solve_entity_selection",
]

PILOT_SELECTION_SEED: Final = "disclosure-drift-milestone-02-pilot-v1"

TOTAL_OPERATING: Final = 20
TOTAL_CONTROLS: Final = 4

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

OPERATING_FINANCIAL_INDUSTRY: Final = "operating_financial_institutions"

DEFAULT_NODE_LIMIT: Final = 200_000

_PROVISIONAL: Final = "provisional"

EntitySelectionStatus = Literal["feasible", "infeasible", "infeasible_or_unproven"]


def selection_rank(cik_padded: str, selection_seed: str = PILOT_SELECTION_SEED) -> str:
    """Return the frozen deterministic tie-break rank for a CIK.

    ``SHA256(selection_seed + "|" + cik_padded)``, canonical lowercase hex. Production
    callers use the frozen ``PILOT_SELECTION_SEED``; ``selection_seed`` may be
    overridden only for synthetic tests.
    """
    payload = f"{selection_seed}|{cik_padded}".encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class Candidate:
    """One immutable candidate entity consumed from the frozen candidate snapshot.

    Every eligibility-relevant field defaults to its fail-closed value: a field left
    unset can never satisfy an affirmative quota. ``filing_time_name`` is diagnostic
    only and never affects selection order.
    """

    cik_padded: str
    filing_time_name: str
    category: str
    primary_universe_eligible: bool = False
    engineering_only_stress: bool = False
    size_stratum: str | None = None
    size_evidence_level: str = "unavailable"
    industry_group: str | None = None
    industry_evidence_level: str = "unavailable"
    industry_quota_eligible: bool = False
    history_class: str | None = None
    history_evidence_level: str = "unavailable"
    currently_inactive: bool = False
    control_kind: str | None = None
    evidence_penalty: int = 0

    @property
    def rank(self) -> str:
        """Deterministic tie-break rank under the frozen production seed."""
        return selection_rank(self.cik_padded)


@dataclass(frozen=True, slots=True)
class CandidateDiagnostic:
    """Why a candidate did not enter the final selection."""

    cik_padded: str
    filing_time_name: str
    category: str
    reason: str


@dataclass(frozen=True, slots=True)
class QuotaDiagnostic:
    """One quota dimension's integer-only satisfaction state.

    ``excluded_pool_count`` (Decision 017) counts only candidates whose *raw*
    classification matches this quota's exact dimension/key but who cannot
    contribute because the applicable eligibility or evidence gate fails; a
    candidate belonging to another stratum, family, class, or control kind is
    never counted here, regardless of its own eligibility.
    """

    dimension: str
    key: str
    comparison_operator: str
    required_count: int
    available_eligible_count: int
    achieved_count: int
    status: str
    binding_constraint: bool
    excluded_pool_count: int


@dataclass(frozen=True, slots=True)
class EntitySelectionResult:
    """The S4.1 entity-selection outcome: status, selection, and diagnostics.

    A non-feasible result never carries a partial selected set: ``selected_operating``
    and ``selected_controls`` are empty unless ``status == "feasible"``.
    """

    status: EntitySelectionStatus
    selection_seed: str
    selected_operating: tuple[Candidate, ...]
    selected_controls: tuple[Candidate, ...]
    quota_results: tuple[QuotaDiagnostic, ...]
    excluded_candidates: tuple[CandidateDiagnostic, ...]
    unresolved_candidates: tuple[CandidateDiagnostic, ...]
    expanded_node_count: int
    node_limit: int
    node_limit_exhausted: bool

    @property
    def selected_order(self) -> tuple[Candidate, ...]:
        """All selected entities in deterministic rank order, operating then controls."""
        return self.selected_operating + self.selected_controls

    @property
    def is_feasible(self) -> bool:
        """Whether this result is a complete, approved selection."""
        return self.status == "feasible"

    def entity_result_digest(self) -> str:
        """Stable digest over the selected entity identity.

        This is an S4.2 hashing input, not the M2.3 manifest hash (Stage S6).
        """
        payload = "|".join(f"{c.category}:{c.cik_padded}" for c in self.selected_order)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _validate_and_normalize(candidates: Iterable[Candidate]) -> tuple[Candidate, ...]:
    """Reject malformed/duplicate canonical CIKs or a non-integer/negative evidence
    penalty; never silently deduplicate or clamp."""
    pool = tuple(candidates)
    seen: dict[str, Candidate] = {}
    for candidate in pool:
        cik = candidate.cik_padded
        if len(cik) != 10 or not cik.isdigit():
            message = f"malformed canonical CIK: {cik!r}"
            raise ValueError(message)
        if cik in seen:
            message = f"duplicate canonical CIK in candidate pool: {cik!r}"
            raise ValueError(message)
        penalty = candidate.evidence_penalty
        if isinstance(penalty, bool) or not isinstance(penalty, int) or penalty < 0:
            message = (
                f"evidence_penalty must be a non-negative integer, got {penalty!r} for CIK {cik!r}"
            )
            raise ValueError(message)
        seen[cik] = candidate
    return pool


def _operating_eligible(candidate: Candidate) -> tuple[bool, str]:
    """Whether an operating candidate may contribute to any affirmative quota.

    Fails closed on every dimension independently, then applies the industry-linked
    primary-universe/engineering-only split (Decision 002; see module docstring).
    """
    if candidate.category != "operating":
        return False, "not_operating_category"
    if candidate.size_stratum not in SIZE_QUOTAS or candidate.size_evidence_level != _PROVISIONAL:
        return False, "size_not_provisional_or_unrecognized"
    if (
        candidate.industry_group not in INDUSTRY_QUOTAS
        or candidate.industry_evidence_level != _PROVISIONAL
        or not candidate.industry_quota_eligible
    ):
        return False, "industry_not_provisional_quota_eligible"
    if (
        candidate.history_class not in HISTORY_QUOTAS
        or candidate.history_evidence_level != _PROVISIONAL
    ):
        return False, "history_not_provisional_or_unrecognized"
    if candidate.industry_group == OPERATING_FINANCIAL_INDUSTRY:
        if candidate.primary_universe_eligible or not candidate.engineering_only_stress:
            return False, "operating_financial_must_be_engineering_only_and_universe_ineligible"
    elif not candidate.primary_universe_eligible or candidate.engineering_only_stress:
        return False, "nonfinancial_operating_must_be_universe_eligible_and_not_stress"
    return True, ""


def _control_eligible(candidate: Candidate, kind: str) -> bool:
    """Whether a control candidate may satisfy the named boundary-control quota."""
    return (
        candidate.category == "control"
        and candidate.control_kind == kind
        and candidate.primary_universe_eligible is False
    )


def _rank_key(candidate: Candidate, selection_seed: str) -> tuple[int, str, str]:
    """Canonical preference key: lower evidence penalty, then rank, then CIK."""
    return (
        candidate.evidence_penalty,
        selection_rank(candidate.cik_padded, selection_seed),
        candidate.cik_padded,
    )


def _hash_key(candidate: Candidate, selection_seed: str) -> tuple[str, str]:
    """Frozen objective terms 3 and 4 only: entity hash, then canonical CIK.

    Deliberately carries no evidence penalty. Objective term 3 minimizes the sorted
    vector of *entity hashes*, so the phase that resolves an equal-total-penalty tie
    must order candidates by hash alone; ordering by ``_rank_key`` there would
    instead minimize the sorted vector of (penalty, hash) pairs, which is a
    different -- and unfrozen -- objective.
    """
    return (selection_rank(candidate.cik_padded, selection_seed), candidate.cik_padded)


@dataclass(frozen=True, slots=True)
class _SuffixCapacity:
    """Suffix quota-reachability counters for one fixed candidate ordering.

    Every array is indexed by position in that ordering; entry ``i`` counts the
    matching candidates in ``order[i:]``. Used only to prune a branch whose suffix
    provably cannot supply what the outstanding quotas still need -- a necessary
    condition for feasibility, so no branch that could complete is ever discarded.
    """

    total: tuple[int, ...]
    size: Mapping[str, tuple[int, ...]]
    industry: Mapping[str, tuple[int, ...]]
    history: Mapping[str, tuple[int, ...]]
    inactive: tuple[int, ...]

    def reachable(
        self,
        i: int,
        remaining_slots: int,
        need_size: Mapping[str, int],
        need_industry: Mapping[str, int],
        need_history: Mapping[str, int],
        inactive_selected: int,
    ) -> bool:
        """Whether the suffix at ``i`` could still cover every outstanding need."""
        if remaining_slots < 0 or self.total[i] < remaining_slots:
            return False
        for key, still_needed in need_size.items():
            if still_needed > self.size[key][i]:
                return False
        for key, still_needed in need_industry.items():
            if still_needed > self.industry[key][i]:
                return False
        for key, still_needed in need_history.items():
            if still_needed > self.history[key][i]:
                return False
        return inactive_selected + self.inactive[i] >= MIN_INACTIVE_EVENTFUL


def _build_suffix_capacity(order: Sequence[Candidate]) -> _SuffixCapacity:
    """Build the suffix quota-reachability counters for one candidate ordering."""
    n = len(order)
    total = [0] * (n + 1)
    size = {key: [0] * (n + 1) for key in SIZE_QUOTAS}
    industry = {key: [0] * (n + 1) for key in INDUSTRY_QUOTAS}
    history = {key: [0] * (n + 1) for key in HISTORY_QUOTAS}
    inactive = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        c = order[i]
        total[i] = total[i + 1] + 1
        for key in SIZE_QUOTAS:
            size[key][i] = size[key][i + 1] + (1 if c.size_stratum == key else 0)
        for key in INDUSTRY_QUOTAS:
            industry[key][i] = industry[key][i + 1] + (1 if c.industry_group == key else 0)
        for key in HISTORY_QUOTAS:
            history[key][i] = history[key][i + 1] + (1 if c.history_class == key else 0)
        inactive[i] = inactive[i + 1] + (
            1 if c.history_class == "eventful" and c.currently_inactive else 0
        )
    return _SuffixCapacity(
        total=tuple(total),
        size={key: tuple(values) for key, values in size.items()},
        industry={key: tuple(values) for key, values in industry.items()},
        history={key: tuple(values) for key, values in history.items()},
        inactive=tuple(inactive),
    )


def _build_min_suffix_penalty(
    order: Sequence[Candidate], unreachable: int
) -> tuple[tuple[int, ...], ...]:
    """Deterministic suffix DP: ``table[i][k]`` is the minimum total evidence
    penalty obtainable by choosing exactly ``k`` candidates from ``order[i:]``,
    **ignoring every quota**, or ``unreachable`` when the suffix holds fewer than
    ``k`` candidates.

    Recurrence, integer-only and independent of the ordering used:
    ``table[n] = (0, unreachable, ..., unreachable)`` and
    ``table[i][k] = min(table[i + 1][k], order[i].evidence_penalty + table[i+1][k-1])``.

    **Admissibility.** For a node at index ``i`` that still needs ``k`` more
    entities, every completion the search could reach selects exactly ``k``
    candidates from ``order[i:]`` and so is one of the ``k``-subsets this table
    minimizes over. Quota-respecting completions are a *subset* of those
    ``k``-subsets, and a minimum taken over a superset can never exceed the minimum
    over a subset. Hence ``table[i][k]`` never overstates the cheapest reachable
    completion, and pruning on ``running_penalty + table[i][k] > target`` cannot
    discard a branch that could still hit ``target``. This holds for *any*
    candidate ordering, which is exactly why the hash-ordered phase can use it
    where the penalty-ordered phase's "cheapest ``k`` are the next ``k``" shortcut
    would be invalid.
    """
    n = len(order)
    table: list[tuple[int, ...]] = [()] * (n + 1)
    table[n] = tuple([0] + [unreachable] * TOTAL_OPERATING)
    for i in range(n - 1, -1, -1):
        penalty = order[i].evidence_penalty
        nxt = table[i + 1]
        current = [0]
        for k in range(1, TOTAL_OPERATING + 1):
            take = penalty + nxt[k - 1]
            best = nxt[k] if nxt[k] < take else take
            current.append(best if best < unreachable else unreachable)
        table[i] = tuple(current)
    return tuple(table)


@dataclass(frozen=True, slots=True)
class _OperatingSearchOutcome:
    chosen: tuple[Candidate, ...] | None
    expanded_node_count: int
    node_limit_exhausted: bool


def _search_operating(
    eligible: Sequence[Candidate],
    selection_seed: str,
    node_limit: int,
) -> _OperatingSearchOutcome:
    """Deterministic, complete two-phase branch-and-bound over eligible operating
    candidates (Decision 013 section 5, as corrected by the combined Opus S4 review's
    blockers B1/B2).

    The two phases answer two different questions and therefore use **two different
    candidate orderings**, each with its own suffix structures. Both orderings are
    total (CIK is unique), so each phase's traversal -- and the shared node count --
    is fully determined by the candidate set, never by input order.

    At each node the candidate at that index is tried include-then-exclude when
    inclusion is still admissible (every one of its size/industry/history buckets
    still has open exact-quota room -- once a bucket's exact target is met, taking
    another same-bucket candidate can never be undone, so it is never a legal
    choice); it is otherwise only excluded.

    **Phase 1 -- prove the minimum total evidence penalty (objective term 2).**
    Ordered by ``_rank_key`` (penalty, hash, CIK). It proves the true minimum
    achievable total (or proves no feasible selection exists at all), pruning any
    branch whose lower bound cannot *improve on* the best value found so far. This
    never mistakes a per-candidate penalty comparison for the true sum (B1): every
    branch is fully explored or soundly pruned before the minimum is accepted.

    **Phase 2 -- minimize the complete sorted entity-hash vector (objective term 3).**
    Ordered by ``_hash_key`` (entity hash, then CIK) and by *nothing else*: no
    per-candidate penalty comparison may influence this tie (B2). Reusing Phase 1's
    penalty-first ordering here would minimize the sorted vector of (penalty, hash)
    pairs instead -- a different objective that returns the larger hash vector
    whenever two equal-total-penalty selections differ in how that total is
    distributed (e.g. 0/15/15 against 10/10/10). Phase 2 accepts a leaf only when its
    running penalty equals Phase 1's proven minimum exactly, and prunes as soon as
    that target is provably out of reach.

    *Why Phase 2's first leaf is the lexicographic minimum.* Take any two distinct
    exact-target completions and let ``i`` be the first index at which they disagree.
    Because the ordering is ascending by hash, ``order[i]`` carries the smallest hash
    in the symmetric difference of the two selections, so the completion containing
    it has the lexicographically smaller sorted hash vector. Depth-first search with
    include-before-exclude explores the entire include branch at ``i`` before the
    exclude branch, so if *any* exact-target completion extends the shared prefix
    with ``order[i]``, one is found before any completion that omits it. Applying
    this at each index in turn, the first complete leaf is the lexicographically
    smallest exact-target hash vector. The include branch is abandoned only after it
    has been proven to contain no exact-target completion.

    Both phases share one node counter and one node limit, since both are part of
    proving the same optimum. Node-limit exhaustion in either phase always aborts the
    whole search with ``chosen=None`` and ``node_limit_exhausted=True``, even when a
    feasible incumbent was already found internally: an unproven-optimal selection is
    never returned as a result.

    Controls are solved separately (:func:`_select_controls`) but remain part of the
    same 24-entity objective; see that function for why the decomposition is exact.
    """
    n = len(eligible)
    # Strictly greater than any achievable total penalty, so a bound of `unreachable`
    # always prunes. Integer-only: the objective admits no floating-point sentinel.
    unreachable = sum(c.evidence_penalty for c in eligible) + 1

    penalty_order = tuple(sorted(eligible, key=lambda c: _rank_key(c, selection_seed)))
    hash_order = tuple(sorted(eligible, key=lambda c: _hash_key(c, selection_seed)))
    penalty_capacity = _build_suffix_capacity(penalty_order)
    hash_capacity = _build_suffix_capacity(hash_order)
    penalty_bound = _build_min_suffix_penalty(penalty_order, unreachable)
    hash_bound = _build_min_suffix_penalty(hash_order, unreachable)

    nodes_expanded = 0
    limit_hit = False

    def admissible_bucket(
        candidate: Candidate,
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
    ) -> tuple[str, str, str] | None:
        size_key = candidate.size_stratum
        industry_key = candidate.industry_group
        history_key = candidate.history_class
        if (
            size_key is not None
            and industry_key is not None
            and history_key is not None
            and need_size[size_key] > 0
            and need_industry[industry_key] > 0
            and need_history[history_key] > 0
        ):
            return size_key, industry_key, history_key
        return None

    # ---- Phase 1: prove the minimum achievable total evidence penalty ----------
    best_penalty: int | None = None

    def dfs_minimize(
        i: int,
        chosen_count: int,
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
        inactive_selected: int,
        running_penalty: int,
    ) -> None:
        nonlocal nodes_expanded, limit_hit, best_penalty
        if limit_hit:
            return
        nodes_expanded += 1
        if nodes_expanded > node_limit:
            limit_hit = True
            return

        remaining_slots = TOTAL_OPERATING - chosen_count
        if remaining_slots == 0:
            if (
                all(v == 0 for v in need_size.values())
                and all(v == 0 for v in need_industry.values())
                and all(v == 0 for v in need_history.values())
                and inactive_selected >= MIN_INACTIVE_EVENTFUL
                and (best_penalty is None or running_penalty < best_penalty)
            ):
                best_penalty = running_penalty
            return
        if i >= n:
            return
        if not penalty_capacity.reachable(
            i, remaining_slots, need_size, need_industry, need_history, inactive_selected
        ):
            return
        if best_penalty is not None:
            lower_bound = running_penalty + penalty_bound[i][remaining_slots]
            if lower_bound >= best_penalty:
                return

        candidate = penalty_order[i]
        bucket = admissible_bucket(candidate, need_size, need_industry, need_history)
        if bucket is not None:
            size_key, industry_key, history_key = bucket
            need_size[size_key] -= 1
            need_industry[industry_key] -= 1
            need_history[history_key] -= 1
            new_inactive = inactive_selected + (
                1 if history_key == "eventful" and candidate.currently_inactive else 0
            )
            dfs_minimize(
                i + 1,
                chosen_count + 1,
                need_size,
                need_industry,
                need_history,
                new_inactive,
                running_penalty + candidate.evidence_penalty,
            )
            need_size[size_key] += 1
            need_industry[industry_key] += 1
            need_history[history_key] += 1

        dfs_minimize(
            i + 1,
            chosen_count,
            need_size,
            need_industry,
            need_history,
            inactive_selected,
            running_penalty,
        )

    dfs_minimize(0, 0, dict(SIZE_QUOTAS), dict(INDUSTRY_QUOTAS), dict(HISTORY_QUOTAS), 0, 0)

    if limit_hit:
        return _OperatingSearchOutcome(
            chosen=None, expanded_node_count=nodes_expanded, node_limit_exhausted=True
        )
    if best_penalty is None:
        return _OperatingSearchOutcome(
            chosen=None, expanded_node_count=nodes_expanded, node_limit_exhausted=False
        )
    target_penalty = best_penalty

    # ---- Phase 2: smallest complete sorted hash vector at that exact target -------
    # Hash-ordered, penalty-blind: objective term 3 ranks selections by their sorted
    # entity-hash vector alone, so nothing about how the (already fixed) total
    # penalty is distributed across candidates may steer this traversal.
    solution: list[Candidate] = []

    def dfs_achieve(
        i: int,
        chosen: list[Candidate],
        need_size: dict[str, int],
        need_industry: dict[str, int],
        need_history: dict[str, int],
        inactive_selected: int,
        running_penalty: int,
    ) -> bool:
        nonlocal nodes_expanded, limit_hit
        if limit_hit:
            return False
        nodes_expanded += 1
        if nodes_expanded > node_limit:
            limit_hit = True
            return False

        remaining_slots = TOTAL_OPERATING - len(chosen)
        if remaining_slots == 0:
            if (
                running_penalty == target_penalty
                and all(v == 0 for v in need_size.values())
                and all(v == 0 for v in need_industry.values())
                and all(v == 0 for v in need_history.values())
                and inactive_selected >= MIN_INACTIVE_EVENTFUL
            ):
                solution.extend(chosen)
                return True
            return False
        if i >= n:
            return False
        if not hash_capacity.reachable(
            i, remaining_slots, need_size, need_industry, need_history, inactive_selected
        ):
            return False
        lower_bound = running_penalty + hash_bound[i][remaining_slots]
        if lower_bound > target_penalty:
            return False

        candidate = hash_order[i]
        bucket = admissible_bucket(candidate, need_size, need_industry, need_history)
        if bucket is not None:
            size_key, industry_key, history_key = bucket
            need_size[size_key] -= 1
            need_industry[industry_key] -= 1
            need_history[history_key] -= 1
            chosen.append(candidate)
            new_inactive = inactive_selected + (
                1 if history_key == "eventful" and candidate.currently_inactive else 0
            )
            if dfs_achieve(
                i + 1,
                chosen,
                need_size,
                need_industry,
                need_history,
                new_inactive,
                running_penalty + candidate.evidence_penalty,
            ):
                return True
            chosen.pop()
            need_size[size_key] += 1
            need_industry[industry_key] += 1
            need_history[history_key] += 1

        return dfs_achieve(
            i + 1,
            chosen,
            need_size,
            need_industry,
            need_history,
            inactive_selected,
            running_penalty,
        )

    dfs_achieve(0, [], dict(SIZE_QUOTAS), dict(INDUSTRY_QUOTAS), dict(HISTORY_QUOTAS), 0, 0)

    # mypy narrows `limit_hit` to False from phase 1's own equivalent guard above and
    # does not account for `dfs_achieve` reassigning it via `nonlocal` -- this branch
    # is genuinely reachable (proven by the node-limit tests) despite the false
    # positive.
    if limit_hit:
        return _OperatingSearchOutcome(  # type: ignore[unreachable]
            chosen=None, expanded_node_count=nodes_expanded, node_limit_exhausted=True
        )
    return _OperatingSearchOutcome(
        chosen=tuple(solution),
        expanded_node_count=nodes_expanded,
        node_limit_exhausted=False,
    )


def _select_controls(
    pool: Sequence[Candidate], selection_seed: str
) -> tuple[dict[str, list[Candidate]], tuple[Candidate, ...], tuple[str, ...]]:
    """Deterministically select one candidate per control kind.

    **Why solving controls separately is exact for the joint 24-entity objective.**
    ``_control_eligible`` matches a candidate to the single kind its ``control_kind``
    names, so the four eligible sets are pairwise disjoint; controls are also
    category-disjoint from the operating pool and every canonical CIK is unique
    (``_validate_and_normalize``). Each kind needs exactly one entity and no control
    contributes to an operating quota, so the feasible 24-entity selections are
    exactly the product of the operating solutions and the four independent control
    choices.

    - *Objective term 2* (total penalty) is a sum over that product, so minimizing
      each factor independently minimizes the total.
    - *Objective term 3* (sorted 24-hash vector) decomposes because a sorted-merge is
      monotone for equal-size disjoint selections: for equal-size selections ``A``
      and ``A'`` and a disjoint ``C``, the smallest element of ``A △ A'`` is also the
      smallest element of ``(A ∪ C) △ (A' ∪ C)``, and the sorted vector containing it
      is the lexicographically smaller one. So replacing either factor by its own
      lexicographic minimum can only shrink the merged vector, and applying that to
      both factors in turn yields the joint minimum.

    Each kind's choice is therefore independently and provably optimal: the single
    lowest (evidence penalty, rank, CIK) eligible candidate for that kind, which is
    minimal in penalty first and -- among the equal-penalty options -- minimal in
    hash, matching the frozen term order.
    """
    eligible_by_kind: dict[str, list[Candidate]] = {kind: [] for kind in CONTROL_QUOTAS}
    for candidate in pool:
        if candidate.category != "control":
            continue
        for kind in CONTROL_QUOTAS:
            if _control_eligible(candidate, kind):
                eligible_by_kind[kind].append(candidate)

    selected: list[Candidate] = []
    missing: list[str] = []
    for kind in CONTROL_QUOTAS:
        options = eligible_by_kind[kind]
        if not options:
            missing.append(kind)
            continue
        best = min(options, key=lambda c: _rank_key(c, selection_seed))
        selected.append(best)

    return eligible_by_kind, tuple(selected), tuple(missing)


def _count_by(items: Iterable[Candidate], attribute: str, key: str) -> int:
    return sum(1 for item in items if getattr(item, attribute) == key)


def _quota_status(status: EntitySelectionStatus, achieved: int, required: int) -> str:
    if status == "infeasible_or_unproven":
        return "unproven"
    if status == "feasible":
        return "pass" if achieved >= required else "fail"
    return "fail"


def _build_quota_results(
    status: EntitySelectionStatus,
    pool: Sequence[Candidate],
    operating_eligible: Sequence[Candidate],
    selected_operating: Sequence[Candidate],
    control_eligible_by_kind: Mapping[str, list[Candidate]],
    selected_controls: Sequence[Candidate],
) -> tuple[QuotaDiagnostic, ...]:
    """Build the per-quota diagnostics, including ``excluded_pool_count`` (Decision 017).

    ``excluded_pool_count`` is always computed from the raw candidate ``pool``
    (every candidate offered, eligible or not) rather than from any eligible-only
    subset, so a candidate that never even reaches ``operating_eligible``/
    ``control_eligible_by_kind`` (e.g. wrong evidence level, wrong universe
    boundary) is still counted -- but only against the one quota whose raw key it
    actually matches, never against an unrelated stratum, family, class, or
    control kind.
    """
    results: list[QuotaDiagnostic] = []
    operating_eligible_ids = {c.cik_padded for c in operating_eligible}
    all_control_eligible_ids = {
        c.cik_padded for options in control_eligible_by_kind.values() for c in options
    }

    def _operating_excluded(attribute: str, key: str) -> int:
        return sum(
            1
            for c in pool
            if c.category == "operating"
            and getattr(c, attribute) == key
            and c.cik_padded not in operating_eligible_ids
        )

    for key, required in SIZE_QUOTAS.items():
        available = _count_by(operating_eligible, "size_stratum", key)
        achieved = _count_by(selected_operating, "size_stratum", key)
        results.append(
            QuotaDiagnostic(
                "size",
                key,
                "exact",
                required,
                available,
                achieved,
                _quota_status(status, achieved, required),
                available < required,
                _operating_excluded("size_stratum", key),
            )
        )
    for key, required in INDUSTRY_QUOTAS.items():
        available = _count_by(operating_eligible, "industry_group", key)
        achieved = _count_by(selected_operating, "industry_group", key)
        results.append(
            QuotaDiagnostic(
                "industry",
                key,
                "exact",
                required,
                available,
                achieved,
                _quota_status(status, achieved, required),
                available < required,
                _operating_excluded("industry_group", key),
            )
        )
    for key, required in HISTORY_QUOTAS.items():
        available = _count_by(operating_eligible, "history_class", key)
        achieved = _count_by(selected_operating, "history_class", key)
        results.append(
            QuotaDiagnostic(
                "history",
                key,
                "exact",
                required,
                available,
                achieved,
                _quota_status(status, achieved, required),
                available < required,
                _operating_excluded("history_class", key),
            )
        )

    inactive_available = sum(
        1 for c in operating_eligible if c.history_class == "eventful" and c.currently_inactive
    )
    inactive_achieved = sum(
        1 for c in selected_operating if c.history_class == "eventful" and c.currently_inactive
    )
    inactive_excluded = sum(
        1
        for c in pool
        if c.category == "operating"
        and c.history_class == "eventful"
        and c.currently_inactive
        and c.cik_padded not in operating_eligible_ids
    )
    results.append(
        QuotaDiagnostic(
            "history_status",
            "eventful_currently_inactive",
            "at_least",
            MIN_INACTIVE_EVENTFUL,
            inactive_available,
            inactive_achieved,
            _quota_status(status, inactive_achieved, MIN_INACTIVE_EVENTFUL),
            inactive_available < MIN_INACTIVE_EVENTFUL,
            inactive_excluded,
        )
    )

    for kind, required in CONTROL_QUOTAS.items():
        options = control_eligible_by_kind.get(kind, [])
        available = len(options)
        achieved = 1 if any(c.control_kind == kind for c in selected_controls) else 0
        eligible_ids_for_kind = {c.cik_padded for c in options}
        excluded = sum(
            1
            for c in pool
            if c.category == "control"
            and c.control_kind == kind
            and c.cik_padded not in eligible_ids_for_kind
        )
        results.append(
            QuotaDiagnostic(
                "control",
                kind,
                "exact",
                required,
                available,
                achieved,
                _quota_status(status, achieved, required),
                available < required,
                excluded,
            )
        )

    controls_available = sum(len(options) for options in control_eligible_by_kind.values())
    controls_achieved = len(selected_controls)
    controls_excluded = sum(
        1 for c in pool if c.category == "control" and c.cik_padded not in all_control_eligible_ids
    )
    results.append(
        QuotaDiagnostic(
            "summary",
            "total_controls",
            "exact",
            TOTAL_CONTROLS,
            controls_available,
            controls_achieved,
            _quota_status(status, controls_achieved, TOTAL_CONTROLS),
            controls_available < TOTAL_CONTROLS,
            controls_excluded,
        )
    )

    operating_available = len(operating_eligible)
    operating_achieved = len(selected_operating)
    operating_excluded = sum(
        1 for c in pool if c.category == "operating" and c.cik_padded not in operating_eligible_ids
    )
    results.append(
        QuotaDiagnostic(
            "summary",
            "operating_total",
            "exact",
            TOTAL_OPERATING,
            operating_available,
            operating_achieved,
            _quota_status(status, operating_achieved, TOTAL_OPERATING),
            operating_available < TOTAL_OPERATING,
            operating_excluded,
        )
    )

    total_required = TOTAL_OPERATING + TOTAL_CONTROLS
    total_available = operating_available + sum(
        len(options) for options in control_eligible_by_kind.values()
    )
    total_achieved = operating_achieved + len(selected_controls)
    results.append(
        QuotaDiagnostic(
            "summary",
            "total_entities",
            "exact",
            total_required,
            total_available,
            total_achieved,
            _quota_status(status, total_achieved, total_required),
            total_available < total_required,
            operating_excluded + controls_excluded,
        )
    )

    return tuple(results)


def solve_entity_selection(
    candidates: Iterable[Candidate],
    *,
    selection_seed: str = PILOT_SELECTION_SEED,
    node_limit: int = DEFAULT_NODE_LIMIT,
) -> EntitySelectionResult:
    """Solve the S4.1 entity-level allocation problem deterministically.

    Implements only the entity-level prefix of the frozen lexicographic objective:
    zero unmet hard entity quotas, then minimize integer evidence penalty, then
    minimize the ordered vector of selected entity hashes. Accession-level terms
    (base/stress-accession counts, accession hashes, reserves) are out of scope for
    S4.1 and remain frozen for S5.

    Raises:
        ValueError: a candidate has a malformed canonical CIK, or the same canonical
            CIK appears more than once in ``candidates``.
    """
    pool = _validate_and_normalize(candidates)

    operating_eligible: list[Candidate] = []
    excluded: list[CandidateDiagnostic] = []
    for candidate in pool:
        if candidate.category not in ("operating", "control"):
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded,
                    candidate.filing_time_name,
                    candidate.category,
                    "unrecognized_category",
                )
            )
            continue
        if candidate.category != "operating":
            continue
        ok, reason = _operating_eligible(candidate)
        if ok:
            operating_eligible.append(candidate)
        else:
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded, candidate.filing_time_name, candidate.category, reason
                )
            )

    control_eligible_by_kind, selected_controls, missing_control_kinds = _select_controls(
        pool, selection_seed
    )
    eligible_control_ids = {
        c.cik_padded for options in control_eligible_by_kind.values() for c in options
    }
    for candidate in pool:
        if candidate.category != "control":
            continue
        if candidate.cik_padded not in eligible_control_ids:
            excluded.append(
                CandidateDiagnostic(
                    candidate.cik_padded,
                    candidate.filing_time_name,
                    candidate.category,
                    "control_ineligible",
                )
            )

    outcome = _search_operating(operating_eligible, selection_seed, node_limit)

    if outcome.node_limit_exhausted:
        status: EntitySelectionStatus = "infeasible_or_unproven"
    elif missing_control_kinds or outcome.chosen is None:
        status = "infeasible"
    else:
        status = "feasible"

    if status == "feasible" and outcome.chosen is not None:
        selected_operating = tuple(
            sorted(outcome.chosen, key=lambda c: _rank_key(c, selection_seed))
        )
        final_controls = tuple(
            sorted(selected_controls, key=lambda c: _rank_key(c, selection_seed))
        )
    else:
        selected_operating = ()
        final_controls = ()

    selected_ciks = {c.cik_padded for c in selected_operating} | {
        c.cik_padded for c in final_controls
    }
    unresolved: list[CandidateDiagnostic] = [
        CandidateDiagnostic(
            c.cik_padded, c.filing_time_name, c.category, "eligible_but_not_selected"
        )
        for c in operating_eligible
        if c.cik_padded not in selected_ciks
    ]
    for options in control_eligible_by_kind.values():
        unresolved.extend(
            CandidateDiagnostic(
                c.cik_padded, c.filing_time_name, c.category, "eligible_but_not_selected"
            )
            for c in options
            if c.cik_padded not in selected_ciks
        )
    unresolved.sort(key=lambda d: d.cik_padded)
    excluded.sort(key=lambda d: d.cik_padded)

    quota_results = _build_quota_results(
        status,
        pool,
        operating_eligible,
        selected_operating,
        control_eligible_by_kind,
        final_controls,
    )

    return EntitySelectionResult(
        status=status,
        selection_seed=selection_seed,
        selected_operating=selected_operating,
        selected_controls=final_controls,
        quota_results=quota_results,
        excluded_candidates=tuple(excluded),
        unresolved_candidates=tuple(unresolved),
        expanded_node_count=outcome.expanded_node_count,
        node_limit=node_limit,
        node_limit_exhausted=outcome.node_limit_exhausted,
    )
