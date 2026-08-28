"""D151-C22: verified transfer, exact receipts, reclaim separation, admission, telemetry -- R3-R7.

Every fixture is a disposable internal directory. The physical SSD is never touched, no real
project artifact is read, and every real authority constant stays ``None``: the isolated test
authorities are constructed here, over these fixtures only, which is exactly the seam C22-R4
names. Each test states the rule it holds and the mutation it kills.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c22_host_a_ssd_qualification as c22q  # noqa: E402

from disclosure_drift.m3 import chunk_storage as cs  # noqa: E402
from disclosure_drift.m3 import chunk_tiering as ct  # noqa: E402
from disclosure_drift.m3 import chunk_transfer as x  # noqa: E402
from disclosure_drift.m3 import host_a_ssd_qualification as q  # noqa: E402

TEST_TRANSFER = x.TransferAuthorization(grant="c22-isolated-test-transfer", granted_by="test")
TEST_RECLAIM = x.ReclaimAuthorization(grant="c22-isolated-test-reclaim", granted_by="test")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_source(
    root: Path, chunk_id: str = "chunk-0000", *, files: dict[str, bytes] | None = None
) -> x.TransferSource:
    """A terminal, immutable, manifested artifact directory with its own terminal receipt."""
    directory = root / "internal" / chunk_id / "attempt-0000"
    directory.mkdir(parents=True)
    payload = (
        {"a.bin": b"alpha" * 40_000, "sub/b.bin": b"bravo" * 12_345, "c.txt": b"charlie"}
        if files is None
        else files
    )
    entries = []
    for relative, data in payload.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entries.append(
            x.ManifestEntry(relative_path=relative, byte_length=len(data), sha256=_sha(data))
        )
    entries.sort(key=lambda e: e.relative_path)
    receipt = q.canonical_json_bytes(
        {
            "contract": "terminal",
            "chunk_id": chunk_id,
            "manifest_digest": x.manifest_digest(entries),
        }
    )
    (directory / x.SOURCE_RECEIPT_FILENAME).write_bytes(receipt)
    return x.TransferSource(
        chunk_id=chunk_id,
        plan_digest=_sha(b"plan"),
        directory=directory,
        entries=tuple(entries),
        receipt_sha256=_sha(receipt),
        receipt_bytes=len(receipt),
        repository_head_sha="7f3926ecf1e97ed187e70142f22e2a15b3f27443",
        repository_tree_sha="bfa71bb3234d286db43946823ea9af3aeb768582",
    )


def destination(root: Path) -> Path:
    path = root / "external"
    path.mkdir(exist_ok=True)
    return path


def run_transfer(
    root: Path,
    *,
    klass: str = q.CLASS_RECLAIM_CAPABLE,
    source: x.TransferSource | None = None,
    **kwargs: Any,
) -> tuple[
    x.VerifiedTransferReceipt,
    x.TransferSource,
    q.HostASsdQualification,
    q.LiveTierObservation,
    Path,
]:
    source = make_source(root) if source is None else source
    record = c22q.qualification(klass=klass)
    dest = destination(root)
    observation = c22q.observation_for(record, dest)
    receipt = x.verified_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=0,
        **kwargs,
    )
    return receipt, source, record, observation, dest


def _files(directory: Path) -> list[str]:
    return sorted(str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file())


# ==========================================================================
# R3: the verified transfer lifecycle -- P3, M3, M4, M5, M6
# ==========================================================================
def test_r3_a_verified_transfer_writes_the_receipt_last_and_the_copy_is_exact(
    tmp_path: Path,
) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    final = dest / source.chunk_id
    assert _files(final) == sorted(
        [e.relative_path for e in source.entries]
        + [x.SOURCE_RECEIPT_FILENAME, x.TRANSFER_RECEIPT_FILENAME]
    )
    assert not (dest / f"{source.chunk_id}{x.PARTIAL_SUFFIX}").exists()
    stored = json.loads((final / x.TRANSFER_RECEIPT_FILENAME).read_bytes())
    assert set(stored) == x.TRANSFER_RECEIPT_FIELDS
    assert stored["contract"] == "m3.3-chunked-f0-transfer-receipt/2"
    assert stored["qualification_identity"] == record.qualification_identity  # M6
    assert stored["stable_tier_compatibility_identity"] == record.stable_tier_compatibility_identity
    assert stored["destination_volume_uuid"] == c22q.VOLUME
    assert (
        stored["source_manifest_digest"]
        == source.manifest_digest
        == stored["chunk_receipt_manifest_digest"]
    )
    assert (
        stored["destination_manifest_verified"] is True
        and stored["destination_content_verified"] is True
    )
    assert x.VerifiedTransferReceipt.from_document(stored) == receipt
    assert set(receipt.bindings()) == set(x.TRANSFER_RECEIPT_REQUIRED_BINDINGS) | {
        "receipt_contract",
        "receipt_identity",
    }
    assert receipt.bindings()["receipt_contract"] == x.VERIFIED_TRANSFER_RECEIPT_CONTRACT
    assert receipt.bindings()["receipt_identity"] == receipt.receipt_identity
    # The accepted reclaim-eligibility bindings are complete, and the source is untouched.
    ct.require_transfer_receipt_bindings(receipt.bindings())
    assert _files(source.directory) == sorted(
        [e.relative_path for e in source.entries] + [x.SOURCE_RECEIPT_FILENAME]
    )
    assert (
        x.derive_transfer_state(
            destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
        ).state
        == x.STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE
    )


def test_m3_m4_no_receipt_without_an_independent_read_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """M3 (receipt before read-back) and M4 (streaming hash trusted): a copy whose bytes on disk
    differ from what was streamed is caught only by reopening the destination."""
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    original = x._copy_one  # noqa: SLF001

    def corrupt_copy(source_path: Path, target_path: Path, entry: x.ManifestEntry) -> Any:
        result = original(source_path, target_path, entry)
        if entry.relative_path == "a.bin":
            with target_path.open(
                "r+b"
            ) as handle:  # same length, different bytes, after the stream hash
                handle.seek(10)
                handle.write(b"X")
        return result

    monkeypatch.setattr(x, "_copy_one", corrupt_copy)
    with pytest.raises(x.ChunkTransferError, match="read back as"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=c22q.observation_for(record, dest),
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert not (dest / source.chunk_id).exists()
    assert not list(dest.rglob(x.TRANSFER_RECEIPT_FILENAME))
    assert (
        x.derive_transfer_state(
            destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
        ).state
        == x.STATE_PARTIAL_COPY
    )


def test_m5_an_existing_final_or_partial_destination_is_refused(tmp_path: Path) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    (dest / source.chunk_id).mkdir()
    with pytest.raises(x.ChunkTransferError, match="already exists"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    (dest / source.chunk_id).rmdir()
    (dest / f"{source.chunk_id}{x.PARTIAL_SUFFIX}").mkdir()
    with pytest.raises(x.ChunkTransferError, match="partial destination"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )


def test_r3_refusals_before_any_byte_is_copied(tmp_path: Path) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    # No authorization.
    with pytest.raises(x.ChunkTransferError, match="transfer authorization"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=None,
            external_reserve_bytes=0,
        )
    # Stale qualification identity: the tier reauthenticates against another record.
    other = c22q.qualification(compat=c22q.compatibility_record(volume_uuid=c22q.OTHER_VOLUME))
    with pytest.raises(q.HostASsdQualificationError, match="volume_uuid"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=other,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    # Wrong volume: the observation is of another device number.
    elsewhere = c22q.observation_for(record, dest, st_dev=observation.attachment["st_dev"] + 1)
    with pytest.raises(x.ChunkTransferError, match="not on the volume"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=elsewhere,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    # A symlink, an extra object, an unclosed database or a changed byte in the source.
    (source.directory / "sub" / "link").symlink_to(source.directory / "a.bin")
    with pytest.raises(x.ChunkTransferError, match="symbolic link"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    (source.directory / "sub" / "link").unlink()
    (source.directory / "extra.bin").write_bytes(b"x")
    with pytest.raises(x.ChunkTransferError, match="unexpected"):
        x.require_terminal_source(source)
    (source.directory / "extra.bin").unlink()
    (source.directory / "catalog.sqlite3-wal").write_bytes(b"")
    with pytest.raises(x.ChunkTransferError, match="not immutable"):
        x.require_terminal_source(source)
    (source.directory / "catalog.sqlite3-wal").unlink()
    (source.directory / "c.txt").write_bytes(b"changed")
    with pytest.raises(x.ChunkTransferError, match="changed while"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert not (dest / source.chunk_id).exists()
    for entry in dest.iterdir():
        assert not (entry / x.TRANSFER_RECEIPT_FILENAME).exists()


def test_c22e_r1_one_contract_string_maps_to_one_exact_shape(tmp_path: Path) -> None:
    """P1/M17/M24/M25/M29: the verified receipt is /2 and only /2; the legacy receipt is /1 and
    only its exact shape; neither parser reads the other's shape under either label; the
    contract is inside the receipt identity."""
    receipt, *_ = run_transfer(tmp_path)
    record = dict(receipt.as_record())
    assert (
        record["contract"]
        == x.VERIFIED_TRANSFER_RECEIPT_CONTRACT
        == cs.VERIFIED_TRANSFER_RECEIPT_CONTRACT
    )
    assert x.VERIFIED_TRANSFER_RECEIPT_CONTRACT == "m3.3-chunked-f0-transfer-receipt/2"
    assert (
        x.LEGACY_TRANSFER_RECEIPT_CONTRACT
        == cs.TRANSFER_RECEIPT_CONTRACT
        == cs.LEGACY_TRANSFER_RECEIPT_CONTRACT
    )
    assert x.LEGACY_TRANSFER_RECEIPT_CONTRACT == "m3.3-chunked-f0-transfer-receipt/1"
    # The identity seals the contract: the same body under another label is another identity.
    assert (
        x.sealed_identity(record, identity_key=x.RECEIPT_IDENTITY_KEY) == receipt.receipt_identity
    )
    relabelled_body = {**record, "contract": x.LEGACY_TRANSFER_RECEIPT_CONTRACT}
    assert (
        x.sealed_identity(relabelled_body, identity_key=x.RECEIPT_IDENTITY_KEY)
        != receipt.receipt_identity
    )
    for _label, edit in (
        (
            "/3",
            lambda r: r.__setitem__("contract", x.VERIFIED_TRANSFER_RECEIPT_CONTRACT[:-1] + "3"),
        ),
        ("extra", lambda r: r.__setitem__("legacy", 1)),
        ("missing", lambda r: r.pop("qualification_identity")),
        ("relabelled outcome", lambda r: r.__setitem__("transfer_outcome", "copied")),
        ("bool as int", lambda r: r.__setitem__("source_bytes", True)),
        (
            "duplicate keys disagree",
            lambda r: r.__setitem__("bytes_transferred", r["destination_bytes"] + 1),
        ),
    ):
        edited = dict(record)
        edit(edited)
        with pytest.raises(x.ChunkTransferError):
            x.VerifiedTransferReceipt.from_document(edited)
    stale = dict(record)
    stale["qualification_class"] = q.CLASS_COPY_ONLY  # edited, not resealed
    with pytest.raises(x.ChunkTransferError, match="does not seal"):
        x.VerifiedTransferReceipt.from_document(stale)
    # The NEW shape under /1 -- unsealed and resealed under /1 -- is refused by name, never read.
    new_shape_under_legacy = {**record, "contract": x.LEGACY_TRANSFER_RECEIPT_CONTRACT}
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        x.VerifiedTransferReceipt.from_document(new_shape_under_legacy)
    new_shape_under_legacy[x.RECEIPT_IDENTITY_KEY] = x.sealed_identity(
        new_shape_under_legacy, identity_key=x.RECEIPT_IDENTITY_KEY
    )
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        x.VerifiedTransferReceipt.from_document(new_shape_under_legacy)
    # The legacy shape under /2 is refused as inexact; the legacy shape under /1 is the legacy
    # receipt, and the legacy parser reads exactly that shape and nothing wider or narrower.
    legacy_keys = (
        "contract",
        "chunk_id",
        "plan_digest",
        "chunk_receipt_manifest_digest",
        "destination_manifest",
        "destination_volume_uuid",
        "objects",
        "bytes_transferred",
        "verified_at_utc",
        "status",
    )
    narrow = {k: record[k] for k in legacy_keys}
    with pytest.raises(x.ChunkTransferError, match="exact"):
        x.VerifiedTransferReceipt.from_document(narrow)
    legacy = {**narrow, "contract": x.LEGACY_TRANSFER_RECEIPT_CONTRACT}
    with pytest.raises(cs.ChunkStorageError, match="exact"):
        cs.TransferReceipt.from_record({**legacy, "receipt_identity": "0" * 64})  # superset refused
    with pytest.raises(cs.ChunkStorageError, match="exact"):
        cs.TransferReceipt.from_record(
            {k: v for k, v in legacy.items() if k != "status"}
        )  # subset refused
    with pytest.raises(cs.ChunkStorageError, match="exact"):
        cs.TransferReceipt.from_record(record)  # the /2 superset is never read as /1
    assert set(legacy) == cs.LEGACY_TRANSFER_RECEIPT_FIELDS
    with pytest.raises(cs.ChunkStorageError, match="exact"):
        cs.TransferReceipt.from_record(
            {
                **legacy,
                "contract": x.VERIFIED_TRANSFER_RECEIPT_CONTRACT,
                "receipt_identity": "0" * 64,
            }
        )


def _write_legacy_copy(source: x.TransferSource, dest: Path) -> Path:
    """A destination that looks exactly like an accepted C1 verified copy with a /1 receipt."""
    from disclosure_drift.m3.chunk_evidence import ArtifactEntry, ArtifactManifest, write_once_json

    final = dest / source.chunk_id
    for entry in source.entries:
        (final / entry.relative_path).parent.mkdir(parents=True, exist_ok=True)
        (final / entry.relative_path).write_bytes(
            (source.directory / entry.relative_path).read_bytes()
        )
    (final / x.SOURCE_RECEIPT_FILENAME).write_bytes(
        (source.directory / x.SOURCE_RECEIPT_FILENAME).read_bytes()
    )
    manifest = ArtifactManifest(
        entries=tuple(
            ArtifactEntry(relative_path=e.relative_path, byte_length=e.byte_length, sha256=e.sha256)
            for e in source.entries
        )
    )
    legacy = cs.TransferReceipt(
        contract=cs.TRANSFER_RECEIPT_CONTRACT,
        chunk_id=source.chunk_id,
        plan_digest=source.plan_digest,
        chunk_receipt_manifest_digest=manifest.digest,
        destination_manifest=manifest,
        destination_volume_uuid=c22q.VOLUME,
        objects=len(source.entries),
        bytes_transferred=source.total_bytes,
        verified_at_utc="2026-08-28T12:00:00Z",
        status="verified",
    )
    return write_once_json(final / x.TRANSFER_RECEIPT_FILENAME, dict(legacy.as_record()))


def test_c22e_p2_p3_a_legacy_receipt_confers_nothing_and_is_never_upgraded(tmp_path: Path) -> None:
    """P2/P3/M26/M28/M30: a valid legacy /1 receipt is read by the legacy route, refused by every
    C22 route by name, never relabelled or rewritten, and never satisfies eligibility."""
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    receipt_path = _write_legacy_copy(source, dest)
    before = receipt_path.read_bytes()
    # The shared reader dispatches on the contract and reads the legacy shape exactly.
    view = cs.read_transfer_receipt_view(receipt_path)
    assert view.contract == cs.LEGACY_TRANSFER_RECEIPT_CONTRACT and view.chunk_id == source.chunk_id
    # Every C22 route refuses it by name, and the file is untouched afterwards.
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        x.derive_transfer_state(
            destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
        )
    with pytest.raises(x.ChunkTransferError, match="legacy"):
        x.recover_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    eligibility = x.reclaim_eligibility(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    assert not eligibility.eligible and eligibility.proofs["transfer_receipt_valid"] is False
    with pytest.raises(x.ChunkTransferError, match="not eligible"):
        x.write_reclaim_intent(
            source=source, destination_root=dest, qualification=record, observation=observation
        )
    with pytest.raises(x.ChunkTransferError, match="no durable reclaim intent|legacy"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert receipt_path.read_bytes() == before
    assert not (dest / f"{source.chunk_id}{x.RECLAIM_DIRECTORY_SUFFIX}").exists()
    assert _files(source.directory) == sorted(
        [e.relative_path for e in source.entries] + [x.SOURCE_RECEIPT_FILENAME]
    )
    # A legacy receipt relabelled /2 -- with or without a malicious reseal -- is refused by the
    # shared reader too, and a /2 label on the legacy shape never reaches the legacy parser.
    legacy_record = json.loads(before)
    relabelled = {**legacy_record, "contract": x.VERIFIED_TRANSFER_RECEIPT_CONTRACT}
    (tmp_path / "relabelled.json").write_bytes(q.canonical_json_bytes(relabelled))
    with pytest.raises(cs.ChunkStorageError, match="refused"):
        cs.read_transfer_receipt_view(tmp_path / "relabelled.json")
    relabelled[x.RECEIPT_IDENTITY_KEY] = x.sealed_identity(
        relabelled, identity_key=x.RECEIPT_IDENTITY_KEY
    )
    (tmp_path / "resealed.json").write_bytes(q.canonical_json_bytes(relabelled))
    with pytest.raises(cs.ChunkStorageError, match="refused"):
        cs.read_transfer_receipt_view(tmp_path / "resealed.json")
    (tmp_path / "unknown.json").write_bytes(
        q.canonical_json_bytes(
            {**legacy_record, "contract": x.VERIFIED_TRANSFER_RECEIPT_CONTRACT[:-1] + "3"}
        )
    )
    with pytest.raises(cs.ChunkStorageError, match="never another"):
        cs.read_transfer_receipt_view(tmp_path / "unknown.json")
    # A /2 receipt reads through the shared reader as an in-memory view that keeps /2.
    verified, other_source, _record, _obs, other_dest = run_transfer(
        tmp_path / "v2", source=make_source(tmp_path / "v2", chunk_id="chunk-0007")
    )
    v2_view = cs.read_transfer_receipt_view(
        other_dest / other_source.chunk_id / x.TRANSFER_RECEIPT_FILENAME
    )
    assert v2_view.contract == cs.VERIFIED_TRANSFER_RECEIPT_CONTRACT
    assert v2_view.chunk_receipt_manifest_digest == verified.source_manifest_digest
    assert v2_view.destination_manifest.digest == verified.source_manifest_digest
    assert v2_view.bytes_transferred == verified.destination_bytes and v2_view.status == "verified"
    # A new-shape document mislabelled /1 is refused by the shared reader as inexact for /1.
    (tmp_path / "newshape_v1.json").write_bytes(
        q.canonical_json_bytes(
            {**verified.as_record(), "contract": x.LEGACY_TRANSFER_RECEIPT_CONTRACT}
        )
    )
    with pytest.raises(cs.ChunkStorageError, match="exact"):
        cs.read_transfer_receipt_view(tmp_path / "newshape_v1.json")
    # Tier-aware eligibility needs bindings taken from a /2 receipt: a complete mapping that does
    # not name the /2 contract -- what a legacy receipt or a hand-made record can offer -- refuses.
    placement = cs.ChunkPlacement(
        chunk_id="chunk-0000",
        state=cs.STATE_INTERNAL_RECLAIM_ELIGIBLE,
        internal_directory=source.directory,
        external_directory=dest / source.chunk_id,
        internal_receipt=None,
        external_receipt=object(),
        transfer_receipt=object(),
        internal_bytes=1,
        external_bytes=1,
        detail="synthetic",
    )  # type: ignore[arg-type]
    complete_but_unversioned = {
        name: f"synthetic-{name}" for name in ct.TRANSFER_RECEIPT_REQUIRED_BINDINGS
    }
    complete_but_unversioned.update(
        {
            "source_bytes": 10,
            "destination_bytes": 10,
            "destination_manifest_verified": True,
            "destination_content_verified": True,
            "transfer_outcome": "verified",
        }
    )
    unversioned = ct.reclaim_eligibility_with_tier(
        placement,
        transfer_record=complete_but_unversioned,
        external_root=dest,
        qualification=record,
    )
    assert (
        not unversioned.eligible and unversioned.proofs["transfer_receipt_is_verified_v2"] is False
    )
    legacy_bindings = ct.transfer_receipt_bindings_of(view)
    from_legacy = ct.reclaim_eligibility_with_tier(
        placement, transfer_record=legacy_bindings, external_root=dest, qualification=record
    )
    assert (
        not from_legacy.eligible and from_legacy.proofs["transfer_receipt_is_verified_v2"] is False
    )
    assert from_legacy.proofs["transfer_receipt_bindings_complete"] is False
    versioned = ct.reclaim_eligibility_with_tier(
        placement, transfer_record=verified.bindings(), external_root=dest, qualification=record
    )
    assert versioned.eligible and versioned.proofs["transfer_receipt_is_verified_v2"] is True
    assert verified.bindings()["receipt_contract"] == x.VERIFIED_TRANSFER_RECEIPT_CONTRACT


# ==========================================================================
# R5: integer, dynamic, pre-mutation admission -- P5, M12, M13
# ==========================================================================
def test_m13_admission_arithmetic_is_checked_integer_and_exact_at_the_boundary() -> None:
    required = x.external_transfer_requirement(
        source_bytes=10, partial_copy_overhead_bytes=3, evidence_overhead_bytes=2, reserve_bytes=5
    )
    assert required == 20
    assert x.require_external_admission(
        free_bytes=20,
        source_bytes=10,
        partial_copy_overhead_bytes=3,
        evidence_overhead_bytes=2,
        reserve_bytes=5,
    ).admitted
    assert x.require_external_admission(
        free_bytes=21,
        source_bytes=10,
        partial_copy_overhead_bytes=3,
        evidence_overhead_bytes=2,
        reserve_bytes=5,
    ).admitted
    with pytest.raises(x.ChunkTransferError, match="NOT ADMITTED"):
        x.require_external_admission(
            free_bytes=19,
            source_bytes=10,
            partial_copy_overhead_bytes=3,
            evidence_overhead_bytes=2,
            reserve_bytes=5,
        )
    for bad in (True, False, -1, 1.5, "10", None, 2**70 * -1):
        with pytest.raises(x.ChunkTransferError, match="non-negative integer"):
            x.require_count(bad, "term")
    with pytest.raises(x.ChunkTransferError):
        x.require_external_admission(
            free_bytes=True,
            source_bytes=0,
            partial_copy_overhead_bytes=0,
            evidence_overhead_bytes=0,
            reserve_bytes=0,
        )
    big = 2**80
    assert x.require_external_admission(
        free_bytes=big + 1,
        source_bytes=big,
        partial_copy_overhead_bytes=0,
        evidence_overhead_bytes=0,
        reserve_bytes=1,
    ).admitted
    # The internal representation: five checked terms, exact boundary, Boolean/float refused.
    requirement = cs.InternalStorageRequirement(
        next_chunk_peak_bytes=7,
        level_transient_bytes=3,
        reserve_bytes=2,
        retained_state_bytes=4,
        output_state_bytes=1,
    )
    assert requirement.required_free_bytes == 17
    assert cs.require_internal_admission(free_bytes=17, requirement=requirement).admitted
    with pytest.raises(cs.ChunkStorageError, match="NOT ADMITTED"):
        cs.require_internal_admission(free_bytes=16, requirement=requirement)
    for name in (
        "next_chunk_peak_bytes",
        "level_transient_bytes",
        "reserve_bytes",
        "retained_state_bytes",
        "output_state_bytes",
    ):
        for bad in (True, -1, 1.0):
            with pytest.raises(cs.ChunkStorageError):
                cs.InternalStorageRequirement(
                    **{
                        **{
                            "next_chunk_peak_bytes": 1,
                            "level_transient_bytes": 1,
                            "reserve_bytes": 1,
                            "retained_state_bytes": 1,
                            "output_state_bytes": 1,
                        },
                        name: bad,
                    }
                )
    with pytest.raises(cs.ChunkStorageError):
        cs.require_internal_admission(free_bytes=1.0, requirement=requirement)  # type: ignore[arg-type]


def test_m12_admission_is_measured_before_the_partial_destination_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    required = (
        source.total_bytes
        + source.receipt_bytes
        + x.allocation_overhead_bytes(source.entries, dest)
        + x.EVIDENCE_OVERHEAD_BYTES
        + 5
    )
    monkeypatch.setattr(x, "measured_free_bytes", lambda _path: required - 1)
    with pytest.raises(x.ChunkTransferError, match="NOT ADMITTED"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=5,
        )
    assert list(dest.iterdir()) == []  # nothing was created before admission
    monkeypatch.setattr(x, "measured_free_bytes", lambda _path: required)
    receipt = x.verified_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=5,
    )
    assert receipt.destination_bytes == source.total_bytes


def test_m13_enospc_is_an_error_and_never_control_flow(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)

    def out_of_space(*_args: Any, **_kwargs: Any) -> Any:
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(x, "_copy_one", out_of_space)
    with pytest.raises(OSError, match="No space"):
        x.verified_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=c22q.observation_for(record, dest),
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert not (dest / source.chunk_id).exists() and not list(
        dest.rglob(x.TRANSFER_RECEIPT_FILENAME)
    )


# ==========================================================================
# R7: states and recovery -- P7, M18
# ==========================================================================
def test_r7_every_state_is_derived_from_disk(tmp_path: Path) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)

    def state() -> x.TransferStateReport:
        return x.derive_transfer_state(
            destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
        )

    assert state().state == x.STATE_NOT_STARTED
    partial = dest / f"{source.chunk_id}{x.PARTIAL_SUFFIX}"
    partial.mkdir()
    (partial / "a.bin").write_bytes(b"alp")
    assert state().state == x.STATE_PARTIAL_COPY
    partial.rename(dest / source.chunk_id)
    assert state().state == x.STATE_FINAL_UNVERIFIED
    (dest / source.chunk_id / "a.bin").unlink()
    (dest / source.chunk_id).rmdir()
    receipt = x.verified_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=0,
    )
    assert state().state == x.STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE
    intent = x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    assert (
        intent.record_kind == x.RECLAIM_INTENT
        and intent.receipt_identity == receipt.receipt_identity
    )
    assert state().state == x.STATE_RECLAIM_INTENT_DURABLE
    (source.directory / "c.txt").unlink()  # an interrupted deletion
    assert state().state == x.STATE_RECLAIM_IN_PROGRESS
    completion = x.reclaim_source(
        authorization=TEST_RECLAIM,
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
    )
    assert completion.record_kind == x.RECLAIM_COMPLETE and completion.deleted_entries == len(
        intent.entries
    )
    assert not source.directory.exists()
    assert state().state == x.STATE_RECLAIM_COMPLETE
    reclaim_dir = dest / f"{source.chunk_id}{x.RECLAIM_DIRECTORY_SUFFIX}"
    assert (
        x.ReclaimRecord.from_document(
            json.loads((reclaim_dir / x.RECLAIM_COMPLETE_FILENAME).read_bytes())
        )
        == completion
    )
    # Conflicts refuse rather than resolve: a completion with the source present (M18), a
    # reclaim record without a receipt, a relabelled contract, a foreign receipt.
    source.directory.mkdir(parents=True)
    (source.directory / "a.bin").write_bytes(b"back")
    with pytest.raises(x.ChunkTransferError, match="still present"):
        state()


def test_m18_a_partial_or_interrupted_reclaim_is_never_complete_on_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    original = x._remove_exact_entries  # noqa: SLF001

    def interrupted(base: Path, files: Any) -> int:
        (base / "a.bin").unlink()  # one deletion, then the process dies
        raise KeyboardInterrupt

    monkeypatch.setattr(x, "_remove_exact_entries", interrupted)
    with pytest.raises(KeyboardInterrupt):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    monkeypatch.setattr(x, "_remove_exact_entries", original)
    report = x.derive_transfer_state(
        destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
    )
    assert report.state == x.STATE_RECLAIM_IN_PROGRESS and report.completion is None
    assert not (
        dest / f"{source.chunk_id}{x.RECLAIM_DIRECTORY_SUFFIX}" / x.RECLAIM_COMPLETE_FILENAME
    ).exists()
    # The exact remaining subset resumes; an unexpected entry refuses the resumption.
    (source.directory / "stray").write_bytes(b"?")
    with pytest.raises(x.ChunkTransferError, match="outside the reclaim intent"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    (source.directory / "stray").unlink()
    completion = x.reclaim_source(
        authorization=TEST_RECLAIM,
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
    )
    assert completion.record_kind == x.RECLAIM_COMPLETE and not source.directory.exists()


def test_r7_recovery_from_a_partial_copy_removes_only_its_own_partial(tmp_path: Path) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    partial = dest / f"{source.chunk_id}{x.PARTIAL_SUFFIX}"
    (partial / "sub").mkdir(parents=True)
    (partial / "a.bin").write_bytes(b"truncated")
    (partial / "sub" / "b.bin").write_bytes(b"")
    receipt = x.recover_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=0,
    )
    assert receipt.recovered_from_state == x.STATE_PARTIAL_COPY and not partial.exists()
    assert (
        x.derive_transfer_state(
            destination_root=dest, chunk_id=source.chunk_id, source_directory=source.directory
        ).state
        == x.STATE_TRANSFER_VERIFIED_RECEIPT_DURABLE
    )
    # A partial holding an object outside this source's manifest is not this transfer's own.
    other = make_source(tmp_path / "other", chunk_id="chunk-0001")
    partial = dest / f"{other.chunk_id}{x.PARTIAL_SUFFIX}"
    partial.mkdir()
    (partial / "not-ours.bin").write_bytes(b"?")
    with pytest.raises(x.ChunkTransferError, match="outside the exact entry list"):
        x.recover_transfer(
            source=other,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert (partial / "not-ours.bin").exists()


def test_r7_an_unreceipted_final_destination_is_reverified_before_any_receipt(
    tmp_path: Path,
) -> None:
    source = make_source(tmp_path)
    record = c22q.qualification()
    dest = destination(tmp_path)
    observation = c22q.observation_for(record, dest)
    final = dest / source.chunk_id
    for entry in source.entries:
        (final / entry.relative_path).parent.mkdir(parents=True, exist_ok=True)
        (final / entry.relative_path).write_bytes(
            (source.directory / entry.relative_path).read_bytes()
        )
    (final / x.SOURCE_RECEIPT_FILENAME).write_bytes(
        (source.directory / x.SOURCE_RECEIPT_FILENAME).read_bytes()
    )
    # A changed destination byte refuses and no receipt appears.
    (final / "c.txt").write_bytes(b"CHARLIE")
    with pytest.raises(x.ChunkTransferError, match="read back as"):
        x.recover_transfer(
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert not (final / x.TRANSFER_RECEIPT_FILENAME).exists()
    (final / "c.txt").write_bytes(b"charlie")
    receipt = x.recover_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=0,
    )
    assert receipt.recovered_from_state == x.STATE_FINAL_UNVERIFIED
    assert (final / x.TRANSFER_RECEIPT_FILENAME).exists()
    # Idempotent: the same source and tier get the same receipt back and no duplicate is written.
    before = (final / x.TRANSFER_RECEIPT_FILENAME).read_bytes()
    again = x.recover_transfer(
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
        authorization=TEST_TRANSFER,
        external_reserve_bytes=0,
    )
    assert again == receipt and (final / x.TRANSFER_RECEIPT_FILENAME).read_bytes() == before
    # A conflicting receipt -- another qualification -- refuses and is never replaced.
    other = c22q.qualification(klass=q.CLASS_COPY_ONLY)
    with pytest.raises(x.ChunkTransferError, match="disagrees"):
        x.recover_transfer(
            source=source,
            destination_root=dest,
            qualification=other,
            observation=c22q.observation_for(other, dest),
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )
    assert (final / x.TRANSFER_RECEIPT_FILENAME).read_bytes() == before
    # A receipt whose destination went missing or conflicts refuses on every later step: no
    # intent may be written over it, and no deletion is ever reached.
    (final / "a.bin").write_bytes(b"gone wrong")
    with pytest.raises(x.ChunkTransferError, match="not eligible"):
        x.write_reclaim_intent(
            source=source, destination_root=dest, qualification=record, observation=observation
        )
    with pytest.raises(x.ChunkTransferError, match="no durable reclaim intent"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert (source.directory / "a.bin").exists()


# ==========================================================================
# R4: reclaim separation -- P4, M7, M8, M9, M10, M11
# ==========================================================================
def test_m7_a_transfer_never_implies_a_reclaim_and_the_real_authority_refuses_first(
    tmp_path: Path,
) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    before = _files(source.directory)
    with pytest.raises(x.ChunkTransferError, match="reclaim authorization"):
        x.reclaim_source(
            authorization=None,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    with pytest.raises(x.ChunkTransferError, match="reclaim authorization"):
        x.reclaim_source(
            authorization=TEST_TRANSFER,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )  # a transfer authorization is not one
    with pytest.raises(x.ChunkTransferError, match="reclaim authorization"):
        x.reclaim_source(
            authorization=receipt,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )  # nor is the receipt
    assert cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.authorize_internal_reclaim()
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.reclaim_transferred_chunk(
            chunk_root=tmp_path,
            chunk_id=source.chunk_id,
            destination_root=dest,
            qualification=record,
            provider=lambda _p: 1 / 0,
        )
    assert _files(source.directory) == before
    assert not (dest / f"{source.chunk_id}{x.RECLAIM_DIRECTORY_SUFFIX}").exists()


def test_m8_the_first_deletion_never_precedes_a_durable_intent(tmp_path: Path) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    before = _files(source.directory)
    with pytest.raises(x.ChunkTransferError, match="no durable reclaim intent"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert _files(source.directory) == before
    intent = x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    stored = json.loads(
        (
            dest / f"{source.chunk_id}{x.RECLAIM_DIRECTORY_SUFFIX}" / x.RECLAIM_INTENT_FILENAME
        ).read_bytes()
    )
    assert (
        stored["record_kind"] == "reclaim_intent"
        and stored["contract"] == "m3.3-chunked-f0-reclaim-record/1"
    )
    assert set(stored) == x.RECLAIM_RECORD_FIELDS and stored["completed_at_utc"] is None
    assert (
        tuple(stored["entries"])
        == intent.entries
        == tuple(sorted([e.relative_path for e in source.entries] + [x.SOURCE_RECEIPT_FILENAME]))
    )
    with pytest.raises(x.ChunkTransferError, match="already exists"):
        x.write_reclaim_intent(
            source=source, destination_root=dest, qualification=record, observation=observation
        )
    assert _files(source.directory) == before  # the intent deleted nothing


def test_m9_deletion_is_exact_entry_never_recursive(tmp_path: Path) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    (source.directory / "sub" / "unexpected.bin").write_bytes(b"not in the intent")
    with pytest.raises(x.ChunkTransferError, match="outside the reclaim intent"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert (source.directory / "sub" / "unexpected.bin").exists() and (
        source.directory / "a.bin"
    ).exists()
    (source.directory / "sub" / "unexpected.bin").unlink()
    (source.directory / "catalog.sqlite3-shm").write_bytes(b"")
    with pytest.raises(x.ChunkTransferError, match="outside the reclaim intent"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    (source.directory / "catalog.sqlite3-shm").unlink()
    source_text = Path(x.__file__).read_text(encoding="utf-8")
    assert "rmtree" not in source_text and "shutil" not in source_text
    completion = x.reclaim_source(
        authorization=TEST_RECLAIM,
        source=source,
        destination_root=dest,
        qualification=record,
        observation=observation,
    )
    assert completion.deleted_entries == 4 and completion.reconciled in (True, False)
    assert completion.free_before_bytes is not None and completion.free_after_bytes is not None
    assert not source.directory.exists() and source.directory.parent.exists()


def test_m10_the_destination_is_revalidated_immediately_before_deletion(tmp_path: Path) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    target = dest / source.chunk_id / "a.bin"
    data = bytearray(target.read_bytes())
    data[5] ^= 0xFF
    target.write_bytes(bytes(data))
    before = _files(source.directory)
    with pytest.raises(x.ChunkTransferError, match="read back as"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert _files(source.directory) == before
    eligibility = x.reclaim_eligibility(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    assert not eligibility.eligible and eligibility.proofs["destination_fully_reread"] is False


def test_m11_a_copy_only_tier_refuses_reclaim_before_eligibility(tmp_path: Path) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path, klass=q.CLASS_COPY_ONLY)
    assert receipt.qualification_class == q.CLASS_COPY_ONLY
    eligibility = x.reclaim_eligibility(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    assert not eligibility.eligible and eligibility.proofs["qualification_reclaim_capable"] is False
    assert all(
        value
        for name, value in eligibility.proofs.items()
        if name != "qualification_reclaim_capable"
    )
    with pytest.raises(q.HostASsdQualificationError, match="only RECLAIM_CAPABLE"):
        x.write_reclaim_intent(
            source=source, destination_root=dest, qualification=record, observation=observation
        )
    with pytest.raises(q.HostASsdQualificationError, match="only RECLAIM_CAPABLE"):
        x.reclaim_source(
            authorization=TEST_RECLAIM,
            source=source,
            destination_root=dest,
            qualification=record,
            observation=observation,
        )
    assert (source.directory / "a.bin").exists()
    failed = c22q.qualification(klass=q.CLASS_FAIL, reconnect="not_run")
    with pytest.raises(q.HostASsdQualificationError, match="class FAIL"):
        x.verified_transfer(
            source=make_source(tmp_path / "f"),
            destination_root=dest,
            qualification=failed,
            observation=c22q.observation_for(failed, dest),
            authorization=TEST_TRANSFER,
            external_reserve_bytes=0,
        )


def test_r4_eligibility_is_a_pure_predicate_with_every_proof(tmp_path: Path) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    eligibility = x.reclaim_eligibility(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    assert eligibility.eligible and set(eligibility.proofs) == {
        "transfer_receipt_valid",
        "tier_reauthenticated_now",
        "destination_fully_reread",
        "source_manifest_exact",
        "source_immutable_terminal",
        "qualification_reclaim_capable",
    }
    assert _files(source.directory)  # computed, never acted on
    elsewhere = c22q.observation_for(record, dest, st_dev=observation.attachment["st_dev"] + 1)
    assert (
        x.reclaim_eligibility(
            source=source, destination_root=dest, qualification=record, observation=elsewhere
        ).proofs["tier_reauthenticated_now"]
        is False
    )
    (source.directory / "c.txt").write_bytes(b"CHANGED")
    assert (
        x.reclaim_eligibility(
            source=source, destination_root=dest, qualification=record, observation=observation
        ).proofs["source_manifest_exact"]
        is False
    )


def test_the_reclaim_record_is_exact_and_an_intent_never_carries_measurements(
    tmp_path: Path,
) -> None:
    receipt, source, record, observation, dest = run_transfer(tmp_path)
    intent = x.write_reclaim_intent(
        source=source, destination_root=dest, qualification=record, observation=observation
    )
    stored = dict(intent.as_record())
    for _label, edit in (
        ("/2", lambda r: r.__setitem__("contract", x.RECLAIM_RECORD_CONTRACT[:-1] + "2")),
        ("unknown kind", lambda r: r.__setitem__("record_kind", "reclaim_started")),
        ("intent with a measurement", lambda r: r.__setitem__("freed_bytes", 0)),
        ("missing field", lambda r: r.pop("entries")),
        ("extra field", lambda r: r.__setitem__("force", True)),
        ("unsorted entries", lambda r: r.__setitem__("entries", list(reversed(r["entries"])))),
    ):
        edited = dict(stored)
        edit(edited)
        with pytest.raises(x.ChunkTransferError):
            x.ReclaimRecord.from_document(edited)
    relabelled = dict(stored)
    relabelled["record_kind"] = x.RECLAIM_COMPLETE  # a relabelled intent is not a completion
    with pytest.raises(x.ChunkTransferError):
        x.ReclaimRecord.from_document(relabelled)


# ==========================================================================
# R6: nonperturbing instrumentation -- P6, M14, M15
# ==========================================================================
def test_m14_m15_the_ledger_is_stat_only_and_every_sample_is_complete(tmp_path: Path) -> None:
    world = tmp_path / "world"
    world.mkdir()
    database = world / "working_catalog.sqlite3"
    wal = world / "working_catalog.sqlite3-wal"
    database.write_bytes(b"not a database, and never opened as one" * 100)
    wal.write_bytes(b"w" * 4096)
    before = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in world.iterdir()}
    with pytest.raises(x.ChunkTransferError, match="outside the active world"):
        x.InstrumentationLedger(
            world / "telemetry.jsonl", internal_path=tmp_path, charged_directory=world
        )
    ledger = x.InstrumentationLedger(
        tmp_path / "telemetry.jsonl",
        internal_path=tmp_path,
        external_path=tmp_path,
        temp_root=tmp_path,
        charged_directory=world,
        qualification_identity="q" * 64,
        tier_identity="t" * 64,
    )
    with pytest.raises(x.ChunkTransferError, match="unknown|outside the required"):
        ledger.sample("bad", surprise=1)
    with ledger.watch(wal_path=wal, interval_seconds=0.05):
        wal.write_bytes(b"w" * 65536)
        ledger.record_transfer(
            bytes_copied=10, copy_seconds=1.0, bytes_read_back=10, read_seconds=0.5
        )
        ledger.record_sizes(retained_input_bytes=7, output_bytes=3)
        with pytest.raises(x.ChunkTransferError, match="still open"):
            ledger.require_complete()
        ledger.sample("copy", wal_path=wal)
    ledger.record_child_exit(parent_rss_before=300, parent_rss_after=100)
    ledger.sample("child_exit", wal_path=wal)
    assert ledger.require_complete() == 2
    lines = (tmp_path / "telemetry.jsonl").read_bytes().decode().splitlines()
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        assert list(record) == sorted(x.SAMPLE_FIELDS) and set(record) == set(x.SAMPLE_FIELDS)
        assert record["pid"] == os.getpid() and record["qualification_identity"] == "q" * 64
        assert record["wal_high_water_bytes"] == 65536
        assert isinstance(record["internal_free_bytes"], int) and isinstance(
            record["internal_low_water_bytes"], int
        )
    last = json.loads(lines[-1])
    assert (
        last["process_exit_rss_reclaimed_bytes"] == 200
        and last["bytes_copied"] == 10
        and last["output_bytes"] == 3
    )
    assert last["copy_bytes_per_second"] == 10 and last["read_bytes_per_second"] == 20
    after = {p.name: (p.stat().st_size, p.stat().st_mtime_ns) for p in world.iterdir()}
    assert after == {**before, wal.name: (65536, after[wal.name][1])}
    assert database.stat().st_mtime_ns == before[database.name][1]
    module = Path(x.__file__).read_text(encoding="utf-8")
    assert "sqlite3" not in module and "connect(" not in module
    assert (tmp_path / "telemetry.jsonl").parent == tmp_path  # outside the world


def test_m15_a_child_that_ends_without_final_metrics_is_visible(tmp_path: Path) -> None:
    ledger = x.InstrumentationLedger(tmp_path / "t.jsonl", internal_path=tmp_path)
    ledger.sample("merge_started:group-0000")
    # No child_exit sample, no exit accounting: the record shows it.
    lines = [json.loads(line) for line in (tmp_path / "t.jsonl").read_bytes().decode().splitlines()]
    assert [line["phase"] for line in lines] == ["merge_started:group-0000"]
    assert lines[0]["process_exit_rss_reclaimed_bytes"] is None
    ledger.record_child_exit(parent_rss_before=5, parent_rss_after=None)
    assert ledger.sample("merge_child_exit:group-0000")["process_exit_rss_reclaimed_bytes"] is None


# ==========================================================================
# The family-facing layer: authority first, terminal source, tier mapping -- R4, R8
# ==========================================================================
def test_r8_the_family_entry_points_refuse_on_authority_before_touching_the_tier(
    tmp_path: Path,
) -> None:
    record = c22q.qualification()
    touched: list[Path] = []

    def provider(path: Path) -> Any:
        touched.append(path)
        message = "the tier was consulted before the authority"
        raise AssertionError(message)

    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None and cs.REAL_INTERNAL_RECLAIM_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.transfer_completed_chunk(
            chunk_root=tmp_path,
            chunk_id="chunk-0000",
            destination_root=tmp_path,
            qualification=record,
            external_reserve_bytes=0,
            provider=provider,
        )
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.reclaim_transferred_chunk(
            chunk_root=tmp_path,
            chunk_id="chunk-0000",
            destination_root=tmp_path,
            qualification=record,
            provider=provider,
        )
    assert touched == []
    with pytest.raises(cs.ChunkStorageError, match="NOT AUTHORIZED"):
        cs.authorize_chunk_transfer()
    # An opened constant grants an authorization naming the constant, and nothing else.
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setattr(cs, "REAL_CHUNK_TRANSFER_AUTHORITY", "granted-in-test")
        grant = cs.authorize_chunk_transfer()
        assert grant == x.TransferAuthorization(
            grant="granted-in-test",
            granted_by="REAL_CHUNK_TRANSFER_AUTHORITY",
        )
    assert cs.REAL_CHUNK_TRANSFER_AUTHORITY is None
    with pytest.raises(cs.ChunkStorageError, match="no valid terminal receipt"):
        cs.transfer_source_of(tmp_path, "chunk-0000")


def test_the_tier_derives_from_the_record_and_copy_only_is_never_reclaim_capable() -> None:
    record = c22q.qualification(klass=q.CLASS_COPY_ONLY)
    tier = ct.external_tier_from_qualification(record, qualified_by="test")
    assert tier.volume_identity == c22q.VOLUME and tier.filesystem == "exfat"
    assert tier.physical_topology == "DIRECT_USB" and tier.round_trip_verified is True
    assert tier.mount_identity == record.stable_tier_compatibility_identity
    assert tier.sustained_copy_bytes_per_second == int(400.0 * (1 << 20))
    assert tier.sustained_read_bytes_per_second == int(585.0 * (1 << 20))
    assert not ct.external_tier_is_qualified(tier) and ct.QUALIFIED_EXTERNAL_TIER is None
    with pytest.raises(ct.ChunkTieringError, match="class FAIL"):
        ct.external_tier_from_qualification(
            c22q.qualification(klass=q.CLASS_FAIL, reconnect="not_run"), qualified_by="test"
        )
    with pytest.raises(ct.ChunkTieringError, match="physical reconnect"):
        ct.external_tier_from_qualification(
            c22q.qualification(reconnect="not_run"), qualified_by="test"
        )
    assert ct.reclaim_eligibility_with_tier.__doc__ is not None
