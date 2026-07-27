# SEC Ingestion Risk Register

**Version:** 0.2 (Stage M2.2-R3)
**Governing records:** `Docs/leakage_register.md` (L01–L18),
`Docs/research_risk_register.md`, Decisions 007–012

## 1. Leakage-register mapping

| Leakage ID | Risk restated for ingestion | Control | Gate |
|---|---|---|---|
| **L01** Future facts | A source artifact that became public **after** the target accession's public-availability boundary enters the target's information set | Tri-state boundary comparison `source_public_availability_boundary <= target_public_availability_boundary`, per Decision 010 section 6. The target's own package is eligible at its own approved boundary. `indeterminate` blocks automatic historical use and raises `REVIEW_AVAILABILITY_ORDER_INDETERMINATE`. Amendments never re-date originals. Restated values stay attached to the accession that reported them | `pilot_acceptance`; unexplained violation blocks release |
| **L04** Survivorship | The universe is drawn from current tickers, exchange membership, or active issuers, silently dropping delisted and failed firms | Universe built from the bulk Submissions archive and EDGAR master indexes only; delisted, acquired, bankrupt, failed, and inactive issuers retained; current ticker files are noncanonical aliases; predecessor and successor CIKs never merged | `release_acceptance`; active-versus-inactive reconciliation by year must be produced |
| **L10** Differential failure | Retrieval or parse failures cluster by year, filer size, or document format, silently reshaping cohort composition | Append-only `ops_retrieval_attempts`, `audit_parser_failures`, and `raw_quarantine_objects`; coverage reported by year, form, filer size, and format; exclusion waterfall must balance; no silent drops | `pilot_acceptance` and `release_acceptance` |
| **L18** External corpora | A third-party SEC corpus with undocumented updates is treated as the point-in-time source of truth | SEC filing plus SEC metadata is the only point-in-time source of truth; external corpora are validation-only and labelled; discrepancies are reported, never reconciled away | `release_acceptance` |

## 2. Additional approved controls

| ID | Risk | Control | Gate |
|---|---|---|---|
| **I01** | SEC fair-access breach or IP block | One shared aggregate limiter across all SEC hosts, 4 requests per second default, 8 maximum, burst 1; per-worker pools cannot collectively exceed it; 403 or unqualified 429 halts aggregate traffic for at least ten minutes before one controlled retry | `unit` and `integration` |
| **I02** | Interrupted or partial acquisition treated as complete | Eleven-step atomic protocol; `.part` never complete; resumable checkpoints; `content_sha256` verified before commit | `unit`, `pilot_acceptance` |
| **I03** | Raw evidence mutated or lost | Immutable append-only observations; a differing later response is a new observation with `REMOTE_CONTENT_CHANGED`; damaged files quarantined and preserved; no deletion; parser failures never delete raw data | `pilot_acceptance`, `release_acceptance` |
| **I04** | Checksum recovery failure after restore | Offline restore rehashes every raw object; 100 percent recovery required, plus identical normalized release hash and zero network requests | `release_acceptance` |
| **I05** | Cohort divergence hides a boundary change | Full divergence audit per Decision 010 section 8, keeping `date_divergence`, `cohort_boundary_crossing`, and `coverage_boundary_divergence` distinct; unexplained divergence blocks freezing; boundary crossings require manual review; coverage-boundary divergence requires review and blocks freezing; entering or leaving the untouched 2024 cohort requires explicit approval | `manual_review`, `release_acceptance` |
| **I06** | Post-acceptance correction silently re-dates a filing | `DATE AS OF CHANGE`, `correction_status`, and all source observations retained; `REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY` when a correction moves a filing across a frozen boundary | `manual_review` |
| **I07** | Co-authoritative header sources disagree | Complete-submission header and separately retrieved SGML header ranked as peers; disagreement preserves both observations, creates a conflict record, and requires review | `unit`, `manual_review` |
| **I08** | Concurrent writers corrupt the catalog | One designated logical writer holds a process-lifetime non-blocking OS advisory lock; timestamps are diagnostic and never permit takeover; a second writer fails loudly; WAL plus `synchronous = FULL`; explicit transactions; SQLite-consistent backups only | `unit`, `integration` |
| **I09** | SEC schema drift silently degrades data | Unknown fields retained and logged; missing required fields raise `SEC_SCHEMA_REQUIRED_FIELD_MISSING` with no default; structural conflict stops for methodological review | `unit`, `pilot_acceptance` |
| **I10** | Outcome or scope creep | No outcome, margin, industry-adjustment, feature, model, or Disclosure Drift Index code exists; CompanyFacts disabled by default and reconciliation-only; the full-archive path is absent; Frames API prohibited | `release_acceptance`, code review |
| **I11** | Privacy or secret leakage into Git | Contact value resolved on demand, never logged or committed; repository hygiene gate rejects tracked raw bodies, SQLite files, `-wal`, `-shm`, Parquet releases, `.part` files, and absolute home paths in manifests | `integration` |
| **I12** | Capacity exhaustion mid-ingestion | Three storage forecasts with percentiles; broad ingestion prohibited unless local free space is at least 2.0 times projected peak working set and backup free space at least 1.2 times the preserved corpus | `manual_review` |
| **I13** | Pilot selection bias or irreproducibility | Frozen seed with `sha256(f"{seed}\|{cik_padded}")` tie-break; no familiarity-based choice; infeasible quotas stop rather than relax; mandatory human approval of the exact manifest | `unit`, `manual_review` |
| **I14** | Backup on the same physical volume | Backup root validated as a distinct volume before broad ingestion is permitted; backup-requiring commands validate the root | `manual_review` |
| **I15** | A date gap is excused by its size rather than by a reason | Reason-based classification only (Decision 010 section 5.1): `same_day_filing`, `expected_after_cutoff_rollover`, `post_acceptance_date_correction`, `unexplained_date_divergence`. No calendar-day allowance exists in code or policy | `unit`, `release_acceptance` |
| **I16** | Rollover assumed from a weekday guess | Rollover requires an injected EDGAR operating calendar **and** acceptance on a proven operating day at or after the frozen cutoff **and** a filing date equal to the next operating day; missing coverage yields `OPERATING_CALENDAR_UNAVAILABLE` and blocks freezing; the production calendar is loaded in M2.2 from an approved official source with snapshot provenance | `unit`, `manual_review` |
| **I18** | Cutoff drift through configuration | The 17:30 America/New_York cutoff is frozen in code for `10-K`, `10-K/A`, `10-KT`, `10-KT/A`; no YAML key and no environment variable exists, asserted by test; changes need a versioned methodological update supported by official SEC documentation | `unit` |
| **I19** | Weekend or holiday acceptance treated as ordinary after-hours behaviour | A purported acceptance on a non-operating day is preserved, classified `unexplained_date_divergence` with `REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`, blocked from automatic rollover, and held for reconciliation | `unit`, `manual_review` |
| **I17** | A correction is silently recorded as after-hours behaviour | Correction is evaluated **before** rollover; `post_acceptance_date_correction` retains preserved observations and requires review when cohort assignment changes | `unit`, `manual_review` |
| **I20** | Derived JSONL falsely appears complete after a torn or corrupted write | SQLite remains authoritative; append file-`fsync` precedes the projection flag; startup validates identity, canonical hash, count, and order; damaged projections rebuild through a durable temporary file, atomic replace, and directory `fsync`; recovery history is retained and unresolved damage blocks completion | `unit`, `integration` |
| **I21** | Applied migration history is rewritten or no longer matches packaged SQL | Startup verifies the exact contiguous version/name/checksum chain before writable operations and never repairs stored checksums silently; unknown, missing, renamed, reordered, or changed migrations fail closed | `unit` |
| **I22** | Reuse or supersession points to missing, cyclic, incompatible, escaped, or damaged evidence | Migration 0008 adds restrictive self-foreign keys; semantic validation rejects self-links, cycles, and source/request mismatches; bounded-stream reuse verification rejects unsafe or symlinked paths, proves the object owner, and copies complete immutable-object and archive-member metadata | `unit`, `integration` |
| **I23** | Partially consumed streamed responses leak temporary files or descriptors | Stream ownership is explicit and closeable; exhaustion, explicit close, context exit, and iteration failure close the spool idempotently; the HTTPX response closes before local consumption and timing uses an explicit monotonic clock | `unit` |
| **I24** | An arbitrary transport byte ceiling silently truncates or refuses a legitimate SEC bulk source | **Intentional nondecision:** no maximum transport size is imposed on approved SEC bulk metadata sources without a separately approved, source-specific policy. Containment comes from bounded-memory disk spooling, archive expansion, member-count and decompression limits, content-type, source-family, URL-containment, and parser validation, deterministic cleanup, and explicit stream closure — not from a guessed byte cap. A size ceiling invented without evidence would fail exactly the large, legitimate sources the census depends on | `unit`, `integration` |
| **I25** | "It spooled successfully" is mistaken for "it is acceptable evidence" | Spooling is transport containment only. Every integrity, storage-representation, archive, parser, reconciliation, and QA gate still applies to a large source, and a source that spools but fails any of them is failed or quarantined with its evidence preserved. Bounded-memory spooling is never permission for an unbounded in-memory read | `unit`, `integration` |

## 3. Stop conditions for Milestone 2

Work stops and a methodological review is requested when:

1. an official SEC schema or observed behaviour conflicts with approved policy;
2. co-authoritative accession-header sources disagree at a material rate;
3. timezone interpretation of acceptance values becomes ambiguous, or acceptance dates fall on non-operating days at a material rate;
4. unexplained cohort divergence appears, or an official filing date precedes its acceptance date;
5. an accession enters or leaves the untouched 2024 cohort without approval;
6. capacity thresholds fail; or
7. raw-object checksum recovery is below 100 percent after restore.
