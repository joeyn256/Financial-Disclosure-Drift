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
inspection, continuation-proposal, and explicit recovery-action library surfaces (Decision 040) —
all read-only except the recovery applier, which mutates only when explicitly invoked with one
action, and none of which is wired to any operator command. The operator command surfaces remain
refused, network permission remains ``NONE``, and nothing here may be treated as evidence that a
later gate has been satisfied.
"""

from __future__ import annotations

from disclosure_drift.m3.acquisition import (
    ACQUISITION_WINDOWS,
    FINAL_MIGRATION_VERSION,
    OPERATIONAL_CATALOG_RELATIVE_PATH,
    RECOVERY_ACTIONS,
    AcquisitionEngine,
    AcquisitionError,
    AcquisitionGateError,
    CatalogPreparation,
    CatalogPreparationError,
    CatalogReconstruction,
    ContainmentError,
    ContinuationProposal,
    ContinuationRequest,
    CumulativeAttemptAccounting,
    DriftListingEntry,
    LiveOperationAuthorization,
    LogicalRequest,
    ReconciliationItem,
    RecoveryActionResult,
    RecoveryObservation,
    RepairRefusedError,
    RequestOutcome,
    RequestReconciliation,
    StorageBinding,
    StoragePreparationError,
    StoreFinding,
    WindowOutcome,
    apply_recovery_action,
    conditional_validators,
    derive_logical_requests,
    observe_recovery_state,
    prepare_operational_catalog,
    prepare_storage,
    propose_continuation,
    reconcile_requests,
    reconstruct_catalog_state,
    resolve_within,
    verified_reusable_predecessor,
)

__all__: list[str] = [
    "ACQUISITION_WINDOWS",
    "FINAL_MIGRATION_VERSION",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "RECOVERY_ACTIONS",
    "AcquisitionEngine",
    "AcquisitionError",
    "AcquisitionGateError",
    "CatalogPreparation",
    "CatalogPreparationError",
    "CatalogReconstruction",
    "ContainmentError",
    "ContinuationProposal",
    "ContinuationRequest",
    "CumulativeAttemptAccounting",
    "DriftListingEntry",
    "LiveOperationAuthorization",
    "LogicalRequest",
    "ReconciliationItem",
    "RecoveryActionResult",
    "RecoveryObservation",
    "RepairRefusedError",
    "RequestOutcome",
    "RequestReconciliation",
    "StorageBinding",
    "StoragePreparationError",
    "StoreFinding",
    "WindowOutcome",
    "apply_recovery_action",
    "conditional_validators",
    "derive_logical_requests",
    "observe_recovery_state",
    "prepare_operational_catalog",
    "prepare_storage",
    "propose_continuation",
    "reconcile_requests",
    "reconstruct_catalog_state",
    "resolve_within",
    "verified_reusable_predecessor",
]
