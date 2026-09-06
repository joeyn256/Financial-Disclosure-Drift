"""D151-C31R2-R21-E6R3: the successor producer -> consumer compatibility bridge.

Owner ruling ``D151_R21_E6R3_R1_SUCCESSOR_COMPATIBILITY_CERTIFICATE``.

Exact producer/consumer repository equality remains the DEFAULT. A successor calibration final
may consume level-1 inputs produced under a different revision ONLY through an explicit,
authenticated compatibility certificate that names exactly one producer revision, one consumer
revision, one plan, one schedule, one predecessor and one input estate.

These are falsification tests: every one of them exists to establish that some specific wrong
certificate, wrong revision or wrong estate is REFUSED, and that the default path is unchanged.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from disclosure_drift.m3 import chunk_multipass as cm
from disclosure_drift.m3.chunk_evidence import ArtifactManifest, ExecutionContract
from disclosure_drift.m3.chunk_multipass import (
    CALIBRATION_SUBSET_CLASSIFICATIONS,
    CALIBRATION_SUBSET_RESULT_CONTRACT,
    INTERMEDIATE_RECEIPT_FILENAME,
    SUCCESSOR_COMPATIBILITY_BRIDGE_ID,
    SUCCESSOR_COMPATIBILITY_CERTIFICATE_CONTRACT,
    SUCCESSOR_ROUTE_CALIBRATION,
    SUCCESSOR_ROUTE_PRODUCTION,
    CalibrationSubsetResult,
    ChunkMultipassError,
    SuccessorCompatibilityCertificate,
    SuccessorFinalRequest,
    _authenticate_successor_compatibility_certificate,
    _compatibility_provenance,
    _require_seed_identity,
    read_successor_compatibility_certificate,
)
from disclosure_drift.m3.repository_identity import RepositoryIdentity

PRODUCER_HEAD = "7a1fcf0831e9159a7b9f4ee9592b75497a1d5178"
PRODUCER_TREE = "f1d7c1125982c1d9e5e30bb19d972653a0e2dc8c"
CONSUMER_HEAD = "c386988fb5d20fe26433a1ca4d00bdc57795248d"
CONSUMER_TREE = "fc3861b4aee49656883672ec0a6e5f743e1726e7"
CATALOG_SHA = "a" * 64
PLAN_DIGEST = "b" * 64
SCHEDULE_DIGEST = "c" * 64
PREDECESSOR_RUN = "d151-c31r2-fixture"
TIP_IDENTITY = "d" * 64
AUDIT_SHA = "e" * 64


def _repository(head: str = CONSUMER_HEAD, tree: str = CONSUMER_TREE) -> RepositoryIdentity:
    return RepositoryIdentity(
        contract="m3.3-repository-identity/1",
        head_sha=head,
        tree_sha=tree,
        dirty_tracked_paths=(),
        untracked_paths=(),
    )


def _contract(catalog_sha256: str = CATALOG_SHA) -> ExecutionContract:
    return ExecutionContract(
        contract_identity="f" * 64,
        parser_id="census",
        parser_version="1",
        evidence_contract="m3.3-evidence/1",
        compact_evidence=True,
        batch_size=1000,
        catalog_source_sha256=catalog_sha256,
        migration_head=15,
    )


def _intermediate(tmp_path: Path, group: int, *, head: str, tree: str, body: str) -> Any:
    """A stand-in for one resolved IntermediateInput.

    Only the four attributes the authenticator reads are provided. The receipt FILE is real, so
    the digest the authenticator measures is a real measurement of real bytes.
    """
    directory = tmp_path / f"group-{group:04d}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / INTERMEDIATE_RECEIPT_FILENAME).write_text(body)
    return SimpleNamespace(
        group_id=f"group-{group:04d}",
        directory=directory,
        receipt=SimpleNamespace(repository_head_sha=head, repository_tree_sha=tree),
    )


def _witness(chunk: int, identity: str) -> Any:
    return SimpleNamespace(
        chunk_id=f"chunk-{chunk:04d}", witness=SimpleNamespace(witness_identity=identity)
    )


def _estate(
    tmp_path: Path,
    *,
    groups: int = 3,
    chunks: int = 4,
    head: str = PRODUCER_HEAD,
    tree: str = PRODUCER_TREE,
) -> tuple[list, list]:
    intermediates = [
        _intermediate(tmp_path, g, head=head, tree=tree, body=json.dumps({"group": g}))
        for g in range(groups)
    ]
    witnesses = [_witness(c, hashlib.sha256(f"w{c}".encode()).hexdigest()) for c in range(chunks)]
    return intermediates, witnesses


def _certificate(
    intermediates: list, witnesses: list, **overrides: Any
) -> SuccessorCompatibilityCertificate:
    fields: dict[str, Any] = {
        "contract": SUCCESSOR_COMPATIBILITY_CERTIFICATE_CONTRACT,
        "bridge_id": SUCCESSOR_COMPATIBILITY_BRIDGE_ID,
        "producer_head_sha": PRODUCER_HEAD,
        "producer_tree_sha": PRODUCER_TREE,
        "consumer_head_sha": CONSUMER_HEAD,
        "consumer_tree_sha": CONSUMER_TREE,
        "plan_digest": PLAN_DIGEST,
        "schedule_digest": SCHEDULE_DIGEST,
        "predecessor_run_id": PREDECESSOR_RUN,
        "predecessor_tip_identity": TIP_IDENTITY,
        "intermediate_receipt_identities": {
            item.group_id: hashlib.sha256(
                (item.directory / INTERMEDIATE_RECEIPT_FILENAME).read_bytes()
            ).hexdigest()
            for item in intermediates
        },
        "retained_witness_identities": {
            item.chunk_id: item.witness.witness_identity for item in witnesses
        },
        "compatibility_audit_sha256": AUDIT_SHA,
        "created_at_utc": "2026-09-06T12:45:52Z",
        "certificate_identity": "",
    }
    fields.update(overrides)
    draft = SuccessorCompatibilityCertificate(**fields)
    if overrides.get("certificate_identity"):
        return draft
    return SuccessorCompatibilityCertificate(**{**fields, "certificate_identity": draft.identity()})


def _plan(digest: str = PLAN_DIGEST) -> Any:
    return SimpleNamespace(plan_digest=digest)


def _schedule(digest: str = SCHEDULE_DIGEST) -> Any:
    return SimpleNamespace(schedule_digest=digest)


def _request(tmp_path: Path, **overrides: Any) -> SuccessorFinalRequest:
    fields: dict[str, Any] = {
        "route": SUCCESSOR_ROUTE_CALIBRATION,
        "plan_path": str(tmp_path / "chunk_plan.json"),
        "schedule_path": str(tmp_path / "merge_schedule.json"),
        "intermediates_root": str(tmp_path / "intermediates"),
        "internal_root": str(tmp_path / "chunks"),
        "external_root": None,
        "operational_catalog": str(tmp_path / "catalog.sqlite3"),
        "world_directory": str(tmp_path / "world"),
        "stage_receipt_root": str(tmp_path / "receipts"),
        "run_id": "d151-fixture-successor",
        "predecessor_run_id": PREDECESSOR_RUN,
        "predecessor_checkpoint_count": 3,
        "predecessor_tip_ordinal": 2,
        "predecessor_tip_identity": TIP_IDENTITY,
        "predecessor_completed_group_count": 3,
        "cache_bytes": 536_870_912,
        "repository_head_sha": CONSUMER_HEAD,
        "repository_tree_sha": CONSUMER_TREE,
        "storage_requirements": {
            "internal_reserve_bytes": 8_589_934_592,
            "level_one_peak_ratio": 1.125,
            "level_two_peak_ratio": 1.25,
            "level_one_transient_bytes": 2_147_483_648,
            "level_two_transient_bytes": 21_474_836_480,
        },
        "expected_sqlite_temp_binding": {},
        "statement_observability": {
            "statement_progress_interval_seconds": 5,
            "progress_handler_vm_steps": 10_000,
            "wal_watchdog_max_uncommitted_frames": 5_100_000,
            "expected_page_size_bytes": 4096,
        },
    }
    fields.update(overrides)
    return SuccessorFinalRequest(**fields)


def _sealed_certificate_file(
    tmp_path: Path, certificate: SuccessorCompatibilityCertificate, name: str = "certificate.json"
) -> tuple[Path, str]:
    """Write one certificate as a real file and return it with the SHA-256 of its BYTES."""
    path = tmp_path / name
    path.write_text(json.dumps(dict(certificate.as_record())))
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def _bridged_request(tmp_path: Path, sealed: str, **overrides: Any) -> SuccessorFinalRequest:
    """A request that seals ``sealed`` as the certificate FILE digest -- the R21-E6R3-C1 source."""
    return _request(
        tmp_path,
        compatibility_certificate_path=str(tmp_path / "certificate.json"),
        compatibility_certificate_sha256=sealed,
        **overrides,
    )


def _sealed_result(
    provenance: Any, *, head: str = CONSUMER_HEAD, tree: str = CONSUMER_TREE
) -> CalibrationSubsetResult:
    """One sealed terminal result, the shape ``_publish_calibration_result`` writes.

    Every field is a placeholder except the ones this file is about: the successor's own
    repository identity -- which is always the CONSUMER revision -- and the compatibility
    provenance beside it.
    """
    result = CalibrationSubsetResult(
        contract=CALIBRATION_SUBSET_RESULT_CONTRACT,
        classifications=CALIBRATION_SUBSET_CLASSIFICATIONS,
        plan_digest=PLAN_DIGEST,
        merge_schedule_digest=SCHEDULE_DIGEST,
        run_id="d151-fixture-successor",
        source_instance_id="fixture-instance",
        source_observation_id="fixture-observation",
        source_sha256="1" * 64,
        source_byte_length=1,
        member_order_digest="2" * 64,
        selected_member_order_digest="3" * 64,
        shard_parent_binding_digest="4" * 64,
        primary_prefix_members=1,
        selected_shard_members=1,
        excluded_shard_members=0,
        selected_members=2,
        full_total_members=3,
        repository_head_sha=head,
        repository_tree_sha=tree,
        catalog_source_sha256=CATALOG_SHA,
        execution_contract_identity="f" * 64,
        chunk_count=34,
        intermediate_count=5,
        parser_run_id="fixture-parser-run",
        run_outcome="ok",
        parser_state_after="chunk_local",
        world_parser_state="chunk_local",
        members=1,
        records=1,
        parsed_records=1,
        quarantined_records=0,
        omitted_field_observations=0,
        materialized_field_observations=0,
        completeness_digest="5" * 64,
        member_manifest_digest="6" * 64,
        table_row_counts={"fixture_table": 1},
        first_witness_accessions_corrected=0,
        first_witness_rows_staged=0,
        evidence_members_corrected=0,
        evidence_delta=0,
        storage_admission={"level": "level_two"},
        admission_event_identity="7" * 64,
        envelope_sha256="8" * 64,
        pid=1,
        rss_peak_bytes=1,
        started_at_utc="2026-09-06T00:00:00Z",
        completed_at_utc="2026-09-06T01:00:00Z",
        manifest=ArtifactManifest.from_record({"entries": []}),
        status="complete",
        result_identity="",
        successor_observability={"status": "clean"},
        compatibility_provenance=provenance,
    )
    return replace(result, result_identity=result.identity())


def _authenticate(
    certificate: SuccessorCompatibilityCertificate,
    intermediates: list,
    witnesses: list,
    *,
    request: SuccessorFinalRequest,
    plan: Any = None,
    schedule: Any = None,
    route: str = SUCCESSOR_ROUTE_CALIBRATION,
) -> None:
    _authenticate_successor_compatibility_certificate(
        certificate,
        route=route,
        plan=plan or _plan(),
        schedule=schedule or _schedule(),
        request=request,
        intermediates=intermediates,
        witnesses=witnesses,
    )


# ---------------------------------------------------------------- A, B: the default path
def test_a_exact_producer_equals_consumer_still_passes_without_a_certificate() -> None:
    """A: the accepted exact-equality path is untouched and needs no certificate."""
    _require_seed_identity(
        label="successor-final",
        repository=_repository(head=PRODUCER_HEAD, tree=PRODUCER_TREE),
        recorded_head=PRODUCER_HEAD,
        recorded_tree=PRODUCER_TREE,
        contract=_contract(),
        catalog_sha256=CATALOG_SHA,
    )


def test_b_mismatched_revisions_without_a_certificate_still_refuse() -> None:
    """B: without a certificate a producer/consumer mismatch refuses exactly as before."""
    with pytest.raises(ChunkMultipassError, match="executed under repository"):
        _require_seed_identity(
            label="successor-final",
            repository=_repository(),
            recorded_head=PRODUCER_HEAD,
            recorded_tree=PRODUCER_TREE,
            contract=_contract(),
            catalog_sha256=CATALOG_SHA,
        )


def test_b2_catalog_seed_digest_is_still_checked_on_both_paths(tmp_path: Path) -> None:
    """The seed-catalog byte check is not part of the bridge and applies to both paths."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    # Each case reaches the catalog check only once its own identity check has passed: the
    # default path needs producer == consumer, the bridged path needs the certified pair.
    cases = (
        (None, _repository(head=PRODUCER_HEAD, tree=PRODUCER_TREE)),
        (certificate, _repository()),
    )
    for cert, repository in cases:
        with pytest.raises(ChunkMultipassError, match="identified by its BYTES"):
            _require_seed_identity(
                label="successor-final",
                repository=repository,
                recorded_head=PRODUCER_HEAD,
                recorded_tree=PRODUCER_TREE,
                contract=_contract(catalog_sha256="9" * 64),
                catalog_sha256=CATALOG_SHA,
                certificate=cert,
            )


# ---------------------------------------------------------------- C: the bridge admits
def test_c_approved_producer_estate_with_a_valid_certificate_passes(tmp_path: Path) -> None:
    """C: the exact certified producer, consumer, plan, schedule, predecessor and estate pass."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))
    _require_seed_identity(
        label="successor-final",
        repository=_repository(),
        recorded_head=PRODUCER_HEAD,
        recorded_tree=PRODUCER_TREE,
        contract=_contract(),
        catalog_sha256=CATALOG_SHA,
        certificate=certificate,
    )


# ---------------------------------------------------------------- D-G: revision falsification
def test_d_wrong_producer_head_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, producer_head_sha="0" * 40)
    with pytest.raises(ChunkMultipassError, match="certifies producer"):
        _require_seed_identity(
            label="successor-final",
            repository=_repository(),
            recorded_head=PRODUCER_HEAD,
            recorded_tree=PRODUCER_TREE,
            contract=_contract(),
            catalog_sha256=CATALOG_SHA,
            certificate=certificate,
        )


def test_e_wrong_producer_tree_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, producer_tree_sha="0" * 40)
    with pytest.raises(ChunkMultipassError, match="certifies producer"):
        _require_seed_identity(
            label="successor-final",
            repository=_repository(),
            recorded_head=PRODUCER_HEAD,
            recorded_tree=PRODUCER_TREE,
            contract=_contract(),
            catalog_sha256=CATALOG_SHA,
            certificate=certificate,
        )


def test_f_mixed_producer_identities_across_intermediates_refuse(tmp_path: Path) -> None:
    """F: every level-1 input must carry the ONE certified producer revision."""
    intermediates, witnesses = _estate(tmp_path, groups=2)
    stray = _intermediate(tmp_path, 2, head="0" * 40, tree=PRODUCER_TREE, body='{"group": 2}')
    intermediates.append(stray)
    certificate = _certificate(intermediates, witnesses)
    with pytest.raises(ChunkMultipassError, match="mixed set is refused"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


@pytest.mark.parametrize(
    ("head", "tree"),
    [("0" * 40, CONSUMER_TREE), (CONSUMER_HEAD, "0" * 40), ("0" * 40, "0" * 40)],
)
def test_g_wrong_consumer_head_or_tree_refuses(tmp_path: Path, head: str, tree: str) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    with pytest.raises(ChunkMultipassError, match="certifies consumer"):
        _require_seed_identity(
            label="successor-final",
            repository=_repository(head=head, tree=tree),
            recorded_head=PRODUCER_HEAD,
            recorded_tree=PRODUCER_TREE,
            contract=_contract(),
            catalog_sha256=CATALOG_SHA,
            certificate=certificate,
        )


# ---------------------------------------------------------------- H, I: sealing falsification
def test_h_certificate_sha_mismatch_refuses(tmp_path: Path) -> None:
    """H: the certificate is admitted by the BYTES the request sealed, never by its path."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    path = tmp_path / "certificate.json"
    path.write_text(json.dumps(dict(certificate.as_record())))
    with pytest.raises(ChunkMultipassError, match="the execution request sealed"):
        read_successor_compatibility_certificate(path, sealed_sha256="0" * 64)


def test_i_altering_the_certificate_after_sealing_refuses(tmp_path: Path) -> None:
    """I: an edit after sealing breaks BOTH the sealed digest and the self-identity."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    path = tmp_path / "certificate.json"
    body = dict(certificate.as_record())
    path.write_text(json.dumps(body))
    sealed = hashlib.sha256(path.read_bytes()).hexdigest()
    # the file the request sealed reads cleanly
    assert read_successor_compatibility_certificate(path, sealed_sha256=sealed) == certificate
    # now tamper, keeping the sealed identity field
    body["producer_head_sha"] = "0" * 40
    path.write_text(json.dumps(body))
    with pytest.raises(ChunkMultipassError, match="the execution request sealed"):
        read_successor_compatibility_certificate(path, sealed_sha256=sealed)
    # and even re-sealing the digest cannot save it: the self-identity no longer matches
    with pytest.raises(ChunkMultipassError, match="altered after sealing"):
        read_successor_compatibility_certificate(
            path, sealed_sha256=hashlib.sha256(path.read_bytes()).hexdigest()
        )


def test_i2_a_certificate_citing_another_ruling_or_contract_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    for field, match in (("bridge_id", "cites ruling"), ("contract", "names contract")):
        certificate = _certificate(intermediates, witnesses, **{field: "something-else"})
        with pytest.raises(ChunkMultipassError, match=match):
            SuccessorCompatibilityCertificate.from_record(dict(certificate.as_record()))


def test_i3_a_certificate_of_the_wrong_shape_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    record = dict(_certificate(intermediates, witnesses).as_record())
    record.pop("plan_digest")
    with pytest.raises(ChunkMultipassError, match="is exact"):
        SuccessorCompatibilityCertificate.from_record(record)
    record = dict(_certificate(intermediates, witnesses).as_record())
    record["extra"] = 1
    with pytest.raises(ChunkMultipassError, match="is exact"):
        SuccessorCompatibilityCertificate.from_record(record)


# ---------------------------------------------------------------- J-M: estate falsification
def test_j_wrong_plan_digest_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, plan_digest="9" * 64)
    with pytest.raises(ChunkMultipassError, match="binds plan"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


def test_k_wrong_schedule_digest_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, schedule_digest="9" * 64)
    with pytest.raises(ChunkMultipassError, match="binds schedule"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


def test_l_changed_intermediate_bytes_refuse(tmp_path: Path) -> None:
    """L: the certificate names each level-1 receipt by digest; a changed receipt refuses."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    (intermediates[1].directory / INTERMEDIATE_RECEIPT_FILENAME).write_text('{"group": "moved"}')
    with pytest.raises(ChunkMultipassError, match="differing by digest"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


def test_l2_an_interchanged_or_extra_intermediate_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    with pytest.raises(ChunkMultipassError, match="level-1 intermediate"):
        _authenticate(certificate, intermediates[:2], witnesses, request=_request(tmp_path))


def test_l3_a_changed_retained_witness_identity_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    witnesses[2] = _witness(2, "0" * 64)
    with pytest.raises(ChunkMultipassError, match="differing by identity"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


def test_m_a_certificate_from_another_predecessor_run_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, predecessor_run_id="d151-other-run")
    with pytest.raises(ChunkMultipassError, match="binds predecessor run"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


def test_m2_a_certificate_bound_to_another_checkpoint_tip_refuses(tmp_path: Path) -> None:
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses, predecessor_tip_identity="9" * 64)
    with pytest.raises(ChunkMultipassError, match="predecessor checkpoint tip"):
        _authenticate(certificate, intermediates, witnesses, request=_request(tmp_path))


# ---------------------------------------------------------------- N: dual provenance
def test_n_a_bridged_result_records_both_producer_and_consumer_identity(tmp_path: Path) -> None:
    """N: a bridged successor never pretends its inputs were built under the consumer."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    _path, sealed = _sealed_certificate_file(tmp_path, certificate)
    provenance = _compatibility_provenance(
        certificate,
        request=_bridged_request(tmp_path, sealed),
        repository=_repository(),
        intermediates=intermediates,
    )
    assert provenance == {
        "compatibility_bridge_id": SUCCESSOR_COMPATIBILITY_BRIDGE_ID,
        "compatibility_certificate_sha256": sealed,
        "compatibility_certificate_identity": certificate.certificate_identity,
        "l1_producer_head": PRODUCER_HEAD,
        "l1_producer_tree": PRODUCER_TREE,
        "successor_consumer_head": CONSUMER_HEAD,
        "successor_consumer_tree": CONSUMER_TREE,
        "compatibility_audit_sha256": AUDIT_SHA,
        "certified_intermediate_count": len(intermediates),
    }
    assert provenance["l1_producer_head"] != provenance["successor_consumer_head"]


def test_n2_an_exact_revision_run_records_no_bridge_provenance(tmp_path: Path) -> None:
    """An unbridged run carries no provenance key at all, so it cannot look bridged."""
    intermediates, _ = _estate(tmp_path)
    assert (
        _compatibility_provenance(
            None,
            request=_request(tmp_path),
            repository=_repository(),
            intermediates=intermediates,
        )
        is None
    )


# ---------------------------------------------------------------- O: scope of the bridge
def test_o_the_bridge_serves_the_calibration_successor_only(tmp_path: Path) -> None:
    """O: the production route has no bridge, so it can never present a certificate."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    with pytest.raises(ChunkMultipassError, match="production route has no bridge"):
        _authenticate(
            certificate,
            intermediates,
            witnesses,
            request=_request(tmp_path, route=SUCCESSOR_ROUTE_PRODUCTION),
            route=SUCCESSOR_ROUTE_PRODUCTION,
        )


def test_o2_no_chunk_or_level_one_producer_reads_a_certificate() -> None:
    """O: only the successor context resolves a certificate; no chunk/L1 path can reach one."""
    source = Path("src/disclosure_drift/m3/chunk_multipass.py").read_text()
    consumers = [
        line.strip()
        for line in source.splitlines()
        if "compatibility_certificate_path" in line and "record[" not in line
    ]
    # the dataclass field, its docstring mention, the paired-field guard, as_record, from_record
    # and the ONE read inside _resolve_successor_context.
    assert any("read_successor_compatibility_certificate(" in line for line in source.splitlines())
    for entry in (
        "run_calibration_subset_chunk",
        "run_calibration_subset_group_merge",
        "run_calibration_subset_chunks",
    ):
        start = source.index(f"def {entry}(")
        body = source[start : start + 6000]
        assert "compatibility_certificate" not in body, (
            f"{entry} must not be able to reach the compatibility bridge"
        )
    assert consumers, "the request field must exist"


def test_o3_consolidation_and_level_one_modules_never_mention_the_bridge() -> None:
    for module in ("chunk_consolidation.py", "chunk_execution.py", "chunk_plan.py"):
        text = Path(f"src/disclosure_drift/m3/{module}").read_text()
        assert "compatibility_certificate" not in text
        assert SUCCESSOR_COMPATIBILITY_BRIDGE_ID not in text


# ---------------------------------------------------------------- P: clean-repo admission
def test_p_the_clean_repository_gate_runs_before_any_certificate_is_read() -> None:
    """P: a dirty working tree still refuses; the bridge cannot be reached before that gate."""
    source = Path("src/disclosure_drift/m3/chunk_multipass.py").read_text()
    start = source.index("def _resolve_successor_context(")
    body = source[start : source.index("\ndef ", start + 10)]
    authenticate = body.index("_authenticate_running_repository(")
    certificate = body.index("read_successor_compatibility_certificate(")
    assert authenticate < certificate, (
        "the running-repository authentication must precede the certificate read, so a dirty or "
        "unexpected checkout refuses before any bridge is consulted"
    )


def test_p2_the_certificate_carries_no_working_tree_claim(tmp_path: Path) -> None:
    """A certificate names revisions only; it can never assert that a tree is clean."""
    intermediates, witnesses = _estate(tmp_path)
    record = dict(_certificate(intermediates, witnesses).as_record())
    assert not [key for key in record if "dirty" in key or "untracked" in key or "clean" in key]


# ---------------------------------------------------------------- request wiring
def test_request_without_a_certificate_renders_exactly_as_before(tmp_path: Path) -> None:
    """The two keys appear only when a certificate is carried, so old requests are unchanged."""
    record = dict(_request(tmp_path).as_record())
    assert "compatibility_certificate_path" not in record
    assert "compatibility_certificate_sha256" not in record
    assert SuccessorFinalRequest.from_record(record).compatibility_certificate_path is None


def test_request_round_trips_a_certificate_pair(tmp_path: Path) -> None:
    request = _request(
        tmp_path,
        compatibility_certificate_path=str(tmp_path / "certificate.json"),
        compatibility_certificate_sha256="1" * 64,
    )
    record = dict(request.as_record())
    assert record["compatibility_certificate_sha256"] == "1" * 64
    assert SuccessorFinalRequest.from_record(record) == request


@pytest.mark.parametrize(
    "overrides",
    [
        {"compatibility_certificate_path": "certificate.json"},
        {"compatibility_certificate_sha256": "1" * 64},
    ],
)
def test_request_refuses_a_half_specified_certificate(tmp_path: Path, overrides: dict) -> None:
    with pytest.raises(ChunkMultipassError, match="BOTH the compatibility certificate path"):
        _request(tmp_path, **overrides)


def test_absent_certificate_file_refuses(tmp_path: Path) -> None:
    with pytest.raises(ChunkMultipassError, match="existing regular file"):
        read_successor_compatibility_certificate(tmp_path / "missing.json", sealed_sha256="1" * 64)


# --------------------------------------------------- Q: R21-E6R3-C1 MAJOR-1, the two digests
#: The two digests of the certificate the owner accepted for the historical bridge. They are
#: pinned here as a regression anchor precisely because they are DIFFERENT values that a single
#: mislabelled key once conflated: the first is the SHA-256 of the certificate FILE's bytes, the
#: second is the certificate's own sealed self-identity over its canonical record.
HISTORICAL_CERTIFICATE_FILE_SHA256 = (
    "2be2641b55faacee8de75f8c67d321835d4e3e1e60c5675c286cab89b14bfc2e"
)
HISTORICAL_CERTIFICATE_SELF_IDENTITY = (
    "e51c94d82669c96077de113ddcd2b00bf9f23f6c7d951e1522c15b7866725175"
)


def test_q_a_certificate_file_digest_is_never_its_self_identity(tmp_path: Path) -> None:
    """MAJOR-1: the two digests answer different questions and are different values.

    The file digest identifies the exact BYTES the request sealed; the self-identity identifies
    the RECORD those bytes decode to. One rendering of a record is not the record.
    """
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    _path, sealed = _sealed_certificate_file(tmp_path, certificate)
    assert sealed != certificate.certificate_identity
    # and for the certificate the owner actually accepted
    assert HISTORICAL_CERTIFICATE_FILE_SHA256 != HISTORICAL_CERTIFICATE_SELF_IDENTITY


def test_q2_provenance_takes_the_file_digest_from_the_sealed_request(tmp_path: Path) -> None:
    """MAJOR-1: the persisted file digest is the sealed request value, not a re-derivation.

    ``read_successor_compatibility_certificate`` refuses unless the bytes it captured digest to
    the request's sealed value, so that value IS the digest of the authenticated buffer. The
    provenance carries exactly it, and carries the self-identity separately.
    """
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    path, sealed = _sealed_certificate_file(tmp_path, certificate)
    request = _bridged_request(tmp_path, sealed)
    parsed = read_successor_compatibility_certificate(path, sealed_sha256=sealed)
    provenance = _compatibility_provenance(
        parsed, request=request, repository=_repository(), intermediates=intermediates
    )
    assert provenance is not None
    assert (
        provenance["compatibility_certificate_sha256"] == request.compatibility_certificate_sha256
    )
    assert provenance["compatibility_certificate_identity"] == parsed.certificate_identity
    assert (
        provenance["compatibility_certificate_sha256"]
        != provenance["compatibility_certificate_identity"]
    )


def test_q3_the_file_digest_cannot_be_derived_from_the_certificate_record(tmp_path: Path) -> None:
    """MAJOR-1: two renderings of ONE record share a self-identity and differ in file digest.

    This is why the file digest must flow from the sealed, authenticated bytes: nothing in the
    certificate's semantic fields determines it.
    """
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    compact = tmp_path / "compact.json"
    compact.write_text(json.dumps(dict(certificate.as_record()), separators=(",", ":")))
    spaced = tmp_path / "spaced.json"
    spaced.write_text(json.dumps(dict(certificate.as_record()), indent=2))
    compact_sha = hashlib.sha256(compact.read_bytes()).hexdigest()
    spaced_sha = hashlib.sha256(spaced.read_bytes()).hexdigest()
    assert compact_sha != spaced_sha
    one = read_successor_compatibility_certificate(compact, sealed_sha256=compact_sha)
    other = read_successor_compatibility_certificate(spaced, sealed_sha256=spaced_sha)
    assert one == other
    # each run persists the digest of the bytes ITS request sealed
    for path, sha in ((compact, compact_sha), (spaced, spaced_sha)):
        parsed = read_successor_compatibility_certificate(path, sealed_sha256=sha)
        provenance = _compatibility_provenance(
            parsed,
            request=_bridged_request(tmp_path, sha),
            repository=_repository(),
            intermediates=intermediates,
        )
        assert provenance is not None
        assert provenance["compatibility_certificate_sha256"] == sha
        assert provenance["compatibility_certificate_identity"] == certificate.certificate_identity


def test_q4_a_certificate_without_a_sealed_request_digest_refuses(tmp_path: Path) -> None:
    """MAJOR-1: provenance is never published with a certificate whose digest was never sealed."""
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    with pytest.raises(ChunkMultipassError, match="no sealed digest"):
        _compatibility_provenance(
            certificate,
            request=_request(tmp_path),
            repository=_repository(),
            intermediates=intermediates,
        )


def test_q5_the_terminal_result_durably_persists_both_digests(tmp_path: Path) -> None:
    """MAJOR-1, durability: both keys survive the terminal's canonical write and re-read.

    ``_publish_calibration_result`` seals the result, writes its canonical bytes and reads them
    back through :func:`read_calibration_subset_result` as its LAST act. This exercises exactly
    that round trip, so a provenance block that could not be re-read would fail here rather than
    at the end of a real merge.
    """
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    _path, sealed = _sealed_certificate_file(tmp_path, certificate)
    provenance = _compatibility_provenance(
        certificate,
        request=_bridged_request(tmp_path, sealed),
        repository=_repository(),
        intermediates=intermediates,
    )
    bridged = _sealed_result(provenance)
    path = tmp_path / cm.CALIBRATION_SUBSET_RESULT_FILENAME
    cm.write_once_canonical_json(path, dict(bridged.as_record()))
    reread = cm.read_calibration_subset_result(path)
    assert reread == bridged
    recorded = reread.compatibility_provenance
    assert recorded is not None
    assert recorded["compatibility_certificate_sha256"] == sealed
    assert recorded["compatibility_certificate_identity"] == certificate.certificate_identity
    assert sealed != certificate.certificate_identity
    # the durable record states both revisions, so it can never read as a same-revision run
    assert recorded["l1_producer_head"] == PRODUCER_HEAD
    assert recorded["successor_consumer_head"] == CONSUMER_HEAD
    assert reread.repository_head_sha == CONSUMER_HEAD


def test_q6_an_unbridged_terminal_result_keeps_its_pre_bridge_shape(tmp_path: Path) -> None:
    """An exact-revision terminal carries neither key and keeps its pre-bridge identity."""
    unbridged = _sealed_result(None)
    record = dict(unbridged.as_record())
    assert "compatibility_provenance" not in record
    path = tmp_path / cm.CALIBRATION_SUBSET_RESULT_FILENAME
    cm.write_once_canonical_json(path, record)
    assert cm.read_calibration_subset_result(path) == unbridged
    bridged = _sealed_result({"compatibility_bridge_id": SUCCESSOR_COMPATIBILITY_BRIDGE_ID})
    assert unbridged.result_identity != bridged.result_identity


# ------------------------------------------ R: R21-E6R3-C1 MAJOR-2, hash and parse one buffer
def test_r_the_parsed_record_comes_from_the_bytes_that_were_authenticated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MAJOR-2: a second read of the path can never reach the parser.

    The certificate on disk is authentic and digests to the sealed value. Any attempt to obtain
    its content through a SECOND read is poisoned here with a different -- but internally
    self-consistent, so otherwise admissible -- certificate. A reader that hashed one read and
    parsed another would return the poisoned producer; this one returns the authentic estate,
    because it hashes and parses the same captured buffer.
    """
    intermediates, witnesses = _estate(tmp_path)
    certificate = _certificate(intermediates, witnesses)
    path, sealed = _sealed_certificate_file(tmp_path, certificate)
    poison = json.dumps(
        dict(_certificate(intermediates, witnesses, producer_head_sha="0" * 40).as_record())
    ).encode("utf-8")
    real_read_bytes = Path.read_bytes

    def poisoned(self: Path) -> bytes:
        return poison if self == path else real_read_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", poisoned)
    parsed = read_successor_compatibility_certificate(path, sealed_sha256=sealed)
    assert parsed == certificate
    assert parsed.producer_head_sha == PRODUCER_HEAD


def test_r2_the_certificate_path_is_read_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MAJOR-2: one open of the certificate, however opened; there is no second window."""
    intermediates, witnesses = _estate(tmp_path)
    path, sealed = _sealed_certificate_file(tmp_path, _certificate(intermediates, witnesses))
    opens: list[str] = []
    real_os_open = os.open
    real_path_open = Path.open
    real_read_bytes = Path.read_bytes

    def counted_os_open(file: Any, *args: Any, **kwargs: Any) -> int:
        if str(file) == str(path):
            opens.append("os.open")
        return real_os_open(file, *args, **kwargs)

    def counted_path_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        if self == path:
            opens.append("Path.open")
        return real_path_open(self, *args, **kwargs)

    def counted_read_bytes(self: Path) -> bytes:
        if self == path:
            opens.append("Path.read_bytes")
        return real_read_bytes(self)

    monkeypatch.setattr(os, "open", counted_os_open)
    monkeypatch.setattr(Path, "open", counted_path_open)
    monkeypatch.setattr(Path, "read_bytes", counted_read_bytes)
    read_successor_compatibility_certificate(path, sealed_sha256=sealed)
    assert opens == ["os.open"], opens


def test_r3_a_symlinked_certificate_refuses(tmp_path: Path) -> None:
    """MAJOR-2: the final component is never followed, so a link is refused, not resolved."""
    intermediates, witnesses = _estate(tmp_path)
    real, sealed = _sealed_certificate_file(tmp_path, _certificate(intermediates, witnesses))
    link = tmp_path / "link.json"
    link.symlink_to(real)
    with pytest.raises(ChunkMultipassError, match="symbolic link"):
        read_successor_compatibility_certificate(link, sealed_sha256=sealed)


def test_r4_a_directory_standing_in_for_a_certificate_refuses(tmp_path: Path) -> None:
    directory = tmp_path / "certificate.json"
    directory.mkdir()
    with pytest.raises(ChunkMultipassError, match="regular file"):
        read_successor_compatibility_certificate(directory, sealed_sha256="0" * 64)


def test_r5_undecodable_certificate_bytes_refuse_after_the_digest_passes(tmp_path: Path) -> None:
    """The captured buffer is what is decoded; bytes that are not UTF-8 refuse, never coerce."""
    path = tmp_path / "certificate.json"
    path.write_bytes(bytes([0xFF, 0xFE]) + b" not utf-8")
    sealed = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ChunkMultipassError, match="not decodable UTF-8"):
        read_successor_compatibility_certificate(path, sealed_sha256=sealed)
