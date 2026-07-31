"""M2.3 Stage S6 pure pilot-manifest tests (Decision 021).

Every test here exercises :mod:`disclosure_drift.release.pilot_manifest`, which is
pure: it opens no database, reads no clock, touches no filesystem, consults no
environment variable, invokes no Git, and never reads ``sys.version``. Fixtures are
synthetic dictionaries, never a catalog. The store's own tests cover persistence.

Test obligations discharged here come from Decision 021 section 20: determinism and
permutation invariance, per-component sensitivity, exclusion proofs, column-order
normativity, circularity, the six structural-fingerprint proofs, the five crosswalk
proofs, the thirteen document blocks, document completeness under section 13.3, and
serialization.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.release import pilot_manifest as pm

#: The single failure type every Decision 021 integrity violation raises.
pm_error = GateFailureError

_DECISION_021 = (
    Path(__file__).resolve().parents[2]
    / "Docs"
    / "Decisions"
    / "decision_021_m23_s6_manifest_construction.md"
)


def _hex(seed: str) -> str:
    """Deterministic 64-character lowercase hex digest for a test seed."""
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _structural(
    parser_run_id: str,
    *,
    region: str = "facts",
    state: str = "valid_present",
    observed_type: str = "object",
    member_name: str | None = "us-gaap:Assets",
    record_path: str | None = "$.facts.us-gaap",
) -> dict[str, object]:
    """One ``census_structural_observations`` row, with decoy excluded columns."""
    return {
        "parser_run_id": parser_run_id,
        "region": region,
        "state": state,
        "observed_type": observed_type,
        "member_name": member_name,
        "record_path": record_path,
        "structural_observation_id": _hex(f"{parser_run_id}:{region}:{member_name}"),
        "source_observation_id": _hex("obs"),
        "row_count": 7,
        "count_is_trustworthy": 1,
        "is_genuine_zero": 0,
        "reason_codes_json": "[]",
        "detail": "decoy",
        "raw_excerpt": "decoy",
        "recorded_at_utc": "2026-01-01T00:00:00Z",
    }


def _observation(structural: tuple[dict[str, object], ...] = ()) -> pm.SourceObservation:
    """One cited source observation carrying the six hashed fields."""
    return pm.SourceObservation(
        source_id="sec/company_tickers",
        request_identity="req/company_tickers/1",
        logical_sha256=_hex("logical"),
        parser_version="parser/1.0",
        outcome="stored_new",
        structural_rows=structural,
    )


#: A canonical, unique, correctly ordered authority set including the record Decision 021
#: section 8.4 makes load-bearing for crosswalk items 14 and 58.
_AUTHORITY_RECORDS: tuple[tuple[str, str], ...] = (
    (
        "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
        hashlib.sha256(b"d010").hexdigest(),
    ),
    (
        "Docs/Decisions/decision_021_m23_s6_manifest_construction.md",
        hashlib.sha256(b"d021").hexdigest(),
    ),
)


def _explicit(**overrides: object) -> pm.ExplicitArguments:
    """The six caller-supplied identity values."""
    fields: dict[str, Any] = {
        "dependency_lock_sha256": _hex("lock"),
        "code_commit_identifier": "903f4ccfb9b393de8e9a696af491b42706a510f2",
        "runtime_python_version": "3.12.13",
        "configuration_sha256": _hex("config"),
        "decision_authority_sha256": _hex("authority"),
        "source_plan_sha256": _hex("plan"),
        "decision_authority_records": _AUTHORITY_RECORDS,
    }
    fields.update(overrides)
    return pm.ExplicitArguments(**fields)


def _components(**overrides: str) -> pm.ManifestComponents:
    """Eight distinct component digests."""
    fields = {
        "source_observation_set_sha256": _hex("c1"),
        "candidate_tables_sha256": _hex("c2"),
        "quota_definitions_sha256": _hex("c3"),
        "selector_policy_sha256": _hex("c4"),
        "selected_entities_sha256": _hex("c5"),
        "selected_accessions_sha256": _hex("c6"),
        "reserves_sha256": _hex("c7"),
        "quota_report_sha256": _hex("c8"),
    }
    fields.update(overrides)
    return pm.ManifestComponents(**fields)


def _snapshot(**overrides: object) -> dict[str, object]:
    """A frozen candidate snapshot at the twenty-two hashed fields, plus decoys."""
    snapshot: dict[str, object] = {
        "snapshot_id": _hex("snap"),
        "snapshot_state": "frozen",
        "coverage_start": "2010-01-01",
        "coverage_end": "2026-06-30",
        "as_of_date": "2026-06-30",
        "include_open_quarter": 0,
        "coverage_policy_version": "coverage/1.0",
        "candidate_policy_version": "pilot-candidate/1.0",
        "sic_family_mapping_version": "sic-family-mapping/0.2",
        "evidence_policy_version": "pilot-evidence/1.0",
        "coverage_window_sha256": _hex("cw"),
        "input_observation_set_sha256": _hex("ios"),
        "candidate_entity_table_sha256": _hex("cet"),
        "candidate_accession_table_sha256": _hex("cat"),
        "candidate_registrant_table_sha256": _hex("crt"),
        "candidate_entity_evidence_sha256": _hex("cee"),
        "candidate_accession_evidence_sha256": _hex("cae"),
        "candidate_entity_reasons_sha256": _hex("cer"),
        "candidate_accession_reasons_sha256": _hex("car"),
        "candidate_snapshot_sha256": _hex("css"),
        "entity_count": 24,
        "accession_count": 2,
        # Decoys: excluded normatively by Decision 021 section 8.2.
        "census_run_id": "job-1",
        "invalidated_reason_code": None,
        "created_at_utc": "2026-01-01T00:00:00Z",
        "frozen_at_utc": "2026-01-02T00:00:00Z",
        "invalidated_at_utc": None,
        "detail": "decoy",
    }
    snapshot.update(overrides)
    return snapshot


def _executable_source(module: object) -> str:
    """Module source with every comment and string literal removed.

    The module's own docstring names the things it disclaims -- ``sys.version``,
    ``ReleaseManifest`` -- so a naive substring search over the raw file would match
    the prose that forbids them. Stripping comments and string literals leaves only
    executable code, which is what these prohibitions are actually about.
    """
    import io
    import tokenize

    raw = Path(module.__file__).read_text(encoding="utf-8")  # type: ignore[attr-defined]
    kept: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(raw).readline):
        if token.type in {tokenize.COMMENT, tokenize.STRING}:
            continue
        kept.append(token.string)
    return " ".join(kept)


# ==========================================================================
# Group A: the structural fingerprint -- Decision 021 section 8.1, six proofs
# ==========================================================================


def test_fingerprint_identical_reparse_is_a_digest_no_op() -> None:
    """Proof 1: a second parser run producing the same five-column set changes nothing."""
    one = [_structural("pr-1"), _structural("pr-1", region="cover", member_name=None)]
    two = [*one, _structural("pr-2"), _structural("pr-2", region="cover", member_name=None)]
    assert pm.structural_fingerprint_sha256(one) == pm.structural_fingerprint_sha256(two)


def test_fingerprint_duplicate_identical_row_is_a_digest_no_op() -> None:
    """Proof 2: step 3 reduces each parser run to a set, so a duplicate collapses."""
    base = [_structural("pr-1")]
    assert pm.structural_fingerprint_sha256(base) == pm.structural_fingerprint_sha256(
        [*base, dict(base[0])]
    )


def test_fingerprint_row_and_parser_run_order_are_irrelevant() -> None:
    """Proof 3: permuting rows or parser runs leaves the digest unchanged."""
    rows = [
        _structural("pr-1"),
        _structural("pr-1", region="cover", member_name=None),
        _structural("pr-2"),
        _structural("pr-2", region="cover", member_name=None),
    ]
    assert pm.structural_fingerprint_sha256(rows) == pm.structural_fingerprint_sha256(
        list(reversed(rows))
    )


@pytest.mark.parametrize(
    ("column", "divergent"),
    [
        ("region", "OTHER"),
        ("state", "malformed"),
        ("observed_type", "scalar"),
        ("member_name", "us-gaap:Other"),
        ("record_path", "$.other"),
    ],
)
def test_fingerprint_parser_run_disagreement_fails_closed(column: str, divergent: str) -> None:
    """Proof 4: divergence in each of the five columns independently fails closed.

    A disagreement is never unioned, intersected, averaged, majority-voted, resolved by
    preferring a parser run, or silently discarded.
    """
    rows = [_structural("pr-1"), _structural("pr-2", **{column: divergent})]
    with pytest.raises(GateFailureError, match="disagree"):
        pm.structural_fingerprint_sha256(rows)


@pytest.mark.parametrize(
    ("column", "changed"),
    [
        ("region", "OTHER"),
        ("state", "malformed"),
        ("observed_type", "scalar"),
        ("member_name", "us-gaap:Other"),
        ("record_path", "$.other"),
    ],
)
def test_fingerprint_each_of_the_five_fields_is_load_bearing(column: str, changed: str) -> None:
    """Proof 5: changing any one of the five columns alone changes the fingerprint."""
    base = pm.structural_fingerprint_sha256([_structural("pr-1")])
    assert pm.structural_fingerprint_sha256([_structural("pr-1", **{column: changed})]) != base


def test_fingerprint_tuple_is_the_frozen_five_columns_with_no_three_column_fallback() -> None:
    """Proof 6: the frozen tuple is asserted literally, so a silent reversion fails."""
    assert pm.STRUCTURAL_FINGERPRINT_COLUMNS == (
        "region",
        "state",
        "observed_type",
        "member_name",
        "record_path",
    )
    source = Path(pm.__file__).read_text(encoding="utf-8")
    assert '"region",\n    "state",\n    "member_name",\n)' not in source
    assert source.count("STRUCTURAL_FINGERPRINT_COLUMNS") >= 2


def test_fingerprint_excluded_columns_never_reach_the_digest() -> None:
    """``parser_run_id``, identity, counts, flags, free text, and timestamps are excluded."""
    base = pm.structural_fingerprint_sha256([_structural("pr-1")])
    noisy = _structural("pr-9")
    noisy.update(
        {
            "structural_observation_id": "ZZZ",
            "source_observation_id": "ZZZ",
            "row_count": 999,
            "count_is_trustworthy": 0,
            "is_genuine_zero": 1,
            "reason_codes_json": '["X"]',
            "detail": "changed",
            "raw_excerpt": "changed",
            "recorded_at_utc": "2099-01-01T00:00:00Z",
        }
    )
    assert pm.structural_fingerprint_sha256([noisy]) == base


def test_fingerprint_distinguishes_null_from_empty_string() -> None:
    """``NULL_SENTINEL`` keeps a SQL NULL distinct from the empty string."""
    for column in ("member_name", "record_path"):
        null = pm.structural_fingerprint_sha256([_structural("pr-1", **{column: None})])
        empty = pm.structural_fingerprint_sha256([_structural("pr-1", **{column: ""})])
        assert null != empty


def test_fingerprint_empty_set_is_deterministic_and_distinct() -> None:
    """An observation with no structural rows contributes the empty-set digest."""
    empty = pm.structural_fingerprint_sha256([])
    assert empty == pm.structural_fingerprint_sha256([])
    assert len(empty) == 64
    assert empty != pm.structural_fingerprint_sha256([_structural("pr-1")])


def test_fingerprint_requires_a_partition_key() -> None:
    """A structural row with no ``parser_run_id`` cannot be partitioned."""
    row = _structural("pr-1")
    del row["parser_run_id"]
    with pytest.raises(GateFailureError, match="parser_run_id"):
        pm.structural_fingerprint_sha256([row])


def test_fingerprint_column_order_is_normative() -> None:
    """Reordering the frozen tuple changes the digest, so the order is load-bearing."""
    from disclosure_drift.release.hashing import hash_table, normalize_value

    rows = [
        {
            column: normalize_value(_structural("pr-1").get(column))
            for column in pm.STRUCTURAL_FINGERPRINT_COLUMNS
        }
    ]
    reordered = ("state", "region", "observed_type", "member_name", "record_path")
    assert hash_table(
        "census_structural_observation_shape", reordered, rows
    ).normalized_content_sha256 != pm.structural_fingerprint_sha256([_structural("pr-1")])


# ==========================================================================
# Group B: component digests -- determinism, sensitivity, exclusions
# ==========================================================================


def test_source_observation_set_binds_the_fingerprint_transitively() -> None:
    """A changed structural shape changes the observation-set digest."""
    one = pm.source_observation_set_sha256([_observation((_structural("pr-1"),))])
    two = pm.source_observation_set_sha256([_observation((_structural("pr-1", region="OTHER"),))])
    assert one != two


def test_selected_entities_digest_is_permutation_invariant() -> None:
    """``hash_table`` sorts rendered rows, so retrieval order cannot matter."""
    rows = [
        {column: f"{column}-{index}" for column in pm.SELECTED_ENTITY_COLUMNS} for index in range(3)
    ]
    assert pm.selected_entities_sha256(rows) == pm.selected_entities_sha256(list(reversed(rows)))


@pytest.mark.parametrize("column", pm.SELECTED_ENTITY_COLUMNS)
def test_selected_entities_every_hashed_column_is_sensitive(column: str) -> None:
    """Changing any single hashed column changes exactly this digest."""
    row = {name: f"{name}-value" for name in pm.SELECTED_ENTITY_COLUMNS}
    changed = dict(row, **{column: "changed"})
    assert pm.selected_entities_sha256([row]) != pm.selected_entities_sha256([changed])


def test_selected_entities_ignores_unhashed_columns() -> None:
    """``recorded_at_utc`` and ``detail`` are excluded from every family."""
    row = {name: f"{name}-value" for name in pm.SELECTED_ENTITY_COLUMNS}
    noisy = dict(row, recorded_at_utc="2099-01-01T00:00:00Z", detail="decoy")
    assert pm.selected_entities_sha256([row]) == pm.selected_entities_sha256([noisy])


@pytest.mark.parametrize("column", pm.SELECTED_ACCESSION_COLUMNS)
def test_selected_accessions_every_hashed_column_is_sensitive(column: str) -> None:
    """Changing any single hashed accession column changes the digest."""
    row = {name: f"{name}-value" for name in pm.SELECTED_ACCESSION_COLUMNS}
    changed = dict(row, **{column: "changed"})
    assert pm.selected_accessions_sha256([row]) != pm.selected_accessions_sha256([changed])


def test_quota_report_combines_four_sub_digests() -> None:
    """Each of the four families independently moves ``quota_report_sha256``."""
    base = {
        "quota_results": [dict.fromkeys(pm.QUOTA_RESULT_COLUMNS, "v")],
        "entity_contributions": [dict.fromkeys(pm.ENTITY_CONTRIBUTION_COLUMNS, "v")],
        "accession_contributions": [dict.fromkeys(pm.ACCESSION_CONTRIBUTION_COLUMNS, "v")],
        "quota_members": [dict.fromkeys(pm.QUOTA_MEMBER_COLUMNS, "v")],
    }
    reference = pm.quota_report_sha256(**base)  # type: ignore[arg-type]
    for family in base:
        mutated = {key: list(value) for key, value in base.items()}
        mutated[family] = [dict(mutated[family][0], **{"snapshot_id": "changed"})]
        assert pm.quota_report_sha256(**mutated) != reference  # type: ignore[arg-type]


def test_reserves_combines_four_sub_digests_including_dispositions() -> None:
    """The migration-0012 dispositions are inside ``reserves_sha256``."""
    base = {
        "reserves": [dict.fromkeys(pm.RESERVE_COLUMNS, "v")],
        "reserve_accessions": [dict.fromkeys(pm.RESERVE_ACCESSION_COLUMNS, "v")],
        "reserve_contributions": [dict.fromkeys(pm.RESERVE_CONTRIBUTION_COLUMNS, "v")],
        "reserve_dispositions": [dict.fromkeys(pm.RESERVE_DISPOSITION_COLUMNS, "v")],
    }
    reference = pm.reserves_sha256(**base)  # type: ignore[arg-type]
    mutated = {key: list(value) for key, value in base.items()}
    mutated["reserve_dispositions"] = [
        dict(mutated["reserve_dispositions"][0], reason_code="OTHER")
    ]
    assert pm.reserves_sha256(**mutated) != reference  # type: ignore[arg-type]


def test_candidate_tables_requires_a_frozen_snapshot() -> None:
    """``snapshot_state`` is asserted, then contributed as the fixed literal."""
    with pytest.raises(GateFailureError, match="frozen"):
        pm.candidate_tables_sha256(_snapshot(snapshot_state="building"))


def test_candidate_tables_excludes_census_run_id_and_the_operational_envelope() -> None:
    """Decision 021 section 8.2's normative exclusions hold."""
    reference = pm.candidate_tables_sha256(_snapshot())
    for column, value in (
        ("census_run_id", "other-job"),
        ("invalidated_reason_code", "X"),
        ("created_at_utc", "2099-01-01T00:00:00Z"),
        ("frozen_at_utc", "2099-01-01T00:00:00Z"),
        ("invalidated_at_utc", "2099-01-01T00:00:00Z"),
        ("detail", "changed"),
    ):
        assert pm.candidate_tables_sha256(_snapshot(**{column: value})) == reference


@pytest.mark.parametrize("field", pm.CANDIDATE_TABLE_FIELDS)
def test_candidate_tables_every_hashed_field_is_sensitive(field: str) -> None:
    """Each of the twenty-two fields moves the digest, except the asserted literal."""
    if field == "snapshot_state":
        pytest.skip("snapshot_state is a fixed literal asserted before hashing")
    reference = pm.candidate_tables_sha256(_snapshot())
    assert pm.candidate_tables_sha256(_snapshot(**{field: "changed"})) != reference


def test_quota_definitions_bind_requirements_not_outcomes() -> None:
    """Layer 3 moves on a definition column and not on a solve outcome."""
    row = dict.fromkeys(pm.QUOTA_RESULT_COLUMNS, "v")
    reference = pm.quota_definitions_sha256(quota_policy_version="q/1", quota_results=[row])
    definition_changed = dict(row, required_count="99")
    outcome_changed = dict(row, achieved_count="99", quota_result="fail")
    assert (
        pm.quota_definitions_sha256(quota_policy_version="q/1", quota_results=[definition_changed])
        != reference
    )
    assert (
        pm.quota_definitions_sha256(quota_policy_version="q/1", quota_results=[outcome_changed])
        == reference
    )


def test_selector_policy_binds_exactly_eleven_fields() -> None:
    """Each of the eleven inputs independently moves ``selector_policy_sha256``."""
    policy_rows = [{"policy_key": key, "policy_version": "v"} for key in pm.CONSUMED_POLICY_KEYS]
    chain = [{"version": 1, "name": "initial", "checksum_sha256": _hex("m1")}]
    kwargs: dict[str, Any] = {
        "policy_versions": policy_rows,
        "migration_chain": chain,
        "selection_input_schema_version": "pilot-joint-selection-input/1.0",
        "manifest_schema_version": "pilot-manifest/1.0",
        "explicit": _explicit(),
    }
    reference = pm.selector_policy_sha256(**kwargs)

    assert (
        pm.selector_policy_sha256(**{**kwargs, "selection_input_schema_version": "x"}) != reference
    )
    assert pm.selector_policy_sha256(**{**kwargs, "manifest_schema_version": "x"}) != reference
    assert (
        pm.selector_policy_sha256(
            **{
                **kwargs,
                "policy_versions": [dict(policy_rows[0], policy_version="x"), *policy_rows[1:]],
            }
        )
        != reference
    )
    assert (
        pm.selector_policy_sha256(**{**kwargs, "migration_chain": [dict(chain[0], name="x")]})
        != reference
    )
    for field in (
        "dependency_lock_sha256",
        "code_commit_identifier",
        "runtime_python_version",
        "configuration_sha256",
        "decision_authority_sha256",
        "source_plan_sha256",
    ):
        assert (
            pm.selector_policy_sha256(**{**kwargs, "explicit": _explicit(**{field: "changed"})})
            != reference
        )


def test_selector_policy_excludes_the_migration_timestamp() -> None:
    """``applied_at_utc`` is excluded from ``migration_chain_sha256``."""
    policy_rows = [{"policy_key": key, "policy_version": "v"} for key in pm.CONSUMED_POLICY_KEYS]
    kwargs: dict[str, Any] = {
        "policy_versions": policy_rows,
        "selection_input_schema_version": "pilot-joint-selection-input/1.0",
        "manifest_schema_version": "pilot-manifest/1.0",
        "explicit": _explicit(),
    }
    chain = {"version": 1, "name": "initial", "checksum_sha256": _hex("m1")}
    assert pm.selector_policy_sha256(
        migration_chain=[chain], **kwargs
    ) == pm.selector_policy_sha256(
        migration_chain=[dict(chain, applied_at_utc="2099-01-01T00:00:00Z")], **kwargs
    )


def test_selector_policy_excludes_the_policy_decision_record_pointer() -> None:
    """``reference_policy_versions.decision_record`` is a navigation pointer, not a value."""
    policy_rows = [{"policy_key": key, "policy_version": "v"} for key in pm.CONSUMED_POLICY_KEYS]
    noisy = [
        dict(row, decision_record="Docs/whatever.md", recorded_at_utc="x") for row in policy_rows
    ]
    kwargs: dict[str, Any] = {
        "migration_chain": [{"version": 1, "name": "initial", "checksum_sha256": _hex("m1")}],
        "selection_input_schema_version": "pilot-joint-selection-input/1.0",
        "manifest_schema_version": "pilot-manifest/1.0",
        "explicit": _explicit(),
    }
    assert pm.selector_policy_sha256(policy_versions=policy_rows, **kwargs) == (
        pm.selector_policy_sha256(policy_versions=noisy, **kwargs)
    )


@pytest.mark.parametrize(
    "field",
    [
        "dependency_lock_sha256",
        "code_commit_identifier",
        "runtime_python_version",
        "configuration_sha256",
        "decision_authority_sha256",
        "source_plan_sha256",
    ],
)
@pytest.mark.parametrize("bad", ["", "   "])
def test_explicit_arguments_fail_closed_when_missing_or_malformed(field: str, bad: str) -> None:
    """A missing or malformed explicit argument is a GateFailureError."""
    with pytest.raises(GateFailureError, match=field):
        _explicit(**{field: bad})


def test_leakage_attestation_is_the_frozen_literal() -> None:
    """The literal commits which attestation was made (section 8.4.1)."""
    assert pm.LEAKAGE_ATTESTATION == "no-outcome-no-filing-text-no-companyfacts/1.0"


# ==========================================================================
# Group C: result digest, root, manifest identity, circularity
# ==========================================================================


def _result(**overrides: Any) -> str:
    """The terminal result digest over a complete fourteen-field preimage."""
    fields: dict[str, Any] = {
        "manifest_hash_policy_version": "pilot-manifest/1.0",
        "selection_run_id": _hex("run"),
        "snapshot_id": _hex("snap"),
        "selection_input_sha256": _hex("input"),
        "selection_input_schema_version": "pilot-joint-selection-input/1.0",
        "run_state": "feasible",
        "selected_entity_count": 24,
        "selected_accession_count": 2,
        "expanded_node_count": 42,
        "node_limit_exhausted": 0,
        "components": _components(),
    }
    fields.update(overrides)
    return pm.selection_result_sha256(**fields)


def test_selection_result_requires_a_feasible_run() -> None:
    """A non-feasible run has no result digest at all (section 6.2)."""
    for state in ("planned", "running", "failed", "infeasible", "infeasible_or_unproven"):
        with pytest.raises(GateFailureError, match="feasible"):
            _result(run_state=state)


@pytest.mark.parametrize(
    "field",
    [
        "manifest_hash_policy_version",
        "selection_run_id",
        "snapshot_id",
        "selection_input_sha256",
        "selection_input_schema_version",
        "selected_entity_count",
        "selected_accession_count",
        "expanded_node_count",
        "node_limit_exhausted",
    ],
)
def test_selection_result_every_scalar_field_is_sensitive(field: str) -> None:
    """Each named scalar in the fourteen-field preimage moves the result digest."""
    assert _result(**{field: "changed"}) != _result()


@pytest.mark.parametrize(
    "component",
    [
        "selected_entities_sha256",
        "selected_accessions_sha256",
        "quota_report_sha256",
        "reserves_sha256",
    ],
)
def test_selection_result_binds_the_four_terminal_components(component: str) -> None:
    """The four terminal component digests are inputs to the result digest."""
    assert _result(components=_components(**{component: _hex("changed")})) != _result()


@pytest.mark.parametrize(
    "component",
    [
        "source_observation_set_sha256",
        "candidate_tables_sha256",
        "quota_definitions_sha256",
        "selector_policy_sha256",
    ],
)
def test_selection_result_excludes_the_non_terminal_components(component: str) -> None:
    """The other four components are root inputs only, not result inputs."""
    assert _result(components=_components(**{component: _hex("changed")})) == _result()


def _root(**overrides: Any) -> str:
    """The root over a complete twelve-field preimage."""
    fields: dict[str, Any] = {
        "manifest_schema_version": "pilot-manifest/1.0",
        "selection_run_id": _hex("run"),
        "snapshot_id": _hex("snap"),
        "selection_result": _hex("result"),
        "components": _components(),
    }
    fields.update(overrides)
    return pm.root_manifest_sha256(**fields)


@pytest.mark.parametrize(
    "field", ["manifest_schema_version", "selection_run_id", "snapshot_id", "selection_result"]
)
def test_root_every_scalar_field_is_sensitive(field: str) -> None:
    """Each named scalar in the twelve-field root preimage moves the root."""
    assert _root(**{field: "changed"}) != _root()


@pytest.mark.parametrize(
    "component",
    [
        "source_observation_set_sha256",
        "candidate_tables_sha256",
        "quota_definitions_sha256",
        "selector_policy_sha256",
        "selected_entities_sha256",
        "selected_accessions_sha256",
        "reserves_sha256",
        "quota_report_sha256",
    ],
)
def test_root_binds_all_eight_components(component: str) -> None:
    """Every one of the eight components is a root input."""
    assert _root(components=_components(**{component: _hex("changed")})) != _root()


def test_manifest_identifier_is_downstream_of_the_root() -> None:
    """``manifest_id`` derives from the root and never the reverse (section 9.1)."""
    root = _root()
    identifier = pm.manifest_identifier(
        root_sha256=root, ordinal_version=1, supersedes_manifest_id=None
    )
    assert len(identifier) == 64
    assert identifier != root
    assert (
        pm.manifest_identifier(
            root_sha256=_hex("other"), ordinal_version=1, supersedes_manifest_id=None
        )
        != identifier
    )
    assert (
        pm.manifest_identifier(root_sha256=root, ordinal_version=2, supersedes_manifest_id=None)
        != identifier
    )
    assert (
        pm.manifest_identifier(
            root_sha256=root, ordinal_version=1, supersedes_manifest_id=_hex("pred")
        )
        != identifier
    )


def test_manifest_identifier_distinguishes_null_predecessor_from_empty_string() -> None:
    """``NULL_SENTINEL`` keeps an absent predecessor distinct from an empty one."""
    root = _root()
    assert pm.manifest_identifier(
        root_sha256=root, ordinal_version=1, supersedes_manifest_id=None
    ) != pm.manifest_identifier(root_sha256=root, ordinal_version=1, supersedes_manifest_id="")


def test_ordinal_version_and_supersedes_are_excluded_from_the_root() -> None:
    """Two ordinal versions of identical content share a root (section 10.1)."""
    root = _root()
    first = pm.manifest_identifier(root_sha256=root, ordinal_version=1, supersedes_manifest_id=None)
    second = pm.manifest_identifier(
        root_sha256=root, ordinal_version=2, supersedes_manifest_id=first
    )
    assert first != second


def test_no_digest_hashes_itself_and_the_graph_is_acyclic() -> None:
    """Circularity: the result digest is provably absent from its own preimage."""
    source = Path(pm.__file__).read_text(encoding="utf-8")
    result_body = source.split("def selection_result_sha256(")[1].split("\ndef ")[0]
    assert '"selection_result_sha256": ' not in result_body
    root_body = source.split("def root_manifest_sha256(")[1].split("\ndef ")[0]
    assert '"root_manifest_sha256": ' not in root_body
    assert '"manifest_id": ' not in root_body
    # No component digest reads either governed table as a table.
    executable = _executable_source(pm)
    assert "pilot_manifest_versions" not in executable
    assert "pilot_projection_recovery_events" not in executable
    assert "pilot_selection_runs" not in executable


def test_the_four_terminal_components_form_a_diamond_not_a_cycle() -> None:
    """Both consumers are downstream of the four producers; neither reads the other."""
    changed = _components(selected_entities_sha256=_hex("changed"))
    assert _result(components=changed) != _result()
    assert _root(components=changed) != _root()


def test_manifest_filename_is_content_derived_from_the_root() -> None:
    """The filename is derived from the root (section 13.5)."""
    root = _root()
    assert pm.manifest_filename(root) == f"pilot_manifest_{root}.json"


# ==========================================================================
# Group D: the section 10 crosswalk -- Decision 021 section 13.2.1, five proofs
# ==========================================================================


def test_crosswalk_table_is_asserted_literally() -> None:
    """Proof 1: 81 rows, contiguous, unique, each in exactly one of four categories."""
    numbers = [item.number for item in pm.CROSSWALK]
    assert numbers == list(range(1, 82))
    assert len({item.number for item in pm.CROSSWALK}) == 81
    assert {item.classification for item in pm.CROSSWALK} == {"D", "T", "X", "S9"}
    for item in pm.CROSSWALK:
        assert item.requirement.strip()
        assert item.group.strip()


def test_crosswalk_frozen_counts_reproduce_mechanically() -> None:
    """Proof 2: the six frozen counts, with unclassified provably zero."""
    assert pm.crosswalk_totals() == {
        "total_section_10_items": 81,
        "directly_included": 42,
        "transitively_included": 30,
        "operationally_excluded": 8,
        "deferred_to_s9": 1,
        "deferred_to_s10": 0,
        "unclassified": 0,
    }


def test_crosswalk_matches_the_accepted_decision_record() -> None:
    """The module's crosswalk is the record's table, row for row."""
    text = _DECISION_021.read_text(encoding="utf-8")
    segment = text.split("### 13.2.1")[1].split("### 13.2.2")[0]
    rows = re.findall(
        r"^\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*([^|]*?)\s*\|\s*(.+?)\s*\|\s*\*\*(D|T|X|S9)\*\*\s*\|",
        segment,
        re.MULTILINE,
    )
    assert len(rows) == 81
    recorded = {int(number): classification for number, _, _, _, classification in rows}
    assert {item.number: item.classification for item in pm.CROSSWALK} == recorded


def test_crosswalk_direct_and_transitive_items_name_a_document_block() -> None:
    """Proof 3a: every D and T item lands in at least one of the thirteen blocks."""
    for item in pm.CROSSWALK:
        if item.classification in {"D", "T"}:
            assert item.blocks, f"item {item.number} has no block"
            assert all(1 <= block <= 13 for block in item.blocks)


def test_crosswalk_excluded_and_deferred_items_carry_no_block() -> None:
    """Proof 3b: an X item is not serialized, and the single S9 item is deferred."""
    for item in pm.CROSSWALK:
        if item.classification in {"X", "S9"}:
            assert item.blocks == ()


def test_crosswalk_single_s9_deferral_is_command_invocation() -> None:
    """Proof 5: the only item deferred as an item is command invocation (item 80)."""
    deferred = [item for item in pm.CROSSWALK if item.classification == "S9"]
    assert len(deferred) == 1
    assert deferred[0].number == 80
    assert "command invocation" in deferred[0].requirement


def test_crosswalk_group_sizes_reproduce_the_seven_compound_splits() -> None:
    """74 original bullets producing 81 atomic requirements (74 + 7 = 81)."""
    sizes: dict[str, int] = {}
    for item in pm.CROSSWALK:
        sizes[item.group] = sizes.get(item.group, 0) + 1
    assert sizes == {
        "Manifest identity": 16,
        "Source provenance": 14,
        "Entity records": 16,
        "Accession records": 18,
        "Quota report": 8,
        "Reconstruction fields": 9,
    }
    assert sum(sizes.values()) == 81


# ==========================================================================
# Group E: the document -- thirteen blocks, completeness, serialization
# ==========================================================================


def _entity_row(order: int = 1, cik: int = 7) -> dict[str, object]:
    """One selected-entity row at the frozen section 7.1 columns."""
    row: dict[str, object] = {name: f"{name}-v" for name in pm.SELECTED_ENTITY_COLUMNS}
    row["cik_numeric"] = cik
    row["selected_order"] = order
    return row


def _accession_row(order: int = 1, plain: str = "0000000001-24-000001") -> dict[str, object]:
    """One selected-accession row at the frozen section 7.2 columns."""
    row: dict[str, object] = {name: f"{name}-v" for name in pm.SELECTED_ACCESSION_COLUMNS}
    row["accession_plain"] = plain
    row["selected_order"] = order
    return row


def _entity_sources(**overrides: object) -> pm.EntityRecordSources:
    """Block-8 record sources with every crosswalk-required family populated."""
    fields: dict[str, Any] = {
        "candidate": {name: f"{name}-v" for name in pm.ENTITY_CANDIDATE_FIELDS},
        "name_change": {name: f"{name}-v" for name in pm.NAME_CHANGE_FLAG_FIELDS},
        "evidence": ({name: f"{name}-v" for name in pm.ENTITY_EVIDENCE_RECORD_COLUMNS},),
        "reasons": ({name: f"{name}-v" for name in pm.CANDIDATE_REASON_RECORD_COLUMNS},),
    }
    fields.update(overrides)
    return pm.EntityRecordSources(**fields)


def _accession_sources(**overrides: object) -> pm.AccessionRecordSources:
    """Block-9 record sources with every crosswalk-required family populated."""
    fields: dict[str, Any] = {
        "candidate": {name: f"{name}-v" for name in pm.ACCESSION_CANDIDATE_FIELDS},
        "derived": {name: f"{name}-v" for name in pm.ACCESSION_DERIVED_FIELDS},
        "registrants": ({name: f"{name}-v" for name in pm.ACCESSION_REGISTRANT_RECORD_COLUMNS},),
    }
    fields.update(overrides)
    return pm.AccessionRecordSources(**fields)


def _reserve_package(target: int) -> dict[str, Any]:
    """One rank-1 reserve package for ``target`` (Decision 020 §7.1, migration 0012)."""
    return {
        **{name: f"{name}-v" for name in pm.RESERVE_COLUMNS},
        "target_cik_numeric": target,
        "reserve_rank": pm.ACCEPTED_RESERVE_RANK,
    }


def _reserve_disposition(target: int) -> dict[str, Any]:
    """One ``REVIEW_PILOT_NO_COMPATIBLE_RESERVE`` disposition for ``target``."""
    return {
        **{name: f"{name}-v" for name in pm.RESERVE_DISPOSITION_COLUMNS},
        "cik_numeric": target,
        "reason_scope": pm.RESERVE_DISPOSITION_SCOPE,
        "reason_code": pm.NO_COMPATIBLE_RESERVE_REASON_CODE,
    }


def _sources(**overrides: object) -> pm.ManifestSources:
    """A complete, minimal set of persisted row families.

    The reserve family is derived from whichever selected entities the caller supplies, so
    every fixture satisfies Decision 020 §7.1's totality — each selected target covered by
    exactly one rank-1 package or exactly one no-compatible-reserve disposition, never both
    and never neither. The first target takes a package and the rest take dispositions, so a
    multi-entity fixture is a **mixed** run by construction. Either family may still be
    overridden explicitly, which is how the adversarial coverage cases below are built.
    """
    entities: Any = overrides.get("selected_entities", (_entity_row(),))
    # Sorted, so which target takes the package never depends on the caller's row order --
    # the persisted reserve family does not, and permutation invariance must stay provable.
    targets = sorted(row["cik_numeric"] for row in entities)
    fields: dict[str, Any] = {
        "snapshot": _snapshot(),
        "observations": (_observation((_structural("pr-1"),)),),
        "policy_versions": tuple(
            {"policy_key": key, "policy_version": "v"} for key in pm.CONSUMED_POLICY_KEYS
        ),
        "migration_chain": ({"version": 1, "name": "initial", "checksum_sha256": _hex("m1")},),
        "selected_entities": (_entity_row(),),
        "selected_accessions": (_accession_row(),),
        "quota_results": ({name: f"{name}-v" for name in pm.QUOTA_RESULT_COLUMNS},),
        "entity_contributions": ({name: f"{name}-v" for name in pm.ENTITY_CONTRIBUTION_COLUMNS},),
        "accession_contributions": (
            {name: f"{name}-v" for name in pm.ACCESSION_CONTRIBUTION_COLUMNS},
        ),
        "quota_members": ({name: f"{name}-v" for name in pm.QUOTA_MEMBER_COLUMNS},),
        "reserves": tuple(_reserve_package(target) for target in targets[:1]),
        "reserve_accessions": ({name: f"{name}-v" for name in pm.RESERVE_ACCESSION_COLUMNS},),
        "reserve_contributions": ({name: f"{name}-v" for name in pm.RESERVE_CONTRIBUTION_COLUMNS},),
        "reserve_dispositions": tuple(_reserve_disposition(target) for target in targets[1:]),
        "reconstruction": pm.ReconstructionFacts(
            selection_seed="pilot-seed/1",
            selection_input_sha256=_hex("input"),
            selection_input_schema_version="pilot-joint-selection-input/1.0",
            declared_candidate_entity_count=24,
            declared_candidate_accession_count=38,
            selected_table_row_counts={
                "pilot_selected_entities": 24,
                "pilot_selected_accessions": 38,
            },
            exclusion_counts_by_reason_code={"REVIEW_PILOT_NO_COMPATIBLE_RESERVE": 3},
            unresolved_quota_count=0,
            provisional_quota_count=1,
        ),
        "entity_record_sources": {7: _entity_sources()},
        "accession_record_sources": {"0000000001-24-000001": _accession_sources()},
        "as_of_timezone": "America/New_York",
    }
    fields.update(overrides)
    return pm.ManifestSources(**fields)


def _document(**overrides: object) -> dict[str, object]:
    """A rendered document over the fixture sources."""
    root = _root()
    identity = pm.ManifestIdentity(
        manifest_id=pm.manifest_identifier(
            root_sha256=root, ordinal_version=1, supersedes_manifest_id=None
        ),
        manifest_schema_version="pilot-manifest/1.0",
        selection_run_id=_hex("run"),
        snapshot_id=_hex("snap"),
        ordinal_version=1,
        supersedes_manifest_id=None,
    )
    fields: dict[str, Any] = {
        "identity": identity,
        "components": _components(),
        "root_sha256": root,
        "selection_result": _hex("result"),
        "explicit": _explicit(),
        "sources": _sources(),
        "quota_policy_version": "m23-pilot-quota-policy-v1",
    }
    fields.update(overrides)
    return pm.build_manifest_document(**fields)


def test_document_carries_all_thirteen_blocks_populated() -> None:
    """All thirteen section 13.2 blocks are present and populated over fixtures."""
    document = _document()
    assert set(document) == set(pm.DOCUMENT_BLOCKS)
    assert sorted(pm.DOCUMENT_BLOCKS.values()) == list(range(1, 14))
    for name in pm.DOCUMENT_BLOCKS:
        assert document[name], f"block {name} is empty"


def test_document_manifest_state_is_the_fixed_proposed_literal() -> None:
    """Stage S6 builds only the proposed-manifest schema (section 13.2.2)."""
    identity = _document()["manifest_identity"]
    assert isinstance(identity, dict)
    assert identity["manifest_state"] == "proposed"
    assert pm.MANIFEST_STATE_LITERAL == "proposed"


def test_document_supersedes_is_the_canonical_null_at_s6() -> None:
    """S6 is forbidden to populate ``supersedes_manifest_id`` at all (section 11.1)."""
    identity = _document()["manifest_identity"]
    assert isinstance(identity, dict)
    assert identity["supersedes_manifest_id"] is None


def test_document_every_leaf_is_bound_by_a_digest() -> None:
    """Section 13.3: no substantive serialized field may be unbound."""
    bindings = pm.document_leaf_bindings(_document())
    assert bindings
    for path, binding in bindings.items():
        assert binding.digests, f"leaf {path} has no binding digest"
        assert 1 <= binding.block <= 13


def test_document_binding_is_field_level_not_block_level() -> None:
    """An invented leaf inside a valid block is refused, not inherited into a binding.

    This is the completeness rule's whole point: under a block-level table any field added
    inside an existing block would silently acquire that block's digests.
    """
    document = _document()
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    assert isinstance(entities[0], dict)
    entities[0]["invented_unbound_field"] = "leak"
    with pytest.raises(pm_error, match="no accepted binding"):
        pm.document_leaf_bindings(document)


def test_document_binding_refuses_an_unknown_block() -> None:
    """A whole block the accepted table does not name is refused as well."""
    document = _document()
    document["invented_block"] = {"field": "value"}
    with pytest.raises(pm_error, match="no accepted binding"):
        pm.document_leaf_bindings(document)


def test_document_omitting_a_required_item_fails_closed() -> None:
    """Removing a required D/T value fails the crosswalk coverage proof."""
    document = _document()
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    assert isinstance(entities[0], dict)
    del entities[0]["cik_padded"]
    # Per-record completeness catches this even though twenty-three sibling records still
    # carry the field, so item 31 would otherwise still look "covered".
    with pytest.raises(pm_error, match="missing the required document fields"):
        pm.verify_document_crosswalk_coverage(document)


def test_document_omitting_a_whole_required_family_fails_closed() -> None:
    """Dropping a value from every record fails the item-level coverage proof too."""
    document = _document()
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    for record in entities:
        assert isinstance(record, dict)
        del record["entity_hash_sha256"]
    with pytest.raises(pm_error, match="missing the required document fields"):
        pm.verify_document_crosswalk_coverage(document)


def _required_record_paths() -> tuple[tuple[str, str], ...]:
    """Every ``(container prefix, record name)`` the accepted binding table declares.

    Derived from the binding table rather than listed, so a nested record or array added
    to the document later is covered by these proofs without editing them.
    """
    found: set[tuple[str, str]] = set()
    for path in pm.DOCUMENT_FIELD_BINDINGS:
        segments = path.split(".")
        for index in range(len(segments) - 1):
            prefix = ".".join(segments[:index])
            if prefix in pm._OPEN_KEYED_PATHS:
                continue
            found.add((prefix, segments[index].removesuffix("[]")))
    return tuple(sorted(found))


def _drop_record(node: object, prefix: str, name: str) -> None:
    """Remove ``name`` from every container instance living at ``prefix``."""
    if prefix == "":
        assert isinstance(node, dict)
        del node[name]
        return
    head, _, rest = prefix.partition(".")
    key = head.removesuffix("[]")
    if isinstance(node, list):
        for element in node:
            _drop_record(element, prefix, name)
        return
    assert isinstance(node, dict)
    target = node[key]
    if head.endswith("[]"):
        assert isinstance(target, list)
        for element in target:
            _drop_record(element, rest, name)
        return
    _drop_record(target, rest, name)


def test_every_required_record_is_declared_by_the_binding_table() -> None:
    """The record inventory the proof below runs over is non-empty and complete."""
    required = _required_record_paths()
    assert len(required) >= 20
    # The blocks, the nested per-record families, and the block-13 count maps.
    assert ("", "selected_entities") in required
    assert ("", "hash_layers") in required
    assert ("selected_entities[]", "classification_evidence") in required
    assert ("selected_entities[]", "candidate_reasons") in required
    assert ("selected_accessions[]", "registrants") in required
    assert ("active_authority", "decision_records") in required
    assert ("historical_reconstruction", "candidate_table_row_counts") in required


@pytest.mark.parametrize(("prefix", "name"), _required_record_paths())
def test_document_removing_a_whole_required_record_fails_closed(prefix: str, name: str) -> None:
    """A dropped record family is refused, never covered by the digest that binds it.

    Section 13.2.1 rules that a digest alone never discharges a requirement: where
    section 10 asks for full records, provenance entries, authority records, or
    reconstruction content, category T requires the values themselves. Item-level
    coverage cannot enforce that on its own, because most items are also discharged by a
    scalar elsewhere -- dropping ``active_authority.decision_records`` leaves item 11
    "covered" by ``decision_authority_sha256``, which is exactly the substitution section
    13.2.1 forbids. Every declared record is therefore required by name.
    """
    document = _document()
    _drop_record(document, prefix, name)
    with pytest.raises(pm_error, match="missing the required document records"):
        pm.verify_document_crosswalk_coverage(document)


def test_document_removing_a_record_from_one_instance_only_fails_closed() -> None:
    """Twenty-three intact sibling records do not excuse the twenty-fourth."""
    rows = tuple(_entity_row(order=order, cik=order) for order in (1, 2, 3))
    document = _document(
        sources=_sources(
            selected_entities=rows,
            entity_record_sources={order: _entity_sources() for order in (1, 2, 3)},
        )
    )
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    assert isinstance(entities[1], dict)
    del entities[1]["classification_evidence"]
    with pytest.raises(pm_error, match="missing the required document records"):
        pm.verify_document_crosswalk_coverage(document)


def test_document_replacing_a_required_record_with_a_scalar_fails_closed() -> None:
    """A record replaced by a bare value is not a record, and is refused as neither."""
    document = _document()
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    assert isinstance(entities[0], dict)
    entities[0]["candidate_reasons"] = "none"
    with pytest.raises(pm_error):
        pm.verify_document_crosswalk_coverage(document)


def test_an_intact_document_carries_every_required_record() -> None:
    """The proofs above are live: the real document satisfies all of them."""
    document = _document()
    for prefix, name in _required_record_paths():
        probe = _document()
        _drop_record(probe, prefix, name)
        assert probe != document, f"{prefix}.{name} was never present to begin with"
    assert pm.verify_document_crosswalk_coverage(document)


# ==========================================================================
# Decision 022 — crosswalk item 46 reserve-rank applicability
# ==========================================================================


def _coverage_document(*, packages: tuple[int, ...], dispositions: tuple[int, ...]) -> Any:
    """A document over two selected targets with an explicitly chosen reserve family."""
    rows = (_entity_row(order=1, cik=7), _entity_row(order=2, cik=8))
    return _document(
        sources=_sources(
            selected_entities=rows,
            entity_record_sources={7: _entity_sources(), 8: _entity_sources()},
            reserves=tuple(_reserve_package(target) for target in packages),
            reserve_dispositions=tuple(_reserve_disposition(target) for target in dispositions),
        )
    )


def test_item_46_constants_track_the_accepted_sources() -> None:
    """The rank and reason code are read from the accepted authorities, never restated.

    A literal copy would drift silently the day either accepted value moved, so both are
    pinned against their owners here: migration ``0012`` and the accepted reserve selector
    for the rank, and the accepted reason registry for the code.
    """
    from disclosure_drift.reasons import REASON_CODES
    from disclosure_drift.sec.reserve_selector import RESERVE_RANK

    assert pm.ACCEPTED_RESERVE_RANK == RESERVE_RANK == 1
    assert pm.NO_COMPATIBLE_RESERVE_REASON_CODE == "REVIEW_PILOT_NO_COMPATIBLE_RESERVE"
    assert pm.NO_COMPATIBLE_RESERVE_REASON_CODE in REASON_CODES
    assert REASON_CODES[pm.NO_COMPATIBLE_RESERVE_REASON_CODE].blocks_release is False
    assert pm.RESERVE_DISPOSITION_SCOPE == "reserve"
    migration = (
        Path(__file__).resolve().parents[2]
        / "src/disclosure_drift/storage/migrations/0012_m23_selection_entity_reasons.sql"
    ).read_text(encoding="utf-8")
    assert "reserve_rank <> 1" in migration
    assert f"reason_code = '{pm.NO_COMPATIBLE_RESERVE_REASON_CODE}'" in migration


def test_item_46_is_unchanged_in_the_crosswalk() -> None:
    """Decision 022 changes no crosswalk row: item 46 stays D, block 12 (§§1, 4)."""
    item = next(entry for entry in pm.CROSSWALK if entry.number == 46)
    assert (item.number, item.requirement, item.classification, item.blocks) == (
        46,
        "reserve rank",
        "D",
        (12,),
    )
    item70 = next(entry for entry in pm.CROSSWALK if entry.number == 70)
    assert (item70.number, item70.requirement, item70.classification, item70.blocks) == (
        70,
        "reserve coverage",
        "D",
        (12,),
    )
    assert pm.crosswalk_totals() == {
        "total_section_10_items": 81,
        "directly_included": 42,
        "transitively_included": 30,
        "operationally_excluded": 8,
        "deferred_to_s9": 1,
        "deferred_to_s10": 0,
        "unclassified": 0,
    }


def test_item_46_not_applicable_set_is_exactly_forty_six() -> None:
    """Non-applicability is narrow: it reaches item 46 and nothing else (Decision 022 §7)."""
    assert frozenset({46}) == pm.NOT_APPLICABLE_WITHOUT_RESERVE_PACKAGE


def test_zero_package_document_discharges_item_46_by_non_applicability() -> None:
    """A run with no compatible reserve for any target verifies (Decision 022 §2.3–2.4)."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    covered = pm.verify_document_crosswalk_coverage(document)
    assert 46 not in covered, "item 46 is not applicable with zero packages"
    assert 70 in covered, "item 70 is still discharged, by the dispositions"
    coverage = pm.reserve_coverage(document)
    assert coverage.targets_with_package == frozenset()
    assert coverage.targets_with_disposition == frozenset({7, 8})
    rendered = pm.render_canonical_json(document)
    assert document["reserves"]["packages"] == [], "the package family is present and empty"
    assert "reserve_rank" not in rendered, "no synthetic rank is ever serialized"
    for invented in ('"N/A"', '"reserve_rank": 0', '"reserve_rank": null'):
        assert invented not in rendered


def test_mixed_document_requires_and_discharges_item_46() -> None:
    """With even one package, item 46 is required as usual (Decision 022 §2.7)."""
    document = _coverage_document(packages=(7,), dispositions=(8,))
    covered = pm.verify_document_crosswalk_coverage(document)
    assert 46 in covered and 70 in covered
    coverage = pm.reserve_coverage(document)
    assert coverage.targets_with_package == frozenset({7})
    assert coverage.targets_with_disposition == frozenset({8})


def test_item_46_is_not_globally_optional() -> None:
    """Removing the rank from a package that exists still fails, package or no package."""
    document = _coverage_document(packages=(7,), dispositions=(8,))
    packages = document["reserves"]["packages"]
    del packages[0]["reserve_rank"]
    with pytest.raises(pm_error, match="missing the required document fields"):
        pm.verify_document_crosswalk_coverage(document)


@pytest.mark.parametrize("rank", [0, 2, -1, None, "1", 1.0, True])
def test_item_46_refuses_a_rank_that_is_not_the_accepted_rank(rank: object) -> None:
    """Migration 0012 admits only rank 1; an invented rank is refused, never coerced."""
    document = _coverage_document(packages=(7,), dispositions=(8,))
    document["reserves"]["packages"][0]["reserve_rank"] = rank
    with pytest.raises(pm_error, match="admits only rank 1"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_target_with_both() -> None:
    """Decision 020 §7.1 makes a package and a disposition mutually exclusive."""
    document = _coverage_document(packages=(7,), dispositions=(7, 8))
    with pytest.raises(pm_error, match="both a reserve package"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_target_with_neither() -> None:
    """A selected target with no package and no disposition fails closed."""
    document = _coverage_document(packages=(7,), dispositions=())
    with pytest.raises(pm_error, match="neither a reserve package"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_missing_disposition_with_zero_packages() -> None:
    """Zero packages is eligible only with *complete* disposition coverage."""
    document = _coverage_document(packages=(), dispositions=(7,))
    with pytest.raises(pm_error, match="neither a reserve package"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_duplicate_disposition() -> None:
    """Exactly one disposition per target; a second is refused, never merged."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    document["reserves"]["dispositions"].append(dict(document["reserves"]["dispositions"][0]))
    with pytest.raises(pm_error, match="more than one reserve disposition"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_duplicate_package() -> None:
    """Exactly one rank-1 package per target."""
    document = _coverage_document(packages=(7,), dispositions=(8,))
    document["reserves"]["packages"].append(dict(document["reserves"]["packages"][0]))
    with pytest.raises(pm_error, match="more than one reserve package"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_an_extra_disposition() -> None:
    """A disposition naming an unselected target is refused, never ignored."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    document["reserves"]["dispositions"].append(_reserve_disposition(999999))
    with pytest.raises(pm_error, match="not a selected entity"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_a_package_for_an_unselected_target() -> None:
    """The same rule on the package side."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    document["reserves"]["packages"].append(_reserve_package(999999))
    with pytest.raises(pm_error, match="not a selected entity"):
        pm.verify_document_crosswalk_coverage(document)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("reason_code", "REVIEW_PILOT_OTHER"),
        ("reason_code", ""),
        ("reason_scope", "candidate"),
    ],
)
def test_reserve_coverage_refuses_a_substituted_reason(column: str, value: str) -> None:
    """Migration 0012 admits exactly one reserve-scope reason code."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    document["reserves"]["dispositions"][0][column] = value
    with pytest.raises(pm_error, match="admits only"):
        pm.verify_document_crosswalk_coverage(document)


@pytest.mark.parametrize("value", [0, -1, None, "7", 1.5, True])
def test_reserve_coverage_refuses_a_malformed_target_cik(value: object) -> None:
    """A target CIK is a positive integer and is never coerced or defaulted."""
    document = _coverage_document(packages=(7,), dispositions=(8,))
    document["reserves"]["packages"][0]["target_cik_numeric"] = value
    with pytest.raises(pm_error, match="malformed target_cik_numeric"):
        pm.verify_document_crosswalk_coverage(document)


def test_reserve_coverage_refuses_an_invented_rank_on_a_disposition() -> None:
    """A rank grafted onto a disposition-only target is an unbound leaf."""
    document = _coverage_document(packages=(), dispositions=(7, 8))
    document["reserves"]["dispositions"][0]["reserve_rank"] = 1
    with pytest.raises(pm_error, match="no accepted binding"):
        pm.verify_document_crosswalk_coverage(document)


def test_document_discharges_every_crosswalk_item_at_item_granularity() -> None:
    """Every D and T item is serialized; every X and S9 item is absent (section 13.2.1)."""
    covered = pm.verify_document_crosswalk_coverage(_document())
    required = {item.number for item in pm.CROSSWALK if item.classification in {"D", "T"}}
    assert required <= set(covered)
    excluded = {item.number for item in pm.CROSSWALK if item.classification in {"X", "S9"}}
    assert not (excluded & set(covered))
    for number in required:
        assert covered[number], f"item {number} maps to no serialized leaf"


def test_every_binding_names_a_real_crosswalk_item_and_digest() -> None:
    """The binding table is derived from the accepted crosswalk, not invented beside it."""
    numbers = {item.number for item in pm.CROSSWALK}
    accepted_digests = {
        "manifest_id",
        "root_manifest_sha256",
        "selection_result_sha256",
        "selection_input_sha256",
        "source_observation_set_sha256",
        "candidate_tables_sha256",
        "quota_definitions_sha256",
        "selector_policy_sha256",
        "selected_entities_sha256",
        "selected_accessions_sha256",
        "reserves_sha256",
        "quota_report_sha256",
    }
    for path, binding in pm.DOCUMENT_FIELD_BINDINGS.items():
        assert binding.digests, path
        assert set(binding.digests) <= accepted_digests, path
        assert set(binding.items) <= numbers, path
        assert 1 <= binding.block <= 13, path
    excluded = {item.number for item in pm.CROSSWALK if item.classification in {"X", "S9"}}
    referenced = {n for binding in pm.DOCUMENT_FIELD_BINDINGS.values() for n in binding.items}
    assert not (excluded & referenced)


def test_document_orders_selected_rows_by_numeric_selected_order() -> None:
    """Blocks 8 and 9 order by the integer, not by its decimal rendering."""
    entities = tuple(_entity_row(order=order, cik=order) for order in (3, 10, 1, 2))
    document = _document(
        sources=_sources(
            selected_entities=entities,
            entity_record_sources={order: _entity_sources() for order in (1, 2, 3, 10)},
        )
    )
    rendered = document["selected_entities"]
    assert isinstance(rendered, list)
    assert [row["selected_order"] for row in rendered] == [1, 2, 3, 10]


def test_document_selected_order_is_permutation_invariant() -> None:
    """Input order cannot change the rendered array."""
    rows = tuple(_entity_row(order=order, cik=order) for order in (1, 2, 3, 10))
    sources = {order: _entity_sources() for order in (1, 2, 3, 10)}
    first = _document(sources=_sources(selected_entities=rows, entity_record_sources=sources))
    second = _document(
        sources=_sources(selected_entities=tuple(reversed(rows)), entity_record_sources=sources)
    )
    assert pm.render_canonical_json(first) == pm.render_canonical_json(second)


@pytest.mark.parametrize("bad", [0, -1, "1", 1.0, None, True])
def test_document_refuses_a_malformed_selected_order(bad: object) -> None:
    """A selected order that is not a positive integer is corrupted storage."""
    row = _entity_row(order=1, cik=1)
    row["selected_order"] = bad
    with pytest.raises(pm_error, match="malformed selected_order"):
        _document(
            sources=_sources(selected_entities=(row,), entity_record_sources={1: _entity_sources()})
        )


def test_document_refuses_duplicate_selected_order() -> None:
    """Two rows claiming one position are refused, never collapsed or reordered."""
    rows = (_entity_row(order=1, cik=1), _entity_row(order=1, cik=2))
    with pytest.raises(pm_error, match="duplicate selected_order"):
        _document(
            sources=_sources(
                selected_entities=rows,
                entity_record_sources={1: _entity_sources(), 2: _entity_sources()},
            )
        )


def test_document_refuses_a_selected_entity_with_no_candidate_record() -> None:
    """A selected row with no candidate source is refused, not serialized partially."""
    with pytest.raises(pm_error, match="no pilot_candidate_entities record"):
        _document(sources=_sources(entity_record_sources={}))


def test_document_refuses_a_selected_accession_with_no_candidate_record() -> None:
    """The accession side fails closed on the same missing-source condition."""
    with pytest.raises(pm_error, match="no pilot_candidate_accessions record"):
        _document(sources=_sources(accession_record_sources={}))


def test_document_refuses_a_truncated_candidate_record() -> None:
    """A candidate row missing a crosswalk-required field is refused, not nulled."""
    partial = {name: "v" for name in pm.ENTITY_CANDIDATE_FIELDS if name != "cik_padded"}
    with pytest.raises(pm_error, match="missing required document fields"):
        _document(sources=_sources(entity_record_sources={7: _entity_sources(candidate=partial)}))


def test_document_renders_a_populated_candidate_reason_family() -> None:
    """Item 44's reasons render as records when the entity has them."""
    document = _document()
    entities = document["selected_entities"]
    assert isinstance(entities, list)
    reasons = entities[0]["candidate_reasons"]
    assert reasons and set(reasons[0]) == set(pm.CANDIDATE_REASON_RECORD_COLUMNS)
    evidence = entities[0]["classification_evidence"]
    assert evidence and set(evidence[0]) == set(pm.ENTITY_EVIDENCE_RECORD_COLUMNS)


def test_document_refuses_a_non_proposed_manifest_state() -> None:
    """Section 13.2.2: S6 builds only the proposed-manifest schema, and says so."""
    for state in ("owner_approved", "rejected", "superseded", "", "PROPOSED"):
        with pytest.raises(pm_error, match="builds only the proposed-manifest"):
            _document(manifest_state=state)


def test_document_serializes_the_proposed_literal_not_the_argument() -> None:
    """The accepted state is serialized as the constant, never echoed from an input."""
    identity = _document(manifest_state="proposed")["manifest_identity"]
    assert isinstance(identity, dict)
    assert identity["manifest_state"] == pm.MANIFEST_STATE_LITERAL


def test_document_excludes_the_operational_envelope() -> None:
    """Section 13.4: paths, timestamps, approval fields, and detail stay out.

    The frozen exclusion list is asserted in full, including ``recorded_at_utc`` and
    ``detail``, which every persisted row carries and no document may.
    """
    rendered = pm.render_canonical_json(_document())
    for excluded in sorted(pm.OPERATIONAL_ENVELOPE_FIELDS):
        assert excluded not in rendered, f"{excluded} leaked into the document"
    assert "recorded_at_utc" in pm.OPERATIONAL_ENVELOPE_FIELDS
    assert "detail" in pm.OPERATIONAL_ENVELOPE_FIELDS


def test_document_projection_refuses_an_operational_field_in_a_frozen_tuple() -> None:
    """A projection tuple that started naming an excluded field fails closed."""
    for tuple_name in (
        pm.ENTITY_CANDIDATE_FIELDS,
        pm.ACCESSION_CANDIDATE_FIELDS,
        pm.SELECTED_ENTITY_COLUMNS,
        pm.SELECTED_ACCESSION_COLUMNS,
    ):
        assert not (set(tuple_name) & pm.OPERATIONAL_ENVELOPE_FIELDS)


def test_document_contains_no_absolute_path_at_any_depth() -> None:
    """No absolute path and no SEC identity appears anywhere in the document."""
    rendered = pm.render_canonical_json(_document())
    assert '"/' not in rendered
    assert "user-agent" not in rendered.lower()


def test_document_defers_command_invocation_to_stage_s9() -> None:
    """The single S9 deferral is provably absent from the S6 document."""
    rendered = pm.render_canonical_json(_document()).lower()
    assert "command_invocation" not in rendered
    assert "argv" not in rendered


def test_document_excludes_the_retrieval_envelope() -> None:
    """The eight X items are provably absent from the substantive body."""
    rendered = pm.render_canonical_json(_document())
    for excluded in (
        "observation_id",
        "retrieval_attempt_id",
        "retrieved_at_utc",
        "transport_sha256",
        "stored_sha256",
        "relative_storage_path",
        "etag",
        "last_modified",
        "supersedes_observation_id",
    ):
        assert excluded not in rendered


def test_document_serialization_is_byte_identical_on_re_render() -> None:
    """Re-serializing the same manifest is byte-identical (section 13.5)."""
    document = _document()
    assert pm.render_canonical_json(document) == pm.render_canonical_json(_document())


def test_document_serialization_uses_sorted_keys_lf_and_utf8() -> None:
    """Canonical JSON: sorted object keys, LF line endings, no nonfinite numbers."""
    rendered = pm.render_canonical_json(_document())
    assert "\r" not in rendered
    assert rendered.endswith("\n")
    reparsed = json.loads(rendered)
    assert list(reparsed) == sorted(reparsed)
    rendered.encode("utf-8")


def test_document_rejects_nonfinite_numbers() -> None:
    """``allow_nan=False`` refuses a nonfinite value outright."""
    with pytest.raises(ValueError, match="Out of range"):
        pm.render_canonical_json({"block": float("inf")})


def test_pilot_manifest_never_reuses_the_sec_inventory_release_manifest() -> None:
    """Section 13.6: only the hashing primitives are shared."""
    source = _executable_source(pm)
    assert "ReleaseManifest" not in source
    assert "RELEASE_SCHEMA_VERSION" not in source
    assert "sec_inventory" not in source


def test_pure_module_touches_no_environment_clock_or_repository() -> None:
    """Section 8.4: nothing is inferred from Git, the environment, or the interpreter."""
    source = _executable_source(pm)
    for forbidden in (
        "os",
        "subprocess",
        "sqlite3",
        "sys",
        "datetime",
        "utc_now",
        "pathlib",
        "open",
    ):
        assert forbidden not in source.split(), f"pure module must not reference {forbidden}"


# ==========================================================================
# The enumerated decision-authority set -- Decision 021 sections 8.4, 13.2
# ==========================================================================


def test_authority_records_are_required_and_never_default_to_empty() -> None:
    """Item 11's pairs are an assertion the caller must make, not an optional extra."""
    with pytest.raises(pm_error, match="decision_authority_records"):
        _explicit(decision_authority_records=())


def test_authority_records_must_include_the_record_that_binds_items_14_and_58() -> None:
    """Section 8.4 commits the as-of zone and the after-hours state here and nowhere else."""
    with pytest.raises(pm_error, match="decision_010"):
        _explicit(
            decision_authority_records=(
                ("Docs/Decisions/decision_021_m23_s6_manifest_construction.md", _hex("d021")),
            )
        )


@pytest.mark.parametrize(
    "records",
    [
        pytest.param(("not-a-pair",), id="not-a-pair"),
        pytest.param((("a.md",),), id="one-element"),
        pytest.param((("a.md", "x", "y"),), id="three-element"),
    ],
)
def test_authority_records_refuse_a_malformed_pair(records: tuple[object, ...]) -> None:
    """Each entry must be a (record identifier, content sha256) pair."""
    with pytest.raises(pm_error, match="must be a"):
        _explicit(decision_authority_records=records)


@pytest.mark.parametrize("identifier", ["", "   ", None, 7])
def test_authority_records_refuse_a_blank_identifier(identifier: object) -> None:
    """A record with no identifier names nothing and is refused."""
    with pytest.raises(pm_error, match="record identifier"):
        _explicit(decision_authority_records=((identifier, _hex("x")),))


@pytest.mark.parametrize(
    "identifier",
    ["/etc/passwd", "/absolute/Docs/decision_010.md", "Docs/../../secrets.md"],
)
def test_authority_records_refuse_an_absolute_or_traversing_path(identifier: str) -> None:
    """No absolute path appears anywhere in the manifest (section 13.4)."""
    with pytest.raises(pm_error, match="relative repository path"):
        _explicit(decision_authority_records=((identifier, _hex("x")),))


@pytest.mark.parametrize(
    "digest", ["", "abc", "Z" * 64, "A" * 64, hashlib.sha256(b"x").hexdigest()[:63], None, 7]
)
def test_authority_records_refuse_a_malformed_digest(digest: object) -> None:
    """A content digest is 64 lowercase hexadecimal characters or it is not one."""
    with pytest.raises(pm_error, match="content digest"):
        _explicit(
            decision_authority_records=(
                (
                    "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
                    digest,
                ),
            )
        )


def test_authority_records_refuse_a_duplicate_identifier() -> None:
    """A repeated record is refused whether or not its digests agree."""
    record = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"
    with pytest.raises(pm_error, match="more than once"):
        _explicit(decision_authority_records=((record, _hex("a")), (record, _hex("a"))))


def test_authority_records_refuse_a_conflicting_duplicate() -> None:
    """Two digests for one record is a conflict, never merged or preferred."""
    record = "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md"
    with pytest.raises(pm_error, match="more than once"):
        _explicit(decision_authority_records=((record, _hex("a")), (record, _hex("b"))))


def test_authority_records_must_be_canonically_ordered() -> None:
    """One enumerated set has one rendering, so the caller supplies it sorted."""
    with pytest.raises(pm_error, match="canonical identifier order"):
        _explicit(decision_authority_records=tuple(reversed(_AUTHORITY_RECORDS)))


def test_authority_records_are_serialized_in_block_four() -> None:
    """The pairs themselves reach the document; the digest alone does not discharge item 11."""
    authority = _document()["active_authority"]
    assert isinstance(authority, dict)
    rendered = [
        (row["decision_record"], row["content_sha256"]) for row in authority["decision_records"]
    ]
    assert rendered == [list(pair) for pair in _AUTHORITY_RECORDS] or rendered == [
        tuple(pair) for pair in _AUTHORITY_RECORDS
    ]


def test_authority_records_do_not_enter_the_selector_policy_preimage() -> None:
    """Section 8.4 has eleven fields; the enumerated pairs are document content only."""
    policy_rows = [{"policy_key": key, "policy_version": "v"} for key in pm.CONSUMED_POLICY_KEYS]
    chain = [{"version": 1, "name": "initial", "checksum_sha256": _hex("m1")}]
    other = (
        (
            "Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md",
            _hex("different"),
        ),
    )
    kwargs: dict[str, Any] = {
        "policy_versions": policy_rows,
        "migration_chain": chain,
        "selection_input_schema_version": "pilot-joint-selection-input/1.0",
        "manifest_schema_version": "pilot-manifest/1.0",
    }
    assert pm.selector_policy_sha256(explicit=_explicit(), **kwargs) == pm.selector_policy_sha256(
        explicit=_explicit(decision_authority_records=other), **kwargs
    )


def test_no_authority_value_is_inferred_from_the_environment() -> None:
    """Section 8.4: nothing is read from Git, the tree, the interpreter, or the environment."""
    source = _executable_source(pm)
    for forbidden in ("subprocess", "os.environ", "sys.version", "Path(", "open("):
        assert forbidden not in source
