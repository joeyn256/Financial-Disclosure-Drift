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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.chunk_evidence import TRANSFER_RECEIPT_FILENAME
from disclosure_drift.m3.chunk_plan import CHUNK_REGION_ORDER, ChunkPlan
from disclosure_drift.m3.chunk_storage import (
    REAL_CHUNK_TRANSFER_AUTHORITY,
    REAL_INTERNAL_RECLAIM_AUTHORITY,
    STATE_COMPLETE_INTERNAL,
    STATE_INTERNAL_RECLAIM_ELIGIBLE,
    STATE_INTERNAL_RECLAIMED,
    STATE_TRANSFER_VERIFIED_EXTERNAL,
    ChunkPlacement,
    TransferReceipt,
    accepted_internal_reserve_bytes,
)

__all__ = [
    "ARTIFACT_LIFECYCLE_STATES",
    "LIFECYCLE_EXTERNAL_COPY_IN_PROGRESS",
    "LIFECYCLE_EXTERNAL_COPY_VERIFIED",
    "LIFECYCLE_INTERNAL_COMPLETE",
    "LIFECYCLE_INTERNAL_RECLAIMED",
    "LIFECYCLE_INTERNAL_RECLAIM_ELIGIBLE",
    "LIFECYCLE_TRANSITIONS",
    "MULTIPASS_LEVEL_ONE_PEAK_RATIO",
    "MULTIPASS_LEVEL_TWO_PEAK_RATIO",
    "MULTIPASS_STORAGE_PLAN_CONTRACT",
    "MULTIPASS_TRANSIENT_BYTES",
    "PRODUCTION_SPILL_POLICY",
    "QUALIFIED_EXTERNAL_TIER",
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

#: The transient allowance beside a merge world -- SQLite temporary space, the correction tables,
#: the receipt and manifest writes. **Closed**: measured on the eventual host, never assumed.
MULTIPASS_TRANSIENT_BYTES: Final[int | None] = None

#: Which deterministic spill policy production will use. **Closed** -- addendum §5. The four
#: candidate keys are exposed below so their consequences can be analyzed; none is frozen.
PRODUCTION_SPILL_POLICY: Final[str | None] = None

#: This storage plan's own contract identity, folded into every plan identity.
MULTIPASS_STORAGE_PLAN_CONTRACT: Final = "m3.3-chunked-f0-multipass-storage-plan/1"


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
# Admission -- addendum §3, §4; D151-C13 §§18-21
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class MultipassStorageRequirements:
    """The owner terms every merge admission needs. Explicit values only; none is defaulted."""

    internal_reserve_bytes: int
    level_one_peak_ratio: float
    level_two_peak_ratio: float
    transient_bytes: int

    def __post_init__(self) -> None:
        for name in ("internal_reserve_bytes", "transient_bytes"):
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
            "transient_bytes": self.transient_bytes,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> MultipassStorageRequirements:
        """Rebuild the requirements from their stored mapping.

        Raises:
            ChunkTieringError: a field is absent or is not of the recorded type.
        """
        try:
            reserve = record["internal_reserve_bytes"]
            transient = record["transient_bytes"]
            one = record["level_one_peak_ratio"]
            two = record["level_two_peak_ratio"]
        except KeyError as exc:
            message = f"storage requirements are missing {exc}; refused rather than defaulted"
            raise ChunkTieringError(message) from exc
        if not isinstance(reserve, int) or not isinstance(transient, int):
            message = "storage requirement byte counts must be integers; refused"
            raise ChunkTieringError(message)
        if not isinstance(one, int | float) or not isinstance(two, int | float):
            message = "storage requirement peak ratios must be numbers; refused"
            raise ChunkTieringError(message)
        return cls(
            internal_reserve_bytes=reserve,
            level_one_peak_ratio=float(one),
            level_two_peak_ratio=float(two),
            transient_bytes=transient,
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
    if (
        MULTIPASS_LEVEL_ONE_PEAK_RATIO is None
        or MULTIPASS_LEVEL_TWO_PEAK_RATIO is None
        or MULTIPASS_TRANSIENT_BYTES is None
    ):
        message = (
            "a real multipass consolidation is NOT ADMISSIBLE: the merge peak ratios and the "
            "transient allowance are None. They are measurements the owner freezes in a later "
            "reviewed change; a None term is a REFUSAL, never a zero, and no level-1 world is "
            "created until every term exists"
        )
        raise ChunkTieringError(message)
    return MultipassStorageRequirements(  # pragma: no cover - unreachable while the terms are None
        internal_reserve_bytes=reserve,
        level_one_peak_ratio=MULTIPASS_LEVEL_ONE_PEAK_RATIO,
        level_two_peak_ratio=MULTIPASS_LEVEL_TWO_PEAK_RATIO,
        transient_bytes=MULTIPASS_TRANSIENT_BYTES,
    )


@dataclass(frozen=True, slots=True)
class MergeStepRequirement:
    """What one merge step needs free on the internal tier before it may begin."""

    step: str
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
        """A deterministic rendering."""
        return {
            "step": self.step,
            "input_bytes": self.input_bytes,
            "seed_catalog_bytes": self.seed_catalog_bytes,
            "peak_ratio": self.peak_ratio,
            "peak_bytes": self.peak_bytes,
            "reserve_bytes": self.reserve_bytes,
            "transient_bytes": self.transient_bytes,
            "required_free_bytes": self.required_free_bytes,
        }


def merge_step_requirement(
    *,
    step: str,
    input_bytes: int,
    seed_catalog_bytes: int,
    peak_ratio: float,
    requirements: MultipassStorageRequirements,
) -> MergeStepRequirement:
    """One step's requirement: ``ceil(inputs x ratio) + seed`` peak, then reserve and transient.

    Raises:
        ChunkTieringError: a byte quantity is negative.
    """
    if input_bytes < 0 or seed_catalog_bytes < 0:
        message = (
            f"a merge step requirement needs non-negative byte quantities; got inputs="
            f"{input_bytes}, seed={seed_catalog_bytes}"
        )
        raise ChunkTieringError(message)
    peak = -(-input_bytes * peak_ratio // 1)  # ceiling, exact for integer-valued products
    return MergeStepRequirement(
        step=step,
        input_bytes=input_bytes,
        seed_catalog_bytes=seed_catalog_bytes,
        peak_ratio=peak_ratio,
        peak_bytes=int(peak) + seed_catalog_bytes,
        reserve_bytes=requirements.internal_reserve_bytes,
        transient_bytes=requirements.transient_bytes,
    )


@dataclass(frozen=True, slots=True)
class MergeAdmission:
    """One admission decision, with every input it was made from."""

    step: str
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
            f"{requirement.transient_bytes} transient. STOP: no world is created. Nothing was "
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
    """

    contract: str
    plan_digest: str
    merge_schedule_digest: str
    seed_catalog_bytes: int
    chunk_bytes_by_id: Mapping[str, int]
    steps: tuple[MergeStepRequirement, ...]
    requirements: MultipassStorageRequirements
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
        """A deterministic digest over every term."""
        payload = json.dumps(dict(self.as_record()), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
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
            "inputs_retained": self.inputs_retained,
            "reclaimable_bytes": self.reclaimable_bytes,
            "reclaim_authority": self.reclaim_authority,
            "transfer_authority": self.transfer_authority,
            "external_tier_qualified": self.external_tier_qualified,
        }


def plan_multipass_storage(
    *,
    plan_digest: str,
    merge_schedule_digest: str,
    groups: Sequence[tuple[str, Sequence[str]]],
    chunk_bytes_by_id: Mapping[str, int],
    seed_catalog_bytes: int,
    requirements: MultipassStorageRequirements,
) -> MultipassStoragePlan:
    """The whole consolidation's storage plan -- D151-C13 §18, §19.

    ``groups`` is the merge schedule's level-1 grouping as ``(group_id, chunk_ids)`` in schedule
    order; ``chunk_bytes_by_id`` is every chunk's authenticated artifact byte length. One
    requirement is projected per level-1 group over its own inputs, and one for the final step
    over the projected intermediates. Nothing is credited for reclaim, because nothing may be
    reclaimed.

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
                input_bytes=sum(chunk_bytes_by_id[chunk_id] for chunk_id in chunk_ids),
                seed_catalog_bytes=seed_catalog_bytes,
                peak_ratio=requirements.level_one_peak_ratio,
                requirements=requirements,
            )
        )
    steps.append(
        merge_step_requirement(
            step="final",
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
