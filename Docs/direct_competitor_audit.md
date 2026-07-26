# Disclosure Drift — Direct Competitor Audit

**Audit date:** 2026-07-25  
**Studies audited:** 11  
**Cumulative literature universe:** 62 sources

## Verdict

No audited study duplicates the full approved design.

The literature already contains direct work on every individual component:

- temporal prediction using full 10-K text;
- one-year bankruptcy prediction from 10-K narrative;
- operating-risk and financial-performance measures from filing text;
- financial semantic drift;
- GenAI-era disclosure language;
- AI-likeness and sentiment in 10-K sections;
- capital-market effects of possible GenAI-assisted MD&A;
- controlled counterfactual financial narratives; and
- full-10-K versus Item 1A predictive comparisons.

The project is defensible only as the combined reliability design frozen in Decision 006.

## Highest-risk competitors

### Harrington et al. (2026)

This is the closest temporal-prediction competitor. It uses full 10-K filings in six sequential
2015–2020 phases and predicts 30-day stock-return direction. It eliminates any claim that Disclosure
Drift is the first temporal-drift study using 10-K prediction.

It does not use the GenAI-era cutoff, one-year operating outcomes, predictive calibration, paired
fact-preserving rewrites, or an evidence-grounded model family.

### Zhang et al. (2026)

This is the closest future-adverse-outcome competitor. It studies 40,475 firm-year observations,
predicts bankruptcy within one year of filing, combines accounting variables with an interpretable
narrative score, and includes out-of-time evaluation.

It does not study continuous operating deterioration, 2024-era reliability, calibration decay, DDI,
or controlled rewrite robustness.

### Grundy and Petry; Gupta, Rawte, and Zaki

These studies remove novelty for operating-risk extraction, adaptive dictionaries, filing changes,
and prediction of future financial performance from SEC narrative.

Disclosure Drift must therefore emphasize whether established text-model families remain reliable
after the writing environment changes.

### Blankespoor, deHaan, and Li; Perlin et al.; Plate et al.

These studies establish that GenAI-era disclosure language, possible AI-assisted financial reporting,
and market responses to AI-likeness are existing research areas.

Disclosure Drift must never describe a detector score as verified AI use. Its focus is downstream
model reliability.

### Matera (2025)

This study uses LLM-generated counterfactual earnings-call narratives while holding quantitative
content fixed. It eliminates novelty for controlled financial-narrative transformation.

Disclosure Drift’s distinction is the preregistered validation of factual preservation and the use of
paired rewrites to test already-frozen filing models.

### Choi (2026)

This late-breaking paper compares full 10-K text with Item 1A at sector, portfolio, and firm levels.
It was added to the cumulative literature matrix during this audit.

The project will report section-specific and aggregation-level robustness without claiming that this
comparison is novel.

## Verification limitation

The Lin (2026) SSRN pilot was verified through the primary SSRN page and indexed primary-PDF
snippets. Direct PDF retrieval was restricted during this audit. The available primary metadata
shows a 50-firm large-cap pilot, event years 2016–2025, filing-event labels tied to following trading
windows, and a rolling out-of-sample design. These details are sufficient to rule out duplication of
the operating-outcome, calibration, and rewrite design, but the full paper must be checked again
before public novelty language is finalized.

## Final conclusion

Milestone 0 may close for engineering progression because:

1. no direct duplicate of the combined design was identified;
2. all individual component-level novelty claims have been prohibited;
3. Stage 1 is preregistered and committed;
4. the contribution is narrow and testable; and
5. the literature review remains a living research control through publication.
