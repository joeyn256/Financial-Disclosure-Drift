# Decision 001 — Milestone 0 Novelty Boundary

**Date:** 2026-07-25  
**Status:** Accepted working decision; final literature refresh still required

## Decision

The project will proceed under the following contribution statement:

> Disclosure Drift tests whether models trained only on pre-2022 Form 10-K disclosures lose
> predictive accuracy or calibration when forecasting one-year-ahead, industry-adjusted operating
> deterioration in 2024-era filings; whether any reliability loss is concentrated in style-dependent
> representations; and whether evidence-grounded models are more stable under both observed
> disclosure drift and preregistered, fact-preserving rewrites.

## Reason

The 61-source literature matrix shows direct prior work on each individual component:

- temporal 10-K prediction;
- future financial and adverse-outcome prediction from 10-K narratives;
- operating-risk measures from Item 1A;
- adaptive dictionaries and filing-change features;
- GenAI-era financial reporting;
- controlled narrative transformation; and
- evidence-grounded financial NLP.

No direct match was identified for the complete combined design.

## Claims prohibited by this decision

The project must not claim to be the first:

1. temporal-drift study using 10-K prediction;
2. out-of-sample audit of predictive 10-K information;
3. future-fundamentals, operating-risk, or bankruptcy prediction study using 10-K text;
4. study of AI-assisted or AI-era financial reporting;
5. controlled rewrite or counterfactual financial-narrative experiment; or
6. evidence-grounded financial NLP project.

## Implications

- Calibration is mandatory, not optional.
- The one-year industry-adjusted operating-margin outcome is central to differentiation.
- Style-heavy, financial-only, and evidence-grounded model families must be compared on identical
  temporal splits.
- The controlled rewrite experiment must remain paired, preregistered, and fact preserving.
- The project must preserve risk-factor order, headings, numeric evidence, and source offsets.
- A final literature refresh is required before publication.

## Revisit triggers

Reopen this decision if a new study directly combines the same outcome, temporal split, calibration
analysis, controlled rewrites, and evidence-grounded defense.
