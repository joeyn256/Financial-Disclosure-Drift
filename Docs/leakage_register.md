# Disclosure Drift — Leakage and Validity Register

## Version 0.2

**Date:** 2026-07-25

| ID | Risk | Example failure | Required prevention | Required test |
|---|---|---|---|---|
| L01 | Future financial facts | A later 10-K/A or CompanyFacts update supplies information unavailable on the original filing date. | Store filing/acceptance dates and use strict as-of joins. | Sampled lineage audit from source filing to model row. |
| L02 | Amendment replacement | The latest amendment silently replaces the original narrative. | Keep every accession separately and explicitly link amendments. | Original-versus-amended regression fixture. |
| L03 | Outcome contamination in features | A later-year filing or later event text enters the predictor window. | Freeze the feature snapshot at the target filing acceptance time. | Maximum feature timestamp must not exceed cutoff. |
| L04 | Survivorship bias | Universe is drawn from current S&P 500 or active tickers. | Build from historical SEC submissions; retain delisted firms. | Reconcile active and inactive issuers by year. |
| L05 | Fiscal-year mismatch | Filing year is treated as the fiscal year without checking period end. | Store filing date, fiscal period end, fiscal year, and form separately. | Year-boundary and non-calendar-filer tests. |
| L06 | Language-model look-ahead | A modern embedding model was trained on 2024 filings or later outcomes. | Primary representations must have defensible cutoffs or frozen vocabularies; modern LLM features are secondary. | Model-card cutoff audit. |
| L07 | Prompt overfitting | Rewrite prompts are changed after seeing which treatment produces the preferred result. | Freeze prompts and validation rules before final-test rewrites. | Hash and version every prompt. |
| L08 | Threshold leakage | Severe deterioration threshold is selected using 2024 event prevalence. | Select the rule from training data only. | Threshold provenance assertion. |
| L09 | Identity memorization | Company name or recurring boilerplate lets the model memorize issuer outcomes. | Report identity-masked and new/returning-firm results. | Identity-ablation evaluation. |
| L10 | Parser-selection leakage | Later filings with difficult HTML are dropped more often, changing cohort composition. | Track every failure and report coverage by year, industry, size, and format. | Differential-failure dashboard. |
| L11 | Outcome censoring | 2025 firms without complete future outcomes are treated as non-events. | Use a fixed availability cutoff and keep 2025 provisional. | Censoring and follow-up completeness report. |
| L12 | Detector-label leakage | AI-likeness score is treated as a true label and optimized against. | Use proxy language only; do not train a definitive authorship classifier. | Claims and terminology review. |
| L13 | Peer leakage | Industry medians or similarity pools use firms whose facts were filed later than the target cutoff. | Construct peer features point-in-time. | Peer member timestamp test. |
| L14 | Normalization leakage | Winsorization, scaling, vocabulary, or imputation uses transition/final-test distributions. | Fit every transformation on training data only. | Serialized transform provenance test. |
| L15 | Model-selection leakage | Final-test performance influences feature families or hyperparameters. | Lock the 2024 test table and evaluate once after specification freeze. | Access log and experiment manifest. |
| L16 | Rewrite-outcome leakage | Rewrite quality review is influenced by downstream model-score movement. | Review factual preservation before calculating model outputs. | Blinded rewrite review protocol. |
| L17 | Structural information loss | Extraction discards risk ordering, headings, or source offsets. | Preserve document structure alongside clean text. | Round-trip source-offset and order tests. |
| L18 | External dataset mismatch | A third-party SEC corpus has undocumented updates or restatements. | Treat external corpora as validation sources, not the point-in-time source of truth. | Cross-corpus discrepancy report. |
| L19 | Pilot-use look-ahead | The M2.3 engineering pilot's eventful/inactive-history stratification (current-state knowledge that post-dates every pilot filing) is used to inform a feature, vocabulary, threshold, transform, model family, model selection, or outcome/DDI construction choice. | Treat the pilot and its stratification as engineering-coverage only; never let pilot composition or membership inform any research artifact governed by the preregistration. | Provenance check that no feature/threshold/model/outcome artifact cites pilot membership or stratification as a basis. |
