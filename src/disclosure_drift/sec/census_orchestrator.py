"""Restartable Stage M2.2 metadata-census orchestration."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Mapping
from contextlib import suppress
from dataclasses import dataclass, field, replace
from functools import partial
from pathlib import Path
from typing import Any, Final

from disclosure_drift.config import ProjectConfig
from disclosure_drift.errors import RawObjectIntegrityError
from disclosure_drift.paths import DataTree
from disclosure_drift.reasons import REASON_CODES
from disclosure_drift.sec.archive import ArchiveDefenceError, ArchiveMember, iter_members
from disclosure_drift.sec.census import CensusCatalog, QAMetric
from disclosure_drift.sec.census_completion import (
    CensusCompletionDecision,
    ParserTerminalState,
    PlannedSourceState,
    RetrievalTerminalState,
)
from disclosure_drift.sec.http_client import (
    FetchResult,
    ProhibitedRetrievalError,
    RetrievalPolicy,
    SecClient,
)
from disclosure_drift.sec.httpx_transport import HttpxTransport
from disclosure_drift.sec.identifiers import IdentifierError, normalize_cik, parse_accession
from disclosure_drift.sec.index_plan import (
    CoverageWindow,
    IndexInstancePlan,
    coverage_summary,
    plan_index_instances,
)
from disclosure_drift.sec.index_reconciliation import (
    IndexInstance as ReconciliationInstance,
)
from disclosure_drift.sec.index_reconciliation import (
    ReconciliationReport,
    SubmissionsAccession,
    reconcile_index,
)
from disclosure_drift.sec.index_retrieval import (
    IndexInstanceOutcome,
    IndexRetrievalAccounting,
    InstanceLifecycleState,
    logical_budget,
    new_event_id,
    order_instances,
    retrieve_instance,
)
from disclosure_drift.sec.observation_catalog import (
    ObservationRecorder,
    RecoveryEvent,
    load_observations,
    rebuild_audit_projection,
    reconcile,
    record_recovery_events,
    validate_audit_projection,
)
from disclosure_drift.sec.parsers.base import (
    ParseOutcome,
    QuarantinedRecord,
    RecordLocation,
    merge_outcomes,
)
from disclosure_drift.sec.parsers.calendar import parse_edgar_calendar
from disclosure_drift.sec.parsers.historical import parse_historical_submissions
from disclosure_drift.sec.parsers.sic import parse_sic_reference
from disclosure_drift.sec.parsers.submissions import (
    HistoricalFileReference,
    parse_submissions_document,
)
from disclosure_drift.sec.parsers.tickers import (
    parse_company_tickers,
    parse_company_tickers_exchange,
)
from disclosure_drift.sec.rate_limit import AggregateRateLimiter
from disclosure_drift.sec.snapshots import SnapshotStore, SourceObservation
from disclosure_drift.sec.source_registry import SOURCES, SourceSpec
from disclosure_drift.sec.transport import Transport
from disclosure_drift.sec.urls import request_identity
from disclosure_drift.storage.catalog import CatalogWriter
from disclosure_drift.storage.sqlite import transaction, utc_now

__all__ = ["CENSUS_AUDIT_FILENAME", "CensusOrchestrator", "CensusRunReport"]

CENSUS_AUDIT_FILENAME: Final = "census_qa_summary.json"
_BASE_SOURCES: Final[tuple[str, ...]] = (
    "sec_bulk_submissions",
    "sec_company_tickers_exchange",
    "sec_company_tickers",
    "sec_sic_code_list",
    "sec_edgar_filing_calendar",
)


@dataclass(frozen=True, slots=True)
class CensusRunReport:
    """Terminal accounting for one census run."""

    census_run_id: str
    completed: bool
    source_observations: int
    parsed_records: int
    quarantined_records: int
    historical_references_retrieved: int
    metrics: tuple[QAMetric, ...]
    audit_path: Path
    detail: str
    completion: CensusCompletionDecision
    index_coverage: Mapping[str, object] = field(default_factory=dict)
    index_accounting: Mapping[str, object] = field(default_factory=dict)
    accession_resolutions: int = 0
    unresolved_accession_fields: tuple[str, ...] = ()


class CensusOrchestrator:
    """Coordinates approved metadata retrieval, immutable storage, parsing, and QA."""

    def __init__(
        self,
        config: ProjectConfig,
        *,
        transport: Transport | None = None,
        calendar_target_year: int | None = None,
        coverage: CoverageWindow | None = None,
    ) -> None:
        """Create an orchestrator.

        Args:
            config: Validated project configuration.
            transport: Injected transport. Tests supply a fake; production builds an
                httpx transport lazily so no HTTP library is imported otherwise.
            calendar_target_year: The year the annual-calendar instance must cover.
                This is part of the census plan and is never inferred from the current
                date or the retrieval timestamp. When absent, the annual-calendar
                source asserts nothing and blocks completion, which is the fail-closed
                reading of Decision 011.
            coverage: Explicit coverage window and as-of date. The quarterly index plan
                is derived from it; the as-of date is never read from the clock. When
                absent, no index instance is planned and no index coverage is claimed.
        """
        self._config = config
        self._transport = transport
        self._calendar_target_year = calendar_target_year
        self._coverage = coverage
        self._index_plan = None if coverage is None else plan_index_instances(coverage)
        self._satisfied_index_keys: set[str] = set()

    def run(self) -> CensusRunReport:
        """Run or safely resume the complete metadata census."""
        user_agent = self._config.require_sec_user_agent()
        self._config.require_network()
        tree = self._config.data_tree()
        tree.ensure_tree()
        census_run_id = uuid.uuid4().hex
        owned_transport = self._transport is None
        transport = self._transport or HttpxTransport()
        try:
            return self._run_with_transport(
                tree,
                census_run_id,
                user_agent,
                transport,
            )
        finally:
            if owned_transport:
                transport.close()

    def _run_with_transport(
        self,
        tree: DataTree,
        census_run_id: str,
        user_agent: str,
        transport: Transport,
    ) -> CensusRunReport:
        policy = RetrievalPolicy(
            max_transient_retries=self._config.sec.max_retries,
            cooldown_seconds=self._config.sec.cooldown_seconds,
            connect_timeout_seconds=self._config.sec.connect_timeout_seconds,
            read_timeout_seconds=self._config.sec.read_timeout_seconds,
            bulk_read_timeout_seconds=self._config.sec.bulk_read_timeout_seconds,
        )
        client = SecClient(
            transport,
            user_agent,
            AggregateRateLimiter(
                self._config.sec.requests_per_second,
                burst=self._config.sec.burst,
            ),
            policy,
        )
        parsed = 0
        quarantined = 0
        historical_retrieved = 0
        completed = False
        detail = "census stopped before completion"

        with CatalogWriter(tree.catalog_database, tree.locks) as writer:
            writer.migrate()
            writer.seed_reference_data()
            self._start_job(writer, census_run_id)
            recovery = reconcile(writer.connection, tree)
            if recovery.events:
                record_recovery_events(
                    writer,
                    recovery.events,
                    census_run_id=census_run_id,
                )
            projection_rebuilt = False
            if recovery.projection_recovery_required:
                rebuild_audit_projection(
                    writer.connection,
                    tree.audit / "census_source_observations.jsonl",
                    census_run_id=census_run_id,
                )
                projection_rebuilt = True

            snapshot_store = SnapshotStore(tree)
            snapshot_store.adopt(load_observations(writer.connection))
            recorder = ObservationRecorder(writer, tree)
            catalog = CensusCatalog(writer)
            self._persist_index_instances(writer, census_run_id)
            historical_queue: list[tuple[str, HistoricalFileReference]] = []
            plan: dict[str, PlannedSourceState] = {}
            base_instance_ids: dict[str, str] = {}
            for source_id in _BASE_SOURCES:
                planned = self._base_plan(source_id)
                plan[planned.instance_id] = planned
                base_instance_ids[source_id] = planned.instance_id
                self._persist_plan(writer, census_run_id, planned)
            try:
                for source_id in _BASE_SOURCES:
                    planned = plan[base_instance_ids[source_id]]
                    observation, outcome, references = self._retrieve_and_parse(
                        client,
                        snapshot_store,
                        recorder,
                        source_id,
                    )
                    planned = self._after_observation(planned, observation, outcome)
                    if outcome is None:
                        plan[planned.instance_id] = planned
                        self._persist_plan(writer, census_run_id, planned)
                        continue
                    try:
                        result = catalog.persist(
                            outcome,
                            historical_references=references,
                            source_observation_id=observation.observation_id,
                        )
                    except Exception:
                        failed_plan = replace(
                            planned,
                            catalog_state="failed",
                            qa_state="failed",
                            unresolved_blocking_reasons=tuple(
                                sorted(
                                    {
                                        *planned.unresolved_blocking_reasons,
                                        "catalog_write_failed",
                                    }
                                )
                            ),
                        )
                        plan[failed_plan.instance_id] = failed_plan
                        self._persist_plan(writer, census_run_id, failed_plan)
                        raise
                    planned = self._after_catalog(planned, outcome)
                    plan[planned.instance_id] = planned
                    self._persist_plan(writer, census_run_id, planned)
                    parsed += result.parsed
                    quarantined += result.quarantined
                    if source_id == "sec_bulk_submissions":
                        historical_queue.extend(self._reference_queue(outcome, references))

                for cik, reference in historical_queue:
                    planned = self._historical_plan(cik, reference)
                    plan[planned.instance_id] = planned
                    self._persist_plan(writer, census_run_id, planned)
                    observation, outcome = self._retrieve_historical(
                        client,
                        snapshot_store,
                        recorder,
                        cik,
                        reference,
                    )
                    planned = self._after_observation(planned, observation, outcome)
                    if outcome is None:
                        plan[planned.instance_id] = planned
                        self._persist_plan(writer, census_run_id, planned)
                        self._update_historical_status(
                            writer,
                            cik,
                            reference,
                            planned.retrieval_state,
                        )
                        continue
                    try:
                        result = catalog.persist(
                            outcome,
                            source_observation_id=observation.observation_id,
                        )
                    except Exception:
                        failed_plan = replace(
                            planned,
                            catalog_state="failed",
                            qa_state="failed",
                            unresolved_blocking_reasons=tuple(
                                sorted(
                                    {
                                        *planned.unresolved_blocking_reasons,
                                        "catalog_write_failed",
                                    }
                                )
                            ),
                        )
                        plan[failed_plan.instance_id] = failed_plan
                        self._persist_plan(writer, census_run_id, failed_plan)
                        self._update_historical_status(
                            writer,
                            cik,
                            reference,
                            failed_plan.retrieval_state,
                        )
                        raise
                    planned = self._after_catalog(planned, outcome)
                    plan[planned.instance_id] = planned
                    self._persist_plan(writer, census_run_id, planned)
                    parsed += result.parsed
                    quarantined += result.quarantined
                    historical_retrieved += int(planned.successful_terminal)
                    self._update_historical_status(
                        writer,
                        cik,
                        reference,
                        "retrieved" if planned.successful_terminal else planned.retrieval_state,
                    )

                # Quarterly index instances are processed after every submissions source,
                # so reconciliation compares against the complete submissions side.
                index_accounting = self._process_index_instances(
                    writer, census_run_id, client, snapshot_store, recorder, catalog
                )

                # Decision 012: canonical accession fields are derived only now, from
                # every persisted observation, so the result cannot depend on the order
                # the observations were ingested in during this run.
                resolutions = catalog.resolve_persisted_accessions()
                resolution_blocking = sorted(
                    {
                        f"accession_unresolved:{accession}:{field_name}"
                        for accession, resolution in resolutions.items()
                        for field_name in resolution.blocking_fields
                    }
                    | {
                        f"accession_2024_approval_required:{accession}"
                        for accession, resolution in resolutions.items()
                        if resolution.requires_2024_approval
                    }
                )

                _, unprojected = recorder.flush_projection()
                projection_path = tree.audit / "census_source_observations.jsonl"
                projection_validation = validate_audit_projection(
                    writer.connection,
                    projection_path,
                )
                if projection_validation.requires_recovery:
                    record_recovery_events(
                        writer,
                        (
                            RecoveryEvent(
                                scenario="audit_projection_interrupted",
                                action_taken="projection_rebuild_required",
                                detail=projection_validation.detail,
                                relative_path=projection_validation.projection_path,
                                resolution_state="blocked",
                            ),
                        ),
                        census_run_id=census_run_id,
                    )
                    rebuild_audit_projection(
                        writer.connection,
                        projection_path,
                        census_run_id=census_run_id,
                    )
                    unprojected = recorder.unprojected()
                    projection_validation = validate_audit_projection(
                        writer.connection,
                        projection_path,
                    )
                metrics = catalog.qa_metrics(census_run_id)
                integrity = writer.integrity()
                release_blocking_count = self._release_blocking_count(tuple(plan.values()))
                recovery_reasons = recovery.blocking_reasons(projection_rebuilt=projection_rebuilt)
                index_reasons = self._index_coverage_reasons()
                completion = CensusCompletionDecision(
                    sources=tuple(plan.values()),
                    recovery_passed=not recovery_reasons,
                    recovery_blocking_reasons=(
                        *recovery_reasons,
                        *resolution_blocking,
                        *index_reasons,
                    ),
                    sqlite_integrity_passed=integrity.passed,
                    release_blocking_reason_count=release_blocking_count,
                    qa_report_written=True,
                    audit_projection_complete=(not unprojected and projection_validation.is_valid),
                )
                audit_path = self._write_qa(
                    tree,
                    census_run_id,
                    metrics,
                    completion,
                )
                completed = completion.completed
                detail = completion.detail
                self._finish_job(writer, census_run_id, completed, detail)
                observation_count = self._count(writer.connection, "census_source_observations")
                return CensusRunReport(
                    census_run_id=census_run_id,
                    completed=completed,
                    source_observations=observation_count,
                    parsed_records=parsed,
                    quarantined_records=quarantined,
                    historical_references_retrieved=historical_retrieved,
                    metrics=metrics,
                    audit_path=audit_path,
                    detail=detail,
                    completion=completion,
                    index_coverage=self.index_coverage(),
                    index_accounting=dict(index_accounting.as_record()),
                    accession_resolutions=len(resolutions),
                    unresolved_accession_fields=tuple(resolution_blocking),
                )
            except Exception as exc:
                self._finish_job(writer, census_run_id, False, f"{type(exc).__name__}: {exc}")
                raise

    def _retrieve_and_parse(
        self,
        client: SecClient,
        store: SnapshotStore,
        recorder: ObservationRecorder,
        source_id: str,
    ) -> tuple[
        SourceObservation,
        ParseOutcome | None,
        tuple[HistoricalFileReference, ...],
    ]:
        spec = SOURCES[source_id]
        result = self._fetch(client, store, spec)
        observation = store.record(result)
        if not observation.is_usable:
            recorder.record(observation)
            return observation, None, ()
        try:
            store.verify_payload(observation)
        except RawObjectIntegrityError as exc:
            refused = replace(
                observation,
                outcome="quarantined",
                reason_codes=("RAW_FILE_CHECKSUM_MISMATCH",),
                detail=str(exc),
            )
            recorder.record(refused)
            return refused, None, ()

        if source_id == "sec_bulk_submissions":
            return self._parse_bulk(store, recorder, observation)
        recorder.record(observation)
        payload = store.load_payload(observation)
        location = RecordLocation(observation.observation_id, source_id)
        if source_id in {"sec_company_tickers", "sec_company_tickers_exchange"}:
            decoded, failure = _json_payload(payload, location, spec.parser_version)
            if failure is not None:
                return observation, failure, ()
            outcome = (
                parse_company_tickers(decoded, location)
                if source_id == "sec_company_tickers"
                else parse_company_tickers_exchange(decoded, location)
            )
            return observation, outcome, ()
        if source_id == "sec_sic_code_list":
            return (
                observation,
                parse_sic_reference(payload.decode("utf-8", "replace"), location),
                (),
            )
        if source_id == "sec_edgar_filing_calendar":
            return (
                observation,
                parse_edgar_calendar(
                    payload.decode("utf-8", "replace"),
                    location,
                    target_year=self._calendar_target_year,
                ),
                (),
            )
        return observation, None, ()

    def _parse_bulk(
        self,
        store: SnapshotStore,
        recorder: ObservationRecorder,
        observation: SourceObservation,
    ) -> tuple[
        SourceObservation,
        ParseOutcome | None,
        tuple[HistoricalFileReference, ...],
    ]:
        path = store.payload_path(observation)
        members: tuple[ArchiveMember, ...]
        try:
            members = tuple(
                iter_members(
                    path,
                    name_suffix=".json",
                    archive_relative_path=observation.relative_storage_path,
                    archive_sha256=observation.logical_sha256,
                )
            )
        except ArchiveDefenceError as exc:
            quarantined = replace(
                observation,
                outcome="quarantined",
                reason_codes=(exc.reason_code,),
                detail=str(exc),
            )
            recorder.record(quarantined)
            return quarantined, None, ()

        recorder.record(observation, members=members)
        if not members:
            location = RecordLocation(observation.observation_id, observation.source_id)
            empty_archive_failure = _parse_failure(
                location,
                SOURCES["sec_bulk_submissions"].parser_version,
                "bulk submissions archive contained no JSON submission members",
                b"",
            )
            return observation, empty_archive_failure, ()
        outcomes: list[ParseOutcome] = []
        references: list[HistoricalFileReference] = []
        for member in members:
            location = RecordLocation(
                observation.observation_id,
                observation.source_id,
                member_name=member.name,
            )
            decoded, failure = _json_payload(
                member.payload,
                location,
                SOURCES["sec_bulk_submissions"].parser_version,
            )
            if failure is not None:
                outcomes.append(failure)
                continue
            outcome, member_references = parse_submissions_document(decoded, location)
            outcomes.append(outcome)
            references.extend(member_references)
        merged = merge_outcomes(
            "submissions-json",
            SOURCES["sec_bulk_submissions"].parser_version,
            outcomes,
        )
        return observation, merged, tuple(references)

    def _retrieve_historical(
        self,
        client: SecClient,
        store: SnapshotStore,
        recorder: ObservationRecorder,
        cik: str,
        reference: HistoricalFileReference,
    ) -> tuple[SourceObservation, ParseOutcome | None]:
        spec = SOURCES["sec_submissions_historical"]
        # Narrowed the same way as the planning path: a reference reaching retrieval has
        # already been proved retrievable, and the guard makes that explicit rather than
        # assumed, so the template parameter is a concrete ``str``.
        historical_file = reference.name
        if not reference.is_retrievable or historical_file is None:
            message = (
                "refusing to retrieve a malformed historical reference at "
                f"{reference.location.describe()}: {'; '.join(reference.problems)}"
            )
            raise ProhibitedRetrievalError(message)
        parameters = {"historical_file": historical_file}
        result = self._fetch(
            client,
            store,
            spec,
            parameters=parameters,
            purpose="retrieve source-referenced historical submissions metadata",
        )
        observation = store.record(result)
        if not observation.is_usable:
            recorder.record(observation)
            return observation, None
        try:
            store.verify_payload(observation)
        except RawObjectIntegrityError as exc:
            refused = replace(
                observation,
                outcome="quarantined",
                reason_codes=("RAW_FILE_CHECKSUM_MISMATCH",),
                detail=str(exc),
            )
            recorder.record(refused)
            return refused, None
        recorder.record(observation)
        location = RecordLocation(observation.observation_id, spec.source_id)
        decoded, failure = _json_payload(
            store.load_payload(observation),
            location,
            spec.parser_version,
        )
        if failure is not None:
            return observation, failure
        return (
            observation,
            parse_historical_submissions(decoded, location, registrant_cik=cik),
        )

    @staticmethod
    def _fetch(
        client: SecClient,
        store: SnapshotStore,
        spec: SourceSpec,
        *,
        parameters: Mapping[str, str] | None = None,
        purpose: str | None = None,
    ) -> FetchResult:
        url = spec.url(**dict(parameters or {}))
        identity = request_identity(spec.source_id, url, dict(parameters or {}))
        previous = store.latest_for(spec.source_id, identity)
        return client.fetch(
            spec.source_id,
            purpose=purpose or spec.purpose,
            parameters=parameters,
            etag=previous.etag,
            last_modified=previous.last_modified,
            stream=spec.expected_content == "zip",
        )

    @staticmethod
    def _reference_queue(
        outcome: ParseOutcome,
        references: tuple[HistoricalFileReference, ...],
    ) -> list[tuple[str, HistoricalFileReference]]:
        cik_by_member: dict[str | None, str] = {}
        for record in outcome.records:
            if not record.native_identity.startswith("registrant:"):
                continue
            try:
                cik = normalize_cik(str(record.payload.get("cik")))[1]
            except IdentifierError:
                continue
            cik_by_member[record.location.member_name] = cik
        # A malformed reference is never queued: its name may not be usable as a URL
        # template parameter. It is already preserved as a quarantined source record
        # and it already blocks the parser run through the structural verdict.
        return [
            (cik_by_member[reference.location.member_name], reference)
            for reference in references
            if reference.is_retrievable and reference.location.member_name in cik_by_member
        ]

    def _process_index_instances(
        self,
        writer: CatalogWriter,
        census_run_id: str,
        client: SecClient,
        store: SnapshotStore,
        recorder: ObservationRecorder,
        catalog: CensusCatalog,
    ) -> IndexRetrievalAccounting:
        """Retrieve, parse, and reconcile every unsatisfied planned index instance.

        One worker, chronological order, one logical retrieval per instance per pass,
        through the shared client. Progress is persisted after each lifecycle stage, so a
        stopped run resumes from the earliest unsatisfied required instance.
        """
        accounting = IndexRetrievalAccounting()
        if self._index_plan is None:
            return accounting

        ordered = order_instances(self._index_plan)
        already = self._satisfied_from_catalog(writer, census_run_id)
        self._satisfied_index_keys |= already
        accounting.instances_planned = len(ordered)
        accounting.instances_already_satisfied = len(
            [item for item in ordered if item.instance_key in already]
        )
        accounting.logical_budget = logical_budget(
            self._index_plan, sorted(self._satisfied_index_keys)
        )

        for instance in ordered:
            if instance.instance_key in self._satisfied_index_keys:
                # Verified satisfied by an earlier process: reuse it, do not re-request.
                continue
            if not instance.required:
                # The provisional open quarter was not explicitly included.
                self._record_instance_state(
                    writer,
                    census_run_id,
                    instance,
                    "planned",
                    detail=(
                        "provisional open quarter excluded from this plan; not retrieved "
                        "and not missing"
                    ),
                )
                continue
            if accounting.logical_retrievals_initiated >= accounting.logical_budget:
                accounting.stopped_early = True
                accounting.stop_reason = "request_boundary_reached"
                break

            outcome = retrieve_instance(
                client,
                store,
                instance,
                on_state=partial(self._on_instance_state, writer, census_run_id),
            )
            accounting.logical_retrievals_initiated += outcome.logical_retrievals
            accounting.http_attempts += outcome.http_attempts

            if outcome.observation is not None:
                recorder.record(outcome.observation)

            if outcome.state != "parsed":
                accounting.instances_failed += 1
                accounting.outcomes.append(outcome)
                self._record_instance_state(
                    writer,
                    census_run_id,
                    instance,
                    outcome.state,
                    observation_id=(
                        None if outcome.observation is None else outcome.observation.observation_id
                    ),
                    logical_retrievals=outcome.logical_retrievals,
                    http_attempts=outcome.http_attempts,
                    reason_codes=outcome.reason_codes,
                    detail=outcome.detail,
                )
                if outcome.global_stop_reason is not None:
                    accounting.stopped_early = True
                    accounting.stop_reason = outcome.global_stop_reason
                    break
                # An ordinary per-instance failure lets later quarters proceed.
                continue

            settled = self._reconcile_instance(writer, census_run_id, catalog, instance, outcome)
            accounting.outcomes.append(settled)
            if settled.satisfied:
                accounting.instances_successful += 1
                self._satisfied_index_keys.add(instance.instance_key)
            else:
                accounting.instances_failed += 1

        self._persist_accounting(writer, census_run_id, accounting)
        return accounting

    def _on_instance_state(
        self,
        writer: CatalogWriter,
        census_run_id: str,
        state: InstanceLifecycleState,
        outcome: IndexInstanceOutcome,
    ) -> None:
        """Persist one intermediate lifecycle transition.

        A named bound method rather than a closure over the loop variable, so the
        binding is explicit and cannot capture a later iteration's instance.
        """
        self._record_instance_state(
            writer,
            census_run_id,
            outcome.instance,
            state,
            observation_id=(
                None if outcome.observation is None else outcome.observation.observation_id
            ),
            logical_retrievals=outcome.logical_retrievals,
            http_attempts=outcome.http_attempts,
        )

    def _reconcile_instance(
        self,
        writer: CatalogWriter,
        census_run_id: str,
        catalog: CensusCatalog,
        instance: IndexInstancePlan,
        outcome: IndexInstanceOutcome,
    ) -> IndexInstanceOutcome:
        """Persist parsed rows, reconcile against submissions, and settle the instance.

        Only a ``parsed`` outcome reaches here, which by construction carries both a parse
        result and an observation. Binding them to locals behind an explicit guard states
        that contract in code and narrows both types, instead of asserting it.

        Raises:
            RawObjectIntegrityError: the outcome lacked the parse or observation a parsed
                state guarantees, which would mean the caller mis-routed it.
        """
        parse = outcome.parse
        observation = outcome.observation
        if parse is None or observation is None:
            message = (
                f"instance {instance.instance_key} reached reconciliation in state "
                f"{outcome.state!r} without both a parse result and an observation"
            )
            raise RawObjectIntegrityError(message)
        catalog.persist(parse, source_observation_id=observation.observation_id)
        self._record_instance_state(
            writer,
            census_run_id,
            instance,
            "parsed",
            observation_id=observation.observation_id,
            logical_retrievals=outcome.logical_retrievals,
            http_attempts=outcome.http_attempts,
        )

        # Both sides must be keyed identically before comparison. The index parser keeps
        # the source-native dashed accession it read from the file-name column, while the
        # catalog stores the undashed plain form. Comparing them unnormalized would make
        # every accession look index-only *and* submissions-only at once.
        rows = [self._normalized_index_row(record.payload) for record in parse.records]
        submissions = self._submissions_accessions(writer)
        report = reconcile_index(
            rows,
            submissions,
            required_instances=[
                ReconciliationInstance(
                    year=instance.year,
                    quarter=instance.quarter,
                    retrieved=True,
                    observation_id=observation.observation_id,
                    parse_usable=True,
                )
            ],
            index_observation_id=observation.observation_id,
        )
        self._persist_reconciliation(writer, census_run_id, report)
        # Lower-authority index evidence is now persisted as observations, so the
        # Decision 012 resolver picks it up on the canonical rebuild below. It may
        # corroborate or conflict; it can never override entity submissions outside the
        # correction rules.
        catalog.resolve_persisted_accessions()

        state: InstanceLifecycleState = "satisfied"
        detail = f"{instance.instance_key} retrieved, verified, parsed, persisted, and reconciled"
        if report.blocks_completion:
            state = "failed"
            detail = (
                f"{instance.instance_key} reconciliation did not satisfy its QA gate: "
                f"{report.reason_codes}"
            )
        self._record_instance_state(
            writer,
            census_run_id,
            instance,
            state,
            observation_id=observation.observation_id,
            logical_retrievals=outcome.logical_retrievals,
            http_attempts=outcome.http_attempts,
            reason_codes=report.reason_codes,
            detail=detail,
            reconciled=True,
            satisfied=state == "satisfied",
        )
        return replace(
            outcome,
            state=state,
            reason_codes=report.reason_codes,
            detail=detail,
        )

    @staticmethod
    def _normalized_index_row(payload: Mapping[str, Any]) -> dict[str, Any]:
        """Return an index row keyed by the canonical undashed accession.

        The source-native dashed value is retained under ``accession_source_native`` so
        the parsed record and the comparison never disagree about what the index said.
        """
        row = dict(payload)
        raw = row.get("accession_plain")
        if raw:
            row["accession_source_native"] = raw
            # Invalid values stay source-native for indeterminate reconciliation.
            with suppress(IdentifierError):
                row["accession_plain"] = parse_accession(str(raw)).plain
        return row

    @staticmethod
    def _submissions_accessions(writer: CatalogWriter) -> list[SubmissionsAccession]:
        """Read submissions-derived accessions for comparison."""
        rows = writer.connection.execute(
            "SELECT accession_plain, form_type, registrant_cik_numeric, filing_date_sec, "
            "source_observation_id FROM census_accessions ORDER BY accession_plain"
        ).fetchall()
        return [
            SubmissionsAccession(
                accession_plain=str(row["accession_plain"]),
                form_type=None if row["form_type"] is None else str(row["form_type"]),
                cik_padded=f"{int(row['registrant_cik_numeric']):010d}",
                date_filed=None if row["filing_date_sec"] is None else str(row["filing_date_sec"]),
                observation_id=str(row["source_observation_id"]),
            )
            for row in rows
        ]

    def _satisfied_from_catalog(
        self,
        writer: CatalogWriter,
        census_run_id: str,
    ) -> set[str]:
        """Return instance keys a previous pass already satisfied and verified.

        Verification is required before reuse: the observation must still exist and its
        stored payload must still match its recorded hashes. An instance whose evidence
        no longer verifies is not treated as satisfied.
        """
        rows = writer.connection.execute(
            "SELECT instance_key, observation_id FROM census_index_instances "
            "WHERE satisfied = 1 AND reconciled = 1 ORDER BY instance_key"
        ).fetchall()
        verified: set[str] = set()
        for row in rows:
            observation_id = row["observation_id"]
            if observation_id is None:
                continue
            present = writer.connection.execute(
                "SELECT 1 FROM census_source_observations WHERE observation_id = ?",
                (str(observation_id),),
            ).fetchone()
            lineage = writer.connection.execute(
                "SELECT 1 FROM census_parser_runs WHERE source_observation_id = ?",
                (str(observation_id),),
            ).fetchone()
            if present is not None and lineage is not None:
                verified.add(str(row["instance_key"]))
        return verified

    def _record_instance_state(
        self,
        writer: CatalogWriter,
        census_run_id: str,
        instance: IndexInstancePlan,
        state: str,
        *,
        observation_id: str | None = None,
        logical_retrievals: int = 0,
        http_attempts: int = 0,
        reason_codes: tuple[str, ...] = (),
        detail: str = "",
        reconciled: bool = False,
        satisfied: bool = False,
    ) -> None:
        """Persist one lifecycle transition transactionally and append its event."""
        now = utc_now()
        with transaction(writer.connection) as connection:
            connection.execute(
                "INSERT INTO census_index_instances "
                "(census_run_id, instance_key, year, quarter, required, retrieved, "
                "parse_usable, observation_id, recorded_at_utc, lifecycle_state, "
                "instance_kind, reconciled, satisfied, logical_retrievals, "
                "http_attempts, reason_codes_json, detail, updated_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(census_run_id, instance_key) DO UPDATE SET "
                "lifecycle_state = excluded.lifecycle_state, "
                "retrieved = MAX(census_index_instances.retrieved, excluded.retrieved), "
                "parse_usable = MAX(census_index_instances.parse_usable, "
                "  excluded.parse_usable), "
                "observation_id = COALESCE(excluded.observation_id, "
                "  census_index_instances.observation_id), "
                "reconciled = MAX(census_index_instances.reconciled, excluded.reconciled), "
                "satisfied = MAX(census_index_instances.satisfied, excluded.satisfied), "
                "logical_retrievals = census_index_instances.logical_retrievals + "
                "  excluded.logical_retrievals, "
                "http_attempts = MAX(census_index_instances.http_attempts, "
                "  excluded.http_attempts), "
                "reason_codes_json = excluded.reason_codes_json, "
                "detail = excluded.detail, "
                "updated_at_utc = excluded.updated_at_utc",
                (
                    census_run_id,
                    instance.instance_key,
                    instance.year,
                    instance.quarter,
                    int(instance.required),
                    int(
                        state
                        in {"retrieved", "validly_reused", "parsed", "reconciled", "satisfied"}
                    ),
                    int(state in {"parsed", "reconciled", "satisfied"}),
                    observation_id,
                    now,
                    state,
                    instance.kind,
                    int(reconciled),
                    int(satisfied),
                    logical_retrievals if state == "retrieval_started" else 0,
                    http_attempts,
                    json.dumps(list(reason_codes)),
                    detail,
                    now,
                ),
            )
            connection.execute(
                "INSERT INTO census_index_instance_events "
                "(event_id, census_run_id, instance_key, lifecycle_state, observation_id, "
                "logical_retrievals, http_attempts, reason_codes_json, detail, "
                "occurred_at_utc) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    new_event_id(),
                    census_run_id,
                    instance.instance_key,
                    state,
                    observation_id,
                    logical_retrievals,
                    http_attempts,
                    json.dumps(list(reason_codes)),
                    detail,
                    now,
                ),
            )

    @staticmethod
    def _persist_reconciliation(
        writer: CatalogWriter,
        census_run_id: str,
        report: ReconciliationReport,
    ) -> None:
        """Persist every reconciliation comparison, including the disagreements."""
        now = utc_now()
        with transaction(writer.connection) as connection:
            for item in report.outcomes:
                connection.execute(
                    "INSERT OR IGNORE INTO census_index_reconciliation "
                    "(reconciliation_id, census_run_id, accession_plain, state, "
                    "instance_key, index_values_json, submissions_values_json, "
                    "index_observation_id, submissions_observation_id, "
                    "conflicting_fields_json, is_approved_form, reason_codes_json, "
                    "detail, policy_version, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        new_event_id(),
                        census_run_id,
                        item.accession_plain,
                        item.state,
                        item.instance_key,
                        json.dumps(dict(item.index_values), sort_keys=True, default=str),
                        json.dumps(dict(item.submissions_values), sort_keys=True, default=str),
                        item.index_observation_id,
                        item.submissions_observation_id,
                        json.dumps(list(item.conflicting_fields)),
                        int(item.is_approved_form),
                        json.dumps(list(item.reason_codes)),
                        item.detail,
                        report.policy_version,
                        now,
                    ),
                )

    @staticmethod
    def _persist_accounting(
        writer: CatalogWriter,
        census_run_id: str,
        accounting: IndexRetrievalAccounting,
    ) -> None:
        """Persist per-run accounting with logical and actual counts kept apart."""
        with transaction(writer.connection) as connection:
            connection.execute(
                "INSERT INTO census_index_retrieval_accounting "
                "(census_run_id, instances_planned, instances_already_satisfied, "
                "logical_budget, logical_retrievals_initiated, http_attempts, retries, "
                "instances_successful, instances_failed, instances_remaining, "
                "stopped_early, stop_reason, recorded_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(census_run_id) DO UPDATE SET "
                "instances_planned = excluded.instances_planned, "
                "instances_already_satisfied = excluded.instances_already_satisfied, "
                "logical_budget = excluded.logical_budget, "
                "logical_retrievals_initiated = excluded.logical_retrievals_initiated, "
                "http_attempts = excluded.http_attempts, retries = excluded.retries, "
                "instances_successful = excluded.instances_successful, "
                "instances_failed = excluded.instances_failed, "
                "instances_remaining = excluded.instances_remaining, "
                "stopped_early = excluded.stopped_early, "
                "stop_reason = excluded.stop_reason",
                (
                    census_run_id,
                    accounting.instances_planned,
                    accounting.instances_already_satisfied,
                    accounting.logical_budget,
                    accounting.logical_retrievals_initiated,
                    accounting.http_attempts,
                    accounting.retries,
                    accounting.instances_successful,
                    accounting.instances_failed,
                    accounting.instances_remaining,
                    int(accounting.stopped_early),
                    accounting.stop_reason,
                    utc_now(),
                ),
            )

    def _persist_index_instances(self, writer: CatalogWriter, census_run_id: str) -> None:
        """Persist every planned quarterly index instance for this run.

        Future quarters are deliberately not written: they are not planned, so they must
        not appear as rows that could later be read as missing.
        """
        if self._index_plan is None:
            return
        now = utc_now()
        with transaction(writer.connection) as connection:
            for item in self._index_plan.instances:
                connection.execute(
                    "INSERT INTO census_index_instances "
                    "(census_run_id, instance_key, year, quarter, required, retrieved, "
                    "parse_usable, observation_id, recorded_at_utc) "
                    "VALUES (?, ?, ?, ?, ?, 0, 0, NULL, ?) "
                    "ON CONFLICT(census_run_id, instance_key) DO UPDATE SET "
                    "required = excluded.required",
                    (
                        census_run_id,
                        item.instance_key,
                        item.year,
                        item.quarter,
                        int(item.required),
                        now,
                    ),
                )

    def index_coverage(self) -> Mapping[str, object]:
        """Return the coverage summary, keeping finalized and provisional parts apart."""
        if self._index_plan is None:
            return {
                "index_planning": "not_requested",
                "detail": (
                    "no coverage window was supplied, so no quarterly index instance was "
                    "planned and no reconciliation coverage is claimed"
                ),
            }
        open_instance = self._index_plan.provisional_open
        return coverage_summary(
            self._index_plan,
            satisfied_keys=sorted(self._satisfied_index_keys),
            retrieved_open=bool(
                open_instance is not None
                and open_instance.instance_key in self._satisfied_index_keys
            ),
        )

    def _index_coverage_reasons(self) -> tuple[str, ...]:
        """Return blocking reasons for required closed-quarter index coverage.

        Only required closed quarters block. The provisional open quarter is reported
        separately and never fails closed-quarter historical completion, and a future
        quarter is not planned at all, so it is neither missing nor a failure.
        """
        if self._index_plan is None:
            return ()
        satisfied = self._satisfied_index_keys
        return tuple(
            f"index_required_closed_quarter_missing:{item.instance_key}"
            for item in self._index_plan.required_closed
            if item.instance_key not in satisfied
        )

    def _base_plan(self, source_id: str) -> PlannedSourceState:
        """Plan one required base source instance.

        The annual calendar's requested target year is part of the instance identity,
        so re-running the census for a different year produces a distinct, deterministic
        plan instance rather than silently reusing the previous year's verdict.
        """
        spec = SOURCES[source_id]
        url = spec.url()
        identity = request_identity(source_id, url)
        discriminator = identity
        if source_id == "sec_edgar_filing_calendar":
            discriminator = f"{identity}|target_year={self._calendar_target_year}"
        return PlannedSourceState(
            instance_id=_plan_instance_id("base", source_id, discriminator),
            source_id=source_id,
            request_identity=identity,
            required=True,
            scope="base",
        )

    @staticmethod
    def _historical_plan(
        cik: str,
        reference: HistoricalFileReference,
    ) -> PlannedSourceState:
        source_id = "sec_submissions_historical"
        # Bind the name to a local after the guard so it is a concrete ``str`` from here
        # on. A malformed reference never reaches URL construction.
        historical_file = reference.name
        if not reference.is_retrievable or historical_file is None:
            message = (
                "refusing to plan a retrieval for a malformed historical reference at "
                f"{reference.location.describe()}: {'; '.join(reference.problems)}"
            )
            raise ProhibitedRetrievalError(message)
        parameters = {"historical_file": historical_file}
        url = SOURCES[source_id].url(**parameters)
        identity = request_identity(source_id, url, parameters)
        return PlannedSourceState(
            instance_id=_plan_instance_id(
                "historical",
                source_id,
                f"{cik}|{identity}",
            ),
            source_id=source_id,
            request_identity=identity,
            required=True,
            scope="historical",
        )

    @staticmethod
    def _after_observation(
        planned: PlannedSourceState,
        observation: SourceObservation,
        outcome: ParseOutcome | None,
    ) -> PlannedSourceState:
        retrieval: RetrievalTerminalState
        if observation.outcome == "reused_snapshot":
            retrieval = "reused"
        elif observation.is_usable:
            retrieval = "retrieved"
        elif observation.outcome == "quarantined":
            retrieval = "quarantined"
        else:
            retrieval = "failed"

        reasons = {
            code
            for code in observation.reason_codes
            if code in REASON_CODES and REASON_CODES[code].blocks_release
        }
        parser_state: ParserTerminalState
        if outcome is None:
            parser_state = "missing"
            reasons.add(f"required_parser_missing:{planned.source_id}")
        elif outcome.structural_failures:
            # A nested region that was absent, null, wrongly typed, or internally
            # inconsistent yields an unknown count. Reporting it as a completed parse
            # with zero records would manufacture a false zero, so the run fails.
            parser_state = "failed"
            for item in outcome.structural_failures:
                reasons.add(f"structural_{item.state}:{planned.source_id}:{item.region}")
            reasons.update(
                code
                for code in outcome.reason_codes
                if code in REASON_CODES and REASON_CODES[code].blocks_release
            )
        elif outcome.quarantined:
            parser_state = "quarantined"
            reasons.add(f"required_parser_quarantined:{planned.source_id}")
            reasons.update(
                code
                for code in outcome.reason_codes
                if code in REASON_CODES and REASON_CODES[code].blocks_release
            )
        else:
            parser_state = "completed"
        if retrieval not in {"retrieved", "reused"}:
            reasons.add(f"retrieval_{retrieval}:{planned.source_id}")

        return replace(
            planned,
            retrieval_state=retrieval,
            snapshot_state="verified" if observation.is_usable else "not_verified",
            parser_state=parser_state,
            qa_state="blocked" if reasons else "unknown",
            unresolved_blocking_reasons=tuple(sorted(reasons)),
            observation_id=observation.observation_id,
        )

    @staticmethod
    def _after_catalog(
        planned: PlannedSourceState,
        outcome: ParseOutcome,
    ) -> PlannedSourceState:
        reasons = set(planned.unresolved_blocking_reasons)
        if outcome.quarantined:
            reasons.add(f"required_parser_quarantined:{planned.source_id}")
        return replace(
            planned,
            catalog_state="committed",
            qa_state=(
                "passed" if planned.parser_state == "completed" and not reasons else "blocked"
            ),
            unresolved_blocking_reasons=tuple(sorted(reasons)),
        )

    @staticmethod
    def _persist_plan(
        writer: CatalogWriter,
        census_run_id: str,
        planned: PlannedSourceState,
    ) -> None:
        with transaction(writer.connection) as connection:
            connection.execute(
                "INSERT INTO census_plan_sources "
                "(census_run_id, source_instance_id, source_id, request_identity, "
                "required, source_scope, retrieval_state, snapshot_state, parser_state, "
                "catalog_state, qa_state, unresolved_blocking_reasons_json, "
                "observation_id, successful_terminal, updated_at_utc) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(census_run_id, source_instance_id) DO UPDATE SET "
                "retrieval_state = excluded.retrieval_state, "
                "snapshot_state = excluded.snapshot_state, "
                "parser_state = excluded.parser_state, "
                "catalog_state = excluded.catalog_state, "
                "qa_state = excluded.qa_state, "
                "unresolved_blocking_reasons_json = "
                "excluded.unresolved_blocking_reasons_json, "
                "observation_id = excluded.observation_id, "
                "successful_terminal = excluded.successful_terminal, "
                "updated_at_utc = excluded.updated_at_utc",
                (
                    census_run_id,
                    planned.instance_id,
                    planned.source_id,
                    planned.request_identity,
                    int(planned.required),
                    planned.scope,
                    planned.retrieval_state,
                    planned.snapshot_state,
                    planned.parser_state,
                    planned.catalog_state,
                    planned.qa_state,
                    json.dumps(list(planned.unresolved_blocking_reasons)),
                    planned.observation_id,
                    int(planned.successful_terminal),
                    utc_now(),
                ),
            )

    @staticmethod
    def _update_historical_status(
        writer: CatalogWriter,
        cik: str,
        reference: HistoricalFileReference,
        state: str,
    ) -> None:
        status = {
            "retrieved": "retrieved",
            "reused": "retrieved",
            "quarantined": "blocked",
            "blocked": "blocked",
            "unavailable": "unavailable",
            "unknown": "unknown",
            "not_retrieved": "not_retrieved",
        }.get(state, "failed")
        with transaction(writer.connection) as connection:
            connection.execute(
                "UPDATE census_historical_references SET retrieval_status = ? "
                "WHERE source_observation_id = ? AND registrant_cik_padded = ? "
                "AND historical_file = ?",
                (
                    status,
                    reference.location.observation_id,
                    cik,
                    reference.name,
                ),
            )

    @staticmethod
    def _release_blocking_count(sources: tuple[PlannedSourceState, ...]) -> int:
        """Count unresolved blockers in this run's required source plan.

        Historical QA metrics intentionally retain old failed observations. Retention
        is not the same as an unresolved current-run blocker: a later verified run
        must be able to resolve a transient source failure without deleting its audit
        evidence.
        """
        return sum(len(source.unresolved_blocking_reasons) for source in sources if source.required)

    @staticmethod
    def _start_job(writer: CatalogWriter, census_run_id: str) -> None:
        with transaction(writer.connection) as connection:
            connection.execute(
                "INSERT INTO ops_ingestion_jobs "
                "(job_id, job_kind, job_state, stage, started_at_utc, detail) "
                "VALUES (?, 'sec_census', 'running', 'M2.2', ?, ?)",
                (
                    census_run_id,
                    utc_now(),
                    "approved SEC metadata sources only; filing documents prohibited",
                ),
            )

    @staticmethod
    def _finish_job(
        writer: CatalogWriter,
        census_run_id: str,
        completed: bool,
        detail: str,
    ) -> None:
        with transaction(writer.connection) as connection:
            connection.execute(
                "UPDATE ops_ingestion_jobs SET job_state = ?, finished_at_utc = ?, "
                "detail = ? WHERE job_id = ?",
                (
                    "completed" if completed else "failed",
                    utc_now(),
                    detail,
                    census_run_id,
                ),
            )

    @staticmethod
    def _write_qa(
        tree: DataTree,
        census_run_id: str,
        metrics: tuple[QAMetric, ...],
        completion: CensusCompletionDecision,
    ) -> Path:
        destination = tree.audit / CENSUS_AUDIT_FILENAME
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "census_run_id": census_run_id,
            "report_version": "m2.2-r1-census-qa/1.0",
            "completion_contract": completion.as_record(),
            "metrics": [metric.as_record() for metric in metrics],
        }
        destination.write_text(
            json.dumps(payload, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        return destination

    @staticmethod
    def _count(connection: sqlite3.Connection, table: str) -> int:
        row = connection.execute(
            f"SELECT COUNT(*) AS rows FROM {table}"  # noqa: S608 - internal constant
        ).fetchone()
        return int(row["rows"]) if row is not None else 0


def _json_payload(
    payload: bytes,
    location: RecordLocation,
    parser_version: str,
) -> tuple[Mapping[str, Any], ParseOutcome | None]:
    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {}, _parse_failure(location, parser_version, f"malformed JSON: {exc}", payload)
    if not isinstance(decoded, dict):
        return {}, _parse_failure(
            location,
            parser_version,
            f"JSON root is {type(decoded).__name__}, not an object",
            payload,
        )
    return decoded, None


def _plan_instance_id(scope: str, source_id: str, identity: str) -> str:
    digest = hashlib.sha256(f"{scope}|{source_id}|{identity}".encode()).hexdigest()
    return f"{scope}-{digest[:24]}"


def _parse_failure(
    location: RecordLocation,
    parser_version: str,
    detail: str,
    payload: bytes,
) -> ParseOutcome:
    parser_id = parser_version.split("/", 1)[0]
    return ParseOutcome(
        parser_id=parser_id,
        parser_version=parser_version,
        quarantined=(
            QuarantinedRecord(
                location=location,
                parser_id=parser_id,
                parser_version=parser_version,
                reason_codes=("SEC_RESPONSE_MALFORMED",),
                detail=detail,
                raw_excerpt=payload[:500].decode("utf-8", "replace"),
            ),
        ),
    )
