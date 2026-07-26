# Decision 003 — Temporal Split and Holdout Protection

## Version 0.2

**Date:** 2026-07-25  
**Status:** Approved by project owner  
**Supersedes:** Decision 003 draft version dated 2026-07-25

## Decision

Assign cohorts by the SEC acceptance date of the original Form 10-K:

| Cohort | Dates | Role |
|---|---|---|
| Development | 2010–2021 | All outcome-based development and rolling-origin selection |
| Transition evaluation | 2022–2023 | Locked evaluation; no predictive tuning |
| Final primary test | 2024 | One untouched confirmatory evaluation |
| Prospective secondary test | 2025 | Predictions frozen before outcome linkage; evaluation after maturity gate |
| Current monitoring cohort | 2026 | Text-only drift monitoring and frozen prospective predictions |

## 2025 maturity gate

Evaluate the 2025 cohort no earlier than **2027-03-31**, and only when:

- overall follow-up completeness is at least 90%;
- every major size and industry family has at least 80% completeness;
- predictions were generated and hashed before outcome linkage;
- the pre-2022 model, DDI, features, thresholds, and calibration rules remain unchanged; and
- a prospective-evaluation decision record is committed before metrics are opened.

The 2025 result is a secondary confirmatory replication and cannot replace the 2024 primary result.

## 2026 monitoring and future evaluation

In 2026 the project may collect filings, calculate frozen features and DDI values, analyze outcome-free
language drift, and save prospective model predictions.

It may not report one-year predictive accuracy, calibration, operating deterioration, or model decay
for the 2026 cohort until future annual outcomes mature. The earliest planned cutoff is
**2028-03-31**, followed by the same coverage and freeze gates used for 2025.

## Reason

This design keeps the project current while preventing non-random censoring and future-information
leakage. It creates a mature 2024 primary test, a prospective 2025 replication, and a live 2026
monitoring cohort that can become a later prospective test.
