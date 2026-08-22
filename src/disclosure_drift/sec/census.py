"""Transactional parsed-record and normalized registrant census catalog writes."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import date
from typing import Any, Final, Literal, cast

from disclosure_drift.m3.compact_evidence import (
    FULL_EVIDENCE,
    CompactEvidencePolicy,
    ResolutionDigest,
    compact_index_payload,
    compact_parsed_payload,
    corroboration_observations,
    is_default_resolution,
    materialized_fields,
    reconstructed_observations,
)
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.accession_resolution import (
    RESOLUTION_POLICY_VERSION,
    AccessionFieldObservation,
    AccessionResolution,
    resolve_accession,
)
from disclosure_drift.sec.calendar import CALENDAR_DERIVATION_VERSION
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.parsers.base import (
    PARSER_LAYER_VERSION,
    ParsedRecord,
    ParseOutcome,
    QuarantinedRecord,
)
from disclosure_drift.sec.parsers.full_index import INDEX_ROW_PREFIX
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
    #: The state written to ``census_parser_runs.outcome``. Set by
    #: :meth:`CensusCatalog.persist_streamed`, whose caller has no merged
    #: :class:`~disclosure_drift.sec.parsers.base.ParseOutcome` left to derive it from.
    #: :meth:`CensusCatalog.persist` leaves it empty; that path still reads the outcome itself.
    run_outcome: str = ""


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


#: The most structural observations a streamed run's summary carries verbatim.
#:
#: The merged :meth:`CensusCatalog.persist` renders every structural observation into
#: ``census_parser_runs.summary_json``. On the accepted first planned source that is 1,976,418
#: observations and roughly 1.35 GB of JSON in one cell -- which exceeds SQLite's
#: ``SQLITE_MAX_LENGTH`` of 1,000,000,000 bytes outright, so the merged shape cannot produce a
#: valid row for that source at any memory budget. The detail is not lost by bounding it: every
#: observation is already persisted individually in ``census_structural_observations``, which is
#: its authoritative home, and the summary's copy was always a duplicate. What the summary keeps
#: is the subset that changes the run's meaning -- the observations whose counts may not be
#: believed -- plus an explicit accounting of what was observed, so a reader is never left to
#: infer from a short array that the source was quiet.
STREAMED_STRUCTURAL_DETAIL_LIMIT: Final = 1_000

#: How many accessions one page of :meth:`CensusCatalog._iter_observed_accessions` holds.
#: Large enough that paging costs a negligible number of extra index seeks, small enough
#: that the page itself is never a meaningful share of memory.
_ACCESSION_PAGE_SIZE: Final = 10_000

#: Batch size meaning "do not split this logical write at all".
#:
#: One transaction for the whole write is the accepted behaviour, and it stays the default
#: everywhere the operational catalog is the target: a source either lands entirely or not
#: at all, and no partially written source is ever durable. Splitting is opt-in and is for a
#: **run-local working catalog** only, where bounded durable progress is the point.
SINGLE_TRANSACTION: Final = 0


class BoundedTransaction:
    """One logical write carried out as one, or as a bounded series, of real transactions.

    A single transaction spanning an entire source is correct and is what the operational
    catalog gets. It stops being *executable* once the source is large enough: every page the
    write dirties has to stay in the journal until the one commit, so the journal grows with
    the whole source rather than with any bounded unit of work, and the page cache spills
    long before the end (the accepted D111 remediation instrument).

    With a positive ``batch_size`` this commits after that many units and immediately opens
    the next transaction. What that buys is bounded journal residency and bounded lost work
    on interruption. What it must not buy -- and does not -- is a different result: the rows,
    their identities, and their order are decided by the writer, and a commit boundary is
    only a point at which already-decided rows become durable.

    A committed batch is **execution progress, never a disposition**. Nothing here records
    that a source succeeded; the caller does that once, after the last unit, and a run
    interrupted between batches leaves committed rows and no success claim
    (the accepted D111 remediation instrument).

    ``checkpoint`` additionally truncates the write-ahead log at each boundary, which is what
    keeps the log itself bounded rather than merely the transaction. It is for a run-local
    working catalog with exactly one connection; it is not used against the operational
    catalog, where a concurrent reader legitimately holds frames the checkpoint would wait on.
    """

    __slots__ = ("_batch_size", "_checkpoint", "_connection", "_open", "_seen", "batches")

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        batch_size: int = SINGLE_TRANSACTION,
        checkpoint: bool = False,
    ) -> None:
        if batch_size < 0:
            message = f"batch size must not be negative; got {batch_size}"
            raise ValueError(message)
        self._connection = connection
        self._batch_size = batch_size
        self._checkpoint = checkpoint
        self._open = False
        self._seen = 0
        #: How many real transactions the logical write actually committed.
        self.batches = 0

    def __enter__(self) -> BoundedTransaction:
        self._begin()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> None:
        if exc_type is not None:
            self._rollback()
            return
        self._commit()

    def unit(self) -> None:
        """Count one unit of work and close the batch when it is full.

        Called between units, never inside one: the boundary is only ever at a point where
        the writer has finished everything one unit implies.
        """
        self._seen += 1
        if self._batch_size and self._seen >= self._batch_size:
            self._commit()
            self._seen = 0
            self._begin()

    def _begin(self) -> None:
        self._connection.execute("BEGIN IMMEDIATE")
        self._open = True

    def _commit(self) -> None:
        if not self._open:
            return
        if self._connection.in_transaction:
            self._connection.execute("COMMIT")
        self._open = False
        self.batches += 1
        if self._checkpoint:
            self._connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    def _rollback(self) -> None:
        if self._open and self._connection.in_transaction:
            self._connection.execute("ROLLBACK")
        self._open = False


@dataclass(slots=True)
class _StreamedRunAccumulator:
    """The bounded run-level state :meth:`CensusCatalog.persist_streamed` may retain.

    Everything ``merge_outcomes`` accumulates falls into one of three classes, and this keeps
    only the first two:

    * **Bounded by the schema or by anomalies** -- unknown field paths, normalization warnings,
      duplicate identities, required-field failures, quarantine reason codes, and historical-file
      references. Measured across the whole accepted first planned source these come to 19
      distinct unknown paths, 0 warnings, 0 duplicates, 14,250 failures, and 4,675 references.
      They are kept whole.
    * **Bounded by construction** -- counts. Kept as integers.
    * **Proportional to the source** -- the structural observations themselves, at just over two
      per archive member. Only the blocking ones are kept, and only up to
      :data:`STREAMED_STRUCTURAL_DETAIL_LIMIT`; the rows themselves are already durable before
      this sees them.

    Nothing here holds a parsed record, a payload, or an archive member, so its size does not
    follow the source.
    """

    unknown_fields: set[str] = dataclass_field(default_factory=set)
    normalization_warnings: list[str] = dataclass_field(default_factory=list)
    duplicate_identities: list[tuple[str, int]] = dataclass_field(default_factory=list)
    required_field_failures: list[tuple[str, str]] = dataclass_field(default_factory=list)
    quarantine_reason_codes: set[str] = dataclass_field(default_factory=set)
    structural_reason_codes: set[str] = dataclass_field(default_factory=set)
    historical_references: list[HistoricalFileReference] = dataclass_field(default_factory=list)
    structural_observed: int = 0
    blocking_structural: int = 0
    retained_structural: list[Mapping[str, object]] = dataclass_field(default_factory=list)

    def absorb(self, outcome: ParseOutcome, references: Sequence[HistoricalFileReference]) -> None:
        """Fold one part's outcome into the run-level state and keep nothing else."""
        self.unknown_fields.update(outcome.unknown_fields)
        self.normalization_warnings.extend(outcome.normalization_warnings)
        self.duplicate_identities.extend(outcome.duplicate_identities)
        self.required_field_failures.extend(outcome.required_field_failures)
        for quarantined in outcome.quarantined:
            self.quarantine_reason_codes.update(quarantined.reason_codes)
        self.historical_references.extend(references)
        for observed in outcome.structural:
            self.structural_observed += 1
            self.structural_reason_codes.update(observed.reason_codes)
            if not observed.blocks_success:
                continue
            self.blocking_structural += 1
            if len(self.retained_structural) < STREAMED_STRUCTURAL_DETAIL_LIMIT:
                self.retained_structural.append(observed.as_record())

    def apply_duplicate_identities(
        self, connection: sqlite3.Connection, parser_run_id: str
    ) -> None:
        """Raise ``duplicate_indicator`` for every identity any part reported as duplicated.

        The merged path decides this per record against the whole run's duplicate list, which a
        stream cannot have while its records are being written. Applying it once at the end over
        the accumulated identities reaches the same rows with the same final value, and touches
        only rows this run inserted.
        """
        identities = sorted({identity for identity, _ in self.duplicate_identities})
        if not identities:
            return
        for identity in identities:
            connection.execute(
                "UPDATE census_parsed_records SET duplicate_indicator = 1 "
                "WHERE parser_run_id = ? AND native_identity = ?",
                (parser_run_id, identity),
            )

    def reason_codes(self) -> tuple[str, ...]:
        """The run's reason codes, by the same rule :attr:`ParseOutcome.reason_codes` uses."""
        codes: set[str] = set()
        if self.unknown_fields:
            codes.add("PARSER_SCHEMA_DRIFT_OBSERVED")
        if self.duplicate_identities:
            codes.add("PARSER_DUPLICATE_SOURCE_RECORD")
        if self.required_field_failures:
            codes.add("SEC_SCHEMA_REQUIRED_FIELD_MISSING")
        codes.update(self.quarantine_reason_codes)
        codes.update(self.structural_reason_codes)
        return tuple(sorted(codes))

    def summary(
        self, *, parser_id: str, parser_version: str, parsed: int, quarantined: int
    ) -> Mapping[str, object]:
        """The streamed run summary: :meth:`ParseOutcome.summary`'s shape, bounded.

        Every key the merged summary carries is present and carries the same value, computed by
        the same rule. ``structural`` is the one array that is a subset rather than the whole,
        and ``structural_detail`` states exactly what that subset is and where the rest lives --
        so the bound is disclosed in the record itself rather than inferred from a short array.
        """
        return {
            "parser_id": parser_id,
            "parser_version": parser_version,
            "layer_version": PARSER_LAYER_VERSION,
            "counts": {
                "parsed": parsed,
                "quarantined": quarantined,
                "duplicate_identities": len(self.duplicate_identities),
                "required_field_failures": len(self.required_field_failures),
                "unknown_fields": len(self.unknown_fields),
                "normalization_warnings": len(self.normalization_warnings),
                "structural_observations": self.structural_observed,
                "structural_failures": self.blocking_structural,
            },
            "counts_are_trustworthy": self.blocking_structural == 0,
            "unknown_field_paths": sorted(self.unknown_fields),
            "normalization_warnings": list(self.normalization_warnings),
            "duplicate_identities": [list(item) for item in self.duplicate_identities],
            "required_field_failures": [list(item) for item in self.required_field_failures],
            "reason_codes": list(self.reason_codes()),
            "structural": [dict(item) for item in self.retained_structural],
            "structural_detail": {
                "scope": "blocking_only",
                "observed": self.structural_observed,
                "blocking": self.blocking_structural,
                "retained": len(self.retained_structural),
                "retention_limit": STREAMED_STRUCTURAL_DETAIL_LIMIT,
                "table": "census_structural_observations",
            },
        }


@dataclass
class ResolutionEvidence:
    """What one catalog's Decision 012 resolution produced, physically and logically (D113 §8).

    The digest is over the **logical** resolution set -- every accession's complete resolution,
    whether its rows were written or left to the reconstruction -- so it is identical under both
    evidence contracts and a single comparison proves the omission cost nothing. The counts
    beside it are the only record of the physical/logical split, which is what stops a missing
    row from looking like an accident.

    It **accumulates** across every resolution call on one ``CensusCatalog``, so a caller that
    resolves in chunks reaches the same digest and the same counts as one that resolves the
    whole catalog at once. E0 does the latter, and does it once.
    """

    digest: ResolutionDigest = dataclass_field(default_factory=ResolutionDigest)
    accessions: int = 0
    implicit: int = 0
    explicit: int = 0
    omitted_field_rows: int = 0
    materialized_field_rows: int = 0
    omitted_cohort_rows: int = 0
    materialized_cohort_rows: int = 0

    def record(self, resolution: AccessionResolution, *, implicit: bool) -> None:
        """Fold one accession's resolution in and count how it was represented."""
        self.digest.record(resolution)
        self.accessions += 1
        rows = len(resolution.fields)
        if implicit:
            self.implicit += 1
            self.omitted_field_rows += rows
            self.omitted_cohort_rows += 1
        else:
            self.explicit += 1
            self.materialized_field_rows += rows
            self.materialized_cohort_rows += 1

    def completeness_digest(self) -> str:
        """The D113 §8 resolution-completeness digest over the full logical result."""
        return self.digest.hexdigest()


class CensusCatalog:
    """Single-writer persistence from parsed source records into normalized census rows."""

    def __init__(
        self,
        writer: CatalogWriter,
        *,
        approved_2024_transitions: Mapping[str, bool] | None = None,
        compact_evidence: CompactEvidencePolicy = FULL_EVIDENCE,
    ) -> None:
        """Create the catalog writer.

        Args:
            writer: The single logical catalog writer holding the lease.
            approved_2024_transitions: Accessions whose entry into or exit from the 2024
                primary-test cohort has been explicitly approved. Absent approval the
                transition is recorded and blocked (Decision 012 section 6).
            compact_evidence: The accepted Decision 112 compact evidence contract, or the
                full-observation contract. **Full by default**, so no historical M2
                acquisition path and no operational-catalog write changes behaviour; D112 §3
                limits the ruling to E0 successor execution and this argument is that limit.
        """
        self._writer = writer
        self._approved_2024_transitions = dict(approved_2024_transitions or {})
        self._compact = compact_evidence
        self._resolution_evidence = ResolutionEvidence()

    @property
    def compact_evidence(self) -> CompactEvidencePolicy:
        """Which evidence contract this catalog writes and reads under."""
        return self._compact

    @property
    def resolution_evidence(self) -> ResolutionEvidence:
        """The D113 §8 evidence the resolution pass accumulated.

        Built under **both** contracts, because its digest is over the *logical* resolution
        set: that is what lets the full-observation path and the compact path be compared on
        one value rather than table by table.
        """
        return self._resolution_evidence

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
            # Hoisted out of the record loop: the merged outcome's duplicate list is a
            # property of the whole source, so deriving it per record was quadratic in the
            # source (accepted Decision 111 §3's defect class, in a path it did not reach).
            duplicates = frozenset(identity for identity, _ in outcome.duplicate_identities)
            for record in outcome.records:
                parsed_id = self._insert_record(
                    connection, parser_run_id, record, outcome, duplicates
                )
                normalized = self._normalize_record(connection, parsed_id, record, started)
                registrants += normalized[0]
                accessions += normalized[1]
            for quarantined_record in outcome.quarantined:
                self._insert_quarantine(connection, parser_run_id, quarantined_record, started)
            self._insert_structural(connection, parser_run_id, observation_id, outcome, started)
            self._flush_run_level_derivations(connection, observation_id)
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

    def persist_streamed(
        self,
        outcomes: Iterable[tuple[ParseOutcome, Sequence[HistoricalFileReference]]],
        *,
        parser_id: str,
        parser_version: str,
        source_observation_id: str,
        batch_size: int = SINGLE_TRANSACTION,
        checkpoint_batches: bool = False,
    ) -> ParserWriteResult:
        """Persist one logical parser run from a **stream** of per-part outcomes.

        The bounded-memory twin of :meth:`persist`, for a source whose parts are too numerous
        to merge in memory first (accepted Decision 110 §8, Workstream B). It writes the same
        one ``census_parser_runs`` row, with the same ``parser_run_id`` preimage, and the same
        rows in the same order into every other table -- but it consumes each part, writes it,
        and drops it, so nothing proportional to the whole source is ever resident.

        Three details make the streamed result identical to the merged one rather than merely
        similar:

        * **Duplicate identities are applied at the end.** ``merge_outcomes`` concatenates the
          per-part duplicate lists, so a record's run-level duplicate flag can depend on a part
          that has not been read yet. Each record is therefore inserted with its own part's
          verdict and one bounded ``UPDATE`` afterwards raises the flag for every identity any
          part reported. The flag is not part of any identity preimage, so no row's id moves.
        * **Historical references are applied at the end.** They are accumulated per part and
          written once, so a reference row's ``INSERT OR IGNORE`` cannot race a sibling part.
          They no longer *need* to run last: each reference now carries its own declaring
          registrant (accepted Decision 129 §6, D129-R4), so nothing here reads a parsed
          record to resolve a CIK. The position is retained because it is the accepted write
          order and moving it would change nothing except which rows land in which batch.
        * **Interleaving is safe.** Quarantine and structural rows go to tables that record
          normalization neither reads nor writes, so writing them per part rather than in three
          passes cannot change what normalization sees.

        The one deliberate difference is the run summary's ``structural`` array, which is
        bounded here and complete in :meth:`persist`; see :func:`_streamed_summary`.

        **Batching.** By default this is one transaction, exactly as before: a source lands
        whole or not at all. A positive ``batch_size`` splits it into that many parts per real
        transaction, which is required against a **run-local working catalog** because a single
        transaction over a source this large cannot keep its journal bounded (accepted
        the accepted D111 instrument). Batching changes durability granularity and nothing
        else -- every row, identity, and order is decided before any boundary is reached, so
        two different batch sizes produce byte-identical governed output.

        A batched run is **truthful while incomplete**: the run row is seeded ``failed``, which
        is the state the accepted vocabulary already reserves for "do not read this run's
        counts as a real observation", and it is corrected to the real terminal only after the
        last part. An interruption therefore leaves committed rows under a run that claims
        nothing, never a partial source wearing a success (the accepted D111 instrument).

        Args:
            outcomes: Each part's outcome paired with the historical-file references it named.
                Consumed exactly once, lazily.
            parser_id: The **run-level** parser id, as ``merge_outcomes`` would have set it.
            parser_version: The run-level parser version, likewise.
            source_observation_id: The one observation every part belongs to.
            batch_size: Parts per real transaction, or :data:`SINGLE_TRANSACTION` for one.
            checkpoint_batches: Truncate the write-ahead log at each batch boundary. For a
                run-local working catalog with one connection; not for the operational catalog.
        """
        observation_id = self._require_streamed_observation(source_observation_id)
        parser_run_id = _stable_id("parser-run", observation_id, parser_id, parser_version)
        existing = self._writer.connection.execute(
            "SELECT parsed_count, quarantined_count, outcome FROM census_parser_runs "
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
                run_outcome=str(existing["outcome"]),
            )

        authoritative = require_parser_version(
            parser_id,
            parser_version,
            context=f"parser run for observation {observation_id}",
        )
        started = utc_now()
        accumulator = _StreamedRunAccumulator()
        registrants = 0
        accessions = 0
        parsed = 0
        quarantined = 0
        connection = self._writer.connection
        with BoundedTransaction(
            connection, batch_size=batch_size, checkpoint=checkpoint_batches
        ) as bounded:
            # Seeded ``failed`` rather than ``completed``: with a positive batch size this row
            # is durable long before the run is over, and the accepted meaning of ``failed`` is
            # exactly "no consumer may read this run's counts -- including zero -- as a real
            # observation". A run that never reaches its last part keeps it.
            connection.execute(
                "INSERT INTO census_parser_runs "
                "(parser_run_id, source_observation_id, parser_id, parser_version, "
                "started_at_utc, finished_at_utc, parsed_count, quarantined_count, "
                "outcome, summary_json) VALUES (?, ?, ?, ?, ?, ?, 0, 0, 'failed', '{}')",
                (parser_run_id, observation_id, parser_id, authoritative, started, started),
            )
            for outcome, references in outcomes:
                part_duplicates = frozenset(
                    identity for identity, _ in outcome.duplicate_identities
                )
                for record in outcome.records:
                    self._require_streamed_location(record.location.observation_id, observation_id)
                    parsed_id = self._insert_record(
                        connection, parser_run_id, record, outcome, part_duplicates
                    )
                    normalized = self._normalize_record(connection, parsed_id, record, started)
                    registrants += normalized[0]
                    accessions += normalized[1]
                    parsed += 1
                for quarantined_record in outcome.quarantined:
                    self._require_streamed_location(
                        quarantined_record.location.observation_id, observation_id
                    )
                    self._insert_quarantine(connection, parser_run_id, quarantined_record, started)
                    quarantined += 1
                for item in outcome.structural:
                    self._require_streamed_location(item.location.observation_id, observation_id)
                self._insert_structural(connection, parser_run_id, observation_id, outcome, started)
                accumulator.absorb(outcome, references)
                # One part is one unit: the boundary is only ever reached where every row that
                # part implies has already been written.
                bounded.unit()
            accumulator.apply_duplicate_identities(connection, parser_run_id)
            self._flush_run_level_derivations(connection, observation_id)
            self._insert_historical_references(
                connection, observation_id, accumulator.historical_references
            )
            if accumulator.blocking_structural:
                state = "failed"
            elif quarantined:
                state = "completed_with_quarantine"
            else:
                state = "completed"
            connection.execute(
                "UPDATE census_parser_runs SET finished_at_utc = ?, parsed_count = ?, "
                "quarantined_count = ?, outcome = ?, summary_json = ? "
                "WHERE parser_run_id = ?",
                (
                    utc_now(),
                    parsed,
                    quarantined,
                    state,
                    _json(
                        accumulator.summary(
                            parser_id=parser_id,
                            parser_version=authoritative,
                            parsed=parsed,
                            quarantined=quarantined,
                        )
                    ),
                    parser_run_id,
                ),
            )
        return ParserWriteResult(
            parser_run_id=parser_run_id,
            parsed=parsed,
            quarantined=quarantined,
            normalized_registrants=registrants,
            normalized_accessions=accessions,
            run_outcome=state,
        )

    def _require_streamed_observation(self, observation_id: str) -> str:
        """The streamed twin of :meth:`_observation_id`'s catalog-presence check.

        The merged path derives the observation from the records themselves and refuses when
        they disagree. A stream cannot look at all its records first, so the caller states the
        observation and every part is checked against it as it arrives -- same refusal, one
        record earlier.
        """
        exists = self._writer.connection.execute(
            "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
            (observation_id,),
        ).fetchone()
        if exists is None:
            message = f"source observation {observation_id!r} is not in the catalog"
            raise ValueError(message)
        return observation_id

    @staticmethod
    def _require_streamed_location(observed: str, expected: str) -> None:
        if observed != expected:
            message = (
                "parser outcome must belong to exactly one source observation; found "
                f"{sorted({observed, expected})}"
            )
            raise ValueError(message)

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

    def _insert_record(
        self,
        connection: sqlite3.Connection,
        parser_run_id: str,
        record: ParsedRecord,
        outcome: ParseOutcome,
        duplicate_identities: frozenset[str] | None = None,
    ) -> str:
        """Write one parsed source record.

        ``duplicate_identities`` is the run's duplicate set, hoisted by the caller. It used to
        be recomputed here as a linear scan of ``outcome.duplicate_identities`` **per record**,
        which is the same per-record-over-run-level-state shape accepted Decision 111 §3
        removed from two other derivations and did not reach here. It is only visible on the
        merged path, where the outcome is the whole source: on one real median ``company.idx``
        quarter that is 252,622 records against 62,266 duplicate identities, or **15.7 billion
        string comparisons for one of seventy quarters**. Membership in a set answers exactly
        the same question, so no row's value moves.
        """
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
        if duplicate_identities is None:
            duplicate_identities = frozenset(
                identity for identity, _ in outcome.duplicate_identities
            )
        duplicate = record.duplicate_indicator or record.native_identity in duplicate_identities
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
                _json(self._persisted_payload(record)),
                _json(record.unknown_fields),
                _json(record.normalization_warnings),
                _json(record.reason_codes),
                int(duplicate),
                int(record.conflict_indicator),
                utc_now(),
            ),
        )
        return parsed_id

    def _persisted_payload(self, record: ParsedRecord) -> Mapping[str, object]:
        """The payload this contract stores for one parsed record.

        Identical to the parsed payload except for two record classes under the compact
        contract, and ``record_sha256`` is untouched in both cases so no row's identity moves:

        * an **accession-class** record, whose full payload is read by nothing and is reduced
          to the governed projection (accepted Decision 112 §7);
        * an **index-row** record, whose ``raw_line`` is the complete source text of a row the
          same payload already decomposes field by field, dropped by accepted Decision 113
          §3.C while every parsed field, the line number, and the problems list stay.
        """
        if not self._compact:
            return record.payload
        if record.native_identity.startswith("accession:"):
            return compact_parsed_payload(record.payload)
        if record.native_identity.startswith(INDEX_ROW_PREFIX):
            return compact_index_payload(record.payload)
        return record.payload

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
        if not self._compact:
            fields = sorted(record.payload)
        else:
            # The canonical row is the observation for every governed field that round-trips
            # through it, so only what it cannot carry is written (D112 §§4.B, 6). A later
            # witness carries provenance the canonical row does not, and the incumbent's rows
            # are back-filled first so a disagreement is represented by every row that
            # disagrees rather than by the newcomer alone.
            first_witness = self._is_first_witness(connection, accession.plain, parsed_id)
            if not first_witness:
                self._backfill_incumbent_observations(connection, accession.plain)
            fields = list(materialized_fields(record.payload, first_witness=first_witness))
        for field in fields:
            self._insert_accession_observation(
                connection,
                accession_plain=accession.plain,
                observation_id=record.location.observation_id,
                parsed_id=parsed_id,
                field=field,
                value=record.payload[field],
                observed=observed,
            )
        return 1

    @staticmethod
    def _insert_accession_observation(
        connection: sqlite3.Connection,
        *,
        accession_plain: str,
        observation_id: str,
        parsed_id: str,
        field: str,
        value: object,
        observed: str,
    ) -> None:
        """Write one field observation, with the identifier both contracts agree on."""
        connection.execute(
            "INSERT OR IGNORE INTO census_accession_observations "
            "(accession_observation_id, accession_plain, source_observation_id, "
            "parsed_record_id, field_name, raw_value_json, observed_at_utc, "
            "conflict_indicator) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                _stable_id(
                    "accession-observation",
                    accession_plain,
                    observation_id,
                    parsed_id,
                    field,
                ),
                accession_plain,
                observation_id,
                parsed_id,
                field,
                _json(value),
                observed,
                0,
            ),
        )

    @staticmethod
    def _is_first_witness(
        connection: sqlite3.Connection,
        accession_plain: str,
        parsed_id: str,
    ) -> bool:
        """Whether the canonical row for this accession is the one this record just created.

        Read after the ``ON CONFLICT`` upsert rather than before it: the upsert keeps the
        original ``parsed_record_id``, so the row naming this record is proof the insert took
        the create branch, and the check needs no second query on the common path.
        """
        row = connection.execute(
            "SELECT parsed_record_id FROM census_accessions WHERE accession_plain = ?",
            (accession_plain,),
        ).fetchone()
        return row is not None and str(row["parsed_record_id"]) == parsed_id

    @staticmethod
    def _backfill_incumbent_observations(
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> None:
        """Materialize the canonical row's own omitted observations, once, before a rival.

        A conflict is evidence about a *set* of rows, and the accepted conflict pass marks a
        row only when it can see a sibling that differs. Writing the newcomer alone would
        leave a disagreement with one side missing, so the incumbent is restored to rows
        first. It is idempotent: the identifiers are the same ones the omitted rows would have
        carried, so a second rival back-fills nothing.
        """
        row = connection.execute(
            "SELECT accession_plain, source_observation_id, parsed_record_id, "
            "first_observed_at_utc, form_type, filing_date_sec, report_date, "
            "acceptance_datetime_sec_raw, primary_document_name, "
            "CASE WHEN registrant_cik_numeric IS NULL THEN NULL "
            "ELSE printf('%010d', registrant_cik_numeric) END AS registrant_cik_padded "
            "FROM census_accessions WHERE accession_plain = ?",
            (accession_plain,),
        ).fetchone()
        if row is None:
            return
        for field, value in reconstructed_observations(dict(row)):
            CensusCatalog._insert_accession_observation(
                connection,
                accession_plain=accession_plain,
                observation_id=str(row["source_observation_id"]),
                parsed_id=str(row["parsed_record_id"]),
                field=field,
                value=value,
                observed=str(row["first_observed_at_utc"]),
            )

    # -- Decision 012 resolution pass --------------------------------------- #
    def resolve_persisted_accessions(
        self,
        accessions: Sequence[str] | None = None,
        *,
        batch_size: int = SINGLE_TRANSACTION,
        checkpoint_batches: bool = False,
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
        return dict(
            self.iter_persisted_accession_resolutions(
                accessions, batch_size=batch_size, checkpoint_batches=checkpoint_batches
            )
        )

    def count_persisted_accession_resolutions(
        self,
        accessions: Sequence[str] | None = None,
        *,
        batch_size: int = SINGLE_TRANSACTION,
        checkpoint_batches: bool = False,
    ) -> int:
        """Resolve exactly as :meth:`resolve_persisted_accessions` does, and count the results.

        Same writes, same order, same determinism -- the only difference is that the
        resolutions are not collected. E0 reports the resolution *count* and reads nothing else,
        so building the mapping would retain one :class:`AccessionResolution` per accession for
        a number this method can produce with none of them (accepted Decision 110 §8). On E0's
        first planned source that mapping is roughly 21.5 million entries.
        """
        return sum(
            1
            for _ in self.iter_persisted_accession_resolutions(
                accessions, batch_size=batch_size, checkpoint_batches=checkpoint_batches
            )
        )

    def iter_persisted_accession_resolutions(
        self,
        accessions: Sequence[str] | None = None,
        *,
        batch_size: int = SINGLE_TRANSACTION,
        checkpoint_batches: bool = False,
    ) -> Iterator[tuple[str, AccessionResolution]]:
        """Yield each accession's resolution as it is written, retaining none of them.

        The shared implementation behind :meth:`resolve_persisted_accessions` and
        :meth:`count_persisted_accession_resolutions`, so there is one resolution order and one
        set of writes rather than two that must be kept in step.

        When no explicit list is given the targets are paged with a keyset scan over the
        ``(accession_plain, ...)`` unique index rather than read with ``fetchall``. Two reasons,
        both required: the full list is one string per accession and does not fit, and a single
        long-lived cursor would have to stay open across every resolution's write transaction.
        The order is identical -- ascending ``accession_plain``, which is what the unpaged query
        also produced.

        One transaction per accession is the default and is what the operational catalog gets.
        A positive ``batch_size`` groups that many accessions into one real transaction instead,
        for the run-local working catalog: each accession reads only its own persisted evidence
        and writes only its own rows, so grouping changes when the rows become durable and
        nothing about what they are (the accepted D111 remediation instrument).

        Args:
            accessions: Restrict to these accessions; default is every observed accession.
            batch_size: Accessions per real transaction, or :data:`SINGLE_TRANSACTION` for one
                transaction each.
            checkpoint_batches: Truncate the write-ahead log at each batch boundary.
        """
        connection = self._writer.connection
        with BoundedTransaction(
            connection,
            batch_size=batch_size or 1,
            checkpoint=checkpoint_batches,
        ) as bounded:
            for accession_plain in (
                list(accessions)
                if accessions is not None
                else self._iter_observed_accessions(connection)
            ):
                stored, reconstructed = self._observation_rows(connection, accession_plain)
                prior = self._prior_filing_dates(connection, accession_plain)
                approved = self._approved_2024_transitions.get(accession_plain, False)
                resolution = resolve_accession(
                    accession_plain,
                    _observations_from_rows(accession_plain, self._ordered(stored + reconstructed)),
                    prior_filing_dates=prior,
                    approved_2024_transition=approved,
                )
                implicit = self._is_implicit_resolution(
                    accession_plain,
                    resolution,
                    stored=stored,
                    reconstructed=reconstructed,
                    prior=prior,
                    approved=approved,
                )
                if not implicit:
                    self._persist_resolution(connection, resolution)
                self._resolution_evidence.record(resolution, implicit=implicit)
                self._project_canonical(connection, resolution)
                bounded.unit()
                yield accession_plain, resolution

    def _is_implicit_resolution(
        self,
        accession_plain: str,
        resolution: AccessionResolution,
        *,
        stored: Sequence[Mapping[str, Any]],
        reconstructed: Sequence[Mapping[str, Any]],
        prior: Sequence[str],
        approved: bool,
    ) -> bool:
        """Whether this resolution is D113 §4's ``DEFAULT_CANONICAL_RESOLUTION``.

        Decided by rebuilding the resolution the *reader* will rebuild -- from the reconstructed
        observation stream alone, with no prior-cohort history and no approval -- and comparing.
        Nothing is assumed about which cases are default: a competing witness, a conflict, a
        malformed alternative, an authority-level choice, a prior filing date, and an approved
        2024 transition all make the two differ and are all therefore materialized (D113 §5).

        The fast path is the ordinary one. When an accession carries no stored observation, no
        prior filing date and no approval, the two inputs are the same list and the comparison
        cannot fail; skipping the second resolve keeps the pass one resolution per accession on
        the path that is 99 % of a real source.
        """
        if not self._compact:
            return False
        if not stored and not prior and not approved:
            return True
        return is_default_resolution(
            resolution,
            resolve_accession(
                accession_plain,
                _observations_from_rows(accession_plain, self._ordered(list(reconstructed))),
            ),
        )

    def _ordered(self, rows: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        """Observation rows in the order one ``ORDER BY accession_observation_id`` produced.

        The full-observation path reads a single ordered cursor. A compact read is up to three
        streams -- the stored rows, the canonical row's reconstruction, and the full-index
        corroboration assertions -- so it is re-sorted on the same key rather than left in
        concatenation order: the resolver's ranking ignores order, but the winning and competing
        identifier lists it records do not.
        """
        if self._compact:
            rows.sort(key=lambda item: str(item["accession_observation_id"]))
        return rows

    def _iter_observed_accessions(self, connection: sqlite3.Connection) -> Iterator[str]:
        """Every accession carrying at least one observation, ascending, in bounded pages.

        Under the compact contract the scan is over ``census_accessions`` instead. The two
        enumerate the same accessions: an observation's ``accession_plain`` is a foreign key
        into ``census_accessions``, and every canonical row is created by the same call that
        would have written its observations, so neither table can hold an accession the other
        does not. What changes is only which one is asked.
        """
        table, column = (
            ("census_accessions", "accession_plain")
            if self._compact
            else ("census_accession_observations", "DISTINCT accession_plain")
        )
        after = ""
        while True:
            page = [
                str(row["accession_plain"])
                for row in connection.execute(
                    f"SELECT {column} FROM {table} "  # noqa: S608 - both literals, never input
                    "WHERE accession_plain > ? ORDER BY accession_plain LIMIT ?",
                    (after, _ACCESSION_PAGE_SIZE),
                ).fetchall()
            ]
            if not page:
                return
            yield from page
            after = page[-1]

    def _observation_rows(
        self,
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> tuple[list[Mapping[str, Any]], list[Mapping[str, Any]]]:
        """One accession's observation rows, split into the stored and the reconstructed.

        Under the full-observation contract everything is stored and the second list is empty.
        Under the compact contract the stored rows are joined by two reconstructions, each
        carrying the same value, the same provenance, and the same deterministic identifier the
        omitted row would have carried:

        * the canonical ``census_accessions`` row's own governed fields
          (:func:`reconstructed_observations`, accepted D112 §4.C);
        * every full-index corroboration assertion bound to this accession
          (:func:`corroboration_observations`, accepted D113 §9).

        The split matters beyond ordering: whether an accession carries a *stored* observation
        is exactly what separates D113 §4's implicit default from §5's materialized exception.
        """
        stored = _stored_observation_rows(connection, accession_plain)
        rows: list[Mapping[str, Any]] = list(stored)
        if not self._compact:
            return rows, []
        reconstructed = _reconstructed_rows(connection, accession_plain, stored)
        reconstructed += _corroboration_rows(connection, accession_plain, stored)
        return rows, reconstructed

    def _field_observations(
        self,
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> list[AccessionFieldObservation]:
        """Build Decision 012 observations from persisted source-native rows.

        Ordering here is only for reproducibility of the *input list*; the resolver's
        ranking never consults it, so the canonical result is unchanged by it.
        """
        stored, reconstructed = self._observation_rows(connection, accession_plain)
        return _observations_from_rows(accession_plain, self._ordered(stored + reconstructed))

    @staticmethod
    def _prior_filing_dates(
        connection: sqlite3.Connection,
        accession_plain: str,
    ) -> list[str]:
        """Return filing dates from earlier persisted resolutions."""
        return _prior_filing_dates(connection, accession_plain)

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

        **Each reference is written with its own parent registrant.** The CIK was formerly
        resolved once per observation, from the lowest-``parsed_record_id`` registrant
        record of the whole source, and stamped on every reference. That is correct only
        where a source describes one registrant, and the bulk archive describes hundreds of
        thousands: accepted Decision 129 §6 (D129-R4) records the result, ``5,337`` of
        ``5,337`` rows carrying one CIK where ``4,144`` distinct registrants were
        represented. The value now comes from
        :attr:`~disclosure_drift.sec.parsers.submissions.HistoricalFileReference.registrant_cik_padded`,
        set by the document that actually declared the entry, so no lookup, ordering, or
        per-reference scan is involved and the D111 cost this method was tuned for does not
        return. The persisted schema is unchanged: ``registrant_cik_padded`` already exists
        on both tables and is already part of the primary key, so no migration is implied.
        """
        references = list(references)
        if not references:
            return
        for reference in references:
            try:
                cik = normalize_cik(reference.registrant_cik_padded)[1]
            except IdentifierError as exc:
                # Unreachable from the parser, which admits no reference until the
                # declaring document's own CIK has normalized. Stated rather than assumed
                # because the alternative to failing here is writing a reference under
                # somebody else's registrant, which is the defect being repaired.
                message = (
                    f"historical reference {reference.name!r} at "
                    f"{reference.location.describe()} carries an unusable parent registrant "
                    f"CIK {reference.registrant_cik_padded!r}: {exc}. No registrant is "
                    "inferred and no observation-wide value is substituted."
                )
                raise ValueError(message) from exc
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

    def _flush_run_level_derivations(
        self,
        connection: sqlite3.Connection,
        observation_id: str,
    ) -> None:
        """Apply the derivations that are functions of the run's **whole** observation.

        Candidate lineage edges and accession conflict indicators used to be recomputed
        after **every** record, which made each of them quadratic in the record count: one
        full ``GROUP BY`` over every registrant observation of the source per registrant
        record (twice), and one grouped read plus update per accession record. Measured on
        E0's first planned source that is the dominant latency cost -- the marginal cost of
        a 40-member block grew 5x across the first 400 members alone (accepted Decision 111
        section 6).

        Computing each once, after the last record, writes **exactly** the same rows,
        because both derivations are monotone in the evidence they read:

        * :meth:`_candidate_edges` emits every pair of CIKs that share one alias value. The
          set of CIKs sharing a value only ever grows as records are added, and the pairs
          from any prefix are a subset of the pairs from the whole. The final call therefore
          produces the union of every per-record call, and the edge identity does not depend
          on when it was computed.
        * A conflict indicator is only ever raised, never cleared, and it is a function of
          the distinct raw values recorded for one ``(accession, field)``. The final pass
          sees every value any record contributed, so it raises exactly the flags the
          per-record calls raised between them.

        What changes is the number of times each is computed, not what either decides.
        """
        self._candidate_edges(connection, observation_id, kind="company_name")
        self._candidate_edges(connection, observation_id, kind="ticker")
        self._mark_accession_conflicts(connection)

    @staticmethod
    def _mark_accession_conflicts(connection: sqlite3.Connection) -> None:
        """Raise the conflict indicator wherever one accession field carries rival values.

        One set-based statement rather than a grouped read and an update per accession.
        It is deliberately not scoped to the current run: an accession's conflicts are a
        property of **all** its observations regardless of which source contributed them,
        the flag is only ever raised, and every earlier run already ran this same pass over
        its own accessions -- so an untouched accession is re-examined and found already
        correct rather than changed. Scoping it to the run would additionally require a
        scan the schema has no index for.

        Written as a correlated ``EXISTS`` rather than the ``GROUP BY ... HAVING
        COUNT(DISTINCT ...)`` it reads like, and the difference is memory rather than taste.
        The grouped form has to build one temporary B-tree over **every** accession
        observation in the catalog before it can answer, which is an intermediate
        proportional to the whole source and is exactly what the accepted Decision 110
        section 8 memory invariant forbids. The ``EXISTS`` form asks the same question one
        row at a time, and each probe is an index range over a single accession's handful of
        observations. Both mark exactly the rows in a group whose values disagree: a group
        holds two different values if and only if each of its rows has a sibling that
        differs from it.
        """
        connection.execute(
            "UPDATE census_accession_observations AS o SET conflict_indicator = 1 "
            "WHERE o.conflict_indicator = 0 AND EXISTS ("
            "SELECT 1 FROM census_accession_observations AS rival "
            "WHERE rival.accession_plain = o.accession_plain "
            "AND rival.field_name = o.field_name "
            "AND rival.raw_value_json <> o.raw_value_json)"
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


def _reconstructed_rows(
    connection: sqlite3.Connection,
    accession_plain: str,
    stored: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """Yield the observation rows one canonical accession row implies, shaped as read rows.

    The compact contract's reader half. Each row carries exactly what the omitted
    ``census_accession_observations`` row would have carried -- the same deterministic
    identifier, the same ``raw_value_json`` rendering, the same provenance and observation
    time -- so a consumer cannot tell a reconstructed row from a stored one, which is the
    point: the canonical row *is* the observation.

    A materialized row for the same field is not suppressed here. It cannot collide: an
    observation is materialized precisely when the canonical column could not reproduce it, and
    the incumbent's own governed fields are back-filled before any rival is written, so the
    identifier a reconstruction emits is never also present as a stored row for the same
    ``(accession, source, parsed record, field)``.
    """
    row = connection.execute(
        "SELECT a.accession_plain, a.source_observation_id, a.parsed_record_id, "
        "a.first_observed_at_utc, a.form_type, a.filing_date_sec, a.report_date, "
        "a.acceptance_datetime_sec_raw, a.primary_document_name, "
        "CASE WHEN a.registrant_cik_numeric IS NULL THEN NULL "
        "ELSE printf('%010d', a.registrant_cik_numeric) END AS registrant_cik_padded, "
        "s.source_id, s.logical_sha256 "
        "FROM census_accessions AS a "
        "JOIN census_source_observations AS s ON s.observation_id = a.source_observation_id "
        "WHERE a.accession_plain = ?",
        (accession_plain,),
    ).fetchone()
    if row is None:
        return []
    observation_id = str(row["source_observation_id"])
    parsed_id = str(row["parsed_record_id"])
    # The already-read rows answer this; the back-filled incumbent of a disagreement is stored
    # under the canonical row's own provenance and must not be reconstructed on top of itself.
    written = {
        str(item["field_name"])
        for item in stored
        if str(item["source_observation_id"]) == observation_id
        and str(item["parsed_record_id"]) == parsed_id
    }
    return [
        {
            "accession_observation_id": _stable_id(
                "accession-observation", accession_plain, observation_id, parsed_id, field
            ),
            "source_observation_id": observation_id,
            "parsed_record_id": parsed_id,
            "field_name": field,
            "raw_value_json": _json(value),
            "observed_at_utc": str(row["first_observed_at_utc"]),
            "source_id": str(row["source_id"]),
            "logical_sha256": row["logical_sha256"],
        }
        for field, value in reconstructed_observations(dict(row))
        if field not in written
    ]


def _stored_observation_rows(
    connection: sqlite3.Connection,
    accession_plain: str,
) -> list[Mapping[str, Any]]:
    """One accession's persisted ``census_accession_observations`` rows, ordered by identity.

    Typed as mappings rather than as ``sqlite3.Row`` so a stored row and a reconstructed one are
    the same thing to every caller. ``Row`` supports the whole read interface used here; the
    cast states that rather than copying every row into a ``dict`` per accession, which on E0's
    first planned source would be one allocation per observation for no gain.
    """
    return cast(
        "list[Mapping[str, Any]]",
        connection.execute(
            "SELECT o.accession_observation_id, o.source_observation_id, o.parsed_record_id, "
            "o.field_name, o.raw_value_json, o.observed_at_utc, s.source_id, s.logical_sha256 "
            "FROM census_accession_observations AS o "
            "JOIN census_source_observations AS s "
            "  ON s.observation_id = o.source_observation_id "
            "WHERE o.accession_plain = ? "
            "ORDER BY o.accession_observation_id",
            (accession_plain,),
        ).fetchall(),
    )


def _prior_filing_dates(connection: sqlite3.Connection, accession_plain: str) -> list[str]:
    """Filing dates from earlier persisted resolutions of this accession.

    Earlier derived resolutions are retained, so a correction's cohort consequences can be
    recorded rather than overwritten. Under the compact contract an accession with an implicit
    resolution has none by construction -- a prior filing date is exactly one of the things
    that stops a resolution being the default -- so the two readings agree.
    """
    return [
        str(row["resolved_value"])
        for row in connection.execute(
            "SELECT resolved_value FROM census_accession_field_resolutions "
            "WHERE accession_plain = ? AND field_name = 'official_filing_date' "
            "AND status IN ('resolved', 'resolved_by_correction') "
            "ORDER BY resolved_at_utc",
            (accession_plain,),
        ).fetchall()
        if row["resolved_value"]
    ]


def reconstructed_accession_resolution(
    connection: sqlite3.Connection,
    accession_plain: str,
) -> AccessionResolution:
    """The Decision 012 resolution one accession's compact evidence implies (D113 §4).

    ``DEFAULT_CANONICAL_RESOLUTION`` made executable: the reader rebuilds the omitted rows by
    replaying the accepted resolver over the observation stream the canonical accession row and
    the full-index corroboration assertions imply, under the frozen contract. It is the same
    stream, in the same order, that the resolution pass itself resolved, so the answer is the
    row that was not written rather than an approximation of it.

    Safe to ask about **any** accession, materialized or not: stored observations are read as
    well, so an accession whose rows *were* written reconstructs to the same resolution they
    hold. The caller decides which source to trust; the accepted reader prefers the persisted
    row and falls back to this only where none exists.
    """
    stored = _stored_observation_rows(connection, accession_plain)
    rows: list[Mapping[str, Any]] = list(stored)
    rows += _reconstructed_rows(connection, accession_plain, stored)
    rows += _corroboration_rows(connection, accession_plain, stored)
    rows.sort(key=lambda item: str(item["accession_observation_id"]))
    return resolve_accession(
        accession_plain,
        _observations_from_rows(accession_plain, rows),
        prior_filing_dates=_prior_filing_dates(connection, accession_plain),
    )


def _observations_from_rows(
    accession_plain: str,
    rows: Sequence[Mapping[str, Any]],
) -> list[AccessionFieldObservation]:
    """Turn persisted or reconstructed observation rows into Decision 012 observations.

    One function, so a reconstructed row is filtered, decoded, and typed by exactly the code a
    stored row is: an unmapped source field, an unresolvable source, undecodable JSON, and a
    blank value are dropped identically whichever cursor produced the row.
    """
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


def _corroboration_rows(
    connection: sqlite3.Connection,
    accession_plain: str,
    stored: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    """The observation rows one accession's full-index corroboration assertions imply.

    The D113 §9 reader half. A ``company.idx`` row that corroborates an already-canonical
    accession is not repeated as three observation rows; the parsed record the traversal
    already wrote *is* the assertion, carrying the accession it binds to, the quarter's source
    identity, the CIK, form and filing date it asserts, its line number, and a
    ``record_sha256`` over the complete raw row. This restores the observations that assertion
    implies, with the identical deterministic identifiers, values, and provenance.

    ``observed_at_utc`` comes from the parsed record's own ``recorded_at_utc`` rather than from
    the materialization pass's run-level clock, because a reconstruction must read a persisted
    value and not a wall clock it cannot see. It feeds nothing but the relation row's audit
    timestamps; no classification, no resolution, and no membership verdict reads it.

    A row whose observations *are* stored -- a disagreement, a co-registrant, anything D113 §10
    keeps explicit -- is skipped here, exactly as :func:`_reconstructed_rows` skips a
    back-filled incumbent, so nothing is ever reconstructed on top of itself.
    """
    written = {
        (str(item["parsed_record_id"]), str(item["field_name"]))
        for item in stored
        if item["parsed_record_id"] is not None
    }
    # A range over ``idx_census_parsed_identity``: the parser stamps
    # ``index_row:{dashed accession}:{line}``, so one seek finds every quarter's row for this
    # accession. ``:`` is 0x3A and ``;`` is 0x3B, so the half-open bound is exact.
    prefix = f"{INDEX_ROW_PREFIX}{parse_accession(accession_plain).dashed}:"
    rows: list[Mapping[str, Any]] = []
    for record in connection.execute(
        "SELECT p.parsed_record_id, p.source_observation_id, p.payload_json, "
        "p.recorded_at_utc, s.source_id, s.logical_sha256 "
        "FROM census_parsed_records AS p "
        "JOIN census_source_observations AS s "
        "  ON s.observation_id = p.source_observation_id "
        "WHERE p.native_identity >= ? AND p.native_identity < ? "
        "ORDER BY p.parsed_record_id",
        (prefix, f"{prefix};"),
    ).fetchall():
        payload = _index_assertion(record["payload_json"])
        if payload is None:
            continue
        plain, cik_padded = payload
        if plain != accession_plain:
            continue
        parsed_id = str(record["parsed_record_id"])
        observation_id = str(record["source_observation_id"])
        decoded = json.loads(str(record["payload_json"]))
        rows += [
            {
                "accession_observation_id": _stable_id(
                    "accession-observation", accession_plain, observation_id, parsed_id, field
                ),
                "source_observation_id": observation_id,
                "parsed_record_id": parsed_id,
                "field_name": field,
                "raw_value_json": _json(value),
                "observed_at_utc": str(record["recorded_at_utc"]),
                "source_id": str(record["source_id"]),
                "logical_sha256": record["logical_sha256"],
            }
            for field, value in corroboration_observations(decoded, cik_padded=cik_padded)
            if (parsed_id, field) not in written
        ]
    return rows


def _index_assertion(raw: object) -> tuple[str, str] | None:
    """One index-row payload's ``(accession_plain, cik_padded)``, or ``None``.

    The same refusals the accepted R23 materialization applies, restated for the reader so a
    row it never observed is never reconstructed: a payload the parser recorded ``problems``
    for establishes nothing, and a malformed accession or CIK contributes nothing rather than
    contributing a guessed one.
    """
    try:
        decoded = json.loads(str(raw))
    except (TypeError, ValueError):
        return None
    if not isinstance(decoded, dict) or decoded.get("problems"):
        return None
    accession = decoded.get("accession_plain")
    cik = decoded.get("cik_padded")
    if not isinstance(accession, str) or not isinstance(cik, str):
        return None
    try:
        return parse_accession(accession).plain, normalize_cik(cik)[1]
    except IdentifierError:
        return None


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
