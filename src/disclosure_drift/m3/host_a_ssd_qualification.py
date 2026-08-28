"""Host-A / direct-SSD qualification records and tier reauthentication -- D151-C22 R2.

A qualification record is the sealed, canonical document the owner's Phase-A qualification
instrument writes after the physical qualification of the exact Host-A host and one directly
connected SSD. This module reads such a record **exactly** -- every top-level field present,
nothing extra, the contract exact, both sealed identities recomputed -- and derives from it the
only two questions production ever asks: may a verified copy target this tier, and may the
internal copy of a transferred artifact ever be reclaimed after such a copy.

Two identities, two purposes (C22-R2). The **complete qualification identity** seals every
measured field of the record. The **stable tier-compatibility identity** seals only the ten
fields that survive detaching and re-attaching the same device: the host model and architecture,
the hashed host identity, the hashed media serial, the physical media size, the volume UUID, the
filesystem type, the volume's total bytes, the direct topology class and the hashed enclosure
identity. Attachment observations -- BSD disk identifier, partition identifier, ``st_dev``,
mount path, device node, USB address and session -- are recorded, never compared: a re-attached
volume legitimately reports new ones, and a different device behind a familiar name does not.

Nothing here decides from a path, a volume name or a display string, and nothing here opens a
database. Reading the live tier launches only fixed read-only system queries.
"""

from __future__ import annotations

import hashlib
import json
import os
import plistlib
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.external_working_root import (
    ExternalWorkingRootError,
    VolumeIdentity,
    macos_volume_identity,
)

__all__ = [
    "ATTACHMENT_OBSERVATION_FIELDS",
    "CLASS_COPY_ONLY",
    "CLASS_FAIL",
    "CLASS_RECLAIM_CAPABLE",
    "ENCLOSURE_HASH_DOMAIN",
    "HOST_HASH_DOMAIN",
    "MEDIA_SERIAL_HASH_DOMAIN",
    "QUALIFICATION_CLASSES",
    "QUALIFICATION_CONTRACT",
    "QUALIFICATION_DOCUMENT_FIELDS",
    "QUALIFICATION_FILENAME",
    "QUALIFICATION_IDENTITY_KEY",
    "QUALIFICATION_RECORD_KIND",
    "RECONNECT_COMPLETED",
    "STABLE_TIER_COMPATIBILITY_FIELDS",
    "STABLE_TIER_COMPATIBILITY_IDENTITY_KEY",
    "STABLE_TIER_COMPATIBILITY_KEY",
    "SUPPORTED_FILESYSTEMS",
    "TOPOLOGY_DIRECT_USB",
    "TOPOLOGY_NOT_DIRECT",
    "HostASsdQualification",
    "HostASsdQualificationError",
    "LiveTierObservation",
    "LiveTierProvider",
    "StableTierCompatibility",
    "UsbChain",
    "canonical_json_bytes",
    "classify_topology",
    "domain_hash",
    "enclosure_identity_hash",
    "live_tier_from_readings",
    "macos_live_tier",
    "observe_live_tier",
    "reauthenticate_qualified_tier",
    "require_copy_capable",
    "require_reclaim_capable",
    "require_tier_reauthentication",
    "sealed_identity",
    "usb_chain_from_registry",
]


class HostASsdQualificationError(DisclosureDriftError):
    """A qualification record, a live tier reading or a reauthentication is refused."""


#: The one contract this build reads and writes for a qualification record. No ``/2``, no alias.
QUALIFICATION_CONTRACT: Final = "m3.3-host-a-direct-ssd-qualification/1"
#: The record kind a qualification document must state.
QUALIFICATION_RECORD_KIND: Final = "host_a_direct_ssd_qualification"
#: The file name a qualification record is sealed under inside its evidence namespace.
QUALIFICATION_FILENAME: Final = "qualification.json"
#: The key carrying the complete qualification identity: SHA-256 over the canonical record
#: without this key.
QUALIFICATION_IDENTITY_KEY: Final = "qualification_identity"
#: The key carrying the stable tier-compatibility representation.
STABLE_TIER_COMPATIBILITY_KEY: Final = "stable_tier_compatibility"
#: The key carrying the stable tier-compatibility identity: SHA-256 over the canonical
#: compatibility representation alone.
STABLE_TIER_COMPATIBILITY_IDENTITY_KEY: Final = "stable_tier_compatibility_identity"

#: Every predicate passed, file and parent-directory durability included.
CLASS_RECLAIM_CAPABLE: Final = "RECLAIM_CAPABLE"
#: Every integrity, performance, topology, capacity and reconnect predicate passed and file
#: fsync succeeded, but parent-directory durability could not be established.
CLASS_COPY_ONLY: Final = "COPY_ONLY"
#: Any other required predicate failed. Nothing is ever admitted on a FAIL record.
CLASS_FAIL: Final = "FAIL"
#: The only three classes a record may state.
QUALIFICATION_CLASSES: Final[tuple[str, ...]] = (CLASS_RECLAIM_CAPABLE, CLASS_COPY_ONLY, CLASS_FAIL)

#: Host port -> cable -> SSD enclosure, with no hub, dock, monitor hub or pass-through device.
TOPOLOGY_DIRECT_USB: Final = "DIRECT_USB"
#: Anything else.
TOPOLOGY_NOT_DIRECT: Final = "NOT_DIRECT"
#: The filesystems a qualification may be taken on.
SUPPORTED_FILESYSTEMS: Final[tuple[str, ...]] = ("apfs", "exfat")
#: The reconnect-checkpoint status that alone proves the physical reconnect qualification.
RECONNECT_COMPLETED: Final = "completed"

#: The ten fields of the stable tier-compatibility representation, in canonical order.
STABLE_TIER_COMPATIBILITY_FIELDS: Final[tuple[str, ...]] = (
    "architecture",
    "enclosure_identity_hash",
    "filesystem_type",
    "host_identity_hash",
    "host_model",
    "media_serial_hash",
    "media_size_bytes",
    "topology_class",
    "volume_total_bytes",
    "volume_uuid",
)
#: Attachment observations: recorded in a live reading, and decided on by nothing, ever.
ATTACHMENT_OBSERVATION_FIELDS: Final[tuple[str, ...]] = (
    "device_node",
    "location_id",
    "partition",
    "partition_uuid",
    "session_id",
    "st_dev",
    "st_ino",
    "usb_address",
    "whole_disk",
)
#: The exact top-level key set of a qualification document. A key missing or unexpected refuses.
QUALIFICATION_DOCUMENT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "attachment_observations",
        "capacity",
        "cleanup",
        "contract",
        "durability",
        "ended_utc",
        "host",
        "metrics",
        "operator_checkpoints",
        "payload",
        "power_observations",
        "predicates",
        "push_notification_capability",
        "qualification_class",
        "qualification_identity",
        "qualification_run_id",
        "quiescence_before_checkpoint_1",
        "reconnect_checkpoint",
        "record_kind",
        "stable_media_identity",
        "stable_tier_compatibility",
        "stable_tier_compatibility_identity",
        "started_utc",
        "transport",
        "unmount_characterization",
    }
)
#: Domain separators for the three hashed identities. A raw host UUID or device serial never
#: enters a record this module writes or compares; only the domain-separated digest does.
HOST_HASH_DOMAIN: Final = "d151-c22-host-identity/1"
MEDIA_SERIAL_HASH_DOMAIN: Final = "d151-c22-media-serial/1"
ENCLOSURE_HASH_DOMAIN: Final = "d151-c22-enclosure-identity/1"

_HEX64: Final = re.compile(r"\A[0-9a-f]{64}\Z")
_HEX16: Final = re.compile(r"\A[0-9a-f]{16}\Z")
_DISKUTIL: Final = "/usr/sbin/diskutil"
_IOREG: Final = "/usr/sbin/ioreg"
_SYSCTL: Final = "/usr/sbin/sysctl"
_USB_DEVICE_CLASS: Final = "IOUSBHostDevice"


# --------------------------------------------------------------------------- #
# Canonical form and sealed identities -- packet §4
# --------------------------------------------------------------------------- #
def canonical_json_bytes(record: object) -> bytes:
    """The one canonical serialization of a record: UTF-8, object only, sorted keys, compact
    separators, no NaN or Infinity, exactly one trailing newline.

    Raises:
        HostASsdQualificationError: ``record`` is not a mapping or carries a non-finite number.
    """
    if not isinstance(record, Mapping):
        message = "a canonical record is a JSON object; a non-object is refused"
        raise HostASsdQualificationError(message)
    try:
        text = json.dumps(
            dict(record), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
    except (TypeError, ValueError) as exc:
        message = f"a record could not be rendered canonically and is refused: {exc}"
        raise HostASsdQualificationError(message) from exc
    return (text + "\n").encode("utf-8")


def sealed_identity(record: Mapping[str, object], *, identity_key: str) -> str:
    """SHA-256 over the canonical record **without** its identity field."""
    body = {str(key): value for key, value in record.items() if str(key) != identity_key}
    return hashlib.sha256(canonical_json_bytes(body)).hexdigest()


def domain_hash(domain: str, value: str) -> str:
    """A domain-separated SHA-256 of a raw identity value (host UUID, device serial)."""
    return hashlib.sha256(domain.encode("utf-8") + b"\x1f" + value.encode("utf-8")).hexdigest()


def enclosure_identity_hash(
    *,
    vendor_id: str | None,
    product_id: str | None,
    vendor_name: str | None,
    product_name: str | None,
    bcd_device: int | None,
    serial_hash: str | None,
) -> str:
    """The hashed enclosure/bridge identity over its six public fields."""
    return hashlib.sha256(
        canonical_json_bytes(
            {
                "domain": ENCLOSURE_HASH_DOMAIN,
                "vendor_id": vendor_id,
                "product_id": product_id,
                "vendor_name": vendor_name,
                "product_name": product_name,
                "bcd_device": bcd_device,
                "serial_hash": serial_hash,
            }
        )
    ).hexdigest()


def _require_text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        message = f"qualification field {name!r} must be a non-empty string; got {value!r}"
        raise HostASsdQualificationError(message)
    return value


def _require_hex64(value: object, name: str) -> str:
    text = _require_text(value, name)
    if _HEX64.match(text) is None:
        message = f"qualification field {name!r} must be a 64-hex-digit digest; refused"
        raise HostASsdQualificationError(message)
    return text


def _require_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        message = (
            f"qualification field {name!r} must be a non-negative integer, never a Boolean or a "
            f"float; got {value!r}"
        )
        raise HostASsdQualificationError(message)
    return value


def _require_mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        message = f"qualification field {name!r} must be an object; refused"
        raise HostASsdQualificationError(message)
    return {str(key): item for key, item in value.items()}


# --------------------------------------------------------------------------- #
# The stable tier-compatibility representation -- R2
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class StableTierCompatibility:
    """The ten fields a re-attached device must reproduce to be the qualified tier."""

    architecture: str
    enclosure_identity_hash: str
    filesystem_type: str
    host_identity_hash: str
    host_model: str
    media_serial_hash: str
    media_size_bytes: int
    topology_class: str
    volume_total_bytes: int
    volume_uuid: str

    def __post_init__(self) -> None:
        _require_text(self.architecture, "architecture")
        _require_hex64(self.enclosure_identity_hash, "enclosure_identity_hash")
        if self.filesystem_type not in SUPPORTED_FILESYSTEMS:
            message = (
                f"filesystem {self.filesystem_type!r} is not one a qualification may be taken "
                f"on ({', '.join(SUPPORTED_FILESYSTEMS)})"
            )
            raise HostASsdQualificationError(message)
        _require_hex64(self.host_identity_hash, "host_identity_hash")
        _require_text(self.host_model, "host_model")
        _require_hex64(self.media_serial_hash, "media_serial_hash")
        _require_count(self.media_size_bytes, "media_size_bytes")
        _require_text(self.topology_class, "topology_class")
        _require_count(self.volume_total_bytes, "volume_total_bytes")
        _require_text(self.volume_uuid, "volume_uuid")

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering, in canonical field order."""
        return {name: getattr(self, name) for name in STABLE_TIER_COMPATIBILITY_FIELDS}

    def identity(self) -> str:
        """SHA-256 over the canonical representation."""
        return hashlib.sha256(canonical_json_bytes(self.as_record())).hexdigest()

    @classmethod
    def from_record(cls, record: Mapping[str, object]) -> StableTierCompatibility:
        """Rebuild from an exact record: every field present, none extra, each typed.

        Raises:
            HostASsdQualificationError: the record is not exactly the ten typed fields.
        """
        present = {str(key) for key in record}
        expected = set(STABLE_TIER_COMPATIBILITY_FIELDS)
        if present != expected:
            message = (
                "a stable tier-compatibility record is exact; this one is missing "
                f"{sorted(expected - present)} and carries unexpected {sorted(present - expected)}"
            )
            raise HostASsdQualificationError(message)
        return cls(
            architecture=_require_text(record["architecture"], "architecture"),
            enclosure_identity_hash=_require_hex64(
                record["enclosure_identity_hash"], "enclosure_identity_hash"
            ),
            filesystem_type=_require_text(record["filesystem_type"], "filesystem_type"),
            host_identity_hash=_require_hex64(record["host_identity_hash"], "host_identity_hash"),
            host_model=_require_text(record["host_model"], "host_model"),
            media_serial_hash=_require_hex64(record["media_serial_hash"], "media_serial_hash"),
            media_size_bytes=_require_count(record["media_size_bytes"], "media_size_bytes"),
            topology_class=_require_text(record["topology_class"], "topology_class"),
            volume_total_bytes=_require_count(record["volume_total_bytes"], "volume_total_bytes"),
            volume_uuid=_require_text(record["volume_uuid"], "volume_uuid"),
        )

    def differences(self, other: StableTierCompatibility) -> tuple[str, ...]:
        """The names of every stable field on which ``other`` differs, in canonical order."""
        return tuple(
            name
            for name in STABLE_TIER_COMPATIBILITY_FIELDS
            if getattr(self, name) != getattr(other, name)
        )


# --------------------------------------------------------------------------- #
# The sealed qualification record
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class HostASsdQualification:
    """One sealed qualification record, read exactly, with its two identities verified.

    ``document`` is the complete verified document. The decided-on fields are lifted into typed
    attributes; every other section is required to be present and of its recorded shape and is
    otherwise carried opaque, because the complete identity seals it whole.
    """

    contract: str
    record_kind: str
    qualification_run_id: str
    started_utc: str
    ended_utc: str
    qualification_class: str
    stable_tier_compatibility: StableTierCompatibility
    stable_tier_compatibility_identity: str
    qualification_identity: str
    reconnect_status: str
    predicates: Mapping[str, bool]
    document: Mapping[str, object]

    @property
    def physical_reconnect_qualified(self) -> bool:
        """Whether the physical disconnect/reconnect stage ran and every reconnect predicate
        passed. A record whose reconnect stage was not run never qualifies a tier."""
        return (
            self.reconnect_status == RECONNECT_COMPLETED
            and self.predicates.get("reconnect_stable_identity_unchanged") is True
            and self.predicates.get("reconnect_manifest_exact") is True
            and self.predicates.get("reconnect_topology_direct") is True
            and self.predicates.get("reconnect_readback_at_least_250_mib_s") is True
        )

    @property
    def admits_verified_copy(self) -> bool:
        """Whether a verified copy may target this tier: class RECLAIM_CAPABLE or COPY_ONLY,
        physical reconnect qualified, and a direct topology. FAIL admits nothing."""
        return (
            self.qualification_class in (CLASS_RECLAIM_CAPABLE, CLASS_COPY_ONLY)
            and self.physical_reconnect_qualified
            and self.stable_tier_compatibility.topology_class == TOPOLOGY_DIRECT_USB
        )

    @property
    def admits_reclaim(self) -> bool:
        """Whether a reclaim may ever rest on this tier: a copy-admitting RECLAIM_CAPABLE record.
        COPY_ONLY is a valid copy tier and is never represented as reclaim-capable."""
        return self.admits_verified_copy and self.qualification_class == CLASS_RECLAIM_CAPABLE

    @classmethod
    def from_document(cls, document: Mapping[str, object]) -> HostASsdQualification:
        """Read one qualification document exactly, or refuse.

        Refusals, in order: not an object; a top-level key missing or unexpected; the wrong
        contract or record kind (no ``/2``, no alias, no upgrade); a decided-on field of the
        wrong type; a compatibility record that is not exactly its ten fields; a compatibility
        identity that is not the identity of the compatibility record; a qualification identity
        that is not the identity of the document beside it -- which is what a relabelled class,
        an edited field or a stale seal all look like; and a compatibility record that does not
        agree with the host and media sections it summarizes.

        Raises:
            HostASsdQualificationError: any refusal above.
        """
        stored = _require_mapping(document, "document")
        present = set(stored)
        if present != QUALIFICATION_DOCUMENT_FIELDS:
            message = (
                "a qualification document is exact; this one is missing "
                f"{sorted(QUALIFICATION_DOCUMENT_FIELDS - present)} and carries unexpected "
                f"{sorted(present - QUALIFICATION_DOCUMENT_FIELDS)}; refused rather than read"
            )
            raise HostASsdQualificationError(message)
        contract = stored["contract"]
        if contract != QUALIFICATION_CONTRACT:
            message = (
                f"the qualification document carries contract {contract!r}; this build reads "
                f"exactly {QUALIFICATION_CONTRACT!r} and never upgrades, aliases or reinterprets"
            )
            raise HostASsdQualificationError(message)
        if stored["record_kind"] != QUALIFICATION_RECORD_KIND:
            message = f"the qualification document records kind {stored['record_kind']!r}; refused"
            raise HostASsdQualificationError(message)
        run_id = _require_text(stored["qualification_run_id"], "qualification_run_id")
        if _HEX16.match(run_id) is None:
            message = "the qualification run identifier is not sixteen hex digits; refused"
            raise HostASsdQualificationError(message)
        klass = _require_text(stored["qualification_class"], "qualification_class")
        if klass not in QUALIFICATION_CLASSES:
            message = (
                f"qualification class {klass!r} is not one of {list(QUALIFICATION_CLASSES)}; "
                "refused rather than mapped"
            )
            raise HostASsdQualificationError(message)
        for name in ("started_utc", "ended_utc", "push_notification_capability"):
            _require_text(stored[name], name)
        for name in (
            "attachment_observations",
            "capacity",
            "cleanup",
            "durability",
            "host",
            "metrics",
            "payload",
            "quiescence_before_checkpoint_1",
            "reconnect_checkpoint",
            "stable_media_identity",
            "transport",
            "unmount_characterization",
        ):
            _require_mapping(stored[name], name)
        for name in ("operator_checkpoints", "power_observations"):
            if not isinstance(stored[name], Sequence) or isinstance(stored[name], str | bytes):
                message = f"qualification field {name!r} must be a list; refused"
                raise HostASsdQualificationError(message)
        raw_predicates = _require_mapping(stored["predicates"], "predicates")
        predicates: dict[str, bool] = {}
        for name, value in raw_predicates.items():
            if not isinstance(value, bool):
                message = f"qualification predicate {name!r} is not a Boolean; refused"
                raise HostASsdQualificationError(message)
            predicates[name] = value
        reconnect = _require_mapping(stored["reconnect_checkpoint"], "reconnect_checkpoint")
        reconnect_status = _require_text(reconnect.get("status"), "reconnect_checkpoint.status")
        compat = StableTierCompatibility.from_record(
            _require_mapping(stored[STABLE_TIER_COMPATIBILITY_KEY], STABLE_TIER_COMPATIBILITY_KEY)
        )
        compat_identity = _require_hex64(
            stored[STABLE_TIER_COMPATIBILITY_IDENTITY_KEY], STABLE_TIER_COMPATIBILITY_IDENTITY_KEY
        )
        if compat_identity != compat.identity():
            message = (
                "the stable tier-compatibility identity does not seal the compatibility record "
                "beside it; a relabelled or edited record is refused rather than resealed"
            )
            raise HostASsdQualificationError(message)
        identity = _require_hex64(stored[QUALIFICATION_IDENTITY_KEY], QUALIFICATION_IDENTITY_KEY)
        if identity != sealed_identity(stored, identity_key=QUALIFICATION_IDENTITY_KEY):
            message = (
                "the qualification identity does not seal the document beside it; a relabelled "
                "class, an edited field or a stale seal is refused rather than repaired"
            )
            raise HostASsdQualificationError(message)
        host = _require_mapping(stored["host"], "host")
        media = _require_mapping(stored["stable_media_identity"], "stable_media_identity")
        agreements = (
            ("host_model", host.get("model")),
            ("architecture", host.get("architecture")),
            ("host_identity_hash", host.get("host_identity_hash")),
            ("media_serial_hash", media.get("media_serial_hash")),
            ("media_size_bytes", media.get("media_size_bytes")),
            ("enclosure_identity_hash", media.get("enclosure_identity_hash")),
            ("volume_uuid", media.get("volume_uuid")),
            ("filesystem_type", media.get("filesystem_type")),
            ("volume_total_bytes", media.get("volume_total_bytes")),
            ("topology_class", media.get("topology_class")),
        )
        disagreeing = [name for name, value in agreements if getattr(compat, name) != value]
        if disagreeing:
            message = (
                "the stable tier-compatibility record disagrees with the host and media "
                f"sections it summarizes on {disagreeing}; refused"
            )
            raise HostASsdQualificationError(message)
        return cls(
            contract=str(contract),
            record_kind=str(stored["record_kind"]),
            qualification_run_id=run_id,
            started_utc=str(stored["started_utc"]),
            ended_utc=str(stored["ended_utc"]),
            qualification_class=klass,
            stable_tier_compatibility=compat,
            stable_tier_compatibility_identity=compat_identity,
            qualification_identity=identity,
            reconnect_status=reconnect_status,
            predicates=predicates,
            document=dict(stored),
        )

    @classmethod
    def from_path(cls, path: Path) -> HostASsdQualification:
        """Read a sealed record from its file, requiring the bytes to be byte-canonical.

        Raises:
            HostASsdQualificationError: the file is a link, absent, not decodable, not an
                object, not byte-for-byte canonical, or not an exact sealed record.
        """
        if path.is_symlink():
            message = "a qualification record is never read through a symbolic link"
            raise HostASsdQualificationError(message)
        if not path.is_file():
            message = "no qualification record exists at the stated location; refused"
            raise HostASsdQualificationError(message)
        raw = path.read_bytes()
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            message = f"the qualification record is not decodable canonical JSON: {exc}"
            raise HostASsdQualificationError(message) from exc
        if not isinstance(decoded, dict):
            message = "the qualification record is not a JSON object; refused"
            raise HostASsdQualificationError(message)
        if canonical_json_bytes(decoded) != raw:
            message = (
                "the qualification record is not byte-canonical (sorted keys, compact "
                "separators, one trailing newline); a re-serialized or edited file is refused"
            )
            raise HostASsdQualificationError(message)
        return cls.from_document(decoded)


def require_copy_capable(qualification: HostASsdQualification) -> HostASsdQualification:
    """Return the record only if a verified copy may target its tier.

    Raises:
        HostASsdQualificationError: the class is FAIL, the physical reconnect qualification is
            absent, or the topology is not direct. Nothing is ever admitted on a FAIL record.
    """
    if qualification.qualification_class == CLASS_FAIL:
        message = (
            f"qualification {qualification.qualification_run_id} is class FAIL; no verified "
            "copy, spill, transfer or reclaim may rest on it. A later qualification is a "
            "separately authorized fresh run with a fresh namespace, never this record relabelled"
        )
        raise HostASsdQualificationError(message)
    if not qualification.physical_reconnect_qualified:
        message = (
            f"qualification {qualification.qualification_run_id} carries no completed physical "
            f"reconnect qualification (reconnect status {qualification.reconnect_status!r}); a "
            "tier whose identity was never proved stable across a physical reconnect admits "
            "nothing"
        )
        raise HostASsdQualificationError(message)
    if not qualification.admits_verified_copy:
        message = (
            f"qualification {qualification.qualification_run_id} records topology "
            f"{qualification.stable_tier_compatibility.topology_class!r}; only a direct "
            "topology admits a verified copy"
        )
        raise HostASsdQualificationError(message)
    return qualification


def require_reclaim_capable(qualification: HostASsdQualification) -> HostASsdQualification:
    """Return the record only if a reclaim may ever rest on its tier.

    Raises:
        HostASsdQualificationError: the record does not admit a copy, or its class is not
            RECLAIM_CAPABLE. COPY_ONLY is refused here by construction.
    """
    require_copy_capable(qualification)
    if qualification.qualification_class != CLASS_RECLAIM_CAPABLE:
        message = (
            f"qualification {qualification.qualification_run_id} is class "
            f"{qualification.qualification_class}; only RECLAIM_CAPABLE may ever underwrite a "
            "reclaim, and a verified copy on this tier leaves the internal copy retained"
        )
        raise HostASsdQualificationError(message)
    return qualification


# --------------------------------------------------------------------------- #
# Reading the live tier -- R2 reauthentication
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class UsbChain:
    """The USB devices between a built-in host controller and one storage device."""

    vendor_id: int
    product_id: int
    vendor_name: str | None
    product_name: str | None
    bcd_device: int | None
    serial: str | None
    location_id: int | None
    usb_address: int | None
    session_id: int | None
    upstream_count: int

    @property
    def enclosure_hash(self) -> str:
        """The hashed enclosure identity of the storage device."""
        return enclosure_identity_hash(
            vendor_id=f"0x{self.vendor_id:04X}",
            product_id=f"0x{self.product_id:04X}",
            vendor_name=self.vendor_name,
            product_name=self.product_name,
            bcd_device=self.bcd_device,
            serial_hash=None
            if self.serial is None
            else domain_hash(MEDIA_SERIAL_HASH_DOMAIN, self.serial),
        )


@dataclass(frozen=True, slots=True)
class LiveTierObservation:
    """What the tier IS right now: its stable representation and its attachment observations."""

    stable: StableTierCompatibility
    attachment: Mapping[str, object]

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "stable": dict(self.stable.as_record()),
            "stable_identity": self.stable.identity(),
            "attachment": {
                name: self.attachment.get(name) for name in ATTACHMENT_OBSERVATION_FIELDS
            },
        }


#: How a live tier observation is obtained for a path. Substituting one is **the** test seam:
#: no test may depend on the operator's SSD being attached. Every guard resolves
#: :func:`macos_live_tier` from module globals at call time.
LiveTierProvider = Callable[[Path], LiveTierObservation]


def classify_topology(upstream_count: int) -> str:
    """Direct means exactly nothing between the host controller and the storage device."""
    return TOPOLOGY_DIRECT_USB if upstream_count == 0 else TOPOLOGY_NOT_DIRECT


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _optional_text(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _find_media(
    node: Mapping[str, Any], whole_disk: str, chain: list[Mapping[str, Any]]
) -> list[Mapping[str, Any]] | None:
    here = [*chain, node] if node.get("IOObjectClass") == _USB_DEVICE_CLASS else chain
    if node.get("BSD Name") == whole_disk and node.get("IOObjectClass") == "IOMedia":
        return here
    for child in node.get("IORegistryEntryChildren") or ():
        if isinstance(child, Mapping):
            found = _find_media(child, whole_disk, here)
            if found is not None:
                return found
    return None


def usb_chain_from_registry(parsed: object, whole_disk: str) -> UsbChain:
    """The USB chain above ``whole_disk``'s media from a parsed IORegistry property list.

    Pure over the parsed data, so a synthetic registry -- a hub between controller and device,
    a device with no serial -- exercises exactly the classification production applies.

    Raises:
        HostASsdQualificationError: the media is not beneath any USB device, or the storage
            device carries no vendor/product identity.
    """
    roots: Sequence[Any] = parsed if isinstance(parsed, list) else [parsed]
    chain: list[Mapping[str, Any]] | None = None
    for root in roots:
        if isinstance(root, Mapping):
            chain = _find_media(root, whole_disk, [])
            if chain is not None:
                break
    if not chain:
        message = (
            f"media {whole_disk!r} is not beneath any USB storage device in the IORegistry; a "
            "tier whose attachment cannot be read is refused rather than assumed direct"
        )
        raise HostASsdQualificationError(message)
    storage = chain[-1]
    vendor = storage.get("idVendor")
    product = storage.get("idProduct")
    if not isinstance(vendor, int) or not isinstance(product, int):
        message = "the storage device reports no USB vendor/product identity; refused"
        raise HostASsdQualificationError(message)
    return UsbChain(
        vendor_id=vendor,
        product_id=product,
        vendor_name=_optional_text(storage.get("USB Vendor Name")),
        product_name=_optional_text(storage.get("USB Product Name")),
        bcd_device=_optional_int(storage.get("bcdDevice")),
        serial=_optional_text(storage.get("USB Serial Number")),
        location_id=_optional_int(storage.get("locationID")),
        usb_address=_optional_int(storage.get("USB Address")),
        session_id=_optional_int(storage.get("sessionID")),
        upstream_count=len(chain) - 1,
    )


def live_tier_from_readings(
    *,
    volume: VolumeIdentity,
    partition_info: Mapping[str, object],
    whole_info: Mapping[str, object],
    chain: UsbChain,
    host_model: str,
    architecture: str,
    platform_uuid: str,
    st_dev: int,
    st_ino: int,
) -> LiveTierObservation:
    """Assemble one live observation from its readings. Pure; the readings are the seams.

    Raises:
        HostASsdQualificationError: the storage device carries no serial, the media reports no
            size, or the volume reports no total.
    """
    if chain.serial is None:
        message = (
            "the storage device exposes no serial number; without one no stable media identity "
            "exists and the tier is refused"
        )
        raise HostASsdQualificationError(message)
    media_size = whole_info.get("Size")
    total = partition_info.get("TotalSize")
    if isinstance(media_size, bool) or not isinstance(media_size, int):
        message = "the whole disk reports no media size; refused"
        raise HostASsdQualificationError(message)
    if isinstance(total, bool) or not isinstance(total, int):
        message = "the volume reports no total size; refused"
        raise HostASsdQualificationError(message)
    stable = StableTierCompatibility(
        architecture=architecture,
        enclosure_identity_hash=chain.enclosure_hash,
        filesystem_type=volume.filesystem_type,
        host_identity_hash=domain_hash(HOST_HASH_DOMAIN, platform_uuid),
        host_model=host_model,
        media_serial_hash=domain_hash(MEDIA_SERIAL_HASH_DOMAIN, chain.serial),
        media_size_bytes=media_size,
        topology_class=classify_topology(chain.upstream_count),
        volume_total_bytes=total,
        volume_uuid=volume.volume_uuid,
    )
    attachment = {
        "device_node": _optional_text(partition_info.get("DeviceNode")),
        "location_id": chain.location_id,
        "partition": volume.device_identifier,
        "partition_uuid": _optional_text(partition_info.get("DiskUUID")),
        "session_id": chain.session_id,
        "st_dev": st_dev,
        "st_ino": st_ino,
        "usb_address": chain.usb_address,
        "whole_disk": _optional_text(whole_info.get("DeviceIdentifier")),
    }
    return LiveTierObservation(stable=stable, attachment=attachment)


def _diskutil_info(target: str) -> Mapping[str, object]:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_DISKUTIL, "info", "-plist", str(target)],
            capture_output=True,
            check=True,
            timeout=60,
        )
        parsed = plistlib.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        message = f"disk information could not be read ({type(exc).__name__}); refused"
        raise HostASsdQualificationError(message) from exc
    if not isinstance(parsed, dict):
        message = "disk information did not parse as a property-list dictionary; refused"
        raise HostASsdQualificationError(message)
    return {str(key): value for key, value in parsed.items()}


def _usb_registry() -> object:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_IOREG, "-a", "-p", "IOService", "-r", "-c", _USB_DEVICE_CLASS, "-l", "-w0"],
            capture_output=True,
            check=True,
            timeout=60,
        )
        return plistlib.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        message = f"the USB registry could not be read ({type(exc).__name__}); refused"
        raise HostASsdQualificationError(message) from exc


def _host_model() -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_SYSCTL, "-n", "hw.model"], capture_output=True, check=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as exc:
        message = f"the host model could not be read ({type(exc).__name__}); refused"
        raise HostASsdQualificationError(message) from exc
    return _require_text(completed.stdout.decode("utf-8", errors="replace").strip(), "host_model")


def _platform_uuid() -> str:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_IOREG, "-rd1", "-c", "IOPlatformExpertDevice"],
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        message = f"the host platform identity could not be read ({type(exc).__name__}); refused"
        raise HostASsdQualificationError(message) from exc
    text = completed.stdout.decode("utf-8", errors="replace")
    match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', text)
    if match is None:
        message = "the host reports no platform identity; refused"
        raise HostASsdQualificationError(message)
    return match.group(1)


def macos_live_tier(path: Path) -> LiveTierObservation:
    """Measure the tier hosting ``path`` from structured system queries -- the default provider.

    Raises:
        HostASsdQualificationError: any reading fails or is incomplete.
    """
    try:
        volume = macos_volume_identity(path)
    except ExternalWorkingRootError as exc:
        message = f"the volume hosting the path could not be identified: {exc}"
        raise HostASsdQualificationError(message) from exc
    partition_info = _diskutil_info(volume.device_identifier)
    whole = partition_info.get("ParentWholeDisk")
    if not isinstance(whole, str) or not whole:
        message = "the volume reports no parent whole disk; refused"
        raise HostASsdQualificationError(message)
    whole_info = _diskutil_info(whole)
    chain = usb_chain_from_registry(_usb_registry(), whole)
    st = volume.mount_point.stat()
    return live_tier_from_readings(
        volume=volume,
        partition_info=partition_info,
        whole_info=whole_info,
        chain=chain,
        host_model=_host_model(),
        architecture=os.uname().machine,
        platform_uuid=_platform_uuid(),
        st_dev=st.st_dev,
        st_ino=st.st_ino,
    )


def observe_live_tier(
    path: Path, *, provider: LiveTierProvider | None = None
) -> LiveTierObservation:
    """One live observation of the tier hosting ``path``, through the provider seam."""
    resolve = macos_live_tier if provider is None else provider
    return resolve(path)


def require_tier_reauthentication(
    qualification: HostASsdQualification, observation: LiveTierObservation
) -> LiveTierObservation:
    """Hold a live observation to the record's stable representation, field for field -- R2.

    Every one of the ten stable fields must agree exactly. No attachment observation is
    consulted: a changed disk number, partition identifier, ``st_dev``, mount path, device node,
    USB address or session is a re-attachment, not a different tier; a changed media serial,
    volume UUID, filesystem, host, capacity, topology or enclosure is a different tier, whatever
    name it is mounted under.

    Raises:
        HostASsdQualificationError: any stable field differs.
    """
    moved = qualification.stable_tier_compatibility.differences(observation.stable)
    if moved:
        message = (
            "the live tier is not the qualified tier "
            f"{qualification.stable_tier_compatibility_identity}: "
            f"stable fields {list(moved)} differ (attachment observations are never the reason). "
            "Reauthentication is refused; nothing is copied, read as durable, or reclaimed"
        )
        raise HostASsdQualificationError(message)
    return observation


def reauthenticate_qualified_tier(
    qualification: HostASsdQualification,
    path: Path,
    *,
    provider: LiveTierProvider | None = None,
) -> LiveTierObservation:
    """Admissibility first, then a fresh measurement, then the field-for-field comparison.

    Raises:
        HostASsdQualificationError: the record does not admit a copy, the tier cannot be read,
            or the live tier is not the qualified one.
    """
    require_copy_capable(qualification)
    return require_tier_reauthentication(qualification, observe_live_tier(path, provider=provider))
