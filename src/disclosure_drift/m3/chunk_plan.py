"""Deterministic chunk identity for a chunked F0 -- D151-C1 §5.

**What a chunk is.** A chunk is a half-open interval over the *canonical governed member
ordering* of exactly one frozen source artifact. It is never a wall-clock window, never a
byte range, never "whatever the worker got through", and never a filesystem enumeration. A
chunk that takes ninety minutes and a chunk that takes five hours have the same membership,
because membership is decided here, before any of them starts, from the archive's own central
directory.

**The canonical order is not archive order, and that is not an invention of this module.**
Accepted Decision 129 §7 defers every historical overflow shard until the primary traversal
has ended, so the accepted monolithic F0 absorbs members in exactly this sequence:

1. every **primary** submissions document, in archive ordinal order;
2. then every **historical shard**, in archive ordinal order.

That is the order ``CompactSourceEvidence.absorb`` is called in, so it is the order the member
manifest ordinals and the source completeness digest are folded in. Chunking over any other
order would move a governed digest, so this module derives the same permutation and binds it
into the plan identity.

**Two regions, and the boundary between them is always a chunk boundary.** The primary region
is ``[0, P)`` and the shard region is ``[P, P + S)``. No chunk straddles them, because a shard
may only be parsed once *every* primary document has declared whatever it declares -- the
accepted parent rule -- and a chunk that held both would have to resolve a parent map it cannot
yet have. The region split is what makes the accepted barrier expressible as an ordinal
property rather than as an execution convention.

**N is not frozen here.** :data:`PRODUCTION_CHUNK_MEMBERS` is ``None`` and this record does not
choose it: D151-C1 §5 and §28 reserve that to a later owner freeze. Every caller states its own
``chunk_members``, and changing it produces a **different plan identity** rather than a
re-partitioning of the same one.

**The number of chunks is capped, and the cap is architectural.** The single-pass merge reads
every chunk in one compound select, so a partition it cannot attach at once is a partition it
cannot consolidate. :data:`SINGLE_PASS_CHUNK_CAP` is **nine** -- one slot below the ten the
running SQLite library actually attaches, deliberately, as reserved headroom rather than as a
library limit. A plan needing more is refused **at construction**, before any chunk process
starts, and the cap it was sealed under is part of its digest.

**A calibration-only plan is the one deliberate exception, and it is a different contract.**
D151-C10 decouples the width a plan may *describe* from the width the single-pass consolidator
may *consume*. A plan sealed under :data:`CALIBRATION_PLAN_CONTRACT` may partition the source into
more than :data:`SINGLE_PASS_CHUNK_CAP` chunks -- at most :data:`CALIBRATION_CHUNK_CEILING` -- so
that ONE individual chunk of a smaller size can be executed and measured before any multi-pass
consolidation exists. The contract string is already folded into every plan digest, so the
distinction moves the sealed identity without adding a key to an ordinary plan's digest inputs;
an accepted ordinary plan keeps its identity byte for byte. A calibration-only plan is required
to be WIDER than the single-pass cap, so it can never sit inside the width the consolidator
accepts, and nothing here makes the consolidator able to read more than nine chunks.

**A canonical multipass plan is the third contract, and it is the only one a >9 world is built
from.** D151-C13 §4 freezes :data:`MULTIPASS_PLAN_CONTRACT`: a deterministic complete-source
partition of more than :data:`SINGLE_PASS_CHUNK_CAP` and at most :data:`MULTIPASS_CHUNK_CEILING`
chunks, consumed only through the two-level merge in :mod:`~disclosure_drift.m3.chunk_multipass`.
It is a different contract rather than a widened calibration plan for the same mechanical
reasons: the contract is inside every digest, so relabelling a sealed plan in any direction moves
its identity and is refused; the single-pass consolidator refuses it by width and by contract;
and a calibration-only plan -- whose chunks are noncanonical evidence -- can never be presented
to the multipass finalizer, because its digest says what it is. A multipass plan additionally
records the single-pass cap it was sealed under as **exactly** the cap this build enforces, so a
lowered declared capacity cannot move the fan-in the merge schedule is derived from.

**A dependency-closed calibration subset is the fourth contract, and it is calibration-only --
D151-C27R1.** :data:`CALIBRATION_SUBSET_PLAN_CONTRACT` describes a bounded real-source selection:
a proper primary prefix plus every historical shard whose accepted D129-R5 declaring parent lies
inside that prefix, derived by ONE read-only scan of the real archive
(:func:`derive_dependency_closure`). Its chunks are stated in selected coordinates while the full
canonical universe -- count, region bounds and ordering digest -- stays bound beside the selected
identities, and every one of them is inside the plan digest. The three complete-source readers
refuse it, its reader refuses them, and every artifact built from it carries the four
:data:`CALIBRATION_SUBSET_CLASSIFICATIONS` labels.

**Nothing here authorizes anything.** No world is created, no member is decompressed, no
database is opened, and no process is started. Reading a central directory is a measurement;
the dependency-resolution scan reads two fields of each primary document and writes nothing.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError

# The shard predicate is the accepted one, imported rather than restated: a second expression of
# "is this member a historical shard" is a second answer waiting to disagree with F0's. The
# name-level archive defences arrive the same way, and by REUSE rather than by restatement:
# `scan_central_directory` is the single implementation `iter_members` itself runs, so the
# population this module partitions is the population the accepted traversal reads -- member
# count ceiling, special-member refusal, canonicalization, portable collision, forward
# file-versus-descendant collision and reverse descendant-versus-file collision, all of them,
# once. The payload-level defences -- declared size, expansion ratio, cumulative expansion --
# stay where they are, in the accepted readers, during chunk execution, where the bytes are.
from disclosure_drift.m3.offline_parse import (
    OfflineParseError,
    _is_historical_shard_member,
    _primary_document_declarations,
    _resolve_shard_parent,
)
from disclosure_drift.sec.archive import (
    ArchiveDefenceError,
    iter_members,
    scan_central_directory,
)

__all__ = [
    "CALIBRATION_CHUNK_CEILING",
    "CALIBRATION_PLAN_CONTRACT",
    "CALIBRATION_SUBSET_CLASSIFICATIONS",
    "CALIBRATION_SUBSET_PLAN_CONTRACT",
    "CHUNKABLE_SOURCE_IDS",
    "CHUNK_PLAN_CONTRACT",
    "CHUNK_REGION_ORDER",
    "DEPENDENCY_CLOSURE_RULE",
    "GOVERNED_MEMBER_SUFFIX",
    "MEMBER_ORDER_CONTRACT",
    "MULTIPASS_CHUNK_CEILING",
    "MULTIPASS_CHUNK_FLOOR",
    "MULTIPASS_PLAN_CONTRACT",
    "PRODUCTION_CHUNK_MEMBERS",
    "REGION_PRIMARY",
    "REGION_SHARD",
    "RESERVED_ATTACHMENT_HEADROOM",
    "SHARD_EXCLUSION_CIK_CONFLICT",
    "SHARD_EXCLUSION_CLASSES",
    "SHARD_EXCLUSION_MULTIPLE_DECLARERS",
    "SHARD_EXCLUSION_PARENT_OUTSIDE_PREFIX",
    "SHARD_EXCLUSION_UNDECLARED",
    "SINGLE_PASS_CHUNK_CAP",
    "CalibrationSubsetPlan",
    "CalibrationSubsetTarget",
    "CanonicalMember",
    "ChunkBounds",
    "ChunkPlan",
    "ChunkPlanError",
    "DependencyClosure",
    "ShardExclusion",
    "ShardParentBinding",
    "build_calibration_chunk_plan",
    "build_calibration_subset_plan",
    "build_chunk_plan",
    "build_multipass_chunk_plan",
    "canonical_json_bytes",
    "canonical_member_sequence",
    "chunk_by_id",
    "chunks_in_region",
    "compute_member_order_digest",
    "derive_dependency_closure",
    "partition_regions",
    "production_chunk_members",
    "require_calibration_subset_plan",
    "require_chunkable_source",
    "require_plan_coverage",
    "require_sealed_plan",
    "resolve_calibration_subset_members",
    "resolve_chunk_members",
    "selected_member_ceiling",
    "selected_member_sequence",
    "selected_shard_member_order_digest",
    "verify_source_identity",
]


class ChunkPlanError(DisclosureDriftError):
    """A chunk-plan precondition failed. Never repaired, never approximated."""


#: This plan shape's own contract identity, folded into every plan digest so a chunk built by a
#: differently shaped successor refuses rather than half-reading a record it does not know.
CHUNK_PLAN_CONTRACT: Final = "m3.3-chunked-f0-plan/2"

#: The canonical member ordering's own identity. Separate from the plan contract because the two
#: can move independently: a plan may gain a field without the ordering changing, and an ordering
#: change must invalidate every plan whatever else stayed the same.
MEMBER_ORDER_CONTRACT: Final = "m3.3-chunked-f0-member-order/1"

#: The suffix filter the accepted F0 traversal applies. Restated here only so the two
#: populations are provably the same one; a test asserts the sequences are identical.
GOVERNED_MEMBER_SUFFIX: Final = ".json"

#: The primary-document region: every member the accepted traversal parses in-line.
REGION_PRIMARY: Final = "primary"

#: The historical-shard region: every member accepted Decision 129 §7 defers.
REGION_SHARD: Final = "shard"

#: Region order, which is also execution order. A shard chunk may not begin until every primary
#: chunk has reached a terminal, because the parent map is not complete before then.
CHUNK_REGION_ORDER: Final[tuple[str, str]] = (REGION_PRIMARY, REGION_SHARD)

#: The sources a chunk plan may be built over.
#:
#: Chunking is a property of a **multi-member** governed artifact. Every other accepted source is
#: a single payload that is its own single member: it is already one chunk, and partitioning it
#: has no meaning. Restricting the plan here rather than "supporting" the degenerate case keeps
#: a caller from believing a single-payload source was chunked when it could not have been.
CHUNKABLE_SOURCE_IDS: Final[frozenset[str]] = frozenset({"sec_bulk_submissions"})

#: The attachment count one **single-pass** consolidation may require of SQLite.
#:
#: **This is an architectural cap, not a library limit, and the difference matters.** The running
#: SQLite build's ``SQLITE_LIMIT_ATTACHED`` is **ten**, measured from the library rather than
#: declared, and neither ``main`` nor ``temp`` consumes one of those ten -- ten real attaches
#: succeed beside both. The single-pass merge could therefore read ten chunks. It is capped at
#: **nine** deliberately, leaving :data:`RESERVED_ATTACHMENT_HEADROOM` of exactly one slot
#: unspent, so that a later reviewed change may attach one more database -- a correction ledger,
#: a second evidence artifact, a verification handle -- without the partition size becoming the
#: thing that has to move.
#:
#: A plan requiring more than this is refused **at construction**, before any chunk process
#: starts, and the cap it was built under is folded into :attr:`ChunkPlan.plan_digest`, so a
#: sealed plan cannot later be reinterpreted as a larger one. The consolidator then re-asks the
#: running library the capability question for itself -- see
#: :func:`~disclosure_drift.m3.chunk_consolidation.require_attachable` -- because a plan built on
#: one host may be consolidated on another.
#:
#: Multi-pass sorted loading remains a **future** fallback; D151-C3 §3 does not implement it.
SINGLE_PASS_CHUNK_CAP: Final = 9

#: How many attachment slots the single-pass architecture deliberately leaves unspent.
#:
#: Not the main database and not the temporary one: measurement says neither consumes a slot.
#: One slot of genuine headroom, which is what makes the cap nine rather than ten.
RESERVED_ATTACHMENT_HEADROOM: Final = 1

#: The contract of a **calibration-only** plan -- D151-C10.
#:
#: A calibration-only plan describes a deterministic complete-source partition WIDER than the
#: single-pass cap, so that one individual chunk of it can be executed and measured before any
#: multi-pass consolidation exists. It is a different contract rather than a flag on the ordinary
#: one, for reasons that are all mechanical: the contract is already folded into every plan
#: digest, so the distinction moves the sealed identity without adding a key to an ordinary
#: plan's digest inputs -- an accepted ordinary plan keeps its identity byte for byte; a reader
#: that knows only the ordinary contract refuses this one outright rather than half-reading it;
#: and the record carries it in a field every consumer already reads. It cannot be relabelled
#: after sealing, because the digest folds it, and it is not an authorization of anything.
CALIBRATION_PLAN_CONTRACT: Final = "m3.3-chunked-f0-calibration-plan/1"

#: How many chunks a calibration-only plan may describe. **Thirty-four, exactly.**
#:
#: Not a library limit and not a performance figure: it is the narrowest ceiling that admits the
#: owner-authorized calibration point, ``chunk_members = 30000`` over the governed source --
#: ``ceil(980497 / 30000) = 33`` primary chunks and ``ceil(5337 / 30000) = 1`` shard chunk. A
#: partition needing more is refused at construction and on every read, exactly as an ordinary
#: plan is refused above nine. It says nothing about consolidation, which remains single-pass
#: over at most :data:`SINGLE_PASS_CHUNK_CAP` chunks whatever this ceiling is, and a wider
#: ceiling is a new owner instrument and a reviewed change, never a larger literal.
CALIBRATION_CHUNK_CEILING: Final = 34

#: The contract of a **canonical multipass** plan -- D151-C13 §4.
#:
#: A multipass plan describes a deterministic complete-source partition WIDER than the single-pass
#: cap, exactly as a calibration-only plan does, and differs from one in what may be built from
#: it: its chunks are canonical inputs to the two-level merge, and only that merge may create the
#: final F0 world from them. The contract string is folded into the plan digest, so an ordinary
#: plan, a calibration-only plan and a multipass plan over the same partition are three distinct
#: sealed identities and none can be relabelled into another after sealing. It authorizes
#: nothing: real chunk execution stays closed by
#: :data:`~disclosure_drift.m3.chunk_execution.REAL_CHUNKED_F0_EXECUTION_AUTHORITY`, and real
#: multipass consolidation stays closed by its own ``None`` authority in the multipass module.
MULTIPASS_PLAN_CONTRACT: Final = "m3.3-chunked-f0-multipass-plan/1"

#: The narrowest partition a multipass plan may describe: one chunk more than the single-pass cap.
#:
#: A partition the single-pass architecture admits is an ordinary plan and is built as one; a
#: multipass plan that fits in nine would be a second, slower route to the same world, and it
#: is refused at construction and on every read.
MULTIPASS_CHUNK_FLOOR: Final = SINGLE_PASS_CHUNK_CAP + 1

#: The widest partition a multipass plan may describe. **Thirty-four, exactly.**
#:
#: The owner-authorized maximum width (D151-C13 §4), and its own literal rather than an alias of
#: :data:`CALIBRATION_CHUNK_CEILING` so that the two can move independently in later reviewed
#: changes. It is what keeps the two-level merge schedule at exactly two levels: thirty-four
#: chunks in two regions group into at most five level-1 intermediates, which is below the
#: fan-in a single merge attaches. The planner is bounded rather than open-ended.
MULTIPASS_CHUNK_CEILING: Final = 34

#: The three plan contracts this build reads. Any other is refused before its digest is checked.
_PLAN_CONTRACTS: Final[frozenset[str]] = frozenset(
    {CHUNK_PLAN_CONTRACT, CALIBRATION_PLAN_CONTRACT, MULTIPASS_PLAN_CONTRACT}
)

#: The frozen production chunk size. **Closed** -- D151-C1 §5 and §28.
#:
#: C1 engineers the mechanism and measures the sizing model; it does not choose ``N``. ``None``
#: means every production path that would need one refuses, and a caller that has a real number
#: has it because an owner froze it in a later reviewed change, not because this module guessed.
PRODUCTION_CHUNK_MEMBERS: Final[int | None] = None


def production_chunk_members() -> int:
    """The frozen production chunk size, or a refusal -- D151-C1 §5.

    Raises:
        ChunkPlanError: :data:`PRODUCTION_CHUNK_MEMBERS` is ``None``, which is its C1 state.
    """
    frozen = PRODUCTION_CHUNK_MEMBERS
    if frozen is None:
        message = (
            "no production chunk size is frozen: PRODUCTION_CHUNK_MEMBERS is None and D151-C1 "
            "deliberately does not choose one. A real chunked F0 needs an owner-frozen N in a "
            "later reviewed change; it is never defaulted, inferred from a host, or read from "
            "an environment variable"
        )
        raise ChunkPlanError(message)
    return frozen


def require_chunkable_source(source_id: str) -> str:
    """Return ``source_id``, or refuse a source chunking has no meaning for.

    Raises:
        ChunkPlanError: the source is not one of :data:`CHUNKABLE_SOURCE_IDS`.
    """
    if source_id not in CHUNKABLE_SOURCE_IDS:
        message = (
            f"source {source_id!r} is not a chunkable governed source; only "
            f"{sorted(CHUNKABLE_SOURCE_IDS)} carries a member population a chunk plan can "
            "partition. A single-payload source is its own single member and is never "
            "'chunked into one' merely so a code path applies to it"
        )
        raise ChunkPlanError(message)
    return source_id


@dataclass(frozen=True, slots=True)
class CanonicalMember:
    """One governed member, at its place in both orderings.

    ``archive_ordinal`` is the position the accepted :func:`iter_members` traversal assigns --
    the value that reaches ``ArchiveMember.member_index`` and, through it, the deferred-shard
    ordering. ``canonical_position`` is the position in F0's own absorb order, which is the one
    a chunk interval is stated in and the one the member manifest records.
    """

    canonical_position: int
    archive_ordinal: int
    member_name: str
    region: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "canonical_position": self.canonical_position,
            "archive_ordinal": self.archive_ordinal,
            "member_name": self.member_name,
            "region": self.region,
        }


def canonical_member_sequence(archive_path: Path) -> tuple[CanonicalMember, ...]:
    """The governed member population of one archive, in accepted F0 absorb order.

    **Central directory only.** No member is decompressed and no payload is read, for the same
    reason :func:`~disclosure_drift.m3.offline_parse._historical_shard_member_names` reads it
    that way: building a plan must not cost what the run costs.

    **The name-level defences are the accepted ones by reuse, not by restatement** --
    :func:`~disclosure_drift.sec.archive.scan_central_directory` is the single implementation
    :func:`~disclosure_drift.sec.archive.iter_members` itself runs. That is what makes the
    populations provably identical rather than intended to be: the member-count ceiling, the
    special-member refusal, canonicalization, the portable-name collision, the **forward**
    file-versus-descendant collision and the **reverse** descendant-versus-file collision all
    admit and refuse here exactly as they do there, because they are the same statements.

    The suffix filter and the ordinal numbering are then applied over the admitted file members
    in central-directory order -- which is the order ``iter_members`` assigns
    ``ArchiveMember.member_index`` in, over the same filtered population.

    Raises:
        ArchiveDefenceError: the archive is corrupt, a member name is hostile or collides, or
            the archive holds more members than the accepted ceiling admits.
    """
    primary: list[tuple[int, str]] = []
    shard: list[tuple[int, str]] = []
    try:
        with zipfile.ZipFile(archive_path) as archive:
            admitted = scan_central_directory(archive_path, archive.infolist())
            ordinal = 0
            for canonical, _info in admitted.values():
                if not canonical.endswith(GOVERNED_MEMBER_SUFFIX):
                    continue
                if _is_historical_shard_member(canonical):
                    shard.append((ordinal, canonical))
                else:
                    primary.append((ordinal, canonical))
                ordinal += 1
    except zipfile.BadZipFile as exc:
        message = (
            f"archive {archive_path.name} is corrupt and is refused rather than read as "
            f"holding no governed members: {exc}"
        )
        raise ArchiveDefenceError(message) from exc
    members: list[CanonicalMember] = []
    for archive_ordinal, name in primary:
        members.append(
            CanonicalMember(
                canonical_position=len(members),
                archive_ordinal=archive_ordinal,
                member_name=name,
                region=REGION_PRIMARY,
            )
        )
    for archive_ordinal, name in shard:
        members.append(
            CanonicalMember(
                canonical_position=len(members),
                archive_ordinal=archive_ordinal,
                member_name=name,
                region=REGION_SHARD,
            )
        )
    return tuple(members)


def compute_member_order_digest(members: Sequence[CanonicalMember]) -> str:
    """A deterministic digest over the whole canonical ordering.

    Every member's canonical position, archive ordinal, region and exact name, in order. A
    reordered archive, a renamed member, a member added, a member removed, or a shard that has
    become a primary all move it -- which is what makes it the identity a chunk authenticates
    its own slice against.
    """
    digest = hashlib.sha256()
    digest.update(MEMBER_ORDER_CONTRACT.encode("utf-8"))
    digest.update(b"\x1e")
    for member in members:
        digest.update(
            "\x1f".join(
                (
                    str(member.canonical_position),
                    str(member.archive_ordinal),
                    member.region,
                    member.member_name,
                )
            ).encode("utf-8")
        )
        digest.update(b"\x1e")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class ChunkBounds:
    """One chunk's identity and its half-open canonical interval."""

    chunk_id: str
    region: str
    start: int
    end: int

    @property
    def member_count(self) -> int:
        """How many governed members this chunk consumes."""
        return self.end - self.start

    def contains(self, position: int) -> bool:
        """Whether one canonical position belongs to this chunk."""
        return self.start <= position < self.end

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "chunk_id": self.chunk_id,
            "region": self.region,
            "start": self.start,
            "end": self.end,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ChunkBounds:
        """Rebuild bounds from their stored mapping.

        Raises:
            ChunkPlanError: a field is absent or is not of the recorded type.
        """
        try:
            return cls(
                chunk_id=str(record["chunk_id"]),
                region=str(record["region"]),
                start=_stored_int(record["start"], "start"),
                end=_stored_int(record["end"], "end"),
            )
        except KeyError as exc:
            message = f"a chunk-bounds record is missing {exc}; it is refused rather than read"
            raise ChunkPlanError(message) from exc


def _stored_int(value: object, field: str) -> int:
    """One stored integer, refusing anything that is not one.

    ``bool`` is excluded deliberately: it is an ``int`` in Python and is never an ordinal here.

    Raises:
        ChunkPlanError: the value is not an integer this build reads as one.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        message = (
            f"chunk-plan field {field!r} holds {type(value).__name__} where an integer is "
            "required; a plan that cannot be read is refused rather than coerced"
        )
        raise ChunkPlanError(message)
    return int(value)


@dataclass(frozen=True, slots=True)
class ChunkPlan:
    """The complete durable binding a chunked F0 executes under -- D151-C1 §5.

    Everything a chunk must agree with before it may consume one byte: which contract, which
    source instance, which observation, which artifact (by digest **and** length), which
    canonical ordering, how many members that ordering holds, how they were partitioned, the
    single-pass cap it was sealed under, and every chunk's exact interval. ``plan_digest`` folds
    all of it, so a single changed bound -- or a raised cap -- produces a different plan rather
    than a compatible one.

    ``contract`` is one of exactly three -- :data:`CHUNK_PLAN_CONTRACT` for a single-pass plan,
    :data:`CALIBRATION_PLAN_CONTRACT` for a calibration-only one and :data:`MULTIPASS_PLAN_CONTRACT`
    for a canonical multipass one -- and it is inside the digest, which is what makes
    :attr:`calibration_only` and :attr:`multipass` properties of the sealed identity rather than
    labels a caller could change after the fact.
    """

    contract: str
    member_order_contract: str
    source_instance_id: str
    source_observation_id: str
    source_id: str
    source_sha256: str
    source_byte_length: int
    member_order_digest: str
    total_members: int
    primary_members: int
    shard_members: int
    chunk_members: int
    chunk_count: int
    single_pass_chunk_cap: int
    chunks: tuple[ChunkBounds, ...]
    plan_digest: str

    @property
    def calibration_only(self) -> bool:
        """Whether this plan is sealed under :data:`CALIBRATION_PLAN_CONTRACT` -- D151-C10.

        Derived from the contract the digest folds, never from a separate field a caller could
        set: a plan is calibration-only exactly when its sealed identity says so.
        """
        return self.contract == CALIBRATION_PLAN_CONTRACT

    @property
    def multipass(self) -> bool:
        """Whether this plan is sealed under :data:`MULTIPASS_PLAN_CONTRACT` -- D151-C13.

        Derived from the contract the digest folds, for the same reason :attr:`calibration_only`
        is: the sealed identity says what the plan is, and nothing else does.
        """
        return self.contract == MULTIPASS_PLAN_CONTRACT

    def as_record(self) -> Mapping[str, object]:
        """The complete plan as a plain mapping, carrying no absolute path."""
        record = dict(self._digest_inputs())
        record["plan_digest"] = self.plan_digest
        return record

    def _digest_inputs(self) -> Mapping[str, object]:
        """Everything the plan digest folds -- that is, everything except the digest itself."""
        return {
            "contract": self.contract,
            "member_order_contract": self.member_order_contract,
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_id": self.source_id,
            "source_sha256": self.source_sha256,
            "source_byte_length": self.source_byte_length,
            "member_order_digest": self.member_order_digest,
            "total_members": self.total_members,
            "primary_members": self.primary_members,
            "shard_members": self.shard_members,
            "chunk_members": self.chunk_members,
            "chunk_count": self.chunk_count,
            "single_pass_chunk_cap": self.single_pass_chunk_cap,
            "chunks": [dict(bounds.as_record()) for bounds in self.chunks],
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> ChunkPlan:
        """Rebuild a plan from its stored mapping and re-derive its digest.

        The stored digest is **recomputed and compared** rather than trusted: a record whose
        digest does not describe its own contents is a tampered or truncated plan, and a chunk
        that continued from it would be authenticating against a value nothing checked.

        Raises:
            ChunkPlanError: a field is absent, is not of the recorded type, or the stored digest
                does not match the record's own contents.
        """
        try:
            raw_chunks = record["chunks"]
            if not isinstance(raw_chunks, Sequence) or isinstance(raw_chunks, str | bytes):
                message = "a chunk plan's 'chunks' field is not a sequence and is refused"
                raise ChunkPlanError(message)
            plan = cls(
                contract=str(record["contract"]),
                member_order_contract=str(record["member_order_contract"]),
                source_instance_id=str(record["source_instance_id"]),
                source_observation_id=str(record["source_observation_id"]),
                source_id=str(record["source_id"]),
                source_sha256=str(record["source_sha256"]),
                source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
                member_order_digest=str(record["member_order_digest"]),
                total_members=_stored_int(record["total_members"], "total_members"),
                primary_members=_stored_int(record["primary_members"], "primary_members"),
                shard_members=_stored_int(record["shard_members"], "shard_members"),
                chunk_members=_stored_int(record["chunk_members"], "chunk_members"),
                chunk_count=_stored_int(record["chunk_count"], "chunk_count"),
                single_pass_chunk_cap=_stored_int(
                    record["single_pass_chunk_cap"], "single_pass_chunk_cap"
                ),
                chunks=tuple(
                    ChunkBounds.from_record(item)
                    for item in raw_chunks
                    if isinstance(item, Mapping)
                ),
                plan_digest=str(record["plan_digest"]),
            )
        except KeyError as exc:
            message = f"a chunk-plan record is missing {exc}; it is refused rather than read"
            raise ChunkPlanError(message) from exc
        if len(plan.chunks) != len(raw_chunks):
            message = "a chunk-plan record carries a chunk entry that is not a mapping; refused"
            raise ChunkPlanError(message)
        if plan.contract not in _PLAN_CONTRACTS:
            message = (
                f"a chunk plan carrying contract {plan.contract!r} is refused; this build "
                f"executes {CHUNK_PLAN_CONTRACT!r}, {CALIBRATION_PLAN_CONTRACT!r} and "
                f"{MULTIPASS_PLAN_CONTRACT!r} and never adopts another shape"
            )
            raise ChunkPlanError(message)
        return require_sealed_plan(plan)


def _plan_digest(plan: ChunkPlan) -> str:
    payload = json.dumps(
        dict(plan._digest_inputs()),  # noqa: SLF001 - the plan's own digest over its own inputs
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def require_sealed_plan(plan: ChunkPlan) -> ChunkPlan:
    """Return ``plan`` only if it is exactly its sealed self -- D151-C10.

    The digest is recomputed over the plan's own fields and compared with the one it carries,
    and every coverage rule -- the width rule its contract selects included -- is re-derived.
    :meth:`ChunkPlan.from_record` runs this over every plan read from disk; the consolidator runs
    it over the plan object it is handed, so a plan altered in memory after sealing -- a
    relabelled contract, a trimmed chunk tuple, a rewritten count, a raised cap -- is refused at
    the point of consumption rather than trusted because it was once valid. A frozen dataclass
    makes such an alteration a copy rather than a mutation; this is what makes the copy worthless.

    Raises:
        ChunkPlanError: the recorded digest does not describe the plan's own contents, or a
            coverage rule fails.
    """
    recomputed = _plan_digest(plan)
    if recomputed != plan.plan_digest:
        message = (
            "a chunk plan's recorded digest does not describe its own contents: recorded "
            f"{plan.plan_digest!r}, recomputed {recomputed!r}. A plan whose digest nothing "
            "checks is not an identity, and it is refused rather than repaired"
        )
        raise ChunkPlanError(message)
    return require_plan_coverage(plan)


def _require_positive_chunk_members(chunk_members: int) -> int:
    """Refuse a chunk size that is not a partition size, before anything is read.

    Raises:
        ChunkPlanError: ``chunk_members`` is zero or negative.
    """
    if chunk_members <= 0:
        message = (
            f"a chunk plan needs a positive chunk size; got {chunk_members}. Zero or negative "
            "would produce either no chunks or an unbounded number of empty ones, and neither "
            "is a partition of the source"
        )
        raise ChunkPlanError(message)
    return chunk_members


def partition_regions(
    *, primary_members: int, shard_members: int, chunk_members: int
) -> tuple[ChunkBounds, ...]:
    """The deterministic partition of a two-region population into chunk intervals.

    Pure arithmetic over three integers, stated once so that both plan builders share it and so
    that the partition a real source produces can be proved from its region counts alone: each
    **region** is cut into intervals of ``chunk_members`` members, the last interval of each
    region carries the remainder, the boundary between the regions is always a chunk boundary,
    and chunk identifiers number the intervals in canonical order. A region with no members
    produces no chunk. It builds no plan and reads nothing.

    Raises:
        ChunkPlanError: ``chunk_members`` is not positive.
    """
    _require_positive_chunk_members(chunk_members)
    bounds: list[ChunkBounds] = []
    for region, base, count in (
        (REGION_PRIMARY, 0, primary_members),
        (REGION_SHARD, primary_members, shard_members),
    ):
        for offset in range(0, count, chunk_members):
            bounds.append(
                ChunkBounds(
                    chunk_id=f"chunk-{len(bounds):04d}",
                    region=region,
                    start=base + offset,
                    end=base + min(offset + chunk_members, count),
                )
            )
    return tuple(bounds)


def _build_plan(
    *,
    contract: str,
    archive_path: Path,
    source_instance_id: str,
    source_observation_id: str,
    source_id: str,
    source_sha256: str,
    source_byte_length: int,
    chunk_members: int,
) -> ChunkPlan:
    """The one plan body both public builders run; ``contract`` is the only thing they choose."""
    require_chunkable_source(source_id)
    _require_positive_chunk_members(chunk_members)
    if source_byte_length < 0:
        message = f"a chunk plan needs a non-negative source byte length; got {source_byte_length}"
        raise ChunkPlanError(message)
    members = canonical_member_sequence(archive_path)
    if not members:
        message = (
            f"archive {archive_path.name} holds no governed {GOVERNED_MEMBER_SUFFIX} member; a "
            "chunk plan over an empty population is refused rather than built as zero chunks"
        )
        raise ChunkPlanError(message)
    primary_members = sum(1 for member in members if member.region == REGION_PRIMARY)
    shard_members = len(members) - primary_members
    bounds = partition_regions(
        primary_members=primary_members, shard_members=shard_members, chunk_members=chunk_members
    )
    plan = ChunkPlan(
        contract=contract,
        member_order_contract=MEMBER_ORDER_CONTRACT,
        source_instance_id=source_instance_id,
        source_observation_id=source_observation_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_byte_length=source_byte_length,
        member_order_digest=compute_member_order_digest(members),
        total_members=len(members),
        primary_members=primary_members,
        shard_members=shard_members,
        chunk_members=chunk_members,
        chunk_count=len(bounds),
        single_pass_chunk_cap=SINGLE_PASS_CHUNK_CAP,
        chunks=bounds,
        plan_digest="",
    )
    # The digest is over every field except itself, so the plan is built once with an empty
    # digest and then sealed. `replace` rather than a hand-written field list: a field added to
    # the dataclass and forgotten in a copy helper is exactly how a digest stops covering it.
    sealed = replace(plan, plan_digest=_plan_digest(plan))
    return require_plan_coverage(sealed)


def build_chunk_plan(
    *,
    archive_path: Path,
    source_instance_id: str,
    source_observation_id: str,
    source_id: str,
    source_sha256: str,
    source_byte_length: int,
    chunk_members: int,
) -> ChunkPlan:
    """Build one deterministic single-pass chunk plan over one frozen archive -- D151-C1 §5.

    The partition is stated rather than searched for (:func:`partition_regions`): each
    **region** is cut into intervals of ``chunk_members`` members, the last interval of each
    region carries the remainder, and the boundary between the regions is always a chunk
    boundary. A source with no shards produces no shard chunks; a source with no primaries
    produces no primary chunks; an empty governed population is refused, because a plan over
    nothing is not a plan.

    ``chunk_members`` is the caller's, deliberately. See :data:`PRODUCTION_CHUNK_MEMBERS`.

    **The single-pass cap is established here, before anything executes.** A partition needing
    more than :data:`SINGLE_PASS_CHUNK_CAP` chunks is refused by :func:`require_plan_coverage`
    at the end of this function -- so the refusal lands before chunk zero starts, which is the
    D151-C3 §11 requirement, and the cap is folded into the sealed digest so the plan cannot
    later be reinterpreted as a larger one. A wider partition for calibration is a different
    contract with its own builder, :func:`build_calibration_chunk_plan`; it is never this one
    with the cap relaxed.

    Raises:
        ChunkPlanError: the source is not chunkable, ``chunk_members`` is not positive, the
            archive holds no governed member, the partition needs more chunks than the
            single-pass architecture admits, or the coverage check fails.
        ArchiveDefenceError: the archive is corrupt, a member name is hostile, or the archive
            holds more members than the accepted ceiling admits.
    """
    return _build_plan(
        contract=CHUNK_PLAN_CONTRACT,
        archive_path=archive_path,
        source_instance_id=source_instance_id,
        source_observation_id=source_observation_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_byte_length=source_byte_length,
        chunk_members=chunk_members,
    )


def build_calibration_chunk_plan(
    *,
    archive_path: Path,
    source_instance_id: str,
    source_observation_id: str,
    source_id: str,
    source_sha256: str,
    source_byte_length: int,
    chunk_members: int,
) -> ChunkPlan:
    """Build one deterministic CALIBRATION-ONLY chunk plan over one frozen archive -- D151-C10.

    The same partition arithmetic, the same canonical ordering, the same source binding and the
    same digest as :func:`build_chunk_plan`, sealed under :data:`CALIBRATION_PLAN_CONTRACT`
    instead of :data:`CHUNK_PLAN_CONTRACT`. That one difference is inside the digest, so the
    result is a distinct authenticated identity that no reader can mistake for a single-pass
    plan and no caller can turn into one after the fact.

    **What it is for, and only that.** A calibration-only plan describes a partition WIDER than
    the single-pass cap -- more than :data:`SINGLE_PASS_CHUNK_CAP` and at most
    :data:`CALIBRATION_CHUNK_CEILING` chunks -- so that ONE individual chunk of a smaller size can
    be executed, in the accepted child process with every accepted binding, and measured. Its
    chunks are noncanonical evidence: no F0 terminal, no F1 admission, no final world. The
    single-pass consolidator refuses the whole plan by width before it reads anything, and this
    build implements no consolidation that could read it.

    A partition that fits the single-pass cap is refused here: it is an ordinary plan and is
    built as one. Nothing here authorizes a real run; real execution stays closed by
    :data:`~disclosure_drift.m3.chunk_execution.REAL_CHUNKED_F0_EXECUTION_AUTHORITY`.

    Raises:
        ChunkPlanError: the source is not chunkable, ``chunk_members`` is not positive, the
            archive holds no governed member, the partition fits the single-pass cap or exceeds
            the calibration ceiling, or the coverage check fails.
        ArchiveDefenceError: the archive is corrupt, a member name is hostile, or the archive
            holds more members than the accepted ceiling admits.
    """
    return _build_plan(
        contract=CALIBRATION_PLAN_CONTRACT,
        archive_path=archive_path,
        source_instance_id=source_instance_id,
        source_observation_id=source_observation_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_byte_length=source_byte_length,
        chunk_members=chunk_members,
    )


def build_multipass_chunk_plan(
    *,
    archive_path: Path,
    source_instance_id: str,
    source_observation_id: str,
    source_id: str,
    source_sha256: str,
    source_byte_length: int,
    chunk_members: int,
) -> ChunkPlan:
    """Build one deterministic CANONICAL MULTIPASS chunk plan over one frozen archive -- D151-C13.

    The same partition arithmetic, the same canonical ordering, the same source binding and the
    same digest as :func:`build_chunk_plan`, sealed under :data:`MULTIPASS_PLAN_CONTRACT`. That one
    difference is inside the digest, so the result is a distinct authenticated identity that no
    reader can mistake for a single-pass plan or for a calibration-only plan, and that no caller
    can turn into either after the fact.

    **What it is for.** A multipass plan describes a partition WIDER than the single-pass cap --
    more than :data:`SINGLE_PASS_CHUNK_CAP` and at most :data:`MULTIPASS_CHUNK_CEILING` chunks --
    whose chunks are canonical inputs to the deterministic two-level merge in
    :mod:`~disclosure_drift.m3.chunk_multipass`. Only that merge's second level may create the
    final F0 world; the single-pass consolidator refuses the plan by width and by contract. The
    single-pass cap it records is required to be exactly the cap this build enforces, because the
    merge schedule's fan-in is derived from it.

    ``chunk_members`` is the caller's, deliberately: :data:`PRODUCTION_CHUNK_MEMBERS` stays
    ``None`` and nothing here chooses a production size. Nothing here authorizes a real run.

    Raises:
        ChunkPlanError: the source is not chunkable, ``chunk_members`` is not positive, the
            archive holds no governed member, the partition fits the single-pass cap or exceeds
            the multipass ceiling, or the coverage check fails.
        ArchiveDefenceError: the archive is corrupt, a member name is hostile, or the archive
            holds more members than the accepted ceiling admits.
    """
    return _build_plan(
        contract=MULTIPASS_PLAN_CONTRACT,
        archive_path=archive_path,
        source_instance_id=source_instance_id,
        source_observation_id=source_observation_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_byte_length=source_byte_length,
        chunk_members=chunk_members,
    )


def require_plan_coverage(plan: ChunkPlan) -> ChunkPlan:
    """Return ``plan``, or refuse a partition that is not one -- D151-C1 §29 C03-C05.

    Seven properties, and every one of them refuses rather than warns:

    * the partition's width is the one its **contract** admits -- within the single-pass cap for
      an ordinary plan (D151-C3 §11); wider than that cap and at most the calibration ceiling for
      a calibration-only plan (D151-C10); wider than that cap, at most the multipass ceiling and
      sealed under exactly this build's cap for a multipass plan (D151-C13); no width at all for
      any other contract;
    * chunk identifiers are **unique**;
    * intervals are **ascending** and **contiguous** -- no gap;
    * intervals do not **overlap**;
    * the first starts at ``0`` and the last ends at ``total_members`` -- exact coverage, once;
    * no interval is **empty**;
    * no interval **straddles** the primary/shard boundary, and no shard chunk precedes a
      primary chunk.

    **The cap is checked here rather than only where the merge runs**, which is the whole point
    of D151-C3 §11: a partition this architecture cannot consolidate must be refused *before the
    first chunk process starts*, not after every chunk has been parsed. This function runs inside
    :func:`build_chunk_plan` and inside :meth:`ChunkPlan.from_record`, so a plan is refused both
    when it is built and when it is read back, and a record that declares a **larger** cap than
    this build enforces is refused as well -- the declared value is never trusted over the
    constant.

    Raises:
        ChunkPlanError: any of them fails, naming the exact chunk and the exact bounds.
    """
    if plan.single_pass_chunk_cap > SINGLE_PASS_CHUNK_CAP:
        message = (
            f"a chunk plan declares a single-pass cap of {plan.single_pass_chunk_cap} where this "
            f"build enforces {SINGLE_PASS_CHUNK_CAP}. The declared value is a record of what the "
            "plan was sealed under, never a permission to exceed what this build implements"
        )
        raise ChunkPlanError(message)
    _require_admissible_width(plan)
    if plan.primary_members + plan.shard_members != plan.total_members:
        message = (
            f"a chunk plan's region counts do not sum to its member count: "
            f"{plan.primary_members} primary + {plan.shard_members} shard != "
            f"{plan.total_members} total"
        )
        raise ChunkPlanError(message)
    if plan.chunk_count != len(plan.chunks):
        message = (
            f"a chunk plan declares {plan.chunk_count} chunks and carries {len(plan.chunks)}; "
            "the declared count is never trusted over the bounds it is supposed to describe"
        )
        raise ChunkPlanError(message)
    if not plan.chunks:
        message = "a chunk plan carries no chunk; a partition of a non-empty source is refused"
        raise ChunkPlanError(message)
    identifiers = [bounds.chunk_id for bounds in plan.chunks]
    if len(set(identifiers)) != len(identifiers):
        duplicated = sorted({name for name in identifiers if identifiers.count(name) > 1})
        message = (
            f"a chunk plan repeats chunk identifier(s) {duplicated}; a chunk id is an identity "
            "and two intervals may never share one"
        )
        raise ChunkPlanError(message)
    cursor = 0
    seen_shard = False
    for bounds in plan.chunks:
        if bounds.region not in CHUNK_REGION_ORDER:
            message = (
                f"chunk {bounds.chunk_id!r} declares region {bounds.region!r}; the regions are "
                f"{list(CHUNK_REGION_ORDER)} and no other label is executed"
            )
            raise ChunkPlanError(message)
        if bounds.end <= bounds.start:
            message = (
                f"chunk {bounds.chunk_id!r} carries the empty or inverted interval "
                f"[{bounds.start}, {bounds.end}); every chunk consumes at least one member"
            )
            raise ChunkPlanError(message)
        if bounds.start != cursor:
            problem = "a gap" if bounds.start > cursor else "an overlap"
            message = (
                f"chunk {bounds.chunk_id!r} starts at {bounds.start} where {cursor} was "
                f"required: the plan has {problem}. Exact coverage once is the whole contract, "
                "and a plan that misses or repeats a member is refused rather than adjusted"
            )
            raise ChunkPlanError(message)
        expected_region = REGION_SHARD if bounds.start >= plan.primary_members else REGION_PRIMARY
        if bounds.region != expected_region:
            message = (
                f"chunk {bounds.chunk_id!r} declares region {bounds.region!r} but its interval "
                f"[{bounds.start}, {bounds.end}) lies in {expected_region!r}"
            )
            raise ChunkPlanError(message)
        if bounds.region == REGION_PRIMARY and bounds.end > plan.primary_members:
            message = (
                f"chunk {bounds.chunk_id!r} straddles the primary/shard boundary at "
                f"{plan.primary_members}. A shard may only be parsed once every primary "
                "document has declared what it declares, so the boundary is always a chunk "
                "boundary and never an interior position"
            )
            raise ChunkPlanError(message)
        if bounds.region == REGION_SHARD:
            seen_shard = True
        elif seen_shard:
            message = (
                f"chunk {bounds.chunk_id!r} is a primary chunk following a shard chunk; the "
                "accepted parent rule requires every primary document to be read first"
            )
            raise ChunkPlanError(message)
        cursor = bounds.end
    if cursor != plan.total_members:
        message = (
            f"a chunk plan covers [0, {cursor}) of {plan.total_members} governed members; the "
            "partition must cover the source exactly once and is refused rather than extended"
        )
        raise ChunkPlanError(message)
    if isinstance(plan, CalibrationSubsetPlan):
        # D151-C27R1: the selection rules, over and above the partition rules above.
        _require_subset_coverage(plan)
    return plan


def _require_admissible_width(plan: ChunkPlan) -> None:
    """The width rule, decided by the contract the digest folds -- D151-C3 §11, D151-C10.

    An ordinary plan may not need more chunks than the single-pass cap; that rule is unchanged.
    A calibration-only plan must need MORE than that cap -- a partition the single-pass
    architecture admits is an ordinary plan and is built as one, so no calibration-only plan can
    ever sit inside the width the consolidator accepts -- and at most
    :data:`CALIBRATION_CHUNK_CEILING`. A multipass plan (D151-C13) must likewise need more than
    the single-pass cap and at most :data:`MULTIPASS_CHUNK_CEILING`, and it is additionally held
    to the **constant** rather than to its own declared cap: a multipass record whose declared
    single-pass capacity is not exactly :data:`SINGLE_PASS_CHUNK_CAP` is refused, because the
    merge schedule's fan-in is derived from that value and a lowered declaration would otherwise
    admit a ten-chunk plan under a cap of three. Any other contract is refused: a plan of unknown
    shape has no width rule, and it gets no benefit of the doubt.

    Raises:
        ChunkPlanError: the width is not the one the contract admits.
    """
    if plan.contract == CHUNK_PLAN_CONTRACT:
        if plan.chunk_count > plan.single_pass_chunk_cap:
            message = (
                f"this partition needs {plan.chunk_count} chunks and the single-pass chunked-F0 "
                f"architecture admits {plan.single_pass_chunk_cap}. The refusal is HERE, at plan "
                "construction, so that it lands before chunk zero starts rather than after every "
                "chunk has been parsed and the merge discovers it cannot read them all in one "
                "pass. The running SQLite build attaches ten databases and neither main nor temp "
                f"consumes one of them; the cap is {SINGLE_PASS_CHUNK_CAP} rather than ten "
                f"because {RESERVED_ATTACHMENT_HEADROOM} slot is deliberately left unspent. Use "
                "a larger chunk size; multi-pass sorted loading is a future fallback this build "
                "does not implement"
            )
            raise ChunkPlanError(message)
        return
    if plan.contract == CALIBRATION_PLAN_CONTRACT:
        if plan.chunk_count <= plan.single_pass_chunk_cap:
            message = (
                f"a calibration-only chunk plan needs {plan.chunk_count} chunks, which the "
                f"single-pass chunked-F0 architecture admits ({plan.single_pass_chunk_cap}). A "
                "calibration-only plan exists solely to describe a partition WIDER than the "
                "single-pass cap so that one chunk of it can be measured; a partition that fits "
                "is an ordinary plan and is built as one. This is what keeps every "
                "calibration-only plan outside the width the consolidator accepts, and it is "
                "refused rather than admitted as a narrower plan under a wider label"
            )
            raise ChunkPlanError(message)
        if plan.chunk_count > CALIBRATION_CHUNK_CEILING:
            message = (
                f"a calibration-only chunk plan needs {plan.chunk_count} chunks and D151-C10 "
                f"admits at most CALIBRATION_CHUNK_CEILING = {CALIBRATION_CHUNK_CEILING}: the "
                "narrowest ceiling that describes the owner-authorized 30,000-member calibration "
                "partition (33 primary chunks and 1 shard chunk). The planner is bounded rather "
                "than open-ended; a wider partition needs a new owner instrument and a reviewed "
                "change, never a larger literal"
            )
            raise ChunkPlanError(message)
        return
    if plan.contract == MULTIPASS_PLAN_CONTRACT:
        if plan.single_pass_chunk_cap != SINGLE_PASS_CHUNK_CAP:
            message = (
                f"a multipass chunk plan declares a single-pass cap of "
                f"{plan.single_pass_chunk_cap} where this build enforces {SINGLE_PASS_CHUNK_CAP}. "
                "The two-level merge derives its fan-in from that value, so a multipass plan is "
                "held to the constant exactly -- a lowered declaration is refused as firmly as a "
                "raised one, never admitted as a narrower plan"
            )
            raise ChunkPlanError(message)
        if plan.chunk_count < MULTIPASS_CHUNK_FLOOR:
            message = (
                f"a multipass chunk plan needs {plan.chunk_count} chunks, which the single-pass "
                f"chunked-F0 architecture admits ({SINGLE_PASS_CHUNK_CAP}). A multipass plan "
                "exists solely to describe a partition WIDER than the single-pass cap, consumed "
                "through the two-level merge; a partition that fits is an ordinary plan and is "
                "built as one. It is refused rather than admitted as a slower route to a world "
                "the single-pass consolidator already builds"
            )
            raise ChunkPlanError(message)
        if plan.chunk_count > MULTIPASS_CHUNK_CEILING:
            message = (
                f"a multipass chunk plan needs {plan.chunk_count} chunks and D151-C13 admits at "
                f"most MULTIPASS_CHUNK_CEILING = {MULTIPASS_CHUNK_CEILING}: the owner-authorized "
                "maximum width, and the width at which a two-region partition still groups into "
                "at most five level-1 intermediates. The planner is bounded rather than "
                "open-ended; a wider partition needs a new owner instrument and a reviewed "
                "change, never a larger literal"
            )
            raise ChunkPlanError(message)
        return
    if plan.contract == CALIBRATION_SUBSET_PLAN_CONTRACT:
        # D151-C27R1: a subset plan is multipass-shaped -- consumed only by the two-level
        # calibration merge -- so it is held to the multipass width rule and to this build's
        # cap exactly, and it must be the subset TYPE, not a base plan wearing the contract.
        if not isinstance(plan, CalibrationSubsetPlan):
            message = (
                f"a plan carrying {CALIBRATION_SUBSET_PLAN_CONTRACT!r} that is not a "
                "calibration-subset plan record is refused; the contract names a shape"
            )
            raise ChunkPlanError(message)
        if plan.single_pass_chunk_cap != SINGLE_PASS_CHUNK_CAP:
            message = (
                f"a calibration-subset plan declares a single-pass cap of "
                f"{plan.single_pass_chunk_cap} where this build enforces "
                f"{SINGLE_PASS_CHUNK_CAP}; the merge fan-in derives from it and it is held "
                "to the constant exactly"
            )
            raise ChunkPlanError(message)
        if not MULTIPASS_CHUNK_FLOOR <= plan.chunk_count <= CALIBRATION_CHUNK_CEILING:
            message = (
                f"a calibration-subset plan needs {plan.chunk_count} chunks; D151-C27R1 admits "
                f"more than {SINGLE_PASS_CHUNK_CAP} and at most CALIBRATION_CHUNK_CEILING = "
                f"{CALIBRATION_CHUNK_CEILING}, consumed only through the two-level calibration "
                "merge. The planner is bounded rather than open-ended"
            )
            raise ChunkPlanError(message)
        return
    message = (
        f"a chunk plan carrying contract {plan.contract!r} has no width rule in this build; "
        f"only {CHUNK_PLAN_CONTRACT!r}, {CALIBRATION_PLAN_CONTRACT!r}, "
        f"{MULTIPASS_PLAN_CONTRACT!r} and {CALIBRATION_SUBSET_PLAN_CONTRACT!r} are executed"
    )
    raise ChunkPlanError(message)


def chunk_by_id(plan: ChunkPlan, chunk_id: str) -> ChunkBounds:
    """One chunk's bounds, or a refusal.

    Raises:
        ChunkPlanError: the plan carries no chunk of that identity.
    """
    for bounds in plan.chunks:
        if bounds.chunk_id == chunk_id:
            return bounds
    message = (
        f"chunk {chunk_id!r} is not in this plan; the plan carries "
        f"{[bounds.chunk_id for bounds in plan.chunks][:8]}"
        f"{'...' if plan.chunk_count > 8 else ''}. A chunk identity is never inferred"
    )
    raise ChunkPlanError(message)


def chunks_in_region(plan: ChunkPlan, region: str) -> tuple[ChunkBounds, ...]:
    """Every chunk of one region, in canonical plan order."""
    return tuple(bounds for bounds in plan.chunks if bounds.region == region)


def verify_source_identity(
    plan: ChunkPlan, *, observed_sha256: str, observed_byte_length: int
) -> None:
    """Refuse a chunk run against an artifact that is not the one the plan was built over.

    Both are compared, and separately: a length alone admits a different file of the same size,
    and a digest alone leaves a refusal unable to say how far apart the two artifacts are.

    Raises:
        ChunkPlanError: either identity differs.
    """
    if observed_sha256 != plan.source_sha256:
        message = (
            f"the source artifact SHA-256 is {observed_sha256!r} where the chunk plan was built "
            f"over {plan.source_sha256!r}. A chunk consumes the artifact its plan names and no "
            "other; nothing is reparsed, re-planned, or adopted"
        )
        raise ChunkPlanError(message)
    if observed_byte_length != plan.source_byte_length:
        message = (
            f"the source artifact is {observed_byte_length} bytes where the chunk plan records "
            f"{plan.source_byte_length}"
        )
        raise ChunkPlanError(message)


def resolve_chunk_members(
    plan: ChunkPlan, archive_path: Path, chunk_id: str
) -> tuple[CanonicalMember, ...]:
    """The exact members one chunk consumes, re-derived and authenticated.

    The plan binds the ordering by **digest** rather than by carrying nine hundred thousand
    names: a chunk re-derives the ordering from the same central directory and proves it reached
    the same one. A single renamed, added, removed, or reordered member changes the digest and
    the chunk refuses -- before a member is decompressed and before a world exists.

    Raises:
        ChunkPlanError: the chunk is not in the plan, or the archive's ordering is not the one
            the plan was built over.
        ArchiveDefenceError: the archive is corrupt or a member name is hostile.
    """
    bounds = chunk_by_id(plan, chunk_id)
    members = canonical_member_sequence(archive_path)
    observed = compute_member_order_digest(members)
    if observed != plan.member_order_digest:
        message = (
            f"the archive's canonical member ordering digest is {observed!r} where the chunk "
            f"plan records {plan.member_order_digest!r}: the source this chunk was given is not "
            "the population the plan partitions. The chunk is refused and nothing was created"
        )
        raise ChunkPlanError(message)
    if len(members) != plan.total_members:  # pragma: no cover - the digest already fixes it
        message = (
            f"the archive holds {len(members)} governed members where the plan records "
            f"{plan.total_members}"
        )
        raise ChunkPlanError(message)
    return members[bounds.start : bounds.end]


# --------------------------------------------------------------------------- #
# The dependency-closed calibration subset -- D151-C27R1
# --------------------------------------------------------------------------- #
#: The contract of a **dependency-closed calibration-subset** plan -- D151-C27R1 §4.
#:
#: A subset plan describes a bounded, real-source selection: the first ``primary_prefix_members``
#: primary documents in canonical order, plus every historical shard whose accepted D129-R5
#: declaring parent lies inside that prefix. It is a fourth contract rather than a flag on any of
#: the three complete-source ones, for the mechanical reasons the others give: the contract is
#: inside the digest, the three complete-source readers refuse it outright, and its own reader
#: refuses them. Every artifact built from it is calibration-only and noncanonical.
CALIBRATION_SUBSET_PLAN_CONTRACT: Final = "m3.3-chunked-f0-calibration-subset-plan/1"

#: The four labels every calibration-subset artifact carries -- D151-C27R1 R6. Exact, in order.
CALIBRATION_SUBSET_CLASSIFICATIONS: Final[tuple[str, ...]] = (
    "CALIBRATION_ONLY",
    "NONCANONICAL",
    "NOT_A_PRODUCTION_INPUT",
    "NOT_A_BOUNDED_CANARY",
)

#: The dependency-closure rule a subset plan is derived under, folded into its identity.
#:
#: A shard is SELECTED when, over the COMPLETE real archive, exactly one primary document
#: declares it under ``filings.files`` (the accepted D129-R5 rule, applied verbatim through
#: :func:`~disclosure_drift.m3.offline_parse._resolve_shard_parent`: the declared parent must
#: equal the registrant the shard's own name encodes), and that declaring document's full
#: canonical position lies inside the primary prefix. Every other shard is EXCLUDED under
#: exactly one of :data:`SHARD_EXCLUSION_CLASSES`. Nothing is inferred from a filename alone, a
#: same-CIK primary alone, a caller-supplied mapping, or a plan-carried mapping.
DEPENDENCY_CLOSURE_RULE: Final = "d129-r5-declaring-parent-within-primary-prefix"

#: The declaring parent resolves but sits at or beyond the primary prefix.
SHARD_EXCLUSION_PARENT_OUTSIDE_PREFIX: Final = "parent_outside_prefix"
#: No primary document declares the shard at all; its filename binds nothing.
SHARD_EXCLUSION_UNDECLARED: Final = "undeclared"
#: More than one distinct declaring registrant, or more than one declaring document.
SHARD_EXCLUSION_MULTIPLE_DECLARERS: Final = "multiple_declarers"
#: Exactly one declaring registrant, and it contradicts the registrant the filename encodes.
SHARD_EXCLUSION_CIK_CONFLICT: Final = "cik_conflict"
#: Every exclusion class, in the order the plan records them. Exact.
SHARD_EXCLUSION_CLASSES: Final[tuple[str, ...]] = (
    SHARD_EXCLUSION_PARENT_OUTSIDE_PREFIX,
    SHARD_EXCLUSION_UNDECLARED,
    SHARD_EXCLUSION_MULTIPLE_DECLARERS,
    SHARD_EXCLUSION_CIK_CONFLICT,
)


@dataclass(frozen=True, slots=True)
class CalibrationSubsetTarget:
    """The two caller-stated numbers a subset plan is built from -- D151-C27R1 R8.

    Carried as a typed record rather than as module constants: an owner packet states the
    calibration point, the launcher hands it here, and the plan identity folds both numbers.
    Nothing in this module chooses either.
    """

    primary_prefix_members: int
    chunk_members: int

    def __post_init__(self) -> None:
        for name in ("primary_prefix_members", "chunk_members"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                message = f"a calibration-subset target's {name!r} must be a positive integer"
                raise ChunkPlanError(message)


@dataclass(frozen=True, slots=True)
class ShardParentBinding:
    """One SELECTED shard and the accepted declaration that binds it, in full coordinates."""

    shard_canonical_position: int
    shard_member_name: str
    shard_archive_ordinal: int
    parent_member_name: str
    parent_canonical_position: int
    parent_registrant_cik_padded: str

    def digest_row(self) -> str:
        """This binding's line in the shard-parent-binding digest."""
        return "\x1f".join(
            (
                "selected",
                str(self.shard_canonical_position),
                self.shard_member_name,
                str(self.shard_archive_ordinal),
                self.parent_member_name,
                str(self.parent_canonical_position),
                self.parent_registrant_cik_padded,
            )
        )


@dataclass(frozen=True, slots=True)
class ShardExclusion:
    """One EXCLUDED shard, the class it was excluded under, and the evidence for that class."""

    shard_canonical_position: int
    shard_member_name: str
    shard_archive_ordinal: int
    exclusion_class: str
    declarer_positions: tuple[int, ...]
    declared_ciks: tuple[str, ...]

    def digest_row(self) -> str:
        """This exclusion's line in the shard-parent-binding digest."""
        return "\x1f".join(
            (
                "excluded",
                str(self.shard_canonical_position),
                self.shard_member_name,
                str(self.shard_archive_ordinal),
                self.exclusion_class,
                ",".join(str(position) for position in self.declarer_positions),
                ",".join(self.declared_ciks),
            )
        )


@dataclass(frozen=True, slots=True)
class DependencyClosure:
    """Every shard of the full shard region, classified once under the closure rule.

    ``selected`` and ``excluded`` are each in canonical order, and together they cover the shard
    region exactly once, so the binding digest proves both that every eligible shard was
    included and that every ineligible shard was excluded -- D151-C27R1 §5.
    """

    rule: str
    primary_prefix_members: int
    full_primary_members: int
    full_shard_members: int
    selected: tuple[ShardParentBinding, ...]
    excluded: tuple[ShardExclusion, ...]

    def excluded_by_class(self) -> Mapping[str, int]:
        """How many shards each exclusion class holds. Every class is present, zero included."""
        counts = dict.fromkeys(SHARD_EXCLUSION_CLASSES, 0)
        for item in self.excluded:
            counts[item.exclusion_class] += 1
        return counts

    def binding_digest(self) -> str:
        """The shard-parent-binding digest over every selected AND excluded shard, in order."""
        rows = sorted(
            [(item.shard_canonical_position, item.digest_row()) for item in self.selected]
            + [(item.shard_canonical_position, item.digest_row()) for item in self.excluded]
        )
        digest = hashlib.sha256()
        for part in (
            self.rule,
            str(self.primary_prefix_members),
            str(self.full_primary_members),
            str(self.full_shard_members),
        ):
            digest.update(part.encode("utf-8"))
            digest.update(b"\x1e")
        for _position, row in rows:
            digest.update(row.encode("utf-8"))
            digest.update(b"\x1e")
        return digest.hexdigest()


def _require_proper_prefix(primary_prefix_members: int, full_primary_members: int) -> None:
    if not 0 < primary_prefix_members < full_primary_members:
        message = (
            f"a calibration subset selects a PROPER primary prefix; got {primary_prefix_members} "
            f"of {full_primary_members} primary members. A prefix that is the whole primary "
            "region is a complete-source plan and is built as one, never as a subset"
        )
        raise ChunkPlanError(message)


def derive_dependency_closure(
    archive_path: Path,
    members: Sequence[CanonicalMember],
    *,
    primary_prefix_members: int,
) -> DependencyClosure:
    """Classify every shard of the archive under the closure rule -- D151-C27R1 R1.

    **One deterministic read-only scan of the real archive**, reading only the two fields the
    accepted D129-R5 rule depends on: each primary document's own registrant and the overflow
    names it declares under ``filings.files``, extracted by the accepted
    :func:`~disclosure_drift.m3.offline_parse._primary_document_declarations` and bounded exactly
    as :func:`~disclosure_drift.m3.offline_parse._declare_shard_parents` bounds them -- a
    declaration naming a member the archive does not carry binds nothing. The verdict for every
    shard is then the accepted :func:`~disclosure_drift.m3.offline_parse._resolve_shard_parent`,
    called rather than restated. The scan covers the WHOLE archive, not the prefix: a second
    declarer beyond the prefix is what makes a shard ineligible, and only a complete scan can see
    it. No derived archive is created, no observation altered, no catalog written, no chunk
    parsed and no world created.

    ``members`` is the canonical sequence the caller already derived from the central directory;
    the traversal here is required to visit exactly that population.

    Raises:
        ChunkPlanError: the prefix is not a proper prefix of the primary region, or the traversal
            visits a population other than ``members``.
        ArchiveDefenceError: the archive is refused by the accepted archive defences.
        OfflineParseError: a member name is shard-shaped only beneath a directory prefix.
    """
    primaries = [member for member in members if member.region == REGION_PRIMARY]
    shards = [member for member in members if member.region == REGION_SHARD]
    _require_proper_prefix(primary_prefix_members, len(primaries))
    primary_by_name = {member.member_name: member for member in primaries}
    shard_names = frozenset(member.member_name for member in shards)
    declared_ciks: dict[str, set[str]] = {}
    declarers: dict[str, set[tuple[int, str, str]]] = {}
    visited = 0
    for archive_member in iter_members(archive_path, name_suffix=GOVERNED_MEMBER_SUFFIX):
        visited += 1
        name = archive_member.name
        if _is_historical_shard_member(name):
            if name not in shard_names:
                message = (
                    f"the dependency-resolution scan met shard {name!r}, which the canonical "
                    "member sequence does not carry; the two populations must be one"
                )
                raise ChunkPlanError(message)
            continue
        primary = primary_by_name.get(name)
        if primary is None:
            message = (
                f"the dependency-resolution scan met primary {name!r}, which the canonical "
                "member sequence does not carry; the two populations must be one"
            )
            raise ChunkPlanError(message)
        padded, declarations = _primary_document_declarations(archive_member.payload)
        if padded is None:
            continue
        for declaration in declarations:
            if declaration not in shard_names:
                # Bounded exactly as the accepted fold bounds it.
                continue
            declared_ciks.setdefault(declaration, set()).add(padded)
            declarers.setdefault(declaration, set()).add(
                (primary.canonical_position, primary.member_name, padded)
            )
    if visited != len(members):
        message = (
            f"the dependency-resolution scan visited {visited} governed members where the "
            f"canonical sequence holds {len(members)}; the two populations must be one"
        )
        raise ChunkPlanError(message)
    selected: list[ShardParentBinding] = []
    excluded: list[ShardExclusion] = []
    for shard in shards:
        name = shard.member_name
        parents = declared_ciks.get(name, set())
        rows = sorted(declarers.get(name, set()))
        evidence = (tuple(row[0] for row in rows), tuple(sorted(parents)))
        try:
            resolved = _resolve_shard_parent(name, declared_ciks)
        except OfflineParseError:
            if not parents:
                excluded.append(_exclusion(shard, SHARD_EXCLUSION_UNDECLARED, evidence))
            elif len(parents) > 1:
                excluded.append(_exclusion(shard, SHARD_EXCLUSION_MULTIPLE_DECLARERS, evidence))
            else:
                excluded.append(_exclusion(shard, SHARD_EXCLUSION_CIK_CONFLICT, evidence))
            continue
        if len(rows) != 1:
            excluded.append(_exclusion(shard, SHARD_EXCLUSION_MULTIPLE_DECLARERS, evidence))
            continue
        parent_position, parent_name, parent_cik = rows[0]
        if parent_cik != resolved:  # pragma: no cover - a single declarer IS the resolved one
            message = f"shard {name!r} resolved to {resolved!r} but its declarer is {parent_cik!r}"
            raise ChunkPlanError(message)
        if parent_position >= primary_prefix_members:
            excluded.append(_exclusion(shard, SHARD_EXCLUSION_PARENT_OUTSIDE_PREFIX, evidence))
            continue
        selected.append(
            ShardParentBinding(
                shard_canonical_position=shard.canonical_position,
                shard_member_name=name,
                shard_archive_ordinal=shard.archive_ordinal,
                parent_member_name=parent_name,
                parent_canonical_position=parent_position,
                parent_registrant_cik_padded=resolved,
            )
        )
    return DependencyClosure(
        rule=DEPENDENCY_CLOSURE_RULE,
        primary_prefix_members=primary_prefix_members,
        full_primary_members=len(primaries),
        full_shard_members=len(shards),
        selected=tuple(selected),
        excluded=tuple(excluded),
    )


def _exclusion(
    shard: CanonicalMember,
    exclusion_class: str,
    evidence: tuple[tuple[int, ...], tuple[str, ...]],
) -> ShardExclusion:
    """One exclusion row: the shard, the class, and the declarer positions and CIKs seen."""
    positions, ciks = evidence
    return ShardExclusion(
        shard_canonical_position=shard.canonical_position,
        shard_member_name=shard.member_name,
        shard_archive_ordinal=shard.archive_ordinal,
        exclusion_class=exclusion_class,
        declarer_positions=positions,
        declared_ciks=ciks,
    )


def selected_shard_member_order_digest(
    members: Sequence[CanonicalMember], closure: DependencyClosure
) -> str:
    """The selected shards' ordering digest, over their FULL canonical positions -- R2."""
    chosen: list[CanonicalMember] = []
    for binding in closure.selected:
        member = members[binding.shard_canonical_position]
        if member.member_name != binding.shard_member_name or member.region != REGION_SHARD:
            message = (
                f"binding for {binding.shard_member_name!r} names full position "
                f"{binding.shard_canonical_position}, which holds {member.member_name!r}"
            )
            raise ChunkPlanError(message)
        chosen.append(member)
    return compute_member_order_digest(chosen)


def selected_member_sequence(
    members: Sequence[CanonicalMember], closure: DependencyClosure
) -> tuple[CanonicalMember, ...]:
    """The complete selected sequence, in SELECTED coordinates.

    The primary prefix keeps its full positions -- a prefix is its own coordinate system -- and
    every selected shard follows it, renumbered contiguously in canonical order. Archive ordinal,
    name and region are carried unchanged, so a selected member is still exactly one real member
    of the real archive; only the position a chunk interval is stated in is the selected one.
    """
    prefix = closure.primary_prefix_members
    selected = list(members[:prefix])
    if any(member.region != REGION_PRIMARY for member in selected):
        message = "the primary prefix is not wholly primary; the canonical order is broken"
        raise ChunkPlanError(message)
    for binding in closure.selected:
        member = members[binding.shard_canonical_position]
        selected.append(
            CanonicalMember(
                canonical_position=len(selected),
                archive_ordinal=member.archive_ordinal,
                member_name=member.member_name,
                region=REGION_SHARD,
            )
        )
    return tuple(selected)


@dataclass(frozen=True, slots=True)
class CalibrationSubsetPlan(ChunkPlan):
    """A sealed dependency-closed calibration-subset plan -- D151-C27R1.

    The inherited fields keep their meanings, with one coordinate rule stated once:
    ``member_order_digest`` is the FULL canonical ordering's digest, while ``total_members``,
    ``primary_members``, ``shard_members`` and every chunk interval are stated in SELECTED
    coordinates (:func:`selected_member_sequence`). The full universe and the selection are both
    bound -- full counts, full digest, the closure rule, the selected and parent-binding digests,
    the selected counts -- and every one of them is inside ``plan_digest``. Selected identities
    supplement the full ones and never replace them (R2).
    """

    primary_prefix_members: int
    full_total_members: int
    full_primary_members: int
    full_shard_members: int
    dependency_closure_rule: str
    selected_shard_members: int
    excluded_shard_members: int
    excluded_shards_by_class: Mapping[str, int]
    selected_shard_member_order_digest: str
    shard_parent_binding_digest: str
    selected_member_order_digest: str
    selected_members: int
    classifications: tuple[str, ...]

    @property
    def calibration_subset(self) -> bool:
        """Whether this plan is sealed under :data:`CALIBRATION_SUBSET_PLAN_CONTRACT`."""
        return self.contract == CALIBRATION_SUBSET_PLAN_CONTRACT

    def _digest_inputs(self) -> Mapping[str, object]:
        """Every inherited digest input plus every subset field -- nothing is outside the seal."""
        inputs = dict(ChunkPlan._digest_inputs(self))  # noqa: SLF001 - the plan's own inputs
        inputs.update(
            {
                "primary_prefix_members": self.primary_prefix_members,
                "full_total_members": self.full_total_members,
                "full_primary_members": self.full_primary_members,
                "full_shard_members": self.full_shard_members,
                "dependency_closure_rule": self.dependency_closure_rule,
                "selected_shard_members": self.selected_shard_members,
                "excluded_shard_members": self.excluded_shard_members,
                "excluded_shards_by_class": dict(sorted(self.excluded_shards_by_class.items())),
                "selected_shard_member_order_digest": self.selected_shard_member_order_digest,
                "shard_parent_binding_digest": self.shard_parent_binding_digest,
                "selected_member_order_digest": self.selected_member_order_digest,
                "selected_members": self.selected_members,
                "classifications": list(self.classifications),
            }
        )
        return inputs

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> CalibrationSubsetPlan:
        """Rebuild a subset plan from its EXACT stored mapping and re-derive its digest.

        Exact shape: a missing key, an unexpected key, a value of another type, any of the three
        complete-source contracts, or a digest that does not describe the record refuses.

        Raises:
            ChunkPlanError: any of them.
        """
        present = {str(key) for key in record}
        if present != _CALIBRATION_SUBSET_RECORD_KEYS:
            message = (
                "a calibration-subset plan record is exact; this one is missing "
                f"{sorted(_CALIBRATION_SUBSET_RECORD_KEYS - present)} and carries unexpected "
                f"{sorted(present - _CALIBRATION_SUBSET_RECORD_KEYS)}; refused rather than read"
            )
            raise ChunkPlanError(message)
        raw_chunks = record["chunks"]
        if not isinstance(raw_chunks, Sequence) or isinstance(raw_chunks, str | bytes):
            message = "a calibration-subset plan's 'chunks' field is not a sequence; refused"
            raise ChunkPlanError(message)
        raw_labels = record["classifications"]
        if not isinstance(raw_labels, Sequence) or isinstance(raw_labels, str | bytes):
            message = "a calibration-subset plan's 'classifications' is not a sequence; refused"
            raise ChunkPlanError(message)
        raw_by_class = record["excluded_shards_by_class"]
        if not isinstance(raw_by_class, Mapping):
            message = "a calibration-subset plan's 'excluded_shards_by_class' is not a mapping"
            raise ChunkPlanError(message)
        chunks = tuple(
            ChunkBounds.from_record(item) for item in raw_chunks if isinstance(item, Mapping)
        )
        if len(chunks) != len(raw_chunks):
            message = "a calibration-subset plan carries a chunk entry that is not a mapping"
            raise ChunkPlanError(message)
        plan = cls(
            contract=str(record["contract"]),
            member_order_contract=str(record["member_order_contract"]),
            source_instance_id=str(record["source_instance_id"]),
            source_observation_id=str(record["source_observation_id"]),
            source_id=str(record["source_id"]),
            source_sha256=str(record["source_sha256"]),
            source_byte_length=_stored_int(record["source_byte_length"], "source_byte_length"),
            member_order_digest=str(record["member_order_digest"]),
            total_members=_stored_int(record["total_members"], "total_members"),
            primary_members=_stored_int(record["primary_members"], "primary_members"),
            shard_members=_stored_int(record["shard_members"], "shard_members"),
            chunk_members=_stored_int(record["chunk_members"], "chunk_members"),
            chunk_count=_stored_int(record["chunk_count"], "chunk_count"),
            single_pass_chunk_cap=_stored_int(
                record["single_pass_chunk_cap"], "single_pass_chunk_cap"
            ),
            chunks=chunks,
            plan_digest=str(record["plan_digest"]),
            primary_prefix_members=_stored_int(
                record["primary_prefix_members"], "primary_prefix_members"
            ),
            full_total_members=_stored_int(record["full_total_members"], "full_total_members"),
            full_primary_members=_stored_int(
                record["full_primary_members"], "full_primary_members"
            ),
            full_shard_members=_stored_int(record["full_shard_members"], "full_shard_members"),
            dependency_closure_rule=str(record["dependency_closure_rule"]),
            selected_shard_members=_stored_int(
                record["selected_shard_members"], "selected_shard_members"
            ),
            excluded_shard_members=_stored_int(
                record["excluded_shard_members"], "excluded_shard_members"
            ),
            excluded_shards_by_class={
                str(key): _stored_int(value, f"excluded_shards_by_class[{key}]")
                for key, value in raw_by_class.items()
            },
            selected_shard_member_order_digest=str(record["selected_shard_member_order_digest"]),
            shard_parent_binding_digest=str(record["shard_parent_binding_digest"]),
            selected_member_order_digest=str(record["selected_member_order_digest"]),
            selected_members=_stored_int(record["selected_members"], "selected_members"),
            classifications=tuple(str(item) for item in raw_labels),
        )
        return require_calibration_subset_plan(plan)


#: The exact key set of a persisted subset plan record: the inherited digest inputs, the subset
#: fields, and the digest itself.
_CALIBRATION_SUBSET_RECORD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "contract",
        "member_order_contract",
        "source_instance_id",
        "source_observation_id",
        "source_id",
        "source_sha256",
        "source_byte_length",
        "member_order_digest",
        "total_members",
        "primary_members",
        "shard_members",
        "chunk_members",
        "chunk_count",
        "single_pass_chunk_cap",
        "chunks",
        "plan_digest",
        "primary_prefix_members",
        "full_total_members",
        "full_primary_members",
        "full_shard_members",
        "dependency_closure_rule",
        "selected_shard_members",
        "excluded_shard_members",
        "excluded_shards_by_class",
        "selected_shard_member_order_digest",
        "shard_parent_binding_digest",
        "selected_member_order_digest",
        "selected_members",
        "classifications",
    }
)


def require_calibration_subset_plan(plan: ChunkPlan) -> CalibrationSubsetPlan:
    """Return ``plan`` only if it is a sealed calibration-subset plan.

    Raises:
        ChunkPlanError: the plan is not its sealed self, or is not a subset plan.
    """
    require_sealed_plan(plan)
    if not isinstance(plan, CalibrationSubsetPlan) or not plan.calibration_subset:
        message = (
            f"a plan sealed under contract {plan.contract!r} is not a calibration-subset plan; "
            f"this reader consumes only {CALIBRATION_SUBSET_PLAN_CONTRACT!r} and never adopts "
            "the ordinary, calibration-only or multipass contract"
        )
        raise ChunkPlanError(message)
    return plan


def _require_hex_digest(value: str, field: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        message = f"a calibration-subset plan's {field!r} is not a SHA-256 hex digest; refused"
        raise ChunkPlanError(message)


def _require_subset_coverage(plan: CalibrationSubsetPlan) -> None:
    """The subset-specific coverage rules, over and above the inherited partition rules."""
    _require_proper_prefix(plan.primary_prefix_members, plan.full_primary_members)
    checks: tuple[tuple[bool, str], ...] = (
        (
            plan.full_total_members == plan.full_primary_members + plan.full_shard_members,
            "the full region counts do not sum to the full member count",
        ),
        (
            plan.primary_members == plan.primary_prefix_members,
            "the selected primary count is not the primary prefix",
        ),
        (
            plan.selected_shard_members >= 1 and plan.shard_members == plan.selected_shard_members,
            "the selected shard count must be at least one and equal the shard region count",
        ),
        (
            plan.selected_shard_members + plan.excluded_shard_members == plan.full_shard_members,
            "selected and excluded shards do not sum to the full shard count",
        ),
        (
            set(plan.excluded_shards_by_class) == set(SHARD_EXCLUSION_CLASSES)
            and all(
                not isinstance(value, bool) and isinstance(value, int) and value >= 0
                for value in plan.excluded_shards_by_class.values()
            )
            and sum(plan.excluded_shards_by_class.values()) == plan.excluded_shard_members,
            "the per-class exclusion counts are not exactly the four classes summing to the "
            "excluded shard count",
        ),
        (
            plan.selected_members == plan.primary_prefix_members + plan.selected_shard_members
            and plan.total_members == plan.selected_members,
            "the selected member count is not prefix plus selected shards, or is not the total",
        ),
        (
            plan.dependency_closure_rule == DEPENDENCY_CLOSURE_RULE,
            f"the closure rule is not {DEPENDENCY_CLOSURE_RULE!r}",
        ),
        (
            plan.classifications == CALIBRATION_SUBSET_CLASSIFICATIONS,
            f"the classifications are not exactly {list(CALIBRATION_SUBSET_CLASSIFICATIONS)}",
        ),
        (
            len(chunks_in_region(plan, REGION_SHARD)) == 1,
            "a subset plan carries exactly ONE shard chunk holding the complete selected "
            "shard sequence",
        ),
    )
    for condition, problem in checks:
        if not condition:
            message = f"a calibration-subset plan is refused: {problem}"
            raise ChunkPlanError(message)
    for field in (
        "member_order_digest",
        "selected_shard_member_order_digest",
        "shard_parent_binding_digest",
        "selected_member_order_digest",
    ):
        _require_hex_digest(getattr(plan, field), field)


def selected_member_ceiling(plan: CalibrationSubsetPlan) -> int:
    """The most members a subset plan over this source could select: prefix plus every shard."""
    return plan.primary_prefix_members + plan.full_shard_members


def build_calibration_subset_plan(
    *,
    archive_path: Path,
    source_instance_id: str,
    source_observation_id: str,
    source_id: str,
    source_sha256: str,
    source_byte_length: int,
    target: CalibrationSubsetTarget,
) -> CalibrationSubsetPlan:
    """Build one dependency-closed calibration-subset plan over one frozen archive -- D151-C27R1.

    The full canonical ordering is derived from the central directory exactly as every other
    builder derives it and bound by its digest; the dependency closure is then derived by the
    one read-only scan :func:`derive_dependency_closure` makes; the selected sequence is the
    prefix plus the selected shards; the primary prefix is partitioned by the accepted
    :func:`partition_regions` arithmetic and the selected shards form exactly ONE chunk, whatever
    their number. The plan identity folds every full and selected identity. Nothing here
    authorizes anything.

    Raises:
        ChunkPlanError: the source is not chunkable, the target is not a proper prefix, no shard
            is selected, or a coverage rule fails.
        ArchiveDefenceError: the archive is corrupt or hostile.
    """
    require_chunkable_source(source_id)
    if source_byte_length < 0:
        message = f"a chunk plan needs a non-negative source byte length; got {source_byte_length}"
        raise ChunkPlanError(message)
    members = canonical_member_sequence(archive_path)
    if not members:
        message = (
            f"archive {archive_path.name} holds no governed {GOVERNED_MEMBER_SUFFIX} member; a "
            "calibration-subset plan over an empty population is refused"
        )
        raise ChunkPlanError(message)
    closure = derive_dependency_closure(
        archive_path, members, primary_prefix_members=target.primary_prefix_members
    )
    if not closure.selected:
        message = (
            f"no shard is dependency-closed by the primary prefix [0, "
            f"{target.primary_prefix_members}); a subset plan with no shard chunk is refused"
        )
        raise ChunkPlanError(message)
    selected = selected_member_sequence(members, closure)
    # The primary prefix is cut by the accepted partition arithmetic; the selected shards are
    # ONE chunk holding the complete dependency-closed sequence, whatever its length (§5).
    primary_bounds = partition_regions(
        primary_members=closure.primary_prefix_members,
        shard_members=0,
        chunk_members=target.chunk_members,
    )
    bounds = (
        *primary_bounds,
        ChunkBounds(
            chunk_id=f"chunk-{len(primary_bounds):04d}",
            region=REGION_SHARD,
            start=closure.primary_prefix_members,
            end=closure.primary_prefix_members + len(closure.selected),
        ),
    )
    plan = CalibrationSubsetPlan(
        contract=CALIBRATION_SUBSET_PLAN_CONTRACT,
        member_order_contract=MEMBER_ORDER_CONTRACT,
        source_instance_id=source_instance_id,
        source_observation_id=source_observation_id,
        source_id=source_id,
        source_sha256=source_sha256,
        source_byte_length=source_byte_length,
        member_order_digest=compute_member_order_digest(members),
        total_members=len(selected),
        primary_members=closure.primary_prefix_members,
        shard_members=len(closure.selected),
        chunk_members=target.chunk_members,
        chunk_count=len(bounds),
        single_pass_chunk_cap=SINGLE_PASS_CHUNK_CAP,
        chunks=bounds,
        plan_digest="",
        primary_prefix_members=closure.primary_prefix_members,
        full_total_members=len(members),
        full_primary_members=closure.full_primary_members,
        full_shard_members=closure.full_shard_members,
        dependency_closure_rule=closure.rule,
        selected_shard_members=len(closure.selected),
        excluded_shard_members=len(closure.excluded),
        excluded_shards_by_class=closure.excluded_by_class(),
        selected_shard_member_order_digest=selected_shard_member_order_digest(members, closure),
        shard_parent_binding_digest=closure.binding_digest(),
        selected_member_order_digest=compute_member_order_digest(selected),
        selected_members=len(selected),
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
    )
    sealed = replace(plan, plan_digest=_plan_digest(plan))
    return require_calibration_subset_plan(sealed)


def resolve_calibration_subset_members(
    plan: CalibrationSubsetPlan, archive_path: Path, chunk_id: str
) -> tuple[CanonicalMember, ...]:
    """The exact members one subset chunk consumes, rederived from the REAL source -- R3.

    In order: the full canonical universe is rederived from the central directory and held to
    the plan's full digest and full counts; the dependency closure is rederived by the same
    read-only scan the builder made and held to the plan's parent-binding digest, selected-shard
    digest and every count; the selected sequence is rebuilt and held to the selected digest and
    count; and only then is this chunk's interval sliced from it. No caller-carried member list
    is consulted at any point.

    Raises:
        ChunkPlanError: the chunk is not in the plan, or any identity differs.
    """
    bounds = chunk_by_id(plan, chunk_id)
    members = canonical_member_sequence(archive_path)
    observed = compute_member_order_digest(members)
    if observed != plan.member_order_digest:
        message = (
            f"the archive's FULL canonical member ordering digest is {observed!r} where the "
            f"calibration-subset plan records {plan.member_order_digest!r}: the source this "
            "chunk was given is not the universe the plan selects from. Refused; nothing created"
        )
        raise ChunkPlanError(message)
    counts = (
        len(members),
        sum(1 for member in members if member.region == REGION_PRIMARY),
        sum(1 for member in members if member.region == REGION_SHARD),
    )
    if counts != (plan.full_total_members, plan.full_primary_members, plan.full_shard_members):
        message = (
            f"the archive holds {counts} (total, primary, shard) governed members where the "
            f"calibration-subset plan records ({plan.full_total_members}, "
            f"{plan.full_primary_members}, {plan.full_shard_members})"
        )
        raise ChunkPlanError(message)
    closure = derive_dependency_closure(
        archive_path, members, primary_prefix_members=plan.primary_prefix_members
    )
    binding = closure.binding_digest()
    if binding != plan.shard_parent_binding_digest:
        message = (
            f"the rederived shard-parent binding digest is {binding!r} where the plan records "
            f"{plan.shard_parent_binding_digest!r}; the dependency closure is not the one the "
            "plan was sealed over. Refused; nothing created"
        )
        raise ChunkPlanError(message)
    if (len(closure.selected), len(closure.excluded)) != (
        plan.selected_shard_members,
        plan.excluded_shard_members,
    ) or closure.excluded_by_class() != dict(plan.excluded_shards_by_class):
        message = (
            f"the rederived closure selects {len(closure.selected)} and excludes "
            f"{len(closure.excluded)} shards ({closure.excluded_by_class()}) where the plan "
            f"records {plan.selected_shard_members} / {plan.excluded_shard_members} "
            f"({dict(plan.excluded_shards_by_class)})"
        )
        raise ChunkPlanError(message)
    shard_digest = selected_shard_member_order_digest(members, closure)
    if shard_digest != plan.selected_shard_member_order_digest:
        message = (
            f"the rederived selected-shard ordering digest is {shard_digest!r} where the plan "
            f"records {plan.selected_shard_member_order_digest!r}"
        )
        raise ChunkPlanError(message)
    selected = selected_member_sequence(members, closure)
    selected_digest = compute_member_order_digest(selected)
    if selected_digest != plan.selected_member_order_digest or len(selected) != plan.total_members:
        message = (
            f"the rederived selected member ordering is {selected_digest!r} over {len(selected)} "
            f"members where the plan records {plan.selected_member_order_digest!r} over "
            f"{plan.total_members}"
        )
        raise ChunkPlanError(message)
    return selected[bounds.start : bounds.end]


def canonical_json_bytes(document: Mapping[str, object]) -> bytes:
    """The one persisted rendering of a calibration-subset document -- D151-C27R1 §4.

    UTF-8, sorted keys, compact separators, no NaN or Infinity, one trailing newline. A value
    JSON cannot carry is refused rather than coerced through ``default=``.

    Raises:
        ChunkPlanError: the document holds a value JSON cannot represent.
    """
    try:
        rendered = json.dumps(
            document, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False
        )
    except (TypeError, ValueError) as exc:
        message = f"a calibration-subset document holds a value JSON cannot carry: {exc}"
        raise ChunkPlanError(message) from exc
    return rendered.encode("utf-8") + b"\n"
