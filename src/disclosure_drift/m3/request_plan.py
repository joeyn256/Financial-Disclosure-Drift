"""Milestone 3.1 request plan and budget (`Milestones/milestone_03_master_plan.md` §§15-16,
Decision 028 §10, `Docs/m3/templates/request_budget.md`).

The request plan is the deterministic, **zero-request** artifact M3.1B produces for the M3.2A
bootstrap window and the owner approves at Gate F. It states, route by route, how many unique
logical requests the window intends to place, how many physical attempts it could make in the worst
case, how many new raw objects it could store, the rate-limiter spacing floor, and the exact hard
ceiling above which acquisition must stop. It constructs no transport, resolves no host, and places
no request.

Two properties make it safe to approve against:

**Determinism.** The plan is a pure function of explicit inputs — the coverage window, the calendar
year and evidence-manifest entry count, the set of catalog instances already satisfied, and the
request rate. Nothing consults the clock, the network, or anything not passed in. Identical inputs
reproduce byte-identical canonical bytes and the same content hash, which is what lets two dry runs
be compared for exact agreement (master plan §17 stop condition 2).

**`A_reachable` is derived, never asserted.** The master plan (§16) is explicit that the maximum
physical attempts per route must be derived from the implemented response-policy state machine, and
"never assumed to be the sum of the retry, redirect, and cooldown bounds — those mechanisms interact
inside one loop." :func:`derive_a_reachable` composes the *real* policy constants
(`MAX_TRANSIENT_RETRIES`, `MAX_REDIRECT_DEPTH`) with each route's *real* URL family, so a change to
either moves the derived value; a hardcoded integer could not. The derivation and its justification
are in :func:`derive_a_reachable`. It is **independently confirmed** by driving the real state
machine in rehearsal scenarios A2/A4/A6; a disagreement between the derived and tested bound is a
phase stop condition (master plan §17 item 9), which is exactly why the two are computed by
different mechanisms.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Final

from disclosure_drift.errors import DisclosureDriftError
from disclosure_drift.sec import urls
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.sec.response_policy import MAX_TRANSIENT_RETRIES
from disclosure_drift.sec.source_registry import SOURCES, SourceSpec
from disclosure_drift.sec.urls import MAX_REDIRECT_DEPTH

__all__ = [
    "M3_2A_BOOTSTRAP_ROUTES",
    "M3_2B_DEPENDENT_ROUTES",
    "MAX_COOLDOWN_CONTINUES",
    "REQUEST_PLAN_SCHEMA_VERSION",
    "RequestPlan",
    "RequestPlanInputError",
    "RoutePlan",
    "build_m3_2a_request_plan",
    "build_m3_2b_dependent_plan",
    "canonical_plan_bytes",
    "derive_a_reachable",
    "derive_redirect_reachability",
    "render_budget",
    "request_plan_from_document",
]

#: The plan schema this module implements. A change to the plan's shape or meaning is a version
#: increment governed by a decision, so this is a constant, not a parameter.
REQUEST_PLAN_SCHEMA_VERSION: Final = "m3-request-plan/1.0"

#: The seven bootstrap routes of the M3.2A window, in the master plan §15 order. The two dependent
#: routes (`sec_submissions_entity`, `sec_submissions_historical`) belong to the M3.2B window, which
#: is planned separately after M3.2A freezes its objects, and are deliberately excluded here.
M3_2A_BOOTSTRAP_ROUTES: Final[tuple[str, ...]] = (
    "sec_bulk_submissions",
    "sec_company_tickers_exchange",
    "sec_company_tickers",
    "sec_sic_code_list",
    "sec_edgar_filing_calendar",
    "sec_edgar_calendar_announcement",
    "sec_full_index_company",
)

#: The two dependent route families of the M3.2B window (master plan §15; accepted contract §6).
#: They are deliberately excluded from :data:`M3_2A_BOOTSTRAP_ROUTES` above and are planned only
#: after M3.2A freezes its objects, by :func:`build_m3_2b_dependent_plan`. Declared here, beside the
#: bootstrap tuple, so window membership has **one** definition that the planner and the acquisition
#: driver both read rather than two that can drift apart.
M3_2B_DEPENDENT_ROUTES: Final[tuple[str, ...]] = (
    "sec_submissions_entity",
    "sec_submissions_historical",
)

#: The maximum number of extra physical attempts one cooldown can add to a single retrieval. The
#: response-policy loop permits exactly one controlled post-cooldown request and treats a second
#: cooldown as terminal (`sec/http_client.py`), so a cooldown contributes at most one continue.
MAX_COOLDOWN_CONTINUES: Final = 1


class RequestPlanInputError(DisclosureDriftError):
    """Raised when a request-plan input cannot describe a coherent, zero-request plan.

    Fail-closed: an input that cannot be planned deterministically is refused rather than guessed
    at, because a guessed count would enter a budget the owner is asked to approve.
    """


def _url_family(source_id: str) -> urls._UrlFamilyPolicy:  # noqa: SLF001 - single source of truth
    """The route's registered URL family.

    Read directly from `sec/urls`'s policy table, which is the one authority on which URLs a route
    admits and therefore on how far it can redirect. `sec/urls` is outside this contract's
    authorized paths, so the table cannot be re-exported through a public accessor; reading it
    here keeps a single source of truth rather than duplicating the family definitions.
    """
    return urls._SOURCE_URL_POLICIES[source_id]  # noqa: SLF001 - see docstring


# --------------------------------------------------------------------------- #
# A_reachable — derived from the implemented state machine, never asserted
# --------------------------------------------------------------------------- #
def derive_redirect_reachability(spec: SourceSpec) -> int:
    """Return the maximum redirect hops the route's URL family can actually admit.

    A hop survives only if it validates against the route's URL family and is a *new* in-family URL
    (`sec/urls.resolve_redirect` refuses an out-of-family target, a same-path change on an
    identity-bound or manifest-resolved source, a loop back to a visited URL, and a chain deeper
    than ``MAX_REDIRECT_DEPTH``). So reachability is a property of the family, not a constant:

    - a **manifest-resolved** or **identity-bound** route pins the path, so the only in-family
      redirect target repeats the current URL and is refused as a loop → **0** hops;
    - a route whose family is a single exact path admits exactly one in-family URL → **0** hops;
    - a family of *k* exact paths admits ``k`` URLs, so at most ``k - 1`` new hops before a loop;
    - a **pattern** family admits unboundedly many in-family URLs, so it reaches the hard
      ``MAX_REDIRECT_DEPTH`` cap.

    Every result is clamped to ``MAX_REDIRECT_DEPTH``, which the resolver enforces regardless.
    """
    family = _url_family(spec.source_id)
    if spec.manifest_resolved or spec.is_entity_specific:
        # Path pinned: an identity-bound source (Decision-registered entity document) or a
        # manifest-resolved source may only redirect within the same path, so no new URL exists.
        reachable = 0
    elif family.path_pattern is not None:
        reachable = MAX_REDIRECT_DEPTH
    else:
        reachable = max(0, len(family.exact_paths) - 1)
    return min(MAX_REDIRECT_DEPTH, reachable)


def derive_a_reachable(spec: SourceSpec) -> int:
    """Return the maximum reachable physical attempts for one route.

    Derived from the implemented response-policy loop, **not** assumed additive. The loop caps three
    independent budgets on a single retrieval:

    - **retries**: the ordinal starts at 1 and the loop goes terminal when it reaches
      ``MAX_TRANSIENT_RETRIES`` *before* sending, so retries add at most
      ``MAX_TRANSIENT_RETRIES - 1`` continues;
    - **cooldown**: exactly one controlled post-cooldown request is permitted and a second cooldown
      is terminal, so a cooldown adds at most :data:`MAX_COOLDOWN_CONTINUES` continue;
    - **redirects**: at most :func:`derive_redirect_reachability` hops, each an additional attempt,
      bounded independently of the retry and cooldown budgets.

    The three budgets do interact — after a cooldown every further retry is refused — but the worst
    *realizable* path still reaches the independent sum, because the retries can all precede the
    single cooldown and redirect hops consume neither the retry nor the cooldown budget. The
    interaction can therefore only lower a given path's count, never raise it above this bound. That
    is the composition argument the master plan §16 demands in place of a naive additive assumption,
    and rehearsal A2/A4/A6 confirms the bound by driving the real machine to its worst path.
    """
    initial_attempt = 1
    retry_continues = MAX_TRANSIENT_RETRIES - 1
    return (
        initial_attempt
        + retry_continues
        + MAX_COOLDOWN_CONTINUES
        + derive_redirect_reachability(spec)
    )


# --------------------------------------------------------------------------- #
# Plan data model
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class RoutePlan:
    """One route's line in the M3.2A request plan."""

    source_id: str
    host: str
    planned_unique_logical_requests: int
    a_reachable: int
    basis: str

    @property
    def maximum_physical_attempts(self) -> int:
        """The worst-case attempts for this route: ``U × A_reachable``."""
        return self.planned_unique_logical_requests * self.a_reachable

    @property
    def maximum_new_raw_objects(self) -> int:
        """Each planned logical request can create at most one new terminal object."""
        return self.planned_unique_logical_requests

    def as_record(self) -> dict[str, object]:
        """Deterministic mapping for the plan hash and the budget render."""
        return {
            "source_id": self.source_id,
            "host": self.host,
            "planned_unique_logical_requests": self.planned_unique_logical_requests,
            "a_reachable": self.a_reachable,
            "maximum_physical_attempts": self.maximum_physical_attempts,
            "maximum_new_raw_objects": self.maximum_new_raw_objects,
            "basis": self.basis,
        }


@dataclass(frozen=True, slots=True)
class RequestPlan:
    """The deterministic M3.2A request plan and its derived budget."""

    acquisition_window: str
    coverage_start: date
    coverage_end: date
    as_of_date: date
    include_open_quarter: bool
    calendar_year: int
    calendar_evidence_entry_count: int
    requests_per_second: float
    required_index_keys: tuple[str, ...]
    expected_cache_hits: int
    routes: tuple[RoutePlan, ...]

    @property
    def planned_unique_logical_requests(self) -> int:
        """Total unique logical requests across the window's routes."""
        return sum(route.planned_unique_logical_requests for route in self.routes)

    @property
    def maximum_physical_attempts(self) -> int:
        """``Σ U(route) × A_reachable(route)`` — never a single asserted multiplier."""
        return sum(route.maximum_physical_attempts for route in self.routes)

    @property
    def maximum_new_raw_objects(self) -> int:
        """Upper bound on new terminal objects, equal to planned unique logical requests."""
        return self.planned_unique_logical_requests

    @property
    def hard_request_ceiling(self) -> int:
        """The exact stop-before ceiling for this window. No contingency, no padding."""
        return self.maximum_physical_attempts

    @property
    def rate_limiter_spacing_floor_seconds(self) -> float:
        """A minimum spacing floor, not a maximum or a prediction."""
        return max(0, self.maximum_physical_attempts - 1) / self.requests_per_second

    def as_payload(self) -> dict[str, object]:
        """The canonical, hashable representation of the whole plan."""
        return {
            "request_plan_schema_version": REQUEST_PLAN_SCHEMA_VERSION,
            "acquisition_window": self.acquisition_window,
            "inputs": {
                "coverage_start": self.coverage_start.isoformat(),
                "coverage_end": self.coverage_end.isoformat(),
                "as_of_date": self.as_of_date.isoformat(),
                "include_open_quarter": self.include_open_quarter,
                "calendar_year": self.calendar_year,
                "calendar_evidence_entry_count": self.calendar_evidence_entry_count,
                "requests_per_second": self.requests_per_second,
            },
            "required_index_keys": list(self.required_index_keys),
            "expected_cache_hits": self.expected_cache_hits,
            "routes": [route.as_record() for route in self.routes],
            "totals": {
                "planned_unique_logical_requests": self.planned_unique_logical_requests,
                "maximum_physical_attempts": self.maximum_physical_attempts,
                "maximum_new_raw_objects": self.maximum_new_raw_objects,
                "hard_request_ceiling": self.hard_request_ceiling,
                "rate_limiter_spacing_floor_seconds": self.rate_limiter_spacing_floor_seconds,
            },
        }

    @property
    def request_plan_sha256(self) -> str:
        """The content hash over the canonical plan bytes."""
        return hashlib.sha256(canonical_plan_bytes(self)).hexdigest()

    @property
    def request_plan_id(self) -> str:
        """A content-derived identifier, so two identical plans collide by identity."""
        return f"m3-2a-request-plan-{self.request_plan_sha256}"


def canonical_plan_bytes(plan: RequestPlan) -> bytes:
    """Serialize a plan in the project's canonical JSON form.

    UTF-8 with no byte-order mark, LF only, keys sorted by code point at every level, compact
    separators, non-finite numbers refused, and one trailing newline — the same discipline the
    execution receipt uses, so a plan hash is reproducible on any machine.
    """
    rendered = json.dumps(
        plan.as_payload(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return f"{rendered}\n".encode()


# --------------------------------------------------------------------------- #
# Deterministic plan construction
# --------------------------------------------------------------------------- #
_SINGLETON_ROUTES: Final[tuple[str, ...]] = (
    "sec_bulk_submissions",
    "sec_company_tickers_exchange",
    "sec_company_tickers",
    "sec_sic_code_list",
    "sec_edgar_filing_calendar",
)


def _host_of(source_id: str) -> str:
    """The single canonical host used to display a route, from its URL family."""
    hosts = sorted(_url_family(source_id).hosts)
    return hosts[0] if len(hosts) == 1 else "/".join(hosts)


def build_m3_2a_request_plan(
    *,
    coverage_start: date,
    coverage_end: date,
    as_of_date: date,
    include_open_quarter: bool,
    calendar_year: int,
    calendar_evidence_entry_count: int,
    already_satisfied_index_keys: frozenset[str],
    requests_per_second: float,
) -> RequestPlan:
    """Build the deterministic M3.2A request plan from explicit inputs.

    Args:
        coverage_start, coverage_end, as_of_date, include_open_quarter: the explicit coverage
            window; passed straight to the accepted quarterly index planner.
        calendar_year: the explicit year whose EDGAR filing calendar is retrieved (one instance).
        calendar_evidence_entry_count: the number of approved calendar-announcement manifest
            entries; each is one logical request, and an empty manifest lawfully plans zero.
        already_satisfied_index_keys: quarterly index instances already satisfied in the catalog.
            They are excluded before planning and reported as cache hits, never subtracted twice.
        requests_per_second: the configured aggregate rate, for the spacing floor.

    Raises:
        RequestPlanInputError: an input cannot describe a coherent zero-request plan.
    """
    if calendar_evidence_entry_count < 0:
        message = (
            f"calendar_evidence_entry_count {calendar_evidence_entry_count} is negative; a "
            f"manifest has zero or more approved entries"
        )
        raise RequestPlanInputError(message)
    if requests_per_second <= 0:
        message = f"requests_per_second {requests_per_second} must be positive"
        raise RequestPlanInputError(message)
    if not coverage_start <= calendar_year_bounds(calendar_year)[0] or not (
        calendar_year_bounds(calendar_year)[1] >= coverage_start
        and calendar_year_bounds(calendar_year)[0] <= coverage_end
    ):
        message = (
            f"calendar_year {calendar_year} lies outside the coverage window "
            f"{coverage_start.isoformat()}..{coverage_end.isoformat()}; the calendar year must "
            f"intersect the coverage the plan is built for"
        )
        raise RequestPlanInputError(message)

    # The coverage window's own validation (coverage_end >= coverage_start, as_of within it, and the
    # executable policy version) is enforced by CoverageWindow; a ValueError there surfaces to the
    # caller unchanged, because those are the same coherence checks stated once.
    window = CoverageWindow(
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        as_of_date=as_of_date,
        include_open_quarter=include_open_quarter,
    )
    planned = plan_index_instances(window)
    required_index_keys = tuple(planned.required_keys)

    satisfied_in_plan = frozenset(required_index_keys) & already_satisfied_index_keys
    unsatisfied_index_count = len(required_index_keys) - len(satisfied_in_plan)

    routes = tuple(
        _build_route(
            source_id,
            calendar_evidence_entry_count=calendar_evidence_entry_count,
            unsatisfied_index_count=unsatisfied_index_count,
        )
        for source_id in M3_2A_BOOTSTRAP_ROUTES
    )

    return RequestPlan(
        acquisition_window="M3.2A",
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        as_of_date=as_of_date,
        include_open_quarter=include_open_quarter,
        calendar_year=calendar_year,
        calendar_evidence_entry_count=calendar_evidence_entry_count,
        requests_per_second=requests_per_second,
        required_index_keys=required_index_keys,
        expected_cache_hits=len(satisfied_in_plan),
        routes=routes,
    )


def build_m3_2b_dependent_plan(
    *,
    coverage_start: date,
    coverage_end: date,
    as_of_date: date,
    include_open_quarter: bool,
    calendar_year: int,
    calendar_evidence_entry_count: int,
    entity_instance_count: int,
    historical_instance_count: int,
    requests_per_second: float,
) -> RequestPlan:
    """Build the deterministic M3.2B dependent plan from explicit reconciled counts.

    The dependent window plans exactly the two routes :data:`M3_2B_DEPENDENT_ROUTES` names, and
    **never derives its own instance counts**. Both counts arrive from the caller, which obtains
    them by reconciling frozen M3.2A objects against the explicit reconciliation set (Decision 045
    §13); this function refuses to invent, estimate, or round either one. That is what keeps the
    eventual exact M3.2B request count a fact about reviewed evidence rather than about this code.

    The coverage inputs, calendar year, and calendar-evidence entry count are carried through from
    the same explicit reconciliation set. They are *provenance*, not planning inputs: no M3.2B route
    is a quarterly index or a calendar announcement, so neither the coverage window nor the calendar
    count changes a single planned request here. They are recorded because
    :meth:`RequestPlan.as_payload` is the frozen ``m3-request-plan/1.0`` shape shared with M3.2A,
    and a plan document that omitted them would not be a document of that schema. ``expected_cache
    _hits`` is ``0`` and ``required_index_keys`` is empty for the same reason: this window plans no
    quarterly index instance, so it excludes none and requires none.

    Nothing here reads the clock, the network, the catalog, or the filesystem, and the schema
    version is unchanged, so the accepted M3.2A plan hash is untouched by this addition.

    Raises:
        RequestPlanInputError: an input cannot describe a coherent zero-request plan.
    """
    if entity_instance_count < 0 or historical_instance_count < 0:
        message = (
            f"dependent instance counts must not be negative; received "
            f"entity={entity_instance_count}, historical={historical_instance_count}"
        )
        raise RequestPlanInputError(message)
    if calendar_evidence_entry_count < 0:
        message = (
            f"calendar_evidence_entry_count {calendar_evidence_entry_count} is negative; a "
            f"manifest has zero or more approved entries"
        )
        raise RequestPlanInputError(message)
    if requests_per_second <= 0:
        message = f"requests_per_second {requests_per_second} must be positive"
        raise RequestPlanInputError(message)
    if coverage_end < coverage_start:
        message = (
            f"coverage_end {coverage_end.isoformat()} precedes coverage_start "
            f"{coverage_start.isoformat()}"
        )
        raise RequestPlanInputError(message)

    planned_counts = {
        "sec_submissions_entity": entity_instance_count,
        "sec_submissions_historical": historical_instance_count,
    }
    bases = {
        "sec_submissions_entity": "one per reconciled dependent entity instance",
        "sec_submissions_historical": "one per reconciled historical submissions file",
    }
    routes = tuple(
        RoutePlan(
            source_id=source_id,
            host=_host_of(source_id),
            planned_unique_logical_requests=planned_counts[source_id],
            a_reachable=derive_a_reachable(SOURCES[source_id]),
            basis=bases[source_id],
        )
        for source_id in M3_2B_DEPENDENT_ROUTES
    )

    return RequestPlan(
        acquisition_window="M3.2B",
        coverage_start=coverage_start,
        coverage_end=coverage_end,
        as_of_date=as_of_date,
        include_open_quarter=include_open_quarter,
        calendar_year=calendar_year,
        calendar_evidence_entry_count=calendar_evidence_entry_count,
        requests_per_second=requests_per_second,
        required_index_keys=(),
        expected_cache_hits=0,
        routes=routes,
    )


def request_plan_from_document(payload: bytes) -> RequestPlan:
    """Reconstruct the plan a stored plan document *is*, rather than rebuilding it from inputs.

    A stored plan is the artifact the owner approved and the receipt chain recorded a hash of. It is
    therefore the authority on its own ceiling and its own hash, and a consumer that needs the plan
    an interrupted run was executing must read it, not re-derive it. Rebuilding from the recorded
    ``inputs`` section alone cannot reproduce the plan: the exclusion of already-satisfied instances
    happens *before* the plan is formed, and the satisfied set is not an input the document carries.
    A rebuild therefore silently plans the cached instances again, producing a larger ceiling and a
    different hash — which would make every plan that had a cache hit fail its own "plan hash
    unchanged" check.

    Every :class:`RequestPlan` and :class:`RoutePlan` field is present in
    :meth:`RequestPlan.as_payload`, so the reconstruction is exact rather than approximate, and it
    is *proved* exact here: the reconstructed plan is re-serialized and compared against the
    supplied bytes. A document that does not round-trip is refused rather than repaired, because
    anything less would let a hand-edited or non-canonical document assert a hash it does not hash
    to. Passing that comparison means ``request_plan_sha256`` equals the SHA-256 of the stored bytes
    by construction, so nothing about the governed identity is recomputed or re-derived.

    Args:
        payload: the exact stored plan bytes, as written by ``m3 plan-requests``.

    Raises:
        RequestPlanInputError: the bytes are not a canonical document of this schema version.
    """
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"the stored request plan is not readable UTF-8 JSON: {exc}"
        raise RequestPlanInputError(message) from exc
    if not isinstance(document, dict):
        message = "the stored request plan is not a JSON object"
        raise RequestPlanInputError(message)

    version = document.get("request_plan_schema_version")
    if version != REQUEST_PLAN_SCHEMA_VERSION:
        message = (
            f"the stored request plan declares schema {version!r}, not "
            f"{REQUEST_PLAN_SCHEMA_VERSION!r}; a plan of another schema is not this plan"
        )
        raise RequestPlanInputError(message)

    try:
        inputs = document["inputs"]
        routes = document["routes"]
        required_keys = document["required_index_keys"]
        if not isinstance(inputs, dict) or not isinstance(routes, list):
            raise TypeError  # noqa: TRY301 - joined with the KeyError path below
        plan = RequestPlan(
            acquisition_window=str(document["acquisition_window"]),
            coverage_start=date.fromisoformat(str(inputs["coverage_start"])),
            coverage_end=date.fromisoformat(str(inputs["coverage_end"])),
            as_of_date=date.fromisoformat(str(inputs["as_of_date"])),
            include_open_quarter=bool(inputs["include_open_quarter"]),
            calendar_year=int(inputs["calendar_year"]),
            calendar_evidence_entry_count=int(inputs["calendar_evidence_entry_count"]),
            requests_per_second=float(inputs["requests_per_second"]),
            required_index_keys=tuple(str(key) for key in required_keys),
            expected_cache_hits=int(document["expected_cache_hits"]),
            routes=tuple(
                RoutePlan(
                    source_id=str(route["source_id"]),
                    host=str(route["host"]),
                    planned_unique_logical_requests=int(route["planned_unique_logical_requests"]),
                    a_reachable=int(route["a_reachable"]),
                    basis=str(route["basis"]),
                )
                for route in routes
                if isinstance(route, dict)
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        message = (
            f"the stored request plan does not carry the fields "
            f"{REQUEST_PLAN_SCHEMA_VERSION} defines: {exc}"
        )
        raise RequestPlanInputError(message) from exc

    if canonical_plan_bytes(plan) != payload:
        message = (
            "re-serializing the reconstructed plan does not reproduce the stored bytes, so the "
            "stored document is not a canonical plan of this schema and its recorded hash cannot "
            "be trusted; a correction is a new plan, never a repaired read"
        )
        raise RequestPlanInputError(message)
    return plan


def calendar_year_bounds(calendar_year: int) -> tuple[date, date]:
    """The first and last day of a calendar year, for the coverage-intersection check."""
    return date(calendar_year, 1, 1), date(calendar_year, 12, 31)


def _build_route(
    source_id: str,
    *,
    calendar_evidence_entry_count: int,
    unsatisfied_index_count: int,
) -> RoutePlan:
    """Construct one route line, computing its planned logical request count."""
    spec = SOURCES[source_id]
    if source_id in _SINGLETON_ROUTES:
        planned = 1
        basis = "one instance"
    elif source_id == "sec_edgar_calendar_announcement":
        planned = calendar_evidence_entry_count
        basis = "one per approved calendar-evidence manifest entry"
    elif source_id == "sec_full_index_company":
        planned = unsatisfied_index_count
        basis = "one per required closed quarter not already satisfied"
    else:  # pragma: no cover - the route set is closed and fully enumerated above
        message = f"no planned-count rule for route {source_id!r}"
        raise RequestPlanInputError(message)
    return RoutePlan(
        source_id=source_id,
        host=_host_of(source_id),
        planned_unique_logical_requests=planned,
        a_reachable=derive_a_reachable(spec),
        basis=basis,
    )


# --------------------------------------------------------------------------- #
# Budget rendering
# --------------------------------------------------------------------------- #
def render_budget(plan: RequestPlan) -> Mapping[str, object]:
    """Render the machine-derived budget quantities for the `show-budget` command.

    Only the quantities the plan can derive from explicit inputs are rendered; the operator
    estimates in the budget template (`Docs/m3/templates/request_budget.md` §4) are not invented
    here, because a guessed count would enter an owner approval. The command that displays this
    approves neither the ceiling nor the request count.
    """
    return {
        "acquisition_window": plan.acquisition_window,
        "request_plan_schema_version": REQUEST_PLAN_SCHEMA_VERSION,
        "request_plan_sha256": plan.request_plan_sha256,
        "planned_unique_logical_requests": plan.planned_unique_logical_requests,
        "maximum_physical_attempts": plan.maximum_physical_attempts,
        "maximum_new_raw_objects": plan.maximum_new_raw_objects,
        "hard_request_ceiling": plan.hard_request_ceiling,
        "rate_limiter_spacing_floor_seconds": plan.rate_limiter_spacing_floor_seconds,
        "expected_cache_hits": plan.expected_cache_hits,
        "per_route": [route.as_record() for route in plan.routes],
    }
