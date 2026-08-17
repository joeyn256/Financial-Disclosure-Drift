"""Governed stale-writer-lease reconciliation proofs (accepted Decision 103 R3-R7).

Every test here drives production code over a **disposable** SQLite catalog beneath a
**synthetic** temporary root. Nothing in this module resolves, opens, names, prints, or infers
the accepted private evidence root; nothing opens the accepted operational catalog; and nothing
reads, writes, or approximates the real stale lease this capability was built for. The fixtures
build their own catalog from the packaged migrations and delete it with the temporary directory.

Three conventions carry most of the weight.

**Test-scoped activation.** :data:`~disclosure_drift.m3.e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY`
ships ``None`` under accepted Decision 104, so ``execute`` is not reachable as the repository
stands. Every test that drives the execute machine therefore injects its own disposable token —
through the ``activated`` fixture, or by ``monkeypatch`` where the token's identity is itself the
subject — and never through the shipped constant. Two tests deliberately do the opposite and read
the shipped value rather than setting it: ``test_the_shipped_activation_constant_is_disabled`` and
``test_execute_is_unreachable_under_the_shipped_activation_constant``.

**A real dead process, not an invented number.** The "recorded writer is gone" predicate is
proved against the PID of a subprocess this module started and reaped, so ``os.kill(pid, 0)``
answers from the kernel rather than from a guess about which numbers are unused.

**Absence is measured, never inferred.** Where a test asserts that nothing was written, it
walks the whole evidence root and compares the complete before/after file inventory and every
byte of the catalog — rather than trusting a return value that says nothing happened.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from disclosure_drift.config import EVIDENCE_ROOT_ENV
from disclosure_drift.m3 import e0
from disclosure_drift.m3.receipt import (
    _ABSOLUTE_PATH_PATTERN,
    _EMAIL_PATTERN,
    RUN_NAMESPACE_DIRNAME,
)
from disclosure_drift.storage import catalog as catalog_module
from disclosure_drift.storage.catalog import (
    LEASE_FILENAME,
    LEASE_STATE_HELD,
    LEASE_STATE_RELEASED,
    STALE_LEASE_RECONCILIATION_REASON,
    CatalogWriter,
    LeaseFormatError,
    PersistedLease,
    exclusive_lease_lock,
    host_fingerprint,
    lease_path,
    read_persisted_lease,
    reconciled_lease_document,
    strictly_read_only_connection,
    writer_process_is_alive,
)
from disclosure_drift.storage.sqlite import apply_migrations, connect

try:  # pragma: no cover - supported CI and production platforms are Unix
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

_EXPIRED_ACQUIRED = "2026-08-16T21:45:35.818376Z"
_EXPIRED_AT = "2026-08-16T22:00:35.818376Z"
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
    """Exactly the configuration surface the recovery reads (predicate ``L10``)."""

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


def _write_lease(catalog: Path, **overrides: object) -> Path:
    """Write a lease document beside ``catalog`` at mode ``0600`` and return its path."""
    path = lease_path(catalog.parent)
    payload: dict[str, object] = {
        "lease_id": "4a327881f6424d5ea0b32136ba5e3b46",
        "writer_pid": 1,
        "host_fingerprint": host_fingerprint(),
        "acquired_at_utc": _EXPIRED_ACQUIRED,
        "expires_at_utc": _EXPIRED_AT,
        "state": LEASE_STATE_HELD,
    }
    payload.update(overrides)
    path.write_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
    path.chmod(0o600)
    return path


@pytest.fixture
def stale_lease(catalog: Path, dead_pid: int) -> Path:
    """The exact accepted interruption residue: `held`, expired, this host, a dead writer."""
    return _write_lease(catalog, writer_pid=dead_pid)


def _identity(catalog: Path) -> tuple[str, str]:
    """This disposable catalog's ``(logical digest, input observation-set digest)``."""
    with strictly_read_only_connection(catalog) as connection:
        return (
            e0.catalog_snapshot_digest(connection).require_full(),
            e0.input_observation_set_digest(connection),
        )


def _preflight(evidence_root: Path, catalog: Path, config: _Config, **overrides: object):  # noqa: ANN202
    logical, observations = _identity(catalog)
    keywords: dict[str, object] = {
        "expected_catalog_logical_sha256": logical,
        "expected_input_observation_set_sha256": observations,
    }
    keywords.update(overrides)
    return e0.reconcile_writer_lease_preflight(
        evidence_root=evidence_root, config=config, **keywords
    )


def _execute(evidence_root: Path, catalog: Path, config: _Config, **overrides: object):  # noqa: ANN202
    logical, observations = _identity(catalog)
    keywords: dict[str, object] = {
        "expected_catalog_logical_sha256": logical,
        "expected_input_observation_set_sha256": observations,
    }
    keywords.update(overrides)
    return e0.reconcile_writer_lease_execute(evidence_root=evidence_root, config=config, **keywords)


#: SQLite's own sidecars. Excluded from every inventory comparison because *reading* a WAL
#: database materializes them: `strictly_read_only_connection` opens with
#: `SQLITE_OPEN_READONLY`, which leaves the database file byte-identical but still requires the
#: shared-memory index, so an empty `-wal` and a `-shm` appear on the first read and are not a
#: mutation of catalog state. The WAL's *length* is asserted separately and must stay zero.
_SQLITE_SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")


def _inventory(root: Path) -> dict[str, bytes]:
    """Every regular file beneath ``root`` except SQLite's sidecars, by root-relative name."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.name.endswith(_SQLITE_SIDECAR_SUFFIXES)
    }


def _record(evidence_root: Path) -> dict[str, object]:
    directory = e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)
    loaded = json.loads((directory / e0.LEASE_RECOVERY_RECORD_FILENAME).read_text("utf-8"))
    assert isinstance(loaded, dict)
    return loaded


@pytest.fixture
def activated(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run the execute machine against a disposable token, never the shipped one."""
    monkeypatch.setattr(e0, "STALE_WRITER_LEASE_RECOVERY_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    yield


# ==========================================================================
# The lease document format (Decision 103 R4)
# ==========================================================================


def test_a_structurally_valid_lease_round_trips_through_the_reader(catalog: Path) -> None:
    path = _write_lease(catalog)
    lease = read_persisted_lease(path.read_bytes())

    assert lease.state == LEASE_STATE_HELD
    assert lease.lease_id == "4a327881f6424d5ea0b32136ba5e3b46"
    assert lease.host_fingerprint == host_fingerprint()
    assert lease.has_expired()


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (b"not json at all", "not readable UTF-8 JSON"),
        (b"[]", "not a JSON object"),
        (b'{"state": "held"}', "missing required field"),
        (b"\xff\xfe", "not readable UTF-8 JSON"),
    ],
)
def test_a_malformed_lease_document_is_refused(payload: bytes, expected: str) -> None:
    """L-T3: the reader fails closed on every shape that is not a lease."""
    with pytest.raises(LeaseFormatError, match=expected):
        read_persisted_lease(payload)


def test_a_lease_carrying_an_unknown_field_is_refused(catalog: Path) -> None:
    """L-T3: a key this module never writes means an unaccounted-for writer, not a detail."""
    path = _write_lease(catalog, injected_field="anything")
    with pytest.raises(LeaseFormatError, match="unrecognized field"):
        read_persisted_lease(path.read_bytes())


@pytest.mark.parametrize(
    "overrides",
    [
        {"writer_pid": 0},
        {"writer_pid": "43427"},
        {"writer_pid": True},
        {"lease_id": ""},
        {"host_fingerprint": "   "},
        {"expires_at_utc": "2026-08-16 22:00:35"},
        {"acquired_at_utc": 17},
    ],
)
def test_a_lease_with_an_unusable_field_value_is_refused(
    catalog: Path, overrides: Mapping[str, object]
) -> None:
    """L-T3: every field a takeover decision rests on is typed and checked."""
    path = _write_lease(catalog, **overrides)
    with pytest.raises(LeaseFormatError):
        read_persisted_lease(path.read_bytes())


def test_only_a_held_lease_can_be_reconciled(catalog: Path) -> None:
    """L-T2 and R4: `released` is a finished lifecycle, not a thing to reconcile again."""
    path = _write_lease(catalog, state=LEASE_STATE_RELEASED, released_at_utc=_EXPIRED_AT)
    lease = read_persisted_lease(path.read_bytes())
    with pytest.raises(LeaseFormatError, match="only a lease in state 'held'"):
        reconciled_lease_document(lease, reconciled_at_utc=_FAR_FUTURE)


def test_the_reconciled_document_cannot_be_read_as_a_voluntary_release(catalog: Path) -> None:
    """L-T21 and R4: an auditor cannot conclude the dead writer released its own lease.

    The four properties that make that true are asserted individually, because each closes a
    different reading: the state is the ordinary one every existing reader understands, the
    field that means "the holder let go" is absent, the recovery is named explicitly, and the
    dead writer is still named as the holder rather than being erased.
    """
    lease = read_persisted_lease(_write_lease(catalog, writer_pid=43_427).read_bytes())
    document = reconciled_lease_document(lease, reconciled_at_utc=_FAR_FUTURE)

    assert document["state"] == LEASE_STATE_RELEASED
    assert "released_at_utc" not in document
    assert document["reconciliation_reason"] == STALE_LEASE_RECONCILIATION_REASON
    assert document["reconciled_at_utc"] == _FAR_FUTURE
    assert document["reconciled_prior_state"] == LEASE_STATE_HELD
    # The prior holder's own values are carried through unchanged, so they *are* the prior
    # values; a separate `prior_writer_pid` copy would be an exact duplicate, not provenance.
    assert document["writer_pid"] == 43_427
    assert document["lease_id"] == lease.lease_id
    assert document["acquired_at_utc"] == lease.acquired_at_utc
    # And the result is still a valid lease every existing reader can parse.
    assert read_persisted_lease(e0.canonical_bytes(document)).state == LEASE_STATE_RELEASED


def test_an_ordinary_holder_release_is_distinguishable_from_a_reconciliation(
    catalog: Path, tmp_path: Path
) -> None:
    """R4: the two release paths are told apart by the fields they write, not by prose."""
    with CatalogWriter(catalog, catalog.parent):
        pass
    released = read_persisted_lease(lease_path(catalog.parent).read_bytes())

    assert released.state == LEASE_STATE_RELEASED
    assert "released_at_utc" in released.document
    assert "reconciliation_reason" not in released.document


# ==========================================================================
# The eligibility ladder (Decision 103 R3, predicates L1-L11)
# ==========================================================================


def test_an_eligible_stale_lease_passes_preflight_and_mutates_nothing(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config
) -> None:
    """L-T11: every predicate holds, and the whole evidence root is byte-identical after."""
    before = _inventory(evidence_root)
    report = _preflight(evidence_root, catalog, config)

    assert report.passed, report.refusals
    assert report.facts["writer_lease"] == LEASE_STATE_HELD
    assert report.facts["lease_host_binding"] == "this host"
    assert report.facts["recorded_writer_process"] == "not alive"
    assert report.facts["lease_expiry"] == "expired"
    assert report.facts["exclusive_writer_lock"] == "available"
    assert report.facts["catalog_identity"] == "matches the accepted recovery baseline"
    assert report.facts["network_switches_disabled"] is True
    assert report.facts["recovery_namespace"] == "absent"
    assert report.facts["write_ahead_log_bytes"] == 0
    assert _inventory(evidence_root) == before
    assert e0._wal_byte_length(catalog) == 0  # noqa: SLF001


def test_an_absent_lease_refuses_because_there_is_nothing_to_reconcile(
    evidence_root: Path, catalog: Path, config: _Config, activated: None
) -> None:
    """L-T1: the recovery acts on an existing stale lease and never creates one."""
    report = _preflight(evidence_root, catalog, config)

    assert not report.passed
    assert report.facts["writer_lease"] == "absent"
    assert any("no regular persisted writer lease" in item for item in report.refusals)
    assert not lease_path(catalog.parent).exists()

    with pytest.raises(e0.PreflightRefusalError, match="no regular persisted writer lease"):
        _execute(evidence_root, catalog, config)
    assert not lease_path(catalog.parent).exists()


def test_a_released_lease_refuses_at_preflight_and_at_execute(
    evidence_root: Path, catalog: Path, config: _Config, activated: None
) -> None:
    """L-T2: the state that means "no writer holds this" is not a stale-held lease."""
    _write_lease(catalog, state=LEASE_STATE_RELEASED, released_at_utc=_EXPIRED_AT)

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["writer_lease"] == LEASE_STATE_RELEASED
    assert any("is stale-held and eligible" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="stale-held and eligible"):
        _execute(evidence_root, catalog, config)


def test_a_malformed_lease_refuses_before_anything_is_examined(
    evidence_root: Path, catalog: Path, config: _Config, activated: None
) -> None:
    """L-T3: an unparseable lease is never repaired, replaced, or reconciled."""
    path = lease_path(catalog.parent)
    path.write_bytes(b'{"state": "held"')
    path.chmod(0o600)
    before = path.read_bytes()

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["writer_lease"] == "structurally invalid"
    assert any("not structurally valid" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="not structurally valid"):
        _execute(evidence_root, catalog, config)
    assert path.read_bytes() == before


def test_a_live_writer_process_refuses_however_long_the_lease_has_been_held(
    evidence_root: Path, catalog: Path, config: _Config, activated: None
) -> None:
    """L-T4: elapsed time never converts a live writer's lease into a stale one.

    This process is used as the live writer, so "alive" is answered by the kernel about a
    process that unambiguously exists rather than by a stub.
    """
    _write_lease(catalog, writer_pid=os.getpid(), expires_at_utc=_EXPIRED_AT)

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["recorded_writer_process"] == "alive"
    assert report.facts["lease_expiry"] == "expired"
    assert any("still alive" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="still alive"):
        _execute(evidence_root, catalog, config)


def test_an_unavailable_exclusive_advisory_lock_refuses(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T5: a free advisory lock is required, and a held one refuses even for a dead PID.

    The lock is taken through the accepted mechanism on an independent descriptor. ``flock``
    conflicts across descriptors, so the recovery's own non-blocking attempt genuinely fails
    rather than being told it succeeded by the operating system.
    """
    with exclusive_lease_lock(stale_lease, writable=False):
        report = _preflight(evidence_root, catalog, config)
        assert not report.passed
        assert report.facts["exclusive_writer_lock"] == "unavailable"
        assert any("advisory lock is not available" in item for item in report.refusals)

        with pytest.raises(e0.PreflightRefusalError, match="advisory lock is not available"):
            _execute(evidence_root, catalog, config)


def test_a_lease_taken_on_a_different_host_refuses(
    evidence_root: Path, catalog: Path, dead_pid: int, config: _Config, activated: None
) -> None:
    """L-T6: this host cannot observe another host's writer, so it may not judge it dead."""
    _write_lease(catalog, writer_pid=dead_pid, host_fingerprint="some-other-host")

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["lease_host_binding"] == "a different host"
    assert any("different host" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="different host"):
        _execute(evidence_root, catalog, config)


def test_an_unexpired_lease_refuses_even_with_a_dead_writer(
    evidence_root: Path, catalog: Path, dead_pid: int, config: _Config, activated: None
) -> None:
    """L-T7: a dead PID on its own never authorizes takeover; every predicate is conjunctive."""
    _write_lease(catalog, writer_pid=dead_pid, expires_at_utc=_FAR_FUTURE)

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["recorded_writer_process"] == "not alive"
    assert report.facts["lease_expiry"] == "unexpired"
    assert any("has not reached its recorded expiry" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="recorded expiry"):
        _execute(evidence_root, catalog, config)


def test_a_catalog_failing_an_integrity_gate_refuses(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T8: the three SQLite gates must all pass before a lease is cleared over the catalog.

    A real orphan row is created with foreign-key enforcement off, so ``foreign_key_check``
    reports an actual violation rather than the predicate being stubbed out.
    """
    with connect(catalog, writer=True) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO inventory_reasons (accession_plain, reason_code, detail, "
            "recorded_at_utc) VALUES ('0000000000-00-000000', 'NO-SUCH-CODE', NULL, ?)",
            ("2026-01-01T00:00:00Z",),
        )
        connection.commit()

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["foreign_key_violations"] != 0
    assert any("three SQLite integrity gates" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="integrity gates"):
        _execute(evidence_root, catalog, config)


@pytest.mark.parametrize(
    "override",
    ["expected_catalog_logical_sha256", "expected_input_observation_set_sha256"],
)
def test_a_catalog_whose_identity_is_not_the_expected_one_refuses(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    override: str,
) -> None:
    """L-T9: a lease is never cleared over a catalog the accepted policy did not name.

    Both halves of the identity are checked independently, so a match on one cannot carry a
    mismatch on the other.
    """
    report = _preflight(evidence_root, catalog, config, **{override: "9" * 64})
    assert not report.passed
    assert report.facts["catalog_identity"] == "differs"
    assert any("not the one the accepted recovery policy" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="accepted recovery policy"):
        _execute(evidence_root, catalog, config, **{override: "9" * 64})


@pytest.mark.parametrize("switch", ["enabled", "m3_acquire_enabled"])
def test_an_enabled_network_switch_refuses(
    evidence_root: Path, catalog: Path, stale_lease: Path, activated: None, switch: str
) -> None:
    """L-T10: a recovery that reconciles a lease still runs with the network off."""
    config = _Config(network=_Network(**{switch: True}))

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["network_switches_disabled"] is False
    assert any("network switch is enabled" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="network switch is enabled"):
        _execute(evidence_root, catalog, config)


def test_an_existing_recovery_namespace_refuses_as_a_conflicting_operation(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T11's namespace half: a reconciliation is create-once and is never repeated."""
    e0.create_run_namespace(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["recovery_namespace"] == "already exists"
    assert any("create-once" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="create-once"):
        _execute(evidence_root, catalog, config)


def test_a_pending_write_ahead_log_refuses(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T5's second signal: a non-empty WAL is state a writer has not finished landing."""
    catalog.with_name(f"{catalog.name}-wal").write_bytes(b"\x00" * 64)

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert report.facts["write_ahead_log_bytes"] == 64  # noqa: PLR2004
    assert any("write-ahead log" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="write-ahead log"):
        _execute(evidence_root, catalog, config)


@pytest.mark.parametrize("kind", ["symlink", "directory"])
def test_a_lease_that_is_not_a_regular_file_refuses(
    evidence_root: Path, catalog: Path, config: _Config, activated: None, tmp_path: Path, kind: str
) -> None:
    """L-T23: a symlinked or non-regular lease would put the lock and the write elsewhere."""
    path = lease_path(catalog.parent)
    if kind == "symlink":
        elsewhere = tmp_path / "outside.lease"
        elsewhere.write_bytes(b"{}")
        path.symlink_to(elsewhere)
        expected_after = elsewhere.read_bytes()
    else:
        path.mkdir()
        expected_after = b""

    report = _preflight(evidence_root, catalog, config)
    assert not report.passed
    assert any("no regular persisted writer lease" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="no regular persisted writer lease"):
        _execute(evidence_root, catalog, config)
    if kind == "symlink":
        assert (tmp_path / "outside.lease").read_bytes() == expected_after


def test_the_lock_helper_refuses_a_symlinked_lease_outright(catalog: Path, tmp_path: Path) -> None:
    """L-T23 at the primitive: the lock itself refuses before a descriptor is used."""
    elsewhere = tmp_path / "outside.lease"
    elsewhere.write_bytes(b"{}")
    path = lease_path(catalog.parent)
    path.symlink_to(elsewhere)

    with (
        pytest.raises(LeaseFormatError, match="symbolic link"),
        exclusive_lease_lock(path, writable=False),
    ):
        pass  # pragma: no cover - the context manager never opens


def test_the_lock_helper_never_creates_the_lease_it_inspects(catalog: Path) -> None:
    """R3: asking whether the lock is free must not bring a lease into existence."""
    path = lease_path(catalog.parent)
    assert not path.exists()

    with (
        pytest.raises(LeaseFormatError, match="absent or is not a regular file"),
        exclusive_lease_lock(path, writable=False),
    ):
        pass  # pragma: no cover - the context manager never opens
    assert not path.exists()


# ==========================================================================
# Execute: exactly one reconciliation, under one continuously held lock
# ==========================================================================


def test_an_eligible_stale_lease_reconciles_exactly_once(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T12 and L-T13: the operation succeeds once and refuses every time thereafter."""
    outcome = _execute(evidence_root, catalog, config)

    assert outcome.status == "complete"
    assert outcome.run_namespace == e0.LEASE_RECOVERY_RUN_NAMESPACE
    assert outcome.result_token == (
        f"M3_3_STALE_WRITER_LEASE_RECOVERY_COMPLETE:{outcome.terminal_record_id}"
    )
    assert outcome.prior_lease_file_sha256 != outcome.resulting_lease_file_sha256

    lease = read_persisted_lease(stale_lease.read_bytes())
    assert lease.state == LEASE_STATE_RELEASED

    # A second execute has two independent reasons to refuse, and states the first it reaches.
    with pytest.raises(e0.PreflightRefusalError) as caught:
        _execute(evidence_root, catalog, config)
    assert "stale-held and eligible" in str(caught.value)
    assert "create-once" in str(caught.value)


def test_the_reconciliation_changes_only_the_lease_and_its_own_record(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T14, L-T15, L-T16 and R5: the complete durable effect, measured rather than promised.

    The whole evidence root is inventoried before and after. Exactly one file's bytes change —
    the lease — and exactly one file appears: the recovery record. The catalog is byte-identical
    and no WAL or shared-memory sidecar is left behind.
    """
    before = _inventory(evidence_root)
    catalog_bytes = catalog.read_bytes()
    logical_before, observations_before = _identity(catalog)

    _execute(evidence_root, catalog, config)

    after = _inventory(evidence_root)
    lease_name = str(stale_lease.relative_to(evidence_root))
    record_name = f"{RUN_NAMESPACE_DIRNAME}/{e0.LEASE_RECOVERY_RUN_NAMESPACE}/" + (
        e0.LEASE_RECOVERY_RECORD_FILENAME
    )

    assert set(after) - set(before) == {record_name}
    assert set(before) - set(after) == set()
    changed = {name for name in before if before[name] != after[name]}
    assert changed == {lease_name}

    # L-T15: byte-identical and logically identical.
    assert catalog.read_bytes() == catalog_bytes
    assert _identity(catalog) == (logical_before, observations_before)

    # L-T16: the write-ahead log stays empty. SQLite materializes an empty `-wal` and a `-shm`
    # on the first read of a WAL database even through a strictly read-only handle, so their
    # existence is a read-side artifact; a non-zero WAL would be pending catalog state and is
    # what this asserts against.
    assert e0._wal_byte_length(catalog) == 0  # noqa: SLF001
    assert not catalog.with_name(f"{catalog.name}-journal").exists()


def test_the_reconciled_lease_and_record_keep_private_file_permissions(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """L-T22 and R5: nothing this writes becomes group- or world-readable."""
    _execute(evidence_root, catalog, config)
    directory = e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)

    assert stat.S_IMODE(stale_lease.stat().st_mode) == 0o600
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    record = directory / e0.LEASE_RECOVERY_RECORD_FILENAME
    assert stat.S_IMODE(record.stat().st_mode) == 0o600


def test_the_exclusive_lock_is_held_across_the_reassertion_and_the_mutation(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L-T17 and R5: the critical section is genuinely locked at both of its boundaries.

    Proved by probing from an independent descriptor at each boundary and requiring the probe
    to **fail**. A test that merely checked the code called the lock first would prove nothing
    about whether the lock was still held when the bytes were written.
    """
    probes: list[str] = []

    def probe(label: str) -> None:
        descriptor = os.open(stale_lease, os.O_RDONLY)
        try:
            with pytest.raises(BlockingIOError):
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            os.close(descriptor)
        probes.append(label)

    original_reassert = e0._reassert_under_lock  # noqa: SLF001
    original_rewrite = catalog_module.rewrite_locked_lease

    def reassert(descriptor: int, state: object) -> object:
        probe("reassert")
        return original_reassert(descriptor, state)  # type: ignore[arg-type]

    def rewrite(descriptor: int, payload: bytes) -> None:
        probe("mutate")
        original_rewrite(descriptor, payload)

    monkeypatch.setattr(e0, "_reassert_under_lock", reassert)
    monkeypatch.setattr(catalog_module, "rewrite_locked_lease", rewrite)

    _execute(evidence_root, catalog, config)
    assert probes == ["reassert", "mutate"]


def test_a_lease_that_changes_between_the_check_and_the_lock_refuses(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L-T18: the ladder's measurement is a claim about a past instant, and it is made good.

    The lease is rewritten in the window between the read-only ladder and the lock — the exact
    race the under-lock reassertion exists for — and the operation refuses without mutating.
    """
    original = e0._lease_lock  # noqa: SLF001
    tampered = {"done": False}

    def tamper(path: Path, *, writable: bool):  # noqa: ANN202
        if writable and not tampered["done"]:
            tampered["done"] = True
            _write_lease(catalog, writer_pid=stale_lease and 1, acquired_at_utc=_FAR_FUTURE)
        return original(path, writable=writable)

    monkeypatch.setattr(e0, "_lease_lock", tamper)

    with pytest.raises(e0.PreflightRefusalError, match="changed between the eligibility check"):
        _execute(evidence_root, catalog, config)
    assert tampered["done"]
    assert read_persisted_lease(stale_lease.read_bytes()).state == LEASE_STATE_HELD
    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


def test_a_writer_that_becomes_alive_under_the_lock_refuses(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R6: liveness is re-measured inside the critical section, not carried forward.

    A PID is a reusable number, so "the recorded writer is gone" can become false between the
    ladder and the lock without a single byte of the lease changing — which is why the digest
    check alone is not enough and the predicate itself is re-measured. Simulated by making the
    liveness answer flip after the ladder's call, which is exactly what PID reuse looks like.
    """
    answers = iter([False, True])
    monkeypatch.setattr(catalog_module, "writer_process_is_alive", lambda _pid: next(answers, True))
    before = stale_lease.read_bytes()

    with pytest.raises(e0.PreflightRefusalError, match="no longer holds under the lock"):
        _execute(evidence_root, catalog, config)

    assert stale_lease.read_bytes() == before
    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


def test_a_host_binding_that_stops_matching_under_the_lock_refuses(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R6: every mutable predicate is reasserted, not only the ones that can plausibly move."""
    answers = iter([host_fingerprint()])
    monkeypatch.setattr(
        catalog_module, "host_fingerprint", lambda: next(answers, "a-different-host")
    )
    before = stale_lease.read_bytes()

    with pytest.raises(e0.PreflightRefusalError, match="no longer holds under the lock"):
        _execute(evidence_root, catalog, config)

    assert stale_lease.read_bytes() == before
    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lease_id", "ffffffffffffffffffffffffffffffff"),
        ("writer_pid", 4_242_424),
        ("host_fingerprint", "another-host"),
        ("expires_at_utc", _FAR_FUTURE),
        ("state", LEASE_STATE_RELEASED),
    ],
)
def test_a_locked_lease_that_diverges_field_wise_refuses(
    catalog: Path, stale_lease: Path, field: str, value: object
) -> None:
    """L-T19 and L-T20: identity, not just bytes, has to still be the lease that was examined.

    Exercised at the reassertion directly, with a state object whose recorded digest matches
    the file exactly but whose remembered lease differs in one field. Only a direct call can
    reach that branch: two documents that differ in a field cannot share a digest.
    """
    raw = stale_lease.read_bytes()
    observed = read_persisted_lease(raw)
    remembered = PersistedLease(
        lease_id=observed.lease_id,
        writer_pid=observed.writer_pid,
        host_fingerprint=observed.host_fingerprint,
        acquired_at_utc=observed.acquired_at_utc,
        expires_at_utc=observed.expires_at_utc,
        state=observed.state,
        document=dict(observed.document),
    )
    state = e0._StaleLeaseState(  # noqa: SLF001
        catalog_path=catalog,
        lease_path=stale_lease,
        lease=replace_lease(remembered, field, value),
        lease_file_sha256=e0.file_digest(stale_lease)[0],
        lease_byte_length=len(raw),
        identity=e0._measure_catalog_identity(catalog),  # noqa: SLF001
    )

    descriptor = os.open(stale_lease, os.O_RDONLY)
    try:
        with pytest.raises(e0.PreflightRefusalError, match="diverged in"):
            e0._reassert_under_lock(descriptor, state)  # noqa: SLF001
    finally:
        os.close(descriptor)


def replace_lease(lease: PersistedLease, field: str, value: object) -> PersistedLease:
    """A copy of ``lease`` with one field replaced, for the divergence cases above."""
    fields = {
        "lease_id": lease.lease_id,
        "writer_pid": lease.writer_pid,
        "host_fingerprint": lease.host_fingerprint,
        "acquired_at_utc": lease.acquired_at_utc,
        "expires_at_utc": lease.expires_at_utc,
        "state": lease.state,
    }
    fields[field] = value
    return PersistedLease(document=dict(lease.document), **fields)  # type: ignore[arg-type]


def test_a_replacement_shorter_than_the_persisted_lease_is_refused(stale_lease: Path) -> None:
    """R5: the in-place rewrite never truncates first, so no window of an empty lease exists."""
    from disclosure_drift.errors import CatalogWriteError

    with (
        exclusive_lease_lock(stale_lease, writable=True) as descriptor,
        pytest.raises(CatalogWriteError, match="shorter than the persisted one"),
    ):
        catalog_module.rewrite_locked_lease(descriptor, b"{}")
    assert read_persisted_lease(stale_lease.read_bytes()).state == LEASE_STATE_HELD


# ==========================================================================
# The durable recovery record (Decision 103 R7)
# ==========================================================================


def test_the_record_binds_the_prior_and_resulting_lease_digests(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """R-T1: both digests are recorded, and both are reproducible from the files themselves."""
    prior_digest, prior_bytes = e0.file_digest(stale_lease)
    outcome = _execute(evidence_root, catalog, config)
    resulting_digest, resulting_bytes = e0.file_digest(stale_lease)
    document = _record(evidence_root)

    assert (
        document["prior_lease"]["file_sha256"] == prior_digest == (outcome.prior_lease_file_sha256)
    )
    assert document["prior_lease"]["byte_length"] == prior_bytes
    assert document["prior_lease"]["state"] == LEASE_STATE_HELD
    assert (
        document["resulting_lease"]["file_sha256"]
        == resulting_digest
        == (outcome.resulting_lease_file_sha256)
    )
    assert document["resulting_lease"]["byte_length"] == resulting_bytes
    assert document["resulting_lease"]["state"] == LEASE_STATE_RELEASED
    assert document["resulting_lease"]["reconciliation_reason"] == (
        STALE_LEASE_RECONCILIATION_REASON
    )


def test_the_record_binds_the_catalog_and_observation_digests_before_and_after(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """R-T2 and R-T3: both digests are bound on both sides, and both sides are equal.

    Equality is the point of the record. A recovery that recorded only one measurement could
    not tell an auditor that the catalog was untouched; recording both and requiring them equal
    turns "we did not write to it" into something checkable from the artifact alone.
    """
    logical, observations = _identity(catalog)
    _execute(evidence_root, catalog, config)
    document = _record(evidence_root)

    before = document["catalog_before"]
    after = document["catalog_after"]
    assert before == after
    assert before["catalog_logical_sha256"] == logical
    assert before["input_observation_set_sha256"] == observations
    assert before["quick_check"] == "ok"
    assert before["integrity_check"] == "ok"
    assert before["foreign_key_violations"] == 0
    assert before["applied_migration_chain"] == list(range(1, 16))
    assert before["wal_byte_length"] == 0
    assert before["file_sha256"] == e0.file_digest(catalog)[0]


def test_the_record_binds_the_governed_authority_and_states_zero_network_activity(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R-T5: the authority identity is bound as a digest, and never as its value.

    Decision 104 adds the negative half. The record must bind the authority that was
    **actually active for this execution** — the value ``_require_activation`` returned —
    rather than a literal the record builder carries. Asserting only that some 64-character
    digest is present would pass equally well against a hardcoded one, so the test pins the
    digest to the injected token *and* requires it to differ from the Decision 103 literal,
    which is the exact value a hardcoding would most plausibly have used.
    """
    import hashlib

    authority = "TEST-ONLY-DISPOSABLE-AUTHORITY"
    monkeypatch.setattr(e0, "STALE_WRITER_LEASE_RECOVERY_AUTHORITY", authority)
    _execute(evidence_root, catalog, config)
    document = _record(evidence_root)

    assert document["owner_authority_sha256"] == hashlib.sha256(authority.encode()).hexdigest()
    assert authority not in json.dumps(document)
    d103_literal = "M3_3_D103_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED"
    assert document["owner_authority_sha256"] != hashlib.sha256(d103_literal.encode()).hexdigest()
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    assert document["record_type"] == e0.LEASE_RECOVERY_RECORD_TYPE
    assert document["operation"] == "stale_writer_lease_reconciliation"
    assert document["outcome"] == "reconciled"

    # R7: every eligibility result is bound, and each is a measured value rather than a literal
    # the record asserts about itself.
    assert document["eligibility"] == {
        "catalog_identity_matched": True,
        "catalog_integrity_passed": True,
        "conflicting_recovery_detected": False,
        "exclusive_advisory_lock_acquired": True,
        "lease_expired": True,
        "lease_structurally_valid": True,
        "lock_held_across_reassertion_and_mutation": True,
        "network_switches_disabled": True,
        "other_active_writer_detected": False,
        "persisted_state_before": LEASE_STATE_HELD,
        "recorded_writer_process_alive": False,
        "recorded_writer_host_matched": True,
    }


def test_the_record_carries_no_absolute_path_secret_or_private_root_component(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """R-T4: the record names only fixed root-relative paths, counts, digests, and enums."""
    _execute(evidence_root, catalog, config)
    directory = e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)
    raw = (directory / e0.LEASE_RECOVERY_RECORD_FILENAME).read_text("utf-8")
    document = _record(evidence_root)

    assert str(evidence_root) not in raw
    assert _SYNTHETIC_ROOT_MARKER not in raw
    assert not _ABSOLUTE_PATH_PATTERN.search(raw)
    assert not _EMAIL_PATTERN.search(raw)
    assert document["catalog_relative_path"] == e0.OPERATIONAL_CATALOG_RELATIVE_PATH
    assert document["lease_relative_path"] == f"catalogs/{LEASE_FILENAME}"

    # The accepted §5 scan is applied by production over the pre-identity projection — the two
    # derived identity fields are added afterwards, and `result_token` is a governed field name
    # every accepted terminal record already uses. Reproducing that exact scope here proves the
    # scan production runs is the scan asserted, rather than a differently shaped one.
    e0._refuse_prohibited_recovery_content(  # noqa: SLF001
        {k: v for k, v in document.items() if k not in {"terminal_record_id", "result_token"}}
    )


def test_the_record_identity_reproduces_and_a_self_referential_preimage_fails(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """R7 and §11: the identity is recomputable, and it cannot contain the token it names."""
    _execute(evidence_root, catalog, config)
    document = _record(evidence_root)

    identity = e0.compute_terminal_record_id(document)
    assert document["terminal_record_id"] == identity
    assert document["result_token"] == f"M3_3_STALE_WRITER_LEASE_RECOVERY_COMPLETE:{identity}"

    # A preimage that included either self-referential field would not reproduce.
    with_token = dict(document)
    assert e0.canonical_bytes(with_token) != e0.canonical_bytes(
        {k: v for k, v in document.items() if k not in {"terminal_record_id", "result_token"}}
    )

    # The stored bytes are canonical, so the record round-trips byte for byte.
    directory = e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)
    stored = (directory / e0.LEASE_RECOVERY_RECORD_FILENAME).read_bytes()
    assert e0.canonical_bytes(document) == stored


def test_the_record_is_write_once(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """R7: the durable evidence is created with ``O_EXCL`` and is never replaced."""
    _execute(evidence_root, catalog, config)
    directory = e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE)
    with pytest.raises(FileExistsError):
        e0.write_once(directory / e0.LEASE_RECOVERY_RECORD_FILENAME, b"{}\n")


# ==========================================================================
# The successor's lease predicate, and the operator surface (R6, R8)
# ==========================================================================


def test_the_e0_lease_predicate_clears_once_the_stale_lease_is_reconciled(
    evidence_root: Path, catalog: Path, stale_lease: Path, config: _Config, activated: None
) -> None:
    """E-T1 and E-T2: E0 refuses before the governed reconciliation and stops refusing after.

    Only the lease predicate is at issue here — the disposable catalog carries no transition
    terminal, so the surrounding preflight refuses for its own reasons before and after. That
    is the honest scope of the claim: reconciliation clears the lease gate and nothing else.
    """
    before = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert before.facts["writer_lease"] == LEASE_STATE_HELD
    assert any("lease state is 'held'" in item for item in before.refusals)

    _execute(evidence_root, catalog, config)

    after = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert after.facts["writer_lease"] == LEASE_STATE_RELEASED
    assert not any("lease state is 'held'" in item for item in after.refusals)


def test_execute_is_unreachable_under_the_shipped_activation_constant(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    tmp_path: Path,
) -> None:
    """R6 and Decision 104: the shipped constant refuses ``execute``, and touches nothing.

    Deliberately **not** monkeypatched. Every other execute test in this file injects a
    disposable token, which is the only honest way to exercise the machine; this one is the
    complement, and its whole value is that it runs the door the repository actually ships.
    A `monkeypatch.setattr(..., None)` here would prove the gate works when told to be
    ``None`` — the shipped value is the thing in question, so it is read rather than set.

    Two invocation shapes, because the refusal has to be unconditional in both. With the
    private root unset, exit ``3`` must win over the configuration error the unset root would
    otherwise produce. With it set, exit ``3`` must still win, and the fully populated
    evidence root must come through byte-identical: a refusal that read the lease, took the
    lock, or created the recovery namespace before answering would leave a trace here.
    """
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None
    before = _inventory(evidence_root)
    checkout = tmp_path / "checkout"

    with pytest.raises(e0.StageNotEnabledError, match="is None"):
        _execute(evidence_root, catalog, config)

    unset_root = e0.run_reconcile_writer_lease_command(
        mode="execute",
        config=config,
        repository_root=checkout,
        environ={},
    )
    assert unset_root.exit_code == e0.EXIT_STAGE_NOT_ENABLED
    assert any("not enabled" in line for line in unset_root.lines)
    assert not any(EVIDENCE_ROOT_ENV in line for line in unset_root.lines)

    resolvable_root = e0.run_reconcile_writer_lease_command(
        mode="execute",
        config=config,
        repository_root=checkout,
        environ={EVIDENCE_ROOT_ENV: str(evidence_root)},
    )
    assert resolvable_root.exit_code == e0.EXIT_STAGE_NOT_ENABLED
    assert any("not enabled" in line for line in resolvable_root.lines)

    assert stale_lease.read_bytes() == before[str(stale_lease.relative_to(evidence_root))]
    assert _inventory(evidence_root) == before
    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


def test_a_passing_preflight_neither_activates_nor_implies_mutation_authority(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision 104: preflight stays read-only, and a PASS confers nothing.

    This is the shape most likely to be misread by an operator: every predicate holds, the
    ladder reports ``PASS``, and the obvious next inference is that the reconciliation is
    therefore available. It is not, and the report says so on its own face —
    ``reconciliation_enabled`` is rendered as a measured fact, so a PASS that an operator can
    read is never a PASS they can act on while the constant is ``None``.

    Running preflight first and execute immediately after, in one test against one root, is
    the point: a passing preflight is not a reservation, not a handshake, and not a state the
    following execute can consume.
    """
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None
    before = _inventory(evidence_root)

    report = _preflight(evidence_root, catalog, config)
    assert report.passed, report.refusals
    assert report.facts["reconciliation_enabled"] is False
    assert any("reconciliation_enabled" in line and "False" in line for line in report.lines)

    # The command runner takes no catalog or digest option by design (R6), so the accepted
    # identity policy reaches it as a keyword default, substituted here for the disposable
    # catalog's own digests exactly as the operator-surface test does.
    logical, observations = _identity(catalog)
    for function in (e0.reconcile_writer_lease_preflight, e0.reconcile_writer_lease_execute):
        defaults = function.__kwdefaults__
        monkeypatch.setitem(defaults, "expected_catalog_logical_sha256", logical)
        monkeypatch.setitem(defaults, "expected_input_observation_set_sha256", observations)
    environ = {EVIDENCE_ROOT_ENV: str(evidence_root)}
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    passed = e0.run_reconcile_writer_lease_command(
        mode="preflight", config=config, repository_root=checkout, environ=environ
    )
    assert passed.exit_code == e0.EXIT_OK
    assert any("preflight: PASS" in line for line in passed.lines)
    assert any("reconciliation_enabled" in line and "False" in line for line in passed.lines)

    refused = e0.run_reconcile_writer_lease_command(
        mode="execute", config=config, repository_root=checkout, environ=environ
    )
    assert refused.exit_code == e0.EXIT_STAGE_NOT_ENABLED

    assert _inventory(evidence_root) == before
    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


def test_the_shipped_activation_constant_is_disabled() -> None:
    """Accepted Decision 104: the recovery ships **disabled**, and no token ships with it.

    Decision 103 authorizes this surface's implementation and expressly withholds authority
    to reconcile the real lease. Shipping the literal its §8 illustrates would have granted
    in source exactly what the record withheld, which is the defect Decision 104 corrects. A
    later exact owner instrument replaces this literal to authorize one real reconciliation.

    Three assertions, none of them redundant. The source assertion is the load-bearing one: a
    runtime check alone would pass against a module some other test had already overridden.
    The runtime check catches a reassignment made elsewhere in the module rather than at the
    definition. And the token's *absence* from the whole file is what stops the value being
    reintroduced under another name, in a default argument, or in a comment a later reader
    could mistake for the shipped state.

    The disabled state is asserted here as a property of the shipped source, and separately
    exercised as behaviour by
    :func:`test_execute_is_unreachable_under_the_shipped_activation_constant`.
    """
    source = Path(e0.__file__).read_text(encoding="utf-8")
    assert "STALE_WRITER_LEASE_RECOVERY_AUTHORITY: Final[str | None] = None\n" in source
    assert "M3_3_D103_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED" not in source
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None

    # Decision 104 corrects one constant and nothing around it. The other two activation
    # constants are governed by Decision 101 and are asserted in full by
    # `test_m3_e0.py::test_the_shipped_activation_constants_match_the_governing_record`;
    # what matters here is only that this correction did not reach them.
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is not None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is not None


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


def test_the_recovery_command_takes_only_config_and_mode() -> None:
    """R6: none of the prohibited operator options exists on this surface."""
    from disclosure_drift import cli

    recover = _subparser(_subparser(cli.build_parser(), "m3"), "reconcile-writer-lease")
    options = {option for action in recover._actions for option in action.option_strings}  # noqa: SLF001

    assert options == {"-h", "--help", "--config", "--mode"}
    for prohibited in (
        "--force",
        "--pid",
        "--lease-id",
        "--host",
        "--catalog",
        "--lease-file",
        "--evidence-root",
        "--ignore-lock",
        "--skip-check",
        "--run-namespace",
        "--network",
    ):
        assert prohibited not in options
    modes = next(action for action in recover._actions if action.dest == "mode")  # noqa: SLF001
    assert tuple(modes.choices or ()) == ("preflight", "execute")


def test_an_unrecognized_mode_is_a_usage_error(config: _Config, tmp_path: Path) -> None:
    """R6: `verify` is not a mode of this surface, and neither is anything else."""
    for mode in ("verify", "repair", ""):
        result = e0.run_reconcile_writer_lease_command(
            mode=mode, config=config, repository_root=tmp_path, environ={}
        )
        assert result.exit_code == e0.EXIT_USAGE


def test_preflight_without_a_private_root_is_a_configuration_error(
    config: _Config, tmp_path: Path
) -> None:
    """The Decision 094 §7.3 exit table, unchanged: an unset root is exit ``1``."""
    result = e0.run_reconcile_writer_lease_command(
        mode="preflight", config=config, repository_root=tmp_path / "checkout", environ={}
    )
    assert result.exit_code == e0.EXIT_CONFIG_ERROR
    assert any(EVIDENCE_ROOT_ENV in line for line in result.lines)


def test_the_operator_surface_reports_a_refusal_and_a_success_without_a_private_path(
    evidence_root: Path,
    catalog: Path,
    stale_lease: Path,
    config: _Config,
    activated: None,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R6: rendered output carries counts, digest prefixes, enums, and relative names only."""
    # The command runner takes no catalog or digest option by design (R6), so the accepted
    # identity policy reaches it as a keyword default. The disposable catalog's own digests are
    # substituted there rather than a new operator knob being invented for the test.
    logical, observations = _identity(catalog)
    for function in (e0.reconcile_writer_lease_preflight, e0.reconcile_writer_lease_execute):
        defaults = function.__kwdefaults__
        monkeypatch.setitem(defaults, "expected_catalog_logical_sha256", logical)
        monkeypatch.setitem(defaults, "expected_input_observation_set_sha256", observations)
    environ = {EVIDENCE_ROOT_ENV: str(evidence_root)}
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    passed = e0.run_reconcile_writer_lease_command(
        mode="preflight", config=config, repository_root=checkout, environ=environ
    )
    assert passed.exit_code == e0.EXIT_OK
    assert any("preflight: PASS" in line for line in passed.lines)

    done = e0.run_reconcile_writer_lease_command(
        mode="execute", config=config, repository_root=checkout, environ=environ
    )
    assert done.exit_code == e0.EXIT_OK

    refused = e0.run_reconcile_writer_lease_command(
        mode="execute", config=config, repository_root=checkout, environ=environ
    )
    assert refused.exit_code == e0.EXIT_GATE_FAILURE

    for line in (*passed.lines, *done.lines, *refused.lines):
        assert str(evidence_root) not in line
        assert _SYNTHETIC_ROOT_MARKER not in line
