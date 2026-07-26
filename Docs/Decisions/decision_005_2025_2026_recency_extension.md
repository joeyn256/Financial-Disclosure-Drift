# Decision 005 — 2025 and 2026 Recency Extension

**Date:** 2026-07-25  
**Status:** Approved by project owner

## Decision

- **2024:** untouched primary confirmatory test;
- **2025:** prospective secondary confirmatory test after a 2027-03-31 maturity gate;
- **2026:** current text-only monitoring cohort with frozen prospective predictions;
- **2026 outcomes:** not evaluated before the earliest planned 2028-03-31 maturity gate.

## Rationale

A Form 10-K accepted in 2025 usually reports a fiscal period ending in late 2024 or during 2025.
Its one-year-ahead operating outcome generally appears in the next annual filing, which may not be
accepted until 2026 or early 2027. Early evaluation would disproportionately omit later-fiscal-year,
late-filing, distressed, or otherwise incomplete firms.

Accepted 2026 Forms 10-K are valuable immediately for current disclosure-language monitoring,
data-quality analysis, DDI measurement, and timestamped predictions. They do not yet support a
complete one-year operating-outcome evaluation.

## Safeguards

1. Generate and hash 2025 and 2026 predictions before outcome linkage.
2. Preserve model, feature, DDI, threshold, and environment hashes.
3. Never code an immature missing outcome as neutral or non-event.
4. Report follow-up completeness overall and by size, industry, fiscal timing, and filing status.
5. Label all 2026 dashboard results as **outcome-free monitoring**.
