"""Candidate-snapshot builder tests (M3.3 contract §26 items 1, 4, 5, 6, 7).

The fixture is a synthetic **census layer**, not a hand-written candidate snapshot: the
builder derives every candidate row from it exactly as it would from a real parse, so
these tests exercise production logic rather than a restatement of it.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from disclosure_drift.m3.candidate_snapshot import (
    CandidateSnapshotError,
    CandidateSnapshotInputs,
    build_and_freeze_candidate_snapshot,
)
from disclosure_drift.m3.offline_parse import run_offline_metadata_parse
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_selection_store import load_frozen_joint_candidates
from disclosure_drift.sec.accession_selector import (
    APPROVED_DEFERRED_QUOTA_KEYS,
    DEFERRED_QUOTA_KEY,
    QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS,
)
from disclosure_drift.storage.catalog import ELIGIBLE_FORM_TYPES, CatalogWriter
from disclosure_drift.storage.sqlite import apply_migrations, connect, transaction

_OBSERVATION = "obs-bulk-submissions-1"
#: The accepted ``company.idx`` observation whose ``cik_padded`` rows ESTABLISH each
#: accession's complete substantive registrant set (Decision 072 R23 section 5.2).
#: Under **Decision 083 R59** an accession without such evidence has an
#: ``unestablished`` set and is blocked from candidacy entirely, so a realistic
#: census fixture must carry it -- see ``test_group_r59`` for the absent case.
_INDEX_OBSERVATION = "obs-full-index-company-1"
_RUN = "job-census-1"
_AT = "2026-01-01T00:00:00Z"
_INPUTS = CandidateSnapshotInputs(
    census_run_id=_RUN,
    coverage_start="2009-01-01",
    coverage_end="2026-06-30",
    as_of_date="2026-06-30",
)


def _seed_reference(connection: sqlite3.Connection) -> None:
    with transaction(connection) as active:
        for form_type, is_amendment, eligible, description in ELIGIBLE_FORM_TYPES:
            active.execute(
                "INSERT OR REPLACE INTO reference_form_types (form_type, is_amendment, "
                "is_eligible_universe, description, decision_record) VALUES (?, ?, ?, ?, ?)",
                (form_type, int(is_amendment), int(eligible), description, "D007"),
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


def _parsed_record(connection: sqlite3.Connection, parsed_record_id: str) -> None:
    """One accepted parsed-record row, which every observation foreign-keys to."""
    connection.execute(
        "INSERT OR IGNORE INTO census_parsed_records (parsed_record_id, parser_run_id, "
        "source_observation_id, native_identity, record_sha256, record_index, payload_json, "
        "unknown_fields_json, warnings_json, reason_codes_json, duplicate_indicator, "
        "conflict_indicator, recorded_at_utc) VALUES (?, 'pr-1', ?, ?, ?, 0, '{}', '[]', "
        "'[]', '[]', 0, 0, ?)",
        (parsed_record_id, _OBSERVATION, parsed_record_id, "e" * 64, _AT),
    )


def _seed_sic_authority(connection: sqlite3.Connection, *codes: str) -> None:
    """The accepted SIC authority, as an E0 parse of the official code list leaves it."""
    for code in codes:
        connection.execute(
            "INSERT OR REPLACE INTO reference_sic_codes (sic_code, description, office, "
            "source_snapshot_id, source_url, retrieved_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
            (
                code,
                f"Synthetic description for {code}",
                "Office of Synthetic Issuers",
                "obs",
                "",
                _AT,
            ),
        )


def _registrant(
    connection: sqlite3.Connection,
    cik: int,
    *,
    name: str,
    category: str,
    sic: str,
    entity_type: str = "operating",
    former_name: str | None = None,
) -> None:
    padded = f"{cik:010d}"
    connection.execute(
        "INSERT OR IGNORE INTO census_registrants (cik_numeric, cik_padded, "
        "first_observed_at_utc, latest_observed_at_utc) VALUES (?, ?, ?, ?)",
        (cik, padded, _AT, _AT),
    )
    kinds = [
        ("company_name", name, "name"),
        ("filing_status", category, "category"),
        ("sic", sic, "sic"),
        ("entity_type", entity_type, "entityType"),
        ("fiscal_year_end", "1231", "fiscalYearEnd"),
    ]
    if former_name is not None:
        kinds.append(("former_name", former_name, "formerNames"))
    _parsed_record(connection, f"parsed-{cik}")
    for index, (kind, value, source_field) in enumerate(kinds):
        connection.execute(
            "INSERT INTO census_registrant_observations (registrant_observation_id, "
            "cik_numeric, observation_kind, value_text, source_observation_id, "
            "parsed_record_id, source_field, observed_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                f"ro-{cik}-{index}",
                cik,
                kind,
                value,
                _OBSERVATION,
                f"parsed-{cik}",
                source_field,
                _AT,
            ),
        )


def _accession(
    connection: sqlite3.Connection,
    cik: int,
    year: int,
    seq: int,
    *,
    form: str = "10-K",
    cohort: str = "development",
    parent: str | None = None,
    co_registrants: tuple[int, ...] = (),
    establish_registrant_set: bool = True,
) -> str:
    plain = f"{cik:010d}{year % 100:02d}{seq:06d}"
    dashed = f"{cik:010d}-{year % 100:02d}-{seq:06d}"
    filing_date = f"{year}-03-01"
    is_amendment = int(form.endswith("/A"))
    _parsed_record(connection, f"parsed-acc-{plain}")
    connection.execute(
        "INSERT INTO census_accessions (accession_plain, accession_dashed, "
        "registrant_cik_numeric, submitter_cik_numeric, form_type, is_amendment, "
        "is_discovery_form, is_negative_control, filing_date_sec, report_date, "
        "acceptance_date_sec, official_filing_temporal_cohort, accepted_temporal_cohort, "
        "xbrl_flag, inline_xbrl_flag, source_observation_id, parsed_record_id, "
        "first_observed_at_utc, latest_observed_at_utc) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, 0, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?)",
        (
            plain,
            dashed,
            cik,
            cik,
            form,
            is_amendment,
            filing_date,
            f"{year - 1}-12-31",
            filing_date,
            cohort,
            cohort,
            _OBSERVATION,
            f"parsed-acc-{plain}",
            _AT,
            _AT,
        ),
    )
    for field, value in (
        ("filingDate", f'"{filing_date}"'),
        ("form", f'"{form}"'),
        ("isXBRL", "1"),
        ("isInlineXBRL", "1"),
        ("cik", str(cik)),
    ):
        connection.execute(
            "INSERT INTO census_accession_observations (accession_observation_id, "
            "accession_plain, source_observation_id, parsed_record_id, field_name, "
            "raw_value_json, observed_at_utc, conflict_indicator) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
            (
                f"ao-{plain}-{field}",
                plain,
                _OBSERVATION,
                f"parsed-acc-{plain}",
                field,
                value,
                _AT,
            ),
        )
    connection.execute(
        "INSERT INTO census_accession_field_resolutions (accession_plain, field_name, "
        "status, resolved_value, authority_class, policy_version, is_material, "
        "blocks_dependents, resolution_sha256, resolved_at_utc) "
        "VALUES (?, 'official_filing_date', 'resolved', ?, 'entity_submissions', "
        "'accession-resolution/1.0', 1, 0, ?, ?)",
        (plain, filing_date, "0" * 64, _AT),
    )
    if parent is not None:
        connection.execute(
            "INSERT INTO census_accession_field_resolutions (accession_plain, field_name, "
            "status, resolved_value, authority_class, policy_version, is_material, "
            "blocks_dependents, resolution_sha256, resolved_at_utc) "
            "VALUES (?, 'amendment_relationship', 'resolved', ?, 'entity_submissions', "
            "'accession-resolution/1.0', 1, 0, ?, ?)",
            (plain, parent, "1" * 64, _AT),
        )
    connection.execute(
        "INSERT INTO census_accession_cohort_resolutions (accession_plain, policy_version, "
        "official_filing_temporal_cohort, accepted_temporal_cohort, cohort_boundary_crossed, "
        "requires_2024_approval, resolution_sha256, resolved_at_utc) "
        "VALUES (?, 'accession-resolution/1.0', ?, ?, 0, 0, ?, ?)",
        (plain, cohort, cohort, "2" * 64, _AT),
    )
    if establish_registrant_set:
        # One accepted ``company.idx`` row per registrant, exactly as the real index
        # carries a filing: this is the only accepted route by which R23 section 5.2
        # establishes the substantive set, and the only thing that makes the accession a
        # candidate at all under **Decision 083 R59**.
        for member in (cik, *co_registrants):
            connection.execute(
                "INSERT INTO census_accession_observations (accession_observation_id, "
                "accession_plain, source_observation_id, parsed_record_id, field_name, "
                "raw_value_json, observed_at_utc, conflict_indicator) "
                "VALUES (?, ?, ?, ?, 'cik_padded', ?, ?, 0)",
                (
                    f"ao-{plain}-idx-{member}",
                    plain,
                    _INDEX_OBSERVATION,
                    f"parsed-acc-{plain}",
                    f'"{member:010d}"',
                    _AT,
                ),
            )
    return plain


def _seed_census(connection: sqlite3.Connection) -> None:
    with transaction(connection) as active:
        active.execute(
            "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
            "started_at_utc, detail) VALUES (?, 'sec_census', 'completed', 'M2.2', ?, '')",
            (_RUN, _AT),
        )
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "logical_sha256, parser_version, recorded_at_utc) VALUES "
            "(?, 'sec_bulk_submissions', 'req/bulk/1', 'https://example.invalid/a', "
            "'census', ?, 'stored_new', ?, 'submissions-json/1.0', ?)",
            (_OBSERVATION, _AT, "a" * 64, _AT),
        )
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "logical_sha256, parser_version, recorded_at_utc) VALUES "
            "(?, 'sec_full_index_company', 'req/index/1', "
            "'https://example.invalid/company.idx', 'census', ?, 'stored_new', ?, "
            "'full-index/1.0', ?)",
            (_INDEX_OBSERVATION, _AT, "b" * 64, _AT),
        )
        active.execute(
            "INSERT INTO census_parser_runs (parser_run_id, source_observation_id, parser_id, "
            "parser_version, started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
            "outcome, summary_json) VALUES ('pr-1', ?, 'submissions-json', "
            "'submissions-json/1.0', ?, ?, 3, 0, 'completed', '{}')",
            (_OBSERVATION, _AT, _AT),
        )
        for index, (region, state, observed) in enumerate(
            (("filings", "valid_present", "object"), ("formerNames", "valid_empty", "array"))
        ):
            active.execute(
                "INSERT INTO census_structural_observations (structural_observation_id, "
                "parser_run_id, source_observation_id, region, state, observed_type, "
                "count_is_trustworthy, is_genuine_zero, recorded_at_utc) "
                "VALUES (?, 'pr-1', ?, ?, ?, ?, 1, 0, ?)",
                (f"struct-{index}", _OBSERVATION, region, state, observed, _AT),
            )
        _seed_sic_authority(active, "3571", "1311", "3826", "6726", "6770")
        _registrant(
            active,
            1,
            name="Alpha Technologies Inc",
            category="Large accelerated filer",
            sic="3571",
            former_name="Alpha Systems Inc",
        )
        _registrant(active, 2, name="Beta Energy Corp", category="Accelerated filer", sic="1311")
        original = _accession(active, 1, 2020, 1)
        _accession(active, 1, 2021, 2, form="10-K/A", parent=original)
        _accession(active, 2, 2009, 1, cohort="support_2009")
        _accession(active, 2, 2018, 2)


@pytest.fixture
def catalog(tmp_path: Path) -> Iterator[Path]:
    """A migrated catalog carrying only an accepted synthetic census layer."""
    database = tmp_path / "catalog.sqlite3"
    with connect(database, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference(connection)
        _seed_census(connection)
    yield database


def _build(database: Path, tmp_path: Path, **kwargs: object) -> object:
    with CatalogWriter(database, tmp_path / "locks") as writer:
        return build_and_freeze_candidate_snapshot(writer=writer, inputs=_INPUTS, **kwargs)  # type: ignore[arg-type]


# ==========================================================================
# Group A: a conforming snapshot freezes, deterministically
# ==========================================================================


def test_a_conforming_census_layer_freezes_a_snapshot(catalog: Path, tmp_path: Path) -> None:
    frozen = _build(catalog, tmp_path)
    assert frozen.snapshot_id  # type: ignore[attr-defined]
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT snapshot_state, entity_count, accession_count, candidate_snapshot_sha256 "
            "FROM pilot_candidate_snapshots"
        ).fetchone()
    assert row["snapshot_state"] == "frozen"
    assert row["entity_count"] == 2
    assert row["accession_count"] == 4
    assert row["candidate_snapshot_sha256"] == frozen.candidate_snapshot_sha256  # type: ignore[attr-defined]


def test_two_builds_in_separate_catalogs_share_one_identity(tmp_path: Path) -> None:
    """Decision 016 §1's required property: identity is content, not run."""
    identities = []
    for index in (1, 2):
        database = tmp_path / f"catalog-{index}.sqlite3"
        with connect(database, writer=True) as connection:
            apply_migrations(connection)
            _seed_reference(connection)
            _seed_census(connection)
        identities.append(_build(database, tmp_path / str(index)).snapshot_id)  # type: ignore[attr-defined]
    assert identities[0] == identities[1]


def test_the_frozen_snapshot_rejects_mutation(catalog: Path, tmp_path: Path) -> None:
    frozen = _build(catalog, tmp_path)
    with connect(catalog, writer=True) as connection, pytest.raises(sqlite3.DatabaseError):
        connection.execute(
            "UPDATE pilot_candidate_snapshots SET entity_count = 99 WHERE snapshot_id = ?",
            (frozen.snapshot_id,),  # type: ignore[attr-defined]
        )


# ==========================================================================
# Group B: OQ-3 and R5 -- collision, pre-existing building, atomic rollback
# ==========================================================================


def test_a_rebuild_in_the_same_catalog_fails_closed(catalog: Path, tmp_path: Path) -> None:
    _build(catalog, tmp_path)
    with pytest.raises(CandidateSnapshotError, match="already exists"):
        _build(catalog, tmp_path)


def test_a_preexisting_building_snapshot_blocks(catalog: Path, tmp_path: Path) -> None:
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO pilot_candidate_snapshots (snapshot_id, census_run_id, coverage_start, "
            "coverage_end, as_of_date, include_open_quarter, coverage_policy_version, "
            "candidate_policy_version, sic_family_mapping_version, evidence_policy_version, "
            "coverage_window_sha256, input_observation_set_sha256, snapshot_state, "
            "created_at_utc, detail) VALUES (?, ?, '2009-01-01', '2026-06-30', '2026-06-30', 0, "
            "'pilot-coverage/1.0', 'pilot-candidate/1.0', 'sic-family-mapping/0.2', "
            "'pilot-evidence/1.0', ?, ?, 'building', ?, '')",
            ("b" * 64, _RUN, "c" * 64, "d" * 64, _AT),
        )
    with pytest.raises(CandidateSnapshotError, match="building candidate snapshot"):
        _build(catalog, tmp_path)


@pytest.mark.parametrize(
    "step",
    ["after_snapshot_insert", "after_children", "after_digests", "after_revalidation"],
)
def test_a_fault_at_any_step_leaves_no_partial_snapshot(
    catalog: Path, tmp_path: Path, step: str
) -> None:
    with pytest.raises(CandidateSnapshotError, match="injected rehearsal fault"):
        _build(catalog, tmp_path, fault=step)
    with connect(catalog) as connection:
        for table in (
            "pilot_candidate_snapshots",
            "pilot_candidate_entities",
            "pilot_candidate_accessions",
            "pilot_candidate_entity_evidence",
            "pilot_candidate_accession_evidence",
        ):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"  # noqa: S608 -- fixed allowlist
            ).fetchone()[0]
            assert count == 0, f"{table} kept rows after a rolled-back transaction"


# ==========================================================================
# Group C: the OR-2 mapping, applied
# ==========================================================================


def test_the_accepted_classification_reaches_the_candidate_rows(
    catalog: Path, tmp_path: Path
) -> None:
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        rows = {
            int(row["cik_numeric"]): row
            for row in connection.execute(
                "SELECT cik_numeric, size_stratum, industry_family, sic_code, "
                "primary_universe_eligible, filing_time_name FROM pilot_candidate_entities"
            ).fetchall()
        }
    assert rows[1]["size_stratum"] == "large_accelerated"
    assert rows[1]["industry_family"] == "technology_and_communications"
    assert rows[2]["industry_family"] == "energy_and_utilities"
    assert rows[1]["filing_time_name"] == "Alpha Technologies Inc"


def test_a_pre_study_accession_carries_its_provenance_reason(catalog: Path, tmp_path: Path) -> None:
    """Decision 019 §7: the marker is present exactly where pre-study is claimed."""
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        support = connection.execute(
            "SELECT accession_plain, support_eligible, provisional_official_cohort "
            "FROM pilot_candidate_accessions WHERE support_eligible = 1"
        ).fetchall()
        reasons = connection.execute(
            "SELECT accession_plain FROM pilot_candidate_accession_reasons "
            "WHERE reason_scope = 'cohort' AND reason_code = 'PILOT_ACCESSION_PRE_STUDY_SUPPORT'"
        ).fetchall()
    assert len(support) == 1
    assert support[0]["provisional_official_cohort"] is None
    assert [row["accession_plain"] for row in reasons] == [support[0]["accession_plain"]]


def test_a_resolvable_amendment_links_to_its_original(catalog: Path, tmp_path: Path) -> None:
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT amendment_linkage_state, provisional_parent_accession "
            "FROM pilot_candidate_accessions WHERE is_amendment = 1"
        ).fetchone()
    assert row["amendment_linkage_state"] == "amends_original"
    assert row["provisional_parent_accession"] is not None


def test_an_unresolvable_amendment_fails_to_unresolved_with_its_review_reason(
    catalog: Path, tmp_path: Path
) -> None:
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "DELETE FROM census_accession_field_resolutions "
            "WHERE field_name = 'amendment_relationship'"
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT accession_plain, amendment_linkage_state, provisional_parent_accession "
            "FROM pilot_candidate_accessions WHERE is_amendment = 1"
        ).fetchone()
        reason = connection.execute(
            "SELECT 1 FROM pilot_candidate_accession_reasons WHERE accession_plain = ? "
            "AND reason_code = 'REVIEW_AMENDMENT_PARENT_UNRESOLVED'",
            (row["accession_plain"],),
        ).fetchone()
    assert row["amendment_linkage_state"] == "unresolved_amendment"
    assert row["provisional_parent_accession"] is None
    assert reason is not None


def test_a_registrant_without_a_company_name_refuses_the_snapshot(
    catalog: Path, tmp_path: Path
) -> None:
    """``filing_time_name`` is NOT NULL and is never synthesized."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "DELETE FROM census_registrant_observations "
            "WHERE cik_numeric = 1 AND observation_kind = 'company_name'"
        )
    with pytest.raises(CandidateSnapshotError, match="company-name observation"):
        _build(catalog, tmp_path)


def test_a_plain_dashed_disagreement_fails_closed(catalog: Path, tmp_path: Path) -> None:
    """Decision 018 §5: disagreement fails closed and is never reconciled."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        plain = str(
            active.execute(
                "SELECT accession_plain FROM census_accessions ORDER BY accession_plain LIMIT 1"
            ).fetchone()[0]
        )
        active.execute(
            "UPDATE census_accessions SET accession_dashed = '0000000009-99-000009' "
            "WHERE accession_plain = ?",
            (plain,),
        )
    with pytest.raises(CandidateSnapshotError, match="disagrees with the canonical"):
        _build(catalog, tmp_path)


def test_an_unmapped_sic_is_review_required_not_mapped_by_proximity(
    catalog: Path, tmp_path: Path
) -> None:
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_registrant_observations SET value_text = '3826' "
            "WHERE cik_numeric = 1 AND observation_kind = 'sic'"
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT industry_family, industry_evidence_level, industry_quota_eligible "
            "FROM pilot_candidate_entities WHERE cik_numeric = 1"
        ).fetchone()
    assert row["industry_family"] is None
    assert row["industry_evidence_level"] == "review_required"
    assert row["industry_quota_eligible"] == 0


# ==========================================================================
# Group D: identity recomputation and non-contamination
# ==========================================================================


def test_an_sic_outside_the_accepted_authority_fails_closed(catalog: Path, tmp_path: Path) -> None:
    """Decision 007 / Decision 067 §10.5: the SIC code list is the only permitted source."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_registrant_observations SET value_text = '9995' "
            "WHERE cik_numeric = 1 AND observation_kind = 'sic'"
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT sic_code, industry_family, industry_evidence_level, "
            "primary_universe_eligible FROM pilot_candidate_entities WHERE cik_numeric = 1"
        ).fetchone()
    assert row["sic_code"] is None
    assert row["industry_family"] is None
    assert row["industry_evidence_level"] == "review_required"
    assert row["primary_universe_eligible"] == 0


def test_an_unestablished_sic_authority_fails_every_sic_classification_closed(
    catalog: Path, tmp_path: Path
) -> None:
    """An accepted-as-unavailable SIC source leaves the authority empty."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute("DELETE FROM reference_sic_codes")
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        rows = connection.execute(
            "SELECT sic_code, industry_family, primary_universe_eligible, control_kind "
            "FROM pilot_candidate_entities"
        ).fetchall()
    assert all(row["sic_code"] is None for row in rows)
    assert all(row["industry_family"] is None for row in rows)
    assert all(row["primary_universe_eligible"] == 0 for row in rows)
    assert all(row["control_kind"] is None for row in rows)


def test_a_boundary_control_sic_reaches_the_candidate_row(catalog: Path, tmp_path: Path) -> None:
    """R20 (Decision 071 §4): the RIC/ETF predicate, end to end through the builder."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_registrant_observations SET value_text = '6726' "
            "WHERE cik_numeric = 2 AND observation_kind = 'sic'"
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT candidate_category, control_kind, primary_universe_eligible "
            "FROM pilot_candidate_entities WHERE cik_numeric = 2"
        ).fetchone()
        control_accessions = connection.execute(
            "SELECT control_eligible, base_eligible FROM pilot_candidate_accessions "
            "WHERE anchor_cik_numeric = 2"
        ).fetchall()
    assert row["candidate_category"] == "control"
    assert row["control_kind"] == "registered_investment_company_or_etf"
    assert row["primary_universe_eligible"] == 0
    assert all(item["control_eligible"] == 1 for item in control_accessions)
    assert all(item["base_eligible"] == 0 for item in control_accessions)


def test_an_entity_type_string_can_never_create_a_control(catalog: Path, tmp_path: Path) -> None:
    """R20 (Decision 071 §4): the removed ``entityType == kind`` mapping stays removed."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_registrant_observations SET value_text = 'foreign_private_issuer' "
            "WHERE cik_numeric = 1 AND observation_kind = 'entity_type'"
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        row = connection.execute(
            "SELECT candidate_category, control_kind FROM pilot_candidate_entities "
            "WHERE cik_numeric = 1"
        ).fetchone()
    assert row["candidate_category"] != "control"
    assert row["control_kind"] is None


def test_the_former_name_payload_is_the_decision_019_canonical_form(
    catalog: Path, tmp_path: Path
) -> None:
    """Decision 019 §8.2: exactly one of two key sets, ``relationship`` included."""
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        value = connection.execute(
            "SELECT canonical_observed_value FROM pilot_candidate_entity_evidence "
            "WHERE classification_dimension = 'identity' AND source_field = "
            "'former_name_relationship'"
        ).fetchone()[0]
    payload = json.loads(str(value))
    assert set(payload) == {"current_name", "prior_name", "relationship"}
    assert payload["relationship"] == "prior_current"
    assert str(value) == json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def test_amendment_purpose_stays_unproven_and_quota_ineligible(
    catalog: Path, tmp_path: Path
) -> None:
    """IN-2 / Decision 014 §6: no category is manufactured from metadata."""
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        amendment = connection.execute(
            "SELECT amendment_purpose_category, amendment_purpose_evidence_level, "
            "amendment_purpose_resolution_sha256, amendment_purpose_quota_eligible "
            "FROM pilot_candidate_accessions WHERE is_amendment = 1"
        ).fetchone()
        original = connection.execute(
            "SELECT amendment_purpose_evidence_level FROM pilot_candidate_accessions "
            "WHERE is_amendment = 0 LIMIT 1"
        ).fetchone()
        reason = connection.execute(
            "SELECT COUNT(*) FROM pilot_candidate_accession_reasons WHERE reason_code = "
            "'REVIEW_PILOT_AMENDMENT_PURPOSE_UNPROVEN' AND reason_scope = 'amendment'"
        ).fetchone()[0]
    assert amendment["amendment_purpose_category"] is None
    assert amendment["amendment_purpose_evidence_level"] == "unproven"
    assert amendment["amendment_purpose_resolution_sha256"] is None
    assert amendment["amendment_purpose_quota_eligible"] == 0
    assert original["amendment_purpose_evidence_level"] == "unavailable"
    assert reason == 1


@pytest.mark.parametrize("level", ["unproven", "review_required", "conflicting", "unavailable"])
def test_no_non_provisional_purpose_level_can_be_quota_eligible(
    catalog: Path, tmp_path: Path, level: str
) -> None:
    """Decision 014 §6, enforced by migration 0009 rather than by convention."""
    frozen = _build(catalog, tmp_path)
    with connect(catalog, writer=True) as connection, pytest.raises(sqlite3.DatabaseError):
        connection.execute(
            "UPDATE pilot_candidate_accessions SET amendment_purpose_quota_eligible = 1, "
            "amendment_purpose_evidence_level = ? WHERE snapshot_id = ?",
            (level, frozen.snapshot_id),  # type: ignore[attr-defined]
        )


def test_the_cited_observation_digest_recomputes_from_persisted_evidence(
    catalog: Path, tmp_path: Path
) -> None:
    frozen = _build(catalog, tmp_path)
    with connect(catalog) as connection:
        persisted = sorted(
            {
                str(row[0])
                for row in connection.execute(
                    "SELECT source_observation_id FROM pilot_candidate_entity_evidence "
                    "UNION SELECT source_observation_id FROM pilot_candidate_accession_evidence"
                ).fetchall()
            }
        )
    assert tuple(persisted) == frozen.cited_observation_ids  # type: ignore[attr-defined]


def test_no_operational_value_reaches_the_snapshot_identity(catalog: Path, tmp_path: Path) -> None:
    """A different ``census_run_id`` over identical content keeps one identity."""
    first = _build(catalog, tmp_path)
    other = tmp_path / "catalog-2.sqlite3"
    with connect(other, writer=True) as connection:
        apply_migrations(connection)
        _seed_reference(connection)
        _seed_census(connection)
        with transaction(connection) as active:
            active.execute(
                "INSERT INTO ops_ingestion_jobs (job_id, job_kind, job_state, stage, "
                "started_at_utc, detail) VALUES ('job-other', 'sec_census', 'completed', "
                "'M2.2', ?, '')",
                (_AT,),
            )
    with CatalogWriter(other, tmp_path / "locks-2") as writer:
        second = build_and_freeze_candidate_snapshot(
            writer=writer,
            inputs=CandidateSnapshotInputs(
                census_run_id="job-other",
                coverage_start=_INPUTS.coverage_start,
                coverage_end=_INPUTS.coverage_end,
                as_of_date=_INPUTS.as_of_date,
            ),
        )
    assert second.snapshot_id == first.snapshot_id  # type: ignore[attr-defined]
    assert second.candidate_snapshot_sha256 == first.candidate_snapshot_sha256  # type: ignore[attr-defined]


# ==========================================================================
# Decision 072: the corrected full-index route, end to end
# ==========================================================================

_INDEX_ACCESSION_DASHED = "0000000001-20-000001"
_INDEX_ACCESSION_PLAIN = "0000000001" + "20" + "000001"


def _company_index_bytes(rows: tuple[tuple[str, int], ...]) -> bytes:
    """A synthetic ``company.idx`` in the shape the accepted parser reads."""
    header = (
        "Company Name                  Form Type   CIK         Date Filed  File Name\n"
        + "-" * 100
        + "\n"
    )
    body = "".join(
        f"{name:<30}{'10-K':<12}{cik:<12}{'2020-03-01':<12}"
        f"edgar/data/{cik}/{_INDEX_ACCESSION_DASHED}.txt\n"
        for name, cik in rows
    )
    return (header + body).encode("utf-8")


def _materialize_full_index(
    catalog: Path, tmp_path: Path, rows: tuple[tuple[str, int], ...]
) -> None:
    """Run the real offline driver over a synthetic index object -- not a stub."""
    tree = DataTree.from_root(tmp_path / "data")
    relative = "raw/sec/indexes/company_2020_QTR1.idx"
    target = tree.data_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _company_index_bytes(rows)
    target.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "INSERT INTO census_source_observations (observation_id, source_id, "
            "request_identity, requested_url, purpose, retrieved_at_utc, outcome, "
            "stored_sha256, logical_sha256, content_sha256, stored_size_bytes, "
            "content_size_bytes, storage_representation, relative_storage_path, "
            "parser_version, recorded_at_utc) VALUES ('obs-index-1', "
            "'sec_full_index_company', 'req/index/1', 'https://example.invalid/company.idx', "
            "'census', ?, 'stored_new', ?, ?, ?, ?, ?, 'identical', ?, 'company-idx/1.0', ?)",
            (_AT, digest, digest, digest, len(payload), len(payload), relative, _AT),
        )
        active.execute(
            "INSERT INTO census_plan_sources (census_run_id, source_instance_id, source_id, "
            "request_identity, required, source_scope, retrieval_state, snapshot_state, "
            "parser_state, catalog_state, qa_state, unresolved_blocking_reasons_json, "
            "observation_id, successful_terminal, updated_at_utc) VALUES (?, 'base|index', "
            "'sec_full_index_company', 'req/index/1', 1, 'base', 'retrieved', 'verified', "
            "'not_started', 'committed', 'passed', '[]', 'obs-index-1', 1, ?)",
            (_RUN, _AT),
        )
    with CatalogWriter(catalog, tmp_path / "index-locks") as writer:
        run_offline_metadata_parse(writer=writer, tree=tree)


def test_a_full_index_co_registrant_reaches_the_candidate_registrant_rows(
    catalog: Path, tmp_path: Path
) -> None:
    """Decision 072 §3: the corrected route, through production code end to end."""
    _materialize_full_index(
        catalog, tmp_path, (("ALPHA TECHNOLOGIES INC", 1), ("CO REGISTRANT LLC", 2))
    )
    frozen = _build(catalog, tmp_path)
    with connect(catalog) as connection:
        registrants = connection.execute(
            "SELECT registrant_cik_numeric, role, is_anchor FROM "
            "pilot_candidate_accession_registrants WHERE accession_plain = ? "
            "ORDER BY registrant_cik_numeric",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchall()
        flag = connection.execute(
            "SELECT multi_registrant FROM pilot_candidate_accessions WHERE accession_plain = ?",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchone()[0]
    # **Decision 083 R58**: a genuinely multi-registrant accession has NO anchor. Both
    # substantive registrants are 'associated', neither is promoted, and the scalar the
    # schema used to demand is NULL rather than filled with an arbitrary CIK.
    assert [(int(row["registrant_cik_numeric"]), str(row["role"])) for row in registrants] == [
        (1, "associated"),
        (2, "associated"),
    ]
    assert sum(int(row["is_anchor"]) for row in registrants) == 0
    assert flag == 1
    with connect(catalog) as connection:
        anchor, completeness = connection.execute(
            "SELECT anchor_cik_numeric, registrant_set_completeness "
            "FROM pilot_candidate_accessions WHERE accession_plain = ?",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchone()
    assert anchor is None
    assert completeness == "established"
    assert frozen.snapshot_id  # type: ignore[attr-defined]


def test_the_accepted_decision_019_loader_accepts_the_associated_registrant(
    catalog: Path, tmp_path: Path
) -> None:
    """The registrant set must survive the accepted S5.2 mapping, not just the write."""
    _materialize_full_index(
        catalog, tmp_path, (("ALPHA TECHNOLOGIES INC", 1), ("CO REGISTRANT LLC", 2))
    )
    frozen = _build(catalog, tmp_path)
    with connect(catalog) as connection:
        loaded = load_frozen_joint_candidates(connection, frozen.snapshot_id)  # type: ignore[attr-defined]
    candidate = next(
        item for item in loaded.accessions if item.accession_plain == _INDEX_ACCESSION_PLAIN
    )
    assert candidate.multi_registrant == 1
    assert candidate.multi_registrant_evidence_level == "provisional"


def test_without_the_full_index_route_the_accession_is_single_registrant(
    catalog: Path, tmp_path: Path
) -> None:
    """The regression the old category-C behaviour would have produced."""
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        flag = connection.execute(
            "SELECT multi_registrant FROM pilot_candidate_accessions WHERE accession_plain = ?",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchone()[0]
        roles = connection.execute(
            "SELECT DISTINCT role FROM pilot_candidate_accession_registrants"
        ).fetchall()
    assert flag == 0
    assert [str(row[0]) for row in roles] == ["anchor"]


def test_a_submitter_only_registrant_never_makes_the_flag_true(
    catalog: Path, tmp_path: Path
) -> None:
    """Decision 019 §6.2 / **R23** §5.2: submitter-only never contributes."""
    with connect(catalog, writer=True) as connection, transaction(connection) as active:
        active.execute(
            "UPDATE census_accessions SET submitter_cik_numeric = 2 WHERE accession_plain = ?",
            (_INDEX_ACCESSION_PLAIN,),
        )
    _build(catalog, tmp_path)
    with connect(catalog) as connection:
        rows = connection.execute(
            "SELECT role FROM pilot_candidate_accession_registrants "
            "WHERE accession_plain = ? ORDER BY registrant_cik_numeric",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchall()
        flag = connection.execute(
            "SELECT multi_registrant FROM pilot_candidate_accessions WHERE accession_plain = ?",
            (_INDEX_ACCESSION_PLAIN,),
        ).fetchone()[0]
    assert [str(row[0]) for row in rows] == ["anchor", "submitter_only"]
    assert flag == 0


def test_the_multi_registrant_quota_is_not_deferred() -> None:
    """**R24**: the only accepted M2.3 quota deferral stays the difficult-package key."""
    assert QUOTA_KEY_MULTI_REGISTRANT_ACCESSIONS not in APPROVED_DEFERRED_QUOTA_KEYS
    assert set(APPROVED_DEFERRED_QUOTA_KEYS) == {DEFERRED_QUOTA_KEY}
