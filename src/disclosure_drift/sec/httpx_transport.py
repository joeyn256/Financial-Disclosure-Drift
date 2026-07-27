"""The single module permitted to import an HTTP client library.

Everything about *when* and *whether* to request lives in
:mod:`disclosure_drift.sec.http_client`; this module only turns a
:class:`~disclosure_drift.sec.transport.SecRequest` into an httpx call and maps the
result back onto :class:`~disclosure_drift.sec.transport.TransportResponse`.

``httpx`` ships in the approved ``[sec]`` extra. Importing this module without it
raises :class:`~disclosure_drift.sec.transport.TransportUnavailableError` with an
actionable message rather than an obscure import error.
"""

from __future__ import annotations

import tempfile
import time
from collections.abc import Iterator
from types import TracebackType
from typing import TYPE_CHECKING, BinaryIO, Final

from disclosure_drift.sec.transport import (
    CloseableByteStream,
    SecRequest,
    TransportFailureKind,
    TransportResponse,
    TransportUnavailableError,
)

if TYPE_CHECKING:
    import httpx  # type: ignore[import-not-found,unused-ignore]

__all__ = ["HTTPX_INSTALL_HINT", "HttpxTransport", "httpx_is_available"]

HTTPX_INSTALL_HINT: Final = (
    "httpx is required for SEC retrieval. Install the approved extra: "
    'python -m pip install -e ".[dev,sec]"'
)
_STREAM_CHUNK_BYTES: Final = 1024 * 256


def httpx_is_available() -> bool:
    """Whether the approved HTTP client extra is installed."""
    try:
        import httpx  # type: ignore[import-not-found,unused-ignore]  # noqa: PLC0415
    except ImportError:
        return False
    return bool(httpx.__version__)


class HttpxTransport:
    """Thin httpx adapter with explicit timeouts and streaming support.

    Redirects are **not** followed here. The client is constructed with
    ``follow_redirects=False`` so that every hop returns to
    :mod:`disclosure_drift.sec.http_client`, which validates it against the source
    registry, the permitted URL family, and the filing-body guard before issuing the
    next request. Automatic redirect following would bypass those checks.
    """

    def __init__(self) -> None:
        try:
            import httpx  # noqa: PLC0415
        except ImportError as exc:
            raise TransportUnavailableError(HTTPX_INSTALL_HINT) from exc
        self._httpx = httpx
        self._client = httpx.Client(follow_redirects=False, http2=False)

    def __enter__(self) -> HttpxTransport:
        """Return the open transport."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the underlying client."""
        self.close()

    def close(self) -> None:
        """Close the underlying httpx client."""
        self._client.close()

    def send(self, request: SecRequest) -> TransportResponse:
        """Perform one request, mapping transport errors onto failure kinds."""
        httpx = self._httpx
        timeout = httpx.Timeout(
            connect=request.timeout_connect,
            read=request.timeout_read,
            write=request.timeout_read,
            pool=request.timeout_connect,
        )
        started_at = time.monotonic()
        try:
            if request.stream:
                return self._send_streamed(request, timeout, started_at)
            response = self._client.get(
                request.url,
                headers=dict(request.headers),
                timeout=timeout,
                follow_redirects=False,
            )
            try:
                body = response.content
                elapsed_seconds = time.monotonic() - started_at
                return self._map(response, body=body, elapsed_seconds=elapsed_seconds)
            finally:
                response.close()
        except httpx.ConnectTimeout as exc:
            return self._failure(
                request,
                "connect_timeout",
                exc,
                elapsed_seconds=time.monotonic() - started_at,
            )
        except httpx.ReadTimeout as exc:
            return self._failure(
                request,
                "read_timeout",
                exc,
                elapsed_seconds=time.monotonic() - started_at,
            )
        except httpx.RemoteProtocolError as exc:
            return self._failure(
                request,
                "stream_interrupted",
                exc,
                elapsed_seconds=time.monotonic() - started_at,
            )
        except httpx.HTTPError as exc:
            return self._failure(
                request,
                "connection_error",
                exc,
                elapsed_seconds=time.monotonic() - started_at,
            )

    # -- internals ---------------------------------------------------------- #
    def _send_streamed(
        self,
        request: SecRequest,
        timeout: httpx.Timeout,
        started_at: float,
    ) -> TransportResponse:
        spool: BinaryIO | None = None
        with self._client.stream(
            "GET",
            request.url,
            headers=dict(request.headers),
            timeout=timeout,
            follow_redirects=False,
        ) as response:
            if response.status_code != 200:
                response.read()
                elapsed_seconds = time.monotonic() - started_at
                return self._map(
                    response,
                    body=response.content,
                    elapsed_seconds=elapsed_seconds,
                )
            # Consume the network stream while the response context is open, but
            # spool it to an anonymous temporary file rather than a Python list.
            # This keeps a bulk archive out of memory while still allowing stream
            # errors to be mapped by ``send`` and retried by the policy layer.
            spool = tempfile.TemporaryFile(mode="w+b")  # noqa: SIM115 - iterator owns handle
            try:
                for chunk in response.iter_bytes(_STREAM_CHUNK_BYTES):
                    spool.write(chunk)
                spool.seek(0)
            except BaseException:
                spool.close()
                raise
        elapsed_seconds = time.monotonic() - started_at
        try:
            return self._map(
                response,
                body=b"",
                chunks=self._spooled_chunks(spool),
                elapsed_seconds=elapsed_seconds,
            )
        except BaseException:
            spool.close()
            raise

    @staticmethod
    def _spooled_chunks(handle: BinaryIO) -> CloseableByteStream:
        """Return an explicitly owned iterator over a disk-spooled response."""

        def read_chunks() -> Iterator[bytes]:
            while chunk := handle.read(_STREAM_CHUNK_BYTES):
                yield chunk

        return CloseableByteStream(read_chunks(), close_callback=handle.close)

    @property
    def follows_redirects(self) -> bool:
        """Always ``False``: the policy layer validates and follows hops itself."""
        return bool(self._client.follow_redirects)

    def _map(
        self,
        response: object,
        *,
        body: bytes,
        elapsed_seconds: float,
        chunks: CloseableByteStream | None = None,
    ) -> TransportResponse:
        status = int(getattr(response, "status_code", 0))
        headers = {
            str(key): str(value) for key, value in dict(getattr(response, "headers", {})).items()
        }
        history = getattr(response, "history", ())
        redirects = tuple(str(item.url) for item in history)
        return TransportResponse(
            status=status,
            headers=headers,
            final_url=str(getattr(response, "url", "")),
            redirects=redirects,
            body=body,
            chunks=chunks,
            elapsed_seconds=elapsed_seconds,
        )

    @staticmethod
    def _failure(
        request: SecRequest,
        kind: TransportFailureKind,
        exc: BaseException,
        *,
        elapsed_seconds: float,
    ) -> TransportResponse:
        return TransportResponse(
            status=0,
            headers={},
            final_url=request.url,
            failure=kind,
            detail=f"{type(exc).__name__}: {exc}",
            elapsed_seconds=elapsed_seconds,
        )
