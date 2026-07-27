"""SEC retrieval policy, exercised with a fake transport.

No test opens a socket, imports an HTTP library, or depends on live SEC content.
The autouse socket guard in ``conftest`` remains in force throughout.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import replace

import pytest

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.http_client import (
    ACCEPTABLE_CONTENT_TYPES,
    ProhibitedRetrievalError,
    RetrievalPolicy,
    SecClient,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import (
    MAX_IN_MEMORY_BYTES,
    CloseableByteStream,
    SecRequest,
    Transport,
    TransportFailureKind,
    TransportResponse,
)
from disclosure_drift.sec.urls import MAX_REDIRECT_DEPTH, RedirectBoundaryError, validate_url

VALID_AGENT = "Financial Disclosure Drift research@your-institution.edu"
BULK = "sec_bulk_submissions"
TICKERS = "sec_company_tickers_exchange"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
ENTITY = "sec_submissions_entity"
ANNOUNCEMENT = "sec_edgar_calendar_announcement"
JSON_BODY = b'{"cik":"0000000001","name":"SYNTHETIC ONE"}'
BLOCK_PAGE = (
    b"<html><body>Your Request Has Been Identified As Part Of A Network Of "
    b"Automated Tools</body></html>"
)
_REQUEST_FINAL_URL = "__fixture_request_url__"


class FakeClock:
    """Deterministic clock shared by the limiter and the client sleeper."""

    def __init__(self) -> None:
        self.now = 1_000.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class FakeTransport:
    """Replays scripted responses and records every request it received."""

    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[SecRequest] = []
        self.closed = False

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        if not self._responses:
            message = "FakeTransport exhausted: the client made an unexpected request"
            raise AssertionError(message)
        response = self._responses.pop(0)
        if response.final_url == _REQUEST_FINAL_URL:
            return replace(response, final_url=request.url)
        return response

    def close(self) -> None:
        self.closed = True


def response(
    status: int = 200,
    *,
    body: bytes = JSON_BODY,
    content_type: str | None = "application/json",
    headers: Mapping[str, str] | None = None,
    chunks: Iterator[bytes] | None = None,
    failure: TransportFailureKind | None = None,
    redirects: tuple[str, ...] = (),
    final_url: str | None = None,
) -> TransportResponse:
    merged = dict(headers or {})
    if content_type is not None:
        merged.setdefault("Content-Type", content_type)
    return TransportResponse(
        status=status,
        headers=merged,
        final_url=_REQUEST_FINAL_URL if final_url is None else final_url,
        redirects=redirects,
        body=body,
        chunks=chunks,
        failure=failure,
    )


def build(
    responses: Sequence[TransportResponse],
    *,
    rate: float = 4.0,
    policy: RetrievalPolicy | None = None,
) -> tuple[SecClient, FakeTransport, FakeClock]:
    clock = FakeClock()
    transport = FakeTransport(responses)
    limiter = AggregateRateLimiter(rate, burst=1, clock=clock.time, sleeper=clock.sleep)
    client = SecClient(
        transport,
        VALID_AGENT,
        limiter,
        policy or RetrievalPolicy(),
        sleeper=clock.sleep,
    )
    return client, transport, clock


# --------------------------------------------------------------------------- #
# Guards before any request is constructed
# --------------------------------------------------------------------------- #
def test_transport_protocol_is_satisfied_by_the_fake() -> None:
    assert isinstance(FakeTransport([]), Transport)


@pytest.mark.parametrize("agent", ["", "   "])
def test_client_refuses_construction_without_a_contact_identity(agent: str) -> None:
    limiter = AggregateRateLimiter(4.0)
    with pytest.raises(ProhibitedRetrievalError, match="validated contact identity"):
        SecClient(FakeTransport([]), agent, limiter)


def test_unregistered_source_is_refused_before_any_request() -> None:
    client, transport, _ = build([])
    with pytest.raises(Exception, match="not registered"):
        client.fetch("kaggle_issuer_list", purpose="census")
    assert transport.requests == []


def test_missing_purpose_is_refused() -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="recorded purpose"):
        client.fetch(TICKERS, purpose="   ")
    assert transport.requests == []


def test_entity_specific_source_requires_an_explicit_purpose() -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="explicit purpose"):
        client.fetch(ENTITY, purpose="qa", parameters={"cik_padded": "0000000001"})
    assert transport.requests == []


def test_entity_specific_source_accepts_a_documented_purpose() -> None:
    client, transport, _ = build([response()])
    result = client.fetch(
        ENTITY,
        purpose="reconcile fiscal-year-end absent from the bulk snapshot",
        parameters={"cik_padded": "0000000001"},
    )
    assert result.is_usable
    assert transport.requests[0].url.endswith("/submissions/CIK0000000001.json")


def test_no_request_is_made_for_a_filing_body_url() -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="exact SEC-referenced filename"):
        client.fetch(
            "sec_submissions_historical",
            purpose="retrieve the referenced historical submissions file",
            parameters={"historical_file": "../Archives/edgar/data/1/x-index.htm"},
        )
    assert transport.requests == []


@pytest.mark.parametrize("cik", ["1", "CIK0000000001", "0000000000", "../0000000001"])
def test_entity_identity_is_canonical_before_request_construction(cik: str) -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="CIK|cik_padded"):
        client.fetch(
            ENTITY,
            purpose="controlled entity submissions reconciliation",
            parameters={"cik_padded": cik},
        )
    assert transport.requests == []


def test_historical_redirect_cannot_escape_to_current_entity_submissions() -> None:
    escaped = "https://data.sec.gov/submissions/CIK0000000001.json"
    client, transport, _ = build(
        [
            response(
                302,
                body=b"",
                content_type=None,
                headers={"Location": escaped},
            )
        ]
    )
    result = client.fetch(
        "sec_submissions_historical",
        purpose="retrieve source-referenced historical submissions metadata",
        parameters={"historical_file": "CIK0000000001-submissions-001.json"},
    )
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY"
    assert len(transport.requests) == 1


def test_manifest_resolved_source_refuses_a_caller_supplied_url() -> None:
    """A calendar announcement is not an arbitrary-URL escape hatch (Decision 011 §7)."""
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="manifest-resolved"):
        client.fetch(
            ANNOUNCEMENT,
            purpose="retrieve a date-specific EDGAR closure announcement",
            parameters={"announcement_url": "https://www.sec.gov/anything-i-like"},
        )
    assert transport.requests == []


def test_manifest_resolved_source_requires_an_evidence_id() -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="evidence_id"):
        client.fetch(
            ANNOUNCEMENT,
            purpose="retrieve a date-specific EDGAR closure announcement",
        )
    assert transport.requests == []


def test_unknown_evidence_id_is_refused_by_the_manifest() -> None:
    client, transport, _ = build([])
    with pytest.raises(Exception, match="not in the reviewed manifest"):
        client.fetch(
            ANNOUNCEMENT,
            purpose="retrieve a date-specific EDGAR closure announcement",
            evidence_id="an_announcement_i_remembered",
        )
    assert transport.requests == []


def test_ordinary_sources_reject_an_announcement_url_parameter() -> None:
    client, transport, _ = build([])
    with pytest.raises(ProhibitedRetrievalError, match="caller-supplied URL"):
        client.fetch(
            TICKERS,
            purpose="census alias evidence",
            parameters={"announcement_url": "https://www.sec.gov/x"},
        )
    assert transport.requests == []


def test_registry_records_the_canonical_calendar_location() -> None:
    calendar_source = SOURCES["sec_edgar_filing_calendar"]
    announcement = SOURCES[ANNOUNCEMENT]
    assert calendar_source.url_template.endswith(
        "/submit-filings/filer-support-resources/edgar-calendar"
    )
    assert calendar_source.category == "operating_calendar_evidence"
    assert announcement.category == "calendar_announcement"
    assert announcement.manifest_resolved
    assert all(
        source.url_template.startswith(("https://www.sec.gov", "https://data.sec.gov"))
        for source in SOURCES.values()
        if not source.manifest_resolved
    )


# --------------------------------------------------------------------------- #
# Request construction
# --------------------------------------------------------------------------- #
def test_contact_identity_is_sent_but_never_exposed_in_redacted_headers() -> None:
    client, transport, _ = build([response()])
    client.fetch(TICKERS, purpose="census alias evidence")
    request = transport.requests[0]
    assert request.headers["User-Agent"] == VALID_AGENT
    assert request.redacted_headers()["User-Agent"] == "[REDACTED]"
    assert VALID_AGENT not in str(request.redacted_headers())
    assert VALID_AGENT not in repr(request)
    assert "headers=" not in repr(request)


def test_conditional_headers_are_sent_when_a_snapshot_exists() -> None:
    client, transport, _ = build([response(304, body=b"", content_type=None)])
    client.fetch(
        TICKERS,
        purpose="census alias evidence",
        etag='W/"abc"',
        last_modified="Wed, 01 Jul 2026 00:00:00 GMT",
    )
    request = transport.requests[0]
    assert request.headers["If-None-Match"] == 'W/"abc"'
    assert request.headers["If-Modified-Since"] == "Wed, 01 Jul 2026 00:00:00 GMT"


def test_bulk_sources_use_the_bulk_read_timeout() -> None:
    client, transport, _ = build([response(content_type="application/zip", body=b"PK\x03\x04")])
    client.fetch(BULK, purpose="census bulk submissions snapshot")
    request = transport.requests[0]
    assert request.timeout_read == 180.0
    assert request.timeout_connect == 10.0


def test_document_sources_use_the_ordinary_read_timeout() -> None:
    client, transport, _ = build([response()])
    client.fetch(TICKERS, purpose="census alias evidence")
    assert transport.requests[0].timeout_read == 60.0


def test_every_request_passes_through_the_aggregate_limiter() -> None:
    client, _, clock = build([response(), response()])
    client.fetch(TICKERS, purpose="census alias evidence")
    client.fetch(TICKERS, purpose="census alias evidence")
    assert client.request_count == 2
    assert clock.sleeps, "the second request must wait for its rate-limit slot"


# --------------------------------------------------------------------------- #
# Response handling
# --------------------------------------------------------------------------- #
def test_successful_retrieval_captures_provenance_headers() -> None:
    client, _, _ = build(
        [
            response(
                headers={
                    "ETag": 'W/"snapshot-1"',
                    "Last-Modified": "Wed, 01 Jul 2026 00:00:00 GMT",
                    "Content-Encoding": "gzip",
                }
            )
        ]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert result.body == JSON_BODY
    assert result.etag == 'W/"snapshot-1"'
    assert result.last_modified == "Wed, 01 Jul 2026 00:00:00 GMT"
    assert result.declared_content_type == "application/json"
    assert result.content_encoding == "gzip"
    assert result.attempts == 1


def test_not_modified_reuses_the_preserved_snapshot() -> None:
    client, _, _ = build([response(304, body=b"", content_type=None)])
    result = client.fetch(TICKERS, purpose="census alias evidence", etag='W/"abc"')
    assert result.outcome == "not_modified"
    assert result.is_reusable_snapshot
    assert not result.is_usable
    assert result.etag == 'W/"abc"'
    assert "unchanged" in result.detail


def test_redirect_chain_is_recorded() -> None:
    old = "https://www.sec.gov/edgar/filer-information/calendar"
    current = "https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar"
    client, _, _ = build(
        [
            response(302, body=b"", content_type=None, headers={"Location": old}),
            response(
                body=b"<html>EDGAR calendar</html>",
                content_type="text/html",
                final_url=old,
            ),
        ]
    )
    result = client.fetch(
        "sec_edgar_filing_calendar",
        purpose="official EDGAR operating-calendar evidence",
    )
    assert result.redirects == (current, old)
    assert result.attempts == 2


@pytest.mark.parametrize(
    "location",
    [
        "http://www.sec.gov/edgar/filer-information/calendar",
        "https://x@sec/edgar/filer-information/calendar",
        "https://www.sec.gov:8443/edgar/filer-information/calendar",
        "https://www.sec.gov/Archives/edgar/data/1/document.htm",
        "https://www.sec.gov/files/company_tickers.json",
    ],
)
def test_each_redirect_hop_is_validated_before_the_next_request(location: str) -> None:
    client, transport, _ = build(
        [response(302, body=b"", content_type=None, headers={"Location": location})]
    )
    result = client.fetch(
        "sec_edgar_filing_calendar",
        purpose="official EDGAR operating-calendar evidence",
    )
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY"
    assert len(transport.requests) == 1


def test_policy_owned_redirect_loop_is_refused() -> None:
    current = "https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar"
    old = "https://www.sec.gov/edgar/filer-information/calendar"
    client, transport, _ = build(
        [
            response(302, body=b"", content_type=None, headers={"Location": old}),
            response(302, body=b"", content_type=None, headers={"Location": current}),
        ]
    )
    result = client.fetch(
        "sec_edgar_filing_calendar",
        purpose="official EDGAR operating-calendar evidence",
    )
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_DEPTH_EXCEEDED"
    assert len(transport.requests) == 2


def test_policy_owned_redirect_depth_is_bounded() -> None:
    targets = [
        f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"
        for year, quarter in (
            (2020, 2),
            (2020, 3),
            (2020, 4),
            (2021, 1),
            (2021, 2),
            (2021, 3),
        )
    ]
    client, transport, _ = build(
        [
            response(302, body=b"", content_type=None, headers={"Location": target})
            for target in targets
        ]
    )
    result = client.fetch(
        "sec_full_index_company",
        purpose="quarterly metadata coverage reconciliation",
        parameters={"year": "2020", "quarter": "1"},
    )
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_DEPTH_EXCEEDED"
    assert len(transport.requests) == MAX_REDIRECT_DEPTH + 1


def test_transport_supplied_hidden_redirect_history_fails_closed() -> None:
    external = "https://outside.invalid/intermediate"
    client, transport, _ = build(
        [
            response(
                body=JSON_BODY,
                redirects=(external,),
                final_url="https://www.sec.gov/files/company_tickers_exchange.json",
            )
        ]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "failed"
    assert result.redirects == (external,)
    assert "transport_redirect_history_refused" in result.actions
    assert len(transport.requests) == 1


def test_unexplained_transport_final_url_fails_closed() -> None:
    client, _, _ = build(
        [
            response(
                final_url="https://www.sec.gov/files/company_tickers_exchange.json",
            )
        ]
    )
    result = client.fetch("sec_company_tickers", purpose="census ticker evidence")
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY"


@pytest.mark.parametrize(
    "final_url",
    [
        "",
        "https://www.sec.gov:invalid/files/company_tickers_exchange.json",
    ],
)
def test_missing_or_malformed_terminal_url_fails_closed_and_releases_stream(
    final_url: str,
) -> None:
    closed: list[str] = []
    stream = CloseableByteStream(
        iter([JSON_BODY]),
        close_callback=lambda: closed.append("closed"),
    )
    client, transport, _ = build(
        [
            response(
                body=b"",
                chunks=stream,
                final_url=final_url,
            )
        ]
    )

    result = client.fetch(TICKERS, purpose="census alias evidence", stream=True)

    assert result.outcome == "failed"
    assert result.reason_code == "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY"
    assert result.attempts == 1
    assert len(transport.requests) == 1
    assert stream.closed
    assert closed == ["closed"]


@pytest.mark.parametrize(
    "url",
    [
        "https://www.sec.gov/files/company_tickers.json.backup",
        "https://www.sec.gov/files/company_tickers.json/anything",
        "https://www.sec.gov/files/company_tickers.json%2f..",
        "https://www.sec.gov/files/company_tickers.json%2F..",
        "https://www.sec.gov/files/company_tickers.json%5c..",
        "https://www.sec.gov/files/company_tickers.json%5C..",
        "https://www.sec.gov/files/%2e%2E/company_tickers.json",
        "https://www.sec.gov/files/%252f/company_tickers.json",
        "https://www.sec.gov/files/%252e%252e/company_tickers.json",
        "https://www.sec.gov/files/company_tickers.json%00",
        "https://www.sec.gov/files/company_tickers.json?unexpected=1",
        "https://www.sec.gov/files/company_tickers.json?x=1&x=2",
        "https://www.sec.gov/files/company_tickers.json#fragment",
        (
            "https://www.sec.gov/files/company_tickers.json%2f..%2fArchives"
            "%2fedgar%2fdata%2f1%2fdocument.htm"
        ),
    ],
)
def test_structured_exact_url_policy_rejects_ambiguous_attacks(url: str) -> None:
    with pytest.raises(RedirectBoundaryError):
        validate_url(url, SOURCES["sec_company_tickers"])


def test_wrong_content_type_is_quarantined() -> None:
    client, _, _ = build([response(content_type="text/html", body=b"<html></html>")])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "quarantined"
    assert result.is_failure
    assert not result.is_usable


def test_block_page_with_status_200_triggers_cooldown_then_fails() -> None:
    client, _, clock = build(
        [
            response(body=BLOCK_PAGE, content_type="text/html"),
            response(body=BLOCK_PAGE, content_type="text/html"),
        ],
        policy=RetrievalPolicy(cooldown_seconds=600.0),
    )
    result = client.fetch("sec_sic_code_list", purpose="official SIC reference load")
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_BLOCK_PAGE"
    assert max(clock.sleeps) >= 600.0


def test_403_halts_aggregate_traffic_for_the_cooldown_then_retries_once() -> None:
    client, transport, clock = build([response(403, body=b"", content_type=None), response()])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert len(transport.requests) == 2
    assert result.attempts == 2
    assert max(clock.sleeps) >= 600.0
    assert "cooldown" in result.actions


def test_transient_failures_after_cooldown_do_not_restart_the_retry_budget() -> None:
    client, transport, _ = build(
        [
            response(503, body=b"", content_type=None),
            response(502, body=b"", content_type=None),
            response(403, body=b"", content_type=None),
            response(503, body=b"", content_type=None),
            response(),
        ],
        policy=RetrievalPolicy(max_transient_retries=5),
    )

    result = client.fetch(TICKERS, purpose="census alias evidence")

    assert result.outcome == "failed"
    assert result.attempts == 4
    assert len(transport.requests) == 4
    assert "post_cooldown_retry_refused" in result.actions


def test_429_with_retry_after_waits_the_named_delay() -> None:
    client, _, clock = build(
        [response(429, body=b"", content_type=None, headers={"Retry-After": "30"}), response()]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert 30.0 in clock.sleeps
    assert max(clock.sleeps) < 600.0


def test_unqualified_429_enters_the_global_cooldown() -> None:
    client, _, clock = build([response(429, body=b"", content_type=None), response()])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert max(clock.sleeps) >= 600.0


def test_transient_5xx_is_retried_with_backoff_then_succeeds() -> None:
    client, transport, clock = build(
        [
            response(503, body=b"", content_type=None),
            response(502, body=b"", content_type=None),
            response(),
        ]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert result.attempts == 3
    assert len(transport.requests) == 3
    assert any(delay >= 1.0 for delay in clock.sleeps)


def test_persistent_5xx_fails_within_the_retry_budget() -> None:
    policy = RetrievalPolicy(max_transient_retries=3)
    client, transport, _ = build(
        [response(500, body=b"", content_type=None) for _ in range(3)], policy=policy
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "failed"
    assert len(transport.requests) == 3
    assert result.body == b""


@pytest.mark.parametrize(
    "failure",
    ["connection_error", "connect_timeout", "read_timeout", "stream_interrupted"],
)
def test_transport_failures_retry_then_fail(failure: TransportFailureKind) -> None:
    policy = RetrievalPolicy(max_transient_retries=2)
    client, transport, _ = build(
        [response(0, body=b"", content_type=None, failure=failure) for _ in range(2)],
        policy=policy,
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "failed"
    assert result.status is None
    assert len(transport.requests) == 2


def test_transport_failure_then_success_is_recovered() -> None:
    client, _, _ = build(
        [response(0, body=b"", content_type=None, failure="read_timeout"), response()]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "retrieved"
    assert result.attempts == 2


def test_empty_body_is_never_reported_as_an_empty_dataset() -> None:
    client, _, _ = build([response(body=b"", content_type="application/json")])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "failed"
    assert result.reason_code == "SEC_RESPONSE_EMPTY"
    assert result.is_failure


def test_html_where_json_expected_is_quarantined_not_parsed() -> None:
    client, _, _ = build([response(body=b"<!DOCTYPE html><html>", content_type="application/json")])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "quarantined"
    assert result.reason_code == "SEC_RESPONSE_MALFORMED"


def test_archive_without_a_zip_signature_is_quarantined() -> None:
    client, _, _ = build([response(body=b"not-a-zip", content_type="application/zip")])
    result = client.fetch(BULK, purpose="census bulk submissions snapshot")
    assert result.outcome == "quarantined"
    assert result.reason_code == "RAW_ARCHIVE_INVALID"


@pytest.mark.parametrize(
    ("payload", "content_type", "reason_code"),
    [
        (b"not-a-zip", "application/zip", "RAW_ARCHIVE_INVALID"),
        (b"PK\x03\x04payload", "text/html", "SEC_RESPONSE_MALFORMED"),
    ],
)
def test_streamed_quarantine_transfers_evidence_ownership(
    payload: bytes,
    content_type: str,
    reason_code: str,
) -> None:
    closed: list[str] = []
    stream = CloseableByteStream(
        iter([payload[:4], payload[4:]]),
        close_callback=lambda: closed.append("closed"),
    )
    client, _, _ = build(
        [
            response(
                body=b"",
                chunks=stream,
                content_type=content_type,
                headers={
                    "ETag": '"quarantine-etag"',
                    "Last-Modified": "Sun, 26 Jul 2026 12:00:00 GMT",
                    "Content-Encoding": "gzip",
                },
            )
        ]
    )

    result = client.fetch(BULK, purpose="census bulk submissions snapshot", stream=True)

    assert result.outcome == "quarantined"
    assert result.reason_code == reason_code
    assert result.etag == '"quarantine-etag"'
    assert result.last_modified == "Sun, 26 Jul 2026 12:00:00 GMT"
    assert result.content_encoding == "gzip"
    assert result.body == payload
    assert result.chunks is None
    assert stream.closed
    result.close()
    assert stream.closed
    assert closed == ["closed"]


def test_streamed_archive_returns_chunks_without_buffering() -> None:
    payload = [b"PK\x03\x04", b"member-bytes"]
    client, transport, _ = build(
        [response(content_type="application/zip", body=b"", chunks=iter(payload))]
    )
    result = client.fetch(BULK, purpose="census bulk submissions snapshot", stream=True)
    assert result.outcome == "retrieved"
    assert result.body == b""
    assert result.chunks is not None
    assert isinstance(result.chunks, CloseableByteStream)
    assert list(result.chunks) == payload
    assert result.chunks.closed
    assert transport.requests[0].stream is True


def test_partial_fetch_stream_close_releases_transport_stream() -> None:
    closed: list[str] = []

    def payload() -> Iterator[bytes]:
        try:
            yield b"PK\x03\x04"
            yield b"member-bytes"
        finally:
            closed.append("closed")

    client, _, _ = build([response(content_type="application/zip", body=b"", chunks=payload())])
    result = client.fetch(BULK, purpose="census bulk submissions snapshot", stream=True)
    assert result.chunks is not None

    assert next(result.chunks) == b"PK\x03\x04"
    assert closed == []
    result.close()
    result.close()

    assert result.chunks.closed
    assert closed == ["closed"]


def test_fetch_result_context_closes_transport_stream() -> None:
    closed: list[str] = []

    def payload() -> Iterator[bytes]:
        try:
            yield b"PK\x03\x04"
            yield b"member-bytes"
        finally:
            closed.append("closed")

    client, _, _ = build([response(content_type="application/zip", body=b"", chunks=payload())])
    with client.fetch(
        BULK,
        purpose="census bulk submissions snapshot",
        stream=True,
    ) as result:
        assert result.chunks is not None
        assert next(result.chunks) == b"PK\x03\x04"

    assert result.chunks.closed
    assert closed == ["closed"]


def test_retried_stream_is_closed_before_next_attempt() -> None:
    first_closed: list[str] = []
    first_stream = CloseableByteStream(
        iter([b"PK\x03\x04transient"]),
        close_callback=lambda: first_closed.append("closed"),
    )
    client, transport, _ = build(
        [
            response(
                status=503,
                body=b"",
                chunks=first_stream,
                content_type="application/zip",
            ),
            response(
                body=b"",
                chunks=iter([b"PK\x03\x04", b"member-bytes"]),
                content_type="application/zip",
            ),
        ]
    )

    result = client.fetch(BULK, purpose="census bulk submissions snapshot", stream=True)

    assert result.outcome == "retrieved"
    assert first_stream.closed
    assert first_closed == ["closed"]
    assert len(transport.requests) == 2
    result.close()


def test_oversized_buffered_body_is_quarantined() -> None:
    oversized = b"{" + b"a" * MAX_IN_MEMORY_BYTES
    client, _, _ = build([response(body=oversized, content_type="application/json")])
    result = client.fetch(TICKERS, purpose="census alias evidence")
    assert result.outcome == "quarantined"
    assert "stream it instead" in result.detail


def test_octet_stream_is_accepted_for_json_and_zip() -> None:
    assert "application/octet-stream" in ACCEPTABLE_CONTENT_TYPES["json"]
    assert "application/octet-stream" in ACCEPTABLE_CONTENT_TYPES["zip"]
    client, _, _ = build([response(content_type="application/octet-stream")])
    assert client.fetch(TICKERS, purpose="census alias evidence").is_usable


def test_missing_content_type_does_not_fail_a_valid_payload() -> None:
    client, _, _ = build([response(content_type=None)])
    assert client.fetch(TICKERS, purpose="census alias evidence").is_usable


# --------------------------------------------------------------------------- #
# R3 final acceptance: streamed quarantine evidence and terminal reason codes
# --------------------------------------------------------------------------- #
class _OwnedSpool:
    """Stands in for the on-disk spool so closure is observable."""

    def __init__(self, payload: bytes, size: int = 8) -> None:
        self.parts = [payload[index : index + size] for index in range(0, len(payload), size)]
        self.closed = False
        self._next = 0

    def __iter__(self) -> _OwnedSpool:
        return self

    def __next__(self) -> bytes:
        if self._next >= len(self.parts):
            raise StopIteration
        part = self.parts[self._next]
        self._next += 1
        return part

    def close(self) -> None:
        self.closed = True


def test_malformed_streamed_response_preserves_its_quarantined_evidence() -> None:
    """A streamed payload lives in the spool, not in ``response.body``.

    Recording the empty body would destroy the very evidence quarantine exists to keep,
    so the spool is drained into the body before the result is returned.
    """
    payload = b"<!DOCTYPE html><html>this is not the json that was promised</html>"
    spool = _OwnedSpool(payload)
    stream = CloseableByteStream(iter(spool), close_callback=spool.close)
    client, transport, _ = build(
        [
            TransportResponse(
                status=200,
                headers={"Content-Type": "application/json", "ETag": 'W/"x"'},
                final_url=TICKERS_URL,
                body=b"",
                chunks=stream,
            )
        ]
    )
    result = client.fetch(TICKERS, purpose="census alias evidence", stream=True)

    assert result.outcome == "quarantined"
    assert result.body == payload
    assert result.declared_content_type == "application/json"
    assert result.provenance_headers
    assert spool.closed
    # The stream was consumed to build the evidence, so it is not handed on as a
    # second owner of a closed resource.
    assert result.chunks is None


def test_a_streamed_error_response_closes_every_attempt_spool() -> None:
    spools = [_OwnedSpool(b"<html>server error</html>") for _ in range(6)]
    responses = [
        TransportResponse(
            status=500,
            headers={"Content-Type": "text/html"},
            final_url=TICKERS_URL,
            body=b"",
            chunks=CloseableByteStream(iter(spool), close_callback=spool.close),
        )
        for spool in spools
    ]
    client, transport, _ = build(responses)
    result = client.fetch(TICKERS, purpose="census alias evidence", stream=True)

    assert result.is_failure
    assert all(spool.closed for spool in spools[: len(transport.requests)])
    assert result.chunks is None


def test_exhausted_retries_carry_a_registered_terminal_reason() -> None:
    """A terminal failure must name a reason, or it reads as an empty dataset."""
    responses = [
        TransportResponse(status=503, headers={}, final_url=TICKERS_URL, body=b"") for _ in range(6)
    ]
    client, transport, _ = build(responses)
    result = client.fetch(TICKERS, purpose="census alias evidence")

    assert result.outcome == "failed"
    assert result.reason_code == "SEC_RETRIES_EXHAUSTED"
    assert result.reason_code in REASON_CODES
    assert REASON_CODES[result.reason_code].blocks_release
    # Every retry is a real HTTP attempt, and they are counted as such.
    assert result.attempts == len(transport.requests)
    assert result.attempts > 1


def test_refused_post_cooldown_retry_carries_a_registered_terminal_reason() -> None:
    """Refusing the one controlled retry is terminal, so it must name a reason.

    The cooldown branch ends the retrieval without exhausting the numeric budget, so
    it does not pass through the exhaustion branch. It must still supply a registered
    release-blocking code; otherwise a blocked source reports a failure with no reason,
    which downstream cannot distinguish from a source that legitimately returned nothing.
    """
    client, transport, _ = build(
        [
            response(403, body=b"", content_type=None),
            response(503, body=b"", content_type=None),
            response(),
        ],
        policy=RetrievalPolicy(max_transient_retries=5),
    )

    result = client.fetch(TICKERS, purpose="census alias evidence")

    assert result.outcome == "failed"
    assert "post_cooldown_retry_refused" in result.actions
    assert result.reason_code is not None
    assert result.reason_code in REASON_CODES
    assert REASON_CODES[result.reason_code].blocks_release
    # The refused retry is never issued, so the third scripted response is untouched.
    assert len(transport.requests) == 2
    assert result.attempts == len(transport.requests)


@pytest.mark.parametrize(
    ("failure_kind", "expected_reason_code"),
    [
        ("connection_error", "SEC_RETRIES_EXHAUSTED"),
        ("connect_timeout", "SEC_RETRIES_EXHAUSTED"),
        ("read_timeout", "SEC_RETRIES_EXHAUSTED"),
        ("stream_interrupted", "SEC_RESPONSE_MALFORMED"),
    ],
)
def test_exhausted_transport_failures_carry_a_registered_terminal_reason(
    failure_kind: TransportFailureKind,
    expected_reason_code: str,
) -> None:
    """A transport failure that survives the budget is terminal, exactly like a 503."""
    responses = [
        TransportResponse(
            status=0,
            headers={},
            final_url=TICKERS_URL,
            failure=failure_kind,
            detail="synthetic transport failure",
        )
        for _ in range(6)
    ]
    client, transport, _ = build(responses)

    result = client.fetch(TICKERS, purpose="census alias evidence")

    assert result.outcome == "failed"
    assert result.reason_code == expected_reason_code
    assert result.reason_code in REASON_CODES
    assert REASON_CODES[result.reason_code].blocks_release
    assert result.attempts == len(transport.requests)
    assert result.attempts > 1
