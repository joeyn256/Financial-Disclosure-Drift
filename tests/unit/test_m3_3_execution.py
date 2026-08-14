"""M3.3-I/R execution tests: the world, the tracks, the R28 bridge, and I7.

Every test here drives production code over a disposable synthetic catalog. Nothing
stubs the builder, the selector, the store, the seal, or the manifest, and nothing
touches the accepted real private catalog.

Governing records exercised: accepted Decisions 070-074, in particular **R27**-**R30**
(dual-track rehearsal, the bridge, and the two real-path gates), **R31** (reserve
rehearsal totality), **R33** (same-build cohort-boundary derivation), and **R34**
(acceptance-date ordering).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.m3 import candidate_snapshot as cs
from disclosure_drift.m3 import execution_rehearsal as er
from disclosure_drift.m3 import offline_execution as ox
from disclosure_drift.m3 import rehearsal_snapshot as rsnap
from disclosure_drift.m3 import rehearsal_world as rw
from disclosure_drift.paths import DataTree
from disclosure_drift.sec.accession_selection_store import (
    JointSelectionRunIdentity,
    load_frozen_joint_candidates,
)
from disclosure_drift.sec.accession_selector import (
    APPROVED_DEFERRED_QUOTA_KEYS,
    CROSS_CUTTING_QUOTAS,
    QUOTA_KEY_LINKED_AMENDMENT_ENTITIES,
)
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import connect, transaction

_INPUTS = er._INPUTS


# ==========================================================================
# Group A: the synthetic world and Track A, over the real production path
# ==========================================================================


@pytest.fixture(scope="module")
def world(tmp_path_factory: pytest.TempPathFactory) -> Iterator[rw.RehearsalWorld]:
    """One materialized base case, derived by the real offline parse."""
    root = tmp_path_factory.mktemp("m3_3_world")
    yield rw.build_rehearsal_world(
        tree=DataTree.from_root(root / "data"),
        database=root / "source.sqlite3",
        lock_root=root / "locks",
    )


@pytest.fixture(scope="module")
def paired(
    world: rw.RehearsalWorld, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[rsnap.PairedSnapshots]:
    """The paired Track-A / Track-B construction over that base case."""
    root = tmp_path_factory.mktemp("m3_3_paired")
    yield rsnap.build_paired_snapshots(
        source_database=world.database,
        track_a_database=root / "a.sqlite3",
        track_b_database=root / "b.sqlite3",
        lock_root=root / "locks",
        inputs=_INPUTS,
    )


def test_the_world_is_derived_by_the_offline_parse_without_a_request(
    world: rw.RehearsalWorld,
) -> None:
    record = world.parse_report.as_record()
    assert record["requests_made"] == 0
    assert record["transports_constructed"] == 0
    assert record["required_parse"] > 0
    assert world.census_registrant_count == 24


def test_every_planned_source_receives_exactly_one_r18_disposition(
    world: rw.RehearsalWorld,
) -> None:
    report = world.parse_report
    assert report.is_complete
    counted = (
        len(report.by_disposition("E0_REQUIRED_PARSE"))
        + len(report.by_disposition("E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"))
        + len(report.by_disposition("E0_NOT_REQUIRED_VALIDATION_OR_PROVENANCE_ONLY"))
    )
    assert counted == report.planned_source_count


def test_a_category_c_source_is_left_deliberately_untouched(world: rw.RehearsalWorld) -> None:
    with connect(world.database, writer=False) as connection:
        state = connection.execute(
            "SELECT parser_state FROM census_plan_sources WHERE source_id = "
            "'sec_edgar_filing_calendar'"
        ).fetchone()
    assert state["parser_state"] == "not_started"


def test_the_candidate_form_universe_is_the_reference_family(
    world: rw.RehearsalWorld, paired: rsnap.PairedSnapshots
) -> None:
    """IMP-3: an unrelated ``10-D`` census row must not fail the builder closed.

    Proved directly on all three sides rather than inferred from a passing build: the
    row **exists** in the census / source-history layer, it **never** becomes a
    ``pilot_candidate_accessions`` row, and its exclusion is **reported** by form with
    the expected deterministic count (CLAUDE.md rule 11). **R20** §6.2 still reads the
    same row as source-history evidence, so the bound is on the candidate universe
    only -- it does not blind the control predicates.
    """
    with connect(world.database, writer=False) as connection:
        census = connection.execute(
            "SELECT accession_plain, registrant_cik_numeric FROM census_accessions "
            "WHERE form_type = '10-D' ORDER BY accession_plain"
        ).fetchall()
    assert len(census) == 1
    plain = str(census[0]["accession_plain"])
    anchor = int(census[0]["registrant_cik_numeric"])

    for snapshot, database in (
        (paired.track_a, paired.track_a_database),
        (paired.track_b, paired.track_b_database),
    ):
        assert snapshot.excluded_form_counts["10-D"] == 1
        with connect(database, writer=False) as connection:
            excluded = connection.execute(
                "SELECT COUNT(*) FROM pilot_candidate_accessions "
                "WHERE snapshot_id = ? AND (accession_plain = ? OR form_type = '10-D')",
                (snapshot.snapshot_id, plain),
            ).fetchone()[0]
            asset_backed = connection.execute(
                "SELECT COUNT(*) FROM pilot_candidate_entities WHERE snapshot_id = ? "
                "AND cik_numeric = ? AND control_kind = 'asset_backed_issuer'",
                (snapshot.snapshot_id, anchor),
            ).fetchone()[0]
        assert excluded == 0
        assert asset_backed == 1


def test_track_a_is_infeasible_on_amendment_purpose_and_nothing_else(
    paired: rsnap.PairedSnapshots, tmp_path: Path
) -> None:
    """Decision 073 §1: the expected builder-derived disposition, proved mechanically."""
    with CatalogWriter(paired.track_a_database, tmp_path / "locks") as writer:
        outcome = ox.execute_selection(
            writer=writer,
            inputs=ox.ExecutionInputs(
                snapshot_id=paired.track_a.snapshot_id,
                node_limit=er.TEST_ONLY_NODE_LIMIT,
                occurred_at_utc="2026-01-01T00:00:00Z",
                event_id="evt-a",
            ),
        )
    assert outcome.persisted.run_state == "infeasible"
    binding = tuple(
        item.key
        for item in outcome.persisted.result.accession_quota_results
        if item.binding_constraint
    )
    assert binding == ("amendment_purpose_categories",)


def test_the_operating_financial_quota_is_reachable(paired: rsnap.PairedSnapshots) -> None:
    """IMP-1: Decision 016 §2 keeps quota and universe eligibility independent."""
    with connect(paired.track_b_database, writer=False) as connection:
        rows = connection.execute(
            "SELECT industry_quota_eligible, primary_universe_eligible, engineering_only_stress "
            "FROM pilot_candidate_entities WHERE industry_family = "
            "'operating_financial_institutions' AND candidate_category = 'operating'"
        ).fetchall()
    assert rows
    for row in rows:
        assert row["industry_quota_eligible"] == 1
        assert row["primary_universe_eligible"] == 0
        assert row["engineering_only_stress"] == 1


# ==========================================================================
# Group B: R28 - the bridge, including adversarial differences
# ==========================================================================


def test_the_bridge_passes_with_only_amendment_purpose_differences(
    paired: rsnap.PairedSnapshots,
) -> None:
    assert paired.bridge.passed
    assert paired.bridge.violations == ()
    assert paired.bridge.differences
    changed = {
        item.field for item in paired.bridge.differences if item.scope.endswith("accessions")
    }
    assert changed <= rsnap.BRIDGE_ALLOWED_ACCESSION_COLUMNS


def test_the_bridge_covers_every_candidate_family(paired: rsnap.PairedSnapshots) -> None:
    assert set(paired.bridge.compared_scopes) == {
        "pilot_candidate_entities",
        "pilot_candidate_accessions",
        "pilot_candidate_accession_registrants",
        "pilot_candidate_entity_evidence",
        "pilot_candidate_accession_evidence",
        "reasons",
        "snapshot",
    }
    assert paired.bridge.compared_rows > 0


@pytest.mark.parametrize(
    ("statement", "field"),
    [
        (
            "UPDATE census_registrant_observations SET value_text = 'Accelerated filer' "
            "WHERE observation_kind = 'filing_status' AND cik_numeric = 1",
            "size_stratum",
        ),
        (
            "UPDATE census_accessions SET inline_xbrl_flag = 1 - inline_xbrl_flag "
            "WHERE accession_plain = (SELECT MIN(accession_plain) FROM census_accessions)",
            "has_inline_xbrl",
        ),
        (
            "UPDATE census_accession_observations SET raw_value_json = '\"9999999999\"' "
            "WHERE field_name = 'cik_padded' AND accession_plain = "
            "(SELECT MIN(accession_plain) FROM census_accession_observations "
            "WHERE field_name = 'cik_padded')",
            "multi_registrant",
        ),
    ],
)
def test_the_bridge_fails_on_any_unrelated_difference(
    world: rw.RehearsalWorld,
    paired: rsnap.PairedSnapshots,
    tmp_path: Path,
    statement: str,
    field: str,
) -> None:
    """**R28** is an explicit allowlist: an unrelated difference must fail the bridge.

    The divergence is introduced in the **census input** and the Track-B snapshot is then
    rebuilt from it, because a frozen snapshot refuses mutation outright. That is the
    adversarial case the bridge exists to catch: a Track B quietly built over a different
    candidate universe.
    """
    source = tmp_path / "diverged.sqlite3"
    er._copy(world.database, source)
    with connect(source, writer=True) as connection, transaction(connection) as active:
        active.execute(statement)
    with CatalogWriter(source, tmp_path / "locks") as writer:
        base = cs.derive_candidate_snapshot(writer.connection, _INPUTS)
        overlaid, _ = rsnap.apply_synthetic_amendment_purpose(base)
        frozen = cs.persist_and_freeze_derivation(
            writer=writer, inputs=_INPUTS, derivation=overlaid
        )
    report = rsnap.compare_tracks(
        paired.track_a_database,
        source,
        snapshot_a=paired.track_a.snapshot_id,
        snapshot_b=frozen.snapshot_id,
    )
    assert not report.passed
    assert any(item.field == field for item in report.violations), [
        item.field for item in report.violations
    ]


def test_the_production_builder_cannot_reach_the_overlay() -> None:
    """Decision 073 §7: the injection path is mechanically unreachable from production."""
    import subprocess
    import sys

    probe = (
        "import sys, importlib;"
        "importlib.import_module('disclosure_drift.m3.candidate_snapshot');"
        "print([m for m in sys.modules if 'rehearsal' in m])"
    )
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe], capture_output=True, text=True, check=True
    )
    assert result.stdout.strip() == "[]"
    builder = Path(cs.__file__).read_text(encoding="utf-8")
    assert "rehearsal_snapshot" not in builder
    assert rsnap.SYNTHETIC_REHEARSAL_ONLY not in builder


def test_the_overlay_refuses_a_category_outside_the_frozen_three(
    world: rw.RehearsalWorld,
) -> None:
    with connect(world.database, writer=False) as connection:
        derivation = cs.derive_candidate_snapshot(connection, _INPUTS)
    with pytest.raises(GateFailureError, match="three frozen"):
        rsnap.apply_synthetic_amendment_purpose(derivation, categories=("invented_category",))


def test_the_overlay_touches_only_amendment_accessions(world: rw.RehearsalWorld) -> None:
    with connect(world.database, writer=False) as connection:
        derivation = cs.derive_candidate_snapshot(connection, _INPUTS)
    overlaid, stipulated = rsnap.apply_synthetic_amendment_purpose(derivation)
    by_plain = {str(item.columns["accession_plain"]): item.columns for item in overlaid.accessions}
    assert stipulated
    assert set(stipulated) <= {plain for plain, row in by_plain.items() if row["is_amendment"]}
    assert set(stipulated.values()) == set(cs.classify.AMENDMENT_PURPOSE_CATEGORIES)


# ==========================================================================
# Group C: R33 - the same-build cohort-boundary derivation
# ==========================================================================


@pytest.mark.parametrize(
    ("filing", "acceptance", "expected", "unknown"),
    [
        ("2015-03-01", "2015-03-01", 0, False),
        ("2021-12-29", "2022-01-03", 1, False),
        ("2023-12-29", "2024-01-03", 1, False),
        ("2024-12-30", "2025-01-03", 1, False),
        ("2025-12-30", "2026-01-03", 1, False),
        ("2010-01-01", "2024-06-01", 1, False),
        ("2009-03-01", "2009-03-02", 0, False),
        (None, "2015-03-01", 1, True),
        ("2015-03-01", None, 1, True),
        ("2015-03-01", "not-a-date", 1, True),
    ],
)
def test_the_cohort_boundary_is_derived_from_this_builds_own_facts(
    filing: str | None, acceptance: str | None, expected: int, unknown: bool
) -> None:
    """**R33**: same-build derivation; an unknown label is never a silent "no crossing"."""
    _, _, ambiguous, is_unknown = cs._cohort_boundary(filing, acceptance)
    assert ambiguous == expected
    assert is_unknown is unknown


def test_the_cohort_boundary_derivation_is_order_invariant() -> None:
    first = cs._cohort_boundary("2021-12-29", "2022-01-03")
    second = cs._cohort_boundary("2021-12-29", "2022-01-03")
    assert first == second
    swapped = cs._cohort_boundary("2022-01-03", "2021-12-29")
    assert swapped[2] == 1


def test_the_two_tracks_agree_on_every_cohort_boundary(paired: rsnap.PairedSnapshots) -> None:
    """**R33** with **R28**: the derived value must be identical on both sides."""

    def flags(database: Path, snapshot_id: str) -> dict[str, int]:
        with connect(database, writer=False) as connection:
            return {
                str(row["accession_plain"]): int(row["cohort_ambiguous"])
                for row in connection.execute(
                    "SELECT accession_plain, cohort_ambiguous FROM pilot_candidate_accessions "
                    "WHERE snapshot_id = ?",
                    (snapshot_id,),
                ).fetchall()
            }

    assert flags(paired.track_a_database, paired.track_a.snapshot_id) == flags(
        paired.track_b_database, paired.track_b.snapshot_id
    )


def test_a_boundary_crossing_accession_is_not_base_eligible(
    paired: rsnap.PairedSnapshots,
) -> None:
    with connect(paired.track_b_database, writer=False) as connection:
        rows = connection.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accessions "
            "WHERE cohort_ambiguous = 1 AND base_eligible = 1"
        ).fetchone()[0]
    assert rows == 0


# ==========================================================================
# Group D: R32 / R34 - linkage and acceptance ordering
# ==========================================================================


def test_the_linked_amendment_quota_is_hard_and_not_deferred() -> None:
    """**R32**: the quota is never deferred; only its real evidence path is gated."""
    assert CROSS_CUTTING_QUOTAS[QUOTA_KEY_LINKED_AMENDMENT_ENTITIES] == 8
    assert QUOTA_KEY_LINKED_AMENDMENT_ENTITIES not in APPROVED_DEFERRED_QUOTA_KEYS


def test_no_accepted_source_field_resolves_amendment_relationship() -> None:
    """**R32**'s mechanical basis, asserted against the accepted map rather than prose."""
    from disclosure_drift.sec.census import CANONICAL_FIELD_BY_SOURCE_FIELD

    assert "amendment_relationship" not in set(CANONICAL_FIELD_BY_SOURCE_FIELD.values())


@pytest.mark.parametrize(
    ("value", "resolves"),
    [
        ("20200301170000", True),
        ("2020-03-01T17:00:00.000Z", False),
        ("", False),
        ("2020030117", False),
        ("20201301170000", False),
    ],
)
def test_acceptance_parsing_stays_strict(value: str, resolves: bool) -> None:
    """**R34**: strict parsing is retained; a malformed value never becomes a date."""
    from disclosure_drift.sec.temporal import TemporalPolicyError, acceptance_date_sec

    if resolves:
        assert acceptance_date_sec(value).isoformat() == "2020-03-01"
    else:
        with pytest.raises(TemporalPolicyError):
            acceptance_date_sec(value)


# ==========================================================================
# Group E: I7 - selection, pairs, reconstruction, replay, seal, manifest
# ==========================================================================


@pytest.fixture(scope="module")
def executed(
    paired: rsnap.PairedSnapshots, tmp_path_factory: pytest.TempPathFactory
) -> Iterator[tuple[Path, ox.SelectionOutcome]]:
    """One feasible persisted Track-B run, reused by the downstream tests."""
    root = tmp_path_factory.mktemp("m3_3_executed")
    database = root / "run.sqlite3"
    er._copy(paired.track_b_database, database)
    with CatalogWriter(database, root / "locks") as writer:
        outcome = ox.execute_selection(
            writer=writer,
            inputs=ox.ExecutionInputs(
                snapshot_id=paired.track_b.snapshot_id,
                node_limit=er.TEST_ONLY_NODE_LIMIT,
                occurred_at_utc="2026-01-01T00:00:00Z",
                event_id="evt-b",
            ),
        )
    yield database, outcome


def test_the_rehearsal_snapshot_reaches_a_feasible_selection(
    executed: tuple[Path, ox.SelectionOutcome],
) -> None:
    _, outcome = executed
    assert outcome.feasible
    assert outcome.persisted.selected_entity_count == 24


def test_the_pair_quota_counts_six_distinct_entities(
    executed: tuple[Path, ox.SelectionOutcome],
) -> None:
    """Decision 071 IN-3: a pair is a property of the joint result, counted per entity."""
    _, outcome = executed
    assert outcome.pairs.satisfied
    assert len(outcome.pairs.entities) == 6
    assert len(set(outcome.pairs.entities)) == 6


def test_replay_is_write_free_to_the_r3_standard(
    executed: tuple[Path, ox.SelectionOutcome],
) -> None:
    database, outcome = executed
    proof = ox.replay_selection_write_free(database, outcome.persisted.selection_run_id, replays=3)
    assert proof.write_free
    assert proof.strictly_read_only
    assert proof.digest_before == proof.digest_after


@pytest.mark.parametrize("component", sorted(JointSelectionRunIdentity.__dataclass_fields__))
def test_every_governed_identity_component_is_refused_when_corrupted(
    executed: tuple[Path, ox.SelectionOutcome], tmp_path: Path, component: str
) -> None:
    """Obligation C: mutate every governed component independently and prove refusal."""
    database, outcome = executed
    columns = {
        "snapshot_id": ("snapshot_id", "0" * 64),
        "selection_seed": ("selection_seed", "not-the-frozen-seed"),
        "selector_policy_version": ("selector_policy_version", "not-a-policy/9.9"),
        "quota_policy_version": ("quota_policy_version", "not-a-policy/9.9"),
        "node_limit": ("search_node_limit", er.TEST_ONLY_NODE_LIMIT + 1),
        "selection_input_sha256": ("selection_input_sha256", "1" * 64),
        "selection_run_id": ("selection_run_id", "2" * 64),
    }
    column, value = columns[component]
    corrupted = tmp_path / f"corrupt-{component}.sqlite3"
    er._copy(database, corrupted)
    assert (
        er._corruption_refused(corrupted, outcome.persisted.selection_run_id, column, value)
        is not None
    )


def test_the_seal_and_manifest_replay_to_an_identical_root(
    executed: tuple[Path, ox.SelectionOutcome], tmp_path: Path
) -> None:
    database, outcome = executed
    working = tmp_path / "manifest.sqlite3"
    er._copy(database, working)
    tree = DataTree.from_root(tmp_path / "data")
    with CatalogWriter(working, tmp_path / "locks") as writer:
        result = ox.seal_and_replay_manifest(
            writer=writer,
            selection_run_id=outcome.persisted.selection_run_id,
            data_tree=tree,
            explicit=er.test_only_explicit_arguments(),
            generated_at_utc="2026-01-01T00:00:00Z",
        )
    assert result.identical_root_on_replay
    assert result.document_bytes_identical
    assert len(result.selection_result_sha256) == 64


# ==========================================================================
# Group F: R31 - reserve totality
# ==========================================================================


def test_the_positive_reserve_path_yields_exactly_one_rank_one_package() -> None:
    """**R31** E5(a): the compatible path, proved at the pure reserve layer."""
    probe = er._Probe()
    er._run_e5_positive_reserve_path(probe)
    assert probe.passed, probe.detail


def test_a_no_compatible_reserve_disposition_is_nonblocking(
    executed: tuple[Path, ox.SelectionOutcome],
) -> None:
    """**R31**: a disposition is lawful, durable, and not selection infeasibility."""
    database, outcome = executed
    shape = er._reserve_shape(database, outcome.persisted.selection_run_id)
    assert outcome.persisted.run_state == "feasible"
    assert shape["targets"] == shape["packages"] + shape["dispositions"]
    assert shape["overlap"] == 0
    assert shape["invented_ranks"] == 0


# ==========================================================================
# Group G: boundaries, receipts, and rendered output
# ==========================================================================


def test_the_test_only_node_limit_is_not_a_production_value() -> None:
    """OR-7 stays deferred: the rehearsal value reaches no configuration or default."""
    from disclosure_drift import config as config_module

    assert er.TEST_ONLY_NODE_LIMIT != 0
    for module in (config_module, cs):
        assert str(er.TEST_ONLY_NODE_LIMIT) not in Path(module.__file__).read_text(encoding="utf-8")
    assert "node_limit" not in Path("configs/project.yaml").read_text(encoding="utf-8")


def test_no_execution_module_imports_a_transport() -> None:
    """Contract §10.2 item 8, proved by test rather than asserted."""
    for module in (ox, er, rsnap, rw):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for prohibited in ("import socket", "import httpx", "import urllib", "http_client"):
            assert prohibited not in source


def test_the_rehearsal_never_reads_the_environment() -> None:
    """``EV_ROOT`` is named only in prohibitions: no module here reads any environment."""
    import ast

    for module in (ox, er, rsnap, rw):
        tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
        names = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)} | {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        assert not names & {"environ", "getenv", "environb"}


@pytest.mark.parametrize(
    "argv",
    [
        ["disclosure-drift", "m3", "rehearse-execution", "--scenarios", "all"],
        ["disclosure-drift", "m3", "manifest-output"],
    ],
)
def test_the_command_invocation_field_renders(argv: list[str]) -> None:
    """Crosswalk item 80, delivered here (Decision 021 §16)."""
    assert ox.render_command_invocation(argv) == " ".join(argv)


@pytest.mark.parametrize(
    "argv",
    [
        ["disclosure-drift", "m3", "offline-parse", "--catalog", "/absolute/private.sqlite3"],
        ["disclosure-drift", "m3", "offline-parse", "--root", "~/evidence"],
        ["disclosure-drift", "m3", "offline-parse", "--url", "https://www.sec.gov/x"],
        [],
    ],
)
def test_the_command_invocation_field_refuses_a_path_or_an_sec_identity(
    argv: list[str],
) -> None:
    with pytest.raises(GateFailureError):
        ox.render_command_invocation(argv)


def test_the_offline_execution_policy_versions_come_from_their_owning_constants() -> None:
    from disclosure_drift import pilot_policy

    versions = ox.offline_execution_policy_versions()
    assert versions["quota_policy_version"] == pilot_policy.PILOT_QUOTA_POLICY_VERSION
    assert (
        versions["joint_selector_policy_version"]
        == pilot_policy.PILOT_JOINT_SELECTOR_POLICY_VERSION
    )
    assert len(ox.cohort_definition_digest()) == 64


def test_the_execution_rehearsal_report_never_claims_real_feasibility() -> None:
    """Both real-path gates are generated separately, by name, and never merged.

    Decision 073 **R30** and Decision 074 **R32** are independently governed and
    independently auditable, and `real_builder_feasibility_proved` is a third, separate
    claim that neither gate stands in for (Decision 075 §6).
    """
    report = er.ExecutionRehearsalReport(
        outcomes=(),
        builder_derived_disposition="INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE",
        accepted_selector_feasible_on_rehearsal_snapshot=True,
        bridge={},
    )
    payload = json.loads(report.canonical_bytes())
    assert payload["real_builder_feasibility_proved"] is False
    assert payload["real_amendment_purpose_feasibility_gate"] == "OPEN"
    assert payload["real_linked_amendment_feasibility_gate"] == "OPEN"
    assert payload["real_private_parse_authorization"] == "NO"
    assert payload["actual_network_requests"] == 0

    # No merged or generic substitute stands in for either named gate.
    assert "real_feasibility_gate" not in payload
    gates = {key for key in payload if key.endswith("_feasibility_gate")}
    assert gates == {
        "real_amendment_purpose_feasibility_gate",
        "real_linked_amendment_feasibility_gate",
    }
    # Additive completion of an already-governed status block: the report schema version
    # is deliberately NOT bumped (Decision 075 §6.1).
    assert payload["report_schema_version"] == "m3-3a-execution-rehearsal-report/1.0"


def test_every_track_b_scenario_declares_the_governed_feasibility_source() -> None:
    """**R29**: a Track-B outcome may never claim builder-derived feasibility."""
    assert er.FEASIBILITY_SOURCE_REHEARSAL == "EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT"
    assert set(er.SCENARIO_IDS) == {"E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"}
    assert tuple(er.scenario_titles()) == er.SCENARIO_IDS


def test_an_unknown_scenario_is_refused() -> None:
    with pytest.raises(er.ExecutionRehearsalError, match="unknown execution-rehearsal scenario"):
        er.run_execution_rehearsal(["E9"], workspace_root=Path())


# ==========================================================================
# Group H: OBS-H - full-index corroboration and disagreement
# ==========================================================================


def test_full_index_corroboration_reaches_the_registrant_rows(
    paired: rsnap.PairedSnapshots,
) -> None:
    """**R23**: co-registrants come from accepted ``company.idx`` rows and nowhere else."""
    with connect(paired.track_b_database, writer=False) as connection:
        associated = connection.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accession_registrants WHERE role = 'associated'"
        ).fetchone()[0]
        flagged = connection.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accessions WHERE multi_registrant = 1"
        ).fetchone()[0]
    assert associated == 2
    assert flagged == 2


def test_a_full_index_disagreement_is_a_diagnostic_not_an_overwrite(
    world: rw.RehearsalWorld, tmp_path: Path
) -> None:
    """OBS-H: Decision 012 gives the index level 3, so it never overwrites level 2.

    The index's ``date_filed`` is changed to a value the submissions document contradicts.
    The authoritative filing date must be unchanged, and the conflicting observation must
    still be recorded rather than dropped.
    """
    target = tmp_path / "disagreement.sqlite3"
    er._copy(world.database, target)
    with connect(target, writer=False) as connection:
        row = connection.execute(
            "SELECT o.accession_plain, o.raw_value_json FROM census_accession_observations AS o "
            "JOIN census_source_observations AS s ON s.observation_id = o.source_observation_id "
            "WHERE o.field_name = 'date_filed' AND s.source_id = 'sec_full_index_company' "
            "ORDER BY o.accession_plain LIMIT 1"
        ).fetchone()
        assert row is not None
        plain = str(row["accession_plain"])
        authoritative = connection.execute(
            "SELECT resolved_value FROM census_accession_field_resolutions "
            "WHERE accession_plain = ? AND field_name = 'official_filing_date'",
            (plain,),
        ).fetchone()["resolved_value"]
    with connect(target, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_accession_observations SET raw_value_json = '\"1999-01-01\"' "
            "WHERE accession_plain = ? AND field_name = 'date_filed'",
            (plain,),
        )
    with CatalogWriter(target, tmp_path / "locks") as writer:
        frozen = cs.build_and_freeze_candidate_snapshot(writer=writer, inputs=_INPUTS)
    with connect(target, writer=False) as connection:
        candidate = connection.execute(
            "SELECT official_filing_date FROM pilot_candidate_accessions "
            "WHERE snapshot_id = ? AND accession_plain = ?",
            (frozen.snapshot_id, plain),
        ).fetchone()
        retained = connection.execute(
            "SELECT COUNT(*) FROM census_accession_observations "
            "WHERE accession_plain = ? AND raw_value_json = '\"1999-01-01\"'",
            (plain,),
        ).fetchone()[0]
    assert candidate["official_filing_date"] == authoritative
    assert int(retained) == 1


# ==========================================================================
# Group I: freeze validations (obligation B)
# ==========================================================================


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (er._corrupt_dashed_form, "disagrees with the canonical dashed form"),
        (er._corrupt_registrant_cik, "not the canonical rendering"),
        (er._remove_company_name, "filing_time_name"),
        (er._corrupt_full_index_cik, "non-canonical CIK"),
        (er._orphan_accession_anchor, "no accepted registrant row"),
    ],
)
def test_each_freeze_obligation_fails_for_its_own_reason(
    world: rw.RehearsalWorld,
    tmp_path: Path,
    mutate: object,
    expected: str,
) -> None:
    """Obligation B: one violated obligation per fixture, each non-vacuous."""
    target = tmp_path / "freeze.sqlite3"
    er._copy(world.database, target)
    with connect(target, writer=True) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        with transaction(connection) as active:
            mutate(active)  # type: ignore[operator]
    observed = er._refusal(target, tmp_path)
    assert observed is not None
    assert expected in observed


def test_a_rebuild_in_the_same_catalog_fails_closed(
    paired: rsnap.PairedSnapshots, tmp_path: Path
) -> None:
    """OQ-3: never ``INSERT OR REPLACE``, never a silent recognize-and-return."""
    target = tmp_path / "rebuild.sqlite3"
    er._copy(paired.track_a_database, target)
    observed = er._refusal(target, tmp_path)
    assert observed is not None
    assert "already exists" in observed


def test_a_building_snapshot_at_entry_blocks(world: rw.RehearsalWorld, tmp_path: Path) -> None:
    """**R5**: a ``building`` row is nonauthoritative and blocks pending owner disposition."""
    target = tmp_path / "building.sqlite3"
    er._copy(world.database, target)
    with connect(target, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
            "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
            "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
            "coverage_window_sha256, input_observation_set_sha256, snapshot_state, "
            "created_at_utc, detail) VALUES (?, ?, '2009-01-01', '2026-06-30', '2026-06-30', 0, "
            "'pilot-coverage/1.0', 'pilot-candidate/1.0', 'sic-family-mapping/0.2', "
            "'pilot-evidence/1.0', ?, ?, 'building', '2026-01-01T00:00:00Z', '')",
            ("9" * 64, rw.CENSUS_RUN_ID, "8" * 64, "7" * 64),
        )
    observed = er._refusal(target, tmp_path)
    assert observed is not None
    assert "building candidate snapshot is present at entry" in observed


def test_the_loader_accepts_every_frozen_track_b_row(paired: rsnap.PairedSnapshots) -> None:
    """The accepted Decision-019 loader validates the frozen snapshot end to end."""
    with connect(paired.track_b_database, writer=False) as connection:
        loaded = load_frozen_joint_candidates(connection, paired.track_b.snapshot_id)
    assert loaded.entity_count == 24
    assert len(loaded.accessions) == loaded.accession_count


def test_a_declared_count_cannot_drift_from_the_frozen_rows(
    paired: rsnap.PairedSnapshots, tmp_path: Path
) -> None:
    target = tmp_path / "counts.sqlite3"
    er._copy(paired.track_b_database, target)
    with (
        pytest.raises(sqlite3.IntegrityError),
        connect(target, writer=True) as connection,
        transaction(connection) as active,
    ):
        active.execute(
            "UPDATE pilot_candidate_snapshots SET entity_count = entity_count + 1 "
            "WHERE snapshot_id = ?",
            (paired.track_b.snapshot_id,),
        )


# ==========================================================================
# Group J: the whole rehearsal, and the CLI surface (obligations F and G)
# ==========================================================================


def test_the_whole_execution_rehearsal_passes(tmp_path: Path) -> None:
    """All eight scenarios run, none skipped, and the report claims no real feasibility."""
    report = er.run_execution_rehearsal(workspace_root=tmp_path)
    failed = [item.scenario_id for item in report.outcomes if not item.passed]
    assert not failed, [(item.scenario_id, item.detail) for item in report.outcomes]
    assert report.complete
    assert report.builder_derived_disposition == "INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE"
    assert report.accepted_selector_feasible_on_rehearsal_snapshot
    assert report.bridge["violation_count"] == 0
    tracks = {item.scenario_id: item.track for item in report.outcomes}
    assert tracks == {
        "E1": "TRACK_A",
        "E2": "TRACK_A",
        "E3": "TRACK_B",
        "E4": "TRACK_A",
        "E5": "TRACK_B",
        "E6": "TRACK_B",
        "E7": "TRACK_B",
        "E8": "TRACK_B",
    }
    for outcome in report.outcomes:
        expected = (
            er.FEASIBILITY_SOURCE_BUILDER
            if outcome.track == "TRACK_A"
            else er.FEASIBILITY_SOURCE_REHEARSAL
        )
        assert outcome.feasibility_source == expected


def test_every_m3_3_real_execution_surface_refuses(tmp_path: Path) -> None:
    """Contract §19: recognized surfaces, each refusing its own unissued owner gate."""
    from disclosure_drift.cli import _M3_3_GATED_COMMANDS, main

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    for name, gate, _ in _M3_3_GATED_COMMANDS:
        assert gate in {"M3.3-E0", "M3.3-E1", "M3.3-E2"}
        assert main(["m3", name, "--evidence-root", str(evidence)]) == 3


def test_the_rehearsal_command_writes_an_offline_execution_receipt(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Obligation G: `invocation_mode = offline_execution` with zero request counts."""
    from disclosure_drift.cli import main
    from disclosure_drift.m3.receipt import inspect_receipt

    evidence = tmp_path / "evidence"
    evidence.mkdir()
    code = main(
        [
            "m3",
            "rehearse-execution",
            "--evidence-root",
            str(evidence),
            "--evidence-out",
            "report.json",
            "--receipt-out",
            "receipt.json",
        ]
    )
    assert code == 0
    printed = capsys.readouterr().out
    assert "M3_3A_EXECUTION_REHEARSAL_PASSED_NO_REAL_EXECUTION_AUTHORIZED" in printed
    assert str(tmp_path) not in printed

    # Both real-path gates are printed separately and by name, beside the distinct
    # builder-feasibility claim, and nothing merges them (Decision 075 §6.2).
    for line in (
        "real builder feasibility proved        : no",
        "real amendment-purpose feasibility gate: OPEN",
        "real linked-amendment feasibility gate : OPEN",
    ):
        assert line in printed
    assert "real feasibility gate" not in printed

    document = inspect_receipt(evidence / "receipt.json")
    assert document["invocation_mode"] == ox.OFFLINE_EXECUTION_MODE
    assert document["phase"] == "M3.3A"
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    assert document["completion_status"] == "complete"
    payload = json.loads((evidence / "report.json").read_text(encoding="utf-8"))
    assert payload["real_builder_feasibility_proved"] is False
    assert payload["real_amendment_purpose_feasibility_gate"] == "OPEN"
    assert payload["real_linked_amendment_feasibility_gate"] == "OPEN"


# ==========================================================================
# Group K: mutation-campaign survivors, closed narrowly
# ==========================================================================


def test_the_ric_etf_sic_set_is_exactly_the_two_enumerated_codes() -> None:
    """**R26**: `{6722, 6726}`, never broadened by proximity, and 6798 is excluded."""
    from disclosure_drift.m3 import candidate_controls as controls

    assert set(controls.RIC_ETF_SIC_CODES) == {"6722", "6726"}
    assert "6798" not in controls.RIC_ETF_SIC_CODES
    verdict = controls.classify_control_kind(
        controls.ControlEvidence(sic_code="6798", sic_resolved=True)
    )
    assert verdict.control_kind is None
    assert verdict.status == "not_a_control"


def test_an_amendment_alone_never_establishes_the_foreign_private_issuer_control() -> None:
    """**R20** §6.4: the **original** forms only."""
    from disclosure_drift.m3 import candidate_controls as controls

    amendment_only = controls.original_forms({"20-F/A", "40-F/A"})
    assert amendment_only == frozenset()
    verdict = controls.classify_control_kind(
        controls.ControlEvidence(submission_forms=amendment_only)
    )
    assert verdict.status == "not_a_control"
    with_original = controls.classify_control_kind(
        controls.ControlEvidence(submission_forms=controls.original_forms({"20-F/A", "20-F"}))
    )
    assert with_original.control_kind == "foreign_private_issuer"


def test_an_unusable_bound_observation_stays_category_b(tmp_path: Path) -> None:
    """**R14**: never converted into a fabricated empty parse."""
    from disclosure_drift.m3 import offline_parse as op
    from disclosure_drift.sec.snapshots import SourceObservation

    source = op.PlannedSource(
        census_run_id=rw.CENSUS_RUN_ID,
        source_instance_id="base|sec_company_tickers|0",
        source_id="sec_company_tickers",
        request_identity="req/x",
        required=True,
        source_scope="base",
        retrieval_state="retrieved",
        snapshot_state="verified",
        parser_state="not_started",
        observation_id="obs-1",
    )
    unusable = SourceObservation(
        observation_id="obs-1",
        source_id="sec_company_tickers",
        requested_url="https://example.invalid/a.json",
        purpose="census",
        retrieved_at_utc="2026-01-01T00:00:00Z",
        outcome="failed",
        storage_representation="identical",
        relative_storage_path=None,
    )
    assert not unusable.has_payload
    assert op.classify_planned_source(source, unusable) == "E0_REQUIRED_BUT_ACCEPTED_UNAVAILABLE"


def test_the_bridge_records_a_violation_rather_than_permitting_everything(
    paired: rsnap.PairedSnapshots,
) -> None:
    """**R28**: `allowed` is a decision per column, never a constant true."""
    difference = rsnap.BridgeDifference(
        scope="pilot_candidate_entities",
        key="cik_numeric=1",
        field="size_stratum",
        track_a="large_accelerated",
        track_b="accelerated",
        allowed=False,
    )
    report = rsnap.BridgeReport(
        differences=(difference,), compared_scopes=("pilot_candidate_entities",), compared_rows=1
    )
    assert not report.passed
    assert report.violations == (difference,)
    assert all(
        item.allowed is (item.field in rsnap.BRIDGE_ALLOWED_ACCESSION_COLUMNS)
        for item in paired.bridge.differences
        if item.scope == "pilot_candidate_accessions"
    )


def test_a_superset_replacement_bundle_is_rejected() -> None:
    """**R31**: whole-bundle compatibility is exact; no accession is dropped to match."""
    target, spare = 4_200_001, 4_200_002
    entities = [er._reserve_entity(cik) for cik in (target, spare)]
    accessions = [er._reserve_accession(cik, 2018, 1) for cik in (target, spare)]
    plain = accessions[0].accession_plain
    exact = er._reserve_construction(
        entities, accessions, target_cik=f"{target:010d}", selected_plains=[plain]
    )
    assert len(exact.packages) == 1

    widened = er._reserve_construction(
        entities,
        [*accessions, er._reserve_accession(spare, 2019, 2)],
        target_cik=f"{target:010d}",
        selected_plains=[plain],
    )
    assert not widened.packages
    assert len(widened.no_compatible_reserve) == 1


def test_a_subset_replacement_bundle_is_rejected() -> None:
    """**R31** / **E5**: exactness holds in the *narrowing* direction too.

    The accepted M2.3 reserve suite already proves strict-subset rejection at the
    contribution-set level. This is the M3.3 I/R-level proof, taken through the **same**
    accepted ``build_reserve_packages`` entry point that E5 uses, so the M3.3 suite
    itself directly proves **both** directions rather than inheriting one of them. No
    reserve-signature logic is duplicated and ``reserve_selector.py`` is untouched.

    The exact-match control matters: it proves the two-accession target shape *is*
    coverable, so the strict-subset rejection is caused by the narrowing and not by an
    unbuildable fixture.
    """
    target, spare = 4_300_001, 4_300_002
    entities = [er._reserve_entity(cik) for cik in (target, spare)]
    target_bundle = [er._reserve_accession(target, y, s) for y, s in ((2018, 1), (2019, 2))]
    spare_bundle = [er._reserve_accession(spare, y, s) for y, s in ((2018, 3), (2019, 4))]
    selected = [item.accession_plain for item in target_bundle]

    exact = er._reserve_construction(
        entities,
        [*target_bundle, *spare_bundle],
        target_cik=f"{target:010d}",
        selected_plains=selected,
    )
    assert len(exact.packages) == 1
    assert not exact.no_compatible_reserve
    covering = {item.accession_plain for item in exact.packages[0].accessions}
    assert covering == {item.accession_plain for item in spare_bundle}

    narrowed = er._reserve_construction(
        entities,
        [*target_bundle, spare_bundle[0]],
        target_cik=f"{target:010d}",
        selected_plains=selected,
    )
    # Premise: the surviving replacement's whole bundle is a strict subset of the one
    # that matched exactly -- nothing else about the pool changed.
    assert {spare_bundle[0].accession_plain} < covering
    assert not narrowed.packages
    assert len(narrowed.no_compatible_reserve) == 1


def test_a_self_referential_amendment_parent_stays_unresolved() -> None:
    """**R32**: an unresolved parentage claim is never promoted to a resolved one."""
    state, parent = cs._amendment_linkage(
        "000000000117000005",
        is_amendment=True,
        resolution={  # type: ignore[arg-type]
            "status": "resolved",
            "resolved_value": "0000000001-17-000005",
        },
        originals={"000000000117000005": False},
    )
    assert state == "unresolved_amendment"
    assert parent is None


def test_a_parent_absent_from_the_snapshot_stays_unresolved() -> None:
    state, parent = cs._amendment_linkage(
        "000000000117000005",
        is_amendment=True,
        resolution={  # type: ignore[arg-type]
            "status": "resolved",
            "resolved_value": "0000000001-16-000004",
        },
        originals={},
    )
    assert state == "unresolved_amendment"
    assert parent is None


def test_the_replay_proof_observes_the_handle_rather_than_asserting_it(
    executed: tuple[Path, ox.SelectionOutcome],
) -> None:
    """**R3**: a logical convention on a read-write handle is insufficient."""
    from disclosure_drift.storage.sqlite import connect as sqlite_connect

    database, outcome = executed
    proof = ox.replay_selection_write_free(database, outcome.persisted.selection_run_id, replays=1)
    assert proof.strictly_read_only

    with sqlite_connect(database, writer=False) as connection:
        assert not ox._write_refused(connection)
