"""Read-only recovery-state inspection (`Docs/m3/templates/interrupted_run_recovery.md`).

After an interrupted acquisition, something must answer *is it safe to resume* — without touching
anything. That is this module. It reports the receipt chain, the interruption point, the database,
raw-store, and partial-file state, the consumed physical attempts, and one of `SAFE`, `UNSAFE`, or
`UNDETERMINED`.

**It never repairs.** The template is explicit that inspection "never adopts, quarantines,
rebuilds, reconciles, resumes, or calls ``observation_catalog.reconcile()``", and the master
plan's deliverable is the inspection surface *and proof that it cannot invoke a writer*. Three
independent things supply that proof:

1. **Nothing writable is imported.** `reconcile`, `record_recovery_events`,
   `rebuild_audit_projection`, `ObservationRecorder`, `CatalogWriter`, and `RawStore` are absent
   from this module's namespace, so no accidental call is reachable — a test asserts it.
2. **The connection refuses writes.** :func:`read_only_catalog` opens the catalog through the
   non-writer helper *and* sets ``PRAGMA query_only``, so a write fails closed at SQLite rather than
   relying on the convention that all writes route through ``CatalogWriter``. A read-only connection
   also takes no writer lease, so inspecting never contends with, or masquerades as, a writer.
3. **Everything is compared, nothing is acted on.** Orphans, partial files, and projection drift are
   counted and reported; the deterministic corrective action is *named* for a separately authorized
   M3.2 repair to perform.

**`UNDETERMINED` is a stop condition, not a judgement call.** The governing documents name exactly
two triggers — a receipt chain that does not resolve, and a committed row whose object is missing —
and deliberately give no finer per-condition rule. The classification here implements those two
literally: an unmet condition whose cause is known is `UNSAFE`; an unmet condition that leaves it
unknowable whether a write committed is `UNDETERMINED`. Nothing stricter is synthesized, because
inventing a rule the governance does not state is exactly how a stop condition gets quietly
downgraded.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.receipt import ReceiptValidationError, inspect_receipt
from disclosure_drift.m3.request_plan import RequestPlan, derive_a_reachable
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.observation_catalog import load_observations, validate_audit_projection
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import read_only_connection
from disclosure_drift.storage.sqlite import integrity_report

__all__ = [
    "RECOVERY_DETERMINATIONS",
    "ConditionResult",
    "RecoveryInspectionError",
    "RecoveryState",
    "inspect_receiptless_first_invocation",
    "inspect_recovery_state",
    "read_only_catalog",
]

RECOVERY_DETERMINATIONS: Final = ("SAFE", "UNDETERMINED", "UNSAFE")

#: The audit projection this inspection validates against SQLite.
_PROJECTION_FILENAME: Final = "census_source_observations.jsonl"

#: The suffix a not-yet-promoted transfer carries. A `.part` file existing is ordinary; a committed
#: row *pointing at* one would mean a partial was treated as complete, which is the real condition.
_PART_SUFFIX: Final = ".part"

#: The suffix of a raw object's durable recovery-intent manifest. Read here — never written — so the
#: forensic receiptless mode can derive the pre-ledger consumed baseline from durable evidence.
_LINEAGE_SUFFIX: Final = ".lineage.json"

_MET: Final = "MET"
_NOT_MET: Final = "NOT MET"
_NOT_APPLICABLE: Final = "N/A"

#: Selection run states that mean a selection was in flight when the run stopped.
_IN_FLIGHT_SELECTION_STATES: Final = ("planned", "running")


class RecoveryInspectionError(DisclosureDriftError):
    """Raised when inspection cannot even begin — a missing catalog or an unreadable head receipt.

    Distinct from `UNDETERMINED`. `UNDETERMINED` is a *finding* about evidence that exists but does
    not settle whether a write committed; this is a caller error, and reporting it as a finding
    would let a mistyped path read as a genuine recovery ambiguity.
    """


def _as_count(value: object) -> int:
    """Narrow a receipt field the receipt schema has already validated as a count."""
    if isinstance(value, bool) or not isinstance(value, int):
        message = f"expected an integer count, found {type(value).__name__}"
        raise RecoveryInspectionError(message)
    return value


@contextmanager
def read_only_catalog(catalog_path: Path) -> Iterator[sqlite3.Connection]:
    """Open the catalog so that a write is impossible, not merely unintended.

    ``read_only_connection`` takes no writer lease, and ``PRAGMA query_only`` makes SQLite itself
    reject any statement that would mutate the database. That upgrade matters: without it,
    "read-only" rests on the convention that writes route through ``CatalogWriter``, and a
    convention is not the proof the contract asks for.
    """
    with read_only_connection(catalog_path) as connection:
        connection.execute("PRAGMA query_only = TRUE")
        yield connection


@dataclass(frozen=True, slots=True)
class ConditionResult:
    """One row of the §8 safe-resume determination table."""

    number: str
    condition: str
    status: str
    detail: str

    @property
    def blocks(self) -> bool:
        """Whether this condition prevents a `SAFE` determination."""
        return self.status == _NOT_MET

    def as_record(self) -> dict[str, object]:
        """Deterministic mapping for the evidence record."""
        return {
            "number": self.number,
            "condition": self.condition,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True, slots=True)
class RecoveryState:
    """The complete read-only recovery finding."""

    determination: str
    basis: str
    required_action: str
    conditions: tuple[ConditionResult, ...]
    receipt_chain: tuple[str, ...]
    interruption_state: str | None
    consumed_physical_attempts: int
    committed_observation_count: int
    orphan_object_count: int
    rows_without_object_count: int
    partial_file_count: int

    @property
    def resume_authorized(self) -> bool:
        """Only `SAFE` authorizes a resume, and only under a separate M3.2 contract."""
        return self.determination == "SAFE"

    def as_record(self) -> Mapping[str, object]:
        """Non-secret evidence mapping. Carries counts, states, and identifiers only.

        No absolute path appears here: the template forbids recording one, and an evidence record is
        shared. Paths reaching this record are relative to the data root or omitted entirely.
        """
        return {
            "determination": self.determination,
            "basis": self.basis,
            "required_action": self.required_action,
            "receipt_chain": list(self.receipt_chain),
            "interruption_state": self.interruption_state,
            "consumed_physical_attempts": self.consumed_physical_attempts,
            "committed_observation_count": self.committed_observation_count,
            "orphan_object_count": self.orphan_object_count,
            "rows_without_object_count": self.rows_without_object_count,
            "partial_file_count": self.partial_file_count,
            "conditions": [condition.as_record() for condition in self.conditions],
        }


# --------------------------------------------------------------------------- #
# Receipt chain
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _ChainWalk:
    """The resolved receipt chain, and whether it reached the first attempt."""

    receipt_ids: tuple[str, ...]
    consumed_physical_attempts: int
    interruption_state: str | None
    resolved: bool
    detail: str
    request_plan_sha256: str | None = None


def _walk_receipt_chain(head_path: Path) -> _ChainWalk:
    """Follow `recovery_predecessor_receipt_id` back toward the first attempt.

    A missing or unreadable predecessor stops the walk and marks the chain unresolved. The missing
    receipt is *never* reconstructed: the template says so explicitly, and a reconstructed receipt
    would assert a consumed count nobody recorded.
    """
    receipts_dir = head_path.parent
    seen: list[str] = []
    consumed = 0
    interruption_state: str | None = None
    recorded_plan_sha256: str | None = None
    current = head_path
    visited: set[str] = set()

    while True:
        try:
            document = inspect_receipt(current)
        except (OSError, ReceiptValidationError) as exc:
            return _ChainWalk(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed,
                interruption_state=interruption_state,
                resolved=False,
                detail=f"a receipt in the chain is missing or unreadable: {exc}",
                request_plan_sha256=recorded_plan_sha256,
            )

        if recorded_plan_sha256 is None:
            recorded = document.get("request_plan_sha256")
            recorded_plan_sha256 = None if recorded is None else str(recorded)

        receipt_id = str(document["receipt_id"])
        if receipt_id in visited:
            return _ChainWalk(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed,
                interruption_state=interruption_state,
                resolved=False,
                detail="the receipt chain loops back on itself and cannot reach a first attempt",
                request_plan_sha256=recorded_plan_sha256,
            )
        visited.add(receipt_id)
        seen.append(receipt_id)
        consumed += _as_count(document["actual_physical_attempt_count"])
        if interruption_state is None:
            state = document.get("interruption_state")
            interruption_state = None if state is None else str(state)

        predecessor = document.get("recovery_predecessor_receipt_id")
        if predecessor is None:
            return _ChainWalk(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed,
                interruption_state=interruption_state,
                resolved=True,
                detail="the chain resolves to a first attempt",
                request_plan_sha256=recorded_plan_sha256,
            )
        current = receipts_dir / f"receipt-{predecessor}.json"


# --------------------------------------------------------------------------- #
# Filesystem and catalog observation
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _StoreState:
    """What the raw store and catalog agree, and disagree, about."""

    committed_observation_count: int
    committed_per_route: Mapping[str, int]
    rows_without_object: tuple[str, ...]
    rows_pointing_at_partials: tuple[str, ...]
    orphan_object_count: int
    partial_file_count: int


def _inspect_store(connection: sqlite3.Connection, tree: DataTree) -> _StoreState:
    """Compare committed rows against stored objects, writing nothing.

    Both directions are counted, because they mean different things. A row without its object is the
    dangerous direction and a stop condition; an object without its row is an orphan, which a
    separately authorized repair can adopt or quarantine.
    """
    observations = load_observations(connection)
    committed_paths: set[str] = set()
    committed_per_route: dict[str, int] = {}
    rows_without_object: list[str] = []
    rows_pointing_at_partials: list[str] = []

    for item in observations:
        committed_per_route[item.source_id] = committed_per_route.get(item.source_id, 0) + 1
        relative = item.relative_storage_path
        if relative is None:
            # A row may lawfully reference no stored object: a `304` reuse observation records
            # that the preserved snapshot was reused and creates nothing new. Treating that as a
            # row without its object would fire the stop condition on ordinary revalidation.
            continue
        committed_paths.add(relative)
        if relative.endswith(_PART_SUFFIX):
            rows_pointing_at_partials.append(item.observation_id)
        if not (tree.data_root / relative).is_file():
            rows_without_object.append(item.observation_id)

    partial_files = 0
    orphans = 0
    raw_root = tree.data_root / "raw"
    if raw_root.is_dir():
        for path in raw_root.rglob("*"):
            if not path.is_file():
                continue
            if path.name.endswith(_PART_SUFFIX):
                partial_files += 1
                continue
            if path.name.endswith(".lineage.json"):
                continue
            if _is_under(path, tree.quarantine):
                continue
            relative = str(path.relative_to(tree.data_root))
            if relative not in committed_paths:
                orphans += 1

    return _StoreState(
        committed_observation_count=len(observations),
        committed_per_route=committed_per_route,
        rows_without_object=tuple(rows_without_object),
        rows_pointing_at_partials=tuple(rows_pointing_at_partials),
        orphan_object_count=orphans,
        partial_file_count=partial_files,
    )


def _is_under(path: Path, ancestor: Path) -> bool:
    """Whether ``path`` lies within ``ancestor``, without resolving symlinks."""
    return ancestor in path.parents


def _unresolved_recovery_states(connection: sqlite3.Connection) -> int:
    """Recovery states still marked ``blocked``, i.e. awaiting a ruling."""
    row = connection.execute(
        "SELECT COUNT(*) FROM census_recovery_states WHERE resolution_state = 'blocked'"
    ).fetchone()
    return int(row[0])


def _in_flight_selection_runs(connection: sqlite3.Connection) -> int:
    """Selection runs that had not reached a terminal state."""
    placeholders = ",".join("?" for _ in _IN_FLIGHT_SELECTION_STATES)
    row = connection.execute(
        f"SELECT COUNT(*) FROM pilot_selection_runs WHERE run_state IN ({placeholders})",  # noqa: S608
        _IN_FLIGHT_SELECTION_STATES,
    ).fetchone()
    return int(row[0])


# --------------------------------------------------------------------------- #
# The inspection
# --------------------------------------------------------------------------- #
def inspect_recovery_state(
    *,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    data_root: Path,
) -> RecoveryState:
    """Determine whether an interrupted run may safely resume. Writes nothing.

    Args:
        plan: the approved request plan the interrupted run was executing.
        receipt_chain_head: path to the most recent receipt; predecessors resolve beside it.
        catalog_path: the SQLite catalog to inspect read-only.
        data_root: the data root whose raw store is inspected.

    Raises:
        RecoveryInspectionError: the catalog or head receipt is absent, so inspection cannot begin.
    """
    if not Path(catalog_path).is_file():
        message = (
            f"catalog {Path(catalog_path).name!r} does not exist; recovery inspection needs the "
            f"catalog the interrupted run was writing to"
        )
        raise RecoveryInspectionError(message)
    if not Path(receipt_chain_head).is_file():
        message = (
            f"head receipt {Path(receipt_chain_head).name!r} does not exist; the chain has no "
            f"starting point to walk back from"
        )
        raise RecoveryInspectionError(message)

    tree = DataTree.from_root(data_root)
    walk = _walk_receipt_chain(Path(receipt_chain_head))

    with read_only_catalog(Path(catalog_path)) as connection:
        integrity = integrity_report(connection)
        store = _inspect_store(connection, tree)
        projection = validate_audit_projection(connection, tree.audit / _PROJECTION_FILENAME)
        unresolved_states = _unresolved_recovery_states(connection)
        selection_runs = _in_flight_selection_runs(connection)

    headroom_fits, headroom_detail = _headroom(plan, walk, store)

    conditions = (
        ConditionResult(
            "8.1",
            "The receipt chain resolves completely",
            _MET if walk.resolved else _NOT_MET,
            walk.detail,
        ),
        ConditionResult(
            "8.2",
            "The interruption state is established, not guessed",
            _MET if walk.interruption_state is not None else _NOT_MET,
            (
                f"recorded as {walk.interruption_state!r} by the receipt schema"
                if walk.interruption_state is not None
                else "no receipt on the chain records an interruption state, so the interruption "
                "point is not established and would have to be guessed"
            ),
        ),
        ConditionResult(
            "8.3",
            "The catalog passes quick, integrity, and foreign-key checks",
            _MET if integrity.passed else _NOT_MET,
            (
                f"quick_check={integrity.quick_check}, "
                f"integrity_check={integrity.integrity_check}, "
                f"foreign_key_violations={integrity.foreign_key_violations}"
            ),
        ),
        ConditionResult(
            "8.4",
            "No row exists without its object",
            _MET if not store.rows_without_object else _NOT_MET,
            f"{len(store.rows_without_object)} committed row(s) have no stored object",
        ),
        ConditionResult(
            "8.5",
            "Every orphan is adopted or quarantined",
            _MET if store.orphan_object_count == 0 else _NOT_MET,
            f"{store.orphan_object_count} object(s) on disk have no committed row",
        ),
        ConditionResult(
            "8.6",
            "No `.part` file was treated as complete",
            _MET if not store.rows_pointing_at_partials else _NOT_MET,
            (
                f"{len(store.rows_pointing_at_partials)} committed row(s) point at a partial file; "
                f"{store.partial_file_count} partial file(s) are present and unpromoted, which is "
                f"ordinary"
            ),
        ),
        ConditionResult(
            "8.7",
            "The audit projection is consistent or has been rebuilt from SQLite",
            _MET if projection.is_valid else _NOT_MET,
            (
                "the projection agrees with SQLite"
                if projection.is_valid
                else "the projection disagrees with SQLite and must be rebuilt from it"
            ),
        ),
        ConditionResult(
            "8.8",
            "The remainder fits inside the remaining ceiling headroom",
            _MET if headroom_fits else _NOT_MET,
            headroom_detail,
        ),
        ConditionResult(
            "8.9",
            "No unresolved schema-drift incident is open",
            _MET if unresolved_states == 0 else _NOT_MET,
            f"{unresolved_states} recovery state(s) remain blocked and await a ruling",
        ),
        ConditionResult(
            "8.10",
            "The plan hash is unchanged",
            _plan_hash_status(plan, walk),
            _plan_hash_detail(plan, walk),
        ),
        ConditionResult(
            "8.11",
            "For a selection: the accepted lifecycle guards leave exactly one lawful next state",
            _NOT_APPLICABLE if selection_runs == 0 else _NOT_MET,
            (
                "no selection run was in flight"
                if selection_runs == 0
                else f"{selection_runs} selection run(s) were in flight; Milestone 3.2 owns the "
                f"selection lifecycle and this phase does not rule on it"
            ),
        ),
    )

    determination, basis, action = _determine(conditions, walk=walk, store=store)
    return RecoveryState(
        determination=determination,
        basis=basis,
        required_action=action,
        conditions=conditions,
        receipt_chain=walk.receipt_ids,
        interruption_state=walk.interruption_state,
        consumed_physical_attempts=walk.consumed_physical_attempts,
        committed_observation_count=store.committed_observation_count,
        orphan_object_count=store.orphan_object_count,
        rows_without_object_count=len(store.rows_without_object),
        partial_file_count=store.partial_file_count,
    )


def _headroom(plan: RequestPlan, walk: _ChainWalk, store: _StoreState) -> tuple[bool, str]:
    """Whether the remaining work fits under the ceiling the run has already partly consumed.

    The remainder is bounded **per route**, with each route's own ``A_reachable`` — the same
    decomposition the ceiling itself was built from. That correspondence is what makes the check
    meaningful: a run that has completed nothing needs exactly the whole ceiling and fits, and every
    completed request frees precisely the headroom it was budgeted. Bounding the remainder with a
    single worst-case multiplier instead would make the check unsatisfiable for any plan containing
    a route below that maximum, which would refuse every resume rather than judge it.

    Completion is counted from committed catalog rows per route, not from the receipt chain, because
    the catalog is the authority on what actually persisted. A route with more committed rows than
    planned contributes zero remaining rather than a negative, so extra rows can never manufacture
    headroom.
    """
    ceiling = plan.hard_request_ceiling
    remaining_headroom = ceiling - walk.consumed_physical_attempts

    remaining_logical = 0
    worst_case_remaining = 0
    for route in plan.routes:
        completed = store.committed_per_route.get(route.source_id, 0)
        outstanding = max(0, route.planned_unique_logical_requests - completed)
        remaining_logical += outstanding
        worst_case_remaining += outstanding * derive_a_reachable(SOURCES[route.source_id])

    fits = worst_case_remaining <= remaining_headroom
    detail = (
        f"{remaining_logical} logical request(s) remain; worst case {worst_case_remaining} "
        f"attempt(s) against {remaining_headroom} of {ceiling} remaining headroom"
    )
    return fits, detail


def _plan_hash_status(plan: RequestPlan, walk: _ChainWalk) -> str:
    """Whether the supplied plan is the one the interrupted run was executing.

    Resuming against a *different* plan than the one the run consumed would carry a consumed count
    forward against a budget nobody approved, so a mismatch is not met. A chain that records no plan
    hash also fails: the condition asks whether the hash is unchanged, and an absent hash cannot
    establish that it is.
    """
    if walk.request_plan_sha256 is None:
        return _NOT_MET
    return _MET if walk.request_plan_sha256 == plan.request_plan_sha256 else _NOT_MET


def _plan_hash_detail(plan: RequestPlan, walk: _ChainWalk) -> str:
    """State what was compared, without assuming it matched."""
    if walk.request_plan_sha256 is None:
        return (
            "no receipt on the chain records a request_plan_sha256, so it cannot be established "
            "that the plan is unchanged"
        )
    if walk.request_plan_sha256 == plan.request_plan_sha256:
        return f"the chain and the supplied plan agree on {plan.request_plan_sha256}"
    return (
        f"the chain recorded plan {walk.request_plan_sha256} but the supplied plan is "
        f"{plan.request_plan_sha256}"
    )


def _determine(
    conditions: tuple[ConditionResult, ...],
    *,
    walk: _ChainWalk,
    store: _StoreState,
) -> tuple[str, str, str]:
    """Classify the conditions into `SAFE`, `UNSAFE`, or `UNDETERMINED`.

    The split follows the governing prose exactly. `UNDETERMINED` is reserved for the two cases the
    documents name, both of which leave it unknowable whether a write committed:

    - the receipt chain does not resolve, so the consumed count and interruption point are unknown;
    - a committed row has no object, so it cannot be established what was actually persisted.

    Every other unmet condition has a known cause and is `UNSAFE`, which a separately authorized
    M3.2 repair may correct before inspection runs again. No finer rule is invented here.
    """
    if not walk.resolved:
        return (
            "UNDETERMINED",
            f"the receipt chain does not resolve to a first attempt: {walk.detail}",
            "Stop. Do not resume. Refer for an owner ruling; never reconstruct a missing receipt.",
        )
    if store.rows_without_object:
        return (
            "UNDETERMINED",
            (
                f"{len(store.rows_without_object)} committed row(s) have no stored object, so it "
                f"cannot be established what was persisted"
            ),
            "Stop. Do not resume. Refer for an owner ruling.",
        )

    blocking = [condition for condition in conditions if condition.blocks]
    if blocking:
        listed = "; ".join(f"{item.number} {item.condition} ({item.detail})" for item in blocking)
        return (
            "UNSAFE",
            f"{len(blocking)} condition(s) are not met with a known cause: {listed}",
            (
                "Stop. A separately authorized Milestone 3.2 repair may apply the deterministic "
                "action, after which this read-only inspection must run again and return SAFE. "
                "Inspection itself never repairs."
            ),
        )
    return (
        "SAFE",
        "every safe-resume condition is met",
        (
            "Resume is authorized only under a separate Milestone 3.2 contract, and only after the "
            "duplicate-prevention proof is complete, carrying the consumed count forward under the "
            "same approved ceiling."
        ),
    )


# --------------------------------------------------------------------------- #
# Explicit receiptless first-invocation inspection (Decision 051 §7.4, §8; §5A)
# --------------------------------------------------------------------------- #
def _registered_run_or_refuse(connection: sqlite3.Connection, census_run_id: str) -> None:
    """Refuse unless ``census_run_id`` resolves to exactly one registered acquisition job.

    Receiptless mode is bound to the exact interrupted run identity (Decision 051 §7.4). A run id
    that does not resolve is a caller error, reported the same way a missing head receipt is, so a
    mistyped id can never read as a genuine recovery finding.
    """
    row = connection.execute(
        "SELECT 1 FROM ops_ingestion_jobs WHERE job_id = ?",
        (census_run_id,),
    ).fetchone()
    if row is None:
        message = (
            f"census run {census_run_id!r} does not resolve to a registered acquisition run; "
            "receiptless inspection is bound to the exact interrupted run identity and never "
            "invents one"
        )
        raise RecoveryInspectionError(message)


def _ledger_reservation_count(connection: sqlite3.Connection, census_run_id: str) -> int:
    """Count the durable pre-send reservations this run committed (Decision 051 §6).

    Every committed ``started`` row counts as one consumed physical attempt, including a row
    stranded before its transport call; a terminal state never erases the consumption.
    """
    row = connection.execute(
        "SELECT COUNT(*) FROM ops_retrieval_attempts WHERE job_id = ?",
        (census_run_id,),
    ).fetchone()
    return int(row[0])


def _raw_lineage_attempts(tree: DataTree) -> int:
    """Sum the physical-attempt counts recorded in the raw store's durable lineage manifests.

    This is the pre-ledger, incident-specific consumed evidence Decision 051 §5 accepts for the
    interrupted initial T5 invocation, whose lineage durably records ``attempts = 1``. Per data
    dictionary §5A this incident evidence is deliberately **not** the future primary attempt
    ledger — ``ops_retrieval_attempts`` is — so it is read only in this forensic receiptless mode,
    and it is disjoint from the ledger for a genuine first invocation, which predates the runtime
    writer. A manifest that cannot be read, or whose ``attempts`` is not a non-negative integer,
    contributes nothing rather than an inferred value.
    """
    total = 0
    raw_root = tree.data_root / "raw"
    if not raw_root.is_dir():
        return 0
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or not path.name.endswith(_LINEAGE_SUFFIX):
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(document, dict):
            continue
        attempts = document.get("attempts")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
            continue
        total += attempts
    return total


def inspect_receiptless_first_invocation(
    *,
    plan: RequestPlan,
    census_run_id: str,
    catalog_path: Path,
    data_root: Path,
) -> RecoveryState:
    """Forensically inspect an interrupted first invocation that emitted no receipt. Writes nothing.

    This is the explicit, read-only mode Decision 051 §7.4 permits and §8 bounds. It is selected
    explicitly — never by a missing receipt — and is bound to the exact interrupted
    ``census_run_id``. It may establish facts and the consumed count, but it can return only
    ``UNSAFE`` or ``UNDETERMINED``: it never returns ``SAFE``, never proposes continuation, and
    never enables ``--resume-from``. The predecessor-receipt requirement of Decision 050 §8 remains
    binding for every resume, and this mode supplies none.

    The consumed count is derived from durable evidence: the pre-ledger, incident-specific
    raw-lineage attempts (Decision 051 §5) plus every committed ``ops_retrieval_attempts``
    reservation bound to the run (§6). The two surfaces are disjoint for a genuine first invocation,
    so they sum without double counting; the approved ceiling is read from the plan and never
    reinterpreted.

    Args:
        plan: the approved request plan the interrupted run was executing.
        census_run_id: the exact interrupted run identity; must resolve to a registered run.
        catalog_path: the SQLite catalog to inspect read-only.
        data_root: the data root whose raw store is inspected.

    Raises:
        RecoveryInspectionError: the catalog is absent, or the run id does not resolve.
    """
    if not Path(catalog_path).is_file():
        message = (
            f"catalog {Path(catalog_path).name!r} does not exist; receiptless inspection needs the "
            f"catalog the interrupted run was writing to"
        )
        raise RecoveryInspectionError(message)

    tree = DataTree.from_root(data_root)

    with read_only_catalog(Path(catalog_path)) as connection:
        _registered_run_or_refuse(connection, census_run_id)
        integrity = integrity_report(connection)
        store = _inspect_store(connection, tree)
        projection = validate_audit_projection(connection, tree.audit / _PROJECTION_FILENAME)
        unresolved_states = _unresolved_recovery_states(connection)
        selection_runs = _in_flight_selection_runs(connection)
        ledger_reservations = _ledger_reservation_count(connection, census_run_id)

    lineage_attempts = _raw_lineage_attempts(tree)
    consumed = lineage_attempts + ledger_reservations

    # The headroom check reuses the same per-route decomposition the receipt-chain mode uses; only
    # the consumed count's provenance differs. No receipt is walked, so a synthetic unresolved walk
    # carries the durably derived consumed count into it.
    walk = _ChainWalk(
        receipt_ids=(),
        consumed_physical_attempts=consumed,
        interruption_state=None,
        resolved=False,
        detail="receiptless first-invocation inspection: no receipt chain was walked",
        request_plan_sha256=None,
    )
    headroom_fits, headroom_detail = _headroom(plan, walk, store)

    conditions = (
        ConditionResult(
            "8.1",
            "The receipt chain resolves completely",
            _NOT_MET,
            "no receipt was emitted for this first invocation; receiptless inspection is forensic "
            "and is never resume-eligible",
        ),
        ConditionResult(
            "8.2",
            "The interruption state is established, not guessed",
            _NOT_MET,
            "no receipt records an interruption state, so a receiptless first invocation "
            "establishes none",
        ),
        ConditionResult(
            "8.3",
            "The catalog passes quick, integrity, and foreign-key checks",
            _MET if integrity.passed else _NOT_MET,
            (
                f"quick_check={integrity.quick_check}, "
                f"integrity_check={integrity.integrity_check}, "
                f"foreign_key_violations={integrity.foreign_key_violations}"
            ),
        ),
        ConditionResult(
            "8.4",
            "No row exists without its object",
            _MET if not store.rows_without_object else _NOT_MET,
            f"{len(store.rows_without_object)} committed row(s) have no stored object",
        ),
        ConditionResult(
            "8.5",
            "Every orphan is adopted or quarantined",
            _MET if store.orphan_object_count == 0 else _NOT_MET,
            f"{store.orphan_object_count} object(s) on disk have no committed row",
        ),
        ConditionResult(
            "8.6",
            "No `.part` file was treated as complete",
            _MET if not store.rows_pointing_at_partials else _NOT_MET,
            (
                f"{len(store.rows_pointing_at_partials)} committed row(s) point at a partial file; "
                f"{store.partial_file_count} partial file(s) are present and unpromoted, which is "
                f"ordinary"
            ),
        ),
        ConditionResult(
            "8.7",
            "The audit projection is consistent or has been rebuilt from SQLite",
            _MET if projection.is_valid else _NOT_MET,
            (
                "the projection agrees with SQLite"
                if projection.is_valid
                else "the projection disagrees with SQLite and must be rebuilt from it"
            ),
        ),
        ConditionResult(
            "8.8",
            "The remainder fits inside the remaining ceiling headroom",
            _MET if headroom_fits else _NOT_MET,
            headroom_detail,
        ),
        ConditionResult(
            "8.9",
            "No unresolved schema-drift incident is open",
            _MET if unresolved_states == 0 else _NOT_MET,
            f"{unresolved_states} recovery state(s) remain blocked and await a ruling",
        ),
        ConditionResult(
            "8.10",
            "The plan hash is unchanged",
            _NOT_MET,
            "no receipt records a request_plan_sha256, so it cannot be established that the plan "
            "is unchanged; a receiptless first invocation carries no such evidence",
        ),
        ConditionResult(
            "8.11",
            "For a selection: the accepted lifecycle guards leave exactly one lawful next state",
            _NOT_APPLICABLE if selection_runs == 0 else _NOT_MET,
            (
                "no selection run was in flight"
                if selection_runs == 0
                else f"{selection_runs} selection run(s) were in flight; Milestone 3.2 owns the "
                f"selection lifecycle and this phase does not rule on it"
            ),
        ),
    )

    determination, basis, action = _determine_receiptless(
        store,
        consumed=consumed,
        ledger_reservations=ledger_reservations,
        lineage_attempts=lineage_attempts,
    )
    return RecoveryState(
        determination=determination,
        basis=basis,
        required_action=action,
        conditions=conditions,
        receipt_chain=(),
        interruption_state=None,
        consumed_physical_attempts=consumed,
        committed_observation_count=store.committed_observation_count,
        orphan_object_count=store.orphan_object_count,
        rows_without_object_count=len(store.rows_without_object),
        partial_file_count=store.partial_file_count,
    )


def _determine_receiptless(
    store: _StoreState,
    *,
    consumed: int,
    ledger_reservations: int,
    lineage_attempts: int,
) -> tuple[str, str, str]:
    """Classify a receiptless first invocation into `UNSAFE` or `UNDETERMINED` — never `SAFE`.

    The two `UNDETERMINED` triggers are the same ones the governing prose names, read for a run with
    no receipt to reconcile against: a committed row whose object is missing, and raw evidence the
    catalog does not account for (an orphan) — in receiptless mode the latter means the raw-store
    and catalog surfaces disagree with no receipt to settle them, which is exactly the interrupted
    initial T5 invocation's condition (Decision 051 §3.12). Every other state is `UNSAFE`: a
    receiptless first invocation is never resume-eligible, because Decision 050 §8's predecessor
    receipt does not exist. `SAFE` is unreachable by construction.
    """
    consumed_detail = (
        f"the accepted consumed count is {consumed} "
        f"({lineage_attempts} from durable raw lineage plus {ledger_reservations} committed "
        f"reservation(s))"
    )
    if store.rows_without_object:
        return (
            "UNDETERMINED",
            (
                f"{len(store.rows_without_object)} committed row(s) have no stored object, so it "
                f"cannot be established what was persisted; {consumed_detail}"
            ),
            "Stop. Do not resume. Refer for an owner ruling; a receiptless first invocation is "
            "never resume-eligible and no receipt is ever reconstructed.",
        )
    if store.orphan_object_count > 0:
        return (
            "UNDETERMINED",
            (
                f"{store.orphan_object_count} raw object(s) are present with no committed catalog "
                f"row and no receipt to reconcile them, so the raw-store and catalog surfaces "
                f"disagree and it cannot be established what committed; {consumed_detail}"
            ),
            "Stop. Do not resume. Refer for an owner ruling; never reconstruct a missing receipt, "
            "adopt the orphan, or mark the run here.",
        )
    return (
        "UNSAFE",
        (
            f"no predecessor receipt exists for this first invocation, so continuation is not "
            f"authorized (Decision 050 §8); {consumed_detail}"
        ),
        "Stop. A receiptless first invocation is forensic only: it can never return SAFE, propose "
        "continuation, or enable --resume-from. Any later resume requires a separate owner ruling "
        "and a valid predecessor receipt.",
    )
