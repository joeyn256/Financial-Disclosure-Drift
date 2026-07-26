"""Stage M2.2-R2.7: quarterly index retrieval orchestration and resumability.

Entirely offline. A scripted transport answers the registered quarterly index URL, so no
socket is opened and no live SEC request is made. Every request still travels through the
shared :class:`SecClient`, so identity, rate limiting, retries, cooldown, redirect and
URL containment, block-page handling, snapshot reuse, and recovery remain in force.
"""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from datetime import date
from pathlib import Path

import pytest

from disclosure_drift.paths import DataTree
from disclosure_drift.sec.http_client import RetrievalPolicy, SecClient
from disclosure_drift.sec.index_plan import CoverageWindow, plan_index_instances
from disclosure_drift.sec.index_retrieval import (
    GLOBAL_STOP_REASONS,
    INDEX_RETRIEVAL_POLICY_VERSION,
    IndexRetrievalAccounting,
    logical_budget,
    order_instances,
    retrieve_instance,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.snapshots import SnapshotStore
from disclosure_drift.sec.transport import SecRequest, TransportResponse

AGENT = "Financial Disclosure Drift research@your-institution.edu"

INDEX_BODY = b"""\
Company Name        Form Type  CIK     Date Filed  File Name
-----------------------------------------------------------------------------
SYNTHETIC ONE INC   10-K       320193  2024-02-01  d/0000320193-24-000001.txt
"""
BLOCK_BODY = (
    b"<html>Your Request Has Been Identified As Part Of A Network Of Automated Tools</html>"
)


class Clock:
    """Deterministic clock so rate limiting and backoff never sleep for real."""

    def __init__(self) -> None:
        self.now = 1000.0
        self.sleeps: list[float] = []

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class ScriptedTransport:
    """Answers each URL from a script. Opens no socket."""

    def __init__(self, script: Mapping[str, list[TransportResponse]]) -> None:
        self.script = {key: list(value) for key, value in script.items()}
        self.requests: list[SecRequest] = []

    def send(self, request: SecRequest) -> TransportResponse:
        self.requests.append(request)
        queue = self.script.get(request.url)
        if not queue:
            return ok(request.url)
        return queue.pop(0)

    def close(self) -> None:
        return None


def index_url(year: int, quarter: int) -> str:
    """The one URL shape this source may ever request."""
    return f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/company.idx"


def ok(url: str, body: bytes = INDEX_BODY) -> TransportResponse:
    return TransportResponse(
        status=200,
        headers={"Content-Type": "text/plain", "ETag": f'W/"{url[-20:]}"'},
        final_url=url,
        body=body,
    )


def blocked(url: str) -> TransportResponse:
    return TransportResponse(
        status=200, headers={"Content-Type": "text/html"}, final_url=url, body=BLOCK_BODY
    )


def transient(url: str) -> TransportResponse:
    return TransportResponse(status=503, headers={}, final_url=url, body=b"")


def client_for(transport: ScriptedTransport) -> SecClient:
    clock = Clock()
    limiter = AggregateRateLimiter(4.0, burst=1, clock=clock.time, sleeper=clock.sleep)
    return SecClient(transport, AGENT, limiter, RetrievalPolicy(), sleeper=clock.sleep)


@pytest.fixture
def store(tmp_path: Path) -> SnapshotStore:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    return SnapshotStore(tree)


def year_plan(as_of: str, *, include_open: bool = False) -> tuple:
    """Return the ordered instances for a 2024 plan evaluated at ``as_of``."""
    plan = plan_index_instances(
        CoverageWindow(
            coverage_start=date(2024, 1, 1),
            coverage_end=date(2024, 12, 31),
            as_of_date=date.fromisoformat(as_of),
            include_open_quarter=include_open,
        )
    )
    return plan, order_instances(plan)


# --------------------------------------------------------------------------- #
# Ordering and budget
# --------------------------------------------------------------------------- #
def test_instances_are_ordered_chronologically_with_the_open_quarter_last() -> None:
    _, ordered = year_plan("2024-08-15")
    assert [item.instance_key for item in ordered] == ["2024QTR1", "2024QTR2", "2024QTR3"]
    assert ordered[-1].kind == "provisional_open_quarter"


def test_the_budget_is_derived_from_the_plan() -> None:
    plan, _ = year_plan("2024-08-15")
    assert logical_budget(plan) == 2
    included, _ = year_plan("2024-08-15", include_open=True)
    assert logical_budget(included) == 3


def test_already_satisfied_instances_are_not_budgeted() -> None:
    plan, _ = year_plan("2024-08-15")
    assert logical_budget(plan, satisfied_keys=["2024QTR1"]) == 1
    assert logical_budget(plan, satisfied_keys=["2024QTR1", "2024QTR2"]) == 0


def test_a_sixty_four_quarter_plan_has_no_hidden_small_limit() -> None:
    plan = plan_index_instances(
        CoverageWindow(date(2009, 1, 1), date(2024, 12, 31), date(2025, 1, 15))
    )
    assert len(plan.required_closed) == 64
    assert logical_budget(plan) == 64
    ordered = order_instances(plan)
    assert [(item.year, item.quarter) for item in ordered] == sorted(
        (item.year, item.quarter) for item in ordered
    )
    assert ordered[0].instance_key == "2009QTR1"
    assert ordered[-1].instance_key == "2024QTR4"


# --------------------------------------------------------------------------- #
# Per-instance retrieval
# --------------------------------------------------------------------------- #
def test_one_logical_retrieval_may_contain_several_actual_attempts(
    store: SnapshotStore,
) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport({url: [transient(url), transient(url), ok(url)]})
    outcome = retrieve_instance(client_for(transport), store, ordered[0])
    assert outcome.state == "parsed"
    assert outcome.logical_retrievals == 1
    assert outcome.http_attempts == 3
    assert outcome.retries == 2


def test_lifecycle_states_are_reported_in_order(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    seen: list[str] = []
    retrieve_instance(
        client_for(ScriptedTransport({url: [ok(url)]})),
        store,
        ordered[0],
        on_state=lambda state, _partial: seen.append(state),
    )
    assert seen == ["retrieval_started", "retrieved", "parsed"]


def test_only_the_approved_quarterly_index_url_is_ever_requested(
    store: SnapshotStore,
) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport({url: [ok(url)]})
    retrieve_instance(client_for(transport), store, ordered[0])
    assert [request.url for request in transport.requests] == [url]


def test_no_filing_document_or_accession_url_is_constructed(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    transport = ScriptedTransport({})
    for instance in ordered[:2]:
        retrieve_instance(client_for(transport), store, instance)
    for request in transport.requests:
        assert "/Archives/edgar/data/" not in request.url
        assert "-index.htm" not in request.url
        assert not request.url.endswith(".xml")


def test_a_verified_snapshot_is_reused_on_a_second_pass(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport({url: [ok(url), TransportResponse(304, {}, url)]})
    client = client_for(transport)
    first = retrieve_instance(client, store, ordered[0])
    second = retrieve_instance(client, store, ordered[0])
    assert first.state == "parsed"
    assert second.state == "parsed"
    assert second.observation is not None
    assert second.observation.outcome in {"reused_snapshot", "unchanged_content"}


# --------------------------------------------------------------------------- #
# Failure continuation and global stops
# --------------------------------------------------------------------------- #
def test_a_block_page_stops_the_whole_loop(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport({url: [blocked(url)] * 6})
    outcome = retrieve_instance(client_for(transport), store, ordered[0])
    assert outcome.global_stop_reason == "global_cooldown_or_block"
    assert outcome.global_stop_reason in GLOBAL_STOP_REASONS
    assert not outcome.satisfied


def test_a_redirect_off_the_boundary_stops_the_whole_loop(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport(
        {url: [TransportResponse(302, {"Location": "https://evil.example/x.idx"}, url)]}
    )
    outcome = retrieve_instance(client_for(transport), store, ordered[0])
    assert outcome.global_stop_reason == "network_containment_failure"


def test_a_malformed_required_quarter_does_not_stop_later_quarters(
    store: SnapshotStore,
) -> None:
    _, ordered = year_plan("2024-08-15")
    bad, good = index_url(2024, 1), index_url(2024, 2)
    transport = ScriptedTransport({bad: [ok(bad, body=b"no separator anywhere")], good: [ok(good)]})
    client = client_for(transport)
    first = retrieve_instance(client, store, ordered[0])
    second = retrieve_instance(client, store, ordered[1])
    assert first.state == "indeterminate"
    assert first.global_stop_reason is None
    assert not first.satisfied
    assert second.state == "parsed"


def test_failed_evidence_is_preserved_not_discarded(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    transport = ScriptedTransport({url: [ok(url, body=b"no separator anywhere")]})
    outcome = retrieve_instance(client_for(transport), store, ordered[0])
    assert outcome.observation is not None
    assert outcome.observation.has_payload


# --------------------------------------------------------------------------- #
# Open quarter
# --------------------------------------------------------------------------- #
def test_a_parsed_open_quarter_never_contributes_finalized_coverage(
    store: SnapshotStore,
) -> None:
    _, ordered = year_plan("2024-08-15", include_open=True)
    open_instance = ordered[-1]
    url = index_url(open_instance.year, open_instance.quarter)
    outcome = retrieve_instance(
        client_for(ScriptedTransport({url: [ok(url)]})), store, open_instance
    )
    assert outcome.state == "parsed"
    assert not outcome.contributes_finalized_coverage
    assert not open_instance.is_finalized_period


def test_an_open_quarter_failure_leaves_closed_quarters_alone(store: SnapshotStore) -> None:
    _, ordered = year_plan("2024-08-15", include_open=True)
    closed, open_instance = ordered[0], ordered[-1]
    closed_url = index_url(closed.year, closed.quarter)
    open_url = index_url(open_instance.year, open_instance.quarter)
    transport = ScriptedTransport(
        {closed_url: [ok(closed_url)], open_url: [ok(open_url, body=b"broken")]}
    )
    client = client_for(transport)
    closed_outcome = retrieve_instance(client, store, closed)
    open_outcome = retrieve_instance(client, store, open_instance)
    assert closed_outcome.state == "parsed"
    assert open_outcome.state == "indeterminate"
    assert closed_outcome.instance.is_finalized_period


# --------------------------------------------------------------------------- #
# Accounting
# --------------------------------------------------------------------------- #
def test_accounting_keeps_logical_and_actual_counts_apart() -> None:
    accounting = IndexRetrievalAccounting(
        instances_planned=3,
        instances_already_satisfied=1,
        logical_budget=2,
        logical_retrievals_initiated=2,
        http_attempts=5,
        instances_successful=2,
    )
    assert accounting.retries == 3
    assert accounting.instances_remaining == 0
    record = accounting.as_record()
    assert record["policy_version"] == INDEX_RETRIEVAL_POLICY_VERSION
    assert record["logical_retrievals_initiated"] == 2
    assert record["http_attempts"] == 5
    assert record["retries"] == 3


def test_remaining_counts_unsatisfied_instances() -> None:
    accounting = IndexRetrievalAccounting(
        instances_planned=4,
        instances_already_satisfied=1,
        logical_budget=3,
        logical_retrievals_initiated=3,
        http_attempts=3,
        instances_successful=1,
        instances_failed=2,
    )
    assert accounting.instances_remaining == 2
    assert accounting.retries == 0


def test_a_stopped_run_records_its_stop_reason() -> None:
    accounting = IndexRetrievalAccounting(
        instances_planned=64,
        logical_budget=64,
        logical_retrievals_initiated=7,
        http_attempts=9,
        instances_successful=6,
        instances_failed=1,
        stopped_early=True,
        stop_reason="global_cooldown_or_block",
    )
    record = accounting.as_record()
    assert record["stopped_early"] is True
    assert record["stop_reason"] == "global_cooldown_or_block"
    assert record["instances_remaining"] == 58


# --------------------------------------------------------------------------- #
# No network
# --------------------------------------------------------------------------- #
def test_nothing_here_opens_a_socket(store: SnapshotStore) -> None:
    """The autouse conftest fixture makes any socket use raise.

    Reaching a parsed outcome therefore proves the whole path is offline.
    """
    _, ordered = year_plan("2024-08-15")
    url = index_url(2024, 1)
    outcome = retrieve_instance(client_for(ScriptedTransport({url: [ok(url)]})), store, ordered[0])
    assert outcome.state == "parsed"


def test_a_temporary_directory_store_needs_no_network(tmp_path: Path) -> None:
    with tempfile.TemporaryDirectory() as directory:
        tree = DataTree.from_root(Path(directory))
        tree.ensure_tree()
        assert SnapshotStore(tree).observations == ()
