"""D151-C22: Host-A / direct-SSD qualification records and tier reauthentication -- R2, P1, P2.

Every record here is synthetic: no test depends on the operator's SSD, on the private evidence
root, or on the sealed Phase-A record. The exact-shape parser, the two sealed identities, the
direct-topology classification, the stable-versus-attachment distinction, the fail-closed
admissibility of FAIL and reconnect-absent records, and the exact capability envelope of the two
new production modules are proved over disposable fixtures.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d151_c13_intermediates as c13i  # noqa: E402

from disclosure_drift.m3 import chunk_transfer as x  # noqa: E402
from disclosure_drift.m3 import host_a_ssd_qualification as q  # noqa: E402

VOLUME = "397A4D4A-0000-4000-8000-00000000C22A"
OTHER_VOLUME = "397A4D4A-0000-4000-8000-00000000C22B"
CHUNK_FAMILY = (
    "chunk_plan",
    "chunk_evidence",
    "chunk_execution",
    "chunk_storage",
    "chunk_consolidation",
    "chunk_multipass",
    "chunk_tiering",
)


def _hex(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def compatibility_record(**overrides: object) -> dict[str, Any]:
    record: dict[str, Any] = {
        "architecture": "arm64",
        "enclosure_identity_hash": _hex("enclosure"),
        "filesystem_type": "exfat",
        "host_identity_hash": _hex("host"),
        "host_model": "MacBookPro17,1",
        "media_serial_hash": _hex("serial"),
        "media_size_bytes": 500_107_862_016,
        "topology_class": q.TOPOLOGY_DIRECT_USB,
        "volume_total_bytes": 499_955_924_992,
        "volume_uuid": VOLUME,
    }
    record.update(overrides)
    return record


def qualification_document(
    *,
    klass: str = q.CLASS_RECLAIM_CAPABLE,
    reconnect: str = q.RECONNECT_COMPLETED,
    compat: dict[str, Any] | None = None,
    predicates: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """A complete, sealed, synthetic qualification document of the Phase-A shape."""
    compat = compatibility_record() if compat is None else compat
    reconnect_ran = reconnect == q.RECONNECT_COMPLETED
    preds: dict[str, bool] = {
        "every_size_and_sha256_exact": True,
        "file_fsync_succeeded": True,
        "file_fullfsync_succeeded": klass != q.CLASS_FAIL,
        "parent_directory_durability_established": klass == q.CLASS_RECLAIM_CAPABLE,
        "first_readback_at_least_250_mib_s": klass != q.CLASS_FAIL,
        "mean_write_fsync_complete_at_least_300_mib_s": klass != q.CLASS_FAIL,
        "no_zero_progress_interval_over_15_s": True,
        "topology_direct": compat["topology_class"] == q.TOPOLOGY_DIRECT_USB,
        "transport_stable_no_detach_reset_or_remount": True,
        "reconnect_stable_identity_unchanged": reconnect_ran,
        "reconnect_manifest_exact": reconnect_ran,
        "reconnect_topology_direct": reconnect_ran,
        "reconnect_readback_at_least_250_mib_s": reconnect_ran,
        "reconnect_stage_completed": reconnect_ran,
    }
    if predicates:
        preds.update(predicates)
    document: dict[str, Any] = {
        "contract": q.QUALIFICATION_CONTRACT,
        "record_kind": q.QUALIFICATION_RECORD_KIND,
        "qualification_run_id": "a8ab8881e1c4b7fa",
        "started_utc": "2026-08-28T11:41:00Z",
        "ended_utc": "2026-08-28T12:11:00Z",
        "host": {
            "model": compat["host_model"],
            "architecture": compat["architecture"],
            "host_identity_hash": compat["host_identity_hash"],
            "chip": "Apple M1",
        },
        "transport": {"before_reconnect": {"topology_class": compat["topology_class"]}},
        "stable_media_identity": {
            "media_serial_hash": compat["media_serial_hash"],
            "media_size_bytes": compat["media_size_bytes"],
            "enclosure_identity_hash": compat["enclosure_identity_hash"],
            "volume_uuid": compat["volume_uuid"],
            "filesystem_type": compat["filesystem_type"],
            "volume_total_bytes": compat["volume_total_bytes"],
            "topology_class": compat["topology_class"],
        },
        "attachment_observations": {"before_reconnect": {"whole_disk": "disk4"}},
        "capacity": {"external_free_before_copy_bytes": 246_725_607_424},
        "power_observations": [{"stage": "start", "battery_percent": 100}],
        "operator_checkpoints": [{"checkpoint": 1}],
        "push_notification_capability": "available",
        "payload": {"manifest_sha256": _hex("payload"), "total_bytes": 25_769_812_534},
        "metrics": {
            "write": {"mean_write_fsync_complete_mib_per_s": 400.0},
            "first_readback": {"mean_first_readback_mib_per_s": 580.0},
            "reconnect_readback": (
                {"mean_mib_per_s": 585.0} if reconnect_ran else {"status": "not_run"}
            ),
        },
        "durability": {"file_fsync": "succeeded"},
        "unmount_characterization": {"outcome": "refused_busy"},
        "cleanup": {"ssd_namespace_absent": True},
        "quiescence_before_checkpoint_1": {"governed_processes": []},
        "reconnect_checkpoint": {"status": reconnect},
        "predicates": preds,
        "qualification_class": klass,
        q.STABLE_TIER_COMPATIBILITY_KEY: dict(compat),
    }
    return seal(document)


def seal(document: dict[str, Any]) -> dict[str, Any]:
    """Recompute both identities over the (edited) document."""
    document.pop(q.QUALIFICATION_IDENTITY_KEY, None)
    compat = document[q.STABLE_TIER_COMPATIBILITY_KEY]
    document[q.STABLE_TIER_COMPATIBILITY_IDENTITY_KEY] = hashlib.sha256(
        q.canonical_json_bytes(compat)
    ).hexdigest()
    document[q.QUALIFICATION_IDENTITY_KEY] = q.sealed_identity(
        document, identity_key=q.QUALIFICATION_IDENTITY_KEY
    )
    return document


def write_record(path: Path, document: dict[str, Any]) -> Path:
    path.write_bytes(q.canonical_json_bytes(document))
    return path


def qualification(**kwargs: Any) -> q.HostASsdQualification:
    return q.HostASsdQualification.from_document(qualification_document(**kwargs))


def observation_for(
    record: q.HostASsdQualification, path: Path, **attachment: object
) -> q.LiveTierObservation:
    """A live observation of the qualified tier, hosted on ``path``'s filesystem."""
    st = path.stat()
    fields: dict[str, object] = {
        "device_node": "/dev/disk4s2",
        "location_id": 18874368,
        "partition": "disk4s2",
        "partition_uuid": "411E4166-1A78-4B2B-BB75-9AFB9239C42B",
        "session_id": 14635592949514,
        "st_dev": st.st_dev,
        "st_ino": st.st_ino,
        "usb_address": 1,
        "whole_disk": "disk4",
    }
    fields.update(attachment)
    return q.LiveTierObservation(stable=record.stable_tier_compatibility, attachment=fields)


def provider_for(record: q.HostASsdQualification, **attachment: object) -> Any:
    def provide(path: Path) -> q.LiveTierObservation:
        return observation_for(record, path, **attachment)

    return provide


# ==========================================================================
# Canonical form, exact parse, sealed identities -- packet §4, M17
# ==========================================================================
def test_canonical_form_is_sorted_compact_utf8_with_one_trailing_newline() -> None:
    payload = q.canonical_json_bytes({"b": 1, "a": [1, 2.5, "é"]})
    assert payload == '{"a":[1,2.5,"é"],"b":1}\n'.encode()
    with pytest.raises(q.HostASsdQualificationError, match="JSON object"):
        q.canonical_json_bytes(["not", "an", "object"])  # type: ignore[arg-type]
    with pytest.raises(q.HostASsdQualificationError, match="canonically"):
        q.canonical_json_bytes({"nan": float("nan")})


def test_a_sealed_record_parses_exactly_and_round_trips_from_its_file(tmp_path: Path) -> None:
    document = qualification_document()
    record = q.HostASsdQualification.from_document(document)
    assert record.contract == q.QUALIFICATION_CONTRACT
    assert record.qualification_class == q.CLASS_RECLAIM_CAPABLE
    assert record.stable_tier_compatibility.volume_uuid == VOLUME
    assert (
        record.stable_tier_compatibility_identity == document["stable_tier_compatibility_identity"]
    )
    assert record.qualification_identity == document["qualification_identity"]
    assert record.physical_reconnect_qualified and record.admits_verified_copy
    assert record.admits_reclaim
    path = write_record(tmp_path / q.QUALIFICATION_FILENAME, document)
    assert q.HostASsdQualification.from_path(path) == record
    # A re-serialized (non-canonical) file is refused even though its content is identical.
    (tmp_path / "pretty.json").write_text(json.dumps(document, indent=2))
    with pytest.raises(q.HostASsdQualificationError, match="byte-canonical"):
        q.HostASsdQualification.from_path(tmp_path / "pretty.json")
    with pytest.raises(q.HostASsdQualificationError, match="no qualification record"):
        q.HostASsdQualification.from_path(tmp_path / "absent.json")


@pytest.mark.parametrize(
    ("label", "edit"),
    [
        ("a missing top-level key", lambda d: d.pop("durability")),
        ("an extra top-level key", lambda d: d.__setitem__("legacy_alias", True)),
        ("a /2 contract", lambda d: d.__setitem__("contract", q.QUALIFICATION_CONTRACT[:-1] + "2")),
        ("a /0 contract", lambda d: d.__setitem__("contract", q.QUALIFICATION_CONTRACT[:-1] + "0")),
        ("another record kind", lambda d: d.__setitem__("record_kind", "ssd_qualification")),
        ("an unknown class", lambda d: d.__setitem__("qualification_class", "PASS")),
        ("a non-Boolean predicate", lambda d: d["predicates"].__setitem__("topology_direct", 1)),
        ("a run id that is not hex16", lambda d: d.__setitem__("qualification_run_id", "run-1")),
        ("a list where an object is required", lambda d: d.__setitem__("host", [])),
        ("an object where a list is required", lambda d: d.__setitem__("power_observations", {})),
    ],
)
def test_m17_exact_shape_refusals_and_no_upgrade(label: str, edit: Any) -> None:
    document = qualification_document()
    edit(document)
    seal(document)  # resealed on purpose: the SHAPE is what refuses, not a stale identity
    with pytest.raises(q.HostASsdQualificationError):
        q.HostASsdQualification.from_document(document)


def test_m17_a_relabelled_class_without_resealing_is_a_stale_seal() -> None:
    document = qualification_document(klass=q.CLASS_FAIL)
    document["qualification_class"] = q.CLASS_RECLAIM_CAPABLE  # relabelled, not resealed
    with pytest.raises(q.HostASsdQualificationError, match="does not seal the document"):
        q.HostASsdQualification.from_document(document)
    document["predicates"]["file_fullfsync_succeeded"] = True
    document["predicates"]["parent_directory_durability_established"] = True
    seal(document)
    # Resealed, the relabel is a different record with a different identity, and it is exact.
    assert q.HostASsdQualification.from_document(document).qualification_class == "RECLAIM_CAPABLE"


def test_m1_the_stable_compatibility_record_is_exactly_ten_typed_fields() -> None:
    for missing in q.STABLE_TIER_COMPATIBILITY_FIELDS:
        compat = compatibility_record()
        compat.pop(missing)
        with pytest.raises(q.HostASsdQualificationError, match="exact"):
            q.StableTierCompatibility.from_record(compat)
    with pytest.raises(q.HostASsdQualificationError, match="exact"):
        q.StableTierCompatibility.from_record({**compatibility_record(), "mount_path": "/x"})
    for name, value in (
        ("media_size_bytes", True),
        ("media_size_bytes", 1.5),
        ("volume_total_bytes", -1),
        ("volume_uuid", ""),
        ("media_serial_hash", "abc"),
        ("filesystem_type", "ntfs"),
    ):
        with pytest.raises(q.HostASsdQualificationError):
            q.StableTierCompatibility.from_record(compatibility_record(**{name: value}))


def test_m1_every_stable_field_moves_the_compatibility_identity_and_the_seal() -> None:
    base = q.StableTierCompatibility.from_record(compatibility_record())
    seen = {base.identity()}
    moved = {
        "architecture": "x86_64",
        "enclosure_identity_hash": _hex("other-enclosure"),
        "filesystem_type": "apfs",
        "host_identity_hash": _hex("other-host"),
        "host_model": "MacBookPro18,3",
        "media_serial_hash": _hex("other-serial"),
        "media_size_bytes": base.media_size_bytes + 1,
        "topology_class": q.TOPOLOGY_NOT_DIRECT,
        "volume_total_bytes": base.volume_total_bytes + 1,
        "volume_uuid": OTHER_VOLUME,
    }
    assert set(moved) == set(q.STABLE_TIER_COMPATIBILITY_FIELDS)
    for name, value in moved.items():
        other = q.StableTierCompatibility.from_record(compatibility_record(**{name: value}))
        assert other.identity() not in seen, name
        seen.add(other.identity())
        assert other.differences(base) == (name,)
    # The compatibility record inside a document must agree with the sections it summarizes,
    # and the document identity moves with any field of the document.
    document = qualification_document()
    document[q.STABLE_TIER_COMPATIBILITY_KEY]["volume_uuid"] = OTHER_VOLUME
    seal(document)
    with pytest.raises(q.HostASsdQualificationError, match="disagrees"):
        q.HostASsdQualification.from_document(document)
    edited = qualification_document()
    identity = edited["qualification_identity"]
    edited["capacity"]["external_free_before_copy_bytes"] += 1
    assert seal(edited)["qualification_identity"] != identity


# ==========================================================================
# Fail-closed admissibility -- §7, R8, owner direction
# ==========================================================================
def test_a_fail_record_admits_nothing_and_is_never_relabelled() -> None:
    record = qualification(klass=q.CLASS_FAIL, reconnect="not_run")
    assert not record.admits_verified_copy and not record.admits_reclaim
    with pytest.raises(q.HostASsdQualificationError, match="class FAIL"):
        q.require_copy_capable(record)
    with pytest.raises(q.HostASsdQualificationError, match="class FAIL"):
        q.require_reclaim_capable(record)
    with pytest.raises(q.HostASsdQualificationError, match="class FAIL"):
        q.reauthenticate_qualified_tier(record, Path("/"), provider=lambda _p: 1 / 0)


def test_an_absent_physical_reconnect_qualification_admits_nothing() -> None:
    record = qualification(klass=q.CLASS_RECLAIM_CAPABLE, reconnect="not_run")
    assert not record.physical_reconnect_qualified
    with pytest.raises(q.HostASsdQualificationError, match="physical reconnect"):
        q.require_copy_capable(record)
    partial = qualification(predicates={"reconnect_manifest_exact": False})
    with pytest.raises(q.HostASsdQualificationError, match="physical reconnect"):
        q.require_copy_capable(partial)


def test_c24_r1_reconnect_status_is_an_independent_conjunct() -> None:
    """D151-C24-R1, closing C23-MINOR-3: the reconnect status decides on its own.

    The records above move the status and the four reconnect predicates together, so every one
    of them would still refuse if ``physical_reconnect_qualified`` stopped consulting the status
    at all. This record separates them: it is the admitted RECLAIM_CAPABLE record in every
    field -- all four reconnect predicates True, the reconnect read-back rate present -- except
    that the checkpoint the operator acknowledges never completed. A record may claim the
    reconnect happened in every derived predicate; only the checkpoint says that it did.
    """
    document = qualification_document(klass=q.CLASS_RECLAIM_CAPABLE)
    document["reconnect_checkpoint"] = {"status": "not_run"}
    hostile = q.HostASsdQualification.from_document(seal(document))

    # Everything except the checkpoint says the stage ran, and the record is exactly shaped,
    # correctly sealed and parsed: the refusal below is not a stale seal or a malformed file.
    assert hostile.reconnect_status == "not_run"
    assert hostile.qualification_class == q.CLASS_RECLAIM_CAPABLE
    assert [
        hostile.predicates[name]
        for name in (
            "reconnect_stable_identity_unchanged",
            "reconnect_manifest_exact",
            "reconnect_topology_direct",
            "reconnect_readback_at_least_250_mib_s",
        )
    ] == [True, True, True, True]
    metrics = hostile.document["metrics"]
    assert isinstance(metrics, dict)
    assert metrics["reconnect_readback"] == {"mean_mib_per_s": 585.0}
    assert hostile.qualification_identity == q.sealed_identity(
        hostile.document, identity_key=q.QUALIFICATION_IDENTITY_KEY
    )
    assert (
        hostile.stable_tier_compatibility_identity == hostile.stable_tier_compatibility.identity()
    )

    # And it still admits nothing.
    assert hostile.physical_reconnect_qualified is False
    assert hostile.admits_verified_copy is False
    assert hostile.admits_reclaim is False
    with pytest.raises(q.HostASsdQualificationError, match="physical reconnect"):
        q.require_copy_capable(hostile)
    with pytest.raises(q.HostASsdQualificationError, match="physical reconnect"):
        q.require_reclaim_capable(hostile)
    with pytest.raises(q.HostASsdQualificationError, match="physical reconnect"):
        q.reauthenticate_qualified_tier(hostile, Path("/"), provider=lambda _p: 1 / 0)

    # The control that isolates the cause: the same document with the checkpoint restored --
    # nothing else edited -- parses, qualifies and admits a reclaim.
    document["reconnect_checkpoint"] = {"status": q.RECONNECT_COMPLETED}
    admitted = q.HostASsdQualification.from_document(seal(document))
    assert admitted.physical_reconnect_qualified is True
    assert q.require_reclaim_capable(admitted) is admitted
    assert {
        key: value
        for key, value in admitted.document.items()
        if key not in ("reconnect_checkpoint", q.QUALIFICATION_IDENTITY_KEY)
    } == {
        key: value
        for key, value in hostile.document.items()
        if key not in ("reconnect_checkpoint", q.QUALIFICATION_IDENTITY_KEY)
    }


def test_copy_only_admits_a_copy_and_never_a_reclaim() -> None:
    record = qualification(klass=q.CLASS_COPY_ONLY)
    assert record.admits_verified_copy and not record.admits_reclaim
    assert q.require_copy_capable(record) is record
    with pytest.raises(q.HostASsdQualificationError, match="only RECLAIM_CAPABLE"):
        q.require_reclaim_capable(record)


def test_a_non_direct_topology_admits_no_copy() -> None:
    record = qualification(compat=compatibility_record(topology_class=q.TOPOLOGY_NOT_DIRECT))
    with pytest.raises(q.HostASsdQualificationError, match="direct"):
        q.require_copy_capable(record)


# ==========================================================================
# Topology -- M2; live readings -- P1
# ==========================================================================
def _device(name: str, *, serial: str | None, children: list[dict[str, Any]]) -> dict[str, Any]:
    node: dict[str, Any] = {
        "IOObjectClass": "IOUSBHostDevice",
        "IORegistryEntryName": name,
        "idVendor": 0x090C,
        "idProduct": 0x2320,
        "USB Vendor Name": "SSK Corporation",
        "USB Product Name": name,
        "bcdDevice": 256,
        "locationID": 18874368,
        "USB Address": 1,
        "sessionID": 14635592949514,
        "IORegistryEntryChildren": children,
    }
    if serial is not None:
        node["USB Serial Number"] = serial
    return node


def _media(bsd: str) -> dict[str, Any]:
    return {"IOObjectClass": "IOMedia", "BSD Name": bsd, "IORegistryEntryChildren": []}


def _registry(*roots: dict[str, Any]) -> list[dict[str, Any]]:
    return list(roots)


def test_m2_direct_means_no_device_between_controller_and_storage() -> None:
    assert q.classify_topology(0) == q.TOPOLOGY_DIRECT_USB
    assert q.classify_topology(1) == q.TOPOLOGY_NOT_DIRECT
    direct = q.usb_chain_from_registry(
        _registry(_device("SSK SSD", serial="S1", children=[_media("disk4")])), "disk4"
    )
    assert direct.upstream_count == 0 and q.classify_topology(direct.upstream_count) == "DIRECT_USB"
    hub = _device(
        "USB3.1 Hub",
        serial="H1",
        children=[_device("SSK SSD", serial="S1", children=[_media("disk4")])],
    )
    behind_hub = q.usb_chain_from_registry(_registry(hub), "disk4")
    assert behind_hub.upstream_count == 1
    assert q.classify_topology(behind_hub.upstream_count) == q.TOPOLOGY_NOT_DIRECT
    assert behind_hub.serial == "S1" and behind_hub.product_name == "SSK SSD"
    with pytest.raises(q.HostASsdQualificationError, match="not beneath any USB"):
        q.usb_chain_from_registry(
            _registry(_device("Other", serial="X", children=[_media("disk9")])), "disk4"
        )


def test_a_hub_topology_is_never_admitted_as_direct_by_the_live_reading(tmp_path: Path) -> None:
    from disclosure_drift.m3.external_working_root import VolumeIdentity

    volume = VolumeIdentity(
        volume_uuid=VOLUME,
        mount_point=tmp_path,
        filesystem_type="exfat",
        device_identifier="disk4s2",
    )
    hub = _device(
        "Dock Hub",
        serial="H1",
        children=[_device("SSK SSD", serial="S1", children=[_media("disk4")])],
    )
    chain = q.usb_chain_from_registry(_registry(hub), "disk4")
    live = q.live_tier_from_readings(
        volume=volume,
        partition_info={
            "TotalSize": 499_955_924_992,
            "DiskUUID": "P",
            "DeviceNode": "/dev/disk4s2",
        },
        whole_info={"Size": 500_107_862_016, "DeviceIdentifier": "disk4"},
        chain=chain,
        host_model="MacBookPro17,1",
        architecture="arm64",
        platform_uuid="UUID",
        st_dev=1,
        st_ino=2,
    )
    assert live.stable.topology_class == q.TOPOLOGY_NOT_DIRECT
    record = qualification()
    with pytest.raises(q.HostASsdQualificationError, match="topology_class"):
        q.require_tier_reauthentication(record, live)
    no_serial = q.usb_chain_from_registry(
        _registry(_device("SSK SSD", serial=None, children=[_media("disk4")])), "disk4"
    )
    with pytest.raises(q.HostASsdQualificationError, match="no serial"):
        q.live_tier_from_readings(
            volume=volume,
            partition_info={"TotalSize": 1},
            whole_info={"Size": 1, "DeviceIdentifier": "disk4"},
            chain=no_serial,
            host_model="m",
            architecture="arm64",
            platform_uuid="U",
            st_dev=1,
            st_ino=2,
        )


def test_the_live_reading_hashes_raw_identities_and_never_records_them(tmp_path: Path) -> None:
    from disclosure_drift.m3.external_working_root import VolumeIdentity

    volume = VolumeIdentity(
        volume_uuid=VOLUME,
        mount_point=tmp_path,
        filesystem_type="exfat",
        device_identifier="disk4s2",
    )
    chain = q.usb_chain_from_registry(
        _registry(_device("SSK SSD", serial="RAW-SERIAL-0071", children=[_media("disk4")])), "disk4"
    )
    live = q.live_tier_from_readings(
        volume=volume,
        partition_info={"TotalSize": 10, "DiskUUID": "P", "DeviceNode": "/dev/disk4s2"},
        whole_info={"Size": 20, "DeviceIdentifier": "disk4"},
        chain=chain,
        host_model="MacBookPro17,1",
        architecture="arm64",
        platform_uuid="RAW-PLATFORM-UUID",
        st_dev=1,
        st_ino=2,
    )
    rendered = json.dumps(dict(live.as_record()))
    assert "RAW-SERIAL" not in rendered and "RAW-PLATFORM" not in rendered
    assert live.stable.media_serial_hash == q.domain_hash(
        q.MEDIA_SERIAL_HASH_DOMAIN, "RAW-SERIAL-0071"
    )
    assert live.stable.host_identity_hash == q.domain_hash(q.HOST_HASH_DOMAIN, "RAW-PLATFORM-UUID")
    assert live.stable.enclosure_identity_hash == q.enclosure_identity_hash(
        vendor_id="0x090C",
        product_id="0x2320",
        vendor_name="SSK Corporation",
        product_name="SSK SSD",
        bcd_device=256,
        serial_hash=live.stable.media_serial_hash,
    )
    assert set(live.as_record()["attachment"]) == set(q.ATTACHMENT_OBSERVATION_FIELDS)  # type: ignore[arg-type]


# ==========================================================================
# Reauthentication -- R2, M16
# ==========================================================================
def test_m16_attachment_changes_reauthenticate_and_stable_changes_refuse(tmp_path: Path) -> None:
    record = qualification()
    first = observation_for(record, tmp_path)
    assert q.require_tier_reauthentication(record, first) is first
    # A re-attached device: new disk number, partition, st_dev, session -- still the tier.
    reattached = observation_for(
        record,
        tmp_path,
        whole_disk="disk7",
        partition="disk7s2",
        st_dev=first.attachment["st_dev"] + 1,
        session_id=1,
        usb_address=9,
    )
    assert q.require_tier_reauthentication(record, reattached) is reattached
    assert (
        q.reauthenticate_qualified_tier(
            record, tmp_path, provider=provider_for(record, whole_disk="disk9")
        ).attachment["whole_disk"]
        == "disk9"
    )
    for name, value in (
        ("volume_uuid", OTHER_VOLUME),
        ("media_serial_hash", _hex("other-serial")),
        ("media_size_bytes", 1),
        ("filesystem_type", "apfs"),
        ("host_identity_hash", _hex("other-host")),
        ("enclosure_identity_hash", _hex("other-enclosure")),
        ("volume_total_bytes", 1),
        ("topology_class", q.TOPOLOGY_NOT_DIRECT),
    ):
        moved = q.LiveTierObservation(
            stable=q.StableTierCompatibility.from_record(compatibility_record(**{name: value})),
            attachment=first.attachment,
        )
        with pytest.raises(q.HostASsdQualificationError) as caught:
            q.require_tier_reauthentication(record, moved)
        assert name in str(caught.value)
        assert "whole_disk" not in str(caught.value) and "st_dev" not in str(caught.value)
    # A familiar display name is not identity: nothing here compares a name or a path.
    source = Path(q.__file__).read_text(encoding="utf-8")
    assert "VolumeName" not in source and "volume_name" not in source


# ==========================================================================
# The exact capability envelope of the two new modules -- z02/z03 discipline, P6
# ==========================================================================
NEW_MODULES = {
    "disclosure_drift.m3.host_a_ssd_qualification": q,
    "disclosure_drift.m3.chunk_transfer": x,
}
ACCEPTED_LAUNCHES = {
    "disclosure_drift.m3.host_a_ssd_qualification": [
        ("/usr/sbin/diskutil", ("info", "-plist", "str(target)")),
        ("/usr/sbin/ioreg", ("-a", "-p", "IOService", "-r", "-c", "IOUSBHostDevice", "-l", "-w0")),
        ("/usr/sbin/sysctl", ("-n", "hw.model")),
        ("/usr/sbin/ioreg", ("-rd1", "-c", "IOPlatformExpertDevice")),
    ],
    "disclosure_drift.m3.chunk_transfer": [("/usr/sbin/sysctl", ("-n", "vm.swapusage"))],
}
#: chunk_transfer holds exactly one exact-entry deletion site, two directory removals (the
#: emptied subdirectories and the base) and one rename (the atomic finalization). Every other
#: destructive capability is absent; host_a_ssd_qualification holds none at all.
ACCEPTED_DESTRUCTIVE = {
    "disclosure_drift.m3.host_a_ssd_qualification": [],
    "disclosure_drift.m3.chunk_transfer": [".rename(", ".rmdir(", ".rmdir(", ".unlink("],
}
ACCEPTED_WRITE_OPENS = {
    "disclosure_drift.m3.host_a_ssd_qualification": [],
    "disclosure_drift.m3.chunk_transfer": [
        ("O_CREAT", "O_EXCL", "O_WRONLY"),
        ("O_CREAT", "O_EXCL", "O_WRONLY"),
        ("O_APPEND", "O_CREAT", "O_WRONLY"),
    ],
}


def _write_opens(source: str) -> list[tuple[str, ...]]:
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            flags = c13i._os_open_write_flags(node, {"os"})  # noqa: SLF001
            if flags:
                found.append(flags)
    return found


def test_the_new_modules_hold_exactly_their_accepted_capabilities() -> None:
    for name, module in NEW_MODULES.items():
        source = Path(module.__file__).read_text(encoding="utf-8")
        violations = sorted(text for _line, text in c13i.capability_violations(source))
        assert violations == ACCEPTED_DESTRUCTIVE[name], (name, violations)
        assert c13i.subprocess_launches(source) == ACCEPTED_LAUNCHES[name], name
        assert _write_opens(source) == ACCEPTED_WRITE_OPENS[name], name
        assert c13i.environment_closure_violations(name, source) == [], name
        tree = ast.parse(source)
        imported = {
            (alias.name if isinstance(node, ast.Import) else f"{node.module}")
            for node in ast.walk(tree)
            if isinstance(node, ast.Import | ast.ImportFrom)
            for alias in node.names
        }
        assert not any(item.startswith("sqlite3") for item in imported), name
        assert "sqlite3" not in source and "shutil" not in source, name
        assert "DISCLOSURE_DRIFT" not in source and "argparse" not in source, name
        for prefix in ("httpx", "disclosure_drift.sec", "disclosure_drift.m3.e0"):
            assert not any(item.startswith(prefix) for item in imported), (name, prefix)


def test_the_new_modules_never_name_a_chunk_family_module() -> None:
    """The accepted closure proofs (C1 A39, C3 A28) scan every non-family source for a family
    name; the two C22 modules keep them true by construction and are wired in only from the
    family side."""
    for module in NEW_MODULES.values():
        source = Path(module.__file__).read_text(encoding="utf-8")
        for name in CHUNK_FAMILY:
            assert name not in source, (module.__name__, name)


def test_raw_identities_never_enter_committed_source_or_tests() -> None:
    for path in (
        Path(q.__file__),
        Path(x.__file__),
        Path(__file__),
        Path(__file__).parent / "test_d151_c22_transfer_reclaim.py",
        Path(__file__).parent.parent / "integration" / "test_d151_c22_transfer_lifecycle.py",
    ):
        if path.exists():
            text = path.read_text(encoding="utf-8")
            raw_serial_prefix = "SSKP" + "SSD0000"
            raw_host_prefix = "f35d" + "77f6f617"
            assert raw_serial_prefix not in text, path.name
            assert raw_host_prefix not in text, path.name
