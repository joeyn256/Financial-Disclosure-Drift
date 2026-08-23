"""Decision 141 — the transport profile, and the launch conditions it is checked beside.

Every test here exists to **fail** if one specific Decision 141 protection is removed. The
governing finding is that accepted runbook §28e condition 3 -- "the SSD is **directly
connected** -- no hub" -- was false on the operator's actual hardware: the volume reaches the
host three USB hub tiers deep inside a ThinkPad Thunderbolt 4 Dock. A launch condition that
the machine can check is not left as a sentence.

The organising rule, inherited from Decision 140's file and restated because it is the reason
these tests are shaped the way they are: **a test that cannot fail proves nothing.** Nothing
here depends on the operator's SSD being attached, on a dock being present, or on any
particular machine -- every topology is synthesised through the provider seam, and the two
tests that do touch the live host are explicitly skipped when it cannot answer.
"""

from __future__ import annotations

import plistlib
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d138_safety_envelope_correction as d138  # noqa: E402

from disclosure_drift.m3 import canary_runtime as runtime  # noqa: E402
from disclosure_drift.m3 import dock_transport as dt  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402

_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID

#: Patched by string target rather than by attribute, so the seam stays typed-strict clean.
_IOREG_RUN = "disclosure_drift.m3.dock_transport.subprocess.run"


def _storage(
    *,
    vendor: int = dt.QUALIFIED_STORAGE_VENDOR_ID,
    product: int = dt.QUALIFIED_STORAGE_PRODUCT_ID,
    serial: str | None = dt.QUALIFIED_STORAGE_SERIAL,
) -> dt.UsbDevice:
    return dt.UsbDevice(vendor_id=vendor, product_id=product, serial=serial, name="SSK SSD")


def _hub(vendor: int, product: int) -> dt.UsbDevice:
    return dt.UsbDevice(vendor_id=vendor, product_id=product, serial=None, name="Hub")


def _observation(
    chain: tuple[tuple[int, int], ...],
    *,
    storage: dt.UsbDevice | None = None,
    device_identifier: str = "diskN sN",
) -> dt.TransportObservation:
    """A synthetic topology: ``chain`` is the upstream cascade, host-side first."""
    return dt.TransportObservation(
        device_identifier=device_identifier,
        storage=storage if storage is not None else _storage(),
        upstream=tuple(_hub(vendor, product) for vendor, product in chain),
    )


_DOCK = dt.QUALIFIED_DOCK_UPSTREAM_CHAIN
_THIRD_PARTY_HUB = ((0x2109, 0x0817),)


def _provider(observation: dt.TransportObservation) -> Any:
    def _resolve(_device_identifier: str) -> dt.TransportObservation:
        return observation

    return _resolve


# ==========================================================================
# A. Classification — D141-R3
# ==========================================================================
def test_the_qualified_dock_cascade_is_positively_recognised() -> None:
    """**D141-R3.** The measured topology classifies as the dock, and nothing else does."""
    assert dt.classify_transport(_observation(_DOCK)) == dt.TRANSPORT_DOCK


def test_a_direct_connection_is_recognised_and_is_not_the_dock() -> None:
    """**D141-R8.** Decision 136's topology stays qualified and stays distinct."""
    observed = dt.classify_transport(_observation(()))
    assert observed == dt.TRANSPORT_DIRECT
    assert observed != dt.TRANSPORT_DOCK


def test_the_dock_is_never_reclassified_as_direct() -> None:
    """The converse of the above, asserted rather than assumed to follow."""
    assert dt.classify_transport(_observation(_DOCK)) != dt.TRANSPORT_DIRECT


@pytest.mark.parametrize(
    "chain",
    [
        pytest.param(_THIRD_PARTY_HUB, id="an-unrelated-third-party-hub"),
        pytest.param(_DOCK[:-1], id="the-dock-cascade-one-tier-short"),
        pytest.param(_DOCK[1:], id="the-dock-cascade-missing-its-host-side-hub"),
        pytest.param((*_DOCK, *_THIRD_PARTY_HUB), id="the-dock-cascade-plus-an-extra-hub"),
        pytest.param(tuple(reversed(_DOCK)), id="the-dock-cascade-in-the-wrong-order"),
    ],
)
def test_an_unqualified_cascade_is_never_admitted(chain: tuple[tuple[int, int], ...]) -> None:
    """**D141-R5.** Qualified is the only answer that admits; everything else refuses.

    The reversed case is the one worth stating aloud: the comparison is **ordered**, so a
    cascade built from exactly the right hubs in the wrong arrangement is a different topology
    and is refused rather than accepted on set membership.
    """
    assert dt.classify_transport(_observation(chain)) == dt.TRANSPORT_UNQUALIFIED
    with pytest.raises(dt.DockTransportError, match="did not qualify"):
        dt.require_qualified_transport("diskN sN", provider=_provider(_observation(chain)))


@pytest.mark.parametrize(
    "storage",
    [
        pytest.param(_storage(vendor=0xDEAD), id="wrong-vendor"),
        pytest.param(_storage(product=0xBEEF), id="wrong-product"),
        pytest.param(_storage(serial="SSKPSSD0000000000072"), id="wrong-serial"),
        pytest.param(_storage(serial=None), id="no-serial-at-all"),
    ],
)
def test_the_right_volume_behind_the_wrong_enclosure_is_refused(storage: dt.UsbDevice) -> None:
    """**D141-R4.** The enclosure is part of the qualified transport, not incidental to it.

    A volume can be moved into a different enclosure and keep its UUID, so the UUID alone
    cannot answer *is this attached the way it was qualified?* — which is the whole question
    this module exists to ask.
    """
    observation = _observation(_DOCK, storage=storage)
    assert dt.classify_transport(observation) == dt.TRANSPORT_UNQUALIFIED
    with pytest.raises(dt.DockTransportError, match="did not qualify"):
        dt.require_qualified_transport("diskN sN", provider=_provider(observation))


# ==========================================================================
# B. Volatile identity is recorded and never decided on — D141-R7
# ==========================================================================
@pytest.mark.parametrize("identifier", ["disk4s2", "disk9s1", "disk127s3"])
def test_a_changed_bsd_disk_number_never_causes_a_refusal(identifier: str) -> None:
    """**D141-R7, and the explicit non-refusal the Decision 141 authorization requires.**

    ``disk4``/``disk4s2`` change across reboots and re-plugs. The profile is built from USB
    vendor/product identity and cascade shape, so the same hardware under a different BSD
    number is the **same** qualified transport. A guard that refused here would be a guard the
    operator learns to work around.
    """
    observation = _observation(_DOCK, device_identifier=identifier)
    assert dt.classify_transport(observation) == dt.TRANSPORT_DOCK
    admitted = dt.require_qualified_transport(identifier, provider=_provider(observation))
    assert admitted.device_identifier == identifier
    assert dict(admitted.as_record())["transport_class"] == dt.TRANSPORT_DOCK


def test_no_frozen_constant_in_the_profile_is_a_bsd_identifier() -> None:
    """The rule stated as an assertion rather than only in a docstring."""
    frozen = (
        dt.QUALIFIED_STORAGE_SERIAL,
        dt.DOCK_PRODUCT_NAME,
        *(f"0x{v:04X}:0x{p:04X}" for v, p in dt.QUALIFIED_DOCK_UPSTREAM_CHAIN),
    )
    assert not any("disk" in str(value).casefold() for value in frozen)


# ==========================================================================
# C. The narrowing assertion — D141-R6
# ==========================================================================
def test_omitting_the_assertion_admits_either_qualified_topology() -> None:
    """The authorization leaves selecting one topology to the owner, so both are admitted."""
    for chain, expected in ((_DOCK, dt.TRANSPORT_DOCK), ((), dt.TRANSPORT_DIRECT)):
        observation = _observation(chain)
        admitted = dt.require_qualified_transport("diskN sN", provider=_provider(observation))
        assert dt.classify_transport(admitted) == expected


def test_a_supplied_assertion_can_only_narrow() -> None:
    """**D141-R6.** The same shape as ``--require-volume-uuid``: it adds, it never removes."""
    dock = _provider(_observation(_DOCK))
    direct = _provider(_observation(()))
    assert dt.require_qualified_transport("d", required=dt.TRANSPORT_DOCK, provider=dock)
    assert dt.require_qualified_transport("d", required=dt.TRANSPORT_DIRECT, provider=direct)
    with pytest.raises(dt.DockTransportError, match="requires"):
        dt.require_qualified_transport("d", required=dt.TRANSPORT_DIRECT, provider=dock)
    with pytest.raises(dt.DockTransportError, match="requires"):
        dt.require_qualified_transport("d", required=dt.TRANSPORT_DOCK, provider=direct)


def test_an_assertion_naming_an_unqualified_class_is_itself_refused() -> None:
    """A demand for something Decision 141 never qualified cannot be satisfied, so it refuses."""
    with pytest.raises(dt.DockTransportError, match="not a transport"):
        dt.require_qualified_transport(
            "d", required="THUNDERBOLT", provider=_provider(_observation(_DOCK))
        )


# ==========================================================================
# D. The reader itself — D141-R2
# ==========================================================================
def _plist_tree(children: list[dict[str, Any]]) -> bytes:
    return plistlib.dumps(
        [{"IOObjectClass": "IORegistryEntry", "IORegistryEntryChildren": children}]
    )


def _usb_node(
    vendor: int, product: int, serial: str | None, children: list[dict[str, Any]]
) -> dict[str, Any]:
    node: dict[str, Any] = {
        "IOObjectClass": "IOUSBHostDevice",
        "IORegistryEntryName": "node",
        "idVendor": vendor,
        "idProduct": product,
        "IORegistryEntryChildren": children,
    }
    if serial is not None:
        node["USB Serial Number"] = serial
    return node


def _patch_ioreg(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
    class _Completed:
        stdout = payload

    monkeypatch.setattr(_IOREG_RUN, lambda *_a, **_k: _Completed())


def test_the_reader_counts_one_physical_device_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Interface and mass-storage nubs inherit the device's ids; counting them would lie.

    Left unfiltered, the real topology's four USB devices read as seven entries and the
    cascade comparison could never match. This is that filter's killer.
    """
    nub = {
        "IOObjectClass": "IOUSBMassStorageInterfaceNub",
        "idVendor": dt.QUALIFIED_STORAGE_VENDOR_ID,
        "idProduct": dt.QUALIFIED_STORAGE_PRODUCT_ID,
        "IORegistryEntryChildren": [{"IOObjectClass": "IOMedia", "BSD Name": "disk9s1"}],
    }
    tree = _plist_tree(
        [
            _usb_node(
                *_DOCK[0],
                None,
                [
                    _usb_node(
                        *_DOCK[1],
                        "000000001",
                        [
                            _usb_node(
                                *_DOCK[2],
                                "000000001",
                                [
                                    _usb_node(
                                        dt.QUALIFIED_STORAGE_VENDOR_ID,
                                        dt.QUALIFIED_STORAGE_PRODUCT_ID,
                                        dt.QUALIFIED_STORAGE_SERIAL,
                                        [nub],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ]
    )
    _patch_ioreg(monkeypatch, tree)
    observed = dt.read_usb_attachment("disk9s1")
    assert len(observed.upstream) == 3
    assert observed.upstream_chain == _DOCK
    assert observed.storage.serial == dt.QUALIFIED_STORAGE_SERIAL
    assert dt.classify_transport(observed) == dt.TRANSPORT_DOCK


def test_a_media_that_is_not_beneath_any_usb_device_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An internal NVMe volume has no USB ancestry; that is a refusal, not an empty chain."""
    _patch_ioreg(monkeypatch, _plist_tree([]))
    with pytest.raises(dt.DockTransportError, match="not present beneath any USB device"):
        dt.read_usb_attachment("disk9s1")


def test_an_unreadable_ioregistry_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    """A lookup that fails is refused, never assumed to pass — the D137-R1 rule, reused."""

    message = "ioreg is unavailable"

    def _boom(*_a: Any, **_k: Any) -> Any:
        raise OSError(message)

    monkeypatch.setattr(_IOREG_RUN, _boom)
    with pytest.raises(dt.DockTransportError, match="could not be read"):
        dt.read_usb_attachment("disk9s1")


def test_unparseable_ioregistry_output_refuses(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_ioreg(monkeypatch, b"not a property list")
    with pytest.raises(dt.DockTransportError, match="could not be read"):
        dt.read_usb_attachment("disk9s1")


# ==========================================================================
# E. The check reaches the production launch path — D141-R5, D141-R9
# ==========================================================================
def _external(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    chain: tuple[tuple[int, int], ...] = _DOCK,
    storage: dt.UsbDevice | None = None,
    on_ac: bool | None = True,
    lid_closed: bool | None = False,
) -> Path:
    """Stand ``tmp_path`` up as the synthetic qualified volume, with a settable attachment."""
    d138._external_volume(monkeypatch, tmp_path)
    monkeypatch.setattr(ewr, "transport_of", lambda _i: _observation(chain, storage=storage))
    monkeypatch.setattr(
        ewr,
        "host_power_state",
        lambda: runtime.PowerState(on_ac_power=on_ac, clamshell_closed=lid_closed),
    )
    return tmp_path / "work"


def test_the_transport_check_actually_reaches_the_production_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The reachability proof the Decision 141 authorization requires.**

    Every other test in this file could pass while the guard sat in a module nothing calls --
    which is exactly the defect Decision 141 found in ``require_launch_power_conditions``, a
    fully implemented and fully unit-tested guard that **no production path invoked**. This
    asserts the opposite property directly: the refusal is raised *through*
    ``require_external_envelope``, the one composed point all three canary modes flow through.
    """
    work = _external(monkeypatch, tmp_path, chain=_THIRD_PARTY_HUB)
    with pytest.raises(dt.DockTransportError, match="did not qualify"):
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_the_qualified_dock_passes_the_production_envelope_and_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The positive half: it admits, and the launch record states what it ran over."""
    work = _external(monkeypatch, tmp_path)
    preflight = ewr.require_external_envelope(
        work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
    )
    assert preflight is not None
    record = dict(preflight.as_record())
    assert dict(record["transport"])["transport_class"] == dt.TRANSPORT_DOCK  # type: ignore[call-overload]
    assert dict(record["power"])["on_ac_power"] is True  # type: ignore[call-overload]
    # Passing every guard is still not an authorization to launch — D137-R12, unchanged.
    assert record["canary_authorized"] is False


def test_the_same_volume_over_an_unqualified_topology_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The right UUID is not enough: identity and attachment are different questions."""
    work = _external(monkeypatch, tmp_path, chain=_THIRD_PARTY_HUB)
    with pytest.raises(dt.DockTransportError):
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_the_direct_topology_refuses_when_the_dock_profile_is_selected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The authorization's "unqualified alternate topology" case**, through production code."""
    work = _external(monkeypatch, tmp_path, chain=())
    with pytest.raises(dt.DockTransportError, match="requires"):
        ewr.require_external_envelope(
            work,
            observed_at="2026-08-23T00:00:00Z",
            asserted_uuid=_QUALIFIED,
            required_transport=dt.TRANSPORT_DOCK,
        )
    # ...and is admitted when nothing narrower is demanded, because D141 revokes nothing.
    assert (
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
        is not None
    )


def test_a_changed_bsd_number_does_not_refuse_through_the_production_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The explicit non-refusal, asserted where it matters rather than only in the unit."""
    work = _external(monkeypatch, tmp_path)
    for identifier in ("disk4s2", "disk31s7"):
        monkeypatch.setattr(
            ewr,
            "transport_of",
            lambda _i, _id=identifier: _observation(_DOCK, device_identifier=_id),
        )
        assert (
            ewr.require_external_envelope(
                work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
            )
            is not None
        )


def test_battery_power_refuses_through_the_production_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D141-R9.** The guard Decision 140 wrote and nothing called is now on the launch path."""
    work = _external(monkeypatch, tmp_path, on_ac=False)
    with pytest.raises(runtime.CanaryRuntimeError, match="battery power"):
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_a_closed_lid_refuses_through_the_production_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    work = _external(monkeypatch, tmp_path, lid_closed=True)
    with pytest.raises(runtime.CanaryRuntimeError, match="lid closed"):
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )


def test_an_unreadable_host_condition_refuses_unless_explicitly_asserted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown is not satisfied, and the escape hatch excuses unknown only."""
    work = _external(monkeypatch, tmp_path, on_ac=None)
    with pytest.raises(runtime.CanaryRuntimeError, match="could not be read"):
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
    assert (
        ewr.require_external_envelope(
            work,
            observed_at="2026-08-23T00:00:00Z",
            asserted_uuid=_QUALIFIED,
            operator_asserts_power_conditions=True,
        )
        is not None
    )
    # The assertion excuses an unreadable state; it never excuses a battery.
    work = _external(monkeypatch, tmp_path, on_ac=False)
    with pytest.raises(runtime.CanaryRuntimeError, match="battery power"):
        ewr.require_external_envelope(
            work,
            observed_at="2026-08-23T00:00:00Z",
            asserted_uuid=_QUALIFIED,
            operator_asserts_power_conditions=True,
        )


def test_the_internal_historical_path_never_reads_a_transport_or_a_power_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D141-R10.** The accepted Decision 116 internal path is byte-for-byte unchanged.

    Decision 140 was careful that an internal root costs no ``diskutil`` call; Decision 141 must
    be equally careful that it costs no ``ioreg`` and no ``pmset``. Proved by making both fatal.
    """

    def _forbidden(*_a: Any, **_k: Any) -> Any:  # pragma: no cover - proving absence
        message = "an internal root must not read the transport or the host power state"
        raise AssertionError(message)

    monkeypatch.setattr(ewr, "transport_of", _forbidden)
    monkeypatch.setattr(ewr, "host_power_state", _forbidden)
    assert (
        ewr.require_external_envelope(tmp_path / "work", observed_at="2026-08-23T00:00:00Z") is None
    )


def test_the_d130_archive_tar_is_never_opened_by_the_transport_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Decision 141 §13.** The new guard reads the IORegistry; it touches no archive byte."""
    opened: list[str] = []
    real_open = Path.open

    def _watch(self: Path, *a: Any, **k: Any) -> Any:
        opened.append(self.name)
        return real_open(self, *a, **k)

    work = _external(monkeypatch, tmp_path)
    monkeypatch.setattr(Path, "open", _watch)
    assert (
        ewr.require_external_envelope(
            work, observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
        is not None
    )
    assert ewr.D130_ARCHIVE_TAR_NAME not in opened
