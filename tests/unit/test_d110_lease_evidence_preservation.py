"""Writer-lease evidence preservation (accepted Decision 110 §5, Workstream A).

D109 finding **F2**, accepted MAJOR: ordinary :class:`CatalogWriter` acquisition could overwrite
a persisted ``held`` lease as soon as it obtained a *free* advisory ``flock``, and it did so
**before** the ordinary create-once predicates refused the attempt. The two signals disagree by
construction — ``flock`` lives on the open file description and the kernel drops it the instant a
process dies, so a SIGKILL-class death (a jetsam memory-pressure kill, ``kill -9``, power loss)
leaves the lock free while the document on disk still records ``held``. That is precisely how the
interrupted M3.3-E0 v2 run's stale lease was destroyed 3.96 seconds after the kernel killed it,
and with it the only surviving record of how that run ended.

The invariant these tests hold: **an existing persisted ``held`` or structurally invalid lease is
never overwritten by ordinary writer acquisition merely because the advisory lock is free.** Only
the governed Decision 103 R3 stale-writer reconciliation may record ``held -> released``.

Every test drives production code over a **disposable** SQLite catalog beneath a **synthetic**
temporary root. Nothing here resolves, opens, names, prints, or infers the accepted private
evidence root; nothing opens the accepted operational catalog; and nothing reads, writes, or
approximates the real lease. Two conventions carry the weight:

**Refusal is proved on bytes, not on return values.** Every refusal test captures the lease file's
exact bytes beforehand and compares them afterwards, because "it raised" and "it changed nothing"
are different claims and only the second is the invariant.

**A real dead process, not an invented number.** Where a test needs a writer that is provably
gone, it uses the PID of a subprocess this module started and reaped, so ``os.kill(pid, 0)``
answers from the kernel rather than from a guess about which numbers are unused.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from disclosure_drift.errors import SingleWriterViolationError
from disclosure_drift.m3 import e0
from disclosure_drift.m3.receipt import RUN_NAMESPACE_DIRNAME
from disclosure_drift.storage import catalog as catalog_module
from disclosure_drift.storage.catalog import (
    LEASE_STATE_HELD,
    LEASE_STATE_RELEASED,
    STALE_LEASE_RECONCILIATION_REASON,
    CatalogWriter,
    LeaseFormatError,
    host_fingerprint,
    lease_path,
    read_persisted_lease,
    strictly_read_only_connection,
    writer_process_is_alive,
)
from disclosure_drift.storage.sqlite import apply_migrations, connect

_ACQUIRED = "2026-08-16T21:45:35.818376Z"
_EXPIRES = "2026-08-16T22:00:35.818376Z"
_FAR_FUTURE = "2099-01-01T00:00:00Z"

#: A synthetic evidence-root value that is *not* read from the ambient environment.
_SYNTHETIC_ROOT_MARKER = "synthetic-private-root"


# ==========================================================================
# Fixtures: a disposable catalog, a synthetic root, and a genuinely dead PID
# ==========================================================================


@dataclass(frozen=True, slots=True)
class _Sec:
    requests_per_second: float = 1.0
    burst: int = 1
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0
    bulk_read_timeout_seconds: float = 300.0
    max_retries: int = 3
    cooldown_seconds: float = 1.0


@dataclass(frozen=True, slots=True)
class _Network:
    enabled: bool = False
    m3_acquire_enabled: bool = False


@dataclass(frozen=True, slots=True)
class _Config:
    sec: _Sec = _Sec()
    network: _Network = _Network()


@pytest.fixture
def config() -> _Config:
    return _Config()


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    """A synthetic private root. Never the accepted one, and never read from the environment."""
    root = tmp_path / _SYNTHETIC_ROOT_MARKER
    root.mkdir()
    (root / "catalogs").mkdir()
    (root / RUN_NAMESPACE_DIRNAME).mkdir()
    return root


@pytest.fixture
def catalog(evidence_root: Path) -> Path:
    """A disposable catalog at the accepted head, built from the packaged migrations."""
    path = evidence_root / e0.OPERATIONAL_CATALOG_RELATIVE_PATH
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
    return path


@pytest.fixture(scope="module")
def dead_pid() -> int:
    """A PID whose process this module started and reaped, so it is provably not alive."""
    process = subprocess.Popen([sys.executable, "-c", "pass"])  # noqa: S603
    process.wait()
    assert not writer_process_is_alive(process.pid)
    return process.pid


@pytest.fixture
def activated_recovery(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Drive the governed recovery against a disposable token, never the shipped one."""
    monkeypatch.setattr(e0, "STALE_WRITER_LEASE_RECOVERY_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    yield


def _lease_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "lease_id": "4a327881f6424d5ea0b32136ba5e3b46",
        "writer_pid": 1,
        "host_fingerprint": host_fingerprint(),
        "acquired_at_utc": _ACQUIRED,
        "expires_at_utc": _EXPIRES,
        "state": LEASE_STATE_HELD,
    }
    payload.update(overrides)
    return payload


def _write_lease(catalog: Path, **overrides: object) -> Path:
    """Write a lease document beside ``catalog`` at mode ``0600`` and return its path."""
    path = lease_path(catalog.parent)
    path.write_bytes(json.dumps(_lease_payload(**overrides), sort_keys=True).encode("utf-8"))
    path.chmod(0o600)
    return path


def _write_raw_lease(catalog: Path, raw: bytes) -> Path:
    """Put exactly ``raw`` at the lease path beside ``catalog``."""
    path = lease_path(catalog.parent)
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


def _acquire(catalog: Path) -> CatalogWriter:
    return CatalogWriter(catalog, catalog.parent)


def _refuses_without_touching(catalog: Path, expected: type[Exception], match: str) -> None:
    """Assert acquisition refuses with ``expected`` and the lease's bytes are exactly unchanged.

    Both halves matter and only together: a refusal that still truncated the document would
    satisfy the first assertion and destroy the evidence the refusal exists to protect.
    """
    path = lease_path(catalog.parent)
    before = path.read_bytes()
    with pytest.raises(expected, match=match):
        _acquire(catalog).__enter__()
    assert path.read_bytes() == before


# ==========================================================================
# A1-A2: acquisition that was always legitimate stays legitimate
# ==========================================================================


def test_a1_an_absent_lease_still_permits_ordinary_acquisition(catalog: Path) -> None:
    """**A1.** No document means nothing to preserve, so the first writer proceeds.

    This is the ordinary first-acquisition case and the crash-between-``open``-and-``write``
    case at once: ``O_CREAT`` leaves a zero-length file, and a zero-length file is the absence
    of a lease rather than a malformed one.
    """
    path = lease_path(catalog.parent)
    assert not path.exists()

    with _acquire(catalog) as writer:
        assert writer.lease.lease_id
        assert read_persisted_lease(path.read_bytes()).state == LEASE_STATE_HELD

    assert read_persisted_lease(path.read_bytes()).state == LEASE_STATE_RELEASED


def test_a1_a_zero_length_lease_file_is_absence_not_corruption(catalog: Path) -> None:
    """**A1**, the other way in: an empty file is what ``O_CREAT`` itself leaves behind."""
    path = _write_raw_lease(catalog, b"")

    with _acquire(catalog) as writer:
        assert writer.lease.lease_id
    assert read_persisted_lease(path.read_bytes()).state == LEASE_STATE_RELEASED


def test_a2_a_valid_released_lease_permits_ordinary_acquisition(catalog: Path) -> None:
    """**A2.** ``released`` is the one state that clears the gate, and it still clears it."""
    _write_lease(catalog, state=LEASE_STATE_RELEASED, released_at_utc=_EXPIRES)

    with _acquire(catalog) as writer:
        assert writer.lease.lease_id != "4a327881f6424d5ea0b32136ba5e3b46"


def test_a2_a_governed_reconciled_release_permits_ordinary_acquisition(catalog: Path) -> None:
    """**A2**, applied to the release form the governed recovery writes.

    The Decision 103 R4 reconciled document records ``released`` with provenance fields and
    deliberately *without* ``released_at_utc``. The acquisition gate must read it as released —
    if it did not, a completed governed recovery would leave the catalog permanently unwritable,
    which is the failure mode the recovery exists to end.
    """
    _write_lease(
        catalog,
        state=LEASE_STATE_RELEASED,
        reconciliation_reason=STALE_LEASE_RECONCILIATION_REASON,
        reconciled_at_utc=_EXPIRES,
        reconciled_prior_state=LEASE_STATE_HELD,
    )

    with _acquire(catalog) as writer:
        assert writer.lease.lease_id


# ==========================================================================
# A3-A6: every refusal, proved on the bytes
# ==========================================================================


def test_a3_a_held_lease_refuses_even_though_the_advisory_lock_is_free(catalog: Path) -> None:
    """**A3.** The free lock is the whole point: it is what used to authorize the overwrite."""
    path = _write_lease(catalog)

    # The lock genuinely is free. Nothing here is racing a live writer.
    with catalog_module.exclusive_lease_lock(path, writable=False):
        pass

    _refuses_without_touching(catalog, SingleWriterViolationError, "records 'held'")


def test_a4_a_dead_and_expired_held_lease_still_refuses(catalog: Path, dead_pid: int) -> None:
    """**A4.** The exact accepted interruption residue, and every excuse for taking it.

    ``held``, expired a quarter of an hour ago, recorded on *this* host, and naming a writer the
    kernel confirms is gone. Each of those was a reason the old code could feel safe overwriting
    it; each of them is also true of every lease a jetsam kill leaves behind. Deciding this case
    is the governed reconciliation's job, and refusing is how the evidence reaches it.
    """
    _write_lease(catalog, writer_pid=dead_pid)
    assert not writer_process_is_alive(dead_pid)

    _refuses_without_touching(catalog, SingleWriterViolationError, "records 'held'")


def test_a4_an_unexpired_held_lease_refuses_on_the_same_ground(catalog: Path) -> None:
    """**A4**, the complement: expiry is not what decides this, so neither is its absence."""
    _write_lease(catalog, expires_at_utc=_FAR_FUTURE)

    _refuses_without_touching(catalog, SingleWriterViolationError, "records 'held'")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(b"not json at all", "not readable UTF-8 JSON", id="not-json"),
        pytest.param(b"[]", "not a JSON object", id="not-an-object"),
        pytest.param(b'{"state": "held"}', "missing required field", id="missing-fields"),
        pytest.param(b"\xff\xfe", "not readable UTF-8 JSON", id="not-utf8"),
    ],
)
def test_a5_a_malformed_lease_refuses_and_is_preserved(
    catalog: Path, raw: bytes, expected: str
) -> None:
    """**A5.** A document whose meaning cannot be accounted for is not proof the catalog is free.

    Decision 105 established this for the E0 predicates; Decision 110 extends it to the one gate
    that reaches bytes before any predicate runs. Note what refusing buys: the malformed document
    survives for a human to look at, which is impossible once it has been truncated.
    """
    _write_raw_lease(catalog, raw)

    _refuses_without_touching(catalog, LeaseFormatError, expected)


def test_a5_a_lease_carrying_an_unknown_field_refuses(catalog: Path) -> None:
    """**A5**, fail-closed in the other direction: a key this module never writes."""
    _write_lease(catalog, state=LEASE_STATE_RELEASED, invented_field="whatever")

    _refuses_without_touching(catalog, LeaseFormatError, "unrecognized field")


def test_a5_a_lease_recording_an_unknown_state_refuses(catalog: Path) -> None:
    """**A5**, the third direction: structurally valid, but a state with no accepted meaning.

    ``held`` and ``released`` are the only two states this module has ever written. A third is
    either someone else's file or a value from a future this build does not implement, and
    guessing which would be exactly the inference D105 forbids.
    """
    _write_lease(catalog, state="quiesced")

    _refuses_without_touching(catalog, LeaseFormatError, "neither 'held' nor 'released'")


def test_a6_a_torn_lease_refuses_and_is_preserved(catalog: Path) -> None:
    """**A6.** The in-place rewrite's own crash window, which is not a small file but half a file.

    ``rewrite_locked_lease`` and ``_release_lease`` both write in place, so an interruption
    leaves a prefix of valid JSON. It parses as far as it goes and then stops, which is exactly
    the shape most likely to be mistaken for a readable document by a lenient reader.
    """
    intact = json.dumps(_lease_payload(), sort_keys=True).encode("utf-8")
    _write_raw_lease(catalog, intact[: len(intact) // 2])

    _refuses_without_touching(catalog, LeaseFormatError, "not readable UTF-8 JSON")


def test_a6_an_oversized_lease_refuses_and_is_preserved(catalog: Path) -> None:
    """**A6**, the bounded-read edge: larger than this module writes within is not this module's.

    D105's accepted 64 KiB observation was recorded non-blocking precisely because an oversized
    lease fails closed. It still does, and now it does so without being truncated to fit.
    """
    payload = _lease_payload(lease_id="0" * (64 * 1024))
    _write_raw_lease(catalog, json.dumps(payload, sort_keys=True).encode("utf-8"))

    _refuses_without_touching(catalog, LeaseFormatError, "larger than the")


# ==========================================================================
# A7: the governed recovery is unimpaired, and its output is accepted
# ==========================================================================


def test_a7_the_governed_reconciliation_still_recovers_a_stale_held_lease(
    evidence_root: Path,
    catalog: Path,
    config: _Config,
    dead_pid: int,
    activated_recovery: None,
) -> None:
    """**A7.** The whole composition, in one test, because the parts are only useful together.

    A stale ``held`` lease now refuses ordinary acquisition (the D110 invariant); the governed
    Decision 103 R3 reconciliation converts it to ``released`` with its provenance intact (the
    D103 capability, unweakened); and the ordinary writer then acquires normally (the two
    contracts still fit). Break any one of the three and the catalog is either unrecoverable or
    unprotected.
    """
    stale = _write_lease(catalog, writer_pid=dead_pid)
    _refuses_without_touching(catalog, SingleWriterViolationError, "records 'held'")

    with strictly_read_only_connection(catalog) as connection:
        logical = e0.catalog_snapshot_digest(connection).require_full()
        observations = e0.input_observation_set_digest(connection)

    outcome = e0.reconcile_writer_lease_execute(
        evidence_root=evidence_root,
        config=config,
        expected_catalog_logical_sha256=logical,
        expected_input_observation_set_sha256=observations,
    )
    assert outcome.status == "complete"

    reconciled = read_persisted_lease(stale.read_bytes())
    assert reconciled.state == LEASE_STATE_RELEASED
    assert reconciled.document["reconciliation_reason"] == STALE_LEASE_RECONCILIATION_REASON
    assert reconciled.document["reconciled_prior_state"] == LEASE_STATE_HELD
    assert reconciled.writer_pid == dead_pid

    with _acquire(catalog) as writer:
        assert writer.lease.lease_id


# ==========================================================================
# A11: the ordinary lifecycle is untouched
# ==========================================================================


def test_a11_the_acquire_release_reacquire_lifecycle_is_unchanged(catalog: Path) -> None:
    """**A11.** Sequential writers still work, and each release still names its own holder."""
    path = lease_path(catalog.parent)

    with _acquire(catalog) as first:
        first_id = first.lease.lease_id
        held = read_persisted_lease(path.read_bytes())
        assert held.state == LEASE_STATE_HELD
        assert held.lease_id == first_id

    released = read_persisted_lease(path.read_bytes())
    assert released.state == LEASE_STATE_RELEASED
    assert released.lease_id == first_id
    assert released.document["released_at_utc"]

    with _acquire(catalog) as second:
        assert second.lease.lease_id != first_id

    assert read_persisted_lease(path.read_bytes()).state == LEASE_STATE_RELEASED


def test_a11_a_live_writer_still_blocks_a_second_writer_on_the_lock(catalog: Path) -> None:
    """**A11**, the concurrent half: a genuinely live holder is refused by the lock, as before.

    The distinction the new gate must not blur: this refusal comes from the advisory lock and
    means "someone is writing right now". The D110 refusal comes from the document and means
    "someone was writing and never finished". Both refuse; they are not the same fact.
    """
    with (
        _acquire(catalog),
        pytest.raises(SingleWriterViolationError, match="another catalog writer"),
    ):
        _acquire(catalog).__enter__()


def test_a11_a_failed_connection_still_releases_the_lease_it_took(
    catalog: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**A11**, the unhappy half: a writer that legitimately acquired still releases on failure.

    Otherwise the D110 gate would convert every mid-``__enter__`` failure into a permanent
    catalog lock-out, which is the opposite of preserving evidence.
    """

    def explode(*_: object, **__: object) -> object:
        message = "synthetic connection failure"
        raise RuntimeError(message)

    monkeypatch.setattr(catalog_module, "connect", explode)
    with pytest.raises(RuntimeError, match="synthetic connection failure"):
        _acquire(catalog).__enter__()

    monkeypatch.undo()
    assert read_persisted_lease(lease_path(catalog.parent).read_bytes()).state == (
        LEASE_STATE_RELEASED
    )
    with _acquire(catalog) as writer:
        assert writer.lease.lease_id


# ==========================================================================
# A12: no execution authority is opened by any of this
# ==========================================================================


def test_a12_every_execution_authority_ships_none() -> None:
    """**A12.** D110 is remediation. It grants nothing, and the source says so literally.

    The constants are read from the shipped module *and* from its source text, because a test
    that only read the attribute could pass against a value some other test had monkeypatched.
    """
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None

    source = Path(e0.__file__).read_text(encoding="utf-8")
    for name in (
        "M3_3_E0_EXECUTION_AUTHORITY",
        "PRE_E0_CATALOG_TRANSITION_AUTHORITY",
        "STALE_WRITER_LEASE_RECOVERY_AUTHORITY",
    ):
        assert f"{name}: Final[str | None] = None\n" in source


# ==========================================================================
# Non-vacuity: the pre-D110 behaviour is restored, and the family notices
# ==========================================================================


def test_the_provenance_regression_dies_if_the_pre_d110_overwrite_is_restored(
    catalog: Path, dead_pid: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bounded mutation proof: put the defect back and watch A3-A6 stop holding.

    ``_refuse_unacquirable_lease`` is replaced by the no-op it effectively was before Decision
    110 — the acquisition path proceeded on a free advisory lock alone. The stale ``held`` lease
    is then overwritten exactly as it was on 2026-08-18, which is what makes A3, A4, A5, A6 and
    A8 real tests rather than restatements of code that could not fail.
    """
    stale = _write_lease(catalog, writer_pid=dead_pid)
    before = stale.read_bytes()

    monkeypatch.setattr(
        CatalogWriter,
        "_refuse_unacquirable_lease",
        staticmethod(lambda _descriptor: None),
    )

    with _acquire(catalog) as writer:
        overwritten = read_persisted_lease(stale.read_bytes())
        assert overwritten.state == LEASE_STATE_HELD
        assert overwritten.writer_pid != dead_pid
        assert overwritten.lease_id == writer.lease.lease_id

    assert stale.read_bytes() != before
    assert read_persisted_lease(stale.read_bytes()).writer_pid != dead_pid
