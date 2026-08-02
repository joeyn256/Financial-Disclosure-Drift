"""Milestone 3.1 request plan and budget (`Milestones/milestone_03_master_plan.md` §§15-16,
Decision 028 §10, `Docs/m3/templates/request_budget.md`).

The request plan is the deterministic, zero-request M3.2A artifact the owner approves at Gate F.
These tests pin the properties that make it safe to approve against:

- **Determinism.** Identical explicit inputs reproduce byte-identical canonical bytes and the same
  content hash; nothing consults the clock, the network, or a live catalog beyond the explicit
  already-satisfied set passed in.
- **`A_reachable` is derived, never asserted.** It is a function of the real response-policy
  constants and each route's real URL family, so a change to either moves the derived value — a
  hardcoded constant could not. The master plan forbids a naive additive assumption; the derivation
  is justified by the state-machine composition and is independently confirmed by rehearsal
  A2/A4/A6 (not here).
- **Budget arithmetic matches Decision 028 §10 exactly**, including that already-satisfied instances
  are excluded before planning and reported as cache hits, never subtracted twice.
- **The hard ceiling equals `Σ U(route) × A_reachable(route)`**, with no contingency.
"""

from __future__ import annotations

import json
from datetime import date

import pytest

from disclosure_drift.m3.request_plan import (
    M3_2A_BOOTSTRAP_ROUTES,
    MAX_COOLDOWN_CONTINUES,
    REQUEST_PLAN_SCHEMA_VERSION,
    RequestPlan,
    RequestPlanInputError,
    build_m3_2a_request_plan,
    canonical_plan_bytes,
    derive_a_reachable,
    derive_redirect_reachability,
    render_budget,
)
from disclosure_drift.sec.response_policy import MAX_TRANSIENT_RETRIES
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.sec.urls import MAX_REDIRECT_DEPTH

# --------------------------------------------------------------------------- #
# Fixed inputs — Decision 013 §1 coverage, one closed quarter after the D028 fix
# --------------------------------------------------------------------------- #
_COVERAGE_START = date(2024, 1, 1)
_COVERAGE_END = date(2024, 6, 30)
_AS_OF = date(2024, 6, 30)


def build(**overrides: object) -> RequestPlan:
    """A minimal valid M3.2A plan input set."""
    params = {
        "coverage_start": _COVERAGE_START,
        "coverage_end": _COVERAGE_END,
        "as_of_date": _AS_OF,
        "include_open_quarter": False,
        "calendar_year": 2024,
        "calendar_evidence_entry_count": 2,
        "already_satisfied_index_keys": frozenset(),
        "requests_per_second": 5.0,
    }
    params.update(overrides)
    return build_m3_2a_request_plan(**params)


# --------------------------------------------------------------------------- #
# Schema version and route set
# --------------------------------------------------------------------------- #
def test_the_schema_version_is_the_one_the_contract_fixes() -> None:
    assert REQUEST_PLAN_SCHEMA_VERSION == "m3-request-plan/1.0"


def test_the_window_covers_exactly_the_seven_bootstrap_routes() -> None:
    assert set(M3_2A_BOOTSTRAP_ROUTES) == {
        "sec_bulk_submissions",
        "sec_company_tickers_exchange",
        "sec_company_tickers",
        "sec_sic_code_list",
        "sec_edgar_filing_calendar",
        "sec_edgar_calendar_announcement",
        "sec_full_index_company",
    }


def test_every_bootstrap_route_is_a_registered_source() -> None:
    for source_id in M3_2A_BOOTSTRAP_ROUTES:
        assert source_id in SOURCES


def test_the_two_dependent_routes_are_not_in_the_m3_2a_window() -> None:
    assert "sec_submissions_entity" not in M3_2A_BOOTSTRAP_ROUTES
    assert "sec_submissions_historical" not in M3_2A_BOOTSTRAP_ROUTES


# --------------------------------------------------------------------------- #
# A_reachable derivation (master plan §16, Decision 028 §10)
# --------------------------------------------------------------------------- #
def test_the_base_attempt_count_tracks_the_real_policy_constants() -> None:
    """1 initial + (MAX_TRANSIENT_RETRIES-1) retry-continues + one cooldown continue."""
    for source_id in ("sec_bulk_submissions", "sec_company_tickers", "sec_sic_code_list"):
        spec = SOURCES[source_id]
        assert derive_redirect_reachability(spec) == 0
        assert derive_a_reachable(spec) == 1 + (MAX_TRANSIENT_RETRIES - 1) + MAX_COOLDOWN_CONTINUES


def test_a_single_exact_path_route_cannot_redirect() -> None:
    for source_id in (
        "sec_bulk_submissions",
        "sec_company_tickers",
        "sec_company_tickers_exchange",
        "sec_sic_code_list",
        "sec_edgar_calendar_announcement",
    ):
        assert derive_redirect_reachability(SOURCES[source_id]) == 0


def test_a_two_exact_path_route_admits_exactly_one_hop() -> None:
    assert derive_redirect_reachability(SOURCES["sec_edgar_filing_calendar"]) == 1
    assert derive_a_reachable(SOURCES["sec_edgar_filing_calendar"]) == 7


def test_a_pattern_route_reaches_the_redirect_depth_cap() -> None:
    assert derive_redirect_reachability(SOURCES["sec_full_index_company"]) == MAX_REDIRECT_DEPTH
    assert derive_a_reachable(SOURCES["sec_full_index_company"]) == 11


def test_an_identity_bound_route_cannot_redirect_despite_a_pattern() -> None:
    for source_id in ("sec_submissions_entity", "sec_submissions_historical"):
        assert derive_redirect_reachability(SOURCES[source_id]) == 0
        assert derive_a_reachable(SOURCES[source_id]) == 6


def test_a_manifest_resolved_route_cannot_redirect() -> None:
    assert derive_redirect_reachability(SOURCES["sec_edgar_calendar_announcement"]) == 0


def test_redirect_reachability_never_exceeds_the_depth_cap() -> None:
    for source_id in M3_2A_BOOTSTRAP_ROUTES:
        assert derive_redirect_reachability(SOURCES[source_id]) <= MAX_REDIRECT_DEPTH


def test_a_reachable_is_never_a_bare_asserted_constant() -> None:
    """It must compose the real constants, so every route equals base + its own reachability."""
    base = 1 + (MAX_TRANSIENT_RETRIES - 1) + MAX_COOLDOWN_CONTINUES
    for source_id in M3_2A_BOOTSTRAP_ROUTES:
        spec = SOURCES[source_id]
        assert derive_a_reachable(spec) == base + derive_redirect_reachability(spec)


# --------------------------------------------------------------------------- #
# Per-route planned counts (master plan §15)
# --------------------------------------------------------------------------- #
def test_each_singleton_route_plans_exactly_one_logical_request() -> None:
    plan = build()
    routes = {route.source_id: route for route in plan.routes}
    for source_id in (
        "sec_bulk_submissions",
        "sec_company_tickers_exchange",
        "sec_company_tickers",
        "sec_sic_code_list",
        "sec_edgar_filing_calendar",
    ):
        assert routes[source_id].planned_unique_logical_requests == 1


def test_the_announcement_route_plans_one_request_per_manifest_entry() -> None:
    plan = build(calendar_evidence_entry_count=3)
    routes = {route.source_id: route for route in plan.routes}
    assert routes["sec_edgar_calendar_announcement"].planned_unique_logical_requests == 3


def test_an_empty_calendar_manifest_lawfully_plans_zero_announcement_requests() -> None:
    plan = build(calendar_evidence_entry_count=0)
    routes = {route.source_id: route for route in plan.routes}
    assert routes["sec_edgar_calendar_announcement"].planned_unique_logical_requests == 0


def test_the_full_index_route_plans_one_request_per_required_closed_quarter() -> None:
    # 2024 Q1 and Q2 both close on or before 2024-06-30.
    plan = build()
    routes = {route.source_id: route for route in plan.routes}
    assert routes["sec_full_index_company"].planned_unique_logical_requests == 2


def test_an_already_satisfied_quarter_is_excluded_and_reported_as_a_cache_hit() -> None:
    plan = build()
    satisfied_key = plan.required_index_keys[0]
    reduced = build(already_satisfied_index_keys=frozenset({satisfied_key}))
    routes = {route.source_id: route for route in reduced.routes}
    assert routes["sec_full_index_company"].planned_unique_logical_requests == 1
    assert reduced.expected_cache_hits == 1


def test_a_cache_hit_is_reported_but_never_subtracted_twice() -> None:
    plan = build()
    satisfied = frozenset(plan.required_index_keys)  # both quarters already satisfied
    reduced = build(already_satisfied_index_keys=satisfied)
    routes = {route.source_id: route for route in reduced.routes}
    assert routes["sec_full_index_company"].planned_unique_logical_requests == 0
    assert reduced.expected_cache_hits == 2
    # Excluded instances leave the plan; they are not also subtracted from the total.
    assert reduced.planned_unique_logical_requests == plan.planned_unique_logical_requests - 2


def test_a_satisfied_key_that_is_not_in_the_plan_is_ignored_not_an_error() -> None:
    plan = build(already_satisfied_index_keys=frozenset({"2019QTR3"}))
    assert plan.expected_cache_hits == 0


# --------------------------------------------------------------------------- #
# Budget arithmetic (Decision 028 §10)
# --------------------------------------------------------------------------- #
def test_planned_unique_logical_requests_sums_the_routes() -> None:
    plan = build()
    assert plan.planned_unique_logical_requests == sum(
        route.planned_unique_logical_requests for route in plan.routes
    )


def test_maximum_physical_attempts_is_the_sum_of_u_times_a_reachable() -> None:
    plan = build()
    expected = sum(
        route.planned_unique_logical_requests * derive_a_reachable(SOURCES[route.source_id])
        for route in plan.routes
    )
    assert plan.maximum_physical_attempts == expected


def test_maximum_new_raw_objects_equals_planned_unique_logical_requests() -> None:
    plan = build()
    assert plan.maximum_new_raw_objects == plan.planned_unique_logical_requests


def test_the_hard_ceiling_equals_the_maximum_physical_attempts() -> None:
    plan = build()
    assert plan.hard_request_ceiling == plan.maximum_physical_attempts


def test_the_spacing_floor_is_derived_from_the_attempts_and_the_rate() -> None:
    plan = build(requests_per_second=4.0)
    assert plan.rate_limiter_spacing_floor_seconds == pytest.approx(
        max(0, plan.maximum_physical_attempts - 1) / 4.0
    )


def test_no_contingency_multiplier_is_applied() -> None:
    plan = build()
    bare_ceiling = sum(
        route.planned_unique_logical_requests * derive_a_reachable(SOURCES[route.source_id])
        for route in plan.routes
    )
    assert plan.hard_request_ceiling == bare_ceiling  # exactly, no padding


def test_a_route_that_plans_zero_requests_contributes_zero_attempts() -> None:
    plan = build(calendar_evidence_entry_count=0)
    routes = {route.source_id: route for route in plan.routes}
    assert routes["sec_edgar_calendar_announcement"].maximum_physical_attempts == 0


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
def test_a_negative_calendar_entry_count_is_refused() -> None:
    with pytest.raises(RequestPlanInputError, match="calendar_evidence_entry_count"):
        build(calendar_evidence_entry_count=-1)


def test_a_non_positive_request_rate_is_refused() -> None:
    with pytest.raises(RequestPlanInputError, match="requests_per_second"):
        build(requests_per_second=0.0)


def test_a_coverage_end_before_start_is_refused() -> None:
    with pytest.raises((RequestPlanInputError, ValueError)):
        build(coverage_start=date(2024, 6, 30), coverage_end=date(2024, 1, 1))


def test_a_calendar_year_outside_the_coverage_is_refused() -> None:
    with pytest.raises(RequestPlanInputError, match="calendar_year"):
        build(calendar_year=1999)


# --------------------------------------------------------------------------- #
# Determinism, canonical bytes, and content hash
# --------------------------------------------------------------------------- #
def test_identical_inputs_reproduce_identical_canonical_bytes() -> None:
    assert canonical_plan_bytes(build()) == canonical_plan_bytes(build())


def test_identical_inputs_reproduce_the_same_content_hash() -> None:
    assert build().request_plan_sha256 == build().request_plan_sha256


def test_a_different_coverage_moves_the_hash() -> None:
    wider = build(coverage_end=date(2024, 9, 30), as_of_date=date(2024, 9, 30))
    assert wider.request_plan_sha256 != build().request_plan_sha256


def test_the_plan_id_is_derived_from_the_content_hash() -> None:
    plan = build()
    assert plan.request_plan_sha256 in plan.request_plan_id


def test_canonical_bytes_are_utf8_lf_sorted_with_one_trailing_newline() -> None:
    payload = canonical_plan_bytes(build())
    assert payload.endswith(b"\n")
    assert not payload.endswith(b"\n\n")
    assert b"\r" not in payload
    document = json.loads(payload)
    assert list(document) == sorted(document)


def test_the_content_hash_is_sha256_over_the_canonical_bytes() -> None:
    import hashlib

    plan = build()
    assert plan.request_plan_sha256 == hashlib.sha256(canonical_plan_bytes(plan)).hexdigest()


def test_the_schema_version_is_inside_the_hashed_payload() -> None:
    document = json.loads(canonical_plan_bytes(build()))
    assert document["request_plan_schema_version"] == REQUEST_PLAN_SCHEMA_VERSION


def test_the_canonical_payload_carries_no_absolute_path_or_identity() -> None:
    text = canonical_plan_bytes(build()).decode("utf-8")
    assert "/Users/" not in text
    assert "@" not in text


# --------------------------------------------------------------------------- #
# Budget rendering
# --------------------------------------------------------------------------- #
def test_the_budget_renders_the_derived_quantities() -> None:
    budget = render_budget(build())
    assert budget["planned_unique_logical_requests"] == build().planned_unique_logical_requests
    assert budget["maximum_physical_attempts"] == build().maximum_physical_attempts
    assert budget["maximum_new_raw_objects"] == build().maximum_new_raw_objects
    assert budget["hard_request_ceiling"] == build().hard_request_ceiling
    assert "rate_limiter_spacing_floor_seconds" in budget


def test_the_budget_reports_per_route_a_reachable() -> None:
    budget = render_budget(build())
    per_route = budget["per_route"]
    full_index = next(row for row in per_route if row["source_id"] == "sec_full_index_company")
    assert full_index["a_reachable"] == 11


def test_the_budget_names_the_acquisition_window() -> None:
    assert render_budget(build())["acquisition_window"] == "M3.2A"


def test_the_budget_is_pure_and_leaves_the_plan_unchanged() -> None:
    plan = build()
    before = canonical_plan_bytes(plan)
    render_budget(plan)
    assert canonical_plan_bytes(plan) == before
