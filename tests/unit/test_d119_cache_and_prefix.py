"""Accepted Decision 119 — the cache-bound persistence correction and the prefix surface.

Two bounded changes, and this module holds the proofs for both.

**C1, the explicit page-cache budget (Decision 119 §4).** The Decision 111 working catalog
wrote through SQLite's own default of about 2 MiB because nothing configured one, and accepted
Decision 118 measured that against a working set two orders of magnitude larger. The correction
is one connection-local ``PRAGMA cache_size`` on the run-local **writable** working catalog and
nothing else. The proofs are therefore as much about reach as about effect: an unconfigured
working catalog still reports SQLite's default, the accepted operational catalog is never
touched by it, the shared connection helper configures no cache at all, and two canaries that
differ *only* in the budget reach byte-identical evidence.

**The bounded diagnostic prefix (Decision 119 §§6-8).** A way to run the exact accepted
materialization path over the first ``N`` governed members, so it can be measured at real
scale without committing to a whole source. Every proof here is about what it cannot do: it
cannot reach a source disposition, cannot run the resolution or association passes, cannot
emit any of the five accepted complete-source identities, cannot write the canary result
document, cannot reach a second source, and cannot become a complete-source canary even when
its bound is the whole archive. ``--mode run`` remains the only mode that may establish a real
source, and it refuses a bound outright.

Everything runs over the Decision 116 synthetic world beneath ``tmp_path``. No test resolves,
opens, names, or infers the accepted private evidence root, none reads a real SEC artifact, none
touches a real catalog, and none runs a real source.
"""

from __future__ import annotations

import ast
import inspect
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d112_compact_evidence as d112  # noqa: E402
import test_d116_single_source_canary as d116  # noqa: E402

from disclosure_drift.m3 import offline_parse as op  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3 import working_catalog as wc  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.storage import sqlite as storage_sqlite  # noqa: E402
from disclosure_drift.storage.catalog import strictly_read_only_connection  # noqa: E402
from disclosure_drift.storage.sqlite import connect  # noqa: E402

_BULK_INSTANCE = d116._BULK_INSTANCE
_INDEX_INSTANCE = d116._INDEX_INSTANCE

#: The synthetic bulk archive's member count. Pinned rather than measured so a fixture that
#: grew a member cannot silently turn "the bound equals the whole archive" into "the bound is a
#: proper prefix", which is a different claim from the one Decision 119 §6 asks to be proved.
_ARCHIVE_MEMBERS = 3


# ==========================================================================
# Helpers
# ==========================================================================
def _world(root: Path) -> tuple[Path, DataTree, Path]:
    """A stand-in private root, its tree, and a lawful disposable work root beside it."""
    private = d116._private_root(root)
    return private, DataTree.from_root(private), root / "work"


def _prefix(
    root: Path,
    *,
    member_limit: int,
    instance: str = _BULK_INSTANCE,
    run_id: str = "prefix-1",
    batch_size: int = canary.CANARY_BATCH_SIZE,
    cache_bytes: int | None = canary.WORKING_CATALOG_CACHE_BYTES,
) -> tuple[canary.CanaryPrefixResult, Path, canary.CanaryWorld]:
    """Run one bounded diagnostic prefix and return everything it measured."""
    private, tree, work_root = _world(root)
    result = canary.run_single_source_prefix_profile(
        operational_catalog=d116._catalog(private),
        tree=tree,
        work_root=work_root,
        run_id=run_id,
        source_instance_id=instance,
        member_limit=member_limit,
        batch_size=batch_size,
        cache_bytes=cache_bytes,
    )
    return result, private, canary.CanaryWorld(run_id=run_id, directory=work_root / run_id)


def _canary(
    root: Path, *, run_id: str, cache_bytes: int | None
) -> tuple[canary.CanaryResult, Path, canary.CanaryWorld]:
    """One complete-source canary over the bulk source, under a stated cache budget."""
    private, tree, work_root = _world(root)
    result = canary.run_single_source_canary(
        operational_catalog=d116._catalog(private),
        tree=tree,
        work_root=work_root,
        run_id=run_id,
        source_instance_id=_BULK_INSTANCE,
        cache_bytes=cache_bytes,
    )
    return result, private, canary.CanaryWorld(run_id=run_id, directory=work_root / run_id)


def _sidecar_count(path: Path, table: str) -> int:
    connection = sqlite3.connect(f"{path.absolute().as_uri()}?mode=ro", uri=True)
    try:
        return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])  # noqa: S608
    finally:
        connection.close()


def _member_ordinals(path: Path) -> list[int]:
    connection = sqlite3.connect(f"{path.absolute().as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT member_ordinal FROM compact_source_members ORDER BY member_ordinal"
        ).fetchall()
    finally:
        connection.close()
    return [int(row[0]) for row in rows]


@pytest.fixture(scope="module")
def prefix_run(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, Path, Any]:
    """One bounded prefix of two members, committed one member at a time.

    ``batch_size=1`` so that every traversed member reaches a commit boundary and the durable
    counts are non-zero. That is not a relaxation of the accepted batch size — the operator
    surface and the library default both stay at :data:`canary.CANARY_BATCH_SIZE` — it is how a
    three-member fixture can say anything at all about what a prefix leaves durable.
    """
    return _prefix(tmp_path_factory.mktemp("d119-prefix"), member_limit=2, batch_size=1)


# ==========================================================================
# Decision 119 §4 (C1): the explicit cache budget, and the exact reach of it
# ==========================================================================
def test_the_accepted_budget_is_512_mebibytes_in_sqlite_negative_form() -> None:
    """Decision 119 §4: the accepted budget, and the one pragma value it must resolve to."""
    assert canary.WORKING_CATALOG_CACHE_BYTES == 512 * 1024 * 1024
    assert canary.WORKING_CATALOG_CACHE_SIZE_PRAGMA == -524288
    assert wc.cache_size_pragma(canary.WORKING_CATALOG_CACHE_BYTES) == -524288


def test_a_working_catalog_without_a_budget_keeps_the_sqlite_default(tmp_path: Path) -> None:
    """Decision 119 §4: an existing caller that asks for nothing gets exactly what it got before."""
    private, _tree, _work = _world(tmp_path)
    with wc.WorkingCatalog(d116._catalog(private), tmp_path / "plain") as working:
        assert working.requested_cache_bytes is None
        assert working.requested_cache_size_pragma is None
        assert working.effective_cache_size_pragma == wc.SQLITE_DEFAULT_CACHE_SIZE_PRAGMA


def test_a_working_catalog_that_asks_reports_the_budget_it_asked_for(tmp_path: Path) -> None:
    """Decision 119 §4: read back from SQLite, not echoed from the argument."""
    private, _tree, _work = _world(tmp_path)
    with wc.WorkingCatalog(
        d116._catalog(private),
        tmp_path / "budgeted",
        cache_bytes=canary.WORKING_CATALOG_CACHE_BYTES,
    ) as working:
        reported = int(working.connection.execute("PRAGMA cache_size").fetchone()[0])
        assert reported == -524288
        assert working.effective_cache_size_pragma == -524288
        assert working.requested_cache_bytes == 512 * 1024 * 1024


def test_the_disposable_canary_requests_the_accepted_budget_by_default() -> None:
    """Decision 119 §4: the D116 path binds the accepted value rather than inheriting a default."""
    for function in (canary.run_single_source_canary, canary.run_single_source_prefix_profile):
        default = inspect.signature(function).parameters["cache_bytes"].default
        assert default == canary.WORKING_CATALOG_CACHE_BYTES


def test_the_canary_path_actually_runs_under_the_accepted_budget(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """Decision 119 §4: the *run's* own connection reports it, not a constructed twin."""
    result, _private, _world_paths = prefix_run
    assert result.working_catalog_cache_bytes == 512 * 1024 * 1024
    assert result.working_catalog_cache_size_pragma == -524288
    assert result.working_catalog_effective_cache_size_pragma == -524288


def test_an_unrepresentable_cache_budget_is_refused(tmp_path: Path) -> None:
    """A budget SQLite's kibibyte form cannot state exactly is refused, never rounded."""
    for budget in (0, -1, 1023, 1025):
        with pytest.raises(wc.WorkingCatalogError):
            wc.cache_size_pragma(budget)
    private, _tree, _work = _world(tmp_path)
    with pytest.raises(wc.WorkingCatalogError):
        wc.WorkingCatalog(d116._catalog(private), tmp_path / "bad", cache_bytes=1500)
    # Refused at construction, so nothing was created to leave behind.
    assert not (tmp_path / "bad").exists()


def test_the_accepted_catalog_connection_receives_no_cache_mutation(tmp_path: Path) -> None:
    """Decision 119 §4: the budget reaches the run-local writable copy and nothing else."""
    result, private, _world_paths = _prefix(tmp_path, member_limit=1)
    assert result.working_catalog_effective_cache_size_pragma == -524288
    accepted = d116._catalog(private)
    with strictly_read_only_connection(accepted) as reader:
        assert int(reader.execute("PRAGMA cache_size").fetchone()[0]) == -2000
    with connect(accepted, read_only=True) as reader:
        assert int(reader.execute("PRAGMA cache_size").fetchone()[0]) == -2000


def test_the_shared_connection_helper_configures_no_cache_at_all() -> None:
    """The budget is opt-in on one class; no global default moved to make it possible."""
    source = Path(storage_sqlite.__file__).read_text(encoding="utf-8")
    assert "cache_size" not in source


def test_the_working_catalog_configures_no_performance_pragma_but_the_cache() -> None:
    """Decision 119 §4: C1 is the only performance behaviour this module changed.

    Asserted on the pragma names the module assigns, so a later edit that reached for
    ``mmap_size``, ``cache_spill``, ``page_size``, or a different ``synchronous`` fails here
    rather than being noticed in a review.
    """
    source = Path(wc.__file__).read_text(encoding="utf-8")
    assigned = set(re.findall(r"PRAGMA (\w+)\s*=", source))
    assert assigned == {"journal_mode", "synchronous", "cache_size"}


def test_the_accepted_batch_size_and_checkpoint_cadence_are_unchanged() -> None:
    """Decision 119 §4, restated as a pin: the cache is the only knob that moved."""
    assert canary.CANARY_BATCH_SIZE == 250
    prefix = inspect.signature(canary.run_single_source_prefix_profile).parameters
    assert prefix["batch_size"].default == canary.CANARY_BATCH_SIZE
    complete = inspect.signature(canary.run_single_source_canary).parameters
    assert complete["batch_size"].default == canary.CANARY_BATCH_SIZE


def test_the_preflight_reports_the_requested_budget_and_creates_nothing(tmp_path: Path) -> None:
    """Decision 119 §4: deterministic read-only verification, before anything exists."""
    private, _tree, work_root = _world(tmp_path)
    report = canary.preflight_single_source_canary(
        operational_catalog=d116._catalog(private),
        work_root=work_root,
        run_id="preflight-1",
        source_instance_id=_BULK_INSTANCE,
    )
    record = report.as_record()
    assert record["working_catalog_cache_bytes"] == 512 * 1024 * 1024
    assert record["working_catalog_cache_size_pragma"] == -524288
    assert report.world_absent
    assert not (work_root / "preflight-1").exists()


# ==========================================================================
# Decision 119 §4: the budget moves no row, no ordering, and no digest
# ==========================================================================
def test_two_canaries_differing_only_in_cache_budget_reach_identical_evidence(
    tmp_path: Path,
) -> None:
    """Decision 119 §4: the semantic output of the two runs is required to be equal, not similar.

    Two runs over the **same** accepted catalog into two separate disposable worlds — one under
    SQLite's own default cache and one under the accepted 512 MiB budget. One catalog rather
    than two, so that everything but the budget is held fixed and the whole result record can be
    compared rather than only its digests. A budget that had reached anything but memory would
    move at least one of the five identities, one of the durable counts, or one of the rows they
    summarize.
    """
    private = d116._private_root(tmp_path)
    accepted = d116._catalog(private)
    tree = DataTree.from_root(private)
    runs = []
    for label, budget in (("default", None), ("budgeted", canary.WORKING_CATALOG_CACHE_BYTES)):
        work_root = tmp_path / f"work-{label}"
        runs.append(
            (
                canary.run_single_source_canary(
                    operational_catalog=accepted,
                    tree=tree,
                    work_root=work_root,
                    run_id=f"{label}-1",
                    source_instance_id=_BULK_INSTANCE,
                    cache_bytes=budget,
                ),
                canary.CanaryWorld(run_id=f"{label}-1", directory=work_root / f"{label}-1"),
            )
        )
    (default_run, default_world), (budgeted, budgeted_world) = runs
    assert default_run.identities() == budgeted.identities()
    assert default_run.member_manifest_digest
    assert default_run.projection_digest
    assert default_run.resolution_digest
    assert default_run.compact_evidence_identity
    # Everything a wall clock, a filesystem, or the world's own name decides. The working
    # catalog's file digest is here because its rows carry `utc_now()` timestamps, so two runs
    # a millisecond apart produce different bytes carrying identical governed content — which
    # is exactly what the identities below assert and this digest cannot.
    volatile = {
        "run_id",
        "started_at_utc",
        "completed_at_utc",
        "working_catalog_sha256",
        "work_root_free_bytes_before",
        "work_root_free_bytes_after",
    }
    left = {k: v for k, v in default_run.as_record().items() if k not in volatile}
    right = {k: v for k, v in budgeted.as_record().items() if k not in volatile}
    assert left == right
    # And the durable rows agree, which is what makes the digest equality informative.
    for table in ("census_accessions", "census_parsed_records", "census_accession_observations"):
        query = f"SELECT COUNT(*) AS n FROM {table}"  # noqa: S608
        assert d116._count(default_world.working_catalog, query) == d116._count(
            budgeted_world.working_catalog, query
        )


def test_the_cache_budget_is_not_part_of_any_accepted_identity(tmp_path: Path) -> None:
    """Decision 119 §4: an execution parameter never enters evidence semantics."""
    result, _private, world_paths = _canary(
        tmp_path, run_id="identity-1", cache_bytes=canary.WORKING_CATALOG_CACHE_BYTES
    )
    record = result.as_record()
    assert "working_catalog_cache_bytes" not in record
    assert "working_catalog_cache_size_pragma" not in record
    document = world_paths.result.read_text(encoding="utf-8")
    assert "cache_size" not in document


# ==========================================================================
# Decision 119 §6: the prefix bound belongs to exactly one mode
# ==========================================================================
@pytest.mark.parametrize("limit", [0, -1, -250])
def test_a_non_positive_member_limit_is_refused(tmp_path: Path, limit: int) -> None:
    """Decision 119 §6: zero and negative bounds refuse rather than meaning 'every member'."""
    private, tree, work_root = _world(tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError, match="positive"):
        canary.run_single_source_prefix_profile(
            operational_catalog=d116._catalog(private),
            tree=tree,
            work_root=work_root,
            run_id="refused-1",
            source_instance_id=_BULK_INSTANCE,
            member_limit=limit,
        )
    assert not (work_root / "refused-1").exists()


def test_the_operator_surface_requires_a_positive_bound_for_a_prefix(tmp_path: Path) -> None:
    """Decision 119 §6: ``profile-prefix`` requires the bound, validated before anything runs."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    for limit in (None, 0, -3):
        with pytest.raises(canary.SingleSourceCanaryError, match="member-limit"):
            canary.run_canary_source_command(
                mode="profile-prefix",
                run_id="p-1",
                source_instance_id=_BULK_INSTANCE,
                work_root=str(tmp_path / "work"),
                repository_root=checkout,
                environ={},
                member_limit=limit,
            )


@pytest.mark.parametrize("mode", ["run", "preflight"])
def test_the_production_modes_reject_a_member_limit(tmp_path: Path, mode: str) -> None:
    """Decision 119 §6: ``run`` is complete-source-only and must refuse a bound, not ignore one."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match="no --member-limit"):
        canary.run_canary_source_command(
            mode=mode,
            run_id="r-1",
            source_instance_id=_BULK_INSTANCE,
            work_root=str(tmp_path / "work"),
            repository_root=checkout,
            environ={},
            member_limit=1,
        )


def test_the_complete_source_entry_point_has_no_member_cap() -> None:
    """Decision 119 §6: the production path uses ``None`` because it can express nothing else."""
    assert "max_members" not in inspect.signature(op.materialize_one_planned_source).parameters
    assert inspect.signature(op._stream_bulk_submissions).parameters["max_members"].default is None
    source = Path(canary.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    complete = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "run_single_source_canary"
    )
    called = {
        node.func.id
        for node in ast.walk(complete)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "materialize_planned_source_prefix" not in called
    assert "run_single_source_prefix_profile" not in called


# ==========================================================================
# Decision 119 §6: exactly N deterministic governed members, and nothing after them
# ==========================================================================
@pytest.mark.parametrize("limit", [1, 2, 3])
def test_a_prefix_traverses_exactly_the_first_n_members(tmp_path: Path, limit: int) -> None:
    """Decision 119 §6: exactly ``N`` members, and their ordinals are exactly ``0 .. N-1``."""
    result, _private, world_paths = _prefix(tmp_path, member_limit=limit, batch_size=1)
    assert result.requested_member_limit == limit
    assert result.members_processed == limit
    assert result.recorded_member_count == limit
    assert _member_ordinals(world_paths.sidecar) == list(range(limit))
    assert result.member_ordinal_first == 0
    assert result.member_ordinal_last == limit - 1
    assert result.member_payload_byte_length > 0


def test_a_prefix_longer_than_the_archive_stops_at_the_archive(tmp_path: Path) -> None:
    """A bound the artifact cannot satisfy is reported truthfully, never rounded up or down."""
    result, _private, _world_paths = _prefix(tmp_path, member_limit=99, batch_size=1)
    assert result.requested_member_limit == 99
    assert result.members_processed == _ARCHIVE_MEMBERS
    assert result.classification == op.DIAGNOSTIC_PREFIX_CLASSIFICATION


def test_a_prefix_whose_bound_is_the_whole_archive_is_still_diagnostic(tmp_path: Path) -> None:
    """Decision 119 §6: ``prefix N == complete member count`` must not silently become a canary."""
    result, _private, world_paths = _prefix(tmp_path, member_limit=_ARCHIVE_MEMBERS, batch_size=1)
    assert result.members_processed == _ARCHIVE_MEMBERS
    assert result.classification == "INCOMPLETE_DIAGNOSTIC_PREFIX"
    assert result.source_finalized is False
    assert result.parser_state_after == result.parser_state_before == "not_started"
    assert _sidecar_count(world_paths.sidecar, "compact_source_evidence") == 0
    assert not world_paths.result.exists()


def test_a_prefix_reaches_no_source_disposition(prefix_run: tuple[Any, Path, Any]) -> None:
    """Decision 119 §6: no terminal, in the plan row, in the ledger, or in the parser run."""
    result, _private, world_paths = prefix_run
    assert result.source_finalized is False
    assert result.parser_state_before == "not_started"
    assert result.parser_state_after == "not_started"
    assert result.run_local_progress_state == "in_progress"
    assert result.durable_parser_runs_claiming_completion == 0
    assert result.durable_parser_run_count >= 1
    with connect(world_paths.working_catalog, writer=False) as connection:
        outcomes = {
            str(row["outcome"])
            for row in connection.execute("SELECT outcome FROM census_parser_runs")
        }
    assert outcomes == {"failed"}


def test_a_prefix_leaves_the_committed_batches_durable(prefix_run: tuple[Any, Path, Any]) -> None:
    """Progress is real: the accepted batch semantics made the traversed members durable."""
    result, _private, world_paths = prefix_run
    assert result.durable_canonical_accession_count > 0
    assert result.durable_parsed_record_count > 0
    assert result.parsed_accession_count > 0
    assert (
        d116._count(world_paths.working_catalog, "SELECT COUNT(*) AS n FROM census_accessions")
        == result.durable_canonical_accession_count
    )


def test_a_prefix_runs_no_resolution_and_no_association_pass(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """Decision 119 §6: the phases of a whole run are unreachable from a prefix."""
    _result, _private, world_paths = prefix_run
    working = world_paths.working_catalog
    for table in (
        "census_accession_field_resolutions",
        "census_accession_cohort_resolutions",
        "census_accession_registrants",
    ):
        query = f"SELECT COUNT(*) AS n FROM {table}"  # noqa: S608
        assert d116._count(working, query) == 0
    assert _sidecar_count(world_paths.sidecar, "compact_resolution_evidence") == 0
    assert _sidecar_count(world_paths.sidecar, "compact_corroboration_evidence") == 0


def test_a_prefix_emits_no_complete_source_identity(prefix_run: tuple[Any, Path, Any]) -> None:
    """Decision 119 §6: none of the five accepted identities exists to be mistaken for one."""
    result, _private, world_paths = prefix_run
    record = result.as_record()
    for absent in (
        "member_manifest_digest",
        "projection_digest",
        "resolution_digest",
        "corroboration_digest",
        "compact_evidence_identity",
        "disposition",
    ):
        assert absent not in record, absent
    assert not hasattr(result, "compact_evidence_identity")
    assert _sidecar_count(world_paths.sidecar, "compact_source_evidence") == 0
    document = json.loads(world_paths.prefix_result.read_text(encoding="utf-8"))
    assert "compact_evidence_identity" not in document
    assert document["classification"] == "INCOMPLETE_DIAGNOSTIC_PREFIX"


def test_a_prefix_writes_its_own_document_and_never_the_canary_one(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """Decision 119 §6: a world holding a prefix result holds no canary result."""
    _result, _private, world_paths = prefix_run
    assert world_paths.prefix_result.is_file()
    assert not world_paths.result.exists()
    assert canary.CANARY_PREFIX_RESULT_FILENAME != canary.CANARY_RESULT_FILENAME


def test_the_second_planned_source_is_unreachable_from_a_prefix(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """Decision 119 §6: source 2 is untouched, asserted on durable state rather than a log."""
    _result, _private, world_paths = prefix_run
    working = world_paths.working_catalog
    assert (
        d116._count(
            working,
            "SELECT COUNT(*) AS n FROM census_parser_runs WHERE source_observation_id = ?",
            d112._INDEX_OBSERVATION,
        )
        == 0
    )
    with connect(working, writer=False) as connection:
        states = {
            str(row["source_instance_id"]): str(row["parser_state"])
            for row in connection.execute(
                "SELECT source_instance_id, parser_state FROM census_plan_sources"
            )
        }
    assert states == {_BULK_INSTANCE: "not_started", _INDEX_INSTANCE: "not_started"}


def test_a_source_with_one_indivisible_member_refuses_a_prefix(tmp_path: Path) -> None:
    """Decision 119 §6: a prefix bounds a member ordering; a single-payload source has none."""
    private, tree, work_root = _world(tmp_path)
    with pytest.raises(op.OfflineParseError, match="indivisible"):
        canary.run_single_source_prefix_profile(
            operational_catalog=d116._catalog(private),
            tree=tree,
            work_root=work_root,
            run_id="single-1",
            source_instance_id=_INDEX_INSTANCE,
            member_limit=1,
        )


# ==========================================================================
# Decision 119 §7: create-once, disposable, and fail-closed
# ==========================================================================
def test_a_duplicate_world_identity_is_refused_for_a_prefix(tmp_path: Path) -> None:
    """A prefix world is create-once: an identity that has one is refused, never resumed."""
    private, tree, work_root = _world(tmp_path)
    kwargs: dict[str, Any] = {
        "operational_catalog": d116._catalog(private),
        "tree": tree,
        "work_root": work_root,
        "run_id": "once-1",
        "source_instance_id": _BULK_INSTANCE,
        "member_limit": 1,
        "batch_size": 1,
    }
    first = canary.run_single_source_prefix_profile(**kwargs)
    assert first.members_processed == 1
    with pytest.raises(canary.SingleSourceCanaryError, match="create-once"):
        canary.run_single_source_prefix_profile(**kwargs)


def test_a_work_root_inside_the_private_evidence_root_is_refused_for_a_prefix(
    tmp_path: Path,
) -> None:
    """Decision 119 §7: private evidence is never a writable target, refused by the run itself."""
    private, tree, _work = _world(tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError):
        canary.run_single_source_prefix_profile(
            operational_catalog=d116._catalog(private),
            tree=tree,
            work_root=private / "inside",
            run_id="inside-1",
            source_instance_id=_BULK_INSTANCE,
            member_limit=1,
        )
    assert not (private / "inside").exists()


def test_the_operational_catalog_is_byte_identical_after_a_prefix(tmp_path: Path) -> None:
    """The authoritative input is read-only here exactly as it is for a complete canary."""
    before = None
    private, tree, work_root = _world(tmp_path)
    accepted = d116._catalog(private)
    before = wc.file_digest(accepted)
    result = canary.run_single_source_prefix_profile(
        operational_catalog=accepted,
        tree=tree,
        work_root=work_root,
        run_id="readonly-1",
        source_instance_id=_BULK_INSTANCE,
        member_limit=2,
        batch_size=1,
    )
    assert result.operational_catalog_unchanged
    assert wc.file_digest(accepted) == before
    assert d116._count(accepted, "SELECT COUNT(*) AS n FROM census_accessions") == 0
    assert d116._count(accepted, "SELECT COUNT(*) AS n FROM census_parser_runs") == 0


def test_a_prefix_result_document_carries_no_absolute_path(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """No world path, work root, or stand-in private root reaches the result document."""
    _result, private, world_paths = prefix_run
    document = world_paths.prefix_result.read_text(encoding="utf-8")
    for absolute in (str(private), str(world_paths.directory), str(world_paths.directory.parent)):
        assert absolute not in document
    assert document.count(canary.WORKING_CATALOG_FILENAME) == 1


def test_completed_prefix_evidence_is_never_overwritten(
    prefix_run: tuple[Any, Path, Any],
) -> None:
    """The result document is write-once at the operating system, not by a prior check."""
    _result, _private, world_paths = prefix_run
    with pytest.raises(canary.SingleSourceCanaryError, match="never overwritten"):
        canary._write_once(world_paths.prefix_result, b"{}")


# ==========================================================================
# The operator surface
# ==========================================================================
def test_the_operator_surface_runs_a_prefix_end_to_end(tmp_path: Path) -> None:
    """One invocation, rendered leak-free, classified as a diagnostic prefix."""
    private = d116._private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    work_root = tmp_path / "work"
    outcome = canary.run_canary_source_command(
        mode="profile-prefix",
        run_id="operator-1",
        source_instance_id=_BULK_INSTANCE,
        work_root=str(work_root),
        repository_root=checkout,
        environ={canary.EVIDENCE_ROOT_ENV: str(private)},
        member_limit=1,
    )
    assert outcome.exit_code == 0
    rendered = "\n".join(outcome.lines)
    assert "canary-source profile-prefix" in rendered
    assert "INCOMPLETE_DIAGNOSTIC_PREFIX" in rendered
    assert str(private) not in rendered
    assert str(work_root) not in rendered
    assert (work_root / "operator-1" / canary.CANARY_PREFIX_RESULT_FILENAME).is_file()
    assert not (work_root / "operator-1" / canary.CANARY_RESULT_FILENAME).exists()


def test_an_unknown_mode_still_names_every_mode_that_exists(tmp_path: Path) -> None:
    """The refusal enumerates the three modes, so it cannot go stale silently."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    private = d116._private_root(tmp_path)
    with pytest.raises(canary.SingleSourceCanaryError, match="profile-prefix"):
        canary.run_canary_source_command(
            mode="execute",
            run_id="unknown-1",
            source_instance_id=_BULK_INSTANCE,
            work_root=str(tmp_path / "work"),
            repository_root=checkout,
            environ={canary.EVIDENCE_ROOT_ENV: str(private)},
        )
