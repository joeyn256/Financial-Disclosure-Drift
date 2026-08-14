# Decision 071 — M3.3-I/R Methodology-Gap Adjudication and Resumption Authorization

```text
STATUS: ACCEPTED — OWNER M3.3-I/R METHODOLOGY-GAP ADJUDICATION
DATE: 2026-08-13
OWNER: Sol/GPT
OUTCOME: M3_3_I_R_METHODOLOGY_GAPS_OWNER_RULED
IMPLEMENTATION_AUTHORIZATION: YES — THE SAME BOUNDED M3.3-I/R STAGE, RESUMED
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

**This record supplies the two operational definitions M3.3-I/R stopped for, disposes the
five implementation observations that stop reported, and authorizes the *same* bounded
I/R stage to resume.** It creates no new stage and no new authority:
[Decision 070](decision_070_m3_3_i_r_implementation_authorization.md) remains accepted
and **unconsumed**, because no frozen implementation target was ever committed.

**It authorizes no real execution.** M3.3-E0, M3.3-E1, M3.3-E2, and M3.4 all remain
unauthorized; network, SEC, reacquisition, and private-evidence access all remain
**NONE**; migration remains `none`; and `m3.2-complete` remains immutable.

**Where this record and an earlier governing record disagree**, this record controls only
where it supplies the previously missing operational definition. Decisions 014, 018, and
067–070 are **not** retroactively rewritten. Decisions 001–070 remain accepted and
byte-unchanged.

---

## 1. Entry state

| Fact | Value |
|---|---|
| Branch | `main` |
| HEAD / `origin/main` | `882dec057d7446faedd45e3528c77a14051598c8` (tree `1c1faa972347deddc3004c5424ad1485b5ff3beb`) |
| Working tree | dirty by the authorized, tested, **uncommitted** partial M3.3-I/R work only |
| Latest accepted decision at entry | **Decision 070** |
| Decision 070 authority | **UNCONSUMED** — no frozen implementation target exists |
| `m3.2-complete` | unchanged (tag object `2865a1479e4576dc18a4098c928b278812f38d00`) |
| Migration chain | `0001`–`0013` |
| Tracked network switches | `network.enabled` `false`; `network.m3_acquire_enabled` `false` |

## 2. Owner acceptance of the stop

```text
M3_3_I_R_METHODOLOGY_STOP_OWNER_ACCEPTED
```

**The prior implementation stop was correct.** The session reached a condition Decision
070 §29 reserves — accepted methodology insufficient to establish a required field — and
returned rather than inventing a rule. The absence of a commit, the missing I7
workstream, the missing mutation campaign, the missing governance synchronization, and
the missing rehearsal artifact are **unfinished work under the unconsumed Decision 070
authority**, not implementation failures.

Two genuine methodology gaps were identified, and both are resolved below: **MG-1**,
Decision 014 §5 event-flag detection semantics, and **MG-2**, boundary-control
classification semantics.

## 3. Ruling R19 — Event-Flag Detection Semantics (MG-1)

```text
M3_3_MG_1_EVENT_FLAG_DETECTION_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.** Decision 014 §5's **twelve** event names are
preserved exactly and remain engineering-coverage classifications only.

**The general rule.** An event flag is true **only** from accepted, structured, explicit
evidence that mechanically establishes that event. **Lack of evidence is not a positive
event**, and valid former-name history is never turned into an identity conflict.

**No detector may use** substring matching, regular expressions over descriptive status
text, fuzzy matching, arbitrary synonyms, company-name keywords, ticker keywords, SEC
`entityType` inference, operator judgment, fame or familiarity, outcome data, filing
narrative, or absence from an alias-only ticker list.

| # | Flag | Predicate |
|---|---|---|
| 4.1 | `inactive` | accepted persisted structured status/classification evidence explicitly and canonically establishes it; otherwise **NOT OBSERVED** |
| 4.2 | `acquired` | as above; no substring and no name-change inference |
| 4.3 | `delisted` | as above. **Absence of a ticker, or absence from `sec_company_tickers*`, is not proof** — those remain alias sources, never an authoritative universe |
| 4.4 | `bankrupt_or_failed` | as above; no inference from names, entity type, or prose |
| 4.5 | `successor_or_predecessor_lineage` | accepted persisted lineage evidence establishes a predecessor/successor relationship involving the candidate. **Never** inferred from similar names, former names alone, same SIC, or ticker reuse |
| 4.6 | `reverse_merger_or_de_spac_review` | accepted structured lineage/review evidence **explicitly** identifies the condition. A generic lineage edge, a shell classification, and a name change each imply **nothing**. Where accepted evidence cannot distinguish it from generic lineage: **NOT OBSERVED**, and **no proxy is invented** |
| 4.7 | `fiscal_year_end_change` | for candidate history: **(A)** the eligible candidate accession history contains a `10-KT` or `10-KT/A`, **or (B)** two consecutive eligible original annual reports whose `report_date` month/day values are more than **7** days apart by the accepted fixed leap-year circular distance. A missing or invalid `report_date` needed for a comparison is **`review_required` for that comparison** and is never guessed. The later selection cross-cutting quota keeps Decision 018's existing selected-accession rule exactly; candidate-history detection is **not** conflated with selected-quota counting |
| 4.8 | `transition_report_filed` | the eligible candidate accession history contains exact form `10-KT` or `10-KT/A`. No text inference |
| 4.9 | `company_name_or_ticker_transition` | **name-only**, per the accepted M2.3 rule: accepted identity evidence, `evidence_role = winning`, evidence level `provisional`, a parseable former-name record, and a valid prior/current or from/to relationship. **Ticker-only evidence does not contribute.** Multiple valid former names are **not** automatically a conflict |
| 4.10 | `multi_registrant_annual_filing` | at least one eligible annual-report accession has more than one **substantively contributing** registrant under the accepted mapping. Submitter-only, noncontributing rows never establish it |
| 4.11 | `unusual_amendment_history` | the accepted amendment-lineage machinery yields a non-ordinary diagnostic — unresolved, possible, ambiguous, cyclic, type-conflicting, order-conflicting, or another accepted review-required/conflicting lineage state. **An ordinary resolved amendment does not establish it**, and no new amendment heuristic is added |
| 4.12 | `material_source_or_identity_conflict` | existing accepted evidence/resolution machinery **explicitly** classifies a material source or identity-relevant fact as conflicting. It is **not** inferred from multiple company names, former-name history, more than one observation, a missing field, an unavailable field, or a merely `review_required` field |

### 3.1 History stratum

**Eventful** requires at least one of the twelve flags affirmatively true. **Stable**
requires every Decision 014 §5 condition to hold mechanically: sufficient eligible
original annual-report history; no observed CIK succession event; no transition report;
no unresolved amendment lineage; no material fiscal-year-end change; no observed
inactive/acquired/bankrupt/failed/delisted state; and no conflicting registrant identity.

**If a fact required to establish `stable` is unresolved, it does not become "no event":**
history is `review_required` and contributes to no affirmative quota.

The "at least six currently inactive/acquired/delisted/bankrupt/failed/or absent-from-
current-public-company-lists" quota may count **only** evidence actually establishable
from accepted evidence, and — because `sec_company_tickers*` is alias-only — **simple
absence from that source may not satisfy the absent-from-public-lists branch**. If the
hard quota cannot be satisfied from accepted evidence, the selector reports
**infeasible**. The detector is never tuned after seeing the real pool, and evidence is
never reacquired automatically.

**Cite as:** *M3.3 Owner Ruling R19 — Event-Flag Detection Semantics.*

## 4. Ruling R20 — Boundary-Control Evidence Predicates (MG-2)

```text
M3_3_MG_2_BOUNDARY_CONTROL_CLASSIFICATION_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED. SEC `entityType` may not assign `control_kind`**, and
the first-cut exact-string comparison between `entityType` and the four kind names is
removed. Classification is evidence-predicate based.

| Kind | Predicate |
|---|---|
| `registered_investment_company_or_etf` | accepted SIC evidence maps to the RIC/ETF boundary-control set **already frozen by `sic-family-mapping/0.2`**. That exact mapping is reused; no competing SIC list is created and none is broadened by proximity. Missing, conflicting, or review-required SIC ⇒ **no affirmative classification** |
| `asset_backed_issuer` | the accepted stored SEC submissions history contains at least one exact Form **`10-D`**. Form metadata only — no filing body, no narrative, no `entityType`, no name heuristic, no new source, and the observation must already exist inside accepted stored metadata |
| `shell_or_blank_check_issuer` | accepted SIC evidence maps to the shell/blank-check boundary-control set already frozen by accepted SIC authority, including the accepted blank-check treatment. Historical shell status is **never** inferred from `entityType`, company name, generic lineage, former names, or reverse-merger suspicion. This is a metadata-qualified boundary-control classification, not a claim about every historical accession |
| `foreign_private_issuer` *(annual-report filer)* | the accepted stored submissions history contains at least one **original** `20-F` or `40-F`. An amendment alone never counts. No country, incorporation-state, `entityType`, or name heuristic; no new retrieval |

### 4.1 Overlap and absence

Exactly one predicate true ⇒ assign that kind. Zero ⇒ the candidate is **not**
affirmatively a boundary control. **More than one ⇒ `review_required` / conflicting**, and
**no precedence among control kinds is defined**: an overlapping candidate cannot satisfy
a control-kind quota unless a later owner ruling resolves it. Controls remain
primary-universe ineligible under the existing rules.

If one or more of the four required control categories cannot be supplied from the
accepted candidate pool, **selection is infeasible**. The predicates are **not** loosened
after seeing the pool, and acquisition is **not** reopened.

**Cite as:** *M3.3 Owner Ruling R20 — Boundary-Control Evidence Predicates.*

## 5. Ruling R21 — XBRL Composite Resolution Value (IN-1)

```text
M3_3_IN_1_XBRL_COMPOSITE_RESOLUTION_OWNER_RULED
```

**Status: RESOLVED — OWNER RULED.** `hash_table`'s internal row/field separator may
**not** be used as an application-level encoding.

The XBRL resolution binds **two** persisted governed facts, so its logical
`resolved_value` is the canonical serialization of exactly:

```json
{ "has_inline_xbrl": <canonical persisted nullable flag>,
  "has_xbrl":        <canonical persisted nullable flag> }
```

rendered through the repository's **existing accepted canonical-JSON serializer**. **No
second JSON serializer and no second hash implementation is created.** That canonical
value is the single `resolved_value` logical field fed into the existing
`pilot_candidate_resolution` `hash_table` preimage; key membership is exactly those two
keys, and no other XBRL field enters it. **Every other single-valued resolution dimension
retains its exact canonical persisted scalar.**

**Cite as:** *M3.3 Owner Ruling R21 — XBRL Composite Resolution Value.*

## 6. Observation dispositions

| ID | Disposition |
|---|---|
| **IN-2** — amendment purpose | **Conservative fail-closed principle ACCEPTED.** No category is invented from metadata that does not establish one. `provisional` evidence with an established accepted category may satisfy the quota; `unproven`, `review_required`, `conflicting`, and `unavailable` may not. Where accepted M3.3 metadata yields `unproven` and no accepted derivation exists: the category stays absent as the schema permits, the resolution digest stays absent where the accepted iff rule requires, `amendment_purpose_quota_eligible` stays false, required provenance rows stay truthful, and the accession keeps any other independently valid role. If the three-category hard quota is ultimately infeasible, **report infeasible**. Purpose is never manufactured from a form suffix, a company name, filing timing, an amendment count, or generic linkage |
| **IN-3** — 2009/2010 pairing | **ELEVATED TO A REQUIRED I/R CORRECTION.** `support_eligible = support_2009` is **not** sufficient proof of the pair quota. A contributing pair belongs to one anchor CIK and has: one valid SUPPORT-role original `10-K` whose official filing date is calendar year **2009** and which is explicitly pre-study / outside the applicable study cohorts; **and** one valid BASE-role original `10-K` whose official filing date is calendar year **2010** with provisional official cohort `development`; **both selected in the same joint result**; counted **once per distinct entity**. The hard requirement is **six distinct entities**. A 2009 support accession without its selected 2010 target satisfies no pair, and vice versa. Implemented in I7 on the accepted joint-selection machinery, with positive and every single-condition negative test. Accepted role definitions are unchanged |
| **IN-4** — package-level network imports | **NONBLOCKING BY ITSELF.** No broad package-import refactor is performed merely because the existing `disclosure_drift.m3` initializer transitively imports modules that themselves import `socket`/`urllib`. The governed prohibition is **no network construction, no network call, and no SEC client or transport creation** during I/R rehearsal and offline execution. Tests and rehearsal are strengthened with a **process-level network bomb**, and the complete E1–E8 rehearsal must make zero such calls. The claim to make is *"no network construction or use occurred"*, never *"no network capability imported"*. If import itself caused a network or durable side effect, that is fixed narrowly or stopped on |
| **IN-5** — mechanical 135-field test | **ADOPTED AS A REQUIRED TEST IMPROVEMENT.** A schema test derives writable-column counts independently from the applied migration-`0009` schema for each of the eight candidate tables and requires `28 + 26 + 35 + 8 + 13 + 13 + 6 + 6 = 135`. It does not assert a literal total without deriving the per-table counts, and it fails if a table's writable schema changes without the OR-2 accounting being updated |

## 7. Calendar-source R18 recheck

The prior stop classified `sec_edgar_calendar_announcement` as category C. That
classification is **not** accepted merely because the partial implementation said so: the
calendar source is traced separately through the accepted OR-2 mapping before I1 is
finalized. If no authoritative candidate field or required freeze provenance consumes its
parsed output, category C is valid; if accepted OR-2 requires `census_calendar_days` for
authoritative candidate content or provenance, it is classified by R18's actual rule and
the already-authorized R17 `census_calendar_days` write is exercised. **The choice is not
made on the basis of desired feasibility**, the trace is documented in the tests and the
rehearsal evidence, and a genuine conflict between accepted records is a stop-and-report.

## 8. What this record does not authorize

It does **not**: authorize the real offline parse (**M3.3-E0**) or progression to
**M3.3-E1** or **M3.3-E2**; authorize a real snapshot, selection, manifest, or root;
approve a root or begin **M3.4**; enable network access; authorize an SEC request,
reacquisition, or re-retrieval; authorize a migration; authorize reading, resolving, or
mutating `EV_ROOT`, the accepted real private catalog, or any M3.2 private evidence;
supply **OR-6**, **OR-7**, **OR-9**, or **OR-11**; pre-resolve Decision 023 **O1**; close
any limitation (**D021-L2** and **D067-L1** remain `ACTIVE`); move `m3.2-complete`; or
create any tag.

**No real candidate distribution has been inspected.** R19, R20, and R21 were frozen
**before** any real candidate execution, from accepted records and synthetic fixtures
only, and none of them may be tuned after a real pool is observed.

## 9. Next authorized action

**Resume and complete the same bounded M3.3-I/R stage under Decision 070's unconsumed
authority**, then return to Sol/GPT for a separate read-only bug-discovery pass and a
fresh independent A1 rehearsal acceptance. **Do not independently accept your own
implementation, and do not execute E0.**

```text
M3_3_DECISION_071_METHODOLOGY_GAP_ADJUDICATION_RECORDED
```
