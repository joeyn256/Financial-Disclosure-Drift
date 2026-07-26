# Milestone 2 — SEC Universe, Filing Inventory, and Point-in-Time Ingestion

**Status:** Approved; Stage M2.1 in progress
**Controlling records:** `Docs/preregistration.md` (including section 25.1 Deviation D001),
Decisions 001–010, `Docs/leakage_register.md`, `Docs/research_risk_register.md`,
`Docs/sec_ingestion_risk_register.md`, `Docs/sec_ingestion_acceptance_tests.md`,
`Docs/sec_data_dictionary.md`, `Milestones/claude_milestone_02_ingestion_prompt.md`

This specification is a controlling requirement, not a retrospective summary. Where it conflicts with
an implementation convenience, this specification wins. Where an official SEC schema or observed
source behaviour conflicts with this specification, work stops, evidence is preserved, and a
methodological review is requested.

## 1. Objective

Build a reproducible, auditable, point-in-time-safe system for:

1. identifying the historical U.S. domestic Form 10-K reporting universe;
2. preserving delisted, acquired, bankrupt, failed, inactive, and successor issuers;
3. constructing an accession-level inventory of eligible original Forms 10-K and related amendments;
4. preserving immutable raw SEC source evidence;
5. supporting deterministic pilot ingestion and future incremental 2026 refreshes.

## 2. Scope boundary

**In scope:** universe construction, filing inventory, raw ingestion governance, bounded pilot
retrieval, release validation, storage forecasting, backup and restore.

**Out of scope, and absent from the code base:** 10-K section extraction, Item 1A or Item 7 parsing,
textual features, financial outcome construction, operating-margin calculation, industry adjustment,
predictive modelling, calibration, the Disclosure Drift Index, generative-AI rewrites, any 2024–2026
outcome evaluation, and unrestricted production-scale ingestion.

Milestone 2 must not construct or link outcomes.

## 3. Documentation authorization note

`CLAUDE.md` rule 14 makes `Docs/`, `Literature/`, and `Milestones/` read-only during engineering
milestones. The approved Milestone 2 assignment explicitly authorizes two exceptions:

1. creating the nine new Milestone 2 documents listed in section 4; and
2. appending the dated Deviation D001 entry to `Docs/preregistration.md` section 25.1 under that
   document's own section 25 procedure, preserving every pre-existing word.

No other research document may be modified during Milestone 2. Decisions 001–006 and the
preregistration's original protocol wording are untouched.

## 4. Documentation deliverables

| File | Role |
|---|---|
| `Milestones/milestone_02_sec_universe_and_inventory_spec.md` | This specification |
| `Milestones/claude_milestone_02_ingestion_prompt.md` | Consolidated controlling implementation prompt |
| `Docs/Decisions/decision_007_sec_universe.md` | Universe and issuer identity |
| `Docs/Decisions/decision_008_filing_inventory.md` | Inventory and amendment policy |
| `Docs/Decisions/decision_009_raw_data_governance.md` | Raw-data governance and storage |
| `Docs/Decisions/decision_010_temporal_availability_and_cohort_assignment.md` | Temporal policy and availability boundary |
| `Docs/sec_data_dictionary.md` | Field-level dictionary |
| `Docs/sec_ingestion_risk_register.md` | Ingestion risks, controls, gates, leakage mapping |
| `Docs/sec_ingestion_acceptance_tests.md` | Acceptance-test specifications |

Plus the append-only Deviation D001 entry in `Docs/preregistration.md`.

## 5. Implementation stages and gates

| Stage | Content | Network | Exit condition |
|---|---|---|---|
| M2.0 | Preflight and implementation plan | none | Plan approved |
| **M2.1** | Documentation, configuration, path policy, SQLite schema and migrations, reason codes, raw-object structures, offline default, synthetic fixtures, unit tests, CLI skeletons | **none** | Lint, format, mypy, pytest, secret scan, hygiene scan, CLI checks all pass with zero network calls |
| M2.2 | SEC client, aggregate limiter, metadata-only census | metadata only | Downloaded objects and checksums reported; no filing bodies |
| M2.3 | Deterministic pilot selection and manifest freeze | none | Manifest, quota report, checksums presented |
| M2.4 | **Human approval checkpoint** | none | Explicit approval of the exact CIK and accession list |
| M2.5 | Bounded pilot ingestion | pilot only | Approved accessions retrieved; lineage preserved |
| M2.6 | Inventory validation | none | All QA gates and the idempotent second run pass |
| M2.7 | Forecast, backup, restore, release | none | Three forecasts, offline restore, twice-built identical release |
| M2.8 | Completion review | none | Full report; no commit without instruction |

No code path may bypass Stage M2.4. Broad ingestion remains disabled throughout.

## 6. Frozen policy summary

- **Sources and prohibitions:** Decision 007 sections 2–3.
- **Identity:** CIK canonical, accession canonical for filings, submitter CIK never assumed to be the
  registrant, multiple registrants supported.
- **Temporal:** official SEC filing date authoritative, acceptance date audit-only, tri-state
  availability comparison, per Decision 010.
- **Raw data:** immutable, append-only observations, dual hashing, quarantine not replacement, per
  Decision 009.
- **Access:** `DISCLOSURE_DRIFT_SEC_USER_AGENT` required at the network boundary; 4 requests per
  second default, 8 maximum, burst 1, one shared aggregate limiter across all SEC hosts; timeouts
  10/60/180 seconds; 5 transient retries; 60-second backoff ceiling; `Retry-After` honoured;
  403 or unqualified 429 halts aggregate traffic for at least ten minutes before one controlled
  retry. An SEC outage never becomes a valid empty result.
- **CompanyFacts:** disabled by default, reconciliation and QA only, full-archive path absent, Frames
  API prohibited.

## 7. Quality gates

The seventeen gate families from the approved assignment are specified case by case in
`Docs/sec_ingestion_acceptance_tests.md`, each with `test_id`, `requirement`, `level`,
`fixture_or_input`, `procedure`, `expected_result`, `failure_severity`, `blocks_release`,
`evidence_artifact`, and `decision_reference`. Test levels are `unit`, `integration`,
`pilot_acceptance`, `release_acceptance`, and `manual_review`.

Test counts are not gates. Distinct behavioural guarantees and boundary cases are.

## 8. Capacity precondition for broad ingestion

Broad ingestion stays prohibited unless local free space is at least 2.0 times the projected peak
local working set and backup free space is at least 1.2 times the projected preserved corpus. If
capacity fails, work stops with a scope or storage recommendation.

## 9. Reporting

Progress reports state the approximate implementation percentage, completed work, current stage,
remaining work, and blockers. A stage is never reported complete while its acceptance tests are
unpassed. Quarantined and unresolved cases are always disclosed.
