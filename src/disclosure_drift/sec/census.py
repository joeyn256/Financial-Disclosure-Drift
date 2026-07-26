"""Transactional parsed-record and normalized registrant census catalog writes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Any, Final, Literal

from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_resolution import (
    RESOLUTION_POLICY_VERSION,
    AccessionFieldObservation,
    AccessionResolution,
    resolve_accession,
)
from disclosure_drift.sec.calendar import CALENDAR_DERIVATION_VERSION
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.parsers.base import ParsedRecord, ParseOutcome, QuarantinedRecord
from disclosure_drift.sec.parsers.submissions import HistoricalFileReference
from disclosure_drift.sec.parsers.versions import require_parser_version
from disclosure_drift.sec.temporal import acceptance_date_sec, cohort_label_for_value
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction, utc_now

CANONICAL_FIELD_BY_SOURCE_FIELD: Mapping[str, str] = {
    # submissions documents
    "form": "form",
    "filingDate": "official_filing_date",
    "reportDate": "report_date",
    "acceptanceDateTime": "acceptance_timestamp",
    "cik": "registrant_cik",
    "primaryDocument": "primary_document_metadata",
    # full company index (lower authority; corroborates or conflicts only)
    "form_type": "form",
    "date_filed": "official_filing_date",
    "cik_padded": "registrant_cik",
}
"""Source-native field name to Decision 012 canonical field name.

A source field with no entry here contributes no canonical authority. That is
deliberate: an unmapped field cannot silently start resolving a canonical value.
"""

RESOLVABLE_SOURCE_IDS: frozenset[str] = frozenset(
    {
        "sec_bulk_submissions",
        "sec_submissions_entity",
        "sec_submissions_historical",
        "sec_full_index_company",
    }
)
"""Sources whose observations may take part in accession-field resolution.

Identity-alias sources are excluded here as well as being level 4 in Decision 012, so
they cannot contribute even a competing value for a filing field.
"""

__all__ = [
    "DISCOVERY_FORMS",
    "NEGATIVE_CONTROL_FORMS",
    "CensusCatalog",
    "ParserWriteResult",
    "QAMetric",
]

DISCOVERY_FORMS: Final[frozenset[str]] = frozenset({"10-K", "10-K/A", "10-KT", "10-KT/A"})
NEGATIVE_CONTROL_FORMS: Final[frozenset[str]] = frozenset({"20-F", "20-F/A", "40-F", "40-F/A"})
MetricStatus = Literal[
    "value",
    "zero",
    "unavailable",
    "failed",
    "blocked",
    "unknown",
    "not_retrieved",
]


@dataclass(frozen=True, slots=True)
class ParserWriteResult:
    """Result of one logical parser-run write."""

    parser_run_id: str
    parsed: int
    quarantined: int
    normalized_registrants: int
    normalized_accessions: int
    already_present: bool = False


@dataclass(frozen=True, slots=True)
class QAMetric:
    """One deterministic QA value with explicit missing-state semantics."""

    name: str
    status: MetricStatus
    value: int | None
    detail: str
    dimension: Mapping[str, object]

    def as_record(self) -> Mapping[str, object]:
        return {
            "metric_name": self.name,
            "status": self.status,
            "value": self.value,
            "detail": self.detail,
            "dimension": dict(sorted(self.dimension.items())),
        }


class CensusCatalog:
    """Single-writer persistence from parsed source records into normalized census rows."""

    def __init__(
        self,
        writer: CatalogWriter,
        *,
        approved_2024_transitions: Mapping[str, bool] | None = None,
    ) -> None:
        """Create the catalog writer.

        Args:
            writer: The single logical catalog writer holding the lease.
            approved_2024_transitions: Accessions whose entry into or exit from the 2024
                primary-test cohort has been explicitly approved. Absent approval the
                transition is recorded and blocked (Decision 012 section 6).
        """
        self._writer = writer
        self._approved_2024_transitions = dict(approved_2024_transitions or {})

    def persist(
        self,
        outcome: ParseOutcome,
        *,
        historical_references: Iterable[HistoricalFileReference] = (),
        source_observation_id: str | None = None,
    ) -> ParserWriteResult:
        """Persist a parser outcome and its normalized observations atomically."""
        observation_id = self._observation_id(outcome, source_observation_id)
        parser_run_id = _stable_id(
            "parser-run", observation_id, outcome.parser_id, outcome.parser_version
        )
        existing = self._writer.connection.execute(
            "SELECT parsed_count, quarantined_count FROM census_parser_runs "
            "WHERE parser_run_id = ?",
            (parser_run_id,),
        ).fetchone()
        if existing is not None:
            return ParserWriteResult(
                parser_run_id=parser_run_id,
                parsed=int(existing["parsed_count"]),
                quarantined=int(existing["quarantined_count"]),
                normalized_registrants=0,
                normalized_accessions=0,
                already_present=True,
            )

        # Fail closed before writing provenance: the version recorded on a parser run
        # must be the version the implementation actually is.
        authoritative = require_parser_version(
            outcome.parser_id,
            outcome.parser_version,
            context=f"parser run for observation {observation_id}",
        )
        started = utc_now()
        registrants = 0
        accessions = 0
        with transaction(self._writer.connection) as connection:
            connection.execute(
                "INSERT INTO census_parser_runs "
                "(parser_run_id, source_observation_id, parser_id, parser_version, "
                "started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
                "outcome, summary_json) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'completed', '{}')",
                (
                    parser_run_id,
                    observation_id,
                    outcome.parser_id,
                    authoritative,
                    started,
                    started,
                ),
            )
            for record in outcome.records:
                parsed_id = self._insert_record(connection, parser_run_id, record, outcome)
                normalized = self._normalize_record(connection, parsed_id, record, started)
                registrants += normalized[0]
                accessions += normalized[1]
            for quarantined_record in outcome.quarantined:
                self._insert_quarantine(connection, parser_run_id, quarantined_record, started)
            self._insert_structural(connection, parser_run_id, observation_id, outcome, started)
            self._insert_historical_references(connection, observation_id, historical_references)
            # A structural failure means at least one nested region yielded an unknown
            # count. The run is recorded as failed so that no consumer can read its
            # record count -- including zero -- as a real observation.
            if outcome.structural_failures:
                state = "failed"
            elif outcome.quarantined:
                state = "completed_with_quarantine"
            else:
                state = "completed"
            connection.execute(
                "UPDATE census_parser_runs SET finished_at_utc = ?, parsed_count = ?, "
                "quarantined_count = ?, outcome = ?, summary_json = ? "
                "WHERE parser_run_id = ?",
                (
                    utc_now(),
                    len(outcome.records),
                    len(outcome.quarantined),
                    state,
                    _json(dict(outcome.summary())),
                    parser_run_id,
                ),
            )
        return ParserWriteResult(
            parser_run_id=parser_run_id,
            parsed=len(outcome.records),
            quarantined=len(outcome.quarantined),
            normalized_registrants=registrants,
            normalized_accessions=accessions,
        )

    def qa_metrics(self, census_run_id: str) -> tuple[QAMetric, ...]:
        """Build and persist the deterministic Stage M2.2 QA summary."""
        connection = self._writer.connection
        metrics: tuple[QAMetric, ...] = (
            _count_metric(connection, "source_observations", "census_source_observations"),
            _count_metric(
                connection,
                "usable_snapshots",
                "census_source_observations",
                "outcome IN ('stored_new','unchanged_content','superseded','reused_snapshot')",
            ),
            _count_metric(connection, "canonical_ciks", "census_registrants"),
            _count_metric(
                connection, "alias_and_history_observations", "census_registrant_observations"
            ),
            _count_metric(
                connection,
                "sic_coverage",
                "census_registrant_observations",
                "observation_kind = 'sic'",
            ),
            _count_metric(
                connection,
                "fiscal_year_end_coverage",
                "census_registrant_observations",
                "observation_kind = 'fiscal_year_end'",
            ),
            _count_metric(connection, "accessions", "census_accessions"),
            _count_metric(connection, "amendments", "census_accessions", "is_amendment = 1"),
            _count_metric(
                connection,
                "originals",
                "census_accessions",
                "is_discovery_form = 1 AND is_amendment = 0",
            ),
            _count_metric(connection, "historical_references", "census_historical_references"),
            _count_metric(
                connection,
                "malformed_historical_references",
                "census_malformed_historical_references",
            ),
            _count_metric(
                connection,
                "structural_regions_observed",
                "census_structural_observations",
            ),
            _count_metric(
                connection,
                "structural_genuine_zeros",
                "census_structural_observations",
                "is_genuine_zero = 1",
            ),
            _count_metric(
                connection,
                "structural_unknown_counts",
                "census_structural_observations",
                "count_is_trustworthy = 0",
            ),
            _count_metric(
                connection,
                "parser_runs_failed_structurally",
                "census_parser_runs",
                "outcome = 'failed'",
            ),
            _count_metric(
                connection,
                "acceptance_date_available",
                "census_accessions",
                "acceptance_date_sec IS NOT NULL",
            ),
            _count_metric(
                connection,
                "filing_date_available",
                "census_accessions",
                "filing_date_sec IS NOT NULL",
            ),
            _count_metric(
                connection,
                "cohort_assignments",
                "census_accessions",
                "official_filing_temporal_cohort NOT IN ('unresolved')",
            ),
            _count_metric(
                connection,
                "cohort_unresolved",
                "census_accessions",
                "official_filing_temporal_cohort = 'unresolved'",
            ),
            _count_metric(
                connection,
                "cohort_support_2009",
                "census_accessions",
                "official_filing_temporal_cohort = 'support_2009'",
            ),
            _count_metric(
                connection,
                "cohort_out_of_scope",
                "census_accessions",
                "official_filing_temporal_cohort = 'out_of_scope'",
            ),
            _count_metric(
                connection,
                "date_divergences",
                "census_accessions",
                "date_divergence_reason IS NOT NULL",
            ),
            _count_metric(
                connection,
                "schema_drift",
                "census_parsed_records",
                "unknown_fields_json <> '[]'",
            ),
            _count_metric(connection, "malformed_and_quarantined", "census_quarantined_records"),
            _count_metric(
                connection,
                "retained_control_candidates",
                "census_accessions",
                "is_negative_control = 1",
            ),
            self._blocking_metric(connection),
        )
        metrics += self._source_status_metrics(connection)
        metrics += self._snapshot_status_metrics(connection)
        metrics += self._accession_form_metrics(connection)
        metrics += self._grouped_metrics(
            connection,
            name="historical_reference_coverage",
            table="census_historical_references",
            dimension_column="retrieval_status",
            dimension_name="status",
        )
        metrics += self._grouped_metrics(
            connection,
            name="cohort_assignments",
            table="census_accessions",
            dimension_column="official_filing_temporal_cohort",
            dimension_name="cohort",
        )
        metrics += self._grouped_metrics(
            connection,
            name="date_divergence_reasons",
            table="census_accessions",
            dimension_column="date_divergence_reason",
            dimension_name="reason",
        )
        metrics += self._calendar_metrics(connection)
        recorded = utc_now()
        with transaction(connection) as writable:
            for metric in metrics:
                writable.execute(
                    "INSERT OR REPLACE INTO census_qa_metrics "
                    "(census_run_id, metric_name, dimension_json, metric_status, "
                    "metric_value, detail, recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        census_run_id,
                        metric.name,
                        _json(metric.dimension),
                        metric.status,
                        metric.value,
                        metric.detail,
                        recorded,
                    ),
                )
        return metrics

    def _observation_id(
        self,
        outcome: ParseOutcome,
        supplied_observation_id: str | None,
    ) -> str:
        locations = [record.location.observation_id for record in outcome.records]
        locations.extend(record.location.observation_id for record in outcome.quarantined)
        locations.extend(item.location.observation_id for item in outcome.structural)
        unique: set[str] = set(locations)
        if supplied_observation_id is not None:
            unique.add(supplied_observation_id)
        if len(unique) != 1:
            message = (
                f"parser outcome must belong to exactly one source observation; found "
                f"{sorted(unique)}"
            )
            raise ValueError(message)
        observation_id = unique.pop()
        exists = self._writer.connection.execute(
            "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        if exists is None:
            message = f"source observation {observation_id!r} is not in the catalog"
            raise ValueError(message)
        return observation_id

    @staticmethod
    def _insert_record(
        connection: sqlite3.Connection,
        parser_run_id: str,
        record: ParsedRecord,
        outcome: ParseOutcome,
    ) -> str:
        location = record.location
        parsed_id = _stable_id(
            "parsed",
            location.observation_id,
            record.parser_id,
            record.parser_version,
            record.native_identity,
            record.record_sha256,
            location.member_name or "",
            location.record_path or "",
            str(location.record_index),
        )
        duplicate = record.duplicate_indicator or any(
            identity == record.native_identity for identity, _ in outcome.duplicate_identities
        )
        connection.execute(
            "INSERT INTO census_parsed_records "
            "(parsed_record_id, parser_run_id, source_observation_id, native_identity, "
            "record_sha256, member_name, record_path, record_index, payload_json, "
            "unknown_fields_json, warnings_json, reason_codes_json, duplicate_indicator, "
            "conflict_indicator, recorded_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                parsed_id,
                parser_run_id,
                location.observation_id,
                record.native_identity,
                record.record_sha256,
                location.member_name,
                location.record_path,
                location.record_index,
                _json(record.payload),
                _json(record.unknown_fields),
                _json(record.normalization_warnings),
                _json(record.reason_codes),
                int(duplicate),
                int(record.conflict_indicator),
                utc_now(),
            ),
        )
        return parsed_id

    @staticmethod
    def _insert_quarantine(
        connection: sqlite3.Connection,
        parser_run_id: str,
        record: QuarantinedRecord,
        recorded: str,
    ) -> None:
        location = record.location
        quarantine_id = _stable_id(
            "quarantine",
            parser_run_id,
            location.describe(),
            record.native_identity or "",
            record.detail,
        )
        connection.execute(
            "INSERT INTO census_quarantined_records "
            "(quarantine_record_id, parser_run_id, source_observation_id, native_identity, "
            "member_name, record_path, record_index, reason_codes_json, detail, "
            "raw_excerpt, recorded_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                quarantine_id,
                parser_run_id,
                location.observation_id,
                record.native_identity,
                location.member_name,
                location.record_path,
                location.record_index,
                _json(record.reason_codes),
                record.detail,
                record.raw_excerpt,
                recorded,
            ),
        )

    def _normalize_record(
        self,
        connection: sqlite3.Connection,
        parsed_id: str,
        record: ParsedRecord,
        observed: str,
    ) -> tuple[int, int]:
        identity = record.native_identity
        if identity.startswith("registrant:"):
            return self._normalize_registrant(connection, parsed_id, record, observed), 0
        if identity.startswith(("ticker_alias:", "exchange_alias:")):
            return self._normalize_alias(connection, parsed_id, record, observed), 0
        if identity.startswith("accession:"):
            return 0, self._normalize_accession(connection, parsed_id, record, observed)
        if identity.startswith("sic:"):
            self._normalize_sic(connection, record, observed)
        if identity.startswith("calendar_"):
            self._normalize_calendar(connection, record)
        return 0, 0

    def _normalize_registrant(
        self,
        connection: sqlite3.Connection,
        parsed_id: str,
        record: ParsedRecord,
        observed: str,
    ) -> int:
        cik = record.payload.get("cik")
        try:
            numeric, padded = normalize_cik(str(cik))
        except IdentifierError:
            return 0
        self._upsert_registrant(connection, numeric, padded, observed)
        fields: list[tuple[str, object, str | None, str | None, str]] = []
        fields.append(("company_name", record.payload.get("name"), None, None, "name"))
        fields.extend(self._former_name_fields(record.payload.get("formerNames")))
        fields.extend(
            ("ticker", value, None, None, "tickers")
            for value in _items(record.payload.get("tickers"))
        )
        fields.extend(
            ("exchange", value, None, None, "exchanges")
            for value in _items(record.payload.get("exchanges"))
        )
        fields.extend(
            [
                ("sic", record.payload.get("sic"), None, None, "sic"),
                (
                    "fiscal_year_end",
                    record.payload.get("fiscalYearEnd"),
                    None,
                    None,
                    "fiscalYearEnd",
                ),
                ("entity_type", record.payload.get("entityType"), None, None, "entityType"),
                ("filing_status", record.payload.get("category"), None, None, "category"),
            ]
        )
        for kind, value, valid_from, valid_to, source_field in fields:
            self._insert_history(
                connection,
                numeric,
                kind,
                value,
                valid_from,
                valid_to,
                record.location.observation_id,
                parsed_id,
                source_field,
                observed,
            )
        self._candidate_edges(connection, record.location.observation_id, kind="company_name")
        self._candidate_edges(connection, record.location.observation_id, kind="ticker")
        return 1

    def _normalize_alias(
        self,
        connection: sqlite3.Connection,
        parsed_id: str,
        record: ParsedRecord,
        observed: str,
    ) -> int:
        raw_cik = record.payload.get("cik") or record.payload.get("cik_str")
        try:
            numeric, padded = normalize_cik(str(raw_cik))
        except IdentifierError:
            return 0
        self._upsert_registrant(connection, numeric, padded, observed)
        name = record.payload.get("name") or record.payload.get("title")
        ticker = record.payload.get("ticker")
        exchange = record.payload.get("exchange")
        for kind, value, source in (
            ("company_name", name, "name/title"),
            ("ticker", ticker, "ticker"),
            ("exchange", exchange, "exchange"),
        ):
            self._insert_history(
                connection,
                numeric,
                kind,
                value,
                None,
                None,
                record.location.observation_id,
                parsed_id,
                source,
                observed,
            )
        self._candidate_edges(connection, record.location.observation_id, kind="company_name")
        self._candidate_edges(connection, record.location.observation_id, kind="ticker")
        return 1

    def _normalize_accession(
        self,
        connection: sqlite3.Connection,
        parsed_id: str,
        record: ParsedRecord,
        observed: str,
    ) -> int:
        accession_raw = _text(record.payload.get("accessionNumber"))
        form = _text(record.payload.get("form"))
        cik_raw = record.payload.get("cik")
        if accession_raw is None or form is None or cik_raw is None:
            return 0
        try:
            accession = parse_accession(accession_raw)
            numeric, padded = normalize_cik(str(cik_raw))
        except IdentifierError:
            return 0
        self._upsert_registrant(connection, numeric, padded, observed)
        filing_date = _date_text(record.payload.get("filingDate"))
        acceptance_raw = _text(record.payload.get("acceptanceDateTime"))
        acceptance_date = _acceptance_date(acceptance_raw)
        # Canonical fields are a *derived projection*. This insert seeds the row from
        # the observation so foreign keys resolve, but every canonical value is
        # overwritten by resolve_persisted_accessions() from the persisted resolution.
        # Nothing downstream may read these seed values as authoritative.
        filing_cohort = _cohort(filing_date)
        accepted_cohort = _cohort(acceptance_date)
        divergence = _divergence(filing_date, acceptance_date)
        values = (
            accession.plain,
            accession.dashed,
            numeric,
            accession.submitter_cik_numeric,
            form,
            int(form.endswith("/A")),
            int(form in DISCOVERY_FORMS),
            int(form in NEGATIVE_CONTROL_FORMS),
            filing_date,
            _date_text(record.payload.get("reportDate")),
            acceptance_raw,
            acceptance_date,
            filing_cohort,
            accepted_cohort,
            divergence,
            _text(record.payload.get("primaryDocument")),
            _flag(record.payload.get("isXBRL")),
            _flag(record.payload.get("isInlineXBRL")),
            record.location.observation_id,
            parsed_id,
            observed,
            observed,
        )
        connection.execute(
            "INSERT INTO census_accessions "
            "(accession_plain, accession_dashed, registrant_cik_numeric, "
            "submitter_cik_numeric, form_type, is_amendment, is_discovery_form, "
            "is_negative_control, filing_date_sec, report_date, "
            "acceptance_datetime_sec_raw, acceptance_date_sec, "
            "official_filing_temporal_cohort, accepted_temporal_cohort, "
            "date_divergence_reason, primary_document_name, xbrl_flag, inline_xbrl_flag, "
            "source_observation_id, parsed_record_id, first_observed_at_utc, "
            "latest_observed_at_utc) VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(accession_plain) DO UPDATE SET "
            "latest_observed_at_utc = excluded.latest_observed_at_utc",
            values,
        )
        for field, value in sorted(record.payload.items()):
            connection.execute(
                "INSERT OR IGNORE INTO census_accession_observations "
                "(accession_observation_id, accession_plain, source_observation_id, "
                "parsed_record_id, field_name, raw_value_json, observed_at_utc, "
                "conflict_indicator) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _stable_id(
                        "accession-observation",
                        accession.plain,
                        record.location.observation_id,
                        parsed_id,
                        field,
                    ),
                    accession.plain,
                    record.location.observation_id,
                    parsed_id,
                    field,
                    _json(value),
                    observed,
                    0,
                ),
            )
        self._mark_accession_conflicts(connection, accession.plain)
        return 1

    # -- Decision 012 resolution pass --------------------------------------- #
    def resolve_persisted_accessions(
        self,
        accessions: Sequence[str] | None = None,
    ) -> Mapping[str, AccessionResolution]:
        """Resolve canonical accession fields from every persisted observation.

        This is the only writer of canonical values in ``census_accessions``. It runs
        after observations are persisted, reads them back from the catalog rather than
        from whatever the current parse produced, and therefore rebuilds the identical
        result on a rerun or after a restart.

        Args:
            accessions: Restrict to these accessions; default is every accession that
                has at least one persisted observation.

        Returns:
            The resolution per accession, keyed by plain accession number.
        """
        connection = self._writer.connection
        targets = (
            list(accessions)
            if accessions is not None
            else [
                str(row["accession_plain"])
                for row in connection.execute(
                    "SELECT DISTINCT accession_plain FROM census_accession_observations "
                    "ORDER BY accession_plain"
                ).fetchall()
            ]
        )
        resolved: dict[str, AccessionResolution] = {}
        for accession_plain in targets:
            observations = self._field_observations(connection, accession_plain)
            prior = self._prior_filing_dates(connection, accession_plain)
            resolution = resolve_accession(
                accession_plain,
                observations,
                prior_filing_dates=prior,
                approved_2024_transition=self._approved_2024_transitions.get(
                    accession_plain, False
                ),
            )
            with transaction(connection) as write:
                self._persist_resolution(write, resolution)
                self._project_canonical(write, resolution)
            resolved[accession_plain] = resolution
        return resolved

    @staticmethod
    def _field_observations(
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> list[AccessionFieldObservation]:
        """Build Decision 012 observations from persisted source-native rows.

        Ordering here is only for reproducibility of the *input list*; the resolver's
        ranking never consults it, so the canonical result is unchanged by it.
        """
        rows = connection.execute(
            "SELECT o.accession_observation_id, o.source_observation_id, o.field_name, "
            "o.raw_value_json, o.observed_at_utc, s.source_id, s.logical_sha256 "
            "FROM census_accession_observations AS o "
            "JOIN census_source_observations AS s "
            "  ON s.observation_id = o.source_observation_id "
            "WHERE o.accession_plain = ? "
            "ORDER BY o.accession_observation_id",
            (accession_plain,),
        ).fetchall()
        observations: list[AccessionFieldObservation] = []
        for row in rows:
            canonical = CANONICAL_FIELD_BY_SOURCE_FIELD.get(str(row["field_name"]))
            if canonical is None:
                continue
            source_id = str(row["source_id"])
            if source_id not in RESOLVABLE_SOURCE_IDS:
                continue
            try:
                value = json.loads(str(row["raw_value_json"]))
            except (TypeError, ValueError):
                continue
            if value is None or str(value).strip() == "":
                continue
            observations.append(
                AccessionFieldObservation(
                    observation_id=str(row["accession_observation_id"]),
                    source_id=source_id,
                    accession_plain=accession_plain,
                    field_name=canonical,
                    value=value,
                    observed_at_utc=str(row["observed_at_utc"]),
                    source_version=(
                        None if row["logical_sha256"] is None else str(row["logical_sha256"])[:16]
                    ),
                )
            )
        return observations

    @staticmethod
    def _prior_filing_dates(
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> list[str]:
        """Return filing dates from earlier persisted resolutions.

        Earlier derived resolutions are retained, so a correction's cohort consequences
        can be recorded rather than overwritten.
        """
        rows = connection.execute(
            "SELECT resolved_value FROM census_accession_field_resolutions "
            "WHERE accession_plain = ? AND field_name = 'official_filing_date' "
            "AND status IN ('resolved', 'resolved_by_correction') "
            "ORDER BY resolved_at_utc",
            (accession_plain,),
        ).fetchall()
        return [str(row["resolved_value"]) for row in rows if row["resolved_value"]]

    @staticmethod
    def _persist_resolution(
        connection: sqlite3.Connection,
        resolution: AccessionResolution,
    ) -> None:
        """Write every field resolution and the cohort consequence."""
        now = utc_now()
        for name, item in sorted(resolution.fields.items()):
            connection.execute(
                "INSERT INTO census_accession_field_resolutions "
                "(accession_plain, field_name, status, resolved_value, authority_class, "
                "policy_version, winning_observation_ids_json, "
                "competing_observation_ids_json, correction_evidence_id, "
                "reason_codes_json, is_material, blocks_dependents, detail, "
                "resolution_sha256, resolved_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(accession_plain, field_name, policy_version) DO UPDATE SET "
                "status = excluded.status, resolved_value = excluded.resolved_value, "
                "authority_class = excluded.authority_class, "
                "winning_observation_ids_json = excluded.winning_observation_ids_json, "
                "competing_observation_ids_json = excluded.competing_observation_ids_json, "
                "correction_evidence_id = excluded.correction_evidence_id, "
                "reason_codes_json = excluded.reason_codes_json, "
                "is_material = excluded.is_material, "
                "blocks_dependents = excluded.blocks_dependents, "
                "detail = excluded.detail, "
                "resolution_sha256 = excluded.resolution_sha256",
                (
                    resolution.accession_plain,
                    name,
                    item.status,
                    None if item.value is None else str(item.value),
                    item.authority,
                    RESOLUTION_POLICY_VERSION,
                    _json(list(item.winning_observation_ids)),
                    _json(list(item.competing_observation_ids)),
                    item.correction_evidence_id,
                    _json(list(item.reason_codes)),
                    int(item.is_material),
                    int(item.blocks_dependents),
                    item.detail,
                    item.resolution_hash(),
                    now,
                ),
            )
        connection.execute(
            "INSERT INTO census_accession_cohort_resolutions "
            "(accession_plain, policy_version, official_filing_temporal_cohort, "
            "accepted_temporal_cohort, prior_filing_cohorts_json, "
            "cohort_boundary_crossed, requires_2024_approval, approval_reference, "
            "reason_codes_json, resolution_sha256, resolved_at_utc) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(accession_plain, policy_version) DO UPDATE SET "
            "official_filing_temporal_cohort = excluded.official_filing_temporal_cohort, "
            "accepted_temporal_cohort = excluded.accepted_temporal_cohort, "
            "prior_filing_cohorts_json = excluded.prior_filing_cohorts_json, "
            "cohort_boundary_crossed = excluded.cohort_boundary_crossed, "
            "requires_2024_approval = excluded.requires_2024_approval, "
            "reason_codes_json = excluded.reason_codes_json, "
            "resolution_sha256 = excluded.resolution_sha256",
            (
                resolution.accession_plain,
                RESOLUTION_POLICY_VERSION,
                resolution.official_filing_cohort,
                resolution.accepted_cohort,
                _json(list(resolution.prior_filing_cohorts)),
                int(resolution.cohort_boundary_crossed),
                int(resolution.requires_2024_approval),
                None,
                _json(list(resolution.reason_codes)),
                resolution.resolution_hash(),
                now,
            ),
        )

    @staticmethod
    def _project_canonical(
        connection: sqlite3.Connection,
        resolution: AccessionResolution,
    ) -> None:
        """Overwrite canonical accession fields from the persisted resolution.

        An unresolved material field is projected as ``NULL`` together with the
        ``unresolved`` cohort label, so no consumer can mistake a conflict for a value.
        """
        form = resolution.value("form")
        filing_date = resolution.value("official_filing_date")
        connection.execute(
            "UPDATE census_accessions SET "
            "form_type = COALESCE(?, form_type), "
            "is_amendment = CASE WHEN ? IS NULL THEN is_amendment ELSE ? END, "
            "filing_date_sec = ?, "
            "report_date = ?, "
            "acceptance_datetime_sec_raw = ?, "
            "official_filing_temporal_cohort = ?, "
            "accepted_temporal_cohort = ?, "
            "primary_document_name = ? "
            "WHERE accession_plain = ?",
            (
                None if form is None else str(form),
                None if form is None else str(form),
                None if form is None else int(str(form).endswith("/A")),
                None if filing_date is None else str(filing_date),
                _optional_text(resolution.value("report_date")),
                _optional_text(resolution.value("acceptance_timestamp")),
                resolution.official_filing_cohort,
                resolution.accepted_cohort,
                _optional_text(resolution.value("primary_document_metadata")),
                resolution.accession_plain,
            ),
        )

    @staticmethod
    def _normalize_sic(
        connection: sqlite3.Connection,
        record: ParsedRecord,
        observed: str,
    ) -> None:
        code = _text(record.payload.get("sic"))
        description = _text(record.payload.get("description"))
        if code is None or description is None:
            return
        source = connection.execute(
            "SELECT requested_url FROM census_source_observations WHERE observation_id = ?",
            (record.location.observation_id,),
        ).fetchone()
        connection.execute(
            "INSERT OR REPLACE INTO reference_sic_codes "
            "(sic_code, description, office, source_snapshot_id, source_url, "
            "retrieved_at_utc) VALUES (?, ?, ?, ?, ?, ?)",
            (
                code,
                description,
                _text(record.payload.get("office")),
                record.location.observation_id,
                str(source["requested_url"]) if source is not None else "unknown",
                observed,
            ),
        )

    @staticmethod
    def _normalize_calendar(connection: sqlite3.Connection, record: ParsedRecord) -> None:
        day = _date_text(record.payload.get("date"))
        status = _text(record.payload.get("status"))
        if day is None or status not in {"operating", "non_operating", "unknown"}:
            return
        evidence_id = _text(record.payload.get("evidence_id")) or record.native_identity
        connection.execute(
            "INSERT OR IGNORE INTO census_calendar_days "
            "(calendar_date, status, source_observation_id, evidence_id, "
            "derivation_version, conflicting, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                day,
                status,
                record.location.observation_id,
                evidence_id,
                CALENDAR_DERIVATION_VERSION,
                int(record.conflict_indicator),
                "; ".join(record.normalization_warnings),
            ),
        )

    @staticmethod
    def _upsert_registrant(
        connection: sqlite3.Connection,
        numeric: int,
        padded: str,
        observed: str,
    ) -> None:
        connection.execute(
            "INSERT INTO census_registrants "
            "(cik_numeric, cik_padded, first_observed_at_utc, latest_observed_at_utc) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(cik_numeric) DO UPDATE SET "
            "latest_observed_at_utc = excluded.latest_observed_at_utc",
            (numeric, padded, observed, observed),
        )

    @staticmethod
    def _insert_history(
        connection: sqlite3.Connection,
        numeric: int,
        kind: str,
        value: object,
        valid_from: str | None,
        valid_to: str | None,
        observation_id: str,
        parsed_id: str,
        source_field: str,
        observed: str,
    ) -> None:
        text = _text(value)
        if text is None:
            return
        history_id = _stable_id(
            "history",
            str(numeric),
            kind,
            text,
            valid_from or "",
            valid_to or "",
            observation_id,
            parsed_id,
        )
        connection.execute(
            "INSERT OR IGNORE INTO census_registrant_observations "
            "(registrant_observation_id, cik_numeric, observation_kind, value_text, "
            "valid_from, valid_to, source_observation_id, parsed_record_id, source_field, "
            "observed_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                history_id,
                numeric,
                kind,
                text,
                valid_from,
                valid_to,
                observation_id,
                parsed_id,
                source_field,
                observed,
            ),
        )

    @staticmethod
    def _former_name_fields(
        value: object,
    ) -> list[tuple[str, object, str | None, str | None, str]]:
        fields: list[tuple[str, object, str | None, str | None, str]] = []
        for item in _items(value):
            if isinstance(item, Mapping):
                fields.append(
                    (
                        "former_name",
                        item.get("name"),
                        _date_text(item.get("from")),
                        _date_text(item.get("to")),
                        "formerNames",
                    )
                )
            else:
                fields.append(("former_name", item, None, None, "formerNames"))
        return fields

    @staticmethod
    def _insert_historical_references(
        connection: sqlite3.Connection,
        observation_id: str,
        references: Iterable[HistoricalFileReference],
    ) -> None:
        """Persist every reference, valid or malformed.

        A malformed entry cannot be stored in ``census_historical_references`` because
        that table's primary key requires a usable file name, so it is preserved in
        ``census_malformed_historical_references`` with its raw entry intact. Nothing
        is discarded, and a valid sibling is still recorded as retrievable.
        """
        for reference in references:
            row = connection.execute(
                "SELECT payload_json FROM census_parsed_records "
                "WHERE source_observation_id = ? AND native_identity LIKE 'registrant:%' "
                "ORDER BY parsed_record_id LIMIT 1",
                (observation_id,),
            ).fetchone()
            cik: str | None = None
            if row is not None:
                payload = json.loads(str(row["payload_json"]))
                try:
                    cik = normalize_cik(str(payload.get("cik")))[1]
                except IdentifierError:
                    cik = None

            if not reference.is_retrievable or reference.name is None:
                connection.execute(
                    "INSERT OR IGNORE INTO census_malformed_historical_references "
                    "(malformed_reference_id, source_observation_id, registrant_cik_padded, "
                    "observed_name, member_name, record_index, problems_json, "
                    "unknown_fields_json, raw_entry_json, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        _stable_id(
                            "malformed-historical",
                            observation_id,
                            str(reference.location.member_name),
                            str(reference.location.record_index),
                        ),
                        observation_id,
                        cik,
                        reference.name,
                        reference.location.member_name,
                        reference.location.record_index,
                        _json(list(reference.problems)),
                        _json(list(reference.unknown_fields)),
                        _json(dict(reference.raw_entry or {})),
                        utc_now(),
                    ),
                )
                continue
            if cik is None:
                continue
            connection.execute(
                "INSERT OR IGNORE INTO census_historical_references "
                "(source_observation_id, registrant_cik_padded, historical_file, "
                "filing_count, filing_from, filing_to, member_name, record_index, "
                "retrieval_status, is_retrievable, unknown_fields_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'not_retrieved', 1, ?)",
                (
                    observation_id,
                    cik,
                    reference.name,
                    reference.filing_count,
                    reference.filing_from,
                    reference.filing_to,
                    reference.location.member_name,
                    reference.location.record_index,
                    _json(list(reference.unknown_fields)),
                ),
            )

    @staticmethod
    def _insert_structural(
        connection: sqlite3.Connection,
        parser_run_id: str,
        observation_id: str,
        outcome: ParseOutcome,
        recorded_at: str,
    ) -> None:
        """Persist the typed structural verdict for every nested region observed."""
        for item in outcome.structural:
            connection.execute(
                "INSERT OR IGNORE INTO census_structural_observations "
                "(structural_observation_id, parser_run_id, source_observation_id, region, "
                "state, observed_type, member_name, record_path, row_count, "
                "count_is_trustworthy, is_genuine_zero, reason_codes_json, detail, "
                "raw_excerpt, recorded_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    _stable_id(
                        "structural",
                        observation_id,
                        parser_run_id,
                        item.region,
                        str(item.location.member_name),
                    ),
                    parser_run_id,
                    observation_id,
                    item.region,
                    item.state,
                    item.observed_type,
                    item.location.member_name,
                    item.location.record_path,
                    item.row_count,
                    int(item.count_is_trustworthy),
                    int(item.is_genuine_zero),
                    _json(list(item.reason_codes)),
                    item.detail,
                    item.raw_excerpt,
                    recorded_at,
                ),
            )

    @staticmethod
    def _candidate_edges(
        connection: sqlite3.Connection,
        observation_id: str,
        *,
        kind: str,
    ) -> None:
        rows = connection.execute(
            "SELECT value_text, GROUP_CONCAT(DISTINCT printf('%010d', cik_numeric)) AS ciks "
            "FROM census_registrant_observations "
            "WHERE source_observation_id = ? AND observation_kind = ? "
            "GROUP BY value_text HAVING COUNT(DISTINCT cik_numeric) > 1",
            (observation_id, kind),
        ).fetchall()
        for row in rows:
            ciks = sorted(str(row["ciks"]).split(","))
            for index, left in enumerate(ciks):
                for right in ciks[index + 1 :]:
                    connection.execute(
                        "INSERT OR IGNORE INTO census_candidate_lineage_edges "
                        "(candidate_edge_id, from_cik_padded, to_cik_padded, evidence_kind, "
                        "evidence_value, source_observation_id, status, detail) "
                        "VALUES (?, ?, ?, ?, ?, ?, 'candidate_only', ?)",
                        (
                            _stable_id(
                                "candidate-edge",
                                left,
                                right,
                                kind,
                                str(row["value_text"]),
                                observation_id,
                            ),
                            left,
                            right,
                            kind,
                            str(row["value_text"]),
                            observation_id,
                            "shared alias is explicit review evidence only; CIKs remain separate",
                        ),
                    )

    @staticmethod
    def _mark_accession_conflicts(
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> None:
        fields = connection.execute(
            "SELECT field_name FROM census_accession_observations "
            "WHERE accession_plain = ? GROUP BY field_name "
            "HAVING COUNT(DISTINCT raw_value_json) > 1",
            (accession_plain,),
        ).fetchall()
        for row in fields:
            connection.execute(
                "UPDATE census_accession_observations SET conflict_indicator = 1 "
                "WHERE accession_plain = ? AND field_name = ?",
                (accession_plain, str(row["field_name"])),
            )

    @staticmethod
    def _blocking_metric(connection: sqlite3.Connection) -> QAMetric:
        row = connection.execute(
            "SELECT COUNT(*) AS rows FROM census_observation_reasons r "
            "JOIN reference_reason_codes c ON c.reason_code = r.reason_code "
            "WHERE c.blocks_release = 1"
        ).fetchone()
        count = int(row["rows"]) if row is not None else 0
        quarantine_rows = connection.execute(
            "SELECT reason_codes_json FROM census_quarantined_records"
        ).fetchall()
        count += sum(
            1
            for quarantine_row in quarantine_rows
            if any(
                code in REASON_CODES and REASON_CODES[code].blocks_release
                for code in json.loads(str(quarantine_row["reason_codes_json"]))
            )
        )
        status: MetricStatus = "blocked" if count else "zero"
        return QAMetric(
            name="unresolved_release_blocking_reasons",
            status=status,
            value=count,
            detail="release-blocking source-observation reasons currently retained",
            dimension={},
        )

    @staticmethod
    def _source_status_metrics(connection: sqlite3.Connection) -> tuple[QAMetric, ...]:
        from disclosure_drift.sec.source_registry import SOURCES  # noqa: PLC0415

        metrics: list[QAMetric] = []
        for source_id in sorted(SOURCES):
            row = connection.execute(
                "SELECT outcome, detail FROM census_source_observations "
                "WHERE source_id = ? ORDER BY retrieved_at_utc DESC, recorded_at_utc DESC "
                "LIMIT 1",
                (source_id,),
            ).fetchone()
            if row is None:
                status: MetricStatus = "not_retrieved"
                value = None
                detail = "no source observation exists"
            else:
                outcome = str(row["outcome"])
                status = (
                    "failed"
                    if outcome == "failed"
                    else "blocked"
                    if outcome == "quarantined"
                    else "value"
                )
                value = 1 if status == "value" else None
                detail = str(row["detail"] or outcome)
            metrics.append(
                QAMetric(
                    name="source_retrieval_status",
                    status=status,
                    value=value,
                    detail=detail,
                    dimension={"source_id": source_id},
                )
            )
        return tuple(metrics)

    @staticmethod
    def _accession_form_metrics(connection: sqlite3.Connection) -> tuple[QAMetric, ...]:
        rows = connection.execute(
            "SELECT form_type, substr(filing_date_sec, 1, 4) AS filing_year, "
            "COUNT(*) AS rows FROM census_accessions "
            "GROUP BY form_type, substr(filing_date_sec, 1, 4) "
            "ORDER BY form_type, filing_year"
        ).fetchall()
        return tuple(
            QAMetric(
                name="accessions_by_form_and_year",
                status="value" if int(row["rows"]) else "zero",
                value=int(row["rows"]),
                detail="accession count retaining originals and amendments separately",
                dimension={
                    "form": str(row["form_type"]),
                    "year": (
                        str(row["filing_year"]) if row["filing_year"] is not None else "unknown"
                    ),
                },
            )
            for row in rows
        )

    @staticmethod
    def _snapshot_status_metrics(connection: sqlite3.Connection) -> tuple[QAMetric, ...]:
        rows = connection.execute(
            "SELECT outcome, COUNT(*) AS rows FROM census_source_observations "
            "GROUP BY outcome ORDER BY outcome"
        ).fetchall()
        return tuple(
            QAMetric(
                name="snapshot_status",
                status="value" if int(row["rows"]) else "zero",
                value=int(row["rows"]),
                detail="immutable source-observation count by snapshot outcome",
                dimension={"outcome": str(row["outcome"])},
            )
            for row in rows
        )

    @staticmethod
    def _grouped_metrics(
        connection: sqlite3.Connection,
        *,
        name: str,
        table: str,
        dimension_column: str,
        dimension_name: str,
    ) -> tuple[QAMetric, ...]:
        permitted = {
            ("census_historical_references", "retrieval_status"),
            ("census_accessions", "official_filing_temporal_cohort"),
            ("census_accessions", "date_divergence_reason"),
        }
        if (table, dimension_column) not in permitted:
            message = f"unsupported grouped QA query {table}.{dimension_column}"
            raise ValueError(message)
        rows = connection.execute(
            f"SELECT {dimension_column} AS dimension, COUNT(*) AS rows "  # noqa: S608
            f"FROM {table} GROUP BY {dimension_column} ORDER BY {dimension_column}"
        ).fetchall()
        return tuple(
            QAMetric(
                name=name,
                status="value" if int(row["rows"]) else "zero",
                value=int(row["rows"]),
                detail=f"deterministic grouped count from {table}",
                dimension={
                    dimension_name: (
                        str(row["dimension"]) if row["dimension"] is not None else "unknown"
                    )
                },
            )
            for row in rows
        )

    @staticmethod
    def _calendar_metrics(connection: sqlite3.Connection) -> tuple[QAMetric, ...]:
        rows = connection.execute(
            "SELECT status, COUNT(DISTINCT calendar_date) AS rows "
            "FROM census_calendar_days GROUP BY status ORDER BY status"
        ).fetchall()
        known = {
            str(row["status"]): int(row["rows"]) for row in rows if str(row["status"]) != "unknown"
        }
        start = date(2009, 1, 1)
        end = date(2026, 12, 31)
        total = (end - start).days + 1
        known_dates_row = connection.execute(
            "SELECT COUNT(DISTINCT calendar_date) AS rows FROM census_calendar_days "
            "WHERE status IN ('operating', 'non_operating')"
        ).fetchone()
        known_dates = int(known_dates_row["rows"]) if known_dates_row is not None else 0
        metrics = [
            QAMetric(
                name="edgar_calendar_days",
                status="value" if count else "zero",
                value=count,
                detail="proven calendar dates by tri-state determination",
                dimension={"status": status},
            )
            for status, count in sorted(known.items())
        ]
        metrics.append(
            QAMetric(
                name="edgar_calendar_days",
                status="unknown" if total > known_dates else "zero",
                value=total - known_dates,
                detail=(
                    "dates in the 2009-2026 census window without a persisted proven "
                    "determination; they cannot support automatic rollover"
                ),
                dimension={"status": "unknown"},
            )
        )
        conflict_row = connection.execute(
            "SELECT COUNT(DISTINCT calendar_date) AS rows FROM census_calendar_days "
            "WHERE conflicting = 1"
        ).fetchone()
        conflicts = int(conflict_row["rows"]) if conflict_row is not None else 0
        metrics.append(
            QAMetric(
                name="edgar_calendar_conflicts",
                status="blocked" if conflicts else "zero",
                value=conflicts,
                detail="conflicting calendar determinations require review",
                dimension={},
            )
        )
        return tuple(metrics)


def _count_metric(
    connection: sqlite3.Connection,
    name: str,
    table: str,
    condition: str | None = None,
) -> QAMetric:
    sql = f"SELECT COUNT(*) AS rows FROM {table}"  # noqa: S608 - internal constants only
    if condition:
        sql += f" WHERE {condition}"
    row = connection.execute(sql).fetchone()
    count = int(row["rows"]) if row is not None else 0
    return QAMetric(
        name=name,
        status="value" if count else "zero",
        value=count,
        detail=f"deterministic count from {table}",
        dimension={},
    )


def _stable_id(*parts: str) -> str:
    value = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _items(value: object) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _date_text(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError:
        return None


def _acceptance_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return acceptance_date_sec(value).isoformat()
    except Exception:  # malformed values remain on the parsed source record
        return None


def _optional_text(value: object) -> str | None:
    """Return ``str(value)`` or ``None``, so an unresolved field projects as NULL."""
    return None if value is None else str(value)


def _cohort(value: str | None) -> str:
    """Return the persisted cohort label, never ``None`` for a valid date.

    Delegates to the canonical temporal helper so ``support_2009``, the five frozen
    cohorts, ``out_of_scope``, and ``unresolved`` all stay distinguishable. Storing
    ``NULL`` for a valid 2009 or out-of-scope date would collapse a known exclusion
    into an unknown one.
    """
    return cohort_label_for_value(value)


def _divergence(filing_date: str | None, acceptance_date: str | None) -> str | None:
    if filing_date is None or acceptance_date is None or filing_date == acceptance_date:
        return None
    return "unresolved_at_metadata_census"


def _flag(value: object) -> int | None:
    if value in (0, "0"):
        return 0
    if value in (1, "1"):
        return 1
    return None
