# SEC and Pilot Data Dictionary

**Version:** 0.4 (through migration `0013`; Decision 051 M3.2 attempt-accounting semantics)
**Status:** current for the operational SQLite catalog as of migration
`0013_m23_manifest_lifecycle_guards.sql`.
**Governing records:** Decisions 007–012 (sections 1–8, the SEC ingestion and census schema);
Decisions 013, 014, 016, 017, 018, 019, 020, 021, 022, 023 (sections 9–14, the M2.3 pilot schema);
accepted [Decision 051](Decisions/decision_051_m3_2_post_t5_remediation_governance.md) (section 5A,
the M3.2 physical-attempt consumed-count semantics).
**Scope:** the complete operational SQLite catalog created by migrations `0001`–`0013`, and the
frozen Parquet release tables. Sections 1–8 cover the SEC ingestion and census layers
(migrations `0001`–`0008`). **Sections 9–14 cover the M2.3 pilot layer** (migrations
`0009`–`0013`), added at version 0.3 to close the coverage gap the final integrated Milestones 1–2
audit recorded ([Decision 025](Decisions/decision_025_integrated_audit_documentation_corrections.md)).
Decision 051 changes no schema and creates no migration; it assigns accepted runtime meaning to the
existing `ops_retrieval_attempts` table. Decision 055 likewise changes no schema and creates no
migration; it assigns accepted runtime meaning to the existing `ops_checkpoints` table (§5B) and
fixes the fail-closed receiptless coverage rule (§5A). **The chain remains `0001`–`0013`.**

**Migrations are the schema ground truth; accepted decisions govern methodology and semantics.**
This dictionary describes what the migrations create and what the accepted decisions say about it.
It defines nothing of its own, and where it and a migration or decision disagree, the migration or
decision controls (CLAUDE.md authority rules). Every statement in sections 9–14 was verified against
`sqlite_master` on a scratch catalog built by the accepted `0001`–`0013` chain.

**No real pilot sample or release exists.** Exactly one initial M3.2A T5 invocation occurred and
ended non-successfully after one physical retrieval attempt. Decision 051 preserves its immutable
raw object and lineage, accepts one consumed attempt of 801, leaves the interrupted operational state
untouched, and authorizes no new live operation, T6, M3.2B, Gate H, snapshot, selection, manifest, or
publication.

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
| `checkpoint_key`, `checkpoint_value` | TEXT | no | `ops_checkpoints`; supports resumable acquisition. `checkpoint_key` is the table's `TEXT PRIMARY KEY`, which is what makes a namespaced key a single-use token (§5B) |
| `event_kind`, `event_payload_json` | TEXT | no | Audit tables; payloads never contain the SEC contact value |
| `parser_run_id`, `parser_version`, `failure_reason_code` | TEXT | no | `audit_parser_runs`, `audit_parser_failures`; failures are recorded, never discarded |
| `schema_drift_kind` | TEXT | no | `unknown_field_retained`, `required_field_missing`, `type_changed`, `unexpected_null`, `malformed_nested_array`, `new_historical_file_reference` |

### 5A. M3.2 physical-attempt accounting (Decision 051)

`ops_retrieval_attempts` is the accepted future primary durable consumed-count surface. Its rows
represent **durably reserved physical-attempt slots**, not merely completed HTTP responses.

| Field | Type | Null | Accepted semantics |
|---|---|---|---|
| `retrieval_attempt_id` | TEXT | no | Opaque primary key for one reservation |
| `job_id` | TEXT | yes | Governed acquisition-run identity when available; never a receipt substitute |
| `source_url_canonical` | TEXT | no | Canonical request URL; contains no contact identity or credential |
| `logical_role` | TEXT | no | Registered logical request role |
| `attempt_number` | INTEGER | no | Positive ordinal; every retry and redirect send receives its own row |
| `attempt_state` | TEXT | no | `started`, `succeeded`, `failed`, `quarantined`, or `abandoned` |
| `started_at_utc` | TEXT | no | Written and committed before the physical transport send |
| `finished_at_utc` | TEXT | yes | Set only when terminal disposition is deterministically known |
| `action_taken` | TEXT | yes | Sanitized operational action; no headers, body, identity, credential, or private path |
| `reason_code` | TEXT | yes | Registered reason when applicable |

Counting and reconciliation rules:

1. One `started` row commits before each physical send. A failed commit prevents the send.
2. Every committed `started` row counts as consumed, including a row stranded before the transport
   call. This is the accepted one-attempt conservative reservation.
3. A stranded `started` row remains consumed; later deterministic evidence may update its state but
   never erase its consumption.
4. Receipts, committed observations, raw lineage, and response accounting reconcile with this table.
   No segment is counted twice.
5. An irreconcilable mismatch is `UNDETERMINED` and prohibits continuation and live entry.
6. Full per-route `A_reachable` is charged only when the exact count for at most one identifiable
   in-flight request is genuinely unrecorded, unattributable, or ambiguous. An unknown route bound
   or multiple possible in-flight requests is `UNDETERMINED`.
7. The approved ceiling is never increased, reset, shadowed, or reinterpreted.

The interrupted initial T5 invocation predates this runtime writer. Its real table remains empty and
is not backfilled. Decision 051 accepts **1 of 801** for that one historical invocation from the
verified immutable raw lineage and sequential call-path proof. That incident-specific evidence does
not make raw lineage the future primary attempt ledger.

**Receiptless ledger coverage is decided globally and one-to-one (Decision 055 §8).** Where a
receiptless inspection reconciles reservations against owned raw-lineage segments, coverage is a
property of the **whole** segment set, not of each manifest independently: a durable reservation may
satisfy **at most one** segment. The determination is `UNDETERMINED` on unmatched cardinality,
multiply matchable cardinality, duplicate reservation reuse, source/URL/run mismatch, a leftover
contradiction, or any inability to establish an exact bijection — including one reservation against
two owned same-URL segments, which is `UNDETERMINED` rather than a consumed count of `1`. This
corrects the per-manifest evaluation recorded as **M3-L14**; the entry is **not closed** by the
correction being implemented.

### 5B. M3.2 carry-in authority consumption (Decision 055)

A **carry-in authority** is the one-use owner artifact that lets a *clean* new M3.2A run begin from
an approved non-zero consumed baseline. It is **never a resume**. Consumption is recorded as exactly
one `ops_checkpoints` row. **No migration is involved**: the table created by migration
`0001_initial.sql` already provides everything required, and the chain remains `0001`–`0013`.

| Field | Value written |
|---|---|
| `checkpoint_key` | `m3_2_carry_in_authority:<sha256>` — the namespace prefix plus the SHA-256 of the authority's exact canonical bytes. The table's `TEXT PRIMARY KEY` is what enforces single use |
| `checkpoint_value` | Canonical JSON, a **closed document** with exactly these nine fields: `acquisition_window`, `approved_request_ceiling`, `authority_sha256`, `authorized_census_run_id`, `authorizing_decision_reference`, `consumed_request_count_carried_forward`, `historical_route_allocation`, `request_plan_sha256`, `schema_version`. The stored TEXT is **byte-for-byte the canonical serialization** of that document — not merely bytes that parse to it |
| `updated_at_utc` | The invocation's recorded UTC start instant |

Rules:

1. The row is inserted in the **same existing `BEGIN IMMEDIATE` transaction** as the new run's
   `ops_ingestion_jobs` registration. **Both commit, or neither row exists.**
2. **Replay is refused by the primary key.** An authority is consumed exactly once.
3. **Burn-before-wire:** a pre-wire failure after that commit leaves the authority consumed **even
   with zero physical attempts placed**. There is **no automatic reissue, retry, or replacement** — a
   replacement authority is a new owner act.
4. The `checkpoint_value` carries **no secret, no identity header or value, no response body, and no
   private absolute path**. Every field in it is a public hash, a governed window or plan identity,
   an integer, or an opaque run identifier.
5. The checkpoint and the chain's root receipt **mutually cross-check**, and the checkpoint is read
   as the **whole closed document** rather than for the one figure the arithmetic needs — finding a
   row under the expected key proves only that something was written there. Any of the following is
   **`UNDETERMINED`** and **cannot authorize continuation**; neither surface is ever edited to match
   the other:
   - a missing authority hash on the root, or an absent checkpoint;
   - malformed JSON, a non-object, a **missing** field, or an **extra** field;
   - **bytes that are not the canonical serialization** of the document they parse to —
     re-indented, re-ordered, or carrying a duplicate key whose discarded value no comparison would
     ever see. A lawful consumption writes canonical bytes, so anything else records no burn this
     catalog made;
   - a malformed value: an unknown schema version, an unaccepted acquisition window, an
     authorizing reference that is not a canonical `Decision NNN`, an allocation keyed by anything
     but a non-empty registered route, an allocation count that is not a **non-negative integer**
     (a Boolean and a negative count are each refused, so an allocation can never sum to a
     plausible baseline out of impossible parts), an allocation not summing to the carried
     baseline, or a baseline above the ceiling;
   - an embedded `authority_sha256` that disagrees with the deterministic key the row is filed
     under;
   - a plan, window, ceiling, or carried-forward figure that disagrees with the root receipt;
   - **any departure from the fixed Decision 055 values** (below);
   - an `authorized_census_run_id` that does not resolve to a governed acquisition run registered
     in that same window — the checkpoint and the run registration commit together, so they cannot
     lawfully disagree;
   - two carry-in checkpoints claiming the **same** authorized run, which no lawful consumption
     produces.

   The **fixed** Decision 055 values — schema `m3-carry-in-authority/1.0`, window `M3.2A`, the
   frozen plan, ceiling `801`, seed `1` on `sec_bulk_submissions`, and `Decision 055` as the
   authorizing record — are proved **here as well as** where the artifact is admitted, against the
   same constants through the same validator. Agreement between the checkpoint and the receipt is
   not authorization: a forged root and a checkpoint forged to match it agree perfectly, and
   neither surface can influence what the accepted values are.

**No carry-in artifact exists or has been consumed.** The mechanism is implemented and tested only;
a clean carry-in run additionally requires the separately authorized orphan adoption of
Decision 055 §9, and **M3-L16** remains open.

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
| `0001_initial` | core catalog, reference tables | 2, 3, 5, 5B, 7 |
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
| `0014_m33_multi_registrant_relational_correction` | **1 census relation + 4 table rebuilds + 8 triggers** | **10, 11, 16** |
| `0015_m33_verified_document_evidence` | **4 evidence relations + 1 table rebuild + 23 triggers** | **15** |

**Coverage is complete for `0001`–`0015`.**

**Note on `0014`.** The R46 multi-registrant relational correction changed tables §§10–11 already
describe — it made `census_accessions.registrant_cik_numeric` and both anchor columns nullable, added
`census_accession_registrants` and the per-accession `registrant_set_completeness` fact, and replaced
the snapshot-freeze anchor invariant. **Those §§10–11 rows were not revised when `0014` landed**, so
they still read as the pre-correction schema. The relation and the completeness fact now have their
own section — **§16** — added when accepted
[Decision 094](Decisions/decision_094_m3_3_pre_e0_executability_redesign.md) §6 supplied their
writer. [Decision 083](Decisions/decision_083_m3_3_pre_e0_multi_registrant_correction.md) §§3–7 and
the migration itself remain authoritative for the §§10–11 columns `0014` made nullable. The
migrations are ground truth for the persisted contract; this dictionary describes the schema and
never defines it.

**Neither `0014` nor `0015` is applied to the accepted operational catalog.** That catalog is at head
`0013`, and carrying it to `0015` is the separately gated Decision 094 §5 transition. Nothing in this
dictionary authorizes applying a migration.

Milestone 3 phases M3.4–M3.5 have not begun and are not authorized; when they introduce schema, this
dictionary must be extended in the same pass (Decision 024 §8).

## 15. Verified document-evidence layer (migration `0015`)

**No module writes any `document_*` table.** This is schema ahead of its writer, in the same sense
as §10: the writer is the Decision 083 **R64** document-adjudication protocol
`m3.3-document-evidence/1.0`, which is **owner accepted and EXECUTION DEFERRED**. The four relations
ship **empty**, and only synthetic disposable test fixtures populate them. **No real Decision-081
evidence is stored, and the Decision-081 private evidence artifacts are not read.**

Governing records: [Decision 082](Decisions/decision_082_m3_3_d081_owner_adjudication_and_pre_e0_contracts.md)
§11 (the schema contract) and §12 (the protocol);
[Decision 083](Decisions/decision_083_m3_3_pre_e0_multi_registrant_correction.md) §8 (**R63**, the
four dispositions) and §9 (**R64**);
[Decision 087](Decisions/decision_087_m3_3_r46_owner_acceptance_and_verified_evidence_schema.md) §§4–9.

**The artifact bytes are not here.** `document_artifacts` is a governed **catalog-metadata** relation
(**R63** item A): the Complete Submission Text stays in the private external evidence root and never
enters SQLite. **No absolute `EV_ROOT` path, private filesystem path, local user path, or scratch
path is persisted**, and there is deliberately **no locator column at all** — `artifact_sha256` is
itself the content address, so the "only if technically required" permission is never exercised.
Every text column carries a shape CHECK that a filesystem path violates.

| Table | PK | Key uniqueness / FKs | Material CHECKs | Role |
|---|---|---|---|---|
| `document_artifacts` | `artifact_sha256` (64-hex) | **UNIQUE (`accession_plain`,`source_class`)** — one artifact per accession per class, which is the artifact-substitution guard; idx on `accession_plain`. No FK to `census_accessions`: the D081 artifacts have no census row until **E0**, which is unauthorized | `accession_plain` is 18 digits; `source_class` ∈ {`complete_submission_text`} (Decision 080 **R45**, Decision 082 **R56**); `byte_length` > 0; `source_url` GLOB `https://www.sec.gov/Archives/*` with no space or backslash; `retrieval_receipt_id` charset excludes `/`, `\`, `:` and space; UTC timestamp shape | Binds one document artifact by content hash and public source identity |
| `document_review_records` | `review_id` (64-hex) | **UNIQUE (`accession_plain`,`reviewer_role`)** — one record per pass per accession; FK `artifact_sha256` → `document_artifacts`, which must additionally be **registered to this review's own accession** (Decision 088 §4); idx on (`accession_plain`,`artifact_sha256`) and on `review_epoch_id` | `reviewer_role` ∈ {`review_a`,`review_b`,`adjudication`} and must agree with `review_pass` ∈ {`A`,`B`,`ADJUDICATION`}; `protocol_version` = `m3.3-document-evidence/1.0`; `purpose_category` is Decision 014 §6's three frozen categories; `abstention_reason` is Decision 082 §12.2's four allowed abstentions and exists exactly when `abstained` = 1; an abstention asserts nothing; `original_form_asserted` ∈ {`10-K`,`10-KT`} (**X-2**/**R44**); `reviewer_model` charset excludes spaces, so **no personal name** can be recorded | One independent review pass |
| `document_review_spans` | (`review_id`,`span_ordinal`) | FK → `document_review_records`; idx on (`review_id`,`span_role`) | `span_ordinal` ≥ 1; `span_role` ∈ {`amendment_purpose`,`original_form`,`original_filing_date`,`original_accession`}; `span_text_verbatim` non-empty; `span_location` is strictly `bytes:<decimal>-<decimal>` into the frozen artifact, ASCII digits only (Decision 088 §7) — a shape no filesystem path, sign, space, or letter satisfies | Exact source-span provenance (Decision 082 §12.5) |
| `document_adjudicated_evidence` | (`accession_plain`,`evidence_kind`) | FK `artifact_sha256` → `document_artifacts`; idx on `artifact_sha256` | **`evidence_kind` ∈ {`amendment_purpose`,`explicit_original`} — this is where R63 item C is enforced**; `agreement_state` ∈ {`agreed`,`resolved`,`conflicting`,`abstained`}; `evidence_level` ∈ {`verified`,`conflicting`,`unavailable`} and `verified` requires `agreed` or `resolved`; a value exists exactly when the outcome is `agreed` or `resolved`; per-kind value shapes; `contributing_review_ids_json` is the canonical sorted array | The frozen final adjudication result |

### 15.1 Where `verified` is authorized, and where it is not

Decision 083 **R63** item C authorizes `evidence_level = 'verified'` for **amendment purpose** and
**amendment linkage / explicit-original** evidence **only**. The `evidence_kind` CHECK above is that
authorization made structural: an unauthorized dimension is refused at the kind, before an evidence
level is even considered.

Migration `0015` widens **exactly two** constraints on `pilot_candidate_accessions`, and no others:

| # | Constraint | Before | After |
|---|---|---|---|
| 1 | `amendment_purpose_evidence_level` | `provisional`, `unproven`, `review_required`, `conflicting`, `unavailable` | the same **plus `verified`** |
| 2 | `amendment_purpose_quota_eligible` | requires `amendment_purpose_evidence_level = 'provisional'` | requires it ∈ (`provisional`, `verified`) |

Every other evidence-level CHECK in the catalog — `size`, `industry`, `history`,
`primary_universe`, `filing_date`, `cohort`, `xbrl`, and both registrant relations — is left exactly
as migrations `0009` and `0014` wrote it, still excluding `verified`.

Two triggers make widening 1 non-silent: `amendment_purpose_evidence_level = 'verified'` on insert
or update requires a frozen `document_adjudicated_evidence` row for that accession, of kind
`amendment_purpose`, at level `verified`. **`verified` cannot be asserted from nowhere.**

### 15.2 Linkage: what the relationship is, versus how strongly it was verified

**No `verified_amends_original` state exists** (**R63** item B; Decision 087 §6). The relationship
stays `pilot_candidate_accessions.amendment_linkage_state = 'amends_original'`, whose vocabulary
migration `0015` does **not** touch. Verification strength lives separately, in
`document_adjudicated_evidence.evidence_level = 'verified'` with its document, review, and
adjudication provenance.

### 15.3 Reviewer identity: opaque epochs, never people

**R63** item D: `review_epoch_id` is a durable **opaque** 64-hex identifier, beside `reviewer_role`
and `reviewer_model`. **No personal name is persisted and no raw Claude session ID is required.**

Distinctness is enforced, not documented, by two mechanisms that combine:

* **UNIQUE (`accession_plain`, `reviewer_role`)** — within one accession each role appears once;
* **`document_review_records_epoch_carries_one_role`** — a given epoch carries exactly one role,
  globally.

Three roles therefore force three distinct epochs for any accession. The rule is one role per epoch,
**not** one row per epoch, so a single fresh Review-A epoch reviewing all 108 frozen artifacts — the
**R64** protocol's actual shape — stays lawful.

### 15.4 Adjudication provenance

Six triggers make an adjudicated row unwritable unless its evidence is present:

| Trigger | Refuses |
|---|---|
| `document_adjudicated_evidence_requires_bound_artifact` | an adjudication whose artifact is not the one every review of that accession bound |
| `document_adjudicated_evidence_binds_its_own_accession` | an adjudication naming an artifact **registered to another accession** (Decision 088 §4) |
| `document_adjudicated_evidence_requires_review_provenance` | a missing Review A or Review B; and a `resolved` outcome with no third adjudication record |
| `document_adjudicated_evidence_agreed_requires_agreeing_passes` | an **`agreed`** outcome where either pass abstained or asserted a different value (Decision 088 §5) |
| `document_adjudicated_evidence_review_ids_are_exact` | a contributing set that is not exactly the reviews of that accession and artifact |
| `document_adjudicated_evidence_verified_requires_spans` | `verified` where any non-abstaining review lacks a span of the matching role (Decision 082 §12.5) |

**What `agreed` means, and what it does not.** Decision 082 §12.6 defines `agreed` as A and B
agreeing exactly, so both passes must be non-abstaining and must carry the adjudicated value — the
purpose category, or the `<FORM>|<DATE>` pair. Without that rule the span-backing trigger above is
**vacuous over two abstentions**, and the D087 review demonstrated exactly that: `agreed` +
`verified` with zero spans anywhere. **Abstention is still never a negative assertion** — an
abstention remains a recorded outcome under Decision 080 **AP-1** totality, and the `abstained`,
`conflicting`, and `resolved` routes are unchanged. A genuine disagreement's lawful disposition is
`resolved`, with its third adjudication record.

The registered-accession invariant is enforced on **both** sides — here, and on
`document_review_records` by `document_review_records_bind_their_own_accession`. Each does
independent work: with the review-side guard removed, the adjudication-side guard still refuses a
cross-bound row.

The contributing set is validated by **arithmetic, not `json1`**: for `n` reviews the canonical array
is `1 + 67n` characters with `2n` quotes, and every identity must appear inside it. The repository's
declared SQLite floor is 3.37, where JSON1 is an optional compile-time extension, so the check is
written to hold on every build that floor admits.

### 15.5 Append-only and frozen at insert

Decision 082 §11.2: each relation is "append-only and immutable once frozen". Every row here is
written **already frozen**, so "immutable once frozen" and "immutable" are the same rule and **no
lifecycle transition is invented** (Decision 087 §8).

Three mechanisms enforce it, and **all three are required**:

| Mechanism | Triggers | Closes |
|---|---|---|
| Direct mutation refused | eight unconditional `BEFORE UPDATE` / `BEFORE DELETE` triggers, two per relation | `UPDATE` and `DELETE` on all four relations |
| **Conflict resolution refused** | four `BEFORE INSERT` **replacement guards**, one per relation, covering **every unique route** | `INSERT OR REPLACE`, a duplicate `INSERT`, and a silent `INSERT OR IGNORE` |
| Append-after-consumption refused | `document_review_spans_never_appended_after_adjudication` and `document_review_records_never_added_after_adjudication` | growing a review's evidentiary basis after its evidence was consumed |

**Why the middle row exists.** The D087 independent review proved that the eight `UPDATE`/`DELETE`
triggers are **necessary but not sufficient**: SQLite resolves an `INSERT OR REPLACE` conflict by
deleting the conflicting row and inserting the new one, and that implicit delete fires no
`BEFORE DELETE` trigger unless `PRAGMA recursive_triggers` is on — **which this project never sets**.
A frozen adjudicated result, a review record's role and epoch, span provenance, and bound artifact
metadata were each rewritten that way while every other protection stayed silent. Accepted migration
`0013` met the same defect on `pilot_manifest_versions` and `pilot_selection_runs`; Decision 088 §3
applies that accepted pattern here. Together the three mechanisms discharge all five Decision 087 §8
protections; **no one of them does so alone**.

### 15.6 Hash domains

Every digest goes through `src/disclosure_drift/release/hashing.py` under a **new**
evidence-specific domain; **no second hash implementation is introduced** (Decision 082 §11.3 /
Decision 067 §9 **R16**). The domains are `document_artifact`, `document_review_record`,
`document_review_span`, `document_adjudicated_evidence`, and Decision 082 §12.7's three pass-level
domains `document_review_a_table`, `document_review_b_table`, and `document_adjudication_table`.
Their executable home is `src/disclosure_drift/m3/document_evidence.py`.

**A new domain leaves every existing digest byte-unchanged**, and **no existing column tuple is
widened** (accepted Decision 084 **R67**). That is why the evidence layer disturbs no accepted
candidate, registrant, snapshot, or selection identity.

### 15.7 Open observation — non-canonical contributor encodings (OBS-1)

**This is recorded as open, not fixed.** `contributing_review_ids_json` is validated by arithmetic
rather than by `json1` (§15.4), and that arithmetic admits a **non-canonical encoding** of the same
length and quote count — for example two identities concatenated inside one pair of quotes beside an
empty string. The D087 independent review reported it, and accepted
[Decision 088](Decisions/decision_088_m3_3_d087_verified_evidence_review_corrections.md) §8 ruled it
**NON-GATING and DEFERRED** on these grounds:

* the **authoritative** membership set is `document_review_records`, never the JSON string;
* `document_evidence.contributing_review_ids_json` emits canonically sorted, deduplicated,
  hex-validated identities, so nothing in this repository produces the degenerate form;
* **no false hash-derived membership** is constructible — a 64-hex identity cannot be smuggled in;
* a clean fix without JSON1, under the declared SQLite 3.37 floor, may cost complexity
  disproportionate to the current risk.

**It must not be described as closed** until a future authorized record takes it up.

**State class:** Operational-only (§9.1).

**Future-stage boundary. Documenting this table family authorizes nothing.** Review A, Review B, the
document adjudication, **M3.3-E0**, **M3.3-E1**, **M3.3-E2**, and **M3.4** all remain
**UNAUTHORIZED**, and network, SEC, and HTTP authority is **NONE** at `REQUEST_CEILING = 0`. The
schema itself is **NOT YET OWNER ACCEPTED**: it failed its first independent review, was corrected
under Decision 088, and awaits a **fresh** independent acceptance rereview.

## 16. Canonical multi-registrant association layer (migration `0014`)

**Governing records:** accepted
[Decision 083](Decisions/decision_083_m3_3_pre_e0_multi_registrant_correction.md) **R58**/**R59**,
which created the relation, and accepted
[Decision 094](Decisions/decision_094_m3_3_pre_e0_executability_redesign.md) §§6.1–6.5, which
supplies its writer and fixes the derivation, the transaction shape, and the consumer rule.

**State class:** Operational-derived. **Written only at M3.3-E0**, by
`src/disclosure_drift/m3/offline_parse.py`'s association projection, inside the **same** E0
`CatalogWriter` invocation as the parse — not by a second catalog writer. **The table ships empty**:
the accepted catalog is at head `0013`, so neither the relation nor its completeness column exists
there yet, and E0 is not authorized.

### 16.1 `census_accession_registrants`

One row per `(accession_plain, registrant_cik_numeric)`.

| Field | Meaning |
|---|---|
| `accession_plain` | the canonical accession the membership belongs to |
| `registrant_cik_numeric` / `registrant_cik_padded` | the member's canonical CIK, in both renderings; the padded value must be `printf('%010d', …)` of the numeric one, and a mismatch is a totality failure |
| `association_class` | `substantive` for a membership this projection writes. A submitter that is not a registrant never establishes the set (Decision 019 §6.2) and is never promoted here |
| `evidence_level` | `provisional` for a valid, internally consistent accepted metadata witness. `conflicting`, `review_required`, and `unavailable` retain the existing fail-closed vocabulary and **never** establish completeness |
| `source_observation_id` / `parsed_record_id` | the **singular** provenance of the strongest accepted membership witness, chosen by Decision 012's source-authority order, then `source_observation_id`, then the nullable `parsed_record_id` with a missing identity sorting **after** every present one |
| `first_observed_at_utc` / `latest_observed_at_utc` | the minimum and maximum across **all** supporting membership observations |

Where more than one persisted observation supports a membership, **all of them remain independently
durable** in the accepted observation tables; none is deleted to make the projection singular.

### 16.2 `census_accessions.registrant_set_completeness`

Per accession, and written **last** — after the relation for that accession is total.

| Value | Meaning |
|---|---|
| `established` | every Decision 094 §6.2 condition holds: both membership sets non-empty, submissions corroborated by the full index, every member already a persisted `census_registrants` row, every required provenance reference present, exact CIK normalization and accession binding, and both blocking Decision 012 resolutions clear |
| `unestablished` | anything else. **This is a lawful, expected, fail-closed state**, not a defect — and it is never proof of a sole registrant |

The scalar `census_accessions.registrant_cik_numeric` is **derived, not authoritative**: for an
established singleton it **must** equal that sole member; for an established multi-member set it is
`NULL`; for an unestablished set it is not authoritative at all.

**A missing member is never invented.** A valid full-index-only member with no `census_registrants`
row leaves the accession `unestablished`, its unbindable count recorded, and its candidacy blocked
under existing reason `PILOT_ACCESSION_REGISTRANT_SET_UNESTABLISHED`. Relation rows for the members
E0 *does* know may lawfully exist beside an `unestablished` accession, and **no consumer may read
those rows as a complete set**.

### 16.3 The consumer rule

The candidate builder and every later Decision 093 linkage consumer read this relation **together
with** the completeness column, and nothing else: no re-derivation from
`census_accession_observations`, no scalar CIK, no anchor, no heuristic. An established joint filing's
form is attributed to **every** substantive member in entity-domain history, while accession-domain
counts still dedupe by canonical accession. An unestablished accession contributes **no** entity
history.

**Documenting this layer authorizes nothing.** Applying `0014` or `0015` to the accepted catalog,
running E0, and enabling either activation constant each remain a separate owner act.
