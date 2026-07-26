# Decision 004 — Evaluation, Inference, and Rewrite Protocol

**Date:** 2026-07-25  
**Status:** Proposed freeze pending project-owner approval

## Primary comparison families

- B0: constant development-median benchmark
- F: financial-only
- S: traditional style-heavy text
- FS: financial plus traditional style
- E: financial plus evidence-grounded text

TF-IDF, pre-2022 embeddings, modern LLM representations, and nonlinear estimators are secondary.

## Primary regression evaluation

- MAE
- relative MAE versus B0
- calibration intercept
- calibration slope
- decile calibration plot

## Secondary classification evaluation

- PR AUC
- Brier score
- calibration intercept and slope
- recall and precision at 10% review capacity
- ROC AUC and 10-bin equal-frequency ECE

## Temporal-decay statistic

`Decay(m) = rMAE(m,2024) - rMAE(m,historical out-of-fold)`

The primary historical reference consists of pooled rolling-origin predictions from 2015–2021.

## Inference

- 2,000 company-clustered bootstrap replicates
- fixed seed 20260725
- paired resamples for model contrasts
- percentile 95% confidence intervals
- two-sided tests
- Holm adjustment across H1–H5 at familywise alpha 0.05
- HC3 standard errors for the primary 2024 DDI-error regression

## Confirmatory hypotheses

1. `Decay(S) > 0`
2. `Decay(S) > Decay(F)`
3. DDI positively predicts absolute S-model error in 2024 after frozen controls
4. rewrite sensitivity of S exceeds E
5. E has lower rMAE decay and lower calibration-slope deterioration than S

## Rewrite protocol

- prompt pilot: at most 60 passages from 2018–2021, excluded from confirmation;
- production: 450 distinct 2022–2023 filings, one passage per filing;
- 150 passages each from Items 1A, 7, and 9A;
- treatments: Plain-English, Standardized professional, Evidence-first;
- no outcome-based sampling;
- deterministic preservation checks before scoring;
- human audit of at least 75 or 15%, whichever is larger;
- at least 95% audited factual-preservation pass rate;
- fewer than 400 valid passages makes the rewrite analysis exploratory.

For each accepted filing and treatment:

`Shift = abs(rewrite prediction - original prediction) / IQR(development outcome)`

The filing-level sensitivity is the median Shift across the three treatments.

## Negative control

F predictions must not change after text rewriting. Any change is a pipeline defect.

## Reason

Accuracy alone is insufficient under temporal shift. Calibration, paired model comparisons, clustered
uncertainty, and a blinded fact-preservation process are needed to distinguish real reliability loss
from cohort difficulty or rewrite errors.
