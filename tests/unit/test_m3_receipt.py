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

from disclosure_drift.m3.receipt import (
    COMPLETION_STATUSES,
    INTERRUPTION_STATES,
    INVOCATION_MODES,
    PHASES,
    RECEIPT_SCHEMA_VERSION,
    RESPONSE_CLASSIFICATION_BUCKETS,
    SCHEMA_DRIFT_OUTCOMES,
    ZERO_NETWORK_MODES,
    ExecutionReceipt,
    ProhibitedReceiptContentError,
    ReceiptValidationError,
    ReceiptWriteError,
    canonical_bytes,
    compute_receipt_id,
    inspect_receipt,
    receipts_directory,
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
def test_the_schema_version_is_the_one_decision_028_fixed() -> None:
    assert RECEIPT_SCHEMA_VERSION == "m3-execution-receipt/2.0"


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


def test_a_run_that_resumed_nothing_carries_no_carried_forward_count() -> None:
    with pytest.raises(ReceiptValidationError, match="consumed_request_count_carried_forward"):
        live(consumed_request_count_carried_forward=5)


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
