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
    "MAX_COOLDOWN_CONTINUES",
    "REQUEST_PLAN_SCHEMA_VERSION",
    "RequestPlan",
    "RequestPlanInputError",
    "RoutePlan",
    "build_m3_2a_request_plan",
    "canonical_plan_bytes",
    "derive_a_reachable",
    "derive_redirect_reachability",
    "render_budget",
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
