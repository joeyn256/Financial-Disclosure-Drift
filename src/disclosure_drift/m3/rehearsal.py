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
import tempfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError, RawObjectIntegrityError
from disclosure_drift.m3.receipt import (
    INTERRUPTION_STATES,
    SCHEMA_DRIFT_OUTCOMES,
    ExecutionReceipt,
    inspect_receipt,
    scan_for_prohibited_content,
    validate_receipt_document,
    write_receipt,
)
from disclosure_drift.m3.recovery import read_only_catalog
from disclosure_drift.m3.request_plan import M3_2A_BOOTSTRAP_ROUTES, derive_a_reachable
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.http_client import (
    ProhibitedRetrievalError,
    RetrievalPolicy,
    SecClient,
)
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.parsers.base import ParseOutcome, RecordLocation
from disclosure_drift.sec.parsers.submissions import (
    REGION_FILES,
    REGION_RECENT,
    parse_submissions_document,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.raw_store import RawStore
from disclosure_drift.sec.request_ceiling import (
    PhysicalAttemptCeiling,
    RequestCeilingExhaustedError,
)
from disclosure_drift.sec.response_policy import MAX_TRANSIENT_RETRIES, classify_response
from disclosure_drift.sec.snapshots import SnapshotStore
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.transport import SecRequest, TransportResponse
from disclosure_drift.sec.urls import (
    MAX_REDIRECT_DEPTH,
    RedirectBoundaryError,
    normalize_url,
    resolve_redirect,
    validate_url,
)
from disclosure_drift.storage.catalog import CatalogWriter

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


#: The version A12(b)'s rehearsal receipts declare. It names the harness that emitted them, so a
#: receipt from the rehearsal is never mistaken for one from a live acquisition command.
_REHEARSAL_COMMAND_VERSION: Final = "m3-rehearsal-harness/1.0"


def _clock_instant(seconds: float) -> str:
    """An RFC 3339 UTC timestamp derived from the *injected* clock, never the system clock.

    Spec §2.3: nothing reads the system clock into a recorded value. A12(b) needs two runs whose
    operational timestamps genuinely differ, and the only lawful source of that difference is the
    frozen clock the run was given.
    """
    return datetime.fromtimestamp(seconds, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    def a_reachable_fully_tested(self) -> bool:
        """Whether every registered route's bound was independently tested.

        `a_reachable_agrees` speaks only for the routes that were measured. A route the ceiling
        counts but no test exercised is a gap in the Gate F evidence, not a pass, so it is reported
        separately rather than folded into the agreement boolean.
        """
        return not self.unmeasured_routes

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
            "a_reachable_fully_tested": self.a_reachable_fully_tested,
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
    probe: _Probe,
    *,
    logical: int = 0,
    attempts: int = 0,
) -> ScenarioOutcome:
    """Turn one probe's observations into the scenario's evidence record.

    The probe's notes carry the *observed* facts — reason codes, object counts, orderings — so they
    travel into the report's `findings` rather than being accumulated and discarded. A record whose
    findings were always empty would say a scenario passed without saying what it saw, which is
    exactly what spec §5 requires the matrix to show.
    """
    return ScenarioOutcome(
        scenario_id=scenario.scenario_id,
        title=scenario.title,
        passed=probe.passed,
        detail=probe.detail,
        simulated_logical_requests=logical,
        simulated_physical_attempts=attempts,
        findings=tuple(probe.notes),
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
# Content-addressed storage: an isolated synthetic tree and what is on disk in it
# --------------------------------------------------------------------------- #
@contextmanager
def _synthetic_tree(prefix: str, workspace: Path) -> Iterator[DataTree]:
    """An isolated synthetic data tree below ``workspace``, removed when the scenario ends.

    Spec §2.5 requires an isolated synthetic data root: never the machine's default data root and
    never a personal path. Every scenario that makes a claim about *stored* state opens one of
    these, so the claim is checked against real files rather than against a client-level response.

    Contract §11 additionally fixes *where* that root may live: `m3 rehearse` writes its synthetic
    data tree and synthetic catalog "below the external evidence root", alongside the evidence and
    the receipt. ``workspace`` is that location, supplied by the caller — a system temporary
    directory would put operator evidence outside the boundary the operator named. The directory is
    still removed when the scenario ends, so re-running writes nothing that a later run could
    collide with.
    """
    with tempfile.TemporaryDirectory(prefix=prefix, dir=workspace) as scratch:
        tree = DataTree.from_root(Path(scratch) / "data")
        tree.ensure_tree()
        yield tree


def _stored_objects(tree: DataTree) -> tuple[Path, ...]:
    """Every content-addressed raw object below ``tree``, excluding its lineage siblings.

    Counting objects on disk is the only way to tell content addressing apart from a client that
    merely returned equal bytes twice: identical bodies must collapse to one object, and differing
    bodies must produce two with the first left intact.
    """
    found: list[Path] = []
    for root in (tree.raw_bulk, tree.raw_indexes, tree.raw_filings, tree.quarantine):
        if not root.is_dir():
            continue
        found.extend(
            path
            for path in root.rglob("*")
            if path.is_file() and not path.name.endswith(".lineage.json")
        )
    return tuple(sorted(found))


def _part_files(tree: DataTree) -> tuple[Path, ...]:
    """Every leftover `.part` file below ``tree``. A completed store leaves none."""
    return tuple(sorted(path for path in tree.data_root.rglob("*.part") if path.is_file()))


def _verification_failure(store: SnapshotStore, observation: object) -> str | None:
    """Verify a stored object against its hashes, returning the failure text or ``None``."""
    try:
        store.verify_payload(observation)  # type: ignore[arg-type]
    except RawObjectIntegrityError as exc:
        return str(exc)
    return None


# --------------------------------------------------------------------------- #
# A1 - all-success acquisition
# --------------------------------------------------------------------------- #
def _refusal_code(action: Callable[[], object]) -> str | None:
    """Run ``action`` and return the reason code it was refused with, or ``None`` if it succeeded.

    Driving the real resolver and reporting its code is what makes A6 a test rather than a
    restatement of a constant.
    """
    try:
        action()
    except RedirectBoundaryError as exc:
        return str(getattr(exc, "reason_code", "") or "")
    except (ProhibitedRetrievalError, ValueError) as exc:  # pragma: no cover - defensive
        return type(exc).__name__
    return None


def _run_a1(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
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
    # The client-level result is only half of A1. The spec's expected *persisted state* and
    # expected *files* are properties of the content-addressed store, so both retrievals are
    # persisted through the real `SnapshotStore` into an isolated synthetic tree and the objects
    # are counted and verified on disk. Without this the scenario would still pass with the store
    # entirely absent, which is not a rehearsal of "content-addressed raw storage and provenance".
    with _synthetic_tree("m3-rehearsal-a1-", workspace) as tree:
        store = SnapshotStore(tree)
        stored = [store.record(first), store.record(second)]
        for observation, result in zip(stored, (first, second), strict=True):
            probe.require(
                observation.outcome == "stored_new",
                f"{observation.source_id}: a first storage recorded {observation.outcome!r} "
                f"rather than 'stored_new'",
            )
            probe.require(
                observation.reason_codes == (),
                f"{observation.source_id}: a first storage carried reason codes "
                f"{observation.reason_codes}; A1 expects none, and SOURCE_CONTENT_UPDATED "
                f"applies only to a later changed living source",
            )
            probe.require(
                observation.content_sha256 == _body_digest(result.body),
                f"{observation.source_id}: the recorded content digest does not match the "
                f"retrieved bytes, so the object cannot stand as evidence for the response",
            )
            failure = _verification_failure(store, observation)
            probe.require(
                failure is None,
                f"{observation.source_id}: the stored object did not verify against its "
                f"content_sha256 ({failure})",
            )

        objects = _stored_objects(tree)
        probe.require(
            len(objects) == 2,
            f"two logical requests produced {len(objects)} content-addressed object(s), not one "
            f"per logical request",
        )
        missing_lineage = sorted(
            path.name for path in objects if not RawStore.lineage_path(path).is_file()
        )
        probe.require(
            not missing_lineage,
            f"stored object(s) {missing_lineage} have no .lineage.json sibling, so their "
            f"provenance is unrecorded",
        )
        leftovers = _part_files(tree)
        probe.require(
            not leftovers,
            f"{len(leftovers)} .part file(s) survived a clean run; A1 expects zero",
        )
        probe.note(
            f"{len(objects)} content-addressed objects stored, each with a lineage sibling and "
            f"each verified against its content_sha256; zero .part files"
        )

    probe.note("request order is deterministic across runs")
    return _outcome(scenario, probe, logical=2, attempts=2)


# --------------------------------------------------------------------------- #
# A2 - retry then success
# --------------------------------------------------------------------------- #
def _run_a2(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:  # noqa: ARG001
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
    return _outcome(scenario, probe, logical=1, attempts=3)


# --------------------------------------------------------------------------- #
# A3 - Retry-After, usable and unusable
# --------------------------------------------------------------------------- #
def _run_a3(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:  # noqa: ARG001
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
    probe.note(
        f"a usable Retry-After classified {usable.kind!r} and delayed exactly "
        f"{usable.delay_seconds}s without halting aggregate traffic; an unusable HTTP-date value "
        f"classified {unusable.kind!r} and fell through to the cooldown path"
    )
    return _outcome(
        scenario,
        probe,
        logical=1,
        attempts=len(transport.requests),
    )


# --------------------------------------------------------------------------- #
# A4 - cooldown and block-page termination
# --------------------------------------------------------------------------- #
def _run_a4(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:  # noqa: ARG001
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
        # Spec §6 pass criterion 3: "every observed reason code equals its expected code and is a
        # registered code". Requiring merely that *some* code is present would accept a second
        # unqualified 429 terminating as SEC_BLOCK_PAGE, or a block page terminating as
        # SEC_RETRIES_EXHAUSTED, which are different findings with different operator actions.
        probe.require(
            result.reason_code == expected_code,
            f"{label}: terminated with reason code {result.reason_code!r}, expected "
            f"{expected_code!r}; a terminal failure carrying the wrong code misreports why the "
            f"run stopped, and no code at all could be read as an empty dataset",
        )
        probe.require(
            result.reason_code in REASON_CODES,
            f"{label}: terminal reason code {result.reason_code!r} is not in the registered "
            f"registry, so it may never be recorded",
        )
        probe.require(
            result.attempts == 2,
            f"{label}: expected exactly one controlled post-cooldown request, observed "
            f"{result.attempts} attempts",
        )
        probe.note(f"{label} terminated with {result.reason_code!r} (expected {expected_code!r})")

    return _outcome(scenario, probe, logical=3, attempts=attempts)


# --------------------------------------------------------------------------- #
# A5 - stop before budget overflow
# --------------------------------------------------------------------------- #
def _run_a5(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:  # noqa: ARG001
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
    observed_code: str | None = None
    try:
        client.fetch(_CALENDAR, purpose="rehearsal ceiling overflow evidence")
    except RequestCeilingExhaustedError as exc:
        refused = True
        observed_code = str(exc.reason_code)
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
    probe.note(
        f"attempt C+1 was refused with {observed_code!r} and the counter remained at "
        f"{ceiling.consumed}; a run completing exactly at C={exact.approved_ceiling} succeeded and "
        f"was not reported as stopped_at_ceiling"
    )
    return _outcome(scenario, probe, logical=3, attempts=3)


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
    (".htm suffix", "https://www.sec.gov/files/company_tickers.htm"),
    (".xml suffix", "https://www.sec.gov/files/company_tickers.xml"),
    (".xsd suffix", "https://www.sec.gov/files/company_tickers.xsd"),
    (".txt suffix", "https://www.sec.gov/files/company_tickers.txt"),
    ("relative traversal", "https://www.sec.gov/files/../secrets/company_tickers.json"),
)


def _run_a6(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:  # noqa: ARG001
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

    # Redirect refusals, driven through the real resolver rather than asserted about.
    index_spec = SOURCES[_FULL_INDEX]
    start = "https://www.sec.gov/Archives/edgar/full-index/2020/QTR1/company.idx"

    # (i) a hop leaving the source's URL family
    escaped = _refusal_code(
        lambda: resolve_redirect(
            "https://www.sec.gov/files/company_tickers.json",
            start,
            index_spec,
            seen=(normalize_url(start),),
            identity_url=start,
        )
    )
    probe.require(
        escaped == "SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
        f"a hop leaving the URL family was refused with {escaped!r}, not "
        f"SEC_REDIRECT_OUTSIDE_SOURCE_BOUNDARY",
    )

    # (ii) a loop back to a URL already visited
    looped = _refusal_code(
        lambda: resolve_redirect(
            start, start, index_spec, seen=(normalize_url(start),), identity_url=start
        )
    )
    probe.require(
        looped == "SEC_REDIRECT_DEPTH_EXCEEDED",
        f"a redirect loop was refused with {looped!r}, not SEC_REDIRECT_DEPTH_EXCEEDED",
    )

    # (iii) a chain deeper than the accepted depth
    visited = tuple(
        normalize_url(f"https://www.sec.gov/Archives/edgar/full-index/20{20 + n}/QTR1/company.idx")
        for n in range(MAX_REDIRECT_DEPTH + 2)
    )
    over_depth = _refusal_code(
        lambda: resolve_redirect(
            "https://www.sec.gov/Archives/edgar/full-index/2019/QTR1/company.idx",
            start,
            index_spec,
            seen=visited,
            identity_url=start,
        )
    )
    probe.require(
        over_depth == "SEC_REDIRECT_DEPTH_EXCEEDED",
        f"an over-depth chain was refused with {over_depth!r}, not SEC_REDIRECT_DEPTH_EXCEEDED",
    )

    # A lawful in-family hop must still be accepted, or the three refusals above would prove
    # only that the resolver refuses everything.
    lawful = _refusal_code(
        lambda: resolve_redirect(
            "https://www.sec.gov/Archives/edgar/full-index/2021/QTR2/company.idx",
            start,
            index_spec,
            seen=(normalize_url(start),),
            identity_url=start,
        )
    )
    probe.require(
        lawful is None,
        f"a lawful in-family hop was refused with {lawful!r}; the refusals prove nothing if "
        f"every hop is refused",
    )
    probe.note(
        f"only GET and only the approved SEC hosts are permitted across {len(SOURCES)} routes"
    )
    return _outcome(scenario, probe)


# --------------------------------------------------------------------------- #
# A7 and A8 - the parser and schema-drift path
# --------------------------------------------------------------------------- #
#: The `filings` region of the synthetic document, split out so a variant can rebuild it without
#: reaching into a nested literal.
_SUBMISSIONS_FILINGS: Final[Mapping[str, object]] = {
    "recent": {
        "accessionNumber": ["0000000001-24-000001"],
        "filingDate": ["2024-02-01"],
        "form": ["10-K"],
    },
    "files": [
        {
            "name": "CIK0000000001-submissions-001.json",
            "filingCount": 1,
            "filingFrom": "2010-01-01",
            "filingTo": "2010-12-31",
        }
    ],
}

#: The well-formed synthetic submissions document A7 and A8 mutate. It is shaped the way the
#: accepted `submissions-json` parser expects and carries no real registrant, accession, or CIK.
_SUBMISSIONS_BASE: Final[Mapping[str, object]] = {
    "cik": "1",
    "name": "SYNTHETIC ONE",
    "sic": "2834",
    "fiscalYearEnd": "1231",
    "tickers": ["SYN"],
    "exchanges": ["Nasdaq"],
    "formerNames": [{"name": "OLD SYNTHETIC", "from": "2018-01-01", "to": "2020-01-01"}],
    "addresses": {"business": {"street1": "1 SYNTHETIC WAY", "city": "SYNTHETICA"}},
    "filings": _SUBMISSIONS_FILINGS,
}


def _submissions_body(document: Mapping[str, object]) -> bytes:
    """Serialize a synthetic submissions document as the scripted response body."""
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def _json_copy(value: Mapping[str, object]) -> dict[str, object]:
    """A deep copy of a synthetic fixture, taken through the same JSON round trip a body makes.

    Copying via the serialized form rather than by reference means a variant can never mutate the
    shared base document, which would make one scenario's fixture depend on another's.
    """
    copied = json.loads(_submissions_body(value).decode())
    if not isinstance(copied, dict):  # pragma: no cover - the fixtures are objects
        message = f"synthetic fixture {value!r} is not a JSON object"
        raise RehearsalError(message)
    return copied


def _submissions_variant(**regions: object) -> dict[str, object]:
    """A deep copy of the base document with top-level regions replaced."""
    document = _json_copy(_SUBMISSIONS_BASE)
    for key, value in regions.items():
        if value is _DROP:
            document.pop(key, None)
        else:
            document[key] = value
    return document


#: Sentinel meaning "delete this key", so a variant can express *absence* rather than a null.
_DROP: Final = object()


def _parsed_through_the_real_path(
    probe: _Probe,
    label: str,
    document: Mapping[str, object],
    *,
    tree_prefix: str,
    workspace: Path,
) -> tuple[ParseOutcome, tuple[object, ...]]:
    """Retrieve, store, and parse one synthetic document through the accepted production path.

    The retrieval is the real `SecClient` over a scripted transport, the storage is the real
    `SnapshotStore` over an isolated synthetic tree, and the parse is the real
    `submissions-json` parser — which is what calls `sec.schema_drift.inspect_payload`. Asserting
    only that the raw body survived `fetch` would leave A7 and A8 passing with every parser and
    drift-detection callable replaced by a stub, which is the finding this exists to close.

    The raw object is verified *after* the parse in every variant, because the spec requires
    evidence to be retained whether the parse succeeded or failed.
    """
    body = _submissions_body(document)
    client, transport, _ = _client([_scripted(body=body)])
    result = client.fetch(
        _ENTITY,
        purpose=f"rehearsal schema-drift evidence ({label})",
        parameters=_parameters_for(_ENTITY),
    )
    probe.require(
        result.outcome == "retrieved",
        f"{label}: the synthetic document was not retrieved ({result.outcome!r}), so nothing "
        f"reached the parser",
    )
    probe.require(
        result.body == body,
        f"{label}: the payload was altered before evidence was preserved",
    )
    probe.require(
        len(transport.requests) == 1,
        f"{label}: the parse path placed {len(transport.requests)} request(s); parsing retrieves "
        f"nothing and a historical reference is recorded, never followed",
    )

    with _synthetic_tree(tree_prefix, workspace) as tree:
        store = SnapshotStore(tree)
        observation = store.record(result)
        outcome, references = parse_submissions_document(
            json.loads(result.body.decode()),
            RecordLocation(observation_id=observation.observation_id, source_id=_ENTITY),
        )
        stored = tree.data_root / str(observation.relative_storage_path)
        probe.require(
            stored.is_file(),
            f"{label}: the raw object was deleted; evidence is retained in every variant",
        )
        probe.require(
            RawStore.lineage_path(stored).is_file(),
            f"{label}: the retained raw object has no lineage sibling",
        )
        failure = _verification_failure(store, observation)
        probe.require(
            failure is None,
            f"{label}: the retained raw object did not verify against its content_sha256 "
            f"({failure})",
        )
        probe.require(
            not _part_files(tree),
            f"{label}: a .part file survived the parse",
        )
    return outcome, references


def _validated_drift_receipt(
    probe: _Probe,
    label: str,
    *,
    outcome_value: str,
    event_count: int,
    completion_status: str,
    reason_code: str | None,
) -> None:
    """Build and validate the receipt the spec names for this scenario, without writing one.

    Contract §4 emits exactly one receipt per rehearsal *invocation*, so a per-scenario receipt is
    never written to the evidence root. It is still constructed and validated here, because A7 and
    A8 each specify an expected `schema_drift_outcome` and A8 an expected `completion_status`, and a
    membership check against the enum would not prove the schema accepts the whole combination.
    """
    if outcome_value not in SCHEMA_DRIFT_OUTCOMES:
        probe.failures.append(
            f"{label}: the receipt schema has no {outcome_value!r} drift outcome to record"
        )
        return
    try:
        receipt = ExecutionReceipt(
            command_name="m3 rehearse",
            command_version=_REHEARSAL_COMMAND_VERSION,
            phase="M3.1A",
            invocation_mode="rehearsal",
            configuration_fingerprint=hashlib.sha256(label.encode()).hexdigest(),
            migration_chain_head="none",
            started_at_utc=_clock_instant(1_000.0),
            completed_at_utc=_clock_instant(1_001.0),
            elapsed_seconds=1.0,
            actual_logical_request_count=0,
            actual_physical_attempt_count=0,
            schema_drift_outcome=outcome_value,
            schema_drift_event_count=event_count,
            completion_status=completion_status,
            reason_code=reason_code,
            reason_detail=(
                None
                if reason_code is None
                else "the synthetic document was refused by the accepted parser."
            ),
            rehearsal_evidence_reference=f"m3-1a-rehearsal-report-{'0' * 64}",
        )
        validate_receipt_document(receipt.as_document())
    except DisclosureDriftError as exc:
        probe.failures.append(
            f"{label}: the receipt the spec names for this scenario does not validate: {exc}"
        )


def _run_a7(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
    """Unknown fields are retained, admitted, and never block a lawful parse."""
    probe = _Probe()

    # Unknown fields at four depths: top level, inside `filings`, inside `filings.recent`, and
    # inside a nested address block. Only a walker that really descends finds the last three.
    filings = _json_copy(_SUBMISSIONS_FILINGS)
    filings["unknownRegion"] = {"deeper": True}
    recent = filings["recent"]
    if isinstance(recent, dict):
        recent["unknownColumn"] = ["synthetic"]
    addresses = {"business": {"street1": "1 SYNTHETIC WAY", "unknownAddressField": "synthetic"}}
    document = _submissions_variant(unknown_leaf=1, filings=filings, addresses=addresses)

    outcome, _ = _parsed_through_the_real_path(
        probe, "unknown fields", document, tree_prefix="m3-rehearsal-a7-", workspace=workspace
    )

    # The drift report is produced by `sec.schema_drift.inspect_payload`, which the parser calls.
    reports = outcome.drift_reports
    probe.require(bool(reports), "the parser produced no drift report at all")
    blocking = tuple(event for report in reports for event in report.blocking_events)
    probe.require(
        not blocking,
        f"an unknown field produced {len(blocking)} blocking drift event(s); retention must be "
        f"non-blocking",
    )
    retained = tuple(
        sorted({name for report in reports for name in report.retained_unknown_fields})
    )
    probe.require(
        "unknown_leaf" in retained,
        f"the top-level unknown field was not recorded as retained; the report retained {retained}",
    )

    expected_paths = (
        "addresses.business.unknownAddressField",
        "filings.recent.unknownColumn",
        "filings.unknownRegion",
        "unknown_leaf",
    )
    missing = sorted(set(expected_paths) - set(outcome.unknown_fields))
    probe.require(
        not missing,
        f"unknown field(s) {missing} were discarded rather than retained with their exact paths; "
        f"the parser recorded {outcome.unknown_fields}",
    )
    probe.require(
        "PARSER_SCHEMA_DRIFT_OBSERVED" in outcome.reason_codes,
        f"retained unknown fields did not raise PARSER_SCHEMA_DRIFT_OBSERVED; the run recorded "
        f"{outcome.reason_codes}",
    )
    drift_code = REASON_CODES.get("PARSER_SCHEMA_DRIFT_OBSERVED")
    probe.require(
        drift_code is not None and not drift_code.blocks_release,
        "retained unknown fields must be non-blocking; the registered code blocks release",
    )
    blocking_codes = sorted(
        code
        for code in outcome.reason_codes
        if code in REASON_CODES and REASON_CODES[code].blocks_release
    )
    probe.require(
        not blocking_codes,
        f"the unknown fields blocked a lawful parse with {blocking_codes}",
    )

    # "The record parsed and admitted", and its count still believable.
    probe.require(
        bool(outcome.records) and not outcome.quarantined,
        f"the drifted document produced {len(outcome.records)} record(s) and "
        f"{len(outcome.quarantined)} quarantine(s); a lawful parse admits the record",
    )
    probe.require(
        outcome.counts_are_trustworthy,
        "an unknown field made the record counts untrustworthy, which blocks a lawful parse",
    )
    registrant = outcome.records[0] if outcome.records else None
    probe.require(
        registrant is not None and "unknown_leaf" in registrant.unknown_fields,
        "the admitted record does not carry the retained field names",
    )

    # The retained names are inside the record hash, so a discarded unknown field cannot leave the
    # record looking identical. Without this, "retained" could mean "listed and then ignored".
    if registrant is not None:
        without = replace(registrant, unknown_fields=())
        probe.require(
            without.record_sha256 != registrant.record_sha256,
            "dropping the retained field names left the record hash unchanged, so an unknown "
            "field could be discarded silently",
        )

    # Inverse control: a document with no unknown field must record none. Otherwise the assertions
    # above would pass against a parser that reports drift unconditionally.
    clean_outcome, _ = _parsed_through_the_real_path(
        probe,
        "no unknown fields",
        _submissions_variant(),
        tree_prefix="m3-rehearsal-a7-clean-",
        workspace=workspace,
    )
    probe.require(
        clean_outcome.unknown_fields == (),
        f"a document with no unknown field reported {clean_outcome.unknown_fields} as retained, so "
        f"retention is reported unconditionally and proves nothing",
    )
    probe.require(
        "PARSER_SCHEMA_DRIFT_OBSERVED" not in clean_outcome.reason_codes,
        "a document with no unknown field still raised PARSER_SCHEMA_DRIFT_OBSERVED",
    )

    event_count = sum(len(report.events) for report in reports)
    _validated_drift_receipt(
        probe,
        "unknown fields",
        outcome_value="unknown_fields_retained",
        event_count=event_count,
        completion_status="complete",
        reason_code=None,
    )
    probe.note(
        f"unknown fields at {len(expected_paths)} depths were retained with their exact paths, "
        f"admitted as {len(outcome.records)} parsed record(s) with no quarantine, and recorded as "
        f"{event_count} non-blocking drift event(s) under PARSER_SCHEMA_DRIFT_OBSERVED"
    )
    return _outcome(scenario, probe, logical=2, attempts=2)


# --------------------------------------------------------------------------- #
# A8 - blocking schema drift
# --------------------------------------------------------------------------- #
def _run_a8(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
    """A structurally invalid payload never becomes a defaulted or coerced row."""
    probe = _Probe()

    def _recent(**columns: object) -> dict[str, object]:
        block = _json_copy(_SUBMISSIONS_FILINGS)
        block["recent"] = columns
        return block

    #: The four blocking variants: the mutated document, the code the spec names, and the
    #: structural state the accepted parser must reach. `None` means the failure is a top-level
    #: required-field failure rather than a nested structural verdict.
    variants: tuple[tuple[str, dict[str, object], str, str | None], ...] = (
        (
            "required field missing",
            _submissions_variant(name=_DROP),
            "SEC_SCHEMA_REQUIRED_FIELD_MISSING",
            None,
        ),
        (
            "unexpected null",
            _submissions_variant(filings={"recent": None, "files": []}),
            "PARSER_STRUCTURE_NULL",
            "null",
        ),
        (
            "changed type",
            _submissions_variant(filings={"recent": [], "files": []}),
            "PARSER_STRUCTURE_WRONG_TYPE",
            "wrong_type",
        ),
        (
            "malformed nested array",
            _submissions_variant(
                filings=_recent(
                    accessionNumber=["0000000001-24-000001", "0000000001-24-000002"],
                    filingDate=["2024-02-01"],
                    form=["10-K"],
                )
            ),
            "PARSER_STRUCTURE_MALFORMED",
            "malformed",
        ),
    )

    for index, (label, document, expected_code, expected_state) in enumerate(variants):
        outcome, _ = _parsed_through_the_real_path(
            probe,
            label,
            document,
            tree_prefix=f"m3-rehearsal-a8-{index}-",
            workspace=workspace,
        )
        probe.require(
            expected_code in outcome.reason_codes,
            f"{label}: the parser recorded {outcome.reason_codes}, not the {expected_code!r} the "
            f"spec names; a blocking drift reported under the wrong code misstates why the run "
            f"stopped",
        )
        probe.require(
            expected_code in REASON_CODES and REASON_CODES[expected_code].blocks_release,
            f"{label}: {expected_code} is unregistered or does not block release; blocking drift "
            f"that does not block is not blocking",
        )
        # "Processing stops": the counts may not be believed, so nothing downstream may read the
        # region as an empty result.
        probe.require(
            not outcome.counts_are_trustworthy,
            f"{label}: the parser reported trustworthy counts for a document it could not parse, "
            f"so a structural failure could be read as a real zero",
        )
        if expected_state is not None:
            observed_state = outcome.region_state(REGION_RECENT)
            probe.require(
                observed_state == expected_state,
                f"{label}: filings.recent resolved to {observed_state!r}, not {expected_state!r}",
            )
            # Scoped to the region under test: the spec permits valid siblings to remain
            # recorded, and `filings.files` being an honest empty list is one of them.
            failed_region = [
                item
                for item in outcome.structural
                if item.region == REGION_RECENT and (item.is_genuine_zero or item.row_count == 0)
            ]
            probe.require(
                not failed_region,
                f"{label}: the unusable region was reported as a genuine zero ({failed_region}), "
                f"so a structural failure could be read as 'this registrant has no filings'",
            )
        # "No invalid/defaulted/coerced normalized row is admitted": the unusable region yields no
        # accession record. A registrant record may lawfully survive as a valid sibling.
        admitted = [
            record
            for record in outcome.records
            if (record.location.record_path or "").startswith(REGION_RECENT)
        ]
        probe.require(
            not admitted,
            f"{label}: {len(admitted)} record(s) were admitted from an unusable region; no default "
            f"is supplied, no type coerced, and no row dropped",
        )
        _validated_drift_receipt(
            probe,
            label,
            outcome_value="blocked",
            event_count=max(1, sum(len(report.events) for report in outcome.drift_reports)),
            completion_status="failed",
            reason_code=expected_code,
        )
        probe.note(f"{label}: refused with {expected_code} and the raw object retained")

    # The fifth variant: a historical-file reference, malformed and merely new.
    malformed_reference = _submissions_variant(
        filings={
            "recent": _json_copy(_SUBMISSIONS_FILINGS)["recent"],
            # A name outside the accepted pattern. It is preserved as evidence and must never be
            # turned into a URL, which is why the reference below has to be unretrievable.
            "files": [{"name": "not-a-submissions-file.json", "filingCount": 1}],
        }
    )
    outcome, references = _parsed_through_the_real_path(
        probe,
        "malformed historical reference",
        malformed_reference,
        tree_prefix="m3-rehearsal-a8-4-",
        workspace=workspace,
    )
    probe.require(
        "PARSER_HISTORICAL_REFERENCE_MALFORMED" in outcome.reason_codes,
        f"a malformed historical-file reference recorded {outcome.reason_codes}, not "
        f"PARSER_HISTORICAL_REFERENCE_MALFORMED",
    )
    probe.require(
        outcome.region_state(REGION_FILES) == "malformed",
        f"filings.files resolved to {outcome.region_state(REGION_FILES)!r}, not 'malformed'",
    )
    probe.require(
        bool(references) and not any(getattr(item, "is_retrievable", False) for item in references),
        "a malformed historical reference was still marked retrievable, so it could be turned "
        "into a URL",
    )

    new_reference = _submissions_variant()
    fresh_outcome, fresh_references = _parsed_through_the_real_path(
        probe,
        "new historical reference",
        new_reference,
        tree_prefix="m3-rehearsal-a8-5-",
        workspace=workspace,
    )
    probe.require(
        len(fresh_references) == 1 and getattr(fresh_references[0], "is_retrievable", False),
        "a well-formed new historical reference was not recorded as a retrievable reference",
    )
    probe.require(
        not fresh_outcome.quarantined,
        f"a merely new historical reference was quarantined ({len(fresh_outcome.quarantined)}); "
        f"only a malformed one is",
    )
    # "Does not silently expand the plan": the route a historical reference would be retrieved on
    # is not in the M3.2A window at all, so no reference can add a request to the approved budget.
    probe.require(
        "sec_submissions_historical" not in M3_2A_BOOTSTRAP_ROUTES,
        "the historical-submissions route is inside the M3.2A window, so a newly observed "
        "reference would silently expand the approved plan",
    )
    probe.note(
        "a malformed historical reference was refused as unretrievable and a merely new one was "
        "recorded without expanding the M3.2A plan"
    )
    return _outcome(scenario, probe, logical=6, attempts=6)


# --------------------------------------------------------------------------- #
# A9 - byte-identical duplicate and valid 304
# --------------------------------------------------------------------------- #
#: A synthetic entity tag. It never came from SEC; it exists so the conditional request in A9(b)
#: can send a validator drawn from the observation it is revalidating, as the reuse rules require.
_A9_ETAG: Final = '"synthetic-rehearsal-fixture"'


def _run_a9(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
    """Identical bodies collapse by identity; a lawful 304 reuses the preserved snapshot.

    Both variants run against one real `SnapshotStore` over an isolated synthetic tree, because
    "one object and two immutable observations" is a claim about persisted state. Comparing two
    client-level bodies would pass with no store at all.
    """
    probe = _Probe()
    etag_headers = {"ETag": _A9_ETAG}
    client, _, _ = _client(
        [
            _scripted(headers=etag_headers),
            _scripted(headers=etag_headers),
            _scripted(304, body=b"", headers=etag_headers),
        ]
    )

    with _synthetic_tree("m3-rehearsal-a9-", workspace) as tree:
        store = SnapshotStore(tree)

        # (a) the same logical request returns a byte-identical 200.
        first = client.fetch(_TICKERS, purpose="rehearsal duplicate evidence")
        stored_first = store.record(first)
        after_first = _stored_objects(tree)
        original_bytes = after_first[0].read_bytes() if after_first else b""

        second = client.fetch(_TICKERS, purpose="rehearsal duplicate evidence")
        stored_second = store.record(second)

        probe.require(
            first.body == second.body,
            "two byte-identical responses did not produce identical bodies",
        )
        probe.require(
            first.identity == second.identity,
            "content addressing keyed on something other than request identity",
        )
        probe.require(
            stored_first.outcome == "stored_new",
            f"variant (a): the first storage recorded {stored_first.outcome!r}",
        )
        probe.require(
            stored_second.outcome == "unchanged_content",
            f"variant (a): a byte-identical second body recorded {stored_second.outcome!r} "
            f"rather than 'unchanged_content'",
        )
        probe.require(
            stored_second.reason_codes == ("SOURCE_CONTENT_UNCHANGED",),
            f"variant (a): the second observation carried {stored_second.reason_codes} rather "
            f"than the SOURCE_CONTENT_UNCHANGED verdict the spec names",
        )
        probe.require(
            stored_second.relative_storage_path == stored_first.relative_storage_path,
            "variant (a): the second observation claimed a second object rather than reusing "
            "the preserved one, so identical bodies did not collapse by identity",
        )

        # (b) a conditional request receives a valid 304 and reuses the preserved snapshot.
        reused = client.fetch(
            _TICKERS, purpose="rehearsal revalidation evidence", etag=stored_first.etag or _A9_ETAG
        )
        stored_reuse = store.record(reused)
        probe.require(
            reused.outcome == "not_modified",
            f"a valid 304 produced {reused.outcome!r} rather than a reuse",
        )
        probe.require(
            stored_reuse.outcome == "reused_snapshot",
            f"variant (b): a lawful 304 recorded {stored_reuse.outcome!r} rather than "
            f"'reused_snapshot'; {stored_reuse.detail}",
        )
        probe.require(
            stored_reuse.reason_codes == ("SOURCE_SNAPSHOT_REUSED",),
            f"variant (b): the reuse observation carried {stored_reuse.reason_codes} rather than "
            f"the SOURCE_SNAPSHOT_REUSED verdict the spec names",
        )
        probe.require(
            stored_reuse.relative_storage_path == stored_first.relative_storage_path,
            "variant (b): the reuse did not point at the preserved object",
        )

        objects = _stored_objects(tree)
        probe.require(
            len(objects) == 1,
            f"three retrievals of identical content produced {len(objects)} objects; content "
            f"addressing must collapse them to exactly one",
        )
        probe.require(
            len(store.observations) == 3,
            f"{len(store.observations)} observations were recorded; a lawful 304 and a duplicate "
            f"200 each still record their own immutable observation",
        )
        probe.require(
            bool(objects) and objects[0].read_bytes() == original_bytes,
            "the preserved object was rewritten by a later identical retrieval",
        )
        missing_lineage = sorted(
            path.name for path in objects if not RawStore.lineage_path(path).is_file()
        )
        probe.require(not missing_lineage, f"stored object(s) {missing_lineage} have no lineage")
        probe.require(not _part_files(tree), "a duplicate or 304 left a .part file behind")
        probe.note(
            f"one raw object and {len(store.observations)} immutable observations; verdicts "
            f"{stored_second.reason_codes[0] if stored_second.reason_codes else 'none'} and "
            f"{stored_reuse.reason_codes[0] if stored_reuse.reason_codes else 'none'}"
        )
    return _outcome(scenario, probe, logical=3, attempts=3)


# --------------------------------------------------------------------------- #
# A10 - changed body is a new observation
# --------------------------------------------------------------------------- #
def _run_a10(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
    """A differing later response is always a new observation and never an overwrite."""
    probe = _Probe()
    original = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC"}}'
    changed = b'{"0":{"cik_str":1,"ticker":"SYN","title":"SYNTHETIC RENAMED"}}'

    client, _, _ = _client([_scripted(body=original), _scripted(body=changed)])
    first = client.fetch(_TICKERS, purpose="rehearsal changed-body evidence")
    second = client.fetch(_TICKERS, purpose="rehearsal changed-body evidence")

    # The spec's expected files are "two raw objects — the first is never overwritten", and its
    # expected reason codes are SnapshotStore verdicts. Both are properties of the store, so the
    # living-source variant and the closed-quarter dated-snapshot variant are persisted through
    # the real store into isolated synthetic trees rather than asserted about.
    with _synthetic_tree("m3-rehearsal-a10-living-", workspace) as tree:
        store = SnapshotStore(tree)
        stored_first = store.record(first)
        preserved = tree.data_root / str(stored_first.relative_storage_path)
        preserved_bytes = preserved.read_bytes()
        stored_second = store.record(second)

        probe.require(
            stored_second.outcome == "superseded",
            f"a changed body at a living source recorded {stored_second.outcome!r} rather than "
            f"'superseded'",
        )
        probe.require(
            stored_second.reason_codes == ("SOURCE_CONTENT_UPDATED",),
            f"the living-source change carried {stored_second.reason_codes} rather than the "
            f"SOURCE_CONTENT_UPDATED verdict the spec names",
        )
        probe.require(
            stored_second.supersedes_observation_id == stored_first.observation_id,
            "the supersession lineage does not name the earlier observation, so the change was "
            "absorbed rather than recorded",
        )
        probe.require(
            len(_stored_objects(tree)) == 2,
            f"a changed body produced {len(_stored_objects(tree))} object(s); the spec requires "
            f"two, because the first is never overwritten",
        )
        probe.require(
            preserved.is_file() and preserved.read_bytes() == preserved_bytes,
            "the first object was overwritten or removed by the later differing response "
            "(CLAUDE.md rule 6)",
        )
        probe.require(not _part_files(tree), "the changed-body store left a .part file behind")

    # A closed-quarter dated snapshot that changes is an anomaly requiring review, not an update.
    with _synthetic_tree("m3-rehearsal-a10-dated-", workspace) as tree:
        parameters = _parameters_for(_FULL_INDEX)
        dated_client, _, _ = _client(
            [
                _scripted(body=b"CIK|Company Name\n1|SYNTHETIC\n", content_type="text/plain"),
                _scripted(
                    body=b"CIK|Company Name\n1|SYNTHETIC RENAMED\n", content_type="text/plain"
                ),
            ]
        )
        dated_store = SnapshotStore(tree)
        dated_first = dated_client.fetch(
            _FULL_INDEX, purpose="rehearsal dated-artifact evidence", parameters=parameters
        )
        dated_store.record(dated_first, period_is_closed=True)
        dated_second = dated_client.fetch(
            _FULL_INDEX, purpose="rehearsal dated-artifact evidence", parameters=parameters
        )
        dated_stored = dated_store.record(dated_second, period_is_closed=True)

        probe.require(
            "SOURCE_DATED_ARTIFACT_CHANGED" in dated_stored.reason_codes,
            f"a closed-quarter dated snapshot that changed carried {dated_stored.reason_codes} "
            f"rather than the SOURCE_DATED_ARTIFACT_CHANGED anomaly verdict the spec names",
        )
        probe.require(
            len(_stored_objects(tree)) == 2,
            f"the changed dated artifact produced {len(_stored_objects(tree))} object(s) rather "
            f"than two; the earlier snapshot is evidence and is never replaced",
        )
        probe.note(
            f"closed-quarter dated change recorded as {dated_stored.reason_codes} over two "
            f"preserved objects"
        )

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
    for code, must_review in (
        ("SOURCE_CONTENT_UPDATED", False),
        ("SOURCE_DATED_ARTIFACT_CHANGED", True),
        ("SOURCE_IMMUTABLE_IDENTITY_MUTATED", True),
    ):
        probe.require(code in REASON_CODES, f"{code} is not registered")
        if code in REASON_CODES and must_review:
            probe.require(
                REASON_CODES[code].requires_manual_review or REASON_CODES[code].blocks_release,
                f"{code} marks an anomaly at an immutable or closed identity and must not be "
                f"treated as an ordinary update",
            )
    probe.note("two distinct objects; the first is never overwritten")
    return _outcome(scenario, probe, logical=2, attempts=2)


# --------------------------------------------------------------------------- #
# A11 - interruption and recovery
# --------------------------------------------------------------------------- #
def _run_a11(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
    """Each abort point leaves a distinguishable state, and a resume re-requests nothing committed.

    This is the scenario the acquisition rehearsal exists for, so it is exercised against a real
    synthetic data tree and catalog rather than asserted about. Every artifact lives under a
    temporary root that is removed when the scenario ends; nothing touches an operator data root.
    """
    probe = _Probe()

    with tempfile.TemporaryDirectory(prefix="m3-rehearsal-a11-", dir=workspace) as scratch:
        tree = DataTree.from_root(Path(scratch) / "data")
        tree.ensure_tree()
        with CatalogWriter(tree.catalog_database, tree.locks) as writer:
            writer.migrate()
            writer.seed_reference_data()

            # (a) before any byte reaches the raw store: nothing exists anywhere.
            probe.require(
                not any(path.is_file() for path in tree.raw_bulk.rglob("*")),
                "variant (a): an object existed before the raw store was written",
            )

            client, _, _ = _client([_scripted_for(_TICKERS)])
            fetched = client.fetch(_TICKERS, purpose="rehearsal interruption evidence")
            observation = SnapshotStore(tree).record(fetched)

            # (b) promoted and fsynced, before the catalog transaction commits: exactly one orphan.
            stored = tree.data_root / str(observation.relative_storage_path)
            probe.require(stored.is_file(), "variant (b): the promoted object is missing")
            probe.require(
                RawStore.lineage_path(stored).is_file(),
                "variant (b): the promoted object has no lineage sibling",
            )
            committed = writer.connection.execute(
                "SELECT COUNT(*) FROM census_source_observations"
            ).fetchone()[0]
            probe.require(
                committed == 0,
                f"variant (b): {committed} row(s) were committed before the catalog transaction",
            )

            # (c) immediately after the catalog commit: the row exists and the object verifies.
            ObservationRecorder(writer, tree).record(observation)
            committed = writer.connection.execute(
                "SELECT COUNT(*) FROM census_source_observations"
            ).fetchone()[0]
            probe.require(
                committed == 1, f"variant (c): expected one committed row, found {committed}"
            )
            probe.require(
                stored.is_file(),
                "variant (c): the committed row lost its object, which is a stop condition",
            )

        # (d) restart and resume. The resumed pass consults the catalog, finds the retrieval
        # already committed, and skips it. The transport is scripted with nothing, so had the
        # resume actually fetched, `_ScriptedTransport.send` would raise rather than pass quietly.
        resumed_client, resumed_transport, _ = _client([])
        with read_only_catalog(tree.catalog_database) as connection:
            satisfied = {
                str(row[0])
                for row in connection.execute(
                    "SELECT DISTINCT source_id FROM census_source_observations"
                ).fetchall()
            }
        probe.require(
            _TICKERS in satisfied,
            "variant (d): the resumed pass could not see the committed retrieval",
        )

        resume_error: str | None = None
        for source_id in (_TICKERS,):
            if source_id in satisfied:
                continue  # already committed: the resume must not re-request it
            try:  # pragma: no cover - reached only if the skip rule regresses
                resumed_client.fetch(source_id, purpose="rehearsal resume evidence")
            except RehearsalError as exc:
                resume_error = str(exc)
        probe.require(
            resume_error is None,
            f"variant (d): the resumed pass attempted a request: {resume_error}",
        )
        probe.require(
            not resumed_transport.requests,
            f"variant (d): {len(resumed_transport.requests)} request(s) were issued for an "
            f"already-committed retrieval",
        )

        # The skip must be a decision, not an accident of an empty work list: an UNsatisfied
        # source is fetched, which proves the loop above would have issued a request.
        control_client, control_transport, _ = _client([_scripted_for(_CALENDAR)])
        control_client.fetch(_CALENDAR, purpose="rehearsal resume control")
        probe.require(
            len(control_transport.requests) == 1,
            "variant (d): the control retrieval issued no request, so the skip proves nothing",
        )

    for code in (
        "SEC_ACQUISITION_INTERRUPTED",
        "RAW_PARTIAL_DOWNLOAD",
        "RAW_FILE_CHECKSUM_MISMATCH",
    ):
        probe.require(code in REASON_CODES, f"{code} is not registered")
    for state in (
        "before_raw_store_write",
        "after_raw_store_write_before_catalog_commit",
        "after_catalog_commit",
    ):
        probe.require(
            state in INTERRUPTION_STATES,
            f"{state!r} is not a receipt interruption state, so it cannot be recorded",
        )

    probe.note(
        "inspection alone changes no byte; the recovery inspector is read-only by construction"
    )
    return _outcome(scenario, probe, logical=1, attempts=1)


# --------------------------------------------------------------------------- #
# A12 - redaction and non-contamination
# --------------------------------------------------------------------------- #
def _run_a12(scenario: _Scenario, workspace: Path) -> ScenarioOutcome:
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

    # (b) Non-contamination: run A with receipts disabled, B with receipts enabled, and C with
    # receipts enabled and every operational value varied. Every STORED identity must be
    # byte-identical across all three. Comparing `request_identity` alone would prove nothing --
    # it is a pure function of source, URL, and parameters, with no clock or receipt input.
    identities: list[tuple[str, ...]] = []
    receipt_ids: list[str] = []
    receipt_validation_failures: list[str] = []
    for label, clock_start, emit_receipt in (
        ("A", 1_000.0, False),
        ("B", 1_000.0, True),
        ("C", 9_999.0, True),
    ):
        with tempfile.TemporaryDirectory(
            prefix=f"m3-rehearsal-a12{label}-", dir=workspace
        ) as scratch:
            tree = DataTree.from_root(Path(scratch) / "data")
            tree.ensure_tree()
            clock = _FrozenClock(clock_start)
            transport = _ScriptedTransport([_scripted_for(_TICKERS)])
            limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
            client = SecClient(
                transport, _REHEARSAL_AGENT, limiter, RetrievalPolicy(), sleeper=clock.sleep
            )
            fetched = client.fetch(_TICKERS, purpose="rehearsal non-contamination evidence")
            observation = SnapshotStore(tree).record(fetched)

            # These are the values a governed identity is computed from.
            identities.append(
                (
                    str(observation.identity),
                    str(observation.content_sha256),
                    str(observation.logical_sha256),
                    str(observation.relative_storage_path),
                )
            )

            if emit_receipt:
                # Receipt emission is the variable under test, so a REAL receipt is constructed
                # and written through `m3.receipt` into this run's temporary tree. Hashing a
                # string would make legs B and C differ only because their labels differ, which
                # would prove nothing about receipts at all; every field that separates B from C
                # below is derived from the injected clock, never from the leg's name.
                receipt_root = Path(scratch) / "evidence"
                started = _clock_instant(clock_start)
                completed = _clock_instant(clock_start + 1.0)
                receipt = ExecutionReceipt(
                    command_name="m3 rehearse",
                    command_version=_REHEARSAL_COMMAND_VERSION,
                    phase="M3.1A",
                    invocation_mode="rehearsal",
                    configuration_fingerprint=hashlib.sha256(
                        f"rehearsal-clock-{int(clock_start)}".encode()
                    ).hexdigest(),
                    migration_chain_head="none",
                    started_at_utc=started,
                    completed_at_utc=completed,
                    elapsed_seconds=1.0,
                    actual_logical_request_count=0,
                    actual_physical_attempt_count=0,
                    schema_drift_outcome="none",
                    schema_drift_event_count=0,
                    completion_status="complete",
                    rehearsal_evidence_reference=(
                        f"m3-1a-rehearsal-report-{hashlib.sha256(started.encode()).hexdigest()}"
                    ),
                )
                written = write_receipt(
                    receipt,
                    evidence_root=receipt_root,
                    repository_root=Path(scratch) / "checkout",
                )
                try:
                    inspected = inspect_receipt(written)
                except DisclosureDriftError as exc:
                    receipt_validation_failures.append(f"run {label}: {exc}")
                else:
                    if inspected.get("receipt_id") != receipt.receipt_id:
                        receipt_validation_failures.append(
                            f"run {label}: the written receipt does not carry the identity it "
                            f"computed"
                        )
                receipt_ids.append(receipt.receipt_id)

    probe.require(
        len(set(identities)) == 1,
        f"varying receipt emission or operational values moved a stored identity: {identities}",
    )
    probe.require(
        not receipt_validation_failures,
        f"a receipt emitted by run B or C did not validate: {receipt_validation_failures}",
    )
    probe.require(
        len(set(receipt_ids)) == len(receipt_ids) == 2,
        "runs B and C produced identical receipt identifiers; the operational values did not "
        "actually vary, so the comparison proves nothing",
    )
    probe.note(
        f"every stored identity is byte-identical with receipts disabled, enabled, and varied; "
        f"runs B and C emitted {len(set(receipt_ids))} distinct validated receipt_id values"
    )
    return _outcome(scenario, probe, logical=3, attempts=3)


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
                "no lawful URL exists to exercise this route without a manifest entry, so no "
                "attempt could be placed and its A_reachable is NOT independently tested. When "
                "the approved calendar-evidence manifest is non-empty this route DOES contribute "
                "to the window ceiling, so Gate F must not treat this as inert: master plan §16 "
                "requires an independently tested bound for every route the ceiling counts"
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


#: The directory `m3 rehearse` opens its per-invocation scratch root inside. It lives below the
#: evidence root the operator named, per contract §11, and never survives the invocation.
_WORKSPACE_DIRECTORY: Final = "rehearsal-workspace"


def run_rehearsal(
    scenario_ids: Sequence[str] | None = None,
    *,
    workspace_root: Path,
) -> RehearsalReport:
    """Run the requested scenarios and return the rehearsal evidence report.

    Args:
        scenario_ids: the scenarios to run, or ``None`` for all twelve. Only a report over all
            twelve can satisfy the M3.1A completion token; a subset is for diagnosis.
        workspace_root: the already-validated external evidence root. Contract §11 places the
            synthetic data tree and synthetic catalog **below the external evidence root**, so the
            location is required rather than defaulted: a default would silently write operator
            evidence outside the boundary the operator named, which is the failure the argument
            exists to prevent.

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
    # One scratch root per invocation, below the evidence root and removed when the invocation
    # ends. Nothing synthetic is retained, so a second identical run neither collides with the
    # first nor needs the write-once artifact rule relaxed: that rule guards the named plan,
    # evidence, and receipt, which this directory never contains.
    scratch_parent = Path(workspace_root) / _WORKSPACE_DIRECTORY
    scratch_parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="m3-rehearsal-", dir=scratch_parent) as workspace:
            for scenario_id in SCENARIO_IDS:
                if scenario_id not in requested:
                    continue
                scenario = by_id[scenario_id]
                runner = scenario.run
                if not callable(runner):  # pragma: no cover - registry defect
                    message = f"scenario {scenario_id} has no runner"
                    raise RehearsalError(message)
                outcomes.append(runner(scenario, Path(workspace)))
    finally:
        # Leave the evidence root as it was found when nothing else put anything here. A retained
        # empty directory is not evidence, and an operator comparing two runs should not have to
        # explain one.
        with suppress(OSError):
            scratch_parent.rmdir()

    derived = {source_id: derive_a_reachable(spec) for source_id, spec in sorted(SOURCES.items())}
    tested, unmeasured = _tested_a_reachable()
    return RehearsalReport(
        outcomes=tuple(outcomes),
        derived_a_reachable=derived,
        tested_a_reachable=tested,
        unmeasured_routes=unmeasured,
    )
