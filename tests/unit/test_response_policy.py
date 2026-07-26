"""Offline classification of the SEC response matrix.

No test contacts the SEC or provokes rate restrictions; every response is simulated.
"""

from __future__ import annotations

import pytest

from disclosure_drift.sec.response_policy import (
    COOLDOWN_SECONDS,
    MAX_TRANSIENT_RETRIES,
    RETRY_BACKOFF_CEILING_SECONDS,
    TransportFailure,
    backoff_delay,
    classify_response,
    classify_transport_failure,
)

BLOCK_PAGE = (
    "<html><body>Your Request Has Been Identified As Part Of A Network Of Automated Tools"
    "</body></html>"
)


def test_success_proceeds() -> None:
    action = classify_response(200, {}, '{"cik":"320193"}', expected="json")
    assert action.kind == "proceed"
    assert action.is_valid_result


@pytest.mark.parametrize("status", [408, 500, 502, 503, 504])
def test_transient_statuses_retry_with_backoff(status: int) -> None:
    action = classify_response(status, {}, "error", attempt=1)
    assert action.kind == "retry"
    assert action.retryable
    assert 0 < action.delay_seconds <= RETRY_BACKOFF_CEILING_SECONDS
    assert not action.is_valid_result


@pytest.mark.parametrize("status", [408, 503])
def test_transient_statuses_fail_after_the_retry_budget(status: int) -> None:
    action = classify_response(status, {}, "error", attempt=MAX_TRANSIENT_RETRIES)
    assert action.kind == "fail"
    assert not action.retryable


def test_429_with_retry_after_honours_the_header() -> None:
    action = classify_response(429, {"Retry-After": "30"}, "")
    assert action.kind == "retry_after"
    assert action.delay_seconds == 30.0
    assert not action.halts_aggregate_traffic


def test_429_with_lowercase_header_is_honoured() -> None:
    assert classify_response(429, {"retry-after": "12"}, "").delay_seconds == 12.0


def test_429_with_unparseable_retry_after_falls_back_to_cooldown() -> None:
    action = classify_response(429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, "")
    assert action.kind == "cooldown"
    assert action.halts_aggregate_traffic


def test_unqualified_429_halts_aggregate_traffic() -> None:
    action = classify_response(429, {}, "")
    assert action.kind == "cooldown"
    assert action.delay_seconds >= COOLDOWN_SECONDS
    assert action.halts_aggregate_traffic


def test_403_halts_aggregate_traffic_with_a_block_reason() -> None:
    action = classify_response(403, {}, "")
    assert action.kind == "cooldown"
    assert action.delay_seconds >= COOLDOWN_SECONDS
    assert action.halts_aggregate_traffic
    assert action.reason_code == "SEC_BLOCK_PAGE"


def test_historical_404_is_absent_evidence_not_a_retry_loop() -> None:
    action = classify_response(404, {}, "", is_recent_filing=False)
    assert action.kind == "fail"
    assert not action.retryable


def test_recent_404_retries_then_fails() -> None:
    first = classify_response(404, {}, "", is_recent_filing=True, attempt=1)
    assert first.kind == "retry"
    last = classify_response(404, {}, "", is_recent_filing=True, attempt=MAX_TRANSIENT_RETRIES)
    assert last.kind == "fail"
    assert last.reason_code == "SEC_SCHEMA_REQUIRED_FIELD_MISSING"


def test_block_page_body_with_status_200_triggers_cooldown() -> None:
    action = classify_response(200, {}, BLOCK_PAGE, expected="html")
    assert action.kind == "cooldown"
    assert action.reason_code == "SEC_BLOCK_PAGE"
    assert action.halts_aggregate_traffic


def test_empty_body_never_becomes_a_valid_empty_result() -> None:
    action = classify_response(200, {}, "", content_length=0, expected="json")
    assert action.kind == "fail"
    assert action.reason_code == "SEC_RESPONSE_EMPTY"
    assert not action.is_valid_result


def test_html_where_json_expected_is_quarantined() -> None:
    action = classify_response(200, {}, "<!DOCTYPE html><html>", expected="json")
    assert action.kind == "quarantine"
    assert action.reason_code == "SEC_RESPONSE_MALFORMED"


def test_malformed_json_is_quarantined() -> None:
    action = classify_response(200, {}, "not json at all", expected="json")
    assert action.kind == "quarantine"
    assert action.reason_code == "SEC_RESPONSE_MALFORMED"


def test_json_array_payload_is_accepted() -> None:
    assert classify_response(200, {}, "[{}]", expected="json").kind == "proceed"


def test_invalid_archive_is_quarantined() -> None:
    action = classify_response(200, {}, "not-a-zip", expected="archive")
    assert action.kind == "quarantine"
    assert action.reason_code == "RAW_ARCHIVE_INVALID"


def test_valid_archive_signature_proceeds() -> None:
    assert classify_response(200, {}, "PK\x03\x04rest", expected="archive").kind == "proceed"


def test_unhandled_status_fails() -> None:
    assert classify_response(418, {}, "teapot").kind == "fail"


@pytest.mark.parametrize(
    "kind",
    ["connection_error", "connect_timeout", "read_timeout", "stream_interrupted"],
)
def test_transport_failures_retry_then_fail(kind: TransportFailure) -> None:
    retry = classify_transport_failure(kind, attempt=1)
    assert retry.kind == "retry"
    assert retry.retryable
    exhausted = classify_transport_failure(kind, attempt=MAX_TRANSIENT_RETRIES)
    assert exhausted.kind == "fail"


def test_interrupted_stream_records_a_partial_download_reason() -> None:
    action = classify_transport_failure("stream_interrupted", attempt=1)
    assert action.reason_code == "RAW_PARTIAL_DOWNLOAD"


def test_backoff_grows_and_is_capped() -> None:
    assert backoff_delay(1) == 1.0
    assert backoff_delay(2) == 2.0
    assert backoff_delay(10) == RETRY_BACKOFF_CEILING_SECONDS
    with pytest.raises(ValueError, match="one-based"):
        backoff_delay(0)
