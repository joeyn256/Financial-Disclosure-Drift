# Architecture Map — Disclosure Drift

**Purpose:** orient a reader to where each stage of the data-flow pipeline lives, without
re-reading the full milestone plan or every decision record. This is a navigation aid: it names
source modules, governing decisions, persistence, and tests, and states lifecycle status. It is
**not** an independent authority — see CLAUDE.md's authority rules. Where this map and a decision
record, migration, or module docstring disagree, the decision/migration/module controls.

Data flows top to bottom through the sections below; later sections depend on earlier ones.

## 0. Milestone boundary — what is built, and what is only defined

Added at [Decision 024](Decisions/decision_024_m2_m3_boundary_governance.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`), which fixes where Milestone 2 implementation ends, and
updated at [Decision 026](Decisions/decision_026_milestones_0_1_2_final_closeout.md)
(`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`),
which records formal closeout. This section is a **governance orientation layer**: it names no
module, migration, table, CLI command, or runtime path that does not already appear below, and it
invents none for a future milestone.

| Milestone | What it is | State |
|---|---|---|
| **Milestone 0** | The research and governance foundation: research question and framing, the novelty review and its prohibited-claims boundary, the approved preregistration, the frozen cohorts and outcome cutoffs, bootstrap seed `20260725`, the leakage register, the deviation register and D001, and Decisions 001–006. It owns no source module; the frozen definitions it fixed are executed by `cohorts.py` in §1 below | **Formally closed** (Decision 026 §6). Its frozen research definitions remain frozen — closure does not unfreeze one, and changing any still requires an approved decision record plus a reviewed code change (CLAUDE.md rule 3) |
| **Milestone 1** | Foundational configuration, frozen cohort definitions, CLI and exit-code boundary, logging, packaging, and the offline safety baseline — §§1 and 9 below | **Formally closed** (Decision 026 §7). Implemented, accepted, and in production use since Milestone 1 |
| **Milestone 2** | SEC source policy and the offline census (§2); raw-object, inventory, and catalog layers (§3); the candidate/selection/manifest schema (§4); entity selection (§5); joint accession selection (§6); reserve packages (§7); and pilot-manifest construction, terminal result identity, lifecycle enforcement, verification, and atomicity (§8) | **Formally closed** (Decision 026 §§8–10) — the deterministic **offline** SEC, storage, selection, replay, and manifest architecture through accepted Stage M2.3 S6, checkpointed at `m2.3-s6-complete`. **No live SEC pilot has been executed**: S6 creates only a `proposed` manifest, over fixtures |
| **Milestone 3** | Controlled live execution and exact-root approval: **M3.1** acquisition-path rehearsal and Gate F; **M3.2** controlled metadata-only SEC acquisition in **two sequential windows** and Gate H; **M3.3** the candidate-snapshot builder and execution rehearsal, then the frozen real pilot snapshot, deterministic execution, the exact real-data manifest, and the CLI output deferred from S6; **M3.4** the accepted approval entry point, then explicit owner approval of the exact root hash; **M3.5** integrated real-pilot acceptance and Milestone 3 closeout | **Master planning complete; Decisions 028 and 029 accepted after independent PASS; bounded M3.1 contract accepted and implementation-authorized** (Decision 024 §5.1; [Decision 027](Decisions/decision_027_m3_master_plan_and_operational_readiness.md); accepted [Decision 028](Decisions/decision_028_m3_1_readiness_corrections.md); accepted [Decision 029](Decisions/decision_029_m3_1_rehearsal_completeness_and_reason_semantics.md); [`Milestones/contracts/m3_1.md`](../Milestones/contracts/m3_1.md)). **The M3.1 acquisition-rehearsal and Gate-F planning implementation exists in the tree under `src/disclosure_drift/m3/`, `sec/request_ceiling.py`, and the `m3` CLI subcommands, and is NOT accepted.** No Milestone 3 migration, table, network allowlist, real snapshot, real manifest, approved root, or publication path exists, and no later phase is implemented or authorized |

**Assignment to Milestone 3 is not authorization to begin it** (Decision 024 §8), and **planning a
phase is not authorization to begin it either** (Decision 027 §20). Every Milestone 3 phase
additionally requires a separate accepted governance record where applicable, a bounded
implementation contract, explicit owner authorization, exact path authorization, and satisfaction of
its inherited prerequisite gates. **Closeout satisfied only the precondition** that Milestone 1 and
Milestone 2 closeout must precede any Milestone 3 implementation — **it granted no implementation
authority**, and implementation authorization remains `NO` for every phase (Decision 026 §21;
Decision 027 §20). `INDEPENDENT_M3_1_CONTRACT_REVIEW` is discharged: `Milestones/contracts/m3_1.md`
is accepted with `IMPLEMENTATION_AUTHORIZATION: YES`, and the M3.1 implementation exists in the tree
without being accepted. The **Decision 029 §11 code remediation** is implemented and the
disposable-clone validation run on the corrected tree is complete; a frozen commit and the **first
durable §17 review** by a non-author session remain — the review reproduces and records that
validation.

### Milestone 3 planning artifacts — documentation only, naming no runtime path

Recorded at Decision 027 (`ACCEPTED — OWNER APPROVED 2026-07-31`, outcome
`M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`) and corrected by accepted Decision 028.
**Every item below is a document.**
None is a module, a migration, a table, a CLI command, or a runtime path, and none creates one.

| Artifact | What it fixes |
|---|---|
| [`Docs/Decisions/decision_028_m3_1_readiness_corrections.md`](Decisions/decision_028_m3_1_readiness_corrections.md) | The accepted bounded planner-v2, A1–A12, reason-code, receipt-v2, budget, ceiling, recovery, and M3-L11 owner rulings. **Authorizes no implementation** |
| [`Milestones/contracts/m3_1.md`](../Milestones/contracts/m3_1.md) | Exact-path bounded M3.1 contract. **Accepted; `IMPLEMENTATION_AUTHORIZATION: YES`; the M3.1 implementation exists in the tree and is not accepted** |
| [`Milestones/milestone_03_master_plan.md`](../Milestones/milestone_03_master_plan.md) | The five phases, each with 36 specified fields, and their frozen internal subdivisions; the request-volume policy; the two-layer evidence model; the mandatory contents of every future phase contract |
| [`Docs/m3/operator_runbook.md`](m3/operator_runbook.md) | The 31-step Mac operator sequence, with every command labelled `AVAILABLE NOW` or `PLANNED — NOT YET IMPLEMENTED` |
| [`Docs/m3/offline_rehearsal_spec.md`](m3/offline_rehearsal_spec.md) | Two rehearsals: **A1–A12** acquisition at M3.1A, before the first SEC request; **E1–E8** execution at M3.3A, before the real snapshot freeze. **A1–A12 is implemented but has not been run to a passing operational token; E1–E8 remains unimplemented and belongs to M3.3A** |
| [`Docs/m3/execution_receipt_spec.md`](m3/execution_receipt_spec.md) | The proposed `m3-execution-receipt/2.0` design for dry-run and live commands — permitted fields, prohibited fields, serialization, storage, retention, redaction, replay, recovery, versioning, validation. **Creates no code and no table** |
| [`Docs/m3/limitations_register.md`](m3/limitations_register.md) | Every inherited limitation plus twelve new Milestone 3 entries. **Closes none** |
| [`Docs/m3/templates/`](m3/templates/request_budget.md) | The eight frozen operational templates: request budget, Gate F, Gate H, schema-drift incident, interrupted-run recovery, real-snapshot evidence, root-hash approval, and the public evidence index |

**Two rules these artifacts add to this map.**

**One:** an **execution receipt** is operational evidence and appears in **no** governed identity. It
is not part of §8's digest graph, is not a manifest input, and is not committed by
`root_manifest_sha256` or `manifest_id`. Every identity described in §§4–8 stays computable from
persisted substantive rows alone (Decision 027 §§17–18), and carries exactly one integrity identity,
`receipt_id`.

**Two:** every identity in §§4–8 is **deterministic**. Unchanged governed state plus byte-identical
canonical serialization reproduces the **same** `root_manifest_sha256`; re-deriving it changes
nothing, and only a **differing** root implies changed governed state (Decision 027 §10.2).

**One inherited defect touches §2.** Decision 013 §1 requires coverage through the **closed 2026
Q2** quarter; the planner in `index_plan.py` checks “containing quarter” before
`quarter_end <= as_of_date` and misclassifies the exact quarter end as provisional. Proposed
Decision 028 preserves Decision 013 and records the required total order and
`quarterly-index-instances/2.0`. **M3-L12 remains active and Gate F remains blocked until that
correction is implemented, tested, independently accepted, and checkpointed.** M3-L11 likewise
remains active until the reserved-path ignore, hygiene, and resolved-path CLI protections land.

**Closing a milestone does not close its accepted limitations.** Decision 020 §19.1, Decision 021
§19, Decision 022's applicability boundary, and Decision 023 §7's **O1**–**O4** all remain active and
are inherited by Milestone 3, with **O1** still an unresolved future owner-ruling condition
(Decision 026 §12).

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
  accession-level objective terms (§6 below) can still change the joint optimum. That draft's
  disposition is now frozen by
  [018](Decisions/decision_018_m23_s5_accession_selection_policy.md) §6 — it remains unchanged, stays
  `running`, is non-publishable, and is never mutated, deleted, promoted, or used as a manifest
  source. Decision 018 §3.3 confirms it does not retrofit or alter the accepted S4 selector or any S4
  persisted artifact. See "Lifecycle notes" below.

## 6. Accession selection — accepted and checkpointed (Stages S5.1 and S5.2)

**Purpose:** joint entity-accession selection so both quota families are solved as one assignment
problem.

- **Source:** [`accession_selector.py`](../src/disclosure_drift/sec/accession_selector.py) (S5.1,
  pure, in-memory — the **sole methodological selector**),
  [`accession_selection_store.py`](../src/disclosure_drift/sec/accession_selection_store.py) (S5.2,
  frozen reader, deterministic run identity, transactional persistence, reconstruction, same-ID
  idempotence).
- **Decisions:** entity-level counting units and the entity-side objective are frozen
  ([013](Decisions/decision_013_pilot_selection_mechanics.md) §3–§5). The accession-specific
  interpretation is now frozen by
  [018](Decisions/decision_018_m23_s5_accession_selection_policy.md) — roles (§7), caps (§8), entity
  accession floors (§9), the applicability-aware evidence penalty within the unchanged Decision 013
  §5 order (§3), canonical dashed accession identity and the tie-break formula (§5), the
  deterministic `selected_order` rule (§4), families and linked-amendment coverage (§10),
  cross-cutting quota operationalization (§11–§16), node-limit and failure semantics (§17), the
  retry prohibition (§18), and the S5.1/S5.2 methodological boundary (§19). See
  [`Docs/decision_index.md`](decision_index.md) and
  [`Milestones/contracts/m23_s5_1.md`](../Milestones/contracts/m23_s5_1.md).
- **Persistence:** `pilot_selected_accessions`, `pilot_selected_accession_quota_contributions`,
  `pilot_quota_results`, `pilot_quota_result_members` (migration `0009`), written inside the S5 joint
  run's single `running` window; `reference_policy_versions` joint-selector row (migration `0011`,
  INSERT-only). Decision 018 required **no DDL** (§25), and the
  `PILOT_JOINT_SELECTOR_POLICY_VERSION` constant it approved (§20) now exists in `pilot_policy.py`.
  `pilot_candidate_accessions` and `pilot_candidate_accession_registrants` are still **schema ahead
  of a writer** — no candidate-snapshot builder exists (see §4).
- **Tests:** `test_m23_accession_selector.py`, `test_m23_accession_selection_store.py`.
- **Status:** **accepted and checkpointed** — tag `m2.3-s5-complete` (`51837c0`), the combined
  S5.1–S5.3 boundary, owner-accepted 2026-07-29. The S5 joint run receives its own content-derived
  `selection_run_id`, distinct from the S4 draft's, and reaches `feasible`. `selection_result_sha256`
  is written by **Stage S6** and by nothing else (Decision 021 §6): the accepted S6 store seals it
  append-once on an already-`feasible` run, and migration `0013` enforces that at the schema layer.
  It is `NULL` in any catalog no S6 seal has run against, and **no production catalog exists**.

## 7. Reserve packages — accepted and checkpointed (Stage S5.4)

**Purpose:** deterministic same-signature replacement candidates for a selected entity that later
fails objective verification (Decision 013 §6, D11). A reserve is **constructed, never applied**;
substitution is an M2.5 event.

- **Source:** [`reserve_selector.py`](../src/disclosure_drift/sec/reserve_selector.py) (pure —
  eligibility, ranking, package assembly, signatures, no-compatible-reserve dispositions); the
  quota-contribution membership output in
  [`accession_selector.py`](../src/disclosure_drift/sec/accession_selector.py); persistence and
  fail-closed reconstruction in
  [`accession_selection_store.py`](../src/disclosure_drift/sec/accession_selection_store.py).
- **Decisions:** [013](Decisions/decision_013_pilot_selection_mechanics.md) §6 (D11, no
  discretionary substitution; complete quota-contribution signature required),
  [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §7 (reserve-package table
  design and signature contents), [020](Decisions/decision_020_m23_s5_4_reserve_architecture.md)
  (controlling: membership source, identity boundary, schema ruling, the nine owner rulings, and the
  five accepted limitations in §19.1).
- **Persistence:** `pilot_reserves`, `pilot_reserve_accessions`, `pilot_reserve_quota_contributions`,
  `pilot_selected_entity_quota_contributions`, `pilot_selected_accession_quota_contributions`,
  `pilot_quota_result_members` (migration `0009`), plus `pilot_selection_entity_reasons` (migration
  `0012`, DDL-only: one `STRICT` table and four triggers). All written inside the S5 run's single
  `running` window, in one transaction, with `running -> feasible` as its last statement.
- **Tests:** `test_m23_reserve_selector.py`, plus the reserve coverage in
  `test_m23_accession_selection_store.py`, `test_m23_pilot_schema.py`, and
  `test_migration_provenance.py`.
- **Status:** **accepted and checkpointed** — tag `m2.3-s5.4-complete`, owner-accepted 2026-07-30 on
  the final independent recommendation `ACCEPT_M23_S5_4_FOR_CHECKPOINT`. Reserves are **never
  published and are not a manifest input before Stage S6**; Decision 021 §7.4 rules that Stage S6
  binds them, with their `pilot_selection_entity_reasons` dispositions, into `reserves_sha256`.
- **A run with zero reserve packages is lawful and manifest-eligible.** Decision 020 §7.1 makes
  `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` target-specific and nonblocking, and migration `0012` accepts
  one such disposition per selected target as complete coverage.
  [Decision 022](Decisions/decision_022_m23_s6_reserve_rank_applicability.md)
  (`ACCEPTED — OWNER APPROVED 2026-07-31`) is the controlling record for what that means at Stage S6:
  crosswalk item 46's reserve rank is applicable **once per persisted package** and is **structurally
  not applicable** for a target carrying the disposition instead, while item 70 remains the total
  per-target coverage requirement. No synthetic package and no invented rank is ever created or
  serialized.

## 8. Manifest and release

**Purpose:** two distinct things live here — (a) the general release-manifest/hashing machinery
already used for non-pilot releases, and (b) the pilot-specific manifest Stage S6 produces. They are
**distinct artifacts**: the pilot manifest reuses only the hashing primitives, never
`ReleaseManifest`, `build_manifest`, or `RELEASE_SCHEMA_VERSION` (Decision 021 §13.6).

- **Source (general release machinery, implemented):**
  [`release/hashing.py`](../src/disclosure_drift/release/hashing.py) (normalized table-content
  hashing), [`release/manifest.py`](../src/disclosure_drift/release/manifest.py) (release gates,
  diffs), [`forecast/storage.py`](../src/disclosure_drift/forecast/storage.py) (capacity
  forecasting), [`audit/cohort_divergence.py`](../src/disclosure_drift/audit/cohort_divergence.py).
- **Source (pilot manifest, implemented and accepted at Stage S6):**
  [`release/pilot_manifest.py`](../src/disclosure_drift/release/pilot_manifest.py) — pure: the eight
  component digests, the five-column structural-fingerprint reduction, `selection_result_sha256`, the
  root, `manifest_id`, the thirteen-block §13.2 document schema, the 81-item §13.2.1 crosswalk, and
  the canonical-JSON renderer. No SQLite, clock, filesystem, environment, Git, or `sys.version`.
  [`sec/pilot_manifest_store.py`](../src/disclosure_drift/sec/pilot_manifest_store.py) — persistence:
  row loading, the seven fail-closed eligibility checks, append-once sealing in its own prior
  transaction, one `proposed` `pilot_manifest_versions` row written atomically with its serialized
  document, public verification, and write-free idempotent replay; it takes the six Decision 021 §8.4
  explicit arguments and infers none of them. **`pilot_projection_recovery_events` remains schema
  only** — S6 writes it not at all (Decision 021 §16).
- **Decisions:** [009](Decisions/decision_009_raw_data_governance.md) §10 (general hashing),
  [013](Decisions/decision_013_pilot_selection_mechanics.md) §7–§8 (D12 manifest hashing precedent
  the pilot manifest reuses, D13 approval semantics),
  [016](Decisions/decision_016_m23_schema_and_artifact_architecture.md) §8 (hash boundaries —
  excluded fields, dedicated `pilot_projection_recovery_events` table),
  [021](Decisions/decision_021_m23_s6_manifest_construction.md) **v0.5** (**controlling for Stage S6;
  `ACCEPTED`, owner approved 2026-07-30, binding**: the exact preimage of `selection_result_sha256` and of all eight component hashes
  plus the root, the circularity exclusions and commitment closure, manifest identity and its
  six-field immutability, manifest eligibility, the proposed-only boundary, the **complete
  pilot-manifest document contract** operationalizing
  [`milestone_2_3_pilot_selection_plan.md`](../Milestones/milestone_2_3_pilot_selection_plan.md)
  §10 — including the **exhaustive item-by-item §10 crosswalk** over all 81 atomic items with zero
  unclassified (§13.2.1) — the **five-column** structural-fingerprint partition rule, and the frozen
  **eight-trigger** migration-`0013` SQL — **status `ACCEPTED`, binding**. Its §15.5 states the append-once and identity guarantee: a run is inserted only
  unsealed, can never be replaced or deleted, cannot have `selection_run_id`, `snapshot_id`, or
  `selection_input_sha256` changed, and therefore carries a `selection_result_sha256` that is
  append-once **and remains recomputable from its persisted preimage** across every direct SQLite
  write path. Its §19.11 v0.4 finding on run replacement, deletion, and identity mutation is
  **closed** by triggers 6, 7, and 8).
- **Persistence:** `0009_m23_pilot_schema.sql` (the `pilot_manifest_versions` schema) plus
  `0013_m23_manifest_lifecycle_guards.sql` — **DDL-only, eight triggers, no table, column, or
  index**, reproducing the Decision 021 §15.1 SQL byte-for-byte and its nine §15.3 digests over a
  10939-byte, 186-line statement region. `pilot_projection_recovery_events` still has no writer.
- **Tests:** `test_m23_pilot_manifest.py` (the pure hashing, document-schema, crosswalk,
  completeness, and serialization contract), `test_m23_pilot_manifest_store.py` (eligibility,
  sealing, persistence, atomicity, verification, replay, explicit-argument discipline),
  `test_m23_pilot_schema.py` (the eight triggers adversarially under every pragma combination),
  `test_migration_provenance.py`, `test_release_forecast_and_audit.py`.
- **Status:** general release machinery accepted and in use; **pilot manifest construction is Stage
  S6 — implemented, independently accepted, and checkpointed** at `m2.3-s6-complete`. Governance is
  Decision 021 v0.5 (architecture), Decision 022 (item-46 applicability), and
  [Decision 023](Decisions/decision_023_m23_s6_acceptance_and_path_ratification.md) (acceptance,
  `M23_STAGE_S6_ACCEPTED_AND_COMPLETE`, owner approved 2026-07-31). Its contract,
  [`Milestones/contracts/m23_s6.md`](../Milestones/contracts/m23_s6.md), is now
  `ACCEPTED_AND_COMPLETE` with `IMPLEMENTATION_AUTHORIZATION: NO` and authorizes nothing further. S6
  delivered **machinery plus the complete manifest document schema, fixture-tested**, and can create
  only a `proposed` manifest: the exact real-data instance and CLI output belong to **M3.3**, owner
  approval of the root hash to **M3.4**, and Gate F live-metadata safety to **M3.1** — the phases
  Decision 024 §5.1 renamed from Stages S9, S10, and S7 — **none
  authorized**, and all unreachable while no candidate-snapshot builder and no production catalog
  exist (Decision 021 §17). Decision 023 §7 records four accepted nonblocking limitations: an empty
  sole-carrier crosswalk family fails closed (**O1**), the release root is assumed owner-controlled
  (**O2**), atomicity governs newly created artifacts only (**O3**), and item-46 enforcement is
  consistent defence in depth (**O4**).

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

This section states lifecycle semantics as defined by Decision 016 §5, Decision 018 §6/§27, and the
S4 implementation; it does not introduce any new state or transition.

- **S4 entity-only running drafts.** A Stage-S4 selection run persists entity selections and quota
  results, but its `pilot_selection_runs.run_state` is deliberately never advanced past `running`
  by S4 code. `feasible` requires the accession-level objective terms to also be solved, which S4
  does not attempt. Treat any S4 run row as a draft, not a completed selection. A permanently-
  `running` S4 draft is expected residue, not an abandoned run
  ([018](Decisions/decision_018_m23_s5_accession_selection_policy.md) §27).
- **The S5 joint entity-accession run — accepted and implemented (Decision 018 §6).** S5 produces a
  **distinct, content-derived** joint-selection run rather than editing the S4 draft in place. The
  S4 draft remains unchanged, remains in `running`, is non-publishable, and is never mutated,
  deleted, promoted, or used as a manifest source. **Only the S5 joint run may advance toward
  publication.** This was previously an S5 preflight proposal; Decision 018 froze it, and it is no
  longer an open question. Decision 016 §5's `pilot_selection_runs` lifecycle
  (`planned -> running -> {feasible, infeasible, infeasible_or_unproven}`, `failed -> running` only
  via an explicit recorded retry event) is unchanged and applies to the S5 run row; Decision 018 §18
  additionally prohibits any automatic retry and authorizes no S5 retry entry point, so
  `failed -> running` is exercised by no S5 module.
- **S6 is the manifest-machinery boundary, and it is accepted.** Manifest serialization and hashing
  (Decision 013 §7) are Stage S6, together with the complete document schema Decision 021 §13 freezes
  from milestone plan §10 and enumerates item by item in §13.2.1; the **owner-approval workflow
  (Decision 013 §8) is not** — Decision 021 §11.1 confines S6 code to creating a `proposed` manifest,
  and §17 places Gate F safety, live metadata, the exact real-data manifest instance and CLI output,
  and owner approval of the root hash in the four stages it called S7, S8, S9, and S10 — now
  **M3.1, M3.2, M3.3, and M3.4** under Decision 024 §5.1, which renamed them and altered none of
  their substance. S6 requires a `feasible` S5 joint run, which exists as an implemented path.
  **S6 is implemented, accepted, and checkpointed** (Decision 023), and **accepted S6 is the end of
  Milestone 2 implementation** (Decision 024 §2). **At the Milestone 2 / Milestone 3 boundary Decision
  024 recorded, no Milestone 3 phase had begun, none was authorized, no S7 or Milestone 3 contract
  existed, and no Milestone 3 implementation existed** — the M3.1 bounded authorization and
  implementation described below came afterwards. The
  **Milestone 2 / Milestone 3 boundary is recorded** (Decision 024), the final independent integrated
  Milestones 1–2 audit and its bounded corrections and rereviews are complete, and **Milestones 0, 1,
  and 2 are now formally closed** (Decision 026, `MILESTONES_0_1_2_FORMALLY_ACCEPTED_AND_CLOSED`).
  Closure changed no module, table, migration, or runtime path described anywhere in this map.
  **Milestone 3 master planning is likewise complete and likewise changed nothing here**
  ([Decision 027](Decisions/decision_027_m3_master_plan_and_operational_readiness.md) v0.2,
  `M3_MASTER_PLAN_AND_OPERATIONAL_READINESS_DESIGN_ACCEPTED`): the planning pack in §0 above is
  documentation, it names no module, migration, table, or CLI command that does not already appear in
  this map, and it grants no implementation authority. **v0.2 applied eleven bounded corrections after
  the required independent review of v0.1** and likewise changed no module, table, migration, or
  runtime path. Decision 028 is accepted after independent PASS, and **Decision 029 is accepted**
  (2026-08-02) as the bounded M3.1 remediation record — it likewise creates no module, table,
  migration, or runtime path, and grants no network authority. The M3.1 contract is accepted with
  `IMPLEMENTATION_AUTHORIZATION: YES` and the M3.1 implementation exists in the tree without being
  accepted; the Decision 029 §11 code remediation is implemented and the disposable-clone validation
  run on the corrected tree is complete, so a frozen commit and the **first durable §17 review** —
  which reproduces and records that validation — remain.
