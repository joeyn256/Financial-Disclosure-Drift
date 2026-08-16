"""Milestone 3.1 execution receipts (``Docs/m3/execution_receipt_spec.md``, Decision 028 §§9-10).

The receipt specification's §0 rule -- *a receipt is operational evidence and never an input to any
governed identity* -- is a suite-level property (rehearsal A12), not a per-receipt check. What these
tests pin down is everything the module itself must guarantee:

- the §4 classification table, enforced exactly: every ``R`` field present, every ``C`` field
  present in its named modes and **absent** outside them, and no placeholder for an omission;
- §6 canonical serialization, byte-for-byte reproducible;
- §13's single integrity identity, recomputed over the preimage that excludes ``receipt_id``;
- §14's fail-closed validation, including the zero-network rule that makes a simulated total in a
  ``rehearsal`` receipt an error rather than a reporting convention;
- §5's prohibited-content scan, proven non-vacuous by positive controls; and
- §7's write-once immutability and read-only inspection.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.m3 import receipt as receipt_module
from disclosure_drift.m3.receipt import (
    COMPLETION_STATUSES,
    INTERRUPTION_STATES,
    INVOCATION_MODES,
    OPERATOR_RECEIPT_FILENAME,
    PHASES,
    READABLE_RECEIPT_SCHEMA_VERSIONS,
    RECEIPT_SCHEMA_VERSION,
    RECEIPT_SCHEMA_VERSION_V2,
    RECEIPT_SCHEMA_VERSION_V4,
    RESPONSE_CLASSIFICATION_BUCKETS,
    RUN_NAMESPACE_DIRNAME,
    SCHEMA_DRIFT_OUTCOMES,
    ZERO_NETWORK_MODES,
    ExecutionReceipt,
    ProhibitedReceiptContentError,
    ReceiptChainResolutionError,
    ReceiptValidationError,
    ReceiptWriteError,
    canonical_bytes,
    compute_receipt_id,
    content_derived_receipt_name,
    inspect_receipt,
    receipts_directory,
    resolve_predecessor_receipt,
    scan_for_prohibited_content,
    validate_receipt_document,
    write_receipt,
)

# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
_BASE: Mapping[str, Any] = {
    "command_name": "m3 rehearse",
    "command_version": "m3.1a/1.0",
    "phase": "M3.1A",
    "configuration_fingerprint": "a" * 64,
    "migration_chain_head": "0013_pilot_manifest",
    "started_at_utc": "2026-08-01T12:00:00Z",
    "completed_at_utc": "2026-08-01T12:00:04Z",
    "elapsed_seconds": 4.0,
    "actual_logical_request_count": 0,
    "actual_physical_attempt_count": 0,
    "completion_status": "complete",
}


def rehearsal(**overrides: Any) -> ExecutionReceipt:
    """A minimal valid ``rehearsal`` receipt."""
    fields: dict[str, Any] = {
        **_BASE,
        "invocation_mode": "rehearsal",
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "rehearsal_evidence_reference": "m3-1a-rehearsal-report-0001",
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def live(**overrides: Any) -> ExecutionReceipt:
    """A minimal valid ``live`` receipt."""
    fields: dict[str, Any] = {
        **_BASE,
        "command_name": "m3 acquire",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "source_registry_version": "sec-sources/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "parser_versions": {"submissions": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-0001",
        "request_plan_sha256": "b" * 64,
        "approved_request_ceiling": 40,
        "planned_logical_request_count": 8,
        "maximum_physical_attempt_count": 32,
        "planned_per_route": {"sec_full_index": 8},
        "actual_logical_request_count": 8,
        "actual_physical_attempt_count": 9,
        "actual_per_route": {
            "sec_full_index": {"logical_request_count": 8, "physical_attempt_count": 9},
        },
        "response_classification_totals": {
            "proceed": 8,
            "retry": 1,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": 8, "503": 1},
        "raw_object_count": 8,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def dry_run(**overrides: Any) -> ExecutionReceipt:
    """A minimal valid ``dry_run`` receipt: a plan, a budget, and no approved ceiling."""
    fields: dict[str, Any] = {
        **_BASE,
        "command_name": "m3 plan-requests",
        "phase": "M3.1B",
        "invocation_mode": "dry_run",
        "source_registry_version": "sec-sources/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-0001",
        "request_plan_sha256": "b" * 64,
        "planned_logical_request_count": 8,
        "maximum_physical_attempt_count": 32,
        "planned_per_route": {"sec_full_index": 8},
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def offline_execution(**overrides: Any) -> ExecutionReceipt:
    """A minimal valid ``offline_execution`` receipt."""
    fields: dict[str, Any] = {
        **_BASE,
        "command_name": "m3 execute",
        "phase": "M3.3A",
        "invocation_mode": "offline_execution",
        "quota_policy_version": "pilot-quota/1.0",
        "joint_selector_policy_version": "pilot-joint-selector/1.0",
        "replacement_signature_policy_version": "pilot-replacement-signature/1.0",
        "manifest_hash_policy_version": "pilot-manifest-hash/1.0",
        "selection_input_schema_version": "accession-selection-input/1.0",
        "parser_versions": {"submissions": "1.0"},
        "cohort_definition_digest": "e" * 64,
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def approval(**overrides: Any) -> ExecutionReceipt:
    """A minimal valid ``approval`` receipt."""
    fields: dict[str, Any] = {
        **_BASE,
        "command_name": "m3 approve-root",
        "phase": "M3.4A",
        "invocation_mode": "approval",
        "manifest_hash_policy_version": "pilot-manifest-hash/1.0",
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


_ZERO_NETWORK_BUILDERS: Mapping[str, Any] = {
    "rehearsal": rehearsal,
    "dry_run": dry_run,
    "offline_execution": offline_execution,
    "approval": approval,
}


# --------------------------------------------------------------------------- #
# Fixed vocabularies (§4, §12)
# --------------------------------------------------------------------------- #
def test_the_writer_schema_version_is_the_one_decision_055_fixed() -> None:
    """Decision 055 §7.1 unfroze the schema for exactly one successor. The writer emits it."""
    assert RECEIPT_SCHEMA_VERSION == "m3-execution-receipt/3.0"
    assert RECEIPT_SCHEMA_VERSION_V2 == "m3-execution-receipt/2.0"


def test_every_schema_version_remains_readable() -> None:
    """`2.0` and `3.0` stay readable; the reader dispatches on the version it finds (§7.1).

    Accepted Decision 094 §10.1 adds `4.0` as a **readable** successor for the two PRE-E0
    commands. The writer constant asserted above is unchanged and still emits `3.0`, which is
    the property that actually matters: adding a version a reader accepts does not change what
    any existing command writes.
    """
    assert READABLE_RECEIPT_SCHEMA_VERSIONS == (
        "m3-execution-receipt/2.0",
        "m3-execution-receipt/3.0",
        "m3-execution-receipt/4.0",
    )
    assert RECEIPT_SCHEMA_VERSION_V4 == "m3-execution-receipt/4.0"


def test_the_enumerations_are_exactly_the_specified_value_sets() -> None:
    assert set(INVOCATION_MODES) == {
        "rehearsal",
        "dry_run",
        "live",
        "offline_execution",
        "approval",
    }
    assert set(PHASES) == {
        "M3.1A",
        "M3.1B",
        "M3.2A",
        "M3.2B",
        "M3.3A",
        "M3.3B",
        "M3.4A",
        "M3.4B",
        "M3.5",
    }
    assert set(COMPLETION_STATUSES) == {
        "complete",
        "failed",
        "interrupted",
        "stopped_at_ceiling",
        "stopped_by_gate",
    }
    assert set(SCHEMA_DRIFT_OUTCOMES) == {"none", "unknown_fields_retained", "blocked"}
    assert set(INTERRUPTION_STATES) == {
        "before_raw_store_write",
        "after_raw_store_write_before_catalog_commit",
        "after_catalog_commit",
        "during_selection",
        "during_manifest_write",
    }
    assert set(RESPONSE_CLASSIFICATION_BUCKETS) == {
        "proceed",
        "retry",
        "retry_after",
        "cooldown",
        "fail",
        "quarantine",
    }


def test_live_is_the_only_mode_that_places_requests() -> None:
    assert set(ZERO_NETWORK_MODES) == set(INVOCATION_MODES) - {"live"}


@pytest.mark.parametrize("value", ["M3.6", "m3.1a", "M3.1", ""])
def test_an_unknown_phase_is_refused(value: str) -> None:
    with pytest.raises(ReceiptValidationError, match="phase"):
        rehearsal(phase=value)


def test_an_unknown_invocation_mode_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="invocation_mode"):
        rehearsal(invocation_mode="simulation")


def test_an_unknown_completion_status_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="completion_status"):
        rehearsal(completion_status="ok")


# --------------------------------------------------------------------------- #
# Class conformance (§4, §14) -- R fields
# --------------------------------------------------------------------------- #
def test_every_required_field_is_present_in_every_mode() -> None:
    required = {
        "receipt_schema_version",
        "receipt_id",
        "command_name",
        "command_version",
        "phase",
        "invocation_mode",
        "configuration_fingerprint",
        "migration_chain_head",
        "started_at_utc",
        "completed_at_utc",
        "elapsed_seconds",
        "actual_logical_request_count",
        "actual_physical_attempt_count",
        "completion_status",
    }
    for receipt in (rehearsal(), dry_run(), live()):
        assert required <= set(receipt.as_document())


def test_the_schema_version_field_is_written_by_the_module_not_the_caller() -> None:
    assert rehearsal().as_document()["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION


@pytest.mark.parametrize(
    "name",
    ["command_name", "command_version", "configuration_fingerprint", "migration_chain_head"],
)
def test_a_blank_required_string_is_not_a_value(name: str) -> None:
    with pytest.raises(ReceiptValidationError, match=name):
        rehearsal(**{name: "   "})


# --------------------------------------------------------------------------- #
# Class conformance -- C fields present in, and absent outside, their modes
# --------------------------------------------------------------------------- #
def test_a_c_field_is_absent_outside_its_named_modes() -> None:
    document = rehearsal().as_document()
    for name in (
        "source_registry_version",
        "index_plan_policy_version",
        "request_plan_schema_version",
        "acquisition_window",
        "request_plan_id",
        "approved_request_ceiling",
        "planned_logical_request_count",
        "actual_per_route",
        "response_classification_totals",
        "raw_object_count",
        "quota_policy_version",
    ):
        assert name not in document


def test_supplying_a_c_field_outside_its_named_modes_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="approved_request_ceiling"):
        rehearsal(approved_request_ceiling=40)


def test_the_dry_run_ceiling_is_refused_because_a_dry_run_precedes_approval() -> None:
    with pytest.raises(ReceiptValidationError, match="approved_request_ceiling"):
        dry_run(approved_request_ceiling=40)


def test_a_missing_c_field_inside_its_named_modes_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="request_plan_id"):
        live(request_plan_id=None)


def test_a_rehearsal_receipt_must_carry_its_evidence_reference() -> None:
    with pytest.raises(ReceiptValidationError, match="rehearsal_evidence_reference"):
        rehearsal(rehearsal_evidence_reference=None)


def test_a_live_receipt_must_not_carry_a_rehearsal_evidence_reference() -> None:
    with pytest.raises(ReceiptValidationError, match="rehearsal_evidence_reference"):
        live(rehearsal_evidence_reference="m3-1a-rehearsal-report-0001")


def test_an_offline_execution_field_is_refused_in_live() -> None:
    with pytest.raises(ReceiptValidationError, match="quota_policy_version"):
        live(quota_policy_version="pilot-quota/1.0")


# --------------------------------------------------------------------------- #
# No placeholder (§6.8, §14)
# --------------------------------------------------------------------------- #
def test_an_omitted_field_is_omitted_and_never_rendered_as_null() -> None:
    text = rehearsal().canonical_bytes().decode("utf-8")

    assert "null" not in text
    assert '"approved_request_ceiling"' not in text


def test_a_null_in_a_parsed_document_is_refused_rather_than_read_as_omitted() -> None:
    document = dict(live().as_document())
    document["raw_object_count"] = None

    with pytest.raises(ReceiptValidationError, match="raw_object_count"):
        validate_receipt_document(document)


def test_a_placeholder_string_is_refused() -> None:
    document = dict(live().as_document())
    document["request_plan_id"] = "N/A"

    with pytest.raises(ReceiptValidationError, match="request_plan_id"):
        validate_receipt_document(document)


def test_an_unknown_field_is_refused_because_the_permitted_set_is_closed() -> None:
    document = dict(rehearsal().as_document())
    document["operator_note"] = "looked fine"

    with pytest.raises(ReceiptValidationError, match="operator_note"):
        validate_receipt_document(document)


# --------------------------------------------------------------------------- #
# Types (§4)
# --------------------------------------------------------------------------- #
def test_a_count_must_be_an_integer_not_a_float() -> None:
    with pytest.raises(ReceiptValidationError, match="actual_logical_request_count"):
        rehearsal(actual_logical_request_count=0.0)


def test_a_boolean_is_not_an_integer_count() -> None:
    with pytest.raises(ReceiptValidationError, match="actual_physical_attempt_count"):
        rehearsal(actual_physical_attempt_count=False)


def test_a_negative_count_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="schema_drift_event_count"):
        rehearsal(schema_drift_event_count=-1)


def test_a_non_finite_elapsed_time_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="elapsed_seconds"):
        rehearsal(elapsed_seconds=float("inf"))


def test_a_timestamp_must_be_rfc_3339_utc_with_a_z_suffix() -> None:
    with pytest.raises(ReceiptValidationError, match="started_at_utc"):
        rehearsal(started_at_utc="2026-08-01T12:00:00+00:00")


def test_a_completion_before_its_start_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="completed_at_utc"):
        rehearsal(started_at_utc="2026-08-01T12:00:04Z", completed_at_utc="2026-08-01T12:00:00Z")


# --------------------------------------------------------------------------- #
# Zero-network modes (§4.5.1, §14)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mode", ["rehearsal", "dry_run", "offline_execution", "approval"])
def test_a_non_zero_network_count_in_a_zero_network_mode_is_fail_closed(mode: str) -> None:
    build = _ZERO_NETWORK_BUILDERS[mode]

    with pytest.raises(ReceiptValidationError, match="actual_logical_request_count"):
        build(actual_logical_request_count=3, actual_physical_attempt_count=3)


@pytest.mark.parametrize("mode", ["rehearsal", "dry_run", "offline_execution", "approval"])
def test_every_zero_network_mode_builds_a_valid_receipt(mode: str) -> None:
    document = _ZERO_NETWORK_BUILDERS[mode]().as_document()

    assert document["invocation_mode"] == mode
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0


def test_a_rehearsal_receipt_may_not_carry_simulated_object_totals() -> None:
    with pytest.raises(ReceiptValidationError, match="raw_object_count"):
        rehearsal(raw_object_count=12)


def test_a_rehearsal_receipt_may_not_carry_simulated_classification_totals() -> None:
    with pytest.raises(ReceiptValidationError, match="response_classification_totals"):
        rehearsal(
            response_classification_totals={
                "proceed": 3,
                "retry": 1,
                "retry_after": 0,
                "cooldown": 1,
                "fail": 0,
                "quarantine": 0,
            }
        )


# --------------------------------------------------------------------------- #
# Accounting consistency (§14)
# --------------------------------------------------------------------------- #
def test_physical_attempts_may_not_be_fewer_than_logical_requests() -> None:
    with pytest.raises(ReceiptValidationError, match="actual_physical_attempt_count"):
        live(
            actual_physical_attempt_count=7,
            actual_per_route={
                "sec_full_index": {"logical_request_count": 8, "physical_attempt_count": 7},
            },
        )


def test_live_physical_attempts_may_not_exceed_the_approved_ceiling() -> None:
    with pytest.raises(ReceiptValidationError, match="approved_request_ceiling"):
        live(approved_request_ceiling=8)


def test_planned_per_route_must_sum_to_the_reported_planned_total() -> None:
    with pytest.raises(ReceiptValidationError, match="planned_per_route"):
        live(planned_per_route={"sec_full_index": 7})


def test_actual_per_route_must_sum_to_the_reported_actual_totals() -> None:
    with pytest.raises(ReceiptValidationError, match="actual_per_route"):
        live(
            actual_per_route={
                "sec_full_index": {"logical_request_count": 7, "physical_attempt_count": 9},
            }
        )


def test_classified_responses_may_not_exceed_the_attempts_that_produced_them() -> None:
    with pytest.raises(ReceiptValidationError, match="response_classification_totals"):
        live(
            response_classification_totals={
                "proceed": 8,
                "retry": 4,
                "retry_after": 0,
                "cooldown": 0,
                "fail": 0,
                "quarantine": 0,
            }
        )


def test_there_is_no_unclassified_bucket() -> None:
    with pytest.raises(ReceiptValidationError, match="response_classification_totals"):
        live(
            response_classification_totals={
                "proceed": 8,
                "retry": 1,
                "retry_after": 0,
                "cooldown": 0,
                "fail": 0,
                "quarantine": 0,
                "unclassified": 0,
            }
        )


def test_a_missing_classification_bucket_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="response_classification_totals"):
        live(response_classification_totals={"proceed": 8, "retry": 1})


# --------------------------------------------------------------------------- #
# Completion, reasons, and recovery (§4.8, §11, §14)
# --------------------------------------------------------------------------- #
def test_a_complete_run_carries_no_reason_code() -> None:
    with pytest.raises(ReceiptValidationError, match="reason_code"):
        rehearsal(reason_code="SEC_REQUEST_CEILING_EXHAUSTED", reason_detail="not applicable")


@pytest.mark.parametrize(
    "status", ["failed", "interrupted", "stopped_at_ceiling", "stopped_by_gate"]
)
def test_every_non_complete_status_carries_a_reason(status: str) -> None:
    with pytest.raises(ReceiptValidationError, match="reason_code"):
        rehearsal(completion_status=status)


def test_an_unregistered_reason_code_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="SEC_INVENTED_CODE"):
        rehearsal(
            completion_status="failed",
            reason_code="SEC_INVENTED_CODE",
            reason_detail="a code that no registry knows.",
        )


def test_a_registered_reason_code_is_accepted() -> None:
    receipt = rehearsal(
        completion_status="failed",
        reason_code="SEC_REQUEST_CEILING_EXHAUSTED",
        reason_detail="the rehearsal stopped at the injected ceiling.",
    )

    assert receipt.as_document()["reason_code"] == "SEC_REQUEST_CEILING_EXHAUSTED"


def test_an_interrupted_run_carries_its_interruption_state() -> None:
    with pytest.raises(ReceiptValidationError, match="interruption_state"):
        rehearsal(
            completion_status="interrupted",
            reason_code="SEC_ACQUISITION_INTERRUPTED",
            reason_detail="the rehearsal simulated an interruption.",
        )


def test_an_uninterrupted_run_carries_no_interruption_state() -> None:
    with pytest.raises(ReceiptValidationError, match="interruption_state"):
        rehearsal(interruption_state="after_catalog_commit")


def test_a_live_ceiling_stop_carries_a_positive_remaining_planned_count() -> None:
    with pytest.raises(ReceiptValidationError, match="remaining_planned_logical_request_count"):
        live(
            completion_status="stopped_at_ceiling",
            reason_code="SEC_REQUEST_CEILING_EXHAUSTED",
            reason_detail="the approved ceiling was reached.",
            remaining_planned_logical_request_count=0,
        )


def test_a_live_ceiling_stop_is_accepted_with_remaining_planned_work() -> None:
    receipt = live(
        completion_status="stopped_at_ceiling",
        reason_code="SEC_REQUEST_CEILING_EXHAUSTED",
        reason_detail="the approved ceiling was reached.",
        remaining_planned_logical_request_count=3,
    )

    assert receipt.as_document()["remaining_planned_logical_request_count"] == 3


def test_the_remaining_planned_count_is_absent_when_the_run_did_not_stop_at_a_ceiling() -> None:
    with pytest.raises(ReceiptValidationError, match="remaining_planned_logical_request_count"):
        live(remaining_planned_logical_request_count=3)


def test_a_rehearsal_ceiling_stop_carries_no_remaining_planned_count() -> None:
    """``remaining_planned_logical_request_count`` is ``C: live``; a rehearsal never carries it."""
    with pytest.raises(ReceiptValidationError, match="remaining_planned_logical_request_count"):
        rehearsal(
            completion_status="stopped_at_ceiling",
            reason_code="SEC_REQUEST_CEILING_EXHAUSTED",
            reason_detail="the injected ceiling was reached.",
            remaining_planned_logical_request_count=3,
        )


def test_a_resumed_live_run_carries_the_attempts_already_spent() -> None:
    receipt = live(
        recovery_predecessor_receipt_id="c" * 64,
        consumed_request_count_carried_forward=5,
    )

    assert receipt.as_document()["consumed_request_count_carried_forward"] == 5


def test_a_resumed_live_run_that_omits_the_carried_forward_count_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="consumed_request_count_carried_forward"):
        live(recovery_predecessor_receipt_id="c" * 64)


def test_a_run_that_resumed_nothing_may_not_claim_a_baseline_from_nowhere() -> None:
    """Still refused under `3.0`, and now for the accurate reason.

    Under `2.0` a carried-forward count without a predecessor was simply a field outside its
    condition. Decision 055 §7.2 makes a non-zero baseline lawful on a clean carry-in root, so the
    combination is no longer nonsensical on its face — what makes *this* document invalid is that
    it names no carry-in authority for the baseline it claims. The refusal is preserved; only the
    reason is sharper.
    """
    with pytest.raises(ReceiptValidationError, match="carry_in_authority_sha256"):
        live(consumed_request_count_carried_forward=5)


def test_the_v2_table_still_refuses_a_carried_forward_count_without_a_predecessor() -> None:
    """The `2.0` table is unchanged: there, the field is conditional on a resume alone."""
    resumed = live(
        recovery_predecessor_receipt_id="c" * 64,
        consumed_request_count_carried_forward=5,
    )
    document = _as_v2(resumed.as_document())
    del document["recovery_predecessor_receipt_id"]  # leaving the count with nothing to resume from
    document["receipt_id"] = compute_receipt_id(document)

    with pytest.raises(ReceiptValidationError, match="consumed_request_count_carried_forward"):
        validate_receipt_document(document)


def test_a_predecessor_identifier_must_look_like_a_receipt_id() -> None:
    with pytest.raises(ReceiptValidationError, match="recovery_predecessor_receipt_id"):
        live(
            recovery_predecessor_receipt_id="yesterday's run",
            consumed_request_count_carried_forward=5,
        )


# --------------------------------------------------------------------------- #
# Resulting identities are one-way references (§4.7)
# --------------------------------------------------------------------------- #
def test_a_resulting_identity_is_recorded_where_the_command_produced_one() -> None:
    receipt = offline_execution(
        resulting_snapshot_id="snapshot-0001",
        resulting_root_manifest_sha256="f" * 64,
        resulting_manifest_id="manifest-0001",
    )

    assert receipt.as_document()["resulting_snapshot_id"] == "snapshot-0001"


def test_a_command_that_produced_no_identity_omits_the_reference() -> None:
    """§4.7 qualifies each reference with "where the command produced one"."""
    assert "resulting_snapshot_id" not in offline_execution().as_document()


def test_a_resulting_identity_may_not_appear_outside_its_named_modes() -> None:
    with pytest.raises(ReceiptValidationError, match="resulting_snapshot_id"):
        live(resulting_snapshot_id="snapshot-0001")


def test_an_approval_receipt_may_reference_only_the_two_manifest_identities() -> None:
    approval(resulting_root_manifest_sha256="f" * 64, resulting_manifest_id="manifest-0001")

    with pytest.raises(ReceiptValidationError, match="resulting_selection_run_id"):
        approval(resulting_selection_run_id="selection-0001")


# --------------------------------------------------------------------------- #
# Canonical serialization (§6)
# --------------------------------------------------------------------------- #
def test_canonical_bytes_are_utf_8_with_one_trailing_newline_and_no_bom() -> None:
    payload = rehearsal().canonical_bytes()

    assert payload.endswith(b"\n")
    assert not payload.endswith(b"\n\n")
    assert not payload.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in payload
    payload.decode("utf-8")


def test_keys_are_sorted_by_code_point() -> None:
    document = json.loads(rehearsal().canonical_bytes())

    assert list(document) == sorted(document)


def test_an_integer_renders_without_a_decimal_point() -> None:
    text = live().canonical_bytes().decode("utf-8")

    assert '"approved_request_ceiling":40' in text


def test_serialization_is_reproducible_from_a_reordered_mapping() -> None:
    document = rehearsal().as_document()
    reordered = dict(reversed(list(document.items())))

    assert canonical_bytes(reordered) == canonical_bytes(document)


def test_a_non_finite_number_never_reaches_the_canonical_form() -> None:
    with pytest.raises(ReceiptValidationError):
        canonical_bytes({"elapsed_seconds": float("nan")})


# --------------------------------------------------------------------------- #
# The single integrity identity (§13)
# --------------------------------------------------------------------------- #
def test_the_receipt_id_is_sha256_over_the_preimage_that_excludes_it() -> None:
    receipt = rehearsal()
    preimage = canonical_bytes(receipt.preimage_document())

    assert "receipt_id" not in receipt.preimage_document()
    assert receipt.receipt_id == hashlib.sha256(preimage).hexdigest()


def test_the_receipt_id_is_recomputable_from_the_written_document() -> None:
    document = rehearsal().as_document()

    assert compute_receipt_id(document) == document["receipt_id"]


def test_altering_any_field_moves_the_receipt_id() -> None:
    assert rehearsal().receipt_id != rehearsal(command_version="m3.1a/1.1").receipt_id


def test_a_tampered_receipt_id_is_refused() -> None:
    document = dict(rehearsal().as_document())
    document["receipt_id"] = "0" * 64

    with pytest.raises(ReceiptValidationError, match="receipt_id"):
        validate_receipt_document(document)


def test_no_second_receipt_integrity_field_is_permitted() -> None:
    document = dict(rehearsal().as_document())
    document["receipt_content_sha256"] = "d" * 64

    with pytest.raises(ReceiptValidationError, match="receipt_content_sha256"):
        validate_receipt_document(document)


# --------------------------------------------------------------------------- #
# Prohibited content (§5, §9) -- the scan must be non-vacuous
# --------------------------------------------------------------------------- #
def test_an_email_address_anywhere_in_the_receipt_is_refused() -> None:
    with pytest.raises(ProhibitedReceiptContentError, match="reason_detail"):
        rehearsal(
            completion_status="failed",
            reason_code="SEC_ACQUISITION_INTERRUPTED",
            reason_detail="contact researcher@example.edu about the halt.",
        )


def test_a_sec_user_agent_identity_is_refused_because_it_carries_an_email() -> None:
    document = dict(rehearsal().as_document())
    document["configuration_fingerprint"] = "Jane Researcher jane@example.edu"

    with pytest.raises(ProhibitedReceiptContentError):
        validate_receipt_document(document)


def test_an_absolute_path_is_refused() -> None:
    with pytest.raises(ProhibitedReceiptContentError, match="reason_detail"):
        rehearsal(
            completion_status="failed",
            reason_code="SEC_ACQUISITION_INTERRUPTED",
            reason_detail="the store at /srv/private/data was unreadable.",
        )


def test_a_home_relative_path_is_refused() -> None:
    with pytest.raises(ProhibitedReceiptContentError, match="reason_detail"):
        rehearsal(
            completion_status="failed",
            reason_code="SEC_ACQUISITION_INTERRUPTED",
            reason_detail="the store at ~/data was unreadable.",
        )


def test_a_windows_absolute_path_is_refused() -> None:
    with pytest.raises(ProhibitedReceiptContentError, match="reason_detail"):
        rehearsal(
            completion_status="failed",
            reason_code="SEC_ACQUISITION_INTERRUPTED",
            reason_detail=r"the store at C:\data was unreadable.",
        )


@pytest.mark.parametrize(
    "value",
    ["Bearer abc123", "Basic dXNlcjpwYXNz", "authorization: token abc"],
)
def test_a_credential_shaped_value_is_refused(value: str) -> None:
    document = dict(rehearsal().as_document())
    document["command_version"] = value

    with pytest.raises(ProhibitedReceiptContentError):
        validate_receipt_document(document)


@pytest.mark.parametrize(
    "name",
    ["sec_user_agent", "api_token", "cookie", "authorization", "password"],
)
def test_a_prohibited_field_name_is_refused_by_the_scan_itself(name: str) -> None:
    """The scan is checked directly, so it stays non-vacuous independently of the field set."""
    with pytest.raises(ProhibitedReceiptContentError, match=name):
        scan_for_prohibited_content({name: "some value"})


def test_the_scan_reaches_into_nested_values() -> None:
    with pytest.raises(ProhibitedReceiptContentError):
        scan_for_prohibited_content({"parser_versions": {"submissions": "/opt/parsers/v1"}})


def test_the_scan_passes_a_clean_receipt() -> None:
    scan_for_prohibited_content(live().as_document())


# --------------------------------------------------------------------------- #
# Storage: content-derived name, write-once, immutable (§7)
# --------------------------------------------------------------------------- #
def test_receipts_live_in_a_dedicated_directory_under_the_evidence_root(tmp_path: Path) -> None:
    assert receipts_directory(tmp_path).parent == tmp_path


def test_a_receipt_is_written_under_a_content_derived_name(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    receipt = rehearsal()

    written = write_receipt(receipt, evidence_root=evidence, repository_root=checkout)

    assert receipt.receipt_id in written.name
    assert written.read_bytes() == receipt.canonical_bytes()


def test_rewriting_the_identical_receipt_is_a_collision_by_identity_not_an_error(
    tmp_path: Path,
) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    receipt = rehearsal()

    first = write_receipt(receipt, evidence_root=evidence, repository_root=checkout)
    second = write_receipt(receipt, evidence_root=evidence, repository_root=checkout)

    assert first == second


def test_a_written_receipt_is_never_overwritten_with_different_bytes(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    receipt = rehearsal()
    written = write_receipt(receipt, evidence_root=evidence, repository_root=checkout)
    written.write_bytes(b"{}\n")

    with pytest.raises(ReceiptWriteError, match="immutable"):
        write_receipt(receipt, evidence_root=evidence, repository_root=checkout)


def test_a_receipt_is_never_written_inside_the_repository_checkout(tmp_path: Path) -> None:
    from disclosure_drift.m3.evidence_paths import EvidenceRootError

    checkout = tmp_path / "checkout"
    checkout.mkdir()

    with pytest.raises(EvidenceRootError):
        write_receipt(rehearsal(), evidence_root=checkout / "evidence", repository_root=checkout)


# --------------------------------------------------------------------------- #
# Inspection is read-only (§7, §14)
# --------------------------------------------------------------------------- #
def test_inspection_returns_the_validated_document(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    receipt = live()
    written = write_receipt(receipt, evidence_root=evidence, repository_root=checkout)

    assert inspect_receipt(written) == receipt.as_document()


def test_inspection_refuses_a_file_whose_bytes_are_not_canonical(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    document = rehearsal().as_document()
    path.write_bytes(json.dumps(document, indent=2).encode("utf-8"))

    with pytest.raises(ReceiptValidationError, match="canonical"):
        inspect_receipt(path)


def test_inspection_refuses_a_receipt_altered_after_it_was_written(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    written = write_receipt(rehearsal(), evidence_root=evidence, repository_root=checkout)
    document = json.loads(written.read_bytes())
    document["command_version"] = "m3.1a/9.9"
    written.write_bytes(canonical_bytes(document))

    with pytest.raises(ReceiptValidationError, match="receipt_id"):
        inspect_receipt(written)


def test_inspection_leaves_the_file_untouched(tmp_path: Path) -> None:
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    evidence = tmp_path / "evidence"
    written = write_receipt(rehearsal(), evidence_root=evidence, repository_root=checkout)
    before = written.read_bytes()

    inspect_receipt(written)

    assert written.read_bytes() == before


def test_inspection_refuses_a_receipt_written_under_an_unknown_schema_version(
    tmp_path: Path,
) -> None:
    path = tmp_path / "receipt.json"
    document = dict(rehearsal().as_document())
    document["receipt_schema_version"] = "m3-execution-receipt/1.0"
    path.write_bytes(canonical_bytes(document))

    with pytest.raises(ReceiptValidationError, match="receipt_schema_version"):
        inspect_receipt(path)


# --------------------------------------------------------------------------- #
# §11 identity non-contamination, asserted at the suite level
# --------------------------------------------------------------------------- #
# Contract §11 is explicit: "A suite-level test must prove every accepted governed identity
# byte-identical with receipts disabled, enabled, and varied." Rehearsal A12(b) proves it for the
# acquisition-layer identities it can reach; the S5 selection identity and the S6 manifest root are
# the governed identities the milestone actually protects, and no test computed them across a
# varying receipt at all. A receipt that entered one of them would be a phase-stopping defect
# (§18 stop condition 8), so the property is proven here rather than argued from the absence of an
# import edge.
_GOVERNED_SNAPSHOT_ID = "a" * 64
_GOVERNED_NODE_LIMIT = 2_000_000


def _governed_identities() -> tuple[str, ...]:
    """Compute the S5 selection identity and the S6 manifest root from fixed synthetic inputs.

    Pure functions only: no catalog, no clock, no filesystem, no receipt. Recomputing this while a
    receipt is absent, present, and varied is the whole experiment, so it must depend on nothing
    but its literal inputs.
    """
    from disclosure_drift.release import pilot_manifest as pm
    from disclosure_drift.sec.accession_selection_store import (
        FrozenJointCandidateSet,
        build_joint_selection_run_identity,
    )

    candidate_set = FrozenJointCandidateSet(
        snapshot_id=_GOVERNED_SNAPSHOT_ID,
        candidate_snapshot_sha256=hashlib.sha256(b"candidate-tables").hexdigest(),
        entity_count=24,
        accession_count=2,
        entities=(),
        accessions=(),
        entity_content_sha256=hashlib.sha256(b"entities").hexdigest(),
        accession_content_sha256=hashlib.sha256(b"accessions").hexdigest(),
    )
    selection = build_joint_selection_run_identity(candidate_set, node_limit=_GOVERNED_NODE_LIMIT)

    components = pm.ManifestComponents(
        source_observation_set_sha256=hashlib.sha256(b"c1").hexdigest(),
        candidate_tables_sha256=hashlib.sha256(b"c2").hexdigest(),
        quota_definitions_sha256=hashlib.sha256(b"c3").hexdigest(),
        selector_policy_sha256=hashlib.sha256(b"c4").hexdigest(),
        selected_entities_sha256=hashlib.sha256(b"c5").hexdigest(),
        selected_accessions_sha256=hashlib.sha256(b"c6").hexdigest(),
        reserves_sha256=hashlib.sha256(b"c7").hexdigest(),
        quota_report_sha256=hashlib.sha256(b"c8").hexdigest(),
    )
    result = pm.selection_result_sha256(
        manifest_hash_policy_version="pilot-manifest/1.0",
        selection_run_id=selection.selection_run_id,
        snapshot_id=selection.snapshot_id,
        selection_input_sha256=selection.selection_input_sha256,
        selection_input_schema_version="pilot-joint-selection-input/1.0",
        run_state="feasible",
        selected_entity_count=24,
        selected_accession_count=2,
        expanded_node_count=42,
        node_limit_exhausted=0,
        components=components,
    )
    root = pm.root_manifest_sha256(
        manifest_schema_version="pilot-manifest/1.0",
        selection_run_id=selection.selection_run_id,
        snapshot_id=selection.snapshot_id,
        selection_result=result,
        components=components,
    )
    return (selection.selection_input_sha256, selection.selection_run_id, result, root)


def test_no_governed_identity_is_contaminated_by_a_receipt(tmp_path: Path) -> None:
    """Receipts disabled, enabled, and varied: every governed identity is byte-identical."""
    evidence_root = tmp_path / "private-evidence"
    checkout = tmp_path / "checkout"
    checkout.mkdir()

    # Leg A -- receipts disabled: no receipt is constructed, serialized, or written at all.
    disabled = _governed_identities()
    assert not receipts_directory(evidence_root).exists()

    # Leg B -- receipts enabled: one is constructed and written, then the identities recomputed.
    first = rehearsal()
    write_receipt(first, evidence_root=evidence_root, repository_root=checkout)
    enabled = _governed_identities()

    # Leg C -- receipts varied: every operational value the receipt carries is different.
    second = rehearsal(
        command_name="m3 rehearse-again",
        command_version="m3.1a/9.9",
        configuration_fingerprint="f" * 64,
        migration_chain_head="0007_something_else",
        started_at_utc="2027-01-02T03:04:05Z",
        completed_at_utc="2027-01-02T03:04:06Z",
        elapsed_seconds=1.0,
        completion_status="interrupted",
        interruption_state="after_catalog_commit",
        reason_code="SEC_ACQUISITION_INTERRUPTED",
        reason_detail="a synthetic operational difference.",
        schema_drift_outcome="unknown_fields_retained",
        schema_drift_event_count=3,
        rehearsal_evidence_reference="m3-1a-rehearsal-report-0002",
    )
    write_receipt(second, evidence_root=evidence_root, repository_root=checkout)
    varied = _governed_identities()

    assert disabled == enabled == varied
    for identity in disabled:
        assert len(identity) == 64

    # The anti-tautology control: the two receipts really did differ, and both really exist.
    assert first.receipt_id != second.receipt_id
    written = sorted(receipts_directory(evidence_root).glob("receipt-*.json"))
    assert len(written) == 2
    assert inspect_receipt(written[0])["receipt_id"] != inspect_receipt(written[1])["receipt_id"]


def test_the_governed_identity_probe_is_sensitive_to_its_own_inputs() -> None:
    """The inverse control.

    A probe that returned constants would report non-contamination no matter what a receipt did.
    Changing one governed input must move the identities the previous test compares.
    """
    from disclosure_drift.sec.accession_selection_store import (
        FrozenJointCandidateSet,
        build_joint_selection_run_identity,
    )

    baseline = _governed_identities()
    moved = build_joint_selection_run_identity(
        FrozenJointCandidateSet(
            snapshot_id="b" * 64,
            candidate_snapshot_sha256=hashlib.sha256(b"candidate-tables").hexdigest(),
            entity_count=24,
            accession_count=2,
            entities=(),
            accessions=(),
            entity_content_sha256=hashlib.sha256(b"entities").hexdigest(),
            accession_content_sha256=hashlib.sha256(b"accessions").hexdigest(),
        ),
        node_limit=_GOVERNED_NODE_LIMIT,
    )

    assert moved.selection_run_id != baseline[1]
    assert moved.selection_input_sha256 != baseline[0]


def test_no_governed_module_imports_the_receipt_module() -> None:
    """A structural companion to the byte comparison: there is no path for contamination.

    The byte-identity test proves the property today; this proves there is no import edge that
    could make it false tomorrow without the change being visible in a diff.
    """
    import importlib
    import sys

    governed = (
        "disclosure_drift.release.pilot_manifest",
        "disclosure_drift.release.manifest",
        "disclosure_drift.release.hashing",
        "disclosure_drift.sec.accession_selection_store",
        "disclosure_drift.sec.entity_selection_store",
        "disclosure_drift.sec.pilot_manifest_store",
    )
    for name in governed:
        module = importlib.import_module(name)
        source = Path(str(module.__file__)).read_text(encoding="utf-8")
        assert "m3.receipt" not in source, f"{name} references the receipt module"
        assert "ExecutionReceipt" not in source, f"{name} references the receipt type"
    assert all(name in sys.modules for name in governed)


# --------------------------------------------------------------------------- #
# Schema 3.0: the carry-in root, and mixed-version reading (Decision 055 §7)
#
# `2.0` receipts stay byte-unchanged, valid, and readable; the writer emits `3.0`; and the two new
# field conditions interlock so that every malformed combination fails closed.
# --------------------------------------------------------------------------- #
def _as_v2(document: dict[str, Any]) -> dict[str, Any]:
    """Relabel a document as `2.0` and re-derive its identity, as a real `2.0` receipt would."""
    downgraded = {
        key: value
        for key, value in document.items()
        if key not in {"receipt_id", "receipt_schema_version"}
    }
    downgraded["receipt_schema_version"] = RECEIPT_SCHEMA_VERSION_V2
    downgraded["receipt_id"] = compute_receipt_id(downgraded)
    return downgraded


def carry_in_root(**overrides: Any) -> ExecutionReceipt:
    """A clean carry-in root: no predecessor, a non-zero baseline, and its authority hash."""
    fields: dict[str, Any] = {
        "consumed_request_count_carried_forward": 1,
        "carry_in_authority_sha256": "c" * 64,
    }
    fields.update(overrides)
    return live(**fields)


def test_a_written_receipt_declares_the_writer_schema() -> None:
    assert live().as_document()["receipt_schema_version"] == "m3-execution-receipt/3.0"


def test_a_v2_receipt_remains_valid_and_readable(tmp_path: Path) -> None:
    """The compatibility guarantee, exercised end to end rather than asserted."""
    document = _as_v2(live().as_document())

    validate_receipt_document(document)  # still valid under its own table

    path = tmp_path / "receipt-v2.json"
    path.write_bytes(canonical_bytes(document))
    assert inspect_receipt(path) == document


def test_a_v2_receipt_is_never_rewritten_by_being_read(tmp_path: Path) -> None:
    """Reading dispatches on the declared version; it never upgrades bytes in place (§7.1)."""
    payload = canonical_bytes(_as_v2(live().as_document()))
    path = tmp_path / "receipt-v2.json"
    path.write_bytes(payload)

    inspect_receipt(path)
    inspect_receipt(path)

    assert path.read_bytes() == payload


def test_a_v2_receipt_keeps_its_own_ceiling_rule_and_is_not_retroactively_invalidated() -> None:
    """§7.1: `2.0` receipts remain valid **under their former rules**, not under `3.0`'s.

    `3.0` introduced the cumulative bound — carried-forward plus actual must fit the ceiling.
    `2.0` never had it: it bounded `actual_physical_attempt_count` alone. Applying the new rule to
    old documents would refuse receipts that were correct when written, which is a rewrite of the
    record by refusal rather than the version dispatch the ruling calls for.

    The document below is exactly that case: its actual count of 9 fits the ceiling of 40 on its
    own, and only the *sum* with its carried-forward 35 exceeds it. It is assembled by relabelling
    a validated document rather than by constructing one, because the `3.0` writer would refuse to
    produce it — which is the point: only a receipt written under `2.0` can look like this.
    """
    document = _as_v2(
        live(
            recovery_predecessor_receipt_id="d" * 64,
            consumed_request_count_carried_forward=1,
        ).as_document()
    )
    document["consumed_request_count_carried_forward"] = 35  # 35 + 9 = 44, over a ceiling of 40
    document["receipt_id"] = compute_receipt_id(document)

    validate_receipt_document(document)  # readable and usable, exactly as it always was

    # The positive control: the same accounting under `3.0` is refused, so the dispatch above is a
    # real version distinction rather than the cumulative rule having been dropped altogether.
    promoted = {
        key: value
        for key, value in document.items()
        if key not in {"receipt_id", "receipt_schema_version"}
    }
    promoted["receipt_schema_version"] = RECEIPT_SCHEMA_VERSION
    promoted["receipt_id"] = compute_receipt_id(promoted)

    with pytest.raises(ReceiptValidationError, match="ceiling bounds cumulative consumption"):
        validate_receipt_document(promoted)


def test_a_v2_receipt_still_bounds_its_own_actual_count_by_the_ceiling() -> None:
    """The `2.0` rule it *did* have is untouched: `actual` alone may not exceed the ceiling."""
    document = _as_v2(live().as_document())
    document["approved_request_ceiling"] = 8  # its actual count is 9
    document["receipt_id"] = compute_receipt_id(document)

    with pytest.raises(ReceiptValidationError, match="exceeds the approved_request_ceiling"):
        validate_receipt_document(document)


def test_a_v2_receipt_may_not_carry_the_new_field() -> None:
    """`2.0`'s permitted set is closed, so the `3.0` field is not readable into it."""
    document = _as_v2(live().as_document())
    document["carry_in_authority_sha256"] = "c" * 64
    document["receipt_id"] = compute_receipt_id(document)

    with pytest.raises(ReceiptValidationError, match="carry_in_authority_sha256"):
        validate_receipt_document(document)


def test_an_unknown_schema_version_is_refused() -> None:
    """A version no reader knows is refused rather than assumed to be the current one (§12).

    ``4.0`` was the unknown version before accepted Decision 094 §10.1 introduced it; now that
    a reader dispatches on it, the unknown case needs a version that is genuinely absent from
    :data:`READABLE_RECEIPT_SCHEMA_VERSIONS`. That is the same property under test, and it
    stays non-vacuous: the assertion below would fail the moment a ``5.0`` reader appeared
    without this test being revisited.
    """
    document = live().as_document()
    document["receipt_schema_version"] = "m3-execution-receipt/5.0"

    assert "m3-execution-receipt/5.0" not in READABLE_RECEIPT_SCHEMA_VERSIONS
    with pytest.raises(ReceiptValidationError, match="receipt_schema_version"):
        validate_receipt_document(document)


def test_a_v3_document_carrying_v4_only_vocabulary_is_refused() -> None:
    """Decision 094 §10.1: no v4 vocabulary may enter a v2/v3 validator.

    The mutation proof §12.3 item 7 asks for. Each of the three v4-only vocabulary objects is
    injected into an otherwise valid ``3.0`` document, and each must be refused by the ``3.0``
    table -- not by a shared module-level tuple, which is exactly the coupling that would make
    the isolation a convention rather than a fact.
    """
    for field, value in (
        ("invocation_mode", "offline_catalog_transition"),
        ("invocation_mode", "offline_parse"),
        ("interruption_state", "after_migration_0014_before_0015"),
    ):
        document = dict(live().as_document())
        document[field] = value
        document["receipt_schema_version"] = RECEIPT_SCHEMA_VERSION
        with pytest.raises(ReceiptValidationError):
            validate_receipt_document(document)


def test_a_v4_reason_code_is_refused_by_the_v3_registry() -> None:
    """The v4 reason vocabulary is stage-scoped and never enters ``reasons.py`` (§10.1)."""
    from disclosure_drift.m3.receipt import REASON_CODES_V4
    from disclosure_drift.reasons import REASON_CODES

    assert not set(REASON_CODES_V4) & set(REASON_CODES)
    document = dict(live().as_document())
    document["completion_status"] = "failed"
    document["reason_code"] = REASON_CODES_V4[0]
    document["reason_detail"] = "a stage-scoped v4 code in a v3 receipt"
    with pytest.raises(ReceiptValidationError, match="disclosure_drift.reasons"):
        validate_receipt_document(document)


def test_a_clean_carry_in_root_records_its_authority_and_its_baseline() -> None:
    """§7.4: no predecessor, carries 1, names the authority, counts only this run's attempts."""
    receipt = carry_in_root()
    document = receipt.as_document()

    assert "recovery_predecessor_receipt_id" not in document
    assert document["consumed_request_count_carried_forward"] == 1
    assert document["carry_in_authority_sha256"] == "c" * 64
    assert document["actual_physical_attempt_count"] == 9  # this invocation's wire attempts only
    validate_receipt_document(document)


def test_an_ordinary_fresh_root_omits_both_carry_in_fields() -> None:
    document = live().as_document()
    assert "consumed_request_count_carried_forward" not in document
    assert "carry_in_authority_sha256" not in document


def test_a_resume_requires_its_carried_forward_count_and_omits_the_authority() -> None:
    receipt = live(
        recovery_predecessor_receipt_id="d" * 64,
        consumed_request_count_carried_forward=5,
    )
    document = receipt.as_document()

    assert "carry_in_authority_sha256" not in document
    validate_receipt_document(document)


def test_a_resume_may_not_also_name_a_carry_in_authority() -> None:
    """§7.3: the authority is absent on resume receipts. A root is not a continuation."""
    with pytest.raises(ReceiptValidationError, match="carry_in_authority_sha256"):
        live(
            recovery_predecessor_receipt_id="d" * 64,
            consumed_request_count_carried_forward=5,
            carry_in_authority_sha256="c" * 64,
        )


def test_a_nonzero_baseline_without_a_predecessor_must_name_its_authority() -> None:
    """A baseline claimed from nowhere is exactly what the authority hash exists to prevent."""
    with pytest.raises(ReceiptValidationError, match="carry_in_authority_sha256"):
        live(consumed_request_count_carried_forward=1)


def test_an_authority_without_a_baseline_is_refused() -> None:
    with pytest.raises(ReceiptValidationError, match="consumed_request_count_carried_forward"):
        live(carry_in_authority_sha256="c" * 64)


def test_a_zero_baseline_on_an_ordinary_root_is_refused() -> None:
    """§7.2: an ordinary zero-baseline fresh root *omits* the field rather than writing 0."""
    with pytest.raises(ReceiptValidationError, match="consumed_request_count_carried_forward"):
        live(consumed_request_count_carried_forward=0)


def test_the_carry_in_fields_may_not_appear_outside_a_live_receipt() -> None:
    with pytest.raises(ReceiptValidationError, match="carry_in_authority_sha256"):
        rehearsal(carry_in_authority_sha256="c" * 64)


def test_carried_forward_plus_actual_may_not_exceed_the_approved_ceiling() -> None:
    """§7.4: the ceiling bounds *cumulative* consumption, not this invocation alone."""
    with pytest.raises(ReceiptValidationError, match="cumulative"):
        carry_in_root(
            approved_request_ceiling=9,  # 1 carried + 9 actual = 10
            consumed_request_count_carried_forward=1,
        )


def test_cumulative_consumption_exactly_at_the_ceiling_is_lawful() -> None:
    """Equality is not overflow: a window may lawfully finish exactly at its ceiling."""
    receipt = carry_in_root(approved_request_ceiling=10)
    assert receipt.consumed_request_count_carried_forward == 1
    validate_receipt_document(receipt.as_document())


def test_the_carry_in_field_name_exemption_is_exactly_one_key_wide() -> None:
    """The `auth` key-fragment guard is narrowed by one permitted name, and no further.

    `carry_in_authority_sha256` is a decision-fixed field name that happens to contain `auth`.
    Exempting it must not reopen the guard: every neighbouring name, and the same name nested one
    level down, must still be refused.
    """
    for prohibited in (
        "authorization",
        "auth_token",
        "carry_in_authority_sha256_extra",
        "x_carry_in_authority_sha256",
    ):
        with pytest.raises(ProhibitedReceiptContentError, match="auth"):
            scan_for_prohibited_content({prohibited: "value"})

    with pytest.raises(ProhibitedReceiptContentError, match="auth"):
        scan_for_prohibited_content({"parser_versions": {"carry_in_authority_sha256": "1.0"}})


def test_the_exempt_field_is_still_scanned_for_prohibited_values() -> None:
    """Exempting the *name* never exempts the *value* it carries."""
    with pytest.raises(ProhibitedReceiptContentError):
        scan_for_prohibited_content({"carry_in_authority_sha256": "Bearer abc123"})


# --------------------------------------------------------------------------- #
# Predecessor resolution across the accepted receipt locations (Decision 063)
# --------------------------------------------------------------------------- #
# A chain head is written where its operator named it. `--receipt-out` has always allowed that, and
# the accepted M3.2 convention gives every run its own namespace, so a real chain spans two of them:
# `runs/m3_2_decision_062_sic_continuation/execution_receipt.json` names a predecessor that lives in
# `runs/m3_2a_clean_carry_in/`. Resolving only beside the head cannot find it, and an intact chain
# reads as broken. These tests pin what the locator may and may not do about that.
def _place(receipt: ExecutionReceipt, path: Path) -> Path:
    """Write one receipt exactly where ``--receipt-out`` would put it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(receipt.canonical_bytes())
    return path


def _evidence_root(tmp_path: Path) -> Path:
    """A governed evidence root, outside any checkout."""
    root = tmp_path / "evidence"
    root.mkdir(exist_ok=True)
    return root


def _successor(predecessor: ExecutionReceipt, **overrides: Any) -> ExecutionReceipt:
    """A `live` receipt that names ``predecessor`` as the receipt it continues.

    §7.2 requires a resume to state what it inherits, so the carried-forward baseline travels with
    the predecessor link rather than being repeated at every call site.
    """
    fields: dict[str, Any] = {
        "request_plan_id": "plan-successor",
        "recovery_predecessor_receipt_id": predecessor.receipt_id,
        "consumed_request_count_carried_forward": predecessor.actual_physical_attempt_count,
    }
    fields.update(overrides)
    return live(**fields)


def _namespace(root: Path, name: str) -> Path:
    """One run namespace beneath the evidence root."""
    return root / RUN_NAMESPACE_DIRNAME / name


def _tree_state(root: Path) -> dict[str, tuple[bytes, int]]:
    """Every file beneath ``root``, with its bytes and modification time."""
    return {
        str(path.relative_to(root)): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_a_predecessor_beside_the_head_still_resolves(tmp_path: Path) -> None:
    """The accepted same-directory content-derived behaviour, unchanged and tried first.

    Both with and without an evidence root: supplying one may only *add* places to look, never
    change where a chain that already resolves finds its predecessor.
    """
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    directory = receipts_directory(root)
    _place(predecessor, directory / content_derived_receipt_name(predecessor.receipt_id))

    for evidence_root in (None, root):
        path, document = resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=directory, evidence_root=evidence_root
        )
        assert document["receipt_id"] == predecessor.receipt_id
        assert path.name == content_derived_receipt_name(predecessor.receipt_id)


def test_a_real_shaped_cross_namespace_chain_resolves(tmp_path: Path) -> None:
    """The T7 shape: two run namespaces, one `execution_receipt.json` each."""
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    head = _successor(predecessor)
    _place(predecessor, _namespace(root, "m3_2a_clean_carry_in") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        head, _namespace(root, "m3_2_decision_062_sic_continuation") / OPERATOR_RECEIPT_FILENAME
    )

    path, document = resolve_predecessor_receipt(
        predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
    )

    assert document["receipt_id"] == predecessor.receipt_id
    assert path.parent.name == "m3_2a_clean_carry_in"
    assert path.name == OPERATOR_RECEIPT_FILENAME


def test_the_same_cross_namespace_chain_is_unresolvable_without_an_evidence_root(
    tmp_path: Path,
) -> None:
    """The defect this locator exists to fix, stated as a test.

    Identical fixture to the case above; only the root is withheld. Without it the search is the
    head's own directory alone, which is exactly where a per-run predecessor never is.
    """
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    _place(predecessor, _namespace(root, "m3_2a_clean_carry_in") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        _successor(predecessor),
        _namespace(root, "m3_2_decision_062_sic_continuation") / OPERATOR_RECEIPT_FILENAME,
    )

    with pytest.raises(ReceiptChainResolutionError, match="no evidence root was supplied"):
        resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=head_path.parent, evidence_root=None
        )


def test_a_predecessor_in_the_dedicated_receipts_directory_resolves(tmp_path: Path) -> None:
    """§7.1's dedicated directory is searched too, not only the run namespaces."""
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    _place(
        predecessor,
        receipts_directory(root) / content_derived_receipt_name(predecessor.receipt_id),
    )
    head_path = _place(
        _successor(predecessor),
        _namespace(root, "some_run") / OPERATOR_RECEIPT_FILENAME,
    )

    path, _ = resolve_predecessor_receipt(
        predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
    )

    assert path.parent == receipts_directory(root)


def test_a_candidate_must_carry_exactly_the_requested_identity(tmp_path: Path) -> None:
    """A file at the content-derived name claims an identity; a document that contradicts it is a
    defect, and is refused rather than accepted as "close enough"."""
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    impostor = live(request_plan_id="plan-impostor")
    _place(impostor, receipts_directory(root) / content_derived_receipt_name(wanted.receipt_id))
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError, match="different receipt_id"):
        resolve_predecessor_receipt(
            wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_a_predecessor_that_was_never_written_does_not_resolve(tmp_path: Path) -> None:
    """Nothing is synthesized to close the gap: zero candidates is a refusal."""
    root = _evidence_root(tmp_path)
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError, match="does not resolve to a readable receipt"):
        resolve_predecessor_receipt("d" * 64, head_directory=head_path.parent, evidence_root=root)


def test_an_unrelated_receipt_in_another_namespace_is_ignored(tmp_path: Path) -> None:
    """Non-vacuity for the identity test, and for the search order at the same time.

    The unrelated namespace sorts *first*, so a resolver that returned the first readable receipt it
    found — rather than the one whose validated identity was asked for — would return it. The
    assertion is that it does not.
    """
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    unrelated = live(request_plan_id="plan-unrelated")
    _place(unrelated, _namespace(root, "aaa_unrelated") / OPERATOR_RECEIPT_FILENAME)
    _place(wanted, _namespace(root, "zzz_wanted") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "mmm_head") / OPERATOR_RECEIPT_FILENAME
    )

    path, document = resolve_predecessor_receipt(
        wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
    )

    assert path.parent.name == "zzz_wanted"
    assert document["receipt_id"] == wanted.receipt_id


def test_an_unrelated_namespace_alone_cannot_satisfy_a_chain(tmp_path: Path) -> None:
    """The other half of the same rule: an unrelated receipt is ignored, never substituted."""
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    _place(
        live(request_plan_id="plan-unrelated"), _namespace(root, "other") / "execution_receipt.json"
    )
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError, match="does not resolve to a readable receipt"):
        resolve_predecessor_receipt(
            wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_a_malformed_receipt_at_the_content_derived_name_is_raised_not_skipped(
    tmp_path: Path,
) -> None:
    """A damaged receipt at the name that claims this identity is that receipt's defect.

    Skipping it and looking elsewhere would let a chain resolve *around* a corrupt receipt, which is
    the failure the chain check exists to surface.
    """
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    broken = receipts_directory(root) / content_derived_receipt_name(wanted.receipt_id)
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_text("{not json", encoding="utf-8")
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptValidationError):
        resolve_predecessor_receipt(
            wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_a_malformed_operator_named_receipt_elsewhere_cannot_block_a_lawful_chain(
    tmp_path: Path,
) -> None:
    """`execution_receipt.json` claims no identity, so a damaged one is another run's problem.

    It can never satisfy the requested identity, and an unrelated damaged file must not decide the
    fate of a chain that does not reference it.
    """
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    damaged = _namespace(root, "aaa_damaged") / OPERATOR_RECEIPT_FILENAME
    damaged.parent.mkdir(parents=True, exist_ok=True)
    damaged.write_text('{"receipt_schema_version":"m3-execution-receipt/1.0"}\n', encoding="utf-8")
    _place(wanted, _namespace(root, "zzz_wanted") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "mmm_head") / OPERATOR_RECEIPT_FILENAME
    )

    path, _ = resolve_predecessor_receipt(
        wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
    )

    assert path.parent.name == "zzz_wanted"


def test_two_valid_receipts_with_one_identity_are_necessarily_byte_identical() -> None:
    """Why byte-identical aliases are the *only* reachable multi-candidate outcome.

    §13 makes `receipt_id` the digest of the canonical preimage and §14 re-checks that it recomputes
    at every inspection. A document that differs anywhere therefore cannot keep the identity, so two
    files that both validate under one `receipt_id` cannot differ. The alias tolerance below is that
    fact, not a relaxation invented to make a case pass.
    """
    original = live(request_plan_id="plan-a").as_document()
    altered = dict(original)
    altered["request_plan_id"] = "plan-b"

    assert compute_receipt_id(altered) != original["receipt_id"]
    with pytest.raises(ReceiptValidationError, match="recompute"):
        validate_receipt_document(altered)


def test_byte_identical_aliases_resolve_deterministically(tmp_path: Path) -> None:
    """One receipt at two accepted paths is one receipt, and the search order decides which."""
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    _place(predecessor, _namespace(root, "zzz_copy") / OPERATOR_RECEIPT_FILENAME)
    _place(
        predecessor,
        receipts_directory(root) / content_derived_receipt_name(predecessor.receipt_id),
    )
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "mmm_head") / OPERATOR_RECEIPT_FILENAME
    )

    resolutions = {
        resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
        )[0]
        for _ in range(3)
    }

    assert resolutions == {
        receipts_directory(root) / content_derived_receipt_name(predecessor.receipt_id)
    }


def test_two_distinct_receipts_claiming_one_identity_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-vacuity for the ambiguity guard, which validation otherwise makes unreachable.

    Because a valid receipt's identity always recomputes, no pair of files on a real filesystem can
    reach this branch — which is precisely why it must be tested through the loader rather than
    through fixtures. The loader is replaced so two candidates validate to *different* documents
    under one identity; the guard must refuse rather than pick one. If a future change ever weakens
    identity validation, this is the test that keeps the choice from being made silently.
    """
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    _place(wanted, _namespace(root, "aaa_first") / OPERATOR_RECEIPT_FILENAME)
    _place(wanted, _namespace(root, "bbb_second") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "zzz_head") / OPERATOR_RECEIPT_FILENAME
    )

    def _forged(path: Path | str) -> dict[str, object]:
        document = live(request_plan_id=f"plan-{Path(path).parent.name}").as_document()
        document["receipt_id"] = wanted.receipt_id  # one identity, two different documents
        return document

    monkeypatch.setattr(receipt_module, "inspect_receipt", _forged)

    with pytest.raises(ReceiptChainResolutionError, match="contents differ"):
        resolve_predecessor_receipt(
            wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_a_symbolic_link_at_an_accepted_receipt_location_is_refused(tmp_path: Path) -> None:
    """Refused even though the link's target is a perfectly valid matching receipt.

    A receipt is addressed by a real path. A link is an indirection nobody recorded, and following
    one would make the resolved chain depend on filesystem state outside the evidence it governs.
    """
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    real = _place(predecessor, _namespace(root, "real") / OPERATOR_RECEIPT_FILENAME)
    linked = _namespace(root, "linked") / OPERATOR_RECEIPT_FILENAME
    linked.parent.mkdir(parents=True, exist_ok=True)
    linked.symlink_to(real)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "zzz_head") / OPERATOR_RECEIPT_FILENAME
    )

    with pytest.raises(ReceiptChainResolutionError, match="symbolic link"):
        resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_a_symbolic_link_beside_the_head_is_refused(tmp_path: Path) -> None:
    """The same rule at the same-directory location, which discovery never reaches."""
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    real = _place(predecessor, _namespace(root, "real") / OPERATOR_RECEIPT_FILENAME)
    head_directory = _namespace(root, "head")
    head_directory.mkdir(parents=True, exist_ok=True)
    (head_directory / content_derived_receipt_name(predecessor.receipt_id)).symlink_to(real)

    with pytest.raises(ReceiptChainResolutionError, match="symbolic link"):
        resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=head_directory, evidence_root=root
        )


def test_a_namespace_linked_outside_the_evidence_root_is_refused(tmp_path: Path) -> None:
    """A path escape: the candidate is lexically inside the root and really outside it."""
    root = _evidence_root(tmp_path)
    outside = tmp_path / "outside"
    predecessor = live(request_plan_id="plan-predecessor")
    _place(predecessor, outside / OPERATOR_RECEIPT_FILENAME)
    (root / RUN_NAMESPACE_DIRNAME).mkdir(parents=True, exist_ok=True)
    (root / RUN_NAMESPACE_DIRNAME / "escape").symlink_to(outside, target_is_directory=True)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "zzz_head") / OPERATOR_RECEIPT_FILENAME
    )

    with pytest.raises(
        ReceiptChainResolutionError, match="symbolic link|outside the evidence root"
    ):
        resolve_predecessor_receipt(
            predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
        )


def test_the_root_containment_guard_is_not_vacuous(tmp_path: Path) -> None:
    """The containment refusal is decided on resolved paths, and it does fire.

    Stated directly against the predicate as well as through a fixture, so the refusal above cannot
    be passing only because the symlink walk happened to reach it first.
    """
    root = _evidence_root(tmp_path)
    inside = root / RUN_NAMESPACE_DIRNAME / "a" / OPERATOR_RECEIPT_FILENAME
    inside.parent.mkdir(parents=True, exist_ok=True)
    inside.write_text("{}", encoding="utf-8")

    receipt_module._refuse_escaping_candidate(root, inside)  # inside: no refusal

    with pytest.raises(ReceiptChainResolutionError, match="outside the evidence root"):
        receipt_module._refuse_escaping_candidate(root, tmp_path / "outside" / "receipt.json")


def test_the_run_namespace_directory_may_not_itself_be_a_link(tmp_path: Path) -> None:
    """`runs/` is enumerated, so it is checked before anything under it is read."""
    root = _evidence_root(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (root / RUN_NAMESPACE_DIRNAME).symlink_to(elsewhere, target_is_directory=True)
    head_directory = root / "head"
    head_directory.mkdir()

    with pytest.raises(ReceiptChainResolutionError, match="symbolic link"):
        resolve_predecessor_receipt("e" * 64, head_directory=head_directory, evidence_root=root)


def test_resolution_mutates_no_receipt_and_creates_no_file(tmp_path: Path) -> None:
    """Receipts are immutable, and resolution is a read. Proved over the whole tree, twice.

    Both outcomes are covered: a resolution that succeeds and one that refuses. A refusal that
    "helpfully" materialized a canonical copy to satisfy the old resolver would be caught here.
    """
    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    _place(predecessor, _namespace(root, "m3_2a_clean_carry_in") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        _successor(predecessor),
        _namespace(root, "m3_2_decision_062_sic_continuation") / OPERATOR_RECEIPT_FILENAME,
    )
    before = _tree_state(root)

    resolve_predecessor_receipt(
        predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
    )
    with pytest.raises(ReceiptChainResolutionError):
        resolve_predecessor_receipt("f" * 64, head_directory=head_path.parent, evidence_root=root)

    assert _tree_state(root) == before


def test_resolution_constructs_no_network_access(tmp_path: Path) -> None:
    """Offline by construction: the module imports no transport, and the suite blocks sockets.

    ``tests/conftest.py`` makes every socket call raise for the whole session, so the successful
    resolution below is itself the proof that no connection was attempted.
    """
    assert not {"httpx", "socket", "urllib", "requests", "http"} & set(vars(receipt_module))

    root = _evidence_root(tmp_path)
    predecessor = live(request_plan_id="plan-predecessor")
    _place(predecessor, _namespace(root, "predecessor_run") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "head_run") / OPERATOR_RECEIPT_FILENAME
    )

    _, document = resolve_predecessor_receipt(
        predecessor.receipt_id, head_directory=head_path.parent, evidence_root=root
    )

    assert document["receipt_id"] == predecessor.receipt_id


# --------------------------------------------------------------------------- #
# Decision 064 §8 — sanitized predecessor-resolution diagnostics
# --------------------------------------------------------------------------- #
def test_a_zero_candidate_refusal_states_what_the_search_actually_did(tmp_path: Path) -> None:
    """An operator staring at a broken chain needs the classification, not just the verdict.

    The message must say which identity failed, that a search ran and how much it examined, that
    the answer was *zero* matches rather than an ambiguity, and which relative scopes were covered.
    """
    root = _evidence_root(tmp_path)
    _place(live(request_plan_id="plan-unrelated"), _namespace(root, "other") / "r.json")
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError) as raised:
        resolve_predecessor_receipt("d" * 64, head_directory=head_path.parent, evidence_root=root)

    message = str(raised.value)
    assert "d" * 12 in message, "the requested identity is named, truncated"
    assert "category=no_candidate_matched" in message
    assert "valid matches=0" in message
    assert "candidate files examined=" in message
    assert "runs/other" in message and "runs/head" in message
    assert "receipts" in message


def test_a_resolution_refusal_never_prints_the_private_evidence_root(tmp_path: Path) -> None:
    """Diagnostics are relative. The resolved root is private and never reaches a message."""
    root = _evidence_root(tmp_path)
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError) as raised:
        resolve_predecessor_receipt("d" * 64, head_directory=head_path.parent, evidence_root=root)

    message = str(raised.value)
    assert str(root) not in message
    assert str(tmp_path) not in message
    assert not any(part.startswith("/") for part in message.split()), "no absolute path appears"


def test_a_refusal_without_an_evidence_root_states_that_no_search_ran(tmp_path: Path) -> None:
    """The two zero-match categories are distinguishable: nothing found, versus nothing searched."""
    root = _evidence_root(tmp_path)
    head_path = _place(live(request_plan_id="plan-head"), _namespace(root, "head") / "r.json")

    with pytest.raises(ReceiptChainResolutionError) as raised:
        resolve_predecessor_receipt("d" * 64, head_directory=head_path.parent)

    assert "category=no_evidence_root_for_discovery" in str(raised.value)


def test_an_ambiguous_refusal_is_classified_as_ambiguity_not_absence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two distinct receipts under one identity is a different failure from finding none.

    Reached through the loader for the reason the ambiguity guard's own test documents: identity
    validation makes the branch unreachable from real files. What is asserted here is only that the
    refusal *classifies itself* as an ambiguity, so an operator is never left reading a
    two-candidate collision as an absent predecessor.
    """
    root = _evidence_root(tmp_path)
    wanted = live(request_plan_id="plan-wanted")
    _place(wanted, _namespace(root, "aaa_first") / OPERATOR_RECEIPT_FILENAME)
    _place(wanted, _namespace(root, "bbb_second") / OPERATOR_RECEIPT_FILENAME)
    head_path = _place(
        live(request_plan_id="plan-head"), _namespace(root, "zzz_head") / OPERATOR_RECEIPT_FILENAME
    )

    def _forged(path: Path | str) -> dict[str, object]:
        document = live(request_plan_id=f"plan-{Path(path).parent.name}").as_document()
        document["receipt_id"] = wanted.receipt_id
        return document

    monkeypatch.setattr(receipt_module, "inspect_receipt", _forged)

    with pytest.raises(ReceiptChainResolutionError) as raised:
        resolve_predecessor_receipt(
            wanted.receipt_id, head_directory=head_path.parent, evidence_root=root
        )

    message = str(raised.value)
    assert "category=ambiguous_distinct_candidates" in message
    assert "distinct receipts=" in message
    assert str(root) not in message
