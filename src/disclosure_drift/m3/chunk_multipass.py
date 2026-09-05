"""Semantically exact two-level consolidation of a >9-chunk F0 -- D151-C13.

**The counterexample this module exists to survive.** The single-pass consolidator upgrades every
later chunk's local-first witness of an accession to a rival of the source's true first witness,
and back-fills the true first witness's omitted observations. D151-C8 falsified the belief that
this correction composes naively across two levels: a chunk's local-first witness that WINS
within its level-1 group is treated there as a first witness -- so, for a payload whose
non-membership governed fields are inert, it materializes nothing but what fails to round-trip --
and then LOSES globally at level 2 to an earlier group's witness, where the accepted rival rule
requires every governed field it observed. Five observation rows are missing from a naive merge
of intermediates. Level 2 therefore performs an **additive global loser upgrade**
(:func:`stage_first_witness_corrections`): every level-1 group winner that is not the global
winner is re-materialized as a rival from its own retained ``payload_json`` through the accepted
:func:`~disclosure_drift.m3.compact_evidence.materialized_fields`, and the global winner's
canonical row is back-filled through the accepted
:func:`~disclosure_drift.m3.compact_evidence.reconstructed_observations`. The identifiers are the
accepted content-derived ones and the load is the accepted ``INSERT OR IGNORE`` under the accepted
priority ordering, so the upgrade is purely additive and idempotent.

**The correction is set-based at both levels.** The single-pass consolidator's Python
row-at-a-time correction loop (D151-C8 M2) is not on this path. Contested accessions are ranked by
one window function, the winner back-fill and the loser upgrade are each ONE ``INSERT ... SELECT``
over that ranking joined to the loaded canonical rows and payloads, and the accepted rendering and
identity functions are reached as deterministic SQLite user functions inside those statements --
called, never restated. The statement count is a constant; the row count is the contested
population.

**Exactly two levels, region-homogeneous, derived from the sealed plan.** A multipass plan of ten
to thirty-four chunks groups contiguously in canonical plan order into level-1 groups of at most
:data:`MERGE_FAN_IN` chunks, and a group holds primary chunks or shard chunks, never both -- which
keeps the accepted primary-before-shard barrier mechanical and leaves level 2 at most five inputs.
The grouping is a pure function of the plan, sealed into :attr:`MergeSchedule.schedule_digest`,
and every intermediate binds that digest: a caller cannot supply a grouping.

**An intermediate is a first-class artifact and not a world.** It is create-once, manifested and
authenticated, it retains every input's rows and the reduced first-witness ledger level 2 needs,
and it writes no F0 terminal, no final receipt and no source parser state. Only level 2 creates
the canonical world, and it does so at the accepted finalization boundary: merge complete, then
semantic reconstruction, then compact evidence, then the accepted D140-R12
:func:`~disclosure_drift.m3.single_source_canary.require_f0_success`, then the durable terminal.
The final receipt is the accepted
:class:`~disclosure_drift.m3.chunk_consolidation.FinalWorldReceipt` contract; a multipass world
differs from a single-pass world in how it was built, not in what it is.

**Every merge primitive is the accepted single-pass one, imported.** The sorted bulk loads, the
first/last reductions, the observation load, the parser-run reduction, the member-delta
correction, the sidecar merge with its completeness-digest replay, the accepted plan state and
the derived F0 outcome and payload all come from :mod:`~disclosure_drift.m3.chunk_consolidation`.
Nothing here is a second expression of a merge rule.

**Authority is load-bearing, and it is the first gate on every world-creating path -- D151-C15
R2.** :func:`require_real_multipass_authority` is the first statement of the orchestrator, of both
launchers, of both merge bodies and of the child entry point -- ahead of every request document,
directory, child process, storage-plan record, intermediate and final world. While
:data:`REAL_MULTIPASS_F0_AUTHORITY` is ``None`` each of them refuses before its first filesystem
mutation, and a hand-written child request refuses inside the child. Authority is necessary and
not sufficient: **storage admission is the last gate.** Before a level-1 world or the final
world is created, the step's projected peak plus the governed reserve plus **that level's own**
transient allowance must be free on the internal tier (:mod:`~disclosure_drift.m3.chunk_tiering`).
Every owner term is ``None`` and ``None`` refuses, so an open authority alone admits nothing, and
no parameter of any production entry substitutes for the owner terms. No input is deleted, spilled
or reclaimed by anything here, and no command-line surface reaches this module.

**Between them, the SQLite temporary placement is proved -- D151-C17 R6.** Storage admission
charges free bytes on the filesystem that will host the world; SQLite spills its whole-plan
sorters and workfiles wherever ``SQLITE_TMPDIR`` points, and silently onto the internal volume
when it points nowhere. :func:`~disclosure_drift.m3.chunk_tiering.require_sqlite_temp_binding`
therefore measures both volume identities through the accepted D137-R8 provider and refuses a
mismatch before any world, attempt directory or database exists. The orchestrator proves it, and
then **each merge child proves it again for itself**: a child that accepted the parent's word, or
a field in its request, would be trusting a claim it had not measured. That variable is read by
:mod:`~disclosure_drift.m3.chunk_tiering` alone, from the environment SQLite itself consumes;
THIS module reads no environment at all, and no environment-derived configuration capability
exists on this path beyond the two exact owner-approved ``SQLITE_TMPDIR`` reads -- that one, and
the accepted D137-R8 guard's own: the committed audit
(``tests/unit/test_d151_c13_intermediates.py``, D151-C21 R2) holds every module on the path to a
finite, enumerated route taxonomy -- ``os.environ`` and its imported, aliased, subscripted and
reflective spellings, ``os.path`` and ``pathlib`` expansion, ``tempfile``, ``getpass``,
``shutil.which``, ``ctypes``, ``sys.modules``/``importlib``/``__import__`` indirection and
environment-printing subprocesses -- and that finite property is what is claimed, not a proof
against every conceivable side channel. No command-line control reaches this module. Its
presence alone is never the proof -- the volume identity is.

**The measured binding is durable and remeasured -- D151-C19 R4.** The orchestrator's measured
:class:`~disclosure_drift.m3.chunk_tiering.SqliteTempBinding` is folded into the sealed storage
plan (contract ``/2``, written once with the identity that seals it) and handed to every merge
child as the topology the consolidation was admitted on. The child never trusts it: it measures
its own binding first, and then requires the two to agree field for field before any world,
attempt directory or database exists. A changed ``SQLITE_TMPDIR``, a changed volume, or a forged
or pre-C19 binding record refuses.

**One seal, one restart comparison -- D151-C21 R4.** The recorded document is verified whole --
its exact serialized shape and its full ``storage_plan_identity``, attachment-instance fields
included -- and only then is it compared with the freshly computed plan by
:meth:`~disclosure_drift.m3.chunk_tiering.MultipassStoragePlan.restart_compatibility`, which
omits exactly the binding's attach-time identifiers (``st_dev`` and ``diskNsM``). The same
volume re-attached under a different disk number therefore continues; a changed volume UUID,
filesystem type or temporary-root inode refuses; and the document is never rewritten. Every child
is handed the binding its parent measured NOW, not the recorded one, and compares all eight fields
against its own measurement.

**The two transient allowances are separate -- D151-C17 R5.** Level 2 materializes whole-plan
temporary state that no level-1 group does, so
:data:`~disclosure_drift.m3.chunk_tiering.MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES` and
:data:`~disclosure_drift.m3.chunk_tiering.MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES` are independent
owner terms, each refusing on its own, with no fallback in either direction. Each storage step
records which level it was charged at, so a sealed plan cannot be re-read as if the other
allowance had applied.

**The final receipt's four correction counters are whole-F0 -- D151-C15 R1.** The accepted
single-pass receipt reports the cross-chunk first-witness correction its consolidation applied over
its plan's chunks. The multipass receipt reports exactly that quantity over ITS plan's chunks,
derived at level 2 from the retained, authenticated chunk artifacts by the accepted definition
(:func:`_plan_first_witness_counters`) -- never the stage counts of either level, and never their
sum -- so the value is a function of the sealed plan and not of the level-1 grouping.

**The dependency-closed calibration route is separate, envelope-gated and noncanonical --
D151-C27R1.** Every production entry above keeps its authority-first gate and its exact bootstrap
byte for byte, and refuses a calibration-subset plan. The calibration route -- one launch shape
for the chunk, group and final roles, its own bootstrap, its own bodies -- is gated by the
pipe-delivered :class:`~disclosure_drift.m3.chunk_execution.CalibrationChildEnvelope` instead,
runs the same accepted merge primitives, and ends in a calibration-subset result rather than a
canonical terminal: no parser state, no ``parsed`` mark, no F0 checkpoint, no final receipt. Each
merge child emits its own admission event -- level, transient allowance and arithmetic in its own
words -- into the ledger its envelope names, after validation and before its world exists.

**The calibration route is retention-aware -- D151-C29R1.** A calibration level-1 group resolves
and verifies only ITS scheduled chunks (:func:`~disclosure_drift.m3.chunk_consolidation.
resolve_contiguous_chunk_inputs`), so no other group's bulky chunk world is required or opened.
After a chunk's terminal authenticates, the orchestrator writes its **retained witness**
(:data:`CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT`): the exact two-table projection the
whole-F0 counters are derived from, a primary chunk's declarations copy, and a sealed record
binding the chunk receipt, its manifest, the plan, the schedule and the source. After the
group's intermediate authenticates, a create-once **group checkpoint** binds chunk receipt,
witness and intermediate, and only then -- and only under an explicit
:class:`CalibrationDeletionGrant` naming the group -- are that group's chunk worlds
exact-deleted through the accepted exact-entry primitive, never a tree removal, with a
create-once deletion record written after every source is absent. The calibration final then
consumes the five intermediates, every retained witness and every checkpoint, and derives the
four whole-F0 counters by :func:`_plan_first_witness_counters` over the witnesses under the
SAME statements it runs over chunk worlds. Every production entry, body, launcher, bootstrap
and authority gate above is untouched; the production reclaim authority stays ``None`` and no
calibration deletion is, or can confer, a production reclaim.

**The durable Level-Two stage spine is a separate, successor-only route -- D151-C31R2-R19A-C2.**
The accepted finalizers above run one transaction over the whole merge; the failed C31R2 final
proved that shape cannot be checkpointed, resumed or attributed. The successor route at the end
of this module -- :func:`run_successor_multipass_final` (production, authority first) and
:func:`run_successor_calibration_final` (calibration, sealed plan first) -- runs the same
accepted merge primitives as one transaction PER STAGE, commits each stage's applied-unit row
with its semantic writes, issues an exact ``PRAGMA main.wal_checkpoint(TRUNCATE)`` and publishes
an immutable receipt, so a restart classifies committed evidence rather than guessing. Its six
persistent ``m3_l2_*`` relations replace the legacy TEMP ones on that route only; every legacy
body, gate, bootstrap and TEMP relation above is byte for byte what it was.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
import subprocess
import sys
import time
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Final, NoReturn, Protocol, cast

import disclosure_drift.errors as _errors_module
import disclosure_drift.m3.canary_phases as _canary_phases_module
import disclosure_drift.m3.canary_runtime as _canary_runtime_module
import disclosure_drift.m3.chunk_consolidation as _chunk_consolidation_module
import disclosure_drift.m3.chunk_evidence as _chunk_evidence_module
import disclosure_drift.m3.chunk_execution as _chunk_execution_module
import disclosure_drift.m3.chunk_plan as _chunk_plan_module
import disclosure_drift.m3.chunk_storage as _chunk_storage_module
import disclosure_drift.m3.chunk_tiering as _chunk_tiering_module
import disclosure_drift.m3.compact_evidence as _compact_evidence_module
import disclosure_drift.m3.offline_parse as _offline_parse_module
import disclosure_drift.m3.repository_identity as _repository_identity_module
import disclosure_drift.m3.single_source_canary as _single_source_canary_module
import disclosure_drift.m3.working_catalog as _working_catalog_module
import disclosure_drift.sec.census as _census_module
import disclosure_drift.storage.catalog as _storage_catalog_module
import disclosure_drift.storage.sqlite as _storage_sqlite_module
from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_phases import (
    PHASE_F0,
    PHASE_RESTART_CONTRACT,
    PHASE_STATUS_COMPLETE,
    PhaseCheckpoint,
    read_phase_checkpoint,
    write_phase_checkpoint,
)
from disclosure_drift.m3.canary_runtime import free_bytes, process_peak_resident_bytes

# The accepted single-pass merge primitives, imported rather than restated. They are private to
# the consolidator's module because the single-pass consolidator is their only OTHER caller; a
# second expression of any of them here would be a second answer waiting to disagree.
from disclosure_drift.m3.chunk_consolidation import (
    _LOAD_ORDER,
    _MERGE_STRATEGY,
    CORRECTIONS_TABLE,
    DUPLICATE_IDENTITY_UPDATE_SQL,
    MEMBER_DELTA_SUMMARY_SQL,
    REDUCED_PARSER_RUN_INSERT_SQL,
    SIDECAR_DIGEST_REPLAY_SQL,
    SIDECAR_MEMBER_SUMMARY_SQL,
    STATEMENT_KIND_EXECUTE,
    STATEMENT_KIND_FETCHALL,
    STATEMENT_KIND_ITERATE,
    ChunkInput,
    FinalWorldReceipt,
    _accepted_plan_state,
    _AcceptedPlanState,
    _apply_duplicate_identities,
    _attach_all,
    _columns,
    _deferrable_index_records,
    _deferrable_indexes,
    _detach_all,
    _keyed_first_last_load,
    _load_accession_observations,
    _member_deltas,
    _merge_sidecar,
    _nearest_existing,
    _reduced_parser_run,
    _ReducedRun,
    _sorted_bulk_load,
    _union_all,
    derived_f0_outcome,
    derived_f0_payload,
    require_attachable,
    resolve_chunk_inputs,
    resolve_contiguous_chunk_inputs,
)
from disclosure_drift.m3.chunk_evidence import (
    CHUNK_DECLARATIONS_FILENAME,
    CHUNK_PLAN_FILENAME,
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    PARENT_MAP_FILENAME,
    ArtifactEntry,
    ArtifactManifest,
    ChunkEvidenceError,
    ChunkReceipt,
    ExecutionContract,
    build_artifact_manifest,
    file_sha256,
    read_receipt_document,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.chunk_execution import (
    _WITNESS_SCHEMA,
    CALIBRATION_ROLE_CHUNK,
    CALIBRATION_ROLE_FINAL,
    CALIBRATION_ROLE_GROUP,
    F0_WRITTEN_TABLES,
    CalibrationChildEnvelope,
    ChunkExecutionError,
    ChunkRequest,
    _read_json_object,
    _require_process_dead,
    completed_chunk_receipt,
    delivered_calibration_envelope,
    execute_calibration_subset_chunk_body,
    issue_calibration_envelope,
    measured_calibration_binding,
    merge_parent_map,
    next_attempt_directory,
    read_declarations,
    receive_calibration_envelope,
    require_calibration_envelope,
    require_envelope_binding,
    require_envelope_request,
    table_row_counts,
    write_once_canonical_json,
)
from disclosure_drift.m3.chunk_plan import (
    CALIBRATION_SUBSET_CLASSIFICATIONS,
    CHUNK_REGION_ORDER,
    MULTIPASS_PLAN_CONTRACT,
    REGION_PRIMARY,
    REGION_SHARD,
    SINGLE_PASS_CHUNK_CAP,
    CalibrationSubsetPlan,
    ChunkBounds,
    ChunkPlan,
    ChunkPlanError,
    canonical_json_bytes,
    chunk_by_id,
    require_calibration_subset_plan,
    require_chunkable_source,
    require_sealed_plan,
)
from disclosure_drift.m3.chunk_storage import (
    authoritative_input,
    derive_chunk_placement,
    internal_free_bytes,
)
from disclosure_drift.m3.chunk_tiering import (
    MERGE_LEVEL_ONE,
    MERGE_LEVEL_TWO,
    MERGE_LEVELS,
    MergeAdmission,
    MultipassStoragePlan,
    MultipassStorageRequirements,
    SqliteTempBinding,
    accepted_multipass_storage_requirements,
    merge_step_requirement,
    plan_multipass_storage,
    require_merge_admission,
    require_sqlite_temp_binding,
)
from disclosure_drift.m3.chunk_transfer import (
    ChunkTransferError,
    InstrumentationLedger,
    _remove_exact_entries,
    _walk_files,
)
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    IDENTITY_FOLD_STATEMENTS,
    MEMBER_MANIFEST_ROWS_SQL,
    CompactEvidenceSidecar,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.m3.offline_parse import SingleSourceOutcome, write_containment
from disclosure_drift.m3.repository_identity import (
    RepositoryIdentity,
    require_clean_running_repository,
)
from disclosure_drift.m3.single_source_canary import (
    phase_execution_identity,
    require_f0_success,
)
from disclosure_drift.m3.working_catalog import (
    EVENT_STATEMENT_END,
    EVENT_STATEMENT_ERROR,
    EVENT_STATEMENT_SAMPLE,
    EVENT_STATEMENT_START,
    EVENT_WATCHDOG_ABORT,
    JOURNAL_AUTHENTIC,
    JOURNAL_MISSING,
    PROGRESS_LEDGER_FILENAME,
    WAL_FRAME_HEADER_BYTES,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
    SourceProgress,
    StatementJournalWriter,
    WalObservation,
    WorkingCatalog,
    WorkingCatalogError,
    authenticate_statement_journal,
    cache_size_pragma,
    checkpoint_main_truncate,
    file_digest,
    normalized_wal_bytes,
    observe_wal,
    promote_world_directory,
    require_sqlite_page_size,
    wal_index_committed_frames,
)
from disclosure_drift.sec.census import CensusCatalog, _stable_id
from disclosure_drift.sec.census import _json as _stable_json
from disclosure_drift.storage.sqlite import connect, transaction, utc_now

__all__ = [
    "CALIBRATION_ADMISSION_EVENT_KIND",
    "CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT",
    "CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND",
    "CALIBRATION_GROUP_DELETION_EVENT_KIND",
    "CALIBRATION_RETAINED_PAYLOAD_FILENAME",
    "CALIBRATION_RETAINED_WITNESS_FILENAME",
    "CALIBRATION_SUBSET_RESULT_CONTRACT",
    "CALIBRATION_SUBSET_RESULT_FILENAME",
    "DEFAULT_SYNTHETIC_CACHE_BYTES",
    "EXPECTED_DEFERRED_INDEX_NAMES",
    "GOVERNED_INTERMEDIATE_MANIFEST_NAMES",
    "INTERMEDIATE_RECEIPT_CONTRACT",
    "INTERMEDIATE_RECEIPT_FILENAME",
    "INTERMEDIATE_WITNESS_FILENAME",
    "L2_APPLIED_UNIT_CONTRACT",
    "L2_APPLIED_UNITS_TABLE",
    "L2_CONNECTION_STATE_CONTRACT",
    "L2_CONTROL_TABLES",
    "L2_CROSS_STORE_BINDING_CONTRACT",
    "L2_CROSS_STORE_BINDINGS_TABLE",
    "L2_DEFERRED_INDEX_SET_CONTRACT",
    "L2_DEFERRED_INDEXES_TABLE",
    "L2_PERSISTENT_RELATIONS",
    "L2_STAGE_ADMISSION_CONTRACT",
    "L2_STAGE_PLAN_CONTRACT",
    "L2_STAGE_PLAN_TABLE",
    "L2_STAGE_RECEIPT_CONTRACT",
    "MERGE_FAN_IN",
    "MERGE_SCHEDULE_CONTRACT",
    "MERGE_SCHEDULE_FILENAME",
    "MULTIPASS_CONSOLIDATION_CONTRACT",
    "MULTIPASS_REQUEST_KIND_FINAL",
    "MULTIPASS_REQUEST_KIND_GROUP",
    "REAL_MULTIPASS_F0_AUTHORITY",
    "STORAGE_PLAN_FILENAME",
    "SUCCESSOR_REQUEST_KIND_FINAL",
    "SUCCESSOR_ROUTE_CALIBRATION",
    "SUCCESSOR_ROUTE_PRODUCTION",
    "SUCCESSOR_ROUTES",
    "L2_APPLIED_UNIT_CONTRACT_V2",
    "L2_OBSERVABILITY_CLOSEOUT_CONTRACT",
    "L2_STAGE_PLAN_CONTRACT_V2",
    "L2_STAGE_RECEIPT_CONTRACT_V2",
    "L2_STATEMENT_EVENT_CONTRACT",
    "L2_STATEMENT_EXECUTION_SET_CONTRACT",
    "L2_STATEMENT_JOURNAL_CONTRACT",
    "L2_STATEMENT_REGISTRY_CONTRACT",
    "L2_TOOL_MANIFEST_CONTRACT",
    "STATEMENT_PROGRESS_DIRECTORY",
    "AppliedUnit",
    "CalibrationAdmissionEvent",
    "CalibrationChunkExecution",
    "CalibrationChunkWitness",
    "CalibrationDeletionGrant",
    "CalibrationGroupCheckpoint",
    "CalibrationGroupDeletion",
    "CalibrationSubsetMultipassResult",
    "CalibrationSubsetResult",
    "ChunkMultipassError",
    "FinalMergeRequest",
    "GroupMergeRequest",
    "GroupRequestProvenance",
    "IntermediateInput",
    "IntermediateReceipt",
    "L2Stage",
    "L2StagePlan",
    "MergeGroup",
    "MergeSchedule",
    "MultipassResult",
    "PlanWitnessSource",
    "RetainedWitnessInput",
    "SuccessorConnectionState",
    "SuccessorFinalRequest",
    "StatementObservabilityTerms",
    "SuccessorRunOutcome",
    "ToolManifest",
    "calibration_admission_event_path",
    "calibration_group_checkpoint_path",
    "calibration_group_deletion_path",
    "calibration_retained_root",
    "calibration_witness_attempt_directory",
    "completed_calibration_chunk_witness",
    "completed_intermediate_receipt",
    "delete_calibration_group_chunk_worlds",
    "derive_calibration_subset_schedule",
    "derive_merge_schedule",
    "finalize_calibration_subset_body",
    "finalize_multipass_body",
    "group_by_id",
    "group_chunks",
    "intermediate_attempt_directory",
    "merge_calibration_subset_group_body",
    "merge_group_body",
    "next_calibration_witness_attempt_directory",
    "next_intermediate_attempt_directory",
    "read_calibration_admission_event",
    "read_calibration_chunk_witness",
    "read_calibration_group_checkpoint",
    "read_calibration_group_deletion",
    "read_calibration_subset_result",
    "read_observability_closeout",
    "read_stage_receipt",
    "require_executable_level_two_cache_bytes",
    "require_multipass_plan",
    "require_r21_observability_ready",
    "require_statement_observability_terms",
    "require_real_multipass_authority",
    "require_sealed_schedule",
    "require_successor_cache_bytes",
    "resolve_calibration_chunk_witnesses",
    "resolve_calibration_group_checkpoints",
    "resolve_intermediate_inputs",
    "run_calibration_subset_chunk",
    "run_calibration_subset_chunks",
    "run_calibration_subset_final_merge",
    "run_calibration_subset_group_merge",
    "run_calibration_subset_multipass",
    "run_final_merge",
    "run_group_merge",
    "run_multipass_f0",
    "run_successor_calibration_final",
    "run_successor_multipass_final",
    "select_group_inputs",
    "stable_binding_identity",
    "stage_first_witness_corrections",
    "stage_receipt_path",
    "successor_stage_graph",
    "successor_statement_registry",
    "write_calibration_chunk_witness",
    "write_calibration_group_checkpoint",
]


class ChunkMultipassError(DisclosureDriftError):
    """A multipass-consolidation precondition failed. Never repaired, never partially applied."""


#: The merge schedule's own contract identity, folded into every schedule digest.
MERGE_SCHEDULE_CONTRACT: Final = "m3.3-chunked-f0-merge-schedule/1"

#: The level-1 intermediate receipt's contract identity -- D151-C13 §8.
INTERMEDIATE_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-intermediate-receipt/1"

#: The multipass consolidator's own contract identity, recorded on the final receipt beside the
#: accepted final-receipt contract so a reader can tell HOW the world was built.
MULTIPASS_CONSOLIDATION_CONTRACT: Final = "m3.3-chunked-f0-multipass-consolidation/1"

#: The intermediate receipt's fixed filename. Written LAST, inside the intermediate attempt.
INTERMEDIATE_RECEIPT_FILENAME: Final = "intermediate_receipt.json"

#: The reduced first-witness ledger an intermediate carries for level 2.
INTERMEDIATE_WITNESS_FILENAME: Final = "intermediate_witness.sqlite3"

#: The sealed merge schedule's copy, carried by every intermediate and by the multipass root.
MERGE_SCHEDULE_FILENAME: Final = "merge_schedule.json"

#: The deterministic storage plan's copy at the multipass root.
STORAGE_PLAN_FILENAME: Final = "storage_plan.json"

#: The maximum inputs one merge operation attaches at once: exactly the single-pass cap.
MERGE_FAN_IN: Final = SINGLE_PASS_CHUNK_CAP

#: The governed token authorizing one **real** multipass consolidation. ``None`` -- D151-C13
#: §40, made load-bearing by D151-C15 R2. :func:`require_real_multipass_authority` reads it and is
#: the FIRST statement of every entry that can create a request document, an attempt directory,
#: a child process, an intermediate or a final world: :func:`run_multipass_f0`,
#: :func:`run_group_merge`, :func:`run_final_merge`, :func:`merge_group_body`,
#: :func:`finalize_multipass_body` and the child entry point. The closure is also structural --
#: no command-line surface reaches this module, no environment variable or configuration key is
#: read, and the storage terms a real consolidation would need are ``None`` as well -- but this
#: constant is what every world-creating path refuses on first. A later owner instrument replaces
#: only this literal, in a reviewed change; it opens the authority gate and nothing else.
REAL_MULTIPASS_F0_AUTHORITY: Final[str | None] = None

MULTIPASS_REQUEST_KIND_GROUP: Final = "group"
MULTIPASS_REQUEST_KIND_FINAL: Final = "final"

_DIRECTORY_MODE: Final = 0o700
_INTERMEDIATES_DIRECTORY: Final = "intermediates"
_FINAL_DIRECTORY: Final = "final"

#: The bootstrap the merge child runs. Deliberately not a console script or a subcommand.
_CHILD_BOOTSTRAP: Final = (
    "import sys;"
    "from disclosure_drift.m3.chunk_multipass import _child_main;"
    "sys.exit(_child_main(sys.argv[1]))"
)


def require_real_multipass_authority() -> str:
    """The token authorizing one real multipass consolidation, or a refusal -- D151-C13 §40.

    Raises:
        ChunkMultipassError: :data:`REAL_MULTIPASS_F0_AUTHORITY` is ``None``.
    """
    granted = REAL_MULTIPASS_F0_AUTHORITY
    if granted is None:
        message = (
            "real multipass F0 consolidation is NOT AUTHORIZED: REAL_MULTIPASS_F0_AUTHORITY is "
            "None. D151-C13 engineers and falsifies the two-level architecture and authorizes no "
            "run of it; no command-line surface, environment variable, configuration key, plan, "
            "receipt or passing test substitutes for this constant"
        )
        raise ChunkMultipassError(message)
    return granted


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ChunkMultipassError(message)


# --------------------------------------------------------------------------- #
# The plan gate
# --------------------------------------------------------------------------- #
def require_multipass_plan(plan: ChunkPlan) -> ChunkPlan:
    """Refuse, before anything is read, a plan the multipass consolidator may not consume.

    The plan must be exactly its sealed self -- the digest recomputed and every coverage rule
    re-derived through :func:`~disclosure_drift.m3.chunk_plan.require_sealed_plan` -- and it must
    be sealed under :data:`~disclosure_drift.m3.chunk_plan.MULTIPASS_PLAN_CONTRACT`. An ordinary
    plan belongs to the single-pass consolidator; a calibration-only plan's chunks are noncanonical
    evidence and no world is ever assembled from them; an unknown contract was already refused by
    the plan module. The contract is inside the digest, so a relabelled record cannot reach here.

    Raises:
        ChunkPlanError: the plan is not its sealed self.
        ChunkMultipassError: the plan is not a multipass plan.
    """
    require_sealed_plan(plan)
    if plan.contract != MULTIPASS_PLAN_CONTRACT:
        message = (
            f"a plan sealed under contract {plan.contract!r} is never consolidated by the "
            f"multipass consolidator, which consumes only {MULTIPASS_PLAN_CONTRACT!r}. An "
            "ordinary plan is the single-pass consolidator's; a calibration-only plan exists to "
            "execute and measure one chunk, its chunks are noncanonical evidence and no world "
            "is ever assembled from them. Nothing was read, listed or created"
        )
        raise ChunkMultipassError(message)
    return plan


# --------------------------------------------------------------------------- #
# The merge schedule -- D151-C13 §§6, 7
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class MergeGroup:
    """One level-1 merge: a contiguous, region-homogeneous run of chunks in canonical order."""

    group_id: str
    ordinal: int
    region: str
    chunk_ids: tuple[str, ...]
    plan_ordinals: tuple[int, ...]
    start: int
    end: int

    @property
    def member_count(self) -> int:
        """How many governed members this group's intermediate covers."""
        return self.end - self.start

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "group_id": self.group_id,
            "ordinal": self.ordinal,
            "region": self.region,
            "chunk_ids": list(self.chunk_ids),
            "plan_ordinals": list(self.plan_ordinals),
            "start": self.start,
            "end": self.end,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> MergeGroup:
        """Rebuild one group from its stored mapping.

        Raises:
            ChunkMultipassError: a field is absent or is not of the recorded type.
        """
        try:
            chunk_ids = record["chunk_ids"]
            plan_ordinals = record["plan_ordinals"]
            if not isinstance(chunk_ids, list) or not isinstance(plan_ordinals, list):
                message = "a merge group's chunk_ids and plan_ordinals must be lists; refused"
                raise ChunkMultipassError(message)
            return cls(
                group_id=str(record["group_id"]),
                ordinal=_stored_int(record["ordinal"], "ordinal"),
                region=str(record["region"]),
                chunk_ids=tuple(str(item) for item in chunk_ids),
                plan_ordinals=tuple(_stored_int(item, "plan_ordinals") for item in plan_ordinals),
                start=_stored_int(record["start"], "start"),
                end=_stored_int(record["end"], "end"),
            )
        except KeyError as exc:
            message = f"a merge-group record is missing {exc}; it is refused rather than read"
            raise ChunkMultipassError(message) from exc


def _stored_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        message = (
            f"multipass field {field!r} holds {type(value).__name__} where an integer is "
            "required; a record that cannot be read is refused rather than coerced"
        )
        raise ChunkMultipassError(message)
    return int(value)


@dataclass(frozen=True, slots=True)
class MergeSchedule:
    """The deterministic two-level merge schedule of one sealed multipass plan.

    Derived from the plan, never accepted as input: :func:`derive_merge_schedule` is the only
    constructor a consumer should reach, and :func:`require_sealed_schedule` re-derives the
    schedule from the plan and refuses one that differs in any group's membership, order, region
    or interval. ``schedule_digest`` folds the plan digest, the grouping contract, the fan-in,
    every group and the level-2 input order.
    """

    contract: str
    plan_digest: str
    fan_in: int
    groups: tuple[MergeGroup, ...]
    level_two_inputs: tuple[str, ...]
    schedule_digest: str

    def _digest_inputs(self) -> Mapping[str, object]:
        return {
            "contract": self.contract,
            "plan_digest": self.plan_digest,
            "fan_in": self.fan_in,
            "groups": [dict(group.as_record()) for group in self.groups],
            "level_two_inputs": list(self.level_two_inputs),
        }

    def as_record(self) -> Mapping[str, object]:
        """The complete schedule as a plain mapping."""
        record = dict(self._digest_inputs())
        record["schedule_digest"] = self.schedule_digest
        return record

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> MergeSchedule:
        """Rebuild a schedule from its stored mapping and re-derive its digest.

        Raises:
            ChunkMultipassError: a field is absent, the contract is unknown, or the stored digest
                does not describe the record's own contents.
        """
        try:
            groups = record["groups"]
            inputs = record["level_two_inputs"]
            if not isinstance(groups, list) or not isinstance(inputs, list):
                message = "a merge schedule's groups and level_two_inputs must be lists; refused"
                raise ChunkMultipassError(message)
            schedule = cls(
                contract=str(record["contract"]),
                plan_digest=str(record["plan_digest"]),
                fan_in=_stored_int(record["fan_in"], "fan_in"),
                groups=tuple(
                    MergeGroup.from_record(item) for item in groups if isinstance(item, Mapping)
                ),
                level_two_inputs=tuple(str(item) for item in inputs),
                schedule_digest=str(record["schedule_digest"]),
            )
        except KeyError as exc:
            message = f"a merge-schedule record is missing {exc}; it is refused rather than read"
            raise ChunkMultipassError(message) from exc
        if len(schedule.groups) != len(groups):
            message = "a merge schedule carries a group entry that is not a mapping; refused"
            raise ChunkMultipassError(message)
        if schedule.contract != MERGE_SCHEDULE_CONTRACT:
            message = (
                f"a merge schedule carrying contract {schedule.contract!r} is refused; this build "
                f"derives {MERGE_SCHEDULE_CONTRACT!r} and never adopts another shape"
            )
            raise ChunkMultipassError(message)
        recomputed = _schedule_digest(schedule)
        if recomputed != schedule.schedule_digest:
            message = (
                "a merge schedule's recorded digest does not describe its own contents: recorded "
                f"{schedule.schedule_digest!r}, recomputed {recomputed!r}. It is refused rather "
                "than repaired"
            )
            raise ChunkMultipassError(message)
        return schedule


def _schedule_digest(schedule: MergeSchedule) -> str:
    payload = json.dumps(
        dict(schedule._digest_inputs()),  # noqa: SLF001 - the schedule's own digest
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def group_chunks(
    chunks: Sequence[ChunkBounds], *, fan_in: int = MERGE_FAN_IN
) -> tuple[MergeGroup, ...]:
    """Group chunk bounds into contiguous, region-homogeneous runs of at most ``fan_in``.

    Pure arithmetic, stated once. Regions are taken in the accepted region order and each region's
    chunks are cut, in the order given, into runs of ``fan_in`` with the last run carrying the
    remainder. Group identifiers number the runs across regions in that order, so for the real
    source at thirty-four chunks -- thirty-three primary and one shard -- the result is exactly
    ``9 / 9 / 9 / 6`` primary groups followed by one one-chunk shard group.

    Raises:
        ChunkMultipassError: ``fan_in`` is not positive, or a region's chunks are not contiguous
            in the order given.
    """
    if fan_in < 1:
        message = f"a merge schedule needs a positive fan-in; got {fan_in}"
        raise ChunkMultipassError(message)
    groups: list[MergeGroup] = []
    for region in CHUNK_REGION_ORDER:
        members = [
            (index, bounds) for index, bounds in enumerate(chunks) if bounds.region == region
        ]
        for offset in range(0, len(members), fan_in):
            run = members[offset : offset + fan_in]
            for (_, previous), (_, following) in zip(run, run[1:], strict=False):
                if following.start != previous.end:
                    message = (
                        f"chunks {previous.chunk_id!r} and {following.chunk_id!r} are not "
                        "contiguous in canonical order; a merge group is a contiguous run and "
                        "the schedule is refused rather than derived over a gap"
                    )
                    raise ChunkMultipassError(message)
            groups.append(
                MergeGroup(
                    group_id=f"group-{len(groups):04d}",
                    ordinal=len(groups),
                    region=region,
                    chunk_ids=tuple(bounds.chunk_id for _, bounds in run),
                    plan_ordinals=tuple(index for index, _ in run),
                    start=run[0][1].start,
                    end=run[-1][1].end,
                )
            )
    return tuple(groups)


def derive_merge_schedule(plan: ChunkPlan) -> MergeSchedule:
    """The one merge schedule a sealed multipass plan implies -- D151-C13 §§6, 7.

    Raises:
        ChunkMultipassError: the plan is not a multipass plan, or the grouping leaves level 2
            with more inputs than one merge attaches -- impossible within the multipass ceiling,
            and refused rather than assumed.
    """
    require_multipass_plan(plan)
    groups = group_chunks(plan.chunks, fan_in=MERGE_FAN_IN)
    if len(groups) > MERGE_FAN_IN:
        message = (  # pragma: no cover - unreachable at or below MULTIPASS_CHUNK_CEILING
            f"the plan groups into {len(groups)} level-1 intermediates and one merge attaches "
            f"{MERGE_FAN_IN}; a third level is not implemented and the schedule is refused"
        )
        raise ChunkMultipassError(message)
    schedule = MergeSchedule(
        contract=MERGE_SCHEDULE_CONTRACT,
        plan_digest=plan.plan_digest,
        fan_in=MERGE_FAN_IN,
        groups=groups,
        level_two_inputs=tuple(group.group_id for group in groups),
        schedule_digest="",
    )
    return replace(schedule, schedule_digest=_schedule_digest(schedule))


def require_sealed_schedule(schedule: MergeSchedule, plan: ChunkPlan) -> MergeSchedule:
    """Return ``schedule`` only if it is exactly the schedule ``plan`` implies.

    The digest is recomputed and compared, and the whole schedule is re-derived from the plan and
    compared structurally, so a group whose membership, order, region or interval moved -- with or
    without a recomputed digest -- is refused at the point of consumption.

    Raises:
        ChunkMultipassError: the schedule is not its sealed self, or is not the plan's.
    """
    recomputed = _schedule_digest(schedule)
    if recomputed != schedule.schedule_digest:
        message = (
            "a merge schedule's recorded digest does not describe its own contents: recorded "
            f"{schedule.schedule_digest!r}, recomputed {recomputed!r}. Refused rather than repaired"
        )
        raise ChunkMultipassError(message)
    # A calibration-subset plan implies its schedule through its own derivation (D151-C27R1);
    # the dispatch is on the sealed type, and a production plan is derived exactly as before.
    derived = (
        derive_calibration_subset_schedule(plan)
        if isinstance(plan, CalibrationSubsetPlan)
        else derive_merge_schedule(plan)
    )
    if derived != schedule:
        message = (
            f"the merge schedule {schedule.schedule_digest[:16]}... is not the schedule plan "
            f"{plan.plan_digest[:16]}... implies ({derived.schedule_digest[:16]}...). A schedule "
            "is derived from the sealed plan and never accepted as discretionary input: a group "
            "whose membership, order, region or interval differs is refused"
        )
        raise ChunkMultipassError(message)
    return schedule


def group_by_id(schedule: MergeSchedule, group_id: str) -> MergeGroup:
    """One group's record, or a refusal.

    Raises:
        ChunkMultipassError: the schedule carries no group of that identity.
    """
    for group in schedule.groups:
        if group.group_id == group_id:
            return group
    message = (
        f"group {group_id!r} is not in this merge schedule; the schedule carries "
        f"{[group.group_id for group in schedule.groups]}. A group identity is never inferred"
    )
    raise ChunkMultipassError(message)


# --------------------------------------------------------------------------- #
# The set-based first-witness correction -- D151-C13 §§11, 12, 15
# --------------------------------------------------------------------------- #
#: The run-local ranking of every input's canonical accession row: one row per (accession,
#: input), ranked in canonical input order. A ``TEMP`` table; it never reaches a catalog.
WITNESS_RANK_TABLE: Final = "chunk_witness_rank"

_FUNCTION_STABLE_ID: Final = "dd_stable_id"
_FUNCTION_RIVAL_FIELDS: Final = "dd_rival_fields_json"
_FUNCTION_RECONSTRUCTED_FIELDS: Final = "dd_reconstructed_fields_json"


def _utf8_rendering(value: object) -> str:
    """The accepted ``raw_value_json`` rendering of one value, refusing what SQLite would refuse.

    The accepted writer hands the rendered text to ``sqlite3``, which encodes it as UTF-8 and
    refuses a lone surrogate. Rendering inside a user function must refuse the same input rather
    than hand SQLite an already-escaped form it would store.
    """
    rendered = _stable_json(value)
    rendered.encode("utf-8")
    return rendered


def _rival_fields_json(payload_json: str) -> str:
    """Every governed field a rival witness materializes, rendered, as one JSON object.

    The accepted :func:`~disclosure_drift.m3.compact_evidence.materialized_fields` with
    ``first_witness=False``, called over the payload the chunk already persisted, and the accepted
    ``raw_value_json`` rendering of each value. Returned as an object so ``json_each`` can explode
    it into one row per field inside a single ``INSERT ... SELECT``.
    """
    payload = json.loads(payload_json)
    rendered = {
        field: _utf8_rendering(payload[field])
        for field in materialized_fields(payload, first_witness=False)
    }
    return json.dumps(rendered, sort_keys=True, separators=(",", ":"))


def _reconstructed_fields_json(
    acceptance_datetime_sec_raw: object,
    registrant_cik_padded: object,
    filing_date_sec: object,
    form_type: object,
    primary_document_name: object,
    report_date: object,
) -> str:
    """Every omitted observation one canonical row implies, rendered, as one JSON object.

    The accepted :func:`~disclosure_drift.m3.compact_evidence.reconstructed_observations` over the
    canonical row's columns, handed in as the same SQL values a ``sqlite3.Row`` would carry.
    """
    row = {
        "acceptance_datetime_sec_raw": acceptance_datetime_sec_raw,
        "registrant_cik_padded": registrant_cik_padded,
        "filing_date_sec": filing_date_sec,
        "form_type": form_type,
        "primary_document_name": primary_document_name,
        "report_date": report_date,
    }
    rendered = {field: _utf8_rendering(value) for field, value in reconstructed_observations(row)}
    return json.dumps(rendered, sort_keys=True, separators=(",", ":"))


def _register_correction_functions(connection: sqlite3.Connection) -> None:
    """Bind the accepted identity and rendering functions into this connection, deterministically.

    ``deterministic=True`` is a statement of fact SQLite is allowed to rely on: each function is
    a pure function of its arguments, which is what makes the statements below plannable.
    """
    connection.create_function(_FUNCTION_STABLE_ID, 5, _stable_id, deterministic=True)
    connection.create_function(_FUNCTION_RIVAL_FIELDS, 1, _rival_fields_json, deterministic=True)
    connection.create_function(
        _FUNCTION_RECONSTRUCTED_FIELDS, 6, _reconstructed_fields_json, deterministic=True
    )


def stage_first_witness_corrections(
    connection: sqlite3.Connection, aliases: Sequence[str]
) -> tuple[int, int]:
    """Stage every observation row the cross-input first-witness rule implies -- SET-BASED.

    The accepted semantics are the single-pass consolidator's, unchanged: for an accession whose
    canonical rows appear in more than one attached input, the canonical-earliest input's witness
    is the true first witness and every later input's local-first witness is a rival. The true
    first witness has its omitted observations back-filled from its canonical row; every rival
    materializes every governed field it observed, from its own retained payload. What changes is
    the shape of the work:

    * one window function ranks every input's canonical accession row per accession
      (:data:`WITNESS_RANK_TABLE`);
    * ONE ``INSERT ... SELECT`` stages the winner back-fill over the loaded ``census_accessions``
      rows joined to that ranking, rendering through the accepted reconstruction as a user
      function exploded by ``json_each``;
    * ONE ``INSERT ... SELECT`` stages the rival upgrade over the loaded ``census_parsed_records``
      payloads joined to that ranking, rendering through the accepted rival rule the same way;
    * the identifiers are the accepted content-derived ones, computed by the accepted function
      inside the statement.

    Inputs are level-agnostic: attached chunk worlds at level 1, attached intermediates at level
    2. At level 2 the "later input's local-first witness" is exactly a level-1 group winner that
    loses globally, and this is the additive global loser upgrade D151-C13 §12 requires. The
    staging table is the one the accepted single-pass observation load
    (:func:`~disclosure_drift.m3.chunk_consolidation._load_accession_observations`) reads, under
    the accepted ``INSERT OR IGNORE`` priority ordering, so the upgrade is additive and a second
    application is refused here (the tables already exist) and would be idempotent there. No
    Python statement runs per accession or per rival.

    Returns:
        ``(accessions_corrected, rows_staged)``.

    Raises:
        ChunkMultipassError: a ranked row has no loaded canonical row or payload to correct
            from, which cannot be true of inputs that were just loaded.
    """
    already = connection.execute(
        "SELECT name FROM temp.sqlite_master WHERE type = 'table' AND name IN (?, ?)",
        (CORRECTIONS_TABLE, WITNESS_RANK_TABLE),
    ).fetchall()
    if already:
        message = (
            "the first-witness correction has already been staged on this connection "
            f"({[str(row['name']) for row in already]} exist). The staged rows are loaded once "
            "under INSERT OR IGNORE, which is idempotent; staging them a second time is refused "
            "explicitly rather than re-derived"
        )
        raise ChunkMultipassError(message)
    _register_correction_functions(connection)
    connection.execute(
        f"CREATE TEMP TABLE {CORRECTIONS_TABLE} ("  # noqa: S608
        "accession_observation_id TEXT, accession_plain TEXT, source_observation_id TEXT, "
        "parsed_record_id TEXT, field_name TEXT, raw_value_json TEXT, observed_at_utc TEXT, "
        "conflict_indicator INTEGER)"
    )
    union = _union_all(
        aliases,
        "census_accessions",
        "accession_plain, source_observation_id, parsed_record_id, first_observed_at_utc",
        extra=" AS chunk_ordinal",
    )
    connection.execute(
        f"CREATE TEMP TABLE {WITNESS_RANK_TABLE} AS "  # noqa: S608
        "SELECT accession_plain, source_observation_id, parsed_record_id, first_observed_at_utc, "
        "chunk_ordinal, "
        "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY chunk_ordinal) AS witness_rank, "
        "COUNT(*) OVER (PARTITION BY accession_plain) AS witnesses "
        f"FROM ({union})"
    )
    orphaned_winners = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "LEFT JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain "
        "WHERE w.witness_rank = 1 AND w.witnesses > 1 AND a.accession_plain IS NULL"
    ).fetchone()
    _require(
        int(orphaned_winners["n"]) == 0,
        "a contested accession has no loaded canonical row between load and correction; the "
        "consolidation is refused rather than corrected against a row that is not there",
    )
    orphaned_rivals = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "LEFT JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id "
        "WHERE w.witness_rank > 1 AND p.parsed_record_id IS NULL"
    ).fetchone()
    _require(
        int(orphaned_rivals["n"]) == 0,
        "a rival witness's parsed record is absent at correction time; the consolidation is "
        "refused rather than materialized from nothing",
    )
    # The winner back-fill: the accepted reconstruction over the loaded canonical row, once per
    # contested accession, exploded into one staged row per reconstructed field.
    connection.execute(
        f"INSERT INTO temp.{CORRECTIONS_TABLE} "  # noqa: S608
        f"SELECT {_FUNCTION_STABLE_ID}('accession-observation', a.accession_plain, "
        "a.source_observation_id, a.parsed_record_id, je.key), "
        "a.accession_plain, a.source_observation_id, a.parsed_record_id, je.key, je.value, "
        "a.first_observed_at_utc, 0 "
        f"FROM temp.{WITNESS_RANK_TABLE} AS w "
        "JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain, "
        f"json_each({_FUNCTION_RECONSTRUCTED_FIELDS}(a.acceptance_datetime_sec_raw, "
        "CASE WHEN a.registrant_cik_numeric IS NULL THEN NULL "
        "ELSE printf('%010d', a.registrant_cik_numeric) END, "
        "a.filing_date_sec, a.form_type, a.primary_document_name, a.report_date)) AS je "
        "WHERE w.witness_rank = 1 AND w.witnesses > 1"
    )
    # The rival upgrade -- at level 2, the global loser upgrade: every input's local-first witness
    # that is not the canonical-earliest one, re-materialized from its own retained payload.
    connection.execute(
        f"INSERT INTO temp.{CORRECTIONS_TABLE} "  # noqa: S608
        f"SELECT {_FUNCTION_STABLE_ID}('accession-observation', w.accession_plain, "
        "w.source_observation_id, w.parsed_record_id, je.key), "
        "w.accession_plain, w.source_observation_id, w.parsed_record_id, je.key, je.value, "
        "w.first_observed_at_utc, 0 "
        f"FROM temp.{WITNESS_RANK_TABLE} AS w "
        "JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id, "
        f"json_each({_FUNCTION_RIVAL_FIELDS}(p.payload_json)) AS je "
        "WHERE w.witness_rank > 1"
    )
    summary = connection.execute(
        f"SELECT (SELECT COUNT(*) FROM temp.{WITNESS_RANK_TABLE} "  # noqa: S608
        "WHERE witness_rank = 1 AND witnesses > 1) AS contested, "
        f"(SELECT COUNT(*) FROM temp.{CORRECTIONS_TABLE}) AS staged"
    ).fetchone()
    return int(summary["contested"]), int(summary["staged"])


#: The plan-wide accession-witness table the whole-F0 receipt counters are derived from --
#: D151-C15 R1. Run-local, ``TEMP``, never an accepted catalog table.
PLAN_WITNESS_TABLE: Final = "plan_chunk_witnesses"

#: Its ranking: every chunk's canonical accession row, ranked by plan ordinal within its accession.
PLAN_WITNESS_RANK_TABLE: Final = "plan_witness_rank"

#: The plan-wide copy of every chunk's first-witness ledger. Its name is the ledger table's own,
#: deliberately: the accepted member-delta reduction reads ``<alias>.chunk_first_witness`` and is
#: handed the ``temp`` schema as its one alias, so it runs unchanged over the whole plan.
PLAN_LEDGER_TABLE: Final = "chunk_first_witness"


class PlanWitnessSource(Protocol):
    """What the whole-F0 counter derivation reads from one chunk -- D151-C29R1.

    Its plan ordinal, a database holding its ``census_accessions`` rows and a database holding
    its ``chunk_first_witness`` ledger: the chunk artifacts themselves
    (:class:`~disclosure_drift.m3.chunk_consolidation.ChunkInput`) or, on the retention-aware
    calibration route, their exact retained projection (:class:`RetainedWitnessInput`).
    """

    @property
    def ordinal(self) -> int:
        """The chunk's plan ordinal -- the ranking key."""

    @property
    def catalog_path(self) -> Path:
        """A database holding this chunk's ``census_accessions`` rows."""

    @property
    def witness_path(self) -> Path:
        """A database holding this chunk's ``chunk_first_witness`` ledger."""


def _plan_first_witness_counters(
    connection: sqlite3.Connection, chunks: Sequence[PlanWitnessSource]
) -> tuple[int, int, int, int]:
    """The final receipt's four correction counters, derived over the plan's chunks -- D151-C15 R1.

    The accepted single-pass receipt reports what its consolidation corrected across ITS chunks:
    ``first_witness_accessions_corrected`` is the number of accessions whose canonical row appears
    in more than one chunk world; ``first_witness_rows_staged`` is every observation row the
    correction staged for them -- the accepted reconstruction over the canonical-earliest chunk's
    row and the accepted rival rule over each later chunk's local-first witness; and
    ``evidence_members_corrected`` / ``evidence_delta`` are the accepted member-delta reduction
    over every chunk's first-witness ledger. The multipass receipt reports exactly those four
    quantities over the plan's chunks, whatever the level-1 grouping was. They are NOT the level-2
    stage counts, which omit every correction a group applied internally, and NOT the sum of the
    two levels' stage counts, which repeats every group winner's back-fill and every member
    corrected at both levels (D151-C14 §32).

    The derivation reads only retained, authenticated artifacts -- each chunk's
    ``census_accessions`` rows and its first-witness ledger, attached immutably at most
    :data:`MERGE_FAN_IN` at a time -- joined to the final world's loaded canonical rows and
    payloads. The rendering functions are the accepted ones; the row counts are the
    ``INSERT ... SELECT`` shapes of :func:`stage_first_witness_corrections` with the insert
    replaced by a count, so what is counted is exactly what one pass over these chunks would have
    staged; the member reduction is
    :func:`~disclosure_drift.m3.chunk_consolidation._member_deltas` itself. Database interaction
    scales with the CHUNK COUNT and never with the accession or rival population: no statement is
    issued per accession or per rival (D151-C8 M2). Under the traced implementation the count is
    ``11 + 6 * chunks`` -- per chunk, one attach and one detach of its catalog, one attach and one
    detach of its witness ledger, one insert of its accession rows and one of its ledger rows --
    and the committed statement-count test holds this prose to the measurement (D151-C19 R6).

    Since D151-C29R1 each item is a :class:`PlanWitnessSource`: a chunk world or its exact
    retained projection, whose payload carries the same two tables under the same names. The
    retention-aware calibration final therefore runs these SAME statements over the witnesses
    after the chunk worlds are gone; nothing below distinguishes the two.

    Raises:
        ChunkMultipassError: the derivation was already run on this connection; a contested
            accession has no canonical row in the final world; or a rival's parsed record is
            absent -- refused rather than counted against a row that is not there.
    """
    already = connection.execute(
        "SELECT name FROM temp.sqlite_master WHERE type = 'table' AND name IN (?, ?, ?)",
        (PLAN_WITNESS_TABLE, PLAN_WITNESS_RANK_TABLE, PLAN_LEDGER_TABLE),
    ).fetchall()
    _require(
        not already,
        "the whole-F0 counters were already derived on this connection "
        f"({[str(row['name']) for row in already]} exist); a second derivation is refused",
    )
    _register_correction_functions(connection)
    connection.execute(
        f"CREATE TEMP TABLE {PLAN_WITNESS_TABLE} ("  # noqa: S608
        "accession_plain TEXT NOT NULL, parsed_record_id TEXT NOT NULL, "
        "chunk_ordinal INTEGER NOT NULL)"
    )
    connection.execute(
        f"CREATE TEMP TABLE {PLAN_LEDGER_TABLE} ("  # noqa: S608
        "native_identity TEXT NOT NULL, member_ordinal INTEGER NOT NULL, "
        "record_ordinal INTEGER NOT NULL, delta_materialized INTEGER NOT NULL)"
    )
    for offset in range(0, len(chunks), MERGE_FAN_IN):
        batch = chunks[offset : offset + MERGE_FAN_IN]
        catalogs = _attach_all(connection, [item.catalog_path for item in batch], "pc")
        try:
            for alias, item in zip(catalogs, batch, strict=True):
                connection.execute(
                    f"INSERT INTO temp.{PLAN_WITNESS_TABLE} "  # noqa: S608
                    "(accession_plain, parsed_record_id, chunk_ordinal) "
                    "SELECT accession_plain, parsed_record_id, ? "
                    f"FROM {alias}.census_accessions",
                    (item.ordinal,),
                )
        finally:
            _detach_all(connection, catalogs)
        ledgers = _attach_all(connection, [item.witness_path for item in batch], "pw")
        try:
            for alias in ledgers:
                connection.execute(
                    f"INSERT INTO temp.{PLAN_LEDGER_TABLE} "  # noqa: S608
                    "(native_identity, member_ordinal, record_ordinal, delta_materialized) "
                    "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                    f"FROM {alias}.chunk_first_witness"
                )
        finally:
            _detach_all(connection, ledgers)
    connection.execute(
        f"CREATE TEMP TABLE {PLAN_WITNESS_RANK_TABLE} AS "  # noqa: S608
        "SELECT accession_plain, parsed_record_id, "
        "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY chunk_ordinal) AS witness_rank, "
        "COUNT(*) OVER (PARTITION BY accession_plain) AS witnesses "
        f"FROM temp.{PLAN_WITNESS_TABLE}"
    )
    orphaned_winners = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "LEFT JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain "
        "WHERE w.witness_rank = 1 AND w.witnesses > 1 AND a.accession_plain IS NULL"
    ).fetchone()
    _require(
        int(orphaned_winners["n"]) == 0,
        "a contested accession of the plan has no canonical row in the final world; the whole-F0 "
        "counters are refused rather than derived against a row that is not there",
    )
    orphaned_rivals = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "LEFT JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id "
        "WHERE w.witness_rank > 1 AND p.parsed_record_id IS NULL"
    ).fetchone()
    _require(
        int(orphaned_rivals["n"]) == 0,
        "a chunk's local-first witness has no parsed record in the final world; the whole-F0 "
        "counters are refused rather than derived from nothing",
    )
    contested = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{PLAN_WITNESS_RANK_TABLE} "  # noqa: S608
        "WHERE witness_rank = 1 AND witnesses > 1"
    ).fetchone()
    winner_rows = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain, "
        f"json_each({_FUNCTION_RECONSTRUCTED_FIELDS}(a.acceptance_datetime_sec_raw, "
        "CASE WHEN a.registrant_cik_numeric IS NULL THEN NULL "
        "ELSE printf('%010d', a.registrant_cik_numeric) END, "
        "a.filing_date_sec, a.form_type, a.primary_document_name, a.report_date)) AS je "
        "WHERE w.witness_rank = 1 AND w.witnesses > 1"
    ).fetchone()
    rival_rows = connection.execute(
        f"SELECT COUNT(*) AS n FROM temp.{PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
        "JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id, "
        f"json_each({_FUNCTION_RIVAL_FIELDS}(p.payload_json)) AS je "
        "WHERE w.witness_rank > 1"
    ).fetchone()
    members, delta = _member_deltas(connection, ("temp",))
    return int(contested["n"]), int(winner_rows["n"]) + int(rival_rows["n"]), members, delta


# --------------------------------------------------------------------------- #
# The intermediate artifact -- D151-C13 §§8, 9, 27, 28
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class IntermediateReceipt:
    """One level-1 intermediate's create-once terminal record -- D151-C13 §8.

    It binds the multipass plan and the merge schedule it was built under, which group it is and
    which interval that group covers, every input chunk by identity and by the digest of the
    receipt document that bound it, the source and the canonical ordering, the execution contract
    every input shared, the code that ran the merge, the objects it produced with their digests,
    the reduced witness ledger's identity, the compact evidence's identity, the resulting
    catalog's byte identity and what it counted. ``parser_state_after`` is deliberately absent:
    an intermediate establishes no source-level terminal.
    """

    contract: str
    plan_digest: str
    merge_schedule_digest: str
    group_id: str
    group_ordinal: int
    region: str
    start: int
    end: int
    input_chunk_ids: tuple[str, ...]
    input_receipt_sha256: tuple[str, ...]
    input_manifest_digests: tuple[str, ...]
    chunk_inputs: tuple[Mapping[str, object], ...]
    source_instance_id: str
    source_observation_id: str
    source_sha256: str
    source_byte_length: int
    member_order_digest: str
    repository_head_sha: str
    repository_tree_sha: str
    execution_contract: ExecutionContract
    parser_run_id: str
    catalog_sha256: str
    table_row_counts: Mapping[str, int]
    members: int
    records: int
    omitted_field_observations: int
    materialized_field_observations: int
    member_manifest_digest: str
    witness_ledger_identity: str
    compact_evidence_identity: str
    first_witness_accessions_corrected: int
    first_witness_rows_staged: int
    evidence_members_corrected: int
    evidence_delta: int
    storage_admission: Mapping[str, object]
    earliest_input_started_at_utc: str
    attempt: int
    pid: int
    rss_peak_bytes: int | None
    started_at_utc: str
    completed_at_utc: str
    manifest: ArtifactManifest
    status: str

    def as_record(self) -> Mapping[str, object]:
        """The complete receipt as a plain mapping, carrying no absolute path."""
        return {
            "contract": self.contract,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "group_id": self.group_id,
            "group_ordinal": self.group_ordinal,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "input_chunk_ids": list(self.input_chunk_ids),
            "input_receipt_sha256": list(self.input_receipt_sha256),
            "input_manifest_digests": list(self.input_manifest_digests),
            "chunk_inputs": [dict(item) for item in self.chunk_inputs],
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_sha256": self.source_sha256,
            "source_byte_length": self.source_byte_length,
            "member_order_digest": self.member_order_digest,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "execution_contract": dict(self.execution_contract.as_record()),
            "parser_run_id": self.parser_run_id,
            "catalog_sha256": self.catalog_sha256,
            "table_row_counts": dict(sorted(self.table_row_counts.items())),
            "members": self.members,
            "records": self.records,
            "omitted_field_observations": self.omitted_field_observations,
            "materialized_field_observations": self.materialized_field_observations,
            "member_manifest_digest": self.member_manifest_digest,
            "witness_ledger_identity": self.witness_ledger_identity,
            "compact_evidence_identity": self.compact_evidence_identity,
            "first_witness_accessions_corrected": self.first_witness_accessions_corrected,
            "first_witness_rows_staged": self.first_witness_rows_staged,
            "evidence_members_corrected": self.evidence_members_corrected,
            "evidence_delta": self.evidence_delta,
            "storage_admission": dict(self.storage_admission),
            "earliest_input_started_at_utc": self.earliest_input_started_at_utc,
            "attempt": self.attempt,
            "pid": self.pid,
            "rss_peak_bytes": self.rss_peak_bytes,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "manifest": dict(self.manifest.as_record()),
            "status": self.status,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> IntermediateReceipt:  # noqa: PLR0915
        """Rebuild a receipt from its stored mapping, refusing one this build cannot read.

        Raises:
            ChunkMultipassError: a required field is absent or is not of the recorded type.
        """
        try:
            manifest = record["manifest"]
            contract = record["execution_contract"]
            counts = record["table_row_counts"]
            admission = record["storage_admission"]
            chunk_inputs = record["chunk_inputs"]
            if (
                not isinstance(manifest, Mapping)
                or not isinstance(contract, Mapping)
                or not isinstance(counts, Mapping)
                or not isinstance(admission, Mapping)
                or not isinstance(chunk_inputs, list)
            ):
                message = (
                    "an intermediate receipt's manifest, execution contract, row counts, storage "
                    "admission or chunk inputs are not of the recorded shape and it is refused"
                )
                raise ChunkMultipassError(message)
            peak = record.get("rss_peak_bytes")
            return cls(
                contract=str(record["contract"]),
                plan_digest=str(record["plan_digest"]),
                merge_schedule_digest=str(record["merge_schedule_digest"]),
                group_id=str(record["group_id"]),
                group_ordinal=_stored_int(record["group_ordinal"], "group_ordinal"),
                region=str(record["region"]),
                start=_stored_int(record["start"], "start"),
                end=_stored_int(record["end"], "end"),
                input_chunk_ids=_stored_strings(record["input_chunk_ids"], "input_chunk_ids"),
                input_receipt_sha256=_stored_strings(
                    record["input_receipt_sha256"], "input_receipt_sha256"
                ),
                input_manifest_digests=_stored_strings(
                    record["input_manifest_digests"], "input_manifest_digests"
                ),
                chunk_inputs=tuple(
                    {str(key): value for key, value in item.items()}
                    for item in chunk_inputs
                    if isinstance(item, Mapping)
                ),
                source_instance_id=str(record["source_instance_id"]),
                source_observation_id=str(record["source_observation_id"]),
                source_sha256=str(record["source_sha256"]),
                source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
                member_order_digest=str(record["member_order_digest"]),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                execution_contract=ExecutionContract.from_record(contract),
                parser_run_id=str(record["parser_run_id"]),
                catalog_sha256=str(record["catalog_sha256"]),
                table_row_counts={
                    str(key): _stored_int(value, str(key)) for key, value in counts.items()
                },
                members=_stored_int(record["members"], "members"),
                records=_stored_int(record["records"], "records"),
                omitted_field_observations=_stored_int(
                    record["omitted_field_observations"], "omitted_field_observations"
                ),
                materialized_field_observations=_stored_int(
                    record["materialized_field_observations"], "materialized_field_observations"
                ),
                member_manifest_digest=str(record["member_manifest_digest"]),
                witness_ledger_identity=str(record["witness_ledger_identity"]),
                compact_evidence_identity=str(record["compact_evidence_identity"]),
                first_witness_accessions_corrected=_stored_int(
                    record["first_witness_accessions_corrected"],
                    "first_witness_accessions_corrected",
                ),
                first_witness_rows_staged=_stored_int(
                    record["first_witness_rows_staged"], "first_witness_rows_staged"
                ),
                evidence_members_corrected=_stored_int(
                    record["evidence_members_corrected"], "evidence_members_corrected"
                ),
                evidence_delta=_stored_int(record["evidence_delta"], "evidence_delta"),
                storage_admission={str(key): value for key, value in admission.items()},
                earliest_input_started_at_utc=str(record["earliest_input_started_at_utc"]),
                attempt=_stored_int(record["attempt"], "attempt"),
                pid=_stored_int(record["pid"], "pid"),
                rss_peak_bytes=None if peak is None else _stored_int(peak, "rss_peak_bytes"),
                started_at_utc=str(record["started_at_utc"]),
                completed_at_utc=str(record["completed_at_utc"]),
                manifest=ArtifactManifest.from_record(manifest),
                status=str(record["status"]),
            )
        except KeyError as exc:
            message = f"an intermediate receipt is missing {exc}; it is refused rather than read"
            raise ChunkMultipassError(message) from exc
        except ChunkEvidenceError as exc:
            message = f"an intermediate receipt's manifest or contract is refused: {exc}"
            raise ChunkMultipassError(message) from exc


def _stored_strings(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        message = f"intermediate field {field!r} is not a list and is refused"
        raise ChunkMultipassError(message)
    return tuple(str(item) for item in value)


@dataclass(frozen=True, slots=True)
class IntermediateInput:
    """One validated intermediate, resolved to its one verified attempt directory."""

    group_id: str
    ordinal: int
    region: str
    start: int
    end: int
    directory: Path
    receipt: IntermediateReceipt

    @property
    def catalog_path(self) -> Path:
        """This intermediate's working catalog."""
        return self.directory / WORKING_CATALOG_FILENAME

    @property
    def sidecar_path(self) -> Path:
        """This intermediate's reduced compact-evidence sidecar."""
        return self.directory / COMPACT_EVIDENCE_SIDECAR_FILENAME

    @property
    def witness_path(self) -> Path:
        """This intermediate's reduced first-witness ledger."""
        return self.directory / INTERMEDIATE_WITNESS_FILENAME

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "group_id": self.group_id,
            "ordinal": self.ordinal,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "manifest_digest": self.receipt.manifest.digest,
            "input_chunk_ids": list(self.receipt.input_chunk_ids),
        }


def intermediate_attempt_directory(root: Path, group_id: str, attempt: int) -> Path:
    """Where one attempt at one intermediate lives. Create-once, never reused."""
    return root / group_id / f"attempt-{attempt:03d}"


def _attempt_directories(root: Path, group_id: str) -> list[Path]:
    parent = root / group_id
    if not parent.is_dir():
        return []
    return sorted(path for path in parent.iterdir() if path.is_dir() and not path.is_symlink())


def completed_intermediate_receipt(
    root: Path, group_id: str
) -> tuple[IntermediateReceipt, Path] | None:
    """The one valid terminal receipt this group carries, or ``None`` -- D151-C13 §27.

    Every attempt directory is inspected. An attempt with no receipt file never completed and is
    skipped. An attempt WITH a receipt is verified against the artifacts it names, and **a receipt
    that fails to verify is a loud refusal, never "never ran"**: the swallowed-invalid-receipt
    ambiguity D151-C8 recorded against chunk discovery is deliberately not inherited here, because
    an intermediate that once completed and no longer verifies is a changed artifact, and the
    canonical multipass must stop rather than rebuild beside it. Two valid receipts for one group
    are ambiguous authority and are refused rather than ranked.

    Raises:
        ChunkMultipassError: a present receipt does not read, does not describe this group, or
            does not verify; or more than one attempt carries a valid receipt.
    """
    found: list[tuple[IntermediateReceipt, Path]] = []
    for directory in _attempt_directories(root, group_id):
        receipt_path = directory / INTERMEDIATE_RECEIPT_FILENAME
        if not receipt_path.is_file():
            continue
        try:
            receipt = IntermediateReceipt.from_record(
                read_receipt_document(receipt_path, contract=INTERMEDIATE_RECEIPT_CONTRACT)
            )
            verify_artifact_manifest(
                directory, receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
            )
        except (ChunkEvidenceError, ChunkMultipassError) as exc:
            message = (
                f"intermediate {group_id!r} attempt {directory.name!r} carries a receipt that "
                f"does not verify: {exc}. A completed intermediate whose artifacts moved is a "
                "changed artifact, not an attempt that never ran; the canonical multipass STOPS "
                "rather than reinterpreting it or rebuilding beside it"
            )
            raise ChunkMultipassError(message) from exc
        _require(
            receipt.group_id == group_id and receipt.status == "complete",
            f"intermediate attempt {directory.name!r} under {group_id!r} carries a receipt for "
            f"group {receipt.group_id!r} with status {receipt.status!r}; refused",
        )
        found.append((receipt, directory))
    if len(found) > 1:
        message = (
            f"intermediate {group_id!r} carries {len(found)} valid terminal receipts, in "
            f"{[path.name for _, path in found]}. Duplicate authority is refused rather than "
            "resolved: nothing here ranks two completed merges of the same group by attempt "
            "number, modification time or size"
        )
        raise ChunkMultipassError(message)
    return found[0] if found else None


def next_intermediate_attempt_directory(root: Path, group_id: str) -> tuple[Path, int]:
    """The lowest unused attempt directory for one group, and its ordinal.

    Raises:
        ChunkMultipassError: the group already carries a valid terminal receipt -- a completed
            intermediate is immutable and is reused, never rebuilt -- or a present receipt does
            not verify.
    """
    existing = completed_intermediate_receipt(root, group_id)
    if existing is not None:
        message = (
            f"intermediate {group_id!r} already carries a valid terminal receipt (attempt "
            f"{existing[0].attempt}); a completed intermediate is IMMUTABLE and is reused, never "
            "re-merged"
        )
        raise ChunkMultipassError(message)
    attempt = 0
    while intermediate_attempt_directory(root, group_id, attempt).exists():
        attempt += 1
    return intermediate_attempt_directory(root, group_id, attempt), attempt


def _refuse_foreign_intermediate_directories(schedule: MergeSchedule, root: Path) -> None:
    known = {group.group_id for group in schedule.groups}
    if not root.is_dir():
        return
    foreign = sorted(
        path.name
        for path in root.iterdir()
        if path.is_dir() and not path.is_symlink() and path.name not in known
    )
    if foreign:
        message = (
            f"{len(foreign)} intermediate directory/directories are present that this schedule "
            f"does not name: {foreign[:8]}. An extra intermediate belongs to some other schedule, "
            "and a finalizer that ignored it would be choosing between two answers silently"
        )
        raise ChunkMultipassError(message)


def resolve_intermediate_inputs(
    plan: ChunkPlan,
    schedule: MergeSchedule,
    *,
    intermediates_root: Path,
    internal_root: Path | None = None,
    external_root: Path | None = None,
    chunk_inputs: Sequence[ChunkInput] | None = None,
) -> tuple[IntermediateInput, ...]:
    """Resolve every group of one schedule to exactly one verified intermediate.

    Every intermediate must belong to ONE coherent execution of ONE schedule of ONE plan, proved
    rather than assumed: the receipt binds this plan's digest and this schedule's digest, names
    exactly the group the schedule assigns it -- identity, ordinal, region and interval -- and
    exactly the input chunks the schedule assigns that group; every intermediate names the same
    source, the same canonical ordering, the same repository revision and the same normalized
    execution contract; the intervals together cover the source exactly once; and no intermediate
    directory the schedule does not name is present. When the chunk roots are given -- or, since
    D151-C15, when the caller hands in the plan's chunks already resolved through the accepted
    single-pass admission -- every bound input chunk receipt is re-read from its one authoritative
    copy and its digest is held to the one the intermediate bound, so an intermediate cannot be
    laundered onto a different set of chunks and a chunk cannot be swapped under an intermediate.
    The artifact set is verified byte-exactly at the point of consumption.

    Raises:
        ChunkMultipassError: any of them.
    """
    _refuse_foreign_intermediate_directories(schedule, intermediates_root)
    inputs: list[IntermediateInput] = []
    head: str | None = None
    tree: str | None = None
    contract: ExecutionContract | None = None
    cursor = 0
    for group in schedule.groups:
        found = completed_intermediate_receipt(intermediates_root, group.group_id)
        _require(
            found is not None,
            f"intermediate {group.group_id!r} has no valid terminal receipt. A missing "
            "intermediate is never treated as empty, skipped, reconstructed or rebuilt here",
        )
        assert found is not None  # noqa: S101 - narrowed by the refusal above
        receipt, directory = found
        _require(
            receipt.plan_digest == plan.plan_digest,
            f"intermediate {group.group_id!r} was built under plan digest {receipt.plan_digest!r}"
            f", not {plan.plan_digest!r}. An intermediate of another partition is never admitted",
        )
        _require(
            receipt.merge_schedule_digest == schedule.schedule_digest,
            f"intermediate {group.group_id!r} was built under merge schedule "
            f"{receipt.merge_schedule_digest!r}, not {schedule.schedule_digest!r}",
        )
        _require(
            (receipt.group_ordinal, receipt.region, receipt.start, receipt.end)
            == (group.ordinal, group.region, group.start, group.end),
            f"intermediate {group.group_id!r} records ordinal {receipt.group_ordinal} "
            f"{receipt.region}[{receipt.start}, {receipt.end}) where the schedule assigns "
            f"ordinal {group.ordinal} {group.region}[{group.start}, {group.end})",
        )
        _require(
            receipt.input_chunk_ids == group.chunk_ids,
            f"intermediate {group.group_id!r} was merged from chunks "
            f"{list(receipt.input_chunk_ids)} where the schedule assigns {list(group.chunk_ids)}",
        )
        _require(
            receipt.source_instance_id == plan.source_instance_id
            and receipt.source_observation_id == plan.source_observation_id
            and receipt.source_sha256 == plan.source_sha256
            and receipt.source_byte_length == plan.source_byte_length
            and receipt.member_order_digest == plan.member_order_digest,
            f"intermediate {group.group_id!r} names a source, observation, artifact or canonical "
            "ordering the plan does not",
        )
        _require(
            receipt.start == cursor,
            f"intermediate {group.group_id!r} starts at {receipt.start} where {cursor} was "
            "required: the admitted intermediates leave a gap or overlap",
        )
        if head is None:
            head, tree = receipt.repository_head_sha, receipt.repository_tree_sha
        _require(
            receipt.repository_head_sha == head and receipt.repository_tree_sha == tree,
            f"intermediate {group.group_id!r} was merged under repository "
            f"{receipt.repository_head_sha}/{receipt.repository_tree_sha} where an earlier one "
            f"was merged under {head}/{tree}",
        )
        if contract is None:
            contract = receipt.execution_contract
        divergence = contract.disagreements(receipt.execution_contract)
        _require(
            not divergence,
            f"intermediate {group.group_id!r} carries a different execution contract than an "
            "earlier intermediate of the same schedule: "
            + "; ".join(
                f"{field} {expected!r} != {observed!r}" for field, expected, observed in divergence
            ),
        )
        if chunk_inputs is not None or internal_root is not None:
            _require_bound_chunk_receipts(
                plan,
                receipt,
                internal_root=internal_root,
                external_root=external_root,
                chunk_inputs=chunk_inputs,
            )
        verify_artifact_manifest(
            directory, receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
        )
        inputs.append(
            IntermediateInput(
                group_id=group.group_id,
                ordinal=group.ordinal,
                region=group.region,
                start=group.start,
                end=group.end,
                directory=directory,
                receipt=receipt,
            )
        )
        cursor = receipt.end
    _require(
        cursor == plan.total_members,
        f"the admitted intermediates cover [0, {cursor}) of {plan.total_members} governed members",
    )
    return tuple(inputs)


def _require_bound_chunk_receipts(
    plan: ChunkPlan,
    receipt: IntermediateReceipt,
    *,
    internal_root: Path | None = None,
    external_root: Path | None = None,
    chunk_inputs: Sequence[ChunkInput] | None = None,
) -> None:
    """Hold an intermediate's bound input chunk receipts to the chunks on disk -- §9, A12.

    Each input chunk is resolved to its ONE authoritative copy -- through the accepted placement
    derivation when the chunk roots are given, or taken from ``chunk_inputs`` when the caller has
    already resolved the whole plan through the accepted single-pass admission, which the level-2
    finalizer does exactly once (D151-C15) -- and the digest of the receipt document found there
    is compared with the one the intermediate bound. Either route refuses two copies that
    disagree, so a chunk present on both tiers is one logical input and never two.
    """
    by_id = None if chunk_inputs is None else {item.chunk_id: item for item in chunk_inputs}
    for chunk_id, bound_sha256, bound_manifest in zip(
        receipt.input_chunk_ids,
        receipt.input_receipt_sha256,
        receipt.input_manifest_digests,
        strict=True,
    ):
        if by_id is not None:
            item = by_id.get(chunk_id)
            if item is None:
                message = (
                    f"intermediate {receipt.group_id!r} binds input chunk {chunk_id!r}, which "
                    "the resolved plan does not carry; refused"
                )
                raise ChunkMultipassError(message)
            directory = item.directory
            chunk_receipt: ChunkReceipt | None = item.receipt
        else:
            if internal_root is None:
                message = (
                    "binding input chunk receipts needs the chunk roots or the resolved chunks"
                )
                raise ChunkMultipassError(message)
            placement = derive_chunk_placement(
                plan, chunk_id, internal_root=internal_root, external_root=external_root
            )
            directory, _tier = authoritative_input(placement)
            chunk_receipt = placement.internal_receipt or placement.external_receipt
        observed, _length = file_sha256(directory / CHUNK_RECEIPT_FILENAME)
        _require(
            observed == bound_sha256
            and chunk_receipt is not None
            and chunk_receipt.manifest.digest == bound_manifest,
            f"intermediate {receipt.group_id!r} bound input chunk {chunk_id!r} by receipt "
            f"digest {bound_sha256!r} and manifest {bound_manifest!r}, and the chunk's one "
            f"authoritative copy now carries receipt digest {observed!r}. An intermediate is "
            "never admitted over inputs other than the ones it was merged from",
        )


# --------------------------------------------------------------------------- #
# Requests -- what a merge child process is handed, and the only thing it is handed
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class GroupMergeRequest:
    """Everything one level-1 group merge process is given."""

    plan_path: str
    schedule_path: str
    group_id: str
    attempt: int
    attempt_directory: str
    internal_root: str
    external_root: str | None
    operational_catalog: str
    cache_bytes: int | None
    repository_head_sha: str
    repository_tree_sha: str
    storage_requirements: Mapping[str, object]
    expected_sqlite_temp_binding: Mapping[str, object]
    kind: str = MULTIPASS_REQUEST_KIND_GROUP

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Paths are the caller's; nothing is discovered."""
        return {
            "kind": self.kind,
            "plan_path": self.plan_path,
            "schedule_path": self.schedule_path,
            "group_id": self.group_id,
            "attempt": self.attempt,
            "attempt_directory": self.attempt_directory,
            "internal_root": self.internal_root,
            "external_root": self.external_root,
            "operational_catalog": self.operational_catalog,
            "cache_bytes": self.cache_bytes,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "storage_requirements": dict(self.storage_requirements),
            "expected_sqlite_temp_binding": dict(self.expected_sqlite_temp_binding),
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> GroupMergeRequest:
        """Rebuild a request from its stored mapping.

        Raises:
            ChunkMultipassError: a field is absent or is not of the recorded type.
        """
        try:
            cache = record["cache_bytes"]
            external = record["external_root"]
            storage = record["storage_requirements"]
            expected = record["expected_sqlite_temp_binding"]
            if not isinstance(storage, Mapping) or not isinstance(expected, Mapping):
                message = (
                    "a group merge request's storage requirements or expected temp binding are "
                    "not mappings"
                )
                raise ChunkMultipassError(message)
            return cls(
                kind=str(record["kind"]),
                plan_path=str(record["plan_path"]),
                schedule_path=str(record["schedule_path"]),
                group_id=str(record["group_id"]),
                attempt=_stored_int(record["attempt"], "attempt"),
                attempt_directory=str(record["attempt_directory"]),
                internal_root=str(record["internal_root"]),
                external_root=None if external is None else str(external),
                operational_catalog=str(record["operational_catalog"]),
                cache_bytes=None if cache is None else _stored_int(cache, "cache_bytes"),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                storage_requirements={str(key): value for key, value in storage.items()},
                expected_sqlite_temp_binding={str(key): value for key, value in expected.items()},
            )
        except KeyError as exc:
            message = f"a group merge request could not be read as this build writes them: {exc}"
            raise ChunkMultipassError(message) from exc


@dataclass(frozen=True, slots=True)
class FinalMergeRequest:
    """Everything the level-2 finalization process is given."""

    plan_path: str
    schedule_path: str
    intermediates_root: str
    internal_root: str
    external_root: str | None
    operational_catalog: str
    world_directory: str
    run_id: str
    cache_bytes: int | None
    repository_head_sha: str
    repository_tree_sha: str
    storage_requirements: Mapping[str, object]
    expected_sqlite_temp_binding: Mapping[str, object]
    capacity_observations: tuple[Mapping[str, object], ...] = ()
    kind: str = MULTIPASS_REQUEST_KIND_FINAL

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "kind": self.kind,
            "plan_path": self.plan_path,
            "schedule_path": self.schedule_path,
            "intermediates_root": self.intermediates_root,
            "internal_root": self.internal_root,
            "external_root": self.external_root,
            "operational_catalog": self.operational_catalog,
            "world_directory": self.world_directory,
            "run_id": self.run_id,
            "cache_bytes": self.cache_bytes,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "storage_requirements": dict(self.storage_requirements),
            "expected_sqlite_temp_binding": dict(self.expected_sqlite_temp_binding),
            "capacity_observations": [dict(item) for item in self.capacity_observations],
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> FinalMergeRequest:
        """Rebuild a request from its stored mapping.

        Raises:
            ChunkMultipassError: a field is absent or is not of the recorded type.
        """
        try:
            cache = record["cache_bytes"]
            external = record["external_root"]
            storage = record["storage_requirements"]
            observations = record["capacity_observations"]
            expected = record["expected_sqlite_temp_binding"]
            if (
                not isinstance(storage, Mapping)
                or not isinstance(observations, list)
                or not isinstance(expected, Mapping)
            ):
                message = (
                    "a final merge request's storage, binding or observations are not of shape"
                )
                raise ChunkMultipassError(message)
            return cls(
                kind=str(record["kind"]),
                plan_path=str(record["plan_path"]),
                schedule_path=str(record["schedule_path"]),
                intermediates_root=str(record["intermediates_root"]),
                internal_root=str(record["internal_root"]),
                external_root=None if external is None else str(external),
                operational_catalog=str(record["operational_catalog"]),
                world_directory=str(record["world_directory"]),
                run_id=str(record["run_id"]),
                cache_bytes=None if cache is None else _stored_int(cache, "cache_bytes"),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                storage_requirements={str(key): value for key, value in storage.items()},
                expected_sqlite_temp_binding={str(key): value for key, value in expected.items()},
                capacity_observations=tuple(
                    {str(key): value for key, value in item.items()}
                    for item in observations
                    if isinstance(item, Mapping)
                ),
            )
        except KeyError as exc:
            message = f"a final merge request could not be read as this build writes them: {exc}"
            raise ChunkMultipassError(message) from exc


def _authenticate_running_repository(*, head: str, tree: str, label: str) -> RepositoryIdentity:
    """Measure the repository THIS process imported its code from, and hold the request to it.

    The accepted derivation, exactly as the chunk child applies it (D151-C5 MINOR-2): the request
    names the commit and tree the coordinator believes the merge runs under, and the merge process
    measures its own and refuses any other, before anything is created.

    Raises:
        RepositoryIdentityError: the working tree is not clean, or the identity cannot be derived.
        ChunkMultipassError: the measured identity is not the one the request names.
    """
    identity = require_clean_running_repository()
    if (identity.head_sha, identity.tree_sha) != (head, tree):
        message = (
            f"merge {label!r} was asked to execute under repository {head}/{tree} and the code "
            f"this process actually imported is {identity.head_sha}/{identity.tree_sha}. The "
            "identity is MEASURED by the merge process itself; the merge is refused before "
            "anything is created"
        )
        raise ChunkMultipassError(message)
    return identity


def _read_plan_and_schedule(plan_path: str, schedule_path: str) -> tuple[ChunkPlan, MergeSchedule]:
    plan = ChunkPlan.from_record(_read_json_object(Path(plan_path), "multipass chunk plan"))
    require_multipass_plan(plan)
    schedule = MergeSchedule.from_record(_read_json_object(Path(schedule_path), "merge schedule"))
    require_sealed_schedule(schedule, plan)
    return plan, schedule


def select_group_inputs(inputs: Sequence[ChunkInput], group: MergeGroup) -> tuple[ChunkInput, ...]:
    """This group's inputs, in group order, out of a whole plan's resolved chunks.

    Raises:
        ChunkMultipassError: an input the group names is absent, or the selection is not the
            contiguous, region-homogeneous interval the group records.
    """
    by_id = {item.chunk_id: item for item in inputs}
    _require(
        len(by_id) == len(inputs),
        "the resolved chunk inputs repeat a chunk identity; exactly one logical input per chunk "
        "participates in a merge, whatever physical copies exist",
    )
    selected: list[ChunkInput] = []
    cursor = group.start
    for chunk_id in group.chunk_ids:
        _require(chunk_id in by_id, f"group {group.group_id!r} names chunk {chunk_id!r}, absent")
        item = by_id[chunk_id]
        _require(
            item.region == group.region,
            f"group {group.group_id!r} is a {group.region} group and chunk {chunk_id!r} is a "
            f"{item.region} chunk; a level-1 group is region-homogeneous by construction",
        )
        _require(
            item.start == cursor,
            f"chunk {chunk_id!r} starts at {item.start} where group {group.group_id!r} required "
            f"{cursor}: the group's inputs are not one contiguous interval",
        )
        selected.append(item)
        cursor = item.end
    _require(
        cursor == group.end,
        f"group {group.group_id!r}'s inputs cover [{group.start}, {cursor}) where the schedule "
        f"records [{group.start}, {group.end})",
    )
    return tuple(selected)


def _require_seed_identity(
    *,
    label: str,
    repository: RepositoryIdentity,
    recorded_head: str,
    recorded_tree: str,
    contract: ExecutionContract,
    catalog_sha256: str,
) -> None:
    _require(
        repository.head_sha == recorded_head and repository.tree_sha == recorded_tree,
        f"the inputs of {label!r} executed under repository {recorded_head}/{recorded_tree} and "
        f"this merge is running from {repository.head_sha}/{repository.tree_sha}, measured from "
        "the checkout this code was imported from. Nothing was merged",
    )
    _require(
        catalog_sha256 == contract.catalog_source_sha256,
        f"the accepted catalog this merge would seed from digests to {catalog_sha256!r} and every "
        f"input executed against {contract.catalog_source_sha256!r}; the seed is identified by "
        "its BYTES, never by its path",
    )


def _admit_merge_step(
    *,
    step: str,
    level: str,
    target: Path,
    input_bytes: int,
    seed_catalog_bytes: int,
    peak_ratio: float,
    requirements: MultipassStorageRequirements,
) -> MergeAdmission:
    """The load-bearing storage gate, run BEFORE the step's world directory exists -- §20.

    ``level`` is required and is not inferred from ``step``: it selects this step's own transient
    allowance through :meth:`MultipassStorageRequirements.transient_for`, which has no fallback
    between levels (D151-C17 R5).
    """
    requirement = merge_step_requirement(
        step=step,
        level=level,
        input_bytes=input_bytes,
        seed_catalog_bytes=seed_catalog_bytes,
        peak_ratio=peak_ratio,
        requirements=requirements,
    )
    return require_merge_admission(
        free_bytes=internal_free_bytes(_nearest_existing(target)), requirement=requirement
    )


def _require_expected_binding(
    measured: SqliteTempBinding, expected: Mapping[str, object], *, label: str
) -> SqliteTempBinding:
    """Hold THIS process's measured binding to the one the consolidation was admitted on -- C19 §14.

    The request carries the orchestrator's measurement as the expected topology. It is a claim
    about the past, never a proof about this process: the proof is the measurement this process
    just took, and the two must agree field for field. A changed ``SQLITE_TMPDIR`` (a different
    directory identity), a changed volume, a forged record or a pre-C19 record refuses, before
    any world, attempt directory or database exists. Nothing in the request can assert equality;
    it can only be contradicted by what was measured.
    """
    expected_binding = SqliteTempBinding.from_record(expected)
    _require(
        measured == expected_binding,
        f"merge {label!r} measured a SQLite temporary binding that is not the one this "
        f"consolidation was admitted on (measured {dict(measured.as_record())}, expected "
        f"{dict(expected_binding.as_record())}); refused BEFORE any world exists, because a "
        "child that continued on the parent's word would be trusting a claim it had just "
        "contradicted",
    )
    return measured


def _record_storage_plan(path: Path, storage_plan: MultipassStoragePlan) -> None:
    """Write the sealed storage plan once; on restart, require the recorded one to be compatible.

    Two questions, in order, and they are different questions (D151-C21 R4):

    1. **Is the recorded document exactly what was sealed?** It is read back through
       :meth:`~disclosure_drift.m3.chunk_tiering.MultipassStoragePlan.from_document`, which
       refuses a superseded ``/1`` contract, an unknown contract, a record whose fields do not
       rebuild, a stale or edited record -- an attachment-instance field edited without
       resealing included -- and a smuggled field. Every one of its eight binding fields is
       inside that seal.
    2. **May this restart continue on it?** The recorded plan and the plan this consolidation
       just computed are compared by
       :meth:`~disclosure_drift.m3.chunk_tiering.MultipassStoragePlan.restart_compatibility`:
       every storage term, every input, and the binding's restart-stable fields -- the temporary
       root's inode and both volumes' UUID and filesystem type. The three attach-time
       identifiers (``st_dev``, ``diskNsM``) are the only fields excluded, because the same
       volume re-attached after a reboot or re-plug legitimately reports new ones. A changed
       temporary root, a recreated directory, a different volume or a changed term refuses
       here, before any child is started.

    The document is never rewritten or upgraded in place. The restarting orchestrator carries
    its OWN fresh measurement forward to every child it launches.
    """
    if path.exists():
        existing = MultipassStoragePlan.from_document(_read_json_object(path, "storage plan"))
        recorded = existing.restart_compatibility()
        current = storage_plan.restart_compatibility()
        differing = sorted(
            key for key in set(recorded) | set(current) if recorded.get(key) != current.get(key)
        )
        _require(
            recorded == current,
            f"the storage plan already recorded at {path.name!r} is not the one this "
            f"consolidation was given, by restart compatibility (differing: {differing}; "
            f"recorded identity {existing.identity()}, this run {storage_plan.identity()}); a "
            "restart continues exactly the recorded consolidation -- its terms, its inputs and "
            "the stable identity of its SQLite temporary binding -- or refuses. Attach-time "
            "device identifiers are sealed in the record and are not what decides this",
        )
        return
    write_once_json(path, dict(storage_plan.as_document()))


# --------------------------------------------------------------------------- #
# Level 1 -- the group merge, INSIDE its own process
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _GroupEvidence:
    members: int
    records: int
    omitted: int
    materialized: int
    member_manifest_digest: str
    witness_ledger_identity: str
    compact_evidence_identity: str
    evidence_members_corrected: int
    evidence_delta: int


def _merge_group_evidence(
    *, attempt_root: Path, inputs: Sequence[ChunkInput], group: MergeGroup, plan: ChunkPlan
) -> _GroupEvidence:
    """The intermediate's reduced compact evidence and reduced witness ledger -- §28, §29.

    The accepted within-group member-delta correction is applied to the inputs' member manifest
    rows exactly as the single-pass sidecar merge applies it across chunks, restricted to this
    group's interval -- so every row that is not the group's first witness of its identity
    downgrades its member here. The reduced ledger then retains ONE row per native identity: the
    group's first witness, with its canonical member ordinal, record ordinal and delta. That is
    the minimum level 2 needs to decide, across intermediates, which group winners lose globally
    and what each such loss costs its member -- and it is exactly the set the single-pass merge
    would still have needed to rank. No source row is written: an intermediate carries no
    completeness digest and claims no source-level evidence.
    """
    sidecar_path = attempt_root / COMPACT_EVIDENCE_SIDECAR_FILENAME
    witness_path = attempt_root / INTERMEDIATE_WITNESS_FILENAME
    CompactEvidenceSidecar(sidecar_path).close()
    ledger = sqlite3.connect(witness_path, isolation_level=None)
    try:
        ledger.executescript(_WITNESS_SCHEMA)
    finally:
        ledger.close()
    connection = sqlite3.connect(f"file:{sidecar_path}", uri=True, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        witness_aliases = _attach_all(connection, [item.witness_path for item in inputs], "w")
        connection.execute(f"ATTACH DATABASE 'file:{witness_path.resolve()}' AS iw")
        try:
            corrected = _member_deltas(connection, witness_aliases)
            union = _union_all(
                witness_aliases,
                "chunk_first_witness",
                "native_identity, member_ordinal, record_ordinal, delta_materialized",
            )
            connection.execute(
                "INSERT INTO iw.chunk_first_witness (native_identity, member_ordinal, "  # noqa: S608
                "record_ordinal, delta_materialized) "
                "WITH ranked AS ("
                "  SELECT native_identity, member_ordinal, record_ordinal, delta_materialized,"
                "    ROW_NUMBER() OVER (PARTITION BY native_identity "
                "                       ORDER BY member_ordinal, record_ordinal) AS rn"
                f"  FROM ({union}))"
                "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                "FROM ranked WHERE rn = 1 ORDER BY native_identity"
            )
            connection.executemany(
                "INSERT INTO iw.chunk_witness_meta (key, value) VALUES (?, ?)",
                [
                    ("level", "1"),
                    ("group_id", group.group_id),
                    ("plan_digest", plan.plan_digest),
                    ("region", group.region),
                    ("start", str(group.start)),
                    ("end", str(group.end)),
                ],
            )
            digest = hashlib.sha256()
            digest.update(f"{INTERMEDIATE_RECEIPT_CONTRACT}\x1f{group.group_id}".encode())
            digest.update(b"\x1e")
            for row in connection.execute(
                "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                "FROM iw.chunk_first_witness ORDER BY native_identity"
            ):
                digest.update(
                    "\x1f".join(
                        (
                            str(row["native_identity"]),
                            str(row["member_ordinal"]),
                            str(row["record_ordinal"]),
                            str(row["delta_materialized"]),
                        )
                    ).encode("utf-8")
                )
                digest.update(b"\x1e")
            ledger_identity = digest.hexdigest()
        finally:
            connection.execute("DETACH DATABASE iw")
            _detach_all(connection, witness_aliases)
        sidecar_aliases = _attach_all(connection, [item.sidecar_path for item in inputs], "s")
        try:
            columns = _columns(connection, "compact_source_members")
            projection = ", ".join(columns)
            corrected_projection = ", ".join(
                "materialized_field_observations + COALESCE(d.delta, 0)"
                if column == "materialized_field_observations"
                else (
                    "omitted_field_observations - COALESCE(d.delta, 0)"
                    if column == "omitted_field_observations"
                    else f"m.{column}"
                )
                for column in columns
            )
            members_union = _union_all(sidecar_aliases, "compact_source_members", projection)
            connection.execute(
                f"INSERT INTO main.compact_source_members ({projection}) "  # noqa: S608
                f"SELECT {corrected_projection} FROM ({members_union}) AS m "
                "LEFT JOIN chunk_member_delta AS d ON d.member_ordinal = m.member_ordinal "
                "ORDER BY m.member_ordinal"
            )
        finally:
            _detach_all(connection, sidecar_aliases)
        summary = connection.execute(
            "SELECT COUNT(*) AS n, COUNT(DISTINCT member_ordinal) AS d, "
            "MIN(member_ordinal) AS lo, MAX(member_ordinal) AS hi, "
            "SUM(parsed_registrants + parsed_accessions + parsed_other) AS records, "
            "SUM(omitted_field_observations) AS omitted, "
            "SUM(materialized_field_observations) AS materialized "
            "FROM main.compact_source_members"
        ).fetchone()
        total = int(summary["n"])
        _require(
            total == int(summary["d"]),
            "the intermediate's member manifest repeats a member ordinal; two inputs absorbed "
            "the same member and the merge is refused",
        )
        _require(
            total == group.member_count
            and int(summary["lo"]) == group.start
            and int(summary["hi"]) == group.end - 1,
            f"the intermediate's member manifest holds {total} members over "
            f"[{summary['lo']}, {summary['hi']}] where the group covers {group.member_count} "
            f"over [{group.start}, {group.end - 1}]",
        )
        _require(
            int(summary["omitted"]) >= 0,
            "a first-witness correction drove a member's omitted-observation count below zero, "
            "which cannot be true of any real parse. The merge is refused, not clamped",
        )
        totals = (
            total,
            int(summary["records"] or 0),
            int(summary["omitted"] or 0),
            int(summary["materialized"] or 0),
        )
    finally:
        connection.close()
    reopened = CompactEvidenceSidecar(sidecar_path)
    try:
        manifest_digest = reopened.member_manifest_digest(plan.source_observation_id)
        evidence_identity = reopened.identity()
    finally:
        reopened.close()
    return _GroupEvidence(
        members=totals[0],
        records=totals[1],
        omitted=totals[2],
        materialized=totals[3],
        member_manifest_digest=manifest_digest,
        witness_ledger_identity=ledger_identity,
        compact_evidence_identity=evidence_identity,
        evidence_members_corrected=corrected[0],
        evidence_delta=corrected[1],
    )


def merge_group_body(request: GroupMergeRequest) -> IntermediateReceipt:  # noqa: PLR0915
    """Merge exactly one level-1 group into one immutable intermediate, receipt LAST -- §§8, 9, 26.

    Every predicate is re-established here, in the process that does the work: the real multipass
    authority is required FIRST (D151-C15 R2), before anything is read or created; the code
    identity is measured and held to the request; the plan is re-read, re-sealed and required to be
    a multipass plan; the schedule is re-read, re-sealed and re-derived from the plan; every chunk
    of the whole plan is resolved through the accepted single-pass admission and this group's
    inputs are selected from that set and proved to be its contiguous, region-homogeneous
    interval; the seed catalog is identified by digest; the storage step is admitted BEFORE the
    attempt directory exists. The merge then runs the accepted primitives -- reduced parser run,
    key-sorted bulk loads, first/last reductions, the SET-BASED first-witness correction, the
    observation load, index rebuild -- and NONE of the whole-observation derivations, no parser
    state, no ``parsed`` ledger mark, no checkpoint and no final receipt: an intermediate is
    nonterminal by construction. The reduced sidecar and reduced witness ledger are then built,
    every input is re-verified unchanged, and the intermediate receipt is written LAST.

    Raises:
        RepositoryIdentityError: the checkout this code runs from is dirty or unidentifiable.
        ChunkMultipassError: any multipass precondition fails.
        ChunkPlanError: the plan is not its sealed self.
        ChunkConsolidationError, ChunkStorageError, ChunkEvidenceError: a chunk input refuses.
        ChunkTieringError: the storage step is not admitted.
    """
    require_real_multipass_authority()
    repository = _authenticate_running_repository(
        head=request.repository_head_sha, tree=request.repository_tree_sha, label=request.group_id
    )
    attempt_root = Path(request.attempt_directory)
    if attempt_root.exists():
        message = (
            f"intermediate attempt directory {attempt_root.name!r} already exists; an attempt is "
            "create-once. A previous attempt is left exactly as it is and a retry builds a new "
            "directory beside it -- nothing is reused, repaired, cleaned or deleted"
        )
        raise ChunkMultipassError(message)
    plan, schedule = _read_plan_and_schedule(request.plan_path, request.schedule_path)
    require_chunkable_source(plan.source_id)
    group = group_by_id(schedule, request.group_id)
    requirements = MultipassStorageRequirements.from_record(request.storage_requirements)
    # D151-C17 R6, at the stated position: storage requirements, then the temp binding, then
    # everything expensive. This process proves for ITSELF that SQLite's spill lands on the
    # filesystem the admission below charges; a child that trusted its parent's word would be
    # trusting a claim it had not measured.
    _require_expected_binding(
        require_sqlite_temp_binding(charged_path=attempt_root),
        request.expected_sqlite_temp_binding,
        label=group.group_id,
    )
    operational_catalog = Path(request.operational_catalog)
    catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    started = utc_now()
    rss_before = process_peak_resident_bytes()
    every = resolve_chunk_inputs(
        plan,
        internal_root=Path(request.internal_root),
        external_root=None if request.external_root is None else Path(request.external_root),
    )
    inputs = select_group_inputs(every, group)
    require_attachable(len(inputs))
    contract = inputs[0].receipt.execution_contract
    _require_seed_identity(
        label=group.group_id,
        repository=repository,
        recorded_head=inputs[0].receipt.repository_head_sha,
        recorded_tree=inputs[0].receipt.repository_tree_sha,
        contract=contract,
        catalog_sha256=catalog_sha256,
    )
    admission = _admit_merge_step(
        step=group.group_id,
        level=MERGE_LEVEL_ONE,
        target=attempt_root,
        input_bytes=sum(item.receipt.manifest.total_bytes for item in inputs),
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_one_peak_ratio,
        requirements=requirements,
    )
    attempt_root.mkdir(mode=_DIRECTORY_MODE, parents=True)
    with WorkingCatalog(
        operational_catalog, attempt_root, cache_bytes=request.cache_bytes
    ) as world:
        connection = world.connection
        _require(
            world.identity.migration_head == contract.migration_head,
            f"the intermediate was seeded at migration head {world.identity.migration_head} "
            f"where every input executed at {contract.migration_head}",
        )
        world.ledger.begin_source(plan.source_instance_id, plan.source_id)
        aliases = _attach_all(connection, [item.catalog_path for item in inputs], "k")
        try:
            indexes = _deferrable_indexes(connection)
            for name, _sql in indexes:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            with transaction(connection):
                with write_containment(connection):
                    reduced = _reduced_parser_run(connection, aliases, contract=contract)
                    for table in _LOAD_ORDER:
                        if table == "census_accession_observations":
                            continue
                        if _MERGE_STRATEGY[table] == "keyed_first_last":
                            _keyed_first_last_load(connection, table, aliases)
                        else:
                            _sorted_bulk_load(connection, table, aliases)
                corrected, staged_rows = stage_first_witness_corrections(connection, aliases)
                with write_containment(connection):
                    _load_accession_observations(connection, aliases)
            for _name, sql in indexes:
                connection.execute(sql)
            counts = table_row_counts(connection)
        finally:
            _detach_all(connection, aliases)
    evidence = _merge_group_evidence(
        attempt_root=attempt_root, inputs=inputs, group=group, plan=plan
    )
    for item in inputs:
        verify_artifact_manifest(
            item.directory,
            item.receipt.manifest,
            exclude=(CHUNK_RECEIPT_FILENAME, "transfer_receipt.json"),
        )
    write_once_json(attempt_root / CHUNK_PLAN_FILENAME, dict(plan.as_record()))
    write_once_json(attempt_root / MERGE_SCHEDULE_FILENAME, dict(schedule.as_record()))
    manifest = build_artifact_manifest(attempt_root, exclude=(INTERMEDIATE_RECEIPT_FILENAME,))
    catalog_entry = next(
        entry for entry in manifest.entries if entry.relative_path == WORKING_CATALOG_FILENAME
    )
    receipt = IntermediateReceipt(
        contract=INTERMEDIATE_RECEIPT_CONTRACT,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_id=group.group_id,
        group_ordinal=group.ordinal,
        region=group.region,
        start=group.start,
        end=group.end,
        input_chunk_ids=tuple(item.chunk_id for item in inputs),
        input_receipt_sha256=tuple(
            file_sha256(item.directory / CHUNK_RECEIPT_FILENAME)[0] for item in inputs
        ),
        input_manifest_digests=tuple(item.receipt.manifest.digest for item in inputs),
        chunk_inputs=tuple(dict(item.as_record()) for item in inputs),
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        source_byte_length=plan.source_byte_length,
        member_order_digest=plan.member_order_digest,
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        execution_contract=contract,
        parser_run_id=reduced.parser_run_id,
        catalog_sha256=catalog_entry.sha256,
        table_row_counts=counts,
        members=evidence.members,
        records=evidence.records,
        omitted_field_observations=evidence.omitted,
        materialized_field_observations=evidence.materialized,
        member_manifest_digest=evidence.member_manifest_digest,
        witness_ledger_identity=evidence.witness_ledger_identity,
        compact_evidence_identity=evidence.compact_evidence_identity,
        first_witness_accessions_corrected=corrected,
        first_witness_rows_staged=staged_rows,
        evidence_members_corrected=evidence.evidence_members_corrected,
        evidence_delta=evidence.evidence_delta,
        storage_admission=dict(admission.as_record()),
        earliest_input_started_at_utc=min(item.receipt.started_at_utc for item in inputs),
        attempt=request.attempt,
        pid=os.getpid(),
        rss_peak_bytes=process_peak_resident_bytes() or rss_before,
        started_at_utc=started,
        completed_at_utc=utc_now(),
        manifest=manifest,
        status="complete",
    )
    # LAST. Nothing is written after this, and nothing that fails before it leaves one.
    write_once_json(attempt_root / INTERMEDIATE_RECEIPT_FILENAME, dict(receipt.as_record()))
    return receipt


# --------------------------------------------------------------------------- #
# Level 2 -- the finalization, INSIDE its own process
# --------------------------------------------------------------------------- #
def finalize_multipass_body(request: FinalMergeRequest) -> FinalWorldReceipt:  # noqa: PLR0915
    """Build ONE canonical F0 world from every validated intermediate, receipt LAST -- §§10, 12.

    The sequence is the single-pass consolidator's, over intermediates instead of chunks, with
    the set-based correction performing the additive global loser upgrade at step 8:

    0. the real multipass authority is required FIRST (D151-C15 R2), before anything is read;
    1. the code identity is measured and held to the request; the plan and the schedule are
       re-read, re-sealed and re-derived; the storage terms are read;
    2. every chunk of the plan is resolved exactly once through the accepted single-pass
       admission; every intermediate is resolved to exactly one verified copy, proved to belong
       to this plan and this schedule, proved to cover the source exactly once, and its bound
       input chunk receipts are held to those resolved chunks;
    3. the intermediates' repository identity is required to be THIS checkout's, and the seed
       catalog is required by digest to be the one every input copied;
    4. the accepted plan state is derived; the storage step is admitted BEFORE the world exists;
    5. the final world is created from the accepted operational catalog;
    6. every intermediate's catalog is attached immutably; 7. the indexes are dropped;
    8. the reduced parser run, the key-sorted loads, the accepted duplicate-identity pass, the
       SET-BASED global loser upgrade and the observation load run under the accepted containment;
    9. the two accepted whole-observation derivations run ONCE; 10. the indexes are rebuilt, and
       the four whole-F0 correction counters are derived over the plan's chunks (D151-C15 R1);
    11. the sidecar is merged through the accepted sidecar merge -- cross-group member deltas,
        contiguity, the completeness digest replayed over canonical member order -- BEFORE the
        gate; 12. the accepted D140-R12 gate is applied over the complete derived outcome;
    13. only then is the ledger marked parsed; 14. every intermediate is re-verified unchanged;
    15. the F0 checkpoint is written from the mechanically derived payload; 16. the final receipt
        is written LAST, under the accepted final-receipt contract.

    Raises:
        RepositoryIdentityError, ChunkMultipassError, ChunkPlanError, ChunkTieringError,
        ChunkEvidenceError: a precondition fails.
        SingleSourceCanaryError: the consolidated F0 reached a blocking terminal.
    """
    require_real_multipass_authority()
    repository = _authenticate_running_repository(
        head=request.repository_head_sha, tree=request.repository_tree_sha, label="final"
    )
    plan, schedule = _read_plan_and_schedule(request.plan_path, request.schedule_path)
    require_chunkable_source(plan.source_id)
    requirements = MultipassStorageRequirements.from_record(request.storage_requirements)
    # D151-C17 R6, measured in THIS process, before anything is resolved or created; C19 §14,
    # held to the binding the consolidation was admitted on.
    _require_expected_binding(
        require_sqlite_temp_binding(charged_path=Path(request.world_directory)),
        request.expected_sqlite_temp_binding,
        label="final",
    )
    operational_catalog = Path(request.operational_catalog)
    catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    # The plan's chunks, resolved ONCE through the accepted single-pass admission -- the twelve
    # refusals and the byte-exact manifest verification -- so that the intermediates are bound to
    # that resolution and the whole-F0 counters are derived over it (D151-C15 R1).
    chunks = resolve_chunk_inputs(
        plan,
        internal_root=Path(request.internal_root),
        external_root=None if request.external_root is None else Path(request.external_root),
    )
    intermediates = resolve_intermediate_inputs(
        plan, schedule, intermediates_root=Path(request.intermediates_root), chunk_inputs=chunks
    )
    require_attachable(len(intermediates))
    contract = intermediates[0].receipt.execution_contract
    _require_seed_identity(
        label="final",
        repository=repository,
        recorded_head=intermediates[0].receipt.repository_head_sha,
        recorded_tree=intermediates[0].receipt.repository_tree_sha,
        contract=contract,
        catalog_sha256=catalog_sha256,
    )
    state = _accepted_plan_state(operational_catalog, plan)
    started_at_utc = min(item.receipt.earliest_input_started_at_utc for item in intermediates)
    world_directory = Path(request.world_directory)
    if world_directory.exists():
        message = (
            f"the consolidated world {world_directory.name!r} already exists; a final world is "
            "create-once and is never reused, resumed, repaired, or overwritten"
        )
        raise ChunkMultipassError(message)
    admission = _admit_merge_step(
        step="final",
        level=MERGE_LEVEL_TWO,
        target=world_directory,
        input_bytes=sum(item.receipt.manifest.total_bytes for item in intermediates),
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_two_peak_ratio,
        requirements=requirements,
    )
    free_before = admission.free_bytes
    world_directory.mkdir(mode=_DIRECTORY_MODE, parents=True)
    with WorkingCatalog(
        operational_catalog, world_directory, cache_bytes=request.cache_bytes
    ) as world:
        connection = world.connection
        _require(
            world.identity.migration_head == contract.migration_head,
            f"the final world was seeded at migration head {world.identity.migration_head} where "
            f"every input executed at {contract.migration_head}",
        )
        world.ledger.begin_source(plan.source_instance_id, plan.source_id)
        aliases = _attach_all(connection, [item.catalog_path for item in intermediates], "k")
        try:
            indexes = _deferrable_indexes(connection)
            for name, _sql in indexes:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            with transaction(connection):
                with write_containment(connection):
                    reduced = _reduced_parser_run(connection, aliases, contract=contract)
                    for table in _LOAD_ORDER:
                        if table == "census_accession_observations":
                            continue
                        if _MERGE_STRATEGY[table] == "keyed_first_last":
                            _keyed_first_last_load(connection, table, aliases)
                        else:
                            _sorted_bulk_load(connection, table, aliases)
                    _apply_duplicate_identities(connection, reduced)
                # The additive global loser upgrade -- outside the containment, because it lands
                # in run-local TEMP tables that are not accepted catalog tables. Its counts are
                # this LEVEL's operation counts and are not the receipt's (D151-C15 R1).
                _l2_corrected, _l2_staged = stage_first_witness_corrections(connection, aliases)
                with write_containment(connection):
                    _load_accession_observations(connection, aliases)
                    CensusCatalog._candidate_edges(  # noqa: SLF001 - the accepted derivation
                        connection, plan.source_observation_id, kind="company_name"
                    )
                    CensusCatalog._candidate_edges(  # noqa: SLF001
                        connection, plan.source_observation_id, kind="ticker"
                    )
                    CensusCatalog._mark_accession_conflicts(connection)  # noqa: SLF001
                    connection.execute(
                        "UPDATE census_plan_sources SET parser_state = ? "
                        "WHERE source_instance_id = ?",
                        (reduced.parser_state, plan.source_instance_id),
                    )
            for _name, sql in indexes:
                connection.execute(sql)
            counts = table_row_counts(connection)
        finally:
            _detach_all(connection, aliases)
        # The four whole-F0 correction counters, over the plan's chunks -- D151-C15 R1. Derived
        # once the intermediates are detached, so the attachment budget is the chunks' alone.
        plan_counters = _plan_first_witness_counters(connection, chunks)
        # The accepted sidecar merge, over intermediates: the cross-group member deltas, the
        # contiguity of the whole manifest, the completeness digest replayed over canonical
        # member order, and the source row -- BEFORE the gate, at the accepted position. Its
        # member-delta pair is this LEVEL's and is not the receipt's (D151-C15 R1).
        completeness, manifest_digest, totals, _level_two_evidence = _merge_sidecar(
            sidecar_path=world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME,
            inputs=cast("Sequence[ChunkInput]", intermediates),
            plan=plan,
            source_id=plan.source_id,
        )
        outcome = derived_f0_outcome(
            plan=plan,
            state=state,
            reduced=reduced,
            members=totals["members"],
            records=totals["records"],
            omitted=totals["omitted"],
            materialized=totals["materialized"],
            completeness_digest=completeness,
        )
        # D140-R12, at the accepted position, by the accepted predicate. Nothing below this line
        # runs for a blocking terminal -- not the ledger, not the checkpoint, not the receipt.
        require_f0_success(outcome)
        world.ledger.mark_parsed(
            plan.source_instance_id, parts=plan.total_members, batches=reduced.parsed
        )
    for item in intermediates:
        verify_artifact_manifest(
            item.directory, item.receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
        )
    checkpoint = PhaseCheckpoint(
        contract=PHASE_RESTART_CONTRACT,
        phase=PHASE_F0,
        status=PHASE_STATUS_COMPLETE,
        run_id=request.run_id,
        source_instance_id=plan.source_instance_id,
        execution_identity=phase_execution_identity(
            repository=repository, batch_size=contract.batch_size
        ),
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        catalog_source_sha256=contract.catalog_source_sha256,
        migration_head=contract.migration_head,
        plan_fingerprint=state.plan_fingerprint,
        completed_at_utc=utc_now(),
        pid=os.getpid(),
        rss_peak_bytes_at_start=None,
        rss_peak_bytes_at_terminal=process_peak_resident_bytes(),
        payload=dict(
            derived_f0_payload(
                outcome=outcome,
                state=state,
                plan=plan,
                started_at_utc=started_at_utc,
                catalog_source_sha256=contract.catalog_source_sha256,
                work_root_free_bytes_before=free_before,
                capacity_observations=request.capacity_observations,
            )
        ),
    )
    ledger = RunProgressLedger(world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        write_phase_checkpoint(ledger, checkpoint)
    finally:
        ledger.close()
    manifest = build_artifact_manifest(world_directory, exclude=(FINAL_WORLD_RECEIPT_FILENAME,))
    chunk_inputs: list[Mapping[str, object]] = []
    for item in intermediates:
        chunk_inputs.extend(item.receipt.chunk_inputs)
    receipt = FinalWorldReceipt(
        contract=FINAL_WORLD_RECEIPT_CONTRACT,
        consolidation_contract=MULTIPASS_CONSOLIDATION_CONTRACT,
        plan_digest=plan.plan_digest,
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        catalog_source_sha256=contract.catalog_source_sha256,
        execution_contract_identity=contract.contract_identity,
        chunk_count=plan.chunk_count,
        chunk_inputs=tuple(dict(item) for item in chunk_inputs),
        chunks_unchanged=True,
        parser_run_id=reduced.parser_run_id,
        run_outcome=reduced.outcome,
        parser_state_after=reduced.parser_state,
        members=totals["members"],
        records=totals["records"],
        parsed_records=reduced.parsed,
        quarantined_records=reduced.quarantined,
        omitted_field_observations=totals["omitted"],
        materialized_field_observations=totals["materialized"],
        completeness_digest=completeness,
        member_manifest_digest=manifest_digest,
        table_row_counts=counts,
        first_witness_accessions_corrected=plan_counters[0],
        first_witness_rows_staged=plan_counters[1],
        evidence_members_corrected=plan_counters[2],
        evidence_delta=plan_counters[3],
        manifest=manifest,
        completed_at_utc=utc_now(),
        status="complete",
    )
    # LAST. A finalization that stopped anywhere above leaves a world with no final receipt.
    write_once_json(world_directory / FINAL_WORLD_RECEIPT_FILENAME, dict(receipt.as_record()))
    return receipt


# --------------------------------------------------------------------------- #
# The process boundary -- runs in the PARENT
# --------------------------------------------------------------------------- #
def _child_main(request_path: str) -> int:
    """The merge child's entry point. Not a command; there is no surface that names it.

    The real multipass authority is required before the request is even read (D151-C15 R2): a
    hand-written request handed straight to this bootstrap refuses here, and the body it would
    have reached requires the same authority again before it creates anything.
    """
    require_real_multipass_authority()
    record = _read_json_object(Path(request_path), "multipass merge request")
    kind = str(record.get("kind", ""))
    if kind == MULTIPASS_REQUEST_KIND_GROUP:
        merge_group_body(GroupMergeRequest.from_record(record))
        return 0
    if kind == MULTIPASS_REQUEST_KIND_FINAL:
        finalize_multipass_body(FinalMergeRequest.from_record(record))
        return 0
    message = f"a multipass merge request of kind {kind!r} is not one this build executes"
    raise ChunkMultipassError(message)


def _spawn_merge(
    request_path: Path, *, timeout_seconds: float | None, observe: Callable[[str], None] | None
) -> None:
    if observe is not None:
        observe("MERGE_PROCESS_START")
    completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed bootstrap, no shell
        [sys.executable, "-c", _CHILD_BOOTSTRAP, str(request_path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    if observe is not None:
        observe("MERGE_PROCESS_EXIT")
    if completed.returncode != 0:
        message = (
            f"merge {request_path.name!r} ended with exit status {completed.returncode} and is "
            "NOT complete. Nothing was cleaned, deleted or retried in place, and no terminal "
            f"receipt exists for it. stderr tail: {completed.stderr.strip()[-800:]!r}"
        )
        raise ChunkMultipassError(message)


def run_group_merge(
    request: GroupMergeRequest,
    *,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> IntermediateReceipt:
    """Run one level-1 group merge in a FRESH child process, and prove that process ended.

    The real multipass authority is required FIRST (D151-C15 R2), before the request document is
    written and before a process is started; the predecessor merge's process is dead before this
    one starts; the merge runs in a process that is not this one; the child exits and its status
    is inspected; the receipt exists, verifies against its own artifacts and describes this group
    and attempt.

    Raises:
        ChunkMultipassError: the authority is ``None``, the predecessor is alive, the child
            failed, the child left no receipt, or the receipt does not describe this merge.
    """
    require_real_multipass_authority()
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    attempt_root = Path(request.attempt_directory)
    attempt_root.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = attempt_root.parent / f"{request.group_id}-{request.attempt:03d}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    _spawn_merge(request_path, timeout_seconds=timeout_seconds, observe=observe)
    receipt = IntermediateReceipt.from_record(
        read_receipt_document(
            attempt_root / INTERMEDIATE_RECEIPT_FILENAME, contract=INTERMEDIATE_RECEIPT_CONTRACT
        )
    )
    verify_artifact_manifest(
        attempt_root, receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
    )
    _require(
        receipt.group_id == request.group_id and receipt.attempt == request.attempt,
        f"the receipt in {attempt_root.name!r} describes group {receipt.group_id!r} attempt "
        f"{receipt.attempt}, not {request.group_id!r} attempt {request.attempt}",
    )
    _require(
        receipt.pid != os.getpid(),
        "the intermediate receipt records THIS process's pid, so the merge did not run in a "
        "separate operating-system process and would reclaim nothing when it 'ended'",
    )
    _require_process_dead(receipt.pid)
    return receipt


def run_final_merge(
    request: FinalMergeRequest,
    *,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> Mapping[str, object]:
    """Run the level-2 finalization in a FRESH child process, and prove that process ended.

    The real multipass authority is required FIRST (D151-C15 R2), before the request document is
    written and before a process is started. Returns the final receipt document as read back from
    the world, verified against the world's own artifacts.

    Raises:
        ChunkMultipassError: the authority is ``None``, the predecessor is alive, the child
            failed, or the receipt is absent or does not describe a separate process.
    """
    require_real_multipass_authority()
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    world_directory = Path(request.world_directory)
    world_directory.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = world_directory.parent / f"{world_directory.name}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    _spawn_merge(request_path, timeout_seconds=timeout_seconds, observe=observe)
    document = read_receipt_document(
        world_directory / FINAL_WORLD_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
    )
    manifest_record = document.get("manifest")
    _require(isinstance(manifest_record, Mapping), "the final receipt carries no manifest")
    verify_artifact_manifest(
        world_directory,
        ArtifactManifest.from_record(cast("Mapping[str, object]", manifest_record)),
        exclude=(FINAL_WORLD_RECEIPT_FILENAME,),
    )
    _require(
        str(document.get("consolidation_contract")) == MULTIPASS_CONSOLIDATION_CONTRACT,
        "the final receipt was not written by the multipass finalizer",
    )
    return document


# --------------------------------------------------------------------------- #
# The orchestrator -- runs in the PARENT, starts every merge in its own process
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class MultipassResult:
    """What one multipass consolidation established, and where it put it."""

    world_directory: Path
    receipt: Mapping[str, object]
    schedule: MergeSchedule
    storage_plan: MultipassStoragePlan
    intermediates: tuple[IntermediateReceipt, ...]
    merge_pids: tuple[int, ...]


def _write_or_require_same(path: Path, record: Mapping[str, object], label: str) -> None:
    """Write a durable copy once; on restart, require the existing copy to be identical."""
    if path.exists():
        existing = _read_json_object(path, label)
        expected = json.loads(json.dumps(record, sort_keys=True, default=str))
        _require(
            dict(existing) == expected,
            f"the {label} already recorded at {path.name!r} is not the one this consolidation "
            "was given; a restart continues exactly the recorded consolidation or refuses",
        )
        return
    write_once_json(path, dict(record))


@contextmanager
def _instrumented(
    telemetry: InstrumentationLedger | None, *, step: str, wal_path: Path
) -> Iterator[None]:
    """Stat-only instrumentation around one child merge -- D151-C22 R6, a nonactivated seam.

    Nothing here opens a database: the ledger watches the child's write-ahead log by ``stat``
    and the volumes by ``statvfs`` on a thread, and the orchestrator self-reports its own
    resident size before and after the child so process-exit reclamation is measured. Absent a
    ledger this is a no-op and the run is byte-for-byte the accepted one.
    """
    if telemetry is None:
        yield
        return
    rss_before = process_peak_resident_bytes()
    telemetry.sample(f"merge_started:{step}", wal_path=wal_path)
    with telemetry.watch(wal_path=wal_path):
        yield
    telemetry.record_child_exit(
        parent_rss_before=rss_before, parent_rss_after=process_peak_resident_bytes()
    )
    telemetry.sample(f"merge_child_exit:{step}", wal_path=wal_path)


def run_multipass_f0(  # noqa: PLR0915
    *,
    plan: ChunkPlan,
    internal_root: Path,
    operational_catalog: Path,
    multipass_root: Path,
    run_id: str,
    external_root: Path | None = None,
    cache_bytes: int | None = None,
    capacity_observations: Sequence[Mapping[str, object]] = (),
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
    telemetry: InstrumentationLedger | None = None,
) -> MultipassResult:
    """Consolidate a >9-chunk plan: every level-1 group, then level 2, each in its own process.

    **Two gates, in this order, before anything is read or created -- D151-C15 R2.** The real
    multipass authority is required first: while :data:`REAL_MULTIPASS_F0_AUTHORITY` is ``None``
    this refuses before the storage terms are consulted. Then the storage terms are the
    owner-frozen ones -- every one of which is ``None`` -- and
    :func:`~disclosure_drift.m3.chunk_tiering.accepted_multipass_storage_requirements` refuses
    before the plan is read from disk, before a chunk is resolved and before any directory is
    created. Authority is necessary and not sufficient: an open authority with ``None`` storage
    terms still refuses here, on storage. No parameter of this entry substitutes for either gate;
    the storage seam D151-C13 carried was removed by D151-C15 §9, and there is no environment
    variable, configuration key or command-line flag behind either.

    Then, in order: the plan is required to be a sealed multipass plan; the executing repository
    is measured; the merge schedule is derived and recorded create-once beside the plan; every
    chunk is resolved through the accepted admission and the deterministic storage plan is
    computed from their authenticated byte lengths and recorded -- or, on a restart, verified
    whole against the recorded document and compared with it by restart compatibility
    (D151-C21 R4), the fresh measurement being what every child below is handed; each level-1
    group that already
    carries a valid intermediate is reused, and each that does not is merged in a fresh child
    process that ends before the next begins; then the finalization runs in one more fresh
    process. Nothing is deleted at any point: every chunk and every intermediate is retained.

    Raises:
        ChunkMultipassError: the authority is ``None``, or a multipass precondition fails.
        ChunkTieringError: the storage requirements are not owner-qualified, or a step is not
            admitted.
        ChunkPlanError, ChunkConsolidationError, ChunkStorageError, ChunkEvidenceError,
            RepositoryIdentityError: a precondition fails.
    """
    require_real_multipass_authority()
    requirements = accepted_multipass_storage_requirements()
    # D151-C17 R6: where SQLite will spill is settled BEFORE the run root exists. Every merge
    # child re-establishes this for itself; this is the orchestrator refusing early, not the
    # proof any child relies on.
    binding = require_sqlite_temp_binding(charged_path=multipass_root)
    require_multipass_plan(plan)
    repository = require_clean_running_repository()
    schedule = derive_merge_schedule(plan)
    multipass_root.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    plan_path = multipass_root / CHUNK_PLAN_FILENAME
    schedule_path = multipass_root / MERGE_SCHEDULE_FILENAME
    _write_or_require_same(plan_path, dict(plan.as_record()), "multipass chunk plan")
    _write_or_require_same(schedule_path, dict(schedule.as_record()), "merge schedule")
    inputs = resolve_chunk_inputs(plan, internal_root=internal_root, external_root=external_root)
    _catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    storage_plan = plan_multipass_storage(
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        groups=[(group.group_id, group.chunk_ids) for group in schedule.groups],
        chunk_bytes_by_id={item.chunk_id: item.receipt.manifest.total_bytes for item in inputs},
        seed_catalog_bytes=catalog_bytes,
        requirements=requirements,
        sqlite_temp_binding=binding,
    )
    _record_storage_plan(multipass_root / STORAGE_PLAN_FILENAME, storage_plan)
    intermediates_root = multipass_root / _INTERMEDIATES_DIRECTORY
    by_id = {item.chunk_id: item for item in inputs}
    receipts: list[IntermediateReceipt] = []
    pids: list[int] = []
    previous: int | None = None
    for group in schedule.groups:
        existing = completed_intermediate_receipt(intermediates_root, group.group_id)
        if existing is not None:
            receipts.append(existing[0])
            continue
        # Admission BEFORE the child is started, over the same rule the child re-applies before
        # it creates anything: decided per step, never "run until full".
        _admit_merge_step(
            step=group.group_id,
            level=MERGE_LEVEL_ONE,
            target=intermediate_attempt_directory(intermediates_root, group.group_id, 0),
            input_bytes=sum(
                by_id[chunk_id].receipt.manifest.total_bytes for chunk_id in group.chunk_ids
            ),
            seed_catalog_bytes=catalog_bytes,
            peak_ratio=requirements.level_one_peak_ratio,
            requirements=requirements,
        )
        attempt_directory, attempt = next_intermediate_attempt_directory(
            intermediates_root, group.group_id
        )
        with _instrumented(
            telemetry,
            step=group.group_id,
            wal_path=attempt_directory / f"{WORKING_CATALOG_FILENAME}-wal",
        ):
            receipt = run_group_merge(
                GroupMergeRequest(
                    plan_path=str(plan_path),
                    schedule_path=str(schedule_path),
                    group_id=group.group_id,
                    attempt=attempt,
                    attempt_directory=str(attempt_directory),
                    internal_root=str(internal_root),
                    external_root=None if external_root is None else str(external_root),
                    operational_catalog=str(operational_catalog),
                    cache_bytes=cache_bytes,
                    repository_head_sha=repository.head_sha,
                    repository_tree_sha=repository.tree_sha,
                    storage_requirements=dict(requirements.as_record()),
                    expected_sqlite_temp_binding=dict(binding.as_record()),
                ),
                predecessor_pid=previous,
                timeout_seconds=timeout_seconds,
                observe=observe,
            )
        previous = receipt.pid
        pids.append(receipt.pid)
        receipts.append(receipt)
    world_directory = multipass_root / _FINAL_DIRECTORY
    _admit_merge_step(
        step="final",
        level=MERGE_LEVEL_TWO,
        target=world_directory,
        input_bytes=sum(receipt.manifest.total_bytes for receipt in receipts),
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_two_peak_ratio,
        requirements=requirements,
    )
    with _instrumented(
        telemetry, step="final", wal_path=world_directory / f"{WORKING_CATALOG_FILENAME}-wal"
    ):
        document = run_final_merge(
            FinalMergeRequest(
                plan_path=str(plan_path),
                schedule_path=str(schedule_path),
                intermediates_root=str(intermediates_root),
                internal_root=str(internal_root),
                external_root=None if external_root is None else str(external_root),
                operational_catalog=str(operational_catalog),
                world_directory=str(world_directory),
                run_id=run_id,
                cache_bytes=cache_bytes,
                repository_head_sha=repository.head_sha,
                repository_tree_sha=repository.tree_sha,
                storage_requirements=dict(requirements.as_record()),
                expected_sqlite_temp_binding=dict(binding.as_record()),
                capacity_observations=tuple(dict(item) for item in capacity_observations),
            ),
            predecessor_pid=previous,
            timeout_seconds=timeout_seconds,
            observe=observe,
        )
    return MultipassResult(
        world_directory=world_directory,
        receipt=document,
        schedule=schedule,
        storage_plan=storage_plan,
        intermediates=tuple(receipts),
        merge_pids=tuple(pids),
    )


# --------------------------------------------------------------------------- #
# The dependency-closed calibration route -- D151-C27R1
# --------------------------------------------------------------------------- #
#: The calibration-subset terminal result's contract -- D151-C27R1 §4. Never a canonical F0
#: receipt or checkpoint: the accepted final-receipt reader, the F0 checkpoint reader and every
#: production reader refuse it, and it satisfies no complete-source reader.
CALIBRATION_SUBSET_RESULT_CONTRACT: Final = "m3.3-chunked-f0-calibration-subset-result/1"

#: The result's fixed filename, written LAST into the calibration final world.
CALIBRATION_SUBSET_RESULT_FILENAME: Final = "calibration_subset_result.json"

#: The kind every child-produced admission event carries -- D151-C27R1 R7.
CALIBRATION_ADMISSION_EVENT_KIND: Final = "calibration_merge_admission"

#: The calibration child's bootstrap -- one launch shape for all three roles -- D151-C27R1 R4.
#: Deliberately separate from :data:`_CHILD_BOOTSTRAP`: the production bootstrap keeps its
#: authority-first refusal byte for byte, and this one enters :func:`_calibration_child_main`,
#: whose FIRST statement receives and validates the pipe-delivered envelope.
_CALIBRATION_CHILD_BOOTSTRAP: Final = (
    "import sys;"
    "from disclosure_drift.m3.chunk_multipass import _calibration_child_main;"
    "sys.exit(_calibration_child_main(sys.argv[1], sys.argv[2]))"
)

_CALIBRATION_STEP_FINAL: Final = "final"

_ADMISSION_EVENT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "event_kind",
        "classifications",
        "run_id",
        "plan_digest",
        "role",
        "step_id",
        "child_pid",
        "level",
        "input_bytes",
        "seed_catalog_bytes",
        "peak_bytes",
        "reserve_bytes",
        "transient_bytes",
        "required_free_bytes",
        "free_before_bytes",
        "admitted",
        "sqlite_temp_binding_identity",
        "envelope_sha256",
        "monotonic_ns",
        "event_identity",
    }
)


def _measured_calibration_binding(charged_path: Path) -> SqliteTempBinding:
    """The calibration child's own measured binding, through the accepted guard -- C17 R6."""
    measured = measured_calibration_binding(charged_path)
    _require(
        isinstance(measured, SqliteTempBinding),
        "the calibration binding measurement did not return a SQLite temp binding; refused",
    )
    return cast("SqliteTempBinding", measured)


def _within(container: Path, candidate: Path) -> bool:
    """Whether ``candidate`` lies at or beneath ``container``, by resolved path."""
    return candidate.resolve().is_relative_to(container.resolve())


def _stored_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        message = (
            f"calibration field {field!r} holds {type(value).__name__} where a bool is required"
        )
        raise ChunkMultipassError(message)
    return value


def _stored_labels(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or tuple(str(item) for item in value) != (
        CALIBRATION_SUBSET_CLASSIFICATIONS
    ):
        message = (
            f"calibration field {field!r} must be exactly "
            f"{list(CALIBRATION_SUBSET_CLASSIFICATIONS)}; refused"
        )
        raise ChunkMultipassError(message)
    return CALIBRATION_SUBSET_CLASSIFICATIONS


def _record_identity(record: Mapping[str, object], identity_key: str) -> str:
    """SHA-256 over the canonical bytes of the whole record without its identity field."""
    body = {key: value for key, value in record.items() if key != identity_key}
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def stable_binding_identity(binding: SqliteTempBinding) -> str:
    """The restart-stable identity of a measured SQLite temp binding -- its stable fields only."""
    return hashlib.sha256(canonical_json_bytes(dict(binding.stable_record()))).hexdigest()


@dataclass(frozen=True, slots=True)
class CalibrationAdmissionEvent:
    """One merge child's own record of the admission it ran under -- D151-C27R1 R7.

    Emitted by the child, in the child, AFTER its envelope, request, temp binding and admission
    were validated and BEFORE any substantive merge work or world directory exists, into the
    instrumentation ledger the envelope explicitly names. It carries the level the step was
    charged at and that level's transient allowance, so a level-2 charge is distinguishable from
    a level-1 one in the child's own words. Create-once: the parent can neither synthesize nor
    overwrite it, and ``event_identity`` seals the whole record.
    """

    event_kind: str
    classifications: tuple[str, ...]
    run_id: str
    plan_digest: str
    role: str
    step_id: str
    child_pid: int
    level: str
    input_bytes: int
    seed_catalog_bytes: int
    peak_bytes: int
    reserve_bytes: int
    transient_bytes: int
    required_free_bytes: int
    free_before_bytes: int
    admitted: bool
    sqlite_temp_binding_identity: str
    envelope_sha256: str
    monotonic_ns: int
    event_identity: str

    def _identity_inputs(self) -> dict[str, object]:
        return {
            "event_kind": self.event_kind,
            "classifications": list(self.classifications),
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "role": self.role,
            "step_id": self.step_id,
            "child_pid": self.child_pid,
            "level": self.level,
            "input_bytes": self.input_bytes,
            "seed_catalog_bytes": self.seed_catalog_bytes,
            "peak_bytes": self.peak_bytes,
            "reserve_bytes": self.reserve_bytes,
            "transient_bytes": self.transient_bytes,
            "required_free_bytes": self.required_free_bytes,
            "free_before_bytes": self.free_before_bytes,
            "admitted": self.admitted,
            "sqlite_temp_binding_identity": self.sqlite_temp_binding_identity,
            "envelope_sha256": self.envelope_sha256,
            "monotonic_ns": self.monotonic_ns,
        }

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        record = self._identity_inputs()
        record["event_identity"] = self.event_identity
        return record

    def identity(self) -> str:
        """The identity the record implies -- over everything but the identity field."""
        return _record_identity(self._identity_inputs(), "event_identity")

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationAdmissionEvent:
        """Rebuild an event from its EXACT mapping and re-derive its identity.

        Raises:
            ChunkMultipassError: any key is missing or unexpected, a value is of another type,
                the kind or labels are wrong, the level is not a merge level, the event records a
                refusal, or the stored identity does not describe the record.
        """
        present = {str(key) for key in record}
        if present != _ADMISSION_EVENT_KEYS:
            message = (
                "a calibration admission event is exact; this one is missing "
                f"{sorted(_ADMISSION_EVENT_KEYS - present)} and carries unexpected "
                f"{sorted(present - _ADMISSION_EVENT_KEYS)}; refused"
            )
            raise ChunkMultipassError(message)
        event = cls(
            event_kind=str(record["event_kind"]),
            classifications=_stored_labels(record["classifications"], "classifications"),
            run_id=str(record["run_id"]),
            plan_digest=str(record["plan_digest"]),
            role=str(record["role"]),
            step_id=str(record["step_id"]),
            child_pid=_stored_int(record["child_pid"], "child_pid"),
            level=str(record["level"]),
            input_bytes=_stored_int(record["input_bytes"], "input_bytes"),
            seed_catalog_bytes=_stored_int(record["seed_catalog_bytes"], "seed_catalog_bytes"),
            peak_bytes=_stored_int(record["peak_bytes"], "peak_bytes"),
            reserve_bytes=_stored_int(record["reserve_bytes"], "reserve_bytes"),
            transient_bytes=_stored_int(record["transient_bytes"], "transient_bytes"),
            required_free_bytes=_stored_int(record["required_free_bytes"], "required_free_bytes"),
            free_before_bytes=_stored_int(record["free_before_bytes"], "free_before_bytes"),
            admitted=_stored_bool(record["admitted"], "admitted"),
            sqlite_temp_binding_identity=str(record["sqlite_temp_binding_identity"]),
            envelope_sha256=str(record["envelope_sha256"]),
            monotonic_ns=_stored_int(record["monotonic_ns"], "monotonic_ns"),
            event_identity=str(record["event_identity"]),
        )
        _require(
            event.event_kind == CALIBRATION_ADMISSION_EVENT_KIND,
            f"a calibration admission event of kind {event.event_kind!r} is refused",
        )
        _require(
            event.level in MERGE_LEVELS
            and event.role in (CALIBRATION_ROLE_GROUP, CALIBRATION_ROLE_FINAL),
            f"a calibration admission event charged at {event.level!r} for role {event.role!r} "
            "names no merge level or no merge role; refused",
        )
        _require(
            event.admitted
            and event.required_free_bytes
            == event.peak_bytes + event.reserve_bytes + event.transient_bytes,
            "a calibration admission event must record an ADMITTED step whose floor is peak + "
            "reserve + transient; refused",
        )
        _require(
            event.identity() == event.event_identity,
            "a calibration admission event's recorded identity does not describe its own "
            f"contents: recorded {event.event_identity!r}, recomputed {event.identity()!r}",
        )
        return event


def calibration_admission_event_path(
    ledger: Path, *, role: str, step_id: str, attempt: int | None
) -> Path:
    """Where one merge child's admission event lives inside the instrumentation ledger."""
    suffix = "" if attempt is None else f"-attempt-{attempt:03d}"
    return ledger / f"admission-{role}-{step_id}{suffix}.json"


def read_calibration_admission_event(path: Path) -> CalibrationAdmissionEvent:
    """One admission event, read from its canonical bytes, or a refusal.

    Raises:
        ChunkMultipassError: the file is absent, a link, not canonical, or not an exact event.
    """
    _require(not path.is_symlink(), f"event {path.name!r} is a symbolic link and is refused")
    _require(path.is_file(), f"no calibration admission event exists at {path.name!r}")
    payload = path.read_bytes()
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"event {path.name!r} is not decodable JSON: {exc}"
        raise ChunkMultipassError(message) from exc
    _require(isinstance(decoded, dict), f"event {path.name!r} is not a JSON object")
    event = CalibrationAdmissionEvent.from_record(cast("Mapping[str, object]", decoded))
    _require(
        canonical_json_bytes(event.as_record()) == payload,
        f"event {path.name!r} is not persisted as its canonical bytes; refused",
    )
    return event


def _emit_calibration_admission_event(
    *,
    envelope: CalibrationChildEnvelope,
    admission: MergeAdmission,
    binding: SqliteTempBinding,
    input_bytes: int,
    seed_catalog_bytes: int,
    charged_directory: Path,
    attempt: int | None,
) -> CalibrationAdmissionEvent:
    """Emit THIS child's admission event, create-once, into the ledger the envelope names -- R7.

    Runs after the envelope, request, temp binding and admission were validated and before the
    charged directory exists. The ledger must exist, be a directory, and lie outside the charged
    directory. The event carries this process's pid and the SHA-256 of the envelope -- never the
    envelope itself.

    Raises:
        ChunkMultipassError: the envelope names no ledger, the ledger is unusable, or the event
            already exists.
    """
    _require(
        envelope.instrumentation_ledger is not None,
        f"a calibration {envelope.role!r} child needs an instrumentation ledger in its envelope "
        "to emit its admission event into; none was supplied and the merge is refused",
    )
    ledger = Path(str(envelope.instrumentation_ledger))
    _require(
        ledger.is_dir() and not ledger.is_symlink(),
        "the calibration instrumentation ledger must be an existing directory that is not a link",
    )
    _require(
        not _within(charged_directory, ledger),
        "the calibration instrumentation ledger must lie outside the directory admission "
        "charges; an event inside the charged directory would perturb the measurement",
    )
    event = CalibrationAdmissionEvent(
        event_kind=CALIBRATION_ADMISSION_EVENT_KIND,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        run_id=envelope.run_id,
        plan_digest=envelope.plan_digest,
        role=envelope.role,
        step_id=envelope.step_id,
        child_pid=os.getpid(),
        level=admission.level,
        input_bytes=input_bytes,
        seed_catalog_bytes=seed_catalog_bytes,
        peak_bytes=admission.peak_bytes,
        reserve_bytes=admission.reserve_bytes,
        transient_bytes=admission.transient_bytes,
        required_free_bytes=admission.required_free_bytes,
        free_before_bytes=admission.free_bytes,
        admitted=admission.admitted,
        sqlite_temp_binding_identity=stable_binding_identity(binding),
        envelope_sha256=envelope.sha256,
        monotonic_ns=time.monotonic_ns(),
        event_identity="",
    )
    sealed = replace(event, event_identity=event.identity())
    path = calibration_admission_event_path(
        ledger, role=envelope.role, step_id=envelope.step_id, attempt=attempt
    )
    try:
        write_once_canonical_json(path, dict(sealed.as_record()))
    except ChunkExecutionError as exc:
        message = f"the calibration admission event could not be emitted: {exc}"
        raise ChunkMultipassError(message) from exc
    return sealed


_RESULT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "contract",
        "classifications",
        "plan_digest",
        "merge_schedule_digest",
        "run_id",
        "source_instance_id",
        "source_observation_id",
        "source_sha256",
        "source_byte_length",
        "member_order_digest",
        "selected_member_order_digest",
        "shard_parent_binding_digest",
        "primary_prefix_members",
        "selected_shard_members",
        "excluded_shard_members",
        "selected_members",
        "full_total_members",
        "repository_head_sha",
        "repository_tree_sha",
        "catalog_source_sha256",
        "execution_contract_identity",
        "chunk_count",
        "intermediate_count",
        "parser_run_id",
        "run_outcome",
        "parser_state_after",
        "world_parser_state",
        "members",
        "records",
        "parsed_records",
        "quarantined_records",
        "omitted_field_observations",
        "materialized_field_observations",
        "completeness_digest",
        "member_manifest_digest",
        "table_row_counts",
        "first_witness_accessions_corrected",
        "first_witness_rows_staged",
        "evidence_members_corrected",
        "evidence_delta",
        "storage_admission",
        "admission_event_identity",
        "envelope_sha256",
        "pid",
        "rss_peak_bytes",
        "started_at_utc",
        "completed_at_utc",
        "manifest",
        "status",
        "result_identity",
    }
)


@dataclass(frozen=True, slots=True)
class CalibrationSubsetResult:
    """The calibration-only terminal result of one dependency-closed subset run -- R6.

    Not a canonical F0 receipt, not a checkpoint, not a production input, not a bounded canary:
    it carries the four labels, both the full and the selected identities, the child's own
    admission and the identity of the admission event it emitted, and a measured
    ``world_parser_state`` proving the world was never marked parsed. ``parser_state_after`` is
    ``chunk_local``: a calibration world claims no source-level terminal.
    """

    contract: str
    classifications: tuple[str, ...]
    plan_digest: str
    merge_schedule_digest: str
    run_id: str
    source_instance_id: str
    source_observation_id: str
    source_sha256: str
    source_byte_length: int
    member_order_digest: str
    selected_member_order_digest: str
    shard_parent_binding_digest: str
    primary_prefix_members: int
    selected_shard_members: int
    excluded_shard_members: int
    selected_members: int
    full_total_members: int
    repository_head_sha: str
    repository_tree_sha: str
    catalog_source_sha256: str
    execution_contract_identity: str
    chunk_count: int
    intermediate_count: int
    parser_run_id: str
    run_outcome: str
    parser_state_after: str
    world_parser_state: str
    members: int
    records: int
    parsed_records: int
    quarantined_records: int
    omitted_field_observations: int
    materialized_field_observations: int
    completeness_digest: str
    member_manifest_digest: str
    table_row_counts: Mapping[str, int]
    first_witness_accessions_corrected: int
    first_witness_rows_staged: int
    evidence_members_corrected: int
    evidence_delta: int
    storage_admission: Mapping[str, object]
    admission_event_identity: str
    envelope_sha256: str
    pid: int
    rss_peak_bytes: int | None
    started_at_utc: str
    completed_at_utc: str
    manifest: ArtifactManifest
    status: str
    result_identity: str
    #: D151-C31R2-R19B-C2 §32: the successor terminal binds its observability closeout here; a
    #: legacy calibration result never carries the key and its identity is unchanged.
    successor_observability: Mapping[str, object] | None = None

    def _identity_inputs(self) -> dict[str, object]:
        inputs: dict[str, object] = {
            "contract": self.contract,
            "classifications": list(self.classifications),
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "run_id": self.run_id,
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_sha256": self.source_sha256,
            "source_byte_length": self.source_byte_length,
            "member_order_digest": self.member_order_digest,
            "selected_member_order_digest": self.selected_member_order_digest,
            "shard_parent_binding_digest": self.shard_parent_binding_digest,
            "primary_prefix_members": self.primary_prefix_members,
            "selected_shard_members": self.selected_shard_members,
            "excluded_shard_members": self.excluded_shard_members,
            "selected_members": self.selected_members,
            "full_total_members": self.full_total_members,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "catalog_source_sha256": self.catalog_source_sha256,
            "execution_contract_identity": self.execution_contract_identity,
            "chunk_count": self.chunk_count,
            "intermediate_count": self.intermediate_count,
            "parser_run_id": self.parser_run_id,
            "run_outcome": self.run_outcome,
            "parser_state_after": self.parser_state_after,
            "world_parser_state": self.world_parser_state,
            "members": self.members,
            "records": self.records,
            "parsed_records": self.parsed_records,
            "quarantined_records": self.quarantined_records,
            "omitted_field_observations": self.omitted_field_observations,
            "materialized_field_observations": self.materialized_field_observations,
            "completeness_digest": self.completeness_digest,
            "member_manifest_digest": self.member_manifest_digest,
            "table_row_counts": dict(sorted(self.table_row_counts.items())),
            "first_witness_accessions_corrected": self.first_witness_accessions_corrected,
            "first_witness_rows_staged": self.first_witness_rows_staged,
            "evidence_members_corrected": self.evidence_members_corrected,
            "evidence_delta": self.evidence_delta,
            "storage_admission": dict(self.storage_admission),
            "admission_event_identity": self.admission_event_identity,
            "envelope_sha256": self.envelope_sha256,
            "pid": self.pid,
            "rss_peak_bytes": self.rss_peak_bytes,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "manifest": dict(self.manifest.as_record()),
            "status": self.status,
        }
        if self.successor_observability is not None:
            inputs["successor_observability"] = dict(self.successor_observability)
        return inputs

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        record = self._identity_inputs()
        record["result_identity"] = self.result_identity
        return record

    def identity(self) -> str:
        """The identity the record implies -- over everything but the identity field."""
        return _record_identity(self._identity_inputs(), "result_identity")

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationSubsetResult:  # noqa: PLR0915
        """Rebuild a result from its EXACT mapping and re-derive its identity.

        Raises:
            ChunkMultipassError: the shape, contract, labels, status or identity refuses.
        """
        present = {str(key) for key in record} - {"successor_observability"}
        if present != _RESULT_KEYS:
            message = (
                "a calibration-subset result is exact; this one is missing "
                f"{sorted(_RESULT_KEYS - present)} and carries unexpected "
                f"{sorted(present - _RESULT_KEYS)}; refused"
            )
            raise ChunkMultipassError(message)
        counts = record["table_row_counts"]
        admission = record["storage_admission"]
        manifest = record["manifest"]
        observability = record.get("successor_observability")
        if (
            not isinstance(counts, Mapping)
            or not isinstance(admission, Mapping)
            or not isinstance(manifest, Mapping)
            or not (observability is None or isinstance(observability, Mapping))
        ):
            message = "a calibration-subset result's counts, admission or manifest are not mappings"
            raise ChunkMultipassError(message)
        peak = record["rss_peak_bytes"]
        try:
            result = cls(
                contract=str(record["contract"]),
                classifications=_stored_labels(record["classifications"], "classifications"),
                plan_digest=str(record["plan_digest"]),
                merge_schedule_digest=str(record["merge_schedule_digest"]),
                run_id=str(record["run_id"]),
                source_instance_id=str(record["source_instance_id"]),
                source_observation_id=str(record["source_observation_id"]),
                source_sha256=str(record["source_sha256"]),
                source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
                member_order_digest=str(record["member_order_digest"]),
                selected_member_order_digest=str(record["selected_member_order_digest"]),
                shard_parent_binding_digest=str(record["shard_parent_binding_digest"]),
                primary_prefix_members=_stored_int(
                    record["primary_prefix_members"], "primary_prefix_members"
                ),
                selected_shard_members=_stored_int(
                    record["selected_shard_members"], "selected_shard_members"
                ),
                excluded_shard_members=_stored_int(
                    record["excluded_shard_members"], "excluded_shard_members"
                ),
                selected_members=_stored_int(record["selected_members"], "selected_members"),
                full_total_members=_stored_int(record["full_total_members"], "full_total_members"),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                catalog_source_sha256=str(record["catalog_source_sha256"]),
                execution_contract_identity=str(record["execution_contract_identity"]),
                chunk_count=_stored_int(record["chunk_count"], "chunk_count"),
                intermediate_count=_stored_int(record["intermediate_count"], "intermediate_count"),
                parser_run_id=str(record["parser_run_id"]),
                run_outcome=str(record["run_outcome"]),
                parser_state_after=str(record["parser_state_after"]),
                world_parser_state=str(record["world_parser_state"]),
                members=_stored_int(record["members"], "members"),
                records=_stored_int(record["records"], "records"),
                parsed_records=_stored_int(record["parsed_records"], "parsed_records"),
                quarantined_records=_stored_int(
                    record["quarantined_records"], "quarantined_records"
                ),
                omitted_field_observations=_stored_int(
                    record["omitted_field_observations"], "omitted_field_observations"
                ),
                materialized_field_observations=_stored_int(
                    record["materialized_field_observations"], "materialized_field_observations"
                ),
                completeness_digest=str(record["completeness_digest"]),
                member_manifest_digest=str(record["member_manifest_digest"]),
                table_row_counts={
                    str(key): _stored_int(value, str(key)) for key, value in counts.items()
                },
                first_witness_accessions_corrected=_stored_int(
                    record["first_witness_accessions_corrected"],
                    "first_witness_accessions_corrected",
                ),
                first_witness_rows_staged=_stored_int(
                    record["first_witness_rows_staged"], "first_witness_rows_staged"
                ),
                evidence_members_corrected=_stored_int(
                    record["evidence_members_corrected"], "evidence_members_corrected"
                ),
                evidence_delta=_stored_int(record["evidence_delta"], "evidence_delta"),
                storage_admission={str(key): value for key, value in admission.items()},
                admission_event_identity=str(record["admission_event_identity"]),
                envelope_sha256=str(record["envelope_sha256"]),
                pid=_stored_int(record["pid"], "pid"),
                rss_peak_bytes=None if peak is None else _stored_int(peak, "rss_peak_bytes"),
                started_at_utc=str(record["started_at_utc"]),
                completed_at_utc=str(record["completed_at_utc"]),
                manifest=ArtifactManifest.from_record(manifest),
                status=str(record["status"]),
                result_identity=str(record["result_identity"]),
                successor_observability=None
                if observability is None
                else {str(key): value for key, value in observability.items()},
            )
        except ChunkEvidenceError as exc:
            message = f"a calibration-subset result's manifest is refused: {exc}"
            raise ChunkMultipassError(message) from exc
        _require(
            result.contract == CALIBRATION_SUBSET_RESULT_CONTRACT,
            f"a result carrying contract {result.contract!r} is refused; this reader consumes "
            f"only {CALIBRATION_SUBSET_RESULT_CONTRACT!r}",
        )
        _require(
            result.status == "complete" and result.parser_state_after == "chunk_local",
            "a calibration-subset result records a complete run that claims no source-level "
            "parser state; refused",
        )
        _require(
            result.identity() == result.result_identity,
            "a calibration-subset result's recorded identity does not describe its own contents: "
            f"recorded {result.result_identity!r}, recomputed {result.identity()!r}",
        )
        return result


def read_calibration_subset_result(path: Path) -> CalibrationSubsetResult:
    """One calibration-subset result, read from its canonical bytes, or a refusal.

    Raises:
        ChunkMultipassError: the file is absent, a link, not canonical, or not an exact result.
    """
    _require(not path.is_symlink(), f"result {path.name!r} is a symbolic link and is refused")
    _require(
        path.is_file(),
        f"no calibration-subset result exists at {path.name!r}; an absent terminal is a refusal",
    )
    payload = path.read_bytes()
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"result {path.name!r} is not decodable JSON: {exc}"
        raise ChunkMultipassError(message) from exc
    _require(isinstance(decoded, dict), f"result {path.name!r} is not a JSON object")
    result = CalibrationSubsetResult.from_record(cast("Mapping[str, object]", decoded))
    _require(
        canonical_json_bytes(result.as_record()) == payload,
        f"result {path.name!r} is not persisted as its canonical bytes; refused",
    )
    return result


# --------------------------------------------------------------------------- #
# The calibration schedule and readers
# --------------------------------------------------------------------------- #
def derive_calibration_subset_schedule(plan: ChunkPlan) -> MergeSchedule:
    """The one merge schedule a sealed calibration-subset plan implies -- the same grouping.

    The grouping arithmetic is :func:`group_chunks`, unchanged, over the subset plan's chunks in
    selected coordinates: for the C29 target that is exactly 9 / 9 / 9 / 6 primary groups and one
    one-chunk shard group. The schedule contract and shape are the accepted ones; its
    ``plan_digest`` binds the subset plan, so no production schedule can be mistaken for it.

    Raises:
        ChunkPlanError, ChunkMultipassError: the plan is not a sealed subset plan.
    """
    require_calibration_subset_plan(plan)
    groups = group_chunks(plan.chunks, fan_in=MERGE_FAN_IN)
    _require(
        len(groups) <= MERGE_FAN_IN,
        f"the subset plan groups into {len(groups)} level-1 intermediates and one merge attaches "
        f"{MERGE_FAN_IN}; refused",
    )
    schedule = MergeSchedule(
        contract=MERGE_SCHEDULE_CONTRACT,
        plan_digest=plan.plan_digest,
        fan_in=MERGE_FAN_IN,
        groups=groups,
        level_two_inputs=tuple(group.group_id for group in groups),
        schedule_digest="",
    )
    return replace(schedule, schedule_digest=_schedule_digest(schedule))


def _read_calibration_plan_and_schedule(
    plan_path: str, schedule_path: str
) -> tuple[CalibrationSubsetPlan, MergeSchedule]:
    plan = CalibrationSubsetPlan.from_record(
        _read_json_object(Path(plan_path), "calibration-subset plan")
    )
    schedule = MergeSchedule.from_record(_read_json_object(Path(schedule_path), "merge schedule"))
    require_sealed_schedule(schedule, plan)
    return plan, schedule


def _write_canonical_or_require_same(path: Path, record: Mapping[str, object], label: str) -> None:
    """Write a canonical copy once; on restart, require the existing bytes to be identical."""
    if path.exists():
        _require(
            not path.is_symlink() and path.read_bytes() == canonical_json_bytes(record),
            f"the {label} already recorded at {path.name!r} is not the one this calibration was "
            "given; a restart continues exactly the recorded calibration or refuses",
        )
        return
    write_once_canonical_json(path, dict(record))


# --------------------------------------------------------------------------- #
# The retention-aware calibration lifecycle -- D151-C29R1
# --------------------------------------------------------------------------- #
#: The retained per-chunk witness's contract -- D151-C29R1 §6, the ONE persisted contract the
#: retention correction adds. A witness is the SMALLEST exact representation of what the
#: calibration finalization consumes from a chunk after level one: the two-column
#: ``census_accessions`` projection and the first-witness ledger the whole-F0 counters are
#: derived from (:func:`_plan_first_witness_counters`), the primary chunk's declarations the shard
#: chunk's parent map is merged from, and a sealed record binding the chunk's terminal receipt,
#: its manifest, the plan, the schedule, the source and the payload. It is not a chunk receipt --
#: the chunk-receipt reader refuses it by contract -- and no production finalizer consumes it.
CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT: Final = (
    "m3.3-chunked-f0-calibration-chunk-retained-witness/1"
)

#: The witness record's fixed filename. Written LAST, inside the witness attempt directory.
CALIBRATION_RETAINED_WITNESS_FILENAME: Final = "chunk_retained_witness.json"

#: The witness payload: a run-local SQLite file holding exactly the two projected tables and a
#: meta table saying what it is. Never a catalog, never a migration, never a production input.
CALIBRATION_RETAINED_PAYLOAD_FILENAME: Final = "retained_witness.sqlite3"

#: The two per-group lifecycle records -- D151-C29R1 §7 -- modelled on the C27R1 admission-event
#: precedent: an ``event_kind``, an exact key set and an identity seal, persisted as canonical
#: bytes create-once. The checkpoint binds chunk receipt <-> retained witness <-> intermediate and
#: is what makes a chunk world deletable; the deletion record is written only after every source
#: directory is absent. Neither is a production reclaim record and neither can confer one.
CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND: Final = "calibration_group_checkpoint"
CALIBRATION_GROUP_DELETION_EVENT_KIND: Final = "calibration_group_deletion"

#: Where a calibration multipass keeps its retained artifacts, beside ``intermediates`` and
#: ``final`` under the multipass root -- a convention of the root's layout, like those two, so
#: the reused request contracts keep their exact C27R1 shape. The final child derives it from
#: ``intermediates_root`` and verifies everything it finds there.
_RETAINED_DIRECTORY: Final = "retained"
_CHECKPOINT_SUFFIX: Final = "-checkpoint.json"
_DELETION_SUFFIX: Final = "-deletion.json"

#: The payload schema. The two table names are the ACCEPTED ones deliberately: the whole-F0
#: counter derivation reads ``<alias>.census_accessions`` and ``<alias>.chunk_first_witness``
#: and runs over a retained payload under exactly the same statements it runs over a chunk world.
_RETAINED_PAYLOAD_SCHEMA: Final = """
CREATE TABLE census_accessions (
    accession_plain     TEXT PRIMARY KEY,
    parsed_record_id    TEXT NOT NULL
) STRICT;

CREATE TABLE chunk_first_witness (
    native_identity     TEXT PRIMARY KEY,
    member_ordinal      INTEGER NOT NULL,
    record_ordinal      INTEGER NOT NULL,
    delta_materialized  INTEGER NOT NULL CHECK (delta_materialized >= 0)
) STRICT;

CREATE TABLE retained_witness_meta (
    key                 TEXT PRIMARY KEY,
    value               TEXT NOT NULL
) STRICT;
"""

_WITNESS_KEYS: Final[frozenset[str]] = frozenset(
    {
        "contract",
        "classifications",
        "run_id",
        "plan_digest",
        "merge_schedule_digest",
        "chunk_id",
        "chunk_ordinal",
        "region",
        "start",
        "end",
        "member_order_digest",
        "selected_member_order_digest",
        "shard_parent_binding_digest",
        "source_instance_id",
        "source_observation_id",
        "source_sha256",
        "source_byte_length",
        "chunk_attempt",
        "chunk_receipt_sha256",
        "chunk_manifest_digest",
        "chunk_manifest_total_bytes",
        "chunk_execution_identity",
        "execution_contract_identity",
        "repository_head_sha",
        "repository_tree_sha",
        "chunk_started_at_utc",
        "chunk_completed_at_utc",
        "payload_filename",
        "payload_sha256",
        "payload_byte_length",
        "accession_rows",
        "ledger_rows",
        "semantic_payload_identity",
        "declarations_sha256",
        "declarations_byte_length",
        "witness_attempt",
        "pid",
        "written_at_utc",
        "witness_identity",
    }
)

_CHECKPOINT_CHUNK_KEYS: Final[frozenset[str]] = frozenset(
    {
        "chunk_id",
        "ordinal",
        "attempt",
        "receipt_sha256",
        "manifest",
        "witness_attempt",
        "witness_identity",
        "payload_sha256",
    }
)

_CHECKPOINT_KEYS: Final[frozenset[str]] = frozenset(
    {
        "event_kind",
        "classifications",
        "run_id",
        "plan_digest",
        "merge_schedule_digest",
        "group_id",
        "group_ordinal",
        "region",
        "start",
        "end",
        "chunks",
        "intermediate_attempt",
        "intermediate_receipt_sha256",
        "intermediate_manifest_digest",
        "intermediate_catalog_sha256",
        "pid",
        "written_at_utc",
        "checkpoint_identity",
    }
)

_DELETION_CHUNK_KEYS: Final[frozenset[str]] = frozenset(
    {"chunk_id", "attempt", "entries", "entries_deleted", "resumed"}
)

_DELETION_KEYS: Final[frozenset[str]] = frozenset(
    {
        "event_kind",
        "classifications",
        "run_id",
        "plan_digest",
        "merge_schedule_digest",
        "group_id",
        "grant_identity",
        "checkpoint_identity",
        "chunks",
        "free_before_bytes",
        "free_after_bytes",
        "freed_bytes",
        "expected_freed_bytes",
        "sources_absent",
        "pid",
        "completed_at_utc",
        "deletion_identity",
    }
)


def _hex64(value: object, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or set(value) - set("0123456789abcdef"):
        message = f"calibration field {field!r} is not a SHA-256 hex digest; refused"
        raise ChunkMultipassError(message)
    return value


def _exact_keys(record: Mapping[str, object], expected: frozenset[str], label: str) -> None:
    present = {str(key) for key in record}
    if present != expected:
        message = (
            f"a {label} is exact; this one is missing {sorted(expected - present)} and carries "
            f"unexpected {sorted(present - expected)}; refused"
        )
        raise ChunkMultipassError(message)


def _decoded_canonical_object(path: Path, label: str) -> tuple[Mapping[str, object], bytes]:
    _require(not path.is_symlink(), f"{label} {path.name!r} is a symbolic link and is refused")
    _require(path.is_file(), f"no {label} exists at {path.name!r}; an absent record is a refusal")
    payload = path.read_bytes()
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        message = f"{label} {path.name!r} is not decodable JSON: {exc}"
        raise ChunkMultipassError(message) from exc
    _require(isinstance(decoded, dict), f"{label} {path.name!r} is not a JSON object")
    return cast("Mapping[str, object]", decoded), payload


def calibration_retained_root(intermediates_root: Path) -> Path:
    """Where a calibration multipass keeps its retained witnesses and lifecycle records.

    The sibling of the intermediates root named ``retained`` -- the multipass root's layout,
    which the orchestrator lays down and the final child derives from the one root path its
    unchanged request carries.
    """
    return intermediates_root.parent / _RETAINED_DIRECTORY


def calibration_witness_attempt_directory(retained_root: Path, chunk_id: str, attempt: int) -> Path:
    """Where one attempt at one chunk's retained witness lives. Create-once, never reused."""
    return retained_root / chunk_id / f"attempt-{attempt:03d}"


def calibration_group_checkpoint_path(retained_root: Path, group_id: str) -> Path:
    """Where one group's create-once checkpoint record lives."""
    return retained_root / f"{group_id}{_CHECKPOINT_SUFFIX}"


def calibration_group_deletion_path(retained_root: Path, group_id: str) -> Path:
    """Where one group's create-once deletion-complete record lives."""
    return retained_root / f"{group_id}{_DELETION_SUFFIX}"


@dataclass(frozen=True, slots=True)
class CalibrationChunkWitness:
    """One chunk's retained witness record -- D151-C29R1 §6.

    Sealed by ``witness_identity`` over every other field. It binds the run, the subset plan and
    the schedule it will be consumed under, the chunk (identity, plan ordinal, kind and
    selected-coordinate interval), the full canonical ordering and the selected ordering, the
    source artifact, the chunk's authenticated terminal receipt (the SHA-256 of the receipt
    document as found in its one authoritative copy, the manifest digest and byte total, the
    execution identity, the contract identity and the repository the chunk ran under), and the
    exact retained payload (its bytes, its row counts and its content identity) plus the
    declarations copy a primary chunk carries. Written only after the chunk's terminal receipt
    verified against its artifacts, and never by a chunk child.
    """

    contract: str
    classifications: tuple[str, ...]
    run_id: str
    plan_digest: str
    merge_schedule_digest: str
    chunk_id: str
    chunk_ordinal: int
    region: str
    start: int
    end: int
    member_order_digest: str
    selected_member_order_digest: str
    shard_parent_binding_digest: str
    source_instance_id: str
    source_observation_id: str
    source_sha256: str
    source_byte_length: int
    chunk_attempt: int
    chunk_receipt_sha256: str
    chunk_manifest_digest: str
    chunk_manifest_total_bytes: int
    chunk_execution_identity: str
    execution_contract_identity: str
    repository_head_sha: str
    repository_tree_sha: str
    chunk_started_at_utc: str
    chunk_completed_at_utc: str
    payload_filename: str
    payload_sha256: str
    payload_byte_length: int
    accession_rows: int
    ledger_rows: int
    semantic_payload_identity: str
    declarations_sha256: str | None
    declarations_byte_length: int | None
    witness_attempt: int
    pid: int
    written_at_utc: str
    witness_identity: str

    def _identity_inputs(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "classifications": list(self.classifications),
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "chunk_id": self.chunk_id,
            "chunk_ordinal": self.chunk_ordinal,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "member_order_digest": self.member_order_digest,
            "selected_member_order_digest": self.selected_member_order_digest,
            "shard_parent_binding_digest": self.shard_parent_binding_digest,
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_sha256": self.source_sha256,
            "source_byte_length": self.source_byte_length,
            "chunk_attempt": self.chunk_attempt,
            "chunk_receipt_sha256": self.chunk_receipt_sha256,
            "chunk_manifest_digest": self.chunk_manifest_digest,
            "chunk_manifest_total_bytes": self.chunk_manifest_total_bytes,
            "chunk_execution_identity": self.chunk_execution_identity,
            "execution_contract_identity": self.execution_contract_identity,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "chunk_started_at_utc": self.chunk_started_at_utc,
            "chunk_completed_at_utc": self.chunk_completed_at_utc,
            "payload_filename": self.payload_filename,
            "payload_sha256": self.payload_sha256,
            "payload_byte_length": self.payload_byte_length,
            "accession_rows": self.accession_rows,
            "ledger_rows": self.ledger_rows,
            "semantic_payload_identity": self.semantic_payload_identity,
            "declarations_sha256": self.declarations_sha256,
            "declarations_byte_length": self.declarations_byte_length,
            "witness_attempt": self.witness_attempt,
            "pid": self.pid,
            "written_at_utc": self.written_at_utc,
        }

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        record = self._identity_inputs()
        record["witness_identity"] = self.witness_identity
        return record

    def identity(self) -> str:
        """The identity the record implies -- over everything but the identity field."""
        return _record_identity(self._identity_inputs(), "witness_identity")

    def meta_rows(self) -> tuple[tuple[str, str], ...]:
        """What the payload's own meta table must say, so the payload says what it is."""
        return (
            ("contract", self.contract),
            ("run_id", self.run_id),
            ("plan_digest", self.plan_digest),
            ("chunk_id", self.chunk_id),
            ("chunk_receipt_sha256", self.chunk_receipt_sha256),
        )

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationChunkWitness:  # noqa: PLR0915
        """Rebuild a witness from its EXACT mapping and re-derive its identity.

        Raises:
            ChunkMultipassError: the shape, contract, labels, region, interval, digests,
                declarations consistency or identity refuses.
        """
        _exact_keys(record, _WITNESS_KEYS, "calibration retained witness")
        declarations_sha256 = record["declarations_sha256"]
        declarations_length = record["declarations_byte_length"]
        witness = cls(
            contract=str(record["contract"]),
            classifications=_stored_labels(record["classifications"], "classifications"),
            run_id=str(record["run_id"]),
            plan_digest=_hex64(record["plan_digest"], "plan_digest"),
            merge_schedule_digest=_hex64(record["merge_schedule_digest"], "merge_schedule_digest"),
            chunk_id=str(record["chunk_id"]),
            chunk_ordinal=_stored_int(record["chunk_ordinal"], "chunk_ordinal"),
            region=str(record["region"]),
            start=_stored_int(record["start"], "start"),
            end=_stored_int(record["end"], "end"),
            member_order_digest=_hex64(record["member_order_digest"], "member_order_digest"),
            selected_member_order_digest=_hex64(
                record["selected_member_order_digest"], "selected_member_order_digest"
            ),
            shard_parent_binding_digest=_hex64(
                record["shard_parent_binding_digest"], "shard_parent_binding_digest"
            ),
            source_instance_id=str(record["source_instance_id"]),
            source_observation_id=str(record["source_observation_id"]),
            source_sha256=str(record["source_sha256"]),
            source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
            chunk_attempt=_stored_int(record["chunk_attempt"], "chunk_attempt"),
            chunk_receipt_sha256=_hex64(record["chunk_receipt_sha256"], "chunk_receipt_sha256"),
            chunk_manifest_digest=_hex64(record["chunk_manifest_digest"], "chunk_manifest_digest"),
            chunk_manifest_total_bytes=_stored_int(
                record["chunk_manifest_total_bytes"], "chunk_manifest_total_bytes"
            ),
            chunk_execution_identity=str(record["chunk_execution_identity"]),
            execution_contract_identity=str(record["execution_contract_identity"]),
            repository_head_sha=str(record["repository_head_sha"]),
            repository_tree_sha=str(record["repository_tree_sha"]),
            chunk_started_at_utc=str(record["chunk_started_at_utc"]),
            chunk_completed_at_utc=str(record["chunk_completed_at_utc"]),
            payload_filename=str(record["payload_filename"]),
            payload_sha256=_hex64(record["payload_sha256"], "payload_sha256"),
            payload_byte_length=_stored_int(record["payload_byte_length"], "payload_byte_length"),
            accession_rows=_stored_int(record["accession_rows"], "accession_rows"),
            ledger_rows=_stored_int(record["ledger_rows"], "ledger_rows"),
            semantic_payload_identity=_hex64(
                record["semantic_payload_identity"], "semantic_payload_identity"
            ),
            declarations_sha256=(
                None
                if declarations_sha256 is None
                else _hex64(declarations_sha256, "declarations_sha256")
            ),
            declarations_byte_length=(
                None
                if declarations_length is None
                else _stored_int(declarations_length, "declarations_byte_length")
            ),
            witness_attempt=_stored_int(record["witness_attempt"], "witness_attempt"),
            pid=_stored_int(record["pid"], "pid"),
            written_at_utc=str(record["written_at_utc"]),
            witness_identity=str(record["witness_identity"]),
        )
        _require(
            witness.contract == CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT,
            f"a retained witness carrying contract {witness.contract!r} is refused; this reader "
            f"consumes only {CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT!r}",
        )
        _require(
            witness.region in CHUNK_REGION_ORDER and 0 <= witness.start < witness.end,
            f"a retained witness for chunk {witness.chunk_id!r} names region {witness.region!r} "
            f"over [{witness.start}, {witness.end}); refused",
        )
        _require(
            witness.payload_filename == CALIBRATION_RETAINED_PAYLOAD_FILENAME,
            f"a retained witness names payload {witness.payload_filename!r}; refused",
        )
        primary = witness.region == REGION_PRIMARY
        _require(
            (witness.declarations_sha256 is not None) == primary
            and (witness.declarations_byte_length is not None) == primary,
            f"a retained witness for {witness.region} chunk {witness.chunk_id!r} must carry a "
            "declarations copy exactly when the chunk is a primary chunk; refused",
        )
        _require(
            witness.identity() == witness.witness_identity,
            "a retained witness's recorded identity does not describe its own contents: "
            f"recorded {witness.witness_identity!r}, recomputed {witness.identity()!r}",
        )
        return witness


@dataclass(frozen=True, slots=True)
class RetainedWitnessInput:
    """One validated retained witness, resolved to its one verified attempt directory.

    The final's counter source for a chunk whose world is gone: ``catalog_path`` and
    ``witness_path`` both name the payload, whose ``census_accessions`` and
    ``chunk_first_witness`` tables are the exact projections the accepted derivation reads.
    """

    chunk_id: str
    ordinal: int
    region: str
    start: int
    end: int
    directory: Path
    witness: CalibrationChunkWitness

    @property
    def payload_path(self) -> Path:
        """The retained payload database."""
        return self.directory / CALIBRATION_RETAINED_PAYLOAD_FILENAME

    @property
    def catalog_path(self) -> Path:
        """Where the derivation reads this chunk's ``census_accessions`` projection."""
        return self.payload_path

    @property
    def witness_path(self) -> Path:
        """Where the derivation reads this chunk's ``chunk_first_witness`` ledger."""
        return self.payload_path

    @property
    def declarations_path(self) -> Path:
        """The primary chunk's retained declarations copy."""
        return self.directory / CHUNK_DECLARATIONS_FILENAME


def _witness_attempt_directories(retained_root: Path, chunk_id: str) -> list[Path]:
    parent = retained_root / chunk_id
    if not parent.is_dir() or parent.is_symlink():
        return []
    return sorted(path for path in parent.iterdir() if path.is_dir() and not path.is_symlink())


def _retained_payload_identity(
    connection: sqlite3.Connection, catalog_alias: str, ledger_alias: str, *, chunk_id: str
) -> tuple[str, int, int]:
    """The content identity of one chunk's two projections, in a fixed order, and both row
    counts -- computed the same way from a chunk world and from its retained copy."""
    digest = hashlib.sha256()
    digest.update(f"{CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT}\x1f{chunk_id}".encode())
    digest.update(b"\x1e")
    accession_rows = 0
    for row in connection.execute(
        "SELECT accession_plain, parsed_record_id "  # noqa: S608 - alias is ours
        f"FROM {catalog_alias}.census_accessions ORDER BY accession_plain"
    ):
        digest.update("\x1f".join((str(row[0]), str(row[1]))).encode("utf-8"))
        digest.update(b"\x1e")
        accession_rows += 1
    digest.update(b"\x1d")
    ledger_rows = 0
    for row in connection.execute(
        "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "  # noqa: S608
        f"FROM {ledger_alias}.chunk_first_witness ORDER BY native_identity"
    ):
        digest.update(
            "\x1f".join((str(row[0]), str(row[1]), str(row[2]), str(row[3]))).encode("utf-8")
        )
        digest.update(b"\x1e")
        ledger_rows += 1
    return digest.hexdigest(), accession_rows, ledger_rows


def _verify_retained_witness_files(
    directory: Path, witness: CalibrationChunkWitness, *, deep: bool
) -> None:
    """Hold a witness directory to its record: exact file set, payload bytes, declarations
    bytes, the payload's own meta rows and row counts, and -- when ``deep`` -- the payload's
    recomputed content identity."""
    expected = {CALIBRATION_RETAINED_WITNESS_FILENAME, witness.payload_filename}
    if witness.region == REGION_PRIMARY:
        expected.add(CHUNK_DECLARATIONS_FILENAME)
    present: set[str] = set()
    for path in directory.iterdir():
        _require(
            not path.is_symlink() and path.is_file(),
            f"retained witness {witness.chunk_id!r} holds {path.name!r}, which is not a regular "
            "file; refused",
        )
        present.add(path.name)
    _require(
        present == expected,
        f"retained witness {witness.chunk_id!r} holds unexpected {sorted(present - expected)} "
        f"and lacks {sorted(expected - present)}; an inexact witness directory is refused",
    )
    sha256, length = file_sha256(directory / witness.payload_filename)
    _require(
        sha256 == witness.payload_sha256 and length == witness.payload_byte_length,
        f"retained witness {witness.chunk_id!r} payload digests to {sha256}/{length} where the "
        f"record seals {witness.payload_sha256}/{witness.payload_byte_length}; a changed payload "
        "is refused rather than re-read",
    )
    if witness.region == REGION_PRIMARY:
        sha256, length = file_sha256(directory / CHUNK_DECLARATIONS_FILENAME)
        _require(
            sha256 == witness.declarations_sha256 and length == witness.declarations_byte_length,
            f"retained witness {witness.chunk_id!r} declarations copy digests to {sha256} where "
            f"the record seals {witness.declarations_sha256}; refused",
        )
    payload = directory / witness.payload_filename
    connection = sqlite3.connect(f"file:{payload.resolve()}?immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        meta = tuple(
            (str(row["key"]), str(row["value"]))
            for row in connection.execute(
                "SELECT key, value FROM retained_witness_meta ORDER BY key"
            )
        )
        _require(
            meta == tuple(sorted(witness.meta_rows())),
            f"retained witness {witness.chunk_id!r} payload describes {dict(meta)} where the "
            f"record binds {dict(witness.meta_rows())}; refused",
        )
        accessions = connection.execute("SELECT COUNT(*) AS n FROM census_accessions").fetchone()
        ledger = connection.execute("SELECT COUNT(*) AS n FROM chunk_first_witness").fetchone()
        _require(
            (int(accessions["n"]), int(ledger["n"]))
            == (witness.accession_rows, witness.ledger_rows),
            f"retained witness {witness.chunk_id!r} payload holds {accessions['n']} accession "
            f"rows and {ledger['n']} ledger rows where the record seals {witness.accession_rows} "
            f"and {witness.ledger_rows}; refused",
        )
        if deep:
            identity, _rows, _ledger_rows = _retained_payload_identity(
                connection, "main", "main", chunk_id=witness.chunk_id
            )
            _require(
                identity == witness.semantic_payload_identity,
                f"retained witness {witness.chunk_id!r} payload content identity is "
                f"{identity!r} where the record seals {witness.semantic_payload_identity!r}; "
                "a stale or resealed payload is refused",
            )
    finally:
        connection.close()


def read_calibration_chunk_witness(
    directory: Path, *, deep: bool = False
) -> CalibrationChunkWitness:
    """One retained witness, read from its canonical bytes and held to its files, or a refusal.

    ``deep`` additionally recomputes the payload's content identity row by row -- the
    independent re-read the pre-deletion checkpoint performs; the final holds the payload to its
    sealed bytes and the record to its seal and to the checkpoint that bound it.

    Raises:
        ChunkMultipassError: the record is absent, a link, not canonical, not an exact witness,
            or the directory does not hold exactly what the record seals.
    """
    decoded, payload = _decoded_canonical_object(
        directory / CALIBRATION_RETAINED_WITNESS_FILENAME, "calibration retained witness"
    )
    witness = CalibrationChunkWitness.from_record(decoded)
    _require(
        canonical_json_bytes(witness.as_record()) == payload,
        f"retained witness {witness.chunk_id!r} is not persisted as its canonical bytes; refused",
    )
    _verify_retained_witness_files(directory, witness, deep=deep)
    return witness


def completed_calibration_chunk_witness(
    retained_root: Path, chunk_id: str
) -> tuple[CalibrationChunkWitness, Path] | None:
    """The one valid retained witness this chunk carries, or ``None``.

    Every attempt directory is inspected; one with no record never completed and is skipped; one
    WITH a record is verified and a record that fails to verify is a loud refusal, never "never
    ran" (the intermediate rule, D151-C13 §27). Two valid witnesses are ambiguous and refused.

    Raises:
        ChunkMultipassError: a present record does not verify, describes another chunk, or more
            than one attempt carries a valid record.
    """
    found: list[tuple[CalibrationChunkWitness, Path]] = []
    for directory in _witness_attempt_directories(retained_root, chunk_id):
        if not (directory / CALIBRATION_RETAINED_WITNESS_FILENAME).is_file():
            continue
        try:
            witness = read_calibration_chunk_witness(directory)
        except ChunkMultipassError as exc:
            message = (
                f"retained witness {chunk_id!r} attempt {directory.name!r} carries a record that "
                f"does not verify: {exc}. A changed witness is a changed artifact, not an attempt "
                "that never ran; the calibration STOPS rather than rebuilding beside it"
            )
            raise ChunkMultipassError(message) from exc
        _require(
            witness.chunk_id == chunk_id,
            f"retained witness attempt {directory.name!r} under {chunk_id!r} describes chunk "
            f"{witness.chunk_id!r}; refused",
        )
        found.append((witness, directory))
    if len(found) > 1:
        message = (
            f"chunk {chunk_id!r} carries {len(found)} valid retained witnesses, in "
            f"{[path.name for _, path in found]}. Duplicate authority is refused rather than "
            "resolved"
        )
        raise ChunkMultipassError(message)
    return found[0] if found else None


def next_calibration_witness_attempt_directory(
    retained_root: Path, chunk_id: str
) -> tuple[Path, int]:
    """The lowest unused witness attempt directory for one chunk, and its ordinal.

    Raises:
        ChunkMultipassError: the chunk already carries a valid witness -- a completed witness is
            immutable and is reused, never rewritten -- or a present record does not verify.
    """
    existing = completed_calibration_chunk_witness(retained_root, chunk_id)
    if existing is not None:
        message = (
            f"chunk {chunk_id!r} already carries a valid retained witness (attempt "
            f"{existing[0].witness_attempt}); a witness is create-once and is never rewritten"
        )
        raise ChunkMultipassError(message)
    attempt = 0
    while calibration_witness_attempt_directory(retained_root, chunk_id, attempt).exists():
        attempt += 1
    return calibration_witness_attempt_directory(retained_root, chunk_id, attempt), attempt


def write_calibration_chunk_witness(
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    *,
    chunk_id: str,
    run_id: str,
    chunk_root: Path,
    retained_root: Path,
    external_root: Path | None = None,
) -> tuple[CalibrationChunkWitness, Path]:
    """Write one chunk's retained witness, create-once, after its terminal authenticated -- §6.

    In order: the sealed subset plan and schedule are required; the chunk is resolved through
    the accepted admission (a chunk with no verified terminal receipt refuses here, so a witness
    is never written before the chunk is terminal); the payload is built by attaching the chunk
    world immutably and copying exactly the two projected tables in a fixed order; the content
    identity is computed from the SOURCE and from the COPY and the two must agree; a primary
    chunk's declarations are re-serialized through the accepted writer and held byte-identical to
    the chunk's manifested entry; the sealed record is written LAST; and the witness is then
    independently re-read, deep, before it is returned.

    Raises:
        ChunkMultipassError: the chunk already carries a witness, the copy is not exact, or the
            re-read refuses.
        ChunkPlanError, ChunkConsolidationError, ChunkStorageError, ChunkEvidenceError: the
            chunk is not an authenticated terminal member of this plan.
    """
    require_calibration_subset_plan(plan)
    require_sealed_schedule(schedule, plan)
    (chunk,) = resolve_contiguous_chunk_inputs(
        plan, (chunk_id,), internal_root=chunk_root, external_root=external_root
    )
    attempt_directory, attempt = next_calibration_witness_attempt_directory(retained_root, chunk_id)
    receipt_sha256, _receipt_length = file_sha256(chunk.directory / CHUNK_RECEIPT_FILENAME)
    attempt_directory.mkdir(mode=_DIRECTORY_MODE, parents=True)
    payload_path = attempt_directory / CALIBRATION_RETAINED_PAYLOAD_FILENAME
    connection = sqlite3.connect(payload_path, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(_RETAINED_PAYLOAD_SCHEMA)
        catalogs = _attach_all(connection, [chunk.catalog_path], "pc")
        ledgers = _attach_all(connection, [chunk.witness_path], "pw")
        try:
            connection.execute(
                "INSERT INTO main.census_accessions (accession_plain, parsed_record_id) "  # noqa: S608
                f"SELECT accession_plain, parsed_record_id FROM {catalogs[0]}.census_accessions "
                "ORDER BY accession_plain"
            )
            connection.execute(
                "INSERT INTO main.chunk_first_witness (native_identity, member_ordinal, "  # noqa: S608
                "record_ordinal, delta_materialized) "
                "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                f"FROM {ledgers[0]}.chunk_first_witness ORDER BY native_identity"
            )
            source_identity, source_rows, source_ledger = _retained_payload_identity(
                connection, catalogs[0], ledgers[0], chunk_id=chunk_id
            )
            copy_identity, accession_rows, ledger_rows = _retained_payload_identity(
                connection, "main", "main", chunk_id=chunk_id
            )
            _require(
                (copy_identity, accession_rows, ledger_rows)
                == (source_identity, source_rows, source_ledger),
                f"the retained payload of chunk {chunk_id!r} is not an exact copy of the chunk's "
                "projections; nothing is sealed over an inexact copy",
            )
        finally:
            _detach_all(connection, ledgers)
            _detach_all(connection, catalogs)
        connection.executemany(
            "INSERT INTO main.retained_witness_meta (key, value) VALUES (?, ?)",
            [
                ("contract", CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT),
                ("run_id", run_id),
                ("plan_digest", plan.plan_digest),
                ("chunk_id", chunk_id),
                ("chunk_receipt_sha256", receipt_sha256),
            ],
        )
    finally:
        connection.close()
    declarations_sha256: str | None = None
    declarations_length: int | None = None
    if chunk.region == REGION_PRIMARY:
        entry = next(
            item
            for item in chunk.receipt.manifest.entries
            if item.relative_path == CHUNK_DECLARATIONS_FILENAME
        )
        declared = read_declarations(chunk.directory / CHUNK_DECLARATIONS_FILENAME)
        write_once_json(
            attempt_directory / CHUNK_DECLARATIONS_FILENAME,
            {name: sorted(parents) for name, parents in sorted(declared.items())},
        )
        declarations_sha256, declarations_length = file_sha256(
            attempt_directory / CHUNK_DECLARATIONS_FILENAME
        )
        _require(
            declarations_sha256 == entry.sha256 and declarations_length == entry.byte_length,
            f"the retained declarations copy of chunk {chunk_id!r} is not byte-identical to the "
            "chunk's manifested declarations; refused",
        )
    payload_sha256, payload_length = file_sha256(payload_path)
    witness = CalibrationChunkWitness(
        contract=CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        run_id=run_id,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        chunk_id=chunk_id,
        chunk_ordinal=chunk.ordinal,
        region=chunk.region,
        start=chunk.start,
        end=chunk.end,
        member_order_digest=plan.member_order_digest,
        selected_member_order_digest=plan.selected_member_order_digest,
        shard_parent_binding_digest=plan.shard_parent_binding_digest,
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        source_byte_length=plan.source_byte_length,
        chunk_attempt=chunk.receipt.attempt,
        chunk_receipt_sha256=receipt_sha256,
        chunk_manifest_digest=chunk.receipt.manifest.digest,
        chunk_manifest_total_bytes=chunk.receipt.manifest.total_bytes,
        chunk_execution_identity=chunk.receipt.execution_identity,
        execution_contract_identity=chunk.receipt.execution_contract.contract_identity,
        repository_head_sha=chunk.receipt.repository_head_sha,
        repository_tree_sha=chunk.receipt.repository_tree_sha,
        chunk_started_at_utc=chunk.receipt.started_at_utc,
        chunk_completed_at_utc=chunk.receipt.completed_at_utc,
        payload_filename=CALIBRATION_RETAINED_PAYLOAD_FILENAME,
        payload_sha256=payload_sha256,
        payload_byte_length=payload_length,
        accession_rows=accession_rows,
        ledger_rows=ledger_rows,
        semantic_payload_identity=copy_identity,
        declarations_sha256=declarations_sha256,
        declarations_byte_length=declarations_length,
        witness_attempt=attempt,
        pid=os.getpid(),
        written_at_utc=utc_now(),
        witness_identity="",
    )
    sealed = replace(witness, witness_identity=witness.identity())
    # LAST. A witness that stopped anywhere above leaves an attempt with no record.
    write_once_canonical_json(
        attempt_directory / CALIBRATION_RETAINED_WITNESS_FILENAME, dict(sealed.as_record())
    )
    reread = read_calibration_chunk_witness(attempt_directory, deep=True)
    _require(
        reread == sealed,
        f"the retained witness of chunk {chunk_id!r} did not re-read as what was sealed; refused",
    )
    return sealed, attempt_directory


def _require_witness_binds_plan(
    witness: CalibrationChunkWitness,
    *,
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    run_id: str,
    ordinal: int,
    bounds: ChunkBounds,
) -> None:
    _require(
        witness.run_id == run_id
        and witness.plan_digest == plan.plan_digest
        and witness.merge_schedule_digest == schedule.schedule_digest,
        f"retained witness {witness.chunk_id!r} binds run {witness.run_id!r} / plan "
        f"{witness.plan_digest[:16]}... / schedule {witness.merge_schedule_digest[:16]}... "
        f"where this calibration is run {run_id!r} / plan {plan.plan_digest[:16]}... / "
        f"schedule {schedule.schedule_digest[:16]}...; a witness of another run is never admitted",
    )
    _require(
        (witness.chunk_id, witness.chunk_ordinal, witness.region, witness.start, witness.end)
        == (bounds.chunk_id, ordinal, bounds.region, bounds.start, bounds.end),
        f"retained witness {witness.chunk_id!r} records ordinal {witness.chunk_ordinal} "
        f"{witness.region}[{witness.start}, {witness.end}) where the plan assigns ordinal "
        f"{ordinal} {bounds.region}[{bounds.start}, {bounds.end}) to {bounds.chunk_id!r}",
    )
    _require(
        witness.member_order_digest == plan.member_order_digest
        and witness.selected_member_order_digest == plan.selected_member_order_digest
        and witness.shard_parent_binding_digest == plan.shard_parent_binding_digest
        and witness.source_instance_id == plan.source_instance_id
        and witness.source_observation_id == plan.source_observation_id
        and witness.source_sha256 == plan.source_sha256
        and witness.source_byte_length == plan.source_byte_length,
        f"retained witness {witness.chunk_id!r} names a source, observation, artifact or "
        "ordering the plan does not",
    )


def _require_witness_matches_chunk(
    witness: CalibrationChunkWitness, receipt: ChunkReceipt, directory: Path
) -> None:
    """Hold an existing witness to the chunk world beside it, while that world still exists."""
    observed, _length = file_sha256(directory / CHUNK_RECEIPT_FILENAME)
    _require(
        observed == witness.chunk_receipt_sha256
        and receipt.manifest.digest == witness.chunk_manifest_digest
        and receipt.attempt == witness.chunk_attempt
        and receipt.execution_identity == witness.chunk_execution_identity,
        f"retained witness {witness.chunk_id!r} binds receipt {witness.chunk_receipt_sha256[:16]}"
        f"... attempt {witness.chunk_attempt} and the chunk's one authoritative copy now carries "
        f"receipt {observed[:16]}... attempt {receipt.attempt}; a witness is never admitted "
        "beside a chunk other than the one it was taken from",
    )


def _refuse_foreign_retained_entries(
    plan: CalibrationSubsetPlan, schedule: MergeSchedule, retained_root: Path
) -> None:
    if not retained_root.is_dir():
        return
    known_directories = {bounds.chunk_id for bounds in plan.chunks}
    known_files = {
        calibration_group_checkpoint_path(retained_root, g.group_id).name for g in schedule.groups
    }
    known_files |= {
        calibration_group_deletion_path(retained_root, g.group_id).name for g in schedule.groups
    }
    foreign = sorted(
        path.name
        for path in retained_root.iterdir()
        if path.is_symlink()
        or (path.is_dir() and path.name not in known_directories)
        or (path.is_file() and path.name not in known_files)
        or not (path.is_dir() or path.is_file())
    )
    _require(
        not foreign,
        f"{len(foreign)} entry/entries are present under the retained root that this plan and "
        f"schedule do not name: {foreign[:8]}. An extra witness or record belongs to some other "
        "run, and a finalizer that ignored it would be choosing between two answers silently",
    )


def resolve_calibration_chunk_witnesses(
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    *,
    run_id: str,
    retained_root: Path,
) -> tuple[RetainedWitnessInput, ...]:
    """Resolve every chunk of the plan to exactly one verified retained witness -- P3, P5.

    Every witness must belong to ONE execution of ONE schedule of ONE plan under ONE run, proved
    rather than assumed: the record binds this run, plan and schedule, names exactly the chunk,
    ordinal, kind and selected interval the plan assigns, names the plan's source and both
    orderings; the intervals together cover the selected members exactly once; every witness
    names the same repository revision and the same execution contract identity; the payload's
    bytes and the declarations copy are held to the seal; and nothing the plan and schedule do
    not name is present under the retained root. No chunk world is opened or required.

    Raises:
        ChunkMultipassError: any of them.
    """
    _refuse_foreign_retained_entries(plan, schedule, retained_root)
    inputs: list[RetainedWitnessInput] = []
    head: str | None = None
    tree: str | None = None
    contract_identity: str | None = None
    cursor = 0
    for ordinal, bounds in enumerate(plan.chunks):
        found = completed_calibration_chunk_witness(retained_root, bounds.chunk_id)
        _require(
            found is not None,
            f"chunk {bounds.chunk_id!r} has no valid retained witness. A missing witness is "
            "never treated as empty, skipped, reconstructed or re-derived from a chunk world",
        )
        assert found is not None  # noqa: S101 - narrowed by the refusal above
        witness, directory = found
        _require_witness_binds_plan(
            witness, plan=plan, schedule=schedule, run_id=run_id, ordinal=ordinal, bounds=bounds
        )
        _require(
            witness.start == cursor,
            f"retained witness {bounds.chunk_id!r} starts at {witness.start} where {cursor} was "
            "required: the admitted witnesses leave a gap or overlap",
        )
        if head is None:
            head, tree = witness.repository_head_sha, witness.repository_tree_sha
            contract_identity = witness.execution_contract_identity
        _require(
            witness.repository_head_sha == head
            and witness.repository_tree_sha == tree
            and witness.execution_contract_identity == contract_identity,
            f"retained witness {bounds.chunk_id!r} was taken from a chunk that executed under "
            f"{witness.repository_head_sha}/{witness.repository_tree_sha} with contract "
            f"{witness.execution_contract_identity[:16]}... where an earlier chunk executed "
            f"under {head}/{tree} with {str(contract_identity)[:16]}...",
        )
        inputs.append(
            RetainedWitnessInput(
                chunk_id=bounds.chunk_id,
                ordinal=ordinal,
                region=bounds.region,
                start=bounds.start,
                end=bounds.end,
                directory=directory,
                witness=witness,
            )
        )
        cursor = witness.end
    _require(
        cursor == plan.total_members,
        f"the admitted witnesses cover [0, {cursor}) of {plan.total_members} selected members",
    )
    return tuple(inputs)


# --------------------------------------------------------------------------- #
# The group checkpoint -- what makes a chunk world deletable (§7)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CheckpointChunkBinding:
    """One chunk inside a group checkpoint: its receipt, its exact manifest, its witness."""

    chunk_id: str
    ordinal: int
    attempt: int
    receipt_sha256: str
    manifest: ArtifactManifest
    witness_attempt: int
    witness_identity: str
    payload_sha256: str

    @property
    def entries(self) -> tuple[str, ...]:
        """Every object the chunk world holds: the manifested set plus the receipt, sorted."""
        return tuple(
            sorted(
                [*(entry.relative_path for entry in self.manifest.entries), CHUNK_RECEIPT_FILENAME]
            )
        )

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        return {
            "chunk_id": self.chunk_id,
            "ordinal": self.ordinal,
            "attempt": self.attempt,
            "receipt_sha256": self.receipt_sha256,
            "manifest": dict(self.manifest.as_record()),
            "witness_attempt": self.witness_attempt,
            "witness_identity": self.witness_identity,
            "payload_sha256": self.payload_sha256,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CheckpointChunkBinding:
        """Rebuild one binding from its EXACT mapping.

        Raises:
            ChunkMultipassError: the shape or a field refuses.
        """
        _exact_keys(record, _CHECKPOINT_CHUNK_KEYS, "checkpoint chunk binding")
        manifest = record["manifest"]
        _require(
            isinstance(manifest, Mapping), "a checkpoint chunk binding's manifest is not a mapping"
        )
        try:
            rebuilt = ArtifactManifest.from_record(cast("Mapping[str, object]", manifest))
        except ChunkEvidenceError as exc:
            message = f"a checkpoint chunk binding's manifest is refused: {exc}"
            raise ChunkMultipassError(message) from exc
        return cls(
            chunk_id=str(record["chunk_id"]),
            ordinal=_stored_int(record["ordinal"], "ordinal"),
            attempt=_stored_int(record["attempt"], "attempt"),
            receipt_sha256=_hex64(record["receipt_sha256"], "receipt_sha256"),
            manifest=rebuilt,
            witness_attempt=_stored_int(record["witness_attempt"], "witness_attempt"),
            witness_identity=_hex64(record["witness_identity"], "witness_identity"),
            payload_sha256=_hex64(record["payload_sha256"], "payload_sha256"),
        )


@dataclass(frozen=True, slots=True)
class CalibrationGroupCheckpoint:
    """One group's create-once checkpoint -- §7 step 4: chunk receipt, witness, intermediate.

    Written by the orchestrator only after every chunk of the group is terminal and verified,
    every witness has been independently re-read (deep), and the group's intermediate is terminal
    and bound to exactly those chunk receipts. Sealed by ``checkpoint_identity``.
    """

    event_kind: str
    classifications: tuple[str, ...]
    run_id: str
    plan_digest: str
    merge_schedule_digest: str
    group_id: str
    group_ordinal: int
    region: str
    start: int
    end: int
    chunks: tuple[CheckpointChunkBinding, ...]
    intermediate_attempt: int
    intermediate_receipt_sha256: str
    intermediate_manifest_digest: str
    intermediate_catalog_sha256: str
    pid: int
    written_at_utc: str
    checkpoint_identity: str

    def _identity_inputs(self) -> dict[str, object]:
        return {
            "event_kind": self.event_kind,
            "classifications": list(self.classifications),
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "group_id": self.group_id,
            "group_ordinal": self.group_ordinal,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "chunks": [dict(item.as_record()) for item in self.chunks],
            "intermediate_attempt": self.intermediate_attempt,
            "intermediate_receipt_sha256": self.intermediate_receipt_sha256,
            "intermediate_manifest_digest": self.intermediate_manifest_digest,
            "intermediate_catalog_sha256": self.intermediate_catalog_sha256,
            "pid": self.pid,
            "written_at_utc": self.written_at_utc,
        }

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        record = self._identity_inputs()
        record["checkpoint_identity"] = self.checkpoint_identity
        return record

    def identity(self) -> str:
        """The identity the record implies -- over everything but the identity field."""
        return _record_identity(self._identity_inputs(), "checkpoint_identity")

    @property
    def chunk_ids(self) -> tuple[str, ...]:
        """The bound chunks, in group order."""
        return tuple(item.chunk_id for item in self.chunks)

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationGroupCheckpoint:
        """Rebuild a checkpoint from its EXACT mapping and re-derive its identity.

        Raises:
            ChunkMultipassError: the shape, kind, labels, bindings or identity refuses.
        """
        _exact_keys(record, _CHECKPOINT_KEYS, "calibration group checkpoint")
        chunks = record["chunks"]
        _require(
            isinstance(chunks, list) and bool(chunks),
            "a calibration group checkpoint's chunks must be a non-empty list",
        )
        checkpoint = cls(
            event_kind=str(record["event_kind"]),
            classifications=_stored_labels(record["classifications"], "classifications"),
            run_id=str(record["run_id"]),
            plan_digest=_hex64(record["plan_digest"], "plan_digest"),
            merge_schedule_digest=_hex64(record["merge_schedule_digest"], "merge_schedule_digest"),
            group_id=str(record["group_id"]),
            group_ordinal=_stored_int(record["group_ordinal"], "group_ordinal"),
            region=str(record["region"]),
            start=_stored_int(record["start"], "start"),
            end=_stored_int(record["end"], "end"),
            chunks=tuple(
                CheckpointChunkBinding.from_record(
                    cast("Mapping[str, object]", item) if isinstance(item, Mapping) else {}
                )
                for item in cast("list[object]", chunks)
            ),
            intermediate_attempt=_stored_int(
                record["intermediate_attempt"], "intermediate_attempt"
            ),
            intermediate_receipt_sha256=_hex64(
                record["intermediate_receipt_sha256"], "intermediate_receipt_sha256"
            ),
            intermediate_manifest_digest=_hex64(
                record["intermediate_manifest_digest"], "intermediate_manifest_digest"
            ),
            intermediate_catalog_sha256=_hex64(
                record["intermediate_catalog_sha256"], "intermediate_catalog_sha256"
            ),
            pid=_stored_int(record["pid"], "pid"),
            written_at_utc=str(record["written_at_utc"]),
            checkpoint_identity=str(record["checkpoint_identity"]),
        )
        _require(
            checkpoint.event_kind == CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND,
            f"a calibration group checkpoint of kind {checkpoint.event_kind!r} is refused",
        )
        _require(
            len({item.chunk_id for item in checkpoint.chunks}) == len(checkpoint.chunks),
            "a calibration group checkpoint repeats a chunk; refused",
        )
        _require(
            checkpoint.identity() == checkpoint.checkpoint_identity,
            "a calibration group checkpoint's recorded identity does not describe its own "
            f"contents: recorded {checkpoint.checkpoint_identity!r}, recomputed "
            f"{checkpoint.identity()!r}",
        )
        return checkpoint


def read_calibration_group_checkpoint(path: Path) -> CalibrationGroupCheckpoint:
    """One group checkpoint, read from its canonical bytes, or a refusal.

    Raises:
        ChunkMultipassError: the file is absent, a link, not canonical, or not an exact record.
    """
    decoded, payload = _decoded_canonical_object(path, "calibration group checkpoint")
    checkpoint = CalibrationGroupCheckpoint.from_record(decoded)
    _require(
        canonical_json_bytes(checkpoint.as_record()) == payload,
        f"checkpoint {path.name!r} is not persisted as its canonical bytes; refused",
    )
    return checkpoint


def _require_checkpoint_binds_group(
    checkpoint: CalibrationGroupCheckpoint,
    *,
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    group: MergeGroup,
    run_id: str,
) -> None:
    _require(
        checkpoint.run_id == run_id
        and checkpoint.plan_digest == plan.plan_digest
        and checkpoint.merge_schedule_digest == schedule.schedule_digest,
        f"checkpoint {checkpoint.group_id!r} binds run {checkpoint.run_id!r} / plan "
        f"{checkpoint.plan_digest[:16]}... / schedule {checkpoint.merge_schedule_digest[:16]}"
        f"... where this calibration is run {run_id!r} / plan {plan.plan_digest[:16]}... / "
        f"schedule {schedule.schedule_digest[:16]}...; refused",
    )
    _require(
        (
            checkpoint.group_id,
            checkpoint.group_ordinal,
            checkpoint.region,
            checkpoint.start,
            checkpoint.end,
        )
        == (group.group_id, group.ordinal, group.region, group.start, group.end)
        and checkpoint.chunk_ids == group.chunk_ids,
        f"checkpoint {checkpoint.group_id!r} records ordinal {checkpoint.group_ordinal} "
        f"{checkpoint.region}[{checkpoint.start}, {checkpoint.end}) over "
        f"{list(checkpoint.chunk_ids)} where the schedule assigns ordinal {group.ordinal} "
        f"{group.region}[{group.start}, {group.end}) over {list(group.chunk_ids)}",
    )


def _require_checkpoint_binds_witnesses(
    checkpoint: CalibrationGroupCheckpoint, witnesses: Mapping[str, CalibrationChunkWitness]
) -> None:
    for binding in checkpoint.chunks:
        witness = witnesses.get(binding.chunk_id)
        _require(
            witness is not None,
            f"checkpoint {checkpoint.group_id!r} binds chunk {binding.chunk_id!r}, which carries "
            "no retained witness; refused",
        )
        assert witness is not None  # noqa: S101 - narrowed above
        _require(
            witness.witness_identity == binding.witness_identity
            and witness.witness_attempt == binding.witness_attempt
            and witness.payload_sha256 == binding.payload_sha256
            and witness.chunk_receipt_sha256 == binding.receipt_sha256
            and witness.chunk_manifest_digest == binding.manifest.digest
            and witness.chunk_attempt == binding.attempt
            and witness.chunk_ordinal == binding.ordinal,
            f"checkpoint {checkpoint.group_id!r} bound chunk {binding.chunk_id!r} by witness "
            f"{binding.witness_identity[:16]}... over receipt {binding.receipt_sha256[:16]}... "
            f"and the retained witness present now is {witness.witness_identity[:16]}... over "
            f"receipt {witness.chunk_receipt_sha256[:16]}...; a resealed or substituted witness "
            "is refused",
        )


def _require_checkpoint_binds_intermediate(
    checkpoint: CalibrationGroupCheckpoint, receipt: IntermediateReceipt, directory: Path
) -> None:
    observed, _length = file_sha256(directory / INTERMEDIATE_RECEIPT_FILENAME)
    _require(
        observed == checkpoint.intermediate_receipt_sha256
        and receipt.manifest.digest == checkpoint.intermediate_manifest_digest
        and receipt.catalog_sha256 == checkpoint.intermediate_catalog_sha256
        and receipt.attempt == checkpoint.intermediate_attempt,
        f"checkpoint {checkpoint.group_id!r} binds intermediate receipt "
        f"{checkpoint.intermediate_receipt_sha256[:16]}... attempt "
        f"{checkpoint.intermediate_attempt} and the intermediate present now carries receipt "
        f"{observed[:16]}... attempt {receipt.attempt}; refused",
    )


def _require_intermediate_binds_chunks(
    receipt: IntermediateReceipt, group: MergeGroup, inputs: Sequence[ChunkInput]
) -> tuple[str, ...]:
    """The intermediate's bound receipt digests, held to the chunk worlds present now."""
    _require(
        receipt.input_chunk_ids == group.chunk_ids
        and tuple(item.chunk_id for item in inputs) == group.chunk_ids,
        f"intermediate {receipt.group_id!r} was merged from {list(receipt.input_chunk_ids)} "
        f"where the schedule assigns {list(group.chunk_ids)}; refused",
    )
    observed: list[str] = []
    for item, bound_sha256, bound_manifest in zip(
        inputs, receipt.input_receipt_sha256, receipt.input_manifest_digests, strict=True
    ):
        sha256, _length = file_sha256(item.directory / CHUNK_RECEIPT_FILENAME)
        _require(
            sha256 == bound_sha256 and item.receipt.manifest.digest == bound_manifest,
            f"intermediate {receipt.group_id!r} bound input chunk {item.chunk_id!r} by receipt "
            f"digest {bound_sha256!r} and the chunk's one authoritative copy now carries "
            f"{sha256!r}; an intermediate is never checkpointed over inputs other than the ones "
            "it was merged from",
        )
        observed.append(sha256)
    return tuple(observed)


def write_calibration_group_checkpoint(
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    *,
    group_id: str,
    run_id: str,
    chunk_root: Path,
    retained_root: Path,
    intermediates_root: Path,
    external_root: Path | None = None,
) -> CalibrationGroupCheckpoint:
    """Write one group's checkpoint, create-once, after chunk + witness + intermediate -- §7.

    In order: the sealed plan and schedule; the group; no checkpoint yet; this group's chunk
    worlds resolved through the accepted admission (terminal, verified, this plan); every chunk's
    retained witness independently re-read DEEP and held to the chunk beside it; the group's
    intermediate terminal, verified, and bound to exactly these chunk receipts; then the record.
    Nothing here deletes anything.

    Raises:
        ChunkMultipassError, ChunkPlanError, ChunkConsolidationError, ChunkStorageError,
        ChunkEvidenceError: any proof fails.
    """
    require_calibration_subset_plan(plan)
    require_sealed_schedule(schedule, plan)
    group = group_by_id(schedule, group_id)
    path = calibration_group_checkpoint_path(retained_root, group_id)
    _require(
        not path.exists() and not path.is_symlink(),
        f"group {group_id!r} already carries a checkpoint; a checkpoint is create-once",
    )
    inputs = resolve_contiguous_chunk_inputs(
        plan, group.chunk_ids, internal_root=chunk_root, external_root=external_root
    )
    bindings: list[CheckpointChunkBinding] = []
    for item in inputs:
        found = completed_calibration_chunk_witness(retained_root, item.chunk_id)
        _require(
            found is not None,
            f"chunk {item.chunk_id!r} carries no retained witness; a checkpoint is never written "
            "-- and a chunk world is never deletable -- without one",
        )
        assert found is not None  # noqa: S101 - narrowed above
        witness, directory = found
        read_calibration_chunk_witness(directory, deep=True)
        _require_witness_binds_plan(
            witness,
            plan=plan,
            schedule=schedule,
            run_id=run_id,
            ordinal=item.ordinal,
            bounds=chunk_by_id(plan, item.chunk_id),
        )
        _require_witness_matches_chunk(witness, item.receipt, item.directory)
        bindings.append(
            CheckpointChunkBinding(
                chunk_id=item.chunk_id,
                ordinal=item.ordinal,
                attempt=item.receipt.attempt,
                receipt_sha256=witness.chunk_receipt_sha256,
                manifest=item.receipt.manifest,
                witness_attempt=witness.witness_attempt,
                witness_identity=witness.witness_identity,
                payload_sha256=witness.payload_sha256,
            )
        )
    found_intermediate = completed_intermediate_receipt(intermediates_root, group_id)
    _require(
        found_intermediate is not None,
        f"group {group_id!r} carries no valid intermediate; a checkpoint is never written -- and "
        "a chunk world is never deletable -- before its level-one intermediate is terminal",
    )
    assert found_intermediate is not None  # noqa: S101 - narrowed above
    receipt, directory = found_intermediate
    _require(
        receipt.plan_digest == plan.plan_digest
        and receipt.merge_schedule_digest == schedule.schedule_digest
        and (receipt.group_ordinal, receipt.region, receipt.start, receipt.end)
        == (group.ordinal, group.region, group.start, group.end),
        f"intermediate {group_id!r} does not describe this plan, schedule and group; refused",
    )
    _require_intermediate_binds_chunks(receipt, group, inputs)
    intermediate_sha256, _length = file_sha256(directory / INTERMEDIATE_RECEIPT_FILENAME)
    checkpoint = CalibrationGroupCheckpoint(
        event_kind=CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        run_id=run_id,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_id=group.group_id,
        group_ordinal=group.ordinal,
        region=group.region,
        start=group.start,
        end=group.end,
        chunks=tuple(bindings),
        intermediate_attempt=receipt.attempt,
        intermediate_receipt_sha256=intermediate_sha256,
        intermediate_manifest_digest=receipt.manifest.digest,
        intermediate_catalog_sha256=receipt.catalog_sha256,
        pid=os.getpid(),
        written_at_utc=utc_now(),
        checkpoint_identity="",
    )
    sealed = replace(checkpoint, checkpoint_identity=checkpoint.identity())
    try:
        write_once_canonical_json(path, dict(sealed.as_record()))
    except ChunkExecutionError as exc:
        message = f"the calibration group checkpoint could not be written: {exc}"
        raise ChunkMultipassError(message) from exc
    return sealed


def resolve_calibration_group_checkpoints(
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    *,
    run_id: str,
    retained_root: Path,
    witnesses: Sequence[RetainedWitnessInput],
) -> tuple[CalibrationGroupCheckpoint, ...]:
    """Every group's checkpoint, each binding this run, plan, schedule and group, and each of
    its chunk bindings held to the resolved witness -- identity, attempt, payload, receipt.

    Raises:
        ChunkMultipassError: a checkpoint is absent, does not verify, or binds other witnesses.
    """
    by_id = {item.chunk_id: item.witness for item in witnesses}
    checkpoints: list[CalibrationGroupCheckpoint] = []
    for group in schedule.groups:
        checkpoint = read_calibration_group_checkpoint(
            calibration_group_checkpoint_path(retained_root, group.group_id)
        )
        _require_checkpoint_binds_group(
            checkpoint, plan=plan, schedule=schedule, group=group, run_id=run_id
        )
        _require_checkpoint_binds_witnesses(checkpoint, by_id)
        checkpoints.append(checkpoint)
    return tuple(checkpoints)


def _require_witness_bound_intermediates(
    intermediates: Sequence[IntermediateInput],
    witnesses: Sequence[RetainedWitnessInput],
    checkpoints: Sequence[CalibrationGroupCheckpoint],
) -> None:
    """Hold every intermediate to its bound chunk receipts THROUGH the witnesses and checkpoints
    -- the retention-aware form of :func:`_require_bound_chunk_receipts`, which needs no chunk
    world: the digest an intermediate bound must be the digest its chunk's witness sealed and
    the digest the group checkpoint bound beside that witness and beside this intermediate."""
    by_chunk = {item.chunk_id: item.witness for item in witnesses}
    by_group = {item.group_id: item for item in checkpoints}
    for intermediate in intermediates:
        receipt = intermediate.receipt
        checkpoint = by_group.get(intermediate.group_id)
        _require(
            checkpoint is not None,
            f"intermediate {intermediate.group_id!r} has no checkpoint; refused",
        )
        assert checkpoint is not None  # noqa: S101 - narrowed above
        _require_checkpoint_binds_intermediate(checkpoint, receipt, intermediate.directory)
        bound_by_id = {item.chunk_id: item for item in checkpoint.chunks}
        for chunk_id, bound_sha256, bound_manifest in zip(
            receipt.input_chunk_ids,
            receipt.input_receipt_sha256,
            receipt.input_manifest_digests,
            strict=True,
        ):
            witness = by_chunk.get(chunk_id)
            binding = bound_by_id.get(chunk_id)
            _require(
                witness is not None and binding is not None,
                f"intermediate {intermediate.group_id!r} binds input chunk {chunk_id!r}, which "
                "the resolved witnesses or the checkpoint do not carry; refused",
            )
            assert witness is not None and binding is not None  # noqa: S101 - narrowed above
            _require(
                witness.chunk_receipt_sha256 == bound_sha256
                and witness.chunk_manifest_digest == bound_manifest
                and binding.receipt_sha256 == bound_sha256
                and binding.manifest.digest == bound_manifest,
                f"intermediate {intermediate.group_id!r} bound input chunk {chunk_id!r} by "
                f"receipt digest {bound_sha256!r} and manifest {bound_manifest!r}, and the "
                f"chunk's retained witness seals receipt {witness.chunk_receipt_sha256!r}. An "
                "intermediate is never admitted over inputs other than the ones it was merged "
                "from",
            )


# --------------------------------------------------------------------------- #
# Exact calibration deletion -- grant FIRST, then the checkpoint, then the accepted primitive
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class CalibrationDeletionGrant:
    """An explicit, typed calibration deletion grant -- §7, the first effective gate.

    Not an authority: it is a caller-constructed statement that THIS run of THIS plan under THIS
    schedule may exact-delete the chunk worlds of exactly ``group_ids`` after their checkpoints
    exist. No production reclaim, transfer or execution authority is read, opened or implied by
    it, and no production path constructs one.
    """

    run_id: str
    plan_digest: str
    merge_schedule_digest: str
    group_ids: tuple[str, ...]

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "group_ids": list(self.group_ids),
        }

    def identity(self) -> str:
        """A digest over the grant, recorded by every deletion it admitted."""
        return hashlib.sha256(canonical_json_bytes(self.as_record())).hexdigest()


def _require_calibration_deletion_grant(
    grant: object, *, run_id: str, plan_digest: str, merge_schedule_digest: str, group_id: str
) -> CalibrationDeletionGrant:
    if not isinstance(grant, CalibrationDeletionGrant):
        message = (
            "a calibration deletion removes a chunk world only under an explicit "
            "CalibrationDeletionGrant; none was supplied. A checkpoint, a witness, an intermediate "
            "and a completed run are each necessary and none of them is this"
        )
        raise ChunkMultipassError(message)
    _require(
        grant.run_id == run_id
        and grant.plan_digest == plan_digest
        and grant.merge_schedule_digest == merge_schedule_digest
        and group_id in grant.group_ids,
        f"the calibration deletion grant names run {grant.run_id!r} / plan "
        f"{grant.plan_digest[:16]}... / schedule {grant.merge_schedule_digest[:16]}... over "
        f"groups {list(grant.group_ids)}, and this deletion is run {run_id!r} / plan "
        f"{plan_digest[:16]}... / schedule {merge_schedule_digest[:16]}... group {group_id!r}; "
        "nothing is deleted",
    )
    return grant


@dataclass(frozen=True, slots=True)
class DeletedChunkWorld:
    """One chunk world's exact deletion, as the deletion record carries it."""

    chunk_id: str
    attempt: int
    entries: tuple[str, ...]
    entries_deleted: int
    resumed: bool

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        return {
            "chunk_id": self.chunk_id,
            "attempt": self.attempt,
            "entries": list(self.entries),
            "entries_deleted": self.entries_deleted,
            "resumed": self.resumed,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> DeletedChunkWorld:
        """Rebuild one deleted world from its EXACT mapping.

        Raises:
            ChunkMultipassError: the shape or a field refuses.
        """
        _exact_keys(record, _DELETION_CHUNK_KEYS, "deleted chunk world")
        return cls(
            chunk_id=str(record["chunk_id"]),
            attempt=_stored_int(record["attempt"], "attempt"),
            entries=_stored_strings(record["entries"], "entries"),
            entries_deleted=_stored_int(record["entries_deleted"], "entries_deleted"),
            resumed=_stored_bool(record["resumed"], "resumed"),
        )


@dataclass(frozen=True, slots=True)
class CalibrationGroupDeletion:
    """One group's create-once deletion-complete record -- §7. Never a production reclaim."""

    event_kind: str
    classifications: tuple[str, ...]
    run_id: str
    plan_digest: str
    merge_schedule_digest: str
    group_id: str
    grant_identity: str
    checkpoint_identity: str
    chunks: tuple[DeletedChunkWorld, ...]
    free_before_bytes: int
    free_after_bytes: int
    freed_bytes: int
    expected_freed_bytes: int
    sources_absent: bool
    pid: int
    completed_at_utc: str
    deletion_identity: str

    def _identity_inputs(self) -> dict[str, object]:
        return {
            "event_kind": self.event_kind,
            "classifications": list(self.classifications),
            "run_id": self.run_id,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "group_id": self.group_id,
            "grant_identity": self.grant_identity,
            "checkpoint_identity": self.checkpoint_identity,
            "chunks": [dict(item.as_record()) for item in self.chunks],
            "free_before_bytes": self.free_before_bytes,
            "free_after_bytes": self.free_after_bytes,
            "freed_bytes": self.freed_bytes,
            "expected_freed_bytes": self.expected_freed_bytes,
            "sources_absent": self.sources_absent,
            "pid": self.pid,
            "completed_at_utc": self.completed_at_utc,
        }

    def as_record(self) -> Mapping[str, object]:
        """The exact persisted rendering."""
        record = self._identity_inputs()
        record["deletion_identity"] = self.deletion_identity
        return record

    def identity(self) -> str:
        """The identity the record implies -- over everything but the identity field."""
        return _record_identity(self._identity_inputs(), "deletion_identity")

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationGroupDeletion:
        """Rebuild a deletion record from its EXACT mapping and re-derive its identity.

        Raises:
            ChunkMultipassError: the shape, kind, labels, completion or identity refuses.
        """
        _exact_keys(record, _DELETION_KEYS, "calibration group deletion")
        chunks = record["chunks"]
        _require(
            isinstance(chunks, list) and bool(chunks),
            "a calibration group deletion's chunks must be a non-empty list",
        )
        deletion = cls(
            event_kind=str(record["event_kind"]),
            classifications=_stored_labels(record["classifications"], "classifications"),
            run_id=str(record["run_id"]),
            plan_digest=_hex64(record["plan_digest"], "plan_digest"),
            merge_schedule_digest=_hex64(record["merge_schedule_digest"], "merge_schedule_digest"),
            group_id=str(record["group_id"]),
            grant_identity=_hex64(record["grant_identity"], "grant_identity"),
            checkpoint_identity=_hex64(record["checkpoint_identity"], "checkpoint_identity"),
            chunks=tuple(
                DeletedChunkWorld.from_record(
                    cast("Mapping[str, object]", item) if isinstance(item, Mapping) else {}
                )
                for item in cast("list[object]", chunks)
            ),
            free_before_bytes=_stored_int(record["free_before_bytes"], "free_before_bytes"),
            free_after_bytes=_stored_int(record["free_after_bytes"], "free_after_bytes"),
            freed_bytes=_stored_int(record["freed_bytes"], "freed_bytes"),
            expected_freed_bytes=_stored_int(
                record["expected_freed_bytes"], "expected_freed_bytes"
            ),
            sources_absent=_stored_bool(record["sources_absent"], "sources_absent"),
            pid=_stored_int(record["pid"], "pid"),
            completed_at_utc=str(record["completed_at_utc"]),
            deletion_identity=str(record["deletion_identity"]),
        )
        _require(
            deletion.event_kind == CALIBRATION_GROUP_DELETION_EVENT_KIND
            and deletion.sources_absent,
            f"a calibration group deletion of kind {deletion.event_kind!r} that does not record "
            "every source absent is refused",
        )
        _require(
            deletion.identity() == deletion.deletion_identity,
            "a calibration group deletion's recorded identity does not describe its own "
            f"contents: recorded {deletion.deletion_identity!r}, recomputed "
            f"{deletion.identity()!r}",
        )
        return deletion


def read_calibration_group_deletion(path: Path) -> CalibrationGroupDeletion:
    """One group deletion record, read from its canonical bytes, or a refusal.

    Raises:
        ChunkMultipassError: the file is absent, a link, not canonical, or not an exact record.
    """
    decoded, payload = _decoded_canonical_object(path, "calibration group deletion")
    deletion = CalibrationGroupDeletion.from_record(decoded)
    _require(
        canonical_json_bytes(deletion.as_record()) == payload,
        f"deletion record {path.name!r} is not persisted as its canonical bytes; refused",
    )
    return deletion


def _validate_chunk_world_for_deletion(
    directory: Path, binding: CheckpointChunkBinding
) -> tuple[tuple[str, ...], bool]:
    """Hold one chunk world to its checkpoint binding BEFORE anything is deleted.

    Returns the entries still present and whether this is a resumption. The present set must be
    exactly the checkpoint's entry list, or -- after an interrupted exact deletion, which removes
    entries in sorted order -- exactly a trailing suffix of it; every present object is re-hashed
    against the manifest (the receipt against the bound receipt digest). Anything else refuses.
    """
    entries = binding.entries
    if not directory.exists() and not directory.is_symlink():
        return (), True
    _require(
        directory.is_dir() and not directory.is_symlink(),
        f"chunk world {binding.chunk_id!r} attempt {binding.attempt} is not a directory; refused",
    )
    try:
        present = tuple(_walk_files(directory))
    except ChunkTransferError as exc:
        message = f"chunk world {binding.chunk_id!r} cannot be walked for deletion: {exc}"
        raise ChunkMultipassError(message) from exc
    unexpected = sorted(set(present) - set(entries))
    _require(
        not unexpected,
        f"chunk world {binding.chunk_id!r} holds objects outside its checkpointed manifest: "
        f"{unexpected[:8]}; nothing is deleted and no recursive removal exists here",
    )
    already_gone = len(entries) - len(present)
    _require(
        present == entries[already_gone:],
        f"chunk world {binding.chunk_id!r} holds {list(present)[:8]} where an interrupted exact "
        f"deletion would have left {list(entries[already_gone:])[:8]}; a partial world that is "
        "not the remainder of an exact deletion is refused rather than finished",
    )
    recorded = {entry.relative_path: entry for entry in binding.manifest.entries}
    for relative in present:
        sha256, length = file_sha256(directory / relative)
        if relative == CHUNK_RECEIPT_FILENAME:
            _require(
                sha256 == binding.receipt_sha256,
                f"chunk world {binding.chunk_id!r} receipt digests to {sha256} where the "
                f"checkpoint bound {binding.receipt_sha256}; nothing is deleted",
            )
            continue
        entry = recorded[relative]
        _require(
            sha256 == entry.sha256 and length == entry.byte_length,
            f"chunk world {binding.chunk_id!r} object {relative!r} does not match the "
            "checkpointed manifest; a changed world is refused rather than deleted",
        )
    return present, already_gone > 0


def delete_calibration_group_chunk_worlds(
    grant: object,
    *,
    plan: CalibrationSubsetPlan,
    schedule: MergeSchedule,
    group_id: str,
    run_id: str,
    chunk_root: Path,
    retained_root: Path,
    intermediates_root: Path,
) -> CalibrationGroupDeletion:
    """Exact-delete one group's chunk worlds, grant FIRST, after the checkpoint -- §7.

    The explicit deletion grant is the first effective gate. Then, in order: the sealed plan and
    schedule; the group; the group's checkpoint (read, sealed, bound to this run, plan, schedule
    and group); no completed deletion yet; every retained witness durable -- re-read, held to its
    seal and to the checkpoint's binding; the intermediate durable -- terminal, verified, held to
    the checkpoint; then EVERY chunk world validated against its checkpointed manifest before the
    first deletion. Only then is free space measured and each attempt directory removed through
    the accepted exact-entry primitive -- never a tree removal, never an unlisted object -- and
    the completion record is written only after every source directory is absent.

    Raises:
        ChunkMultipassError: any refusal. Nothing is deleted on a refusal before the first
            deletion; a refusal after it leaves the exact remaining subset for a resumption under
            the same grant.
    """
    admitted = _require_calibration_deletion_grant(
        grant,
        run_id=run_id,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_id=group_id,
    )
    require_calibration_subset_plan(plan)
    require_sealed_schedule(schedule, plan)
    group = group_by_id(schedule, group_id)
    checkpoint = read_calibration_group_checkpoint(
        calibration_group_checkpoint_path(retained_root, group_id)
    )
    _require_checkpoint_binds_group(
        checkpoint, plan=plan, schedule=schedule, group=group, run_id=run_id
    )
    completion_path = calibration_group_deletion_path(retained_root, group_id)
    _require(
        not completion_path.exists() and not completion_path.is_symlink(),
        f"group {group_id!r} already records a completed deletion; refused",
    )
    witnesses: dict[str, CalibrationChunkWitness] = {}
    for binding in checkpoint.chunks:
        found = completed_calibration_chunk_witness(retained_root, binding.chunk_id)
        _require(
            found is not None,
            f"chunk {binding.chunk_id!r} carries no durable retained witness; nothing is deleted",
        )
        assert found is not None  # noqa: S101 - narrowed above
        witnesses[binding.chunk_id] = found[0]
    _require_checkpoint_binds_witnesses(checkpoint, witnesses)
    found_intermediate = completed_intermediate_receipt(intermediates_root, group_id)
    _require(
        found_intermediate is not None,
        f"group {group_id!r} carries no valid intermediate; nothing is deleted",
    )
    assert found_intermediate is not None  # noqa: S101 - narrowed above
    _require_checkpoint_binds_intermediate(checkpoint, found_intermediate[0], found_intermediate[1])
    # Every world validated BEFORE the first deletion.
    worlds: list[tuple[Path, CheckpointChunkBinding, tuple[str, ...], bool]] = []
    for binding in checkpoint.chunks:
        directory = chunk_root / binding.chunk_id / f"attempt-{binding.attempt:03d}"
        present, resumed = _validate_chunk_world_for_deletion(directory, binding)
        worlds.append((directory, binding, present, resumed))
    free_before = internal_free_bytes(chunk_root)
    expected_freed = 0
    deleted: list[DeletedChunkWorld] = []
    for directory, binding, present, resumed in worlds:
        expected_freed += sum((directory / relative).stat().st_size for relative in present)
        removed = 0
        if present:
            try:
                removed = _remove_exact_entries(directory, list(binding.entries))
            except ChunkTransferError as exc:
                message = f"the exact deletion of chunk world {binding.chunk_id!r} refused: {exc}"
                raise ChunkMultipassError(message) from exc
        _require(
            not directory.exists() and not directory.is_symlink(),
            f"chunk world {binding.chunk_id!r} still exists after its exact deletion",
        )
        deleted.append(
            DeletedChunkWorld(
                chunk_id=binding.chunk_id,
                attempt=binding.attempt,
                entries=binding.entries,
                entries_deleted=removed,
                resumed=resumed,
            )
        )
    free_after = internal_free_bytes(chunk_root)
    record = CalibrationGroupDeletion(
        event_kind=CALIBRATION_GROUP_DELETION_EVENT_KIND,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        run_id=run_id,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_id=group_id,
        grant_identity=admitted.identity(),
        checkpoint_identity=checkpoint.checkpoint_identity,
        chunks=tuple(deleted),
        free_before_bytes=free_before,
        free_after_bytes=free_after,
        freed_bytes=free_after - free_before,
        expected_freed_bytes=expected_freed,
        sources_absent=True,
        pid=os.getpid(),
        completed_at_utc=utc_now(),
        deletion_identity="",
    )
    sealed = replace(record, deletion_identity=record.identity())
    try:
        write_once_canonical_json(completion_path, dict(sealed.as_record()))
    except ChunkExecutionError as exc:
        message = f"the calibration group deletion record could not be written: {exc}"
        raise ChunkMultipassError(message) from exc
    return sealed


@dataclass(frozen=True, slots=True)
class CalibrationChunkExecution:
    """What the retention-aware lifecycle needs to run a calibration chunk child itself -- P8.

    Supplied by the caller when the orchestrator is to parse each group's chunks before merging
    that group (so no more than one group's bulky worlds need exist at once); absent, every chunk
    of the plan must already be terminal or already witnessed-and-deleted.
    """

    data_root: Path
    source_instance_id: str
    batch_size: int


# --------------------------------------------------------------------------- #
# Level 1 -- the calibration group merge, INSIDE its own process
# --------------------------------------------------------------------------- #
def merge_calibration_subset_group_body(  # noqa: PLR0915
    request: GroupMergeRequest, envelope: CalibrationChildEnvelope
) -> IntermediateReceipt:
    """Merge one level-1 group of a calibration-subset plan into one intermediate -- D151-C27R1.

    The calibration analogue of the accepted group body, gated by the pipe-delivered envelope
    instead of the production authority: the envelope for the group role is required FIRST; the
    code identity is measured; the attempt is create-once; the plan is read through the EXACT
    subset reader and the schedule re-derived from it; the envelope is held to the plan, group
    and ceiling; the temp binding is measured and held to the expected one; THIS group's inputs
    -- and only this group's, so no other group's bulky chunk world is required or opened
    (D151-C29R1 P2) -- are resolved through the accepted admission; the step is admitted; the
    child's own admission event is emitted; and only then does the attempt directory exist.
    The merge is the accepted primitive sequence, unchanged, and the receipt is the accepted
    intermediate receipt.
    """
    require_calibration_envelope(envelope, role=CALIBRATION_ROLE_GROUP)
    repository = _authenticate_running_repository(
        head=request.repository_head_sha, tree=request.repository_tree_sha, label=request.group_id
    )
    attempt_root = Path(request.attempt_directory)
    _require(
        not attempt_root.exists(),
        f"intermediate attempt directory {attempt_root.name!r} already exists; an attempt is "
        "create-once and a retry builds a new directory beside it",
    )
    plan, schedule = _read_calibration_plan_and_schedule(request.plan_path, request.schedule_path)
    require_chunkable_source(plan.source_id)
    group = group_by_id(schedule, request.group_id)
    require_envelope_binding(
        envelope, plan=plan, role=CALIBRATION_ROLE_GROUP, step_id=group.group_id
    )
    requirements = MultipassStorageRequirements.from_record(request.storage_requirements)
    binding = _require_expected_binding(
        _measured_calibration_binding(attempt_root),
        request.expected_sqlite_temp_binding,
        label=group.group_id,
    )
    operational_catalog = Path(request.operational_catalog)
    catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    started = utc_now()
    rss_before = process_peak_resident_bytes()
    # D151-C29R1 P2: this group's chunks, and only this group's, through the accepted admission.
    inputs = select_group_inputs(
        resolve_contiguous_chunk_inputs(
            plan,
            group.chunk_ids,
            internal_root=Path(request.internal_root),
            external_root=None if request.external_root is None else Path(request.external_root),
        ),
        group,
    )
    require_attachable(len(inputs))
    contract = inputs[0].receipt.execution_contract
    _require_seed_identity(
        label=group.group_id,
        repository=repository,
        recorded_head=inputs[0].receipt.repository_head_sha,
        recorded_tree=inputs[0].receipt.repository_tree_sha,
        contract=contract,
        catalog_sha256=catalog_sha256,
    )
    input_bytes = sum(item.receipt.manifest.total_bytes for item in inputs)
    admission = _admit_merge_step(
        step=group.group_id,
        level=MERGE_LEVEL_ONE,
        target=attempt_root,
        input_bytes=input_bytes,
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_one_peak_ratio,
        requirements=requirements,
    )
    _emit_calibration_admission_event(
        envelope=envelope,
        admission=admission,
        binding=binding,
        input_bytes=input_bytes,
        seed_catalog_bytes=catalog_bytes,
        charged_directory=attempt_root,
        attempt=request.attempt,
    )
    attempt_root.mkdir(mode=_DIRECTORY_MODE, parents=True)
    with WorkingCatalog(
        operational_catalog, attempt_root, cache_bytes=request.cache_bytes
    ) as world:
        connection = world.connection
        _require(
            world.identity.migration_head == contract.migration_head,
            f"the intermediate was seeded at migration head {world.identity.migration_head} "
            f"where every input executed at {contract.migration_head}",
        )
        world.ledger.begin_source(plan.source_instance_id, plan.source_id)
        aliases = _attach_all(connection, [item.catalog_path for item in inputs], "k")
        try:
            indexes = _deferrable_indexes(connection)
            for name, _sql in indexes:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            with transaction(connection):
                with write_containment(connection):
                    reduced = _reduced_parser_run(connection, aliases, contract=contract)
                    for table in _LOAD_ORDER:
                        if table == "census_accession_observations":
                            continue
                        if _MERGE_STRATEGY[table] == "keyed_first_last":
                            _keyed_first_last_load(connection, table, aliases)
                        else:
                            _sorted_bulk_load(connection, table, aliases)
                corrected, staged_rows = stage_first_witness_corrections(connection, aliases)
                with write_containment(connection):
                    _load_accession_observations(connection, aliases)
            for _name, sql in indexes:
                connection.execute(sql)
            counts = table_row_counts(connection)
        finally:
            _detach_all(connection, aliases)
    evidence = _merge_group_evidence(
        attempt_root=attempt_root, inputs=inputs, group=group, plan=plan
    )
    for item in inputs:
        verify_artifact_manifest(
            item.directory,
            item.receipt.manifest,
            exclude=(CHUNK_RECEIPT_FILENAME, "transfer_receipt.json"),
        )
    write_once_canonical_json(attempt_root / CHUNK_PLAN_FILENAME, dict(plan.as_record()))
    write_once_json(attempt_root / MERGE_SCHEDULE_FILENAME, dict(schedule.as_record()))
    manifest = build_artifact_manifest(attempt_root, exclude=(INTERMEDIATE_RECEIPT_FILENAME,))
    catalog_entry = next(
        entry for entry in manifest.entries if entry.relative_path == WORKING_CATALOG_FILENAME
    )
    receipt = IntermediateReceipt(
        contract=INTERMEDIATE_RECEIPT_CONTRACT,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        group_id=group.group_id,
        group_ordinal=group.ordinal,
        region=group.region,
        start=group.start,
        end=group.end,
        input_chunk_ids=tuple(item.chunk_id for item in inputs),
        input_receipt_sha256=tuple(
            file_sha256(item.directory / CHUNK_RECEIPT_FILENAME)[0] for item in inputs
        ),
        input_manifest_digests=tuple(item.receipt.manifest.digest for item in inputs),
        chunk_inputs=tuple(dict(item.as_record()) for item in inputs),
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        source_byte_length=plan.source_byte_length,
        member_order_digest=plan.member_order_digest,
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        execution_contract=contract,
        parser_run_id=reduced.parser_run_id,
        catalog_sha256=catalog_entry.sha256,
        table_row_counts=counts,
        members=evidence.members,
        records=evidence.records,
        omitted_field_observations=evidence.omitted,
        materialized_field_observations=evidence.materialized,
        member_manifest_digest=evidence.member_manifest_digest,
        witness_ledger_identity=evidence.witness_ledger_identity,
        compact_evidence_identity=evidence.compact_evidence_identity,
        first_witness_accessions_corrected=corrected,
        first_witness_rows_staged=staged_rows,
        evidence_members_corrected=evidence.evidence_members_corrected,
        evidence_delta=evidence.evidence_delta,
        storage_admission=dict(admission.as_record()),
        earliest_input_started_at_utc=min(item.receipt.started_at_utc for item in inputs),
        attempt=request.attempt,
        pid=os.getpid(),
        rss_peak_bytes=process_peak_resident_bytes() or rss_before,
        started_at_utc=started,
        completed_at_utc=utc_now(),
        manifest=manifest,
        status="complete",
    )
    # LAST. Nothing is written after this, and nothing that fails before it leaves one.
    write_once_json(attempt_root / INTERMEDIATE_RECEIPT_FILENAME, dict(receipt.as_record()))
    return receipt


# --------------------------------------------------------------------------- #
# Level 2 -- the calibration finalization, INSIDE its own process
# --------------------------------------------------------------------------- #
def finalize_calibration_subset_body(  # noqa: PLR0915
    request: FinalMergeRequest, envelope: CalibrationChildEnvelope
) -> CalibrationSubsetResult:
    """Build ONE calibration-only world from every intermediate, result LAST -- D151-C27R1 R6.

    The calibration analogue of the accepted finalization, gated by the envelope for the final
    role and charged at level two, with every canonical terminal deliberately absent: the merge
    is the accepted primitive sequence and the accepted D140-R12 gate is applied over the derived
    outcome, but no ``census_plan_sources.parser_state`` is written, the ledger is never marked
    parsed, no F0 phase checkpoint and no final world receipt exist. The world's parser state is
    measured after the merge and recorded in the result, which is written under the
    calibration-subset result contract and satisfies no complete-source reader.

    Retention-aware since D151-C29R1: the final consumes the five authenticated intermediates,
    one authenticated retained witness per planned chunk and every group checkpoint, and it
    resolves no chunk world -- the whole-F0 counters are derived over the witnesses' exact
    projections under the unchanged derivation, so a run whose chunk worlds were exact-deleted
    group by group reproduces the retain-everything result semantic for semantic.
    """
    require_calibration_envelope(envelope, role=CALIBRATION_ROLE_FINAL)
    repository = _authenticate_running_repository(
        head=request.repository_head_sha,
        tree=request.repository_tree_sha,
        label="calibration-final",
    )
    plan, schedule = _read_calibration_plan_and_schedule(request.plan_path, request.schedule_path)
    require_chunkable_source(plan.source_id)
    require_envelope_binding(
        envelope,
        plan=plan,
        role=CALIBRATION_ROLE_FINAL,
        step_id=_CALIBRATION_STEP_FINAL,
        run_id=request.run_id,
    )
    requirements = MultipassStorageRequirements.from_record(request.storage_requirements)
    world_directory = Path(request.world_directory)
    binding = _require_expected_binding(
        _measured_calibration_binding(world_directory),
        request.expected_sqlite_temp_binding,
        label="calibration-final",
    )
    operational_catalog = Path(request.operational_catalog)
    catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    # D151-C29R1 P5: no chunk world is resolved or opened. The plan's chunks are represented by
    # their retained witnesses, every group by its checkpoint, and each intermediate is bound to
    # its input chunk receipts THROUGH the witnesses and the checkpoints.
    retained_root = calibration_retained_root(Path(request.intermediates_root))
    witnesses = resolve_calibration_chunk_witnesses(
        plan, schedule, run_id=request.run_id, retained_root=retained_root
    )
    checkpoints = resolve_calibration_group_checkpoints(
        plan, schedule, run_id=request.run_id, retained_root=retained_root, witnesses=witnesses
    )
    intermediates = resolve_intermediate_inputs(
        plan, schedule, intermediates_root=Path(request.intermediates_root)
    )
    _require_witness_bound_intermediates(intermediates, witnesses, checkpoints)
    require_attachable(len(intermediates))
    contract = intermediates[0].receipt.execution_contract
    _require_seed_identity(
        label="calibration-final",
        repository=repository,
        recorded_head=intermediates[0].receipt.repository_head_sha,
        recorded_tree=intermediates[0].receipt.repository_tree_sha,
        contract=contract,
        catalog_sha256=catalog_sha256,
    )
    state = _accepted_plan_state(operational_catalog, plan)
    started_at_utc = min(item.receipt.earliest_input_started_at_utc for item in intermediates)
    _require(
        not world_directory.exists(),
        f"the calibration world {world_directory.name!r} already exists; a world is create-once "
        "and is never reused, resumed, repaired or overwritten",
    )
    input_bytes = sum(item.receipt.manifest.total_bytes for item in intermediates)
    admission = _admit_merge_step(
        step=_CALIBRATION_STEP_FINAL,
        level=MERGE_LEVEL_TWO,
        target=world_directory,
        input_bytes=input_bytes,
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_two_peak_ratio,
        requirements=requirements,
    )
    event = _emit_calibration_admission_event(
        envelope=envelope,
        admission=admission,
        binding=binding,
        input_bytes=input_bytes,
        seed_catalog_bytes=catalog_bytes,
        charged_directory=world_directory,
        attempt=None,
    )
    world_directory.mkdir(mode=_DIRECTORY_MODE, parents=True)
    with WorkingCatalog(
        operational_catalog, world_directory, cache_bytes=request.cache_bytes
    ) as world:
        connection = world.connection
        _require(
            world.identity.migration_head == contract.migration_head,
            f"the calibration world was seeded at migration head {world.identity.migration_head} "
            f"where every input executed at {contract.migration_head}",
        )
        world.ledger.begin_source(plan.source_instance_id, plan.source_id)
        aliases = _attach_all(connection, [item.catalog_path for item in intermediates], "k")
        try:
            indexes = _deferrable_indexes(connection)
            for name, _sql in indexes:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            with transaction(connection):
                with write_containment(connection):
                    reduced = _reduced_parser_run(connection, aliases, contract=contract)
                    for table in _LOAD_ORDER:
                        if table == "census_accession_observations":
                            continue
                        if _MERGE_STRATEGY[table] == "keyed_first_last":
                            _keyed_first_last_load(connection, table, aliases)
                        else:
                            _sorted_bulk_load(connection, table, aliases)
                    _apply_duplicate_identities(connection, reduced)
                _l2_corrected, _l2_staged = stage_first_witness_corrections(connection, aliases)
                with write_containment(connection):
                    _load_accession_observations(connection, aliases)
                    CensusCatalog._candidate_edges(  # noqa: SLF001 - the accepted derivation
                        connection, plan.source_observation_id, kind="company_name"
                    )
                    CensusCatalog._candidate_edges(  # noqa: SLF001
                        connection, plan.source_observation_id, kind="ticker"
                    )
                    CensusCatalog._mark_accession_conflicts(connection)  # noqa: SLF001
                    # Deliberately NO census_plan_sources.parser_state update: a calibration
                    # world is never marked as a parsed source (R6).
            for _name, sql in indexes:
                connection.execute(sql)
            counts = table_row_counts(connection)
        finally:
            _detach_all(connection, aliases)
        plan_counters = _plan_first_witness_counters(connection, witnesses)
        completeness, manifest_digest, totals, _level_two_evidence = _merge_sidecar(
            sidecar_path=world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME,
            inputs=cast("Sequence[ChunkInput]", intermediates),
            plan=plan,
            source_id=plan.source_id,
        )
        outcome = derived_f0_outcome(
            plan=plan,
            state=state,
            reduced=reduced,
            members=totals["members"],
            records=totals["records"],
            omitted=totals["omitted"],
            materialized=totals["materialized"],
            completeness_digest=completeness,
        )
        # D140-R12, by the accepted predicate, over the derived outcome. A blocking terminal
        # leaves a world with no result, exactly as the canonical path leaves one with no receipt.
        require_f0_success(outcome)
        state_row = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
            (plan.source_instance_id,),
        ).fetchone()
        world_parser_state = "" if state_row is None else str(state_row["parser_state"])
        # Deliberately NO mark_parsed, NO F0 phase checkpoint, NO final world receipt (R6).
    for item in intermediates:
        verify_artifact_manifest(
            item.directory, item.receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
        )
    manifest = build_artifact_manifest(
        world_directory, exclude=(CALIBRATION_SUBSET_RESULT_FILENAME,)
    )
    result = CalibrationSubsetResult(
        contract=CALIBRATION_SUBSET_RESULT_CONTRACT,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        run_id=request.run_id,
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        source_byte_length=plan.source_byte_length,
        member_order_digest=plan.member_order_digest,
        selected_member_order_digest=plan.selected_member_order_digest,
        shard_parent_binding_digest=plan.shard_parent_binding_digest,
        primary_prefix_members=plan.primary_prefix_members,
        selected_shard_members=plan.selected_shard_members,
        excluded_shard_members=plan.excluded_shard_members,
        selected_members=plan.selected_members,
        full_total_members=plan.full_total_members,
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        catalog_source_sha256=contract.catalog_source_sha256,
        execution_contract_identity=contract.contract_identity,
        chunk_count=plan.chunk_count,
        intermediate_count=len(intermediates),
        parser_run_id=reduced.parser_run_id,
        run_outcome=reduced.outcome,
        parser_state_after="chunk_local",
        world_parser_state=world_parser_state,
        members=totals["members"],
        records=totals["records"],
        parsed_records=reduced.parsed,
        quarantined_records=reduced.quarantined,
        omitted_field_observations=totals["omitted"],
        materialized_field_observations=totals["materialized"],
        completeness_digest=completeness,
        member_manifest_digest=manifest_digest,
        table_row_counts=counts,
        first_witness_accessions_corrected=plan_counters[0],
        first_witness_rows_staged=plan_counters[1],
        evidence_members_corrected=plan_counters[2],
        evidence_delta=plan_counters[3],
        storage_admission=dict(admission.as_record()),
        admission_event_identity=event.event_identity,
        envelope_sha256=envelope.sha256,
        pid=os.getpid(),
        rss_peak_bytes=process_peak_resident_bytes(),
        started_at_utc=started_at_utc,
        completed_at_utc=utc_now(),
        manifest=manifest,
        status="complete",
        result_identity="",
    )
    sealed = replace(result, result_identity=result.identity())
    # LAST. A finalization that stopped anywhere above leaves a world with no result.
    write_once_canonical_json(
        world_directory / CALIBRATION_SUBSET_RESULT_FILENAME, dict(sealed.as_record())
    )
    return sealed


# --------------------------------------------------------------------------- #
# The calibration process boundary -- runs in the PARENT; one launch, three roles
# --------------------------------------------------------------------------- #
def _calibration_child_main(request_path: str, envelope_fd: str) -> int:
    """The calibration child's entry point. Not a command; there is no surface that names it.

    FIRST the pipe-delivered envelope is received and validated -- contract, exact shape, role,
    parent pid -- then the request document is admitted only if its bytes are the ones the
    envelope binds, and only then is control handed to the body the envelope's role names, which
    re-validates the envelope against the plan, step and ceiling before creating anything.
    """
    envelope = receive_calibration_envelope(envelope_fd)
    record = require_envelope_request(envelope, Path(request_path))
    kind = str(record.get("kind", ""))
    if envelope.role == CALIBRATION_ROLE_CHUNK and "kind" not in record:
        execute_calibration_subset_chunk_body(ChunkRequest.from_record(record), envelope)
        return 0
    if envelope.role == CALIBRATION_ROLE_GROUP and kind == MULTIPASS_REQUEST_KIND_GROUP:
        merge_calibration_subset_group_body(GroupMergeRequest.from_record(record), envelope)
        return 0
    if envelope.role == CALIBRATION_ROLE_FINAL and kind == MULTIPASS_REQUEST_KIND_FINAL:
        finalize_calibration_subset_body(FinalMergeRequest.from_record(record), envelope)
        return 0
    if envelope.role == CALIBRATION_ROLE_FINAL and kind == SUCCESSOR_REQUEST_KIND_FINAL:
        # D151-C31R2-R19A-C2: the successor calibration final, under the SAME received envelope
        # and the same final role; its body requires that role FIRST and re-seals the plan.
        _successor_calibration_final_body(SuccessorFinalRequest.from_record(record), envelope)
        return 0
    message = (
        f"a calibration envelope for role {envelope.role!r} was handed a request of kind "
        f"{kind or 'chunk'!r}; the two must agree and the child refuses"
    )
    raise ChunkMultipassError(message)


def _spawn_calibration_child(
    request_path: Path,
    envelope: CalibrationChildEnvelope,
    *,
    timeout_seconds: float | None,
    observe: Callable[[str], None] | None,
) -> None:
    """Start ONE calibration child with its envelope on an inherited pipe, and prove it ended.

    The envelope's canonical bytes are written into the pipe and the write end closed before
    the interpreter starts; the child inherits only the read end, whose number -- not its
    contents -- is the second argument. Nothing about the envelope enters argv, the
    environment, disk or this process's logs.
    """
    if observe is not None:
        observe("CALIBRATION_PROCESS_START")
    with delivered_calibration_envelope(envelope) as envelope_fd:
        completed = subprocess.run(  # noqa: S603 - fixed interpreter, fixed bootstrap, no shell
            [
                sys.executable,
                "-c",
                _CALIBRATION_CHILD_BOOTSTRAP,
                str(request_path),
                str(envelope_fd),
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            pass_fds=(envelope_fd,),
        )
    if observe is not None:
        observe("CALIBRATION_PROCESS_EXIT")
    if completed.returncode != 0:
        message = (
            f"calibration child {request_path.name!r} ended with exit status "
            f"{completed.returncode} and is NOT complete. Nothing was cleaned, deleted or retried "
            f"in place, and no terminal exists for it. stderr tail: "
            f"{completed.stderr.strip()[-800:]!r}"
        )
        raise ChunkMultipassError(message)


def run_calibration_subset_chunk(
    request: ChunkRequest,
    *,
    plan: CalibrationSubsetPlan,
    run_id: str,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> ChunkReceipt:
    """Run one calibration-subset chunk in a FRESH child process under a fresh envelope.

    The sealed subset plan is required FIRST; the predecessor is dead; the request is written
    create-once; the envelope is issued over exactly those bytes; the child runs the calibration
    chunk body; the receipt exists, verifies, describes this chunk and attempt, binds this plan,
    names a process that is not this one, and that process is gone.

    Raises:
        ChunkPlanError: the plan is not a sealed subset plan.
        ChunkMultipassError, ChunkExecutionError, ChunkEvidenceError: any proof fails.
    """
    require_calibration_subset_plan(plan)
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    attempt_root = Path(request.attempt_directory)
    attempt_root.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = attempt_root.parent / f"{request.chunk_id}-{request.attempt:03d}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = issue_calibration_envelope(
        run_id=run_id,
        plan=plan,
        role=CALIBRATION_ROLE_CHUNK,
        step_id=request.chunk_id,
        request_path=request_path,
        instrumentation_ledger=None,
    )
    _spawn_calibration_child(
        request_path, envelope, timeout_seconds=timeout_seconds, observe=observe
    )
    receipt = ChunkReceipt.from_record(
        read_receipt_document(
            attempt_root / CHUNK_RECEIPT_FILENAME, contract=CHUNK_RECEIPT_CONTRACT
        )
    )
    verify_artifact_manifest(attempt_root, receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,))
    _require(
        receipt.chunk_id == request.chunk_id and receipt.attempt == request.attempt,
        f"the receipt in {attempt_root.name!r} describes chunk {receipt.chunk_id!r} attempt "
        f"{receipt.attempt}, not {request.chunk_id!r} attempt {request.attempt}",
    )
    _require(
        receipt.plan_digest == plan.plan_digest,
        f"the receipt binds plan {receipt.plan_digest[:16]}..., not the calibration-subset plan "
        f"{plan.plan_digest[:16]}... this launch ran under",
    )
    _require(
        receipt.pid != os.getpid(),
        "the chunk receipt records THIS process's pid, so the chunk did not run in a separate "
        "operating-system process",
    )
    _require_process_dead(receipt.pid)
    return receipt


def run_calibration_subset_chunks(
    plan: CalibrationSubsetPlan,
    *,
    plan_path: Path,
    chunk_root: Path,
    operational_catalog: Path,
    data_root: Path,
    source_instance_id: str,
    run_id: str,
    batch_size: int,
    cache_bytes: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> tuple[ChunkReceipt, ...]:
    """Every chunk of a calibration-subset plan, each in its own process, with the region barrier.

    Restart-safe: a chunk that already carries a valid receipt under this plan is reused, never
    re-executed; the merged parent map is written once when the shard chunk is reached -- after
    every primary chunk has a terminal -- and required identical on a restart. The measured
    repository identity of this process is what every request names.
    """
    require_calibration_subset_plan(plan)
    repository = require_clean_running_repository()
    plan_path.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    _write_canonical_or_require_same(plan_path, plan.as_record(), "calibration-subset plan")
    chunk_root.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    receipts: list[ChunkReceipt] = []
    contributions: list[Mapping[str, set[str]]] = []
    parent_map_path: Path | None = None
    previous: int | None = None
    for bounds in plan.chunks:
        if bounds.region == REGION_SHARD and parent_map_path is None:
            merged = merge_parent_map(contributions)
            parent_map_path = chunk_root / PARENT_MAP_FILENAME
            _write_or_require_same(
                parent_map_path,
                {name: sorted(parents) for name, parents in sorted(merged.items())},
                "merged parent map",
            )
        existing = completed_chunk_receipt(chunk_root, bounds.chunk_id)
        if existing is not None:
            receipt, directory = existing
            _require(
                receipt.plan_digest == plan.plan_digest,
                f"chunk {bounds.chunk_id!r} already carries a receipt under plan "
                f"{receipt.plan_digest[:16]}..., not this calibration-subset plan; refused",
            )
        else:
            directory, attempt = next_attempt_directory(chunk_root, bounds.chunk_id)
            receipt = run_calibration_subset_chunk(
                ChunkRequest(
                    plan_path=str(plan_path),
                    chunk_id=bounds.chunk_id,
                    attempt=attempt,
                    attempt_directory=str(directory),
                    operational_catalog=str(operational_catalog),
                    data_root=str(data_root),
                    source_instance_id=source_instance_id,
                    batch_size=batch_size,
                    cache_bytes=cache_bytes,
                    repository_head_sha=repository.head_sha,
                    repository_tree_sha=repository.tree_sha,
                    parent_map_path=None if parent_map_path is None else str(parent_map_path),
                ),
                plan=plan,
                run_id=run_id,
                predecessor_pid=previous,
                timeout_seconds=timeout_seconds,
                observe=observe,
            )
            previous = receipt.pid
        receipts.append(receipt)
        if bounds.region == REGION_PRIMARY:
            contributions.append(read_declarations(directory / CHUNK_DECLARATIONS_FILENAME))
    return tuple(receipts)


def run_calibration_subset_group_merge(
    request: GroupMergeRequest,
    *,
    plan: CalibrationSubsetPlan,
    run_id: str,
    instrumentation_ledger: Path,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> IntermediateReceipt:
    """Run one calibration level-1 group merge in a FRESH child process under a fresh envelope.

    Raises:
        ChunkPlanError: the plan is not a sealed subset plan.
        ChunkMultipassError, ChunkExecutionError, ChunkEvidenceError: any proof fails.
    """
    require_calibration_subset_plan(plan)
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    attempt_root = Path(request.attempt_directory)
    attempt_root.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = attempt_root.parent / f"{request.group_id}-{request.attempt:03d}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = issue_calibration_envelope(
        run_id=run_id,
        plan=plan,
        role=CALIBRATION_ROLE_GROUP,
        step_id=request.group_id,
        request_path=request_path,
        instrumentation_ledger=instrumentation_ledger,
    )
    _spawn_calibration_child(
        request_path, envelope, timeout_seconds=timeout_seconds, observe=observe
    )
    receipt = IntermediateReceipt.from_record(
        read_receipt_document(
            attempt_root / INTERMEDIATE_RECEIPT_FILENAME, contract=INTERMEDIATE_RECEIPT_CONTRACT
        )
    )
    verify_artifact_manifest(
        attempt_root, receipt.manifest, exclude=(INTERMEDIATE_RECEIPT_FILENAME,)
    )
    _require(
        receipt.group_id == request.group_id
        and receipt.attempt == request.attempt
        and receipt.plan_digest == plan.plan_digest,
        f"the receipt in {attempt_root.name!r} describes group {receipt.group_id!r} attempt "
        f"{receipt.attempt} under plan {receipt.plan_digest[:16]}..., not {request.group_id!r} "
        f"attempt {request.attempt} under {plan.plan_digest[:16]}...",
    )
    _require(
        receipt.pid != os.getpid(),
        "the intermediate receipt records THIS process's pid, so the merge did not run in a "
        "separate operating-system process",
    )
    _require_process_dead(receipt.pid)
    return receipt


def run_calibration_subset_final_merge(
    request: FinalMergeRequest,
    *,
    plan: CalibrationSubsetPlan,
    instrumentation_ledger: Path,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> CalibrationSubsetResult:
    """Run the calibration finalization in a FRESH child process under a fresh envelope.

    Returns the calibration-subset result read back through its exact reader and verified
    against the world's own artifacts.

    Raises:
        ChunkPlanError: the plan is not a sealed subset plan.
        ChunkMultipassError, ChunkExecutionError, ChunkEvidenceError: any proof fails.
    """
    require_calibration_subset_plan(plan)
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    world_directory = Path(request.world_directory)
    world_directory.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    request_path = world_directory.parent / f"{world_directory.name}-request.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = issue_calibration_envelope(
        run_id=request.run_id,
        plan=plan,
        role=CALIBRATION_ROLE_FINAL,
        step_id=_CALIBRATION_STEP_FINAL,
        request_path=request_path,
        instrumentation_ledger=instrumentation_ledger,
    )
    _spawn_calibration_child(
        request_path, envelope, timeout_seconds=timeout_seconds, observe=observe
    )
    result = read_calibration_subset_result(world_directory / CALIBRATION_SUBSET_RESULT_FILENAME)
    verify_artifact_manifest(
        world_directory, result.manifest, exclude=(CALIBRATION_SUBSET_RESULT_FILENAME,)
    )
    _require(
        result.plan_digest == plan.plan_digest
        and result.run_id == request.run_id
        and result.envelope_sha256 == envelope.sha256,
        "the calibration-subset result does not describe this plan, run and envelope; refused",
    )
    _require(
        result.pid != os.getpid(),
        "the calibration-subset result records THIS process's pid, so the finalization did not "
        "run in a separate operating-system process",
    )
    _require_process_dead(result.pid)
    return result


@dataclass(frozen=True, slots=True)
class CalibrationSubsetMultipassResult:
    """What one calibration-subset consolidation established, and where it put it."""

    world_directory: Path
    result: CalibrationSubsetResult
    schedule: MergeSchedule
    storage_plan: MultipassStoragePlan
    intermediates: tuple[IntermediateReceipt, ...]
    merge_pids: tuple[int, ...]
    witnesses: tuple[CalibrationChunkWitness, ...] = ()
    checkpoints: tuple[CalibrationGroupCheckpoint, ...] = ()
    deletions: tuple[CalibrationGroupDeletion | None, ...] = ()


@dataclass(frozen=True, slots=True)
class _GroupOutcome:
    receipt: IntermediateReceipt
    witnesses: tuple[CalibrationChunkWitness, ...]
    checkpoint: CalibrationGroupCheckpoint
    deletion: CalibrationGroupDeletion | None
    pids: tuple[int, ...]
    previous: int | None


@dataclass(frozen=True, slots=True)
class _CalibrationLifecycle:
    """The retention-aware lifecycle of one calibration multipass, group by group -- P8.

    For each level-1 group in schedule order: every chunk of the group is terminal (reused,
    or parsed now in a fresh child when a :class:`CalibrationChunkExecution` was supplied);
    every chunk carries a retained witness (written now, after the terminal authenticated, or
    re-read and held to the chunk beside it); the group's intermediate is terminal (reused, or
    merged now in a fresh child over exactly this group's chunks); the group's checkpoint binds
    chunk receipt, witness and intermediate (written now, or re-read and held to all three); and
    only then, only under an explicit grant naming the group, are the group's chunk worlds
    exact-deleted. A group that already records a completed deletion is never re-parsed: its
    witnesses stand in for its worlds, and nothing here opens a world that is gone.
    """

    plan: CalibrationSubsetPlan
    schedule: MergeSchedule
    run_id: str
    chunk_root: Path
    retained_root: Path
    intermediates_root: Path
    plan_path: Path
    schedule_path: Path
    operational_catalog: Path
    catalog_bytes: int
    storage_requirements: MultipassStorageRequirements
    binding: SqliteTempBinding
    repository: RepositoryIdentity
    instrumentation_ledger: Path
    chunk_execution: CalibrationChunkExecution | None
    deletion_grant: CalibrationDeletionGrant | None
    external_root: Path | None
    cache_bytes: int | None
    timeout_seconds: float | None
    observe: Callable[[str], None] | None

    def _grant_covers(self, group: MergeGroup) -> bool:
        return self.deletion_grant is not None and group.group_id in self.deletion_grant.group_ids

    def _existing_deletion(self, group: MergeGroup) -> CalibrationGroupDeletion | None:
        path = calibration_group_deletion_path(self.retained_root, group.group_id)
        if not path.exists() and not path.is_symlink():
            return None
        deletion = read_calibration_group_deletion(path)
        _require(
            deletion.run_id == self.run_id
            and deletion.plan_digest == self.plan.plan_digest
            and deletion.merge_schedule_digest == self.schedule.schedule_digest
            and deletion.group_id == group.group_id
            and tuple(item.chunk_id for item in deletion.chunks) == group.chunk_ids,
            f"group {group.group_id!r} records a deletion of another run, plan, schedule or "
            "group; refused",
        )
        return deletion

    def _existing_checkpoint(self, group: MergeGroup) -> CalibrationGroupCheckpoint | None:
        path = calibration_group_checkpoint_path(self.retained_root, group.group_id)
        if not path.exists() and not path.is_symlink():
            return None
        checkpoint = read_calibration_group_checkpoint(path)
        _require_checkpoint_binds_group(
            checkpoint, plan=self.plan, schedule=self.schedule, group=group, run_id=self.run_id
        )
        return checkpoint

    def _ensure_parent_map(self) -> Path:
        """The merged parent map the shard chunk consumes, from every primary chunk's RETAINED
        declarations copy -- a deleted primary world contributes through its witness."""
        contributions: list[Mapping[str, set[str]]] = []
        for bounds in self.plan.chunks:
            if bounds.region != REGION_PRIMARY:
                continue
            found = completed_calibration_chunk_witness(self.retained_root, bounds.chunk_id)
            _require(
                found is not None,
                f"the shard chunk needs every primary chunk's retained declarations and chunk "
                f"{bounds.chunk_id!r} carries no witness; refused",
            )
            assert found is not None  # noqa: S101 - narrowed above
            contributions.append(read_declarations(found[1] / CHUNK_DECLARATIONS_FILENAME))
        merged = merge_parent_map(contributions)
        path = self.chunk_root / PARENT_MAP_FILENAME
        _write_or_require_same(
            path,
            {name: sorted(parents) for name, parents in sorted(merged.items())},
            "merged parent map",
        )
        return path

    def _run_chunk(self, bounds: ChunkBounds, previous: int | None) -> ChunkReceipt:
        execution = self.chunk_execution
        _require(
            execution is not None,
            f"chunk {bounds.chunk_id!r} has no terminal receipt and no retained witness, and no "
            "chunk execution was supplied; nothing here parses a chunk on its own",
        )
        assert execution is not None  # noqa: S101 - narrowed above
        parent_map_path = self._ensure_parent_map() if bounds.region == REGION_SHARD else None
        directory, attempt = next_attempt_directory(self.chunk_root, bounds.chunk_id)
        return run_calibration_subset_chunk(
            ChunkRequest(
                plan_path=str(self.plan_path),
                chunk_id=bounds.chunk_id,
                attempt=attempt,
                attempt_directory=str(directory),
                operational_catalog=str(self.operational_catalog),
                data_root=str(execution.data_root),
                source_instance_id=execution.source_instance_id,
                batch_size=execution.batch_size,
                cache_bytes=self.cache_bytes,
                repository_head_sha=self.repository.head_sha,
                repository_tree_sha=self.repository.tree_sha,
                parent_map_path=None if parent_map_path is None else str(parent_map_path),
            ),
            plan=self.plan,
            run_id=self.run_id,
            predecessor_pid=previous,
            timeout_seconds=self.timeout_seconds,
            observe=self.observe,
        )

    def _ensure_chunk(
        self,
        bounds: ChunkBounds,
        *,
        deletion: CalibrationGroupDeletion | None,
        checkpoint: CalibrationGroupCheckpoint | None,
        group: MergeGroup,
        previous: int | None,
    ) -> tuple[CalibrationChunkWitness, int | None]:
        found = completed_calibration_chunk_witness(self.retained_root, bounds.chunk_id)
        if deletion is not None:
            _require(
                found is not None,
                f"group {group.group_id!r} records a completed deletion and chunk "
                f"{bounds.chunk_id!r} carries no retained witness; refused",
            )
            assert found is not None  # noqa: S101 - narrowed above
            return found[0], previous
        existing = completed_chunk_receipt(self.chunk_root, bounds.chunk_id)
        if existing is None and found is not None:
            _require(
                checkpoint is not None and self._grant_covers(group),
                f"chunk {bounds.chunk_id!r} carries a retained witness but no chunk world, and "
                "its group carries no checkpoint or no deletion grant names it; an interrupted "
                "deletion is resumed only under the grant that admitted it, and nothing here "
                "re-parses a chunk beside its witness",
            )
            return found[0], previous
        if existing is None:
            receipt = self._run_chunk(bounds, previous)
            previous = receipt.pid
            directory = self.chunk_root / bounds.chunk_id / f"attempt-{receipt.attempt:03d}"
        else:
            receipt, directory = existing
            _require(
                receipt.plan_digest == self.plan.plan_digest,
                f"chunk {bounds.chunk_id!r} already carries a receipt under plan "
                f"{receipt.plan_digest[:16]}..., not this calibration-subset plan; refused",
            )
        if found is None:
            witness, _witness_directory = write_calibration_chunk_witness(
                self.plan,
                self.schedule,
                chunk_id=bounds.chunk_id,
                run_id=self.run_id,
                chunk_root=self.chunk_root,
                retained_root=self.retained_root,
                external_root=self.external_root,
            )
            return witness, previous
        witness = found[0]
        _require_witness_binds_plan(
            witness,
            plan=self.plan,
            schedule=self.schedule,
            run_id=self.run_id,
            ordinal=self.plan.chunks.index(bounds),
            bounds=bounds,
        )
        _require_witness_matches_chunk(witness, receipt, directory)
        return witness, previous

    def _merge_group(
        self, group: MergeGroup, witnesses: Sequence[CalibrationChunkWitness], previous: int | None
    ) -> IntermediateReceipt:
        _admit_merge_step(
            step=group.group_id,
            level=MERGE_LEVEL_ONE,
            target=intermediate_attempt_directory(self.intermediates_root, group.group_id, 0),
            input_bytes=sum(item.chunk_manifest_total_bytes for item in witnesses),
            seed_catalog_bytes=self.catalog_bytes,
            peak_ratio=self.storage_requirements.level_one_peak_ratio,
            requirements=self.storage_requirements,
        )
        attempt_directory, attempt = next_intermediate_attempt_directory(
            self.intermediates_root, group.group_id
        )
        return run_calibration_subset_group_merge(
            GroupMergeRequest(
                plan_path=str(self.plan_path),
                schedule_path=str(self.schedule_path),
                group_id=group.group_id,
                attempt=attempt,
                attempt_directory=str(attempt_directory),
                internal_root=str(self.chunk_root),
                external_root=None if self.external_root is None else str(self.external_root),
                operational_catalog=str(self.operational_catalog),
                cache_bytes=self.cache_bytes,
                repository_head_sha=self.repository.head_sha,
                repository_tree_sha=self.repository.tree_sha,
                storage_requirements=dict(self.storage_requirements.as_record()),
                expected_sqlite_temp_binding=dict(self.binding.as_record()),
            ),
            plan=self.plan,
            run_id=self.run_id,
            instrumentation_ledger=self.instrumentation_ledger,
            predecessor_pid=previous,
            timeout_seconds=self.timeout_seconds,
            observe=self.observe,
        )

    def ensure_group(self, group: MergeGroup, previous: int | None) -> _GroupOutcome:
        """Bring one group to its checkpointed -- and, under a grant, deleted -- state."""
        deletion = self._existing_deletion(group)
        checkpoint = self._existing_checkpoint(group)
        _require(
            deletion is None or checkpoint is not None,
            f"group {group.group_id!r} records a completed deletion without a checkpoint; refused",
        )
        pids: list[int] = []
        witnesses: list[CalibrationChunkWitness] = []
        for chunk_id in group.chunk_ids:
            before = previous
            witness, previous = self._ensure_chunk(
                chunk_by_id(self.plan, chunk_id),
                deletion=deletion,
                checkpoint=checkpoint,
                group=group,
                previous=previous,
            )
            if previous is not None and previous != before:
                pids.append(previous)
            witnesses.append(witness)
        existing = completed_intermediate_receipt(self.intermediates_root, group.group_id)
        if existing is not None:
            receipt = existing[0]
            _require(
                receipt.plan_digest == self.plan.plan_digest,
                f"intermediate {group.group_id!r} already carries a receipt under plan "
                f"{receipt.plan_digest[:16]}..., not this calibration-subset plan; refused",
            )
        else:
            _require(
                deletion is None and checkpoint is None,
                f"group {group.group_id!r} carries a checkpoint or deletion record but no "
                "intermediate; refused",
            )
            receipt = self._merge_group(group, witnesses, previous)
            previous = receipt.pid
            pids.append(receipt.pid)
        if checkpoint is None:
            checkpoint = write_calibration_group_checkpoint(
                self.plan,
                self.schedule,
                group_id=group.group_id,
                run_id=self.run_id,
                chunk_root=self.chunk_root,
                retained_root=self.retained_root,
                intermediates_root=self.intermediates_root,
                external_root=self.external_root,
            )
        else:
            _require_checkpoint_binds_witnesses(
                checkpoint, {item.chunk_id: item for item in witnesses}
            )
            found = completed_intermediate_receipt(self.intermediates_root, group.group_id)
            assert found is not None  # noqa: S101 - established above
            _require_checkpoint_binds_intermediate(checkpoint, found[0], found[1])
        if deletion is None and self._grant_covers(group):
            deletion = delete_calibration_group_chunk_worlds(
                self.deletion_grant,
                plan=self.plan,
                schedule=self.schedule,
                group_id=group.group_id,
                run_id=self.run_id,
                chunk_root=self.chunk_root,
                retained_root=self.retained_root,
                intermediates_root=self.intermediates_root,
            )
        return _GroupOutcome(
            receipt=receipt,
            witnesses=tuple(witnesses),
            checkpoint=checkpoint,
            deletion=deletion,
            pids=tuple(pids),
            previous=previous,
        )


def run_calibration_subset_multipass(  # noqa: PLR0915
    *,
    plan: CalibrationSubsetPlan,
    internal_root: Path,
    operational_catalog: Path,
    multipass_root: Path,
    run_id: str,
    storage_requirements: MultipassStorageRequirements,
    instrumentation_ledger: Path,
    external_root: Path | None = None,
    cache_bytes: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
    chunk_execution: CalibrationChunkExecution | None = None,
    deletion_grant: CalibrationDeletionGrant | None = None,
) -> CalibrationSubsetMultipassResult:
    """Consolidate a calibration-subset plan, retention-aware: group by group, each level-1
    group parsed (when asked), witnessed, merged, checkpointed and -- under an explicit grant --
    exact-deleted before the next group's bulky worlds need exist; then level 2 over the five
    intermediates and every retained witness -- D151-C27R1, made retention-aware by D151-C29R1.

    The sealed subset plan is required FIRST. The storage terms are the caller's explicit,
    typed calibration terms -- never the owner-frozen production terms, which stay ``None`` and
    are never consulted here. Then, in the accepted order: the SQLite temp binding is measured;
    the executing repository is measured; the calibration schedule is derived and recorded
    create-once beside the canonical plan copy; each group is brought to its checkpointed state
    (:class:`_CalibrationLifecycle`) in a chain of fresh children under fresh envelopes; the
    deterministic storage plan is computed from the witnesses' authenticated chunk byte lengths
    and recorded, or held compatible on a restart; and the finalization runs in one more fresh
    child over the intermediates and the witnesses alone. Nothing is deleted without a grant, and
    nothing a grant admits is deleted before its checkpoint exists.
    """
    require_calibration_subset_plan(plan)
    binding = _measured_calibration_binding(multipass_root)
    repository = require_clean_running_repository()
    schedule = derive_calibration_subset_schedule(plan)
    intermediates_root = multipass_root / _INTERMEDIATES_DIRECTORY
    world_directory = multipass_root / _FINAL_DIRECTORY
    retained_root = calibration_retained_root(intermediates_root)
    _require(
        not _within(intermediates_root, instrumentation_ledger)
        and not _within(world_directory, instrumentation_ledger)
        and not _within(retained_root, instrumentation_ledger),
        "the calibration instrumentation ledger must lie outside the intermediates root, the "
        "retained root and the final world",
    )
    multipass_root.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    instrumentation_ledger.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    retained_root.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    plan_path = multipass_root / CHUNK_PLAN_FILENAME
    schedule_path = multipass_root / MERGE_SCHEDULE_FILENAME
    _write_canonical_or_require_same(plan_path, plan.as_record(), "calibration-subset plan")
    _write_or_require_same(schedule_path, dict(schedule.as_record()), "calibration merge schedule")
    _refuse_foreign_retained_entries(plan, schedule, retained_root)
    _catalog_sha256, catalog_bytes = file_digest(operational_catalog)
    lifecycle = _CalibrationLifecycle(
        plan=plan,
        schedule=schedule,
        run_id=run_id,
        chunk_root=internal_root,
        retained_root=retained_root,
        intermediates_root=intermediates_root,
        plan_path=plan_path,
        schedule_path=schedule_path,
        operational_catalog=operational_catalog,
        catalog_bytes=catalog_bytes,
        storage_requirements=storage_requirements,
        binding=binding,
        repository=repository,
        instrumentation_ledger=instrumentation_ledger,
        chunk_execution=chunk_execution,
        deletion_grant=deletion_grant,
        external_root=external_root,
        cache_bytes=cache_bytes,
        timeout_seconds=timeout_seconds,
        observe=observe,
    )
    receipts: list[IntermediateReceipt] = []
    witnesses: list[CalibrationChunkWitness] = []
    checkpoints: list[CalibrationGroupCheckpoint] = []
    deletions: list[CalibrationGroupDeletion | None] = []
    pids: list[int] = []
    previous: int | None = None
    for group in schedule.groups:
        outcome = lifecycle.ensure_group(group, previous)
        previous = outcome.previous
        pids.extend(outcome.pids)
        receipts.append(outcome.receipt)
        witnesses.extend(outcome.witnesses)
        checkpoints.append(outcome.checkpoint)
        deletions.append(outcome.deletion)
    storage_plan = plan_multipass_storage(
        plan_digest=plan.plan_digest,
        merge_schedule_digest=schedule.schedule_digest,
        groups=[(group.group_id, group.chunk_ids) for group in schedule.groups],
        chunk_bytes_by_id={item.chunk_id: item.chunk_manifest_total_bytes for item in witnesses},
        seed_catalog_bytes=catalog_bytes,
        requirements=storage_requirements,
        sqlite_temp_binding=binding,
    )
    _record_storage_plan(multipass_root / STORAGE_PLAN_FILENAME, storage_plan)
    _admit_merge_step(
        step=_CALIBRATION_STEP_FINAL,
        level=MERGE_LEVEL_TWO,
        target=world_directory,
        input_bytes=sum(receipt.manifest.total_bytes for receipt in receipts),
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=storage_requirements.level_two_peak_ratio,
        requirements=storage_requirements,
    )
    result = run_calibration_subset_final_merge(
        FinalMergeRequest(
            plan_path=str(plan_path),
            schedule_path=str(schedule_path),
            intermediates_root=str(intermediates_root),
            internal_root=str(internal_root),
            external_root=None if external_root is None else str(external_root),
            operational_catalog=str(operational_catalog),
            world_directory=str(world_directory),
            run_id=run_id,
            cache_bytes=cache_bytes,
            repository_head_sha=repository.head_sha,
            repository_tree_sha=repository.tree_sha,
            storage_requirements=dict(storage_requirements.as_record()),
            expected_sqlite_temp_binding=dict(binding.as_record()),
        ),
        plan=plan,
        instrumentation_ledger=instrumentation_ledger,
        predecessor_pid=previous,
        timeout_seconds=timeout_seconds,
        observe=observe,
    )
    return CalibrationSubsetMultipassResult(
        world_directory=world_directory,
        result=result,
        schedule=schedule,
        storage_plan=storage_plan,
        intermediates=tuple(receipts),
        merge_pids=tuple(pids),
        witnesses=tuple(witnesses),
        checkpoints=tuple(checkpoints),
        deletions=tuple(deletions),
    )


# --------------------------------------------------------------------------- #
# The durable Level-Two stage / restart spine -- D151-C31R2-R19A-C2
# --------------------------------------------------------------------------- #
# Everything below this line is the successor-only spine accepted R18 designed and the R19A-C2
# packet family authorized. It changes no legacy body above: the accepted finalizers keep their
# one-transaction shape, their TEMP relations and their gates byte for byte, and the successor
# reaches the accepted merge primitives by call. What is new is durability: every stage is one
# transaction on the world catalog that commits its semantic writes and its applied-unit row
# together, followed by an exact ``PRAGMA main.wal_checkpoint(TRUNCATE)`` and an immutable
# external receipt, so a restart classifies committed evidence rather than guessing from a
# directory listing, a WAL length or an exit status.

#: The successor StagePlan's contract.
L2_STAGE_PLAN_CONTRACT: Final = "m3.3-chunked-f0-l2-stage-plan/1"

#: One applied unit -- the row that commits with the semantic writes it describes.
L2_APPLIED_UNIT_CONTRACT: Final = "m3.3-chunked-f0-l2-applied-unit/1"

#: One stage's immutable external receipt, published after COMMIT and checkpoint.
L2_STAGE_RECEIPT_CONTRACT: Final = "m3.3-chunked-f0-l2-stage-receipt/1"

#: One binding of a second store (sidecar, run progress, checkpoint, result) into the catalog.
L2_CROSS_STORE_BINDING_CONTRACT: Final = "m3.3-chunked-f0-l2-cross-store-binding/1"

#: The persisted deferred-index set: exact DDL captured in the same transaction as the DROP.
L2_DEFERRED_INDEX_SET_CONTRACT: Final = "m3.3-chunked-f0-l2-deferred-index-set/1"

#: The pre-world storage admission record, create-once and consumed immediately.
L2_STAGE_ADMISSION_CONTRACT: Final = "m3.3-chunked-f0-l2-stage-admission/1"

#: The reconstructed connection state every successor connection is held to.
L2_CONNECTION_STATE_CONTRACT: Final = "m3.3-chunked-f0-l2-connection-state/1"

# --------------------------------------------------------------------------- #
# D151-C31R2-R19B-C2 -- statement observability, the WAL watchdog and the /2 contracts
# --------------------------------------------------------------------------- #
#: The executable successor StagePlan. ``/1`` above stays for read-only historical parsing and
#: is never executed after R19B; every writer emits ``/2`` and every executing reader requires
#: it. There is no automatic conversion in either direction.
L2_STAGE_PLAN_CONTRACT_V2: Final = "m3.3-chunked-f0-l2-stage-plan/2"

#: The applied unit that binds its statement registry and statement execution set.
L2_APPLIED_UNIT_CONTRACT_V2: Final = "m3.3-chunked-f0-l2-applied-unit/2"

#: The stage receipt that carries the execution set and the observability status.
L2_STAGE_RECEIPT_CONTRACT_V2: Final = "m3.3-chunked-f0-l2-stage-receipt/2"

#: The runtime tool manifest's own contract -- never a StagePlan contract string.
L2_TOOL_MANIFEST_CONTRACT: Final = "m3.3-chunked-f0-l2-tool-manifest/1"

#: The operation registry a StagePlan binds: every material operation of every stage.
L2_STATEMENT_REGISTRY_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-registry/1"

#: The per-statement journal and its event lines (restated literals; equal to the primitives').
L2_STATEMENT_JOURNAL_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-journal/1"
L2_STATEMENT_EVENT_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-event/1"

#: The ordered set of successful, sealed journals one applied unit binds.
L2_STATEMENT_EXECUTION_SET_CONTRACT: Final = "m3.3-chunked-f0-l2-statement-execution-set/1"

#: The durable per-run observability closeout published before the terminal record.
L2_OBSERVABILITY_CLOSEOUT_CONTRACT: Final = "m3.3-chunked-f0-l2-observability-closeout/1"

#: The one directory name statement journals live under, beneath the stage receipt root.
STATEMENT_PROGRESS_DIRECTORY: Final = "statement-progress"

#: The request kind a successor final carries; refused by :func:`_child_main` and by every
#: legacy reader, and dispatched by the calibration child only under the final role.
SUCCESSOR_REQUEST_KIND_FINAL: Final = "successor-final"

#: The two successor routes. A route is a property of the request, of the StagePlan and of the
#: process-local proof, and the three must agree.
SUCCESSOR_ROUTE_PRODUCTION: Final = "production"
SUCCESSOR_ROUTE_CALIBRATION: Final = "calibration"
SUCCESSOR_ROUTES: Final[tuple[str, ...]] = (SUCCESSOR_ROUTE_PRODUCTION, SUCCESSOR_ROUTE_CALIBRATION)

#: The calibration envelope step the successor final is issued under.
_SUCCESSOR_CALIBRATION_STEP: Final = "successor-final"

#: The successor control tables inside ``working_catalog.sqlite3`` -- run-local, successor-only,
#: never migration-managed, never business tables, never inside a row count or logical digest.
L2_STAGE_PLAN_TABLE: Final = "m3_l2_stage_plan"
L2_APPLIED_UNITS_TABLE: Final = "m3_l2_applied_units"
L2_CROSS_STORE_BINDINGS_TABLE: Final = "m3_l2_cross_store_bindings"
L2_DEFERRED_INDEXES_TABLE: Final = "m3_l2_deferred_indexes"
L2_CONTROL_TABLES: Final[tuple[str, ...]] = (
    L2_STAGE_PLAN_TABLE,
    L2_APPLIED_UNITS_TABLE,
    L2_CROSS_STORE_BINDINGS_TABLE,
    L2_DEFERRED_INDEXES_TABLE,
)

#: The six successor persistent internal semantic relations: the durable counterparts of the
#: six legacy TEMP relations, charged as world-volume growth rather than SQLITE_TMPDIR spill.
L2_WITNESS_RANK_TABLE: Final = "m3_l2_chunk_witness_rank"
L2_CORRECTIONS_TABLE: Final = "m3_l2_chunk_observation_corrections"
L2_PLAN_WITNESS_TABLE: Final = "m3_l2_plan_chunk_witnesses"
L2_PLAN_WITNESS_RANK_TABLE: Final = "m3_l2_plan_witness_rank"
L2_PLAN_LEDGER_TABLE: Final = "m3_l2_chunk_first_witness"
L2_MEMBER_DELTA_TABLE: Final = "m3_l2_chunk_member_delta"
L2_PERSISTENT_RELATIONS: Final[tuple[str, ...]] = (
    L2_WITNESS_RANK_TABLE,
    L2_CORRECTIONS_TABLE,
    L2_PLAN_WITNESS_TABLE,
    L2_PLAN_WITNESS_RANK_TABLE,
    L2_PLAN_LEDGER_TABLE,
    L2_MEMBER_DELTA_TABLE,
)

#: The five declared secondary indexes the successor captures, drops and rebuilds -- exact.
EXPECTED_DEFERRED_INDEX_NAMES: Final[tuple[str, ...]] = (
    "idx_census_parsed_identity",
    "idx_census_parsed_observation",
    "idx_census_registrant_history",
    "idx_census_structural_state",
    "idx_census_structural_untrustworthy",
)

#: The exact governed manifest membership of one level-1 intermediate -- D151-R19A-C5-R1. The
#: accepted intermediate receipt's manifest is the sole authority; these six names are what an
#: authentic manifest holds, in canonical filename order, and nothing else is a member.
GOVERNED_INTERMEDIATE_MANIFEST_NAMES: Final[tuple[str, ...]] = (
    CHUNK_PLAN_FILENAME,
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    INTERMEDIATE_WITNESS_FILENAME,
    MERGE_SCHEDULE_FILENAME,
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
)

#: The successor stage identifiers, in graph order. Route-specific terminal stages are named by
#: their route suffix; the two routes never share a terminal stage identifier.
_STAGE_INITIALIZE: Final = "S0"
_STAGE_CAPTURE_DROP_INDEXES: Final = "S1"
_STAGE_REDUCED_PARSER_RUN: Final = "S2"
_STAGE_WITNESS_RANK: Final = "S11"
_STAGE_CORRECTIONS: Final = "S12"
_STAGE_ACCESSION_OBSERVATIONS: Final = "S13"
_STAGE_EDGES_AND_CONFLICTS: Final = "S14"
_STAGE_PARSER_STATE: Final = "S15P"
_STAGE_COUNTERS_FINALIZE: Final = "S17C"
_STAGE_SIDECAR: Final = "S18"
_STAGE_OUTCOME: Final = "S19"
_STAGE_MARK_PARSED: Final = "S20P"
_STAGE_REAUTHENTICATE_PRODUCTION: Final = "S21P"
_STAGE_F0_CHECKPOINT: Final = "S22P"
_STAGE_FINAL_RECEIPT: Final = "S23P"
_STAGE_REAUTHENTICATE_CALIBRATION: Final = "S20C"
_STAGE_CALIBRATION_RESULT: Final = "S21C"

#: The table stages S3..S10 in the accepted foreign-key load order, minus the observation table
#: (S13, loaded after the corrections) -- each its own transaction, checkpoint and receipt.
_TABLE_STAGES: Final[tuple[tuple[str, str], ...]] = (
    ("S3", "census_parsed_records"),
    ("S4", "census_quarantined_records"),
    ("S5", "census_structural_observations"),
    ("S6", "census_registrants"),
    ("S7", "census_registrant_observations"),
    ("S8", "census_accessions"),
    ("S9", "census_historical_references"),
    ("S10", "census_malformed_historical_references"),
)

_KIND_INITIALIZE: Final = "initialize_and_promote_world"
_KIND_CAPTURE_DROP: Final = "capture_and_drop_deferred_indexes"
_KIND_REDUCED_RUN: Final = "reduced_parser_run"
_KIND_TABLE_LOAD: Final = "table_load"
_KIND_WITNESS_RANK: Final = "chunk_witness_rank"
_KIND_CORRECTIONS: Final = "observation_corrections"
_KIND_OBSERVATION_LOAD: Final = "accession_observations"
_KIND_EDGES: Final = "candidate_edges_and_accession_conflicts"
_KIND_PARSER_STATE: Final = "parser_state"
_KIND_INDEX_REBUILD: Final = "deferred_index_rebuild"
_KIND_COUNTER_CATALOG: Final = "counter_catalog_batch"
_KIND_COUNTER_LEDGER: Final = "counter_ledger_batch"
_KIND_COUNTERS_FINALIZE: Final = "plan_witness_rank_finalize"
_KIND_SIDECAR: Final = "sidecar_merge"
_KIND_OUTCOME: Final = "derive_outcome_and_require_f0_success"
_KIND_MARK_PARSED: Final = "mark_parsed"
_KIND_REAUTHENTICATE: Final = "reauthenticate_intermediates_and_selected_requests"
_KIND_F0_CHECKPOINT: Final = "publish_f0_checkpoint"
_KIND_FINAL_RECEIPT: Final = "final_production_receipt_last"
_KIND_CALIBRATION_RESULT: Final = "calibration_subset_result_last"

_ATTACH_NONE: Final = "none"
_ATTACH_INTERMEDIATES: Final = "intermediates"
_ATTACH_CATALOG_BATCH: Final = "catalog_batch"
_ATTACH_LEDGER_BATCH: Final = "ledger_batch"

#: The at-most-nine attachment bound the engine asserts itself, never leaving it to SQLite.
_MAX_STAGE_ATTACHMENTS: Final = SINGLE_PASS_CHUNK_CAP

#: The default page-cache budget a synthetic successor StagePlan carries in this repository's
#: tests. Not a production value: the successor refuses a plan without an explicit budget.
DEFAULT_SYNTHETIC_CACHE_BYTES: Final = 8_388_608

_BINDING_SIDECAR: Final = "sidecar"
_BINDING_MARK_PARSED: Final = "mark_parsed"
_BINDING_REAUTHENTICATION: Final = "intermediate_reauthentication"
_BINDING_F0_CHECKPOINT: Final = "f0_checkpoint"
_BINDING_RESULT_READY: Final = "result_ready"

_WAL_ABSENT: Final = "WAL_ABSENT"
_WAL_ZERO: Final = "WAL_ZERO"
_WAL_NONZERO: Final = "WAL_NONZERO"

#: A refusal text both derivation guards share -- the legacy TEMP guard and the successor's
#: applied-unit guard -- so a reader of either refusal recognizes the same rule.
_ALREADY_DERIVED: Final = "already derived on this connection"

_STAGE_CONFLICT: Final = "STAGE_CONFLICT"
_STAGE_EXECUTE: Final = "STAGE_EXECUTE"
_STAGE_COMMITTED_RECEIPT_PENDING: Final = "STAGE_COMMITTED_RECEIPT_PENDING"
_STAGE_COMPLETE: Final = "STAGE_COMPLETE"
_RESIDUE_NONE: Final = "NONE"
_RESIDUE_PENDING: Final = "COMMITTED_STAGE_PENDING_RECEIPT"
_RESIDUE_ROLLBACK: Final = "ROLLBACK_OR_INTERRUPTION_RESIDUE"


def _stage_conflict(detail: str) -> NoReturn:
    """Raise a terminal successor conflict: nothing is repaired, reinitialized or retried."""
    message = (
        f"{_STAGE_CONFLICT}: {detail}. A successor conflict is terminal: nothing here repairs, "
        "reinitializes, deletes, checkpoints or re-executes anything"
    )
    raise ChunkMultipassError(message)


def require_successor_cache_bytes(value: object) -> int:
    """The successor's page-cache budget, or a refusal -- D151-C31R2-R19A-C2 §40.

    ``type(value) is int`` deliberately, not ``isinstance``: ``bool`` is an ``int`` subclass and
    ``True`` is never a byte count. Missing, ``None``, a float, zero, a negative value and a
    value that is not a whole number of kibibytes are each refused independently -- the failed
    run passed ``null`` and silently ran a 35 GiB merge on SQLite's 2 MiB default, which is
    exactly the silence a required field exists to end.

    Raises:
        ChunkMultipassError: the value is not a positive integer multiple of 1024.
    """
    if value is None:
        message = (
            "a successor StagePlan requires cache_bytes; None is a REFUSAL, never SQLite's "
            "default page cache"
        )
        raise ChunkMultipassError(message)
    if type(value) is not int:
        message = (
            f"a successor StagePlan's cache_bytes must be an int, not {type(value).__name__}; "
            "a bool or a float is refused rather than coerced"
        )
        raise ChunkMultipassError(message)
    if value <= 0:
        message = f"a successor StagePlan's cache_bytes must be positive; got {value}"
        raise ChunkMultipassError(message)
    if value % 1024:
        message = (
            f"a successor StagePlan's cache_bytes must be a whole number of kibibytes; {value} "
            "is not"
        )
        raise ChunkMultipassError(message)
    return value


def require_executable_level_two_cache_bytes(value: object) -> int:
    """The FUTURE Level-Two execution gate on the page-cache budget -- D151-C31R2-R19B-C2 §17.

    Asked again at every successor execution boundary that opens a world -- the initialization
    attempt and every bounded reopen -- with the rules of :func:`require_successor_cache_bytes`:
    ``type(value) is int``, no bool, no ``None``, no float, positive, a whole number of kibibytes.
    A parsed historical request whose cache is ``null`` stays readable and is never executed
    through this boundary; no SQLite default, synthetic or owner-candidate budget is substituted.

    Raises:
        ChunkMultipassError: the value is not an executable page-cache budget.
    """
    try:
        return require_successor_cache_bytes(value)
    except ChunkMultipassError as exc:
        message = (
            f"a Level-Two execution boundary requires an explicit executable cache_bytes ({exc}); "
            "a null, defaulted or substituted budget never opens a world"
        )
        raise ChunkMultipassError(message) from exc


#: The bounds the four statement-observability terms are held to -- exact ints, bool refused.
_INTERVAL_SECONDS_BOUNDS: Final = (1, 300)
_VM_STEPS_BOUNDS: Final = (1_000, 100_000)
_FRAME_BOUND_BOUNDS: Final = (1, 1 << 62)
_OBSERVABILITY_TERM_KEYS: Final[frozenset[str]] = frozenset(
    {
        "statement_progress_interval_seconds",
        "progress_handler_vm_steps",
        "wal_watchdog_max_uncommitted_frames",
        "expected_page_size_bytes",
    }
)


def _exact_int(value: object, name: str, bounds: tuple[int, int]) -> int:
    """``type(value) is int`` within closed ``bounds``; a bool, float or string is refused."""
    low, high = bounds
    if type(value) is not int:
        message = f"{name} must be an int, not {type(value).__name__}; a bool or a float is refused"
        raise ChunkMultipassError(message)
    if value < low or value > high:
        message = f"{name} must lie in [{low}, {high}]; got {value}"
        raise ChunkMultipassError(message)
    return value


@dataclass(frozen=True, slots=True)
class StatementObservabilityTerms:
    """The four request-carried observability terms a StagePlan /2 binds -- §19.

    None of them is a production value frozen by R19B: each is carried by the request that
    launches a successor run, validated exactly, and sealed into the StagePlan identity.
    """

    statement_progress_interval_seconds: int
    progress_handler_vm_steps: int
    wal_watchdog_max_uncommitted_frames: int
    expected_page_size_bytes: int

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "statement_progress_interval_seconds": self.statement_progress_interval_seconds,
            "progress_handler_vm_steps": self.progress_handler_vm_steps,
            "wal_watchdog_max_uncommitted_frames": self.wal_watchdog_max_uncommitted_frames,
            "expected_page_size_bytes": self.expected_page_size_bytes,
        }

    @property
    def frame_size_bytes(self) -> int:
        """One WAL frame at the expected page size: ``page_size + 24``."""
        return self.expected_page_size_bytes + WAL_FRAME_HEADER_BYTES

    @property
    def derived_watchdog_bytes(self) -> int:
        """The bytes the frame bound admits before the watchdog trips: frames x frame size."""
        return self.wal_watchdog_max_uncommitted_frames * self.frame_size_bytes


def require_statement_observability_terms(value: object) -> StatementObservabilityTerms:
    """The exact four-key mapping, each term an exact int within its bound -- §19.

    Raises:
        ChunkMultipassError: not a mapping with exactly the four keys, or a term is not an
            exact int in range, or the page size is not a SQLite page size.
    """
    if not isinstance(value, Mapping):
        message = (
            "statement_observability must be a mapping of the four observability terms; got "
            f"{type(value).__name__}"
        )
        raise ChunkMultipassError(message)
    keys = {str(key) for key in value}
    if keys != _OBSERVABILITY_TERM_KEYS:
        message = (
            f"statement_observability must carry exactly {sorted(_OBSERVABILITY_TERM_KEYS)}; got "
            f"{sorted(keys)}"
        )
        raise ChunkMultipassError(message)
    interval = _exact_int(
        value["statement_progress_interval_seconds"],
        "statement_progress_interval_seconds",
        _INTERVAL_SECONDS_BOUNDS,
    )
    vm_steps = _exact_int(
        value["progress_handler_vm_steps"], "progress_handler_vm_steps", _VM_STEPS_BOUNDS
    )
    frames = _exact_int(
        value["wal_watchdog_max_uncommitted_frames"],
        "wal_watchdog_max_uncommitted_frames",
        _FRAME_BOUND_BOUNDS,
    )
    try:
        page_size = require_sqlite_page_size(value["expected_page_size_bytes"])
    except WorkingCatalogError as exc:
        raise ChunkMultipassError(str(exc)) from exc
    return StatementObservabilityTerms(
        statement_progress_interval_seconds=interval,
        progress_handler_vm_steps=vm_steps,
        wal_watchdog_max_uncommitted_frames=frames,
        expected_page_size_bytes=page_size,
    )


def _identity_of(record: Mapping[str, object]) -> str:
    """SHA-256 over the canonical bytes of a record that carries no identity field."""
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def _json_text(record: object) -> str:
    """The canonical text rendering of one JSON-carriable value, without the trailing newline."""
    return canonical_json_bytes(cast("Mapping[str, object]", {"v": record})).decode("utf-8")[5:-2]


def _json_object(text: str, label: str) -> Mapping[str, object]:
    try:
        decoded = json.loads(text)
    except ValueError as exc:
        message = f"the successor {label} is not decodable JSON: {exc}"
        raise ChunkMultipassError(message) from exc
    if not isinstance(decoded, dict):
        message = f"the successor {label} is not a JSON object; refused"
        raise ChunkMultipassError(message)
    return cast("Mapping[str, object]", decoded)


@dataclass(frozen=True, slots=True)
class SuccessorFinalRequest:
    """Everything one successor final process is given -- and the only thing it is given.

    ``route`` selects the production or the calibration successor; the wrapper that reads the
    request requires the route it serves. ``cache_bytes`` is REQUIRED and validated at
    construction. ``stop_after_stage`` bounds one process to a prefix of the stage graph, which
    is how a stage runs in a fresh process: the next invocation classifies the committed
    evidence and continues. ``predecessor_*`` bind the run this successor continues -- claims
    about the predecessor, sealed into the StagePlan identity and held to the input count.
    """

    route: str
    plan_path: str
    schedule_path: str
    intermediates_root: str
    internal_root: str
    external_root: str | None
    operational_catalog: str
    world_directory: str
    stage_receipt_root: str
    run_id: str
    predecessor_run_id: str
    predecessor_checkpoint_count: int
    predecessor_tip_ordinal: int
    predecessor_tip_identity: str
    predecessor_completed_group_count: int
    cache_bytes: int
    repository_head_sha: str
    repository_tree_sha: str
    storage_requirements: Mapping[str, object]
    expected_sqlite_temp_binding: Mapping[str, object]
    statement_observability: Mapping[str, object]
    capacity_observations: tuple[Mapping[str, object], ...] = ()
    stop_after_stage: str | None = None
    kind: str = SUCCESSOR_REQUEST_KIND_FINAL

    def __post_init__(self) -> None:
        if self.kind != SUCCESSOR_REQUEST_KIND_FINAL:
            message = f"a successor request of kind {self.kind!r} is refused"
            raise ChunkMultipassError(message)
        if self.route not in SUCCESSOR_ROUTES:
            message = f"a successor request names route {self.route!r}; refused"
            raise ChunkMultipassError(message)
        require_successor_cache_bytes(self.cache_bytes)
        require_statement_observability_terms(self.statement_observability)
        for name in (
            "predecessor_checkpoint_count",
            "predecessor_tip_ordinal",
            "predecessor_completed_group_count",
        ):
            _stored_int(getattr(self, name), name)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering. Paths are the caller's; nothing is discovered."""
        return {
            "kind": self.kind,
            "route": self.route,
            "plan_path": self.plan_path,
            "schedule_path": self.schedule_path,
            "intermediates_root": self.intermediates_root,
            "internal_root": self.internal_root,
            "external_root": self.external_root,
            "operational_catalog": self.operational_catalog,
            "world_directory": self.world_directory,
            "stage_receipt_root": self.stage_receipt_root,
            "run_id": self.run_id,
            "predecessor_run_id": self.predecessor_run_id,
            "predecessor_checkpoint_count": self.predecessor_checkpoint_count,
            "predecessor_tip_ordinal": self.predecessor_tip_ordinal,
            "predecessor_tip_identity": self.predecessor_tip_identity,
            "predecessor_completed_group_count": self.predecessor_completed_group_count,
            "cache_bytes": self.cache_bytes,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "storage_requirements": dict(self.storage_requirements),
            "expected_sqlite_temp_binding": dict(self.expected_sqlite_temp_binding),
            "statement_observability": dict(self.statement_observability),
            "capacity_observations": [dict(item) for item in self.capacity_observations],
            "stop_after_stage": self.stop_after_stage,
        }

    @property
    def observability_terms(self) -> StatementObservabilityTerms:
        """The validated observability terms this request carries."""
        return require_statement_observability_terms(self.statement_observability)

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> SuccessorFinalRequest:
        """Rebuild a request from its stored mapping.

        Raises:
            ChunkMultipassError: a field is absent, is not of the recorded type, the kind or
                route is unknown, or the cache budget is refused.
        """
        try:
            external = record["external_root"]
            storage = record["storage_requirements"]
            expected = record["expected_sqlite_temp_binding"]
            observability = record["statement_observability"]
            observations = record["capacity_observations"]
            stop_after = record["stop_after_stage"]
            if (
                not isinstance(storage, Mapping)
                or not isinstance(expected, Mapping)
                or not isinstance(observability, Mapping)
                or not isinstance(observations, list)
            ):
                message = (
                    "a successor request's storage, binding, observability terms or "
                    "observations are not of shape"
                )
                raise ChunkMultipassError(message)
            return cls(
                kind=str(record["kind"]),
                route=str(record["route"]),
                plan_path=str(record["plan_path"]),
                schedule_path=str(record["schedule_path"]),
                intermediates_root=str(record["intermediates_root"]),
                internal_root=str(record["internal_root"]),
                external_root=None if external is None else str(external),
                operational_catalog=str(record["operational_catalog"]),
                world_directory=str(record["world_directory"]),
                stage_receipt_root=str(record["stage_receipt_root"]),
                run_id=str(record["run_id"]),
                predecessor_run_id=str(record["predecessor_run_id"]),
                predecessor_checkpoint_count=_stored_int(
                    record["predecessor_checkpoint_count"], "predecessor_checkpoint_count"
                ),
                predecessor_tip_ordinal=_stored_int(
                    record["predecessor_tip_ordinal"], "predecessor_tip_ordinal"
                ),
                predecessor_tip_identity=str(record["predecessor_tip_identity"]),
                predecessor_completed_group_count=_stored_int(
                    record["predecessor_completed_group_count"],
                    "predecessor_completed_group_count",
                ),
                cache_bytes=require_successor_cache_bytes(record["cache_bytes"]),
                repository_head_sha=str(record["repository_head_sha"]),
                repository_tree_sha=str(record["repository_tree_sha"]),
                storage_requirements={str(key): value for key, value in storage.items()},
                expected_sqlite_temp_binding={str(key): value for key, value in expected.items()},
                statement_observability={str(key): value for key, value in observability.items()},
                capacity_observations=tuple(
                    {str(key): value for key, value in item.items()}
                    for item in observations
                    if isinstance(item, Mapping)
                ),
                stop_after_stage=None if stop_after is None else str(stop_after),
            )
        except KeyError as exc:
            message = f"a successor request could not be read as this build writes them: {exc}"
            raise ChunkMultipassError(message) from exc


# --------------------------------------------------------------------------- #
# The runtime tool manifest -- §26: recomputed from the implementation files at every admission
# --------------------------------------------------------------------------- #
#: The implementation modules whose bytes every successor stage is bound to. Recomputed from
#: the files on disk at every stage admission and compared with the StagePlan-bound identity;
#: a stored identity is never trusted and never copied forward.
_TOOL_MANIFEST_MODULES: Final[tuple[tuple[str, str], ...]] = (
    ("disclosure_drift.m3.chunk_multipass", __file__),
    ("disclosure_drift.m3.chunk_consolidation", _chunk_consolidation_module.__file__),
    ("disclosure_drift.m3.working_catalog", _working_catalog_module.__file__),
    ("disclosure_drift.m3.chunk_tiering", _chunk_tiering_module.__file__),
    ("disclosure_drift.m3.chunk_execution", _chunk_execution_module.__file__),
    ("disclosure_drift.m3.chunk_evidence", _chunk_evidence_module.__file__),
    ("disclosure_drift.m3.chunk_plan", _chunk_plan_module.__file__),
    ("disclosure_drift.m3.chunk_storage", _chunk_storage_module.__file__),
    ("disclosure_drift.m3.compact_evidence", _compact_evidence_module.__file__),
    ("disclosure_drift.m3.offline_parse", _offline_parse_module.__file__),
    ("disclosure_drift.m3.single_source_canary", _single_source_canary_module.__file__),
    ("disclosure_drift.m3.canary_phases", _canary_phases_module.__file__),
    ("disclosure_drift.m3.repository_identity", _repository_identity_module.__file__),
    ("disclosure_drift.storage.sqlite", _storage_sqlite_module.__file__),
    ("disclosure_drift.storage.catalog", _storage_catalog_module.__file__),
    ("disclosure_drift.sec.census", _census_module.__file__),
    # D151-C31R2-R19B-C2 (R19A-R1 MINOR-2): the two further modules the successor region
    # reaches -- the peak-RSS and free-space readers, and the error base every refusal derives
    # from -- so the declared influence set is the complete one.
    ("disclosure_drift.m3.canary_runtime", _canary_runtime_module.__file__),
    ("disclosure_drift.errors", _errors_module.__file__),
)


@dataclass(frozen=True, slots=True)
class ToolManifest:
    """The implementation files a successor stage runs from, hashed NOW, and their identity."""

    entries: tuple[Mapping[str, object], ...]
    identity: str

    def as_record(self) -> Mapping[str, object]:
        """The persisted rendering: the entries and the identity over them."""
        return {
            "contract": L2_TOOL_MANIFEST_CONTRACT,
            "entries": [dict(entry) for entry in self.entries],
            "tool_manifest_identity": self.identity,
        }

    def source_file_digests(self) -> Mapping[str, str]:
        """Module name to direct source-file digest -- the per-file view of the same bytes."""
        return {str(entry["module"]): str(entry["sha256"]) for entry in self.entries}


def _runtime_tool_manifest() -> ToolManifest:
    """Hash every implementation file this process actually imported, from disk, now.

    Raises:
        ChunkMultipassError: a module is not loaded from a ``.py`` source file, or a file is a
            link or absent.
    """
    entries: list[Mapping[str, object]] = []
    for module, file in _TOOL_MANIFEST_MODULES:
        path = Path(str(file))
        if path.suffix != ".py":
            message = (
                f"implementation module {module!r} is not loaded from a .py source file "
                f"({path.name!r}); the successor binds source bytes and refuses anything else"
            )
            raise ChunkMultipassError(message)
        try:
            sha256, length = file_sha256(path)
        except ChunkEvidenceError as exc:
            message = f"implementation module {module!r} could not be hashed: {exc}"
            raise ChunkMultipassError(message) from exc
        entries.append(
            {"module": module, "filename": path.name, "sha256": sha256, "byte_length": length}
        )
    body = {"contract": L2_TOOL_MANIFEST_CONTRACT, "entries": entries}
    return ToolManifest(entries=tuple(entries), identity=_identity_of(body))


def _require_runtime_tool_identity(expected_identity: str, *, label: str) -> ToolManifest:
    """Recompute the manifest from disk and hold it to ``expected_identity`` -- §26.

    Raises:
        ChunkMultipassError: the implementation files on disk are not the ones bound.
    """
    manifest = _runtime_tool_manifest()
    if manifest.identity != expected_identity:
        _stage_conflict(
            f"{label}: the implementation files on disk hash to tool-manifest identity "
            f"{manifest.identity[:16]}... where the StagePlan binds {expected_identity[:16]}...; "
            "a changed tool is never continued under the old identity"
        )
    return manifest


# --------------------------------------------------------------------------- #
# Governed membership and selected-request provenance -- D151-R19A-C5-R1/R2, C6-R2, C7
# --------------------------------------------------------------------------- #
def _governed_intermediate_manifest_entries(
    receipt: IntermediateReceipt,
) -> tuple[ArtifactEntry, ...]:
    """The six governed manifest entries of one authenticated intermediate receipt, canonical.

    The accepted intermediate receipt and its manifest are the SOLE authority for governed
    membership (D151-R19A-C5-R1). The input is the already parsed receipt the accepted resolver
    returned -- never a directory listing, a flattened name set, a glob or a Boolean -- and the
    membership is taken from the manifest it carries, authenticated rather than trusted:

    * the contract is exactly :data:`INTERMEDIATE_RECEIPT_CONTRACT` and the status is complete;
    * the manifest re-derives through the accepted :class:`ArtifactManifest.from_record`, which
      recomputes the stored digest over the entries beside it, and the recomputed identity
      equals the receipt's own;
    * there are exactly six entries, each a canonical basename -- no absolute path, no parent
      traversal, no nested path, no empty component, no duplicate -- and their names are
      exactly :data:`GOVERNED_INTERMEDIATE_MANIFEST_NAMES`, each once;
    * the receipt filename and any ``*-request.json`` are refused as members, as is any
      seventh, unknown or missing entry.

    The entries are returned exactly as the manifest carries them -- hashes, byte lengths and
    paths unchanged -- in canonical filename order.

    Raises:
        ChunkMultipassError: any of the above.
    """
    _require(
        receipt.contract == INTERMEDIATE_RECEIPT_CONTRACT and receipt.status == "complete",
        f"governed membership is taken only from a complete {INTERMEDIATE_RECEIPT_CONTRACT!r} "
        f"receipt; this one carries {receipt.contract!r} with status {receipt.status!r}",
    )
    try:
        rederived = ArtifactManifest.from_record(dict(receipt.manifest.as_record()))
    except ChunkEvidenceError as exc:
        message = f"an intermediate receipt's manifest does not re-derive: {exc}"
        raise ChunkMultipassError(message) from exc
    _require(
        rederived.digest == receipt.manifest.digest and rederived == receipt.manifest,
        "an intermediate receipt's manifest identity does not describe its own entries; refused",
    )
    entries = receipt.manifest.entries
    _require(
        len(entries) == len(GOVERNED_INTERMEDIATE_MANIFEST_NAMES),
        f"an intermediate manifest must carry exactly {len(GOVERNED_INTERMEDIATE_MANIFEST_NAMES)} "
        f"governed entries; this one carries {len(entries)}: "
        f"{[entry.relative_path for entry in entries]}",
    )
    seen: set[str] = set()
    for entry in entries:
        name = entry.relative_path
        _require(
            bool(name)
            and "/" not in name
            and "\\" not in name
            and name not in {".", ".."}
            and not name.startswith("/")
            and name == name.strip(),
            f"manifest entry {name!r} is not a canonical basename; refused",
        )
        _require(
            name != INTERMEDIATE_RECEIPT_FILENAME and not name.endswith("-request.json"),
            f"manifest entry {name!r} is never a governed member: the receipt and the group "
            "request are provenance, not semantic input",
        )
        _require(
            name in GOVERNED_INTERMEDIATE_MANIFEST_NAMES,
            f"manifest entry {name!r} is not one of the governed names "
            f"{list(GOVERNED_INTERMEDIATE_MANIFEST_NAMES)}; refused",
        )
        _require(name not in seen, f"manifest entry {name!r} appears more than once; refused")
        seen.add(name)
        _require(
            len(entry.sha256) == 64 and entry.byte_length >= 0,
            f"manifest entry {name!r} carries a malformed digest or byte length; refused",
        )
    _require(
        seen == set(GOVERNED_INTERMEDIATE_MANIFEST_NAMES),
        "an intermediate manifest is missing "
        f"{sorted(set(GOVERNED_INTERMEDIATE_MANIFEST_NAMES) - seen)}",
    )
    return tuple(sorted(entries, key=lambda entry: entry.relative_path))


@dataclass(frozen=True, slots=True)
class GroupRequestProvenance:
    """The selected attempt's group request, bound as provenance and nothing more -- C5-R2."""

    relative_filename: str
    byte_length: int
    sha256: str

    def as_record(self) -> Mapping[str, object]:
        """The persisted rendering, with its classification stated explicitly."""
        return {
            "relative_filename": self.relative_filename,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            "governed_manifest_member": False,
            "governed_aggregate_member": False,
            "successor_semantic_input": False,
            "provenance_bound": True,
        }


def _selected_group_request_provenance(intermediate: IntermediateInput) -> GroupRequestProvenance:
    """The one group request the selected attempt belongs to, by deterministic association.

    D151-R19A-C6-R2:
    ``request_path = attempt_root.parent / f"{group_id}-{attempt:03d}-request.json"``
    from the accepted selected-intermediate resolution -- never a glob, a first match, a
    lexicographic or newest choice, or a candidate-set winner. Other attempts' retained requests
    may sit beside it; their presence is not ambiguity. The selected request must be a regular
    non-symlink file with the expected basename in the expected group directory, and it is
    never a manifest member, never governed aggregate bytes and never a semantic input.

    Raises:
        ChunkMultipassError: the attempt directory does not carry the selected ordinal, the
            request is absent, a link, or not a regular file, or it is named by the manifest.
    """
    attempt = intermediate.receipt.attempt
    directory = intermediate.directory
    expected_directory = f"attempt-{attempt:03d}"
    _require(
        directory.name == expected_directory and directory.parent.name == intermediate.group_id,
        f"intermediate {intermediate.group_id!r} resolved to {directory.parent.name}/"
        f"{directory.name} where its receipt names attempt {attempt}; the selected request "
        "is associated through the accepted resolution and never guessed",
    )
    request_path = directory.parent / f"{intermediate.group_id}-{attempt:03d}-request.json"
    try:
        status = os.lstat(request_path)
    except OSError as exc:
        message = (
            f"the selected group request {request_path.name!r} for intermediate "
            f"{intermediate.group_id!r} is absent; a StagePlan binds every selected request "
            f"as provenance and refuses without it: {exc}"
        )
        raise ChunkMultipassError(message) from exc
    _require(
        stat.S_ISREG(status.st_mode),
        f"the selected group request {request_path.name!r} is not a regular file "
        "(a symbolic link or another object is refused)",
    )
    _require(
        request_path.name
        not in {entry.relative_path for entry in intermediate.receipt.manifest.entries},
        f"the selected group request {request_path.name!r} is named by the intermediate "
        "manifest; a request is provenance and never a governed member",
    )
    sha256, length = file_sha256(request_path)
    return GroupRequestProvenance(
        relative_filename=request_path.name, byte_length=length, sha256=sha256
    )


def _successor_intermediate_descriptor(intermediate: IntermediateInput) -> Mapping[str, object]:
    """One StagePlan intermediate descriptor: receipt, manifest, governed entries, provenance."""
    receipt = intermediate.receipt
    entries = _governed_intermediate_manifest_entries(receipt)
    provenance = _selected_group_request_provenance(intermediate)
    document_sha256, document_length = file_sha256(
        intermediate.directory / INTERMEDIATE_RECEIPT_FILENAME
    )
    return {
        "group_id": intermediate.group_id,
        "ordinal": intermediate.ordinal,
        "region": intermediate.region,
        "start": intermediate.start,
        "end": intermediate.end,
        "attempt": receipt.attempt,
        "attempt_directory_name": intermediate.directory.name,
        "receipt_document_sha256": document_sha256,
        "receipt_document_byte_length": document_length,
        "receipt_record_identity": _identity_of(dict(receipt.as_record())),
        "manifest_digest": receipt.manifest.digest,
        "manifest_total_bytes": receipt.manifest.total_bytes,
        "governed_entries": [dict(entry.as_record()) for entry in entries],
        "governed_bytes": sum(entry.byte_length for entry in entries),
        "input_chunk_ids": list(receipt.input_chunk_ids),
        "witness_ledger_identity": receipt.witness_ledger_identity,
        "compact_evidence_identity": receipt.compact_evidence_identity,
        "group_request_provenance": dict(provenance.as_record()),
    }


# --------------------------------------------------------------------------- #
# The stage graph -- §32
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class L2Stage:
    """One successor stage: its ordinal, identifier, unit, kind and attachment class."""

    ordinal: int
    stage_id: str
    unit_id: str
    kind: str
    attachments: str
    batch: int | None = None
    table: str | None = None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "ordinal": self.ordinal,
            "stage_id": self.stage_id,
            "unit_id": self.unit_id,
            "kind": self.kind,
            "attachments": self.attachments,
            "batch": self.batch,
            "table": self.table,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> L2Stage:
        """Rebuild one stage descriptor from its stored mapping."""
        batch = record.get("batch")
        table = record.get("table")
        return cls(
            ordinal=_stored_int(record["ordinal"], "ordinal"),
            stage_id=str(record["stage_id"]),
            unit_id=str(record["unit_id"]),
            kind=str(record["kind"]),
            attachments=str(record["attachments"]),
            batch=None if batch is None else _stored_int(batch, "batch"),
            table=None if table is None else str(table),
        )


def successor_stage_graph(route: str, counter_source_count: int) -> tuple[L2Stage, ...]:
    """The exact ordered stage graph of one successor route over ``counter_source_count`` chunks.

    Variable-count by construction: the number of counter batches is ``ceil(chunks / fan-in)``,
    the five deferred-index units are exact, and the production and calibration routes differ
    only in their terminal stages (§32). Nothing here names five intermediates or any other
    campaign-specific count.
    """
    _require(route in SUCCESSOR_ROUTES, f"route {route!r} has no stage graph")
    _require(counter_source_count >= 1, "a successor stage graph needs at least one chunk source")
    stages: list[L2Stage] = []

    def add(stage_id: str, unit_id: str, kind: str, attachments: str, **extra: object) -> None:
        batch = extra.get("batch")
        table = extra.get("table")
        stages.append(
            L2Stage(
                ordinal=len(stages),
                stage_id=stage_id,
                unit_id=unit_id,
                kind=kind,
                attachments=attachments,
                batch=None if batch is None else int(cast("int", batch)),
                table=None if table is None else str(table),
            )
        )

    add(_STAGE_INITIALIZE, "world", _KIND_INITIALIZE, _ATTACH_NONE)
    add(_STAGE_CAPTURE_DROP_INDEXES, "deferred-index-set", _KIND_CAPTURE_DROP, _ATTACH_NONE)
    add(_STAGE_REDUCED_PARSER_RUN, "census_parser_runs", _KIND_REDUCED_RUN, _ATTACH_INTERMEDIATES)
    for stage_id, table in _TABLE_STAGES:
        add(stage_id, table, _KIND_TABLE_LOAD, _ATTACH_INTERMEDIATES, table=table)
    add(_STAGE_WITNESS_RANK, L2_WITNESS_RANK_TABLE, _KIND_WITNESS_RANK, _ATTACH_INTERMEDIATES)
    add(_STAGE_CORRECTIONS, L2_CORRECTIONS_TABLE, _KIND_CORRECTIONS, _ATTACH_NONE)
    add(
        _STAGE_ACCESSION_OBSERVATIONS,
        "census_accession_observations",
        _KIND_OBSERVATION_LOAD,
        _ATTACH_INTERMEDIATES,
        table="census_accession_observations",
    )
    add(_STAGE_EDGES_AND_CONFLICTS, "census_candidate_lineage_edges", _KIND_EDGES, _ATTACH_NONE)
    if route == SUCCESSOR_ROUTE_PRODUCTION:
        add(
            _STAGE_PARSER_STATE,
            "census_plan_sources.parser_state",
            _KIND_PARSER_STATE,
            _ATTACH_NONE,
        )
    for index, name in enumerate(EXPECTED_DEFERRED_INDEX_NAMES):
        add(f"S16.{index}", name, _KIND_INDEX_REBUILD, _ATTACH_NONE)
    batches = -(-counter_source_count // MERGE_FAN_IN)
    for batch in range(batches):
        add(
            f"S17A.{batch}",
            f"batch-{batch:03d}",
            _KIND_COUNTER_CATALOG,
            _ATTACH_CATALOG_BATCH,
            batch=batch,
        )
        add(
            f"S17B.{batch}",
            f"batch-{batch:03d}",
            _KIND_COUNTER_LEDGER,
            _ATTACH_LEDGER_BATCH,
            batch=batch,
        )
    add(_STAGE_COUNTERS_FINALIZE, L2_PLAN_WITNESS_RANK_TABLE, _KIND_COUNTERS_FINALIZE, _ATTACH_NONE)
    add(_STAGE_SIDECAR, COMPACT_EVIDENCE_SIDECAR_FILENAME, _KIND_SIDECAR, _ATTACH_NONE)
    add(_STAGE_OUTCOME, "derived-outcome", _KIND_OUTCOME, _ATTACH_NONE)
    if route == SUCCESSOR_ROUTE_PRODUCTION:
        add(_STAGE_MARK_PARSED, PROGRESS_LEDGER_FILENAME, _KIND_MARK_PARSED, _ATTACH_NONE)
        add(_STAGE_REAUTHENTICATE_PRODUCTION, "intermediates", _KIND_REAUTHENTICATE, _ATTACH_NONE)
        add(_STAGE_F0_CHECKPOINT, PHASE_F0, _KIND_F0_CHECKPOINT, _ATTACH_NONE)
        add(_STAGE_FINAL_RECEIPT, FINAL_WORLD_RECEIPT_FILENAME, _KIND_FINAL_RECEIPT, _ATTACH_NONE)
    else:
        add(_STAGE_REAUTHENTICATE_CALIBRATION, "intermediates", _KIND_REAUTHENTICATE, _ATTACH_NONE)
        add(
            _STAGE_CALIBRATION_RESULT,
            CALIBRATION_SUBSET_RESULT_FILENAME,
            _KIND_CALIBRATION_RESULT,
            _ATTACH_NONE,
        )
    return tuple(stages)


# --------------------------------------------------------------------------- #
# The operation registry -- D151-C31R2-R19B-C2 §20, §21, §24 (owner rulings C2-R1, C2-R2)
# --------------------------------------------------------------------------- #
_ROLE_WORKING_CATALOG: Final = "WORKING_CATALOG"
_ROLE_COMPACT_EVIDENCE: Final = "COMPACT_EVIDENCE"
_ROLE_INTERMEDIATES: Final = "INTERMEDIATES"
_ROLE_WORLD: Final = "WORLD"
_WATCHDOG_ROLES: Final[frozenset[str]] = frozenset({_ROLE_WORKING_CATALOG, _ROLE_COMPACT_EVIDENCE})

_MODE_STATIC_SQL: Final = "STATIC_SQL"
_MODE_DYNAMIC_SQL_CAPTURE: Final = "DYNAMIC_SQL_CAPTURE"
_MODE_CALLABLE_NON_SQL: Final = "CALLABLE_NON_SQL"
_SQL_MODES: Final[frozenset[str]] = frozenset({_MODE_STATIC_SQL, _MODE_DYNAMIC_SQL_CAPTURE})

_PHASE_PREPARE: Final = "prepare"
_PHASE_TRANSACTION: Final = "transaction"
_PHASE_POST_COMMIT: Final = "post_commit"

_S18_PATH_BUILD: Final = "BUILD"
_S18_PATH_AUTHENTICATE: Final = "AUTHENTICATE"
_S18_PATHS: Final[tuple[str, ...]] = (_S18_PATH_BUILD, _S18_PATH_AUTHENTICATE)

_KIND_EXECUTEMANY: Final = "executemany"
_KIND_CALLABLE: Final = "callable"
_KIND_PATH_DECISION: Final = "path_decision"
_SQL_EXECUTION_KINDS: Final[frozenset[str]] = frozenset(
    {STATEMENT_KIND_EXECUTE, STATEMENT_KIND_FETCHALL, STATEMENT_KIND_ITERATE, _KIND_EXECUTEMANY}
)

_EXPECTED_DATA_DEPENDENT: Final = "data_dependent"
_EXPECTED_S2_DUPLICATES: Final = "witness:S2.duplicate_identities"

#: The owner classification of the one ``executemany`` in the consolidator (D151-R19B-C2-R1):
#: bounded by the duplicate-accession correction set, never routed through instrumentation.
STAGE_ROWS_CLASSIFICATION: Final = "BOUNDED_CONTROL_OPERATION"

#: The exact static statements the successor stage functions execute, stated once so the
#: registry binds each SHA-256 before execution and the runtime holds the text to it.
_SQL_COUNT_TEMPLATE: Final = "SELECT COUNT(*) AS n FROM main.{table}"
_SQL_S11_CONTESTED: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_WITNESS_RANK_TABLE} "  # noqa: S608
    "WHERE witness_rank = 1 AND witnesses > 1"
)
_SQL_S12_ORPHANED_WINNERS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "LEFT JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain "
    "WHERE w.witness_rank = 1 AND w.witnesses > 1 AND a.accession_plain IS NULL"
)
_SQL_S12_ORPHANED_RIVALS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "LEFT JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id "
    "WHERE w.witness_rank > 1 AND p.parsed_record_id IS NULL"
)
_SQL_S12_INSERT_WINNERS: Final = (
    f"INSERT INTO main.{L2_CORRECTIONS_TABLE} "  # noqa: S608
    f"SELECT {_FUNCTION_STABLE_ID}('accession-observation', a.accession_plain, "
    "a.source_observation_id, a.parsed_record_id, je.key), "
    "a.accession_plain, a.source_observation_id, a.parsed_record_id, je.key, je.value, "
    "a.first_observed_at_utc, 0 "
    f"FROM main.{L2_WITNESS_RANK_TABLE} AS w "
    "JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain, "
    f"json_each({_FUNCTION_RECONSTRUCTED_FIELDS}(a.acceptance_datetime_sec_raw, "
    "CASE WHEN a.registrant_cik_numeric IS NULL THEN NULL "
    "ELSE printf('%010d', a.registrant_cik_numeric) END, "
    "a.filing_date_sec, a.form_type, a.primary_document_name, a.report_date)) AS je "
    "WHERE w.witness_rank = 1 AND w.witnesses > 1"
)
_SQL_S12_INSERT_RIVALS: Final = (
    f"INSERT INTO main.{L2_CORRECTIONS_TABLE} "  # noqa: S608
    f"SELECT {_FUNCTION_STABLE_ID}('accession-observation', w.accession_plain, "
    "w.source_observation_id, w.parsed_record_id, je.key), "
    "w.accession_plain, w.source_observation_id, w.parsed_record_id, je.key, je.value, "
    "w.first_observed_at_utc, 0 "
    f"FROM main.{L2_WITNESS_RANK_TABLE} AS w "
    "JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id, "
    f"json_each({_FUNCTION_RIVAL_FIELDS}(p.payload_json)) AS je "
    "WHERE w.witness_rank > 1"
)
_SQL_S12_SUMMARY: Final = (
    f"SELECT (SELECT COUNT(*) FROM main.{L2_WITNESS_RANK_TABLE} "  # noqa: S608
    "WHERE witness_rank = 1 AND witnesses > 1) AS contested, "
    f"(SELECT COUNT(*) FROM main.{L2_CORRECTIONS_TABLE}) AS staged"
)
_SQL_S15P_UPDATE: Final = (
    "UPDATE census_plan_sources SET parser_state = ? WHERE source_instance_id = ?"
)
_SQL_S17C_INSERT_RANK: Final = (
    f"INSERT INTO main.{L2_PLAN_WITNESS_RANK_TABLE} "  # noqa: S608
    "(accession_plain, parsed_record_id, witness_rank, witnesses) "
    "SELECT accession_plain, parsed_record_id, "
    "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY chunk_ordinal) AS witness_rank, "
    "COUNT(*) OVER (PARTITION BY accession_plain) AS witnesses "
    f"FROM main.{L2_PLAN_WITNESS_TABLE}"
)
_SQL_S17C_ORPHANED_WINNERS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "LEFT JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain "
    "WHERE w.witness_rank = 1 AND w.witnesses > 1 AND a.accession_plain IS NULL"
)
_SQL_S17C_ORPHANED_RIVALS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "LEFT JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id "
    "WHERE w.witness_rank > 1 AND p.parsed_record_id IS NULL"
)
_SQL_S17C_CONTESTED: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_PLAN_WITNESS_RANK_TABLE} "  # noqa: S608
    "WHERE witness_rank = 1 AND witnesses > 1"
)
_SQL_S17C_WINNER_ROWS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "JOIN main.census_accessions AS a ON a.accession_plain = w.accession_plain, "
    f"json_each({_FUNCTION_RECONSTRUCTED_FIELDS}(a.acceptance_datetime_sec_raw, "
    "CASE WHEN a.registrant_cik_numeric IS NULL THEN NULL "
    "ELSE printf('%010d', a.registrant_cik_numeric) END, "
    "a.filing_date_sec, a.form_type, a.primary_document_name, a.report_date)) AS je "
    "WHERE w.witness_rank = 1 AND w.witnesses > 1"
)
_SQL_S17C_RIVAL_ROWS: Final = (
    f"SELECT COUNT(*) AS n FROM main.{L2_PLAN_WITNESS_RANK_TABLE} AS w "  # noqa: S608
    "JOIN main.census_parsed_records AS p ON p.parsed_record_id = w.parsed_record_id, "
    f"json_each({_FUNCTION_RIVAL_FIELDS}(p.payload_json)) AS je "
    "WHERE w.witness_rank > 1"
)
_SQL_S17C_INSERT_MEMBER_DELTA: Final = (
    f"INSERT INTO main.{L2_MEMBER_DELTA_TABLE} (member_ordinal, delta) "  # noqa: S608
    "WITH ranked AS ("
    "  SELECT member_ordinal, delta_materialized,"
    "    ROW_NUMBER() OVER (PARTITION BY native_identity "
    "                       ORDER BY member_ordinal, record_ordinal) AS rn"
    f"  FROM main.{L2_PLAN_LEDGER_TABLE})"
    "SELECT member_ordinal, SUM(delta_materialized) AS delta FROM ranked "
    "WHERE rn > 1 GROUP BY member_ordinal"
)
_SQL_S17C_DELTAS: Final = (
    "SELECT COUNT(*) AS members, COALESCE(SUM(delta), 0) AS total "  # noqa: S608
    f"FROM main.{L2_MEMBER_DELTA_TABLE}"
)

#: The exact prefixes that identify the statements two modules R19B may not edit issue, as
#: observed at the connection-boundary proxy. Exact runtime SQL is captured at that boundary;
#: the registry binds the builder identity and this prefix.
_PREFIX_CANDIDATE_EDGES_SELECT: Final = (
    "SELECT value_text, GROUP_CONCAT(DISTINCT printf('%010d', cik_numeric)) AS ciks "
    "FROM census_registrant_observations"
)
_PREFIX_CANDIDATE_EDGES_INSERT: Final = "INSERT OR IGNORE INTO census_candidate_lineage_edges"
_PREFIX_MARK_CONFLICTS: Final = (
    "UPDATE census_accession_observations AS o SET conflict_indicator = 1"
)
_PREFIX_TABLE_ROW_COUNTS: Final = "SELECT COUNT(*) AS rows FROM "

#: Per stage kind, the proxy-observed statement prefixes that are bounded control operations
#: -- executed through the proxy unjournaled and counted, never instrumented: S14's per-pair
#: candidate-edge insert is bounded by the alias-sharing pair set, not by record volume.
_BOUNDED_PROXY_PREFIXES: Final[Mapping[str, tuple[str, ...]]] = {
    _KIND_EDGES: (_PREFIX_CANDIDATE_EDGES_INSERT,),
}

_OP_CANDIDATE_EDGES_SELECT: Final = "candidate_edges.select"
_OP_MARK_CONFLICTS: Final = "mark_accession_conflicts.update"
_OP_TABLE_ROW_COUNTS: Final = "table_row_counts"
_OP_PATH_DECISION: Final = "path_decision"
_OP_REAUTHENTICATE: Final = "reauthenticate_intermediates"
_OP_BUILD_MANIFEST: Final = "build_artifact_manifest"

_CC: Final = "disclosure_drift.m3.chunk_consolidation."
_CM: Final = "disclosure_drift.m3.chunk_multipass."
_CE: Final = "disclosure_drift.m3.compact_evidence.CompactEvidenceSidecar."
_CENSUS: Final = "disclosure_drift.sec.census.CensusCatalog."


def _count_sql(table: str) -> str:
    """The exact count statement the successor issues over one main table."""
    return _SQL_COUNT_TEMPLATE.format(table=table)


def _sql_sha256(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


def _source_module(source_callable: str) -> str:
    """The module a source callable lives in (its class segment removed where it has one)."""
    for prefix, module in (
        (_CENSUS, "disclosure_drift.sec.census"),
        (_CE, "disclosure_drift.m3.compact_evidence"),
        (_CM + "_StageInstrumentation.", "disclosure_drift.m3.chunk_multipass"),
    ):
        if source_callable.startswith(prefix):
            return module
    return source_callable.rsplit(".", 1)[0]


@dataclass(frozen=True, slots=True)
class _OperationDescriptor:
    """One registered material operation: what it is, where it runs, how its SQL is identified."""

    stage_id: str
    stage_ordinal: int
    unit_kind: str
    statement_ordinal: int
    operation: str
    database_role: str
    source_callable: str
    operation_kind: str
    sql_identity_mode: str
    static_sql_sha256: str | None
    sql_prefix: str | None
    expected_executions: int | str
    path: str | None
    phase: str
    watchdog_applicable: bool

    @property
    def statement_id(self) -> str:
        return f"{self.stage_id}/{self.operation}"

    def body(self) -> dict[str, object]:
        return {
            "stage_id": self.stage_id,
            "stage_ordinal": self.stage_ordinal,
            "unit_kind": self.unit_kind,
            "statement_ordinal": self.statement_ordinal,
            "statement_id": self.statement_id,
            "operation": self.operation,
            "database_role": self.database_role,
            "source_callable": self.source_callable,
            "source_module": _source_module(self.source_callable),
            "operation_kind": self.operation_kind,
            "sql_identity_mode": self.sql_identity_mode,
            "static_sql_sha256": self.static_sql_sha256,
            "sql_prefix": self.sql_prefix,
            "instrumentation_required": True,
            "watchdog_applicable": self.watchdog_applicable,
            "expected_executions": self.expected_executions,
            "path": self.path,
            "phase": self.phase,
        }

    def as_record(self) -> Mapping[str, object]:
        record = self.body()
        record["descriptor_identity"] = _identity_of(record)
        return record

    @property
    def identity(self) -> str:
        return _identity_of(self.body())


def _descriptor(
    stage: L2Stage,
    ordinal: int,
    operation: str,
    *,
    mode: str,
    kind: str,
    source: str,
    role: str = _ROLE_WORKING_CATALOG,
    static_sql: str | None = None,
    prefix: str | None = None,
    expected: int | str = 1,
    path: str | None = None,
    phase: str = _PHASE_TRANSACTION,
) -> _OperationDescriptor:
    _require(
        (mode == _MODE_STATIC_SQL) == (static_sql is not None),
        f"descriptor {operation!r}: STATIC_SQL binds exactly one static text",
    )
    _require(
        mode != _MODE_CALLABLE_NON_SQL or kind in {_KIND_CALLABLE, _KIND_PATH_DECISION},
        f"descriptor {operation!r}: a non-SQL operation is a callable or a path decision",
    )
    _require(
        mode == _MODE_CALLABLE_NON_SQL or kind in _SQL_EXECUTION_KINDS,
        f"descriptor {operation!r}: a SQL operation names a SQL execution kind",
    )
    return _OperationDescriptor(
        stage_id=stage.stage_id,
        stage_ordinal=stage.ordinal,
        unit_kind=stage.kind,
        statement_ordinal=ordinal,
        operation=operation,
        database_role=role,
        source_callable=source,
        operation_kind=kind,
        sql_identity_mode=mode,
        static_sql_sha256=None if static_sql is None else _sql_sha256(static_sql),
        sql_prefix=prefix,
        expected_executions=expected,
        path=path,
        phase=phase,
        watchdog_applicable=role in _WATCHDOG_ROLES and mode in _SQL_MODES,
    )


def _declared_operations(  # noqa: PLR0915 - one exhaustive table per stage kind
    stage: L2Stage, counter_source_count: int
) -> tuple[_OperationDescriptor, ...]:
    """Every material operation of one stage, in its declared order -- derived from source.

    S0 and S1 perform seed-bounded control work only (control schema, StagePlan row, the five
    persisted index rows and their DROP); S19 derives its outcome from committed witnesses and
    runs no SQL; S20P and S22P write the run-progress ledger, a control store. Every other stage
    lists each statement its function executes over a record-volume relation.
    """
    items: list[_OperationDescriptor] = []

    def add(operation: str, **terms: object) -> None:
        items.append(_descriptor(stage, len(items), operation, **cast("dict[str, Any]", terms)))

    def count(table: str, expected: int = 1) -> None:
        add(
            f"count:{table}",
            mode=_MODE_STATIC_SQL,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CM + "_StageInstrumentation.count",
            static_sql=_count_sql(table),
            expected=expected,
        )

    static = _MODE_STATIC_SQL
    dynamic = _MODE_DYNAMIC_SQL_CAPTURE
    kind = stage.kind
    if kind == _KIND_REDUCED_RUN:
        add(
            "reduced_parser_run.select_chunk_runs",
            mode=dynamic,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CC + "_reduced_parser_run",
        )
        add(
            "reduced_parser_run.insert_run_row",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CC + "_reduced_parser_run",
            static_sql=REDUCED_PARSER_RUN_INSERT_SQL,
        )
        count("census_parser_runs")
    elif kind == _KIND_TABLE_LOAD:
        table = str(stage.table)
        if _MERGE_STRATEGY[table] == "keyed_first_last":
            add(
                "keyed_first_last_load.insert",
                mode=dynamic,
                kind=STATEMENT_KIND_EXECUTE,
                source=_CC + "_keyed_first_last_load",
            )
        else:
            add(
                "sorted_bulk_load.insert",
                mode=dynamic,
                kind=STATEMENT_KIND_EXECUTE,
                source=_CC + "_sorted_bulk_load",
            )
        if table == "census_parsed_records":
            add(
                "apply_duplicate_identities.update",
                mode=static,
                kind=STATEMENT_KIND_EXECUTE,
                source=_CC + "_apply_duplicate_identities",
                static_sql=DUPLICATE_IDENTITY_UPDATE_SQL,
                expected=_EXPECTED_S2_DUPLICATES,
            )
        count(table)
    elif kind == _KIND_WITNESS_RANK:
        count(L2_WITNESS_RANK_TABLE, 2)
        add(
            "witness_rank.insert",
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_stage_witness_rank",
        )
        add(
            "witness_rank.contested",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CM + "_stage_witness_rank",
            static_sql=_SQL_S11_CONTESTED,
        )
    elif kind == _KIND_CORRECTIONS:
        count(L2_CORRECTIONS_TABLE)
        add(
            "corrections.orphaned_winners",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CM + "_stage_observation_corrections",
            static_sql=_SQL_S12_ORPHANED_WINNERS,
        )
        add(
            "corrections.orphaned_rivals",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CM + "_stage_observation_corrections",
            static_sql=_SQL_S12_ORPHANED_RIVALS,
        )
        add(
            "corrections.insert_winners",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_stage_observation_corrections",
            static_sql=_SQL_S12_INSERT_WINNERS,
        )
        add(
            "corrections.insert_rivals",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_stage_observation_corrections",
            static_sql=_SQL_S12_INSERT_RIVALS,
        )
        add(
            "corrections.summary",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CM + "_stage_observation_corrections",
            static_sql=_SQL_S12_SUMMARY,
        )
    elif kind == _KIND_OBSERVATION_LOAD:
        add(
            "load_accession_observations.insert",
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_successor_load_accession_observations",
        )
        count("census_accession_observations")
    elif kind == _KIND_EDGES:
        add(
            _OP_CANDIDATE_EDGES_SELECT,
            mode=dynamic,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CENSUS + "_candidate_edges",
            prefix=_PREFIX_CANDIDATE_EDGES_SELECT,
            expected=2,
        )
        add(
            _OP_MARK_CONFLICTS,
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CENSUS + "_mark_accession_conflicts",
            prefix=_PREFIX_MARK_CONFLICTS,
        )
        count("census_candidate_lineage_edges")
    elif kind == _KIND_PARSER_STATE:
        add(
            "parser_state.update",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_stage_parser_state",
            static_sql=_SQL_S15P_UPDATE,
        )
    elif kind == _KIND_INDEX_REBUILD:
        add(
            "index_rebuild.create",
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CM + "_stage_index_rebuild",
        )
    elif kind in {_KIND_COUNTER_CATALOG, _KIND_COUNTER_LEDGER}:
        batch = int(cast("int", stage.batch))
        size = min(MERGE_FAN_IN, counter_source_count - batch * MERGE_FAN_IN)
        if kind == _KIND_COUNTER_CATALOG:
            add(
                "counter_catalog.insert",
                mode=dynamic,
                kind=STATEMENT_KIND_EXECUTE,
                source=_CM + "_stage_counter_catalog_batch",
                expected=size,
            )
            count(L2_PLAN_WITNESS_TABLE)
        else:
            add(
                "counter_ledger.insert",
                mode=dynamic,
                kind=STATEMENT_KIND_EXECUTE,
                source=_CM + "_stage_counter_ledger_batch",
                expected=size,
            )
            count(L2_PLAN_LEDGER_TABLE)
    elif kind == _KIND_COUNTERS_FINALIZE:
        count(L2_PLAN_WITNESS_RANK_TABLE, 2)
        count(L2_MEMBER_DELTA_TABLE)
        source = _CM + "_stage_counters_finalize"
        add(
            "counters.insert_rank",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=source,
            static_sql=_SQL_S17C_INSERT_RANK,
        )
        add(
            "counters.orphaned_winners",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_ORPHANED_WINNERS,
        )
        add(
            "counters.orphaned_rivals",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_ORPHANED_RIVALS,
        )
        add(
            "counters.contested",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_CONTESTED,
        )
        add(
            "counters.winner_rows",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_WINNER_ROWS,
        )
        add(
            "counters.rival_rows",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_RIVAL_ROWS,
        )
        add(
            "counters.insert_member_delta",
            mode=static,
            kind=STATEMENT_KIND_EXECUTE,
            source=source,
            static_sql=_SQL_S17C_INSERT_MEMBER_DELTA,
        )
        add(
            "counters.deltas",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=source,
            static_sql=_SQL_S17C_DELTAS,
        )
    elif kind == _KIND_SIDECAR:
        sidecar = _ROLE_COMPACT_EVIDENCE
        add(
            _OP_PATH_DECISION,
            mode=_MODE_CALLABLE_NON_SQL,
            kind=_KIND_PATH_DECISION,
            source=_CM + "_prepare_sidecar",
            role=sidecar,
            phase=_PHASE_PREPARE,
        )
        add(
            "member_deltas.create_temp",
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CC + "_member_deltas",
            role=sidecar,
            path=_S18_PATH_BUILD,
            phase=_PHASE_PREPARE,
        )
        add(
            "member_deltas.summary",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CC + "_member_deltas",
            role=sidecar,
            static_sql=MEMBER_DELTA_SUMMARY_SQL,
            path=_S18_PATH_BUILD,
            phase=_PHASE_PREPARE,
        )
        add(
            "merge_sidecar.insert_members",
            mode=dynamic,
            kind=STATEMENT_KIND_EXECUTE,
            source=_CC + "_merge_sidecar",
            role=sidecar,
            path=_S18_PATH_BUILD,
            phase=_PHASE_PREPARE,
        )
        add(
            "merge_sidecar.summary",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CC + "_merge_sidecar",
            role=sidecar,
            static_sql=SIDECAR_MEMBER_SUMMARY_SQL,
            path=_S18_PATH_BUILD,
            phase=_PHASE_PREPARE,
        )
        add(
            "merge_sidecar.digest_replay",
            mode=static,
            kind=STATEMENT_KIND_ITERATE,
            source=_CC + "_merge_sidecar",
            role=sidecar,
            static_sql=SIDECAR_DIGEST_REPLAY_SQL,
            path=_S18_PATH_BUILD,
            phase=_PHASE_PREPARE,
        )
        add(
            "sidecar.member_manifest_rows",
            mode=static,
            kind=STATEMENT_KIND_FETCHALL,
            source=_CE + "member_manifest_digest",
            role=sidecar,
            static_sql=MEMBER_MANIFEST_ROWS_SQL,
            phase=_PHASE_PREPARE,
        )
        for table, sql in IDENTITY_FOLD_STATEMENTS:
            add(
                f"sidecar.identity_fold:{table}",
                mode=static,
                kind=STATEMENT_KIND_FETCHALL,
                source=_CE + "identity",
                role=sidecar,
                static_sql=sql,
                phase=_PHASE_PREPARE,
            )
    elif kind == _KIND_REAUTHENTICATE:
        add(
            _OP_REAUTHENTICATE,
            mode=_MODE_CALLABLE_NON_SQL,
            kind=_KIND_CALLABLE,
            source=_CM + "_prepare_reauthentication",
            role=_ROLE_INTERMEDIATES,
            phase=_PHASE_PREPARE,
        )
    elif kind in {_KIND_FINAL_RECEIPT, _KIND_CALIBRATION_RESULT}:
        add(
            _OP_TABLE_ROW_COUNTS,
            mode=dynamic,
            kind=STATEMENT_KIND_FETCHALL,
            source="disclosure_drift.m3.chunk_execution.table_row_counts",
            prefix=_PREFIX_TABLE_ROW_COUNTS,
            expected=len(F0_WRITTEN_TABLES),
        )
        add(
            _OP_BUILD_MANIFEST,
            mode=_MODE_CALLABLE_NON_SQL,
            kind=_KIND_CALLABLE,
            source=_CM + "_finish_terminal",
            role=_ROLE_WORLD,
            phase=_PHASE_POST_COMMIT,
        )
    return tuple(items)


def successor_statement_registry(
    route: str, counter_source_count: int
) -> tuple[Mapping[str, object], ...]:
    """The exact ordered registry of every material operation of one route -- §20, §21."""
    records: list[Mapping[str, object]] = []
    for stage in successor_stage_graph(route, counter_source_count):
        records.extend(
            item.as_record() for item in _declared_operations(stage, counter_source_count)
        )
    return tuple(records)


def _registry_identity(
    route: str, counter_source_count: int, registry: Sequence[Mapping[str, object]]
) -> str:
    return _identity_of(
        {
            "contract": L2_STATEMENT_REGISTRY_CONTRACT,
            "route": route,
            "counter_source_count": counter_source_count,
            "descriptors": [dict(item) for item in registry],
        }
    )


def registry_counts(registry: Sequence[Mapping[str, object]]) -> Mapping[str, int]:
    """The four counts §21 asks for, over one registry."""
    modes = [str(item["sql_identity_mode"]) for item in registry]
    return {
        "MATERIAL_OPERATION_COUNT": len(registry),
        "MATERIAL_SQL_STATEMENT_COUNT": sum(1 for mode in modes if mode in _SQL_MODES),
        "STATIC_SQL_DESCRIPTOR_COUNT": modes.count(_MODE_STATIC_SQL),
        "DYNAMIC_SQL_CAPTURE_DESCRIPTOR_COUNT": modes.count(_MODE_DYNAMIC_SQL_CAPTURE),
        "CALLABLE_NON_SQL_DESCRIPTOR_COUNT": modes.count(_MODE_CALLABLE_NON_SQL),
    }


# --------------------------------------------------------------------------- #
# The successor StagePlan -- §18 (/2 since D151-C31R2-R19B-C2 §19)
# --------------------------------------------------------------------------- #
_STAGE_PLAN_V2_FIELDS: Final[tuple[str, ...]] = (
    "statement_registry",
    "statement_registry_identity",
    "statement_progress_root",
    "statement_progress_interval_seconds",
    "progress_handler_vm_steps",
    "wal_watchdog_max_uncommitted_frames",
    "wal_watchdog_storage_ceiling_bytes",
    "expected_page_size_bytes",
)


def _require_watchdog_within_ceiling(terms: StatementObservabilityTerms, ceiling: int) -> None:
    """``frames x (page_size + 24) <= wal_watchdog_storage_ceiling_bytes`` -- §26, §36."""
    _require(
        terms.derived_watchdog_bytes <= ceiling,
        f"wal_watchdog_max_uncommitted_frames = {terms.wal_watchdog_max_uncommitted_frames} at "
        f"page size {terms.expected_page_size_bytes} derives {terms.derived_watchdog_bytes} "
        f"bytes, above the Level-Two transient ceiling of {ceiling} bytes; refused",
    )


def _require_stage_plan_v2_fields(body: Mapping[str, object]) -> None:
    """Every /2 field present, exact, and consistent with the body it sits in."""
    missing = [name for name in _STAGE_PLAN_V2_FIELDS if name not in body]
    _require(not missing, f"a /2 StagePlan lacks {missing}; refused")
    terms = require_statement_observability_terms(
        {name: body[name] for name in _OBSERVABILITY_TERM_KEYS}
    )
    ceiling = _exact_int(
        body["wal_watchdog_storage_ceiling_bytes"],
        "wal_watchdog_storage_ceiling_bytes",
        (1, 1 << 62),
    )
    _require_watchdog_within_ceiling(terms, ceiling)
    root = Path(str(body["statement_progress_root"]))
    expected_root = Path(str(body["stage_receipt_root"])) / STATEMENT_PROGRESS_DIRECTORY
    _require(
        root == expected_root and ".." not in root.parts and root.is_absolute(),
        f"statement_progress_root must be exactly {expected_root.name!r} beneath the stage "
        "receipt root, with no traversal component; refused",
    )
    registry = body["statement_registry"]
    _require(isinstance(registry, list) and bool(registry), "a /2 StagePlan binds a registry")
    records = cast("list[Mapping[str, object]]", registry)
    route = str(body["route"])
    count = _stored_int(body["counter_source_count"], "counter_source_count")
    _require(
        [dict(item) for item in records]
        == [dict(item) for item in successor_statement_registry(route, count)]
        and str(body["statement_registry_identity"]) == _registry_identity(route, count, records),
        "a /2 StagePlan's statement registry is not the one this build derives for its route "
        "and chunk count, or its identity does not describe it; refused",
    )


@dataclass(frozen=True, slots=True)
class L2StagePlan:
    """The generic, variable-count successor StagePlan: its canonical body and its identity.

    Every field §18 names is inside ``body``; ``identity`` is the SHA-256 over the canonical
    bytes of the body with the identity field removed, and a reader always recomputes it. The
    body is a pure function of durable inputs -- receipts, manifests, requests, plan, schedule,
    repository, implementation bytes, storage terms, cache budget and paths -- so an expected
    plan built fresh in a later process equals the stored one exactly, or the stage conflicts.
    """

    body: Mapping[str, object]
    identity: str

    @property
    def route(self) -> str:
        """The route this plan was sealed for."""
        return str(self.body["route"])

    @property
    def successor_run_id(self) -> str:
        """The successor run this plan belongs to."""
        return str(self.body["successor_run_id"])

    @property
    def canonical_world_path(self) -> str:
        """The exact canonical successor-world path."""
        return str(self.body["canonical_world_path"])

    @property
    def cache_bytes(self) -> int:
        """The required page-cache budget."""
        return require_successor_cache_bytes(self.body["cache_bytes"])

    @property
    def tool_manifest_identity(self) -> str:
        """The bound implementation identity, recomputed at every admission."""
        return str(self.body["tool_manifest_identity"])

    @property
    def contract(self) -> str:
        """The contract this plan was sealed under: ``/1`` (historical) or ``/2``."""
        return str(self.body["contract"])

    @property
    def executable(self) -> bool:
        """Only a ``/2`` plan is executable; a ``/1`` plan is readable for forensics only."""
        return self.contract == L2_STAGE_PLAN_CONTRACT_V2

    @property
    def observability_terms(self) -> StatementObservabilityTerms:
        """The four bound observability terms (``/2`` only)."""
        _require(self.executable, "a /1 StagePlan carries no observability terms")
        return require_statement_observability_terms(
            {name: self.body[name] for name in _OBSERVABILITY_TERM_KEYS}
        )

    @property
    def wal_watchdog_storage_ceiling_bytes(self) -> int:
        """The per-active-transaction WAL storage ceiling (``/2`` only)."""
        _require(self.executable, "a /1 StagePlan carries no watchdog ceiling")
        return _exact_int(
            self.body["wal_watchdog_storage_ceiling_bytes"],
            "wal_watchdog_storage_ceiling_bytes",
            (1, 1 << 62),
        )

    @property
    def statement_progress_root(self) -> Path:
        """Where this plan's statement journals live (``/2`` only)."""
        _require(self.executable, "a /1 StagePlan carries no statement progress root")
        return Path(str(self.body["statement_progress_root"]))

    @property
    def statement_registry(self) -> tuple[Mapping[str, object], ...]:
        """The bound operation registry (``/2`` only)."""
        _require(self.executable, "a /1 StagePlan carries no statement registry")
        return tuple(
            cast("Mapping[str, object]", item)
            for item in cast("list[object]", self.body["statement_registry"])
        )

    @property
    def statement_registry_identity(self) -> str:
        """The bound registry identity (``/2`` only)."""
        _require(self.executable, "a /1 StagePlan carries no statement registry")
        return str(self.body["statement_registry_identity"])

    @property
    def stages(self) -> tuple[L2Stage, ...]:
        """The exact ordered stage graph."""
        graph = self.body["stage_graph"]
        return tuple(
            L2Stage.from_record(cast("Mapping[str, object]", item))
            for item in cast("list[object]", graph)
        )

    @property
    def intermediates(self) -> tuple[Mapping[str, object], ...]:
        """Every intermediate descriptor, in schedule order."""
        return tuple(
            cast("Mapping[str, object]", item)
            for item in cast("list[object]", self.body["intermediates"])
        )

    def as_record(self) -> Mapping[str, object]:
        """The persisted rendering: the body plus its identity."""
        record = dict(self.body)
        record["stage_plan_identity"] = self.identity
        return record

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> L2StagePlan:
        """Rebuild a StagePlan from its stored mapping and recompute its identity.

        Raises:
            ChunkMultipassError: the contract, route or identity refuse, or a required field is
                absent or malformed.
        """
        body = {str(key): value for key, value in record.items() if key != "stage_plan_identity"}
        recorded = record.get("stage_plan_identity")
        plan = cls(body=body, identity=_identity_of(body))
        _require(
            str(body.get("contract")) in {L2_STAGE_PLAN_CONTRACT, L2_STAGE_PLAN_CONTRACT_V2},
            f"a successor StagePlan carrying contract {body.get('contract')!r} is refused",
        )
        _require(plan.route in SUCCESSOR_ROUTES, f"a StagePlan names route {plan.route!r}; refused")
        _require(
            recorded is None or str(recorded) == plan.identity,
            "a successor StagePlan's recorded identity does not describe its own body: recorded "
            f"{recorded!r}, recomputed {plan.identity!r}",
        )
        require_successor_cache_bytes(body.get("cache_bytes"))
        count = _stored_int(body["input_group_count"], "input_group_count")
        _require(
            count == len(plan.intermediates)
            and count
            == _stored_int(
                body["predecessor_completed_group_count"], "predecessor_completed_group_count"
            ),
            "a successor StagePlan's input_group_count must equal both its descriptor count and "
            "the predecessor's completed group count; refused",
        )
        _require(
            tuple(stage.ordinal for stage in plan.stages) == tuple(range(len(plan.stages))),
            "a successor StagePlan's stage graph is not contiguous from ordinal 0; refused",
        )
        if plan.executable:
            _require_stage_plan_v2_fields(body)
        return plan


def _build_successor_stage_plan(
    *,
    request: SuccessorFinalRequest,
    plan: ChunkPlan,
    schedule: MergeSchedule,
    intermediates: Sequence[IntermediateInput],
    counter_source_count: int,
    counter_source_identities: Sequence[str],
    repository: RepositoryIdentity,
    contract: ExecutionContract,
    state: _AcceptedPlanState,
    seed_catalog_sha256: str,
    seed_catalog_bytes: int,
    tool_manifest: ToolManifest,
    expected_index_records: Sequence[tuple[int, str, str, str]],
    requirements: MultipassStorageRequirements,
    binding: SqliteTempBinding,
) -> L2StagePlan:
    """Build the expected StagePlan from authenticated inputs -- the StagePlan inventory builder.

    Uses the accepted intermediate resolution (already applied by the caller), the accepted
    manifest verifier (applied inside that resolution),
    :func:`_governed_intermediate_manifest_entries`
    for membership and :func:`_selected_group_request_provenance` for the selected request. It
    never enumerates a directory to decide membership.
    """
    descriptors = [_successor_intermediate_descriptor(item) for item in intermediates]
    index_set = [
        {"ordinal": ordinal, "name": name, "table": table, "sql": sql}
        for ordinal, name, table, sql in expected_index_records
    ]
    world = Path(request.world_directory)
    terms = request.observability_terms
    ceiling = requirements.transient_for(MERGE_LEVEL_TWO)
    _require(
        type(ceiling) is int and ceiling > 0,
        "a /2 StagePlan derives its WAL watchdog storage ceiling from the Level-Two transient "
        f"allowance, which must be a positive integer; the requirement carries {ceiling!r}",
    )
    _require_watchdog_within_ceiling(terms, ceiling)
    registry = successor_statement_registry(request.route, counter_source_count)
    body: dict[str, object] = {
        "contract": L2_STAGE_PLAN_CONTRACT_V2,
        "route": request.route,
        "successor_run_id": request.run_id,
        "predecessor_run_id": request.predecessor_run_id,
        "predecessor_checkpoint_count": request.predecessor_checkpoint_count,
        "predecessor_tip_ordinal": request.predecessor_tip_ordinal,
        "predecessor_tip_identity": request.predecessor_tip_identity,
        "predecessor_completed_group_count": request.predecessor_completed_group_count,
        "input_group_count": len(descriptors),
        "intermediates": descriptors,
        "governed_input_bytes": sum(
            int(cast("int", item["governed_bytes"])) for item in descriptors
        ),
        "counter_source_count": counter_source_count,
        "counter_source_identities": list(counter_source_identities),
        "plan_digest": plan.plan_digest,
        "schedule_digest": schedule.schedule_digest,
        "source_instance_id": plan.source_instance_id,
        "source_observation_id": plan.source_observation_id,
        "source_sha256": plan.source_sha256,
        "source_byte_length": plan.source_byte_length,
        "member_order_digest": plan.member_order_digest,
        "repository_head_sha": repository.head_sha,
        "repository_tree_sha": repository.tree_sha,
        "tool_manifest": dict(tool_manifest.as_record()),
        "tool_manifest_identity": tool_manifest.identity,
        "source_file_digests": dict(tool_manifest.source_file_digests()),
        "stage_graph": [
            dict(stage.as_record())
            for stage in successor_stage_graph(request.route, counter_source_count)
        ],
        "expected_deferred_index_names": list(EXPECTED_DEFERRED_INDEX_NAMES),
        "expected_deferred_index_count": len(EXPECTED_DEFERRED_INDEX_NAMES),
        "expected_deferred_index_set": index_set,
        "expected_deferred_index_set_identity": _identity_of(
            {"contract": L2_DEFERRED_INDEX_SET_CONTRACT, "indexes": index_set}
        ),
        "internal_relation_names": list(L2_CONTROL_TABLES + L2_PERSISTENT_RELATIONS),
        "cache_bytes": request.cache_bytes,
        "statement_registry": [dict(item) for item in registry],
        "statement_registry_identity": _registry_identity(
            request.route, counter_source_count, registry
        ),
        "statement_progress_root": str(
            Path(request.stage_receipt_root) / STATEMENT_PROGRESS_DIRECTORY
        ),
        **dict(terms.as_record()),
        "wal_watchdog_storage_ceiling_bytes": ceiling,
        "stage_receipt_root": str(Path(request.stage_receipt_root)),
        "canonical_world_path": str(world),
        "initialization_attempt_parent": str(world.parent),
        "storage_requirements": dict(requirements.as_record()),
        "storage_requirement_identity": _identity_of(
            {"level": MERGE_LEVEL_TWO, "requirements": dict(requirements.as_record())}
        ),
        "sqlite_temp_binding_identity": stable_binding_identity(binding),
        "semantic_policy_identities": {
            "execution_contract_identity": contract.contract_identity,
            "seed_catalog_sha256": seed_catalog_sha256,
            "seed_catalog_byte_length": seed_catalog_bytes,
            "catalog_source_sha256": contract.catalog_source_sha256,
            "migration_head": contract.migration_head,
            "accepted_plan_state": {
                "plan_position": state.plan_position,
                "plan_source_count": state.plan_source_count,
                "parser_state_before": state.parser_state_before,
                "disposition": state.disposition,
                "plan_fingerprint": state.plan_fingerprint,
                "observation_id": state.observation_id,
                "artifact_sha256": state.artifact_sha256,
                "artifact_byte_length": state.artifact_byte_length,
            },
        },
    }
    return L2StagePlan.from_record(body)


# --------------------------------------------------------------------------- #
# Route proofs -- §15: the private engine runs only under a process-local proof
# --------------------------------------------------------------------------- #
#: A per-process nonce every route proof carries. Minted at import, never persisted, never
#: derivable from a request, a StagePlan, an envelope or a Boolean: a proof constructed
#: elsewhere -- another process, a stored record, a hand-built object -- does not carry it.
_ROUTE_PROOF_NONCE: Final = os.urandom(16).hex()


@dataclass(frozen=True, slots=True)
class _SuccessorRouteProof:
    """Process-local evidence that a route gate was passed in THIS process, and by which gate.

    The wrapper that passed the gate mints it; the private engine requires it and re-invokes
    the bound gate at every stage's STEP 0, so a route whose authority was withdrawn between
    stages refuses at the next one. It is not durable, not serializable and not authority: the
    gate function it binds is.
    """

    route: str
    pid: int
    nonce: str
    gate_name: str
    gate: Callable[[], object]
    envelope: CalibrationChildEnvelope | None
    plan_digest: str | None

    def require_live(self, route: str) -> None:
        """Re-run this proof's gate, in this process, for exactly ``route``.

        Raises:
            ChunkMultipassError: the proof is for another route, another process or was not
                minted here; or the bound gate refuses.
        """
        if self.route != route:
            message = (
                f"a {self.route!r} route proof was handed to the {route!r} successor route; a "
                "proof never crosses routes and the engine refuses before anything is read"
            )
            raise ChunkMultipassError(message)
        if self.pid != os.getpid() or self.nonce != _ROUTE_PROOF_NONCE:
            message = (
                "a successor route proof is process-local: this one was not minted by a route "
                "gate in this process and is refused"
            )
            raise ChunkMultipassError(message)
        self.gate()


def _require_route_proof(proof: object, route: str) -> _SuccessorRouteProof:
    """The engine's gate: an exact proof object for exactly this route, or a refusal.

    Refuses a missing proof, a Boolean, an envelope, a StagePlan, a request or any other
    object standing in for one -- none of them is a gate that was passed in this process.

    Raises:
        ChunkMultipassError: the object is not a live route proof for ``route``.
    """
    if not isinstance(proof, _SuccessorRouteProof):
        message = (
            f"the successor engine requires a process-local route proof; got "
            f"{type(proof).__name__}. A Boolean, an envelope, a StagePlan, a request or a "
            "persisted record is never authority, and the engine refuses before anything is read"
        )
        raise ChunkMultipassError(message)
    proof.require_live(route)
    return proof


def _mint_successor_route_proof(
    route: str,
    *,
    gate: Callable[[], object],
    gate_name: str,
    envelope: CalibrationChildEnvelope | None = None,
    plan_digest: str | None = None,
) -> _SuccessorRouteProof:
    """Mint the proof a wrapper hands the engine, AFTER that wrapper passed ``gate`` itself."""
    return _SuccessorRouteProof(
        route=route,
        pid=os.getpid(),
        nonce=_ROUTE_PROOF_NONCE,
        gate_name=gate_name,
        gate=gate,
        envelope=envelope,
        plan_digest=plan_digest,
    )


# --------------------------------------------------------------------------- #
# Connection-state reconstruction -- §21
# --------------------------------------------------------------------------- #
_SQLITE_DETERMINISTIC_FLAG: Final = 0x800

#: The three deterministic correction functions, with the exact arities the statements use.
_CORRECTION_FUNCTION_ARITIES: Final[tuple[tuple[str, int], ...]] = (
    (_FUNCTION_STABLE_ID, 5),
    (_FUNCTION_RIVAL_FIELDS, 1),
    (_FUNCTION_RECONSTRUCTED_FIELDS, 6),
)


@dataclass(frozen=True, slots=True)
class SuccessorConnectionState:
    """What one successor connection was verified to hold, sealed as one identity."""

    body: Mapping[str, object]
    identity: str

    def as_record(self) -> Mapping[str, object]:
        """The persisted rendering."""
        record = dict(self.body)
        record["connection_state_identity"] = self.identity
        return record


def _establish_successor_connection_state(
    connection: sqlite3.Connection,
    expected_stage_plan: L2StagePlan,
    route_proof: _SuccessorRouteProof,
) -> SuccessorConnectionState:
    """Establish and verify every connection-scoped fact a successor stage relies on -- §21.

    Called immediately after every successor writer connection is created or reopened, before
    any semantic SQL, ATTACH, stage classification or derivation. Nothing is inherited from a
    previous connection: the row factory, ``foreign_keys``, the exact cache pragma derived from
    the StagePlan's budget and the three deterministic correction functions are established
    here and then READ BACK from SQLite -- ``PRAGMA function_list`` reports each function's
    name, arity and deterministic flag -- and the implementation files are re-hashed from disk
    and held to the StagePlan's tool identity. The whole is sealed as ``connection_state_identity``,
    which every applied-unit row and stage receipt binds.

    Raises:
        ChunkMultipassError: the route proof is not live, or any fact cannot be established
            exactly.
    """
    _require_route_proof(route_proof, expected_stage_plan.route)
    connection.row_factory = sqlite3.Row
    probe = connection.execute("SELECT 1 AS one").fetchone()
    _require(isinstance(probe, sqlite3.Row), "the successor connection's row factory is not Row")
    connection.execute("PRAGMA foreign_keys = ON")
    foreign_keys = int(connection.execute("PRAGMA foreign_keys").fetchone()[0])
    _require(foreign_keys == 1, f"PRAGMA foreign_keys reads {foreign_keys} where 1 is required")
    cache_bytes = expected_stage_plan.cache_bytes
    expected_pragma = cache_size_pragma(cache_bytes)
    connection.execute(f"PRAGMA cache_size = {expected_pragma}")
    observed_pragma = int(connection.execute("PRAGMA main.cache_size").fetchone()[0])
    _require(
        observed_pragma == expected_pragma,
        f"PRAGMA cache_size reads {observed_pragma} where the StagePlan's {cache_bytes} bytes "
        f"require {expected_pragma}",
    )
    page_size = int(connection.execute("PRAGMA main.page_size").fetchone()[0])
    expected_page_size = expected_stage_plan.observability_terms.expected_page_size_bytes
    _require(
        page_size == expected_page_size,
        f"PRAGMA page_size reads {page_size} where the StagePlan expects "
        f"{expected_page_size}; the WAL frame boundary cannot be derived and the world is refused",
    )
    _register_correction_functions(connection)
    registered = {
        str(row["name"]): (int(row["narg"]), int(row["flags"]))
        for row in connection.execute("PRAGMA function_list")
        if int(row["builtin"]) == 0
        and str(row["name"]) in {name for name, _arity in _CORRECTION_FUNCTION_ARITIES}
    }
    functions: list[Mapping[str, object]] = []
    for name, arity in _CORRECTION_FUNCTION_ARITIES:
        found = registered.get(name)
        _require(
            found is not None,
            f"correction function {name!r} is not registered on this connection; refused",
        )
        assert found is not None  # noqa: S101 - narrowed by the refusal above
        narg, flags = found
        deterministic = bool(flags & _SQLITE_DETERMINISTIC_FLAG)
        _require(
            narg == arity and deterministic,
            f"correction function {name!r} is registered with arity {narg} and deterministic="
            f"{deterministic} where arity {arity} and deterministic=True are required",
        )
        functions.append({"name": name, "arity": arity, "deterministic": True})
    tool_manifest = _require_runtime_tool_identity(
        expected_stage_plan.tool_manifest_identity, label="connection state"
    )
    body: dict[str, object] = {
        "contract": L2_CONNECTION_STATE_CONTRACT,
        "route": expected_stage_plan.route,
        "stage_plan_identity": expected_stage_plan.identity,
        "row_factory": "sqlite3.Row",
        "foreign_keys": foreign_keys,
        "cache_bytes": cache_bytes,
        "cache_size_pragma": observed_pragma,
        "page_size_bytes": page_size,
        "functions": functions,
        "tool_manifest_identity": tool_manifest.identity,
        "source_file_digests": dict(tool_manifest.source_file_digests()),
        "setup_complete": True,
    }
    return SuccessorConnectionState(body=body, identity=_identity_of(body))


# --------------------------------------------------------------------------- #
# The successor control schema -- §24, §25
# --------------------------------------------------------------------------- #
_L2_CONTROL_SCHEMA: Final = f"""
CREATE TABLE {L2_STAGE_PLAN_TABLE} (
    singleton             INTEGER PRIMARY KEY CHECK (singleton = 1),
    contract              TEXT NOT NULL,
    successor_run_id      TEXT NOT NULL,
    route                 TEXT NOT NULL,
    canonical_world_path  TEXT NOT NULL,
    stage_plan_identity   TEXT NOT NULL,
    body_json             TEXT NOT NULL
) STRICT;

CREATE TABLE {L2_APPLIED_UNITS_TABLE} (
    stage_ordinal                       INTEGER PRIMARY KEY,
    stage_id                            TEXT NOT NULL UNIQUE,
    unit_id                             TEXT NOT NULL,
    unit_kind                           TEXT NOT NULL,
    contract                            TEXT NOT NULL,
    route                               TEXT NOT NULL,
    successor_run_id                    TEXT NOT NULL,
    stage_plan_identity                 TEXT NOT NULL,
    predecessor_unit_identity           TEXT NOT NULL,
    input_identities_json               TEXT NOT NULL,
    receipt_identities_json             TEXT NOT NULL,
    request_provenance_identities_json  TEXT NOT NULL,
    repository_head_sha                 TEXT NOT NULL,
    repository_tree_sha                 TEXT NOT NULL,
    tool_manifest_identity              TEXT NOT NULL,
    connection_state_identity           TEXT NOT NULL,
    source_file_digests_json            TEXT NOT NULL,
    stage_operation_identity            TEXT NOT NULL,
    rows_written                        INTEGER NOT NULL CHECK (rows_written >= 0),
    outcome_witness_json                TEXT NOT NULL,
    committed_at_utc                    TEXT NOT NULL,
    statement_registry_identity         TEXT NOT NULL,
    statement_execution_set_identity    TEXT NOT NULL,
    statement_execution_set_json        TEXT NOT NULL,
    unit_identity                       TEXT NOT NULL UNIQUE,
    UNIQUE (stage_id, unit_id)
) STRICT;

CREATE TABLE {L2_CROSS_STORE_BINDINGS_TABLE} (
    stage_ordinal        INTEGER PRIMARY KEY,
    binding_kind         TEXT NOT NULL,
    contract             TEXT NOT NULL,
    target_name          TEXT NOT NULL,
    target_byte_length   INTEGER,
    target_sha256        TEXT,
    target_identity      TEXT NOT NULL,
    body_json            TEXT NOT NULL,
    binding_identity     TEXT NOT NULL UNIQUE
) STRICT;

CREATE TABLE {L2_DEFERRED_INDEXES_TABLE} (
    ordinal       INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    table_name    TEXT NOT NULL,
    create_sql    TEXT NOT NULL,
    set_identity  TEXT NOT NULL
) STRICT;

CREATE TABLE {L2_WITNESS_RANK_TABLE} (
    accession_plain        TEXT NOT NULL,
    source_observation_id  TEXT NOT NULL,
    parsed_record_id       TEXT NOT NULL,
    first_observed_at_utc  TEXT NOT NULL,
    chunk_ordinal          INTEGER NOT NULL,
    witness_rank           INTEGER NOT NULL,
    witnesses              INTEGER NOT NULL
);

CREATE TABLE {L2_CORRECTIONS_TABLE} (
    accession_observation_id  TEXT,
    accession_plain           TEXT,
    source_observation_id     TEXT,
    parsed_record_id          TEXT,
    field_name                TEXT,
    raw_value_json            TEXT,
    observed_at_utc           TEXT,
    conflict_indicator        INTEGER
);

CREATE TABLE {L2_PLAN_WITNESS_TABLE} (
    accession_plain    TEXT NOT NULL,
    parsed_record_id   TEXT NOT NULL,
    chunk_ordinal      INTEGER NOT NULL
);

CREATE TABLE {L2_PLAN_LEDGER_TABLE} (
    native_identity     TEXT NOT NULL,
    member_ordinal      INTEGER NOT NULL,
    record_ordinal      INTEGER NOT NULL,
    delta_materialized  INTEGER NOT NULL
);

CREATE TABLE {L2_PLAN_WITNESS_RANK_TABLE} (
    accession_plain    TEXT NOT NULL,
    parsed_record_id   TEXT NOT NULL,
    witness_rank       INTEGER NOT NULL,
    witnesses          INTEGER NOT NULL
);

CREATE TABLE {L2_MEMBER_DELTA_TABLE} (
    member_ordinal  INTEGER NOT NULL,
    delta           INTEGER NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class AppliedUnit:
    """One committed applied-unit row, read back from the world catalog."""

    stage_ordinal: int
    stage_id: str
    unit_id: str
    unit_kind: str
    stage_plan_identity: str
    predecessor_unit_identity: str
    tool_manifest_identity: str
    connection_state_identity: str
    stage_operation_identity: str
    rows_written: int
    outcome_witness: Mapping[str, object]
    committed_at_utc: str
    unit_identity: str
    body: Mapping[str, object]
    statement_registry_identity: str = ""
    statement_execution_set_identity: str = ""
    statement_execution_set: Mapping[str, object] | None = None

    @property
    def contract(self) -> str:
        """The applied-unit contract this row was committed under."""
        return str(self.body["contract"])

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> AppliedUnit:
        """Rebuild one row and recompute its identity over the body it carries.

        A ``/1`` row (no statement columns) stays readable; a ``/2`` row binds its registry
        and execution-set identities and the execution set itself inside the identity.

        Raises:
            ChunkMultipassError: the stored identity does not describe the row.
        """
        columns = set(row.keys())
        versioned = "statement_execution_set_json" in columns
        body: dict[str, object] = {
            "contract": str(row["contract"]),
            "route": str(row["route"]),
            "successor_run_id": str(row["successor_run_id"]),
            "stage_ordinal": int(row["stage_ordinal"]),
            "stage_id": str(row["stage_id"]),
            "unit_id": str(row["unit_id"]),
            "unit_kind": str(row["unit_kind"]),
            "stage_plan_identity": str(row["stage_plan_identity"]),
            "predecessor_unit_identity": str(row["predecessor_unit_identity"]),
            "input_identities": json.loads(str(row["input_identities_json"])),
            "receipt_identities": json.loads(str(row["receipt_identities_json"])),
            "request_provenance_identities": json.loads(
                str(row["request_provenance_identities_json"])
            ),
            "repository_head_sha": str(row["repository_head_sha"]),
            "repository_tree_sha": str(row["repository_tree_sha"]),
            "tool_manifest_identity": str(row["tool_manifest_identity"]),
            "connection_state_identity": str(row["connection_state_identity"]),
            "source_file_digests": json.loads(str(row["source_file_digests_json"])),
            "stage_operation_identity": str(row["stage_operation_identity"]),
            "rows_written": int(row["rows_written"]),
            "outcome_witness": json.loads(str(row["outcome_witness_json"])),
            "committed_at_utc": str(row["committed_at_utc"]),
        }
        execution_set: Mapping[str, object] | None = None
        if versioned:
            execution_set = _json_object(
                str(row["statement_execution_set_json"]), "statement execution set"
            )
            body["statement_registry_identity"] = str(row["statement_registry_identity"])
            body["statement_execution_set_identity"] = str(row["statement_execution_set_identity"])
            body["statement_execution_set"] = dict(execution_set)
        identity = _identity_of(body)
        expected_contract = L2_APPLIED_UNIT_CONTRACT_V2 if versioned else L2_APPLIED_UNIT_CONTRACT
        _require(
            str(row["unit_identity"]) == identity and str(row["contract"]) == expected_contract,
            f"applied unit {row['stage_id']!r} carries identity {row['unit_identity']!r} where "
            f"its body recomputes to {identity!r}; refused",
        )
        witness = body["outcome_witness"]
        _require(isinstance(witness, Mapping), "an applied unit's outcome witness is not a mapping")
        if versioned:
            _require(
                str(row["statement_execution_set_identity"])
                == str(cast("Mapping[str, object]", execution_set).get("execution_set_identity")),
                f"applied unit {row['stage_id']!r} binds an execution-set identity its own "
                "execution set does not carry; refused",
            )
        return cls(
            stage_ordinal=int(row["stage_ordinal"]),
            stage_id=str(row["stage_id"]),
            unit_id=str(row["unit_id"]),
            unit_kind=str(row["unit_kind"]),
            stage_plan_identity=str(row["stage_plan_identity"]),
            predecessor_unit_identity=str(row["predecessor_unit_identity"]),
            tool_manifest_identity=str(row["tool_manifest_identity"]),
            connection_state_identity=str(row["connection_state_identity"]),
            stage_operation_identity=str(row["stage_operation_identity"]),
            rows_written=int(row["rows_written"]),
            outcome_witness=cast("Mapping[str, object]", witness),
            committed_at_utc=str(row["committed_at_utc"]),
            unit_identity=identity,
            body=body,
            statement_registry_identity=str(body.get("statement_registry_identity", "")),
            statement_execution_set_identity=str(body.get("statement_execution_set_identity", "")),
            statement_execution_set=execution_set,
        )


def _stage_operation_identity(stage_plan: L2StagePlan, stage: L2Stage) -> str:
    """The exact semantic operation one stage performs under one StagePlan, as one identity."""
    return _identity_of(
        {"stage_plan_identity": stage_plan.identity, "stage": dict(stage.as_record())}
    )


def _applied_units(connection: sqlite3.Connection) -> tuple[AppliedUnit, ...]:
    rows = connection.execute(
        f"SELECT * FROM main.{L2_APPLIED_UNITS_TABLE} ORDER BY stage_ordinal"  # noqa: S608
    ).fetchall()
    return tuple(AppliedUnit.from_row(row) for row in rows)


def _insert_applied_unit(
    connection: sqlite3.Connection,
    *,
    stage_plan: L2StagePlan,
    stage: L2Stage,
    predecessor_unit_identity: str,
    input_identities: Sequence[str],
    receipt_identities: Sequence[str],
    request_provenance_identities: Sequence[str],
    connection_state: SuccessorConnectionState,
    rows_written: int,
    outcome_witness: Mapping[str, object],
    execution_set: Mapping[str, object],
) -> AppliedUnit:
    """Insert one applied-unit row INSIDE the caller's open transaction, outside containment.

    The row binds everything §25 names plus (D151-C31R2-R19B-C2 §29) the StagePlan's statement
    registry identity and the stage attempt's statement execution set, and is sealed by
    ``unit_identity``; the table's primary key and uniqueness constraints refuse a duplicate
    ordinal, a duplicate stage and a duplicate unit, and the caller has already held the
    predecessor to the expected identity.

    Raises:
        ChunkMultipassError: the connection is not inside a transaction, or the execution set
            does not carry its own identity.
    """
    _require(
        connection.in_transaction,
        "an applied-unit row is inserted inside the transaction that wrote the stage's data, "
        "never in a transaction of its own",
    )
    execution_set_identity = str(execution_set.get("execution_set_identity", ""))
    _require(
        len(execution_set_identity) == 64
        and str(execution_set.get("contract")) == L2_STATEMENT_EXECUTION_SET_CONTRACT,
        "an applied unit binds a sealed statement execution set carrying its own identity",
    )
    committed_at = utc_now()
    body: dict[str, object] = {
        "contract": L2_APPLIED_UNIT_CONTRACT_V2,
        "route": stage_plan.route,
        "successor_run_id": stage_plan.successor_run_id,
        "stage_ordinal": stage.ordinal,
        "stage_id": stage.stage_id,
        "unit_id": stage.unit_id,
        "unit_kind": stage.kind,
        "stage_plan_identity": stage_plan.identity,
        "predecessor_unit_identity": predecessor_unit_identity,
        "input_identities": list(input_identities),
        "receipt_identities": list(receipt_identities),
        "request_provenance_identities": list(request_provenance_identities),
        "repository_head_sha": str(stage_plan.body["repository_head_sha"]),
        "repository_tree_sha": str(stage_plan.body["repository_tree_sha"]),
        "tool_manifest_identity": str(connection_state.body["tool_manifest_identity"]),
        "connection_state_identity": connection_state.identity,
        "source_file_digests": dict(
            cast("Mapping[str, str]", connection_state.body["source_file_digests"])
        ),
        "stage_operation_identity": _stage_operation_identity(stage_plan, stage),
        "rows_written": rows_written,
        "outcome_witness": dict(outcome_witness),
        "committed_at_utc": committed_at,
        "statement_registry_identity": stage_plan.statement_registry_identity,
        "statement_execution_set_identity": execution_set_identity,
        "statement_execution_set": dict(execution_set),
    }
    identity = _identity_of(body)
    connection.execute(
        f"INSERT INTO main.{L2_APPLIED_UNITS_TABLE} ("  # noqa: S608
        "stage_ordinal, stage_id, unit_id, unit_kind, contract, route, successor_run_id, "
        "stage_plan_identity, predecessor_unit_identity, input_identities_json, "
        "receipt_identities_json, request_provenance_identities_json, repository_head_sha, "
        "repository_tree_sha, tool_manifest_identity, connection_state_identity, "
        "source_file_digests_json, stage_operation_identity, rows_written, "
        "outcome_witness_json, committed_at_utc, statement_registry_identity, "
        "statement_execution_set_identity, statement_execution_set_json, unit_identity) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            stage.ordinal,
            stage.stage_id,
            stage.unit_id,
            stage.kind,
            L2_APPLIED_UNIT_CONTRACT_V2,
            stage_plan.route,
            stage_plan.successor_run_id,
            stage_plan.identity,
            predecessor_unit_identity,
            _json_text(list(input_identities)),
            _json_text(list(receipt_identities)),
            _json_text(list(request_provenance_identities)),
            body["repository_head_sha"],
            body["repository_tree_sha"],
            body["tool_manifest_identity"],
            connection_state.identity,
            _json_text(body["source_file_digests"]),
            body["stage_operation_identity"],
            rows_written,
            _json_text(dict(outcome_witness)),
            committed_at,
            stage_plan.statement_registry_identity,
            execution_set_identity,
            _json_text(dict(execution_set)),
            identity,
        ),
    )
    row = connection.execute(
        f"SELECT * FROM main.{L2_APPLIED_UNITS_TABLE} WHERE stage_ordinal = ?",  # noqa: S608
        (stage.ordinal,),
    ).fetchone()
    return AppliedUnit.from_row(row)


def _insert_cross_store_binding(
    connection: sqlite3.Connection,
    *,
    stage: L2Stage,
    kind: str,
    target_name: str,
    target_byte_length: int | None,
    target_sha256: str | None,
    target_identity: str,
    body: Mapping[str, object],
) -> str:
    """Insert one cross-store binding row inside the open transaction; return its identity."""
    _require(connection.in_transaction, "a cross-store binding is committed with its applied unit")
    record: dict[str, object] = {
        "contract": L2_CROSS_STORE_BINDING_CONTRACT,
        "stage_ordinal": stage.ordinal,
        "binding_kind": kind,
        "target_name": target_name,
        "target_byte_length": target_byte_length,
        "target_sha256": target_sha256,
        "target_identity": target_identity,
        "body": dict(body),
    }
    identity = _identity_of(record)
    connection.execute(
        f"INSERT INTO main.{L2_CROSS_STORE_BINDINGS_TABLE} ("  # noqa: S608
        "stage_ordinal, binding_kind, contract, target_name, target_byte_length, "
        "target_sha256, target_identity, body_json, binding_identity) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            stage.ordinal,
            kind,
            L2_CROSS_STORE_BINDING_CONTRACT,
            target_name,
            target_byte_length,
            target_sha256,
            target_identity,
            _json_text(dict(body)),
            identity,
        ),
    )
    return identity


def _cross_store_binding(
    connection: sqlite3.Connection, stage_ordinal: int
) -> Mapping[str, object] | None:
    row = connection.execute(
        f"SELECT * FROM main.{L2_CROSS_STORE_BINDINGS_TABLE} WHERE stage_ordinal = ?",  # noqa: S608
        (stage_ordinal,),
    ).fetchone()
    if row is None:
        return None
    record: dict[str, object] = {
        "contract": str(row["contract"]),
        "stage_ordinal": int(row["stage_ordinal"]),
        "binding_kind": str(row["binding_kind"]),
        "target_name": str(row["target_name"]),
        "target_byte_length": None
        if row["target_byte_length"] is None
        else int(row["target_byte_length"]),
        "target_sha256": None if row["target_sha256"] is None else str(row["target_sha256"]),
        "target_identity": str(row["target_identity"]),
        "body": _json_object(str(row["body_json"]), "cross-store binding"),
    }
    _require(
        _identity_of(record) == str(row["binding_identity"]),
        f"cross-store binding for stage ordinal {stage_ordinal} does not describe its own body",
    )
    record["binding_identity"] = str(row["binding_identity"])
    return record


# --------------------------------------------------------------------------- #
# Stage receipts -- the immutable external record published after COMMIT and checkpoint
# --------------------------------------------------------------------------- #
def stage_receipt_path(receipt_root: Path, stage: L2Stage) -> Path:
    """Where one stage's receipt lives: create-once, canonical bytes, never rewritten."""
    unit = stage.unit_id.replace("/", "_").replace(".", "_")
    return receipt_root / f"stage-{stage.ordinal:03d}-{stage.stage_id}-{unit}.json"


def read_stage_receipt(path: Path) -> Mapping[str, object]:
    """One stage receipt read from its canonical bytes with its identity recomputed.

    Raises:
        ChunkMultipassError: absent, a link, not canonical, wrong contract, or an identity that
            does not describe the record.
    """
    _require(not path.is_symlink(), f"stage receipt {path.name!r} is a symbolic link; refused")
    _require(path.is_file(), f"no stage receipt exists at {path.name!r}")
    payload = path.read_bytes()
    record = _json_object(payload.decode("utf-8"), f"stage receipt {path.name!r}")
    _require(
        canonical_json_bytes(record) == payload,
        f"stage receipt {path.name!r} is not persisted as its canonical bytes; refused",
    )
    body = {key: value for key, value in record.items() if key != "receipt_identity"}
    _require(
        str(record.get("contract")) in {L2_STAGE_RECEIPT_CONTRACT, L2_STAGE_RECEIPT_CONTRACT_V2}
        and str(record.get("receipt_identity")) == _identity_of(body),
        f"stage receipt {path.name!r} carries contract {record.get('contract')!r} or an "
        "identity that does not describe its body; refused",
    )
    return record


def _publish_stage_receipt(
    *,
    receipt_root: Path,
    stage_plan: L2StagePlan,
    stage: L2Stage,
    unit: AppliedUnit,
    main_state: _FileState,
    normalized_wal: int,
    observability: Mapping[str, object],
    entry_classification: str,
    wal_residue_disposition: Mapping[str, object],
) -> Mapping[str, object]:
    """Publish one stage's immutable receipt and read it back -- §30 steps 15-16 (/2)."""
    body: dict[str, object] = {
        "contract": L2_STAGE_RECEIPT_CONTRACT_V2,
        "route": stage_plan.route,
        "successor_run_id": stage_plan.successor_run_id,
        "stage_ordinal": stage.ordinal,
        "stage_id": stage.stage_id,
        "unit_id": stage.unit_id,
        "unit_kind": stage.kind,
        "stage_plan_identity": stage_plan.identity,
        "unit_identity": unit.unit_identity,
        "predecessor_unit_identity": unit.predecessor_unit_identity,
        "connection_state_identity": unit.connection_state_identity,
        "tool_manifest_identity": unit.tool_manifest_identity,
        "stage_operation_identity": unit.stage_operation_identity,
        "rows_written": unit.rows_written,
        "outcome_witness": dict(unit.outcome_witness),
        "committed_at_utc": unit.committed_at_utc,
        "main_file_sha256": main_state.sha256,
        "main_file_byte_length": main_state.byte_length,
        "main_file_inode": main_state.inode,
        "normalized_wal_bytes": normalized_wal,
        "statement_registry_identity": unit.statement_registry_identity,
        "statement_execution_set_identity": unit.statement_execution_set_identity,
        "statement_execution_set": dict(unit.statement_execution_set or {}),
        "observability_status": str(observability["status"]),
        "observability_gap": dict(observability),
        "entry_classification": entry_classification,
        "wal_residue_disposition": dict(wal_residue_disposition),
        "published_at_utc": utc_now(),
    }
    body["receipt_identity"] = _identity_of(body)
    path = stage_receipt_path(receipt_root, stage)
    try:
        write_once_canonical_json(path, body)
    except ChunkExecutionError as exc:
        message = f"stage receipt {path.name!r} could not be published: {exc}"
        raise ChunkMultipassError(message) from exc
    return read_stage_receipt(path)


# --------------------------------------------------------------------------- #
# File-state snapshots and the mode=ro pre-state probe -- §22, §23
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _FileState:
    """One path's lstat class, inode, byte length and (for a regular file) SHA-256."""

    name: str
    lstat_class: str
    inode: int | None
    byte_length: int | None
    sha256: str | None

    def as_record(self) -> Mapping[str, object]:
        return {
            "name": self.name,
            "lstat_class": self.lstat_class,
            "inode": self.inode,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
        }


def _file_state(path: Path, *, digest: bool = True) -> _FileState:
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return _FileState(path.name, "absent", None, None, None)
    if stat.S_ISLNK(status.st_mode):
        return _FileState(path.name, "symlink", status.st_ino, status.st_size, None)
    if not stat.S_ISREG(status.st_mode):
        return _FileState(path.name, "other", status.st_ino, status.st_size, None)
    sha256 = file_sha256(path)[0] if digest and status.st_size else None
    if digest and not status.st_size:
        sha256 = hashlib.sha256(b"").hexdigest()
    return _FileState(path.name, "file", status.st_ino, status.st_size, sha256)


@dataclass(frozen=True, slots=True)
class _WorldSnapshot:
    """The authoritative pre-state of one world catalog: main, WAL class and SHM (evidence)."""

    main: _FileState
    wal: _FileState
    wal_class: str
    shm: _FileState

    def as_record(self) -> Mapping[str, object]:
        return {
            "main": dict(self.main.as_record()),
            "wal": dict(self.wal.as_record()),
            "wal_class": self.wal_class,
            "shm": dict(self.shm.as_record()),
        }


def _world_snapshot(catalog_path: Path) -> _WorldSnapshot:
    main = _file_state(catalog_path)
    _require(
        main.lstat_class == "file",
        f"the successor world catalog {catalog_path.name!r} is {main.lstat_class}; refused",
    )
    wal = _file_state(catalog_path.with_name(catalog_path.name + "-wal"))
    if wal.lstat_class == "absent":
        wal_class = _WAL_ABSENT
    elif wal.lstat_class == "file" and wal.byte_length == 0:
        wal_class = _WAL_ZERO
    elif wal.lstat_class == "file":
        wal_class = _WAL_NONZERO
    else:
        _stage_conflict(f"the write-ahead log {wal.name!r} is {wal.lstat_class}")
    shm = _file_state(catalog_path.with_name(catalog_path.name + "-shm"))
    return _WorldSnapshot(main=main, wal=wal, wal_class=wal_class, shm=shm)


@dataclass(frozen=True, slots=True)
class _MinimalStagePlanIdentity:
    """What the mode=ro probe may read: the five identifying fields, nothing else."""

    contract: str
    successor_run_id: str
    route: str
    canonical_world_path: str
    stage_plan_identity: str
    snapshot_before: _WorldSnapshot
    snapshot_after: _WorldSnapshot


def _prestate_stage_plan_identity(catalog_path: Path) -> _MinimalStagePlanIdentity:
    """STEP 1-3 of every existing-world stage: snapshot, mode=ro identity read, snapshot.

    The probe is SQLite-logically read-only through the accepted connect helper's
    ``read_only=True`` (URI ``mode=ro``): it observes committed WAL content truthfully and can
    fold nothing into main -- a read-write open would checkpoint a crashed WAL on close before
    the state was classified, and ``immutable=1`` is blind to the WAL. It may create the two
    exact SQLite sidecars beside the catalog (a zero-length ``-wal`` and an ``-shm``), which is
    EXPECTED_MODE_RO_SIDECAR_HOUSEKEEPING and never a conflict; it may not change main, may
    not create a nonzero WAL and may not touch a preexisting nonzero WAL.

    Raises:
        ChunkMultipassError: the world has no StagePlan row, or the probe changed authoritative
            state.
    """
    before = _world_snapshot(catalog_path)
    try:
        with connect(catalog_path, read_only=True) as probe:
            row = probe.execute(
                "SELECT contract, successor_run_id, route, canonical_world_path, "  # noqa: S608
                f"stage_plan_identity FROM main.{L2_STAGE_PLAN_TABLE} WHERE singleton = 1"
            ).fetchone()
    except (sqlite3.Error, DisclosureDriftError) as exc:
        _stage_conflict(
            f"the world catalog {catalog_path.name!r} carries no readable successor StagePlan "
            f"({exc}); an arbitrary, legacy or historical world is never continued by the "
            "successor"
        )
    if row is None:
        _stage_conflict(
            f"the world catalog {catalog_path.name!r} carries no successor StagePlan; an "
            "arbitrary, legacy or historical world is never continued by the successor"
        )
    after = _world_snapshot(catalog_path)
    _require_probe_preserved(before, after)
    return _MinimalStagePlanIdentity(
        contract=str(row["contract"]),
        successor_run_id=str(row["successor_run_id"]),
        route=str(row["route"]),
        canonical_world_path=str(row["canonical_world_path"]),
        stage_plan_identity=str(row["stage_plan_identity"]),
        snapshot_before=before,
        snapshot_after=after,
    )


def _require_probe_preserved(before: _WorldSnapshot, after: _WorldSnapshot) -> None:
    """The exact §22 STEP-3 predicate over the two snapshots around a mode=ro probe."""
    main_same = after.main.lstat_class == "file" and (
        before.main.inode,
        before.main.byte_length,
        before.main.sha256,
    ) == (after.main.inode, after.main.byte_length, after.main.sha256)
    if not main_same:
        message = (
            "the mode=ro pre-state probe changed the world's main file (inode, length or "
            "SHA-256 moved); STOP -- the pre-state mechanism itself is compromised"
        )
        raise ChunkMultipassError(message)
    if before.wal_class == _WAL_NONZERO:
        preserved = after.wal.lstat_class == "file" and (
            before.wal.inode,
            before.wal.byte_length,
            before.wal.sha256,
        ) == (after.wal.inode, after.wal.byte_length, after.wal.sha256)
        if not preserved:
            message = (
                "the mode=ro pre-state probe changed a preexisting nonzero write-ahead log; "
                "STOP -- committed evidence may have been folded before classification"
            )
            raise ChunkMultipassError(message)
    elif before.wal_class == _WAL_ZERO:
        _require(
            after.wal_class in {_WAL_ZERO, _WAL_ABSENT},
            "the mode=ro pre-state probe turned a zero-length write-ahead log into a nonzero one",
        )
    else:
        _require(
            after.wal_class in {_WAL_ABSENT, _WAL_ZERO},
            "the mode=ro pre-state probe created a nonzero write-ahead log; refused",
        )


def _normalized_wal_class(snapshot: _WorldSnapshot) -> int:
    """``WAL_ABSENT == WAL_ZERO == 0`` at a clean boundary; a nonzero WAL is its length."""
    if snapshot.wal_class == _WAL_NONZERO:
        return int(snapshot.wal.byte_length or 0)
    return 0


# --------------------------------------------------------------------------- #
# The bounded world session -- §22 STEP 4-6 and §35, one per stage
# --------------------------------------------------------------------------- #
class _WalPreservationGuard:
    """A ``mode=ro`` handle held across a writer's close so nothing is folded implicitly.

    SQLite checkpoints and deletes a write-ahead log when the LAST connection to a database
    closes. Whenever a session opens over a nonzero log, this guard is opened first and released
    only after the engine has explicitly disposed of the log -- a residue TRUNCATE or the stage
    boundary's own checkpoint. A session that ends without such a disposition (a conflict, an
    abort before classification) therefore leaves the log exactly as it found it: the guard
    outlives the writer's close, and a read-only handle folds nothing when it closes itself.
    """

    __slots__ = ("_connection", "released")

    def __init__(self, catalog_path: Path) -> None:
        self._connection: sqlite3.Connection | None = sqlite3.connect(
            f"{catalog_path.absolute().as_uri()}?mode=ro", uri=True, isolation_level=None
        )
        self._connection.execute("SELECT 1").fetchone()
        self.released = False

    def release(self) -> None:
        """The log was explicitly disposed of: the writer's close may now delete an empty log."""
        self.released = True

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None


class _NoGuard:
    """The guard's shape when the pre-state log was absent or zero: nothing to preserve."""

    __slots__ = ("released",)

    def __init__(self) -> None:
        self.released = True

    def release(self) -> None:
        self.released = True

    def close(self) -> None:
        return None


@dataclass(frozen=True, slots=True)
class _WorldSession:
    """One boundedly reopened world: catalog, connection, state and the authenticated plan."""

    world: WorkingCatalog
    connection: sqlite3.Connection
    connection_state: SuccessorConnectionState
    stage_plan: L2StagePlan
    prestate: _MinimalStagePlanIdentity
    guard: _WalPreservationGuard | _NoGuard

    @property
    def catalog_path(self) -> Path:
        return self.world.path


def _read_stored_stage_plan(connection: sqlite3.Connection) -> L2StagePlan:
    row = connection.execute(
        f"SELECT * FROM main.{L2_STAGE_PLAN_TABLE} WHERE singleton = 1"  # noqa: S608
    ).fetchone()
    if row is None:
        _stage_conflict("the world carries no successor StagePlan row")
    plan = L2StagePlan.from_record(_json_object(str(row["body_json"]), "StagePlan body"))
    _require(
        plan.identity == str(row["stage_plan_identity"])
        and plan.route == str(row["route"])
        and plan.successor_run_id == str(row["successor_run_id"])
        and plan.canonical_world_path == str(row["canonical_world_path"])
        and str(row["contract"]) == plan.contract,
        "the stored StagePlan row's identifying columns do not describe its own body; refused",
    )
    return plan


@contextmanager
def _successor_world_session(
    *,
    request: SuccessorFinalRequest,
    expected: L2StagePlan,
    proof: _SuccessorRouteProof,
) -> Iterator[_WorldSession]:
    """STEP 0 through STEP 6 of §22 for an existing canonical world, then the stage.

    Route gate (the live proof) first; then the file snapshot, the mode=ro identity read and
    the post-probe snapshot; then the accepted attach-existing writer reopen; then §21
    connection-state reconstruction; then the complete in-world StagePlan re-read and held to
    the minimal identity, to the expected invocation and to the runtime tool identity. Only a
    session that reached the end of that sequence is handed to a stage.
    """
    proof.require_live(expected.route)
    world_directory = Path(request.world_directory)
    _require(
        not world_directory.is_symlink() and world_directory.is_dir(),
        f"the canonical successor world {world_directory.name!r} is not a regular directory",
    )
    catalog_path = world_directory / WORKING_CATALOG_FILENAME
    prestate = _prestate_stage_plan_identity(catalog_path)
    if prestate.contract == L2_STAGE_PLAN_CONTRACT:
        _stage_conflict(
            "the world carries a historical /1 StagePlan, which is readable for forensics and "
            "is NEVER executed after D151-C31R2-R19B-C2; nothing is converted"
        )
    _require(
        prestate.contract == L2_STAGE_PLAN_CONTRACT_V2
        and prestate.route == expected.route
        and prestate.successor_run_id == expected.successor_run_id
        and prestate.canonical_world_path == expected.canonical_world_path
        and prestate.stage_plan_identity == expected.identity,
        f"{_STAGE_CONFLICT}: the world's minimal StagePlan identity "
        f"({prestate.route!r}, {prestate.successor_run_id!r}, "
        f"{prestate.stage_plan_identity[:16]}...) "
        f"is not the expected invocation ({expected.route!r}, {expected.successor_run_id!r}, "
        f"{expected.identity[:16]}...); nothing is repaired or reinitialized",
    )
    _require(expected.executable, "only a /2 StagePlan opens a world; a /1 plan is read-only")
    guard: _WalPreservationGuard | _NoGuard = (
        _WalPreservationGuard(catalog_path)
        if prestate.snapshot_before.wal_class == _WAL_NONZERO
        else _NoGuard()
    )
    try:
        with WorkingCatalog(
            Path(request.operational_catalog),
            world_directory,
            cache_bytes=require_executable_level_two_cache_bytes(expected.cache_bytes),
            attach=True,
        ) as world:
            connection = world.connection
            connection_state = _establish_successor_connection_state(connection, expected, proof)
            stored = _read_stored_stage_plan(connection)
            if (
                stored.identity != prestate.stage_plan_identity
                or stored.identity != expected.identity
            ):
                _stage_conflict(
                    f"the complete in-world StagePlan recomputes to {stored.identity[:16]}... "
                    f"where the mode=ro read saw {prestate.stage_plan_identity[:16]}... and this "
                    f"invocation expects {expected.identity[:16]}..."
                )
            _require(stored.executable, "the stored StagePlan is not executable")
            yield _WorldSession(
                world=world,
                connection=connection,
                connection_state=connection_state,
                stage_plan=stored,
                prestate=prestate,
                guard=guard,
            )
            if guard.released:
                # An explicit disposition ran: the writer's close may delete an EMPTY log.
                guard.close()
    finally:
        # A session that ends without an explicit disposition keeps the guard across the
        # writer's close, so an unexplained or pending log is never folded implicitly.
        guard.close()


# --------------------------------------------------------------------------- #
# The stage context -- what every stage function is handed
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _StageContext:
    """Every authenticated input a successor stage may consume, resolved once per process."""

    request: SuccessorFinalRequest
    proof: _SuccessorRouteProof
    route: str
    plan: ChunkPlan
    schedule: MergeSchedule
    intermediates: tuple[IntermediateInput, ...]
    counter_sources: tuple[PlanWitnessSource, ...]
    counter_source_identities: tuple[str, ...]
    repository: RepositoryIdentity
    contract: ExecutionContract
    state: _AcceptedPlanState
    seed_catalog_sha256: str
    seed_catalog_bytes: int
    requirements: MultipassStorageRequirements
    binding: SqliteTempBinding
    stage_plan: L2StagePlan
    world_directory: Path
    receipt_root: Path

    @property
    def catalog_path(self) -> Path:
        return self.world_directory / WORKING_CATALOG_FILENAME

    @property
    def stages(self) -> tuple[L2Stage, ...]:
        return self.stage_plan.stages

    def stage_by_id(self, stage_id: str) -> L2Stage:
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        message = f"stage {stage_id!r} is not in this StagePlan's graph"
        raise ChunkMultipassError(message)


def _witness_of(units: Sequence[AppliedUnit], stage_id: str) -> Mapping[str, object]:
    for unit in units:
        if unit.stage_id == stage_id:
            return unit.outcome_witness
    _stage_conflict(f"stage {stage_id!r} has no committed applied unit to read from")


def _reduced_run_from_witness(witness: Mapping[str, object]) -> _ReducedRun:
    return _ReducedRun(
        parser_run_id=str(witness["parser_run_id"]),
        parser_id=str(witness["parser_id"]),
        parser_version=str(witness["parser_version"]),
        outcome=str(witness["outcome"]),
        parsed=_stored_int(witness["parsed"], "parsed"),
        quarantined=_stored_int(witness["quarantined"], "quarantined"),
        parser_state=str(witness["parser_state"]),
        duplicate_identities=_stored_strings(
            witness["duplicate_identities"], "duplicate_identities"
        ),
    )


def _count(connection: sqlite3.Connection, table: str, *, schema: str = "main") -> int:
    row = connection.execute(f"SELECT COUNT(*) AS n FROM {schema}.{table}").fetchone()  # noqa: S608
    return int(row["n"])


def _require_not_derived(units: Sequence[AppliedUnit], stage: L2Stage) -> None:
    """The successor's second-derivation guard: applied-unit state, same refusal text."""
    if any(unit.stage_id == stage.stage_id for unit in units):
        message = (
            f"successor stage {stage.stage_id!r} ({stage.kind}) was {_ALREADY_DERIVED}'s world -- "
            "its applied unit is committed -- and a second derivation is refused rather than "
            "re-derived"
        )
        raise ChunkMultipassError(message)


# --------------------------------------------------------------------------- #
# Statement instrumentation -- D151-C31R2-R19B-C2 §22-§37: journals, sampler, watchdog
# --------------------------------------------------------------------------- #
_ABORT_WATCHDOG: Final = "WATCHDOG_ABORT"
_ABORT_INSTRUMENTATION: Final = "INSTRUMENTATION_FAILURE"
_ABORT_RECORD_CONTRACT: Final = "m3.3-chunked-f0-l2-instrumentation-abort/1"
_STAGE_ID_PATTERN: Final = re.compile(r"^S[0-9]+[A-Z]?(\.[0-9]+)?$")
_ATTEMPT_NAME_PATTERN: Final = re.compile(r"^attempt-([0-9]{3})$")
_ABORT_NAME_PATTERN: Final = re.compile(r"^abort-attempt-[0-9]{3}\.json$")
_JOURNAL_NAME_PATTERN: Final = re.compile(r"^statement-([0-9]{4})\.jsonl$")
_OBSERVABILITY_COMPLETE: Final = "OBSERVABILITY_COMPLETE"
_OBSERVABILITY_GAP_MISSING: Final = "OBSERVABILITY_GAP_MISSING"
_OBSERVABILITY_GAP_CHANGED: Final = "OBSERVABILITY_GAP_CHANGED"
_NANOSECONDS_PER_SECOND: Final = 1_000_000_000

#: The monotonic clock the sampler and the journals read. A module attribute rather than a
#: direct call so a test can drive the sampling interval deterministically; production never
#: rebinds it.
_monotonic_ns: Callable[[], int] = time.monotonic_ns


class _InstrumentationAbortError(ChunkMultipassError):
    """A fail-closed instrumentation or watchdog abort: the statement was interrupted.

    Raised after sqlite3 returned from the interrupted statement, never inside the callback,
    and never for an unrelated ``OperationalError``.
    """

    def __init__(self, cause: str, detail: str) -> None:
        super().__init__(f"{cause}: {detail}")
        self.cause = cause
        self.detail = detail


def _stage_directory_name(stage: L2Stage) -> str:
    """``stage-NNN-<id>`` from validated identifiers only; a ``.`` becomes ``_``."""
    _require(
        bool(_STAGE_ID_PATTERN.match(stage.stage_id)),
        f"stage identifier {stage.stage_id!r} is not a valid successor stage id",
    )
    return f"stage-{stage.ordinal:03d}-{stage.stage_id.replace('.', '_')}"


def _require_real_directory(path: Path, label: str) -> None:
    try:
        status = os.lstat(path)
    except FileNotFoundError as exc:
        message = f"{label} {path.name!r} is absent"
        raise ChunkMultipassError(message) from exc
    _require(stat.S_ISDIR(status.st_mode), f"{label} {path.name!r} is not a real directory")


def _require_progress_root(ctx: _StageContext) -> Path:
    """The one statement-progress root: exactly ``<receipt root>/statement-progress``."""
    root = ctx.stage_plan.statement_progress_root
    expected = ctx.receipt_root / STATEMENT_PROGRESS_DIRECTORY
    _require(
        root == expected and ".." not in root.parts,
        f"the StagePlan's statement progress root is not {expected.name!r} beneath the stage "
        "receipt root; refused",
    )
    _require_real_directory(ctx.receipt_root, "stage receipt root")
    root.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    _require_real_directory(root, "statement progress root")
    return root


def _allocate_stage_attempt(ctx: _StageContext, stage: L2Stage) -> tuple[int, Path]:
    """The next create-once stage-attempt directory: a crashed attempt is never reused."""
    root = _require_progress_root(ctx)
    stage_directory = root / _stage_directory_name(stage)
    stage_directory.mkdir(mode=_DIRECTORY_MODE, exist_ok=True)
    _require_real_directory(stage_directory, "stage progress directory")
    ordinals: list[int] = []
    for name in sorted(entry.name for entry in stage_directory.iterdir()):
        match = _ATTEMPT_NAME_PATTERN.match(name)
        if match is None:
            if _ABORT_NAME_PATTERN.match(name):
                continue
            _stage_conflict(
                f"stage progress directory {stage_directory.name!r} holds an entry {name!r} "
                "this build never writes"
            )
        _require_real_directory(stage_directory / name, "stage attempt")
        ordinals.append(int(match.group(1)))
    ordinal = max(ordinals, default=-1) + 1
    attempt = stage_directory / f"attempt-{ordinal:03d}"
    try:
        attempt.mkdir(mode=_DIRECTORY_MODE)
    except FileExistsError as exc:
        message = f"stage attempt {attempt.name!r} already exists; an attempt is create-once"
        raise ChunkMultipassError(message) from exc
    return ordinal, attempt


def _representable(value: object) -> object:
    """A JSON-carriable rendering of one parameter value, or a refusal marker."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, bytes | bytearray | memoryview):
        return {"bytes_sha256": hashlib.sha256(bytes(value)).hexdigest(), "bytes": len(value)}
    return {"unrepresentable": type(value).__name__}


def _parameter_evidence(parameters: object) -> Mapping[str, object]:
    """Canonical shape and, where bounded, a value digest of one ``execute`` binding -- §23."""
    if isinstance(parameters, Mapping):
        items = [(str(key), value) for key, value in sorted(parameters.items())]
        shape = [[key, type(value).__name__] for key, value in items]
        values: object = {key: _representable(value) for key, value in items}
        count = len(items)
    elif isinstance(parameters, tuple | list):
        shape = [[str(index), type(value).__name__] for index, value in enumerate(parameters)]
        values = [_representable(value) for value in parameters]
        count = len(parameters)
    else:
        return {
            "kind": "unrepresentable",
            "count": None,
            "shape_identity": None,
            "value_sha256": None,
        }
    rendered = cast("Mapping[str, object]", {"values": values})
    return {
        "kind": "bound",
        "count": count,
        "shape_identity": _identity_of({"shape": shape}),
        "value_sha256": _identity_of(rendered),
    }


class _StreamingParameterEvidence:
    """Bounded evidence over an ``executemany`` iterable as sqlite3 consumes it -- §23.

    The exact iterable is forwarded row by row; nothing is buffered, nothing is consumed twice:
    each row's canonical rendering feeds a streaming SHA-256 and its shape is held to the first
    row's. A row a canonical rendering cannot represent marks the digest unrepresentable and the
    count and shape evidence stand alone.
    """

    __slots__ = ("_digest", "_iterable", "representable", "rows", "shape", "shape_consistent")

    def __init__(self, iterable: object) -> None:
        self._iterable = iterable
        self._digest = hashlib.sha256()
        self.rows = 0
        self.shape: list[str] | None = None
        self.shape_consistent = True
        self.representable = True

    def __iter__(self) -> Iterator[object]:
        for row in cast("Iterable[object]", self._iterable):
            self.rows += 1
            values = list(row) if isinstance(row, tuple | list) else [row]
            shape = [type(value).__name__ for value in values]
            if self.shape is None:
                self.shape = shape
            elif shape != self.shape:
                self.shape_consistent = False
            if self.representable:
                try:
                    self._digest.update(canonical_json_bytes({"row": values}))
                except (ChunkPlanError, TypeError, ValueError):
                    self.representable = False
            yield row

    def record(self) -> Mapping[str, object]:
        return {
            "kind": "streamed",
            "count": self.rows,
            "shape_identity": _identity_of({"shape": self.shape or []}),
            "shape_consistent": self.shape_consistent,
            "value_sha256": self._digest.hexdigest() if self.representable else None,
            "representable": self.representable,
        }


class _MaterializedRows:
    """The rows of one proxy-observed statement, fetched under the progress handler."""

    __slots__ = ("_rows", "rowcount")

    def __init__(self, rows: Sequence[sqlite3.Row]) -> None:
        self._rows = list(rows)
        self.rowcount = len(self._rows)

    def fetchall(self) -> list[sqlite3.Row]:
        return list(self._rows)

    def fetchone(self) -> sqlite3.Row | None:
        return self._rows[0] if self._rows else None

    def __iter__(self) -> Iterator[sqlite3.Row]:
        return iter(self._rows)


class _TransactionWatch:
    """One watchdog-applicable database's WAL, watched over one active transaction -- §36."""

    __slots__ = (
        "baseline_frames",
        "connection_id",
        "database_path",
        "page_size",
        "peak_growth_frames",
        "role",
        "shm_path",
        "wal_path",
    )

    def __init__(self, role: str, database_path: Path, page_size: int) -> None:
        self.role = role
        self.database_path = database_path
        self.wal_path = database_path.with_name(database_path.name + "-wal")
        self.shm_path = database_path.with_name(database_path.name + "-shm")
        self.page_size = page_size
        self.baseline_frames: int | None = None
        self.peak_growth_frames = 0
        self.connection_id: int | None = None

    def observe(self) -> WalObservation:
        return observe_wal(self.wal_path, expected_page_size=self.page_size)

    def begin(self, observation: WalObservation) -> None:
        """Record the transaction baseline ONCE; never reset per statement."""
        self.baseline_frames = observation.conservative_frames
        self.peak_growth_frames = 0

    def growth(self, observation: WalObservation) -> int:
        _require(self.baseline_frames is not None, "no transaction baseline was recorded")
        assert self.baseline_frames is not None  # noqa: S101 - narrowed above
        growth = observation.conservative_frames - self.baseline_frames
        self.peak_growth_frames = max(self.peak_growth_frames, growth)
        return growth


class _ProgressSampler:
    """The ``set_progress_handler`` callback -- §33, §36, §37.

    The fast path is a counter, a monotonic read and a comparison. The slow path, on the
    configured interval, stats the already-validated database files, reads free space and the
    process peak RSS, appends one bounded ``STATEMENT_SAMPLE`` and evaluates the watchdog. Any
    failure on the slow path sets the abort cause and returns nonzero; the exception never
    escapes the callback (sqlite3 would silently swallow it) and is translated after sqlite3
    returns. Nothing here issues SQL, opens a connection, creates or deletes a file.
    """

    __slots__ = (
        "_bound",
        "_instrumentation",
        "_interval_ns",
        "_journal",
        "_next_sample_ns",
        "_watch",
        "abort_cause",
        "abort_detail",
        "abort_journaled",
        "last_growth_frames",
        "max_peak_rss_bytes",
        "samples",
        "ticks",
    )

    def __init__(
        self,
        instrumentation: _StageInstrumentation,
        journal: StatementJournalWriter,
        watch: _TransactionWatch,
        *,
        started_ns: int,
    ) -> None:
        self._instrumentation = instrumentation
        self._journal = journal
        self._watch = watch
        terms = instrumentation.terms
        self._interval_ns = terms.statement_progress_interval_seconds * _NANOSECONDS_PER_SECOND
        self._bound = terms.wal_watchdog_max_uncommitted_frames
        self._next_sample_ns = started_ns + self._interval_ns
        self.ticks = 0
        self.samples = 0
        self.abort_cause: str | None = None
        self.abort_detail = ""
        self.abort_journaled = False
        self.max_peak_rss_bytes: int | None = None
        self.last_growth_frames = 0

    def __call__(self) -> int:
        try:
            self.ticks += 1
            now = _monotonic_ns()
            if now < self._next_sample_ns:
                return 0
            self._next_sample_ns = now + self._interval_ns
            return self._sample(now)
        except BaseException as exc:  # noqa: BLE001 - nothing may escape the callback
            if self.abort_cause is None:
                self.abort_cause = _ABORT_INSTRUMENTATION
                self.abort_detail = f"{type(exc).__name__}: {exc}"[:600]
            return 1

    def _sample(self, now_ns: int) -> int:
        observation = self._watch.observe()
        growth = self._watch.growth(observation)
        self.last_growth_frames = growth
        main_bytes = self._watch.database_path.stat().st_size
        try:
            shm_bytes: int | None = os.lstat(self._watch.shm_path).st_size
        except FileNotFoundError:
            shm_bytes = None
        free = self._instrumentation.free_space()
        peak_rss = process_peak_resident_bytes()
        if peak_rss is None:
            message = "the peak-RSS helper returned None"
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        self.max_peak_rss_bytes = max(self.max_peak_rss_bytes or 0, peak_rss)
        self.samples += 1
        self._journal.append(
            EVENT_STATEMENT_SAMPLE,
            {
                "sample_ordinal": self.samples,
                "utc": utc_now(),
                "monotonic_ns": now_ns,
                "vm_step_ticks": self.ticks,
                "wal": dict(observation.as_record()),
                "main_file_bytes": main_bytes,
                "shm_bytes": shm_bytes,
                "transaction_baseline_frames": self._watch.baseline_frames,
                "observed_growth_frames": growth,
                "wal_watchdog_max_uncommitted_frames": self._bound,
                "free_bytes": dict(free),
                "process_peak_rss_bytes": peak_rss,
            },
        )
        if growth > self._bound:
            self.abort_cause = _ABORT_WATCHDOG
            self.abort_detail = (
                f"observed uncommitted WAL growth of {growth} frames exceeds the bound of "
                f"{self._bound} frames on {self._watch.role} (baseline "
                f"{self._watch.baseline_frames}, conservative frames "
                f"{observation.conservative_frames})"
            )
            terms = self._instrumentation.terms
            self._journal.append(
                EVENT_WATCHDOG_ABORT,
                {
                    "utc": utc_now(),
                    "monotonic_ns": now_ns,
                    "database_role": self._watch.role,
                    "observed_growth_frames": growth,
                    "transaction_baseline_frames": self._watch.baseline_frames,
                    "wal_watchdog_max_uncommitted_frames": self._bound,
                    "page_size_bytes": self._watch.page_size,
                    "frame_size_bytes": self._watch.page_size + WAL_FRAME_HEADER_BYTES,
                    "derived_byte_ceiling": self._bound
                    * (self._watch.page_size + WAL_FRAME_HEADER_BYTES),
                    "wal_watchdog_storage_ceiling_bytes": self._instrumentation.ceiling,
                    "wal": dict(observation.as_record()),
                    "detail": self.abort_detail,
                    "progress_handler_vm_steps": terms.progress_handler_vm_steps,
                },
            )
            self.abort_journaled = True
            return 1
        return 0


class _InstrumentedConnection:
    """The connection-boundary proxy for modules R19B may not edit -- §20 (S14, terminal).

    The only attribute it exposes is ``execute``: the exact SQL text a census derivation or the
    accepted row counter hands to it is matched against this stage's registered prefixes and
    executed through the instrumentation, or -- for the one bounded control prefix -- executed
    directly and counted. Anything else is an unregistered statement and refuses before sqlite3
    sees it. Rows of an observed ``fetchall`` statement are materialized under the progress
    handler so the whole statement is observed, not only its first step.
    """

    __slots__ = ("_connection", "_instrumentation")

    def __init__(
        self, instrumentation: _StageInstrumentation, connection: sqlite3.Connection
    ) -> None:
        self._instrumentation = instrumentation
        self._connection = connection

    @property
    def in_transaction(self) -> bool:
        return self._connection.in_transaction

    def execute(self, sql: str, parameters: object = ()) -> object:
        descriptor = self._instrumentation.proxy_descriptor(sql)
        if descriptor is None:
            self._instrumentation.note_bounded(sql)
            return self._connection.execute(sql, cast("Any", parameters))
        result = self._instrumentation.execute(
            self._connection,
            sql,
            parameters,
            operation=descriptor.operation,
            kind=descriptor.operation_kind,
            role=descriptor.database_role,
        )
        if descriptor.operation_kind == STATEMENT_KIND_FETCHALL:
            return _MaterializedRows(cast("Sequence[sqlite3.Row]", result))
        return result


@dataclass(frozen=True, slots=True)
class _CompletedStatement:
    """One sealed, successful statement journal and everything the execution set binds."""

    record: Mapping[str, object]

    @property
    def operation(self) -> str:
        return str(self.record["operation"])


class _StageInstrumentation:
    """Everything one stage attempt observes: the runner, the proxy, the journals, the set.

    Constructed once per stage attempt with the StagePlan's terms, this stage's registry
    slice and the attempt's create-once directory. Every material statement of the attempt --
    seam-routed, proxy-observed or issued here -- passes through :meth:`execute`, which
    creates the statement's journal, appends and fsyncs ``STATEMENT_START`` before sqlite3
    sees the SQL, installs the progress handler around exactly that statement, removes it in
    ``finally``, journals the terminal event, seals the journal and records the execution.
    """

    def __init__(
        self,
        ctx: _StageContext,
        stage: L2Stage,
        prior_units: Sequence[AppliedUnit],
        attempt_ordinal: int,
        attempt_directory: Path,
        *,
        descriptors: Sequence[_OperationDescriptor] | None = None,
    ) -> None:
        self.ctx = ctx
        self.stage = stage
        self.terms = ctx.stage_plan.observability_terms
        self.ceiling = ctx.stage_plan.wal_watchdog_storage_ceiling_bytes
        self.registry_identity = ctx.stage_plan.statement_registry_identity
        self.descriptors: tuple[_OperationDescriptor, ...] = tuple(
            _declared_operations(stage, len(ctx.counter_sources))
            if descriptors is None
            else descriptors
        )
        self._by_operation = {item.operation: item for item in self.descriptors}
        _require(
            len(self._by_operation) == len(self.descriptors),
            f"stage {stage.stage_id!r} declares an operation twice",
        )
        self.attempt_ordinal = attempt_ordinal
        self.attempt_directory = attempt_directory
        self.progress_root = ctx.stage_plan.statement_progress_root
        self.prior_units = tuple(prior_units)
        self.executions: list[_CompletedStatement] = []
        self.bounded_executions: dict[str, int] = {}
        self.selected_path: str | None = None
        self.abort: _InstrumentationAbortError | None = None
        self._next_ordinal = 0
        self._watches: dict[str, _TransactionWatch] = {}
        self.pid = os.getpid()
        anchor = (
            ctx.world_directory
            if os.path.lexists(ctx.world_directory)
            else ctx.world_directory.parent
        )
        self.world_device = anchor.stat().st_dev
        self.same_device = self.world_device == ctx.binding.temp_root_device
        self._sidecar_path = ctx.world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME

    # -- registry ----------------------------------------------------------- #
    def descriptor_for(self, operation: str) -> _OperationDescriptor:
        descriptor = self._by_operation.get(operation)
        if descriptor is None:
            message = (
                f"{operation!r} is not a registered material operation of stage "
                f"{self.stage.stage_id!r}; an unregistered statement never executes"
            )
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        if descriptor.path is not None and descriptor.path != self.selected_path:
            message = (
                f"{descriptor.statement_id} is declared for the {descriptor.path} path and the "
                f"journaled path decision selected {self.selected_path!r}"
            )
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        return descriptor

    def proxy_descriptor(self, sql: str) -> _OperationDescriptor | None:
        """The registered descriptor a proxy-observed statement matches, or ``None`` when the
        statement is one of this stage's bounded control prefixes."""
        for descriptor in self.descriptors:
            if descriptor.sql_prefix is not None and sql.startswith(descriptor.sql_prefix):
                return descriptor
        for prefix in _BOUNDED_PROXY_PREFIXES.get(self.stage.kind, ()):
            if sql.startswith(prefix):
                return None
        message = (
            f"a statement reached the connection boundary of stage {self.stage.stage_id!r} that "
            f"no registered operation or bounded control prefix names: {sql[:80]!r}"
        )
        raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)

    def note_bounded(self, sql: str) -> None:
        for prefix in _BOUNDED_PROXY_PREFIXES.get(self.stage.kind, ()):
            if sql.startswith(prefix):
                self.bounded_executions[prefix] = self.bounded_executions.get(prefix, 0) + 1
                return

    def proxy(self, connection: sqlite3.Connection) -> _InstrumentedConnection:
        return _InstrumentedConnection(self, connection)

    def expected_executions(self, descriptor: _OperationDescriptor) -> int | str:
        expected = descriptor.expected_executions
        if expected == _EXPECTED_S2_DUPLICATES:
            witness = _witness_of(self.prior_units, _STAGE_REDUCED_PARSER_RUN)
            return len(_stored_strings(witness["duplicate_identities"], "duplicate_identities"))
        return expected

    # -- measurement -------------------------------------------------------- #
    def free_space(self) -> Mapping[str, object]:
        """Free bytes on the world's filesystem, reported for both logical roles -- §34."""
        world = free_bytes(self.ctx.world_directory)
        if world is None:
            message = "the free-space helper returned None for the world root"
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        if not self.same_device:
            message = (
                "the SQLite temporary root and the world are on different devices; the accepted "
                "binding refuses that topology and no separate-device production route exists"
            )
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        return _free_space_by_role(world, world, same_device=True)

    def _watch(
        self, role: str, connection: sqlite3.Connection, database_path: Path
    ) -> _TransactionWatch:
        watch = self._watches.get(role)
        if watch is None:
            watch = _TransactionWatch(role, database_path, self.terms.expected_page_size_bytes)
            self._watches[role] = watch
        if watch.connection_id != id(connection):
            page_size = int(connection.execute("PRAGMA main.page_size").fetchone()[0])
            if page_size != self.terms.expected_page_size_bytes:
                message = (
                    f"{role} reports page size {page_size} where the StagePlan expects "
                    f"{self.terms.expected_page_size_bytes}; no material statement runs"
                )
                raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
            derived = self.terms.wal_watchdog_max_uncommitted_frames * (
                page_size + WAL_FRAME_HEADER_BYTES
            )
            if derived > self.ceiling:
                message = (
                    f"{role}: the frame bound derives {derived} bytes at the actual page size, "
                    f"above the storage ceiling of {self.ceiling}; no material statement runs"
                )
                raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
            if role == _ROLE_COMPACT_EVIDENCE:
                # The sidecar builds in autocommit statements; without an auto-checkpoint the
                # log grows monotonically across them, so a per-statement baseline is exact.
                connection.execute("PRAGMA wal_autocheckpoint = 0")
            watch.connection_id = id(connection)
        return watch

    def begin_world_transaction(self, connection: sqlite3.Connection) -> WalObservation:
        """Record the world transaction's baseline ONCE, right after BEGIN -- §36."""
        _require(connection.in_transaction, "the transaction baseline is taken inside BEGIN")
        watch = self._watch(_ROLE_WORKING_CATALOG, connection, self.ctx.catalog_path)
        observation = watch.observe()
        watch.begin(observation)
        return observation

    # -- journals ----------------------------------------------------------- #
    def _bindings(
        self,
        descriptor: _OperationDescriptor,
        ordinal: int,
        sql_sha256: str | None,
        kind: str,
    ) -> dict[str, object]:
        plan = self.ctx.stage_plan
        return {
            "journal_contract": L2_STATEMENT_JOURNAL_CONTRACT,
            "successor_run_id": plan.successor_run_id,
            "route": plan.route,
            "stage_plan_identity": plan.identity,
            "statement_registry_identity": self.registry_identity,
            "descriptor_identity": descriptor.identity,
            "stage_id": self.stage.stage_id,
            "stage_ordinal": self.stage.ordinal,
            "unit_id": self.stage.unit_id,
            "unit_kind": self.stage.kind,
            "stage_attempt_ordinal": self.attempt_ordinal,
            "statement_id": descriptor.statement_id,
            "statement_ordinal": ordinal,
            "operation": descriptor.operation,
            "database_role": descriptor.database_role,
            "sql_identity_mode": descriptor.sql_identity_mode,
            "runtime_sql_sha256": sql_sha256,
            "execution_kind": kind,
            "process_pid": self.pid,
        }

    def _open_journal(self, ordinal: int) -> StatementJournalWriter:
        try:
            return StatementJournalWriter.create(
                self.attempt_directory / f"statement-{ordinal:04d}.jsonl"
            )
        except WorkingCatalogError as exc:
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc

    def _record(
        self,
        descriptor: _OperationDescriptor,
        ordinal: int,
        sql_sha256: str | None,
        kind: str,
        evidence: Mapping[str, object],
        journal: StatementJournalWriter,
        sealed: tuple[str, int],
        rowcount: int | None,
        elapsed_ns: int,
    ) -> None:
        sha256, length = sealed
        self.executions.append(
            _CompletedStatement(
                {
                    "statement_ordinal": ordinal,
                    "statement_id": descriptor.statement_id,
                    "operation": descriptor.operation,
                    "descriptor_identity": descriptor.identity,
                    "sql_identity_mode": descriptor.sql_identity_mode,
                    "runtime_sql_sha256": sql_sha256,
                    "execution_kind": kind,
                    "parameter_identity": dict(evidence),
                    "database_role": descriptor.database_role,
                    "journal_relative_path": str(journal.path.relative_to(self.progress_root)),
                    "journal_byte_length": length,
                    "journal_sha256": sha256,
                    "journal_chain_tip": journal.tip,
                    "journal_event_count": journal.sequence,
                    "stage_attempt_ordinal": self.attempt_ordinal,
                    "rowcount": rowcount,
                    "elapsed_ns": elapsed_ns,
                }
            )
        )

    def _seal(
        self, journal: StatementJournalWriter, kind: str, body: Mapping[str, object]
    ) -> tuple[str, int]:
        try:
            journal.append(kind, body)
            return journal.seal()
        except WorkingCatalogError as exc:
            journal.abandon()
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc

    def _refuse_before_execution(
        self,
        journal: StatementJournalWriter,
        bindings: Mapping[str, object],
        started_ns: int,
        detail: str,
    ) -> NoReturn:
        """A refusal BEFORE sqlite3 saw the statement: START, then ERROR, sealed, then raised."""
        try:
            journal.append(
                EVENT_STATEMENT_START,
                {**bindings, "utc": utc_now(), "monotonic_ns": started_ns, "refused": detail},
            )
        except WorkingCatalogError as exc:
            journal.abandon()
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc
        self._seal(
            journal,
            EVENT_STATEMENT_ERROR,
            {
                "utc": utc_now(),
                "monotonic_ns": _monotonic_ns(),
                "error": detail,
                "refused_before_execution": True,
            },
        )
        raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, detail)

    def _fail(
        self,
        journal: StatementJournalWriter,
        sampler: _ProgressSampler | None,
        watch: _TransactionWatch | None,
        exc: BaseException,
        started_ns: int,
    ) -> BaseException:
        """Journal a non-success terminal event, seal, and return the exception to raise."""
        cause = None if sampler is None else sampler.abort_cause
        body: dict[str, object] = {
            "utc": utc_now(),
            "monotonic_ns": _monotonic_ns(),
            "elapsed_ns": _monotonic_ns() - started_ns,
            "error_type": type(exc).__name__,
            "error": str(exc)[:600],
            "samples": 0 if sampler is None else sampler.samples,
            "vm_step_ticks": 0 if sampler is None else sampler.ticks,
        }
        if cause is not None:
            assert sampler is not None  # noqa: S101 - cause comes from the sampler
            body["abort_cause"] = cause
            body["abort_detail"] = sampler.abort_detail
            if cause == _ABORT_WATCHDOG and sampler.abort_journaled:
                try:
                    journal.seal()
                except WorkingCatalogError as seal_error:
                    journal.abandon()
                    return _InstrumentationAbortError(
                        _ABORT_WATCHDOG,
                        f"{sampler.abort_detail} (journal seal failed: {seal_error})",
                    )
                abort = _InstrumentationAbortError(_ABORT_WATCHDOG, sampler.abort_detail)
                self.abort = abort
                return abort
            self._seal(journal, EVENT_STATEMENT_ERROR, body)
            abort = _InstrumentationAbortError(str(cause), sampler.abort_detail)
            self.abort = abort
            return abort
        self._seal(journal, EVENT_STATEMENT_ERROR, body)
        return exc

    def execute(  # noqa: PLR0913, PLR0915
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: object,
        *,
        operation: str,
        kind: str,
        role: str = _ROLE_WORKING_CATALOG,
    ) -> object:
        """Run one registered material statement under a sealed journal -- §22, §27, §33."""
        descriptor = self.descriptor_for(operation)
        for condition, detail in (
            (descriptor.sql_identity_mode in _SQL_MODES, "is not a SQL operation"),
            (
                kind == descriptor.operation_kind,
                f"is declared {descriptor.operation_kind!r}, executed as {kind!r}",
            ),
            (
                role == descriptor.database_role,
                f"is declared on {descriptor.database_role}, executed on {role}",
            ),
        ):
            if not condition:
                message = f"{descriptor.statement_id} {detail}"
                raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        database_path = (
            self.ctx.catalog_path if role == _ROLE_WORKING_CATALOG else self._sidecar_path
        )
        watch = self._watch(role, connection, database_path)
        if role == _ROLE_COMPACT_EVIDENCE and not connection.in_transaction:
            watch.begin(watch.observe())
        if watch.baseline_frames is None:
            message = f"{descriptor.statement_id}: no transaction baseline was recorded"
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, message)
        sql_sha256 = _sql_sha256(sql)
        ordinal = self._next_ordinal
        self._next_ordinal += 1
        journal = self._open_journal(ordinal)
        started_ns = _monotonic_ns()
        bindings = self._bindings(descriptor, ordinal, sql_sha256, kind)
        if (
            descriptor.sql_identity_mode == _MODE_STATIC_SQL
            and sql_sha256 != descriptor.static_sql_sha256
        ):
            detail = (
                f"{descriptor.statement_id}: the runtime SQL hashes to {sql_sha256[:16]}... where "
                f"the StagePlan binds {str(descriptor.static_sql_sha256)[:16]}...; refused before "
                "sqlite3 saw it"
            )
            self._refuse_before_execution(journal, bindings, started_ns, detail)
        streaming: _StreamingParameterEvidence | None = None
        if kind == _KIND_EXECUTEMANY:
            streaming = _StreamingParameterEvidence(parameters)
            evidence: Mapping[str, object] = {"kind": "streamed", "count": None}
        else:
            evidence = _parameter_evidence(parameters)
        observation = watch.observe()
        peak_rss = process_peak_resident_bytes()
        if peak_rss is None:
            self._refuse_before_execution(
                journal, bindings, started_ns, "the peak-RSS helper returned None"
            )
        try:
            free = self.free_space()
        except _InstrumentationAbortError as exc:
            self._refuse_before_execution(journal, bindings, started_ns, exc.detail)
        try:
            journal.append(
                EVENT_STATEMENT_START,
                {
                    **bindings,
                    "utc": utc_now(),
                    "monotonic_ns": started_ns,
                    "parameter_evidence": dict(evidence),
                    "measurements": {
                        "wal": dict(observation.as_record()),
                        "transaction_baseline_frames": watch.baseline_frames,
                        "wal_watchdog_max_uncommitted_frames": (
                            self.terms.wal_watchdog_max_uncommitted_frames
                        ),
                        "page_size_bytes": watch.page_size,
                        "frame_size_bytes": watch.page_size + WAL_FRAME_HEADER_BYTES,
                        "derived_byte_ceiling": self.terms.wal_watchdog_max_uncommitted_frames
                        * (watch.page_size + WAL_FRAME_HEADER_BYTES),
                        "wal_watchdog_storage_ceiling_bytes": self.ceiling,
                        "progress_handler_vm_steps": self.terms.progress_handler_vm_steps,
                        "statement_progress_interval_seconds": (
                            self.terms.statement_progress_interval_seconds
                        ),
                        "free_bytes": dict(free),
                        "process_peak_rss_bytes": peak_rss,
                        "watchdog_applicable": descriptor.watchdog_applicable,
                    },
                },
            )
        except WorkingCatalogError as exc:
            journal.abandon()
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc
        sampler = _ProgressSampler(self, journal, watch, started_ns=started_ns)
        connection.set_progress_handler(sampler, self.terms.progress_handler_vm_steps)
        if kind == STATEMENT_KIND_ITERATE:
            return self._stream(
                connection,
                sql,
                parameters,
                descriptor,
                ordinal,
                sql_sha256,
                evidence,
                journal,
                sampler,
                watch,
                started_ns,
            )
        result: object
        rowcount: int | None
        try:
            if kind == STATEMENT_KIND_FETCHALL:
                rows = connection.execute(sql, cast("Any", parameters)).fetchall()
                result, rowcount = rows, len(rows)
            elif kind == _KIND_EXECUTEMANY:
                assert streaming is not None  # noqa: S101 - set above for this kind
                cursor = connection.executemany(sql, cast("Any", streaming))
                result, rowcount = cursor, int(cursor.rowcount)
                evidence = streaming.record()
            else:
                cursor = connection.execute(sql, cast("Any", parameters))
                result, rowcount = cursor, int(cursor.rowcount)
        except BaseException as exc:
            connection.set_progress_handler(None, 0)
            raise self._fail(journal, sampler, watch, exc, started_ns) from exc
        finally:
            connection.set_progress_handler(None, 0)
        sealed = self._complete(journal, sampler, watch, evidence, started_ns, rowcount)
        self._record(
            descriptor,
            ordinal,
            sql_sha256,
            kind,
            evidence,
            journal,
            sealed,
            rowcount,
            _monotonic_ns() - started_ns,
        )
        return result

    def _complete(
        self,
        journal: StatementJournalWriter,
        sampler: _ProgressSampler | None,
        watch: _TransactionWatch | None,
        evidence: Mapping[str, object],
        started_ns: int,
        rowcount: int | None,
    ) -> tuple[str, int]:
        now = _monotonic_ns()
        observation = None if watch is None else watch.observe()
        peak_rss = process_peak_resident_bytes()
        body: dict[str, object] = {
            "utc": utc_now(),
            "monotonic_ns": now,
            "elapsed_ns": now - started_ns,
            "rowcount": rowcount,
            "parameter_evidence": dict(evidence),
            "samples": 0 if sampler is None else sampler.samples,
            "vm_step_ticks": 0 if sampler is None else sampler.ticks,
            "maximum_process_peak_rss_bytes": max(
                [
                    value
                    for value in (
                        (None if sampler is None else sampler.max_peak_rss_bytes),
                        peak_rss,
                    )
                    if value is not None
                ],
                default=None,
            ),
        }
        if observation is not None and watch is not None:
            body["wal"] = dict(observation.as_record())
            body["observed_growth_frames"] = watch.growth(observation)
            body["peak_observed_growth_frames"] = watch.peak_growth_frames
            body["transaction_baseline_frames"] = watch.baseline_frames
        return self._seal(journal, EVENT_STATEMENT_END, body)

    def _stream(  # noqa: PLR0913
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: object,
        descriptor: _OperationDescriptor,
        ordinal: int,
        sql_sha256: str,
        evidence: Mapping[str, object],
        journal: StatementJournalWriter,
        sampler: _ProgressSampler,
        watch: _TransactionWatch,
        started_ns: int,
    ) -> Iterator[sqlite3.Row]:
        """An iterated statement: the handler stays installed until the last row is consumed."""
        rows = 0
        try:
            cursor = connection.execute(sql, cast("Any", parameters))
            for row in cursor:
                rows += 1
                yield row
        except BaseException as exc:
            connection.set_progress_handler(None, 0)
            raise self._fail(journal, sampler, watch, exc, started_ns) from exc
        finally:
            connection.set_progress_handler(None, 0)
        sealed = self._complete(journal, sampler, watch, evidence, started_ns, rows)
        self._record(
            descriptor,
            ordinal,
            sql_sha256,
            STATEMENT_KIND_ITERATE,
            evidence,
            journal,
            sealed,
            rows,
            _monotonic_ns() - started_ns,
        )

    def consolidation_runner(
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: object,
        kind: str,
        operation: str,
    ) -> object:
        """The seam runner for the consolidator's helpers over the world catalog."""
        return self.execute(
            connection, sql, parameters, operation=operation, kind=kind, role=_ROLE_WORKING_CATALOG
        )

    def sidecar_runner(
        self,
        connection: sqlite3.Connection,
        sql: str,
        parameters: object,
        kind: str,
        operation: str,
    ) -> object:
        """The seam runner for the sidecar build and its folds over the compact-evidence file."""
        return self.execute(
            connection, sql, parameters, operation=operation, kind=kind, role=_ROLE_COMPACT_EVIDENCE
        )

    def count(self, connection: sqlite3.Connection, table: str) -> int:
        """The exact main-table count, as a registered static statement of this stage."""
        rows = cast(
            "Sequence[sqlite3.Row]",
            self.execute(
                connection,
                _count_sql(table),
                (),
                operation=f"count:{table}",
                kind=STATEMENT_KIND_FETCHALL,
            ),
        )
        return int(rows[0]["n"])

    def record_callable(
        self,
        operation: str,
        work: Callable[[], object],
        *,
        facts: Mapping[str, object] | None = None,
    ) -> object:
        """Journal one genuine non-SQL material operation: START, the work, END."""
        descriptor = self.descriptor_for(operation)
        _require(
            descriptor.sql_identity_mode == _MODE_CALLABLE_NON_SQL
            and descriptor.operation_kind == _KIND_CALLABLE,
            f"{descriptor.statement_id} is not a callable operation",
        )
        ordinal = self._next_ordinal
        self._next_ordinal += 1
        journal = self._open_journal(ordinal)
        started_ns = _monotonic_ns()
        bindings = self._bindings(descriptor, ordinal, None, _KIND_CALLABLE)
        try:
            journal.append(
                EVENT_STATEMENT_START,
                {
                    **bindings,
                    "utc": utc_now(),
                    "monotonic_ns": started_ns,
                    "facts": dict(facts or {}),
                    "process_peak_rss_bytes": process_peak_resident_bytes(),
                },
            )
        except WorkingCatalogError as exc:
            journal.abandon()
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc
        try:
            result = work()
        except BaseException as exc:
            raise self._fail(journal, None, None, exc, started_ns) from exc
        evidence: Mapping[str, object] = {"kind": "callable", "count": None}
        sealed = self._complete(journal, None, None, evidence, started_ns, None)
        self._record(
            descriptor,
            ordinal,
            None,
            _KIND_CALLABLE,
            evidence,
            journal,
            sealed,
            None,
            _monotonic_ns() - started_ns,
        )
        return result

    def record_path_decision(
        self,
        *,
        sidecar_state: Mapping[str, object],
        selected: str | None,
        expected_path: str | None,
    ) -> None:
        """Journal S18's path decision FIRST -- C2-R2; a conflicting sidecar selects nothing."""
        descriptor = self.descriptor_for(_OP_PATH_DECISION)
        ordinal = self._next_ordinal
        self._next_ordinal += 1
        journal = self._open_journal(ordinal)
        started_ns = _monotonic_ns()
        bindings = self._bindings(descriptor, ordinal, None, _KIND_PATH_DECISION)
        decision = {
            "sidecar_file_state": dict(sidecar_state),
            "file_state_identity": _identity_of({"sidecar_file_state": dict(sidecar_state)}),
            "expected_path": expected_path,
            "selected_path": selected,
        }
        try:
            journal.append(
                EVENT_STATEMENT_START,
                {**bindings, "utc": utc_now(), "monotonic_ns": started_ns, "decision": decision},
            )
        except WorkingCatalogError as exc:
            journal.abandon()
            raise _InstrumentationAbortError(_ABORT_INSTRUMENTATION, str(exc)) from exc
        evidence: Mapping[str, object] = {
            "kind": "path_decision",
            "count": None,
            "selected_path": selected,
        }
        sealed = self._complete(journal, None, None, evidence, started_ns, None)
        self._record(
            descriptor,
            ordinal,
            None,
            _KIND_PATH_DECISION,
            evidence,
            journal,
            sealed,
            None,
            _monotonic_ns() - started_ns,
        )
        self.selected_path = selected

    # -- the execution set -------------------------------------------------- #
    def coverage(self, phases: frozenset[str]) -> tuple[Mapping[str, object], ...]:
        """Exact coverage of the required descriptors of ``phases`` on the selected path."""
        report: list[Mapping[str, object]] = []
        for descriptor in self.descriptors:
            if descriptor.phase not in phases:
                continue
            if descriptor.path is not None:
                _require(
                    self.selected_path is not None,
                    f"stage {self.stage.stage_id!r} declares conditional paths and no path "
                    "decision was journaled",
                )
                if descriptor.path != self.selected_path:
                    continue
            observed = sum(1 for item in self.executions if item.operation == descriptor.operation)
            expected = self.expected_executions(descriptor)
            report.append(
                {
                    "statement_id": descriptor.statement_id,
                    "expected": expected,
                    "observed": observed,
                }
            )
            if expected == _EXPECTED_DATA_DEPENDENT:
                continue
            _require(
                observed == expected,
                f"coverage: {descriptor.statement_id} has {observed} sealed successful journal(s) "
                f"where exactly {expected} are required on the "
                f"{self.selected_path or 'unconditional'} path",
            )
        return tuple(report)

    def execution_set(self, phases: frozenset[str]) -> Mapping[str, object]:
        """The ordered, sealed statement execution set and its identity -- §29."""
        coverage = self.coverage(phases)
        body: dict[str, object] = {
            "contract": L2_STATEMENT_EXECUTION_SET_CONTRACT,
            "successor_run_id": self.ctx.stage_plan.successor_run_id,
            "stage_plan_identity": self.ctx.stage_plan.identity,
            "statement_registry_identity": self.registry_identity,
            "stage_id": self.stage.stage_id,
            "stage_ordinal": self.stage.ordinal,
            "stage_attempt_ordinal": self.attempt_ordinal,
            "selected_path": self.selected_path,
            "phases": sorted(phases),
            "coverage": [dict(item) for item in coverage],
            "bounded_control_executions": dict(sorted(self.bounded_executions.items())),
            "statements": [dict(item.record) for item in self.executions],
        }
        body["execution_set_identity"] = _identity_of(body)
        return body

    def publish_abort_record(self, normalized: bool, checkpoint: object) -> Path:
        """The durable record of an instrumentation or watchdog abort, create-once."""
        abort = self.abort
        record: dict[str, object] = {
            "contract": _ABORT_RECORD_CONTRACT,
            "successor_run_id": self.ctx.stage_plan.successor_run_id,
            "stage_plan_identity": self.ctx.stage_plan.identity,
            "stage_id": self.stage.stage_id,
            "stage_ordinal": self.stage.ordinal,
            "stage_attempt_ordinal": self.attempt_ordinal,
            "cause": None if abort is None else abort.cause,
            "detail": None if abort is None else abort.detail,
            "statements_sealed": len(self.executions),
            "ABORT_WAL_NORMALIZED": normalized,
            "checkpoint_result": checkpoint,
            "applied_unit_inserted": False,
            "stage_receipt_published": False,
            "utc": utc_now(),
        }
        record["abort_record_identity"] = _identity_of(record)
        path = self.attempt_directory.parent / f"abort-attempt-{self.attempt_ordinal:03d}.json"
        write_once_canonical_json(path, record)
        return path


def _free_space_by_role(
    world_free: int, temp_free: int, *, same_device: bool
) -> Mapping[str, object]:
    """Both logical roles' free bytes, never summed -- §34 (pure; unit-testable for two devices)."""
    return {
        "world_free_bytes": world_free,
        "sqlite_temp_free_bytes": temp_free,
        "same_device": same_device,
        "drawdowns_summed": False,
    }


def _stage_instrumentation_for(
    ctx: _StageContext, stage: L2Stage, prior: Sequence[AppliedUnit]
) -> _StageInstrumentation:
    ordinal, directory = _allocate_stage_attempt(ctx, stage)
    return _StageInstrumentation(ctx, stage, prior, ordinal, directory)


# --------------------------------------------------------------------------- #
# Observability -- §30-§32: journals are observational after COMMIT
# --------------------------------------------------------------------------- #
def _journal_observability(
    progress_root: Path, execution_set: Mapping[str, object] | None
) -> Mapping[str, object]:
    """Re-authenticate every journal an execution set binds; report, never repair or rerun."""
    if execution_set is None:
        return {
            "status": _OBSERVABILITY_GAP_MISSING,
            "expected_journal_count": 0,
            "missing": [],
            "changed": [],
            "detail": "the applied unit binds no execution set",
        }
    statements = cast("list[Mapping[str, object]]", execution_set.get("statements", []))
    missing: list[Mapping[str, object]] = []
    changed: list[Mapping[str, object]] = []
    for item in statements:
        relative = str(item["journal_relative_path"])
        expected_sha = str(item["journal_sha256"])
        expected_length = _stored_int(item["journal_byte_length"], "journal_byte_length")
        path = progress_root / relative
        if ".." in Path(relative).parts:
            changed.append(
                {
                    "journal_relative_path": relative,
                    "expected_sha256": expected_sha,
                    "expected_byte_length": expected_length,
                    "observed": "traversal",
                }
            )
            continue
        status = authenticate_statement_journal(
            path, expected_sha256=expected_sha, expected_byte_length=expected_length
        )
        if status == JOURNAL_AUTHENTIC:
            continue
        entry: dict[str, object] = {
            "journal_relative_path": relative,
            "expected_sha256": expected_sha,
            "expected_byte_length": expected_length,
        }
        if status == JOURNAL_MISSING:
            missing.append(entry)
            continue
        try:
            observed_sha, observed_length = file_sha256(path)
            entry["observed_sha256"] = observed_sha
            entry["observed_byte_length"] = observed_length
        except ChunkEvidenceError as exc:
            entry["observed"] = str(exc)[:200]
        changed.append(entry)
    if missing:
        status_label = _OBSERVABILITY_GAP_MISSING
    elif changed:
        status_label = _OBSERVABILITY_GAP_CHANGED
    else:
        status_label = _OBSERVABILITY_COMPLETE
    return {
        "status": status_label,
        "expected_journal_count": len(statements),
        "missing": missing,
        "changed": changed,
        "detail": "observational: a gap revokes no committed semantics and triggers no rerun",
    }


def _unit_observability(ctx: _StageContext, unit: AppliedUnit) -> Mapping[str, object]:
    return _journal_observability(
        ctx.stage_plan.statement_progress_root, unit.statement_execution_set
    )


def observability_stage_statuses(
    progress_root: Path, units: Sequence[AppliedUnit]
) -> tuple[Mapping[str, object], ...]:
    """The canonical ordered per-stage observability statuses over committed units -- §32."""
    statuses: list[Mapping[str, object]] = []
    for unit in units:
        report = _journal_observability(progress_root, unit.statement_execution_set)
        statuses.append(
            {
                "stage_id": unit.stage_id,
                "stage_ordinal": unit.stage_ordinal,
                "applied_unit_identity": unit.unit_identity,
                "statement_execution_set_identity": unit.statement_execution_set_identity,
                "observability_status": report["status"],
                "expected_journal_count": report["expected_journal_count"],
                "missing": [
                    dict(item) for item in cast("list[Mapping[str, object]]", report["missing"])
                ],
                "changed": [
                    dict(item) for item in cast("list[Mapping[str, object]]", report["changed"])
                ],
            }
        )
    return tuple(statuses)


def _observability_summary(statuses: Sequence[Mapping[str, object]]) -> tuple[str, int]:
    identity = _identity_of({"observability_stage_statuses": [dict(item) for item in statuses]})
    gaps = sum(1 for item in statuses if item["observability_status"] != _OBSERVABILITY_COMPLETE)
    return identity, gaps


def read_observability_closeout(path: Path) -> Mapping[str, object]:
    """One durable observability closeout, canonical, with its identity recomputed.

    Raises:
        ChunkMultipassError: absent, a link, not canonical, wrong contract, or its identity
            does not describe its body.
    """
    _require(not path.is_symlink(), f"closeout {path.name!r} is a symbolic link; refused")
    _require(path.is_file(), f"no observability closeout exists at {path.name!r}")
    payload = path.read_bytes()
    record = _json_object(payload.decode("utf-8"), f"closeout {path.name!r}")
    body = {key: value for key, value in record.items() if key != "closeout_identity"}
    _require(
        canonical_json_bytes(record) == payload
        and str(record.get("contract")) == L2_OBSERVABILITY_CLOSEOUT_CONTRACT
        and str(record.get("closeout_identity")) == _identity_of(body),
        f"closeout {path.name!r} is not canonical, carries another contract, or does not "
        "describe its own body; refused",
    )
    return record


def require_r21_observability_ready(
    terminal_record: Mapping[str, object], *, stage_receipt_root: Path
) -> Mapping[str, object]:
    """The R21 qualification gate -- C2-R3: terminal gap count zero AND a fresh recheck of zero.

    Reads the terminal record's bound observability, the closeout it names beneath the receipt
    root, holds the closeout's identity to the binding, and re-authenticates every journal the
    closeout's execution sets name NOW. Post-terminal evidence loss therefore refuses.

    Raises:
        ChunkMultipassError: no observability binding, a gap at terminal time, a closeout that
            is absent or does not match, or a current gap.
    """
    bound = terminal_record.get("successor_observability")
    _require(
        isinstance(bound, Mapping),
        "the terminal record binds no successor observability; not R21-ready",
    )
    binding = cast("Mapping[str, object]", bound)
    terminal_gaps = _stored_int(binding["observability_gap_count"], "observability_gap_count")
    _require(
        terminal_gaps == 0,
        f"the terminal record recorded {terminal_gaps} observability gap(s); not R21-ready",
    )
    closeout = read_observability_closeout(
        stage_receipt_root / str(binding["closeout_relative_filename"])
    )
    _require(
        str(closeout["closeout_identity"]) == str(binding["closeout_identity"])
        and str(closeout["observability_summary_identity"])
        == str(binding["observability_summary_identity"]),
        "the closeout beneath the receipt root is not the one the terminal record binds",
    )
    progress_root = stage_receipt_root / STATEMENT_PROGRESS_DIRECTORY
    current_gaps = 0
    rechecked: list[Mapping[str, object]] = []
    for entry in cast("list[Mapping[str, object]]", closeout["observability_stage_statuses"]):
        execution_set = cast("Mapping[str, object] | None", entry.get("statement_execution_set"))
        report = _journal_observability(progress_root, execution_set)
        if report["status"] != _OBSERVABILITY_COMPLETE:
            current_gaps += 1
        rechecked.append({"stage_id": entry["stage_id"], "current_status": report["status"]})
    _require(
        current_gaps == 0,
        f"{current_gaps} stage(s) lost or changed a journal since the terminal record; "
        "not R21-ready",
    )
    return {
        "terminal_observability_gap_count": terminal_gaps,
        "current_observability_gap_count": current_gaps,
        "stages_rechecked": rechecked,
        "r21_observability_ready": True,
    }


# --------------------------------------------------------------------------- #
# Same-database stage semantics -- each returns (rows_written, outcome witness)
# --------------------------------------------------------------------------- #
def _stage_capture_and_drop_indexes(
    connection: sqlite3.Connection, ctx: _StageContext
) -> tuple[int, Mapping[str, object]]:
    """S1: enumerate, persist and drop the five deferrable indexes in ONE transaction -- §29."""
    records = _deferrable_index_records(connection)
    expected = cast(
        "list[Mapping[str, object]]", ctx.stage_plan.body["expected_deferred_index_set"]
    )
    observed = [
        {"ordinal": ordinal, "name": name, "table": table, "sql": sql}
        for ordinal, name, table, sql in records
    ]
    _require(
        len(records) == len(EXPECTED_DEFERRED_INDEX_NAMES)
        and tuple(name for _o, name, _t, _s in records) == EXPECTED_DEFERRED_INDEX_NAMES,
        f"the world declares {[name for _o, name, _t, _s in records]} deferrable indexes where "
        f"exactly {list(EXPECTED_DEFERRED_INDEX_NAMES)} are required",
    )
    _require(
        [dict(item) for item in expected] == observed,
        "the world's deferrable index set is not the set the StagePlan bound; refused",
    )
    set_identity = _identity_of({"contract": L2_DEFERRED_INDEX_SET_CONTRACT, "indexes": observed})
    _require(
        set_identity == str(ctx.stage_plan.body["expected_deferred_index_set_identity"]),
        "the deferred-index set identity does not equal the StagePlan's expected identity",
    )
    for ordinal, name, table, sql in records:
        connection.execute(
            f"INSERT INTO main.{L2_DEFERRED_INDEXES_TABLE} "  # noqa: S608
            "(ordinal, name, table_name, create_sql, set_identity) VALUES (?, ?, ?, ?, ?)",
            (ordinal, name, table, sql, set_identity),
        )
    for _ordinal, name, _table, _sql in records:
        connection.execute(f"DROP INDEX main.{name}")
    remaining = {
        str(row["name"])
        for row in connection.execute(
            "SELECT name FROM main.sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
        )
        if str(row["name"]) in EXPECTED_DEFERRED_INDEX_NAMES
    }
    _require(not remaining, f"deferred indexes {sorted(remaining)} survived the DROP; refused")
    return len(records), {
        "deferred_index_count": len(records),
        "deferred_index_names": [name for _o, name, _t, _s in records],
        "deferred_index_set_identity": set_identity,
    }


def _stage_reduced_parser_run(
    connection: sqlite3.Connection,
    aliases: Sequence[str],
    ctx: _StageContext,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S2: the accepted reduced parser-run row, under containment, witnessed durably."""
    with write_containment(connection):
        reduced = _reduced_parser_run(
            connection,
            aliases,
            contract=ctx.contract,
            statement_runner=instr.consolidation_runner,
        )
    return 1, {
        "parser_run_id": reduced.parser_run_id,
        "parser_id": reduced.parser_id,
        "parser_version": reduced.parser_version,
        "outcome": reduced.outcome,
        "parsed": reduced.parsed,
        "quarantined": reduced.quarantined,
        "parser_state": reduced.parser_state,
        "duplicate_identities": list(reduced.duplicate_identities),
        "row_count": instr.count(connection, "census_parser_runs"),
    }


def _stage_table_load(
    connection: sqlite3.Connection,
    aliases: Sequence[str],
    ctx: _StageContext,
    stage: L2Stage,
    units: Sequence[AppliedUnit],
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S3..S10: one table's accepted key-sorted load or first/last reduction, under containment."""
    table = str(stage.table)
    runner = instr.consolidation_runner
    with write_containment(connection):
        if _MERGE_STRATEGY[table] == "keyed_first_last":
            _keyed_first_last_load(connection, table, aliases, statement_runner=runner)
        else:
            _sorted_bulk_load(connection, table, aliases, statement_runner=runner)
        if table == "census_parsed_records":
            reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
            _apply_duplicate_identities(connection, reduced, statement_runner=runner)
    count = instr.count(connection, table)
    return count, {"table": table, "row_count": count}


def _fetched(
    instr: _StageInstrumentation, connection: sqlite3.Connection, sql: str, operation: str
) -> sqlite3.Row:
    """One registered static ``fetchall`` statement's first row, executed under a journal."""
    rows = cast(
        "Sequence[sqlite3.Row]",
        instr.execute(connection, sql, (), operation=operation, kind=STATEMENT_KIND_FETCHALL),
    )
    return rows[0]


def _stage_witness_rank(
    connection: sqlite3.Connection,
    aliases: Sequence[str],
    units: Sequence[AppliedUnit],
    stage: L2Stage,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S11: the level-2 witness ranking, persisted -- the same window function, durable."""
    _require_not_derived(units, stage)
    _require(
        instr.count(connection, L2_WITNESS_RANK_TABLE) == 0,
        f"{L2_WITNESS_RANK_TABLE} is not empty before S11; refused rather than appended to",
    )
    union = _union_all(
        aliases,
        "census_accessions",
        "accession_plain, source_observation_id, parsed_record_id, first_observed_at_utc",
        extra=" AS chunk_ordinal",
    )
    instr.execute(
        connection,
        f"INSERT INTO main.{L2_WITNESS_RANK_TABLE} "  # noqa: S608
        "(accession_plain, source_observation_id, parsed_record_id, first_observed_at_utc, "
        "chunk_ordinal, witness_rank, witnesses) "
        "SELECT accession_plain, source_observation_id, parsed_record_id, first_observed_at_utc, "
        "chunk_ordinal, "
        "ROW_NUMBER() OVER (PARTITION BY accession_plain ORDER BY chunk_ordinal) AS witness_rank, "
        "COUNT(*) OVER (PARTITION BY accession_plain) AS witnesses "
        f"FROM ({union})",
        (),
        operation="witness_rank.insert",
        kind=STATEMENT_KIND_EXECUTE,
    )
    count = instr.count(connection, L2_WITNESS_RANK_TABLE)
    contested = _fetched(instr, connection, _SQL_S11_CONTESTED, "witness_rank.contested")
    return count, {"row_count": count, "contested": int(contested["n"])}


def _stage_observation_corrections(
    connection: sqlite3.Connection,
    units: Sequence[AppliedUnit],
    stage: L2Stage,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S12: the additive global loser upgrade, persisted -- the accepted statements, durable.

    The two ``INSERT ... SELECT`` shapes of :func:`stage_first_witness_corrections` over the
    persisted ranking, with the accepted rendering functions reached as the deterministic SQL
    user functions §21 re-registered. No Python statement runs per accession or per rival.
    """
    _require_not_derived(units, stage)
    _require(
        instr.count(connection, L2_CORRECTIONS_TABLE) == 0,
        f"{L2_CORRECTIONS_TABLE} is not empty before S12; refused rather than appended to",
    )
    orphaned_winners = _fetched(
        instr, connection, _SQL_S12_ORPHANED_WINNERS, "corrections.orphaned_winners"
    )
    _require(
        int(orphaned_winners["n"]) == 0,
        "a contested accession has no loaded canonical row between load and correction; the "
        "consolidation is refused rather than corrected against a row that is not there",
    )
    orphaned_rivals = _fetched(
        instr, connection, _SQL_S12_ORPHANED_RIVALS, "corrections.orphaned_rivals"
    )
    _require(
        int(orphaned_rivals["n"]) == 0,
        "a rival witness's parsed record is absent at correction time; the consolidation is "
        "refused rather than materialized from nothing",
    )
    instr.execute(
        connection,
        _SQL_S12_INSERT_WINNERS,
        (),
        operation="corrections.insert_winners",
        kind=STATEMENT_KIND_EXECUTE,
    )
    instr.execute(
        connection,
        _SQL_S12_INSERT_RIVALS,
        (),
        operation="corrections.insert_rivals",
        kind=STATEMENT_KIND_EXECUTE,
    )
    summary = _fetched(instr, connection, _SQL_S12_SUMMARY, "corrections.summary")
    staged = int(summary["staged"])
    return staged, {
        "contested": int(summary["contested"]),
        "rows_staged": staged,
        "row_count": staged,
    }


def _successor_load_accession_observations(
    connection: sqlite3.Connection, aliases: Sequence[str], instr: _StageInstrumentation
) -> None:
    """S13's load: the accepted single sorted load, reading the PERSISTED corrections."""
    columns = _columns(connection, "census_accession_observations")
    projection = ", ".join(columns)
    parts = [
        f"SELECT {projection}, {ordinal} AS chunk_ordinal, 0 AS priority "  # noqa: S608
        f"FROM {alias}.census_accession_observations"
        for ordinal, alias in enumerate(aliases)
    ]
    parts.append(
        f"SELECT {projection}, 2147483647 AS chunk_ordinal, 1 AS priority "  # noqa: S608
        f"FROM main.{L2_CORRECTIONS_TABLE}"
    )
    union = " UNION ALL ".join(parts)
    instr.execute(
        connection,
        f"INSERT OR IGNORE INTO census_accession_observations ({projection}) "  # noqa: S608
        f"SELECT {projection} FROM ({union}) "
        "ORDER BY accession_observation_id, priority, chunk_ordinal",
        (),
        operation="load_accession_observations.insert",
        kind=STATEMENT_KIND_EXECUTE,
    )


def _stage_accession_observations(
    connection: sqlite3.Connection, aliases: Sequence[str], instr: _StageInstrumentation
) -> tuple[int, Mapping[str, object]]:
    """S13: the observation load over the intermediates plus the persisted corrections."""
    with write_containment(connection):
        _successor_load_accession_observations(connection, aliases, instr)
    count = instr.count(connection, "census_accession_observations")
    return count, {"table": "census_accession_observations", "row_count": count}


def _stage_edges_and_conflicts(
    connection: sqlite3.Connection, ctx: _StageContext, instr: _StageInstrumentation
) -> tuple[int, Mapping[str, object]]:
    """S14: the two accepted whole-observation derivations, once, under containment.

    The census derivations live in a module R19B may not edit; they receive the connection
    boundary proxy, which captures each statement's exact SQL immediately before sqlite3 sees it
    and performs the execution under a journal (D151-C31R2-R19B-C2 §20).
    """
    observed = cast("sqlite3.Connection", instr.proxy(connection))
    with write_containment(connection):
        CensusCatalog._candidate_edges(  # noqa: SLF001 - the accepted derivation
            observed, ctx.plan.source_observation_id, kind="company_name"
        )
        CensusCatalog._candidate_edges(  # noqa: SLF001
            observed, ctx.plan.source_observation_id, kind="ticker"
        )
        CensusCatalog._mark_accession_conflicts(observed)  # noqa: SLF001
    count = instr.count(connection, "census_candidate_lineage_edges")
    return count, {"table": "census_candidate_lineage_edges", "row_count": count}


def _stage_parser_state(
    connection: sqlite3.Connection,
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S15P: the accepted parser_state update -- production only, the one permitted column."""
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    with write_containment(connection):
        instr.execute(
            connection,
            _SQL_S15P_UPDATE,
            (reduced.parser_state, ctx.plan.source_instance_id),
            operation="parser_state.update",
            kind=STATEMENT_KIND_EXECUTE,
        )
    row = connection.execute(
        "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
        (ctx.plan.source_instance_id,),
    ).fetchone()
    observed = "" if row is None else str(row["parser_state"])
    _require(observed == reduced.parser_state, "the parser_state update did not land; refused")
    return 1, {"parser_state": observed}


def _stage_index_rebuild(
    connection: sqlite3.Connection, ctx: _StageContext, stage: L2Stage, instr: _StageInstrumentation
) -> tuple[int, Mapping[str, object]]:
    """S16.k: rebuild exactly one index from its PERSISTED DDL -- never from sqlite_master."""
    row = connection.execute(
        "SELECT ordinal, name, table_name, create_sql, set_identity "  # noqa: S608
        f"FROM main.{L2_DEFERRED_INDEXES_TABLE} WHERE name = ?",
        (stage.unit_id,),
    ).fetchone()
    if row is None:
        _stage_conflict(f"no persisted DDL exists for deferred index {stage.unit_id!r}")
    persisted = [
        {
            "ordinal": int(item["ordinal"]),
            "name": str(item["name"]),
            "table": str(item["table_name"]),
            "sql": str(item["create_sql"]),
        }
        for item in connection.execute(
            "SELECT ordinal, name, table_name, create_sql "  # noqa: S608
            f"FROM main.{L2_DEFERRED_INDEXES_TABLE} ORDER BY ordinal"
        )
    ]
    set_identity = _identity_of({"contract": L2_DEFERRED_INDEX_SET_CONTRACT, "indexes": persisted})
    expected_identity = str(ctx.stage_plan.body["expected_deferred_index_set_identity"])
    if set_identity != expected_identity or set_identity != str(row["set_identity"]):
        _stage_conflict(
            f"the persisted deferred-index set recomputes to {set_identity[:16]}... where the "
            f"StagePlan bound {expected_identity[:16]}...; a rebuild never executes DDL the "
            "plan did not seal"
        )
    instr.execute(
        connection,
        str(row["create_sql"]),
        (),
        operation="index_rebuild.create",
        kind=STATEMENT_KIND_EXECUTE,
    )
    stored = connection.execute(
        "SELECT sql, tbl_name FROM main.sqlite_master WHERE type = 'index' AND name = ?",
        (stage.unit_id,),
    ).fetchone()
    _require(
        stored is not None
        and str(stored["sql"]) == str(row["create_sql"])
        and str(stored["tbl_name"]) == str(row["table_name"]),
        f"index {stage.unit_id!r} did not rebuild to its exact persisted DDL; refused",
    )
    return 1, {
        "index": stage.unit_id,
        "table": str(row["table_name"]),
        "create_sql": str(row["create_sql"]),
        "deferred_index_set_identity": str(row["set_identity"]),
    }


def _counter_batch(ctx: _StageContext, stage: L2Stage) -> tuple[PlanWitnessSource, ...]:
    batch = int(cast("int", stage.batch))
    return ctx.counter_sources[batch * MERGE_FAN_IN : (batch + 1) * MERGE_FAN_IN]


def _stage_counter_catalog_batch(
    connection: sqlite3.Connection,
    aliases: Sequence[str],
    ctx: _StageContext,
    stage: L2Stage,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S17A[n]: every chunk's canonical accession rows for one fan-in batch, persisted."""
    batch = _counter_batch(ctx, stage)
    _require(len(aliases) == len(batch), "the catalog batch attachments do not match the batch")
    rows = 0
    for alias, item in zip(aliases, batch, strict=True):
        cursor = cast(
            "sqlite3.Cursor",
            instr.execute(
                connection,
                f"INSERT INTO main.{L2_PLAN_WITNESS_TABLE} "  # noqa: S608
                "(accession_plain, parsed_record_id, chunk_ordinal) "
                "SELECT accession_plain, parsed_record_id, ? "
                f"FROM {alias}.census_accessions",
                (item.ordinal,),
                operation="counter_catalog.insert",
                kind=STATEMENT_KIND_EXECUTE,
            ),
        )
        rows += int(cursor.rowcount)
    return rows, {
        "batch": stage.batch,
        "chunk_ordinals": [item.ordinal for item in batch],
        "rows": rows,
        "row_count": instr.count(connection, L2_PLAN_WITNESS_TABLE),
    }


def _stage_counter_ledger_batch(
    connection: sqlite3.Connection,
    aliases: Sequence[str],
    ctx: _StageContext,
    stage: L2Stage,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S17B[n]: every chunk's first-witness ledger for one fan-in batch, persisted."""
    batch = _counter_batch(ctx, stage)
    _require(len(aliases) == len(batch), "the ledger batch attachments do not match the batch")
    rows = 0
    for alias in aliases:
        cursor = cast(
            "sqlite3.Cursor",
            instr.execute(
                connection,
                f"INSERT INTO main.{L2_PLAN_LEDGER_TABLE} "  # noqa: S608
                "(native_identity, member_ordinal, record_ordinal, delta_materialized) "
                "SELECT native_identity, member_ordinal, record_ordinal, delta_materialized "
                f"FROM {alias}.chunk_first_witness",
                (),
                operation="counter_ledger.insert",
                kind=STATEMENT_KIND_EXECUTE,
            ),
        )
        rows += int(cursor.rowcount)
    return rows, {
        "batch": stage.batch,
        "chunk_ordinals": [item.ordinal for item in batch],
        "rows": rows,
        "row_count": instr.count(connection, L2_PLAN_LEDGER_TABLE),
    }


def _stage_counters_finalize(
    connection: sqlite3.Connection,
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    stage: L2Stage,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """S17C: the four whole-F0 counters over the persisted plan witnesses -- D151-C15 R1.

    The accepted derivation's ranking, orphan checks, two counts and member-delta reduction,
    each reading the persisted relations by their successor names. The closure keys stay
    distinct: ``accession_plain`` for the witness ranking, ``native_identity`` for the
    member-delta reduction.
    """
    _require_not_derived(units, stage)
    _require(
        instr.count(connection, L2_PLAN_WITNESS_RANK_TABLE) == 0
        and instr.count(connection, L2_MEMBER_DELTA_TABLE) == 0,
        "the counter relations are not empty before S17C; refused rather than appended to",
    )
    expected_batches = -(-len(ctx.counter_sources) // MERGE_FAN_IN)
    seen = {
        unit.stage_id
        for unit in units
        if unit.unit_kind in {_KIND_COUNTER_CATALOG, _KIND_COUNTER_LEDGER}
    }
    _require(
        len(seen) == 2 * expected_batches,
        f"S17C requires every counter batch committed; {len(seen)} of {2 * expected_batches} are",
    )
    instr.execute(
        connection,
        _SQL_S17C_INSERT_RANK,
        (),
        operation="counters.insert_rank",
        kind=STATEMENT_KIND_EXECUTE,
    )
    orphaned_winners = _fetched(
        instr, connection, _SQL_S17C_ORPHANED_WINNERS, "counters.orphaned_winners"
    )
    _require(
        int(orphaned_winners["n"]) == 0,
        "a contested accession of the plan has no canonical row in the final world; the whole-F0 "
        "counters are refused rather than derived against a row that is not there",
    )
    orphaned_rivals = _fetched(
        instr, connection, _SQL_S17C_ORPHANED_RIVALS, "counters.orphaned_rivals"
    )
    _require(
        int(orphaned_rivals["n"]) == 0,
        "a chunk's local-first witness has no parsed record in the final world; the whole-F0 "
        "counters are refused rather than derived from nothing",
    )
    contested = _fetched(instr, connection, _SQL_S17C_CONTESTED, "counters.contested")
    winner_rows = _fetched(instr, connection, _SQL_S17C_WINNER_ROWS, "counters.winner_rows")
    rival_rows = _fetched(instr, connection, _SQL_S17C_RIVAL_ROWS, "counters.rival_rows")
    instr.execute(
        connection,
        _SQL_S17C_INSERT_MEMBER_DELTA,
        (),
        operation="counters.insert_member_delta",
        kind=STATEMENT_KIND_EXECUTE,
    )
    deltas = _fetched(instr, connection, _SQL_S17C_DELTAS, "counters.deltas")
    rank_rows = instr.count(connection, L2_PLAN_WITNESS_RANK_TABLE)
    return rank_rows, {
        "first_witness_accessions_corrected": int(contested["n"]),
        "first_witness_rows_staged": int(winner_rows["n"]) + int(rival_rows["n"]),
        "evidence_members_corrected": int(deltas["members"]),
        "evidence_delta": int(deltas["total"]),
        "row_count": rank_rows,
        "member_delta_rows": int(deltas["members"]),
    }


# --------------------------------------------------------------------------- #
# Cross-store stages -- §36: never atomic across stores, always convergent
# --------------------------------------------------------------------------- #
def _sidecar_is_complete_readonly(path: Path, ctx: _StageContext) -> bool:
    """Whether a present sidecar holds the finished source row, read through ``mode=ro``.

    A raw read-only handle rather than the accepted class: the class constructor upserts its
    schema rows and would rewrite bytes of an artifact this classification must preserve.
    """
    for suffix in ("-wal", "-shm"):
        if os.path.lexists(path.with_name(path.name + suffix)):
            return False
    try:
        reader = sqlite3.connect(
            f"{path.absolute().as_uri()}?mode=ro", uri=True, isolation_level=None
        )
    except sqlite3.Error:
        return False
    try:
        reader.row_factory = sqlite3.Row
        try:
            row = reader.execute(
                "SELECT members, completeness_digest FROM compact_source_evidence "
                "WHERE source_observation_id = ?",
                (ctx.plan.source_observation_id,),
            ).fetchone()
        except sqlite3.Error:
            return False
    finally:
        reader.close()
    return (
        row is not None
        and int(row["members"]) == ctx.plan.total_members
        and bool(row["completeness_digest"])
    )


def _prepare_sidecar(ctx: _StageContext, instr: _StageInstrumentation) -> Mapping[str, object]:
    """S18's out-of-catalog half: build or authenticate the sidecar, never overwrite one.

    The path decision is journaled FIRST (D151-R19B-C2-R2): the sidecar's file state selects
    BUILD (absent) or AUTHENTICATE (present and complete); a present, incomplete sidecar selects
    nothing and is a conflict. Every material BUILD statement and both authenticate-time folds
    run through the sidecar runner under the same watchdog model as the working catalog.
    """
    path = ctx.world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME
    state = _file_state(path, digest=False)
    complete = state.lstat_class == "file" and _sidecar_is_complete_readonly(path, ctx)
    if state.lstat_class == "absent":
        selected: str | None = _S18_PATH_BUILD
    elif complete:
        selected = _S18_PATH_AUTHENTICATE
    else:
        selected = None
    instr.record_path_decision(
        sidecar_state={**dict(state.as_record()), "complete": complete},
        selected=selected,
        expected_path=_S18_PATH_BUILD if state.lstat_class == "absent" else _S18_PATH_AUTHENTICATE,
    )
    if selected == _S18_PATH_BUILD:
        completeness, manifest_digest, totals, _level_two_evidence = _merge_sidecar(
            sidecar_path=path,
            inputs=cast("Sequence[ChunkInput]", ctx.intermediates),
            plan=ctx.plan,
            source_id=ctx.plan.source_id,
            statement_runner=instr.sidecar_runner,
        )
    elif selected == _S18_PATH_AUTHENTICATE:
        reopened = CompactEvidenceSidecar(path, statement_runner=instr.sidecar_runner)
        try:
            evidence = reopened.source_evidence(ctx.plan.source_observation_id)
            manifest_digest = reopened.member_manifest_digest(ctx.plan.source_observation_id)
        finally:
            reopened.close()
        _require(evidence is not None, "the sidecar carries no source evidence row; refused")
        assert evidence is not None  # noqa: S101 - narrowed by the refusal above
        completeness = str(evidence["completeness_digest"])
        totals = {
            "members": int(cast("int", evidence["members"])),
            "records": int(cast("int", evidence["records"])),
            "omitted": int(cast("int", evidence["omitted_field_observations"])),
            "materialized": int(cast("int", evidence["materialized_field_observations"])),
        }
    else:
        _stage_conflict(
            f"the sidecar {path.name!r} is present but is {state.lstat_class} or incomplete; a "
            "partial or conflicting sidecar is preserved exactly as it is and never rebuilt"
        )
    reopened = CompactEvidenceSidecar(path, statement_runner=instr.sidecar_runner)
    try:
        identity = reopened.identity()
    finally:
        reopened.close()
    for suffix in ("-wal", "-shm"):
        _require(
            not os.path.lexists(path.with_name(path.name + suffix)),
            f"the sidecar left a {suffix} beside it after close; refused",
        )
    sha256, length = file_sha256(path)
    _fsync_path(path)
    return {
        "completeness_digest": completeness,
        "member_manifest_digest": manifest_digest,
        "totals": dict(totals),
        "sidecar_identity": identity,
        "sidecar_sha256": sha256,
        "sidecar_byte_length": length,
    }


def _fsync_path(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _derived_outcome(ctx: _StageContext, units: Sequence[AppliedUnit]) -> SingleSourceOutcome:
    """The accepted F0 outcome re-derived from the committed S2 and S18 witnesses."""
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    sidecar = _witness_of(units, _STAGE_SIDECAR)
    totals = cast("Mapping[str, object]", sidecar["totals"])
    return derived_f0_outcome(
        plan=ctx.plan,
        state=ctx.state,
        reduced=reduced,
        members=_stored_int(totals["members"], "members"),
        records=_stored_int(totals["records"], "records"),
        omitted=_stored_int(totals["omitted"], "omitted"),
        materialized=_stored_int(totals["materialized"], "materialized"),
        completeness_digest=str(sidecar["completeness_digest"]),
    )


def _require_bound_plan_state(ctx: _StageContext) -> None:
    """The accepted plan state read now equals the one the StagePlan sealed."""
    policies = cast("Mapping[str, object]", ctx.stage_plan.body["semantic_policy_identities"])
    bound = cast("Mapping[str, object]", policies["accepted_plan_state"])
    observed = {
        "plan_position": ctx.state.plan_position,
        "plan_source_count": ctx.state.plan_source_count,
        "parser_state_before": ctx.state.parser_state_before,
        "disposition": ctx.state.disposition,
        "plan_fingerprint": ctx.state.plan_fingerprint,
        "observation_id": ctx.state.observation_id,
        "artifact_sha256": ctx.state.artifact_sha256,
        "artifact_byte_length": ctx.state.artifact_byte_length,
    }
    if dict(bound) != observed:
        _stage_conflict("the accepted plan state moved since the StagePlan was sealed")


def _stage_outcome(
    ctx: _StageContext, units: Sequence[AppliedUnit]
) -> tuple[int, Mapping[str, object]]:
    """S19: the accepted D140-R12 gate over the derived outcome; nothing below it on refusal."""
    _require_bound_plan_state(ctx)
    outcome = _derived_outcome(ctx, units)
    require_f0_success(outcome)
    return 0, {
        "disposition": outcome.outcome.disposition,
        "parser_run_id": outcome.outcome.parser_run_id,
        "parser_state_before": outcome.outcome.parser_state_before,
        "parser_state_after": outcome.outcome.parser_state_after,
        "parsed_records": outcome.outcome.parsed_records,
        "quarantined_records": outcome.outcome.quarantined_records,
        "members": outcome.members,
        "records": outcome.records,
        "omitted_field_observations": outcome.omitted_field_observations,
        "materialized_field_observations": outcome.materialized_field_observations,
        "completeness_digest": outcome.completeness_digest,
        "f0_success": True,
    }


def _progress_identity(progress: SourceProgress) -> str:
    return _identity_of(
        {
            "source_instance_id": progress.source_instance_id,
            "state": progress.state,
            "parts_committed": progress.parts_committed,
            "batches_committed": progress.batches_committed,
        }
    )


def _prepare_mark_parsed(ctx: _StageContext, units: Sequence[AppliedUnit]) -> Mapping[str, object]:
    """S20P's run-progress half: mark parsed once, or hold an existing mark to the expectation."""
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    ledger = RunProgressLedger(ctx.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        progress = ledger.progress(ctx.plan.source_instance_id)
        if progress is None:
            _stage_conflict("the run-progress ledger carries no source row to mark parsed")
        if progress.state == "in_progress":
            ledger.mark_parsed(
                ctx.plan.source_instance_id, parts=ctx.plan.total_members, batches=reduced.parsed
            )
        elif progress.state != "parsed" or (
            progress.parts_committed,
            progress.batches_committed,
        ) != (
            ctx.plan.total_members,
            reduced.parsed,
        ):
            _stage_conflict(
                f"the run-progress ledger records state {progress.state!r} "
                f"({progress.parts_committed}/{progress.batches_committed}) where 'parsed' over "
                f"{ctx.plan.total_members}/{reduced.parsed} is the only convergent state"
            )
        after = ledger.progress(ctx.plan.source_instance_id)
    finally:
        ledger.close()
    _require(after is not None and after.state == "parsed", "mark_parsed did not land; refused")
    assert after is not None  # noqa: S101 - narrowed above
    return {
        "state": after.state,
        "parts_committed": after.parts_committed,
        "batches_committed": after.batches_committed,
        "progress_identity": _progress_identity(after),
    }


def _prepare_reauthentication(
    ctx: _StageContext, instr: _StageInstrumentation
) -> Mapping[str, object]:
    """S21P / S20C's out-of-catalog half: every StagePlan intermediate and selected request."""
    resolved = cast(
        "tuple[IntermediateInput, ...]",
        instr.record_callable(
            _OP_REAUTHENTICATE,
            lambda: _resolve_route_intermediates(ctx.request, ctx.plan, ctx.schedule, ctx.route),
            facts={"input_group_count": len(ctx.intermediates)},
        ),
    )
    descriptors = [_successor_intermediate_descriptor(item) for item in resolved]
    bound = [dict(item) for item in ctx.stage_plan.intermediates]
    _require(
        len(descriptors)
        == _stored_int(ctx.stage_plan.body["input_group_count"], "input_group_count"),
        f"{len(descriptors)} intermediates resolved where the StagePlan enumerates "
        f"{ctx.stage_plan.body['input_group_count']}",
    )
    if [dict(item) for item in descriptors] != bound:
        _stage_conflict(
            "a StagePlan-enumerated intermediate or its selected request changed after the "
            "merge: the re-derived descriptors differ from the sealed ones, and no checkpoint or "
            "result is published over changed inputs"
        )
    return {
        "input_group_count": len(descriptors),
        "descriptor_identity": _identity_of({"intermediates": descriptors}),
        "receipt_document_sha256": [str(item["receipt_document_sha256"]) for item in descriptors],
        "request_sha256": [
            str(cast("Mapping[str, object]", item["group_request_provenance"])["sha256"])
            for item in descriptors
        ],
    }


def _phase_checkpoint(ctx: _StageContext, units: Sequence[AppliedUnit]) -> PhaseCheckpoint:
    outcome = _derived_outcome(ctx, units)
    initialize = _witness_of(units, _STAGE_INITIALIZE)
    started_at_utc = min(item.receipt.earliest_input_started_at_utc for item in ctx.intermediates)
    return PhaseCheckpoint(
        contract=PHASE_RESTART_CONTRACT,
        phase=PHASE_F0,
        status=PHASE_STATUS_COMPLETE,
        run_id=ctx.request.run_id,
        source_instance_id=ctx.plan.source_instance_id,
        execution_identity=phase_execution_identity(
            repository=ctx.repository, batch_size=ctx.contract.batch_size
        ),
        repository_head_sha=ctx.repository.head_sha,
        repository_tree_sha=ctx.repository.tree_sha,
        catalog_source_sha256=ctx.contract.catalog_source_sha256,
        migration_head=ctx.contract.migration_head,
        plan_fingerprint=ctx.state.plan_fingerprint,
        completed_at_utc=utc_now(),
        pid=os.getpid(),
        rss_peak_bytes_at_start=None,
        rss_peak_bytes_at_terminal=process_peak_resident_bytes(),
        payload=dict(
            derived_f0_payload(
                outcome=outcome,
                state=ctx.state,
                plan=ctx.plan,
                started_at_utc=started_at_utc,
                catalog_source_sha256=ctx.contract.catalog_source_sha256,
                work_root_free_bytes_before=_stored_int(
                    initialize["free_before_bytes"], "free_before_bytes"
                ),
                capacity_observations=ctx.request.capacity_observations,
            )
        ),
    )


def _checkpoint_core(checkpoint: PhaseCheckpoint) -> Mapping[str, object]:
    """The deterministic core of a phase checkpoint -- everything but the process facts."""
    record = dict(checkpoint.as_record())
    for key in ("completed_at_utc", "pid", "rss_peak_bytes_at_start", "rss_peak_bytes_at_terminal"):
        record.pop(key, None)
    return record


def _prepare_f0_checkpoint(
    ctx: _StageContext, units: Sequence[AppliedUnit]
) -> Mapping[str, object]:
    """S22P's run-progress half: write the F0 phase checkpoint once, or hold the existing one."""
    expected = _phase_checkpoint(ctx, units)
    ledger = RunProgressLedger(ctx.world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        existing = read_phase_checkpoint(ledger, PHASE_F0)
        if existing is None:
            write_phase_checkpoint(ledger, expected)
            existing = read_phase_checkpoint(ledger, PHASE_F0)
    finally:
        ledger.close()
    _require(existing is not None, "the F0 phase checkpoint did not land; refused")
    assert existing is not None  # noqa: S101 - narrowed above
    if dict(_checkpoint_core(existing)) != dict(_checkpoint_core(expected)):
        _stage_conflict(
            "the run-progress ledger already carries an F0 phase checkpoint that is not the one "
            "this world derives; a checkpoint is never overwritten and never continued under"
        )
    return {
        "execution_identity": existing.execution_identity,
        "checkpoint_identity": _identity_of(dict(existing.as_record())),
        "core_identity": _identity_of(dict(_checkpoint_core(existing))),
        "completed_at_utc": existing.completed_at_utc,
        "pid": existing.pid,
    }


def _plan_counters(units: Sequence[AppliedUnit]) -> tuple[int, int, int, int]:
    witness = _witness_of(units, _STAGE_COUNTERS_FINALIZE)
    return (
        _stored_int(
            witness["first_witness_accessions_corrected"], "first_witness_accessions_corrected"
        ),
        _stored_int(witness["first_witness_rows_staged"], "first_witness_rows_staged"),
        _stored_int(witness["evidence_members_corrected"], "evidence_members_corrected"),
        _stored_int(witness["evidence_delta"], "evidence_delta"),
    )


def _result_ready_core(
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    connection: sqlite3.Connection,
    instr: _StageInstrumentation,
) -> Mapping[str, object]:
    """The semantic core the RESULT_READY binding seals: what the final record will say."""
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    sidecar = _witness_of(units, _STAGE_SIDECAR)
    counters = _plan_counters(units)
    outcome = _witness_of(units, _STAGE_OUTCOME)
    counts = table_row_counts(cast("sqlite3.Connection", instr.proxy(connection)))
    return {
        "stage_plan_identity": ctx.stage_plan.identity,
        "parser_run_id": reduced.parser_run_id,
        "run_outcome": reduced.outcome,
        "parser_state_after": reduced.parser_state,
        "parsed_records": reduced.parsed,
        "quarantined_records": reduced.quarantined,
        "totals": dict(cast("Mapping[str, object]", sidecar["totals"])),
        "completeness_digest": str(sidecar["completeness_digest"]),
        "member_manifest_digest": str(sidecar["member_manifest_digest"]),
        "first_witness_accessions_corrected": counters[0],
        "first_witness_rows_staged": counters[1],
        "evidence_members_corrected": counters[2],
        "evidence_delta": counters[3],
        "table_row_counts": dict(sorted(counts.items())),
        "f0_success": bool(outcome["f0_success"]),
    }


def _publish_final_receipt(
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    *,
    manifest: ArtifactManifest,
    observability: Mapping[str, object],
) -> Mapping[str, object]:
    """S23P's LAST act: the accepted FinalWorldReceipt, create-once, over the closed world."""
    core = _witness_of(units, _STAGE_FINAL_RECEIPT)
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    totals = cast("Mapping[str, object]", core["totals"])
    counts = {
        str(key): _stored_int(value, str(key))
        for key, value in cast("Mapping[str, object]", core["table_row_counts"]).items()
    }
    chunk_inputs: list[Mapping[str, object]] = []
    for item in ctx.intermediates:
        chunk_inputs.extend(item.receipt.chunk_inputs)
    receipt = FinalWorldReceipt(
        contract=FINAL_WORLD_RECEIPT_CONTRACT,
        consolidation_contract=MULTIPASS_CONSOLIDATION_CONTRACT,
        plan_digest=ctx.plan.plan_digest,
        source_instance_id=ctx.plan.source_instance_id,
        source_observation_id=ctx.plan.source_observation_id,
        source_sha256=ctx.plan.source_sha256,
        repository_head_sha=ctx.repository.head_sha,
        repository_tree_sha=ctx.repository.tree_sha,
        catalog_source_sha256=ctx.contract.catalog_source_sha256,
        execution_contract_identity=ctx.contract.contract_identity,
        chunk_count=ctx.plan.chunk_count,
        chunk_inputs=tuple(dict(item) for item in chunk_inputs),
        chunks_unchanged=True,
        parser_run_id=reduced.parser_run_id,
        run_outcome=reduced.outcome,
        parser_state_after=reduced.parser_state,
        members=_stored_int(totals["members"], "members"),
        records=_stored_int(totals["records"], "records"),
        parsed_records=reduced.parsed,
        quarantined_records=reduced.quarantined,
        omitted_field_observations=_stored_int(totals["omitted"], "omitted"),
        materialized_field_observations=_stored_int(totals["materialized"], "materialized"),
        completeness_digest=str(core["completeness_digest"]),
        member_manifest_digest=str(core["member_manifest_digest"]),
        table_row_counts=counts,
        first_witness_accessions_corrected=_stored_int(
            core["first_witness_accessions_corrected"], "c"
        ),
        first_witness_rows_staged=_stored_int(core["first_witness_rows_staged"], "c"),
        evidence_members_corrected=_stored_int(core["evidence_members_corrected"], "c"),
        evidence_delta=_stored_int(core["evidence_delta"], "c"),
        manifest=manifest,
        completed_at_utc=utc_now(),
        status="complete",
        successor_observability=dict(observability),
    )
    path = ctx.world_directory / FINAL_WORLD_RECEIPT_FILENAME
    # LAST. Nothing is written after this.
    write_once_json(path, dict(receipt.as_record()))
    return read_receipt_document(path, contract=FINAL_WORLD_RECEIPT_CONTRACT)


def _publish_calibration_result(
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    *,
    manifest: ArtifactManifest,
    observability: Mapping[str, object],
) -> CalibrationSubsetResult:
    """S21C's LAST act: the accepted CalibrationSubsetResult, sealed and create-once."""
    core = _witness_of(units, _STAGE_CALIBRATION_RESULT)
    initialize = _witness_of(units, _STAGE_INITIALIZE)
    reduced = _reduced_run_from_witness(_witness_of(units, _STAGE_REDUCED_PARSER_RUN))
    totals = cast("Mapping[str, object]", core["totals"])
    counts = {
        str(key): _stored_int(value, str(key))
        for key, value in cast("Mapping[str, object]", core["table_row_counts"]).items()
    }
    plan = ctx.plan
    _require(isinstance(plan, CalibrationSubsetPlan), "the calibration result needs a subset plan")
    subset = cast("CalibrationSubsetPlan", plan)
    envelope = ctx.proof.envelope
    _require(envelope is not None, "the calibration result needs the child's envelope")
    assert envelope is not None  # noqa: S101 - narrowed above
    started_at_utc = min(item.receipt.earliest_input_started_at_utc for item in ctx.intermediates)
    result = CalibrationSubsetResult(
        contract=CALIBRATION_SUBSET_RESULT_CONTRACT,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        plan_digest=subset.plan_digest,
        merge_schedule_digest=ctx.schedule.schedule_digest,
        run_id=ctx.request.run_id,
        source_instance_id=subset.source_instance_id,
        source_observation_id=subset.source_observation_id,
        source_sha256=subset.source_sha256,
        source_byte_length=subset.source_byte_length,
        member_order_digest=subset.member_order_digest,
        selected_member_order_digest=subset.selected_member_order_digest,
        shard_parent_binding_digest=subset.shard_parent_binding_digest,
        primary_prefix_members=subset.primary_prefix_members,
        selected_shard_members=subset.selected_shard_members,
        excluded_shard_members=subset.excluded_shard_members,
        selected_members=subset.selected_members,
        full_total_members=subset.full_total_members,
        repository_head_sha=ctx.repository.head_sha,
        repository_tree_sha=ctx.repository.tree_sha,
        catalog_source_sha256=ctx.contract.catalog_source_sha256,
        execution_contract_identity=ctx.contract.contract_identity,
        chunk_count=subset.chunk_count,
        intermediate_count=len(ctx.intermediates),
        parser_run_id=reduced.parser_run_id,
        run_outcome=reduced.outcome,
        parser_state_after="chunk_local",
        world_parser_state=str(core["world_parser_state"]),
        members=_stored_int(totals["members"], "members"),
        records=_stored_int(totals["records"], "records"),
        parsed_records=reduced.parsed,
        quarantined_records=reduced.quarantined,
        omitted_field_observations=_stored_int(totals["omitted"], "omitted"),
        materialized_field_observations=_stored_int(totals["materialized"], "materialized"),
        completeness_digest=str(core["completeness_digest"]),
        member_manifest_digest=str(core["member_manifest_digest"]),
        table_row_counts=counts,
        first_witness_accessions_corrected=_stored_int(
            core["first_witness_accessions_corrected"], "c"
        ),
        first_witness_rows_staged=_stored_int(core["first_witness_rows_staged"], "c"),
        evidence_members_corrected=_stored_int(core["evidence_members_corrected"], "c"),
        evidence_delta=_stored_int(core["evidence_delta"], "c"),
        storage_admission=dict(cast("Mapping[str, object]", initialize["admission"])),
        admission_event_identity=str(initialize["admission_event_identity"]),
        envelope_sha256=envelope.sha256,
        pid=os.getpid(),
        rss_peak_bytes=process_peak_resident_bytes(),
        started_at_utc=started_at_utc,
        completed_at_utc=utc_now(),
        manifest=manifest,
        status="complete",
        result_identity="",
        successor_observability=dict(observability),
    )
    sealed = replace(result, result_identity=result.identity())
    # LAST. Nothing is written after this.
    write_once_canonical_json(
        ctx.world_directory / CALIBRATION_SUBSET_RESULT_FILENAME, dict(sealed.as_record())
    )
    return read_calibration_subset_result(ctx.world_directory / CALIBRATION_SUBSET_RESULT_FILENAME)


# --------------------------------------------------------------------------- #
# Stage classification -- §31
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _Progress:
    """What the committed evidence says: every applied unit, what comes next, and its label.

    ``classification`` is one of ``STAGE_EXECUTE`` (the next stage has no unit and no receipt),
    ``STAGE_COMMITTED_RECEIPT_PENDING`` (the last unit is committed and its receipt is absent)
    and ``STAGE_COMPLETE`` (every stage is applied and receipted); ``STAGE_CONFLICT`` is never a
    label, it is raised.
    """

    units: tuple[AppliedUnit, ...]
    next_stage: L2Stage | None
    pending: L2Stage | None
    terminal_complete: bool
    classification: str


def _terminal_record_present(ctx: _StageContext, stage: L2Stage) -> bool:
    if stage.kind == _KIND_FINAL_RECEIPT:
        return os.path.lexists(ctx.world_directory / FINAL_WORLD_RECEIPT_FILENAME)
    if stage.kind == _KIND_CALIBRATION_RESULT:
        return os.path.lexists(ctx.world_directory / CALIBRATION_SUBSET_RESULT_FILENAME)
    return False


def _is_terminal(stage: L2Stage) -> bool:
    return stage.kind in {_KIND_FINAL_RECEIPT, _KIND_CALIBRATION_RESULT}


def _verify_committed_witness(
    connection: sqlite3.Connection,
    world: WorkingCatalog,
    ctx: _StageContext,
    unit: AppliedUnit,
    units: Sequence[AppliedUnit],
) -> None:
    """§31 H: a committed output witness that no longer describes the world is a conflict."""
    witness = unit.outcome_witness
    if unit.unit_kind in {_KIND_TABLE_LOAD, _KIND_OBSERVATION_LOAD, _KIND_EDGES}:
        table = str(witness["table"])
        observed = _count(connection, table)
        if observed != _stored_int(witness["row_count"], "row_count"):
            _stage_conflict(
                f"stage {unit.stage_id!r} committed {witness['row_count']} rows in {table!r} and "
                f"the world now holds {observed}"
            )
    elif unit.unit_kind in {_KIND_WITNESS_RANK, _KIND_CORRECTIONS, _KIND_COUNTERS_FINALIZE}:
        table = {
            _KIND_WITNESS_RANK: L2_WITNESS_RANK_TABLE,
            _KIND_CORRECTIONS: L2_CORRECTIONS_TABLE,
            _KIND_COUNTERS_FINALIZE: L2_PLAN_WITNESS_RANK_TABLE,
        }[unit.unit_kind]
        observed = _count(connection, table)
        if observed != _stored_int(witness["row_count"], "row_count"):
            _stage_conflict(
                f"stage {unit.stage_id!r} committed {witness['row_count']} rows in {table!r} and "
                f"the world now holds {observed}"
            )
    elif unit.unit_kind in {_KIND_COUNTER_CATALOG, _KIND_COUNTER_LEDGER}:
        # A batch appends to a relation later batches append to as well: the relation's count
        # is held to the SUM of every committed batch of this kind, checked at the latest one.
        table = {
            _KIND_COUNTER_CATALOG: L2_PLAN_WITNESS_TABLE,
            _KIND_COUNTER_LEDGER: L2_PLAN_LEDGER_TABLE,
        }[unit.unit_kind]
        same_kind = [item for item in units if item.unit_kind == unit.unit_kind]
        if same_kind and same_kind[-1].stage_ordinal == unit.stage_ordinal:
            expected = sum(_stored_int(item.outcome_witness["rows"], "rows") for item in same_kind)
            observed = _count(connection, table)
            if observed != expected or observed != _stored_int(witness["row_count"], "row_count"):
                _stage_conflict(
                    f"the committed counter batches of {unit.stage_id!r} sum to {expected} rows in "
                    f"{table!r} and the world now holds {observed}"
                )
    elif unit.unit_kind == _KIND_CAPTURE_DROP:
        present = {
            str(row["name"])
            for row in connection.execute(
                "SELECT name FROM main.sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
            )
        }
        rebuilt = {item.unit_id for item in units if item.unit_kind == _KIND_INDEX_REBUILD}
        expected_absent = set(EXPECTED_DEFERRED_INDEX_NAMES) - rebuilt
        if expected_absent & present:
            _stage_conflict(f"dropped indexes {sorted(expected_absent & present)} are present")
        persisted = _count(connection, L2_DEFERRED_INDEXES_TABLE)
        if persisted != len(EXPECTED_DEFERRED_INDEX_NAMES):
            _stage_conflict(f"{persisted} deferred-index rows persisted where 5 are required")
    elif unit.unit_kind == _KIND_INDEX_REBUILD:
        stored = connection.execute(
            "SELECT sql FROM main.sqlite_master WHERE type = 'index' AND name = ?", (unit.unit_id,)
        ).fetchone()
        if stored is None or str(stored["sql"]) != str(witness["create_sql"]):
            _stage_conflict(f"rebuilt index {unit.unit_id!r} is absent or its DDL moved")
    elif unit.unit_kind == _KIND_MARK_PARSED:
        progress = world.ledger.progress(ctx.plan.source_instance_id)
        if (
            progress is None
            or progress.state != "parsed"
            or _progress_identity(progress) != str(witness["progress_identity"])
        ):
            _stage_conflict(
                "a mark_parsed binding exists but the run-progress ledger is not parsed"
            )
    elif unit.unit_kind == _KIND_F0_CHECKPOINT:
        checkpoint = read_phase_checkpoint(world.ledger, PHASE_F0)
        if checkpoint is None or _identity_of(dict(checkpoint.as_record())) != str(
            witness["checkpoint_identity"]
        ):
            _stage_conflict(
                "an F0 checkpoint binding exists but the ledger's checkpoint is absent or differs"
            )
    elif unit.unit_kind == _KIND_SIDECAR:
        path = ctx.world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME
        state = _file_state(path)
        if state.lstat_class != "file" or state.sha256 != str(witness["sidecar_sha256"]):
            _stage_conflict("the bound sidecar is absent or its bytes moved since its binding")
    if unit.unit_kind in {
        _KIND_SIDECAR,
        _KIND_MARK_PARSED,
        _KIND_REAUTHENTICATE,
        _KIND_F0_CHECKPOINT,
        _KIND_FINAL_RECEIPT,
        _KIND_CALIBRATION_RESULT,
    }:
        binding = _cross_store_binding(connection, unit.stage_ordinal)
        if binding is None or str(binding["binding_identity"]) != str(witness["binding_identity"]):
            _stage_conflict(
                f"stage {unit.stage_id!r} has no cross-store binding row or a different one"
            )


def _classify(session: _WorldSession, ctx: _StageContext) -> _Progress:
    """§31 over the committed rows and the published receipts; every conflict is terminal."""
    stages = ctx.stages
    units = _applied_units(session.connection)
    ordinals = [unit.stage_ordinal for unit in units]
    if ordinals != list(range(len(units))):
        _stage_conflict(f"applied units are not contiguous from ordinal 0: {ordinals}")
    for unit in units:
        stage = stages[unit.stage_ordinal] if unit.stage_ordinal < len(stages) else None
        if stage is None or (stage.stage_id, stage.unit_id, stage.kind) != (
            unit.stage_id,
            unit.unit_id,
            unit.unit_kind,
        ):
            _stage_conflict(
                f"applied unit ordinal {unit.stage_ordinal} is not the StagePlan's stage"
            )
        if (
            unit.stage_plan_identity != session.stage_plan.identity
            or unit.stage_operation_identity != _stage_operation_identity(session.stage_plan, stage)
            or unit.tool_manifest_identity != session.stage_plan.tool_manifest_identity
        ):
            _stage_conflict(
                f"applied unit {unit.stage_id!r} binds another StagePlan, semantic operation or "
                "tool identity than this invocation"
            )
        expected_predecessor = (
            units[unit.stage_ordinal - 1].unit_identity
            if unit.stage_ordinal
            else session.stage_plan.identity
        )
        if unit.predecessor_unit_identity != expected_predecessor:
            _stage_conflict(
                f"applied unit {unit.stage_id!r} binds a predecessor that is not its predecessor"
            )
        _verify_committed_witness(session.connection, session.world, ctx, unit, units)
    # Receipts: every applied unit but possibly the last carries one; none exists beyond them.
    pending: L2Stage | None = None
    for index, stage in enumerate(stages):
        if _is_terminal(stage):
            present = _terminal_record_present(ctx, stage)
            applied = index < len(units)
            if present and not applied:
                _stage_conflict(
                    f"the terminal record for {stage.stage_id!r} exists with no RESULT_READY unit"
                )
            if applied and not present:
                pending = stage
            continue
        path = stage_receipt_path(ctx.receipt_root, stage)
        exists = os.path.lexists(path)
        if index < len(units):
            if not exists:
                if index == len(units) - 1:
                    pending = stage
                else:
                    _stage_conflict(
                        f"stage {stage.stage_id!r} is applied, a later stage is applied too, "
                        "and its receipt is absent"
                    )
                continue
            receipt = read_stage_receipt(path)
            unit = units[index]
            if (
                str(receipt["unit_identity"]) != unit.unit_identity
                or str(receipt["stage_plan_identity"]) != session.stage_plan.identity
                or str(receipt["stage_operation_identity"]) != unit.stage_operation_identity
            ):
                _stage_conflict(
                    f"stage {stage.stage_id!r}'s receipt does not describe its applied unit"
                )
        elif exists:
            _stage_conflict(
                f"a receipt exists for {stage.stage_id!r} with no applied unit: a receipt never "
                "outruns committed data"
            )
    next_stage = stages[len(units)] if len(units) < len(stages) else None
    if pending is not None:
        classification = _STAGE_COMMITTED_RECEIPT_PENDING
    elif next_stage is None:
        classification = _STAGE_COMPLETE
    else:
        classification = _STAGE_EXECUTE
    return _Progress(
        units=units,
        next_stage=next_stage,
        pending=pending,
        terminal_complete=next_stage is None and pending is None,
        classification=classification,
    )


# --------------------------------------------------------------------------- #
# The engine -- §30 step order, §28 initialization, §35 bounded reopen per stage
# --------------------------------------------------------------------------- #
def _attach_for_stage(
    connection: sqlite3.Connection, ctx: _StageContext, stage: L2Stage
) -> tuple[str, ...]:
    """ATTACH the stage's immutable inputs outside any transaction, at most nine."""
    if stage.attachments == _ATTACH_NONE:
        return ()
    if stage.attachments == _ATTACH_INTERMEDIATES:
        paths = [item.catalog_path for item in ctx.intermediates]
        prefix = "k"
    elif stage.attachments == _ATTACH_CATALOG_BATCH:
        paths = [item.catalog_path for item in _counter_batch(ctx, stage)]
        prefix = "pc"
    elif stage.attachments == _ATTACH_LEDGER_BATCH:
        paths = [item.witness_path for item in _counter_batch(ctx, stage)]
        prefix = "pw"
    else:
        message = f"stage {stage.stage_id!r} names attachment class {stage.attachments!r}"
        raise ChunkMultipassError(message)
    _require(
        len(paths) <= _MAX_STAGE_ATTACHMENTS,
        f"stage {stage.stage_id!r} would attach {len(paths)} databases; the engine bounds a "
        f"stage at {_MAX_STAGE_ATTACHMENTS} and never leaves that to SQLite",
    )
    _require(not connection.in_transaction, "ATTACH is issued outside any transaction")
    return _attach_all(connection, paths, prefix)


def _require_no_attachments(connection: sqlite3.Connection) -> None:
    attached = [
        str(row["name"])
        for row in connection.execute("PRAGMA database_list")
        if str(row["name"]) not in {"main", "temp"}
    ]
    _require(not attached, f"{attached} remain attached where none may")


def _execute_semantics(
    session: _WorldSession,
    ctx: _StageContext,
    stage: L2Stage,
    units: Sequence[AppliedUnit],
    aliases: Sequence[str],
    prepared: Mapping[str, object] | None,
    instr: _StageInstrumentation,
) -> tuple[int, Mapping[str, object]]:
    """The stage's exact semantic writes, inside the open transaction, before the applied row."""
    connection = session.connection
    kind = stage.kind
    if kind == _KIND_CAPTURE_DROP:
        return _stage_capture_and_drop_indexes(connection, ctx)
    if kind == _KIND_REDUCED_RUN:
        return _stage_reduced_parser_run(connection, aliases, ctx, instr)
    if kind == _KIND_TABLE_LOAD:
        return _stage_table_load(connection, aliases, ctx, stage, units, instr)
    if kind == _KIND_WITNESS_RANK:
        return _stage_witness_rank(connection, aliases, units, stage, instr)
    if kind == _KIND_CORRECTIONS:
        return _stage_observation_corrections(connection, units, stage, instr)
    if kind == _KIND_OBSERVATION_LOAD:
        return _stage_accession_observations(connection, aliases, instr)
    if kind == _KIND_EDGES:
        return _stage_edges_and_conflicts(connection, ctx, instr)
    if kind == _KIND_PARSER_STATE:
        return _stage_parser_state(connection, ctx, units, instr)
    if kind == _KIND_INDEX_REBUILD:
        return _stage_index_rebuild(connection, ctx, stage, instr)
    if kind == _KIND_COUNTER_CATALOG:
        return _stage_counter_catalog_batch(connection, aliases, ctx, stage, instr)
    if kind == _KIND_COUNTER_LEDGER:
        return _stage_counter_ledger_batch(connection, aliases, ctx, stage, instr)
    if kind == _KIND_COUNTERS_FINALIZE:
        return _stage_counters_finalize(connection, ctx, units, stage, instr)
    if kind == _KIND_OUTCOME:
        return _stage_outcome(ctx, units)
    _require(prepared is not None, f"stage {stage.stage_id!r} needs its cross-store half")
    assert prepared is not None  # noqa: S101 - narrowed above
    if kind == _KIND_SIDECAR:
        identity = _insert_cross_store_binding(
            connection,
            stage=stage,
            kind=_BINDING_SIDECAR,
            target_name=COMPACT_EVIDENCE_SIDECAR_FILENAME,
            target_byte_length=_stored_int(prepared["sidecar_byte_length"], "sidecar_byte_length"),
            target_sha256=str(prepared["sidecar_sha256"]),
            target_identity=str(prepared["sidecar_identity"]),
            body=prepared,
        )
        return 0, {**dict(prepared), "binding_identity": identity}
    if kind == _KIND_MARK_PARSED:
        identity = _insert_cross_store_binding(
            connection,
            stage=stage,
            kind=_BINDING_MARK_PARSED,
            target_name=PROGRESS_LEDGER_FILENAME,
            target_byte_length=None,
            target_sha256=None,
            target_identity=str(prepared["progress_identity"]),
            body=prepared,
        )
        return 0, {**dict(prepared), "binding_identity": identity}
    if kind == _KIND_REAUTHENTICATE:
        identity = _insert_cross_store_binding(
            connection,
            stage=stage,
            kind=_BINDING_REAUTHENTICATION,
            target_name="intermediates",
            target_byte_length=None,
            target_sha256=None,
            target_identity=str(prepared["descriptor_identity"]),
            body=prepared,
        )
        return 0, {**dict(prepared), "binding_identity": identity}
    if kind == _KIND_F0_CHECKPOINT:
        identity = _insert_cross_store_binding(
            connection,
            stage=stage,
            kind=_BINDING_F0_CHECKPOINT,
            target_name=PROGRESS_LEDGER_FILENAME,
            target_byte_length=None,
            target_sha256=None,
            target_identity=str(prepared["checkpoint_identity"]),
            body=prepared,
        )
        return 0, {**dict(prepared), "binding_identity": identity}
    if kind in {_KIND_FINAL_RECEIPT, _KIND_CALIBRATION_RESULT}:
        core = dict(_result_ready_core(ctx, units, connection, instr))
        if kind == _KIND_CALIBRATION_RESULT:
            row = connection.execute(
                "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
                (ctx.plan.source_instance_id,),
            ).fetchone()
            core["world_parser_state"] = "" if row is None else str(row["parser_state"])
        target = (
            FINAL_WORLD_RECEIPT_FILENAME
            if kind == _KIND_FINAL_RECEIPT
            else CALIBRATION_SUBSET_RESULT_FILENAME
        )
        identity = _insert_cross_store_binding(
            connection,
            stage=stage,
            kind=_BINDING_RESULT_READY,
            target_name=target,
            target_byte_length=None,
            target_sha256=None,
            target_identity=_identity_of(core),
            body=core,
        )
        return 0, {**core, "binding_identity": identity}
    message = f"stage kind {kind!r} has no executor"
    raise ChunkMultipassError(message)


def _prepare_stage(
    ctx: _StageContext,
    stage: L2Stage,
    units: Sequence[AppliedUnit],
    instr: _StageInstrumentation,
) -> Mapping[str, object] | None:
    """The cross-store half of a stage, BEFORE the world is boundedly reopened -- §36."""
    if stage.kind == _KIND_SIDECAR:
        return _prepare_sidecar(ctx, instr)
    if stage.kind == _KIND_MARK_PARSED:
        return _prepare_mark_parsed(ctx, units)
    if stage.kind == _KIND_REAUTHENTICATE:
        return _prepare_reauthentication(ctx, instr)
    if stage.kind == _KIND_F0_CHECKPOINT:
        return _prepare_f0_checkpoint(ctx, units)
    if _is_terminal(stage):
        return {}
    return None


def _publish_observability_closeout(
    ctx: _StageContext,
    units: Sequence[AppliedUnit],
    *,
    stage: L2Stage,
    post_commit_set: Mapping[str, object],
    attempt_ordinal: int,
) -> Mapping[str, object]:
    """The durable per-run observability closeout, create-once, before the terminal -- C2-R3."""
    statuses = observability_stage_statuses(ctx.stage_plan.statement_progress_root, units)
    summary_identity, gaps = _observability_summary(statuses)
    entries = [
        {**dict(status), "statement_execution_set": dict(unit.statement_execution_set or {})}
        for status, unit in zip(statuses, units, strict=True)
    ]
    record: dict[str, object] = {
        "contract": L2_OBSERVABILITY_CLOSEOUT_CONTRACT,
        "successor_run_id": ctx.stage_plan.successor_run_id,
        "route": ctx.route,
        "stage_plan_identity": ctx.stage_plan.identity,
        "statement_registry_identity": ctx.stage_plan.statement_registry_identity,
        "terminal_stage_id": stage.stage_id,
        "terminal_attempt_ordinal": attempt_ordinal,
        "observability_stage_statuses": entries,
        "observability_summary_identity": summary_identity,
        "observability_gap_count": gaps,
        "terminal_statement_execution_set_identity": units[-1].statement_execution_set_identity,
        "post_commit_execution_set": dict(post_commit_set),
        "utc": utc_now(),
    }
    record["closeout_identity"] = _identity_of(record)
    name = f"observability-closeout-{stage.stage_id}-attempt-{attempt_ordinal:03d}.json"
    try:
        write_once_canonical_json(ctx.receipt_root / name, record)
    except ChunkExecutionError as exc:
        message = f"the observability closeout {name!r} could not be published: {exc}"
        raise ChunkMultipassError(message) from exc
    return {
        "contract": L2_OBSERVABILITY_CLOSEOUT_CONTRACT,
        "closeout_relative_filename": name,
        "closeout_identity": str(record["closeout_identity"]),
        "observability_summary_identity": summary_identity,
        "observability_gap_count": gaps,
        "observability_stage_statuses": [
            {"stage_id": item["stage_id"], "observability_status": item["observability_status"]}
            for item in statuses
        ],
        "terminal_statement_execution_set_identity": units[-1].statement_execution_set_identity,
        "post_commit_execution_set_identity": str(post_commit_set["execution_set_identity"]),
    }


def _finish_terminal(ctx: _StageContext, stage: L2Stage, units: Sequence[AppliedUnit]) -> None:
    """Publish the final semantic record LAST, over the closed world -- never before.

    The world's artifact manifest is a journaled post-commit callable, the observability of
    every committed stage is re-evaluated and published as the closeout, and only then is the
    terminal record written, binding the closeout's identities (D151-C31R2-R19B-C2 §32).
    """
    instr = _stage_instrumentation_for(ctx, stage, units)
    terminal_name = (
        FINAL_WORLD_RECEIPT_FILENAME
        if stage.kind == _KIND_FINAL_RECEIPT
        else CALIBRATION_SUBSET_RESULT_FILENAME
    )
    manifest = cast(
        "ArtifactManifest",
        instr.record_callable(
            _OP_BUILD_MANIFEST,
            lambda: build_artifact_manifest(ctx.world_directory, exclude=(terminal_name,)),
            facts={"world": ctx.world_directory.name, "excluded": terminal_name},
        ),
    )
    post_commit = instr.execution_set(frozenset({_PHASE_POST_COMMIT}))
    binding = _publish_observability_closeout(
        ctx, units, stage=stage, post_commit_set=post_commit, attempt_ordinal=instr.attempt_ordinal
    )
    if stage.kind == _KIND_FINAL_RECEIPT:
        _publish_final_receipt(ctx, units, manifest=manifest, observability=binding)
    else:
        _publish_calibration_result(ctx, units, manifest=manifest, observability=binding)


def _seal_stage(
    session: _WorldSession,
    ctx: _StageContext,
    stage: L2Stage,
    unit: AppliedUnit,
    *,
    entry_classification: str,
    wal_residue_disposition: Mapping[str, object],
) -> Mapping[str, object] | None:
    """§30 steps 9-16 after COMMIT: no transaction, no attachment, checkpoint, validate, receipt."""
    connection = session.connection
    _require(
        not connection.in_transaction, "the stage transaction must be committed before sealing"
    )
    _require_no_attachments(connection)
    checkpoint_main_truncate(connection)
    normalized = normalized_wal_bytes(ctx.catalog_path)
    session.guard.release()
    units = _applied_units(connection)
    _require(
        bool(units) and units[-1].unit_identity == unit.unit_identity,
        "the applied unit did not read back as the last committed unit; refused",
    )
    _verify_committed_witness(connection, session.world, ctx, units[-1], units)
    main_state = _file_state(ctx.catalog_path)
    if _is_terminal(stage):
        return None
    observability = _unit_observability(ctx, units[-1])
    return _publish_stage_receipt(
        receipt_root=ctx.receipt_root,
        stage_plan=session.stage_plan,
        stage=stage,
        unit=units[-1],
        main_state=main_state,
        normalized_wal=normalized,
        observability=observability,
        entry_classification=entry_classification,
        wal_residue_disposition=wal_residue_disposition,
    )


def _dispose_wal_residue(
    session: _WorldSession, ctx: _StageContext, progress: _Progress
) -> Mapping[str, object]:
    """The WAL disposition AFTER classification and predecessor revalidation -- C1-R2 (§38).

    A nonzero pre-state log is one of three things. Explained by a committed applied unit whose
    receipt is absent: left for the receipt convergence, which checkpoints it explicitly.
    Holding committed frames that no applied unit explains: a terminal conflict -- the engine
    commits nothing without an applied-unit row in the same transaction, so committed frames
    without one are foreign, and they are never checkpointed merely because a log exists.
    Holding no committed frame at all -- a rollback, an interruption, a SIGKILL or a timeout's
    uncommitted tail -- a residue: checkpointed to exactly ``(0, 0, 0)``, held to a zero-length
    log, the predecessor revalidated again, and the next transaction's baseline is 0.
    """
    before = session.prestate.snapshot_before
    if before.wal_class != _WAL_NONZERO:
        return {
            "class": _RESIDUE_NONE,
            "residue_bytes": 0,
            "committed_frames": None,
            "normalized": False,
        }
    residue_bytes = _normalized_wal_class(before)
    if progress.pending is not None:
        return {
            "class": _RESIDUE_PENDING,
            "residue_bytes": residue_bytes,
            "committed_frames": None,
            "normalized": False,
            "detail": "explained by the committed applied unit whose receipt is pending; the "
            "receipt convergence checkpoints it explicitly",
        }
    shm = session.catalog_path.with_name(session.catalog_path.name + "-shm")
    try:
        committed = wal_index_committed_frames(shm)
    except WorkingCatalogError as exc:
        _stage_conflict(
            f"the world's write-ahead log holds {residue_bytes} bytes and its committed frames "
            f"cannot be counted ({exc}); nothing is checkpointed"
        )
    if committed > 0:
        _stage_conflict(
            f"the world's write-ahead log holds {committed} committed frame(s) that no applied "
            f"unit explains (log {residue_bytes} bytes, classification {progress.classification}); "
            "an unexplained committed mutation is never checkpointed merely because a log exists"
        )
    connection = session.connection
    _require(not connection.in_transaction, "a residue is disposed of outside any transaction")
    _require_no_attachments(connection)
    result = checkpoint_main_truncate(connection)
    _require(
        normalized_wal_bytes(session.catalog_path) == 0,
        "the residue checkpoint did not leave a zero-length log; refused",
    )
    again = _classify(session, ctx)
    _require(
        again.classification == progress.classification
        and again.pending is None
        and (again.next_stage is None) == (progress.next_stage is None)
        and (
            again.next_stage is None
            or progress.next_stage is None
            or again.next_stage.ordinal == progress.next_stage.ordinal
        )
        and [item.unit_identity for item in again.units]
        == [item.unit_identity for item in progress.units],
        "the predecessor revalidation after the residue checkpoint disagrees with the "
        "classification before it; refused",
    )
    session.guard.release()
    return {
        "class": _RESIDUE_ROLLBACK,
        "residue_bytes": residue_bytes,
        "committed_frames": 0,
        "checkpoint_result": list(result),
        "normalized": True,
        "transaction_baseline_frames": 0,
    }


def _normalize_after_abort(
    session: _WorldSession, ctx: _StageContext, instr: _StageInstrumentation, prior_count: int
) -> None:
    """After a watchdog or instrumentation abort: prove nothing durable, then try to normalize.

    The interrupted transaction was rolled back (by SQLite on interruption, or by the accepted
    transaction context); the attachments are detached; no applied unit, receipt or terminal
    record exists for this stage. Then one graceful ``PRAGMA main.wal_checkpoint(TRUNCATE)`` is
    attempted and its outcome recorded as ``ABORT_WAL_NORMALIZED``; a failure to normalize never
    turns the uncommitted, interrupted stage into a semantic conflict -- the next process
    disposes of the residue.
    """
    connection = session.connection
    normalized = False
    outcome: object = None
    try:
        _require(not connection.in_transaction, "the aborted transaction is still open")
        _require_no_attachments(connection)
        _require(
            len(_applied_units(connection)) == prior_count,
            "an applied unit exists for an aborted stage; refused",
        )
        _require(
            not os.path.lexists(stage_receipt_path(ctx.receipt_root, instr.stage)),
            "a stage receipt exists for an aborted stage; refused",
        )
        outcome = list(checkpoint_main_truncate(connection))
        _require(normalized_wal_bytes(ctx.catalog_path) == 0, "the log is not zero after TRUNCATE")
        normalized = True
        session.guard.release()
    except (ChunkMultipassError, WorkingCatalogError, sqlite3.Error) as exc:
        outcome = f"{type(exc).__name__}: {exc}"[:400]
    instr.publish_abort_record(normalized, outcome)


def _run_stage(
    ctx: _StageContext,
    stage: L2Stage,
    prior: Sequence[AppliedUnit],
    carried_disposition: Mapping[str, object] | None = None,
) -> None:
    """One stage, end to end: prepare, reopen, authenticate, attach, write, seal, publish.

    ``carried_disposition`` is the WAL disposition the stage loop's classification session
    made just before this stage; the stage's own session records its own disposition, and the
    receipt carries whichever was not ``NONE`` so a residue recovery stays observable.
    """
    instr = _stage_instrumentation_for(ctx, stage, prior)
    try:
        prepared = _prepare_stage(ctx, stage, prior, instr)
    except BaseException:
        if instr.abort is not None:
            sidecar = ctx.world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME
            wal = sidecar.with_name(sidecar.name + "-wal")
            instr.publish_abort_record(not os.path.lexists(wal) or wal.stat().st_size == 0, None)
        raise
    with _successor_world_session(
        request=ctx.request, expected=ctx.stage_plan, proof=ctx.proof
    ) as session:
        progress = _classify(session, ctx)
        _require(
            progress.pending is None
            and progress.next_stage is not None
            and progress.next_stage.ordinal == stage.ordinal,
            f"the world's committed evidence no longer names {stage.stage_id!r} as the next stage",
        )
        disposition = _dispose_wal_residue(session, ctx, progress)
        if disposition["class"] == _RESIDUE_NONE and carried_disposition is not None:
            disposition = carried_disposition
        units = progress.units
        predecessor = units[-1].unit_identity if units else session.stage_plan.identity
        input_identities = [
            str(item["manifest_digest"]) for item in session.stage_plan.intermediates
        ]
        receipt_identities = [
            str(item["receipt_document_sha256"]) for item in session.stage_plan.intermediates
        ]
        provenance = [
            str(cast("Mapping[str, object]", item["group_request_provenance"])["sha256"])
            for item in session.stage_plan.intermediates
        ]
        connection = session.connection
        aliases = _attach_for_stage(connection, ctx, stage)
        try:
            try:
                with transaction(connection):
                    instr.begin_world_transaction(connection)
                    rows_written, witness = _execute_semantics(
                        session, ctx, stage, units, aliases, prepared, instr
                    )
                    execution_set = instr.execution_set(
                        frozenset({_PHASE_PREPARE, _PHASE_TRANSACTION})
                    )
                    unit = _insert_applied_unit(
                        connection,
                        stage_plan=session.stage_plan,
                        stage=stage,
                        predecessor_unit_identity=predecessor,
                        input_identities=input_identities,
                        receipt_identities=receipt_identities,
                        request_provenance_identities=provenance,
                        connection_state=session.connection_state,
                        rows_written=rows_written,
                        outcome_witness=witness,
                        execution_set=execution_set,
                    )
            finally:
                _detach_all(connection, aliases)
        except BaseException:
            if instr.abort is not None:
                _normalize_after_abort(session, ctx, instr, len(units))
            raise
        _seal_stage(
            session,
            ctx,
            stage,
            unit,
            entry_classification=progress.classification,
            wal_residue_disposition=disposition,
        )
    if _is_terminal(stage):
        _finish_terminal(ctx, stage, [*prior, unit])


def _converge_receipt(ctx: _StageContext, stage: L2Stage) -> None:
    """§31 B: the unit is committed and its receipt is absent -- publish without re-execution."""
    with _successor_world_session(
        request=ctx.request, expected=ctx.stage_plan, proof=ctx.proof
    ) as session:
        progress = _classify(session, ctx)
        _require(
            progress.pending is not None and progress.pending.ordinal == stage.ordinal,
            f"stage {stage.stage_id!r} is no longer receipt-pending",
        )
        disposition = _dispose_wal_residue(session, ctx, progress)
        unit = progress.units[-1]
        _require(
            unit.stage_ordinal == stage.ordinal, "the pending stage is not the last applied unit"
        )
        _seal_stage(
            session,
            ctx,
            stage,
            unit,
            entry_classification=progress.classification,
            wal_residue_disposition=disposition,
        )
        units = progress.units
    if _is_terminal(stage):
        _finish_terminal(ctx, stage, units)


_ATTEMPT_COMPLETE: Final = "COMPLETE"
_ATTEMPT_INCOMPLETE: Final = "INCOMPLETE"
_ATTEMPT_INCOMPLETE_NONZERO_WAL: Final = "INCOMPLETE_NONZERO_WAL"
_ATTEMPT_MALFORMED_SIDECAR: Final = "MALFORMED_SIDECAR"


def _attempt_bytes(attempt: Path) -> tuple[int, int, int]:
    """``(files, logical bytes, allocated bytes)`` of one attempt, by lstat alone."""
    files = logical = allocated = 0
    for dirpath, _dirnames, filenames in os.walk(attempt):
        for name in filenames:
            status = os.lstat(Path(dirpath) / name)
            if stat.S_ISREG(status.st_mode):
                files += 1
                logical += status.st_size
                allocated += status.st_blocks * 512
    return files, logical, allocated


def _classify_one_attempt(
    attempt: Path, ordinal: int, expected: L2StagePlan
) -> Mapping[str, object]:
    """Classify one initialization attempt without opening it through anything but
    ``immutable=1`` -- R19A-R1 MINOR-1 (D151-C31R2-R19B-C2 §13).

    COMPLETE requires a regular non-link main catalog and ledger, a write-ahead log that is
    absent or zero, no malformed sidecar, and -- read through ``immutable=1``, which creates
    nothing -- the expected StagePlan identity beside a committed S0 unit. A nonzero log is
    interrupted residue: preserved, never checkpointed, never promoted, never complete.
    """
    catalog = attempt / WORKING_CATALOG_FILENAME
    main = _file_state(catalog, digest=False)
    wal = _file_state(catalog.with_name(catalog.name + "-wal"), digest=False)
    shm = _file_state(catalog.with_name(catalog.name + "-shm"), digest=False)
    ledger = _file_state(attempt / PROGRESS_LEDGER_FILENAME, digest=False)
    files, logical, allocated = _attempt_bytes(attempt)
    record: dict[str, object] = {
        "name": attempt.name,
        "ordinal": ordinal,
        "main": dict(main.as_record()),
        "wal": dict(wal.as_record()),
        "shm": dict(shm.as_record()),
        "ledger": dict(ledger.as_record()),
        "file_count": files,
        "logical_bytes": logical,
        "allocated_bytes": allocated,
    }
    if main.lstat_class != "file" or ledger.lstat_class != "file":
        classification, reason = _ATTEMPT_INCOMPLETE, "no regular catalog and ledger"
    elif wal.lstat_class not in {"absent", "file"} or shm.lstat_class not in {"absent", "file"}:
        classification, reason = _ATTEMPT_MALFORMED_SIDECAR, "a log or index sidecar is not a file"
    elif wal.lstat_class == "file" and wal.byte_length:
        classification, reason = _ATTEMPT_INCOMPLETE_NONZERO_WAL, "interrupted residue: nonzero log"
    else:
        classification, reason = _authenticate_attempt_immutable(catalog, expected)
    record["classification"] = classification
    record["reason"] = reason
    return record


def _authenticate_attempt_immutable(catalog: Path, expected: L2StagePlan) -> tuple[str, str]:
    """Read the attempt's StagePlan row and S0 unit through ``immutable=1``: no side effect."""
    try:
        probe = sqlite3.connect(f"{catalog.absolute().as_uri()}?immutable=1", uri=True)
    except sqlite3.Error as exc:
        return _ATTEMPT_INCOMPLETE, f"not openable: {exc}"
    try:
        probe.row_factory = sqlite3.Row
        plan_row = probe.execute(
            f"SELECT stage_plan_identity FROM main.{L2_STAGE_PLAN_TABLE} WHERE singleton = 1"  # noqa: S608
        ).fetchone()
        unit_row = probe.execute(
            f"SELECT stage_id FROM main.{L2_APPLIED_UNITS_TABLE} WHERE stage_ordinal = 0"  # noqa: S608
        ).fetchone()
    except sqlite3.Error as exc:
        return _ATTEMPT_INCOMPLETE, f"no readable successor rows: {exc}"
    finally:
        probe.close()
    if plan_row is None or unit_row is None:
        return _ATTEMPT_INCOMPLETE, "no StagePlan row or no S0 unit"
    if str(plan_row["stage_plan_identity"]) != expected.identity:
        return _ATTEMPT_INCOMPLETE, "another StagePlan identity"
    if str(unit_row["stage_id"]) != _STAGE_INITIALIZE:
        return _ATTEMPT_INCOMPLETE, "ordinal 0 is not S0"
    return _ATTEMPT_COMPLETE, "expected StagePlan and committed S0 through immutable=1"


def _classify_attempt_residue(
    world: Path, expected: L2StagePlan
) -> tuple[Mapping[str, object], ...]:
    """Every sibling initialization attempt of ``world``, classified by lstat and immutable reads.

    A symbolic link, a non-directory or a malformed ordinal beside the world is a conflict; a
    duplicate ordinal cannot arise from distinct names but is refused all the same. Nothing here
    alters an inventory, inode, length, digest or mtime.
    """
    parent = world.parent
    if not parent.is_dir():
        return ()
    prefix = f"{world.name}.init-attempt-"
    records: list[Mapping[str, object]] = []
    for name in sorted(entry.name for entry in parent.iterdir()):
        if not name.startswith(prefix):
            continue
        suffix = name[len(prefix) :]
        status = os.lstat(parent / name)
        if len(suffix) != 3 or not suffix.isdigit():
            _stage_conflict(f"initialization attempt {name!r} carries a malformed ordinal")
        if stat.S_ISLNK(status.st_mode):
            _stage_conflict(f"initialization attempt {name!r} is a symbolic link")
        if not stat.S_ISDIR(status.st_mode):
            _stage_conflict(f"initialization attempt {name!r} is not a directory")
        records.append(_classify_one_attempt(parent / name, int(suffix), expected))
    ordinals = [int(cast("int", item["ordinal"])) for item in records]
    if len(set(ordinals)) != len(ordinals):
        _stage_conflict("two initialization attempts carry the same ordinal")
    return tuple(records)


def _initialize_world_attempt(ctx: _StageContext, attempt_ordinal: int) -> None:
    """P1 admission, then S0 inside a create-once attempt, then atomic promotion -- §27, §28."""
    world = ctx.world_directory
    attempt = world.parent / f"{world.name}.init-attempt-{attempt_ordinal:03d}"
    _require(
        not os.path.lexists(attempt), f"initialization attempt {attempt.name!r} already exists"
    )
    ctx.proof.require_live(ctx.route)
    tool_manifest = _require_runtime_tool_identity(
        ctx.stage_plan.tool_manifest_identity, label="admission"
    )
    input_bytes = _stored_int(ctx.stage_plan.body["governed_input_bytes"], "governed_input_bytes")
    admission = _admit_merge_step(
        step=_SUCCESSOR_CALIBRATION_STEP,
        level=MERGE_LEVEL_TWO,
        target=world,
        input_bytes=input_bytes,
        seed_catalog_bytes=ctx.seed_catalog_bytes,
        peak_ratio=ctx.requirements.level_two_peak_ratio,
        requirements=ctx.requirements,
    )
    record: dict[str, object] = {
        "contract": L2_STAGE_ADMISSION_CONTRACT,
        "route": ctx.route,
        "successor_run_id": ctx.request.run_id,
        "stage_plan_identity": ctx.stage_plan.identity,
        "tool_manifest_identity": tool_manifest.identity,
        "sqlite_temp_binding": dict(ctx.binding.as_record()),
        "admission": dict(admission.as_record()),
        "input_bytes": input_bytes,
        "seed_catalog_bytes": ctx.seed_catalog_bytes,
        "attempt_ordinal": attempt_ordinal,
        "initialization_attempt_directory_name": attempt.name,
        "reusable": False,
        "utc": utc_now(),
    }
    record["admission_identity"] = _identity_of(record)
    ctx.receipt_root.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    stage = ctx.stages[0]
    instr = _stage_instrumentation_for(ctx, stage, ())
    try:
        write_once_canonical_json(
            ctx.receipt_root / f"admission-attempt-{attempt_ordinal:03d}.json", record
        )
    except ChunkExecutionError as exc:
        message = f"the successor admission record could not be written: {exc}"
        raise ChunkMultipassError(message) from exc
    event_identity: str | None = None
    if ctx.route == SUCCESSOR_ROUTE_CALIBRATION:
        envelope = ctx.proof.envelope
        _require(
            envelope is not None, "a calibration successor admission needs the child's envelope"
        )
        assert envelope is not None  # noqa: S101 - narrowed above
        event = _emit_calibration_admission_event(
            envelope=envelope,
            admission=admission,
            binding=ctx.binding,
            input_bytes=input_bytes,
            seed_catalog_bytes=ctx.seed_catalog_bytes,
            charged_directory=world,
            attempt=attempt_ordinal,
        )
        event_identity = event.event_identity
    attempt.mkdir(mode=_DIRECTORY_MODE)
    with WorkingCatalog(
        Path(ctx.request.operational_catalog),
        attempt,
        cache_bytes=require_executable_level_two_cache_bytes(ctx.stage_plan.cache_bytes),
    ) as world_catalog:
        connection = world_catalog.connection
        _require(
            world_catalog.identity.migration_head == ctx.contract.migration_head,
            "the successor world was seeded at migration head "
            f"{world_catalog.identity.migration_head} "
            f"where every input executed at {ctx.contract.migration_head}",
        )
        world_catalog.ledger.begin_source(ctx.plan.source_instance_id, ctx.plan.source_id)
        connection_state = _establish_successor_connection_state(
            connection, ctx.stage_plan, ctx.proof
        )
        with transaction(connection):
            for statement in _L2_CONTROL_SCHEMA.split(";"):
                if statement.strip():
                    connection.execute(statement)
            connection.execute(
                f"INSERT INTO main.{L2_STAGE_PLAN_TABLE} (singleton, contract, successor_run_id, "  # noqa: S608
                "route, canonical_world_path, stage_plan_identity, body_json) "
                "VALUES (1, ?, ?, ?, ?, ?, ?)",
                (
                    L2_STAGE_PLAN_CONTRACT_V2,
                    ctx.stage_plan.successor_run_id,
                    ctx.stage_plan.route,
                    ctx.stage_plan.canonical_world_path,
                    ctx.stage_plan.identity,
                    _json_text(dict(ctx.stage_plan.body)),
                ),
            )
            _insert_applied_unit(
                connection,
                stage_plan=ctx.stage_plan,
                stage=stage,
                predecessor_unit_identity=ctx.stage_plan.identity,
                input_identities=[
                    str(item["manifest_digest"]) for item in ctx.stage_plan.intermediates
                ],
                receipt_identities=[
                    str(item["receipt_document_sha256"]) for item in ctx.stage_plan.intermediates
                ],
                request_provenance_identities=[
                    str(cast("Mapping[str, object]", item["group_request_provenance"])["sha256"])
                    for item in ctx.stage_plan.intermediates
                ],
                connection_state=connection_state,
                rows_written=0,
                outcome_witness={
                    "admission_identity": str(record["admission_identity"]),
                    "admission": dict(admission.as_record()),
                    "admission_event_identity": event_identity,
                    "free_before_bytes": admission.free_bytes,
                    "seed_catalog_sha256": ctx.seed_catalog_sha256,
                    "seed_catalog_byte_length": ctx.seed_catalog_bytes,
                    "attempt_ordinal": attempt_ordinal,
                    "attempt_directory_name": attempt.name,
                    "begin_source": True,
                },
                execution_set=instr.execution_set(frozenset({_PHASE_PREPARE, _PHASE_TRANSACTION})),
            )
        checkpoint_main_truncate(connection)
        normalized_wal_bytes(attempt / WORKING_CATALOG_FILENAME)
        stored = _read_stored_stage_plan(connection)
        _require(
            stored.identity == ctx.stage_plan.identity, "the stored StagePlan did not read back"
        )
        _require(
            len(_applied_units(connection)) == 1, "S0 did not read back as the one applied unit"
        )
    promote_world_directory(attempt, world)


def _ensure_world(ctx: _StageContext) -> tuple[Mapping[str, object], ...]:
    """§28 states: initialize, preserve an incomplete attempt, promote a complete one.

    R19A-R1 MINOR-1: a canonical world's sibling attempts are classified too. A complete,
    authenticated attempt beside an existing canonical world is a conflict; incomplete residue
    is preserved, never invalidates an authentic world, and is returned -- allocated bytes
    measured after classification -- as storage-planning evidence.
    """
    world = ctx.world_directory
    residue = _classify_attempt_residue(world, ctx.stage_plan)
    complete = [item for item in residue if item["classification"] == _ATTEMPT_COMPLETE]
    if os.path.lexists(world):
        _require(
            not world.is_symlink() and world.is_dir(),
            f"the canonical successor world {world.name!r} exists and is not a directory",
        )
        if complete:
            _stage_conflict(
                f"{len(complete)} complete, authenticated initialization attempt(s) "
                f"({[item['name'] for item in complete]}) sit beside the canonical world "
                f"{world.name!r}; a second complete world under one StagePlan is never continued"
            )
        return residue
    if len(complete) > 1:
        _stage_conflict(
            f"{len(complete)} complete initialization attempts exist beside an absent world"
        )
    if complete:
        promote_world_directory(world.parent / str(complete[0]["name"]), world)
        return tuple(item for item in residue if item["classification"] != _ATTEMPT_COMPLETE)
    ordinals = [int(cast("int", item["ordinal"])) for item in residue]
    _initialize_world_attempt(ctx, max(ordinals, default=-1) + 1)
    return residue


@dataclass(frozen=True, slots=True)
class SuccessorRunOutcome:
    """What one successor invocation established, read back from durable evidence."""

    route: str
    successor_run_id: str
    stage_plan_identity: str | None
    world_directory: Path
    stage_receipt_root: Path
    completed_stage_ids: tuple[str, ...]
    terminal_reached: bool
    final_receipt: Mapping[str, object] | None
    calibration_result: CalibrationSubsetResult | None
    observability: Mapping[str, object] | None = None
    retained_attempt_residue: tuple[Mapping[str, object], ...] = ()


def _successor_outcome_from_disk(
    request: SuccessorFinalRequest, *, residue: Sequence[Mapping[str, object]] = ()
) -> SuccessorRunOutcome:
    """The outcome as the receipts and the terminal record on disk describe it."""
    world = Path(request.world_directory)
    receipt_root = Path(request.stage_receipt_root)
    completed: list[tuple[int, str]] = []
    identity: str | None = None
    if receipt_root.is_dir():
        for path in sorted(receipt_root.iterdir()):
            if path.name.startswith("stage-") and path.suffix == ".json":
                receipt = read_stage_receipt(path)
                completed.append(
                    (
                        _stored_int(receipt["stage_ordinal"], "stage_ordinal"),
                        str(receipt["stage_id"]),
                    )
                )
                identity = str(receipt["stage_plan_identity"])
    final_receipt: Mapping[str, object] | None = None
    calibration_result: CalibrationSubsetResult | None = None
    if (
        request.route == SUCCESSOR_ROUTE_PRODUCTION
        and (world / FINAL_WORLD_RECEIPT_FILENAME).is_file()
    ):
        final_receipt = read_receipt_document(
            world / FINAL_WORLD_RECEIPT_FILENAME, contract=FINAL_WORLD_RECEIPT_CONTRACT
        )
        manifest_record = final_receipt.get("manifest")
        _require(isinstance(manifest_record, Mapping), "the final receipt carries no manifest")
        verify_artifact_manifest(
            world,
            ArtifactManifest.from_record(cast("Mapping[str, object]", manifest_record)),
            exclude=(FINAL_WORLD_RECEIPT_FILENAME,),
        )
        completed.append((len(completed) + 1_000_000, _STAGE_FINAL_RECEIPT))
    if (
        request.route == SUCCESSOR_ROUTE_CALIBRATION
        and (world / CALIBRATION_SUBSET_RESULT_FILENAME).is_file()
    ):
        calibration_result = read_calibration_subset_result(
            world / CALIBRATION_SUBSET_RESULT_FILENAME
        )
        verify_artifact_manifest(
            world, calibration_result.manifest, exclude=(CALIBRATION_SUBSET_RESULT_FILENAME,)
        )
        completed.append((len(completed) + 1_000_000, _STAGE_CALIBRATION_RESULT))
    observability: Mapping[str, object] | None = None
    if final_receipt is not None and isinstance(
        final_receipt.get("successor_observability"), Mapping
    ):
        observability = cast("Mapping[str, object]", final_receipt["successor_observability"])
    elif calibration_result is not None and calibration_result.successor_observability is not None:
        observability = calibration_result.successor_observability
    return SuccessorRunOutcome(
        route=request.route,
        successor_run_id=request.run_id,
        stage_plan_identity=identity,
        world_directory=world,
        stage_receipt_root=receipt_root,
        completed_stage_ids=tuple(stage_id for _ordinal, stage_id in sorted(completed)),
        terminal_reached=final_receipt is not None or calibration_result is not None,
        final_receipt=final_receipt,
        calibration_result=calibration_result,
        observability=observability,
        retained_attempt_residue=tuple(dict(item) for item in residue),
    )


def _resolve_route_intermediates(
    request: SuccessorFinalRequest, plan: ChunkPlan, schedule: MergeSchedule, route: str
) -> tuple[IntermediateInput, ...]:
    """The route's accepted intermediate resolution: production binds chunks as well."""
    intermediates_root = Path(request.intermediates_root)
    if route == SUCCESSOR_ROUTE_PRODUCTION:
        chunks = resolve_chunk_inputs(
            plan,
            internal_root=Path(request.internal_root),
            external_root=None if request.external_root is None else Path(request.external_root),
        )
        return resolve_intermediate_inputs(
            plan, schedule, intermediates_root=intermediates_root, chunk_inputs=chunks
        )
    return resolve_intermediate_inputs(plan, schedule, intermediates_root=intermediates_root)


def _measured_successor_binding(charged_path: Path) -> SqliteTempBinding:
    """THIS process's SQLite temporary binding for the successor world -- D151-C17 R6."""
    return require_sqlite_temp_binding(charged_path=charged_path)


def _resolve_successor_context(
    request: SuccessorFinalRequest, proof: _SuccessorRouteProof
) -> _StageContext:
    """P0 ROUTE_GATE_AND_AUTHENTICATE: everything a stage may consume, authenticated once."""
    proof.require_live(request.route)
    repository = _authenticate_running_repository(
        head=request.repository_head_sha, tree=request.repository_tree_sha, label="successor-final"
    )
    plan: ChunkPlan
    if request.route == SUCCESSOR_ROUTE_PRODUCTION:
        plan, schedule = _read_plan_and_schedule(request.plan_path, request.schedule_path)
    else:
        plan, schedule = _read_calibration_plan_and_schedule(
            request.plan_path, request.schedule_path
        )
        _require(
            proof.plan_digest == plan.plan_digest,
            "the calibration successor's sealed plan identity is not the one the envelope bound",
        )
    require_chunkable_source(plan.source_id)
    requirements = MultipassStorageRequirements.from_record(request.storage_requirements)
    world = Path(request.world_directory)
    receipt_root = Path(request.stage_receipt_root)
    _require(
        world != receipt_root
        and not _within(world, receipt_root)
        and not _within(receipt_root, world),
        "the stage receipt root must lie outside the successor world and the reverse",
    )
    binding = _require_expected_binding(
        _measured_successor_binding(world),
        request.expected_sqlite_temp_binding,
        label="successor-final",
    )
    operational = Path(request.operational_catalog)
    seed_sha256, seed_bytes = file_digest(operational)
    counter_sources: tuple[PlanWitnessSource, ...]
    if request.route == SUCCESSOR_ROUTE_PRODUCTION:
        chunks = resolve_chunk_inputs(
            plan,
            internal_root=Path(request.internal_root),
            external_root=None if request.external_root is None else Path(request.external_root),
        )
        intermediates = resolve_intermediate_inputs(
            plan, schedule, intermediates_root=Path(request.intermediates_root), chunk_inputs=chunks
        )
        counter_sources = tuple(chunks)
        identities = tuple(f"{item.chunk_id}:{item.receipt.manifest.digest}" for item in chunks)
    else:
        retained_root = calibration_retained_root(Path(request.intermediates_root))
        witnesses = resolve_calibration_chunk_witnesses(
            cast("CalibrationSubsetPlan", plan),
            schedule,
            run_id=request.predecessor_run_id,
            retained_root=retained_root,
        )
        checkpoints = resolve_calibration_group_checkpoints(
            cast("CalibrationSubsetPlan", plan),
            schedule,
            run_id=request.predecessor_run_id,
            retained_root=retained_root,
            witnesses=witnesses,
        )
        intermediates = resolve_intermediate_inputs(
            plan, schedule, intermediates_root=Path(request.intermediates_root)
        )
        _require_witness_bound_intermediates(intermediates, witnesses, checkpoints)
        counter_sources = tuple(witnesses)
        identities = tuple(f"{item.chunk_id}:{item.witness.witness_identity}" for item in witnesses)
    require_attachable(len(intermediates))
    contract = intermediates[0].receipt.execution_contract
    _require_seed_identity(
        label="successor-final",
        repository=repository,
        recorded_head=intermediates[0].receipt.repository_head_sha,
        recorded_tree=intermediates[0].receipt.repository_tree_sha,
        contract=contract,
        catalog_sha256=seed_sha256,
    )
    state = _accepted_plan_state(operational, plan)
    tool_manifest = _runtime_tool_manifest()
    with connect(operational, read_only=True) as reader:
        expected_indexes = _deferrable_index_records(reader)
    stage_plan = _build_successor_stage_plan(
        request=request,
        plan=plan,
        schedule=schedule,
        intermediates=intermediates,
        counter_source_count=len(counter_sources),
        counter_source_identities=identities,
        repository=repository,
        contract=contract,
        state=state,
        seed_catalog_sha256=seed_sha256,
        seed_catalog_bytes=seed_bytes,
        tool_manifest=tool_manifest,
        expected_index_records=expected_indexes,
        requirements=requirements,
        binding=binding,
    )
    if request.stop_after_stage is not None:
        _require(
            any(stage.stage_id == request.stop_after_stage for stage in stage_plan.stages),
            f"stop_after_stage {request.stop_after_stage!r} names no stage of this route",
        )
    return _StageContext(
        request=request,
        proof=proof,
        route=request.route,
        plan=plan,
        schedule=schedule,
        intermediates=intermediates,
        counter_sources=counter_sources,
        counter_source_identities=identities,
        repository=repository,
        contract=contract,
        state=state,
        seed_catalog_sha256=seed_sha256,
        seed_catalog_bytes=seed_bytes,
        requirements=requirements,
        binding=binding,
        stage_plan=stage_plan,
        world_directory=world,
        receipt_root=receipt_root,
    )


def _run_successor_stages(ctx: _StageContext) -> SuccessorRunOutcome:
    """The stage loop: classify committed evidence, converge a pending receipt, or run the next."""
    residue = _ensure_world(ctx)
    stop_after = ctx.request.stop_after_stage
    while True:
        with _successor_world_session(
            request=ctx.request, expected=ctx.stage_plan, proof=ctx.proof
        ) as session:
            progress = _classify(session, ctx)
            disposition = _dispose_wal_residue(session, ctx, progress)
        if progress.pending is not None:
            _converge_receipt(ctx, progress.pending)
            continue
        if progress.next_stage is None:
            break
        if stop_after is not None and progress.units and progress.units[-1].stage_id == stop_after:
            break
        _run_stage(ctx, progress.next_stage, progress.units, disposition)
    return _successor_outcome_from_disk(ctx.request, residue=residue)


def _run_successor_final(
    request: SuccessorFinalRequest, proof: _SuccessorRouteProof
) -> SuccessorRunOutcome:
    """The private engine entry: proof first, then P0 authentication, then the stage loop."""
    _require_route_proof(proof, request.route)
    return _run_successor_stages(_resolve_successor_context(request, proof))


# --------------------------------------------------------------------------- #
# The two public route gates -- §15
# --------------------------------------------------------------------------- #
def run_successor_multipass_final(request: SuccessorFinalRequest) -> SuccessorRunOutcome:
    """The production successor final: authority FIRST, then the durable stage spine.

    The real multipass authority is the absolute first effective operation -- before a path is
    stat'ed, a request parsed, a StagePlan read, a manifest read, a world inspected, a proof
    minted or a file created. Then the production route request is validated, the process-local
    production proof is minted from the gate that just passed, and the private engine runs the
    stage loop under it, re-invoking the gate at every stage's STEP 0.

    Raises:
        ChunkMultipassError: the authority is ``None``, the request is not a production
            successor request, or any successor precondition, classification or stage refuses.
    """
    require_real_multipass_authority()
    _require(
        isinstance(request, SuccessorFinalRequest) and request.route == SUCCESSOR_ROUTE_PRODUCTION,
        "run_successor_multipass_final serves the production route only",
    )
    proof = _mint_successor_route_proof(
        SUCCESSOR_ROUTE_PRODUCTION,
        gate=require_real_multipass_authority,
        gate_name="require_real_multipass_authority",
    )
    return _run_successor_final(request, proof)


def run_successor_calibration_final(
    request: SuccessorFinalRequest,
    *,
    calibration_plan: ChunkPlan,
    instrumentation_ledger: Path,
    predecessor_pid: int | None = None,
    timeout_seconds: float | None = None,
    observe: Callable[[str], None] | None = None,
) -> SuccessorRunOutcome:
    """The calibration successor final: sealed plan FIRST, then one envelope-gated child.

    The sealed calibration-subset plan is the absolute first effective operation -- a constructed
    envelope is not authority, and no path, StagePlan or world is touched before it. Then the
    request is written create-once, the envelope is issued over exactly those bytes, and the
    existing calibration child lifecycle spawns one child that receives the envelope, requires
    the final role, holds the sealed plan identity, mints its own proof and enters the engine.

    Raises:
        ChunkPlanError: the plan is not a sealed subset plan.
        ChunkMultipassError, ChunkExecutionError, ChunkEvidenceError: any proof fails.
    """
    require_calibration_subset_plan(calibration_plan)
    _require(
        isinstance(request, SuccessorFinalRequest) and request.route == SUCCESSOR_ROUTE_CALIBRATION,
        "run_successor_calibration_final serves the calibration route only",
    )
    if predecessor_pid is not None:
        _require_process_dead(predecessor_pid)
    receipt_root = Path(request.stage_receipt_root)
    receipt_root.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
    launch = 0
    while os.path.lexists(receipt_root / f"successor-request-{launch:03d}.json"):
        launch += 1
    request_path = receipt_root / f"successor-request-{launch:03d}.json"
    write_once_json(request_path, dict(request.as_record()))
    envelope = issue_calibration_envelope(
        run_id=request.run_id,
        plan=cast("CalibrationSubsetPlan", calibration_plan),
        role=CALIBRATION_ROLE_FINAL,
        step_id=_SUCCESSOR_CALIBRATION_STEP,
        request_path=request_path,
        instrumentation_ledger=instrumentation_ledger,
    )
    _spawn_calibration_child(
        request_path, envelope, timeout_seconds=timeout_seconds, observe=observe
    )
    outcome = _successor_outcome_from_disk(request)
    if outcome.calibration_result is not None:
        _require(
            outcome.calibration_result.run_id == request.run_id
            and outcome.calibration_result.plan_digest == calibration_plan.plan_digest
            and outcome.calibration_result.envelope_sha256 == envelope.sha256,
            "the calibration-subset result does not describe this plan, run and envelope; refused",
        )
        _require(
            outcome.calibration_result.pid != os.getpid(),
            "the calibration-subset result records THIS process's pid; the finalization did not "
            "run in a separate operating-system process",
        )
        _require_process_dead(outcome.calibration_result.pid)
    return outcome


def _successor_calibration_final_body(
    request: SuccessorFinalRequest, envelope: CalibrationChildEnvelope
) -> SuccessorRunOutcome:
    """The spawned calibration successor child's body: envelope role FIRST, then the engine.

    In order: the exact-contract envelope for the final role; the sealed subset plan re-read
    and held to the envelope's plan identity, step and run; the process-local calibration proof
    minted from a gate that re-validates both; then the private engine.
    """
    require_calibration_envelope(envelope, role=CALIBRATION_ROLE_FINAL)
    _require(
        request.route == SUCCESSOR_ROUTE_CALIBRATION,
        "the calibration successor child serves the calibration route only",
    )
    plan, _schedule = _read_calibration_plan_and_schedule(request.plan_path, request.schedule_path)
    require_envelope_binding(
        envelope,
        plan=plan,
        role=CALIBRATION_ROLE_FINAL,
        step_id=_SUCCESSOR_CALIBRATION_STEP,
        run_id=request.run_id,
    )

    def gate() -> object:
        require_calibration_envelope(envelope, role=CALIBRATION_ROLE_FINAL)
        return require_calibration_subset_plan(plan)

    proof = _mint_successor_route_proof(
        SUCCESSOR_ROUTE_CALIBRATION,
        gate=gate,
        gate_name="require_calibration_envelope",
        envelope=envelope,
        plan_digest=plan.plan_digest,
    )
    return _run_successor_final(request, proof)
