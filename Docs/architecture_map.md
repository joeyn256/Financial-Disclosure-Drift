# Architecture Map — Disclosure Drift

**Purpose:** orient a reader to where each stage of the data-flow pipeline lives, without
re-reading the full milestone plan or every decision record. This is a navigation aid: it names
source modules, governing decisions, persistence, and tests, and states lifecycle status. It is
**not** an independent authority — see CLAUDE.md's authority rules. Where this map and a decision
record, migration, or module docstring disagree, the decision/migration/module controls.

Data flows top to bottom through the sections below; later sections depend on earlier ones.

## 1. Configuration and cohorts

**Purpose:** load typed, validated project configuration and expose the frozen temporal research
definitions everything else consults.

- **Source:** [`src/disclosure_drift/config.py`](../src/disclosure_drift/config.py),
  [`src/disclosure_drift/cohorts.py`](../src/disclosure_drift/cohorts.py) (canonical location for
  cohort windows, maturity gates, bootstrap seed — CLAUDE.md rule 3).
- **Decisions:** [003 v0.2](Decisions/decision_003_temporal_split.md) (cohort windows, maturity
  gates unchanged by 010), [005](Decisions/decision_005_2025_2026_recency_extension.md) (recency
  extension), [010](Decisions/decision_010_temporal_availability_and_cohort_assignment.md)
  (cohort date-source rule — controls over 003 on that point).
- **Persistence:** none (in-memory constants, `configs/project.yaml`).
- **Tests:** `tests/unit/test_cohorts.py`, `tests/unit/test_config.py`,
  `tests/unit/test_config_errors.py`, `tests/unit/test_env_overrides.py`.
- **Status:** accepted, in production use since Milestone 1.

## 2. SEC source policy and offline census

**Purpose:** define which SEC endpoints are ever contacted, under what rate/retry/response policy,
and orchestrate the read-only metadata census (Stage M2.2).

- **Source:** [`src/disclosure_drift/sec/source_registry.py`](../src/disclosure_drift/sec/source_registry.py),
  [`sources.py`](../src/disclosure_drift/sec/sources.py),
  [`urls.py`](../src/disclosure_drift/sec/urls.py),
  [`http_client.py`](../src/disclosure_drift/sec/http_client.py),
  [`httpx_transport.py`](../src/disclosure_drift/sec/httpx_transport.py),
  [`transport.py`](../src/disclosure_drift/sec/transport.py),
  [`rate_limit.py`](../src/disclosure_drift/sec/rate_limit.py),
  [`response_policy.py`](../src/disclosure_drift/sec/response_policy.py),
  [`census.py`](../src/disclosure_drift/sec/census.py),
  [`census_orchestrator.py`](../src/disclosure_drift/sec/census_orchestrator.py),
  [`census_completion.py`](../src/disclosure_drift/sec/census_completion.py),
  [`index_plan.py`](../src/disclosure_drift/sec/index_plan.py),
  [`index_retrieval.py`](../src/disclosure_drift/sec/index_retrieval.py),
  [`index_reconciliation.py`](../src/disclosure_drift/sec/index_reconciliation.py),
  [`calendar.py`](../src/disclosure_drift/sec/calendar.py),
  [`calendar_evidence.py`](../src/disclosure_drift/sec/calendar_evidence.py),
  [`parsers/`](../src/disclosure_drift/sec/parsers/).
- **Decisions:** [007](Decisions/decision_007_sec_universe.md) (SEC universe, canonical CIK
  identity), [011](Decisions/decision_011_edgar_operating_calendar_provenance.md) (operating-calendar
  provenance), [012](Decisions/decision_012_accession_observation_resolution.md) (accession
  observation resolution). As-of cutoff for M2.3: Decision 013 §1 (D1) — `2026-06-30`, closed
  quarters only.
- **Persistence:** `0002_source_observations.sql`, `0003_census_catalog.sql`,
  `0007_r2_index_retrieval.sql`.
- **Tests:** `tests/unit/test_sec_http_client.py`, `test_sec_parsers_and_census.py`,
  `test_rate_limit.py`, `test_response_policy.py`, `test_r2_index_planning.py`,
  `test_r2_index_retrieval.py`, `test_operating_calendar.py`,
  `test_operating_calendar_evidence.py`, `tests/integration/test_r2_census_end_to_end.py`.
- **Status:** accepted, in production use since Stage M2.2.

## 3. Raw-object and inventory/catalog layers

**Purpose:** durably store retrieved raw objects with full lineage, classify accessions and
amendments, and serialize every write through one catalog writer.

- **Source:** [`raw_store.py`](../src/disclosure_drift/sec/raw_store.py),
  [`snapshots.py`](../src/disclosure_drift/sec/snapshots.py),
  [`archive.py`](../src/disclosure_drift/sec/archive.py),
  [`observation_catalog.py`](../src/disclosure_drift/sec/observation_catalog.py),
  [`inventory.py`](../src/disclosure_drift/sec/inventory.py),
  [`amendments.py`](../src/disclosure_drift/sec/amendments.py),
  [`accession_resolution.py`](../src/disclosure_drift/sec/accession_resolution.py),
  [`temporal.py`](../src/disclosure_drift/sec/temporal.py),
  [`availability.py`](../src/disclosure_drift/sec/availability.py),
  [`storage/catalog.py`](../src/disclosure_drift/storage/catalog.py) (single logical writer),
  [`storage/sqlite.py`](../src/disclosure_drift/storage/sqlite.py).
- **Decisions:** [008](Decisions/decision_008_filing_inventory.md) (inventory, amendment policy),
  [009](Decisions/decision_009_raw_data_governance.md) (raw-data governance — append-only,
  CLAUDE.md rule 6), [010](Decisions/decision_010_temporal_availability_and_cohort_assignment.md)
  (temporal availability), [012](Decisions/decision_012_accession_observation_resolution.md).
- **Persistence:** `0001_initial.sql`, `0002_source_observations.sql`,
  `0004_m22_r1_safety.sql`–`0008_r3_durability_and_lineage.sql`.
- **Tests:** `test_raw_store.py`, `test_sec_snapshots.py`, `test_sec_archive.py`,
  `test_observation_catalog.py`, `test_observation_lineage.py`, `test_inventory_and_amendments.py`,
  `test_r2_accession_resolution.py`, `test_availability_boundary.py`, `test_temporal.py`,
  `test_storage_catalog.py`, `test_migration_provenance.py`, `test_projection_durability.py`.
- **Status:** accepted, in production use since Stage M2.2/R2–R3.

## 4. Candidate snapshots

**Purpose:** freeze an immutable, hashed pilot-candidate snapshot from `census_accessions`
metadata before any selection runs, per Decision 013 §2 (D2).

- **Source:** schema only — `pilot_candidate_snapshots`, `pilot_candidate_entities`,
  `pilot_candidate_accessions`, `pilot_candidate_accession_registrants`,
  `pilot_candidate_entity_evidence`, `pilot_candidate_accession_evidence`,
  `pilot_candidate_entity_reasons`, `pilot_candidate_accession_reasons`
  (migration `0009`). **No module currently writes any `pilot_candidate_*` table** — this is schema
  that exists ahead of its writer, not an implemented snapshot builder.
- **Decisions:** [013](Decisions/decision_013_pilot_selection_mechanics.md) §2 (D2),
  [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §3–§4 (table family,
  evidence normalization).
- **Persistence:** `0009_m23_pilot_schema.sql`.
- **Tests:** `test_m23_pilot_schema.py` (schema/integrity/reconstruction only — no snapshot-builder
  tests exist because no builder exists).
- **Status:** schema accepted and implemented (Stage S3); snapshot-writing logic **not
  implemented**.

## 5. Entity selection

**Purpose:** deterministic constrained entity-level selection against frozen quotas — the S4.1 pure
solver plus S4.2 persistence adapter.

- **Source:** [`entity_selector.py`](../src/disclosure_drift/sec/entity_selector.py) (S4.1, pure,
  in-memory), [`entity_selection_store.py`](../src/disclosure_drift/sec/entity_selection_store.py)
  (S4.2, persistence adapter), [`pilot.py`](../src/disclosure_drift/sec/pilot.py) (legacy
  compatibility facade), [`pilot_policy.py`](../src/disclosure_drift/pilot_policy.py) (frozen policy
  version constants).
- **Decisions:** [013](Decisions/decision_013_pilot_selection_mechanics.md) §5 (D10, selector
  policy), [014](Decisions/decision_014_pilot_evidence_and_classification_policy.md) (evidence
  levels, classification), [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md)
  §5–§6 (lifecycle, integrity), [017](Decisions/decision_017_s4_quota_policy_and_control_evidence.md)
  (frozen quota-policy version, `excluded_pool_count`, boundary-control evidence).
- **Persistence:** `pilot_selection_runs`, `pilot_selection_run_events`, `pilot_selected_entities`,
  `pilot_selected_entity_quota_contributions`, `pilot_quota_results`, `pilot_quota_result_members`
  (migration `0009`); `reference_policy_versions` quota-policy row (migration `0010`).
- **Tests:** `test_m23_entity_selector.py`, `test_m23_entity_selection_store.py`,
  `test_pilot_selection.py`.
- **Status:** **accepted and checkpointed** — tag `m2.3-s4-complete` (`e7157aa`). Persists an
  **entity-only running draft**: `run_state` stays `running`, never `feasible`, because
  accession-level objective terms (§6 below) can still change the joint optimum. See "Lifecycle
  notes" below.

## 6. Accession selection — pending Decision 018

**Purpose (intended, not implemented):** joint entity-accession selection so both quota families are
solved as one assignment problem.

- **Source: not implemented.** No `accession_selector.py` or `accession_selection_store.py` module
  exists in this repository. Any reference to these names elsewhere in this documentation set is a
  **provisional, unauthorized proposal name**, not a claim that the module exists.
- **Decisions:** entity-level counting units and the entity-side objective are frozen
  ([013](Decisions/decision_013_pilot_selection_mechanics.md) §3–§5). The accession-specific
  interpretation is **Pending — required before S5.1** (Decision 018 — does not exist yet). See
  [`Docs/decision_index.md`](decision_index.md) and
  [`Milestones/contracts/m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md).
- **Persistence:** schema exists ahead of its writer —
  `pilot_candidate_accessions`, `pilot_candidate_accession_registrants`,
  `pilot_selected_accessions`, `pilot_selected_accession_quota_contributions` (migration `0009`).
  No code writes to any of these tables.
- **Tests:** none exist for accession selection logic (there is no implementation to test).
- **Status:** **BLOCKED_PENDING_DECISION_018.** Architecture preflight for this stage is complete
  (concluded no migration-`0009` schema contradiction blocks it), but implementation has not begun
  and is not authorized until Decision 018 is approved.

## 7. Reserve packages

**Purpose (intended, not implemented):** deterministic same-signature replacement candidates for a
selected entity/accession that later fails objective verification (Decision 013 §6, D11).

- **Source:** not implemented.
- **Decisions:** [013](Decisions/decision_013_pilot_selection_mechanics.md) §6 (D11, no
  discretionary substitution; complete quota-contribution signature required),
  [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §7 (reserve-package table
  design and signature contents).
- **Persistence:** schema exists ahead of its writer — `pilot_reserves`, `pilot_reserve_accessions`,
  `pilot_reserve_quota_contributions` (migration `0009`).
- **Tests:** none (no implementation).
- **Status:** policy approved; belongs to the Stage-S5 envelope as its **S5.4** boundary — a later
  sub-stage within S5, not concurrent with S5.1. Not started.

## 8. Manifest and release

**Purpose:** two distinct things live here — (a) the general release-manifest/hashing machinery
already used for non-pilot releases, and (b) the pilot-specific manifest that Stage S6 will produce.

- **Source (general release machinery, implemented):**
  [`release/hashing.py`](../src/disclosure_drift/release/hashing.py) (normalized table-content
  hashing), [`release/manifest.py`](../src/disclosure_drift/release/manifest.py) (release gates,
  diffs), [`forecast/storage.py`](../src/disclosure_drift/forecast/storage.py) (capacity
  forecasting), [`audit/cohort_divergence.py`](../src/disclosure_drift/audit/cohort_divergence.py).
- **Source (pilot manifest, not implemented):** `pilot_manifest_versions`,
  `pilot_projection_recovery_events` exist as schema only (migration `0009`); no module serializes a
  pilot manifest.
- **Decisions:** [009](Decisions/decision_009_raw_data_governance.md) §10 (general hashing),
  [013](Decisions/decision_013_pilot_selection_mechanics.md) §7–§8 (D12 manifest hashing precedent
  the pilot manifest will reuse, D13 approval semantics),
  [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §8 (hash boundaries —
  excluded fields, dedicated `pilot_projection_recovery_events` table).
- **Persistence:** `0009_m23_pilot_schema.sql` (pilot manifest schema, unwritten).
- **Tests:** `test_release_forecast_and_audit.py`, `test_m23_pilot_schema.py` (hash-contract-adjacent
  assertions only).
- **Status:** general release machinery accepted and in use; **pilot manifest construction is Stage
  S6, not started**, and depends on S5 completing first.

## 9. Validation and CI

**Purpose:** the acceptance gates every change must pass, and how to invoke them.

- **Source:** [`Makefile`](../Makefile) (`make fast`, `make check`, `make context`),
  [`.github/workflows/ci.yml`](../.github/workflows/ci.yml) (two required jobs: core environment,
  SEC-enabled environment), [`scripts/check_no_secrets.py`](../scripts/check_no_secrets.py),
  [`scripts/check_repo_hygiene.py`](../scripts/check_repo_hygiene.py),
  [`scripts/context_snapshot.sh`](../scripts/context_snapshot.sh) (read-only live-state snapshot).
- **Decisions:** CLAUDE.md engineering conventions; no single decision record owns CI mechanics.
- **Persistence:** none.
- **Tests:** `tests/integration/test_no_network.py`, `test_cli.py`, `test_sec_cli.py`,
  `test_optional_dependencies.py`, `test_httpx_transport.py` — see
  [`Docs/change_impact_map.md`](change_impact_map.md) for the full test-selection map.
- **Status:** accepted; both CI jobs green at the accepted baseline commit.

## Lifecycle notes: S4 drafts, the planned S5 joint run, and the S6 manifest boundary

This section states existing lifecycle semantics as already defined by Decision 016 §5 and the S4
implementation; it does not introduce any new state or transition.

- **S4 entity-only running drafts.** A Stage-S4 selection run persists entity selections and quota
  results, but its `pilot_selection_runs.run_state` is deliberately never advanced past `running`
  by S4 code. `feasible` requires the accession-level objective terms to also be solved, which S4
  does not attempt. Treat any S4 run row as a draft, not a completed selection.
- **The planned S5 joint entity-accession run — proposal, not accepted design.** The read-only S5
  preflight *recommended* that S5 produce a **distinct, content-derived** joint-selection run rather
  than editing the S4 draft in place. **That recommendation is pending Decision 018 and is not
  accepted design.** This map does not freeze the S5 run-identity rule and does not freeze the S4
  draft's disposition — it does not assume disposal, supersession, reuse, or in-place rewrite. Both
  questions are Decision 018's to settle (see
  [`Milestones/contracts/m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md), "S4 draft disposition").
  What *is* already accepted is Decision 016 §5's `pilot_selection_runs` lifecycle
  (`planned -> running -> {feasible, infeasible, infeasible_or_unproven}`, `failed -> running` only
  via an explicit recorded retry event), which applies to whatever run row S5 eventually produces.
- **S6 is the final-manifest boundary.** Manifest serialization, hashing, and owner-approval
  workflow (Decision 013 §7–§8) are Stage S6 and have not started. S6 depends on a `feasible` S5
  selection run existing first; it is not reachable from the current S4-only state.
