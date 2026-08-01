"""SEC retrieval policy: rate limiting, retries, cooldown, and validation.

All Stage M2.2 network policy lives here and is expressed against the
:class:`~disclosure_drift.sec.transport.Transport` protocol, so every behaviour is
testable with a fake transport and without network access. This module imports no
HTTP library.

Enforced rules:

* the contact identity is validated **before** a request is constructed, and only
  a redacted form ever reaches a log or an audit record;
* one shared aggregate limiter gates every request;
* only registered official SEC sources may be requested, and a filing-body or
  accession-package URL is refused outright in Stage M2.2;
* responses are classified by :mod:`disclosure_drift.sec.response_policy`;
* a ``403`` or an unqualified ``429`` halts aggregate traffic for the configured
  cooldown before one controlled retry;
* declared content type is validated against the registered expectation;
* a transport or HTTP failure is never reported as an empty dataset;
* redirects are followed **here**, one validated hop at a time, so no automatic
  redirect following can bypass the source registry, the permitted URL family, or
  the filing-body guard. Every hop and the final URL are validated before a payload
  is trusted, and the validated chain is recorded on the result.
"""

from __future__ import annotations

import itertools
import re
import time as _time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Final, Literal

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.logging_config import get_logger
from disclosure_drift.sec.calendar_evidence import require_evidence
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.response_policy import (
    ExpectedPayload,
    ResponseAction,
    classify_response,
    classify_transport_failure,
)
from disclosure_drift.sec.source_registry import (
    ContentKind,
    SourceSpec,
    filing_body_url_is_prohibited,
    require_registered,
)
from disclosure_drift.sec.transport import (
    MAX_IN_MEMORY_BYTES,
    CloseableByteStream,
    SecRequest,
    Transport,
    TransportResponse,
)
from disclosure_drift.sec.urls import (
    REDIRECT_STATUSES,
    RedirectBoundaryError,
    RedirectHop,
    normalize_url,
    request_identity,
    resolve_redirect,
    validate_chain,
    validate_url,
)

__all__ = [
    "ACCEPTABLE_CONTENT_TYPES",
    "BODY_PREFIX_BYTES",
    "FetchOutcome",
    "FetchResult",
    "ProhibitedRetrievalError",
    "RetrievalPolicy",
    "SecClient",
]

_LOGGER_NAME: Final = "sec.http"
_HISTORICAL_FILE: Final = re.compile(r"^CIK[0-9]{10}-submissions-[0-9]{3}\.json$")
_PROVENANCE_HEADERS: Final[tuple[str, ...]] = (
    "etag",
    "last-modified",
    "content-type",
    "content-length",
    "content-encoding",
    "date",
)
BODY_PREFIX_BYTES: Final = 4096
"""How much of a body is inspected for block-page and payload-shape checks."""

ACCEPTABLE_CONTENT_TYPES: Final[Mapping[ContentKind, tuple[str, ...]]] = {
    "json": ("application/json", "text/json", "application/octet-stream"),
    "zip": ("application/zip", "application/x-zip-compressed", "application/octet-stream"),
    "html": ("text/html", "application/xhtml+xml"),
    "text": ("text/plain", "application/octet-stream"),
}
"""Content types accepted for each registered expectation."""

_EXPECTED_PAYLOAD: Final[Mapping[ContentKind, ExpectedPayload]] = {
    "json": "json",
    "zip": "archive",
    "html": "html",
    "text": "text",
}

FetchOutcome = Literal["retrieved", "not_modified", "failed", "quarantined"]


class ProhibitedRetrievalError(DisclosureDriftError):
    """Raised when a retrieval is refused by Stage M2.2 policy."""


@dataclass(frozen=True, slots=True)
class RetrievalPolicy:
    """Timeouts, retry budget, and cooldown for SEC retrieval."""

    connect_timeout_seconds: float = 10.0
    read_timeout_seconds: float = 60.0
    bulk_read_timeout_seconds: float = 180.0
    max_transient_retries: int = 5
    cooldown_seconds: float = 600.0

    def read_timeout_for(self, spec: SourceSpec) -> float:
        """Return the read timeout appropriate to the source size class."""
        return (
            self.bulk_read_timeout_seconds
            if spec.expected_content == "zip"
            else (self.read_timeout_seconds)
        )


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Outcome of one controlled retrieval.

    ``identity`` is the normalized request identity. A preserved snapshot may only
    be reused within one identity, so it is carried here rather than recomputed.

    ``sent_etag`` and ``sent_last_modified`` record the validators this request
    actually sent, which the snapshot store needs to decide whether a ``304`` may be
    honoured at all.
    """

    outcome: FetchOutcome
    source_id: str
    url: str
    purpose: str
    status: int | None = None
    body: bytes = b""
    chunks: CloseableByteStream | None = None
    etag: str | None = None
    last_modified: str | None = None
    declared_content_type: str | None = None
    content_encoding: str | None = None
    provenance_headers: Mapping[str, str] = field(default_factory=dict)
    redirects: tuple[str, ...] = ()
    redirect_hops: tuple[RedirectHop, ...] = ()
    final_url: str | None = None
    identity: str | None = None
    sent_etag: str | None = None
    sent_last_modified: str | None = None
    attempts: int = 0
    reason_code: str | None = None
    detail: str = ""
    actions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Wrap legacy iterator inputs in the explicit ownership contract."""
        object.__setattr__(self, "chunks", CloseableByteStream.coerce(self.chunks))

    def __enter__(self) -> FetchResult:
        """Return the result while retaining ownership of any stream."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object | None,
    ) -> None:
        """Close any streamed body when leaving the result scope."""
        self.close()

    def close(self) -> None:
        """Close the streamed body, if present; safe to call repeatedly."""
        if self.chunks is not None:
            self.chunks.close()

    @property
    def is_usable(self) -> bool:
        """Only a retrieved payload may be parsed."""
        return self.outcome == "retrieved"

    @property
    def sent_any_validator(self) -> bool:
        """Whether this request carried a conditional validator."""
        return bool(self.sent_etag or self.sent_last_modified)

    @property
    def is_reusable_snapshot(self) -> bool:
        """Whether the caller should reuse its preserved snapshot unchanged."""
        return self.outcome == "not_modified"

    @property
    def is_failure(self) -> bool:
        """Whether this retrieval failed. A failure is never an empty dataset."""
        return self.outcome in {"failed", "quarantined"}


@dataclass(slots=True)
class _Attempt:
    """Mutable state for one logical retrieval, including its validated hops."""

    spec: SourceSpec
    requested_url: str
    current_url: str
    purpose: str
    identity: str
    sent_etag: str | None
    sent_last_modified: str | None
    retry_ordinal: int = 1
    http_attempts: int = 0
    hops: list[RedirectHop] = field(default_factory=list)
    chain: tuple[str, ...] = ()
    actions: list[str] = field(default_factory=list)
    _visited: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Seed the loop-detection set with the normalized requested URL."""
        self._visited = [normalize_url(self.requested_url)]

    @property
    def visited(self) -> tuple[str, ...]:
        """Normalized URLs already requested on this chain, for loop detection."""
        return tuple(self._visited)

    def record_hop(self, status: int, next_url: str) -> None:
        """Record one validated hop and advance the current URL."""
        self.hops.append(RedirectHop(status=status, from_url=self.current_url, to_url=next_url))
        self._visited.append(normalize_url(next_url))
        self.current_url = next_url


class SecClient:
    """Controlled client for approved official SEC sources."""

    def __init__(
        self,
        transport: Transport,
        user_agent: str,
        limiter: AggregateRateLimiter,
        policy: RetrievalPolicy | None = None,
        *,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        if not user_agent.strip():
            message = (
                "SecClient requires a validated contact identity; call "
                "ProjectConfig.require_sec_user_agent() before constructing a client"
            )
            raise ProhibitedRetrievalError(message)
        self._transport = transport
        self._user_agent = user_agent
        self._limiter = limiter
        self._policy = policy or RetrievalPolicy()
        self._sleeper = sleeper or _time.sleep
        self._logger = get_logger(_LOGGER_NAME)
        self._request_count = 0

    @property
    def request_count(self) -> int:
        """Number of transport requests issued."""
        return self._request_count

    # -- public API --------------------------------------------------------- #
    def fetch(
        self,
        source_id: str,
        *,
        purpose: str,
        parameters: Mapping[str, str] | None = None,
        evidence_id: str | None = None,
        etag: str | None = None,
        last_modified: str | None = None,
        stream: bool = False,
    ) -> FetchResult:
        """Retrieve one approved source with full policy enforcement.

        Args:
            source_id: Registered source identifier.
            purpose: Why this retrieval is needed. Required for the audit record,
                and mandatory for entity-specific sources.
            parameters: URL-template parameters.
            evidence_id: Required for a manifest-resolved source, such as a
                date-specific calendar announcement. The URL comes from the reviewed
                manifest, never from the caller (Decision 011 section 7).
            etag: Preserved entity tag, sent as ``If-None-Match``.
            last_modified: Preserved timestamp, sent as ``If-Modified-Since``.
            stream: Whether to stream rather than buffer the body.
        """
        spec = require_registered(source_id)
        if not purpose.strip():
            message = f"retrieval of {source_id!r} requires a recorded purpose"
            raise ProhibitedRetrievalError(message)
        if spec.is_entity_specific and len(purpose.strip()) < 12:
            message = (
                f"entity-specific retrieval of {source_id!r} requires an explicit purpose; "
                f"received {purpose!r}"
            )
            raise ProhibitedRetrievalError(message)

        url = self._resolve_url(spec, parameters, evidence_id)
        if filing_body_url_is_prohibited(url):
            message = (
                f"refusing to retrieve {url}: Stage M2.2 retrieves metadata only and never "
                "a filing body or accession package"
            )
            raise ProhibitedRetrievalError(message)
        try:
            validate_url(url, spec, role="request", identity_url=url)
        except RedirectBoundaryError as exc:
            raise ProhibitedRetrievalError(str(exc)) from exc

        return self._fetch_with_policy(
            spec,
            url,
            purpose=purpose,
            identity=request_identity(spec.source_id, url, dict(parameters or {})),
            etag=etag,
            last_modified=last_modified,
            stream=stream,
        )

    # -- internals ---------------------------------------------------------- #
    @staticmethod
    def _resolve_url(
        spec: SourceSpec,
        parameters: Mapping[str, str] | None,
        evidence_id: str | None,
    ) -> str:
        """Resolve the official URL, refusing caller-supplied announcement URLs."""
        supplied = dict(parameters or {})
        if not spec.manifest_resolved:
            if "announcement_url" in supplied:
                message = f"source {spec.source_id!r} does not accept a caller-supplied URL"
                raise ProhibitedRetrievalError(message)
            if spec.source_id == "sec_submissions_entity":
                raw_cik = supplied.get("cik_padded", "")
                try:
                    padded = normalize_cik(raw_cik)[1]
                except IdentifierError as exc:
                    message = f"entity submissions request has invalid CIK identity: {exc}"
                    raise ProhibitedRetrievalError(message) from exc
                if raw_cik != padded:
                    message = (
                        "entity submissions request requires the canonical ten-digit "
                        f"cik_padded value; received {raw_cik!r}"
                    )
                    raise ProhibitedRetrievalError(message)
            if spec.source_id == "sec_submissions_historical":
                filename = supplied.get("historical_file", "")
                if _HISTORICAL_FILE.fullmatch(filename) is None:
                    message = (
                        "historical submissions requests require the exact SEC-referenced "
                        f"filename CIK##########-submissions-###.json; received {filename!r}"
                    )
                    raise ProhibitedRetrievalError(message)
            return spec.url(**supplied)

        if supplied.get("announcement_url"):
            message = (
                f"source {spec.source_id!r} is manifest-resolved: pass evidence_id, not a "
                "caller-supplied announcement_url. Arbitrary URLs are not retrievable."
            )
            raise ProhibitedRetrievalError(message)
        if not evidence_id:
            message = (
                f"source {spec.source_id!r} requires an evidence_id from the reviewed "
                "calendar-evidence manifest"
            )
            raise ProhibitedRetrievalError(message)
        return require_evidence(evidence_id).url

    def _build_request(
        self,
        spec: SourceSpec,
        url: str,
        *,
        purpose: str,
        etag: str | None,
        last_modified: str | None,
        stream: bool,
    ) -> SecRequest:
        headers: dict[str, str] = {
            "User-Agent": self._user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": self._accept_header(spec.expected_content),
        }
        if spec.supports_conditional_requests:
            if etag:
                headers["If-None-Match"] = etag
            if last_modified:
                headers["If-Modified-Since"] = last_modified
        return SecRequest(
            url=url,
            headers=headers,
            timeout_connect=self._policy.connect_timeout_seconds,
            timeout_read=self._policy.read_timeout_for(spec),
            purpose=purpose,
            source_id=spec.source_id,
            stream=stream,
            follow_redirects=False,
        )

    @staticmethod
    def _accept_header(kind: ContentKind) -> str:
        return {
            "json": "application/json",
            "zip": "application/zip",
            "html": "text/html",
            "text": "text/plain",
        }[kind]

    def _fetch_with_policy(  # noqa: PLR0912, PLR0915 - one explicit policy loop
        self,
        spec: SourceSpec,
        url: str,
        *,
        purpose: str,
        identity: str,
        etag: str | None,
        last_modified: str | None,
        stream: bool,
    ) -> FetchResult:
        state = _Attempt(
            spec=spec,
            requested_url=url,
            current_url=url,
            purpose=purpose,
            identity=identity,
            sent_etag=etag if spec.supports_conditional_requests else None,
            sent_last_modified=last_modified if spec.supports_conditional_requests else None,
        )
        request = self._build_request(
            spec,
            url,
            purpose=purpose,
            etag=etag,
            last_modified=last_modified,
            stream=stream,
        )
        cooldowns = 0

        while True:
            try:
                validate_url(
                    state.current_url,
                    spec,
                    role="request",
                    identity_url=state.requested_url,
                )
            except RedirectBoundaryError as exc:
                state.actions.append("pre_request_boundary_refused")
                return self._boundary_failure(
                    state,
                    TransportResponse(
                        status=0,
                        headers={},
                        final_url=state.current_url,
                        failure="connection_error",
                    ),
                    exc,
                )
            self._limiter.acquire()
            self._request_count += 1
            state.http_attempts += 1
            self._logger.info(
                "sec request source=%s url=%s request=%d retry_ordinal=%d "
                "hop=%d stream=%s purpose=%s headers=%s",
                spec.source_id,
                state.current_url,
                state.http_attempts,
                state.retry_ordinal,
                len(state.hops),
                stream,
                purpose,
                dict(request.redacted_headers()),
            )
            response = self._transport.send(request)

            if response.redirects:
                state.actions.append("transport_redirect_history_refused")
                hidden = ", ".join(response.redirects)
                hidden_error = RedirectBoundaryError(
                    "transport followed redirect history outside the policy-owned "
                    f"hop loop: {hidden}",
                    "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
                )
                return self._boundary_failure(
                    state,
                    response,
                    hidden_error,
                    transport_redirects=response.redirects,
                )

            if response.succeeded_at_transport_level and response.status in REDIRECT_STATUSES:
                try:
                    next_url = resolve_redirect(
                        response.header("location") or "",
                        state.current_url,
                        spec,
                        seen=state.visited,
                        identity_url=state.requested_url,
                    )
                except RedirectBoundaryError as exc:
                    state.actions.append("redirect_refused")
                    return self._boundary_failure(state, response, exc)
                response.close()
                state.record_hop(response.status, next_url)
                self._logger.info(
                    "sec redirect source=%s status=%d to=%s",
                    spec.source_id,
                    response.status,
                    next_url,
                )
                request = self._build_request(
                    spec,
                    next_url,
                    purpose=purpose,
                    etag=etag,
                    last_modified=last_modified,
                    stream=stream,
                )
                continue

            if response.succeeded_at_transport_level:
                try:
                    if not response.final_url.strip():
                        message = (
                            "transport did not report a terminal URL for a successful response"
                        )
                        raise RedirectBoundaryError(
                            message,
                            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
                        )
                    reported_final = validate_url(
                        response.final_url,
                        spec,
                        role="final URL",
                        identity_url=state.requested_url,
                    )
                    validated_current = validate_url(
                        state.current_url,
                        spec,
                        role="request",
                        identity_url=state.requested_url,
                    )
                    if reported_final != validated_current:
                        message = (
                            "transport reported a terminal URL different from the "
                            "policy-validated request without exposing its redirect hop"
                        )
                        raise RedirectBoundaryError(
                            message,
                            "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
                        )
                    state.chain = validate_chain(
                        state.requested_url,
                        tuple(state.hops),
                        reported_final,
                        spec,
                    )
                except RedirectBoundaryError as exc:
                    state.actions.append("boundary_refused")
                    return self._boundary_failure(state, response, exc)

            if response.succeeded_at_transport_level and response.status == 304:
                state.actions.append("not_modified")
                response.close()
                return FetchResult(
                    outcome="not_modified",
                    source_id=spec.source_id,
                    url=state.requested_url,
                    purpose=purpose,
                    status=304,
                    etag=response.etag or etag,
                    last_modified=response.last_modified or last_modified,
                    provenance_headers=self._selected_headers(response),
                    redirects=state.chain,
                    redirect_hops=tuple(state.hops),
                    final_url=state.current_url,
                    identity=identity,
                    sent_etag=state.sent_etag,
                    sent_last_modified=state.sent_last_modified,
                    attempts=state.http_attempts,
                    detail="official content unchanged; the preserved snapshot is reused",
                    actions=tuple(state.actions),
                )

            first_chunk, rebuilt_chunks = self._peek(response.chunks)

            if not response.succeeded_at_transport_level:
                action = classify_transport_failure(
                    response.failure or "connection_error", attempt=state.retry_ordinal
                )
            else:
                action = self._classify(
                    spec, response, attempt=state.retry_ordinal, first_chunk=first_chunk
                )
            state.actions.append(action.kind)

            if action.kind == "proceed":
                return self._retrieved(state, response, rebuilt_chunks)
            if action.kind == "quarantine":
                return self._terminal(
                    "quarantined",
                    state,
                    response,
                    action,
                    chunks=rebuilt_chunks,
                )
            if rebuilt_chunks is not None:
                rebuilt_chunks.close()
            if action.kind == "fail":
                return self._terminal("failed", state, response, action)

            if action.kind == "cooldown":
                if cooldowns >= 1:
                    # A second cooldown ends the retrieval. A block page or a 403
                    # already carries SEC_BLOCK_PAGE, but an unqualified 429 cooldown
                    # carries no reason code, so returning the action unchanged would
                    # produce a terminal failure with no registered reason. The two
                    # adjacent terminal branches apply the same fallback, for the same
                    # purpose: no consumer may read this failure as an empty dataset.
                    state.actions.append("second_cooldown_terminal")
                    halted = ResponseAction(
                        kind="fail",
                        reason=(
                            f"{action.reason}; aggregate traffic had already halted once, "
                            "so the retrieval is terminal"
                        ),
                        reason_code=action.reason_code or "SEC_RETRIES_EXHAUSTED",
                        halts_aggregate_traffic=action.halts_aggregate_traffic,
                    )
                    return self._terminal("failed", state, response, halted)
                cooldowns += 1
                delay = max(action.delay_seconds, self._policy.cooldown_seconds)
                self._logger.warning(
                    "halting aggregate SEC traffic for %.0f seconds: %s",
                    delay,
                    action.reason,
                )
                self._limiter.halt(delay)
                continue

            # retry or retry_after
            if cooldowns >= 1:
                # Refusing the retry ends the retrieval, and a retry action carries no
                # reason code while it is still retryable. The terminal result must name
                # a registered reason for the same purpose as the exhaustion branch
                # below: no consumer may read this failure as an empty dataset.
                state.actions.append("post_cooldown_retry_refused")
                terminal_action = ResponseAction(
                    kind="fail",
                    reason=(
                        f"{action.reason}; the one controlled post-cooldown request "
                        "was terminal, so no further request was issued"
                    ),
                    reason_code=action.reason_code or "SEC_RETRIES_EXHAUSTED",
                )
                return self._terminal("failed", state, response, terminal_action)
            if state.retry_ordinal >= self._policy.max_transient_retries:
                # A retry action carries no reason code while it is still retryable.
                # Exhausting the budget makes it terminal, and a terminal failure must
                # always name a registered reason so no consumer can read it as an
                # empty dataset.
                state.actions.append("retry_budget_exhausted")
                exhausted = ResponseAction(
                    kind="fail",
                    reason=(
                        f"{action.reason}; retries exhausted after {state.http_attempts} attempts"
                    ),
                    reason_code=action.reason_code or "SEC_RETRIES_EXHAUSTED",
                )
                return self._terminal("failed", state, response, exhausted)
            if action.delay_seconds > 0:
                self._sleeper(action.delay_seconds)
            state.retry_ordinal += 1

    def _classify(
        self,
        spec: SourceSpec,
        response: TransportResponse,
        *,
        attempt: int,
        first_chunk: bytes | None = None,
    ) -> ResponseAction:
        # Streamed payloads are validated from their peeked first chunk, so a block
        # page, an empty stream, or a missing archive signature is caught without
        # buffering the whole artifact.
        inspected = response.body if first_chunk is None else first_chunk
        action = classify_response(
            response.status,
            response.headers,
            self._prefix(inspected),
            content_length=len(inspected),
            expected=_EXPECTED_PAYLOAD[spec.expected_content],
            attempt=attempt,
            is_recent_filing=False,
        )
        if action.kind != "proceed":
            return action

        declared = response.content_type
        if declared is not None and declared not in ACCEPTABLE_CONTENT_TYPES[spec.expected_content]:
            return ResponseAction(
                kind="quarantine",
                reason=(
                    f"declared content type {declared!r} is not acceptable for "
                    f"{spec.expected_content!r}"
                ),
                reason_code="SEC_RESPONSE_MALFORMED",
            )
        if first_chunk is None and len(response.body) > MAX_IN_MEMORY_BYTES:
            return ResponseAction(
                kind="quarantine",
                reason="buffered payload exceeds the in-memory limit; stream it instead",
                reason_code="SEC_RESPONSE_MALFORMED",
            )
        return action

    @staticmethod
    def _prefix(body: bytes) -> str:
        return body[:BODY_PREFIX_BYTES].decode("utf-8", errors="replace")

    @staticmethod
    def _peek(
        chunks: CloseableByteStream | None,
    ) -> tuple[bytes | None, CloseableByteStream | None]:
        """Read the first chunk for validation and hand back an intact iterator."""
        if chunks is None:
            return None, None
        first = next(chunks, b"")
        if not first:
            chunks.close()
            return b"", None
        rebuilt = CloseableByteStream(
            itertools.chain([first], chunks),
            close_callback=chunks.close,
        )
        return first, rebuilt

    def _retrieved(
        self,
        state: _Attempt,
        response: TransportResponse,
        chunks: CloseableByteStream | None = None,
    ) -> FetchResult:
        if state.hops:
            self._logger.info(
                "sec validated redirect chain source=%s chain=%s",
                state.spec.source_id,
                list(state.chain),
            )
        return FetchResult(
            outcome="retrieved",
            source_id=state.spec.source_id,
            url=state.requested_url,
            purpose=state.purpose,
            status=response.status,
            body=response.body,
            chunks=chunks,
            etag=response.etag,
            last_modified=response.last_modified,
            declared_content_type=response.content_type,
            content_encoding=response.content_encoding,
            provenance_headers=self._selected_headers(response),
            redirects=state.chain,
            redirect_hops=tuple(state.hops),
            final_url=state.current_url,
            identity=state.identity,
            sent_etag=state.sent_etag,
            sent_last_modified=state.sent_last_modified,
            attempts=state.http_attempts,
            detail="retrieved",
            actions=tuple(state.actions),
        )

    def _terminal(
        self,
        outcome: FetchOutcome,
        state: _Attempt,
        response: TransportResponse,
        action: ResponseAction,
        *,
        chunks: CloseableByteStream | None = None,
    ) -> FetchResult:
        self._logger.error(
            "sec retrieval %s source=%s status=%s reason=%s",
            outcome,
            state.spec.source_id,
            response.status if response.succeeded_at_transport_level else "transport-failure",
            action.reason,
        )
        body = b"" if outcome == "failed" else response.body
        preserved_chunks = chunks
        if outcome == "quarantined" and chunks is not None:
            # A streamed payload lives in the spool, not in ``response.body``. Recording
            # the empty body here would destroy the very evidence quarantine exists to
            # keep, so the spool is drained into the body and then closed. The stream is
            # not handed on: it has already been consumed, and a half-read iterator would
            # be a second owner of a closed resource.
            body = self._drain_for_quarantine(state, chunks)
            preserved_chunks = None
        return FetchResult(
            outcome=outcome,
            source_id=state.spec.source_id,
            url=state.requested_url,
            purpose=state.purpose,
            status=response.status if response.succeeded_at_transport_level else None,
            body=body,
            chunks=preserved_chunks,
            etag=response.etag,
            last_modified=response.last_modified,
            declared_content_type=response.content_type,
            content_encoding=response.content_encoding,
            provenance_headers=self._selected_headers(response),
            redirects=state.chain,
            redirect_hops=tuple(state.hops),
            final_url=state.current_url,
            identity=state.identity,
            sent_etag=state.sent_etag,
            sent_last_modified=state.sent_last_modified,
            attempts=state.http_attempts,
            reason_code=action.reason_code,
            detail=action.reason,
            actions=tuple(state.actions),
        )

    def _drain_for_quarantine(
        self,
        state: _Attempt,
        chunks: CloseableByteStream,
    ) -> bytes:
        """Materialize a spooled payload so quarantined evidence is preserved.

        Reading is bounded by the same in-memory ceiling the buffered path uses, so a
        pathological response cannot be pulled entirely into memory just because it was
        rejected. When the bound is reached the prefix already read is kept: a truncated
        artifact is still evidence, and it is marked as such in the log. The spool is
        closed on every path, including an iteration failure.
        """
        collected = bytearray()
        truncated = False
        try:
            for chunk in chunks:
                remaining = MAX_IN_MEMORY_BYTES - len(collected)
                if remaining <= 0:
                    truncated = True
                    break
                collected.extend(chunk[:remaining])
                if len(chunk) > remaining:
                    truncated = True
                    break
        except OSError as exc:
            self._logger.error(
                "sec quarantine spool read failed source=%s: %s", state.spec.source_id, exc
            )
        finally:
            chunks.close()
        if truncated:
            self._logger.warning(
                "sec quarantine evidence truncated at %d bytes source=%s",
                MAX_IN_MEMORY_BYTES,
                state.spec.source_id,
            )
        return bytes(collected)

    @staticmethod
    def _selected_headers(response: TransportResponse) -> Mapping[str, str]:
        """Return only response headers approved for immutable provenance."""
        selected: dict[str, str] = {}
        for name in _PROVENANCE_HEADERS:
            value = response.header(name)
            if value is not None:
                selected[name] = value
        return selected

    def _boundary_failure(
        self,
        state: _Attempt,
        response: TransportResponse,
        exc: RedirectBoundaryError,
        *,
        transport_redirects: tuple[str, ...] = (),
    ) -> FetchResult:
        """Fail closed when a hop or the final URL left the approved boundary.

        The payload is discarded: a response reached outside the registered source
        family is never parsed, and never reported as an empty dataset.
        """
        self._logger.error(
            "sec redirect boundary refused source=%s reason=%s", state.spec.source_id, exc
        )
        response.close()
        return FetchResult(
            outcome="failed",
            source_id=state.spec.source_id,
            url=state.requested_url,
            purpose=state.purpose,
            status=response.status if response.succeeded_at_transport_level else None,
            redirects=transport_redirects or state.chain,
            redirect_hops=tuple(state.hops),
            final_url=response.final_url or state.current_url,
            identity=state.identity,
            sent_etag=state.sent_etag,
            sent_last_modified=state.sent_last_modified,
            attempts=state.http_attempts,
            reason_code=exc.reason_code,
            detail=str(exc),
            actions=tuple(state.actions),
        )
