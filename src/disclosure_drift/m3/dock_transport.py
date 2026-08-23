"""How the qualified external volume is **attached**, proved rather than assumed.

**What this module is for.** Accepted Decision 136 qualified *which* volume the corrected
complete-source canary may run on, and Decisions 137, 138 and 140 built the fail-closed envelope
around *that volume*. None of them asked how the volume reaches the host. Decision 136 assumed a
direct connection and the operator runbook stated it as a launch condition -- "the SSD is
**directly connected** -- no hub". **Decision 141** measured the operator's actual topology and
found that condition false: the SSD now reaches the host through a ThinkPad Thunderbolt 4 Dock,
three USB hub tiers deep. This module is the machinery that makes the attachment a *proved*
launch condition instead of a sentence in a runbook.

**Why it is a module of its own.** The separation
:mod:`~disclosure_drift.m3.canary_runtime` already argues for holds here too.
:mod:`~disclosure_drift.m3.external_working_root` answers questions about *the volume* -- which
one is this, how much room is left, is the archive intact.
:mod:`~disclosure_drift.m3.canary_runtime` answers questions about *the host* -- power, lid, is
another canary running. Neither answers what sits on the wire **between** them, and folding a
USB-topology walk into either would put a third unrelated subsystem behind an existing import.

**The Volume UUID remains the primary identity.** Nothing here weakens, replaces, or stands in
for it. Accepted Decision 136's `397A4D4A-9508-391E-814E-3B533C7BD049` is still the one identity
a working root is authenticated against; the transport profile is a **second, narrower** launch
condition that asks a different question -- *is that volume attached the way it was qualified?*

**Stable identity only.** The BSD identifiers ``disk4`` and ``disk4s2`` are attach-time names
that change across reboots and re-plugs, so **no** value frozen in this module is one. The
current identifier is used as a momentary *lookup key* -- it is read from the volume that has
already been authenticated by UUID, and it is never compared against anything. What is compared
is the USB vendor/product identity of the storage device and of every hub above it, which are
properties of the hardware rather than of this boot. IORegistry entry ids and ``locationID``
values are likewise recorded as evidence and decided on by nothing.

**What a matching transport does not prove.** It proves the volume is attached the way Decision
141 qualified it. It does not prove the dock, its cables, its bridge, or the SSD cannot fail; it
does not convert ExFAT into a journaled filesystem; and it does not extend accepted Decision 136
§11 (D136-R8) beyond the one canary that exception already covers. Decision 141 §12 records what
the bounded qualification did and did not establish.

The controlling records are, under ``Docs/Decisions/``:
``decision_136_m3_3_external_ssd_active_volume_qualification.md``,
``decision_140_m3_3_total_pre_canary_hardening.md``, and
``decision_141_m3_3_thunderbolt_dock_qualification.md``.
"""

from __future__ import annotations

import plistlib
import subprocess
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "DOCK_PRODUCT_NAME",
    "DOCK_THUNDERBOLT_DEVICE_ID",
    "DOCK_THUNDERBOLT_VENDOR_ID",
    "QUALIFIED_DOCK_UPSTREAM_CHAIN",
    "QUALIFIED_STORAGE_PRODUCT_ID",
    "QUALIFIED_STORAGE_SERIAL",
    "QUALIFIED_STORAGE_VENDOR_ID",
    "QUALIFIED_TRANSPORT_CLASSES",
    "TRANSPORT_DIRECT",
    "TRANSPORT_DOCK",
    "TRANSPORT_UNQUALIFIED",
    "DockTransportError",
    "TransportObservation",
    "TransportProvider",
    "UsbDevice",
    "classify_transport",
    "read_usb_attachment",
    "require_qualified_transport",
]


class DockTransportError(DisclosureDriftError):
    """Raised when the qualified volume is not attached the way Decision 141 qualified it."""


# --------------------------------------------------------------------------- #
# The three transport classes -- D141-R3
# --------------------------------------------------------------------------- #
#: The **Decision 141** topology: the SSD reaches the host as a USB mass-storage device through
#: the ThinkPad Thunderbolt 4 Dock's internal hub cascade, which is itself tunnelled over a
#: 40 Gb/s USB4 link.
#:
#: The name says ``USB_VIA`` rather than ``THUNDERBOLT`` deliberately, and the distinction is the
#: whole point of Decision 141 §4. The dock is a genuine Thunderbolt 4 device and macOS reports
#: its upstream link at 40 Gb/s -- but it negotiated ``usb_four`` mode, its downstream
#: Thunderbolt receptacle is empty, and ``diskutil`` reports the volume's own ``BusProtocol`` as
#: ``USB``. Calling this "Thunderbolt storage" because the dock's product name contains the word
#: would be exactly the inference Decision 141 §4 forbids.
TRANSPORT_DOCK: Final = "USB_VIA_THUNDERBOLT_DOCK"

#: The **Decision 136** topology: the SSD plugged straight into the host, with no hub between.
#:
#: Decision 141 does **not** revoke it (D141-R8). It remains a recognized qualified transport, it
#: is never reclassified as the dock, and an owner who returns to it does not thereby lose the
#: envelope.
TRANSPORT_DIRECT: Final = "USB_DIRECT"

#: Anything else. Not a topology this repository has qualified, and therefore a refusal.
TRANSPORT_UNQUALIFIED: Final = "UNQUALIFIED"

#: The transports a corrected complete-source canary may run over. Membership is the whole test:
#: there is no "probably fine" third answer, because **qualified is the only answer that admits**.
QUALIFIED_TRANSPORT_CLASSES: Final = (TRANSPORT_DOCK, TRANSPORT_DIRECT)


# --------------------------------------------------------------------------- #
# The frozen Decision 141 profile -- D141-R4
# --------------------------------------------------------------------------- #
#: The qualified storage device's USB vendor identity, ``0x090C`` (SSK Corporation).
QUALIFIED_STORAGE_VENDOR_ID: Final = 0x090C

#: The qualified storage device's USB product identity, ``0x2320``.
QUALIFIED_STORAGE_PRODUCT_ID: Final = 0x2320

#: The qualified storage device's USB serial number.
#:
#: A per-unit hardware identifier of the enclosure, in the same class of fact as the Volume UUID
#: accepted Decision 136 already publishes, and not a credential. It is required because the
#: vendor/product pair alone identifies a *model* rather than *this* device.
QUALIFIED_STORAGE_SERIAL: Final = "SSKPSSD0000000000071"

#: The dock's USB hub cascade above the storage device, **host-side first** -- D141-R4.
#:
#: Read from the operator's live topology on 2026-08-23 and frozen here:
#:
#: * ``0x8087:0x0B40`` -- the Intel hub on the dock's USB4 side, the first device below the
#:   Mac's own USB host controller;
#: * ``0x17EF:0x30B6`` -- the first Lenovo hub tier;
#: * ``0x17EF:0x30B8`` -- the second Lenovo hub tier, which the SSD hangs from.
#:
#: **The comparison is exact and ordered**, which is a deliberate constraint rather than an
#: oversight. Decision 141 qualified the SSD on *one* dock port; a different port on the same
#: dock produces a different cascade, and a cascade this profile has not seen is a topology this
#: repository has not qualified. Runbook §28f therefore names the port as a launch condition, and
#: a refusal here is repaired by restoring the qualified port -- never by relaxing this tuple.
QUALIFIED_DOCK_UPSTREAM_CHAIN: Final = (
    (0x8087, 0x0B40),
    (0x17EF, 0x30B6),
    (0x17EF, 0x30B8),
)

#: The dock's Thunderbolt-side vendor identity, ``0x17EF`` (Lenovo). **Evidence, not a
#: predicate**: reading it costs a ``system_profiler`` subprocess, and the USB cascade above
#: already establishes that this exact dock is between the host and the volume. Decision 141 §6
#: keeps the launch check to the one cheap ``ioreg`` call.
DOCK_THUNDERBOLT_VENDOR_ID: Final = 0x17EF

#: The dock's Thunderbolt-side device identity, ``0x30B3``. Evidence, not a predicate.
DOCK_THUNDERBOLT_DEVICE_ID: Final = 0x30B3

#: What macOS calls the dock. Recorded so a report is readable; decided on by nothing, because a
#: product name is the one attribute a different device can trivially claim.
DOCK_PRODUCT_NAME: Final = "ThinkPad Thunderbolt 4 Dock"

_IOREG: Final = "/usr/sbin/ioreg"
_USB_DEVICE_CLASS: Final = "IOUSBHostDevice"


@dataclass(frozen=True, slots=True)
class UsbDevice:
    """One USB device on the path from the host controller to the storage media."""

    vendor_id: int
    product_id: int
    serial: str | None
    name: str

    @property
    def identity(self) -> tuple[int, int]:
        """The ``(vendor, product)`` pair every comparison in this module is made on."""
        return (self.vendor_id, self.product_id)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic rendering carrying no absolute path."""
        return {
            "vendor_id": f"0x{self.vendor_id:04X}",
            "product_id": f"0x{self.product_id:04X}",
            "serial": self.serial,
            "name": self.name,
        }


@dataclass(frozen=True, slots=True)
class TransportObservation:
    """How one already-authenticated volume is attached, as read from the IORegistry.

    :attr:`upstream` is **host-side first** and excludes the storage device itself, so an empty
    tuple means "nothing between the host controller and the disk" -- the Decision 136 direct
    topology -- rather than "not measured". A measurement that could not be taken raises;
    it never becomes an empty tuple.
    """

    #: The BSD identifier the walk was keyed on. Recorded for the report and **decided on by
    #: nothing**: it is an attach-time name, and Decision 141 §5 forbids depending on one.
    device_identifier: str
    storage: UsbDevice
    upstream: tuple[UsbDevice, ...]

    @property
    def upstream_chain(self) -> tuple[tuple[int, int], ...]:
        """The ordered ``(vendor, product)`` pairs above the storage device, host-side first."""
        return tuple(device.identity for device in self.upstream)

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free rendering."""
        return {
            "device_identifier": self.device_identifier,
            "storage": dict(self.storage.as_record()),
            "upstream": [dict(device.as_record()) for device in self.upstream],
            "transport_class": classify_transport(self),
        }


#: How a transport observation is obtained for an already-authenticated volume.
#:
#: Substituting one is **the** test seam, for the same reason
#: :data:`~disclosure_drift.m3.external_working_root.VolumeIdentityProvider` exists: no test in
#: this repository may depend on the operator's SSD being attached, let alone attached through a
#: particular dock. Every guard below resolves :func:`read_usb_attachment` from module globals at
#: call time rather than binding it as a default argument, so a substitution reaches the composed
#: preflight and the run path too.
TransportProvider = Callable[[str], TransportObservation]


def _usb_device(node: Mapping[str, Any]) -> UsbDevice | None:
    """``node`` as a :class:`UsbDevice`, or ``None`` when it is not a USB device node.

    Only nodes whose registry class is exactly ``IOUSBHostDevice`` qualify. The interface and
    mass-storage nubs beneath a device inherit its ``idVendor``/``idProduct``, so matching on
    those properties alone would count the same physical device three times and turn a two-hub
    cascade into a five-entry chain.
    """
    if node.get("IOObjectClass") != _USB_DEVICE_CLASS:
        return None
    vendor = node.get("idVendor")
    product = node.get("idProduct")
    if not isinstance(vendor, int) or not isinstance(product, int):
        return None
    serial = node.get("USB Serial Number")
    return UsbDevice(
        vendor_id=vendor,
        product_id=product,
        serial=serial if isinstance(serial, str) else None,
        name=str(node.get("IORegistryEntryName", "")),
    )


def _find_media(
    node: Mapping[str, Any], device_identifier: str, chain: tuple[UsbDevice, ...]
) -> tuple[UsbDevice, ...] | None:
    """The USB chain from the host controller down to ``device_identifier``'s media, or ``None``.

    Walking **downward** and accumulating is what makes the ancestry available at all: the
    plist ``ioreg`` emits is a tree of children, so a node cannot be asked for its parents.
    """
    device = _usb_device(node)
    here = (*chain, device) if device is not None else chain
    if node.get("BSD Name") == device_identifier:
        return here
    for child in node.get("IORegistryEntryChildren") or ():
        if isinstance(child, dict):
            found = _find_media(child, device_identifier, here)
            if found is not None:
                return found
    return None


def read_usb_attachment(device_identifier: str) -> TransportObservation:
    """Read how the volume behind ``device_identifier`` is attached -- D141-R2.

    ``ioreg -a`` emits a **property list**, and it is parsed as one. The human-oriented ``ioreg``
    table is never parsed, for the same reason
    :func:`~disclosure_drift.m3.external_working_root.macos_volume_identity` never parses the
    ``diskutil info`` table: a structured form exists, so the fragile one is not used.

    The subtree is rooted at every ``IOUSBHostDevice`` rather than at the whole IOService plane,
    which keeps the reading to a few hundred kilobytes and a few tens of milliseconds -- cheap
    enough to be a launch precondition.

    Args:
        device_identifier: The BSD identifier of the **already UUID-authenticated** volume, used
            purely as a lookup key. Passing an unauthenticated one would prove nothing, which is
            why no caller in this repository derives it from anything but an admitted volume.

    Raises:
        DockTransportError: the IORegistry could not be read or parsed, the media is not present
            beneath any USB device, or it is present but no USB device sits above it. Every one
            of those is refused rather than reported as an empty or partial topology.
    """
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell, no operator input
            [_IOREG, "-a", "-p", "IOService", "-r", "-c", _USB_DEVICE_CLASS, "-l", "-w0"],
            capture_output=True,
            check=True,
            timeout=60,
        )
        parsed = plistlib.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
        message = (
            f"the USB attachment of the qualified volume could not be read "
            f"({type(exc).__name__}); a transport that cannot be identified is refused, never "
            "assumed to be the one Decision 141 qualified"
        )
        raise DockTransportError(message) from exc
    roots: Sequence[Any] = parsed if isinstance(parsed, list) else [parsed]
    chain: tuple[UsbDevice, ...] | None = None
    for root in roots:
        if isinstance(root, dict):
            chain = _find_media(root, device_identifier, ())
            if chain is not None:
                break
    if chain is None:
        message = (
            "the qualified volume's media is not present beneath any USB device in the "
            "IORegistry; the volume is not attached the way Decision 141 qualified it, so the "
            "run is refused rather than started over an unproved transport"
        )
        raise DockTransportError(message)
    if not chain:
        message = (
            "the qualified volume's media was located but no USB device sits above it; a "
            "topology with no identifiable storage device is refused rather than admitted"
        )
        raise DockTransportError(message)
    return TransportObservation(
        device_identifier=device_identifier, storage=chain[-1], upstream=chain[:-1]
    )


def classify_transport(observation: TransportObservation) -> str:
    """Which of the three classes ``observation`` is -- D141-R3.

    Read in order, because each answer is only meaningful once the earlier one has been ruled
    out:

    * the storage device is not the qualified one -> :data:`TRANSPORT_UNQUALIFIED`. The right
      volume behind the wrong enclosure is a different piece of hardware, whatever its UUID says;
    * nothing sits above it -> :data:`TRANSPORT_DIRECT`, the Decision 136 topology;
    * exactly the frozen dock cascade sits above it -> :data:`TRANSPORT_DOCK`;
    * anything else -> :data:`TRANSPORT_UNQUALIFIED`.

    **Direct is never reclassified as the dock and the dock is never reclassified as direct**
    (D141-R8): the two are distinguished by the presence and identity of the cascade, so the only
    way to be classified as the dock is to actually be behind it.
    """
    storage = observation.storage
    if storage.identity != (QUALIFIED_STORAGE_VENDOR_ID, QUALIFIED_STORAGE_PRODUCT_ID):
        return TRANSPORT_UNQUALIFIED
    if storage.serial != QUALIFIED_STORAGE_SERIAL:
        return TRANSPORT_UNQUALIFIED
    if not observation.upstream:
        return TRANSPORT_DIRECT
    if observation.upstream_chain == QUALIFIED_DOCK_UPSTREAM_CHAIN:
        return TRANSPORT_DOCK
    return TRANSPORT_UNQUALIFIED


def require_qualified_transport(
    device_identifier: str,
    *,
    required: str | None = None,
    provider: TransportProvider | None = None,
) -> TransportObservation:
    """Refuse a launch over a transport Decision 141 did not qualify -- D141-R5.

    Three outcomes, one of which is a pass:

    * the observed class is one of :data:`QUALIFIED_TRANSPORT_CLASSES`, and either no specific
      one was demanded or the demanded one matches -> **pass**;
    * the observed class is not qualified -> **refused**;
    * a specific class was demanded and a *different* qualified one is present -> **refused**.

    ``required`` is an **assertion that can only narrow**, in the same shape as
    ``--require-volume-uuid`` (D138-R12): omitting it admits either qualified topology, and
    supplying it admits exactly one. It is deliberately not an operator flag: the Decision 141
    authorization leaves the selection of *one* topology for the real canary to the owner
    (Decision 141 §16), so the repository recognizes both and refuses a third rather than
    pre-empting that choice.

    Args:
        device_identifier: The BSD identifier of the already UUID-authenticated volume.
        required: The one qualified class to demand, or ``None`` for either.
        provider: How the observation is obtained. Substituted in tests.

    Raises:
        DockTransportError: the transport is not qualified, is not the demanded one, or could
            not be read at all.
    """
    if required is not None and required not in QUALIFIED_TRANSPORT_CLASSES:
        message = (
            f"{required!r} is not a transport Decision 141 qualified; the qualified classes are "
            f"{', '.join(QUALIFIED_TRANSPORT_CLASSES)}"
        )
        raise DockTransportError(message)
    resolve = read_usb_attachment if provider is None else provider
    observation = resolve(device_identifier)
    observed = classify_transport(observation)
    if observed not in QUALIFIED_TRANSPORT_CLASSES:
        message = (
            "the qualified volume is attached over a transport Decision 141 did not qualify. "
            "The accepted topologies are the ThinkPad Thunderbolt 4 Dock cascade and a direct "
            "connection; the volume is presently behind neither, so the run is refused. Restore "
            "the qualified attachment -- the same dock, the same dock port, the same cables -- "
            "rather than relaxing the profile"
        )
        raise DockTransportError(message)
    if required is not None and observed != required:
        message = (
            f"the qualified volume is attached over {observed}, and this run requires "
            f"{required}. Both are transports Decision 141 recognizes, so this is a refusal to "
            "run over the wrong one rather than a claim that the present one is unsafe"
        )
        raise DockTransportError(message)
    return observation
