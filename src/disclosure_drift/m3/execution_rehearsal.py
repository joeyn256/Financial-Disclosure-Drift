"""The M3.3A execution rehearsal, scenarios E1-E8 (`Docs/m3/offline_rehearsal_spec.md` Part II).

Every scenario runs against a **disposable** data tree and catalog this module creates
under a caller-supplied workspace. Nothing here reads the accepted real private catalog,
resolves ``EV_ROOT``, opens a socket, or constructs a transport, and no successful run
is an authorization for M3.3-E0, M3.3-E1, M3.3-E2, or M3.4.

**Two tracks, never conflated** (accepted Decision 073 §3, **R27**). Each scenario
declares which one it ran on, and the declaration travels into the evidence report:

======  =======  ==========================================================
id      track    what it proves
======  =======  ==========================================================
E1      A        the real builder freezes deterministically over synthetic
                 stored objects, through the real offline parse
E2      A        every governing freeze validation refuses, each for its own
                 reason
E3      B        the accepted joint selector reaches ``feasible`` on a
                 conforming snapshot
E4      A        the builder-derived snapshot is **infeasible**, and
                 node-limit exhaustion is not mislabelled as proven
                 infeasibility
E5      B        reserve and disposition totality
E6      B        reconstruction refuses every stored identity mismatch
E7      B        the seal and the manifest are atomic, and faults leave
                 neither a row nor a file
E8      B        replay is write-free and regeneration reproduces the root;
                 Decision 023 **O1** fails closed and is referred
======  =======  ==========================================================

``FEASIBILITY SOURCE`` on every Track-B outcome is
``EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT`` (**R29**). A passing rehearsal
proves the accepted system operates correctly on a conforming feasible snapshot; it
proves **nothing** about whether the real metadata-only builder can produce one. **Both**
real-path gates stay open, and the generated report states them **separately** and by
name: ``M3_3_REAL_AMENDMENT_PURPOSE_FEASIBILITY_GATE_OPEN`` (**R30**) and
``M3_3_REAL_LINKED_AMENDMENT_FEASIBILITY_GATE_OPEN`` (**R32**). They are never merged
into one flag, and neither is ``real_builder_feasibility_proved``.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Final

from disclosure_drift.errors import DisclosureDriftError, GateFailureError
from disclosure_drift.m3 import offline_execution as ox
from disclosure_drift.m3 import rehearsal_world as world
from disclosure_drift.m3.candidate_snapshot import (
    CandidateSnapshotError,
    CandidateSnapshotInputs,
    build_and_freeze_candidate_snapshot,
)
from disclosure_drift.m3.rehearsal_snapshot import build_paired_snapshots
from disclosure_drift.paths import DataTree
from disclosure_drift.release.pilot_manifest import (
    REQUIRED_DECISION_AUTHORITY_RECORDS,
    ExplicitArguments,
)
from disclosure_drift.sec.accession_selection_store import (
    JointSelectionRunIdentity,
    reconstruct_persisted_joint_selection,
)
from disclosure_drift.sec.accession_selector import (
    DEFERRED_QUOTA_KEY,
    DEFERRED_QUOTA_REQUIRED_COUNT,
    QUOTA_DIMENSION_CROSS_CUTTING,
    AccessionCandidate,
    AccessionQuotaDiagnostic,
    EntityCandidate,
    JointSelectionResult,
    NameChangeEvidence,
    QuotaContributionMembership,
    SelectedAccession,
    accession_selection_rank,
)
from disclosure_drift.sec.entity_selector import (
    PILOT_SELECTION_SEED,
    Candidate,
    selection_rank,
)
from disclosure_drift.sec.reserve_selector import ReserveConstruction, build_reserve_packages
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import connect, transaction

__all__ = [
    "EXECUTION_REHEARSAL_REPORT_SCHEMA_VERSION",
    "FEASIBILITY_SOURCE_BUILDER",
    "FEASIBILITY_SOURCE_REHEARSAL",
    "SCENARIO_IDS",
    "TEST_ONLY_NODE_LIMIT",
    "ExecutionRehearsalError",
    "ExecutionRehearsalReport",
    "ScenarioOutcome",
    "run_execution_rehearsal",
    "scenario_titles",
    "test_only_explicit_arguments",
]

EXECUTION_REHEARSAL_REPORT_SCHEMA_VERSION: Final = "m3-3a-execution-rehearsal-report/1.0"

#: The eight mandatory scenarios. The registry is validated against this tuple at
#: import, so a scenario cannot be quietly dropped, duplicated, or disabled.
SCENARIO_IDS: Final[tuple[str, ...]] = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8")

#: **R29**'s two mutually exclusive feasibility sources. A Track-B outcome may never
#: claim the first, and no code path below constructs the first for a Track-B scenario.
FEASIBILITY_SOURCE_BUILDER: Final = "BUILDER_DERIVED"
FEASIBILITY_SOURCE_REHEARSAL: Final = "EXPLICITLY_GOVERNED_SYNTHETIC_REHEARSAL_SNAPSHOT"

#: **OR-7 is deferred.** No production ``node_limit`` has been owner-selected, so the
#: rehearsal states an explicitly test-only one. It is never a configuration value, never
#: a production default, and never a resolution of OR-7.
TEST_ONLY_NODE_LIMIT: Final = 2_000_000

#: A deliberately tiny limit, used only to prove node-limit exhaustion is reported as
#: ``infeasible_or_unproven`` and never as proven infeasibility (**R10**).
TEST_ONLY_EXHAUSTING_NODE_LIMIT: Final = 1

_AT: Final = "2026-01-01T00:00:00Z"
_INPUTS: Final = CandidateSnapshotInputs(
    census_run_id=world.CENSUS_RUN_ID,
    coverage_start=world.COVERAGE_START,
    coverage_end=world.COVERAGE_END,
    as_of_date="2026-06-30",
)


class ExecutionRehearsalError(DisclosureDriftError):
    """The rehearsal could not run. A failing scenario is a finding, not an error."""


# --------------------------------------------------------------------------
# Outcome records
# --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ScenarioOutcome:
    """One executed scenario, its track, and exactly what it proved."""

    scenario_id: str
    title: str
    track: str
    passed: bool
    detail: str
    feasibility_source: str
    feasibility_claim: str
    findings: tuple[str, ...] = ()

    def as_record(self) -> Mapping[str, object]:
        """A deterministic, path-free, identity-free record."""
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "rehearsal_input_track": self.track,
            "passed": self.passed,
            "detail": self.detail,
            "feasibility_source": self.feasibility_source,
            "feasibility_claim": self.feasibility_claim,
            "findings": list(self.findings),
        }


@dataclass(frozen=True, slots=True)
class ExecutionRehearsalReport:
    """The private M3.3A execution-rehearsal evidence report."""

    outcomes: tuple[ScenarioOutcome, ...]
    builder_derived_disposition: str
    accepted_selector_feasible_on_rehearsal_snapshot: bool
    bridge: Mapping[str, object]

    @property
    def passed(self) -> bool:
        """Whether every executed scenario passed."""
        return all(outcome.passed for outcome in self.outcomes)

    @property
    def complete(self) -> bool:
        """Whether all eight mandatory scenarios ran, in order."""
        return tuple(item.scenario_id for item in self.outcomes) == SCENARIO_IDS

    def as_payload(self) -> dict[str, object]:
        """The canonical, hashable representation of the report."""
        return {
            "report_schema_version": EXECUTION_REHEARSAL_REPORT_SCHEMA_VERSION,
            "complete": self.complete,
            "passed": self.passed,
            "builder_derived_selection_disposition": self.builder_derived_disposition,
            "accepted_selector_feasible_on_conforming_explicit_rehearsal_snapshot": (
                self.accepted_selector_feasible_on_rehearsal_snapshot
            ),
            # The two real-path gates are independently governed and independently
            # auditable -- Decision 073 **R30** and Decision 074 **R32** -- and are never
            # merged into one field. `real_builder_feasibility_proved` is a third,
            # separate claim and neither gate stands in for it (Decision 075 §3.3).
            "real_builder_feasibility_proved": False,
            "real_amendment_purpose_feasibility_gate": "OPEN",
            "real_linked_amendment_feasibility_gate": "OPEN",
            "real_private_parse_authorization": "NO",
            "actual_network_requests": 0,
            "transports_constructed": 0,
            "test_only_node_limit": TEST_ONLY_NODE_LIMIT,
            "r28_bridge": dict(self.bridge),
            "scenarios": [outcome.as_record() for outcome in self.outcomes],
        }

    def canonical_bytes(self) -> bytes:
        """Canonical JSON, matching the receipt and rehearsal discipline."""
        rendered = json.dumps(
            self.as_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return f"{rendered}\n".encode()

    @property
    def evidence_reference(self) -> str:
        """A content-derived, non-sensitive identifier a receipt may cite."""
        digest = hashlib.sha256(self.canonical_bytes()).hexdigest()
        return f"m3-3a-execution-rehearsal-report-{digest}"


@dataclass(slots=True)
class _Probe:
    """Accumulates what a scenario observed, so assertions read as facts."""

    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def require(self, condition: bool, message: str) -> None:  # noqa: FBT001
        """Record a failure unless ``condition`` holds."""
        if not condition:
            self.failures.append(message)

    def note(self, message: str) -> None:
        """Record an observed fact, whether or not anything failed."""
        self.notes.append(message)

    @property
    def passed(self) -> bool:
        """Whether the scenario observed no failure."""
        return not self.failures

    @property
    def detail(self) -> str:
        """The first failure, or a short statement that nothing failed."""
        return self.failures[0] if self.failures else "every expectation held"


# --------------------------------------------------------------------------
# Shared fixtures
# --------------------------------------------------------------------------


def test_only_explicit_arguments() -> ExplicitArguments:
    """The six Decision 021 §8.4 arguments, as **explicitly test-only** values.

    **OR-6 is deferred to M3.3-E2.** These are rehearsal values and are never recorded,
    reported, or reused as the future real ones: they are derived from fixed literals
    here precisely so no ambient fact — a Git commit, an interpreter version, a
    configuration file — can leak in and look like a real assertion.
    """

    def digest(seed: str) -> str:
        return hashlib.sha256(f"m3-3a-rehearsal-test-only/{seed}".encode()).hexdigest()

    return ExplicitArguments(
        dependency_lock_sha256=digest("dependency-lock"),
        code_commit_identifier="0" * 40,
        runtime_python_version="0.0.0-test-only",
        configuration_sha256=digest("configuration"),
        decision_authority_sha256=digest("decision-authority"),
        source_plan_sha256=digest("source-plan"),
        decision_authority_records=tuple(
            sorted((record, digest(record)) for record in REQUIRED_DECISION_AUTHORITY_RECORDS)
        ),
    )


@dataclass(frozen=True, slots=True)
class _Pair:
    """One materialized paired construction, ready for a scenario to use."""

    root: Path
    tree: DataTree
    source: Path
    track_a: Path
    track_b: Path
    snapshot_a: str
    snapshot_b: str
    bridge: Mapping[str, object]
    parse_report: Mapping[str, object]
    stipulated: Mapping[str, str]


def _reserve_twin_design(subset: set[int] | None, *, copies: int = 1) -> world.WorldDesign:
    """Add unselected sibling registrants so reserve packages become constructible.

    A replacement candidate is any **unselected** pool entity whose replacement
    signature equals the target's (Decision 020 §7). The siblings are given CIKs whose
    accepted tie-break hash is strictly greater than every base-case entity's, so the
    accepted entity objective — which minimizes the sorted hash vector — selects the base
    case and leaves every sibling available as a replacement. Nothing about the selector
    is changed; the design simply makes the lawful outcome the deterministic one.
    """
    base = world.base_case_design()
    floor = max(selection_rank(entry.padded) for entry in base.entities)
    targets = [entry for entry in base.entities if subset is None or entry.cik in subset]
    entities = list(base.entities)
    candidate = 200_000
    for entry in [item for _ in range(copies) for item in targets]:
        while selection_rank(f"{candidate:010d}") <= floor:
            candidate += 1
        accessions = tuple(
            replace(
                item,
                cik=candidate,
                parent_plain=(
                    None
                    if item.parent_plain is None
                    else item.parent_plain.replace(f"{entry.cik:010d}", f"{candidate:010d}", 1)
                ),
                co_registrants=tuple(900_000 + value for value in item.co_registrants),
            )
            for item in entry.accessions
        )
        entities.append(
            replace(
                entry,
                cik=candidate,
                name=f"{entry.name} Reserve Sibling",
                accessions=accessions,
            )
        )
        candidate += 1
    return world.WorldDesign(entities=tuple(entities))


@contextmanager
def _paired(workspace: Path, name: str, design: world.WorldDesign | None = None) -> Iterator[_Pair]:
    """Materialize one disposable paired construction under ``workspace``."""
    root = workspace / name
    root.mkdir(parents=True, exist_ok=True)
    tree = DataTree.from_root(root / "data")
    source = root / "source.sqlite3"
    built = world.build_rehearsal_world(
        tree=tree, database=source, lock_root=root / "locks", design=design
    )
    paired = build_paired_snapshots(
        source_database=source,
        track_a_database=root / "track_a.sqlite3",
        track_b_database=root / "track_b.sqlite3",
        lock_root=root / "locks",
        inputs=_INPUTS,
    )
    yield _Pair(
        root=root,
        tree=tree,
        source=source,
        track_a=paired.track_a_database,
        track_b=paired.track_b_database,
        snapshot_a=paired.track_a.snapshot_id,
        snapshot_b=paired.track_b.snapshot_id,
        bridge=paired.bridge.as_record(),
        parse_report=built.parse_report.as_record(),
        stipulated=paired.stipulated_categories,
    )


def _execute(
    database: Path, snapshot_id: str, *, node_limit: int, event: str
) -> ox.SelectionOutcome:
    """Run one selection through the I7 driver against a disposable catalog."""
    with CatalogWriter(database, database.parent / f"locks-{event}") as writer:
        return ox.execute_selection(
            writer=writer,
            inputs=ox.ExecutionInputs(
                snapshot_id=snapshot_id,
                node_limit=node_limit,
                occurred_at_utc=_AT,
                event_id=f"evt-{event}",
            ),
        )


# --------------------------------------------------------------------------
# E1 - deterministic snapshot freeze, through the real offline parse (Track A)
# --------------------------------------------------------------------------


def _run_e1(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e1") as pair:
        report = pair.parse_report

        def count(key: str) -> int:
            """One report count, narrowed once so a cell type cannot leak."""
            return int(str(report[key]))

        probe.require(
            count("requests_made") == 0 and count("transports_constructed") == 0,
            "the offline parse must place no request and construct no transport",
        )
        probe.require(
            count("not_required_validation_or_provenance_only") >= 1,
            "R18 category C must be exercised: a validation-only source left untouched",
        )
        probe.require(
            count("required_but_accepted_unavailable") >= 1,
            "R18 category B must be exercised: an accepted-unavailable source preserved",
        )
        probe.require(
            count("full_index_registrant_observations") > 0,
            "R22/R23: the full index must materialize candidate-facing registrants",
        )
        probe.note(f"offline parse dispositions: {json.dumps(dict(sorted(report.items())))}")

        with connect(pair.source, writer=False) as connection:
            untouched = connection.execute(
                "SELECT COUNT(*) FROM census_plan_sources WHERE source_id = "
                "'sec_edgar_filing_calendar' AND parser_state = 'not_started'"
            ).fetchone()[0]
        probe.require(
            int(untouched) == 1,
            "a category-C source must keep parser_state unmutated",
        )

        # Freezing twice from identical inputs must yield an identical identity.
        twin = pair.root / "twin.sqlite3"
        tree = DataTree.from_root(pair.root / "twin-data")
        twin_world = world.build_rehearsal_world(
            tree=tree, database=twin, lock_root=pair.root / "twin-locks"
        )
        with CatalogWriter(twin, pair.root / "twin-locks") as writer:
            second = build_and_freeze_candidate_snapshot(writer=writer, inputs=_INPUTS)
        probe.require(
            second.snapshot_id == pair.snapshot_a,
            "two builds over identical synthetic inputs must share one snapshot_id",
        )
        probe.require(
            second.candidate_snapshot_sha256
            == _stored_scalar(pair.track_a, pair.snapshot_a, "candidate_snapshot_sha256"),
            "two builds over identical inputs must share one candidate_snapshot_sha256",
        )
        probe.note(f"twin world derived {twin_world.census_accession_count} census accessions")

        # A frozen snapshot rejects mutation.
        probe.require(
            _mutation_refused(pair.track_a, pair.snapshot_a),
            "a frozen snapshot must refuse mutation of a content field",
        )

        # Every injected fault rolls the whole transaction back.
        for step in (
            "after_snapshot_insert",
            "after_children",
            "after_digests",
            "after_revalidation",
        ):
            faulted = pair.root / f"fault-{step}.sqlite3"
            _copy(pair.source, faulted)
            try:
                with CatalogWriter(faulted, pair.root / "fault-locks") as writer:
                    build_and_freeze_candidate_snapshot(writer=writer, inputs=_INPUTS, fault=step)
            except CandidateSnapshotError:
                pass
            else:  # pragma: no cover - a fault that did not fire is a finding
                probe.require(False, f"the injected fault at {step} did not fail closed")
            with connect(faulted, writer=False) as connection:
                remaining = connection.execute(
                    "SELECT COUNT(*) FROM pilot_candidate_snapshots"
                ).fetchone()[0]
            probe.require(
                int(remaining) == 0,
                f"a fault at {step} left a partial authoritative snapshot",
            )
    return _outcome("E1", "A", probe, FEASIBILITY_SOURCE_BUILDER, "builder integrity only")


def _stored_scalar(database: Path, snapshot_id: str, column: str) -> object:
    with connect(database, writer=False) as connection:
        row = connection.execute(
            f"SELECT {column} FROM pilot_candidate_snapshots WHERE snapshot_id = ?",  # noqa: S608
            (snapshot_id,),
        ).fetchone()
    return None if row is None else row[column]


def _mutation_refused(database: Path, snapshot_id: str) -> bool:
    try:
        with connect(database, writer=True) as connection, transaction(connection) as active:
            active.execute(
                "UPDATE pilot_candidate_snapshots SET entity_count = entity_count + 1 "
                "WHERE snapshot_id = ?",
                (snapshot_id,),
            )
    except sqlite3.IntegrityError:
        return True
    return False


def _copy(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with connect(source, writer=False) as origin, sqlite3.connect(target) as destination:
        origin.backup(destination)


# --------------------------------------------------------------------------
# E2 - snapshot-validation refusal (Track A)
# --------------------------------------------------------------------------


def _run_e2(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e2") as pair:
        # Each variant violates exactly one governing obligation, in isolation, and must
        # fail for its own reason rather than incidentally.
        variants: tuple[tuple[str, Callable[[sqlite3.Connection], None], str], ...] = (
            (
                "plain/dashed disagreement",
                _corrupt_dashed_form,
                "disagrees with the canonical dashed form",
            ),
            (
                "registrant CIK unresolved",
                _corrupt_registrant_cik,
                "not the canonical rendering",
            ),
            (
                "company name absent",
                _remove_company_name,
                "filing_time_name",
            ),
            (
                "non-canonical full-index CIK",
                _corrupt_full_index_cik,
                "non-canonical CIK",
            ),
            (
                "accession without a registrant row",
                _orphan_accession_anchor,
                "no accepted registrant row",
            ),
        )
        for label, mutate, expected in variants:
            target = pair.root / f"e2-{abs(hash(label)) % 10_000}.sqlite3"
            _copy(pair.source, target)
            with connect(target, writer=True) as connection:
                connection.execute("PRAGMA foreign_keys = OFF")
                with transaction(connection) as active:
                    mutate(active)
            observed = _refusal(target, pair.root)
            probe.require(
                observed is not None and expected in observed,
                f"{label}: expected a refusal naming {expected!r}, observed {observed!r}",
            )
            probe.note(f"{label}: refused")
            with connect(target, writer=False) as connection:
                frozen = connection.execute(
                    "SELECT COUNT(*) FROM pilot_candidate_snapshots WHERE snapshot_state = 'frozen'"
                ).fetchone()[0]
            probe.require(int(frozen) == 0, f"{label}: a frozen snapshot survived the refusal")

        # An OQ-3 rebuild in the same catalog fails closed rather than replacing.
        rebuilt = pair.root / "e2-rebuild.sqlite3"
        _copy(pair.track_a, rebuilt)
        observed = _refusal(rebuilt, pair.root)
        probe.require(
            observed is not None and "already exists" in observed,
            f"OQ-3: a rebuild in the same catalog must fail closed, observed {observed!r}",
        )
    return _outcome("E2", "A", probe, FEASIBILITY_SOURCE_BUILDER, "freeze validation only")


def _refusal(database: Path, lock_root: Path) -> str | None:
    """Build against ``database`` and return the refusal message, or ``None``."""
    try:
        with CatalogWriter(database, lock_root / "e2-locks") as writer:
            build_and_freeze_candidate_snapshot(writer=writer, inputs=_INPUTS)
    except (CandidateSnapshotError, GateFailureError, sqlite3.IntegrityError) as exc:
        return str(exc)
    return None


def _corrupt_dashed_form(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        "SELECT accession_plain FROM census_accessions ORDER BY accession_plain LIMIT 1"
    ).fetchone()
    connection.execute(
        "UPDATE census_accessions SET accession_dashed = '9999999999-99-999999' "
        "WHERE accession_plain = ?",
        (row["accession_plain"],),
    )


def _corrupt_registrant_cik(connection: sqlite3.Connection) -> None:
    connection.execute(
        "UPDATE census_registrants SET cik_padded = '1' WHERE cik_numeric = "
        "(SELECT MIN(cik_numeric) FROM census_registrants)"
    )


def _remove_company_name(connection: sqlite3.Connection) -> None:
    connection.execute(
        "DELETE FROM census_registrant_observations WHERE observation_kind = 'company_name' "
        "AND cik_numeric = (SELECT MIN(cik_numeric) FROM census_registrants)"
    )


def _corrupt_full_index_cik(connection: sqlite3.Connection) -> None:
    connection.execute(
        "UPDATE census_accession_observations SET raw_value_json = '\"not-a-cik\"' "
        "WHERE field_name = 'cik_padded' AND source_observation_id IN "
        "(SELECT observation_id FROM census_source_observations "
        "WHERE source_id = 'sec_full_index_company') AND accession_plain = "
        "(SELECT MIN(accession_plain) FROM census_accession_observations "
        "WHERE field_name = 'cik_padded')"
    )


def _orphan_accession_anchor(connection: sqlite3.Connection) -> None:
    connection.execute(
        "DELETE FROM census_registrants WHERE cik_numeric = "
        "(SELECT registrant_cik_numeric FROM census_accessions ORDER BY accession_plain LIMIT 1)"
    )


# --------------------------------------------------------------------------
# E3 - feasible selection (Track B)
# --------------------------------------------------------------------------


def _run_e3(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e3") as pair:
        outcome = _execute(
            pair.track_b, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event="e3"
        )
        probe.require(
            outcome.feasible, f"expected a feasible run, observed {outcome.persisted.run_state!r}"
        )
        probe.require(
            outcome.pairs.satisfied,
            f"the 2009/2010 pair quota needs six distinct entities, "
            f"observed {outcome.pairs.entities}",
        )
        probe.require(
            outcome.reconstructed.selection_run_id == outcome.persisted.selection_run_id,
            "independent reconstruction must reproduce the persisted run",
        )
        probe.note(f"pairs: {json.dumps(dict(outcome.pairs.as_record()))}")
        with connect(pair.track_b, writer=False) as connection:
            state = connection.execute(
                "SELECT run_state FROM pilot_selection_runs WHERE selection_run_id = ?",
                (outcome.persisted.selection_run_id,),
            ).fetchone()["run_state"]
        probe.require(state == "feasible", "the run must end at feasible")
    return _outcome(
        "E3",
        "B",
        probe,
        FEASIBILITY_SOURCE_REHEARSAL,
        "the accepted selector is feasible on a conforming rehearsal snapshot",
    )


# --------------------------------------------------------------------------
# E4 - infeasible and node-limit fail-closed behaviour (Track A)
# --------------------------------------------------------------------------


def _run_e4(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e4") as pair:
        builder = _execute(
            pair.track_a, pair.snapshot_a, node_limit=TEST_ONLY_NODE_LIMIT, event="e4a"
        )
        probe.require(
            builder.persisted.run_state == "infeasible",
            f"the builder-derived snapshot must be infeasible, "
            f"observed {builder.persisted.run_state!r}",
        )
        binding = tuple(
            item.key
            for item in builder.persisted.result.accession_quota_results
            if item.binding_constraint
        )
        probe.require(
            binding == ("amendment_purpose_categories",),
            f"the sole binding constraint must be the amendment-purpose quota, observed {binding}",
        )
        probe.note(f"builder-derived binding constraints: {list(binding)}")
        with connect(pair.track_a, writer=False) as connection:
            sealed = connection.execute(
                "SELECT selection_result_sha256 FROM pilot_selection_runs "
                "WHERE selection_run_id = ?",
                (builder.persisted.selection_run_id,),
            ).fetchone()["selection_result_sha256"]
            manifests = connection.execute(
                "SELECT COUNT(*) FROM pilot_manifest_versions"
            ).fetchone()[0]
        probe.require(sealed is None, "an infeasible run must carry no selection_result_sha256")
        probe.require(int(manifests) == 0, "an infeasible run must produce no manifest")

        exhausted = _execute(
            pair.track_b,
            pair.snapshot_b,
            node_limit=TEST_ONLY_EXHAUSTING_NODE_LIMIT,
            event="e4b",
        )
        probe.require(
            exhausted.persisted.run_state == "infeasible_or_unproven",
            "node-limit exhaustion must be infeasible_or_unproven, never proven infeasibility",
        )
        probe.require(
            exhausted.persisted.node_limit_exhausted,
            "node-limit exhaustion must be recorded on the run",
        )
    return _outcome(
        "E4",
        "A",
        probe,
        FEASIBILITY_SOURCE_BUILDER,
        "INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE on the builder-derived snapshot",
    )


# --------------------------------------------------------------------------
# E5 - reserve and disposition totality (Track B)
# --------------------------------------------------------------------------


def _run_e5(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    # (b) no target has a compatible reserve, and (c) a mixed run: both persisted
    # end to end through the accepted store.
    for label, design in (
        ("zero-coverage", None),
        ("mixed", _reserve_twin_design({1, 2, 3, 101, 102})),
    ):
        with _paired(workspace, f"e5-{label}", design=design) as pair:
            outcome = _execute(
                pair.track_b, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event=f"e5{label}"
            )
            probe.require(outcome.feasible, f"{label}: the run must be feasible")
            shape = _reserve_shape(pair.track_b, outcome.persisted.selection_run_id)
            probe.require(
                shape["targets"] == shape["packages"] + shape["dispositions"],
                f"{label}: item 70 requires exactly one package or one disposition per target",
            )
            probe.require(
                shape["overlap"] == 0,
                f"{label}: no target may carry both a package and a disposition",
            )
            probe.require(
                shape["invented_ranks"] == 0,
                f"{label}: no synthetic package, placeholder, or invented reserve rank",
            )
            if label == "zero-coverage":
                probe.require(
                    shape["packages"] == 0, "the zero-coverage variant must have no package"
                )
            else:
                probe.require(
                    shape["packages"] > 0, "the mixed variant must have at least one package"
                )
                probe.require(
                    shape["dispositions"] > 0,
                    "the mixed variant must have at least one disposition",
                )
            probe.note(f"{label}: {json.dumps(shape)}")

    # (a) The positive compatible-reserve path, proved directly at the **pure** reserve
    # layer under accepted R31 (Decision 074 §2.1). The former requirement — that every
    # selected target hold a rank-1 package — is superseded: Decision 020 §7 makes a
    # target-specific no-compatible-reserve disposition a lawful, nonblocking outcome, so
    # requiring universal coverage imposed a production-invalid condition. The pilot-scale
    # fully twinned pool and its 2,000,000-node search are therefore not rebuilt.
    _run_e5_positive_reserve_path(probe)
    return _outcome(
        "E5", "B", probe, FEASIBILITY_SOURCE_REHEARSAL, "reserve and disposition totality"
    )


def _reserve_entity(cik: int, *, history: str = "stable") -> EntityCandidate:
    """One lawful operating candidate, at the fields reserve compatibility reads."""
    return EntityCandidate(
        candidate=Candidate(
            cik_padded=f"{cik:010d}",
            filing_time_name=f"Reserve Fixture {cik}",
            category="operating",
            primary_universe_eligible=True,
            engineering_only_stress=False,
            size_stratum="large_accelerated",
            size_evidence_level="provisional",
            industry_group="technology_and_communications",
            industry_evidence_level="provisional",
            industry_quota_eligible=True,
            history_class=history,
            history_evidence_level="provisional",
            currently_inactive=False,
        ),
        name_change=NameChangeEvidence(),
    )


def _reserve_accession(cik: int, year: int, seq: int, *, form: str = "10-K") -> AccessionCandidate:
    """One lawful base-eligible original annual accession for that candidate."""
    dashed = f"{cik:010d}-{year % 100:02d}-{seq:06d}"
    return AccessionCandidate(
        accession_plain=dashed.replace("-", ""),
        accession_number_dashed=dashed,
        anchor_cik_numeric=cik,
        form_type=form,
        is_amendment=False,
        official_filing_date=f"{year}-03-01",
        report_date=f"{year - 1}-12-31",
        cohort_applicability="applies",
        provisional_official_cohort="development",
        filing_date_evidence_level="provisional",
        cohort_evidence_level="provisional",
        xbrl_evidence_level="provisional",
        has_xbrl=True,
        has_inline_xbrl=True,
        base_eligible=True,
    )


def _reserve_construction(
    entities: Sequence[EntityCandidate],
    accessions: Sequence[AccessionCandidate],
    *,
    target_cik: str,
    selected_plains: Sequence[str],
) -> ReserveConstruction:
    """Run the accepted **pure** reserve constructor over one explicit selected result.

    The selected result is stated rather than solved: Decision 020's reserve layer is
    explicitly downstream of the initial joint selection and does not determine it, so a
    minimal stated result exercises the production reserve rules without inventing a
    second selection methodology.
    """
    membership = QuotaContributionMembership.derive(
        entities,
        accessions,
        selected_entity_ciks=[target_cik],
        selected_accession_plains=list(selected_plains),
        selection_seed=PILOT_SELECTION_SEED,
    )
    by_plain = {item.accession_plain: item for item in accessions}
    selected = tuple(
        SelectedAccession(
            accession_plain=plain,
            accession_number_dashed=by_plain[plain].accession_number_dashed,
            anchor_cik_padded=by_plain[plain].anchor_cik_padded,
            accession_role="base",
            selected_order=order,
            accession_tie_break_sha256=accession_selection_rank(
                by_plain[plain].anchor_cik_padded,
                by_plain[plain].accession_number_dashed,
                PILOT_SELECTION_SEED,
            ),
        )
        for order, plain in enumerate(selected_plains, start=1)
    )
    target = next(item for item in entities if item.candidate.cik_padded == target_cik)
    result = JointSelectionResult(
        status="feasible",
        selection_seed=PILOT_SELECTION_SEED,
        selected_operating=(target.candidate,),
        selected_controls=(),
        selected_accessions=selected,
        objective=None,
        entity_quota_results=(),
        accession_quota_results=(),
        deferred_quota_result=AccessionQuotaDiagnostic(
            dimension=QUOTA_DIMENSION_CROSS_CUTTING,
            key=DEFERRED_QUOTA_KEY,
            comparison_operator=">=",
            required_count=DEFERRED_QUOTA_REQUIRED_COUNT,
            available_eligible_count=0,
            achieved_count=0,
            status="unproven",
            binding_constraint=False,
            excluded_pool_count=0,
            evidence_state="unproven",
            deferred=True,
        ),
        excluded_candidates=(),
        accession_diagnostics=(),
        amendment_families=(),
        quota_contributions=membership,
        expanded_node_count=0,
        node_limit=TEST_ONLY_NODE_LIMIT,
        node_limit_exhausted=False,
    )
    return build_reserve_packages(
        entities,
        accessions,
        result,
        selection_run_id="0" * 64,
        snapshot_id="1" * 64,
        selection_seed=PILOT_SELECTION_SEED,
    )


def _run_e5_positive_reserve_path(probe: _Probe) -> None:
    """**R31** E5(a) — the compatible-reserve positive path, proved directly.

    Small and bounded on purpose: the pilot-scale joint selector is not invoked, no
    production reserve rule is altered, and no accession is dropped from a replacement's
    whole bundle to manufacture compatibility.
    """
    target, first, second = 4_100_001, 4_100_002, 4_100_003
    entities = [_reserve_entity(cik) for cik in (target, first, second)]
    accessions = [_reserve_accession(cik, 2018, 1) for cik in (target, first, second)]
    target_padded = f"{target:010d}"
    target_plain = accessions[0].accession_plain

    covered = _reserve_construction(
        entities, accessions, target_cik=target_padded, selected_plains=[target_plain]
    )
    probe.require(
        len(covered.packages) == 1 and not covered.no_compatible_reserve,
        f"a compatible replacement must yield exactly one package, observed "
        f"{len(covered.packages)} package(s) and "
        f"{len(covered.no_compatible_reserve)} disposition(s)",
    )
    package = covered.packages[0]
    probe.require(package.reserve_rank == 1, "the persisted package must be rank 1")
    probe.require(
        package.target_cik_padded == target_padded
        and package.replacement_cik_padded != target_padded,
        "target and replacement must be disjoint",
    )
    probe.require(
        package.replaces_signature_sha256 == package.reserve_signature_sha256,
        "compatibility is exact signature equality, recomputed on both sides",
    )
    probe.note(f"positive path: rank-1 package for {package.replacement_cik_padded}")

    # Determinism where two compatible replacements exist: the accepted tie-break, not
    # insertion order, decides -- and it decides identically on a reversed pool.
    reversed_pool = _reserve_construction(
        list(reversed(entities)),
        list(reversed(accessions)),
        target_cik=target_padded,
        selected_plains=[target_plain],
    )
    probe.require(
        len(reversed_pool.packages) == 1
        and reversed_pool.packages[0].replacement_cik_padded == package.replacement_cik_padded,
        "the rank-1 replacement must be chosen deterministically, independent of pool order",
    )
    probe.note("determinism: two compatible replacements resolve identically on a reversed pool")

    # A superset bundle is rejected: whole-bundle compatibility is exact, and no accession
    # may be dropped from a replacement to manufacture a match.
    superset = [*accessions, _reserve_accession(first, 2019, 2)]
    widened = _reserve_construction(
        entities, superset, target_cik=target_padded, selected_plains=[target_plain]
    )
    probe.require(
        len(widened.packages) == 1
        and widened.packages[0].replacement_cik_padded == f"{second:010d}",
        "a replacement whose whole bundle is a superset of the target's must be rejected",
    )
    probe.note("superset bundle rejected; the exactly matching replacement is used instead")

    # With no compatible replacement at all, the target receives exactly one deterministic
    # no-compatible-reserve disposition and nothing else.
    alone = _reserve_construction(
        entities[:1], accessions[:1], target_cik=target_padded, selected_plains=[target_plain]
    )
    probe.require(
        not alone.packages and len(alone.no_compatible_reserve) == 1,
        "a target with no compatible replacement must receive exactly one disposition",
    )
    probe.note("no-compatible-reserve disposition is target-specific, durable, nonblocking")


def _reserve_shape(database: Path, selection_run_id: str) -> dict[str, int]:
    with connect(database, writer=False) as connection:
        targets = int(
            connection.execute(
                "SELECT COUNT(*) FROM pilot_selected_entities WHERE selection_run_id = ?",
                (selection_run_id,),
            ).fetchone()[0]
        )
        packages = int(
            connection.execute(
                "SELECT COUNT(*) FROM pilot_reserves WHERE selection_run_id = ?",
                (selection_run_id,),
            ).fetchone()[0]
        )
        dispositions = int(
            connection.execute(
                "SELECT COUNT(*) FROM pilot_selection_entity_reasons WHERE selection_run_id = ? "
                "AND reason_code = 'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'",
                (selection_run_id,),
            ).fetchone()[0]
        )
        overlap = int(
            connection.execute(
                "SELECT COUNT(*) FROM pilot_reserves AS r "
                "JOIN pilot_selection_entity_reasons AS d "
                "ON d.selection_run_id = r.selection_run_id "
                "AND d.cik_numeric = r.target_cik_numeric "
                "WHERE r.selection_run_id = ? AND d.reason_code = "
                "'REVIEW_PILOT_NO_COMPATIBLE_RESERVE'",
                (selection_run_id,),
            ).fetchone()[0]
        )
        invented = int(
            connection.execute(
                "SELECT COUNT(*) FROM pilot_reserves "
                "WHERE selection_run_id = ? AND reserve_rank <> 1",
                (selection_run_id,),
            ).fetchone()[0]
        )
    return {
        "targets": targets,
        "packages": packages,
        "dispositions": dispositions,
        "overlap": overlap,
        "invented_ranks": invented,
    }


# --------------------------------------------------------------------------
# E6 - reconstruction mismatch refusal (Track B)
# --------------------------------------------------------------------------


def _run_e6(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e6") as pair:
        outcome = _execute(
            pair.track_b, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event="e6"
        )
        probe.require(outcome.feasible, "E6 needs a feasible persisted run to corrupt")
        run_id = outcome.persisted.selection_run_id
        mutations = {
            "snapshot_id": ("snapshot_id", "0" * 64),
            "selection_seed": ("selection_seed", "not-the-frozen-seed"),
            "selector_policy_version": ("selector_policy_version", "not-a-policy/9.9"),
            "quota_policy_version": ("quota_policy_version", "not-a-policy/9.9"),
            "node_limit": ("search_node_limit", TEST_ONLY_NODE_LIMIT + 1),
            "selection_input_sha256": ("selection_input_sha256", "1" * 64),
        }
        covered = set(mutations) | {"selection_run_id"}
        governed = set(JointSelectionRunIdentity.__dataclass_fields__)
        probe.require(
            covered == governed,
            f"every governed identity component must be mutated; "
            f"missing {sorted(governed - covered)}",
        )
        for label, (column, value) in mutations.items():
            corrupted = pair.root / f"e6-{label}.sqlite3"
            _copy(pair.track_b, corrupted)
            refusal = _corruption_refused(corrupted, run_id, column, value)
            probe.require(
                refusal is not None,
                f"a corrupted {label} was neither refused at the schema nor at reconstruction",
            )
            probe.note(f"{label}: refused at the {refusal}")
        probe.note(
            "the immutable-identity trigger refuses three components outright, so those "
            "corruptions never reach reconstruction; the remaining three are refused by "
            "the single centralized identity comparison"
        )
    return _outcome(
        "E6", "B", probe, FEASIBILITY_SOURCE_REHEARSAL, "reconstruction mismatch refusal"
    )


def _corruption_refused(
    database: Path, selection_run_id: str, column: str, value: object
) -> str | None:
    """Corrupt one governed identity component and report where it was refused.

    Two independent layers refuse, and either one is a fail-closed pass: migration
    ``0013``'s immutable-identity trigger rejects a change to ``selection_run_id``,
    ``snapshot_id``, or ``selection_input_sha256`` at the write, and the accepted single
    centralized :class:`JointSelectionRunIdentity` comparison rejects the rest at
    reconstruction. ``None`` means the corruption was accepted, which is a finding.
    """
    try:
        with connect(database, writer=True) as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            with transaction(connection) as active:
                active.execute(
                    f"UPDATE pilot_selection_runs SET {column} = ? "  # noqa: S608
                    "WHERE selection_run_id = ?",
                    (value, selection_run_id),
                )
    except sqlite3.IntegrityError:
        return "schema"
    try:
        with connect(database, writer=False) as connection:
            reconstruct_persisted_joint_selection(connection, selection_run_id)
    except (GateFailureError, sqlite3.Error):
        return "reconstruction"
    return None


# --------------------------------------------------------------------------
# E7 - seal and manifest atomicity (Track B)
# --------------------------------------------------------------------------


def _run_e7(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e7") as pair:
        outcome = _execute(
            pair.track_b, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event="e7"
        )
        probe.require(outcome.feasible, "E7 needs a feasible persisted run")
        run_id = outcome.persisted.selection_run_id
        explicit = test_only_explicit_arguments()
        # Migration 0013 makes a persisted manifest row undeletable, so the fault
        # variant's catalog is copied **before** any manifest exists rather than
        # manufactured by deleting one afterwards.
        faulted = pair.root / "e7-fault.sqlite3"
        _copy(pair.track_b, faulted)
        with CatalogWriter(pair.track_b, pair.root / "locks-e7") as writer:
            manifest = ox.seal_and_replay_manifest(
                writer=writer,
                selection_run_id=run_id,
                data_tree=pair.tree,
                explicit=explicit,
                generated_at_utc=_AT,
            )
        probe.require(
            manifest.identical_root_on_replay,
            "an authorized retry must reproduce the identical root and document bytes",
        )
        probe.note(f"manifest: {json.dumps(dict(manifest.as_record()))}")
        document = (
            pair.tree.releases / "pilot" / Path(manifest.manifest.relative_manifest_path).name
        )
        probe.require(document.is_file(), "the manifest document must exist beside its row")

        original = document.read_bytes()
        for label, mutate in (
            ("deleted", lambda: document.unlink()),
            ("truncated", lambda: document.write_bytes(original[: len(original) // 2])),
            ("byte-modified", lambda: document.write_bytes(original.replace(b"{", b"[", 1))),
        ):
            mutate()
            refused = _verification_refused(
                pair.track_b, manifest.manifest.identity.manifest_id, pair.tree, explicit
            )
            probe.require(refused, f"verification accepted a {label} document")
            with connect(pair.track_b, writer=False) as connection:
                rows = connection.execute(
                    "SELECT COUNT(*) FROM pilot_manifest_versions"
                ).fetchone()[0]
            probe.require(int(rows) == 1, f"{label}: the manifest row must be left unchanged")
            document.write_bytes(original)
            probe.note(f"{label}: refused, row unchanged")

        # A fault before the document is written leaves neither a new row nor a file.
        broken_tree = DataTree.from_root(pair.root / "e7-readonly")
        (broken_tree.releases / "pilot").mkdir(parents=True, exist_ok=True)
        (broken_tree.releases / "pilot").chmod(0o500)
        try:
            with CatalogWriter(faulted, pair.root / "locks-e7b") as writer:
                ox.seal_and_replay_manifest(
                    writer=writer,
                    selection_run_id=run_id,
                    data_tree=broken_tree,
                    explicit=explicit,
                    generated_at_utc=_AT,
                )
        except (GateFailureError, OSError, DisclosureDriftError):
            probe.note("a write fault before the document commit failed closed")
        else:
            probe.require(False, "a manifest write fault did not fail closed")
        finally:
            (broken_tree.releases / "pilot").chmod(0o700)
        with connect(faulted, writer=False) as connection:
            rows = connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0]
            sealed = connection.execute(
                "SELECT selection_result_sha256 FROM pilot_selection_runs "
                "WHERE selection_run_id = ?",
                (run_id,),
            ).fetchone()["selection_result_sha256"]
        probe.require(int(rows) == 0, "a manifest write fault must leave no row")
        probe.require(
            sealed is not None,
            "sealing happens in its own prior transaction and survives a manifest fault",
        )
    return _outcome("E7", "B", probe, FEASIBILITY_SOURCE_REHEARSAL, "seal and manifest atomicity")


def _verification_refused(
    database: Path, manifest_id: str, tree: DataTree, explicit: ExplicitArguments
) -> bool:
    from disclosure_drift.sec.pilot_manifest_store import verify_pilot_manifest

    try:
        with connect(database, writer=False) as connection:
            verify_pilot_manifest(connection, manifest_id, data_tree=tree, explicit=explicit)
    except (GateFailureError, DisclosureDriftError, OSError):
        return True
    return False


# --------------------------------------------------------------------------
# E8 - identical replay and Decision 023 O1 (Track B)
# --------------------------------------------------------------------------


def _run_e8(workspace: Path) -> ScenarioOutcome:
    probe = _Probe()
    with _paired(workspace, "e8") as pair:
        # The second clean rebuild starts from the frozen snapshot **before** any
        # selection exists. Migration 0009 refuses every selected-row delete once a run
        # leaves ``running`` and migration 0013 makes a manifest row undeletable, so a
        # rebuild is produced by re-running the accepted path in a fresh catalog rather
        # than by manufacturing a state the accepted lifecycle never produces.
        rebuild = pair.root / "e8-rebuild.sqlite3"
        _copy(pair.track_b, rebuild)
        outcome = _execute(
            pair.track_b, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event="e8"
        )
        probe.require(outcome.feasible, "E8 needs a feasible persisted run")
        run_id = outcome.persisted.selection_run_id
        proof = ox.replay_selection_write_free(pair.track_b, run_id, replays=2)
        probe.require(proof.write_free, "replay must leave every durable byte identical")
        probe.note(f"replay: {json.dumps(dict(proof.as_record()))}")

        explicit = test_only_explicit_arguments()
        with CatalogWriter(pair.track_b, pair.root / "locks-e8") as writer:
            manifest = ox.seal_and_replay_manifest(
                writer=writer,
                selection_run_id=run_id,
                data_tree=pair.tree,
                explicit=explicit,
                generated_at_utc=_AT,
            )
        probe.require(
            manifest.identical_root_on_replay,
            "regeneration from unchanged state must reproduce the identical root",
        )

        # Two clean rebuilds from the same frozen snapshot agree on everything.
        second = _execute(rebuild, pair.snapshot_b, node_limit=TEST_ONLY_NODE_LIMIT, event="e8b")
        probe.require(
            second.persisted.selection_run_id == run_id,
            "two clean rebuilds from one frozen snapshot must share a run identity",
        )
        probe.require(
            second.persisted.selected_accession_count == outcome.persisted.selected_accession_count,
            "two clean rebuilds must select the same accessions",
        )

        # (b) Decision 023 O1: a required milestone-plan §10 item whose **sole**
        # serialized carrier family is empty. The accepted crosswalk coverage check must
        # refuse to place it, and nothing may be written as a result.
        empty_carrier = _document_with_empty_sole_carrier(manifest.manifest.document)
        refused = _crosswalk_refused(empty_carrier)
        probe.require(refused is not None, "Decision 023 O1 must fail closed")
        probe.note(f"Decision 023 O1: refused ({refused})")
        with connect(pair.track_b, writer=False) as connection:
            rows = connection.execute("SELECT COUNT(*) FROM pilot_manifest_versions").fetchone()[0]
        probe.require(int(rows) == 1, "the O1 fixture must add no manifest row and delete none")
        probe.note("Decision 023 O1: failed closed and referred, never resolved")
    return _outcome(
        "E8", "B", probe, FEASIBILITY_SOURCE_REHEARSAL, "write-free replay, identical root, and O1"
    )


#: The block and family whose emptiness leaves a required milestone-plan §10 item with
#: **no** other serialized carrier. Decision 023 **O1** is exactly that condition.
_SOLE_CARRIER_BLOCK: Final = "selected_accessions"


def _document_with_empty_sole_carrier(
    document: Mapping[str, object],
) -> Mapping[str, object]:
    """One rendered manifest whose sole carrier family for a required item is empty.

    Nothing is reclassified, no category is added, and no count is changed: the family
    is emptied and the accepted coverage check is then asked to place the items it
    carried. That is the exact Decision 023 **O1** trigger, and the correct behaviour is
    to fail closed and refer, never to find the item another home.
    """
    emptied = dict(document)
    for key, value in document.items():
        if isinstance(value, Mapping) and _SOLE_CARRIER_BLOCK in value:
            block = dict(value)
            block[_SOLE_CARRIER_BLOCK] = []
            emptied[key] = block
        elif key == _SOLE_CARRIER_BLOCK:
            emptied[key] = []
    return emptied


def _crosswalk_refused(document: Mapping[str, object]) -> str | None:
    """Whether the accepted crosswalk coverage check refuses the emptied document."""
    from disclosure_drift.release.pilot_manifest import verify_document_crosswalk_coverage

    try:
        verify_document_crosswalk_coverage(document)
    except (GateFailureError, DisclosureDriftError, KeyError, TypeError) as exc:
        return type(exc).__name__
    return None


# --------------------------------------------------------------------------
# Registry and entry point
# --------------------------------------------------------------------------


_TITLES: Final[Mapping[str, str]] = {
    "E1": "Deterministic snapshot freeze",
    "E2": "Snapshot-validation refusal",
    "E3": "Feasible selection",
    "E4": "Infeasible and node-limit fail-closed behaviour",
    "E5": "Reserve and disposition totality",
    "E6": "Reconstruction mismatch refusal",
    "E7": "Seal and manifest atomicity",
    "E8": "Identical replay and Decision 023 O1 handling",
}

_REGISTRY: Final[Mapping[str, Callable[[Path], ScenarioOutcome]]] = {
    "E1": _run_e1,
    "E2": _run_e2,
    "E3": _run_e3,
    "E4": _run_e4,
    "E5": _run_e5,
    "E6": _run_e6,
    "E7": _run_e7,
    "E8": _run_e8,
}


def _outcome(
    scenario_id: str, track: str, probe: _Probe, source: str, claim: str
) -> ScenarioOutcome:
    return ScenarioOutcome(
        scenario_id=scenario_id,
        title=_TITLES[scenario_id],
        track=f"TRACK_{track}",
        passed=probe.passed,
        detail=probe.detail,
        feasibility_source=source,
        feasibility_claim=claim,
        findings=tuple(probe.notes),
    )


def _validate_registry() -> None:
    """Refuse at import if the registry is not exactly the eight mandatory scenarios."""
    if tuple(_REGISTRY) != SCENARIO_IDS or tuple(_TITLES) != SCENARIO_IDS:
        message = (
            f"the execution-rehearsal registry must be exactly {SCENARIO_IDS}; "
            f"found {tuple(_REGISTRY)}"
        )
        raise ExecutionRehearsalError(message)


_validate_registry()


def scenario_titles() -> Mapping[str, str]:
    """The eight scenario titles, in order."""
    return dict(_TITLES)


def run_execution_rehearsal(
    scenario_ids: Sequence[str] | None = None, *, workspace_root: Path
) -> ExecutionRehearsalReport:
    """Run the requested scenarios and return the execution-rehearsal evidence report.

    Args:
        scenario_ids: The scenarios to run; all eight when omitted. A subset is for
            diagnosis and never produces a complete report.
        workspace_root: Where the disposable data trees and catalogs are created. It is
            never the repository checkout and never the accepted private evidence root.
    """
    requested = SCENARIO_IDS if scenario_ids is None else tuple(scenario_ids)
    unknown = sorted(set(requested) - set(SCENARIO_IDS))
    if unknown:
        message = (
            f"unknown execution-rehearsal scenario(s) {unknown}; the registry is {SCENARIO_IDS}"
        )
        raise ExecutionRehearsalError(message)

    workspace = workspace_root / "m3_3a_execution_rehearsal"
    workspace.mkdir(parents=True, exist_ok=True)
    outcomes = [
        _REGISTRY[scenario_id](workspace)
        for scenario_id in SCENARIO_IDS
        if scenario_id in set(requested)
    ]
    with _paired(workspace, "bridge") as pair:
        bridge = dict(pair.bridge)
    feasible = any(outcome.scenario_id == "E3" and outcome.passed for outcome in outcomes)
    return ExecutionRehearsalReport(
        outcomes=tuple(outcomes),
        builder_derived_disposition="INFEASIBLE_AMENDMENT_PURPOSE_COVERAGE",
        accepted_selector_feasible_on_rehearsal_snapshot=feasible,
        bridge=bridge,
    )
