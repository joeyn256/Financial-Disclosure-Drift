"""Internal-hot / external-spill placement for completed chunks -- D151-C1 §§8-13.

**The tiering claim, stated before the mechanism.** The monolithic F0 spent roughly twenty-seven
hours issuing record-by-record random writes into one B-tree far larger than any page cache the
host can hold, on an external ExFAT volume reached over a dock. A chunked F0 changes the shape of
that work twice: the **active** chunk is a small database on fast internal NVMe, whose working set
a page cache can actually hold, and a **completed** chunk is an immutable object that the external
volume receives as bulk sequential bytes rather than as a long-lived random-update workload. This
module owns the second half: where a completed chunk lives, how it gets to the other tier, how
that arrival is proved, and -- above all -- how the runtime refuses to start work it cannot
finish.

**Capacity is a precondition, never a discovery.** D151-C1 §10 forbids "run until ENOSPC". Before
the next chunk starts, free space on the internal tier must be at least an accepted reserve plus
the projected peak requirement of the chunk about to run. Neither quantity is frozen in C1:
:data:`INTERNAL_RESERVE_BYTES` and :data:`CHUNK_PEAK_REQUIREMENT_BYTES` are ``None``, and ``None``
**refuses** -- it is never read as zero, never defaulted, and never inferred from the host. If the
floor cannot be established, the next chunk does not start; nothing is deleted to clear it.

**Nothing here removes anything.** No file-removal or directory-removal call appears anywhere in
this module, on any code path, and a test asserts exactly that against the source text. Reclaim is
a *decision* this module can compute and refuse; it is not a capability this module holds.
:data:`REAL_INTERNAL_RECLAIM_AUTHORITY` is ``None`` and
:func:`require_real_internal_reclaim_authority` refuses on every call.

**A verified transfer is not permission to reclaim.** D151-C1 §11 and §12: an external copy that
verifies makes the internal copy *eligible* for a separately governed reclaim; it never removes it
as a side effect, and the only verified copy is never the one considered.
"""

from __future__ import annotations

import hashlib
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.chunk_evidence import (
    CHUNK_RECEIPT_CONTRACT,
    CHUNK_RECEIPT_FILENAME,
    TRANSFER_RECEIPT_CONTRACT,
    TRANSFER_RECEIPT_FILENAME,
    ArtifactManifest,
    ChunkEvidenceError,
    ChunkReceipt,
    build_artifact_manifest,
    read_receipt_document,
    verify_artifact_manifest,
    write_once_json,
)
from disclosure_drift.m3.chunk_execution import completed_chunk_receipt
from disclosure_drift.m3.chunk_plan import ChunkPlan, chunk_by_id
from disclosure_drift.m3.external_working_root import QUALIFIED_EXTERNAL_VOLUME_UUID
from disclosure_drift.storage.sqlite import utc_now

__all__ = [
    "CHUNK_STORAGE_STATES",
    "CHUNK_PEAK_REQUIREMENT_BYTES",
    "INTERNAL_RESERVE_BYTES",
    "REAL_CHUNK_TRANSFER_AUTHORITY",
    "REAL_INTERNAL_RECLAIM_AUTHORITY",
    "STATE_COMPLETE_INTERNAL",
    "STATE_INTERNAL_RECLAIMED",
    "STATE_INTERNAL_RECLAIM_ELIGIBLE",
    "STATE_PLANNED",
    "STATE_RUNNING_INTERNAL",
    "STATE_TRANSFER_VERIFIED_EXTERNAL",
    "CapacityDecision",
    "ChunkPlacement",
    "ChunkStorageError",
    "TransferReceipt",
    "accepted_internal_reserve_bytes",
    "authoritative_input",
    "derive_chunk_placement",
    "derive_placements",
    "internal_free_bytes",
    "internal_reclaim_plan",
    "projected_next_chunk_peak_bytes",
    "require_capacity_for_next_chunk",
    "require_real_chunk_transfer_authority",
    "require_real_internal_reclaim_authority",
    "select_spill_candidates",
    "transfer_chunk",
]


class ChunkStorageError(DisclosureDriftError):
    """A tiered-storage precondition failed. Never worked around, never best-effort."""


#: The internal free-space reserve the runtime must leave standing. **Closed** -- D151-C1 §10.
#:
#: ``None`` is not zero and is never read as zero. C1 engineers the mechanism and measures the
#: sizing model; the real number is a property of the eventual execution host and of the frozen
#: chunk size, and an owner freezes it in a later reviewed change. Until then every capacity
#: decision that would need it **refuses**, which is exactly the behaviour a missing floor should
#: produce: the run does not start rather than starting without a floor.
INTERNAL_RESERVE_BYTES: Final[int | None] = None

#: The projected peak internal requirement of one chunk. **Closed** -- D151-C1 §10.
#:
#: The same reasoning. A measured projection from completed chunks is available through
#: :func:`projected_next_chunk_peak_bytes`, which is a *measurement over evidence* rather than a
#: frozen policy value; this constant is the frozen one and it stays ``None``.
CHUNK_PEAK_REQUIREMENT_BYTES: Final[int | None] = None

#: The governed token authorizing a **real** verified chunk transfer onto the qualified external
#: volume. ``None`` -- D151-C1 §24. A transfer whose destination is that volume refuses.
REAL_CHUNK_TRANSFER_AUTHORITY: Final[str | None] = None

#: The governed token authorizing a **real** reclaim of an internal chunk copy. ``None``.
#:
#: There is no deletion capability in this module to authorize: the constant exists so that the
#: refusal is explicit and so that a later owner instrument has exactly one literal to replace,
#: in a reviewed change that would also have to *add* the mechanism.
REAL_INTERNAL_RECLAIM_AUTHORITY: Final[str | None] = None

#: The chunk has bounds in the plan and no attempt has begun.
STATE_PLANNED: Final = "PLANNED"

#: An attempt directory exists on the internal tier and carries no valid terminal receipt.
STATE_RUNNING_INTERNAL: Final = "RUNNING_INTERNAL"

#: A valid terminal receipt exists on the internal tier and no verified external copy does.
STATE_COMPLETE_INTERNAL: Final = "COMPLETE_INTERNAL"

#: Both tiers carry the chunk and the external copy verifies against the internal receipt.
STATE_TRANSFER_VERIFIED_EXTERNAL: Final = "TRANSFER_VERIFIED_EXTERNAL"

#: The external copy verifies **and** every reclaim precondition holds. Still not a deletion.
STATE_INTERNAL_RECLAIM_ELIGIBLE: Final = "INTERNAL_RECLAIM_ELIGIBLE"

#: Only the verified external copy is present. Reachable in C1 only by an operator act outside
#: this module, because this module deletes nothing.
STATE_INTERNAL_RECLAIMED: Final = "INTERNAL_RECLAIMED"

#: Every state, in lifecycle order.
CHUNK_STORAGE_STATES: Final[tuple[str, ...]] = (
    STATE_PLANNED,
    STATE_RUNNING_INTERNAL,
    STATE_COMPLETE_INTERNAL,
    STATE_TRANSFER_VERIFIED_EXTERNAL,
    STATE_INTERNAL_RECLAIM_ELIGIBLE,
    STATE_INTERNAL_RECLAIMED,
)

#: Which tier a resolved consolidation input was read from.
TIER_INTERNAL: Final = "internal"
TIER_EXTERNAL: Final = "external"

_COPY_CHUNK_BYTES: Final = 1 << 20
_DIRECTORY_MODE: Final = 0o700


def require_real_chunk_transfer_authority() -> str:
    """The token authorizing a real chunk transfer onto the qualified volume, or a refusal.

    Raises:
        ChunkStorageError: :data:`REAL_CHUNK_TRANSFER_AUTHORITY` is ``None``.
    """
    granted = REAL_CHUNK_TRANSFER_AUTHORITY
    if granted is None:
        message = (
            "a real chunk transfer onto the qualified external volume is NOT AUTHORIZED: "
            "REAL_CHUNK_TRANSFER_AUTHORITY is None. D151-C1 §9 keeps real transfer CLOSED. "
            "Nothing was copied, nothing was written, and no operator flag, environment "
            "variable or configuration key substitutes for this constant"
        )
        raise ChunkStorageError(message)
    return granted


def require_real_internal_reclaim_authority() -> str:
    """The token authorizing a real internal reclaim, or a refusal -- D151-C1 §12.

    Raises:
        ChunkStorageError: :data:`REAL_INTERNAL_RECLAIM_AUTHORITY` is ``None``, which is its
            D151-C1 state. There is additionally no deletion capability in this module for such
            a token to enable.
    """
    granted = REAL_INTERNAL_RECLAIM_AUTHORITY
    if granted is None:
        message = (
            "internal chunk reclaim is NOT AUTHORIZED: REAL_INTERNAL_RECLAIM_AUTHORITY is None, "
            "and this module holds no removal capability at all -- no file-removal or "
            "directory-removal call appears on any code path in it. Reclaim eligibility is a "
            "computation here; performing one needs both a new owner instrument and a reviewed "
            "source change that would first have to ADD the mechanism"
        )
        raise ChunkStorageError(message)
    return granted


def accepted_internal_reserve_bytes() -> int:
    """The accepted internal free-space reserve, or a refusal -- D151-C1 §10.

    Raises:
        ChunkStorageError: :data:`INTERNAL_RESERVE_BYTES` is ``None``. **A ``None`` reserve is
            never treated as a zero reserve**, which is exactly the adversarial case D151-C1 §30
            A48 names: zero would admit every capacity decision and make the floor decorative.
    """
    reserve = INTERNAL_RESERVE_BYTES
    if reserve is None:
        message = (
            "no accepted internal free-space reserve is frozen: INTERNAL_RESERVE_BYTES is None. "
            "A None reserve is a REFUSAL, never a zero reserve: zero would satisfy every "
            "capacity comparison and turn the floor into decoration. The next chunk does not "
            "start, and nothing is deleted, moved, or cleaned to reach a floor that does not "
            "exist"
        )
        raise ChunkStorageError(message)
    return reserve


@dataclass(frozen=True, slots=True)
class CapacityDecision:
    """One capacity decision, with every input it was made from."""

    free_bytes: int
    reserve_bytes: int
    projected_peak_bytes: int
    required_bytes: int
    admitted: bool

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "free_bytes": self.free_bytes,
            "reserve_bytes": self.reserve_bytes,
            "projected_peak_bytes": self.projected_peak_bytes,
            "required_bytes": self.required_bytes,
            "admitted": self.admitted,
        }


def projected_next_chunk_peak_bytes(
    placements: Sequence[ChunkPlacement], *, headroom_ratio: float = 1.0
) -> int | None:
    """The projected internal peak of the next chunk, measured from completed ones.

    A **measurement over evidence**, deliberately not a frozen constant: it is the largest
    completed chunk's internal artifact size, optionally scaled. ``None`` when no chunk has
    completed yet, because a projection from nothing is a guess, and a guess is exactly what
    D151-C1 §10 forbids the capacity floor from resting on.

    Raises:
        ChunkStorageError: ``headroom_ratio`` is below one, which would project a chunk smaller
            than the largest already observed.
    """
    if headroom_ratio < 1.0:
        message = (
            f"a chunk peak projection headroom ratio below 1.0 ({headroom_ratio}) would project "
            "less space than a completed chunk already needed, and is refused"
        )
        raise ChunkStorageError(message)
    observed = [
        placement.internal_bytes for placement in placements if placement.internal_bytes is not None
    ]
    if not observed:
        return None
    return int(max(observed) * headroom_ratio)


def require_capacity_for_next_chunk(
    *,
    free_bytes: int,
    reserve_bytes: int | None = None,
    projected_peak_bytes: int | None = None,
) -> CapacityDecision:
    """Admit the next chunk onto the internal tier, or refuse it -- D151-C1 §10.

    The rule, stated once::

        internal_free >= accepted_internal_reserve + projected_next_chunk_peak_requirement

    ``>=`` at the floor, so the floor itself admits and one byte below refuses. **Neither input
    may be absent.** ``reserve_bytes`` defaults to :func:`accepted_internal_reserve_bytes`, which
    refuses while the constant is ``None``; ``projected_peak_bytes`` must be supplied or measured,
    and ``None`` refuses rather than contributing zero.

    **This never waits for ENOSPC and never frees space.** A refusal here means the next chunk
    does not start; the caller's remaining options are a governed transfer of a completed chunk
    to the durable tier, or a guarded stop. Neither is taken here.

    Raises:
        ChunkStorageError: an input is absent, or the floor is not met.
    """
    reserve = accepted_internal_reserve_bytes() if reserve_bytes is None else reserve_bytes
    if projected_peak_bytes is None:
        message = (
            "the next chunk's projected peak internal requirement is unknown, so the capacity "
            "floor cannot be established. An unknown projection is a REFUSAL, never a zero: the "
            "next chunk does not start, and nothing runs until free space happens to run out"
        )
        raise ChunkStorageError(message)
    if reserve < 0 or projected_peak_bytes < 0 or free_bytes < 0:
        message = (
            f"a capacity decision needs non-negative byte quantities; got free={free_bytes}, "
            f"reserve={reserve}, projected={projected_peak_bytes}"
        )
        raise ChunkStorageError(message)
    required = reserve + projected_peak_bytes
    # Python integers are arbitrary precision, so this sum cannot silently wrap. Stated because
    # D151-C1 §30 A47 asks the question, and the answer is a property of the language rather
    # than of a check that could be removed.
    decision = CapacityDecision(
        free_bytes=free_bytes,
        reserve_bytes=reserve,
        projected_peak_bytes=projected_peak_bytes,
        required_bytes=required,
        admitted=free_bytes >= required,
    )
    if not decision.admitted:
        message = (
            f"the next chunk is NOT ADMITTED onto the internal tier: {free_bytes} bytes free, "
            f"below the required {required} = {reserve} reserve + {projected_peak_bytes} "
            "projected chunk peak. STOP: the chunk does not start. Nothing was deleted, "
            "reclaimed, or cleaned to reach the floor, and there is no best-effort mode that "
            "writes until the filesystem refuses"
        )
        raise ChunkStorageError(message)
    return decision


@dataclass(frozen=True, slots=True)
class TransferReceipt:
    """One verified transfer's create-once terminal record -- D151-C1 §§9, 11, 12."""

    contract: str
    chunk_id: str
    plan_digest: str
    chunk_receipt_manifest_digest: str
    destination_manifest: ArtifactManifest
    destination_volume_uuid: str
    objects: int
    bytes_transferred: int
    verified_at_utc: str
    status: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "contract": self.contract,
            "chunk_id": self.chunk_id,
            "plan_digest": self.plan_digest,
            "chunk_receipt_manifest_digest": self.chunk_receipt_manifest_digest,
            "destination_manifest": dict(self.destination_manifest.as_record()),
            "destination_volume_uuid": self.destination_volume_uuid,
            "objects": self.objects,
            "bytes_transferred": self.bytes_transferred,
            "verified_at_utc": self.verified_at_utc,
            "status": self.status,
        }

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> TransferReceipt:
        """Rebuild a transfer receipt from its stored mapping.

        Raises:
            ChunkStorageError: a field is absent or is not of the recorded type.
        """
        try:
            manifest = record["destination_manifest"]
            if not isinstance(manifest, Mapping):
                message = "a transfer receipt's destination manifest is not a mapping; refused"
                raise ChunkStorageError(message)
            return cls(
                contract=str(record["contract"]),
                chunk_id=str(record["chunk_id"]),
                plan_digest=str(record["plan_digest"]),
                chunk_receipt_manifest_digest=str(record["chunk_receipt_manifest_digest"]),
                destination_manifest=ArtifactManifest.from_record(manifest),
                destination_volume_uuid=str(record["destination_volume_uuid"]),
                objects=int(str(record["objects"])),
                bytes_transferred=int(str(record["bytes_transferred"])),
                verified_at_utc=str(record["verified_at_utc"]),
                status=str(record["status"]),
            )
        except (KeyError, ValueError) as exc:
            message = f"a transfer receipt could not be read as this build writes them: {exc}"
            raise ChunkStorageError(message) from exc
        except ChunkEvidenceError as exc:
            message = f"a transfer receipt's destination manifest is refused: {exc}"
            raise ChunkStorageError(message) from exc


def transfer_chunk(
    *,
    source_directory: Path,
    destination_directory: Path,
    destination_volume_uuid: str | None,
) -> TransferReceipt:
    """Copy one completed immutable chunk to the durable tier and prove it arrived.

    The sequence is fixed and every step is a refusal point:

    1. the **source** is a completed chunk -- its terminal receipt is read and verified against
       its own artifacts, so a chunk that was altered after completion never transfers;
    2. the **destination volume is identified**. An unidentifiable volume refuses: a verified
       transfer onto something the runtime cannot name is not a durable copy. A destination on
       the accepted qualified external volume additionally requires
       :func:`require_real_chunk_transfer_authority`, which is closed;
    3. every object is copied and hashed **as it is written**;
    4. every object is then **independently re-read and re-hashed** from the destination, in a
       separate pass, and compared against the source manifest. A truncated copy and a copy of
       the same length with different bytes both fail here;
    5. the transfer receipt is written **LAST**, inside the destination.

    The internal copy is untouched throughout. A verified transfer is not a reclaim.

    Raises:
        ChunkStorageError: any step refuses.
        ChunkEvidenceError: the source receipt or either manifest refuses.
    """
    receipt_path = source_directory / CHUNK_RECEIPT_FILENAME
    chunk_receipt = ChunkReceipt.from_record(
        read_receipt_document(receipt_path, contract=CHUNK_RECEIPT_CONTRACT)
    )
    verify_artifact_manifest(
        source_directory, chunk_receipt.manifest, exclude=(CHUNK_RECEIPT_FILENAME,)
    )
    if destination_volume_uuid is None:
        message = (
            "the destination volume could not be identified, so this transfer is refused. A "
            "verified durable copy is never written onto a volume the runtime cannot name: an "
            "unidentified destination is indistinguishable from an ordinary directory left at a "
            "mount point after the volume went away"
        )
        raise ChunkStorageError(message)
    if destination_volume_uuid == QUALIFIED_EXTERNAL_VOLUME_UUID:
        require_real_chunk_transfer_authority()
    if destination_directory.exists():
        message = (
            f"external chunk copy {destination_directory.name!r} already exists; a durable copy "
            "is create-once and is never overwritten, resumed, or repaired"
        )
        raise ChunkStorageError(message)
    destination_directory.mkdir(mode=_DIRECTORY_MODE, parents=True)
    written = 0
    for entry in chunk_receipt.manifest.entries:
        source_object = source_directory / entry.relative_path
        target_object = destination_directory / entry.relative_path
        target_object.parent.mkdir(mode=_DIRECTORY_MODE, parents=True, exist_ok=True)
        digest = hashlib.sha256()
        length = 0
        with source_object.open("rb") as reader, target_object.open("xb") as target:
            for block in iter(lambda: reader.read(_COPY_CHUNK_BYTES), b""):
                digest.update(block)
                length += len(block)
                target.write(block)
            target.flush()
        if digest.hexdigest() != entry.sha256 or length != entry.byte_length:
            message = (
                f"object {entry.relative_path!r} changed while it was being copied: the source "
                f"read back as {length} bytes / {digest.hexdigest()} against the manifest's "
                f"{entry.byte_length} / {entry.sha256}. The transfer is refused; the internal "
                "copy is untouched and remains the only authoritative one"
            )
            raise ChunkStorageError(message)
        written += length
    # The chunk's own terminal receipt travels with it, byte for byte. It is deliberately NOT in
    # the manifest -- the manifest is what the receipt describes -- but a durable copy that could
    # not say which chunk it is, under which plan, would be an anonymous directory of databases.
    receipt_bytes = receipt_path.read_bytes()
    with (destination_directory / CHUNK_RECEIPT_FILENAME).open("xb") as target:
        target.write(receipt_bytes)
    if (destination_directory / CHUNK_RECEIPT_FILENAME).read_bytes() != receipt_bytes:
        message = (  # pragma: no cover - a filesystem that returns other bytes than it stored
            "the copied chunk receipt does not read back as the bytes that were written"
        )
        raise ChunkStorageError(message)
    # The independent second pass. Deliberately not the write-time hash: a write-time digest
    # proves what the process believed it wrote, and this proves what the destination now holds.
    destination_manifest = build_artifact_manifest(
        destination_directory,
        exclude=(CHUNK_RECEIPT_FILENAME, TRANSFER_RECEIPT_FILENAME),
    )
    if destination_manifest.digest != chunk_receipt.manifest.digest:
        message = (
            "the destination does not hold the chunk's artifact set after transfer: destination "
            f"manifest {destination_manifest.digest!r} against source "
            f"{chunk_receipt.manifest.digest!r}. A partial, truncated, or extra-object copy is "
            "refused, and no transfer receipt is written -- so the external copy can never be "
            "mistaken for a verified one"
        )
        raise ChunkStorageError(message)
    verify_artifact_manifest(
        destination_directory,
        chunk_receipt.manifest,
        exclude=(CHUNK_RECEIPT_FILENAME, TRANSFER_RECEIPT_FILENAME),
    )
    receipt = TransferReceipt(
        contract=TRANSFER_RECEIPT_CONTRACT,
        chunk_id=chunk_receipt.chunk_id,
        plan_digest=chunk_receipt.plan_digest,
        chunk_receipt_manifest_digest=chunk_receipt.manifest.digest,
        destination_manifest=destination_manifest,
        destination_volume_uuid=destination_volume_uuid,
        objects=len(destination_manifest.entries),
        bytes_transferred=written,
        verified_at_utc=utc_now(),
        status="verified",
    )
    # LAST. An interrupted transfer therefore leaves an unverified directory and no receipt,
    # which every consumer below reads as "not a durable copy".
    write_once_json(destination_directory / TRANSFER_RECEIPT_FILENAME, dict(receipt.as_record()))
    return receipt


@dataclass(frozen=True, slots=True)
class ChunkPlacement:
    """Where one chunk physically is, derived from durable evidence rather than declared.

    Every field below comes from re-reading and re-hashing objects on disk. Nothing here trusts
    a file that says what state a chunk is in: D151-C1 §11 asks for exactly that, and a status
    file is precisely what an adversary with write access edits first.
    """

    chunk_id: str
    state: str
    internal_directory: Path | None
    external_directory: Path | None
    internal_receipt: ChunkReceipt | None
    external_receipt: ChunkReceipt | None
    transfer_receipt: TransferReceipt | None
    internal_bytes: int | None
    external_bytes: int | None
    detail: str

    @property
    def has_verified_external(self) -> bool:
        """Whether a verified durable external copy exists."""
        return self.transfer_receipt is not None and self.external_receipt is not None

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "chunk_id": self.chunk_id,
            "state": self.state,
            "internal_present": self.internal_directory is not None,
            "external_present": self.external_directory is not None,
            "internal_bytes": self.internal_bytes,
            "external_bytes": self.external_bytes,
            "verified_external": self.has_verified_external,
            "detail": self.detail,
        }


def _verified_external(
    chunk_id: str, external_root: Path
) -> tuple[Path, ChunkReceipt, TransferReceipt] | None:
    directory = external_root / chunk_id
    if directory.is_symlink() or not directory.is_dir():
        return None
    transfer_path = directory / TRANSFER_RECEIPT_FILENAME
    if not transfer_path.is_file():
        return None
    transfer = TransferReceipt.from_record(
        read_receipt_document(transfer_path, contract=TRANSFER_RECEIPT_CONTRACT)
    )
    receipt = ChunkReceipt.from_record(
        read_receipt_document(directory / CHUNK_RECEIPT_FILENAME, contract=CHUNK_RECEIPT_CONTRACT)
    )
    verify_artifact_manifest(
        directory,
        receipt.manifest,
        exclude=(CHUNK_RECEIPT_FILENAME, TRANSFER_RECEIPT_FILENAME),
    )
    if transfer.chunk_receipt_manifest_digest != receipt.manifest.digest:
        message = (
            f"the transfer receipt for chunk {chunk_id!r} binds artifact manifest "
            f"{transfer.chunk_receipt_manifest_digest!r} where the chunk receipt beside it "
            f"records {receipt.manifest.digest!r}. The external copy is refused rather than "
            "read as verified"
        )
        raise ChunkStorageError(message)
    if transfer.chunk_id != chunk_id or receipt.chunk_id != chunk_id:
        message = (
            f"the external copy at {directory.name!r} describes chunk "
            f"{transfer.chunk_id!r}/{receipt.chunk_id!r} rather than {chunk_id!r}"
        )
        raise ChunkStorageError(message)
    return directory, receipt, transfer


def _directory_bytes(directory: Path | None) -> int | None:
    if directory is None:
        return None
    total = 0
    for path in directory.rglob("*"):
        if path.is_file() and not path.is_symlink():
            total += path.stat().st_size
    return total


def derive_chunk_placement(
    plan: ChunkPlan,
    chunk_id: str,
    *,
    internal_root: Path,
    external_root: Path | None = None,
) -> ChunkPlacement:
    """Where one chunk is, and what state that makes it -- derived, never declared.

    Raises:
        ChunkStorageError: the two tiers carry copies that disagree, or an external copy is
            present and does not verify.
        ChunkEvidenceError: a receipt or manifest refuses.
    """
    chunk_by_id(plan, chunk_id)
    internal = completed_chunk_receipt(internal_root, chunk_id)
    external = None if external_root is None else _verified_external(chunk_id, external_root)
    internal_receipt = None if internal is None else internal[0]
    internal_directory = None if internal is None else internal[1]
    external_directory = None if external is None else external[0]
    external_receipt = None if external is None else external[1]
    transfer_receipt = None if external is None else external[2]
    if internal_receipt is not None and external_receipt is not None:
        _require_agreeing_copies(chunk_id, internal_receipt, external_receipt)
    if internal_receipt is None and external_receipt is None:
        attempts = (internal_root / chunk_id).is_dir()
        return ChunkPlacement(
            chunk_id=chunk_id,
            state=STATE_RUNNING_INTERNAL if attempts else STATE_PLANNED,
            internal_directory=None,
            external_directory=None,
            internal_receipt=None,
            external_receipt=None,
            transfer_receipt=None,
            internal_bytes=None,
            external_bytes=None,
            detail=(
                "an attempt directory exists and carries no valid terminal receipt"
                if attempts
                else "no attempt has begun"
            ),
        )
    if internal_receipt is not None and external_receipt is None:
        return ChunkPlacement(
            chunk_id=chunk_id,
            state=STATE_COMPLETE_INTERNAL,
            internal_directory=internal_directory,
            external_directory=None,
            internal_receipt=internal_receipt,
            external_receipt=None,
            transfer_receipt=None,
            internal_bytes=_directory_bytes(internal_directory),
            external_bytes=None,
            detail="complete and immutable on the internal tier; no durable copy exists yet",
        )
    if internal_receipt is None:
        return ChunkPlacement(
            chunk_id=chunk_id,
            state=STATE_INTERNAL_RECLAIMED,
            internal_directory=None,
            external_directory=external_directory,
            internal_receipt=None,
            external_receipt=external_receipt,
            transfer_receipt=transfer_receipt,
            internal_bytes=None,
            external_bytes=_directory_bytes(external_directory),
            detail="only the verified external copy is present",
        )
    return ChunkPlacement(
        chunk_id=chunk_id,
        state=STATE_INTERNAL_RECLAIM_ELIGIBLE,
        internal_directory=internal_directory,
        external_directory=external_directory,
        internal_receipt=internal_receipt,
        external_receipt=external_receipt,
        transfer_receipt=transfer_receipt,
        internal_bytes=_directory_bytes(internal_directory),
        external_bytes=_directory_bytes(external_directory),
        detail=(
            "byte-identical verified copies on both tiers; the internal copy is ELIGIBLE for a "
            "separately governed reclaim and has not been reclaimed"
        ),
    )


def _require_agreeing_copies(chunk_id: str, internal: ChunkReceipt, external: ChunkReceipt) -> None:
    """Refuse two copies of one chunk that do not describe the same execution -- §22.

    Every identity must agree exactly. Disagreement is **never** resolved by preferring the
    internal copy, the faster copy, the newer copy, or the larger one: two different answers to
    "what did this chunk produce" is a condition to report, not a tie to break.
    """
    comparisons = (
        ("plan_digest", internal.plan_digest, external.plan_digest),
        ("member_order_digest", internal.member_order_digest, external.member_order_digest),
        ("execution_identity", internal.execution_identity, external.execution_identity),
        ("start", str(internal.start), str(external.start)),
        ("end", str(internal.end), str(external.end)),
        ("source_sha256", internal.source_sha256, external.source_sha256),
        ("manifest_digest", internal.manifest.digest, external.manifest.digest),
    )
    for field, left, right in comparisons:
        if left != right:
            message = (
                f"chunk {chunk_id!r} carries two copies that disagree on {field}: internal "
                f"{left!r}, external {right!r}. Duplicate authority is REFUSED rather than "
                "resolved -- nothing here prefers the internal copy because it is faster, the "
                "external because it is durable, or either because it is newer"
            )
            raise ChunkStorageError(message)


def derive_placements(
    plan: ChunkPlan, *, internal_root: Path, external_root: Path | None = None
) -> tuple[ChunkPlacement, ...]:
    """Every chunk's placement, in canonical plan order."""
    return tuple(
        derive_chunk_placement(
            plan, bounds.chunk_id, internal_root=internal_root, external_root=external_root
        )
        for bounds in plan.chunks
    )


def authoritative_input(placement: ChunkPlacement) -> tuple[Path, str]:
    """The one directory a consolidator reads this chunk from, and which tier it is.

    **Which physical copy is read is performance policy; the logical identity is not.** When both
    tiers carry the chunk, :func:`derive_chunk_placement` has already proved their receipts agree
    on every identity, so reading either reaches the same rows. The internal copy is preferred
    because it is the fast tier -- and that preference can never select a *stale* copy, because a
    copy that disagreed would have refused before this is reached.

    Raises:
        ChunkStorageError: the chunk has no verified copy on either tier.
    """
    if placement.internal_directory is not None:
        return placement.internal_directory, TIER_INTERNAL
    if placement.external_directory is not None:
        return placement.external_directory, TIER_EXTERNAL
    message = (
        f"chunk {placement.chunk_id!r} has no verified copy on either tier (state "
        f"{placement.state}). Consolidation is refused: a missing chunk is never treated as an "
        "empty one, skipped, or reconstructed"
    )
    raise ChunkStorageError(message)


def select_spill_candidates(
    placements: Sequence[ChunkPlacement], *, needed_bytes: int
) -> tuple[ChunkPlacement, ...]:
    """Which completed internal chunks to evacuate, deterministically -- D151-C1 §13.

    **The rule is canonical plan order, oldest chunk ordinal first**, and it is chosen for a
    reason that survives review: the chunk plan already defines a total order over chunks that is
    a property of the *source*, so evacuating in that order makes the spill sequence reproducible
    from the plan alone. Nothing here reads filesystem enumeration order, ``mtime``, directory
    listing order, size, or an operator's choice -- each of which would make two runs of the same
    plan evacuate different chunks and leave the decision unrecorded.

    Only chunks in :data:`STATE_COMPLETE_INTERNAL` are eligible: a running chunk is mutable, and
    an already-transferred chunk has nothing to gain from being transferred again.

    Raises:
        ChunkStorageError: ``needed_bytes`` is negative, or the eligible chunks cannot together
            release it -- in which case nothing partial is attempted.
    """
    if needed_bytes < 0:
        message = f"a spill selection needs a non-negative byte target; got {needed_bytes}"
        raise ChunkStorageError(message)
    selected: list[ChunkPlacement] = []
    released = 0
    for placement in placements:
        if released >= needed_bytes:
            break
        if placement.state != STATE_COMPLETE_INTERNAL:
            continue
        selected.append(placement)
        released += placement.internal_bytes or 0
    if released < needed_bytes:
        message = (
            f"no deterministic spill selection releases {needed_bytes} bytes: the completed "
            f"internal chunks together account for {released}. STOP: the next chunk does not "
            "start, nothing is evacuated part-way, and nothing is deleted to make the "
            "difference"
        )
        raise ChunkStorageError(message)
    return tuple(selected)


@dataclass(frozen=True, slots=True)
class ReclaimPlan:
    """What a governed reclaim *would* remove, and every proof it rests on.

    A computation, not an action. It exists so that eligibility can be reasoned about, tested and
    reviewed without a deletion capability existing anywhere near it.
    """

    chunk_id: str
    eligible: bool
    objects: tuple[str, ...]
    bytes_reclaimable: int
    proofs: Mapping[str, bool]
    detail: str

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering."""
        return {
            "chunk_id": self.chunk_id,
            "eligible": self.eligible,
            "objects": list(self.objects),
            "bytes_reclaimable": self.bytes_reclaimable,
            "proofs": dict(sorted(self.proofs.items())),
            "detail": self.detail,
        }


def internal_reclaim_plan(placement: ChunkPlacement) -> ReclaimPlan:
    """What reclaiming this chunk's internal copy would take, and whether it is eligible.

    Six proofs, every one of which must hold -- D151-C1 §12:

    * the chunk's own **terminal receipt is valid**;
    * an **external copy exists**;
    * the external copy's **manifest validated**;
    * **per-object cryptographic verification** completed;
    * the external **receipt was written last** and is present;
    * the external copy was **independently re-read** and the two copies' identities agree.

    All six are established by :func:`derive_chunk_placement` before this is reached, which is
    why an eligible placement is exactly :data:`STATE_INTERNAL_RECLAIM_ELIGIBLE` and nothing
    weaker. **Never the only verified copy**: a chunk with no external copy is not eligible, so
    the last copy can never be the one considered.

    Performing a reclaim additionally requires :func:`require_real_internal_reclaim_authority`,
    which refuses, **and** a mechanism this module does not contain.
    """
    proofs = {
        "chunk_terminal_receipt_valid": placement.internal_receipt is not None,
        "external_copy_exists": placement.external_directory is not None,
        "external_manifest_validated": placement.external_receipt is not None,
        "per_object_verification_complete": placement.transfer_receipt is not None,
        "external_receipt_written_last": (
            placement.transfer_receipt is not None
            and placement.transfer_receipt.status == "verified"
        ),
        "identities_agree": placement.state == STATE_INTERNAL_RECLAIM_ELIGIBLE,
    }
    eligible = all(proofs.values())
    objects = (
        ()
        if placement.internal_receipt is None
        else tuple(entry.relative_path for entry in placement.internal_receipt.manifest.entries)
    )
    return ReclaimPlan(
        chunk_id=placement.chunk_id,
        eligible=eligible,
        objects=objects if eligible else (),
        bytes_reclaimable=(placement.internal_bytes or 0) if eligible else 0,
        proofs=proofs,
        detail=(
            "eligible for a separately governed reclaim; NOT reclaimed, and this module holds "
            "no deletion capability"
            if eligible
            else "not eligible: at least one durable proof is absent, so the internal copy may "
            "be the only verified one"
        ),
    )


def internal_free_bytes(path: Path) -> int:
    """Free bytes on the filesystem hosting ``path``. A measurement, and only a measurement.

    ``shutil`` is imported by this module for :func:`shutil.disk_usage` and for nothing else; no
    other name from it is referenced anywhere here. Stated where a reader scanning for a removal
    capability will meet it.
    """
    return shutil.disk_usage(path).free
