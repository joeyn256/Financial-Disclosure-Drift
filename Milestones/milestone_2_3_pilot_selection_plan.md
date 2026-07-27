# Financial Disclosure Drift
## Milestone 2.3 — Deterministic Pilot Selection and Controlled Live-Metadata Readiness Plan

**This is the CORRECTED M2.3 plan.** It supersedes a pre-repository planning draft (not itself a
repository artifact) by applying corrections **P1–P12** from a read-only Opus 5 audit (repository
baseline `d9e09a5`; audit findings **C1–C13**, blockers **B1–B3**, corrections **P1–P12**). Every
correction below is marked inline as **[P#]**. Text with no `[P#]` marker is carried over unchanged
from the original plan. Decisions D1–D13 and D15/D18 from §15 have since been approved and recorded
as
`Docs/Decisions/decision_013_pilot_selection_mechanics.md`,
`Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md`, and
`Docs/Decisions/decision_015_pilot_use_prohibition.md`; D16 was declined; D17 is the governance
exception under which this document and the other S1/S2 documentation edits were made (see
"Documentation authorization note" below).

**Status:** Plan Mode only — **no implementation authorized by this document.**
**Accepted baseline:** `d9e09a5`
**M2.2 completion tag:** `m2.2-r3-complete`
**Implementation authorization:** Not granted
**Live SEC authorization:** Not granted
**M2.5 authorization:** Not granted
**Corrected:** 2026-07-27, during the M2.3 governance-repair exception (Decision 010 audit; see
"Documentation authorization note"). Corrections P1–P12 applied. Precisely: D1–D15 and D18 were
resolved as applicable and recorded as Decisions 013–015; D16 was declined; D17 was the scoped
documentation-authorization exception itself, not a policy decision to be "recorded" alongside the
others.

---

## Documentation authorization note

`CLAUDE.md` rule 14 makes `Docs/`, `Literature/`, and `Milestones/` read-only during engineering
milestones, following the precedent set at `Milestones/milestone_02_sec_universe_and_inventory_spec.md`
§3. The M2.3 audit's D17 recommendation, approved by the project owner on 2026-07-27, authorizes a
scoped exception, limited to exactly:

1. creating `Docs/Decisions/decision_registry.md`;
2. marking the live `decision_003_temporal_split.md` as superseded (date-source rule only) with a
   forward pointer to Decision 010;
3. extending `CLAUDE.md`'s precedence list to Decisions 001–015;
4. drafting the M2.3 pilot-policy decision records (013, 014, 015);
5. adding the pilot-use leakage prohibition to `Docs/leakage_register.md` as L19;
6. correcting this M2.3 plan per audit corrections P1–P12 (this document).

No other research document is modified under this exception. No production Python, migration,
manifest, SEC retrieval, or Git staging/commit/push/tag action occurs under it. Stages S3 onward
(schema, selector implementation, accession selector, manifest serialization, live retrieval) remain
unauthorized until a separate, explicit instruction.

**Second correction pass (2026-07-27):** the owner separately, explicitly directed portability
fixes (removing local-path references from items 4 and 6 above), cross-reference corrections within
the decision records created under items 4 and 6, freezing the SIC-to-family mapping
(`sic-family-mapping/0.2`, within Decision 014, item 4 above), and one item **outside** the original
six-item D17 list: approving and clarifying `Docs/Decisions/decision_002_primary_outcome.md`
(primary-universe boundary, `primary_universe_eligible`, XBRL concept-hierarchy freezing rule). That
edit is authorized directly by the owner's explicit, itemized instruction in this pass, not by the
original D17 enumeration — noted here per `CLAUDE.md` rule 14's requirement to explain any edit
beyond previously declared scope.

**Third correction pass (2026-07-27):** a read-only Stage S3 schema-and-artifact architecture review
was produced and accepted, and the owner directed creation of a further, **new** decision record —
`Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md` — freezing the Stage S3
candidate/selection/manifest table family, ID scheme, lifecycle rules, integrity constraints,
reserve-package signature model, and hash boundaries, plus targeted corrections to
`Docs/Decisions/decision_002_primary_outcome.md` (the pilot's primary-universe-ineligible entity
count is eight, not four), `Docs/Decisions/decision_013_pilot_selection_mechanics.md` §4 (the
multi-registrant storage table name), and this document's status. Creating Decision 016 is, like the
Decision 002 edit in the second pass, formally **outside** the original six-item D17 list (which
named Decisions 013–015, not a fourth record); it is authorized directly by the owner's explicit,
itemized instruction in this pass, per `CLAUDE.md` rule 14. **No migration, schema, code, or test
file was created or modified in this pass.** Stage S3 implementation (migration `0009`, schema DDL,
reason codes, selector code, and schema/integrity/reconstruction tests) remains unauthorized until a
separate, explicit instruction.

---

## Executive finding

M2.3 cannot yet generate a defensible real pilot manifest from the accepted M2.2 state.

The accepted M2.2 baseline is a hardened metadata-ingestion architecture with migrations, source
policies, parsers, audit lineage, durability controls, dry-run planning, and synthetic tests. It is
not a populated SEC candidate universe.

Therefore, M2.3 should be divided into three controlled parts:

1. **M2.3A — Offline selection-policy and readiness freeze**
2. **M2.3B — First authorized, metadata-only live SEC operation**
3. **M2.3C — Offline deterministic pilot selection and owner approval**

No filing body, accession page, primary document, complete submission, filing-level XBRL package, or
CompanyFacts outcome information should be retrieved in M2.3.

The governing Milestone 2 specification already freezes a 24-entity engineering pilot, including 20
operating companies, four boundary controls, detailed coverage quotas, a dedicated pilot seed,
accession caps, and a mandatory approval stop before pilot-body ingestion.

**[P11]** The originally estimated "≈15% complete" status (see §16) was optimistic. The one
substantive asset, `pilot.py`, is unwired *and* algorithmically unsound (audit findings C2/C3), and
the classifier it depends on (C7/C8) has no producer anywhere in `src/`. The first correction pass
put this at **≈8–10% complete** — essentially "constants and a seed are frozen," with no sound
selection mechanism, classifier, or real candidate data yet in place. A second correction pass
(2026-07-27) updated this to ≈22–23% complete, once S1/S2 (governance repair and decision freeze)
were substantially done. **A third correction pass (2026-07-27) updates this again to ≈28% complete,
now that the Stage S3 schema-and-artifact architecture has been reviewed and frozen (Decision 016) —
see §16 for the current breakdown.**

---

# 1. Data already available from M2.2

## 1.1 Eligible for designing and validating the selector

The following accepted M2.2 assets may be used immediately and offline:

- frozen cohort definitions and maturity gates;
- official-filing-date cohort assignment;
- acceptance-time audit fields and after-hours logic;
- frozen eligible filing forms;
- metadata-source registry and SEC URL containment policy;
- deterministic census-plan construction;
- source-observation and raw-object lineage models;
- SQLite migrations `0001` through `0008`;
- reason-code registry;
- tri-state operating-calendar logic;
- parsers for approved M2.2 metadata sources;
- synthetic SEC fixtures;
- simulated HTTP failure, retry, cooldown, quarantine, and recovery tests;
- catalog integrity, migration-provenance, and JSONL reconstruction mechanisms;
- CLI command surfaces for `select-pilot` and `show-pilot`;
- the accepted M2.2 dry-run plan and plan-hashing behavior.

These assets are eligible for:

- specifying the candidate schema;
- implementing the deterministic selector;
- testing selection against synthetic candidate pools;
- proving infeasibility behavior;
- testing manifest serialization and hashing;
- proving that prohibited URLs cannot be constructed;
- preparing the first live-metadata command.

## 1.2 Not eligible as real pilot candidates

The following are not presently available:

- a real populated historical issuer candidate table;
- a complete real accession candidate table;
- real filing-time filer-size classifications;
- real linked amendment sets;
- real multi-registrant cases;
- real 10-KT cases;
- real 2009–2010 support pairs;
- real 2024–2026 annual-report candidates;
- real negative-control classifications;
- real difficult-package classifications.

Synthetic fixtures must never be mixed into the production candidate pool.

The current `select-pilot` and `show-pilot` command names should be treated as stage-gated
interfaces, not proof that a complete selector already exists. **(Audit §2, "Premature
implementation: none found," confirms this reading is correct: the CLI names are refusal stubs,
`cli.py:464-487`, and nothing in `src/` performs pilot selection.)**

---

# 2. Additional SEC metadata required before real selection

## 2.1 Required metadata-only census

The first authorized live operation should retrieve only the already approved metadata families
needed to create a dated candidate snapshot:

- SEC bulk Submissions archive;
- **[P1]** closed-quarter EDGAR full-index company files (`sec_full_index_company`,
  `/Archives/edgar/full-index/{year}/QTR{q}/company.idx`) from 2009 through the approved cutoff.
  *Correction: the registered source is `company.idx`, not a "master index." No `master.idx` source
  is registered in this repository. (Decision 010 §4.1 also uses "Master index" wording — that is
  the same drift, noted here for cross-reference; correcting Decision 010's wording is out of scope
  for this plan and would require its own review.)*
- **[P2]** daily index observations for the open 2026 period — **flagged as new work, not already
  approved.** No `SourceSpec` for a daily-index source exists in the repository. Registering one
  requires a new source registration, a new exact-path `_UrlFamilyPolicy` entry (per audit finding
  C13 — the filing-body guard does not defend a new daily-index source by itself), a new parser and
  parser version, and a Decision 007 amendment. **Decision 013 §1 declines this work for M2.3
  (D16 declined): no daily-index source is registered, and open-2026-Q3 coverage is not retrieved.**
- the approved SEC operating-calendar evidence;
- approved SIC-reference evidence;
- approved ticker and exchange files only as noncanonical reconciliation aids;
- referenced historical submission metadata files identified inside the official bulk submissions
  data, where already authorized by the source policy.

## 2.2 Metadata that should remain prohibited

M2.3 should not retrieve:

- accession index HTML;
- accession index JSON;
- primary filing documents;
- complete submission text;
- separate SGML headers;
- filing exhibits;
- Inline XBRL documents;
- standalone XBRL instances or taxonomies;
- CompanyFacts;
- filing bodies used to classify amendment purpose;
- any financial outcome source.

## 2.3 Important observability limitation

Several frozen pilot quotas cannot be conclusively proven from M2.2 metadata alone.

**[P3]** The following table applies the four corrections from audit §3.2, measured against the
actual parser code rather than assumed behavior:

| Quota attribute | M2.2 metadata-only observability |
|---|---|
| Form, accession, CIK, filing date, report date | Generally observable |
| 10-K versus 10-K/A versus 10-KT | Observable |
| 2009–2010 filing pairs | Observable |
| Name-history changes | **[P3] Name changes: fully observable** (`formerNames` with `from`/`to` fields, `parsers/submissions.py:134,365`). **Ticker changes: not observable** — only the current `tickers` field exists; no historical ticker record is retained by any approved M2.3 source. |
| Fiscal-year/report-date changes | Usually inferable, but sometimes ambiguous |
| Multi-registrant status | **[P3] Metadata-qualified via the quarterly index.** `company.idx` emits one row per registrant per accession; grouping by File Name yields the registrant set. The Submissions JSON is per-CIK and cannot establish multi-registrant status alone (`sec_full_index_company`; `parsers/full_index.py`). |
| Filing-time accelerated-filer status | Not reliably available in basic submissions/index metadata; `category` is entity-level current and commonly blank for inactive issuers (`parsers/submissions.py:123`) |
| Definitive Inline XBRL status | **[P3] Metadata-qualified, not merely "not reliable."** `isXBRL`/`isInlineXBRL` are per-filing and already parsed; `census_accessions` (migration `0003:137-138`) already has `xbrl_flag`/`inline_xbrl_flag` columns (`parsers/submissions.py:147-148`). |
| Amendment-purpose category | Usually requires amendment filing content |
| Difficult or high-document-count package | Requires accession document inventory |
| Shell status at the accession | Often requires cover-page or filing evidence |
| Acquired, failed, bankrupt, or inactive history | May require explicit documented evidence beyond current ticker files |

**[P3]** Consequence: the frozen cross-cutting quota "4 name or ticker changes" must be satisfied by
*name* changes alone at M2.3 (see `Docs/Decisions/decision_013_pilot_selection_mechanics.md` §3);
ticker changes are retrieval-verified or unobservable, not "partly observable" as the uncorrected
plan stated.

### Recommended resolution

Freeze two evidence levels:

- **Metadata-qualified:** sufficient for deterministic provisional selection in M2.3.
- **Retrieval-verified:** conclusively verified during the bounded M2.5 pilot retrieval.

**(Now formalized as a five-state evidence taxonomy — `verified`, `provisional`,
`review_required`, `conflicting`, `unavailable` — in
`Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md` §1.)**

M2.3 should freeze:

1. the exact proposed manifest;
2. deterministic reserve candidates;
3. every provisional classification;
4. the evidence still needed in M2.5;
5. automatic replacement rules when a selected case fails retrieval verification.

This preserves the frozen quotas without authorizing prohibited document access during M2.3.

Owner approval is required because this establishes how a frozen quota may be provisionally
satisfied before document-level verification. **(Approved — Decision 014 §1.)**

---

# 3. Deterministic pilot sampling unit

The pilot has a hierarchical design.

## Primary unit: SEC entity

The quota-allocation unit is the **CIK-defined SEC entity**.

The final set contains:

- 20 operating-company entities;
- four negative or boundary-control entities.

CIK remains canonical. Name and ticker are time-bounded aliases.

## Secondary unit: accession

The retrieval and filing-observation unit is the **accession**.

For each selected CIK, the selector chooses:

- up to four base annual-report accessions;
- linked amendments or other approved stress accessions;
- support accessions where needed;
- control evidence accessions.

## Provenance unit: source observation

Duplicate retrievals, changed SEC metadata snapshots, and source reconciliation remain represented
as source observations. A new source observation does not create a second accession.

This pilot is an **engineering-coverage pilot**, not a probability sample and not an inferentially
representative sample of public companies.

---

# 4. Representation of issuers, industries, years, forms, and edge cases

## 4.1 Frozen entity quotas

The controlling specification freezes:

- 24 total SEC entities;
- 20 operating companies;
- four boundary controls.

Operating-company size quotas:

- seven large accelerated filers;
- seven accelerated filers;
- six non-accelerated or smaller-reporting companies.

Industry quotas:

- four technology and communications;
- four operating financial institutions;
- three industrial and materials;
- three consumer, retail, and services;
- three healthcare and life sciences;
- three energy and utilities.

History quotas:

- 10 stable-history entities;
- 10 eventful-history entities;
- at least six eventful entities that are inactive, acquired, delisted, bankrupt, failed, or absent
  from current public-company lists.

Controls:

- one registered investment company or ETF;
- one asset-backed issuer;
- one shell or blank-check issuer;
- one foreign-private-issuer annual-report filer.

These quotas are frozen and should not be silently relaxed.

## 4.2 Cross-cutting accession coverage

The selected accession set must collectively include at least:

- eight entities with evidence-linked annual-report amendments;
- three amendment-purpose categories;
- two entities with 10-KT or 10-KT/A filings;
- three fiscal-year-end changes;
- four name or ticker changes;
- two multi-registrant annual filings;
- six paired 2009-support and 2010-target cases;
- 12 pre-Inline-XBRL original filings;
- 12 Inline-XBRL original filings;
- six original 2024 filings;
- four original 2025 or 2026 filings;
- six difficult or nonstandard filing packages.

Limits:

- no more than four base annual-report accessions per CIK;
- no more than 96 base accessions;
- no more than 24 additional stress accessions;
- no more than 120 total pilot accessions.

## 4.3 Recommended operational definitions needing approval

### Industry

**[P4]** The original wording below is unsatisfiable as written (audit blocker B2: no approved M2.3
source carries filing-time SIC — the Submissions JSON `sic` field is entity-level current only,
`company.idx` has no SIC column, and SGML-header SIC is a prohibited filing-body object). It is
retained here for reference, with the resolution that replaces it:

> Use an accession-anchored industry assignment: (1) determine the selected entity's anchor
> accession; (2) use filing-time SIC evidence where available; (3) map the SIC to one frozen
> broad-industry family; (4) retain conflicting or missing SIC as `review_required`. Do not assign
> industry from a current company profile.

**Resolution (approved — `Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md`
§3–§4):** current entity SIC may be used *provisionally*, not as a current-profile assignment
overriding accession anchoring, subject to the evidence-level rules in Decision 014 §1, with the
SIC-to-family mapping in Decision 014 §4 frozen as `sic-family-mapping/0.2` (2026-07-27).
Implementing the mapping in code remains gated by Stage S3.

### Size

Use filing-time filer category only.

A current company size, market capitalization, or later filing status cannot be backfilled onto an
earlier accession.

Where definitive filing-time evidence is unavailable during M2.3:

- mark the category `provisional`;
- preserve the evidence basis;
- require M2.5 verification;
- include a same-stratum reserve candidate.

**(Approved and detailed — Decision 014 §2.)**

### Stable history

Recommended definition:

- at least four eligible original annual-report filings;
- no observed CIK succession event;
- no 10-KT;
- no unresolved amendment lineage;
- no material fiscal-year-end change;
- no observed inactive, acquired, bankrupt, failed, or delisted state;
- no conflicting registrant identity.

### Eventful history

An entity qualifies when at least one frozen event flag exists:

- inactive;
- acquired;
- delisted;
- bankrupt or failed;
- successor or predecessor lineage;
- reverse merger or de-SPAC review;
- fiscal-year-end change;
- 10-KT filing;
- company-name or ticker transition;
- multi-registrant annual filing;
- unusual amendment history;
- material source or identity conflict.

These definitions must be frozen before looking at the real candidate distribution. **(Approved as
stated — Decision 014 §5.)**

---

# 5. Exclusions and fail-closed conditions

A candidate must not enter an affirmative operating-company quota when any required field is
unresolved.

## Candidate-level fail-closed conditions

- malformed or noncanonical CIK;
- malformed accession;
- unsupported form;
- missing official filing date;
- unresolved registrant identity;
- unexplained conflicting form or filing date;
- missing source provenance;
- source object failing checksum verification;
- source snapshot failing parser or schema gates;
- unresolved domestic-reporting-regime classification;
- asset-backed, investment-company, shell, or blank-check status for an operating-company slot;
- ambiguous cohort assignment **[P5] — distinct from a *provisional* cohort assignment.** Every
  M2.3 candidate carries a provisional official filing date by design (audit blocker B1, since
  accession-header retrieval is prohibited); read strictly without this distinction, this fail-closed
  condition would reject every candidate. **`Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md`
  §7 resolves this: `cohort_evidence_level = provisional` is expected and selectable; only genuine
  ambiguity (indeterminate ordering, unexplained date divergence, unreconcilable conflicting
  observations) triggers this exclusion.**
- provisional future quarter not covered by the approved as-of plan.

## Selection-level fail-closed conditions

- fewer than 20 eligible operating entities;
- any boundary-control category unavailable;
- impossible size or industry quotas;
- cross-cutting quotas infeasible under the accession caps;
- duplicate CIK in entity slots;
- duplicate accession in accession slots;
- selector result changes across identical reruns;
- selector depends on SQLite row order;
- any prohibited field or outcome table is read;
- candidate-pool hash differs between selection and reconstruction;
- manifest cannot be reconstructed from SQLite and frozen source observations.

The selector must report infeasibility. It must not relax quotas automatically.

---

# 6. Duplicate, superseded, amended, transition, and ambiguous observations

## Duplicates

- Accession number is the canonical filing identifier.
- Identical accession metadata from multiple sources becomes one accession with multiple
  observations.
- Exact duplicate observations may be recognized by source identity and content hash.
- Conflicting observations remain preserved and create a review condition.
- Deduplication must not use company name or ticker.

## Superseded metadata

"Superseded" applies to source observations or candidate snapshots, not to original filings.

A later metadata snapshot may supersede an earlier observation, but it may not:

- delete the earlier observation;
- rewrite its retrieval timestamp;
- mutate its content hash;
- alter a previously frozen manifest.

## Amendments

Every 10-K/A and 10-KT/A remains a separate accession.

An amendment must never:

- replace an original filing;
- inherit the original filing timestamp;
- change the original filing cohort;
- become an implicit latest annual report;
- satisfy a linked-amendment quota unless parentage is evidence-supported.

An unresolved amendment may be selected as a stress accession, but it should not satisfy the "linked
amendment" quota.

## "Transition" terminology

Two meanings must remain separate:

- **transition cohort:** filings dated in 2022–2023;
- **transition annual report:** Form 10-KT or 10-KT/A.

The schema, CLI output, and manifest must not use an unlabeled `transition` boolean.

## Ambiguous cases

Ambiguity should result in:

- `review_required`;
- one or more machine-readable reason codes;
- preserved evidence;
- exclusion from affirmative quota satisfaction unless the quota explicitly targets ambiguity.

---

# 7. Leakage prevention

## 7.1 Hard information boundary

M2.3 may read only:

- SEC filing metadata;
- approved source and calendar evidence;
- accession and CIK identity fields;
- classification evidence explicitly approved for pilot engineering;
- source provenance and QA data.

M2.3 must not read:

- financial statement outcomes;
- operating margins;
- future deterioration labels;
- CompanyFacts values;
- filing narrative text;
- Item 1A or Item 7 content;
- textual features;
- Disclosure Drift Index values;
- model scores or predictions;
- market returns;
- analyst or media information chosen because of later company performance.

## 7.2 Temporal boundary

Cohort assignment uses the official SEC filing date. Acceptance timestamp remains audit-only.

The 17:30 America/New_York cutoff remains an availability and audit rule.

## 7.3 Holdout safeguards

The 2024, 2025, and 2026 filings may be selected only to test ingestion architecture and temporal
coverage.

They may not influence:

- feature definitions;
- thresholds;
- model families;
- model tuning;
- outcome definitions;
- DDI construction;
- rewrite policies.

**[P10]** In addition, the pilot's eventful/inactive-history stratification (§4.3, "Eventful
history") is itself current-state knowledge that post-dates every pilot filing. Using it to
stratify engineering coverage is legitimate; using the resulting pilot or its stratification to
inform any feature, threshold, vocabulary, transform, model choice, or outcome/DDI construction is
prohibited. **This is now recorded as `Docs/Decisions/decision_015_pilot_use_prohibition.md` and
`Docs/leakage_register.md` L19.**

The 2025 and 2026 outcome maturity gates and pre-linkage prediction safeguards remain unchanged.

## 7.4 Selection freeze order

The required order is:

1. approve selection rules;
2. hash code, configuration, quota definitions, and source plan;
3. authorize metadata-only retrieval;
4. freeze and hash the candidate snapshot;
5. run the selector offline;
6. generate the exact manifest and reserve list;
7. obtain owner approval;
8. keep M2.5 disabled.

## 7.5 Temporal-policy contradiction and governance repair

**[P6]** The original wording understated this contradiction by describing it as "an archived
Decision 003 version." **The contradiction was in the live, currently-in-force
`decision_003_temporal_split.md`** (Status: *Approved by project owner*), which stated at line 11:
"Assign cohorts by the SEC **acceptance date** of the original Form 10-K," with no forward pointer
to Decision 010. Separately, **no decision registry existed** to verify which record controls
(audit finding C10), and `CLAUDE.md`'s precedence list named only Decisions 001–006, omitting
007–012 (including Decision 010 itself — audit finding C11).

**Governance repair completed under the D17 exception (see "Documentation authorization note"
above):**

- `Docs/Decisions/decision_003_temporal_split.md` now carries a superseded banner naming Decision
  010 as controlling for the cohort date-source rule only.
- `Docs/Decisions/decision_registry.md` now exists and names Decision 010 as controlling for that
  rule.
- `CLAUDE.md`'s precedence list now spans Decisions 001–015.

M2.3 must still verify, at implementation time (Stage S3 onward, not part of this correction), that:

- no selector imports the archived acceptance-date rule;
- tests cover every cohort boundary using the official filing date.

---

# 8. Seed, ordering, tie-breakers, and hashing

## 8.1 Frozen seeds

Two seeds must not be conflated:

- research bootstrap seed: `20260725`;
- pilot-selection seed: `disclosure-drift-milestone-02-pilot-v1`.

The bootstrap seed must not determine the pilot.

## 8.2 Entity tie-breaker

Frozen entity tie-breaker:

```text
SHA256(
  "disclosure-drift-milestone-02-pilot-v1"
  + "|"
  + cik_padded
)
```

## 8.3 Recommended accession tie-breaker

```text
SHA256(
  selection_seed
  + "|"
  + cik_padded
  + "|"
  + accession_number_canonical
)
```

## 8.4 Recommended deterministic optimization

A simple hash sort cannot simultaneously guarantee all size, industry, history, control, and
accession-level quotas. **(Confirmed by audit findings C2/C3: the current `select_pilot` greedy pass
can raise infeasibility on a pool where a feasible solution exists, and its infeasibility signal is
unreliable.)**

Use a deterministic constrained selector with a lexicographic objective:

1. require zero unmet hard quotas;
2. minimize unresolved or provisional evidence;
3. minimize base-accession count;
4. minimize stress-accession count;
5. minimize the ordered vector of entity hashes;
6. minimize the ordered vector of accession hashes.

Implementation requirements:

- integer and categorical comparisons only;
- no floating-point objective;
- explicit candidate ordering before search;
- deterministic branch order;
- deterministic timeout or search-node limit;
- timeout produces `infeasible_or_unproven`, never a partial manifest;
- same input snapshot always produces the same selected and reserve lists.

**(Approved — `Docs/Decisions/decision_013_pilot_selection_mechanics.md` §5. Not implemented by this
document; the existing greedy selector is replaced, not extended, at Stage S4.)**

## 8.5 Manifest hashing

**[P7]** An as-of/candidate-snapshot hash contract already has a working precedent in this
repository — `IndexPlan`'s plan hash and `CoverageWindow.as_record()` (`index_plan.py:117-125`),
which consults no clock. The eventual implementation reuses this precedent and
`release/hashing.py` rather than inventing a parallel scheme.

Use canonical JSON with:

- UTF-8 encoding;
- LF line endings;
- sorted object keys;
- arrays already placed in deterministic order;
- no nonfinite numbers;
- no floating-point fields where avoidable;
- canonical accession and CIK formatting;
- UTC timestamps formatted with `Z`;
- relative paths only.

Recommended hash layers:

1. source-observation hashes;
2. candidate-table hashes;
3. quota-definition hash;
4. selector-policy hash;
5. entity-table hash;
6. accession-table hash;
7. reserve-table hash;
8. quota-report hash;
9. root manifest hash.

A non-deterministic `generated_at` timestamp should either be excluded from the content hash or
separated into an audit envelope. **(Approved — Decision 013 §7.)**

---

# 9. Defensible pilot sample size

The frozen sample of 24 SEC entities is defensible for an engineering pilot because it deliberately
covers:

- three filer-size groups;
- six industry families;
- stable and eventful histories;
- four structurally excluded control categories;
- historical and current filing formats;
- amendments;
- transition reports;
- identity and lineage complications;
- 2009 support filings;
- pre-Inline and Inline periods.

It is not defensible as:

- a statistical prevalence estimate;
- a representative random sample;
- a powered test of the research hypothesis;
- evidence of general model performance.

The accession count should not be fixed in advance beyond the frozen limits. The selector should
choose the smallest accession set that satisfies the quotas, subject to:

- no more than 96 base accessions;
- no more than 24 stress accessions;
- no more than 120 total.

If the real candidate universe cannot satisfy the frozen design, M2.3 fails closed and reports the
binding constraints.

---

# 10. Required pilot-manifest contents

## Manifest identity

- manifest schema version;
- manifest version;
- status: proposed, owner-approved, rejected, or superseded;
- selection seed;
- selection-policy version;
- quota-policy version;
- selector code commit;
- Python version;
- dependency-lock hash;
- migration versions and checksums;
- active decision-record hashes;
- configuration hash;
- as-of date and time zone;
- source-plan hash;
- candidate-pool hash.

## Source provenance

For every source snapshot:

- source ID;
- source URL identity or approved source key;
- source observation ID;
- retrieval attempt ID;
- retrieved-at UTC;
- HTTP validator metadata;
- transport hash;
- decoded-content hash;
- stored-object hash;
- relative storage path;
- parser version;
- parser status;
- schema fingerprint;
- supersession lineage.

## Entity records

- padded and numeric CIK;
- entity role;
- operating or control classification;
- industry family and evidence basis;
- filer-size category and evidence basis;
- history category;
- event flags;
- current-status evidence;
- alias evidence;
- provisional flags;
- review reasons;
- deterministic entity hash;
- reserve rank.

## Accession records

- canonical accession number;
- CIK and registrant CIK relationships;
- form;
- original or amendment role;
- official filing date;
- acceptance timestamps;
- report date;
- fiscal year end;
- official cohort;
- acceptance audit cohort;
- after-hours state;
- amendment parent and evidence state;
- base, stress, support, or control role;
- cross-cutting quotas satisfied;
- provisional-verification requirements;
- deterministic accession hash.

## Quota report

For every quota:

- required value;
- achieved value;
- selected members;
- evidence level;
- provisional count;
- reserve coverage;
- pass, fail, or unproven;
- reason for failure.

## Reconstruction fields

- canonical SQL/query or selector-input version;
- candidate-table row counts;
- selected-table row counts;
- exclusion counts by reason;
- unresolved counts;
- input and output hashes;
- command invocation with no personal path or SEC identity;
- confirmation that no prohibited data source was read.

---

# 11. Acceptance gates before the first live metadata request

## Gate A — Repository baseline

Manual Mac validation must confirm:

```text
branch = main
HEAD = d9e09a5
tag m2.2-r3-complete resolves correctly
main and origin/main are synchronized
working tree is clean
nothing is staged
```

**Status: passed** (audit §0, performed 2026-07-27 against `d9e09a5`).

## Gate B — Read-only implementation audit

Inspect the actual repository at `d9e09a5` for:

- `select-pilot` and `show-pilot` behavior;
- stage gates;
- migrations and existing pilot tables;
- candidate-query implementations;
- quota constants;
- pilot-seed usage;
- accidental accession-document URLs;
- outcome-related imports;
- stale acceptance-date cohort logic;
- premature or incomplete pilot code.

No edits occur during this audit.

**Status: passed** (audit §1–§3; findings C1–C13, blockers B1–B3).

## Gate C — Decision freeze

All owner decisions listed in Section 15 must be approved and recorded before selector
implementation or live retrieval.

**Status: passed (2026-07-27).** Precisely: D1–D15 and D18 were resolved as applicable and recorded
as Decisions 013–015; D16 was declined; D17 was the scoped documentation-authorization exception
itself, not a policy decision recorded alongside the others. Gate C is now fully satisfied for the
documentation-only decisions, including the two conditions that had been outstanding: the
SIC-to-family mapping (Decision 014 §4) is frozen as `sic-family-mapping/0.2`, and the Decision 002
primary-universe-boundary clarification is recorded. **Stage S3 (schema) and later remain
separately gated and unauthorized** — passing Gate C authorizes nothing beyond the documentation
work already done.

## Gate D — Offline selector acceptance

Synthetic tests must prove:

- exact feasible solution;
- deterministic solution across repeated runs;
- deterministic solution across insertion orders;
- deterministic solution across fresh SQLite databases;
- correct tie behavior;
- infeasible quota reporting;
- accession-cap enforcement;
- amendment separation;
- ambiguity exclusion;
- reserve ordering;
- canonical manifest hashing;
- zero network calls.

**Status: not started. Unauthorized by this document (Stage S4).**

## Gate E — Full quality suite

At minimum:

- accepted M2.2 test suite remains green;
- new M2.3 unit and integration tests pass;
- Ruff lint passes;
- Ruff formatting passes;
- mypy passes;
- secret scan passes;
- repository hygiene passes;
- migration provenance passes;
- quick, integrity, and foreign-key checks pass;
- fresh migrations are idempotent.

**Status: not applicable yet — no M2.3 code exists.**

## Gate F — Network containment

Before the live command:

- SEC identity is configured locally and never echoed;
- URL allowlist contains metadata sources only;
- accession archive paths are explicitly denied;
- filing-document suffixes and routes are denied;
- CompanyFacts remains disabled;
- network defaults to disabled;
- the command requires an explicit live flag or stage authorization;
- request budget is printed before execution;
- a dry-run makes zero requests;
- two dry-runs produce identical stable plan output and plan hash.

**Status: not started (Stage S7).**

## Gate G — As-of freeze

**[P8]** The as-of mechanism **already exists**: `CoverageWindow(coverage_start, coverage_end,
as_of_date, include_open_quarter, policy_version)` plus the CLI `--as-of` flag (`cli.py:123-147`) and
the `required_closed_quarter` / `provisional_open_quarter` / `not_planned` taxonomy
(`Docs/sec_census_plan.md:36-38`). This gate reduces to *approving a concrete date and recording it*,
not designing a new mechanism.

The owner must approve a concrete as-of cutoff.

The cutoff must not be implicit "today." It should identify:

- last included SEC filing date;
- last included acceptance time where applicable;
- closed-quarter coverage;
- treatment of the current 2026 quarter;
- required daily-index dates;
- calendar evidence version.

**Status: approved — `Docs/Decisions/decision_013_pilot_selection_mechanics.md` §1: as-of
2026-06-30, coverage through closed 2026 Q2, `include_open_quarter = false`, no open-Q3 daily-index
retrieval (D16 declined).**

## Gate H — Pre-run recovery state

Before the first request:

- use an isolated M2.3 data root;
- make a consistent SQLite backup of any accepted prior state;
- record available storage;
- confirm quarantine and staging paths;
- confirm the single-writer lock;
- verify no stale `.part` files or unresolved recovery events;
- save the approved census-plan hash.

**Status: not started (Stage S8).**

Only after Gates A–H pass may the owner run the first metadata-only command.

---

# 12. Rollback, quarantine, retry, rate-limit, and audit requirements

## Rate limiting

Retain the frozen project policy:

- shared aggregate limiter;
- four requests per second default;
- burst one;
- configurable maximum eight;
- no independent worker-pool budgets.

## Retry

Retain:

- maximum five transient retries;
- exponential or policy-defined backoff;
- 60-second backoff ceiling;
- `Retry-After` honored for 429;
- aggregate traffic halt for 403 or unqualified 429;
- minimum 10-minute cooldown;
- one controlled aggregate retry, not one retry per worker.

## Quarantine

Quarantine and preserve:

- malformed JSON;
- HTML returned for a JSON source;
- SEC block pages;
- empty required responses;
- invalid ZIP archives;
- interrupted streams;
- checksum failures;
- source-schema failures;
- partial files;
- objects with unexplained remote-content changes;
- files whose catalog lineage cannot be verified.

Quarantined evidence cannot enter the candidate pool.

## Rollback

Rollback must not mean deleting evidence.

On failure:

1. stop new requests;
2. mark the ingestion job failed;
3. preserve retrieval attempts;
4. preserve committed immutable raw objects;
5. quarantine partial or unverifiable objects;
6. roll back uncommitted SQLite transactions;
7. reconstruct JSONL projections from authoritative SQLite;
8. rerun integrity and foreign-key checks;
9. require an explicit resume or new-run decision.

A differing remote response becomes a new observation. It must never overwrite an earlier raw
object.

## Audit

The live run must record:

- approved plan hash;
- logical requests;
- actual HTTP attempts;
- retries and cooldowns;
- status outcomes;
- response hashes;
- parser versions;
- source QA;
- candidate row counts;
- excluded and unresolved counts;
- recovery events;
- zero prohibited URL attempts;
- zero filing-body downloads;
- zero outcome-data access.

---

# 13. Actions prohibited during M2.3

The following remain prohibited:

- filing-body retrieval;
- accession-index retrieval;
- primary-document retrieval;
- complete-submission retrieval;
- SGML-body retrieval;
- filing-level XBRL retrieval;
- CompanyFacts retrieval;
- section extraction;
- Item 1A or Item 7 parsing;
- textual feature construction;
- operating-margin construction;
- outcome linkage;
- industry-adjusted outcome calculations;
- model training or evaluation;
- DDI construction;
- generative-AI rewrites;
- 2024 outcome access;
- 2025 or 2026 outcome access;
- unrestricted ingestion;
- selecting famous or familiar issuers manually;
- using current ticker membership as the universe;
- silent quota relaxation;
- silent manual substitution;
- treating amendments as replacements;
- treating unresolved evidence as affirmative eligibility;
- creating or approving an M2.5 retrieval command;
- staging, committing, pushing, or tagging without explicit owner authorization.

**[P12]** Also prohibited: adding any new reason code, source registration, or migration without a
recorded decision reference. `reasons.py` and `source_registry.py` already enforce a
`decision_reference` field on their entries; this plan names that existing enforcement explicitly
rather than leaving it implicit.

---

# 14. Formal M2.3 completion

M2.3 is complete only when all of the following are true:

1. The actual `d9e09a5` repository has been inspected in read-only mode.
2. Every M2.3 policy decision has been approved and recorded.
3. Pilot candidate and manifest schemas are versioned.
4. The deterministic selector is implemented.
5. Feasibility and infeasibility behavior are tested.
6. The first authorized live operation retrieved approved SEC metadata only.
7. All retrieved metadata has immutable raw lineage and passing QA.
8. A dated candidate snapshot has been frozen and hashed.
9. The selector produces exactly 24 entities:
   - 20 operating entities;
   - four boundary controls.
10. The bounded accession set respects all caps.
11. Every quota is marked passed, failed, or provisionally passed with explicit verification
    requirements.
12. A deterministic reserve list exists.
13. Two clean rebuilds from the same candidate snapshot produce identical:
    - entity selections;
    - accession selections;
    - reserve ordering;
    - quota results;
    - root manifest hash.
14. The full test, static-analysis, security, and hygiene suite passes.
15. Zero prohibited SEC objects were requested.
16. Zero outcomes, features, models, or filing text were accessed.
17. The owner reviews the exact CIK and accession list.
18. The owner explicitly approves the manifest hash.
19. M2.5 remains disabled after approval.
20. Any commit, push, or completion tag occurs only after a separate explicit instruction.

**Milestone 2 as a whole is not complete at M2.3 completion.**

**Status as of this correction (2026-07-27): item 1 (audit) and item 2 for the documentation-only
decisions are satisfied — precisely, D1–D15 and D18 resolved as applicable and recorded as
Decisions 013–015, D16 declined, D17 the scoped authorization itself. Items 3–19 are not started.**

---

# 15. Decisions requiring owner approval

The following decisions remain unresolved or insufficiently operationalized in the original plan.
**All decisions below have since been approved and recorded** as
`Docs/Decisions/decision_013_pilot_selection_mechanics.md` (D1, D2, D8, D9, D10, D11, D12, D13),
`Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md` (D3, D4, D5/D14, D6, D7,
D15), and `Docs/Decisions/decision_015_pilot_use_prohibition.md` (D18). D16 was declined. D17 is the
governance exception under which this correction was made. The original plan text is preserved below
for traceability; see the linked decision records for the controlling, approved policy.

## D1 — M2.3 as-of cutoff

Approve the exact historical and current metadata cutoff, including treatment of the open 2026
quarter.

**Recommendation:** use an explicit past SEC operating date and freeze it in the source plan; never
use a dynamic current date.

**[P8] Amended scope:** the as-of mechanism already exists (`CoverageWindow`, CLI `--as-of`); this
reduces to picking a date. **Approved: 2026-06-30, closed Q2 2026, `include_open_quarter = false`,
no open-Q3 daily-index retrieval; D16 (daily-index registration) declined for M2.3. See Decision 013
§1.**

## D2 — Candidate-storage boundary

Decide whether metadata-only accession candidates populate `inventory_accessions` before body
retrieval or live in separate candidate tables.

**Recommendation:** use separate tables or immutable candidate-snapshot tables, such as:

- `pilot_candidate_snapshots`;
- `pilot_candidate_entities`;
- `pilot_candidate_accessions`;
- `pilot_selection_runs`;
- `pilot_selected_entities`;
- `pilot_selected_accessions`;
- `pilot_reserves`;
- `pilot_quota_results`;
- `pilot_manifest_versions`.

This avoids treating a candidate as a fully inventoried or retrieved filing.

**[P9] Amended scope:** the candidate/retrieved split already exists structurally
(`census_accessions` vs. `inventory_accessions`); the real question is whether the selector reads
mutable `census_accessions` directly or a frozen immutable snapshot derived from it. **Approved: the
latter — an immutable hashed snapshot; `inventory_accessions` is not written before M2.5. See
Decision 013 §2.**

## D3 — Metadata-qualified versus retrieval-verified quotas

Approve provisional quota satisfaction during M2.3.

**Recommendation:** allow provisional metadata qualification only when paired with deterministic
reserves and mandatory M2.5 verification.

**Approved — formalized as the five-state evidence taxonomy in Decision 014 §1.**

## D4 — Filing-time size taxonomy

Freeze:

- evidence precedence;
- treatment of smaller-reporting status overlapping non-accelerated status;
- anchor accession;
- handling of missing or conflicting filer category.

**Approved — Decision 014 §2.**

## D5 — Industry mapping

Freeze:

- SIC-to-family mapping;
- accession used for industry;
- conflict handling;
- treatment of changing SICs.

**Approved — Decision 014 §3–§4. The SIC-to-family mapping (§4) was approved as a review-pending
draft (`sic-family-mapping/0.1-draft`) and has since been frozen, with the owner's corrections
applied, as `sic-family-mapping/0.2` (2026-07-27). Implementing the mapping in code remains gated by
Stage S3, which is separately unauthorized.**

## D6 — Stable versus eventful history

Approve exact machine-readable definitions and required evidence.

**Approved as originally proposed — Decision 014 §5.**

## D7 — Amendment-purpose taxonomy

Define the three or more purpose categories.

**Recommendation:** defer definitive purpose verification to M2.5 and use provisional categories
only when available from metadata-safe evidence.

**Approved — Decision 014 §6.**

## D8 — Cross-cutting quota unit

Clarify whether:

- six 2009–2010 pairs must involve six distinct entities;
- six 2024 originals must involve six distinct entities;
- four 2025/2026 originals must involve four distinct entities;
- pre-Inline and Inline counts are accession counts or distinct-entity counts.

**Recommendation:** treat wording that says "original filings" as accession counts, but require six
distinct entities for the six support pairs.

**Approved, extended to the name/ticker-change quota given ticker history is unobservable at M2.3 —
Decision 013 §3.**

## D9 — Multi-registrant quota accounting

Decide how one accession with several registrants counts toward the 24-entity sample.

**Recommendation:** one selected anchor entity occupies one entity slot; all registrant CIKs are
preserved, and the accession may satisfy the multi-registrant quota once.

**Approved as recommended — Decision 013 §4.**

## D10 — Deterministic optimization objective

Approve the lexicographic constrained-search objective and infeasibility behavior.

**Approved. Approving this is also approving that `select_pilot`'s current greedy algorithm is
replaced, not extended (audit finding C2) — Decision 013 §5.**

## D11 — Reserve and substitution policy

Approve whether any manual substitution is permitted.

**Recommendation:** allow substitution only when a selected accession fails objective verification
or safe retrieval. Replacement must use the next deterministic same-stratum reserve. No discretionary
company choice.

**Approved as recommended — Decision 013 §6.**

## D12 — Manifest serialization and hash contract

Approve canonical JSON rules, hash layers, and treatment of non-deterministic audit timestamps.

**Approved, with the existing `IndexPlan`/`CoverageWindow.as_record()` hash precedent identified for
reuse — Decision 013 §7.**

## D13 — M2.3 approval semantics

Decide whether M2.3 completion requires:

- generation of the proposed manifest only; or
- owner approval of the exact manifest hash.

**Recommendation:** require owner approval of the exact hash. That makes the mandatory stop
auditable.

**Approved as recommended — Decision 013 §8.**

## D14 — Industry assignment when filing-time SIC is unavailable

**(Audit-identified; folded into D5 above.)** See Decision 014 §3–§4.

## D15 — Provisional cohort assignment under Decision 010

**(Audit-identified.)** Rule that a precedence-2-only official filing date yields
`cohort_evidence_level = provisional`, distinct from "ambiguous cohort assignment" in §5.

**Approved, with mandatory M2.5 header verification and an automatic-replacement trigger — Decision
014 §7.**

## D16 — Register a daily-index source for open-2026 coverage

**(Audit-identified.)** **Declined for M2.3.** See Decision 013 §1. The 2025/2026 originals quota is
satisfied from closed quarters only, and the as-of date (2026-06-30) is set accordingly.

## D17 — Governance repair authorization

**(Audit-identified.)** S1 edits `Docs/` and `CLAUDE.md`, which `CLAUDE.md` rule 14 makes read-only
during engineering milestones.

**Approved as a scoped exception — see "Documentation authorization note" above. This is the
authorization under which this corrected plan and the accompanying decision records were written.**

## D18 — Pilot-use prohibition

**(Audit-identified.)** State that the pilot is engineering-coverage only: no feature, threshold,
vocabulary, transform, or model choice may be fit on or informed by pilot membership or its
eventful/inactive stratification.

**Approved — recorded as Decision 015 and `Docs/leakage_register.md` L19.**

---

# 16. Staged implementation plan and percentage allocation

| Stage | Scope | M2.3 share |
|---|---|---:|
| M2.3A-1 | Read-only repository and specification audit | 8% |
| M2.3A-2 | Resolve and freeze owner decisions | 15% |
| M2.3A-3 | Candidate snapshot schema and provenance design | 15% |
| M2.3A-4 | Deterministic entity selector | 16% |
| M2.3A-5 | Accession selector, stress cases, and reserves | 12% |
| M2.3A-6 | Manifest serialization, hashing, and CLI output | 10% |
| M2.3B | Live-metadata readiness and bounded census operation | 10% |
| M2.3C-1 | Automated tests, CI, leakage and security gates | 9% |
| M2.3C-2 | Manual Mac acceptance and owner approval stop | 5% |
| **Total** | | **100%** |

### Current evidence-based M2.3 status

**[P11]** The original estimate of "approximately 15% complete" was optimistic; the first correction
pass (2026-07-27) put it at **approximately 8–10% complete**. A second correction pass (2026-07-27)
updated the estimate to **approximately 22–23% complete**, once S1 and S2 were substantially
complete. **This third correction pass (2026-07-27) updates the estimate again:**

**Approximately 28% complete** — S0 (read-only audit, M2.3A-1, 8%), S1/S2 (governance repair and
decision freeze, M2.3A-2, 15%), and the Stage S3 schema-and-artifact architecture review and freeze
(Decision 016 — the design portion of M2.3A-3's 15% share, credited here at ≈5%) are now
substantially done; **the remaining ≈72% is unstarted**, covering the rest of M2.3A-3 (reason
codes, migration `0009` itself, and schema/integrity/reconstruction tests) through M2.3C-2:

- high-level pilot size and quotas are frozen;
- the pilot seed and entity tie-breaker are frozen;
- the CLI command surfaces exist (as refusal stubs, not a working selector);
- M2.2 provides a strong durability and provenance foundation;
- D1–D15 and D18 are resolved as applicable and recorded as Decisions 013–015; D16 is declined; D17
  was the scoped documentation-authorization exception itself;
- the SIC-to-industry-family mapping is frozen (Decision 014 §4, `sic-family-mapping/0.2`);
- Decision 002's primary-universe-boundary clarification is recorded, and corrected to name eight
  primary-universe-ineligible pilot entities (four boundary controls plus four
  operating-financial-institutions quota entities), not four;
- portability corrections (removing local-path references) and cross-reference corrections
  (Decision 013/014 internal citations, quota-figure typo, the Decision 013 §4 registrant-storage
  table name) are applied;
- the Stage S3 schema and artifact architecture is reviewed and frozen (Decision 016): the
  candidate/selection/manifest table family, the content-derived ID scheme, snapshot/selection/
  manifest lifecycle rules, composite-key and quota-operator integrity constraints, the
  reserve-package signature model, and the hash-boundary rules (including the source-content hash
  definition and the dedicated pilot projection-recovery table).

Still incomplete or unverified:

- new reason codes for pilot classifications and states (Stage S3, unauthorized);
- migration `0009` and the S3 schema itself (Stage S3, unauthorized);
- schema, integrity, and manifest-reconstruction tests (Stage S3, unauthorized);
- deterministic constrained-search selector implementation (Stage S4, unauthorized);
- accession tie-breaker implementation (Stage S5, unauthorized);
- reserve-package policy implementation (Stage S5, unauthorized);
- manifest hash contract implementation (Stage S6, unauthorized);
- real candidate metadata (Stage S8, unauthorized);
- first live metadata run (Stage S8, unauthorized);
- candidate snapshot (Stage S9, unauthorized);
- exact pilot manifest (Stage S9, unauthorized);
- owner approval of the manifest hash (Stage S10).

This percentage applies only to M2.3, not to Milestone 2 overall.

---

# 17. Recommended model and validation assignments

## Claude Opus 5

Use Opus 5 for:

- the initial read-only repository audit;
- identifying premature or contradictory pilot implementations;
- schema and migration architecture;
- deterministic constrained-selector design;
- infeasibility diagnostics;
- final integration review;
- adversarial leakage and provenance review.

## Claude Sonnet 5

Use Sonnet 5 after the decisions and architecture are frozen for:

- bounded production implementation;
- straightforward SQLite migrations;
- candidate-query code;
- canonical serializers and hash utilities;
- CLI wiring;
- fixture creation;
- unit-test expansion;
- documentation synchronization;
- targeted bug fixes.

## Claude Fable 5

Use Fable 5 selectively for:

- an independent methodology review of the final pilot design;
- checking whether quotas are actually measurable from authorized metadata;
- challenging the stable/eventful and industry definitions;
- reviewing leakage boundaries;
- reviewing the exact proposed manifest and quota report before owner approval.

## Manual Mac validation

The project owner should personally perform or supervise:

- baseline commit and tag verification;
- clean-tree verification;
- model-generated diff review;
- isolated Python 3.12 environment creation;
- SEC identity validation without displaying the value;
- deterministic dry-run comparison;
- first live metadata-only command;
- monitoring the request count and allowed-source list;
- confirmation of zero filing-body URLs;
- SQLite integrity and foreign-key checks;
- manifest reconstruction;
- inspection of the exact CIK and accession list;
- Git staging, commit, push, and completion tagging.

### Recommended sequence

1. **Opus 5:** read-only audit and final implementation plan. **— done.**
2. **Owner:** approve D1–D13 (and audit-identified D14–D18). **— done for the documentation-only
   decisions; recorded as Decisions 013–015 (D16 declined, D17 is this exception).**
3. **Opus 5:** architecture design. **— done (Decision 016); migration `0009` itself remains not
   started and unauthorized by this document.**
4. **Sonnet 5:** bounded implementation and tests.
5. **Opus 5:** integration and adversarial code review.
6. **Manual Mac:** offline acceptance.
7. **Manual Mac:** first authorized metadata-only run.
8. **Sonnet 5:** correct narrow implementation defects, when needed.
9. **Fable 5:** independent methodology and manifest review.
10. **Owner:** approve or reject the exact manifest hash.
11. Stop with M2.5 disabled.

---

No implementation, live SEC access, manifest creation, or Git operation is authorized by this
corrected plan. Stage S3 (schema/migration `0009`) and every later stage remain unauthorized until a
separate, explicit instruction.
