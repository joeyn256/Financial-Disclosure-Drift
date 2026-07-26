"""Pure classification of SEC response behaviour.

This module has no HTTP dependency and opens no socket. It maps an observed
outcome — status code, headers, body prefix, or transport exception kind — onto a
single action, so the full response matrix can be tested offline in Stage M2.1 and
merely wired to a client in Stage M2.2.

Two invariants are enforced here:

* a failure never becomes a valid empty result;
* a ``403`` or an unqualified ``429`` halts **aggregate** SEC traffic for a
  cooldown period rather than letting each worker retry independently.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal

__all__ = [
    "BLOCK_PAGE_SIGNATURES",
    "COOLDOWN_SECONDS",
    "MAX_TRANSIENT_RETRIES",
    "RETRY_BACKOFF_CEILING_SECONDS",
    "ActionKind",
    "ExpectedPayload",
    "ResponseAction",
    "TransportFailure",
    "backoff_delay",
    "classify_response",
    "classify_transport_failure",
]

ActionKind = Literal["proceed", "retry", "retry_after", "cooldown", "fail", "quarantine"]
TransportFailure = Literal[
    "connection_error",
    "connect_timeout",
    "read_timeout",
    "stream_interrupted",
]
ExpectedPayload = Literal["json", "html", "text", "archive", "binary", "any"]

MAX_TRANSIENT_RETRIES: Final = 5
RETRY_BACKOFF_CEILING_SECONDS: Final = 60.0
COOLDOWN_SECONDS: Final = 600.0
_BASE_BACKOFF_SECONDS: Final = 1.0

RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({408, 500, 502, 503, 504})
BLOCK_PAGE_SIGNATURES: Final[tuple[str, ...]] = (
    "your request has been identified as part of a network of automated tools",
    "request rate threshold",
    "undeclared automated tools",
    "sec.gov / automated access",
    "declare your traffic",
)


@dataclass(frozen=True, slots=True)
class ResponseAction:
    """What the client must do next, and why."""

    kind: ActionKind
    reason: str
    delay_seconds: float = 0.0
    reason_code: str | None = None
    halts_aggregate_traffic: bool = False
    retryable: bool = False

    @property
    def is_valid_result(self) -> bool:
        """Only ``proceed`` yields a usable payload. Failures are never empty results."""
        return self.kind == "proceed"


def backoff_delay(attempt: int) -> float:
    """Return the exponential backoff delay for a one-based attempt number.

    ``int ** int`` is typed as ``Any`` because a negative exponent would yield a
    float, so every step here is a declared ``float`` and the returned value comes
    from a narrowed local rather than from the expression directly.
    """
    if attempt < 1:
        message = "attempt numbers are one-based"
        raise ValueError(message)
    exponent: int = attempt - 1
    growth: float = float(2**exponent)
    delay: float = _BASE_BACKOFF_SECONDS * growth
    if delay >= RETRY_BACKOFF_CEILING_SECONDS:
        return RETRY_BACKOFF_CEILING_SECONDS
    return delay


def _retry_after_seconds(headers: Mapping[str, str]) -> float | None:
    """Return a non-negative delay from ``Retry-After``, or ``None`` when unusable.

    Only the delta-seconds form is honoured; an HTTP-date value yields ``None`` so
    the caller falls back to the aggregate cooldown.
    """
    for key, value in headers.items():
        if key.lower() != "retry-after":
            continue
        try:
            seconds: float = float(value.strip())
        except (TypeError, ValueError):
            return None
        return seconds if seconds > 0.0 else 0.0
    return None


def _looks_like_block_page(body_prefix: str) -> bool:
    lowered = body_prefix.lower()
    return any(signature in lowered for signature in BLOCK_PAGE_SIGNATURES)


def _looks_like_html(body_prefix: str) -> bool:
    lowered = body_prefix.lstrip().lower()
    return lowered.startswith(("<!doctype html", "<html", "<head", "<?xml-stylesheet"))


def classify_transport_failure(kind: TransportFailure, attempt: int = 1) -> ResponseAction:
    """Classify a transport-level failure with no HTTP status."""
    if attempt >= MAX_TRANSIENT_RETRIES:
        return ResponseAction(
            kind="fail",
            reason=f"{kind} persisted through {attempt} attempts",
            reason_code="SEC_RESPONSE_MALFORMED" if kind == "stream_interrupted" else None,
        )
    reason_code = "RAW_PARTIAL_DOWNLOAD" if kind == "stream_interrupted" else None
    return ResponseAction(
        kind="retry",
        reason=f"transient {kind}",
        delay_seconds=backoff_delay(attempt),
        reason_code=reason_code,
        retryable=True,
    )


def classify_response(
    status: int,
    headers: Mapping[str, str] | None = None,
    body_prefix: str = "",
    content_length: int | None = None,
    expected: ExpectedPayload = "any",
    attempt: int = 1,
    is_recent_filing: bool = False,
) -> ResponseAction:
    """Classify an SEC HTTP response.

    Args:
        status: HTTP status code.
        headers: Response headers, matched case-insensitively.
        body_prefix: First bytes of the body, decoded, for signature checks.
        content_length: Decoded entity length when known.
        expected: Payload type the caller requested.
        attempt: One-based attempt number for backoff.
        is_recent_filing: Whether a ``404`` is unexpected because the target is recent.
    """
    header_map: Mapping[str, str] = {} if headers is None else headers

    if status == 403:
        return ResponseAction(
            kind="cooldown",
            reason="SEC returned 403; aggregate traffic halts before one controlled retry",
            delay_seconds=COOLDOWN_SECONDS,
            reason_code="SEC_BLOCK_PAGE",
            halts_aggregate_traffic=True,
        )

    if status == 429:
        retry_after = _retry_after_seconds(header_map)
        if retry_after is not None:
            return ResponseAction(
                kind="retry_after",
                reason="SEC returned 429 with Retry-After",
                delay_seconds=retry_after,
                retryable=True,
            )
        return ResponseAction(
            kind="cooldown",
            reason="SEC returned 429 without Retry-After; aggregate traffic halts",
            delay_seconds=COOLDOWN_SECONDS,
            halts_aggregate_traffic=True,
        )

    if status in RETRYABLE_STATUSES:
        if attempt >= MAX_TRANSIENT_RETRIES:
            return ResponseAction(
                kind="fail",
                reason=f"status {status} persisted through {attempt} attempts",
            )
        return ResponseAction(
            kind="retry",
            reason=f"transient status {status}",
            delay_seconds=backoff_delay(attempt),
            retryable=True,
        )

    if status == 404:
        if is_recent_filing:
            if attempt < MAX_TRANSIENT_RETRIES:
                return ResponseAction(
                    kind="retry",
                    reason="404 on a recent filing may be propagation delay",
                    delay_seconds=backoff_delay(attempt),
                    retryable=True,
                )
            return ResponseAction(
                kind="fail",
                reason="404 persisted for a recent filing",
                reason_code="SEC_SCHEMA_REQUIRED_FIELD_MISSING",
            )
        return ResponseAction(
            kind="fail",
            reason="404 on an archival path recorded as absent evidence",
        )

    if status != 200:
        return ResponseAction(kind="fail", reason=f"unhandled status {status}")

    if _looks_like_block_page(body_prefix):
        return ResponseAction(
            kind="cooldown",
            reason="response body carries an SEC block-page signature",
            delay_seconds=COOLDOWN_SECONDS,
            reason_code="SEC_BLOCK_PAGE",
            halts_aggregate_traffic=True,
        )

    if content_length == 0 or (content_length is None and not body_prefix):
        return ResponseAction(
            kind="fail",
            reason="empty body; a failure never becomes a valid empty result",
            reason_code="SEC_RESPONSE_EMPTY",
        )

    if expected == "json":
        stripped = body_prefix.lstrip()
        if _looks_like_html(body_prefix):
            return ResponseAction(
                kind="quarantine",
                reason="HTML returned where JSON was expected",
                reason_code="SEC_RESPONSE_MALFORMED",
            )
        if stripped and stripped[0] not in "{[":
            return ResponseAction(
                kind="quarantine",
                reason="body does not begin as a JSON document",
                reason_code="SEC_RESPONSE_MALFORMED",
            )

    if expected == "archive" and not body_prefix.startswith(("PK\x03\x04", "PK\x05\x06")):
        return ResponseAction(
            kind="quarantine",
            reason="archive payload lacks a ZIP local-file signature",
            reason_code="RAW_ARCHIVE_INVALID",
        )

    return ResponseAction(kind="proceed", reason="response accepted")
