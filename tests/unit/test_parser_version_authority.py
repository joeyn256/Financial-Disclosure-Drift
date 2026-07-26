"""Parser-version provenance: one authoritative definition, drift impossible.

The parser implementation owns its identifier and version. The source registry records
which parser is compatible and *derives* the version, so a second hand-maintained copy
cannot fall behind. Before this was enforced, three registrations had already drifted:
``submissions-json`` sat at 1.0 against an implementation at 1.1, and both calendar
parsers sat at 1.0 against implementations at 2.0.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from disclosure_drift.paths import DataTree
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.parsers.calendar import (
    ANNOUNCEMENT_PARSER_ID,
    ANNOUNCEMENT_PARSER_VERSION,
    CALENDAR_PARSER_ID,
    CALENDAR_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.full_index import (
    FULL_INDEX_PARSER_ID,
    FULL_INDEX_PARSER_VERSION,
)
from disclosure_drift.sec.parsers.submissions import PARSER_ID, PARSER_VERSION
from disclosure_drift.sec.parsers.versions import (
    PARSER_VERSIONS,
    ParserVersionError,
    parser_version_for,
    require_parser_version,
    versions_agree,
)
from disclosure_drift.sec.snapshots import SnapshotStore
from disclosure_drift.sec.source_registry import SOURCES, require_registered
from disclosure_drift.sec.urls import request_identity

TICKERS = "sec_company_tickers_exchange"
TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
BODY = b'{"fields":["cik","name","ticker","exchange"],"data":[[1,"SYN","SYN","Nasdaq"]]}'


@pytest.fixture
def store(tmp_path: Path) -> SnapshotStore:
    tree = DataTree.from_root(tmp_path)
    tree.ensure_tree()
    return SnapshotStore(tree)


# --------------------------------------------------------------------------- #
# 1. Registry and parser versions agree
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("source_id", sorted(SOURCES))
def test_every_registration_derives_the_implementation_version(source_id: str) -> None:
    spec = SOURCES[source_id]
    assert spec.parser_id in PARSER_VERSIONS
    assert spec.parser_version == PARSER_VERSIONS[spec.parser_id]


def test_the_authoritative_table_is_built_from_the_implementations() -> None:
    assert PARSER_VERSIONS[PARSER_ID] == PARSER_VERSION
    assert PARSER_VERSIONS[CALENDAR_PARSER_ID] == CALENDAR_PARSER_VERSION
    assert PARSER_VERSIONS[ANNOUNCEMENT_PARSER_ID] == ANNOUNCEMENT_PARSER_VERSION
    assert PARSER_VERSIONS[FULL_INDEX_PARSER_ID] == FULL_INDEX_PARSER_VERSION


def test_the_previously_drifted_versions_are_now_correct() -> None:
    # The three that had silently fallen behind their implementations.
    assert SOURCES["sec_bulk_submissions"].parser_version == "submissions-json/1.1"
    assert SOURCES["sec_edgar_filing_calendar"].parser_version == "edgar-calendar/2.0"
    assert (
        SOURCES["sec_edgar_calendar_announcement"].parser_version
        == "edgar-calendar-announcement/2.0"
    )


def test_the_registry_stores_no_duplicate_version_string() -> None:
    """``parser_version`` must be derived, not a stored field.

    A stored field is what allows drift, so this asserts the attribute is a property on
    the class rather than a dataclass field.
    """
    spec = SOURCES["sec_bulk_submissions"]
    assert "parser_version" not in spec.__dataclass_fields__
    assert isinstance(type(spec).parser_version, property)


def test_an_unknown_parser_identity_has_no_default_version() -> None:
    with pytest.raises(ParserVersionError, match="no implementation declaring a version"):
        parser_version_for("not-a-real-parser")


# --------------------------------------------------------------------------- #
# 2. An intentional mismatch fails before ingestion or reuse
# --------------------------------------------------------------------------- #
def test_a_pinned_expected_version_that_disagrees_fails_closed() -> None:
    from disclosure_drift.sec import source_registry

    drifted = replace(
        SOURCES["sec_bulk_submissions"],
        expected_parser_version="submissions-json/0.9",
    )
    with pytest.raises(AssertionError, match="expects parser version"):
        source_registry._validate_registry_entry(drifted)  # noqa: SLF001


def test_a_registration_naming_an_unimplemented_parser_fails_closed() -> None:
    from disclosure_drift.sec import source_registry

    unknown = replace(SOURCES["sec_bulk_submissions"], parser_id="ghost-parser")
    with pytest.raises(AssertionError, match="no implementation declares"):
        source_registry._validate_registry_entry(unknown)  # noqa: SLF001


def test_a_mismatched_version_is_refused_before_a_parser_run_is_persisted() -> None:
    with pytest.raises(ParserVersionError, match="would record"):
        require_parser_version(PARSER_ID, "submissions-json/0.9", context="parser run")


def test_the_matching_version_is_accepted_and_returned() -> None:
    assert require_parser_version(PARSER_ID, PARSER_VERSION) == PARSER_VERSION
    assert require_parser_version(PARSER_ID, None) == PARSER_VERSION


# --------------------------------------------------------------------------- #
# 3. Persisted parser runs record the authoritative version
# --------------------------------------------------------------------------- #
def test_a_registered_source_reports_the_authoritative_version_to_the_catalog() -> None:
    spec = require_registered("sec_bulk_submissions")
    # This is the value the catalog writes into census_parser_runs.parser_version.
    assert spec.parser_version == parser_version_for(spec.parser_id)
    assert spec.parser_version.endswith("/1.1")


# --------------------------------------------------------------------------- #
# 4 and 5. Reuse rejects an incompatible version, accepts a matching one
# --------------------------------------------------------------------------- #
def retrieved(**overrides: object) -> FetchResult:
    values: dict[str, object] = {
        "outcome": "retrieved",
        "source_id": TICKERS,
        "url": TICKERS_URL,
        "purpose": "parser-version authority check",
        "status": 200,
        "body": BODY,
        "etag": 'W/"v1"',
        "last_modified": "Wed, 01 Jul 2026 00:00:00 GMT",
        "declared_content_type": "application/json",
        "identity": request_identity(TICKERS, TICKERS_URL),
        "final_url": TICKERS_URL,
        "attempts": 1,
    }
    values.update(overrides)
    return FetchResult(**values)  # type: ignore[arg-type]


def not_modified(**overrides: object) -> FetchResult:
    values: dict[str, object] = {
        "outcome": "not_modified",
        "source_id": TICKERS,
        "url": TICKERS_URL,
        "purpose": "parser-version authority check",
        "status": 304,
        "identity": request_identity(TICKERS, TICKERS_URL),
        "final_url": TICKERS_URL,
        "attempts": 1,
    }
    values.update(overrides)
    return FetchResult(**values)  # type: ignore[arg-type]


def test_reuse_is_permitted_when_the_parser_version_matches(store: SnapshotStore) -> None:
    first = store.record(retrieved())
    assert first.parser_version == SOURCES[TICKERS].parser_version
    latest = store.latest_for(TICKERS, request_identity(TICKERS, TICKERS_URL))
    reused = store.record(
        not_modified(sent_etag=latest.etag, sent_last_modified=latest.last_modified)
    )
    assert reused.outcome == "reused_snapshot"
    assert "SOURCE_SNAPSHOT_REUSED" in reused.reason_codes


def test_reuse_is_refused_when_the_prior_parser_version_is_incompatible(
    store: SnapshotStore,
) -> None:
    store.record(retrieved())
    latest = store.latest_for(TICKERS, request_identity(TICKERS, TICKERS_URL))
    spec = SOURCES[TICKERS]
    stale = replace(latest, parser_version="company-tickers-exchange/0.9")
    decision = store.evaluate_reuse(
        spec,
        not_modified(sent_etag=latest.etag, sent_last_modified=latest.last_modified),
        stale,
        request_identity(TICKERS, TICKERS_URL),
    )
    assert not decision.permitted
    assert "parser_compatibility_known" in decision.failed_checks
    assert "must be reparsed" in decision.detail


def test_a_missing_prior_parser_version_is_never_compatible(store: SnapshotStore) -> None:
    store.record(retrieved())
    latest = store.latest_for(TICKERS, request_identity(TICKERS, TICKERS_URL))
    unversioned = replace(latest, parser_version=None)
    decision = store.evaluate_reuse(
        SOURCES[TICKERS],
        not_modified(sent_etag=latest.etag, sent_last_modified=latest.last_modified),
        unversioned,
        request_identity(TICKERS, TICKERS_URL),
    )
    assert not decision.permitted
    assert "parser_compatibility_known" in decision.failed_checks


@pytest.mark.parametrize(
    ("recorded", "expected"),
    [
        (PARSER_VERSION, True),
        ("submissions-json/1.0", False),
        ("submissions-json/2.0", False),
        (None, False),
    ],
)
def test_versions_agree_only_on_an_exact_match(recorded: str | None, expected: bool) -> None:
    assert versions_agree(PARSER_ID, recorded) is expected


# --------------------------------------------------------------------------- #
# 6. No live request
# --------------------------------------------------------------------------- #
def test_none_of_this_needs_a_network_request(store: SnapshotStore) -> None:
    """The autouse conftest fixture makes any socket use raise.

    Recording an observation and evaluating reuse therefore proves the version authority
    is enforced entirely offline.
    """
    observation = store.record(retrieved())
    assert observation.parser_version == SOURCES[TICKERS].parser_version
