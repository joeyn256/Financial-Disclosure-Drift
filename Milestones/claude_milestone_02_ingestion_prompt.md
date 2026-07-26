# Milestone 2 — Consolidated Implementation Assignment

**Project:** Financial Disclosure Drift
**Repository:** `~/Projects/"Financial Disclosure Drift"` (name, capitalization, and spaces preserved)
**Status:** Approved, including the temporal-policy addendum integrated below
**Role of the implementer:** implementation engineer

This file is the single coherent controlling prompt for Milestone 2. It integrates the approved
temporal-policy addendum. It deliberately contains no duplicated or conflicting conversational
correction messages.

The implementer may inspect the repository, propose implementation details, write production Python,
write tests, update CI, and create the approved documentation. The implementer may not redefine the
research question, cohorts, universe rules, point-in-time policy, amendment policy, pilot quotas, or
raw-data governance. No commit or push occurs without an explicit instruction.

## 1. Objective

Build a reproducible, auditable, point-in-time-safe system for universe construction, filing
inventory, raw ingestion governance, bounded pilot retrieval, and release validation, as specified in
`Milestones/milestone_02_sec_universe_and_inventory_spec.md`.

Milestone 2 does not construct or link outcomes and does not implement section parsing, features,
models, calibration, the Disclosure Drift Index, rewrites, or broad ingestion.

## 2. Frozen research context

Cohort windows: development 2010-01-01 to 2021-12-31, transition 2022-01-01 to 2023-12-31, primary
untouched test 2024-01-01 to 2024-12-31, prospective 2025-01-01 to 2025-12-31, monitoring 2026-01-01
to 2026-12-31. Maturity gates 2027-03-31 and 2028-03-31. Bootstrap seed 20260725.

No 2022–2026 outcome may redefine features, model families, thresholds, the Disclosure Drift Index,
universe eligibility, filing-selection rules, or the primary outcome.

## 3. Integrated temporal-policy addendum

Authority: `Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md`, recorded as
Deviation D001 in `Docs/preregistration.md` section 25.1.

1. Frozen cohort windows are unchanged. `cohort_for()` logic is unchanged and date-source agnostic.
2. The **official SEC filing date** determines `official_filing_temporal_cohort`, which is
   authoritative. The **acceptance date** determines `accepted_temporal_cohort`, which is audit-only.
3. Field precedence for the official filing date: the **accession-header source class** — the
   complete-submission header and a separately retrieved SGML header, treated as co-authoritative
   peers — carries `FILED AS OF DATE` as the canonical value after retrieval. Submissions API
   `filingDate` and master-index `date filed` are provisional discovery and reconciliation
   observations. `DATE AS OF CHANGE`, correction status, and the resolved-value source are retained.
4. Field precedence for acceptance: the same co-authoritative accession-header class carries
   `<ACCEPTANCE-DATETIME>`; Submissions API `acceptanceDateTime` is a discovery observation.
5. When co-authoritative header sources disagree, both observations are preserved, a conflict record
   is created, and the accession requires review. Nothing is chosen silently.
6. `acceptance_date_sec` is the first eight characters of the SEC `YYYYMMDDHHMMSS` value, never a UTC
   conversion. The raw value is preserved permanently. Normalized Eastern and UTC timestamps are
   timezone-aware. Timezone ambiguity stops for review.
7. The point-in-time cutoff is the **public-availability boundary**. Comparison is tri-state:
   `eligible`, `ineligible`, `indeterminate`. The target's own filing package is eligible against its
   own approved boundary. `indeterminate` blocks automatic historical use and raises a review reason;
   it never asserts unavailability and never passes silently.
8. Amendments carry their own dates and cohorts, remain `amendment_non_target`, and never inherit or
   alter the original's cohort.
9. Cohort divergence is reported in full. Unexplained divergence blocks release freezing; boundary
   crossings require manual review; any accession entering or leaving the untouched 2024 cohort must
   be listed explicitly and approved before release freezing.

## 4. Access policy

`DISCLOSURE_DRIFT_SEC_USER_AGENT` is the only canonical SEC identity variable; there is no bare
`SEC_USER_AGENT` alias. `require_sec_user_agent()` runs at the network boundary and rejects absent,
blank, unchanged-example, and RFC-reserved-placeholder values, values with no project or organization
identity, and values with no email-like administrative contact. Offline commands work without it.
Every network command fails before request construction when it is invalid. The value is never
written to ordinary request logs and never committed; logs expose only configured or not-configured
state.

One shared aggregate limiter across all SEC hosts: 4 requests per second by default, 8 maximum, burst
1. Timeouts 10 seconds connect, 60 seconds ordinary read, 180 seconds bulk read. Five transient
retries, 60-second backoff ceiling. `Retry-After` honoured on 429. A 403 or unqualified 429 halts
aggregate SEC traffic for at least ten minutes before one controlled retry, applied globally rather
than per worker. Failures never become valid empty results.

## 5. Storage and catalog policy

Four storage roles per Decision 009: immutable raw files on the filesystem, an operational SQLite
catalog, frozen Parquet releases, and readable JSONL event logs. Two runtime roots,
`DISCLOSURE_DRIFT_DATA_ROOT` and `DISCLOSURE_DRIFT_BACKUP_ROOT`, which may be absolute machine-local
paths; the audit directory is always `{data_root}/audit/sec`. Database rows, manifests, and releases
store only paths relative to their configured root.

SQLite 3.37 or newer with `STRICT` tables where supported, `foreign_keys = ON`,
`busy_timeout = 10000`, writer-side WAL and `synchronous = FULL`, one designated logical writer,
explicit transactions, versioned migrations, and the `quick_check` / `integrity_check` /
`foreign_key_check` release gates.

The eleven-step atomic write protocol, dual hashing, deterministic gzip for text-like objects,
quarantine instead of replacement, and the no-deletion rule are specified in Decision 009.

## 6. Reference-data policy

`reference_form_types`, `reference_reason_codes`, `reference_cohort_definitions`, and
`reference_policy_versions` are seeded in Stage M2.1 from already-frozen project definitions.
`reference_sic_codes` is created in M2.1 but populated in M2.2 from an approved SEC source snapshot.
No SIC taxonomy is seeded from memory; any earlier policy-critical SIC constant carries explicit
source metadata and does not present itself as a complete taxonomy.

## 7. Pilot design

24 SEC entities: 20 operating-company candidates and 4 negative or boundary controls.

Selection seed `disclosure-drift-milestone-02-pilot-v1`, with the tie-break

```python
sha256(f"{selection_seed}|{cik_padded}".encode("utf-8"))
```

Operating-company quotas — size 7 large accelerated, 7 accelerated, 6 non-accelerated or
smaller-reporting; industry 4 technology and communications, 4 operating financial institutions,
3 industrial and materials, 3 consumer, retail and services, 3 healthcare and life sciences, 3 energy
and utilities; history 10 stable and 10 eventful, with at least 6 eventful entities currently
inactive, acquired, delisted, bankrupt, failed, or absent from current public-company lists.

Controls — one registered investment company or ETF, one asset-backed issuer, one shell or blank-check
issuer, one foreign-private-issuer annual-report filer.

Cross-cutting minimums — 8 entities with linked annual-report amendments, 3 amendment-purpose
categories, 2 entities with 10-KT or 10-KT/A, 3 fiscal-year-end changes, 4 name or ticker changes,
2 multi-registrant annual filings, 6 paired 2009 support and 2010 target cases, 12 pre-Inline-XBRL
originals, 12 Inline-XBRL originals, 6 original 2024 filings, 4 original 2025 or 2026 filings, and
6 difficult or nonstandard filing packages.

Accession limits — at most 4 base annual-report accessions per CIK, at most 96 base accessions,
24 additional stress accessions, 120 total.

Selection is deterministic and never based on familiarity or fame. If quotas are infeasible on real
data, the selector stops and names the binding constraints; it never relaxes a quota. After selection,
`pilot_entities`, `pilot_accessions`, `pilot_quota_report`, `pilot_selection_manifest`, and checksums
are presented and work **stops** for explicit approval of the exact CIK and accession list, even when
every automated quota passes.

## 8. Bounded pilot download

After approval, retrieve for each approved accession the complete submission text, filing index HTML,
filing index JSON when available, any separately available SGML header, the primary annual-report
document, filing-level XBRL components, and any object needed to verify registrant, amendment, or
issuer classification. Every document listed by the SEC accession index is inventoried. For at least
six technically difficult or high-document-count accessions, the complete package including exhibits
and images is downloaded to support a realistic tail-storage forecast. Unrestricted full-production
ingestion is not enabled.

## 9. Release architecture

SQLite is the operational source of normalized state; Parquet is the frozen portable release format
with a pinned writer, Zstandard compression, stable column and row order, UTC-normalized timestamps,
explicit Eastern filing dates, relative paths only, a release schema version, no personal contact
data, table-level hashes, a release-level content hash, a manifest, and an acceptance report.
Releases are built twice from the same SQLite state and compared on normalized table-content hashes.
Frozen releases are never edited; incremental updates create new releases and release diffs.

## 10. Command surface

```bash
python -m disclosure_drift validate-sec-config
python -m disclosure_drift sec census
python -m disclosure_drift sec select-pilot
python -m disclosure_drift sec show-pilot
python -m disclosure_drift sec ingest-pilot
python -m disclosure_drift sec validate-inventory
python -m disclosure_drift sec forecast-storage
python -m disclosure_drift sec build-release
python -m disclosure_drift sec verify-release
python -m disclosure_drift sec backup
python -m disclosure_drift sec restore-test
```

Network commands fail before requesting when the user agent is missing or invalid. Pilot ingestion
refuses to run without an approved frozen pilot manifest. Broad-ingestion commands are absent or
disabled. Release creation refuses when a release-blocking gate fails. Outcome-related commands do
not exist.

## 11. Dependency sequencing

Stage M2.1 installs and imports no HTTP library and makes no SEC request; the existing
network-import prohibition stays in force and the response-behaviour matrix is tested through a pure
offline classifier. `httpx` is introduced in M2.2, confined to a single auditable client module.
`pyarrow` is introduced in M2.7 as an optional release extra.

## 12. Prohibitions

Do not alter frozen cohorts, the research question, or the contribution; construct any outcome; access
or infer 2025–2026 outcomes; use 2024–2026 outcomes for design choices; use current ticker lists as
the universe; silently exclude failed or inactive issuers; treat the accession prefix as the
registrant CIK without verification; collapse multi-registrant filings; replace originals with
amendments; classify every amendment as a restatement; overwrite original structured facts with later
restatements; assume current CompanyFacts is point-in-time safe; use the Frames API for historical
point-in-time features; fabricate an exact public-dissemination timestamp; silently fill missing
metadata; silently discard parser failures; delete or overwrite raw SEC files; place raw SEC data in
Git; commit a real SEC contact email; use absolute personal paths in release manifests; enable broad
production ingestion; broaden the milestone into parsing, features, models, outcomes, or the
Disclosure Drift Index; or commit or push without an explicit instruction.

When a frozen rule conflicts with implementation convenience, the frozen rule wins. When official SEC
schema or observed behaviour conflicts with approved policy, stop, preserve the evidence, and request
a methodological review.

## 13. Reporting

Each progress report states the approximate Milestone 2 implementation percentage, completed work, the
current stage, remaining work, and blockers or review decisions. A stage is never reported complete
while its acceptance tests are unpassed, and quarantined or unresolved cases are always disclosed.
