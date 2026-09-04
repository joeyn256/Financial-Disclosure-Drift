"""Tiered-storage lifecycle, admission and spill design for a multipass F0 -- D151-C13 addendum.

**What this module decides, and what it deliberately cannot do.** A canonical F0 with more than
nine chunks retains every completed chunk, builds level-1 intermediates from them, and builds one
final world from the intermediates. Every one of those artifacts lives on the internal tier while
it is being written, and the owner's D151-C13 tiered-storage addendum states the future model for
where they live afterwards: completed and verified internally, retained internally while the
admission model says the next merge can start, copied to a **qualified** external tier when
internal headroom approaches the governed boundary, verified byte-exactly at the destination, and
only then -- under a **separate** reclaim authority -- reclaimable internally. This module states
that model as durable states, monotonic transitions, an admission rule, a deterministic spill seam
and an abstract qualification predicate. It holds **no copy capability and no removal capability**:
nothing here transfers a byte or removes one, and a test asserts that against the source text.

**Admission is a precondition, never a discovery.** Before every level-1 group merge and before
the level-2 finalization, free internal space must cover the step's projected peak requirement plus
the governed reserve plus the transient allowance. The projected peak is arithmetic over the
authenticated byte lengths of the inputs that already exist; the reserve, the peak ratios and the
transient allowance are owner terms, and every one of them is ``None`` in C13. ``None`` refuses. It
is never read as zero, never inferred from the host, never defaulted, and there is no environment
variable, configuration key or command-line flag that substitutes for it. A real multipass
execution is therefore NOT ADMISSIBLE after C13, mechanically: the terms it would need do not exist.

**All inputs remain retained.** C13 holds no transfer authority, no reclaim authority and no
external-storage authority, so the storage plan assumes every chunk and every intermediate stays
exactly where it was written. The plan's reclaimable byte count is zero by construction, and the
admission arithmetic never credits space it would have to delete something to obtain.

**Qualification is a predicate, not a mount point.** :data:`QUALIFIED_EXTERNAL_TIER` is ``None``.
A candidate tier is admitted only when it is exactly the owner-qualified one, and the predicate
takes no filesystem path at all: a mounted directory is evidence that something is mounted, never
that it is the qualified device, filesystem, topology and mount identity the owner will bind.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3 import external_working_root as _external
from disclosure_drift.m3.chunk_evidence import TRANSFER_RECEIPT_FILENAME
from disclosure_drift.m3.chunk_plan import CHUNK_REGION_ORDER, ChunkPlan
from disclosure_drift.m3.chunk_storage import (
    REAL_CHUNK_TRANSFER_AUTHORITY,
    REAL_INTERNAL_RECLAIM_AUTHORITY,
    STATE_COMPLETE_INTERNAL,
    STATE_INTERNAL_RECLAIM_ELIGIBLE,
    STATE_INTERNAL_RECLAIMED,
    STATE_TRANSFER_VERIFIED_EXTERNAL,
    VERIFIED_TRANSFER_RECEIPT_CONTRACT,
    ChunkPlacement,
    TransferReceipt,
    accepted_internal_reserve_bytes,
)
from disclosure_drift.m3.external_working_root import (
    SQLITE_TMPDIR_ENV,
    ExternalWorkingRootError,
    VolumeIdentity,
    VolumeIdentityProvider,
    require_usable_sqlite_temp_root,
)
from disclosure_drift.m3.host_a_ssd_qualification import (
    HostASsdQualification,
    require_copy_capable,
)

__all__ = [
    "external_tier_from_qualification",
    "reclaim_eligibility_with_tier",
    "ARTIFACT_LIFECYCLE_STATES",
    "LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS",
    "LIFECYCLE_EXTERNAL_COPY_VERIFIED",
    "LIFECYCLE_INTERNAL_COMPLETE",
    "LIFECYCLE_INTERNAL_RECLAIMED",
    "LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE",
    "LIFECYCLE_TRANSITIONS",
    "MERGE_LEVELS",
    "MERGE_LEVEL_ONE",
    "MERGE_LEVEL_TWO",
    "MULTIPASS_LEVEL_ONE_PEAK_RATIO",
    "MULTIPASS_LEVEL_TWO_PEAK_RATIO",
    "MULTIPASS_STORAGE_PLAN_CONTRACT",
    "SQLITE_TEMP_BINDING_ATTACHMENT_FIELDS",
    "SQLITE_TEMP_BINDING_FIELDS",
    "SQLITE_TEMP_BINDING_STABLE_FIELDS",
    "STORAGE_PLAN_IDENTITY_KEY",
    "SUPERSEDED_STORAGE_PLAN_CONTRACTS",
    "MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES",
    "MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES",
    "PRODUCTION_SPILL_POLICY",
    "QUALIFIED_EXTERNAL_TIER",
    "SqliteTempBinding",
    "SPILL_POLICIES",
    "SPILL_POLICY_LARGEST_ARTIFACT",
    "SPILL_POLICY_PLAN_ORDINAL",
    "SPILL_POLICY_REGION_THEN_ORDINAL",
    "SPILL_POLICY_SEALED_ORDER",
    "TRANSFER_RECEIPT_REQUIRED_BINDINGS",
    "ChunkTieringError",
    "ExternalTierQualification",
    "LifecycleEvidence",
    "MergeAdmission",
    "MergeStepRequirement",
    "MultipassStoragePlan",
    "MultipassStorageRequirements",
    "ReclaimEligibility",
    "SpillProposal",
    "accepted_multipass_storage_requirements",
    "derive_artifact_lifecycle",
    "external_tier_is_qualified",
    "merge_step_requirement",
    "plan_multipass_storage",
    "production_spill_policy",
    "propose_spill",
    "reclaim_eligibility",
    "require_internal_reclaim",
    "require_lifecycle_transition",
    "require_merge_admission",
    "require_qualified_external_tier",
    "require_sufficient_spill",
    "require_transfer_receipt_bindings",
    "transfer_receipt_bindings_of",
]


class ChunkTieringError(DisclosureDriftError):
    """A tiered-storage precondition failed. Never worked around, never best-effort."""


# --------------------------------------------------------------------------- #
# Owner terms. Every one is None, and None refuses.
# --------------------------------------------------------------------------- #
#: The projected peak of a level-1 group merge, as a multiple of its inputs' authenticated bytes.
#: **Closed** -- D151-C13 §20. A level-1 world is seeded from a copy of the operational catalog,
#: bulk-loads every input's rows through a write-ahead log and rebuilds its indexes; how much
#: larger than its inputs that transiently gets is a measurement the owner will freeze, not a
#: number this record guesses. ``None`` refuses every admission that would need it.
MULTIPASS_LEVEL_ONE_PEAK_RATIO: Final[float | None] = None

#: The projected peak of the level-2 finalization, as a multiple of the intermediates' bytes.
#: **Closed** for the same reason.
MULTIPASS_LEVEL_TWO_PEAK_RATIO: Final[float | None] = None

#: The LEVEL-1 transient allowance beside one group merge -- D151-C17 R5. SQLite temporary
#: space, the level-1 correction tables, the receipt and manifest writes. **Closed**: measured on
#: the eventual host, never assumed, and never borrowed from the level-2 term.
MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES: Final[int | None] = None

#: The LEVEL-2 transient allowance beside the finalization -- D151-C17 R5, closing D151-C16
#: MINOR-1. **Closed**, and separately closed: level 2 is not level 1 with more inputs. Only
#: level 2 materializes WHOLE-PLAN temporary state, so its allowance is a different measurement
#: and is never satisfied by :data:`MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES`.
#:
#: **What the eventual measurement must be, and by what method.** The quantity that freezes this
#: term is the TOTAL SQLITE TEMPORARY FILESYSTEM HIGH-WATER across the whole governed finalizer:
#: the peak temporary allocation on the volume :func:`require_sqlite_temp_binding` binds, at any
#: instant of the run. It is **not** a sum of estimated table sizes.
#:
#: The method is the accepted one, and it is not negotiable, because D140-R7 already settled it:
#: SQLite's spill is **not observable from outside the spilling process** -- it unlinks the files
#: it is still writing, so a traversal of the temporary root reads a lower bound of unknown
#: tightness that is *zero during a large sort*. See
#: :func:`~disclosure_drift.m3.external_working_root._visible_directory_allocation`, whose whole
#: docstring is that warning, and
#: :data:`~disclosure_drift.m3.external_working_root.UNMEASURED_UNLINKED_SQLITE_TEMP`, the status
#: an honest observation carries instead of a fabricated zero. **Free space is the authoritative
#: signal**: a ``statvfs`` counts allocated unlinked blocks, which is exactly what a spill
#: consumes. So this term is frozen from the observed FREE-SPACE DRAWDOWN on the bound volume,
#: sampled across the finalizer and taken at its high-water -- never from a directory walk, and
#: never from a schema enumeration.
#:
#: No enumeration of named temporary relations is the whole cost either: the whole-plan window
#: functions in :func:`~disclosure_drift.m3.chunk_consolidation._member_deltas` and in the
#: Level-Two witness-ranking query sort their whole input, and SQLite serves that from sorter
#: and transient-B-tree workfiles that are not named tables and cannot be read out of
#: ``temp.sqlite_master`` at all. A measurement that enumerates tables therefore systematically
#: understates this term.
#:
#: **So: measure the filesystem, not the schema.** Named-table and page counts are legitimate
#: supporting diagnostics; they are never the quantity. A future storage-qualification session
#: that reports only a named-relation enumeration, or a traversal of the temporary root, has not
#: measured this term.
#:
#: LEGACY MONOLITHIC LEVEL-2 TRANSIENT REGIME
#:
#: The historical observation the method was drawn from, under the accepted one-transaction
#: finalizer: D151-C15 §INFO-2 projected this from two tables. D151-C16 measured the real
#: finalizer and found SIX temporary tables coexisting at the counter peak::
#:
#:     chunk_observation_corrections   the level-2 staged correction rows
#:     chunk_witness_rank              the level-2 ranking over the intermediates
#:     plan_chunk_witnesses            every chunk's canonical accession rows, whole plan
#:     plan_witness_rank               a SECOND copy of that, same cardinality, ranked
#:     chunk_first_witness             every chunk's first-witness ledger, whole plan
#:     chunk_member_delta              the reduced member deltas
#:
#: SUCCESSOR DURABLE-STAGE LEVEL-2 STORAGE REGIME
#:
#: The durable-stage successor (D151-C31R2-R19A-C2) replaces those TEMP relations, on its route
#: only, with six persistent successor relations inside the world catalog::
#:
#:     m3_l2_chunk_observation_corrections
#:     m3_l2_chunk_witness_rank
#:     m3_l2_plan_chunk_witnesses
#:     m3_l2_plan_witness_rank
#:     m3_l2_chunk_first_witness
#:     m3_l2_chunk_member_delta
#:
#: The six successor persistent relations are charged as WORLD-VOLUME growth: they are pages of
#: ``working_catalog.sqlite3`` and belong to the world's peak, not to this term. The successor's
#: unlinked sorter, transient B-tree, workfile and other SQLite temporary allocation are charged
#: to the SQLITE_TMPDIR volume as its high-water, and that is what this term bounds on the
#: successor route. :data:`MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES` remains ``None``: R21 must
#: remeasure the successor transient high-water, and R19A-C2 freezes no production storage value.
#: The regime-independent measurement method above governs this successor transient term
#: unchanged.
MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES: Final[int | None] = None

#: The two merge levels, named once. A storage step is charged at exactly one of them, and the
#: name is carried in the step's own record so a sealed plan cannot later be read as if the other
#: level's allowance had applied.
MERGE_LEVEL_ONE: Final = "level-1"
MERGE_LEVEL_TWO: Final = "level-2"
MERGE_LEVELS: Final[tuple[str, ...]] = (MERGE_LEVEL_ONE, MERGE_LEVEL_TWO)

#: Which deterministic spill policy production will use. **Closed** -- addendum §5. The four
#: candidate keys are exposed below so their consequences can be analyzed; none is frozen.
PRODUCTION_SPILL_POLICY: Final[str | None] = None

#: This storage plan's own contract identity, folded into every plan identity. ``/2`` since
#: D151-C19 R4A: the record durably binds the measured SQLite temporary placement the admission
#: relied on (:class:`SqliteTempBinding`), and its persisted document carries the identity that
#: seals it (:data:`STORAGE_PLAN_IDENTITY_KEY`).
MULTIPASS_STORAGE_PLAN_CONTRACT: Final = "m3.3-chunked-f0-multipass-storage-plan/2"

#: Persisted storage-plan contracts this build refuses to read. A ``/1`` record predates the
#: durable temp binding; it is never upgraded, defaulted or reinterpreted (C19-R4A). No real
#: ``/1`` record was ever written: the multipass authority has never been open.
SUPERSEDED_STORAGE_PLAN_CONTRACTS: Final[tuple[str, ...]] = (
    "m3.3-chunked-f0-multipass-storage-plan/1",
)

#: The key under which a persisted storage-plan document carries its own sealed identity.
STORAGE_PLAN_IDENTITY_KEY: Final = "storage_plan_identity"


# --------------------------------------------------------------------------- #
# Durable lifecycle states and monotonic transitions -- addendum §2
# --------------------------------------------------------------------------- #
#: Immutable and fully verified on the internal tier; no external copy exists.
LIFECYCLE_INTERNAL_COMPLETE: Final = "INTERNAL_COMPLETE"

#: An external directory for the artifact exists and carries no verified transfer receipt.
LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS: Final = "SSD_COPY_IN_PROGRESS"

#: The external copy verifies byte-exactly against the internal receipt's manifest.
LIFECYCLE_EXTERNAL_COPY_VERIFIED: Final = "SSD_COPY_VERIFIED"

#: A verified external copy whose transfer receipt binds everything addendum §7 requires. Still
#: not a deletion: reclaim needs its own authority, which is ``None``.
LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE: Final = "INTERNAL_RECLAIM_ELIGIBLE"

#: Only the verified external copy remains. Reachable only through an explicit reclaim.
LIFECYCLE_INTERNAL_RECLAIMED: Final = "INTERNAL_RECLAIMED"

#: Every lifecycle state, in order.
ARTIFACT_LIFECYCLE_STATES: Final[tuple[str, ...]] = (
    LIFECYCLE_INTERNAL_COMPLETE,
    LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS,
    LIFECYCLE_EXTERNAL_COPY_VERIFIED,
    LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE,
    LIFECYCLE_INTERNAL_RECLAIMED,
)

#: The only transitions a lifecycle may take, each forward by construction. There is no edge from
#: :data:`LIFECYCLE_INTERNAL_COMPLETE` to :data:`LIFECYCLE_INTERNAL_RECLAIMED`, and no edge back.
LIFECYCLE_TRANSITIONS: Final[Mapping[str, frozenset[str]]] = {
    LIFECYCLE_INTERNAL_COMPLETE: frozenset(
        {LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, LIFECYCLE_EXTERNAL_COPY_VERIFIED}
    ),
    LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS: frozenset({LIFECYCLE_EXTERNAL_COPY_VERIFIED}),
    LIFECYCLE_EXTERNAL_COPY_VERIFIED: frozenset({LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE}),
    LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE: frozenset({LIFECYCLE_INTERNAL_RECLAIMED}),
    LIFECYCLE_INTERNAL_RECLAIMED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class LifecycleEvidence:
    """The durable evidence a transition is decided from. Every field is a proof, not a claim."""

    external_tier_qualified: bool = False
    transfer_authority: str | None = None
    external_copy_verified: bool = False
    transfer_receipt_bindings_complete: bool = False
    reclaim_authority: str | None = None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "external_tier_qualified": self.external_tier_qualified,
            "transfer_authority": self.transfer_authority,
            "external_copy_verified": self.external_copy_verified,
            "transfer_receipt_bindings_complete": self.transfer_receipt_bindings_complete,
            "reclaim_authority": self.reclaim_authority,
        }


def require_lifecycle_transition(current: str, target: str, evidence: LifecycleEvidence) -> str:
    """Admit one lifecycle transition, or refuse it -- addendum §2, §6, §7, §9.

    Two questions, in order. Is the edge one the lifecycle has at all? Forward edges only, one
    step at a time, and never from :data:`LIFECYCLE_INTERNAL_COMPLETE` straight to
    :data:`LIFECYCLE_INTERNAL_RECLAIMED`. Then, is the evidence for that edge present? A copy needs
    a qualified tier and a transfer authority; verification needs the copy to have verified;
    eligibility needs a receipt that binds everything §7 requires; reclaim needs its own authority.
    A transfer never implies a reclaim: the verified edge and the reclaimed edge need different
    evidence, and the second is refused while :data:`REAL_INTERNAL_RECLAIM_AUTHORITY` is ``None``.

    Raises:
        ChunkTieringError: the edge does not exist, or its evidence is absent.
    """
    if current not in LIFECYCLE_TRANSITIONS or target not in ARTIFACT_LIFECYCLE_STATES:
        message = (
            f"lifecycle transition {current!r} -> {target!r} names a state this build does not "
            f"have; the states are {list(ARTIFACT_LIFECYCLE_STATES)}"
        )
        raise ChunkTieringError(message)
    if target not in LIFECYCLE_TRANSITIONS[current]:
        message = (
            f"lifecycle transition {current!r} -> {target!r} is not an edge of the lifecycle. "
            "Transitions are monotonic and evidence-backed, one step at a time; in particular "
            "INTERNAL_COMPLETE never reaches INTERNAL_RECLAIMED without a separately verified "
            "external copy and an explicit reclaim authority in between"
        )
        raise ChunkTieringError(message)
    if target in {LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS, LIFECYCLE_EXTERNAL_COPY_VERIFIED}:
        if not evidence.external_tier_qualified:
            message = (
                f"lifecycle transition {current!r} -> {target!r} needs a QUALIFIED external tier "
                "and none is qualified; a mounted path is never inferred to be one"
            )
            raise ChunkTieringError(message)
        if evidence.transfer_authority is None:
            message = (
                f"lifecycle transition {current!r} -> {target!r} needs an explicit transfer "
                "authority and REAL_CHUNK_TRANSFER_AUTHORITY is None; nothing is copied"
            )
            raise ChunkTieringError(message)
    if target == LIFECYCLE_EXTERNAL_COPY_VERIFIED and not evidence.external_copy_verified:
        message = (
            "a copy is not verified merely because it completed: destination verification "
            "independent of the source filesystem cache is required before SSD_COPY_VERIFIED"
        )
        raise ChunkTieringError(message)
    if target == LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE and not (
        evidence.external_copy_verified and evidence.transfer_receipt_bindings_complete
    ):
        message = (
            "the internal copy is not RECLAIM-ELIGIBLE: eligibility needs a verified external "
            "copy AND a transfer receipt binding every field the addendum requires"
        )
        raise ChunkTieringError(message)
    if target == LIFECYCLE_INTERNAL_RECLAIMED and evidence.reclaim_authority is None:
        message = (
            "internal reclaim is NOT AUTHORIZED: a verified external copy makes the internal copy "
            "RECLAIM-ELIGIBLE, never reclaimed; REAL_INTERNAL_RECLAIM_AUTHORITY is None and a "
            "transfer never implies a deletion"
        )
        raise ChunkTieringError(message)
    return target


def derive_artifact_lifecycle(placement: ChunkPlacement, *, external_root: Path | None) -> str:
    """The lifecycle state one chunk's durable evidence implies -- derived, never declared.

    Built over the accepted :class:`~disclosure_drift.m3.chunk_storage.ChunkPlacement`, which
    already re-read and re-hashed both tiers. One distinction is added on top of it: an external
    directory that exists and carries no verified transfer receipt is a copy **in progress**
    rather than nothing, because a partial copy occupies external capacity and must never be
    mistaken for a verified one. And one distinction is removed: the accepted placement calls a
    chunk with two verified copies reclaim-eligible, whereas the addendum makes eligibility
    additionally depend on the receipt's bindings (:func:`require_reclaim_eligibility`), so two
    verified copies derive to :data:`LIFECYCLE_EXTERNAL_COPY_VERIFIED` here.

    Raises:
        ChunkTieringError: the chunk is not a completed artifact at all.
    """
    if placement.state == STATE_INTERNAL_RECLAIMED:
        return LIFECYCLE_INTERNAL_RECLAIMED
    if placement.state in {STATE_TRANSFER_VERIFIED_EXTERNAL, STATE_INTERNAL_RECLAIM_ELIGIBLE}:
        return LIFECYCLE_EXTERNAL_COPY_VERIFIED
    if placement.state != STATE_COMPLETE_INTERNAL:
        message = (
            f"chunk {placement.chunk_id!r} is in placement state {placement.state!r} and is not "
            "a completed artifact; a lifecycle is derived only for a chunk whose terminal "
            "receipt verifies"
        )
        raise ChunkTieringError(message)
    if external_root is not None:
        candidate = external_root / placement.chunk_id
        if (
            candidate.is_dir()
            and not candidate.is_symlink()
            and not (candidate / TRANSFER_RECEIPT_FILENAME).is_file()
        ):
            return LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS
    return LIFECYCLE_INTERNAL_COMPLETE


# --------------------------------------------------------------------------- #
# The transfer receipt the future real transfer must write -- addendum §7
# --------------------------------------------------------------------------- #
#: Every binding a future create-once transfer receipt must carry, and carry non-empty. The
#: accepted ``m3.3-chunked-f0-transfer-receipt/1`` binds a strict subset of these, which is
#: exactly why :func:`require_reclaim_eligibility` refuses it: a receipt that cannot say which
#: source repository, which destination path and which transfer instant produced the copy is
#: verification evidence, not reclaim evidence.
TRANSFER_RECEIPT_REQUIRED_BINDINGS: Final[tuple[str, ...]] = (
    "source_chunk_id",
    "source_manifest_digest",
    "source_receipt_sha256",
    "source_bytes",
    "source_plan_digest",
    "source_repository_head_sha",
    "source_repository_tree_sha",
    "destination_volume_identity",
    "destination_canonical_path",
    "destination_bytes",
    "destination_manifest_verified",
    "destination_content_verified",
    "transfer_started_at_utc",
    "transfer_completed_at_utc",
    "transfer_outcome",
)


def require_transfer_receipt_bindings(record: Mapping[str, object]) -> Mapping[str, object]:
    """Return ``record`` only if it binds every field addendum §7 requires, non-empty.

    Raises:
        ChunkTieringError: a required binding is absent, ``None`` or empty, or the outcome is
            not ``"verified"``.
    """
    missing = [
        name
        for name in TRANSFER_RECEIPT_REQUIRED_BINDINGS
        if record.get(name) is None or record.get(name) == ""
    ]
    if missing:
        message = (
            f"a transfer receipt does not bind {missing}; only a receipt carrying every "
            "required binding may make an internal copy RECLAIM-ELIGIBLE, and this one is "
            "verification evidence at most"
        )
        raise ChunkTieringError(message)
    if record.get("transfer_outcome") != "verified":
        message = (
            f"a transfer receipt records outcome {record.get('transfer_outcome')!r}; only a "
            "'verified' outcome may confer eligibility"
        )
        raise ChunkTieringError(message)
    for flag in ("destination_manifest_verified", "destination_content_verified"):
        if record.get(flag) is not True:
            message = f"a transfer receipt records {flag} = {record.get(flag)!r}; True is required"
            raise ChunkTieringError(message)
    return record


def transfer_receipt_bindings_of(receipt: TransferReceipt) -> Mapping[str, object]:
    """The addendum-§7 bindings an accepted ``/1`` transfer receipt can supply, and no more.

    Stated as a mapping so the gap is visible: the fields the ``/1`` contract binds are renamed
    onto the required names, and every required name it cannot supply is simply absent. Handing
    the result to :func:`require_transfer_receipt_bindings` therefore refuses, which is the
    correct answer for a receipt the addendum did not design.
    """
    return {
        "source_chunk_id": receipt.chunk_id,
        "source_manifest_digest": receipt.chunk_receipt_manifest_digest,
        "source_plan_digest": receipt.plan_digest,
        "destination_volume_identity": receipt.destination_volume_uuid,
        "destination_bytes": receipt.bytes_transferred,
        "destination_manifest_verified": receipt.destination_manifest.digest
        == receipt.chunk_receipt_manifest_digest,
        "destination_content_verified": receipt.status == "verified",
        "transfer_completed_at_utc": receipt.verified_at_utc,
        "transfer_outcome": receipt.status,
    }


@dataclass(frozen=True, slots=True)
class ReclaimEligibility:
    """What a governed reclaim would rest on. A computation; never an action."""

    chunk_id: str
    lifecycle: str
    eligible: bool
    reclaim_authority: str | None
    proofs: Mapping[str, bool]
    detail: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "chunk_id": self.chunk_id,
            "lifecycle": self.lifecycle,
            "eligible": self.eligible,
            "reclaim_authority": self.reclaim_authority,
            "proofs": dict(sorted(self.proofs.items())),
            "detail": self.detail,
        }


def reclaim_eligibility(
    placement: ChunkPlacement,
    *,
    transfer_record: Mapping[str, object] | None,
    external_root: Path | None = None,
) -> ReclaimEligibility:
    """Decide whether one internal copy is RECLAIM-ELIGIBLE. A computation; never an action.

    Eligibility needs all of: a verified external copy (the accepted placement proofs), a
    transfer receipt binding every addendum-§7 field, an internal copy that still exists, and
    the internal copy never being the only verified one. Eligible is not reclaimed: performing
    a reclaim is :func:`require_internal_reclaim`, which refuses.

    Raises:
        ChunkTieringError: the chunk is not a completed artifact.
    """
    lifecycle = derive_artifact_lifecycle(placement, external_root=external_root)
    bindings_complete = False
    if transfer_record is not None:
        try:
            require_transfer_receipt_bindings(transfer_record)
        except ChunkTieringError:
            bindings_complete = False
        else:
            bindings_complete = True
    proofs = {
        "internal_copy_present": placement.internal_directory is not None,
        "external_copy_verified": lifecycle == LIFECYCLE_EXTERNAL_COPY_VERIFIED,
        "transfer_receipt_bindings_complete": bindings_complete,
        "never_the_only_verified_copy": placement.has_verified_external,
    }
    eligible = all(proofs.values())
    return ReclaimEligibility(
        chunk_id=placement.chunk_id,
        lifecycle=lifecycle,
        eligible=eligible,
        reclaim_authority=REAL_INTERNAL_RECLAIM_AUTHORITY,
        proofs=proofs,
        detail=(
            "RECLAIM-ELIGIBLE and NOT reclaimed: reclaim needs a separate authority, which is "
            "None, and a mechanism this module does not hold"
            if eligible
            else "not eligible: at least one proof is absent"
        ),
    )


def require_internal_reclaim(eligibility: ReclaimEligibility) -> str:
    """The token authorizing the reclaim of one eligible internal copy, or a refusal.

    Two refusals, in order: an ineligible copy is refused on eligibility, and an eligible one is
    refused on authority -- :data:`REAL_INTERNAL_RECLAIM_AUTHORITY` is ``None``, so every call
    refuses in C13, and there is no removal capability anywhere in this module for a token to
    enable. A transfer never implies a reclaim.

    Raises:
        ChunkTieringError: always, while the authority is ``None``.
    """
    if not eligibility.eligible:
        message = (
            f"internal reclaim of chunk {eligibility.chunk_id!r} is refused: the copy is not "
            f"RECLAIM-ELIGIBLE (lifecycle {eligibility.lifecycle!r}, proofs "
            f"{dict(sorted(eligibility.proofs.items()))}). Nothing was deleted"
        )
        raise ChunkTieringError(message)
    granted = REAL_INTERNAL_RECLAIM_AUTHORITY
    if granted is None:
        message = (
            f"internal reclaim of chunk {eligibility.chunk_id!r} is NOT AUTHORIZED: "
            "REAL_INTERNAL_RECLAIM_AUTHORITY is None. A verified external copy makes the "
            "internal copy RECLAIM-ELIGIBLE, never reclaimed; nothing was deleted, and this "
            "module holds no removal capability"
        )
        raise ChunkTieringError(message)
    return granted  # pragma: no cover - unreachable while the authority is None


# --------------------------------------------------------------------------- #
# The external-tier qualification predicate -- addendum §6
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ExternalTierQualification:
    """What the owner binds when the actual Host-A external topology is qualified.

    Every field is a fact about the device, its filesystem, its topology, its mount identity, its
    capacity, its measured sustained behaviour, its round-trip verification and its disconnect
    semantics. None of them is derivable from a path; all of them are recorded by the owner's
    qualification instrument, which does not exist in C13.
    """

    volume_identity: str
    filesystem: str
    physical_topology: str
    mount_identity: str
    writable_capacity_bytes: int
    sustained_copy_bytes_per_second: int
    sustained_read_bytes_per_second: int
    round_trip_verified: bool
    disconnect_semantics: str
    qualified_by: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "volume_identity": self.volume_identity,
            "filesystem": self.filesystem,
            "physical_topology": self.physical_topology,
            "mount_identity": self.mount_identity,
            "writable_capacity_bytes": self.writable_capacity_bytes,
            "sustained_copy_bytes_per_second": self.sustained_copy_bytes_per_second,
            "sustained_read_bytes_per_second": self.sustained_read_bytes_per_second,
            "round_trip_verified": self.round_trip_verified,
            "disconnect_semantics": self.disconnect_semantics,
            "qualified_by": self.qualified_by,
        }


#: The one external tier a real spill may target. ``None`` -- addendum §6: the owner qualifies
#: the actual Host-A topology separately, and a tier used successfully before is not thereby
#: qualified for this run. There is no path-derived fallback.
QUALIFIED_EXTERNAL_TIER: Final[ExternalTierQualification | None] = None


def external_tier_is_qualified(candidate: ExternalTierQualification | None) -> bool:
    """Whether ``candidate`` is exactly the owner-qualified tier. Never inferred from a path."""
    return (
        QUALIFIED_EXTERNAL_TIER is not None
        and candidate is not None
        and candidate == QUALIFIED_EXTERNAL_TIER
        and candidate.round_trip_verified
    )


def require_qualified_external_tier(
    candidate: ExternalTierQualification | None,
) -> ExternalTierQualification:
    """Return the qualified tier ``candidate`` names, or refuse.

    Raises:
        ChunkTieringError: no tier is qualified, no candidate was named, or the candidate is
            not the qualified one.
    """
    if QUALIFIED_EXTERNAL_TIER is None:
        message = (
            "no external tier is qualified: QUALIFIED_EXTERNAL_TIER is None. A real SSD spill "
            "needs the owner to qualify the actual Host-A topology -- device, filesystem, "
            "topology, mount identity, capacity, sustained behaviour, round-trip verification "
            "and disconnect semantics -- and a mounted path is never inferred to be it"
        )
        raise ChunkTieringError(message)
    if candidate is None or not external_tier_is_qualified(candidate):
        message = (
            "the named external tier is not the qualified one; a spill onto an unqualified "
            "tier is refused before anything is copied"
        )
        raise ChunkTieringError(message)
    return candidate


# --------------------------------------------------------------------------- #
# SQLite temporary placement -- D151-C17 R6, closing D151-C16 MINOR-2
# --------------------------------------------------------------------------- #
#: Every field of a :class:`SqliteTempBinding` record, in its recorded order. A record is exact:
#: a key missing or unexpected -- including the three-field pre-C19 shape -- is refused.
SQLITE_TEMP_BINDING_FIELDS: Final[tuple[str, ...]] = (
    "temp_root_device",
    "temp_root_inode",
    "temp_volume_uuid",
    "temp_filesystem_type",
    "temp_device_identifier",
    "charged_volume_uuid",
    "charged_filesystem_type",
    "charged_device_identifier",
)

#: The binding fields that identify the temporary root and both volumes **stably** across a
#: detach and re-attach of the same volume -- D151-C21 R4 (closing D151-C20 MINOR-4).
#:
#: A volume keeps its Volume UUID and filesystem type across reboots and re-plugs, and a
#: directory keeps its inode while it exists on that volume; those are the facts a governed
#: restart may continue on. Every one of them still moves the full document identity: this is a
#: classification for the restart comparison, never a second seal.
SQLITE_TEMP_BINDING_STABLE_FIELDS: Final[tuple[str, ...]] = (
    "temp_root_inode",
    "temp_volume_uuid",
    "temp_filesystem_type",
    "charged_volume_uuid",
    "charged_filesystem_type",
)

#: The **attachment-instance** observations -- D151-C21 R4. ``st_dev`` and ``diskNsM`` are
#: assigned at attach time and legitimately differ after a detach and re-attach of the very same
#: volume, so they are recorded and sealed (every field moves the document identity, and an
#: edited record refuses) but they never decide, on their own, that a restart is incompatible.
#: A merge child still compares all eight fields against the binding its parent measured NOW.
SQLITE_TEMP_BINDING_ATTACHMENT_FIELDS: Final[tuple[str, ...]] = (
    "temp_root_device",
    "temp_device_identifier",
    "charged_device_identifier",
)


def _measured_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = f"a SQLite temp binding's {name!r} must be a non-negative integer; got {value!r}"
        raise ChunkTieringError(message)
    return value


@dataclass(frozen=True, slots=True)
class SqliteTempBinding:
    """Measured proof that SQLite's spill lands on the filesystem admission charges -- C19-R4.

    Every field is a measurement taken by the process that holds the record, never a claim
    handed to it. The temporary root is identified by the device and inode numbers of the
    directory SQLite will use -- a filesystem identity that carries **no** path, for the reason
    :meth:`~disclosure_drift.m3.external_working_root.VolumeIdentity.as_record` states -- and
    both volumes are the accepted D137-R8 identities. The binding RESULT is not a Boolean anyone
    could set: it is the two measured volume identities, which the constructor requires to agree,
    so a record whose volumes differ cannot exist.

    Two classifications of the same eight fields serve two different questions (D151-C21 R4).
    :meth:`as_record` is the whole measurement and is what the storage-plan document seals and
    what a merge child is held to. :meth:`stable_record` is the subset that survives a detach
    and re-attach of the same volume -- :data:`SQLITE_TEMP_BINDING_STABLE_FIELDS` -- and is what
    a governed restart is compared on; the attachment-instance observations in
    :data:`SQLITE_TEMP_BINDING_ATTACHMENT_FIELDS` are sealed but do not decide that comparison.
    """

    temp_root_device: int
    temp_root_inode: int
    temp_volume_uuid: str
    temp_filesystem_type: str
    temp_device_identifier: str
    charged_volume_uuid: str
    charged_filesystem_type: str
    charged_device_identifier: str

    def __post_init__(self) -> None:
        _measured_int(self.temp_root_device, "temp_root_device")
        _measured_int(self.temp_root_inode, "temp_root_inode")
        for name in SQLITE_TEMP_BINDING_FIELDS[2:]:
            if not isinstance(getattr(self, name), str):
                message = f"a SQLite temp binding's {name!r} must be a string"
                raise ChunkTieringError(message)
        for name in ("temp_volume_uuid", "charged_volume_uuid"):
            if not getattr(self, name).strip():
                message = (
                    f"a SQLite temp binding's {name!r} is blank; an unidentified volume is refused"
                )
                raise ChunkTieringError(message)
        if self.temp_volume_uuid.strip().casefold() != self.charged_volume_uuid.strip().casefold():
            message = (
                "a SQLite temp binding whose temporary volume differs from its charged volume is "
                "not a binding; it is refused rather than recorded"
            )
            raise ChunkTieringError(message)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering that carries **no** absolute path."""
        return {name: getattr(self, name) for name in SQLITE_TEMP_BINDING_FIELDS}

    def stable_record(self) -> Mapping[str, object]:
        """The restart-stable subset of the measurement -- D151-C21 R4.

        Exactly :data:`SQLITE_TEMP_BINDING_STABLE_FIELDS`, in their recorded order. Never
        serialized on its own: the document carries :meth:`as_record`, sealed whole.
        """
        return {name: getattr(self, name) for name in SQLITE_TEMP_BINDING_STABLE_FIELDS}

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> SqliteTempBinding:
        """Rebuild a binding from its exact stored mapping.

        Raises:
            ChunkTieringError: a key is missing or unexpected, a value is not of the recorded
                type, or the two volumes disagree.
        """
        expected = set(SQLITE_TEMP_BINDING_FIELDS)
        present = {str(key) for key in record}
        if present != expected:
            message = (
                "a SQLite temp binding record is exact; this one is missing "
                f"{sorted(expected - present)} and carries unexpected "
                f"{sorted(present - expected)}. A record of another shape -- including the "
                "pre-C19 three-field one -- is refused rather than reinterpreted"
            )
            raise ChunkTieringError(message)
        return cls(
            temp_root_device=_measured_int(record["temp_root_device"], "temp_root_device"),
            temp_root_inode=_measured_int(record["temp_root_inode"], "temp_root_inode"),
            temp_volume_uuid=str(record["temp_volume_uuid"]),
            temp_filesystem_type=str(record["temp_filesystem_type"]),
            temp_device_identifier=str(record["temp_device_identifier"]),
            charged_volume_uuid=str(record["charged_volume_uuid"]),
            charged_filesystem_type=str(record["charged_filesystem_type"]),
            charged_device_identifier=str(record["charged_device_identifier"]),
        )


def require_sqlite_temp_binding(
    *,
    charged_path: Path,
    environ: Mapping[str, str] | None = None,
    provider: VolumeIdentityProvider | None = None,
) -> SqliteTempBinding:
    """Refuse a merge whose SQLite spill would not land where its free space was charged.

    **The defect this closes -- D151-C16 MINOR-2.** :func:`require_merge_admission` charges a
    step's peak, reserve and transient allowance against the free bytes of the filesystem hosting
    the merge world. SQLite does not put its temporary store there. It puts it where
    ``SQLITE_TMPDIR`` says, and if that is unset it falls back to the operating system's
    temporary directory -- on this platform, the internal volume -- silently. A merge could then
    be admitted against one filesystem's free space while spilling whole-plan sorter and
    workfile bytes onto another, which is exactly the accounting the level-2 transient allowance
    exists to make honest.

    **The mechanism is the accepted one, reused rather than restated -- D151-C17 §§11, 12.** The
    identity compared is
    :class:`~disclosure_drift.m3.external_working_root.VolumeIdentity`, obtained through the
    accepted :data:`~disclosure_drift.m3.external_working_root.VolumeIdentityProvider` -- the
    same structured ``diskutil`` reading, resolved from that module's globals at call time so a
    substituted provider reaches this guard too. Nothing here compares path strings, prefixes,
    or writability, and nothing here accepts the presence of an environment variable as proof of
    anything: the variable says where to look, and the volume identity is what decides.

    The conditions, all fail-closed, in the shape D137-R8 established and corrected by C19-R1:

    * an explicitly supplied ``environ`` **agrees** with the process environment SQLite consumes;
    * the raw value is a candidate **SQLite itself will use** -- set, non-blank, free of
      surrounding whitespace, absolute, an existing directory, writable and searchable -- through
      :func:`~disclosure_drift.m3.external_working_root.require_usable_sqlite_temp_root`, the
      ONE validator both guards share (C19-R2);
    * its volume identity **equals** the identity of the filesystem hosting ``charged_path``.

    The returned binding is the whole measurement -- the temporary root's device and inode, both
    volume identities -- and since C19-R4 it is recorded in the sealed storage plan and handed to
    every merge child as the topology it must remeasure and match.

    ``charged_path`` need not exist yet -- a merge world is identified before it is created --
    so its nearest existing ancestor is measured, which is on the same volume by construction.

    Args:
        charged_path: The directory whose free bytes admission will charge.
        environ: A caller or test mapping, cross-checked against the process environment.
        provider: The volume identity provider. ``None`` resolves the accepted one at call time.

    Returns:
        The measured binding, for the caller to record.

    Raises:
        ChunkTieringError: the temporary root is absent, unusable, or on a different volume.
    """
    consumed = os.environ.get(SQLITE_TMPDIR_ENV)
    if environ is not None and environ.get(SQLITE_TMPDIR_ENV) != consumed:
        message = (
            f"the {SQLITE_TMPDIR_ENV} value supplied for validation is not the one SQLite will "
            "read from the process environment; validating one environment while SQLite "
            "consumes another proves nothing about where the spill lands, so the disagreement "
            "is refused rather than resolved in either direction"
        )
        raise ChunkTieringError(message)
    # The candidate conditions are SQLite's own, shared with the accepted D137-R8 guard through
    # ONE validator (C19-R1, C19-R2): the raw value, never a normalized copy; W_OK | X_OK.
    try:
        candidate = require_usable_sqlite_temp_root(consumed)
    except ExternalWorkingRootError as exc:
        message = (
            f"{exc}. A merge world is NOT created: the temporary root is stated explicitly and "
            "verified as the one SQLite will use, never discovered mid-merge"
        )
        raise ChunkTieringError(message) from exc
    try:
        temp_stat = candidate.stat()
    except OSError as exc:
        message = (
            f"the {SQLITE_TMPDIR_ENV} temporary root could not be identified "
            f"({type(exc).__name__}); an identity that cannot be read is refused, never assumed"
        )
        raise ChunkTieringError(message) from exc
    resolve = _external.macos_volume_identity if provider is None else provider
    try:
        temp_volume: VolumeIdentity = resolve(candidate)
        charged_volume: VolumeIdentity = resolve(_external._nearest_existing(charged_path))  # noqa: SLF001 - the accepted pre-creation resolver
    except ExternalWorkingRootError as exc:
        message = (
            f"the volume hosting the merge world or the {SQLITE_TMPDIR_ENV} temporary root could "
            f"not be identified ({exc}); an identity that cannot be read is refused, never "
            "assumed to match"
        )
        raise ChunkTieringError(message) from exc
    if temp_volume.volume_uuid.strip().casefold() != charged_volume.volume_uuid.strip().casefold():
        message = (
            f"{SQLITE_TMPDIR_ENV} is on volume {temp_volume.volume_uuid} and this merge's "
            f"storage admission charges free space on volume {charged_volume.volume_uuid}. "
            "SQLite's spill must be counted by the same capacity model as the world it serves, "
            "so the merge is refused BEFORE any world, attempt directory or database exists"
        )
        raise ChunkTieringError(message)
    return SqliteTempBinding(
        temp_root_device=int(temp_stat.st_dev),
        temp_root_inode=int(temp_stat.st_ino),
        temp_volume_uuid=temp_volume.volume_uuid,
        temp_filesystem_type=temp_volume.filesystem_type,
        temp_device_identifier=temp_volume.device_identifier,
        charged_volume_uuid=charged_volume.volume_uuid,
        charged_filesystem_type=charged_volume.filesystem_type,
        charged_device_identifier=charged_volume.device_identifier,
    )


# --------------------------------------------------------------------------- #
# Admission -- addendum §3, §4; D151-C13 §§18-21
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class MultipassStorageRequirements:
    """The owner terms every merge admission needs. Explicit values only; none is defaulted."""

    internal_reserve_bytes: int
    level_one_peak_ratio: float
    level_two_peak_ratio: float
    level_one_transient_bytes: int
    level_two_transient_bytes: int

    def transient_for(self, level: str) -> int:
        """This requirement's transient allowance for exactly ``level`` -- D151-C17 R5.

        There is no fallback in either direction and no default. A level whose allowance is
        absent is a refusal, never the other level's number: level 2 materializes whole-plan
        temporary state that no level-1 group does, so borrowing level 1's allowance for it would
        under-reserve by exactly the amount D151-C16 MINOR-1 was about, and borrowing level 2's
        for level 1 would silently over-reserve and mask a level-1 measurement error.

        Raises:
            ChunkTieringError: ``level`` is not one of :data:`MERGE_LEVELS`.
        """
        if level == MERGE_LEVEL_ONE:
            return self.level_one_transient_bytes
        if level == MERGE_LEVEL_TWO:
            return self.level_two_transient_bytes
        message = (
            f"a merge step must be charged at exactly one of {list(MERGE_LEVELS)}; got "
            f"{level!r}. A step whose level is not stated has no transient allowance, and an "
            "unknown level is refused rather than resolved to either level's number"
        )
        raise ChunkTieringError(message)

    def __post_init__(self) -> None:
        for name in (
            "internal_reserve_bytes",
            "level_one_transient_bytes",
            "level_two_transient_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                message = (
                    f"storage requirement {name!r} must be a non-negative integer; got {value!r}"
                )
                raise ChunkTieringError(message)
        for name in ("level_one_peak_ratio", "level_two_peak_ratio"):
            ratio = getattr(self, name)
            if isinstance(ratio, bool) or not isinstance(ratio, int | float) or ratio < 1.0:
                message = (
                    f"storage requirement {name!r} must be a ratio of at least 1.0 -- a merge "
                    f"world is never projected smaller than its inputs; got {ratio!r}"
                )
                raise ChunkTieringError(message)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "internal_reserve_bytes": self.internal_reserve_bytes,
            "level_one_peak_ratio": self.level_one_peak_ratio,
            "level_two_peak_ratio": self.level_two_peak_ratio,
            "level_one_transient_bytes": self.level_one_transient_bytes,
            "level_two_transient_bytes": self.level_two_transient_bytes,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> MultipassStorageRequirements:
        """Rebuild the requirements from their stored mapping.

        A record carrying the pre-D151-C17 generic ``transient_bytes`` key is refused rather than
        read: one number cannot answer both levels, and silently treating it as either level's
        allowance is the defect D151-C16 MINOR-2 named.

        Raises:
            ChunkTieringError: a field is absent, carries the superseded generic key, or is not
                of the recorded type.
        """
        if "transient_bytes" in record:
            message = (
                "storage requirements carry the superseded generic 'transient_bytes'; since "
                "D151-C17 a requirement states 'level_one_transient_bytes' and "
                "'level_two_transient_bytes' separately, and a single generic allowance is "
                "refused rather than applied to a level it was not measured for"
            )
            raise ChunkTieringError(message)
        try:
            reserve = record["internal_reserve_bytes"]
            level_one_transient = record["level_one_transient_bytes"]
            level_two_transient = record["level_two_transient_bytes"]
            one = record["level_one_peak_ratio"]
            two = record["level_two_peak_ratio"]
        except KeyError as exc:
            message = f"storage requirements are missing {exc}; refused rather than defaulted"
            raise ChunkTieringError(message) from exc
        if (
            not isinstance(reserve, int)
            or not isinstance(level_one_transient, int)
            or not isinstance(level_two_transient, int)
        ):
            message = "storage requirement byte counts must be integers; refused"
            raise ChunkTieringError(message)
        if not isinstance(one, int | float) or not isinstance(two, int | float):
            message = "storage requirement peak ratios must be numbers; refused"
            raise ChunkTieringError(message)
        return cls(
            internal_reserve_bytes=reserve,
            level_one_peak_ratio=float(one),
            level_two_peak_ratio=float(two),
            level_one_transient_bytes=level_one_transient,
            level_two_transient_bytes=level_two_transient,
        )


def accepted_multipass_storage_requirements() -> MultipassStorageRequirements:
    """The owner-frozen requirements, or a refusal -- D151-C13 §20.

    Raises:
        ChunkTieringError: any term is ``None``. The reserve refuses through the accepted
            :func:`~disclosure_drift.m3.chunk_storage.accepted_internal_reserve_bytes`, so a
            ``None`` reserve is never read as zero here either.
    """
    try:
        reserve = accepted_internal_reserve_bytes()
    except DisclosureDriftError as exc:
        message = (
            "a real multipass consolidation is NOT ADMISSIBLE: no accepted internal reserve is "
            f"frozen ({exc}). No level-1 world is created"
        )
        raise ChunkTieringError(message) from exc
    absent = [
        name
        for name, term in (
            ("MULTIPASS_LEVEL_ONE_PEAK_RATIO", MULTIPASS_LEVEL_ONE_PEAK_RATIO),
            ("MULTIPASS_LEVEL_TWO_PEAK_RATIO", MULTIPASS_LEVEL_TWO_PEAK_RATIO),
            ("MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES", MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES),
            ("MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES", MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES),
        )
        if term is None
    ]
    if (
        MULTIPASS_LEVEL_ONE_PEAK_RATIO is None
        or MULTIPASS_LEVEL_TWO_PEAK_RATIO is None
        or MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES is None
        or MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES is None
    ):
        message = (
            "a real multipass consolidation is NOT ADMISSIBLE: "
            f"{absent} are None. They are measurements the owner freezes in a later reviewed "
            "change; a None term is a REFUSAL, never a zero, no level's term stands in for "
            "another's, and no world is created until every term exists"
        )
        raise ChunkTieringError(message)
    return MultipassStorageRequirements(  # pragma: no cover - unreachable while the terms are None
        internal_reserve_bytes=reserve,
        level_one_peak_ratio=MULTIPASS_LEVEL_ONE_PEAK_RATIO,
        level_two_peak_ratio=MULTIPASS_LEVEL_TWO_PEAK_RATIO,
        level_one_transient_bytes=MULTIPASS_LEVEL_ONE_TRANSIENT_BYTES,
        level_two_transient_bytes=MULTIPASS_LEVEL_TWO_TRANSIENT_BYTES,
    )


@dataclass(frozen=True, slots=True)
class MergeStepRequirement:
    """What one merge step needs free on the internal tier before it may begin."""

    step: str
    level: str
    input_bytes: int
    seed_catalog_bytes: int
    peak_ratio: float
    peak_bytes: int
    reserve_bytes: int
    transient_bytes: int

    @property
    def required_free_bytes(self) -> int:
        """Peak plus reserve plus transient: the whole floor, never a part of it."""
        return self.peak_bytes + self.reserve_bytes + self.transient_bytes

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering.

        ``level`` is inside the record, and therefore inside every identity that folds it, so a
        sealed storage plan states which level's transient allowance each step was charged at and
        cannot afterwards be read as though the other level's had applied -- D151-C17 R5, §16.
        """
        return {
            "step": self.step,
            "level": self.level,
            "input_bytes": self.input_bytes,
            "seed_catalog_bytes": self.seed_catalog_bytes,
            "peak_ratio": self.peak_ratio,
            "peak_bytes": self.peak_bytes,
            "reserve_bytes": self.reserve_bytes,
            "transient_bytes": self.transient_bytes,
            "required_free_bytes": self.required_free_bytes,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> MergeStepRequirement:
        """Rebuild one step from its exact stored mapping -- C19-R4A.

        Raises:
            ChunkTieringError: a key is missing or unexpected, a value is not of the recorded
                type, the level is not a merge level, or the recorded floor is not the sum of
                its parts.
        """
        expected = {
            "step",
            "level",
            "input_bytes",
            "seed_catalog_bytes",
            "peak_ratio",
            "peak_bytes",
            "reserve_bytes",
            "transient_bytes",
            "required_free_bytes",
        }
        present = {str(key) for key in record}
        if present != expected:
            message = (
                f"a storage step record is exact; this one is missing {sorted(expected - present)} "
                f"and carries unexpected {sorted(present - expected)}; refused rather than read"
            )
            raise ChunkTieringError(message)
        level = str(record["level"])
        if level not in MERGE_LEVELS:
            message = (
                f"a storage step record names level {level!r}, not one of {list(MERGE_LEVELS)}"
            )
            raise ChunkTieringError(message)
        ratio = record["peak_ratio"]
        if isinstance(ratio, bool) or not isinstance(ratio, int | float):
            message = "a storage step record's peak ratio must be a number"
            raise ChunkTieringError(message)
        step = cls(
            step=str(record["step"]),
            level=level,
            input_bytes=_measured_int(record["input_bytes"], "input_bytes"),
            seed_catalog_bytes=_measured_int(record["seed_catalog_bytes"], "seed_catalog_bytes"),
            peak_ratio=float(ratio),
            peak_bytes=_measured_int(record["peak_bytes"], "peak_bytes"),
            reserve_bytes=_measured_int(record["reserve_bytes"], "reserve_bytes"),
            transient_bytes=_measured_int(record["transient_bytes"], "transient_bytes"),
        )
        if _measured_int(record["required_free_bytes"], "required_free_bytes") != (
            step.required_free_bytes
        ):
            message = (
                f"a storage step record for {step.step!r} states a floor that is not its peak "
                "plus reserve plus transient; refused rather than read"
            )
            raise ChunkTieringError(message)
        return step


def merge_step_requirement(
    *,
    step: str,
    level: str,
    input_bytes: int,
    seed_catalog_bytes: int,
    peak_ratio: float,
    requirements: MultipassStorageRequirements,
) -> MergeStepRequirement:
    """One step's requirement: ``ceil(inputs x ratio) + seed`` peak, then reserve and transient.

    ``level`` selects the transient allowance through
    :meth:`MultipassStorageRequirements.transient_for`, which has no fallback -- D151-C17 R5.
    The level is required, not inferred from ``step``: a step name is a label, and deriving a
    storage charge from a label is how one level's allowance silently becomes another's.

    Raises:
        ChunkTieringError: a byte quantity is negative, or ``level`` is not a merge level.
    """
    transient = requirements.transient_for(level)
    if input_bytes < 0 or seed_catalog_bytes < 0:
        message = (
            f"a merge step requirement needs non-negative byte quantities; got inputs="
            f"{input_bytes}, seed={seed_catalog_bytes}"
        )
        raise ChunkTieringError(message)
    peak = -(-input_bytes * peak_ratio // 1)  # ceiling, exact for integer-valued products
    return MergeStepRequirement(
        step=step,
        level=level,
        input_bytes=input_bytes,
        seed_catalog_bytes=seed_catalog_bytes,
        peak_ratio=peak_ratio,
        peak_bytes=int(peak) + seed_catalog_bytes,
        reserve_bytes=requirements.internal_reserve_bytes,
        transient_bytes=transient,
    )


@dataclass(frozen=True, slots=True)
class MergeAdmission:
    """One admission decision, with every input it was made from."""

    step: str
    level: str
    free_bytes: int
    required_free_bytes: int
    peak_bytes: int
    reserve_bytes: int
    transient_bytes: int
    admitted: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "step": self.step,
            "level": self.level,
            "free_bytes": self.free_bytes,
            "required_free_bytes": self.required_free_bytes,
            "peak_bytes": self.peak_bytes,
            "reserve_bytes": self.reserve_bytes,
            "transient_bytes": self.transient_bytes,
            "admitted": self.admitted,
        }


def require_merge_admission(
    *, free_bytes: int, requirement: MergeStepRequirement
) -> MergeAdmission:
    """Admit the next merge step onto the internal tier, or refuse it BEFORE its world exists.

    The rule, stated once::

        free_internal_bytes >= step_peak_bytes + internal_reserve_bytes + transient_bytes

    ``>=`` at the floor: the floor itself admits and one byte below refuses. ENOSPC is not a
    control mechanism, a step is never started because only its final artifact would fit, and a
    refusal frees nothing: the caller's options are a governed spill of a completed artifact onto
    a qualified tier -- which needs authority this build does not hold -- or a STOP for the owner.

    Raises:
        ChunkTieringError: the floor is not met, or ``free_bytes`` is negative.
    """
    if free_bytes < 0:
        message = f"an admission decision needs a non-negative free-space reading; got {free_bytes}"
        raise ChunkTieringError(message)
    required = requirement.required_free_bytes
    decision = MergeAdmission(
        step=requirement.step,
        level=requirement.level,
        free_bytes=free_bytes,
        required_free_bytes=required,
        peak_bytes=requirement.peak_bytes,
        reserve_bytes=requirement.reserve_bytes,
        transient_bytes=requirement.transient_bytes,
        admitted=free_bytes >= required,
    )
    if not decision.admitted:
        message = (
            f"merge step {requirement.step!r} is NOT ADMITTED onto the internal tier: "
            f"{free_bytes} bytes free, below the required {required} = {requirement.peak_bytes} "
            f"projected peak + {requirement.reserve_bytes} reserve + "
            f"{requirement.transient_bytes} transient at {requirement.level}. STOP: no world "
            "is created. Nothing was "
            "deleted, spilled, reclaimed or cleaned to reach the floor, and there is no mode "
            "that writes until the filesystem refuses"
        )
        raise ChunkTieringError(message)
    return decision


@dataclass(frozen=True, slots=True)
class MultipassStoragePlan:
    """The deterministic storage requirement of one whole multipass consolidation.

    Every term is either authenticated evidence -- the chunks' manifest byte lengths -- or an
    explicit owner term carried in ``requirements``. All inputs are assumed retained: the plan's
    reclaimable byte count is zero, its reclaim and transfer authorities are the closed constants,
    and no external tier is qualified. The identity digest folds every number, so a plan quoted
    in a refusal can be traced back to exactly what it was computed from.

    **One seal, one comparison -- D151-C21 R4.** :meth:`identity` seals the whole record,
    measured SQLite temporary binding included, and is what the persisted document carries and
    what :meth:`from_document` verifies; every field moves it. :meth:`restart_compatibility` is a
    separate, in-memory representation that answers a different question -- may a restart
    continue on this recorded plan? -- and it omits exactly the binding's attachment-instance
    observations, which legitimately differ after the same volume is detached and re-attached.
    It is never serialized and is not a contract field.
    """

    contract: str
    plan_digest: str
    merge_schedule_digest: str
    seed_catalog_bytes: int
    chunk_bytes_by_id: Mapping[str, int]
    steps: tuple[MergeStepRequirement, ...]
    requirements: MultipassStorageRequirements
    sqlite_temp_binding: SqliteTempBinding
    inputs_retained: bool
    reclaimable_bytes: int
    reclaim_authority: str | None
    transfer_authority: str | None
    external_tier_qualified: bool

    @property
    def retained_chunk_bytes(self) -> int:
        """Every completed chunk artifact, retained for the whole consolidation."""
        return sum(self.chunk_bytes_by_id.values())

    @property
    def projected_intermediate_bytes(self) -> int:
        """The level-1 intermediates' projected footprint, retained through finalization."""
        return sum(step.peak_bytes for step in self.steps if step.step != "final")

    @property
    def peak_required_free_bytes(self) -> int:
        """The largest single-step floor; every step is admitted individually against it."""
        return max((step.required_free_bytes for step in self.steps), default=0)

    def identity(self) -> str:
        """A deterministic digest over every term -- the full seal, binding included."""
        payload = json.dumps(dict(self.as_record()), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def restart_compatibility(self) -> Mapping[str, object]:
        """What a governed restart must find unchanged -- D151-C21 R4. In memory only.

        Every term of :meth:`as_record` except that the SQLite temporary binding is reduced to
        its restart-stable fields (:meth:`SqliteTempBinding.stable_record`): the temporary root's
        inode and both volumes' UUID and filesystem type. The attachment-instance observations
        -- ``temp_root_device``, ``temp_device_identifier``, ``charged_device_identifier`` -- are
        the only fields excluded. They stay sealed in the document through :meth:`identity`, and
        a merge child still compares all eight against the binding its parent measured now.

        Deliberately not a digest and not a document field: the document's one identity remains
        the full seal, and this representation exists only to be compared, in memory, against the
        plan a restarting orchestrator has just computed.
        """
        record = dict(self.as_record())
        record["sqlite_temp_binding"] = dict(self.sqlite_temp_binding.stable_record())
        return record

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering -- the sealed record, every binding field included."""
        return {
            "contract": self.contract,
            "plan_digest": self.plan_digest,
            "merge_schedule_digest": self.merge_schedule_digest,
            "seed_catalog_bytes": self.seed_catalog_bytes,
            "chunk_bytes_by_id": dict(sorted(self.chunk_bytes_by_id.items())),
            "retained_chunk_bytes": self.retained_chunk_bytes,
            "projected_intermediate_bytes": self.projected_intermediate_bytes,
            "steps": [dict(step.as_record()) for step in self.steps],
            "requirements": dict(self.requirements.as_record()),
            "sqlite_temp_binding": dict(self.sqlite_temp_binding.as_record()),
            "inputs_retained": self.inputs_retained,
            "reclaimable_bytes": self.reclaimable_bytes,
            "reclaim_authority": self.reclaim_authority,
            "transfer_authority": self.transfer_authority,
            "external_tier_qualified": self.external_tier_qualified,
        }

    def as_document(self) -> Mapping[str, object]:
        """The durable form: the record plus the identity that seals it -- C19-R4A."""
        return {**dict(self.as_record()), STORAGE_PLAN_IDENTITY_KEY: self.identity()}

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> MultipassStoragePlan:
        """Read a persisted storage plan back, or refuse -- C19-R4A.

        Three refusals, in order: a superseded or unknown contract (a ``/1`` record is never
        upgraded, defaulted or reinterpreted); a record whose fields do not rebuild; and a
        record whose sealed identity is not the identity of the fields it accompanies, which is
        what a relabelled ``/1``, an edited binding or a stale digest all look like.

        Raises:
            ChunkTieringError: the document is not exactly a sealed current storage plan.
        """
        contract = document.get("contract")
        if contract in SUPERSEDED_STORAGE_PLAN_CONTRACTS:
            message = (
                f"the storage plan records the superseded contract {contract!r}; this build reads "
                f"only {MULTIPASS_STORAGE_PLAN_CONTRACT!r}. There is no automatic upgrade and no "
                "fallback: a pre-C19 record does not bind the measured SQLite temporary "
                "placement and is refused at its governed location"
            )
            raise ChunkTieringError(message)
        if contract != MULTIPASS_STORAGE_PLAN_CONTRACT:
            message = (
                f"the storage plan records contract {contract!r}, which this build does not "
                f"write; only {MULTIPASS_STORAGE_PLAN_CONTRACT!r} is read"
            )
            raise ChunkTieringError(message)
        try:
            requirements = MultipassStorageRequirements.from_record(
                _mapping_field(document["requirements"], "requirements")
            )
            binding = SqliteTempBinding.from_record(
                _mapping_field(document["sqlite_temp_binding"], "sqlite_temp_binding")
            )
            raw_steps = document["steps"]
            if not isinstance(raw_steps, list):
                message = "a storage plan's steps must be a list"
                raise ChunkTieringError(message)
            steps = tuple(
                MergeStepRequirement.from_record(_mapping_field(item, "steps"))
                for item in raw_steps
            )
            raw_bytes = _mapping_field(document["chunk_bytes_by_id"], "chunk_bytes_by_id")
            chunk_bytes_by_id = {
                str(chunk_id): _measured_int(length, "chunk_bytes_by_id")
                for chunk_id, length in raw_bytes.items()
            }
            rebuilt = cls(
                contract=str(contract),
                plan_digest=str(document["plan_digest"]),
                merge_schedule_digest=str(document["merge_schedule_digest"]),
                seed_catalog_bytes=_measured_int(
                    document["seed_catalog_bytes"], "seed_catalog_bytes"
                ),
                chunk_bytes_by_id=chunk_bytes_by_id,
                steps=steps,
                requirements=requirements,
                sqlite_temp_binding=binding,
                inputs_retained=_bool_field(document["inputs_retained"], "inputs_retained"),
                reclaimable_bytes=_measured_int(document["reclaimable_bytes"], "reclaimable_bytes"),
                reclaim_authority=_optional_str_field(
                    document["reclaim_authority"], "reclaim_authority"
                ),
                transfer_authority=_optional_str_field(
                    document["transfer_authority"], "transfer_authority"
                ),
                external_tier_qualified=_bool_field(
                    document["external_tier_qualified"], "external_tier_qualified"
                ),
            )
        except KeyError as exc:
            message = f"the storage plan is missing {exc}; refused rather than defaulted"
            raise ChunkTieringError(message) from exc
        sealed = document.get(STORAGE_PLAN_IDENTITY_KEY)
        if not isinstance(sealed, str) or sealed != rebuilt.identity():
            message = (
                f"the storage plan's recorded identity {sealed!r} is not the identity of the "
                f"record it accompanies ({rebuilt.identity()}); a relabelled, edited or stale "
                "record is refused rather than resealed"
            )
            raise ChunkTieringError(message)
        stored = {str(key): value for key, value in document.items()}
        stored.pop(STORAGE_PLAN_IDENTITY_KEY, None)
        if _json_normal(stored) != _json_normal(dict(rebuilt.as_record())):
            message = (
                "the storage plan carries fields that are not the ones its identity seals; "
                "refused rather than read past them"
            )
            raise ChunkTieringError(message)
        return rebuilt


def _mapping_field(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = f"a storage plan's {name!r} must be a mapping"
        raise ChunkTieringError(message)
    return {str(key): item for key, item in value.items()}


def _bool_field(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        message = f"a storage plan's {name!r} must be a Boolean"
        raise ChunkTieringError(message)
    return value


def _optional_str_field(value: object, name: str) -> str | None:
    if value is not None and not isinstance(value, str):
        message = f"a storage plan's {name!r} must be a string or null"
        raise ChunkTieringError(message)
    return value


def _json_normal(record: Mapping[str, object]) -> object:
    return json.loads(json.dumps(dict(record), sort_keys=True))


def plan_multipass_storage(
    *,
    plan_digest: str,
    merge_schedule_digest: str,
    groups: Sequence[tuple[str, Sequence[str]]],
    chunk_bytes_by_id: Mapping[str, int],
    seed_catalog_bytes: int,
    requirements: MultipassStorageRequirements,
    sqlite_temp_binding: SqliteTempBinding,
) -> MultipassStoragePlan:
    """The whole consolidation's storage plan -- D151-C13 §18, §19; C19-R4.

    ``groups`` is the merge schedule's level-1 grouping as ``(group_id, chunk_ids)`` in schedule
    order; ``chunk_bytes_by_id`` is every chunk's authenticated artifact byte length. One
    requirement is projected per level-1 group over its own inputs, and one for the final step
    over the projected intermediates. Nothing is credited for reclaim, because nothing may be
    reclaimed. ``sqlite_temp_binding`` is the binding :func:`require_sqlite_temp_binding`
    MEASURED for this consolidation's root -- it is required, folded into the identity, and
    never defaulted, so the sealed plan states which temporary root and which volume the
    admission relied on.

    Raises:
        ChunkTieringError: a group names a chunk with no recorded byte length.
    """
    steps: list[MergeStepRequirement] = []
    for group_id, chunk_ids in groups:
        missing = [chunk_id for chunk_id in chunk_ids if chunk_id not in chunk_bytes_by_id]
        if missing:
            message = (
                f"storage planning for {group_id!r} has no authenticated byte length for "
                f"{missing}; a plan over an unmeasured input is a guess and is refused"
            )
            raise ChunkTieringError(message)
        steps.append(
            merge_step_requirement(
                step=group_id,
                level=MERGE_LEVEL_ONE,
                input_bytes=sum(chunk_bytes_by_id[chunk_id] for chunk_id in chunk_ids),
                seed_catalog_bytes=seed_catalog_bytes,
                peak_ratio=requirements.level_one_peak_ratio,
                requirements=requirements,
            )
        )
    steps.append(
        merge_step_requirement(
            step="final",
            level=MERGE_LEVEL_TWO,
            input_bytes=sum(step.peak_bytes for step in steps),
            seed_catalog_bytes=seed_catalog_bytes,
            peak_ratio=requirements.level_two_peak_ratio,
            requirements=requirements,
        )
    )
    return MultipassStoragePlan(
        contract=MULTIPASS_STORAGE_PLAN_CONTRACT,
        plan_digest=plan_digest,
        merge_schedule_digest=merge_schedule_digest,
        seed_catalog_bytes=seed_catalog_bytes,
        chunk_bytes_by_id=dict(chunk_bytes_by_id),
        steps=tuple(steps),
        requirements=requirements,
        sqlite_temp_binding=sqlite_temp_binding,
        inputs_retained=True,
        reclaimable_bytes=0,
        reclaim_authority=REAL_INTERNAL_RECLAIM_AUTHORITY,
        transfer_authority=REAL_CHUNK_TRANSFER_AUTHORITY,
        external_tier_qualified=external_tier_is_qualified(QUALIFIED_EXTERNAL_TIER),
    )


# --------------------------------------------------------------------------- #
# The deterministic spill seam -- addendum §5
# --------------------------------------------------------------------------- #
#: Spill completed internal chunks in canonical plan order, lowest ordinal first.
SPILL_POLICY_PLAN_ORDINAL: Final = "plan_ordinal"

#: Spill the largest completed internal artifact first; plan ordinal breaks ties.
SPILL_POLICY_LARGEST_ARTIFACT: Final = "largest_artifact"

#: Spill by region in the accepted region order, then by plan ordinal within the region.
SPILL_POLICY_REGION_THEN_ORDINAL: Final = "region_then_ordinal"

#: Spill in an explicitly sealed order the owner supplies; every eligible chunk must be named.
SPILL_POLICY_SEALED_ORDER: Final = "sealed_order"

#: Every policy this seam can evaluate. None is production; :data:`PRODUCTION_SPILL_POLICY` is
#: ``None`` and :func:`production_spill_policy` refuses.
SPILL_POLICIES: Final[tuple[str, ...]] = (
    SPILL_POLICY_PLAN_ORDINAL,
    SPILL_POLICY_LARGEST_ARTIFACT,
    SPILL_POLICY_REGION_THEN_ORDINAL,
    SPILL_POLICY_SEALED_ORDER,
)


def production_spill_policy() -> str:
    """The frozen production spill policy, or a refusal.

    Raises:
        ChunkTieringError: :data:`PRODUCTION_SPILL_POLICY` is ``None``.
    """
    policy = PRODUCTION_SPILL_POLICY
    if policy is None:
        message = (
            "no production spill policy is frozen: PRODUCTION_SPILL_POLICY is None. The seam "
            f"evaluates {list(SPILL_POLICIES)} deterministically so their consequences can be "
            "analyzed; choosing one is owner work and is never defaulted"
        )
        raise ChunkTieringError(message)
    return policy


@dataclass(frozen=True, slots=True)
class SpillProposal:
    """Which completed internal artifacts a policy would evacuate, and whether that suffices."""

    policy: str
    needed_bytes: int
    candidates: tuple[str, ...]
    released_bytes: int
    sufficient: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "policy": self.policy,
            "needed_bytes": self.needed_bytes,
            "candidates": list(self.candidates),
            "released_bytes": self.released_bytes,
            "sufficient": self.sufficient,
        }


def propose_spill(
    placements: Sequence[ChunkPlacement],
    *,
    plan: ChunkPlan,
    policy: str,
    needed_bytes: int,
    sealed_order: Sequence[str] | None = None,
) -> SpillProposal:
    """Propose, deterministically, which completed internal chunks a policy would spill.

    Every key is reproducible from durable evidence -- the sealed plan, the artifacts' byte
    lengths, an explicitly sealed order -- and none reads wall-clock time, filesystem enumeration
    order or an operator's choice. Only chunks in the accepted ``COMPLETE_INTERNAL`` placement
    state are eligible: a running chunk is mutable, and one with a verified external copy has
    nothing left to spill. A proposal is analysis: it copies nothing.

    Raises:
        ChunkTieringError: the policy is unknown, ``needed_bytes`` is negative, or the sealed
            policy was chosen without an order naming every eligible chunk exactly once.
    """
    if policy not in SPILL_POLICIES:
        message = f"spill policy {policy!r} is not one of {list(SPILL_POLICIES)}; refused"
        raise ChunkTieringError(message)
    if needed_bytes < 0:
        message = f"a spill proposal needs a non-negative byte target; got {needed_bytes}"
        raise ChunkTieringError(message)
    ordinal = {bounds.chunk_id: index for index, bounds in enumerate(plan.chunks)}
    region_rank = {region: index for index, region in enumerate(CHUNK_REGION_ORDER)}
    region_of = {bounds.chunk_id: bounds.region for bounds in plan.chunks}
    eligible = [
        placement
        for placement in placements
        if placement.state == STATE_COMPLETE_INTERNAL and placement.chunk_id in ordinal
    ]
    if policy == SPILL_POLICY_SEALED_ORDER:
        if sealed_order is None or sorted(sealed_order) != sorted(
            placement.chunk_id for placement in eligible
        ):
            message = (
                "the sealed-order spill policy needs an explicit order naming every eligible "
                "chunk exactly once; refused rather than completed from another key"
            )
            raise ChunkTieringError(message)
        position = {chunk_id: index for index, chunk_id in enumerate(sealed_order)}
        ranked = sorted(eligible, key=lambda placement: position[placement.chunk_id])
    elif policy == SPILL_POLICY_LARGEST_ARTIFACT:
        ranked = sorted(
            eligible,
            key=lambda placement: (-(placement.internal_bytes or 0), ordinal[placement.chunk_id]),
        )
    elif policy == SPILL_POLICY_REGION_THEN_ORDINAL:
        ranked = sorted(
            eligible,
            key=lambda placement: (
                region_rank[region_of[placement.chunk_id]],
                ordinal[placement.chunk_id],
            ),
        )
    else:
        ranked = sorted(eligible, key=lambda placement: ordinal[placement.chunk_id])
    selected: list[str] = []
    released = 0
    for placement in ranked:
        if released >= needed_bytes:
            break
        selected.append(placement.chunk_id)
        released += placement.internal_bytes or 0
    return SpillProposal(
        policy=policy,
        needed_bytes=needed_bytes,
        candidates=tuple(selected),
        released_bytes=released,
        sufficient=released >= needed_bytes,
    )


def require_sufficient_spill(proposal: SpillProposal) -> SpillProposal:
    """Return a proposal that releases what is needed, or STOP for the owner.

    Raises:
        ChunkTieringError: the proposal cannot release ``needed_bytes``; nothing partial is
            attempted and nothing is deleted to make the difference.
    """
    if not proposal.sufficient:
        message = (
            f"no safe spill path exists under policy {proposal.policy!r}: the eligible completed "
            f"internal chunks release {proposal.released_bytes} of the {proposal.needed_bytes} "
            "bytes needed. STOP FOR OWNER: the next merge step does not start, nothing is "
            "evacuated part-way, and nothing is deleted"
        )
        raise ChunkTieringError(message)
    return proposal


# --------------------------------------------------------------------------- #
# D151-C22: the qualification record as the tier, and tier-aware eligibility -- R2, R4
# --------------------------------------------------------------------------- #
_MIB: Final = 1 << 20


def _measured_rate(section: object, key: str) -> int:
    if not isinstance(section, Mapping):
        message = "the qualification record carries no measured throughput section; refused"
        raise ChunkTieringError(message)
    value = section.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float) or value < 0:
        message = f"the qualification record carries no measured {key}; refused"
        raise ChunkTieringError(message)
    return int(value * _MIB)


def external_tier_from_qualification(
    qualification: HostASsdQualification, *, qualified_by: str
) -> ExternalTierQualification:
    """The external tier one sealed qualification record describes -- C22-R2.

    Every field is a fact the record measured: the stable tier-compatibility identity is the
    mount identity, the physical reconnect qualification is the round-trip verification, and the
    sustained rates are the sealed fsync-complete write and post-reconnect read means. A record
    of class FAIL, or one whose physical reconnect stage did not run, describes no tier at all
    and refuses here; a COPY_ONLY record describes a copy tier and is never represented as
    reclaim-capable by anything derived from it.

    Raises:
        ChunkTieringError: the record does not admit a copy or carries no measured rates.
    """
    try:
        require_copy_capable(qualification)
    except DisclosureDriftError as exc:
        message = f"no external tier is derivable from this qualification record: {exc}"
        raise ChunkTieringError(message) from exc
    metrics = qualification.document.get("metrics")
    if not isinstance(metrics, Mapping):
        message = "the qualification record carries no metrics section; refused"
        raise ChunkTieringError(message)
    compat = qualification.stable_tier_compatibility
    return ExternalTierQualification(
        volume_identity=compat.volume_uuid,
        filesystem=compat.filesystem_type,
        physical_topology=compat.topology_class,
        mount_identity=qualification.stable_tier_compatibility_identity,
        writable_capacity_bytes=compat.volume_total_bytes,
        sustained_copy_bytes_per_second=_measured_rate(
            metrics.get("write"), "mean_write_fsync_complete_mib_per_s"
        ),
        sustained_read_bytes_per_second=_measured_rate(
            metrics.get("reconnect_readback"), "mean_mib_per_s"
        ),
        round_trip_verified=qualification.physical_reconnect_qualified,
        disconnect_semantics="safe_eject_then_physical_reconnect_reauthenticated",
        qualified_by=qualified_by,
    )


def reclaim_eligibility_with_tier(
    placement: ChunkPlacement,
    *,
    transfer_record: Mapping[str, object] | None,
    external_root: Path | None = None,
    qualification: HostASsdQualification | None,
) -> ReclaimEligibility:
    """The accepted eligibility predicate, plus the tier's own proof -- C22-R4.

    Everything :func:`reclaim_eligibility` proves, and additionally that the qualification
    record admits a reclaim -- class RECLAIM_CAPABLE with a completed physical reconnect
    qualification -- and that the bindings came from a verified ``/2`` receipt (C22E-R1). A
    COPY_ONLY or FAIL record, no record, or a legacy ``/1`` receipt makes the copy ineligible
    whatever else the bindings say. A computation; never an action.
    """
    base = reclaim_eligibility(
        placement, transfer_record=transfer_record, external_root=external_root
    )
    proofs = dict(base.proofs)
    proofs["qualification_reclaim_capable"] = (
        qualification is not None and qualification.admits_reclaim
    )
    # D151-C22E-R1: only bindings taken from a verified /2 receipt may confer eligibility here.
    # A legacy /1 receipt's bindings, or any mapping that does not name the /2 contract, refuse.
    proofs["transfer_receipt_is_verified_v2"] = (
        transfer_record is not None
        and transfer_record.get("receipt_contract") == VERIFIED_TRANSFER_RECEIPT_CONTRACT
    )
    eligible = all(proofs.values())
    return ReclaimEligibility(
        chunk_id=base.chunk_id,
        lifecycle=base.lifecycle,
        eligible=eligible,
        reclaim_authority=REAL_INTERNAL_RECLAIM_AUTHORITY,
        proofs=proofs,
        detail=(
            "RECLAIM-ELIGIBLE on a RECLAIM_CAPABLE tier and NOT reclaimed: deletion needs the "
            "reclaim authority, which is None, a durable intent, and a mechanism this module "
            "does not hold"
            if eligible
            else "not eligible: at least one proof is absent"
        ),
    )
