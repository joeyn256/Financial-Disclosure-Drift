"""Milestone 3.2 stage T2.4 — continuation proposal and the explicit recovery applier.

Decision 040 §§2–7 fix what these tests prove: the continuation proposal is deterministic,
read-only, and bound to the predecessor receipt chain, the exact plan hash, window, and approved
ceiling; cumulative attempt accounting carries the chain forward, counts post-receipt committed
attempts exactly once, charges at most one identifiable receiptless in-flight request at its full
registered ``A_reachable``, and collapses every ambiguity to ``UNDETERMINED`` with continuation
prohibited; and the recovery applier is inert — never invoked by any detection path, refusing
unknown, mismatched, stale, multi-action, and ``UNDETERMINED`` requests, applying exactly one
accepted primitive per explicit invocation, and requiring a fresh read-only inspection afterward.

Every test is offline: the suite-wide autouse socket guard makes that structural, and every
"transport" is a scripted in-memory object the test owns.
"""

from __future__ import annotations

import hashlib
import inspect as inspect_module
import json
import sqlite3
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Final

import pytest

from disclosure_drift.errors import CatalogWriteError, RawObjectIntegrityError
from disclosure_drift.m3 import acquisition as acquisition_module
from disclosure_drift.m3.acquisition import (
    RECOVERY_ACTIONS,
    AcquisitionEngine,
    AcquisitionGateError,
    LiveOperationAuthorization,
    RecoveryActionResult,
    RepairRefusedError,
    StorageBinding,
    apply_recovery_action,
    conditional_validators,
    derive_logical_requests,
    prepare_operational_catalog,
    prepare_storage,
    propose_continuation,
    rebuild_projection_eligibility,
    reconcile_requests,
    reconstruct_catalog_state,
    verified_reusable_predecessor,
)
from disclosure_drift.m3.receipt import ExecutionReceipt, write_receipt
from disclosure_drift.m3.recovery import inspect_recovery_state
from disclosure_drift.m3.request_plan import (
    RequestPlan,
    build_m3_2a_request_plan,
    derive_a_reachable,
)
from disclosure_drift.sec.http_client import RetrievalPolicy, SecClient
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    open_recovery_state,
    rebuild_audit_projection,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.raw_store import RawStore
from disclosure_drift.sec.request_ceiling import PhysicalAttemptCeiling
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import SecRequest, TransportResponse
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction

_AGENT: Final = "Disclosure Drift Test Harness (offline-fixture@example.invalid)"
_CATALOG_RELATIVE: Final = "catalogs/m3_2a_operational.sqlite3"
_DATA_RELATIVE: Final = "runs/m3_2a/data"
_PROJECTION: Final = "census_source_observations.jsonl"

#: The lawful pre-registered ingestion-run identity every mutating recovery action supplies.
#: Tests may create this fixture row (Decision 041 §7); the applier itself never creates one.
_RUN: Final = "m3-2a-fixture-run-0001"

#: A valid 32-hex spool nonce, exactly the shape ``SnapshotStore`` writes.
_NONCE: Final = "deadbeef" * 4
_NONCE_B: Final = "feedface" * 4
_NONCE_C: Final = "cafef00d" * 4
_SCENARIO: Final = "t2_4_recovery_action"

#: Engine observation stamps on either side of the fixture receipt's completion instant.
_PRE_RECEIPT_STAMP: Final = "2026-08-01T12:00:05Z"
_POST_RECEIPT_STAMP: Final = "2026-08-04T00:00:00Z"
_RECEIPT_COMPLETED: Final = "2026-08-01T12:00:09Z"


# --------------------------------------------------------------------------- #
# Offline seams
# --------------------------------------------------------------------------- #
class _ScriptedTransport:
    """Replays scripted responses and records requests. Opens no socket."""

    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[SecRequest] = []

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        if not self._responses:
            message = "the scripted transport was exhausted"
            raise AssertionError(message)
        response = self._responses.pop(0)
        if response.final_url == "":
            response = TransportResponse(
                status=response.status,
                headers=response.headers,
                final_url=request.url,
                body=response.body,
                chunks=response.chunks,
                failure=response.failure,
            )
        return response

    def close(self) -> None:
        return None


class _FrozenClock:
    def __init__(self) -> None:
        self.now = 1_000.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _zip_bytes() -> bytes:
    import io
    import zipfile

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        info = zipfile.ZipInfo("CIK0000000001.json", date_time=(1980, 1, 1, 0, 0, 0))
        info.create_system = 3
        info.external_attr = 0o600 << 16
        archive.writestr(info, b'{"cik":1}')
    return buffer.getvalue()


def _scripted(
    status: int = 200,
    *,
    body: bytes = b'{"ok":1}',
    content_type: str | None = "application/json",
    headers: Mapping[str, str] | None = None,
) -> TransportResponse:
    merged = dict(headers or {})
    if content_type is not None:
        merged.setdefault("Content-Type", content_type)
    return TransportResponse(status=status, headers=merged, final_url="", body=body)


def _success_for(source_id: str, *, etag: str | None = None) -> TransportResponse:
    expected = SOURCES[source_id].expected_content
    headers = {"ETag": etag} if etag else {}
    if expected == "zip":
        return _scripted(body=_zip_bytes(), content_type="application/zip", headers=headers)
    if expected == "html":
        return _scripted(
            body=b"<html><body>calendar</body></html>",
            content_type="text/html",
            headers=headers,
        )
    if expected == "text":
        return _scripted(
            body=b"CIK|Company Name\n1|SYNTHETIC\n", content_type="text/plain", headers=headers
        )
    return _scripted(headers=headers)


def _plan() -> RequestPlan:
    """Five singletons plus two quarterly instances; ceiling 53."""
    return build_m3_2a_request_plan(
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2010, 6, 30),
        as_of_date=date(2010, 7, 1),
        include_open_quarter=False,
        calendar_year=2010,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
    )


def _authorization(plan: RequestPlan) -> LiveOperationAuthorization:
    return LiveOperationAuthorization(
        window="M3.2A",
        plan_sha256=plan.request_plan_sha256,
        approved_ceiling=plan.hard_request_ceiling,
        authorization_reference="OWNER_TEST_FIXTURE_AUTHORIZATION",
    )


# --------------------------------------------------------------------------- #
# Harness: one catalog and storage binding across engine runs and inspections
# --------------------------------------------------------------------------- #
class _Harness:
    def __init__(self, evidence_root: Path) -> None:
        self.plan = _plan()
        self.preparation = prepare_operational_catalog(
            evidence_root=evidence_root, relative_path=_CATALOG_RELATIVE
        )
        self.storage: StorageBinding = prepare_storage(
            evidence_root=evidence_root, data_root_relative=_DATA_RELATIVE
        )
        self.writer = CatalogWriter(self.preparation.database_path, self.preparation.lock_directory)
        self.writer.__enter__()
        self._writer_open = True
        with transaction(self.writer.connection) as connection:
            connection.execute(
                "INSERT INTO ops_ingestion_jobs "
                "(job_id, job_kind, job_state, stage, started_at_utc) "
                "VALUES (?, 'm3_2a_acquisition', 'stopped', 'M3.2A', '2026-08-01T12:00:00Z')",
                (_RUN,),
            )

    @property
    def catalog_path(self) -> Path:
        return self.preparation.database_path

    def run(
        self,
        responses: Sequence[TransportResponse],
        *,
        headroom: int | None = None,
        stamp: str = _PRE_RECEIPT_STAMP,
    ) -> object:
        gate = PhysicalAttemptCeiling(
            self.plan.hard_request_ceiling,
            consumed=(0 if headroom is None else self.plan.hard_request_ceiling - headroom),
        )
        clock = _FrozenClock()
        transport = _ScriptedTransport(responses)
        limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
        client = SecClient(
            transport, _AGENT, limiter, RetrievalPolicy(), sleeper=clock.sleep, ceiling=gate
        )
        recorder = ObservationRecorder(writer=self.writer, tree=self.storage.tree)
        engine = AcquisitionEngine(
            plan=self.plan,
            window="M3.2A",
            ceiling=gate,
            client=client,
            storage=self.storage,
            recorder=recorder,
            clock=lambda: stamp,
        )
        engine.preflight(_authorization(self.plan))
        return engine.run()

    def flush_projection(self) -> None:
        ObservationRecorder(writer=self.writer, tree=self.storage.tree).flush_projection()

    def release(self) -> None:
        """Release the single-writer lease so the applier can take its own."""
        if self._writer_open:
            self.writer.__exit__(None, None, None)
            self._writer_open = False

    def close(self) -> None:
        self.release()


@contextmanager
def _harness(tmp_path: Path) -> Iterator[_Harness]:
    harness = _Harness(tmp_path / "evidence")
    try:
        yield harness
    finally:
        harness.close()


def _requests(plan: RequestPlan) -> tuple[str, ...]:
    return tuple(request.source_id for request in derive_logical_requests(plan))


def _success_script(plan: RequestPlan, *, etag: str | None = None) -> list[TransportResponse]:
    return [_success_for(source_id, etag=etag) for source_id in _requests(plan)]


# --------------------------------------------------------------------------- #
# Receipts
# --------------------------------------------------------------------------- #
def _receipt(plan: RequestPlan, **overrides: object) -> ExecutionReceipt:
    """A live, interrupted receipt bound to the fixture plan and its exact ceiling."""
    fields: dict[str, object] = {
        "command_name": "m3 acquire",
        "command_version": "m3.2a/1.0",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0013_m23_manifest_lifecycle_guards",
        "started_at_utc": "2026-08-01T12:00:00Z",
        "completed_at_utc": _RECEIPT_COMPLETED,
        "elapsed_seconds": 9.0,
        "source_registry_version": "m2.2-source-registry/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "parser_versions": {"company-tickers": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": plan.request_plan_id,
        "request_plan_sha256": plan.request_plan_sha256,
        "approved_request_ceiling": plan.hard_request_ceiling,
        "planned_logical_request_count": plan.planned_unique_logical_requests,
        "maximum_physical_attempt_count": plan.hard_request_ceiling,
        "planned_per_route": {
            "sec_bulk_submissions": 1,
            "sec_company_tickers_exchange": 1,
            "sec_company_tickers": 1,
            "sec_sic_code_list": 1,
            "sec_edgar_filing_calendar": 1,
            "sec_full_index_company": 2,
        },
        "actual_logical_request_count": 3,
        "actual_physical_attempt_count": 3,
        "actual_per_route": {
            "sec_bulk_submissions": {"logical_request_count": 3, "physical_attempt_count": 3},
        },
        "response_classification_totals": {
            "proceed": 3,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": 3},
        "raw_object_count": 3,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "completion_status": "interrupted",
        "reason_code": "SEC_ACQUISITION_INTERRUPTED",
        "reason_detail": "the acquisition was interrupted before completion.",
        "interruption_state": "after_catalog_commit",
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)  # type: ignore[arg-type]


def _write_receipts(tmp_path: Path, *receipts: ExecutionReceipt) -> Path:
    checkout = tmp_path / "checkout"
    checkout.mkdir(exist_ok=True)
    evidence = tmp_path / "receipt-evidence"
    head: Path | None = None
    for item in receipts:
        head = write_receipt(item, evidence_root=evidence, repository_root=checkout)
    assert head is not None
    return head


def _propose(
    harness: _Harness,
    head: Path,
    *,
    window: str = "M3.2A",
    ceiling: int | None = None,
) -> object:
    return propose_continuation(
        plan=harness.plan,
        receipt_chain_head=head,
        catalog_path=harness.catalog_path,
        storage=harness.storage,
        window=window,
        approved_ceiling=(harness.plan.hard_request_ceiling if ceiling is None else ceiling),
    )


def _tree_digest(harness: _Harness) -> str:
    """One digest over the catalog bytes and every data-root file, for no-mutation proofs."""
    digest = hashlib.sha256()
    digest.update(harness.catalog_path.read_bytes())
    for path in sorted(harness.storage.data_root.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(harness.storage.data_root)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


# =========================================================================== #
# Continuation proposal — bindings, accounting, and refusals
# =========================================================================== #
class TestContinuationProposal:
    def test_a_clean_interrupted_run_yields_a_permitted_proposal(self, tmp_path: Path) -> None:
        """Kill point 6: safe resume with the carried count exact and satisfied excluded."""
        with _harness(tmp_path) as harness:
            outcome = harness.run(_success_script(harness.plan), headroom=3)
            assert outcome.completion_status == "stopped_at_ceiling"
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.permitted is True
        assert proposal.determination == "SAFE"
        assert proposal.refusal_reasons == ()
        assert proposal.accounting.chain_consumed == 3
        assert proposal.accounting.post_receipt_attempts == 0
        assert proposal.accounting.in_flight_charge == 0
        assert proposal.accounting.cumulative_consumed == 3
        assert proposal.remaining_headroom == harness.plan.hard_request_ceiling - 3
        assert len(proposal.already_satisfied_excluded) == 3
        assert len(proposal.remaining) == 4
        satisfied = set(proposal.already_satisfied_excluded)
        remaining = {request.identity_label for request in proposal.remaining}
        assert satisfied.isdisjoint(remaining), "no satisfied request is ever replayed"
        worst = sum(
            acquisition_module.derive_a_reachable(SOURCES[request.source_id])
            for request in proposal.remaining
        )
        assert proposal.worst_case_remaining_attempts == worst
        assert proposal.fits is True
        assert proposal.predecessor_receipt_id == proposal.receipt_chain[0]
        totals = proposal.reconciliation.totals
        assert totals["not_attempted"] == 4, (
            "requests past the exhausted headroom were never attempted and never reached "
            "a transport"
        )
        engine_totals = dict(outcome.classification_totals)
        assert engine_totals["not_attempted"] == 4 and engine_totals["stopped"] == 0, (
            "the engine stops before, never after: exhausted headroom means the request "
            "was never started, not started-then-stopped"
        )

    def test_the_proposal_is_deterministic_and_read_only(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            before = _tree_digest(harness)
            first = _propose(harness, head)
            second = _propose(harness, head)
            after = _tree_digest(harness)

        assert before == after, "a proposal mutates nothing"
        first_bytes = json.dumps(first.reconciliation.as_record(), sort_keys=True)
        second_bytes = json.dumps(second.reconciliation.as_record(), sort_keys=True)
        assert first_bytes == second_bytes
        assert first.accounting == second.accounting
        assert [item.identity_label for item in first.remaining] == [
            item.identity_label for item in second.remaining
        ]

    def test_a_receiptless_in_flight_request_is_charged_at_full_a_reachable(
        self, tmp_path: Path
    ) -> None:
        """Kill point 2: a partial spool marks receiptless activity; the first unresolved
        request is charged its whole registered bound, and it still remains to be done."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            staging = harness.storage.tree.staging
            staging.mkdir(parents=True, exist_ok=True)
            (staging / f"sec_sic_code_list-{_NONCE}.part").write_bytes(b"partial")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        expected_route = _requests(harness.plan)[3]
        assert expected_route == "sec_sic_code_list", (
            "the spool's parsed route and the first unresolved planned request agree"
        )
        expected_charge = acquisition_module.derive_a_reachable(SOURCES[expected_route])
        assert proposal.accounting.in_flight_charge == expected_charge
        assert proposal.accounting.in_flight_request_identity is not None
        assert proposal.accounting.cumulative_consumed == 3 + expected_charge
        assert proposal.accounting.undetermined is False
        charged = proposal.accounting.in_flight_request_identity
        assert charged in {request.request_identity for request in proposal.remaining}, (
            "the charged request was never satisfied, so it remains to be re-attempted"
        )

    def test_post_receipt_rows_are_counted_once_with_no_in_flight_charge(
        self, tmp_path: Path
    ) -> None:
        """Kill point 4's complete case: rows after the final receipt account for themselves."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), stamp=_POST_RECEIPT_STAMP)
            harness.flush_projection()
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=0,
                    actual_physical_attempt_count=0,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": 0,
                            "physical_attempt_count": 0,
                        },
                    },
                    response_classification_totals={
                        "proceed": 0,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": 0},
                    raw_object_count=0,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.accounting.chain_consumed == 0
        assert proposal.accounting.post_receipt_attempts == 7
        assert proposal.accounting.in_flight_charge == 0
        assert proposal.accounting.undetermined is False
        assert proposal.accounting.cumulative_consumed == 7
        assert proposal.remaining == ()
        assert len(proposal.already_satisfied_excluded) == 7
        assert proposal.permitted is True

    def test_an_unresolvable_chain_is_undetermined_and_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    recovery_predecessor_receipt_id="0" * 64,
                    consumed_request_count_carried_forward=1,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.permitted is False
        assert proposal.determination == "UNDETERMINED"
        assert any("UNDETERMINED" in reason for reason in proposal.refusal_reasons)

    def test_a_row_without_its_object_is_undetermined(self, tmp_path: Path) -> None:
        """Kill point 5: it cannot be established what persisted, so nothing continues."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            stored = next(
                observation
                for observation in reconstruction.observations
                if observation.relative_storage_path
            )
            (harness.storage.data_root / str(stored.relative_storage_path)).unlink()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.determination == "UNDETERMINED"
        assert proposal.permitted is False

    def test_an_ambiguous_boundary_instant_is_undetermined(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3, stamp=_RECEIPT_COMPLETED)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert proposal.permitted is False
        assert proposal.determination == "UNDETERMINED"
        assert "attributed uniquely" in proposal.accounting.basis

    def test_material_disagreement_between_rows_and_chain_is_undetermined(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=1,
                    actual_physical_attempt_count=1,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": 1,
                            "physical_attempt_count": 1,
                        },
                    },
                    response_classification_totals={
                        "proceed": 1,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": 1},
                    raw_object_count=1,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "disagrees materially" in proposal.accounting.basis
        assert proposal.permitted is False

    def test_zero_headroom_with_remaining_work_refuses_continuation(self, tmp_path: Path) -> None:
        """Kill point 8: the ceiling is never raised; the proposal stops for re-planning."""
        plan = _plan()
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            ceiling = plan.hard_request_ceiling
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=ceiling,
                    actual_physical_attempt_count=ceiling,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": ceiling,
                            "physical_attempt_count": ceiling,
                        },
                    },
                    response_classification_totals={
                        "proceed": ceiling,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": ceiling},
                    raw_object_count=3,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.remaining_headroom == 0
        assert proposal.fits is False
        assert proposal.permitted is False
        assert any("never raised" in reason for reason in proposal.refusal_reasons)

    def test_the_gate_itself_refuses_a_resume_past_its_ceiling(self) -> None:
        """The accepted constructor is the last line: consumed can never exceed approved."""
        with pytest.raises(ValueError, match="may not begin past its own ceiling"):
            PhysicalAttemptCeiling(53, consumed=60)
        gate = PhysicalAttemptCeiling(1, consumed=1)
        with pytest.raises(Exception, match="refused and never placed"):
            gate.before_attempt()
        with pytest.raises(AttributeError):
            gate.approved_ceiling = 100  # type: ignore[misc]

    def test_a_non_live_predecessor_is_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            rehearsal = ExecutionReceipt(
                command_name="m3 rehearse",
                command_version="m3.1a/1.0",
                phase="M3.1A",
                invocation_mode="rehearsal",
                configuration_fingerprint="a" * 64,
                migration_chain_head="0013_m23_manifest_lifecycle_guards",
                started_at_utc="2026-08-01T12:00:00Z",
                completed_at_utc=_RECEIPT_COMPLETED,
                elapsed_seconds=4.0,
                actual_logical_request_count=0,
                actual_physical_attempt_count=0,
                completion_status="interrupted",
                reason_code="SEC_ACQUISITION_INTERRUPTED",
                reason_detail="the rehearsal was interrupted.",
                interruption_state="after_catalog_commit",
                schema_drift_outcome="none",
                schema_drift_event_count=0,
                rehearsal_evidence_reference="m3-1a-rehearsal-report-0001",
            )
            head = _write_receipts(tmp_path, rehearsal)
            proposal = _propose(harness, head)

        assert proposal.permitted is False
        assert any("live" in reason for reason in proposal.refusal_reasons)

    def test_a_ceiling_argument_mismatch_is_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head, ceiling=harness.plan.hard_request_ceiling + 1)

        assert proposal.permitted is False
        assert any("never reinterpreted" in reason for reason in proposal.refusal_reasons)

    def test_an_unknown_window_is_a_caller_error(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            with pytest.raises(AcquisitionGateError, match="not one of the accepted"):
                _propose(harness, head, window="M9.9Z")

    def test_remaining_requests_carry_no_validators_without_a_verified_predecessor(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan, etag='"v1"'), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            satisfied_route = _requests(harness.plan)[1]
            validators = conditional_validators(reconstruction, satisfied_route)

        for request in proposal.remaining:
            assert request.etag is None
            assert request.last_modified is None
        assert validators == ('"v1"', None), (
            "a satisfied identity's verified predecessor supplies lawful validators"
        )


# =========================================================================== #
# The explicit recovery applier
# =========================================================================== #
def _delete_row(harness: _Harness, observation_id: str) -> None:
    """Simulate a crash between promotion and commit by removing the committed row."""
    connection = harness.writer.connection
    connection.execute(
        "DELETE FROM census_observation_reasons WHERE observation_id = ?", (observation_id,)
    )
    connection.execute(
        "DELETE FROM census_archive_members WHERE observation_id = ?", (observation_id,)
    )
    connection.execute(
        "DELETE FROM census_source_observations WHERE observation_id = ?", (observation_id,)
    )
    connection.commit()
    rebuild_audit_projection(connection, harness.storage.tree.audit / _PROJECTION)


def _singleton_observation_id(harness: _Harness, source_id: str) -> tuple[str, str]:
    reconstruction = reconstruct_catalog_state(
        catalog_path=harness.catalog_path, storage=harness.storage
    )
    observation = next(
        item
        for item in reconstruction.observations
        if item.source_id == source_id and item.relative_storage_path
    )
    return observation.observation_id, str(observation.relative_storage_path)


def _apply(
    harness: _Harness,
    head: Path,
    action: str,
    target: str,
    *,
    census_run_id: str = _RUN,
    network_disabled: bool = True,
) -> RecoveryActionResult:
    # `network_disabled=True` is a statement of fact about this harness, not a convenience: every
    # test here runs entirely offline against a temporary evidence root, so the tracked switches
    # are genuinely off. The projection rebuild's eligibility reads it; the other three ignore it.
    return apply_recovery_action(
        action=action,
        target=target,
        plan=harness.plan,
        receipt_chain_head=head,
        catalog_path=harness.catalog_path,
        storage=harness.storage,
        census_run_id=census_run_id,
        network_disabled=network_disabled,
    )


def _state_rows(harness: _Harness) -> list[sqlite3.Row]:
    """Every write-ahead state row, read through a genuinely fresh connection."""
    with sqlite3.connect(f"file:{harness.catalog_path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            "SELECT * FROM census_recovery_states ORDER BY recorded_at_utc, recovery_state_id"
        ).fetchall()


def _event_scenarios(harness: _Harness) -> list[str]:
    with sqlite3.connect(f"file:{harness.catalog_path}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return [
            str(row["scenario"])
            for row in connection.execute(
                "SELECT scenario FROM census_recovery_events ORDER BY occurred_at_utc, event_id"
            ).fetchall()
        ]


def _inspect(harness: _Harness, head: Path) -> object:
    return inspect_recovery_state(
        plan=harness.plan,
        receipt_chain_head=head,
        catalog_path=harness.catalog_path,
        data_root=harness.storage.data_root,
    )


class TestRecoveryApplier:
    def test_a_proven_orphan_is_adopted_through_the_authoritative_path(
        self, tmp_path: Path
    ) -> None:
        """Kill point 3: the orphan is adopted only via the accepted reconcile path, and a
        fresh inspection is still required afterward — the applier never continues on its own."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            observation_id, relative = _singleton_observation_id(
                harness, _requests(harness.plan)[1]
            )
            _delete_row(harness, observation_id)
            harness.release()
            assert _inspect(harness, head).determination == "UNSAFE"

            result = _apply(harness, head, "adopt-orphan", relative)

            assert result.action_taken == "adopted_verified"
            assert result.event_recorded is True
            assert result.post_state_undetermined is False
            assert result.requires_fresh_inspection is True
            assert result.continuation_prohibited is True
            with sqlite3.connect(harness.catalog_path) as read_back:
                restored = read_back.execute(
                    "SELECT COUNT(*) FROM census_source_observations WHERE observation_id = ?",
                    (observation_id,),
                ).fetchone()[0]
            assert restored == 1, "adoption restored the committed row from its lineage intent"

            follow_up = _apply(harness, head, "rebuild-projection", _PROJECTION)
            assert follow_up.action_taken == "projection_rebuilt"
            assert _inspect(harness, head).determination == "SAFE"

    def test_the_applier_refuses_every_action_from_undetermined(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            observation_id, relative = _singleton_observation_id(
                harness, _requests(harness.plan)[1]
            )
            _delete_row(harness, observation_id)
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    recovery_predecessor_receipt_id="0" * 64,
                    consumed_request_count_carried_forward=1,
                ),
            )
            with pytest.raises(RepairRefusedError, match="UNDETERMINED"):
                _apply(harness, head, "adopt-orphan", relative)

    def test_an_unknown_or_multi_action_request_is_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            for bogus in ("adopt-orphan quarantine-partial", "all", "ADOPT-ORPHAN", ""):
                with pytest.raises(RepairRefusedError):
                    _apply(harness, head, bogus, "anything")

    def test_a_stale_request_against_a_clean_state_is_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            with pytest.raises(RepairRefusedError, match="stale or already resolved"):
                _apply(harness, head, "quarantine-partial", "raw/sec/indexes/nothing.part")

    def test_an_action_differing_from_the_recommendation_is_refused(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            partial = harness.storage.tree.raw_indexes / "stray.part"
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"partial")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(partial.relative_to(harness.storage.data_root))
            with pytest.raises(RepairRefusedError, match="differs from the deterministic"):
                _apply(harness, head, "adopt-orphan", relative)
            with pytest.raises(RepairRefusedError, match="not a current"):
                _apply(harness, head, "quarantine-partial", "raw/sec/indexes/other.part")

    def test_quarantine_partial_preserves_and_never_deletes(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            partial = harness.storage.tree.raw_indexes / "stray.part"
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"partial-payload")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(partial.relative_to(harness.storage.data_root))
            harness.release()

            result = _apply(harness, head, "quarantine-partial", relative)

            assert result.action_taken == "quarantined"
            assert result.event_recorded is True
            assert not partial.exists()
            quarantine = harness.storage.tree.quarantine
            preserved = [
                path
                for path in quarantine.rglob("*")
                if path.is_file() and not path.name.endswith(".reason")
            ]
            assert any(path.read_bytes() == b"partial-payload" for path in preserved), (
                "the partial's bytes are preserved in quarantine, never deleted"
            )

    def test_remove_stale_part_requires_a_provably_never_promoted_spool(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            staging = harness.storage.tree.staging
            staging.mkdir(parents=True, exist_ok=True)
            spool = staging / f"sec_sic_code_list-{_NONCE_B}.part"
            spool.write_bytes(b"spooled")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(spool.relative_to(harness.storage.data_root))
            harness.release()

            result = _apply(harness, head, "remove-stale-part", relative)
            assert result.action_taken == "removed_never_promoted_temporary"
            assert result.event_recorded is True
            assert not spool.exists()

            second = staging / f"sec_sic_code_list-{_NONCE_C}.part"
            second.write_bytes(b"spooled")
            second.with_name(second.name + ".lineage.json").write_text("{}")
            with pytest.raises(RepairRefusedError, match="lineage intent"):
                _apply(
                    harness,
                    head,
                    "remove-stale-part",
                    str(second.relative_to(harness.storage.data_root)),
                )
            assert second.exists(), "a refusal mutates nothing"

    def test_rebuild_projection_uses_the_accepted_primitive(self, tmp_path: Path) -> None:
        """A projection that *lags* SQLite is reconstructed through the accepted primitive.

        The lag is produced the way a real one occurs — the last committed row never reached the
        derived file — so what is repaired here is a byte-exact prefix of the authoritative
        serialization, which is the condition Decision 064 §5 authorizes the rebuild for.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            projection = harness.storage.tree.audit / _PROJECTION
            lines = projection.read_bytes().splitlines(keepends=True)
            assert len(lines) > 1, "the fixture needs more than one projected row to truncate one"
            projection.write_bytes(b"".join(lines[:-1]))
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()
            assert _inspect(harness, head).determination == "UNSAFE"

            result = _apply(harness, head, "rebuild-projection", _PROJECTION)

            assert result.action_taken == "projection_rebuilt"
            assert result.event_recorded is True
            assert _inspect(harness, head).determination == "SAFE"

    def test_rebuild_projection_refuses_a_divergent_projection(self, tmp_path: Path) -> None:
        """Decision 064 §5.1: the rebuild repairs a lagging projection, never a diverging one.

        Bytes the authoritative catalog cannot account for are unadjudicated evidence about what
        wrote to the audit trail. Reconstructing over them would destroy exactly the evidence an
        owner needs, so the action refuses and the damaged file is left untouched for a ruling.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            projection = harness.storage.tree.audit / _PROJECTION
            with projection.open("ab") as handle:
                handle.write(b"{broken\n")
            damaged = projection.read_bytes()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            with pytest.raises(
                RepairRefusedError, match="diverges from SQLite rather than lagging"
            ):
                _apply(harness, head, "rebuild-projection", _PROJECTION)

            assert projection.read_bytes() == damaged, "a refusal mutates nothing"
            assert _state_rows(harness) == [], "a refusal opens no write-ahead state"

    def test_rebuild_projection_refuses_an_unproved_network_state(self, tmp_path: Path) -> None:
        """Condition 10 fails closed: an unestablished network state is treated as an open one."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            projection = harness.storage.tree.audit / _PROJECTION
            lines = projection.read_bytes().splitlines(keepends=True)
            projection.write_bytes(b"".join(lines[:-1]))
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            with pytest.raises(RepairRefusedError, match="network is disabled"):
                _apply(harness, head, "rebuild-projection", _PROJECTION, network_disabled=False)

            assert _state_rows(harness) == [], "a refusal opens no write-ahead state"

    def test_no_other_action_inherits_the_rebuild_eligibility(self, tmp_path: Path) -> None:
        """Decision 064 §5: the action-specific gate is for `rebuild-projection` alone.

        The same UNDETERMINED state that the projection rebuild may proceed from — here produced by
        a committed row with no object, which is unrelated to the projection — still refuses every
        other action, exactly as the blanket rule always did.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            _, relative = _singleton_observation_id(harness, _requests(harness.plan)[1])
            (harness.storage.tree.data_root / relative).unlink()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()
            assert _inspect(harness, head).determination == "UNDETERMINED"

            for action, target in (
                ("adopt-orphan", relative),
                ("quarantine-partial", relative),
                ("remove-stale-part", relative),
            ):
                with pytest.raises(RepairRefusedError, match="UNDETERMINED"):
                    _apply(harness, head, action, target)

            eligibility = rebuild_projection_eligibility(
                action="rebuild-projection",
                plan=harness.plan,
                receipt_chain_head=head,
                catalog_path=harness.catalog_path,
                storage=harness.storage,
                network_disabled=True,
            )
            assert not eligibility.permitted
            assert "authoritative_observations_unambiguous" in eligibility.unmet

    def test_orphan_adoption_is_scoped_to_exactly_one_event(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            first_id, first_relative = _singleton_observation_id(
                harness, _requests(harness.plan)[1]
            )
            second_id, _ = _singleton_observation_id(harness, _requests(harness.plan)[2])
            _delete_row(harness, first_id)
            _delete_row(harness, second_id)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            with pytest.raises(RepairRefusedError, match="exactly one authorized event"):
                _apply(harness, head, "adopt-orphan", first_relative)

    def test_one_action_never_cascades_into_a_second_repair(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            observation_id, relative = _singleton_observation_id(
                harness, _requests(harness.plan)[1]
            )
            _delete_row(harness, observation_id)
            partial = harness.storage.tree.raw_indexes / "stray.part"
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"partial")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            result = _apply(harness, head, "adopt-orphan", relative)

            assert result.action_taken == "adopted_verified"
            assert partial.exists(), "the unrelated partial was not touched — no cascade"
            assert _inspect(harness, head).determination == "UNSAFE", (
                "the remaining defect still blocks; nothing auto-continued"
            )

    def test_failed_event_recording_is_undetermined_and_prohibits_continuation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The prohibition is durable, not in-memory: the write-ahead row stays blocked."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            partial = harness.storage.tree.raw_indexes / "stray.part"
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"partial")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(partial.relative_to(harness.storage.data_root))

            def _refuse_recording(*args: object, **kwargs: object) -> int:
                message = "injected recording failure"
                raise CatalogWriteError(message)

            monkeypatch.setattr(acquisition_module, "record_recovery_events", _refuse_recording)
            harness.release()
            result = _apply(harness, head, "quarantine-partial", relative)

            assert result.event_recorded is False
            assert result.state_resolved is False
            assert result.post_state_undetermined is True
            assert "UNDETERMINED" in result.detail
            assert "continuation is prohibited" in result.detail
            rows = _state_rows(harness)
            assert len(rows) == 1
            assert rows[0]["resolution_state"] == "blocked", (
                "the exact write-ahead state remains durably blocked, so a restarted process "
                "sees the prohibition without this result object"
            )
            assert rows[0]["recovery_state_id"] == result.recovery_state_id
            assert rows[0]["scenario"] == _SCENARIO
            assert _event_scenarios(harness) == [], "no completed event was recorded"
            monkeypatch.undo()

            proposal = _propose(harness, head)
            assert proposal.permitted is False
            assert proposal.determination == "UNDETERMINED"
            assert any("write-ahead" in reason for reason in proposal.refusal_reasons)
            inspection = _inspect(harness, head)
            assert inspection.determination == "UNSAFE", (
                "the accepted inspector's condition 8.9 sees the blocked state"
            )

    def test_the_action_vocabulary_is_exactly_the_four_authorized_classes(self) -> None:
        assert RECOVERY_ACTIONS == (
            "adopt-orphan",
            "quarantine-partial",
            "rebuild-projection",
            "remove-stale-part",
        )


# =========================================================================== #
# Structural boundaries
# =========================================================================== #
class TestStructuralBoundaries:
    def test_no_detection_surface_can_reach_the_applier(self) -> None:
        """Reconstruction, reconciliation, proposal, and their helpers never invoke a repair."""
        read_only_surfaces = (
            reconstruct_catalog_state,
            verified_reusable_predecessor,
            conditional_validators,
            reconcile_requests,
            propose_continuation,
            acquisition_module._item_for,
            acquisition_module._classify_item,
            acquisition_module._repair_sweep,
            acquisition_module._identify_in_flight,
            acquisition_module._interpret_staging_spools,
            acquisition_module._contradicting_store_evidence,
            acquisition_module._segment_after_receipt,
            acquisition_module._verify_write_ahead_state,
        )
        for surface in read_only_surfaces:
            source = inspect_module.getsource(surface)
            assert "apply_recovery_action" not in source
            assert "rebuild_audit_projection" not in source or surface in {
                acquisition_module._repair_sweep,
            }, "no read surface rebuilds the projection"

    def test_detection_surfaces_write_nothing(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            partial = harness.storage.tree.raw_indexes / "stray.part"
            partial.parent.mkdir(parents=True, exist_ok=True)
            partial.write_bytes(b"partial")
            before = _tree_digest(harness)
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            reconcile_requests(
                plan=harness.plan,
                reconstruction=reconstruction,
                storage=harness.storage,
            )
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            _propose(harness, head)
            after = _tree_digest(harness)

        assert before == after

    def test_a_refused_action_mutates_nothing(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            before = _tree_digest(harness)
            with pytest.raises(RepairRefusedError):
                _apply(harness, head, "adopt-orphan", "raw/sec/indexes/none")
            after = _tree_digest(harness)

        assert before == after

    def test_no_transport_module_is_imported_by_the_t2_4_surfaces(self) -> None:
        source = inspect_module.getsource(acquisition_module)
        for line in source.splitlines():
            if line.startswith(("import ", "from ")):
                for forbidden in ("httpx", "socket", "urllib", "requests"):
                    assert forbidden not in line


# =========================================================================== #
# Decision 041 §§8-9 — the durable write-ahead lifecycle
# =========================================================================== #
def _stage_partial(harness: _Harness) -> str:
    partial = harness.storage.tree.raw_indexes / "stray.part"
    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.write_bytes(b"partial")
    return str(partial.relative_to(harness.storage.data_root))


class TestWriteAheadLifecycle:
    def test_a_successful_action_opens_records_and_exactly_resolves(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            result = _apply(harness, head, "quarantine-partial", relative)

            assert result.census_run_id == _RUN
            assert result.event_recorded is True
            assert result.state_resolved is True
            assert result.post_state_undetermined is False
            rows = _state_rows(harness)
            assert len(rows) == 1, "exactly one write-ahead state row exists — never a second"
            row = rows[0]
            assert row["census_run_id"] == _RUN
            assert row["recovery_state_id"] == result.recovery_state_id
            assert row["scenario"] == _SCENARIO
            assert row["resolution_state"] == "resolved"
            assert row["action_taken"] == "quarantined", (
                "the resolved row records the completed action result"
            )
            assert "write-ahead block" in str(row["detail"]), "the blocked detail is preserved"
            assert row["relative_path"] == relative
            assert _event_scenarios(harness) == ["interrupted_part_download"], (
                "exactly one actual completed event was recorded, under the accepted "
                "CHECK-constrained event vocabulary"
            )
            assert _SCENARIO not in _event_scenarios(harness), (
                "the write-ahead scenario never reaches census_recovery_events"
            )

    def test_a_missing_run_identity_refuses_before_mutation(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            partial = harness.storage.tree.data_root / relative
            with pytest.raises(RepairRefusedError, match="no census run identity"):
                _apply(harness, head, "quarantine-partial", relative, census_run_id="")
            assert partial.exists(), "nothing mutated"
            assert _state_rows(harness) == []

    def test_an_unregistered_run_identity_refuses_before_mutation(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            partial = harness.storage.tree.data_root / relative
            with pytest.raises(
                RepairRefusedError, match="does not resolve to a lawful existing governed"
            ):
                _apply(
                    harness,
                    head,
                    "quarantine-partial",
                    relative,
                    census_run_id="never-registered-run",
                )
            assert partial.exists(), "nothing mutated"
            assert _state_rows(harness) == []

    def test_an_open_failure_refuses_before_mutation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            partial = harness.storage.tree.data_root / relative

            def _refuse_open(*args: object, **kwargs: object) -> None:
                message = "injected open failure"
                raise CatalogWriteError(message)

            monkeypatch.setattr(acquisition_module, "open_recovery_state", _refuse_open)
            harness.release()
            with pytest.raises(RepairRefusedError, match="could not be opened"):
                _apply(harness, head, "quarantine-partial", relative)
            assert partial.exists(), "nothing mutated"
            assert _state_rows(harness) == []
            assert _event_scenarios(harness) == []

    def test_a_blocked_state_verification_failure_refuses_before_mutation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            partial = harness.storage.tree.data_root / relative

            monkeypatch.setattr(
                acquisition_module,
                "_verify_write_ahead_state",
                lambda *args: False,
            )
            harness.release()
            with pytest.raises(RepairRefusedError, match="could not be verified"):
                _apply(harness, head, "quarantine-partial", relative)
            assert partial.exists(), "nothing mutated"
            rows = _state_rows(harness)
            assert len(rows) == 1 and rows[0]["resolution_state"] == "blocked", (
                "the committed block remains durably blocked for owner adjudication"
            )
            assert _event_scenarios(harness) == []

    def test_a_mutation_failure_leaves_the_exact_state_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            partial = harness.storage.tree.data_root / relative

            def _refuse_quarantine(*args: object, **kwargs: object) -> Path:
                message = "injected mutation failure"
                raise RawObjectIntegrityError(message)

            monkeypatch.setattr(RawStore, "quarantine", _refuse_quarantine)
            harness.release()
            with pytest.raises(RawObjectIntegrityError, match="injected mutation failure"):
                _apply(harness, head, "quarantine-partial", relative)
            assert partial.exists(), "the mutation failed; the partial is untouched"
            rows = _state_rows(harness)
            assert len(rows) == 1 and rows[0]["resolution_state"] == "blocked"
            assert _event_scenarios(harness) == [], "no completed event was recorded"

    def test_a_resolution_failure_leaves_the_exact_state_blocked(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))

            def _refuse_resolution(*args: object, **kwargs: object) -> bool:
                message = "injected resolution failure"
                raise CatalogWriteError(message)

            monkeypatch.setattr(acquisition_module, "resolve_recovery_state", _refuse_resolution)
            harness.release()
            result = _apply(harness, head, "quarantine-partial", relative)

            assert result.event_recorded is True
            assert result.state_resolved is False
            assert result.post_state_undetermined is True
            assert "could not be exactly resolved" in result.detail
            rows = _state_rows(harness)
            assert len(rows) == 1 and rows[0]["resolution_state"] == "blocked"
            assert _event_scenarios(harness) == ["interrupted_part_download"]

    def test_a_resolution_readback_failure_is_undetermined_even_when_resolved(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))

            original = acquisition_module._verify_write_ahead_state

            def _blocked_only(catalog_path: Path, run: str, state: str, expected: str) -> bool:
                if expected == "resolved":
                    return False
                return original(catalog_path, run, state, expected)

            monkeypatch.setattr(acquisition_module, "_verify_write_ahead_state", _blocked_only)
            harness.release()
            result = _apply(harness, head, "quarantine-partial", relative)

            assert result.state_resolved is True
            assert result.post_state_undetermined is True, (
                "the current invocation is UNDETERMINED even though the durable row resolved"
            )
            assert "readback could not complete" in result.detail
            rows = _state_rows(harness)
            assert rows[0]["resolution_state"] == "resolved", (
                "a later process recomputes from durable catalog state and sees the resolution"
            )

    def test_a_second_action_is_refused_while_a_state_is_unresolved(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            open_recovery_state(
                harness.writer,
                census_run_id=_RUN,
                recovery_state_id="pre-existing-block",
                scenario=_SCENARIO,
                action_taken="quarantine-partial",
                detail="an earlier action's unresolved write-ahead block",
            )
            partial = harness.storage.tree.data_root / relative
            with pytest.raises(RepairRefusedError, match="already exist for run"):
                _apply(harness, head, "quarantine-partial", relative)
            assert partial.exists(), "nothing mutated"
            assert len(_state_rows(harness)) == 1, "no second block was opened"

    def test_no_in_memory_field_is_the_sole_continuation_prohibition(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Discard the result object entirely; the durable state still refuses everything."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))

            def _refuse_recording(*args: object, **kwargs: object) -> int:
                message = "injected recording failure"
                raise CatalogWriteError(message)

            monkeypatch.setattr(acquisition_module, "record_recovery_events", _refuse_recording)
            harness.release()
            _apply(harness, head, "quarantine-partial", relative)
            monkeypatch.undo()

            proposal = _propose(harness, head)
            assert proposal.permitted is False
            assert proposal.determination == "UNDETERMINED"
            assert any("write-ahead" in reason for reason in proposal.refusal_reasons)
            second = harness.storage.tree.raw_indexes / "second-stray.part"
            second.write_bytes(b"second partial")
            second_relative = str(second.relative_to(harness.storage.data_root))
            with pytest.raises(RepairRefusedError, match="already exist for run"):
                _apply(harness, head, "quarantine-partial", second_relative)
            assert second.exists(), "the second action mutated nothing"


# =========================================================================== #
# Decision 041 §9 / packet §10 — restart durability across OS processes
# =========================================================================== #
_CHILD_PREAMBLE = """
import json
import sys
from datetime import date
from pathlib import Path

import disclosure_drift.m3.acquisition as acq
from disclosure_drift.errors import CatalogWriteError
from disclosure_drift.m3.request_plan import build_m3_2a_request_plan

evidence_root, catalog_rel, data_rel, head = sys.argv[1:5]
plan = build_m3_2a_request_plan(
    coverage_start=date(2010, 1, 1),
    coverage_end=date(2010, 6, 30),
    as_of_date=date(2010, 7, 1),
    include_open_quarter=False,
    calendar_year=2010,
    calendar_evidence_entry_count=0,
    already_satisfied_index_keys=frozenset(),
    requests_per_second=4.0,
)
storage = acq.prepare_storage(
    evidence_root=Path(evidence_root), data_root_relative=data_rel
)
catalog = Path(evidence_root) / catalog_rel
"""

_CHILD_APPLY = (
    _CHILD_PREAMBLE
    + """
target, run_id, inject = sys.argv[5:8]
if inject == "fail-event":
    def _refuse(*args, **kwargs):
        raise CatalogWriteError("injected recording failure")

    acq.record_recovery_events = _refuse
result = acq.apply_recovery_action(
    action="quarantine-partial",
    target=target,
    plan=plan,
    receipt_chain_head=Path(head),
    catalog_path=catalog,
    storage=storage,
    census_run_id=run_id,
)
print(
    json.dumps(
        {
            "event_recorded": result.event_recorded,
            "state_resolved": result.state_resolved,
            "post_state_undetermined": result.post_state_undetermined,
            "recovery_state_id": result.recovery_state_id,
        }
    )
)
"""
)

_CHILD_RESTART = (
    _CHILD_PREAMBLE  # noqa: S608 - a fixed child-process script, not query construction
    + """
import sqlite3

from disclosure_drift.m3.recovery import inspect_recovery_state

proposal = acq.propose_continuation(
    plan=plan,
    receipt_chain_head=Path(head),
    catalog_path=catalog,
    storage=storage,
    window="M3.2A",
    approved_ceiling=plan.hard_request_ceiling,
)
inspection = inspect_recovery_state(
    plan=plan,
    receipt_chain_head=Path(head),
    catalog_path=catalog,
    data_root=storage.data_root,
)
with sqlite3.connect(f"file:{catalog}?mode=ro", uri=True) as connection:
    blocked = connection.execute(
        "SELECT COUNT(*) FROM census_recovery_states WHERE resolution_state = 'blocked'"
    ).fetchone()[0]
print(
    json.dumps(
        {
            "permitted": proposal.permitted,
            "determination": proposal.determination,
            "inspection": inspection.determination,
            "blocked": blocked,
            "write_ahead_refusal": any(
                "write-ahead" in reason for reason in proposal.refusal_reasons
            ),
        }
    )
)
"""
)


def _run_child(script: str, *arguments: str) -> dict[str, object]:
    completed = subprocess.run(  # noqa: S603 - sys.executable over a fixed script, offline
        [sys.executable, "-c", script, *arguments],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.strip().splitlines()[-1])
    assert isinstance(payload, dict)
    return payload


class TestRestartDurabilityAcrossProcesses:
    def test_failed_event_recording_survives_a_restart_and_prohibits_continuation(
        self, tmp_path: Path
    ) -> None:
        """The applier fails in one OS process; a genuinely fresh process still refuses."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            evidence_root = str(harness.catalog_path.parents[1])
            harness.release()

            applied = _run_child(
                _CHILD_APPLY,
                evidence_root,
                _CATALOG_RELATIVE,
                _DATA_RELATIVE,
                str(head),
                relative,
                _RUN,
                "fail-event",
            )
            assert applied["event_recorded"] is False
            assert applied["post_state_undetermined"] is True

            restarted = _run_child(
                _CHILD_RESTART,
                evidence_root,
                _CATALOG_RELATIVE,
                _DATA_RELATIVE,
                str(head),
            )
            assert restarted["blocked"] == 1, "the fresh OS process sees the unresolved state"
            assert restarted["permitted"] is False, "restart prohibits continuation"
            assert restarted["determination"] == "UNDETERMINED"
            assert restarted["inspection"] == "UNSAFE"
            assert restarted["write_ahead_refusal"] is True

    def test_the_successful_control_resolves_and_a_restart_permits(self, tmp_path: Path) -> None:
        """The same action without the injected failure: resolved, and a fresh process agrees."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            relative = _stage_partial(harness)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            evidence_root = str(harness.catalog_path.parents[1])
            harness.release()

            applied = _run_child(
                _CHILD_APPLY,
                evidence_root,
                _CATALOG_RELATIVE,
                _DATA_RELATIVE,
                str(head),
                relative,
                _RUN,
                "none",
            )
            assert applied["event_recorded"] is True
            assert applied["state_resolved"] is True
            assert applied["post_state_undetermined"] is False

            restarted = _run_child(
                _CHILD_RESTART,
                evidence_root,
                _CATALOG_RELATIVE,
                _DATA_RELATIVE,
                str(head),
            )
            assert restarted["blocked"] == 0
            assert restarted["inspection"] == "SAFE"
            assert restarted["determination"] == "SAFE"
            assert restarted["permitted"] is True


# =========================================================================== #
# Packet §11 — durable in-flight identity, never positional inference
# =========================================================================== #
def _spool(harness: _Harness, name: str, *, payload: bytes = b"partial") -> Path:
    staging = harness.storage.tree.staging
    staging.mkdir(parents=True, exist_ok=True)
    spool = staging / name
    spool.write_bytes(payload)
    return spool


class TestInFlightIdentity:
    def test_a_spool_route_disagreeing_with_position_is_undetermined(self, tmp_path: Path) -> None:
        """The spool names a route after the first unresolved request: contradiction."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            _spool(harness, f"sec_edgar_filing_calendar-{_NONCE}.part")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "disagrees with the first unresolved" in proposal.accounting.basis
        assert proposal.accounting.in_flight_charge == 0, "never charged on a contradiction"
        assert proposal.permitted is False
        assert proposal.determination == "UNDETERMINED"

    def test_two_unresolved_requests_sharing_the_route_are_undetermined(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=5)
            harness.flush_projection()
            _spool(harness, f"sec_full_index_company-{_NONCE}.part")
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=5,
                    actual_physical_attempt_count=5,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": 5,
                            "physical_attempt_count": 5,
                        },
                    },
                    response_classification_totals={
                        "proceed": 5,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": 5},
                    raw_object_count=5,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "share the spool's route" in proposal.accounting.basis
        assert proposal.permitted is False

    def test_multiple_spools_are_undetermined_without_any_other_evidence(
        self, tmp_path: Path
    ) -> None:
        """Two spools alone suffice: no partial or orphan is additionally required."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            _spool(harness, f"sec_sic_code_list-{_NONCE}.part")
            _spool(harness, f"sec_edgar_filing_calendar-{_NONCE_B}.part")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "more than one in-flight request appears possible" in proposal.accounting.basis
        assert proposal.permitted is False

    @pytest.mark.parametrize(
        "name",
        [
            f"unregistered_route-{'deadbeef' * 4}.part",
            "sec_sic_code_list-nothex.part",
            "sec_sic_code_list-deadbeef.part",
            "noseparator.part",
        ],
    )
    def test_an_ambiguous_or_malformed_spool_is_undetermined(
        self, tmp_path: Path, name: str
    ) -> None:
        """No generic string split: exact registered prefix and exact nonce, or refusal."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            _spool(harness, name)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "does not parse" in proposal.accounting.basis
        assert proposal.permitted is False

    def test_a_symlinked_spool_is_refused_as_identification_evidence(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            outside = tmp_path / "outside-target.part"
            outside.write_bytes(b"outside")
            staging = harness.storage.tree.staging
            staging.mkdir(parents=True, exist_ok=True)
            (staging / f"sec_sic_code_list-{_NONCE}.part").symlink_to(outside)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "symbolic link" in proposal.accounting.basis
        assert proposal.permitted is False
        assert outside.read_bytes() == b"outside", "the link target is untouched"

    def test_an_orphan_without_a_spool_is_undetermined_never_a_zero_charge(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            orphan = harness.storage.tree.raw_indexes / "orphan.bin"
            orphan.parent.mkdir(parents=True, exist_ok=True)
            orphan.write_bytes(b"orphan")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "never becomes a zero charge" in proposal.accounting.basis
        assert proposal.accounting.in_flight_charge == 0
        assert proposal.permitted is False

    def test_contradicting_evidence_beside_a_valid_spool_is_undetermined(
        self, tmp_path: Path
    ) -> None:
        """Condition seven: no other durable evidence may contradict the single identity."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            _spool(harness, f"sec_sic_code_list-{_NONCE}.part")
            stray = harness.storage.tree.raw_indexes / "unattributed.part"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_bytes(b"raw partial")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "no single in-flight identity is uncontradicted" in proposal.accounting.basis
        assert proposal.permitted is False

    def test_post_receipt_activity_after_the_identified_request_is_undetermined(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), stamp=_POST_RECEIPT_STAMP)
            harness.flush_projection()
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            victim = next(
                observation
                for observation in reconstruction.observations
                if observation.source_id == "sec_sic_code_list"
            )
            stored = harness.storage.data_root / str(victim.relative_storage_path)
            lineage = RawStore.lineage_path(stored)
            stored.unlink()
            if lineage.is_file():
                lineage.unlink()
            _delete_row(harness, victim.observation_id)
            _spool(harness, f"sec_sic_code_list-{_NONCE}.part")
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=0,
                    actual_physical_attempt_count=0,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": 0,
                            "physical_attempt_count": 0,
                        },
                    },
                    response_classification_totals={
                        "proceed": 0,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": 0},
                    raw_object_count=0,
                ),
            )
            proposal = _propose(harness, head)

        assert proposal.accounting.undetermined is True
        assert "after the identified one" in proposal.accounting.basis
        assert proposal.permitted is False

    def test_no_durable_in_flight_evidence_means_no_charge(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.accounting.in_flight_charge == 0
        assert proposal.accounting.in_flight_request_identity is None
        assert proposal.accounting.undetermined is False


# =========================================================================== #
# Packet §12 — the exhaustive continuation-state partition
# =========================================================================== #
class TestContinuationStatePartition:
    def test_the_partition_is_pairwise_disjoint_and_total(self) -> None:
        sets = (
            acquisition_module._SATISFYING_ITEM_STATES,
            acquisition_module._RETRYABLE_ITEM_STATES,
            acquisition_module._BLOCKING_ITEM_STATES,
            acquisition_module._UNCERTAIN_ITEM_STATES,
        )
        for index, first in enumerate(sets):
            for second in sets[index + 1 :]:
                assert not (first & second), "the four sets are pairwise disjoint"
        union = frozenset().union(*sets)
        assert union == acquisition_module._ITEM_STATE_VOCABULARY
        assert union == frozenset(
            {
                "satisfied_new",
                "satisfied_duplicate",
                "satisfied_not_modified",
                "satisfied_superseding",
                "absent",
                "failed",
                "not_attempted",
                "quarantined",
                "stopped",
                "archive_lineage_missing_or_invalid",
                "hash_mismatch",
                "row_without_object",
            }
        ), "the union is exactly the complete emitted-state vocabulary"

    def test_an_unknown_state_refuses_rather_than_falling_through(self) -> None:
        item = acquisition_module.ReconciliationItem(
            position=0,
            source_id="sec_company_tickers",
            identity_label="sec_company_tickers",
            request_identity="synthetic",
            state="a_state_no_set_claims",
            observation_id=None,
            verified=False,
            excluded_from_continuation=False,
            attempts=0,
            reason_codes=(),
            conditions=(),
        )
        with pytest.raises(AcquisitionGateError, match="outside the exhaustive"):
            acquisition_module._classify_item(item)

    def test_every_item_contributes_exactly_once_to_continuation_treatment(
        self, tmp_path: Path
    ) -> None:
        """Satisfied, retryable, and blocking items in one proposal, each counted once."""
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(404, body=b"", content_type=None)
        with _harness(tmp_path) as harness:
            harness.run(script, headroom=5)
            harness.flush_projection()
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            exchange = verified_reusable_predecessor(reconstruction, "sec_company_tickers_exchange")
            assert exchange is not None
            (harness.storage.data_root / str(exchange.relative_storage_path)).write_bytes(
                b"tampered"
            )
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        items = proposal.reconciliation.items
        treatments = [acquisition_module._classify_item(item) for item in items]
        counted = (
            len(proposal.already_satisfied_excluded)
            + len(proposal.remaining)
            + sum(1 for treatment in treatments if treatment == "blocking")
            + sum(1 for treatment in treatments if treatment == "uncertain")
        )
        assert counted == len(items) == plan.planned_unique_logical_requests
        remaining_labels = {request.identity_label for request in proposal.remaining}
        excluded_labels = set(proposal.already_satisfied_excluded)
        blocking_labels = {
            item.identity_label
            for item, treatment in zip(items, treatments, strict=True)
            if treatment == "blocking"
        }
        assert not remaining_labels & excluded_labels
        assert not remaining_labels & blocking_labels
        assert not excluded_labels & blocking_labels

    def test_hash_mismatch_is_blocking_and_refuses_continuation(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            tickers = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert tickers is not None
            (harness.storage.data_root / str(tickers.relative_storage_path)).write_bytes(
                b"tampered"
            )
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        item = next(
            entry
            for entry in proposal.reconciliation.items
            if entry.source_id == "sec_company_tickers"
        )
        assert item.state == "hash_mismatch"
        assert acquisition_module._classify_item(item) == "blocking"
        assert item.identity_label not in set(proposal.already_satisfied_excluded), (
            "a blocking defect never counts as satisfied"
        )
        assert item.identity_label not in {
            request.identity_label for request in proposal.remaining
        }, "omitted from the remainder only because the whole proposal is refused"
        assert proposal.permitted is False
        assert any(
            "blocking reconciliation defect" in reason for reason in proposal.refusal_reasons
        )
        assert any("hash_mismatch" in reason for reason in proposal.refusal_reasons)

    def test_invalid_archive_lineage_is_blocking_and_refuses_continuation(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            harness.writer.connection.execute("DELETE FROM census_archive_members")
            harness.writer.connection.commit()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        item = next(
            entry
            for entry in proposal.reconciliation.items
            if entry.source_id == "sec_bulk_submissions"
        )
        assert item.state == "archive_lineage_missing_or_invalid"
        assert acquisition_module._classify_item(item) == "blocking"
        assert proposal.permitted is False
        assert any(
            "blocking reconciliation defect" in reason for reason in proposal.refusal_reasons
        )

    def test_an_absence_without_a_terminal_reason_escalates_to_blocking(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            requests = derive_logical_requests(harness.plan)
            sic = next(request for request in requests if request.source_id == "sec_sic_code_list")
            identity = acquisition_module.planned_request_identity(sic)
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            template = reconstruction.observations[0]
            from dataclasses import replace as dataclass_replace

            uncoded = dataclass_replace(
                template,
                observation_id="ab" * 16,
                source_id="sec_sic_code_list",
                identity=identity,
                relative_storage_path=None,
                outcome="failed",
                http_status=500,
                reason_codes=(),
            )
            recorder = ObservationRecorder(writer=harness.writer, tree=harness.storage.tree)
            recorder.record(uncoded)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        item = next(
            entry
            for entry in proposal.reconciliation.items
            if entry.source_id == "sec_sic_code_list"
        )
        assert item.state == "failed"
        assert "absence_without_terminal_reason" in item.conditions
        assert acquisition_module._classify_item(item) == "blocking"
        assert proposal.permitted is False
        assert item.identity_label not in {request.identity_label for request in proposal.remaining}

    def test_retryable_states_are_included_exactly_once_in_the_remainder(
        self, tmp_path: Path
    ) -> None:
        """A coded absence is still-owed work: in the remainder, and in the worst case."""
        plan = _plan()
        script = _success_script(plan)
        requests = derive_logical_requests(plan)
        tickers = next(
            index
            for index, request in enumerate(requests)
            if request.source_id == "sec_company_tickers"
        )
        script[tickers] = _scripted(404, body=b"", content_type=None)
        with _harness(tmp_path) as harness:
            harness.run(script, headroom=5)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        labels = [request.identity_label for request in proposal.remaining]
        assert labels.count("sec_company_tickers") == 1, (
            "the absent request is included exactly once in the remainder"
        )
        assert len(labels) == len(set(labels))
        worst = sum(
            acquisition_module.derive_a_reachable(SOURCES[request.source_id])
            for request in proposal.remaining
        )
        assert proposal.worst_case_remaining_attempts == worst

    def test_row_without_object_is_persistence_uncertain(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            reconstruction = reconstruct_catalog_state(
                catalog_path=harness.catalog_path, storage=harness.storage
            )
            tickers = verified_reusable_predecessor(reconstruction, "sec_company_tickers")
            assert tickers is not None
            stored = harness.storage.data_root / str(tickers.relative_storage_path)
            lineage = RawStore.lineage_path(stored)
            stored.unlink()
            if lineage.is_file():
                lineage.unlink()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        item = next(
            entry
            for entry in proposal.reconciliation.items
            if entry.source_id == "sec_company_tickers"
        )
        assert item.state == "row_without_object"
        assert acquisition_module._classify_item(item) == "uncertain"
        assert proposal.determination == "UNDETERMINED"
        assert proposal.permitted is False
        assert any("persistence-uncertain" in reason for reason in proposal.refusal_reasons)
        assert item.identity_label not in {request.identity_label for request in proposal.remaining}


# =========================================================================== #
# Packet §13 — recovery-boundary scoping, and §14 — symlink-sweep alignment
# =========================================================================== #
class TestRecoveryBoundaryScoping:
    def test_one_valid_orphan_plus_one_stray_lineage_intent_refuses_before_mutation(
        self, tmp_path: Path
    ) -> None:
        """The guard is load-bearing: without it the accepted primitive would adopt the
        orphan AND quarantine the unrelated intent in one pass — an unauthorized cascade."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            observation_id, relative = _singleton_observation_id(
                harness, _requests(harness.plan)[1]
            )
            _delete_row(harness, observation_id)
            stray_intent = harness.storage.tree.raw_indexes / "ghost.bin.lineage.json"
            stray_intent.parent.mkdir(parents=True, exist_ok=True)
            stray_intent.write_text('{"intent":"stray"}', encoding="utf-8")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            orphan_path = harness.storage.data_root / relative
            before = _tree_digest(harness)

            with pytest.raises(RepairRefusedError, match="lineage intent without its raw"):
                _apply(harness, head, "adopt-orphan", relative)

            assert _tree_digest(harness) == before, "catalog and filesystem digests unchanged"
            assert orphan_path.exists(), "the orphan is preserved"
            assert stray_intent.exists(), "the stray intent is preserved"
            assert _state_rows(harness) == [], "refused before the write-ahead block"


class TestSymlinkSweepAlignment:
    def test_a_symlinked_staging_spool_is_never_a_removal_candidate(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            outside = tmp_path / "linked-target.part"
            outside.write_bytes(b"linked payload")
            staging = harness.storage.tree.staging
            staging.mkdir(parents=True, exist_ok=True)
            link = staging / f"sec_sic_code_list-{_NONCE}.part"
            link.symlink_to(outside)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(link.relative_to(harness.storage.data_root))

            sweep = acquisition_module._repair_sweep(harness.catalog_path, harness.storage)
            observed = acquisition_module._staging_partials(harness.storage.tree)
            assert relative not in sweep.staging_partials, (
                "the mutating sweep never lists a symlinked spool as a candidate"
            )
            assert relative not in observed, (
                "the read-only observer and the mutating sweep classify it consistently"
            )

            with pytest.raises(RepairRefusedError):
                _apply(harness, head, "remove-stale-part", relative)
            assert link.is_symlink(), "the link itself is untouched"
            assert outside.read_bytes() == b"linked payload", "the link target is untouched"

    def test_the_deletion_path_refuses_a_symlink_even_as_a_forced_candidate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Defence in depth: even if a sweep ever offered a symlink, removal still refuses."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            outside = tmp_path / "linked-target.part"
            outside.write_bytes(b"linked payload")
            staging = harness.storage.tree.staging
            staging.mkdir(parents=True, exist_ok=True)
            link = staging / f"sec_sic_code_list-{_NONCE}.part"
            link.symlink_to(outside)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            relative = str(link.relative_to(harness.storage.data_root))

            original = acquisition_module._repair_sweep

            def _forged(catalog_path: Path, storage: StorageBinding) -> object:
                sweep = original(catalog_path, storage)
                from dataclasses import replace as dataclass_replace

                return dataclass_replace(sweep, staging_partials=(relative,))

            monkeypatch.setattr(acquisition_module, "_repair_sweep", _forged)
            with pytest.raises(RepairRefusedError, match="symbolic link"):
                _apply(harness, head, "remove-stale-part", relative)
            assert link.is_symlink()
            assert outside.read_bytes() == b"linked payload"


# =========================================================================== #
# Packet §15 — accounting overlap and deterministic refusal semantics
# =========================================================================== #
class TestAccountingAndRefusalSemantics:
    def test_snapshot_exclusion_overlaps_historical_disposition_counters(
        self, tmp_path: Path
    ) -> None:
        """The same items count in both; the counters are never additive."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        reconciliation = proposal.reconciliation
        assert reconciliation.already_satisfied_excluded_count == 7
        assert reconciliation.duplicate_object_count == 7
        duplicate_labels = {
            item.identity_label
            for item in reconciliation.items
            if item.state == "satisfied_duplicate"
        }
        excluded_labels = {
            item.identity_label for item in reconciliation.items if item.excluded_from_continuation
        }
        assert duplicate_labels <= excluded_labels, (
            "every byte-identical duplicate is also excluded from continuation — the "
            "snapshot count overlaps the disposition counter"
        )
        assert (
            reconciliation.already_satisfied_excluded_count + reconciliation.duplicate_object_count
            != len(reconciliation.items)
        ), "summing the overlapping counters as exclusive outcomes double-counts"

    def test_permitted_and_the_refusal_reasons_agree_everywhere(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            clean = _propose(harness, head)
            mismatched = _propose(harness, head, ceiling=harness.plan.hard_request_ceiling + 1)

        for proposal in (clean, mismatched):
            assert proposal.permitted is (proposal.refusal_reasons == ()), (
                "permitted and its refusal explanations are one fact stated twice"
            )
        assert clean.permitted is True
        assert mismatched.permitted is False

    def test_cumulative_consumption_above_the_ceiling_has_a_deterministic_reason(
        self, tmp_path: Path
    ) -> None:
        """Each chained receipt lawfully records at most the ceiling; the chain sums past it.

        Decision 055 §7.4 bounds each receipt's own ``carried_forward + actual`` by the ceiling, so
        both receipts here are individually valid: the root carries nothing and places the ceiling
        exactly, and its successor carries nothing forward and places the ceiling again. What
        exceeds the ceiling is the **chain arithmetic** summed across both — precisely the condition
        the continuation proposal must refuse, and now proven through the chain rather than through
        a single receipt the schema would no longer accept.
        """
        ceiling = _plan().hard_request_ceiling
        at_ceiling = {
            "actual_logical_request_count": ceiling,
            "actual_physical_attempt_count": ceiling,
            "actual_per_route": {
                "sec_bulk_submissions": {
                    "logical_request_count": ceiling,
                    "physical_attempt_count": ceiling,
                },
            },
            "response_classification_totals": {
                "proceed": ceiling,
                "retry": 0,
                "retry_after": 0,
                "cooldown": 0,
                "fail": 0,
                "quarantine": 0,
            },
            "status_code_totals": {"200": ceiling},
            "raw_object_count": 3,
        }
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            first_receipt = _receipt(harness.plan, **at_ceiling)
            _write_receipts(tmp_path, first_receipt)
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    recovery_predecessor_receipt_id=first_receipt.receipt_id,
                    consumed_request_count_carried_forward=0,
                    **at_ceiling,
                ),
            )
            first = _propose(harness, head)
            second = _propose(harness, head)

        assert first.permitted is False
        assert any("already exceeds the approved ceiling" in r for r in first.refusal_reasons)
        assert first.refusal_reasons == second.refusal_reasons, "refusals are deterministic"

    def test_an_unresolved_write_ahead_state_has_its_own_refusal_reason(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            open_recovery_state(
                harness.writer,
                census_run_id=_RUN,
                recovery_state_id="unresolved-block",
                scenario=_SCENARIO,
                action_taken="quarantine-partial",
                detail="an interrupted action's unresolved write-ahead block",
            )
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.permitted is False
        assert proposal.determination == "UNDETERMINED", (
            "an unresolved write-ahead state is persistence-uncertain, not merely unsafe"
        )
        assert any(
            "t2_4_recovery_action write-ahead state(s) remain blocked" in reason
            for reason in proposal.refusal_reasons
        )
        assert any(
            "the read-only inspection is UNSAFE" in reason for reason in proposal.refusal_reasons
        ), "the accepted inspector's condition 8.9 refusal is also carried"

    def test_an_inspection_that_is_not_safe_is_a_refusal_reason(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan), headroom=3)
            harness.flush_projection()
            orphan = harness.storage.tree.raw_indexes / "orphan.bin"
            orphan.parent.mkdir(parents=True, exist_ok=True)
            orphan.write_bytes(b"orphan")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            proposal = _propose(harness, head)

        assert proposal.permitted is False
        assert any(
            "the read-only inspection is UNSAFE" in reason for reason in proposal.refusal_reasons
        )


_TERMINAL_RUN: Final = "m3-2-terminal-fixture-run-0001"


def _condition(state: object, number: str) -> object:
    """One §8 condition from a completed inspection, by its number."""
    return next(item for item in state.conditions if item.number == number)


def _register_terminal_run(
    harness: _Harness,
    *,
    job_state: str = "completed",
    attempts: int = 3,
    started_at_utc: str = "2026-08-01T12:00:00Z",
    finished_at_utc: str = _RECEIPT_COMPLETED,
) -> None:
    """The durable run row and pre-send ledger a terminal receipt must agree with.

    The receipt carries no run identity by design, so the terminal path joins on the facts both
    surfaces recorded independently — window, start, and end — and then reconciles the attempt
    count against the ledger. Both are written here so the fixture is a state a real invocation
    could have left, not a row shaped to satisfy one comparison.
    """
    connection = harness.writer.connection
    with transaction(connection) as open_connection:
        open_connection.execute(
            "INSERT INTO ops_ingestion_jobs "
            "(job_id, job_kind, job_state, stage, started_at_utc, finished_at_utc) "
            "VALUES (?, 'm3_2_acquisition', ?, 'M3.2A', ?, ?)",
            (_TERMINAL_RUN, job_state, started_at_utc, finished_at_utc),
        )
        for ordinal in range(attempts):
            open_connection.execute(
                "INSERT INTO ops_retrieval_attempts "
                "(retrieval_attempt_id, job_id, source_url_canonical, logical_role, "
                "attempt_number, attempt_state, started_at_utc) "
                "VALUES (?, ?, ?, 'acquire', ?, 'started', ?)",
                (
                    f"attempt-{ordinal}",
                    _TERMINAL_RUN,
                    f"https://www.sec.gov/fixture/{ordinal}",
                    ordinal + 1,
                    started_at_utc,
                ),
            )


def _set_outcome(harness: _Harness, observation_id: str, outcome: str) -> None:
    """Restate one committed observation's outcome, leaving the row and its object in place."""
    connection = harness.writer.connection
    connection.execute(
        "UPDATE census_source_observations SET outcome = ? WHERE observation_id = ?",
        (outcome, observation_id),
    )
    connection.commit()
    rebuild_audit_projection(connection, harness.storage.tree.audit / _PROJECTION)


_SHADOW_INSTANT: Final = "2099-01-01T00:00:00Z"


def _shadow_row(
    harness: _Harness, observation_id: str, shadow_id: str, **overrides: object
) -> None:
    """Copy one committed observation into a strictly newer row for the same identity.

    Every column is copied from a row the recorder itself wrote, so the shadow differs from real
    evidence only in what ``overrides`` names. That is what makes the tests below able to isolate
    one rule at a time: the identity, the route, and the provenance are unchanged, and the newest
    row for that identity is the shadow.
    """
    connection = harness.writer.connection
    columns = [
        row[1]
        for row in connection.execute("PRAGMA table_info(census_source_observations)").fetchall()
    ]
    assignable = ", ".join(name for name in columns if name != "observation_id")
    connection.execute(
        f"INSERT INTO census_source_observations (observation_id, {assignable}) "  # noqa: S608
        f"SELECT ?, {assignable} FROM census_source_observations WHERE observation_id = ?",
        (shadow_id, observation_id),
    )
    fields = {"retrieved_at_utc": _SHADOW_INSTANT, "projected_to_audit": 0, **overrides}
    assignments = ", ".join(f"{name} = ?" for name in fields)
    connection.execute(
        f"UPDATE census_source_observations SET {assignments} "  # noqa: S608
        f"WHERE observation_id = ?",
        (*fields.values(), shadow_id),
    )
    connection.commit()
    rebuild_audit_projection(connection, harness.storage.tree.audit / _PROJECTION)


def _shadow_with_a_newer_unresolvable_row(harness: _Harness, observation_id: str) -> None:
    """Give one identity a newer *usable* row whose object is absent, keeping the older good one.

    This is the state that separates "judge the newest" from "keep looking until something
    satisfies": the identity's most recent evidence does not resolve, and an earlier row for the
    same identity does.
    """
    _shadow_row(
        harness,
        observation_id,
        "shadow" + "0" * 26,
        relative_storage_path="raw/sec/bulk/never-promoted.json",
    )


def _shadow_with_a_newer_unusable_row(harness: _Harness, observation_id: str) -> None:
    """Give one identity a newer **non-usable** row that still names the good object's path.

    A quarantined observation keeps a storage path, so it is not filtered out by the payload
    check — only by the usable-outcome rule. That makes this the fixture that isolates that rule.
    """
    _shadow_row(harness, observation_id, "quarantined" + "0" * 21, outcome="quarantined")


def _restate_identity(harness: _Harness, observation_id: str, url: str) -> None:
    """Move one committed row onto a different request identity of the same route.

    This is the shape an owner-approved endpoint substitution leaves behind: the route still holds
    a committed row, but it belongs to an identity the current plan no longer contains, so the
    planned identity is genuinely unsatisfied.
    """
    connection = harness.writer.connection
    connection.execute(
        "UPDATE census_source_observations SET request_identity = ?, requested_url = ? "
        "WHERE observation_id = ?",
        (url, url, observation_id),
    )
    connection.commit()
    rebuild_audit_projection(connection, harness.storage.tree.audit / _PROJECTION)


# =========================================================================== #
# Decision 064 §§3-4 — a successful terminal head is established, and is never resumable
# =========================================================================== #
def _complete_receipt(plan: RequestPlan, **overrides: object) -> ExecutionReceipt:
    """A live receipt recording a window that finished successfully."""
    fields: dict[str, object] = {
        "completion_status": "complete",
        "reason_code": None,
        "reason_detail": None,
        "interruption_state": None,
    }
    fields.update(overrides)
    return _receipt(plan, **fields)


class TestSuccessfulTerminalHead:
    """Establishing a terminal state and authorizing a resume are separate questions.

    The whole point of Decision 064 §4 is that making the first answerable for a `complete` head
    must not make the second answerable too. Every test here asserts both halves.
    """

    def test_a_complete_head_establishes_its_terminal_state(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert _condition(state, "8.2").status == "MET"
            assert state.head_completion_status == "complete"
            assert state.interruption_state is None
            assert state.determination == "SAFE"

    def test_a_complete_head_is_never_classified_as_a_failure(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.head_acquisition_complete is True
            assert "failed" not in _condition(state, "8.2").detail
            assert state.interruption_state is None, "no interruption state is fabricated"

    def test_a_complete_head_refuses_a_continuation_proposal(self, tmp_path: Path) -> None:
        """The refusal is explicit and stated on its own, not inherited from an empty remainder."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            proposal = _propose(harness, head)

            assert proposal.permitted is False
            assert any(
                "records a completed acquisition" in reason for reason in proposal.refusal_reasons
            )
            assert proposal.inspection.continuation_permitted is False

    def test_a_complete_head_beside_a_disagreeing_run_establishes_nothing(
        self, tmp_path: Path
    ) -> None:
        """Every one of the ten terminal conditions still applies to a successful head."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness, job_state="failed")
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert _condition(state, "8.2").status == "NOT MET"
            assert "the two surfaces disagree" in _condition(state, "8.2").detail

    def test_a_complete_head_over_an_ambiguous_store_establishes_nothing(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            _, relative = _singleton_observation_id(harness, _requests(harness.plan)[1])
            (harness.storage.tree.data_root / relative).unlink()
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert _condition(state, "8.2").status == "NOT MET"
            assert "no stored object" in _condition(state, "8.2").detail
            assert state.determination == "UNDETERMINED"

    def test_a_complete_head_over_a_blocked_recovery_state_establishes_nothing(
        self, tmp_path: Path
    ) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            open_recovery_state(
                harness.writer,
                census_run_id=_RUN,
                recovery_state_id="blocked-state-01",
                scenario="t2_4_recovery_action",
                action_taken="adopt-orphan",
                detail="an unadjudicated mutation",
                relative_path="raw/bulk/example",
            )
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert _condition(state, "8.2").status == "NOT MET"
            assert "remain blocked" in _condition(state, "8.2").detail


# =========================================================================== #
# Decision 064 §6 — condition 8.8 counts per identity, never per route
# =========================================================================== #
class TestIdentityLevelHeadroom:
    def test_an_outstanding_identity_is_counted_even_when_its_route_holds_a_failure(
        self, tmp_path: Path
    ) -> None:
        """The pre-correction defect, stated as its own test.

        One route, one planned identity, and one committed row for a *different* identity on that
        route. Route-level counting read the row as completion and reported nothing remaining;
        identity-level counting reports the one request that is genuinely still owed, charged its
        own route's `A_reachable`.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            source_id = _requests(harness.plan)[1]
            observation_id, _ = _singleton_observation_id(harness, source_id)
            _restate_identity(harness, observation_id, "https://www.sec.gov/retired-path")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.remaining_logical_requests == 1
            assert state.worst_case_remaining_attempts == derive_a_reachable(SOURCES[source_id])
            assert "1 logical request(s) remain" in _condition(state, "8.8").detail

    def test_a_fully_satisfied_plan_leaves_nothing_remaining(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            _register_terminal_run(harness)
            head = _write_receipts(tmp_path, _complete_receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.remaining_logical_requests == 0
            assert state.worst_case_remaining_attempts == 0
            assert _condition(state, "8.8").status == "MET"
            assert state.continuation_permitted is False

    def test_a_failed_row_never_counts_as_satisfaction(self, tmp_path: Path) -> None:
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            source_id = _requests(harness.plan)[1]
            observation_id, _ = _singleton_observation_id(harness, source_id)
            _set_outcome(harness, observation_id, "failed")
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.remaining_logical_requests == 1
            assert state.worst_case_remaining_attempts == derive_a_reachable(SOURCES[source_id])

    def test_an_identity_is_judged_on_its_newest_evidence_and_never_on_an_older_row(
        self, tmp_path: Path
    ) -> None:
        """The identity is decided once, on its newest usable row, with no fallback.

        Non-vacuity for the decided-once guard: the identity here has an older row that *would*
        satisfy it, and the walk must not reach for it. Falling back would report the identity
        satisfied on evidence that has been superseded by evidence which does not resolve, and
        under-counting the remainder is the wrong direction for a headroom check to be wrong in.

        The continuation surface judges the same identity the same way and reaches a *stricter*
        conclusion: a committed row whose object is absent is persistence-uncertain, so the whole
        proposal is `UNDETERMINED` and the transport remainder is deliberately empty. That is not
        the two surfaces disagreeing about the evidence — it is the difference between "how many
        planned identities are unsatisfied" and "what may lawfully be re-requested", and nothing
        may be re-requested from an uncertain state. The agreement property between the two
        remainders is asserted where it is meaningful, in the test below this one.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            source_id = _requests(harness.plan)[1]
            observation_id, _ = _singleton_observation_id(harness, source_id)
            _shadow_with_a_newer_unresolvable_row(harness, observation_id)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.remaining_logical_requests == 1, "the newest evidence does not resolve"
            assert state.worst_case_remaining_attempts == derive_a_reachable(SOURCES[source_id])
            assert state.determination == "UNDETERMINED"
            assert state.continuation_permitted is False

            proposal = _propose(harness, head)

            assert proposal.permitted is False
            assert proposal.determination == "UNDETERMINED"
            assert proposal.remaining == (), "nothing is re-requested from an uncertain state"

    def test_a_later_unusable_row_never_unsatisfies_an_identity_its_object_still_satisfies(
        self, tmp_path: Path
    ) -> None:
        """A quarantined retry after a good retrieval does not take the identity back.

        The newest row here is not usable, and it names the *same* stored object as the good row
        beneath it — so only the usable-outcome rule can exclude it. Excluding it is what the
        accepted snapshot store does when it looks for the latest usable observation, and the two
        surfaces have to agree: the object is still present and still satisfies the request, so the
        identity is satisfied and nothing is owed.
        """
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan))
            harness.flush_projection()
            source_id = _requests(harness.plan)[1]
            observation_id, _ = _singleton_observation_id(harness, source_id)
            _shadow_with_a_newer_unusable_row(harness, observation_id)
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)

            assert state.remaining_logical_requests == 0, "the good object still satisfies it"
            assert state.worst_case_remaining_attempts == 0
            proposal = _propose(harness, head)
            assert len(proposal.remaining) == 0, (
                "the continuation surface reaches the same conclusion from the same evidence"
            )

    def test_the_inspection_and_the_continuation_agree_on_the_remainder(
        self, tmp_path: Path
    ) -> None:
        """The two counts are the same count. That is the property §10 actually asks for."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan)[:3], headroom=3)
            harness.flush_projection()
            head = _write_receipts(tmp_path, _receipt(harness.plan))
            harness.release()

            state = _inspect(harness, head)
            proposal = _propose(harness, head)

            assert state.remaining_logical_requests == len(proposal.remaining)
            assert state.worst_case_remaining_attempts == proposal.worst_case_remaining_attempts

    def test_a_remainder_beyond_the_ceiling_is_still_refused(self, tmp_path: Path) -> None:
        """The ceiling semantics are untouched: a remainder that does not fit is not met."""
        with _harness(tmp_path) as harness:
            harness.run(_success_script(harness.plan)[:1], headroom=1)
            harness.flush_projection()
            head = _write_receipts(
                tmp_path,
                _receipt(
                    harness.plan,
                    actual_logical_request_count=53,
                    actual_physical_attempt_count=53,
                    actual_per_route={
                        "sec_bulk_submissions": {
                            "logical_request_count": 53,
                            "physical_attempt_count": 53,
                        },
                    },
                    response_classification_totals={
                        "proceed": 53,
                        "retry": 0,
                        "retry_after": 0,
                        "cooldown": 0,
                        "fail": 0,
                        "quarantine": 0,
                    },
                    status_code_totals={"200": 53},
                    raw_object_count=53,
                ),
            )
            harness.release()

            state = _inspect(harness, head)

            assert _condition(state, "8.8").status == "NOT MET"
            assert state.consumed_physical_attempts == 53
            assert state.remaining_logical_requests > 0
