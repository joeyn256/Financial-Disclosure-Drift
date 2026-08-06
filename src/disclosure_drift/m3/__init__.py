"""Milestone 3 operational surfaces.

Everything in this package is offline in Milestone 3.1: it opens no socket, constructs no
transport, and reads no live SEC data. Network permission for M3.1A is ``NONE`` and for M3.1B is
``ZERO LIVE REQUESTS``.

Milestone 3.2 adds controlled acquisition. Its catalog, immutable-storage, and acquisition-engine
foundation exists in :mod:`disclosure_drift.m3.acquisition`, and it is **transport-agnostic**:
importing or constructing anything here opens no socket and builds no client. The engine executes
only over a transport a caller injects, and only after an explicit per-window authorization that
no configuration key, contract acceptance, or gate token can synthesize. The operator command
surfaces remain refused, network permission remains ``NONE``, and nothing here may be treated as
evidence that a later gate has been satisfied.
"""

from __future__ import annotations

from disclosure_drift.m3.acquisition import (
    ACQUISITION_WINDOWS,
    FINAL_MIGRATION_VERSION,
    OPERATIONAL_CATALOG_RELATIVE_PATH,
    AcquisitionEngine,
    AcquisitionError,
    AcquisitionGateError,
    CatalogPreparation,
    CatalogPreparationError,
    ContainmentError,
    LiveOperationAuthorization,
    LogicalRequest,
    RecoveryObservation,
    RequestOutcome,
    StorageBinding,
    StoragePreparationError,
    WindowOutcome,
    derive_logical_requests,
    observe_recovery_state,
    prepare_operational_catalog,
    prepare_storage,
    resolve_within,
)

__all__: list[str] = [
    "ACQUISITION_WINDOWS",
    "FINAL_MIGRATION_VERSION",
    "OPERATIONAL_CATALOG_RELATIVE_PATH",
    "AcquisitionEngine",
    "AcquisitionError",
    "AcquisitionGateError",
    "CatalogPreparation",
    "CatalogPreparationError",
    "ContainmentError",
    "LiveOperationAuthorization",
    "LogicalRequest",
    "RecoveryObservation",
    "RequestOutcome",
    "StorageBinding",
    "StoragePreparationError",
    "WindowOutcome",
    "derive_logical_requests",
    "observe_recovery_state",
    "prepare_operational_catalog",
    "prepare_storage",
    "resolve_within",
]
