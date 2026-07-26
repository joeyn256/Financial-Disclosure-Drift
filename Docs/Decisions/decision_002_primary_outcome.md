# Decision 002 — Primary Outcome and Company Universe

**Date:** 2026-07-25  
**Status:** Proposed freeze pending project-owner approval

## Decision

The primary prediction target is the training-capped, industry-adjusted, one-year change in operating
margin for nonfinancial U.S. domestic public operating companies.

## Formula

`OM(i,t) = OperatingIncomeLoss(i,t) / Revenue(i,t)`

`RawDeltaOM(i,t+1) = OM(i,t+1) - OM(i,t)`

`AdjDeltaOM(i,t+1) = RawDeltaOM(i,t+1) - industry-year median`

Industry is the first two digits of the target filing’s SEC SIC. The cell must have at least 10 firms;
otherwise use the corresponding one-digit SIC-year cell. If that also has fewer than 10 firms, exclude
the observation from the primary adjusted analysis.

## Outcome transformation

- regression caps: development-cohort 1st and 99th percentiles;
- caps applied unchanged to every later cohort;
- uncapped outcome reported as robustness;
- severe deterioration: uncapped adjusted outcome at or below the development-cohort 10th percentile.

## Outcome timing

Use the next eligible annual fiscal period with a period-end gap of 300–430 days. Primary outcomes use
facts first reported in the next original Form 10-K. Later amendments and restatements are robustness
versions.

## Primary universe

Include original Forms 10-K accepted from 2010 through 2024 for U.S. domestic operating companies.

Primary exclusions include:

- SIC 6000–6999;
- shell, blank-check, fund, ETF, and asset-backed issuers;
- non-positive revenue;
- unreconciled revenue or operating income;
- nonstandard annual duration;
- unmatched next annual period;
- invalid SIC;
- failed Item 7 extraction;
- no prior eligible 10-K for the common cohort; and
- frozen parser failures.

Delisted and failed firms remain eligible.

## Reason

Operating-margin change is an economically interpretable continuous outcome that differs from the
short-horizon returns, bankruptcy, tax, and risk outcomes emphasized by the closest competitors.
Industry adjustment reduces differences in typical profitability changes across business categories,
while a continuous target avoids designing the entire project around a rare event.

## Deferred implementation detail

The exact XBRL concept hierarchy is not selected by outcome performance. It will be frozen after the
24-company pilot based on reconciliation quality and then applied identically across cohorts.

## Revisit triggers

Reopen before later-period evaluation only if:

1. pilot reconciliation is materially unreliable;
2. the common cohort fails the minimum feasibility gates; or
3. the SEC facts cannot support a stable cross-company concept hierarchy.
