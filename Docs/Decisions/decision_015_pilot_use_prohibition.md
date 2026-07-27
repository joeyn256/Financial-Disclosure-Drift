# Decision 015 — M2.3 Pilot-Use Prohibition

**Date:** 2026-07-27
**Status:** Approved by project owner
**Type:** Implementation and leakage-prevention decision. **Not** a preregistration deviation;
`Docs/preregistration.md` is unchanged. No hypothesis, cohort window, maturity gate, outcome
definition, threshold, or seed is altered.
**Supersedes:** nothing.
**Governs:** Milestone 2.3 onward
**Related:** Decision 013 (pilot selection mechanics), Decision 014 §5 (stable/eventful history),
`Docs/leakage_register.md` L19 (this decision's leakage-register entry)

## 1. Decision

The M2.3 engineering pilot, and specifically its eventful/inactive-history stratification (Decision
014 §5), is **engineering-coverage only**. It may not inform, directly or indirectly:

- feature definitions;
- vocabulary;
- thresholds;
- transformations;
- model families;
- model selection;
- outcome construction;
- Disclosure Drift Index (DDI) construction.

This prohibition applies regardless of whether the informing use is explicit (e.g. tuning a
threshold against pilot composition) or incidental (e.g. choosing a vocabulary because it performed
well on the 24-entity pilot).

## 2. Reason

Audit finding (§3.3, "New — not in the plan"): whether an issuer is currently absent from public
company lists, inactive, acquired, delisted, bankrupt, or failed is knowledge that **post-dates**
every filing in the pilot. Using that current-state fact to *stratify an engineering pilot*
(ensuring coverage of both stable and eventful histories) is legitimate and does not touch any
outcome. Using the resulting pilot — or its stratification — to fit or inform any feature,
threshold, vocabulary, transform, or model choice would be look-ahead: it would let a fact knowable
only in hindsight shape decisions applied to the frozen research design. The plan's existing §7.3
holdout safeguards fence the 2024–2026 filing cohorts but say nothing about this distinct
current-state-stratification risk, hence a separate, explicit prohibition.

## 3. Scope note

This decision does not prohibit using the pilot for its intended engineering purposes: proving the
selector is sound, proving manifest reconstruction is deterministic, exercising ingestion QA gates,
and validating retrieval-verification workflows ahead of M2.5. The prohibition is specifically on
letting pilot membership or its stratification leak into any research artifact governed by
`Docs/preregistration.md`.

## 4. Leakage register

This decision is recorded as `Docs/leakage_register.md` entry **L19**.
