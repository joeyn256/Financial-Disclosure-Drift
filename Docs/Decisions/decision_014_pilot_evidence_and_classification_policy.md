# Decision 014 — M2.3 Pilot Evidence Levels and Classification Policy

**Date:** 2026-07-27
**Status:** Approved by project owner. §4 (SIC-to-industry-family mapping) was approved as a draft
pending owner review on 2026-07-27 and was **frozen as `sic-family-mapping/0.2` on 2026-07-27**
during the same-day governance-repair correction pass.
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged. No hypothesis, cohort window, maturity gate, outcome
definition, threshold, or seed is altered.
**Supersedes:** nothing. Freezes classification policy left open by
`Milestones/milestone_2_3_pilot_selection_plan.md` §15 (D3, D4, D5/D14, D6, D7) and audit-identified
blocker B2, plus provisional cohort assignment under Decision 010 (audit blocker B1).
**Governs:** Milestone 2.3 onward
**Related:** Decision 010 (cohort date-source rule and public-availability boundary), Decision 013
(pilot selection mechanics), Decision 015 (pilot-use prohibition), `Docs/leakage_register.md` L04
(survivorship bias)

## 1. Evidence levels (D3)

Every pilot candidate classification (size, industry, history, cohort, amendment purpose) is
assigned exactly one of five evidence states:

| State | Meaning |
|---|---|
| `verified` | Confirmed by retrieval-verified, document-level evidence (not available during M2.3 — all M2.3 evidence is metadata-only). |
| `provisional` | Metadata-qualified: sufficient for deterministic engineering selection, not yet document-verified. |
| `review_required` | Evidence is missing, stale, or conflicting; cannot satisfy an affirmative quota. |
| `conflicting` | Two or more preserved source observations disagree and neither is authoritative without further evidence. |
| `unavailable` | No approved M2.3 source carries this field for this candidate. |

A **provisional** candidate may satisfy a provisional engineering quota only when all three hold:

1. its evidence basis (source, field, observation ID) is stored on the candidate record;
2. M2.5 verification of that classification is mandatory before any use beyond engineering
   coverage; and
3. a deterministic same-stratum reserve exists, chosen by the same tie-breaker rules as initial
   selection (Decision 013 §6).

A candidate whose evidence state is `review_required`, `conflicting`, or `unavailable` **cannot**
satisfy an affirmative quota of any kind. It may still be recorded for coverage/reporting purposes.

## 2. Filer-size classification (D4)

- Current SEC entity-category metadata (`category` field, entity-level, current value —
  `parsers/submissions.py:123`) may be used **only provisionally**, and only when it maps
  unambiguously to one of: large accelerated filer; accelerated filer; non-accelerated filer or
  smaller-reporting company.
- Missing or conflicting classification is `review_required` and **cannot** satisfy a size quota.
- The audit (§3.2) notes `category` is commonly blank for inactive issuers — exactly the population
  the ≥6 "inactive eventful" entities depend on (see §5 below and `Docs/leakage_register.md` L04).
  A blank or ambiguous category is `review_required`, not defaulted to any stratum.
- Every selected `provisional` size classification requires M2.5 filing-cover-page verification and
  a deterministic same-size reserve (per §1 rule 3).
- Overlap between "smaller-reporting company" and "non-accelerated filer" is resolved by treating
  them as one combined stratum for the size quota (per the frozen **7/7/6** wording — seven large
  accelerated, seven accelerated, six non-accelerated or smaller-reporting), since the two
  categories are not always mutually exclusive in current SEC metadata and no M2.3 source can
  reliably distinguish them without document evidence.

## 3. Industry assignment (D5, D14 combined) — policy

- Current entity SIC (`submissions` JSON `sic`/`sicDescription`, entity-level, current value) may be
  used **provisionally**, only where present and non-conflicting.
- Missing, stale, or conflicting SIC is `review_required` and **cannot** satisfy an affirmative
  industry quota. `REVIEW_CONFLICTING_SIC` already exists as a reason code (`inventory.py:126`) and
  is reused rather than adding a new one at this stage.
- **L04 survivorship exposure is explicit:** for a delisted, acquired, or bankrupt issuer, current
  SIC is disproportionately stale or absent (audit blocker B2). Assigning industry from current SIC
  would systematically bias the industry quota toward survivors if `review_required` candidates were
  allowed to silently drop out rather than being tracked. This decision requires the exclusion
  itself (§1 rule) to be visible in the quota report, not merely absent.
- Every selected provisional industry classification requires M2.5 filing-time SIC verification
  (from the accession's own filing-time SIC evidence, not the current entity profile) and a
  deterministic same-family reserve.
- Filing-time SIC does not exist in any approved M2.3 source (audit blocker B2: `submissions` JSON
  SIC is entity-level current only; `company.idx` has no SIC column; SGML-header SIC is a
  filing-body object, prohibited throughout M2.3). This decision does not attempt to manufacture a
  filing-time SIC source in M2.3 — it accepts provisional current-SIC assignment under the rules
  above, deferring conclusive verification to M2.5.

## 4. SIC-to-industry-family mapping — **FROZEN, `sic-family-mapping/0.2`**

Version identifier: `sic-family-mapping/0.2`, frozen by owner approval on 2026-07-27. Version 0.1
was a draft circulated for review and is superseded in full by this version; the corrections between
0.1 and 0.2 are noted inline below for traceability.

This mapping is **still not implemented in any Python module by this decision** — freezing the
mapping as a decision-record artifact is not itself a code change. Implementation remains gated by
Stage S3 (schema/migration work), which is not authorized by this decision.

Six frozen families (per `Milestones/milestone_2_3_pilot_selection_plan.md` §4.1): technology and
communications; operating financial institutions; industrial and materials; consumer, retail, and
services; healthcare and life sciences; energy and utilities.

| Family | SIC ranges / codes | Notes |
|---|---|---|
| **Technology and communications** | 3570–3579 (computer/office equipment); 3661–3669 (communications equipment); 3670–3679 (semiconductors and related electronic components); 4812, 4813, 4822, 4830, 4841, 4899 (telephone, broadcasting, cable, other communications); 7370–7374 (prepackaged software, computer integrated systems, data processing) | **v0.2 changes:** 3612 and 3620–3629 reassigned to Industrial and Materials (see that row). Computer-services range narrowed from 7370–7379 to 7370–7374; 7377 reassigned to Consumer, Retail, and Services (see that row). 7375, 7376, 7378, 7379 are not mapped and remain `review_required`. |
| **Operating financial institutions** | 6020–6036 (national/state commercial banks, savings institutions); 6141–6199 (non-depository credit institutions); 6200–6221 (security/commodity brokers, exchanges); 6300–6411 (insurance carriers and agents); 6712 (bank holding companies) | **Excludes** 6726 (investment offices, NEC) and closed-end/open-end fund codes, which map to the RIC/ETF **boundary-control** category, and 6770 (blank checks), which maps to the shell/blank-check **boundary-control** category — neither is eligible for the operating-company industry quota. **v0.2:** 6712 is included only in an **engineering-only operating-financial stratum** — usable for pilot coverage/stratification tracking, but it may not affirmatively satisfy the operating-financial industry quota without further owner-reviewed resolution. 6719 (other holding companies, NEC) remains `review_required`, unchanged from 0.1. **6798 (REITs) is removed from affirmative operating-financial quota satisfaction** (0.1 had included it): classified `review_required`, usable only as an **engineering-only real-estate stress case**, never as a quota-satisfying industry member. |
| **Industrial and materials** | 1000–1499 (mining, excluding 1220–1241 and 1300–1399 — see Energy); 1500–1799 (construction); 2200–2299, 2600–2699 (textiles, paper); 2800–2819, 2860–2899 (industrial chemicals, excluding pharmaceuticals); 3000–3099 (rubber, plastics); 3200–3299 (stone, clay, glass); 3300–3499 (primary/fabricated metals); 3500–3569, 3580–3599 (industrial machinery, excluding computer equipment); **3612, 3620–3629** (electrical industrial apparatus, incl. power/distribution transformers); 3700–3799 (transportation equipment); 4000–4699 (railroads, trucking, transportation services, excluding communications) | **v0.2 changes:** 3612 and 3620–3629 reassigned here from Technology. The 1000–1499 exclusion now explicitly covers **both** 1220–1241 (coal, per 0.1) **and** 1300–1399 (oil and gas extraction) — 0.1 excluded only 1220–1241, leaving 1300–1399 double-counted against the Energy row; that overlap is corrected. |
| **Consumer, retail, and services** | 2000–2099, 2100–2199 (food and tobacco manufacturing); 2300–2399 (apparel); 2500–2599 (furniture); 2700–2799 (printing, publishing); 5000–5199 (wholesale trade); 5200–5999 (retail trade, incl. 5800–5899 eating/drinking); 7000–7099 (hotels); 7200–7299 (personal services); 7300–7369 (business services, excluding computer services); **7377** (computer rental and leasing); 7500–7599 (auto repair); 7800–7999 (motion pictures, amusement, recreation) | **v0.2 changes:** the 2000–2199 description is corrected to **food and tobacco manufacturing** — 0.1 incorrectly attached "apparel manufacturing" to this range; apparel is, and remains, its own 2300–2399 entry. 7377 reassigned here from Technology. |
| **Healthcare and life sciences** | 2830–2836 (pharmaceutical preparations, biological products, diagnostic substances); 3841–3851 (surgical and medical instruments); 8000–8099 (health services) | **v0.2 changes:** 3826 (laboratory analytical instruments) is **removed from automatic Healthcare classification** (0.1 had included it) and marked `review_required` — it spans general scientific/industrial instrumentation as well as healthcare-adjacent use. 8731 (commercial physical/biological research) remains `review_required`, unchanged from 0.1. |
| **Energy and utilities** | 1220–1241 (bituminous coal and lignite mining); 1300–1399 (oil and gas extraction); 2900–2999 (petroleum refining); 4900–4999 (electric, gas, sanitary services, incl. 4911, 4922–4924, 4931, 4941) | Unchanged from 0.1. |

Any SIC code not covered by the ranges above, any code newly excluded by a v0.2 correction (3826,
6798, 6719), or any code the owner flags during future review, is `review_required` for the industry
quota rather than defaulted into a family by proximity.

**Foreign-private-issuer (FPI) control classification is not a SIC matter.** FPI status is a filer
attribute independent of industry and is governed by §2 (filer classification) evidence, not this
mapping.

## 5. Stable and eventful history (D6)

Using the proposed definitions from the corrected M2.3 plan
(`Milestones/milestone_2_3_pilot_selection_plan.md` §4.3):

**Stable history** — an entity qualifies when all hold:

- at least four eligible original annual-report filings;
- no observed CIK succession event;
- no 10-KT;
- no unresolved amendment lineage;
- no material fiscal-year-end change;
- no observed inactive, acquired, bankrupt, failed, or delisted state;
- no conflicting registrant identity.

**Eventful history** — an entity qualifies when at least one frozen event flag exists: inactive;
acquired; delisted; bankrupt or failed; successor or predecessor lineage; reverse merger or de-SPAC
review; fiscal-year-end change; 10-KT filing; company-name or ticker transition; multi-registrant
annual filing; unusual amendment history; material source or identity conflict.

These definitions are frozen as stated and must not be adjusted after the real candidate
distribution is inspected — a change requires a new decision record.

**Current inactive, acquired, delisted, failed, or similar status may be used only for
engineering-coverage stratification** (which stable/eventful bucket a candidate falls in for
quota-filling purposes). It must never influence feature definitions, vocabulary, thresholds,
transforms, model choice, or outcome construction — see Decision 015 and
`Docs/leakage_register.md` L19.

## 6. Amendment-purpose categories (D7)

Three high-level categories are frozen:

1. administrative, certification, signature, or exhibit-only;
2. financial-statement, accounting, restatement, or XBRL correction;
3. narrative, business, risk, control, or governance disclosure.

Because definitive purpose generally requires filing-level (document-body) evidence, which is
prohibited in M2.3, these categories may be marked only `provisional` or `unproven` during M2.3.
Definitive verification belongs to M2.5. No amendment-purpose classification may satisfy an
affirmative quota at the `unproven` level; a `provisional` classification follows the §1 rules
(evidence basis stored, M2.5 verification mandatory, same-stratum reserve).

## 7. Provisional cohort assignment under Decision 010 (audit blocker B1)

Decision 010 §4.1 ranks official-filing-date sources: accession-header evidence is
precedence 1 ("canonical after retrieval"), while Submissions API `filingDate` and index
`date filed` are precedence 2 ("provisional discovery and reconciliation observation"). Because
accession-header retrieval is a filing-body operation prohibited throughout M2.3, **every M2.3
candidate carries a precedence-2, provisional official filing date and therefore a provisional
cohort.**

This decision rules that a precedence-2-only official filing date yields:

```text
cohort_evidence_level = provisional
```

and that **this is not the same condition as "ambiguous cohort assignment"** in the plan's §5
candidate-level fail-closed list. A provisional-by-design cohort (every M2.3 candidate) is eligible
for selection; an ambiguous cohort (e.g. `indeterminate` ordering, unexplained date divergence per
Decision 010 §5.1, or conflicting precedence-2 observations that cannot be reconciled) is not.

Requirements:

- M2.5 accession-header verification is mandatory for every selected candidate's cohort assignment.
- If M2.5 verification later shows the official filing date crosses a frozen cohort boundary
  relative to the provisional value, this triggers either deterministic same-stratum replacement
  (Decision 013 §6) or a formal manifest revision — never a silent correction of the frozen
  manifest.

## 8. Reason

Each classification area above resolves a specific observability gap the audit identified (B1, B2,
and the four corrected observability rows in audit §3.2) using the same shape: accept current/
metadata-only evidence provisionally, exclude unresolved evidence from affirmative quota
satisfaction, and require M2.5 document-level verification with a deterministic reserve. This
avoids two failure modes simultaneously: rejecting every M2.3 candidate (because no M2.3 evidence is
ever document-verified), and silently treating unverified metadata as ground truth.
