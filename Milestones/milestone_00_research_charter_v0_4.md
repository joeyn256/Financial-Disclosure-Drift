# Disclosure Drift

## Milestone 0 Research Charter and Novelty Audit — Version 0.4

**Date:** 2026-07-25  
**Status:** Stage 1 preregistration drafted; project-owner approval, Stage 2 freeze records, and direct-competitor full-paper audit remain

## 1. Working title

**Disclosure Drift: Temporal Reliability of Financial-Filing Models in the Generative-AI Era**

## 2. Novelty verdict

**Proceed with a combined reliability contribution.**

The cumulative 61-source literature matrix establishes prior work on temporal 10-K prediction,
future financial and adverse-outcome prediction from filing narratives, operating-risk indices,
GenAI-era reporting, controlled financial-text transformations, and evidence-grounded financial NLP.

No direct match has been identified for the complete combination of:

1. pre-2022 model development;
2. a 2024-era untouched test;
3. one-year industry-adjusted operating deterioration;
4. accuracy and calibration decay;
5. a direct comparison of financial, style-heavy, and evidence-grounded models;
6. observed disclosure drift; and
7. paired fact-preserving rewrites.

Novelty remains provisional until all High-threat papers receive full-paper review and the literature
is refreshed immediately before publication.

## 3. Frozen contribution statement

> Disclosure Drift tests whether models trained only on pre-2022 Form 10-K disclosures lose
> predictive accuracy or calibration when forecasting one-year-ahead, industry-adjusted operating
> deterioration in 2024-era filings; whether any reliability loss is concentrated in style-dependent
> representations; and whether evidence-grounded models are more stable under both observed
> disclosure drift and preregistered, fact-preserving rewrites.

## 4. Confirmatory hypotheses

- **H1:** the style-heavy model has positive relative-MAE decay in 2024;
- **H2:** the style-heavy model decays more than the financial-only model;
- **H3:** higher frozen DDI predicts larger absolute style-model error in 2024;
- **H4:** the style-heavy model is more sensitive to fact-preserving rewrites than the
  evidence-grounded model;
- **H5:** the evidence-grounded model has less relative-MAE decay and less calibration-slope
  deterioration than the style-heavy model.

Two-sided inference and Holm adjustment are required. Null and contradictory results remain reportable.

## 5. Primary company universe

Primary common cohort:

- U.S. domestic operating companies;
- original Form 10-K;
- acceptance dates 2010–2024;
- valid point-in-time financial facts;
- valid Item 7 extraction;
- a prior eligible Form 10-K;
- a matched next annual period.

Primary exclusions:

- SIC 6000–6999;
- funds, ETFs, asset-backed issuers, shells, and blank-check companies;
- foreign private issuers;
- non-positive revenue;
- unreconciled financial concepts;
- annual periods outside 300–430 days;
- invalid SIC;
- failed parser observations.

Delisted, bankrupt, and failed companies remain eligible.

## 6. Primary text scope

- Item 1A — Risk Factors
- Item 7 — Management’s Discussion and Analysis
- Item 9A — Controls and Procedures

Item 7 is required. Missing optional sections receive explicit indicators. Source order, headings,
list structure, and offsets must be retained.

## 7. Temporal design

| Cohort | Acceptance dates | Role |
|---|---|---|
| Development | 2010–2021 | All outcome-based feature and model development |
| Transition evaluation | 2022–2023 | Locked evaluation; no predictive tuning |
| Final primary test | 2024 | One untouched confirmatory evaluation |
| Provisional extension | 2025 onward | Monitoring only until complete outcome coverage |

Model selection uses the five rolling-origin folds recorded in Decision 003. The term **transition
validation** is superseded.

## 8. Primary outcome

`OM = OperatingIncomeLoss / Revenue`

`RawDeltaOM = OM(t+1) - OM(t)`

`AdjDeltaOM = RawDeltaOM - median RawDeltaOM for target-filing SIC industry and t+1 year`

Primary industry rule:

- 2-digit SEC SIC-year median;
- minimum 10 firms;
- fallback to 1-digit SIC-year;
- exclude from adjusted primary analysis if fallback also has fewer than 10 firms.

Regression caps are the development-cohort 1st and 99th percentiles. Severe deterioration is the
development-cohort 10th percentile of the uncapped adjusted outcome. Every threshold remains fixed
after development.

## 9. Primary model families

1. B0 constant benchmark
2. F financial-only
3. S traditional style-heavy text
4. FS financial plus traditional style
5. E financial plus evidence-grounded text

TF-IDF, embeddings, nonlinear estimators, and modern LLM representations are secondary.

## 10. Primary evaluation

Regression:

- MAE;
- relative MAE;
- calibration intercept;
- calibration slope; and
- calibration plots.

Classification:

- PR AUC;
- Brier score;
- calibration intercept and slope; and
- recall/precision at 10% review capacity.

Inference:

- 2,000 company-clustered bootstrap replicates;
- seed 20260725;
- paired contrasts;
- percentile 95% intervals;
- two-sided tests; and
- Holm familywise adjustment across H1–H5.

## 11. Disclosure Drift Index

The DDI is a period-style proxy, not an AI-authorship detector. It will distinguish 2018–2021 from
2022–2023 using transparent, outcome-free language and structure measures. It may not use 2024 text,
financial outcomes, or prediction errors during construction.

Explicit AI terminology is excluded from the primary DDI and modeled separately.

## 12. Rewrite experiment

- historical prompt pilot: maximum 60 passages from 2018–2021;
- confirmatory production sample: 450 distinct 2022–2023 filings;
- 150 passages each from Items 1A, 7, and 9A;
- one passage per filing;
- treatments: Plain-English, Standardized professional, Evidence-first;
- outcome-free sampling;
- deterministic preservation tests;
- blinded human audit;
- minimum 95% factual-preservation pass rate;
- fewer than 400 valid passages makes the analysis exploratory.

## 13. Final-test lock

No 2024 outcome may be viewed until the repository records:

- approved preregistration;
- Stage 2A and Stage 2B specifications;
- code and environment hashes;
- feature and model manifests;
- classification threshold;
- DDI freeze;
- prompt hashes;
- 2024 row-ID hash; and
- completed leakage checklist.

## 14. Prohibited claims

The project may not state or imply:

- verified AI authorship;
- causation solely from the post-2022 timing;
- fraud, misconduct, deception, or reporting failure;
- investment suitability;
- novelty for any individual study component already represented in the literature matrix; or
- factual preservation without passing the frozen validation process.

## 15. Required records created in this branch

- `Docs/preregistration_v0_1.md`
- `Docs/Decisions/decision_002_primary_outcome.md`
- `Docs/Decisions/decision_003_temporal_split.md`
- `Docs/Decisions/decision_004_evaluation_protocol.md`

Decision 001 remains the novelty-boundary record.

## 16. Remaining Milestone 0 work

Before Milestone 0 is complete:

1. Joey reviews and approves or revises Stage 1;
2. every High-threat literature source receives full-paper field completion;
3. Stage 2A implementation details are frozen after the pre-2022 pilot;
4. Stage 2B DDI and rewrite rules are frozen before 2024 outcome access;
5. a final risk and leakage audit is completed;
6. the preregistration is versioned as approved;
7. a Git commit provides a timestamped freeze; and
8. Claude’s first repository-foundation prompt is prepared.

## 17. Current milestone estimate

**Approximately 85% complete after installation of this draft.**

Claude Code remains blocked from research implementation. Repository foundation may begin only after
Stage 1 is approved, and SEC ingestion may not begin until the Milestone 1 engineering specification
is separately approved.

## 18. Methodological references

- TRIPOD+AI, BMJ 2024
- PROBAST+AI, BMJ 2025
- SEC EDGAR API documentation
- Ovadia et al., predictive uncertainty under dataset shift
- Disclosure Drift 61-source literature matrix
