"""The httpx adapter, exercised through ``httpx.MockTransport``.

No socket is opened: every response is served by a mock transport inside the test.
The module skips only when the optional ``[sec]`` extra is absent, which is permitted
in the core CI environment and a failure in the SEC-enabled one — see
``tests/unit/test_optional_dependencies.py`` and the two CI jobs.
"""

from __future__ import annotations

import gc
import inspect
import os
from typing import Any

import pytest

httpx = pytest.importorskip(
    "httpx",
    reason='the [sec] extra is not installed; run pip install -e ".[dev,sec]"',
)

from disclosure_drift.sec import httpx_transport as transport_module  # noqa: E402
from disclosure_drift.sec.httpx_transport import HttpxTransport, httpx_is_available  # noqa: E402
from disclosure_drift.sec.transport import (  # noqa: E402
    CloseableByteStream,
    SecRequest,
    TransportResponse,
)

URL = "https://www.sec.gov/files/company_tickers_exchange.json"
JSON_BODY = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC ONE","exchange":"Nasdaq"}}'


def request(url: str = URL, *, stream: bool = False) -> SecRequest:
    return SecRequest(
        url=url,
        headers={"User-Agent": "Financial Disclosure Drift research@your-institution.edu"},
        timeout_connect=10.0,
        timeout_read=60.0,
        purpose="census alias evidence",
        source_id="sec_company_tickers_exchange",
        stream=stream,
    )


def transport_with(handler: Any) -> HttpxTransport:
    """Build the adapter with its httpx client replaced by a mock transport."""
    adapter = HttpxTransport()
    adapter.close()
    adapter._client = httpx.Client(  # noqa: SLF001 - test seam for the mock transport
        transport=httpx.MockTransport(handler),
        follow_redirects=False,
        max_redirects=5,
    )
    return adapter


class TrackedSpool:
    """Proxy used to prove exact close and file-descriptor ownership."""

    def __init__(self, handle: Any, *, fail_on_read: int | None = None) -> None:
        self._handle = handle
        self._fail_on_read = fail_on_read
        self.read_calls = 0
        self.close_calls = 0

    @property
    def closed(self) -> bool:
        return bool(self._handle.closed)

    def write(self, data: bytes) -> int:
        return int(self._handle.write(data))

    def seek(self, offset: int) -> int:
        return int(self._handle.seek(offset))

    def read(self, size: int = -1) -> bytes:
        self.read_calls += 1
        if self._fail_on_read == self.read_calls:
            message = "synthetic local spool read failure"
            raise OSError(message)
        return bytes(self._handle.read(size))

    def fileno(self) -> int:
        return int(self._handle.fileno())

    def close(self) -> None:
        self.close_calls += 1
        self._handle.close()


def tracked_spools(
    monkeypatch: pytest.MonkeyPatch,
    *,
    fail_on_read: int | None = None,
) -> list[TrackedSpool]:
    """Patch temporary-file creation and return every owned spool."""
    spools: list[TrackedSpool] = []
    real_temporary_file = transport_module.tempfile.TemporaryFile

    def tracked_temporary_file(*args: Any, **kwargs: Any) -> TrackedSpool:
        spool = TrackedSpool(
            real_temporary_file(*args, **kwargs),
            fail_on_read=fail_on_read,
        )
        spools.append(spool)
        return spool

    monkeypatch.setattr(transport_module.tempfile, "TemporaryFile", tracked_temporary_file)
    return spools


def test_extra_is_available_when_this_module_runs() -> None:
    assert httpx_is_available()


def test_successful_json_response_is_mapped() -> None:
    served: list[httpx.Response] = []

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(
            200,
            content=JSON_BODY,
            headers={
                "Content-Type": "application/json",
                "ETag": 'W/"snapshot-1"',
                "Last-Modified": "Wed, 01 Jul 2026 00:00:00 GMT",
            },
        )
        served.append(response)
        return response

    with transport_with(handler) as adapter:
        response = adapter.send(request())
        assert served[0].is_closed

    assert isinstance(response, TransportResponse)
    assert response.status == 200
    assert response.body == JSON_BODY
    assert response.content_type == "application/json"
    assert response.etag == 'W/"snapshot-1"'
    assert response.last_modified == "Wed, 01 Jul 2026 00:00:00 GMT"
    assert response.succeeded_at_transport_level
    assert response.redirects == ()
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


def test_request_headers_are_forwarded() -> None:
    seen: dict[str, str] = {}

    def handler(incoming: httpx.Request) -> httpx.Response:
        seen.update(dict(incoming.headers))
        return httpx.Response(200, content=JSON_BODY, headers={"Content-Type": "application/json"})

    with transport_with(handler) as adapter:
        adapter.send(request())

    assert seen["user-agent"].startswith("Financial Disclosure Drift")


def test_conditional_not_modified_is_mapped_without_a_body() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(304, headers={"ETag": 'W/"snapshot-1"'})

    with transport_with(handler) as adapter:
        response = adapter.send(request())

    assert response.status == 304
    assert response.body == b""
    assert response.etag == 'W/"snapshot-1"'


def test_redirect_response_is_returned_without_following() -> None:
    old = "https://www.sec.gov/edgar/filer-information/calendar"
    new = "https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar"
    requested: list[str] = []

    def handler(incoming: httpx.Request) -> httpx.Response:
        requested.append(str(incoming.url))
        if str(incoming.url) == old:
            return httpx.Response(301, headers={"Location": new})
        return httpx.Response(200, content=b"<html></html>", headers={"Content-Type": "text/html"})

    with transport_with(handler) as adapter:
        response = adapter.send(request(old))

    assert response.status == 301
    assert response.redirects == ()
    assert response.final_url == old
    assert response.header("location") == new
    assert requested == [old]
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


@pytest.mark.parametrize("status", [304, 403, 404, 429, 500, 503])
def test_error_statuses_are_reported_without_raising(status: int) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=b"", headers={"Content-Type": "text/plain"})

    with transport_with(handler) as adapter:
        response = adapter.send(request())

    assert response.status == status
    assert response.succeeded_at_transport_level
    assert response.failure is None
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


def test_retry_after_header_is_preserved_for_the_policy_layer() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"})

    with transport_with(handler) as adapter:
        response = adapter.send(request())

    assert response.header("retry-after") == "30"


def test_streamed_response_yields_chunks_and_closes_resources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"PK\x03\x04" + b"member-bytes" * 64
    served: list[httpx.Response] = []
    spools = tracked_spools(monkeypatch)

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(
            200,
            content=payload,
            headers={"Content-Type": "application/zip"},
        )
        served.append(response)
        return response

    with transport_with(handler) as adapter:
        response = adapter.send(request(stream=True))
        assert served[0].is_closed
        assert not spools[0].closed
        assert response.chunks is not None
        assert isinstance(response.chunks, CloseableByteStream)
        assert b"".join(response.chunks) == payload
        assert spools[0].closed
        assert spools[0].close_calls == 1

    assert response.body == b""
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


def test_partial_stream_consumption_can_be_closed_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"PK\x03\x04" + b"member-bytes" * 64
    spools = tracked_spools(monkeypatch)

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=payload)

    with transport_with(handler) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        assert next(response.chunks) == payload
        assert not spools[0].closed
        response.close()

    assert response.chunks.closed
    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_zero_stream_consumption_can_be_closed_immediately(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        response.chunks.close()

    assert response.chunks.closed
    assert spools[0].closed
    assert spools[0].read_calls == 0
    assert spools[0].close_calls == 1


def test_streamed_response_context_closes_after_partial_consumption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with (
        transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter,
        adapter.send(request(stream=True)) as response,
    ):
        assert response.chunks is not None
        assert next(response.chunks) == b"PK\x03\x04payload"
        assert not response.chunks.closed

    assert response.chunks.closed
    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_stream_context_closes_after_partial_consumption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        with response.chunks as chunks:
            assert next(chunks) == b"PK\x03\x04payload"

    assert response.chunks.closed
    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_stream_iteration_exception_closes_spool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"x" * (transport_module._STREAM_CHUNK_BYTES + 1)  # noqa: SLF001
    spools = tracked_spools(monkeypatch, fail_on_read=2)

    with transport_with(lambda _: httpx.Response(200, content=payload)) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        chunk_bytes = transport_module._STREAM_CHUNK_BYTES  # noqa: SLF001
        assert next(response.chunks) == payload[:chunk_bytes]
        with pytest.raises(OSError, match="synthetic local spool read failure"):
            next(response.chunks)

    assert response.chunks.closed
    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_network_stream_exception_closes_httpx_response_and_spool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)
    served: list[httpx.Response] = []

    class InterruptedBody(httpx.SyncByteStream):
        def __init__(self) -> None:
            self.close_calls = 0

        def __iter__(self) -> Any:
            yield b"PK\x03\x04"
            message = "synthetic peer interruption"
            raise httpx.RemoteProtocolError(message)

        def close(self) -> None:
            self.close_calls += 1

    body = InterruptedBody()

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(200, stream=body)
        served.append(response)
        return response

    with transport_with(handler) as adapter:
        response = adapter.send(request(stream=True))

    assert response.failure == "stream_interrupted"
    assert served[0].is_closed
    assert body.close_calls == 1
    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_repeated_stream_close_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        response.chunks.close()
        response.chunks.close()
        response.close()

    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_stream_close_releases_temporary_file_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter:
        response = adapter.send(request(stream=True))
        descriptor = spools[0].fileno()
        os.fstat(descriptor)
        response.close()

    with pytest.raises(OSError):
        os.fstat(descriptor)
    assert spools[0].close_calls == 1


def test_abandoned_stream_has_garbage_collection_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spools = tracked_spools(monkeypatch)

    with transport_with(lambda _: httpx.Response(200, content=b"PK\x03\x04payload")) as adapter:
        response = adapter.send(request(stream=True))
        assert response.chunks is not None
        del response
        gc.collect()

    assert spools[0].closed
    assert spools[0].close_calls == 1


def test_streamed_error_status_is_read_and_mapped() -> None:
    served: list[httpx.Response] = []

    def handler(_: httpx.Request) -> httpx.Response:
        response = httpx.Response(
            503,
            content=b"unavailable",
            headers={"Content-Type": "text/plain"},
        )
        served.append(response)
        return response

    with transport_with(handler) as adapter:
        response = adapter.send(request(stream=True))

    assert served[0].is_closed
    assert response.status == 503
    assert response.chunks is None
    assert response.body == b"unavailable"
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


def test_explicit_monotonic_clock_supplies_elapsed_timing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readings = iter([150.0, 150.375])
    monkeypatch.setattr(transport_module.time, "monotonic", lambda: next(readings))

    with transport_with(lambda _: httpx.Response(200, content=JSON_BODY)) as adapter:
        response = adapter.send(request())

    assert response.elapsed_seconds == 0.375


def test_mapping_does_not_depend_on_httpx_elapsed_state() -> None:
    class ResponseWithoutTiming:
        status_code = 200
        headers = {"Content-Type": "application/json"}
        history: tuple[object, ...] = ()
        url = URL

        def __getattribute__(self, name: str) -> object:
            if name in {"elapsed", "_elapsed"}:
                message = f"HTTPX timing attribute {name!r} was accessed"
                raise AssertionError(message)
            return super().__getattribute__(name)

    with transport_with(lambda _: httpx.Response(200)) as adapter:
        response = adapter._map(  # noqa: SLF001 - focused adapter mapping contract
            ResponseWithoutTiming(),
            body=JSON_BODY,
            elapsed_seconds=0.25,
        )

    assert response.elapsed_seconds == 0.25
    assert "_elapsed" not in inspect.getsource(HttpxTransport)


@pytest.mark.parametrize(
    ("exception", "expected"),
    [
        (lambda: httpx.ConnectTimeout("connect timed out"), "connect_timeout"),
        (lambda: httpx.ReadTimeout("read timed out"), "read_timeout"),
        (lambda: httpx.RemoteProtocolError("peer closed"), "stream_interrupted"),
        (lambda: httpx.ConnectError("refused"), "connection_error"),
    ],
)
def test_transport_exceptions_map_to_failure_kinds(exception: Any, expected: str) -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise exception()

    with transport_with(handler) as adapter:
        response = adapter.send(request())

    assert response.failure == expected
    assert not response.succeeded_at_transport_level
    assert response.status == 0
    assert response.detail is not None
    assert isinstance(response.elapsed_seconds, float)
    assert response.elapsed_seconds >= 0.0


def test_close_is_idempotent() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"{}", headers={"Content-Type": "application/json"})

    adapter = transport_with(handler)
    adapter.close()
    adapter.close()
