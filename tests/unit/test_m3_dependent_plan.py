"""Deterministic M3.2B dependent-plan derivation (Decision 045 §4.3, §13).

Every test here is offline, and structurally so: :func:`derive_dependent_plan` accepts no
transport, imports no client, and refuses outright when the invoking configuration is
transport-capable. The suite-wide socket guard in ``tests/conftest.py`` makes that structural
rather than aspirational.

The fixtures are synthetic throughout. **No test resolves the real M3.2B sentinel count**: every
reconciliation set below enumerates a handful of invented entity identities, so what is proved is
the derivation's determinism and its refusal matrix, never the eventual approved count — which
Decision 045 §13 reserves for a real post-M3.2A derivation followed by separate owner approval.

Each refusal is paired with a positive control, so no refusal test can pass against a derivation
that refuses everything.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import date
from pathlib import Path
from typing import Any, Final

import pytest

from disclosure_drift.m3.acquisition import (
    DEPENDENT_RECONCILIATION_SET_VERSION,
    M3_2B_DEPENDENT_ROUTES,
    DependentPlanError,
    derive_dependent_plan,
    prepare_operational_catalog,
    prepare_storage,
    reconstruct_catalog_state,
)
from disclosure_drift.m3.request_plan import (
    RequestPlan,
    build_m3_2a_request_plan,
    canonical_plan_bytes,
    request_plan_from_document,
)
from disclosure_drift.sec.http_client import FetchResult
from disclosure_drift.sec.observation_catalog import ObservationRecorder
from disclosure_drift.sec.source_registry import SOURCES
from disclosure_drift.storage.catalog import CatalogWriter

_CATALOG_RELATIVE: Final = "catalogs/m3_2a_operational.sqlite3"
_DATA_RELATIVE: Final = "runs/m3_2a/data"
_PURPOSE: Final = "acquire an approved Milestone 3.2 metadata object for an offline fixture"

#: Synthetic entity identities. They are ten-digit CIK-shaped strings that address no real filer's
#: document in any test, because nothing here constructs a transport.
_FIXTURE_CIKS: Final[tuple[str, ...]] = ("0000000001", "0000000002", "0000000003")


def _m3_2a_plan() -> RequestPlan:
    """The frozen M3.2A window whose objects a dependent derivation reads."""
    return build_m3_2a_request_plan(
        coverage_start=date(2010, 1, 1),
        coverage_end=date(2010, 6, 30),
        as_of_date=date(2010, 7, 1),
        include_open_quarter=False,
        calendar_year=2010,
        calendar_evidence_entry_count=0,
        already_satisfied_index_keys=frozenset(),
        requests_per_second=4.0,
    )


def _body_for(source_id: str) -> tuple[bytes, str]:
    """A payload shaped to the route's registered expected content kind."""
    expected = SOURCES[source_id].expected_content
    if expected == "zip":
        # A minimal but genuine ZIP: the archive route checks the local-file signature.
        import io
        import zipfile

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("CIK0000000001.json", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            archive.writestr(info, b'{"cik":1}')
        return buffer.getvalue(), "application/zip"
    if expected == "html":
        return b"<html><body>calendar</body></html>", "text/html"
    if expected == "text":
        return b"CIK|Company Name\n1|SYNTHETIC\n", "text/plain"
    return b'{"ok":1}', "application/json"


class _Frozen:
    """One frozen M3.2A window: a real catalog, a real object store, real committed objects."""

    def __init__(self, evidence_root: Path) -> None:
        self.plan = _m3_2a_plan()
        self.preparation = prepare_operational_catalog(
            evidence_root=evidence_root, relative_path=_CATALOG_RELATIVE
        )
        self.storage = prepare_storage(
            evidence_root=evidence_root, data_root_relative=_DATA_RELATIVE
        )
        self.catalog_path = self.preparation.database_path
        self.objects: list[Mapping[str, str]] = []
        self._freeze()

    def _freeze(self) -> None:
        """Commit one verified object per singleton bootstrap route, as a real window would."""
        with CatalogWriter(self.preparation.database_path, self.preparation.lock_directory) as (
            writer
        ):
            recorder = ObservationRecorder(writer=writer, tree=self.storage.tree)
            for source_id in ("sec_company_tickers", "sec_company_tickers_exchange"):
                body, content_type = _body_for(source_id)
                observation = self.storage.snapshot_store.record(
                    FetchResult(
                        outcome="retrieved",
                        source_id=source_id,
                        url=SOURCES[source_id].url(),
                        purpose=_PURPOSE,
                        status=200,
                        body=body,
                        declared_content_type=content_type,
                        final_url=SOURCES[source_id].url(),
                        attempts=1,
                    ),
                    retrieved_at_utc="2026-08-04T00:00:00Z",
                )
                recorder.record(observation)
                self.objects.append(
                    {
                        "source_id": observation.source_id,
                        "request_identity": observation.identity,
                        "content_sha256": str(observation.content_sha256),
                    }
                )

    def reconstruction(self) -> object:
        return reconstruct_catalog_state(catalog_path=self.catalog_path, storage=self.storage)


def _plan_inputs() -> dict[str, object]:
    return {
        "coverage_start": "2010-01-01",
        "coverage_end": "2010-06-30",
        "as_of_date": "2010-07-01",
        "include_open_quarter": False,
        "calendar_year": 2010,
        "calendar_evidence_entry_count": 0,
    }


def _dependent_instances(ciks: Sequence[str] = _FIXTURE_CIKS) -> list[dict[str, object]]:
    """One entity instance per fixture CIK, plus one historical file for the first."""
    instances: list[dict[str, object]] = [
        {
            "source_id": "sec_submissions_entity",
            "instance_key": cik,
            "parameters": {"cik_padded": cik},
        }
        for cik in ciks
    ]
    if ciks:
        historical = f"CIK{ciks[0]}-submissions-001.json"
        instances.append(
            {
                "source_id": "sec_submissions_historical",
                "instance_key": historical,
                "parameters": {"historical_file": historical},
            }
        )
    return instances


def _reconciliation_set(frozen: _Frozen, **overrides: Any) -> dict[str, object]:
    """The reviewed artifact the derivation consumes, with one element overridable per test."""
    document: dict[str, object] = {
        "reconciliation_set_schema_version": DEPENDENT_RECONCILIATION_SET_VERSION,
        "from_window": "M3.2A",
        "plan_inputs": _plan_inputs(),
        "frozen_objects": [dict(entry) for entry in frozen.objects],
        "dependent_instances": _dependent_instances(),
    }
    document.update(overrides)
    return document


def _derive(frozen: _Frozen, document: Mapping[str, object], **overrides: Any) -> object:
    arguments: dict[str, Any] = {
        "from_window": "M3.2A",
        "catalog_path": frozen.catalog_path,
        "storage": frozen.storage,
        "reconciliation_set": document,
        "requests_per_second": 4.0,
        "transport_capable_configuration": False,
    }
    arguments.update(overrides)
    return derive_dependent_plan(**arguments)


@pytest.fixture
def frozen(tmp_path: Path) -> _Frozen:
    return _Frozen(tmp_path)


class TestDeterministicDerivation:
    """The success path, and the properties that make it safe to approve against."""

    def test_it_derives_only_the_two_authorized_dependent_routes(self, frozen: _Frozen) -> None:
        derivation = _derive(frozen, _reconciliation_set(frozen))
        plan = derivation.plan  # type: ignore[attr-defined]

        assert plan.acquisition_window == "M3.2B"
        assert tuple(route.source_id for route in plan.routes) == M3_2B_DEPENDENT_ROUTES
        assert plan.required_index_keys == ()
        assert plan.expected_cache_hits == 0

    def test_the_counts_come_from_the_reviewed_set_and_nowhere_else(self, frozen: _Frozen) -> None:
        derivation = _derive(frozen, _reconciliation_set(frozen))

        assert derivation.entity_instance_count == len(_FIXTURE_CIKS)  # type: ignore[attr-defined]
        assert derivation.historical_instance_count == 1  # type: ignore[attr-defined]
        assert derivation.dependent_instance_count == len(_FIXTURE_CIKS) + 1  # type: ignore[attr-defined]

    def test_a_different_reviewed_set_derives_a_different_count(self, frozen: _Frozen) -> None:
        """Positive control: the count tracks the reviewed evidence rather than being fixed."""
        smaller = _reconciliation_set(
            frozen, dependent_instances=_dependent_instances(_FIXTURE_CIKS[:1])
        )

        derivation = _derive(frozen, smaller)

        assert derivation.entity_instance_count == 1  # type: ignore[attr-defined]

    def test_two_derivations_of_one_set_are_byte_identical(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(frozen)

        first = _derive(frozen, document)
        second = _derive(frozen, document)

        assert first.plan_bytes == second.plan_bytes  # type: ignore[attr-defined]
        assert first.plan.request_plan_sha256 == second.plan.request_plan_sha256  # type: ignore[attr-defined]

    def test_the_derived_document_round_trips_through_the_accepted_reader(
        self, frozen: _Frozen
    ) -> None:
        """A derived plan is a real plan: the accepted canonical reader accepts it unchanged."""
        derivation = _derive(frozen, _reconciliation_set(frozen))

        reread = request_plan_from_document(derivation.plan_bytes)  # type: ignore[attr-defined]

        assert reread == derivation.plan  # type: ignore[attr-defined]
        assert canonical_plan_bytes(reread) == derivation.plan_bytes  # type: ignore[attr-defined]

    def test_the_derived_ceiling_is_the_derived_worst_case_and_approves_nothing(
        self, frozen: _Frozen
    ) -> None:
        derivation = _derive(frozen, _reconciliation_set(frozen))
        plan = derivation.plan  # type: ignore[attr-defined]

        assert plan.hard_request_ceiling == plan.maximum_physical_attempts
        assert plan.hard_request_ceiling == sum(
            route.planned_unique_logical_requests * route.a_reachable for route in plan.routes
        )

    def test_it_verifies_every_declared_frozen_object(self, frozen: _Frozen) -> None:
        derivation = _derive(frozen, _reconciliation_set(frozen))

        assert derivation.verified_object_count == len(frozen.objects)  # type: ignore[attr-defined]
        assert derivation.verified_object_count > 0  # type: ignore[attr-defined]


class TestRefusalMatrix:
    """Every refusal Decision 045 §4.3 and §13 requires, each with a positive control above."""

    def test_a_transport_capable_configuration_refuses(self, frozen: _Frozen) -> None:
        with pytest.raises(DependentPlanError, match="transport-capable"):
            _derive(frozen, _reconciliation_set(frozen), transport_capable_configuration=True)

    def test_a_source_window_other_than_m3_2a_refuses(self, frozen: _Frozen) -> None:
        with pytest.raises(DependentPlanError, match="M3.2A"):
            _derive(frozen, _reconciliation_set(frozen), from_window="M3.2B")

    def test_a_set_of_another_schema_refuses(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(
            frozen, reconciliation_set_schema_version="m3-2b-reconciliation-set/9.9"
        )

        with pytest.raises(DependentPlanError, match="schema"):
            _derive(frozen, document)

    def test_a_set_naming_another_source_window_refuses(self, frozen: _Frozen) -> None:
        with pytest.raises(DependentPlanError, match="source window"):
            _derive(frozen, _reconciliation_set(frozen, from_window="M3.2B"))

    def test_absent_plan_inputs_refuse(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(frozen)
        del document["plan_inputs"]

        with pytest.raises(DependentPlanError, match="plan_inputs"):
            _derive(frozen, document)

    def test_incomplete_plan_inputs_refuse(self, frozen: _Frozen) -> None:
        inputs = _plan_inputs()
        del inputs["calendar_year"]

        with pytest.raises(DependentPlanError, match="plan_inputs"):
            _derive(frozen, _reconciliation_set(frozen, plan_inputs=inputs))

    def test_a_declared_object_the_catalog_does_not_hold_refuses(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(
            frozen,
            frozen_objects=[
                *frozen.objects,
                {
                    "source_id": "sec_sic_code_list",
                    "request_identity": "not-a-committed-identity",
                    "content_sha256": "a" * 64,
                },
            ],
        )

        with pytest.raises(DependentPlanError, match="does not resolve"):
            _derive(frozen, document)

    def test_a_hash_disagreement_between_the_set_and_the_object_refuses(
        self, frozen: _Frozen
    ) -> None:
        """The reviewed set and the frozen object must agree exactly, not approximately."""
        objects = [dict(entry) for entry in frozen.objects]
        objects[0]["content_sha256"] = "b" * 64

        with pytest.raises(DependentPlanError, match="different\n?\\s*digest|different digest"):
            _derive(frozen, _reconciliation_set(frozen, frozen_objects=objects))

    def test_a_satisfying_object_the_set_omits_refuses(self, frozen: _Frozen) -> None:
        """Agreement is checked in both directions, so an omission is a disagreement too."""
        document = _reconciliation_set(frozen, frozen_objects=[dict(frozen.objects[0])])

        with pytest.raises(DependentPlanError, match="not declared"):
            _derive(frozen, document)

    def test_an_empty_frozen_object_set_refuses(self, frozen: _Frozen) -> None:
        with pytest.raises(DependentPlanError, match="frozen_objects"):
            _derive(frozen, _reconciliation_set(frozen, frozen_objects=[]))

    def test_a_bootstrap_route_in_the_dependent_instances_refuses(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(
            frozen,
            dependent_instances=[
                {
                    "source_id": "sec_company_tickers",
                    "instance_key": "bootstrap",
                    "parameters": {},
                }
            ],
        )

        with pytest.raises(DependentPlanError, match="only"):
            _derive(frozen, document)

    def test_a_repeated_dependent_identity_refuses(self, frozen: _Frozen) -> None:
        repeated = _dependent_instances(_FIXTURE_CIKS[:1])
        document = _reconciliation_set(frozen, dependent_instances=[*repeated, repeated[0]])

        with pytest.raises(DependentPlanError, match="repeats identity"):
            _derive(frozen, document)

    def test_an_instance_whose_parameters_cannot_build_a_url_refuses(self, frozen: _Frozen) -> None:
        document = _reconciliation_set(
            frozen,
            dependent_instances=[
                {
                    "source_id": "sec_submissions_entity",
                    "instance_key": "0000000001",
                    "parameters": {"wrong_parameter": "0000000001"},
                }
            ],
        )

        with pytest.raises(DependentPlanError, match="cannot construct its URL"):
            _derive(frozen, document)

    def test_an_empty_dependent_instance_set_refuses(self, frozen: _Frozen) -> None:
        """A derivation never writes out a zero-request dependent plan."""
        with pytest.raises(DependentPlanError, match="dependent_instances"):
            _derive(frozen, _reconciliation_set(frozen, dependent_instances=[]))

    def test_an_absent_catalog_refuses(self, tmp_path: Path, frozen: _Frozen) -> None:
        with pytest.raises(DependentPlanError, match="cannot be read"):
            _derive(
                frozen,
                _reconciliation_set(frozen),
                catalog_path=tmp_path / "absent" / "catalog.sqlite3",
            )

    def test_a_tampered_frozen_object_refuses(self, frozen: _Frozen) -> None:
        """Provenance is re-verified on disk, not trusted from the catalog row."""
        reconstruction = frozen.reconstruction()
        observation = next(
            item
            for item in reconstruction.observations  # type: ignore[attr-defined]
            if item.relative_storage_path
        )
        target = frozen.storage.data_root / str(observation.relative_storage_path)
        target.chmod(0o600)
        target.write_bytes(b'{"tampered":true}')

        with pytest.raises(DependentPlanError):
            _derive(frozen, _reconciliation_set(frozen))


class TestStructuralZeroNetwork:
    """The derivation is incapable of transport construction, not merely refused from it."""

    def test_the_derivation_accepts_no_transport_collaborator(self) -> None:
        import inspect

        signature = inspect.signature(derive_dependent_plan)

        assert "transport" not in signature.parameters
        assert "transport_factory" not in signature.parameters
        assert "client" not in signature.parameters

    def test_no_http_library_is_loaded_by_importing_the_derivation(self) -> None:
        """Runtime proof: reaching the derivation loads no HTTP library.

        Run in a fresh interpreter deliberately. In the full suite ``httpx`` is already resident
        because the accepted transport suite imports it, so an in-process assertion would fail for
        a reason that has nothing to do with this module — and would pass vacuously when this file
        ran alone. A separate process makes the claim mean what it says.
        """
        probe = "\n".join(
            (
                "import sys",
                "from disclosure_drift.m3.acquisition import derive_dependent_plan",
                "assert callable(derive_dependent_plan)",
                "print(sorted(m for m in sys.modules if m.split('.')[0] == 'httpx'))",
            )
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe], capture_output=True, text=True, check=False
        )

        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == "[]"

    def test_the_reviewed_set_is_ordinary_json(self, frozen: _Frozen, tmp_path: Path) -> None:
        """Positive control: the fixture set is a real document an operator could write."""
        path = tmp_path / "reconciliation-set.json"
        path.write_text(json.dumps(_reconciliation_set(frozen)), encoding="utf-8")

        derivation = _derive(frozen, json.loads(path.read_text(encoding="utf-8")))

        assert derivation.dependent_instance_count > 0  # type: ignore[attr-defined]
