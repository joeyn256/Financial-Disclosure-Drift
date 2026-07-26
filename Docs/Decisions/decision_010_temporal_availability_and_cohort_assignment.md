# Decision 010 — Temporal Availability and Cohort Assignment

**Date:** 2026-07-25
**Status:** Approved by project owner
**Supersedes:** Decision 003 **only** for its cohort date-source rule
**Preregistration deviation entry:** `Docs/preregistration.md` section 25.1, Deviation D001 —
"Cohort-assignment date source and point-in-time boundary", dated 2026-07-25
**Governs:** Milestone 2 onward

## 1. Decision

1. The frozen cohort windows are unchanged. Development 2010-01-01 to 2021-12-31, transition
   2022-01-01 to 2023-12-31, primary test 2024-01-01 to 2024-12-31, prospective 2025-01-01 to
   2025-12-31, monitoring 2026-01-01 to 2026-12-31. The maturity gates 2027-03-31 and 2028-03-31 and
   the bootstrap seed 20260725 are unchanged.
2. The **official SEC filing date** determines the authoritative temporal cohort,
   `official_filing_temporal_cohort`.
3. The **SEC acceptance date** determines a separate audit-only cohort, `accepted_temporal_cohort`.
4. The point-in-time leakage boundary is the accession's **public-availability boundary**, not its
   raw acceptance timestamp.
5. Decision 003 is preserved in full. Only its date-source rule is superseded.

## 2. Reason

A Form 10-K accepted after the SEC daily cutoff receives the next business day's official filing date
and is not publicly disseminated until that date. Cohorting by acceptance date would place such a
filing in a cohort earlier than the date on which any market participant could have read it, and
would set a predictor cutoff before public availability.

The change was motivated solely by official SEC filing and dissemination mechanics. No SEC filing, no
outcome value, no transition-cohort metric, and no final-test metric was inspected before or during
this decision. The deviation is prospective and outcome-blind.

## 3. Cohort assignment

The frozen cohort logic in `src/disclosure_drift/cohorts.py` is unchanged and is date-source
agnostic. It is called twice:

```python
official_filing_temporal_cohort = cohort_for(official_filing_date)   # authoritative
accepted_temporal_cohort        = cohort_for(acceptance_date_sec)    # audit only
```

Neither call may alter a frozen window. A change to any window requires a new decision record and a
reviewed code change.

## 4. Authoritative field mapping

### 4.1 Official filing date

| Precedence | Source class | Field | Role |
|---|---|---|---|
| 1 | **Accession header** (co-authoritative) | `FILED AS OF DATE` in the complete-submission header **or** in a separately retrieved SGML header | Canonical accession-level value after retrieval |
| 2 | Submissions API | `filingDate` | Provisional discovery and reconciliation observation |
| 2 | Master index | `date filed` | Provisional discovery and reconciliation observation |

The complete-submission header and the separately retrieved SGML header form **one
highest-precedence source class**. Neither is ranked above the other. When they disagree, both
observations are preserved, a conflict record is created, and the accession requires review. The
implementation must not choose between them silently.

Also retained for every accession: `DATE AS OF CHANGE`, correction status, and the source used for
the resolved value.

### 4.2 Acceptance datetime

| Precedence | Source class | Field |
|---|---|---|
| 1 | **Accession header** (co-authoritative) | `<ACCEPTANCE-DATETIME>` in the complete-submission header or the separately retrieved SGML header |
| 2 | Submissions API | `acceptanceDateTime`, when supplied |

Conflicting observations are preserved, not replaced.

### 4.3 Acceptance-date derivation

The raw SEC value is preserved permanently in `acceptance_datetime_sec_raw`.

`acceptance_date_sec` is derived from the **first eight characters** of the SEC `YYYYMMDDHHMMSS`
value. It is never derived by converting through UTC.

Normalized timestamps `acceptance_datetime_et` and `acceptance_datetime_utc` are timezone-aware and
interpreted under the documented SEC Eastern-time policy.

Interpretation uses round-trip validation through UTC for both daylight-saving folds. A candidate
survives only when converting it to UTC and back reproduces the original wall clock. The three
outcomes are distinct:

| Outcome | Condition | Consequence |
|---|---|---|
| Ordinary valid time | One surviving candidate, or two candidates sharing one effective UTC offset | Interpreted normally |
| **Nonexistent local time** | No surviving candidate, because the wall clock is skipped by the spring-forward transition | Stops for review with `REVIEW_TIMEZONE_NONEXISTENT` |
| **Ambiguous local time** | Two surviving candidates with different UTC offsets, because the wall clock occurs twice under the fall-back transition | Stops for review with `REVIEW_TIMEZONE_AMBIGUOUS` |

Neither anomalous case selects an offset automatically. The raw SEC value is preserved in both
cases, and the two conditions carry distinct messages and distinct reason codes so the audit can
tell a skipped time from a doubled one.

## 5. Public-availability boundary

Every accession carries:

| Field | Meaning |
|---|---|
| `public_availability_date_proxy` | Date-level proxy for public availability |
| `availability_precision` | `timestamp` or `date` |
| `availability_basis` | `same_day_acceptance`, `later_official_filing_date`, or `filing_date_only` |

- When the official filing date equals the acceptance date, the acceptance timestamp may serve as a
  `timestamp`-precision boundary with basis `same_day_acceptance`.
- When the official filing date is later than the acceptance date, the official filing date is used
  as a `date`-precision boundary with basis `later_official_filing_date`. An exact dissemination
  timestamp is never fabricated.
- When no acceptance value is available, the boundary is `date` precision with basis
  `filing_date_only`, and the accession receives `REVIEW_MISSING_ACCEPTANCE_TIMESTAMP`.

## 5.1 Reason-based date-divergence classification

A difference between the acceptance date and the official filing date is **never**
explained by the size of the gap. There is no calendar-day allowance. Each accession
receives exactly one classification:

| Reason | Condition | Explained | Consequence |
|---|---|---|---|
| `same_day_filing` | The official filing date equals the SEC acceptance date. | Yes | No review. |
| `expected_after_cutoff_rollover` | The eligible annual report was accepted **on a proven EDGAR operating day**, at or after the frozen 17:30 America/New_York cutoff, **and** the official filing date equals the next operating business day. All three conditions are required. | Yes | No review, but still reported in the divergence audit. |
| `post_acceptance_date_correction` | Filing metadata or `DATE AS OF CHANGE` indicates an authorized later correction or filing-date adjustment. | Yes | Preserved observations required; review required when it affects cohort assignment. |
| `unexplained_date_divergence` | The difference cannot be established from the approved rules and preserved source evidence. | No | **Blocks release freezing** and requires review. |

Order of evaluation is fixed: same-day, then filing-date-before-acceptance, then
correction, then rollover, then unexplained. Because correction is evaluated before
rollover, a correction can never be silently recorded as ordinary after-hours
behaviour.

Additional rules:

- An official filing date **earlier** than the acceptance date requires review and is
  never classified as an ordinary rollover.
- Rollover requires an **injected EDGAR operating calendar**. No weekday is assumed to
  be an operating day. When no calendar is supplied, or when the dates fall outside
  the calendar's coverage, the classification is `unexplained_date_divergence` with
  `OPERATING_CALENDAR_UNAVAILABLE`; nothing is assumed.
- Stage M2.1 tests rollover with a synthetic operating calendar carrying
  `source_kind = synthetic_fixture`. The production calendar is loaded in Stage M2.2
  from an approved official source and retains snapshot provenance
  (`source_kind = sec_snapshot` with a required `snapshot_id`).

## 5.2 Frozen after-hours cutoff

For the supported forms `10-K`, `10-K/A`, `10-KT`, and `10-KT/A`, the production
after-hours cutoff is **frozen at 17:30 America/New_York**.

- It is **not** a user-configurable setting. There is no key in
  `configs/project.yaml` and no entry in the environment allowlist, and a unit test
  asserts both absences.
- Tests may inject a different cutoff to exercise boundary behaviour. Production
  policy changes require a **versioned methodological update supported by official
  SEC documentation**, recorded as a new decision or a revision of this one.
- No frozen cutoff is defined for any other form. When a form outside the supported
  set is supplied, an after-cutoff rollover cannot be inferred and the divergence is
  `unexplained_date_divergence`.

## 5.3 Acceptance on a non-operating day

A purported SEC acceptance dated on a non-operating day is **not rollover-eligible**.
EDGAR does not ordinarily accept filings on weekends or federal holidays, so such an
observation indicates a data problem rather than ordinary after-hours behaviour.

- The observation is preserved exactly as received.
- The accession is classified `unexplained_date_divergence` and carries
  `REVIEW_ACCEPTANCE_ON_NON_OPERATING_DAY`.
- Automatic rollover classification is blocked, reconciliation is required, and the
  accession blocks release freezing until reconciled.

## 6. Point-in-time eligibility as a tri-state comparison

The test is `source_public_availability_boundary <= target_public_availability_boundary`, evaluated as
a tri-state outcome, never as a bare Boolean.

| Outcome | Condition |
|---|---|
| `eligible` | The source is the target's own accession, evaluated against the target's approved boundary; or both boundaries are exact timestamps and the source timestamp is at or before the target timestamp; or the boundaries are on different dates and the source date precedes the target date |
| `ineligible` | Both boundaries are exact timestamps and the source timestamp is after the target timestamp; or the source date follows the target date |
| `indeterminate` | Two different accessions share the same boundary date and at least one boundary has `date` precision, so their order cannot be established |

`indeterminate` blocks automatic historical use and creates a review reason
(`REVIEW_AVAILABILITY_ORDER_INDETERMINATE`). It must never be recorded as a claim that the source was
definitely unavailable, and it must never be silently treated as eligible.

The target accession's own filing package is always eligible against its own approved boundary, even
when that boundary is later than its acceptance timestamp.

## 7. Amendments

A linked `10-K/A` or `10-KT/A` carries its own official filing date, its own acceptance datetime, its
own authoritative and audit cohorts, `inventory_role = amendment_non_target`, and an explicit
relationship to the original accession. It never inherits the original filing's cohort and never
changes it.

## 8. Cohort-divergence audit

The acquisition and release audits must report:

- total accessions where the two cohort fields differ;
- counts by original versus amendment;
- counts by form;
- counts by acceptance year and by official filing year;
- every accession crossing a frozen cohort boundary, with the old and new cohort assignments,
  acceptance datetime, official filing date, availability basis, and all source observations.

Gating rules:

| Condition | Consequence |
|---|---|
| Divergence fully explained by SEC filing-date rules | Not a failure; reported |
| Unexplained divergence | Blocks release freezing |
| Divergence crossing a frozen cohort boundary | Requires manual review |
| Accession entering or leaving the untouched 2024 cohort | Listed explicitly in the acceptance report and approved before release freezing |

## 9. Restatements and corrections

Later restated values remain attached to the later accession that reported them. An originally
reported observation is never destructively replaced. Post-acceptance corrections are recorded as new
observations with `correction_status` and, when they move a filing across a frozen boundary,
`REVIEW_CORRECTION_CROSSES_COHORT_BOUNDARY`.

## 10. Revisit triggers

Reopen this decision if:

1. the SEC changes its filing-date assignment or dissemination rules;
2. pilot evidence shows accession-header sources disagree at a material rate;
3. timezone interpretation becomes ambiguous in official documentation; or
4. the `indeterminate` rate is high enough to affect universe composition; or
5. the official EDGAR operating calendar becomes unavailable or changes definition; or
6. official SEC documentation establishes a different filing cutoff, which requires a
   versioned methodological update before any code change.
