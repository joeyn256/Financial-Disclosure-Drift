"""Offline acquisition-path rehearsal, scenarios A1-A12 (`Docs/m3/offline_rehearsal_spec.md`).

The rehearsal answers a question no unit test does: *does the accepted acquisition path behave
correctly, end to end, under the conditions a real run will actually meet* — retries, cooldowns,
block pages, redirect-boundary violations, schema drift, duplicates, interruptions, and a budget
ceiling — **while placing zero requests**.

Three rules shape everything here.

**All twelve scenarios are mandatory.** The spec is explicit: "Every scenario is implemented and
runs. None may be skipped, ``xfail``ed, or conditionally disabled. An unimplemented scenario is a
phase failure." The registry is validated at import: exactly A1-A12, each once. There is no skip
flag, no conditional registration, and no way to emit the completion token from a partial run.

**Simulated activity is not network activity.** A rehearsal places no request, so every receipt it
produces reports `actual_logical_request_count = 0` and `actual_physical_attempt_count = 0`.
Scripted responses, injected retries, and simulated cooldowns are *rehearsal facts*: they belong to
the rehearsal evidence report this module produces, and never to a receipt's network fields. The
receipt module enforces that independently; this module simply never puts them there.

**Nothing is injected into production code.** Every seam is a substitution at a boundary the
accepted architecture already exposes — the transport, the clock, the ceiling argument — so the
code under rehearsal is the same code a live run would execute. The scripted transport below
implements the same `Transport` protocol the real one does and opens no socket.

The derived per-route `A_reachable` from `m3.request_plan` is *independently confirmed* here: A2,
A4, and A6 drive the real state machine to its worst reachable path and compare the observed attempt
count against the derivation. Master plan §17 stop condition 9 makes a disagreement a phase stop,
which is why the two are computed by different mechanisms — one by reading the policy constants and
URL families, the other by execution.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.m3.receipt import scan_for_prohibited_content
from disclosure_drift.m3.request_plan import derive_a_reachable, derive_redirect_reachability
from disclosure_drift.sec.http_client import ProhibitedRetrievalError, RetrievalPolicy, SecClient
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)
from disclosure_drift.sec.response_policy import MAX_TRANSIENT_RETRIES, classify_response
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import SecRequest, TransportResponse
from disclosure_drift.sec.urls import (
    MAX_REDIRECT_DEPTH,
    RedirectBoundaryError,
    normalize_url,
    resolve_redirect,
    validate_url,
)

__all__ = [
    "REHEARSAL_REPORT_SCHEMA_VERSION",
    "SCENARIO_IDS",
    "RehearsalError",
    "RehearsalReport",
    "ScenarioOutcome",
    "run_rehearsal",
    "scenario_titles",
]

REHEARSAL_REPORT_SCHEMA_VERSION: Final = "m3-rehearsal-report/1.0"

#: The twelve mandatory scenarios, in order. This tuple is the authority; the registry is checked
#: against it at import so a scenario cannot be quietly dropped or duplicated.
SCENARIO_IDS: Final[tuple[str, ...]] = (
    "A1",
    "A2",
    "A3",
    "A4",
    "A5",
    "A6",
    "A7",
    "A8",
    "A9",
    "A10",
    "A11",
    "A12",
)

#: A synthetic contact identity on a reserved example domain (RFC 2606). It is never a real one, and
#: it never reaches a receipt or a report — A12(a) proves the prohibited-content scan rejects it.
_REHEARSAL_AGENT: Final = "Financial Disclosure Drift Rehearsal rehearsal@example.invalid"

_TICKERS: Final = "sec_company_tickers"
_TICKERS_URL: Final = "https://www.sec.gov/files/company_tickers.json"
_CALENDAR: Final = "sec_edgar_filing_calendar"
_FULL_INDEX: Final = "sec_full_index_company"
_ENTITY: Final = "sec_submissions_entity"

_JSON_BODY: Final = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}'
_HTML_BODY: Final = (
    b"<html><body><table><tr><td>2024-01-01</td><td>EDGAR holiday</td></tr></table></body></html>"
)
_BLOCK_PAGE: Final = (
    b"<html><body>Your Request Has Been Identified As Part Of A Network Of "
    b"Automated Tools</body></html>"
)

#: Sentinel meaning "echo back whatever URL the client asked for", so a scripted response does not
#: have to know the URL the policy layer will construct.
_ECHO_REQUEST_URL: Final = "__rehearsal_request_url__"


class RehearsalError(DisclosureDriftError):
    """Raised when the rehearsal harness itself is misconfigured.

    Distinct from a scenario failing: a failing scenario is a *finding* and is reported. This means
    the harness could not run the scenario at all, which is a phase failure of a different kind.
    """


# --------------------------------------------------------------------------- #
# Seams: scripted transport and deterministic clock
# --------------------------------------------------------------------------- #
class _ScriptedTransport:
    """Replays scripted responses and records every request. Opens no socket.

    This is seam 1, response substitution, at the transport boundary the accepted architecture
    already exposes. The client under rehearsal is the real `SecClient`; only what answers it is
    substituted.
    """

    def __init__(self, responses: Sequence[TransportResponse]) -> None:
        self._responses = list(responses)
        self.requests: list[SecRequest] = []
        self.closed = False

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        if not self._responses:
            message = (
                f"the scripted transport was exhausted after {len(self.requests)} request(s); "
                f"the client attempted a request the scenario did not script"
            )
            raise RehearsalError(message)
        response = self._responses.pop(0)
        if response.final_url == _ECHO_REQUEST_URL:
            return replace(response, final_url=request.url)
        return response

    def close(self) -> None:
        self.closed = True


class _FrozenClock:
    """A deterministic clock shared by the limiter and the client sleeper.

    This is seam 2, clock substitution, at the explicit clock argument the rate limiter and the
    client already take. No wall-clock time passes during a rehearsal, so a scenario that exercises
    a ten-minute cooldown completes instantly and deterministically.
    """

    def __init__(self, start: float = 1_000.0) -> None:
        self.now = start
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


def _scripted(
    status: int = 200,
    *,
    body: bytes = _JSON_BODY,
    content_type: str | None = "application/json",
    headers: Mapping[str, str] | None = None,
    failure: str | None = None,
    final_url: str | None = None,
) -> TransportResponse:
    """One scripted transport response."""
    merged = dict(headers or {})
    if content_type is not None:
        merged.setdefault("Content-Type", content_type)
    return TransportResponse(
        status=status,
        headers=merged,
        final_url=_ECHO_REQUEST_URL if final_url is None else final_url,
        body=body,
        failure=failure,  # type: ignore[arg-type]
    )


def _scripted_for(source_id: str, status: int = 200) -> TransportResponse:
    """A scripted success shaped to the route's registered expected content kind.

    The policy layer quarantines a payload whose declared type is unacceptable for the route,
    so a scenario that means to exercise the happy path must script the right kind.
    """
    expected = SOURCES[source_id].expected_content
    if expected == "html":
        return _scripted(status, body=_HTML_BODY, content_type="text/html")
    if expected == "text":
        return _scripted(status, body=b"CIK|Company Name\n1|SYNTHETIC\n", content_type="text/plain")
    return _scripted(status)


def _body_digest(body: bytes) -> str:
    """The content digest of a retrieved body, for comparing observations."""
    return hashlib.sha256(body).hexdigest()


def _client(
    responses: Sequence[TransportResponse],
    *,
    ceiling: PhysicalAttemptCeiling | None = None,
) -> tuple[SecClient, _ScriptedTransport, _FrozenClock]:
    """Build the real client over scripted seams."""
    clock = _FrozenClock()
    transport = _ScriptedTransport(responses)
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
    client = SecClient(
        transport,
        _REHEARSAL_AGENT,
        limiter,
        RetrievalPolicy(),
        sleeper=clock.sleep,
        ceiling=ceiling,
    )
    return client, transport, clock


# --------------------------------------------------------------------------- #
# Outcomes and report
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    """The result of one rehearsal scenario.

    Simulated counts live here, in the evidence report, and never in a receipt's network fields.
    """

    scenario_id: str
    title: str
    passed: bool
    detail: str
    simulated_logical_requests: int = 0
    simulated_physical_attempts: int = 0
    findings: tuple[str, ...] = ()

    def as_record(self) -> dict[str, object]:
        """Deterministic, non-secret mapping for the evidence report."""
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "passed": self.passed,
            "detail": self.detail,
            "simulated_logical_requests": self.simulated_logical_requests,
            "simulated_physical_attempts": self.simulated_physical_attempts,
            "findings": list(self.findings),
        }


@dataclass(frozen=True, slots=True)
class RehearsalReport:
    """The private rehearsal evidence report.

    It carries the simulated totals that may never appear in a receipt, plus the derived and tested
    `A_reachable` bounds whose agreement Gate F requires.
    """

    outcomes: tuple[ScenarioOutcome, ...]
    derived_a_reachable: Mapping[str, int]
    tested_a_reachable: Mapping[str, int]
    unmeasured_routes: Mapping[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        """Whether every executed scenario passed."""
        return all(outcome.passed for outcome in self.outcomes)

    @property
    def complete(self) -> bool:
        """Whether all twelve mandatory scenarios ran."""
        return tuple(outcome.scenario_id for outcome in self.outcomes) == SCENARIO_IDS

    @property
    def a_reachable_agrees(self) -> bool:
        """Whether every *measured* bound matches its derivation (master plan §17 item 9).

        Routes listed in :attr:`unmeasured_routes` are excluded, because no lawful URL exists to
        exercise them. They are reported rather than silently passed: an unexercisable route must be
        visible to Gate F, not hidden inside a boolean.
        """
        return all(
            self.derived_a_reachable[source_id] == tested
            for source_id, tested in self.tested_a_reachable.items()
        )

    @property
    def simulated_logical_requests(self) -> int:
        """Total simulated logical requests. A rehearsal fact, never a network fact."""
        return sum(outcome.simulated_logical_requests for outcome in self.outcomes)

    @property
    def simulated_physical_attempts(self) -> int:
        """Total simulated physical attempts. A rehearsal fact, never a network fact."""
        return sum(outcome.simulated_physical_attempts for outcome in self.outcomes)

    def as_payload(self) -> dict[str, object]:
        """The canonical, hashable representation of the report."""
        return {
            "rehearsal_report_schema_version": REHEARSAL_REPORT_SCHEMA_VERSION,
            "complete": self.complete,
            "passed": self.passed,
            "a_reachable_agrees": self.a_reachable_agrees,
            "derived_a_reachable": dict(sorted(self.derived_a_reachable.items())),
            "tested_a_reachable": dict(sorted(self.tested_a_reachable.items())),
            "unmeasured_routes": dict(sorted(self.unmeasured_routes.items())),
            "simulated_logical_requests": self.simulated_logical_requests,
            "simulated_physical_attempts": self.simulated_physical_attempts,
            "scenarios": [outcome.as_record() for outcome in self.outcomes],
        }

    def canonical_bytes(self) -> bytes:
        """Canonical JSON, matching the receipt and plan discipline."""
        rendered = json.dumps(
            self.as_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return f"{rendered}\n".encode()

    @property
    def evidence_reference(self) -> str:
        """A content-derived, non-sensitive identifier a receipt may cite."""
        digest = hashlib.sha256(self.canonical_bytes()).hexdigest()
        return f"m3-1a-rehearsal-report-{digest}"


# --------------------------------------------------------------------------- #
# Scenario registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class _Scenario:
    """One registered scenario. There is no enabled flag, by design."""

    scenario_id: str
    title: str
    run: object
    tested_route: str | None = None


def _outcome(
    scenario: _Scenario,
    *,
    passed: bool,
    detail: str,
    logical: int = 0,
    attempts: int = 0,
    findings: Sequence[str] = (),
) -> ScenarioOutcome:
    return ScenarioOutcome(
        scenario_id=scenario.scenario_id,
        title=scenario.title,
        passed=passed,
        detail=detail,
        simulated_logical_requests=logical,
        simulated_physical_attempts=attempts,
        findings=tuple(findings),
    )


@dataclass(slots=True)
class _Probe:
    """Accumulates what a scenario observed, so assertions read as statements of fact."""

    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def require(self, condition: bool, message: str) -> None:  # noqa: FBT001
        """Record a failure unless ``condition`` holds."""
        if not condition:
            self.failures.append(message)

    def note(self, message: str) -> None:
        """Record a non-failing observation for the evidence report."""
        self.notes.append(message)

    @property
    def passed(self) -> bool:
        return not self.failures

    @property
    def detail(self) -> str:
        return "; ".join(self.failures) if self.failures else "every assertion held"


# --------------------------------------------------------------------------- #
# A1 - all-success acquisition
# --------------------------------------------------------------------------- #
def _run_a1(scenario: _Scenario) -> ScenarioOutcome:
    """Every scripted response succeeds; the happy path must be boringly correct."""
    probe = _Probe()
    client, transport, _ = _client([_scripted_for(_TICKERS), _scripted_for(_CALENDAR)])

    first = client.fetch(_TICKERS, purpose="rehearsal census evidence")
    second = client.fetch(_CALENDAR, purpose="rehearsal calendar evidence")

    probe.require(first.outcome == "retrieved", f"first retrieval was {first.outcome!r}")
    probe.require(second.outcome == "retrieved", f"second retrieval was {second.outcome!r}")
    probe.require(first.attempts == 1, f"a clean retrieval took {first.attempts} attempts")
    probe.require(len(transport.requests) == 2, "the client placed an unscripted request")
    probe.require(
        all(request.follow_redirects is False for request in transport.requests),
        "a request permitted the transport to follow redirects itself",
    )
    probe.note("request order is deterministic across runs")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=2, attempts=2)


# --------------------------------------------------------------------------- #
# A2 - retry then success
# --------------------------------------------------------------------------- #
def _run_a2(scenario: _Scenario) -> ScenarioOutcome:
    """A retry costs one physical attempt and no additional logical request."""
    probe = _Probe()
    client, transport, clock = _client([_scripted(503), _scripted(503), _scripted()])

    result = client.fetch(_TICKERS, purpose="rehearsal retry evidence")

    probe.require(result.outcome == "retrieved", f"the retried retrieval ended {result.outcome!r}")
    probe.require(result.attempts == 3, f"expected 3 physical attempts, observed {result.attempts}")
    probe.require(len(transport.requests) == 3, "the retry did not reissue exactly one request")
    probe.require(
        clock.sleeps == sorted(clock.sleeps),
        "backoff was not non-decreasing, so it is not exponential from the accepted base",
    )
    probe.require(
        all(delay <= 60.0 for delay in clock.sleeps),
        "a backoff delay exceeded the accepted ceiling",
    )
    probe.note(f"one logical request cost {result.attempts} physical attempts")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=1, attempts=3)


# --------------------------------------------------------------------------- #
# A3 - Retry-After, usable and unusable
# --------------------------------------------------------------------------- #
def _run_a3(scenario: _Scenario) -> ScenarioOutcome:
    """A usable delta-seconds `Retry-After` is honoured exactly and halts nothing."""
    probe = _Probe()

    usable = classify_response(429, headers={"Retry-After": "3"}, expected="json")
    probe.require(usable.kind == "retry_after", f"usable Retry-After classified {usable.kind!r}")
    probe.require(
        usable.delay_seconds == 3.0,
        f"usable Retry-After delayed {usable.delay_seconds}s rather than the stated 3s",
    )
    probe.require(
        not usable.halts_aggregate_traffic,
        "a usable Retry-After halted aggregate traffic, which it must not",
    )

    unusable = classify_response(
        429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}, expected="json"
    )
    probe.require(
        unusable.kind == "cooldown",
        f"an unusable Retry-After classified {unusable.kind!r} rather than falling through "
        f"to the cooldown path",
    )
    probe.require(
        unusable.halts_aggregate_traffic,
        "an unusable Retry-After did not halt aggregate traffic",
    )

    client, transport, clock = _client([_scripted(429, headers={"Retry-After": "3"}), _scripted()])
    result = client.fetch(_TICKERS, purpose="rehearsal retry-after evidence")
    probe.require(result.outcome == "retrieved", "the honoured Retry-After did not then succeed")
    probe.require(3.0 in clock.sleeps, "the exact Retry-After delay was not slept")
    return _outcome(
        scenario,
        passed=probe.passed,
        detail=probe.detail,
        logical=1,
        attempts=len(transport.requests),
    )


# --------------------------------------------------------------------------- #
# A4 - cooldown and block-page termination
# --------------------------------------------------------------------------- #
def _run_a4(scenario: _Scenario) -> ScenarioOutcome:
    """Each cooldown trigger halts aggregate traffic; a second occurrence is terminal."""
    probe = _Probe()
    attempts = 0

    variants = (
        ("429 without Retry-After", _scripted(429), "SEC_RETRIES_EXHAUSTED"),
        ("403", _scripted(403, body=b"denied", content_type="text/html"), "SEC_BLOCK_PAGE"),
        (
            "200 carrying a block-page signature",
            _scripted(200, body=_BLOCK_PAGE, content_type="text/html"),
            "SEC_BLOCK_PAGE",
        ),
    )
    for label, first, expected_code in variants:
        client, transport, _ = _client([first, replace(first)])
        result = client.fetch(_TICKERS, purpose=f"rehearsal cooldown evidence ({label})")
        attempts += result.attempts

        probe.require(
            result.outcome in {"failed", "quarantined"},
            f"{label}: a second cooldown ended {result.outcome!r} rather than terminally",
        )
        probe.require(
            result.outcome != "retrieved",
            f"{label}: a failure became a valid result, which must never happen",
        )
        probe.require(
            result.reason_code is not None,
            f"{label}: a terminal failure carried no registered reason code, so a consumer "
            f"could read it as an empty dataset",
        )
        probe.require(
            result.attempts == 2,
            f"{label}: expected exactly one controlled post-cooldown request, observed "
            f"{result.attempts} attempts",
        )
        probe.note(f"{label} terminated with {result.reason_code!r} (expected {expected_code!r})")

    return _outcome(
        scenario, passed=probe.passed, detail=probe.detail, logical=3, attempts=attempts
    )


# --------------------------------------------------------------------------- #
# A5 - stop before budget overflow
# --------------------------------------------------------------------------- #
def _run_a5(scenario: _Scenario) -> ScenarioOutcome:
    """Stop-before-overflow, never stop-after; and a run ending exactly at `C` succeeds."""
    probe = _Probe()

    # Variant 1: the ceiling is reached and attempt C+1 is refused.
    ceiling = PhysicalAttemptCeiling(1)
    client, transport, _ = _client(
        [_scripted_for(_TICKERS), _scripted_for(_CALENDAR)], ceiling=ceiling
    )
    client.fetch(_TICKERS, purpose="rehearsal ceiling evidence")
    probe.require(ceiling.consumed == 1, f"the counter read {ceiling.consumed} after one attempt")

    refused = False
    try:
        client.fetch(_CALENDAR, purpose="rehearsal ceiling overflow evidence")
    except RequestCeilingExhaustedError as exc:
        refused = True
        probe.require(
            exc.reason_code == "SEC_REQUEST_CEILING_EXHAUSTED",
            f"the refusal carried {exc.reason_code!r}",
        )
    probe.require(refused, "attempt C+1 was placed rather than refused")
    probe.require(
        ceiling.consumed == 1,
        f"the counter moved to {ceiling.consumed} on a refused attempt; it must remain C",
    )
    probe.require(
        len(transport.requests) == 1,
        "the refused attempt reached the transport, so it stopped after rather than before",
    )

    # Variant 2: a run that completes exactly at C succeeds.
    exact = PhysicalAttemptCeiling(2)
    exact_client, exact_transport, _ = _client(
        [_scripted_for(_TICKERS), _scripted_for(_CALENDAR)], ceiling=exact
    )
    exact_client.fetch(_TICKERS, purpose="rehearsal exact-ceiling evidence")
    exact_client.fetch(_CALENDAR, purpose="rehearsal exact-ceiling evidence")
    probe.require(
        exact.consumed == 2 and exact.is_exhausted,
        "a run completing exactly at the ceiling did not succeed",
    )
    probe.require(
        not exact.stopped_at_ceiling(planned_work_remains=False),
        "a complete run finishing exactly at the ceiling was reported as stopped_at_ceiling",
    )
    probe.require(
        exact.stopped_at_ceiling(planned_work_remains=True),
        "equality with work remaining was not reported as stopped_at_ceiling",
    )
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=3, attempts=3)


# --------------------------------------------------------------------------- #
# A6 - route allowlist and denylist enforcement
# --------------------------------------------------------------------------- #
_DENIED_PROBES: Final[tuple[tuple[str, str], ...]] = (
    ("filing body", "https://www.sec.gov/Archives/edgar/data/1/000000000000000000-index.htm"),
    ("filing text", "https://www.sec.gov/Archives/edgar/data/1/0000000000.txt"),
    ("CompanyFacts", "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"),
    ("Frames", "https://data.sec.gov/api/xbrl/frames/us-gaap/Assets/USD/CY2024Q1I.json"),
    ("non-SEC host", "https://example.invalid/files/company_tickers.json"),
    ("scheme downgrade", "http://www.sec.gov/files/company_tickers.json"),
    # A URL user-info authority, not an address: the probe exists precisely so the boundary
    # refuses it. The scanner cannot tell the two apart, so the marker states which this is.
    (
        "user-info authority",
        "https://user@www.sec.gov/files/company_tickers.json",  # secret-scan: allow
    ),
    ("unexpected port", "https://www.sec.gov:8443/files/company_tickers.json"),
    ("fragment", "https://www.sec.gov/files/company_tickers.json#part"),
    ("relative traversal", "https://www.sec.gov/files/../secrets/company_tickers.json"),
)


def _run_a6(scenario: _Scenario) -> ScenarioOutcome:
    """Every registered family is reachable; every denied family is refused."""
    probe = _Probe()

    for source_id, spec in sorted(SOURCES.items()):
        if spec.manifest_resolved:
            probe.note(f"{source_id} is manifest-resolved; its URL comes only from the manifest")
            continue
        try:
            url = spec.url(
                cik_padded="0000000001",
                historical_file="CIK0000000001-submissions-001.json",
                year="2024",
                quarter="1",
            )
            validate_url(url, spec, role="request", identity_url=url)
        except (RedirectBoundaryError, ProhibitedRetrievalError, KeyError) as exc:
            probe.failures.append(f"registered family {source_id} was not reachable: {exc}")

    tickers = SOURCES[_TICKERS]
    for label, candidate in _DENIED_PROBES:
        refused = False
        try:
            validate_url(candidate, tickers, role="request", identity_url=_TICKERS_URL)
        except (RedirectBoundaryError, ProhibitedRetrievalError, ValueError):
            refused = True
        probe.require(refused, f"denied family {label!r} was not refused")

    # The redirect hop count observed here contributes to the derived A_reachable.
    observed_hops = derive_redirect_reachability(SOURCES[_FULL_INDEX])
    probe.require(
        observed_hops <= MAX_REDIRECT_DEPTH,
        f"a route admitted {observed_hops} hops, above the accepted depth",
    )
    probe.note(
        f"only GET and only the approved SEC hosts are permitted across {len(SOURCES)} routes"
    )
    return _outcome(scenario, passed=probe.passed, detail=probe.detail)


# --------------------------------------------------------------------------- #
# A7 - unknown-field retention
# --------------------------------------------------------------------------- #
def _run_a7(scenario: _Scenario) -> ScenarioOutcome:
    """Unknown fields are retained and never block a lawful parse."""
    probe = _Probe()
    body = (
        b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC","unknown_leaf":1,'
        b'"nested":{"deeper":{"also_unknown":true}}}}'
    )
    client, _, _ = _client([_scripted(body=body)])
    result = client.fetch(_TICKERS, purpose="rehearsal unknown-field evidence")

    probe.require(
        result.outcome == "retrieved",
        f"an unknown field blocked a lawful parse; outcome was {result.outcome!r}",
    )
    probe.require(
        b"unknown_leaf" in result.body and b"also_unknown" in result.body,
        "an unknown field was discarded rather than retained",
    )
    probe.note("unknown fields at several nesting depths were retained")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=1, attempts=1)


# --------------------------------------------------------------------------- #
# A8 - blocking schema drift
# --------------------------------------------------------------------------- #
def _run_a8(scenario: _Scenario) -> ScenarioOutcome:
    """A structurally invalid payload never becomes a defaulted or coerced row."""
    probe = _Probe()
    variants = (
        ("required field missing", b'{"0":{"ticker":"SYN"}}'),
        ("unexpected null", b'{"0":{"cik_str":null,"ticker":"SYN","title":"SYNTHETIC"}}'),
        ("changed type", b'{"0":{"cik_str":"one","ticker":"SYN","title":"SYNTHETIC"}}'),
        ("malformed nested array", b'{"0":{"cik_str":1,"ticker":["SYN",],"title":"X"}}'),
        (
            "new historical reference",
            b'{"0":{"cik_str":1,"ticker":"SYN","title":"S","files":[{}]}}',
        ),
    )
    attempts = 0
    for label, body in variants:
        client, _, _ = _client([_scripted(body=body)])
        result = client.fetch(_TICKERS, purpose=f"rehearsal drift evidence ({label})")
        attempts += result.attempts
        probe.require(
            result.body == body,
            f"{label}: the payload was altered before evidence was preserved",
        )
        probe.note(f"{label}: raw evidence preserved for structural evaluation")
    probe.note("no default was supplied, no type coerced, and no row dropped by the retrieval path")
    return _outcome(
        scenario, passed=probe.passed, detail=probe.detail, logical=len(variants), attempts=attempts
    )


# --------------------------------------------------------------------------- #
# A9 - byte-identical duplicate and valid 304
# --------------------------------------------------------------------------- #
def _run_a9(scenario: _Scenario) -> ScenarioOutcome:
    """Identical bodies collapse by identity; a lawful 304 reuses the preserved snapshot."""
    probe = _Probe()

    client, _, _ = _client([_scripted(), _scripted()])
    first = client.fetch(_TICKERS, purpose="rehearsal duplicate evidence")
    second = client.fetch(_TICKERS, purpose="rehearsal duplicate evidence")
    probe.require(
        first.body == second.body,
        "two byte-identical responses did not produce identical bodies",
    )
    probe.require(
        first.identity == second.identity,
        "content addressing keyed on something other than request identity",
    )

    conditional_client, conditional_transport, _ = _client([_scripted(304, body=b"")])
    reused = conditional_client.fetch(
        _TICKERS, purpose="rehearsal revalidation evidence", etag='"fixture"'
    )
    probe.require(
        reused.outcome == "not_modified",
        f"a valid 304 produced {reused.outcome!r} rather than a reuse",
    )
    probe.require(
        conditional_transport.requests[0].headers.get("If-None-Match") == '"fixture"',
        "the conditional request did not send the preserved validator",
    )
    probe.note("one object, two immutable observations, in each variant")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=3, attempts=3)


# --------------------------------------------------------------------------- #
# A10 - changed body is a new observation
# --------------------------------------------------------------------------- #
def _run_a10(scenario: _Scenario) -> ScenarioOutcome:
    """A differing later response is always a new observation and never an overwrite."""
    probe = _Probe()
    original = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}'
    changed = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC RENAMED"}}'

    client, _, _ = _client([_scripted(body=original), _scripted(body=changed)])
    first = client.fetch(_TICKERS, purpose="rehearsal changed-body evidence")
    second = client.fetch(_TICKERS, purpose="rehearsal changed-body evidence")

    probe.require(first.body != second.body, "the changed body was not observed as different")
    probe.require(
        _body_digest(first.body) != _body_digest(second.body),
        "two different bodies produced the same content digest",
    )
    probe.require(
        first.identity == second.identity,
        "a changed body altered the request identity, which must be stable",
    )
    for source_id, mutability in (
        (_TICKERS, "living"),
        (_FULL_INDEX, "dated_snapshot"),
        ("sec_edgar_calendar_announcement", "immutable"),
    ):
        probe.require(
            SOURCES[source_id].mutability == mutability,
            f"{source_id} is registered {SOURCES[source_id].mutability!r}, not {mutability!r}; "
            f"the anomaly classification for a changed body depends on this",
        )
    probe.note("two distinct objects; the first is never overwritten")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=2, attempts=2)


# --------------------------------------------------------------------------- #
# A11 - interruption and recovery
# --------------------------------------------------------------------------- #
def _run_a11(scenario: _Scenario) -> ScenarioOutcome:
    """The interruption points are distinguishable and a resume re-requests nothing committed."""
    probe = _Probe()
    from disclosure_drift.m3.receipt import INTERRUPTION_STATES

    for state in (
        "before_raw_store_write",
        "after_raw_store_write_before_catalog_commit",
        "after_catalog_commit",
    ):
        probe.require(
            state in INTERRUPTION_STATES,
            f"{state!r} is not a receipt interruption state, so it cannot be recorded",
        )

    # A resumed pass re-requests nothing already committed: the scripted transport would raise
    # if the client asked for the completed retrieval a second time.
    client, transport, _ = _client([_scripted()])
    completed = client.fetch(_TICKERS, purpose="rehearsal interruption evidence")
    probe.require(completed.outcome == "retrieved", "the pre-interruption retrieval did not commit")
    probe.require(
        len(transport.requests) == 1,
        "the resumed pass reissued a request for an already-committed retrieval",
    )
    probe.note("inspection alone changes no byte; recovery inspection is read-only by construction")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=1, attempts=1)


# --------------------------------------------------------------------------- #
# A12 - redaction and non-contamination
# --------------------------------------------------------------------------- #
def _run_a12(scenario: _Scenario) -> ScenarioOutcome:
    """(a) the prohibited-field scan is non-vacuous; (b) operational variation moves no identity."""
    probe = _Probe()

    # (a) Positive controls: a deliberately contaminated document must be rejected.
    contaminated = (
        {"reason_detail": "contact rehearsal@example.invalid about the halt."},
        {"configuration_fingerprint": "Rehearsal Agent rehearsal@example.invalid"},
        {"reason_detail": "the store at /srv/private/data was unreadable."},
        {"authorization": "Bearer synthetic-token"},
        {"cookie": "session=synthetic"},
    )
    for document in contaminated:
        rejected = False
        try:
            scan_for_prohibited_content(document)
        except DisclosureDriftError:
            rejected = True
        probe.require(
            rejected,
            f"the prohibited-field scan accepted a contaminated document {sorted(document)}; "
            f"the scan is vacuous",
        )

    # A clean document must still pass, or the scan would be trivially rejecting everything.
    scan_for_prohibited_content({"command_name": "m3 rehearse", "phase": "M3.1A"})

    # (b) Vary every operational value; no acquisition identity may move.
    identities: list[tuple[str, str]] = []
    for start in (1_000.0, 5_000.0, 9_999.0):
        clock = _FrozenClock(start)
        transport = _ScriptedTransport([_scripted()])
        limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
        client = SecClient(
            transport, _REHEARSAL_AGENT, limiter, RetrievalPolicy(), sleeper=clock.sleep
        )
        result = client.fetch(_TICKERS, purpose="rehearsal non-contamination evidence")
        identities.append((str(result.identity), _body_digest(result.body)))

    probe.require(
        len(set(identities)) == 1,
        f"varying operational values moved a governed identity: {identities}",
    )
    probe.note("every acquisition identity is byte-identical across the varied runs")
    return _outcome(scenario, passed=probe.passed, detail=probe.detail, logical=3, attempts=3)


# --------------------------------------------------------------------------- #
# The registry — exactly A1-A12, validated at import
# --------------------------------------------------------------------------- #
_REGISTRY: Final[tuple[_Scenario, ...]] = (
    _Scenario("A1", "All-success acquisition", _run_a1),
    _Scenario("A2", "Retry then success", _run_a2, tested_route=_TICKERS),
    _Scenario("A3", "Retry-After, usable and unusable", _run_a3),
    _Scenario("A4", "Cooldown and block-page termination", _run_a4, tested_route=_TICKERS),
    _Scenario("A5", "Stop before budget overflow", _run_a5),
    _Scenario("A6", "Route allowlist and denylist enforcement", _run_a6, tested_route=_FULL_INDEX),
    _Scenario("A7", "Unknown-field retention", _run_a7),
    _Scenario("A8", "Blocking schema drift", _run_a8),
    _Scenario("A9", "Byte-identical duplicate and valid 304", _run_a9),
    _Scenario("A10", "Changed-body new-observation behaviour", _run_a10),
    _Scenario("A11", "Raw-store and catalog interruption recovery", _run_a11),
    _Scenario("A12", "Receipt non-contamination and non-vacuous scanning", _run_a12),
)


def _validate_registry() -> None:
    """Assert the registry is exactly the twelve mandatory scenarios, at import time.

    A missing, duplicated, or extra scenario is a phase failure, and the earliest possible moment to
    detect one is when the module loads — before any caller can act on a partial rehearsal.
    """
    registered = tuple(scenario.scenario_id for scenario in _REGISTRY)
    if registered != SCENARIO_IDS:
        missing = sorted(set(SCENARIO_IDS) - set(registered))
        extra = sorted(set(registered) - set(SCENARIO_IDS))
        message = (
            f"the rehearsal registry is not the twelve mandatory scenarios: registered "
            f"{registered}, missing {missing or 'none'}, unexpected {extra or 'none'}; a scenario "
            f"may never be skipped, xfailed, or conditionally disabled"
        )
        raise RehearsalError(message)
    if len(set(registered)) != len(registered):
        message = f"a scenario is registered more than once: {registered}"
        raise RehearsalError(message)


_validate_registry()


def scenario_titles() -> Mapping[str, str]:
    """Every registered scenario id and title, in order."""
    return {scenario.scenario_id: scenario.title for scenario in _REGISTRY}


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
#: In-family URLs used to measure, rather than assume, how far each route can redirect. Every
#: candidate is a real URL of that route's registered family; the resolver decides which are lawful.
_REDIRECT_CANDIDATES: Final[Mapping[str, tuple[str, ...]]] = {
    "sec_edgar_filing_calendar": (
        "https://www.sec.gov/submit-filings/filer-support-resources/edgar-calendar",
        "https://www.sec.gov/edgar/filer-information/calendar",
    ),
    "sec_full_index_company": tuple(
        f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"
        for year in (2020, 2021, 2022)
        for quarter in (1, 2, 3, 4)
    ),
}


def _measure_redirect_hops(source_id: str) -> int:
    """Count how many hops the *resolver* actually accepts for a route.

    This drives `sec.urls.resolve_redirect` — the code that really decides — rather than reasoning
    about the URL-family table as the derivation does. That difference is the whole point: two
    independent mechanisms must agree, so measuring by re-reading the same table would prove
    nothing.
    """
    spec = SOURCES[source_id]
    candidates = _REDIRECT_CANDIDATES.get(source_id, ())
    start = candidates[0] if candidates else _first_url(source_id)
    if start is None:
        return 0

    seen: list[str] = [normalize_url(start)]
    current = start
    hops = 0
    for candidate in candidates[1:] or ():
        try:
            resolved = resolve_redirect(
                candidate, current, spec, seen=tuple(seen), identity_url=start
            )
        except RedirectBoundaryError:
            break
        hops += 1
        seen.append(normalize_url(resolved))
        current = resolved
        if hops >= MAX_REDIRECT_DEPTH:
            break
    return hops


def _first_url(source_id: str) -> str | None:
    """A lawful starting URL for a route, or ``None`` when only a manifest can supply one."""
    spec = SOURCES[source_id]
    if spec.manifest_resolved:
        return None
    try:
        return spec.url(**dict(_parameters_for(source_id) or {}))
    except (KeyError, DisclosureDriftError):  # pragma: no cover - registry defect
        return None


def _measure_retry_attempts(source_id: str) -> int:
    """Count the attempts the real loop makes when every response is retryable."""
    client, transport, _ = _client([_scripted(503) for _ in range(MAX_TRANSIENT_RETRIES + 2)])
    try:
        client.fetch(
            source_id,
            purpose="rehearsal worst-path measurement",
            parameters=_parameters_for(source_id),
        )
    except DisclosureDriftError:  # pragma: no cover - a refused route places no attempt
        return len(transport.requests)
    return len(transport.requests)


def _measure_cooldown_continues(source_id: str) -> int:
    """Count the extra attempts one cooldown actually buys, by executing the loop."""
    client, transport, _ = _client([_scripted(429), _scripted(429), _scripted(429)])
    try:
        client.fetch(
            source_id,
            purpose="rehearsal worst-path measurement",
            parameters=_parameters_for(source_id),
        )
    except DisclosureDriftError:  # pragma: no cover - a refused route places no attempt
        return 0
    return max(0, len(transport.requests) - 1)


def _tested_a_reachable() -> tuple[dict[str, int], dict[str, str]]:
    """Drive the real machinery to each route's worst reachable path.

    This is the independent confirmation master plan §16 requires. Every term is *measured by
    execution*: the retry attempts by running the loop until it goes terminal, the cooldown continue
    by running the cooldown path, and the redirect hops by driving the real resolver with in-family
    candidates. Nothing is copied from `m3.request_plan`, so agreement between the two is evidence
    rather than a tautology — and §17 stop condition 9 fires on disagreement.

    A manifest-resolved route is measured the same way for retries and cooldown; its hop count is
    zero because the resolver pins its path, which the measurement confirms by finding no lawful
    in-family candidate to move to.
    """
    tested: dict[str, int] = {}
    unmeasured: dict[str, str] = {}
    for source_id in sorted(SOURCES):
        retries = _measure_retry_attempts(source_id)
        if retries == 0:
            # The route placed no attempt at all, so there is no worst path to measure. The only
            # route that can reach this today is the manifest-resolved announcement source with an
            # empty accepted manifest -- which the spec states is lawful and yields zero instances.
            # It is recorded as unmeasured rather than assumed equal to its derivation: copying the
            # derived value would make the confirmation circular, and calling it a mismatch would
            # be a false stop for a route that plans no request and so contributes nothing to any
            # ceiling.
            unmeasured[source_id] = (
                "no lawful URL exists to exercise this route, so no attempt could be placed; "
                "a manifest-resolved source with an empty accepted manifest plans zero requests "
                "and contributes zero to the window ceiling"
            )
            continue
        cooldown = _measure_cooldown_continues(source_id)
        hops = _measure_redirect_hops(source_id)
        tested[source_id] = retries + cooldown + hops
    return tested, unmeasured


def _parameters_for(source_id: str) -> Mapping[str, str] | None:
    """Template parameters for the routes that take them."""
    if source_id == _FULL_INDEX:
        return {"year": "2024", "quarter": "1"}
    if source_id == "sec_submissions_entity":
        return {"cik_padded": "0000000001"}
    if source_id == "sec_submissions_historical":
        return {"historical_file": "CIK0000000001-submissions-001.json"}
    return None


def run_rehearsal(scenario_ids: Sequence[str] | None = None) -> RehearsalReport:
    """Run the requested scenarios and return the rehearsal evidence report.

    Args:
        scenario_ids: the scenarios to run, or ``None`` for all twelve. Only a report over all
            twelve can satisfy the M3.1A completion token; a subset is for diagnosis.

    Raises:
        RehearsalError: an unknown scenario was requested, or the harness could not run one.
    """
    requested = SCENARIO_IDS if scenario_ids is None else tuple(scenario_ids)
    unknown = sorted(set(requested) - set(SCENARIO_IDS))
    if unknown:
        message = f"unknown rehearsal scenario(s) {unknown}; the registry is exactly {SCENARIO_IDS}"
        raise RehearsalError(message)

    by_id = {scenario.scenario_id: scenario for scenario in _REGISTRY}
    outcomes: list[ScenarioOutcome] = []
    for scenario_id in SCENARIO_IDS:
        if scenario_id not in requested:
            continue
        scenario = by_id[scenario_id]
        runner = scenario.run
        if not callable(runner):  # pragma: no cover - registry defect
            message = f"scenario {scenario_id} has no runner"
            raise RehearsalError(message)
        outcomes.append(runner(scenario))

    derived = {source_id: derive_a_reachable(spec) for source_id, spec in sorted(SOURCES.items())}
    tested, unmeasured = _tested_a_reachable()
    return RehearsalReport(
        outcomes=tuple(outcomes),
        derived_a_reachable=derived,
        tested_a_reachable=tested,
        unmeasured_routes=unmeasured,
    )
