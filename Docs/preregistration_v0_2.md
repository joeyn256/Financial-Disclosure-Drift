# Disclosure Drift

## Stage 1 Preregistration and Definition Freeze — Version 0.2

**Date:** 2026-07-25  
**Status:** Approved by the project owner, subject only to documented Stage 2 implementation freezes.  
**Project:** Disclosure Drift: Temporal Reliability of Financial-Filing Models in the Generative-AI Era

---

## 1. Purpose of this preregistration

This document freezes the research question, target population, outcome logic, temporal design,
confirmatory hypotheses, comparison groups, evaluation metrics, inference rules, rewrite experiment,
and final-test protections before production modeling begins.

This is a **staged preregistration**:

- **Stage 1, this document:** freezes the economic and statistical design.
- **Stage 2A, before any 2022–2024 outcome evaluation:** freezes the exact XBRL concept hierarchy,
  parser rules, feature formulas, estimator implementations, and hyperparameter grids using only the
  pilot and pre-2022 outcomes.
- **Stage 2B, before any 2024 outcome access:** freezes the Disclosure Drift Index, rewrite prompts,
  rewrite provider/model versions, and factual-preservation rules using text-only transition data and
  a historical rewrite pilot.

Any change after its applicable freeze gate must be recorded in `Docs/Decisions/`, assigned a new
preregistration version, and labeled confirmatory or exploratory.

---

## 2. Confirmatory contribution

> Disclosure Drift tests whether models trained only on pre-2022 Form 10-K disclosures lose
> predictive accuracy or calibration when forecasting one-year-ahead, industry-adjusted operating
> deterioration in 2024-era filings; whether any reliability loss is concentrated in style-dependent
> representations; and whether evidence-grounded models are more stable under both observed
> disclosure drift and preregistered, fact-preserving rewrites.

The project does not claim to be the first study of temporal 10-K prediction, future-outcome
prediction from filing narratives, AI-assisted financial reporting, controlled financial-text
rewrites, or evidence-grounded financial NLP.

---

## 3. Intended use

The models are research instruments for studying temporal reliability. They are not intended to:

- make investment recommendations;
- label a company as having used generative AI;
- diagnose fraud, misconduct, deception, or reporting failure;
- replace financial analysis, auditing, or regulatory review; or
- provide a deployable company-risk score.

---

## 4. Unit of analysis and prediction time

The primary unit is a **company–Form 10-K filing observation**.

For target filing `F(i,t)`:

- `i` is the SEC Central Index Key;
- `t` is the fiscal period reported by the original Form 10-K;
- the prediction timestamp is the SEC acceptance timestamp of the original Form 10-K;
- every predictor must have been publicly available by that timestamp;
- the outcome is derived from the next eligible annual fiscal period, `t+1`.

Amended Forms 10-K/A are linked and retained, but they do not replace original filing text or
originally reported facts in the primary analysis.

---

## 5. Data sources

Primary sources:

1. SEC submissions history and accession metadata;
2. original Form 10-K and linked Form 10-K/A filing archives;
3. filing-level inline XBRL and SEC CompanyFacts data;
4. SEC filing metadata, including CIK, form, filing date, acceptance time, fiscal year end, and SIC.

External corpora may be used only for validation or engineering comparison. The project’s point-in-time
source of truth must remain the SEC filing and its associated SEC metadata.

---

## 6. Target population

### 6.1 Primary population

U.S. domestic public operating companies filing an original Form 10-K with acceptance dates from
2010-01-01 through 2024-12-31.

Support filings from 2009 may be collected only to create lagged text and financial features for 2010
targets.

### 6.2 Primary exclusions

Exclude an observation from the common confirmatory cohort when any of the following applies:

1. the target filing is not an original Form 10-K;
2. the issuer is a foreign private issuer primarily reporting through Form 20-F or 40-F;
3. the issuer is a mutual fund, ETF, asset-backed issuer, blank-check company, or shell company;
4. the target filing SIC is between 6000 and 6999, inclusive;
5. no valid SEC SIC is available at the target filing;
6. annual revenue is non-positive for fiscal period `t` or `t+1`;
7. operating income/loss or revenue cannot be reconciled for `t` or `t+1`;
8. the duration of either annual fiscal period is outside 300–430 days;
9. the next eligible fiscal period cannot be matched with a period-end gap of 300–430 days;
10. Item 7 cannot be extracted with at least 250 normalized word tokens;
11. no prior eligible Form 10-K is available for longitudinal features;
12. the filing is identified as a parser failure under the frozen parser-quality rules.

Delisted, bankrupt, acquired, and failed firms remain eligible when the required historical filings
and outcomes exist.

### 6.3 Secondary population

A secondary all-eligible cohort will include firms lacking a prior filing, with explicit missing-history
indicators. Results from this cohort are robustness analyses, not the primary confirmatory result.

### 6.4 Minimum feasibility gates

The project remains confirmatory only if the frozen common cohort contains at least:

- 5,000 training observations from 2010–2021;
- 750 eligible 2024 final-test observations; and
- 75 severe-deterioration events in the 2024 cohort.

If a gate is not met, the project is reclassified as a pilot and the preregistration must be revised
before viewing primary test metrics.

---

## 7. Text scope

### 7.1 Primary text representation

The primary filing-level text representation combines, in source order:

1. Item 1A — Risk Factors, when available;
2. Item 7 — Management’s Discussion and Analysis;
3. Item 9A — Controls and Procedures, when available.

Section markers, headings, list structure, source order, and source offsets must be preserved.

Item 7 is required for the common cohort. Missing Item 1A or Item 9A is represented through explicit
missing-section indicators rather than silently excluding the filing.

### 7.2 Secondary text analyses

Section-specific models for Item 1A, Item 7, and Item 9A are secondary. Item 7A and Item 8 accounting
notes remain deferred until parser feasibility is demonstrated and a separate decision record is
approved.

---

## 8. Temporal design

Cohorts are assigned by the original Form 10-K SEC acceptance date.

| Cohort | Acceptance dates | Permitted use |
|---|---|---|
| Development | 2010-01-01 to 2021-12-31 | Feature development, estimator selection, hyperparameter selection, and outcome-based analysis |
| Transition evaluation | 2022-01-01 to 2023-12-31 | Locked evaluation and mechanism analysis; no predictive-model tuning |
| Final primary test | 2024-01-01 to 2024-12-31 | One untouched confirmatory evaluation |
| Prospective secondary test | 2025-01-01 to 2025-12-31 | Build text/features and freeze predictions now; do not evaluate outcomes before the maturity gate |
| Current monitoring cohort | 2026-01-01 to 2026-12-31 | Text-only drift monitoring, data-quality analysis, and frozen prospective predictions; no one-year outcome claims |

The earlier label **transition validation** is superseded. The 2022–2023 outcomes may not be used to
change predictor definitions, model families, hyperparameters, thresholds, or the primary outcome.

### 8.1 Recency and maturity gates

#### 2025 prospective secondary test

The 2025 cohort may be evaluated only after all of the following hold:

1. the fixed outcome-availability cutoff is **2027-03-31**;
2. at least 90% of the potentially eligible 2025 common cohort has either a valid next-year outcome
   or a documented terminal reason that makes the outcome unavailable;
3. no size quartile or major industry family has follow-up completeness below 80%;
4. the model code, features, thresholds, DDI, and estimator parameters remain identical to the
   pre-2022 freeze;
5. the 2025 prediction file was generated and hashed before outcome linkage; and
6. a separate prospective-evaluation decision record is committed before metrics are opened.

The 2025 analysis is a **secondary confirmatory replication**, not a replacement for the 2024 primary
test.

#### 2026 current monitoring cohort

During 2026 the project may:

- collect and parse accepted 2026 Forms 10-K;
- calculate frozen text, structure, financial, and DDI features available at filing time;
- report outcome-free disclosure-language and data-quality trends;
- generate and hash frozen predictions from the pre-2022 models; and
- document prediction-distribution and covariate-shift diagnostics that do not use future outcomes.

The project may not describe 2026 predictive accuracy, calibration, operating deterioration, or model
decay until one-year outcomes mature. The earliest planned outcome cutoff is **2028-03-31**, followed
by the same coverage and freeze requirements used for 2025.

Neither the 2025 nor 2026 cohort may be used to retrain, recalibrate, or redefine the primary models.

### 8.2 Rolling-origin development folds

Predictive choices must be made from pre-2022 data using these rolling-origin folds:

| Fold | Training filings | Validation filings |
|---|---|---|
| A | 2010–2014 | 2015–2016 |
| B | 2010–2016 | 2017–2018 |
| C | 2010–2018 | 2019 |
| D | 2010–2019 | 2020 |
| E | 2010–2020 | 2021 |

All observations from the same company and acceptance year remain together. No random split may
replace these folds in the confirmatory analysis.

The final frozen models are refit on all eligible 2010–2021 observations and then evaluated without
updating on 2022, 2023, and 2024.

---

## 9. Primary outcome

### 9.1 Operating margin

For company `i` and fiscal period `t`:

`OM(i,t) = OperatingIncomeLoss(i,t) / Revenue(i,t)`

The exact versioned XBRL concept-precedence hierarchy will be frozen in Stage 2A after the pilot.
Custom-company concepts may not enter the primary hierarchy unless they can be mapped and validated
under a documented rule that is applied consistently across all cohorts.

### 9.2 One-year change

`RawDeltaOM(i,t+1) = OM(i,t+1) - OM(i,t)`

### 9.3 Industry adjustment

The primary industry classification is the first two digits of the SEC SIC recorded at the target
filing.

For the calendar year of the `t+1` fiscal-period end:

`AdjDeltaOM(i,t+1) = RawDeltaOM(i,t+1) - median(RawDeltaOM for the same 2-digit SIC and year)`

Rules:

- the industry-year median uses all otherwise eligible outcome observations;
- the target filing’s SIC is used, preventing a later classification change from redefining the peer
  group;
- a 2-digit SIC-year cell must contain at least 10 valid firms;
- if it contains fewer than 10, use the corresponding 1-digit SIC-year median;
- if the fallback cell also contains fewer than 10, exclude the observation from the primary
  industry-adjusted analysis and retain it only for the unadjusted robustness analysis.

### 9.4 Primary regression target

The confirmatory continuous target is `AdjDeltaOM`.

For regression only:

- estimate the 1st and 99th percentile caps from eligible 2010–2021 training outcomes;
- apply those fixed caps to development, transition, and final-test outcomes;
- report the uncapped outcome as a robustness analysis.

No outcome cap may be estimated from 2022 or later observations.

### 9.5 Severe-deterioration classification

The secondary confirmatory label is:

`SevereDeterioration = 1` when uncapped `AdjDeltaOM` is less than or equal to the 10th percentile of
eligible uncapped 2010–2021 `AdjDeltaOM`; otherwise `0`.

The numerical threshold must be calculated once from the frozen development cohort, rounded to six
decimal places, saved in the experiment manifest, and applied unchanged to all later cohorts.

No resampling method such as SMOTE will be used in the primary classification analysis.

### 9.6 Outcome versions

Primary outcomes use facts as first reported in the next original Form 10-K. Amendment-adjusted and
restatement-aware outcomes are secondary robustness analyses.

---

## 10. Predictor families

All primary families use the same common cohort and prediction timestamps.

### B0 — Constant benchmark

Predict the median capped development outcome estimated from the applicable training fold.

### F — Financial-only model

Point-in-time structured predictors may include:

- current and lagged operating margin;
- revenue and operating-income changes;
- operating cash flow;
- total assets and log assets;
- leverage;
- liquidity;
- investment and asset growth;
- current profitability and loss indicators;
- industry indicators;
- fiscal-period and filing-timing controls.

No narrative-derived variable may enter F.

### S — Traditional style-heavy text model

Transparent measures may include:

- Loughran–McDonald tone categories;
- readability;
- section and document length;
- sentence-length distribution;
- lexical diversity;
- numeric density;
- boilerplate share;
- year-over-year similarity;
- industry-peer similarity;
- heading and list density; and
- other frozen surface-style measures.

S may not include structured financial facts other than non-economic controls needed to create valid
comparisons, such as filing year and section-missing indicators.

### FS — Financial plus traditional style model

Union of F and S.

### E — Evidence-grounded model

F plus source-linked textual evidence that is designed to represent disclosed economic facts rather
than surface style. Candidate classes include:

- numeric claims linked to filing offsets;
- newly introduced or removed material facts;
- named risk categories and their changes;
- claim specificity;
- internal-control statements;
- accounting-policy changes;
- segment, geography, concentration, and operating-risk changes;
- numeric-text inconsistencies;
- contradictions between narrative claims and reported financial direction.

Every evidence-grounded feature must retain source lineage and pass an ablation against F alone.

### Secondary model families

- TF-IDF lexical model;
- a financial-domain representation model released before 2022, subject to a documented cutoff audit;
- nonlinear estimators applied to the frozen tabular feature families; and
- modern LLM-derived representations, which are exploratory because of possible training-data
  contamination.

---

## 11. Model-building protocol

### 11.1 Primary estimator framework

The primary regression estimator for F, S, FS, and E will be a regularized linear model using the same
training and selection protocol across families. The exact implementation and hyperparameter grid
will be frozen in Stage 2A using only rolling-origin development performance.

The primary classification estimator will be regularized logistic regression using the same feature
families and temporal protocol.

A secondary nonlinear estimator may be reported, but it cannot replace the primary estimator after
later-period performance is observed.

### 11.2 Hyperparameter selection

For each candidate configuration:

1. replay preprocessing, imputation, scaling, and model fitting separately inside every rolling fold;
2. compute relative MAE in each validation fold;
3. rank configurations by the median relative MAE across folds;
4. break ties using lower raw MAE, then fewer effective parameters, then the simpler specification.

No 2022–2024 outcome may enter hyperparameter selection.

### 11.3 Preprocessing

- continuous predictor imputation: training-fold median;
- missingness indicators: required when a predictor is imputed;
- scaling: training-fold median and interquartile range;
- categorical levels: learned from the training fold, with an explicit unseen category;
- feature removal: predictors with more than 40% missingness in the development cohort are excluded
  from the primary model;
- vocabulary, document-frequency cutoffs, similarity reference sets, and all other transforms are fit
  on training data only;
- no target encoding;
- deterministic seeds and versioned manifests are required.

---

## 12. Disclosure Drift Index

The Disclosure Drift Index is an **AI-era language proxy**, not an AI-authorship detector.

### 12.1 Primary construction

A regularized logistic model will distinguish:

- reference text: 2018–2021 filings;
- transition text: 2022–2023 filings.

Only transparent, outcome-free style components may enter the index. The initial frozen component
classes are:

1. sentence-length level and dispersion;
2. lexical diversity and vocabulary concentration;
3. readability;
4. tone, uncertainty, litigious, and constraining language;
5. numeric-token density;
6. named-entity and firm-specific term density;
7. section length, heading density, and list density;
8. year-over-year similarity;
9. peer similarity and boilerplate share; and
10. pre-2022 language-model perplexity, only if the model cutoff is defensible.

Explicit AI product and AI-risk terms will be removed from the primary DDI feature calculation and
reported separately as controls.

The DDI model may use 2022–2023 text labels indicating period membership, but it may not use financial
outcomes, model errors, or 2024 text when selecting components or coefficients. Companies must be
grouped during DDI cross-validation to reduce issuer memorization.

The frozen model is then applied once to 2024 filings.

### 12.2 Robustness index

An equal-weight composite of training-standardized transparent components will be reported as a
secondary alternative.

### 12.3 Interpretation

A higher DDI indicates greater resemblance to the transition-period style pattern under the frozen
feature set. It does not establish AI use or causation.

---

## 13. Confirmatory hypotheses and test statistics

Define:

- `rMAE(m,p) = MAE of model m in period p / MAE of B0 in period p`;
- `Hist(m)` as pooled rolling-origin out-of-fold performance for 2015–2021;
- `Decay(m) = rMAE(m,2024) - rMAE(m,Hist)`;
- `CalDecay(m) = abs(1 - calibration_slope(m,2024)) - abs(1 - calibration_slope(m,Hist))`;
- `RewriteSensitivity(m)` as defined in Section 16.

### H1 — Temporal reliability

`Decay(S) > 0`

The traditional style-heavy model becomes less reliable in 2024 than in historical out-of-fold
evaluation.

### H2 — Differential style decay

`Decay(S) - Decay(F) > 0`

The style-heavy model deteriorates more than the financial-only model.

### H3 — Drift concentration

In the 2024 cohort, the coefficient on standardized DDI is positive in a regression of absolute
style-model prediction error on DDI, controlling for log assets, filing length, explicit AI-term
discussion, and 2-digit SIC indicators.

### H4 — Rewrite sensitivity

`RewriteSensitivity(S) - RewriteSensitivity(E) > 0`

Traditional style features are more sensitive than evidence-grounded features to fact-preserving
rewrites.

### H5 — Evidence-grounded temporal robustness

Both of the following must hold:

1. `Decay(E) - Decay(S) < 0`; and
2. `CalDecay(E) - CalDecay(S) < 0`.

H5 is supported only when both components satisfy the applicable multiplicity-adjusted criterion.

All directional hypotheses will nevertheless be evaluated with two-sided confidence intervals and
two-sided p-values.

---

## 14. Performance metrics

### 14.1 Continuous primary outcome

Primary:

- mean absolute error;
- relative MAE against B0;
- continuous calibration intercept;
- continuous calibration slope from `observed = intercept + slope × predicted`; and
- calibration plots by prediction decile with a smooth curve.

Secondary:

- root mean squared error;
- median absolute error;
- R-squared;
- Spearman correlation;
- mean prediction bias;
- raw uncapped-outcome performance; and
- top and bottom prediction-decile outcome separation.

### 14.2 Severe-deterioration classification

Primary secondary-task metrics:

- precision-recall AUC;
- Brier score;
- calibration intercept;
- calibration slope; and
- recall and precision at a fixed 10% review capacity.

Additional:

- ROC AUC;
- expected calibration error using 10 equal-frequency bins;
- confusion matrix at the frozen development threshold; and
- event prevalence by cohort.

Classification thresholds may not be selected from transition or final-test prevalence.

---

## 15. Statistical inference

### 15.1 Bootstrap

Use 2,000 nonparametric bootstrap replicates with seed `20260725`.

- resample companies with replacement;
- retain all observations for a sampled company;
- use identical resamples for paired model comparisons;
- report percentile 95% confidence intervals;
- report both point estimates and confidence intervals for every confirmatory metric.

For a one-year cross-section with one filing per company, company resampling reduces to ordinary
observation-level resampling.

### 15.2 H3 regression

The primary H3 regression uses the 2024 cohort with heteroskedasticity-robust HC3 standard errors.
A 2-digit-SIC cluster bootstrap is a robustness analysis.

### 15.3 Multiple testing

The five confirmatory hypothesis families H1–H5 use Holm adjustment with familywise alpha `0.05`.

- report unadjusted and adjusted p-values;
- H5 uses an intersection rule: both component tests must satisfy the H5 adjusted threshold;
- all other analyses are secondary or exploratory unless a later preregistered decision states
  otherwise.

No result will be described as confirmatory solely because its unadjusted p-value is below 0.05.

---

## 16. Controlled fact-preserving rewrite benchmark

### 16.1 Prompt-development pilot

A maximum of 60 passages from 2018–2021 may be used to develop prompts and validation rules.
Pilot passages are excluded from the confirmatory rewrite sample.

### 16.2 Production sample

Select one passage from each of 450 distinct 2022–2023 filings:

- 150 Item 1A passages;
- 150 Item 7 passages;
- 150 Item 9A passages.

Sampling may be stratified by filing year, 2-digit SIC, size quartile, and DDI tertile. Outcome values
and model errors may not be used for sampling.

Each passage should contain approximately 250–500 words, subject to sentence-boundary preservation.

### 16.3 Confirmatory treatments

1. **Plain-English:** improve clarity and sentence structure without changing information.
2. **Standardized professional:** rewrite into polished, standardized corporate prose without changing
   information.
3. **Evidence-first:** foreground existing numbers, named facts, and source-specific evidence without
   adding information.

Confidence-enhancing, uncertainty-reducing, persuasive, or risk-minimizing treatments are exploratory
because they create a greater risk of altering material meaning.

### 16.4 Required preservation

Every accepted rewrite must preserve:

- every number, percentage, date, currency value, and direction of change;
- company, product, segment, geography, and counterparty names;
- negation;
- causal direction;
- uncertainty and material qualifications;
- disclosed risks and events;
- accounting claims; and
- the absence of facts not present in the original.

### 16.5 Validation

Before model scores are calculated:

- deterministic number, date, percentage, and named-entity checks must pass;
- automated contradiction and omission checks must pass under frozen rules;
- reviewers must be blinded to downstream model-score changes;
- manually audit at least 75 rewrites or 15% of accepted rewrites, whichever is larger;
- the audited factual-preservation pass rate must be at least 95%;
- no treatment may have an audited failure rate above 10%.

If fewer than 400 valid production passages remain, the rewrite study is labeled exploratory.

### 16.6 Prediction-level experiment

Replace only the selected passage in its original filing section, recompute the affected text and
evidence features, and score the already frozen pre-2022 models.

Financial-only predictions must remain unchanged; any movement in F is a pipeline failure.

For filing `j`, model `m`, and treatment `k`:

`Shift(j,m,k) = abs(pred_rewrite - pred_original) / IQR(training outcome)`

`RewriteSensitivity(j,m)` is the median `Shift` across the three confirmatory treatments.

The model-level statistic is the median across filings. Paired company bootstrap comparisons are used
for H4.

---

## 17. Subgroup and error analyses

These analyses are secondary unless separately preregistered:

- year;
- 2-digit SIC;
- company-size quartile;
- profitable versus loss-making baseline;
- high versus low DDI;
- complete versus missing optional sections;
- new versus returning issuer;
- original versus amendment-aware outcomes;
- technology-company exclusion;
- firms explicitly discussing AI;
- parser confidence;
- extreme versus ordinary outcome observations; and
- false-positive and false-negative case studies.

Every subgroup must report sample size, event count where relevant, performance estimate, and
confidence interval. Small groups will be combined or suppressed under a frozen minimum-size rule.

---

## 18. Falsification and robustness analyses

Required:

1. placebo cutoff dates before 2022;
2. matched pre/post company samples;
3. alternative 1-digit and 2-digit SIC adjustments;
4. unadjusted operating-margin change;
5. uncapped outcome;
6. removal of technology firms;
7. removal of explicit AI-risk or AI-product discussion;
8. original-only versus amendment-aware outcomes;
9. fixed-vocabulary versus updated-vocabulary measures;
10. identity-masked text;
11. negative-control formatting changes that do not alter prose;
12. equal-weight DDI;
13. section-specific results; and
14. nonlinear estimator variants.

Robustness analyses may qualify or weaken a conclusion but may not replace the preregistered primary
result because they appear more favorable.

---

## 19. Primary and prospective test locks

The 2024 outcomes are not permitted for model or prompt development. The same frozen model and
feature definitions apply to 2025 and 2026. Any 2025 or 2026 predictions intended for later
evaluation must be generated, timestamped, and hashed before the corresponding outcome table is
linked.

Before the first 2024 outcome evaluation, the repository must contain:

1. an approved Stage 1 preregistration;
2. Stage 2A and Stage 2B freeze records;
3. the frozen code commit hash;
4. environment lock and package versions;
5. feature-schema and model-manifest hashes;
6. the severe-deterioration threshold;
7. DDI coefficients and component definitions;
8. rewrite prompt hashes;
9. a hash of the 2024 row-identification table; and
10. a completed leakage checklist.

The 2024 feature table may be built without outcome columns. The outcome table must remain separate
until the one-time evaluation command is run.

If metrics are viewed and any model, feature, threshold, or prompt is then changed, all subsequent
2024 results are exploratory unless an independent untouched cohort is designated in a new protocol.

---

## 20. Missing data and parser failures

Missingness must be reported by year, industry, size, section, and cohort.

- predictor imputation is training-only;
- outcome values are never imputed;
- parser failures remain in an audit table;
- failed filings are never silently dropped;
- differential failure rates across cohorts must be measured;
- an exclusion waterfall is required for every primary analysis.

---

## 21. Confirmatory interpretation rules

A confirmatory claim requires:

1. the preregistered effect direction;
2. the Holm-adjusted criterion;
3. a confidence interval consistent with the claim;
4. no failed data-quality or leakage gate;
5. no materially contradictory robustness evidence left unexplained; and
6. language that describes temporal association rather than proven GenAI causation.

Negative, null, and hypothesis-contradicting results remain part of the final paper and application.

---

## 22. Stop and redesign conditions

Stop before final-test access when:

1. a direct study is found that duplicates the full combined contribution;
2. the primary operating-margin outcome fails pilot reconciliation;
3. common-cohort feasibility gates are not met;
4. parser error is materially related to filing period or firm characteristics and cannot be measured
   or controlled;
5. evidence-grounded features cannot retain source lineage;
6. final-test outcomes are accessed before the freeze package exists;
7. rewrite factual-preservation gates fail; or
8. the primary estimator cannot produce reproducible predictions from a clean environment.

---

## 23. Stage 2A items still to freeze from the pilot

These are implementation details, not open research choices:

- exact XBRL concept-precedence hierarchy;
- exact annual-fact context resolution;
- parser boundary thresholds;
- minimum parser confidence;
- exact feature formulas;
- exact estimator package and version;
- hyperparameter grids;
- text tokenization and normalization;
- minimum subgroup reporting size; and
- exact publication-table schema.

They must be decided using the pilot and pre-2022 data only.

---

## 24. Stage 2B items still to freeze

Before 2024 outcome access:

- DDI component implementations and coefficients;
- DDI model and version;
- rewrite provider and model versions;
- system and user prompts;
- deterministic settings where supported;
- contradiction and omission checks;
- human-audit form; and
- accepted-rewrite exclusion reasons.

---

## 25. Deviations

Every deviation must record:

- date;
- decision owner;
- affected hypothesis or analysis;
- reason;
- whether any transition or final-test metric had been viewed;
- expected direction of impact;
- new version number; and
- whether the changed result is confirmatory or exploratory.

Silently changing a definition is prohibited.

---

## 26. Reporting framework

The final study will adapt the transparency principles of TRIPOD+AI and the risk-of-bias domains of
PROBAST+AI to a company-level financial prediction setting. At minimum it will report development and
evaluation data separately, all model-building steps, clustering, thresholds, calibration,
confidence intervals, error analysis, subgroup heterogeneity, code availability, data lineage, and
deviations.

---

## 27. References used to design this protocol

- Collins GS, Moons KGM, Dhiman P, et al. TRIPOD+AI statement. BMJ. 2024;385:e078378.
  https://www.bmj.com/content/385/bmj-2023-078378
- Moons KGM, Damen J, Kaul T, et al. PROBAST+AI. BMJ. 2025;388:e082505.
  https://www.bmj.com/content/388/bmj-2024-082505
- U.S. Securities and Exchange Commission. EDGAR Application Programming Interfaces.
  https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Ovadia Y, Fertig E, Ren J, et al. Can You Trust Your Model’s Uncertainty? NeurIPS. 2019.
  https://arxiv.org/abs/1906.02530
- Disclosure Drift cumulative 61-source literature matrix and Decision 001.

---

## 28. Approval

**Project owner:** Joey Nihill  
**Approval status:** Approved by project owner  
**Approval date:** 2026-07-25  
**Approved version:** Stage 1 v0.2  
**Repository commit:** Pending local Git initialization and commit
