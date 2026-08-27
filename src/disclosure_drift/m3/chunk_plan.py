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

**Nothing here authorizes anything.** No world is created, no member is decompressed, no
database is opened, and no process is started. Reading a central directory is a measurement.
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
from disclosure_drift.m3.offline_parse import _is_historical_shard_member
from disclosure_drift.sec.archive import (
    ArchiveDefenceError,
    scan_central_directory,
)

__all__ = [
    "CALIBRATION_CHUNK_CEILING",
    "CALIBRATION_PLAN_CONTRACT",
    "CHUNKABLE_SOURCE_IDS",
    "CHUNK_PLAN_CONTRACT",
    "CHUNK_REGION_ORDER",
    "GOVERNED_MEMBER_SUFFIX",
    "MEMBER_ORDER_CONTRACT",
    "MULTIPASS_CHUNK_CEILING",
    "MULTIPASS_CHUNK_FLOOR",
    "MULTIPASS_PLAN_CONTRACT",
    "PRODUCTION_CHUNK_MEMBERS",
    "REGION_PRIMARY",
    "REGION_SHARD",
    "RESERVED_ATTACHMENT_HEADROOM",
    "SINGLE_PASS_CHUNK_CAP",
    "CanonicalMember",
    "ChunkBounds",
    "ChunkPlan",
    "ChunkPlanError",
    "build_calibration_chunk_plan",
    "build_chunk_plan",
    "build_multipass_chunk_plan",
    "canonical_member_sequence",
    "chunk_by_id",
    "chunks_in_region",
    "compute_member_order_digest",
    "partition_regions",
    "production_chunk_members",
    "require_chunkable_source",
    "require_plan_coverage",
    "require_sealed_plan",
    "resolve_chunk_members",
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
    message = (
        f"a chunk plan carrying contract {plan.contract!r} has no width rule in this build; "
        f"only {CHUNK_PLAN_CONTRACT!r}, {CALIBRATION_PLAN_CONTRACT!r} and "
        f"{MULTIPASS_PLAN_CONTRACT!r} are executed"
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
