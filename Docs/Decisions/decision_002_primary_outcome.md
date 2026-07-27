# Decision 002 — Primary Outcome and Company Universe

**Date:** 2026-07-25  
**Status:** Approved by project owner (approved 2026-07-27, with the primary-universe-boundary
clarification in the new section below; original decision text of 2026-07-25 otherwise unchanged)

## Decision

The primary prediction target is the training-capped, industry-adjusted, one-year change in operating
margin for nonfinancial U.S. domestic public operating companies.

## Formula

`OM(i,t) = OperatingIncomeLoss(i,t) / Revenue(i,t)`

`RawDeltaOM(i,t+1) = OM(i,t+1) - OM(i,t)`

`AdjDeltaOM(i,t+1) = RawDeltaOM(i,t+1) - industry-year median`

Industry is the first two digits of the target filing’s SEC SIC. The cell must have at least 10 firms;
otherwise use the corresponding one-digit SIC-year cell. If that also has fewer than 10 firms, exclude
the observation from the primary adjusted analysis.

## Outcome transformation

- regression caps: development-cohort 1st and 99th percentiles;
- caps applied unchanged to every later cohort;
- uncapped outcome reported as robustness;
- severe deterioration: uncapped adjusted outcome at or below the development-cohort 10th percentile.

## Outcome timing

Use the next eligible annual fiscal period with a period-end gap of 300–430 days. Primary outcomes use
facts first reported in the next original Form 10-K. Later amendments and restatements are robustness
versions.

## Primary universe

Include original Forms 10-K accepted from 2010 through 2024 for U.S. domestic operating companies.

Primary exclusions include:

- SIC 6000–6999;
- shell, blank-check, fund, ETF, and asset-backed issuers;
- non-positive revenue;
- unreconciled revenue or operating income;
- nonstandard annual duration;
- unmatched next annual period;
- invalid SIC;
- failed Item 7 extraction;
- no prior eligible 10-K for the common cohort; and
- frozen parser failures.

Delisted and failed firms remain eligible.

## Primary-universe boundary clarification (added 2026-07-27)

This section formalizes the existing SIC 6000–6999 exclusion above and ties it explicitly to the
M2.3 engineering pilot's **eight** primary-universe-ineligible selected entities
(`Docs/Decisions/decision_013_pilot_selection_mechanics.md`,
`Docs/Decisions/decision_014_pilot_evidence_and_classification_policy.md`,
`Docs/Decisions/decision_015_pilot_use_prohibition.md`,
`Docs/Decisions/decision_016_m23_schema_and_artifact_architecture.md`).

- **Corrected 2026-07-27 (governance-repair, third pass):** the frozen 24-entity pilot contains
  **eight** entities that are `primary_universe_eligible = false`, not four. This follows from the
  controlling rule below (each excluded for its own applicable condition, not from SIC alone), applied
  to the pilot's own frozen composition, not a new exclusion: **four** are the pilot's boundary
  controls (registered investment company/ETF,
  asset-backed issuer, shell/blank-check issuer, foreign-private-issuer annual-report filer), and
  **four** are the pilot's operating-financial-institutions industry-quota entities (Decision 014
  §4's `operating_financial_institutions` family, all of which fall inside SIC 6000–6999). Both
  groups of four are **engineering-only** relative to the primary research universe. They exist to
  exercise ingestion, classification, and selector architecture — never to represent the primary
  research universe.
- **Corrected 2026-07-27 (fourth pass): `primary_universe_eligible` does not derive from SIC alone.**
  `primary_universe_eligible` is `true` **only** when all of the following hold: (1) the entity is
  an eligible operating-company candidate, not a boundary control; (2) required primary-universe
  classification evidence is sufficiently resolved; (3) the entity's SIC is not in 6000–6999; and
  (4) no other Decision 002 primary-universe exclusion (shell, blank-check, fund/ETF, asset-backed,
  non-positive revenue, unreconciled facts, etc. — see "Primary universe" above) applies. This flag
  name gives the existing "Primary exclusions" list above a single, citable identifier for use in
  schema and code once M2.3/M2.5 implementation is authorized.
- Consequences: every boundary-control entity has `primary_universe_eligible = false` **regardless
  of SIC** (condition 1 alone excludes it); every entity with SIC 6000–6999 has
  `primary_universe_eligible = false` **regardless of candidate category** (condition 3 alone
  excludes it); unresolved or conflicting required universe evidence fails closed to `false`
  (condition 2); and SIC 6712 may provisionally satisfy the engineering operating-financial pilot
  quota (Decision 014 §4) but remains primary-universe ineligible and engineering-only. The two
  conditions above are independently sufficient to exclude, not merely the SIC condition, which is
  why both the four boundary controls and the four operating-financial-institutions quota entities
  are excluded even though they are excluded for different reasons under this rule.
- These eight entities **may not enter primary outcome construction, model training, evaluation, or
  Disclosure Drift Index (DDI) claims** under any circumstance, consistent with
  `Docs/Decisions/decision_015_pilot_use_prohibition.md` and `Docs/leakage_register.md` L19.
- The XBRL concept hierarchy (see "Deferred implementation detail" below) must be frozen using
  **accounting semantics, synthetic fixtures, and development-cohort-only (2010–2021) reconciliation
  evidence** — not the M2.3 pilot's own reconciliation quality broadly, since the pilot includes
  these engineering-only, non-primary-universe entities.
- The full 24-entity M2.3 pilot (20 operating companies plus the 4 boundary controls) may be used to
  **test execution** of the already-frozen concept hierarchy — confirming that ingestion and
  reconciliation code runs correctly against real pilot data — but it may **not alter** the
  hierarchy itself once frozen.

## Reason

Operating-margin change is an economically interpretable continuous outcome that differs from the
short-horizon returns, bankruptcy, tax, and risk outcomes emphasized by the closest competitors.
Industry adjustment reduces differences in typical profitability changes across business categories,
while a continuous target avoids designing the entire project around a rare event.

## Deferred implementation detail

The exact XBRL concept hierarchy is not selected by outcome performance. **Amended 2026-07-27:** it
is frozen using accounting semantics, synthetic fixtures, and development-cohort-only (2010–2021)
reconciliation evidence — not "after the 24-company pilot based on reconciliation quality" as
originally worded, since the pilot includes engineering-only financial/control entities that are
never part of the primary universe (see "Primary-universe boundary clarification" above). The
24-entity pilot may test that the already-frozen hierarchy executes correctly; it is not itself a
basis for freezing or revising the hierarchy. Once frozen, the hierarchy is applied identically
across cohorts.

## Revisit triggers

Reopen before later-period evaluation only if:

1. pilot reconciliation is materially unreliable;
2. the common cohort fails the minimum feasibility gates; or
3. the SEC facts cannot support a stable cross-company concept hierarchy.
