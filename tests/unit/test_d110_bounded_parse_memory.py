"""Bounded-memory bulk-archive parsing (accepted Decision 110 §§7-9, Workstream B).

D109 finding **F1**, accepted MAJOR: the one authorized real M3.3-E0 v2 execution ran roughly 63
minutes, reached no durable source boundary at all, and was killed by the kernel holding about
33.9 GB of compressed process memory. The measured cause is on E0's first planned source — a
1.56 GB archive of 985,834 JSON members expanding to 5.71 GB and parsing to roughly 22.5 million
records — where ``_parse_bulk_submissions`` materialised **every** member and **every** member's
parse outcome before persisting any of them, and ``merge_outcomes`` then copied all of it again.

Two families of proof live here, and they are different claims:

**Equivalence.** The streamed path must write the same catalog the merged path writes. These
tests run both over the same synthetic archive into two separate disposable catalogs and compare
every row of every census table the parse touches. This is what makes the remediation
execution-mechanics rather than a change of meaning, so it is asserted on the rows themselves
rather than on counts.

**Boundedness.** Peak memory must not follow the input. The scaling tests drive **production**
parsing code — :func:`~disclosure_drift.m3.offline_parse.run_offline_metadata_parse` end to end —
over two materially different input volumes and require that a tenfold input does not produce a
tenfold peak. A companion mutation test restores the pre-D110 materialising implementation and
requires the same measurement to fail, so the bound is a real observation rather than a threshold
that could never be crossed.

Everything runs over disposable catalogs beneath temporary directories. Nothing here resolves,
opens, names, or infers the accepted private evidence root, and no test reads a real SEC artifact.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tracemalloc
import zipfile
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.m3 import offline_parse as op
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.census import STREAMED_STRUCTURAL_DETAIL_LIMIT, CensusCatalog
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES, CatalogWriter
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

_AT = "2026-01-01T00:00:00Z"
_RUN = "job-census-1"
_OBSERVATION = "obs-bulk-1"
_INSTANCE = "base|sec_bulk_submissions|1"
_ARCHIVE_RELATIVE = "raw/sec/bulk/sec_bulk_submissions-synthetic.zip"

#: Every table the bulk parse writes, in the order a diff is easiest to read.
_COMPARED_TABLES = (
    "census_parser_runs",
    "census_parsed_records",
    "census_quarantined_records",
    "census_structural_observations",
    "census_registrants",
    "census_registrant_observations",
    "census_accessions",
    "census_accession_observations",
    "census_accession_registrants",
    "census_accession_field_resolutions",
    "census_accession_cohort_resolutions",
    "census_historical_references",
    "census_malformed_historical_references",
    "census_candidate_lineage_edges",
)


# ==========================================================================
# A synthetic bulk archive whose size is a parameter
# ==========================================================================


def _submissions_document(cik: int, *, filings: int, historical: int = 1) -> dict[str, Any]:
    """One synthetic submissions document with a caller-chosen number of filings.

    ``filings`` is the knob the scaling tests turn: it is what makes an archive's *content* and
    its *parsed record count* grow without changing how many members the archive holds, which
    isolates record-scale memory from the archive index's own per-member cost.
    """
    padded = f"{cik:010d}"
    return {
        "cik": str(cik),
        "name": f"SYNTHETIC {cik}",
        "sic": "2834",
        "fiscalYearEnd": "1231",
        "tickers": [f"SY{cik}"],
        "exchanges": ["Nasdaq"],
        "formerNames": [{"name": f"OLD {cik}", "from": "2018-01-01", "to": "2020-01-01"}],
        "filings": {
            "recent": {
                "accessionNumber": [f"{padded}-24-{index:06d}" for index in range(filings)],
                "filingDate": ["2024-02-01"] * filings,
                "form": ["10-K"] * filings,
            },
            "files": [
                {
                    "name": f"CIK{padded}-submissions-{index:03d}.json",
                    "filingCount": 1,
                    "filingFrom": "2010-01-01",
                    "filingTo": "2010-12-31",
                }
                for index in range(historical)
            ],
        },
    }


def _write_archive(
    path: Path, *, members: int, filings: int, malformed: int = 0, duplicate: bool = False
) -> bytes:
    """Build a synthetic bulk archive and return its bytes.

    ``malformed`` members are missing ``filings`` entirely, which is a blocking drift event and
    therefore produces a quarantined record and an untrustworthy structural verdict — the shapes
    the run-state and reason-code accounting have to survive on both paths.

    ``duplicate`` gives the **last** member the first member's CIK and lists one of its
    accessions twice. That is the case a stream cannot decide locally: the duplicate is detected
    inside the last document, but the run-level verdict it produces applies to a record the first
    member contributed and that was written long before the last member was read.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        for index in range(members):
            last = duplicate and index == members - 1
            cik = 1 if last else index + 1
            document: dict[str, Any] = _submissions_document(cik, filings=filings)
            if last:
                recent = document["filings"]["recent"]
                for key in ("accessionNumber", "filingDate", "form"):
                    recent[key] = [recent[key][0], *recent[key]]
            if index < malformed:
                document = copy.deepcopy(document)
                del document["filings"]
            archive.writestr(
                f"CIK{cik:010d}-member-{index:06d}.json",
                json.dumps(document, sort_keys=True),
            )
        # A non-JSON member, so the suffix filter is exercised on both paths alike.
        archive.writestr("readme.txt", "not a submissions document")
    return path.read_bytes()


def _seed_catalog(database: Path, tree: DataTree, archive_bytes: bytes) -> None:
    """A disposable catalog carrying exactly one planned bulk-submissions source."""
    digest = hashlib.sha256(archive_bytes).hexdigest()
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        with transaction(connection) as active:
            for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
                active.execute(
                    "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                    "is_eligible_universe, description, decision_record) VALUES (?,?,?,?,?)",
                    (form_type, int(is_amendment), int(eligible), description, "D007"),
                )
            for code in REASON_CODES.values():
                active.execute(
                    "INSERT OR REPLACE INTO reference_reason_codes (reason_code, category, "
                    "description, blocks_release, requires_manual_review, decision_record) "
                    "VALUES (?,?,?,?,?,?)",
                    (
                        code.code,
                        code.category,
                        code.description,
                        int(code.blocks_release),
                        int(code.requires_manual_review),
                        code.decision_reference,
                    ),
                )
            active.execute(
                "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
                "started_at_utc, detail) VALUES (?, 'sec_census', 'completed', 'M2.2', ?, '')",
                (_RUN, _AT),
            )
            active.execute(
                "INSERT INTO census_source_observations (observation_id, source_id, "
                "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
                "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
                "content_size_bytes, storage_representation, relative_storage_path, "
                "parser_version, recorded_at_utc) VALUES (?, 'sec_bulk_submissions', "
                "'req/bulk/1', 'https://example.invalid/submissions.zip', 'census', ?, "
                "'stored_new', ?, ?, ?, ?, ?, 'identical', ?, 'submissions-json/1.0', ?)",
                (
                    _OBSERVATION,
                    _AT,
                    digest,
                    digest,
                    digest,
                    len(archive_bytes),
                    len(archive_bytes),
                    _ARCHIVE_RELATIVE,
                    _AT,
                ),
            )
            active.execute(
                "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                "source_id, request_identity, required, source_scope, retrieval_state, "
                "snapshot_state, parser_state, catalog_state, qa_state, "
                "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                "updated_at_utc) VALUES (?, ?, 'sec_bulk_submissions', 'req/bulk/1', 1, "
                "'base', 'retrieved', 'verified', 'not_started', 'committed', 'passed', "
                "'[]', ?, 1, ?)",
                (_RUN, _INSTANCE, _OBSERVATION, _AT),
            )


def _world(
    root: Path, *, members: int, filings: int, malformed: int = 0, duplicate: bool = False
) -> tuple[Path, DataTree]:
    """A disposable catalog plus data tree holding one synthetic bulk archive."""
    tree = DataTree.from_root(root / "data")
    database = root / "catalog.sqlite3"
    raw = _write_archive(
        tree.data_root / _ARCHIVE_RELATIVE,
        members=members,
        filings=filings,
        malformed=malformed,
        duplicate=duplicate,
    )
    _seed_catalog(database, tree, raw)
    return database, tree


def _observation(tree: DataTree, database: Path) -> SourceObservation:
    from disclosure_drift.sec.observation_catalog import load_observations

    with connect(database, writer=False) as connection:
        return next(
            item for item in load_observations(connection) if item.observation_id == _OBSERVATION
        )


def _rows(database: Path, table: str) -> list[tuple[Any, ...]]:
    """Every row of ``table``, ordered deterministically and with volatile columns dropped.

    Timestamps are excluded because both paths stamp ``utc_now()`` at their own instants; the
    claim under test is that the *content* is identical, not that two runs happened at once.
    """
    with connect(database, writer=False) as connection:
        columns = [
            str(row["name"])
            for row in connection.execute(f"PRAGMA table_info({table})")  # noqa: S608
            if not str(row["name"]).endswith(("_at_utc", "_at"))
        ]
        if not columns:
            return []
        projection = ", ".join(columns)
        return sorted(
            tuple(row)
            for row in connection.execute(f"SELECT {projection} FROM {table}")  # noqa: S608
        )


def _run_streamed(database: Path, tree: DataTree, locks: Path) -> op.OfflineParseReport:
    with CatalogWriter(database, locks) as writer:
        return op.run_offline_metadata_parse(writer=writer, tree=tree)


def _run_merged(database: Path, tree: DataTree, locks: Path) -> op.OfflineParseReport:
    """Drive the identical production driver the pre-D110 way: merge first, then persist once.

    Emptying :data:`~disclosure_drift.m3.offline_parse.STREAMED_SOURCE_IDS` is exactly what the
    module did before Decision 110 — every source through ``_parse_source`` and
    ``CensusCatalog.persist``. Running *the same driver* both ways is what makes the comparison
    an apples-to-apples one: everything downstream of persistence, including the §6.4 association
    projection, runs identically on both sides and cannot mask a difference or invent one.
    """
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(op, "STREAMED_SOURCE_IDS", frozenset())
        with CatalogWriter(database, locks) as writer:
            return op.run_offline_metadata_parse(writer=writer, tree=tree)


# ==========================================================================
# Equivalence: the streamed catalog is the merged catalog
# ==========================================================================


@pytest.mark.parametrize(
    ("members", "filings", "malformed", "duplicate"),
    [
        pytest.param(6, 3, 0, False, id="plain"),
        pytest.param(6, 3, 2, False, id="with-malformed-members"),
        pytest.param(6, 3, 0, True, id="with-a-cross-member-duplicate"),
        pytest.param(3, 40, 0, False, id="filing-heavy"),
    ],
)
def test_the_streamed_path_writes_the_same_rows_as_the_merged_path(
    tmp_path: Path, members: int, filings: int, malformed: int, duplicate: bool
) -> None:
    """Row-for-row equivalence across every table the bulk parse touches.

    The four shapes are the ones where a streaming rewrite could plausibly diverge: ordinary
    members, members that quarantine, a duplicate identity that only the *last* member reveals,
    and documents heavy enough that record order within a member matters.
    """
    streamed_root = tmp_path / "streamed"
    merged_root = tmp_path / "merged"
    streamed_root.mkdir()
    merged_root.mkdir()
    streamed_db, streamed_tree = _world(
        streamed_root, members=members, filings=filings, malformed=malformed, duplicate=duplicate
    )
    merged_db, merged_tree = _world(
        merged_root, members=members, filings=filings, malformed=malformed, duplicate=duplicate
    )

    _run_streamed(streamed_db, streamed_tree, streamed_root / "locks")
    _run_merged(merged_db, merged_tree, merged_root / "locks")

    for table in _COMPARED_TABLES:
        if table == "census_parser_runs":
            continue
        assert _rows(streamed_db, table) == _rows(merged_db, table), table


def test_the_streamed_run_row_matches_except_for_the_bounded_summary(tmp_path: Path) -> None:
    """The one deliberate difference, stated exactly rather than left to a diff.

    Identity, counts, and run state are identical. ``summary_json`` differs in one array and
    gains one key that says so. Everything else in the summary is computed by the same rule.
    """
    streamed_root = tmp_path / "streamed"
    merged_root = tmp_path / "merged"
    streamed_root.mkdir()
    merged_root.mkdir()
    streamed_db, streamed_tree = _world(streamed_root, members=5, filings=4)
    merged_db, merged_tree = _world(merged_root, members=5, filings=4)

    _run_streamed(streamed_db, streamed_tree, streamed_root / "locks")
    _run_merged(merged_db, merged_tree, merged_root / "locks")

    streamed_run = _rows(streamed_db, "census_parser_runs")
    merged_run = _rows(merged_db, "census_parser_runs")
    assert len(streamed_run) == len(merged_run) == 1

    with connect(streamed_db, writer=False) as connection:
        streamed = dict(connection.execute("SELECT * FROM census_parser_runs").fetchone())
    with connect(merged_db, writer=False) as connection:
        merged = dict(connection.execute("SELECT * FROM census_parser_runs").fetchone())

    for column in ("parser_run_id", "source_observation_id", "parser_id", "parser_version"):
        assert streamed[column] == merged[column], column
    assert streamed["parsed_count"] == merged["parsed_count"]
    assert streamed["quarantined_count"] == merged["quarantined_count"]
    assert streamed["outcome"] == merged["outcome"]

    left = json.loads(str(streamed["summary_json"]))
    right = json.loads(str(merged["summary_json"]))
    for key in (
        "parser_id",
        "parser_version",
        "layer_version",
        "counts",
        "counts_are_trustworthy",
        "unknown_field_paths",
        "normalization_warnings",
        "duplicate_identities",
        "required_field_failures",
        "reason_codes",
    ):
        assert left[key] == right[key], key

    # The bounded array, and the disclosure that makes the bound legible.
    assert left["structural"] == []
    assert right["structural"] != []
    assert left["structural_detail"] == {
        "scope": "blocking_only",
        "observed": left["counts"]["structural_observations"],
        "blocking": 0,
        "retained": 0,
        "retention_limit": STREAMED_STRUCTURAL_DETAIL_LIMIT,
        "table": "census_structural_observations",
    }
    assert "structural_detail" not in right


def test_the_streamed_summary_keeps_the_blocking_structural_detail(tmp_path: Path) -> None:
    """What the bound keeps is the part that changes the run's meaning.

    A blocking structural verdict is why a run is recorded ``failed`` and why its counts may not
    be read. Those observations stay in the summary verbatim; the ones that merely say "this
    region was fine" are the volume, and they remain individually durable in their own table.
    """
    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=4, filings=2, malformed=2)

    _run_streamed(database, tree, root / "locks")

    with connect(database, writer=False) as connection:
        row = connection.execute("SELECT * FROM census_parser_runs").fetchone()
        persisted = connection.execute(
            "SELECT COUNT(*) AS n FROM census_structural_observations"
        ).fetchone()["n"]
    summary = json.loads(str(row["summary_json"]))

    assert row["outcome"] == "failed"
    assert summary["counts_are_trustworthy"] is False
    assert summary["structural_detail"]["blocking"] > 0
    assert len(summary["structural"]) == summary["structural_detail"]["blocking"]
    assert all(item["count_is_trustworthy"] is False for item in summary["structural"])
    # Every observation, blocking or not, is durable in its own table.
    assert persisted == summary["structural_detail"]["observed"]


def test_a_cross_member_duplicate_identity_reaches_records_written_before_it(
    tmp_path: Path,
) -> None:
    """The ordering hazard a streaming rewrite is most likely to get wrong.

    The duplicate CIK appears only in the archive's **last** member, long after the records it
    marks were inserted. The merged path knew about it up front; the streamed path applies it in
    one bounded pass at the end. Both must reach the same rows, and this asserts the flag is
    genuinely raised rather than the fixture happening to produce none.
    """
    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=4, filings=2, duplicate=True)

    _run_streamed(database, tree, root / "locks")

    with connect(database, writer=False) as connection:
        flagged = connection.execute(
            "SELECT native_identity FROM census_parsed_records WHERE duplicate_indicator = 1 "
            "ORDER BY native_identity"
        ).fetchall()
        summary = json.loads(
            str(connection.execute("SELECT summary_json FROM census_parser_runs").fetchone()[0])
        )

    assert summary["duplicate_identities"], "the fixture must actually produce a duplicate"
    reported = {identity for identity, _ in summary["duplicate_identities"]}
    assert {str(row["native_identity"]) for row in flagged} >= reported


def test_the_streamed_plan_row_reaches_the_same_parser_state(tmp_path: Path) -> None:
    """The plan-row terminal is derived from the run state, and the two vocabularies agree."""
    for malformed, expected in ((0, "completed"), (2, "failed")):
        root = tmp_path / f"case-{malformed}"
        root.mkdir()
        database, tree = _world(root, members=4, filings=2, malformed=malformed)

        report = _run_streamed(database, tree, root / "locks")

        with connect(database, writer=False) as connection:
            state = connection.execute(
                "SELECT parser_state FROM census_plan_sources WHERE source_instance_id = ?",
                (_INSTANCE,),
            ).fetchone()["parser_state"]
        assert state == expected, malformed
        assert report.by_disposition("E0_REQUIRED_PARSE")[0].parser_state_after == expected


def test_a_repeat_streamed_persist_is_idempotent(tmp_path: Path) -> None:
    """Re-running against an already-recorded run reports it rather than writing it twice."""
    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=4, filings=2)

    _run_streamed(database, tree, root / "locks")
    before = {table: _rows(database, table) for table in _COMPARED_TABLES}

    observation = _observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])
    with CatalogWriter(database, root / "locks") as writer:
        repeat = CensusCatalog(writer).persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES["sec_bulk_submissions"].parser_version,
            source_observation_id=observation.observation_id,
        )

    assert repeat.already_present is True
    assert repeat.run_outcome == "completed"
    assert {table: _rows(database, table) for table in _COMPARED_TABLES} == before


def test_a_part_bound_to_another_observation_is_refused(tmp_path: Path) -> None:
    """The streamed twin of the merged path's one-observation rule, refused one record earlier.

    Both of that rule's refusals are proved: an observation the catalog does not carry, and a
    real observation the archive's parts do not belong to. The merged path decides the second by
    surveying every record first; a stream decides it on the first record that disagrees, which
    is the same rule reached sooner rather than a weaker one.
    """
    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=2, filings=2)
    observation = _observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])

    def run(observation_id: str) -> None:
        with CatalogWriter(database, root / "locks") as writer:
            CensusCatalog(writer).persist_streamed(
                op._stream_bulk_submissions(store, observation),
                parser_id=op._BULK_PARSER_ID,
                parser_version=SOURCES["sec_bulk_submissions"].parser_version,
                source_observation_id=observation_id,
            )

    with pytest.raises(ValueError, match="is not in the catalog"):
        run("obs-that-is-not-bound")

    with connect(database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
            "content_size_bytes, storage_representation, relative_storage_path, "
            "parser_version, recorded_at_utc) VALUES ('obs-other', 'sec_bulk_submissions', "
            "'req/bulk/2', 'https://example.invalid/other.zip', 'census', ?, 'stored_new', "
            "'a', 'a', 'a', 1, 1, 'identical', 'raw/sec/bulk/other.zip', "
            "'submissions-json/1.0', ?)",
            (_AT, _AT),
        )

    with pytest.raises(ValueError, match="exactly one source observation"):
        run("obs-other")


# ==========================================================================
# Boundedness: peak memory must not follow the input
# ==========================================================================


def _peak_traced_bytes(root: Path, *, members: int, filings: int) -> tuple[int, int]:
    """Peak traced Python memory for one production run, with its parsed-record count.

    The catalog build is deliberately outside the measured window: the claim is about what
    *parsing and persisting* retains, and seeding a fixture is neither.
    """
    database, tree = _world(root, members=members, filings=filings)
    tracemalloc.start()
    try:
        tracemalloc.reset_peak()
        report = _run_streamed(database, tree, root / "locks")
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    parsed = report.by_disposition("E0_REQUIRED_PARSE")[0].parsed_records
    return peak, parsed


def test_a_tenfold_input_does_not_produce_a_tenfold_peak(tmp_path: Path) -> None:
    """**The D110 §9 acceptance requirement**, on production code, over real parsed volume.

    Content per member is the dimension that scales: ten times the filings is ten times the
    parsed records from the same number of archive members, which isolates record-scale
    retention from the archive index's own unavoidable per-member cost. The merged path retained
    every one of those records; the streamed path retains one member's worth at a time, so the
    peak barely moves.

    The bound is 3x against a ~10x input, and it is loose on purpose: peak memory is *allowed*
    to depend on one member, and a member with ten times the filings is ten times the chunk. The
    measured streamed ratio is about 1.6x, the merged ratio about 7.5x, and the mutation test
    below pins that difference from the other side.
    """
    small_root = tmp_path / "small"
    large_root = tmp_path / "large"
    small_root.mkdir()
    large_root.mkdir()

    small_peak, small_records = _peak_traced_bytes(small_root, members=40, filings=40)
    large_peak, large_records = _peak_traced_bytes(large_root, members=40, filings=400)

    record_ratio = large_records / small_records
    peak_ratio = large_peak / small_peak
    assert record_ratio >= 9.0, (small_records, large_records)
    assert peak_ratio < 3.0, {
        "small_peak_bytes": small_peak,
        "large_peak_bytes": large_peak,
        "peak_ratio": peak_ratio,
        "record_ratio": record_ratio,
    }


def test_a_tenfold_member_count_does_not_produce_a_tenfold_peak(tmp_path: Path) -> None:
    """The other input dimension: more members rather than bigger ones.

    This one cannot be perfectly flat and is not claimed to be — ``iter_members`` must hold the
    archive's central directory and its collision-detection sets for the whole traversal, which
    is proportional to the member *count*. Measured on the accepted first planned source that
    fixed cost is about 1.07 GB of RSS for 985,834 members and it stays flat thereafter, which is
    why it is inside the owner's 2.5 GiB ceiling rather than the thing that broke it. What must
    not scale is everything downstream of it.
    """
    small_root = tmp_path / "small"
    large_root = tmp_path / "large"
    small_root.mkdir()
    large_root.mkdir()

    small_peak, small_records = _peak_traced_bytes(small_root, members=30, filings=6)
    large_peak, large_records = _peak_traced_bytes(large_root, members=300, filings=6)

    assert large_records / small_records >= 9.0
    assert large_peak / small_peak < 3.0, {
        "small_peak_bytes": small_peak,
        "large_peak_bytes": large_peak,
        "peak_ratio": large_peak / small_peak,
    }


_RSS_PROGRAM = """
import json, resource, sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from d110_rss_harness import measure

print(json.dumps(measure(Path(sys.argv[2]), members=int(sys.argv[3]), filings=int(sys.argv[4]))))
"""

_RSS_HARNESS = '''
"""Out-of-process RSS harness for the D110 memory proof."""
from __future__ import annotations

import importlib
import resource
import sys
from pathlib import Path


def measure(root: Path, *, members: int, filings: int) -> dict[str, int]:
    module = importlib.import_module("test_d110_bounded_parse_memory")
    database, tree = module._world(root, members=members, filings=filings)
    before = _rss()
    report = module._run_streamed(database, tree, root / "locks")
    return {
        "rss_before": before,
        "rss_peak": _rss(),
        "records": report.by_disposition("E0_REQUIRED_PARSE")[0].parsed_records,
    }


def _rss() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024
'''


def test_a_tenfold_input_does_not_produce_a_tenfold_process_rss(tmp_path: Path) -> None:
    """The same requirement measured on process RSS rather than traced Python allocations.

    D110 §9 asks for an RSS-capable measurement alongside ``tracemalloc`` where native memory
    materially contributes, and here it does: ``zipfile`` decompression and SQLite both allocate
    outside Python's allocator. Each size runs in its own subprocess because ``ru_maxrss`` is a
    high-water mark for the whole process and cannot be reset.
    """
    harness_dir = tmp_path / "harness"
    harness_dir.mkdir()
    (harness_dir / "d110_rss_harness.py").write_text(_RSS_HARNESS, encoding="utf-8")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(harness_dir), str(Path(__file__).parent), environment.get("PYTHONPATH", "")]
    )

    measured: dict[str, dict[str, int]] = {}
    for label, filings in (("small", 40), ("large", 400)):
        root = tmp_path / label
        root.mkdir()
        completed = subprocess.run(  # noqa: S603
            [
                sys.executable,
                "-c",
                _RSS_PROGRAM,
                str(harness_dir),
                str(root),
                "40",
                str(filings),
            ],
            capture_output=True,
            text=True,
            check=True,
            env=environment,
        )
        measured[label] = json.loads(completed.stdout.strip().splitlines()[-1])

    small = measured["small"]
    large = measured["large"]
    assert large["records"] / small["records"] >= 9.0
    growth_small = max(small["rss_peak"] - small["rss_before"], 1)
    growth_large = max(large["rss_peak"] - large["rss_before"], 1)
    assert growth_large / growth_small < 3.0, measured


def test_the_memory_bound_dies_if_the_materialising_parse_is_restored(tmp_path: Path) -> None:
    """Non-vacuity: put the pre-D110 implementation back and the scaling proof must fail.

    ``materialize_source_layer`` is pointed at the merged path for the bulk source — exactly what
    it did before Decision 110 — and the same tenfold input is measured again. If the assertion
    in :func:`test_a_tenfold_input_does_not_produce_a_tenfold_peak` could pass either way it
    would prove nothing; this shows it cannot.
    """
    small_root = tmp_path / "small"
    large_root = tmp_path / "large"
    small_root.mkdir()
    large_root.mkdir()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(op, "STREAMED_SOURCE_IDS", frozenset())
        small_peak, small_records = _peak_traced_bytes(small_root, members=40, filings=40)
        large_peak, large_records = _peak_traced_bytes(large_root, members=40, filings=400)

    assert large_records / small_records >= 9.0
    assert large_peak / small_peak >= 3.0, {
        "small_peak_bytes": small_peak,
        "large_peak_bytes": large_peak,
        "peak_ratio": large_peak / small_peak,
    }


def test_the_streamed_traversal_does_not_grow_across_member_boundaries(tmp_path: Path) -> None:
    """Boundedness stated per boundary rather than as one aggregate.

    A peak measurement is an aggregate and can hide slow accumulation that only a much larger
    fixture would expose. This walks the production generator and records live traced memory at
    every member boundary, then requires the second half of the traversal to sit no higher than
    the first — the property the aggregate measurement is evidence *for*, and the same property
    §11 asks the multi-source canary to show across completed sources.

    Live memory is used rather than peak because peak is monotonic by definition and would make
    the assertion unfalsifiable. ``ParseOutcome`` carries ``slots``, so it cannot be weak-
    referenced; measuring what the heap holds is both possible and the more direct claim.
    """
    import gc

    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=60, filings=8)
    observation = _observation(tree, database)
    store = SnapshotStore(tree)
    store.adopt([observation])

    live: list[int] = []
    tracemalloc.start()
    try:
        for outcome, _ in op._stream_bulk_submissions(store, observation):
            assert outcome.records
            del outcome
            gc.collect()
            live.append(tracemalloc.get_traced_memory()[0])
    finally:
        tracemalloc.stop()

    assert len(live) == 60
    half = len(live) // 2
    first = sum(live[:half]) / half
    second = sum(live[half:]) / (len(live) - half)
    assert second <= first * 1.10, {"first_half_mean": first, "second_half_mean": second}


def test_the_offline_parse_report_is_unchanged_by_streaming(tmp_path: Path) -> None:
    """The R18 disposition accounting is untouched: same disposition, same counts, same totals."""
    root = tmp_path / "streamed"
    root.mkdir()
    database, tree = _world(root, members=5, filings=3)

    report = _run_streamed(database, tree, root / "locks")

    assert report.is_complete
    assert report.planned_source_count == 1
    (only,) = report.outcomes
    assert only.disposition == "E0_REQUIRED_PARSE"
    assert only.source_id == "sec_bulk_submissions"
    assert only.parser_state_before == "not_started"
    assert only.parser_state_after == "completed"
    assert only.parsed_records > 0
    assert only.quarantined_records == 0
