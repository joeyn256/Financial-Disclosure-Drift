# Disclosure Drift — Literature Search Log

## Batch 02

**Search date:** 2026-07-25  
**Cumulative verified sources:** 61  
**Sources added in this batch:** 31  
**Status:** The numerical target of 50–75 sources has been reached. Full-paper verification remains required for the most direct working-paper competitors.

## Purpose

Literature Batch 02 focused on the gaps that remained after the first novelty pass:

1. future operating and financial outcomes predicted from 10-K, MD&A, and Item 1A text;
2. out-of-time or out-of-sample reliability of filing-text models;
3. textual change and adaptive dictionaries;
4. structural disclosure information such as risk ordering and prominence;
5. GenAI-era corporate communication and explicit AI-risk disclosures; and
6. auditable, evidence-grounded financial NLP.

## Search channels

- SSRN
- arXiv
- ACL Anthology
- publisher and journal pages
- accounting-school research briefs
- backward references from direct competitors
- forward searches using direct-competitor titles and core constructs

## Representative search strings

- `"10-K" future operating performance prediction text`
- `"10-K" out-of-sample predictive information`
- `"10-K" temporal reliability calibration`
- `"operating risk" "10-K text"`
- `"bankruptcy prediction" "10-K narratives"`
- `"SEC filing changes" financial performance dictionary`
- `"risk factor prominence" future adverse outcomes`
- `"risk factor disclosure summaries" LLM`
- `"AI risk disclosures" 10-K 2020 2024`
- `grounded financial reasoning benchmark`
- `auditable financial question answering evidence`
- `financial retrieval augmented generation benchmark`

## Most consequential additions

### 1. Grundy and Petry — operating and financing risk from 10-K text

This paper directly constructs operating and financing risk measures from Item 1A disclosures.
Disclosure Drift therefore cannot claim to introduce the general idea of extracting operating risk
from 10-K text.

### 2. Zhang et al. — one-year bankruptcy prediction from 10-K narratives

This study combines an interpretable narrative stress score, accounting baselines, a one-year
post-filing outcome, holdout testing, and out-of-time validation. It is a close competitor for the
future-adverse-outcome component.

### 3. Lin — out-of-sample audit of predictive 10-K information

This July 2026 pilot directly frames its contribution as an audit of predictive information in SEC
10-K text. Disclosure Drift must avoid claiming to be the first out-of-sample reliability audit.

### 4. Gupta, Rawte, and Zaki — filing changes and future financial performance

This study automatically learns a dictionary from changes in 10-K and 8-K filings and predicts
future financial-performance indicators. It narrows novelty for adaptive dictionaries and
performance prediction.

### 5. Chin, Liu, and Moffitt — risk-factor prominence

Risk-factor ordering predicts future adverse outcomes. The planned feature set must preserve
document structure so that model decay is not incorrectly attributed only to changes in prose.

## Contribution after Batch 02

> Disclosure Drift tests whether models trained only on pre-2022 10-K disclosures lose accuracy
> and calibration when predicting one-year-ahead, industry-adjusted operating deterioration in
> 2024-era filings; whether any deterioration is concentrated in style-dependent representations;
> and whether evidence-grounded models are more stable under both observed disclosure drift and
> preregistered, fact-preserving rewrites.

This contribution is still provisional. The defensibility comes from the **combination**, not from
any single component.

## Claims now explicitly unavailable

- first temporal-drift study using 10-K prediction;
- first out-of-sample audit of predictive information in 10-K text;
- first prediction of future fundamentals, operating risk, or bankruptcy from 10-K narrative;
- first use of adaptive financial dictionaries;
- first measurement of GenAI-era corporate-disclosure change;
- first controlled or counterfactual transformation of financial narrative; and
- first evidence-grounded financial NLP system.

## Remaining literature work

1. Read the full text of every High-threat source.
2. Record sample years, sample size, exact outcome, split design, and evaluation metrics.
3. Perform a final author/title/DOI audit.
4. Refresh the search immediately before the research paper is released.
5. Label sources that are working papers or pilots so their claims are not treated as settled evidence.
