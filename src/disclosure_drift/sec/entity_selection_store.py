"""S4.2 -- frozen candidate-snapshot reconstruction and entity-selection persistence.

Reads one frozen ``pilot_candidate_snapshots`` row (migration 0009) into the pure
S4.1 :class:`~disclosure_drift.sec.entity_selector.Candidate` shape, runs the S4.1
solver in-memory, and persists an **entity-only running draft** into the existing
migration-0009 tables. The persisted draft is never presented as a final feasible
pilot run or a manifest: ``run_state`` stays ``'running'`` because S5 accession-level
objective terms can still change the joint optimum (Decision 013 section 5).

This module does not read from or write to SQLite outside of what it is explicitly
given a connection for, does not retrieve SEC data, and does not touch
``inventory_*`` tables. No dependency, table, migration, source registration, or
reason code is added here.

``quota_policy_version`` now defaults to the frozen ``PILOT_QUOTA_POLICY_VERSION``
(Decision 017 section 1; migration 0010 seeds the identical value into
``reference_policy_versions``), resolving the ambiguity an earlier revision of this
module flagged. The parameter remains overridable so tests can pin an arbitrary,
non-production value without touching the frozen constant.
"""

from __future__ import annotations

import hashlib
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError
from disclosure_drift.pilot_policy import (
    PILOT_CANDIDATE_POLICY_VERSION,
    PILOT_EVIDENCE_POLICY_VERSION,
    PILOT_QUOTA_POLICY_VERSION,
    PILOT_SELECTOR_POLICY_VERSION,
    SIC_FAMILY_MAPPING_VERSION,
)
from disclosure_drift.release.hashing import hash_table
from disclosure_drift.sec.entity_selector import (
    DEFAULT_NODE_LIMIT,
    PILOT_SELECTION_SEED,
    Candidate,
    QuotaDiagnostic,
    selection_rank,
    solve_entity_selection,
)
from disclosure_drift.storage.sqlite import transaction

__all__ = [
    "ENTITY_SELECTION_INPUT_SCHEMA_VERSION",
    "EntitySelectionRunIdentity",
    "FrozenEntityCandidateSet",
    "PersistedEntitySelectionResult",
    "build_entity_selection_run_identity",
    "execute_and_persist_entity_selection",
    "load_frozen_entity_candidates",
    "reconstruct_persisted_entity_selection",
]

# Owned by this module (not a repository-wide policy constant): versions the
# normalized entity-selection input/run-identity record shape defined below.
ENTITY_SELECTION_INPUT_SCHEMA_VERSION: Final = "pilot-entity-selection-input/1.0"

_OBJECTIVE_TERM_ORDER: Final = (
    "zero_unmet_hard_entity_quotas|minimize_evidence_penalty|minimize_entity_hash_vector"
)

_PILOT_SELECTION_INFEASIBLE: Final = "PILOT_SELECTION_INFEASIBLE"
_PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN: Final = "PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN"

_CANDIDATE_ENTITY_COLUMNS: Final = (
    "cik_numeric",
    "cik_padded",
    "entity_tie_break_sha256",
    "candidate_category",
    "control_kind",
    "size_stratum",
    "size_evidence_level",
    "industry_family",
    "industry_quota_eligible",
    "industry_evidence_level",
    "history_class",
    "history_evidence_level",
    "currently_inactive",
    "primary_universe_eligible",
    "engineering_only_stress",
    "filing_time_name",
)


@dataclass(frozen=True, slots=True)
class FrozenEntityCandidateSet:
    """One frozen snapshot's entity candidates, verified and reconstructed."""

    snapshot_id: str
    candidate_snapshot_sha256: str
    entity_count: int
    candidates: tuple[Candidate, ...]


@dataclass(frozen=True, slots=True)
class EntitySelectionRunIdentity:
    """The deterministic, content-derived identity of one entity-selection run."""

    snapshot_id: str
    selection_seed: str
    selector_policy_version: str
    quota_policy_version: str
    node_limit: int
    selection_input_sha256: str
    selection_run_id: str


@dataclass(frozen=True, slots=True)
class PersistedEntitySelectionResult:
    """A reconstructed or freshly persisted entity-selection outcome.

    ``is_entity_feasible_draft`` is the only supported way to tell a running
    entity-only draft apart from a final feasible pilot run: this module never
    sets ``run_state = 'feasible'`` (that requires S5 accession-level terms), so
    a caller must not treat ``is_entity_feasible_draft`` as manifest-ready.
    """

    selection_run_id: str
    snapshot_id: str
    run_state: str
    is_entity_feasible_draft: bool
    selection_seed: str
    selector_policy_version: str
    quota_policy_version: str
    node_limit: int
    expanded_node_count: int | None
    node_limit_exhausted: bool
    selection_input_sha256: str
    selected_entity_count: int | None
    selected_accession_count: int | None
    selected_operating: tuple[Candidate, ...]
    selected_controls: tuple[Candidate, ...]
    quota_results: tuple[QuotaDiagnostic, ...]

    @property
    def selected_order(self) -> tuple[Candidate, ...]:
        """All selected entities in persisted order, operating then controls."""
        return self.selected_operating + self.selected_controls


def load_frozen_entity_candidates(
    connection: sqlite3.Connection, snapshot_id: str
) -> FrozenEntityCandidateSet:
    """Reconstruct the S4.1 candidate input set from one frozen snapshot.

    Performs no writes. Fails closed on: a missing snapshot, a non-frozen
    snapshot, an entity-row-count mismatch against the frozen declared count, a
    canonical CIK disagreement, a stored entity tie-break hash that does not
    match the frozen ``SHA256(PILOT_SELECTION_SEED + "|" + cik_padded)`` formula,
    or a candidate/evidence/SIC-family policy version that does not match the
    frozen Python policy constants. Does not reclassify SICs or evidence; it only
    consumes the resolved frozen candidate fields.
    """
    snapshot_row = connection.execute(
        "SELECT snapshot_id, snapshot_state, entity_count, candidate_snapshot_sha256, "
        "candidate_policy_version, sic_family_mapping_version, evidence_policy_version "
        "FROM pilot_candidate_snapshots WHERE snapshot_id = ?",
        (snapshot_id,),
    ).fetchone()
    if snapshot_row is None:
        message = f"no pilot candidate snapshot exists for snapshot_id {snapshot_id!r}"
        raise GateFailureError(message)
    if snapshot_row["snapshot_state"] != "frozen":
        message = (
            f"pilot candidate snapshot {snapshot_id!r} is "
            f"{snapshot_row['snapshot_state']!r}, not frozen"
        )
        raise GateFailureError(message)
    if snapshot_row["candidate_policy_version"] != PILOT_CANDIDATE_POLICY_VERSION:
        message = (
            "frozen snapshot candidate_policy_version "
            f"{snapshot_row['candidate_policy_version']!r} does not match the frozen "
            f"PILOT_CANDIDATE_POLICY_VERSION {PILOT_CANDIDATE_POLICY_VERSION!r}"
        )
        raise GateFailureError(message)
    if snapshot_row["sic_family_mapping_version"] != SIC_FAMILY_MAPPING_VERSION:
        message = (
            "frozen snapshot sic_family_mapping_version "
            f"{snapshot_row['sic_family_mapping_version']!r} does not match the frozen "
            f"SIC_FAMILY_MAPPING_VERSION {SIC_FAMILY_MAPPING_VERSION!r}"
        )
        raise GateFailureError(message)
    if snapshot_row["evidence_policy_version"] != PILOT_EVIDENCE_POLICY_VERSION:
        message = (
            "frozen snapshot evidence_policy_version "
            f"{snapshot_row['evidence_policy_version']!r} does not match the frozen "
            f"PILOT_EVIDENCE_POLICY_VERSION {PILOT_EVIDENCE_POLICY_VERSION!r}"
        )
        raise GateFailureError(message)

    declared_entity_count = snapshot_row["entity_count"]
    rows = connection.execute(
        f"SELECT {', '.join(_CANDIDATE_ENTITY_COLUMNS)} "  # noqa: S608 -- fixed column allowlist
        "FROM pilot_candidate_entities WHERE snapshot_id = ? ORDER BY cik_numeric",
        (snapshot_id,),
    ).fetchall()
    if len(rows) != declared_entity_count:
        message = (
            f"pilot candidate snapshot {snapshot_id!r} declares entity_count "
            f"{declared_entity_count}, but {len(rows)} pilot_candidate_entities rows exist"
        )
        raise GateFailureError(message)

    candidates: list[Candidate] = []
    for row in rows:
        cik_numeric = row["cik_numeric"]
        cik_padded = row["cik_padded"]
        expected_padded = f"{cik_numeric:010d}"
        if cik_padded != expected_padded:
            message = (
                f"snapshot {snapshot_id!r} cik_numeric {cik_numeric} has stored cik_padded "
                f"{cik_padded!r}, expected canonical {expected_padded!r}"
            )
            raise GateFailureError(message)
        expected_tie_break = selection_rank(cik_padded, PILOT_SELECTION_SEED)
        if row["entity_tie_break_sha256"] != expected_tie_break:
            message = (
                f"snapshot {snapshot_id!r} cik {cik_padded!r} has a stored entity_tie_break_sha256 "
                "that does not match SHA256(PILOT_SELECTION_SEED + '|' + cik_padded)"
            )
            raise GateFailureError(message)
        candidates.append(
            Candidate(
                cik_padded=cik_padded,
                filing_time_name=row["filing_time_name"],
                category=row["candidate_category"],
                primary_universe_eligible=bool(row["primary_universe_eligible"]),
                engineering_only_stress=bool(row["engineering_only_stress"]),
                size_stratum=row["size_stratum"],
                size_evidence_level=row["size_evidence_level"],
                industry_group=row["industry_family"],
                industry_evidence_level=row["industry_evidence_level"],
                industry_quota_eligible=bool(row["industry_quota_eligible"]),
                history_class=row["history_class"],
                history_evidence_level=row["history_evidence_level"],
                currently_inactive=bool(row["currently_inactive"]),
                control_kind=row["control_kind"],
                evidence_penalty=0,
            )
        )

    return FrozenEntityCandidateSet(
        snapshot_id=snapshot_id,
        candidate_snapshot_sha256=snapshot_row["candidate_snapshot_sha256"],
        entity_count=declared_entity_count,
        candidates=tuple(candidates),
    )


def _normalized_candidate_content_sha256(candidates: Sequence[Candidate]) -> str:
    """Row-order-independent content hash over selector-relevant candidate fields.

    ``filing_time_name`` (diagnostic only) is deliberately excluded: names never
    enter a hash or an ordering decision. :func:`hash_table` sorts rows internally,
    so candidate insertion order and database row-return order cannot change this.
    """
    columns = (
        "cik_padded",
        "category",
        "primary_universe_eligible",
        "engineering_only_stress",
        "size_stratum",
        "size_evidence_level",
        "industry_group",
        "industry_evidence_level",
        "industry_quota_eligible",
        "history_class",
        "history_evidence_level",
        "currently_inactive",
        "control_kind",
        "evidence_penalty",
    )
    rows = (
        {
            "cik_padded": c.cik_padded,
            "category": c.category,
            "primary_universe_eligible": c.primary_universe_eligible,
            "engineering_only_stress": c.engineering_only_stress,
            "size_stratum": c.size_stratum,
            "size_evidence_level": c.size_evidence_level,
            "industry_group": c.industry_group,
            "industry_evidence_level": c.industry_evidence_level,
            "industry_quota_eligible": c.industry_quota_eligible,
            "history_class": c.history_class,
            "history_evidence_level": c.history_evidence_level,
            "currently_inactive": c.currently_inactive,
            "control_kind": c.control_kind,
            "evidence_penalty": c.evidence_penalty,
        }
        for c in candidates
    )
    return hash_table("pilot_entity_selection_candidates", columns, rows).normalized_content_sha256


def build_entity_selection_run_identity(
    candidate_set: FrozenEntityCandidateSet,
    *,
    selection_seed: str = PILOT_SELECTION_SEED,
    selector_policy_version: str = PILOT_SELECTOR_POLICY_VERSION,
    quota_policy_version: str = PILOT_QUOTA_POLICY_VERSION,
    node_limit: int = DEFAULT_NODE_LIMIT,
) -> EntitySelectionRunIdentity:
    """Derive the deterministic input hash and run ID for one entity-selection run.

    Excludes every timestamp, event ID, path, SEC identity, secret, and name from
    both hashes; the frozen entity-level objective-term order is included so a
    change to it would change the identity. The same frozen snapshot and selector
    parameters always produce the same two hashes, regardless of candidate
    insertion order, database row-return order, which fresh SQLite database was
    used, or what audit timestamp/event ID a caller later supplies.

    Neither hash is the M2.3 manifest hash (Stage S6).
    """
    candidates_content_sha256 = _normalized_candidate_content_sha256(candidate_set.candidates)
    input_fields: dict[str, object] = {
        "schema": ENTITY_SELECTION_INPUT_SCHEMA_VERSION,
        "snapshot_id": candidate_set.snapshot_id,
        "candidate_snapshot_sha256": candidate_set.candidate_snapshot_sha256,
        "selection_seed": selection_seed,
        "selector_policy_version": selector_policy_version,
        "quota_policy_version": quota_policy_version,
        "node_limit": node_limit,
        "objective_term_order": _OBJECTIVE_TERM_ORDER,
        "candidates_content_sha256": candidates_content_sha256,
    }
    selection_input_sha256 = hash_table(
        "pilot_entity_selection_input", tuple(sorted(input_fields)), [input_fields]
    ).normalized_content_sha256

    run_identity_fields: dict[str, object] = {
        "schema": ENTITY_SELECTION_INPUT_SCHEMA_VERSION,
        "snapshot_id": candidate_set.snapshot_id,
        "selection_input_sha256": selection_input_sha256,
    }
    selection_run_id = hash_table(
        "pilot_entity_selection_run_identity",
        tuple(sorted(run_identity_fields)),
        [run_identity_fields],
    ).normalized_content_sha256

    return EntitySelectionRunIdentity(
        snapshot_id=candidate_set.snapshot_id,
        selection_seed=selection_seed,
        selector_policy_version=selector_policy_version,
        quota_policy_version=quota_policy_version,
        node_limit=node_limit,
        selection_input_sha256=selection_input_sha256,
        selection_run_id=selection_run_id,
    )


def _entity_quota_contributions(candidate: Candidate) -> tuple[tuple[str, str], ...]:
    """The exact (dimension, key) quota pairs one selected entity contributes to.

    Controls contribute only to their control kind and the two totals; they never
    contribute to an operating quota (size, industry, history, or the
    eventful/currently-inactive minimum).
    """
    if candidate.category == "control":
        return (
            ("control", candidate.control_kind or ""),
            ("summary", "total_controls"),
            ("summary", "total_entities"),
        )
    contributions = [
        ("summary", "operating_total"),
        ("size", candidate.size_stratum or ""),
        ("industry", candidate.industry_group or ""),
        ("history", candidate.history_class or ""),
    ]
    if candidate.history_class == "eventful" and candidate.currently_inactive:
        contributions.append(("history_status", "eventful_currently_inactive"))
    contributions.append(("summary", "total_entities"))
    return tuple(contributions)


def _quota_result_id(selection_run_id: str, dimension: str, key: str) -> str:
    payload = f"{selection_run_id}|{dimension}|{key}".encode()
    return hashlib.sha256(payload).hexdigest()


def _persist_entity_feasible_draft(
    c: sqlite3.Connection,
    *,
    selection_run_id: str,
    snapshot_id: str,
    selection_seed: str,
    selected_operating: tuple[Candidate, ...],
    selected_controls: tuple[Candidate, ...],
    quota_results: tuple[QuotaDiagnostic, ...],
    recorded_at_utc: str,
) -> None:
    """Persist exactly one entity-only running draft: selected rows, per-entity
    quota contributions, quota results, and quota-result members. Never inserts
    an accession, reserve, or manifest row.
    """
    selected_order = selected_operating + selected_controls
    order_index_by_cik = {
        candidate.cik_padded: index for index, candidate in enumerate(selected_order)
    }
    contributions_by_key: dict[tuple[str, str], list[Candidate]] = {}
    for order, candidate in enumerate(selected_order, start=1):
        entity_role = "operating" if candidate.category == "operating" else "control"
        c.execute(
            "INSERT INTO pilot_selected_entities "
            "(selection_run_id, snapshot_id, cik_numeric, selected_order, entity_hash_sha256, "
            "entity_role, candidate_category, size_stratum, industry_family, history_class, "
            "control_kind, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                selection_run_id,
                snapshot_id,
                int(candidate.cik_padded),
                order,
                selection_rank(candidate.cik_padded, selection_seed),
                entity_role,
                candidate.category,
                candidate.size_stratum,
                candidate.industry_group,
                candidate.history_class,
                candidate.control_kind,
                recorded_at_utc,
            ),
        )
        for dimension, key in _entity_quota_contributions(candidate):
            c.execute(
                "INSERT INTO pilot_selected_entity_quota_contributions "
                "(selection_run_id, snapshot_id, cik_numeric, quota_dimension, quota_key, "
                "recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    selection_run_id,
                    snapshot_id,
                    int(candidate.cik_padded),
                    dimension,
                    key,
                    recorded_at_utc,
                ),
            )
            contributions_by_key.setdefault((dimension, key), []).append(candidate)

    for diagnostic in quota_results:
        quota_result_id = _quota_result_id(selection_run_id, diagnostic.dimension, diagnostic.key)
        # Decision 017 section 2: excluded_pool_count is computed by the S4.1 solver
        # itself from the raw candidate pool (same-key candidates that failed
        # eligibility), not re-derived here from a coarse pool-size subtraction.
        c.execute(
            "INSERT INTO pilot_quota_results "
            "(quota_result_id, selection_run_id, snapshot_id, quota_dimension, quota_key, "
            "comparison_operator, required_count, achieved_count, eligible_pool_count, "
            "excluded_pool_count, evidence_state, quota_result, binding_constraint, "
            "recorded_at_utc) "
            # 'provisional' here means only the frozen classification (control-kind, for
            # a control quota; the resolved size/industry/history/etc. value otherwise)
            # is provisionally accepted -- not that every evidence dimension on the
            # contributing candidates is resolved (Decision 017 section 3).
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'provisional', ?, ?, ?)",
            (
                quota_result_id,
                selection_run_id,
                snapshot_id,
                diagnostic.dimension,
                diagnostic.key,
                diagnostic.comparison_operator,
                diagnostic.required_count,
                diagnostic.achieved_count,
                diagnostic.available_eligible_count,
                diagnostic.excluded_pool_count,
                diagnostic.status,
                1 if diagnostic.binding_constraint else 0,
                recorded_at_utc,
            ),
        )
        members = contributions_by_key.get((diagnostic.dimension, diagnostic.key), ())
        ordered_members = sorted(members, key=lambda cand: order_index_by_cik[cand.cik_padded])
        for member_order, member in enumerate(ordered_members, start=1):
            c.execute(
                "INSERT INTO pilot_quota_result_members "
                "(quota_result_id, selection_run_id, snapshot_id, member_order, member_kind, "
                "cik_numeric, recorded_at_utc) VALUES (?, ?, ?, ?, 'entity', ?, ?)",
                (
                    quota_result_id,
                    selection_run_id,
                    snapshot_id,
                    member_order,
                    int(member.cik_padded),
                    recorded_at_utc,
                ),
            )


def execute_and_persist_entity_selection(
    connection: sqlite3.Connection,
    snapshot_id: str,
    *,
    selection_seed: str = PILOT_SELECTION_SEED,
    selector_policy_version: str = PILOT_SELECTOR_POLICY_VERSION,
    quota_policy_version: str = PILOT_QUOTA_POLICY_VERSION,
    node_limit: int = DEFAULT_NODE_LIMIT,
    occurred_at_utc: str,
    event_id: str,
) -> PersistedEntitySelectionResult:
    """Run the S4.1 solver against one frozen snapshot and persist the result.

    Idempotent: if a run with the same content-derived ``selection_run_id``
    already exists, its stored ``selection_input_sha256`` is verified against the
    freshly derived one and the already-persisted result is returned (after full
    reconstruction, not a bare cache hit) rather than writing anything new. A
    same-ID run whose stored content differs is rejected, never overwritten.

    A matching existing run must also be in a state this call can safely stand in
    for: a complete entity-feasible ``running`` draft, or a terminal ``infeasible``/
    ``infeasible_or_unproven`` result, are reconstructed and returned normally. A
    ``planned`` run, an incomplete ``running`` run (no persisted 24-entity draft
    yet), or a ``failed`` run is a same-ID row this call cannot safely treat as
    equivalent to a fresh solve -- S5 retry orchestration is out of scope here, so
    rather than silently return an unusable empty result, this raises
    :class:`~disclosure_drift.errors.GateFailureError`.

    Everything -- run creation, the planned->running transition, the pure
    in-memory solve, and result persistence -- happens inside one transaction, so
    any exception leaves the database exactly as it was before this call: no
    partial run, event, selected, contribution, quota-result, or member row can
    survive.

    ``occurred_at_utc`` and ``event_id`` are audit metadata only; they never enter
    ``selection_input_sha256`` or ``selection_run_id``.
    """
    candidate_set = load_frozen_entity_candidates(connection, snapshot_id)
    identity = build_entity_selection_run_identity(
        candidate_set,
        selection_seed=selection_seed,
        selector_policy_version=selector_policy_version,
        quota_policy_version=quota_policy_version,
        node_limit=node_limit,
    )

    existing = connection.execute(
        "SELECT selection_input_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
        (identity.selection_run_id,),
    ).fetchone()
    if existing is not None:
        if existing["selection_input_sha256"] != identity.selection_input_sha256:
            message = (
                f"selection_run_id {identity.selection_run_id!r} already exists with a "
                "different stored selection_input_sha256; refusing to overwrite"
            )
            raise GateFailureError(message)
        reconstructed = reconstruct_persisted_entity_selection(
            connection, identity.selection_run_id
        )
        if reconstructed.run_state in ("infeasible", "infeasible_or_unproven") or (
            reconstructed.run_state == "running" and reconstructed.is_entity_feasible_draft
        ):
            return reconstructed
        # 'planned', an incomplete 'running' row (no persisted 24-entity draft yet),
        # or 'failed' -- none of these is a result this call can safely stand in for;
        # S5 retry orchestration (failed -> running) is explicitly out of scope here,
        # so this fails closed rather than silently returning an unusable result.
        message = (
            f"selection_run_id {identity.selection_run_id!r} already exists in "
            f"unusable state {reconstructed.run_state!r} (entity-feasible draft: "
            f"{reconstructed.is_entity_feasible_draft}); refusing to reconstruct or retry it here"
        )
        raise GateFailureError(message)

    result = solve_entity_selection(
        candidate_set.candidates, selection_seed=selection_seed, node_limit=node_limit
    )

    with transaction(connection) as c:
        c.execute(
            "INSERT INTO pilot_selection_runs "
            "(selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
            "quota_policy_version, search_node_limit, run_state, selection_input_sha256, "
            "started_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, 'planned', ?, ?)",
            (
                identity.selection_run_id,
                snapshot_id,
                selection_seed,
                selector_policy_version,
                quota_policy_version,
                node_limit,
                identity.selection_input_sha256,
                occurred_at_utc,
            ),
        )
        c.execute(
            "INSERT INTO pilot_selection_run_events "
            "(event_id, selection_run_id, snapshot_id, from_state, to_state, attempt_number, "
            "occurred_at_utc) VALUES (?, ?, ?, 'planned', 'running', 1, ?)",
            (event_id, identity.selection_run_id, snapshot_id, occurred_at_utc),
        )
        c.execute(
            "UPDATE pilot_selection_runs SET run_state = 'running' WHERE selection_run_id = ?",
            (identity.selection_run_id,),
        )

        if result.status == "feasible":
            _persist_entity_feasible_draft(
                c,
                selection_run_id=identity.selection_run_id,
                snapshot_id=snapshot_id,
                selection_seed=selection_seed,
                selected_operating=result.selected_operating,
                selected_controls=result.selected_controls,
                quota_results=result.quota_results,
                recorded_at_utc=occurred_at_utc,
            )
            c.execute(
                "UPDATE pilot_selection_runs SET selected_entity_count = ?, "
                "selected_accession_count = 0, expanded_node_count = ?, node_limit_exhausted = 0 "
                "WHERE selection_run_id = ?",
                (
                    len(result.selected_operating) + len(result.selected_controls),
                    result.expanded_node_count,
                    identity.selection_run_id,
                ),
            )
        else:
            terminal_state = result.status
            reason_code = (
                _PILOT_SELECTION_INFEASIBLE
                if terminal_state == "infeasible"
                else _PILOT_SELECTION_INFEASIBLE_OR_UNPROVEN
            )
            # No pilot_selection_run_events row is recorded for this transition:
            # UNIQUE (selection_run_id, attempt_number) permits exactly one event
            # per attempt, and attempt 1's event already recorded planned->running
            # above. failure_reason_code and finished_at_utc on the run itself
            # carry the audit trail for why the run ended non-feasible; only a
            # failed->running retry requires a matching event (see the schema's
            # pilot_selection_run_retry_requires_event trigger).
            c.execute(
                "UPDATE pilot_selection_runs SET run_state = ?, selected_entity_count = 0, "
                "selected_accession_count = 0, expanded_node_count = ?, node_limit_exhausted = ?, "
                "failure_reason_code = ?, finished_at_utc = ? WHERE selection_run_id = ?",
                (
                    terminal_state,
                    result.expanded_node_count,
                    1 if result.node_limit_exhausted else 0,
                    reason_code,
                    occurred_at_utc,
                    identity.selection_run_id,
                ),
            )

    return reconstruct_persisted_entity_selection(connection, identity.selection_run_id)


def reconstruct_persisted_entity_selection(
    connection: sqlite3.Connection, selection_run_id: str
) -> PersistedEntitySelectionResult:
    """Reconstruct a persisted entity-selection outcome, failing closed on any
    mismatch between the declared and actual persisted content.

    A ``running`` run with ``selected_entity_count == 24`` is an entity-feasible
    running draft; every other state (``planned``, ``infeasible``,
    ``infeasible_or_unproven``, ``failed``, or a ``running`` run with no result
    yet) reconstructs with empty selected/quota-result tuples -- never a partial
    approved selection.
    """
    run_row = connection.execute(
        "SELECT selection_run_id, snapshot_id, selection_seed, selector_policy_version, "
        "quota_policy_version, search_node_limit, run_state, expanded_node_count, "
        "node_limit_exhausted, selected_entity_count, selected_accession_count, "
        "selection_input_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
        (selection_run_id,),
    ).fetchone()
    if run_row is None:
        message = f"no pilot selection run exists for selection_run_id {selection_run_id!r}"
        raise GateFailureError(message)

    snapshot_id = run_row["snapshot_id"]
    is_entity_feasible_draft = (
        run_row["run_state"] == "running" and run_row["selected_entity_count"] == 24
    )

    if not is_entity_feasible_draft:
        return PersistedEntitySelectionResult(
            selection_run_id=selection_run_id,
            snapshot_id=snapshot_id,
            run_state=run_row["run_state"],
            is_entity_feasible_draft=False,
            selection_seed=run_row["selection_seed"],
            selector_policy_version=run_row["selector_policy_version"],
            quota_policy_version=run_row["quota_policy_version"],
            node_limit=run_row["search_node_limit"],
            expanded_node_count=run_row["expanded_node_count"],
            node_limit_exhausted=bool(run_row["node_limit_exhausted"]),
            selection_input_sha256=run_row["selection_input_sha256"],
            selected_entity_count=run_row["selected_entity_count"],
            selected_accession_count=run_row["selected_accession_count"],
            selected_operating=(),
            selected_controls=(),
            quota_results=(),
        )

    selected_rows = connection.execute(
        "SELECT cik_numeric, selected_order, entity_hash_sha256, entity_role, "
        "candidate_category, size_stratum, industry_family, history_class, control_kind "
        "FROM pilot_selected_entities WHERE selection_run_id = ? AND snapshot_id = ? "
        "ORDER BY selected_order",
        (selection_run_id, snapshot_id),
    ).fetchall()
    if len(selected_rows) != run_row["selected_entity_count"]:
        message = (
            f"selection_run_id {selection_run_id!r} declares selected_entity_count "
            f"{run_row['selected_entity_count']}, but {len(selected_rows)} "
            "pilot_selected_entities rows exist"
        )
        raise GateFailureError(message)
    actual_orders = [row["selected_order"] for row in selected_rows]
    if actual_orders != list(range(1, len(selected_rows) + 1)):
        message = (
            f"selection_run_id {selection_run_id!r} selected_order values are not "
            f"contiguous from 1: {actual_orders!r}"
        )
        raise GateFailureError(message)

    selection_seed = run_row["selection_seed"]
    selected_operating: list[Candidate] = []
    selected_controls: list[Candidate] = []
    for row in selected_rows:
        cik_numeric = row["cik_numeric"]
        candidate_row = connection.execute(
            f"SELECT {', '.join(_CANDIDATE_ENTITY_COLUMNS)} "  # noqa: S608 -- fixed allowlist
            "FROM pilot_candidate_entities WHERE snapshot_id = ? AND cik_numeric = ?",
            (snapshot_id, cik_numeric),
        ).fetchone()
        if candidate_row is None:
            message = (
                f"selection_run_id {selection_run_id!r} selected cik_numeric {cik_numeric} "
                f"has no matching pilot_candidate_entities row in snapshot {snapshot_id!r}"
            )
            raise GateFailureError(message)
        if (
            candidate_row["candidate_category"] != row["candidate_category"]
            or candidate_row["size_stratum"] != row["size_stratum"]
            or candidate_row["industry_family"] != row["industry_family"]
            or candidate_row["history_class"] != row["history_class"]
            or candidate_row["control_kind"] != row["control_kind"]
        ):
            message = (
                f"selection_run_id {selection_run_id!r} cik_numeric {cik_numeric} classification "
                "in pilot_selected_entities does not match the frozen candidate snapshot"
            )
            raise GateFailureError(message)
        cik_padded = candidate_row["cik_padded"]
        expected_hash = selection_rank(cik_padded, selection_seed)
        if row["entity_hash_sha256"] != expected_hash:
            message = (
                f"selection_run_id {selection_run_id!r} cik {cik_padded!r} has a stored "
                "entity_hash_sha256 that does not match the S4.1 rank formula under its own "
                "recorded selection_seed"
            )
            raise GateFailureError(message)
        candidate = Candidate(
            cik_padded=cik_padded,
            filing_time_name=candidate_row["filing_time_name"],
            category=candidate_row["candidate_category"],
            primary_universe_eligible=bool(candidate_row["primary_universe_eligible"]),
            engineering_only_stress=bool(candidate_row["engineering_only_stress"]),
            size_stratum=candidate_row["size_stratum"],
            size_evidence_level=candidate_row["size_evidence_level"],
            industry_group=candidate_row["industry_family"],
            industry_evidence_level=candidate_row["industry_evidence_level"],
            industry_quota_eligible=bool(candidate_row["industry_quota_eligible"]),
            history_class=candidate_row["history_class"],
            history_evidence_level=candidate_row["history_evidence_level"],
            currently_inactive=bool(candidate_row["currently_inactive"]),
            control_kind=candidate_row["control_kind"],
            evidence_penalty=0,
        )
        if row["entity_role"] == "operating":
            selected_operating.append(candidate)
        else:
            selected_controls.append(candidate)

    contribution_rows = connection.execute(
        "SELECT cik_numeric, quota_dimension, quota_key FROM "
        "pilot_selected_entity_quota_contributions WHERE selection_run_id = ? AND snapshot_id = ? "
        "ORDER BY cik_numeric, quota_dimension, quota_key",
        (selection_run_id, snapshot_id),
    ).fetchall()
    contribution_counts: dict[tuple[str, str], int] = {}
    for row in contribution_rows:
        key = (row["quota_dimension"], row["quota_key"])
        contribution_counts[key] = contribution_counts.get(key, 0) + 1

    quota_rows = connection.execute(
        "SELECT quota_result_id, quota_dimension, quota_key, comparison_operator, "
        "required_count, achieved_count, eligible_pool_count, excluded_pool_count, "
        "binding_constraint, quota_result "
        "FROM pilot_quota_results WHERE selection_run_id = ? AND snapshot_id = ? "
        "ORDER BY quota_dimension, quota_key",
        (selection_run_id, snapshot_id),
    ).fetchall()
    quota_results: list[QuotaDiagnostic] = []
    for row in quota_rows:
        key = (row["quota_dimension"], row["quota_key"])
        contribution_count = contribution_counts.get(key, 0)
        if contribution_count != row["achieved_count"]:
            message = (
                f"selection_run_id {selection_run_id!r} quota {key!r} declares achieved_count "
                f"{row['achieved_count']}, but {contribution_count} matching "
                "pilot_selected_entity_quota_contributions rows exist"
            )
            raise GateFailureError(message)
        member_count = connection.execute(
            "SELECT COUNT(*) FROM pilot_quota_result_members WHERE quota_result_id = ?",
            (row["quota_result_id"],),
        ).fetchone()[0]
        if member_count != row["achieved_count"]:
            message = (
                f"selection_run_id {selection_run_id!r} quota {key!r} declares achieved_count "
                f"{row['achieved_count']}, but {member_count} pilot_quota_result_members rows "
                "exist"
            )
            raise GateFailureError(message)
        quota_results.append(
            QuotaDiagnostic(
                dimension=row["quota_dimension"],
                key=row["quota_key"],
                comparison_operator=row["comparison_operator"],
                required_count=row["required_count"],
                available_eligible_count=row["eligible_pool_count"],
                achieved_count=row["achieved_count"],
                status=row["quota_result"],
                binding_constraint=bool(row["binding_constraint"]),
                excluded_pool_count=row["excluded_pool_count"],
            )
        )

    return PersistedEntitySelectionResult(
        selection_run_id=selection_run_id,
        snapshot_id=snapshot_id,
        run_state=run_row["run_state"],
        is_entity_feasible_draft=True,
        selection_seed=selection_seed,
        selector_policy_version=run_row["selector_policy_version"],
        quota_policy_version=run_row["quota_policy_version"],
        node_limit=run_row["search_node_limit"],
        expanded_node_count=run_row["expanded_node_count"],
        node_limit_exhausted=bool(run_row["node_limit_exhausted"]),
        selection_input_sha256=run_row["selection_input_sha256"],
        selected_entity_count=run_row["selected_entity_count"],
        selected_accession_count=run_row["selected_accession_count"],
        selected_operating=tuple(selected_operating),
        selected_controls=tuple(selected_controls),
        quota_results=tuple(quota_results),
    )
