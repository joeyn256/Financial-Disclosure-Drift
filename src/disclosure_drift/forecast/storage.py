"""Storage forecasting and capacity gates (assignment section 21).

Three scenarios are produced from measured pilot samples: ``base_case``,
``high_storage_case``, and ``high_failure_case``. Broad ingestion stays prohibited
unless local free space is at least 2.0 times the projected peak working set and
backup free space is at least 1.2 times the projected preserved corpus.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from disclosure_drift.errors import GateFailureError

__all__ = [
    "BACKUP_FREE_SPACE_MULTIPLE",
    "LOCAL_FREE_SPACE_MULTIPLE",
    "PERCENTILES",
    "AccessionMeasurement",
    "CapacityVerdict",
    "Distribution",
    "ScenarioForecast",
    "StorageForecast",
    "build_forecast",
    "describe",
    "evaluate_capacity",
]

LOCAL_FREE_SPACE_MULTIPLE: Final = 2.0
BACKUP_FREE_SPACE_MULTIPLE: Final = 1.2
PERCENTILES: Final[tuple[int, ...]] = (75, 90, 95)
_HIGH_STORAGE_PERCENTILE: Final = 95
_HIGH_FAILURE_RETRY_MULTIPLE: Final = 2.0
_HIGH_FAILURE_QUARANTINE_SHARE: Final = 0.10


@dataclass(frozen=True, slots=True)
class AccessionMeasurement:
    """Measured cost of one ingested accession."""

    accession_plain: str
    requests: int
    document_count: int
    complete_submission_bytes: int
    primary_document_bytes: int
    xbrl_bytes: int
    exhibit_and_image_bytes: int
    uncompressed_bytes: int
    compressed_bytes: int
    download_seconds: float
    parse_seconds: float

    @property
    def preserved_bytes(self) -> int:
        """Bytes retained on disk after deterministic compression."""
        return self.compressed_bytes


@dataclass(frozen=True, slots=True)
class Distribution:
    """Summary statistics required by the assignment."""

    minimum: float
    median: float
    mean: float
    p75: float
    p90: float
    p95: float
    maximum: float
    count: int

    def as_mapping(self) -> Mapping[str, float]:
        """Render the summary as an ordered mapping."""
        return {
            "minimum": self.minimum,
            "median": self.median,
            "mean": self.mean,
            "p75": self.p75,
            "p90": self.p90,
            "p95": self.p95,
            "maximum": self.maximum,
        }


def describe(values: Sequence[float]) -> Distribution:
    """Return the required summary statistics for ``values``.

    Percentiles use the nearest-rank method so results are reproducible without a
    numerical dependency.
    """
    if not values:
        message = "a forecast distribution needs at least one measurement"
        raise GateFailureError(message)
    ordered = sorted(float(value) for value in values)
    return Distribution(
        minimum=ordered[0],
        median=_percentile(ordered, 50),
        mean=sum(ordered) / len(ordered),
        p75=_percentile(ordered, 75),
        p90=_percentile(ordered, 90),
        p95=_percentile(ordered, 95),
        maximum=ordered[-1],
        count=len(ordered),
    )


def _percentile(ordered: Sequence[float], percentile: int) -> float:
    if len(ordered) == 1:
        return ordered[0]
    rank = max(1, min(len(ordered), round(percentile / 100 * len(ordered) + 0.5)))
    return ordered[rank - 1]


@dataclass(frozen=True, slots=True)
class ScenarioForecast:
    """One projected scenario."""

    name: str
    accessions: int
    projected_requests: int
    projected_preserved_bytes: int
    projected_peak_working_set_bytes: int
    projected_download_hours: float
    projected_parse_hours: float
    assumptions: str


@dataclass(frozen=True, slots=True)
class StorageForecast:
    """The three required scenarios plus the measured distributions."""

    sample_size: int
    target_accessions: int
    distributions: Mapping[str, Distribution]
    scenarios: Mapping[str, ScenarioForecast]

    @property
    def base_case(self) -> ScenarioForecast:
        """The central projection."""
        return self.scenarios["base_case"]

    @property
    def high_storage_case(self) -> ScenarioForecast:
        """The tail-heavy storage projection."""
        return self.scenarios["high_storage_case"]

    @property
    def high_failure_case(self) -> ScenarioForecast:
        """The retry-and-quarantine-heavy projection."""
        return self.scenarios["high_failure_case"]


def build_forecast(
    measurements: Sequence[AccessionMeasurement],
    target_accessions: int,
    *,
    staging_peak_share: float = 0.05,
    catalog_bytes_per_accession: int = 12_000,
    audit_bytes_per_accession: int = 4_000,
) -> StorageForecast:
    """Build the three scenarios from measured pilot accessions."""
    if target_accessions <= 0:
        message = "target_accessions must be positive"
        raise GateFailureError(message)

    preserved = [float(item.preserved_bytes) for item in measurements]
    uncompressed = [float(item.uncompressed_bytes) for item in measurements]
    requests = [float(item.requests) for item in measurements]
    documents = [float(item.document_count) for item in measurements]
    exhibits = [float(item.exhibit_and_image_bytes) for item in measurements]
    download = [item.download_seconds for item in measurements]
    parse = [item.parse_seconds for item in measurements]

    distributions = {
        "preserved_bytes": describe(preserved),
        "uncompressed_bytes": describe(uncompressed),
        "requests_per_accession": describe(requests),
        "documents_per_accession": describe(documents),
        "exhibit_bytes": describe(exhibits),
        "download_seconds": describe(download),
        "parse_seconds": describe(parse),
    }

    overhead = catalog_bytes_per_accession + audit_bytes_per_accession

    def scenario(
        name: str,
        per_accession_bytes: float,
        request_multiple: float,
        quarantine_share: float,
        assumptions: str,
    ) -> ScenarioForecast:
        preserved_total = per_accession_bytes * target_accessions * (1 + quarantine_share)
        peak = preserved_total * (1 + staging_peak_share) + overhead * target_accessions
        return ScenarioForecast(
            name=name,
            accessions=target_accessions,
            projected_requests=int(
                distributions["requests_per_accession"].mean * target_accessions * request_multiple
            ),
            projected_preserved_bytes=int(preserved_total + overhead * target_accessions),
            projected_peak_working_set_bytes=int(peak),
            projected_download_hours=(
                distributions["download_seconds"].mean * target_accessions * request_multiple / 3600
            ),
            projected_parse_hours=distributions["parse_seconds"].mean * target_accessions / 3600,
            assumptions=assumptions,
        )

    scenarios = {
        "base_case": scenario(
            "base_case",
            distributions["preserved_bytes"].mean,
            1.0,
            0.0,
            "mean measured preserved bytes, no extra retries, no quarantine growth",
        ),
        "high_storage_case": scenario(
            "high_storage_case",
            distributions["preserved_bytes"].p95,
            1.0,
            0.02,
            f"p{_HIGH_STORAGE_PERCENTILE} measured preserved bytes with tail-heavy exhibits",
        ),
        "high_failure_case": scenario(
            "high_failure_case",
            distributions["preserved_bytes"].p90,
            _HIGH_FAILURE_RETRY_MULTIPLE,
            _HIGH_FAILURE_QUARANTINE_SHARE,
            "doubled requests from retries and a ten percent quarantine share",
        ),
    }

    return StorageForecast(
        sample_size=len(measurements),
        target_accessions=target_accessions,
        distributions=distributions,
        scenarios=scenarios,
    )


@dataclass(frozen=True, slots=True)
class CapacityVerdict:
    """Whether measured free space permits broad ingestion."""

    local_free_bytes: int
    backup_free_bytes: int
    required_local_bytes: int
    required_backup_bytes: int

    @property
    def local_ok(self) -> bool:
        """Whether the data volume has enough headroom."""
        return self.local_free_bytes >= self.required_local_bytes

    @property
    def backup_ok(self) -> bool:
        """Whether the backup volume has enough headroom."""
        return self.backup_free_bytes >= self.required_backup_bytes

    @property
    def permits_broad_ingestion(self) -> bool:
        """Broad ingestion is permitted only when both thresholds pass."""
        return self.local_ok and self.backup_ok

    def require(self) -> None:
        """Raise unless both capacity thresholds pass.

        Raises:
            GateFailureError: capacity is insufficient; scope or storage must change.
        """
        if self.permits_broad_ingestion:
            return
        message = (
            "capacity thresholds fail, so broad ingestion remains prohibited: "
            f"local free {self.local_free_bytes} < required {self.required_local_bytes}"
            if not self.local_ok
            else (
                "capacity thresholds fail, so broad ingestion remains prohibited: "
                f"backup free {self.backup_free_bytes} < required {self.required_backup_bytes}"
            )
        )
        raise GateFailureError(message)


def evaluate_capacity(
    forecast: StorageForecast,
    local_free_bytes: int,
    backup_free_bytes: int,
    *,
    scenario: str = "high_storage_case",
) -> CapacityVerdict:
    """Compare free space against the required multiples for ``scenario``."""
    projection = forecast.scenarios[scenario]
    return CapacityVerdict(
        local_free_bytes=local_free_bytes,
        backup_free_bytes=backup_free_bytes,
        required_local_bytes=int(
            projection.projected_peak_working_set_bytes * LOCAL_FREE_SPACE_MULTIPLE
        ),
        required_backup_bytes=int(
            projection.projected_preserved_bytes * BACKUP_FREE_SPACE_MULTIPLE
        ),
    )
