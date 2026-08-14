"""OR-1 identity-preimage pinning tests (M3.3 contract §26 item 3; **R15**, **R16**).

Every assertion here pins a preimage **byte for byte**: the ``hash_table`` domain, the
exact field set, and the exact ordering. A reordering, an added field, a removed field,
or a second normalization must change the digest, because that is what makes the
identity graph reviewable rather than merely present.
"""

from __future__ import annotations

import json

import pytest

from disclosure_drift.errors import GateFailureError
from disclosure_drift.m3 import candidate_identity as ci
from disclosure_drift.pilot_policy import PILOT_EVIDENCE_POLICY_VERSION
from disclosure_drift.release.hashing import hash_table
from disclosure_drift.release.pilot_manifest import (
    SourceObservation,
    render_canonical_json,
    source_observation_set_sha256,
)


def _row(**overrides: object) -> ci.CandidateEvidenceRow:
    """One candidate evidence row, at the R15 eight fields."""
    base: dict[str, object] = {
        "classification_dimension": "size",
        "evidence_role": "winning",
        "source_observation_id": "obs-1",
        "parsed_record_id": "parsed-1",
        "source_field": "category",
        "canonical_observed_value": "Large accelerated filer",
        "policy_version": PILOT_EVIDENCE_POLICY_VERSION,
        "precedence": 2,
    }
    base.update(overrides)
    return ci.CandidateEvidenceRow(**base)  # type: ignore[arg-type]


# ==========================================================================
# evidence_sha256 -- R15's exact eight fields, and nothing else
# ==========================================================================


def test_evidence_preimage_is_exactly_the_decision_016_field_set() -> None:
    assert ci.EVIDENCE_PREIMAGE_FIELDS == (
        "canonical_observed_value",
        "classification_dimension",
        "evidence_role",
        "parsed_record_id",
        "policy_version",
        "precedence",
        "source_field",
        "source_observation_id",
    )
    assert tuple(sorted(_row().preimage())) == ci.EVIDENCE_PREIMAGE_FIELDS


def test_evidence_sha256_reproduces_the_pinned_hash_table_call() -> None:
    row = _row()
    fields = row.preimage()
    expected = hash_table(
        "pilot_candidate_evidence_row", tuple(sorted(fields)), [fields]
    ).normalized_content_sha256
    assert ci.evidence_sha256(row) == expected


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("classification_dimension", "industry"),
        ("evidence_role", "supporting"),
        ("source_observation_id", "obs-2"),
        ("parsed_record_id", "parsed-2"),
        ("source_field", "sic"),
        ("canonical_observed_value", "Accelerated filer"),
        ("policy_version", "pilot-evidence/9.9"),
        ("precedence", 3),
    ],
)
def test_every_included_field_moves_the_evidence_digest(field: str, value: object) -> None:
    assert ci.evidence_sha256(_row()) != ci.evidence_sha256(_row(**{field: value}))


def test_a_null_canonical_value_stays_distinct_from_the_empty_string() -> None:
    """Decision 067 §7.1: a canonical ``NULL`` stays a canonical ``NULL``."""
    assert ci.evidence_sha256(_row(canonical_observed_value=None)) != ci.evidence_sha256(
        _row(canonical_observed_value="")
    )


def test_a_reordered_preimage_is_a_different_digest() -> None:
    fields = _row().preimage()
    reordered = tuple(reversed(ci.EVIDENCE_PREIMAGE_FIELDS))
    assert hash_table(
        "pilot_candidate_evidence_row", reordered, [fields]
    ).normalized_content_sha256 != ci.evidence_sha256(_row())


# ==========================================================================
# R16-C1 -- contributor membership
# ==========================================================================


def test_contributors_keep_only_the_strongest_precedence_per_source_field() -> None:
    strong = _row(precedence=2, source_observation_id="obs-strong")
    weak = _row(precedence=4, source_observation_id="obs-weak")
    assert ci.resolution_contributors([strong, weak]) == (strong,)


def test_contributors_are_not_all_rows_in_the_dimension() -> None:
    """A weaker observation of the same field never contributes."""
    rows = [_row(precedence=2), _row(precedence=3, source_observation_id="obs-3")]
    assert len(ci.resolution_contributors(rows)) < len(rows)


def test_equal_precedence_disagreement_contributes_nothing() -> None:
    """The field is unresolved: no value is guessed and no tie is broken."""
    rows = [
        _row(precedence=2, canonical_observed_value="a", source_observation_id="obs-a"),
        _row(precedence=2, canonical_observed_value="b", source_observation_id="obs-b"),
    ]
    assert ci.resolution_contributors(rows) == ()


def test_membership_is_not_inferred_from_evidence_role() -> None:
    """Two rows differing only in role are both contributors or both are not."""
    winning = _row(evidence_role="winning")
    supporting = _row(evidence_role="supporting", source_observation_id="obs-2")
    assert set(ci.resolution_contributors([winning, supporting])) == {winning, supporting}


def test_a_second_source_field_contributes_its_own_winner() -> None:
    category = _row(source_field="category")
    sic = _row(source_field="sic", source_observation_id="obs-sic")
    assert set(ci.resolution_contributors([category, sic])) == {category, sic}


def test_contributor_ordering_is_deterministic_and_input_order_independent() -> None:
    rows = [
        _row(source_field="a", precedence=2, source_observation_id="obs-a"),
        _row(source_field="b", precedence=3, source_observation_id="obs-b"),
        _row(source_field="c", precedence=1, source_observation_id="obs-c"),
    ]
    assert ci.resolution_contributors(rows) == ci.resolution_contributors(list(reversed(rows)))


def test_contributors_refuse_a_mixed_dimension_input() -> None:
    with pytest.raises(GateFailureError, match="one classification dimension"):
        ci.resolution_contributors([_row(), _row(classification_dimension="industry")])


def test_contributing_digest_pins_the_decision_067_field_order() -> None:
    rows = (_row(),)
    expected = hash_table(
        "pilot_candidate_resolution_evidence",
        ("evidence_role", "precedence", "evidence_sha256"),
        [
            {
                "evidence_role": rows[0].evidence_role,
                "precedence": rows[0].precedence,
                "evidence_sha256": rows[0].evidence_sha256,
            }
        ],
    ).normalized_content_sha256
    assert ci.contributing_evidence_sha256(rows) == expected


def test_unrelated_evidence_is_excluded_from_the_contributor_digest() -> None:
    """A weaker observation of the same field is in the dimension but not a contributor."""
    everything = (_row(), _row(precedence=4, source_observation_id="obs-weak"))
    contributors = ci.resolution_contributors(everything)
    assert contributors == (everything[0],)
    assert ci.contributing_evidence_sha256(contributors) != ci.contributing_evidence_sha256(
        everything
    )


# ==========================================================================
# The eight resolution digests
# ==========================================================================


@pytest.mark.parametrize("dimension", sorted(ci.RESOLUTION_DIMENSIONS))
def test_every_governed_dimension_has_a_classification_column(dimension: str) -> None:
    assert ci.CLASSIFICATION_COLUMNS_BY_DIMENSION[dimension]


def test_resolution_digest_pins_its_four_field_preimage() -> None:
    contributors = ci.resolution_contributors([_row()])
    digest = ci.resolution_sha256(
        dimension="size",
        contributors=contributors,
        evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
        classification={"size_stratum": "large_accelerated"},
    )
    fields = {
        "classification_dimension": "size",
        "contributing_evidence_sha256": ci.contributing_evidence_sha256(contributors),
        "evidence_policy_version": PILOT_EVIDENCE_POLICY_VERSION,
        "resolved_value": "large_accelerated",
    }
    expected = hash_table(
        "pilot_candidate_resolution", tuple(sorted(fields)), [fields]
    ).normalized_content_sha256
    assert digest == expected


def test_a_resolved_value_with_no_contributor_fails_closed() -> None:
    with pytest.raises(GateFailureError, match="no contributing candidate"):
        ci.resolution_sha256(
            dimension="size",
            contributors=(),
            evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
            classification={"size_stratum": "large_accelerated"},
        )


# --------------------------------------------------------------------------
# R21 -- the XBRL composite resolved value (Decision 071 §8)
# --------------------------------------------------------------------------


def _xbrl(has_xbrl: object, has_inline: object) -> str:
    return ci.resolved_value_rendering(
        "xbrl", {"has_xbrl": has_xbrl, "has_inline_xbrl": has_inline}
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [((1, 1), (0, 1)), ((1, 1), (1, 0)), ((0, 0), (1, 0)), ((0, 0), (0, 1))],
)
def test_each_xbrl_flag_independently_moves_the_resolved_value(
    left: tuple[int, int], right: tuple[int, int]
) -> None:
    assert _xbrl(*left) != _xbrl(*right)


def test_the_xbrl_resolved_value_uses_the_accepted_canonical_json_serializer() -> None:
    """R21: the accepted Decision 021 §13.5 serializer, not a second encoder."""
    rendered = _xbrl(1, 0)
    assert rendered == render_canonical_json({"has_inline_xbrl": 0, "has_xbrl": 1})
    assert json.loads(rendered) == {"has_inline_xbrl": 0, "has_xbrl": 1}


def test_the_xbrl_resolved_value_never_uses_a_hash_table_delimiter() -> None:
    """R21: ``hash_table``'s internal separators are not an application encoding."""
    for rendered in (_xbrl(1, 1), _xbrl(0, None), _xbrl(None, None)):
        assert "\x1f" not in rendered
        assert "\x1e" not in rendered


def test_the_xbrl_resolved_value_is_construction_order_independent() -> None:
    forward = ci.resolved_value_rendering("xbrl", {"has_xbrl": 1, "has_inline_xbrl": 0})
    reverse = ci.resolved_value_rendering("xbrl", {"has_inline_xbrl": 0, "has_xbrl": 1})
    assert forward == reverse


def test_a_null_xbrl_flag_is_deterministic_and_distinct() -> None:
    assert _xbrl(None, 1) == _xbrl(None, 1)
    assert _xbrl(None, 1) != _xbrl(0, 1)
    assert json.loads(_xbrl(None, 1))["has_xbrl"] is None


def test_a_non_integer_xbrl_flag_fails_closed() -> None:
    with pytest.raises(GateFailureError, match="integer or NULL"):
        _xbrl("1", 0)


def test_the_xbrl_resolution_digest_is_independently_reconstructable() -> None:
    contributors = ci.resolution_contributors([_row(classification_dimension="xbrl")])
    classification = {"has_xbrl": 1, "has_inline_xbrl": 0}
    digest = ci.resolution_sha256(
        dimension="xbrl",
        contributors=contributors,
        evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
        classification=classification,
    )
    fields = {
        "classification_dimension": "xbrl",
        "contributing_evidence_sha256": ci.contributing_evidence_sha256(contributors),
        "evidence_policy_version": PILOT_EVIDENCE_POLICY_VERSION,
        "resolved_value": render_canonical_json({"has_inline_xbrl": 0, "has_xbrl": 1}),
    }
    assert (
        digest
        == hash_table(
            "pilot_candidate_resolution", tuple(sorted(fields)), [fields]
        ).normalized_content_sha256
    )


def test_only_the_xbrl_dimension_is_composite() -> None:
    assert set(ci.COMPOSITE_RESOLUTION_DIMENSIONS) == {"xbrl"}
    for dimension in sorted(set(ci.RESOLUTION_DIMENSIONS) - ci.COMPOSITE_RESOLUTION_DIMENSIONS):
        columns = ci.CLASSIFICATION_COLUMNS_BY_DIMENSION[dimension]
        assert len(columns) == 1
        rendered = ci.resolved_value_rendering(dimension, {columns[0]: "value"})
        assert rendered == "value"


def test_an_unregistered_dimension_is_refused() -> None:
    with pytest.raises(GateFailureError, match="governed resolution dimensions"):
        ci.resolved_value_rendering("not_a_dimension", {})


def test_a_census_resolution_digest_is_never_a_candidate_resolution_digest() -> None:
    """Decision 067 §10.7: similar names never justify reusing the census digest."""
    census_like = hash_table(
        "census_accession_field_resolutions", ("resolved_value",), [{"resolved_value": "x"}]
    ).normalized_content_sha256
    candidate = ci.resolution_sha256(
        dimension="cohort",
        contributors=ci.resolution_contributors([_row(classification_dimension="cohort")]),
        evidence_policy_version=PILOT_EVIDENCE_POLICY_VERSION,
        classification={"provisional_official_cohort": "development"},
    )
    assert candidate != census_like


# ==========================================================================
# Snapshot-level identities
# ==========================================================================


def test_snapshot_identity_refuses_a_preimage_that_is_not_the_frozen_five() -> None:
    with pytest.raises(GateFailureError, match="must carry exactly"):
        ci.snapshot_identity_sha256({"coverage_window_sha256": "a"})


def test_snapshot_content_digest_binds_snapshot_id_exactly_once() -> None:
    assert "snapshot_id" in ci.SNAPSHOT_CONTENT_FIELDS
    for columns in (
        ci.ENTITY_TABLE_COLUMNS,
        ci.ACCESSION_TABLE_COLUMNS,
        ci.REGISTRANT_TABLE_COLUMNS,
        ci.ENTITY_EVIDENCE_COLUMNS,
        ci.ACCESSION_EVIDENCE_COLUMNS,
        ci.ENTITY_REASONS_COLUMNS,
        ci.ACCESSION_REASONS_COLUMNS,
    ):
        assert "snapshot_id" not in columns


def test_no_family_digest_carries_a_timestamp_path_or_free_text() -> None:
    forbidden = {"recorded_at_utc", "detail", "evidence_id", "census_run_id"}
    for columns in (
        ci.ENTITY_TABLE_COLUMNS,
        ci.ACCESSION_TABLE_COLUMNS,
        ci.REGISTRANT_TABLE_COLUMNS,
        ci.ENTITY_EVIDENCE_COLUMNS,
        ci.ACCESSION_EVIDENCE_COLUMNS,
        ci.ENTITY_REASONS_COLUMNS,
        ci.ACCESSION_REASONS_COLUMNS,
        ci.SNAPSHOT_CONTENT_FIELDS,
        ci.SNAPSHOT_IDENTITY_FIELDS,
        ci.COVERAGE_WINDOW_FIELDS,
    ):
        assert not forbidden & set(columns)


def test_input_observation_set_digest_is_the_decision_021_digest() -> None:
    """Decision 067 §9.1: definitionally identical, not merely similarly named."""
    observations = [
        SourceObservation(
            source_id="sec_bulk_submissions",
            request_identity="req/1",
            logical_sha256="a" * 64,
            parser_version="submissions-json/1.0",
            outcome="stored_new",
        )
    ]
    assert ci.input_observation_set_sha256(observations) == source_observation_set_sha256(
        observations
    )
