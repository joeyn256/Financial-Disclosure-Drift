"""PRE-E0 catalog transition and M3.3-E0 offline-parse proofs (accepted Decision 094 §12.3).

Every test here drives production code over a **disposable** temporary catalog beneath a
**synthetic** temporary root. Nothing in this module resolves, opens, names, prints, or infers
the accepted private evidence root, and nothing opens the accepted operational catalog: the
fixtures build their own catalog from the packaged migrations and delete it with the temporary
directory.

Two conventions carry most of the weight, and both are deliberate.

**Test-scoped activation.** :data:`~disclosure_drift.m3.e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY`
and :data:`~disclosure_drift.m3.e0.M3_3_E0_EXECUTION_AUTHORITY` gate the two ``execute`` state
machines, and each carries exactly the value its governing record gives it — which is what
``test_the_shipped_activation_constants_match_the_governing_record`` asserts against the *file*,
not against a runtime value. Accepted Decision 101 §7 activated the transition constant and §8
activated the E0 constant, each by its own separate owner act against its own distinct governed
token. Decision 094 §12.3 items 1-2 and 8-10 require both machines to be proved
non-vacuously whatever the shipped values are, so a test that needs a machine reachable
overrides the attribute for the duration of one test, and a test about the gate itself disables
it the same way. That is a harness override of an in-memory constant against a disposable
catalog; it changes no shipped byte, and it is the only mechanism by which "this machine is
correct" and "this machine is unreachable when its constant is ``None``" can both be checked
claims rather than assertions.

**Fail-closed reading.** Where a test asserts an absence — no namespace, no lease, no page, no
invented entity — it measures the absence directly rather than trusting a return value.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, replace
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
    ExecutionReceipt,
    ExecutionReceiptV4,
    ReceiptValidationError,
    canonical_bytes,
    content_derived_receipt_name,
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


# ==========================================================================
# Decision 099 R97: a disposable accepted-shaped M3.2 completion chain
#
# §5.2 predicate 3 binds the **accepted** M3.2 completion receipts, whose bytes this suite may
# not read and could not reproduce. Decision 099 §3 authorizes a disposable test to replace the
# fixed pins **in memory** with a synthetic accepted-shaped chain; the shipped literals stay the
# accepted ones and are asserted directly against the source file by
# `test_the_shipped_m3_2_completion_pins_are_the_accepted_ones`.
#
# Every value below is invented for a temporary directory. Nothing here resolves, reads, names,
# copies, or approximates the accepted private root, its catalog, or its receipts.
# ==========================================================================

_M3_2_HEAD_NAMESPACE = "m3_2_synthetic_continuation"
_M3_2_ROOT_NAMESPACE = "m3_2_synthetic_carry_in"

#: The head run is the run the seeded plan rows already carry, because `census_plan_sources` is
#: the accepted run-to-observation attribution relation and the fixture's plan is already bound
#: to that run. The row is relabelled into accepted M3.2 shape rather than a second plan being
#: invented, which would take the accepted plan size past its fixed 76.
_M3_2_HEAD_RUN_ID = rw.CENSUS_RUN_ID
_M3_2_ROOT_RUN_ID = "m3-2-acquisition-synthetic-carry-in-root"
_M3_2_HEAD_STARTED = "2026-08-11T09:00:00Z"
_M3_2_HEAD_COMPLETED = "2026-08-11T09:00:03Z"
_M3_2_ROOT_STARTED = "2026-08-10T09:00:00Z"
_M3_2_ROOT_COMPLETED = "2026-08-10T09:30:00Z"
_M3_2_HEAD_PLAN_SHA256 = "c" * 64
_M3_2_ROOT_PLAN_SHA256 = "b" * 64
_M3_2_HEAD_ATTEMPTS = 1
_M3_2_ROOT_ATTEMPTS = 3
_M3_2_ROOT_CARRIED_FORWARD = 1

#: The Decision 055 §7.5 arithmetic the production binding restates: the chain's own attempts
#: plus the root's carried-forward baseline, added exactly once. Deliberately **not** the head's
#: own carried-forward figure, which is `_M3_2_ROOT_CARRIED_FORWARD + _M3_2_ROOT_ATTEMPTS` and
#: would double-count if it were summed — so an implementation that added it fails this fixture.
_M3_2_CUMULATIVE = _M3_2_HEAD_ATTEMPTS + _M3_2_ROOT_ATTEMPTS + _M3_2_ROOT_CARRIED_FORWARD
_M3_2_SYNTHETIC_OBSERVATION = "obs-m3-2-synthetic-head"


def _acquisition_receipt(**overrides: object) -> ExecutionReceipt:
    """One accepted-shaped ``live`` M3.2A acquisition receipt over invented values."""
    fields: dict[str, object] = {
        "command_name": "m3 acquire",
        "command_version": "m3.2a/1.0",
        "phase": "M3.2A",
        "invocation_mode": "live",
        "configuration_fingerprint": "a" * 64,
        "migration_chain_head": "0013_m23_manifest_lifecycle_guards",
        "started_at_utc": _M3_2_ROOT_STARTED,
        "completed_at_utc": _M3_2_ROOT_COMPLETED,
        "elapsed_seconds": 1800.0,
        "source_registry_version": "m2.2-source-registry/1.0",
        "index_plan_policy_version": "quarterly-index-instances/2.0",
        "request_plan_schema_version": "m3-request-plan/1.0",
        "parser_versions": {"company-tickers": "1.0"},
        "acquisition_window": "M3.2A",
        "request_plan_id": "plan-synthetic",
        "request_plan_sha256": _M3_2_ROOT_PLAN_SHA256,
        "approved_request_ceiling": 801,
        "planned_logical_request_count": 3,
        "maximum_physical_attempt_count": 60,
        "planned_per_route": {"sec_company_tickers": 3},
        "actual_logical_request_count": _M3_2_ROOT_ATTEMPTS,
        "actual_physical_attempt_count": _M3_2_ROOT_ATTEMPTS,
        "actual_per_route": {
            "sec_company_tickers": {
                "logical_request_count": _M3_2_ROOT_ATTEMPTS,
                "physical_attempt_count": _M3_2_ROOT_ATTEMPTS,
            },
        },
        "response_classification_totals": {
            "proceed": _M3_2_ROOT_ATTEMPTS,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": _M3_2_ROOT_ATTEMPTS},
        "raw_object_count": _M3_2_ROOT_ATTEMPTS,
        "duplicate_object_count": 0,
        "cache_hit_count": 0,
        "not_modified_count": 0,
        "quarantined_object_count": 0,
        "redirect_hop_count": 0,
        "cooldown_count": 0,
        "schema_drift_outcome": "none",
        "schema_drift_event_count": 0,
        "completion_status": "failed",
        "reason_code": "SEC_ACQUISITION_INTERRUPTED",
        "reason_detail": "the synthetic carry-in root ended failed.",
        "consumed_request_count_carried_forward": _M3_2_ROOT_CARRIED_FORWARD,
        "carry_in_authority_sha256": "d" * 64,
    }
    fields.update(overrides)
    return ExecutionReceipt(**fields)


def _m3_2_root_receipt(**overrides: object) -> ExecutionReceipt:
    """The chain root: a `failed` clean carry-in with no predecessor of its own."""
    return _acquisition_receipt(**overrides)


def _m3_2_head_receipt(predecessor_receipt_id: str, **overrides: object) -> ExecutionReceipt:
    """The chain head: one `complete` logical request continuing the root."""
    fields: dict[str, object] = {
        "started_at_utc": _M3_2_HEAD_STARTED,
        "completed_at_utc": _M3_2_HEAD_COMPLETED,
        "elapsed_seconds": 3.0,
        "request_plan_sha256": _M3_2_HEAD_PLAN_SHA256,
        "actual_logical_request_count": _M3_2_HEAD_ATTEMPTS,
        "actual_physical_attempt_count": _M3_2_HEAD_ATTEMPTS,
        "actual_per_route": {
            "sec_sic_code_list": {
                "logical_request_count": _M3_2_HEAD_ATTEMPTS,
                "physical_attempt_count": _M3_2_HEAD_ATTEMPTS,
            },
        },
        "response_classification_totals": {
            "proceed": _M3_2_HEAD_ATTEMPTS,
            "retry": 0,
            "retry_after": 0,
            "cooldown": 0,
            "fail": 0,
            "quarantine": 0,
        },
        "status_code_totals": {"200": _M3_2_HEAD_ATTEMPTS},
        "raw_object_count": _M3_2_HEAD_ATTEMPTS,
        "completion_status": "complete",
        "reason_code": None,
        "reason_detail": None,
        "recovery_predecessor_receipt_id": predecessor_receipt_id,
        # A resumed head states what it inherited; the root's own baseline plus the root's
        # attempts. It is *not* a second term of the cumulative sum.
        "consumed_request_count_carried_forward": (
            _M3_2_ROOT_CARRIED_FORWARD + _M3_2_ROOT_ATTEMPTS
        ),
        "carry_in_authority_sha256": None,
    }
    fields.update(overrides)
    return _acquisition_receipt(**fields)


def _write_m3_2_receipt(evidence_root: Path, namespace: str, receipt: ExecutionReceipt) -> Path:
    directory = evidence_root / "runs" / namespace
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / OPERATOR_RECEIPT_FILENAME
    path.write_bytes(receipt.canonical_bytes())
    return path


def _seed_m3_2_catalog_binding(catalog: Path) -> str:
    """Write the accepted-shaped run rows, attempt ledger, and head observation attribution.

    Returns the head observation identity, which is an already plan-bound observation when the
    fixture seeded one and a purpose-built row otherwise. Reusing an existing binding matters:
    attaching a new observation to a category-B pad row would change what a real offline parse
    dispositions, and the parse is the subject of other tests in this module.
    """
    with connect(catalog, writer=True) as connection:
        row = connection.execute(
            "SELECT observation_id FROM census_plan_sources WHERE observation_id IS NOT NULL "
            "ORDER BY source_instance_id LIMIT 1"
        ).fetchone()
        observation = None if row is None else str(row[0])
        with transaction(connection) as active:
            if observation is None:
                observation = _M3_2_SYNTHETIC_OBSERVATION
                active.execute(
                    "INSERT INTO census_source_observations (observation_id, source_id, "
                    "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
                    "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
                    "content_size_bytes, storage_representation, relative_storage_path, "
                    "parser_version, recorded_at_utc) VALUES (?, 'sec_sic_code_list', "
                    "'req/sic/0', 'https://example.invalid/sic', 'census', ?, 'stored_new', "
                    "?, ?, ?, 1, 1, 'identical', 'raw/sec/bulk/sic.json', 'fixture/1.0', ?)",
                    (observation, _AT, "e" * 64, "e" * 64, "e" * 64, _AT),
                )
                active.execute(
                    "UPDATE census_plan_sources SET observation_id = ? WHERE source_instance_id "
                    "= (SELECT MIN(source_instance_id) FROM census_plan_sources)",
                    (observation,),
                )
            active.execute(
                "UPDATE ops_ingestion_jobs SET job_kind = ?, job_state = 'completed', "
                "stage = 'M3.2A', started_at_utc = ?, finished_at_utc = ? WHERE job_id = ?",
                (
                    e0.M3_2_ACQUISITION_JOB_KIND,
                    _M3_2_HEAD_STARTED,
                    _M3_2_HEAD_COMPLETED,
                    _M3_2_HEAD_RUN_ID,
                ),
            )
            active.execute(
                "INSERT OR REPLACE INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
                "started_at_utc, finished_at_utc, detail) VALUES (?, ?, 'failed', 'M3.2A', ?, ?, "
                "'')",
                (
                    _M3_2_ROOT_RUN_ID,
                    e0.M3_2_ACQUISITION_JOB_KIND,
                    _M3_2_ROOT_STARTED,
                    _M3_2_ROOT_COMPLETED,
                ),
            )
            for run_id, count in (
                (_M3_2_HEAD_RUN_ID, _M3_2_HEAD_ATTEMPTS),
                (_M3_2_ROOT_RUN_ID, _M3_2_ROOT_ATTEMPTS),
            ):
                for index in range(count):
                    active.execute(
                        "INSERT OR REPLACE INTO ops_retrieval_attempts (retrieval_attempt_id, "
                        "job_id, "
                        "source_url_canonical, logical_role, attempt_number, attempt_state, "
                        "started_at_utc) VALUES (?, ?, ?, 'metadata', ?, 'succeeded', ?)",
                        (f"attempt-{run_id}-{index}", run_id, "https://example.invalid/x", 1, _AT),
                    )
    return observation


@dataclass(frozen=True, slots=True)
class M32World:
    """One disposable accepted-shaped M3.2 completion chain and its installed binding."""

    binding: e0.AcquisitionCompletionBinding
    head_path: Path
    root_path: Path
    head: ExecutionReceipt
    root: ExecutionReceipt


def install_m3_2_binding(
    evidence_root: Path,
    catalog: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    head_overrides: Mapping[str, object] | None = None,
    root_overrides: Mapping[str, object] | None = None,
) -> M32World:
    """Build the synthetic chain, seed its catalog binding, and install the pins in memory."""
    root = _m3_2_root_receipt(**dict(root_overrides or {}))
    head = _m3_2_head_receipt(root.receipt_id, **dict(head_overrides or {}))
    root_path = _write_m3_2_receipt(evidence_root, _M3_2_ROOT_NAMESPACE, root)
    head_path = _write_m3_2_receipt(evidence_root, _M3_2_HEAD_NAMESPACE, head)
    observation = _seed_m3_2_catalog_binding(catalog)
    binding = e0.AcquisitionCompletionBinding(
        head=e0.AcquisitionReceiptPin(
            label="T7",
            relative_path=f"runs/{_M3_2_HEAD_NAMESPACE}/{OPERATOR_RECEIPT_FILENAME}",
            file_sha256=hashlib.sha256(head.canonical_bytes()).hexdigest(),
            receipt_id=head.receipt_id,
            run_id=_M3_2_HEAD_RUN_ID,
            completion_status="complete",
            request_plan_sha256=_M3_2_HEAD_PLAN_SHA256,
        ),
        predecessor=e0.AcquisitionReceiptPin(
            label="T6",
            relative_path=f"runs/{_M3_2_ROOT_NAMESPACE}/{OPERATOR_RECEIPT_FILENAME}",
            file_sha256=hashlib.sha256(root.canonical_bytes()).hexdigest(),
            receipt_id=root.receipt_id,
            run_id=_M3_2_ROOT_RUN_ID,
            completion_status="failed",
            request_plan_sha256=_M3_2_ROOT_PLAN_SHA256,
        ),
        acquisition_window="M3.2A",
        head_logical_request_count=_M3_2_HEAD_ATTEMPTS,
        head_physical_attempt_count=_M3_2_HEAD_ATTEMPTS,
        head_observation_id=observation,
        cumulative_physical_attempt_count=_M3_2_CUMULATIVE,
    )
    monkeypatch.setattr(e0, "M3_2_COMPLETION_BINDING", binding)
    return M32World(binding=binding, head_path=head_path, root_path=root_path, head=head, root=root)


@pytest.fixture
def catalog(evidence_root: Path) -> Path:
    """The accepted-shaped disposable catalog at head ``0013``, with 76 planned sources."""
    return build_catalog(evidence_root)


@pytest.fixture
def bound(evidence_root: Path, catalog: Path, monkeypatch: pytest.MonkeyPatch) -> M32World:
    """The disposable catalog plus its accepted-shaped §5.2 predicate 3 completion chain."""
    return install_m3_2_binding(evidence_root, catalog, monkeypatch)


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
# Family 13 + Decision 096 §6.2: a disabled constant makes its mode exit 3
# ==========================================================================


def test_the_shipped_activation_constants_match_the_governing_record() -> None:
    """§7.2, Decision 096 §6.2, and accepted Decision 108 §§2-3: the shipped literals.

    The runtime attribute is asserted too, but the **source** assertion is the load-bearing
    one: a runtime check alone would pass against a module some other test had already
    overridden, and this is the one property no test may leave ambiguous.

    Decision 101 §7 activated the transition constant and §8 activated the E0 constant, each by
    its own separate owner act — which is the independence §7.2 requires. Decision 107 §4 (R117)
    then set the E0 constant back to ``None`` before the stale writer lease was reconciled, so
    that clearing the lease could not re-enable E0-v2 as a side effect of an unrelated
    operation's success. Decision 108 §3 (R119) withdrew the spent transition grant and §2
    (R120) issued the separate E0-v2 instrument Decision 107 §5 reserved. **Decision 108 §5
    (R122) has now withdrawn that instrument too**: the one
    invocation it authorized started, was interrupted at ``BACKUP_VERIFIED`` with no terminal
    record, and R122 requires the withdrawal on return **whatever the outcome**. All three
    governed execute constants are therefore ``None`` again, and each half is asserted so a
    later reopening of one cannot drift into another.

    Every **spent** token's absence from the whole file is asserted for the same reason
    Decision 104's disabled-constant test asserts its own: a consumed grant reintroduced under
    another name, in a default argument, or in a comment a later reader could mistake for the
    shipped state would otherwise go unnoticed. The D108 literal joins that list here — an
    interrupted run consumes its grant exactly as a complete one does.
    """
    withdrawn_transition_value = "M3_3_D101_PRE_E0_CATALOG_TRANSITION_AUTHORIZED"
    withdrawn_e0_value = "M3_3_D101_E0_EXECUTION_AUTHORIZED"
    withdrawn_e0_v2_value = "M3_3_D108_E0_V2_EXECUTION_AUTHORIZED"
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None
    source = Path(e0.__file__).read_text(encoding="utf-8")
    assert "PRE_E0_CATALOG_TRANSITION_AUTHORITY: Final[str | None] = None\n" in source
    assert "M3_3_E0_EXECUTION_AUTHORITY: Final[str | None] = None\n" in source
    assert withdrawn_transition_value not in source
    assert withdrawn_e0_value not in source
    assert withdrawn_e0_v2_value not in source


@pytest.mark.parametrize(
    ("runner", "constant"),
    [
        (e0.run_prepare_e0_catalog_command, "PRE_E0_CATALOG_TRANSITION_AUTHORITY"),
        (e0.run_offline_parse_command, "M3_3_E0_EXECUTION_AUTHORITY"),
    ],
)
def test_execute_returns_exit_three_whatever_the_environment_holds(
    runner: object,
    constant: str,
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    catalog: Path,
    config: _Config,
    tmp_path: Path,
) -> None:
    """§7.2: no environment value, catalog state, receipt, namespace, or flag substitutes.

    The same refusal is required with the runtime root present and absent, with the catalog
    at its lawful head and at another, and with a namespace already on disk — because each of
    those is a thing an operator might reasonably expect to change the answer, and none may.

    The stage's own constant is disabled here rather than assumed: the claim under test is
    that the constant is the *sole* gate, which has to hold whatever value the shipped source
    currently carries.
    """
    monkeypatch.setattr(e0, constant, None)
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
    monkeypatch: pytest.MonkeyPatch,
    evidence_root: Path,
    bound: M32World,
    config: _Config,
    tmp_path: Path,
) -> None:
    """§7.2: a preflight result is a measurement, never an authorization.

    The constant is disabled here for the same reason as its neighbour above: the property is
    that a passing preflight never substitutes for the gate, whatever the gate currently says.
    """
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", None)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["transition_execute_enabled"] is False
    result = e0.run_prepare_e0_catalog_command(
        mode="execute", config=config, repository_root=tmp_path, environ=_environ(evidence_root)
    )
    assert result.exit_code == e0.EXIT_STAGE_NOT_ENABLED


def test_the_activation_check_precedes_root_resolution(
    monkeypatch: pytest.MonkeyPatch, config: _Config, tmp_path: Path
) -> None:
    """Exit ``3`` is unconditional: an unset root cannot mask "this stage is not enabled".

    If the root were resolved first, an operator with no variable set would be told to fix
    their environment for a command that would refuse regardless — and a *set* variable would
    have become a precondition for learning the stage was disabled.

    The constant is disabled explicitly because the claim is about *ordering* — activation is
    consulted before the root — which only has content while the stage is disabled.
    """
    monkeypatch.setattr(e0, "M3_3_E0_EXECUTION_AUTHORITY", None)
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


#: The modules **R81**, §7.3, and accepted Decision 099 R97 forbid this surface from reaching.
#: The recovery and request-plan modules are named explicitly because R97's source-local
#: completion binding is exactly the place a future edit would be tempted to reach for them.
_PROHIBITED_MODULES = frozenset(
    {
        "disclosure_drift.m3.acquisition",
        "disclosure_drift.m3.recovery",
        "disclosure_drift.m3.request_plan",
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
    assert not {
        name
        for name in imported
        if "acquisition" in name or "transport" in name or "recovery" in name
    }
    # R97 reuses exactly two accepted receipt mechanics and nothing else from that module.
    assert {"inspect_receipt", "resolve_predecessor_receipt"} <= set(dir(e0))


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
    evidence_root: Path, bound: M32World, config: _Config, tmp_path: Path
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
    evidence_root: Path, config: _Config, head: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§5.2 predicate 4 and §12.3 item 1: exactly ``0001``-``0013``, contiguous."""
    catalog = build_catalog(evidence_root, head=head)
    install_m3_2_binding(evidence_root, catalog, monkeypatch)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("0001-0013" in refusal for refusal in report.refusals), report.refusals


def test_the_transition_preflight_passes_at_head_0013(
    evidence_root: Path, bound: M32World, config: _Config
) -> None:
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["applied_migration_head"] == "0013"
    assert report.facts["planned_source_count"] == e0.PLANNED_SOURCE_COUNT
    assert report.facts["planned_sources_not_started"] == e0.PLANNED_SOURCE_COUNT
    # §5.2 predicate 3 and predicate 10's ownership half are measured, not assumed absent.
    assert report.facts["m3_2_completion_binding"] == "validated"
    assert report.facts["m3_2_cumulative_physical_attempts"] == _M3_2_CUMULATIVE
    assert report.facts["runs_parent"] == "owned by the operator"


# ==========================================================================
# Family 2: every preflight predicate, measured rather than asserted
# ==========================================================================


def test_the_empty_state_guards_refuse_a_consumed_migration_window(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
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


def test_a_started_plan_source_refuses(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
) -> None:
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


def test_an_enabled_network_switch_refuses(evidence_root: Path, bound: M32World) -> None:
    """§5.2 predicate 13: read from the loaded configuration, not from the tracked file."""
    report = e0.transition_preflight(
        evidence_root=evidence_root, config=_Config(network=_Network(enabled=True))
    )
    assert not report.passed
    assert any("network switch is enabled" in item for item in report.refusals)
    assert report.facts["network_switches_disabled"] is False


def test_a_held_writer_lease_refuses_and_elapsed_time_never_permits_takeover(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
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
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
) -> None:
    """§5.2 predicate 9, finding m1: an absent lease passes without being created."""
    lease = catalog.parent / "catalog_writer.lease"
    assert not lease.exists()
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert not lease.exists()
    assert report.facts["writer_lease"] == "absent"


def test_an_existing_run_namespace_refuses(
    evidence_root: Path, bound: M32World, config: _Config
) -> None:
    """§5.2 predicate 10 and §8: a namespace is create-once and is never reused."""
    (e0.runs_directory(evidence_root) / e0.TRANSITION_RUN_NAMESPACE).mkdir(parents=True)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("create-once" in item for item in report.refusals)


def test_the_disk_predicate_requires_three_copies_plus_a_gibibyte(
    evidence_root: Path, bound: M32World, config: _Config, monkeypatch: pytest.MonkeyPatch
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
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
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

    # The M3.2 completion chain the predicate-3 binding reads already lives under runs/, so
    # the property proved here is that preflight created no *governed* artifact of its own.
    assert not e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE).exists()
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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§8.2 and §12.3 item 12: the refusal happens in preflight, so nothing is created."""
    monkeypatch.setattr(e0, "MAXIMUM_RELEASE_HASH_BYTES", 1)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("release-hash estimate" in item for item in report.refusals)
    assert not e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE).exists()
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
    """§7.1 and adopted optimization O2: not CLI options, and lawfully shaped.

    **Accepted-test conflict, resolved by Decision 103 §13.** This assertion previously pinned
    ``m3_3_e0_offline_parse_v1`` as the current E0 namespace. Decision 103 R1 supersedes that:
    the interrupted v1 run makes v1 unreachable for a successor, and the fixed-namespace design
    is preserved by advancing the *constant* in reviewed source rather than by adding an
    operator option. The assertion is updated, not deleted or skipped, and v1's separate
    identity as the immutable predecessor is asserted immediately below.
    """
    assert e0.TRANSITION_RUN_NAMESPACE == "m3_3_pre_e0_catalog_transition_0013_0015_v1"
    assert e0.E0_RUN_NAMESPACE == "m3_3_e0_offline_parse_v2"
    for namespace in (
        e0.TRANSITION_RUN_NAMESPACE,
        e0.E0_RUN_NAMESPACE,
        e0.E0_PREDECESSOR_RUN_NAMESPACE,
        e0.LEASE_RECOVERY_RUN_NAMESPACE,
    ):
        assert e0.validate_namespace(namespace) == namespace


def test_the_predecessor_namespace_is_v1_and_is_distinct_from_the_current_generation() -> None:
    """D103 R1/R2 (N3, N4): v1 is named, kept separate, and is not a prefix collision.

    ``E0_RUN_NAMESPACE`` and ``E0_PREDECESSOR_RUN_NAMESPACE`` are distinct directory names, so
    a v1 that already exists does not make v2's create-once check fire, and nothing about v2
    reaches into v1's directory by prefix.
    """
    assert e0.E0_PREDECESSOR_RUN_NAMESPACE == "m3_3_e0_offline_parse_v1"
    assert e0.E0_RUN_NAMESPACE != e0.E0_PREDECESSOR_RUN_NAMESPACE
    assert not e0.E0_RUN_NAMESPACE.startswith(e0.E0_PREDECESSOR_RUN_NAMESPACE)
    assert not e0.E0_PREDECESSOR_RUN_NAMESPACE.startswith(e0.E0_RUN_NAMESPACE)


def _every_cli_option_string() -> set[str]:
    """Every option string the shipped parser exposes, at any nesting depth."""
    from disclosure_drift import cli

    found: set[str] = set()

    def walk(parser: argparse.ArgumentParser) -> None:
        for action in parser._actions:  # noqa: SLF001 - argparse exposes no public walk
            found.update(action.option_strings)
            choices = getattr(action, "choices", None)
            if not isinstance(choices, Mapping):
                continue
            for candidate in choices.values():
                if isinstance(candidate, argparse.ArgumentParser):
                    walk(candidate)

    walk(cli.build_parser())
    return found


def test_no_runtime_option_or_environment_value_can_choose_a_run_namespace() -> None:
    """D103 R1 (N2): the generation advances by reviewed source and by nothing else.

    Walked over the *built* parser rather than grepped from source, because the source
    deliberately names ``--run-namespace`` in prose to say it does not exist — a text scan
    would fail on the very comments that document the rule. The recognized environment
    variables are checked the same way: no allowlisted name can carry a namespace either.
    """
    options = _every_cli_option_string()
    for prohibited in ("--run-namespace", "--namespace", "--generation", "--lease-file"):
        assert prohibited not in options
    assert not any("namespace" in option for option in options)
    for variable in RECOGNIZED_ENV_VARS:
        assert "NAMESPACE" not in variable.upper()


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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
) -> None:
    """§7.2 verify: strictly read-only, and it repairs nothing.

    Accepted Decision 099 R98 makes verify open the fixed catalog, so the same permitted
    ``-wal``/``-shm`` companions the preflight proof names appear here for the same reason and
    are named the same way rather than tolerated silently: every file that existed is
    byte-identical, the log is empty, and the run namespace gains nothing at all.
    """
    outcome = _run_transition(evidence_root, config)

    def listing() -> dict[str, bytes]:
        return {
            str(path.relative_to(evidence_root)): path.read_bytes()
            for path in evidence_root.rglob("*")
            if path.is_file()
        }

    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    before = listing()
    namespace_before = sorted(path.name for path in directory.iterdir())
    report = e0.transition_verify(evidence_root=evidence_root)
    after = listing()

    assert report.determined
    assert report.passed, report.refusals
    assert report.facts["result_token"] == outcome.result_token
    assert report.facts["catalog_migration_head"] == "0015"
    assert report.facts["catalog_state_compared"] == "consistent"
    assert report.facts["catalog_state_comparisons"] == 3
    assert {name: after[name] for name in before} == before
    catalog_key = str(catalog.relative_to(evidence_root))
    assert set(after) - set(before) <= {f"{catalog_key}-wal", f"{catalog_key}-shm"}
    wal = catalog.parent / f"{catalog.name}-wal"
    assert not wal.exists() or wal.stat().st_size == 0
    # §8's authorized run write set is exactly four files, and verify adds none of its own —
    # in particular, reading the backup leaves no journal sidecar beside it.
    assert sorted(path.name for path in directory.iterdir()) == namespace_before


def test_a_post_freeze_defect_is_preserved_and_never_repaired(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
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
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
) -> None:
    """§5.4: a namespace is never reused, and ``execute`` never resumes."""
    _run_transition(evidence_root, config)
    with pytest.raises(e0.E0Error):
        _run_transition(evidence_root, config)


def test_the_transition_refuses_at_a_head_that_is_not_0013_under_the_lease(
    evidence_root: Path,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§5.3 item 2 and §5.4: the under-lease recheck refuses before anything is created."""
    install_m3_2_binding(evidence_root, build_catalog(evidence_root, head=15), monkeypatch)
    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged"):
        _run_transition(evidence_root, config)
    assert not e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE).exists()


def test_a_hard_kill_leaves_no_terminal_and_verify_reports_undetermined(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
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
    bound: M32World,
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


def install_interrupted_predecessor(evidence_root: Path, *, events: int = 2) -> Path:
    """Build a disposable v1 namespace in exactly the accepted interrupted shape.

    Accepted Decision 103 R8 makes the successor's predecessor gate load-bearing, so every E0
    test needs a predecessor to run against. The shape reproduced here is the accepted one: a
    chain-valid ledger that reached ``PREFLIGHT_PASSED`` and ``BACKUP_VERIFIED``, no terminal
    record, no execution receipt, and therefore ``UNDETERMINED / NOT COMPLETE``.

    The ledger is written by the **real** :class:`~disclosure_drift.m3.e0.EventLedger`, so the
    chain the gate verifies is a chain production actually produces. Every value is invented
    for a temporary directory; nothing here reads, names, copies, or approximates the accepted
    private root or the real v1 run.
    """
    directory = e0.create_run_namespace(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    ledger = e0.EventLedger(
        directory / e0.E0_EVENTS_FILENAME, e0.E0_PREDECESSOR_RUN_NAMESPACE, kind="E0"
    )
    if events >= 1:
        ledger.append(
            "PREFLIGHT_PASSED",
            {
                "migration_head": "0015",
                "planned_source_count": e0.PLANNED_SOURCE_COUNT,
                "input_observation_set_sha256": "d" * 64,
                "pre_e0_catalog_logical_sha256": "e" * 64,
            },
            observed_at_utc=_AT,
        )
    if events >= 2:  # noqa: PLR2004 - the accepted predecessor stopped at the second boundary
        ledger.append(
            "BACKUP_VERIFIED",
            {
                "relative_path": (
                    f"runs/{e0.E0_PREDECESSOR_RUN_NAMESPACE}/{e0.E0_BACKUP_FILENAME}"
                ),
                "byte_length": 4096,
                "file_sha256": "f" * 64,
                "catalog_logical_sha256": "e" * 64,
            },
            observed_at_utc=_AT,
        )
    return directory


@pytest.fixture
def predecessor(evidence_root: Path) -> Path:
    """The interrupted v1 predecessor every successor-generation E0 run requires."""
    return install_interrupted_predecessor(evidence_root)


@pytest.fixture
def transitioned(
    evidence_root: Path,
    config: _Config,
    predecessor: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    """A disposable catalog carried to head ``0015`` by the real transition machine.

    The E0 machine requires a COMPLETE transition terminal, so the two are chained here
    exactly as the accepted sequence chains them, rather than the terminal being fabricated.
    It also requires the interrupted predecessor (Decision 103 R8), which ``predecessor``
    installs beside it.
    """
    catalog = build_catalog(evidence_root, head=13, sources=True)
    install_m3_2_binding(evidence_root, catalog, monkeypatch)
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    outcome = e0.transition_execute(evidence_root=evidence_root, config=config)
    assert outcome.status == "complete"
    monkeypatch.setattr(e0, "PRE_E0_CATALOG_TRANSITION_AUTHORITY", None)
    return catalog


def test_e0_preflight_requires_a_complete_transition_terminal(
    evidence_root: Path, predecessor: Path, config: _Config
) -> None:
    """§9.1: an absent transition terminal is UNDETERMINED, never permission.

    The refusal is the assertion. ``e0_execute_enabled`` is reported alongside it and is back to
    ``False`` under accepted Decision 108 §5 (R122), which is what
    makes the point sharper rather than weaker: the refusal is the absent transition terminal,
    and it has now stood unchanged across three different activation states — disabled, briefly
    activated by D108 §2, and disabled again on the interrupted invocation's return. **An
    activated E0 is refused by exactly the same predicate as a disabled one.** The fact is
    rendered so an operator reading a refusal can tell the two apart.
    """
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


# ==========================================================================
# Decision 099 R96: a failure terminal derived from the durable event ledger
#
# Decision 098 MAJOR-1: the execute paths necessarily assign an event-conditioned value
# **before** appending the event that permits it, because the event's own `details` carry that
# value. A failure inside that window used to leave a create-once terminal record its own
# §8.1/§9.2 validator refuses, and `_freeze`'s validation error was suppressed. Each test below
# injects at exactly one conditioning-event append boundary and reopens the persisted record
# through the production loader — which validates, so a malformed record fails the test rather
# than being asserted about field by field.
# ==========================================================================


def _fail_the_append(monkeypatch: pytest.MonkeyPatch, event_type: str) -> None:
    """Make one exact ledger append fail, leaving its conditioning event non-durable."""
    original = e0.EventLedger.append

    def guarded(
        self: e0.EventLedger,
        kind: str,
        details: Mapping[str, object],
        *,
        observed_at_utc: str,
    ) -> Mapping[str, object]:
        if kind == event_type:
            message = f"injected disposable-fixture {kind} append failure"
            raise e0.E0Error(message)
        return original(self, kind, details, observed_at_utc=observed_at_utc)

    monkeypatch.setattr(e0.EventLedger, "append", guarded)


def _run_names(kind: str) -> tuple[str, str, str]:
    """``(namespace, terminal filename, events filename)`` for one state machine."""
    if kind == "TRANSITION":
        return (
            e0.TRANSITION_RUN_NAMESPACE,
            e0.TRANSITION_TERMINAL_FILENAME,
            e0.TRANSITION_EVENTS_FILENAME,
        )
    return e0.E0_RUN_NAMESPACE, e0.E0_TERMINAL_FILENAME, e0.E0_EVENTS_FILENAME


def _reopen_terminal(evidence_root: Path, kind: str) -> tuple[Mapping[str, object], frozenset[str]]:
    """Reopen a persisted terminal through the production loader; return it and its events."""
    namespace, terminal_filename, events_filename = _run_names(kind)
    directory = e0.namespace_directory(evidence_root, namespace)
    document, events = e0._load_terminal(
        directory / terminal_filename, directory / events_filename, kind=kind
    )
    return document, frozenset(str(event["event_type"]) for event in events)


@pytest.mark.parametrize(
    ("event_type", "absent", "present"),
    [
        ("BACKUP_VERIFIED", ("backup",), ()),
        (
            "POSTCHECK_PASSED",
            ("post_preexisting_content_sha256",),
            ("backup", "applied_migrations", "post_migration_chain", "post_integrity"),
        ),
    ],
)
def test_a_transition_failure_in_a_conditioning_window_is_durably_representable(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
    event_type: str,
    absent: tuple[str, ...],
    present: tuple[str, ...],
) -> None:
    """§8.1 and §12.3 item 8, at each transition conditioning boundary (Decision 099 R96)."""
    _fail_the_append(monkeypatch, event_type)
    with pytest.raises(e0.E0Error, match="injected"):
        _run_transition(evidence_root, config)

    document, events = _reopen_terminal(evidence_root, "TRANSITION")
    assert event_type not in events
    assert document["status"] == "failed"
    for field in absent:
        assert field not in document, field
    for field in present:
        assert field in document, field

    report = e0.transition_verify(evidence_root=evidence_root)
    assert report.determined
    assert report.refusals == (), report.refusals
    assert not report.passed


@pytest.mark.parametrize(
    ("event_type", "absent", "present"),
    [
        ("BACKUP_VERIFIED", ("backup", "post_migration_chain"), ()),
        (
            "ASSOCIATIONS_MATERIALIZED",
            ("association_totality", "table_hashes", "e0_catalog_state_sha256", "post_integrity"),
            ("backup", "post_migration_chain"),
        ),
        (
            "VALIDATION_PASSED",
            ("table_hashes", "plan_parser_state_hash", "e0_catalog_state_sha256", "post_integrity"),
            ("backup", "association_totality", "post_migration_chain"),
        ),
    ],
)
def test_an_e0_failure_in_a_conditioning_window_is_durably_representable(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
    event_type: str,
    absent: tuple[str, ...],
    present: tuple[str, ...],
) -> None:
    """§9.2 and §12.3 item 8, at each E0 conditioning boundary (Decision 099 R96)."""
    _fail_the_append(monkeypatch, event_type)
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, events = _reopen_terminal(evidence_root, "E0")
    assert event_type not in events
    assert document["status"] == "failed"
    for field in absent:
        assert field not in document, field
    for field in present:
        assert field in document, field

    report = e0.e0_verify(evidence_root=evidence_root)
    assert report.determined
    assert report.refusals == (), report.refusals
    assert not report.passed


@pytest.mark.parametrize("mutant", ["delete_the_projection", "keep_the_pre_event_field"])
def test_removing_the_durable_event_projection_makes_the_window_proof_fail(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
    mutant: str,
) -> None:
    """The R96 non-vacuity proof: the guard is load-bearing, not decorative.

    Two independently sufficient mutants are run, because the projection could be defeated
    either by removing it wholesale or by quietly dropping one row of its table.
    """
    if mutant == "delete_the_projection":
        monkeypatch.setattr(e0, "_project_failure_terminal", lambda *_a, **_k: None)
    else:
        monkeypatch.setattr(
            e0,
            "_TRANSITION_EVENT_CONDITIONED_FIELDS",
            {"BACKUP_VERIFIED": ("backup",)},
        )
    _fail_the_append(monkeypatch, "POSTCHECK_PASSED")
    with pytest.raises(e0.E0Error, match="injected"):
        _run_transition(evidence_root, config)

    # The malformed record is still written create-once, which is the exact Decision 098
    # MAJOR-1 defect: its own validator refuses the bytes the run left behind.
    with pytest.raises(e0.TerminalValidationError, match="post_preexisting_content_sha256"):
        _reopen_terminal(evidence_root, "TRANSITION")
    assert e0.transition_verify(evidence_root=evidence_root).determined


def test_an_unverifiable_ledger_yields_no_terminal_at_all(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R96's stop condition: a terminal is never manufactured over an unverifiable ledger."""
    original = e0.EventLedger.append

    def guarded(
        self: e0.EventLedger,
        kind: str,
        details: Mapping[str, object],
        *,
        observed_at_utc: str,
    ) -> Mapping[str, object]:
        if kind == "BACKUP_VERIFIED":
            self.path.chmod(0o600)
            with self.path.open("ab") as handle:
                handle.write(b"not a canonical event\n")
            message = "injected disposable-fixture BACKUP_VERIFIED append failure"
            raise e0.E0Error(message)
        return original(self, kind, details, observed_at_utc=observed_at_utc)

    monkeypatch.setattr(e0.EventLedger, "append", guarded)
    with pytest.raises(e0.E0Error, match="injected"):
        _run_transition(evidence_root, config)

    directory = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE)
    assert not (directory / e0.TRANSITION_TERMINAL_FILENAME).exists()
    assert not (directory / OPERATOR_RECEIPT_FILENAME).exists()
    report = e0.transition_verify(evidence_root=evidence_root)
    assert not report.determined
    assert not report.passed
    assert "UNDETERMINED / NOT COMPLETE" in "\n".join(report.lines)


# ==========================================================================
# Decision 099 R97: §5.2 predicate 3 — the accepted M3.2 completion binding
#
# Decision 098 MAJOR-2: twelve of thirteen §5.2 predicates were implemented, while
# `transition_preflight` claimed all thirteen. The binding is a *provenance* check, so every
# negative below bends exactly one fact and requires a refusal — a predicate that only ever
# passes proves nothing about what it would refuse.
# ==========================================================================


def test_the_shipped_m3_2_completion_pins_are_the_accepted_ones() -> None:
    """The shipped literals, asserted against the **file** as well as the runtime object.

    The runtime assertion alone would pass against a module some other test had rebound, and
    Decision 099 §3 permits exactly that in-memory substitution — so the source-text assertion
    is the load-bearing one, exactly as it is for the two activation constants.
    """
    binding = e0.M3_2_COMPLETION_BINDING
    assert binding.head.relative_path == (
        "runs/m3_2_decision_062_sic_continuation/execution_receipt.json"
    )
    assert binding.predecessor.relative_path == "runs/m3_2a_clean_carry_in/execution_receipt.json"
    assert binding.acquisition_window == "M3.2A"
    assert binding.cumulative_physical_attempt_count == 77
    assert binding.head_logical_request_count == 1
    assert binding.head_physical_attempt_count == 1

    source = Path(e0.__file__).read_text(encoding="utf-8")
    for accepted in (
        "ae8ace5dc62155c9dca395af238290b0bb5b99dc4e3f1741e3d8ff1c9ab9c3dd",
        "7d72a5501f66d36af9024b80a64060668da315b8880fb5add028917d36ad12e1",
        "m3-2-acquisition-b6f8bc7f48b94e6080038db575b204e5",
        "f77e003ccc0ed8f9c0e55065b3c211aa5e33c7abf86cc71cbe66d427611d890a",
        "0278c857d7816a79907068513fe09d5b78fc3973ba415149fbc9d73605b5359c",
        "37dd811497d4a57e8b911917ed6c0426a22f443c3ddd5aeba8d4da3e076f6a7c",
        "m3-2-acquisition-6db97de60ac64b30bc36371d7b209b44",
        "19be7bdc9071d0dcdcaaa1972e6b4844fa8076c9b1761735f903fa500623af68",
        "6e9d92c859bc48faa6c1c5e47c36fd8e",
    ):
        assert accepted in source, accepted


def test_the_completion_binding_validates_the_accepted_shaped_chain(
    evidence_root: Path, bound: M32World, config: _Config
) -> None:
    """The positive control: predicate 3 passes, and says what it measured."""
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert report.facts["m3_2_completion_binding"] == "validated"
    assert report.facts["m3_2_completion_receipt_head"].startswith(bound.head.receipt_id[:12])
    assert report.facts["m3_2_completion_receipt_root"].startswith(bound.root.receipt_id[:12])
    assert report.facts["m3_2_cumulative_physical_attempts"] == _M3_2_CUMULATIVE
    # The head's own carried-forward baseline is deliberately not a second term of the sum.
    assert bound.head.consumed_request_count_carried_forward != 0
    assert (
        _M3_2_HEAD_ATTEMPTS
        + _M3_2_ROOT_ATTEMPTS
        + _M3_2_ROOT_CARRIED_FORWARD
        + bound.head.consumed_request_count_carried_forward
    ) != _M3_2_CUMULATIVE


def _execute(catalog: Path, statement: str, parameters: tuple[object, ...] = ()) -> None:
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(statement, parameters)


def _rebind(monkeypatch: pytest.MonkeyPatch, world: M32World, **changes: object) -> None:
    monkeypatch.setattr(e0, "M3_2_COMPLETION_BINDING", replace(world.binding, **changes))


def _repin(monkeypatch: pytest.MonkeyPatch, world: M32World, which: str, **changes: object) -> None:
    pin = replace(getattr(world.binding, which), **changes)
    monkeypatch.setattr(e0, "M3_2_COMPLETION_BINDING", replace(world.binding, **{which: pin}))


def _case_absent_receipt(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp).head_path.unlink()


def _case_wrong_file_digest(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _repin(mp, install_m3_2_binding(root, catalog, mp), "head", file_sha256="f" * 64)


def _case_wrong_receipt_id(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _repin(mp, install_m3_2_binding(root, catalog, mp), "head", receipt_id="0" * 64)


def _case_tampered_receipt_bytes(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    """Bytes the pin's digest still matches, so the schema/canonical-form loader is what refuses."""
    world = install_m3_2_binding(root, catalog, mp)
    tampered = world.head_path.read_bytes().replace(b'"phase":"M3.2A"', b'"phase":"M3.9Z"', 1)
    world.head_path.write_bytes(tampered)
    _repin(mp, world, "head", file_sha256=hashlib.sha256(tampered).hexdigest())


def _case_wrong_predecessor_id(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(
        root, catalog, mp, head_overrides={"recovery_predecessor_receipt_id": "1" * 64}
    )


def _case_chain_extension(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    """A root that names a predecessor is not a root — which is also why a cycle is unreachable."""
    install_m3_2_binding(
        root,
        catalog,
        mp,
        root_overrides={
            "recovery_predecessor_receipt_id": "2" * 64,
            "carry_in_authority_sha256": None,
        },
    )


def _case_symlinked_candidate(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    world = install_m3_2_binding(root, catalog, mp)
    other = root / "runs" / "m3_2_symlinked_namespace"
    other.mkdir(parents=True)
    (other / OPERATOR_RECEIPT_FILENAME).symlink_to(world.root_path)


def _case_substituted_resolution(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    """A byte-identical alias in ``receipts/`` resolves before the fixed name and is refused."""
    world = install_m3_2_binding(root, catalog, mp)
    receipts = root / "receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    alias = receipts / content_derived_receipt_name(world.root.receipt_id)
    alias.write_bytes(world.root_path.read_bytes())


def _case_wrong_run_state(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "UPDATE ops_ingestion_jobs SET job_state = 'stopped' WHERE job_id = ?",
        (_M3_2_HEAD_RUN_ID,),
    )


def _case_wrong_job_kind(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "UPDATE ops_ingestion_jobs SET job_kind = 'sec_census' WHERE job_id = ?",
        (_M3_2_ROOT_RUN_ID,),
    )


def _case_wrong_window(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "UPDATE ops_ingestion_jobs SET stage = 'M3.2B' WHERE job_id = ?",
        (_M3_2_HEAD_RUN_ID,),
    )


def _case_wrong_timestamps(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "UPDATE ops_ingestion_jobs SET finished_at_utc = '2026-08-12T00:00:00Z' WHERE job_id = ?",
        (_M3_2_HEAD_RUN_ID,),
    )


def _case_absent_run_row(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(catalog, "DELETE FROM ops_retrieval_attempts WHERE job_id = ?", (_M3_2_ROOT_RUN_ID,))
    _execute(catalog, "DELETE FROM ops_ingestion_jobs WHERE job_id = ?", (_M3_2_ROOT_RUN_ID,))


def _case_attempt_count_disagreement(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "INSERT INTO ops_retrieval_attempts (retrieval_attempt_id, job_id, source_url_canonical, "
        "logical_role, attempt_number, attempt_state, started_at_utc) VALUES "
        "('attempt-extra', ?, 'https://example.invalid/extra', 'metadata', 2, 'succeeded', ?)",
        (_M3_2_HEAD_RUN_ID, _AT),
    )


def _case_wrong_observation_attribution(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    world = install_m3_2_binding(root, catalog, mp)
    _execute(
        catalog,
        "INSERT OR REPLACE INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
        "started_at_utc, detail) VALUES ('other-acquisition-run', ?, 'completed', 'M3.2A', ?, '')",
        (e0.M3_2_ACQUISITION_JOB_KIND, _AT),
    )
    _execute(
        catalog,
        "UPDATE census_plan_sources SET census_run_id = 'other-acquisition-run' "
        "WHERE observation_id = ?",
        (world.binding.head_observation_id,),
    )


def _case_absent_observation(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _rebind(mp, install_m3_2_binding(root, catalog, mp), head_observation_id="no-such-observation")


def _case_wrong_cumulative_total(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _rebind(
        mp,
        install_m3_2_binding(root, catalog, mp),
        cumulative_physical_attempt_count=_M3_2_CUMULATIVE + 1,
    )


def _case_wrong_head_request_count(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _rebind(mp, install_m3_2_binding(root, catalog, mp), head_logical_request_count=99)


def _case_wrong_pinned_window(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _rebind(mp, install_m3_2_binding(root, catalog, mp), acquisition_window="M3.2B")


def _case_wrong_plan_digest(root: Path, catalog: Path, mp: pytest.MonkeyPatch) -> None:
    _repin(mp, install_m3_2_binding(root, catalog, mp), "head", request_plan_sha256="9" * 64)


_BINDING_NEGATIVES = (
    (_case_absent_receipt, "is not a regular file"),
    (_case_wrong_file_digest, "hashes to"),
    (_case_wrong_receipt_id, "derives identity"),
    (_case_tampered_receipt_bytes, "did not validate"),
    (_case_wrong_predecessor_id, "names predecessor"),
    (_case_chain_extension, "names a predecessor"),
    (_case_symlinked_candidate, "did not resolve"),
    (_case_substituted_resolution, "resolves to a receipt other than"),
    (_case_wrong_run_state, "job state does not equal the receipt"),
    (_case_wrong_job_kind, "job kind does not equal the receipt"),
    (_case_wrong_window, "stage does not equal the receipt"),
    (_case_wrong_timestamps, "finish instant does not equal the receipt"),
    (_case_absent_run_row, "carries 0 run row(s)"),
    (_case_attempt_count_disagreement, "durable attempt row(s)"),
    (_case_wrong_observation_attribution, "durable run attribution is not exactly"),
    (_case_absent_observation, "row(s) for the accepted M3.2 head observation"),
    (_case_wrong_cumulative_total, "cumulative physical attempt(s)"),
    (_case_wrong_head_request_count, "logical request(s)"),
    (_case_wrong_pinned_window, "records window"),
    (_case_wrong_plan_digest, "executed plan"),
)


@pytest.mark.parametrize(
    ("mutate", "expected"),
    _BINDING_NEGATIVES,
    ids=[case.__name__.removeprefix("_case_") for case, _ in _BINDING_NEGATIVES],
)
def test_a_broken_completion_binding_refuses_the_transition_preflight(
    evidence_root: Path,
    catalog: Path,
    config: _Config,
    monkeypatch: pytest.MonkeyPatch,
    mutate: object,
    expected: str,
) -> None:
    """§5.2 predicate 3's negative matrix: one bent fact each, every one fail-closed."""
    mutate(evidence_root, catalog, monkeypatch)  # type: ignore[operator]
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any(expected in refusal for refusal in report.refusals), report.refusals
    assert report.facts["m3_2_completion_binding"] == "REFUSED"


def test_neutering_the_completion_binding_lets_every_negative_pass(
    evidence_root: Path, catalog: Path, config: _Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The R97 non-vacuity control: without the guard, a broken chain reads as a PASS."""
    _case_wrong_run_state(evidence_root, catalog, monkeypatch)
    assert not e0.transition_preflight(evidence_root=evidence_root, config=config).passed
    monkeypatch.setattr(e0, "_acquisition_completion_binding", lambda **_k: ([], {}))
    assert e0.transition_preflight(evidence_root=evidence_root, config=config).passed


def test_the_completion_binding_is_rerun_under_the_held_lease(
    evidence_root: Path,
    catalog: Path,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§5.3 item 2: predicate 3 is repeated under the writer lease, before anything is created."""
    _case_wrong_run_state(evidence_root, catalog, monkeypatch)
    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged") as caught:
        _run_transition(evidence_root, config)
    assert "job state does not equal the receipt" in str(caught.value)
    assert not e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE).exists()


def test_e0_does_not_inherit_the_transition_only_completion_predicate(
    evidence_root: Path, transitioned: Path, config: _Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """§9.1 lists E0's own predicates; the M3.2 completion binding is not among them.

    Proved by breaking the binding and requiring E0's preflight to still pass: a predicate E0
    silently inherited would refuse here, and a later E0 would refuse for a reason its own
    ruling never states.
    """
    _execute(
        catalog=_catalog_path(evidence_root),
        statement="UPDATE ops_ingestion_jobs SET job_state = 'stopped' WHERE job_id = ?",
        parameters=(_M3_2_HEAD_RUN_ID,),
    )
    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert report.passed, report.refusals
    assert "m3_2_completion_binding" not in report.facts


def test_the_completion_binding_reads_nothing_and_renders_no_private_path(
    evidence_root: Path, catalog: Path, config: _Config, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R97: strictly read-only, and its refusals name only fixed public relative names."""
    world = install_m3_2_binding(evidence_root, catalog, monkeypatch)

    def listing() -> dict[str, bytes]:
        return {
            str(path.relative_to(evidence_root)): path.read_bytes()
            for path in evidence_root.rglob("*")
            if path.is_file()
        }

    before = listing()
    passing = e0.transition_preflight(evidence_root=evidence_root, config=config)
    world.head_path.unlink()
    refusing = e0.transition_preflight(evidence_root=evidence_root, config=config)
    after = listing()

    assert passing.passed, passing.refusals
    assert not refusing.passed
    assert {name: after[name] for name in before if name in after} == {
        name: before[name] for name in before if name in after
    }
    rendered = "\n".join((*passing.lines, *refusing.lines))
    assert _SYNTHETIC_ROOT_MARKER not in rendered
    assert str(evidence_root) not in rendered
    for line in (*passing.lines, *refusing.lines):
        assert not line.strip().startswith("/")


# ==========================================================================
# Decision 099 R98: the four Decision 098 MINOR dispositions
# ==========================================================================


def test_the_transition_verify_detects_a_post_freeze_catalog_state_mutation(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
) -> None:
    """MINOR-2: §7.2's verify row lists catalog state, and now verify actually reads it."""
    _run_transition(evidence_root, config)
    assert e0.transition_verify(evidence_root=evidence_root).passed

    _execute(catalog, "DELETE FROM ops_schema_migrations WHERE version = 15")
    report = e0.transition_verify(evidence_root=evidence_root)
    assert report.determined
    assert not report.passed
    assert any("applied migration chain" in item for item in report.refusals), report.refusals
    assert report.facts["catalog_state_compared"] == "REFUSED"


def test_the_transition_verify_detects_a_mutated_backup_content_identity(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
) -> None:
    """MINOR-2: the transition's persisted content identity is reproduced, never trusted."""
    _run_transition(evidence_root, config)
    backup = e0.namespace_directory(evidence_root, e0.TRANSITION_RUN_NAMESPACE) / (
        e0.TRANSITION_BACKUP_FILENAME
    )
    backup.chmod(0o600)
    backup.write_bytes(backup.read_bytes() + b"\x00")

    report = e0.transition_verify(evidence_root=evidence_root)
    assert report.determined
    assert not report.passed
    assert any("verified backup" in item for item in report.refusals), report.refusals


@pytest.mark.parametrize(
    ("statement", "expected"),
    [
        (
            "UPDATE census_plan_sources SET parser_state = 'missing' WHERE source_instance_id = "
            "(SELECT MIN(source_instance_id) FROM census_plan_sources)",
            "plan parser-state identity",
        ),
        (
            "UPDATE census_parser_runs SET summary_json = '{\"mutated\":true}'",
            "table hash records",
        ),
    ],
)
def test_the_e0_verify_detects_a_post_freeze_governed_state_mutation(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    statement: str,
    expected: str,
) -> None:
    """MINOR-2: §9.4's governed-state identities are independently reproduced from the catalog."""
    e0.e0_execute(evidence_root=evidence_root, config=config)
    assert e0.e0_verify(evidence_root=evidence_root).passed

    _execute(transitioned, statement)
    report = e0.e0_verify(evidence_root=evidence_root)
    assert report.determined
    assert not report.passed
    assert any(expected in item for item in report.refusals), report.refusals
    assert any("governed catalog-state identity" in item for item in report.refusals)


def test_the_under_lease_recheck_omits_predicate_nine_structurally(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
) -> None:
    """MINOR-3: a typed control-flow choice, never a match on English refusal text."""
    import inspect

    assert "lease_check" in inspect.signature(e0._shared_preflight).parameters

    with CatalogWriter(catalog, catalog.parent):
        checked, _, _ = e0._shared_preflight(
            evidence_root=evidence_root,
            config=config,
            namespace=e0.TRANSITION_RUN_NAMESPACE,
            expected_head=e0.TRANSITION_SOURCE_HEAD,
            lease_check=True,
        )
        omitted, facts, _ = e0._shared_preflight(
            evidence_root=evidence_root,
            config=config,
            namespace=e0.TRANSITION_RUN_NAMESPACE,
            expected_head=e0.TRANSITION_SOURCE_HEAD,
            lease_check=False,
        )

    assert any("holds the catalog lease" in item for item in checked)
    # Predicate 9 alone is dropped: nothing else diverges under the very same conditions.
    assert omitted == []
    assert facts["writer_lease"] == "held by this run"
    source = Path(e0.__file__).read_text(encoding="utf-8")
    assert "writer holds the catalog lease" not in source.split("def _recheck_under_lease", 1)[1]


def test_an_absent_namespace_parent_refuses(
    evidence_root: Path, catalog: Path, config: _Config
) -> None:
    """MINOR-4: §5.2 predicate 10 requires the parent to **already** exist."""
    assert not e0.runs_directory(evidence_root).exists()
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("must already exist" in item for item in report.refusals), report.refusals
    assert report.facts["runs_parent"] == "unsound"
    # Preflight is still strictly read-only: it refuses rather than creating the parent.
    assert not e0.runs_directory(evidence_root).exists()


def test_a_symlinked_namespace_parent_refuses(
    evidence_root: Path, catalog: Path, config: _Config, tmp_path: Path
) -> None:
    """MINOR-4: a symlinked parent places governed artifacts somewhere never approved."""
    elsewhere = tmp_path / "elsewhere-runs"
    elsewhere.mkdir()
    e0.runs_directory(evidence_root).symlink_to(elsewhere, target_is_directory=True)
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("non-symlinked" in item for item in report.refusals), report.refusals


@pytest.mark.parametrize(
    ("uid", "expected"),
    [
        ("other", "not owned by the effective operator"),
        ("unknown", "could not be established"),
    ],
)
def test_a_namespace_parent_the_operator_does_not_own_refuses(
    evidence_root: Path,
    bound: M32World,
    config: _Config,
    monkeypatch: pytest.MonkeyPatch,
    uid: str,
    expected: str,
) -> None:
    """MINOR-4: ownership is checked, and a platform that will not say does not silently pass.

    The effective identity is read through one seam rather than ``os.geteuid`` being called at
    the site, because a real ``chown`` to another user needs privileges this suite must never
    have — and because "the platform will not answer" has to be a reachable state to be proved
    fail-closed at all.
    """
    monkeypatch.setattr(
        e0, "_effective_uid", (lambda: None) if uid == "unknown" else (lambda: os.getuid() + 1)
    )
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any(expected in item for item in report.refusals), report.refusals
    assert report.facts["runs_parent"] == "unsound"


# ==========================================================================
# Decision 099 final review MAJOR-1: the catalog-observed failure window
#
# `catalog_state_observed` conditions a whole §8.1/§9.2 field group. The transition loop used
# to claim the observation **before** the two database reads that produce that group, so a read
# that raised left a create-once terminal declaring the claim while the group was missing --
# which `_load_terminal` refuses. Two independently sufficient guards now close it: every
# execute path exposes the validated complete projection before it sets the flag, and
# `_disclose_failure` claims the observation only when that complete group is actually present.
# ==========================================================================

_CATALOG_OBSERVED_GROUP = ("applied_migrations", "post_migration_chain", "post_integrity")


def _raise_after_first_commit(monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    """Make the first post-commit catalog read raise, at exactly the vulnerable boundary."""
    import disclosure_drift.storage.sqlite as sqlite_module

    original_apply = sqlite_module.apply_migrations
    original_target = getattr(e0, target)
    state = {"committed": False, "fired": False}

    def apply(*args: object, **kwargs: object) -> object:
        result = original_apply(*args, **kwargs)  # type: ignore[arg-type]
        state["committed"] = True
        return result

    def guarded(connection: sqlite3.Connection) -> object:
        if state["committed"] and not state["fired"]:
            state["fired"] = True
            message = f"injected disposable-fixture {target} failure"
            raise sqlite3.OperationalError(message)
        return original_target(connection)

    monkeypatch.setattr(sqlite_module, "apply_migrations", apply)
    monkeypatch.setattr(e0, target, guarded)


def _stall_the_chain_after_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Report a head that did not move, so the in-loop refusal fires after a real observation."""
    import disclosure_drift.storage.sqlite as sqlite_module

    original_apply = sqlite_module.apply_migrations
    original_versions = e0.applied_versions
    state = {"committed": False}

    def apply(*args: object, **kwargs: object) -> object:
        result = original_apply(*args, **kwargs)  # type: ignore[arg-type]
        state["committed"] = True
        return result

    def guarded(connection: sqlite3.Connection) -> tuple[int, ...]:
        if state["committed"]:
            return tuple(range(1, e0.TRANSITION_SOURCE_HEAD + 1))
        return original_versions(connection)

    monkeypatch.setattr(sqlite_module, "apply_migrations", apply)
    monkeypatch.setattr(e0, "applied_versions", guarded)


def _failure_of(document: Mapping[str, object]) -> Mapping[str, object]:
    failure = document["failure"]
    assert isinstance(failure, Mapping)
    return failure


@pytest.mark.parametrize("target", ["applied_versions", "integrity_report"])
def test_a_transition_catalog_read_failure_never_claims_a_catalog_observation(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
    target: str,
) -> None:
    """MAJOR-1 negative controls: each formerly vulnerable read is failed independently.

    The commit has happened and cannot be un-happened, but no **observation** of it exists, so
    the record must not claim one. The production loader is the assertion: a record claiming the
    observation without its group is refused there rather than reported field by field.
    """
    _raise_after_first_commit(monkeypatch, target)
    with pytest.raises(sqlite3.OperationalError, match="injected"):
        _run_transition(evidence_root, config)

    document, _ = _reopen_terminal(evidence_root, "TRANSITION")
    assert document["status"] == "failed"
    failure = _failure_of(document)
    assert failure["catalog_state_observed"] is False
    for field in _CATALOG_OBSERVED_GROUP:
        assert field not in document, field
    # Original failure semantics survive, and nothing invented a chain, an integrity verdict,
    # or an applied-migration record to satisfy a claim that was never earned.
    assert failure["reason_code"] == "PRE_E0_CATALOG_TRANSITION_FAILED"
    assert "OperationalError" in str(failure["reason_detail"])

    report = e0.transition_verify(evidence_root=evidence_root)
    assert report.determined
    assert not report.passed


def test_a_refusal_after_a_complete_catalog_observation_claims_it_truthfully(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MAJOR-1 positive control: a genuine observation is claimed **with** its whole group."""
    _stall_the_chain_after_commit(monkeypatch)
    with pytest.raises(e0.PreflightRefusalError, match="did not move the chain head"):
        _run_transition(evidence_root, config)

    document, _ = _reopen_terminal(evidence_root, "TRANSITION")
    assert document["status"] == "failed"
    assert _failure_of(document)["catalog_state_observed"] is True
    for field in _CATALOG_OBSERVED_GROUP:
        assert field in document, field
    assert document["post_migration_chain"] == list(range(1, e0.TRANSITION_SOURCE_HEAD + 1))
    assert document["applied_migrations"] == []


def test_the_e0_catalog_observation_has_no_nonzero_preassignment_gap(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The equivalent E0 path: the claim and its one conditioned field arrive together.

    E0 reads nothing between them -- the chain it discloses was measured under its own lease
    before the window opens -- so the first failure after the claim finds the field already
    present. Failing the first disposition append lands exactly there.
    """
    _fail_the_append(monkeypatch, "SOURCE_DISPOSITION_RECORDED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, events = _reopen_terminal(evidence_root, "E0")
    assert _failure_of(document)["catalog_state_observed"] is True
    assert document["post_migration_chain"] == list(range(1, 16))
    assert "SOURCE_DISPOSITION_RECORDED" not in events


@pytest.mark.parametrize("standing", ["ordering_only", "derivation_only"])
def test_either_catalog_observed_guard_alone_still_produces_a_lawful_terminal(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
    standing: str,
) -> None:
    """Each guard closes the window on its own, which is why the mutation below removes both."""
    if standing == "ordering_only":
        # The disclosure-time derivation is disabled; the execute path's expose-then-claim
        # ordering is the only thing left, and the claim it makes is true.
        monkeypatch.setattr(
            e0, "_CATALOG_OBSERVED_FIELDS", {"catalog_transition": (), "m3_3_e0_offline_parse": ()}
        )
        expect_claimed = True
    else:
        # The pre-fix ordering is restored -- claim first, expose later -- and the derivation
        # alone must refuse to claim an observation whose group never arrived.
        monkeypatch.setattr(e0, "_catalog_observation", lambda record_type, values: {})
        expect_claimed = False

    _stall_the_chain_after_commit(monkeypatch)
    with pytest.raises(e0.PreflightRefusalError, match="did not move the chain head"):
        _run_transition(evidence_root, config)

    document, _ = _reopen_terminal(evidence_root, "TRANSITION")
    assert _failure_of(document)["catalog_state_observed"] is expect_claimed
    for field in _CATALOG_OBSERVED_GROUP:
        assert (field in document) is expect_claimed, field


def test_reintroducing_the_catalog_observed_window_makes_the_proof_fail(
    evidence_root: Path,
    catalog: Path,
    bound: M32World,
    config: _Config,
    activated_transition: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The MAJOR-1 non-vacuity control: with both guards gone, the defect returns exactly.

    `_catalog_observation` exposing nothing is the pre-fix ordering -- the flag is set while the
    group is still absent -- and the emptied conditioned-field table removes the disclosure-time
    derivation that would otherwise decline the claim. The run then freezes a create-once record
    its own validator refuses, which is what the reviewer reproduced.
    """
    monkeypatch.setattr(e0, "_catalog_observation", lambda record_type, values: {})
    monkeypatch.setattr(
        e0, "_CATALOG_OBSERVED_FIELDS", {"catalog_transition": (), "m3_3_e0_offline_parse": ()}
    )
    _stall_the_chain_after_commit(monkeypatch)
    with pytest.raises(e0.PreflightRefusalError, match="did not move the chain head"):
        _run_transition(evidence_root, config)

    expected = r"(applied_migrations|post_migration_chain|post_integrity) is required"
    with pytest.raises(e0.TerminalValidationError, match=expected):
        _reopen_terminal(evidence_root, "TRANSITION")
    assert e0.transition_verify(evidence_root=evidence_root).determined


# ==========================================================================
# Decision 099 final review MAJOR-2: the failed E0 source-result totality
#
# §9.2 fixes the failed set as "every durable event plus any independently observed category-A
# database boundary lacking its event; no other row". A handled failure used to default it to
# `[]` with all-zero counts even after every disposition had already become durable.
# ==========================================================================


def _interrupt_at_disposition(monkeypatch: pytest.MonkeyPatch, *, occurrence: int) -> None:
    """Interrupt exactly at the Nth category-A disposition append, inside the window."""
    original = e0.EventLedger.append
    seen = {"count": 0}

    def guarded(
        self: e0.EventLedger,
        kind: str,
        details: Mapping[str, object],
        *,
        observed_at_utc: str,
    ) -> Mapping[str, object]:
        if kind == "SOURCE_DISPOSITION_RECORDED" and details["disposition"] == "E0_REQUIRED_PARSE":
            seen["count"] += 1
            if seen["count"] == occurrence:
                message = "injected disposable-fixture operator interrupt"
                raise KeyboardInterrupt(message)
        return original(self, kind, details, observed_at_utc=observed_at_utc)

    monkeypatch.setattr(e0.EventLedger, "append", guarded)


def _details(event: Mapping[str, object]) -> Mapping[str, object]:
    details = event["details"]
    assert isinstance(details, Mapping)
    return details


def _durable_disposition_keys(evidence_root: Path) -> set[tuple[str, str]]:
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    events = e0.read_event_ledger(directory / e0.E0_EVENTS_FILENAME, kind="E0")
    return {
        (str(_details(event)["census_run_id"]), str(_details(event)["source_instance_id"]))
        for event in events
        if str(event["event_type"]) == "SOURCE_DISPOSITION_RECORDED"
    }


def _rows_of(document: Mapping[str, object]) -> list[Mapping[str, object]]:
    results = document["source_results"]
    assert isinstance(results, list)
    rows = []
    for row in results:
        assert isinstance(row, Mapping)
        rows.append(row)
    return rows


def _row_keys(document: Mapping[str, object]) -> list[tuple[str, str]]:
    return [
        (str(row["census_run_id"]), str(row["source_instance_id"])) for row in _rows_of(document)
    ]


def _assert_counts_reconcile(document: Mapping[str, object]) -> None:
    """Proof F: the closed count object is reproduced from the rows, never carried beside them."""
    rows = _rows_of(document)
    counts = document["source_result_counts"]
    assert isinstance(counts, Mapping)
    disposition_total = (
        int(counts["required_parse_count"])
        + int(counts["accepted_unavailable_count"])
        + int(counts["validation_or_provenance_only_count"])
    )
    assert disposition_total == len(rows)
    assert int(counts["parsed_record_count"]) == sum(int(row["parsed_records"]) for row in rows)
    assert int(counts["quarantined_record_count"]) == sum(
        int(row["quarantined_records"]) for row in rows
    )
    assert int(counts["planned_source_count"]) == e0.PLANNED_SOURCE_COUNT


def test_a_failure_after_many_durable_dispositions_reports_all_of_them(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proofs A and F: durable dispositions must not freeze as an empty set with zero counts."""
    _fail_the_append(monkeypatch, "FULL_INDEX_OBSERVATIONS_MATERIALIZED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    durable = _durable_disposition_keys(evidence_root)
    assert len(durable) == e0.PLANNED_SOURCE_COUNT
    assert _row_keys(document) == sorted(durable)
    assert all(row["ledger_event_present"] is True for row in _rows_of(document))
    _assert_counts_reconcile(document)


def test_a_failure_before_any_durable_boundary_invents_no_source_result(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proof B: absent durable evidence stays absent; it is never turned into a result.

    Injected at the backup boundary, which is genuinely *before* any category-A commit. The
    first disposition append is **not** that boundary and no longer stands in for it: accepted
    Decision 100 established that by the time it runs every category-A plan row has already
    committed durably, so an empty set there understates the run rather than describing it. That
    case is now proved as row C of the representability table instead.
    """
    _fail_the_append(monkeypatch, "BACKUP_VERIFIED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    assert document["source_results"] == []
    counts = document["source_result_counts"]
    assert isinstance(counts, Mapping)
    assert int(counts["required_parse_count"]) == 0
    assert int(counts["parsed_record_count"]) == 0
    # The plan itself is still observed truthfully; only the *results* are empty.
    assert int(counts["planned_source_count"]) == e0.PLANNED_SOURCE_COUNT
    # Measured, not assumed: nothing had crossed a boundary, so there was nothing to represent.
    assert _moved_plan_rows(evidence_root) == {}
    assert "interruption_state" not in _failure_of(document)


def test_a_boundary_without_its_event_joins_the_failed_set_exactly_once(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proofs C and D: the union is correct, deduplicated, and never double counted."""
    _interrupt_at_disposition(monkeypatch, occurrence=2)
    with pytest.raises(KeyboardInterrupt, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    assert _failure_of(document)["interruption_state"] == "after_e0_source_commit_before_event"

    durable = _durable_disposition_keys(evidence_root)
    keys = _row_keys(document)
    # Proof D: exactly one row per pair. The first category-A source is present both durably and
    # in boundary state, and it appears once, attributed to its durable event.
    assert len(keys) == len(set(keys))
    assert keys == sorted(keys)
    assert durable <= set(keys)
    assert durable, "the interrupt left no durable disposition to corroborate"

    boundary = [row for row in _rows_of(document) if row["ledger_event_present"] is False]
    assert boundary, "the interrupt left no boundary lacking its durable event"
    with strictly_read_only_connection(_catalog_path(evidence_root)) as connection:
        observed = {
            (str(row["census_run_id"]), str(row["source_instance_id"])): str(row["parser_state"])
            for row in connection.execute(
                "SELECT census_run_id, source_instance_id, parser_state FROM census_plan_sources"
            ).fetchall()
        }
    # Proof C: every boundary row is a category-A source the catalog itself reports as moved,
    # carrying the state the catalog reports rather than one inferred here.
    for row in boundary:
        key = (str(row["census_run_id"]), str(row["source_instance_id"]))
        assert key not in durable
        assert row["disposition"] == "E0_REQUIRED_PARSE"
        assert observed[key] != "not_started"
        assert row["parser_state_after"] == observed[key]
    # No row is invented for a source that never crossed a boundary and has no durable event.
    for key in set(observed) - set(keys):
        assert observed[key] == "not_started"
    _assert_counts_reconcile(document)


def test_an_unverifiable_e0_ledger_manufactures_no_failed_set(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Proof E: fail-closed wins over a manufactured set when the evidence cannot be verified."""
    original = e0.EventLedger.append

    def guarded(
        self: e0.EventLedger,
        kind: str,
        details: Mapping[str, object],
        *,
        observed_at_utc: str,
    ) -> Mapping[str, object]:
        if kind == "FULL_INDEX_OBSERVATIONS_MATERIALIZED":
            self.path.chmod(0o600)
            with self.path.open("ab") as handle:
                handle.write(b"not a canonical event\n")
            message = "injected disposable-fixture FULL_INDEX append failure"
            raise e0.E0Error(message)
        return original(self, kind, details, observed_at_utc=observed_at_utc)

    monkeypatch.setattr(e0.EventLedger, "append", guarded)
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    assert not (directory / e0.E0_TERMINAL_FILENAME).exists()
    report = e0.e0_verify(evidence_root=evidence_root)
    assert not report.determined
    assert not report.passed


@pytest.mark.parametrize("mutant", ["restore_the_empty_default", "drop_the_durable_derivation"])
def test_removing_the_durable_failed_set_derivation_makes_the_proof_fail(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
    mutant: str,
) -> None:
    """The MAJOR-2 non-vacuity control: the derivation is what produces the failed set."""
    if mutant == "restore_the_empty_default":
        monkeypatch.setattr(
            e0,
            "_failed_source_results",
            lambda *_a, **_k: ([], dict.fromkeys(e0.SOURCE_RESULT_COUNT_KEYS, 0)),
        )
    else:
        monkeypatch.setattr(e0, "_failed_source_results", lambda *_a, **_k: None)

    _fail_the_append(monkeypatch, "FULL_INDEX_OBSERVATIONS_MATERIALIZED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    if mutant == "drop_the_durable_derivation":
        # Declining to derive is fail-closed, so no terminal survives at all.
        assert not (directory / e0.E0_TERMINAL_FILENAME).exists()
        return
    document, _ = _reopen_terminal(evidence_root, "E0")
    # Schema-valid but untruthful: every disposition durable, none reported. This is the exact
    # defect, so the MAJOR-2 proofs above must fail whenever this default is restored.
    assert document["source_results"] == []
    assert len(_durable_disposition_keys(evidence_root)) == e0.PLANNED_SOURCE_COUNT


# ==========================================================================
# Accepted Decision 100: the commit-before-event representability gap
#
# `run_offline_metadata_parse` commits one category-A plan-row boundary **per source**, inside
# the call. The outer interruption variable only advances to
# `after_e0_source_commit_before_event` once that call *returns*, so a failure between a source's
# durable commit and its ledger append left the run reading `during_e0_source_parse` -- and the
# derivation gated boundary rows on exactly that reading. §9.2 required the row; the gate dropped
# it. Separately, §8.1 permits `interruption_state` only on an interrupted status, so even after
# the parser returned, a *failed* run could not state the window §9.3 requires for the row.
#
# D100 makes the disclosure describe the actual durable boundary: membership comes from the
# evidence, the interruption state is derived from the resulting rows, and the failure shape
# permits that state exactly where §9.3 mandates it.
# ==========================================================================

_COMMIT_BEFORE_EVENT = "after_e0_source_commit_before_event"


def _moved_plan_rows(evidence_root: Path) -> dict[tuple[str, str], str]:
    """Every plan row whose ``parser_state`` has left ``not_started``, read from the catalog."""
    with strictly_read_only_connection(_catalog_path(evidence_root)) as connection:
        return {
            (str(row["census_run_id"]), str(row["source_instance_id"])): str(row["parser_state"])
            for row in connection.execute(
                "SELECT census_run_id, source_instance_id, parser_state FROM census_plan_sources"
            ).fetchall()
            if str(row["parser_state"]) != "not_started"
        }


def _planned_dispositions(evidence_root: Path) -> dict[tuple[str, str], str]:
    """Each planned source's R18 disposition, from the production classifier, not a guess."""
    with strictly_read_only_connection(_catalog_path(evidence_root)) as connection:
        observations = {item.observation_id: item for item in op.load_observations(connection)}
        return {
            (source.census_run_id, source.source_instance_id): op.classify_planned_source(
                source,
                None if source.observation_id is None else observations.get(source.observation_id),
            )
            for source in op.load_planned_sources(connection)
        }


def _fail_inside_the_parser(monkeypatch: pytest.MonkeyPatch, *, occurrence: int) -> None:
    """Fail the Nth category-A parse, after N-1 boundaries have durably committed.

    ``_parse_source`` is the accepted per-source entry point, and ``materialize_source_layer``
    commits that source's ``census_parser_runs`` row and its ``census_plan_sources.parser_state``
    transition before moving to the next one. Raising here therefore lands inside
    ``run_offline_metadata_parse`` with a real durable boundary already behind it and no
    ``SOURCE_DISPOSITION_RECORDED`` event anywhere -- the exact window D100 governs.
    """
    original = op._parse_source
    seen = {"count": 0}

    def guarded(connection: object, store: object, observation: object) -> object:
        seen["count"] += 1
        if seen["count"] == occurrence:
            message = "injected disposable-fixture mid-parse failure"
            raise op.OfflineParseError(message)
        return original(connection, store, observation)  # type: ignore[arg-type]

    monkeypatch.setattr(op, "_parse_source", guarded)


def _assert_boundary_rows_match_the_catalog(
    document: Mapping[str, object], evidence_root: Path
) -> list[Mapping[str, object]]:
    """Every boundary row corresponds to a moved plan row, carrying the catalog's own state."""
    moved = _moved_plan_rows(evidence_root)
    durable = _durable_disposition_keys(evidence_root)
    boundary = [row for row in _rows_of(document) if row["ledger_event_present"] is False]
    for row in boundary:
        key = (str(row["census_run_id"]), str(row["source_instance_id"]))
        assert key in moved, key
        assert key not in durable, key
        assert row["parser_state_before"] == "not_started"
        assert row["parser_state_after"] == moved[key]
        assert row["disposition"] == "E0_REQUIRED_PARSE"
    # No moved boundary is omitted, and no unmoved source is invented.
    assert set(_row_keys(document)) == set(moved) | durable
    return boundary


def test_a_failure_inside_the_parser_states_its_durable_boundary(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row D, and D100 proofs 1, 2 and 6: the durable boundary is stated, not hidden.

    The run dies *inside* ``run_offline_metadata_parse``, so the outer variable still reads
    ``during_e0_source_parse`` and the status is ``failed`` rather than ``interrupted`` -- the
    two conditions that together made this record unstatable before. The production loader is
    the assertion: ``_reopen_terminal`` validates, so an unlawful record fails the test here
    rather than being asserted about field by field.
    """
    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    # The premise, measured rather than assumed: one durable boundary, and no durable event.
    moved = _moved_plan_rows(evidence_root)
    assert len(moved) == 1, moved
    assert _durable_disposition_keys(evidence_root) == set()

    document, _ = _reopen_terminal(evidence_root, "E0")
    assert document["status"] == "failed"
    failure = _failure_of(document)
    assert failure["reason_code"] == "M3_3_E0_OFFLINE_PARSE_FAILED"
    # Derived from the durable boundary, not from the call-stack position the run died at --
    # which is what `reason_detail` would otherwise have reported here.
    assert failure["interruption_state"] == _COMMIT_BEFORE_EVENT

    boundary = _assert_boundary_rows_match_the_catalog(document, evidence_root)
    assert len(_rows_of(document)) == 1
    assert len(boundary) == 1
    _assert_counts_reconcile(document)


def test_a_boundary_row_carries_the_parser_run_the_catalog_recorded(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The row reports the boundary's own durable output rather than defaulting it to zero."""
    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    (row,) = _rows_of(document)
    with strictly_read_only_connection(_catalog_path(evidence_root)) as connection:
        runs = [dict(item) for item in connection.execute("SELECT * FROM census_parser_runs")]
    assert len(runs) == 1, runs
    assert row["parser_run_id"] == runs[0]["parser_run_id"]
    assert int(row["parsed_records"]) == int(runs[0]["parsed_count"])
    assert int(row["quarantined_records"]) == int(runs[0]["quarantined_count"])
    assert row["observation_id"] == runs[0]["source_observation_id"]


def test_a_failure_after_the_parser_returns_states_every_boundary(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row C: the parser returned, no event is durable yet, and the status is ``failed``.

    Every category-A boundary has committed by the time the first disposition append runs, so
    §9.2 requires all of them. Before D100 this froze an empty set, because a failed terminal
    could not state the window §9.3 requires for the rows.
    """
    _fail_the_append(monkeypatch, "SOURCE_DISPOSITION_RECORDED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    moved = _moved_plan_rows(evidence_root)
    assert moved, "the parser returned without committing a single boundary"
    assert _durable_disposition_keys(evidence_root) == set()

    document, _ = _reopen_terminal(evidence_root, "E0")
    assert document["status"] == "failed"
    assert _failure_of(document)["interruption_state"] == _COMMIT_BEFORE_EVENT
    boundary = _assert_boundary_rows_match_the_catalog(document, evidence_root)
    assert len(boundary) == len(moved)
    _assert_counts_reconcile(document)


def test_a_durable_event_and_its_own_boundary_produce_exactly_one_row(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row E, and D100 proof 3: the union deduplicates toward the durable event.

    The interrupt lands in the disposition loop, so the first category-A source is present
    **both** durably in the ledger and as a moved plan row. It must appear once, attributed to
    its event, while the sources whose events never landed appear once as boundary rows.
    """
    _interrupt_at_disposition(monkeypatch, occurrence=2)
    with pytest.raises(KeyboardInterrupt, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    durable = _durable_disposition_keys(evidence_root)
    moved = _moved_plan_rows(evidence_root)
    assert durable, "the interrupt left no durable disposition to corroborate"
    # The overlap is the point: these keys are attested twice and must still be stated once.
    # `durable` is not a subset of `moved`: category B and C also receive a disposition event,
    # and they deliberately receive no `parser_state` transition to go with it.
    overlap = durable & set(moved)
    assert overlap, "the interrupt left no source attested both durably and in boundary state"

    keys = _row_keys(document)
    assert len(keys) == len(set(keys))
    assert set(keys) == set(moved) | durable
    for row in _rows_of(document):
        key = (str(row["census_run_id"]), str(row["source_instance_id"]))
        assert row["ledger_event_present"] is (key in durable), key
    _assert_boundary_rows_match_the_catalog(document, evidence_root)
    _assert_counts_reconcile(document)


def test_no_non_category_a_source_gains_the_boundary_exception(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D100 proof 5: the exception reaches category A only, by the accepted write set itself.

    Category B and C receive no ``census_plan_sources.parser_state`` transition, so they have no
    database boundary that could be observed independently of their ledger event. That is
    measured against the production classifier rather than assumed from the source ids.
    """
    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    dispositions = _planned_dispositions(evidence_root)
    others = {key for key, value in dispositions.items() if value != "E0_REQUIRED_PARSE"}
    assert others, "the fixture plan holds no non-category-A source to prove the exclusion with"

    moved = _moved_plan_rows(evidence_root)
    document, _ = _reopen_terminal(evidence_root, "E0")
    stated = set(_row_keys(document))
    for key in others:
        assert key not in moved, key
        assert key not in stated, key
    assert all(row["disposition"] == "E0_REQUIRED_PARSE" for row in _rows_of(document))


def test_unreadable_boundary_evidence_manufactures_no_failed_set(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Row F: unverifiable boundary evidence fails closed exactly as an unverifiable ledger does."""

    def unreadable(catalog_path: Path) -> object:
        message = "injected disposable-fixture boundary-evidence read failure"
        raise sqlite3.OperationalError(message)

    monkeypatch.setattr(e0, "_plan_boundary_evidence", unreadable)
    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    assert not (directory / e0.E0_TERMINAL_FILENAME).exists()
    report = e0.e0_verify(evidence_root=evidence_root)
    assert not report.determined
    assert not report.passed


def test_an_interrupted_run_records_its_interrupted_event(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """§10.2's tail event is projected to its closed key set, so it can actually become durable.

    Copying the whole failure object carried ``catalog_state_observed``, which is a terminal
    field and not a permitted ``INTERRUPTED`` detail key. Every append was therefore refused and
    the refusal swallowed, leaving an interrupted run with no ``INTERRUPTED`` event at all. The
    ledger and the terminal must state one interruption state, so the event must exist to state
    it -- which is why D100 fixes it alongside the derivation.
    """
    _interrupt_at_disposition(monkeypatch, occurrence=2)
    with pytest.raises(KeyboardInterrupt, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    events = e0.read_event_ledger(directory / e0.E0_EVENTS_FILENAME, kind="E0")
    tail = [event for event in events if str(event["event_type"]) == "INTERRUPTED"]
    assert len(tail) == 1, [str(event["event_type"]) for event in events]
    details = _details(tail[0])
    assert set(details) == {"reason_code", "reason_detail", "interruption_state"}

    document, _ = _reopen_terminal(evidence_root, "E0")
    # The two durable records of one run agree, which is the whole reason the state is derived
    # before the tail event rather than after it.
    assert details["interruption_state"] == _failure_of(document)["interruption_state"]
    assert details["interruption_state"] == _COMMIT_BEFORE_EVENT


def test_a_failed_run_states_no_interruption_state_without_a_boundary_row(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The widening is bounded: §8.1's rule still governs everywhere §9.3 does not override it.

    A failed run with no boundary row states no interruption state, its ``FAILED`` event carries
    only §10.2's two keys, and the receipt omits the field its own §10.1 schema conditions on an
    interrupted status.
    """
    _fail_the_append(monkeypatch, "FULL_INDEX_OBSERVATIONS_MATERIALIZED")
    with pytest.raises(e0.E0Error, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    assert document["status"] == "failed"
    assert all(row["ledger_event_present"] is True for row in _rows_of(document))
    assert "interruption_state" not in _failure_of(document)

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    events = e0.read_event_ledger(directory / e0.E0_EVENTS_FILENAME, kind="E0")
    (tail,) = [event for event in events if str(event["event_type"]) == "FAILED"]
    assert set(_details(tail)) == {"reason_code", "reason_detail"}
    receipt = inspect_receipt(directory / OPERATOR_RECEIPT_FILENAME)
    assert "interruption_state" not in receipt


def test_a_failed_terminal_may_not_state_an_interruption_state_it_has_not_earned(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The widening cannot be borrowed: without a boundary row the §8.1 rule still refuses."""
    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    document, _ = _reopen_terminal(evidence_root, "E0")
    stripped = dict(document)
    stripped["source_results"] = [
        dict(row) for row in _rows_of(document) if row["ledger_event_present"]
    ]
    raw_counts = document["source_result_counts"]
    assert isinstance(raw_counts, Mapping)
    counts = dict(raw_counts)
    counts["required_parse_count"] = 0
    counts["parsed_record_count"] = 0
    counts["quarantined_record_count"] = 0
    counts["parser_completed_count"] = 0
    stripped["source_result_counts"] = counts
    with pytest.raises(e0.TerminalValidationError, match="interruption_state"):
        e0.validate_e0_terminal(stripped, event_types=frozenset({"PREFLIGHT_PASSED", "FAILED"}))


@pytest.mark.parametrize("mutant", ["regate_on_the_outer_state", "restore_the_section_8_1_rule"])
def test_restoring_the_pre_d100_behavior_makes_the_targeted_proof_fail(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    monkeypatch: pytest.MonkeyPatch,
    mutant: str,
) -> None:
    """The D100 non-vacuity control: each half of the pre-D100 rule reproduces the defect.

    ``regate_on_the_outer_state`` restores the removed derivation gate. Inside the parser the
    caller's variable reads ``during_e0_source_parse``, so the gate dropped every boundary row
    and the derivation returned the empty set -- which is exactly the value asserted below.
    ``restore_the_section_8_1_rule`` restores "``interruption_state`` iff interrupted", leaving a
    frozen record whose own production loader refuses it.
    """
    if mutant == "regate_on_the_outer_state":
        monkeypatch.setattr(
            e0,
            "_failed_source_results",
            lambda *_a, **_k: (
                [],
                {
                    **dict.fromkeys(e0.SOURCE_RESULT_COUNT_KEYS, 0),
                    "planned_source_count": e0.PLANNED_SOURCE_COUNT,
                },
            ),
        )
    else:
        monkeypatch.setattr(e0, "_states_a_source_boundary", lambda _document: False)

    _fail_inside_the_parser(monkeypatch, occurrence=2)
    with pytest.raises(op.OfflineParseError, match="injected"):
        e0.e0_execute(evidence_root=evidence_root, config=config)

    # The durable boundary exists under either mutant; only the disclosure of it is broken.
    assert len(_moved_plan_rows(evidence_root)) == 1

    if mutant == "regate_on_the_outer_state":
        document, _ = _reopen_terminal(evidence_root, "E0")
        assert document["source_results"] == []
        assert "interruption_state" not in _failure_of(document)
        return
    expected = r"failure carries key\(s\) \('interruption_state',\) outside its closed set"
    with pytest.raises(e0.TerminalValidationError, match=expected):
        _reopen_terminal(evidence_root, "E0")


# ==========================================================================
# Family 10: the Decision 103 R8 successor generation
#
# Every test below drives the shipped v2 constant over a disposable catalog beneath a
# synthetic root, beside a synthetic v1 predecessor built by the real event ledger. Nothing
# here resolves, opens, names, or infers the accepted private root, and nothing touches the
# real interrupted v1 run.
# ==========================================================================


def _lease_document(evidence_root: Path, **overrides: object) -> Path:
    """Write a `held` writer lease beside the disposable catalog and return its path."""
    from disclosure_drift.storage.catalog import lease_path

    catalog = _catalog_path(evidence_root)
    path = lease_path(catalog.parent)
    payload: dict[str, object] = {
        "lease_id": "0" * 32,
        "writer_pid": 999_999,
        "host_fingerprint": "synthetic-host",
        "acquired_at_utc": _AT,
        "expires_at_utc": _AT,
        "state": "held",
    }
    payload.update(overrides)
    path.write_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
    path.chmod(0o600)
    return path


def test_e0_preflight_refuses_while_the_writer_lease_records_held(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """E-T1 and D103 R3: the ordinary E0 surface still refuses a held lease, unchanged.

    The recovery command exists precisely so this refusal never has to be softened. E0 does
    not consult it, does not clear a lease, and does not gain a "the writer looks dead" path.
    """
    _lease_document(evidence_root)
    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert not report.passed
    assert report.facts["writer_lease"] == "held"
    assert any("lease state is 'held'" in item for item in report.refusals)


def test_e0_preflight_passes_its_lease_predicate_once_the_lease_reads_released(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """E-T1's other half: `released` is the state that clears the predicate, and only that."""
    _lease_document(evidence_root, state="released", released_at_utc=_AT)
    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert report.passed, report.refusals
    assert report.facts["writer_lease"] == "released"


def test_e0_requires_the_interrupted_predecessor_to_be_present(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """E-T3 and D103 R2: a deleted or renamed v1 stops the successor rather than freeing it.

    The predecessor is moved aside rather than emptied, which is the exact shape of the thing
    R2 forbids: v1 gone, everything else intact, and a successor that would otherwise proceed.
    """
    directory = e0.namespace_directory(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    directory.rename(directory.with_name("moved-aside"))

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert report.facts["predecessor_state"] == "absent"
    assert any("is absent or is not a real directory" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged"):
        e0.e0_execute(evidence_root=evidence_root, config=config)
    assert not e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE).exists()


@pytest.mark.parametrize("filename_attribute", ["E0_TERMINAL_FILENAME"])
def test_a_predecessor_carrying_a_manufactured_terminal_stops_the_successor(
    evidence_root: Path,
    transitioned: Path,
    config: _Config,
    activated_e0: None,
    filename_attribute: str,
) -> None:
    """E-T4 and D103 R2: v1 may never become current-success evidence.

    A terminal record dropped into v1 is the cheapest way to fake a completed predecessor, so
    that is exactly what is attempted here. The successor refuses at preflight and again under
    the lease, and creates no v2 namespace.
    """
    directory = e0.namespace_directory(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    (directory / getattr(e0, filename_attribute)).write_text('{"status": "complete"}\n', "utf-8")

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("may never be mutated into a successful run" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged"):
        e0.e0_execute(evidence_root=evidence_root, config=config)
    assert not e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE).exists()


def test_a_predecessor_carrying_an_execution_receipt_stops_the_successor(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """E-T4: a receipt is the other way a run claims it finished, and it is refused too."""
    directory = e0.namespace_directory(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    (directory / OPERATOR_RECEIPT_FILENAME).write_text("{}\n", "utf-8")

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("may never be mutated into a successful run" in item for item in report.refusals)


@pytest.mark.parametrize("closing", ["EXECUTION_RECEIPT_WRITTEN", "FAILED", "INTERRUPTED"])
def test_a_predecessor_whose_ledger_closed_stops_the_successor(
    evidence_root: Path, config: _Config, closing: str
) -> None:
    """E-T4: the accepted predecessor reached no closing boundary, and that is checked.

    Appended through the real ledger so the chain stays valid — the refusal has to come from
    the event *vocabulary*, not from a broken hash chain that would refuse anything.
    """
    build_catalog(evidence_root, head=15)
    install_interrupted_predecessor(evidence_root)
    directory = e0.namespace_directory(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    events = e0.read_event_ledger(directory / e0.E0_EVENTS_FILENAME, kind="E0")
    ledger = e0.EventLedger(
        directory / e0.E0_EVENTS_FILENAME, e0.E0_PREDECESSOR_RUN_NAMESPACE, kind="E0"
    )
    ledger._sequence = len(events)  # noqa: SLF001 - continue the real chain, not a new one
    ledger._previous = str(events[-1]["event_sha256"])  # noqa: SLF001
    details: dict[str, object] = {"reason_code": "R-QA-006", "reason_detail": "synthetic"}
    if closing == "EXECUTION_RECEIPT_WRITTEN":
        details = {"execution_receipt_id": "a" * 64}
    elif closing == "INTERRUPTED":
        details["interruption_state"] = "before_backup"
    ledger.append(closing, details, observed_at_utc=_AT)

    refusals, facts = e0._predecessor_refusals(evidence_root)  # noqa: SLF001
    assert facts["predecessor_state"] == "closed"
    assert facts["predecessor_event_chain"] == "valid"
    assert any("records closing event(s)" in item for item in refusals)


def test_a_predecessor_with_a_broken_event_chain_stops_the_successor(
    evidence_root: Path, config: _Config
) -> None:
    """E-T3 and D103 R2: v1's immutability is verified, not assumed."""
    build_catalog(evidence_root, head=15)
    directory = install_interrupted_predecessor(evidence_root)
    ledger_path = directory / e0.E0_EVENTS_FILENAME
    # Edit the first event's payload without recomputing its digest: the chain no longer
    # verifies, which is what an edited immutable ledger looks like. Truncating the file
    # instead would leave a shorter but internally consistent chain, which this ledger cannot
    # detect on its own and which the terminal record is what catches.
    lines = ledger_path.read_text("utf-8").splitlines(keepends=True)
    lines[0] = lines[0].replace('"planned_source_count":76', '"planned_source_count":75')
    ledger_path.write_text("".join(lines), "utf-8")

    refusals, facts = e0._predecessor_refusals(evidence_root)  # noqa: SLF001
    assert facts["predecessor_event_chain"] == "invalid"
    assert any("event ledger did not verify" in item for item in refusals)


def test_the_accepted_predecessor_shape_is_undetermined_not_complete(
    evidence_root: Path, predecessor: Path
) -> None:
    """E-T3 and D103 R2: absence of a terminal is reported as UNDETERMINED, never success."""
    refusals, facts = e0._predecessor_refusals(evidence_root)  # noqa: SLF001

    assert refusals == []
    assert facts["predecessor_state"] == "UNDETERMINED / NOT COMPLETE"
    assert facts["predecessor_terminal_record"] == "absent"
    assert facts["predecessor_execution_receipt"] == "absent"
    assert facts["predecessor_event_count"] == 2


def test_an_existing_v2_namespace_refuses_the_create_once_execution(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """N5: create-once is create-once for the successor generation too."""
    e0.create_run_namespace(evidence_root, e0.E0_RUN_NAMESPACE)

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)
    assert not report.passed
    assert any("already exists; it is create-once" in item for item in report.refusals)

    with pytest.raises(e0.PreflightRefusalError, match="under-lease recheck diverged"):
        e0.e0_execute(evidence_root=evidence_root, config=config)


def test_the_successor_writes_its_own_namespace_backup_and_event_sequence(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """N4, N6, E-T5, E-T6: v2 is a run, not a continuation of v1.

    Four separable claims, proved together because they are one property: the successor starts
    from nothing. Its namespace is its own, its backup is its own file, its ledger starts at
    sequence 1, and v1's ledger is byte-identical afterwards.
    """
    predecessor_directory = e0.namespace_directory(evidence_root, e0.E0_PREDECESSOR_RUN_NAMESPACE)
    before = (predecessor_directory / e0.E0_EVENTS_FILENAME).read_bytes()

    outcome = e0.e0_execute(evidence_root=evidence_root, config=config)
    assert outcome.status == "complete"
    assert outcome.run_namespace == e0.E0_RUN_NAMESPACE == "m3_3_e0_offline_parse_v2"

    successor = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    assert successor.is_dir()
    assert successor != predecessor_directory

    # E-T5: a distinct backup file, in the successor's own namespace.
    assert (successor / e0.E0_BACKUP_FILENAME).is_file()
    assert not (predecessor_directory / e0.E0_BACKUP_FILENAME).exists()

    # N6: the successor's ledger is its own chain, from sequence 1, with no inherited head.
    events = e0.read_event_ledger(successor / e0.E0_EVENTS_FILENAME, kind="E0")
    assert [event["sequence"] for event in events[:2]] == [1, 2]
    assert all(event["run_namespace"] == e0.E0_RUN_NAMESPACE for event in events)
    assert "previous_event_sha256" not in events[0]

    # E-T6: v1's ledger is untouched, byte for byte.
    assert (predecessor_directory / e0.E0_EVENTS_FILENAME).read_bytes() == before
    assert not (predecessor_directory / e0.E0_TERMINAL_FILENAME).exists()
    assert not (predecessor_directory / OPERATOR_RECEIPT_FILENAME).exists()


def test_the_successor_run_records_zero_network_activity(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """E-T7: the zero-network construction the successor generation inherits, restated."""
    e0.e0_execute(evidence_root=evidence_root, config=config)
    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))

    assert document["actual_logical_request_count"] == 0
    assert document["actual_physical_attempt_count"] == 0
    receipt = inspect_receipt(directory / OPERATOR_RECEIPT_FILENAME)
    assert receipt["actual_logical_request_count"] == 0
    assert receipt["actual_physical_attempt_count"] == 0


def test_the_successor_leaves_the_migration_chain_at_0015_and_creates_no_0016(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """E-T8: E0 applies no migration, and no sixteenth migration is packaged."""
    assert all(migration.version <= 15 for migration in available_migrations())  # noqa: PLR2004

    e0.e0_execute(evidence_root=evidence_root, config=config)
    with strictly_read_only_connection(transitioned) as connection:
        assert applied_versions(connection) == tuple(range(1, 16))

    directory = e0.namespace_directory(evidence_root, e0.E0_RUN_NAMESPACE)
    document = json.loads((directory / e0.E0_TERMINAL_FILENAME).read_text("utf-8"))
    assert document["post_migration_chain"] == list(range(1, 16))
    assert "applied_migrations" not in document


# ==========================================================================
# Family 11: the Decision 105 unreadable-lease fail-closed correction
#
# Decision 103 R4 rewrites the lease **in place**, so an interrupted rewrite can leave a lease
# file that is not a readable document. Decision 105 fixes what the ordinary transition/E0
# lease predicate must then do: an *existing* lease clears predicate 9 only by being a
# structurally valid document that records exactly `released`. An unreadable lease is not a
# released lease, and it never becomes one by being unreadable.
#
# Everything here drives the shipped predicate over a disposable catalog beneath a synthetic
# root. No test reads, resolves, or names the accepted private root or its real lease.
# ==========================================================================


def _lease_bytes(**overrides: object) -> bytes:
    """Canonical bytes of an otherwise-valid ``held`` lease, with ``overrides`` applied."""
    payload: dict[str, object] = {
        "lease_id": "0" * 32,
        "writer_pid": 999_999,
        "host_fingerprint": "synthetic-host",
        "acquired_at_utc": _AT,
        "expires_at_utc": _AT,
        "state": "held",
    }
    payload.update(overrides)
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def _lease_bytes_without(field: str) -> bytes:
    payload = json.loads(_lease_bytes().decode("utf-8"))
    del payload[field]
    return json.dumps(payload, sort_keys=True).encode("utf-8")


def _write_lease_bytes(evidence_root: Path, raw: bytes) -> Path:
    """Put exactly ``raw`` at the lease path beside the disposable catalog."""
    from disclosure_drift.storage.catalog import lease_path

    path = lease_path(_catalog_path(evidence_root).parent)
    path.write_bytes(raw)
    path.chmod(0o600)
    return path


#: Every shape an **existing** lease file can take that is not a structurally valid document
#: recording a state this module has ever written. The first three are the Decision 103 crash
#: window itself: the in-place rewrite truncates and then writes, so an interruption leaves an
#: empty file or a prefix of the intended document, and a shorter overwrite that lost its
#: truncation would leave the new document followed by a tail of the old one. The rest are the
#: ways a lease can be well-formed JSON and still not be a lease this repository wrote.
_UNREADABLE_LEASE_DOCUMENTS = (
    pytest.param(b"", id="truncated-to-zero"),
    pytest.param(_lease_bytes()[:41], id="torn-prefix"),
    pytest.param(_lease_bytes(writer_pid=1) + b'd": 999999}', id="trailing-tail-of-the-old"),
    pytest.param(b"not json at all", id="not-json"),
    pytest.param(b"[]", id="json-array"),
    pytest.param(b"\xff\xfe", id="not-utf8"),
    pytest.param(_lease_bytes_without("state"), id="missing-state"),
    pytest.param(_lease_bytes(state="reconciling"), id="unknown-state-token"),
    pytest.param(_lease_bytes(state=17), id="state-not-a-string"),
    pytest.param(_lease_bytes(injected_field="anything"), id="unknown-field"),
    pytest.param(_lease_bytes(writer_pid=0), id="non-positive-writer-pid"),
    pytest.param(_lease_bytes(expires_at_utc="2026-08-16 22:00:35"), id="malformed-timestamp"),
)

#: The one refusal Decision 105 adds. Asserted by substring so the test binds to the claim the
#: operator reads, not to the whole sentence.
_D105_REFUSAL = "is not a structurally valid lease recording 'released'"


@pytest.mark.parametrize("raw", _UNREADABLE_LEASE_DOCUMENTS)
def test_an_existing_unusable_writer_lease_refuses_the_ordinary_e0_preflight(
    evidence_root: Path, transitioned: Path, config: _Config, raw: bytes
) -> None:
    """D105 case C, and T3/T4/T5: an existing lease that is not readable stops E0.

    The refusal is required to come from the lease predicate specifically, so the assertion
    names the D105 sentence rather than settling for ``not report.passed`` — which a bad fix
    could satisfy by refusing for some unrelated reason. The bytes are re-read afterwards
    because a read-only preflight must never repair the document it refuses.
    """
    path = _write_lease_bytes(evidence_root, raw)

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert not report.passed
    assert any(_D105_REFUSAL in item for item in report.refusals)
    assert report.facts["writer_lease"] != "absent"
    assert path.read_bytes() == raw


@pytest.mark.parametrize("raw", _UNREADABLE_LEASE_DOCUMENTS)
def test_an_existing_unusable_writer_lease_refuses_the_pre_e0_transition_preflight(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config, raw: bytes
) -> None:
    """D105 case C at the other ordinary gate: the PRE-E0 transition refuses identically.

    Both machines read predicate 9 through one shared implementation, and this is what makes
    that shared-ness a checked claim rather than a reading of the source.
    """
    _write_lease_bytes(evidence_root, raw)

    report = e0.transition_preflight(evidence_root=evidence_root, config=config)

    assert not report.passed
    assert any(_D105_REFUSAL in item for item in report.refusals)


@pytest.mark.parametrize("raw", _UNREADABLE_LEASE_DOCUMENTS)
def test_no_unusable_lease_is_ever_reported_as_a_released_lease(
    evidence_root: Path, catalog: Path, raw: bytes
) -> None:
    """T6: the reader cannot mint ``released`` out of a document it could not validate.

    This is the exact laundering path Decision 105 closes, asserted at the reader rather than
    at the refusal: an unreadable document used to reach the consumer as ``state = None``,
    which is not ``'held'`` and so used to look like permission to proceed. The lock is
    confirmed shareable so the refusal cannot be coming from a live ``flock`` instead.
    """
    _write_lease_bytes(evidence_root, raw)

    present, recorded_state, shareable = e0._lease_state(catalog.parent)  # noqa: SLF001

    assert present is True
    assert shareable is True
    assert recorded_state != "released"


def test_a_valid_held_lease_still_refuses_with_its_unchanged_refusal(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """T1 and D105 case A: the accepted ``held`` refusal is preserved word for word.

    D105 must not merge the two refusals: "a writer holds this" and "this is not a lease I can
    read" are different facts about the world, and an operator acts differently on each.
    """
    _write_lease_bytes(evidence_root, _lease_bytes())

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert not report.passed
    assert report.facts["writer_lease"] == "held"
    assert any("lease state is 'held'" in item for item in report.refusals)
    assert not any(_D105_REFUSAL in item for item in report.refusals)


def test_the_decision_103_reconciled_release_still_clears_the_lease_predicate(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """T2 and D105 case B: the recovery's own output is a lease the ordinary gate accepts.

    Built by the production ``reconciled_lease_document`` rather than by hand, because the
    thing that must keep working is the real R4 document — the whole point of reconciling a
    stale lease is that E0 may then proceed, and a fail-closed reader that refused the
    recovery's result would have closed the door it was opening.
    """
    from disclosure_drift.storage.catalog import read_persisted_lease, reconciled_lease_document

    held = read_persisted_lease(_lease_bytes())
    document = reconciled_lease_document(held, reconciled_at_utc=_AT)
    _write_lease_bytes(evidence_root, canonical_bytes(document))

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert report.passed, report.refusals
    assert report.facts["writer_lease"] == "released"


def test_an_ordinary_released_lease_still_clears_the_lease_predicate(
    evidence_root: Path, transitioned: Path, config: _Config
) -> None:
    """T2's other half: an ordinary holder release, which carries ``released_at_utc``."""
    _write_lease_bytes(evidence_root, _lease_bytes(state="released", released_at_utc=_AT))

    report = e0.e0_preflight(evidence_root=evidence_root, config=config)

    assert report.passed, report.refusals
    assert report.facts["writer_lease"] == "released"


def test_an_absent_lease_keeps_its_pre_d105_semantics_exactly(
    evidence_root: Path, catalog: Path, bound: M32World, config: _Config
) -> None:
    """T7 and D105 case D: absence is untouched — it passes, and is still never created.

    Decision 094 finding m1 is the reason: a read-only preflight must not create the lock file
    to discover whether it could take it. D105 fixes what an *existing* lease means, and is
    required to leave "there is no lease" exactly as it found it.
    """
    lease = catalog.parent / "catalog_writer.lease"
    assert not lease.exists()

    present, recorded_state, shareable = e0._lease_state(catalog.parent)  # noqa: SLF001
    report = e0.transition_preflight(evidence_root=evidence_root, config=config)

    assert (present, recorded_state, shareable) == (False, None, True)
    assert report.passed, report.refusals
    assert report.facts["writer_lease"] == "absent"
    assert not any(_D105_REFUSAL in item for item in report.refusals)
    assert not lease.exists()


def test_decision_105_grants_no_recovery_authority() -> None:
    """T9: D105 is a reader correction, and corrects nothing about who may reconcile.

    Asserted against the shipped **source** as well as the attribute, because a runtime check
    alone would pass against a module an earlier test had already overridden.

    The recovery surface shipped ``None`` when D105 landed; **Decision 107 §3 (R116)** briefly
    activated it for exactly one real reconciliation, and **§5 (R118)** withdrew it again once
    that reconciliation was executed and verified. So the shipped state is ``None`` once more,
    and the D105 claim is unchanged either way: its reader correction produced no reconciliation
    authority, and no token of any generation — D103's illustrative literal or D107's spent
    instrument — is what the module carries.
    """
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None
    source = Path(e0.__file__).read_text(encoding="utf-8")
    assert "M3_3_D103_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED" not in source
    assert "M3_3_D107_REAL_STALE_WRITER_LEASE_RECONCILIATION_AUTHORIZED" not in source


def test_the_shipped_e0_door_is_shut_and_the_constant_is_still_the_only_one(
    monkeypatch: pytest.MonkeyPatch, config: _Config, tmp_path: Path
) -> None:
    """Decision 108 §5 (R122): E0 ``execute`` is shut, and shut by that constant alone.

    Deliberately **not** monkeypatched for the first half. Every other execute test here injects
    a disposable token, which is the only honest way to exercise the machine; this one is the
    complement, and its whole value is that it runs the door the repository actually ships.

    This test has now asserted both shapes: shut under Decision 107 §4 (R117), open under
    Decision 108 §2 (R120), and shut again here on the interrupted invocation's return. The
    property under test survived every inversion unchanged, and is what both halves establish
    together: the constant is the **sole** door. Shipped, the refusal is exit ``3`` from a gate
    that runs ahead of root resolution and consults no lease, catalog page, namespace, or
    receipt; patched to a disposable token, the identical call passes that gate and the *next*
    one — root resolution, with no variable set — refuses at exit ``1``. Activation is necessary
    and never sufficient, in both directions.

    No evidence root is offered on either path, so a passing gate cannot reach private state
    here — which is why the exit ``1`` is the *positive* evidence that the door would open.
    """
    assert e0.M3_3_E0_EXECUTION_AUTHORITY is None

    for environ in ({}, {EVIDENCE_ROOT_ENV: ""}):
        shut = e0.run_offline_parse_command(
            mode="execute", config=config, repository_root=tmp_path, environ=environ
        )
        assert shut.exit_code == e0.EXIT_STAGE_NOT_ENABLED
        assert any("is None" in line for line in shut.lines)

    monkeypatch.setattr(e0, "M3_3_E0_EXECUTION_AUTHORITY", "TEST-ONLY-DISPOSABLE-TOKEN")
    opened = e0.run_offline_parse_command(
        mode="execute", config=config, repository_root=tmp_path, environ={}
    )
    assert opened.exit_code == e0.EXIT_CONFIG_ERROR
    assert not any("is None" in line for line in opened.lines)


def test_the_two_neighbouring_execute_surfaces_stay_shut_as_shipped(
    evidence_root: Path, transitioned: Path, config: _Config, tmp_path: Path
) -> None:
    """Decision 108 §3 (R119) and §1: E0's neighbours stay shut across every move E0 makes.

    This is the capability separation from the other side. Decision 107 §4 shut E0 so that a
    successful reconciliation could not re-enable it; the same rule read forward says an E0
    instrument may not re-enable the transition or the recovery, whose grants are both spent —
    and neither may an E0 *interruption*, which is the state this now holds across. All three
    constants are ``None`` again. Deliberately **not** monkeypatched, for the same reason as the
    test above: these are the doors the repository actually ships.

    The evidence root is the fully transitioned one on purpose — a COMPLETE transition terminal
    is exactly the state from which an operator might expect to re-run the transition, and it
    carries nothing. Exit ``3`` must also win over root resolution with no variable set, because
    "this stage is not enabled" may never depend on the environment being configured.
    """
    assert e0.PRE_E0_CATALOG_TRANSITION_AUTHORITY is None
    assert e0.STALE_WRITER_LEASE_RECOVERY_AUTHORITY is None

    runners = (e0.run_prepare_e0_catalog_command, e0.run_reconcile_writer_lease_command)
    for runner in runners:
        for environ in (_environ(evidence_root), {}, {EVIDENCE_ROOT_ENV: ""}):
            result = runner(
                mode="execute", config=config, repository_root=tmp_path, environ=environ
            )
            assert result.exit_code == e0.EXIT_STAGE_NOT_ENABLED
            assert any("is None" in line for line in result.lines)

    assert not e0.namespace_directory(evidence_root, e0.LEASE_RECOVERY_RUN_NAMESPACE).exists()


def test_no_second_door_runs_e0_around_its_activation_constant() -> None:
    """Decision 108 §2 (R120): one gate, read from one constant, on every E0 execute path.

    The risk this closes is not that ``_require_activation`` stops working — it is that some
    *other* entry point reaches the E0 machine without passing through it. Every module-level
    callable is walked, not just the exported ones (``e0_execute`` is itself not in ``__all__``,
    so an ``__all__`` walk would have missed the primary door), and the module is required to
    carry exactly three ``execute`` callables — **one per governed surface**. ``e0_execute`` is
    E0's only one, and ``run_offline_parse_command`` is the CLI wrapper the test above already
    drives through that constant in both directions.

    This matters more now that the constant is **open**, not less. While E0 shipped disabled, a
    second door would have been a way to run E0 without authority; with Decision 108 §2 (R120)
    holding one exactly-once grant, a second door is also a way to run E0 a **second** time,
    outside the invocation the record authorizes and outside the withdrawal §5 (R122) applies.

    ``transition_execute`` and ``reconcile_writer_lease_execute`` are the other two surfaces'
    execute paths, each gated by its own separate constant, and both of those constants are
    ``None``. Naming them here is the point of the capability separation: reconciling a lease
    runs no parse, and an E0 instrument is not transition or recovery authority.
    """
    callables = {
        name
        for name in dir(e0)
        if not name.startswith("__") and callable(getattr(e0, name)) and "execute" in name
    }
    assert callables == {"e0_execute", "transition_execute", "reconcile_writer_lease_execute"}

    source = Path(e0.__file__).read_text(encoding="utf-8")
    # The constant is read in exactly the places that gate on it or report it as a fact, and a
    # third reader appearing here would be a second door regardless of what it did.
    assert source.count("M3_3_E0_EXECUTION_AUTHORITY,") == 2
    assert source.count("M3_3_E0_EXECUTION_AUTHORITY is not None") == 1


def test_the_successor_still_executes_to_completion_over_a_released_lease(
    evidence_root: Path, transitioned: Path, config: _Config, activated_e0: None
) -> None:
    """T10: activation and execution semantics are otherwise unchanged.

    The stricter reader sits on the refusal path only, so the machine that a valid released
    lease clears must still run all the way to a complete terminal.
    """
    _write_lease_bytes(evidence_root, _lease_bytes(state="released", released_at_utc=_AT))

    outcome = e0.e0_execute(evidence_root=evidence_root, config=config)

    assert outcome.status == "complete"
    assert outcome.run_namespace == e0.E0_RUN_NAMESPACE
