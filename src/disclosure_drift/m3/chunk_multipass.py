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
not sufficient: **storage admission is the second gate.** Before a level-1 world or the final
world is created, the step's projected peak plus the governed reserve plus the transient allowance
must be free on the internal tier (:mod:`~disclosure_drift.m3.chunk_tiering`). Every owner term is
``None`` and ``None`` refuses, so an open authority alone admits nothing, and no parameter of any
production entry substitutes for the owner terms. No input is deleted, spilled or reclaimed by
anything here, no command-line surface reaches this module, and no environment variable is read.

**The final receipt's four correction counters are whole-F0 -- D151-C15 R1.** The accepted
single-pass receipt reports the cross-chunk first-witness correction its consolidation applied over
its plan's chunks. The multipass receipt reports exactly that quantity over ITS plan's chunks,
derived at level 2 from the retained, authenticated chunk artifacts by the accepted definition
(:func:`_plan_first_witness_counters`) -- never the stage counts of either level, and never their
sum -- so the value is a function of the sealed plan and not of the level-1 grouping.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final, cast

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
)
from disclosure_drift.m3.chunk_evidence import (
    CHUNK_PLAN_FILENAME,
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
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
    _read_json_object,
    _require_process_dead,
    table_row_counts,
)
from disclosure_drift.m3.chunk_plan import (
    CHUNK_REGION_ORDER,
    MULTIPASS_PLAN_CONTRACT,
    SINGLE_PASS_CHUNK_CAP,
    ChunkBounds,
    ChunkPlan,
    require_chunkable_source,
    require_sealed_plan,
)
from disclosure_drift.m3.chunk_storage import (
    authoritative_input,
    derive_chunk_placement,
    internal_free_bytes,
)
from disclosure_drift.m3.chunk_tiering import (
    MergeAdmission,
    MultipassStoragePlan,
    MultipassStorageRequirements,
    accepted_multipass_storage_requirements,
    merge_step_requirement,
    plan_multipass_storage,
    require_merge_admission,
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
    "ChunkMultipassError",
    "FinalMergeRequest",
    "GroupMergeRequest",
    "IntermediateInput",
    "IntermediateReceipt",
    "MergeGroup",
    "MergeSchedule",
    "MultipassResult",
    "completed_intermediate_receipt",
    "derive_merge_schedule",
    "finalize_multipass_body",
    "group_by_id",
    "group_chunks",
    "intermediate_attempt_directory",
    "merge_group_body",
    "next_intermediate_attempt_directory",
    "require_multipass_plan",
    "require_real_multipass_authority",
    "require_sealed_schedule",
    "resolve_intermediate_inputs",
    "run_final_merge",
    "run_group_merge",
    "run_multipass_f0",
    "select_group_inputs",
    "stage_first_witness_corrections",
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
    derived = derive_merge_schedule(plan)
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


def _plan_first_witness_counters(
    connection: sqlite3.Connection, chunks: Sequence[ChunkInput]
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
    :func:`~disclosure_drift.m3.chunk_consolidation._member_deltas` itself. The statement count is
    a constant plus two per chunk -- one insert of its accession rows, one of its ledger -- never
    one per accession or per rival.

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
            if not isinstance(storage, Mapping):
                message = "a group merge request's storage requirements are not a mapping"
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
            if not isinstance(storage, Mapping) or not isinstance(observations, list):
                message = "a final merge request's storage or observations are not of shape"
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
    target: Path,
    input_bytes: int,
    seed_catalog_bytes: int,
    peak_ratio: float,
    requirements: MultipassStorageRequirements,
) -> MergeAdmission:
    """The load-bearing storage gate, run BEFORE the step's world directory exists -- §20."""
    requirement = merge_step_requirement(
        step=step,
        input_bytes=input_bytes,
        seed_catalog_bytes=seed_catalog_bytes,
        peak_ratio=peak_ratio,
        requirements=requirements,
    )
    return require_merge_admission(
        free_bytes=internal_free_bytes(_nearest_existing(target)), requirement=requirement
    )


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
    computed from their authenticated byte lengths and recorded; each level-1 group that already
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
    )
    _write_or_require_same(
        multipass_root / STORAGE_PLAN_FILENAME, dict(storage_plan.as_record()), "storage plan"
    )
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
        target=world_directory,
        input_bytes=sum(receipt.manifest.total_bytes for receipt in receipts),
        seed_catalog_bytes=catalog_bytes,
        peak_ratio=requirements.level_two_peak_ratio,
        requirements=requirements,
    )
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
