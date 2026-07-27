# SEC Data Dictionary

**Version:** 0.2 (Stage M2.2-R3)
**Governing records:** Decisions 007–012
**Scope:** the operational SQLite catalog and the frozen Parquet release tables

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
2022–2026 outcome. Milestone 2 does not construct or link outcomes.
