"""Transport abstraction for SEC retrieval.

This module defines the request and response shapes plus the :class:`Transport`
protocol. It imports no HTTP library, so the whole retrieval policy in
:mod:`disclosure_drift.sec.http_client` is testable with a fake transport and
without network access. The only module that imports ``httpx`` is
:mod:`disclosure_drift.sec.httpx_transport`.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from typing import Final, Literal, Protocol, runtime_checkable

from disclosure_drift.errors import DisclosureDriftError

__all__ = [
    "MAX_IN_MEMORY_BYTES",
    "SecRequest",
    "Transport",
    "TransportFailureKind",
    "TransportResponse",
    "TransportUnavailableError",
]

MAX_IN_MEMORY_BYTES: Final = 64 * 1024 * 1024
"""Refuse to buffer more than this in memory; larger payloads must stream."""

TransportFailureKind = Literal[
    "connection_error",
    "connect_timeout",
    "read_timeout",
    "stream_interrupted",
]


class TransportUnavailableError(DisclosureDriftError):
    """Raised when a transport implementation cannot be constructed.

    Typically the approved ``[sec]`` extra is not installed.
    """


@dataclass(frozen=True, slots=True)
class SecRequest:
    """One outbound SEC request.

    ``headers`` already contains the validated contact identity. It is never
    logged: :meth:`redacted_headers` is the only representation used in logs,
    manifests, or audit records.

    ``follow_redirects`` is ``False`` for every SEC retrieval. The policy layer
    follows redirects itself, validating each hop against the source registry and
    the filing-body guard before issuing it, so automatic redirect following can
    never carry a retrieval outside the approved boundary.
    """

    url: str
    headers: Mapping[str, str]
    timeout_connect: float
    timeout_read: float
    purpose: str
    source_id: str
    stream: bool = False
    follow_redirects: bool = False

    def redacted_headers(self) -> Mapping[str, str]:
        """Return headers with the contact identity replaced by a marker."""
        return {
            name: ("[REDACTED]" if name.lower() == "user-agent" else value)
            for name, value in self.headers.items()
        }


@dataclass(frozen=True, slots=True)
class TransportResponse:
    """One transport-level response.

    ``body`` is populated for buffered responses; ``chunks`` is populated for
    streamed responses. Exactly one of them is used by the caller.
    """

    status: int
    headers: Mapping[str, str]
    final_url: str
    redirects: tuple[str, ...] = ()
    body: bytes = b""
    chunks: Iterator[bytes] | None = None
    failure: TransportFailureKind | None = None
    detail: str | None = None
    elapsed_seconds: float = 0.0
    extra: Mapping[str, str] = field(default_factory=dict)

    @property
    def succeeded_at_transport_level(self) -> bool:
        """Whether a response was received at all, regardless of status."""
        return self.failure is None

    def header(self, name: str) -> str | None:
        """Return a header value, matched case-insensitively."""
        lowered = name.lower()
        for key, value in self.headers.items():
            if key.lower() == lowered:
                return value
        return None

    @property
    def content_type(self) -> str | None:
        """Declared content type without parameters."""
        raw = self.header("content-type")
        return None if raw is None else raw.split(";", 1)[0].strip().lower()

    @property
    def etag(self) -> str | None:
        """Entity tag for conditional requests."""
        return self.header("etag")

    @property
    def last_modified(self) -> str | None:
        """Last-Modified value for conditional requests."""
        return self.header("last-modified")

    @property
    def content_encoding(self) -> str | None:
        """Declared content encoding."""
        return self.header("content-encoding")

    @property
    def content_length(self) -> int | None:
        """Declared content length when present and numeric."""
        raw = self.header("content-length")
        if raw is None or not raw.strip().isdigit():
            return None
        return int(raw.strip())


@runtime_checkable
class Transport(Protocol):
    """Minimal transport surface used by the SEC client."""

    def send(self, request: SecRequest) -> TransportResponse:
        """Perform one request and return the response or a transport failure."""
        ...  # pragma: no cover - protocol

    def close(self) -> None:
        """Release any underlying resources."""
        ...  # pragma: no cover - protocol


TransportContext = AbstractContextManager[Transport]
