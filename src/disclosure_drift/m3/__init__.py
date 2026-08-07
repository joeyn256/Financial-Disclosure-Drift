"""Milestone 3 operational surfaces.

Everything in this package is offline in Milestone 3.1: it opens no socket, constructs no
transport, and reads no live SEC data. Network permission for M3.1A is ``NONE`` and for M3.1B is
``ZERO LIVE REQUESTS``.

Milestone 3.2 adds controlled acquisition. Its catalog, immutable-storage, and acquisition-engine
foundation exists in :mod:`disclosure_drift.m3.acquisition`, and it is **transport-agnostic**:
importing or constructing anything here opens no socket and builds no client. The engine executes
only over a transport a caller injects, and only after an explicit per-window authorization that
no configuration key, contract acceptance, or gate token can synthesize. Stage T2.4 adds, in the
same module, the catalog-authoritative reconstruction, deterministic reconciliation and drift
inspection, continuation-proposal, and explicit recovery-action library surfaces (Decision 040).

Stage T2.5-T2.6 (Decision 045) wires the operator surfaces to that foundation: the offline
scope, dependent-plan, reconciliation, run-scoped drift, and recovery commands; the durable M3.2
acquisition-run identity and its run-to-observation attribution; the exhaustive response-event
accounting the frozen receipt's live fields require; and the live-capable acquisition path.

Two structural properties survive that addition, and are the reason importing this package is
still safe anywhere:

* **Importing builds nothing.** The project's only live transport-construction site is
  :func:`~disclosure_drift.m3.acquisition.default_live_transport_factory`, which imports its HTTP
  library *inside the function body*. Importing this package, the CLI, or any test therefore loads
  no HTTP library and opens no socket.
* **Reaching that site requires proving everything first.**
  :func:`~disclosure_drift.m3.acquisition.execute_live_acquisition` calls the factory only after
  the complete operator-boundary conjunction, every window binding, the catalog and storage
  prerequisites, any resume's continuation proposal, and the durable acquisition-run registration
  and its fresh-connection verification have all passed. Nothing here may be treated as evidence
  that a later owner gate has been satisfied.
"""

from __future__ import annotations

from disclosure_drift.m3.acquisition import (
    ACQUISITION_JOB_KIND,
    ACQUISITION_WINDOWS,
    DEPENDENT_RECONCILIATION_SET_VERSION,
    FINAL_MIGRATION_VERSION,
    M3_2B_DEPENDENT_ROUTES,
    NO_HTTP_STATUS_SENTINEL,
    OPERATIONAL_CATALOG_RELATIVE_PATH,
    PROGRESS_SINK_FAILURE_REASON,
    RECOVERY_ACTIONS,
    AcquisitionEngine,
    AcquisitionError,
    AcquisitionGateError,
    AcquisitionRunBinding,
    AcquisitionRunError,
    CatalogPreparation,
    CatalogPreparationError,
    CatalogReconstruction,
    ContainmentError,
    ContinuationProposal,
    ContinuationRequest,
    CumulativeAttemptAccounting,
    DependentPlanDerivation,
    DependentPlanError,
    DriftListingEntry,
    LiveAcquisitionResult,
    LiveOperationAuthorization,
    LiveOperatorGate,
    LogicalRequest,
    PhysicalResponseLog,
    ReconciliationItem,
    RecordingTransport,
    RecoveryActionResult,
    RecoveryObservation,
    RepairRefusedError,
    RequestOutcome,
    RequestReconciliation,
    ResponseAccounting,
    RunScopedDrift,
    StorageBinding,
    StoragePreparationError,
    StoreFinding,
    WindowOutcome,
    apply_recovery_action,
    conditional_validators,
    default_live_transport_factory,
    default_run_id_factory,
    derive_dependent_plan,
    derive_logical_requests,
    drift_for_run,
    execute_live_acquisition,
    observe_recovery_state,
    prepare_operational_catalog,
    prepare_storage,
    propose_continuation,
    reconcile_requests,
    reconstruct_catalog_state,
    register_acquisition_run,
    resolve_within,
    validate_acquisition_run,
    verified_reusable_predecessor,
    verify_window_bindings,
)

__all__: list[str] = [
    "ACQUISITION_JOB_KIND",
    "ACQUISITION_WINDOWS",
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
    "observe_recovery_state",
    "prepare_operational_catalog",
    "prepare_storage",
    "propose_continuation",
    "reconcile_requests",
    "reconstruct_catalog_state",
    "register_acquisition_run",
    "resolve_within",
    "validate_acquisition_run",
    "verified_reusable_predecessor",
    "verify_window_bindings",
]
