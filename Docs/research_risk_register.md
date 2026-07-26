# Disclosure Drift — Research Risk Register

## Version 0.2

**Date:** 2026-07-25  
**Status:** Updated after Literature Batch 02

| ID | Category | Risk | Probability | Impact | Required control | Gate |
|---|---|---|---|---|---|---|
| N01 | Novelty | Harrington et al. (2026) already studies temporal drift in a full-text 10-K prediction task. | High | High | Prohibit any “first temporal 10-K drift study” claim. Distinguish outcome, era, calibration, rewrites, and evidence grounding. | Charter v0.3 |
| N02 | Novelty | Grundy and Petry (2025) already construct operating and financing risk measures from 10-K text. | High | High | Do not claim novelty for extracting operating risk. Center the contribution on later-period reliability and calibration of competing model families. | Preregistration |
| N03 | Novelty | Zhang et al. (2026) already combines one-year bankruptcy outcomes, interpretable 10-K text, accounting baselines, and out-of-time testing. | High | High | Distinguish the continuous operating-margin outcome, GenAI-era design, calibration, and controlled rewrites. | Preregistration |
| N04 | Novelty | Lin (2026) frames a recent study as an audit of predictive information in SEC 10-K text. | High | Medium | Do not claim to be the first predictive audit; document differences in scope and methodology after full-paper review. | Full-paper audit |
| N05 | Novelty | Gupta et al. (2024), Bogachek et al. (2026), and Kim et al. (2024) already predict fundamentals or financial outcomes from filing narratives. | High | High | Avoid broad “first future-fundamentals prediction” claims. | All outputs |
| N06 | Novelty | The 2026 literature is moving quickly and could further narrow the contribution. | High | High | Refresh searches at every major milestone and immediately before publication. | Every milestone |
| D01 | Data | 2025 filings do not yet have uniformly complete one-year-ahead outcomes. | High | High | Keep 2024 as the primary untouched test and 2025 as a locked provisional extension. | Outcome freeze |
| D02 | Data | Parser quality may vary systematically by filing year, filer size, HTML format, and inline-XBRL adoption. | Medium | High | Stratified manual audit, failure queue, parser fixtures, and coverage reporting by cohort. | Milestone 3 |
| D03 | Data | XBRL concept selection may make operating margins incomparable across firms. | Medium | High | Versioned concept hierarchy, reconciliation samples, unit checks, and sector exclusions. | Milestone 4 |
| D04 | Data | Current-index sampling would omit delisted and failed firms. | Medium | High | Build the universe from historical SEC submissions rather than current constituents. | Milestone 2 |
| D05 | Data | Risk-factor ordering, section structure, and filing-format changes may contain information independent of prose. | High | Medium | Preserve source order, headings, offsets, and section structure; include structural controls. | Milestone 3 |
| L01 | Leakage | Later amendments or restated facts may overwrite the information available at the original prediction date. | High | High | Preserve original/amended versions and enforce as-of filing joins. | Milestones 2–4 |
| L02 | Leakage | Modern pretrained models may have memorized evaluation filings or later outcomes. | High | High | Use pre-cutoff models or frozen-vocabulary methods for primary tests; label modern-model analyses secondary. | Milestone 6 |
| L03 | Leakage | Company identity, repeated firms, or issuer-specific memorization may inflate performance. | Medium | High | Report repeated-firm, returning-firm, and new-firm subgroup performance; add identity-removal checks. | Milestone 9 |
| M01 | Measurement | AI-detector scores are unstable, biased, and vulnerable to editing. | High | High | Treat all detector outputs as noisy proxies; use multiple proxy families and never infer verified authorship. | Milestone 7 |
| M02 | Measurement | Controlled rewrites may alter numbers, qualifications, causal claims, or material risk content. | Medium | High | Automated number/entity/negation checks, human audit, frozen prompts, and transparent exclusions. | Milestone 8 |
| M03 | Measurement | The Disclosure Drift Index may capture ordinary secular evolution, AI business exposure, or industry composition. | High | High | Historical pretrends, placebo cutoffs, company effects, industry-year controls, matched samples, and explicit AI-risk controls. | Milestones 7 and 11 |
| M04 | Measurement | Evidence-grounded features may simply reproduce the financial variables rather than add textual evidence. | Medium | Medium | Require source-linked incremental features and ablations beyond financial-only baselines. | Milestone 10 |
| S01 | Statistics | Outcome, metric, or threshold selection after examining the final test creates researcher degrees of freedom. | Medium | High | Freeze the primary outcome, metric, severe-deterioration rule, test cohort, and bootstrap design before access. | Milestone 0 |
| S02 | Statistics | Repeated company observations create correlated errors. | Medium | Medium | Company-clustered bootstrap or cluster-robust inference specified in advance. | Milestone 9 |
| S03 | Statistics | Comparing model decay across periods can be confounded by changes in outcome variance or sample composition. | High | High | Report normalized error, fixed matched cohorts, calibration, outcome distributions, and composition-adjusted comparisons. | Preregistration |
| C01 | Causal interpretation | Post-2022 changes cannot automatically be attributed to generative AI. | High | High | Use “GenAI era,” “disclosure drift,” and “AI-likeness proxy”; separate descriptive evidence from causal inference. | All outputs |
| E01 | Engineering | SEC acquisition may be slow, incomplete, or non-resumable. | Medium | Medium | Bulk archives, manifests, checksums, caching, conservative throttling, and resumable stages. | Milestone 2 |
| P01 | Product | A dashboard may overstate model scores as company risk, AI use, or misconduct. | Medium | High | Display uncertainty and limitations; prohibit verified-AI, fraud, and misconduct labels. | Milestone 12 |

## Current stop conditions

Stop and redesign before production ingestion when any of the following occurs:

1. A direct paper is found that combines the same temporal split, operating outcome, calibration
   analysis, controlled rewrite benchmark, and evidence-grounded defense.
2. The primary operating-margin outcome cannot be reconciled reliably in the pilot.
3. Extraction error is materially correlated with filing period or company characteristics and cannot
   be measured or controlled.
4. The 2024 final-test cohort is accessed for model, prompt, feature, or threshold selection.
5. Fact-preserving rewrite validation fails at an unacceptable preregistered rate.
6. The evidence-grounded model cannot maintain auditable source lineage.
