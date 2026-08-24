"""Decision 144 — the D143 findings, each closed by a test that fails if the closure is removed.

The governing finding is **D143 MAJOR-1**, and it is a *production-reachability* defect rather
than a missing guard. Accepted [Decision 142] §4 selected `USB_VIA_THUNDERBOLT_DOCK` as the one
topology for the first complete-source canary and §6 forbade both automatic and operator
fallback. Decision 141 had already built the mechanism that expresses exactly that -- the
`required_transport` narrowing -- and it was correct, and it was fully unit-tested, and **no
production caller passed it**. All three seams left it at its `None` default, which
`require_qualified_transport` documents as admitting *either* qualified topology, so a directly
attached qualified SSD passed the whole envelope and would have started the first canary on an
unselected topology.

That shape is the reason this file exists rather than a few more helper assertions: it is the
*same* shape Decision 141 §3 found in `require_launch_power_conditions`, one level down. A guard
that runs proves nothing about an argument that never arrives, so **every narrowing test here is
asserted through a production entry point** -- `run_single_source_canary`,
`run_single_source_prefix_profile`, or `run_canary_source_command` -- and never against
`require_external_envelope` with the argument helpfully supplied by the test itself.

The organising rule, inherited from the Decision 140 and 141 files: **a test that cannot fail
proves nothing.** Nothing here depends on the operator's SSD being attached, on a dock being
present, or on any particular machine. Every topology is synthesised through the provider seam.
"""

from __future__ import annotations

import argparse
import ast
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d116_single_source_canary as d116  # noqa: E402
import test_d138_safety_envelope_correction as d138  # noqa: E402

from disclosure_drift.cli import build_parser  # noqa: E402
from disclosure_drift.m3 import canary_runtime as runtime  # noqa: E402
from disclosure_drift.m3 import dock_transport as dt  # noqa: E402
from disclosure_drift.m3 import external_working_root as ewr  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402

_QUALIFIED = ewr.QUALIFIED_EXTERNAL_VOLUME_UUID
_OTHER = "0BADCAFE-0000-0000-0000-000000000000"
_BULK = d116._BULK_INSTANCE

#: The three synthetic topologies, host-side first. `()` is a direct attachment -- nothing above
#: the storage device -- which is the Decision 136 class D141-R8 keeps qualified.
_DOCK = dt.QUALIFIED_DOCK_UPSTREAM_CHAIN
_DIRECT: tuple[tuple[int, int], ...] = ()
_THIRD_PARTY_HUB = ((0x2109, 0x0817),)


def _observation(
    chain: tuple[tuple[int, int], ...], *, device_identifier: str = "diskN sN"
) -> dt.TransportObservation:
    return dt.TransportObservation(
        device_identifier=device_identifier,
        storage=dt.UsbDevice(
            vendor_id=dt.QUALIFIED_STORAGE_VENDOR_ID,
            product_id=dt.QUALIFIED_STORAGE_PRODUCT_ID,
            serial=dt.QUALIFIED_STORAGE_SERIAL,
            name="SSK SSD",
        ),
        upstream=tuple(
            dt.UsbDevice(vendor_id=v, product_id=p, serial=None, name="Hub") for v, p in chain
        ),
    )


def _attach(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    chain: tuple[tuple[int, int], ...] = _DOCK,
    uuid: str = _QUALIFIED,
    on_ac: bool | None = True,
    lid_closed: bool | None = False,
    device_identifier: str = "diskN sN",
) -> Path:
    """Stand ``tmp_path`` up as the synthetic qualified volume, and return its ``SQLITE_TMPDIR``."""
    temp = d138._external_volume(monkeypatch, tmp_path, uuid=uuid)
    monkeypatch.setattr(
        ewr, "transport_of", lambda _i: _observation(chain, device_identifier=device_identifier)
    )
    monkeypatch.setattr(
        ewr,
        "host_power_state",
        lambda: runtime.PowerState(on_ac_power=on_ac, clamshell_closed=lid_closed),
    )
    return temp


def _operator(
    tmp_path: Path,
    temp: Path,
    *,
    mode: str = "preflight",
    run_id: str = "d144",
    asserted: str | None = _QUALIFIED,
    member_limit: int | None = None,
) -> Any:
    """Invoke the real operator entry point, the way `cli.py` invokes it."""
    private = d116._private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return canary.run_canary_source_command(
        mode=mode,
        run_id=run_id,
        source_instance_id=_BULK,
        work_root=str(work),
        repository_root=checkout,
        require_volume_uuid=asserted,
        environ={canary.EVIDENCE_ROOT_ENV: str(private), ewr.SQLITE_TMPDIR_ENV: str(temp)},
        member_limit=member_limit,
    )


def _complete_source(
    tmp_path: Path, *, run_id: str = "d144-run", asserted: str | None = _QUALIFIED
) -> Any:
    """Invoke the complete-source `--mode run` library entry point."""
    private = d116._private_root(tmp_path)
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return canary.run_single_source_canary(
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=work,
        run_id=run_id,
        source_instance_id=_BULK,
        require_volume_uuid=asserted,
    )


def _prefix(
    tmp_path: Path, *, run_id: str = "d144-prefix", asserted: str | None = _QUALIFIED
) -> Any:
    """Invoke the diagnostic `--mode profile-prefix` library entry point."""
    private = d116._private_root(tmp_path)
    work = tmp_path / "work"
    work.mkdir(exist_ok=True)
    return canary.run_single_source_prefix_profile(
        operational_catalog=d116._catalog(private),
        tree=DataTree.from_root(private),
        work_root=work,
        run_id=run_id,
        source_instance_id=_BULK,
        member_limit=1,
        require_volume_uuid=asserted,
    )


# ==========================================================================
# A. The selected topology is narrowed by the PRODUCTION path — D144-R1
# ==========================================================================
def test_the_selection_is_the_accepted_one_and_is_not_a_second_opinion() -> None:
    """The constant *is* Decision 142 §4's class, not a copy of its spelling."""
    assert canary.FIRST_CANARY_REQUIRED_TRANSPORT == dt.TRANSPORT_DOCK
    assert canary.FIRST_CANARY_REQUIRED_TRANSPORT == "USB_VIA_THUNDERBOLT_DOCK"


def test_no_production_envelope_call_omits_the_transport_narrowing() -> None:
    """**The recurrence killer for MAJOR-1**, asserted on the source rather than on behaviour.

    MAJOR-1 was not a wrong argument; it was an **absent** one, at every call site at once. A
    fourth seam added later without the narrowing would reintroduce it in exactly the way the
    behavioural tests below cannot see, because they only exercise the three that exist. This
    reads the module and requires the pin at *every* call, present and future.
    """
    tree = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "require_external_envelope"
    ]
    # Three at Decision 144, four since accepted **Decision 145** added
    # `run_single_source_canary_phase` -- and this assertion is *why* that seam was reviewed for
    # the narrowing rather than merely written. It fired, the seam was checked, and it carries
    # `FIRST_CANARY_REQUIRED_TRANSPORT` like the other three; the loop below re-proves it.
    assert len(calls) == 4, "the production seam count changed; each one needs the narrowing"
    for call in calls:
        pinned = [
            keyword
            for keyword in call.keywords
            if keyword.arg == "required_transport"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "FIRST_CANARY_REQUIRED_TRANSPORT"
        ]
        assert pinned, f"the envelope call at line {call.lineno} does not narrow the transport"


def test_the_narrowing_actually_reaches_the_composed_envelope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The argument arrives.** Not that a refusal happened — that the pin was *passed*.

    A refusal could in principle come from somewhere else. This watches the one function the
    narrowing is for and records what it was actually handed.
    """
    temp = _attach(monkeypatch, tmp_path)
    seen: list[str | None] = []
    real = ewr.require_qualified_transport

    def _watch(identifier: str, *, required: str | None = None, provider: Any = None) -> Any:
        seen.append(required)
        return real(identifier, required=required, provider=provider)

    monkeypatch.setattr(ewr, "require_qualified_transport", _watch)
    _operator(tmp_path, temp)
    assert seen == [dt.TRANSPORT_DOCK]


def test_the_qualified_dock_still_passes_the_production_operator_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The positive half: narrowing to the selected class admits the selected class."""
    temp = _attach(monkeypatch, tmp_path)
    outcome = _operator(tmp_path, temp)
    assert outcome.exit_code == 0
    rendered = "\n".join(outcome.lines)
    assert f'"transport_class": "{dt.TRANSPORT_DOCK}"' in rendered
    # Passing every guard is still not an authorization to launch — D137-R12, unchanged.
    assert '"canary_authorized": false' in rendered


def test_the_direct_topology_refuses_through_the_operator_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**MAJOR-1's exact case.** A qualified SSD, attached directly, at the operator surface."""
    temp = _attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError, match="requires"):
        _operator(tmp_path, temp)
    assert not (tmp_path / "work" / "d144").exists()


def test_the_direct_topology_refuses_through_the_complete_source_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first complete-source canary itself, which is what Decision 142 §4 selected for."""
    _attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError, match=dt.TRANSPORT_DOCK):
        _complete_source(tmp_path)
    assert not (tmp_path / "work" / "d144-run").exists()


def test_the_direct_topology_refuses_through_the_diagnostic_prefix(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A prefix measured over an unselected topology describes a run nobody authorized."""
    _attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError, match="requires"):
        _prefix(tmp_path)
    assert not (tmp_path / "work" / "d144-prefix").exists()


def test_an_unqualified_topology_refuses_through_the_production_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A third topology was always refused, and narrowing does not weaken that."""
    temp = _attach(monkeypatch, tmp_path, chain=_THIRD_PARTY_HUB)
    with pytest.raises(dt.DockTransportError, match="did not qualify"):
        _operator(tmp_path, temp)


def test_the_refusal_names_both_classes_so_the_operator_is_not_guessing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The message states what is attached and what is required, and refuses on the difference."""
    temp = _attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError) as raised:
        _operator(tmp_path, temp)
    message = str(raised.value)
    assert dt.TRANSPORT_DIRECT in message
    assert dt.TRANSPORT_DOCK in message
    # It refuses to run over the wrong one; it does not claim the present one is unsafe.
    assert "refusal to run over the wrong one" in message


def test_there_is_no_fallback_of_any_kind_after_a_transport_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**Decision 142 §6.** A refusal is terminal: no retry, no second class, no created state.

    The counter is owned by this test rather than by the harness, so it survives the exception
    that carries control out — the D140 MINOR-3 shape, not repeated here.
    """
    temp = _attach(monkeypatch, tmp_path, chain=_DIRECT)
    attempts: list[str | None] = []
    real = ewr.require_qualified_transport

    def _count(identifier: str, *, required: str | None = None, provider: Any = None) -> Any:
        attempts.append(required)
        return real(identifier, required=required, provider=provider)

    monkeypatch.setattr(ewr, "require_qualified_transport", _count)
    with pytest.raises(dt.DockTransportError):
        _operator(tmp_path, temp)
    # Exactly one attempt, demanding exactly the dock. A retry with `None` — or with the other
    # qualified class — is the operator fallback D142 §6 forbids, and it does not happen.
    assert attempts == [dt.TRANSPORT_DOCK]
    assert list((tmp_path / "work").iterdir()) == []


@pytest.mark.parametrize("identifier", ["disk4s2", "disk31s7", "disk99s1"])
def test_a_changed_bsd_identifier_is_still_admissible_under_the_narrowing(
    identifier: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**D141-R4 and D141-R7 survive D144.** Narrowing the class never froze a disk number."""
    temp = _attach(monkeypatch, tmp_path, device_identifier=identifier)
    assert _operator(tmp_path, temp, run_id=f"d144-{identifier}").exit_code == 0


# ==========================================================================
# B. `USB_DIRECT` remains separately qualified — D141-R8, D142 §5
# ==========================================================================
def test_both_topologies_remain_qualified_and_a_third_still_refuses() -> None:
    """The narrowing is a first-canary envelope rule, not a revocation of the direct class."""
    assert dt.QUALIFIED_TRANSPORT_CLASSES == (dt.TRANSPORT_DOCK, dt.TRANSPORT_DIRECT)
    assert dt.classify_transport(_observation(_DIRECT)) == dt.TRANSPORT_DIRECT
    assert dt.classify_transport(_observation(_DOCK)) == dt.TRANSPORT_DOCK
    assert dt.classify_transport(_observation(_THIRD_PARTY_HUB)) == dt.TRANSPORT_UNQUALIFIED


def test_the_direct_topology_still_passes_the_general_transport_requirement() -> None:
    """Asked for *a* qualified transport, a direct attachment is still one."""
    observed = dt.require_qualified_transport(
        "diskN sN", required=None, provider=lambda _i: _observation(_DIRECT)
    )
    assert dt.classify_transport(observed) == dt.TRANSPORT_DIRECT


def test_the_direct_topology_still_passes_the_general_envelope_outside_the_narrowing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**The compatibility proof.** The composed envelope admits direct when nothing narrows it.

    This is the property Decision 141 §16 (D141-R8) established and Decision 142 §5 preserved in
    terms, and D144 does not touch it: what D144 narrows is the *first-canary caller*, not the
    library. A later owner decision selecting the direct topology needs a source change here and
    nothing else.
    """
    _attach(monkeypatch, tmp_path, chain=_DIRECT)
    assert (
        ewr.require_external_envelope(
            tmp_path / "work", observed_at="2026-08-23T00:00:00Z", asserted_uuid=_QUALIFIED
        )
        is not None
    )


def test_demanding_the_direct_class_refuses_a_dock_attachment_symmetrically() -> None:
    """Neither class is privileged by the mechanism; only the caller chose one."""
    with pytest.raises(dt.DockTransportError, match="requires"):
        dt.require_qualified_transport(
            "diskN sN", required=dt.TRANSPORT_DIRECT, provider=lambda _i: _observation(_DOCK)
        )


# ==========================================================================
# C. The mandatory UUID is untouched by the narrowing — D140-R2
# ==========================================================================
def test_the_omitted_uuid_still_refuses_through_the_production_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Narrowing the transport did not move the identity assertion out of the way."""
    temp = _attach(monkeypatch, tmp_path)
    with pytest.raises(ewr.ExternalWorkingRootError, match="D140-R2"):
        _operator(tmp_path, temp, asserted=None)


def test_a_wrong_uuid_still_refuses_before_the_transport_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ordering is preserved: identity first, and the IORegistry is never consulted."""
    temp = _attach(monkeypatch, tmp_path)

    def _forbidden(*_a: Any, **_k: Any) -> Any:  # pragma: no cover - proving absence
        message = "the transport must not be read for a volume that failed identity"
        raise AssertionError(message)

    monkeypatch.setattr(ewr, "transport_of", _forbidden)
    with pytest.raises(ewr.ExternalWorkingRootError, match="not the one qualified external volume"):
        _operator(tmp_path, temp, asserted=_OTHER)


def test_the_exact_uuid_disables_no_other_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Supplying the right identity narrows and never widens — the transport still refuses."""
    temp = _attach(monkeypatch, tmp_path, chain=_DIRECT)
    with pytest.raises(dt.DockTransportError):
        _operator(tmp_path, temp, asserted=_QUALIFIED)


def test_the_exact_uuid_does_not_excuse_battery_power(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The same property against the D141-R9 guard, so "narrows only" is proved twice."""
    temp = _attach(monkeypatch, tmp_path, on_ac=False)
    with pytest.raises(runtime.CanaryRuntimeError, match="battery power"):
        _operator(tmp_path, temp)


def test_the_exact_uuid_does_not_excuse_a_closed_lid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """And against the lid half of it."""
    temp = _attach(monkeypatch, tmp_path, lid_closed=True)
    with pytest.raises(runtime.CanaryRuntimeError, match="lid closed"):
        _operator(tmp_path, temp)


# ==========================================================================
# D. The operator-facing CLI text — MINOR-1
# ==========================================================================
def _subparser(parser: argparse.ArgumentParser, name: str) -> argparse.ArgumentParser:
    """The named child parser of ``parser``, or fail the test."""
    for action in parser._actions:  # noqa: SLF001 - argparse exposes no public walk
        choices = getattr(action, "choices", None)
        if isinstance(choices, Mapping) and name in choices:
            child = choices[name]
            assert isinstance(child, argparse.ArgumentParser)
            return child
    message = f"no subparser named {name!r}"
    raise AssertionError(message)


def _uuid_flag_help() -> str:
    """The rendered help for `--require-volume-uuid`, read from the real parser."""
    canary_parser = _subparser(_subparser(build_parser(), "m3"), "canary-source")
    for argument in canary_parser._actions:  # noqa: SLF001 - argparse exposes no public walk
        if argument.dest == "require_volume_uuid":
            assert argument.help is not None
            return argument.help
    message = "--require-volume-uuid is no longer a registered flag"
    raise AssertionError(message)


def test_the_cli_help_states_the_uuid_assertion_is_mandatory() -> None:
    """**MINOR-1.** The flag's own text now says what the code has done since Decision 140.

    Decision 142 §9 corrected this meaning in two runbook places and could not reach this one,
    because the text lives in `src/`. It is the operator-facing surface closest to the moment
    the mistake is made, so it is the one that most needs to be true.
    """
    text = _uuid_flag_help()
    assert "MANDATORY" in text
    assert "OMITTING IT IS ITSELF A REFUSAL" in text
    assert "D140-R2" in text


def test_the_cli_help_no_longer_frames_omission_as_harmless() -> None:
    """The killer for the regression, stated as the absence of the exact pre-D140 framing."""
    text = _uuid_flag_help()
    assert "whether or not this is supplied" not in text
    assert "Omitting it cannot disable a single guard" not in text


def test_the_cli_help_still_protects_the_internal_historical_contract() -> None:
    """**Not weakened accidentally.** An internal root has a different, unchanged contract."""
    text = _uuid_flag_help()
    assert "Decision 116 historical path, unchanged" in text
    assert "not required for it" in text


def test_the_flag_stays_optional_at_the_parser_so_the_internal_path_is_reachable() -> None:
    """Mandatory *on an external route* is not the same as argparse-required.

    Making it `required=True` would refuse the accepted Decision 116 internal path, which needs
    no assertion and never did. The refusal belongs where the externality is known, and that is
    the envelope — which is exactly where it lives.
    """
    parser = build_parser()
    parsed = parser.parse_args(
        [
            "m3",
            "canary-source",
            "--mode",
            "preflight",
            "--source-instance-id",
            "x",
            "--run-id",
            "y",
            "--work-root",
            "/nonexistent/work-root",
        ]
    )
    assert parsed.require_volume_uuid is None


# ==========================================================================
# E. The internal historical path is untouched — D141-R10, D143 OBSERVATION-2
# ==========================================================================
def test_the_internal_path_reads_no_transport_or_power_through_the_production_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**OBSERVATION-2, closed by proof rather than by assertion.**

    D143 recorded that the envelope's guards apply only where the envelope applies, so that a
    future internal-root canary is not assumed to inherit them. D144 adds a narrowing argument
    to all three production callers, and the question that raises is whether the internal path
    now pays for it. It does not: `require_external_envelope` returns `None` for a root with no
    external requirement **before** the transport is consulted, and the narrowing is a module
    constant rather than a reading. Proved the way D141-R10 proved it — by making both fatal.
    """

    def _forbidden(*_a: Any, **_k: Any) -> Any:  # pragma: no cover - proving absence
        message = "an internal root must not read the transport or the host power state"
        raise AssertionError(message)

    monkeypatch.setattr(ewr, "transport_of", _forbidden)
    monkeypatch.setattr(ewr, "host_power_state", _forbidden)
    private = d116._private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    outcome = canary.run_canary_source_command(
        mode="preflight",
        run_id="d144-internal",
        source_instance_id=_BULK,
        work_root=str(tmp_path / "work"),
        repository_root=checkout,
        environ={canary.EVIDENCE_ROOT_ENV: str(private)},
    )
    assert outcome.exit_code == 0
