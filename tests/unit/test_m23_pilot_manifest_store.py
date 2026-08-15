"""M2.3 Stage S6 pilot-manifest store tests (Decision 021).

Every test uses a fresh temporary SQLite catalog built through the **real** lifecycle:
a frozen candidate snapshot, a ``planned`` selection run promoted to ``running``, the
terminal result rows written inside that single window, and a ``running -> feasible``
transition that migrations ``0009`` and ``0012`` only accept when 24 selected entities
carry contiguous ``selected_order``, the declared counts match, every reserve package is
rank 1 with a matching quota-contribution set, and exactly one reserve disposition
exists per selected entity.

No test opens, modifies, or touches a persistent repository database, and none performs
a network call: the autouse ``_block_network`` fixture in ``tests/conftest.py`` already
enforces that.

Test obligations discharged here come from Decision 021 section 20: adversarial
eligibility across all seven conditions, nonblocking dispositions, proposed-only,
append-once sealing, atomicity under injected fault, serialization, reconstruction and
replay, recomputability, explicit-argument discipline, and the no-leakage-surface and
statement-discipline assertions.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import sqlite3
import tokenize
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Final

import pytest

# The accepted Stage-S5 plan builders. Decision 021 section 12 requires the S6 store to
# re-derive its run through ``reconstruct_persisted_joint_selection``, so an S6 fixture
# has to be a run that genuinely reconstructs -- which means one the accepted S5 entry
# point produced. Reusing that suite's frozen-snapshot builders is what keeps this module
# from carrying a second, drifting copy of S5 fixture methodology.
import test_m23_accession_selection_store as s5  # noqa: E402

from disclosure_drift.errors import GateFailureError
from disclosure_drift.paths import DataTree
from disclosure_drift.pilot_policy import (
    PILOT_JOINT_SELECTOR_POLICY_VERSION,
    PILOT_QUOTA_POLICY_VERSION,
)
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.release import pilot_manifest as pm
from disclosure_drift.sec import pilot_manifest_store as store
from disclosure_drift.sec.accession_selection_store import (
    execute_and_persist_joint_selection,
)
from disclosure_drift.sec.temporal import SEC_TIMEZONE_NAME
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

_ENTITIES = 24
_GENERATED_AT = "2026-01-03T00:00:00Z"
#: The plan's evidence rows reference this literal observation id.
_OBSERVATION_ID = "obs-1"


def _hex(seed: str) -> str:
    """Deterministic 64-character lowercase hex digest for a test seed."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _explicit(**overrides: str) -> pm.ExplicitArguments:
    """The six caller-supplied identity values Decision 021 section 8.4 requires."""
    fields: dict[str, Any] = {
        "dependency_lock_sha256": _hex("lock"),
        "code_commit_identifier": "903f4ccfb9b393de8e9a696af491b42706a510f2",
        "runtime_python_version": "3.12.13",
        "configuration_sha256": _hex("config"),
        "decision_authority_sha256": _hex("authority"),
        "source_plan_sha256": _hex("plan"),
        "decision_authority_records": (
            (
                "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
                _hex("d010"),
            ),
            ("Docs/Decisions/decision_021_m23_s6_manifest_construction.md", _hex("d021")),
        ),
    }
    fields.update(overrides)
    return pm.ExplicitArguments(**fields)


def _seed_reference_data(connection: sqlite3.Connection) -> None:
    """Seed the reference tables the pilot foreign keys require."""
    with transaction(connection) as active:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            active.execute(
                "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                "is_eligible_universe, description, decision_record) VALUES (?, ?, ?, ?, ?)",
                (
                    form_type,
                    int(is_amendment),
                    int(eligible),
                    description,
                    "Docs/Decisions/decision_007_sec_universe.md",
                ),
            )
        for code in REASON_CODES.values():
            active.execute(
                "INSERT OR REPLACE INTO reference_reason_codes (reason_code, category, "
                "description, blocks_release, requires_manual_review, decision_record) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    code.code,
                    code.category,
                    code.description,
                    int(code.blocks_release),
                    int(code.requires_manual_review),
                    code.decision_reference,
                ),
            )


def _seed_census(connection: sqlite3.Connection) -> str:
    """One source observation with two parser runs producing an identical shape."""
    observation_id = _OBSERVATION_ID
    with transaction(connection) as active:
        active.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES ('job-1', 'sec_census', 'completed', 'M2.2', "
            "'2026-01-01T00:00:00Z', '')"
        )
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "logical_sha256, parser_version, recorded_at_utc) "
            "VALUES (?, 'sec/company_tickers', 'req/company_tickers/1', "
            "'https://example.invalid/a', 'census', '2026-01-01T00:00:00Z', 'stored_new', "
            "?, 'parser/1.0', '2026-01-01T00:00:00Z')",
            (observation_id, _hex("logical-1")),
        )
        for parser_run_id in ("pr-1", "pr-2"):
            active.execute(
                "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, "
                "parser_id, parser_version, started_at_utc, finished_at_utc, parsed_count, "
                "quarantined_count, outcome, summary_json) "
                "VALUES (?, ?, ?, 'parser/1.0', '2026-01-01T00:00:00Z', "
                "'2026-01-01T00:01:00Z', 1, 0, 'completed', '{}')",
                (parser_run_id, observation_id, f"census_parser_{parser_run_id}"),
            )
            shapes = (
                ("facts", "valid_present", "object", "us-gaap:Assets", "$.facts.us-gaap"),
                ("cover", "valid_empty", "array", None, None),
            )
            for index, (region, state, observed, member, path) in enumerate(shapes):
                active.execute(
                    "INSERT INTO census_structural_observations (structural_observation_id, "
                    "parser_run_id, source_observation_id, region, state, observed_type, "
                    "member_name, record_path, count_is_trustworthy, is_genuine_zero, "
                    "recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0, "
                    "'2026-01-01T00:00:00Z')",
                    (
                        _hex(f"struct-{parser_run_id}-{index}"),
                        parser_run_id,
                        observation_id,
                        region,
                        state,
                        observed,
                        member,
                        path,
                    ),
                )
    return observation_id


def _build_catalog(tmp_path: Path, *, with_reserve: bool = True) -> tuple[Path, str, str]:
    """Build a feasible S5 joint run through the **accepted** S5 entry point.

    Nothing here writes a selection row by hand. The frozen snapshot comes from the
    accepted plan builders and the run comes from
    :func:`execute_and_persist_joint_selection`, so the persisted result is one that
    :func:`reconstruct_persisted_joint_selection` re-derives -- which is the precondition
    Decision 021 section 12 puts on every manifest. A hand-written run would carry
    tie-break hashes the accepted derivation never produces and would be refused, which is
    the point: an S6 fixture that cannot survive reconstruction proves nothing about S6.
    """
    database = tmp_path / "catalog.sqlite3"
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference_data(connection)
        _seed_census(connection)
        plan = s5.reserve_plan() if with_reserve else s5.feasible_plan()
        snapshot_id = s5.write_plan(connection, plan)
        persisted = execute_and_persist_joint_selection(
            connection,
            snapshot_id,
            node_limit=s5._NODE_LIMIT,
            occurred_at_utc=s5._AT,
            event_id="event-1",
        )
        assert persisted.run_state == "feasible"
        assert persisted.selected_entity_count == _ENTITIES
    return database, snapshot_id, persisted.selection_run_id


def _selected_accession_count(database: Path) -> int:
    """The run's actual selected-accession count, read rather than assumed."""
    with connect(database) as connection:
        return int(
            connection.execute("SELECT COUNT(*) FROM pilot_selected_accessions").fetchone()[0]
        )


@pytest.fixture
def catalog(tmp_path: Path) -> Iterator[tuple[Path, str, str, DataTree]]:
    """A feasible S5 joint run and the data tree its manifest is written under.

    The catalog is registered as a scratch catalog only for the lifetime of the test that
    asked for it, and discarded at teardown, so the corruption helper can never be handed
    a stale path from an earlier test.
    """
    database, snapshot_id, run_id = _build_catalog(tmp_path)
    _SCRATCH_CATALOGS.add(database.resolve())
    try:
        yield database, snapshot_id, run_id, DataTree.from_root(tmp_path / "data")
    finally:
        _SCRATCH_CATALOGS.discard(database.resolve())


# ==========================================================================
# Group A: sealing -- Decision 021 sections 6, 11.3, 15.5
# ==========================================================================


def test_sealing_writes_the_recomputed_digest_once(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The seal is computed from the section 6.1 preimage and written once."""
    database, _, run_id, _ = catalog
    with connect(database, writer=True) as connection:
        sealed = store.seal_selection_result(connection, run_id)
        assert len(sealed) == 64
        stored = connection.execute(
            "SELECT selection_result_sha256 FROM pilot_selection_runs WHERE selection_run_id = ?",
            (run_id,),
        ).fetchone()[0]
        assert stored == sealed


def test_sealing_is_idempotent_by_content(catalog: tuple[Path, str, str, DataTree]) -> None:
    """An identical recompute-and-reseal replay is a no-op rather than a failure."""
    database, _, run_id, _ = catalog
    with connect(database, writer=True) as connection:
        first = store.seal_selection_result(connection, run_id)
        assert store.seal_selection_result(connection, run_id) == first


def test_sealing_refuses_a_stored_digest_that_does_not_recompute(
    catalog: tuple[Path, str, str, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A seal that does not recompute is never overwritten; it fails closed.

    The persisted rows a seal is computed over are themselves sealed by migrations
    ``0009`` and ``0012`` outside the single ``running`` window, so this drives the
    comparison directly by making one terminal component recompute differently.
    """
    database, _, run_id, _ = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        monkeypatch.setattr(store, "selected_entities_sha256", lambda rows: _hex("divergent"))
        with pytest.raises(GateFailureError, match="does not recompute"):
            store.seal_selection_result(connection, run_id)


def test_terminal_rows_a_seal_is_computed_over_are_schema_sealed(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Defence in depth: the row families the digests read cannot be edited."""
    database, snapshot_id, run_id, _ = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "UPDATE pilot_candidate_snapshots SET candidate_entity_table_sha256 = ? "
                "WHERE snapshot_id = ?",
                (_hex("tampered"), snapshot_id),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "DELETE FROM pilot_selected_entities WHERE selection_run_id = ?", (run_id,)
            )


@pytest.mark.parametrize("state", ["planned", "running", "failed", "infeasible"])
def test_sealing_refuses_a_non_feasible_run(tmp_path: Path, state: str) -> None:
    """The result digest is defined only for a feasible run (section 6.2)."""
    database, snapshot_id, _ = _build_catalog(tmp_path)
    other = _hex(f"run-{state}")
    with connect(database, writer=True) as connection:
        with transaction(connection) as active:
            active.execute(
                "INSERT INTO pilot_selection_runs (selection_run_id, snapshot_id, selection_seed, "
                "selector_policy_version, quota_policy_version, search_node_limit, run_state, "
                "selection_input_sha256, started_at_utc) VALUES (?, ?, 'pilot-seed/1', ?, ?, "
                "100000, ?, ?, '2026-01-01T00:00:00Z')",
                (
                    other,
                    snapshot_id,
                    PILOT_JOINT_SELECTOR_POLICY_VERSION,
                    PILOT_QUOTA_POLICY_VERSION,
                    state,
                    _hex("si2"),
                ),
            )
        with pytest.raises(GateFailureError, match="feasible"):
            store.seal_selection_result(connection, other)


def test_sealing_refuses_a_missing_run(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Condition 1 of section 11.2: the referenced run must exist."""
    database, _, _, _ = catalog
    with (
        connect(database, writer=True) as connection,
        pytest.raises(GateFailureError, match="does not exist"),
    ):
        store.seal_selection_result(connection, _hex("absent"))


# ==========================================================================
# Group B: build and persist -- Decision 021 sections 11.1, 11.3, 13
# ==========================================================================


def _seal_and_build(
    catalog: tuple[Path, str, str, DataTree], **overrides: Any
) -> store.PersistedPilotManifest:
    """Seal the run and build one proposed manifest."""
    database, _, run_id, tree = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        return store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=overrides.pop("explicit", _explicit()),
            generated_at_utc=_GENERATED_AT,
            **overrides,
        )


def test_manifest_is_created_only_in_the_proposed_state(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """S6 code may create a manifest only in ``manifest_state = 'proposed'``."""
    database, _, _, _ = catalog
    manifest = _seal_and_build(catalog)
    with connect(database) as connection:
        row = connection.execute(
            "SELECT manifest_state, supersedes_manifest_id, approval_reference, "
            "approved_root_sha256, approved_at_utc FROM pilot_manifest_versions "
            "WHERE manifest_id = ?",
            (manifest.identity.manifest_id,),
        ).fetchone()
    assert row["manifest_state"] == "proposed"
    assert row["supersedes_manifest_id"] is None
    assert row["approval_reference"] is None
    assert row["approved_root_sha256"] is None
    assert row["approved_at_utc"] is None


def test_manifest_row_and_document_commit_together(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The row and the serialized JSON commit together or not at all."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    assert path.exists()
    assert path.read_text(encoding="utf-8") == manifest.canonical_json
    with connect(database) as connection:
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 1


def test_manifest_relative_path_is_relative_and_resolves(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """``relative_manifest_path`` is persisted for retrieval and is never absolute."""
    _, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    assert not manifest.relative_manifest_path.startswith("/")
    assert (tree.data_root / manifest.relative_manifest_path).exists()


def test_manifest_filename_is_content_derived_from_the_root(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The filename equals ``pilot_manifest_<root>.json`` (section 13.5)."""
    manifest = _seal_and_build(catalog)
    assert manifest.relative_manifest_path.endswith(
        f"pilot_manifest_{manifest.root_manifest_sha256}.json"
    )


def test_manifest_identity_is_content_derived(catalog: tuple[Path, str, str, DataTree]) -> None:
    """``manifest_id`` recomputes from the root, ordinal, and absent predecessor."""
    manifest = _seal_and_build(catalog)
    assert manifest.identity.manifest_id == pm.manifest_identifier(
        root_sha256=manifest.root_manifest_sha256,
        ordinal_version=1,
        supersedes_manifest_id=None,
    )


def test_manifest_document_carries_all_thirteen_blocks(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """All thirteen section 13.2 blocks are present and populated over the fixture."""
    manifest = _seal_and_build(catalog)
    assert set(manifest.document) == set(pm.DOCUMENT_BLOCKS)
    for block in pm.DOCUMENT_BLOCKS:
        assert manifest.document[block], f"block {block} is empty"


def test_manifest_document_renders_the_persisted_rows(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The document is a rendering of the rows the digests were computed over."""
    database, snapshot_id, run_id, _ = catalog
    manifest = _seal_and_build(catalog)
    document = manifest.document
    assert isinstance(document["selected_entities"], list)
    assert len(document["selected_entities"]) == _ENTITIES
    assert isinstance(document["selected_accessions"], list)
    assert len(document["selected_accessions"]) == _selected_accession_count(database)
    reserves = document["reserves"]
    assert isinstance(reserves, dict)
    with connect(database) as connection:
        packages = int(connection.execute("SELECT COUNT(*) FROM pilot_reserves").fetchone()[0])
        dispositions = int(
            connection.execute("SELECT COUNT(*) FROM pilot_selection_entity_reasons").fetchone()[0]
        )
    assert packages > 0
    assert len(reserves["packages"]) == packages
    assert len(reserves["dispositions"]) == dispositions
    assert packages + dispositions == _ENTITIES


def test_manifest_document_carries_every_transitive_entity_value(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Block 8 carries the section 13.2.1 entity-record items, not only section 7.1.

    Every value is compared against the reconstruction source the crosswalk records for
    it -- ``pilot_candidate_entities`` -- read independently of the manifest build.
    """
    database, snapshot_id, _, _ = catalog
    manifest = _seal_and_build(catalog)
    records = {row["cik_numeric"]: row for row in manifest.document["selected_entities"]}
    assert len(records) == _ENTITIES
    with connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM pilot_candidate_entities WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchall()
    persisted = {row["cik_numeric"]: row for row in rows}
    for cik, record in records.items():
        for field in pm.ENTITY_CANDIDATE_FIELDS:
            assert field in record, f"entity {cik} is missing {field}"
            assert record[field] == persisted[cik][field], f"entity {cik} {field} disagrees"
        for flag in pm.NAME_CHANGE_FLAG_FIELDS:
            assert flag in record, f"entity {cik} is missing {flag}"
        assert isinstance(record["classification_evidence"], list)
        assert isinstance(record["candidate_reasons"], list)
    # The accepted plan gives the first slots identity evidence, so the evidence family is
    # populated rather than vacuously empty. Decision 019 section 8.1.1 makes
    # identity-scope *entity reasons* unsupported at S5, so this plan legitimately has
    # none and the reasons family renders empty here; the rendering of a populated reasons
    # family is proved directly in ``test_m23_pilot_manifest.py``.
    assert any(record["classification_evidence"] for record in records.values())
    dimensions = {
        entry["classification_dimension"]
        for record in records.values()
        for entry in record["classification_evidence"]
    }
    assert "identity" in dimensions
    # The accession-side candidate reasons the plan does write reach block 13.
    counts = manifest.document["historical_reconstruction"]["exclusion_counts_by_reason_code"]
    assert counts, "no candidate reason codes reached the exclusion counts"


def test_manifest_document_carries_every_transitive_accession_value(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Block 9 carries the section 13.2.1 accession-record items, compared to their source."""
    database, snapshot_id, _, _ = catalog
    manifest = _seal_and_build(catalog)
    records = {row["accession_plain"]: row for row in manifest.document["selected_accessions"]}
    with connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM pilot_candidate_accessions WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchall()
    persisted = {row["accession_plain"]: row for row in rows}
    stored_alias = {
        "stored_amendment_linkage_state": "amendment_linkage_state",
        "stored_provisional_parent_accession": "provisional_parent_accession",
        "stored_cohort_evidence_level": "cohort_evidence_level",
        "stored_amendment_purpose_evidence_level": "amendment_purpose_evidence_level",
    }
    for plain, record in records.items():
        for field in pm.ACCESSION_CANDIDATE_FIELDS:
            assert field in record, f"accession {plain} is missing {field}"
            column = stored_alias.get(field, field)
            assert record[field] == persisted[plain][column], f"{plain} {field} disagrees"
        for field in pm.ACCESSION_DERIVED_FIELDS:
            assert field in record, f"accession {plain} is missing {field}"
        assert isinstance(record["registrants"], list)
        assert record["registrants"], f"accession {plain} has no registrant records"
    # The eight *_evidence_level values crosswalk item 63 enumerates.
    levels = {name for name in records[next(iter(records))] if name.endswith("_evidence_level")}
    assert levels == {
        "filing_date_evidence_level",
        "stored_cohort_evidence_level",
        "cohort_evidence_level",
        "xbrl_evidence_level",
        "amendment_purpose_evidence_level",
        "stored_amendment_purpose_evidence_level",
        "amendment_linkage_evidence_level",
        "multi_registrant_evidence_level",
    }
    assert any(record["multi_registrant"] for record in records.values()) or all(
        record["multi_registrant"] in (0, 1) for record in records.values()
    )


def test_manifest_document_discharges_every_crosswalk_item(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Every D and T item is serialized; every X and S9 item is absent (section 13.2.1)."""
    manifest = _seal_and_build(catalog)
    covered = pm.verify_document_crosswalk_coverage(manifest.document)
    required = {item.number for item in pm.CROSSWALK if item.classification in {"D", "T"}}
    assert required <= set(covered)
    excluded = {item.number for item in pm.CROSSWALK if item.classification in {"X", "S9"}}
    assert not (excluded & set(covered))


def _rendered_copy(manifest: store.PersistedPilotManifest) -> dict[str, Any]:
    """A deep copy of the rendered document, so one mutation cannot leak into the next."""
    copied: dict[str, Any] = json.loads(manifest.canonical_json)
    return copied


# ==========================================================================
# Decision 022 — item-46 reserve-rank applicability, over the real catalog
# ==========================================================================


@pytest.fixture
def zero_reserve_catalog(tmp_path: Path) -> Iterator[tuple[Path, str, str, DataTree]]:
    """A feasible run with **zero** reserve packages and complete dispositions.

    This exercises ``_build_catalog(..., with_reserve=False)``, which the accepted
    Stage-S5.1 plan produces: twenty-four selected entities, no compatible reserve for any
    of them, and one ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` row each. Migration ``0012``
    accepts that as total coverage, and Decision 020 §7.1 makes it nonblocking, so it is a
    lawful accepted S5 terminal state rather than an edge case.
    """
    database, snapshot_id, run_id = _build_catalog(tmp_path, with_reserve=False)
    _SCRATCH_CATALOGS.add(database.resolve())
    try:
        yield database, snapshot_id, run_id, DataTree.from_root(tmp_path / "data")
    finally:
        _SCRATCH_CATALOGS.discard(database.resolve())


def test_zero_reserve_fixture_is_the_shape_decision_022_governs(
    zero_reserve_catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The fixture really is zero packages with one disposition per selected target."""
    database, _, _, _ = zero_reserve_catalog
    with connect(database) as connection:
        packages = int(connection.execute("SELECT COUNT(*) FROM pilot_reserves").fetchone()[0])
        entities = int(
            connection.execute("SELECT COUNT(*) FROM pilot_selected_entities").fetchone()[0]
        )
        rows = connection.execute(
            "SELECT reason_scope, reason_code, COUNT(*) FROM pilot_selection_entity_reasons "
            "GROUP BY 1, 2"
        ).fetchall()
        state = connection.execute("SELECT run_state FROM pilot_selection_runs").fetchone()[0]
    assert state == "feasible"
    assert packages == 0
    assert entities == _ENTITIES
    assert [tuple(row) for row in rows] == [
        ("reserve", "REVIEW_PILOT_NO_COMPATIBLE_RESERVE", _ENTITIES)
    ]


def test_zero_reserve_run_builds_persists_verifies_and_replays(
    zero_reserve_catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Decision 022: structural non-applicability never makes such a run ineligible."""
    database, _, run_id, tree = zero_reserve_catalog
    with connect(database, writer=True) as connection:
        sealed = store.seal_selection_result(connection, run_id)
        assert len(sealed) == 64
        manifest = store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
        )
        verified = store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )
        replayed = store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
        )
        rows = int(connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0])
    assert verified.root_manifest_sha256 == manifest.root_manifest_sha256
    assert replayed.identity.manifest_id == manifest.identity.manifest_id
    assert rows == 1
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    assert path.exists()


def test_zero_reserve_document_carries_an_empty_package_family_and_no_invented_rank(
    zero_reserve_catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Clause 8: no synthetic package, no rank 0, null, or "N/A" is ever serialized."""
    manifest = _seal_and_build(zero_reserve_catalog)
    reserves = manifest.document["reserves"]
    assert isinstance(reserves, dict)
    assert reserves["packages"] == [], "the package family is present and empty, not absent"
    assert len(reserves["dispositions"]) == _ENTITIES
    rendered = manifest.canonical_json
    assert "reserve_rank" not in rendered
    for invented in ('"N/A"', '"reserve_rank": 0', '"reserve_rank": null', "placeholder"):
        assert invented not in rendered


def test_zero_reserve_document_discharges_item_46_and_item_70(
    zero_reserve_catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Item 46 by structural non-applicability; item 70 by the dispositions."""
    manifest = _seal_and_build(zero_reserve_catalog)
    covered = pm.verify_document_crosswalk_coverage(manifest.document)
    assert 46 not in covered
    assert 70 in covered
    coverage = pm.reserve_coverage(manifest.document)
    assert coverage.targets_with_package == frozenset()
    assert len(coverage.targets_with_disposition) == _ENTITIES


def test_mixed_reserve_run_requires_item_46_and_succeeds(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The default fixture is mixed; item 46 is required there and is discharged."""
    manifest = _seal_and_build(catalog)
    coverage = pm.reserve_coverage(manifest.document)
    assert coverage.targets_with_package, "the mixed fixture must carry at least one package"
    assert coverage.targets_with_disposition, "and at least one disposition"
    assert not (coverage.targets_with_package & coverage.targets_with_disposition)
    covered = pm.verify_document_crosswalk_coverage(manifest.document)
    assert 46 in covered and 70 in covered
    reserves = manifest.document["reserves"]
    assert isinstance(reserves, dict)
    assert all(row["reserve_rank"] == pm.ACCEPTED_RESERVE_RANK for row in reserves["packages"])


def test_zero_reserve_persisted_missing_disposition_fails_closed(
    zero_reserve_catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The zero-package shape is eligible only with complete **persisted** coverage.

    The corruption is applied to persisted rows rather than to the rendered document, so
    this proves the storage path rather than the rendering. A target left with neither a
    package nor a disposition is refused with ``GateFailureError`` at the public boundary,
    and no manifest row survives. Only the one guard that blocks this exact statement is
    removed, and it is reinstalled from its own captured definition in a ``finally``.
    """
    database, _, run_id, _ = zero_reserve_catalog
    guard = "pilot_selection_entity_reasons_delete_guard"
    raw = sqlite3.connect(_require_scratch_catalog(database), isolation_level=None)
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?", (guard,)
        ).fetchone()
        assert definition is not None, f"{guard} is not installed"
        raw.execute(f"DROP TRIGGER {guard}")
        try:
            raw.execute(
                "DELETE FROM pilot_selection_entity_reasons WHERE rowid = "
                "(SELECT MIN(rowid) FROM pilot_selection_entity_reasons)"
            )
        finally:
            raw.execute(str(definition[0]))
        assert (
            int(
                raw.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name = ?",
                    (guard,),
                ).fetchone()[0]
            )
            == 1
        )
    finally:
        raw.close()
    with connect(database, writer=True) as connection, pytest.raises(GateFailureError):
        store.seal_selection_result(connection, run_id)
    with connect(database) as connection:
        assert (
            int(connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0])
            == 0
        )


def test_reserve_bearing_manifest_is_byte_identical_after_the_clarification(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Decision 022 §6: the existing reserve-bearing path is unchanged, byte for byte.

    These are pinned so that any change to item-46 applicability, or to a preimage, that
    perturbs a reserve-bearing manifest fails here rather than silently reissuing an
    identity the owner has already seen.

    **Re-baselined once, under Decision 083 §10, and every delta is traceable.** The
    fixture carries exactly two genuinely multi-registrant accessions (CIK 17 with 917,
    CIK 18 with 918), so the correction moves precisely five of the eight components and
    no others:

    * ``selector_policy_sha256`` -- its ``migration_chain_sha256`` now covers ``0001``
      through ``0014`` instead of ``0013``. This is migration 0014 existing, and is
      unrelated to registrant semantics;
    * ``selected_entities_sha256``, ``selected_accessions_sha256``, ``reserves_sha256``,
      and ``quota_report_sha256`` -- all four carry ``selection_run_id``, which derives
      from ``selection_input_sha256`` (**E5**), which carries ``accession_content_sha256``,
      which now reports the two multi-registrant accessions as **anchorless** with the
      **R60** sentinel in their tie-break preimage.

    **Unchanged, and asserted as such:** ``source_observation_set_sha256``,
    ``candidate_tables_sha256``, and ``quota_definitions_sha256``. The candidate-table
    digest holding still is the load-bearing one -- it is the frozen snapshot's own
    identity, so **E2**, **E3**, and **E4** are byte-unchanged for this fixture.

    **Re-baselined a second time, under Decision 085 §5-§6, on exactly ONE component.**
    Correcting migration ``0014``'s stale R67 comments and closing its
    established-with-zero-relation doors changes that file's bytes, and the file's
    ``checksum_sha256`` is one of ``MIGRATION_CHAIN_COLUMNS``' three fields. So
    ``selector_policy_sha256`` moved again -- ``29783a60…`` to ``cd237060…`` -- and
    carried ``root_manifest_sha256`` (``afe6fd9e…`` to ``129b8636…``) and ``manifest_id``
    (``44de5d26…`` to ``b07f4965…``) with it. Nothing else moved at all.

    **Re-baselined a third time, under accepted Decision 087 §9, on the same one component
    and for the same one reason.** Migration ``0015`` exists, so ``ops_schema_migrations``
    carries a fifteenth row, so ``migration_chain_sha256`` moves, so
    ``selector_policy_sha256`` moves (``cd237060…`` to ``2f675005…``) and carries
    ``root_manifest_sha256`` (``129b8636…`` to ``317edeb1…``) and ``manifest_id``
    (``b07f4965…`` to ``bd9cbce6…``) with it. This is precisely the path accepted Decision
    086 §3 (**R68**) classified as an EXPECTED GOVERNED POLICY-BINDING CONSEQUENCE::

        migration checksum -> migration_chain_sha256 -> selector_policy_sha256
                           -> root_manifest_sha256 / manifest_id

    The canonical-JSON length moves too, and only this time: ``275547`` to ``275721``. That
    is +174 characters for one rendered ``(version, name, checksum_sha256)`` entry in the
    Decision 021 §13.2 block-5 migration chain -- a row being ADDED, where the Decision-085
    re-baseline only changed an existing row's value. It is arithmetic about the document,
    not a selection or registrant fact.

    **Unchanged, and asserted as such:** all seven other components -- including
    ``candidate_tables_sha256``, which is the frozen snapshot's own identity -- and
    ``selection_result_sha256``. **No verified document evidence exists anywhere in this
    fixture**, so nothing here reflects evidence CONTENT; the movement is caused solely by
    the migration chain, which is the distinction Decision 087 §9 requires to be stated
    rather than assumed.

    **Re-baselined a fourth time, under accepted Decision 088 §11, on the same one component
    and for the same one reason.** Correcting migration ``0015`` for the six accepted D087
    review findings changed that file's bytes, so its ``checksum_sha256`` moved
    (``c5328894…`` to ``d7f22999…``), so ``selector_policy_sha256`` moved (``2f675005…`` to
    ``2de6fd30…``) and carried ``root_manifest_sha256`` (``317edeb1…`` to ``8c4fff82…``) and
    ``manifest_id`` (``bd9cbce6…`` to ``5f3d0462…``) with it. It is the same accepted **R68**
    path, one link earlier.

    **The canonical-JSON length does NOT move this time, and that is the tell.** It stays at
    ``275721``: the previous re-baseline ADDED a block-5 row, while this one only changes an
    existing row's checksum value, and a SHA-256 is 64 characters however its bytes turn out.
    The same eight components remain byte-identical, so the movement is again caused solely
    by the migration chain and not by evidence content -- of which there is still none.
    """
    manifest = _seal_and_build(catalog)
    assert manifest.components == pm.ManifestComponents(
        source_observation_set_sha256=(
            "f0e125af99205058242a6cfb9285d68e988d5fbecc7199eb25c2c9febf40f7e1"
        ),
        candidate_tables_sha256="b882a148be763ded3531509d7b91d800ca7b5f838865a6bfb5cd06988e775a83",
        quota_definitions_sha256="0a2fd409cb7eaad47fbd6cb4c1b3cf11cffa1a56af5716acdb4aacb801ac616d",
        selector_policy_sha256="2de6fd3096df95a674dbfbd7f2fa03930181b89ffedb23a33606248c9533bf49",
        selected_entities_sha256="86a18dac1629d83ee5d8e8f9bb8ad3a606ae0de7ec8c527079b080c8e113d963",
        selected_accessions_sha256="541bbf7b55b3b355b3e5fcbe15572be2a96df35877f25083ba20f4ba78d7ca87",
        reserves_sha256="ac83550bc6168b5d933d8dc1e3abdd451689c39576f1f08ab49abe6950fc935d",
        quota_report_sha256="8b9bb4e4f456b469ecb486160cd81dbd98d6d0a83aca25dcdd2a3f19f65de0eb",
    )
    assert (
        manifest.selection_result_sha256
        == "1c7d8b8ce4357ac3fc7e2b39630c2a60b1cbfac586bd1eba159c7718185c5815"
    )
    assert (
        manifest.root_manifest_sha256
        == "8c4fff82c4ebff94ff530cc29a970a8546c23cef63e23ce89f434a41910f56b8"
    )
    assert (
        manifest.identity.manifest_id
        == "5f3d04629b61bd32a3fda0975fa1a495f61c7699555b813ca53036c963bbeef0"
    )
    assert len(manifest.canonical_json) == 275721


def test_manifest_document_refuses_a_dropped_authority_record_family(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Section 13.2.1: a covering digest never discharges a required class-T record.

    Item 11 asks for the enumerated ``(decision record, content sha256)`` pairs, and
    ``decision_authority_sha256`` sits beside them in the same block. Item-level coverage
    alone therefore cannot catch the pairs going missing -- the digest keeps the item
    "covered" -- which is precisely the substitution section 13.2.1 forbids. Dropping the
    records must fail closed even though the digest that binds them is still there.
    """
    manifest = _seal_and_build(catalog)
    document = _rendered_copy(manifest)
    assert pm.verify_document_crosswalk_coverage(document)
    authority = document["active_authority"]
    assert authority["decision_records"], "the fixture must carry enumerated authority records"
    del authority["decision_records"]
    assert authority["decision_authority_sha256"], "the covering digest is deliberately left in"
    with pytest.raises(GateFailureError, match="missing the required document records"):
        pm.verify_document_crosswalk_coverage(document)


def test_manifest_document_refuses_a_dropped_registrant_family(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Item 49's per-accession registrant records are required, not merely bound.

    ``multi_registrant`` discharges item 49 as well, so removing the registrant records
    leaves the item covered; the record family has to be required in its own right.
    """
    manifest = _seal_and_build(catalog)
    document = _rendered_copy(manifest)
    accessions = document["selected_accessions"]
    assert all(row["registrants"] for row in accessions)
    del accessions[0]["registrants"]
    assert "multi_registrant" in accessions[0], "the covering value is deliberately left in"
    with pytest.raises(GateFailureError, match="missing the required document records"):
        pm.verify_document_crosswalk_coverage(document)


def test_manifest_document_refuses_a_dropped_entity_record_family(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """One entity losing its evidence or reason family fails closed on that record."""
    for family in ("classification_evidence", "candidate_reasons"):
        manifest = _seal_and_build(catalog)
        document = _rendered_copy(manifest)
        entities = document["selected_entities"]
        assert len(entities) == _ENTITIES
        del entities[3][family]
        with pytest.raises(GateFailureError, match="missing the required document records"):
            pm.verify_document_crosswalk_coverage(document)


def test_manifest_document_excludes_every_operational_field(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """The real ``SELECT *`` row shape carries timestamps; the document must not.

    The fixture writes the run through the accepted S5 path, so every selected and
    candidate row genuinely has a ``recorded_at_utc`` and a ``detail``. Asserting their
    absence from the rendering is therefore a live check, not a vacuous one.
    """
    database, _, _, _ = catalog
    manifest = _seal_and_build(catalog)
    with connect(database) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT * FROM pilot_selected_entities LIMIT 1").fetchone()
    # ``sqlite3.Row`` iterates values, so the column names come from ``keys()``.
    columns = set(row.keys())
    assert "recorded_at_utc" in columns
    rendered = pm.render_canonical_json(manifest.document)
    for excluded in sorted(pm.OPERATIONAL_ENVELOPE_FIELDS):
        assert f'"{excluded}"' not in rendered, f"{excluded} leaked into the document"


def test_manifest_document_orders_selected_rows_numerically(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Blocks 8 and 9 are ordered by numeric ``selected_order`` (section 13.2)."""
    manifest = _seal_and_build(catalog)
    entities = [row["selected_order"] for row in manifest.document["selected_entities"]]
    accessions = [row["selected_order"] for row in manifest.document["selected_accessions"]]
    assert entities == list(range(1, _ENTITIES + 1))
    assert accessions == list(range(1, len(accessions) + 1))
    # The defect this pins: a text sort puts 10 before 2 once there are ten or more rows.
    assert entities != sorted(entities, key=str)


def test_manifest_document_every_leaf_is_bound(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Section 13.3: no substantive serialized field is unbound."""
    manifest = _seal_and_build(catalog)
    bindings = pm.document_leaf_bindings(manifest.document)
    assert bindings
    assert all(binding.digests for binding in bindings.values())


def test_manifest_serialization_is_byte_identical_on_re_render(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Re-serializing the same manifest is byte-identical."""
    manifest = _seal_and_build(catalog)
    assert pm.render_canonical_json(manifest.document) == manifest.canonical_json


def test_nonblocking_dispositions_remain_manifest_eligible(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A run carrying no-compatible-reserve dispositions is manifest-eligible."""
    manifest = _seal_and_build(catalog)
    reserves = manifest.document["reserves"]
    assert isinstance(reserves, dict)
    codes = {row["reason_code"] for row in reserves["dispositions"]}
    assert codes == {"REVIEW_PILOT_NO_COMPATIBLE_RESERVE"}


# ==========================================================================
# Group C: eligibility -- Decision 021 section 11.2
# ==========================================================================


def test_manifest_refuses_an_unsealed_run(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Condition 3: the seal must be non-NULL before a manifest may be built."""
    database, _, run_id, tree = catalog
    with (
        connect(database, writer=True) as connection,
        pytest.raises(GateFailureError, match="sealed"),
    ):
        store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
        )


def test_manifest_refuses_a_wrong_selector_policy_version(tmp_path: Path) -> None:
    """Condition 4: the run's recorded policy versions must equal the constants."""
    database, snapshot_id, _ = _build_catalog(tmp_path)
    other = _hex("run-policy")
    tree = DataTree.from_root(tmp_path / "data")
    with connect(database, writer=True) as connection:
        with transaction(connection) as active:
            active.execute(
                "INSERT INTO pilot_selection_runs (selection_run_id, snapshot_id, selection_seed, "
                "selector_policy_version, quota_policy_version, search_node_limit, run_state, "
                "selection_input_sha256, started_at_utc, selected_entity_count, "
                "selected_accession_count, expanded_node_count, finished_at_utc) "
                "VALUES (?, ?, 'pilot-seed/1', 'wrong/9.9', ?, 100000, 'feasible', ?, "
                "'2026-01-01T00:00:00Z', 24, 0, 10, '2026-01-02T00:00:00Z')",
                (other, snapshot_id, PILOT_QUOTA_POLICY_VERSION, _hex("si3")),
            )
        with pytest.raises(GateFailureError, match="selector policy version"):
            store.build_and_persist_pilot_manifest(
                connection,
                other,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )


def test_manifest_refuses_a_non_frozen_snapshot(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Condition 5: the snapshot must be frozen."""
    database, snapshot_id, run_id, tree = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        with transaction(connection) as active:
            active.execute(
                "UPDATE pilot_candidate_snapshots SET snapshot_state = 'invalidated', "
                "invalidated_reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE', "
                "invalidated_at_utc = '2026-01-04T00:00:00Z' WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        with pytest.raises(GateFailureError, match="frozen"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )


def test_manifest_refuses_the_stage_s4_entity_only_draft(tmp_path: Path) -> None:
    """Condition 6: the permanently-``running`` S4 draft is never a manifest source."""
    database, snapshot_id, _ = _build_catalog(tmp_path)
    draft = _hex("s4-draft")
    tree = DataTree.from_root(tmp_path / "data")
    with connect(database, writer=True) as connection:
        with transaction(connection) as active:
            active.execute(
                "INSERT INTO pilot_selection_runs (selection_run_id, snapshot_id, selection_seed, "
                "selector_policy_version, quota_policy_version, search_node_limit, run_state, "
                "selection_input_sha256, started_at_utc) VALUES (?, ?, 'pilot-seed/1', ?, ?, "
                "100000, 'planned', ?, '2026-01-01T00:00:00Z')",
                (
                    draft,
                    snapshot_id,
                    PILOT_JOINT_SELECTOR_POLICY_VERSION,
                    PILOT_QUOTA_POLICY_VERSION,
                    _hex("si-draft"),
                ),
            )
            active.execute(
                "UPDATE pilot_selection_runs SET run_state = 'running', current_attempt = 1 "
                "WHERE selection_run_id = ?",
                (draft,),
            )
        # Layer 1: application eligibility refuses the draft.
        with pytest.raises(GateFailureError, match="feasible"):
            store.build_and_persist_pilot_manifest(
                connection,
                draft,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )
        # Layer 2: migration 0013 block 2 refuses sealing it.
        with pytest.raises(sqlite3.IntegrityError, match="feasible"):
            connection.execute(
                "UPDATE pilot_selection_runs SET selection_result_sha256 = ? "
                "WHERE selection_run_id = ?",
                (_hex("forged"), draft),
            )
        # Layer 3: migration 0013 block 3 refuses a manifest over it.
        with pytest.raises(sqlite3.IntegrityError, match="feasible"):
            connection.execute(
                "INSERT INTO pilot_manifest_versions (manifest_id, selection_run_id, snapshot_id, "
                "manifest_schema_version, ordinal_version, source_observation_set_sha256, "
                "candidate_tables_sha256, quota_definitions_sha256, selector_policy_sha256, "
                "selected_entities_sha256, selected_accessions_sha256, reserves_sha256, "
                "quota_report_sha256, root_manifest_sha256, manifest_state, generated_at_utc) "
                "VALUES (?, ?, ?, 'pilot-manifest/1.0', 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
                "'proposed', '2026-01-03T00:00:00Z')",
                (
                    _hex("m-draft"),
                    draft,
                    snapshot_id,
                    *[_hex(f"c{index}") for index in range(9)],
                ),
            )


def test_manifest_refuses_a_component_that_does_not_recompute(
    catalog: tuple[Path, str, str, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Condition 7: every component hash must independently recompute."""
    database, _, run_id, tree = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        monkeypatch.setattr(store, "reserves_sha256", lambda **kwargs: _hex("divergent"))
        with pytest.raises(GateFailureError, match="recompute"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 0


# ==========================================================================
# Group D: replay, verification, recomputability -- Decision 021 section 12
# ==========================================================================


def test_replay_reads_reconstructs_compares_and_returns_without_writing(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Idempotent replay never replaces: it returns the existing manifest unchanged."""
    database, _, run_id, tree = catalog
    first = _seal_and_build(catalog)
    with connect(database, writer=True) as connection:
        before = connection.execute(
            "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?",
            (first.identity.manifest_id,),
        ).fetchone()
        second = store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc="2026-09-09T00:00:00Z",
        )
        after = connection.execute(
            "SELECT * FROM pilot_manifest_versions WHERE manifest_id = ?",
            (first.identity.manifest_id,),
        ).fetchone()
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 1
    assert second.root_manifest_sha256 == first.root_manifest_sha256
    assert second.canonical_json == first.canonical_json
    assert tuple(before) == tuple(after)


def test_verification_reproduces_every_digest(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Nothing stored is trusted that was not re-derived."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    with connect(database) as connection:
        verified = store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )
    assert verified.root_manifest_sha256 == manifest.root_manifest_sha256
    assert verified.canonical_json == manifest.canonical_json


def test_verification_fails_closed_on_a_corrupted_root(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A corrupted root is caught, and migration 0009 makes it unwritable anyway."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    with connect(database, writer=True) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE pilot_manifest_versions SET root_manifest_sha256 = ? WHERE manifest_id = ?",
                (_hex("forged"), manifest.identity.manifest_id),
            )
        verified = store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )
        assert verified.root_manifest_sha256 == manifest.root_manifest_sha256


#: Catalogs this module built for the test now running. The corruption helper below
#: accepts nothing else, so it cannot touch a real catalog even by mistake.
_SCRATCH_CATALOGS: set[Path] = set()


def _require_scratch_catalog(path: Path) -> str:
    """Refuse to hand back anything but a catalog this suite itself created."""
    resolved = path.resolve()
    if resolved not in _SCRATCH_CATALOGS:
        message = (
            f"refusing to disable a lifecycle guard on {resolved}: corruption fixtures run only "
            "against a throwaway catalog created by this suite's own fixture"
        )
        raise AssertionError(message)
    return str(resolved)


def _corrupt_manifest_row(path: Path, column: str, value: object, manifest_id: str) -> None:
    """Rewrite one persisted ``pilot_manifest_versions`` column out of band.

    Migration 0009's ``pilot_manifest_hashes_immutable`` and migration 0013's identity
    guard make these columns unwritable on every ordinary connection, which is the
    property proved elsewhere. Historically corrupted storage must still be refused, and
    that state is no longer reachable through the guarded path, so it is constructed here
    on a raw connection to the throwaway per-test catalog, in autocommit, with foreign
    keys ON and **only the one guard that blocks this exact column** dropped. The guard is
    reinstalled from its own captured ``sqlite_master`` definition in a ``finally`` block
    before the caller regains control, so every later assertion runs against a fully
    guarded catalog.
    """
    identity_columns = {
        "manifest_id",
        "manifest_schema_version",
        "selection_run_id",
        "snapshot_id",
        "ordinal_version",
        "supersedes_manifest_id",
    }
    guard = (
        "pilot_manifest_versions_identity_guard"
        if column in identity_columns
        else "pilot_manifest_hashes_immutable"
    )
    raw = sqlite3.connect(_require_scratch_catalog(path), isolation_level=None)
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?", (guard,)
        ).fetchone()
        assert definition is not None, f"{guard} is not installed"
        raw.execute(f"DROP TRIGGER {guard}")
        try:
            raw.execute(
                f"UPDATE pilot_manifest_versions SET {column} = ? WHERE manifest_id = ?",  # noqa: S608
                (value, manifest_id),
            )
        finally:
            raw.execute(str(definition[0]))
        restored = raw.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'trigger' AND name = ?", (guard,)
        ).fetchone()[0]
        assert restored == 1, f"{guard} was not reinstalled after the corruption"
    finally:
        raw.close()


_GOVERNED_MANIFEST_COLUMNS: Final[tuple[str, ...]] = (
    "source_observation_set_sha256",
    "candidate_tables_sha256",
    "quota_definitions_sha256",
    "selector_policy_sha256",
    "selected_entities_sha256",
    "selected_accessions_sha256",
    "reserves_sha256",
    "quota_report_sha256",
    "root_manifest_sha256",
    "manifest_schema_version",
    "ordinal_version",
)


@pytest.mark.parametrize("column", _GOVERNED_MANIFEST_COLUMNS)
def test_verification_fails_closed_on_every_corrupted_governed_column(
    catalog: tuple[Path, str, str, DataTree], column: str
) -> None:
    """Every governed stored column is re-derived and compared, not trusted.

    The corruption is applied to persisted state rather than simulated by patching the
    production digest function, so this proves the storage path rather than the call.
    """
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    value: object = 9 if column == "ordinal_version" else _hex(f"divergent-{column}")
    if column == "manifest_schema_version":
        value = "pilot-manifest/9.9"
    _corrupt_manifest_row(database, column, value, manifest.identity.manifest_id)
    with connect(database) as connection, pytest.raises(GateFailureError, match="reproduce"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


@pytest.mark.parametrize("column", _GOVERNED_MANIFEST_COLUMNS)
def test_replay_fails_closed_on_every_corrupted_governed_column(
    catalog: tuple[Path, str, str, DataTree], column: str
) -> None:
    """Same-ID replay compares every governed column, not only the root and the ID.

    Comparing only downstream hashes would let a corrupted component column replay as
    valid while the root it sits beside still matched (Decision 021 sections 11.3, 12).
    """
    database, _, run_id, tree = catalog
    manifest = _seal_and_build(catalog)
    value: object = 9 if column == "ordinal_version" else _hex(f"divergent-{column}")
    if column == "manifest_schema_version":
        value = "pilot-manifest/9.9"
    _corrupt_manifest_row(database, column, value, manifest.identity.manifest_id)
    with connect(database, writer=True) as connection, pytest.raises(GateFailureError):
        store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
        )
    with connect(database) as connection:
        assert (
            int(connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0])
            == 1
        )


def test_replay_after_ordinal_corruption_is_a_gate_failure_not_an_integrity_error(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Every manifest integrity violation surfaces as GateFailureError (section 16).

    An out-of-band ``ordinal_version`` rewrite hides the row from the ordinal lookup. The
    conflict is detected before any statement is issued, so migration 0013's replacement
    guard never has to fire and no raw ``sqlite3.IntegrityError`` reaches the caller.
    """
    database, _, run_id, tree = catalog
    manifest = _seal_and_build(catalog)
    _corrupt_manifest_row(database, "ordinal_version", 7, manifest.identity.manifest_id)
    with connect(database, writer=True) as connection:
        with pytest.raises(GateFailureError, match="already exists"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )
        assert (
            int(connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0])
            == 1
        )


def test_verification_fails_closed_on_a_corrupted_component(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A persisted source row that no longer yields its stored component fails closed."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    raw = sqlite3.connect(_require_scratch_catalog(database), isolation_level=None)
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            ("pilot_quota_results_update_guard",),
        ).fetchone()
        raw.execute("DROP TRIGGER pilot_quota_results_update_guard")
        try:
            raw.execute(
                "UPDATE pilot_quota_results SET eligible_pool_count = eligible_pool_count + 1"
            )
        finally:
            raw.execute(str(definition[0]))
    finally:
        raw.close()
    with connect(database) as connection, pytest.raises(GateFailureError):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_verification_fails_closed_on_a_tampered_document(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A serialized document that does not re-render byte-identically fails closed."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.write_text(manifest.canonical_json.replace("proposed", "owner_approved"), encoding="utf-8")
    with (
        connect(database) as connection,
        pytest.raises(GateFailureError, match="byte-identically"),
    ):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_seal_remains_recomputable_after_every_refused_write(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Section 15.5 clause 9: the seal recomputes from its persisted preimage.

    The three persisted identity fields the section 6.1 preimage reads are immutable,
    so the row a sealed digest was computed from cannot be rewritten underneath it.
    """
    database, snapshot_id, run_id, tree = catalog
    manifest = _seal_and_build(catalog)
    with connect(database, writer=True) as connection:
        for column, value in (
            ("selection_run_id", _hex("other-run")),
            ("snapshot_id", _hex("other-snap")),
            ("selection_input_sha256", _hex("other-input")),
        ):
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(
                    f"UPDATE pilot_selection_runs SET {column} = ? WHERE selection_run_id = ?",  # noqa: S608
                    (value, run_id),
                )
        with pytest.raises(sqlite3.IntegrityError, match="undeletable"):
            connection.execute(
                "DELETE FROM pilot_selection_runs WHERE selection_run_id = ?", (run_id,)
            )
        verified = store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )
        assert verified.selection_result_sha256 == manifest.selection_result_sha256


def test_atomicity_leaves_no_row_and_no_file_on_an_injected_fault(
    catalog: tuple[Path, str, str, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An injected fault rolls the whole manifest write back."""
    database, _, run_id, tree = catalog
    original = Path.write_text

    def exploding(self: Path, *args: Any, **kwargs: Any) -> int:
        if self.name.startswith("pilot_manifest_"):
            message = "injected serialization fault"
            raise OSError(message)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", exploding)
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        with pytest.raises(OSError, match="injected serialization fault"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 0
    monkeypatch.undo()
    directory = tree.releases / "pilot"
    assert not directory.exists() or not list(directory.glob("pilot_manifest_*.json"))


# ==========================================================================
# Group E: statement discipline and leakage surface -- sections 8.4.1, 11.3, 16
# ==========================================================================


def _executable_source(module: object) -> str:
    """Module source with every comment and string literal removed."""
    raw = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]
    kept: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(raw).readline):
        if token.type in {tokenize.COMMENT, tokenize.STRING}:
            continue
        kept.append(token.string)
    return " ".join(kept)


def _executed_sql(module: object) -> list[str]:
    """Every SQL string the module actually passes to ``.execute()``.

    Scanning the raw file would match the module docstring, which names the statement
    forms it forbids. Walking the AST for ``execute`` call arguments leaves only the SQL
    the store really issues, which is what these prohibitions are about.
    """
    raw = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]
    found: list[str] = []
    for node in ast.walk(ast.parse(raw)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "execute":
            continue
        for argument in node.args:
            for piece in ast.walk(argument):
                if isinstance(piece, ast.Constant) and isinstance(piece.value, str):
                    found.append(piece.value)
    return found


@pytest.mark.parametrize(
    "forbidden", ["INSERT OR REPLACE", "REPLACE INTO", "INSERT OR IGNORE", "DELETE FROM"]
)
def test_store_issues_no_replacement_or_delete_statement(forbidden: str) -> None:
    """Section 16: the store writes plain INSERT and plain UPDATE only."""
    for literal in _executed_sql(store):
        assert forbidden not in literal.upper(), f"store must not issue {forbidden}"


def test_store_never_updates_a_selection_run_identity_column() -> None:
    """No UPDATE may name selection_run_id, snapshot_id, or selection_input_sha256."""
    joined = " ".join(_executed_sql(store)).upper()
    updates = list(joined.split("UPDATE PILOT_SELECTION_RUNS SET ")[1:])
    assert updates, "the store must still seal the result digest"
    for fragment in updates:
        assignments = fragment.split("WHERE")[0]
        for column in ("SELECTION_RUN_ID", "SNAPSHOT_ID", "SELECTION_INPUT_SHA256"):
            assert column not in assignments


def test_store_never_advances_a_manifest_past_proposed() -> None:
    """Section 11.1: no code path produces owner_approved or an approval field."""
    joined = " ".join(_executed_sql(store))
    for forbidden in (
        "owner_approved",
        "approved_root_sha256",
        "approved_at_utc",
        "approval_reference",
        "rejected_at_utc",
        "superseded_at_utc",
    ):
        assert forbidden not in joined, f"store must never write {forbidden}"


def test_store_opens_no_outcome_filing_text_or_companyfacts_source() -> None:
    """Section 8.4.1: the only tables read are those sections 6 through 8 enumerate."""
    joined = " ".join(_executed_sql(store)).lower()
    for forbidden in (
        "companyfacts",
        "company_facts",
        "filing_text",
        "outcome_",
        "xbrl_facts",
        "inventory_accessions",
    ):
        assert forbidden not in joined, f"store must not read {forbidden}"


def test_store_infers_no_build_runtime_or_configuration_identity() -> None:
    """Section 8.4: the six explicit arguments are never inferred."""
    source = _executable_source(store)
    for forbidden in ("subprocess", "os", "sys", "environ"):
        assert forbidden not in source.split(), f"store must not reference {forbidden}"


def test_explicit_arguments_are_required_by_the_store(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A missing explicit argument fails closed before anything is written."""
    database, _, run_id, tree = catalog
    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        with pytest.raises(GateFailureError, match="configuration_sha256"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(configuration_sha256=""),
                generated_at_utc=_GENERATED_AT,
            )
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 0


def test_explicit_arguments_change_the_selector_policy_layer_and_the_root(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Each explicit argument is bound into the root through selector_policy_sha256."""
    database, _, run_id, tree = catalog
    first = _seal_and_build(catalog)
    with connect(database, writer=True) as connection:
        second = store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(code_commit_identifier="deadbeef"),
            generated_at_utc=_GENERATED_AT,
            ordinal_version=2,
        )
    assert second.components.selector_policy_sha256 != first.components.selector_policy_sha256
    assert second.root_manifest_sha256 != first.root_manifest_sha256


def test_accepted_s5_replay_neither_clears_nor_mutates_the_seal(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A sealed run survives the accepted S5 statement shapes untouched (section 3.4)."""
    database, _, run_id, _ = catalog
    with connect(database, writer=True) as connection:
        sealed = store.seal_selection_result(connection, run_id)
        with transaction(connection) as active:
            active.execute(
                "UPDATE pilot_selection_runs SET expanded_node_count = 43 "
                "WHERE selection_run_id = ?",
                (run_id,),
            )
        assert (
            connection.execute(
                "SELECT selection_result_sha256 FROM pilot_selection_runs "
                "WHERE selection_run_id = ?",
                (run_id,),
            ).fetchone()[0]
            == sealed
        )


# ==========================================================================
# Group F: the serialized document, atomicity windows, historical
# reconstruction, and the declared candidate counts -- Decision 021
# sections 11.3, 12, 13.5, and crosswalk item 74
# ==========================================================================


def test_verification_fails_closed_when_the_document_is_missing(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A manifest row without its document is a partial manifest and is refused."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.unlink()
    with connect(database) as connection, pytest.raises(GateFailureError, match="missing"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_verification_fails_closed_on_a_wrong_data_tree(
    catalog: tuple[Path, str, str, DataTree], tmp_path: Path
) -> None:
    """Pointing verification at a tree that holds no such document fails closed."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    elsewhere = DataTree.from_root(tmp_path / "other-data")
    with connect(database) as connection, pytest.raises(GateFailureError, match="missing"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=elsewhere, explicit=_explicit()
        )


def test_verification_fails_closed_when_the_document_path_is_a_directory(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A directory standing where the document belongs is refused, not read."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.unlink()
    path.mkdir()
    with connect(database) as connection, pytest.raises(GateFailureError, match="regular file"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_verification_fails_closed_on_an_empty_document(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """A truncated document is refused rather than treated as absent-but-fine."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.write_bytes(b"")
    with connect(database) as connection, pytest.raises(GateFailureError, match="empty"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_verification_fails_closed_on_malformed_document_json(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Bytes that are not the canonical document are refused whatever they parse as."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.write_text("{ this is not json", encoding="utf-8")
    with connect(database) as connection, pytest.raises(GateFailureError, match="byte-identically"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_verification_fails_closed_on_a_semantically_equivalent_rewrite(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Byte preservation is required: an equivalent document with different bytes fails."""
    database, _, _, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    equivalent = json.dumps(json.loads(manifest.canonical_json), sort_keys=True, indent=4) + "\n"
    assert json.loads(equivalent) == json.loads(manifest.canonical_json)
    assert equivalent != manifest.canonical_json
    path.write_text(equivalent, encoding="utf-8")
    with connect(database) as connection, pytest.raises(GateFailureError, match="byte-identically"):
        store.verify_pilot_manifest(
            connection, manifest.identity.manifest_id, data_tree=tree, explicit=_explicit()
        )


def test_replay_requires_the_serialized_document(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Replay reads, reconstructs, compares -- including the document -- and returns."""
    database, _, run_id, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    path.unlink()
    with (
        connect(database, writer=True) as connection,
        pytest.raises(GateFailureError, match="missing"),
    ):
        store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
        )


def test_atomicity_leaves_no_orphan_file_when_the_write_itself_faults(
    catalog: tuple[Path, str, str, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A fault raised *after* the bytes reach disk still leaves no row and no file.

    The earlier atomicity test injects before any byte is written. This one writes the
    document and then fails, which is the window a flag set only after a successful write
    would leave open: the transaction rolls back while the file survives.
    """
    database, _, run_id, tree = catalog
    original = Path.write_text

    def exploding(self: Path, *args: Any, **kwargs: Any) -> int:
        written = original(self, *args, **kwargs)
        if self.name.startswith("pilot_manifest_"):
            message = "injected post-write fault"
            raise OSError(message)
        return written

    with connect(database, writer=True) as connection:
        store.seal_selection_result(connection, run_id)
        monkeypatch.setattr(Path, "write_text", exploding)
        with pytest.raises(OSError, match="injected post-write fault"):
            store.build_and_persist_pilot_manifest(
                connection,
                run_id,
                data_tree=tree,
                explicit=_explicit(),
                generated_at_utc=_GENERATED_AT,
            )
        monkeypatch.undo()
        assert connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0] == 0
    directory = tree.releases / "pilot"
    assert not directory.exists() or not list(directory.glob("pilot_manifest_*.json"))


def test_atomicity_never_deletes_a_pre_existing_document(
    catalog: tuple[Path, str, str, DataTree], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A document that already existed is left alone when a later write faults."""
    database, _, run_id, tree = catalog
    manifest = _seal_and_build(catalog)
    path = tree.releases / "pilot" / pm.manifest_filename(manifest.root_manifest_sha256)
    assert path.exists()
    original = Path.write_text

    def exploding(self: Path, *args: Any, **kwargs: Any) -> int:
        if self.name.startswith("pilot_manifest_"):
            message = "injected fault"
            raise OSError(message)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", exploding)
    # An ordinal-2 manifest over the same run resolves to the same content-derived
    # filename, so the pre-existing document is in the cleanup path's way.
    with (
        connect(database, writer=True) as connection,
        pytest.raises(OSError, match="injected fault"),
    ):
        store.build_and_persist_pilot_manifest(
            connection,
            run_id,
            data_tree=tree,
            explicit=_explicit(),
            generated_at_utc=_GENERATED_AT,
            ordinal_version=2,
        )
    monkeypatch.undo()
    assert path.exists(), "a pre-existing document was deleted by another write's rollback"
    assert path.read_text(encoding="utf-8") == manifest.canonical_json


def test_manifest_requires_the_run_to_reconstruct(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Decision 021 section 12: nothing stored is trusted that was not re-derived.

    A selected-entity row altered out of band no longer follows from the run's frozen
    inputs, so the accepted S5 reconstruction refuses it and no manifest is built.
    """
    database, _, run_id, tree = catalog
    raw = sqlite3.connect(_require_scratch_catalog(database), isolation_level=None)
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            ("pilot_selected_entities_update_guard",),
        ).fetchone()
        raw.execute("DROP TRIGGER pilot_selected_entities_update_guard")
        try:
            raw.execute(
                "UPDATE pilot_selected_entities SET entity_hash_sha256 = ? "
                "WHERE selected_order = 1",
                (_hex("forged-entity"),),
            )
        finally:
            raw.execute(str(definition[0]))
    finally:
        raw.close()
    with connect(database, writer=True) as connection, pytest.raises(GateFailureError):
        store.seal_selection_result(connection, run_id)


def test_manifest_refuses_a_snapshot_whose_declared_counts_disagree(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Crosswalk item 74's source is the declaration, and it must match the rows."""
    database, snapshot_id, run_id, tree = catalog
    raw = sqlite3.connect(_require_scratch_catalog(database), isolation_level=None)
    try:
        raw.execute("PRAGMA foreign_keys = ON")
        definition = raw.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'trigger' AND name = ?",
            ("pilot_snapshot_frozen_fields_immutable",),
        ).fetchone()
        raw.execute("DROP TRIGGER pilot_snapshot_frozen_fields_immutable")
        try:
            raw.execute(
                "UPDATE pilot_candidate_snapshots SET entity_count = entity_count + 1 "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
        finally:
            raw.execute(str(definition[0]))
    finally:
        raw.close()
    with (
        connect(database, writer=True) as connection,
        pytest.raises(GateFailureError, match="declares"),
    ):
        store.seal_selection_result(connection, run_id)


def test_document_carries_the_declared_candidate_counts(
    catalog: tuple[Path, str, str, DataTree],
) -> None:
    """Block 13 renders the snapshot's declared counts and no unnamed extra count."""
    database, snapshot_id, _, _ = catalog
    manifest = _seal_and_build(catalog)
    counts = manifest.document["historical_reconstruction"]["candidate_table_row_counts"]
    with connect(database) as connection:
        declared = connection.execute(
            "SELECT entity_count, accession_count FROM pilot_candidate_snapshots "
            "WHERE snapshot_id = ?",
            (snapshot_id,),
        ).fetchone()
    assert counts == {
        "pilot_candidate_entities": declared[0],
        "pilot_candidate_accessions": declared[1],
    }
    assert "pilot_candidate_accession_registrants" not in counts


def test_document_carries_the_as_of_time_zone(catalog: tuple[Path, str, str, DataTree]) -> None:
    """Crosswalk item 14 is a class-T value and must be serialized, not merely bound."""
    manifest = _seal_and_build(catalog)
    assert manifest.document["candidate_snapshot"]["as_of_timezone"] == SEC_TIMEZONE_NAME


def test_store_requires_the_enumerated_decision_authority_records() -> None:
    """Item 11's pairs are a required assertion; an unstated set is refused."""
    with pytest.raises(GateFailureError, match="decision_authority_records"):
        pm.ExplicitArguments(
            dependency_lock_sha256=_hex("lock"),
            code_commit_identifier="903f4cc",
            runtime_python_version="3.12.13",
            configuration_sha256=_hex("config"),
            decision_authority_sha256=_hex("authority"),
            source_plan_sha256=_hex("plan"),
            decision_authority_records=(),
        )
