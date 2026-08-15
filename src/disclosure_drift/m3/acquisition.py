"""Milestone 3.2 bounded acquisition driver (accepted contract §§9-14; T2 packet §6, T2.2-T2.3).

This module is the **driver-side integration** of surfaces that already exist and are accepted.
It writes no storage layer, no catalog schema, and no transport of its own: the operational
catalog (:mod:`disclosure_drift.storage.catalog`), the immutable content-addressed raw store
(:mod:`disclosure_drift.sec.raw_store`), the observation recorder
(:mod:`disclosure_drift.sec.observation_catalog`), the snapshot store
(:mod:`disclosure_drift.sec.snapshots`), the response-policy client
(:mod:`disclosure_drift.sec.http_client`), the shared physical-attempt gate
(:mod:`disclosure_drift.sec.request_ceiling`), and the source registry
(:mod:`disclosure_drift.sec.source_registry`) are all consumed **unchanged**. Every one of them is
a prohibited path for this stage, which is precisely why the integration lives here.

Three properties are structural rather than conventional:

**No transport is constructible here.** Importing or constructing :class:`AcquisitionEngine` opens
no socket and builds no client. The transport arrives as an injected object, and the engine
refuses to run without an explicit :class:`LiveOperationAuthorization` that no configuration key,
contract acceptance, gate token, or ceiling value can synthesize. The complete live-authorization
conjunction is enforced by the later operator layer; what this module guarantees is a fail-closed
boundary that *makes* that conjunction enforceable, and a refusal that happens before the first
transport call rather than after it.

**The plan is consumed, never re-derived.** :meth:`AcquisitionEngine.preflight` binds an approved
plan by its own content hash, the named window, and the exact approved ceiling integer. A
mismatch on any of the three refuses before any wire activity (contract §9).

**Termination is not success.** A request that reaches a terminal disposition is *classified*; it
is satisfied only by a hash-verified, provenance-complete object (new, or a byte-identical reuse
that independently passes the same checks). A window with any required object absent is
incomplete, and :class:`WindowOutcome` cannot report otherwise — the distinction the accepted
contract §14 draws is represented in the type, not left to a caller's discipline.

**Routes are not interchangeable.** How a payload is retrieved, and what provenance it owes, are
read from the registered route specification rather than fixed uniformly: a bulk archive is
streamed rather than buffered (:func:`route_is_streamed`), and its validated members are recorded
as archive lineage beside it. Treating every route alike would quarantine the bulk submissions
object on size alone, and leave it without the member lineage its later reuse and reconciliation
depend on.

Recovery *observability* is provided here (partial objects, orphans, missing referents, uncertain
outcomes, cumulative attempt state). Recovery **repair**, reconciliation reporting, drift
inspection, and resume are stage T2.4 and are deliberately absent.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal

from disclosure_drift.errors import (
    CatalogWriteError,
    DisclosureDriftError,
    RawObjectIntegrityError,
)
from disclosure_drift.m3.evidence_paths import require_external_evidence_root
from disclosure_drift.m3.receipt import (
    RESPONSE_CLASSIFICATION_BUCKETS,
    ProhibitedReceiptContentError,
    ReceiptValidationError,
    canonical_bytes,
    inspect_receipt,
    scan_for_prohibited_content,
)
from disclosure_drift.m3.recovery import (
    CARRY_IN_ACQUISITION_WINDOW,
    CARRY_IN_APPROVED_REQUEST_CEILING,
    CARRY_IN_AUTHORITY_SCHEMA_VERSION,
    CARRY_IN_AUTHORIZING_DECISION_REFERENCE,
    CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT,
    CARRY_IN_HISTORICAL_ROUTE_ALLOCATION,
    CARRY_IN_REQUEST_PLAN_SHA256,
    PLAN_TRANSITION_ACQUISITION_WINDOW,
    PLAN_TRANSITION_APPROVED_REQUEST_CEILING,
    PLAN_TRANSITION_DECISION_REFERENCE,
    PLAN_TRANSITION_NEW_URL,
    PLAN_TRANSITION_OLD_URL,
    PLAN_TRANSITION_PREDECESSOR_PLAN_SHA256,
    PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION,
    PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID,
    PLAN_TRANSITION_SUBSTITUTION_COUNT,
    PLAN_TRANSITION_SUCCESSOR_PLAN_SHA256,
    PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION,
    SUCCESSFUL_TERMINAL_COMPLETION_STATUS,
    CarryInFixedBindings,
    PlanTransitionAuthority,
    RecoveryState,
    carry_in_checkpoint_key,
    carry_in_fixed_binding_disagreement,
    carry_in_orphan_reference_disagreement,
    inspect_recovery_state,
    read_only_catalog,
)
from disclosure_drift.m3.request_plan import (
    M3_2A_BOOTSTRAP_ROUTES,
    M3_2B_DEPENDENT_ROUTES,
    RequestPlan,
    build_m3_2b_dependent_plan,
    canonical_plan_bytes,
    derive_a_reachable,
    request_plan_from_document,
)
from disclosure_drift.paths import DataTree, PathPolicyError, relative_to_root
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.archive import ArchiveDefenceError, ArchiveMember, iter_members
from disclosure_drift.sec.http_client import (
    FetchResult,
    ProhibitedRetrievalError,
    RetrievalPolicy,
    SecClient,
)
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    ProjectionValidation,
    RecoveryEvent,
    load_observations,
    open_recovery_state,
    rebuild_audit_projection,
    reconcile,
    record_recovery_events,
    resolve_recovery_state,
    validate_audit_projection,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.raw_store import LINEAGE_SUFFIX, RawStore
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)
from disclosure_drift.sec.snapshots import SnapshotIndex, SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import (
    M22_SOURCE_REGISTRY_VERSION,
    SOURCES,
    SourceSpec,
    filing_body_url_is_prohibited,
    require_registered,
)
from disclosure_drift.sec.transport import SecRequest, Transport, TransportResponse
from disclosure_drift.sec.urls import request_identity
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import applied_versions, integrity_report

__all__ = [
    "ACQUISITION_INTERRUPTED_REASON",
    "ACQUISITION_INTERRUPTION_STATES",
    "ACQUISITION_JOB_KIND",
    "ACQUISITION_RUN_JOB_STATES",
    "ACQUISITION_WINDOWS",
    "CARRY_IN_ACQUISITION_WINDOW",
    "CARRY_IN_APPROVED_REQUEST_CEILING",
    "CARRY_IN_AUTHORITY_SCHEMA_VERSION",
    "CARRY_IN_AUTHORIZING_DECISION_REFERENCE",
    "CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT",
    "CARRY_IN_HISTORICAL_ROUTE_ALLOCATION",
    "CARRY_IN_REQUEST_PLAN_SHA256",
    "DEPENDENT_RECONCILIATION_SET_VERSION",
    "FINAL_MIGRATION_VERSION",
    "M3_2B_DEPENDENT_ROUTES",
    "NO_HTTP_STATUS_SENTINEL",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "PROGRESS_SINK_FAILURE_REASON",
    "RECOVERY_ACTIONS",
    "AcquisitionEngine",
    "AcquisitionError",
    "AcquisitionGateError",
    "AcquisitionRunBinding",
    "AcquisitionRunError",
    "CarryInAuthority",
    "CarryInAuthorityError",
    "CatalogPreparation",
    "CatalogPreparationError",
    "CatalogReconstruction",
    "ContainmentError",
    "ContinuationProposal",
    "ContinuationRequest",
    "CumulativeAttemptAccounting",
    "DependentPlanDerivation",
    "DependentPlanError",
    "DriftListingEntry",
    "LiveAcquisitionResult",
    "LiveOperationAuthorization",
    "LiveOperatorGate",
    "LogicalRequest",
    "PhysicalResponseLog",
    "PreSendAttemptLedger",
    "RebuildProjectionEligibility",
    "ReconciliationItem",
    "RecordingTransport",
    "RecoveryActionResult",
    "RecoveryObservation",
    "RepairRefusedError",
    "RequestOutcome",
    "RequestReconciliation",
    "ResponseAccounting",
    "RunScopedDrift",
    "StorageBinding",
    "StoragePreparationError",
    "StoreFinding",
    "WindowOutcome",
    "apply_recovery_action",
    "conditional_validators",
    "default_live_transport_factory",
    "default_run_id_factory",
    "derive_dependent_plan",
    "derive_logical_requests",
    "drift_for_run",
    "execute_live_acquisition",
    "load_approved_plan",
    "load_carry_in_authority",
    "observe_recovery_state",
    "planned_request_identity",
    "prepare_operational_catalog",
    "prepare_storage",
    "propose_continuation",
    "reconcile_requests",
    "rebuild_projection_eligibility",
    "reconstruct_catalog_state",
    "register_acquisition_run",
    "require_admitted_carry_in_authority",
    "require_m3_2a_consumed_baseline",
    "resolve_within",
    "route_is_streamed",
    "validate_acquisition_run",
    "verified_reusable_predecessor",
    "verify_carry_in_authority",
    "verify_window_bindings",
]

#: The operational catalog's path relative to the external evidence root (contract §16).
OPERATIONAL_CATALOG_RELATIVE_PATH: Final = "catalogs/m3_2a_operational.sqlite3"

#: The migration chain the operational catalog is created at. Contract §11 originally fixed it at
#: ``0013`` -- "created only inside an authorized window at migration chain ``0013``" -- and a chain
#: ending anywhere else is a refusal rather than an upgrade. That refusal rule is **unchanged**;
#: only the head it names moves.
#:
#: **Accepted Decision 084 R65** moves it to ``0014``, because accepted Decision 083 §10 added
#: migration ``0014`` (the R46 multi-registrant relational correction) and this constant records the
#: repository's **current schema-chain head**. Leaving it at ``0013`` would make every freshly
#: prepared catalog refuse itself.
#:
#: **It records a schema fact and nothing more.** It does not reopen M3.2, authorize acquisition,
#: authorize network access, authorize applying migration ``0014`` to the accepted private M3.2
#: operational catalog, authorize writing any accepted M3.2 evidence, move ``m3.2-complete``, or
#: grant M3.3-E0 authority. Migration ``0014`` remains prospective and pre-E0, the accepted private
#: M3.2 operational catalog remains untouched, and no invocation against it is authorized.
FINAL_MIGRATION_VERSION: Final = 14

#: The two acquisition windows. A window name outside this set is refused rather than treated as
#: an unrecognized-but-harmless label.
ACQUISITION_WINDOWS: Final[tuple[str, ...]] = ("M3.2A", "M3.2B")

#: The two dependent route families of the M3.2B window (contract §6), re-exported from the
#: planner that owns them. Window separation is enforced in **both** directions: a dependent
#: request in M3.2A and a bootstrap request in M3.2B are each contract §17 stop condition 5, and a
#: guard that checks only one direction leaves the other silently permitted. Reading the tuple from
#: `request_plan` rather than restating it keeps the planner and this driver from disagreeing about
#: which routes belong to which window. It is used by :meth:`AcquisitionEngine._verify_routes` and
#: re-exported here because the driver's window vocabulary is part of its public surface.

#: The ``ops_ingestion_jobs.job_kind`` every M3.2 acquisition run registers under (Decision 045
#: §6A.1). It is deliberately **not** the M2.2 census kind: an M3.2 acquisition run is a different
#: kind of run, and `m3 show-drift --run` and `m3 recover --run` refuse any row that does not carry
#: exactly this kind together with an accepted acquisition window as its stage.
ACQUISITION_JOB_KIND: Final = "m3_2_acquisition"

_INDEX_ROUTE: Final = "sec_full_index_company"
_ANNOUNCEMENT_ROUTE: Final = "sec_edgar_calendar_announcement"
_INSTANCE_KEY_PATTERN: Final = re.compile(r"^(?P<year>\d{4})QTR(?P<quarter>[1-4])$")

#: Reason recorded when a required quarterly index instance is left absent (registered code;
#: `reasons.py` is untouched). The registry defines it as "a required quarterly index instance was
#: not retrieved or not usably parsed", which is exactly the archival-absence and quarantined-body
#: cases this driver must make durable rather than leave uncoded.
_INDEX_ABSENT_REASON: Final = "INDEX_INSTANCE_UNAVAILABLE"

#: Reason recorded when a REQUIRED non-quarterly-index M3.2A object is left terminally absent —
#: its committed observation is ``failed`` or ``quarantined`` (registered under Decision 040 §4).
#: It marks that the required object remains unavailable, and it coexists with — never replaces —
#: a more specific defect code such as ``SEC_RESPONSE_MALFORMED`` or ``RAW_ARCHIVE_INVALID``.
#: Quarterly index instances keep ``INDEX_INSTANCE_UNAVAILABLE``; stopped, interrupted,
#: ceiling-exhausted, and not-attempted requests keep their run classifications and never receive
#: this code merely for lacking an object; no M3.2B mapping is authorized.
_REQUIRED_OBJECT_ABSENT_REASON: Final = "SOURCE_REQUIRED_OBJECT_UNAVAILABLE"

#: Suffix filter for bulk-archive members. The submissions archive carries one JSON document per
#: filer; the accepted archive reader applies this filter and validates every member it yields.
_ARCHIVE_MEMBER_SUFFIX: Final = ".json"

#: Recorded on every observation this driver writes. Entity-specific routes additionally require a
#: purpose of at least twelve characters (``http_client.SecClient.fetch``), which this satisfies.
_ACQUISITION_PURPOSE: Final = (
    "acquire approved Milestone 3.2 metadata object under the owner-approved request plan"
)

RequestDisposition = Literal[
    "satisfied_new",
    "satisfied_duplicate",
    "satisfied_reused",
    "absent",
    "quarantined",
    "failed",
    "stopped",
    "not_attempted",
]
"""Terminal dispositions of one planned logical request.

Three of these are satisfying, and they are kept apart because the accepted accounting keeps them
apart: contract §22 reports ``NEW_RAW_OBJECTS``, ``DUPLICATES_RECONCILED``, and ``CACHE_HITS`` as
three separate quantities, and T2 packet §12 maps a reuse to ``cache_hit_count`` rather than to
``raw_object_count``. Collapsing them would make those figures underivable from a window outcome.

* ``satisfied_new`` — a new immutable object was promoted (``stored_new`` or ``superseded``).
* ``satisfied_duplicate`` — the response was byte-identical to the preserved object, which was
  reconciled and reused rather than rewritten (``unchanged_content``).
* ``satisfied_reused`` — a conditional request confirmed the preserved snapshot (``304``).

``stopped`` is distinct from ``not_attempted``: it marks a request that consumed one or more
physical attempts before the window stopped, which ``not_attempted`` would misreport as untouched.
"""

CompletionStatus = Literal[
    "complete",
    "incomplete",
    "interrupted",
    "stopped_at_ceiling",
    "stopped_by_gate",
    "failed",
]
"""How one acquisition window ended.

``interrupted`` is reserved for a **genuine external interruption of a lawful invocation** — the
catchable ``KeyboardInterrupt`` a SIGINT delivers. It is never another name for an ordinary
failure, a ceiling stop, a gate stop, schema drift, a response-policy failure, or generic engine
incompleteness: each of those keeps its own status, and every one of them is reachable without a
signal ever arriving.
"""

#: The interruption states an M3.2 acquisition window may record. A strict subset of the frozen
#: receipt vocabulary: ``during_selection`` and ``during_manifest_write`` name phases of a
#: *selection* run, and this driver acquires objects rather than selecting, so it can never
#: truthfully be in either. Emitting one from here would assert a phase that did not happen.
ACQUISITION_INTERRUPTION_STATES: Final[tuple[str, ...]] = (
    "after_catalog_commit",
    "after_raw_store_write_before_catalog_commit",
    "before_raw_store_write",
)

#: The already-registered reason a genuine interruption records. No reason code is created,
#: modified, or repurposed here: the registry defines this one as "acquisition was interrupted and
#: no narrower registered reason applies", which is exactly this case.
ACQUISITION_INTERRUPTED_REASON: Final = "SEC_ACQUISITION_INTERRUPTED"

#: The ``ops_ingestion_jobs.job_state`` values one finished acquisition run may be closed into.
#: Every one is a literal the migration ``0001`` CHECK constraint already admits; no state is
#: invented and no migration is required. ``stopped`` is the truthful state of an invocation that
#: was externally interrupted: it neither completed nor failed.
ACQUISITION_RUN_JOB_STATES: Final[tuple[str, ...]] = ("completed", "failed", "stopped")

#: What an interrupted window records as its detail. Fixed and structural: it names no path, no
#: identity, and no operator-supplied text, and it is short enough for the receipt's bounded
#: ``reason_detail`` to be derived beside it.
_INTERRUPTION_DETAIL: Final = (
    "the invocation was externally interrupted; acquisition stopped before the next logical "
    "request began and no further physical request was placed"
)

#: Snapshot-store outcomes that promote a **new** immutable object for the retrieval that produced
#: them. A reuse, a byte-identical duplicate, a failure, and a quarantine each leave no newly
#: promoted object belonging to that retrieval, which is what separates ``before_raw_store_write``
#: from ``after_raw_store_write_before_catalog_commit``.
_PROMOTING_OUTCOMES: Final[frozenset[str]] = frozenset({"stored_new", "superseded"})


class AcquisitionError(DisclosureDriftError):
    """Base class for every refusal this driver raises."""


class ContainmentError(AcquisitionError):
    """Raised when a governed path would escape the evidence root.

    No message names a resolved absolute path: the operator supplied the root and already knows
    it, and master plan §17 stop condition 12 bars an absolute personal path from any output.
    """


class CatalogPreparationError(AcquisitionError):
    """Raised when the operational catalog cannot be created or verified as required."""


class StoragePreparationError(AcquisitionError):
    """Raised when the isolated M3.2 data root cannot be prepared safely."""


class AcquisitionGateError(AcquisitionError):
    """Raised when a gate refuses, always before the wire activity it guards.

    Distinct from the two preparation errors so a caller can map a gate refusal to the exit code
    the accepted command surface reserves for it, without string-matching a message.
    """


class AcquisitionRunError(AcquisitionError):
    """Raised when an M3.2 acquisition-run identity cannot be registered or validated.

    Distinct from :class:`AcquisitionGateError` because its consequence is stated separately by
    Decision 045 §6A.2: a registration or verification failure means **no transport is constructed,
    no physical request occurs, and no acquired object is attributed to the failed run**.
    """


class DependentPlanError(AcquisitionError):
    """Raised when M3.2B dependent-plan derivation refuses.

    Every refusal is fail-closed and pre-emptive: the derivation writes neither a plan nor a
    success receipt unless every frozen object verified and the explicit reconciliation set agreed
    with it exactly (Decision 045 §4.3, §13).
    """


#: Bounded operational failures a single request may raise once it has been placed: the object
#: store, the catalog, the path policy, and the filesystem beneath them. Enumerated rather than
#: caught as a base class on purpose — :class:`AcquisitionGateError` is also a
#: ``DisclosureDriftError``, and a gate refusal must never be swallowed into a request outcome.
#: A programmer error (``TypeError``, ``AttributeError``, ``KeyError``) is likewise absent and
#: still propagates, because turning a defect into a recorded "failed request" would hide it.
_OPERATIONAL_FAILURES: Final = (
    RawObjectIntegrityError,
    CatalogWriteError,
    PathPolicyError,
    sqlite3.Error,
    OSError,
)

#: Public description for each operational failure class, most specific first.
#:
#: These exceptions carry private arguments: an ``OSError`` names the absolute path it failed
#: on, a storage error names the object it refused to overwrite, and a SQLite error can name
#: the database file. Copying ``str(exc)`` into an outcome would publish an operator's private
#: evidence-root layout through a field the later operator surfaces, reports, and receipts all
#: read — the same absolute-path exposure the containment refusals are careful never to make.
#: So the detail is **built from this table**, never from the exception's own arguments: the
#: class name says what failed and the description says what kind of operation it was. Nothing
#: is concealed — an operational failure is still reported as one, still terminates the window,
#: and still leaves its committed rows observable.
_OPERATIONAL_FAILURE_DESCRIPTIONS: Final[tuple[tuple[type[BaseException], str], ...]] = (
    (ArchiveDefenceError, "an accepted archive protection refused the acquired archive"),
    (RawObjectIntegrityError, "an immutable raw object could not be written or verified"),
    (CatalogWriteError, "the operational catalog refused a write"),
    (PathPolicyError, "a governed path was refused by the path policy"),
    (sqlite3.Error, "the operational catalog reported a database error"),
    (OSError, "a filesystem operation failed"),
)


def _operational_detail(exc: BaseException) -> str:
    """A public description of one operational failure, carrying no private argument.

    Deliberately derived from the exception's *class* alone. The message, filename, and any
    other argument the exception carries are never read, so no absolute path, response body,
    or member payload can reach an outcome through this seam regardless of what the underlying
    library chose to put in them.
    """
    for kind, description in _OPERATIONAL_FAILURE_DESCRIPTIONS:
        if isinstance(exc, kind):
            return f"{type(exc).__name__}: {description}"
    return f"{type(exc).__name__}: an operational failure occurred"  # pragma: no cover - total


# --------------------------------------------------------------------------- #
# Containment — every governed path is proved inside the evidence root
# --------------------------------------------------------------------------- #
def resolve_within(root: Path, relative: str | Path, *, label: str) -> Path:
    """Return ``root / relative``, proved to stay inside ``root``.

    Containment is decided on **fully resolved** paths, so a symlink cannot launder an escape:
    a component that resolves outside the root is refused even when the lexical path looks
    contained. An absolute ``relative`` and any ``..`` component are refused outright rather than
    normalized, because normalizing an escape attempt into a lawful path is exactly the silent
    relaxation CLAUDE.md rule 12 forbids.

    The root itself is resolved first, which makes the check correct when the root is reached
    through a symlink (a macOS ``/tmp`` fixture, for instance) rather than refusing every path
    under such a root.

    Args:
        root: The containing directory. Must be absolute.
        relative: A path relative to ``root``.
        label: What the path is, for the refusal message. Never a resolved path.

    Raises:
        ContainmentError: the root is not absolute, or the result escapes it.
    """
    if not root.is_absolute():
        message = f"the {label} root must be an absolute path"
        raise ContainmentError(message)

    candidate = Path(relative)
    if candidate.is_absolute():
        message = (
            f"the {label} must be given relative to the evidence root; an absolute path is "
            "refused because it names a location the root does not govern"
        )
        raise ContainmentError(message)
    if ".." in candidate.parts:
        message = (
            f"the {label} contains a parent-directory component; a path that walks out of the "
            "evidence root is refused rather than normalized"
        )
        raise ContainmentError(message)

    resolved_root = Path(os.path.realpath(root))
    resolved = Path(os.path.realpath(root / candidate))
    if resolved != resolved_root and resolved_root not in resolved.parents:
        message = (
            f"the {label} resolves outside the evidence root; a symlink or link component may "
            "not move a governed artifact out of the root that governs it"
        )
        raise ContainmentError(message)
    return resolved


def _refuse_symlinked_ancestors(root: Path, target: Path, *, label: str) -> None:
    """Refuse when any component between ``root`` and ``target`` is a symlink.

    :func:`resolve_within` already proves the *destination* stays inside the root. This is the
    stricter check the accepted contract's stop condition 13 asks for — "symlink detection at any
    governed path" — and it refuses a symlink that happens to point back inside the root, which
    containment alone would allow.

    ``target`` must be the **lexical** ``root / relative`` path, not a resolved one: resolution
    has already followed every symlink, so a resolved path has none left to detect. Passing a
    resolved path here would make this check silently vacuous.
    """
    root_depth = len(root.parts)
    current = target
    while len(current.parts) > root_depth and current.parent != current:
        if current.is_symlink():
            message = (
                f"a component of the {label} is a symbolic link; governed artifacts are addressed "
                "by real paths only"
            )
            raise ContainmentError(message)
        current = current.parent


# --------------------------------------------------------------------------- #
# Subphase A.1 — the operational catalog
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CatalogPreparation:
    """The result of creating or opening one operational catalog."""

    database_path: Path
    lock_directory: Path
    applied_migrations: tuple[str, ...]
    seeded_counts: Mapping[str, int]
    migration_chain_head: int
    created: bool

    @property
    def chain_is_exact(self) -> bool:
        """Whether the applied chain ends exactly at the accepted final migration."""
        return self.migration_chain_head == FINAL_MIGRATION_VERSION


def prepare_operational_catalog(
    *,
    evidence_root: Path,
    relative_path: str | Path = OPERATIONAL_CATALOG_RELATIVE_PATH,
    lock_relative_path: str | Path | None = None,
    repository_root: Path | None = None,
) -> CatalogPreparation:
    """Create or open the operational catalog at the caller-supplied path.

    The caller always supplies the path; there is no default location and, deliberately, no
    fallback to a repository-local database — a missing or unusable root refuses rather than
    silently writing inside the checkout.

    The chain is applied through the accepted ``CatalogWriter.migrate()`` →
    ``seed_reference_data()`` idiom, which commits each migration with its immutable
    name/checksum provenance row and verifies the applied chain before and after. This function
    adds the two checks that idiom does not make: that the resulting chain **ends exactly** at
    :data:`FINAL_MIGRATION_VERSION`, and that the three SQLite integrity gates pass.

    Args:
        evidence_root: The owner-controlled external root. Validated as external when
            ``repository_root`` is supplied.
        relative_path: The catalog path relative to ``evidence_root``.
        lock_relative_path: Directory for the single-writer lease. Defaults to the catalog's own
            parent directory.
        repository_root: When given, ``evidence_root`` is additionally proved to be outside this
            checkout before anything is created.

    Raises:
        CatalogPreparationError: the chain, the seeds, or the integrity gates are not as required.
        ContainmentError: a governed path escapes the evidence root.
    """
    root = _validated_root(evidence_root, repository_root)
    database_path = resolve_within(root, relative_path, label="operational catalog")
    _refuse_symlinked_ancestors(root, root / relative_path, label="operational catalog path")

    lock_directory = (
        database_path.parent
        if lock_relative_path is None
        else resolve_within(root, lock_relative_path, label="catalog lock directory")
    )
    created = not database_path.exists()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    lock_directory.mkdir(parents=True, exist_ok=True)

    if not created:
        _refuse_inconsistent_recorded_chain(database_path)

    try:
        with CatalogWriter(database_path, lock_directory) as writer:
            applied = writer.migrate()
            seeded = writer.seed_reference_data()
            chain = applied_versions(writer.connection)
            report = integrity_report(writer.connection)
    except (DisclosureDriftError, sqlite3.Error) as exc:
        # A pre-existing database that is not this catalog surfaces as a raw sqlite3 error from
        # the accepted provenance check. Wrapping it keeps the refusal a domain fact — an
        # incompatible catalog — rather than leaking a driver-level error a caller would have to
        # string-match, and it keeps the refusal fail-closed either way.
        message = f"the operational catalog could not be prepared: {exc}"
        raise CatalogPreparationError(message) from exc

    if not chain:
        message = "the operational catalog carries no applied migration chain"
        raise CatalogPreparationError(message)
    head = chain[-1]
    if head != FINAL_MIGRATION_VERSION:
        message = (
            f"the operational catalog's migration chain ends at {head:04d}, not the accepted "
            f"{FINAL_MIGRATION_VERSION:04d}; this stage creates no migration, so a different "
            "chain head is an incompatible catalog rather than something to upgrade"
        )
        raise CatalogPreparationError(message)
    if tuple(chain) != tuple(range(1, FINAL_MIGRATION_VERSION + 1)):
        message = (
            "the operational catalog's migration chain is not contiguous from 0001 to "
            f"{FINAL_MIGRATION_VERSION:04d}; a gapped chain is refused rather than filled in"
        )
        raise CatalogPreparationError(message)
    if not report.passed:
        message = (
            "the operational catalog failed a SQLite integrity gate: "
            f"quick_check={report.quick_check}, integrity_check={report.integrity_check}, "
            f"foreign_key_violations={report.foreign_key_violations}"
        )
        raise CatalogPreparationError(message)

    return CatalogPreparation(
        database_path=database_path,
        lock_directory=lock_directory,
        applied_migrations=applied,
        seeded_counts=dict(seeded),
        migration_chain_head=head,
        created=created,
    )


def _refuse_inconsistent_recorded_chain(database_path: Path) -> None:
    """Refuse an existing database whose recorded chain is not a contiguous prefix.

    This is a **read-only pre-flight look**, not a second migrator. The accepted
    ``apply_migrations`` remains the sole authority on what may be applied and on checksum
    provenance; it already refuses an unknown version, a gap, or a checksum drift. What it cannot do
    is explain a *partially recorded* chain: re-applying `0006` onto a schema that already carries
    `0013`'s objects fails deep inside SQLite with "duplicate column name", which is fail-closed but
    tells an operator nothing about what is actually wrong.

    So this states the domain fact first — the recorded chain is inconsistent, and a partially
    initialized catalog is never repaired here — and leaves every consequential decision to the
    accepted migrator. A database this cannot read is passed through untouched: deciding it is
    unreadable is the migrator's job, not this function's.

    The connection is **closed**, not merely committed. ``sqlite3.Connection`` used as a context
    manager governs the transaction and leaves the connection open, and a read-only handle that
    outlives this pre-flight cannot checkpoint yet still pins a WAL-mode catalog's ``-wal`` and
    ``-shm`` sidecars open for as long as it survives (Decision 066 §5).
    """
    try:
        connection = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
        try:
            connection.row_factory = sqlite3.Row
            recorded = applied_versions(connection)
        finally:
            connection.close()
    except sqlite3.Error:
        return  # Not readable as SQLite; the accepted migrator issues the refusal.

    if not recorded:
        return  # An empty or freshly created file is migrated normally.
    expected = tuple(range(1, len(recorded) + 1))
    if tuple(recorded) == expected:
        return  # A contiguous prefix; the migrator applies whatever remains.

    message = (
        f"the existing operational catalog records migration versions {list(recorded)}, which is "
        "not a contiguous chain from 0001; a partially initialized or inconsistent catalog is "
        "refused rather than repaired, because completing it would apply schema over state this "
        "stage cannot account for"
    )
    raise CatalogPreparationError(message)


def _validated_root(evidence_root: Path, repository_root: Path | None) -> Path:
    """Resolve the evidence root, proving it external when a checkout is supplied."""
    if repository_root is not None:
        return require_external_evidence_root(evidence_root, repository_root)
    if not Path(evidence_root).is_absolute():
        message = "the evidence root must be an absolute path outside the repository checkout"
        raise ContainmentError(message)
    return Path(os.path.realpath(evidence_root))


# --------------------------------------------------------------------------- #
# Subphase A.2 — immutable content-addressed storage
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class StorageBinding:
    """The isolated M3.2 data root and the accepted stores bound to it."""

    data_root: Path
    tree: DataTree
    raw_store: RawStore
    snapshot_store: SnapshotStore


def prepare_storage(
    *,
    evidence_root: Path,
    data_root_relative: str | Path,
    repository_root: Path | None = None,
) -> StorageBinding:
    """Prepare the isolated M3.2 data root and bind the accepted stores to it.

    The stores are the accepted implementations, unmodified: :class:`RawStore` already provides
    ``.part`` staging, hash verification before promotion, atomic no-overwrite hard-link
    promotion, byte-identical reuse, differing-body supersession, quarantine that preserves rather
    than deletes, and ``O_CREAT|O_EXCL`` lineage intents. Nothing here re-implements or weakens
    any of that; this binds them to a proved-contained root.

    Raises:
        StoragePreparationError: the data root cannot be created.
        ContainmentError: the data root escapes the evidence root.
    """
    root = _validated_root(evidence_root, repository_root)
    data_root = resolve_within(root, data_root_relative, label="M3.2 data root")
    _refuse_symlinked_ancestors(root, root / data_root_relative, label="M3.2 data root")
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        tree = DataTree.from_root(data_root)
        tree.ensure_tree()
    except OSError as exc:
        message = f"the M3.2 data root could not be prepared: {type(exc).__name__}"
        raise StoragePreparationError(message) from exc

    raw_store = RawStore(tree)
    return StorageBinding(
        data_root=data_root,
        tree=tree,
        raw_store=raw_store,
        snapshot_store=SnapshotStore(tree, raw_store),
    )


# --------------------------------------------------------------------------- #
# Subphase B.1 — the live-authorization boundary
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class LiveOperationAuthorization:
    """The explicit per-window authorization a live run requires.

    This object is **evidence that the operator layer performed the authorization checks**, not a
    grant of its own and not something this module can construct on a caller's behalf. It is
    deliberately inert: it carries no privilege, and every field it names is re-checked against
    the plan and the ceiling at preflight, so a fabricated instance buys nothing.

    The accepted contract §8 gate ladder is enforced by the later operator surface, which alone
    can read a configuration file, evaluate ``--live``, and confirm the per-window instrument.
    What this type provides is the seam that makes that conjunction *enforceable*: the engine
    refuses to reach a transport without one, and no configuration key, contract acceptance, T2
    acceptance, Gate F readiness token, or ceiling value can stand in for it.
    """

    window: str
    plan_sha256: str
    approved_ceiling: int
    authorization_reference: str

    def __post_init__(self) -> None:
        """Refuse an authorization that is not self-consistent."""
        if self.window not in ACQUISITION_WINDOWS:
            message = (
                f"window {self.window!r} is not one of the accepted acquisition windows "
                f"{ACQUISITION_WINDOWS}"
            )
            raise AcquisitionGateError(message)
        if len(self.plan_sha256) != 64 or not all(
            character in "0123456789abcdef" for character in self.plan_sha256
        ):
            message = "the authorized plan hash must be a lowercase hex SHA-256 digest"
            raise AcquisitionGateError(message)
        if self.approved_ceiling < 0:
            message = "the approved ceiling must not be negative"
            raise AcquisitionGateError(message)
        if not self.authorization_reference.strip():
            message = (
                "the authorization must name the owner instrument it records; an unnamed "
                "authorization is refused rather than treated as sufficient"
            )
            raise AcquisitionGateError(message)


# --------------------------------------------------------------------------- #
# Subphase B.2 — logical requests derived from the approved plan
# --------------------------------------------------------------------------- #
def route_is_streamed(spec: SourceSpec) -> bool:
    """Whether this route's payload must be streamed rather than buffered.

    Read from the **registered route specification**, never hardcoded per call site. A route
    registered as an archive is a bulk object: the accepted transport bound
    (``transport.MAX_IN_MEMORY_BYTES``, 64 MiB) exists precisely so such a payload is not pulled
    into memory, and the accepted response policy *quarantines* a buffered body that exceeds it. A
    driver that buffered the bulk submissions archive would therefore quarantine the one object
    contract §14 requires and §15 makes M3.2B depend on — not because anything was wrong with it,
    but because of how it was asked for.

    This is the same rule the accepted Stage M2.2 caller applies
    (``census_orchestrator``: ``stream=spec.expected_content == "zip"``), read from the same
    registry, so the two cannot drift apart.
    """
    return spec.expected_content == "zip"


@dataclass(frozen=True, slots=True)
class LogicalRequest:
    """One planned logical request: a registered route plus its instance parameters."""

    source_id: str
    instance_key: str
    parameters: Mapping[str, str]

    @property
    def identity_label(self) -> str:
        """A stable label for progress output and reconciliation joins."""
        return self.source_id if not self.instance_key else f"{self.source_id}:{self.instance_key}"


def derive_logical_requests(plan: RequestPlan) -> tuple[LogicalRequest, ...]:
    """Expand an approved plan into the exact logical requests it authorizes.

    The expansion is deterministic and total: routes are visited in plan order, and each route's
    instance list is derived from the plan's own recorded content rather than from the clock, the
    catalog, or the network. Nothing is invented — a route whose planned count cannot be matched
    to concrete instances refuses instead of guessing which instances were meant.

    Raises:
        AcquisitionGateError: a route's planned count and its derivable instances disagree, or a
            required index key is malformed.
    """
    requests: list[LogicalRequest] = []
    index_keys = _index_instance_keys(plan)

    for route in plan.routes:
        spec = require_registered(route.source_id)
        planned = route.planned_unique_logical_requests
        if planned == 0:
            continue
        if route.source_id == _INDEX_ROUTE:
            if len(index_keys) != planned:
                message = (
                    f"route {route.source_id!r} plans {planned} logical request(s) but the plan "
                    f"names {len(index_keys)} quarterly instance(s); the run consumes the "
                    "approved plan and never re-derives one"
                )
                raise AcquisitionGateError(message)
            requests.extend(
                LogicalRequest(
                    source_id=route.source_id,
                    instance_key=key,
                    parameters=_index_parameters(key),
                )
                for key in index_keys
            )
            continue
        if route.source_id == _ANNOUNCEMENT_ROUTE:
            # Manifest-resolved: the URL comes from the reviewed evidence manifest, never from a
            # caller. The approved M3.2A plan carries zero entries; a nonzero count therefore
            # needs a manifest this stage is not authorized to read, so it stops.
            message = (
                f"route {route.source_id!r} plans {planned} logical request(s), but a "
                "manifest-resolved announcement URL comes from the reviewed evidence manifest "
                "rather than from this driver; supply the manifest through the operator layer"
            )
            raise AcquisitionGateError(message)
        if planned != 1:
            message = (
                f"singleton route {route.source_id!r} plans {planned} logical requests; a "
                "singleton route addresses exactly one instance"
            )
            raise AcquisitionGateError(message)
        if spec.manifest_resolved:  # pragma: no cover - the announcement route returns above
            message = f"route {route.source_id!r} is manifest-resolved and needs a manifest entry"
            raise AcquisitionGateError(message)
        requests.append(LogicalRequest(source_id=route.source_id, instance_key="", parameters={}))
    _refuse_duplicate_identities(requests)
    return tuple(requests)


def _refuse_duplicate_identities(requests: Sequence[LogicalRequest]) -> None:
    """Refuse an expansion in which two planned requests address the same identity.

    Two requests for one identity retrieve one object, and the object store correctly
    deduplicates them — so both would classify as satisfied while only one required object exists.
    The window would then report every planned request satisfied on a smaller object set than it
    planned for, which is precisely the false success contract §14 forbids.

    Refused **before any transport**, and refused as a domain error rather than a classification:
    a plan that cannot state distinct work is not work this driver may start. No reason code is
    invented for it, because no request has been attempted and nothing is being classified.
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for request in requests:
        label = request.identity_label
        if label in seen:
            duplicates.append(label)
        seen.add(label)
    if duplicates:
        message = (
            f"the plan expands to repeated logical request identit(ies) {sorted(set(duplicates))}; "
            "two planned requests addressing one identity would retrieve one object and count "
            "twice toward satisfaction, so the expansion is refused before any attempt"
        )
        raise AcquisitionGateError(message)


def _index_instance_keys(plan: RequestPlan) -> tuple[str, ...]:
    """The quarterly instance keys the plan's index route intends to acquire.

    ``required_index_keys`` records every required instance, including those already satisfied
    when the plan was built and reported as ``expected_cache_hits``. The instances still to
    acquire are the required keys minus that many, taken from the front in the planner's own
    chronological order, which is how the planner excluded them.
    """
    required = plan.required_index_keys
    satisfied = plan.expected_cache_hits
    if satisfied < 0 or satisfied > len(required):
        message = (
            f"the plan reports {satisfied} expected cache hit(s) against "
            f"{len(required)} required index instance(s)"
        )
        raise AcquisitionGateError(message)
    remaining = required[satisfied:] if satisfied else required
    for key in remaining:
        if _INSTANCE_KEY_PATTERN.match(key) is None:
            message = f"required index key {key!r} is not a YYYYQTRn instance key"
            raise AcquisitionGateError(message)
    return tuple(remaining)


def _index_parameters(instance_key: str) -> Mapping[str, str]:
    """URL-template parameters for one quarterly index instance."""
    matched = _INSTANCE_KEY_PATTERN.match(instance_key)
    if matched is None:  # pragma: no cover - callers validate first
        message = f"required index key {instance_key!r} is not a YYYYQTRn instance key"
        raise AcquisitionGateError(message)
    return {"year": matched["year"], "quarter": matched["quarter"]}


def _closed_period_flags(plan: RequestPlan) -> Mapping[str, bool]:
    """Whether each planned quarterly instance names a closed period.

    A dated-snapshot identity behaves differently once its period closes: a changed body is
    ordinary while the quarter is open and an anomaly once it has closed. ``SnapshotStore.record``
    fails closed when this is unknown, so the flag is derived from the plan's own coverage inputs
    rather than defaulted.
    """
    window = CoverageWindow(
        coverage_start=plan.coverage_start,
        coverage_end=plan.coverage_end,
        as_of_date=plan.as_of_date,
        include_open_quarter=plan.include_open_quarter,
    )
    return {
        instance.instance_key: instance.is_finalized_period
        for instance in plan_index_instances(window).instances
    }


# --------------------------------------------------------------------------- #
# Subphase B.3 — outcomes
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RequestOutcome:
    """The terminal disposition of one logical request."""

    request: LogicalRequest
    disposition: RequestDisposition
    observation_id: str | None = None
    content_sha256: str | None = None
    relative_storage_path: str | None = None
    stored_size_bytes: int | None = None
    media_type: str | None = None
    http_status: int | None = None
    attempts: int = 0
    reason_codes: tuple[str, ...] = ()
    detail: str = ""

    @property
    def satisfies_requirement(self) -> bool:
        """Whether this outcome satisfies its planned logical request.

        A terminal classification never satisfies a request by itself (contract §14). Only a
        hash-verified, provenance-complete object does — newly stored, reconciled as a
        byte-identical duplicate, or a reuse that independently passed the same verification.
        """
        return self.disposition in {
            "satisfied_new",
            "satisfied_duplicate",
            "satisfied_reused",
        } and bool(self.content_sha256 and self.relative_storage_path)

    @property
    def is_terminal_classification(self) -> bool:
        """Whether the request reached a registered terminal disposition."""
        return self.disposition not in {"not_attempted", "stopped"}


@dataclass(frozen=True, slots=True)
class WindowOutcome:
    """The result of executing one acquisition window."""

    window: str
    plan_sha256: str
    approved_ceiling: int
    consumed_physical_attempts: int
    planned_logical_requests: int
    outcomes: tuple[RequestOutcome, ...]
    completion_status: CompletionStatus
    reason_codes: tuple[str, ...] = ()
    detail: str = ""
    interruption_state: str | None = None
    """Where a genuinely interrupted window stopped, established rather than guessed.

    Present exactly when :attr:`completion_status` is ``interrupted``, and then always one of
    :data:`ACQUISITION_INTERRUPTION_STATES`. The engine derives it from durable raw-store and
    catalog evidence and refuses to produce a window at all when that evidence cannot establish it
    exactly, so a value here is a proved fact rather than an inference from how far the code
    happened to get.
    """
    progress_failures: tuple[str, ...] = ()
    """Operator progress-sink failures observed during the run.

    Recorded rather than raised: a failing progress sink is an operator-output problem, and it
    must not be able to discard a window whose objects are promoted and whose rows are committed.
    Populated entries never make a window successful on their own, and never make one unsuccessful
    either — they are reported so the operator can see their own output failed.
    """

    @property
    def satisfied(self) -> tuple[RequestOutcome, ...]:
        """Outcomes that genuinely satisfied their planned request."""
        return tuple(outcome for outcome in self.outcomes if outcome.satisfies_requirement)

    @property
    def absences(self) -> tuple[RequestOutcome, ...]:
        """Planned requests whose required object is absent.

        Item-level absent-object identities live in the operational catalog and in the later
        reconciliation report, never in the frozen receipt (Decision 034 §6 R1). This property is
        the in-memory view the driver exposes to its caller; it is not a receipt field.
        """
        return tuple(
            outcome
            for outcome in self.outcomes
            if not outcome.satisfies_requirement
            and outcome.disposition not in {"not_attempted", "stopped"}
        )

    @property
    def unattempted(self) -> tuple[RequestOutcome, ...]:
        """Planned requests never attempted, because the window stopped first.

        A request that consumed one or more physical attempts before the window stopped is
        ``stopped``, not ``not_attempted``, and is reported by :attr:`interrupted` instead — the
        attempts it consumed are real and are charged against the ceiling.
        """
        return tuple(outcome for outcome in self.outcomes if outcome.disposition == "not_attempted")

    @property
    def interrupted(self) -> tuple[RequestOutcome, ...]:
        """Planned requests that consumed attempts but reached no terminal classification."""
        return tuple(outcome for outcome in self.outcomes if outcome.disposition == "stopped")

    @property
    def new_raw_objects(self) -> int:
        """Count of newly promoted immutable objects (contract §22 ``NEW_RAW_OBJECTS``)."""
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_new" and outcome.satisfies_requirement
        )

    @property
    def duplicates_reconciled(self) -> int:
        """Count of byte-identical bodies reconciled to a preserved object (§22)."""
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_duplicate" and outcome.satisfies_requirement
        )

    @property
    def cache_hits(self) -> int:
        """Count of conditional requests lawfully confirming a preserved snapshot via ``304``.

        **Decision 040 §6 vocabulary ruling:** this quantity is the future receipt's
        ``not_modified_count`` — a request that was physically attempted with accepted validators
        and reconciled against the preserved evidence. It must **not** populate the future
        receipt's ``cache_hit_count``, which counts instances already satisfied and therefore
        never requested (a continuation proposal reports those separately as
        ``already_satisfied_excluded``). :attr:`not_modified_reuses` is the unambiguous name;
        this accepted alias is retained for existing callers.
        """
        return sum(
            1
            for outcome in self.outcomes
            if outcome.disposition == "satisfied_reused" and outcome.satisfies_requirement
        )

    @property
    def not_modified_reuses(self) -> int:
        """Conditional requests physically attempted and lawfully reconciled as ``304`` reuse.

        The future receipt's ``not_modified_count`` (Decision 040 §6), under a name no reader can
        mistake for the not-requested exclusion count the receipt calls ``cache_hit_count``.
        """
        return self.cache_hits

    @property
    def byte_identical_duplicates(self) -> int:
        """Physically retrieved ``200`` responses whose bytes matched preserved evidence.

        The future receipt's ``duplicate_object_count`` (Decision 040 §6), as the
        receipt-vocabulary name for :attr:`duplicates_reconciled`.
        """
        return self.duplicates_reconciled

    @property
    def planned_work_remains(self) -> bool:
        """Whether any planned logical request is still unsatisfied."""
        return len(self.satisfied) < self.planned_logical_requests

    @property
    def completed_successfully(self) -> bool:
        """Whether the window completed successfully under contract §14.

        Every required object present and verified, no absence, nothing left unattempted or
        interrupted, and no attempt beyond the ceiling. Termination alone is deliberately not
        enough, and no other combination of fields can be read as success.
        """
        return (
            self.completion_status == "complete"
            and not self.absences
            and not self.unattempted
            and not self.interrupted
            and len(self.satisfied) == self.planned_logical_requests
            and self.consumed_physical_attempts <= self.approved_ceiling
        )

    @property
    def classification_totals(self) -> Mapping[str, int]:
        """Per-disposition totals. Sums exactly to the planned logical request count."""
        totals: dict[str, int] = {
            "satisfied_new": 0,
            "satisfied_duplicate": 0,
            "satisfied_reused": 0,
            "absent": 0,
            "quarantined": 0,
            "failed": 0,
            "stopped": 0,
            "not_attempted": 0,
        }
        for outcome in self.outcomes:
            totals[outcome.disposition] += 1
        return totals

    def __post_init__(self) -> None:
        """Refuse a window that claims an interruption it cannot state, or one it did not have.

        Both directions, because both are ways a false resume could be advertised: an
        ``interrupted`` window with no established state would leave the interruption point to be
        guessed, and a non-interrupted window carrying one would assert a phase it never reached.
        """
        interrupted = self.completion_status == "interrupted"
        if interrupted and self.interruption_state not in ACQUISITION_INTERRUPTION_STATES:
            message = (
                f"an interrupted window must record one of {ACQUISITION_INTERRUPTION_STATES} as "
                f"its interruption state, not {self.interruption_state!r}; the interruption point "
                "is established from durable evidence or the window is refused"
            )
            raise AcquisitionGateError(message)
        if not interrupted and self.interruption_state is not None:
            message = (
                f"a window that ended {self.completion_status!r} carries interruption state "
                f"{self.interruption_state!r}; only a genuinely interrupted window has one"
            )
            raise AcquisitionGateError(message)


@dataclass(slots=True)
class _InFlightRetrieval:
    """What the engine durably knows about the one retrieval it was executing.

    Deliberately not a phase enum. It records the two facts a later interruption must reconcile
    against durable state — which planned request was in flight, and what the snapshot store
    returned for it, if it returned at all — and leaves the *classification* to
    :meth:`AcquisitionEngine._established_interruption_state`, which reads the raw store and the
    catalog rather than trusting how far this object got.
    """

    request: LogicalRequest
    observation: SourceObservation | None = None


def verify_window_bindings(
    *,
    plan: RequestPlan,
    window: str,
    approved_ceiling: int,
    authorization: LiveOperationAuthorization,
) -> tuple[LogicalRequest, ...]:
    """Prove every window binding, and return the logical requests the window may place.

    The complete pre-transport bindings proof, extracted from
    :meth:`AcquisitionEngine.preflight` so the operator layer can run it **before a transport
    exists at all**. Decision 045 §6A.2 orders run registration before transport construction, and
    the engine holds an already-constructed client — so a proof that only ran inside the engine
    would necessarily run *after* the transport it is supposed to gate. This function is that
    proof, in one place, with one implementation.

    Checked, in order: the authorization's window; the window's membership of the accepted set;
    the plan's own window; the exact approved plan hash; the operator ceiling equal to the
    authorization exactly; the plan-derived ceiling equal to the authorization exactly; the plan's
    own expansion arithmetic; and every route's registration, window membership, and constructed
    URL against the filing-body prohibition.

    Nothing here opens a socket, constructs a transport, reads configuration, or touches the
    catalog. It returns the requests it proved rather than a boolean, so a caller cannot act on a
    passing check without also taking the expansion it was checked against.

    Raises:
        AcquisitionGateError: any binding does not match.
    """
    if authorization.window != window:
        message = (
            f"the authorization names window {authorization.window!r} but this run executes "
            f"{window!r}"
        )
        raise AcquisitionGateError(message)
    if window not in ACQUISITION_WINDOWS:
        message = f"window {window!r} is not an accepted acquisition window"
        raise AcquisitionGateError(message)
    if plan.acquisition_window != window:
        message = (
            f"the approved plan is for window {plan.acquisition_window!r}, not "
            f"{window!r}; a plan is never executed against another window"
        )
        raise AcquisitionGateError(message)

    if plan.request_plan_sha256 != authorization.plan_sha256:
        message = (
            "the approved plan hash does not match the authorization; the run consumes "
            "exactly the plan the owner approved"
        )
        raise AcquisitionGateError(message)
    if approved_ceiling != authorization.approved_ceiling:
        message = (
            f"the supplied ceiling gate is set to {approved_ceiling}, but the "
            f"authorization approves {authorization.approved_ceiling}; the ceiling must equal "
            "the approved integer exactly"
        )
        raise AcquisitionGateError(message)
    if plan.hard_request_ceiling != authorization.approved_ceiling:
        message = (
            f"the approved plan derives a ceiling of {plan.hard_request_ceiling}, but "
            f"the authorization approves {authorization.approved_ceiling}"
        )
        raise AcquisitionGateError(message)

    requests = derive_logical_requests(plan)
    if len(requests) != plan.planned_unique_logical_requests:
        message = (
            f"the plan totals {plan.planned_unique_logical_requests} logical requests "
            f"but expands to {len(requests)}"
        )
        raise AcquisitionGateError(message)
    _verify_routes(requests, window)
    return requests


def _restricted(
    requests: Sequence[LogicalRequest],
    identities: frozenset[str],
) -> tuple[LogicalRequest, ...]:
    """Narrow a proved expansion to exactly the identities a resume is still owed.

    Narrowing, never widening: every identity must already be in the proved expansion, so a
    restriction cannot introduce a request the window bindings did not verify. An empty
    restriction and an unknown identity are both refused rather than silently ignored — the
    first would execute nothing while reporting a lawful run, and the second would mean the
    continuation proposal and the plan disagree about what the window contains.
    """
    available = {request.identity_label: request for request in requests}
    unknown = sorted(identities - set(available))
    if unknown:
        message = (
            f"the continuation remainder names planned identit(ies) {unknown} that the approved "
            "plan does not expand to; the proposal and the plan disagree about this window"
        )
        raise AcquisitionGateError(message)
    if not identities:
        message = (
            "the continuation remainder is empty, so this invocation has nothing lawful to place"
        )
        raise AcquisitionGateError(message)
    return tuple(request for request in requests if request.identity_label in identities)


def _verify_routes(requests: Sequence[LogicalRequest], window: str) -> None:
    """Prove every planned route is registered, in-window, and not a filing body.

    Window membership is enforced in **both** directions. Contract §17 stop condition 5 names
    "a dependent request in M3.2A **or a bootstrap request in M3.2B**", so each window admits
    only its own families and nothing else — an allowlist of every registered source would
    enforce one half of that rule and silently permit the other.
    """
    allowed = (
        frozenset(M3_2A_BOOTSTRAP_ROUTES)
        if window == "M3.2A"
        else frozenset(M3_2B_DEPENDENT_ROUTES)
    )
    for request in requests:
        spec = require_registered(request.source_id)
        if request.source_id not in allowed:
            message = (
                f"route {request.source_id!r} is not a {window} route; a dependent "
                "request in the bootstrap window, or a bootstrap request in the dependent "
                "window, is a stop condition"
            )
            raise AcquisitionGateError(message)
        url = spec.url(**dict(request.parameters))
        if filing_body_url_is_prohibited(url):
            message = (
                f"route {request.source_id!r} constructs a filing-body or accession URL; "
                "Milestone 3.2 acquires metadata only"
            )
            raise AcquisitionGateError(message)


# --------------------------------------------------------------------------- #
# Subphase B.4 — the engine
# --------------------------------------------------------------------------- #
def _utc_now() -> str:
    """The governed clock's default: an explicit UTC instant in Z form."""
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


@dataclass(slots=True)
class AcquisitionEngine:
    """Executes one acquisition window over an injected transport.

    Every collaborator is supplied explicitly. The engine constructs no transport, no client
    credential, and no ceiling of its own, and it reads no configuration file: a caller that
    cannot supply an authorized plan, the exact approved ceiling, an authenticated client, and an
    explicit :class:`LiveOperationAuthorization` simply cannot run it.

    Args:
        plan: The approved request plan, already parsed from its stored document.
        window: The window this run executes. Must match the plan's own window.
        ceiling: The shared cumulative physical-attempt gate, constructed by the caller with the
            exact approved integer. The engine never raises or replaces it.
        client: The accepted response-policy client, constructed by the caller over an injected
            transport and carrying ``ceiling`` so every wire attempt is counted.
        storage: The prepared data root and its accepted stores.
        recorder: The accepted observation recorder, bound to an open catalog writer.
        clock: Returns the UTC instant recorded on observations. Injected so a run is
            deterministic under test.
        progress: Optional per-request callback for operator output.
        run_binding: The already-registered M3.2 acquisition-run identity this invocation
            executes under (Decision 045 §6A). When supplied, every planned logical request this
            window reaches a disposition for is durably attributed to that run through
            ``census_plan_sources``. It is never minted here: the operator layer registers and
            verifies it *before* a transport exists, and passes the proven binding in.
        restrict_to_identities: The exact planned identities this invocation may place. Supplied
            only by a resume, from the accepted continuation proposal's remaining set, so an
            already-satisfied request is never re-requested and no substantive write is duplicated
            (Decision 045 §14). ``None`` executes the plan's whole expansion, which is what a
            fresh invocation does.
        response_log: The ordered physical-response record a :class:`RecordingTransport` appends
            to. When supplied, per-response accounting (Decision 045 §§9-11) is accumulated in
            :attr:`accounting` as each logical request completes.
    """

    plan: RequestPlan
    window: str
    ceiling: PhysicalAttemptCeiling
    client: SecClient
    storage: StorageBinding
    recorder: ObservationRecorder
    clock: Callable[[], str] = _utc_now
    progress: Callable[[RequestOutcome], None] | None = None
    run_binding: AcquisitionRunBinding | None = None
    restrict_to_identities: frozenset[str] | None = None
    response_log: PhysicalResponseLog | None = None
    accounting: ResponseAccounting = field(default_factory=lambda: ResponseAccounting())
    ledger: PreSendAttemptLedger | None = None
    """The write-ahead physical-attempt ledger bound to this run, on the governed live path.

    When supplied (``execute_live_acquisition`` wires it beside the recording transport), the
    durable ``ops_retrieval_attempts`` reservation count — not the in-memory ceiling — is the
    accepted source of this window's consumed physical-attempt count (Decision 051 §6, §7.2;
    contract §12). The ceiling remains the untouched hard pre-attempt guard. Left ``None`` by the
    accepted offline and fixture callers, which count from the ceiling exactly as before.
    """
    progress_failures: tuple[str, ...] = field(default=(), init=False)
    _authorization: LiveOperationAuthorization | None = field(default=None, init=False)
    _requests: tuple[LogicalRequest, ...] = field(default=(), init=False)
    _in_flight: _InFlightRetrieval | None = field(default=None, init=False)
    _committed_any: bool = field(default=False, init=False)
    _baseline_consumed: int = field(default=0, init=False)

    # -- preflight ---------------------------------------------------------- #
    def preflight(self, authorization: LiveOperationAuthorization) -> tuple[LogicalRequest, ...]:
        """Validate every binding, and return the logical requests this window will place.

        Runs **before the first transport call** and refuses rather than continuing. Every check
        lives in :func:`verify_window_bindings`, which the operator layer calls *before it builds a
        transport at all* (Decision 045 §6, §6A.2). Restating them here is deliberate defence in
        depth rather than duplication: the engine refuses the same bindings a second time, from the
        one implementation, so no caller can reach :meth:`run` around them.

        Passing preflight authorizes nothing on its own — it records that the bindings this
        engine was given are mutually consistent. The operator layer remains responsible for the
        complete live-authorization conjunction.

        Raises:
            AcquisitionGateError: any binding does not match.
        """
        requests = verify_window_bindings(
            plan=self.plan,
            window=self.window,
            approved_ceiling=self.ceiling.approved_ceiling,
            authorization=authorization,
        )
        if self.restrict_to_identities is not None:
            requests = _restricted(requests, self.restrict_to_identities)
        self._authorization = authorization
        self._requests = requests
        return requests

    # -- execution ---------------------------------------------------------- #
    def run(self) -> WindowOutcome:  # noqa: PLR0912 - one explicit termination ladder
        """Execute the window and return its outcome.

        The loop stops before, never after, the attempt that would exceed the ceiling: headroom
        is checked before each logical request, and the shared gate additionally refuses inside
        the client so a retry, a redirect hop, or a controlled post-cooldown request cannot slip
        past. Requests not reached are recorded as ``not_attempted`` rather than omitted, so the
        classification totals always sum to the planned count.

        A genuine external interruption — the catchable ``KeyboardInterrupt`` a SIGINT delivers —
        is caught here, at the narrowest layer that knows which planned request was in flight and
        how many attempts it consumed. Catching it any deeper would lose the attempt accounting a
        resume needs; catching it any shallower would lose which request it happened during. When
        the interruption point cannot be **established exactly** from durable evidence the
        interrupt is re-raised unchanged, so a falsely resumable window is never produced.

        Raises:
            AcquisitionGateError: :meth:`preflight` has not run.
            KeyboardInterrupt: the invocation was interrupted and the exact interruption state
                could not be established. Deliberately propagated rather than absorbed.
        """
        if self._authorization is None:
            message = (
                "preflight has not run; the engine refuses to reach a transport before its "
                "bindings and its explicit live authorization are validated"
            )
            raise AcquisitionGateError(message)

        closed_periods = _closed_period_flags(self.plan)
        outcomes: list[RequestOutcome] = []
        stopped: CompletionStatus | None = None
        stop_reasons: tuple[str, ...] = ()
        stop_detail = ""
        interruption_state: str | None = None

        # The consumption this window starts from, captured before any request is placed. On a
        # fresh window it is zero; on a resume it is the carry-forward the ceiling was constructed
        # with. The durable ledger only counts *this run's* reservations, so this baseline is what
        # keeps the window's consumed count cumulative when the physical-attempt source is the
        # ledger rather than the ceiling (Decision 051 §5, §6).
        self._baseline_consumed = self.ceiling.consumed

        for index, request in enumerate(self._requests):
            if stopped is not None:
                outcomes.append(RequestOutcome(request=request, disposition="not_attempted"))
                continue
            if self.ceiling.is_exhausted:
                stopped = "stopped_at_ceiling"
                stop_reasons = ("SEC_REQUEST_CEILING_EXHAUSTED",)
                stop_detail = (
                    f"the approved ceiling {self.ceiling.approved_ceiling} was consumed with "
                    f"{len(self._requests) - index} planned logical request(s) remaining"
                )
                outcomes.append(RequestOutcome(request=request, disposition="not_attempted"))
                continue

            before_durable = self._durable_consumed()
            try:
                outcome = self._execute(request, closed_periods)
            except KeyboardInterrupt:
                # A genuine external interruption *during* this retrieval. The attempts it already
                # consumed are real, so it is `stopped` rather than `not_attempted`, and the
                # window carries the interruption state the durable evidence establishes. A state
                # that cannot be established exactly re-raises: no receipt is better than a
                # receipt that advertises a resume nothing can safely start from.
                interruption_state = self._established_interruption_state()
                if interruption_state is None:
                    raise
                stopped = "interrupted"
                stop_reasons = (ACQUISITION_INTERRUPTED_REASON,)
                stop_detail = _INTERRUPTION_DETAIL
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="stopped",
                        attempts=self._durable_consumed() - before_durable,
                        reason_codes=stop_reasons,
                        detail=stop_detail,
                    )
                )
                continue
            except RequestCeilingExhaustedError as exc:
                # The ceiling refused an attempt *inside* this request — during a retry, a redirect
                # hop, or the controlled post-cooldown request. Attempts already consumed for it
                # are real, so it is `stopped`, never `not_attempted`.
                stopped = "stopped_at_ceiling"
                stop_reasons = (exc.reason_code,)
                stop_detail = str(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="stopped",
                        attempts=self._durable_consumed() - before_durable,
                        reason_codes=(exc.reason_code,),
                        detail=str(exc),
                    )
                )
                continue
            except ProhibitedRetrievalError as exc:
                # A pre-transport policy refusal from the accepted client: an unregistered source,
                # a missing purpose, a filing-body URL, or a URL outside the registered family.
                # Preflight already proved none of those, so reaching here is an internal
                # inconsistency and the window stops. It carries no reason code: nothing was
                # placed and nothing is being classified, and the one registered code that might
                # look apt — SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY — is defined as a redirect hop
                # or final URL leaving the family, which this is not.
                stopped = "stopped_by_gate"
                stop_reasons = ()
                stop_detail = str(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="stopped",
                        attempts=self._durable_consumed() - before_durable,
                        detail=str(exc),
                    )
                )
                continue
            except _OPERATIONAL_FAILURES as exc:
                # A storage, catalog, path-policy, or integrity failure after the request was
                # placed. Discarding the window here would throw away the classification of every
                # request already committed, along with the attempt accounting a later resume
                # needs, so the window terminates with a recorded outcome instead of an exception.
                # Nothing is repaired, retried, adopted, or deleted: the failure is reported and
                # the run stops. The detail names the failure class and a public description
                # only — never the exception's own arguments, which routinely carry an absolute
                # private path.
                stopped = "failed"
                stop_reasons = ()
                stop_detail = _operational_detail(exc)
                outcomes.append(
                    RequestOutcome(
                        request=request,
                        disposition="failed",
                        attempts=self._durable_consumed() - before_durable,
                        detail=stop_detail,
                    )
                )
                continue

            outcomes.append(outcome)
            try:
                self._report(outcome)
            except KeyboardInterrupt:
                # Interrupted *between* logical requests: this one is fully committed and already
                # classified, and the next one has not begun. Nothing is in flight, so the state
                # is read from what the catalog and raw store durably agree on.
                interruption_state = self._established_interruption_state()
                if interruption_state is None:
                    raise
                stopped = "interrupted"
                stop_reasons = (ACQUISITION_INTERRUPTED_REASON,)
                stop_detail = _INTERRUPTION_DETAIL

        return self._finalize(
            tuple(outcomes),
            stopped,
            stop_reasons,
            stop_detail,
            interruption_state=interruption_state,
        )

    def _durable_consumed(self) -> int:
        """The physical attempts this window consumed, from the durable ledger when there is one.

        On the governed live path a :class:`PreSendAttemptLedger` commits one
        ``ops_retrieval_attempts`` row immediately before each physical send, so the durable
        reservation count — added to the consumption carried forward from a predecessor — is the
        exact number of physical attempts actually reserved (Decision 051 §6, §7.2; contract §12).
        Reading it here, rather than :attr:`PhysicalAttemptCeiling.consumed`, is what keeps an
        interruption in the pre-send window from charging an attempt that left no durable trace: the
        in-memory ceiling may have incremented before the reservation committed, but no row means no
        charge. The ceiling is untouched and remains the hard pre-attempt guard.

        Without a ledger — the accepted offline and fixture callers — the in-memory ceiling remains
        the count, so their behaviour is unchanged.
        """
        if self.ledger is None:
            return self.ceiling.consumed
        return self._baseline_consumed + self.ledger.reserved_count()

    def _report(self, outcome: RequestOutcome) -> None:
        """Hand one outcome to the optional progress callback, defensively.

        The callback is operator output: observational, and never part of the acquisition result.
        A failing progress sink must not be able to discard a window whose objects are already
        promoted and whose rows are already committed, so its failure is contained here and
        recorded as an observable rather than propagated.

        **Decision 045 §12.** The sink is operator-controlled code, so its exception message is
        operator-controlled text: it can carry an absolute personal path, an email address, or a
        credential, and this driver's own retained state feeds receipts, reconciliation reports,
        and other written artifacts. So the raw text is emitted **only** to the local stderr
        diagnostic channel and never retained. What is retained is bounded and structural: the
        planned request's identity label, one fixed internal reason, and the exception's *class
        name*, allowlist-sanitized and length-bounded so a class named to smuggle content still
        cannot. Nothing here reads ``str(exc)`` into retained state, so exclusion does not depend
        on the receipt's prohibited-content validator noticing afterwards.
        """
        if self.progress is None:
            return
        try:
            self.progress(outcome)
        except Exception as exc:  # noqa: BLE001 - an operator sink may fail any way it likes
            _emit_progress_diagnostic(outcome.request.identity_label, exc)
            self.progress_failures = (
                *self.progress_failures,
                sanitized_progress_failure(outcome.request.identity_label, exc),
            )

    def _execute(
        self,
        request: LogicalRequest,
        closed_periods: Mapping[str, bool],
    ) -> RequestOutcome:
        """Place one logical request, store its object, and record its observation.

        Streaming is chosen from the registered route specification, never fixed for every route:
        a bulk archive is streamed to its ``.part`` spool and promoted from there, while a bounded
        metadata document is buffered as before. See :func:`route_is_streamed`.

        The in-flight marker is maintained across the two durable boundaries this method crosses —
        raw-object promotion and catalog commit — so an interruption knows *which* request and
        *which* observation to reconcile against durable state. It is a pointer to the evidence,
        never the verdict: :meth:`_established_interruption_state` reads the raw store and the
        catalog and can contradict it in either direction.
        """
        self._in_flight = _InFlightRetrieval(request=request)
        spec = require_registered(request.source_id)
        period_is_closed = (
            closed_periods.get(request.instance_key) if request.instance_key else None
        )
        with self.client.fetch(
            request.source_id,
            purpose=_ACQUISITION_PURPOSE,
            parameters=dict(request.parameters) or None,
            stream=route_is_streamed(spec),
        ) as result:
            # Response accounting is absorbed the moment the retrieval returns, before any
            # storage or catalog work. A storage or catalog failure downstream is an
            # `_OPERATIONAL_FAILURES` the run loop records as a terminated window, and the
            # physical responses this request already produced are real either way — absorbing
            # afterwards would drop them from the receipt totals exactly when the window most
            # needs them accounted (Decision 045 §9.2).
            self._absorb_response_events(result)
            observation = self.storage.snapshot_store.record(
                result,
                retrieved_at_utc=self.clock(),
                period_is_closed=period_is_closed,
            )
        self._in_flight = _InFlightRetrieval(request=request, observation=observation)
        observation = self._record_observation(spec, request, observation)
        outcome = self._classify(request, observation)
        self._in_flight = None
        self._committed_any = True
        return outcome

    # -- interruption ------------------------------------------------------- #
    def _established_interruption_state(self) -> str | None:
        """The exact interruption state, or ``None`` when durable evidence cannot establish one.

        **Decision 045 correction, MAJOR-1.** The rule is evidence-first. The in-flight marker says
        which retrieval and which observation to look for; what decides is what the catalog and the
        raw store durably hold:

        * a **committed** source observation for the in-flight retrieval is
          ``after_catalog_commit`` — the retrieval counts as completed and a later resume must not
          request it again;
        * a retrieval whose newly promoted object is present and still hashes as recorded, with no
          committed observation, is ``after_raw_store_write_before_catalog_commit`` — the object
          and its lineage survive as durable orphan evidence for the accepted recovery path, and
          nothing here deletes them to make recovery simpler;
        * a retrieval that promoted no new object of its own and committed nothing is
          ``before_raw_store_write``, and stays eligible for a later SAFE resume.

        Two things are deliberately **not** treated as promotions. A ``304`` reuse and a
        byte-identical duplicate reuse a *predecessor's* object, which does not belong to this
        retrieval; a failure or quarantine promotes nothing at all. All four are
        ``before_raw_store_write``.

        Every path that would otherwise have to assume something returns ``None`` instead: a
        snapshot store interrupted before it returned, with an unaccounted object or a missing
        referent anywhere in the raw store, cannot be told apart from a promotion that completed,
        and a promoted object that no longer verifies is not evidence of anything. A catalog or
        filesystem error while establishing this is likewise ``None``. The caller re-raises, so no
        receipt is written at all — which is the whole point: an interruption that cannot be
        classified exactly must not advertise a resume.
        """
        try:
            return self._interruption_state_from_evidence()
        except (DisclosureDriftError, sqlite3.Error, OSError):
            return None

    def _interruption_state_from_evidence(self) -> str | None:
        """The evidence reading itself, with failures left to the caller to treat as inexact.

        The state describes the **interrupted retrieval**, not the last successful one. So a
        retrieval that was in flight decides the answer even when an earlier request committed
        cleanly: reporting that earlier request's ``after_catalog_commit`` would state that the
        interrupted retrieval had committed, which is exactly the false claim a resume must not be
        handed. Only when nothing was in flight does the previous request's commit decide it.
        """
        in_flight = self._in_flight
        if in_flight is not None and in_flight.observation is not None:
            observation = in_flight.observation
            if self._observation_is_committed(observation.observation_id):
                return "after_catalog_commit"
            if observation.outcome in _PROMOTING_OUTCOMES:
                if not self._verified(observation):
                    return None
                return "after_raw_store_write_before_catalog_commit"
            if self._unaccounted_raw_evidence():
                return None
            return "before_raw_store_write"

        # Either no retrieval had begun, or the snapshot store was interrupted before it returned
        # its observation. Both leave nothing durable for the retrieval itself, so both are
        # `before_raw_store_write` — but only once the raw store agrees that nothing unaccounted
        # was promoted, because an interrupted promotion is indistinguishable from a completed one
        # from inside this frame.
        if self._unaccounted_raw_evidence():
            return None
        if in_flight is not None:
            return "before_raw_store_write"
        return "after_catalog_commit" if self._committed_any else "before_raw_store_write"

    def _observation_is_committed(self, observation_id: str) -> bool:
        """Whether this observation is durably committed, read back rather than believed.

        The recorder commits each observation in its own transaction, and that transaction rolls
        back on any exception including a ``KeyboardInterrupt`` raised inside it. So a row visible
        here is a row that committed, and its absence is not "maybe": it is the rolled-back case.
        """
        row = self.recorder.writer.connection.execute(
            "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        return row is not None

    def _unaccounted_raw_evidence(self) -> bool:
        """Whether the raw store holds anything that contradicts "nothing was promoted".

        An orphan object — present on disk, referenced by no committed row — is exactly a promotion
        whose commit did not happen, so its existence means this invocation cannot claim it stopped
        before raw-store promotion. A missing referent is the opposite direction and equally
        disqualifying: a committed row whose object is gone leaves what persisted unknowable.

        A ``.part`` spool is deliberately **not** disqualifying. A spool is by definition
        unpromoted — the accepted store writes it under ``staging`` and promotes out of it — so an
        interrupted stream leaving one behind is precisely the ``before_raw_store_write`` case, not
        a contradiction of it.
        """
        observed = observe_recovery_state(
            storage=self.storage,
            observations=load_observations(self.recorder.writer.connection),
            ceiling=self.ceiling,
        )
        return bool(observed.orphan_objects or observed.missing_referents)

    def _absorb_response_events(self, result: FetchResult) -> None:
        """Account every physical response this retrieval produced, exactly once.

        A no-op when no :class:`RecordingTransport` is wired: an offline caller that injects a
        transport directly still runs, and simply produces no response-event totals.
        """
        if self.response_log is None:
            return
        self.accounting.absorb(result, self.response_log.drain())

    def _record_observation(
        self,
        spec: SourceSpec,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> SourceObservation:
        """Commit one observation, streaming archive lineage when the route owns one.

        The acquired object is the **archive itself**; members are lineage recorded beside it, not
        separately authorized retrievals. Three cases:

        * a newly promoted archive (``stored_new`` / ``superseded``) is opened through the accepted
          archive reader and its validated members are **streamed** into the observation's
          transaction;
        * a reused archive (``unchanged_content`` / ``reused_snapshot``) passes no explicit members
          — the accepted recorder resolves the owning observation's preserved lineage and verifies
          it identifies the same object, which is the reconciliation this stage owes;
        * every other outcome has no object to enumerate.

        Streaming is what makes the whole path bounded, and it moves the archive verdict from
        *before* the write to *during* it. A corrupt archive, a refused member, or an archive
        carrying none of the members it was retrieved for now surfaces mid-transaction, so the
        observation and any rows already written roll back together and the retrieval is recorded
        once, as ``quarantined``, with the accepted registered reason. The catalog therefore never
        sees a partial archive: it sees the whole lineage or none of it. The promoted object stays
        preserved on disk either way — nothing is deleted, repaired, or retried, and no member
        payload is written anywhere.
        """
        prepared = self._with_absence_reason(request, observation)
        if not route_is_streamed(spec) or observation.outcome not in {"stored_new", "superseded"}:
            self.recorder.record(prepared)
            return prepared

        try:
            self.recorder.record(prepared, members=self._archive_members(spec, observation))
        except ArchiveDefenceError as exc:
            quarantined = self._with_absence_reason(
                request,
                replace(
                    observation,
                    outcome="quarantined",
                    reason_codes=(exc.reason_code,),
                    detail=str(exc),
                ),
            )
            self.recorder.record(quarantined)
            return quarantined
        return prepared

    def _archive_members(
        self,
        spec: SourceSpec,
        observation: SourceObservation,
    ) -> Iterator[ArchiveMember]:
        """Yield the archive's validated members once, holding at most one at a time.

        A single pass over the accepted reader, with nothing accumulated. The reader is not
        re-entered, no member is retained after it is yielded, and the archive is read from the
        stored immutable object rather than from anything held in memory — which is what keeps the
        cost of recording lineage proportional to the largest single member instead of to the whole
        expanded archive. Every accepted archive protection still applies, unchanged and at its
        registered limits.

        An archive carrying no accepted member is refused **here**, at the end of the one pass,
        rather than by inspecting a materialized collection: emptiness is only knowable once the
        reader is exhausted, and raising the accepted defence error is what lets the caller record
        the retrieval as quarantined instead of committing an archive with no lineage.
        """
        seen = 0
        for member in iter_members(
            self.storage.snapshot_store.payload_path(observation),
            name_suffix=_ARCHIVE_MEMBER_SUFFIX,
            archive_relative_path=observation.relative_storage_path,
            archive_sha256=observation.logical_sha256,
        ):
            seen += 1
            yield member
        if seen == 0:
            message = (
                f"the {spec.source_id} archive carried no {_ARCHIVE_MEMBER_SUFFIX} members, so it "
                "cannot stand as the bootstrap metadata object it was retrieved to be"
            )
            raise ArchiveDefenceError(message, "RAW_ARCHIVE_INVALID")

    def _with_absence_reason(
        self,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> SourceObservation:
        """Attach the registered absence reason when a required object is left absent.

        The accepted response policy classifies a ``404`` on an archival path as absent evidence
        and deliberately attaches no reason code, because at that layer it is an ordinary outcome.
        At *this* layer it is a required object left absent, and the operational catalog is the
        durable home of that fact (T2 packet §10 item 1; Decision 040 §5). So the registered code
        is attached to the observation before it is committed, rather than only to the in-memory
        outcome — a reconciliation report read from the catalog alone must be able to see it.

        Two registered codes, split exactly as Decision 040 §4 fixes. A quarterly index instance
        keeps ``INDEX_INSTANCE_UNAVAILABLE`` in every window, unchanged. Every other required
        M3.2A request whose committed observation is terminally ``failed`` or ``quarantined``
        additionally carries ``SOURCE_REQUIRED_OBJECT_UNAVAILABLE`` beside — never instead of —
        any more specific defect code the policy already attached. The new mapping is bounded to
        the M3.2A window; Decision 040 authorizes no M3.2B mapping.
        """
        if observation.outcome not in {"failed", "quarantined"}:
            return observation
        if request.source_id == _INDEX_ROUTE:
            if _INDEX_ABSENT_REASON in observation.reason_codes:
                return observation
            return replace(
                observation,
                reason_codes=(*observation.reason_codes, _INDEX_ABSENT_REASON),
            )
        if self.window != "M3.2A":
            return observation
        if _REQUIRED_OBJECT_ABSENT_REASON in observation.reason_codes:
            return observation
        return replace(
            observation,
            reason_codes=(*observation.reason_codes, _REQUIRED_OBJECT_ABSENT_REASON),
        )

    def _classify(
        self,
        request: LogicalRequest,
        observation: SourceObservation,
    ) -> RequestOutcome:
        """Map one recorded observation to its terminal disposition.

        Verification is re-run rather than inferred: an observation that claims a payload is
        treated as satisfying its request only when the stored bytes still hash to the recorded
        ``content_sha256``. That is what keeps "terminally classified" and "satisfied" different
        facts rather than the same one under two names.
        """
        disposition: RequestDisposition
        if observation.outcome == "quarantined":
            disposition = "quarantined"
        elif observation.outcome == "failed":
            disposition = "absent" if observation.http_status == 404 else "failed"
        elif observation.outcome == "reused_snapshot":
            disposition = "satisfied_reused"
        elif observation.outcome == "unchanged_content":
            disposition = "satisfied_duplicate"
        else:
            disposition = "satisfied_new"

        if disposition in {
            "satisfied_new",
            "satisfied_duplicate",
            "satisfied_reused",
        } and not self._verified(observation):
            disposition = "failed"

        return RequestOutcome(
            request=request,
            disposition=disposition,
            observation_id=observation.observation_id,
            content_sha256=observation.content_sha256,
            relative_storage_path=observation.relative_storage_path,
            stored_size_bytes=observation.stored_size_bytes,
            media_type=observation.declared_content_type,
            http_status=observation.http_status,
            attempts=observation.attempts,
            reason_codes=observation.reason_codes,
            detail=observation.detail,
        )

    def _verified(self, observation: SourceObservation) -> bool:
        """Whether the observation's stored object exists and still hashes as recorded."""
        if not observation.relative_storage_path or not observation.content_sha256:
            return False
        try:
            self.storage.snapshot_store.verify_payload(observation)
        except DisclosureDriftError:
            return False
        except OSError:
            return False
        return True

    def _finalize(
        self,
        outcomes: tuple[RequestOutcome, ...],
        stopped: CompletionStatus | None,
        stop_reasons: tuple[str, ...],
        stop_detail: str,
        *,
        interruption_state: str | None = None,
    ) -> WindowOutcome:
        """Assemble the window outcome under the accepted completion semantics."""
        assert self._authorization is not None  # noqa: S101 - run() proves this first
        self._attribute_to_run(outcomes)
        self._refuse_unaccounted_responses()
        planned = len(self._requests)
        satisfied = sum(1 for outcome in outcomes if outcome.satisfies_requirement)

        if stopped is not None:
            status: CompletionStatus = stopped
            reasons = stop_reasons
            detail = stop_detail
        elif satisfied == planned:
            status = "complete"
            reasons = ()
            detail = "every planned logical request is satisfied by a verified object"
        else:
            status = "incomplete"
            reasons = ()
            detail = (
                f"{planned - satisfied} of {planned} planned logical request(s) left their "
                "required object absent; the window is not successfully complete and is not "
                "eligible for the freeze, dependent planning, or Gate H"
            )

        return WindowOutcome(
            window=self.window,
            plan_sha256=self._authorization.plan_sha256,
            approved_ceiling=self.ceiling.approved_ceiling,
            consumed_physical_attempts=self._durable_consumed(),
            planned_logical_requests=planned,
            outcomes=outcomes,
            completion_status=status,
            reason_codes=reasons,
            detail=detail,
            interruption_state=interruption_state,
            progress_failures=self.progress_failures,
        )

    def _attribute_to_run(self, outcomes: Sequence[RequestOutcome]) -> None:
        """Durably attribute every planned request of this invocation to its run.

        Decision 045 §6A.4. The relation is the **existing** ``census_plan_sources``, whose
        semantics `_plan_source_row` documents; nothing here creates a table, a column, a
        migration, or a vocabulary. Every planned logical request gets one row — including the
        ones left ``not_attempted`` or ``stopped`` — because a run's attribution is a statement
        about the work it *owned*, and omitting the unreached requests would make an interrupted
        run indistinguishable from a smaller one.

        A no-op when no run binding was supplied, which is how the accepted offline and fixture
        callers keep working unchanged.

        Raises:
            AcquisitionRunError: attribution could not be committed. Fail-closed and deliberately
                not swallowed: a run whose observations are not durably attributable cannot be
                scoped by ``show-drift --run``, so the operator layer refuses rather than writing
                a receipt that would assert a run identity nothing is bound to.
        """
        if self.run_binding is None:
            return
        now = self.clock()
        try:
            with self.recorder.writer.batch():
                for outcome in outcomes:
                    self.recorder.writer.insert(
                        "census_plan_sources",
                        _plan_source_row(self.run_binding, outcome, recorded_at_utc=now),
                    )
        except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
            message = (
                f"the acquisition run's observation attribution could not be committed "
                f"({type(exc).__name__}); a run whose observations are not durably attributable "
                "is refused rather than reported as a lawful run"
            )
            raise AcquisitionRunError(message) from exc

    def _refuse_unaccounted_responses(self) -> None:
        """Mark the accounting uncertain when a physical response reached no bucket.

        Reachable only when a logical request abandons its retrieval without returning a result —
        a mid-request ceiling refusal, or the accepted client's pre-transport policy refusal. Both
        are unreachable on a lawful invocation: :func:`verify_window_bindings` proves every route
        before the window starts, and a ceiling equal to the plan's own
        ``Σ U × A_reachable`` always leaves each request its full worst case (a resume that does
        not is refused by :func:`propose_continuation` before execution begins). This is therefore
        a fail-closed backstop, and it refuses rather than infers: Decision 045 §9.5 requires the
        accounting to be exact or to stop.
        """
        if self.response_log is None or not self.response_log.pending:
            return
        self.accounting.mark_undetermined(
            f"{len(self.response_log.drain())} physical response(s) were observed by a logical "
            "request that abandoned its retrieval without returning a result, so their "
            "response-policy classification cannot be established"
        )


# --------------------------------------------------------------------------- #
# Foundational recovery observability (inspection only; repair is stage T2.4)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    """What a read-only sweep of the data root and catalog can see.

    Deliberately observational. Nothing here resumes, retries, repairs, deletes, adopts, or
    resets a counter: the deterministic repair applier, the reconciliation report, drift
    inspection, and the resume boundary are stage T2.4.
    """

    partial_objects: tuple[str, ...]
    orphan_objects: tuple[str, ...]
    missing_referents: tuple[str, ...]
    consumed_physical_attempts: int
    approved_ceiling: int

    @property
    def is_clean(self) -> bool:
        """Whether nothing needs a later recovery decision."""
        return not (self.partial_objects or self.orphan_objects or self.missing_referents)

    @property
    def outcome_is_uncertain(self) -> bool:
        """Whether a transaction's durable outcome cannot be determined from what is visible.

        A catalog row whose object is missing is the uncertain case the accepted semantics treat
        as ``UNDETERMINED``: it cannot be told apart from a committed row whose object was never
        promoted. A caller that sees this must refer to the owner rather than resume (contract
        §12); this property states the fact and takes no action on it.
        """
        return bool(self.missing_referents)

    @property
    def remaining_headroom(self) -> int:
        """Ceiling headroom left, for a later resume decision that this does not make."""
        return max(0, self.approved_ceiling - self.consumed_physical_attempts)


def observe_recovery_state(
    *,
    storage: StorageBinding,
    observations: Sequence[SourceObservation],
    ceiling: PhysicalAttemptCeiling,
) -> RecoveryObservation:
    """Report what a read-only sweep can see, without changing anything.

    Args:
        storage: The prepared data root and its stores.
        observations: Committed catalog observations for this run.
        ceiling: The window's attempt gate, read for its cumulative state only.
    """
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }
    partial: list[str] = []
    orphans: list[str] = []
    tree = storage.tree
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name.endswith((".reason", LINEAGE_SUFFIX)):
                continue
            relative = tree.relative(path)
            if path.name.endswith(".part"):
                partial.append(relative)
            elif relative not in recorded:
                orphans.append(relative)

    # A streamed body is spooled to `staging/sec` before it is ever promoted, so an interruption
    # mid-transfer leaves its `.part` there and nowhere else. Scanning only the raw subtrees would
    # report such a run as clean — which is exactly the state a later recovery decision must not
    # be allowed to miss. An orphan is not derivable here: a spool is by definition unpromoted and
    # has no catalog row to be missing from.
    partial.extend(_staging_partials(tree))

    missing = [
        relative for relative in sorted(recorded) if not (tree.data_root / relative).is_file()
    ]
    return RecoveryObservation(
        partial_objects=tuple(sorted(partial)),
        orphan_objects=tuple(orphans),
        missing_referents=tuple(missing),
        consumed_physical_attempts=ceiling.consumed,
        approved_ceiling=ceiling.approved_ceiling,
    )


def _staging_partials(tree: DataTree) -> list[str]:
    """Relative paths of streamed ``.part`` spools left in the staging tree.

    Read-only, and deliberately link-averse: a symlinked component is skipped rather than followed,
    because inspection must not be a way to reach outside the data root. Nothing here mutates,
    adopts, quarantines, or deletes a spool — that is the T2.4 repair applier's decision to make.
    """
    staging = tree.staging
    if not staging.is_dir() or staging.is_symlink():
        return []
    found: list[str] = []
    for path in sorted(staging.rglob("*")):
        if path.is_symlink() or not path.is_file() or not path.name.endswith(".part"):
            continue
        found.append(tree.relative(path))
    return found


def load_approved_plan(payload: bytes) -> RequestPlan:
    """Read an approved plan document, proving it canonical.

    A thin, deliberate re-export of the accepted reader: the driver consumes the stored plan the
    owner approved and never rebuilds one from inputs, so this is the only way a plan enters an
    acquisition run.
    """
    return request_plan_from_document(payload)


# =========================================================================== #
# Stage T2.4 — recovery, reconciliation, resume boundaries, and drift control
# (Decision 040 §§2–7. Everything below is read-only except the explicit
#  recovery-action applier, which mutates only when invoked with one action.)
# =========================================================================== #

#: The four deterministic recovery-action classes Decision 040 §2 (T2.4-D) authorizes. A request
#: naming anything else — including a would-be combined or list-valued action — is refused,
#: never coerced, and never partially applied.
RECOVERY_ACTIONS: Final[tuple[str, ...]] = (
    "adopt-orphan",
    "quarantine-partial",
    "rebuild-projection",
    "remove-stale-part",
)

#: The derived audit projection the rebuild action reconstructs — the accepted filename the
#: recorder, the read-only inspector, and ``observation_catalog.reconcile`` all share.
_PROJECTION_NAME: Final = "census_source_observations.jsonl"

#: Registered reason codes whose presence on a committed observation is a schema-drift event for
#: the deterministic drift listing (Decision 040 §2, T2.4-B). Whether an event blocks is read
#: from the registry's own ``blocks_release`` metadata, never re-declared here: a retained
#: unknown-field record and an ordinary living-source update are nonblocking, and every
#: immutable-identity mutation, validator contradiction, malformed payload, and invalid archive
#: blocks.
_DRIFT_REASON_CODES: Final[tuple[str, ...]] = (
    "PARSER_SCHEMA_DRIFT_OBSERVED",
    "RAW_ARCHIVE_INVALID",
    "RAW_ARCHIVE_MEMBER_REFUSED",
    "SEC_RESPONSE_MALFORMED",
    "SOURCE_CONTENT_UPDATED",
    "SOURCE_DATED_ARTIFACT_CHANGED",
    "SOURCE_IMMUTABLE_IDENTITY_MUTATED",
    "SOURCE_VALIDATOR_CONTRADICTION",
)

#: The exhaustive continuation-state partition. Every item state ``reconcile_requests`` emits
#: belongs to **exactly one** of the four sets below, and their union is the complete
#: emitted-state vocabulary — enforced fail-closed at emission, so a new state can never fall
#: through the partition silently. Continuation treatment is decided from this one mechanism:
#:
#: * **satisfying** — verified satisfying evidence; excluded from replay, never re-requested;
#: * **retryable** — genuinely retryable open work under the accepted Decision 040 semantics
#:   (failed, quarantined, stopped, absent, not attempted); included exactly once in the
#:   continuation remainder, because the work is still owed and is re-acquired under its own
#:   accounting, never reclassified in place;
#: * **blocking** — a defect that explicitly refuses continuation; never counted satisfied, and
#:   omitted from the transport remainder only because the whole proposal is refused;
#: * **uncertain** — durable persistence or attribution cannot be established; the proposal is
#:   ``UNDETERMINED`` and continuation is prohibited.
_SATISFYING_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {
        "satisfied_duplicate",
        "satisfied_new",
        "satisfied_not_modified",
        "satisfied_superseding",
    }
)
_RETRYABLE_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {"absent", "failed", "not_attempted", "quarantined", "stopped"}
)
_BLOCKING_ITEM_STATES: Final[frozenset[str]] = frozenset(
    {"archive_lineage_missing_or_invalid", "hash_mismatch"}
)
_UNCERTAIN_ITEM_STATES: Final[frozenset[str]] = frozenset({"row_without_object"})
_ITEM_STATE_VOCABULARY: Final[frozenset[str]] = (
    _SATISFYING_ITEM_STATES
    | _RETRYABLE_ITEM_STATES
    | _BLOCKING_ITEM_STATES
    | _UNCERTAIN_ITEM_STATES
)

#: Item conditions that escalate a retryable item to blocking treatment. A failed, quarantined,
#: or absent item carrying one of these has residual evidence that cannot be lawfully retried
#: without adjudication: its evidence is unusable or unverifiable, or its absence carries no
#: registered terminal reason and is an adjudication defect rather than ordinary open work.
_BLOCKING_ITEM_CONDITIONS: Final[frozenset[str]] = frozenset(
    {"absence_without_terminal_reason", "unverifiable_evidence"}
)

#: The generic write-ahead state scenario Decision 041 §6 fixes for the T2.4 applier. Stored
#: only in ``census_recovery_states``, whose schema does not constrain scenario vocabulary; it
#: must never be inserted into ``census_recovery_events``, whose scenario set is separately
#: CHECK-constrained.
_T2_4_STATE_SCENARIO: Final = "t2_4_recovery_action"

#: A staging spool's nonce, exactly as the accepted snapshot store names it:
#: ``{registered source_id}-{uuid4 hex}.part``. Registered source identifiers contain no ``-``,
#: so the rightmost ``-`` splits the route prefix from the nonce exactly.
_SPOOL_NONCE: Final = re.compile(r"^[0-9a-f]{32}$")


class RepairRefusedError(AcquisitionError):
    """Raised when the explicit recovery applier refuses a requested action.

    Refusal is the applier's default posture: an unknown or multi-action request, an action that
    differs from the deterministic recommendation, a stale or already-resolved target, any
    ``UNDETERMINED`` state, and any request whose one authorized primitive cannot be scoped to
    exactly the named target without unrelated mutation are all refused before anything mutates.
    """


# --------------------------------------------------------------------------- #
# T2.4-A — catalog-authoritative reconstruction
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CatalogReconstruction:
    """Catalog-authoritative state, rebuilt fresh at one continuation boundary.

    Decision 040 §2 (T2.4-A): the operational catalog is the durable source of truth. This is
    the composition that opens it read-only, loads every durable observation in the catalog's
    own deterministic order, and adopts them into a **fresh** :class:`SnapshotStore`. An earlier
    process's mutable in-memory snapshot state is discarded by construction — this composition
    simply does not accept one, so nothing can inherit it. Quarantined, failed, and otherwise
    unusable observations are adopted as *facts* (reconciliation must see them) but are never
    selectable for reuse: selection flows through the accepted ``latest_for`` usability rules,
    and :func:`verified_reusable_predecessor` re-verifies immutable evidence at the point of
    reuse.
    """

    observations: tuple[SourceObservation, ...]
    store: SnapshotStore
    archive_member_counts: Mapping[str, int]
    archive_lineage_mismatches: Mapping[str, int]
    blocked_recovery_states: int
    blocked_t2_4_recovery_states: int
    """Blocked write-ahead states carrying the exact T2.4 scenario.

    A subset of :attr:`blocked_recovery_states`. Kept separately because an unresolved
    ``t2_4_recovery_action`` block means a T2.4 recovery mutation may have begun without its
    completed event and exact resolution — persistence-uncertain state that a continuation
    proposal must classify ``UNDETERMINED``, not merely unsafe.
    """

    def latest_any(self, source_id: str, identity: str) -> SourceObservation | None:
        """The newest observation for one request identity, usable or not."""
        for observation in reversed(self.observations):
            if observation.source_id == source_id and observation.identity == identity:
                return observation
        return None

    def by_id(self, observation_id: str) -> SourceObservation | None:
        """The observation carrying ``observation_id``, or ``None``."""
        for observation in self.observations:
            if observation.observation_id == observation_id:
                return observation
        return None


def reconstruct_catalog_state(
    *,
    catalog_path: Path,
    storage: StorageBinding,
) -> CatalogReconstruction:
    """Rebuild lawful in-memory state from the durable catalog, writing nothing.

    The connection is the read-only inspector's own (``PRAGMA query_only``), so a write is
    impossible rather than merely unintended. Archive-member lineage is summarized per owning
    observation as bounded aggregates — a count and a mismatch count against the owner's own
    recorded archive identity — never materialized row by row, so a bulk archive's lineage
    cannot pull the whole expansion into memory.

    Raises:
        AcquisitionGateError: the catalog does not exist; reconstruction refuses to invent one.
    """
    if not Path(catalog_path).is_file():
        message = (
            "the operational catalog does not exist; catalog-authoritative reconstruction "
            "refuses to begin from anything but the durable catalog"
        )
        raise AcquisitionGateError(message)

    with read_only_catalog(Path(catalog_path)) as connection:
        observations = load_observations(connection)
        member_counts: dict[str, int] = {}
        for row in connection.execute(
            "SELECT observation_id, COUNT(*) AS members FROM census_archive_members "
            "GROUP BY observation_id ORDER BY observation_id"
        ).fetchall():
            member_counts[str(row["observation_id"])] = int(row["members"])
        mismatches: dict[str, int] = {}
        for observation in observations:
            if member_counts.get(observation.observation_id, 0) == 0:
                continue
            mismatch_row = connection.execute(
                "SELECT COUNT(*) AS mismatched FROM census_archive_members "
                "WHERE observation_id = ? AND (archive_relative_path IS NOT ? "
                "OR archive_sha256 IS NOT ?)",
                (
                    observation.observation_id,
                    observation.relative_storage_path,
                    observation.logical_sha256,
                ),
            ).fetchone()
            mismatched = int(mismatch_row["mismatched"])
            if mismatched:
                mismatches[observation.observation_id] = mismatched
        blocked = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_recovery_states WHERE resolution_state = 'blocked'"
            ).fetchone()[0]
        )
        blocked_t2_4 = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_recovery_states "
                "WHERE resolution_state = 'blocked' AND scenario = ?",
                (_T2_4_STATE_SCENARIO,),
            ).fetchone()[0]
        )

    store = SnapshotStore(storage.tree, storage.raw_store)
    store.adopt(observations)
    return CatalogReconstruction(
        observations=observations,
        store=store,
        archive_member_counts=member_counts,
        archive_lineage_mismatches=mismatches,
        blocked_recovery_states=blocked,
        blocked_t2_4_recovery_states=blocked_t2_4,
    )


def verified_reusable_predecessor(
    reconstruction: CatalogReconstruction,
    source_id: str,
    identity: str | None = None,
) -> SnapshotIndex | None:
    """The latest usable predecessor for one identity, re-verified now — or ``None``.

    Lawful reuse demands more than a row (Decision 040 §2, T2.4-A/C): the latest usable
    observation must resolve through the accepted evidence-owner chain, the owning object must
    still hash exactly as recorded, and an archive owner must carry complete, consistent member
    lineage. Anything less returns ``None`` — a quarantined, failed, missing, tampered, or
    lineage-less predecessor is simply not reusable, and the distinction is reported by the
    reconciliation rather than leaked here as an exception.
    """
    index = reconstruction.store.latest_for(source_id, identity)
    if not index.has_snapshot or index.evidence_observation_id is None:
        return None
    owner = reconstruction.by_id(index.evidence_observation_id)
    if owner is None:
        return None
    try:
        reconstruction.store.verify_payload(owner)
    except (DisclosureDriftError, OSError):
        return None
    spec = require_registered(source_id)
    if spec.expected_content == "zip":
        if reconstruction.archive_member_counts.get(owner.observation_id, 0) == 0:
            return None
        if reconstruction.archive_lineage_mismatches.get(owner.observation_id, 0):
            return None
    return index


def conditional_validators(
    reconstruction: CatalogReconstruction,
    source_id: str,
    identity: str | None = None,
) -> tuple[str | None, str | None] | None:
    """``(etag, last_modified)`` drawn from a lawful verified predecessor, else ``None``.

    Decision 040 §2 (T2.4-C): validators are supplied **only** from a predecessor that verifies
    at the point of reuse — never from an unverified, quarantined, superseded-away, or
    lineage-less row. A predecessor carrying neither validator yields ``None`` rather than an
    empty pair, because a conditional request with nothing to condition on is not one.
    """
    index = verified_reusable_predecessor(reconstruction, source_id, identity)
    if index is None:
        return None
    if index.etag is None and index.last_modified is None:
        return None
    return (index.etag, index.last_modified)


# --------------------------------------------------------------------------- #
# T2.4-B — deterministic reconciliation and drift inspection (read-only)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    """One planned logical request's durable, catalog-derived state."""

    position: int
    source_id: str
    identity_label: str
    request_identity: str
    state: str
    observation_id: str | None
    verified: bool
    excluded_from_continuation: bool
    attempts: int
    reason_codes: tuple[str, ...]
    conditions: tuple[str, ...]

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "attempts": self.attempts,
            "conditions": list(self.conditions),
            "excluded_from_continuation": self.excluded_from_continuation,
            "identity_label": self.identity_label,
            "observation_id": self.observation_id,
            "position": self.position,
            "reason_codes": list(self.reason_codes),
            "request_identity": self.request_identity,
            "source_id": self.source_id,
            "state": self.state,
            "verified": self.verified,
        }


def _classify_item(item: ReconciliationItem) -> str:
    """Assign one reconciliation item to exactly one continuation-treatment category.

    Total and fail-closed over :data:`_ITEM_STATE_VOCABULARY`: a state outside the partition
    raises instead of falling through, so every item contributes exactly once to continuation
    treatment. A retryable item whose conditions show unusable or unverifiable residual
    evidence, or an absence carrying no registered terminal reason, escalates to ``blocking`` —
    that evidence cannot be lawfully retried without adjudication.
    """
    state = item.state
    if state in _UNCERTAIN_ITEM_STATES:
        return "uncertain"
    if state in _BLOCKING_ITEM_STATES:
        return "blocking"
    if state in _SATISFYING_ITEM_STATES:
        return "satisfying"
    if state in _RETRYABLE_ITEM_STATES:
        if any(condition in _BLOCKING_ITEM_CONDITIONS for condition in item.conditions):
            return "blocking"
        return "retryable"
    message = (
        f"reconciliation emitted item state {state!r}, which is outside the exhaustive "
        "continuation-state partition; an unclassifiable state refuses rather than falls "
        "through every set"
    )
    raise AcquisitionGateError(message)


@dataclass(frozen=True, slots=True)
class StoreFinding:
    """One store-level inconsistency the reconciliation surfaces without acting on it."""

    kind: str
    relative_path: str | None
    observation_id: str | None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "kind": self.kind,
            "observation_id": self.observation_id,
            "relative_path": self.relative_path,
        }


@dataclass(frozen=True, slots=True)
class DriftListingEntry:
    """One committed observation carrying registered drift reasons."""

    observation_id: str
    source_id: str
    request_identity: str
    reason_codes: tuple[str, ...]
    blocking: bool

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for serialization and comparison."""
        return {
            "blocking": self.blocking,
            "observation_id": self.observation_id,
            "reason_codes": list(self.reason_codes),
            "request_identity": self.request_identity,
            "source_id": self.source_id,
        }


@dataclass(frozen=True, slots=True)
class RequestReconciliation:
    """The deterministic plan-to-catalog reconciliation for one window.

    Read-only by construction: every input is durable state, every output is in-memory, and
    identical inputs produce a byte-identical :meth:`as_record` serialization. Item-level
    absence identities live here and in the catalog — never in a receipt (Decision 040 §9).
    """

    window: str
    plan_sha256: str
    items: tuple[ReconciliationItem, ...]
    out_of_plan: tuple[tuple[str, str], ...]
    store_findings: tuple[StoreFinding, ...]
    drift: tuple[DriftListingEntry, ...]
    blocked_recovery_states: int
    #: Observations that are out of the *successor* plan only because an owner-approved endpoint
    #: substitution moved their identity (Decision 062 §8). Listed separately from
    #: :attr:`out_of_plan` rather than removed from it, so the evidence stays visible and countable:
    #: a superseded identity is reported, kept, and excluded from blocking — never hidden.
    superseded_out_of_plan: tuple[tuple[str, str], ...] = ()

    @property
    def totals(self) -> Mapping[str, int]:
        """Per-state item totals; always sums to the planned logical request count."""
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.state] = counts.get(item.state, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def absences(self) -> tuple[ReconciliationItem, ...]:
        """Planned requests whose terminal disposition left the required object absent."""
        return tuple(
            item for item in self.items if item.state in {"absent", "failed", "quarantined"}
        )

    @property
    def absences_without_terminal_reason(self) -> tuple[ReconciliationItem, ...]:
        """Absences carrying no registered reason code — each one an adjudication defect."""
        return tuple(item for item in self.absences if not item.reason_codes)

    @property
    def already_satisfied_excluded_count(self) -> int:
        """Every request excluded from the future continuation run.

        The future receipt's ``cache_hit_count`` (Decision 040 §6): already satisfied by
        verified evidence and therefore never requested again. This is a **snapshot over the
        whole durable history**, so it deliberately **overlaps** the two historical disposition
        counters below — a request whose satisfying evidence is a lawful ``304``
        (:attr:`not_modified_count`) or a byte-identical ``200``
        (:attr:`duplicate_object_count`) is *also* excluded here. The three snapshot counters
        must never be summed as mutually exclusive outcomes. The future receipt mapping stays:
        excluded request → ``cache_hit_count``; physically requested lawful ``304`` →
        ``not_modified_count``; physically requested byte-identical ``200`` →
        ``duplicate_object_count``.
        """
        return sum(1 for item in self.items if item.excluded_from_continuation)

    @property
    def not_modified_count(self) -> int:
        """Items whose satisfying evidence is a lawful conditional ``304`` reuse.

        The future receipt's ``not_modified_count`` (Decision 040 §6): a request physically
        attempted with accepted validators and reconciled against preserved evidence. As a
        historical disposition counter it may overlap
        :attr:`already_satisfied_excluded_count` — the same item counts in both — so the two
        are never additive.
        """
        return sum(1 for item in self.items if item.state == "satisfied_not_modified")

    @property
    def duplicate_object_count(self) -> int:
        """Items whose satisfying evidence is a byte-identical ``200`` reconciliation.

        The future receipt's ``duplicate_object_count`` (Decision 040 §6): a physically
        retrieved response whose bytes matched preserved immutable evidence. As a historical
        disposition counter it may overlap :attr:`already_satisfied_excluded_count` — the same
        item counts in both — so the two are never additive.
        """
        return sum(1 for item in self.items if item.state == "satisfied_duplicate")

    @property
    def blocking_drift(self) -> tuple[DriftListingEntry, ...]:
        """Drift events whose registered reasons block."""
        return tuple(entry for entry in self.drift if entry.blocking)

    @property
    def nonblocking_drift(self) -> tuple[DriftListingEntry, ...]:
        """Drift events observed and retained without blocking."""
        return tuple(entry for entry in self.drift if not entry.blocking)

    @property
    def is_clean(self) -> bool:
        """Whether nothing requires adjudication, repair, or referral."""
        return (
            not self.absences
            and not self.out_of_plan
            and not self.store_findings
            and not self.blocking_drift
            and self.blocked_recovery_states == 0
            and all(_classify_item(item) == "satisfying" for item in self.items)
            and all(not item.conditions for item in self.items)
        )

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping: identical inputs serialize byte-identically."""
        return {
            "blocked_recovery_states": self.blocked_recovery_states,
            "drift": [entry.as_record() for entry in self.drift],
            "items": [item.as_record() for item in self.items],
            "out_of_plan": [list(pair) for pair in self.out_of_plan],
            "plan_sha256": self.plan_sha256,
            "store_findings": [finding.as_record() for finding in self.store_findings],
            "superseded_out_of_plan": [list(pair) for pair in self.superseded_out_of_plan],
            "totals": dict(self.totals),
            "window": self.window,
        }


def planned_request_identity(request: LogicalRequest) -> str:
    """The normalized request identity the driver records for one planned request.

    Public because the read-only recovery inspection derives condition 8.8's identity-level
    remainder from exactly this function and :func:`derive_logical_requests` (Decision 064 §6). One
    implementation, one expansion, one identity: the inspection's remainder and the continuation
    remainder cannot be two different counts of two differently-derived request sets.
    """
    spec = require_registered(request.source_id)
    url = spec.url(**dict(request.parameters))
    return request_identity(request.source_id, url, dict(request.parameters))


def _drift_flags(reason_codes: tuple[str, ...]) -> tuple[tuple[str, ...], bool]:
    """The drift-family codes on one observation, and whether any of them blocks."""
    family = tuple(code for code in reason_codes if code in _DRIFT_REASON_CODES)
    blocking = any(REASON_CODES[code].blocks_release for code in family if code in REASON_CODES)
    return family, blocking


def _evidence_conditions(
    reconstruction: CatalogReconstruction,
    observation: SourceObservation,
) -> tuple[str, ...]:
    """Why a usable-looking observation's evidence does not verify, as stable conditions."""
    conditions: list[str] = []
    owner_id = observation.reused_observation_id or observation.observation_id
    owner = reconstruction.by_id(owner_id) or observation
    try:
        path = reconstruction.store.payload_path(owner)
    except DisclosureDriftError:
        return ("row_without_object",)
    if not path.is_file():
        return ("row_without_object",)
    try:
        reconstruction.store.verify_payload(owner)
    except (DisclosureDriftError, OSError):
        conditions.append("hash_mismatch")
    spec = SOURCES.get(observation.source_id)
    if spec is not None and spec.expected_content == "zip":
        members = reconstruction.archive_member_counts.get(owner.observation_id, 0)
        mismatched = reconstruction.archive_lineage_mismatches.get(owner.observation_id, 0)
        if members == 0 or mismatched:
            conditions.append("archive_lineage_missing_or_invalid")
    return tuple(conditions)


def _item_for(
    position: int,
    request: LogicalRequest,
    reconstruction: CatalogReconstruction,
    in_flight_request_identity: str | None,
) -> ReconciliationItem:
    """Derive one planned request's item record from durable state alone."""
    identity = planned_request_identity(request)
    predecessor = verified_reusable_predecessor(reconstruction, request.source_id, identity)
    latest = reconstruction.latest_any(request.source_id, identity)
    conditions: list[str] = []

    if predecessor is not None and predecessor.observation_id is not None:
        satisfying = reconstruction.by_id(predecessor.observation_id)
        state = {
            "stored_new": "satisfied_new",
            "superseded": "satisfied_superseding",
            "unchanged_content": "satisfied_duplicate",
            "reused_snapshot": "satisfied_not_modified",
        }[satisfying.outcome if satisfying is not None else "stored_new"]
        observation_id = predecessor.observation_id
        verified = True
        excluded = True
        attempts = satisfying.attempts if satisfying is not None else 0
        reason_codes = satisfying.reason_codes if satisfying is not None else ()
    elif latest is None:
        state = "not_attempted"
        observation_id = None
        verified = False
        excluded = False
        attempts = 0
        reason_codes = ()
        if identity == in_flight_request_identity:
            state = "stopped"
            conditions.append("receiptless_in_flight")
    else:
        observation_id = latest.observation_id
        verified = False
        excluded = False
        attempts = latest.attempts
        reason_codes = latest.reason_codes
        if latest.outcome == "quarantined":
            state = "quarantined"
        elif latest.outcome == "failed":
            state = "absent" if latest.http_status == 404 else "failed"
        else:
            evidence = _evidence_conditions(reconstruction, latest)
            conditions.extend(evidence)
            if "row_without_object" in evidence:
                state = "row_without_object"
            elif "archive_lineage_missing_or_invalid" in evidence:
                state = "archive_lineage_missing_or_invalid"
            elif "hash_mismatch" in evidence:
                state = "hash_mismatch"
            else:
                state = "failed"
                conditions.append("unverifiable_evidence")

    if state in {"absent", "failed", "quarantined"} and not reason_codes:
        conditions.append("absence_without_terminal_reason")
    family, blocking = _drift_flags(tuple(reason_codes))
    if family:
        conditions.append("drift_blocking" if blocking else "drift_nonblocking")

    return ReconciliationItem(
        position=position,
        source_id=request.source_id,
        identity_label=request.identity_label,
        request_identity=identity,
        state=state,
        observation_id=observation_id,
        verified=verified,
        excluded_from_continuation=excluded,
        attempts=attempts,
        reason_codes=tuple(reason_codes),
        conditions=tuple(conditions),
    )


def reconcile_requests(
    *,
    plan: RequestPlan,
    reconstruction: CatalogReconstruction,
    storage: StorageBinding,
    in_flight_request_identity: str | None = None,
    plan_transition: PlanTransitionAuthority | None = None,
) -> RequestReconciliation:
    """Reconcile the approved plan against durable catalog and object state. Writes nothing.

    Output order is the plan's own deterministic expansion order; store findings and drift
    entries are sorted; identical inputs produce a byte-identical serialization. Detection
    never repairs: an orphan, a partial, a missing referent, or blocking drift is *reported*,
    and every mutation belongs to the separately invoked recovery applier.

    ``plan_transition``, when supplied, is a verified Decision 062 authority: the one committed
    observation whose identity that transition superseded is reported under
    ``superseded_out_of_plan`` instead of ``out_of_plan``. Every other out-of-plan observation is
    unaffected.
    """
    requests = derive_logical_requests(plan)
    items = tuple(
        _item_for(position, request, reconstruction, in_flight_request_identity)
        for position, request in enumerate(requests)
    )
    for item in items:
        if item.state not in _ITEM_STATE_VOCABULARY:
            message = (
                f"reconciliation emitted item state {item.state!r} for "
                f"{item.identity_label!r}, which is outside the exhaustive continuation-state "
                "vocabulary; emission refuses rather than letting a state fall through the "
                "partition"
            )
            raise AcquisitionGateError(message)

    planned = {(request.source_id, planned_request_identity(request)) for request in requests}
    unplanned = sorted(
        {
            (observation.source_id, observation.identity)
            for observation in reconstruction.observations
            if (observation.source_id, observation.identity) not in planned
        }
    )
    superseded = tuple(
        pair
        for pair in unplanned
        if superseded_out_of_plan_observation(plan_transition, pair[0], pair[1])
    )
    out_of_plan = tuple(pair for pair in unplanned if pair not in set(superseded))

    sweep = observe_recovery_state(
        storage=storage,
        observations=reconstruction.observations,
        ceiling=PhysicalAttemptCeiling(0),
    )
    findings: list[StoreFinding] = []
    for relative in sweep.partial_objects:
        findings.append(
            StoreFinding(kind="partial_object", relative_path=relative, observation_id=None)
        )
    for relative in sweep.orphan_objects:
        findings.append(
            StoreFinding(kind="orphan_object", relative_path=relative, observation_id=None)
        )
    referents = {
        observation.relative_storage_path: observation.observation_id
        for observation in reconstruction.observations
        if observation.relative_storage_path
    }
    for relative in sweep.missing_referents:
        findings.append(
            StoreFinding(
                kind="row_without_object",
                relative_path=relative,
                observation_id=referents.get(relative),
            )
        )
    findings.sort(key=lambda finding: (finding.kind, finding.relative_path or ""))

    drift: list[DriftListingEntry] = []
    for observation in reconstruction.observations:
        family, blocking = _drift_flags(observation.reason_codes)
        if family:
            drift.append(
                DriftListingEntry(
                    observation_id=observation.observation_id,
                    source_id=observation.source_id,
                    request_identity=observation.identity,
                    reason_codes=family,
                    blocking=blocking,
                )
            )
    drift.sort(key=lambda entry: entry.observation_id)

    return RequestReconciliation(
        window=plan.acquisition_window,
        plan_sha256=plan.request_plan_sha256,
        items=items,
        out_of_plan=out_of_plan,
        store_findings=tuple(findings),
        drift=tuple(drift),
        blocked_recovery_states=reconstruction.blocked_recovery_states,
        superseded_out_of_plan=superseded,
    )


# --------------------------------------------------------------------------- #
# Decision 062 §7 — the bounded predecessor -> successor plan transition
# --------------------------------------------------------------------------- #
class PlanTransitionRefusedError(AcquisitionError):
    """Raised when a proposed plan transition is not the one Decision 062 authorizes.

    Refusal is the default and every check is literal: this mechanism exists for one external
    endpoint drift, and any mismatch — a second substitution, a changed route, a changed parameter,
    a changed ceiling, a changed quarter set, an arbitrary URL, a registry version either receipt
    does not record — refuses rather than being interpreted charitably.
    """


def verify_plan_transition(
    *,
    predecessor_plan: RequestPlan,
    successor_plan: RequestPlan,
    predecessor_source_registry_version: str | None,
) -> PlanTransitionAuthority:
    """Verify Decision 062 §7's seventeen conditions and return the resulting authority.

    The seventeen are checked here rather than at the point of use because only here are both
    plans *expanded*: conditions 8, 13, 16, and 17 are statements about the concrete logical request
    identities two plans authorize, and a plan document names routes and counts, not URLs. Comparing
    the expansions is what makes "exactly one substitution" a proved fact instead of a description.

    Args:
        predecessor_plan: the plan the predecessor run executed.
        successor_plan: the plan the continuation would execute.
        predecessor_source_registry_version: the registry version the **predecessor receipt**
            recorded. Read from the receipt, never from the predecessor plan document: condition 14
            is about what the run recorded at the time, and the pre-Decision-062 plan schema
            recorded no registry version at all.

    Raises:
        PlanTransitionRefusedError: any of the seventeen conditions does not hold.
    """
    # 1. An explicit accepted owner decision names both plan hashes. The names are the frozen
    #    constants; the comparison is literal, in both directions, so neither a predecessor that is
    #    not the retired plan nor a successor that is not the approved one can enter.
    _require_transition(
        predecessor_plan.request_plan_sha256 == PLAN_TRANSITION_PREDECESSOR_PLAN_SHA256,
        f"the predecessor plan is {predecessor_plan.request_plan_sha256}, not the plan "
        f"{PLAN_TRANSITION_DECISION_REFERENCE} names as the predecessor",
    )
    _require_transition(
        successor_plan.request_plan_sha256 == PLAN_TRANSITION_SUCCESSOR_PLAN_SHA256,
        f"the successor plan is {successor_plan.request_plan_sha256}, not the plan "
        f"{PLAN_TRANSITION_DECISION_REFERENCE} names as the successor",
    )

    # 2. The same M3.2 window, on both sides and against the decision's own binding.
    for label, plan in (("predecessor", predecessor_plan), ("successor", successor_plan)):
        _require_transition(
            plan.acquisition_window == PLAN_TRANSITION_ACQUISITION_WINDOW,
            f"the {label} plan names window {plan.acquisition_window!r}, not "
            f"{PLAN_TRANSITION_ACQUISITION_WINDOW!r}",
        )

    # 3. The same coverage, as-of, calendar, and rate inputs, and the same quarter set.
    _require_transition(
        _transition_inputs(predecessor_plan) == _transition_inputs(successor_plan),
        "the two plans do not share identical coverage, as-of, calendar, rate, and quarter inputs",
    )

    # 4, 6, 7, 17. The same routes, in the same order, with the same planned counts, the same
    #    derived A_reachable values, and therefore the same per-route attempt budget. Comparing the
    #    whole ordered tuple is what refuses an introduced or dropped route: a new route changes the
    #    tuple even when every shared route still agrees.
    _require_transition(
        _transition_routes(predecessor_plan) == _transition_routes(successor_plan),
        "the two plans do not share identical routes, planned counts, and A_reachable values",
    )
    _require_transition(
        predecessor_plan.maximum_physical_attempts == successor_plan.maximum_physical_attempts,
        f"the maximum physical attempt budget moves from "
        f"{predecessor_plan.maximum_physical_attempts} to "
        f"{successor_plan.maximum_physical_attempts}",
    )

    # 5. The same approved global ceiling, on both sides and against the decision's own binding.
    for label, plan in (("predecessor", predecessor_plan), ("successor", successor_plan)):
        _require_transition(
            plan.hard_request_ceiling == PLAN_TRANSITION_APPROVED_REQUEST_CEILING,
            f"the {label} plan's ceiling is {plan.hard_request_ceiling}, not the approved "
            f"{PLAN_TRANSITION_APPROVED_REQUEST_CEILING}",
        )

    # 8, 9, 13, 16. The expansions agree everywhere except one substitution.
    substitution = _verify_single_substitution(predecessor_plan, successor_plan)

    # 10, 11, 12. The substitution is exactly the one named: this route, this old URL, this new URL.
    source_id, old_url, new_url = substitution
    _require_transition(
        source_id == PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID,
        f"the substituted route is {source_id!r}, not {PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID!r}",
    )
    _require_transition(
        old_url == PLAN_TRANSITION_OLD_URL,
        f"the substituted route's old URL is {old_url!r}, not the retired path "
        f"{PLAN_TRANSITION_DECISION_REFERENCE} names",
    )
    _require_transition(
        new_url == PLAN_TRANSITION_NEW_URL,
        f"the substituted route's new URL is {new_url!r}, not the successor path "
        f"{PLAN_TRANSITION_DECISION_REFERENCE} names",
    )

    # 14. The predecessor receipt records the old registry version.
    _require_transition(
        predecessor_source_registry_version == PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION,
        f"the predecessor receipt records source registry "
        f"{predecessor_source_registry_version!r}, not "
        f"{PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION!r}; a transition away from an endpoint "
        f"presupposes a run that used it",
    )

    # 15. The successor run records the successor registry version. The receipt does not exist yet,
    #     so what is checkable now is the binding it will record: the successor plan's own.
    _require_transition(
        successor_plan.source_registry_version == PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION,
        f"the successor plan is bound to source registry "
        f"{successor_plan.source_registry_version!r}, not "
        f"{PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION!r}",
    )
    _require_transition(
        M22_SOURCE_REGISTRY_VERSION == PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION,
        f"the live source registry is {M22_SOURCE_REGISTRY_VERSION!r}, so a successor run would "
        f"record that rather than {PLAN_TRANSITION_SUCCESSOR_REGISTRY_VERSION!r}",
    )

    return PlanTransitionAuthority(
        predecessor_plan_sha256=predecessor_plan.request_plan_sha256,
        successor_plan_sha256=successor_plan.request_plan_sha256,
        substituted_source_id=source_id,
        old_url=old_url,
        new_url=new_url,
    )


def _require_transition(held: bool, refusal: str) -> None:  # noqa: FBT001 - a guard, not a flag
    """Refuse the transition unless the condition holds."""
    if not held:
        message = (
            f"the proposed plan transition is refused: {refusal}. "
            f"{PLAN_TRANSITION_DECISION_REFERENCE} authorizes exactly one substitution and creates "
            f"no general capability to resume against another plan."
        )
        raise PlanTransitionRefusedError(message)


def _transition_inputs(plan: RequestPlan) -> tuple[object, ...]:
    """Every planning input that must be identical across the transition."""
    return (
        plan.coverage_start,
        plan.coverage_end,
        plan.as_of_date,
        plan.include_open_quarter,
        plan.calendar_year,
        plan.calendar_evidence_entry_count,
        plan.requests_per_second,
        plan.required_index_keys,
        plan.expected_cache_hits,
    )


def _transition_routes(plan: RequestPlan) -> tuple[tuple[str, str, int, int], ...]:
    """The ordered route identity, host, planned count, and A_reachable of every route."""
    return tuple(
        (route.source_id, route.host, route.planned_unique_logical_requests, route.a_reachable)
        for route in plan.routes
    )


def _verify_single_substitution(
    predecessor_plan: RequestPlan,
    successor_plan: RequestPlan,
) -> tuple[str, str, str]:
    """Prove the two expansions differ in exactly one request identity, and return it.

    Both plans are expanded into their concrete logical requests and compared positionally. Position
    matters: two expansions holding the same identities in a different order would place requests in
    an order the predecessor's accounting was never built against, so an order change is a
    difference like any other rather than an equivalence.
    """
    before = derive_logical_requests(predecessor_plan)
    after = derive_logical_requests(successor_plan)
    _require_transition(
        len(before) == len(after),
        f"the predecessor plan expands to {len(before)} logical request(s) and the successor to "
        f"{len(after)}",
    )

    differences: list[tuple[str, str, str]] = []
    for position, (old, new) in enumerate(zip(before, after, strict=True)):
        _require_transition(
            old.source_id == new.source_id,
            f"position {position} changes route from {old.source_id!r} to {new.source_id!r}",
        )
        _require_transition(
            dict(old.parameters) == dict(new.parameters),
            f"position {position} changes the parameters of {old.source_id!r}",
        )
        _require_transition(
            old.instance_key == new.instance_key,
            f"position {position} changes the instance key of {old.source_id!r}",
        )
        old_url = _transition_url(predecessor_plan, old)
        new_url = _transition_url(successor_plan, new)
        if old_url != new_url:
            differences.append((old.source_id, old_url, new_url))

    _require_transition(
        len(differences) == PLAN_TRANSITION_SUBSTITUTION_COUNT,
        f"the two plans differ in {len(differences)} request identit(ies); "
        f"{PLAN_TRANSITION_DECISION_REFERENCE} authorizes exactly "
        f"{PLAN_TRANSITION_SUBSTITUTION_COUNT}",
    )
    return differences[0]


def _transition_url(plan: RequestPlan, request: LogicalRequest) -> str:
    """One planned request's normalized URL under a plan's own registry binding.

    The predecessor plan is bound to the retired registry and the successor to the live one, but
    only one registry is importable at a time, so the retired URL cannot be re-derived from the
    retired registry. It does not need to be: the retired path is a frozen Decision 062 constant,
    and substituting it for the one route whose identity moved reconstructs exactly the identity the
    predecessor run actually recorded — which the predecessor receipt and its committed observation
    both independently corroborate.
    """
    if (
        plan.source_registry_version == PLAN_TRANSITION_PREDECESSOR_REGISTRY_VERSION
        or plan.source_registry_version is None
    ) and request.source_id == PLAN_TRANSITION_SUBSTITUTED_SOURCE_ID:
        return PLAN_TRANSITION_OLD_URL
    spec = require_registered(request.source_id)
    return spec.url(**dict(request.parameters))


#: How the Decision 062 §8 supersession classifies the one committed observation the endpoint drift
#: stranded. It is a classification of *evidence*, never a state written anywhere: the failed
#: old-path observation stays stored, unrewritten, undeleted, and unsatisfying.
SUPERSEDED_BY_OWNER_APPROVED_ENDPOINT_DRIFT: Final = "SUPERSEDED_BY_OWNER_APPROVED_ENDPOINT_DRIFT"


def superseded_out_of_plan_observation(
    transition: PlanTransitionAuthority | None,
    source_id: str,
    request_identity_value: str,
) -> bool:
    """Whether one out-of-plan observation is the identity the transition superseded.

    Decision 062 §8: the committed old-path SIC failure is valid immutable historical failure
    evidence. Under the successor plan its identity is no longer planned, so the ordinary
    out-of-plan rule would classify it as an arbitrary blocking observation and refuse continuation
    forever — for evidence the owner explicitly ruled must be kept.

    The exception is deliberately the narrowest thing that resolves that: it applies only with a
    verified transition present, only to the one route the transition substituted, and only to the
    exact old identity, reconstructed from the transition's own frozen old URL rather than matched
    by prefix, suffix, or route alone. Any other out-of-plan observation — including a *different*
    observation on the same route — remains blocking.

    It changes no state and satisfies nothing. The successor SIC request stays unsatisfied and stays
    in the continuation remainder; only the blocking classification of the superseded old identity
    is lifted.
    """
    if transition is None:
        return False
    if source_id != transition.substituted_source_id:
        return False
    return request_identity_value == request_identity(source_id, transition.old_url, {})


# --------------------------------------------------------------------------- #
# T2.4-C — continuation proposal and conservative attempt accounting
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CumulativeAttemptAccounting:
    """The Decision 040 §7 cumulative consumed-attempt calculation, or its refusal.

    Exactly three addends, each counted once: the resolvable predecessor receipt chain's
    cumulative attempts; committed observation attempts deterministically attributed after the
    final terminating receipt; and the full registered ``A_reachable`` for at most one
    identifiable receiptless in-flight request. Any attribution ambiguity is ``UNDETERMINED``
    and prohibits continuation — never estimated, never rounded down.
    """

    chain_consumed: int
    post_receipt_attempts: int
    in_flight_charge: int
    in_flight_request_identity: str | None
    undetermined: bool
    basis: str

    @property
    def cumulative_consumed(self) -> int:
        """The conservative cumulative total charged against the approved ceiling."""
        return self.chain_consumed + self.post_receipt_attempts + self.in_flight_charge


@dataclass(frozen=True, slots=True)
class ContinuationRequest:
    """One remaining logical request, with lawful conditional validators where they exist."""

    position: int
    source_id: str
    identity_label: str
    request_identity: str
    etag: str | None
    last_modified: str | None


@dataclass(frozen=True, slots=True)
class ContinuationProposal:
    """A deterministic, read-only continuation proposal (Decision 040 §2, T2.4-C).

    A proposal only: continuation **authorization** remains an explicit later owner act, and
    continuation **execution** — ``m3 acquire --resume-from`` wiring — remains deferred to the
    operator-surface stage. Nothing here places a request, constructs a transport, emits a
    receipt, or mutates any durable state.
    """

    permitted: bool
    determination: str
    refusal_reasons: tuple[str, ...]
    window: str
    plan_sha256: str
    approved_ceiling: int
    predecessor_receipt_id: str | None
    receipt_chain: tuple[str, ...]
    accounting: CumulativeAttemptAccounting
    remaining_headroom: int
    worst_case_remaining_attempts: int
    fits: bool
    already_satisfied_excluded: tuple[str, ...]
    remaining: tuple[ContinuationRequest, ...]
    reconciliation: RequestReconciliation
    inspection: RecoveryState

    @property
    def already_satisfied_excluded_count(self) -> int:
        """The future receipt's ``cache_hit_count``: satisfied, so never requested."""
        return len(self.already_satisfied_excluded)


def _parse_receipt_instant(value: object) -> datetime | None:
    """Parse one RFC 3339 UTC instant; ``None`` when it cannot be trusted for ordering."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _segment_after_receipt(
    observations: Sequence[SourceObservation],
    completed_at: datetime,
) -> tuple[int, int, frozenset[tuple[str, str]], str | None]:
    """Split committed attempts around the final terminating receipt, or explain why not.

    Returns ``(pre_attempts, post_attempts, post_identities, undetermined_basis)``. A row whose
    instant is unparseable, or that coincides exactly with the receipt boundary, cannot be
    attributed uniquely — that is ``UNDETERMINED``, not a rounding choice.
    """
    pre_attempts = 0
    post_attempts = 0
    post_identities: set[tuple[str, str]] = set()
    for observation in observations:
        instant = _parse_receipt_instant(observation.retrieved_at_utc)
        if instant is None:
            return (
                0,
                0,
                frozenset(),
                (
                    f"observation {observation.observation_id} carries no attributable UTC "
                    "instant, so the post-receipt attempt segment cannot be attributed uniquely"
                ),
            )
        if instant == completed_at:
            return (
                0,
                0,
                frozenset(),
                (
                    f"observation {observation.observation_id} coincides exactly with the "
                    "terminating receipt boundary, so its segment cannot be attributed uniquely"
                ),
            )
        if instant > completed_at:
            post_attempts += observation.attempts
            post_identities.add((observation.source_id, observation.identity))
        else:
            pre_attempts += observation.attempts
    return pre_attempts, post_attempts, frozenset(post_identities), None


@dataclass(frozen=True, slots=True)
class _SpoolInterpretation:
    """What the staging spools durably identify, or why they cannot be interpreted."""

    routes: tuple[str, ...]
    undetermined_basis: str | None


def _interpret_staging_spools(tree: DataTree) -> _SpoolInterpretation:
    """Interpret staging ``.part`` spools by the accepted naming structure, fail-closed.

    A spool identifies a **route** only, and only when it is a regular file contained in the
    accepted staging root whose name parses exactly as
    ``{registered source_id}-{32-hex nonce}.part`` — the structure the accepted snapshot store
    writes. A symlinked staging root, a symlinked or escaping spool, a prefix that is not a
    registered source identifier, and a malformed nonce are each refused as ``UNDETERMINED``:
    an ambiguous generic string split never stands in for the accepted structure, and
    uncertainty never becomes a zero charge.
    """
    staging = tree.staging
    if staging.is_symlink():
        return _SpoolInterpretation(
            (), "the staging root is a symbolic link, so spool evidence cannot be trusted"
        )
    if not staging.is_dir():
        return _SpoolInterpretation((), None)
    resolved_staging = Path(os.path.realpath(staging))
    routes: list[str] = []
    for path in sorted(staging.rglob("*.part")):
        if path.is_symlink():
            return _SpoolInterpretation(
                (),
                f"staging spool {path.name!r} is a symbolic link and is refused as "
                "identification evidence",
            )
        if not path.is_file():
            return _SpoolInterpretation(
                (), f"staging entry {path.name!r} is not a regular spool file"
            )
        resolved = Path(os.path.realpath(path))
        if resolved_staging != resolved.parent and resolved_staging not in resolved.parents:
            return _SpoolInterpretation(
                (), f"staging spool {path.name!r} resolves outside the accepted staging root"
            )
        prefix, separator, nonce = path.name.removesuffix(".part").rpartition("-")
        if not separator or prefix not in SOURCES or _SPOOL_NONCE.fullmatch(nonce) is None:
            return _SpoolInterpretation(
                (),
                f"staging spool {path.name!r} does not parse as the accepted "
                "'{source_id}-{uuid}.part' structure, so its route identity cannot be "
                "established",
            )
        routes.append(prefix)
    return _SpoolInterpretation(tuple(routes), None)


def _contradicting_store_evidence(
    tree: DataTree,
    observations: Sequence[SourceObservation],
) -> tuple[str, ...]:
    """Unaccounted raw-store artifacts that contradict any single lawful in-flight identity.

    Raw-side ``.part`` partials, orphan objects, and stray lineage intents each mark durable
    activity with no lawful route identity of their own. When any exists, a single in-flight
    request cannot reasonably be the whole story, so identification refuses rather than
    charging one request and silently zero-charging the rest. Read-only, and symlink-averse
    like the accepted read-only observer.
    """
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }
    findings: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith(".reason"):
                continue
            relative = tree.relative(path)
            if path.name.endswith(LINEAGE_SUFFIX):
                object_path = path.with_name(path.name.removesuffix(LINEAGE_SUFFIX))
                object_relative = tree.relative(object_path)
                if object_relative not in recorded and not object_path.exists():
                    findings.append(relative)
                continue
            if path.name.endswith(".part") or relative not in recorded:
                findings.append(relative)
    return tuple(sorted(findings))


def _identify_in_flight(
    requests: Sequence[LogicalRequest],
    reconstruction: CatalogReconstruction,
    post_identities: frozenset[tuple[str, str]],
    spool_routes: tuple[str, ...],
) -> tuple[str | None, str | None]:
    """The one durably identified receiptless in-flight request, or why none can be named.

    Identification is evidence-based, never positional — plan-order position alone may never
    identify the request. A staging spool identifies a route; it identifies a logical request
    only when exactly one relevant spool exists, its route parses uniquely, exactly one
    unresolved planned request uses that route, every preceding planned request carries durable
    satisfying or terminal evidence, and no later request shows post-receipt activity. Any
    other reading — a route that disagrees with the sequential position, a shared route, or
    more than one possible in-flight request — is ``UNDETERMINED``, never a guess and never a
    zero charge.
    """
    if len(spool_routes) > 1:
        return None, (
            f"{len(spool_routes)} staging spools exist, so more than one in-flight request "
            "appears possible"
        )

    identities = [planned_request_identity(request) for request in requests]
    unresolved: list[int] = []
    for position, request in enumerate(requests):
        satisfied = (
            verified_reusable_predecessor(reconstruction, request.source_id, identities[position])
            is not None
        )
        has_row = reconstruction.latest_any(request.source_id, identities[position]) is not None
        if not satisfied and not has_row:
            unresolved.append(position)

    if not spool_routes:
        return None, None

    route = spool_routes[0]
    matching = [position for position in unresolved if requests[position].source_id == route]
    if not matching:
        return None, (
            f"the staging spool identifies route {route!r}, but no unresolved planned request "
            "uses that route; the durable evidence contradicts every candidate identity"
        )
    if len(matching) > 1:
        return None, (
            f"{len(matching)} unresolved planned requests share the spool's route {route!r}, "
            "so the in-flight logical request cannot be identified uniquely"
        )
    candidate = matching[0]
    if unresolved[0] != candidate:
        return None, (
            f"the staging spool's route {route!r} disagrees with the first unresolved planned "
            "request in the sequential engine's order; plan-order position alone may never "
            "identify the request, so the contradiction is UNDETERMINED"
        )
    for position in range(candidate + 1, len(requests)):
        if (requests[position].source_id, identities[position]) in post_identities:
            return None, (
                "post-receipt activity exists for a request after the identified one, so more "
                "than one in-flight request appears possible"
            )
    return identities[candidate], None


def propose_continuation(
    *,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    window: str,
    approved_ceiling: int,
    plan_transition: PlanTransitionAuthority | None = None,
    evidence_root: Path | None = None,
) -> ContinuationProposal:
    """Derive the deterministic continuation proposal for one interrupted window.

    Read-only, and bound to everything Decision 040 §2 (T2.4-C) names: the predecessor
    receipt-chain identity, the exact plan hash, the exact acquisition window, the exact
    approved ceiling, the durable catalog and object state, and the cumulative attempt
    evidence. Every refusal is carried in the result rather than raised, so a refused proposal
    is itself deterministic evidence; only caller errors (a missing catalog or head receipt)
    raise.

    Raises:
        AcquisitionGateError: the window is not an accepted acquisition window.
        RecoveryInspectionError: the catalog or the head receipt does not exist.
    """
    if window not in ACQUISITION_WINDOWS:
        message = f"window {window!r} is not one of the accepted acquisition windows"
        raise AcquisitionGateError(message)

    refusals: list[str] = []
    if plan.acquisition_window != window:
        refusals.append(
            f"the approved plan is for window {plan.acquisition_window!r}, not {window!r}"
        )
    if approved_ceiling != plan.hard_request_ceiling:
        refusals.append(
            f"the supplied ceiling {approved_ceiling} does not equal the plan's approved "
            f"ceiling {plan.hard_request_ceiling}; the ceiling is never reinterpreted"
        )

    inspection = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        data_root=storage.data_root,
        plan_transition=plan_transition,
        evidence_root=evidence_root,
    )
    reconstruction = reconstruct_catalog_state(catalog_path=catalog_path, storage=storage)
    requests = derive_logical_requests(plan)

    predecessor_receipt_id: str | None = None
    completed_at: datetime | None = None
    undetermined_basis: str | None = None
    try:
        head = inspect_receipt(Path(receipt_chain_head))
    except (OSError, ReceiptValidationError) as exc:
        refusals.append(f"the predecessor receipt cannot be read as a valid receipt: {exc}")
        head = None
    if head is not None:
        predecessor_receipt_id = str(head["receipt_id"])
        # Decision 064 §4. A successfully completed window is never a predecessor to continue from,
        # and this refusal is stated on its own rather than left to emerge from an empty remainder.
        # The distinction matters: "nothing remains" is a fact about the reconciliation that a plan
        # change, a superseded identity, or a future counting correction could move, whereas "this
        # window already completed" is a fact the head receipt recorded and nothing downstream can
        # rearrange. Read from the receipt itself, so it holds even where the inspection is not
        # consulted, and it is checked here — before the ceiling arithmetic, before the store sweep,
        # and long before any caller could reach a transport.
        if head.get("completion_status") == SUCCESSFUL_TERMINAL_COMPLETION_STATUS:
            refusals.append(
                "the predecessor receipt records a completed acquisition; a successful window has "
                "nothing left to continue and is never resumable, whatever the remainder, the "
                "headroom, or the recovery determination says"
            )
        if head.get("invocation_mode") != "live":
            refusals.append(
                "the predecessor receipt is not a live acquisition receipt; a continuation "
                "binds only to a live predecessor"
            )
        if head.get("acquisition_window") not in {None, window}:
            refusals.append(
                f"the predecessor receipt names window {head.get('acquisition_window')!r}, "
                f"not {window!r}"
            )
        head_ceiling = head.get("approved_request_ceiling")
        if head_ceiling is not None and head_ceiling != approved_ceiling:
            refusals.append(
                f"the predecessor receipt records approved ceiling {head_ceiling}, not "
                f"{approved_ceiling}; the ceiling is never raised, reset, or replaced"
            )
        completed_at = _parse_receipt_instant(head.get("completed_at_utc"))
        if completed_at is None:
            undetermined_basis = (
                "the predecessor receipt carries no attributable completion instant, so the "
                "post-receipt attempt segment cannot be attributed uniquely"
            )

    chain_resolved = all(
        condition.status == "MET"
        for condition in inspection.conditions
        if condition.number == "8.1"
    )
    if not chain_resolved and undetermined_basis is None:
        undetermined_basis = (
            "the predecessor receipt chain does not resolve, so cumulative consumption "
            "cannot be established"
        )

    pre_attempts = 0
    post_attempts = 0
    post_identities: frozenset[tuple[str, str]] = frozenset()
    if undetermined_basis is None and completed_at is not None:
        pre_attempts, post_attempts, post_identities, undetermined_basis = _segment_after_receipt(
            reconstruction.observations, completed_at
        )
    if undetermined_basis is None and pre_attempts > inspection.consumed_physical_attempts:
        undetermined_basis = (
            f"committed rows before the terminating receipt carry {pre_attempts} attempt(s) "
            f"but the receipt chain records {inspection.consumed_physical_attempts}; the "
            "evidence disagrees materially"
        )

    # In-flight identity is established from durable evidence only, never from plan position
    # alone. A streamed spool dies in staging under the accepted `{source_id}-{uuid}.part`
    # structure and identifies a route; raw-side partials, orphans, and stray lineage intents
    # are unaccounted activity with no lawful route identity of their own. Committed
    # post-receipt rows are already accounted exactly by `post_attempts` and are not in-flight
    # evidence — with no spool and no contradicting artifact there is nothing in flight to
    # charge, while any ambiguity is UNDETERMINED rather than a zero charge.
    in_flight_identity: str | None = None
    in_flight_charge = 0
    if undetermined_basis is None:
        spools = _interpret_staging_spools(storage.tree)
        if spools.undetermined_basis is not None:
            undetermined_basis = spools.undetermined_basis
        else:
            contradicting = _contradicting_store_evidence(storage.tree, reconstruction.observations)
            if spools.routes:
                in_flight_identity, in_flight_basis = _identify_in_flight(
                    requests, reconstruction, post_identities, spools.routes
                )
                if in_flight_identity is None:
                    undetermined_basis = in_flight_basis
                elif contradicting:
                    undetermined_basis = (
                        f"{len(contradicting)} unaccounted raw-store artifact(s) exist beside "
                        "the staging spool, so no single in-flight identity is uncontradicted "
                        "and more than one in-flight request appears possible"
                    )
                    in_flight_identity = None
                else:
                    in_flight_charge = derive_a_reachable(SOURCES[spools.routes[0]])
            elif contradicting:
                undetermined_basis = (
                    f"{len(contradicting)} unaccounted raw-store artifact(s) (a partial, an "
                    "orphan, or a stray lineage intent) exist with no lawful route identity, "
                    "so in-flight attribution cannot be established; uncertainty never becomes "
                    "a zero charge"
                )

    accounting = CumulativeAttemptAccounting(
        chain_consumed=inspection.consumed_physical_attempts,
        post_receipt_attempts=post_attempts,
        in_flight_charge=in_flight_charge,
        in_flight_request_identity=in_flight_identity,
        undetermined=undetermined_basis is not None,
        basis=(
            undetermined_basis
            if undetermined_basis is not None
            else "every attempt segment is attributed exactly once"
        ),
    )

    reconciliation = reconcile_requests(
        plan=plan,
        reconstruction=reconstruction,
        storage=storage,
        in_flight_request_identity=in_flight_identity,
        plan_transition=plan_transition,
    )

    # The exhaustive continuation-state partition is the single mechanism deciding every
    # item's treatment: satisfying items are excluded from replay; retryable items are the
    # remainder, each included exactly once; blocking items refuse the whole proposal and are
    # omitted from the transport remainder only because of that refusal; uncertain items make
    # the proposal UNDETERMINED.
    treatments = tuple((item, _classify_item(item)) for item in reconciliation.items)
    already_satisfied = tuple(
        item.identity_label for item, treatment in treatments if treatment == "satisfying"
    )
    blocking_items = tuple(item for item, treatment in treatments if treatment == "blocking")
    uncertain_items = tuple(item for item, treatment in treatments if treatment == "uncertain")
    remaining: list[ContinuationRequest] = []
    for item, treatment in treatments:
        if treatment != "retryable":
            continue
        validators = conditional_validators(reconstruction, item.source_id, item.request_identity)
        etag, last_modified = validators if validators is not None else (None, None)
        remaining.append(
            ContinuationRequest(
                position=item.position,
                source_id=item.source_id,
                identity_label=item.identity_label,
                request_identity=item.request_identity,
                etag=etag,
                last_modified=last_modified,
            )
        )

    cumulative = accounting.cumulative_consumed
    remaining_headroom = max(0, approved_ceiling - cumulative)
    worst_case = sum(derive_a_reachable(SOURCES[request.source_id]) for request in remaining)
    fits = not accounting.undetermined and worst_case <= remaining_headroom

    if accounting.undetermined:
        refusals.append(f"cumulative attempt accounting is UNDETERMINED: {accounting.basis}")
    if cumulative > approved_ceiling and not accounting.undetermined:
        refusals.append(
            f"cumulative consumption {cumulative} already exceeds the approved ceiling "
            f"{approved_ceiling}; no further physical request may occur"
        )
    if not fits and not accounting.undetermined and remaining:
        refusals.append(
            f"the worst-case remainder ({worst_case} attempt(s)) does not fit the remaining "
            f"headroom ({remaining_headroom}); stop for re-planning and a fresh exact owner "
            "approval — the ceiling is never raised"
        )
    if inspection.determination != "SAFE":
        refusals.append(
            f"the read-only inspection is {inspection.determination}: {inspection.basis}"
        )
    if reconstruction.blocked_t2_4_recovery_states:
        refusals.append(
            f"{reconstruction.blocked_t2_4_recovery_states} unresolved t2_4_recovery_action "
            "write-ahead state(s) remain blocked; a recovery mutation may have begun without "
            "its completed event and exact resolution, so continuation is prohibited until "
            "each is exactly resolved and a fresh inspection passes"
        )
    blocking_defects: list[str] = []
    if blocking_items:
        states = sorted({item.state for item in blocking_items})
        blocking_defects.append(f"{len(blocking_items)} item(s) in blocking state(s) {states}")
    if reconciliation.out_of_plan:
        blocking_defects.append(f"{len(reconciliation.out_of_plan)} out-of-plan observation(s)")
    if reconciliation.blocking_drift:
        blocking_defects.append(f"{len(reconciliation.blocking_drift)} blocking drift event(s)")
    if blocking_defects:
        refusals.append(
            "a blocking reconciliation defect refuses continuation: "
            + "; ".join(blocking_defects)
            + " — a blocking defect never counts as satisfied and never silently leaves the "
            "remainder; it is omitted from the transport remainder only because this whole "
            "proposal is refused"
        )
    if uncertain_items:
        labels = sorted(item.identity_label for item in uncertain_items)
        refusals.append(
            f"durable persistence cannot be established for {len(uncertain_items)} item(s) "
            f"{labels}; the state is persistence-uncertain and continuation is prohibited"
        )

    persistence_uncertain = bool(
        accounting.undetermined or uncertain_items or reconstruction.blocked_t2_4_recovery_states
    )
    determination = "UNDETERMINED" if persistence_uncertain else inspection.determination
    # ``permitted`` and the refusal explanations are one fact stated twice: a proposal is
    # permitted exactly when nothing appended a refusal reason, so a suppressed reason cannot
    # leave a silently refused (or silently permitted) proposal behind.
    permitted = not refusals
    return ContinuationProposal(
        permitted=permitted,
        determination=determination,
        refusal_reasons=tuple(refusals),
        window=window,
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=approved_ceiling,
        predecessor_receipt_id=predecessor_receipt_id,
        receipt_chain=inspection.receipt_chain,
        accounting=accounting,
        remaining_headroom=remaining_headroom,
        worst_case_remaining_attempts=worst_case,
        fits=fits,
        already_satisfied_excluded=already_satisfied,
        remaining=tuple(remaining),
        reconciliation=reconciliation,
        inspection=inspection,
    )


# --------------------------------------------------------------------------- #
# T2.4-D — the explicit, inert recovery-action library boundary
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RecoveryActionResult:
    """What one explicitly requested recovery action did, and what must happen next.

    No field here is the only continuation prohibition: the write-ahead
    ``census_recovery_states`` row this result names is the durable authority, and a restarted
    process recomputes from it. ``post_state_undetermined`` reports what *this invocation*
    could prove; the blocked-or-resolved row is what outlives it.
    """

    action: str
    target: str
    census_run_id: str
    recovery_state_id: str
    action_taken: str
    event_recorded: bool
    state_resolved: bool
    post_state_undetermined: bool
    detail: str

    @property
    def requires_fresh_inspection(self) -> bool:
        """A fresh read-only inspection is always required after a mutation."""
        return True

    @property
    def continuation_prohibited(self) -> bool:
        """Continuation stays prohibited until a fresh inspection returns ``SAFE``.

        When event recording, exact resolution, or the resolution readback failed, the state
        is ``UNDETERMINED`` and continuation is prohibited unconditionally — durably, through
        the still-blocked write-ahead row, not through this in-memory field alone (Decision
        040 §2, T2.4-D; Decision 041 §9).
        """
        return True


@dataclass(frozen=True, slots=True)
class _RepairSweep:
    """A read-only sweep of everything the four repair actions could lawfully target."""

    raw_partials: tuple[str, ...]
    staging_partials: tuple[str, ...]
    reconcile_orphans: tuple[str, ...]
    stray_lineage_intents: tuple[str, ...]
    projection: ProjectionValidation

    @property
    def projection_valid(self) -> bool:
        """Whether the derived audit projection agrees with SQLite in full."""
        return self.projection.is_valid


def _repair_sweep(catalog_path: Path, storage: StorageBinding) -> _RepairSweep:
    """Observe, without acting, exactly what ``observation_catalog.reconcile`` would touch.

    Symlink-averse in exact alignment with the accepted read-only observer: a symbolic link is
    skipped, never classified, so a symlinked staging ``.part`` can never become an authorized
    ``remove-stale-part`` candidate and a symlinked object can never become an orphan to adopt.
    The mutating boundary therefore refuses (target-not-a-candidate) exactly where the
    read-only sweep ignores, the link target stays untouched, and no containment protection is
    weakened.
    """
    tree = storage.tree
    with read_only_catalog(Path(catalog_path)) as connection:
        observations = load_observations(connection)
        projection = validate_audit_projection(connection, tree.audit / _PROJECTION_NAME)
    recorded = {
        observation.relative_storage_path
        for observation in observations
        if observation.relative_storage_path
    }

    raw_partials: list[str] = []
    staging_partials: list[str] = []
    orphans: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings, tree.staging):
        if not root.is_dir() or root.is_symlink():
            continue
        in_staging = root == tree.staging
        for path in sorted(root.rglob("*")):
            if path.is_symlink() or not path.is_file():
                continue
            if path.name.endswith(".reason") or path.name.endswith(LINEAGE_SUFFIX):
                continue
            relative = relative_to_root(path, tree.data_root)
            if path.name.endswith(".part"):
                (staging_partials if in_staging else raw_partials).append(relative)
            elif relative not in recorded:
                orphans.append(relative)

    stray_intents: list[str] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings):
        if not root.is_dir():
            continue
        for lineage in sorted(root.rglob(f"*{LINEAGE_SUFFIX}")):
            if lineage.is_symlink():
                continue
            object_path = lineage.with_name(lineage.name.removesuffix(LINEAGE_SUFFIX))
            object_relative = relative_to_root(object_path, tree.data_root)
            if object_relative in recorded or object_path.exists():
                continue
            stray_intents.append(relative_to_root(lineage, tree.data_root))

    return _RepairSweep(
        raw_partials=tuple(raw_partials),
        staging_partials=tuple(staging_partials),
        reconcile_orphans=tuple(orphans),
        stray_lineage_intents=tuple(stray_intents),
        projection=projection,
    )


def _refuse_repair(reason: str) -> RepairRefusedError:
    return RepairRefusedError(f"the recovery action is refused: {reason}")


# --------------------------------------------------------------------------- #
# Decision 064 §5 — the action-specific `rebuild-projection` eligibility gate
# --------------------------------------------------------------------------- #
#: The projection conditions a deterministic rebuild is the accepted repair for. The dividing
#: question is one thing only: **does the file on disk assert anything the authoritative catalog
#: contradicts?**
#:
#: The conditions below all answer *no*. The file is absent, or empty, or a byte-exact prefix of the
#: authoritative serialization that stops early; or what disagrees is not the file's bytes at all
#: but the derived `projected_to_audit` bookkeeping beside them; or what is present is the durable
#: marker the catalog writes when it detects that a reconstruction is owed. Rebuilding from SQLite
#: in any of those states loses nothing, because SQLite is the authority and nothing on disk claims
#: otherwise. `unresolved_recovery_event` in particular has to be here: it is the record that a
#: rebuild is *needed*, and treating it as a defect would make the repair unreachable from exactly
#: the state that asks for it -- §8's circularity, reintroduced one level down.
#:
#: Every other condition is a **divergence**: a payload whose bytes disagree with the catalog's, a
#: reordering, a duplicate or unknown identity, a malformed or truncated line, appended garbage, or
#: a file outside its accepted location. Each means bytes exist that the catalog cannot account for
#: -- evidence about what wrote to the audit trail -- and reconstructing over them would destroy
#: precisely what an owner would need to rule on. Those states are referred, not repaired.
#:
#: The condition names explain; the proof is the byte-level prefix equality the eligibility gate
#: checks beside them, so a state is never admitted on the strength of its label alone.
#:
#: This is a **narrowing** of what `rebuild-projection` previously accepted, and a deliberate one
#: (Decision 064 §5.1). The action used to reconstruct over any invalid projection, on the
#: argument that a derived file holds nothing authoritative. That argument is right about the file's
#: *content* and wrong about its *existence*: bytes the catalog cannot explain are themselves a
#: finding. The repair is not lost, only gated -- a separate owner ruling can still authorize it
#: once the divergence is understood.
#:
#: The list is an allow-list rather than a deny-list, so a projection condition introduced later is
#: refused by default rather than silently admitted.
_RECONSTRUCTIBLE_PROJECTION_CONDITIONS: Final[frozenset[str]] = frozenset(
    {
        "empty_file_with_projected_rows",
        "missing_observation_identity",
        "missing_projection_file",
        "projected_flags_claim_damaged_file",
        "sqlite_projection_flag_stale",
        "unresolved_recovery_event",
        "valid_prefix_only",
        "wrong_row_count",
    }
)


@dataclass(frozen=True, slots=True)
class RebuildProjectionEligibility:
    """Whether the `rebuild-projection` action may proceed, condition by condition.

    Read-only and reportable on its own, so the eligibility of the one deterministic repair can be
    *proved before* it is invoked rather than discovered by invoking it.
    """

    action: str
    permitted: bool
    conditions: tuple[tuple[str, bool, str], ...]

    @property
    def unmet(self) -> tuple[str, ...]:
        """The names of every condition that does not hold, in evaluation order."""
        return tuple(name for name, held, _ in self.conditions if not held)

    @property
    def refusal(self) -> str | None:
        """The first unmet condition's detail, or ``None`` when every condition holds."""
        for _, held, detail in self.conditions:
            if not held:
                return detail
        return None

    def as_record(self) -> Mapping[str, object]:
        """Deterministic mapping for the evidence record."""
        return {
            "action": self.action,
            "permitted": self.permitted,
            "conditions": [
                {"condition": name, "held": held, "detail": detail}
                for name, held, detail in self.conditions
            ],
        }


def _projection_lag_is_reconstructible(projection: ProjectionValidation) -> bool:
    """Whether an invalid projection merely *lags* the catalog rather than diverging from it.

    Two independent things must hold, and the second is the proof rather than the description:
    every reported condition is on the reconstructible list, **and** the bytes actually present are
    a byte-exact prefix of the authoritative serialization. A condition name alone could be
    satisfied by a file whose early lines already disagree; the prefix equality cannot.
    """
    if set(projection.conditions) - _RECONSTRUCTIBLE_PROJECTION_CONDITIONS:
        return False
    return projection.observed_count is None or (
        projection.valid_prefix_count == projection.observed_count
    )


def _condition_status(inspection: RecoveryState, number: str) -> str:
    """One §8 condition's status from a completed inspection, or ``"ABSENT"`` if not evaluated."""
    for condition in inspection.conditions:
        if condition.number == number:
            return condition.status
    return "ABSENT"


def _condition_settled(inspection: RecoveryState, number: str) -> bool:
    """Whether one §8 condition is met, or lawfully not applicable."""
    return _condition_status(inspection, number) in {"MET", "N/A"}


def _rebuild_projection_eligibility(
    *,
    action: str,
    inspection: RecoveryState,
    sweep: _RepairSweep,
    network_disabled: bool,
) -> RebuildProjectionEligibility:
    """Evaluate Decision 064 §5's eleven conditions for the projection rebuild.

    **Why this action has its own gate.** The generic applier refuses every action from an
    ``UNDETERMINED`` inspection, which is correct for the three actions that touch acquired
    evidence. It was structurally wrong for exactly one: the derived audit projection is part of
    what the inspection reads, so a projection that has fallen behind SQLite can itself push the
    determination away from ``SAFE`` — and the only accepted repair for that state was then
    unreachable from it. The condition the action exists to repair was gating the action.

    The fix is **not** "run any action from any determination". It is a narrower gate for this one
    action, and it is stricter than the blanket rule in every direction that matters: it demands a
    resolved chain, an established terminal state, passing integrity, an unambiguous authoritative
    observation set, no orphan or partial or missing-object uncertainty, no blocked recovery state,
    resolved carry-in accounting, a disabled network, and — the load-bearing one — a projection
    mismatch that is a *deterministic reconstruction*, never a divergence. An ``UNDETERMINED``
    caused by anything other than the projection still refuses, because every one of those causes
    has its own condition here.

    Condition 8 of the ruling, writer ownership, is discharged by mechanism rather than by a second
    opinion: the applier opens the exclusive writer lease for its write-ahead block *before* the
    mutation, and a lease held elsewhere raises there and refuses with nothing written. A read-only
    probe here would be a second implementation of the lease rule that could disagree with the real
    one, and the weaker of two disagreeing checks is the one that matters.
    """
    projection = sweep.projection
    divergent = sorted(set(projection.conditions) - _RECONSTRUCTIBLE_PROJECTION_CONDITIONS)
    conditions: tuple[tuple[str, bool, str], ...] = (
        (
            "requested_action_is_rebuild_projection",
            action == "rebuild-projection",
            f"this eligibility applies to 'rebuild-projection' alone; {action!r} was requested and "
            f"no other action inherits it",
        ),
        (
            "receipt_chain_resolves",
            _condition_settled(inspection, "8.1"),
            f"condition 8.1 is {_condition_status(inspection, '8.1')}: the receipt chain must "
            f"resolve to a first attempt before any deterministic repair is applied",
        ),
        (
            "terminal_state_established",
            _condition_settled(inspection, "8.2"),
            f"condition 8.2 is {_condition_status(inspection, '8.2')}: the terminal or "
            f"interruption state must be established, not guessed",
        ),
        (
            "catalog_integrity_passes",
            _condition_settled(inspection, "8.3"),
            f"condition 8.3 is {_condition_status(inspection, '8.3')}: the authoritative catalog "
            f"must pass its quick, integrity, and foreign-key checks before anything is "
            f"reconstructed from it",
        ),
        (
            "authoritative_observations_unambiguous",
            _condition_settled(inspection, "8.4") and inspection.rows_without_object_count == 0,
            f"condition 8.4 is {_condition_status(inspection, '8.4')} with "
            f"{inspection.rows_without_object_count} committed row(s) lacking their object; a "
            f"projection is only reconstructible from an observation set that is itself complete",
        ),
        (
            "no_orphan_or_partial_uncertainty",
            _condition_settled(inspection, "8.5")
            and _condition_settled(inspection, "8.6")
            and inspection.orphan_object_count == 0
            and inspection.partial_file_count == 0,
            f"conditions 8.5/8.6 are {_condition_status(inspection, '8.5')}/"
            f"{_condition_status(inspection, '8.6')} with {inspection.orphan_object_count} "
            f"orphan(s) and {inspection.partial_file_count} partial file(s); unadjudicated store "
            f"state is not a projection problem and is not repaired by rebuilding one",
        ),
        (
            "no_blocked_recovery_state",
            _condition_settled(inspection, "8.9"),
            f"condition 8.9 is {_condition_status(inspection, '8.9')}: a blocked recovery state is "
            f"an unadjudicated mutation, and no action proceeds over one",
        ),
        (
            "carry_in_accounting_resolves",
            _condition_settled(inspection, "8.12"),
            f"condition 8.12 is {_condition_status(inspection, '8.12')}: the chain's carry-in root "
            f"and the catalog's consumption checkpoint must agree",
        ),
        (
            "projection_mismatch_is_deterministically_reconstructible",
            not projection.is_valid and _projection_lag_is_reconstructible(projection),
            (
                "the audit projection already agrees with SQLite, so there is nothing to rebuild"
                if projection.is_valid
                else (
                    f"the projection diverges from SQLite rather than lagging it "
                    f"({', '.join(divergent) or 'its bytes are not a valid prefix'}); a divergent "
                    f"projection is referred for an owner ruling and is never overwritten by this "
                    f"action"
                )
            ),
        ),
        (
            "network_disabled",
            network_disabled,
            "the caller did not establish that the network is disabled; deterministic recovery "
            "runs offline, and an unproved network state is treated exactly like an enabled one",
        ),
        (
            "writer_lease_obtainable",
            True,
            "discharged by the exclusive writer lease the write-ahead block acquires before the "
            "mutation; a lease held elsewhere refuses there, with nothing written",
        ),
    )
    return RebuildProjectionEligibility(
        action=action,
        permitted=all(held for _, held, _ in conditions),
        conditions=conditions,
    )


def rebuild_projection_eligibility(
    *,
    action: str,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    network_disabled: bool,
    evidence_root: Path | None = None,
) -> RebuildProjectionEligibility:
    """Report whether `rebuild-projection` may proceed. Writes nothing, mutates nothing.

    The same evaluation :func:`apply_recovery_action` performs, exposed so it can be *proved* before
    a one-use repair authority is spent. It opens the catalog read-only, walks the receipt chain,
    sweeps the store, and returns the eleven conditions with their statuses.

    Raises:
        RecoveryInspectionError: the catalog or the head receipt is absent, so nothing can be
            established at all.
    """
    inspection = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        data_root=storage.data_root,
        evidence_root=evidence_root,
    )
    return _rebuild_projection_eligibility(
        action=action,
        inspection=inspection,
        sweep=_repair_sweep(catalog_path, storage),
        network_disabled=network_disabled,
    )


def apply_recovery_action(
    *,
    action: str,
    target: str,
    plan: RequestPlan,
    receipt_chain_head: Path,
    catalog_path: Path,
    storage: StorageBinding,
    census_run_id: str,
    lock_directory: Path | None = None,
    evidence_root: Path | None = None,
    # Defaults to "not established", which the projection rebuild's eligibility treats exactly as
    # it treats an enabled network: it refuses. A caller that has proved the switches are off says
    # so; one that has not gets a refusal rather than a silent pass. The other three actions do not
    # read it.
    network_disabled: bool = False,
) -> RecoveryActionResult:
    """Apply exactly one explicitly requested, deterministically required recovery action.

    The applier never runs automatically — no reconstruction, reconciliation, inspection,
    drift, or proposal code calls it — and it refuses rather than adapts: an unknown or
    multi-action request, an ``UNDETERMINED`` state, a stale or already-resolved target, an
    action that differs from the deterministic recommendation, and a request its one authorized
    primitive cannot be scoped to are all refused before anything mutates.

    ``rebuild-projection`` is the one exception to the ``UNDETERMINED`` rule, and it is a *narrower*
    gate rather than a wider one: it is held to :func:`_rebuild_projection_eligibility`'s eleven
    explicit conditions, which include everything the blanket test protected plus a requirement the
    blanket test never made — that the projection mismatch be a deterministic reconstruction of a
    lagging file rather than a divergence. See that function for why the blanket test was
    structurally unable to authorize the repair of a condition it was itself computed from
    (Decision 064 §5). No other action inherits it.

    Every mutation is durably write-ahead protected (Decision 041 §8). The corrected sequence:
    the exact required action and target are recomputed and validated; the caller-supplied,
    already registered ``ops_ingestion_jobs.job_id`` is validated (no run identity is ever
    created, fabricated, or substituted here); a second action is refused while any
    ``t2_4_recovery_action`` state for that run remains unresolved; one opaque unique
    ``recovery_state_id`` is created and persisted ``blocked`` through the accepted
    :func:`open_recovery_state` primitive, committed **before** the mutation and verified
    through a genuinely fresh read-only connection; exactly one authorized mutation runs
    through the accepted primitive for its action class; the actual completed recovery event is
    recorded through the accepted :func:`record_recovery_events` surface with
    ``census_run_id=None`` (opening the block is not itself a recovery event, and no second
    state row is created); only after event recording succeeds is the exact state resolved
    through :func:`resolve_recovery_state`; and the resolution is verified through a fresh
    connection. A failure at any post-mutation step leaves the exact state ``blocked``, so a
    restarted process sees the unresolved block durably — no in-memory field is ever the only
    continuation prohibition. A committed resolution whose readback cannot complete leaves this
    invocation ``UNDETERMINED``; a later process recomputes from durable catalog state.

    Nothing acquired is ever deleted or overwritten; the one deletion this boundary performs is
    a staging spool proven never promoted, never catalogued, never referenced, and never a
    symbolic link. A fresh read-only inspection is required afterwards in every case, and this
    function deliberately does not run it — re-inspection after repair is the operator
    workflow's explicit next step, never an automatic continuation.

    Raises:
        RepairRefusedError: the request is refused; nothing was mutated. A refusal after the
            write-ahead block committed (a verification or scoping anomaly) leaves that block
            durably ``blocked`` for owner adjudication — fail closed, still with no mutation.
        RecoveryInspectionError: the catalog or head receipt is absent, so the pre-mutation
            inspection cannot even begin.
    """
    if action not in RECOVERY_ACTIONS:
        reason = (
            f"{action!r} is not one of the four authorized deterministic action classes "
            f"{RECOVERY_ACTIONS}; combined or unknown actions are never coerced"
        )
        raise _refuse_repair(reason)
    if not target or not target.strip():
        reason = "an explicit target is required; an empty target names nothing"
        raise _refuse_repair(reason)

    inspection = inspect_recovery_state(
        plan=plan,
        receipt_chain_head=receipt_chain_head,
        catalog_path=catalog_path,
        data_root=storage.data_root,
        evidence_root=evidence_root,
    )
    sweep = _repair_sweep(catalog_path, storage)

    # Decision 064 §5. Exactly one action has an action-specific eligibility gate, because exactly
    # one action repairs a condition the determination itself is computed from. `rebuild-projection`
    # is held to the eleven explicit conditions below instead of the blanket determination test;
    # every other action keeps the blanket test unchanged, so no action inherits this and
    # UNDETERMINED for evidence unrelated to the projection still refuses everything.
    if action == "rebuild-projection":
        eligibility = _rebuild_projection_eligibility(
            action=action,
            inspection=inspection,
            sweep=sweep,
            network_disabled=network_disabled,
        )
        if not eligibility.permitted:
            reason = (
                f"the action-specific rebuild-projection eligibility does not hold "
                f"({', '.join(eligibility.unmet)}): {eligibility.refusal}"
            )
            raise _refuse_repair(reason)
    elif inspection.determination == "UNDETERMINED":
        reason = (
            f"the read-only inspection is UNDETERMINED ({inspection.basis}); every action other "
            "than the projection rebuild is refused from UNDETERMINED and the state is referred "
            "to the owner"
        )
        raise _refuse_repair(reason)

    required: dict[str, tuple[str, ...]] = {
        "adopt-orphan": sweep.reconcile_orphans,
        "quarantine-partial": sweep.raw_partials,
        "remove-stale-part": sweep.staging_partials,
        "rebuild-projection": () if sweep.projection_valid else (_PROJECTION_NAME,),
    }
    if all(not targets for targets in required.values()):
        reason = "nothing requires repair; the request is stale or already resolved"
        raise _refuse_repair(reason)
    candidates = required[action]
    if not candidates:
        recommended = ", ".join(sorted(name for name, targets in required.items() if targets))
        reason = (
            f"{action!r} differs from the deterministic recommendation; the current state "
            f"requires only: {recommended}"
        )
        raise _refuse_repair(reason)
    if target not in candidates:
        reason = (
            f"target {target!r} is not a current {action!r} candidate; the request is stale, "
            "already resolved, or misidentified"
        )
        raise _refuse_repair(reason)

    tree = storage.tree
    lock_dir = Path(lock_directory) if lock_directory is not None else Path(catalog_path).parent

    # Per-action scoping preconditions, still before any write of any kind.
    if action == "adopt-orphan":
        if len(sweep.reconcile_orphans) != 1:
            reason = (
                f"{len(sweep.reconcile_orphans)} orphan(s) exist; the accepted reconciliation "
                "primitive cannot be scoped to exactly one authorized event while another "
                "orphan would also be processed — repair one state at a time or refer to the "
                "owner"
            )
            raise _refuse_repair(reason)
        if sweep.stray_lineage_intents:
            reason = (
                "a lineage intent without its raw object exists; the accepted reconciliation "
                "primitive would quarantine it alongside the requested adoption, which is an "
                "unrelated mutation — resolve it first or refer to the owner"
            )
            raise _refuse_repair(reason)
        if not sweep.projection_valid and not _projection_lag_is_reconstructible(sweep.projection):
            # Narrowed from "the projection is valid" to "the projection is not *divergent*", and
            # the narrowing is what keeps the two guards composable (Decision 064 §5.2).
            #
            # The guard exists because the accepted reconciliation primitive persists a projection
            # incident when it finds one, which would be a mutation the operator did not request.
            # That reasoning is exact for a diverging projection: the incident would be recording an
            # unadjudicated corruption, and the adoption would be riding alongside an owner
            # question. It does not hold for a *lagging* one, where the incident records the
            # already-known, already-true, idempotent fact that a rebuild is owed — and where the
            # rebuild is the very next authorized action.
            #
            # Left unnarrowed, the two guards deadlock: adoption would require a projection the
            # rebuild cannot produce while an orphan exists, and the rebuild would require an
            # absence of orphans that adoption cannot deliver. That state is reachable from an
            # ordinary interruption between a raw write and its catalog commit, so the deadlock
            # would not be theoretical. The order that now works is adopt, then rebuild.
            reason = (
                "the audit projection diverges from the catalog rather than lagging it; the "
                "accepted reconciliation primitive would persist an incident for an unadjudicated "
                "divergence alongside the requested adoption — refer the projection first"
            )
            raise _refuse_repair(reason)
    if action == "remove-stale-part":
        spool_path = tree.data_root / target
        if spool_path.is_symlink():
            reason = (
                "the staging spool is a symbolic link and is never a removal candidate; the "
                "link target stays untouched"
            )
            raise _refuse_repair(reason)
        if RawStore.lineage_path(spool_path).exists():
            reason = (
                "the staging spool carries a lineage intent, so it cannot be proven a "
                "never-promoted temporary; quarantine is the lawful disposition"
            )
            raise _refuse_repair(reason)

    # The caller-supplied run identity: required, existing, and free of unresolved T2.4
    # write-ahead states. This applier never creates an ingestion-job row, never invokes the
    # private census-orchestrator job creator, and never substitutes a receipt identity.
    if not census_run_id or not census_run_id.strip():
        reason = (
            "no census run identity was supplied; every mutating T2.4 recovery action "
            "requires a caller-supplied, already registered ops_ingestion_jobs.job_id"
        )
        raise _refuse_repair(reason)
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            job = connection.execute(
                "SELECT 1 FROM ops_ingestion_jobs WHERE job_id = ?",
                (census_run_id,),
            ).fetchone()
            unresolved = int(
                connection.execute(
                    "SELECT COUNT(*) FROM census_recovery_states "
                    "WHERE census_run_id = ? AND scenario = ? AND resolution_state = 'blocked'",
                    (census_run_id, _T2_4_STATE_SCENARIO),
                ).fetchone()[0]
            )
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        reason = (
            f"the run identity could not be validated against the catalog "
            f"({type(exc).__name__}); the action refuses before mutation"
        )
        raise _refuse_repair(reason) from exc
    if job is None:
        reason = (
            f"census run {census_run_id!r} does not resolve to a lawful existing governed "
            "ops_ingestion_jobs row; a run identity is required and is never created, "
            "fabricated, or substituted by this applier"
        )
        raise _refuse_repair(reason)
    if unresolved:
        reason = (
            f"{unresolved} unresolved t2_4_recovery_action write-ahead state(s) already exist "
            f"for run {census_run_id!r}; a second action is refused before mutation until "
            "each is exactly resolved"
        )
        raise _refuse_repair(reason)

    # Open and commit the write-ahead block before the mutation, then verify the exact row
    # through a genuinely fresh read-only connection.
    recovery_state_id = uuid.uuid4().hex
    try:
        with CatalogWriter(Path(catalog_path), lock_dir) as writer:
            open_recovery_state(
                writer,
                census_run_id=census_run_id,
                recovery_state_id=recovery_state_id,
                scenario=_T2_4_STATE_SCENARIO,
                action_taken=action,
                detail=(
                    f"write-ahead block for the explicitly requested recovery action "
                    f"{action!r} on target {target!r}"
                ),
                relative_path=target,
            )
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        reason = (
            f"the write-ahead recovery state could not be opened and committed "
            f"({type(exc).__name__}); the action refuses before mutation"
        )
        raise _refuse_repair(reason) from exc
    if not _verify_write_ahead_state(catalog_path, census_run_id, recovery_state_id, "blocked"):
        reason = (
            "the committed write-ahead block could not be verified through a fresh read-only "
            "connection; the action refuses before mutation"
        )
        raise _refuse_repair(reason)

    event: RecoveryEvent
    action_taken: str
    detail: str

    event_recorded = False
    state_resolved = False
    with CatalogWriter(Path(catalog_path), lock_dir) as writer:
        # Exactly one authorized mutation. A mutation failure raises out of this block with
        # nothing recorded and nothing resolved — the exact write-ahead state stays blocked,
        # which is precisely the durable fail-closed evidence a restarted process needs.
        if action == "adopt-orphan":
            report = reconcile(writer.connection, tree, quarantine_partial=False)
            # Exactly one orphan exists (proven above), so the one adoption-path event this
            # reconcile pass produced is necessarily the requested target's — whether the
            # authoritative path adopted it verified or preserved it in quarantine unproven,
            # in which case the event names the quarantine destination rather than the origin.
            matching = [
                item for item in report.events if item.scenario == "object_without_catalog_row"
            ]
            if not matching:
                reason = (
                    "the accepted reconciliation primitive reported no adoption event for "
                    "the requested orphan; the write-ahead block stays blocked for owner "
                    "adjudication"
                )
                raise _refuse_repair(reason)
            event = matching[0]
            action_taken = event.action_taken
            detail = event.detail
        elif action == "quarantine-partial":
            quarantined = storage.raw_store.quarantine(
                tree.data_root / target,
                "RAW_PARTIAL_DOWNLOAD",
                "interrupted transfer quarantined by the explicit recovery applier",
            )
            action_taken = "quarantined"
            detail = (
                "the partial raw object was preserved in quarantine through the accepted "
                "move-and-preserve path; nothing was deleted"
            )
            event = RecoveryEvent(
                scenario="interrupted_part_download",
                action_taken=action_taken,
                detail=detail,
                relative_path=relative_to_root(quarantined, tree.data_root),
            )
        elif action == "remove-stale-part":
            (tree.data_root / target).unlink()
            action_taken = "removed_never_promoted_temporary"
            detail = (
                "the stale staging spool was removed as a never-promoted, never-catalogued, "
                "never-referenced temporary; no acquired object was touched"
            )
            event = RecoveryEvent(
                scenario="interrupted_part_download",
                action_taken=action_taken,
                detail=detail,
                relative_path=target,
            )
        else:  # rebuild-projection
            # The accepted rebuild primitive, deliberately without a run identity: the
            # projection-specific bulk resolver is never reused for the write-ahead state,
            # which is resolved exactly, by primary key, below (Decision 041 §14).
            rebuilt = rebuild_audit_projection(writer.connection, tree.audit / _PROJECTION_NAME)
            action_taken = "projection_rebuilt"
            detail = (
                f"the derived audit projection was atomically reconstructed from {rebuilt} "
                "authoritative catalog row(s) through the accepted rebuild primitive"
            )
            event = RecoveryEvent(
                scenario="audit_projection_interrupted",
                action_taken=action_taken,
                detail=detail,
                relative_path=_PROJECTION_NAME,
            )

        # The actual completed recovery event, then — only after it succeeds — the exact
        # resolution of the write-ahead state. Order is load-bearing: an event-recording
        # failure must leave the state blocked, never resolved.
        event_recorded = _record_repair_event(writer, event)
        if event_recorded:
            state_resolved = _resolve_write_ahead(
                writer, census_run_id, recovery_state_id, action_taken, detail
            )

    resolution_verified = False
    if state_resolved:
        resolution_verified = _verify_write_ahead_state(
            catalog_path, census_run_id, recovery_state_id, "resolved"
        )

    if not event_recorded:
        detail = (
            f"{detail}; the recovery event could not be recorded, so the exact write-ahead "
            "state remains blocked, the state is UNDETERMINED, and continuation is prohibited"
        )
    elif not state_resolved:
        detail = (
            f"{detail}; the write-ahead state could not be exactly resolved and remains "
            "blocked; the state is UNDETERMINED and continuation is prohibited"
        )
    elif not resolution_verified:
        detail = (
            f"{detail}; exact resolution committed but its fresh readback could not complete, "
            "so this invocation is UNDETERMINED and must not authorize continuation; a later "
            "process recomputes from durable catalog state"
        )

    return RecoveryActionResult(
        action=action,
        target=target,
        census_run_id=census_run_id,
        recovery_state_id=recovery_state_id,
        action_taken=action_taken,
        event_recorded=event_recorded,
        state_resolved=state_resolved,
        post_state_undetermined=not (event_recorded and state_resolved and resolution_verified),
        detail=detail,
    )


def _verify_write_ahead_state(
    catalog_path: Path,
    census_run_id: str,
    recovery_state_id: str,
    expected: str,
) -> bool:
    """Read the exact write-ahead row through a genuinely fresh read-only connection."""
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            row = connection.execute(
                "SELECT scenario, resolution_state FROM census_recovery_states "
                "WHERE census_run_id = ? AND recovery_state_id = ?",
                (census_run_id, recovery_state_id),
            ).fetchone()
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False
    return (
        row is not None
        and str(row["scenario"]) == _T2_4_STATE_SCENARIO
        and str(row["resolution_state"]) == expected
    )


def _record_repair_event(writer: CatalogWriter, event: RecoveryEvent) -> bool:
    """Record the one actual completed recovery event, reporting failure as ``False``.

    ``census_run_id=None`` deliberately: the accepted function then writes only the actual
    ``census_recovery_events`` row and creates no second recovery-state row. The write-ahead
    state opened before the mutation is the only state row, and it is resolved exactly, by
    primary key, afterwards (Decision 041 §8 steps 9–11).
    """
    try:
        return record_recovery_events(writer, (event,), census_run_id=None) == 1
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False


def _resolve_write_ahead(
    writer: CatalogWriter,
    census_run_id: str,
    recovery_state_id: str,
    action_taken: str,
    detail: str,
) -> bool:
    """Exactly resolve the write-ahead state, reporting failure as ``False``."""
    try:
        return resolve_recovery_state(
            writer,
            census_run_id=census_run_id,
            recovery_state_id=recovery_state_id,
            action_taken=action_taken,
            detail=detail,
        )
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False


# =========================================================================== #
# Stage T2.5-T2.6 - operator surfaces and integrated implementation
# (Decision 045. Everything below is offline: nothing here opens a socket
#  except the one auditable transport-construction site in
#  `default_live_transport_factory`, which no other surface may reach.)
# =========================================================================== #

# --------------------------------------------------------------------------- #
# Progress-sink sanitization and exclusion (Decision 045 §12)
# --------------------------------------------------------------------------- #
#: The one fixed internal reason a progress-sink failure is retained under. It is a constant, not
#: a rendering of the exception: an operator sink's message is operator-controlled text, and the
#: retained value must be safe to serialize into a receipt, a reconciliation report, or any other
#: written artifact without depending on a downstream scanner to notice that it was not.
PROGRESS_SINK_FAILURE_REASON: Final = "operator progress sink raised"

#: The longest sanitized exception-class name retained. A class name is already a Python
#: identifier, but bounding it makes the retained field's size a property of this module rather
#: than of the operator's code.
_SANITIZED_CLASS_NAME_MAX_CHARS: Final = 64

#: Characters permitted in a retained exception-class name. An allowlist, so a class named to
#: carry a path separator, an ``@``, or whitespace contributes nothing rather than being filtered
#: by a denylist that a new prohibited form could slip past.
_CLASS_NAME_ALLOWED: Final = re.compile(r"[^A-Za-z0-9_]")


def sanitized_progress_failure(identity_label: str, exc: BaseException) -> str:
    """Return the bounded, structural record of one progress-sink failure.

    Deliberately derived from the exception's *class* alone, exactly as
    :func:`_operational_detail` is, and then allowlist-filtered on top. ``str(exc)``, the
    exception's arguments, its ``filename``, and its ``__notes__`` are never read, so no absolute
    path, email address, credential, or response body can reach retained state through this seam
    regardless of what the operator's sink chose to raise.
    """
    name = _CLASS_NAME_ALLOWED.sub("", type(exc).__name__)[:_SANITIZED_CLASS_NAME_MAX_CHARS]
    return f"{identity_label}: {PROGRESS_SINK_FAILURE_REASON} ({name or 'UnnamedException'})"


def _emit_progress_diagnostic(identity_label: str, exc: BaseException) -> None:
    """Write the raw sink failure to the local stderr diagnostic channel, and nowhere else.

    Decision 045 §12 permits raw operator text on exactly this channel, because it is the only
    thing that makes an operator's own output failure diagnosable and it is never persisted by
    this project. It is deliberately not routed through the logger: file logging is configurable,
    and a configured log file is a written artifact.
    """
    print(  # noqa: T201 - the authorized local stderr diagnostic channel
        f"progress sink failed for {identity_label}: {type(exc).__name__}: {exc}",
        file=sys.stderr,
    )


# --------------------------------------------------------------------------- #
# Exhaustive response-event accounting (Decision 045 §§9-11)
# --------------------------------------------------------------------------- #
#: The receipt-local sentinel status key. Decision 045 §9.4 defines it as meaning exactly "no HTTP
#: status - transport-level failure", and reserves it exclusively for that: a real HTTP response is
#: never recorded under it. The frozen receipt schema is unchanged, because `status_code_totals`
#: is a `count_map` whose keys are already unconstrained strings.
NO_HTTP_STATUS_SENTINEL: Final = "0"

#: Client action markers that each denote exactly one classified physical response. They are the
#: frozen receipt buckets, read from the receipt module rather than restated, so the producer and
#: the validator cannot disagree about the vocabulary.
_CLASSIFIED_ACTIONS: Final[frozenset[str]] = frozenset(RESPONSE_CLASSIFICATION_BUCKETS)

#: The accepted client's marker for a lawful `304`, which returns early and never reaches
#: `classify_response`. Decision 045 §10 rules it one `proceed` bucket at status `304`, so that a
#: `304` cannot silently disappear from the response-policy totals.
_NOT_MODIFIED_ACTION: Final = "not_modified"

#: Markers for a physical response the policy path refused at a boundary instead of classifying.
#: Each is a terminal failure decision taken on a real physical response, so each contributes the
#: already-frozen `fail` bucket - no bucket is invented for it (Decision 045 §9.4).
_BOUNDARY_REFUSAL_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "boundary_refused",
        "redirect_refused",
        "transport_redirect_history_refused",
    }
)

#: Markers that accompany a response rather than denoting one. `request_ceiling_checked` precedes
#: a send; `pre_request_boundary_refused` happens before any send at all and is therefore a
#: pre-transport refusal, which §9.1 excludes from both totals; the three terminal markers annotate
#: a response whose bucket was already appended by the classification step.
_NON_RESPONSE_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "post_cooldown_retry_refused",
        "pre_request_boundary_refused",
        "request_ceiling_checked",
        "retry_budget_exhausted",
        "second_cooldown_terminal",
    }
)


@dataclass(slots=True)
class PhysicalResponseLog:
    """The ordered record of every physical transport send, appended by the recording transport.

    One entry per send: the observed HTTP status, or ``None`` when the send produced no HTTP
    response at all. Nothing else is retained - not a header, not a body, not a URL - because the
    only thing receipt accounting owes is *what status each physical response carried*.
    """

    _sends: list[int | None] = field(default_factory=list)

    def record(self, status: int | None) -> None:
        """Append one physical send's observed status, or ``None`` for a transport failure."""
        self._sends.append(status)

    def drain(self) -> tuple[int | None, ...]:
        """Return and clear the sends recorded since the last drain."""
        drained = tuple(self._sends)
        self._sends.clear()
        return drained

    @property
    def pending(self) -> int:
        """How many recorded sends have not yet been absorbed into accounting."""
        return len(self._sends)


#: The opaque-id prefix a pre-send physical-attempt reservation carries. It is deliberately
#: distinct from the snapshot store's own observation-scoped ``attempt-…`` identifier: the two are
#: separate surfaces (Decision 051 §5A; data dictionary §5A), and a reservation is never a receipt
#: or an observation substitute.
_ATTEMPT_ID_PREFIX: Final = "m3a-attempt-"


def _default_attempt_id() -> str:
    """Return a collision-safe opaque identifier for one physical-attempt reservation."""
    return f"{_ATTEMPT_ID_PREFIX}{uuid.uuid4().hex}"


def _attempt_logical_role(source_id: str) -> str:
    """The registered logical role a reservation records, matching the snapshot store's role.

    Read from the registered route specification — never fixed per call site — so the ledger's
    ``logical_role`` cannot drift from the role the observation records for the same route.
    """
    spec = require_registered(source_id)
    if spec.retrieval_method == "bulk_archive":
        return "bulk_archive"
    return f"census_{spec.category}"


@dataclass(slots=True)
class PreSendAttemptLedger:
    """Write-ahead durable ledger of physical SEC retrieval attempts (Decision 051 §6; §5A).

    Immediately before each physical transport send, :meth:`reserve` commits one
    ``ops_retrieval_attempts`` row in state ``started`` through the accepted single-writer catalog
    boundary. The operational connection is autocommit with ``synchronous = FULL``
    (``storage/sqlite.py``), so the row is durable the instant :meth:`reserve` returns: a process
    that dies between the reservation and the wire still leaves exactly one consumed attempt on
    record, which is the whole point of a write-ahead reservation. If the commit raises, the caller
    must not send — :class:`RecordingTransport` enforces that by reserving *before* it delegates.

    Every retry and redirect send receives its own row with the next positive ordinal. It writes
    only non-secret, schema-valid fields — the canonical request URL (a public SEC URL, never a
    contact identity, credential, header, cookie, body, or private path), the registered logical
    role, a positive per-run ordinal, and an opaque id — and binds each row to the exact
    acquisition job. It never backfills a historical row and never resets its ordinal.

    It uses the already-open writer the recorder holds; it neither opens a connection nor takes a
    second lease, and it constructs no transport, reads no configuration, and opens no socket.
    """

    writer: CatalogWriter
    job_id: str
    clock: Callable[[], str] = _utc_now
    id_factory: Callable[[], str] = _default_attempt_id
    _ordinal: int = field(default=0, init=False)

    def reserve(self, request: SecRequest) -> str:
        """Commit one ``started`` reservation before a physical send, and return its opaque id.

        Raises:
            CatalogWriteError | sqlite3.Error: the reservation could not be committed. Propagated
                unchanged so the caller aborts the physical send it has not yet made.
        """
        self._ordinal += 1
        attempt_id = self.id_factory()
        self.writer.insert(
            "ops_retrieval_attempts",
            {
                "retrieval_attempt_id": attempt_id,
                "job_id": self.job_id,
                "source_url_canonical": request.url,
                "logical_role": _attempt_logical_role(request.source_id),
                "attempt_number": self._ordinal,
                "attempt_state": "started",
                "started_at_utc": self.clock(),
            },
        )
        return attempt_id

    def settle(self, attempt_id: str, *, succeeded: bool) -> None:
        """Record a deterministic terminal state for a reservation, without erasing consumption.

        Called only after the physical send returns, when the transport-level outcome is known. A
        reservation whose send raised, or whose process died first, is deliberately left
        ``started``: a stranded reservation remains consumed (Decision 051 §6.5).
        """
        self.writer.connection.execute(
            "UPDATE ops_retrieval_attempts SET attempt_state = ?, finished_at_utc = ? "
            "WHERE retrieval_attempt_id = ?",
            ("succeeded" if succeeded else "failed", self.clock(), attempt_id),
        )

    def reserved_count(self) -> int:
        """The durable count of physical attempts this run has reserved, read from the ledger.

        Every committed ``started`` row is exactly one consumed physical attempt — including a row
        stranded before its transport call — and a terminal state never erases the consumption
        (Decision 051 §6.3; data dictionary §5A rules 2-3). Counting the committed rows is what
        makes the durable ledger, rather than the in-memory pre-attempt guard, the accepted source
        of the physical-attempt count: an interruption in the pre-send window — after
        :meth:`PhysicalAttemptCeiling.before_attempt` incremented but before this reservation
        committed — leaves no row, so it is charged **zero** rather than inventing an attempt from a
        lost in-memory claim (Decision 051 §7.2; contract §12).

        The count is read through the single-writer connection the reservations commit on, so it
        observes every reservation this run has made (the operational connection is autocommit, so a
        committed row is visible immediately), and it binds to this run's job alone — a different
        run's reservations never leak into it.
        """
        row = self.writer.connection.execute(
            "SELECT COUNT(*) FROM ops_retrieval_attempts WHERE job_id = ?",
            (self.job_id,),
        ).fetchone()
        return int(row[0])


@dataclass(slots=True)
class RecordingTransport:
    """A pure observer around the injected transport, with an optional pre-send attempt ledger.

    It exists because Decision 045 §9.2 requires **every** physical response to contribute its
    actual status - including the intermediate responses of a retry sequence, which the accepted
    :class:`FetchResult` deliberately does not carry - while §9.5 prohibits modifying
    ``sec/http_client.py`` to make receipt accounting convenient. Observing at the transport seam
    satisfies both: the accepted policy loop is untouched and unaware, and the observation is
    exact rather than reconstructed.

    Without a ledger it changes no behaviour: it forwards the request unchanged, returns the
    response object unchanged, and reads only ``status`` and ``failure`` - neither of which consumes
    a streamed body - so a payload reaches the accepted client exactly as the real transport
    produced it. When a :class:`PreSendAttemptLedger` is bound (the governed live path), one durable
    ``started`` reservation commits at this same seam **before** each physical send, so every retry
    and redirect send is counted, and a reservation that cannot be committed aborts the send it
    precedes rather than letting an uncounted attempt reach the wire (Decision 051 §6, §7.2).
    """

    transport: Transport
    log: PhysicalResponseLog
    ledger: PreSendAttemptLedger | None = None

    def send(self, request: SecRequest) -> TransportResponse:
        """Forward one request and record the status of the response it produced.

        A bound ledger reserves one durable ``started`` attempt *before* the physical send; if the
        reservation raises, ``transport.send`` is never reached and no physical send occurs. A send
        that raises after a successful reservation leaves that reservation stranded and still
        consumed; a send that returns settles the reservation to its transport-level terminal
        state.
        """
        reservation = self.ledger.reserve(request) if self.ledger is not None else None
        response = self.transport.send(request)
        self.log.record(response.status if response.succeeded_at_transport_level else None)
        if self.ledger is not None and reservation is not None:
            self.ledger.settle(reservation, succeeded=response.succeeded_at_transport_level)
        return response

    def close(self) -> None:
        """Release the wrapped transport's resources."""
        self.transport.close()


@dataclass(slots=True)
class ResponseAccounting:
    """The exhaustive Decision 045 §9 response-event universe for one window.

    Every response-policy event contributes **exactly one** classification bucket and **exactly
    one** status entry, so the strong invariant holds by construction:

    .. code-block:: text

        sum(response_classification_totals.values()) == sum(status_code_totals.values())

    It is verified rather than assumed: :meth:`absorb` reconciles the bucket stream derived from
    the accepted client's own action log against the physical sends the recording transport
    observed, and marks the accounting **undetermined** when they disagree. Decision 045 §9.5
    requires exactness or a stop, so an undetermined accounting refuses the receipt rather than
    rounding, inferring, or undercounting.
    """

    status_code_totals: dict[str, int] = field(default_factory=dict)
    response_classification_totals: dict[str, int] = field(
        default_factory=lambda: dict.fromkeys(RESPONSE_CLASSIFICATION_BUCKETS, 0)
    )
    redirect_hop_count: int = 0
    undetermined_basis: str | None = None

    @property
    def cooldown_count(self) -> int:
        """Decision 045 §11: exactly the physical responses classified into ``cooldown``.

        Never a count of sleeps, retries, redirect hops, or elapsed cooldown seconds.
        """
        return self.response_classification_totals["cooldown"]

    @property
    def classified_event_count(self) -> int:
        """Total response-policy buckets recorded."""
        return sum(self.response_classification_totals.values())

    @property
    def status_event_count(self) -> int:
        """Total status entries recorded, including the ``"0"`` sentinel."""
        return sum(self.status_code_totals.values())

    @property
    def is_exact(self) -> bool:
        """Whether every response event is accounted exactly once on both sides."""
        return (
            self.undetermined_basis is None
            and self.classified_event_count == self.status_event_count
        )

    def mark_undetermined(self, basis: str) -> None:
        """Record why the accounting cannot be proven exact. The first basis is kept."""
        if self.undetermined_basis is None:
            self.undetermined_basis = basis

    def absorb(self, result: FetchResult, sends: Sequence[int | None]) -> None:
        """Account one logical retrieval's physical responses, exactly once each.

        ``sends`` is the ordered status record of the physical sends this retrieval performed.
        The bucket stream is derived from the accepted client's action log, which appends exactly
        one marker per classified response; a followed redirect appends **no** marker and is
        counted from ``redirect_hops`` instead, which is why the two are reconciled against the
        send count before anything is recorded.
        """
        buckets = _derived_response_buckets(result.actions)
        hops = len(result.redirect_hops)
        if buckets is None:
            self.mark_undetermined(
                "the accepted client reported a response-policy action outside the accounted "
                "vocabulary, so its response bucket cannot be established"
            )
            return
        if len(buckets) + hops != len(sends):
            self.mark_undetermined(
                f"{len(sends)} physical response(s) were observed but "
                f"{len(buckets)} classification(s) and {hops} followed redirect(s) account for "
                f"{len(buckets) + hops}; every response event must be accounted exactly once"
            )
            return
        for status in sends:
            if status == 0:
                self.mark_undetermined(
                    "a transport-level success reported HTTP status 0, which is reserved "
                    "exclusively for the no-HTTP-status transport-failure sentinel"
                )
                return

        self.redirect_hop_count += hops
        # Decision 045 §9.3: a followed redirect contributes one `proceed` bucket, and its
        # redirect-hop count is a *different* metric that also increments for the same physical
        # response. Both are recorded; neither replaces the other.
        for _ in range(hops):
            self.response_classification_totals["proceed"] += 1
        for bucket in buckets:
            self.response_classification_totals[bucket] += 1
        for status in sends:
            key = NO_HTTP_STATUS_SENTINEL if status is None else str(status)
            self.status_code_totals[key] = self.status_code_totals.get(key, 0) + 1

    def as_receipt_totals(self) -> tuple[Mapping[str, int], Mapping[str, int]]:
        """The two frozen receipt maps, in deterministic key order."""
        return (
            dict(sorted(self.response_classification_totals.items())),
            dict(sorted(self.status_code_totals.items())),
        )


def _derived_response_buckets(actions: Sequence[str]) -> tuple[str, ...] | None:
    """Derive one response bucket per classified physical response, or ``None`` if unknown.

    Total over the accepted client's action vocabulary and fail-closed outside it: an unrecognized
    marker returns ``None`` rather than being skipped, because skipping it would silently
    undercount a real response event.
    """
    buckets: list[str] = []
    for action in actions:
        if action in _CLASSIFIED_ACTIONS:
            buckets.append(action)
        elif action == _NOT_MODIFIED_ACTION:
            buckets.append("proceed")
        elif action in _BOUNDARY_REFUSAL_ACTIONS:
            buckets.append("fail")
        elif action not in _NON_RESPONSE_ACTIONS:
            return None
    return tuple(buckets)


# --------------------------------------------------------------------------- #
# M3.2 acquisition-run identity: registration and attribution (Decision 045 §6A)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class AcquisitionRunBinding:
    """One live invocation's registered, verified acquisition-run identity.

    A run identifies **one live command invocation**, not a whole window (§6A.3). A resumed
    invocation therefore carries a *new* binding, and its predecessor lineage travels separately
    through ``--resume-from`` and the predecessor receipt identity.

    Like :class:`LiveOperationAuthorization`, this is evidence that the registration happened, not
    a grant: :func:`validate_acquisition_run` re-reads the durable row through a fresh read-only
    connection, so a fabricated instance buys nothing.
    """

    census_run_id: str
    window: str

    def __post_init__(self) -> None:
        """Refuse a binding that is not self-consistent."""
        if not self.census_run_id.strip():
            message = "an acquisition run binding requires a non-empty run identity"
            raise AcquisitionRunError(message)
        if self.window not in ACQUISITION_WINDOWS:
            message = (
                f"window {self.window!r} is not one of the accepted acquisition windows "
                f"{ACQUISITION_WINDOWS}"
            )
            raise AcquisitionRunError(message)


# --------------------------------------------------------------------------- #
# One-use clean-root carry-in authority (Decision 055 §6, ruling 055-B)
# --------------------------------------------------------------------------- #
#: The canonical-JSON schema of a carry-in authority artifact, and the fixed Decision 055 values
#: every authority is bound to. They live in :mod:`disclosure_drift.m3.recovery` beside the
#: consumption checkpoint they are also cross-checked against, so the artifact gate here and the
#: later catalog cross-check there compare against one set of constants rather than two. Re-exported
#: through this module's ``__all__`` because this is where the authority itself is validated.
#: Every field an authority artifact must carry, and nothing else. The set is **closed**: an
#: unknown field is refused rather than ignored, so an artifact cannot smuggle an unread claim past
#: validation. There is deliberately **no** self-hash field (Decision 055 §6.1) — the artifact's
#: identity is the SHA-256 of its exact canonical bytes, computed by the reader, and a hash recorded
#: inside its own preimage could never be verified without circularity.
_CARRY_IN_REQUIRED_FIELDS: Final[tuple[str, ...]] = (
    "acquisition_window",
    "approved_request_ceiling",
    "authorized_census_run_id",
    "authorizing_decision_reference",
    "historical_consumed_request_count",
    "historical_route_allocation",
    "orphan_adoption_decision_reference",
    "orphan_adoption_evidence_sha256",
    "request_plan_sha256",
    "schema_version",
)

#: A SHA-256 identity as this repository writes them: lowercase, exactly 64 hex digits. An
#: authority's external identity is one, because it is the digest of the artifact's canonical bytes
#: (Decision 055 §6.1) — an uppercase, truncated, prefixed, or free-text value identifies nothing.
_SHA256_IDENTITY_PATTERN: Final = re.compile(r"^[0-9a-f]{64}$")


class CarryInAuthorityError(AcquisitionError):
    """Raised when a carry-in authority is malformed, mismatched, or already consumed.

    Every one of these refuses **before** a transport is constructed, and none of them is
    recoverable in place: a replacement authority is a new owner act, never an automatic retry
    (Decision 055 §6.5).
    """


@dataclass(frozen=True, slots=True)
class CarryInAuthority:
    """One validated, not-yet-consumed carry-in authority.

    It authorizes exactly one **clean-root** live invocation to begin from a non-zero cumulative
    consumed baseline. It is **never a resume**: it names no predecessor receipt, and it may not
    coexist with ``--resume-from`` (Decision 055 §6).

    Like every other gate object in this module it is inert evidence rather than a grant, and here
    that is enforced rather than asserted: this is an ordinary public dataclass, so **constructing
    one directly is possible and grants nothing an artifact would not**. Every production surface
    that executes or burns an authority re-proves, from the object it was handed, the §6.1 content
    rule, the fixed Decision 055 bindings, and the canonical external identity
    (:func:`require_admitted_carry_in_authority`) — so an object carrying anything §6.1 forbids, an
    object naming any unaccepted binding, and a lawfully loaded one whose fields were mutated
    afterwards are each refused before any durable state or transport.

    An object whose bindings are the accepted ones and whose identity is recomputed to match them
    is, by construction, indistinguishable from the artifact carrying those bindings, and is
    admitted. That is not a gap this type can close: the identity is a digest over public inputs by
    a published rule, so it is an integrity identity rather than a signature. What bounds the
    exception is stated elsewhere and deliberately: the accepted bindings are fixed *values* rather
    than a shape (:func:`_verify_fixed_carry_in_bindings`), the single use is enforced by a durable
    ``ops_checkpoints`` primary key rather than by this object's existence, and the artifact's
    provenance — that it came from the governed evidence root — is a **procedural** control under
    §6.2, never an in-process one.
    """

    authority_sha256: str
    acquisition_window: str
    request_plan_sha256: str
    approved_request_ceiling: int
    historical_consumed_request_count: int
    historical_route_allocation: Mapping[str, int]
    authorizing_decision_reference: str
    authorized_census_run_id: str
    orphan_adoption_decision_reference: str
    orphan_adoption_evidence_sha256: str

    @property
    def checkpoint_key(self) -> str:
        """The deterministic ``ops_checkpoints`` key this authority burns its single use in."""
        return carry_in_checkpoint_key(self.authority_sha256)

    def checkpoint_value(self) -> str:
        """The canonical, non-sensitive record a later receipt and catalog cross-check reads.

        It preserves exactly what §7.5's cross-check needs and nothing more: the baseline carried
        in, the bindings it was granted against, and the run it authorized. It carries no secret, no
        identity header or value, no response body, and no private absolute path — and that is
        **proved** before this is ever called rather than asserted here. Every field below except
        ``authority_sha256`` is copied from a binding that
        :func:`require_admitted_carry_in_authority` has already scanned under §6.1, and
        ``authority_sha256`` is proved by that same re-proof to be a lowercase 64-hex digest, which
        no prohibited value can be. Since every boundary reaching this method runs that re-proof
        first, §6.3 holds for any authority — not only for one the CLI loader happened to admit.
        """
        return canonical_bytes(
            {
                "acquisition_window": self.acquisition_window,
                "approved_request_ceiling": self.approved_request_ceiling,
                "authority_sha256": self.authority_sha256,
                "authorized_census_run_id": self.authorized_census_run_id,
                "authorizing_decision_reference": self.authorizing_decision_reference,
                "consumed_request_count_carried_forward": (self.historical_consumed_request_count),
                "historical_route_allocation": dict(
                    sorted(self.historical_route_allocation.items())
                ),
                "request_plan_sha256": self.request_plan_sha256,
                "schema_version": CARRY_IN_AUTHORITY_SCHEMA_VERSION,
            }
        ).decode()


def _carry_in_authority_document(authority: CarryInAuthority) -> dict[str, object]:
    """The closed artifact document this object claims to be the admitted form of.

    Rebuilt from the object's **current** field values rather than retained from the bytes it was
    loaded from, because that is what makes it a proof rather than a memo: hashing a retained
    preimage would re-assert what the loader already knew, while hashing the reconstruction detects
    every field the object no longer agrees with.

    ``schema_version`` is supplied as the fixed constant because the object carries no version of
    its own and there is exactly one an authority may declare (Decision 055 §6.1) — an artifact
    declaring any other never becomes a :class:`CarryInAuthority` at all. The key set is exactly
    :data:`_CARRY_IN_REQUIRED_FIELDS`, which is what makes the digest below comparable to the
    digest of the artifact on disk.

    Raises:
        CarryInAuthorityError: the route allocation is not a mapping, so no closed document can be
            reconstructed from this object at all.
    """
    try:
        allocation = dict(authority.historical_route_allocation)
    except (TypeError, ValueError) as exc:
        message = (
            "the carry-in authority's route allocation is not a mapping, so the closed artifact "
            "document it claims to be the admitted form of cannot be reconstructed"
        )
        raise CarryInAuthorityError(message) from exc
    return {
        "acquisition_window": authority.acquisition_window,
        "approved_request_ceiling": authority.approved_request_ceiling,
        "authorized_census_run_id": authority.authorized_census_run_id,
        "authorizing_decision_reference": authority.authorizing_decision_reference,
        "historical_consumed_request_count": authority.historical_consumed_request_count,
        "historical_route_allocation": allocation,
        "orphan_adoption_decision_reference": authority.orphan_adoption_decision_reference,
        "orphan_adoption_evidence_sha256": authority.orphan_adoption_evidence_sha256,
        "request_plan_sha256": authority.request_plan_sha256,
        "schema_version": CARRY_IN_AUTHORITY_SCHEMA_VERSION,
    }


def _verify_carry_in_document_content(document: Mapping[str, object]) -> None:
    """Refuse a carry-in document carrying §6.1 prohibited content, one field at a time.

    The single scan that **both** the byte-ingestion boundary and the object re-proof run, so an
    artifact admitted from bytes and an object handed straight to an execution or burn boundary are
    held to exactly the same closed-document rule. Decision 055 states that rule of the artifact
    (§6.1) and of the checkpoint (§6.3), and neither statement is conditional on how the value in
    hand came to exist — so neither may be proved only on the path that happens to start from bytes.

    Each field's **value** is scanned in isolation, under a neutral key. The receipt scanner's
    key-fragment guard is therefore not applied to this artifact's own field names, and does not
    need to be: the key set is closed to :data:`_CARRY_IN_REQUIRED_FIELDS` on both paths before a
    caller reaches here, so a prohibited key name is impossible by construction rather than by
    scanning. Several of those decision-fixed names (``authorized_census_run_id``,
    ``authorizing_decision_reference``) contain the ``auth`` fragment that guards against an
    authorization header, and widening the receipt's own allowlist to accommodate a different
    artifact would loosen a control this artifact does not need loosened. Only the **top** level is
    neutralized, so nested keys — the route-allocation source identifiers — are still scanned.

    A refusal names the field and the rule it broke, never the value that broke it: the scanner's
    reason text is fixed prose. Where the prohibited content is itself a nested key, that key
    appears in the reported location, which is the minimum needed to say which entry was refused.

    Raises:
        CarryInAuthorityError: a value carries prohibited content, or is not in a form the scan can
            traverse. Both refuse before any durable state and before any transport.
    """
    for field_name in sorted(document):
        try:
            scan_for_prohibited_content({"value": document[field_name]})
        except ProhibitedReceiptContentError as exc:
            message = f"the carry-in authority carries prohibited content in {field_name}: {exc}"
            raise CarryInAuthorityError(message) from exc
        except ReceiptValidationError as exc:
            # Unreachable through either current caller, which each prove the field shapes first.
            # Kept because this is a safety scan: if it cannot traverse a value, it has not cleared
            # it, and "could not check" must fail closed rather than fall through as "clean".
            message = (
                f"the carry-in authority's {field_name} cannot be proved free of prohibited "
                f"content: {exc}"
            )
            raise CarryInAuthorityError(message) from exc


def require_admitted_carry_in_authority(authority: CarryInAuthority) -> None:
    """Re-prove, from the object alone, that this is *the* admitted Decision 055 carry-in.

    :func:`load_carry_in_authority` is the only place bytes become an authority, but it is not the
    only way an authority object reaches a production surface. :class:`CarryInAuthority` is an
    ordinary public dataclass: a caller can construct one directly, and a caller holding a lawfully
    loaded one can still mutate a mapping inside it. Neither may buy the one-use exception. So
    every production surface that **executes** or **burns** an authority calls this function on the
    object it was actually handed, and proves three things about it:

    1. **The §6.1 content rule** — no secret, no identity header or value, no response body, and no
       private absolute path in any binding. This is the same scan
       :func:`load_carry_in_authority` applies to the artifact's bytes, over the same closed
       document (:func:`_verify_carry_in_document_content`).
    2. **The fixed Decision 055 bindings** — schema ``m3-carry-in-authority/1.0``, window
       ``M3.2A``, the frozen request plan, cumulative ceiling ``801``, historical seed ``1``
       allocated wholly to ``sec_bulk_submissions`` as a whole mapping, ``Decision 055`` as the
       authorizing record, and a canonical non-055 orphan-adoption decision with a lowercase
       64-hex evidence identity.
    3. **The canonical external identity** — ``authority_sha256`` is the SHA-256 of the canonical
       bytes of the closed document the object represents (Decision 055 §6.1).

    The content rule is proved **first**, for two reasons. It is the one property Decision 055
    states unconditionally, of the artifact and of the checkpoint alike; and the binding comparison
    below quotes the values it disagrees with, so scanning first is what keeps a prohibited value
    out of a refusal message as well as out of ``ops_checkpoints``.

    What the third proves, and what it does not, is why the first two are proved here at all. The
    digest is an **integrity** identity, not a signature: it is computed from public bindings by a
    published rule, with no secret and no key, so a caller can recompute one matching whatever
    bindings it chose. What a match establishes is that the bindings are internally intact and have
    not moved since the object was minted — which is what catches post-admission mutation,
    including a moved route-allocation entry. What it cannot establish is **provenance**: that the
    artifact came from the governed evidence root remains a procedural control under §6.2, and no
    in-process check substitutes for it. So a matching digest is never treated as evidence that
    this module's own loader ran, and every property this gate needs is proved from the object.

    Raises:
        CarryInAuthorityError: a binding carries prohibited content, a fixed binding disagrees, or
            the external identity is not this document's. Each refuses before any durable state and
            before any transport.
    """
    document = _carry_in_authority_document(authority)
    _verify_carry_in_document_content(document)
    _verify_fixed_carry_in_bindings(authority)
    _verify_carry_in_authority_identity(authority, document)


def _verify_carry_in_authority_identity(
    authority: CarryInAuthority, document: Mapping[str, object]
) -> None:
    """Prove ``authority_sha256`` is the digest of the canonical document this object represents.

    Decision 055 §6.1 makes the SHA-256 of the exact canonical artifact bytes the authority's
    external identity, and forbids a self-hash field inside the artifact for it to be read back
    from. The identity is therefore *recomputable* from the bindings, and recomputing it is the
    check: an authority admitted from bytes reproduces it exactly, because the loader proved those
    bytes were already canonical before hashing them.

    Recomputable by **anyone**, though — the rule is published and every input is public — so a
    mismatch is evidence and a match is not. This detects an object whose bindings no longer agree
    with the identity it carries; it authenticates nothing. That is why
    :func:`require_admitted_carry_in_authority` proves the §6.1 content rule and the fixed bindings
    separately, rather than letting a matching digest stand in for either.

    ``document`` is the reconstruction the caller already built, passed in so the digest is proved
    over exactly the document the content scan cleared rather than over a second reconstruction.

    Raises:
        CarryInAuthorityError: the identity is not a lowercase 64-hex SHA-256, the bindings do not
            serialize to a canonical document at all, or the digest is not the one carried.
    """
    if not _SHA256_IDENTITY_PATTERN.match(authority.authority_sha256):
        message = (
            f"the carry-in authority's external identity {authority.authority_sha256!r} is not a "
            f"lowercase 64-hex SHA-256, so it identifies no canonical artifact"
        )
        raise CarryInAuthorityError(message)
    try:
        expected = hashlib.sha256(canonical_bytes(document)).hexdigest()
    except (ReceiptValidationError, TypeError) as exc:
        message = (
            f"the carry-in authority's bindings do not serialize to a canonical artifact document, "
            f"so it has no external identity to prove: {exc}"
        )
        raise CarryInAuthorityError(message) from exc
    if authority.authority_sha256 != expected:
        message = (
            "the carry-in authority's external identity is not the SHA-256 of the canonical "
            "artifact document its own bindings form, so that identity no longer describes those "
            "bindings: an authority whose bindings were mutated after admission, and an object "
            "assembled without recomputing its identity, each carry one that does not"
        )
        raise CarryInAuthorityError(message)


def load_carry_in_authority(payload: bytes) -> CarryInAuthority:
    """Parse, canonicalize, hash, and validate one carry-in authority artifact.

    Decision 055 §6.2 requires all four to happen **before transport construction**, and this
    function is where they happen: it is called from the operator surface, well before the single
    construction site is reachable at all.

    The bytes are validated *as bytes*. An artifact whose identity is a hash over its own canonical
    form has to round-trip exactly, so a document that parses but does not re-serialize to the same
    bytes — a different key order, extra whitespace, a non-canonical number — is refused rather than
    silently re-canonicalized into a different identity than the one the owner approved.

    Raises:
        CarryInAuthorityError: the artifact is unreadable, non-canonical, incomplete, or carries a
            field it may not.
    """
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"the carry-in authority is not readable UTF-8 JSON: {exc}"
        raise CarryInAuthorityError(message) from exc
    if not isinstance(document, dict):
        message = "the carry-in authority is not a JSON object"
        raise CarryInAuthorityError(message)

    present = set(document)
    required = set(_CARRY_IN_REQUIRED_FIELDS)
    if missing := sorted(required - present):
        message = (
            f"the carry-in authority is missing required binding(s): {', '.join(missing)}; every "
            f"binding is mandatory and none is inferred"
        )
        raise CarryInAuthorityError(message)
    if unexpected := sorted(present - required):
        message = (
            f"the carry-in authority carries unpermitted field(s): {', '.join(unexpected)}; the "
            f"field set is closed and no self-hash field is permitted inside the artifact"
        )
        raise CarryInAuthorityError(message)

    if canonical_bytes(document) != payload:
        message = (
            "the carry-in authority's stored bytes are not in canonical form, so the SHA-256 that "
            "identifies it would not be the digest of what is on disk"
        )
        raise CarryInAuthorityError(message)

    # The §6.1 prohibited-content scan, on the artifact's values exactly as they arrived. The field
    # set was just proved to be `_CARRY_IN_REQUIRED_FIELDS`, which is the precondition the shared
    # scan documents. It runs here *and* inside the re-proof below, and the two are not redundant:
    # this one sees the document as parsed — including a `schema_version` the reconstruction
    # replaces with the fixed constant, and values a later narrowing would reject for some other
    # reason — so prohibited content is refused as prohibited content wherever it was put.
    _verify_carry_in_document_content(document)

    if document["schema_version"] != CARRY_IN_AUTHORITY_SCHEMA_VERSION:
        message = (
            f"the carry-in authority declares schema {document['schema_version']!r}, not "
            f"{CARRY_IN_AUTHORITY_SCHEMA_VERSION!r}"
        )
        raise CarryInAuthorityError(message)

    route_allocation = document["historical_route_allocation"]
    if not isinstance(route_allocation, dict) or not route_allocation:
        message = "the carry-in authority's historical_route_allocation must be a non-empty object"
        raise CarryInAuthorityError(message)
    allocation: dict[str, int] = {}
    for source_id, count in route_allocation.items():
        if not isinstance(source_id, str) or not source_id.strip():
            message = "the carry-in authority's route allocation keys must be source identifiers"
            raise CarryInAuthorityError(message)
        allocation[source_id] = _carry_in_count(count, f"route allocation for {source_id!r}")

    authority = CarryInAuthority(
        authority_sha256=hashlib.sha256(payload).hexdigest(),
        acquisition_window=_carry_in_text(document["acquisition_window"], "acquisition_window"),
        request_plan_sha256=_carry_in_text(document["request_plan_sha256"], "request_plan_sha256"),
        approved_request_ceiling=_carry_in_count(
            document["approved_request_ceiling"], "approved_request_ceiling"
        ),
        historical_consumed_request_count=_carry_in_count(
            document["historical_consumed_request_count"], "historical_consumed_request_count"
        ),
        # Wrapped so an admitted authority's allocation cannot be mutated through it afterwards.
        # The local `allocation` goes out of scope with this call, so the proxy holds the only
        # reference to it. Prevention and detection are both wanted: this stops the mutation, and
        # `require_admitted_carry_in_authority` refuses any object that carries one anyway.
        historical_route_allocation=MappingProxyType(allocation),
        authorizing_decision_reference=_carry_in_text(
            document["authorizing_decision_reference"], "authorizing_decision_reference"
        ),
        authorized_census_run_id=_carry_in_text(
            document["authorized_census_run_id"], "authorized_census_run_id"
        ),
        orphan_adoption_decision_reference=_carry_in_text(
            document["orphan_adoption_decision_reference"], "orphan_adoption_decision_reference"
        ),
        orphan_adoption_evidence_sha256=_carry_in_text(
            document["orphan_adoption_evidence_sha256"], "orphan_adoption_evidence_sha256"
        ),
    )
    # An artifact that is well-formed but is not *the* accepted carry-in never becomes a
    # `CarryInAuthority` at all. The same re-proof every execution and consumption boundary runs is
    # run here, on the object just built: refusing at ingestion keeps a forged artifact out
    # entirely, and running the identical check means anything this function admits is something
    # those later boundaries will admit too, so a lawful artifact is never accepted here and
    # refused three frames later.
    require_admitted_carry_in_authority(authority)
    return authority


def _carry_in_text(value: object, field: str) -> str:
    """Narrow one required non-empty string binding, or refuse."""
    if not isinstance(value, str) or not value.strip():
        message = f"the carry-in authority's {field} must be a non-empty string"
        raise CarryInAuthorityError(message)
    return value


def _carry_in_count(value: object, field: str) -> int:
    """Narrow one required non-negative integer binding, or refuse."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"the carry-in authority's {field} must be a non-negative integer"
        raise CarryInAuthorityError(message)
    return value


def verify_carry_in_authority(
    authority: CarryInAuthority,
    *,
    window: str,
    plan_sha256: str,
    approved_ceiling: int,
    resuming: bool,
) -> None:
    """Prove the authority was granted for *this* invocation.

    Decision 055 §6.4: each of these refuses **before transport construction**. The authority is
    never trusted to describe the invocation — the invocation's own plan, window, and ceiling are
    the authority on those, and a disagreement means this artifact was not granted for this run.

    Two layers are proved here, and both are needed. The **invocation** layer is the comparison
    against this run's own arguments. The **fixed** layer — that the object is *the* accepted
    Decision 055 carry-in at all, seeded 1 of 801 on ``sec_bulk_submissions`` under the frozen
    plan, carrying the external identity its own bindings hash to — is re-proved at the end, on the
    object this call was handed. :func:`load_carry_in_authority` proves it too, but proving it only
    there would leave the guarantee resting on the assumption that every authority came from bytes,
    and :class:`CarryInAuthority` is publicly constructible and internally mutable, so that
    assumption is not one this gate may make.

    The fixed re-proof runs **last** deliberately. Nothing between here and there touches durable
    state, so the ordering changes no outcome — only which refusal an operator is shown, and the
    specific disagreement between an authority and *this invocation* is the more useful message
    when there is one.

    Raises:
        CarryInAuthorityError: a binding disagrees, the invocation is a resume, or the object is
            not the admitted Decision 055 carry-in.
    """
    if resuming:
        message = (
            "a carry-in authority and --resume-from may never coexist: a carry-in root begins a "
            "clean run from an approved baseline and is never a resume, and a resume carries its "
            "baseline forward from an exact predecessor receipt instead"
        )
        raise CarryInAuthorityError(message)
    if authority.acquisition_window != window:
        message = (
            f"the carry-in authority was granted for window {authority.acquisition_window!r} but "
            f"this invocation executes {window!r}"
        )
        raise CarryInAuthorityError(message)
    if authority.request_plan_sha256 != plan_sha256:
        message = (
            "the carry-in authority names a different approved request plan than this invocation "
            "is executing; a baseline is carried in only under the plan it was approved against"
        )
        raise CarryInAuthorityError(message)
    if authority.approved_request_ceiling != approved_ceiling:
        message = (
            f"the carry-in authority names ceiling {authority.approved_request_ceiling} but this "
            f"invocation was given {approved_ceiling}; the cumulative ceiling is never reset, "
            f"raised, shadowed, or made additive by a carry-in"
        )
        raise CarryInAuthorityError(message)
    allocated = sum(authority.historical_route_allocation.values())
    if allocated != authority.historical_consumed_request_count:
        message = (
            f"the carry-in authority allocates {allocated} historical attempt(s) across routes but "
            f"declares a consumed baseline of {authority.historical_consumed_request_count}; the "
            f"route allocation must account for the baseline exactly"
        )
        raise CarryInAuthorityError(message)
    for source_id in authority.historical_route_allocation:
        if source_id not in SOURCES:
            message = (
                f"the carry-in authority allocates historical consumption to {source_id!r}, which "
                f"is not a registered source route"
            )
            raise CarryInAuthorityError(message)
    if authority.historical_consumed_request_count > approved_ceiling:
        message = (
            f"the carry-in authority's baseline {authority.historical_consumed_request_count} "
            f"already exceeds the approved ceiling {approved_ceiling}; no further physical request "
            f"could lawfully occur"
        )
        raise CarryInAuthorityError(message)
    require_admitted_carry_in_authority(authority)


def _verify_fixed_carry_in_bindings(authority: CarryInAuthority) -> None:
    """Refuse any artifact that is not *the* Decision 055 M3.2A carry-in.

    Decision 055 authorizes one carry-in, for one historical fact: **1** physical attempt of
    cumulative **801**, on ``sec_bulk_submissions``, under the frozen plan, in window ``M3.2A``,
    citing Decision 055 and the separately authorized later Path-B adoption. That is not a shape an
    artifact may instantiate freely — it is a specific accepted value, and every part of it is
    compared literally here.

    This is what makes the exception single-use in substance rather than only in bookkeeping. The
    ``ops_checkpoints`` primary key stops the same artifact being consumed twice; this stops a
    *different* artifact being minted to obtain a second, differently-shaped exception — one seeded
    at ``0`` so a fresh run silently restarts the count, one allocating the attempt to another
    registered route, or one citing a decision that authorized nothing.

    Reached only through :func:`require_admitted_carry_in_authority`, which every artifact
    ingestion, execution, and consumption boundary calls. It is deliberately not the *whole* of
    that re-proof: the content scan proves separately that no binding carries anything §6.1
    forbids, and the identity check proves separately that the bindings still agree with the digest
    the object carries. These are public constants, so copying them is possible and is meant to be
    — what no object may do is name a different window, plan, ceiling, seed, route, or authorizing
    decision and still be admitted.

    Raises:
        CarryInAuthorityError: any fixed binding disagrees.
    """
    disagreement = carry_in_fixed_binding_disagreement(
        CarryInFixedBindings(
            # The artifact's own declared schema was proved equal to this constant before a
            # `CarryInAuthority` could be constructed from bytes, and the type carries no other
            # version, so supplying it here restates a proved fact rather than trusting a claim.
            # The shared validator takes it as a parameter because the *checkpoint* document it also
            # validates does carry a schema field that can genuinely be wrong.
            schema_version=CARRY_IN_AUTHORITY_SCHEMA_VERSION,
            acquisition_window=authority.acquisition_window,
            request_plan_sha256=authority.request_plan_sha256,
            approved_request_ceiling=authority.approved_request_ceiling,
            consumed_request_count=authority.historical_consumed_request_count,
            route_allocation=authority.historical_route_allocation,
            authorizing_decision_reference=authority.authorizing_decision_reference,
        )
    )
    if disagreement is None:
        disagreement = carry_in_orphan_reference_disagreement(
            authority.orphan_adoption_decision_reference,
            authority.orphan_adoption_evidence_sha256,
        )
    if disagreement is not None:
        message = (
            f"the carry-in authority does not match the accepted Decision 055 carry-in: "
            f"{disagreement}"
        )
        raise CarryInAuthorityError(message)


def require_m3_2a_consumed_baseline(window: str, *, carry_in: bool, resuming: bool) -> None:
    """Refuse an M3.2A live acquisition that would begin from no established baseline.

    **M3-L16** records that cumulative M3.2A consumption starts at **1**, not at zero, and lists a
    run observed starting its consumed count at zero as a stop condition. Before Decision 055 there
    was no mechanism to carry that baseline into a clean run, which is precisely why the entry is
    open; now that there is one, using it is not optional. An M3.2A invocation states where its
    baseline comes from, or it does not run.

    Exactly one source is required, and the two are mutually exclusive:

    * a **carry-in authority** — a clean root beginning from the approved historical baseline;
    * a **continuation** — a resume, whose baseline comes from its exact predecessor receipt, and
      which is separately gated by everything Decision 050 §8 requires of a resume.

    Supplying **both** is a contradiction a carry-in is never a resume, refused before this by
    :func:`verify_carry_in_authority`. Supplying **neither** is the zero-baseline start M3-L16
    forbids, refused here.

    This is scoped to ``M3.2A`` alone. Other windows have no historical consumption to carry, so
    their ordinary zero-baseline roots stay lawful and their receipts stay valid — M3.2B in
    particular begins with a genuinely unconsumed ceiling and is untouched by this gate.

    Raises:
        AcquisitionGateError: an M3.2A invocation supplies neither baseline source.
    """
    if window != CARRY_IN_ACQUISITION_WINDOW or carry_in or resuming:
        return
    message = (
        f"an {CARRY_IN_ACQUISITION_WINDOW} live acquisition must state the consumed baseline it "
        f"begins from: cumulative consumption already stands at "
        f"{CARRY_IN_HISTORICAL_CONSUMED_REQUEST_COUNT} of "
        f"{CARRY_IN_APPROVED_REQUEST_CEILING}, and a run that silently restarted the count at zero "
        f"would breach the accepted ceiling accounting. Supply the one-use carry-in authority for "
        f"a clean root, or an exact predecessor receipt for a resume; neither is inferred and "
        f"there is no zero-baseline default"
    )
    raise AcquisitionGateError(message)


def default_run_id_factory() -> str:
    """Allocate one opaque invocation run identity.

    Injectable at every call site that needs one, so a test binds a deterministic identity and a
    real invocation gets a fresh unique one. It is a bare identifier and carries no window, plan,
    receipt, or operator information: a run identity is a key, never a claim.
    """
    return f"m3-2-acquisition-{uuid.uuid4().hex}"


def register_acquisition_run(
    *,
    catalog_path: Path,
    lock_directory: Path,
    census_run_id: str,
    window: str,
    started_at_utc: str,
    detail: str,
    carry_in: CarryInAuthority | None = None,
) -> AcquisitionRunBinding:
    """Register exactly one durable ``ops_ingestion_jobs`` row for this live invocation.

    The Decision 045 §6A.1 responsibility, implemented here in the authorized M3 acquisition
    driver. It writes **one** row with ``job_kind = 'm3_2_acquisition'`` and ``stage`` equal to
    the governed acquisition window exactly. It deliberately does not reuse - and does not
    call - the private M2.2 census registration, which hardcodes an M2.2 job kind and stage;
    ``ops_ingestion_jobs`` carries no CHECK constraint on either column, so an M3.2 row is
    schema-legal and no migration is required or authorized.

    When ``carry_in`` is supplied, the authority is **consumed here, exactly once**, by inserting
    its deterministic ``ops_checkpoints`` primary key inside the **same** ``BEGIN IMMEDIATE``
    transaction as the run registration (Decision 055 §6.3). The two writes commit together or not
    at all, so there is no ordering in which a burned authority leaves no run, or a registered run
    leaves an unburned authority. The primary key itself is what enforces single use — a replay
    collides on it and is refused — so no migration, no new table, and no new column is needed.

    This is a **consumption** boundary, so it re-proves the authority itself rather than trusting
    that whoever assembled the call had it validated, and it compares the authority against **this
    registration's** window and run identity rather than only against the fixed Decision 055
    values. The two halves prove different things and neither implies the other: the re-proof shows
    the object is the admitted authority, while the contextual comparison shows the caller is the
    one it was granted to. It is reachable directly, and burning is the irreversible half of the
    mechanism: both checks happen before the catalog is even opened, so an authority that is not
    the admitted Decision 055 carry-in, or that authorizes some other window or run, leaves
    **neither** the checkpoint row nor the run row.

    Raises:
        AcquisitionRunError: the identity is malformed, already registered, or could not be
            committed. Every one of those refuses **before** a transport is constructed.
        CarryInAuthorityError: the authority is not the admitted Decision 055 carry-in, does not
            authorize this window or this run, or was already consumed. A consumed authority stays
            consumed; a replacement is a new owner act and is never minted here (Decision 055
            §6.5).
    """
    binding = AcquisitionRunBinding(census_run_id=census_run_id, window=window)
    if not started_at_utc.strip():
        message = "an acquisition run registration requires an explicit UTC start instant"
        raise AcquisitionRunError(message)
    if carry_in is not None:
        require_admitted_carry_in_authority(carry_in)
        # The re-proof above establishes that the authority names `M3.2A`; it establishes nothing
        # about the window *this registration* is for. Both contextual bindings are therefore
        # compared here for the same reason: what an authority authorizes is fixed and provable
        # from the object, while what a caller is registering is not, and the burn below is
        # irreversible. Without this, a genuine authority reaches an `M3.2B` job row and spends the
        # one M3.2A exception on a window with no historical consumption to carry.
        if carry_in.acquisition_window != binding.window:
            message = (
                f"the carry-in authority authorizes window {carry_in.acquisition_window!r} but "
                f"this registration is for {binding.window!r}; an authority may be consumed only "
                f"by the window it authorizes, and its single use is never spent on another"
            )
            raise CarryInAuthorityError(message)
        if carry_in.authorized_census_run_id != binding.census_run_id:
            message = (
                f"the carry-in authority authorizes run {carry_in.authorized_census_run_id!r} but "
                f"this registration is for {binding.census_run_id!r}; the authorized run identity "
                f"comes from the artifact and is never substituted"
            )
            raise CarryInAuthorityError(message)
    try:
        with (
            CatalogWriter(Path(catalog_path), Path(lock_directory)) as writer,
            writer.batch() as connection,
        ):
            # The authority is burned first, so a replay reports the refusal that actually caused
            # it. A carry-in root runs under the run identity its artifact names, so a replayed
            # authority also collides on that run id — and reporting *that* would tell the operator
            # a true but downstream fact, sending them to look at the run row rather than at the
            # authority they tried to reuse.
            if carry_in is not None:
                _consume_carry_in_authority(writer, connection, carry_in, started_at_utc)
            existing = connection.execute(
                "SELECT 1 FROM ops_ingestion_jobs WHERE job_id = ?",
                (binding.census_run_id,),
            ).fetchone()
            if existing is not None:
                message = (
                    f"census run {binding.census_run_id!r} is already registered; one live "
                    "invocation registers exactly one run, and an existing identity is never "
                    "adopted, reused, or overwritten"
                )
                raise AcquisitionRunError(message)
            writer.insert(
                "ops_ingestion_jobs",
                {
                    "job_id": binding.census_run_id,
                    "job_kind": ACQUISITION_JOB_KIND,
                    "job_state": "running",
                    "stage": binding.window,
                    "started_at_utc": started_at_utc,
                    "detail": detail,
                },
            )
    except (AcquisitionRunError, CarryInAuthorityError):
        raise
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        message = (
            f"the M3.2 acquisition run could not be registered ({type(exc).__name__}); no "
            "transport is constructed and no physical request occurs"
        )
        raise AcquisitionRunError(message) from exc
    return binding


def _consume_carry_in_authority(
    writer: CatalogWriter,
    connection: sqlite3.Connection,
    carry_in: CarryInAuthority,
    started_at_utc: str,
) -> None:
    """Burn one carry-in authority inside the caller's open transaction.

    The read-then-insert pair is safe precisely because the caller's transaction is
    ``BEGIN IMMEDIATE``: the write lock is already held, so nothing can interleave between the
    check and the insert. The explicit ``SELECT`` exists for the refusal *message* — the
    ``checkpoint_key TEXT PRIMARY KEY`` is the actual guarantee, and the ``IntegrityError`` path
    below is what holds if this check is ever removed.
    """
    key = carry_in.checkpoint_key
    if connection.execute(
        "SELECT 1 FROM ops_checkpoints WHERE checkpoint_key = ?", (key,)
    ).fetchone():
        message = (
            "this carry-in authority has already been consumed; it authorizes exactly one clean "
            "run and is never reissued, retried, or replaced automatically — a replacement "
            "authority is a new owner act"
        )
        raise CarryInAuthorityError(message)
    try:
        writer.insert(
            "ops_checkpoints",
            {
                "checkpoint_key": key,
                "checkpoint_value": carry_in.checkpoint_value(),
                "updated_at_utc": started_at_utc,
            },
        )
    except sqlite3.IntegrityError as exc:
        message = (
            "this carry-in authority has already been consumed; its single use is enforced by the "
            "checkpoint primary key and is never reissued automatically"
        )
        raise CarryInAuthorityError(message) from exc


def validate_acquisition_run(catalog_path: Path, census_run_id: str) -> str:
    """Return the registered stage of one M3.2 acquisition run, or refuse.

    Read through a genuinely fresh read-only connection, so what it proves is what is *durable*
    rather than what some in-memory writer believed. The row must exist, carry exactly
    ``job_kind = 'm3_2_acquisition'``, and carry an accepted acquisition window as its stage:
    an unknown identity, an M2.2 census run, and a row with any other stage are each refused
    (Decision 045 §4.6, §4.7).

    Raises:
        AcquisitionRunError: the run does not resolve to a lawful M3.2 acquisition run.
    """
    if not census_run_id or not census_run_id.strip():
        message = (
            "no census run identity was supplied; an M3.2 run-scoped surface requires an "
            "already-registered ops_ingestion_jobs.job_id and never fabricates one"
        )
        raise AcquisitionRunError(message)
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            row = connection.execute(
                "SELECT job_kind, stage FROM ops_ingestion_jobs WHERE job_id = ?",
                (census_run_id,),
            ).fetchone()
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        message = (
            f"census run {census_run_id!r} could not be validated against the catalog "
            f"({type(exc).__name__})"
        )
        raise AcquisitionRunError(message) from exc
    if row is None:
        message = (
            f"census run {census_run_id!r} does not resolve to an existing governed "
            "ops_ingestion_jobs row; an unknown run identity fails closed and is never created "
            "or substituted here"
        )
        raise AcquisitionRunError(message)
    job_kind = str(row["job_kind"])
    stage = str(row["stage"])
    if job_kind != ACQUISITION_JOB_KIND:
        message = (
            f"census run {census_run_id!r} carries job kind {job_kind!r}, not "
            f"{ACQUISITION_JOB_KIND!r}; this surface scopes to M3.2 acquisition runs only"
        )
        raise AcquisitionRunError(message)
    if stage not in ACQUISITION_WINDOWS:
        message = (
            f"census run {census_run_id!r} carries stage {stage!r}, which is not one of the "
            f"accepted acquisition windows {ACQUISITION_WINDOWS}"
        )
        raise AcquisitionRunError(message)
    return stage


def finish_acquisition_run(
    *,
    catalog_path: Path,
    lock_directory: Path,
    census_run_id: str,
    job_state: str,
    finished_at_utc: str,
    detail: str,
) -> bool:
    """Close the registered run row, reporting failure as ``False`` rather than raising.

    Terminal bookkeeping only: the window's own evidence is its observations, its attribution, and
    its receipt. A failure to close the row must not discard a window whose objects are promoted
    and whose rows are committed, so it is reported and left to a later inspection.

    ``job_state`` is stated by the caller rather than derived from a boolean, because an
    invocation has three truthful terminal states and not two. A window that completed is
    ``completed``; one that failed is ``failed``; one that was externally interrupted is
    ``stopped`` — it neither completed nor failed, and reporting it as either would be a false
    record of what the invocation did. All three are literals migration ``0001``'s CHECK
    constraint already admits: nothing here adds a state, a column, or a migration, and
    ``interrupted`` is deliberately **not** introduced as a database state — it is the receipt's
    completion vocabulary, not this table's.

    Raises:
        AcquisitionRunError: ``job_state`` is not one of :data:`ACQUISITION_RUN_JOB_STATES`. A
            caller error rather than an operational one, so it refuses instead of returning
            ``False``.
    """
    if job_state not in ACQUISITION_RUN_JOB_STATES:
        message = (
            f"job state {job_state!r} is not one of the accepted terminal acquisition-run states "
            f"{ACQUISITION_RUN_JOB_STATES}; a run row is never closed into an invented state"
        )
        raise AcquisitionRunError(message)
    try:
        with (
            CatalogWriter(Path(catalog_path), Path(lock_directory)) as writer,
            writer.batch() as (connection),
        ):
            connection.execute(
                "UPDATE ops_ingestion_jobs SET job_state = ?, finished_at_utc = ?, detail = ? "
                "WHERE job_id = ?",
                (job_state, finished_at_utc, detail, census_run_id),
            )
    except (DisclosureDriftError, sqlite3.Error, OSError):
        return False
    return True


def acquisition_run_job_state(outcome: WindowOutcome) -> str:
    """The truthful terminal ``ops_ingestion_jobs.job_state`` for one finished window.

    Three outcomes, three states, no collapsing. A genuine interruption is ``stopped`` rather than
    ``completed``: an interrupted invocation did not complete its window, and recording it as
    completed would make the run row contradict the interrupted receipt beside it.
    """
    if outcome.completion_status == "interrupted":
        return "stopped"
    return "completed" if outcome.completed_successfully else "failed"


#: How a terminal request disposition maps onto the accepted ``census_plan_sources`` retrieval
#: vocabulary. Every value is one the existing CHECK constraint already admits; none is invented.
_PLAN_SOURCE_RETRIEVAL_STATES: Final[Mapping[str, str]] = {
    "satisfied_new": "retrieved",
    "satisfied_duplicate": "retrieved",
    "satisfied_reused": "reused",
    "absent": "unavailable",
    "quarantined": "quarantined",
    "failed": "failed",
    "stopped": "unknown",
    "not_attempted": "not_retrieved",
}


def _plan_source_row(
    run: AcquisitionRunBinding,
    outcome: RequestOutcome,
    *,
    recorded_at_utc: str,
) -> Mapping[str, object]:
    """Render one run-to-observation attribution row for ``census_plan_sources``.

    **Why this relation, proven from the existing schema** (Decision 045 §6A.4 requires the
    argument to be made before the relation is used, not after):

    * it durably carries the **run** identity - ``census_run_id`` is
      ``NOT NULL REFERENCES ops_ingestion_jobs(job_id)``, the very table §6A.1 registers the M3.2
      run in, so the reference resolves to this invocation's own row;
    * it durably carries the **observation** identity - ``observation_id REFERENCES
      census_source_observations(observation_id)``, the same table the accepted
      :class:`ObservationRecorder` writes, so an attributed observation is the one that was
      actually committed;
    * its **existing semantics are the semantics being recorded**. Migration `0004` states its
      purpose as deriving a run's completion claim "from explicit per-instance terminal states",
      keyed by ``(census_run_id, source_instance_id)``: for one run, one planned source instance,
      what terminal state it reached and which observation it produced. That is exactly what an
      M3.2 acquisition invocation owes - accepted contract §14 makes the identical distinction
      between terminating and being satisfied - so this is the relation's own meaning rather than
      a convenient column shape. ``census_source_observations_r3`` carries no run column
      (migration `0008`), and the sibling run-scoped relations are narrower: ``census_recovery_
      states`` records recovery scenarios rather than ordinary retrievals, and
      ``census_index_instances`` covers only the quarterly index route.

    The M3.2 driver's own vocabulary is *already* this family: Decision 041 has its accepted T2.4
    recovery applier writing ``census_recovery_states`` under a ``census_run_id`` that is an
    ``ops_ingestion_jobs.job_id``. Nothing here creates a table, a column, a migration, an index,
    a reason code, or an event vocabulary.

    Every value below is one the existing CHECK constraints already admit. ``parser_state`` is
    ``not_started`` and is meant literally: Milestone 3.2 acquires metadata objects and parses
    none of them, so claiming any other parser state would be a false record.
    """
    satisfied = outcome.satisfies_requirement
    blocking = sorted(
        code
        for code in outcome.reason_codes
        if code in REASON_CODES and REASON_CODES[code].blocks_release
    )
    if satisfied:
        qa_state = "passed"
    elif outcome.disposition in {"not_attempted", "stopped"}:
        qa_state = "unknown"
    else:
        qa_state = "blocked"
    return {
        "census_run_id": run.census_run_id,
        "source_instance_id": outcome.request.identity_label,
        "source_id": outcome.request.source_id,
        "request_identity": planned_request_identity(outcome.request),
        "required": 1,
        "source_scope": (
            "historical" if outcome.request.source_id == "sec_submissions_historical" else "base"
        ),
        "retrieval_state": _PLAN_SOURCE_RETRIEVAL_STATES[outcome.disposition],
        "snapshot_state": "verified" if satisfied else "not_verified",
        "parser_state": "not_started",
        "catalog_state": "committed" if outcome.observation_id else "not_started",
        "qa_state": qa_state,
        "unresolved_blocking_reasons_json": json.dumps(blocking),
        "observation_id": outcome.observation_id,
        "successful_terminal": int(satisfied),
        "updated_at_utc": recorded_at_utc,
    }


# --------------------------------------------------------------------------- #
# Run-scoped drift inspection (Decision 045 §4.6)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RunScopedDrift:
    """Drift attributable through durable lineage to one exact M3.2 acquisition run."""

    census_run_id: str
    stage: str
    attributed_observation_count: int
    entries: tuple[DriftListingEntry, ...]

    @property
    def blocking(self) -> tuple[DriftListingEntry, ...]:
        """Drift events whose registered reasons block release."""
        return tuple(entry for entry in self.entries if entry.blocking)

    @property
    def nonblocking(self) -> tuple[DriftListingEntry, ...]:
        """Drift events observed and retained without blocking."""
        return tuple(entry for entry in self.entries if not entry.blocking)

    @property
    def has_blocking(self) -> bool:
        """Whether any attributed drift event blocks."""
        return bool(self.blocking)


def drift_for_run(*, catalog_path: Path, census_run_id: str) -> RunScopedDrift:
    """List the drift events attributable to exactly one M3.2 acquisition run.

    **There is no global fallback.** The run is validated first
    (:func:`validate_acquisition_run`), and the listing is then restricted to the observations
    that run durably owns through ``census_plan_sources``. A run that owns no attribution at all
    is *unattributable* rather than clean: drift could not be scoped to it, so it refuses rather
    than silently reporting an empty listing that reads like a passing run (Decision 045 §4.6).

    Read-only throughout: the connection is the accepted read-only inspector's, so a write is
    impossible rather than merely unintended.

    Raises:
        AcquisitionRunError: the run is unknown, not an M3.2 acquisition run, carries a stage
            outside the accepted windows, or owns no durable attribution.
    """
    stage = validate_acquisition_run(catalog_path, census_run_id)
    try:
        with read_only_catalog(Path(catalog_path)) as connection:
            rows = connection.execute(
                "SELECT observation_id FROM census_plan_sources WHERE census_run_id = ? "
                "ORDER BY source_instance_id",
                (census_run_id,),
            ).fetchall()
            observations = load_observations(connection)
    except (DisclosureDriftError, sqlite3.Error, OSError) as exc:
        message = (
            f"the drift listing for census run {census_run_id!r} could not be read "
            f"({type(exc).__name__})"
        )
        raise AcquisitionRunError(message) from exc

    if not rows:
        message = (
            f"census run {census_run_id!r} owns no durable observation attribution, so drift "
            "cannot be scoped to it; an unattributable run fails closed rather than reporting "
            "the unscoped global drift listing"
        )
        raise AcquisitionRunError(message)

    attributed = {str(row["observation_id"]) for row in rows if row["observation_id"] is not None}
    entries: list[DriftListingEntry] = []
    for observation in observations:
        if observation.observation_id not in attributed:
            continue
        family, blocking = _drift_flags(observation.reason_codes)
        if family:
            entries.append(
                DriftListingEntry(
                    observation_id=observation.observation_id,
                    source_id=observation.source_id,
                    request_identity=observation.identity,
                    reason_codes=family,
                    blocking=blocking,
                )
            )
    entries.sort(key=lambda entry: entry.observation_id)
    return RunScopedDrift(
        census_run_id=census_run_id,
        stage=stage,
        attributed_observation_count=len(attributed),
        entries=tuple(entries),
    )


# --------------------------------------------------------------------------- #
# Deterministic M3.2B dependent-plan derivation (Decision 045 §4.3, §13)
# --------------------------------------------------------------------------- #
#: The schema of the explicit reconciliation set this derivation consumes. It is the reviewed
#: operator artifact that states which frozen M3.2A objects the derivation must verify and which
#: dependent instances it must produce. A set of another schema is refused rather than adapted.
DEPENDENT_RECONCILIATION_SET_VERSION: Final = "m3-2b-reconciliation-set/1.0"

#: The window a dependent derivation may derive *from*. Decision 045 §4.3 fixes it exactly.
_DEPENDENT_SOURCE_WINDOW: Final = "M3.2A"


@dataclass(frozen=True, slots=True)
class DependentPlanDerivation:
    """The result of one deterministic M3.2B dependent-plan derivation."""

    plan: RequestPlan
    plan_bytes: bytes
    verified_object_count: int
    entity_instance_count: int
    historical_instance_count: int

    @property
    def dependent_instance_count(self) -> int:
        """Total dependent logical requests the derived plan states."""
        return self.entity_instance_count + self.historical_instance_count


def derive_dependent_plan(
    *,
    from_window: str,
    catalog_path: Path,
    storage: StorageBinding,
    reconciliation_set: Mapping[str, object],
    requests_per_second: float,
    transport_capable_configuration: bool,
) -> DependentPlanDerivation:
    """Derive the M3.2B dependent plan from frozen M3.2A objects. Zero network, always.

    Structurally zero-network: this function constructs no transport, imports no client, and
    accepts none - there is no seam through which one could reach it. It additionally **refuses**
    when the invoking configuration is transport-capable at all, so a derivation can never be run
    from a configuration that could have acquired something (Decision 045 §4.3).

    The derivation is a pure function of durable evidence and one reviewed artifact:

    1. the ``--from-window`` must be exactly ``M3.2A``;
    2. every frozen object the reconciliation set declares must exist as a committed, usable
       observation with that exact ``source_id`` and ``request_identity``, must carry complete
       provenance, must declare the exact ``content_sha256`` the set names, and must still hash to
       it on disk;
    3. agreement is checked in **both** directions - a declared object the catalog does not hold
       and a satisfying bootstrap object the set does not declare are each a refusal, because
       either one means the set and the frozen evidence describe different windows;
    4. only the two authorized dependent routes may be derived, each instance must construct a
       lawful in-family URL, and no instance may address a filing body;
    5. the instance counts come **entirely** from the reviewed set. Nothing here estimates,
       rounds, or extrapolates the eventual exact M3.2B request count, and a set that states no
       dependent instance is refused rather than written out as a zero-request plan.

    Raises:
        DependentPlanError: any of the above does not hold. No plan and no success receipt is
            produced on any refusal.
    """
    if transport_capable_configuration:
        message = (
            "dependent-plan derivation refuses to run from a transport-capable configuration; "
            "it is a zero-network derivation over frozen objects, and a configuration that "
            "could acquire is never the one that derives"
        )
        raise DependentPlanError(message)
    if from_window != _DEPENDENT_SOURCE_WINDOW:
        message = (
            f"dependent-plan derivation derives from {_DEPENDENT_SOURCE_WINDOW!r} only; "
            f"received {from_window!r}"
        )
        raise DependentPlanError(message)

    declared_version = reconciliation_set.get("reconciliation_set_schema_version")
    if declared_version != DEPENDENT_RECONCILIATION_SET_VERSION:
        message = (
            f"the reconciliation set declares schema {declared_version!r}, not "
            f"{DEPENDENT_RECONCILIATION_SET_VERSION!r}; a set of another schema is not this set"
        )
        raise DependentPlanError(message)
    if reconciliation_set.get("from_window") != _DEPENDENT_SOURCE_WINDOW:
        message = (
            f"the reconciliation set names source window "
            f"{reconciliation_set.get('from_window')!r}, not {_DEPENDENT_SOURCE_WINDOW!r}"
        )
        raise DependentPlanError(message)

    inputs = _dependent_plan_inputs(reconciliation_set)
    reconstruction = _dependent_reconstruction(catalog_path, storage)
    verified = _verify_frozen_objects(reconciliation_set, reconstruction, storage)
    entity, historical = _dependent_instance_counts(reconciliation_set)

    plan = build_m3_2b_dependent_plan(
        coverage_start=inputs.coverage_start,
        coverage_end=inputs.coverage_end,
        as_of_date=inputs.as_of_date,
        include_open_quarter=inputs.include_open_quarter,
        calendar_year=inputs.calendar_year,
        calendar_evidence_entry_count=inputs.calendar_evidence_entry_count,
        entity_instance_count=entity,
        historical_instance_count=historical,
        requests_per_second=requests_per_second,
    )
    return DependentPlanDerivation(
        plan=plan,
        plan_bytes=canonical_plan_bytes(plan),
        verified_object_count=verified,
        entity_instance_count=entity,
        historical_instance_count=historical,
    )


def _dependent_reconstruction(
    catalog_path: Path,
    storage: StorageBinding,
) -> CatalogReconstruction:
    """Rebuild catalog-authoritative state for the derivation, refusing an absent catalog."""
    try:
        return reconstruct_catalog_state(catalog_path=catalog_path, storage=storage)
    except AcquisitionGateError as exc:
        message = f"the frozen M3.2A evidence cannot be read: {exc}"
        raise DependentPlanError(message) from exc


@dataclass(frozen=True, slots=True)
class _DependentPlanInputs:
    """The explicit derivation inputs the reviewed reconciliation set states."""

    coverage_start: date
    coverage_end: date
    as_of_date: date
    include_open_quarter: bool
    calendar_year: int
    calendar_evidence_entry_count: int


def _dependent_plan_inputs(reconciliation_set: Mapping[str, object]) -> _DependentPlanInputs:
    """Read the explicit plan inputs the reviewed set carries, refusing anything missing.

    These are carried through to the derived document as provenance rather than used as planning
    inputs - no M3.2B route is a quarterly index or a calendar announcement - but the frozen
    ``m3-request-plan/1.0`` shape requires them, so they are stated explicitly in the reviewed
    artifact rather than defaulted, inferred, or read from the clock.
    """
    block = reconciliation_set.get("plan_inputs")
    if not isinstance(block, Mapping):
        message = (
            "the reconciliation set carries no 'plan_inputs' object; the derived plan document's "
            "inputs are stated explicitly in the reviewed set, never inferred or defaulted"
        )
        raise DependentPlanError(message)
    try:
        return _DependentPlanInputs(
            coverage_start=date.fromisoformat(str(block["coverage_start"])),
            coverage_end=date.fromisoformat(str(block["coverage_end"])),
            as_of_date=date.fromisoformat(str(block["as_of_date"])),
            include_open_quarter=bool(block["include_open_quarter"]),
            calendar_year=int(str(block["calendar_year"])),
            calendar_evidence_entry_count=int(str(block["calendar_evidence_entry_count"])),
        )
    except (KeyError, TypeError, ValueError) as exc:
        message = f"the reconciliation set's 'plan_inputs' are not complete and well-formed: {exc}"
        raise DependentPlanError(message) from exc


def _verify_frozen_objects(
    reconciliation_set: Mapping[str, object],
    reconstruction: CatalogReconstruction,
    storage: StorageBinding,
) -> int:
    """Verify identity, hash, and provenance of every declared frozen object, both directions."""
    declared = reconciliation_set.get("frozen_objects")
    if not isinstance(declared, list) or not declared:
        message = (
            "the reconciliation set declares no 'frozen_objects'; a derivation that verifies "
            "nothing is refused rather than treated as vacuously agreeing"
        )
        raise DependentPlanError(message)

    satisfying = {
        (observation.source_id, observation.identity)
        for observation in reconstruction.observations
        if observation.source_id in M3_2A_BOOTSTRAP_ROUTES
        and verified_reusable_predecessor(
            reconstruction, observation.source_id, observation.identity
        )
        is not None
    }
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(declared):
        if not isinstance(entry, Mapping):
            message = f"frozen object {index} is not an object"
            raise DependentPlanError(message)
        source_id = str(entry.get("source_id", ""))
        identity = str(entry.get("request_identity", ""))
        content_sha256 = str(entry.get("content_sha256", ""))
        if source_id not in M3_2A_BOOTSTRAP_ROUTES:
            message = (
                f"frozen object {index} names route {source_id!r}, which is not an M3.2A "
                "bootstrap route; a dependent derivation reads only frozen bootstrap evidence"
            )
            raise DependentPlanError(message)
        if (source_id, identity) in seen:
            message = f"frozen object {index} repeats identity {identity!r}"
            raise DependentPlanError(message)
        seen.add((source_id, identity))
        _verify_one_frozen_object(
            index, source_id, identity, content_sha256, reconstruction, storage
        )

    undeclared = sorted(satisfying - seen)
    if undeclared:
        message = (
            f"{len(undeclared)} satisfying frozen M3.2A object(s) are not declared by the "
            f"reconciliation set (first: {undeclared[0][0]!r}); the frozen evidence and the "
            "reviewed set describe different windows, so the derivation refuses rather than "
            "deriving from whichever one it happened to read"
        )
        raise DependentPlanError(message)
    return len(seen)


def _verify_one_frozen_object(
    index: int,
    source_id: str,
    identity: str,
    content_sha256: str,
    reconstruction: CatalogReconstruction,
    storage: StorageBinding,
) -> None:
    """Prove one declared frozen object present, hash-exact, and provenance-complete."""
    predecessor = verified_reusable_predecessor(reconstruction, source_id, identity)
    if predecessor is None or predecessor.observation_id is None:
        message = (
            f"frozen object {index} ({source_id}) does not resolve to a verified, reusable "
            "committed observation; a dependent plan is derived only from frozen evidence that "
            "verifies at the point of use"
        )
        raise DependentPlanError(message)
    observation = reconstruction.by_id(predecessor.observation_id)
    if observation is None:
        message = f"frozen object {index} ({source_id}) names an observation the catalog lost"
        raise DependentPlanError(message)
    missing = [
        name
        for name in ("relative_storage_path", "retrieved_at_utc", "purpose", "requested_url")
        if not getattr(observation, name, None)
    ]
    if missing:
        message = (
            f"frozen object {index} ({source_id}) is missing required provenance "
            f"{sorted(missing)}; incomplete provenance is refused rather than derived from"
        )
        raise DependentPlanError(message)
    if observation.content_sha256 != content_sha256 or not content_sha256:
        message = (
            f"frozen object {index} ({source_id}) declares content_sha256 "
            f"{content_sha256[:12]!r}... but the committed observation carries a different "
            "digest; the reviewed set and the frozen object disagree"
        )
        raise DependentPlanError(message)
    try:
        storage.snapshot_store.verify_payload(observation)
    except (DisclosureDriftError, OSError) as exc:
        message = (
            f"frozen object {index} ({source_id}) does not still hash to its recorded digest "
            f"on disk ({type(exc).__name__})"
        )
        raise DependentPlanError(message) from exc


def _dependent_instance_counts(reconciliation_set: Mapping[str, object]) -> tuple[int, int]:
    """Count the reviewed dependent instances per route, proving each one lawful."""
    declared = reconciliation_set.get("dependent_instances")
    if not isinstance(declared, list) or not declared:
        message = (
            "the reconciliation set states no 'dependent_instances'; the eventual exact M3.2B "
            "request count comes from reviewed evidence alone, and a derivation never invents, "
            "estimates, or writes out a zero-request dependent plan"
        )
        raise DependentPlanError(message)

    counts = dict.fromkeys(M3_2B_DEPENDENT_ROUTES, 0)
    seen: set[tuple[str, str]] = set()
    for index, entry in enumerate(declared):
        if not isinstance(entry, Mapping):
            message = f"dependent instance {index} is not an object"
            raise DependentPlanError(message)
        source_id = str(entry.get("source_id", ""))
        instance_key = str(entry.get("instance_key", ""))
        parameters = entry.get("parameters")
        if source_id not in M3_2B_DEPENDENT_ROUTES:
            message = (
                f"dependent instance {index} names route {source_id!r}; only "
                f"{list(M3_2B_DEPENDENT_ROUTES)} may be derived"
            )
            raise DependentPlanError(message)
        if not instance_key.strip():
            message = f"dependent instance {index} carries no instance key"
            raise DependentPlanError(message)
        if not isinstance(parameters, Mapping):
            message = f"dependent instance {index} carries no 'parameters' object"
            raise DependentPlanError(message)
        if (source_id, instance_key) in seen:
            message = (
                f"dependent instance {index} repeats identity {source_id}:{instance_key}; two "
                "planned requests for one identity would retrieve one object and count twice"
            )
            raise DependentPlanError(message)
        seen.add((source_id, instance_key))
        _verify_dependent_instance_url(index, source_id, parameters)
        counts[source_id] += 1
    return counts["sec_submissions_entity"], counts["sec_submissions_historical"]


def _verify_dependent_instance_url(
    index: int,
    source_id: str,
    parameters: Mapping[str, object],
) -> None:
    """Prove one dependent instance constructs a lawful, non-filing-body registered URL."""
    spec = require_registered(source_id)
    try:
        url = spec.url(**{str(key): str(value) for key, value in parameters.items()})
    except DisclosureDriftError as exc:
        message = f"dependent instance {index} ({source_id}) cannot construct its URL: {exc}"
        raise DependentPlanError(message) from exc
    if filing_body_url_is_prohibited(url):
        message = (
            f"dependent instance {index} ({source_id}) constructs a filing-body or accession "
            "URL; Milestone 3.2 acquires metadata only"
        )
        raise DependentPlanError(message)


# --------------------------------------------------------------------------- #
# The live operator boundary and the single transport-construction site
# (Decision 045 §4.2, §6, §6A.2, §14)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class LiveOperatorGate:
    """The operator-boundary facts proved at the command surface, restated at the wire.

    The accepted contract §8 gate ladder is evaluated where a configuration file, an explicit
    ``--live`` flag, and the canonical SEC identity validator can be read - the operator command.
    This type carries those results to the one place a transport is built, so the complete
    Decision 045 §6 conjunction is asserted **adjacent to** the construction site rather than
    trusted from a caller several frames away.

    It is inert, exactly like :class:`LiveOperationAuthorization`: it grants nothing, and every
    field is a fact the command surface derived from real configuration and a real validator. A
    fabricated instance still cannot satisfy the plan-hash, window, ceiling, run-registration, or
    later owner-gated conditions, each of which is proved separately from durable evidence.
    """

    explicit_live: bool
    network_enabled: bool
    m3_acquire_enabled: bool
    sec_identity_validated: bool
    stage_authority_reference: str

    def __post_init__(self) -> None:
        """Refuse a gate that does not carry every required operator-boundary fact.

        Each element is checked **individually** and names itself in the refusal, so a control
        that stops being enforced fails a test of its own rather than hiding inside a conjunction
        that some other element still happens to satisfy.
        """
        if not self.explicit_live:
            message = (
                "live acquisition requires the explicit --live flag; there is no default, and no "
                "configuration key or gate token stands in for it"
            )
            raise AcquisitionGateError(message)
        if not self.network_enabled:
            message = "live acquisition requires the accepted network.enabled prerequisite state"
            raise AcquisitionGateError(message)
        if not self.m3_acquire_enabled:
            message = (
                "live acquisition requires network.m3_acquire_enabled; the global network switch "
                "never enables acquisition on its own"
            )
            raise AcquisitionGateError(message)
        if not self.sec_identity_validated:
            message = (
                "live acquisition requires a contact identity accepted by the canonical SEC "
                "identity validator"
            )
            raise AcquisitionGateError(message)
        if not self.stage_authority_reference.strip():
            message = (
                "live acquisition must name the accepted contract and stage authority it runs "
                "under; an unnamed authority is refused rather than treated as sufficient"
            )
            raise AcquisitionGateError(message)


@dataclass(frozen=True, slots=True)
class LiveAcquisitionResult:
    """Everything one lawful live invocation produced, for receipt assembly."""

    census_run_id: str
    outcome: WindowOutcome
    accounting: ResponseAccounting
    started_at_utc: str
    completed_at_utc: str
    predecessor_receipt_id: str | None
    carried_forward_consumed: int | None
    run_closed: bool
    carry_in_authority_sha256: str | None = None

    @property
    def resumed(self) -> bool:
        """Whether this invocation continued an exact predecessor receipt."""
        return self.predecessor_receipt_id is not None

    @property
    def carried_in(self) -> bool:
        """Whether this invocation was a clean carry-in root rather than an ordinary fresh run."""
        return self.carry_in_authority_sha256 is not None


def default_live_transport_factory() -> Transport:
    """Construct the real HTTP transport. **The only live construction site in the project.**

    Decision 045 §4.2 permits exactly one operator surface to contain a live transport-construction
    path, and §6 requires it to happen at one auditable site after every in-process precondition
    and the §6A run registration have passed. This function is that site.

    ``httpx`` is imported **inside** the function on purpose: importing this module, the CLI, or
    any test therefore loads no HTTP library and opens no socket, and the no-network regression
    keeps holding by construction rather than by discipline. Every test injects a scripted
    transport in place of this factory, so nothing in the suite ever calls it.
    """
    from disclosure_drift.sec.httpx_transport import HttpxTransport  # noqa: PLC0415 - see docstring

    return HttpxTransport()


def execute_live_acquisition(  # noqa: PLR0913 - every collaborator is supplied explicitly
    *,
    plan: RequestPlan,
    window: str,
    approved_ceiling: int,
    authorization: LiveOperationAuthorization,
    gate: LiveOperatorGate,
    catalog: CatalogPreparation,
    storage: StorageBinding,
    user_agent: str,
    requests_per_second: float,
    burst: int,
    policy: RetrievalPolicy,
    continuation: ContinuationProposal | None = None,
    carry_in: CarryInAuthority | None = None,
    transport_factory: Callable[[], Transport] = default_live_transport_factory,
    run_id_factory: Callable[[], str] = default_run_id_factory,
    clock: Callable[[], str] = _utc_now,
    progress: Callable[[RequestOutcome], None] | None = None,
    sleeper: Callable[[float], None] | None = None,
    rate_limiter: AggregateRateLimiter | None = None,
) -> LiveAcquisitionResult:
    """Execute one lawful live acquisition invocation, in the Decision 045 §6A.2 order.

    The ordering is the whole point, and it is enforced by control flow rather than by comment:

    1. the complete operator-boundary conjunction is re-asserted (:class:`LiveOperatorGate`);
    2. every window binding is proved - plan hash, window identity, exact ceiling equality, route
       registration and window membership, filing-body prohibition
       (:func:`verify_window_bindings`);
    3. the catalog and storage prerequisites are validated, and a resume's continuation proposal
       must be permitted and ``SAFE`` with its original ceiling preserved;
    4. exactly one invocation run identity is allocated through the injectable factory;
    5. it is durably registered in ``ops_ingestion_jobs``;
    6. the registration is verified through a genuinely fresh read-only connection;
    7. **only then** is ``transport_factory`` called.

    Every refusal above raises before step 7, so ``transport_factory`` is provably never invoked
    on any refusal path - which is exactly what the mutation campaign and the high-risk tests
    assert by counting its invocations.

    A resumed invocation registers its **own new** run identity (§6A.3) and carries predecessor
    lineage through the continuation proposal instead; it never adopts the predecessor's run ID.

    Raises:
        AcquisitionGateError: an operator-boundary, binding, or continuation condition refuses.
        AcquisitionRunError: the run identity could not be allocated, registered, or verified.
    """
    _require_live_gate(gate)
    requests = verify_window_bindings(
        plan=plan,
        window=window,
        approved_ceiling=approved_ceiling,
        authorization=authorization,
    )
    if not requests:
        message = (
            "the approved plan expands to no logical request, so there is no lawful work to "
            "execute; a live invocation with nothing to acquire refuses before execution begins"
        )
        raise AcquisitionGateError(message)
    if not catalog.chain_is_exact:
        message = (
            f"the operational catalog's migration chain ends at {catalog.migration_chain_head}, "
            f"not the accepted {FINAL_MIGRATION_VERSION}; a live invocation runs only against "
            "the accepted chain"
        )
        raise AcquisitionGateError(message)

    if carry_in is not None:
        # Re-proved adjacent to the construction site, exactly as the operator gate is, and against
        # the object this driver was handed rather than the bytes some earlier frame read. The
        # command surface validates the artifact before any durable state exists; this is what a
        # caller several frames away — one that never read an artifact at all — cannot bypass
        # (Decision 055 §6.2, §6.4). It refuses here, before the run identity is chosen, before
        # registration, and long before `transport_factory` is reachable.
        verify_carry_in_authority(
            carry_in,
            window=window,
            plan_sha256=plan.request_plan_sha256,
            approved_ceiling=approved_ceiling,
            resuming=continuation is not None,
        )
    # Re-asserted here, before the run is registered and long before the transport factory is
    # reachable, for the same reason the operator gate is: the command surface proves it too, and
    # this is what a caller several frames away cannot bypass.
    require_m3_2a_consumed_baseline(
        window, carry_in=carry_in is not None, resuming=continuation is not None
    )

    carried_forward = (
        carry_in.historical_consumed_request_count
        if carry_in is not None
        else _resume_consumption(continuation, approved_ceiling)
    )
    predecessor_receipt_id = continuation.predecessor_receipt_id if continuation else None

    # A carry-in root runs under the run identity its authority names, rather than a freshly
    # generated one: the artifact binds the authorized run, and the checkpoint burned against that
    # binding is what a later receipt and catalog cross-check reads (Decision 055 §6.2).
    census_run_id = carry_in.authorized_census_run_id if carry_in is not None else run_id_factory()
    started_at_utc = clock()
    run = register_acquisition_run(
        catalog_path=catalog.database_path,
        lock_directory=catalog.lock_directory,
        census_run_id=census_run_id,
        window=window,
        started_at_utc=started_at_utc,
        detail=(
            "approved Milestone 3.2 metadata acquisition under the owner-approved request plan; "
            "filing bodies and accession packages prohibited"
        ),
        carry_in=carry_in,
    )
    registered_stage = validate_acquisition_run(catalog.database_path, run.census_run_id)
    if registered_stage != window:
        message = (
            f"the registered acquisition run records stage {registered_stage!r} but this "
            f"invocation executes {window!r}; the registration is not this invocation's"
        )
        raise AcquisitionRunError(message)

    response_log = PhysicalResponseLog()
    ceiling = PhysicalAttemptCeiling(approved_ceiling, consumed=carried_forward or 0)
    accounting = ResponseAccounting()
    transport: RecordingTransport | None = None
    try:
        # ---- the single auditable transport-construction site ----------------------------- #
        transport = RecordingTransport(transport=transport_factory(), log=response_log)
        # ----------------------------------------------------------------------------------- #

        execution_storage = storage if continuation is None else _resumed_storage(catalog, storage)
        restriction = (
            None
            if continuation is None
            else frozenset(item.identity_label for item in continuation.remaining)
        )
        with CatalogWriter(catalog.database_path, catalog.lock_directory) as writer:
            # Bind the write-ahead attempt ledger to the same open single-writer the recorder uses,
            # so every physical send this run makes first commits a durable `started` reservation
            # at the transport seam (Decision 051 §6, §7.2). It is bound here, after the writer is
            # open and before any request is placed, and is scoped to this invocation's job. The
            # same ledger is handed to the engine so the window's consumed physical-attempt count is
            # read from the durable reservations rather than the in-memory ceiling — an interruption
            # in the pre-send window then charges no attempt that left no durable trace.
            ledger = PreSendAttemptLedger(
                writer=writer,
                job_id=run.census_run_id,
                clock=clock,
            )
            transport.ledger = ledger
            client = SecClient(
                transport,
                user_agent,
                # The shared aggregate limiter, constructed from the operator's configured rate
                # unless the caller supplies one. Injection exists so a test drives a
                # deterministic clock rather than sleeping through real rate-limit spacing; the
                # limiter is a collaborator like every other, and supplying one grants nothing.
                rate_limiter or AggregateRateLimiter(requests_per_second, burst),
                policy,
                sleeper=sleeper,
                ceiling=ceiling,
            )
            engine = AcquisitionEngine(
                plan=plan,
                window=window,
                ceiling=ceiling,
                client=client,
                storage=execution_storage,
                recorder=ObservationRecorder(writer=writer, tree=execution_storage.tree),
                clock=clock,
                progress=progress,
                run_binding=run,
                restrict_to_identities=restriction,
                response_log=response_log,
                accounting=accounting,
                ledger=ledger,
            )
            engine.preflight(authorization)
            outcome = engine.run()
    except KeyboardInterrupt:
        # The invocation was interrupted and no window was produced — either the interrupt arrived
        # before execution began at all, or the engine could not establish the interruption point
        # exactly and refused to report one. Either way no receipt exists. The run row is still
        # closed truthfully — it stopped, it did not complete — so a registered run is never left
        # indefinitely `running`, and the interrupt propagates unchanged. Nothing durable is
        # repaired, adopted, or deleted here: what the interruption left behind is preserved for
        # the accepted read-only recovery inspection to rule on.
        finish_acquisition_run(
            catalog_path=catalog.database_path,
            lock_directory=catalog.lock_directory,
            census_run_id=run.census_run_id,
            job_state="stopped",
            finished_at_utc=clock(),
            detail="interrupted before a window outcome was produced",
        )
        raise
    finally:
        if transport is not None:
            transport.close()

    completed_at_utc = clock()
    run_closed = finish_acquisition_run(
        catalog_path=catalog.database_path,
        lock_directory=catalog.lock_directory,
        census_run_id=run.census_run_id,
        job_state=acquisition_run_job_state(outcome),
        finished_at_utc=completed_at_utc,
        detail=outcome.completion_status,
    )
    return LiveAcquisitionResult(
        census_run_id=run.census_run_id,
        outcome=outcome,
        accounting=accounting,
        started_at_utc=started_at_utc,
        completed_at_utc=completed_at_utc,
        predecessor_receipt_id=predecessor_receipt_id,
        carried_forward_consumed=carried_forward,
        run_closed=run_closed,
        carry_in_authority_sha256=None if carry_in is None else carry_in.authority_sha256,
    )


def _resumed_storage(catalog: CatalogPreparation, storage: StorageBinding) -> StorageBinding:
    """Bind the resumed invocation to catalog-authoritative snapshot state.

    Decision 045 §14 requires a resume to wire the *already-accepted* continuation architecture,
    and Decision 040's T2.4-A primitive is the piece that matters here: a fresh
    :class:`SnapshotStore` that has adopted every durable observation, so an object this window
    already preserved is recognized as a predecessor rather than treated as unseen. Without it a
    resumed request could re-store what the predecessor invocation had already promoted.

    A fresh invocation deliberately does not do this: it has no predecessor to adopt, and
    reconstructing one would be reading state a first run has no business inheriting.
    """
    reconstruction = reconstruct_catalog_state(catalog_path=catalog.database_path, storage=storage)
    return replace(storage, snapshot_store=reconstruction.store)


def _require_live_gate(gate: LiveOperatorGate) -> None:
    """Re-assert the operator-boundary conjunction where the transport is about to be built.

    :class:`LiveOperatorGate` already refuses an incomplete gate at construction, so on every
    caller that constructs its own gate this restatement is observationally a no-op — removing it
    changes no outcome, and a mutation campaign will correctly report that. It is kept anyway, and
    the reason is not that it changes behaviour today: it is that the conjunction is proved *on
    this code path*, immediately before the construction site, rather than inherited from a caller
    several frames away. A future caller that passes a gate it did not construct — a cached one, a
    deserialized one, a mutated copy — is refused here instead of reaching the transport.
    """
    LiveOperatorGate(
        explicit_live=gate.explicit_live,
        network_enabled=gate.network_enabled,
        m3_acquire_enabled=gate.m3_acquire_enabled,
        sec_identity_validated=gate.sec_identity_validated,
        stage_authority_reference=gate.stage_authority_reference,
    )


def _resume_consumption(
    continuation: ContinuationProposal | None,
    approved_ceiling: int,
) -> int | None:
    """Validate a resume's continuation proposal and return the consumption it carries forward.

    Decision 045 §14. A resume starts from an exact predecessor receipt, reconstructs cumulative
    consumption conservatively, and refuses on ``UNDETERMINED``, on an unsafe inspection, on
    unresolved write-ahead state, and when the worst-case remainder does not fit - all of which
    :func:`propose_continuation` has already decided. What this adds is the ceiling invariant the
    resumed invocation must not be able to break: the proposal's approved ceiling is the operator
    ceiling exactly, and the carried-forward consumption is never reset, lowered, or discarded.

    Returns ``None`` for a fresh invocation, which starts at zero consumption.
    """
    if continuation is None:
        return None
    if not continuation.permitted:
        message = "the continuation proposal refuses this resume: " + "; ".join(
            continuation.refusal_reasons
        )
        raise AcquisitionGateError(message)
    if continuation.determination != "SAFE":
        message = (
            f"the continuation determination is {continuation.determination!r}; a resume "
            "proceeds only from a SAFE read-only inspection"
        )
        raise AcquisitionGateError(message)
    if continuation.approved_ceiling != approved_ceiling:
        message = (
            f"the continuation proposal carries approved ceiling "
            f"{continuation.approved_ceiling} but this invocation was given {approved_ceiling}; "
            "the approved ceiling is never reset, raised, or replaced across a resume"
        )
        raise AcquisitionGateError(message)
    if continuation.predecessor_receipt_id is None:
        message = (
            "a resume requires an exact predecessor receipt identity; it is never inferred from "
            "ambient state"
        )
        raise AcquisitionGateError(message)
    # Re-asserted adjacent to the construction site, exactly as the operator gate and the carry-in
    # bindings are, and for the same reason: the proposal surface proves it too, and this is what a
    # caller several frames away — one that built a proposal object directly — cannot bypass. It
    # raises here, before the run identity is chosen, before registration, and before
    # `transport_factory` is reachable, so a complete head constructs no network (Decision 064 §4).
    if continuation.inspection.head_acquisition_complete:
        message = (
            "the continuation's predecessor receipt records a completed acquisition; a successful "
            "window is never resumed, and this invocation refuses before a transport is constructed"
        )
        raise AcquisitionGateError(message)
    if not continuation.remaining:
        message = (
            "the continuation proposal leaves no remaining logical request, so this resume has "
            "nothing lawful to acquire and refuses before execution begins rather than "
            "re-requesting already-satisfied work"
        )
        raise AcquisitionGateError(message)
    consumed = continuation.accounting.cumulative_consumed
    if consumed > approved_ceiling:
        message = (
            f"cumulative consumption {consumed} already exceeds the approved ceiling "
            f"{approved_ceiling}; no further physical request may occur"
        )
        raise AcquisitionGateError(message)
    return consumed
