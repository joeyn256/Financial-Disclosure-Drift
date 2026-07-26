# Disclosure Drift

## Milestone 0 Research Charter and Novelty Audit — Version 0.1

**Date:** 2026-07-25  
**Status:** Draft for formal literature-matrix expansion and preregistration-style review

## 1. Working title

**Disclosure Drift: Temporal Reliability of Financial-Filing Models in the Generative-AI Era**

## 2. Novelty verdict

**Proceed, but narrow the claim.**

The project should not claim novelty in any of the following areas by themselves:

- detecting possible generative-AI writing in financial reports;
- measuring post-ChatGPT changes in disclosure tone, readability, or style;
- using LLMs to create counterfactual financial narratives;
- showing temporal distribution shift in financial NLP generally; or
- studying investor reactions to AI-modified disclosures.

Recent work already overlaps with each of those components.

The most defensible contribution is the combined reliability question:

> Do models trained on pre-2022 Form 10-K disclosures lose predictive accuracy or calibration when applied to later filings, is any deterioration concentrated in style-dependent textual features, and are evidence-grounded models more stable under both observed disclosure drift and controlled fact-preserving rewrites?

No directly matching study was identified in the first-pass search. This remains a provisional novelty conclusion until the 50–75-source literature matrix and citation-chaining review are complete.

## 3. Closest competing research identified so far

### Direct overlap

1. **Blankespoor, deHaan, and Li — “Generative AI in Financial Reporting”**  
   Studies generative-AI use across risk factors, MD&A, earnings-call prepared remarks, earnings press releases, and IPO disclosures, including effects on report characteristics.  
   Source: https://doi.org/10.1111/1475-679x.70050

2. **Perlin, Foguesatto, Galanos, and Affonso — “The Use of AI in 10-K Filings”**  
   Uses an AI-text detector and FinBERT to examine AI probability and sentiment across S&P 500 filing sections from 2018–2024.  
   Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6108946

3. **Plate, Voshaar, and Zimmermann — “Investor Reactions to Generative AI Usage in MD&A Disclosures”**  
   Examines investor reactions to generative-AI-created or modified MD&A disclosure.  
   Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5068116

4. **Matera — “Corporate Earnings Calls and Analyst Beliefs”**  
   Uses LLM-generated counterfactual earnings-call narratives that vary presentation while holding quantitative content fixed.  
   Source: https://arxiv.org/abs/2511.15214

5. **Chen and Wang — “More Than Human: The Capital-Market Effects of AI-Generated Corporate Disclosure”**  
   Examines the use and capital-market consequences of disclosures that are at least partially AI written.  
   Source: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5959496

### Adjacent methodological overlap

6. **Guo, Hu, and Yang — “Predict the Future from the Past? On the Temporal Data Distribution Shift in Financial Sentiment Classifications”**  
   Documents temporal performance degradation in financial sentiment models, using StockTwits rather than corporate filings and future operating outcomes.  
   Source: https://arxiv.org/abs/2310.12620

7. **Kim, Muhn, and Nikolaev — “Bloated Disclosures: Can ChatGPT Help Investors Process Information?”**  
   Studies generative-AI summarization of corporate disclosures and the information content of summaries.  
   Source: https://arxiv.org/abs/2306.10224

## 4. Frozen primary research question — Version 0.1

> When models are trained only on pre-2022 Form 10-K disclosures, do their out-of-time predictions of future operating deterioration become less accurate or less well calibrated on later filings, and are evidence-grounded models more temporally and stylistically robust than models based mainly on tone, readability, similarity, or writing style?

## 5. Secondary research questions

1. Which observable disclosure characteristics changed most after 2022?
2. Is predictive deterioration associated with the degree of disclosure drift?
3. Do fact-preserving rewrites materially change traditional text features and model predictions?
4. Are model explanations less stable after temporal or stylistic shift?
5. Can financial facts, numeric evidence, and evidence-linked sentences reduce temporal and rewrite sensitivity?

## 6. Initial hypotheses

### H1 — Temporal reliability

Models trained on 2010–2021 filings will exhibit worse out-of-time performance on the GenAI-era test cohort than on pre-GenAI historical holdouts.

### H2 — Style dependence

The deterioration will be larger for models based on tone, readability, boilerplate, lexical similarity, TF-IDF, or generic embeddings than for financial-only models.

### H3 — Drift concentration

Within the later filing cohorts, higher Disclosure Drift Index values will be associated with larger prediction errors or miscalibration for style-dependent models.

### H4 — Rewrite sensitivity

Fact-preserving stylistic rewrites will change the outputs of style-dependent models more than the outputs of financial-only or evidence-grounded models.

### H5 — Evidence-grounded defense

Models combining point-in-time financial facts with evidence-linked textual features will show lower temporal decay and lower rewrite sensitivity than traditional textual baselines.

These are directional hypotheses. Negative or contradictory findings must be retained and reported.

## 7. Initial company universe

### Include

- U.S. domestic public operating companies;
- Form 10-K and explicitly linked Form 10-K/A filings;
- filings submitted from 2010 onward;
- companies with sufficient point-in-time financial facts and at least two consecutive fiscal years for the primary outcome;
- delisted and failed companies when their historical filings remain available.

### Exclude from the primary sample

- mutual funds and ETFs;
- asset-backed issuers;
- shell companies and blank-check companies where identifiable;
- foreign private issuers primarily filing Form 20-F or Form 40-F;
- financial institutions for which operating margin is not economically comparable;
- filings without reliable section extraction or fiscal-period alignment.

Financial institutions may become a separately designed robustness sample with an outcome suitable for banks and insurers.

## 8. Initial text scope

### Primary sections

- Item 1A — Risk Factors
- Item 7 — Management’s Discussion and Analysis
- Item 9A — Controls and Procedures

### Deferred until parser feasibility is demonstrated

- Item 7A — Quantitative and Qualitative Disclosures About Market Risk
- accounting-policy notes within Item 8
- other footnote-level narrative disclosures

## 9. Time design

### Primary research cohorts

| Cohort | Filing dates | Role |
|---|---:|---|
| Historical training | 2010–2021 | Train pre-GenAI-era models |
| Transition validation | 2022–2023 | Tune specifications and measure structural transition |
| Final primary test | 2024 | Untouched out-of-time test with more complete one-year-ahead outcomes |
| Provisional extension | 2025 | Locked monitoring cohort; primary claims deferred until outcome coverage is sufficiently complete |

The 2025 cohort must not be treated as a fully observed one-year-ahead test merely because the filings themselves are available. Outcome censoring and fiscal-year timing must be reported explicitly.

## 10. Primary outcome — Version 0.1

For company *i* in fiscal year *t*:

**Operating margin**

`OM_it = OperatingIncomeLoss_it / Revenue_it`

**One-year change**

`DeltaOM_i,t+1 = OM_i,t+1 - OM_i,t`

**Industry-adjusted change**

`AdjDeltaOM_i,t+1 = DeltaOM_i,t+1 - median(DeltaOM_industry,t+1)`

The initial industry definition will use a documented SIC-based industry mapping. The exact mapping and minimum industry-year cell size will be frozen using training data only.

### Primary modeling task

Predict continuous `AdjDeltaOM_i,t+1`.

### Primary performance metric

Mean absolute error on the untouched out-of-time test set, with block-bootstrap confidence intervals clustered at the company level.

### Secondary classification task

Predict severe operating deterioration. The numerical threshold will be chosen from the training cohort only after examining event prevalence and will be frozen before the transition and final-test analyses.

Secondary classification metrics will include precision-recall AUC, Brier score, calibration slope, calibration intercept, and recall at a fixed review capacity.

## 11. Required comparison groups

1. Financial variables only
2. Traditional dictionary and readability measures
3. TF-IDF text model
4. Financial-domain embedding model
5. Financial plus traditional text model
6. Evidence-grounded model

All primary comparisons must use identical temporal splits and outcome definitions.

## 12. Prohibited claims

The project must not state or imply that:

- a specific company definitely used generative AI;
- a high AI-likeness or drift score proves AI authorship;
- post-2022 language changes were caused solely by generative AI;
- a model score proves fraud, misconduct, deception, or reporting failure;
- observed pre/post differences are causal without a defensible identification strategy;
- the project is the first study of AI-assisted corporate reporting;
- an LLM-generated rewrite is fact preserving without automated and human validation.

## 13. Leakage register — Version 0.1

| ID | Leakage or validity risk | Initial control |
|---|---|---|
| L01 | Financial facts filed after the prediction date | Store fact filing dates and enforce as-of joins |
| L02 | Later 10-K/A text entering original-filing features | Keep original and amendment versions separate |
| L03 | Outcome information mentioned in later filings | Build outcomes only after feature snapshots are frozen |
| L04 | Survivorship bias from current index membership | Construct universe from historical SEC submissions, not a current constituent list |
| L05 | Fiscal-year and filing-year mismatch | Store filing date, period end, fiscal year, and acceptance timestamp separately |
| L06 | Pretrained-model look-ahead contamination | Prefer models released before the relevant cutoff for primary representation tests; isolate modern-LLM analyses as secondary |
| L07 | Prompt tuning after seeing final results | Freeze rewrite prompts and exclusions before final test |
| L08 | Threshold selection on final-test prevalence | Choose classification thresholds using training data only |
| L09 | Company-specific memorization or identity leakage | Report both repeated-firm and new-/returning-firm subgroup performance |
| L10 | Parser failures correlated with year or company type | Maintain a failure queue and report extraction coverage by year, industry, and filer size |
| L11 | Non-random missing future outcomes | Use a fixed outcome-availability cutoff and report censoring |
| L12 | Using detector scores as ground truth | Treat all AI-likeness measures as noisy proxies and run detector sensitivity tests |

## 14. Falsification and robustness requirements

- placebo cutoff dates before 2022;
- matched pre- and post-period company samples;
- models trained on rolling historical windows;
- alternative industry definitions;
- alternative operating-deterioration definitions;
- removal of technology companies;
- removal of firms explicitly discussing AI as a business risk or product;
- original filing only versus amendment-aware analysis;
- fixed-vocabulary versus updated-vocabulary text models;
- low-drift versus high-drift comparisons;
- negative-control rewrites that change formatting but not prose;
- human-edited rewrites where feasible.

## 15. Pilot requirement before scale

The first end-to-end pilot should use approximately 24 companies:

- 6 industries;
- 4 companies per industry;
- a mix of large, mid-size, and small filers;
- profitable and deteriorating firms;
- original and amended filings;
- older HTML and inline-XBRL filings;
- filings from both pre-2022 and later cohorts.

The pilot must demonstrate:

1. correct filing metadata;
2. reliable Item 1A, Item 7, and Item 9A extraction;
3. point-in-time XBRL alignment;
4. reproducible operating-margin outcomes;
5. at least one complete company-level lineage trace from SEC source to model row.

## 16. Milestone 0 remaining work

Milestone 0 is not complete until the following are delivered:

- a 50–75-source literature matrix;
- a reproducible search log;
- forward and backward citation chaining for the closest competitors;
- final contribution statement;
- formal research-risk register;
- finalized outcome definition;
- finalized universe definition;
- preregistration-style analysis plan;
- decision record explaining why 2024 is the primary final-test cohort and 2025 is provisional.

## 17. Rules for Claude Code

Claude Code should not begin implementation yet.

Its first assignment will remain repository foundation only, and only after Milestone 0 definitions have been reviewed and frozen.

## 18. Official data and governance references

- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC fair-access guidance: https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- SEC Form 10-K: https://www.sec.gov/files/form10-k.pdf
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile: https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence
