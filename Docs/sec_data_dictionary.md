# SEC and Pilot Data Dictionary

**Version:** 0.3 (through migration `0013`, Stage M2.3-S6)
**Status:** current for the operational SQLite catalog as of migration
`0013_m23_manifest_lifecycle_guards.sql`.
**Governing records:** Decisions 007–012 (sections 1–8, the SEC ingestion and census schema);
Decisions 013, 014, 016, 017, 018, 019, 020, 021, 022, 023 (sections 9–14, the M2.3 pilot schema).
**Scope:** the complete operational SQLite catalog created by migrations `0001`–`0013`, and the
frozen Parquet release tables. Sections 1–8 cover the SEC ingestion and census layers
(migrations `0001`–`0008`). **Sections 9–14 cover the M2.3 pilot layer** (migrations
`0009`–`0013`), added at version 0.3 to close the coverage gap the final integrated Milestones 1–2
audit recorded ([Decision 025](Decisions/decision_025_integrated_audit_documentation_corrections.md)).

**Migrations are the schema ground truth; accepted decisions govern methodology and semantics.**
This dictionary describes what the migrations create and what the accepted decisions say about it.
It defines nothing of its own, and where it and a migration or decision disagree, the migration or
decision controls (CLAUDE.md authority rules). Every statement in sections 9–14 was verified against
`sqlite_master` on a scratch catalog built by the accepted `0001`–`0013` chain.

**No real pilot data exists.** No production catalog, candidate-snapshot builder, or real pilot
sample has been created; Milestone 3 has not begun and is not authorized (Decision 024).

Conventions used throughout:

- `TEXT` columns holding timestamps are ISO-8601. UTC values end in `Z`; Eastern values carry an
  explicit offset. Dates are `YYYY-MM-DD`.
- All stored paths are **relative to their configured root** (`DISCLOSURE_DRIFT_DATA_ROOT` or
  `DISCLOSURE_DRIFT_BACKUP_ROOT`). Absolute paths are never persisted.
- `NOT NULL` is stated explicitly. A nullable field is never given a silent default; missing data
  stays missing and, where policy requires, raises a review reason code.
- Tables are `STRICT` unless a note says otherwise.

## 1. Temporal fields (Decision 010)

| Field | Type | Null | Source | Notes |
|---|---|---|---|---|
| `acceptance_datetime_sec_raw` | TEXT | yes | Accession header `<ACCEPTANCE-DATETIME>`; Submissions API during discovery | Preserved verbatim, permanently. `YYYYMMDDHHMMSS` as SEC supplies it |
| `acceptance_date_sec` | TEXT | yes | Derived | First eight characters of the raw value. **Never** derived by UTC conversion |
| `acceptance_datetime_et` | TEXT | yes | Derived | Timezone-aware Eastern representation, resolved by round-tripping both daylight-saving folds through UTC. A skipped wall clock raises `REVIEW_TIMEZONE_NONEXISTENT`; a doubled one raises `REVIEW_TIMEZONE_AMBIGUOUS`. No offset is chosen automatically |
| `acceptance_datetime_utc` | TEXT | yes | Derived | Timezone-aware UTC representation of the same instant |
| `filing_date_sec` | TEXT | no | Accession header `FILED AS OF DATE`; provisional from Submissions API `filingDate` or master-index `date filed` | Official SEC filing date; authoritative for cohort assignment |
| `date_as_of_change` | TEXT | yes | Accession header `DATE AS OF CHANGE` | Retained for correction audit |
| `correction_status` | TEXT | yes | Derived | `none`, `post_acceptance_correction`, or `unresolved` |
| `resolved_value_source` | TEXT | no | Derived | Source class used for the resolved value: `accession_header`, `submissions_api`, `master_index` |
| `public_availability_date_proxy` | TEXT | no | Derived | Date-level proxy for public availability |
| `availability_precision` | TEXT | no | Derived | `timestamp` or `date` |
| `availability_basis` | TEXT | no | Derived | `same_day_acceptance`, `later_official_filing_date`, `filing_date_only` |
| `official_filing_temporal_cohort` | TEXT | no | `cohort_label_for_value(filing_date_sec)` | **Authoritative.** Always one of: the five frozen cohorts, `support_2009`, `out_of_scope`, or `unresolved`. Never `NULL` for a valid date |
| `accepted_temporal_cohort` | TEXT | no | `cohort_label_for_value(acceptance_date_sec)` | **Audit only.** Same label vocabulary; never used for analysis assignment |

### Cohort label vocabulary (Stage M2.2-R2.4)

Four meanings are kept distinct. Collapsing any of them into `NULL` would make a known
exclusion indistinguishable from an unknown date, so persistence uses
`disclosure_drift.sec.temporal.cohort_label_for_value` and never writes `NULL`.

| Label | Meaning | Analysis membership |
|---|---|---|
| `support_2009` | A valid 2009 filing date | Support only, never analysis |
| `development`, `transition`, `primary_test`, `prospective`, `monitoring` | Inside a frozen window | Eligible under that cohort's frozen role |
| `out_of_scope` | A valid, resolved date outside every supported window | None; the exclusion is *known* |
| `unresolved` | The date itself is absent, unparseable, or unresolved | None; the date is *unknown* |

`out_of_scope` and `unresolved` are never interchangeable. The first is evidence of
exclusion; the second is absence of evidence.

### Quarterly index-instance policy (Stage M2.2-R2.6)

The quarterly company index is the required reconciliation unit. Planning inputs are
explicit and persisted: `coverage_start`, `coverage_end`, `as_of_date`, and the policy
version `quarterly-index-instances/1.0`. **The as-of date is never read from the clock**
in planning or parsing, so the same request reproduces the same plan on any later day.

| Instance kind | Condition | Required | Completion effect |
|---|---|---|---|
| `required_closed_quarter` | quarter end ≤ `as_of_date` | yes | Missing, failed, malformed, unavailable, or unreconciled blocks completion |
| `provisional_open_quarter` | quarter contains `as_of_date` | optional | Retrieved only when explicitly included; reported separately; never finalized; failure never fails closed-quarter completion |
| `not_planned` | quarter starts after `as_of_date` | no | Not requested, not missing, not a failure |

A partial intersection with the coverage window still plans the whole quarter, because
the index instance is published per quarter and cannot be requested in part. An annual
index is never a substitute for a missing required quarterly instance; any future annual
support is an additional reconciliation layer only.

Coverage is reported with finalized and provisional parts kept apart: required closed
quarters planned, successful, and failed or unavailable; the provisional open quarter and
whether it was retrieved; future quarters not planned; and separate `finalized` and
`provisional` reconciliation coverage lists. `completed=True` requires every required
closed-quarter instance and every other required source to satisfy the R1 completion
contract, and never claims the open quarter or a future period is finalized.
`coverage_start`, `coverage_end`, `as_of_date`, and the exact instance list are all
included in the deterministic census-plan hash.

### Accession field resolution (Decision 012)

Canonical accession fields in `census_accessions` are **derived views** over immutable
observations, resolved per field by `census_accession_field_resolutions`. Resolution is
deterministic and independent of ingestion order; recency alone is never authority; equal
authority with conflicting values stays `unresolved`. See
`Docs/Decisions/decision_012_accession_observation_resolution.md` for the authority
hierarchy, materiality, correction handling, and the persisted resolution output.

**How observations reach canonical fields.** Three layers, in order, with no shortcut:

1. **Immutable source-native observations** — `_normalize_accession` writes one row per
   source field into `census_accession_observations`, keyed by source observation and
   parsed record. The insert into `census_accessions` at this point only *seeds* the row
   so foreign keys resolve; its canonical values are placeholders.
2. **Deterministic field-level resolution** — `CensusCatalog.resolve_persisted_accessions`
   reads the observations back **from the catalog**, maps source-native names to canonical
   names via `CANONICAL_FIELD_BY_SOURCE_FIELD`, filters to `RESOLVABLE_SOURCE_IDS`, and
   calls `resolve_accession`. Results are written to
   `census_accession_field_resolutions` and `census_accession_cohort_resolutions` with
   their resolution hashes.
3. **Canonical derived projection** — `_project_canonical` is the *only* writer of
   canonical values, and it writes solely from the persisted resolution. An unresolved
   material field projects as `NULL` with the `unresolved` cohort label.

Because step 2 reads persisted observations rather than the current parse, a rerun or a
restart rebuilds the identical resolution. An identity-alias source is excluded at both
step 2's filter and Decision 012 level 4, so it cannot contribute even a competing value
for a filing field. A `sec_full_index_company` observation may corroborate or conflict but
never overrides an entity-submissions observation outside the Decision 012 correction
rules.
| `date_divergence` | INTEGER | no | Derived | 1 when the dates differ, even inside one cohort |
| `cohort_boundary_crossing` | INTEGER | no | Derived | 1 when both dates map and the cohort names differ |
| `coverage_boundary_divergence` | INTEGER | no | Derived | 1 when one date maps and the other is unresolved or outside supported coverage; requires review and blocks freezing |
| `date_divergence_reason` | TEXT | no | Derived | `same_day_filing`, `expected_after_cutoff_rollover`, `post_acceptance_date_correction`, or `unexplained_date_divergence`. No calendar-day allowance is used. Rollover requires a proven operating day, the frozen 17:30 ET cutoff, and the next operating business day |
| `divergence_explained` | INTEGER | no | Derived | 1 for the first three reasons; `unexplained_date_divergence` blocks release freezing |

## 2. Identity fields (Decision 007)

| Field | Type | Null | Notes |
|---|---|---|---|
| `accession_number_dashed` | TEXT | no | Canonical filing identifier, `NNNNNNNNNN-NN-NNNNNN` |
| `accession_number_plain` | TEXT | no | Eighteen digits, no dashes |
| `submitter_cik_numeric` | INTEGER | no | From the accession prefix. **Never** assumed to be the registrant |
| `registrant_cik_numeric` | INTEGER | no | In `inventory_accession_registrants`; one row per registrant |
| `registrant_cik_padded` | TEXT | no | Ten-character zero-padded |
| `is_primary_registrant` | INTEGER | yes | Null when unresolved; `REVIEW_REGISTRANT_CIK_UNRESOLVED` applies |
| `form_type` | TEXT | no | `10-K`, `10-K/A`, `10-KT`, `10-KT/A`, or an unsupported form retained for control evidence |
| `alias_kind` | TEXT | no | `company_name` or `ticker`, in `inventory_company_aliases` |
| `alias_valid_from` / `alias_valid_to` | TEXT | yes | Evidence-bounded; `alias_valid_to` null means "no later evidence", not "current" |
| `lineage_relationship` | TEXT | no | `successor_of`, `predecessor_of`, `merged_into`, `reorganized_as`, `reverse_merger_with`, `de_spac_of` |

## 3. Inventory role and eligibility (Decision 008)

| Field | Type | Null | Notes |
|---|---|---|---|
| `inventory_role` | TEXT | no | `primary_target`, `support_only`, `amendment_non_target`, `control_evidence`, `excluded` |
| `primary_target_flag` | INTEGER | no | 0 for support, amendment, control, and excluded rows |
| `eligibility_state` | TEXT | no | `eligible`, `excluded`, `review_required` |
| `amendment_relationship` | TEXT | yes | `amends_original`, `amends_prior_amendment`, `supplements_original`, `possible_amendment_of`, `unresolved_amendment` |
| `amendment_parent_accession` | TEXT | yes | Null while parentage is unresolved |
| `xbrl_amendment_flag` | INTEGER | yes | Recorded separately from the EDGAR `/A` suffix; disagreement is a review condition |
| `reason_code` | TEXT | no | In `inventory_reasons`; foreign key to `reference_reason_codes` |
| `issuer_type` | TEXT | no | `operating`, `operating_financial_institution`, `asset_backed`, `registered_investment_company`, `shell_or_blank_check`, `unknown` |
| `shell_state_for_accession` | TEXT | no | Accession-specific; a former shell is not permanently excluded |

## 4. Raw-object fields (Decision 009)

| Field | Type | Null | Notes |
|---|---|---|---|
| `raw_object_id` | TEXT | no | Stable identity for a logical object |
| `observation_id` | TEXT | no | One row per retrieval observation; append-only |
| `logical_role` | TEXT | no | `complete_submission`, `sgml_header`, `index_html`, `index_json`, `primary_document`, `xbrl_instance`, `xbrl_schema`, `exhibit`, `image`, `bulk_archive`, `master_index`, `submissions_json`, `other` |
| `source_url_canonical` | TEXT | no | Canonical SEC URL |
| `relative_storage_path` | TEXT | no | Relative to the data root |
| `media_type` | TEXT | yes | As reported |
| `content_encoding_received` | TEXT | yes | As reported |
| `content_sha256` | TEXT | no | Over decoded HTTP entity bytes. **Integrity anchor** |
| `stored_sha256` | TEXT | no | Over locally stored bytes; not asserted portable across machines |
| `content_size_bytes` / `stored_size_bytes` | INTEGER | no | — |
| `retrieved_at_utc` | TEXT | no | — |
| `retrieval_attempt_id` | TEXT | no | Foreign key to `ops_retrieval_attempts` |
| `quarantine_reason_code` | TEXT | yes | In `raw_quarantine_objects`; the file is preserved, never replaced |

## 5. Operational and audit fields

| Field | Type | Null | Notes |
|---|---|---|---|
| `job_id`, `job_kind`, `job_state` | TEXT | no | `ops_ingestion_jobs`; states `pending`, `running`, `stopped`, `completed`, `failed`, `cooldown` |
| `writer_lease_id`, `writer_pid`, `lease_expires_at_utc` | TEXT / INTEGER | no | Diagnostic metadata only. Process-lifetime exclusivity is enforced by a held non-blocking OS advisory lock; timestamps never authorize takeover. |
| `attempt_state` | TEXT | no | `started`, `succeeded`, `failed`, `quarantined`, `abandoned` |
| `http_status`, `retry_after_seconds`, `action_taken` | INTEGER / TEXT | yes | `raw_http_responses`; `action_taken` from the response policy |
| `checkpoint_key`, `checkpoint_value` | TEXT | no | `ops_checkpoints`; supports resumable acquisition |
| `event_kind`, `event_payload_json` | TEXT | no | Audit tables; payloads never contain the SEC contact value |
| `parser_run_id`, `parser_version`, `failure_reason_code` | TEXT | no | `audit_parser_runs`, `audit_parser_failures`; failures are recorded, never discarded |
| `schema_drift_kind` | TEXT | no | `unknown_field_retained`, `required_field_missing`, `type_changed`, `unexpected_null`, `malformed_nested_array`, `new_historical_file_reference` |

## 6. Release fields

| Field | Type | Null | Notes |
|---|---|---|---|
| `release_id`, `release_schema_version`, `frozen_at_utc` | TEXT | no | Frozen releases are never edited |
| `table_name`, `normalized_content_sha256`, `row_count` | TEXT / INTEGER | no | Reproducibility is asserted on normalized content hashes |
| `release_content_sha256` | TEXT | no | Release-level hash over the ordered table hashes |
| `relative_file_path`, `file_sha256`, `file_size_bytes` | TEXT / INTEGER | no | Relative paths only |
| `gate_name`, `gate_result`, `blocks_release` | TEXT / INTEGER | no | `release_acceptance_results` |
| `diff_kind` | TEXT | no | `added`, `removed`, `changed`, `cohort_reassigned` |

## 6A. M2.2 source-observation and census layers

The M2.2 catalog preserves three non-interchangeable layers:

1. `census_source_observations` and `census_archive_members` retain immutable raw
   observation provenance and archive-to-member lineage.
2. `census_parser_runs`, `census_parsed_records`, and
   `census_quarantined_records` retain source-native payloads, parser identity and
   version, deterministic record hashes, source locations, unknown fields,
   warnings, duplicate/conflict indicators, and quarantine details.
3. `census_registrants`, `census_registrant_observations`, and
   `census_accessions` contain normalized census observations derived from layer 2.
   Raw SEC JSON is never written directly into these tables.

| Field / table | Notes |
|---|---|
| `transport_sha256` | Hash of decoded HTTP entity bytes delivered by the transport |
| `stored_sha256` | Hash of the exact local storage representation |
| `logical_sha256` / `content_sha256` | Hash of the parser input; archive-member hashes remain separate |
| `request_identity` | Registered source plus normalized URL and template parameters; bounds `304` reuse |
| `validators_sent_json` | Validators actually sent; required to reconcile a `304` |
| `headers_json` | Redacted response provenance headers only; the contact identity is never stored |
| `census_historical_references` | Source-named overflow metadata with explicit retrieval status |
| `census_registrant_observations` | Name, former-name, ticker, exchange, SIC, fiscal-year-end, entity-type, and official status history |
| `census_candidate_lineage_edges` | Candidate-only shared-alias evidence. It never merges CIK identities |
| `census_accession_observations` | Every source-native accession field observation, including conflicts |
| `census_calendar_days` | Tri-state day status with observation lineage and derivation version |
| `census_qa_metrics` | Deterministic QA values with explicit `value`, `zero`, `unavailable`, `failed`, `blocked`, `unknown`, or `not_retrieved` status |

### 6B. R3 durability and provenance enforcement

SQLite is authoritative; `audit/sec/census_source_observations.jsonl` is a
reconstructible projection. A canonical line is the deterministic, sorted-key
serialization of one SQLite observation, ordered by retrieval time, catalog-recording
time, and observation identity. A normal append is flushed and file-`fsync`ed before
`projected_to_audit` is set. A rebuild is written and `fsync`ed in a temporary file in
the destination directory, atomically replaces the projection, and `fsync`s that
directory before projection flags are updated.

Startup validation compares the complete projection to SQLite by observation identity,
canonical payload hash, row count, and order. Missing files, valid prefixes, truncated or
malformed lines, duplicate or unknown identities, modified payloads, reordering, and
trailing garbage cause deterministic reconstruction. Recovery history is retained in
`census_projection_recovery_events`, including the detected condition, relative
projection path, expected and observed counts, rebuild identity and hash, resolution
state, timestamps, and whether the condition blocked release before resolution.

Migration 0008 rebuilds `census_source_observations` with deferred, restrictive
self-foreign keys for `reused_observation_id` and `supersedes_observation_id`. Additional
validation rejects dangling, self-referential, cyclic, source-incompatible, or
request-identity-incompatible lineage before commit. Reuse points to a verified
object-owning observation and preserves the shared object's storage representation,
stored, logical and applicable transport hashes, sizes, relative path, parser version,
archive-member lineage, and response-encoding provenance. The new retrieval remains its
own immutable observation.
`storage_representation` describes the shared raw object; declared content type and
`content_encoding` remain response provenance (and a `304` inherits them from the
verified evidence response because it has no new entity body).

## 7. Reference tables

| Table | Seeded in M2.1 | Source |
|---|---|---|
| `reference_form_types` | Yes | Decision 007 section 3 |
| `reference_reason_codes` | Yes | `src/disclosure_drift/reasons.py` |
| `reference_cohort_definitions` | Yes | `src/disclosure_drift/cohorts.py` frozen constants |
| `reference_policy_versions` | Yes | Decisions 007–010 and this dictionary |
| `reference_sic_codes` | **Created empty** | Loaded in M2.2 from an approved SEC source snapshot; never seeded from memory |

### 7.1 EDGAR operating calendar

The operating calendar used for `expected_after_cutoff_rollover` is injected, not
embedded. Its provenance record carries `source_kind` (`synthetic_fixture` in Stage
M2.1 tests, `sec_snapshot` in production), `description`, a required `snapshot_id`
for any SEC-derived calendar, and `retrieved_at_utc`. Dates outside the calendar's
coverage yield `OPERATING_CALENDAR_UNAVAILABLE` rather than an assumed answer.

The after-hours cutoff is frozen at **17:30 America/New_York** for `10-K`, `10-K/A`,
`10-KT`, and `10-KT/A`. It has no column, no configuration key, and no environment
variable; it lives only in `src/disclosure_drift/sec/calendar.py` as
`FROZEN_FILING_CUTOFF_ET`. A purported acceptance on a non-operating day is preserved
and flagged `REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`; it never yields
`expected_after_cutoff_rollover`.

## 8. Fields that must never exist

No column stores a SEC contact value, an API key, an absolute personal path, an outcome value, an
operating-margin figure, an industry-adjusted quantity, a Disclosure Drift Index component, or any
2022–2026 outcome. Milestone 2 does not construct or link outcomes. **This prohibition applies to
the pilot layer in sections 9–14 without exception.**

## 9. M2.3 pilot layer — overview

**Migrations `0009`–`0013`, verified against `sqlite_master`.**

| Migration | Tables | Triggers | Indexes | Data | What it adds |
|---|---:|---:|---:|---:|---|
| `0009_m23_pilot_schema` | **21** | 68 | 21 | 1 row | the pilot table family (Decision 016) |
| `0010_m23_quota_policy_reference` | 0 | 0 | 0 | 1 row | `reference_policy_versions` row for `pilot_quota` (Decision 017) |
| `0011_m23_joint_selector_policy_reference` | 0 | 0 | 0 | 1 row | `reference_policy_versions` row for `pilot_joint_selector` (Decision 018 §20) |
| `0012_m23_selection_entity_reasons` | **1** | 4 | 0 | 0 | `pilot_selection_entity_reasons` + lifecycle guards (Decision 020 §8.2) |
| `0013_m23_manifest_lifecycle_guards` | 0 | **8** | 0 | 0 | DDL-only manifest and run lifecycle guards (Decision 021 §15) |

**The catalog therefore holds 22 `pilot_*` tables: the 21 migration `0009` created, plus the one
migration `0012` added.** `0010` and `0011` are INSERT-only policy-reference rows and create no
schema. `0013` is DDL-only and creates no table, column, or index.

All 22 pilot tables are `STRICT`. Every foreign key is `ON DELETE NO ACTION`. Every `*_sha256`
column carries `CHECK (length(x) = 64 AND x NOT GLOB '*[^0-9a-f]*')`.

### 9.1 State classes

| Class | Tables |
|---|---|
| **Candidate state** (frozen snapshot input) | `pilot_candidate_snapshots`, `pilot_candidate_entities`, `pilot_candidate_accessions`, `pilot_candidate_accession_registrants` |
| **Source evidence** | `pilot_candidate_entity_evidence`, `pilot_candidate_accession_evidence` |
| **Candidate reasons (audit)** | `pilot_candidate_entity_reasons`, `pilot_candidate_accession_reasons` |
| **Lifecycle state** | `pilot_selection_runs`, `pilot_selection_run_events` |
| **Selected state** | `pilot_selected_entities`, `pilot_selected_accessions` |
| **Quota state** | `pilot_quota_results`, `pilot_quota_result_members`, `pilot_selected_entity_quota_contributions`, `pilot_selected_accession_quota_contributions` |
| **Reserve state** | `pilot_reserves`, `pilot_reserve_accessions`, `pilot_reserve_quota_contributions`, `pilot_selection_entity_reasons` |
| **Manifest state** | `pilot_manifest_versions` |
| **Operational-only** | `pilot_projection_recovery_events` (no writer; Decision 021 §16 — documented in §13.5) |

### 9.2 Stage boundaries

- **S4** writes an **entity-only draft** into `pilot_selection_runs` + `pilot_selected_entities`,
  and its `run_state` is deliberately never advanced past `running`. That draft is
  **non-publishable and is never a manifest input** (Decision 018 §§6, 27; Decision 020 §11).
- **S5** creates a **distinct, content-derived** joint run that reaches `feasible` and writes the
  selected, quota, contribution, member, reserve, and disposition families inside one `running`
  window, in one transaction.
- **S6** seals `pilot_selection_runs.selection_result_sha256` in its own prior transaction, then
  writes exactly one `proposed` `pilot_manifest_versions` row together with its serialized
  canonical document, in one transaction.

**Writers, exhaustively.** `sec/entity_selection_store.py` (S4), `sec/accession_selection_store.py`
(S5, including reserves and dispositions), `sec/pilot_manifest_store.py` (S6 seal and manifest).
No other module writes a `pilot_*` table, and no module writes
`pilot_projection_recovery_events`.

## 10. Candidate layer (migration `0009`)

**No module writes any `pilot_candidate_*` table.** This is schema ahead of its writer: the
candidate-snapshot builder is Milestone 3 phase M3.3 and does not exist. S4, S5, and S6 read these
tables; accepted tests populate them from fixtures.

| Table | PK | Key uniqueness / FKs | Material CHECKs | Role |
|---|---|---|---|---|
| `pilot_candidate_snapshots` | `snapshot_id` (64-hex, content-derived) | FK `census_run_id` → `ops_ingestion_jobs`; FK `invalidated_reason_code` → `reference_reason_codes` | `snapshot_state IN ('building','frozen','invalidated')`; `include_open_quarter = 0`; each declared `*_sha256` 64-hex-or-NULL; state-conditional presence of counts and digests | Frozen snapshot header. Its 22 declared fields are the entire `candidate_tables_sha256` preimage (Decision 021 §8.2) |
| `pilot_candidate_entities` | (`snapshot_id`, `cik_numeric`) | FK → `pilot_candidate_snapshots`; idx on tie-break and on (`snapshot_id`,`size_stratum`,`industry_family`,`history_class`) | `candidate_category IN ('operating','control','ineligible')`; control ⇔ `control_kind`; `primary_universe_eligible` requires operating + provisional evidence; paired `(value IS NULL) = (resolution_sha256 IS NULL)` for size/industry/history | Candidate entity state. Feeds `entity_content_sha256` → `selection_input_sha256` |
| `pilot_candidate_accessions` | (`snapshot_id`, `accession_plain`) | UNIQUE (`snapshot_id`,`accession_number_dashed`); FK → snapshot, `reference_form_types` | `filing_date_precedence IS NULL OR = 2`; cohort/xbrl/amendment evidence-level enums; `is_amendment = 1` ⇔ linkage state present; four `*_eligible` flags | Candidate accession state. **`accession_plain` is the database and FK identity; `accession_number_dashed` is the canonical form for hashing and presentation** (Decision 018 §5) |
| `pilot_candidate_accession_registrants` | (`snapshot_id`,`accession_plain`,`registrant_cik_numeric`) | **partial UNIQUE `uq_pilot_candidate_accession_single_anchor` (`snapshot_id`,`accession_plain`) `WHERE is_anchor = 1`** — one anchor per accession | `role IN ('anchor','associated','submitter_only')`; `(role='anchor') = (is_anchor=1)` | Multi-registrant relationships |
| `pilot_candidate_entity_evidence` | `evidence_id` | FK → `pilot_candidate_entities`; idx on (`snapshot_id`,`cik_numeric`,`classification_dimension`) | `classification_dimension IN ('size','industry','history','primary_universe','identity')`; `evidence_role IN ('winning','competing','supporting')`; `precedence >= 1` | Source evidence (Decision 014; Decision 019 conversions) |
| `pilot_candidate_accession_evidence` | `evidence_id` | FK → `pilot_candidate_accessions` | as above, over the accession dimensions | Source evidence |
| `pilot_candidate_entity_reasons` | (`snapshot_id`,`cik_numeric`,`reason_scope`,`reason_code`) | FK `reason_code` → `reference_reason_codes` | `reason_scope IN ('eligibility','size','industry','history','primary_universe','identity')` | Candidate audit trail; §10 crosswalk items 44 and 76 |
| `pilot_candidate_accession_reasons` | (`snapshot_id`,`accession_plain`,`reason_scope`,`reason_code`) | FK `reason_code` → `reference_reason_codes` | `reason_scope IN ('eligibility','cohort','xbrl','amendment','multi_registrant','identity')` | Candidate audit trail |

**Digest contribution.** The candidate layer contributes to `candidate_tables_sha256` through the
snapshot's **declared** component digests, which Decision 021 §8.2 binds as the accepted
representation rather than recomputing. Candidate row content is independently bound through
`selection_input_sha256`, which S5 derives from the frozen rows and S6 re-derives at
reconstruction — so the content is proven, not trusted (Decision 021 §19.2).

## 11. Selection layer (migration `0009`)

| Table | PK | Key uniqueness / FKs | Material CHECKs | Lifecycle / role |
|---|---|---|---|---|
| `pilot_selection_runs` | `selection_run_id` (64-hex, content-derived) | UNIQUE (`selection_run_id`,`snapshot_id`); FK → `pilot_candidate_snapshots` | `run_state` enum; `feasible` requires both counts non-NULL; `node_limit_exhausted = 0 OR run_state='infeasible_or_unproven'`; `selection_result_sha256` 64-hex-or-NULL | **18 columns.** Lifecycle `planned → running → {feasible, infeasible, infeasible_or_unproven}`. `selection_result_sha256` is **append-once** and, from migration `0013`, so is the run's identity (§13.2) |
| `pilot_selection_run_events` | `event_id` | UNIQUE (`selection_run_id`,`attempt_number`); FK → run, `reference_reason_codes` | `from_state`/`to_state` enums; `attempt_number >= 1` | Transition audit. **Excluded from every digest** (Decision 021 §6.3) |
| `pilot_selected_entities` | (`selection_run_id`,`snapshot_id`,`cik_numeric`) | UNIQUE (`selection_run_id`,`snapshot_id`,`selected_order`); FK → run, candidate entities | `entity_role IN ('operating','control')`; `selected_order >= 1`; `entity_hash_sha256` 64-hex | **Selected state.** Its frozen eleven-column tuple is the whole `selected_entities_sha256` preimage (Decision 021 §7.1) |
| `pilot_selected_accessions` | (`selection_run_id`,`snapshot_id`,`accession_plain`) | UNIQUE (`selection_run_id`,`snapshot_id`,`selected_order`); FK → run, selected entities, candidate accessions | `accession_role IN ('base','stress','support','control')` — **mutually exclusive**; `selected_order >= 1` | **Selected state.** Frozen seven-column tuple = `selected_accessions_sha256` (Decision 021 §7.2) |
| `pilot_quota_results` | `quota_result_id` | UNIQUE (`selection_run_id`,`snapshot_id`,`quota_dimension`,`quota_key`); UNIQUE (`quota_result_id`,`selection_run_id`,`snapshot_id`) | `comparison_operator IN ('exact','at_least','at_most')`; operator-consistent pass conditions; **`quota_result='pass'` requires `evidence_state='provisional'`** | **Quota state.** Fourteen columns feed `quota_report_sha256`; a four-column subset feeds `quota_definitions_sha256` (Decision 021 §§7.3, 8.3) |
| `pilot_quota_result_members` | (`quota_result_id`,`member_order`) | FK → quota results, selected entities, selected accessions | `member_kind IN ('entity','accession')` with `(kind='entity') = (cik_numeric IS NOT NULL)` and the accession mirror | Quota membership provenance → `quota_report_sha256` |
| `pilot_selected_entity_quota_contributions` | (`selection_run_id`,`snapshot_id`,`cik_numeric`,`quota_dimension`,`quota_key`) | FK → selected entities | — | Contribution arithmetic → `quota_report_sha256`. **Load-bearing for the reserve trigger** (Decision 020 §6) |
| `pilot_selected_accession_quota_contributions` | (`selection_run_id`,`snapshot_id`,`accession_plain`,`quota_dimension`,`quota_key`) | FK → selected accessions | — | Contribution provenance → `quota_report_sha256` |

**Reconstruction and replay.** `reconstruct_persisted_joint_selection` re-derives the run from the
frozen snapshot under its own recorded seed, policy versions, and node limit, and compares every
`JointSelectionRunIdentity` field. Same-ID replay reads, reconstructs, compares, and returns; it
never overwrites, and a stored-content mismatch is a `GateFailureError`.

## 12. Reserve layer (migrations `0009` and `0012`)

| Table | Migration | PK | Key uniqueness / FKs | Material CHECKs | Role |
|---|---|---|---|---|---|
| `pilot_reserves` | `0009` | `reserve_package_id` (64-hex, content-derived) | **UNIQUE (`selection_run_id`,`snapshot_id`,`target_cik_numeric`,`reserve_rank`)** — one package per target per rank; FK → run, selected entities, candidate entities | **`replaces_signature_sha256 = reserve_signature_sha256`** (exact-equality rule); `target_cik_numeric <> replacement_cik_numeric`; `reserve_rank >= 1`; `evidence_floor` enum | Reserve packages. Twelve-column tuple → `reserves_sha256` (Decision 021 §7.4). A reserve is **constructed, never applied** (Decision 013 §6) |
| `pilot_reserve_accessions` | `0009` | (`reserve_package_id`,`accession_plain`) | UNIQUE (`reserve_package_id`,`accession_order`); FK → reserves, candidate accessions | `accession_role` enum; `accession_order >= 1` | Reserve bundle → `reserves_sha256` |
| `pilot_reserve_quota_contributions` | `0009` | (`reserve_package_id`,`quota_dimension`,`quota_key`) | FK → reserves | — | Reserve contribution set → `reserves_sha256` |
| `pilot_selection_entity_reasons` | **`0012`** | (`selection_run_id`,`snapshot_id`,`cik_numeric`,`reason_scope`) | FK → selected entities, `reference_reason_codes` | **`reason_scope IN ('reserve')`**; reserve scope admits only `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` | Durable **no-compatible-reserve disposition** → `reserves_sha256` |

**Migration `0012` triggers — four, all on the reserve-disposition path (Decision 020 §8.2):**

| Trigger | Target | Event | Protected invariant |
|---|---|---|---|
| `pilot_selection_entity_reasons_insert_guard` | `pilot_selection_entity_reasons` | `BEFORE INSERT` | a disposition may be written only inside the run's `running` window |
| `pilot_selection_entity_reasons_update_guard` | `pilot_selection_entity_reasons` | `BEFORE UPDATE` | `selection_run_id`, `snapshot_id`, and `cik_numeric` immutable; checks **both** the OLD and the NEW associated run |
| `pilot_selection_entity_reasons_delete_guard` | `pilot_selection_entity_reasons` | `BEFORE DELETE` | dispositions are not deleted outside the `running` window |
| `pilot_selection_run_feasible_requires_reserve_disposition` | `pilot_selection_runs` | `BEFORE UPDATE OF run_state` | **total, mutually exclusive** reserve coverage for every selected target before the run may reach `feasible`. Its `WHEN` condition narrows the trigger to the single transition `NEW.run_state = 'feasible' AND OLD.run_state = 'running'`; the declared event itself is the unqualified `BEFORE UPDATE OF run_state` |

**Coverage rule (Decision 020 §7.1, Decision 022).** Every selected target carries **exactly one**
of: one rank-1 package, or one `REVIEW_PILOT_NO_COMPATIBLE_RESERVE` disposition. Never both, never
neither. **A run with zero packages and complete dispositions is lawful and manifest-eligible**;
Decision 022 rules that crosswalk item 46's reserve rank is applicable **once per persisted
package** and is **structurally not applicable** for a target covered by a disposition. **No
synthetic package, `reserve_rank = 0`, `null`, `"N/A"`, or invented rank is ever created or
serialized.**

## 13. Manifest layer (migrations `0009` and `0013`)

### 13.1 `pilot_manifest_versions`

**24 columns.** PK `manifest_id` (64-hex, content-derived from root/ordinal/supersedes,
Decision 021 §9.1). Three uniqueness routes, all load-bearing for the replacement guard:

| Route | Index | Definition |
|---|---|---|
| 1 | `sqlite_autoindex_…_1` | `manifest_id` `TEXT PRIMARY KEY` |
| 2 | `sqlite_autoindex_…_2` | UNIQUE (`selection_run_id`, `snapshot_id`, `ordinal_version`) |
| 3 | `uq_pilot_manifest_single_active_approval` | partial UNIQUE (`selection_run_id`, `snapshot_id`) `WHERE manifest_state = 'owner_approved'` |

FKs → `pilot_selection_runs` (`selection_run_id`, `snapshot_id`) and self (`supersedes_manifest_id`).
Material CHECKs: all nine digest columns 64-hex; `manifest_state IN ('proposed','owner_approved',
'rejected','superseded')`; **`approved_root_sha256 = root_manifest_sha256`** whenever state is
`owner_approved` or `superseded`; `relative_manifest_path` non-empty and relative;
`supersedes_manifest_id <> manifest_id`; state-conditional timestamp presence.

**Field classification — the distinction that matters:**

| Kind | Fields | Rule |
|---|---|---|
| **Immutable governed identity** | `manifest_id`, `manifest_schema_version`, `selection_run_id`, `snapshot_id`, `ordinal_version`, `supersedes_manifest_id` | Fixed at `INSERT`, never updated (Decision 021 §9.2), enforced by trigger 4 |
| **Substantive identity** | the eight component digests + `root_manifest_sha256` | Immutable via migration `0009`'s hashes guard; each re-derives from persisted rows |
| **Mutable operational** | `manifest_state`, `approval_reference`, `approved_root_sha256`, `relative_manifest_path`, `detail` | Move under `0009`'s transition guard; correctable without touching identity |
| **Operational envelope** | `generated_at_utc`, `approved_at_utc`, `rejected_at_utc`, `superseded_at_utc` | Excluded from every digest **and from the document's substantive body** (Decision 021 §13.4) |

**S6 writes only `manifest_state = 'proposed'`**, always with `supersedes_manifest_id = NULL`, and
never populates an approval field. Approval is Milestone 3 phase M3.4.

### 13.2 Migration `0013` trigger inventory (Decision 021 §15.1)

**Five target `pilot_selection_runs`; three target `pilot_manifest_versions`** — verified against
`sqlite_master`. All eight abort with `RAISE(ABORT)`; none depends on a pragma.

| # | Trigger | Target | Event | Protected invariant | Identical restatement | §21 |
|---|---|---|---|---|---|---|
| 1 | `pilot_selection_run_insert_unsealed_guard` | runs | `BEFORE INSERT` | every run is inserted **unsealed** | n/a — refuses any pre-sealed INSERT | §15.1 b1 |
| 2 | `pilot_selection_run_result_hash_guard` | runs | `BEFORE UPDATE OF selection_result_sha256` | seal only on a run `feasible` **before and after**; a sealed digest may neither change nor clear | **permitted** — identical reseal is idempotent | §15.1 b2 |
| 3 | `pilot_manifest_versions_insert_guard` | manifests | `BEFORE INSERT` | requires an existing **`feasible`, sealed** run whose snapshot matches | n/a | §15.1 b3 |
| 4 | `pilot_manifest_versions_identity_guard` | manifests | `BEFORE UPDATE OF` the six identity columns | all six immutable; OLD **and** NEW run must be feasible and sealed | **permitted** — identical six-field restatement is a no-op | §15.1 b4 |
| 5 | `pilot_manifest_versions_replacement_guard` | manifests | `BEFORE INSERT` | closes **all three** uniqueness routes against `INSERT OR REPLACE` / `OR IGNORE` / duplicate | n/a | §15.1 b5 |
| 6 | `pilot_selection_run_replacement_guard` | runs | `BEFORE INSERT` | an existing run is never replaced or re-inserted | n/a | §15.1 b6 |
| 7 | `pilot_selection_run_delete_guard` | runs | `BEFORE DELETE` | **unconditional** — runs are undeletable in every state | n/a | §15.1 b7 |
| 8 | `pilot_selection_run_identity_guard` | runs | `BEFORE UPDATE OF selection_run_id, snapshot_id, selection_input_sha256` | the three persisted identity fields are immutable | **permitted** — identical three-field restatement is a no-op | §15.1 b8 |

`selection_input_schema_version` is **not** a column on `pilot_selection_runs`; it is immutable by
absence and enters the preimages as the accepted code constant
`ACCESSION_SELECTION_INPUT_SCHEMA_VERSION` (Decision 021 §3.6).

**Normative region:** 10939 bytes over 186 lines, SHA-256
`7f473802db7471f31106c5b19bc33376424594db88ae6d50f0a4dbf827f0d595`, byte-identical to Decision 021
§15.1 with all eight per-block digests reproducing.

**The §15.5 guarantee.** Together these make `selection_result_sha256` **append-once and
recomputable from its persisted preimage** across every direct SQLite write path.

### 13.3 Digest dependency map (Decision 021 §§6–10)

```
census_source_observations ──▶ source_observation_set_sha256 ─┐
pilot_candidate_snapshots  ──▶ candidate_tables_sha256        ─┤
pilot_quota_results (4 cols)──▶ quota_definitions_sha256      ─┼──▶ root_manifest_sha256 ──▶ manifest_id
reference_policy_versions + ──▶ selector_policy_sha256        ─┤              ▲
  6 explicit arguments                                         │              │
pilot_selected_entities ───▶ selected_entities_sha256 ──┐      │              │
pilot_selected_accessions ─▶ selected_accessions_sha256 ─┼──▶ selection_result_sha256 ─┘
pilot_quota_* ─────────────▶ quota_report_sha256 ───────┤   (the four also feed the root
pilot_reserve* + dispositions ▶ reserves_sha256 ────────┘    directly — a diamond, not a cycle)
```

The graph is **acyclic**: no digest is an input to itself, `manifest_id` is derived from the root and
never the reverse, and `pilot_manifest_versions` is never hashed into any digest.

### 13.4 Serialized document and verification

S6 writes the canonical JSON under `DataTree.releases / "pilot"` as
`pilot_manifest_<root_manifest_sha256>.json` — UTF-8, LF, sorted keys, relative paths only, and
byte-identical on re-serialization. **The row and the file commit together or not at all**; an
injected fault leaves no new row and no new file. `verify_pilot_manifest` re-derives every digest,
the root, `manifest_id`, and the document from persisted rows and fails closed on any difference.
**Idempotent replay reads, reconstructs, compares, and returns without writing.**

### 13.5 `pilot_projection_recovery_events` — schema ahead of its writer

The twenty-second pilot table, and the only one with **no writer, no reader, and no digest role**.
Migration `0009` created it as part of the Decision 016 §5 table family; Decision 016 rejected reusing
`census_projection_recovery_events` for pilot-manifest projection faults and required a **dedicated**
table, so that a pilot fault and a census fault never contend for the same identifier space or
detection logic. **Decision 021 §16 leaves it unwritten at Stage S6, and writing it is an explicit S6
stop condition (§21).** It is documented here because it exists in the catalog, not because anything
populates it.

| Table | Migration | PK | Key uniqueness / FKs | Material CHECKs | Lifecycle / role |
|---|---|---|---|---|---|
| `pilot_projection_recovery_events` | `0009` | `event_id` | no UNIQUE beyond the primary key; FK `manifest_id` → `pilot_manifest_versions` (`manifest_id`), `ON DELETE NO ACTION`; non-unique idx `idx_pilot_projection_recovery_manifest` (`manifest_id`,`resolution_state`) | `expected_count` / `observed_count` each NULL-or-`>= 0`; `resolution_state IN ('blocked','resolved')`; `release_blocking_before_resolution IN (0,1)`; `release_blocking_after_resolution` NULL-or-`IN (0,1)`; **`(resolution_state = 'resolved') = (resolved_at_utc IS NOT NULL)`**; `resolution_state = 'blocked' OR release_blocking_after_resolution IS NOT NULL` | **Append-only.** Twelve columns. Two migration-`0009` triggers — `pilot_projection_recovery_events_immutable_update` (`BEFORE UPDATE`) and `pilot_projection_recovery_events_immutable_delete` (`BEFORE DELETE`) — both unconditional `RAISE(ABORT, 'pilot projection recovery events are append-only')`. A recorded event is never edited and never removed |

**Identity columns.** `event_id` is the row identity and **may be a UUID**: Decision 016 §1 permits
that for operational event IDs precisely because event identity is excluded from every deterministic
hash. `manifest_id` is the only relationship the table carries.

**Owning stage.** The operational S6 boundary: the table is the deferred projection-recovery surface
governed by [Decision 021](Decisions/decision_021_m23_s6_manifest_construction.md) §16, which leaves
it unwritten. No accepted record assigns it an implementing stage.

**Accepted writer: none currently implemented. Accepted reader: none currently implemented.** No
module in `src/` references this table at all (§9.2) — neither to write it nor to read it. There is
therefore no reconstruction path over it, because there is nothing persisted to reconstruct.

**Digest or identity role: none, explicitly.** It is **not a manifest input, not a component-digest
input, not a `selection_result_sha256` input, not a `root_manifest_sha256` input, and not a
`manifest_id` input.** It appears nowhere in the §13.3 dependency map. Decision 021 §10 exclusion 5
states that `pilot_projection_recovery_events` **is never hashed into any digest**, because it is
operational and S6 writes it not at all; its `event_id`, its free-text `detail`, and its timestamps
are each independently in Decision 016 §8's excluded-from-hashing set.

**State class:** Operational-only (§9.1).

**Future-stage boundary.** **Documenting this table authorizes nothing.** It creates no writer, no
reader, no CLI surface, no publication action, and no Milestone 3 implementation. A writer for it
requires its own accepted governance record, a bounded implementation contract, and explicit owner
authorization, exactly as [Decision 024](Decisions/decision_024_m2_m3_boundary_governance.md) §8
requires of every Milestone 3 phase — none of which has begun or is authorized.

## 14. Migration-to-dictionary coverage

| Migration | Layer | Dictionary sections |
|---|---|---|
| `0001_initial` | core catalog, reference tables | 2, 3, 5, 7 |
| `0002_source_observations` | source observations | 4, 6A |
| `0003_census_catalog` | census, operating calendar | 6A, 7.1 |
| `0004_m22_r1_safety` | safety and rate state | 5, 6A |
| `0005_r2_structural_evidence` | structural observations | 6A |
| `0006_r2_resolution_and_reconciliation` | accession resolution | 1 (Decision 012) |
| `0007_r2_index_retrieval` | index retrieval | 1, 6A |
| `0008_r3_durability_and_lineage` | durability, lineage | 6B |
| `0009_m23_pilot_schema` | **21 pilot tables** | **9, 10, 11, 12, 13** |
| `0010_m23_quota_policy_reference` | quota policy row | **9** |
| `0011_m23_joint_selector_policy_reference` | joint selector policy row | **9** |
| `0012_m23_selection_entity_reasons` | **1 pilot table + 4 triggers** | **9, 12** |
| `0013_m23_manifest_lifecycle_guards` | **8 triggers** | **9, 13.2** |

**Coverage is complete for `0001`–`0013`.** Milestone 3 (phases M3.1–M3.5) has not begun and is not
authorized; when it introduces schema, this dictionary must be extended in the same pass
(Decision 024 §8).
