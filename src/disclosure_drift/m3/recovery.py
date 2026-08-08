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
from datetime import UTC, datetime
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
@dataclass(frozen=True, slots=True)
class _SelectedRun:
    """The selected governed run's durable boundary instants, as recorded — never inferred.

    These two fields are the run-identity half of the Decision 051 §6 / contract §12 evidence: the
    raw-lineage fallback is scoped to what provably happened *inside* this run, and the recorded
    start (and finish, where one exists) is the durable evidence that scoping stands on.
    """

    started_at_raw: str
    finished_at_raw: str | None


def _registered_run_or_refuse(
    connection: sqlite3.Connection, census_run_id: str, *, expected_window: str
) -> _SelectedRun:
    """Resolve ``census_run_id`` to the governed interrupted acquisition run, or refuse.

    Receiptless mode is bound to the exact interrupted run identity (Decision 051 §7.4). It is not
    enough that *some* ``ops_ingestion_jobs`` row exists: the row must be a governed M3.2
    acquisition run (``job_kind = 'm3_2_acquisition'``) whose ``stage`` is the window the inspected
    plan describes, so a mistyped id, a non-acquisition job that happens to share an id, or a run
    for a different window can never read as a genuine recovery finding (Decision 051 §6.6, §8; data
    dictionary §5A). A run that does not resolve this way is a caller error, reported the same way a
    missing head receipt is. The resolved row's recorded start and finish instants are returned
    because they are the durable boundaries the raw-evidence attribution is scoped with.
    """
    # Local import: `acquisition` imports this module (for `RecoveryState` and friends), so
    # importing its acquisition-job-kind constant at module scope would be a cycle. By call time
    # both modules are fully initialised, and the constant is the single source of the kind.
    from disclosure_drift.m3.acquisition import ACQUISITION_JOB_KIND

    row = connection.execute(
        "SELECT job_kind, stage, started_at_utc, finished_at_utc FROM ops_ingestion_jobs "
        "WHERE job_id = ?",
        (census_run_id,),
    ).fetchone()
    if row is None:
        message = (
            f"census run {census_run_id!r} does not resolve to a registered acquisition run; "
            "receiptless inspection is bound to the exact interrupted run identity and never "
            "invents one"
        )
        raise RecoveryInspectionError(message)
    job_kind = str(row[0])
    stage = str(row[1])
    if job_kind != ACQUISITION_JOB_KIND:
        message = (
            f"census run {census_run_id!r} carries job kind {job_kind!r}, not a governed M3.2 "
            "acquisition run; receiptless inspection scopes to the interrupted acquisition run, "
            "not to any ingestion job that happens to share an id"
        )
        raise RecoveryInspectionError(message)
    if stage != expected_window:
        message = (
            f"census run {census_run_id!r} records stage {stage!r}, but the inspected plan is for "
            f"window {expected_window!r}; the run identity and the plan must name the same window"
        )
        raise RecoveryInspectionError(message)
    return _SelectedRun(
        started_at_raw=str(row[2]),
        finished_at_raw=None if row[3] is None else str(row[3]),
    )


def _other_acquisition_run_starts(
    connection: sqlite3.Connection, census_run_id: str
) -> tuple[str, ...]:
    """The recorded start instants of every governed M3.2 acquisition run except the selected one.

    A later governed run's start bounds the selected run's raw-evidence window from above: an
    in-scope lineage segment retrieved after another governed acquisition run began belongs to that
    run's accounting, never the selected run's. Earlier runs' starts prove nothing about the
    selected window and are ignored by :func:`_run_window`. Non-acquisition jobs are excluded here
    for the same reason the run resolution refuses them: they are not governed acquisition
    boundaries (Decision 051 §6.6).
    """
    # Local import for the same cycle reason documented in `_registered_run_or_refuse`.
    from disclosure_drift.m3.acquisition import ACQUISITION_JOB_KIND

    rows = connection.execute(
        "SELECT started_at_utc FROM ops_ingestion_jobs WHERE job_kind = ? AND job_id != ?",
        (ACQUISITION_JOB_KIND, census_run_id),
    ).fetchall()
    return tuple(str(row[0]) for row in rows)


def _parse_utc_instant(value: object) -> datetime | None:
    """Parse one strict RFC 3339 UTC instant, or ``None`` when it cannot anchor an ordering.

    Ordering evidence must be exact: a non-string, an empty string, a malformed string, or a naive
    instant proves no order, and every caller treats ``None`` as non-provable evidence rather than
    guessing a position for it (Decision 051 §6.9; contract §12 item 5). The current wall clock is
    never consulted anywhere in this accounting.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class _LedgerReservation:
    """One durable pre-send reservation: its request-URL identity and its commit instant.

    Both fields matter to reconciliation. URL identity alone cannot prove event identity — the
    same URL is lawfully requested more than once across a run's lifetime — so coverage decisions
    additionally require the recorded commit order (`started_at_utc` is written before the physical
    send, §5A) to prove *which* retrieval segment a reservation accounts for.
    """

    source_url_canonical: str
    started_at_raw: str


@dataclass(frozen=True, slots=True)
class _LedgerReservations:
    """The durable pre-send reservations bound to one run (Decision 051 §6; §5A)."""

    count: int
    rows: tuple[_LedgerReservation, ...]


def _ledger_reservations(connection: sqlite3.Connection, census_run_id: str) -> _LedgerReservations:
    """Read the durable ``ops_retrieval_attempts`` reservations bound to this run.

    ``count`` is the primary consumed-count surface: every committed ``started`` row is one
    consumed physical attempt regardless of its lineage, response, or terminal state — including a
    row stranded before its transport call — and a terminal state never erases the consumption
    (§5A rules 1-3). ``rows`` carries each reservation's canonical request URL *and* its pre-send
    commit instant, so a post-ledger segment's raw lineage is recognised by durable event order —
    not URL equality alone — and never counted a second time (§5A rule 4).
    """
    rows = connection.execute(
        "SELECT source_url_canonical, started_at_utc FROM ops_retrieval_attempts WHERE job_id = ?",
        (census_run_id,),
    ).fetchall()
    return _LedgerReservations(
        count=len(rows),
        rows=tuple(
            _LedgerReservation(
                source_url_canonical=str(row[0]),
                started_at_raw=str(row[1]),
            )
            for row in rows
        ),
    )


@dataclass(frozen=True, slots=True)
class _LineageAccounting:
    """The pre-ledger raw-lineage contribution to the consumed count, and any ambiguity found."""

    pre_ledger_attempts: int
    undetermined_reason: str | None


@dataclass(frozen=True, slots=True)
class _RunWindow:
    """The selected run's provable raw-evidence window, built from durable instants only.

    ``started`` is the selected run's recorded start (``None`` when it cannot be parsed).
    ``upper_bound`` is the earliest provable end of the selected run's accounting window: its own
    recorded finish, or the earliest later governed acquisition run's start, whichever is earlier —
    ``None`` when no such bound exists (the interrupted run's ordinary condition). The two flags
    record boundary evidence that *exists but proves no order*: another governed run starting at
    the selected run's exact start instant, or a boundary instant that cannot be parsed. Either
    makes in-window attribution non-provable rather than merely imprecise (Decision 051 §6.9).
    """

    started: datetime | None
    upper_bound: datetime | None
    boundary_ambiguous: bool
    boundary_unparseable: bool


def _run_window(selected: _SelectedRun, other_starts_raw: tuple[str, ...]) -> _RunWindow:
    """Build the selected run's provable window from the recorded run-boundary instants."""
    started = _parse_utc_instant(selected.started_at_raw)
    boundary_ambiguous = False
    boundary_unparseable = False
    upper_bound: datetime | None = None
    if selected.finished_at_raw is not None:
        finished = _parse_utc_instant(selected.finished_at_raw)
        if finished is None:
            boundary_unparseable = True
        else:
            upper_bound = finished
    for raw in other_starts_raw:
        parsed = _parse_utc_instant(raw)
        if parsed is None:
            boundary_unparseable = True
        elif started is not None and parsed == started:
            boundary_ambiguous = True
        elif (
            started is not None
            and parsed > started
            and (upper_bound is None or parsed < upper_bound)
        ):
            upper_bound = parsed
    return _RunWindow(
        started=started,
        upper_bound=upper_bound,
        boundary_ambiguous=boundary_ambiguous,
        boundary_unparseable=boundary_unparseable,
    )


def _selected_run_lineage_contribution(
    document: Mapping[str, object],
    *,
    window: _RunWindow,
    ledger: _LedgerReservations,
) -> tuple[int, str | None]:
    """Attribute one in-scope lineage manifest by durable event identity and order.

    Returns ``(attempts_to_add, undetermined_reason)``. ``(0, None)`` means the manifest is
    provably excluded or provably ledger-covered; a non-``None`` reason means the evidence exists
    but cannot be reconciled exactly, which the caller reports as ``UNDETERMINED`` rather than an
    invented count. The decisions, in order:

    * a manifest retrieved strictly before the selected run's recorded start predates the run and
      is proven to belong elsewhere — excluded (Decision 051 §6.4's boundary discipline);
    * one retrieved strictly after the window's provable upper bound (the run's recorded finish or
      a later governed acquisition run's start) postdates the run — excluded the same way;
    * one whose retrieval instant *equals* a boundary instant proves no order, so ownership of the
      segment is not provable — ``UNDETERMINED``, never a guess;
    * an owned segment is **ledger-covered** only when selected-run reservation rows whose commit
      instants strictly precede the retrieval fully account for its recorded ``attempts`` — those
      sends are already counted once by the ledger, so the lineage adds nothing (§5A rule 4). A
      reservation committed strictly *after* the retrieval is a distinct later event: it is itself
      counted once by the ledger and can never erase or absorb the earlier lineage attempt;
    * an owned segment with **no** preceding or order-ambiguous matching reservation is genuine
      pre-ledger evidence and adds exactly its recorded ``attempts`` (Decision 051 §5);
    * anything between — reservations that only partially account for the segment's attempts, or
      whose order against the retrieval is unparseable or exactly simultaneous — is partially
      matched evidence, which is ``UNDETERMINED`` by rule, not a rounding choice.
    """
    retrieved = _parse_utc_instant(document.get("retrieved_at_utc"))
    if retrieved is None:
        return 0, (
            "an in-scope raw-lineage manifest records no parseable UTC retrieval instant, so it "
            "cannot be ordered against the run boundaries"
        )
    if window.started is None:
        return 0, (
            "the selected run's recorded start instant cannot be parsed, so no in-scope lineage "
            "can be attributed to or excluded from the run"
        )
    if retrieved < window.started:
        return 0, None  # proven to predate the selected run: recorded elsewhere, never added here
    if retrieved == window.started:
        return 0, (
            "an in-scope retrieval instant equals the selected run's recorded start, so which "
            "run owns the segment is not provable"
        )
    if window.upper_bound is not None:
        if retrieved > window.upper_bound:
            return 0, None  # proven to postdate the selected run's window: a later run's segment
        if retrieved == window.upper_bound:
            return 0, (
                "an in-scope retrieval instant equals a governed run boundary, so which run owns "
                "the segment is not provable"
            )
    if window.boundary_ambiguous:
        return 0, (
            "another governed acquisition run records the selected run's exact start instant, so "
            "in-window lineage cannot be attributed between them"
        )
    if window.boundary_unparseable:
        return 0, (
            "a governed run-boundary instant cannot be parsed, so in-window lineage cannot be "
            "proven to belong to the selected run"
        )
    attempts = document.get("attempts")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
        return 0, "an in-scope raw-lineage manifest records no usable attempt count"
    segment_urls = set()
    for key in ("requested_url", "final_url"):
        url = document.get(key)
        if isinstance(url, str) and url:
            segment_urls.add(url)
    if not segment_urls and ledger.rows:
        return 0, (
            "an in-scope raw-lineage manifest records no request URL identity, so ledger "
            "coverage of its segment is not provable"
        )
    preceding = 0
    order_ambiguous = 0
    for reservation in ledger.rows:
        if reservation.source_url_canonical not in segment_urls:
            continue
        reserved_at = _parse_utc_instant(reservation.started_at_raw)
        if reserved_at is None or reserved_at == retrieved:
            order_ambiguous += 1
        elif reserved_at < retrieved:
            preceding += 1
        # A strictly later reservation is its own consumed event, already counted once by the
        # ledger; it neither covers nor erases this earlier retrieval segment.
    if preceding >= attempts:
        return 0, None  # ledger-covered: the preceding reservations already count these sends
    if preceding == 0 and order_ambiguous == 0:
        return attempts, None  # genuine pre-ledger evidence, counted exactly once
    return 0, (
        "selected-run reservations only partially or order-ambiguously account for an in-scope "
        "retrieval segment, so exact ledger coverage is not provable"
    )


def _pre_ledger_lineage_attempts(
    tree: DataTree,
    *,
    in_scope_source_ids: frozenset[str],
    ledger: _LedgerReservations,
    window: _RunWindow,
) -> _LineageAccounting:
    """Sum the physical attempts provably attributable to the selected run and *only* to it.

    Raw lineage is **not** a second consumed-count authority beside ``ops_retrieval_attempts``; it
    is the incident-specific pre-ledger evidence Decision 051 §5 accepts for the interrupted initial
    T5 invocation, whose ledger table is empty and is never backfilled (§5A). URL equality alone
    proves nothing here — the same URL lawfully recurs across runs and across a single run's
    lifetime — so every inclusion and exclusion rests on durable run and event identity:

    * a manifest whose ``source_id`` is not a route of the interrupted run's plan is provably
      unrelated lineage outside this accounting scope, and never changes the count
      (Decision 051 §6.6);
    * an in-scope manifest is attributed by :func:`_selected_run_lineage_contribution`, which
      excludes segments the run boundaries prove belong elsewhere, adds pre-ledger segments the
      selected run provably owns, and adds nothing for segments the ledger's strictly-preceding
      reservations already account for — the same segment is never counted twice, and no segment
      the run owns is ever silently dropped.

    Evidence that cannot be reconciled is never silently treated as zero. A manifest that cannot
    be read, is not a JSON object, records no source identity, or fails exact attribution sets an
    ``UNDETERMINED`` reason, and the total then stands as a durable floor rather than a proven
    exact count (Decision 051 §6.5, §6.9; §5A rule 5). Provably unrelated manifests are excluded
    before any attribution field is inspected, so they never raise a spurious ambiguity.
    """
    total = 0
    undetermined: str | None = None
    raw_root = tree.data_root / "raw"
    if not raw_root.is_dir():
        return _LineageAccounting(0, None)
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or not path.name.endswith(_LINEAGE_SUFFIX):
            continue
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            undetermined = undetermined or "a raw-lineage manifest could not be read"
            continue
        if not isinstance(document, dict):
            undetermined = undetermined or "a raw-lineage manifest is not a JSON object"
            continue
        source_id = document.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            undetermined = undetermined or "a raw-lineage manifest records no source identity"
            continue
        if source_id not in in_scope_source_ids:
            continue  # provably unrelated lineage: outside this run's plan scope, never counted
        contribution, reason = _selected_run_lineage_contribution(
            document, window=window, ledger=ledger
        )
        if reason is not None:
            undetermined = undetermined or reason
            continue
        total += contribution
    return _LineageAccounting(pre_ledger_attempts=total, undetermined_reason=undetermined)


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

    The consumed count is derived from durable evidence with ``ops_retrieval_attempts`` as the
    primary surface (Decision 051 §6; §5A). Every reservation bound to the run is counted exactly
    once, and raw lineage adds **only** the pre-ledger, incident-specific attempts
    (Decision 051 §5) the selected run provably owns. Attribution rests on durable run and event
    identity — the run's recorded boundary instants, later governed runs' starts, and the pre-send
    commit order of matching reservations — never on URL equality alone: a segment the ledger's
    strictly-preceding reservations account for is never counted twice, a strictly later same-URL
    reservation never erases an earlier lineage attempt, and lineage the boundaries prove belongs
    to another run, or that falls outside the interrupted run's plan scope, never changes the
    count. Evidence that cannot be reconciled exactly fails closed as ``UNDETERMINED`` with the
    provable count standing as a durable floor, never an invented exact value. The approved
    ceiling is read from the plan and never reinterpreted.

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
    in_scope_source_ids = frozenset(route.source_id for route in plan.routes)

    with read_only_catalog(Path(catalog_path)) as connection:
        selected = _registered_run_or_refuse(
            connection, census_run_id, expected_window=plan.acquisition_window
        )
        integrity = integrity_report(connection)
        store = _inspect_store(connection, tree)
        projection = validate_audit_projection(connection, tree.audit / _PROJECTION_FILENAME)
        unresolved_states = _unresolved_recovery_states(connection)
        selection_runs = _in_flight_selection_runs(connection)
        ledger = _ledger_reservations(connection, census_run_id)
        other_starts = _other_acquisition_run_starts(connection, census_run_id)

    lineage = _pre_ledger_lineage_attempts(
        tree,
        in_scope_source_ids=in_scope_source_ids,
        ledger=ledger,
        window=_run_window(selected, other_starts),
    )
    # ops_retrieval_attempts is the primary consumed-count surface; pre-ledger raw lineage adds only
    # the incident attempts the ledger does not already hold (§5A rule 4). No segment is counted
    # twice, and the approved ceiling is read from the plan and never reinterpreted.
    consumed = lineage.pre_ledger_attempts + ledger.count

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
        ledger_reservations=ledger.count,
        lineage_attempts=lineage.pre_ledger_attempts,
        undetermined_reason=lineage.undetermined_reason,
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
    undetermined_reason: str | None,
) -> tuple[str, str, str]:
    """Classify a receiptless first invocation into `UNSAFE` or `UNDETERMINED` — never `SAFE`.

    `UNDETERMINED` is returned when the physical-attempt evidence cannot be reconciled exactly
    (malformed, unattributable, or ambiguous raw lineage — Decision 051 §6.5; §5A rule 5), and for
    the two triggers the governing prose names for a run with no receipt to reconcile against: a
    committed row whose object is missing, and raw evidence the catalog does not account for (an
    orphan) — in receiptless mode the latter means the raw-store and catalog surfaces disagree with
    no receipt to settle them, which is exactly the interrupted initial T5 invocation's condition
    (Decision 051 §3.12). Every other state is `UNSAFE`: a receiptless first invocation is never
    resume-eligible, because Decision 050 §8's predecessor receipt does not exist. `SAFE` is
    unreachable by construction.
    """
    consumed_detail = (
        f"the accepted consumed count is {consumed} "
        f"({lineage_attempts} from pre-ledger raw lineage plus {ledger_reservations} durable "
        f"reservation(s))"
    )
    if undetermined_reason is not None:
        return (
            "UNDETERMINED",
            (
                f"the physical-attempt evidence cannot be reconciled exactly: "
                f"{undetermined_reason}; {consumed_detail} from the evidence that could be read, "
                f"which is a durable floor, not a proven exact total"
            ),
            "Stop. Do not resume. Refer for an owner ruling; malformed, unattributable, or "
            "ambiguous attempt evidence is never silently counted as an exact value or as zero.",
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
