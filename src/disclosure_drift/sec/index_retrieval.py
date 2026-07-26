"""Sequential, resumable retrieval and reconciliation of quarterly index instances.

Design in one line: **one worker, chronological order, one logical retrieval per
unsatisfied planned instance per pass, through the existing client.**

No parallel downloader and no second rate limiter exist here. Every request goes through
the injected :class:`~disclosure_drift.sec.http_client.SecClient`, so identity validation,
the aggregate rate limiter, bounded retries, global cooldown, redirect containment,
URL-family containment, block-page handling, snapshot reuse, and recovery all remain in
force exactly as they are for every other source.

**Logical versus actual requests.** The budget is derived from the plan: one logical
retrieval per unsatisfied required closed quarter, plus one for the provisional open
quarter when it was explicitly included. A logical retrieval is one operation on one
instance; the existing bounded HTTP retry policy may make several actual attempts inside
it. The two counts are accounted separately and never conflated, and no arbitrary lower
fixed cap is applied — a 2009-2024 plan of 64 quarters is a budget of 64.

**Resumability.** Each instance's lifecycle state is persisted transactionally as it
advances. On restart the loop verifies persisted raw objects, hashes, and parser and
reconciliation lineage; a fully verified satisfied instance is treated as satisfied
through the existing reuse mechanism and is not retrieved again; the loop then resumes
from the earliest unsatisfied required instance. Earlier attempts and observations are
preserved, and failed evidence is never overwritten or deleted.

**Failure continuation versus global stop.** An ordinary per-instance failure persists
its terminal evidence, keeps the census incomplete, names the exact quarter and reason,
and lets later quarters proceed. A global condition — identity or configuration failure,
a cooldown or blocking response, a containment failure, the request boundary, loss of
catalog writer ownership, or an unsafe recovery state — stops the loop immediately, and
the stopped run remains resumable.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Final, Literal

from disclosure_drift.errors import (
    CatalogWriteError,
    DisclosureDriftError,
    RawObjectIntegrityError,
    SecUserAgentError,
    SingleWriterViolationError,
)
from disclosure_drift.sec.http_client import (
    FetchResult,
    ProhibitedRetrievalError,
    SecClient,
)
from disclosure_drift.sec.index_plan import IndexInstancePlan, PlannedIndexInstances
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation
from disclosure_drift.sec.parsers.full_index import REGION_INDEX_ROWS, parse_company_index
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES, filing_body_url_is_prohibited
from disclosure_drift.sec.urls import RedirectBoundaryError, request_identity

__all__ = [
    "GLOBAL_STOP_REASONS",
    "INDEX_RETRIEVAL_POLICY_VERSION",
    "IndexInstanceOutcome",
    "IndexRetrievalAccounting",
    "InstanceLifecycleState",
    "logical_budget",
    "order_instances",
]

INDEX_RETRIEVAL_POLICY_VERSION: Final = "index-retrieval-orchestration/1.0"
_SOURCE_ID: Final = "sec_full_index_company"

InstanceLifecycleState = Literal[
    "planned",
    "retrieval_started",
    "retrieved",
    "validly_reused",
    "parsed",
    "reconciled",
    "satisfied",
    "failed",
    "blocked",
    "unavailable",
    "indeterminate",
]

GLOBAL_STOP_REASONS: Final[tuple[str, ...]] = (
    "sec_identity_invalid",
    "global_cooldown_or_block",
    "network_containment_failure",
    "request_boundary_reached",
    "catalog_writer_ownership_lost",
    "unsafe_recovery_state",
)
"""Conditions that stop the whole loop rather than failing one instance."""

_COOLDOWN_ACTIONS: Final[frozenset[str]] = frozenset({"cooldown", "redirect_refused"})
_BLOCKING_REASONS: Final[frozenset[str]] = frozenset(
    {"SEC_BLOCK_PAGE", "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY", "SEC_REDIRECT_DEPTH_EXCEEDED"}
)


def order_instances(plan: PlannedIndexInstances) -> tuple[IndexInstancePlan, ...]:
    """Return instances in strict chronological order, open quarter last.

    Required closed quarters are processed oldest first so a stopped run always resumes
    at the earliest gap. The provisional open quarter is processed only after every
    required closed quarter, so an open-quarter failure can never consume the budget or
    the run before the historical record is complete.
    """
    closed = sorted(
        (item for item in plan.instances if item.kind == "required_closed_quarter"),
        key=lambda item: (item.year, item.quarter),
    )
    open_quarters = sorted(
        (item for item in plan.instances if item.kind == "provisional_open_quarter"),
        key=lambda item: (item.year, item.quarter),
    )
    return (*closed, *open_quarters)


def logical_budget(
    plan: PlannedIndexInstances,
    satisfied_keys: Sequence[str] = (),
) -> int:
    """Derive the logical retrieval budget from the plan.

    One logical retrieval per unsatisfied required closed quarter, plus one for the
    provisional open quarter when it was explicitly included and is unsatisfied. No
    arbitrary lower cap is imposed: a valid 2009-2024 plan yields 64.
    """
    satisfied = set(satisfied_keys)
    budget = sum(1 for item in plan.required_closed if item.instance_key not in satisfied)
    open_instance = plan.provisional_open
    if (
        open_instance is not None
        and open_instance.required
        and open_instance.instance_key not in satisfied
    ):
        budget += 1
    return budget


@dataclass(frozen=True, slots=True)
class IndexInstanceOutcome:
    """Terminal result for one instance in one orchestration pass."""

    instance: IndexInstancePlan
    state: InstanceLifecycleState
    observation: SourceObservation | None = None
    parse: ParseOutcome | None = None
    logical_retrievals: int = 0
    http_attempts: int = 0
    reason_codes: tuple[str, ...] = ()
    detail: str = ""
    global_stop_reason: str | None = None

    @property
    def satisfied(self) -> bool:
        """Whether every stage passed, so the instance counts as coverage."""
        return self.state == "satisfied"

    @property
    def retries(self) -> int:
        """Actual attempts beyond the first, inside this logical retrieval."""
        return max(0, self.http_attempts - self.logical_retrievals)

    @property
    def contributes_finalized_coverage(self) -> bool:
        """Only a satisfied closed quarter contributes finalized coverage."""
        return self.satisfied and self.instance.is_finalized_period

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for persistence and the coverage report."""
        return {
            "instance_key": self.instance.instance_key,
            "kind": self.instance.kind,
            "required": self.instance.required,
            "lifecycle_state": self.state,
            "satisfied": self.satisfied,
            "observation_id": None if self.observation is None else self.observation.observation_id,
            "logical_retrievals": self.logical_retrievals,
            "http_attempts": self.http_attempts,
            "retries": self.retries,
            "parsed_row_count": (
                None
                if self.parse is None
                else next(
                    (
                        item.row_count
                        for item in self.parse.structural
                        if item.region == REGION_INDEX_ROWS
                    ),
                    None,
                )
            ),
            "reason_codes": list(self.reason_codes),
            "detail": self.detail,
            "global_stop_reason": self.global_stop_reason,
        }


@dataclass(slots=True)
class IndexRetrievalAccounting:
    """Per-run accounting that keeps logical and actual request counts apart."""

    instances_planned: int = 0
    instances_already_satisfied: int = 0
    logical_budget: int = 0
    logical_retrievals_initiated: int = 0
    http_attempts: int = 0
    instances_successful: int = 0
    instances_failed: int = 0
    stopped_early: bool = False
    stop_reason: str | None = None
    outcomes: list[IndexInstanceOutcome] = field(default_factory=list)

    @property
    def retries(self) -> int:
        """Actual attempts beyond one per logical retrieval."""
        return max(0, self.http_attempts - self.logical_retrievals_initiated)

    @property
    def instances_remaining(self) -> int:
        """Planned instances neither already satisfied nor satisfied in this pass."""
        return max(
            0,
            self.instances_planned - self.instances_already_satisfied - self.instances_successful,
        )

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the report and the catalog."""
        return {
            "policy_version": INDEX_RETRIEVAL_POLICY_VERSION,
            "instances_planned": self.instances_planned,
            "instances_already_satisfied": self.instances_already_satisfied,
            "logical_budget": self.logical_budget,
            "logical_retrievals_initiated": self.logical_retrievals_initiated,
            "http_attempts": self.http_attempts,
            "retries": self.retries,
            "instances_successful": self.instances_successful,
            "instances_failed": self.instances_failed,
            "instances_remaining": self.instances_remaining,
            "stopped_early": self.stopped_early,
            "stop_reason": self.stop_reason,
            "instances": [dict(item.as_record()) for item in self.outcomes],
        }


def retrieve_instance(
    client: SecClient,
    store: SnapshotStore,
    instance: IndexInstancePlan,
    *,
    on_state: Callable[[InstanceLifecycleState, IndexInstanceOutcome], None] | None = None,
) -> IndexInstanceOutcome:
    """Retrieve, verify, and parse one quarterly index instance.

    Exactly one logical retrieval is initiated. The URL is built only from the registered
    quarterly company-index template, and it is proved not to be a filing-document or
    accession URL before the request is constructed.

    Args:
        client: The shared SEC client. All policy lives there.
        store: Snapshot store, which supplies conditional-request validators and
            performs reuse and verification.
        instance: The planned instance to process.
        on_state: Optional callback invoked as each lifecycle state is reached, so the
            caller can persist progress transactionally between stages.

    Returns:
        The terminal outcome for this instance, including whether a global stop condition
        was hit.
    """
    spec = SOURCES[_SOURCE_ID]
    parameters = {"year": str(instance.year), "quarter": str(instance.quarter)}
    url = spec.url(**parameters)

    # Prove containment before any request is constructed. The quarterly index template
    # cannot express a filing-document or accession-document path, and the guard is
    # asserted here rather than assumed.
    if filing_body_url_is_prohibited(url):  # pragma: no cover - registry forbids it
        return _terminal(
            instance,
            "blocked",
            reason_codes=("SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",),
            detail=f"refusing constructed index URL {url}: it resolves as a filing document",
            global_stop_reason="network_containment_failure",
        )

    identity = request_identity(_SOURCE_ID, url, parameters)
    previous = store.latest_for(_SOURCE_ID, identity)
    started = _terminal(instance, "retrieval_started", logical_retrievals=1)
    if on_state is not None:
        on_state("retrieval_started", started)

    try:
        result: FetchResult = client.fetch(
            _SOURCE_ID,
            purpose="reconcile quarterly accession coverage without retrieving any filing",
            parameters=parameters,
            etag=previous.etag,
            last_modified=previous.last_modified,
        )
    except SecUserAgentError as exc:
        return _terminal(
            instance,
            "blocked",
            logical_retrievals=1,
            detail=str(exc),
            global_stop_reason="sec_identity_invalid",
        )
    except RedirectBoundaryError as exc:
        return _terminal(
            instance,
            "blocked",
            logical_retrievals=1,
            reason_codes=(exc.reason_code,),
            detail=str(exc),
            global_stop_reason="network_containment_failure",
        )
    except ProhibitedRetrievalError as exc:
        return _terminal(
            instance,
            "blocked",
            logical_retrievals=1,
            detail=str(exc),
            global_stop_reason="network_containment_failure",
        )

    attempts = max(1, result.attempts)
    stop = _global_stop_for(result)
    observation = store.record(result, period_is_closed=instance.is_finalized_period)

    if not observation.is_usable:
        state: InstanceLifecycleState = (
            "unavailable" if observation.outcome == "failed" else "indeterminate"
        )
        return _terminal(
            instance,
            "blocked" if stop else state,
            observation=observation,
            logical_retrievals=1,
            http_attempts=attempts,
            reason_codes=observation.reason_codes,
            detail=observation.detail,
            global_stop_reason=stop,
        )

    reused = observation.outcome == "reused_snapshot"
    reached: InstanceLifecycleState = "validly_reused" if reused else "retrieved"
    current = _terminal(
        instance,
        reached,
        observation=observation,
        logical_retrievals=1,
        http_attempts=attempts,
    )
    if on_state is not None:
        on_state(reached, current)

    try:
        payload = store.load_payload(observation)
    except RawObjectIntegrityError as exc:
        return _terminal(
            instance,
            "indeterminate",
            observation=observation,
            logical_retrievals=1,
            http_attempts=attempts,
            reason_codes=("RAW_FILE_CHECKSUM_MISMATCH",),
            detail=f"raw-object verification failed: {exc}",
        )

    location = RecordLocation(observation.observation_id, _SOURCE_ID)
    parse = parse_company_index(payload.decode("utf-8", "replace"), location)
    if not parse.counts_are_trustworthy:
        return _terminal(
            instance,
            "indeterminate",
            observation=observation,
            parse=parse,
            logical_retrievals=1,
            http_attempts=attempts,
            reason_codes=parse.reason_codes,
            detail=(
                f"index rows for {instance.instance_key} could not be read as a countable "
                "table; the raw object and every parsed row are preserved"
            ),
        )

    parsed = _terminal(
        instance,
        "parsed",
        observation=observation,
        parse=parse,
        logical_retrievals=1,
        http_attempts=attempts,
    )
    if on_state is not None:
        on_state("parsed", parsed)
    return parsed


def _global_stop_for(result: FetchResult) -> str | None:
    """Return a global stop reason when the response demands one."""
    if result.reason_code in _BLOCKING_REASONS:
        return (
            "network_containment_failure"
            if result.reason_code != "SEC_BLOCK_PAGE"
            else "global_cooldown_or_block"
        )
    if any(action in _COOLDOWN_ACTIONS for action in result.actions):
        return "global_cooldown_or_block"
    return None


def _terminal(
    instance: IndexInstancePlan,
    state: InstanceLifecycleState,
    *,
    observation: SourceObservation | None = None,
    parse: ParseOutcome | None = None,
    logical_retrievals: int = 0,
    http_attempts: int = 0,
    reason_codes: tuple[str, ...] = (),
    detail: str = "",
    global_stop_reason: str | None = None,
) -> IndexInstanceOutcome:
    return IndexInstanceOutcome(
        instance=instance,
        state=state,
        observation=observation,
        parse=parse,
        logical_retrievals=logical_retrievals,
        http_attempts=http_attempts,
        reason_codes=reason_codes,
        detail=detail,
        global_stop_reason=global_stop_reason,
    )


def classify_stop(error: BaseException) -> str | None:
    """Map an exception raised mid-loop onto a global stop reason, if any."""
    if isinstance(error, SingleWriterViolationError):
        return "catalog_writer_ownership_lost"
    if isinstance(error, CatalogWriteError):
        return "unsafe_recovery_state"
    if isinstance(error, SecUserAgentError):
        return "sec_identity_invalid"
    if isinstance(error, RedirectBoundaryError):
        return "network_containment_failure"
    if isinstance(error, DisclosureDriftError):
        return None
    return None


def new_event_id() -> str:
    """Return a fresh identifier for an append-only lifecycle event."""
    return uuid.uuid4().hex
