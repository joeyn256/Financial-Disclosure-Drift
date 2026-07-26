# Milestone 0 Completion — Novelty Audit and Research Charter

**Project:** Disclosure Drift  
**Completion date:** 2026-07-25  
**Status:** Complete for progression to Milestone 1  
**Stage 1 freeze commit:** `2b7d24b` — `Freeze Milestone 0 Stage 1 research design`

## Objective

Determine whether the proposed research contribution is sufficiently distinct before substantial
engineering begins, and freeze a defensible research protocol.

## Completed deliverables

- 62-source cumulative literature matrix;
- reproducible literature search log;
- cumulative BibTeX bibliography;
- 11-study direct-competitor audit;
- research-risk register;
- leakage register;
- Decisions 001–006;
- approved Stage 1 preregistration;
- 2024 primary-test protection;
- prospective 2025 and current 2026 design;
- versioned Research Charter;
- timestamped Git research-design freeze.

## Final research question

Do models developed exclusively on pre-2022 Form 10-K disclosures lose predictive accuracy or
calibration when applied to 2024-era filings, and are evidence-grounded models more robust than
style-heavy models under observed disclosure drift and controlled factual-preservation rewrites?

## Frozen temporal design

| Cohort | Role |
|---|---|
| 2010–2021 | Development and rolling-origin selection |
| 2022–2023 | Locked transition evaluation |
| 2024 | Untouched primary test |
| 2025 | Prospective secondary replication after maturity gate |
| 2026 | Outcome-free monitoring and frozen prospective predictions |

## Completion gates

| Gate | Result |
|---|---|
| Written contribution statement | Passed |
| 50–75 source matrix | Passed — 62 sources |
| Search log and bibliography | Passed |
| Direct competitors identified | Passed |
| Direct duplication unresolved | No direct duplication found |
| Primary outcome defined | Passed |
| Temporal split defined | Passed |
| Confirmatory hypotheses defined | Passed |
| Leakage and risk registers | Passed |
| Preregistration-style plan | Passed |
| Git freeze | Passed — commit `2b7d24b` |

## Standing limitations

- The literature is fast moving and must be refreshed before publication.
- The Lin (2026) pilot requires a full-text recheck when direct access is available.
- Exact XBRL concept precedence, parser thresholds, estimator package, and feature implementations
  remain Stage 2A decisions based only on the historical pilot.
- DDI coefficients and rewrite prompts remain Stage 2B decisions and cannot use 2024 outcomes.

## Authorization for next milestone

Milestone 1 may begin, but it is limited to reproducible repository foundation work.

Claude Code may create infrastructure, tests, configuration, CI, and repository documentation. It may
not download SEC filings, construct outcomes, engineer research features, build the DDI, generate
rewrites, train predictive models, or access final-test outcomes.
