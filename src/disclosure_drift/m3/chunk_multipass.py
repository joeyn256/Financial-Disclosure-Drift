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
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, Protocol, cast

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_phases import (
    PHASE_F0,
    PHASE_RESTART_CONTRACT,
    PHASE_STATUS_COMPLETE,
    PhaseCheckpoint,
    write_phase_checkpoint,
)
from disclosure_drift.m3.canary_runtime import process_peak_resident_bytes

# The accepted single-pass merge primitives, imported rather than restated. They are private to
# the consolidator's module because the single-pass consolidator is their only OTHER caller; a
# second expression of any of them here would be a second answer waiting to disagree.
from disclosure_drift.m3.chunk_consolidation import (
    _LOAD_ORDER,
    _MERGE_STRATEGY,
    CORRECTIONS_TABLE,
    ChunkInput,
    FinalWorldReceipt,
    _accepted_plan_state,
    _apply_duplicate_identities,
    _attach_all,
    _columns,
    _deferrable_indexes,
    _detach_all,
    _keyed_first_last_load,
    _load_accession_observations,
    _member_deltas,
    _merge_sidecar,
    _nearest_existing,
    _reduced_parser_run,
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
    CompactEvidenceSidecar,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.m3.offline_parse import write_containment
from disclosure_drift.m3.repository_identity import (
    RepositoryIdentity,
    require_clean_running_repository,
)
from disclosure_drift.m3.single_source_canary import (
    phase_execution_identity,
    require_f0_success,
)
from disclosure_drift.m3.working_catalog import (
    PROGRESS_LEDGER_FILENAME,
    WORKING_CATALOG_FILENAME,
    RunProgressLedger,
    WorkingCatalog,
    file_digest,
)
from disclosure_drift.sec.census import CensusCatalog, _stable_id
from disclosure_drift.sec.census import _json as _stable_json
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = [
    "CALIBRATION_ADMISSION_EVENT_KIND",
    "CALIBRATION_CHUNK_RETAINED_WITNESS_CONTRACT",
    "CALIBRATION_GROUP_CHECKPOINT_EVENT_KIND",
    "CALIBRATION_GROUP_DELETION_EVENT_KIND",
    "CALIBRATION_RETAINED_PAYLOAD_FILENAME",
    "CALIBRATION_RETAINED_WITNESS_FILENAME",
    "CALIBRATION_SUBSET_RESULT_CONTRACT",
    "CALIBRATION_SUBSET_RESULT_FILENAME",
    "INTERMEDIATE_RECEIPT_CONTRACT",
    "INTERMEDIATE_RECEIPT_FILENAME",
    "INTERMEDIATE_WITNESS_FILENAME",
    "MERGE_FAN_IN",
    "MERGE_SCHEDULE_CONTRACT",
    "MERGE_SCHEDULE_FILENAME",
    "MULTIPASS_CONSOLIDATION_CONTRACT",
    "MULTIPASS_REQUEST_KIND_FINAL",
    "MULTIPASS_REQUEST_KIND_GROUP",
    "REAL_MULTIPASS_F0_AUTHORITY",
    "STORAGE_PLAN_FILENAME",
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
    "IntermediateInput",
    "IntermediateReceipt",
    "MergeGroup",
    "MergeSchedule",
    "MultipassResult",
    "PlanWitnessSource",
    "RetainedWitnessInput",
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
    "require_multipass_plan",
    "require_real_multipass_authority",
    "require_sealed_schedule",
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
    "select_group_inputs",
    "stable_binding_identity",
    "stage_first_witness_corrections",
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

    def _identity_inputs(self) -> dict[str, object]:
        return {
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
        present = {str(key) for key in record}
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
        if (
            not isinstance(counts, Mapping)
            or not isinstance(admission, Mapping)
            or not isinstance(manifest, Mapping)
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
