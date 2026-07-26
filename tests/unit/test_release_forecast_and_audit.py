"""Release hashing and manifests, storage forecasting, and the divergence audit."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from disclosure_drift.audit.cohort_divergence import build_divergence_audit
from disclosure_drift.errors import GateFailureError
from disclosure_drift.forecast.storage import (
    BACKUP_FREE_SPACE_MULTIPLE,
    LOCAL_FREE_SPACE_MULTIPLE,
    AccessionMeasurement,
    build_forecast,
    describe,
    evaluate_capacity,
)
from disclosure_drift.release.hashing import hash_release, hash_table, normalize_value
from disclosure_drift.release.manifest import (
    RELEASE_SCHEMA_VERSION,
    GateOutcome,
    build_manifest,
    diff_releases,
)
from disclosure_drift.sec.calendar import CalendarProvenance, StaticOperatingCalendar
from disclosure_drift.sec.temporal import acceptance_timestamps, assign_cohorts

ET = ZoneInfo("America/New_York")
COLUMNS = ("accession_plain", "filing_date_sec", "official_filing_temporal_cohort")
ROWS = [
    {
        "accession_plain": "000032019324000001",
        "filing_date_sec": date(2024, 2, 15),
        "official_filing_temporal_cohort": "primary_test",
    },
    {
        "accession_plain": "000078901921000002",
        "filing_date_sec": date(2021, 7, 30),
        "official_filing_temporal_cohort": "development",
    },
]


def business_days(first: date, last: date) -> list[date]:
    days: list[date] = []
    current = first
    while current <= last:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def calendar(first: date, last: date) -> StaticOperatingCalendar:
    return StaticOperatingCalendar.from_days(
        business_days(first, last),
        CalendarProvenance(source_kind="synthetic_fixture", description="synthetic"),
    )


# --------------------------------------------------------------------------- #
# Normalized hashing
# --------------------------------------------------------------------------- #
def test_row_order_does_not_change_the_table_hash() -> None:
    forward = hash_table("inventory_accessions", COLUMNS, ROWS)
    backward = hash_table("inventory_accessions", COLUMNS, list(reversed(ROWS)))
    assert forward.normalized_content_sha256 == backward.normalized_content_sha256
    assert forward.row_count == 2


def test_column_order_changes_the_table_hash() -> None:
    reordered = tuple(reversed(COLUMNS))
    assert (
        hash_table("inventory_accessions", COLUMNS, ROWS).normalized_content_sha256
        != hash_table("inventory_accessions", reordered, ROWS).normalized_content_sha256
    )


def test_table_name_is_part_of_the_hash() -> None:
    assert (
        hash_table("a", COLUMNS, ROWS).normalized_content_sha256
        != hash_table("b", COLUMNS, ROWS).normalized_content_sha256
    )


def test_null_is_distinct_from_empty_string() -> None:
    with_null = [{"value": None}]
    with_empty = [{"value": ""}]
    assert (
        hash_table("t", ("value",), with_null).normalized_content_sha256
        != hash_table("t", ("value",), with_empty).normalized_content_sha256
    )


def test_timestamps_are_normalized_to_utc() -> None:
    eastern = datetime(2024, 2, 15, 12, 0, tzinfo=ET)
    same_instant = eastern.astimezone(UTC)
    assert normalize_value(eastern) == normalize_value(same_instant)
    assert normalize_value(eastern).endswith("Z")


def test_naive_timestamps_are_refused() -> None:
    with pytest.raises(GateFailureError, match="naive datetimes"):
        normalize_value(datetime(2024, 2, 15, 12, 0))  # noqa: DTZ001


def test_dates_render_as_iso_and_booleans_as_bits() -> None:
    assert normalize_value(date(2024, 2, 15)) == "2024-02-15"
    assert normalize_value(True) == "1"
    assert normalize_value(False) == "0"


def test_release_hash_is_order_independent_across_tables() -> None:
    first = hash_table("alpha", COLUMNS, ROWS)
    second = hash_table("beta", COLUMNS, ROWS[:1])
    assert hash_release([first, second]) == hash_release([second, first])


def test_building_twice_from_the_same_state_is_identical() -> None:
    build_one = [hash_table("alpha", COLUMNS, ROWS), hash_table("beta", COLUMNS, ROWS[:1])]
    build_two = [hash_table("beta", COLUMNS, ROWS[:1]), hash_table("alpha", COLUMNS, ROWS)]
    assert hash_release(build_one) == hash_release(build_two)


# --------------------------------------------------------------------------- #
# Manifests
# --------------------------------------------------------------------------- #
def manifest(gates: list[GateOutcome], frozen: bool = False) -> object:
    built = build_manifest(
        "release-0001",
        "2026-07-26T00:00:00Z",
        [hash_table("inventory_accessions", COLUMNS, ROWS)],
        gates,
    )
    if not frozen:
        return built
    return build_manifest(
        "release-0001",
        "2026-07-26T00:00:00Z",
        [hash_table("inventory_accessions", COLUMNS, ROWS)],
        gates,
    )


def test_manifest_carries_schema_version_and_content_hash() -> None:
    built = manifest([GateOutcome("sqlite_integrity", "pass", True)])
    assert built.release_schema_version == RELEASE_SCHEMA_VERSION
    assert len(built.release_content_sha256) == 64
    assert built.can_freeze
    built.require_freezable()


def test_blocking_gate_failure_prevents_freezing() -> None:
    built = manifest(
        [
            GateOutcome("sqlite_integrity", "pass", True),
            GateOutcome("cohort_divergence_explained", "fail", True),
        ]
    )
    assert not built.can_freeze
    with pytest.raises(GateFailureError, match="cohort_divergence_explained=fail"):
        built.require_freezable()


def test_not_run_blocking_gate_also_prevents_freezing() -> None:
    built = manifest([GateOutcome("offline_restore", "not_run", True)])
    assert not built.can_freeze


def test_non_blocking_gate_failure_permits_freezing() -> None:
    built = manifest([GateOutcome("coverage_report", "fail", False)])
    assert built.can_freeze


def test_manifest_json_is_deterministic_and_has_no_absolute_paths(tmp_path: Path) -> None:
    built = manifest([GateOutcome("sqlite_integrity", "pass", True)])
    first = built.to_json()
    assert first == built.to_json()
    path = built.write(tmp_path)
    assert path.name == "release-0001_manifest.json"
    assert "/Users/" not in first
    assert "/home/" not in first


def test_frozen_manifest_may_not_be_rewritten(tmp_path: Path) -> None:
    built = build_manifest(
        "release-0002",
        "2026-07-26T00:00:00Z",
        [hash_table("inventory_accessions", COLUMNS, ROWS)],
        [GateOutcome("sqlite_integrity", "pass", True)],
    )
    built.write(tmp_path)
    frozen = build_manifest(
        "release-0002",
        "2026-07-26T00:00:00Z",
        [hash_table("inventory_accessions", COLUMNS, ROWS)],
        [GateOutcome("sqlite_integrity", "pass", True)],
    )
    object.__setattr__(frozen, "frozen_at_utc", "2026-07-26T01:00:00Z")
    with pytest.raises(GateFailureError, match="may not be rewritten"):
        frozen.write(tmp_path)


def test_release_diff_reports_added_removed_and_changed_tables() -> None:
    earlier = [hash_table("alpha", COLUMNS, ROWS), hash_table("gamma", COLUMNS, ROWS)]
    later = [hash_table("alpha", COLUMNS, ROWS[:1]), hash_table("beta", COLUMNS, ROWS)]
    kinds = {entry.table_name: entry.diff_kind for entry in diff_releases(earlier, later)}
    assert kinds == {"alpha": "changed", "beta": "added", "gamma": "removed"}


def test_identical_releases_produce_no_diff() -> None:
    tables = [hash_table("alpha", COLUMNS, ROWS)]
    assert diff_releases(tables, tables) == ()


# --------------------------------------------------------------------------- #
# Storage forecast
# --------------------------------------------------------------------------- #
def measurement(index: int, preserved: int) -> AccessionMeasurement:
    return AccessionMeasurement(
        accession_plain=f"00000000002400{index:04d}",
        requests=8,
        document_count=25,
        complete_submission_bytes=preserved * 3,
        primary_document_bytes=preserved,
        xbrl_bytes=preserved // 4,
        exhibit_and_image_bytes=preserved // 2,
        uncompressed_bytes=preserved * 4,
        compressed_bytes=preserved,
        download_seconds=6.0,
        parse_seconds=1.5,
    )


def test_distribution_reports_every_required_statistic() -> None:
    summary = describe([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    keys = set(summary.as_mapping())
    assert keys == {"minimum", "median", "mean", "p75", "p90", "p95", "maximum"}
    assert summary.minimum == 1
    assert summary.maximum == 10
    assert summary.p90 >= summary.p75 >= summary.median


def test_empty_measurements_are_refused() -> None:
    with pytest.raises(GateFailureError, match="at least one measurement"):
        describe([])


def test_three_scenarios_are_produced_and_ordered() -> None:
    measurements = [measurement(index, 1_000_000 * (index + 1)) for index in range(10)]
    forecast = build_forecast(measurements, target_accessions=1_000)
    assert set(forecast.scenarios) == {"base_case", "high_storage_case", "high_failure_case"}
    assert (
        forecast.high_storage_case.projected_preserved_bytes
        > forecast.base_case.projected_preserved_bytes
    )
    assert forecast.high_failure_case.projected_requests > forecast.base_case.projected_requests
    assert forecast.sample_size == 10
    assert forecast.base_case.accessions == 1_000


def test_capacity_gate_uses_the_approved_multiples() -> None:
    measurements = [measurement(index, 1_000_000) for index in range(5)]
    forecast = build_forecast(measurements, target_accessions=100)
    projection = forecast.high_storage_case
    verdict = evaluate_capacity(
        forecast,
        local_free_bytes=int(projection.projected_peak_working_set_bytes * 3),
        backup_free_bytes=int(projection.projected_preserved_bytes * 2),
    )
    assert verdict.permits_broad_ingestion
    assert verdict.required_local_bytes == int(
        projection.projected_peak_working_set_bytes * LOCAL_FREE_SPACE_MULTIPLE
    )
    assert verdict.required_backup_bytes == int(
        projection.projected_preserved_bytes * BACKUP_FREE_SPACE_MULTIPLE
    )
    verdict.require()


def test_insufficient_capacity_blocks_broad_ingestion() -> None:
    measurements = [measurement(index, 1_000_000) for index in range(5)]
    forecast = build_forecast(measurements, target_accessions=100)
    verdict = evaluate_capacity(forecast, local_free_bytes=1, backup_free_bytes=1)
    assert not verdict.permits_broad_ingestion
    with pytest.raises(GateFailureError, match="broad ingestion remains prohibited"):
        verdict.require()


def test_zero_target_is_refused() -> None:
    with pytest.raises(GateFailureError, match="must be positive"):
        build_forecast([measurement(0, 1)], target_accessions=0)


# --------------------------------------------------------------------------- #
# Cohort-divergence audit
# --------------------------------------------------------------------------- #
def entry(
    accession: str,
    form: str,
    filing: date,
    acceptance_raw: str | None,
    calendar_range: tuple[date, date] | None = None,
) -> tuple[str, str, object, str, tuple[str, ...]]:
    acceptance = None if acceptance_raw is None else acceptance_timestamps(acceptance_raw)
    operating = None if calendar_range is None else calendar(*calendar_range)
    assignment = assign_cohorts(filing, acceptance, calendar=operating)
    return (accession, form, assignment, "same_day_acceptance", ("sgml_header",))


def test_audit_counts_and_splits_divergence() -> None:
    audit = build_divergence_audit(
        [
            entry("a1", "10-K", date(2024, 2, 15), "20240215120000"),
            entry(
                "a2",
                "10-K",
                date(2024, 3, 4),
                "20240301201500",
                (date(2024, 2, 26), date(2024, 3, 15)),
            ),
            entry(
                "a3",
                "10-K/A",
                date(2022, 1, 3),
                "20211231201500",
                (date(2021, 12, 20), date(2022, 1, 14)),
            ),
        ]
    )
    assert audit.total_accessions == 3
    assert audit.date_divergence_total == 2
    assert audit.cohort_boundary_crossings == 1
    assert audit.by_original_or_amendment == {"original": 1, "amendment": 1}
    assert audit.by_acceptance_year == {"2024": 1, "2021": 1}
    assert audit.by_official_filing_year == {"2024": 1, "2022": 1}
    assert audit.by_reason["same_day_filing"] == 1
    assert audit.requires_manual_review


def test_explained_divergence_alone_does_not_block_release() -> None:
    audit = build_divergence_audit(
        [
            entry(
                "a1",
                "10-K",
                date(2024, 3, 4),
                "20240301201500",
                (date(2024, 2, 26), date(2024, 3, 15)),
            )
        ]
    )
    assert audit.unexplained_total == 0
    assert not audit.blocks_release


def test_unexplained_divergence_blocks_release() -> None:
    audit = build_divergence_audit(
        [
            entry(
                "a1",
                "10-K",
                date(2024, 3, 7),
                "20240304090000",
                (date(2024, 2, 26), date(2024, 3, 15)),
            )
        ]
    )
    assert audit.unexplained_total == 1
    assert audit.blocks_release
    assert audit.gate_results()["cohort_divergence_explained"] == "fail"


def test_coverage_boundary_divergence_is_reported_separately() -> None:
    audit = build_divergence_audit([entry("a1", "10-K", date(2027, 1, 4), "20261231120000")])
    assert audit.coverage_boundary_divergences == 1
    assert audit.cohort_boundary_crossings == 0
    assert audit.gate_results()["coverage_boundary_divergence"] == "fail"


def test_2024_membership_change_requires_recorded_approval() -> None:
    entries = [
        entry(
            "a1",
            "10-K",
            date(2024, 1, 2),
            "20231229201500",
            (date(2023, 12, 20), date(2024, 1, 15)),
        )
    ]
    without = build_divergence_audit(entries)
    assert len(without.primary_test_records) == 1
    assert without.unapproved_primary_test_records
    assert without.blocks_release
    assert without.gate_results()["primary_test_membership_approved"] == "fail"

    approved = build_divergence_audit(entries, approvals={"a1": "approved 2026-07-26 by owner"})
    assert not approved.unapproved_primary_test_records
    assert approved.gate_results()["primary_test_membership_approved"] == "pass"


def test_records_carry_the_evidence_required_by_the_audit() -> None:
    audit = build_divergence_audit(
        [
            entry(
                "a1",
                "10-K",
                date(2022, 1, 3),
                "20211231201500",
                (date(2021, 12, 20), date(2022, 1, 14)),
            )
        ]
    )
    record = audit.boundary_crossing_records[0]
    assert record.official_filing_temporal_cohort == "transition"
    assert record.accepted_temporal_cohort == "development"
    assert record.availability_basis == "same_day_acceptance"
    assert record.source_observations == ("sgml_header",)
    assert record.divergence_reason == "expected_after_cutoff_rollover"
    assert "REVIEW_COHORT_DIVERGENCE_BOUNDARY_CROSSING" in record.reason_codes
