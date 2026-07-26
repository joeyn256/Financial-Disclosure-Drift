# SEC Ingestion Acceptance Tests

**Version:** 0.1 (Stage M2.1)
**Governing records:** Decisions 007–010, `Docs/sec_ingestion_risk_register.md`

Every specification carries `test_id`, `requirement`, `level`, `fixture_or_input`, `procedure`,
`expected_result`, `failure_severity`, `blocks_release`, `evidence_artifact`, and
`decision_reference`. Levels are `unit`, `integration`, `pilot_acceptance`, `release_acceptance`, and
`manual_review`.

Test counts are not an acceptance gate. Distinct behavioural guarantees and boundary cases are. The
`stage` column records the earliest stage in which the case can execute; cases marked M2.2+ require
the SEC client and are specified now but implemented later.

Column key for the compact tables below: **Sev** = failure severity (`blocking`, `high`, `medium`);
**BR** = blocks release; **Evidence** = artifact retained as proof; **Ref** = decision reference.

## A. SEC access and response behaviour (`unit`, stage M2.1 for policy, M2.2 for wiring)

Fixtures are synthetic. No test provokes SEC rate restrictions; all responses are simulated.

| test_id | Requirement | Fixture / input | Expected result | Sev | BR | Evidence | Ref |
|---|---|---|---|---|---|---|---|
| ACC-001 | Missing user agent blocks the request | unset variable | `SecUserAgentError` raised **before** request construction; zero sockets opened | blocking | yes | test log | D010 §4 policy, prompt §4 |
| ACC-002 | Blank user agent rejected | `"   "` | same as ACC-001 | blocking | yes | test log | prompt §4 |
| ACC-003 | Unchanged example rejected | `.env.example` value | rejected as placeholder | blocking | yes | test log | prompt §4 |
| ACC-004 | RFC-reserved domain rejected | `x@example.com` | rejected as placeholder | blocking | yes | test log | prompt §4 |
| ACC-005 | Missing organization identity rejected | `contact@your-org.org` alone | rejected | high | yes | test log | prompt §4 |
| ACC-006 | Missing contact rejected | `"Financial Disclosure Drift"` | rejected | high | yes | test log | prompt §4 |
| ACC-007 | Valid value accepted | project name plus real-form address | accepted; value never logged | blocking | yes | redacted log | D009 §2 |
| ACC-010 | Connection timeout | simulated timeout | `retry` with backoff; ≤5 transient retries; ceiling 60 s | high | yes | policy trace | prompt §4 |
| ACC-011 | Read timeout | simulated timeout | as ACC-010 | high | yes | policy trace | prompt §4 |
| ACC-012 | HTTP 408 | status 408 | `retry` | medium | no | policy trace | prompt §4 |
| ACC-013 | HTTP 429 with `Retry-After` | header `Retry-After: 30` | `retry_after` with delay 30 | blocking | yes | policy trace | prompt §4 |
| ACC-014 | HTTP 429 without `Retry-After` | status 429 | global `cooldown` ≥600 s, one controlled retry | blocking | yes | policy trace | prompt §4 |
| ACC-015 | HTTP 403 | status 403 | global `cooldown` ≥600 s; aggregate traffic halted | blocking | yes | policy trace | prompt §4 |
| ACC-016 | HTTP 500/502/503/504 | each status | `retry` with backoff | high | yes | policy trace | prompt §4 |
| ACC-017 | Historical 404 | status 404 on an archival path | `fail` recorded as absent evidence, not an error loop | medium | no | policy trace | D008 §5 |
| ACC-018 | Recent-filing 404 | status 404 on a recent path | `retry` then `fail` with review reason | medium | no | policy trace | D008 §5 |
| ACC-019 | Malformed JSON | truncated JSON body | `quarantine`; never an empty result | high | yes | quarantined fixture | D009 §6 |
| ACC-020 | HTML returned for JSON | HTML body, JSON expected | `quarantine` | high | yes | quarantined fixture | D009 §6 |
| ACC-021 | Empty body | zero-length 200 | `fail`; never a valid empty result | blocking | yes | policy trace | prompt §4 |
| ACC-022 | Interrupted stream | truncated stream | `retry`; `.part` retained then quarantined | blocking | yes | quarantined `.part` | D009 §7 |
| ACC-023 | Invalid ZIP | corrupt archive | `quarantine` with integrity reason | high | yes | quarantined fixture | D009 §6 |
| ACC-024 | Block-page signature | block-page body with 200 | `cooldown`; `SEC_BLOCK_PAGE` | blocking | yes | policy trace | prompt §4 |
| ACC-030 | Aggregate limiter | two simulated worker pools | combined rate never exceeds configured value; burst 1 | blocking | yes | limiter trace | prompt §4 |
| ACC-031 | Configured ceiling | request 12 rps | configuration rejected at `le=8` | blocking | yes | config error | prompt §4 |

## B. Identity and inventory (`unit`, stage M2.1)

| test_id | Requirement | Fixture / input | Expected result | Sev | BR | Ref |
|---|---|---|---|---|---|---|
| IDN-001 | Malformed accession rejected | bad checksum shapes | `IdentifierError` with actionable message | blocking | yes | D008 §1 |
| IDN-001a | Canonical CIK only | `"-5"`, `"+5"`, `" 5 "`, `"5.0"`, `"5e3"`, `"1_000"`, non-ASCII digits | `IdentifierError`; signs and whitespace are never stripped | blocking | yes | D007 §1 |
| IDN-001b | CIK range | `0`, `True`, `False`, `-5`, `10000000000` | rejected; zero is not a CIK and booleans are not integers | blocking | yes | D007 §1 |
| IDN-001c | CIK normalization | `1`, `0000000001`, `9999999999` | ten-digit padded representation; leading zeroes are representation only | blocking | yes | D007 §1 |
| IDN-002 | Duplicate accession rejected | same accession twice | unique-constraint violation surfaced, not silently ignored | blocking | yes | D008 §5 |
| IDN-003 | Submitter ≠ registrant | header with differing CIK | both retained; prefix never used as registrant | blocking | yes | D007 §1 |
| IDN-004 | Multiple registrants | multi-registrant header | one row per registrant; `REVIEW_MULTI_REGISTRANT` | blocking | yes | D007 §1 |
| IDN-005 | Unsupported form retained | `20-F` control | stored with `EXCLUDED_UNSUPPORTED_FORM`, not refused | high | no | D007 §3 |
| INV-001 | Original and amendment separate | 10-K plus 10-K/A | two accessions; original text and cohort unchanged | blocking | yes | D008 §2 |
| INV-002 | Unresolved amendment parent | ambiguous evidence | `unresolved_amendment` plus review reason | high | yes | D008 §2.1 |
| INV-003 | Amendment before alleged original | inverted dates | `unresolved_amendment`; no reassignment | high | yes | D008 §2.2 |
| INV-004 | `/A` is not a restatement | 10-K/A fixture | no restatement classification produced | blocking | yes | D008 §2.2 |
| INV-005 | XBRL flag ≠ suffix | disagreeing flags | both recorded; review condition | high | no | D008 §2.2 |
| INV-006 | Duplicate source observations | same value, two snapshots | recorded once per snapshot; no false change | medium | no | D008 §5 |
| INV-007 | Conflicting filing metadata | API vs header disagreement | both preserved; resolved source recorded | blocking | yes | D010 §4 |
| INV-008 | Co-authoritative header conflict | complete-submission vs SGML header | conflict record; review; neither chosen silently | blocking | yes | D010 §4.1 |
| INV-009 | No silent eligibility | unknown issuer type | `review_required` with `REVIEW_UNKNOWN_ISSUER_TYPE` | blocking | yes | D007 §6 |
| INV-010 | Exclusion completeness | every excluded row | at least one reason code present | blocking | yes | D008 §4 |
| INV-011 | Accession-specific shell state | former shell, later operating | not permanently excluded | high | yes | D007 §6 |
| INV-012 | Lineage not merged | predecessor and successor CIKs | separate issuer rows plus lineage edge | blocking | yes | D007 §5 |

## C. Temporal policy (`unit`, stage M2.1)

| test_id | Requirement | Fixture / input | Expected result | Sev | BR | Ref |
|---|---|---|---|---|---|---|
| TMP-001 | Dates agree | same-day acceptance | both cohorts equal; basis `same_day_acceptance` | blocking | yes | D010 §5 |
| TMP-002 | After-hours acceptance | accepted 20:15 ET, filed next operating day, synthetic calendar | official cohort from filing date; basis `later_official_filing_date`; precision `date`; reason `expected_after_cutoff_rollover` | blocking | yes | D010 §5, §5.1 |
| TMP-002a | Rollover needs a calendar | after-cutoff acceptance, no calendar supplied | `unexplained_date_divergence` with `OPERATING_CALENDAR_UNAVAILABLE`; blocks freezing; nothing assumed | blocking | yes | D010 §5.1 |
| TMP-002b | Non-operating weekday | synthetic calendar with a closed Monday | Monday filing is unexplained; Tuesday filing is `expected_after_cutoff_rollover` | blocking | yes | D010 §5.1 |
| TMP-002c | Acceptance on a non-operating day | Saturday acceptance, next operating day filing | **Not** rollover-eligible: `unexplained_date_divergence` with `REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`; observation preserved; reconciliation required; blocks freezing | blocking | yes | D010 §5.3 |
| TMP-002c1 | Acceptance on a closed holiday | calendar with a closed weekday, after-cutoff acceptance | same as TMP-002c; never `EXPECTED_AFTER_CUTOFF_ROLLOVER` | blocking | yes | D010 §5.3 |
| TMP-002c2 | Rollover needs all three conditions | operating-day acceptance after 17:30 ET and next-operating-day filing, versus each condition removed | only the complete case is `expected_after_cutoff_rollover` | blocking | yes | D010 §5.1, §5.2 |
| TMP-002d | No calendar-day allowance | four-day gap with no approved reason | `unexplained_date_divergence`; blocks freezing | blocking | yes | D010 §5.1 |
| TMP-002e | Correction beats rollover | after-cutoff acceptance plus later `DATE AS OF CHANGE` | `post_acceptance_date_correction`; never `expected_after_cutoff_rollover` | blocking | yes | D010 §5.1 |
| TMP-002f | Correction review scope | correction that moves the cohort versus one that does not | review required only when cohort assignment changes | blocking | yes | D010 §5.1, §8 |
| TMP-002g | Calendar provenance | synthetic versus SEC-snapshot provenance | synthetic flagged; SEC-derived calendar without `snapshot_id` is refused | high | yes | D010 §5.1 |
| TMP-002i | Frozen cutoff | acceptance at 16:15 ET under frozen policy versus an injected 16:00 cutoff | frozen policy gives `unexplained_date_divergence`; the injected cutoff gives a rollover; tests only | blocking | yes | D010 §5.2 |
| TMP-002j | Cutoff is not configurable | tracked YAML, serialized config, environment allowlist | no `cutoff` key and no `*CUTOFF*` variable exists | blocking | yes | D010 §5.2 |
| TMP-002k | Cutoff form scope | `10-K`, `10-K/A`, `10-KT`, `10-KT/A` versus `20-F`, `40-F`, `8-K`, `10-Q` | frozen cutoff returned for supported forms; `CalendarCoverageError` otherwise; an unsupported form can never claim a rollover | blocking | yes | D010 §5.2 |
| TMP-002h | Filing before acceptance | filing date earlier than acceptance date | review plus `unexplained_date_divergence`; never a rollover | blocking | yes | D010 §5.1 |
| TMP-003 | December 31 crossing | accepted 2021-12-31, filed 2022-01-03 | official `transition`, audit `development`; `cohort_boundary_crossing`; manual review | blocking | yes | D010 §8 |
| TMP-003a | Date divergence inside one cohort | accepted 2024-03-01, filed 2024-03-04 | `date_divergence` only; **not** a cohort-boundary crossing | blocking | yes | D010 §8 |
| TMP-003b | Coverage-boundary divergence | accepted 2026-12-31, filed 2027-01-04 | `coverage_boundary_divergence`; review required; blocks freezing | blocking | yes | D010 §8 |
| TMP-004 | 2024 boundary entry or exit | accepted 2023-12-29, filed 2024-01-02 | listed explicitly; explicit approval required before freezing | blocking | yes | D010 §8 |
| TMP-005 | `acceptance_date_sec` derivation | `20211231201500` | `2021-12-31` from the first eight characters; no UTC conversion | blocking | yes | D010 §4.3 |
| TMP-006 | Raw value preserved | any acceptance value | raw string retained verbatim | blocking | yes | D010 §4.3 |
| TMP-007 | Missing acceptance timestamp | header without acceptance | `NULL` audit cohort; basis `filing_date_only`; `REVIEW_MISSING_ACCEPTANCE_TIMESTAMP` | blocking | yes | D010 §5 |
| TMP-008 | Nonexistent local time | `20210314023000` (spring forward) | stops for review with `REVIEW_TIMEZONE_NONEXISTENT`; message says the time does not exist; no offset chosen | blocking | yes | D010 §4.3 |
| TMP-008a | Ambiguous local time | `20211107013000` (fall back) | stops for review with `REVIEW_TIMEZONE_AMBIGUOUS`; message names both offsets; no offset chosen | blocking | yes | D010 §4.3 |
| TMP-008b | Ordinary winter time | `20210115143000` | resolves at UTC-05:00 | blocking | yes | D010 §4.3 |
| TMP-008c | Ordinary summer time | `20210715143000` | resolves at UTC-04:00 | blocking | yes | D010 §4.3 |
| TMP-008d | Transition-adjacent times | `20210314015900` and `20210314030000` | both ordinary, at UTC-05:00 and UTC-04:00 | high | no | D010 §4.3 |
| TMP-009 | 2009 support filing | 2009 filing date | `official_filing_temporal_cohort = 'support_2009'` (never `NULL`), `support_only`, `primary_target_flag = false` | blocking | yes | D008 §3 |
| TMP-009a | Out-of-scope date persisted | 2008 or 2027 filing date | `out_of_scope`, never `NULL` and never `unresolved` | blocking | yes | D008 §3, R2.4 |
| TMP-009b | Unresolved date persisted | absent or unparseable filing date | `unresolved`, distinct from `out_of_scope` | blocking | yes | R2.4 |
| TMP-009c | Acceptance audit cohort | any resolved acceptance date | same label vocabulary, audit-only, never analysis assignment | blocking | yes | D010 |
| ACC-001 | Order-independent resolution | same observation set in both ingestion orders | identical canonical values, unresolved statuses, and resolution hash | blocking | yes | D012 §10 |
| ACC-002 | Equal-authority conflict | two equal-authority sources disagree on a material field | `unresolved`, `ACCESSION_FIELD_CONFLICT_MATERIAL`, downstream use blocked | blocking | yes | D012 §3 |
| ACC-003 | Correction supersedes | official correction on filing date | `resolved_by_correction`, prior observations preserved, cohort recomputed | blocking | yes | D012 §6 |
| ACC-004 | 2024 cohort transition | correction entering or exiting `primary_test` | `ACCESSION_2024_COHORT_TRANSITION_REQUIRES_APPROVAL`, blocked until approved | blocking | yes | D012 §6 |
| ACC-005 | Alias source authority | ticker file observes a filing field | never resolves it; alias sources carry no filing-field authority | blocking | yes | D012 §4 |
| IDX-001 | Index reconciliation states | index and submissions coverage compared | all six states distinguishable; nothing merged or deleted | blocking | yes | D008, R2.5 |
| PLAN-001 | Closed quarter required | quarter end on or before as-of date | `required_closed_quarter`; missing blocks completion | blocking | yes | R2.6 |
| PLAN-002 | Open quarter provisional | quarter containing the as-of date | `provisional_open_quarter`; optional; never finalized | blocking | yes | R2.6 |
| PLAN-003 | Future quarter excluded | quarter starting after the as-of date | `not_planned`; not missing, not a failure | blocking | yes | R2.6 |
| PLAN-004 | Deterministic plan hash | same coverage and as-of dates | identical plan hash; any window change alters it | blocking | yes | R2.6 |
| PLAN-005 | No implicit as-of date | coverage arguments partially supplied | refused; never completed from today's date | blocking | yes | R2.6 |
| PLAN-006 | Open-quarter failure isolation | open quarter not retrieved | closed-quarter coverage still complete; provisional coverage empty | blocking | yes | R2.6 |
| RES-001 | Resolver owns canonical fields | observations persisted then resolved | canonical values written only from the persisted resolution | blocking | yes | D012, R2.6 |
| RES-002 | Order independence through the catalog | same observations in both orders | identical canonical values, statuses, reason codes, and hashes | blocking | yes | D012 §10 |
| RES-003 | Restart mid-ingestion | restart between observations | resolution rebuilt from the catalog; deterministic rebuild matches | blocking | yes | D012, R2.6 |
| RES-004 | Index cannot override submissions | full-index and entity-submissions disagree | entity submissions wins; no conflict raised | blocking | yes | D012 §4 |
| RES-005 | Unresolved blocks cohort use | equal-authority filing-date conflict | canonical filing date `NULL`, cohort `unresolved`, completion blocked | blocking | yes | D012 §3 |
| IDX-002 | Missing required index instance | planned instance absent | `INDEX_REQUIRED_INSTANCE_MISSING`, completion blocked | blocking | yes | R2.5 |
| IDX-003 | No document URL construction | index file-name column parsed | accession extracted as metadata only; no URL built or followed | blocking | yes | M2.2 boundary |
| CAL-010 | Annual calendar target year | plan supplies explicit year | only that year's identified holiday rows assert; other years contextual | blocking | yes | D011, R2.2 |
| CAL-011 | Missing target year | no year supplied | nothing asserted, `REVIEW_CALENDAR_TARGET_YEAR_ABSENT`, source blocked | blocking | yes | D011, R2.2 |
| CAL-012 | Unrecognized calendar structure | page redesign | `indeterminate`, not a valid empty holiday list; source blocked | blocking | yes | D011, R2.2 |
| TMP-010 | No pre-2009 expansion | 2008 filing date | not auto-included; missing stays missing | high | yes | D008 §3 |
| TMP-011 | Amendment cohort independence | amendment in a later cohort | own cohorts; original unchanged | blocking | yes | D010 §7 |
| TMP-012 | Frozen windows unchanged | config mirror mutation | `FrozenDefinitionMismatchError` | blocking | yes | D003, D010 §1 |
| TMP-013 | Maturity gates unchanged | 2027-03-31 / 2028-03-31 | values match frozen constants | blocking | yes | D005 |
| TMP-014 | Missing future outcome | outcome absent | remains `NULL`; never neutral or zero | blocking | yes | prereg §20 |
| AVL-001 | Self-eligibility | target vs its own package | `eligible`, even when the boundary is later than acceptance | blocking | yes | D010 §6 |
| AVL-002 | Exact source after exact target | two timestamps | `ineligible` | blocking | yes | D010 §6 |
| AVL-003 | Exact source at or before target | two timestamps | `eligible` | blocking | yes | D010 §6 |
| AVL-004 | Same-date, date precision, different accessions | one `date`-precision boundary | `indeterminate` plus `REVIEW_AVAILABILITY_ORDER_INDETERMINATE` | blocking | yes | D010 §6 |
| AVL-005 | Different dates | source date earlier | `eligible`; reverse gives `ineligible` | blocking | yes | D010 §6 |
| AVL-006 | Indeterminate is not availability denial | any indeterminate pair | blocks automatic use; never recorded as unavailable; never silently eligible | blocking | yes | D010 §6 |

## D. Filesystem and raw integrity (`unit` and `pilot_acceptance`)

| test_id | Requirement | Expected result | Sev | BR | Ref |
|---|---|---|---|---|---|
| RAW-001 | Partial download | `.part` never promoted; never catalogued as complete | blocking | yes | D009 §7 |
| RAW-002 | Local checksum mismatch | quarantined and preserved; `RAW_FILE_CHECKSUM_MISMATCH` | blocking | yes | D009 §6 |
| RAW-003 | Living metadata content update | new immutable observation with neutral `SOURCE_CONTENT_UPDATED`; prior observation intact | high | no | D009 §6; M2.2 source-update rule |
| RAW-004 | Deterministic gzip round trip | decompression reproduces `content_sha256` | blocking | yes | D009 §5 |
| RAW-005 | Crash before promotion | no catalog row; `.part` retained for reconciliation | blocking | yes | D009 §7 |
| RAW-006 | Crash after promotion before commit | reconciliation adopts the valid orphan; nothing deleted | blocking | yes | D009 §7 |
| RAW-007 | Catalog row with missing file | detected and reported; not silently repaired | blocking | yes | D009 §7 |
| RAW-008 | No normalization | bytes unchanged for line endings, whitespace, encoding, HTML, SGML, JSON | blocking | yes | D009 §5 |
| RAW-009 | No deletion on parser failure | raw object retained; failure recorded | blocking | yes | D009 §6 |
| RAW-010 | Relative paths only | no absolute path persisted | blocking | yes | D009 §2 |

## E. SQLite (`unit`)

| test_id | Requirement | Expected result | Sev | BR |
|---|---|---|---|---|
| SQL-001 | Version floor | SQLite < 3.37 fails with an actionable message | blocking | yes |
| SQL-002 | Foreign keys on | violation rejected on every connection | blocking | yes |
| SQL-003 | STRICT typing | wrong-type insert rejected | blocking | yes |
| SQL-004 | Transaction rollback | failed transaction leaves no partial state | blocking | yes |
| SQL-005 | Single-writer coordination | second writer fails loudly | blocking | yes |
| SQL-006 | Integrity gates | `quick_check`, `integrity_check`, `foreign_key_check` all run; release requires ok and zero rows | blocking | yes |
| SQL-007 | Migration compatibility | migrations idempotent and versioned | blocking | yes |
| SQL-008 | Consistent backup | SQLite backup API used; naïve WAL copy rejected | blocking | yes |

## F. Idempotency, drift, release, privacy, backup, forecast

| test_id | Requirement | Level | Expected result | Sev | BR |
|---|---|---|---|---|---|
| IDM-001 | Second identical pilot run | `pilot_acceptance` | 0 duplicate accessions, 0 duplicate registrant relationships, 0 overwritten raw files, 0 duplicate raw-object identities, 0 unexplained source observations, 0 changed frozen selections | blocking | yes |
| DRF-001..006 | Added, removed, renamed field; changed type; unexpected null; malformed nested array | `unit` | unknown fields retained and logged; missing required fields raise `SEC_SCHEMA_REQUIRED_FIELD_MISSING`; no silent defaults | blocking | yes |
| DRF-007 | New historical-file reference | `unit` | recorded as drift event; processing continues only if required fields remain valid | high | no |
| PIL-001 | Deterministic selection | `unit` | identical selection across runs; exact `sha256(f"{seed}\|{cik_padded}")` tie-break | blocking | yes |
| PIL-002 | Quota satisfaction | `unit` | all §7 quotas verified and reported | blocking | yes |
| PIL-003 | Infeasible quotas | `unit` | selector stops and names binding constraints; never relaxes | blocking | yes |
| PIL-004 | Mandatory approval stop | `manual_review` | ingestion refuses without an approved frozen manifest | blocking | yes |
| REL-001 | Twice-built release | `release_acceptance` | identical normalized table-content hashes | blocking | yes |
| REL-002 | Frozen release immutability | `release_acceptance` | edit attempt refused | blocking | yes |
| REL-003 | Release gate enforcement | `release_acceptance` | freeze refused when any blocking gate fails | blocking | yes |
| REL-004 | Cohort-divergence report | `release_acceptance` | all counts and per-accession records present; unexplained divergence blocks freezing | blocking | yes |
| GIT-001..007 | Repository privacy | `integration` | no tracked raw body, SQLite file, `-wal`, `-shm`, Parquet release, or `.part`; no real contact email; no absolute home path in committed manifests; secret scan passes | blocking | yes |
| BKP-001 | Backup root validation | `integration` | commands requiring backup fail clearly when unset or invalid | blocking | yes |
| BKP-002 | Distinct volume | `manual_review` | broad ingestion prohibited until satisfied | blocking | yes |
| BKP-003 | Offline restore | `release_acceptance` | 100 percent raw-object checksum recovery, 100 percent accession recovery, 100 percent relationship recovery, identical normalized release hash, zero network requests | blocking | yes |
| FCT-001 | Three forecasts | `release_acceptance` | base, high-storage, and high-failure cases with the full percentile set | blocking | yes |
| FCT-002 | Capacity thresholds | `manual_review` | local free space ≥ 2.0 × projected peak working set; backup ≥ 1.2 × preserved corpus; otherwise stop | blocking | yes |
| SCP-001 | Research-scope containment | `unit` | no outcome, margin, industry-adjustment, feature, model, or Disclosure Drift Index code exists | blocking | yes |
| SCP-002 | CompanyFacts default off | `unit` | disabled by default; archive path absent; Frames API prohibited | blocking | yes |
| NET-001 | Offline default | `integration` | every Stage M2.1 command completes with sockets blocked in-process | blocking | yes |
