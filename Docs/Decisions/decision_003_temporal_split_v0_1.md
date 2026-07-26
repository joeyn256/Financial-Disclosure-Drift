# Decision 003 — Temporal Split and Holdout Protection

**Date:** 2026-07-25  
**Status:** Proposed freeze pending project-owner approval

## Decision

Assign cohorts by the SEC acceptance date of the original Form 10-K:

| Cohort | Dates | Role |
|---|---|---|
| Development | 2010–2021 | All outcome-based development and rolling-origin selection |
| Transition evaluation | 2022–2023 | Locked evaluation; no predictive tuning |
| Final primary test | 2024 | One untouched confirmatory evaluation |
| Provisional extension | 2025 onward | Monitoring until future-outcome coverage is complete |

The previous phrase **transition validation** is retired because it could imply permission to tune the
predictive model using post-2021 outcomes.

## Rolling-origin folds

- A: train 2010–2014, validate 2015–2016
- B: train 2010–2016, validate 2017–2018
- C: train 2010–2018, validate 2019
- D: train 2010–2019, validate 2020
- E: train 2010–2020, validate 2021

After selection, refit on 2010–2021 and evaluate unchanged on 2022, 2023, and 2024.

## Final-test protection

Before 2024 outcomes are evaluated, freeze:

- code commit;
- environment;
- feature schema;
- model manifests;
- outcome threshold;
- DDI;
- rewrite prompts;
- row-ID hash; and
- leakage checklist.

If a viewed 2024 metric leads to any change, the modified analysis becomes exploratory.

## Reason

The central research question is whether a model trained only in the pre-2022 environment remains
reliable later. Allowing 2022–2023 outcomes to tune the model would weaken that interpretation.
2024 is the primary test because its one-year-ahead outcomes are substantially more complete than the
2025 cohort.

## Permitted use of 2022–2023 text

Outcome-free 2022–2023 text may be used to construct the DDI and draw the confirmatory rewrite sample,
provided no financial outcome or model-error value enters those procedures.

## Revisit trigger

A redesign after transition evaluation requires a new preregistration version while 2024 remains
unopened.
