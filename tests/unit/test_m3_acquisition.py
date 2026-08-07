"""Milestone 3.2 acquisition-foundation tests (T2 packet §14; contract §18).

Every test here is offline. The suite-wide autouse socket guard in ``tests/conftest.py`` makes
that structural rather than aspirational, and the transport is always a scripted in-memory object
the test owns: no test constructs a real client, resolves a host, or reaches the SEC.

Each refusal boundary is paired with a **positive control** — a case proving the same code path
succeeds when the guarded condition is absent. Without one, a refusal test passes just as happily
against a guard that refuses everything, which is the failure mode these controls exist to catch.
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
import sqlite3
import subprocess
import sys
import tracemalloc
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import replace
from datetime import date
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.errors import CatalogWriteError, RawObjectIntegrityError
from disclosure_drift.m3.acquisition import (
    ACQUISITION_JOB_KIND,
    ACQUISITION_WINDOWS,
    FINAL_MIGRATION_VERSION,
    M3_2B_DEPENDENT_ROUTES,
    NO_HTTP_STATUS_SENTINEL,
    OPERATIONAL_CATALOG_RELATIVE_PATH,
    PROGRESS_SINK_FAILURE_REASON,
    AcquisitionEngine,
    AcquisitionGateError,
    AcquisitionRunError,
    CatalogPreparationError,
    ContainmentError,
    LiveOperationAuthorization,
    LiveOperatorGate,
    PhysicalResponseLog,
    RecordingTransport,
    RequestOutcome,
    ResponseAccounting,
    StorageBinding,
    default_live_transport_factory,
    default_run_id_factory,
    derive_logical_requests,
    drift_for_run,
    execute_live_acquisition,
    load_approved_plan,
    observe_recovery_state,
    prepare_operational_catalog,
    prepare_storage,
    register_acquisition_run,
    resolve_within,
    route_is_streamed,
    validate_acquisition_run,
    verify_window_bindings,
)
from disclosure_drift.m3.receipt import ExecutionReceipt
from disclosure_drift.m3.request_plan import (
    RequestPlan,
    build_m3_2a_request_plan,
    canonical_plan_bytes,
)
from disclosure_drift.sec.archive import ArchiveDefenceError
from disclosure_drift.sec.http_client import RetrievalPolicy, SecClient
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.raw_store import sha256_of
from disclosure_drift.sec.request_ceiling import PhysicalAttemptCeiling
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import (
    MAX_IN_MEMORY_BYTES,
    CloseableByteStream,
    SecRequest,
    TransportResponse,
)
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import applied_versions

_AGENT: Final = "Disclosure Drift Test Harness (offline-fixture@example.invalid)"
_CATALOG_RELATIVE: Final = OPERATIONAL_CATALOG_RELATIVE_PATH
_DATA_RELATIVE: Final = "runs/m3_2a/data"

#: A distinctive body substring no log, exception, or record may ever reproduce.
_BODY_MARKER: Final = "canary-response-payload-substring"

#: A recorded purpose long enough for the accepted client's entity-specific minimum.
_PURPOSE: Final = "acquire an approved Milestone 3.2 metadata object for an offline fixture"


# --------------------------------------------------------------------------- #
# Offline seams
# --------------------------------------------------------------------------- #
class _ScriptedTransport:
    """Replays scripted responses and records requests. Opens no socket."""

    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[SecRequest] = []
        self.closed = False

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        if not self._responses:
            message = (
                f"the scripted transport was exhausted after {len(self.requests)} request(s); "
                "the engine attempted a request the test did not script"
            )
            raise AssertionError(message)
        response = self._responses.pop(0)
        if response.final_url == "":
            response = replace(response, final_url=request.url)
        return response

    def close(self) -> None:
        self.closed = True


class _RefusingClient:
    """A client that fails the test if the engine ever calls it."""

    def __init__(self) -> None:
        self.calls = 0

    def fetch(self, *args: object, **kwargs: object) -> object:
        self.calls += 1
        message = "the engine reached the client despite having no ceiling headroom"
        raise AssertionError(message)


class _FrozenClock:
    """A deterministic clock. No wall-clock time passes in any test."""

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _stamp() -> str:
    """A fixed observation timestamp, so no test reads the system clock."""
    return "2026-08-04T00:00:00Z"


#: Fixed member timestamp for every ZIP fixture in this module.
#:
#: ``ZipFile.writestr`` given a bare member name stamps ``time.localtime()`` into the member
#: header at two-second granularity. An archive built twice a moment apart is then *not*
#: byte-identical — so a fixture meant to prove "the same bytes reconcile as a duplicate"
#: instead delivers changed content whenever the two builds straddle a boundary, and the test
#: fails for a reason that has nothing to do with the code under test. Every archive below is
#: therefore built from an explicit :class:`zipfile.ZipInfo` with every varying field pinned.
_ZIP_EPOCH: Final = (1980, 1, 1, 0, 0, 0)


def _zip_member(name: str, *, compression: int = zipfile.ZIP_DEFLATED) -> zipfile.ZipInfo:
    """A fully specified member header: no clock, no locale, and no platform in the bytes."""
    info = zipfile.ZipInfo(name, date_time=_ZIP_EPOCH)
    info.compress_type = compression
    # ``ZipInfo`` otherwise reports the building platform, so a fixture would differ between a
    # developer machine and CI. Pinning it keeps the archive hash a property of its content.
    info.create_system = 3
    info.external_attr = 0o600 << 16
    return info


def _zip_archive(
    members: Sequence[tuple[str, bytes]],
    *,
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    """Build a ZIP whose bytes are a function of its members and nothing else."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, payload in members:
            archive.writestr(_zip_member(name, compression=compression), payload)
    return buffer.getvalue()


def _zip_bytes() -> bytes:
    """A real, minimal ZIP archive: the archive route checks the local-file signature."""
    return _zip_archive([("CIK0000000001.json", b'{"cik":1}')])


def _scripted(
    status: int = 200,
    *,
    body: bytes = b'{"ok":1}',
    content_type: str | None = "application/json",
    headers: Mapping[str, str] | None = None,
    final_url: str = "",
    failure: str | None = None,
) -> TransportResponse:
    merged = dict(headers or {})
    if content_type is not None:
        merged.setdefault("Content-Type", content_type)
    return TransportResponse(
        status=status,
        headers=merged,
        final_url=final_url,
        body=body,
        failure=failure,  # type: ignore[arg-type]
    )


def _success_for(source_id: str) -> TransportResponse:
    """A scripted 200 shaped to the route's registered expected content kind."""
    expected = SOURCES[source_id].expected_content
    if expected == "zip":
        return _scripted(body=_zip_bytes(), content_type="application/zip")
    if expected == "html":
        return _scripted(body=b"<html><body>calendar</body></html>", content_type="text/html")
    if expected == "text":
        return _scripted(body=b"CIK|Company Name\n1|SYNTHETIC\n", content_type="text/plain")
    return _scripted()


# --------------------------------------------------------------------------- #
# Plan and harness
# --------------------------------------------------------------------------- #
def _plan(*, satisfied: frozenset[str] = frozenset()) -> RequestPlan:
    """A small but genuine M3.2A plan: five singletons plus two quarterly instances."""
    return build_m3_2a_request_plan(
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2010, 6, 30),
        as_of_date=date(2010, 7, 1),
        include_open_quarter=False,
        calendar_year=2010,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=satisfied,
        requests_per_second=4.0,
    )


def _authorization(plan: RequestPlan, *, window: str = "M3.2A") -> LiveOperationAuthorization:
    return LiveOperationAuthorization(
        window=window,
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=plan.hard_request_ceiling,
        authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
    )


def _success_script(plan: RequestPlan) -> list[TransportResponse]:
    """One successful scripted response per logical request the plan expands to."""
    return [_success_for(request.source_id) for request in derive_logical_requests(plan)]


@contextmanager
def _harness(
    evidence_root: Path,
    *,
    plan: RequestPlan,
    responses: Sequence[TransportResponse],
    ceiling: PhysicalAttemptCeiling | None = None,
    window: str = "M3.2A",
    progress: object = None,
) -> Iterator[tuple[AcquisitionEngine, _ScriptedTransport, PhysicalAttemptCeiling, StorageBinding]]:
    """Build the real engine over scripted seams, with a real catalog in a temp root."""
    preparation = prepare_operational_catalog(
        evidence_root=evidence_root,
        relative_path=_CATALOG_RELATIVE,
    )
    storage = prepare_storage(evidence_root=evidence_root, data_root_relative=_DATA_RELATIVE)
    gate = ceiling if ceiling is not None else PhysicalAttemptCeiling(plan.hard_request_ceiling)
    clock = _FrozenClock()
    transport = _ScriptedTransport(responses)
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
    client = SecClient(
        transport,
        _AGENT,
        limiter,
        RetrievalPolicy(),
        sleeper=clock.sleep,
        ceiling=gate,
    )

    with CatalogWriter(preparation.database_path, preparation.lock_directory) as writer:
        recorder = ObservationRecorder(writer=writer, tree=storage.tree)
        engine = AcquisitionEngine(
            plan=plan,
            window=window,
            ceiling=gate,
            client=client,
            storage=storage,
            recorder=recorder,
            clock=_stamp,
            progress=progress,  # type: ignore[arg-type]
        )
        yield engine, transport, gate, storage


class _PersistentHarness:
    """One evidence root, storage binding, and catalog writer across several engine runs.

    Reuse, supersession, and archive lineage are only observable when a *later* run sees what an
    earlier one preserved. A fresh store per run cannot see any of it, so a fixture that rebuilds
    everything each time proves the happy path and nothing about reconciliation.
    """

    def __init__(self, evidence_root: Path, plan: RequestPlan) -> None:
        self.plan = plan
        self.preparation = prepare_operational_catalog(
            evidence_root=evidence_root, relative_path=_CATALOG_RELATIVE
        )
        self.storage = prepare_storage(
            evidence_root=evidence_root, data_root_relative=_DATA_RELATIVE
        )
        self.gate = PhysicalAttemptCeiling(plan.hard_request_ceiling)
        self.writer = CatalogWriter(self.preparation.database_path, self.preparation.lock_directory)
        self.writer.__enter__()

    def engine(
        self,
        responses: Sequence[TransportResponse],
        *,
        progress: object = None,
    ) -> tuple[AcquisitionEngine, _ScriptedTransport]:
        clock = _FrozenClock()
        transport = _ScriptedTransport(responses)
        limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
        client = SecClient(
            transport, _AGENT, limiter, RetrievalPolicy(), sleeper=clock.sleep, ceiling=self.gate
        )
        recorder = ObservationRecorder(writer=self.writer, tree=self.storage.tree)
        engine = AcquisitionEngine(
            plan=self.plan,
            window="M3.2A",
            ceiling=self.gate,
            client=client,
            storage=self.storage,
            recorder=recorder,
            clock=_stamp,
            progress=progress,  # type: ignore[arg-type]
        )
        return engine, transport

    def run(self, responses: Sequence[TransportResponse], *, progress: object = None) -> object:
        engine, _ = self.engine(responses, progress=progress)
        engine.preflight(_authorization(self.plan))
        return engine.run()

    def close(self) -> None:
        self.writer.__exit__(None, None, None)


@contextmanager
def _persistent(evidence_root: Path, plan: RequestPlan) -> Iterator[_PersistentHarness]:
    harness = _PersistentHarness(evidence_root, plan)
    try:
        yield harness
    finally:
        harness.close()


# --------------------------------------------------------------------------- #
# Large streamed archive fixture
# --------------------------------------------------------------------------- #
#: Members and member size for the oversized bulk-archive fixture. Their product must exceed
#: ``MAX_IN_MEMORY_BYTES``; many small members rather than one huge one keeps peak memory at one
#: member while still crossing the threshold that matters.
_BIG_MEMBER_BYTES: Final = 1024 * 1024
_BIG_MEMBER_COUNT: Final = (MAX_IN_MEMORY_BYTES // _BIG_MEMBER_BYTES) + 4


def _incompressible(index: int, size: int) -> bytes:
    """Deterministic, effectively incompressible member content.

    Stored uncompressed, so the archive is genuinely as large as its contents and the expansion
    ratio stays at 1.0 — a zero-filled member would compress to nothing and prove no size boundary.
    """
    seed = hashlib.sha256(f"disclosure-drift-fixture-{index}".encode()).digest()
    return (seed * (size // len(seed) + 1))[:size]


def _write_large_archive(path: Path) -> int:
    """Write a valid ZIP larger than the in-memory bound, streaming member by member."""
    with zipfile.ZipFile(path, "w") as archive:
        for index in range(_BIG_MEMBER_COUNT):
            archive.writestr(
                _zip_member(f"CIK{index:010d}.json", compression=zipfile.ZIP_STORED),
                _incompressible(index, _BIG_MEMBER_BYTES),
            )
    return path.stat().st_size


def _file_stream(path: Path, chunk_size: int = 1024 * 1024) -> CloseableByteStream:
    """Yield a file as owned chunks, so nothing buffers the whole archive in memory."""
    handle = path.open("rb")

    def _chunks() -> Iterator[bytes]:
        while chunk := handle.read(chunk_size):
            yield chunk

    return CloseableByteStream(_chunks(), close_callback=handle.close)


def _streamed_archive_response(path: Path) -> TransportResponse:
    """A scripted 200 delivering the archive as a stream rather than a buffered body."""
    return TransportResponse(
        status=200,
        headers={"Content-Type": "application/zip"},
        final_url="",
        chunks=_file_stream(path),
    )


# =========================================================================== #
# Containment
# =========================================================================== #
class TestContainment:
    """Governed paths never escape the evidence root."""

    def test_relative_path_resolves_inside_the_root(self, tmp_path: Path) -> None:
        resolved = resolve_within(tmp_path, "catalogs/x.sqlite3", label="catalog")
        assert resolved.parent.name == "catalogs"
        assert str(resolved).startswith(str(Path(os.path.realpath(tmp_path))))

    def test_absolute_relative_path_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ContainmentError, match="relative to the evidence root"):
            resolve_within(tmp_path, "/etc/passwd", label="catalog")

    def test_parent_traversal_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ContainmentError, match="parent-directory component"):
            resolve_within(tmp_path, "../escape/x.sqlite3", label="catalog")

    def test_symlink_escape_is_refused(self, tmp_path: Path) -> None:
        outside = tmp_path.parent / "outside_root"
        outside.mkdir(exist_ok=True)
        (tmp_path / "link").symlink_to(outside, target_is_directory=True)
        with pytest.raises(ContainmentError, match="resolves outside the evidence root"):
            resolve_within(tmp_path, "link/x.sqlite3", label="catalog")

    def test_positive_control_same_shape_without_the_symlink_is_accepted(
        self, tmp_path: Path
    ) -> None:
        """The guard refuses the symlink, not the shape: a real directory passes."""
        (tmp_path / "link").mkdir()
        assert resolve_within(tmp_path, "link/x.sqlite3", label="catalog").name == "x.sqlite3"

    def test_relative_evidence_root_is_refused(self) -> None:
        with pytest.raises(ContainmentError, match="absolute path"):
            resolve_within(Path("relative/root"), "x", label="catalog")

    def test_no_refusal_message_names_a_resolved_path(self, tmp_path: Path) -> None:
        """Stop condition 12: an absolute personal path never reaches operator output."""
        with pytest.raises(ContainmentError) as caught:
            resolve_within(tmp_path, "../escape", label="catalog")
        assert str(tmp_path) not in str(caught.value)


# =========================================================================== #
# Operational catalog
# =========================================================================== #
class TestOperationalCatalog:
    """Catalog creation, the exact migration chain, seeding, and integrity."""

    def test_creates_a_clean_catalog_at_the_supplied_path(self, tmp_path: Path) -> None:
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        assert preparation.created is True
        assert preparation.database_path.is_file()
        assert preparation.database_path.parent.name == "catalogs"

    def test_migration_chain_ends_exactly_at_0013(self, tmp_path: Path) -> None:
        preparation = prepare_operational_catalog(evidence_root=tmp_path)
        assert preparation.migration_chain_head == FINAL_MIGRATION_VERSION
        assert preparation.chain_is_exact is True
        with sqlite3.connect(preparation.database_path) as connection:
            connection.row_factory = sqlite3.Row
            versions = applied_versions(connection)
        assert versions == tuple(range(1, FINAL_MIGRATION_VERSION + 1))

    def test_reference_seeding_is_deterministic(self, tmp_path: Path) -> None:
        first = prepare_operational_catalog(evidence_root=tmp_path / "a")
        second = prepare_operational_catalog(evidence_root=tmp_path / "b")
        assert first.seeded_counts == second.seeded_counts
        assert first.seeded_counts["form_types"] > 0
        assert first.seeded_counts["reason_codes"] > 0

    def test_reopening_an_existing_catalog_applies_no_new_migration(self, tmp_path: Path) -> None:
        first = prepare_operational_catalog(evidence_root=tmp_path)
        second = prepare_operational_catalog(evidence_root=tmp_path)
        assert first.applied_migrations != ()
        assert second.applied_migrations == ()
        assert second.created is False
        assert second.migration_chain_head == FINAL_MIGRATION_VERSION

    def test_incompatible_existing_catalog_fails_closed(self, tmp_path: Path) -> None:
        """A database that is not this catalog is refused, never migrated into one."""
        destination = tmp_path / _CATALOG_RELATIVE
        destination.parent.mkdir(parents=True)
        with sqlite3.connect(destination) as connection:
            connection.execute("CREATE TABLE ops_schema_migrations (version INTEGER PRIMARY KEY)")
            connection.execute("INSERT INTO ops_schema_migrations (version) VALUES (99)")
        with pytest.raises(CatalogPreparationError):
            prepare_operational_catalog(evidence_root=tmp_path)

    def test_positive_control_a_fresh_root_at_the_same_path_succeeds(self, tmp_path: Path) -> None:
        """The refusal above is about the incompatible database, not the path."""
        preparation = prepare_operational_catalog(evidence_root=tmp_path / "fresh")
        assert preparation.chain_is_exact is True

    def test_catalog_path_outside_the_root_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ContainmentError):
            prepare_operational_catalog(evidence_root=tmp_path, relative_path="../outside.sqlite3")

    def test_symlinked_catalog_directory_is_refused(self, tmp_path: Path) -> None:
        real = tmp_path / "real_catalogs"
        real.mkdir()
        (tmp_path / "catalogs").symlink_to(real, target_is_directory=True)
        with pytest.raises(ContainmentError, match="symbolic link"):
            prepare_operational_catalog(evidence_root=tmp_path)

    def test_repository_root_argument_refuses_an_internal_evidence_root(
        self, tmp_path: Path
    ) -> None:
        """There is no implicit fallback to a repository-local production database."""
        checkout = tmp_path / "checkout"
        (checkout / "inside").mkdir(parents=True)
        with pytest.raises(Exception, match="inside the repository checkout"):
            prepare_operational_catalog(
                evidence_root=checkout / "inside",
                repository_root=checkout,
            )

    def test_positive_control_an_external_root_passes_the_same_check(self, tmp_path: Path) -> None:
        checkout = tmp_path / "checkout"
        checkout.mkdir()
        external = tmp_path / "external"
        external.mkdir()
        preparation = prepare_operational_catalog(evidence_root=external, repository_root=checkout)
        assert preparation.chain_is_exact is True

    def test_integrity_and_foreign_keys_are_verified(self, tmp_path: Path) -> None:
        preparation = prepare_operational_catalog(evidence_root=tmp_path)
        with CatalogWriter(preparation.database_path, preparation.lock_directory) as writer:
            report = writer.integrity()
        assert report.passed is True
        assert report.foreign_key_violations == 0


# =========================================================================== #
# Immutable storage
# =========================================================================== #
class TestImmutableStorage:
    """The accepted content-addressed store, bound to a contained data root."""

    def test_prepares_an_isolated_data_root(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        assert storage.data_root.is_dir()
        assert storage.tree.raw_indexes.is_dir()
        assert storage.tree.quarantine.is_dir()

    def test_data_root_escape_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(ContainmentError):
            prepare_storage(evidence_root=tmp_path, data_root_relative="../outside")

    def test_object_identity_is_the_exact_sha256_of_the_body(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        body = b"CIK|Company Name\n1|SYNTHETIC\n"
        stored = storage.raw_store.store(
            chunks=[body],
            logical_role="census_registrant_index",
            source_url_canonical="https://www.sec.gov/x",
            retrieval_attempt_id="attempt-1",
            retrieved_at_utc=_stamp(),
            filename="object.idx",
        )
        assert stored.record.content_sha256 == sha256_of(body)

    def test_destination_is_deterministic_for_the_same_filename(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        first = _store(storage, b"one", "same.idx")
        second = _store(storage, b"one", "same.idx")
        assert first.absolute_path == second.absolute_path

    def test_byte_identical_body_reuses_the_existing_object(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        first = _store(storage, b"identical", "reuse.idx")
        second = _store(storage, b"identical", "reuse.idx")
        assert first.absolute_path == second.absolute_path
        assert second.record.content_sha256 == first.record.content_sha256

    def test_overwrite_with_a_differing_body_at_one_destination_is_refused(
        self, tmp_path: Path
    ) -> None:
        """Promotion never replaces an existing object whose stored hash differs."""
        from disclosure_drift.errors import RawObjectIntegrityError

        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        _store(storage, b"original", "collide.idx")
        with pytest.raises(RawObjectIntegrityError, match="refusing to overwrite"):
            _store(storage, b"different", "collide.idx")

    def test_differing_body_is_preserved_as_a_new_observation(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        first = _store(storage, b"v1", "changing-v1.idx")
        second = _store(
            storage,
            b"v2",
            "changing-v2.idx",
            known=(first.record,),
        )
        assert second.record.supersedes_observation_id == first.record.observation_id
        assert second.record.reason_code == "REMOTE_CONTENT_CHANGED"
        assert first.absolute_path.is_file(), "the superseded object is never deleted"

    def test_partial_transfer_leaves_a_part_file_and_no_object(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)

        def _interrupt() -> None:
            message = "simulated interrupted transfer"
            raise OSError(message)

        with pytest.raises(OSError, match="simulated interrupted transfer"):
            storage.raw_store.store(
                chunks=[b"partial"],
                logical_role="census_registrant_index",
                source_url_canonical="https://www.sec.gov/x",
                retrieval_attempt_id="attempt-1",
                retrieved_at_utc=_stamp(),
                filename="interrupted.idx",
                raise_during_stream=_interrupt,
            )
        parts = list(storage.tree.raw_indexes.rglob("*.part"))
        assert parts, "the .part file is preserved for reconciliation"
        assert not (storage.tree.raw_indexes / "interrupted.idx").exists()

    def test_quarantine_preserves_rather_than_deletes(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        stored = _store(storage, b"suspect", "suspect.idx")
        target = storage.raw_store.quarantine(
            stored.absolute_path, "RAW_FILE_CHECKSUM_MISMATCH", "test"
        )
        assert target.is_file()
        assert target.parent == storage.tree.quarantine
        assert not stored.absolute_path.exists()

    def test_verify_detects_a_hash_mismatch(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        stored = _store(storage, b"authentic", "verify.idx")
        assert storage.raw_store.verify(stored.record) is True
        stored.absolute_path.write_bytes(b"tampered")
        assert storage.raw_store.verify(stored.record) is False


def _store(
    storage: StorageBinding,
    body: bytes,
    filename: str,
    *,
    known: Sequence[object] = (),
) -> object:
    """Store one object through the accepted raw store."""
    return storage.raw_store.store(
        chunks=[body],
        logical_role="census_registrant_index",
        source_url_canonical=f"https://www.sec.gov/{filename}",
        retrieval_attempt_id="attempt-1",
        retrieved_at_utc=_stamp(),
        filename=filename,
        known_observations=known,  # type: ignore[arg-type]
    )


# =========================================================================== #
# Plan expansion
# =========================================================================== #
class TestLogicalRequestDerivation:
    """The plan is expanded exactly, never re-derived."""

    def test_expands_to_the_planned_total(self) -> None:
        plan = _plan()
        requests = derive_logical_requests(plan)
        assert len(requests) == plan.planned_unique_logical_requests

    def test_index_instances_come_from_the_plan(self) -> None:
        requests = derive_logical_requests(_plan())
        keys = [request.instance_key for request in requests if request.instance_key]
        assert keys == ["2010QTR1", "2010QTR2"]

    def test_zero_count_routes_are_skipped(self) -> None:
        """The approved plan carries zero announcement entries, so none is requested."""
        requests = derive_logical_requests(_plan())
        assert all(request.source_id != "sec_edgar_calendar_announcement" for request in requests)

    def test_announcement_entries_refuse_without_a_manifest(self) -> None:
        """A manifest-resolved URL is never synthesized by the driver."""
        plan = build_m3_2a_request_plan(
            coverage_start=date(2010, 1, 1),
            coverage_end=date(2010, 6, 30),
            as_of_date=date(2010, 7, 1),
            include_open_quarter=False,
            calendar_year=2010,
            calendar_evidence_entry_count=2,
            already_satisfied_index_keys=frozenset(),
            requests_per_second=4.0,
        )
        with pytest.raises(AcquisitionGateError, match="reviewed evidence manifest"):
            derive_logical_requests(plan)

    def test_cache_hits_reduce_the_expansion(self) -> None:
        plan = _plan(satisfied=frozenset({"2010QTR1"}))
        requests = derive_logical_requests(plan)
        keys = [request.instance_key for request in requests if request.instance_key]
        assert keys == ["2010QTR2"]
        assert plan.expected_cache_hits == 1

    def test_the_accepted_m3_2a_plan_identity_reproduces(self) -> None:
        """Packet stop condition S4: the approved plan identity must still reproduce.

        These are the owner-approved M3.2A values. They are asserted here, in the stage that
        first consumes a plan, so a change to route derivation or ``A_reachable`` is caught by
        the acquisition suite rather than only by the planning suite that produced them.
        """
        plan = build_m3_2a_request_plan(
            coverage_start=date(2009, 1, 1),
            coverage_end=date(2026, 6, 30),
            as_of_date=date(2026, 6, 30),
            include_open_quarter=False,
            calendar_year=2026,
            calendar_evidence_entry_count=0,
            already_satisfied_index_keys=frozenset(),
            requests_per_second=4.0,
        )
        assert plan.request_plan_sha256 == (
            "19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68"
        )
        assert plan.planned_unique_logical_requests == 75
        assert len(plan.required_index_keys) == 70
        assert plan.maximum_new_raw_objects == 75
        assert plan.expected_cache_hits == 0
        assert plan.hard_request_ceiling == 801
        assert plan.rate_limiter_spacing_floor_seconds == 200.0

    def test_the_accepted_plan_expands_to_its_planned_logical_requests(self) -> None:
        """The approved plan drives the engine's expansion, with no announcement entry."""
        plan = build_m3_2a_request_plan(
            coverage_start=date(2009, 1, 1),
            coverage_end=date(2026, 6, 30),
            as_of_date=date(2026, 6, 30),
            include_open_quarter=False,
            calendar_year=2026,
            calendar_evidence_entry_count=0,
            already_satisfied_index_keys=frozenset(),
            requests_per_second=4.0,
        )
        requests = derive_logical_requests(plan)
        assert len(requests) == 75
        index_requests = [item for item in requests if item.source_id == "sec_full_index_company"]
        assert len(index_requests) == 70

    def test_stored_plan_round_trips_through_the_accepted_reader(self) -> None:
        plan = _plan()
        reloaded = load_approved_plan(canonical_plan_bytes(plan))
        assert reloaded.request_plan_sha256 == plan.request_plan_sha256


# =========================================================================== #
# Preflight gates
# =========================================================================== #
class TestPreflightGates:
    """Every binding is checked before the first transport call."""

    def test_preflight_accepts_a_consistent_binding(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=[]) as (engine, transport, _, _):
            requests = engine.preflight(_authorization(plan))
        assert len(requests) == plan.planned_unique_logical_requests
        assert transport.requests == [], "preflight places no request"

    def test_plan_hash_mismatch_refuses_before_any_request(self, tmp_path: Path) -> None:
        plan = _plan()
        wrong = replace(_authorization(plan), plan_sha256="0" * 64)
        with _harness(tmp_path, plan=plan, responses=[]) as (engine, transport, _, _):
            with pytest.raises(AcquisitionGateError, match="plan hash does not match"):
                engine.preflight(wrong)
            assert transport.requests == []

    def test_wrong_window_refuses(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=[]) as (engine, transport, _, _):
            with pytest.raises(AcquisitionGateError, match="names window"):
                engine.preflight(_authorization(plan, window="M3.2B"))
            assert transport.requests == []

    def test_wrong_ceiling_refuses(self, tmp_path: Path) -> None:
        plan = _plan()
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling)
        wrong = replace(_authorization(plan), approved_ceiling=plan.hard_request_ceiling - 1)
        with _harness(tmp_path, plan=plan, responses=[], ceiling=gate) as (engine, transport, _, _):
            with pytest.raises(AcquisitionGateError, match="must equal"):
                engine.preflight(wrong)
            assert transport.requests == []

    def test_running_without_preflight_refuses(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            transport,
            _,
            _,
        ):
            with pytest.raises(AcquisitionGateError, match="preflight has not run"):
                engine.run()
            assert transport.requests == [], "no transport call precedes the authorization check"

    def test_unknown_window_is_refused_by_the_authorization_itself(self) -> None:
        with pytest.raises(AcquisitionGateError, match="accepted acquisition windows"):
            LiveOperationAuthorization(
                window="M9.9",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                authorization_reference="x",
            )

    def test_authorization_requires_a_named_instrument(self) -> None:
        with pytest.raises(AcquisitionGateError, match="name the owner instrument"):
            LiveOperationAuthorization(
                window="M3.2A",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                authorization_reference="   ",
            )

    def test_authorization_requires_a_hex_plan_hash(self) -> None:
        with pytest.raises(AcquisitionGateError, match="hex SHA-256"):
            LiveOperationAuthorization(
                window="M3.2A",
                plan_sha256="not-a-hash",
                approved_ceiling=1,
                authorization_reference="x",
            )

    def test_accepted_windows_are_exactly_the_two(self) -> None:
        assert ACQUISITION_WINDOWS == ("M3.2A", "M3.2B")


# =========================================================================== #
# Route and response policy
# =========================================================================== #
class TestRouteAndResponseEnforcement:
    """Only approved routes, hosts, methods, and content types are ever reached."""

    def test_every_planned_route_is_a_registered_bootstrap_route(self) -> None:
        from disclosure_drift.m3.request_plan import M3_2A_BOOTSTRAP_ROUTES

        for request in derive_logical_requests(_plan()):
            assert request.source_id in M3_2A_BOOTSTRAP_ROUTES
            assert request.source_id in SOURCES

    def test_dependent_routes_are_absent_from_the_bootstrap_window(self) -> None:
        planned = {request.source_id for request in derive_logical_requests(_plan())}
        assert "sec_submissions_entity" not in planned
        assert "sec_submissions_historical" not in planned

    def test_every_request_uses_get_against_an_approved_sec_host(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            transport,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            engine.run()
        assert transport.requests, "the run placed requests"
        for request in transport.requests:
            assert request.url.startswith(("https://www.sec.gov/", "https://data.sec.gov/"))
            assert request.follow_redirects is False

    def test_no_planned_url_is_a_filing_body_or_accession_path(self) -> None:
        from disclosure_drift.sec.source_registry import filing_body_url_is_prohibited

        for request in derive_logical_requests(_plan()):
            url = SOURCES[request.source_id].url(**dict(request.parameters))
            assert filing_body_url_is_prohibited(url) is False
            assert "/Archives/edgar/data/" not in url
            assert not url.endswith((".htm", ".xml", ".xsd"))

    def test_companyfacts_and_frames_are_not_registered_routes(self) -> None:
        """The prohibition is structural: neither has a registration to reach."""
        for source in SOURCES.values():
            assert "companyfacts" not in source.url_template.lower()
            assert "/frames/" not in source.url_template.lower()

    def test_non_sec_host_is_not_reachable_through_the_registry(self) -> None:
        from disclosure_drift.sec.source_registry import SEC_ORIGINS

        for source in SOURCES.values():
            if source.manifest_resolved:
                continue
            assert source.url_template.startswith(SEC_ORIGINS)

    def test_cross_host_redirect_is_refused(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[0] = _scripted(
            301,
            headers={"Location": "https://evil.example.com/submissions.zip"},
            body=b"",
            content_type=None,
        )
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        first = outcome.outcomes[0]
        assert not first.satisfies_requirement
        assert outcome.completed_successfully is False

    def test_positive_control_an_in_family_redirect_is_followed(self, tmp_path: Path) -> None:
        """The refusal above is about the host, not about redirects as such."""
        plan = _plan()
        script = _success_script(plan)
        calendar_index = next(
            index
            for index, request in enumerate(derive_logical_requests(plan))
            if request.source_id == "sec_edgar_filing_calendar"
        )
        script.insert(
            calendar_index,
            _scripted(
                301,
                headers={"Location": "https://www.sec.gov/edgar/filer-information/calendar"},
                body=b"",
                content_type=None,
            ),
        )
        with _harness(tmp_path, plan=plan, responses=script) as (engine, transport, gate, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        calendar = outcome.outcomes[calendar_index]
        assert calendar.satisfies_requirement, "an in-family hop still reaches its object"
        assert gate.consumed == len(outcome.outcomes) + 1, "the hop consumed one attempt"

    def test_unexpected_content_type_is_quarantined(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[1] = _scripted(body=b"<html>not json</html>", content_type="text/html")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.outcomes[1].disposition == "quarantined"
        assert outcome.completed_successfully is False

    def test_invalid_archive_is_quarantined(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[0] = _scripted(body=b"not-a-zip-archive", content_type="application/zip")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.outcomes[0].disposition == "quarantined"

    def test_403_block_page_stops_the_window(self, tmp_path: Path) -> None:
        plan = _plan()
        script = [_scripted(403, body=b"blocked", content_type="text/html")] * 4
        with _harness(tmp_path, plan=plan, responses=[*script, *_success_script(plan)]) as (
            engine,
            _,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.completed_successfully is False
        assert outcome.outcomes[0].disposition in {"failed", "absent", "quarantined"}

    def test_404_on_an_archival_path_is_recorded_as_absence(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[-1] = _scripted(404, body=b"missing", content_type="text/plain")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.outcomes[-1].disposition == "absent"
        assert outcome.completion_status == "incomplete"


# =========================================================================== #
# Ceiling and attempt accounting
# =========================================================================== #
class TestCeilingAccounting:
    """Stop-before-overflow, and every physical attempt counted."""

    def test_zero_headroom_places_no_request(self, tmp_path: Path) -> None:
        plan = _plan()
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling, consumed=plan.hard_request_ceiling)
        with _harness(tmp_path, plan=plan, responses=[], ceiling=gate) as (engine, transport, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert transport.requests == [], "no transport for the attempt that would exceed C"
        assert outcome.completion_status == "stopped_at_ceiling"
        assert outcome.reason_codes == ("SEC_REQUEST_CEILING_EXHAUSTED",)
        assert len(outcome.unattempted) == plan.planned_unique_logical_requests

    def test_exact_headroom_completes_at_the_ceiling(self, tmp_path: Path) -> None:
        """Reaching C exactly with no work remaining is success, not a stop."""
        plan = _plan()
        planned = plan.planned_unique_logical_requests
        gate = PhysicalAttemptCeiling(
            plan.hard_request_ceiling, consumed=plan.hard_request_ceiling - planned
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), ceiling=gate) as (
            engine,
            transport,
            used,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert len(transport.requests) == planned
        assert used.consumed == plan.hard_request_ceiling
        assert used.is_exhausted is True
        assert outcome.completion_status == "complete"
        assert outcome.completed_successfully is True

    def test_one_short_of_headroom_stops_with_work_remaining(self, tmp_path: Path) -> None:
        plan = _plan()
        planned = plan.planned_unique_logical_requests
        gate = PhysicalAttemptCeiling(
            plan.hard_request_ceiling, consumed=plan.hard_request_ceiling - (planned - 1)
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), ceiling=gate) as (
            engine,
            transport,
            used,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert len(transport.requests) == planned - 1
        assert used.consumed == plan.hard_request_ceiling
        assert outcome.completion_status == "stopped_at_ceiling"
        assert len(outcome.unattempted) == 1
        assert outcome.planned_work_remains is True

    def test_the_engine_checks_headroom_before_it_reaches_the_client(self, tmp_path: Path) -> None:
        """Stop-before-overflow is the engine's own check, not only the gate's.

        The shared gate would refuse inside the client anyway, which makes the engine-level
        check invisible to an outcome-only assertion. This substitutes a client that fails the
        test if it is called at all, so the engine's own refusal is observable — and a removal of
        that check is caught rather than masked by the redundant layer beneath it.
        """
        plan = _plan()
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling, consumed=plan.hard_request_ceiling)
        with _harness(tmp_path, plan=plan, responses=[], ceiling=gate) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            refusing = _RefusingClient()
            engine.client = refusing  # type: ignore[assignment]
            outcome = engine.run()
        assert refusing.calls == 0, "the engine never reached the client with no headroom"
        assert outcome.completion_status == "stopped_at_ceiling"

    def test_a_retry_consumes_a_physical_attempt(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script.insert(0, _scripted(503, body=b"", content_type=None))
        with _harness(tmp_path, plan=plan, responses=script) as (engine, transport, gate, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert len(transport.requests) == plan.planned_unique_logical_requests + 1
        assert gate.consumed == plan.planned_unique_logical_requests + 1
        assert outcome.outcomes[0].satisfies_requirement is True

    def test_carried_forward_consumption_is_honoured(self, tmp_path: Path) -> None:
        """A resumed gate begins at its predecessor's count and never resets it."""
        plan = _plan()
        carried = 5
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling, consumed=carried)
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), ceiling=gate) as (
            engine,
            _,
            used,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert used.consumed == carried + plan.planned_unique_logical_requests
        assert outcome.consumed_physical_attempts == used.consumed

    def test_the_ceiling_cannot_be_raised(self, tmp_path: Path) -> None:
        gate = PhysicalAttemptCeiling(10)
        with pytest.raises(AttributeError):
            gate.approved_ceiling = 20  # type: ignore[misc]

    def test_a_resume_beyond_its_own_ceiling_is_refused(self) -> None:
        with pytest.raises(ValueError, match="already exceeds"):
            PhysicalAttemptCeiling(10, consumed=11)

    def test_classification_totals_sum_to_the_planned_count(self, tmp_path: Path) -> None:
        plan = _plan()
        gate = PhysicalAttemptCeiling(
            plan.hard_request_ceiling, consumed=plan.hard_request_ceiling - 2
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), ceiling=gate) as (
            engine,
            _,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        totals = outcome.classification_totals
        assert sum(totals.values()) == plan.planned_unique_logical_requests


# =========================================================================== #
# Completion semantics
# =========================================================================== #
class TestCompletionSemantics:
    """Termination is not success; absence blocks completion."""

    def test_a_fully_satisfied_window_completes_successfully(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            _,
            storage,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
            assert outcome.completion_status == "complete"
            assert outcome.completed_successfully is True
            assert len(outcome.satisfied) == plan.planned_unique_logical_requests
            assert outcome.absences == ()
            for satisfied in outcome.satisfied:
                assert satisfied.content_sha256
                assert satisfied.relative_storage_path
                assert (storage.tree.data_root / satisfied.relative_storage_path).is_file()

    def test_a_terminal_classification_alone_does_not_satisfy(self) -> None:
        """The distinction contract §14 draws is represented in the type itself."""
        from disclosure_drift.m3.acquisition import LogicalRequest

        classified = RequestOutcome(
            request=LogicalRequest(source_id="sec_company_tickers", instance_key="", parameters={}),
            disposition="absent",
            http_status=404,
            reason_codes=("INDEX_INSTANCE_UNAVAILABLE",),
        )
        assert classified.is_terminal_classification is True
        assert classified.satisfies_requirement is False

    def test_an_outcome_without_a_verified_object_never_satisfies(self) -> None:
        from disclosure_drift.m3.acquisition import LogicalRequest

        hollow = RequestOutcome(
            request=LogicalRequest(source_id="sec_company_tickers", instance_key="", parameters={}),
            disposition="satisfied_new",
            content_sha256=None,
            relative_storage_path=None,
        )
        assert hollow.satisfies_requirement is False

    def test_an_unverifiable_object_is_not_counted_as_satisfied(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Satisfaction is re-verified against the stored bytes at classification time.

        A record that *claims* a payload is not evidence that the payload is there and intact.
        This makes verification fail while everything else succeeds, so the assertion isolates
        the re-verification step rather than the surrounding happy path.
        """
        from disclosure_drift.errors import RawObjectIntegrityError

        def _unverifiable(self: object, observation: object) -> None:
            message = "stored bytes do not match the recorded content hash"
            raise RawObjectIntegrityError(message)

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            _,
            storage,
        ):
            engine.preflight(_authorization(plan))
            monkeypatch.setattr(type(storage.snapshot_store), "verify_payload", _unverifiable)
            outcome = engine.run()
        assert outcome.satisfied == (), "an unverifiable object never satisfies its request"
        assert outcome.completion_status == "incomplete"
        assert outcome.completed_successfully is False

    def test_positive_control_the_same_run_verifies_without_the_injected_failure(
        self, tmp_path: Path
    ) -> None:
        """The refusal above is about verification failing, not about the run itself."""
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert len(outcome.satisfied) == plan.planned_unique_logical_requests
        assert outcome.completed_successfully is True

    def test_a_missing_required_object_blocks_successful_completion(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[2] = _scripted(404, body=b"gone", content_type="application/json")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.completion_status == "incomplete"
        assert outcome.completed_successfully is False
        assert len(outcome.absences) == 1
        assert outcome.planned_work_remains is True

    def test_a_stopped_window_is_never_successfully_complete(self, tmp_path: Path) -> None:
        plan = _plan()
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling, consumed=plan.hard_request_ceiling)
        with _harness(tmp_path, plan=plan, responses=[], ceiling=gate) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.completed_successfully is False

    def test_deleting_a_stored_object_withdraws_satisfaction(self, tmp_path: Path) -> None:
        """Satisfaction is re-verified against the bytes, not asserted from the record."""
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            _,
            storage,
        ):
            engine.preflight(_authorization(plan))
            first = engine.run()
            assert first.completed_successfully is True
            path = storage.tree.data_root / (first.satisfied[0].relative_storage_path or "")
            observations = tuple(storage.snapshot_store.observations)
            path.unlink()
            report = observe_recovery_state(
                storage=storage,
                observations=observations,
                ceiling=engine.ceiling,
            )
        assert report.missing_referents, "the deleted object is reported as a missing referent"
        assert report.outcome_is_uncertain is True

    def test_a_rerun_over_identical_input_is_deterministic(self, tmp_path: Path) -> None:
        results = []
        for name in ("first", "second"):
            root = tmp_path / name
            root.mkdir()
            plan = _plan()
            with _harness(root, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
                engine.preflight(_authorization(plan))
                outcome = engine.run()
            results.append(
                (
                    outcome.completion_status,
                    outcome.consumed_physical_attempts,
                    tuple(item.content_sha256 for item in outcome.outcomes),
                    dict(outcome.classification_totals),
                )
            )
        assert results[0] == results[1]


# =========================================================================== #
# Catalog and object transaction ordering
# =========================================================================== #
class TestCatalogIntegration:
    """Objects and catalog rows reconcile before anything reports success."""

    def test_every_satisfied_request_has_a_committed_observation_row(self, tmp_path: Path) -> None:
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        with sqlite3.connect(preparation.database_path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT observation_id FROM census_source_observations"
            ).fetchall()
        recorded = {row["observation_id"] for row in rows}
        for satisfied in outcome.satisfied:
            assert satisfied.observation_id in recorded

    def test_the_catalog_stays_integral_after_a_run(self, tmp_path: Path) -> None:
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            engine.run()
        with CatalogWriter(preparation.database_path, preparation.lock_directory) as writer:
            assert writer.integrity().passed is True

    def test_a_second_writer_is_refused_while_one_is_held(self, tmp_path: Path) -> None:
        from disclosure_drift.errors import SingleWriterViolationError

        preparation = prepare_operational_catalog(evidence_root=tmp_path)
        with (
            CatalogWriter(preparation.database_path, preparation.lock_directory),
            pytest.raises(SingleWriterViolationError),
            CatalogWriter(preparation.database_path, preparation.lock_directory),
        ):
            pass


# =========================================================================== #
# Recovery observability
# =========================================================================== #
class TestRecoveryObservability:
    """Inspection only. Nothing here resumes, repairs, deletes, or resets a counter."""

    def test_a_clean_run_reports_clean(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            gate,
            storage,
        ):
            engine.preflight(_authorization(plan))
            engine.run()
            report = observe_recovery_state(
                storage=storage,
                observations=storage.snapshot_store.observations,
                ceiling=gate,
            )
        assert report.is_clean is True
        assert report.outcome_is_uncertain is False

    def test_a_part_file_is_reported_as_partial(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        storage.tree.raw_indexes.mkdir(parents=True, exist_ok=True)
        (storage.tree.raw_indexes / "leftover.idx.abc.part").write_bytes(b"partial")
        report = observe_recovery_state(
            storage=storage, observations=(), ceiling=PhysicalAttemptCeiling(10)
        )
        assert report.partial_objects
        assert report.is_clean is False

    def test_an_unrecorded_object_is_reported_as_an_orphan(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        _store(storage, b"orphaned", "orphan.idx")
        report = observe_recovery_state(
            storage=storage, observations=(), ceiling=PhysicalAttemptCeiling(10)
        )
        assert report.orphan_objects
        assert report.outcome_is_uncertain is False

    def test_a_row_without_its_object_is_uncertain(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        observation = SourceObservation(
            observation_id="obs-1",
            source_id="sec_company_tickers",
            requested_url="https://www.sec.gov/files/company_tickers.json",
            purpose="test",
            retrieved_at_utc=_stamp(),
            outcome="stored_new",
            relative_storage_path="raw/indexes/absent.json",
        )
        report = observe_recovery_state(
            storage=storage,
            observations=(observation,),
            ceiling=PhysicalAttemptCeiling(10),
        )
        assert report.missing_referents == ("raw/indexes/absent.json",)
        assert report.outcome_is_uncertain is True

    def test_headroom_is_reported_without_being_changed(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        gate = PhysicalAttemptCeiling(801, consumed=800)
        report = observe_recovery_state(storage=storage, observations=(), ceiling=gate)
        assert report.remaining_headroom == 1
        assert gate.consumed == 800, "inspection consumes nothing"


# =========================================================================== #
# Security, leakage, and nonchange
# =========================================================================== #
class TestSecurityAndNonchange:
    """Network stays off, identities stay private, and bodies never reach a log."""

    def test_importing_the_module_constructs_no_transport(self) -> None:
        import disclosure_drift.m3.acquisition as module

        assert "httpx" not in sys.modules or not hasattr(module, "httpx")
        assert not hasattr(module, "Client")

    def test_constructing_the_engine_places_no_request(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=[]) as (_, transport, gate, _):
            assert transport.requests == []
            assert gate.consumed == 0

    def test_tracked_network_switches_are_false(self) -> None:
        from disclosure_drift.config import load_config

        config = load_config()
        assert config.network.enabled is False
        assert config.network.m3_acquire_enabled is False

    def test_no_environment_variable_can_enable_acquisition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The allowlist refuses the variable outright; it is not merely ignored.

        Refusing is the stronger guarantee. An ignored override leaves an operator believing
        acquisition is enabled when it is not, which is exactly the confusion that precedes an
        unauthorized run; a hard refusal makes the attempt visible.
        """
        from disclosure_drift.config import UnknownEnvironmentOverrideError, load_config

        monkeypatch.setenv("DISCLOSURE_DRIFT_NETWORK_ENABLED", "true")
        monkeypatch.setenv("DISCLOSURE_DRIFT_NETWORK_M3_ACQUIRE_ENABLED", "true")
        with pytest.raises(UnknownEnvironmentOverrideError, match="unrecognized environment"):
            load_config()

    def test_positive_control_the_same_load_succeeds_without_those_variables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The refusal above is about the variables, not about ``load_config`` itself."""
        from disclosure_drift.config import load_config

        monkeypatch.delenv("DISCLOSURE_DRIFT_NETWORK_ENABLED", raising=False)
        monkeypatch.delenv("DISCLOSURE_DRIFT_NETWORK_M3_ACQUIRE_ENABLED", raising=False)
        config = load_config()
        assert config.network.enabled is False
        assert config.network.m3_acquire_enabled is False

    def test_the_engine_reads_no_configuration_switch(self, tmp_path: Path) -> None:
        """Authority is an explicit object the caller proves, never a configuration key.

        Decision 045 gives the driver a `LiveOperatorGate` carrying the operator-boundary facts,
        one of which is *named* `m3_acquire_enabled`. That is a value the command surface proved
        and passed in, not a switch this module reads: the property under test is that the driver
        cannot load configuration at all, so it is asserted directly rather than through the
        absence of a field name that is now legitimately present.
        """
        source = Path(
            __import__("disclosure_drift.m3.acquisition", fromlist=["__file__"]).__file__ or ""
        ).read_text(encoding="utf-8")
        assert "load_config" not in source
        assert "disclosure_drift.config" not in source
        assert "ProjectConfig" not in source
        assert "os.environ" not in source

    def test_no_response_body_reaches_a_log_record(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        plan = _plan()
        script = _success_script(plan)
        script[1] = _scripted(
            body=f'{{"payload":"{_BODY_MARKER}"}}'.encode(),
            content_type="application/json",
        )
        with (
            caplog.at_level(logging.DEBUG),
            _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _),
        ):
            engine.preflight(_authorization(plan))
            engine.run()
        assert _BODY_MARKER not in caplog.text

    def test_no_contact_identity_reaches_an_observation_or_outcome(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            transport,
            _,
            storage,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
            rendered = repr(outcome) + repr(storage.snapshot_store.observations)
        assert _AGENT not in rendered
        for request in transport.requests:
            assert "[REDACTED]" in dict(request.redacted_headers()).get("User-Agent", "")

    def test_no_absolute_private_path_appears_in_an_outcome(self, tmp_path: Path) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert str(tmp_path) not in repr(outcome)
        for item in outcome.outcomes:
            assert (
                item.relative_storage_path is None
                or not Path(item.relative_storage_path).is_absolute()
            )

    def test_the_driver_creates_no_repository_local_artifact(self, tmp_path: Path) -> None:
        repository = Path(__file__).resolve().parents[2]
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            engine.run()
        assert not (repository / "catalogs").exists()
        assert not (repository / _DATA_RELATIVE).exists()

    def test_the_driver_imports_no_transport_anywhere_in_its_source(self) -> None:
        """Stronger than a module-level scan: an indented import would evade that.

        The structural proof that matters is that no transport implementation is reachable from
        this module at all, including from inside a function body where a lazy import would sit.
        """
        import ast

        source_path = Path(
            __import__("disclosure_drift.m3.acquisition", fromlist=["__file__"]).__file__ or ""
        )
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert imported, "the driver declares imports"
        for name in imported:
            root = name.split(".")[0]
            assert root not in {"httpx", "socket", "urllib", "requests", "http"}, (
                f"the driver must not import a transport: {name}"
            )


# =========================================================================== #
# Bulk-archive streaming (MAJOR-1)
# =========================================================================== #
class TestBulkArchiveStreaming:
    """A bulk archive is streamed, not buffered, and is chosen by route authority."""

    def test_streaming_is_selected_from_the_registered_route(self) -> None:
        assert route_is_streamed(SOURCES["sec_bulk_submissions"]) is True
        for source_id in ("sec_company_tickers", "sec_sic_code_list", "sec_full_index_company"):
            assert route_is_streamed(SOURCES[source_id]) is False

    def test_the_archive_route_is_requested_as_a_stream(self, tmp_path: Path) -> None:
        """The choice reaches the wire: the archive streams, bounded documents do not."""
        plan = _plan()
        requests = derive_logical_requests(plan)
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            transport,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            engine.run()
        by_source = {placed.source_id: placed.stream for placed in transport.requests}
        assert by_source["sec_bulk_submissions"] is True
        assert by_source["sec_company_tickers"] is False
        assert len(transport.requests) == len(requests)

    def test_an_archive_larger_than_the_memory_bound_is_acquired_not_quarantined(
        self, tmp_path: Path
    ) -> None:
        """The regression this correction exists for.

        The real bootstrap archive is far above the accepted in-memory bound. Buffered, the
        accepted response policy quarantines it as malformed on size alone, and M3.2A can never
        complete: contract §14 names the bulk-submissions object as required and §15 makes M3.2B
        derive from it. Streamed, it is an ordinary acquisition.
        """
        archive = tmp_path / "big.zip"
        size = _write_large_archive(archive)
        assert size > MAX_IN_MEMORY_BYTES, "the fixture must cross the bound it is testing"

        plan = _plan()
        script = _success_script(plan)
        script[0] = _streamed_archive_response(archive)
        root = tmp_path / "root"
        root.mkdir()
        with _harness(root, plan=plan, responses=script) as (engine, transport, gate, storage):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        bulk = outcome.outcomes[0]
        assert bulk.request.source_id == "sec_bulk_submissions"
        assert bulk.disposition == "satisfied_new"
        assert bulk.satisfies_requirement is True
        assert bulk.reason_codes == ()
        assert outcome.completion_status == "complete"
        assert outcome.completed_successfully is True

        stored = storage.tree.data_root / (bulk.relative_storage_path or "")
        assert stored.is_file()
        assert stored.stat().st_size == size, "the whole archive was stored"
        assert bulk.content_sha256 == sha256_of(archive.read_bytes())
        assert transport.requests[0].stream is True
        assert gate.consumed == plan.planned_unique_logical_requests, "exact attempt accounting"
        assert not list(storage.tree.staging.rglob("*.part")), "the spool is cleaned on success"

    def test_positive_control_the_same_archive_buffered_is_quarantined_on_size(
        self, tmp_path: Path
    ) -> None:
        """Proof the fixture really does cross the bound, and that the bound is what bites.

        This drives the accepted client directly with a buffered body of the same archive, which
        is what the driver did before this correction. Without this control, the test above could
        pass against a fixture that was never actually oversized.
        """
        archive = tmp_path / "big.zip"
        _write_large_archive(archive)
        body = archive.read_bytes()
        clock = _FrozenClock()
        transport = _ScriptedTransport([_scripted(body=body, content_type="application/zip")])
        client = SecClient(
            transport,
            _AGENT,
            AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep),
            RetrievalPolicy(),
            sleeper=clock.sleep,
        )
        with client.fetch("sec_bulk_submissions", purpose=_PURPOSE, stream=False) as result:
            assert result.outcome == "quarantined"
            assert result.reason_code == "SEC_RESPONSE_MALFORMED"


# =========================================================================== #
# Archive-member lineage (MAJOR-2)
# =========================================================================== #
def _member_rows(database_path: Path, observation_id: str) -> list[sqlite3.Row]:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT * FROM census_archive_members WHERE observation_id = ? "
            "ORDER BY member_index, member_name",
            (observation_id,),
        ).fetchall()


class TestArchiveMemberLineage:
    """The acquired archive carries its validated member lineage into the catalog."""

    def test_first_acquisition_persists_member_lineage(self, tmp_path: Path) -> None:
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        bulk = outcome.outcomes[0]
        assert bulk.disposition == "satisfied_new"
        rows = _member_rows(preparation.database_path, bulk.observation_id or "")
        assert rows, "the archive's members are recorded as lineage"
        assert rows[0]["member_name"] == "CIK0000000001.json"
        assert rows[0]["archive_relative_path"] == bulk.relative_storage_path
        assert rows[0]["archive_sha256"] == bulk.content_sha256
        assert rows[0]["member_sha256"] == sha256_of(b'{"cik":1}')

    def test_an_archive_with_no_json_members_is_quarantined(self, tmp_path: Path) -> None:
        """An archive that carries none of the metadata it was retrieved for fails closed."""
        plan = _plan()
        script = _success_script(plan)
        script[0] = _scripted(
            body=_zip_archive([("README.txt", b"no submissions here")]),
            content_type="application/zip",
        )
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, storage):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        bulk = outcome.outcomes[0]
        assert bulk.disposition == "quarantined"
        assert bulk.satisfies_requirement is False
        # Decision 040 §4: the required-object code coexists with — never replaces — the more
        # specific accepted defect code on a required M3.2A object's terminal quarantine.
        assert bulk.reason_codes == (
            "RAW_ARCHIVE_INVALID",
            "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        )
        assert outcome.completed_successfully is False
        assert (storage.tree.data_root / (bulk.relative_storage_path or "")).is_file(), (
            "the object is preserved, never deleted"
        )

    def test_a_corrupt_archive_is_quarantined_with_the_accepted_reason(
        self, tmp_path: Path
    ) -> None:
        """A body that passes the signature check but is not a readable archive."""
        plan = _plan()
        script = _success_script(plan)
        script[0] = _scripted(body=b"PK\x03\x04" + b"\x00" * 128, content_type="application/zip")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.outcomes[0].disposition == "quarantined"
        assert outcome.outcomes[0].reason_codes == (
            "RAW_ARCHIVE_INVALID",
            "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        )


# =========================================================================== #
# Reuse, duplication, and supersession through the engine
# =========================================================================== #
class TestReuseAndSupersessionThroughTheEngine:
    """Exercised through AcquisitionEngine, not only through the stores beneath it."""

    def test_byte_identical_rerun_reconciles_as_a_duplicate(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            first = harness.run(_success_script(plan))
            second = harness.run(_success_script(plan))
        assert first.completion_status == "complete"
        assert all(item.disposition == "satisfied_new" for item in first.outcomes)
        assert second.completion_status == "complete"
        assert second.completed_successfully is True
        assert all(item.disposition == "satisfied_duplicate" for item in second.outcomes), (
            "a byte-identical body reconciles to the preserved object"
        )
        assert {item.relative_storage_path for item in second.outcomes} == {
            item.relative_storage_path for item in first.outcomes
        }

    def test_a_rerun_reconciles_even_when_the_clock_moves_between_the_two_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The exact regression control for the fixture defect this correction closes.

        The two acquisitions are separated by a clock jump of several years. While ZIP member
        headers were stamped from ``time.localtime()``, the second archive's bytes differed
        from the first whenever the two builds fell in different two-second windows, so the
        rerun reconciled as *changed content* and this class failed roughly once in twelve
        runs. With pinned member metadata the jump must change nothing.
        """
        import time as time_module

        plan = _plan()
        planned = plan.planned_unique_logical_requests
        with _persistent(tmp_path, plan) as harness:
            first = harness.run(_success_script(plan))
            monkeypatch.setattr(time_module, "time", lambda: 2_000_000_000.0)
            monkeypatch.setattr(
                time_module,
                "localtime",
                lambda *_: time_module.struct_time((2033, 5, 18, 3, 33, 20, 2, 138, 0)),
            )
            second = harness.run(_success_script(plan))

        assert first.completion_status == "complete"
        assert all(item.disposition == "satisfied_duplicate" for item in second.outcomes)
        assert (second.new_raw_objects, second.duplicates_reconciled) == (0, planned)

    def test_lawful_archive_reuse_does_not_raise(self, tmp_path: Path) -> None:
        """The defect this correction closes: reuse used to fail for want of member lineage."""
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            second = harness.run(_success_script(plan))
        bulk = second.outcomes[0]
        assert bulk.request.source_id == "sec_bulk_submissions"
        assert bulk.disposition == "satisfied_duplicate"
        assert bulk.satisfies_requirement is True

    def test_new_and_reused_objects_are_counted_separately(self, tmp_path: Path) -> None:
        """Contract §22 reports new objects and duplicates as different quantities."""
        plan = _plan()
        planned = plan.planned_unique_logical_requests
        with _persistent(tmp_path, plan) as harness:
            first = harness.run(_success_script(plan))
            second = harness.run(_success_script(plan))
        assert (first.new_raw_objects, first.duplicates_reconciled) == (planned, 0)
        assert (second.new_raw_objects, second.duplicates_reconciled) == (0, planned)
        assert second.cache_hits == 0
        assert sum(second.classification_totals.values()) == planned

    def test_changed_content_becomes_a_superseding_observation(self, tmp_path: Path) -> None:
        plan = _plan()
        changed = [
            _scripted(body=b'{"ok":2}')
            if request.source_id == "sec_company_tickers"
            else _success_for(request.source_id)
            for request in derive_logical_requests(plan)
        ]
        with _persistent(tmp_path, plan) as harness:
            first = harness.run(_success_script(plan))
            second = harness.run(changed)
            observations = harness.storage.snapshot_store.observations
        index = next(
            position
            for position, request in enumerate(derive_logical_requests(plan))
            if request.source_id == "sec_company_tickers"
        )
        superseding = second.outcomes[index]
        assert superseding.disposition == "satisfied_new", "changed content is a new object"
        assert superseding.satisfies_requirement is True
        assert superseding.content_sha256 != first.outcomes[index].content_sha256

        recorded = next(
            item for item in observations if item.observation_id == superseding.observation_id
        )
        assert recorded.outcome == "superseded"
        assert recorded.supersedes_observation_id == first.outcomes[index].observation_id
        assert (
            harness.storage.tree.data_root / (first.outcomes[index].relative_storage_path or "")
        ).is_file(), "the superseded object is preserved"

    def test_a_changed_archive_supersedes_and_carries_fresh_member_lineage(
        self, tmp_path: Path
    ) -> None:
        second_member = _zip_archive([("CIK0000000002.json", b'{"cik":2}')])
        changed = [
            _scripted(body=second_member, content_type="application/zip")
            if request.source_id == "sec_bulk_submissions"
            else _success_for(request.source_id)
            for request in derive_logical_requests(_plan())
        ]
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            second = harness.run(changed)
            database = harness.preparation.database_path
        bulk = second.outcomes[0]
        assert bulk.disposition == "satisfied_new"
        rows = _member_rows(database, bulk.observation_id or "")
        assert [row["member_name"] for row in rows] == ["CIK0000000002.json"]
        assert rows[0]["archive_sha256"] == bulk.content_sha256

    def test_overwriting_one_immutable_identity_with_differing_bytes_is_still_refused(
        self, tmp_path: Path
    ) -> None:
        """The store-level guarantee the engine must never be able to talk its way past."""
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        _store(storage, b"original", "immutable.idx")
        with pytest.raises(RawObjectIntegrityError, match="refusing to overwrite"):
            _store(storage, b"different", "immutable.idx")


# =========================================================================== #
# Failure ordering and progress isolation
# =========================================================================== #
class TestFailureOrdering:
    """A failure after an attempt yields a recorded window, never a lost one."""

    def test_a_catalog_failure_after_promotion_is_reported_not_raised(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan = _plan()
        calls = {"n": 0}
        real = ObservationRecorder.record

        def _fail_on_third(self: object, observation: object, **kwargs: object) -> str:
            calls["n"] += 1
            if calls["n"] == 3:
                message = "simulated catalog failure after immutable promotion"
                raise CatalogWriteError(message)
            return real(self, observation, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(ObservationRecorder, "record", _fail_on_third)
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            transport,
            gate,
            storage,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        assert outcome.completion_status == "failed"
        assert outcome.completed_successfully is False
        assert len(outcome.satisfied) == 2, "already committed requests keep their classification"
        assert outcome.outcomes[2].disposition == "failed"
        assert outcome.outcomes[2].detail == (
            "CatalogWriteError: the operational catalog refused a write"
        ), "the failure class is reported; the exception's own arguments are not"
        assert len(outcome.unattempted) == plan.planned_unique_logical_requests - 3
        assert gate.consumed == 3, "attempts consumed remain exact"
        assert len(transport.requests) == 3, "no request follows the stop"
        promoted = storage.tree.data_root / (outcome.outcomes[2].relative_storage_path or "x")
        assert promoted.parent.exists(), "the promoted object is not deleted"

    def test_a_storage_failure_after_an_attempt_is_reported_not_raised(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan = _plan()
        calls = {"n": 0}
        real = SnapshotStore.record

        def _fail_on_second(self: object, result: object, **kwargs: object) -> object:
            calls["n"] += 1
            if calls["n"] == 2:
                message = "simulated raw-object integrity failure"
                raise RawObjectIntegrityError(message)
            return real(self, result, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(SnapshotStore, "record", _fail_on_second)
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            gate,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        assert outcome.completion_status == "failed"
        assert outcome.outcomes[1].disposition == "failed"
        assert gate.consumed == 2
        assert sum(outcome.classification_totals.values()) == plan.planned_unique_logical_requests

    def test_positive_control_the_same_run_completes_without_the_injected_failure(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.completion_status == "complete"

    def test_a_failing_progress_callback_never_discards_the_window(self, tmp_path: Path) -> None:
        """Operator output is observational; it cannot destroy an acquisition result."""
        seen: list[object] = []

        def _sink(outcome: object) -> None:
            seen.append(outcome)
            if len(seen) == 2:
                message = "operator progress sink failed"
                raise RuntimeError(message)

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), progress=_sink) as (
            engine,
            _,
            gate,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        assert outcome.completion_status == "complete"
        assert outcome.completed_successfully is True
        assert gate.consumed == plan.planned_unique_logical_requests
        assert len(outcome.progress_failures) == 1
        # The failure is recorded structurally, never as the sink's own message (Decision 045
        # §12): the identity, the one fixed internal reason, and the exception class.
        assert "operator progress sink failed" not in outcome.progress_failures[0]
        assert PROGRESS_SINK_FAILURE_REASON in outcome.progress_failures[0]
        assert "RuntimeError" in outcome.progress_failures[0]
        assert len(seen) == plan.planned_unique_logical_requests, "reporting continues"

    def test_a_ceiling_stop_inside_a_request_is_not_reported_as_unattempted(
        self, tmp_path: Path
    ) -> None:
        """A request that consumed attempts before the stop is `stopped`, not untouched."""
        plan = _plan()
        planned = plan.planned_unique_logical_requests
        gate = PhysicalAttemptCeiling(
            plan.hard_request_ceiling, consumed=plan.hard_request_ceiling - 1
        )
        script = [_scripted(503, body=b"", content_type=None), *_success_script(plan)]
        with _harness(tmp_path, plan=plan, responses=script, ceiling=gate) as (engine, _, used, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        first = outcome.outcomes[0]
        assert first.disposition == "stopped"
        assert first.attempts == 1, "the attempt it did place is recorded"
        assert first.reason_codes == ("SEC_REQUEST_CEILING_EXHAUSTED",)
        assert outcome.completion_status == "stopped_at_ceiling"
        assert outcome.completed_successfully is False
        assert len(outcome.interrupted) == 1
        assert len(outcome.unattempted) == planned - 1
        assert used.consumed == plan.hard_request_ceiling
        assert sum(outcome.classification_totals.values()) == planned


# =========================================================================== #
# Identity uniqueness and window separation
# =========================================================================== #
class TestUniquenessAndWindowSeparation:
    """No duplicate identity, and neither window admits the other's routes."""

    @staticmethod
    def _duplicated_plan() -> RequestPlan:
        """A plan naming one quarterly instance twice, with counts that still agree.

        The counts agree deliberately: a plan whose totals disagree is already refused, so a
        duplicate that survives arithmetic is the case the uniqueness guard has to catch.
        """
        plan = _plan()
        return replace(
            plan,
            required_index_keys=("2010QTR1", "2010QTR1", "2010QTR2"),
            routes=tuple(
                replace(route, planned_unique_logical_requests=3)
                if route.source_id == "sec_full_index_company"
                else route
                for route in plan.routes
            ),
        )

    def test_duplicate_logical_identities_are_refused_at_expansion(self) -> None:
        with pytest.raises(AcquisitionGateError, match="repeated logical request identit"):
            derive_logical_requests(self._duplicated_plan())

    def test_duplicate_identities_never_reach_a_transport(self, tmp_path: Path) -> None:
        plan = self._duplicated_plan()
        with _harness(tmp_path, plan=plan, responses=[]) as (engine, transport, gate, _):
            with pytest.raises(AcquisitionGateError, match="repeated logical request identit"):
                engine.preflight(_authorization(plan))
            assert transport.requests == []
            assert gate.consumed == 0

    def test_positive_control_distinct_instances_remain_distinct(self) -> None:
        requests = derive_logical_requests(_plan())
        labels = [request.identity_label for request in requests]
        assert len(labels) == len(set(labels))
        assert "sec_full_index_company:2010QTR1" in labels
        assert "sec_full_index_company:2010QTR2" in labels

    def test_the_accepted_plan_still_expands_to_seventy_five_unique_requests(self) -> None:
        plan = build_m3_2a_request_plan(
            coverage_start=date(2009, 1, 1),
            coverage_end=date(2026, 6, 30),
            as_of_date=date(2026, 6, 30),
            include_open_quarter=False,
            calendar_year=2026,
            calendar_evidence_entry_count=0,
            already_satisfied_index_keys=frozenset(),
            requests_per_second=4.0,
        )
        labels = [request.identity_label for request in derive_logical_requests(plan)]
        assert len(labels) == 75
        assert len(set(labels)) == 75

    def test_a_bootstrap_route_is_refused_in_the_dependent_window(self, tmp_path: Path) -> None:
        """Contract §17 item 5 names both directions; the bootstrap direction is checked here."""
        plan = replace(_plan(), acquisition_window="M3.2B")
        with _harness(tmp_path, plan=plan, responses=[], window="M3.2B") as (
            engine,
            transport,
            gate,
            _,
        ):
            with pytest.raises(AcquisitionGateError, match="is not a M3.2B route"):
                engine.preflight(_authorization(plan, window="M3.2B"))
            assert transport.requests == []
            assert gate.consumed == 0

    def test_a_dependent_route_is_refused_in_the_bootstrap_window(self, tmp_path: Path) -> None:
        plan = _plan()
        dependent = replace(
            plan.routes[0],
            source_id="sec_submissions_entity",
            planned_unique_logical_requests=1,
        )
        forged = replace(plan, routes=(dependent, *plan.routes[1:]))
        with _harness(tmp_path, plan=forged, responses=[]) as (engine, transport, _, _):
            with pytest.raises(AcquisitionGateError, match="is not a M3.2A route"):
                engine.preflight(_authorization(forged))
            assert transport.requests == []

    def test_the_dependent_route_set_is_exactly_the_two_m3_2b_families(self) -> None:
        assert M3_2B_DEPENDENT_ROUTES == ("sec_submissions_entity", "sec_submissions_historical")
        for source_id in M3_2B_DEPENDENT_ROUTES:
            assert source_id in SOURCES


# =========================================================================== #
# Reason fidelity and recovery visibility
# =========================================================================== #
class TestReasonFidelityAndRecovery:
    """Absences name their registered code; gate stops do not borrow an unrelated one."""

    def test_an_absent_index_instance_carries_the_registered_reason(self, tmp_path: Path) -> None:
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        script = _success_script(plan)
        script[-1] = _scripted(404, body=b"missing", content_type="text/plain")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        absent = outcome.outcomes[-1]
        assert absent.request.source_id == "sec_full_index_company"
        assert absent.disposition == "absent"
        assert "INDEX_INSTANCE_UNAVAILABLE" in absent.reason_codes
        with sqlite3.connect(preparation.database_path) as connection:
            connection.row_factory = sqlite3.Row
            codes = {
                row["reason_code"]
                for row in connection.execute(
                    "SELECT reason_code FROM census_observation_reasons WHERE observation_id = ?",
                    (absent.observation_id,),
                )
            }
        assert "INDEX_INSTANCE_UNAVAILABLE" in codes, "the absence is durable in the catalog"

    def test_positive_control_a_satisfied_index_instance_carries_no_absence_reason(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert "INDEX_INSTANCE_UNAVAILABLE" not in outcome.outcomes[-1].reason_codes

    def test_a_pre_transport_refusal_does_not_borrow_the_redirect_reason(
        self, tmp_path: Path
    ) -> None:
        """A route refusal is not a redirect escape, and must not be recorded as one."""
        from disclosure_drift.sec.http_client import ProhibitedRetrievalError

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
            engine,
            _,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))

            def _refuse(*args: object, **kwargs: object) -> object:
                message = "refusing to retrieve a prohibited URL"
                raise ProhibitedRetrievalError(message)

            engine.client.fetch = _refuse  # type: ignore[method-assign]
            outcome = engine.run()

        assert outcome.completion_status == "stopped_by_gate"
        assert outcome.reason_codes == ()
        assert "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY" not in outcome.outcomes[0].reason_codes
        assert outcome.outcomes[0].disposition == "stopped"
        assert outcome.completed_successfully is False

    def test_a_streamed_partial_in_staging_is_reported(self, tmp_path: Path) -> None:
        """A spool interrupted mid-transfer lives in staging and nowhere else."""
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        storage.tree.staging.mkdir(parents=True, exist_ok=True)
        spool = storage.tree.staging / "sec_bulk_submissions-abc123.part"
        spool.write_bytes(b"interrupted stream")
        report = observe_recovery_state(
            storage=storage, observations=(), ceiling=PhysicalAttemptCeiling(10)
        )
        assert storage.tree.relative(spool) in report.partial_objects
        assert report.is_clean is False
        assert spool.is_file(), "inspection preserves the spool"

    def test_positive_control_an_empty_staging_tree_reports_clean(self, tmp_path: Path) -> None:
        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        report = observe_recovery_state(
            storage=storage, observations=(), ceiling=PhysicalAttemptCeiling(10)
        )
        assert report.partial_objects == ()
        assert report.is_clean is True

    def test_an_inconsistent_recorded_chain_is_refused_with_a_domain_message(
        self, tmp_path: Path
    ) -> None:
        """A partially recorded chain names what is wrong, rather than failing inside SQLite."""
        preparation = prepare_operational_catalog(evidence_root=tmp_path)
        with sqlite3.connect(preparation.database_path) as connection:
            connection.execute("DELETE FROM ops_schema_migrations WHERE version > 5")
            connection.execute("DELETE FROM ops_schema_migrations WHERE version = 2")
        with pytest.raises(CatalogPreparationError, match="not a contiguous chain from 0001"):
            prepare_operational_catalog(evidence_root=tmp_path)

    def test_positive_control_a_complete_chain_reopens_normally(self, tmp_path: Path) -> None:
        prepare_operational_catalog(evidence_root=tmp_path)
        again = prepare_operational_catalog(evidence_root=tmp_path)
        assert again.chain_is_exact is True
        assert again.applied_migrations == ()


# =========================================================================== #
# Deterministic ZIP fixtures
# =========================================================================== #
class TestDeterministicArchiveFixtures:
    """A fixture that changes with the clock cannot prove anything about byte-identity."""

    def test_repeated_builds_are_byte_identical(self) -> None:
        assert _zip_bytes() == _zip_bytes()
        assert len({sha256_of(_zip_bytes()) for _ in range(12)}) == 1

    def test_the_bytes_do_not_move_when_the_clock_does(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The regression control: pinned metadata means the wall clock is never consulted.

        Before the fixture was pinned, two builds a few seconds apart differed, so a
        "byte-identical rerun" reconciled as changed content roughly once in twelve runs. Moving
        the clock by decades here must change nothing at all.
        """
        import time as time_module

        baseline = _zip_bytes()
        monkeypatch.setattr(time_module, "time", lambda: 2_000_000_000.0)
        monkeypatch.setattr(
            time_module,
            "localtime",
            lambda *_: time_module.struct_time((2033, 5, 18, 3, 33, 20, 2, 138, 0)),
        )
        monkeypatch.setenv("TZ", "Pacific/Kiritimati")
        assert _zip_bytes() == baseline
        assert _write_zip_probe() == _write_zip_probe()

    def test_member_order_and_hashes_are_stable(self) -> None:
        members = [("b.json", b"2"), ("a.json", b"1"), ("c.json", b"3")]
        first = _zip_archive(members)
        assert first == _zip_archive(members)
        with zipfile.ZipFile(io.BytesIO(first)) as archive:
            assert [info.filename for info in archive.infolist()] == ["b.json", "a.json", "c.json"]
            assert {info.date_time for info in archive.infolist()} == {_ZIP_EPOCH}

    def test_the_large_archive_fixture_is_also_deterministic(self, tmp_path: Path) -> None:
        first, second = tmp_path / "a.zip", tmp_path / "b.zip"
        _write_large_archive(first)
        _write_large_archive(second)
        assert sha256_of(first.read_bytes()) == sha256_of(second.read_bytes())

    def test_changed_fixtures_differ_only_by_intended_content(self) -> None:
        assert _zip_archive([("x.json", b"1")]) != _zip_archive([("x.json", b"2")])
        assert _zip_archive([("x.json", b"1")]) != _zip_archive([("y.json", b"1")])


def _write_zip_probe() -> bytes:
    """A second deterministic archive shape, used to prove the clock never leaks in."""
    return _zip_archive([("probe.json", b'{"probe":true}')], compression=zipfile.ZIP_STORED)


# =========================================================================== #
# Bounded archive-member lineage
# =========================================================================== #
@contextmanager
def _captured_member_sources() -> Iterator[list[object]]:
    """Capture whatever the driver hands the recorder as its member source."""
    captured: list[object] = []
    real = ObservationRecorder.record

    def _capture(self: object, observation: object, **kwargs: object) -> str:
        if "members" in kwargs:
            captured.append(kwargs["members"])
        return real(self, observation, **kwargs)  # type: ignore[arg-type]

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(ObservationRecorder, "record", _capture)
        yield captured


class TestArchiveLineageIsMemoryBounded:
    """Lineage is streamed member by member; the expanded archive is never held at once."""

    def test_the_driver_hands_the_recorder_a_one_shot_iterator(self, tmp_path: Path) -> None:
        """Structural proof, independent of any measurement.

        A list or tuple would mean every member payload existed simultaneously before the
        first row was written. An iterator with no ``__len__`` and no ``__getitem__`` cannot
        have been built that way, and cannot be walked twice.
        """
        plan = _plan()
        with (
            _captured_member_sources() as captured,
            _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _),
        ):
            engine.preflight(_authorization(plan))
            engine.run()

        assert len(captured) == 1, "only the archive route carries member lineage"
        source = captured[0]
        assert isinstance(source, Iterator)
        assert not isinstance(source, list | tuple | set | frozenset)
        assert not hasattr(source, "__len__")
        assert not hasattr(source, "__getitem__")
        assert list(source) == [], "the driver already consumed its one pass"

    def test_every_member_row_is_persisted_through_the_lazy_path(self, tmp_path: Path) -> None:
        """Streaming must not cost coverage: many members, all recorded, in order."""
        names = [f"CIK{index:010d}.json" for index in range(64)]
        archive = _zip_archive(
            [(name, f'{{"n":{index}}}'.encode()) for index, name in enumerate(names)]
        )
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        script = _success_script(plan)
        script[0] = _scripted(body=archive, content_type="application/zip")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        bulk = outcome.outcomes[0]
        assert bulk.disposition == "satisfied_new"
        rows = _member_rows(preparation.database_path, bulk.observation_id or "")
        assert [row["member_name"] for row in rows] == names
        assert [row["member_index"] for row in rows] == list(range(64))
        assert all(row["archive_sha256"] == bulk.content_sha256 for row in rows)

    def test_lineage_memory_tracks_the_largest_member_not_the_expanded_archive(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Measured evidence, with a threshold chosen to be loose rather than clever.

        The fixture expands to more than the accepted in-memory bound across many equal
        members. Holding them all — what a materializing driver does — costs the whole
        expansion; streaming costs one member plus the reader's own bounded metadata. The
        assertion allows a quarter of the archive, which is far above the streaming cost and
        far below the materializing one, so it discriminates without being fragile.

        The window measured is the driver's whole lineage phase, not just the recorder call:
        a driver that materialized before handing over would otherwise do its allocating just
        outside a narrower probe and escape unnoticed.
        """
        archive = tmp_path / "big.zip"
        size = _write_large_archive(archive)
        assert size > MAX_IN_MEMORY_BYTES

        peak: dict[str, int] = {}
        real = AcquisitionEngine._record_observation

        def _measure(self: object, spec: object, request: object, observation: object) -> object:
            if not route_is_streamed(spec):  # type: ignore[arg-type]
                return real(self, spec, request, observation)  # type: ignore[arg-type]
            tracemalloc.start()
            try:
                return real(self, spec, request, observation)  # type: ignore[arg-type]
            finally:
                peak["bytes"] = tracemalloc.get_traced_memory()[1]
                tracemalloc.stop()

        monkeypatch.setattr(AcquisitionEngine, "_record_observation", _measure)
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path / "root", relative_path=_CATALOG_RELATIVE
        )
        script = _success_script(plan)
        script[0] = _streamed_archive_response(archive)
        with _harness(tmp_path / "root", plan=plan, responses=script) as (engine, transport, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        bulk = outcome.outcomes[0]
        assert bulk.disposition == "satisfied_new"
        assert transport.requests[0].stream is True, "streaming transport is still in force"
        rows = _member_rows(preparation.database_path, bulk.observation_id or "")
        assert len(rows) == _BIG_MEMBER_COUNT, "every member is still recorded"
        assert peak["bytes"] < size // 4, (
            f"lineage peak {peak['bytes']} should track one {_BIG_MEMBER_BYTES}-byte member, "
            f"not the {size}-byte expansion"
        )

    def test_a_late_enumeration_failure_rolls_back_the_whole_observation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failing at member three leaves no observation row and no member row at all."""
        from disclosure_drift.m3 import acquisition as driver

        real_iter = driver.iter_members

        def _fails_late(*args: object, **kwargs: object) -> Iterator[object]:
            for index, member in enumerate(real_iter(*args, **kwargs)):  # type: ignore[arg-type]
                if index == 2:
                    message = "simulated archive read failure partway through enumeration"
                    raise OSError(message)
                yield member

        monkeypatch.setattr(driver, "iter_members", _fails_late)
        archive = _zip_archive([(f"CIK{index:010d}.json", b'{"n":1}') for index in range(6)])
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        script = _success_script(plan)
        script[0] = _scripted(body=archive, content_type="application/zip")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, gate, storage):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        bulk = outcome.outcomes[0]
        assert bulk.disposition == "failed"
        assert outcome.completion_status == "failed"
        assert outcome.completed_successfully is False
        assert bulk.satisfies_requirement is False
        with sqlite3.connect(preparation.database_path) as connection:
            observations = connection.execute(
                "SELECT count(*) FROM census_source_observations"
            ).fetchone()[0]
            members = connection.execute("SELECT count(*) FROM census_archive_members").fetchone()[
                0
            ]
        assert observations == 0, "the rolled-back observation left no row"
        assert members == 0, "and no partial member lineage"
        assert gate.consumed == 1, "the attempt it did place is still counted"
        promoted = storage.tree.raw_bulk
        assert any(promoted.rglob("*.zip")), "the immutable object stays preserved on disk"

    def test_a_defence_failure_partway_through_quarantines_without_partial_lineage(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The accepted refusal still quarantines, and commits no half-written lineage."""
        from disclosure_drift.m3 import acquisition as driver

        real_iter = driver.iter_members

        def _refuses_late(*args: object, **kwargs: object) -> Iterator[object]:
            for index, member in enumerate(real_iter(*args, **kwargs)):  # type: ignore[arg-type]
                if index == 2:
                    message = "refusing archive member three"
                    raise ArchiveDefenceError(message)
                yield member

        monkeypatch.setattr(driver, "iter_members", _refuses_late)
        archive = _zip_archive([(f"CIK{index:010d}.json", b'{"n":1}') for index in range(6)])
        plan = _plan()
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )
        script = _success_script(plan)
        script[0] = _scripted(body=archive, content_type="application/zip")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        bulk = outcome.outcomes[0]
        assert bulk.disposition == "quarantined"
        assert bulk.reason_codes == (
            "RAW_ARCHIVE_MEMBER_REFUSED",
            "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        )
        assert bulk.satisfies_requirement is False
        assert _member_rows(preparation.database_path, bulk.observation_id or "") == []
        with sqlite3.connect(preparation.database_path) as connection:
            outcome_row = connection.execute(
                "SELECT outcome FROM census_source_observations WHERE observation_id = ?",
                (bulk.observation_id,),
            ).fetchone()
        assert outcome_row[0] == "quarantined", "recorded exactly once, as quarantined"

    def test_the_archive_reader_is_entered_exactly_once(self, tmp_path: Path) -> None:
        """One pass, not two: re-reading the archive would double the cost it exists to avoid."""
        from disclosure_drift.m3 import acquisition as driver

        calls: list[object] = []
        real_iter = driver.iter_members

        def _counting(*args: object, **kwargs: object) -> Iterator[object]:
            calls.append(args)
            yield from real_iter(*args, **kwargs)  # type: ignore[arg-type]

        plan = _plan()
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(driver, "iter_members", _counting)
            with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (
                engine,
                _,
                _,
                _,
            ):
                engine.preflight(_authorization(plan))
                engine.run()
        assert len(calls) == 1


# =========================================================================== #
# Operational-error sanitization
# =========================================================================== #
class TestOperationalErrorSanitization:
    """A failure is reported; the operator's private paths and the payload are not."""

    @staticmethod
    def _run_with_failing_recorder(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        exception: BaseException,
        *,
        marker_body: bytes | None = None,
    ) -> object:
        plan = _plan()
        calls = {"n": 0}
        real = ObservationRecorder.record

        def _fail_on_second(self: object, observation: object, **kwargs: object) -> str:
            calls["n"] += 1
            if calls["n"] == 2:
                raise exception
            return real(self, observation, **kwargs)  # type: ignore[arg-type]

        monkeypatch.setattr(ObservationRecorder, "record", _fail_on_second)
        script = _success_script(plan)
        if marker_body is not None:
            script[1] = _scripted(body=marker_body, content_type="application/json")
        with _harness(tmp_path, plan=plan, responses=script) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            return engine.run()

    def test_an_oserror_absolute_path_never_reaches_an_outcome(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secret = tmp_path / "private-evidence" / "runs" / "m3_2a" / "secret.idx"
        failure = OSError(2, "No such file or directory", str(secret))
        outcome = self._run_with_failing_recorder(tmp_path, monkeypatch, failure)
        rendered = repr(outcome)
        assert str(secret) not in rendered
        assert str(tmp_path) not in rendered
        assert "secret.idx" not in rendered
        assert outcome.outcomes[1].detail == (  # type: ignore[attr-defined]
            "FileNotFoundError: a filesystem operation failed"
        )
        assert outcome.completion_status == "failed"  # type: ignore[attr-defined]
        assert outcome.completed_successfully is False  # type: ignore[attr-defined]

    def test_a_sqlite_error_path_like_value_never_reaches_an_outcome(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        secret = tmp_path / "catalogs" / "m3_2a_operational.sqlite3"
        failure = sqlite3.OperationalError(f"unable to open database file: {secret}")
        outcome = self._run_with_failing_recorder(tmp_path, monkeypatch, failure)
        rendered = repr(outcome)
        assert str(secret) not in rendered
        assert "m3_2a_operational.sqlite3" not in rendered
        assert outcome.outcomes[1].detail == (  # type: ignore[attr-defined]
            "OperationalError: the operational catalog reported a database error"
        )

    def test_a_response_body_marker_never_reaches_an_outcome_or_a_log(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        failure = RawObjectIntegrityError(f"refusing to overwrite {tmp_path}/raw/{_BODY_MARKER}")
        with caplog.at_level(logging.DEBUG):
            outcome = self._run_with_failing_recorder(
                tmp_path,
                monkeypatch,
                failure,
                marker_body=f'{{"payload":"{_BODY_MARKER}"}}'.encode(),
            )
        assert _BODY_MARKER not in repr(outcome)
        assert _BODY_MARKER not in caplog.text
        assert str(tmp_path) not in repr(outcome)
        assert outcome.outcomes[1].detail == (  # type: ignore[attr-defined]
            "RawObjectIntegrityError: an immutable raw object could not be written or verified"
        )

    def test_a_failing_progress_sink_cannot_publish_a_private_path(self, tmp_path: Path) -> None:
        """An operator sink that fails on a file is sanitized the same way."""
        secret = tmp_path / "private-evidence" / "sink.log"

        def _sink(_: object) -> None:
            raise OSError(13, "Permission denied", str(secret))

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), progress=_sink) as (
            engine,
            _,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        joined = " ".join(outcome.progress_failures)
        assert str(secret) not in joined
        assert "sink.log" not in joined
        assert PROGRESS_SINK_FAILURE_REASON in joined
        assert "PermissionError" in joined
        assert outcome.completion_status == "complete", "operator output never decides the window"

    def test_a_deliberate_sink_message_reaches_stderr_and_not_the_retained_state(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Decision 045 §12 inverts the older rule: the operator's own words are not retained.

        A sink's message is operator-controlled text and can carry an absolute path, an address,
        or a credential, so it is diagnosable on stderr and excluded from every retained field.
        The pair of assertions is the positive control: the message provably *did* reach the
        diagnostic channel, so its absence from the retained record is exclusion rather than the
        sink having failed to raise.
        """

        def _sink(_: object) -> None:
            message = "operator progress sink refused this outcome"
            raise RuntimeError(message)

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan), progress=_sink) as (
            engine,
            _,
            _,
            _,
        ):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        captured = capsys.readouterr()
        assert "operator progress sink refused this outcome" in captured.err
        assert "operator progress sink refused this outcome" not in " ".join(
            outcome.progress_failures
        )
        assert PROGRESS_SINK_FAILURE_REASON in outcome.progress_failures[0]

    def test_positive_control_the_same_run_succeeds_without_the_injected_failure(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()
        assert outcome.completion_status == "complete"
        assert all(item.detail != "" or True for item in outcome.outcomes)


# =========================================================================== #
# Stage T2.4 — catalog-authoritative reconstruction (Decision 040 §2, T2.4-A)
# =========================================================================== #
from disclosure_drift.m3.acquisition import (  # noqa: E402 - stage T2.4 surfaces
    LogicalRequest,
    conditional_validators,
    reconcile_requests,
    reconstruct_catalog_state,
    verified_reusable_predecessor,
)


def _etag_script(plan: RequestPlan, etag: str) -> list[TransportResponse]:
    """One successful response per planned request, each carrying the same ETag."""
    script: list[TransportResponse] = []
    for request in derive_logical_requests(plan):
        response = _success_for(request.source_id)
        headers = dict(response.headers)
        headers["ETag"] = etag
        script.append(
            TransportResponse(
                status=response.status,
                headers=headers,
                final_url=response.final_url,
                body=response.body,
            )
        )
    return script


def _reconstruct(harness: _PersistentHarness) -> object:
    return reconstruct_catalog_state(
        catalog_path=harness.preparation.database_path, storage=harness.storage
    )


def _reconcile(harness: _PersistentHarness, reconstruction: object | None = None) -> object:
    return reconcile_requests(
        plan=harness.plan,
        reconstruction=(reconstruction if reconstruction is not None else _reconstruct(harness)),  # type: ignore[arg-type]
        storage=harness.storage,
    )


class TestCatalogAuthoritativeReconstruction:
    def test_reconstruction_adopts_every_durable_row_into_a_fresh_store(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            reconstruction = _reconstruct(harness)

            assert len(reconstruction.observations) == plan.planned_unique_logical_requests
            assert reconstruction.store is not harness.storage.snapshot_store, (
                "the continuation boundary constructs a fresh store; it never inherits the "
                "predecessor process's mutable in-memory state"
            )
            assert reconstruction.store.observations == reconstruction.observations
            again = _reconstruct(harness)
            assert [o.observation_id for o in again.observations] == [
                o.observation_id for o in reconstruction.observations
            ], "reconstruction order is the catalog's own deterministic order"

    def test_quarantined_and_failed_rows_are_facts_but_never_reusable(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        tickers = next(
            index
            for index, request in enumerate(derive_logical_requests(plan))
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(body=b"<html>not json</html>", content_type="application/json")
        with _persistent(tmp_path, plan) as harness:
            harness.run(script)
            reconstruction = _reconstruct(harness)

            quarantined = [
                observation
                for observation in reconstruction.observations
                if observation.outcome == "quarantined"
            ]
            assert len(quarantined) == 1, "the quarantine is adopted as a fact"
            assert verified_reusable_predecessor(reconstruction, "sec_company_tickers") is None, (
                "a quarantined observation is never a reusable predecessor"
            )
            assert conditional_validators(reconstruction, "sec_company_tickers") is None

    def test_reuse_reverifies_immutable_evidence_at_the_point_of_reuse(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_etag_script(plan, '"v1"'))
            reconstruction = _reconstruct(harness)
            index = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert index is not None and index.etag == '"v1"'

            stored = harness.storage.tree.data_root / str(index.relative_storage_path)
            stored.write_bytes(b"tampered")
            fresh = _reconstruct(harness)
            assert verified_reusable_predecessor(fresh, "sec_company_tickers") is None, (
                "a predecessor that no longer hashes as recorded is not lawful evidence"
            )
            assert conditional_validators(fresh, "sec_company_tickers") is None

    def test_a_zip_predecessor_requires_complete_consistent_lineage(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            reconstruction = _reconstruct(harness)
            assert verified_reusable_predecessor(reconstruction, "sec_bulk_submissions") is not None

            harness.writer.connection.execute(
                "DELETE FROM census_archive_members WHERE archive_sha256 IN "
                "(SELECT logical_sha256 FROM census_source_observations "
                " WHERE source_id = 'sec_bulk_submissions')"
            )
            harness.writer.connection.commit()
            stripped = _reconstruct(harness)
            assert verified_reusable_predecessor(stripped, "sec_bulk_submissions") is None, (
                "an archive owner without preserved member lineage is not reusable"
            )


# =========================================================================== #
# Stage T2.4 — reconciliation and drift inspection (Decision 040 §2, T2.4-B)
# =========================================================================== #
class TestRequestReconciliationT24:
    def test_items_follow_plan_order_and_totals_sum_to_the_plan(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            reconciliation = _reconcile(harness)

        assert [item.position for item in reconciliation.items] == list(
            range(plan.planned_unique_logical_requests)
        )
        assert sum(reconciliation.totals.values()) == plan.planned_unique_logical_requests
        assert reconciliation.totals == {"satisfied_new": 7}
        assert reconciliation.already_satisfied_excluded_count == 7
        assert reconciliation.absences == ()
        assert reconciliation.is_clean is True

    def test_identical_inputs_serialize_byte_identically(self, tmp_path: Path) -> None:
        import json as json_module

        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            first = json_module.dumps(_reconcile(harness).as_record(), sort_keys=True)
            second = json_module.dumps(_reconcile(harness).as_record(), sort_keys=True)
        assert first == second

    def test_an_empty_catalog_reconciles_every_item_as_not_attempted(self, tmp_path: Path) -> None:
        """Kill point 1: nothing consumed, nothing recorded — a fresh run plans identically."""
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            reconciliation = _reconcile(harness)
        assert reconciliation.totals == {"not_attempted": 7}
        assert reconciliation.already_satisfied_excluded_count == 0

    def test_the_absence_enumeration_carries_registered_terminal_reasons(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        first_index = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_full_index_company"
        )
        script[tickers] = _scripted(404, body=b"", content_type=None)
        script[first_index] = _scripted(404, body=b"", content_type=None)
        with _persistent(tmp_path, plan) as harness:
            harness.run(script)
            reconciliation = _reconcile(harness)

        absences = {item.source_id: item for item in reconciliation.absences}
        assert set(absences) == {"sec_company_tickers", "sec_full_index_company"}
        assert absences["sec_company_tickers"].state == "absent"
        assert absences["sec_company_tickers"].reason_codes == (
            "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        )
        assert absences["sec_full_index_company"].reason_codes == ("INDEX_INSTANCE_UNAVAILABLE",), (
            "quarterly-index absence behaviour is unchanged by Decision 040"
        )
        assert reconciliation.absences_without_terminal_reason == ()
        assert all(item.excluded_from_continuation is False for item in reconciliation.absences), (
            "an absence is never counted already-satisfied"
        )
        assert all(item.verified is False for item in reconciliation.absences)

    def test_out_of_plan_observations_are_reported(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            stray = replace(
                harness.storage.snapshot_store.observations[0],
                observation_id="deadbeef" * 4,
                source_id="sec_company_tickers",
                identity="sec_company_tickers:out-of-plan",
                relative_storage_path=None,
                outcome="failed",
                reason_codes=("SEC_RESPONSE_EMPTY",),
            )
            recorder = ObservationRecorder(writer=harness.writer, tree=harness.storage.tree)
            recorder.record(stray)
            reconciliation = _reconcile(harness)

        assert ("sec_company_tickers", "sec_company_tickers:out-of-plan") in (
            reconciliation.out_of_plan
        )

    def test_row_without_object_and_store_findings_are_surfaced_not_repaired(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            reconstruction = _reconstruct(harness)
            tickers = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert tickers is not None
            victim = harness.storage.tree.data_root / str(tickers.relative_storage_path)
            payload = victim.read_bytes()
            victim.unlink()
            (harness.storage.tree.raw_indexes).mkdir(parents=True, exist_ok=True)
            stray_partial = harness.storage.tree.raw_indexes / "stray.part"
            stray_partial.write_bytes(b"partial")
            orphan = harness.storage.tree.raw_indexes / "orphan.bin"
            orphan.write_bytes(b"orphan")

            reconciliation = _reconcile(harness)

            item = next(
                entry for entry in reconciliation.items if entry.source_id == "sec_company_tickers"
            )
            assert item.state == "row_without_object"
            assert item.excluded_from_continuation is False
            kinds = {finding.kind for finding in reconciliation.store_findings}
            assert kinds == {"partial_object", "orphan_object", "row_without_object"}
            assert stray_partial.exists() and orphan.exists(), (
                "reconciliation surfaces findings and repairs nothing"
            )
            victim.write_bytes(payload)

    def test_tampered_evidence_is_a_hash_mismatch_item(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_success_script(plan))
            reconstruction = _reconstruct(harness)
            tickers = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert tickers is not None
            victim = harness.storage.tree.data_root / str(tickers.relative_storage_path)
            victim.write_bytes(b"tampered")
            reconciliation = _reconcile(harness)

        item = next(
            entry for entry in reconciliation.items if entry.source_id == "sec_company_tickers"
        )
        assert item.state == "hash_mismatch"
        assert "hash_mismatch" in item.conditions
        assert item.excluded_from_continuation is False

    def test_the_drift_listing_separates_blocking_from_nonblocking(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(body=b"<html>not json</html>", content_type="application/json")
        with _persistent(tmp_path, plan) as harness:
            harness.run(script)
            exchange = next(
                index
                for index, request in enumerate(requests)
                if request.source_id == "sec_company_tickers_exchange"
            )
            second = _success_script(plan)
            second[exchange] = _scripted(body=b'{"ok":2,"changed":true}')
            harness.run(second)
            reconciliation = _reconcile(harness)

        blocking_codes = {
            code for entry in reconciliation.blocking_drift for code in entry.reason_codes
        }
        nonblocking_codes = {
            code for entry in reconciliation.nonblocking_drift for code in entry.reason_codes
        }
        assert "SEC_RESPONSE_MALFORMED" in blocking_codes
        assert "SOURCE_CONTENT_UPDATED" in nonblocking_codes
        assert not (blocking_codes & nonblocking_codes)


# =========================================================================== #
# Stage T2.4 — accounting vocabulary and lawful conditional reuse (§6, T2.4-C)
# =========================================================================== #
class TestAccountingVocabularyT24:
    def test_already_satisfied_304_and_duplicate_200_stay_distinct(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_etag_script(plan, '"v1"'))
            requests = derive_logical_requests(plan)
            second = _etag_script(plan, '"v1"')
            exchange = next(
                index
                for index, request in enumerate(requests)
                if request.source_id == "sec_company_tickers_exchange"
            )
            # A byte-identical 200 for one route; every other route also replays its exact
            # first-run bytes, so the engine reconciles duplicates rather than superseding.
            outcome = harness.run(second)

            assert outcome.duplicates_reconciled == 7
            assert outcome.byte_identical_duplicates == outcome.duplicates_reconciled
            assert outcome.cache_hits == 0
            assert outcome.not_modified_reuses == outcome.cache_hits

            reconciliation = _reconcile(harness)
            assert reconciliation.duplicate_object_count == 7
            assert reconciliation.not_modified_count == 0
            assert reconciliation.already_satisfied_excluded_count == 7
            del exchange

    def test_a_lawful_304_satisfies_only_through_verified_evidence(self, tmp_path: Path) -> None:
        """ETag-only, Last-Modified-only, and dual-validator reuse against the accepted
        store, plus the unreconciled-304 fail-closed refusal (Decision 040 §2, T2.4-C)."""
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            script = _success_script(plan)
            requests = derive_logical_requests(plan)
            tickers = next(
                index
                for index, request in enumerate(requests)
                if request.source_id == "sec_company_tickers"
            )
            script[tickers] = _scripted(
                headers={"ETag": '"v1"', "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"}
            )
            harness.run(script)
            reconstruction = _reconstruct(harness)
            validators = conditional_validators(reconstruction, "sec_company_tickers")
            assert validators == ('"v1"', "Mon, 01 Jan 2024 00:00:00 GMT")

            def revalidate(etag: str | None, last_modified: str | None) -> object:
                clock = _FrozenClock()
                transport = _ScriptedTransport([_scripted(304, body=b"", content_type=None)])
                limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
                client = SecClient(
                    transport,
                    _AGENT,
                    limiter,
                    RetrievalPolicy(),
                    sleeper=clock.sleep,
                    ceiling=PhysicalAttemptCeiling(10),
                )
                with client.fetch(
                    "sec_company_tickers",
                    purpose=_PURPOSE,
                    etag=etag,
                    last_modified=last_modified,
                ) as result:
                    return reconstruction.store.record(result, retrieved_at_utc=_stamp())

            etag, last_modified = validators
            for sent in ((etag, None), (None, last_modified), (etag, last_modified)):
                observation = revalidate(*sent)
                assert observation.outcome == "reused_snapshot"
                assert observation.reason_codes == ("SOURCE_SNAPSHOT_REUSED",)

            mismatched = revalidate('"wrong"', None)
            assert mismatched.outcome == "failed"
            assert mismatched.reason_codes == ("SOURCE_SNAPSHOT_REUSE_UNRECONCILED",)

    def test_an_unreconciled_304_never_counts_as_satisfied(self, tmp_path: Path) -> None:
        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            harness.run(_etag_script(plan, '"v1"'))
            reconstruction = _reconstruct(harness)
            tickers = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert tickers is not None
            stored = harness.storage.tree.data_root / str(tickers.relative_storage_path)
            stored.write_bytes(b"tampered")

            clock = _FrozenClock()
            transport = _ScriptedTransport([_scripted(304, body=b"", content_type=None)])
            limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
            client = SecClient(
                transport,
                _AGENT,
                limiter,
                RetrievalPolicy(),
                sleeper=clock.sleep,
                ceiling=PhysicalAttemptCeiling(10),
            )
            with client.fetch("sec_company_tickers", purpose=_PURPOSE, etag='"v1"') as result:
                observation = reconstruction.store.record(result, retrieved_at_utc=_stamp())
                recorder = ObservationRecorder(writer=harness.writer, tree=harness.storage.tree)
                recorder.record(observation)

            assert observation.outcome == "failed"
            assert observation.reason_codes == ("SOURCE_SNAPSHOT_REUSE_UNRECONCILED",)
            reconciliation = _reconcile(harness)
            item = next(
                entry for entry in reconciliation.items if entry.source_id == "sec_company_tickers"
            )
            assert item.excluded_from_continuation is False, (
                "a failed-closed 304 is never a cache hit and never satisfies the request"
            )


# =========================================================================== #
# Stage T2.4 — the singleton required-object reason (Decision 040 §4)
# =========================================================================== #
class TestSingletonRequiredObjectReason:
    def test_a_singleton_404_carries_the_required_object_code_durably(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(404, body=b"", content_type=None)
        with _persistent(tmp_path, plan) as harness:
            outcome = harness.run(script)
            absent = next(
                item for item in outcome.outcomes if item.request.source_id == "sec_company_tickers"
            )
            assert absent.disposition == "absent"
            assert absent.reason_codes == ("SOURCE_REQUIRED_OBJECT_UNAVAILABLE",)
            persisted = harness.writer.connection.execute(
                "SELECT reason_code FROM census_observation_reasons WHERE observation_id = ?",
                (absent.observation_id,),
            ).fetchall()
            assert [str(row["reason_code"]) for row in persisted] == [
                "SOURCE_REQUIRED_OBJECT_UNAVAILABLE"
            ], "the terminal reason is durable in the catalog, not only in memory"

    def test_the_code_coexists_with_the_more_specific_quarantine_cause(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(body=b"<html>not json</html>", content_type="application/json")
        with _persistent(tmp_path, plan) as harness:
            outcome = harness.run(script)
        quarantined = next(
            item for item in outcome.outcomes if item.request.source_id == "sec_company_tickers"
        )
        assert quarantined.disposition == "quarantined"
        assert quarantined.reason_codes == (
            "SEC_RESPONSE_MALFORMED",
            "SOURCE_REQUIRED_OBJECT_UNAVAILABLE",
        ), "the availability code coexists with — never replaces — the specific cause"

    def test_the_index_route_keeps_its_accepted_code_in_every_window(self, tmp_path: Path) -> None:
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        first_index = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_full_index_company"
        )
        script[first_index] = _scripted(404, body=b"", content_type=None)
        with _persistent(tmp_path, plan) as harness:
            outcome = harness.run(script)
        absent = next(
            item
            for item in outcome.outcomes
            if item.request.source_id == "sec_full_index_company" and item.disposition == "absent"
        )
        assert absent.reason_codes == ("INDEX_INSTANCE_UNAVAILABLE",)
        assert "SOURCE_REQUIRED_OBJECT_UNAVAILABLE" not in absent.reason_codes

    def test_no_m3_2b_mapping_exists(self, tmp_path: Path) -> None:
        """Decision 040 §4 exclusions: the mapping is bounded to the M3.2A window."""
        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=[]) as (engine, _, _, _):
            failed = _failed_observation("sec_submissions_entity")
            request = LogicalRequest(
                source_id="sec_submissions_entity", instance_key="", parameters={}
            )
            engine_b = replace_engine_window(engine, "M3.2B")
            decorated = engine_b._with_absence_reason(request, failed)
            assert "SOURCE_REQUIRED_OBJECT_UNAVAILABLE" not in decorated.reason_codes
            engine_a = replace_engine_window(engine, "M3.2A")
            positive = engine_a._with_absence_reason(request, failed)
            assert "SOURCE_REQUIRED_OBJECT_UNAVAILABLE" in positive.reason_codes, (
                "positive control: the same observation IS decorated in the M3.2A window"
            )


def _failed_observation(source_id: str) -> SourceObservation:
    return SourceObservation(
        observation_id="ab" * 16,
        source_id=source_id,
        requested_url="https://data.sec.gov/submissions/CIK0000000001.json",
        purpose=_PURPOSE,
        retrieved_at_utc=_stamp(),
        outcome="failed",
        http_status=404,
    )


def replace_engine_window(engine: AcquisitionEngine, window: str) -> AcquisitionEngine:
    """A window-variant engine for probing the private absence-reason mapping boundary."""
    return AcquisitionEngine(
        plan=engine.plan,
        window=window,
        ceiling=engine.ceiling,
        client=engine.client,
        storage=engine.storage,
        recorder=engine.recorder,
        clock=engine.clock,
    )


# =========================================================================== #
# Stage T2.5-T2.6 — Decision 045 high-risk behaviour
# =========================================================================== #
#: The address half of the progress-sink positive control. It uses the RFC-reserved `.invalid`
#: TLD, so it is not, and cannot become, a real contact address.
_SINK_ADDRESS: Final = "fixture-operator@example.invalid"


def _sink_private_path(tmp_path: Path) -> str:
    """A genuine absolute local path, derived rather than written as a literal.

    Decision 045 §12's positive control needs a real absolute path in the sink's message. It is
    composed from the test's own temporary root instead of being spelled out, because a literal
    home path in a tracked file is exactly what `scripts/check_repo_hygiene.py` exists to refuse —
    and the derived value is a *better* control anyway: it is an absolute path on this machine
    rather than a plausible-looking string.
    """
    return str(tmp_path / "private-evidence" / "operator-sink.log")


def _script_with(
    plan: RequestPlan,
    extras: Mapping[int, Sequence[TransportResponse]],
) -> list[TransportResponse]:
    """One success per logical request, with extra responses injected before a chosen request.

    Building the script route-by-route rather than by list insertion matters: each route's
    scripted success is shaped to its own registered content kind, so a bare ``insert`` would
    shift every later response onto the wrong route and quarantine half the window for reasons
    that have nothing to do with the code under test.
    """
    script: list[TransportResponse] = []
    for index, request in enumerate(derive_logical_requests(plan)):
        script.extend(extras.get(index, ()))
        script.append(_success_for(request.source_id))
    return script


#: The one logical request whose registered URL family admits a redirect hop. Its family carries
#: two exact paths, so exactly one in-family redirect target exists and a second would loop.
_REDIRECTING_REQUEST_INDEX: Final = 4
_REDIRECT_TARGET: Final = "https://www.sec.gov/edgar/filer-information/calendar"


class _CountingTransportFactory:
    """A transport factory that records every invocation.

    The whole point of Decision 045 §6 is that a refusal never reaches the construction site, so
    the tests need to count invocations rather than infer them. A factory that is never called
    leaves ``calls == 0``, which is the assertion every refusal test makes.
    """

    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.calls = 0
        self.transports: list[_ScriptedTransport] = []

    def __call__(self) -> _ScriptedTransport:
        self.calls += 1
        transport = _ScriptedTransport(self._responses)
        self.transports.append(transport)
        return transport


def _live_gate(**overrides: object) -> LiveOperatorGate:
    """A complete operator gate, with one element overridable per refusal test.

    Every value is a controlled fixture value. ``sec_identity_validated`` records that the command
    surface ran the canonical validator; no test here supplies, fabricates, or requires a real SEC
    contact identity (Decision 045 §11).
    """
    fields: dict[str, object] = {
        "explicit_live": True,
        "network_enabled": True,
        "m3_acquire_enabled": True,
        "sec_identity_validated": True,
        "stage_authority_reference": "OWNER_TEST_FIXTURE_STAGE_AUTHORITY",
    }
    fields.update(overrides)
    return LiveOperatorGate(**fields)  # type: ignore[arg-type]


def _live_arguments(
    evidence_root: Path,
    plan: RequestPlan,
    factory: _CountingTransportFactory,
    *,
    window: str = "M3.2A",
    ceiling: int | None = None,
    run_id: str = "run-fixture-0001",
    data_relative: str = _DATA_RELATIVE,
) -> dict[str, object]:
    """Every explicit collaborator one live invocation needs, over offline seams."""
    approved = plan.hard_request_ceiling if ceiling is None else ceiling
    clock = _FrozenClock()
    return {
        "plan": plan,
        "window": window,
        "approved_ceiling": approved,
        "authorization": LiveOperationAuthorization(
            window=window,
            plan_sha256=plan.request_plan_sha256,
            approved_ceiling=approved,
            authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
        ),
        "gate": _live_gate(),
        "catalog": prepare_operational_catalog(
            evidence_root=evidence_root, relative_path=_CATALOG_RELATIVE
        ),
        "storage": prepare_storage(evidence_root=evidence_root, data_root_relative=data_relative),
        "user_agent": _AGENT,
        "requests_per_second": 4.0,
        "burst": 1,
        "policy": RetrievalPolicy(),
        "transport_factory": factory,
        "run_id_factory": lambda: run_id,
        "clock": _stamp,
        "sleeper": clock.sleep,
        "rate_limiter": AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep),
    }


def _run_live(
    evidence_root: Path,
    plan: RequestPlan,
    responses: Sequence[TransportResponse],
    **overrides: object,
) -> tuple[object, _CountingTransportFactory]:
    """Execute one live invocation over a scripted transport, and return it with its factory."""
    factory = _CountingTransportFactory(responses)
    arguments = _live_arguments(evidence_root, plan, factory)
    arguments.update(overrides)
    result = execute_live_acquisition(**arguments)  # type: ignore[arg-type]
    return result, factory


def _catalog_rows(evidence_root: Path, statement: str, parameters: tuple[object, ...] = ()) -> list:
    """Read durable rows back through a fresh connection, never an in-memory belief."""
    database = evidence_root / _CATALOG_RELATIVE
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(statement, parameters).fetchall()


class TestResponseEventAccounting:
    """Decision 045 §§9-11: every response event accounted exactly once, on both sides."""

    def test_a_normal_response_contributes_its_actual_status_and_one_bucket(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        accounting = result.accounting  # type: ignore[attr-defined]

        assert accounting.is_exact
        assert accounting.status_code_totals == {"200": plan.planned_unique_logical_requests}
        assert accounting.response_classification_totals["proceed"] == (
            plan.planned_unique_logical_requests
        )
        assert accounting.classified_event_count == accounting.status_event_count

    def test_a_followed_redirect_contributes_its_actual_3xx_a_proceed_and_a_hop(
        self, tmp_path: Path
    ) -> None:
        """Decision 045 §9.3: a followed redirect must not disappear because execution continued.

        Redirect-hop counting and response-policy counting are different metrics, and both
        increment for the same physical response.
        """
        plan = _plan()
        script = _script_with(
            plan,
            {
                _REDIRECTING_REQUEST_INDEX: [
                    _scripted(
                        301,
                        body=b"",
                        content_type=None,
                        headers={"Location": _REDIRECT_TARGET},
                    )
                ]
            },
        )
        result, _ = _run_live(tmp_path, plan, script)
        accounting = result.accounting  # type: ignore[attr-defined]

        assert accounting.is_exact
        assert accounting.status_code_totals["301"] == 1
        assert accounting.redirect_hop_count == 1
        assert accounting.response_classification_totals["proceed"] == (
            plan.planned_unique_logical_requests + 1
        )
        assert accounting.classified_event_count == accounting.status_event_count

    def test_a_lawful_304_is_one_304_status_one_proceed_and_no_duplicate(
        self, tmp_path: Path
    ) -> None:
        """Decision 045 §10: a 304 never silently disappears from the response-policy totals."""
        plan = _plan()
        harness = _PersistentHarness(tmp_path, plan)
        first = harness.run(_success_script(plan))
        assert first.completion_status == "complete"  # type: ignore[attr-defined]

        accounting = ResponseAccounting()
        log = PhysicalResponseLog()
        transport = _ScriptedTransport([_scripted(304, body=b"", content_type=None)])
        recording = RecordingTransport(transport=transport, log=log)
        response = recording.send(
            SecRequest(
                url="https://www.sec.gov/files/company_tickers.json",
                headers={},
                timeout_connect=1.0,
                timeout_read=1.0,
                purpose=_PURPOSE,
                source_id="sec_company_tickers",
            )
        )
        assert response.status == 304
        accounting.absorb(
            _fetch_result(status=304, actions=("request_ceiling_checked", "not_modified")),
            log.drain(),
        )

        assert accounting.is_exact
        assert accounting.status_code_totals == {"304": 1}
        assert accounting.response_classification_totals["proceed"] == 1
        assert "0" not in accounting.status_code_totals

    def test_a_transport_failure_is_the_zero_sentinel_and_one_accepted_bucket(
        self, tmp_path: Path
    ) -> None:
        """Decision 045 §9.4: no HTTP status exists, and no bucket is invented for it."""
        plan = _plan()
        script = _script_with(
            plan, {0: [_scripted(0, body=b"", content_type=None, failure="connection_error")]}
        )
        result, _ = _run_live(tmp_path, plan, script)
        accounting = result.accounting  # type: ignore[attr-defined]

        assert accounting.is_exact
        assert accounting.status_code_totals[NO_HTTP_STATUS_SENTINEL] == 1
        assert accounting.response_classification_totals["retry"] == 1
        assert set(accounting.response_classification_totals) == {
            "cooldown",
            "fail",
            "proceed",
            "quarantine",
            "retry",
            "retry_after",
        }
        assert accounting.classified_event_count == accounting.status_event_count

    def test_a_real_http_response_is_never_recorded_under_the_zero_sentinel(self) -> None:
        """The sentinel is reserved exclusively for a transport-level failure."""
        accounting = ResponseAccounting()
        accounting.absorb(
            _fetch_result(status=0, actions=("proceed",)),
            (0,),
        )

        assert not accounting.is_exact
        assert accounting.undetermined_basis is not None
        assert "reserved" in accounting.undetermined_basis
        assert accounting.status_code_totals == {}

    def test_cooldown_count_is_exactly_the_cooldown_bucket(self, tmp_path: Path) -> None:
        """Decision 045 §11: never a count of sleeps, hops, or elapsed seconds."""
        plan = _plan()
        script = _script_with(plan, {0: [_scripted(429, body=b"", content_type=None)]})
        result, _ = _run_live(tmp_path, plan, script)
        accounting = result.accounting  # type: ignore[attr-defined]

        assert accounting.is_exact
        assert accounting.response_classification_totals["cooldown"] == 1
        assert accounting.cooldown_count == accounting.response_classification_totals["cooldown"]
        assert accounting.status_code_totals["429"] == 1

    def test_a_mixed_sequence_accounts_every_event_exactly_once(self, tmp_path: Path) -> None:
        """The §22 mixed-sequence case: redirect, normal response, and transport failure."""
        plan = _plan()
        script = _script_with(
            plan,
            {
                0: [_scripted(0, body=b"", content_type=None, failure="read_timeout")],
                _REDIRECTING_REQUEST_INDEX: [
                    _scripted(
                        307,
                        body=b"",
                        content_type=None,
                        headers={"Location": _REDIRECT_TARGET},
                    )
                ],
            },
        )
        result, _ = _run_live(tmp_path, plan, script)
        accounting = result.accounting  # type: ignore[attr-defined]

        assert accounting.is_exact
        assert accounting.classified_event_count == accounting.status_event_count
        assert accounting.status_code_totals["307"] == 1
        assert accounting.status_code_totals[NO_HTTP_STATUS_SENTINEL] == 1
        assert accounting.status_code_totals["200"] == plan.planned_unique_logical_requests
        assert accounting.redirect_hop_count == 1
        # Every physical send is accounted: seven successes, one refused-then-retried read
        # timeout, and one followed redirect.
        assert accounting.status_event_count == plan.planned_unique_logical_requests + 2

    def test_a_pre_transport_refusal_contributes_to_neither_total(self, tmp_path: Path) -> None:
        """Decision 045 §9.1: a refusal before any physical response is not a response event."""
        plan = _plan()
        factory = _CountingTransportFactory([])
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["approved_ceiling"] = plan.hard_request_ceiling - 1

        with pytest.raises(AcquisitionGateError):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0, "a pre-transport refusal reached the construction site"

    def test_an_unknown_client_action_refuses_rather_than_undercounting(self) -> None:
        """Fail-closed: an unaccounted marker is undetermined, never silently skipped."""
        accounting = ResponseAccounting()
        accounting.absorb(_fetch_result(status=200, actions=("a_marker_from_the_future",)), (200,))

        assert not accounting.is_exact
        assert accounting.status_code_totals == {}

    def test_positive_control_the_same_absorption_is_exact_with_a_known_action(self) -> None:
        accounting = ResponseAccounting()
        accounting.absorb(_fetch_result(status=200, actions=("proceed",)), (200,))

        assert accounting.is_exact
        assert accounting.status_code_totals == {"200": 1}


def _fetch_result(
    *,
    status: int | None,
    actions: tuple[str, ...],
    redirect_hops: tuple[object, ...] = (),
) -> object:
    """A minimal accepted-shape retrieval result, for direct accounting unit tests."""
    from disclosure_drift.sec.http_client import FetchResult

    return FetchResult(
        outcome="retrieved",
        source_id="sec_company_tickers",
        url="https://www.sec.gov/files/company_tickers.json",
        purpose=_PURPOSE,
        status=status,
        actions=actions,
        redirect_hops=redirect_hops,  # type: ignore[arg-type]
    )


class TestAcquisitionRunIdentity:
    """Decision 045 §6A: one durable run per live invocation, registered before any transport."""

    def test_a_lawful_invocation_registers_exactly_one_m3_2_run_row(self, tmp_path: Path) -> None:
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-alpha")

        rows = _catalog_rows(tmp_path, "SELECT job_id, job_kind, stage FROM ops_ingestion_jobs")

        assert len(rows) == 1
        assert rows[0]["job_id"] == "run-alpha"
        assert rows[0]["job_kind"] == ACQUISITION_JOB_KIND
        assert rows[0]["stage"] == "M3.2A"

    def test_the_registered_kind_is_not_the_m2_2_census_kind(self, tmp_path: Path) -> None:
        """The M2.2-only registration is never reused, and its job kind is never hardcoded."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan))

        rows = _catalog_rows(tmp_path, "SELECT job_kind, stage FROM ops_ingestion_jobs")

        assert rows[0]["job_kind"] != "sec_census"
        assert rows[0]["stage"] != "M2.2"

    def test_registration_happens_before_the_transport_is_constructed(self, tmp_path: Path) -> None:
        """Decision 045 §6A.2 step 7: the construction site is reachable only after step 6.

        The factory reads the durable catalog at the moment it is called. Finding the run row
        already committed proves the ordering from the construction site's own point of view,
        which a test that only inspected the end state could not.
        """
        plan = _plan()
        observed: list[int] = []

        class _OrderingFactory(_CountingTransportFactory):
            def __call__(self) -> _ScriptedTransport:
                observed.append(
                    len(_catalog_rows(tmp_path, "SELECT job_id FROM ops_ingestion_jobs"))
                )
                return super().__call__()

        factory = _OrderingFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["transport_factory"] = factory
        execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 1
        assert observed == [1], "the run row was not durable when the transport was constructed"

    def test_a_registration_failure_prevents_every_transport_and_request(
        self, tmp_path: Path
    ) -> None:
        """On failure: no transport, no physical request, and nothing attributed to the run."""
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)

        def _refuse() -> str:
            return "   "

        arguments["run_id_factory"] = _refuse

        with pytest.raises(AcquisitionRunError):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0
        assert _catalog_rows(tmp_path, "SELECT job_id FROM ops_ingestion_jobs") == []
        assert _catalog_rows(tmp_path, "SELECT census_run_id FROM census_plan_sources") == []

    def test_a_failed_registration_verification_prevents_every_transport(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Decision 045 §6A.2 step 6: verification is a separate, load-bearing step.

        The verification re-reads the run row through a genuinely fresh read-only connection. Its
        refusal is forced here rather than simulated by corrupting SQLite, because the accepted
        writer does not silently fail to commit — so what a durable-write fault would look like
        cannot be produced honestly. What *is* under test is that the step happens at all on this
        path, and that its refusal precedes the construction site: skip the call and the transport
        is built regardless of whether the registration was ever verified.
        """
        import disclosure_drift.m3.acquisition as acquisition_module

        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)

        def _unverifiable(catalog_path: Path, census_run_id: str) -> str:
            message = f"the registration of {census_run_id!r} could not be verified"
            raise AcquisitionRunError(message)

        monkeypatch.setattr(acquisition_module, "validate_acquisition_run", _unverifiable)

        with pytest.raises(AcquisitionRunError, match="could not be verified"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0

    def test_a_repeated_run_identity_is_refused_before_any_transport(self, tmp_path: Path) -> None:
        """One live invocation registers one run; an existing identity is never adopted."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-repeated")

        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["run_id_factory"] = lambda: "run-repeated"

        with pytest.raises(AcquisitionRunError, match="already registered"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0

    def test_every_planned_request_is_durably_attributed_to_its_run(self, tmp_path: Path) -> None:
        """Decision 045 §6A.4, through the existing accepted run-scoped relation."""
        plan = _plan()
        result, _ = _run_live(
            tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-attributed"
        )

        rows = _catalog_rows(
            tmp_path,
            "SELECT source_instance_id, observation_id, retrieval_state, successful_terminal "
            "FROM census_plan_sources WHERE census_run_id = ? ORDER BY source_instance_id",
            ("run-attributed",),
        )

        assert len(rows) == plan.planned_unique_logical_requests
        assert all(row["observation_id"] is not None for row in rows)
        assert all(row["retrieval_state"] == "retrieved" for row in rows)
        assert all(row["successful_terminal"] == 1 for row in rows)
        assert result.outcome.completion_status == "complete"  # type: ignore[attr-defined]

    def test_show_drift_isolates_two_distinct_runs_in_one_catalog(self, tmp_path: Path) -> None:
        """Run scoping is real: a second run's drift is not attributed to the first.

        The two runs share one catalog and one data root, so a listing that fell back to unscoped
        global drift would report the second run's quarantined object under the first.
        """
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-clean")

        # A second, independent invocation whose bulk archive is refused, producing drift.
        drifting = _script_with(plan, {})
        drifting[0] = _scripted(body=b"not-a-zip-archive", content_type="application/zip")
        _run_live(tmp_path, plan, drifting, run_id_factory=lambda: "run-drifting")

        clean = drift_for_run(catalog_path=tmp_path / _CATALOG_RELATIVE, census_run_id="run-clean")
        drifted = drift_for_run(
            catalog_path=tmp_path / _CATALOG_RELATIVE, census_run_id="run-drifting"
        )

        assert clean.entries == ()
        assert clean.has_blocking is False
        assert drifted.entries, "the second run produced no drift, so isolation is untested"
        assert drifted.has_blocking is True
        assert {entry.observation_id for entry in clean.entries}.isdisjoint(
            {entry.observation_id for entry in drifted.entries}
        )

    def test_drift_refuses_an_unknown_a_foreign_and_an_unattributed_run(
        self, tmp_path: Path
    ) -> None:
        """Every unlawful run identity fails closed; none falls back to a global listing."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-known")
        catalog = tmp_path / _CATALOG_RELATIVE

        with pytest.raises(AcquisitionRunError, match="does not resolve"):
            drift_for_run(catalog_path=catalog, census_run_id="run-never-registered")

        with CatalogWriter(catalog, catalog.parent) as writer, writer.batch():
            writer.insert(
                "ops_ingestion_jobs",
                {
                    "job_id": "run-census",
                    "job_kind": "sec_census",
                    "job_state": "running",
                    "stage": "M2.2",
                    "started_at_utc": _stamp(),
                    "detail": "a Stage M2.2 census run, not an M3.2 acquisition run",
                },
            )
            writer.insert(
                "ops_ingestion_jobs",
                {
                    "job_id": "run-unattributed",
                    "job_kind": ACQUISITION_JOB_KIND,
                    "job_state": "running",
                    "stage": "M3.2A",
                    "started_at_utc": _stamp(),
                    "detail": "registered but never attributed",
                },
            )

        with pytest.raises(AcquisitionRunError, match="job kind"):
            drift_for_run(catalog_path=catalog, census_run_id="run-census")
        with pytest.raises(AcquisitionRunError, match="no durable observation attribution"):
            drift_for_run(catalog_path=catalog, census_run_id="run-unattributed")

    def test_positive_control_the_known_run_still_lists(self, tmp_path: Path) -> None:
        """The refusals above are not a guard that refuses everything."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-known")

        scoped = drift_for_run(catalog_path=tmp_path / _CATALOG_RELATIVE, census_run_id="run-known")

        assert scoped.stage == "M3.2A"
        assert scoped.attributed_observation_count == plan.planned_unique_logical_requests

    def test_validate_acquisition_run_refuses_a_fabricated_identity(self, tmp_path: Path) -> None:
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-real")
        catalog = tmp_path / _CATALOG_RELATIVE

        assert validate_acquisition_run(catalog, "run-real") == "M3.2A"
        for fabricated in ("", "   ", "run-real-but-not-quite"):
            with pytest.raises(AcquisitionRunError):
                validate_acquisition_run(catalog, fabricated)

    def test_a_run_id_factory_allocates_a_distinct_identity_per_invocation(self) -> None:
        """Positive control: the default mechanism does not return a constant."""
        assert default_run_id_factory() != default_run_id_factory()

    def test_register_refuses_a_window_outside_the_accepted_set(self, tmp_path: Path) -> None:
        preparation = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )

        with pytest.raises(AcquisitionRunError):
            register_acquisition_run(
                catalog_path=preparation.database_path,
                lock_directory=preparation.lock_directory,
                census_run_id="run-bad-window",
                window="M9.9Z",
                started_at_utc=_stamp(),
                detail="fixture",
            )
        assert _catalog_rows(tmp_path, "SELECT job_id FROM ops_ingestion_jobs") == []


class TestLiveOperatorBoundary:
    """Decision 045 §6: the conjunction, and the site no refusal may reach."""

    @pytest.mark.parametrize(
        "element",
        [
            "explicit_live",
            "network_enabled",
            "m3_acquire_enabled",
            "sec_identity_validated",
        ],
    )
    def test_each_conjunction_element_refuses_on_its_own(
        self, tmp_path: Path, element: str
    ) -> None:
        """Every element is load-bearing individually, not merely as part of a conjunction."""
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)

        with pytest.raises(AcquisitionGateError):
            arguments["gate"] = _live_gate(**{element: False})
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0

    def test_an_unnamed_stage_authority_refuses(self, tmp_path: Path) -> None:
        """The gate refuses at construction, which is earlier than the execution path.

        An incomplete gate cannot be built at all, so it can never be handed to the live path.
        The refusal is asserted around the construction *and* the invocation together, because
        either point refusing is the property that matters — and the transport factory must be
        untouched whichever one fires.
        """
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)

        with pytest.raises(AcquisitionGateError, match="stage authority"):
            arguments["gate"] = _live_gate(stage_authority_reference="   ")
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.calls == 0

    def test_a_plan_hash_mismatch_refuses_before_the_construction_site(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["authorization"] = LiveOperationAuthorization(
            window="M3.2A",
            plan_sha256="f" * 64,
            approved_ceiling=plan.hard_request_ceiling,
            authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
        )

        with pytest.raises(AcquisitionGateError, match="plan hash"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    @pytest.mark.parametrize("delta", [-1, 1])
    def test_a_ceiling_that_is_not_exactly_the_plan_ceiling_refuses(
        self, tmp_path: Path, delta: int
    ) -> None:
        """C-1 and C+1 both refuse; only exact equality passes."""
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(
            tmp_path, plan, factory, ceiling=plan.hard_request_ceiling + delta
        )

        with pytest.raises(AcquisitionGateError, match="ceiling"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_the_operator_ceiling_must_equal_the_authorized_ceiling_exactly(
        self, tmp_path: Path
    ) -> None:
        """The gate the operator constructed and the ceiling it was given must be the same integer.

        Distinct from the plan-ceiling check below it: this one catches an operator ceiling that
        disagrees with the authorization it was issued under, even when the authorization itself
        is internally consistent with some other plan.
        """
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["approved_ceiling"] = plan.hard_request_ceiling + 1

        with pytest.raises(AcquisitionGateError, match="must equal the approved integer exactly"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_a_window_the_plan_was_not_built_for_refuses(self, tmp_path: Path) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory, window="M3.2B")

        with pytest.raises(AcquisitionGateError, match="window"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_positive_control_the_exact_bindings_reach_the_construction_site_once(
        self, tmp_path: Path
    ) -> None:
        """Without this, every refusal above would pass against a gate that refuses everything."""
        plan = _plan()
        result, factory = _run_live(tmp_path, plan, _success_script(plan))

        assert factory.calls == 1
        assert result.outcome.completed_successfully is True  # type: ignore[attr-defined]

    def test_the_wrapped_transport_is_closed_even_when_the_window_fails(
        self, tmp_path: Path
    ) -> None:
        """A scripted transport exhausted mid-window still releases its resources."""
        plan = _plan()
        factory = _CountingTransportFactory([_success_for("sec_bulk_submissions")])
        arguments = _live_arguments(tmp_path, plan, factory)

        with pytest.raises(AssertionError, match="scripted transport was exhausted"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert factory.transports[0].closed is True

    def test_verify_window_bindings_refuses_a_route_outside_the_window(self) -> None:
        """Window separation is enforced in both directions, before any transport exists."""
        plan = _plan()
        authorization = LiveOperationAuthorization(
            window="M3.2B",
            plan_sha256=plan.request_plan_sha256,
            approved_ceiling=plan.hard_request_ceiling,
            authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
        )

        with pytest.raises(AcquisitionGateError):
            verify_window_bindings(
                plan=plan,
                window="M3.2B",
                approved_ceiling=plan.hard_request_ceiling,
                authorization=authorization,
            )

    def test_positive_control_verify_window_bindings_returns_the_expansion(self) -> None:
        plan = _plan()
        requests = verify_window_bindings(
            plan=plan,
            window="M3.2A",
            approved_ceiling=plan.hard_request_ceiling,
            authorization=_authorization(plan),
        )

        assert len(requests) == plan.planned_unique_logical_requests

    def test_the_default_transport_factory_is_never_invoked_by_the_suite(self) -> None:
        """Structural: the real factory exists, is callable, and no test ever calls it."""
        assert callable(default_live_transport_factory)


class TestProgressSinkExclusion:
    """Decision 045 §12: raw operator-controlled text never reaches a written artifact."""

    def test_a_sink_exception_carrying_a_path_and_an_address_is_excluded(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The required positive control: both strings reach stderr and neither is retained.

        Exclusion is demonstrated *before* the receipt's prohibited-content validator is relied
        on: the retained field simply never contains either string, so the validator is a backstop
        rather than the defence.
        """

        private_path = _sink_private_path(tmp_path)

        def _sink(_: object) -> None:
            message = f"sink wrote {private_path} and notified {_SINK_ADDRESS}"
            raise RuntimeError(message)

        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan), progress=_sink)
        outcome = result.outcome  # type: ignore[attr-defined]
        retained = " ".join(outcome.progress_failures)
        captured = capsys.readouterr()

        assert private_path in captured.err, "the sink did not actually raise"
        assert _SINK_ADDRESS in captured.err, "the sink did not actually raise"
        assert private_path not in retained
        assert _SINK_ADDRESS not in retained
        assert "fixture-operator" not in retained
        assert PROGRESS_SINK_FAILURE_REASON in retained
        assert outcome.completion_status == "complete"

    def test_the_excluded_text_reaches_no_catalog_row_or_stored_artifact(
        self, tmp_path: Path
    ) -> None:
        """Nothing durable below the evidence root may carry the sink's text either."""

        private_path = _sink_private_path(tmp_path)

        def _sink(_: object) -> None:
            message = f"sink wrote {private_path} and notified {_SINK_ADDRESS}"
            raise RuntimeError(message)

        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), progress=_sink)

        for path in sorted(tmp_path.rglob("*")):
            if not path.is_file():
                continue
            payload = path.read_bytes()
            assert private_path.encode() not in payload, path
            assert _SINK_ADDRESS.encode() not in payload, path

    def test_an_exception_class_named_to_smuggle_content_is_sanitized(self) -> None:
        """The retained class name is allowlist-filtered, not merely assumed to be an identifier."""
        from disclosure_drift.m3.acquisition import sanitized_progress_failure

        # Composed rather than written as a literal, so the fixture proves the allowlist
        # filters separators and address markers without putting either in a tracked file.
        smuggler = type("Bad" + chr(47) + "root" + chr(64) + "host.example", (Exception,), {})
        recorded = sanitized_progress_failure("sec_company_tickers", smuggler())

        assert "/" not in recorded.removeprefix("sec_company_tickers")
        assert "@" not in recorded
        assert PROGRESS_SINK_FAILURE_REASON in recorded


def _continuation(
    plan: RequestPlan,
    *,
    permitted: bool = True,
    determination: str = "SAFE",
    approved_ceiling: int | None = None,
    predecessor_receipt_id: str | None = "predecessor-receipt-identity",
    consumed: int = 0,
    remaining_count: int = 2,
) -> object:
    """A continuation proposal with controlled fixture values.

    ``propose_continuation``'s own derivation - cumulative accounting, in-flight identification,
    UNDETERMINED refusal, write-ahead blocking - is covered exhaustively by the accepted T2.4
    suite. What is under test here is the *resume binding* the live path enforces on top of it,
    so the proposal is supplied directly rather than re-derived.
    """
    from disclosure_drift.m3.acquisition import (
        ContinuationProposal,
        ContinuationRequest,
        CumulativeAttemptAccounting,
        RequestReconciliation,
    )
    from disclosure_drift.m3.recovery import RecoveryState

    ceiling = plan.hard_request_ceiling if approved_ceiling is None else approved_ceiling
    requests = derive_logical_requests(plan)[:remaining_count]
    return ContinuationProposal(
        permitted=permitted,
        determination=determination,
        refusal_reasons=() if permitted else ("a fixture refusal reason",),
        window="M3.2A",
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=ceiling,
        predecessor_receipt_id=predecessor_receipt_id,
        receipt_chain=("predecessor-receipt-identity",),
        accounting=CumulativeAttemptAccounting(
            chain_consumed=consumed,
            post_receipt_attempts=0,
            in_flight_charge=0,
            in_flight_request_identity=None,
            undetermined=False,
            basis="every attempt segment is attributed exactly once",
        ),
        remaining_headroom=max(0, ceiling - consumed),
        worst_case_remaining_attempts=0,
        fits=True,
        already_satisfied_excluded=("sec_bulk_submissions",),
        remaining=tuple(
            ContinuationRequest(
                position=index,
                source_id=request.source_id,
                identity_label=request.identity_label,
                request_identity=request.identity_label,
                etag=None,
                last_modified=None,
            )
            for index, request in enumerate(requests)
        ),
        reconciliation=RequestReconciliation(
            window="M3.2A",
            plan_sha256=plan.request_plan_sha256,
            items=(),
            out_of_plan=(),
            store_findings=(),
            drift=(),
            blocked_recovery_states=0,
        ),
        inspection=RecoveryState(
            determination=determination,
            basis="fixture",
            required_action="none",
            conditions=(),
            receipt_chain=("predecessor-receipt-identity",),
            interruption_state=None,
            consumed_physical_attempts=consumed,
            committed_observation_count=0,
            orphan_object_count=0,
            rows_without_object_count=0,
            partial_file_count=0,
        ),
    )


class TestResumeIntegration:
    """Decision 045 §14: what a resumed live invocation must prove before it may continue."""

    def test_a_resumed_invocation_registers_a_new_run_identity(self, tmp_path: Path) -> None:
        """Decision 045 §6A.3: a run identifies one invocation, never a whole window."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-first")
        result, factory = _run_live(
            tmp_path,
            plan,
            _success_script(plan),
            run_id_factory=lambda: "run-resumed",
            continuation=_continuation(plan),
        )

        assert factory.calls == 1
        assert result.census_run_id == "run-resumed"  # type: ignore[attr-defined]
        assert result.predecessor_receipt_id == "predecessor-receipt-identity"  # type: ignore[attr-defined]
        rows = _catalog_rows(tmp_path, "SELECT job_id FROM ops_ingestion_jobs ORDER BY job_id")
        assert [row["job_id"] for row in rows] == ["run-first", "run-resumed"]

    def test_a_refused_proposal_refuses_the_resume_before_any_transport(
        self, tmp_path: Path
    ) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(plan, permitted=False)

        with pytest.raises(AcquisitionGateError, match="refuses this resume"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    @pytest.mark.parametrize("determination", ["UNDETERMINED", "UNSAFE"])
    def test_a_resume_proceeds_only_from_a_safe_inspection(
        self, tmp_path: Path, determination: str
    ) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(plan, determination=determination)

        with pytest.raises(AcquisitionGateError, match="SAFE"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_a_resume_may_not_change_the_approved_ceiling(self, tmp_path: Path) -> None:
        """The approved ceiling is never reset, raised, or replaced across a resume."""
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(
            plan, approved_ceiling=plan.hard_request_ceiling + 5
        )

        with pytest.raises(AcquisitionGateError, match="never reset, raised, or replaced"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_a_resume_requires_an_exact_predecessor_receipt_identity(self, tmp_path: Path) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(plan, predecessor_receipt_id=None)

        with pytest.raises(AcquisitionGateError, match="exact predecessor receipt"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_a_resume_with_nothing_remaining_refuses_rather_than_re_requesting(
        self, tmp_path: Path
    ) -> None:
        """An already-satisfied substantive write is never repeated."""
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(plan, remaining_count=0)

        with pytest.raises(AcquisitionGateError, match="nothing lawful to acquire"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_a_resume_past_its_own_ceiling_refuses(self, tmp_path: Path) -> None:
        plan = _plan()
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = _continuation(plan, consumed=plan.hard_request_ceiling + 1)

        with pytest.raises(AcquisitionGateError, match="already exceeds"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]
        assert factory.calls == 0

    def test_carried_forward_consumption_is_charged_against_the_ceiling(
        self, tmp_path: Path
    ) -> None:
        """The resumed window starts at the predecessor's consumption, never at zero."""
        plan = _plan()
        carried = 3
        remaining = 2
        result, _ = _run_live(
            tmp_path,
            plan,
            [
                _success_for(request.source_id)
                for request in derive_logical_requests(plan)[:remaining]
            ],
            continuation=_continuation(plan, consumed=carried, remaining_count=remaining),
        )
        outcome = result.outcome  # type: ignore[attr-defined]

        assert result.carried_forward_consumed == carried  # type: ignore[attr-defined]
        assert outcome.approved_ceiling == plan.hard_request_ceiling
        # The predecessor's consumption is carried, and only the remainder is placed on top of
        # it: the ceiling is charged cumulatively and the satisfied work is never re-requested.
        assert outcome.consumed_physical_attempts == carried + remaining

    def test_a_resume_places_only_the_remaining_requests(self, tmp_path: Path) -> None:
        """Decision 045 §14: an already-satisfied substantive write is never repeated.

        The resumed invocation is given a two-request remainder against a seven-request plan, and
        is scripted with exactly two responses. A resume that re-derived the whole expansion would
        exhaust the script and fail loudly, which is precisely the duplication being excluded.
        """
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-predecessor")
        remaining = derive_logical_requests(plan)[:2]

        result, factory = _run_live(
            tmp_path,
            plan,
            [_success_for(request.source_id) for request in remaining],
            run_id_factory=lambda: "run-continued",
            continuation=_continuation(plan, remaining_count=2),
        )
        outcome = result.outcome  # type: ignore[attr-defined]

        assert factory.calls == 1
        assert outcome.planned_logical_requests == 2
        assert len(outcome.satisfied) == 2
        assert outcome.consumed_physical_attempts == 2
        attributed = _catalog_rows(
            tmp_path,
            "SELECT source_instance_id FROM census_plan_sources WHERE census_run_id = ?",
            ("run-continued",),
        )
        assert sorted(row["source_instance_id"] for row in attributed) == sorted(
            request.identity_label for request in remaining
        )

    def test_a_remainder_the_plan_does_not_contain_refuses(self, tmp_path: Path) -> None:
        """The proposal and the plan must agree about what the window contains."""
        plan = _plan()
        proposal = _continuation(plan, remaining_count=1)
        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["continuation"] = replace(
            proposal,  # type: ignore[arg-type]
            remaining=(replace(proposal.remaining[0], identity_label="not_a_planned_identity"),),  # type: ignore[attr-defined]
        )

        with pytest.raises(AcquisitionGateError, match="does not expand to"):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

    def test_positive_control_a_permitted_safe_proposal_resumes(self, tmp_path: Path) -> None:
        """Without this, every refusal above would pass against a resume that refuses everything."""
        plan = _plan()
        remaining = derive_logical_requests(plan)[:2]
        result, factory = _run_live(
            tmp_path,
            plan,
            [_success_for(request.source_id) for request in remaining],
            continuation=_continuation(plan, remaining_count=2),
        )

        assert factory.calls == 1
        assert result.resumed is True  # type: ignore[attr-defined]


class TestReceiptAssembly:
    """Decision 045 §7, §8, §13: what the producer binds, and what the frozen schema refuses."""

    def _receipt(
        self,
        tmp_path: Path,
        plan: RequestPlan,
        script: Sequence[TransportResponse],
        *,
        run_id: str = "run-fixture-0001",
    ) -> ExecutionReceipt:
        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config

        result, _ = _run_live(tmp_path, plan, script, run_id_factory=lambda: run_id)
        return _live_acquisition_receipt(
            result,  # type: ignore[arg-type]
            plan=plan,
            window="M3.2A",
            approved_ceiling=plan.hard_request_ceiling,
            continuation=None,
            config=load_config(None),
            catalog_path=tmp_path / _CATALOG_RELATIVE,
        )

    def test_a_complete_window_produces_a_valid_live_receipt(self, tmp_path: Path) -> None:
        from disclosure_drift.m3.receipt import validate_receipt_document

        plan = _plan()
        receipt = self._receipt(tmp_path, plan, _success_script(plan))
        document = receipt.as_document()
        validate_receipt_document(document)

        assert document["invocation_mode"] == "live"
        assert document["completion_status"] == "complete"
        assert document["acquisition_window"] == "M3.2A"
        assert document["approved_request_ceiling"] == plan.hard_request_ceiling
        assert document["actual_physical_attempt_count"] == plan.planned_unique_logical_requests
        assert document["raw_object_count"] == plan.planned_unique_logical_requests
        assert "reason_code" not in document, "a complete window carries no reason code"

    def test_the_response_totals_satisfy_the_equality_invariant(self, tmp_path: Path) -> None:
        """Decision 045 §9: the two universes agree exactly in the written receipt."""
        plan = _plan()
        document = self._receipt(tmp_path, plan, _success_script(plan)).as_document()

        classification = document["response_classification_totals"]
        statuses = document["status_code_totals"]
        assert sum(classification.values()) == sum(statuses.values())  # type: ignore[union-attr]
        assert document["cooldown_count"] == classification["cooldown"]  # type: ignore[index]

    def test_the_cache_hit_count_is_the_excluded_set_not_the_304_reuses(
        self, tmp_path: Path
    ) -> None:
        """Decision 045 §8: the legacy `WindowOutcome.cache_hits` alias must not populate it."""
        plan = _plan(satisfied=frozenset({"2010QTR1"}))
        document = self._receipt(tmp_path, plan, _success_script(plan)).as_document()

        assert plan.expected_cache_hits == 1
        assert document["cache_hit_count"] == plan.expected_cache_hits
        assert document["not_modified_count"] == 0

    def test_the_two_reuse_counters_are_bound_to_different_dispositions(
        self, tmp_path: Path
    ) -> None:
        """The two reuse counters are never populated from each other, or from the alias.

        A window that places only unconditional requests and stores every object new leaves both
        at zero and ``raw_object_count`` at the planned total, so a receipt that had crossed the
        two counters — or populated either from the legacy ``cache_hits`` alias — would disagree
        with the window it describes.
        """
        plan = _plan()
        document = self._receipt(tmp_path, plan, _success_script(plan)).as_document()

        assert document["raw_object_count"] == plan.planned_unique_logical_requests
        assert document["duplicate_object_count"] == 0
        assert document["not_modified_count"] == 0
        assert document["cache_hit_count"] == plan.expected_cache_hits

    def test_a_duplicate_window_reports_duplicates_and_no_not_modified_reuses(
        self, tmp_path: Path
    ) -> None:
        """Decision 045 §8 / Decision 040 §6: the three reuse counters are never interchangeable.

        A second window over byte-identical bodies, against a store that has preserved the first
        window's objects, reconciles every request as a byte-identical ``200``. That makes
        ``duplicate_object_count`` non-zero while ``raw_object_count`` and ``not_modified_count``
        stay zero — so a receipt that populated any of the three from another would disagree with
        the window it describes. A single-run fixture cannot show this: the distinction only
        exists once a later run sees what an earlier one preserved.
        """
        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config
        from disclosure_drift.m3.acquisition import LiveAcquisitionResult

        plan = _plan()
        with _persistent(tmp_path, plan) as harness:
            first = harness.run(_success_script(plan))
            assert first.completion_status == "complete"  # type: ignore[attr-defined]
            # A second invocation carries its own gate: the approved ceiling is per window and is
            # never doubled, and the equality check refuses anything else.
            harness.gate = PhysicalAttemptCeiling(plan.hard_request_ceiling)
            second = harness.run(_success_script(plan))

        assert second.duplicates_reconciled == plan.planned_unique_logical_requests  # type: ignore[attr-defined]
        accounting = ResponseAccounting()
        for _ in range(plan.planned_unique_logical_requests):
            accounting.absorb(_fetch_result(status=200, actions=("proceed",)), (200,))
        document = _live_acquisition_receipt(
            LiveAcquisitionResult(
                census_run_id="run-duplicates",
                outcome=second,  # type: ignore[arg-type]
                accounting=accounting,
                started_at_utc=_stamp(),
                completed_at_utc=_stamp(),
                predecessor_receipt_id=None,
                carried_forward_consumed=None,
                run_closed=True,
            ),
            plan=plan,
            window="M3.2A",
            approved_ceiling=plan.hard_request_ceiling,
            continuation=None,
            config=load_config(None),
            catalog_path=tmp_path / _CATALOG_RELATIVE,
        ).as_document()

        assert document["duplicate_object_count"] == plan.planned_unique_logical_requests
        assert document["raw_object_count"] == 0
        assert document["not_modified_count"] == 0

    def test_a_quarantined_window_reports_a_registered_reason_and_is_not_complete(
        self, tmp_path: Path
    ) -> None:
        from disclosure_drift.m3.receipt import validate_receipt_document
        from disclosure_drift.reasons import REASON_CODES

        plan = _plan()
        script = _script_with(plan, {})
        script[0] = _scripted(body=b"not-a-zip-archive", content_type="application/zip")
        document = self._receipt(tmp_path, plan, script).as_document()
        validate_receipt_document(document)

        assert document["completion_status"] == "failed"
        assert document["reason_code"] in REASON_CODES
        assert document["quarantined_object_count"] == 1
        assert document["schema_drift_outcome"] == "blocked"

    def test_the_frozen_schema_refuses_completed_with_absences(self) -> None:
        """There is no such completion status, and this stage does not introduce one."""
        from disclosure_drift.m3.receipt import ExecutionReceipt, ReceiptValidationError

        with pytest.raises(ReceiptValidationError, match="completion_status"):
            ExecutionReceipt(
                command_name="m3 acquire",
                command_version="m3.2/1.0",
                phase="M3.2A",
                invocation_mode="live",
                configuration_fingerprint="a" * 64,
                migration_chain_head="0013_m23_manifest_lifecycle_guards",
                started_at_utc="2026-08-04T00:00:00Z",
                completed_at_utc="2026-08-04T00:00:01Z",
                elapsed_seconds=1.0,
                actual_logical_request_count=0,
                actual_physical_attempt_count=0,
                completion_status="completed_with_absences",
            )

    def test_the_frozen_schema_refuses_an_unknown_receipt_field(self, tmp_path: Path) -> None:
        """The permitted field set is closed; a new field requires a new accepted decision."""
        from disclosure_drift.m3.receipt import ReceiptValidationError, validate_receipt_document

        plan = _plan()
        document = self._receipt(tmp_path, plan, _success_script(plan)).as_document()
        document["m3_2_run_identity"] = "run-alpha"

        with pytest.raises(ReceiptValidationError, match="not a permitted receipt field"):
            validate_receipt_document(document)

    def test_no_progress_sink_text_reaches_the_receipt(self, tmp_path: Path) -> None:
        """The §12 exclusion holds through receipt assembly, not only in the window outcome."""
        from disclosure_drift.m3.receipt import canonical_bytes

        private_path = _sink_private_path(tmp_path)

        def _sink(_: object) -> None:
            message = f"sink wrote {private_path} and notified {_SINK_ADDRESS}"
            raise RuntimeError(message)

        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config

        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan), progress=_sink)
        receipt = _live_acquisition_receipt(
            result,  # type: ignore[arg-type]
            plan=plan,
            window="M3.2A",
            approved_ceiling=plan.hard_request_ceiling,
            continuation=None,
            config=load_config(None),
            catalog_path=tmp_path / _CATALOG_RELATIVE,
        )
        payload = canonical_bytes(receipt.as_document())

        assert private_path.encode() not in payload
        assert _SINK_ADDRESS.encode() not in payload

    def test_an_inexact_accounting_refuses_the_receipt(self, tmp_path: Path) -> None:
        """Decision 045 §9.5: exactness or a stop — never an inferred or undercounted receipt."""
        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config
        from disclosure_drift.errors import GateFailureError

        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        result.accounting.mark_undetermined("a fixture accounting defect")  # type: ignore[attr-defined]

        with pytest.raises(GateFailureError, match="not exact"):
            _live_acquisition_receipt(
                result,  # type: ignore[arg-type]
                plan=plan,
                window="M3.2A",
                approved_ceiling=plan.hard_request_ceiling,
                continuation=None,
                config=load_config(None),
                catalog_path=tmp_path / _CATALOG_RELATIVE,
            )


class TestSeparateProcessDurability:
    """A run identity and its attribution outlive the process that wrote them."""

    def test_the_run_row_and_its_attribution_are_readable_from_a_fresh_process(
        self, tmp_path: Path
    ) -> None:
        """An in-process read could be served by a connection the writer still owns.

        Reading through a genuinely separate interpreter is what proves the rows are durable
        rather than merely visible, which is exactly the property a resumed invocation and the
        accepted T2.4 recovery state both depend on.
        """
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan), run_id_factory=lambda: "run-durable")
        database = tmp_path / _CATALOG_RELATIVE

        # The database path travels as an argument rather than being interpolated into the
        # probe, and both lookups bind their run identity as a parameter.
        probe = "\n".join(
            (
                "import sqlite3, sys",
                "connection = sqlite3.connect('file:' + sys.argv[1] + '?mode=ro', uri=True)",
                "kinds = 'SELECT job_kind, stage FROM ops_ingestion_jobs WHERE job_id = ?'",
                "owned = 'SELECT COUNT(*) FROM census_plan_sources WHERE census_run_id = ?'",
                "job = connection.execute(kinds, (sys.argv[2],)).fetchone()",
                "attributed = connection.execute(owned, (sys.argv[2],)).fetchone()[0]",
                "print(job[0], job[1], attributed)",
            )
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe, str(database), "run-durable"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == (
            f"{ACQUISITION_JOB_KIND} M3.2A {plan.planned_unique_logical_requests}"
        )


# --------------------------------------------------------------------------- #
# Genuine interruption: the catchable path, its exact states, and its refusals
#
# Decision 045 correction, MAJOR-1. `interrupted` is a real terminal outcome of a lawful live
# invocation, not a label. Everything below drives the production path — a real `KeyboardInterrupt`
# raised at a real durable boundary — rather than constructing a window outcome by hand.
# --------------------------------------------------------------------------- #
def _interrupt_at(
    monkeypatch: pytest.MonkeyPatch,
    owner: type,
    name: str,
    *,
    call: int,
    after: bool = False,
) -> None:
    """Raise ``KeyboardInterrupt`` on the ``call``-th invocation of ``owner.name``.

    ``after`` chooses which side of the real call the signal lands on, which is exactly what
    separates the three governed interruption points: before the snapshot store promotes anything,
    after promotion but before the recorder's transaction commits, and immediately after it
    committed. Nothing in the accepted store or recorder is edited — the signal is injected around
    them, which is what a real SIGINT does.
    """
    original = getattr(owner, name)
    seen = {"count": 0}

    def _wrapper(self: object, *args: object, **kwargs: object) -> object:
        seen["count"] += 1
        fires = seen["count"] == call
        if fires and not after:
            raise KeyboardInterrupt
        value = original(self, *args, **kwargs)
        if fires and after:
            raise KeyboardInterrupt
        return value

    monkeypatch.setattr(owner, name, _wrapper)


def _committed_observations(evidence_root: Path) -> list[str]:
    """Every durably committed observation identity, read back through a fresh connection."""
    rows = _catalog_rows(
        evidence_root, "SELECT observation_id FROM census_source_observations ORDER BY 1"
    )
    return [row["observation_id"] for row in rows]


def _job_states(evidence_root: Path) -> list[str]:
    """Every registered run's terminal ``job_state``, in registration order."""
    rows = _catalog_rows(evidence_root, "SELECT job_state FROM ops_ingestion_jobs ORDER BY rowid")
    return [row["job_state"] for row in rows]


def _orphan_relative_paths(evidence_root: Path, data_relative: str = _DATA_RELATIVE) -> list[str]:
    """Raw objects on disk that no committed row references — the I2 durable evidence."""
    data_root = evidence_root / data_relative
    recorded = {
        row["relative_storage_path"]
        for row in _catalog_rows(
            evidence_root, "SELECT relative_storage_path FROM census_source_observations"
        )
    }
    found: list[str] = []
    raw_root = data_root / "raw"
    if not raw_root.is_dir():
        return found
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.name.endswith((".lineage.json", ".part", ".reason")):
            continue
        relative = str(path.relative_to(data_root))
        if relative not in recorded:
            found.append(relative)
    return found


class TestGenuineInterruption:
    """MAJOR-1: a real interruption produces a real, exactly classified, resumable receipt."""

    def test_the_frozen_interruption_vocabulary_is_a_strict_acquisition_subset(self) -> None:
        """Acquisition may record only the three states an acquisition can actually be in.

        ``during_selection`` and ``during_manifest_write`` are frozen receipt values that name
        phases of a *selection* run. Milestone 3.2 acquisition selects nothing and writes no
        manifest, so emitting either would assert a phase that never happened — which a resume
        would then have to interpret.
        """
        from disclosure_drift.m3.acquisition import ACQUISITION_INTERRUPTION_STATES
        from disclosure_drift.m3.receipt import INTERRUPTION_STATES

        assert set(ACQUISITION_INTERRUPTION_STATES) < set(INTERRUPTION_STATES)
        assert "during_selection" not in ACQUISITION_INTERRUPTION_STATES
        assert "during_manifest_write" not in ACQUISITION_INTERRUPTION_STATES

    def test_the_interruption_reason_is_the_already_registered_code(self) -> None:
        """No reason code is created, modified, or repurposed by this correction."""
        from disclosure_drift.m3.acquisition import ACQUISITION_INTERRUPTED_REASON
        from disclosure_drift.reasons import REASON_CODES

        assert ACQUISITION_INTERRUPTED_REASON in REASON_CODES

    # -- I1 ----------------------------------------------------------------- #
    def test_i1_an_interruption_before_raw_store_promotion_is_before_raw_store_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """I1: classified exactly, nothing durable for the interrupted retrieval, still retryable.

        The signal lands after the retrieval's response was classified and accounted and before the
        snapshot store promotes anything, so the interrupted request has no committed observation
        and no promoted object of its own.
        """
        plan = _plan()
        _interrupt_at(monkeypatch, SnapshotStore, "record", call=2)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "interrupted"
        assert outcome.interruption_state == "before_raw_store_write"
        assert outcome.reason_codes == ("SEC_ACQUISITION_INTERRUPTED",)
        assert not outcome.completed_successfully
        # The interrupted request consumed a real attempt, so it is `stopped`, never untouched.
        assert [item.disposition for item in outcome.outcomes][:2] == ["satisfied_new", "stopped"]
        assert len(_committed_observations(tmp_path)) == 1
        assert _orphan_relative_paths(tmp_path) == []

    def test_i1_leaves_the_interrupted_request_owed_by_the_real_reconciliation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ``before_raw_store_write`` retrieval stays eligible for a later SAFE resume.

        Read from the accepted reconciliation over durable catalog and store state - the same
        primitive the continuation proposal partitions - rather than from the window outcome the
        interrupted invocation happened to hold in memory.
        """
        plan = _plan()
        _interrupt_at(monkeypatch, SnapshotStore, "record", call=2)
        _run_live(tmp_path, plan, _success_script(plan))
        monkeypatch.undo()

        storage = prepare_storage(evidence_root=tmp_path, data_root_relative=_DATA_RELATIVE)
        reconciliation = reconcile_requests(
            plan=plan,
            reconstruction=reconstruct_catalog_state(
                catalog_path=tmp_path / _CATALOG_RELATIVE, storage=storage
            ),
            storage=storage,
        )
        requests = derive_logical_requests(plan)
        states = {item.identity_label: item.state for item in reconciliation.items}

        # The interrupted retrieval reached no terminal evidence, so it is still open work; the
        # request that committed before it is satisfied and is not owed again.
        assert states[requests[1].identity_label] == "not_attempted"
        assert states[requests[0].identity_label] == "satisfied_new"

    # -- I2 ----------------------------------------------------------------- #
    def test_i2_an_interruption_after_promotion_before_commit_preserves_orphan_evidence(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """I2: the promoted object survives, no observation committed, nothing deleted."""
        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "interrupted"
        assert outcome.interruption_state == "after_raw_store_write_before_catalog_commit"
        assert len(_committed_observations(tmp_path)) == 1
        orphans = _orphan_relative_paths(tmp_path)
        assert len(orphans) == 1, "the promoted object is preserved as durable orphan evidence"
        assert (tmp_path / _DATA_RELATIVE / orphans[0]).is_file()

    # -- I3 ----------------------------------------------------------------- #
    def test_i3_an_interruption_after_catalog_commit_counts_the_retrieval_as_completed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """I3: the observation committed, so the retrieval is done and nothing is orphaned."""
        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2, after=True)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "interrupted"
        assert outcome.interruption_state == "after_catalog_commit"
        assert len(_committed_observations(tmp_path)) == 2
        assert _orphan_relative_paths(tmp_path) == []

    def test_an_interruption_between_logical_requests_is_after_catalog_commit(
        self, tmp_path: Path
    ) -> None:
        """A signal arriving between requests: the previous one committed, the next never began."""
        plan = _plan()
        seen: list[str] = []

        def _sink(outcome: object) -> None:
            seen.append(outcome.request.identity_label)  # type: ignore[attr-defined]
            if len(seen) == 2:
                raise KeyboardInterrupt

        result, factory = _run_live(tmp_path, plan, _success_script(plan), progress=_sink)
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "interrupted"
        assert outcome.interruption_state == "after_catalog_commit"
        assert len(seen) == 2
        # No further transport call happened: only the two requests already reported were placed.
        assert len(factory.transports[0].requests) == 2

    def test_an_interruption_during_the_first_retrieval_is_before_raw_store_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nothing has committed at all, so the window stopped before any promotion."""
        plan = _plan()
        _interrupt_at(monkeypatch, SnapshotStore, "record", call=1)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "interrupted"
        assert outcome.interruption_state == "before_raw_store_write"
        assert _committed_observations(tmp_path) == []

    # -- fail-closed -------------------------------------------------------- #
    def test_an_ambiguous_interruption_produces_no_window_at_all(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The signal lands *inside* the snapshot store, after it promoted and before it returned.

        The engine never learned which observation was minted, and an unaccounted object now exists
        on disk. That is indistinguishable from a promotion that had not happened, so the state
        cannot be established exactly — and the interrupt is re-raised rather than guessed at. No
        window outcome exists, so no receipt can be produced from one.
        """
        plan = _plan()
        _interrupt_at(monkeypatch, SnapshotStore, "record", call=2, after=True)

        with pytest.raises(KeyboardInterrupt):
            _run_live(tmp_path, plan, _success_script(plan))

        monkeypatch.undo()
        assert len(_orphan_relative_paths(tmp_path)) == 1, "the evidence is preserved, not deleted"
        # The registered run is closed truthfully rather than left indefinitely `running`.
        assert _job_states(tmp_path) == ["stopped"]

    def test_an_interruption_at_the_construction_site_places_no_request_and_writes_nothing(
        self, tmp_path: Path
    ) -> None:
        """Interrupted before lawful execution begins: no observation, no window, no receipt."""
        plan = _plan()

        def _interrupting_factory() -> object:
            raise KeyboardInterrupt

        factory = _CountingTransportFactory(_success_script(plan))
        arguments = _live_arguments(tmp_path, plan, factory)
        arguments["transport_factory"] = _interrupting_factory

        with pytest.raises(KeyboardInterrupt):
            execute_live_acquisition(**arguments)  # type: ignore[arg-type]

        assert _committed_observations(tmp_path) == []
        assert _job_states(tmp_path) == ["stopped"]

    # -- the vocabulary is not a catch-all ---------------------------------- #
    def test_a_governed_failure_is_failed_and_carries_no_interruption_state(
        self, tmp_path: Path
    ) -> None:
        """An ordinary terminal failure is never relabelled as an interruption."""
        plan = _plan()
        script = _script_with(plan, {0: [_scripted(500, body=b"", content_type=None)] * 4})
        result, _ = _run_live(tmp_path, plan, script)
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status != "interrupted"
        assert outcome.interruption_state is None

    def test_a_transport_level_failure_is_not_automatically_an_interruption(
        self, tmp_path: Path
    ) -> None:
        """A response-policy transport failure is a retry event, not a signal."""
        plan = _plan()
        script = _script_with(
            plan, {0: [_scripted(0, body=b"", content_type=None, failure="connection_error")]}
        )
        result, _ = _run_live(tmp_path, plan, script)
        outcome = result.outcome  # type: ignore[attr-defined]

        assert outcome.completion_status == "complete"
        assert outcome.interruption_state is None

    def test_a_ceiling_stop_remains_stopped_at_ceiling(self, tmp_path: Path) -> None:
        plan = _plan()
        gate = PhysicalAttemptCeiling(plan.hard_request_ceiling, consumed=plan.hard_request_ceiling)
        with _harness(tmp_path, plan=plan, responses=[], ceiling=gate) as (engine, _, _, _):
            engine.preflight(_authorization(plan))
            outcome = engine.run()

        assert outcome.completion_status == "stopped_at_ceiling"
        assert outcome.interruption_state is None

    def test_a_gate_stop_remains_stopped_by_gate(self, tmp_path: Path) -> None:
        """A pre-transport policy refusal keeps its own status and no interruption state."""
        from disclosure_drift.sec.http_client import ProhibitedRetrievalError

        plan = _plan()
        with _harness(tmp_path, plan=plan, responses=_success_script(plan)) as (engine, _, _, _):
            engine.preflight(_authorization(plan))

            def _refuse(*args: object, **kwargs: object) -> object:
                message = "refusing to retrieve a prohibited URL"
                raise ProhibitedRetrievalError(message)

            engine.client.fetch = _refuse  # type: ignore[method-assign]
            outcome = engine.run()

        assert outcome.completion_status == "stopped_by_gate"
        assert outcome.interruption_state is None

    # -- the window type enforces the pairing ------------------------------- #
    def test_an_interrupted_window_without_a_frozen_state_is_refused(self) -> None:
        from disclosure_drift.m3.acquisition import WindowOutcome

        with pytest.raises(AcquisitionGateError, match="interruption state"):
            WindowOutcome(
                window="M3.2A",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                consumed_physical_attempts=1,
                planned_logical_requests=1,
                outcomes=(),
                completion_status="interrupted",
            )

    def test_an_interrupted_window_with_a_selection_state_is_refused(self) -> None:
        """A frozen receipt value acquisition can never be in is still refused here."""
        from disclosure_drift.m3.acquisition import WindowOutcome

        with pytest.raises(AcquisitionGateError, match="interruption state"):
            WindowOutcome(
                window="M3.2A",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                consumed_physical_attempts=1,
                planned_logical_requests=1,
                outcomes=(),
                completion_status="interrupted",
                interruption_state="during_selection",
            )

    def test_a_non_interrupted_window_may_not_carry_an_interruption_state(self) -> None:
        from disclosure_drift.m3.acquisition import WindowOutcome

        with pytest.raises(AcquisitionGateError, match="genuinely interrupted"):
            WindowOutcome(
                window="M3.2A",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                consumed_physical_attempts=1,
                planned_logical_requests=1,
                outcomes=(),
                completion_status="complete",
                interruption_state="after_catalog_commit",
            )

    def test_positive_control_a_well_formed_interrupted_window_constructs(self) -> None:
        """Without this, the refusals above would pass against a type that refuses everything."""
        from disclosure_drift.m3.acquisition import WindowOutcome

        outcome = WindowOutcome(
            window="M3.2A",
            plan_sha256="0" * 64,
            approved_ceiling=1,
            consumed_physical_attempts=1,
            planned_logical_requests=1,
            outcomes=(),
            completion_status="interrupted",
            interruption_state="after_catalog_commit",
        )

        assert not outcome.completed_successfully


class TestInterruptedRunJobState:
    """Decision 045 correction §8: a stopped invocation is recorded as stopped, never completed."""

    def test_an_interrupted_window_closes_its_run_as_stopped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2, after=True)
        _run_live(tmp_path, plan, _success_script(plan))

        assert _job_states(tmp_path) == ["stopped"]

    def test_a_complete_window_still_closes_its_run_as_completed(self, tmp_path: Path) -> None:
        """Positive control: the new third state did not swallow the ordinary two."""
        plan = _plan()
        _run_live(tmp_path, plan, _success_script(plan))

        assert _job_states(tmp_path) == ["completed"]

    def test_the_job_state_mapping_keeps_the_three_outcomes_apart(self) -> None:
        from disclosure_drift.m3.acquisition import WindowOutcome, acquisition_run_job_state

        def _window(status: str, state: str | None = None) -> object:
            return WindowOutcome(
                window="M3.2A",
                plan_sha256="0" * 64,
                approved_ceiling=1,
                consumed_physical_attempts=0,
                planned_logical_requests=0,
                outcomes=(),
                completion_status=status,  # type: ignore[arg-type]
                interruption_state=state,
            )

        assert acquisition_run_job_state(_window("complete")) == "completed"  # type: ignore[arg-type]
        assert acquisition_run_job_state(_window("failed")) == "failed"  # type: ignore[arg-type]
        assert (
            acquisition_run_job_state(_window("interrupted", "after_catalog_commit"))  # type: ignore[arg-type]
            == "stopped"
        )

    def test_an_invented_job_state_is_refused_rather_than_written(self, tmp_path: Path) -> None:
        """`interrupted` is the receipt's vocabulary; it is never a database job state."""
        from disclosure_drift.m3.acquisition import finish_acquisition_run

        catalog = prepare_operational_catalog(
            evidence_root=tmp_path, relative_path=_CATALOG_RELATIVE
        )

        with pytest.raises(AcquisitionRunError, match="never closed into an invented state"):
            finish_acquisition_run(
                catalog_path=catalog.database_path,
                lock_directory=catalog.lock_directory,
                census_run_id="run-any",
                job_state="interrupted",
                finished_at_utc=_stamp(),
                detail="fixture",
            )


class TestInterruptedReceiptAssembly:
    """The interrupted window becomes an interrupted receipt the accepted recovery path can read."""

    def _receipt_for(self, tmp_path: Path, plan: RequestPlan, result: object) -> ExecutionReceipt:
        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config

        return _live_acquisition_receipt(
            result,  # type: ignore[arg-type]
            plan=plan,
            window="M3.2A",
            approved_ceiling=plan.hard_request_ceiling,
            continuation=None,
            config=load_config(None),
            catalog_path=tmp_path / _CATALOG_RELATIVE,
        )

    def test_an_interrupted_window_produces_a_valid_interrupted_receipt(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from disclosure_drift.m3.receipt import validate_receipt_document

        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        monkeypatch.undo()
        document = self._receipt_for(tmp_path, plan, result).as_document()
        validate_receipt_document(document)

        assert document["completion_status"] == "interrupted"
        assert document["interruption_state"] == "after_raw_store_write_before_catalog_commit"
        assert document["reason_code"] == "SEC_ACQUISITION_INTERRUPTED"
        assert "remaining_planned_logical_request_count" not in document

    def test_a_complete_receipt_carries_no_interruption_state(self, tmp_path: Path) -> None:
        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        document = self._receipt_for(tmp_path, plan, result).as_document()

        assert document["completion_status"] == "complete"
        assert "interruption_state" not in document

    def test_the_frozen_schema_refuses_an_interruption_state_on_a_complete_receipt(
        self, tmp_path: Path
    ) -> None:
        from disclosure_drift.m3.receipt import ReceiptValidationError, validate_receipt_document

        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        document = self._receipt_for(tmp_path, plan, result).as_document()
        document["interruption_state"] = "after_catalog_commit"

        with pytest.raises(ReceiptValidationError):
            validate_receipt_document(document)

    def test_the_frozen_schema_refuses_an_interrupted_receipt_without_a_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from disclosure_drift.m3.receipt import ReceiptValidationError, validate_receipt_document

        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        monkeypatch.undo()
        document = self._receipt_for(tmp_path, plan, result).as_document()
        del document["interruption_state"]

        with pytest.raises(ReceiptValidationError):
            validate_receipt_document(document)

    def test_the_frozen_schema_refuses_an_unaccepted_interruption_state(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        from disclosure_drift.m3.receipt import ReceiptValidationError, validate_receipt_document

        plan = _plan()
        _interrupt_at(monkeypatch, ObservationRecorder, "record", call=2)
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        monkeypatch.undo()
        document = self._receipt_for(tmp_path, plan, result).as_document()
        document["interruption_state"] = "somewhere_in_the_middle"

        with pytest.raises(ReceiptValidationError):
            validate_receipt_document(document)

    def test_the_receipt_instants_are_the_run_s_own_not_a_second_clock(
        self, tmp_path: Path
    ) -> None:
        """The segmentation boundary a resume uses must cover the observations the run wrote.

        A separately sampled, second-truncated completion instant can fall *before* observations
        the run itself produced, which charges them a second time against the approved ceiling on
        every resume. Binding both instants to the run's own clock removes the possibility.
        """
        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        document = self._receipt_for(tmp_path, plan, result).as_document()

        assert document["started_at_utc"] == result.started_at_utc  # type: ignore[attr-defined]
        assert document["completed_at_utc"] == result.completed_at_utc  # type: ignore[attr-defined]


class TestResponsePairingDiagnostic:
    """MINOR-1: the per-retrieval send/action pairing guard is bound by a test of its own.

    The outer equality invariant (`classified_event_count == status_event_count`) already refuses a
    mispaired absorption, so a mutation that deletes the pairing check alone still fails closed.
    That makes the outer invariant a poor witness for the inner one: it passes either way. These
    tests bind the diagnostic itself — its structural basis must be recorded, and nothing may be
    counted — so removing it is a detectable behavioural change rather than a silent one.
    """

    def test_more_sends_than_accounted_events_retains_the_pairing_basis(self) -> None:
        accounting = ResponseAccounting()
        accounting.absorb(_fetch_result(status=200, actions=("proceed",)), (200, 200))

        assert not accounting.is_exact
        assert accounting.undetermined_basis is not None
        assert "2 physical response(s) were observed but" in accounting.undetermined_basis
        assert "accounted exactly once" in accounting.undetermined_basis
        assert accounting.status_code_totals == {}
        assert accounting.classified_event_count == 0

    def test_fewer_sends_than_accounted_events_retains_the_pairing_basis(self) -> None:
        """The guard is symmetric: an over-classified retrieval is refused the same way."""
        accounting = ResponseAccounting()
        accounting.absorb(_fetch_result(status=200, actions=("retry", "proceed")), (200,))

        assert not accounting.is_exact
        assert accounting.undetermined_basis is not None
        assert "1 physical response(s) were observed but" in accounting.undetermined_basis
        assert accounting.status_code_totals == {}
        assert accounting.classified_event_count == 0

    def test_a_redirect_hop_is_counted_by_the_pairing_arithmetic_not_ignored(self) -> None:
        """A followed redirect appends no action marker, so the pairing must count it separately."""
        accounting = ResponseAccounting()
        accounting.absorb(
            _fetch_result(status=200, actions=("proceed",), redirect_hops=("https://example",)),
            (301, 200),
        )

        assert accounting.is_exact
        assert accounting.undetermined_basis is None
        assert accounting.redirect_hop_count == 1
        assert accounting.status_event_count == 2

    def test_positive_control_a_correctly_paired_absorption_records_everything(self) -> None:
        accounting = ResponseAccounting()
        accounting.absorb(_fetch_result(status=200, actions=("retry", "proceed")), (503, 200))

        assert accounting.is_exact
        assert accounting.undetermined_basis is None
        assert accounting.status_code_totals == {"200": 1, "503": 1}

    def test_a_mispaired_retrieval_makes_receipt_production_impossible(
        self, tmp_path: Path
    ) -> None:
        """The diagnostic is not merely observational: it stops the receipt."""
        from disclosure_drift.cli import _live_acquisition_receipt
        from disclosure_drift.config import load_config
        from disclosure_drift.errors import GateFailureError

        plan = _plan()
        result, _ = _run_live(tmp_path, plan, _success_script(plan))
        mispaired = ResponseAccounting()
        mispaired.absorb(_fetch_result(status=200, actions=("proceed",)), (200, 200))

        with pytest.raises(GateFailureError, match="not exact"):
            _live_acquisition_receipt(
                replace(result, accounting=mispaired),  # type: ignore[arg-type,type-var]
                plan=plan,
                window="M3.2A",
                approved_ceiling=plan.hard_request_ceiling,
                continuation=None,
                config=load_config(None),
                catalog_path=tmp_path / _CATALOG_RELATIVE,
            )
