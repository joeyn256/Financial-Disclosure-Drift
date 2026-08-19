"""The accepted Decision 116 disposable single-source compact canary execution path.

Decision 115 stopped before creating a disposable world because no supported path could run
exactly one governed source under the accepted compact contract and be relied on to stop. The
reachable production driver loads the whole plan, traverses every planned source, defaults to
full evidence, and wires no Decision 112 §8 sidecar. This module holds the proofs for the path
that closes that gap.

Five claims carry it, and each is proved against a world built to break it:

**One source.** The requested plan row runs, the *other* planned row is not touched, an
identifier outside the accepted plan is refused, an ambiguous identifier is refused, and no
all-source fallback exists to be reached by accident.

**Disposable isolation.** The accepted operational catalog is byte-identical after a run, its
rows are still absent, every write landed in the working catalog, nothing is promoted, and a
work root that is, contains, or lies inside the private evidence root is refused before
anything is created.

**The compact contract, bound explicitly.** The sidecar exists, states
``e0-compact-evidence/2``, and carries the member manifest, the source evidence, the resolution
evidence, and the corroboration evidence. The full-observation default is not merely absent by
inspection: the same one source run under the full contract writes materially more observation
rows and the identical canonical accession set.

**Determinism.** Two independently built worlds -- separate archives on disk, separate
catalogs, separate work roots, separate identifiers -- reach identical member-manifest,
projection, resolution, corroboration, and compact-evidence identities.

**Fail-closed.** A duplicate world identity is refused, a populated world is never adopted,
completed run-local evidence is never overwritten, and a failure leaves the accepted catalog
unchanged.

Everything runs over the hostile Decision 112 synthetic world beneath ``tmp_path``. No test
resolves, opens, names, or infers the accepted private evidence root, none reads a real SEC
artifact, none touches a real catalog, and none runs a real source.
"""

from __future__ import annotations

import ast
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import test_d110_bounded_parse_memory as world  # noqa: E402
import test_d112_compact_evidence as d112  # noqa: E402

from disclosure_drift.config import EVIDENCE_ROOT_ENV  # noqa: E402
from disclosure_drift.m3 import single_source_canary as canary  # noqa: E402
from disclosure_drift.m3.compact_evidence import (  # noqa: E402
    COMPACT_EVIDENCE,
    COMPACT_EVIDENCE_CONTRACT,
    COMPACT_EVIDENCE_SCHEMA_VERSION,
    FULL_EVIDENCE,
    CompactEvidenceSidecar,
)
from disclosure_drift.m3.offline_parse import (  # noqa: E402
    OfflineParseError,
    materialize_one_planned_source,
    select_planned_source,
)
from disclosure_drift.m3.working_catalog import WorkingCatalog, file_digest  # noqa: E402
from disclosure_drift.paths import DataTree  # noqa: E402
from disclosure_drift.sec.census import CensusCatalog  # noqa: E402
from disclosure_drift.storage.sqlite import connect, transaction  # noqa: E402

_BULK_INSTANCE = world._INSTANCE
_INDEX_INSTANCE = d112._INDEX_INSTANCE


# ==========================================================================
# The world: a stand-in private root carrying two planned sources
# ==========================================================================
def _private_root(root: Path) -> Path:
    """A disposable stand-in for the accepted private evidence root.

    Identical content to the Decision 112 world -- one hostile bulk archive and one
    ``company.idx`` quarter -- placed at the fixed relative paths the canary expects, so the
    operator surface can be exercised end to end without naming or touching a real root.
    """
    private = root / "private"
    tree = DataTree.from_root(private)
    database = private / canary.OPERATIONAL_CATALOG_RELATIVE_PATH
    database.parent.mkdir(parents=True, exist_ok=True)
    raw = d112._write_bulk_archive(tree.data_root / world._ARCHIVE_RELATIVE)
    world._seed_catalog(database, tree, raw)
    d112._seed_index_source(
        database, d112._write_company_index(tree.data_root / d112._INDEX_RELATIVE)
    )
    return private


def _catalog(private: Path) -> Path:
    return private / canary.OPERATIONAL_CATALOG_RELATIVE_PATH


def _prime_bulk(private: Path) -> None:
    """Parse the bulk source into the stand-in catalog, under the compact contract.

    A precondition, not a canary step: the ``company.idx`` quarter can only corroborate an
    accession the submissions layer has already established, so a canary over the index alone
    would exercise nothing but the unbound branch. Built from the same accepted calls the D112
    proofs use, never from the path under test.

    Deliberately **parse only**. Decision 094 §6.4 makes the resolution pass and the
    association projection phases of a whole run rather than of a source, and E0 runs each
    exactly once after every category-A parse; a fixture that ran them here would leave the
    catalog in a state no real sequence reaches, and the canary's own single projection would
    then meet a create-once relation row it did not write.
    """
    database = _catalog(private)
    tree = DataTree.from_root(private)
    from disclosure_drift.m3 import offline_parse as op
    from disclosure_drift.sec.observation_catalog import load_observations
    from disclosure_drift.sec.source_registry import SOURCES

    store = op.SnapshotStore(tree)
    with connect(database, writer=True) as connection:
        store.adopt(load_observations(connection))
        observation = op._observations_by_id(connection)[world._OBSERVATION]
        catalog = CensusCatalog(d112._StubWriter(connection), compact_evidence=COMPACT_EVIDENCE)  # type: ignore[arg-type]
        catalog.persist_streamed(
            op._stream_bulk_submissions(store, observation),
            parser_id=op._BULK_PARSER_ID,
            parser_version=SOURCES[d112._BULK].parser_version,
            source_observation_id=observation.observation_id,
        )
        with transaction(connection) as active:
            active.execute(
                "UPDATE census_plan_sources SET parser_state = 'completed' "
                "WHERE source_instance_id = ?",
                (_BULK_INSTANCE,),
            )


def _run(
    root: Path, *, instance: str = _BULK_INSTANCE, run_id: str = "canary-1", prime: bool = False
) -> tuple[canary.CanaryResult, Path, canary.CanaryWorld]:
    """Build a world, run the canary over exactly one source, and return everything measured."""
    private = _private_root(root)
    if prime:
        _prime_bulk(private)
    work_root = root / "work"
    result = canary.run_single_source_canary(
        operational_catalog=_catalog(private),
        tree=DataTree.from_root(private),
        work_root=work_root,
        run_id=run_id,
        source_instance_id=instance,
    )
    return result, private, canary.CanaryWorld(run_id=run_id, directory=work_root / run_id)


@pytest.fixture(scope="module")
def bulk_run(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, Path, Any]:
    """One canary over the bulk source. Module-scoped: the run is pure and never mutates input."""
    return _run(tmp_path_factory.mktemp("d116-bulk"))


@pytest.fixture(scope="module")
def index_run(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, Path, Any]:
    """One canary over the ``company.idx`` quarter, with the submissions layer already present."""
    return _run(tmp_path_factory.mktemp("d116-index"), instance=_INDEX_INSTANCE, prime=True)


def _count(database: Path, sql: str, *parameters: object) -> int:
    with connect(database, writer=False) as connection:
        return int(connection.execute(sql, parameters).fetchone()["n"])


# ==========================================================================
# Section 5 items 1-3, 9-10: exactly one source, and it is the requested one
# ==========================================================================
def test_the_requested_plan_source_is_the_one_that_runs(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§5 items 1-2: the selector is the plan's own key, and it resolves through the plan."""
    result, _private, world_paths = bulk_run
    assert result.source_instance_id == _BULK_INSTANCE
    assert result.source_id == "sec_bulk_submissions"
    assert result.source_observation_id == world._OBSERVATION
    assert result.disposition == "E0_REQUIRED_PARSE"
    assert result.parser_state_before == "not_started"
    assert result.parser_state_after in {"completed", "quarantined"}
    assert result.parsed_records > 0
    assert result.plan_position >= 1
    assert result.plan_source_count == 2
    assert (
        _count(
            world_paths.working_catalog,
            "SELECT COUNT(*) AS n FROM census_parser_runs WHERE source_observation_id = ?",
            world._OBSERVATION,
        )
        == 1
    )


def test_the_second_planned_source_is_not_touched(bulk_run: tuple[Any, Path, Any]) -> None:
    """§5 items 9-10: one invocation is one source, and there is no continuation to a second.

    Asserted on the *other* row's durable state rather than on a log line: a driver that
    continued would have written a parser run for the index observation and moved its
    ``parser_state``, and neither happened.
    """
    _result, _private, world_paths = bulk_run
    working = world_paths.working_catalog
    assert (
        _count(
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
    assert states[_INDEX_INSTANCE] == "not_started"
    assert states[_BULK_INSTANCE] != "not_started"


def test_a_source_outside_the_accepted_plan_is_refused(tmp_path: Path) -> None:
    """§5 item 3: an identifier the plan does not carry is refused, and no world is created."""
    private = _private_root(tmp_path)
    work_root = tmp_path / "work"
    with pytest.raises(OfflineParseError, match="no planned source carries source_instance_id"):
        canary.run_single_source_canary(
            operational_catalog=_catalog(private),
            tree=DataTree.from_root(private),
            work_root=work_root,
            run_id="refused",
            source_instance_id="base|not_a_planned_source|9",
        )
    assert not (work_root / "refused").exists()


def test_a_path_shaped_identifier_is_refused_like_any_other_non_plan_value(
    tmp_path: Path,
) -> None:
    """§5 item 3: there is no path argument, so a path is simply not a planned identifier."""
    private = _private_root(tmp_path)
    with pytest.raises(OfflineParseError, match="no planned source carries source_instance_id"):
        canary.run_single_source_canary(
            operational_catalog=_catalog(private),
            tree=DataTree.from_root(private),
            work_root=tmp_path / "work",
            run_id="refused",
            source_instance_id=str(private / world._ARCHIVE_RELATIVE),
        )


def test_an_ambiguous_plan_identifier_is_refused(tmp_path: Path) -> None:
    """§5 item 1: 'exactly one' is checked, not assumed, so a repeated key fails closed."""
    private = _private_root(tmp_path)
    database = _catalog(private)
    with connect(database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('job-census-2', 'sec_census', 'completed', "
            "'M2.2', ?, '')",
            (world._AT,),
        )
        active.execute(
            "INSERT INTO census_plan_sources (census_run_id, source_instance_id, source_id, "
            "request_identity, required, source_scope, retrieval_state, snapshot_state, "
            "parser_state, catalog_state, qa_state, unresolved_blocking_reasons_json, "
            "observation_id, successful_terminal, updated_at_utc) VALUES ('job-census-2', ?, "
            "'sec_bulk_submissions', 'req/bulk/1', 1, 'base', 'retrieved', 'verified', "
            "'not_started', 'committed', 'passed', '[]', ?, 1, ?)",
            (_BULK_INSTANCE, world._OBSERVATION, world._AT),
        )
    with pytest.raises(OfflineParseError, match="names 2 planned rows"):
        canary.run_single_source_canary(
            operational_catalog=database,
            tree=DataTree.from_root(private),
            work_root=tmp_path / "work",
            run_id="ambiguous",
            source_instance_id=_BULK_INSTANCE,
        )


def test_no_all_source_fallback_is_reachable_from_the_canary_path() -> None:
    """§5 item 10: the whole-plan driver is not named anywhere in the canary module.

    A structural check rather than a behavioural one, because the failure it guards against is
    a *future* edit that reaches for the convenient whole-plan entry point. Both names are
    exported by the same module the canary already imports, so nothing but this stops one from
    being called.
    """
    source = Path(canary.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    for forbidden in (
        "run_offline_metadata_parse",
        "materialize_source_layer",
        "load_planned_sources",
        "promote_working_catalog",
    ):
        assert forbidden not in names, f"the canary path reaches for {forbidden}"


# ==========================================================================
# Section 7: the disposable world, and what stays authoritative
# ==========================================================================
def test_the_operational_catalog_is_byte_identical_after_a_run(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§7: the authoritative input is read-only, measured on its own bytes."""
    result, private, _world_paths = bulk_run
    assert result.operational_catalog_sha256_before == result.operational_catalog_sha256_after
    assert result.operational_catalog_unchanged
    assert file_digest(_catalog(private))[0] == result.operational_catalog_sha256_after


def test_every_write_landed_in_the_working_catalog_and_none_in_the_accepted_one(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§7: the separation is the point, and it is asserted on rows in both files."""
    result, private, world_paths = bulk_run
    assert world_paths.working_catalog != _catalog(private)
    assert (
        _count(world_paths.working_catalog, "SELECT COUNT(*) AS n FROM census_parsed_records")
        == result.parsed_records
        > 0
    )
    assert _count(_catalog(private), "SELECT COUNT(*) AS n FROM census_parsed_records") == 0
    assert _count(_catalog(private), "SELECT COUNT(*) AS n FROM census_accessions") == 0


def test_the_working_catalog_records_the_accepted_catalog_it_descends_from(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§9: the working catalog's identity names the artifact it was copied from."""
    result, private, _world_paths = bulk_run
    assert result.working_catalog_source_sha256 == result.operational_catalog_sha256_before
    assert result.working_catalog_source_sha256 == file_digest(_catalog(private))[0]
    assert result.migration_head == 15
    assert result.working_catalog_byte_length > 0


def test_a_work_root_inside_the_private_evidence_root_is_refused(tmp_path: Path) -> None:
    """§7: no writable canary output lands inside the authoritative evidence tree."""
    private = tmp_path / "private"
    private.mkdir()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match="lies inside it"):
        canary.require_disposable_work_root(private / "work", checkout, private)
    with pytest.raises(canary.SingleSourceCanaryError, match="private evidence root"):
        canary.require_disposable_work_root(private, checkout, private)


def test_a_work_root_that_contains_the_private_evidence_root_is_refused(tmp_path: Path) -> None:
    """§7: nor may the authoritative tree end up inside a disposable work tree."""
    private = tmp_path / "outer" / "private"
    private.mkdir(parents=True)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match="contains the private evidence root"):
        canary.require_disposable_work_root(tmp_path / "outer", checkout, private)


def test_a_work_root_inside_the_repository_checkout_is_refused(tmp_path: Path) -> None:
    """§7: the accepted external-root boundary is reused rather than restated."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    private = tmp_path / "private"
    private.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match="not a lawful external directory"):
        canary.require_disposable_work_root(checkout / "work", checkout, private)
    with pytest.raises(canary.SingleSourceCanaryError, match="not a lawful external directory"):
        canary.require_disposable_work_root("relative/work", checkout, private)


def test_a_lawful_work_root_resolves(tmp_path: Path) -> None:
    """The boundary refuses rather than defaults, so the passing case is asserted too."""
    checkout = tmp_path / "checkout"
    private = tmp_path / "private"
    work = tmp_path / "work"
    for path in (checkout, private, work):
        path.mkdir()
    assert canary.require_disposable_work_root(work, checkout, private).name == "work"


# ==========================================================================
# Section 8: the compact contract, bound explicitly rather than inherited
# ==========================================================================
def test_the_accepted_compact_contract_is_what_the_sidecar_records(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§8: the run states which contract it ran under, and it is ``e0-compact-evidence/2``."""
    result, _private, world_paths = bulk_run
    assert result.evidence_contract == COMPACT_EVIDENCE_CONTRACT == "e0-compact-evidence/2"
    assert world_paths.sidecar.is_file()
    sidecar = CompactEvidenceSidecar(world_paths.sidecar)
    try:
        evidence = sidecar.source_evidence(world._OBSERVATION)
        assert evidence is not None
        assert evidence["contract"] == COMPACT_EVIDENCE_CONTRACT
        assert evidence["schema_version"] == COMPACT_EVIDENCE_SCHEMA_VERSION
        assert int(evidence["members"]) == result.members > 0
        assert evidence["completeness_digest"] == result.projection_digest
        members = sidecar.members(world._OBSERVATION)
        assert len(members) == result.members
        assert [int(row["member_ordinal"]) for row in members] == list(range(result.members))
        resolution = sidecar.resolution_evidence(canary.CANARY_RESOLUTION_SCOPE)
        assert resolution is not None
        assert resolution["completeness_digest"] == result.resolution_digest
    finally:
        sidecar.close()


def test_the_full_observation_default_is_not_what_ran(bulk_run: tuple[Any, Path, Any]) -> None:
    """§8 and §5 item 7: proved by comparison, not by reading the call site.

    The same one source is materialized again through the same accepted entry point under the
    **full** contract. The canonical accession set is identical and the raw observation layer is
    materially larger, which is exactly the compaction -- so a canary that had silently taken
    the full default could not produce the row counts it did.
    """
    result, private, _world_paths = bulk_run
    reference = private.parent / "full-reference"
    reference_private = _private_root(reference)
    with WorkingCatalog(_catalog(reference_private), reference / "run") as working:
        selected = select_planned_source(working.connection, _BULK_INSTANCE)
        catalog = CensusCatalog(
            canary._WorkingCatalogWriter(working), compact_evidence=FULL_EVIDENCE
        )
        materialize_one_planned_source(
            writer=canary._WorkingCatalogWriter(working),
            tree=DataTree.from_root(reference_private),
            catalog=catalog,
            selected=selected,
        )
        catalog.count_persisted_accession_resolutions()
        full_observations = int(
            working.connection.execute(
                "SELECT COUNT(*) AS n FROM census_accession_observations"
            ).fetchone()["n"]
        )
        full_accessions = int(
            working.connection.execute("SELECT COUNT(*) AS n FROM census_accessions").fetchone()[
                "n"
            ]
        )
        full_field_rows = int(
            working.connection.execute(
                "SELECT COUNT(*) AS n FROM census_accession_field_resolutions"
            ).fetchone()["n"]
        )
    assert result.canonical_accession_count == full_accessions > 0
    assert result.accession_observation_count < full_observations
    assert result.field_resolution_row_count < full_field_rows
    assert result.omitted_field_observations > 0
    assert result.implicit_resolutions > 0


def test_every_accepted_digest_type_is_produced(index_run: tuple[Any, Path, Any]) -> None:
    """§9: the five identities a later execution report reads, all present and all bound."""
    result, _private, world_paths = index_run
    identities = result.identities()
    assert set(identities) == {
        "member_manifest_digest",
        "projection_digest",
        "resolution_digest",
        "corroboration_digest",
        "compact_evidence_identity",
    }
    assert all(len(value) == 64 for value in identities.values()), identities
    assert len(set(identities.values())) == len(identities)
    sidecar = CompactEvidenceSidecar(world_paths.sidecar)
    try:
        corroboration = sidecar.corroboration_evidence(d112._INDEX_OBSERVATION)
        assert corroboration is not None
        assert corroboration["corroboration_digest"] == result.corroboration_digest
        assert int(corroboration["index_rows"]) == result.index_rows > 0
        assert int(corroboration["corroborating"]) == result.corroborating_rows > 0
        assert int(corroboration["exceptions"]) == result.corroboration_exceptions > 0
        assert sidecar.identity() == result.compact_evidence_identity
        assert (
            sidecar.member_manifest_digest(d112._INDEX_OBSERVATION) == result.member_manifest_digest
        )
    finally:
        sidecar.close()


def test_a_source_with_no_corroboration_reports_an_empty_digest_rather_than_a_fabricated_one(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§9: a measurement that does not exist is reported absent, never invented."""
    result, _private, _world_paths = bulk_run
    assert result.corroboration_digest == ""
    assert result.index_rows == result.corroborating_rows == result.corroboration_exceptions == 0


def test_a_single_payload_source_is_its_own_member(index_run: tuple[Any, Path, Any]) -> None:
    """§6: the path is not written for the bulk archive alone; one payload is one member."""
    result, _private, world_paths = index_run
    assert result.members == 1
    sidecar = CompactEvidenceSidecar(world_paths.sidecar)
    try:
        members = sidecar.members(d112._INDEX_OBSERVATION)
        assert len(members) == 1
        assert str(members[0]["member_name"]) == d112._INDEX_RELATIVE
        assert int(members[0]["payload_byte_length"]) > 0
    finally:
        sidecar.close()


# ==========================================================================
# Determinism: two independently built worlds, five identical identities
# ==========================================================================
@pytest.mark.parametrize("instance", [_BULK_INSTANCE, _INDEX_INSTANCE])
def test_two_independent_worlds_reach_identical_identities(tmp_path: Path, instance: str) -> None:
    """§13: separate archives, catalogs, work roots, and run identities -- one set of digests.

    An ingredient that was a property of *this* write rather than of the frozen artifact would
    move at least one of the five and fail here. This is fixture-level determinism, and it is
    not a real-source run.
    """
    prime = instance == _INDEX_INSTANCE
    left, _lp, _lw = _run(tmp_path / "left", instance=instance, run_id="left-1", prime=prime)
    right, _rp, _rw = _run(tmp_path / "right", instance=instance, run_id="right-1", prime=prime)
    assert left.run_id != right.run_id
    assert left.identities() == right.identities()
    assert left.projection_digest
    assert left.resolution_digest
    assert left.member_manifest_digest
    # The counts the identities summarize agree too, which is what makes the equality
    # informative rather than a comparison of two empty digests.
    assert left.members == right.members > 0
    assert left.parsed_records == right.parsed_records > 0
    assert left.canonical_accession_count == right.canonical_accession_count


# ==========================================================================
# Section 10: create-once, and what a failure does not do
# ==========================================================================
def test_a_duplicate_world_identity_is_refused(tmp_path: Path) -> None:
    """§10: an identity whose world exists is refused, never resumed or overwritten."""
    private = _private_root(tmp_path)
    work_root = tmp_path / "work"
    canary.run_single_source_canary(
        operational_catalog=_catalog(private),
        tree=DataTree.from_root(private),
        work_root=work_root,
        run_id="once",
        source_instance_id=_BULK_INSTANCE,
    )
    before = file_digest(work_root / "once" / "canary_result.json")[0]
    with pytest.raises(canary.SingleSourceCanaryError, match="create-once"):
        canary.run_single_source_canary(
            operational_catalog=_catalog(private),
            tree=DataTree.from_root(private),
            work_root=work_root,
            run_id="once",
            source_instance_id=_BULK_INSTANCE,
        )
    assert file_digest(work_root / "once" / "canary_result.json")[0] == before


def test_completed_run_local_evidence_is_never_overwritten(tmp_path: Path) -> None:
    """§10: the result document is write-once at the operating system, not by a prior check."""
    target = tmp_path / "canary_result.json"
    canary._write_once(target, b"first")
    with pytest.raises(canary.SingleSourceCanaryError, match="never overwritten"):
        canary._write_once(target, b"second")
    assert target.read_bytes() == b"first"


def test_a_populated_world_is_never_silently_adopted(tmp_path: Path) -> None:
    """§10: two independent refusals, and neither disturbs what the world already holds.

    The world-level create-once refusal fires first, which is why the run is refused at all.
    The accepted D111 refusal is asserted separately and directly, because it is the one that
    would still hold if a future caller ever built the world some other way.
    """
    private = _private_root(tmp_path)
    work_root = tmp_path / "work"
    occupied = canary.create_world(work_root, "occupied")
    occupied.working_catalog.write_bytes(b"not a catalog")
    with pytest.raises(canary.SingleSourceCanaryError, match="already exists"):
        canary.run_single_source_canary(
            operational_catalog=_catalog(private),
            tree=DataTree.from_root(private),
            work_root=work_root,
            run_id="occupied",
            source_instance_id=_BULK_INSTANCE,
        )
    from disclosure_drift.m3.working_catalog import WorkingCatalogError

    with pytest.raises(WorkingCatalogError, match="already exists"):
        WorkingCatalog(_catalog(private), occupied.directory).__enter__()
    assert occupied.working_catalog.read_bytes() == b"not a catalog"


def test_an_unlawful_run_identity_is_refused_before_anything_is_created(tmp_path: Path) -> None:
    """§10: the identity becomes a directory name, so it is validated rather than trusted."""
    for unlawful in ("../escape", "/absolute", "Upper", "with space", ""):
        with pytest.raises(canary.SingleSourceCanaryError, match="not of the accepted shape"):
            canary.validate_run_id(unlawful)
    assert canary.validate_run_id("canary-1") == "canary-1"


def test_a_failed_run_leaves_the_accepted_catalog_unchanged(tmp_path: Path) -> None:
    """§10: a refusal is not a partial write, measured on the accepted catalog's own bytes."""
    private = _private_root(tmp_path)
    database = _catalog(private)
    before = file_digest(database)[0]
    with pytest.raises(OfflineParseError):
        canary.run_single_source_canary(
            operational_catalog=database,
            tree=DataTree.from_root(private),
            work_root=tmp_path / "work",
            run_id="failing",
            source_instance_id="base|absent|1",
        )
    assert file_digest(database)[0] == before


def test_a_missing_accepted_catalog_is_refused(tmp_path: Path) -> None:
    """Nothing is created to stand in for an absent authoritative input."""
    with pytest.raises(canary.SingleSourceCanaryError, match="does not exist"):
        canary.run_single_source_canary(
            operational_catalog=tmp_path / "absent.sqlite3",
            tree=DataTree.from_root(tmp_path),
            work_root=tmp_path / "work",
            run_id="absent",
            source_instance_id=_BULK_INSTANCE,
        )


# ==========================================================================
# Section 5 items 12-14: no E0 authority, no E0 namespace, no network
# ==========================================================================
def test_the_canary_path_imports_no_transport_and_no_e0_module() -> None:
    """§5 items 12-13, proved by import rather than asserted.

    Measured in a clean interpreter and measured as what **this module adds**, because the
    ``disclosure_drift.m3`` package initializer already imports the M3.1/M3.2 acquisition
    stack. ``disclosure_drift.m3.e0`` is checked alongside the transport prefixes: a canary
    that imported the E0 driver would inherit its namespace and authority vocabulary, which is
    exactly the coupling §5 item 13 forbids.
    """
    import json as _json
    import subprocess

    program = (
        "import sys, json;"
        "import disclosure_drift.m3;"
        "before = set(sys.modules);"
        "import disclosure_drift.m3.single_source_canary as c;"
        "from disclosure_drift.m3.offline_parse import PROHIBITED_IMPORT_PREFIXES as p;"
        "added = set(sys.modules) - before;"
        "banned = (*p, 'disclosure_drift.m3.e0');"
        "print(json.dumps(sorted("
        "name for name in added if any("
        "name == b or name.startswith(b + '.') for b in banned))))"
    )
    completed = subprocess.run(  # noqa: S603 - fixed argument vector, no shell
        [sys.executable, "-c", program], capture_output=True, text=True, check=True
    )
    assert _json.loads(completed.stdout) == [], completed.stdout


def test_the_canary_module_names_no_e0_authority_or_namespace() -> None:
    """§5 item 13: neither an activation constant nor a run namespace appears in the source."""
    source = Path(canary.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "M3_3_E0_EXECUTION_AUTHORITY",
        "PRE_E0_CATALOG_TRANSITION_AUTHORITY",
        "STALE_WRITER_LEASE_RECOVERY_AUTHORITY",
        "E0_RUN_NAMESPACE",
        "create_run_namespace",
    ):
        assert forbidden not in source, f"the canary path names {forbidden}"


def test_the_canary_constructs_no_client_on_any_code_path() -> None:
    """The module's executable body names no client, transport, or socket API."""
    tree = ast.parse(Path(canary.__file__).read_text(encoding="utf-8"))
    names = {
        node.attr if isinstance(node, ast.Attribute) else node.id
        for node in ast.walk(tree)
        if isinstance(node, (ast.Attribute, ast.Name))
    }
    for needle in ("SecClient", "HttpxTransport", "socket", "urlopen", "create_connection"):
        assert needle not in names, f"the canary path reaches for {needle}"


def test_no_migration_is_applied_by_a_canary(bulk_run: tuple[Any, Path, Any]) -> None:
    """§5 item 14 and §17: both catalogs stay at the accepted head, and 0016 does not appear."""
    _result, private, world_paths = bulk_run
    for database in (_catalog(private), world_paths.working_catalog):
        with connect(database, writer=False) as connection:
            applied = [
                int(row["version"])
                for row in connection.execute(
                    "SELECT version FROM ops_schema_migrations ORDER BY version"
                )
            ]
        assert max(applied) == 15
        assert 16 not in applied


def test_the_restated_operational_catalog_path_matches_the_two_accepted_copies() -> None:
    """Decision 095 R81's rule, extended to the third copy: pinned by test, not by comment."""
    from disclosure_drift.m3 import acquisition, e0

    assert (
        canary.OPERATIONAL_CATALOG_RELATIVE_PATH
        == e0.OPERATIONAL_CATALOG_RELATIVE_PATH
        == acquisition.OPERATIONAL_CATALOG_RELATIVE_PATH
        == "catalogs/m3_2a_operational.sqlite3"
    )


# ==========================================================================
# Section 9 and 11: the result surface and the operator surface
# ==========================================================================
def test_the_result_document_is_written_once_and_carries_no_absolute_path(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """§9: the report a later execution record reads, and it names nothing outside its world."""
    result, _private, world_paths = bulk_run
    document = json.loads(world_paths.result.read_text(encoding="utf-8"))
    assert document["contract"] == canary.CANARY_CONTRACT
    assert document["evidence_contract"] == COMPACT_EVIDENCE_CONTRACT
    assert document["world_relative_working_catalog"] == "working_catalog.sqlite3"
    assert document["world_relative_sidecar"] == "compact_evidence.sqlite3"
    assert document["operational_catalog_unchanged"] is True
    assert document["projection_digest"] == result.projection_digest
    rendered = json.dumps(document)
    for leak in ("/private/", "/Users/", "/var/folders", "://"):
        assert leak not in rendered, f"the result document carries {leak}"


def test_the_result_surface_answers_every_required_question(
    index_run: tuple[Any, Path, Any],
) -> None:
    """§9: the exact list an execution report must be able to determine from one invocation."""
    result, _private, _world_paths = index_run
    record = result.as_record()
    for key in (
        "source_instance_id",
        "source_id",
        "plan_position",
        "plan_source_count",
        "source_artifact_sha256",
        "source_artifact_byte_length",
        "disposition",
        "parsed_records",
        "members",
        "canonical_accession_count",
        "registrant_count",
        "substantive_relation_count",
        "quarantined_record_count",
        "structural_observation_count",
        "member_manifest_digest",
        "projection_digest",
        "resolution_digest",
        "corroboration_digest",
        "compact_evidence_identity",
        "working_catalog_sha256",
        "world_relative_working_catalog",
        "world_relative_sidecar",
        "migration_head",
        "association_totality",
    ):
        assert key in record, key
    assert result.canonical_accession_count > 0
    assert result.substantive_relation_count > 0
    assert result.association_totality["census_accession_count"] > 0
    assert result.source_artifact_byte_length > 0
    assert result.working_catalog_wal_byte_length == 0


def test_the_operator_surface_runs_one_source_end_to_end(tmp_path: Path) -> None:
    """§5 item 11: the command builds the world, runs one source, and renders it leak-free."""
    private = _private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    work_root = tmp_path / "work"
    outcome = canary.run_canary_source_command(
        mode="run",
        run_id="operator-1",
        source_instance_id=_BULK_INSTANCE,
        work_root=str(work_root),
        repository_root=checkout,
        environ={EVIDENCE_ROOT_ENV: str(private)},
    )
    assert outcome.exit_code == 0
    rendered = "\n".join(outcome.lines)
    assert "canary-source run" in rendered
    assert str(private) not in rendered
    assert str(work_root) not in rendered
    assert (work_root / "operator-1" / "working_catalog.sqlite3").is_file()
    assert _count(_catalog(private), "SELECT COUNT(*) AS n FROM census_parsed_records") == 0


def test_the_operator_preflight_creates_nothing(tmp_path: Path) -> None:
    """§5: preflight validates every predicate read-only, and the world stays absent."""
    private = _private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    work_root = tmp_path / "work"
    before = file_digest(_catalog(private))[0]
    outcome = canary.run_canary_source_command(
        mode="preflight",
        run_id="preflight-1",
        source_instance_id=_BULK_INSTANCE,
        work_root=str(work_root),
        repository_root=checkout,
        environ={EVIDENCE_ROOT_ENV: str(private)},
    )
    assert outcome.exit_code == 0
    assert not (work_root / "preflight-1").exists()
    assert file_digest(_catalog(private))[0] == before


def test_an_unset_private_root_is_refused_without_naming_a_path(tmp_path: Path) -> None:
    """The private root comes from one variable and has no default, fallback, or path option."""
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match=EVIDENCE_ROOT_ENV) as excinfo:
        canary.resolve_private_root(checkout, environ={})
    assert "/" not in str(excinfo.value).replace(EVIDENCE_ROOT_ENV, "")


def test_an_unknown_mode_is_refused(tmp_path: Path) -> None:
    """The library refuses a mode the parser would not have offered, rather than defaulting."""
    private = _private_root(tmp_path)
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    with pytest.raises(canary.SingleSourceCanaryError, match="unknown canary mode"):
        canary.run_canary_source_command(
            mode="execute",
            run_id="mode-1",
            source_instance_id=_BULK_INSTANCE,
            work_root=str(tmp_path / "work"),
            repository_root=checkout,
            environ={EVIDENCE_ROOT_ENV: str(private)},
        )


def test_the_run_local_progress_ledger_records_the_accepted_terminal(
    bulk_run: tuple[Any, Path, Any],
) -> None:
    """D111: the run-local ledger distinguishes progress from disposition, truthfully."""
    _result, _private, world_paths = bulk_run
    ledger = world_paths.directory / "run_progress.sqlite3"
    assert ledger.is_file()
    connection = sqlite3.connect(ledger)
    try:
        connection.row_factory = sqlite3.Row
        rows = [
            dict(row) for row in connection.execute("SELECT * FROM run_source_progress").fetchall()
        ]
    finally:
        connection.close()
    assert len(rows) == 1
    assert rows[0]["source_instance_id"] == _BULK_INSTANCE
    assert rows[0]["state"] == "disposed"
    assert rows[0]["disposition"] == "E0_REQUIRED_PARSE"
