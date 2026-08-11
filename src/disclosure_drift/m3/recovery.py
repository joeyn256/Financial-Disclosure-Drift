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
import re
import sqlite3
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.receipt import (
    ACQUISITION_WINDOWS,
    ReceiptValidationError,
    canonical_bytes,
    inspect_receipt,
)
from disclosure_drift.m3.request_plan import RequestPlan, derive_a_reachable
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.observation_catalog import load_observations, validate_audit_projection
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import read_only_connection
from disclosure_drift.storage.sqlite import integrity_report

__all__ = [
    "CARRY_IN_ACQUISITION_WINDOW",
    "CARRY_IN_APPROVED_REQUEST_CEILING",
    "CARRY_IN_AUTHORITY_SCHEMA_VERSION",
    "CARRY_IN_AUTHORIZING_DECISION_REFERENCE",
    "CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT",
    "CARRY_IN_HISTORICAL_ROUTE_ALLOCATION",
    "CARRY_IN_REQUEST_PLAN_SHA256",
    "PLAN_TRANSITION_ACQUISITION_WINDOW",
    "PLAN_TRANSITION_APPROVED_REQUEST_CEILING",
    "PLAN_TRANSITION_DECISION_REFERENCE",
    "PLAN_TRANSITION_NEW_URL",
    "PLAN_TRANSITION_OLD_URL",
    "PLAN_TRANSITION_PREDECESSOR_PLAN_SHA256",
    "PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION",
    "PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID",
    "PLAN_TRANSITION_SUBSTITUTION_COUNT",
    "PLAN_TRANSITION_SUCCESSOR_PLAN_SHA256",
    "PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION",
    "RECOVERY_DETERMINATIONS",
    "CarryInFixedBindings",
    "ConditionResult",
    "PlanTransitionAuthority",
    "ReceiptChainAccounting",
    "RecoveryInspectionError",
    "RecoveryState",
    "carry_in_checkpoint_disagreement",
    "carry_in_fixed_binding_disagreement",
    "carry_in_orphan_reference_disagreement",
    "inspect_receiptless_first_invocation",
    "inspect_recovery_state",
    "read_only_catalog",
    "walk_receipt_chain",
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
class ReceiptChainAccounting:
    """The resolved receipt chain, its cumulative consumption, and its carry-in root.

    ``consumed_physical_attempts`` is the Decision 055 §7.5 cumulative total:

    .. code-block:: text

        cumulative = sum(actual_physical_attempt_count over every receipt in the chain)
                   + carried_forward of the single no-predecessor root only

    The root's carried-forward baseline is added **exactly once** — never ``N`` alone, and never
    once per receipt. Every consumer of a chain's consumed count reads this one number, so the
    walker, ``m3 acquire --show-scope``, and every recovery and continuation surface cannot drift
    apart: there is only one implementation of the arithmetic.
    """

    receipt_ids: tuple[str, ...]
    consumed_physical_attempts: int
    interruption_state: str | None
    resolved: bool
    detail: str
    request_plan_sha256: str | None = None
    root_carried_forward: int = 0
    root_carry_in_authority_sha256: str | None = None
    #: The root receipt's own window and ceiling, carried so the carry-in cross-check can compare
    #: the checkpoint against what the root actually recorded. Both are long-standing `2.0` receipt
    #: fields (`acquisition_window`, `approved_request_ceiling`); nothing new is required of a
    #: receipt to populate them.
    root_acquisition_window: str | None = None
    root_approved_request_ceiling: int | None = None
    #: The **head** receipt's own terminal facts, as it recorded them. They describe how *this*
    #: invocation ended, which is a different question from the chain's cumulative arithmetic
    #: above, and they are the evidence condition 8.2 establishes a terminal state from. Each is
    #: `None` only when the head receipt could not be read at all — in which case the chain is
    #: already unresolved and 8.1 has stopped the inspection.
    head_completion_status: str | None = None
    head_reason_code: str | None = None
    head_started_at_utc: str | None = None
    head_completed_at_utc: str | None = None
    head_actual_physical_attempt_count: int | None = None
    head_acquisition_window: str | None = None


def walk_receipt_chain(head_path: Path) -> ReceiptChainAccounting:
    """Follow `recovery_predecessor_receipt_id` back toward the first attempt.

    A missing or unreadable predecessor stops the walk and marks the chain unresolved. The missing
    receipt is *never* reconstructed: the template says so explicitly, and a reconstructed receipt
    would assert a consumed count nobody recorded.

    Mixed ``2.0``/``3.0`` chains walk identically. A ``2.0`` root carries no carried-forward
    baseline, so it contributes zero and the arithmetic is unchanged for every chain written before
    Decision 055; a ``3.0`` clean carry-in root contributes its baseline once, at the root, where it
    is the only receipt in the chain with no predecessor to have inherited it from.

    An **unresolved** chain never contributes a carry-in baseline: the walk did not reach a root, so
    there is no root to read one from, and the caller already treats an unresolved chain as a stop.
    """
    receipts_dir = head_path.parent
    seen: list[str] = []
    consumed = 0
    interruption_state: str | None = None
    recorded_plan_sha256: str | None = None
    current = head_path
    visited: set[str] = set()
    # The head receipt's own terminal facts, carried into every return so a chain that stops early
    # still reports what the head recorded. Populated once, on the first iteration.
    head_facts: dict[str, object] = {}

    while True:
        try:
            document = inspect_receipt(current)
        except (OSError, ReceiptValidationError) as exc:
            return ReceiptChainAccounting(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed,
                interruption_state=interruption_state,
                resolved=False,
                detail=f"a receipt in the chain is missing or unreadable: {exc}",
                request_plan_sha256=recorded_plan_sha256,
                **head_facts,  # type: ignore[arg-type]
            )

        if not seen:
            head_facts = _head_receipt_facts(document)
        if recorded_plan_sha256 is None:
            recorded = document.get("request_plan_sha256")
            recorded_plan_sha256 = None if recorded is None else str(recorded)

        receipt_id = str(document["receipt_id"])
        if receipt_id in visited:
            return ReceiptChainAccounting(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed,
                interruption_state=interruption_state,
                resolved=False,
                detail="the receipt chain loops back on itself and cannot reach a first attempt",
                request_plan_sha256=recorded_plan_sha256,
                **head_facts,  # type: ignore[arg-type]
            )
        visited.add(receipt_id)
        seen.append(receipt_id)
        consumed += _as_count(document["actual_physical_attempt_count"])
        if interruption_state is None:
            state = document.get("interruption_state")
            interruption_state = None if state is None else str(state)

        predecessor = document.get("recovery_predecessor_receipt_id")
        if predecessor is None:
            # The single no-predecessor root: the one receipt whose carried-forward baseline was
            # inherited from outside the chain rather than from a receipt inside it. Added here,
            # once, which is why no other iteration of this loop touches the field.
            carried = _as_count(document.get("consumed_request_count_carried_forward", 0))
            authority = document.get("carry_in_authority_sha256")
            root_window = document.get("acquisition_window")
            root_ceiling = document.get("approved_request_ceiling")
            return ReceiptChainAccounting(
                receipt_ids=tuple(seen),
                consumed_physical_attempts=consumed + carried,
                interruption_state=interruption_state,
                resolved=True,
                detail="the chain resolves to a first attempt",
                request_plan_sha256=recorded_plan_sha256,
                root_carried_forward=carried,
                root_carry_in_authority_sha256=None if authority is None else str(authority),
                root_acquisition_window=None if root_window is None else str(root_window),
                root_approved_request_ceiling=(
                    None if root_ceiling is None else _as_count(root_ceiling)
                ),
                **head_facts,  # type: ignore[arg-type]
            )
        current = receipts_dir / f"receipt-{predecessor}.json"


def _head_receipt_facts(document: Mapping[str, object]) -> dict[str, object]:
    """The head receipt's own terminal facts, read exactly as recorded.

    Read, never derived: each value is whatever the validated receipt carries, so a field the
    schema left absent stays `None` rather than acquiring a default that would look like evidence.
    """
    attempts = document.get("actual_physical_attempt_count")
    return {
        "head_completion_status": _optional_text(document.get("completion_status")),
        "head_reason_code": _optional_text(document.get("reason_code")),
        "head_started_at_utc": _optional_text(document.get("started_at_utc")),
        "head_completed_at_utc": _optional_text(document.get("completed_at_utc")),
        "head_actual_physical_attempt_count": (None if attempts is None else _as_count(attempts)),
        "head_acquisition_window": _optional_text(document.get("acquisition_window")),
    }


def _optional_text(value: object) -> str | None:
    """A receipt field as text, or `None` where the receipt recorded nothing."""
    return None if value is None else str(value)


#: The ``ops_checkpoints`` namespace a consumed carry-in authority burns its single use in. The
#: authority's own SHA-256 completes the key, so the table's ``checkpoint_key TEXT PRIMARY KEY``
#: enforces exactly-once consumption without a migration (Decision 055 §6.3). The prefix keeps the
#: key from colliding with any other checkpoint while leaving the binding to the hash explicit.
CARRY_IN_CHECKPOINT_KEY_PREFIX: Final = "m3_2_carry_in_authority:"


def carry_in_checkpoint_key(authority_sha256: str) -> str:
    """The deterministic single-use checkpoint key for one carry-in authority."""
    return f"{CARRY_IN_CHECKPOINT_KEY_PREFIX}{authority_sha256}"


# --------------------------------------------------------------------------- #
# The fixed Decision 055 carry-in bindings
# --------------------------------------------------------------------------- #
#: Decision 055 authorizes **one** carry-in: one window, one plan, one ceiling, one historical
#: attempt, on one route, under one decision. Every value below is therefore a fixed constant rather
#: than a parameter, and that distinction is the whole control. Checking an artifact only for
#: internal self-consistency — its route allocation summing to its own declared seed, its ceiling
#: equalling whatever the operator typed — proves nothing an artifact's author could not arrange:
#: a self-consistent artifact naming seed `0`, a different registered route, or a decision that
#: authorized nothing would pass. The one-use exception exists for exactly one historical fact, so
#: the values that fact consists of are written here and compared literally.
#:
#: They are deliberately *not* derived from the plan document, the operator's arguments, or the
#: artifact itself. A derived binding is only ever as trustworthy as its input, and the inputs here
#: are precisely what a forged artifact would supply.
CARRY_IN_AUTHORITY_SCHEMA_VERSION: Final = "m3-carry-in-authority/1.0"

#: The one window a carry-in may be granted for (Decision 055 §6.1).
CARRY_IN_ACQUISITION_WINDOW: Final = "M3.2A"

#: The frozen request plan (Decision 055 §5; contract §5). Never re-derived, trimmed, substituted.
CARRY_IN_REQUEST_PLAN_SHA256: Final = (
    "19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68"
)

#: The cumulative ceiling (Decision 055 §5). Never 802, never additive, shadowed, or reset.
CARRY_IN_APPROVED_REQUEST_CEILING: Final = 801

#: The accepted historical physical-attempt consumption, `H` (Decision 055 §4, §5).
CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT: Final = 1

#: The route that one historical attempt is attributable to (Decision 055 §4 fact 2). This is a
#: binding on the *artifact*, checked by literal equality against the whole allocation mapping, so
#: an omitted route, an extra route, a substituted route, and a different count are each refused.
#: It is **not** a runtime per-route ceiling: Decision 055 §5 keeps the global
#: `PhysicalAttemptCeiling` as the sole runtime enforcement, and the remaining bulk-route headroom
#: of 5 stays an accounting figure that refuses nothing at execution time.
CARRY_IN_HISTORICAL_ROUTE_ALLOCATION: Final[Mapping[str, int]] = MappingProxyType(
    {"sec_bulk_submissions": CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT}
)

#: The decision that authorizes the carry-in mechanism itself.
CARRY_IN_AUTHORIZING_DECISION_REFERENCE: Final = "Decision 055"

#: A canonical decision reference: the literal word, one space, exactly three digits. Anything else
#: — a bare number, a file name, a title, a range, prose — is not a decision identity and cannot be
#: resolved to an accepted record.
_DECISION_REFERENCE_PATTERN: Final = re.compile(r"^Decision \d{3}$")

#: A SHA-256 identity as this repository writes them: lowercase, exactly 64 hex digits. Uppercase,
#: truncated, prefixed, and free-text "evidence" values are refused, so the orphan-adoption evidence
#: binding cannot be satisfied by a description of evidence instead of an identity for it.
_SHA256_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class CarryInFixedBindings:
    """The seven Decision 055 values that are fixed, wherever they are carried.

    Both surfaces that must agree about a carry-in carry these same seven: the authority artifact
    the operator supplies, and the `ops_checkpoints` document its consumption durably records. They
    are validated by one implementation against one set of constants, so the artifact gate and the
    later cross-check cannot drift apart or be satisfied by different values.
    """

    schema_version: str
    acquisition_window: str
    request_plan_sha256: str
    approved_request_ceiling: int
    consumed_request_count: int
    route_allocation: Mapping[str, int]
    authorizing_decision_reference: str


def carry_in_fixed_binding_disagreement(bindings: CarryInFixedBindings) -> str | None:
    """Compare one set of carried bindings against the fixed Decision 055 values.

    Returns the first disagreement, or ``None`` when every binding matches exactly. Each comparison
    is literal equality against a constant above — never a range, a minimum, a subset, or a
    consistency check between two fields the same author supplied.
    """
    if bindings.schema_version != CARRY_IN_AUTHORITY_SCHEMA_VERSION:
        return (
            f"the carry-in schema is {bindings.schema_version!r}, not "
            f"{CARRY_IN_AUTHORITY_SCHEMA_VERSION!r}"
        )
    if bindings.acquisition_window != CARRY_IN_ACQUISITION_WINDOW:
        return (
            f"the carry-in names window {bindings.acquisition_window!r}; Decision 055 authorizes a "
            f"carry-in for {CARRY_IN_ACQUISITION_WINDOW!r} alone"
        )
    if bindings.request_plan_sha256 != CARRY_IN_REQUEST_PLAN_SHA256:
        return (
            "the carry-in names a request plan other than the frozen Decision 055 plan; the plan "
            "and its hash are unchanged and are never re-derived or substituted"
        )
    if bindings.approved_request_ceiling != CARRY_IN_APPROVED_REQUEST_CEILING:
        return (
            f"the carry-in names ceiling {bindings.approved_request_ceiling}, not the accepted "
            f"cumulative {CARRY_IN_APPROVED_REQUEST_CEILING}; the ceiling is never raised, "
            f"shadowed, made additive, or reset"
        )
    if bindings.consumed_request_count != CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT:
        return (
            f"the carry-in declares a historical consumed baseline of "
            f"{bindings.consumed_request_count}, not the accepted "
            f"{CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT}; the accepted historical consumption is "
            f"a fact about what already happened, not a value an artifact may state"
        )
    if dict(bindings.route_allocation) != dict(CARRY_IN_HISTORICAL_ROUTE_ALLOCATION):
        return (
            f"the carry-in allocates the historical attempt as "
            f"{dict(sorted(bindings.route_allocation.items()))!r}, not the accepted "
            f"{dict(CARRY_IN_HISTORICAL_ROUTE_ALLOCATION)!r}; the allocation is compared whole, so "
            f"a substituted route, an extra route, and an omitted route are each refused"
        )
    if bindings.authorizing_decision_reference != CARRY_IN_AUTHORIZING_DECISION_REFERENCE:
        return (
            f"the carry-in cites {bindings.authorizing_decision_reference!r} as its authorizing "
            f"decision, not {CARRY_IN_AUTHORIZING_DECISION_REFERENCE!r}"
        )
    return None


def carry_in_orphan_reference_disagreement(
    decision_reference: str,
    evidence_sha256: str,
) -> str | None:
    """Check the two later-act bindings a carry-in authority must name (Decision 055 §6.1, §9).

    Path B requires a **separately authorized** orphan adoption to have been executed, verified, and
    accepted before a carry-in may be minted or consumed. The authority binds that later act by
    naming its decision and its evidence identity. Neither can be verified here — the adoption has
    not happened, and this module opens no operational state to look — so what is enforced is that
    both are *resolvable identities* rather than free text, and that the adoption decision is a
    genuinely different record from the one authorizing the mechanism.

    Returns the first disagreement, or ``None``.
    """
    if not _DECISION_REFERENCE_PATTERN.match(decision_reference):
        return (
            f"the orphan-adoption decision reference {decision_reference!r} is not a canonical "
            f"'Decision NNN' identity, so it names no resolvable accepted record"
        )
    if decision_reference == CARRY_IN_AUTHORIZING_DECISION_REFERENCE:
        return (
            f"the carry-in names {CARRY_IN_AUTHORIZING_DECISION_REFERENCE!r} as its own "
            f"orphan-adoption decision, but Decision 055 §9 expressly neither designs nor performs "
            f"that adoption; it must be the separately authorized later Path-B act"
        )
    if not _SHA256_PATTERN.match(evidence_sha256):
        return (
            "the orphan-adoption evidence identity is not a lowercase 64-hex SHA-256, so it names "
            "no verifiable artifact"
        )
    return None


def carry_in_checkpoint_disagreement(
    connection: sqlite3.Connection,
    chain: ReceiptChainAccounting,
) -> str | None:
    """Cross-check a chain's carry-in root against the durable catalog checkpoint.

    Decision 055 §7.5: the catalog checkpoint and the root receipt **mutually cross-check**, and a
    missing or mismatched authority or carry-in is ``UNDETERMINED`` and cannot authorize
    continuation. Returns the disagreement, or ``None`` when the two agree — including the ordinary
    case of a zero-baseline root, which has nothing to cross-check.

    Both directions are checked, because either one alone can be forged by editing the other:

    * a root claiming a non-zero baseline with **no** authority hash has no durable record of where
      that baseline came from;
    * a root naming an authority whose checkpoint is **absent** claims a burn that never committed;
    * a checkpoint whose recorded baseline **differs** from the receipt's means the two surfaces
      disagree about how much was carried in.

    The checkpoint is validated as the **whole closed document** it is specified to be, not merely
    read for the one figure being compared. Finding a row under the expected key proves only that
    *something* was written there; the row's own contents still have to be the canonical record of
    the accepted carry-in. A checkpoint whose embedded authority hash, plan, window, ceiling,
    decision, route allocation, or authorized run is wrong — or that is truncated, carries an extra
    field, is not stored as the canonical serialization of its own document, or is not parseable at
    all — describes a burn that did not happen as recorded, and no baseline can be established
    from it.

    Three layers, in widening order: the record must be **coherent**, it must **agree with the root
    receipt**, and it must be **the accepted Decision 055 carry-in** — window ``M3.2A``, the frozen
    plan, ceiling ``801``, seed ``1`` on ``sec_bulk_submissions``, ``Decision 055``. The third is
    not implied by the second: a forged root and a checkpoint forged to match it agree with each
    other perfectly. Both surfaces are held against the same constants the artifact gate uses, by
    the same validator.
    """
    if chain.root_carry_in_authority_sha256 is None:
        if chain.root_carried_forward:
            return (
                "the receipt chain's root claims a carried-forward baseline of "
                f"{chain.root_carried_forward} but names no carry-in authority, so the baseline "
                "has no durable record of the authority it was carried in under"
            )
        return None

    authority_sha256 = chain.root_carry_in_authority_sha256
    row = connection.execute(
        "SELECT checkpoint_value FROM ops_checkpoints WHERE checkpoint_key = ?",
        (carry_in_checkpoint_key(authority_sha256),),
    ).fetchone()
    if row is None:
        return (
            "the receipt chain's root names a carry-in authority that the operational catalog "
            "records no consumption checkpoint for, so the authority's single use cannot be "
            "confirmed to have committed"
        )
    checkpoint, malformed = _carry_in_checkpoint_document(row[0])
    if checkpoint is None:
        return malformed

    # Internal validity first: a coherent record of the burn it claims — a real schema, a
    # resolvable decision, and an allocation that accounts for the baseline it says was carried.
    # These are the narrower faults, and naming them precisely is more use to an operator than the
    # blanket "this is not the accepted carry-in" the fixed comparison further down would give.
    if checkpoint.schema_version != CARRY_IN_AUTHORITY_SCHEMA_VERSION:
        return (
            f"the carry-in consumption checkpoint declares schema "
            f"{checkpoint.schema_version!r}, not {CARRY_IN_AUTHORITY_SCHEMA_VERSION!r}"
        )
    if not _DECISION_REFERENCE_PATTERN.match(checkpoint.authorizing_decision_reference):
        return (
            f"the carry-in consumption checkpoint cites "
            f"{checkpoint.authorizing_decision_reference!r} as its authorizing decision, which is "
            f"not a canonical 'Decision NNN' identity"
        )
    allocated = sum(checkpoint.historical_route_allocation.values())
    if allocated != checkpoint.consumed_request_count_carried_forward:
        return (
            f"the carry-in consumption checkpoint allocates {allocated} historical attempt(s) "
            f"across routes but records a carried-forward baseline of "
            f"{checkpoint.consumed_request_count_carried_forward}; the record contradicts itself"
        )
    for source_id in checkpoint.historical_route_allocation:
        if source_id not in SOURCES:
            return (
                f"the carry-in consumption checkpoint allocates historical consumption to "
                f"{source_id!r}, which is not a registered source route"
            )
    if checkpoint.acquisition_window not in ACQUISITION_WINDOWS:
        return (
            f"the carry-in consumption checkpoint names window "
            f"{checkpoint.acquisition_window!r}, which is not an accepted acquisition window"
        )
    if checkpoint.consumed_request_count_carried_forward > checkpoint.approved_request_ceiling:
        return (
            "the carry-in consumption checkpoint records a carried-forward baseline greater than "
            "the ceiling it names, so no further physical request could lawfully have occurred"
        )

    # The key/document relationship. A row filed under one authority's deterministic key whose body
    # names another is a checkpoint that never described the burn it is standing in for.
    if checkpoint.authority_sha256 != authority_sha256:
        return (
            "the carry-in consumption checkpoint is stored under one authority's deterministic key "
            "but its document names a different authority, so the recorded consumption does not "
            "belong to the authority the chain's root claims"
        )
    if checkpoint.consumed_request_count_carried_forward != chain.root_carried_forward:
        return (
            f"the carry-in consumption checkpoint records a carried-forward baseline of "
            f"{checkpoint.consumed_request_count_carried_forward} but the chain's root receipt "
            f"records {chain.root_carried_forward}; the catalog and the receipt disagree"
        )
    if (
        chain.request_plan_sha256 is not None
        and chain.request_plan_sha256 != checkpoint.request_plan_sha256
    ):
        return (
            "the carry-in consumption checkpoint and the receipt chain name different request "
            "plans, so the baseline was not carried in under the plan the chain executed"
        )
    if (
        chain.root_acquisition_window is not None
        and chain.root_acquisition_window != checkpoint.acquisition_window
    ):
        return (
            "the carry-in consumption checkpoint and the chain's root receipt name different "
            "acquisition windows, so the recorded consumption is not this root's"
        )
    if (
        chain.root_approved_request_ceiling is not None
        and chain.root_approved_request_ceiling != checkpoint.approved_request_ceiling
    ):
        return (
            "the carry-in consumption checkpoint and the chain's root receipt name different "
            "approved ceilings; the cumulative ceiling is never reset, raised, or shadowed"
        )

    # The fixed Decision 055 values, compared literally against the same constants the artifact
    # gate compares against. Everything above establishes that the checkpoint is coherent and that
    # it agrees with the root receipt — but agreement between two surfaces proves only that whoever
    # produced one could produce the other. A forged root and a matching forged checkpoint agree
    # perfectly and are still not the accepted carry-in, so the accepted carry-in is what the
    # durable record is finally held against.
    disagreement = carry_in_fixed_binding_disagreement(
        CarryInFixedBindings(
            schema_version=checkpoint.schema_version,
            acquisition_window=checkpoint.acquisition_window,
            request_plan_sha256=checkpoint.request_plan_sha256,
            approved_request_ceiling=checkpoint.approved_request_ceiling,
            consumed_request_count=checkpoint.consumed_request_count_carried_forward,
            route_allocation=checkpoint.historical_route_allocation,
            authorizing_decision_reference=checkpoint.authorizing_decision_reference,
        )
    )
    if disagreement is not None:
        return (
            f"the carry-in consumption checkpoint does not record the accepted Decision 055 "
            f"carry-in: {disagreement}"
        )
    return _carry_in_run_disagreement(connection, checkpoint)


@dataclass(frozen=True, slots=True)
class _CarryInCheckpoint:
    """One parsed, shape-checked carry-in consumption checkpoint document (data dictionary §5B).

    Narrowing to this type is what lets the cross-check compare *values*. A validator that reached
    into a raw mapping would have to re-prove a shape at every comparison, and the one comparison
    that forgot would be the one a malformed row walked through.
    """

    acquisition_window: str
    approved_request_ceiling: int
    authority_sha256: str
    authorized_census_run_id: str
    authorizing_decision_reference: str
    consumed_request_count_carried_forward: int
    historical_route_allocation: Mapping[str, int]
    request_plan_sha256: str
    schema_version: str


#: The exact field set of a carry-in consumption checkpoint document. Closed in both directions: a
#: missing field leaves the record unable to support the cross-check it exists for, and an extra one
#: means the row is not the document this validator is reading.
_CARRY_IN_CHECKPOINT_TEXT_FIELDS: Final[tuple[str, ...]] = (
    "acquisition_window",
    "authority_sha256",
    "authorized_census_run_id",
    "authorizing_decision_reference",
    "request_plan_sha256",
    "schema_version",
)
_CARRY_IN_CHECKPOINT_COUNT_FIELDS: Final[tuple[str, ...]] = (
    "approved_request_ceiling",
    "consumed_request_count_carried_forward",
)
_CARRY_IN_CHECKPOINT_FIELDS: Final[frozenset[str]] = frozenset(
    (*_CARRY_IN_CHECKPOINT_TEXT_FIELDS, *_CARRY_IN_CHECKPOINT_COUNT_FIELDS)
) | {"historical_route_allocation"}


def _noncanonical_checkpoint_reason(stored: object, parsed: Mapping[str, object]) -> str | None:
    """Whether the stored TEXT is exactly the canonical serialization of what it parsed to.

    Data dictionary §5B specifies ``checkpoint_value`` as **canonical JSON**, and
    ``CarryInAuthority.checkpoint_value`` is the only thing that lawfully writes one — so the
    stored bytes of a real burn are, byte for byte, ``canonical_bytes`` of the document. Requiring
    that equality is what turns "is this document coherent" into "is this the record a consumption
    wrote", and it is the only check that sees the *encoding* rather than the parse result:

    * pretty-printed, re-indented, or re-ordered bytes parse to the same mapping and are refused,
      because no lawful writer produced them;
    * a duplicate-key encoding is refused, because ``json.loads`` silently keeps the last value and
      the discarded one would never be seen by any comparison below.

    Returns the disagreement, or ``None`` when the encoding is canonical.
    """
    try:
        canonical = canonical_bytes(parsed).decode()
    except (ReceiptValidationError, TypeError):
        return (
            "the carry-in consumption checkpoint does not serialize to canonical JSON at all, so "
            "it is not a record any lawful consumption wrote"
        )
    if str(stored) != canonical:
        return (
            "the carry-in consumption checkpoint is not stored in canonical form; a consumption "
            "writes the canonical serialization of the closed document, so bytes that merely "
            "parse to the right fields — re-indented, re-ordered, or carrying a duplicate key "
            "whose discarded value nothing here would ever see — record no burn this catalog made"
        )
    return None


def _carry_in_checkpoint_document(
    stored: object, *, require_canonical: bool = True
) -> tuple[_CarryInCheckpoint | None, str]:
    """Parse and shape-check one stored checkpoint value, or say why it is not the document.

    Returns ``(checkpoint, "")`` when the stored value is the closed document with every field of
    the expected type, and ``(None, reason)`` otherwise. A truncated write, a hand-edited row, an
    added field, and a value that is not JSON at all each stop here rather than reaching a
    comparison they might coincidence their way past.

    ``require_canonical`` is off only for the duplicate-run scan, which asks a different question of
    *other* rows — "does anything else claim this run?" — and must keep answering it for a row that
    is malformed in a way this validator would otherwise discard. The subject checkpoint is always
    read canonically.
    """
    try:
        parsed = json.loads(str(stored))
    except ValueError:
        return None, "the carry-in authority's consumption checkpoint is not readable JSON"
    if not isinstance(parsed, dict):
        return None, "the carry-in authority's consumption checkpoint is not a JSON object"
    present = set(parsed)
    if missing := sorted(_CARRY_IN_CHECKPOINT_FIELDS - present):
        return None, (
            f"the carry-in consumption checkpoint is missing required field(s): "
            f"{', '.join(missing)}"
        )
    if unexpected := sorted(present - _CARRY_IN_CHECKPOINT_FIELDS):
        return None, (
            f"the carry-in consumption checkpoint carries unpermitted field(s): "
            f"{', '.join(unexpected)}; the record is a closed document"
        )
    if require_canonical and (reason := _noncanonical_checkpoint_reason(stored, parsed)):
        return None, reason

    text: dict[str, str] = {}
    for name in _CARRY_IN_CHECKPOINT_TEXT_FIELDS:
        value = parsed[name]
        if not isinstance(value, str) or not value.strip():
            return None, (
                f"the carry-in consumption checkpoint's {name} is not a non-empty string, so the "
                f"record is malformed"
            )
        text[name] = value
    counts: dict[str, int] = {}
    for name in _CARRY_IN_CHECKPOINT_COUNT_FIELDS:
        value = parsed[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None, (
                f"the carry-in consumption checkpoint's {name} is not a non-negative integer, so "
                f"the record is malformed"
            )
        counts[name] = value
    raw_allocation = parsed["historical_route_allocation"]
    if not isinstance(raw_allocation, dict) or not raw_allocation:
        return None, (
            "the carry-in consumption checkpoint's historical_route_allocation is not a non-empty "
            "object, so the record is malformed"
        )
    allocation: dict[str, int] = {}
    for source_id, count in raw_allocation.items():
        if not isinstance(source_id, str) or not source_id.strip():
            return None, (
                "the carry-in consumption checkpoint's historical_route_allocation is not a map "
                "keyed by source identifiers, so the record is malformed"
            )
        # A negative count is not a small error to tolerate: it lets an allocation sum to a
        # plausible baseline while charging an impossible number of attempts to some route, so the
        # self-consistency comparison downstream would pass on arithmetic no consumption produced.
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            return None, (
                f"the carry-in consumption checkpoint allocates {count!r} attempt(s) to "
                f"{source_id!r}; every route allocation is a non-negative integer count, so the "
                f"record is malformed"
            )
        allocation[source_id] = count

    return (
        _CarryInCheckpoint(
            acquisition_window=text["acquisition_window"],
            approved_request_ceiling=counts["approved_request_ceiling"],
            authority_sha256=text["authority_sha256"],
            authorized_census_run_id=text["authorized_census_run_id"],
            authorizing_decision_reference=text["authorizing_decision_reference"],
            consumed_request_count_carried_forward=counts["consumed_request_count_carried_forward"],
            historical_route_allocation=allocation,
            request_plan_sha256=text["request_plan_sha256"],
            schema_version=text["schema_version"],
        ),
        "",
    )


def _carry_in_run_disagreement(
    connection: sqlite3.Connection,
    checkpoint: _CarryInCheckpoint,
) -> str | None:
    """Cross-check the checkpoint's authorized run against durable catalog state.

    The receipt schema carries no run identity and Decision 055 authorized no new receipt field, so
    the run the checkpoint names is proved against the ``ops_ingestion_jobs`` row it must have been
    registered alongside. The two writes commit in one transaction, so that run existing as a
    governed acquisition run in the checkpoint's own window is exactly the durable consequence a
    truthful checkpoint has, and its absence is a state no lawful consumption produces.

    Also refuses the impossible state of two distinct carry-in checkpoints claiming the same
    authorized run: a run is registered exactly once, so at most one authority can have burned
    alongside it.
    """
    # Local import: `acquisition` imports this module, so importing its job-kind constant at module
    # scope would be a cycle. Both modules are fully initialised by call time.
    from disclosure_drift.m3.acquisition import ACQUISITION_JOB_KIND

    row = connection.execute(
        "SELECT job_kind, stage FROM ops_ingestion_jobs WHERE job_id = ?",
        (checkpoint.authorized_census_run_id,),
    ).fetchone()
    if row is None:
        return (
            "the carry-in consumption checkpoint names an authorized run that the catalog records "
            "no registered job for, but an authority burns in the same transaction that registers "
            "its run, so the two cannot lawfully disagree"
        )
    if str(row[0]) != ACQUISITION_JOB_KIND or str(row[1]) != checkpoint.acquisition_window:
        return (
            "the carry-in consumption checkpoint's authorized run is not registered as a governed "
            "acquisition run in the checkpoint's own window, so the recorded consumption does not "
            "describe the run it names"
        )

    own_key = carry_in_checkpoint_key(checkpoint.authority_sha256)
    for key, value in connection.execute(
        "SELECT checkpoint_key, checkpoint_value FROM ops_checkpoints"
    ).fetchall():
        if not str(key).startswith(CARRY_IN_CHECKPOINT_KEY_PREFIX) or str(key) == own_key:
            continue
        # Read without the canonical-encoding requirement on purpose. The question asked of another
        # row is whether it *claims* this run, and a row that claims it while being noncanonical is
        # more suspicious, not less — discarding it here would let a hand-written duplicate escape
        # the one refusal that exists for it.
        other, _ = _carry_in_checkpoint_document(value, require_canonical=False)
        if other is not None and other.authorized_census_run_id == (
            checkpoint.authorized_census_run_id
        ):
            return (
                "more than one carry-in consumption checkpoint claims the same authorized run; a "
                "run is registered exactly once, so at most one authority can have burned "
                "alongside it and this state is not reachable by any lawful consumption"
            )
    return None


# --------------------------------------------------------------------------- #
# The fixed Decision 062 predecessor -> successor plan transition
# --------------------------------------------------------------------------- #
#: Condition 8.10 asks whether the plan hash is **unchanged**, and for every ordinary continuation
#: it must stay that way: resuming against a different plan would carry a consumed count forward
#: against a budget nobody approved. Decision 062 §7 opens exactly one bounded exception, for one
#: external fact — SEC retired the `sec_sic_code_list` exact path mid-window — and the constants
#: below are what keep it bounded.
#:
#: They are written literally, for the same reason the Decision 055 carry-in bindings above are: a
#: transition validated only for *internal consistency* would admit any pair of plans an author
#: could arrange to be consistent, which is precisely what "resume with another plan" means. Every
#: value here is compared by literal equality, so this mechanism can authorize the one substitution
#: Decision 062 names and nothing else — not a second substitution, not another route, not another
#: window, not another ceiling, and not an arbitrary URL.
PLAN_TRANSITION_DECISION_REFERENCE: Final = "Decision 062"

#: The predecessor plan: the frozen M3.2A plan the T6 invocation executed.
PLAN_TRANSITION_PREDECESSOR_PLAN_SHA256: Final = (
    "19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68"
)

#: The successor plan: the same window, inputs, quarters, routes, counts, and ceiling, bound to the
#: successor source registry. It differs from the predecessor in one recorded field, and that field
#: moves exactly one logical request identity.
PLAN_TRANSITION_SUCCESSOR_PLAN_SHA256: Final = (
    "f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a"
)

#: The one route whose identity Decision 062 substitutes.
PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID: Final = "sec_sic_code_list"

#: The retired exact URL, and the successor SEC published in its place.
PLAN_TRANSITION_OLD_URL: Final = (
    "https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial"
    "-classification-sic-code-list"
)
PLAN_TRANSITION_NEW_URL: Final = (
    "https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list"
)

#: The exact size of the substitution set. Not a maximum: a transition substituting zero identities
#: is not this transition, and one substituting two is a capability Decision 062 refused to create.
PLAN_TRANSITION_SUBSTITUTION_COUNT: Final = 1

#: The window, ceiling, and registry versions the transition is bound to on both sides.
PLAN_TRANSITION_ACQUISITION_WINDOW: Final = "M3.2A"
PLAN_TRANSITION_APPROVED_REQUEST_CEILING: Final = 801
PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION: Final = "m2.2-source-registry/1.0"
PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION: Final = "m2.2-source-registry/1.1"


@dataclass(frozen=True, slots=True)
class PlanTransitionAuthority:
    """One verified predecessor→successor plan transition.

    Constructing this type **is** the assertion that the transition is Decision 062's, so the
    constructor validates against the frozen constants rather than trusting its caller. A surface
    that receives one therefore knows the pair was checked, and a hand-built authority naming any
    other plan, route, or URL raises here instead of widening condition 8.10.

    The full seventeen-condition check — coverage inputs, route counts, `A_reachable` values,
    attempt budget, and the derived request-identity comparison — lives with the plan expansion in
    the acquisition driver and produces this object. This type is the *result* of that check, not a
    substitute for it.
    """

    predecessor_plan_sha256: str
    successor_plan_sha256: str
    substituted_source_id: str
    old_url: str
    new_url: str
    decision_reference: str = PLAN_TRANSITION_DECISION_REFERENCE

    def __post_init__(self) -> None:
        """Refuse any transition that is not literally the one Decision 062 authorizes."""
        expected = (
            ("decision reference", self.decision_reference, PLAN_TRANSITION_DECISION_REFERENCE),
            (
                "predecessor plan",
                self.predecessor_plan_sha256,
                PLAN_TRANSITION_PREDECESSOR_PLAN_SHA256,
            ),
            ("successor plan", self.successor_plan_sha256, PLAN_TRANSITION_SUCCESSOR_PLAN_SHA256),
            (
                "substituted source",
                self.substituted_source_id,
                PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID,
            ),
            ("old URL", self.old_url, PLAN_TRANSITION_OLD_URL),
            ("new URL", self.new_url, PLAN_TRANSITION_NEW_URL),
        )
        for label, found, required in expected:
            if found != required:
                message = (
                    f"a plan transition may name only the one substitution "
                    f"{PLAN_TRANSITION_DECISION_REFERENCE} authorizes; its {label} is {found!r}, "
                    f"not {required!r}"
                )
                raise RecoveryInspectionError(message)

    def authorizes(self, chain_plan_sha256: str | None, supplied_plan_sha256: str) -> bool:
        """Whether this authority covers moving from the chain's plan to the supplied one.

        Directional on purpose: it authorizes predecessor→successor and never the reverse, so a
        transition cannot be used to resume a successor-plan run against the retired predecessor.
        """
        return (
            chain_plan_sha256 == self.predecessor_plan_sha256
            and supplied_plan_sha256 == self.successor_plan_sha256
        )


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


# --------------------------------------------------------------------------- #
# Condition 8.2 — establishing a terminal state that is not an interruption
# --------------------------------------------------------------------------- #
#: Completion statuses that end an invocation terminally **without** it being an interruption
#: (Decision 062 §3). A receipt recording one of these is not incomplete evidence: the run reached a
#: recorded, non-successful end and said why. `complete` is excluded because a successful window has
#: nothing to recover, and `interrupted` is excluded because it takes the interruption-state path.
_TERMINAL_NON_SUCCESS_STATUSES: Final[frozenset[str]] = frozenset(
    {"failed", "stopped_at_ceiling", "stopped_by_gate"}
)

#: The truthful `ops_ingestion_jobs.job_state` for each terminal non-success completion status —
#: the same mapping the driver applies when it closes a run, restated here as the value the run row
#: is *required to already hold*. A row in any other state disagrees with the receipt beside it, and
#: disagreement is never reconciled by preferring one surface.
_TERMINAL_STATUS_JOB_STATE: Final[Mapping[str, str]] = MappingProxyType(
    {"failed": "failed", "stopped_at_ceiling": "failed", "stopped_by_gate": "failed"}
)

#: The `ops_ingestion_jobs.job_kind` an M3.2 acquisition run is registered under.
_ACQUISITION_JOB_KIND: Final = "m3_2_acquisition"


def establish_terminal_state(
    connection: sqlite3.Connection,
    walk: ReceiptChainAccounting,
    integrity_passed: bool,
    store: _StoreState,
) -> tuple[bool, str]:
    """Whether a terminal, non-interrupted end state is **established** by durable evidence.

    Decision 062 §3 generalizes condition 8.2 from "the interruption state is established" to "the
    terminal *or* interruption state is established, not guessed". The reason is structural: the
    governing live-failure rule covers interrupted, killed, crashed, failed, gate-stopped,
    ceiling-stopped, and uncertain operations alike, but the original predicate could only ever be
    met by an `interruption_state` field — which a correctly-written terminal failure receipt does
    not carry and must never be given one. Left unchanged, the predicate made safe recovery
    structurally impossible for exactly the cases that ended most cleanly.

    This is **not** a relaxation. The interruption path is unchanged, and this path demands *more*
    evidence, not less: all ten conditions below must hold, each read from a durable surface, and
    the first that does not returns the refusal. A receiptless, crashed, killed, or genuinely
    uncertain state satisfies none of them and still reaches `UNDETERMINED`.

    Args:
        connection: the read-only catalog connection.
        walk: the resolved receipt chain, carrying the head receipt's own terminal facts.
        integrity_passed: whether the catalog passed quick, integrity, and foreign-key checks.
        store: the committed-row versus stored-object comparison.

    Returns:
        ``(established, detail)`` — the detail states what was established, or what refused it.
    """
    status = walk.head_completion_status
    # 1. The receipt is valid and immutable. Validity is proved by the walk: every document on the
    #    chain came back from `inspect_receipt`, which validates the schema before returning, so a
    #    head that carries no status could not be read as a receipt at all. Immutability is a
    #    property of this module — it opens the catalog `query_only` and imports no writer — not a
    #    claim to re-derive here.
    if status is None:
        return False, "the head receipt records no completion status, so nothing is established"

    # 2. The completion status is terminal and non-successful.
    if status not in _TERMINAL_NON_SUCCESS_STATUSES:
        return False, (
            f"the head receipt records completion status {status!r}, which is not one of the "
            f"terminal non-success statuses {sorted(_TERMINAL_NON_SUCCESS_STATUSES)}"
        )

    # 3. A registered reason code is present. An unregistered code is prose, not a classification.
    if walk.head_reason_code is None:
        return False, (
            f"the head receipt records completion status {status!r} but no reason code, so why "
            f"the run ended terminally is not established"
        )
    if walk.head_reason_code not in REASON_CODES:
        return False, (
            f"the head receipt's reason code {walk.head_reason_code!r} is not registered, so the "
            f"terminal cause cannot be resolved to an accepted classification"
        )

    # 5. Both boundary instants are present. Checked before the run-row join, which needs them.
    if walk.head_started_at_utc is None or walk.head_completed_at_utc is None:
        return False, (
            "the head receipt does not carry both a started and a completed instant, so the run "
            "it describes cannot be identified without guessing"
        )

    # 4. The run row is terminal and agrees with the receipt. The receipt carries no run id by
    #    design, so the join is on the facts both surfaces independently recorded: window, start,
    #    and end. Exactly one row must match — zero means no registered run describes this receipt,
    #    and two would make "the run" ambiguous, which is not an established state.
    job_id, detail = _terminal_run_row_agreement(connection, walk, status)
    if job_id is None:
        return False, detail

    # 6. The durable attempt count resolves: the pre-send ledger and the receipt agree exactly.
    attempts_detail = _durable_attempt_count_disagreement(connection, walk, job_id)
    if attempts_detail is not None:
        return False, attempts_detail

    # 7. No uncertain commit exists. A recovery state still `blocked` is precisely a mutation whose
    #    outcome is unadjudicated, so terminality cannot be established over it.
    unresolved = _unresolved_recovery_states(connection)
    if unresolved:
        return False, (
            f"{unresolved} recovery state(s) remain blocked, so at least one commit's outcome is "
            f"still uncertain and the terminal state is not established"
        )

    # 8. No orphan, row-without-object, or partial ambiguity exists. Note this is stricter than
    #    condition 8.6, which tolerates an unpromoted `.part` as ordinary: for a run still running
    #    a spool in flight is ordinary, but beside a *terminal* receipt any `.part` is an
    #    unexplained mid-write and the end state is not established.
    ambiguity = _store_ambiguity(store)
    if ambiguity is not None:
        return False, ambiguity

    # 9. The predecessor chain resolves. Without it the receipt describes an end whose beginning is
    #    unknown, and the cumulative consumed count with it.
    if not walk.resolved:
        return False, f"the receipt chain does not resolve to a first attempt: {walk.detail}"

    # 10. Catalog integrity passes.
    if not integrity_passed:
        return False, (
            "the catalog does not pass its quick, integrity, and foreign-key checks, so no state "
            "read from it establishes anything"
        )

    return True, (
        f"terminal state established: the head receipt records {status!r} with registered reason "
        f"{walk.head_reason_code!r}, {detail}, the chain resolves, and the catalog carries no "
        f"uncertain commit, orphan, missing object, or partial"
    )


def _terminal_run_row_agreement(
    connection: sqlite3.Connection,
    walk: ReceiptChainAccounting,
    status: str,
) -> tuple[str | None, str]:
    """Match the head receipt to exactly one terminal run row that agrees with it.

    Returns the matched run id and a describing detail, or ``(None, refusal)``.
    """
    rows = connection.execute(
        "SELECT job_id, job_state FROM ops_ingestion_jobs "
        "WHERE job_kind = ? AND stage = ? AND started_at_utc = ? AND finished_at_utc = ? "
        "ORDER BY job_id",
        (
            _ACQUISITION_JOB_KIND,
            walk.head_acquisition_window,
            walk.head_started_at_utc,
            walk.head_completed_at_utc,
        ),
    ).fetchall()
    if len(rows) != 1:
        return None, (
            f"{len(rows)} registered acquisition run(s) match the head receipt's window and "
            f"boundary instants; exactly one must, or the run the receipt describes is not "
            f"identified"
        )
    job_id, job_state = str(rows[0][0]), str(rows[0][1])
    expected = _TERMINAL_STATUS_JOB_STATE[status]
    if job_state != expected:
        return None, (
            f"run {job_id} is in state {job_state!r} but its receipt records {status!r}, whose "
            f"truthful run state is {expected!r}; the two surfaces disagree and neither is edited "
            f"to match the other"
        )
    return job_id, f"run {job_id} is terminal in state {job_state!r} and agrees with the receipt"


def _durable_attempt_count_disagreement(
    connection: sqlite3.Connection,
    walk: ReceiptChainAccounting,
    job_id: str,
) -> str | None:
    """Why the pre-send attempt ledger and the receipt disagree, or ``None`` when they agree."""
    if walk.head_actual_physical_attempt_count is None:
        return "the head receipt records no physical attempt count"
    row = connection.execute(
        "SELECT COUNT(*) FROM ops_retrieval_attempts WHERE job_id = ?", (job_id,)
    ).fetchone()
    ledger = int(row[0])
    if ledger != walk.head_actual_physical_attempt_count:
        return (
            f"the pre-send ledger records {ledger} attempt(s) for run {job_id} but the receipt "
            f"records {walk.head_actual_physical_attempt_count}; the durable attempt count does "
            f"not resolve"
        )
    return None


def _store_ambiguity(store: _StoreState) -> str | None:
    """The first store-level ambiguity that prevents establishing a terminal end state."""
    if store.rows_without_object:
        return (
            f"{len(store.rows_without_object)} committed row(s) have no stored object, so what "
            f"the run persisted before ending is not established"
        )
    if store.orphan_object_count:
        return (
            f"{store.orphan_object_count} stored object(s) have no committed row, so whether "
            f"their write completed is not established"
        )
    if store.rows_pointing_at_partials:
        return (
            f"{len(store.rows_pointing_at_partials)} committed row(s) point at a partial file, so "
            f"a partial was treated as complete"
        )
    if store.partial_file_count:
        return (
            f"{store.partial_file_count} unpromoted partial file(s) remain beside a terminal "
            f"receipt, so a mid-write is unexplained and the end state is not established"
        )
    return None


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
    plan_transition: PlanTransitionAuthority | None = None,
) -> RecoveryState:
    """Determine whether an interrupted run may safely resume. Writes nothing.

    Args:
        plan: the approved request plan the interrupted run was executing.
        receipt_chain_head: path to the most recent receipt; predecessors resolve beside it.
        catalog_path: the SQLite catalog to inspect read-only.
        data_root: the data root whose raw store is inspected.
        plan_transition: a verified Decision 062 predecessor→successor plan transition, where the
            caller supplies the successor of a plan the chain recorded. Omitted by default, so
            condition 8.10 asks for an unchanged hash unless an authority is explicitly presented.

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
    walk = walk_receipt_chain(Path(receipt_chain_head))

    with read_only_catalog(Path(catalog_path)) as connection:
        integrity = integrity_report(connection)
        store = _inspect_store(connection, tree)
        projection = validate_audit_projection(connection, tree.audit / _PROJECTION_FILENAME)
        unresolved_states = _unresolved_recovery_states(connection)
        selection_runs = _in_flight_selection_runs(connection)
        carry_in_disagreement = carry_in_checkpoint_disagreement(connection, walk)
        # Condition 8.2's second path. Evaluated only where the first does not already settle it,
        # so an interrupted chain reaches exactly the predicate it always did and the terminal
        # path can never quietly satisfy an interruption.
        terminal_established, terminal_detail = (
            (False, "")
            if walk.interruption_state is not None
            else establish_terminal_state(connection, walk, integrity.passed, store)
        )

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
            "The terminal or interruption state is established, not guessed",
            _MET if walk.interruption_state is not None or terminal_established else _NOT_MET,
            _condition_8_2_detail(walk, terminal_established, terminal_detail),
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
            "The plan hash is unchanged, or moves under an explicit owner plan transition",
            _plan_hash_status(plan, walk, plan_transition),
            _plan_hash_detail(plan, walk, plan_transition),
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
        ConditionResult(
            "8.12",
            "The chain's carry-in root agrees with the catalog's consumption checkpoint",
            _NOT_APPLICABLE
            if walk.root_carry_in_authority_sha256 is None and not walk.root_carried_forward
            else (_MET if carry_in_disagreement is None else _NOT_MET),
            (
                "the chain's root carries no baseline, so there is no carry-in to cross-check"
                if walk.root_carry_in_authority_sha256 is None and not walk.root_carried_forward
                else carry_in_disagreement
                or (
                    f"the root's carried-forward baseline of {walk.root_carried_forward} matches "
                    f"the authority's durable consumption checkpoint"
                )
            ),
        ),
    )

    determination, basis, action = _determine(
        conditions,
        walk=walk,
        store=store,
        carry_in_disagreement=carry_in_disagreement,
    )
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


def _condition_8_2_detail(
    walk: ReceiptChainAccounting,
    terminal_established: bool,
    terminal_detail: str,
) -> str:
    """State which of the two paths settled condition 8.2, or why neither did."""
    if walk.interruption_state is not None:
        return f"interruption state recorded as {walk.interruption_state!r} by the receipt schema"
    if terminal_established:
        return terminal_detail
    return (
        f"no receipt on the chain records an interruption state, and no terminal end state is "
        f"established either: {terminal_detail}"
    )


def _headroom(
    plan: RequestPlan, walk: ReceiptChainAccounting, store: _StoreState
) -> tuple[bool, str]:
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


def _plan_hash_status(
    plan: RequestPlan,
    walk: ReceiptChainAccounting,
    transition: PlanTransitionAuthority | None = None,
) -> str:
    """Whether the supplied plan is the one the interrupted run was executing.

    Resuming against a *different* plan than the one the run consumed would carry a consumed count
    forward against a budget nobody approved, so a mismatch is not met. A chain that records no plan
    hash also fails: the condition asks whether the hash is unchanged, and an absent hash cannot
    establish that it is.

    A verified Decision 062 transition is the single exception, and it is not a weakening of the
    rule: the authority is only constructible for one named pair of plan hashes, and the plans it
    connects are proved to differ in exactly one request identity before it exists. Everything the
    condition protects — the same window, ceiling, route counts, and attempt budget — is unchanged
    across the pair, so the consumed count still carries forward against the budget that was
    approved.
    """
    if walk.request_plan_sha256 is None:
        return _NOT_MET
    if walk.request_plan_sha256 == plan.request_plan_sha256:
        return _MET
    if transition is not None and transition.authorizes(
        walk.request_plan_sha256, plan.request_plan_sha256
    ):
        return _MET
    return _NOT_MET


def _plan_hash_detail(
    plan: RequestPlan,
    walk: ReceiptChainAccounting,
    transition: PlanTransitionAuthority | None = None,
) -> str:
    """State what was compared, without assuming it matched."""
    if walk.request_plan_sha256 is None:
        return (
            "no receipt on the chain records a request_plan_sha256, so it cannot be established "
            "that the plan is unchanged"
        )
    if walk.request_plan_sha256 == plan.request_plan_sha256:
        return f"the chain and the supplied plan agree on {plan.request_plan_sha256}"
    if transition is not None and transition.authorizes(
        walk.request_plan_sha256, plan.request_plan_sha256
    ):
        return (
            f"the chain recorded plan {walk.request_plan_sha256} and the supplied plan is "
            f"{plan.request_plan_sha256}; {transition.decision_reference} names exactly this pair "
            f"and substitutes exactly the {transition.substituted_source_id} URL"
        )
    return (
        f"the chain recorded plan {walk.request_plan_sha256} but the supplied plan is "
        f"{plan.request_plan_sha256}"
    )


def _determine(
    conditions: tuple[ConditionResult, ...],
    *,
    walk: ReceiptChainAccounting,
    store: _StoreState,
    carry_in_disagreement: str | None = None,
) -> tuple[str, str, str]:
    """Classify the conditions into `SAFE`, `UNSAFE`, or `UNDETERMINED`.

    The split follows the governing prose exactly. `UNDETERMINED` is reserved for the cases the
    documents name, each of which leaves something unknowable rather than merely wrong:

    - the receipt chain does not resolve, so the consumed count and interruption point are unknown;
    - a committed row has no object, so it cannot be established what was actually persisted;
    - the chain's carry-in root and the catalog's consumption checkpoint disagree, so the cumulative
      consumed count cannot be established at all (Decision 055 §7.5).

    Every other unmet condition has a known cause and is `UNSAFE`, which a separately authorized
    M3.2 repair may correct before inspection runs again. No finer rule is invented here.
    """
    if not walk.resolved:
        return (
            "UNDETERMINED",
            f"the receipt chain does not resolve to a first attempt: {walk.detail}",
            "Stop. Do not resume. Refer for an owner ruling; never reconstruct a missing receipt.",
        )
    if carry_in_disagreement is not None:
        return (
            "UNDETERMINED",
            (
                f"the chain's carry-in root and the operational catalog disagree, so the "
                f"cumulative consumed count cannot be established: {carry_in_disagreement}"
            ),
            (
                "Stop. Do not resume. Refer for an owner ruling; a carry-in that the catalog and "
                "the receipt do not agree on can never authorize continuation, and neither surface "
                "is edited to match the other."
            ),
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


@dataclass(frozen=True, slots=True)
class _OwnedSegment:
    """One raw-lineage retrieval segment the selected run provably owns.

    Ownership is decided by the run boundaries alone; how the segment is *charged* is decided
    later, globally, against the whole reservation set (:func:`_reconcile_owned_segments`).
    """

    urls: frozenset[str]
    retrieved: datetime
    attempts: int


def _selected_run_lineage_contribution(
    document: Mapping[str, object],
    *,
    window: _RunWindow,
    ledger: _LedgerReservations,
) -> tuple[_OwnedSegment | None, str | None]:
    """Decide whether the selected run owns one in-scope lineage manifest's segment.

    Returns ``(owned_segment, undetermined_reason)``. ``(None, None)`` means the manifest is
    provably excluded; a non-``None`` reason means the evidence exists but cannot be ordered
    exactly, which the caller reports as ``UNDETERMINED`` rather than an invented count. The
    decisions, in order:

    * a manifest retrieved strictly before the selected run's recorded start predates the run and
      is proven to belong elsewhere — excluded (Decision 051 §6.4's boundary discipline);
    * one retrieved strictly after the window's provable upper bound (the run's recorded finish or
      a later governed acquisition run's start) postdates the run — excluded the same way;
    * one whose retrieval instant *equals* a boundary instant proves no order, so ownership of the
      segment is not provable — ``UNDETERMINED``, never a guess;
    * anything else inside the window is **owned**, and is returned for global reconciliation.

    This function deliberately no longer decides ledger coverage. Deciding it here — per manifest,
    against the full reservation set — is exactly the **M3-L14** defect: each manifest independently
    found the same reservation sufficient, so one reservation could satisfy two owned segments and
    the reported count fell below the durable floor. Coverage is now a property of the whole segment
    set and is decided once, in one place (Decision 055 §8, ruling 055-D).
    """
    retrieved = _parse_utc_instant(document.get("retrieved_at_utc"))
    if retrieved is None:
        return None, (
            "an in-scope raw-lineage manifest records no parseable UTC retrieval instant, so it "
            "cannot be ordered against the run boundaries"
        )
    if window.started is None:
        return None, (
            "the selected run's recorded start instant cannot be parsed, so no in-scope lineage "
            "can be attributed to or excluded from the run"
        )
    if retrieved < window.started:
        return None, None  # proven to predate the selected run: recorded elsewhere, never added
    if retrieved == window.started:
        return None, (
            "an in-scope retrieval instant equals the selected run's recorded start, so which "
            "run owns the segment is not provable"
        )
    if window.upper_bound is not None:
        if retrieved > window.upper_bound:
            return None, None  # proven to postdate the selected run's window: a later run's segment
        if retrieved == window.upper_bound:
            return None, (
                "an in-scope retrieval instant equals a governed run boundary, so which run owns "
                "the segment is not provable"
            )
    if window.boundary_ambiguous:
        return None, (
            "another governed acquisition run records the selected run's exact start instant, so "
            "in-window lineage cannot be attributed between them"
        )
    if window.boundary_unparseable:
        return None, (
            "a governed run-boundary instant cannot be parsed, so in-window lineage cannot be "
            "proven to belong to the selected run"
        )
    attempts = document.get("attempts")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
        return None, "an in-scope raw-lineage manifest records no usable attempt count"
    segment_urls = frozenset(
        url
        for key in ("requested_url", "final_url")
        if isinstance(url := document.get(key), str) and url
    )
    if not segment_urls and ledger.rows:
        return None, (
            "an in-scope raw-lineage manifest records no request URL identity, so ledger "
            "coverage of its segment is not provable"
        )
    return _OwnedSegment(urls=segment_urls, retrieved=retrieved, attempts=attempts), None


def _reconcile_owned_segments(
    segments: Sequence[_OwnedSegment],
    ledger: _LedgerReservations,
) -> tuple[int, str | None]:
    """Charge every owned segment under one **global one-to-one** reservation-consumption rule.

    Decision 055 §8 (ruling 055-D). A durable reservation may satisfy **at most one** segment, and
    the answer is ``UNDETERMINED`` whenever an exact bijection between reservations and the segments
    they account for cannot be established. Returns ``(pre_ledger_attempts, undetermined_reason)``.

    A reservation is *eligible* for a segment when its canonical request URL is one the segment
    records **and** its pre-send commit instant strictly precedes the segment's retrieval — the
    same durable event-order test as before, applied here across the whole set at once. A
    reservation committed strictly *after* a retrieval remains a distinct later event: it is
    counted once by the ledger and neither covers nor erases the earlier segment.

    The rule, applied over all owned segments together, is an **exact bijection** in both
    directions:

    * a matching reservation whose order against a retrieval is unparseable or exactly simultaneous
      proves no order at all — ``UNDETERMINED``;
    * a segment with **no** eligible reservation is genuine pre-ledger evidence and adds exactly its
      recorded ``attempts`` (Decision 051 §5), consuming nothing;
    * two covered segments whose eligible sets **intersect at all** are multiply matchable: the same
      reservation could account for either, so no assignment is *proved* even where one exists —
      ``UNDETERMINED``;
    * every **counted physical attempt** of a covered segment must map to exactly one eligible
      reservation. Fewer eligible reservations than attempts is unmatched cardinality —
      ``UNDETERMINED``;
    * every **eligible reservation** must map to exactly one counted attempt. One that no attempt
      accounts for is a **leftover contradiction**: the ledger holds a durable pre-send commit for
      that URL, before that retrieval, that the lineage does not explain — ``UNDETERMINED``.

    The last two are a single exact-equality test, and reading it as ``>=`` instead is the
    **M3-L14** defect the measured counterexample turns on. One owned segment recording a single
    attempt, against two eligible preceding same-URL reservations, satisfies the segment's demand
    — and leaves a reservation unaccounted for. Reporting coverage there states a consumed count
    below the durable floor.
    """
    eligible_by_segment: list[frozenset[int]] = []
    for segment in segments:
        eligible: set[int] = set()
        for index, reservation in enumerate(ledger.rows):
            if reservation.source_url_canonical not in segment.urls:
                continue
            reserved_at = _parse_utc_instant(reservation.started_at_raw)
            if reserved_at is None or reserved_at == segment.retrieved:
                return 0, (
                    "selected-run reservations only partially or order-ambiguously account for an "
                    "in-scope retrieval segment, so exact ledger coverage is not provable"
                )
            if reserved_at < segment.retrieved:
                eligible.add(index)
        eligible_by_segment.append(frozenset(eligible))

    covered = [
        (segment, candidates)
        for segment, candidates in zip(segments, eligible_by_segment, strict=True)
        if candidates
    ]

    # Multiply matchable. If two covered segments share any eligible reservation, that reservation
    # could account for either of them. A pairing would still *exist* — but it would be chosen, not
    # proved, and Decision 055 §8 fails closed on multiply matchable cardinality rather than
    # settling it by an arbitrary order.
    claimed: set[int] = set()
    for _segment, candidates in covered:
        if claimed & candidates:
            return 0, (
                "one durable reservation could account for more than one owned retrieval segment, "
                "so no exact one-to-one reservation-to-segment assignment is provable; a "
                "reservation may satisfy at most one segment"
            )
        claimed |= candidates

    # Exact in both directions, which is what makes the surviving assignment a bijection rather
    # than merely a possibility. Fewer eligible reservations than counted attempts is unmatched
    # cardinality. *More* is a leftover contradiction — a durable pre-send commit for that URL,
    # committed before that retrieval, that the lineage does not account for — and it is the half
    # a `>=` comparison silently accepts, reporting a count below the durable floor.
    for segment, candidates in covered:
        if len(candidates) != segment.attempts:
            return 0, (
                "selected-run reservations do not account for an in-scope retrieval segment "
                "exactly: its counted attempts and the reservations eligible to cover them do not "
                "correspond one-to-one, so exact ledger coverage is not provable"
            )

    # Only segments with no eligible reservation are genuine pre-ledger evidence; every covered
    # segment's sends are already counted exactly once by the ledger itself.
    return (
        sum(
            segment.attempts
            for segment, candidates in zip(segments, eligible_by_segment, strict=True)
            if not candidates
        ),
        None,
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
    * an in-scope manifest's **ownership** is decided by :func:`_selected_run_lineage_contribution`,
      which excludes segments the run boundaries prove belong elsewhere;
    * every owned segment is then **charged together**, once, by
      :func:`_reconcile_owned_segments`, under the global one-to-one reservation-consumption rule
      (Decision 055 §8) — the same segment is never counted twice, one reservation never satisfies
      two segments, and no segment the run owns is ever silently dropped.

    Evidence that cannot be reconciled is never silently treated as zero. A manifest that cannot
    be read, is not a JSON object, records no source identity, or fails exact attribution sets an
    ``UNDETERMINED`` reason, and the total then stands as a durable floor rather than a proven
    exact count (Decision 051 §6.5, §6.9; §5A rule 5). Provably unrelated manifests are excluded
    before any attribution field is inspected, so they never raise a spurious ambiguity.
    """
    undetermined: str | None = None
    owned: list[_OwnedSegment] = []
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
        segment, reason = _selected_run_lineage_contribution(document, window=window, ledger=ledger)
        if reason is not None:
            undetermined = undetermined or reason
            continue
        if segment is not None:
            owned.append(segment)
    total, coverage_reason = _reconcile_owned_segments(owned, ledger)
    return _LineageAccounting(
        pre_ledger_attempts=total,
        undetermined_reason=undetermined or coverage_reason,
    )


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
    walk = ReceiptChainAccounting(
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
            "The terminal or interruption state is established, not guessed",
            _NOT_MET,
            "no receipt exists, so neither an interruption state nor a terminal end state is "
            "established; Decision 062's terminal path is reached only from a valid receipt and "
            "explicitly does not extend to a receiptless, crashed, killed, or uncertain state",
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
