"""Deterministic final consolidation of validated chunks into one canonical F0 world.

**The performance claim this module has to survive.** Accepted Decision 118 measured the
monolithic F0's constraint as random-write amplification: every parsed record inserts into
B-trees keyed by SHA-256 identifiers, so each insert lands on an unpredictable page of a database
far larger than any page cache, and the cost per record grows with the database. Chunking is only
a win if consolidation does **not** repeat that shape. So every merge below is one of:

* a **key-sorted bulk load** -- rows are staged with no index at all, sorted once by the target's
  own primary key, and inserted in that order, which appends to the rightmost leaf of the B-tree
  instead of scattering across it;
* a **set-based reduction** -- one statement over the merged table, not one statement per row;
* a **bounded** correction whose size is the cross-chunk duplicate population rather than the
  record population.

Secondary indexes are **dropped before the load and rebuilt once after it**, which is the same
trick for the same reason. Nothing here walks records one at a time issuing indexed writes.

**Two run-level derivations are inherited verbatim, and that is deliberate.** The candidate
lineage edges and the accession conflict pass are accepted Decision 111 §6 whole-observation
derivations that the monolithic F0 *already* runs exactly once, at the end, over the whole
catalog. Consolidation runs the same two, once, over the merged catalog. They are not new cost
introduced by chunking; they are the same cost moved to the same position in a different process.

**Chunks are immutable inputs and are proved to stay that way.** Every chunk database is attached
with SQLite's ``immutable=1`` URI parameter, which opens it read-only and, unlike an ordinary
read-only attach, creates no write-ahead log or shared-memory sidecar beside it -- so the chunk's
artifact **set** is unchanged, not merely its main file. Every chunk's manifest is re-verified
after consolidation and the result is recorded in the final receipt.

**Exactly one thing here is genuinely hard, and it is stated rather than buried.** Under the
compact evidence contract the observation rows an accession record writes depend on whether it is
the **first witness** of that accession in the whole source -- a fact about the source that a
chunk cannot know. Consolidation reconstructs it exactly: the canonical-earliest chunk's row wins,
its omitted observations are back-filled by the accepted reconstruction, and every later chunk's
local-first witness is upgraded to a rival by the accepted
:func:`~disclosure_drift.m3.compact_evidence.materialized_fields` over the payload the chunk
already persisted. Nothing is reparsed from the archive.

**Two D151-C5 hardenings, stated where they bite.** The chunks' agreed execution contract is held
to the parser run row the chunks actually wrote (:func:`_require_parser_run_truth`): agreement
among receipts is agreement among claims, and the manifest-bound run row is the evidence. And the
compact-evidence sidecar is merged and finalized **before** the accepted blocking-terminal gate,
which is where the accepted monolithic F0 finalizes its own -- so a consolidated F0 that reaches a
blocking terminal leaves the same diagnostic sidecar beside the same diagnostic rows that a
monolithic one leaves, and still no ledger terminal, no checkpoint and no receipt.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, cast

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.canary_phases import (
    PHASE_F0,
    PHASE_RESTART_CONTRACT,
    PHASE_STATUS_COMPLETE,
    PhaseCheckpoint,
    write_phase_checkpoint,
)
from disclosure_drift.m3.canary_runtime import process_peak_resident_bytes
from disclosure_drift.m3.capacity_plan import plan_fingerprint
from disclosure_drift.m3.chunk_evidence import (
    CHUNK_RECEIPT_FILENAME,
    FINAL_WORLD_RECEIPT_CONTRACT,
    FINAL_WORLD_RECEIPT_FILENAME,
    TRANSFER_RECEIPT_FILENAME,
    ArtifactManifest,
    ChunkReceipt,
    ExecutionContract,
    build_artifact_manifest,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.chunk_evidence import CHUNK_WITNESS_FILENAME as _WITNESS_FILENAME
from disclosure_drift.m3.chunk_execution import F0_WRITTEN_TABLES, table_row_counts
from disclosure_drift.m3.chunk_plan import (
    CHUNK_PLAN_CONTRACT,
    SINGLE_PASS_CHUNK_CAP,
    ChunkPlan,
    require_chunkable_source,
    require_sealed_plan,
)
from disclosure_drift.m3.chunk_storage import (
    ChunkPlacement,
    authoritative_input,
    derive_placements,
)
from disclosure_drift.m3.compact_evidence import (
    COMPACT_EVIDENCE_SIDECAR_FILENAME,
    CompactEvidenceSidecar,
    ProjectionDigest,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.m3.offline_parse import (
    _STREAMED_PARSER_STATE,
    PlannedSourceOutcome,
    SingleSourceOutcome,
    classify_planned_source,
    planned_source_observation,
    select_planned_source,
    write_containment,
)
from disclosure_drift.m3.repository_identity import (
    RepositoryIdentity,
    require_clean_running_repository,
)

# The accepted D140-R12 blocking-terminal gate, and the accepted phase execution identity --
# imported rather than restated. A consolidated F0 reaches the SAME disposition boundary the
# accepted monolithic F0 reaches, decided by the SAME predicate, so there is no weaker parallel
# success rule for a chunked run to pass while a monolithic one would have stopped.
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
from disclosure_drift.sec.census import (
    STREAMED_STRUCTURAL_DETAIL_LIMIT,
    CensusCatalog,
    _stable_id,
)
from disclosure_drift.sec.census import _json as _stable_json
from disclosure_drift.sec.parsers.base import PARSER_LAYER_VERSION
from disclosure_drift.storage.catalog import strictly_read_only_connection
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = [
    "ACCEPTED_F0_PAYLOAD_KEYS",
    "CONSOLIDATION_CONTRACT",
    "attachment_limit",
    "ChunkConsolidationError",
    "ConsolidationResult",
    "FinalWorldReceipt",
    "consolidate_chunks",
    "derived_f0_outcome",
    "derived_f0_payload",
    "require_attachable",
    "require_single_pass_plan",
    "resolve_chunk_inputs",
    "world_logical_digest",
]


class ChunkConsolidationError(DisclosureDriftError):
    """A consolidation precondition failed. Never repaired, never partially applied."""


#: This consolidator's own contract identity.
CONSOLIDATION_CONTRACT: Final = "m3.3-chunked-f0-consolidation/1"

_ACCESSION_PREFIX: Final = "accession:"
_DIRECTORY_MODE: Final = 0o700

#: The load order. It is FOREIGN-KEY order, not alphabetical: the final world is opened with
#: ``PRAGMA foreign_keys = ON`` exactly as every other catalog connection is, so a child row
#: loaded before its parent would refuse -- which is the correct behaviour and the reason the
#: order is stated once, here, rather than implied by a dictionary's iteration.
_LOAD_ORDER: Final[tuple[str, ...]] = (
    "census_parsed_records",
    "census_quarantined_records",
    "census_structural_observations",
    "census_registrants",
    "census_registrant_observations",
    "census_accessions",
    "census_accession_observations",
    "census_historical_references",
    "census_malformed_historical_references",
)

#: How each table's rows are combined, and the key the sorted load orders by.
#:
#: ``append`` is a plain ``INSERT``: the identifiers are content digests over member-local
#: inputs, chunk member sets are disjoint, so a collision is impossible and is therefore a
#: refusal rather than something to ignore -- exactly as the monolithic path's plain ``INSERT``
#: would refuse it. ``or_ignore`` mirrors the accepted ``INSERT OR IGNORE``: first writer wins,
#: and canonical plan order makes "first" the same row the monolithic traversal would have
#: written first. ``keyed_first_last`` is the accepted upsert reduced over chunks.
_MERGE_STRATEGY: Final[Mapping[str, str]] = {
    "census_parsed_records": "append",
    "census_quarantined_records": "append",
    "census_structural_observations": "or_ignore",
    "census_registrants": "keyed_first_last",
    "census_registrant_observations": "or_ignore",
    "census_accessions": "keyed_first_last",
    "census_accession_observations": "or_ignore",
    "census_historical_references": "or_ignore",
    "census_malformed_historical_references": "or_ignore",
}

#: Each table's identity columns -- the sort key of its bulk load and the grouping key of its
#: reduction. Taken from the migrations' own PRIMARY KEY / UNIQUE declarations.
_MERGE_KEY: Final[Mapping[str, tuple[str, ...]]] = {
    "census_parsed_records": ("parsed_record_id",),
    "census_quarantined_records": ("quarantine_record_id",),
    "census_structural_observations": ("structural_observation_id",),
    "census_registrants": ("cik_numeric",),
    "census_registrant_observations": ("registrant_observation_id",),
    "census_accessions": ("accession_plain",),
    "census_accession_observations": ("accession_observation_id",),
    "census_historical_references": (
        "source_observation_id",
        "registrant_cik_padded",
        "historical_file",
    ),
    "census_malformed_historical_references": ("malformed_reference_id",),
}


@dataclass(frozen=True, slots=True)
class ChunkInput:
    """One validated chunk, resolved to exactly one authoritative physical copy."""

    chunk_id: str
    ordinal: int
    region: str
    start: int
    end: int
    directory: Path
    tier: str
    receipt: ChunkReceipt

    @property
    def catalog_path(self) -> Path:
        """This chunk's working catalog."""
        return self.directory / WORKING_CATALOG_FILENAME

    @property
    def sidecar_path(self) -> Path:
        """This chunk's compact-evidence sidecar."""
        return self.directory / COMPACT_EVIDENCE_SIDECAR_FILENAME

    @property
    def witness_path(self) -> Path:
        """This chunk's first-witness ledger."""
        return self.directory / _WITNESS_FILENAME

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "chunk_id": self.chunk_id,
            "ordinal": self.ordinal,
            "region": self.region,
            "start": self.start,
            "end": self.end,
            "tier": self.tier,
            "manifest_digest": self.receipt.manifest.digest,
            "execution_identity": self.receipt.execution_identity,
        }


def resolve_chunk_inputs(
    plan: ChunkPlan,
    *,
    internal_root: Path,
    external_root: Path | None = None,
    placements: Sequence[ChunkPlacement] | None = None,
) -> tuple[ChunkInput, ...]:
    """Resolve every chunk of one plan to exactly one verified authoritative copy.

    **Every chunk must belong to ONE coherent execution, and that is proved rather than
    assumed** -- D151-C1 §15, corrected by D151-C3 §8. Twelve refusals, each dispositive:

    * a **missing** chunk -- never treated as empty, never reconstructed, never skipped;
    * a chunk carrying **two** valid terminal receipts (ambiguous authority);
    * a chunk whose two tier copies **disagree** on any identity;
    * a chunk built under a **different plan digest**;
    * a chunk built over a **different canonical member ordering**;
    * a chunk built over a **different source artifact**;
    * a chunk naming a **different planned source instance** than the plan;
    * a chunk naming a **different source observation** than the plan;
    * a chunk whose recorded interval is not the interval the plan assigns it (a shifted bound);
    * a chunk whose **normalized execution contract** differs from its predecessors' -- parser,
      parser version, evidence contract, durability granularity, repository revision, seed
      catalog digest or migration head;
    * a **foreign** chunk directory the plan does not name;
    * chunks whose intervals, taken together, leave a **gap**, **overlap**, or miss the source.

    **Why the instance and observation checks are here and not implied.** A receipt is excluded
    from its own artifact manifest -- it must be, since it does not exist when the manifest is
    taken -- so editing ``source_instance_id`` or ``source_observation_id`` inside it leaves every
    artifact byte-identical and every manifest verification green. Only a comparison against the
    plan catches it, so a comparison against the plan is made.

    Raises:
        ChunkConsolidationError: any of them.
        ChunkStorageError: a placement refuses.
        ChunkEvidenceError: a receipt or manifest refuses.
    """
    resolved = (
        derive_placements(plan, internal_root=internal_root, external_root=external_root)
        if placements is None
        else tuple(placements)
    )
    _refuse_foreign_chunk_directories(plan, internal_root, external_root)
    inputs: list[ChunkInput] = []
    head: str | None = None
    tree: str | None = None
    contract: ExecutionContract | None = None
    cursor = 0
    for ordinal, (bounds, placement) in enumerate(zip(plan.chunks, resolved, strict=True)):
        directory, tier = authoritative_input(placement)
        receipt = placement.internal_receipt or placement.external_receipt
        if receipt is None:  # pragma: no cover - authoritative_input already refused
            message = f"chunk {bounds.chunk_id!r} resolved to a directory with no receipt"
            raise ChunkConsolidationError(message)
        _require(
            receipt.plan_digest == plan.plan_digest,
            f"chunk {bounds.chunk_id!r} was produced under plan digest "
            f"{receipt.plan_digest!r}, not {plan.plan_digest!r}. A chunk of another partition is "
            "never admitted: its interval means something different",
        )
        _require(
            receipt.member_order_digest == plan.member_order_digest,
            f"chunk {bounds.chunk_id!r} was produced over canonical member ordering "
            f"{receipt.member_order_digest!r}, not {plan.member_order_digest!r}",
        )
        _require(
            receipt.source_sha256 == plan.source_sha256
            and receipt.source_byte_length == plan.source_byte_length,
            f"chunk {bounds.chunk_id!r} was produced over a different source artifact than the "
            "plan names",
        )
        _require(
            receipt.source_instance_id == plan.source_instance_id,
            f"chunk {bounds.chunk_id!r} names planned source instance "
            f"{receipt.source_instance_id!r} where the plan partitions "
            f"{plan.source_instance_id!r}. A chunk receipt is excluded from its own artifact "
            "manifest, so this field can be edited without moving one byte of the chunk's data "
            "-- which is exactly why it is compared against the plan rather than trusted",
        )
        _require(
            receipt.source_observation_id == plan.source_observation_id,
            f"chunk {bounds.chunk_id!r} names source observation "
            f"{receipt.source_observation_id!r} where the plan records "
            f"{plan.source_observation_id!r}",
        )
        _require(
            (receipt.region, receipt.start, receipt.end)
            == (bounds.region, bounds.start, bounds.end),
            f"chunk {bounds.chunk_id!r} records interval {receipt.region}"
            f"[{receipt.start}, {receipt.end}) where the plan assigns {bounds.region}"
            f"[{bounds.start}, {bounds.end}). A shifted bound is refused rather than trusted "
            "over the plan or used to re-derive one",
        )
        _require(
            receipt.start == cursor,
            f"chunk {bounds.chunk_id!r} starts at {receipt.start} where {cursor} was required: "
            "the admitted chunks leave a gap or overlap. Exact coverage once is the contract",
        )
        if head is None:
            head, tree = receipt.repository_head_sha, receipt.repository_tree_sha
        _require(
            receipt.repository_head_sha == head and receipt.repository_tree_sha == tree,
            f"chunk {bounds.chunk_id!r} executed under repository {receipt.repository_head_sha}/"
            f"{receipt.repository_tree_sha} where an earlier chunk executed under {head}/{tree}. "
            "One consolidated world is never assembled from chunks produced by governing code "
            "that moved between them",
        )
        if contract is None:
            contract = receipt.execution_contract
        divergence = contract.disagreements(receipt.execution_contract)
        _require(
            not divergence,
            f"chunk {bounds.chunk_id!r} ran under a different execution contract than an earlier "
            "chunk of the same plan: "
            + "; ".join(
                f"{field} {expected!r} != {observed!r}" for field, expected, observed in divergence
            )
            + ". Two chunks that did not execute equivalently are not two parts of one execution, "
            "and a world assembled from them would be one no single run could have produced",
        )
        # The dispositive verification, at the point of consumption rather than only at
        # discovery: the bytes about to be read are the bytes the receipt bound.
        verify_artifact_manifest(
            directory,
            receipt.manifest,
            exclude=(CHUNK_RECEIPT_FILENAME, TRANSFER_RECEIPT_FILENAME),
        )
        inputs.append(
            ChunkInput(
                chunk_id=bounds.chunk_id,
                ordinal=ordinal,
                region=bounds.region,
                start=bounds.start,
                end=bounds.end,
                directory=directory,
                tier=tier,
                receipt=receipt,
            )
        )
        cursor = receipt.end
    # Defence in depth, and stated as such: the per-chunk comparison above already requires each
    # receipt's interval to be exactly the plan's, and the plan itself has passed the coverage
    # check, so this cannot fail while both of those hold. It is retained because it states the
    # invariant the loop is maintaining, and because a future change to either of the checks
    # above should have to walk past it.
    _require(
        cursor == plan.total_members,
        f"the admitted chunks cover [0, {cursor}) of {plan.total_members} governed members",
    )
    return tuple(inputs)


def _refuse_foreign_chunk_directories(
    plan: ChunkPlan, internal_root: Path, external_root: Path | None
) -> None:
    """Refuse a chunk directory the plan does not name -- D151-C1 §30 A26.

    An extra chunk is not harmless clutter: it is a chunk of *some* partition, sitting where this
    partition's chunks live, and a consolidator that ignored it would be silently choosing which
    of two answers to build. The condition is reported rather than filtered.
    """
    known = {bounds.chunk_id for bounds in plan.chunks}
    for root in (internal_root, external_root):
        if root is None or not root.is_dir():
            continue
        foreign = sorted(
            path.name
            for path in root.iterdir()
            if path.is_dir() and not path.is_symlink() and path.name not in known
        )
        if foreign:
            message = (
                f"{len(foreign)} chunk directory/directories are present that this plan does not "
                f"name: {foreign[:8]}. An extra chunk belongs to some other partition, and a "
                "consolidator that ignored it would be choosing between two answers silently. "
                "Nothing was read, merged, or deleted"
            )
            raise ChunkConsolidationError(message)


def _nearest_existing(path: Path) -> Path:
    """The closest ancestor of ``path`` that exists -- what a free-space reading can be taken of.

    A volume's free space is a property of the volume, so any existing ancestor answers the same
    question. Walking up rather than assuming the parent exists means a caller that names a world
    two directories deep gets a real measurement instead of a ``FileNotFoundError``.
    """
    for candidate in (path, *path.parents):
        if candidate.exists():
            return candidate
    return Path(path.anchor or ".")  # pragma: no cover - the filesystem root always exists


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ChunkConsolidationError(message)


def _require_consolidation_identity(
    *,
    inputs: Sequence[ChunkInput],
    repository: RepositoryIdentity,
    contract: ExecutionContract,
    operational_catalog: Path,
) -> None:
    """Prove the world about to be built is the one the chunks were built for -- D151-C3 §8 B, D.

    :func:`resolve_chunk_inputs` has already proved the chunks agree **with each other**. This
    asks the different question: does the environment doing the consolidating agree with them?

    **Repository identity is a measurement, not a claim.** ``repository`` came from
    :func:`~disclosure_drift.m3.repository_identity.require_clean_running_repository`, which asks
    Git about the checkout this module's own source was imported from. The chunks' recorded
    identity is compared against that, so a consolidation run from a checkout that has **moved
    since the chunks ran** refuses -- which a comparison among the chunks alone could never
    catch, because they would still agree with one another perfectly.

    **The seed catalog is identified cryptographically, never by path.** Two files at the same
    path are not the same file, and the accepted operational catalog is the seed every chunk's
    working copy descends from. Its digest is read here and compared with the digest every chunk
    recorded; a byte that moved refuses, whatever the path says.

    Raises:
        ChunkConsolidationError: the checkout moved, or the seed catalog is a different artifact.
    """
    recorded_head = inputs[0].receipt.repository_head_sha
    recorded_tree = inputs[0].receipt.repository_tree_sha
    _require(
        repository.head_sha == recorded_head and repository.tree_sha == recorded_tree,
        f"the chunks executed under repository {recorded_head}/{recorded_tree} and this "
        f"consolidation is running from {repository.head_sha}/{repository.tree_sha}. The "
        "identity compared here is MEASURED from the checkout this code was imported from, not "
        "taken from the receipts, so a checkout that moved after the chunks ran is caught even "
        "though every chunk still agrees with every other. Nothing was merged and nothing was "
        "checked out, reset or repaired",
    )
    observed_catalog, _ = file_digest(operational_catalog)
    _require(
        observed_catalog == contract.catalog_source_sha256,
        f"the accepted catalog this consolidation would seed the final world from digests to "
        f"{observed_catalog!r} and every chunk executed against {contract.catalog_source_sha256!r}"
        ". The seed is identified by its BYTES, never by its path: two artifacts at one path are "
        "not one artifact, and a world seeded from a catalog the chunks never saw is not the "
        "world their rows belong to",
    )


# --------------------------------------------------------------------------- #
# Attaching the chunks
# --------------------------------------------------------------------------- #
def _columns(connection: sqlite3.Connection, table: str, *, schema: str = "main") -> list[str]:
    return [
        str(row["name"])
        for row in connection.execute(f"PRAGMA {schema}.table_info({table})")  # noqa: S608
    ]


def attachment_limit() -> int:
    """How many databases this SQLite build will attach to one connection at once.

    ``SQLITE_MAX_ATTACHED`` is a **compile-time** ceiling -- ``sqlite3_limit`` can lower it and
    can never raise it -- so this is **measured from the running library** rather than declared.
    The library Python links here reports ten, and ten real attaches succeed: neither ``main``
    nor ``temp`` consumes one of them.

    This is asked again at consolidation time, on the host that is actually merging, because a
    plan built on one host may be consolidated on another and a compile-time ceiling is a
    property of a build rather than of a plan.
    """
    connection = sqlite3.connect(":memory:")
    try:
        return int(connection.getlimit(sqlite3.SQLITE_LIMIT_ATTACHED))
    finally:
        connection.close()


def require_attachable(chunk_count: int, *, limit: int | None = None) -> int:
    """Refuse a partition this merge cannot read in one pass -- D151-C3 §§3, 11.

    **Two independent questions, and neither substitutes for the other.**

    The first is a **capability** question asked of the running library: will this SQLite build
    attach as many databases as this plan needs? The merge reads every chunk in one compound
    select, so a build whose ``SQLITE_LIMIT_ATTACHED`` is below the chunk count cannot execute
    the plan at all -- whatever the plan was sealed under, and whatever a different host would
    have allowed.

    The second is an **architectural** question, and it is the one
    :data:`~disclosure_drift.m3.chunk_plan.SINGLE_PASS_CHUNK_CAP` answers: this build issues a
    single-pass merge over at most nine chunks. That is one **below** the ten the library
    attaches, deliberately -- one slot of reserved headroom, not a library limit and not the main
    database, which consumes none. It is stated here as a second check because the plan already
    refuses at construction: this is the successor's own re-derivation, in the process that will
    do the work, and it never says *"the planner already checked this"*.

    Neither refusal is repaired by merging in passes. Several sorted passes into one B-tree
    interleave and lose exactly the write locality the sort is for, and an intermediate that
    removed the interleaving would be a second full copy of the source. Multi-pass sorted loading
    remains a future fallback.

    Raises:
        ChunkConsolidationError: the running library cannot attach that many, or the partition
            exceeds the single-pass architectural cap.
    """
    observed = attachment_limit() if limit is None else limit
    if chunk_count > observed:
        message = (
            f"this consolidation needs {chunk_count} attached chunk databases and the SQLite "
            f"build running HERE reports SQLITE_LIMIT_ATTACHED = {observed}. The merge reads "
            "every chunk in one compound select, so this build cannot execute this plan at all. "
            "The partition is REFUSED rather than merged in passes, and nothing was created"
        )
        raise ChunkConsolidationError(message)
    if chunk_count > SINGLE_PASS_CHUNK_CAP:
        message = (
            f"this consolidation needs {chunk_count} chunks and the single-pass chunked-F0 "
            f"architecture admits {SINGLE_PASS_CHUNK_CAP}. The running library attaches "
            f"{observed} and neither main nor temp consumes one of them; the cap sits one below "
            "that as deliberate reserved headroom, not because the library refuses. Use a larger "
            "chunk size, or implement the two-level merge this build deliberately does not"
        )
        raise ChunkConsolidationError(message)
    return chunk_count


def require_single_pass_plan(plan: ChunkPlan) -> ChunkPlan:
    """Refuse, before anything is read, a plan this single-pass consolidator may not consume.

    **This is the D151-C10 decoupling seen from the consolidator's side.** A plan may now describe
    more chunks than the single-pass architecture can merge -- a calibration-only plan does, by
    definition -- and the consolidator's answer to such a plan is the one it always gave: the
    single-pass cap, asked FIRST, over the plan's own chunk bounds, before the repository is
    measured, before a receipt is opened, before a directory is listed and before a database is
    attached. Three questions, in this order:

    1. **Is the plan exactly its sealed self?** The digest is recomputed and the coverage rules
       are re-derived through :func:`~disclosure_drift.m3.chunk_plan.require_sealed_plan`, so an
       object altered after sealing is refused rather than consumed.
    2. **Does it fit the single-pass architecture?** More than
       :data:`~disclosure_drift.m3.chunk_plan.SINGLE_PASS_CHUNK_CAP` chunks is refused with the
       architectural reason -- ahead of the library capability question, which is only asked of
       a partition the architecture admits (:func:`require_attachable`).
    3. **Is it a single-pass plan at all?** This check is **reachable and load-bearing**, and
       D151-C11 (MINOR-1) corrected an earlier claim here that it was defence in depth only. The
       calibration width rule compares a plan's chunk count against the cap the plan **declares**,
       not against this build's constant, and a declared cap is refused only when it exceeds the
       constant. A valid, sealed calibration record that declares a lowered cap -- five chunks
       under a declared cap of three, say -- therefore passes :func:`require_sealed_plan`, passes
       question 2 (five is within nine) and passes :func:`require_attachable`; **this line is the
       only thing that refuses it**, and it refuses on the contract. The same line refuses a
       multipass plan (D151-C13), which is consumed only by the multipass finalizer and never by
       this single-pass consolidator, although a multipass plan is also always wider than the cap.

    Raises:
        ChunkPlanError: the plan is not its sealed self, or fails a coverage rule.
        ChunkConsolidationError: the partition exceeds the single-pass cap, the running library
            cannot attach it, or the plan is not a single-pass plan.
    """
    require_sealed_plan(plan)
    width = len(plan.chunks)
    if width > SINGLE_PASS_CHUNK_CAP:
        message = (
            f"this consolidation needs {width} chunks and the single-pass chunked-F0 "
            f"architecture admits {SINGLE_PASS_CHUNK_CAP}. The refusal is HERE, at the "
            "consolidator's entry, before the repository is measured, before a chunk receipt is "
            "read and before a database is attached: nothing was created, listed, merged or "
            "attached. A partition wider than the cap is never merged in passes and never "
            "partially merged; multi-pass consolidation is a future architecture this build does "
            "not implement"
        )
        raise ChunkConsolidationError(message)
    require_attachable(width)
    if plan.contract != CHUNK_PLAN_CONTRACT:
        message = (
            f"a plan sealed under contract {plan.contract!r} is never consolidated by this "
            f"single-pass consolidator, which consumes only {CHUNK_PLAN_CONTRACT!r}. A "
            "calibration-only plan exists to execute and measure one chunk; its chunks are "
            "noncanonical evidence and no world is ever assembled from them. A multipass plan "
            "is consumed only by the multipass finalizer, whose second level is the one place "
            "a >9 canonical world is created"
        )
        raise ChunkConsolidationError(message)
    return plan


def _attach_all(
    connection: sqlite3.Connection, paths: Sequence[Path], prefix: str
) -> tuple[str, ...]:
    """Attach every chunk artifact read-only and side-effect free, and return the aliases.

    ``immutable=1`` is what makes this safe for an artifact a receipt has bound: an ordinary
    read-only attach of a WAL-mode database creates ``-wal`` and ``-shm`` files beside it, which
    would change the chunk's artifact **set** and make its own manifest verification fail. A
    completed chunk genuinely is immutable, so the promise the parameter makes is one the
    contract already guarantees -- and SQLite refuses a write through the handle either way.
    """
    aliases = []
    for index, path in enumerate(paths):
        alias = f"{prefix}{index}"
        connection.execute(f"ATTACH DATABASE 'file:{path.resolve()}?immutable=1' AS {alias}")
        aliases.append(alias)
    return tuple(aliases)


def _detach_all(connection: sqlite3.Connection, aliases: Sequence[str]) -> None:
    for alias in aliases:
        connection.execute(f"DETACH DATABASE {alias}")


def _union_all(aliases: Sequence[str], table: str, projection: str, *, extra: str = "") -> str:
    """One compound select over the same table in every attached chunk, in plan order.

    ``extra`` adds the per-chunk constants a reduction needs -- the chunk's ordinal, and where
    relevant a priority -- so that a window function or an ``INSERT OR IGNORE`` can reproduce the
    order the monolithic traversal wrote in.
    """
    parts = []
    for ordinal, alias in enumerate(aliases):
        columns = projection if not extra else f"{projection}, {ordinal}{extra}"
        parts.append(f"SELECT {columns} FROM {alias}.{table}")  # noqa: S608
    return " UNION ALL ".join(parts)


# --------------------------------------------------------------------------- #
# Deferred indexes
# --------------------------------------------------------------------------- #
def _deferrable_indexes(connection: sqlite3.Connection) -> tuple[tuple[str, str], ...]:
    """Every explicitly declared index on an F0 table, as ``(name, create statement)``.

    Implicit indexes -- the ones SQLite creates for a ``PRIMARY KEY`` or ``UNIQUE`` clause --
    carry no SQL and cannot be dropped; they stay, which is exactly what makes the *sorted* load
    matter. What is dropped and rebuilt are the declared secondary indexes, whose per-row
    maintenance during a bulk load is pure waste: one sorted build afterwards produces the
    identical index.
    """
    rows = connection.execute(
        "SELECT name, sql, tbl_name FROM sqlite_master WHERE type = 'index' AND sql IS NOT NULL"
    ).fetchall()
    return tuple(
        (str(row["name"]), str(row["sql"]))
        for row in rows
        if str(row["tbl_name"]) in F0_WRITTEN_TABLES
    )


# --------------------------------------------------------------------------- #
# The merge
# --------------------------------------------------------------------------- #
def _sorted_bulk_load(connection: sqlite3.Connection, table: str, aliases: Sequence[str]) -> None:
    """One table's key-sorted bulk load, read straight from every chunk in one statement.

    **There is no staging copy.** An earlier shape of this merge appended every chunk's rows into
    a scratch database and then sorted that; measured on a two-million-row probe it cost an extra
    full read and write of the whole source and ran 1.5x slower than reading the chunks directly,
    and at governed scale it would have needed a second hundred-gigabyte artifact and the free
    space to hold it. The chunks are already the staged form: they are immutable, they are keyed
    the same way, and they can be read in one compound select.

    ``ORDER BY`` the target's own identity columns is the whole point: SQLite inserts into a
    B-tree, and rows arriving in key order append to its rightmost leaf instead of dirtying a
    fresh page per row. Measured directly on the same probe, a random-key load wrote **756.9
    bytes of write-ahead log per row** and the identical rows loaded in key order wrote **379.5**
    -- a 2.0x write amplification at two million rows, which grows with the ratio of tree size to
    page cache and is exactly what accepted Decision 118 measured as F0's constraint.

    ``chunk_ordinal`` breaks ties in canonical plan order, so ``INSERT OR IGNORE``'s
    first-writer-wins reaches the same row the monolithic traversal's first write would have.
    """
    strategy = _MERGE_STRATEGY[table]
    columns = _columns(connection, table)
    projection = ", ".join(columns)
    key = ", ".join(_MERGE_KEY[table])
    verb = "INSERT OR IGNORE INTO" if strategy == "or_ignore" else "INSERT INTO"
    union = _union_all(aliases, table, projection, extra=" AS chunk_ordinal")
    connection.execute(
        f"{verb} {table} ({projection}) "  # noqa: S608
        f"SELECT {projection} FROM ({union}) ORDER BY {key}, chunk_ordinal"
    )


def _keyed_first_last_load(
    connection: sqlite3.Connection, table: str, aliases: Sequence[str]
) -> None:
    """The accepted upsert, reduced over chunks -- ``census_registrants``, ``census_accessions``.

    Both tables are written by ``INSERT ... ON CONFLICT(<key>) DO UPDATE SET
    latest_observed_at_utc = excluded.latest_observed_at_utc``. Over a whole source that means:
    every column comes from the **first** record that created the row, and
    ``latest_observed_at_utc`` from the **last** record that touched it. Over a partition, the
    first record is in the canonical-earliest chunk that holds the key and the last is in the
    canonical-latest -- so the reduction is exactly ``ROW_NUMBER`` over ``chunk_ordinal``.
    """
    columns = _columns(connection, table)
    projection = ", ".join(columns)
    selected = ", ".join(f"f.{column}" for column in columns if column != "latest_observed_at_utc")
    key = _MERGE_KEY[table][0]
    union = _union_all(aliases, table, projection, extra=" AS chunk_ordinal")
    connection.execute(
        f"INSERT INTO {table} ({projection}) "  # noqa: S608
        "WITH ranked AS ("
        "  SELECT *,"
        f"    ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY chunk_ordinal) AS rn_first,"
        f"    ROW_NUMBER() OVER (PARTITION BY {key} ORDER BY chunk_ordinal DESC) AS rn_last"
        f"  FROM ({union}))"
        f"SELECT {selected}, l.latest_observed_at_utc "
        f"FROM ranked AS f JOIN ranked AS l ON l.{key} = f.{key} AND l.rn_last = 1 "
        f"WHERE f.rn_first = 1 ORDER BY f.{key} "
        f"ON CONFLICT({key}) DO UPDATE SET latest_observed_at_utc = excluded.latest_observed_at_utc"
    )


#: The run-local temporary table the cross-chunk first-witness corrections are staged in.
#:
#: A ``TEMP`` table, so it exists only for this connection and never appears in any catalog. It
#: is bounded by the **cross-chunk duplicate accession** population rather than by the record
#: population, which is the whole reason the correction is affordable.
CORRECTIONS_TABLE: Final = "chunk_observation_corrections"


def _first_witness_corrections(
    connection: sqlite3.Connection, aliases: Sequence[str]
) -> tuple[int, int]:
    """Stage every observation row the cross-chunk first-witness rule implies -- the hard case.

    For an accession whose witnesses fall in **one** chunk, that chunk already reproduced the
    accepted behaviour exactly: it saw the same witnesses in the same order and decided the same
    way. Only an accession witnessed in **more than one** chunk needs anything, and for it the
    accepted behaviour decomposes into two additions, both of which are pure functions of rows
    the chunks already persisted:

    * the **winner** -- the canonical-earliest chunk's witness -- is the source's real first
      witness, and a real first witness that is later joined by a rival has its omitted
      observations back-filled by :func:`reconstructed_observations` over its own canonical row.
      Idempotent, and identical to the accepted back-fill, because it reads the same row through
      the same function;
    * every **later chunk's local-first witness** was not the source's first witness after all,
      so it materializes every governed field it observed --
      :func:`materialized_fields` with ``first_witness=False``, over the payload that chunk
      already stored. Its own reduced rows are a strict subset of these and carry identical
      values, so the upgrade is purely additive and never rewrites a row.

    Returns:
        ``(accessions_corrected, rows_staged)``.
    """
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
    contested = connection.execute(
        "SELECT accession_plain, MIN(chunk_ordinal) AS winner, COUNT(*) AS witnesses "  # noqa: S608
        f"FROM ({union}) GROUP BY accession_plain HAVING witnesses > 1 "
        "ORDER BY accession_plain"
    ).fetchall()
    staged = 0
    for row in contested:
        accession = str(row["accession_plain"])
        canonical = connection.execute(
            "SELECT accession_plain, source_observation_id, parsed_record_id, "
            "first_observed_at_utc, form_type, filing_date_sec, report_date, "
            "acceptance_datetime_sec_raw, primary_document_name, "
            "CASE WHEN registrant_cik_numeric IS NULL THEN NULL "
            "ELSE printf('%010d', registrant_cik_numeric) END AS registrant_cik_padded "
            "FROM census_accessions WHERE accession_plain = ?",
            (accession,),
        ).fetchone()
        if canonical is None:  # pragma: no cover - the row was just loaded from the chunks
            message = f"accession {accession!r} vanished between load and correction"
            raise ChunkConsolidationError(message)
        staged += _stage_rows(
            connection,
            accession=accession,
            observation_id=str(canonical["source_observation_id"]),
            parsed_id=str(canonical["parsed_record_id"]),
            observed=str(canonical["first_observed_at_utc"]),
            pairs=list(reconstructed_observations(dict(canonical))),
        )
        rivals = connection.execute(
            "SELECT source_observation_id, parsed_record_id, first_observed_at_utc "  # noqa: S608
            f"FROM ({union}) WHERE accession_plain = ? AND chunk_ordinal > ? "
            "ORDER BY chunk_ordinal",
            (accession, int(row["winner"])),
        ).fetchall()
        for rival in rivals:
            parsed_id = str(rival["parsed_record_id"])
            payload_row = connection.execute(
                "SELECT payload_json FROM census_parsed_records WHERE parsed_record_id = ?",
                (parsed_id,),
            ).fetchone()
            if payload_row is None:  # pragma: no cover - loaded before this runs
                message = f"parsed record {parsed_id!r} is absent at correction time"
                raise ChunkConsolidationError(message)
            payload = json.loads(str(payload_row["payload_json"]))
            staged += _stage_rows(
                connection,
                accession=accession,
                observation_id=str(rival["source_observation_id"]),
                parsed_id=parsed_id,
                observed=str(rival["first_observed_at_utc"]),
                pairs=[
                    (field, payload[field])
                    for field in materialized_fields(payload, first_witness=False)
                ],
            )
    return len(contested), staged


def _stage_rows(
    connection: sqlite3.Connection,
    *,
    accession: str,
    observation_id: str,
    parsed_id: str,
    observed: str,
    pairs: Sequence[tuple[str, object]],
) -> int:
    rows = [
        (
            _stable_id("accession-observation", accession, observation_id, parsed_id, field),
            accession,
            observation_id,
            parsed_id,
            field,
            _stable_json(value),
            observed,
            0,
        )
        for field, value in pairs
    ]
    if rows:
        connection.executemany(
            f"INSERT INTO {CORRECTIONS_TABLE} VALUES (?, ?, ?, ?, ?, ?, ?, ?)",  # noqa: S608
            rows,
        )
    return len(rows)


def _load_accession_observations(connection: sqlite3.Connection, aliases: Sequence[str]) -> None:
    """One sorted load of both the chunk rows and the first-witness corrections.

    A single compound select sorted once, rather than two loads: two sorted loads into one B-tree
    interleave and lose exactly the locality the sort was for. ``priority`` reproduces the
    accepted write order within one identifier -- a first witness's own exception rows are
    written during its parse, and the back-filled reconstruction arrives later and loses the
    ``INSERT OR IGNORE`` -- so first-writer-wins picks the same row the monolithic run kept.
    """
    columns = _columns(connection, "census_accession_observations")
    projection = ", ".join(columns)
    parts = [
        f"SELECT {projection}, {ordinal} AS chunk_ordinal, 0 AS priority "  # noqa: S608
        f"FROM {alias}.census_accession_observations"
        for ordinal, alias in enumerate(aliases)
    ]
    parts.append(
        f"SELECT {projection}, 2147483647 AS chunk_ordinal, 1 AS priority "  # noqa: S608
        f"FROM temp.{CORRECTIONS_TABLE}"
    )
    union = " UNION ALL ".join(parts)
    connection.execute(
        f"INSERT OR IGNORE INTO census_accession_observations ({projection}) "  # noqa: S608
        f"SELECT {projection} FROM ({union}) "
        "ORDER BY accession_observation_id, priority, chunk_ordinal"
    )


def _reduced_parser_run(
    connection: sqlite3.Connection, aliases: Sequence[str], *, contract: ExecutionContract
) -> _ReducedRun:
    """Reduce every chunk's run row to the one row the source's single parser run implies.

    ``parser_run_id`` is a content digest over the observation, the parser and its version, so
    every chunk computes the **same** identifier -- which is correct: they are parts of one
    logical parser run, and there is exactly one of it. What has to be reduced is what the run
    *counted*.

    **The parser identity is read from the rows and held to the contract** -- D151-C5 INFO-2.
    The chunks' rows must name one parser and one version, and that pair must be the pair the
    unanimously validated execution contract declares (:func:`_require_parser_run_truth`). Both
    are established here, before the reduced row is written, so a refusal leaves the world with
    no run row and no loaded table.

    The summary is folded in canonical plan order by the accepted rules. One of them deserves its
    proof written down: ``structural`` is capped at
    :data:`~disclosure_drift.sec.census.STREAMED_STRUCTURAL_DETAIL_LIMIT` retained blocking
    observations, and each chunk already truncated its own array at that same cap.
    Concatenating in plan order and truncating once is therefore **exact**, not approximate: the
    merged prefix needs at most ``LIMIT`` entries in total, and every chunk contributed
    ``min(its blocking count, LIMIT)`` -- which is never fewer than the number still needed by
    the time that chunk is reached.
    """
    projection = (
        "parser_run_id, source_observation_id, parser_id, parser_version, started_at_utc, "
        "finished_at_utc, parsed_count, quarantined_count, outcome, summary_json"
    )
    union = _union_all(aliases, "census_parser_runs", projection, extra=" AS chunk_ordinal")
    rows = connection.execute(f"SELECT * FROM ({union}) ORDER BY chunk_ordinal").fetchall()  # noqa: S608
    if not rows:
        message = "no chunk carries a parser run row; consolidation is refused"
        raise ChunkConsolidationError(message)
    identifiers = {str(row["parser_run_id"]) for row in rows}
    if len(identifiers) != 1:
        message = (
            f"the chunks carry {len(identifiers)} distinct parser_run_id values "
            f"({sorted(identifiers)[:4]}); one source is one logical parser run and a "
            "consolidation that had to choose between two is refused"
        )
        raise ChunkConsolidationError(message)
    parser_run_id = identifiers.pop()
    parser_identities = {(str(row["parser_id"]), str(row["parser_version"])) for row in rows}
    if len(parser_identities) != 1:
        message = (
            f"the chunks' parser run rows name {len(parser_identities)} distinct parser/version "
            f"pairs ({sorted(parser_identities)[:4]}); one source is one parser run under one "
            "parser, and a consolidation that had to choose between two is refused"
        )
        raise ChunkConsolidationError(message)
    parser_id, parser_version = next(iter(parser_identities))
    _require_parser_run_truth(contract=contract, parser_id=parser_id, parser_version=parser_version)
    summaries = [json.loads(str(row["summary_json"])) for row in rows]
    unknown: set[str] = set()
    warnings: list[object] = []
    duplicates: list[object] = []
    failures: list[object] = []
    structural: list[object] = []
    observed = 0
    blocking = 0
    reason_codes: set[str] = set()
    for summary in summaries:
        unknown.update(summary.get("unknown_field_paths", []))
        warnings.extend(summary.get("normalization_warnings", []))
        duplicates.extend(summary.get("duplicate_identities", []))
        failures.extend(summary.get("required_field_failures", []))
        structural.extend(summary.get("structural", []))
        detail = summary.get("structural_detail", {})
        observed += int(detail.get("observed", 0))
        blocking += int(detail.get("blocking", 0))
        reason_codes.update(summary.get("reason_codes", []))
    retained = structural[:STREAMED_STRUCTURAL_DETAIL_LIMIT]
    parsed = sum(int(row["parsed_count"]) for row in rows)
    quarantined = sum(int(row["quarantined_count"]) for row in rows)
    if blocking:
        outcome = "failed"
    elif quarantined:
        outcome = "completed_with_quarantine"
    else:
        outcome = "completed"
    summary_json = _stable_json(
        {
            "parser_id": parser_id,
            "parser_version": parser_version,
            "layer_version": PARSER_LAYER_VERSION,
            "counts": {
                "parsed": parsed,
                "quarantined": quarantined,
                "duplicate_identities": len(duplicates),
                "required_field_failures": len(failures),
                "unknown_fields": len(unknown),
                "normalization_warnings": len(warnings),
                "structural_observations": observed,
                "structural_failures": blocking,
            },
            "counts_are_trustworthy": blocking == 0,
            "unknown_field_paths": sorted(unknown),
            "normalization_warnings": warnings,
            "duplicate_identities": duplicates,
            "required_field_failures": failures,
            "reason_codes": sorted(reason_codes),
            "structural": retained,
            "structural_detail": {
                "scope": "blocking_only",
                "observed": observed,
                "blocking": blocking,
                "retained": len(retained),
                "retention_limit": STREAMED_STRUCTURAL_DETAIL_LIMIT,
                "table": "census_structural_observations",
            },
        }
    )
    connection.execute(
        "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, parser_id, "
        "parser_version, started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
        "outcome, summary_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            parser_run_id,
            str(rows[0]["source_observation_id"]),
            parser_id,
            parser_version,
            min(str(row["started_at_utc"]) for row in rows),
            max(str(row["finished_at_utc"]) for row in rows),
            parsed,
            quarantined,
            outcome,
            summary_json,
        ),
    )
    duplicate_identities = tuple(
        sorted({str(cast("Sequence[object]", item)[0]) for item in duplicates if item})
    )
    return _ReducedRun(
        parser_run_id=parser_run_id,
        parser_id=parser_id,
        parser_version=parser_version,
        outcome=outcome,
        parsed=parsed,
        quarantined=quarantined,
        parser_state=_STREAMED_PARSER_STATE[outcome],
        duplicate_identities=duplicate_identities,
    )


@dataclass(frozen=True, slots=True)
class _ReducedRun:
    """The one parser-run row every chunk is a part of, reduced.

    ``parser_id`` and ``parser_version`` are the pair the chunks' own run rows name -- the
    reduced accepted evidence -- and are already proved equal to the execution contract's.
    """

    parser_run_id: str
    parser_id: str
    parser_version: str
    outcome: str
    parsed: int
    quarantined: int
    parser_state: str
    duplicate_identities: tuple[str, ...]


def _require_parser_run_truth(
    *, contract: ExecutionContract, parser_id: str, parser_version: str
) -> None:
    """Hold the chunks' agreed execution contract to the parser run they actually wrote.

    **Agreement among receipts is agreement among claims -- D151-C5 INFO-2.**
    :func:`resolve_chunk_inputs` proves every chunk's receipt names the same ``parser_id`` and
    ``parser_version``. A receipt is excluded from its own artifact manifest, so the same forgery
    applied to every receipt leaves every artifact byte-identical, every manifest green, and every
    chunk in perfect agreement with every other. The parser run row each chunk wrote into its
    manifest-bound working catalog is different in kind: the accepted catalog writer wrote it from
    the parser that actually ran, and it cannot be edited without moving bytes the receipt binds.
    That row is the truth, and the contract is held to it here -- in the process about to build
    the final world from those rows, before the reduced row is written.

    ``batch_size`` is deliberately not compared: it is an execution-only durability granularity
    the accepted contract already governs chunk-to-chunk, and no run row records it.

    Raises:
        ChunkConsolidationError: the agreed contract names a parser or a version the reduced
            parser-run evidence does not.
    """
    _require(
        contract.parser_id == parser_id and contract.parser_version == parser_version,
        f"every chunk receipt agrees the execution contract was parser {contract.parser_id!r} "
        f"version {contract.parser_version!r}, and the parser run row the chunks actually wrote "
        f"-- the reduced accepted evidence this world is built from -- records {parser_id!r} "
        f"version {parser_version!r}. A contract every receipt agrees on is still a claim; the "
        "durable run row is what the parser wrote, and a consolidation whose declared contract "
        "does not describe its own evidence is refused. Nothing was merged",
    )


def _apply_duplicate_identities(connection: sqlite3.Connection, reduced: _ReducedRun) -> None:
    """Raise the run-level duplicate flag for every identity any chunk reported.

    The accepted streamed path applies this once, at the end, over the identities its parts
    accumulated -- a record's run-level verdict can depend on a part that had not been read when
    it was written. Over a partition the accumulation is the union of the chunks' own, and the
    statement is the accepted one, unchanged. Bounded by construction: the whole governed source
    measured **zero** duplicate identities and nineteen distinct unknown field paths.
    """
    for identity in reduced.duplicate_identities:
        connection.execute(
            "UPDATE census_parsed_records SET duplicate_indicator = 1 "
            "WHERE parser_run_id = ? AND native_identity = ?",
            (reduced.parser_run_id, identity),
        )


# --------------------------------------------------------------------------- #
# Evidence: the member manifest and the replayed completeness digest
# --------------------------------------------------------------------------- #
class _StoredMemberDigest:
    """A stand-in that hands :class:`ProjectionDigest` a member digest already computed.

    The source-level completeness digest is a fold over ``("member-digest", record count, member
    digest)`` in traversal order, and every one of those three values is durable in the merged
    member manifest. Replaying the fold therefore needs no record and no archive byte -- but it
    must be the **accepted** fold rather than a second expression of it, which is what this
    exists for: :meth:`ProjectionDigest.end_member` runs unchanged and simply reads a digest that
    was computed during the chunk's own parse instead of one it just accumulated.
    """

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def hexdigest(self) -> str:
        """The member digest the chunk recorded."""
        return self._value


def _member_deltas(connection: sqlite3.Connection, aliases: Sequence[str]) -> tuple[int, int]:
    """Correct every member's compact-evidence counters for the cross-chunk first-witness rule.

    ``CompactSourceEvidence`` counts a governed field as *omitted* when the canonical accession
    row can carry it and the record is the source's first witness of that accession, and as
    *materialized* otherwise. A chunk decided that against the accessions **it** had seen, so a
    record that is first in its chunk but not first in the source was counted as an omission the
    accepted rule would have materialized.

    Every such record is exactly a ledger row that is not the global minimum for its identity,
    and each carries the difference its downgrade makes. One window function finds them, one
    grouped sum applies them, and the result lands in a ``TEMP`` table that never reaches a
    catalog. **The reduction is over every chunk at once**, which is what makes "first in the
    whole source" answerable at all.

    Returns:
        ``(members_corrected, total_delta)``.
    """
    union = _union_all(
        aliases,
        "chunk_first_witness",
        "native_identity, member_ordinal, record_ordinal, delta_materialized",
    )
    connection.execute(
        "CREATE TEMP TABLE chunk_member_delta AS "  # noqa: S608
        "WITH ranked AS ("
        "  SELECT member_ordinal, delta_materialized,"
        "    ROW_NUMBER() OVER (PARTITION BY native_identity "
        "                       ORDER BY member_ordinal, record_ordinal) AS rn"
        f"  FROM ({union}))"  # noqa: S608
        "SELECT member_ordinal, SUM(delta_materialized) AS delta FROM ranked "
        "WHERE rn > 1 GROUP BY member_ordinal"
    )
    row = connection.execute(
        "SELECT COUNT(*) AS members, COALESCE(SUM(delta), 0) AS total FROM chunk_member_delta"
    ).fetchone()
    return int(row["members"]), int(row["total"])


def _merge_sidecar(
    *,
    sidecar_path: Path,
    inputs: Sequence[ChunkInput],
    plan: ChunkPlan,
    source_id: str,
) -> tuple[str, str, Mapping[str, int], tuple[int, int]]:
    """Build the consolidated compact-evidence sidecar and replay the completeness digest.

    Member ordinals are already the **canonical** ones -- each chunk numbered its members from
    its own interval's start -- so the merged manifest is the whole source's manifest with no
    renumbering, no gaps and no collisions. The source row is then recomputed from it, and its
    completeness digest is replayed through the accepted fold.

    Two attach passes rather than one, deliberately: the witness ledgers are read and reduced,
    detached, and only then are the chunk sidecars attached. That keeps the attachment count at
    one per chunk rather than two, so the chunk-count ceiling stays where
    :func:`require_attachable` states it.

    Raises:
        ChunkConsolidationError: the merged manifest is not exactly the source's members.
    """
    sidecar = CompactEvidenceSidecar(sidecar_path)
    sidecar.close()
    connection = sqlite3.connect(f"file:{sidecar_path}", uri=True, isolation_level=None)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        witness_aliases = _attach_all(connection, [item.witness_path for item in inputs], "w")
        try:
            corrected = _member_deltas(connection, witness_aliases)
        finally:
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
            union = _union_all(sidecar_aliases, "compact_source_members", projection)
            connection.execute(
                f"INSERT INTO main.compact_source_members ({projection}) "  # noqa: S608
                f"SELECT {corrected_projection} FROM ({union}) AS m "
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
            "the merged member manifest repeats a member ordinal; two chunks absorbed the same "
            "member and the consolidation is refused",
        )
        _require(
            total == plan.total_members
            and int(summary["lo"]) == 0
            and int(summary["hi"]) == plan.total_members - 1,
            f"the merged member manifest holds {total} members over "
            f"[{summary['lo']}, {summary['hi']}] where the plan records {plan.total_members} "
            f"over [0, {plan.total_members - 1}]",
        )
        _require(
            int(summary["omitted"]) >= 0,
            "a first-witness correction drove a member's omitted-observation count below zero, "
            "which cannot be true of any real parse. The consolidation is refused, not clamped",
        )
        chain = ProjectionDigest(source_id)
        for row in connection.execute(
            "SELECT parsed_registrants, parsed_accessions, parsed_other, projection_digest "
            "FROM main.compact_source_members ORDER BY member_ordinal"
        ):
            chain._records = (  # noqa: SLF001 - the accepted fold, replayed
                int(row["parsed_registrants"])
                + int(row["parsed_accessions"])
                + int(row["parsed_other"])
            )
            chain._member = cast(  # noqa: SLF001
                "Any", _StoredMemberDigest(str(row["projection_digest"]))
            )
            chain.end_member()
        completeness = chain.hexdigest()
        totals = {
            "members": total,
            "records": int(summary["records"] or 0),
            "omitted": int(summary["omitted"] or 0),
            "materialized": int(summary["materialized"] or 0),
        }
    finally:
        connection.close()
    reopened = CompactEvidenceSidecar(sidecar_path)
    try:
        reopened.record_source(
            source_observation_id=plan.source_observation_id,
            source_id=source_id,
            artifact_sha256=plan.source_sha256,
            artifact_byte_length=plan.source_byte_length,
            members=total,
            records=totals["records"],
            omitted_field_observations=totals["omitted"],
            materialized_field_observations=totals["materialized"],
            completeness_digest=completeness,
        )
        manifest_digest = reopened.member_manifest_digest(plan.source_observation_id)
    finally:
        reopened.close()
    return completeness, manifest_digest, totals, corrected


# --------------------------------------------------------------------------- #
# The final receipt
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class FinalWorldReceipt:
    """The consolidated world's create-once terminal record -- D151-C1 §15, D151-C3 §8 E.

    **It binds the identity consolidation actually ran under, not the one it was told about.**
    ``repository_head_sha`` and ``repository_tree_sha`` are the identity
    :func:`~disclosure_drift.m3.repository_identity.require_clean_running_repository` measured
    from the live checkout at consolidation time; ``catalog_source_sha256`` is the digest of the
    seed catalog the final world was actually built from, taken by reading it; and
    ``execution_contract_identity`` is the normalized execution identity every admitted chunk
    agreed on. A reader of this receipt can therefore answer *which code, which catalog, which
    execution* without trusting anything a caller said.
    """

    contract: str
    consolidation_contract: str
    plan_digest: str
    source_instance_id: str
    source_observation_id: str
    source_sha256: str
    repository_head_sha: str
    repository_tree_sha: str
    catalog_source_sha256: str
    execution_contract_identity: str
    chunk_count: int
    chunk_inputs: tuple[Mapping[str, object], ...]
    chunks_unchanged: bool
    parser_run_id: str
    run_outcome: str
    parser_state_after: str
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
    manifest: ArtifactManifest
    completed_at_utc: str
    status: str

    def as_record(self) -> Mapping[str, object]:
        """The complete receipt as a plain mapping, carrying no absolute path."""
        return {
            "contract": self.contract,
            "consolidation_contract": self.consolidation_contract,
            "plan_digest": self.plan_digest,
            "source_instance_id": self.source_instance_id,
            "source_observation_id": self.source_observation_id,
            "source_sha256": self.source_sha256,
            "repository_head_sha": self.repository_head_sha,
            "repository_tree_sha": self.repository_tree_sha,
            "catalog_source_sha256": self.catalog_source_sha256,
            "execution_contract_identity": self.execution_contract_identity,
            "chunk_count": self.chunk_count,
            "chunk_inputs": [dict(item) for item in self.chunk_inputs],
            "chunks_unchanged": self.chunks_unchanged,
            "parser_run_id": self.parser_run_id,
            "run_outcome": self.run_outcome,
            "parser_state_after": self.parser_state_after,
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
            "manifest": dict(self.manifest.as_record()),
            "completed_at_utc": self.completed_at_utc,
            "status": self.status,
        }


#: Every key the accepted :func:`~disclosure_drift.m3.single_source_canary._phase_f0_body`
#: returns, plus the one its caller adds. Stated as a constant so the derivation below can be
#: checked **against the accepted source** rather than against a reader's memory of it: a test
#: parses the accepted function's own return statement and asserts this set is exactly its keys.
#:
#: A field added to the accepted payload and not derived here would be a field F1 or F2 reads and
#: a consolidated world does not carry, so the check is a real gate rather than documentation.
ACCEPTED_F0_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "started_at_utc",
        "plan_position",
        "plan_source_count",
        "operational_catalog_sha256_before",
        "work_root_free_bytes_before",
        "source_id",
        "source_observation_id",
        "source_artifact_sha256",
        "source_artifact_byte_length",
        "disposition",
        "parser_state_before",
        "parser_state_after",
        "parser_run_id",
        "members",
        "projection_records",
        "parsed_records",
        "quarantined_records",
        "omitted_field_observations",
        "materialized_field_observations",
        "completeness_digest",
        "corroboration",
        "capacity_observations",
    }
)


@dataclass(frozen=True, slots=True)
class _AcceptedPlanState:
    """What the accepted plan says about this source, read before anything was written.

    Read from the **operational catalog** through a strictly read-only handle, which is where
    :func:`~disclosure_drift.m3.single_source_canary.run_canary_phase` reads the same three
    values from. That matters for one of them in particular: ``parser_state_before`` is the state
    the source was in *before* this F0, and the operational catalog is the one copy consolidation
    never writes to, so reading it there is correct by construction rather than by careful
    ordering.
    """

    plan_position: int
    plan_source_count: int
    parser_state_before: str
    disposition: str
    plan_fingerprint: str
    observation_id: str
    artifact_sha256: str
    artifact_byte_length: int


def _accepted_plan_state(operational_catalog: Path, plan: ChunkPlan) -> _AcceptedPlanState:
    """Derive the accepted plan facts a consolidated F0 terminal must carry.

    Every value is read through the **accepted** selector and the **accepted** classifier --
    :func:`select_planned_source`, :func:`planned_source_observation`,
    :func:`classify_planned_source`, :func:`plan_fingerprint` -- so a consolidated world's
    terminal describes the same plan the accepted monolithic F0 would have described.

    The bound observation is then required to be the artifact the plan partitions, by identifier,
    digest **and** byte length. A chunk already proved that for itself; this proves the plan and
    the accepted catalog still agree at the moment the world is assembled.

    Raises:
        ChunkConsolidationError: the bound observation is not the plan's artifact.
        OfflineParseError: the accepted selector or classifier refuses.
    """
    with strictly_read_only_connection(operational_catalog) as reader:
        selected = select_planned_source(reader, plan.source_instance_id)
        observation = planned_source_observation(reader, selected)
        disposition = classify_planned_source(selected.source, observation)
        fingerprint, _ = plan_fingerprint(reader)
    _require(
        observation is not None,
        f"planned source {plan.source_instance_id!r} binds no stored observation at "
        "consolidation time; a consolidated F0 terminal is never assembled over an observation "
        "that is not there",
    )
    assert observation is not None  # noqa: S101 - narrowed by the refusal above
    _require(
        observation.observation_id == plan.source_observation_id,
        f"the planned source is bound to observation {observation.observation_id!r} where the "
        f"chunk plan records {plan.source_observation_id!r}",
    )
    _require(
        (observation.logical_sha256 or "") == plan.source_sha256
        and int(observation.content_size_bytes or 0) == plan.source_byte_length,
        "the bound observation names a different source artifact than the chunk plan does",
    )
    return _AcceptedPlanState(
        plan_position=selected.plan_position,
        plan_source_count=selected.plan_source_count,
        parser_state_before=selected.source.parser_state,
        disposition=disposition,
        plan_fingerprint=fingerprint,
        observation_id=observation.observation_id,
        artifact_sha256=observation.logical_sha256 or "",
        artifact_byte_length=int(observation.content_size_bytes or 0),
    )


def derived_f0_outcome(
    *,
    plan: ChunkPlan,
    state: _AcceptedPlanState,
    reduced: _ReducedRun,
    members: int = 0,
    records: int = 0,
    omitted: int = 0,
    materialized: int = 0,
    completeness_digest: str = "",
) -> SingleSourceOutcome:
    """The accepted F0 outcome object a consolidated world implies -- D151-C3 §6.

    **Every semantic value here is derived, none is accepted from a caller.** The disposition and
    the pre-parse parser state come from the accepted plan through the accepted classifier; the
    post-parse state, the run identifier and the record counts come from the reduced parser run
    the chunks' own rows produced; the evidence totals and the completeness digest come from the
    merged compact sidecar. A caller has no way to state any of them, which is the point: a
    consolidated world that reached a blocking terminal cannot be presented as one that did not.

    ``corroboration`` is ``None``, and mechanically so rather than by omission. The accepted
    :func:`materialize_one_planned_source` populates it only for ``sec_full_index_company``, and
    :func:`~disclosure_drift.m3.chunk_plan.require_chunkable_source` admits only
    ``sec_bulk_submissions`` -- so a chunked F0 has no corroboration to carry, and the accepted
    F2 reads the field as optional. The two facts are asserted together at the call site.
    """
    return SingleSourceOutcome(
        outcome=PlannedSourceOutcome(
            source_instance_id=plan.source_instance_id,
            source_id=plan.source_id,
            disposition=cast("Any", state.disposition),
            parser_run_id=reduced.parser_run_id,
            parsed_records=reduced.parsed,
            quarantined_records=reduced.quarantined,
            parser_state_before=state.parser_state_before,
            parser_state_after=reduced.parser_state,
        ),
        observation=None,
        corroboration=None,
        completeness_digest=completeness_digest,
        members=members,
        records=records,
        omitted_field_observations=omitted,
        materialized_field_observations=materialized,
    )


def derived_f0_payload(
    *,
    outcome: SingleSourceOutcome,
    state: _AcceptedPlanState,
    plan: ChunkPlan,
    started_at_utc: str,
    catalog_source_sha256: str,
    work_root_free_bytes_before: int,
    capacity_observations: Sequence[Mapping[str, object]],
) -> Mapping[str, object]:
    """The accepted F0 phase-checkpoint payload, reconstructed field for field -- D151-C3 §6.

    **This is the accepted payload, not a payload shaped like it.** Every key
    :func:`~disclosure_drift.m3.single_source_canary._phase_f0_body` returns is produced here from
    the same value it produces there, and its caller's one added key --
    ``capacity_observations`` -- is produced here too. :data:`ACCEPTED_F0_PAYLOAD_KEYS` names the
    complete set and a test derives that set from the accepted function's own source, so a field
    added there and missed here is a test failure rather than a world F2 refuses at the end of a
    twenty-seven-hour run.

    **What a caller may still state, and why each one is physical rather than semantic.**
    ``started_at_utc`` is derived from the earliest chunk's recorded start; the free-space reading
    and the capacity observations are measurements of a host at instants that have passed, and no
    consolidated database holds them. None of the three can contradict the world: they name when
    and where, never what.
    """
    return {
        "started_at_utc": started_at_utc,
        "plan_position": state.plan_position,
        "plan_source_count": state.plan_source_count,
        "operational_catalog_sha256_before": catalog_source_sha256,
        "work_root_free_bytes_before": work_root_free_bytes_before,
        "source_id": plan.source_id,
        "source_observation_id": state.observation_id,
        "source_artifact_sha256": state.artifact_sha256,
        "source_artifact_byte_length": state.artifact_byte_length,
        "disposition": outcome.outcome.disposition,
        "parser_state_before": outcome.outcome.parser_state_before,
        "parser_state_after": outcome.outcome.parser_state_after,
        "parser_run_id": outcome.outcome.parser_run_id,
        "members": outcome.members,
        "projection_records": outcome.records,
        "parsed_records": outcome.outcome.parsed_records,
        "quarantined_records": outcome.outcome.quarantined_records,
        "omitted_field_observations": outcome.omitted_field_observations,
        "materialized_field_observations": outcome.materialized_field_observations,
        "completeness_digest": outcome.completeness_digest,
        "corroboration": None,
        "capacity_observations": list(capacity_observations),
    }


@dataclass(frozen=True, slots=True)
class ConsolidationResult:
    """What one consolidation established, and where it put it."""

    world_directory: Path
    receipt: FinalWorldReceipt
    inputs: tuple[ChunkInput, ...]


def consolidate_chunks(  # noqa: PLR0915 - one merge, and every predicate it must establish
    *,
    plan: ChunkPlan,
    internal_root: Path,
    operational_catalog: Path,
    world_directory: Path,
    run_id: str,
    external_root: Path | None = None,
    cache_bytes: int | None = None,
    capacity_observations: Sequence[Mapping[str, object]] = (),
) -> ConsolidationResult:
    """Build ONE canonical F0 world from every validated chunk -- D151-C1 §§15, 16, 22.

    **Before the sequence begins**, the plan itself is refused unless it is exactly its sealed
    self and within the single-pass width (:func:`require_single_pass_plan`, D151-C10) -- so a
    plan wider than the cap, a calibration-only plan among them, costs no measurement, no read,
    no directory and no attach.

    The sequence, in the order it must happen:

    1. the **live repository identity** is derived through the accepted clean-repository
       mechanism, and a dirty or moved checkout refuses before anything is read;
    2. every chunk is resolved to exactly one verified authoritative copy, the whole set is
       proved to be this plan's exact coverage, and every chunk is proved to belong to **one**
       execution -- same plan, same instance, same observation, same repository revision, same
       normalized execution contract;
    3. the chunks' recorded repository identity is required to be the identity **this checkout**
       reports, and the seed catalog is required by **digest** to be the one every chunk copied;
    4. the final world is created from that same accepted operational catalog, so the seed is
       identical rather than merely equivalent;
    5. every chunk's working catalog is attached read-only and immutably -- **there is no staging
       copy**: the chunks already are the staged form;
    6. the declared secondary indexes are dropped;
    7. each table is bulk-loaded by one **key-sorted** statement, under the accepted write
       containment;
    8. the cross-chunk first-witness corrections are computed into a ``TEMP`` table and loaded in
       the same sorted pass as the observation rows;
    9. the two accepted whole-observation derivations are run **once**, exactly as the monolithic
       path runs them once;
    10. the indexes are rebuilt;
    11. the compact-evidence sidecar is merged, its completeness digest replayed and its source
        row finalized -- **before the gate**, which is the accepted position: the accepted
        :func:`~disclosure_drift.m3.offline_parse.materialize_one_planned_source` finishes its
        sidecar before it returns, and only then does
        :func:`~disclosure_drift.m3.single_source_canary._f0` ask the gate (D151-C5 INFO-6);
    12. **the accepted D140-R12 blocking-terminal gate is applied**, over the complete derived
        outcome, between the merge's completion and anything that reads its output -- exactly
        where the accepted ``_f0`` applies it;
    13. only then is the run-local ledger marked parsed;
    14. every chunk's manifest is re-verified, proving consolidation mutated none of them;
    15. the F0 phase checkpoint is written from a **mechanically derived** payload, so the
        accepted F1 admits this world by the accepted rule;
    16. the final receipt is written **LAST**.

    **Step 12 is the disposition boundary, and it is the accepted one.** A consolidated F0 whose
    reduced parser run reached a blocking terminal leaves its durable rows and its finalized
    diagnostic sidecar exactly where they are, for diagnosis -- the same state the accepted
    monolithic F0 leaves -- and marks nothing parsed, writes no phase checkpoint, writes no final
    receipt, and is refused by the accepted F1 admission because there is no F0 terminal to
    continue from. The refusal is raised by
    :func:`~disclosure_drift.m3.single_source_canary.require_f0_success` itself rather than by a
    parallel rule stated here.

    Args:
        run_id: The run this F0 belongs to. A **name**, not a semantic value: it can say which
            run, never what the run found.
        capacity_observations: Physical capacity measurements taken during chunk execution, if
            any. Carried into the terminal exactly as the accepted phase path carries its own.

    Raises:
        ChunkConsolidationError: any consolidation precondition fails.
        SingleSourceCanaryError: the consolidated F0 reached a blocking terminal.
        RepositoryIdentityError: the executing checkout is dirty or cannot be identified.
    """
    require_chunkable_source(plan.source_id)
    # D151-C10: the plan is proved to be exactly its sealed self and to be one this SINGLE-PASS
    # consolidator may consume -- BEFORE the repository is measured, before a receipt is read,
    # before a directory is listed, and before anything is attached. A calibration-only plan is
    # wider than the cap by construction and is refused here, by width, every time.
    require_single_pass_plan(plan)
    # The live identity of the checkout doing the consolidating, measured through the accepted
    # mechanism rather than accepted as an argument -- D151-C3 §9. A dirty or untracked-file
    # working tree refuses here, before a chunk is read.
    repository = require_clean_running_repository()
    inputs = resolve_chunk_inputs(plan, internal_root=internal_root, external_root=external_root)
    require_attachable(len(inputs))
    contract = inputs[0].receipt.execution_contract
    _require_consolidation_identity(
        inputs=inputs,
        repository=repository,
        contract=contract,
        operational_catalog=operational_catalog,
    )
    state = _accepted_plan_state(operational_catalog, plan)
    started_at_utc = min(item.receipt.started_at_utc for item in inputs)
    if world_directory.exists():
        message = (
            f"the consolidated world {world_directory.name!r} already exists; a final world is "
            "create-once and is never reused, resumed, repaired, or overwritten"
        )
        raise ChunkConsolidationError(message)
    # Measured before the world exists, which is exactly what the accepted payload field means:
    # how much room there was on the volume this F0 was about to write into. Taken from the
    # nearest ancestor that exists, because `mkdir(parents=True)` below may be creating several.
    free_before = shutil.disk_usage(_nearest_existing(world_directory)).free
    world_directory.mkdir(mode=_DIRECTORY_MODE, parents=True)

    with WorkingCatalog(operational_catalog, world_directory, cache_bytes=cache_bytes) as world:
        connection = world.connection
        migration_head = world.identity.migration_head
        _require(
            migration_head == contract.migration_head,
            f"the final world was seeded at migration head {migration_head} where every chunk "
            f"executed at {contract.migration_head}",
        )
        # Ahead of the first durable row, exactly as the accepted `_f0` opens: an interruption
        # between here and the merge is visibly an interruption rather than an untouched source.
        world.ledger.begin_source(plan.source_instance_id, plan.source_id)
        aliases = _attach_all(connection, [item.catalog_path for item in inputs], "k")
        try:
            indexes = _deferrable_indexes(connection)
            for name, _sql in indexes:
                connection.execute(f"DROP INDEX IF EXISTS {name}")
            with transaction(connection):
                # The single reduced run row FIRST: every other F0 table carries a foreign key
                # to it, and the final world is opened with `PRAGMA foreign_keys = ON` exactly
                # as every other catalog connection is.
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
                # Outside the containment, deliberately: the corrections land in a run-local
                # TEMP table, which is not an accepted catalog table and must not be admitted to
                # the accepted footprint merely because this path writes one.
                corrected, staged_rows = _first_witness_corrections(connection, aliases)
                with write_containment(connection):
                    _load_accession_observations(connection, aliases)
                    # The two accepted whole-observation derivations, run ONCE -- exactly as the
                    # monolithic path runs them once, at the end, over everything it wrote.
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
        # The compact-evidence sidecar, merged and finalized BEFORE the gate -- D151-C5 INFO-6.
        # This is the accepted order: `materialize_one_planned_source` records the member
        # manifest as it parses and finishes the source row before it returns, and only then
        # does `_f0` ask `require_f0_success`. A blocking terminal therefore leaves the same
        # finalized diagnostic sidecar the monolithic path leaves, beside the same durable rows.
        completeness, manifest_digest, totals, evidence = _merge_sidecar(
            sidecar_path=world_directory / COMPACT_EVIDENCE_SIDECAR_FILENAME,
            inputs=inputs,
            plan=plan,
            source_id=plan.source_id,
        )
        # The complete accepted outcome, derived once: the reduced run's disposition and counts,
        # and the merged sidecar's evidence totals and completeness digest. The gate and the
        # terminal describe this one object.
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
        # D140-R12, at the accepted position: between the parse's completion and anything that
        # reads its output. The predicate is the ACCEPTED one, called rather than restated, so a
        # consolidated F0 reaches the same disposition boundary a monolithic F0 reaches. Nothing
        # below this line runs for a blocking terminal -- not the ledger, not the checkpoint, not
        # the receipt -- and the world stays exactly as it is.
        require_f0_success(outcome)
        world.ledger.mark_parsed(
            plan.source_instance_id,
            parts=plan.total_members,
            batches=reduced.parsed,
        )

    for item in inputs:
        verify_artifact_manifest(
            item.directory,
            item.receipt.manifest,
            exclude=(CHUNK_RECEIPT_FILENAME, TRANSFER_RECEIPT_FILENAME),
        )
    checkpoint = PhaseCheckpoint(
        contract=PHASE_RESTART_CONTRACT,
        phase=PHASE_F0,
        status=PHASE_STATUS_COMPLETE,
        run_id=run_id,
        source_instance_id=plan.source_instance_id,
        # The accepted phase identity, derived from the live repository and the durability
        # granularity every chunk is proved to have shared -- never supplied.
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
                capacity_observations=capacity_observations,
            )
        ),
    )
    ledger = RunProgressLedger(world_directory / PROGRESS_LEDGER_FILENAME)
    try:
        write_phase_checkpoint(ledger, checkpoint)
    finally:
        ledger.close()
    manifest = build_artifact_manifest(world_directory, exclude=(FINAL_WORLD_RECEIPT_FILENAME,))
    receipt = FinalWorldReceipt(
        contract=FINAL_WORLD_RECEIPT_CONTRACT,
        consolidation_contract=CONSOLIDATION_CONTRACT,
        plan_digest=plan.plan_digest,
        source_instance_id=plan.source_instance_id,
        source_observation_id=plan.source_observation_id,
        source_sha256=plan.source_sha256,
        repository_head_sha=repository.head_sha,
        repository_tree_sha=repository.tree_sha,
        catalog_source_sha256=contract.catalog_source_sha256,
        execution_contract_identity=contract.contract_identity,
        chunk_count=len(inputs),
        chunk_inputs=tuple(dict(item.as_record()) for item in inputs),
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
        first_witness_accessions_corrected=corrected,
        first_witness_rows_staged=staged_rows,
        evidence_members_corrected=evidence[0],
        evidence_delta=evidence[1],
        manifest=manifest,
        completed_at_utc=utc_now(),
        status="complete",
    )
    # LAST. A consolidation that stopped anywhere above leaves a world with no final receipt,
    # which every consumer reads as "this is not a consolidated F0 world".
    write_once_json(world_directory / FINAL_WORLD_RECEIPT_FILENAME, dict(receipt.as_record()))
    return ConsolidationResult(world_directory=world_directory, receipt=receipt, inputs=inputs)


def world_logical_digest(connection: sqlite3.Connection) -> Mapping[str, str]:
    """A per-table content digest over every F0-written table, excluding wall-clock columns.

    **The equivalence oracle's measuring instrument.** Two F0 worlds are compared by digesting
    each governed table's rows in a canonical order, with every ``*_at_utc`` column omitted --
    the accepted convention the Decision 110 streamed-versus-merged proof already uses, and for
    the same reason: two runs stamp their own instants, and the claim under test is that the
    *content* is identical rather than that they happened at once.

    Every digest a governed identity is actually built from -- the projection digest, the member
    manifest digest, the sidecar identity -- carries no timestamp at all by construction, so
    those are compared byte for byte elsewhere rather than approximated here.
    """
    digests: dict[str, str] = {}
    for table in F0_WRITTEN_TABLES:
        columns = [
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})")  # noqa: S608
            if not str(row["name"]).endswith(("_at_utc", "_at"))
        ]
        digest = hashlib.sha256()
        digest.update(table.encode("utf-8"))
        if columns:
            projection = ", ".join(columns)
            rows = sorted(
                tuple(str(value) for value in row)
                for row in connection.execute(f"SELECT {projection} FROM {table}")  # noqa: S608
            )
            for row in rows:
                digest.update("\x1f".join(row).encode("utf-8"))
                digest.update(b"\x1e")
        digests[table] = digest.hexdigest()
    return digests
