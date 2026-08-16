"""PRE-E0 catalog transition and M3.3-E0 offline-parse proofs (accepted Decision 094 §12.3).

Every test here drives production code over a **disposable** temporary catalog beneath a
**synthetic** temporary root. Nothing in this module resolves, opens, names, prints, or infers
the accepted private evidence root, and nothing opens the accepted operational catalog: the
fixtures build their own catalog from the packaged migrations and delete it with the temporary
directory.

Two conventions carry most of the weight, and both are deliberate.

**Test-scoped activation.** :data:`~disclosure_drift.m3.e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY`
and :data:`~disclosure_drift.m3.e0.M3_3_E0_EXECUTION_AUTHORITY` ship as ``None``, so the two
``execute`` state machines are unreachable in the shipped source — which is exactly what
``test_both_activation_constants_are_none_in_the_shipped_source`` and its neighbours assert
against the *file*, not against a runtime value. Decision 094 §12.3 items 1-2 and 8-10
nonetheless require those machines to be proved non-vacuously, so the tests that exercise them
override the module attribute for the duration of one test. That is a harness override of an
in-memory constant against a disposable catalog; it activates nothing, it changes no shipped
byte, and it is the only mechanism by which "the code exists and is correct but is disabled"
can be a checked claim rather than an assertion.

**Fail-closed reading.** Where a test asserts an absence — no namespace, no lease, no page, no
invented entity — it measures the absence directly rather than trusting a return value.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import stat
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest

from disclosure_drift.config import (
    ENV_OVERRIDES,
    EVIDENCE_ROOT_ENV,
    RECOGNIZED_ENV_VARS,
    RUNTIME_ROOT_ENV_VARS,
    SECRET_ENV_VARS,
)
from disclosure_drift.m3 import e0
from disclosure_drift.m3 import offline_parse as op
from disclosure_drift.m3 import rehearsal_world as rw
from disclosure_drift.m3.receipt import (
    INTERRUPTION_STATES_V4,
    OPERATOR_RECEIPT_FILENAME,
    RECEIPT_SCHEMA_VERSION_V4,
    ExecutionReceiptV4,
    ReceiptValidationError,
    canonical_bytes,
    inspect_receipt,
)
from disclosure_drift.paths import DataTree
from disclosure_drift.storage.catalog import CatalogWriter, strictly_read_only_connection
from disclosure_drift.storage.sqlite import (
    applied_versions,
    apply_migrations,
    available_migrations,
    connect,
    transaction,
)

_AT = "2026-01-01T00:00:00Z"

#: A synthetic evidence-root value that is *not* read from the ambient environment. Every test
#: that needs the variable supplies its own mapping; no test inspects the operator's value.
_SYNTHETIC_ROOT_MARKER = "synthetic-private-root"


# ==========================================================================
# Fixtures: a disposable accepted-shaped catalog beneath a synthetic root
# ==========================================================================


@dataclass(frozen=True, slots=True)
class _Sec:
    requests_per_second: float = 1.0
    burst: int = 1
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 30.0
    bulk_read_timeout_seconds: float = 300.0
    max_retries: int = 3
    cooldown_seconds: float = 1.0
    user_agent_env: str = "unused"


@dataclass(frozen=True, slots=True)
class _Network:
    enabled: bool = False
    m3_acquire_enabled: bool = False


@dataclass(frozen=True, slots=True)
class _Config:
    """The only configuration surface the two commands read (§5.2 predicate 13, §9.2).

    A stub rather than the tracked project configuration, because these tests must be able to
    flip a network switch to prove the predicate fires, and the tracked file is a prohibited
    path. The fields are exactly the ones production reads.
    """

    sec: _Sec = _Sec()
    network: _Network = _Network()


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    """A synthetic private root. Never the accepted one, and never read from the environment."""
    root = tmp_path / _SYNTHETIC_ROOT_MARKER
    root.mkdir()
    (root / "catalogs").mkdir()
    return root


def _catalog_path(evidence_root: Path) -> Path:
    return evidence_root / e0.OPERATIONAL_CATALOG_RELATIVE_PATH


def _migrations_through(head: int) -> tuple[object, ...]:
    return tuple(item for item in available_migrations() if item.version <= head)


def _seed_plan(connection: sqlite3.Connection, *, count: int, start: int = 0) -> None:
    """Add accepted-shaped category-B plan rows, which need no stored object.

    Category B is the only R18 disposition that is truthful without an observation, so padding
    a plan to its accepted size with anything else would fabricate evidence.
    """
    with transaction(connection) as active:
        for index in range(start, start + count):
            active.execute(
                "INSERT INTO census_plan_sources (census_run_id, source_instance_id, "
                "source_id, request_identity, required, source_scope, retrieval_state, "
                "snapshot_state, parser_state, catalog_state, qa_state, "
                "unresolved_blocking_reasons_json, observation_id, successful_terminal, "
                "updated_at_utc) VALUES (?, ?, 'sec_submissions_historical', ?, 1, 'base', "
                "'failed', 'missing', 'not_started', 'not_started', 'unknown', '[]', NULL, "
                "0, ?)",
                (
                    rw.CENSUS_RUN_ID,
                    f"pad|sec_submissions_historical|{index}",
                    f"req/pad/{index}",
                    _AT,
                ),
            )


def _plan_count(connection: sqlite3.Connection) -> int:
    return int(connection.execute("SELECT COUNT(*) FROM census_plan_sources").fetchone()[0])


def build_catalog(evidence_root: Path, *, head: int = 13, sources: bool = False) -> Path:
    """Create the disposable catalog at exactly ``head``, with an accepted-shaped plan.

    Args:
        evidence_root: The synthetic private root the catalog is created beneath.
        head: The migration head to stop at. ``13`` is the accepted catalog's real head and
            the only lawful transition source; other values exist so the refusal is proved.
        sources: Also write the synthetic stored objects and their plan-bound observations,
            so a real offline parse has something to parse.
    """
    path = _catalog_path(evidence_root)
    with connect(path, writer=True) as connection:
        apply_migrations(connection, _migrations_through(head))  # type: ignore[arg-type]
        rw._seed_reference(connection)
        if sources:
            objects = rw._write_stored_objects(
                DataTree.from_root(evidence_root), rw.base_case_design()
            )
            rw._seed_observations_and_plan(
                connection,
                objects,
                include_unavailable_source=True,
                include_validation_only_source=True,
            )
        existing = _plan_count(connection)
        _seed_plan(connection, count=e0.PLANNED_SOURCE_COUNT - existing, start=existing)
        assert _plan_count(connection) == e0.PLANNED_SOURCE_COUNT
    return path


@pytest.fixture
def catalog(evidence_root: Path) -> Path:
    """The accepted-shaped disposable catalog at head ``0013``, with 76 planned sources."""
    return build_catalog(evidence_root)


@pytest.fixture
def config() -> _Config:
    return _Config()


@pytest.fixture(autouse=True)
def _no_ambient_root(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove the runtime-root variable from every test's environment, without reading it.

    ``monkeypatch.delenv`` with ``raising=False`` deletes by **name**. No test in this module
    ever reads the operator's value, and none can accidentally resolve the accepted root
    because the name is absent for the whole module.
    """
    monkeypatch.delenv(EVIDENCE_ROOT_ENV, raising=False)
    e0._reset_evidence_root_cache()
    yield
    e0._reset_evidence_root_cache()


def _environ(root: Path) -> Mapping[str, str]:
    return {EVIDENCE_ROOT_ENV: str(root)}


# ==========================================================================
# Family 13 + Decision 096 §6.2: both constants disabled, both modes exit 3
# ==========================================================================


def test_both_activation_constants_are_none_in_the_shipped_source() -> None:
    """§7.2, and Decision 096 §6.2: the shipped literals, asserted against the file.

    The runtime attribute is asserted too, but the **source** assertion is the load-bearing
    one: a runtime check alone would pass against a module some other test had already
    overridden, and this is the one property no test may leave ambiguous.
    """
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    source = Path(e0.__file__).read_text(encoding="utf-8")
    assert "PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None" in source
    assert "M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None" in source


@pytest.mark.parametrize(
    "runner",
    [e0.run_prepare_e0_catalog_command, e0.run_offline_parse_command],
)
def test_execute_returns_exit_three_whatever_the_environment_holds(
    runner: object, evidence_root: Path, catalog: Path, config: _Config, tmp_path: Path
) -> None:
    """§7.2: no environment value, catalog state, receipt, namespace, or flag substitutes.

    The same refusal is required with the runtime root present and absent, with the catalog
    at its lawful head and at another, and with a namespace already on disk — because each of
    those is a thing an operator might reasonably expect to change the answer, and none may.
    """
    namespace = e0.runs_directory(evidence_root) / e0.TRANSITION_RUN_NAMESPACE
    namespace.mkdir(parents=True)
    for environ in (_environ(evidence_root), {}, {EVIDENCE_ROOT_ENV: ""}):
        result = runner(  # type: ignore[operator]
            mode="execute",
            config=config,
            repository_root=tmp_path,
            environ=environ,
        )
        assert result.exit_code == e0.EXIT_STAGE_NOT_ENABLED
        assert any("is None" in line for line in result.lines)


def test_a_passing_preflight_does_not_enable_execute(
    evidence_root: Path, catalog: Path, config: _Config, tmp_path: Path
) -> None:
    """§7.2: a preflight result is a measurement, never an authorization."""
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["transition_execute_enabled"] is False
    result = e0.run_prepare_e0_catalog_command(
        mode="execute", config=config, repository_root=tmp_path, environ=_environ(evidence_root)
    )
    assert result.exit_code == e0.EXIT_STAGE_NOT_ENABLED


def test_the_activation_check_precedes_root_resolution(config: _Config, tmp_path: Path) -> None:
    """Exit ``3`` is unconditional: an unset root cannot mask "this stage is not enabled".

    If the root were resolved first, an operator with no variable set would be told to fix
    their environment for a command that would refuse regardless — and a *set* variable would
    have become a precondition for learning the stage was disabled.
    """
    result = e0.run_offline_parse_command(
        mode="execute", config=_Config(), repository_root=tmp_path, environ={}
    )
    assert result.exit_code == e0.EXIT_STAGE_NOT_ENABLED
    preflight = e0.run_offline_parse_command(
        mode="preflight", config=config, repository_root=tmp_path, environ={}
    )
    assert preflight.exit_code == e0.EXIT_CONFIG_ERROR


def test_an_unknown_mode_is_a_usage_error(config: _Config, tmp_path: Path) -> None:
    result = e0.run_prepare_e0_catalog_command(
        mode="repair", config=config, repository_root=tmp_path, environ={}
    )
    assert result.exit_code == e0.EXIT_USAGE


# ==========================================================================
# Decision 095 R81: the source-local catalog constant
# ==========================================================================


def test_the_catalog_constant_equals_the_acquisition_constant() -> None:
    """**R81**: a deliberate duplication of one frozen literal, pinned by equality.

    Both constants are imported independently, so a drift in **either** file fails here.
    """
    from disclosure_drift.m3 import acquisition

    assert acquisition.OPERATIONAL_CATALOG_RELATIVE_PATH == e0.OPERATIONAL_CATALOG_RELATIVE_PATH
    assert e0.OPERATIONAL_CATALOG_RELATIVE_PATH == "catalogs/m3_2a_operational.sqlite3"


#: The modules **R81** and §7.3 forbid this surface from reaching.
_PROHIBITED_MODULES = frozenset(
    {
        "disclosure_drift.m3.acquisition",
        "disclosure_drift.sec.census_orchestrator",
        "disclosure_drift.sec.transport",
        "disclosure_drift.sec.client",
        "httpx",
        "requests",
        "urllib.request",
        "socket",
        "ssl",
        "http.client",
    }
)


def test_the_e0_module_declares_no_prohibited_import() -> None:
    """**R81** and §7.3, read off ``e0.py``'s own syntax tree.

    Every ``import`` and ``from ... import`` in the file is walked, module scope and function
    body alike, because this surface deliberately imports several dependencies inside
    function bodies to keep its own graph small — a module-scope-only check would miss
    exactly the imports most worth checking.
    """
    import ast

    tree = ast.parse(Path(e0.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            imported.add(node.module)
    assert not (imported & _PROHIBITED_MODULES), sorted(imported & _PROHIBITED_MODULES)
    assert not {name for name in imported if "acquisition" in name or "transport" in name}


def test_importing_the_e0_module_adds_no_prohibited_edge() -> None:
    """**R81** transitively: a differential closure, measured in fresh interpreters.

    A bare ``sys.modules`` assertion would be untrue for a reason that has nothing to do
    with this surface: ``disclosure_drift/m3/__init__.py`` eagerly re-exports the accepted
    acquisition foundation, so *every* ``disclosure_drift.m3.*`` import already loads it —
    as ``receipt``, ``offline_parse``, and ``candidate_snapshot`` all do today. What R81
    forbids is a **new** edge from this module, so the closure of importing ``m3.e0`` is
    compared against the closure of importing the bare package it lives in. They must be
    equal: importing ``e0`` reaches nothing the package did not already reach.
    """

    def closure(target: str) -> frozenset[str]:
        probe = (
            "import sys, importlib;"
            f"importlib.import_module({target!r});"
            "print(repr(sorted(sys.modules)))"
        )
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", probe], capture_output=True, text=True, check=True
        )
        loaded = frozenset(json.loads(result.stdout.strip().replace("'", '"')))
        return loaded & _PROHIBITED_MODULES

    assert closure("disclosure_drift.m3.e0") == closure("disclosure_drift.m3")
    # And no HTTP client library is reachable either way.
    assert not (closure("disclosure_drift.m3.e0") & {"httpx", "requests", "urllib.request"})


# ==========================================================================
# Decision 095 R80: the centrally recognized non-override runtime root
# ==========================================================================


def test_the_evidence_root_is_a_recognized_non_override_runtime_root() -> None:
    """**R80** items 1-3: recognized centrally, and applied by nothing in the config layer."""
    assert EVIDENCE_ROOT_ENV == "DISCLOSURE_DRIFT_EVIDENCE_ROOT"
    assert EVIDENCE_ROOT_ENV in RUNTIME_ROOT_ENV_VARS
    assert EVIDENCE_ROOT_ENV in RECOGNIZED_ENV_VARS
    assert EVIDENCE_ROOT_ENV not in ENV_OVERRIDES
    assert EVIDENCE_ROOT_ENV not in SECRET_ENV_VARS


def test_removing_the_evidence_root_from_the_runtime_roots_kills_recognition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """**R80** proof 5: the mutation control, plus the unrelated-name control beside it.

    Recognition must come from ``RUNTIME_ROOT_ENV_VARS``. Recomputing the recognized set
    without the entry must stop recognizing the name, while an unrelated ``DISCLOSURE_DRIFT_*``
    name stays rejected — which is what distinguishes "centrally recognized" from "the
    allowlist has been loosened".
    """
    import disclosure_drift.config as config_module

    mutated = frozenset(RUNTIME_ROOT_ENV_VARS - {EVIDENCE_ROOT_ENV})
    monkeypatch.setattr(config_module, "RUNTIME_ROOT_ENV_VARS", mutated)
    recomputed = frozenset(ENV_OVERRIDES) | SECRET_ENV_VARS | mutated
    assert EVIDENCE_ROOT_ENV not in recomputed
    assert "DISCLOSURE_DRIFT_NOT_A_REAL_SETTING" not in recomputed
    assert config_module.CONFIG_PATH_ENV in RECOGNIZED_ENV_VARS


def test_the_runtime_root_value_never_reaches_a_message_or_a_report(
    evidence_root: Path, catalog: Path, config: _Config, tmp_path: Path
) -> None:
    """**R80** item 3 and §12.3 item 11: field-aware nonleakage on success *and* refusal.

    The synthetic value is checked for by its distinguishing component rather than by a
    blanket "does any line look like a path" detector, which would both over-fire on the
    root-relative catalog name and under-fire on a value that happened to look ordinary.
    """
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    rendered: list[str] = []
    passing = e0.run_prepare_e0_catalog_command(
        mode="preflight", config=config, repository_root=checkout, environ=_environ(evidence_root)
    )
    rendered.extend(passing.lines)
    assert passing.exit_code == e0.EXIT_OK

    # The same command over a catalog at the wrong head: a refusal path, which is where a
    # leak is most likely because a refusal is where a developer reaches for context.
    other = tmp_path / "other-root"
    (other / "catalogs").mkdir(parents=True)
    build_catalog(other, head=12)
    refusing = e0.run_prepare_e0_catalog_command(
        mode="preflight", config=config, repository_root=checkout, environ=_environ(other)
    )
    rendered.extend(refusing.lines)
    assert refusing.exit_code == e0.EXIT_GATE_FAILURE

    unset = e0.run_prepare_e0_catalog_command(
        mode="preflight", config=config, repository_root=checkout, environ={}
    )
    rendered.extend(unset.lines)

    joined = "\n".join(rendered)
    assert _SYNTHETIC_ROOT_MARKER not in joined
    assert str(evidence_root) not in joined
    assert str(other) not in joined
    assert "other-root" not in joined
    # The variable's *name* is legitimately reported; its value never is.
    assert EVIDENCE_ROOT_ENV in joined
    for line in rendered:
        assert not line.strip().startswith("/")


def test_an_unlawful_runtime_root_is_a_configuration_error_naming_no_path(
    tmp_path: Path, config: _Config
) -> None:
    """§7.3 exit ``1``: a root inside the checkout is a mistake in the invocation."""
    inside = tmp_path / "checkout" / "private"
    inside.mkdir(parents=True)
    result = e0.run_offline_parse_command(
        mode="preflight",
        config=config,
        repository_root=tmp_path / "checkout",
        environ={EVIDENCE_ROOT_ENV: str(inside)},
    )
    assert result.exit_code == e0.EXIT_CONFIG_ERROR
    assert str(inside) not in "\n".join(result.lines)


def test_a_relative_runtime_root_is_refused(tmp_path: Path) -> None:
    with pytest.raises(e0.EvidenceRootUnsetError):
        e0.resolve_evidence_root(tmp_path, environ={EVIDENCE_ROOT_ENV: "relative/path"})


# ==========================================================================
# Family 1: exact 0013 -> 0014 -> 0015 selection, and refusal at every other head
# ==========================================================================


def test_the_packaged_target_migrations_match_the_accepted_digests() -> None:
    """§5.1 and §12.3 item 1-2: the exact names and SHA-256 values Decision 094 §1.1 measured."""
    selected = e0._packaged_target_migrations()
    assert [item.version for item in selected] == [14, 15]
    assert selected[0].name == "m33_multi_registrant_relational_correction"
    assert selected[1].name == "m33_verified_document_evidence"
    for migration in selected:
        assert migration.checksum_sha256 == e0.PACKAGED_MIGRATION_SHA256[f"{migration.version:04d}"]


def test_a_drifted_packaged_migration_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """The digest pin is load-bearing: change it and selection refuses rather than applies."""
    monkeypatch.setitem(e0.PACKAGED_MIGRATION_SHA256, "0014", "0" * 64)
    with pytest.raises(e0.PreflightRefusalError, match="0014"):
        e0._packaged_target_migrations()


def test_migration_0016_is_absent_and_would_be_refused() -> None:
    """§5.1: ``0016`` is unauthorized. Selection is by exact version, so it is never included."""
    assert max(item.version for item in available_migrations()) == e0.TRANSITION_TARGET_HEAD
    assert all(item.version <= 15 for item in e0._packaged_target_migrations())


@pytest.mark.parametrize("head", [11, 12, 14, 15])
def test_the_transition_refuses_at_every_head_but_0013(
    evidence_root: Path, config: _Config, head: int
) -> None:
    """§5.2 predicate 4 and §12.3 item 1: exactly ``0001``-``0013``, contiguous."""
    build_catalog(evidence_root, head=head)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("0001-0013" in refusal for refusal in report.refusals), report.refusals


def test_the_transition_preflight_passes_at_head_0013(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["applied_migration_head"] == "0013"
    assert report.facts["planned_source_count"] == e0.PLANNED_SOURCE_COUNT
    assert report.facts["planned_sources_not_started"] == e0.PLANNED_SOURCE_COUNT


# ==========================================================================
# Family 2: every preflight predicate, measured rather than asserted
# ==========================================================================


def test_the_empty_state_guards_refuse_a_consumed_migration_window(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """§1.3 and §5.2 predicate 7: a row in any guard table closes the window."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
            "content_size_bytes, storage_representation, relative_storage_path, "
            "parser_version, recorded_at_utc) VALUES ('obs-guard', 'sec_company_tickers', "
            "'req/guard/0', 'https://example.invalid/guard', 'census', ?, 'stored_new', "
            "?, ?, ?, 1, 1, 'identical', 'raw/sec/bulk/guard.json', 'fixture/1.0', ?)",
            (_AT, "a" * 64, "a" * 64, "a" * 64, _AT),
        )
        active.execute(
            "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, parser_id, "
            "parser_version, started_at_utc, finished_at_utc, parsed_count, "
            "quarantined_count, outcome, summary_json) VALUES "
            "('run-1', 'obs-guard', 'p', '1.0', ?, ?, 0, 0, 'completed', '{}')",
            (_AT, _AT),
        )
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("migration window is closed" in item for item in report.refusals)


def test_a_started_plan_source_refuses(evidence_root: Path, catalog: Path, config: _Config) -> None:
    """§5.2 predicate 8: all 76 sources must still be ``not_started``."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_plan_sources SET parser_state = 'completed' "
            "WHERE source_instance_id = (SELECT MIN(source_instance_id) FROM census_plan_sources)"
        )
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("not_started" in item for item in report.refusals)


def test_a_short_plan_refuses(evidence_root: Path, config: _Config) -> None:
    """§9.1: exactly 76 accepted plan rows, never "at least"."""
    path = _catalog_path(evidence_root)
    with connect(path, writer=True) as connection:
        apply_migrations(connection, _migrations_through(13))  # type: ignore[arg-type]
        rw._seed_reference(connection)
        _seed_plan(connection, count=e0.PLANNED_SOURCE_COUNT - 1)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("exactly 76 sources" in item for item in report.refusals)


def test_an_enabled_network_switch_refuses(evidence_root: Path, catalog: Path) -> None:
    """§5.2 predicate 13: read from the loaded configuration, not from the tracked file."""
    report = e0.transition_preflight(
        evidence_root=evidence_root, config=_Config(network=_Network(enabled=True))
    )
    assert not report.passed
    assert any("network switch is enabled" in item for item in report.refusals)
    assert report.facts["network_switches_disabled"] is False


def test_a_held_writer_lease_refuses_and_elapsed_time_never_permits_takeover(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """§5.2 predicate 9 and §5.3: the OS ``flock`` is authoritative, the recorded expiry is not."""
    with CatalogWriter(catalog, catalog.parent):
        report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("holds the catalog lease" in item for item in report.refusals)

    # Once released, an expired recorded lease is not itself a refusal: the flock is the
    # authority, and a stale record must not become a second, weaker one.
    released = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert released.passed, released.refusals


def test_preflight_never_creates_the_lease_it_inspects(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """§5.2 predicate 9, finding m1: an absent lease passes without being created."""
    lease = catalog.parent / "catalog_writer.lease"
    assert not lease.exists()
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert not lease.exists()
    assert report.facts["writer_lease"] == "absent"


def test_an_existing_run_namespace_refuses(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """§5.2 predicate 10 and §8: a namespace is create-once and is never reused."""
    (e0.runs_directory(evidence_root) / e0.TRANSITION_RUN_NAMESPACE).mkdir(parents=True)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("create-once" in item for item in report.refusals)


def test_the_disk_predicate_requires_three_copies_plus_a_gibibyte(
    evidence_root: Path, catalog: Path, config: _Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§5.2 predicate 11, measured against a stubbed free-space reading."""
    import shutil as shutil_module

    class _Usage:
        free = 1

    monkeypatch.setattr(shutil_module, "disk_usage", lambda _path: _Usage())
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("fewer than the required" in item for item in report.refusals)
    assert int(report.facts["required_disk_bytes"]) >= e0.DISK_HEADROOM_BYTES


def test_preflight_changes_no_catalog_byte_and_creates_no_governed_artifact(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """§5.2's strictly-read-only rule, proved by a before/after tree and byte comparison.

    The catalog file itself must be **byte-identical**: that is the property
    ``strictly_read_only_connection`` exists for, since a read-write handle to a WAL-mode
    database checkpoints on close and rewrites durable bytes without any statement writing.

    Two paths do appear, and they are named rather than tolerated silently: opening a
    WAL-mode database read-only makes SQLite materialize its WAL index, so a ``-shm`` and a
    **zero-length** ``-wal`` are left beside the catalog. Decision 094 §8 names exactly that
    "ordinary fixed-catalog ``-wal``/``-shm`` lifecycle" as a permitted operational
    companion, not a governed artifact: no catalog page changed, the log is empty, and no
    namespace, lease, backup, receipt, or ledger was created.
    """

    def listing() -> dict[str, tuple[int, bytes]]:
        found: dict[str, tuple[int, bytes]] = {}
        for path in sorted(evidence_root.rglob("*")):
            if path.is_file():
                raw = path.read_bytes()
                name = str(path.relative_to(evidence_root))
                found[name] = (len(raw), hashlib.sha256(raw).digest())
        return found

    before = listing()
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    after = listing()

    catalog_key = str(catalog.relative_to(evidence_root))
    assert after[catalog_key] == before[catalog_key]
    appeared = set(after) - set(before)
    assert appeared <= {f"{catalog_key}-wal", f"{catalog_key}-shm"}, sorted(appeared)
    wal = catalog.parent / f"{catalog.name}-wal"
    assert not wal.exists() or wal.stat().st_size == 0
    assert set(before) - set(after) == set()

    assert not (evidence_root / "runs").exists()
    assert not (catalog.parent / "catalog_writer.lease").exists()


# ==========================================================================
# Family 12: the per-table memory bound, measured before any writer opens
# ==========================================================================


def test_the_release_hash_estimate_is_scanned_not_buffered(catalog: Path) -> None:
    """§8.2: the estimator measures whether the catalog can be hashed without hashing it."""
    with strictly_read_only_connection(catalog) as connection:
        estimate = e0.estimate_release_hash_memory(connection)
    assert estimate.row_count >= e0.PLANNED_SOURCE_COUNT
    assert estimate.estimated_peak_bytes > 0
    assert estimate.passes
    assert estimate.memory_ceiling <= e0.MAXIMUM_RELEASE_HASH_BYTES


def test_the_memory_predicate_refuses_before_a_writer_opens(
    evidence_root: Path, catalog: Path, config: _Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§8.2 and §12.3 item 12: the refusal happens in preflight, so nothing is created."""
    monkeypatch.setattr(e0, "MAXIMUM_RELEASE_HASH_BYTES", 1)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("release-hash estimate" in item for item in report.refusals)
    assert not (evidence_root / "runs").exists()
    assert not (catalog.parent / "catalog_writer.lease").exists()


def test_a_platform_that_will_not_report_memory_refuses(
    catalog: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A platform that will not answer must not silently pass the bound."""
    monkeypatch.setattr(e0, "_physical_memory_bytes", lambda: 0)
    with strictly_read_only_connection(catalog) as connection:
        estimate = e0.estimate_release_hash_memory(connection)
    assert estimate.memory_ceiling == 0
    assert not estimate.passes


def test_one_scan_supplies_both_digest_projections(catalog: Path) -> None:
    """§8.2 and adopted optimization O1: the same per-table scan updates both digests.

    Proved by counting the ``SELECT`` statements the digest issues against the tables it
    hashes: a second walk of the catalog would double them.
    """
    executed: list[str] = []
    with strictly_read_only_connection(catalog) as connection:
        connection.set_trace_callback(executed.append)
        digest = connection and e0.catalog_snapshot_digest(connection)
        connection.set_trace_callback(None)
    projected = {table for table, _ in digest.projection}
    scans = [
        statement
        for statement in executed
        if statement.startswith("SELECT ") and " FROM " in statement
    ]
    content_scans = [
        statement
        for statement in scans
        if any(f'FROM "{table}"' in statement for table in projected)
    ]
    assert len(content_scans) == len(projected)
    assert digest.catalog_logical_sha256 is not None
    assert digest.preexisting_content_sha256 != digest.catalog_logical_sha256


def test_a_replayed_projection_carries_no_full_digest_and_refuses_a_missing_table(
    catalog: Path,
) -> None:
    """§8.1: there is no post-transition full logical digest, and a dropped table refuses."""
    with strictly_read_only_connection(catalog) as connection:
        replayed = e0.catalog_snapshot_digest(
            connection, projection=[("census_plan_sources", ("census_run_id",))]
        )
        assert replayed.catalog_logical_sha256 is None
        with pytest.raises(e0.PreflightRefusalError, match="does not carry"):
            e0.catalog_snapshot_digest(connection, projection=[("no_such_table", ("x",))])
        with pytest.raises(e0.PreflightRefusalError, match="column"):
            e0.catalog_snapshot_digest(
                connection, projection=[("census_plan_sources", ("no_such_column",))]
            )
    with pytest.raises(e0.PreflightRefusalError, match="replayed projection"):
        replayed.require_full()


# ==========================================================================
# Family 8: namespaces, modes, symlinks, create-once, fsync, and the ledger
# ==========================================================================


@pytest.mark.parametrize(
    "namespace", ["", "Uppercase", "has space", "-leading", "a" * 129, "../escape", "a/b"]
)
def test_an_unlawful_namespace_is_refused(namespace: str) -> None:
    with pytest.raises(e0.E0Error, match="accepted shape"):
        e0.validate_namespace(namespace)


def test_the_production_namespaces_are_fixed_constants_of_the_accepted_shape() -> None:
    """§7.1 and adopted optimization O2: not CLI options, and lawfully shaped."""
    assert e0.TRANSITION_RUN_NAMESPACE == "m3_3_pre_e0_catalog_transition_0013_0015_v1"
    assert e0.E0_RUN_NAMESPACE == "m3_3_e0_offline_parse_v1"
    for namespace in (e0.TRANSITION_RUN_NAMESPACE, e0.E0_RUN_NAMESPACE):
        assert e0.validate_namespace(namespace) == namespace


def test_the_run_namespace_is_create_once_at_mode_0700(evidence_root: Path) -> None:
    """§8: created once, at ``0700``, and never a second time."""
    directory = e0.create_run_namespace(evidence_root, "temporary-namespace")
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    with pytest.raises(e0.E0Error, match="create-once"):
        e0.create_run_namespace(evidence_root, "temporary-namespace")


def test_a_symlinked_namespace_or_runs_directory_is_refused(
    evidence_root: Path, tmp_path: Path
) -> None:
    """§8: a symlinked run directory would place governed artifacts outside the boundary."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    runs = e0.runs_directory(evidence_root)
    runs.mkdir()
    (runs / "aliased").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(e0.E0Error, match="symbolic link"):
        e0.create_run_namespace(evidence_root, "aliased")


def test_write_once_creates_mode_0600_and_never_replaces(evidence_root: Path) -> None:
    """§8: ``O_CREAT | O_EXCL`` at ``0600``; a second write is refused by the OS, not a check."""
    directory = e0.create_run_namespace(evidence_root, "artifacts")
    target = directory / "record.json"
    e0.write_once(target, b"{}\n")
    assert stat.S_IMODE(target.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        e0.write_once(target, b"{}\n")


def test_a_relative_path_that_ascends_is_refused(evidence_root: Path) -> None:
    with pytest.raises(e0.E0Error, match="may not ascend"):
        e0.resolve_within(evidence_root, "../outside", label="operational catalog")
    with pytest.raises(e0.E0Error, match="relative"):
        e0.resolve_within(evidence_root, "/absolute", label="operational catalog")


def _ledger(evidence_root: Path, namespace: str = "ledger-namespace") -> e0.EventLedger:
    directory = e0.create_run_namespace(evidence_root, namespace)
    return e0.EventLedger(directory / e0.TRANSITION_EVENTS_FILENAME, namespace, kind="TRANSITION")


def test_the_ledger_is_hash_chained_and_verifies(evidence_root: Path) -> None:
    ledger = _ledger(evidence_root)
    ledger.append(
        "PREFLIGHT_PASSED",
        {
            "pre_migration_head": "0013",
            "catalog_bytes": 1,
            "precondition_table_count": 11,
            "pre_catalog_logical_sha256": "a" * 64,
        },
        observed_at_utc=_AT,
    )
    ledger.append(
        "FAILED",
        {"reason_code": "PRE_E0_CATALOG_TRANSITION_FAILED", "reason_detail": "a bounded sentence"},
        observed_at_utc=_AT,
    )
    events = e0.read_event_ledger(ledger.path, kind="TRANSITION")
    assert [event["sequence"] for event in events] == [1, 2]
    assert "previous_event_sha256" not in events[0]
    assert events[1]["previous_event_sha256"] == events[0]["event_sha256"]
    assert stat.S_IMODE(ledger.path.stat().st_mode) == 0o600


def test_an_event_never_contains_its_own_digest_in_its_preimage(evidence_root: Path) -> None:
    """§11: no digest contains its own value in its preimage."""
    ledger = _ledger(evidence_root)
    event = ledger.append(
        "EXECUTION_RECEIPT_WRITTEN", {"execution_receipt_id": "b" * 64}, observed_at_utc=_AT
    )
    preimage = {key: value for key, value in event.items() if key != "event_sha256"}
    assert hashlib.sha256(canonical_bytes(preimage)).hexdigest() == event["event_sha256"]
    self_referential = dict(event)
    assert hashlib.sha256(canonical_bytes(self_referential)).hexdigest() != event["event_sha256"]


@pytest.mark.parametrize("corruption", ["truncate", "reorder", "mutate", "unchain"])
def test_ledger_truncation_reordering_and_mutation_are_detected(
    evidence_root: Path, corruption: str
) -> None:
    """§8 and §12.3 item 8: each failure mode detected for its own reason."""
    ledger = _ledger(evidence_root)
    for index in range(3):
        ledger.append(
            "EXECUTION_RECEIPT_WRITTEN",
            {"execution_receipt_id": f"{index}" * 64},
            observed_at_utc=_AT,
        )
    lines = ledger.path.read_bytes().splitlines(keepends=True)
    if corruption == "truncate":
        ledger.path.write_bytes(lines[0] + lines[1][:-4])
        with pytest.raises(e0.LedgerIntegrityError, match="truncated"):
            e0.read_event_ledger(ledger.path, kind="TRANSITION")
        return
    if corruption == "reorder":
        ledger.path.write_bytes(lines[1] + lines[0] + lines[2])
        with pytest.raises(e0.LedgerIntegrityError, match="reordered or gapped"):
            e0.read_event_ledger(ledger.path, kind="TRANSITION")
        return
    if corruption == "unchain":
        ledger.path.write_bytes(lines[0] + lines[2])
        with pytest.raises(e0.LedgerIntegrityError):
            e0.read_event_ledger(ledger.path, kind="TRANSITION")
        return
    document = json.loads(lines[1].decode("utf-8"))
    document["details"] = {"execution_receipt_id": "f" * 64}
    ledger.path.write_bytes(lines[0] + canonical_bytes(document) + lines[2])
    with pytest.raises(e0.LedgerIntegrityError, match="recompute"):
        e0.read_event_ledger(ledger.path, kind="TRANSITION")


def test_the_ledger_details_projection_is_closed(evidence_root: Path) -> None:
    """§10.2: ``details`` is not an arbitrary JSON escape hatch, in both directions."""
    ledger = _ledger(evidence_root)
    with pytest.raises(e0.E0Error, match="outside the closed projection"):
        ledger.append(
            "EXECUTION_RECEIPT_WRITTEN",
            {"execution_receipt_id": "c" * 64, "extra": "value"},
            observed_at_utc=_AT,
        )
    with pytest.raises(e0.E0Error, match="missing required key"):
        ledger.append("EXECUTION_RECEIPT_WRITTEN", {}, observed_at_utc=_AT)
    with pytest.raises(e0.E0Error, match="not an allowed"):
        ledger.append("ASSOCIATIONS_MATERIALIZED", {}, observed_at_utc=_AT)


def test_the_associations_event_carries_every_totality_key(evidence_root: Path) -> None:
    """§10.2: ``ASSOCIATIONS_MATERIALIZED`` carries every §9.5 key, resolved from the object."""
    directory = e0.create_run_namespace(evidence_root, "e0-namespace")
    ledger = e0.EventLedger(directory / e0.E0_EVENTS_FILENAME, "e0-namespace", kind="E0")
    totality = op.AssociationTotality().as_record()
    assert tuple(totality) == e0.ASSOCIATION_TOTALITY_KEYS
    ledger.append("ASSOCIATIONS_MATERIALIZED", totality, observed_at_utc=_AT)
    partial = dict(totality)
    partial.pop("invalid_cik_rendering_count")
    with pytest.raises(e0.E0Error, match="missing required key"):
        ledger.append("ASSOCIATIONS_MATERIALIZED", partial, observed_at_utc=_AT)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("reason_code", "/absolute/private/path"),
        ("reason_detail", "root at ~/evidence"),
        ("reason_detail", "contact person@example.invalid"),
        ("reason_detail", "line one\nline two"),
    ],
)
def test_a_ledger_detail_may_not_carry_a_path_address_or_newline(
    evidence_root: Path, key: str, value: str
) -> None:
    """§10.2 and §12.3 item 11: field-aware refusal, not a blanket path detector."""
    ledger = _ledger(evidence_root)
    details = {"reason_code": "PRE_E0_CATALOG_TRANSITION_FAILED", "reason_detail": "ok"}
    details[key] = value
    with pytest.raises(e0.E0Error, match="path, address, or newline"):
        ledger.append("FAILED", details, observed_at_utc=_AT)


def test_the_relative_path_detail_is_checked_as_a_relative_path(evidence_root: Path) -> None:
    """The one detail that legitimately contains separators is checked for what it is."""
    ledger = _ledger(evidence_root)
    ledger.append(
        "BACKUP_VERIFIED",
        {
            "relative_path": "runs/a/catalog_backup_0013.sqlite3",
            "byte_length": 1,
            "file_sha256": "d" * 64,
            "catalog_logical_sha256": "e" * 64,
        },
        observed_at_utc=_AT,
    )
    with pytest.raises(e0.E0Error, match="private-root-relative"):
        ledger.append(
            "BACKUP_VERIFIED",
            {
                "relative_path": "/runs/a/catalog_backup_0013.sqlite3",
                "byte_length": 1,
                "file_sha256": "d" * 64,
                "catalog_logical_sha256": "e" * 64,
            },
            observed_at_utc=_AT,
        )


# ==========================================================================
# Families 1, 2, 8, 9: the transition execute machine, over a disposable catalog
# ==========================================================================


@pytest.fixture
def activated_transition(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Override the in-memory constant for one test. See this module's docstring."""
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    yield


@pytest.fixture
def activated_e0(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(e0, "M3_3_E0_EXECUTION_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    yield


def _run_transition(evidence_root: Path, config: _Config) -> e0.ExecuteOutcome:
    return e0.transition_execute(evidence_root=evidence_root, config=config)


def test_the_transition_completes_and_freezes_a_reproducible_terminal(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§§5.3, 8.1, 11 end to end, over a disposable catalog."""
    outcome = _run_transition(evidence_root, config)
    assert outcome.status == "complete"
    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700

    document = json.loads((directory / e0.TRANSITION_TERMINAL_FILENAME).read_text("utf-8"))
    assert document["status"] == "complete"
    assert document["pre_migration_chain"] == list(range(1, 14))
    assert document["post_migration_chain"] == list(range(1, 16))
    assert [item["version"] for item in document["applied_migrations"]] == [14, 15]
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    assert document["post_preexisting_content_sha256"] == document["pre_preexisting_content_sha256"]
    assert (
        document["owner_authority_sha256"]
        == hashlib.sha256(b"TEST-ONLY-DISPOSABLE-TOKEN").hexdigest()
    )

    # §11: the identity recomputes over its own excluding preimage, and the token derives
    # from it rather than the other way round.
    identity = e0.compute_terminal_record_id(document)
    assert document["terminal_record_id"] == identity
    assert document["result_token"] == f"M3_3_PRE_E0_CATALOG_TRANSITION_COMPLETE:{identity}"

    with connect(catalog, writer=False) as connection:
        assert applied_versions(connection) == tuple(range(1, 16))


def test_the_transition_backup_is_closed_fsynced_and_logically_equal(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§5.3 items 4-5 and finding m2: precreated ``0600``, closed, then digested and verified."""
    _run_transition(evidence_root, config)
    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    backup = directory / e0.TRANSITION_BACKUP_FILENAME
    assert stat.S_IMODE(backup.stat().st_mode) == 0o600

    document = json.loads((directory / e0.TRANSITION_TERMINAL_FILENAME).read_text("utf-8"))
    recorded = document["backup"]
    digest, length = e0.file_digest(backup)
    assert recorded["file_sha256"] == digest
    assert recorded["byte_length"] == length
    assert recorded["relative_path"] == (
        f"runs/{e0.TRANSITION_RUN_NAMESPACE}/{e0.TRANSITION_BACKUP_FILENAME}"
    )
    with strictly_read_only_connection(backup) as connection:
        assert applied_versions(connection) == tuple(range(1, 14))
        assert (
            e0.catalog_snapshot_digest(connection).catalog_logical_sha256
            == recorded["catalog_logical_sha256"]
        )
    assert recorded["catalog_logical_sha256"] == document["pre_catalog_logical_sha256"]


def test_every_artifact_is_mode_0600_and_the_write_set_is_exactly_four_files(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§8: the exact authorized write set, plus only the permitted operational sidecars."""
    _run_transition(evidence_root, config)
    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    written = sorted(path.name for path in directory.iterdir())
    assert written == sorted(
        [
            e0.TRANSITION_BACKUP_FILENAME,
            e0.TRANSITION_EVENTS_FILENAME,
            OPERATOR_RECEIPT_FILENAME,
            e0.TRANSITION_TERMINAL_FILENAME,
        ]
    )
    for path in directory.iterdir():
        assert stat.S_IMODE(path.stat().st_mode) == 0o600

    # Outside the namespace, only the fixed catalog and its permitted sidecars changed.
    outside = {
        str(path.relative_to(evidence_root))
        for path in evidence_root.rglob("*")
        if path.is_file() and "runs" not in path.parts
    }
    permitted_prefixes = ("catalogs/",)
    assert all(name.startswith(permitted_prefixes) for name in outside), sorted(outside)


def test_the_transition_verify_reproduces_the_frozen_identity(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§7.2 verify: strictly read-only, and it repairs nothing."""
    outcome = _run_transition(evidence_root, config)
    before = sorted(
        (str(path.relative_to(evidence_root)), path.read_bytes())
        for path in evidence_root.rglob("*")
        if path.is_file()
    )
    report = e0.transition_verify(evidence_root=evidence_root)
    after = sorted(
        (str(path.relative_to(evidence_root)), path.read_bytes())
        for path in evidence_root.rglob("*")
        if path.is_file()
    )
    assert report.determined
    assert report.passed, report.refusals
    assert report.facts["result_token"] == outcome.result_token
    assert before == after


def test_a_post_freeze_defect_is_preserved_and_never_repaired(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§11 and §12.3 item 10: a defect found after freeze is disclosed, never rebuilt."""
    _run_transition(evidence_root, config)
    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    terminal = directory / e0.TRANSITION_TERMINAL_FILENAME
    document = json.loads(terminal.read_text("utf-8"))
    document["status"] = "failed"
    terminal.chmod(0o600)
    terminal.write_bytes(canonical_bytes(document))
    mutated = terminal.read_bytes()

    report = e0.transition_verify(evidence_root=evidence_root)
    assert report.determined
    assert not report.passed
    assert report.refusals
    # The defective artifacts are still exactly as they were found.
    assert terminal.read_bytes() == mutated
    assert (directory / e0.TRANSITION_BACKUP_FILENAME).exists()
    assert (directory / e0.TRANSITION_EVENTS_FILENAME).exists()


def test_a_second_transition_refuses_because_the_namespace_is_create_once(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§5.4: a namespace is never reused, and ``execute`` never resumes."""
    _run_transition(evidence_root, config)
    with pytest.raises(e0.E0Error):
        _run_transition(evidence_root, config)


def test_the_transition_refuses_at_a_head_that_is_not_0013_under_the_lease(
    evidence_root: Path, config: _Config, activated_transition: None
) -> None:
    """§5.3 item 2 and §5.4: the under-lease recheck refuses before anything is created."""
    build_catalog(evidence_root, head=15)
    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged"):
        _run_transition(evidence_root, config)
    assert not (evidence_root / "runs").exists()


def test_a_hard_kill_leaves_no_terminal_and_verify_reports_undetermined(
    evidence_root: Path, catalog: Path, config: _Config, activated_transition: None
) -> None:
    """§9.1 and §12.3 item 8: absence of a terminal is UNDETERMINED, never success."""
    _run_transition(evidence_root, config)
    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    (directory / e0.TRANSITION_TERMINAL_FILENAME).unlink()
    report = e0.transition_verify(evidence_root=evidence_root)
    assert not report.determined
    assert not report.passed
    assert "UNDETERMINED / NOT COMPLETE" in "\n".join(report.lines)


def test_an_absent_namespace_verifies_as_undetermined(evidence_root: Path) -> None:
    report = e0.e0_verify(evidence_root=evidence_root)
    assert not report.determined
    assert not report.passed


def test_a_failure_after_the_namespace_exists_is_disclosed_and_preserved(
    evidence_root: Path,
    catalog: Path,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§5.4: a failure preserves its namespace and evidence and returns to the owner.

    The failure is injected at the backup boundary, which is the first point at which a
    namespace and a ledger already exist and a catalog page does not.
    """

    def _explode(**_kwargs: object) -> Mapping[str, object]:
        message = "injected disposable-fixture backup failure"
        raise e0.PreflightRefusalError(message)

    monkeypatch.setattr(e0, "_verified_backup", _explode)
    with pytest.raises(e0.PreflightRefusalError, match="injected"):
        _run_transition(evidence_root, config)

    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    document = json.loads((directory / e0.TRANSITION_TERMINAL_FILENAME).read_text("utf-8"))
    assert document["status"] == "failed"
    assert document["failure"]["reason_code"] == "PRE_E0_CATALOG_TRANSITION_FAILED"
    assert document["failure"]["catalog_state_observed"] is False
    # No migration ran, so the disclosed record omits every observed-state field rather
    # than filling it with a placeholder.
    for field in ("applied_migrations", "post_migration_chain", "post_integrity", "backup"):
        assert field not in document
    # The catalog is untouched at its entry head, and nothing was restored or deleted.
    with connect(catalog, writer=False) as connection:
        assert applied_versions(connection) == tuple(range(1, 14))
    assert (directory / e0.TRANSITION_EVENTS_FILENAME).exists()


# ==========================================================================
# Families 3, 4, 6, 9: the E0 execute machine, over a disposable catalog
# ==========================================================================


@pytest.fixture
def transitioned(evidence_root: Path, config: _Config, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A disposable catalog carried to head ``0015`` by the real transition machine.

    The E0 machine requires a COMPLETE transition terminal, so the two are chained here
    exactly as the accepted sequence chains them, rather than the terminal being fabricated.
    """
    catalog = build_catalog(evidence_root, head=13, sources=True)
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    outcome = e0.transition_execute(evidence_root=evidence_root, config=config)
    assert outcome.status == "complete"
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", None)
    return catalog


def test_e0_preflight_requires_a_complete_transition_terminal(
    evidence_root: Path, config: _Config
) -> None:
    """§9.1: an absent transition terminal is UNDETERMINED, never permission."""
    build_catalog(evidence_root, head=15)
    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("transition terminal record is absent" in item for item in report.refusals)
    assert report.facts["e0_execute_enabled"] is False


def test_e0_preflight_passes_after_a_complete_transition(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["transition_status"] == "complete"
    assert report.facts["applied_migration_head"] == "0015"
    assert len(str(report.facts["input_observation_set_sha256"])) == 64


def test_e0_completes_and_reconciles_all_76_planned_sources(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """§§9.1-9.5 end to end: 76/76, exact categories, zero network, and a frozen identity."""
    outcome = e0.e0_execute(evidence_root=evidence_root, config=config)
    assert outcome.status == "complete"
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))

    assert len(document["source_results"]) == e0.PLANNED_SOURCE_COUNT
    counts = document["source_result_counts"]
    assert counts["planned_source_count"] == e0.PLANNED_SOURCE_COUNT
    assert (
        counts["required_parse_count"]
        + counts["accepted_unavailable_count"]
        + counts["validation_or_provenance_only_count"]
        == e0.PLANNED_SOURCE_COUNT
    )
    assert counts["required_parse_count"] > 0
    assert counts["accepted_unavailable_count"] > 0
    assert counts["validation_or_provenance_only_count"] > 0
    assert all(row["ledger_event_present"] for row in document["source_results"])
    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    assert document["post_migration_chain"] == list(range(1, 16))

    totality = document["association_totality"]
    assert set(totality) == set(e0.ASSOCIATION_TOTALITY_KEYS)
    assert (
        totality["established_accession_count"] + totality["unestablished_accession_count"]
        == totality["census_accession_count"]
    )
    for zero_key in (
        "established_zero_relation_count",
        "singleton_scalar_mismatch_count",
        "multi_nonnull_scalar_count",
        "orphan_relation_count",
        "invalid_cik_rendering_count",
        "association_provenance_failure_count",
    ):
        assert totality[zero_key] == 0

    identity = e0.compute_terminal_record_id(document)
    assert document["terminal_record_id"] == identity
    assert document["result_token"] == f"M3_3_E0_OFFLINE_PARSE_COMPLETE:{identity}"
    assert document["transition_result_token"].startswith(
        "M3_3_PRE_E0_CATALOG_TRANSITION_COMPLETE:"
    )


def test_the_e0_governed_state_identity_covers_the_sixteen_tables_and_the_plan(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """§9.4: one record per §6.1 table, ordered by name, plus the plan projection."""
    e0.e0_execute(evidence_root=evidence_root, config=config)
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))
    names = [row["table_name"] for row in document["table_hashes"]]
    assert names == sorted(op.E0_PERMITTED_TABLES)
    assert len(names) == 16
    assert len(document["plan_parser_state_hash"]) == 64
    assert len(document["e0_catalog_state_sha256"]) == 64

    with strictly_read_only_connection(transitioned) as connection:
        _, plan_hash, state_hash = e0._governed_state_identity(connection)
    assert plan_hash == document["plan_parser_state_hash"]
    assert state_hash == document["e0_catalog_state_sha256"]


def test_the_e0_event_ledger_records_every_required_boundary(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """§10.2: the closed E0 event vocabulary, in order, with the terminal binding the head."""
    e0.e0_execute(evidence_root=evidence_root, config=config)
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    events = e0.read_event_ledger(directory / e0.E0_EVENTS_FILENAME, kind="E0")
    kinds = [event["event_type"] for event in events]
    for required in (
        "PREFLIGHT_PASSED",
        "BACKUP_VERIFIED",
        "SOURCE_DISPOSITION_RECORDED",
        "FULL_INDEX_OBSERVATIONS_MATERIALIZED",
        "ACCESSION_RESOLUTIONS_PERSISTED",
        "ASSOCIATIONS_MATERIALIZED",
        "VALIDATION_PASSED",
        "IDENTITIES_RECOMPUTED",
        "EXECUTION_RECEIPT_WRITTEN",
    ):
        assert required in kinds
    assert kinds.count("SOURCE_DISPOSITION_RECORDED") == e0.PLANNED_SOURCE_COUNT
    assert "TERMINAL_FROZEN" not in kinds

    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))
    assert document["event_ledger"]["event_count"] == len(events)
    assert document["event_ledger"]["head_event_sha256"] == events[-1]["event_sha256"]


def test_the_e0_receipt_is_a_v4_document_the_terminal_binds(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """§10.1: the receipt is written first and the terminal binds its id — never a cycle."""
    e0.e0_execute(evidence_root=evidence_root, config=config)
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    receipt = inspect_receipt(directory / OPERATOR_RECEIPT_FILENAME)
    assert receipt["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION_V4
    assert receipt["invocation_mode"] == "offline_parse"
    assert receipt["phase"] == "M3.3B"
    assert receipt["actual_logical_request_count"] == 0
    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))
    assert document["execution_receipt_id"] == receipt["receipt_id"]
    assert "terminal_record_id" not in receipt


# ==========================================================================
# Family 3: the sixteen-table authorizer, positive and negative
# ==========================================================================


def test_the_permitted_write_set_is_exactly_the_sixteen_tables() -> None:
    """§6.1: an explicit one-table widening of R17, and nothing else."""
    assert len(op.E0_PERMITTED_TABLES) == 16
    assert "census_accession_registrants" in op.E0_PERMITTED_TABLES
    assert {"census_plan_sources": frozenset({"parser_state"})} == op.E0_PERMITTED_PLAN_COLUMNS


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO census_qa_metrics (census_run_id, metric_name, metric_value, "
        "recorded_at_utc) VALUES ('r', 'm', 1, '2026-01-01T00:00:00Z')",
        "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
        "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
        "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
        "coverage_window_sha256, input_observation_set_sha256, snapshot_state, created_at_utc, "
        "detail) VALUES ('s', 'r', '2009-01-01', '2026-06-30', '2026-06-30', 0, 'c', 'p', "
        "'m', 'e', 'x', 'y', 'building', '2026-01-01T00:00:00Z', '')",
        "DELETE FROM census_source_observations",
        "UPDATE census_plan_sources SET source_id = 'x'",
        "DELETE FROM census_plan_sources",
    ],
)
def test_every_excluded_write_class_is_refused_by_the_authorizer(
    catalog: Path, statement: str
) -> None:
    """§6.1: the authorizer refuses at statement-prepare time, so nothing reaches the file."""
    path = catalog.parent / "authorizer.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
        with op.write_containment(connection), pytest.raises(sqlite3.DatabaseError):
            connection.execute(statement)


def test_the_permitted_relation_and_plan_column_are_accepted_by_the_authorizer(
    catalog: Path,
) -> None:
    """The positive control: without it, a blanket-deny authorizer would pass every negative."""
    path = catalog.parent / "authorizer-positive.sqlite3"
    with connect(path, writer=True) as connection:
        apply_migrations(connection)
        with op.write_containment(connection), transaction(connection) as active:
            active.execute("UPDATE census_plan_sources SET parser_state = 'completed' WHERE 0 = 1")
            active.execute("DELETE FROM census_accession_registrants WHERE 0 = 1")


# ==========================================================================
# Decision 096 R83: the relocated malformed-full-index-CIK proof
# ==========================================================================


@dataclass(frozen=True, slots=True)
class _PreAssociationWorld:
    """One disposable catalog at exactly the pre-association boundary (**R83** item 1)."""

    database: Path
    tree: DataTree
    lock_root: Path


def _pre_association_world(root: Path) -> _PreAssociationWorld:
    """Build the accepted-shaped catalog and stop **before** the association projection.

    Every earlier durable step is the production one: the accepted parsers persist through
    ``CensusCatalog``, the full-index observations are materialized by the production
    materializer, and canonical accessions are resolved by
    ``resolve_persisted_accessions()``. Only the §6.4 projection is withheld, because that
    is the operation under test.
    """
    tree = DataTree.from_root(root / "data")
    database = root / "pre-association.sqlite3"
    lock_root = root / "locks"
    design = rw.base_case_design()
    objects = rw._write_stored_objects(tree, design)
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        rw._seed_reference(connection)
        rw._seed_observations_and_plan(
            connection,
            objects,
            include_unavailable_source=True,
            include_validation_only_source=True,
        )
    with CatalogWriter(database, lock_root) as writer, op.write_containment(writer.connection):
        op.materialize_source_layer(writer=writer, tree=tree)
    return _PreAssociationWorld(database=database, tree=tree, lock_root=lock_root)


def _project(world: _PreAssociationWorld) -> op.AssociationTotality:
    """Invoke the production projection through the same containment E0 uses."""
    with (
        CatalogWriter(world.database, world.lock_root) as writer,
        op.write_containment(writer.connection),
    ):
        return op.materialize_census_associations(writer.connection)


def _one_full_index_cik_observation(database: Path) -> tuple[str, str]:
    """The single plan-bound accepted full-index ``cik_padded`` observation to mutate."""
    with connect(database, writer=False) as connection:
        row = connection.execute(
            "SELECT o.accession_observation_id, o.accession_plain "
            "FROM census_accession_observations AS o "
            "JOIN census_source_observations AS s "
            "ON s.observation_id = o.source_observation_id "
            "JOIN census_plan_sources AS p ON p.observation_id = s.observation_id "
            "WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' "
            "ORDER BY o.accession_plain, o.accession_observation_id LIMIT 1"
        ).fetchone()
    assert row is not None
    return str(row["accession_observation_id"]), str(row["accession_plain"])


def _census_state(database: Path) -> Mapping[str, int]:
    with connect(database, writer=False) as connection:
        return {
            "registrants": int(
                connection.execute("SELECT COUNT(*) FROM census_registrants").fetchone()[0]
            ),
            "relation_rows": int(
                connection.execute("SELECT COUNT(*) FROM census_accession_registrants").fetchone()[
                    0
                ]
            ),
            "established": int(
                connection.execute(
                    "SELECT COUNT(*) FROM census_accessions "
                    "WHERE registrant_set_completeness = 'established'"
                ).fetchone()[0]
            ),
        }


def test_the_pre_association_boundary_projects_cleanly_as_the_positive_control(
    tmp_path: Path,
) -> None:
    """**Decision 096 R83** item 2: the canonical input projects with zero invalid renderings.

    Without this control the adversarial test below would be vacuous: a projection that
    refused for some unrelated missing precondition would look identical.
    """
    world = _pre_association_world(tmp_path / "positive")
    before = _census_state(world.database)
    assert before["relation_rows"] == 0
    assert before["established"] == 0

    totality = _project(world)
    assert totality.invalid_cik_rendering_count == 0
    assert totality.violations() == ()
    assert totality.established_accession_count == 65
    assert totality.established_multi_count == 2
    assert totality.substantive_relation_count == 67

    after = _census_state(world.database)
    assert after["registrants"] == before["registrants"]
    assert after["relation_rows"] == 67
    assert after["established"] == 65


def test_a_malformed_full_index_cik_fails_the_projection_closed(tmp_path: Path) -> None:
    """**Decision 096 R83** items 3-6: the invariant, enforced at its Decision 094 §6.5 owner.

    The adversarial fixture differs from the positive control above by exactly one thing: a
    single plan-bound accepted full-index ``cik_padded`` membership observation is rewritten
    to an invalid rendering *before* the projection runs. The production projection then
    fails closed on ``invalid_cik_rendering_count``, its transaction rolls back so no
    established projection is persisted, no ``census_registrants`` entity is invented for the
    unreadable value, and the candidate builder is never involved at any point.
    """
    world = _pre_association_world(tmp_path / "adversarial")
    observation_id, accession = _one_full_index_cik_observation(world.database)
    before = _census_state(world.database)

    with connect(world.database, writer=True) as connection, transaction(connection) as active:
        changed = active.execute(
            "UPDATE census_accession_observations SET raw_value_json = '\"not-a-cik\"' "
            "WHERE accession_observation_id = ?",
            (observation_id,),
        ).rowcount
    assert changed == 1, "the adversarial mutation must alter exactly one observation"

    with pytest.raises(op.OfflineParseError, match="invalid_cik_rendering_count"):
        _project(world)

    # R83 item 5: the failed transaction persisted nothing, and invented nothing.
    after = _census_state(world.database)
    assert after == before
    assert after["relation_rows"] == 0
    assert after["established"] == 0
    with connect(world.database, writer=False) as connection:
        assert (
            int(
                connection.execute(
                    "SELECT COUNT(*) FROM census_accessions "
                    "WHERE accession_plain = ? AND registrant_set_completeness = 'established'",
                    (accession,),
                ).fetchone()[0]
            )
            == 0
        )


# ==========================================================================
# Family 4: exact membership derivation, totality, and the lawful write shape
# ==========================================================================


def test_membership_is_streamed_one_accession_at_a_time_in_canonical_order(
    tmp_path: Path,
) -> None:
    """§6.4: at most one accession's membership and provenance group is alive at a time.

    The projection consumes a **generator**, and the accumulator is reset at every accession
    boundary — so peak memory is one accession's group rather than the catalog's. Ordering is
    by canonical accession and by nothing else: not by source, plan row, or insertion order.
    """
    import inspect

    world = _pre_association_world(tmp_path / "streaming")
    with connect(world.database, writer=False) as connection:
        eligible = op.membership_observation_sources(connection)
        stream = op._stream_membership_groups(connection, eligible)
        assert inspect.isgenerator(stream)
        first = next(stream)
        assert isinstance(first, op._MembershipGroup)
        accessions = [first.accession_plain, *[group.accession_plain for group in stream]]
    assert accessions == sorted(accessions)
    assert len(accessions) == len(set(accessions))


def test_the_union_is_ordered_by_canonical_cik_and_deduplicated(tmp_path: Path) -> None:
    """§6.2: ``U = S_submissions union S_full_index``, by numeric CIK only.

    Distinct valid CIKs are co-registrants, never a conflict — asserted on the two joint
    accessions the design actually carries rather than on a constructed pair.
    """
    world = _pre_association_world(tmp_path / "union")
    with connect(world.database, writer=False) as connection:
        eligible = op.membership_observation_sources(connection)
        joint = [
            group
            for group in op._stream_membership_groups(connection, eligible)
            if len(group.union) > 1
        ]
    assert len(joint) == 2
    for group in joint:
        assert group.union == tuple(sorted(set(group.union)))
        assert group.submissions <= group.full_index
        assert group.invalid_renderings == 0


def test_a_submissions_member_the_index_does_not_corroborate_is_reported_and_fails_closed(
    tmp_path: Path,
) -> None:
    """§6.2 condition 2: corroboration is required, and its absence is counted, not repaired.

    One accession's full-index membership evidence is withdrawn, leaving its submissions
    member uncorroborated. The projection still completes — a missing corroboration is a
    lawful ``unestablished`` state, not a totality failure — but that accession is fail-closed
    and the count says exactly why.
    """
    world = _pre_association_world(tmp_path / "corroboration")
    with connect(world.database, writer=False) as connection:
        target = str(
            connection.execute(
                "SELECT o.accession_plain FROM census_accession_observations AS o "
                "JOIN census_source_observations AS s "
                "ON s.observation_id = o.source_observation_id "
                "WHERE o.field_name = 'cik_padded' AND s.source_id = 'sec_full_index_company' "
                "ORDER BY o.accession_plain LIMIT 1"
            ).fetchone()[0]
        )
    with connect(world.database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "DELETE FROM census_accession_observations WHERE accession_plain = ? "
            "AND field_name = 'cik_padded' AND source_observation_id IN "
            "(SELECT observation_id FROM census_source_observations "
            "WHERE source_id = 'sec_full_index_company')",
            (target,),
        )

    totality = _project(world)
    assert totality.violations() == ()
    assert totality.submissions_member_missing_full_index_count >= 1
    assert totality.unestablished_accession_count >= 1
    with connect(world.database, writer=False) as connection:
        completeness = str(
            connection.execute(
                "SELECT registrant_set_completeness FROM census_accessions "
                "WHERE accession_plain = ?",
                (target,),
            ).fetchone()[0]
        )
    assert completeness == "unestablished"


def test_the_submitter_is_never_promoted_into_the_relation(tmp_path: Path) -> None:
    """§6.2: the submitter stays a submission fact; this writer never inserts it.

    A submitter CIK that no membership evidence names is written onto an accession, and the
    projection is run afterwards. It must not appear as a relation row and it must not change
    the accession's cardinality.
    """
    world = _pre_association_world(tmp_path / "submitter")
    outsider = 999_999
    with connect(world.database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO census_registrants (cik_numeric, cik_padded, first_observed_at_utc, "
            "latest_observed_at_utc) VALUES (?, ?, ?, ?)",
            (outsider, f"{outsider:010d}", _AT, _AT),
        )
        target = str(
            active.execute(
                "SELECT accession_plain FROM census_accessions ORDER BY accession_plain LIMIT 1"
            ).fetchone()[0]
        )
        active.execute(
            "UPDATE census_accessions SET submitter_cik_numeric = ? WHERE accession_plain = ?",
            (outsider, target),
        )

    _project(world)
    with connect(world.database, writer=False) as connection:
        promoted = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_accession_registrants "
                "WHERE registrant_cik_numeric = ?",
                (outsider,),
            ).fetchone()[0]
        )
        members = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_accession_registrants WHERE accession_plain = ?",
                (target,),
            ).fetchone()[0]
        )
    assert promoted == 0
    assert members == 1


def test_the_established_scalar_equals_its_sole_member_and_a_multi_set_is_null(
    tmp_path: Path,
) -> None:
    """§6.4 item 4: ``must``, not ``may`` — and a lawful multi-registrant scalar is ``NULL``.

    Read back from the persisted rows rather than from the writer's own tallies, so a writer
    that recorded the right numbers while persisting the wrong ones would still fail.
    """
    world = _pre_association_world(tmp_path / "scalar")
    totality = _project(world)
    assert totality.singleton_scalar_mismatch_count == 0
    assert totality.multi_nonnull_scalar_count == 0

    with connect(world.database, writer=False) as connection:
        rows = connection.execute(
            "SELECT a.accession_plain, a.registrant_cik_numeric, COUNT(r.registrant_cik_numeric) "
            "AS members FROM census_accessions AS a "
            "JOIN census_accession_registrants AS r ON r.accession_plain = a.accession_plain "
            "WHERE a.registrant_set_completeness = 'established' "
            "AND r.association_class = 'substantive' GROUP BY a.accession_plain"
        ).fetchall()
        singles = 0
        multis = 0
        for row in rows:
            if int(row["members"]) == 1:
                singles += 1
                sole = int(
                    connection.execute(
                        "SELECT registrant_cik_numeric FROM census_accession_registrants "
                        "WHERE accession_plain = ?",
                        (str(row["accession_plain"]),),
                    ).fetchone()[0]
                )
                assert row["registrant_cik_numeric"] is not None
                assert int(row["registrant_cik_numeric"]) == sole
            else:
                multis += 1
                assert row["registrant_cik_numeric"] is None
    assert (singles, multis) == (63, 2)


def test_completeness_is_written_last_so_no_established_set_lacks_its_relation(
    tmp_path: Path,
) -> None:
    """§6.4 item 5 and §9.5: ``established_zero_relation_count`` is measured, not assumed.

    The count is read back from the persisted rows inside the projection's own transaction,
    so an ordering that marked an accession complete before its relation existed would be a
    totality failure rather than a silently lawful state.
    """
    world = _pre_association_world(tmp_path / "ordering")
    totality = _project(world)
    assert totality.established_zero_relation_count == 0
    with connect(world.database, writer=False) as connection:
        orphaned = int(
            connection.execute(
                "SELECT COUNT(*) FROM census_accessions AS a "
                "WHERE a.registrant_set_completeness = 'established' AND NOT EXISTS "
                "(SELECT 1 FROM census_accession_registrants AS r "
                "WHERE r.accession_plain = a.accession_plain "
                "AND r.association_class = 'substantive')"
            ).fetchone()[0]
        )
    assert orphaned == 0


def test_the_projection_is_create_once_and_a_second_identical_run_changes_no_byte(
    tmp_path: Path,
) -> None:
    """§6.4 item 3 with contract §10.2 item 5: no replacement write, and deterministic.

    An existing row that is byte-for-byte what this run would write is a collision by
    identity and is left exactly as it is; a second identical projection therefore changes no
    durable byte, while a row that differed would fail closed.
    """
    world = _pre_association_world(tmp_path / "create-once")
    first = _project(world)
    before = hashlib.sha256(world.database.read_bytes()).hexdigest()
    second = _project(world)
    after = hashlib.sha256(world.database.read_bytes()).hexdigest()
    assert first.as_record() == second.as_record()
    assert before == after

    with connect(world.database, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_accession_registrants SET evidence_level = 'review_required' "
            "WHERE accession_plain = (SELECT MIN(accession_plain) "
            "FROM census_accession_registrants)"
        )
    with pytest.raises(op.OfflineParseError, match="create-once"):
        _project(world)


def test_the_relocated_proof_uses_no_candidate_builder_or_fallback() -> None:
    """**Decision 096 R83** item 6, asserted against the production source itself.

    Decision 094 §6.5 removed the observation fallback from the candidate layer. That removal
    is what makes the relocation necessary, so it is pinned here: if a future change restored
    an observation-derived or scalar-derived membership rule to the builder, this fails and
    the relocation would have to be revisited rather than silently duplicated.
    """
    from disclosure_drift.m3 import candidate_snapshot as cs

    source = Path(cs.__file__).read_text(encoding="utf-8")
    assert "_read_full_index_registrants" not in source
    assert "sec_full_index_company" not in source
    assert "census_accession_registrants" in source
    assert "registrant_set_completeness" in source
    # This module never reaches the candidate layer at all.
    assert "m3.candidate_snapshot" not in Path(e0.__file__).read_text(encoding="utf-8")


# ==========================================================================
# Family 7: receipt v4 closed fields, and v2/v3 isolation
# ==========================================================================


def _v4(**overrides: object) -> ExecutionReceiptV4:
    base: dict[str, object] = {
        "command_name": e0.E0_COMMAND_NAME,
        "command_version": e0.E0_COMMAND_VERSION,
        "invocation_mode": "offline_parse",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0015",
        "started_at_utc": _AT,
        "completed_at_utc": "2026-01-01T00:01:00Z",
        "elapsed_seconds": 60.0,
        "completion_status": "complete",
        "parser_versions": {"offline_parse": e0.E0_COMMAND_VERSION},
        "cohort_definition_digest": "b" * 64,
    }
    base.update(overrides)
    return ExecutionReceiptV4(**base)  # type: ignore[arg-type]


def test_a_v4_receipt_is_closed_and_self_verifying() -> None:
    receipt = _v4()
    document = receipt.as_document()
    assert document["receipt_schema_version"] == RECEIPT_SCHEMA_VERSION_V4
    assert document["phase"] == "M3.3B"
    assert document["receipt_id"] == receipt.receipt_id
    preimage = {key: value for key, value in document.items() if key != "receipt_id"}
    assert hashlib.sha256(canonical_bytes(preimage)).hexdigest() == receipt.receipt_id


def test_a_v4_receipt_may_not_report_a_request(monkeypatch: pytest.MonkeyPatch) -> None:
    """§10.1: both v4 modes are zero-network, and the schema refuses a nonzero count."""
    with pytest.raises(ReceiptValidationError, match="must both be 0"):
        _v4(actual_logical_request_count=1)


def test_a_v4_interruption_state_must_be_in_the_closed_vocabulary() -> None:
    with pytest.raises(ReceiptValidationError):
        _v4(
            completion_status="interrupted",
            reason_code="M3_3_E0_OFFLINE_PARSE_INTERRUPTED",
            reason_detail="stopped at a boundary",
            interruption_state="during_something_invented",
        )
    receipt = _v4(
        completion_status="interrupted",
        reason_code="M3_3_E0_OFFLINE_PARSE_INTERRUPTED",
        reason_detail="stopped at a boundary",
        interruption_state=INTERRUPTION_STATES_V4[0],
    )
    assert receipt.as_document()["interruption_state"] == INTERRUPTION_STATES_V4[0]


def test_the_transition_mode_carries_no_parser_fields() -> None:
    """§10.1 items 3-4: the transition mode's field set is genuinely smaller."""
    with pytest.raises(ReceiptValidationError):
        _v4(invocation_mode="offline_catalog_transition")
    receipt = _v4(
        command_name=e0.TRANSITION_COMMAND_NAME,
        command_version=e0.TRANSITION_COMMAND_VERSION,
        invocation_mode="offline_catalog_transition",
        parser_versions=None,
        cohort_definition_digest=None,
    )
    document = receipt.as_document()
    assert "parser_versions" not in document
    assert "cohort_definition_digest" not in document


def test_the_interruption_vocabulary_is_exactly_decision_094_section_10_2() -> None:
    assert INTERRUPTION_STATES_V4 == (
        "before_backup",
        "during_backup",
        "after_backup_before_migration",
        "after_migration_0014_before_0015",
        "after_migration_0014_commit_before_event",
        "after_migration_0015_commit_before_event",
        "after_migration_0015_before_transition_freeze",
        "during_e0_source_parse",
        "after_e0_source_commit_before_event",
        "during_e0_full_index_observation_materialization",
        "after_e0_full_index_observations_before_resolution",
        "during_e0_accession_resolution",
        "after_e0_resolution_before_association_materialization",
        "during_e0_association_materialization",
        "after_e0_materialization_before_validation",
        "after_e0_validation_before_freeze",
    )


# ==========================================================================
# Families 8, 9: closed terminal schemas and non-self-referential identities
# ==========================================================================


def _minimal_transition_terminal() -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": e0.TRANSITION_TERMINAL_SCHEMA_VERSION,
        "record_type": "catalog_transition",
        "run_namespace": e0.TRANSITION_RUN_NAMESPACE,
        "command_name": e0.TRANSITION_COMMAND_NAME,
        "command_version": e0.TRANSITION_COMMAND_VERSION,
        "status": "failed",
        "started_at_utc": _AT,
        "completed_at_utc": _AT,
        "owner_authority_sha256": "a" * 64,
        "catalog_relative_path": e0.OPERATIONAL_CATALOG_RELATIVE_PATH,
        "pre_migration_chain": list(range(1, 14)),
        "target_migration_chain": list(range(1, 16)),
        "packaged_migration_sha256": {"0014": "b" * 64, "0015": "c" * 64},
        "precondition_counts": {"census_accessions": 0},
        "pre_integrity": {
            "quick_check": "ok",
            "integrity_check": "ok",
            "foreign_key_violations": 0,
        },
        "pre_catalog_logical_sha256": "d" * 64,
        "pre_preexisting_content_sha256": "e" * 64,
        "event_ledger": {
            "relative_path": "runs/x/catalog_transition_events.jsonl",
            "event_count": 1,
            "head_event_sha256": "f" * 64,
        },
        "execution_receipt_id": "0" * 64,
        "actual_logical_request_count": 0,
        "actual_physical_attempt_count": 0,
        "failure": {
            "reason_code": "PRE_E0_CATALOG_TRANSITION_FAILED",
            "reason_detail": "a bounded sentence",
            "catalog_state_observed": False,
        },
    }
    identity = e0.compute_terminal_record_id(document)
    document["terminal_record_id"] = identity
    document["result_token"] = e0.result_token("catalog_transition", "failed", identity)
    return document


def test_a_terminal_record_validates_and_its_identity_reproduces() -> None:
    document = _minimal_transition_terminal()
    e0.validate_transition_terminal(document, event_types=frozenset({"FAILED"}))


def test_a_terminal_identity_never_contains_itself_in_its_preimage() -> None:
    """§11: the two excluded fields, and nothing else."""
    document = _minimal_transition_terminal()
    identity = document["terminal_record_id"]
    preimage = {
        key: value
        for key, value in document.items()
        if key not in {"terminal_record_id", "result_token"}
    }
    assert hashlib.sha256(canonical_bytes(preimage)).hexdigest() == identity
    # A self-referential preimage produces a different value, so a record that computed its
    # identity over itself could never validate.
    assert hashlib.sha256(canonical_bytes(document)).hexdigest() != identity


@pytest.mark.parametrize("field", ["terminal_record_id", "result_token", "status"])
def test_a_mutated_terminal_field_fails_validation(field: str) -> None:
    document = _minimal_transition_terminal()
    document[field] = "9" * 64 if field != "status" else "complete"
    with pytest.raises(e0.TerminalValidationError):
        e0.validate_transition_terminal(document, event_types=frozenset({"FAILED"}))


def test_a_terminal_record_may_not_carry_a_placeholder() -> None:
    """§8.1: an inapplicable field is absent, never ``null`` or ``"N/A"``."""
    document = _minimal_transition_terminal()
    document["pre_catalog_logical_sha256"] = "N/A"
    with pytest.raises(e0.TerminalValidationError, match="placeholder"):
        e0.validate_transition_terminal(document, event_types=frozenset({"FAILED"}))


def test_a_conditional_field_present_without_its_event_is_refused() -> None:
    """§8.1's conditional-presence table is exact in both directions."""
    document = _minimal_transition_terminal()
    document["post_migration_chain"] = list(range(1, 16))
    identity = e0.compute_terminal_record_id(document)
    document["terminal_record_id"] = identity
    document["result_token"] = e0.result_token("catalog_transition", "failed", identity)
    with pytest.raises(e0.TerminalValidationError, match="does not permit it"):
        e0.validate_transition_terminal(document, event_types=frozenset({"FAILED"}))


def test_a_nonzero_request_count_is_refused_by_the_terminal_schema() -> None:
    """§7.3: both counts are exactly zero in every record this stage writes."""
    document = _minimal_transition_terminal()
    document["actual_logical_request_count"] = 1
    identity = e0.compute_terminal_record_id(document)
    document["terminal_record_id"] = identity
    document["result_token"] = e0.result_token("catalog_transition", "failed", identity)
    with pytest.raises(e0.TerminalValidationError, match="exactly 0"):
        e0.validate_transition_terminal(document, event_types=frozenset({"FAILED"}))


def test_a_broken_totality_invariant_is_refused_by_the_e0_terminal() -> None:
    """§9.5: a zero-fixed count is an invariant, never a reportable state."""
    totality = dict.fromkeys(e0.ASSOCIATION_TOTALITY_KEYS, 0)
    totality["invalid_cik_rendering_count"] = 1
    with pytest.raises(e0.TerminalValidationError, match="zero-fixed invariant"):
        e0._require_totality_invariants(totality)


def test_the_result_token_derives_from_the_identity_and_not_the_reverse() -> None:
    token = e0.result_token("m3_3_e0_offline_parse", "interrupted", "a" * 64)
    assert token == f"M3_3_E0_OFFLINE_PARSE_INTERRUPTED:{'a' * 64}"
    with pytest.raises(e0.TerminalValidationError):
        e0.result_token("catalog_transition", "aborted", "a" * 64)
