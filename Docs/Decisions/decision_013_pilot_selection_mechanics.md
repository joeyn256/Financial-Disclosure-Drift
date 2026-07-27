# Decision 013 — M2.3 Pilot Selection Mechanics

**Date:** 2026-07-27
**Status:** Approved by project owner
**Type:** Implementation and provenance decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged by this record. No hypothesis, cohort window, maturity gate,
outcome definition, threshold, or seed is altered.
**Supersedes:** nothing. Freezes selection-mechanics policy left open by
`Milestones/milestone_2_3_pilot_selection_plan.md` §15 (D1, D2, D8, D9, D10, D11, D12, D13).
**Governs:** Milestone 2.3 onward
**Related:** Decision 007 (SEC universe, canonical CIK identity), Decision 008 (filing inventory,
`census_accessions` vs. `inventory_accessions`), Decision 009 (raw-data governance), Decision 010
(cohort date-source rule — see Decision 014 §7 on provisional cohort assignment), Decision 014
(pilot evidence levels and classification), Decision 015 (pilot-use prohibition)

This record approves the plan corrections **P8, P9** and the plan's D1, D2, D8, D9, D10, D11, D12,
D13 (`Milestones/milestone_2_3_pilot_selection_plan.md` §15), as amended by the M2.3 audit findings
recorded in that plan (audit findings C1–C13, blockers B1–B3, corrections P1–P12 — see the plan's
own front matter for provenance). It authorizes **no implementation** — schema (S3), the
selector (S4/S5), and manifest serialization (S6) remain unauthorized until a separate instruction.

## 1. Census as-of cutoff (D1)

- As-of date: **2026-06-30**.
- Coverage extends through the closed 2026 Q2 quarter only.
- `include_open_quarter = false`.
- No open-2026-Q3 daily-index retrieval occurs in M2.3.
- **D16 (register a daily-index source for open-2026 coverage) is declined for M2.3.** No new
  `SourceSpec`, URL-family policy entry, or parser is registered for a daily-index source in this
  milestone. If a future milestone needs open-quarter coverage, that requires its own decision
  record and a Decision 007 amendment (audit finding B3, plan correction P2).
- Per plan correction **P8**, this reduces to *approving a concrete date*, not designing a new
  mechanism: `CoverageWindow(coverage_start, coverage_end, as_of_date, include_open_quarter,
  policy_version)` and the CLI `--as-of` flag already exist (`cli.py:123-147`), as does the
  `required_closed_quarter` / `provisional_open_quarter` / `not_planned` taxonomy
  (`Docs/sec_census_plan.md:36-38`). No new as-of mechanism may be built; the existing one is used
  with this date.
- Per plan correction **P1**, the registered closed-quarter source is `sec_full_index_company`
  (`company.idx`, `/Archives/edgar/full-index/{year}/QTR{q}/company.idx`). There is no
  `master.idx` source. References to a "master index" in the plan or in Decision 010 §4.1 are
  wording drift, not a second registered source; no second source is registered by this decision.

## 2. Candidate storage (D2)

Per plan correction **P9**: the candidate/retrieved split already exists structurally —
`census_accessions` (metadata-only candidates, written by `census.py`) versus
`inventory_accessions` (post-retrieval inventory; nothing currently writes it). This decision does
not create new tables; it freezes the policy those tables must eventually follow:

- The pilot selector must eventually operate from an **immutable, hashed pilot-candidate snapshot**
  derived from `census_accessions`, not from `census_accessions` directly (which remains mutable as
  new census runs append observations).
- **`inventory_accessions` is not written before M2.5.** Writing it implies retrieval-verified
  inventory status that M2.3 metadata-only evidence cannot support.
- The snapshot tables anticipated for schema design (not created by this decision —
  see Decision 013 header and `Milestones/milestone_2_3_pilot_selection_plan.md` §15 D2) are:
  `pilot_candidate_snapshots`, `pilot_candidate_entities`, `pilot_candidate_accessions`,
  `pilot_selection_runs`, `pilot_selected_entities`, `pilot_selected_accessions`, `pilot_reserves`,
  `pilot_quota_results`, `pilot_manifest_versions`.
- **Multi-registrant metadata (added 2026-07-27):** Stage S3's schema must include
  `pilot_candidate_accession_registrants` or an equivalent normalized candidate-snapshot structure
  that preserves every registrant CIK on a multi-registrant candidate accession (mirroring
  `inventory_accession_registrants`'s role, but as an immutable candidate-snapshot table, not the
  post-retrieval inventory table). **`inventory_accession_registrants` must not be relied upon
  before M2.5** — the same rule that applies to `inventory_accessions` generally applies to this
  associated registrant table.

## 3. Counting units (D8)

- Six 2009-support/2010-target pairs must involve **six distinct entities**.
- Four name-or-ticker-change cases must involve **four distinct entities**.
- During M2.3, **former-name evidence** (`formerNames` with `from`/`to`, fully observable per audit
  §3.2) may satisfy this quota. **Current ticker data cannot prove a historical ticker change** —
  only the current `tickers` field is available, so ticker-change claims are retrieval-verified or
  unobservable at M2.3 (audit finding, plan §2.3 correction P3). The frozen "4 name or ticker
  changes" quota is satisfied by name changes alone in M2.3; any ticker-change contribution to this
  quota requires M2.5 verification.
- 12 pre-Inline-XBRL and 12 Inline-XBRL requirements count **distinct original accessions**, not
  distinct entities.
- Six original 2024 filings must cover **six distinct entities**.
- Four original 2025 or 2026 filings must cover **four distinct entities**.
- Two multi-registrant cases must be **two distinct accessions** (not necessarily two distinct
  anchor entities — see §4 below).

## 4. Multi-registrant accounting (D9)

- One selected **anchor CIK** occupies one entity slot.
- Every associated registrant CIK on a multi-registrant candidate accession is preserved in
  **`pilot_candidate_accession_registrants`** (see §2 above and Decision 016 §3) — the immutable
  candidate-snapshot table, **not** `inventory_accession_registrants` (Decision 008), which is
  post-retrieval and must not be relied upon before M2.5.
- The accession satisfies the multi-registrant quota **once**, regardless of how many registrant
  CIKs it carries.
- Other registrant CIKs on that accession do not themselves consume entity slots unless
  independently selected as their own anchor entity through the normal quota process.

## 5. Selector policy (D10)

Per audit findings C2/C3 and plan §8.4: the existing `select_pilot` (`pilot.py:169-211`) is a single
greedy pass that can raise `GateFailureError` on a pool where a feasible solution exists, because
size and industry quotas are a joint assignment problem rather than independently satisfiable.
`QuotaResult.available` (`pilot.py:291`) is a marginal count that cannot distinguish genuine
infeasibility from greedy failure.

**The existing greedy selector must eventually be replaced, not extended.** Its replacement (not
authorized for implementation by this decision) must use:

- integer and categorical comparisons only — no floating-point objective;
- explicit input ordering, fixed before search begins;
- deterministic branch ordering;
- a lexicographic objective (plan §8.4): zero unmet hard quotas, then minimize unresolved/
  provisional evidence, then minimize base-accession count, then stress-accession count, then the
  ordered vector of entity hashes, then the ordered vector of accession hashes;
- a deterministic search-node limit;
- `infeasible_or_unproven` on exhaustion — never a partial manifest;
- the same input snapshot must always produce the same selected and reserve lists.

The infeasibility message's existing invitation to "request... a documented manual substitution"
(`pilot.py:283-285`, audit finding C4) must be removed when the selector is implemented — see
§6 below (reserves and substitution), which forbids discretionary substitution outright.

## 6. Reserves and substitution (D11)

- **No discretionary manual issuer substitution is permitted.**
- Replacement occurs **only** when objective verification (e.g. M2.5 filing-header verification) or
  safe retrieval fails for a selected candidate.
- Replacement always uses the **next deterministic same-stratum reserve**, determined by the same
  tie-breaker and ordering rules used for initial selection — never a discretionary company choice.
- **Reserve compatibility (amended 2026-07-27):** "same-stratum" is not satisfied by matching size or
  industry alone. A deterministic reserve must preserve the **complete quota-contribution or
  replacement-compatibility signature** of the candidate it replaces — every quota dimension the
  original candidate was selected to satisfy (size, industry, history category, cross-cutting
  coverage contributions, and control category where applicable), not merely one or two of them. A
  reserve that matches on size or industry but would silently drop or alter a cross-cutting
  contribution (e.g. a name-change or multi-registrant contribution) is not compatible.
- **If no compatible reserve exists**, replacement is not permitted by discretionary approximation.
  The selector must either perform a **complete deterministic reselection** over the frozen candidate
  snapshot (never a partial, hand-adjusted manifest) or return a **fail-closed
  `infeasible_or_unproven`** result. A partial or best-effort substitution is never an acceptable
  third option.

## 7. Manifest hashing (D12)

- Use canonical JSON: UTF-8, LF line endings, sorted object keys, arrays in deterministic order, no
  nonfinite numbers, canonical accession/CIK formatting, UTC timestamps with `Z`, relative paths
  only.
- The hash contract must eventually include (not implemented by this decision): source-observation
  hashes, candidate-table hash, quota-definition hash, selector-policy hash, entity-table hash,
  accession-table hash, reserve-table hash, quota-report hash, and root manifest hash.
- **`generated_at` is excluded from the content hash** (or moved to a separate audit envelope not
  covered by the content hash).
- Per plan correction **P7**: an as-of/candidate-snapshot hash precedent already exists —
  `IndexPlan`'s plan hash and `CoverageWindow.as_record()` (`index_plan.py:117-125`), which consults
  no clock. The eventual implementation reuses this precedent rather than inventing a parallel
  hashing scheme, and reuses `release/hashing.py`.

## 8. Approval semantics (D13)

- M2.3 completion requires **owner approval of the exact final manifest hash**, not merely
  generation of a proposed manifest.
- M2.5 remains disabled after that approval until separately authorized. Approving the M2.3 manifest
  hash is not itself an M2.5 authorization.

## 9. Reason

Every mechanic above either (a) reuses an existing, already-reviewed mechanism rather than
authorizing a new one (as-of window, hashing precedent, candidate/inventory table split), or (b)
closes a specific soundness gap the audit identified in the current scaffold (greedy selector
unsoundness, discretionary-substitution wording, marginal-only infeasibility reporting). None of
these mechanics reads, fits on, or is informed by any 2022–2026 outcome; all are pre-registration
mechanical/provenance choices about how metadata-only candidates are organized, selected, and
hashed.
