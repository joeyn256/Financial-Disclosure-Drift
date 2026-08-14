# Decision 072 — M3.3 Full-Index / Multi-Registrant Source Correction

```text
STATUS: ACCEPTED — OWNER M3.3 FULL-INDEX / MULTI-REGISTRANT SOURCE CORRECTION
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_R18_FULL_INDEX_SOURCE_DISPOSITION_OWNER_CORRECTED
IMPLEMENTATION_AUTHORIZATION: YES — THE SAME BOUNDED M3.3-I/R STAGE, CONTINUED
REAL_PRIVATE_PARSE_AUTHORIZATION: NO
REAL_SNAPSHOT_AUTHORIZATION: NO
REAL_SELECTION_AUTHORIZATION: NO
MANIFEST_ROOT_CONSTRUCTION_AUTHORIZATION: NO
M3_4_AUTHORIZATION: NO
NETWORK_AUTHORIZATION: NONE
REACQUISITION_AUTHORIZATION: NONE
PRIVATE_EVIDENCE_AUTHORIZATION: NONE
MIGRATION_AUTHORIZED: none
REQUEST_CEILING: 0
```

**This is a narrow owner correction discovered during owner review of the resumed
M3.3-I/R report.** It corrects one source disposition, restores the accepted evidence
path for a hard quota, and disposes the six observations that report raised. It creates
no new stage: [Decision 070](decision_070_m3_3_i_r_implementation_authorization.md)
remains accepted and unconsumed, and
[Decision 071](decision_071_m3_3_i_r_methodology_gap_adjudication.md) remains accepted.

**It supersedes Decision 068 / the corrected M3.3 contract's R18 source disposition
ONLY to the extent that `sec_full_index_company` was classified category C /
validation-only / candidate-irrelevant.** All other accepted Decision 067–071 authority
stands. No general reopening of the contract occurs, and there is no migration, no new
network source, no reacquisition, no quota change, and no selector-methodology change.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 remain
unauthorized; network, SEC, reacquisition, and private evidence remain **NONE**.

---

## 1. The defect

The prior R18 analysis classified all 70 `sec_full_index_company` sources as category C
because the then-current orchestration path routed their parsed content only toward
`census_index_*` structures that OR-2 does not consume.

**That reasoning is insufficient.** Source disposition is governed by accepted
**methodological use**, not by whether the current implementation happens to expose a
candidate-facing route. Accepted methodology uses `company.idx` to establish
multi-registrant membership, and the Submissions JSON alone cannot: `census_accessions`
carries one registrant CIK and one submitter CIK and no more.

A zero `multi_registrant` result produced because M3.3 elected not to parse
`company.idx` would therefore be an **implementation error, not legitimate
infeasibility**.

## 2. Ruling R22 — Full-Index Source Disposition

```text
M3_3_R18_FULL_INDEX_SOURCE_DISPOSITION_OWNER_CORRECTED
```

`sec_full_index_company` is **CANDIDATE-SUBSTANTIVE**. It is **category A** when its
plan-bound accepted stored observation is usable and its required offline parse
succeeds; **category B** when the source is unavailable, failed, malformed, unbound, or
otherwise cannot safely establish its required evidence; and **never category C**.

The 70 accepted quarterly objects remain plan-bound stored evidence and **no new
retrieval is authorized**. Category B does **not** convert the multi-registrant quota
into a deferred quota; if required evidence remains unavailable after the correct source
path exists, the later selector may be **infeasible**.

**Cite as:** *M3.3 Owner Ruling R22 — Full-Index Source Disposition.*

## 3. Ruling R23 — Full-Index Registrant Materialization

Restores the accepted candidate-facing path from stored `company.idx` evidence to the
registrant representation M3.3 candidate construction consumes.

| Aspect | Rule |
|---|---|
| **Source** | Only plan-bound accepted stored `sec_full_index_company` objects |
| **Parser** | The existing accepted pure `parsers/full_index.py`. **No second full-index parser, no second accession canonicalizer, no string parsing inside the builder, no network** |
| **Accession binding (§5.1)** | The canonical accession identity derived from the `File Name` column by the **existing** canonicalization machinery. Never by company name, ticker, row order, recency, object size, path, or operator choice. A `company.idx` accession must match an accession already established in the authoritative census accession layer; **a full-index row never creates a candidate accession**. An index-only accession is reported as a diagnostic, never manufactured |
| **Anchor (§5.2)** | The authoritative anchor remains the already resolved census accession anchor. A `company.idx` row whose canonical CIK equals it is corroborating evidence |
| **Associated (§5.2)** | Every **other distinct canonical CIK** appearing in accepted `company.idx` rows for that same canonical accession. Registrant relationships are never inferred from company name |
| **Submitter-only (§5.2)** | `company.idx` creates **no** submitter-only membership. Existing accepted submitter-only evidence is preserved and remains noncontributing |
| **Multi-registrant (§5.3)** | True **iff** the candidate-facing registrant set has exactly one valid anchor **and** at least one distinct valid associated registrant. Submitter-only rows never make it true; repeated rows for one CIK never create a second registrant; the flag is never a raw row count |
| **Evidence level (§5.4)** | A successfully parsed, internally consistent, plan-bound row establishing an anchor or associated registrant is metadata-qualified **`provisional`**. **No `verified` during M3.3.** Malformed, conflicting, or structurally inconsistent evidence keeps its accepted weak or fail-closed state; a conflict is never promoted to satisfy a quota |
| **Consistency (§5.5)** | Where `company.idx` supplies accession, form, filing-date, or CIK fields checkable against the authoritative record, they are consistency and provenance evidence under existing accepted resolution semantics. They **never silently overwrite** an authoritative value, and a material unexplained conflict fails closed. An accession identity is never repaired from name similarity |
| **Destination (§5.6)** | The **existing R17-authorized** census representation OR-2 already consumes. **No `census_index_*` write**, **no R17 widening**, **no migration**, **no parallel M3-only registrant table.** A narrow M3 offline persistence helper may write only already-permitted tables and must preserve the accepted canonical identity, provenance, and evidence conventions |

**Cite as:** *M3.3 Owner Ruling R23 — Full-Index Registrant Materialization.*

## 4. Ruling R24 — Multi-Registrant Hard-Quota Preservation

```text
M3_3_MULTI_REGISTRANT_HARD_QUOTA_SOURCE_PATH_OWNER_RESTORED
```

The frozen multi-registrant requirement is **measurable, hard, not deferred, and not
optional**. It may **not** be placed in `APPROVED_DEFERRED_QUOTA_KEYS` or any equivalent
mechanism. The only previously approved M2.3 unmeasurable-quota deferral remains
`difficult_or_nonstandard_packages`, and **that exception is not generalized**.

The joint selector consumes the corrected `multi_registrant` flags after full-index
materialization. If the correctly materialized frozen real pool cannot satisfy the
requirement, the accepted **infeasible** disposition is returned. The quota is never
lowered or deferred; submitter-only rows and duplicate registrant rows are never counted;
registrants are never invented; company names are never identity; and data is never
reacquired automatically.

**Cite as:** *M3.3 Owner Ruling R24 — Multi-Registrant Hard-Quota Preservation.*

## 5. Ruling R25 — Semantic Source-Disposition Standard

R18 category classification is based on the **accepted role** of a source in M3.3
authoritative candidate construction. **A source does not become category C merely
because existing code lacks a candidate-facing parse or persistence route.** Category C
means the accepted M3.3 methodology does not require the source's substantive content to
establish authoritative candidate facts.

| Source | Disposition |
|---|---|
| `sec_full_index_company` | **A / B** — candidate-substantive, due to multi-registrant |
| `sec_edgar_filing_calendar` | **C** — the accepted current trace establishes no candidate-facing substantive dependency |
| `sec_edgar_calendar_announcement` | **C** — unless an authoritative candidate dependency is independently found |

This record authorizes no other source's reclassification without the same forward-trace
standard.

**Cite as:** *M3.3 Owner Ruling R25 — Semantic Source-Disposition Standard.*

## 6. Ruling R26 — RIC/ETF SIC Enumeration

The **R20** RIC/ETF SIC set is exactly **`6722`** and **`6726`** — the mechanical
enumeration of the accepted open-end / closed-end investment-office wording. It is not
broadened by proximity, and **`6798` is not included**: accepted policy treats REITs as
an engineering-only operating-financial matter, not the RIC/ETF control. No further
methodology choice remains on OBS-B.

**Cite as:** *M3.3 Owner Ruling R26 — RIC/ETF SIC Enumeration.*

## 7. Dispositions of the resumed report's observations

| ID | Disposition |
|---|---|
| **OBS-A** — calendar A → C | **ACCEPTED.** The calendar is not authoritative candidate content: the accepted rule derives `acceptance_date_sec` directly from the SEC acceptance value, and candidate construction does not use `census_calendar_days` for filing or acceptance dates. Category C is retained unless a contradictory authoritative dependency is found, and the removed calendar parse branch is **not** restored merely because this record corrects the full-index source |
| **OBS-B** — RIC/ETF `{6722, 6726}` | **ACCEPTED**, and fixed by **R26** |
| **OBS-C** — four R19 status flags may remain NOT OBSERVED | **ACCEPTED as a possible real-pool consequence.** R19 is not weakened. If accepted real evidence does not establish them they remain unobserved, and if a hard quota is consequently infeasible **after the correct source set has been materialized**, the infeasible disposition is reported |
| **OBS-D** — multi-registrant expected zero / non-binding | **REJECTED.** It conflicts with accepted Decisions 014, 016, 018, and 019. The quota is measurable from authorized metadata, hard, not deferred, not optional, and not covered by the difficult-package deferral. Corrected by **R22**, **R23**, and **R24** |
| **OBS-E** — FPI naming | **ACCEPTED.** Project-facing semantic kind `foreign_private_issuer_annual_report_filer`; persisted migration-`0009` value `foreign_private_issuer`, which stays authoritative for persistence. No migration, no CHECK alias, no schema rewrite |
| **OBS-F** — SIC authority fail-closed | **ACCEPTED**, and the rule is not weakened. Note that the accepted M3.2 evidence set contains the approved SIC source object and that M3.3 offline parsing is responsible for exercising the accepted stored source path during synthetic rehearsal: **a deliberately absent synthetic SIC fixture is not evidence that the real accepted source is absent** |

## 8. Governance surfaces this record corrects

Current-state records must say: the calendar remains **C**; the full index is **A/B**;
multi-registrant remains **hard**; `{6722, 6726}` is confirmed; and Decision 071's OBS-D
inference is **rejected**. **Decision 068 is not rewritten historically** — the
correction is expressed as supersession on the one point R22 names.

## 9. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root;
approve a root or begin **M3.4**; enable network access; authorize an SEC request,
reacquisition, or re-retrieval; authorize a migration or a sixteenth R17 table; authorize
any `census_index_*` write; authorize reading or mutating `EV_ROOT`, the accepted real
private catalog, or any M3.2 private evidence; change any quota, role definition, or
selector methodology; supply **OR-6**, **OR-7**, **OR-9**, or **OR-11**; pre-resolve
Decision 023 **O1**; close any limitation; move `m3.2-complete`; or create any tag.

## 10. Next authorized action

**Continue the same still-uncommitted Decision-070 / Decision-071 M3.3-I/R stage**, with
every uncompleted Decision-071 obligation still in force, then return to Sol/GPT. **Do
not independently accept the implementation, and do not execute E0.**

```text
M3_3_DECISION_072_FULL_INDEX_SOURCE_CORRECTION_RECORDED
```
